"""Ventanas OBSERVADAS de siembra y cosecha (Piura Agronomía, calendario_siembra_cosecha_piura.csv, DRAP 2016-2024).

Son meses en que se sembró o cosechó ≥ 10 % del área (anuales) o de la producción (perennes) según la estadística
agrícola oficial agregada por zona. Describen lo que se hizo, NO lo que conviene: el motor las usa solo para decir si
el mes de siembra elegido tiene experiencia local, nunca para descartar.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .validacion import ACEPTADA, IGNORADA, RECHAZADA, ZONAS_AGREGADAS, ZONAS_PARCELA

ARCHIVO = "calendario_siembra_cosecha_piura.csv"
COLUMNAS = ("crop", "zona", "desfase_siembra_cosecha_observado", "mes_pico_cosecha", "mes_pico_siembra",
            "ventana_cosecha_observada", "ventana_siembra_observada", "confianza", "source_url", "periodo",
            "validation_status", "applicability_note")
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "sep": 9,
         "oct": 10, "nov": 11, "dic": 12}
# nombre del archivo -> cultivo del catálogo. Lo ambiguo no se mapea (se ignora y se anota).
CULTIVO = {"algodon (Pima)": "algodon", "algodon (no Pima)": "algodon", "platano/banano": "banano",
           "frijol caupi": "caupi", "arveja": "arveja", "arveja (grano verde)": "arveja"}
AMBIGUOS = {"frijol caupi (vaina verde)": "puede ser caupí o el 'frijol verde' del catálogo; no se asigna",
            "frijol castilla/grano seco": "'frijol castilla' en Piura suele ser caupí, pero la fila dice grano seco "
                                          "(podría ser frijol grano); no se asigna"}
FUENTE = "Piura Agronomía, calendario_siembra_cosecha_piura.csv (DRAP Piura, campaña agrícola 2016-2024)"


@dataclass
class VentanaObservada:
    cultivo: str
    zona: str
    siembra: set = field(default_factory=set)
    cosecha: set = field(default_factory=set)
    texto_siembra: list = field(default_factory=list)
    texto_cosecha: list = field(default_factory=list)
    variedades: list = field(default_factory=list)
    confianza: float = 0.0
    url: str = ""
    periodo: str = ""

    def describir(self) -> str:
        return (f"siembra observada {' / '.join(self.texto_siembra) or 'sin dato'}; cosecha observada "
                f"{' / '.join(self.texto_cosecha) or 'sin dato'} ({', '.join(self.variedades)}; {self.periodo}; "
                f"confianza {self.confianza:g})")


def meses_de(texto: str) -> set[int]:
    """'feb-mar; ago' -> {2, 3, 8}; 'dic-feb' cruza el año. Lanza ValueError si no se entiende."""
    out = set()
    for parte in (p.strip() for p in texto.split(";") if p.strip()):
        if "-" in parte:
            a, b = (MESES[x.strip()] for x in parte.split("-"))
            m = a
            while True:
                out.add(m)
                if m == b:
                    break
                m = m % 12 + 1
        else:
            out.add(MESES[parte])
    return out


def zonas_de(texto: str) -> list[str] | None:
    """Códigos de zona de CONTRATO.md a los que aplica la fila. Desde la ronda 6 de Agronomía la columna `zona`
    trae el código (alto_piura, …), no el nombre; un nombre ('Alto Piura') ya no se adivina: la fila se rechaza.
    Una zona agregada (medio_bajo_piura) se expande a sus zonas. None = código no reconocido."""
    t = (texto or "").strip()
    if t in ZONAS_PARCELA:
        return [t]
    if t in ZONAS_AGREGADAS:
        return list(ZONAS_AGREGADAS[t])
    return None


def cargar(cat, ruta: Path) -> dict:
    """Valida y carga. Devuelve {(cultivo, zona): VentanaObservada}. Anota cada fila en cat.registro."""
    out: dict = {}
    if not ruta.exists():
        return out
    with open(ruta, encoding="utf-8") as f:
        lector = csv.DictReader(f)
        faltan = [c for c in COLUMNAS if c not in (lector.fieldnames or [])]
        if faltan:
            cat._anotar(ruta, "-", "", "calendario", RECHAZADA, f"faltan columnas {faltan}: archivo no cargado")
            return out
        for i, r in enumerate(lector, start=2):
            nombre = r["crop"].strip()
            cultivo = CULTIVO.get(nombre, nombre)
            if nombre in AMBIGUOS:
                cat._anotar(ruta, i, nombre, "calendario", IGNORADA, AMBIGUOS[nombre])
                continue
            if cultivo not in cat.fichas:
                cat._anotar(ruta, i, nombre, "calendario", IGNORADA, "cultivo fuera del catálogo del motor")
                continue
            if cat.fichas[cultivo].modulo != "anual":
                cat._anotar(ruta, i, cultivo, "calendario", IGNORADA, "perenne: la ventana es de cosecha y el motor "
                            "no programa siembras de perennes")
                continue
            problemas = []
            zonas = zonas_de(r["zona"])
            extra = [z.strip() for z in (r.get("zonas_aplicables") or "").split(";") if z.strip()]
            if zonas is None:
                problemas.append(f"zona '{r['zona']}' no es un código de CONTRATO.md ({', '.join(ZONAS_PARCELA)})")
            elif extra:
                malas = [z for z in extra if z not in ZONAS_PARCELA]
                if malas:
                    problemas.append(f"zonas_aplicables con códigos inválidos {malas}")
                else:
                    zonas = list(dict.fromkeys(zonas + extra))
            if not r["source_url"].startswith("http"):
                problemas.append("sin source_url")
            if not r["periodo"].strip():
                problemas.append("sin periodo")
            try:
                conf = float(r["confianza"])
                if not 0 <= conf <= 1:
                    problemas.append("confianza fuera de 0-1")
            except ValueError:
                conf = 0.0
                problemas.append("confianza no numérica")
            try:
                siembra = meses_de(r["ventana_siembra_observada"])
                cosecha = meses_de(r["ventana_cosecha_observada"])
            except (KeyError, ValueError) as e:
                problemas.append(f"ventana ilegible ({e})")
                siembra = cosecha = set()
            ausencia = "ausencia" in (r.get("validation_status") or "") and not siembra and not cosecha
            if ausencia and not problemas:  # marcador de ausencia observada: no es ventana, es una alerta
                for zona in zonas:
                    cat.ausencias_calendario[(cultivo, zona)] = (r["periodo"], r["source_url"], conf)
                cat._anotar(ruta, i, cultivo, "calendario", ACEPTADA,
                            f"{', '.join(zonas)}: ausencia observada (0 ha en la DRAP, {r['periodo']}); sin ventana de "
                            "siembra observada; se usa como alerta, no como ventana")
                continue
            if not siembra:
                problemas.append("sin ventana de siembra observada")
            if problemas:
                cat._anotar(ruta, i, cultivo, "calendario", RECHAZADA, "; ".join(problemas))
                continue
            for zona in zonas:
                v = out.setdefault((cultivo, zona), VentanaObservada(cultivo, zona, url=r["source_url"],
                                                                      periodo=r["periodo"]))
                v.siembra |= siembra
                v.cosecha |= cosecha
                v.texto_siembra.append(r["ventana_siembra_observada"])
                v.texto_cosecha.append(r["ventana_cosecha_observada"])
                v.variedades.append(nombre)
                v.confianza = max(v.confianza, conf)
            cat._anotar(ruta, i, cultivo, "calendario", ACEPTADA,
                        f"{', '.join(zonas)}: siembra {r['ventana_siembra_observada']} (regional, observado; ventana observada, "
                        "no recomendación)")
    return out


def evaluar_mes(v: VentanaObservada, mes: int) -> str:
    """'dentro', 'borde' (a un mes de la ventana) o 'fuera'."""
    if mes in v.siembra:
        return "dentro"
    if ((mes % 12) + 1) in v.siembra or ((mes - 2) % 12 + 1) in v.siembra:
        return "borde"
    return "fuera"

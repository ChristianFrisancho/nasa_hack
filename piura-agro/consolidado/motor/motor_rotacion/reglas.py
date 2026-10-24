"""Reglas de Piura Agronomía cargadas como reglas del motor.

Cada regla es una fila CONTRATO.md (reglas_rotacion.csv, fichas_anuales.csv, recuperacion_suelo.csv). Se validan
antes de usarse; si una no cumple el contrato, el motor la deja inactiva y lo anota en el registro. El
comportamiento (cuándo avisa) está en filtros.f_normas, estado_suelo y nutrientes; aquí solo se cargan y se
interpretan sus valores (ventanas de siembra por zona, cifras FEN 2017, pronóstico ENFEN).
"""
from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

from .validacion import (ACEPTADA, IGNORADA, RECHAZADA, ZONAS_AGREGADAS, faltan_columnas, validar_fila_contrato,
                         zonas_de_fila)

ARCHIVOS = ("reglas_rotacion.csv", "fichas_anuales.csv", "recuperacion_suelo.csv")
REGLAS_USADAS = {
    "R4R001": "arroz con drenaje deficiente o napa < 2 m sube napa y ECe",
    "R4R002": "con drenaje funcional y napa ≥ 2 m el arroz puede lavar sales",
    "R4R003": "alerta de Niño + parcela inundable + cultivo en campo ene-abr = riesgo alto de pérdida",
    "R4R004": "campo limpio 75-80 días tras el algodón",
    "R4R005": "gorgojo de la chupadera: al menos 1 campaña sin algodón",
    "R4R006": "socas de algodón prohibidas",
    "R4A002": "ventana de siembra algodón", "R4A003": "ventana de siembra algodón",
    "R4A006": "ventana de siembra algodón", "R4A007": "ventana de siembra algodón",
    "R4A010": "ventana de siembra algodón", "R4A011": "ventana de siembra algodón",
    "R4A014": "ventana de siembra algodón", "R4A015": "ventana de siembra algodón",
    "R4A021": "área perdida FEN 2017", "R4A022": "área afectada FEN 2017",
    "R4A025": "pronóstico ENFEN vigente",
    "R4A026": "napa ≥ 2 m para que valga ECe ≈ 1.5·ECw",
    "R4S001": "prohibido incorporar rastrojo de algodón (RM 0251-94-AG Art. 12)",
}
# Solo para archivos antiguos sin columna zona (formato anterior a CONTRATO.md con zona). Con zona/zonas_aplicables
# (ronda 6 de Agronomía en adelante) manda el código del contrato y esto no se usa.
LUGAR_A_ZONAS = {
    "Medio y Bajo Piura": ("medio_piura", "bajo_piura"),
    "Alto Piura": ("alto_piura",),
    "Valle del Chira": ("chira",),
    "San Lorenzo": ("san_lorenzo",),
}
MESES = {m: i for i, m in enumerate(("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"), 1)}
VIGENCIA_PRONOSTICO_DIAS = 60  # supuesto del motor: un comunicado ENFEN se considera vigente 60 días


def cargar_reglas(cat, directorio: Path) -> dict[str, dict]:
    reglas: dict[str, dict] = {}
    for nombre in ARCHIVOS:
        ruta = Path(directorio) / nombre
        if not ruta.exists():
            continue
        with open(ruta, newline="", encoding="utf-8") as fh:
            lector = csv.DictReader(fh)
            filas, cab = list(lector), lector.fieldnames or []
        faltan = faltan_columnas(cab)
        sin_zona = faltan == ["zona"]
        no_usadas = no_cumplen = 0
        for r in filas:
            rid = r.get("id", "")
            if sin_zona:
                r = {**r, "zona": ""}
            problemas = [f"faltan columnas {faltan}"] if faltan and not sin_zona else validar_fila_contrato(r, numerica=False)
            if rid not in REGLAS_USADAS:
                no_usadas += 1
                no_cumplen += bool(problemas)
                continue
            if problemas:
                cat._anotar(ruta, rid, r.get("cultivo", ""), r.get("variable", ""), RECHAZADA,
                            "; ".join(problemas) + " → regla inactiva")
                continue
            reglas[rid] = r
            cat._anotar(ruta, rid, r.get("cultivo", ""), r.get("variable", ""), ACEPTADA,
                        f"regla del motor: {REGLAS_USADAS[rid]}"
                        + (" (aceptada con salvedad: el archivo no trae la columna zona; la zona se deduce de 'lugar' cuando hace falta)" if sin_zona else ""))
        if no_usadas:
            cat._anotar(ruta, f"{no_usadas} filas", "", "", IGNORADA,
                        f"filas que el motor v1 no modela (de ellas {no_cumplen} no cumplirían el contrato)")
    return reglas


def _fecha(txt: str) -> tuple[int, int]:
    d, m = txt.strip().split()
    return MESES[m[:3].lower()], int(d)


def ventana(r: dict) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """'1 ene - 28 feb' -> ((1, 1), (2, 28))."""
    try:
        a, b = re.split(r"\s+-\s+", r["valor"])
        return _fecha(a), _fecha(b)
    except (ValueError, KeyError):
        return None


def mes_en_ventana(mes: int, v) -> str:
    """'si' si todo el mes cae en la ventana, 'parcial' si una parte, 'no' si nada (ventanas que cruzan el año incluidas)."""
    (m1, d1), (m2, d2) = v
    meses = list(range(m1, m2 + 1)) if m1 <= m2 else list(range(m1, 13)) + list(range(1, m2 + 1))
    if mes not in meses:
        return "no"
    completo = (mes != m1 or d1 == 1) and (mes != m2 or d2 >= 28)
    return "si" if completo else "parcial"


def zonas_regla(r: dict) -> tuple[str, ...]:
    """Zonas concretas en que vale una regla: códigos de zona/zonas_aplicables (las agregadas se expanden);
    solo si la fila no trae ninguno se deduce de 'lugar' (archivos antiguos)."""
    out: list[str] = []
    for z in zonas_de_fila(r):
        out += list(ZONAS_AGREGADAS.get(z, (z,)))
    if out:
        return tuple(dict.fromkeys(out))
    return LUGAR_A_ZONAS.get(r.get("lugar", ""), ())


def ventanas_algodon(reglas: dict, zona: str | None) -> list[dict]:
    out = []
    for rid, r in reglas.items():
        if r.get("variable") == "ventana_siembra" and r.get("cultivo") == "algodon":
            if zona is None or zona in zonas_regla(r):
                out.append(r)
    return out


def alerta_enfen_vigente(reglas: dict, hoy: date | None = None) -> tuple[bool | None, str]:
    r = reglas.get("R4A025")
    if r is None:
        return None, "sin pronóstico ENFEN cargado"
    try:
        emitido = date.fromisoformat(r["fecha_o_periodo"])
    except ValueError:
        return None, "fecha del comunicado ENFEN ilegible"
    hoy = hoy or date.today()
    dias = (hoy - emitido).days
    if dias > VIGENCIA_PRONOSTICO_DIAS:
        return None, f"el comunicado ENFEN tiene {dias} días; puede estar desactualizado"
    return True, f"ENFEN {r['fecha_o_periodo']}: {r['valor']}"

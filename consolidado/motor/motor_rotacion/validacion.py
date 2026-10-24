"""Validación de filas antes de entrar al motor (CONTRATO.md: "si no lo cumple, no entra").

Dos familias de archivos:
- formato CONTRATO.md (variable, valor, …, tipo_evidencia, estado, notas): `validar_fila_contrato`.
- esquemas del repo nasa_hack (parametros_cultivo_v2, fao56_kc, nutrientes_cultivo, umbrales de salinidad):
  validadores por esquema que exigen lo mismo en sustancia: cultivo, cifra numérica coherente, unidad y fuente con URL.

Cada fila revisada deja un `Registro` (aceptada | rechazada | ignorada) con el motivo. Ignorada = cumple el
contrato pero el motor no la usa (cultivo fuera del catálogo o variable que el motor no modela).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

from .cifra import ESTADOS, TIPOS_EVIDENCIA

COLUMNAS_CONTRATO = ("variable", "valor", "valor_min", "valor_max", "unidad", "cultivo", "variedad", "etapa", "zona",
                     "lugar", "lat", "lon", "fecha_o_periodo", "fuente", "url_o_doi", "metodo", "tipo_evidencia",
                     "estado", "notas")
COLUMNAS_OPCIONALES = ("fuente_primaria", "subzona", "zonas_aplicables")
ZONAS = ("alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura", "medio_bajo_piura",
         "piura_region", "")
# zona agregada -> zonas que cubre (un dato 'medio_bajo_piura' vale para una parcela de Medio o Bajo Piura,
# con prioridad menor que un dato de la zona exacta)
ZONAS_AGREGADAS = {"medio_bajo_piura": ("medio_piura", "bajo_piura")}
# códigos de zona concretos (los que puede tener una parcela)
ZONAS_PARCELA = ("alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura")
CONTRATO_MD = Path(__file__).resolve().parents[3] / "CONTRATO.md"


def unidades_de_contrato(texto: str) -> tuple[str, ...]:
    """Lista de unidades de la línea '- Unidades …: a, b, c y d.' de CONTRATO.md, sin las glosas entre paréntesis.
    Se lee del archivo (no se copia a mano) porque la copia en código se quedó atrás dos veces."""
    linea = next((x for x in texto.splitlines() if x.startswith("- Unidades")), None)
    if linea is None:
        raise ValueError("CONTRATO.md no tiene la línea '- Unidades …'")
    lista = linea.split(":", 1)[1].split(". ")[0]
    lista = re.sub(r"\s\([^)]*\)", "", lista)  # '%/(dS/m) (pendiente …)' -> '%/(dS/m)'
    return tuple(u.strip().rstrip(".") for u in re.split(r",\s*|\s+y\s+", lista) if u.strip())


if not CONTRATO_MD.exists():
    raise FileNotFoundError(f"falta {CONTRATO_MD}: el motor toma de ahí la lista de unidades del contrato")
# Unidades de CONTRATO.md (SI o agrícolas estándar) + las SI/adimensionales que el contrato admite por ser SI
UNIDADES_CONTRATO = unidades_de_contrato(CONTRATO_MD.read_text(encoding="utf-8"))
UNIDADES_SI_EXTRA = ("m", "cm", "pH", "adimensional", "fracción", "0-1", "kg/t", "m3")
METODO_DOTACION = "dotacion_asignada"
METODO_CE_NO_DECLARADO = "ce_extracto_no_declarado"
VARIABLES_CE_SUELO = ("ce_suelo", "ece", "ece_suelo", "conductividad_electrica_suelo", "ce_extracto")
ACEPTADA, RECHAZADA, IGNORADA = "aceptada", "rechazada", "ignorada"


@dataclass
class Registro:
    archivo: str
    fila: str  # id de la fila o número
    cultivo: str
    variable: str
    estado: str  # aceptada | rechazada | ignorada
    motivo: str

    def a_dict(self) -> dict:
        return asdict(self)


def _num(x):
    if x is None:
        return None
    x = str(x).strip()
    if x == "":
        return None
    try:
        return float(x.replace(",", "."))
    except ValueError:
        return "no_numerico"


def zonas_aplicables(r: dict) -> list[str]:
    """Lista de códigos de `zonas_aplicables` (separados por ';'). Vacía si la columna falta o está vacía."""
    return [z.strip() for z in (r.get("zonas_aplicables") or "").split(";") if z.strip()]


def zonas_de_fila(r: dict) -> list[str]:
    """Zonas en que vale la fila: `zonas_aplicables` si la trae (análogo multizona); si no, la `zona`.
    Una zona agregada (medio_bajo_piura) se devuelve tal cual: Catalogo.ficha la expande con menor prioridad."""
    za = zonas_aplicables(r)
    if za:
        return za
    z = (r.get("zona") or "").strip()
    return [z] if z else []


def validar_zona_columna(r: dict) -> list[str]:
    """Para archivos con esquema del repo que ahora traen `zona` (ronda 6 de Agronomía): código válido o vacío."""
    z = (r.get("zona") or "").strip()
    p = [] if z in ZONAS else [f"zona inválida '{z}' (debe ser un código de CONTRATO.md)"]
    malas = [x for x in zonas_aplicables(r) if x not in ZONAS or x in ("", "piura_region")]
    return p + ([f"zonas_aplicables con códigos inválidos {malas}"] if malas else [])


def faltan_columnas(cabecera: list[str]) -> list[str]:
    return [c for c in COLUMNAS_CONTRATO if c not in cabecera]


# Fuentes genéricas (tabla de especie sin sitio) según cultivos/validar.py R7: pueden ir con zona y zonas_aplicables
# vacías. Copia literal de la tupla GEN de ese script.
FUENTES_GENERICAS = ("Allen et al. 1998", "FAO EcoCrop", "Tanji & Kielen", "Tanji y Kielen", "Ayers",
                     "Crop Salt Tolerance", "Steduto", "Rhoades", "Grieve")


def es_generica(r: dict) -> bool:
    """R7: genérica = fuente de tabla de especie, o fila sin lugar de tipo bibliografico/analogo_externo/prediccion."""
    fuente = (r.get("fuente") or "")
    sin_lugar = not (r.get("lugar") or "").strip()
    return fuente.startswith(FUENTES_GENERICAS) or (
        sin_lugar and (r.get("tipo_evidencia") or "").strip() in ("bibliografico", "analogo_externo", "prediccion"))


def validar_fila_contrato(r: dict, numerica: bool = True) -> list[str]:
    """Problemas de una fila CONTRATO.md (lista vacía = cumple). `numerica=False` admite valor categórico
    (reglas: 'prohibido', '1 ene - 28 feb')."""
    p = []
    if not (r.get("variable") or "").strip():
        p.append("sin variable")
    unidad = (r.get("unidad") or "").strip()
    if not unidad:
        p.append("sin unidad")
    elif numerica and unidad not in UNIDADES_CONTRATO + UNIDADES_SI_EXTRA:  # reglas categóricas: no aplica
        p.append(f"unidad '{unidad}' fuera de la lista de CONTRATO.md")
    if not (r.get("fuente") or "").strip():
        p.append("sin fuente")
    if not (r.get("url_o_doi") or "").strip():
        p.append("sin url_o_doi")
    te, est = (r.get("tipo_evidencia") or "").strip(), (r.get("estado") or "").strip()
    if te not in TIPOS_EVIDENCIA:
        p.append(f"tipo_evidencia inválido '{te}'")
    if est not in ESTADOS:
        p.append(f"estado inválido '{est}'")
    metodo = (r.get("metodo") or "").strip()
    if metodo == METODO_DOTACION and est != "estimado":
        p.append(f"metodo dotacion_asignada exige estado 'estimado' (tiene '{est}')")
    if metodo == METODO_CE_NO_DECLARADO:
        if est != "observado":
            p.append(f"metodo ce_extracto_no_declarado exige estado 'observado' (tiene '{est}')")
        if unidad and unidad != "dS/m":
            p.append("CE con extracto no declarado debe ir en dS/m")
    zona = (r.get("zona") or "").strip()
    if zona not in ZONAS:
        p.append(f"zona inválida '{zona}' (debe ser un código de CONTRATO.md)")
    malas = [z for z in zonas_aplicables(r) if z not in ZONAS or z in ("", "piura_region", "medio_bajo_piura")]
    if malas:
        p.append(f"zonas_aplicables con códigos inválidos {malas} (piura_region y medio_bajo_piura no valen: "
                 "liste las zonas concretas, como exige cultivos/validar.py R7)")
    if "zonas_aplicables" in r and not zona and not (r.get("zonas_aplicables") or "").strip() and not es_generica(r):
        p.append("zona vacía sin zonas_aplicables en una fila no genérica (regla R7 de cultivos/validar.py): declare "
                 "las zonas donde vale el dato")
    v, lo, hi = _num(r.get("valor")), _num(r.get("valor_min")), _num(r.get("valor_max"))
    if numerica and "no_numerico" in (v, lo, hi):
        p.append("valor/valor_min/valor_max no numérico")
    if not numerica and "no_numerico" in (lo, hi):
        p.append("valor_min/valor_max no numérico")
    texto_valor = (r.get("valor") or "").strip()
    if est == "desconocido" and texto_valor:
        p.append("estado desconocido con valor (el contrato exige valor vacío)")
    if est in ("observado", "estimado") and not texto_valor and lo is None and hi is None:
        p.append(f"estado {est} sin valor ni rango")
    if isinstance(lo, float) and isinstance(hi, float) and lo > hi:
        p.append("valor_min > valor_max")
    if (isinstance(v, float) and isinstance(lo, float) and v < lo) or (isinstance(v, float) and isinstance(hi, float) and v > hi):
        p.append("valor fuera de [valor_min, valor_max]")
    if texto_valor and lo is None and hi is None and est != "desconocido" and not (r.get("notas") or "").strip():
        p.append("sin rango y sin notas que expliquen por qué")
    if te == "analogo_externo" and not (r.get("notas") or "").strip():
        p.append("analogo_externo sin notas de comparabilidad")
    if te == "prediccion" and not ((r.get("metodo") or "").strip() or (r.get("notas") or "").strip()):
        p.append("prediccion sin modelo/entradas en metodo o notas")
    return p


# ------------------------------------------------------------------------------------ esquemas del repo
PARAMETROS_RECONOCIDOS = {
    "pH_suelo_absoluto_ecocrop": ("pH", True), "pH_suelo_optimo": ("pH", True),
    "temperatura_adaptacion": ("°C", True), "temperatura_optima": ("°C", True),
    "temperatura_umbral_estres_reproductivo": ("°C", True),  # Tmáx del aire en floración (ronda 7b de Agronomía)
    "profundidad_suelo_apta_minima": ("m", False), "profundidad_suelo_favorable_minima": ("m", False),
}


def validar_parametro(r: dict) -> list[str]:
    p = []
    par = r.get("parameter", "")
    if par not in PARAMETROS_RECONOCIDOS:
        return [f"parámetro no reconocido '{par}'"]
    unidad, necesita_max = PARAMETROS_RECONOCIDOS[par]
    if (r.get("unit") or "").strip() != unidad:
        p.append(f"unidad '{r.get('unit')}' distinta de '{unidad}'")
    lo, hi = _num(r.get("min_value")), _num(r.get("max_value"))
    if not isinstance(lo, float):
        p.append("min_value vacío o no numérico")
    if necesita_max and not isinstance(hi, float):
        p.append("max_value vacío o no numérico")
    if isinstance(lo, float) and isinstance(hi, float) and lo > hi:
        p.append("min_value > max_value")
    if unidad == "pH" and any(isinstance(x, float) and not 0 < x < 14 for x in (lo, hi)):
        p.append("pH fuera de 0-14")
    if unidad == "m" and isinstance(lo, float) and not 0 < lo < 10:
        p.append("profundidad fuera de 0-10 m")
    if not (r.get("source_url") or "").startswith("http"):
        p.append("sin source_url")
    if not (r.get("geographic_scope") or "").strip():
        p.append("sin geographic_scope (alcance de la fuente)")
    return p


def validar_kc(r: dict) -> list[str]:
    p = []
    vals = {k: _num(r.get(k)) for k in ("Kc_initial", "Kc_mid_min", "Kc_mid_max", "Kc_end_min", "Kc_end_max")}
    for k, v in vals.items():
        if not isinstance(v, float):
            p.append(f"{k} vacío o no numérico")
        elif not 0.1 <= v <= 1.5:
            p.append(f"{k}={v} fuera de 0.1-1.5")
    if not p:
        if vals["Kc_mid_min"] > vals["Kc_mid_max"] or vals["Kc_end_min"] > vals["Kc_end_max"]:
            p.append("mínimo > máximo en Kc")
    if not (r.get("source_url") or "").startswith("http"):
        p.append("sin source_url")
    if not (r.get("source_table") or "").strip():
        p.append("sin source_table")
    return p


def validar_nutriente(r: dict) -> list[str]:
    p = []
    mt = r.get("measurement_type", "")
    if not mt.startswith(("exportación", "absorción")):
        p.append(f"measurement_type no reconocido '{mt}'")
    for k in ("N_kg_per_t", "P2O5_kg_per_t", "K2O_kg_per_t"):
        v = _num(r.get(k))
        if v == "no_numerico" or (isinstance(v, float) and v < 0):
            p.append(f"{k} inválido")
    if all(_num(r.get(k)) is None for k in ("N_kg_per_t", "P2O5_kg_per_t", "K2O_kg_per_t")):
        p.append("sin ninguna cifra de N/P2O5/K2O")
    if not (r.get("source_url") or "").startswith("http"):
        p.append("sin source_url")
    if not (r.get("source_table") or "").strip():
        p.append("sin source_table")
    if not (r.get("source_region") or "").strip():
        p.append("sin source_region (no se puede clasificar la evidencia)")
    return p


def validar_salinidad(r: dict) -> list[str]:
    p = []
    puntos = [_num(r.get(f"ECe_{k}")) for k in (100, 90, 75, 50, 0)]
    if not all(isinstance(x, float) for x in puntos):
        p.append("ECe_100..ECe_0 incompletos o no numéricos")
    elif any(a >= b for a, b in zip(puntos, puntos[1:])):
        p.append("ECe_100 < ECe_90 < ECe_75 < ECe_50 < ECe_0 no se cumple")
    if (r.get("unidad") or "").strip() != "dS/m":
        p.append("unidad distinta de dS/m")
    if not (r.get("fuente") or "").strip():
        p.append("sin fuente")
    if not (r.get("url_o_doi") or "").strip():
        p.append("sin url_o_doi")
    te, est = (r.get("tipo_evidencia") or "").strip(), (r.get("estado") or "").strip()
    if te not in TIPOS_EVIDENCIA:
        p.append(f"tipo_evidencia inválido '{te}'")
    if est not in ESTADOS:
        p.append(f"estado inválido '{est}'")
    if te == "analogo_externo" and not (r.get("notas") or "").strip():
        p.append("analogo_externo sin notas de comparabilidad")
    return p

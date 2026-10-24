#!/usr/bin/env python3
"""Clasificación ENSO costero (ICEN oficial, ENFEN NT 01-2024) por campaña, tomada de Piura Territorio (solo lectura):
suelos/datos/clima/clasificacion_campanias_icen.csv (campañas 1981-82 a 2025-26). Para campañas anteriores aplica la misma
regla de Territorio (suelos/scripts/escenarios_clima.py) sobre suelos/datos/clima/icen_oficial_categorias.csv y comprueba
que esa regla reproduce el CSV de Territorio en todas las campañas que este cubre.
Escenario de Piura Datos: sin_el_nino (neutro o La Niña), el_nino_debil, el_nino_moderado, el_nino_fuerte_extraordinario,
según magnitud_en_campania (calida_*). Campaña ago-jul con año = año de julio (anio_lluvias)."""
import csv
from pathlib import Path
CL = Path(__file__).resolve().parents[2] / "suelos/datos/clima"
FUENTE = ("ICEN oficial ENFEN (http://met.igp.gob.pe/datos/ICEN.txt), regla NT ENFEN 01-2024; clasificación por campaña de "
          "Piura Territorio (suelos/datos/clima/clasificacion_campanias_icen.csv)")
U = {"calida_extraordinaria": 3.5, "calida_fuerte": 2.1, "calida_moderada": 1.3, "calida_debil": 0.5}

def cat(v):
    for k, u in U.items():
        if v > u: return k
    return "neutra"

def escenario(enso, mag):
    if enso != "el_nino": return "sin_el_nino"
    return {"calida_debil": "el_nino_debil", "calida_moderada": "el_nino_moderado"}.get(mag, "el_nino_fuerte_extraordinario")

def _regla():
    m = [(int(r["year"]), int(r["month"]), float(r["icen"]), r["evento"]) for r in csv.DictReader((CL / "icen_oficial_categorias.csv").open())]
    out = {}
    for Y in range(m[0][0] + 1, m[-1][0] + 1):
        w = [x for x in m if (x[0] == Y - 1 and x[1] == 12) or (x[0] == Y and x[1] <= 4)]
        wc = [x for x in m if (x[0] == Y - 1 and x[1] >= 8) or (x[0] == Y and x[1] <= 7)]
        nino = [x for x in w if x[3].startswith("el_nino")]; nina = [x for x in w if x[3].startswith("la_nina")]
        if len(nino) >= 2 and len(nino) >= len(nina): enso, ev = "el_nino", nino[0][3]
        elif len(nina) >= 2: enso, ev = "la_nina", nina[0][3]
        else: enso, ev = "neutro", ""
        mag = cat(max(x[2] for x in wc if x[3] == ev)) if enso == "el_nino" else ""
        out[Y] = (enso, mag, ev)
    return out

def clasificacion():
    """{anio_lluvias: (escenario, enso_costero, magnitud_en_campania, evento, origen)}"""
    terr = {int(r["anio_lluvias"]): (r["enso_costero"], r["magnitud_en_campania"], r["evento_icen"])
            for r in csv.DictReader((CL / "clasificacion_campanias_icen.csv").open())}
    regla = _regla()
    for y, t in terr.items():
        if y in regla and regla[y] != (t[0], t[1] if t[0] == "el_nino" else "", t[2]):
            raise SystemExit(f"ERROR icen_campanias: la regla no reproduce a Territorio en {y}: {regla[y]} vs {t}")
    out = {y: (escenario(e, m), e, m, ev, "regla de Territorio aplicada por Piura Datos") for y, (e, m, ev) in regla.items()}
    out.update({y: (escenario(e, m), e, m, ev, "Territorio") for y, (e, m, ev) in terr.items()})
    return out

if __name__ == "__main__":
    c = clasificacion()
    for y in sorted(c):
        if 1970 <= y <= 2026 and c[y][0] != "sin_el_nino": print(y, c[y])

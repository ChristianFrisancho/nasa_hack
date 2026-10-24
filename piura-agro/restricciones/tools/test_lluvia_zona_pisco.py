#!/usr/bin/env python3
"""Test de lluvia_zona_pisco.csv. Uso: ../suelos/.venv/bin/python tools/test_lluvia_zona_pisco.py"""
import csv, sys, re, statistics
from pathlib import Path
from icen_campanias import clasificacion
B = Path(__file__).resolve().parents[1]
R = list(csv.DictReader((B / "lluvia_zona_pisco.csv").open()))
CLS = clasificacion()
F = []
def chk(c, m):
    if not c: F.append(m); print("FALLA", m)
chk(len(R) == 7 * 14 * 3, f"filas {len(R)} != 294")
ZON = {"alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura"}
for r in R:
    v, lo, hi = float(r["valor"]), float(r["valor_min"]), float(r["valor_max"])
    chk(0 <= lo <= v <= hi, f"orden min<=valor<=max {r['lugar']} {r['fecha_o_periodo']}")
    chk(r["unidad"] == "mm" and r["tipo_evidencia"] == "prediccion" and r["estado"] == "estimado", "etiquetas")
    chk(r["zona"] in ZON and (r["zona"] != "sierra_piura" or r["subzona"]), f"zona {r['zona']}")
    chk("Modelo: PISCOp" in r["notas"] and "entradas:" in r["notas"], "prediccion sin modelo/entradas en notas")
    anios = [int(x) for x in re.search(r"años \[([^\]]*)\]", r["notas"]).group(1).split(", ") if x]
    per = r["fecha_o_periodo"].split(", ")[1]
    for y in anios:  # ningún año fuera de su escenario
        camps = [y] if per == "ene-abr" else [y, y + 1] if per == "may-dic" else None
        if camps:
            chk(all(CLS[c][0] == "sin_el_nino" for c in camps) == (r["escenario"] == "sin_el_nino"), f"año {y} mal asignado en {per} {r['escenario']}")
    if r["escenario"] == "sin_el_nino" and per == "ene-abr":
        chk(not {1983, 1987, 1992, 1993, 1995, 1998, 2016, 2017, 2019} & set(anios), "sin_el_nino ene-abr incluye un año El Niño")
        chk(len(anios) == 29, f"sin_el_nino ene-abr n={len(anios)} != 29 (39 campañas 1981-2019 menos 10 El Niño)")
    if r["escenario"] == "el_nino_fuerte_extraordinario":
        chk("3,98" in r["notas"], "falta nota ICEN 3,98 ago-2026")
idx = {(r["lugar"].split(",")[0], r["fecha_o_periodo"].split(", ")[1], r["escenario"]): float(r["valor"]) for r in R}
for z in ("Valle del Chira", "Medio Piura", "Bajo Piura", "San Lorenzo", "Alto Piura"):
    chk(idx[(z, "ene-abr", "sin_el_nino")] > idx[(z, "may-dic", "sin_el_nino")], f"{z}: ene-abr no supera may-dic")
    chk(idx[(z, "ene-abr", "el_nino_fuerte_extraordinario")] > 3 * idx[(z, "ene-abr", "sin_el_nino")], f"{z}: El Niño fuerte no triplica ene-abr")
# contraste con la serie PISCOp de Territorio (ponderada por WorldCover): mediana sin El Niño ene-abr dentro de x0,5-x2
T = {}
for r in csv.DictReader((B.parent / "suelos/datos/clima/clima_por_zona_series.csv").open()):
    if r["producto"] == "PISCOp_lluvia" and int(r["month"]) <= 4:
        T.setdefault(r["subzona"], {}).setdefault(int(r["year"]), 0.0)
        T[r["subzona"]][int(r["year"])] += float(r["valor"])
for z, d in T.items():
    med = statistics.median(v for y, v in d.items() if CLS[y][0] == "sin_el_nino")
    mio = idx[(z, "ene-abr", "sin_el_nino")]
    print(f"  {z:18s} ene-abr sin El Niño: Piura Datos {mio:6.1f} | Territorio (WorldCover) {med:6.1f} mm")
    chk(0.5 <= mio / med <= 2, f"{z}: difiere más de x2 de la serie de Territorio")
print(f"{len(R)} filas"); print("PASA" if not F else f"FALLAN {len(F)}"); sys.exit(1 if F else 0)

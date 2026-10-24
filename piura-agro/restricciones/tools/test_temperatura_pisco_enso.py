#!/usr/bin/env python3
"""Test de temperatura_pisco_zona_enso.csv: 3 escenarios x 7 puntos (6 zonas) x 12 meses x 2 variables; Tmín < Tmáx;
P10 <= media <= P90; etiquetas del CONTRATO; la media ponderada por n de campañas de los tres escenarios reproduce
temperatura_pisco_zona.csv dentro de 0,1 °C (las campañas El Niño débil faltan en los tres; se reporta el error máximo);
las campañas de cada escenario coinciden con las de lluvia_zona_pisco.csv en los años que ambos cubren (1981-2019).
Uso: ../suelos/.venv/bin/python tools/test_temperatura_pisco_enso.py"""
import ast, csv, re, sys
from collections import defaultdict
from pathlib import Path
B = Path(__file__).resolve().parents[1]
F, BASE, LL = B / "temperatura_pisco_zona_enso.csv", B / "temperatura_pisco_zona.csv", B / "lluvia_zona_pisco.csv"
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","setiembre","octubre","noviembre","diciembre"]
ESCS = {"sin_el_nino", "el_nino_moderado", "el_nino_fuerte_extraordinario"}
ZONAS = {"alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura"}
fallas, filas = [], list(csv.DictReader(F.open(encoding="utf-8")))
if len(filas) != 3 * 7 * 12 * 2: fallas.append(f"{len(filas)} filas, se esperan 504")
claves = {(r["escenario"], r["subzona"], r["mes"], r["variable"]) for r in filas}
if len(claves) != len(filas): fallas.append("filas duplicadas")
for e in ESCS:
    for z in ZONAS:
        n = sum(1 for r in filas if r["escenario"] == e and r["zona"] == z)
        if n != (48 if z == "sierra_piura" else 24): fallas.append(f"{e} {z}: {n} filas")
par = defaultdict(dict)
pond = defaultdict(lambda: [0.0, 0])
def campanias(nota):
    return ast.literal_eval(re.search(r"n=\d+ campañas (\[.*?\])", nota).group(1))
for r in filas:
    v, lo, hi = float(r["valor"]), float(r["valor_min"]), float(r["valor_max"])
    if not lo <= v <= hi: fallas.append(f"P10<=media<=P90: {r['escenario']} {r['subzona']} {r['mes']} {r['variable']}")
    if (r["unidad"], r["tipo_evidencia"], r["estado"], r["cultivo"]) != ("°C", "prediccion", "estimado", "todos"): fallas.append(f"etiquetas {r['subzona']}")
    if r["escenario"] not in ESCS or r["zona"] not in ZONAS or r["mes"] not in MESES or "PISCOt" not in r["fuente"]: fallas.append(f"escenario/zona/mes/fuente {r['subzona']}")
    t = "max" if "_max_" in r["variable"] else "min"
    par[(r["escenario"], r["subzona"], r["mes"])][t] = v
    n = len(campanias(r["notas"]))
    if f"n={n} " not in r["notas"]: fallas.append("n no cuadra con la lista")
    if n < 5 and "poco fiables" not in r["notas"]: fallas.append(f"falta aviso de pocas campañas: {r['escenario']} {r['subzona']}")
    p = pond[(r["subzona"], r["mes"], r["variable"])]; p[0] += v * n; p[1] += n
for k, d in par.items():
    if not d.get("min", 99) < d.get("max", -99): fallas.append(f"Tmín >= Tmáx o falta: {k}")
base = {(r["subzona"], r["fecha_o_periodo"].split(", ")[1], r["variable"]): float(r["valor"]) for r in csv.DictReader(BASE.open(encoding="utf-8"))}
err = max(abs(pond[k][0] / pond[k][1] - base[k]) for k in base)
if set(base) != set(pond): fallas.append("claves distintas a temperatura_pisco_zona.csv")
if err > 0.1: fallas.append(f"media ponderada difiere {err:.3f} °C de temperatura_pisco_zona.csv")
# campañas por escenario vs lluvia (lluvia lista años calendario; se pasan a campaña ago-jul)
ll = {}
for r in csv.DictReader(LL.open(encoding="utf-8")):
    if r["variable"] != "precipitacion_mensual" or r["subzona"] not in ("", "Sierra Ayabaca"): continue
    mes = r["fecha_o_periodo"].split(", ")[1]; k = MESES.index(mes) + 1
    ys = ast.literal_eval(re.search(r"años (\[.*?\]) \(n=", r["notas"]).group(1))
    ll[(r["escenario"], mes)] = {f"{y + (1 if k >= 8 else 0) - 1}-{str(y + (1 if k >= 8 else 0))[2:]}" for y in ys}
nll = 0
for r in filas:
    if r["subzona"] != "Chulucanas" or "_max_" not in r["variable"]: continue
    mias = {c for c in campanias(r["notas"]) if int(c[:4]) + (0 if MESES.index(r["mes"]) + 1 >= 8 else 1) <= 2019}
    if mias != ll[(r["escenario"], r["mes"])]: fallas.append(f"campañas distintas a lluvia: {r['escenario']} {r['mes']}: {sorted(mias ^ ll[(r['escenario'], r['mes'])])}")
    nll += 1
print(f"{len(filas)} filas; error máx. media ponderada vs temperatura_pisco_zona.csv = {err:.3f} °C; {nll} listas de campañas comparadas con lluvia")
for f in fallas: print("FALLA", f)
print("PASA" if not fallas else f"FALLAN {len(fallas)}"); sys.exit(1 if fallas else 0)

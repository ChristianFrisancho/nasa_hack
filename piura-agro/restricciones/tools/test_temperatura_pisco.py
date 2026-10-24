#!/usr/bin/env python3
"""Test de temperatura_pisco_zona.csv: 7 puntos x 12 meses x (Tmax, Tmin), Tmin < Tmax, P10 <= valor <= P90, etiquetas del
CONTRATO, rangos físicos por piso, y coherencia con la climatología PISCO 1981-2010 a 0,05° (archivo distinto): ±1,5 °C en costa; en sierra, dentro del rango de las 3x3 celdas 0,05° ±0,5 °C
(el relieve hace que celdas vecinas difieran hasta 9 °C); fuera de ese rango, sólo si notas dice 'Discrepa con PISCO'.
Uso: ../suelos/.venv/bin/python tools/test_temperatura_pisco.py"""
import csv, sys
from collections import defaultdict
from pathlib import Path
B = Path(__file__).resolve().parents[1]
F = B / "temperatura_pisco_zona.csv"
CLIM = B.parent / "suelos/datos/clima/raw/{v}_mean_1981-2010_005.nc"
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","setiembre","octubre","noviembre","diciembre"]
ZONAS = {"alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura"}
RANGO = {("costa", "max"): (20, 40), ("costa", "min"): (10, 28), ("sierra", "max"): (8, 32), ("sierra", "min"): (-2, 22)}
fallas, filas = [], list(csv.DictReader(F.open(encoding="utf-8")))
if len(filas) != 168: fallas.append(f"{len(filas)} filas, se esperan 168")
par, meses = defaultdict(dict), defaultdict(set)
try:
    import rasterio; clim = {v: rasterio.open(str(CLIM).format(v=v)) for v in ("tmax", "tmin")}
except Exception as e:
    clim = None; fallas.append(f"no se pudo abrir la climatología de contraste: {e}")
for r in filas:
    v, lo, hi = float(r["valor"]), float(r["valor_min"]), float(r["valor_max"])
    mes = r["fecha_o_periodo"].split(", ")[1]; t = "max" if "_max_" in r["variable"] else "min"
    par[(r["subzona"], mes)][t] = v; meses[r["zona"]].add(mes)
    if not lo <= v <= hi: fallas.append(f"P10<=valor<=P90: {r['subzona']} {mes} {t}")
    if (r["unidad"], r["metodo"], r["tipo_evidencia"], r["estado"]) != ("°C", "media_mensual_de_diarios", "prediccion", "estimado"):
        fallas.append(f"etiquetas: {r['subzona']} {mes} {t}")
    if r["zona"] not in ZONAS or not r["lat"] or not r["lon"] or "POWER - PISCOt" not in r["notas"] or "no medición en chacra" not in r["notas"]:
        fallas.append(f"zona/lat/lon/notas: {r['subzona']} {mes}")
    a, b = RANGO[("sierra" if r["zona"] == "sierra_piura" else "costa", t)]
    if not a <= v <= b: fallas.append(f"fuera de rango físico {a}-{b}: {r['subzona']} {mes} {t} = {v}")
    if clim:
        ds = clim["t" + t]; b = MESES.index(mes) + 1; lon_, lat_ = float(r["lon"]), float(r["lat"])
        c = float(next(ds.sample([(lon_, lat_)], indexes=b))[0])
        if r["zona"] != "sierra_piura":
            if abs(c - v) > 1.5: fallas.append(f"difiere {v - c:+.1f} °C de PISCO 1981-2010 0,05°: {r['subzona']} {mes} {t}")
        else:  # sierra: la celda 0,1° promedia relieve; basta con caer dentro del rango de las 0,05° que cubre (3x3) ± 0,5 °C
            i, j = ds.index(lon_, lat_); a = ds.read(b, window=((i - 1, i + 2), (j - 1, j + 2)))
            if not a.min() - 0.5 <= v <= a.max() + 0.5 and "Discrepa con PISCO" not in r["notas"]:
                fallas.append(f"fuera del rango 3x3 de PISCO 0,05° ({a.min():.1f}-{a.max():.1f}): {r['subzona']} {mes} {t} = {v}")
for k, d in par.items():
    if not d.get("min", 99) < d.get("max", -99): fallas.append(f"Tmin >= Tmax o falta una: {k}")
for z in ZONAS:
    if len(meses[z]) != 12: fallas.append(f"{z}: {len(meses[z])} meses")
print(f"{len(filas)} filas; zonas con 12 meses: {sum(len(meses[z]) == 12 for z in ZONAS)}/6")
for f in fallas: print("FALLA", f)
print("PASA" if not fallas else f"FALLAN {len(fallas)}"); sys.exit(1 if fallas else 0)

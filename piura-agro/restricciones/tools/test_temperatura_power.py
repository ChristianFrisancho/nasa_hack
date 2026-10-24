#!/usr/bin/env python3
"""Test mínimo de temperatura_media_max_min_zona.csv: 12 meses x 6 zonas, Tmin < Tmax, P10 <= valor <= P90, etiquetas del CONTRATO."""
import csv, sys
from collections import defaultdict
from pathlib import Path
F = Path(__file__).resolve().parents[1] / "temperatura_media_max_min_zona.csv"
ZONAS = {"alto_piura", "medio_piura", "bajo_piura", "chira", "san_lorenzo", "sierra_piura"}
fallas = []
filas = list(csv.DictReader(F.open(encoding="utf-8")))
par = defaultdict(dict)
for r in filas:
    par[(r["subzona"], r["fecha_o_periodo"])][r["variable"]] = r
    v, lo, hi = float(r["valor"]), float(r["valor_min"]), float(r["valor_max"])
    if not lo <= v <= hi: fallas.append(f"P10<=valor<=P90 falla: {r['subzona']} {r['fecha_o_periodo']} {r['variable']}")
    if (r["unidad"], r["metodo"], r["tipo_evidencia"], r["estado"]) != ("°C", "media_mensual_de_diarios", "prediccion", "estimado"):
        fallas.append(f"etiquetas: {r['subzona']} {r['variable']}")
    if "reanálisis, no estación" not in r["notas"] or not r["lat"] or not r["lon"]: fallas.append(f"notas/lat/lon: {r['subzona']}")
meses = defaultdict(set)
for (sub, per), d in par.items():
    tx, tn = d.get("temperatura_max_media_mensual"), d.get("temperatura_min_media_mensual")
    if not tx or not tn: fallas.append(f"falta Tmax o Tmin: {sub} {per}"); continue
    if not float(tn["valor"]) < float(tx["valor"]): fallas.append(f"Tmin >= Tmax: {sub} {per}")
    meses[tx["zona"]].add(per.split(", ")[1])
for z in ZONAS:
    if len(meses[z]) != 12: fallas.append(f"{z}: {len(meses[z])} meses, se esperan 12")
print(f"{len(filas)} filas; zonas con 12 meses: {sum(len(meses[z]) == 12 for z in ZONAS)}/6")
for f in fallas: print("FALLA", f)
print("PASA" if not fallas else f"FALLAN {len(fallas)}"); sys.exit(1 if fallas else 0)

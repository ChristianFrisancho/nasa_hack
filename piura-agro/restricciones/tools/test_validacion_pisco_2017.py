#!/usr/bin/env python3
"""Test: ninguna cifra de Rollenbeck 2022 ni de Chusis pasa como valor exacto u observado.
Uso: python3 tools/test_validacion_pisco_2017.py  (imprime PASA o FALLA y sale con 1 si falla)"""
import csv, sys
from pathlib import Path
B = Path(__file__).resolve().parents[1]
F = list(csv.DictReader((B / "anexos" / "validacion_pisco_2017.csv").open(encoding="utf-8")))
err = []
for r in F:
    e = r.get("estado_referencia", "")
    if e not in ("estimado", "desconocido"): err.append(f"{r['estacion_pisco']} {r['mes']}: estado_referencia '{e}' (debe ser estimado o desconocido)")
    if "Rollenbeck" in r["fuente"] and r["valor_publico_mm"] and (e != "estimado" or "aproximada" not in r["razon_estado"]):
        err.append(f"{r['estacion_pisco']} {r['mes']}: cifra Rollenbeck sin marca de estimado/aproximada")
    if r["estacion_pisco"] == "Chusis" and (r["valor_publico_mm"] or e != "desconocido" or "fuente primaria" not in r["razon_estado"]):
        err.append("Chusis: debe quedar desconocido, sin cifra pública y con la razón")
lz = (B / "lluvia_zona_pisco.csv").read_text(encoding="utf-8")
if "aproximad" not in lz or "orden de magnitud" not in lz: err.append("lluvia_zona_pisco.csv: falta la nota de cifra aproximada / orden de magnitud")
print("\n".join(err) if err else f"{len(F)} filas revisadas")
print("FALLA" if err else "PASA"); sys.exit(1 if err else 0)

#!/usr/bin/env python3
"""Marca el estado de las cifras públicas de la validación PISCOp mar-2017 (anexos/validacion_pisco_2017.csv).
Rollenbeck et al. 2022 (Remote Sensing 14:824) cita en el texto los totales de 'Piura' (ene 78.6, feb 205, mar 481, abr 6.5 mm) y de
Chulucanas ('reached 1130 mm', sin decir el mes con todas las letras). No nombra la estación de Piura ni da la fuente primaria; no son
datos SENAMHI verificados. Por eso van como estimado ('cifra citada, aproximada'), no como valor exacto. Chusis no tiene cifra
pública: desconocido. Idempotente. Uso: python3 tools/validacion_pisco_2017.py
"""
import csv
from pathlib import Path
B = Path(__file__).resolve().parents[1]
P = B / "anexos" / "validacion_pisco_2017.csv"
NOTA_R = ("Cifra citada en el texto de Rollenbeck et al. 2022 (artículo de radar, fuente secundaria); no nombra la estación ni la "
          "fuente primaria, por eso es aproximada y va como estimado, no como medición exacta.")
NOTA_C = ("Sin fuente primaria: ni el Informe Técnico Extraordinario 001-2017/ENFEN ni el boletín SENAMHI de El Niño de marzo de 2017 "
          "publican el total de Chusis, Bernal o Sechura (búsquedas rondas 6 y 7). El valor PISCOp queda sin contraste.")
filas = list(csv.DictReader(P.open(encoding="utf-8")))
base = [c for c in filas[0].keys() if c not in ("estado_referencia", "tipo_cifra_referencia", "razon_estado")]
cols = base[:base.index("valor_publico_mm") + 1] + ["estado_referencia", "tipo_cifra_referencia"] + base[base.index("valor_publico_mm") + 1:] + ["razon_estado"]
for r in filas:
    if r["valor_publico_mm"].strip():
        r["estado_referencia"], r["tipo_cifra_referencia"], r["razon_estado"] = "estimado", "citada_en_texto_aproximada", NOTA_R
    else:
        r["estado_referencia"], r["tipo_cifra_referencia"], r["razon_estado"] = "desconocido", "sin_cifra_publica", NOTA_C
        r["razon_pisco_ref"] = ""
with P.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows({c: r.get(c, "") for c in cols} for r in filas)
print(f"OK {len(filas)} filas -> anexos/validacion_pisco_2017.csv "
      f"(estimado {sum(r['estado_referencia']=='estimado' for r in filas)}, desconocido {sum(r['estado_referencia']=='desconocido' for r in filas)})")

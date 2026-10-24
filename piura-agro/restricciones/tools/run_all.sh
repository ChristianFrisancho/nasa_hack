#!/usr/bin/env bash
# Regenera todo lo de Piura Datos (restricciones/) desde insumos y fuentes, corre los tests y termina en PIPELINE_OK.
# Uso (desde cualquier lugar): bash restricciones/tools/run_all.sh
# Necesita, en carpetas hermanas y sólo para leer: ../cultivos/raw/drap_dataset.csv, ../suelos/datos/{cew_por_zona,pendiente_por_zona}.csv,
# ../suelos/datos/clima/ (PISCOp, PISCOt, CHIRPS, ICEN, series), ../modelo/ranking_features.csv y el entorno ../suelos/.venv (rasterio).
# No baja nada de internet: temperatura_power corre con --offline sobre el caché clima/power_raw/.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=python3
VPY=../suelos/.venv/bin/python
paso() { echo "== $*"; "$@"; }
for f in ../cultivos/raw/drap_dataset.csv ../suelos/datos/cew_por_zona.csv ../suelos/datos/pendiente_por_zona.csv \
         ../suelos/datos/clima/raw/PISCOp_monthly.nc ../modelo/ranking_features.csv "$VPY"; do
  [ -e "$f" ] || { echo "FALTA dependencia externa: $f"; exit 2; }
done
# 1. extracción cruda
paso $PY tools/extraer_drap.py
paso $PY tools/extraer_pdfs.py
# 2. curado manual (cada cifra leída en su fuente) y puntos ANA
for s in insumos_curados insumos_curados_r1b insumos_curados_r2 insumos_curados_r3 insumos_curados_r4 insumos_curados_r7 \
         balance_ionico_ana cew_ana_puntos insumo_pendiente; do paso $PY tools/$s.py; done
# 3. unión y validación contra el CONTRATO
paso $PY tools/limpiar.py --estricto
paso $PY tools/cew_resumen_zona.py
paso $PY tools/test_limpiar.py
paso $PY tools/cobertura.py
paso $PY tools/cobertura_md.py
paso $PY tools/rendimiento_desconocido.py
# 4. clima (necesita rasterio)
paso $VPY tools/temperatura_power.py --offline
paso $VPY tools/test_temperatura_power.py
paso $VPY tools/temperatura_pisco.py
paso $VPY tools/test_temperatura_pisco.py
paso $VPY tools/pisco_vs_chirps.py
paso $VPY tools/chirps_vs_senamhi.py
paso $VPY tools/lluvia_zona_pisco.py
paso $VPY tools/test_lluvia_zona_pisco.py
paso $PY tools/validacion_pisco_2017.py
paso $PY tools/test_validacion_pisco_2017.py
# 5. ronda 6b (otro ejecutor, ver ronda6b_grok.md): sólo si existe
# No reescribe su CSV si ya existe (no tocar archivos de 6b); en una copia limpia lo genera con su propio script.
if [ -f tools/test_temperatura_pisco_enso.py ]; then
  if [ ! -f temperatura_pisco_zona_enso.csv ] && [ -f tools/temperatura_pisco_enso.py ]; then paso $VPY tools/temperatura_pisco_enso.py; fi
  paso $VPY tools/test_temperatura_pisco_enso.py
else echo "== (sin test_temperatura_pisco_enso.py: se omite)"; fi
# 6. control final: el validador del flujo n8n (mismo código) sobre la salida, si hay node
if command -v node >/dev/null; then
  $PY -c "import csv,json; json.dump(list(csv.DictReader(open('evidencia_observada.csv',encoding='utf-8'))),open('/tmp/_filas_n8n.json','w'),ensure_ascii=False)"
  node n8n/harness.js /tmp/_filas_n8n.json | $PY -c "import json,sys; d=json.load(sys.stdin); print('== validador n8n:', d['filas_validas'], 'de', d['filas_recibidas'], 'válidas'); sys.exit(0 if d['pasa'] else 1)"
fi
echo "filas: $(($(wc -l < evidencia_observada.csv)-1)) en evidencia_observada.csv"
echo PIPELINE_OK

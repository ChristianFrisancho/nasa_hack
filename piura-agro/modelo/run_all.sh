#!/usr/bin/env bash
# Reproduce todo el modelo de Piura Modelos. Semilla fija 42. Uso: bash run_all.sh
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
export CLIMA=${CLIMA:-zona}           # ronda 4: clima activo (zona = ERA5-Land/ERA5/CHIRPS por zona; power = NASA POWER)
export LLUVIA=${LLUVIA:-pisco}        # ronda 5: lluvia activa (pisco = PISCOp v2.1 mensual 1981-2019 + relleno 2020-2025 por mapeo de cuantiles desde POWER)
PYM=${PYM:-python3}                   # ronda 5: python del motor consolidado (consolidado/motor no usa el .venv de modelo)
$PY scripts/descargar_power.py        # NASA POWER diario (no rebaja si ya existe)
$PY scripts/descargar_clima_zona.py   # ronda 4: clima por zona (no rebaja si ya existe; tramos en data/clima_zona/_cache)
$PY scripts/rendimientos_observados.py  # DRAP: rendimiento y precio por distrito y año; ronda 3: incluye ALGODON generico y precio en soles de 2018 (IPC BCRP)
$PY scripts/cargar_evidencia.py       # ronda 3: lint del CONTRATO sobre restricciones/evidencia_observada.csv -> data/evidencia_modelo.csv
$PY scripts/rend_zona.py              # ronda 2: rendimiento de referencia por zona (DRAP)
$PY scripts/lluvia_mensual.py         # ronda 5: lluvia mensual por zona PISCOp, CHIRPS, POWER y r4 -> data/lluvia_mensual_zona.csv
for LL in r4 chirps power; do         # ronda 5: alternativas de lluvia con clima por zona (estabilidad y comparar_lluvia)
  LLUVIA=$LL $PY scripts/agua.py
  LLUVIA=$LL $PY scripts/validacion.py
done
CLIMA=power LLUVIA=power $PY scripts/agua.py        # ronda 4: todo POWER (alternativa clima_power)
CLIMA=power LLUVIA=power $PY scripts/validacion.py  # ronda 4: habilidad del clima con POWER, para comparar
$PY scripts/agua.py                   # ET0 PM, ETc, Peff y riego neto (clima y lluvia activos; va al final para que demanda_agua.csv sea la de PISCOp)
$PY scripts/importancia.py            # ablacion y permutacion por cultivo, zona y escenario (normal, fen_2017, fen_2023); OAT y Sobol en normal
$PY scripts/publicar_ranking.py       # ranking_features.csv
$PY scripts/central.py                # escenario central por zona y mes
$PY scripts/intervalo.py              # ronda 2: Monte Carlo del margen (P10/P50/P90, p_top1)
$PY scripts/adversarial.py            # ronda 2: pasada adversarial, un supuesto a la vez
$PY scripts/perennes_agua.py          # agua de perennes contra dotacion ANA; ronda 3: mango con Kc Silva Junior et al. 2023 y calor en floracion
$PY scripts/validacion.py             # LOYO y GroupKFold (referencia distrito-año y zona-año), con y sin eventos
$PY scripts/estabilidad.py            # ronda 3: bootstrap de semillas y rangos alternativos; robustez del top-5 (~6 min)
$PY experimentos/comparar_lluvia.py   # ronda 5: correlacion de lluvia entre zonas, riego neto y LOYO por fuente de lluvia
$PY experimentos/exp_cew_variantes.py # ronda 5: variantes a-d de CEw en mi modelo propio (cew_por_zona.csv)
# ronda 5: CEw y tabla final contra el MOTOR CONSOLIDADO (consolidado/motor), con ECe zonal (desconocida en 4 zonas) y con el rango hipotesis 0.5-12
(cd ../consolidado/motor && for M in desconocida rango_global; do
   ECE_MODO=$M $PYM ../../modelo/experimentos/cew_motor.py
   ECE_MODO=$M $PYM ../../modelo/experimentos/cew_motor_variantes.py
 done && $PYM ../../modelo/experimentos/motor_tabla_final.py)

#!/usr/bin/env bash
# Regenera salidas/ (ronda 6: con ESCENARIOS CLIMÁTICOS ICEN y lluvia PISCOp). Ejecutar desde consolidado/motor/.
# evidencia_integrar_r5.csv reemplaza a evidencia_observada_r3.csv: trae los mismos costos salvo el análogo Phaseolus
# (ENA 2018), que la ronda 5 retiró, más los puntos de CEw.
set -euo pipefail
INT="datos_agronomia/motor_integracion.csv datos_repo/evidencia_integrar_r5.csv"
python3 scripts/extraer_evidencia_r5.py
(cd datos_repo && sha256sum evidencia_observada.csv cew_por_zona.csv temperatura_pisco_zona.csv \
  lluvia_zona_pisco.csv evidencia_integrar_r5.csv > SHA256SUMS)
for f in ejemplos/*.json; do
  n=$(basename "$f" .json)
  python3 -m motor_rotacion "$f" --secuencias 2 --integrar $INT --registro salidas/integracion_registro.tsv > "salidas/$n.txt"
  python3 -m motor_rotacion "$f" --secuencias 2 --integrar $INT --formato json > "salidas/$n.json"
done
python3 -m pytest -v tests > salidas/pytest.txt 2>&1 || true
tail -1 salidas/pytest.txt

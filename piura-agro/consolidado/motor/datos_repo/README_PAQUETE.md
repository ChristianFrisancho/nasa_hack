# Datos agronómicos Piura v2

Empieza por `informe_piura_v2.md` para interpretar los resultados y por `operacion_v2.md` para revisar los flujos n8n. `verify_v2.py` comprueba tamaños, esquema y marcas de calidad. Todos los archivos CSV están codificados en UTF-8; `clima_piura_1981_2025.csv.gz` es un CSV comprimido con gzip.

El paquete separa clima regional NASA POWER, suelo cartográfico, parámetros tomados de FAO/SENASA, candidatos de plagas, análogos externos y escenarios hipotéticos. Las columnas vacías o `unknown` son desconocidas reales: no rellenarlas con cero. Los resultados Tavily en `fuentes_tavily.csv` son documentos encontrados, no hechos verificados automáticamente.

Los coeficientes de absorción de nutrientes son biomasa total por tonelada de producto principal y no dosis de fertilizante. `ETc_reference_mm` es demanda evapotranspirativa estándar y no riego bruto. `analogos_comparacion_v2.csv` incluye cero coincidencias completas; no trasladar sus resultados como observaciones de Piura. Las clases de suelo cartográficas no son análisis de una parcela.

Para evaluar una finca concreta faltan su polígono, horizonte y análisis de suelo, disponibilidad y calidad de agua, historial, cultivar, calendario, plagas diagnosticadas y presupuesto. `model_inputs_v2.schema.json` describe las entradas.



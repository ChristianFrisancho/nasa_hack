# Operación de la base agrícola Piura v2

Flujos activos en n8n:

- [Fuentes oficiales y clima NASA](https://moraprix.app.n8n.cloud/workflow/FZuImrDNKPsFj306): diario 06:00, hora de Lima. Actualiza NASA POWER (ventana reciente con latencia), archivo SENASA y catálogo SIAR con upsert.
- [Investigación Tavily](https://moraprix.app.n8n.cloud/workflow/4TeSMeSTACXljaBk): lunes 07:00, hora de Lima. 74 consultas, 32 básicas y 42 avanzadas, hasta 8 y 5 resultados respectivamente. La ejecución manual 8 terminó con `success`; versión publicada activa `323ed9d6-b2f6-44a9-9858-106115183d07`.

Tavily usa la credencial `Header Auth account` dentro de n8n. La clave no está en código ni en estos archivos. La corrida acumuló 568 registros temáticos de 379 URL distintas en la tabla de evidencia. Algunos documentos aparecen bajo varios temas; dos consultas no devolvieron resultados. El texto Tavily de cada resultado está truncado a 24 000 caracteres y puede faltar: el índice no equivale a validación agronómica.

Tablas n8n del proyecto:

| Tabla | ID | Filas comprobadas |
|---|---|---:|
| Piura_agro_evidencia | SW9ZbPKCuDmDufK4 | 3 232 |
| Piura_requisitos_cultivo | YztU0FIRW54yKfi4 | 186 |
| Piura_plagas_hospedantes_v2 | L4mYAPuMWvue3Vvb | 42 |
| Piura_suelos_regionales_v2 | LWaoscsYYg6T73jj | 12 |
| Piura_analogos_validacion_v2 | pszOSeG9qpKM7MrG | 68 |
| Piura_suelo_perfiles | LIqVcWGoO2dul5La | 0; exige muestras de parcela |

Los 82 180 registros climáticos históricos diarios se entregan en `clima_piura_1981_2025.csv.gz`; se descargaron de NASA POWER para cinco **puntos de referencia**, no se hicieron pasar por estaciones del agricultor ni se insertaron masivamente en n8n. Sus unidades y coordenadas se conservan. ET0 es una aproximación FAO-56 a partir de datos diarios POWER y humedad relativa media; antes de 1984 la radiación falta, así que ET0 es nula/desconocida, no cero.

Los parámetros numéricos de cultivos en n8n provienen de fuentes verificadas, pero sus etiquetas distinguen referencias externas, proxies, valores retenidos por conflicto y umbrales que requieren suelo/variedad local. La tabla se amplió manualmente después de leer FAO/SENASA; **la programación Tavily automatiza búsqueda y actualización de documentos candidatos, no la interpretación automática de dosis**. Antes de recomendar cultivos, revisar las ejecuciones semanales, mantener la credencial/cuota y revalidar restricciones sanitarias.

Anomalías documentales a no ignorar: Tabla 16 del estudio de suelos del Bajo Piura no suma el total declarado; la duración de caupí de FAO-56 no coincide con la suma de etapas; las dos cifras de agua anual de papaya se refieren a ámbitos/métricas diferentes y no se aplican. `analogos_comparacion_v2.csv` conserva diferencias de resultado vacías hasta que existan datos comparables de campo.

# Piura: apoyo a la rotación de cultivos

Entrada del equipo al reto «Field Shift: Adapting Farms with NASA Data» (NASA Space Apps 2026). Dada una parcela en Piura, el sistema dice cuál es el mejor cultivo siguiente, por qué, qué recursos pide, qué le deja al suelo y qué dato podría cambiar la recomendación.

El repositorio tiene tres capas:

- **[`dashboard/`](dashboard/)** es el tablero interactivo «Raíz» con D3.js. El modo rápido funciona sin servidor con las 80 etiquetas DRAP, unidad/condición de suelo y mes; el [HTML autónomo](dashboard/standalone.html) también lo incluye. Para recalcular con zona y mediciones propias, ejecuta `python dashboard/server.py` y visita `http://localhost:8000/dashboard/`. El ranking muestra puestos, márgenes, agua, alertas, descartes y faltantes.

- [`piura-agro/`](piura-agro/) es la versión más nueva (24 de octubre de 2026). Trae un contrato de datos común, datos por zona y un motor de rotación que se puede correr y que tiene tests. Empieza por aquí.
- [`piura-data/`](piura-data/) es el paquete de referencia v2. Ahí están la capa de plagas, los nutrientes FAO, el clima diario NASA POWER en cinco puntos, las exportaciones de n8n y el informe agronómico. Sigue valiendo para lo que `piura-agro/` todavía no cubre.

## Lo principal

- **[`piura-agro/consolidado/recomendaciones_por_parcela.csv`](piura-agro/consolidado/recomendaciones_por_parcela.csv)**: para cada parcela de ejemplo y su cultivo anterior, todos los cultivos siguientes evaluados. Cada fila trae el puesto, la decisión (aceptado, descartado o sin datos), un resumen y el porqué completo filtro por filtro. También trae el margen P10/P50 en PEN/ha, el agua de riego en m3/ha, lo que el cultivo saca del suelo (N, P2O5 y K2O en kg/ha), lo que deja, la ECe tras la cosecha, el primer cultivo en cada escenario de El Niño y los datos que cambiarían la recomendación. El orden pone primero a los cultivos con menos alertas graves, luego a los que no pierden casi seguro, luego a los de menos alertas, y después ordena por margen conservador (P10).
- **[`piura-agro/consolidado/cultivos_resumen.csv`](piura-agro/consolidado/cultivos_resumen.csv)**: una fila por cultivo. Da el ciclo, el Kc, la tolerancia a la sal (ECe sin pérdida y pérdida por dS/m), la temperatura y el pH óptimos y la raíz. También da cuánto N, P2O5 y K2O saca del suelo, cuánto N fija si es leguminosa, qué conviene sembrar después y qué evitar, con sus fuentes.
- **[`piura-agro/consolidado/piura_super_dataset.csv`](piura-agro/consolidado/piura_super_dataset.csv)**: todas las cifras en formato largo, 17 150 filas. Solo tiene columnas con datos y las clave van primero (tema, cultivo, zona, variable, valor, rango, unidad, estado). Las columnas casi vacías pasaron a `notas`. Lo regenera [`armar_tablas_limpias.py`](piura-agro/consolidado/tools/armar_tablas_limpias.py).
- **[El motor](piura-agro/consolidado/motor/)**: `python3 -m motor_rotacion ejemplos/bajo_piura_tras_arroz.json` da, por parcela, los cultivos aceptados y descartados con su motivo, el margen P10/P50/P90 en PEN/ha, la ECe proyectada, las secuencias viables y la recomendación en tres escenarios ICEN. Los perennes van aparte. Los tests se corren con `python3 -m pytest consolidado/motor/tests`.
- **[El contrato de datos](piura-agro/CONTRATO.md)** y las **[reglas](piura-agro/REGLAS.md)**.
- **Registros de decisiones**: cada carpeta tiene un `decisions.tsv` con una fila por decisión (qué, por qué, evidencia, resultado).

## Estado

- La ronda 6 del motor está completa y probada (62 tests). La ronda 7 (necesidad de riego por escenario, costo del agua y el «dato que cambiaría la recomendación») quedó a medias: sus 6 tests nuevos fallan porque se escribieron antes que el código.
- Hallazgos: el drenaje, la pendiente, el costo y la ECe del suelo son los factores que más pesan. Lo que cambia la recomendación es si se conoce o no la salinidad del agua de riego, más que su valor. CHIRPS subestima la lluvia en la costa, así que el motor usa PISCOp. HWSD falla contra los datos de chacra.
- Faltan la salinidad del agua de canal en Medio y Bajo Piura, la ECe medida en pasta saturada y el costo del agua.

Los datos crudos pesados (NetCDF de PISCO, HWSD) y los PDF de las fuentes no están en el repo: se citan por URL en cada fila. Ningún valor reemplaza un análisis de suelo, un derecho de riego ni un ensayo en la parcela.

## Referencia v2 (`piura-data/`)

Este repositorio contiene la investigación y los datos de referencia para evaluar cultivos según clima, suelo, agua, nutrientes, plagas, restricciones de la parcela y prioridades del agricultor. Empieza por el [informe agronómico](piura-data/informe_piura_v2.md) y las [reglas del modelo](piura-data/criterios_modelo.md). El [inventario de factores](piura-data/inventario_features.csv) y el [esquema de entradas](piura-data/model_inputs_v2.schema.json) muestran qué debe medir o proporcionar el agricultor.

Los datos incluyen 82 180 registros climáticos diarios NASA POWER de cinco puntos de referencia en Piura (1981–2025), 186 parámetros de cultivo, 42 relaciones de plagas, unidades cartográficas de suelo, 210 escenarios ilustrativos de ETc y 3 232 registros de evidencia recolectada. La [guía del paquete](piura-data/README_PAQUETE.md) explica cada capa y sus límites. Los coeficientes de nutrientes y agua no sustituyen un análisis de suelo, un derecho de riego ni un ensayo en la parcela.

Los flujos activos de n8n son [investigación Tavily semanal](https://moraprix.app.n8n.cloud/workflow/4TeSMeSTACXljaBk) y [fuentes oficiales más NASA diarios](https://moraprix.app.n8n.cloud/workflow/FZuImrDNKPsFj306). Sus exportaciones están en `piura-data/`; para importarlas en otra instancia hay que vincular su propia credencial Tavily y configurar las tablas de datos. No se incluye ninguna clave API. La [guía de operación](piura-data/operacion_v2.md) registra los horarios y los controles de calidad.

Para comprobar los archivos:

```bash
python -m pip install -r requirements.txt
python piura-data/verify_v2.py
```

Los scripts `build_*.py` dentro de `piura-data/` documentan cómo se generaron las tablas de referencia a partir de las fuentes guardadas o citadas. Los CSV distinguen observaciones regionales, parámetros de otras regiones y valores desconocidos; las comparaciones externas aún no están validadas como equivalentes a Piura.

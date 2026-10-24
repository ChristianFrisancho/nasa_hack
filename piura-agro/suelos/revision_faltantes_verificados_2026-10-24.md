# Evidencia nueva para los campos que seguían como “sin medir”

Verificación de fuentes públicas realizada el 24 de octubre de 2026. Se revisaron los PDFs depositados por la Universidad César Vallejo y se contrastaron con los registros regionales de SoilGrids, HWSD y ANA que ya usa el tablero.

## Acidez (pH)

- **Tablazo Sur, La Unión:** la tabla 2 de Mendoza Flores (2025) publica resultados de pH entre **7.12 y 8.88**. Sus ocho filas describen grupos cuya columna “cantidad” suma 40 predios. La tesis no aclara si cada cifra representa una muestra individual o un resumen de grupo, ni especifica el protocolo de pH. El tablero lo rotula como evidencia de sector, nunca como pH de toda la zona ni de la parcela elegida. Fuente: [ficha UCV](https://hdl.handle.net/20.500.12692/170594), [PDF público](https://repositorio.ucv.edu.pe/bitstream/handle/20.500.12692/170594/Mendoza_FEC-SD.pdf?sequence=1&isAllowed=y), tabla 2.
- **Sullana, parcela de limón:** la tesis de Atoche Alvarado (2025) informa **pH 7.8 en la muestra inicial Base #00**; las muestras tratadas quedaron entre 7.5 y 7.8. Se incorpora solo el valor inicial como un punto de Sullana, no como promedio del valle del Chira. Fuente: [ficha UCV](https://hdl.handle.net/20.500.12692/170943), [PDF público](https://repositorio.ucv.edu.pe/bitstream/handle/20.500.12692/170943/Atoche_ALA.pdf?sequence=2&isAllowed=n), tabla 4 y conclusión 4.
- **Cobertura regional:** el tablero conserva por separado la mediana zonal y el rango espacial de HWSD v2 y SoilGrids 2.0. Para Bajo Piura, por ejemplo, HWSD estima 7.20 (6.70–7.50) y SoilGrids 7.75 (7.58–7.98). Son modelos basados en mapas/perfiles y sus escalas no equivalen a una prueba de laboratorio; el desacuerdo se muestra, no se promedia.

## Profundidad de suelo y napa

- **Profundidad física:** HWSD v2 clasifica como >100 cm la unidad cartográfica típica de suelo cultivado en Bajo Piura. Es una clase a escala regional, no una calicata ni profundidad efectiva garantizada. No detecta con precisión una costra, roca o napa dentro del lote.
- **Napa freática:** el informe ERH de ANA/AAA (2015) tabula 41 sondeos eléctricos verticales del **valle conjunto Medio y Bajo Piura**, sin coordenadas individuales disponibles en el anexo consultado. Su mediana fue 2.3 m, el intervalo intercuartílico 0.6–6.0 m; 20/41 quedaron por encima de una napa a menos de 2 m y 11/41 a menos de 1 m. Son inferencias geofísicas, no lecturas piezométricas. El tablero ya los denomina explícitamente “Medio y Bajo Piura (41 SEV sin ubicar)” para no atribuirlos al Bajo Piura por separado.
- Referencia: [ERH Piura, tomos I–II, ANA/AAA Jequetepeque-Zarumilla](https://www.ana.gob.pe/sites/default/files/normatividad/files/erh_piura_tomos_i_ii_rd_0.pdf), cuadros 7.6–7.18.

## Qué todavía no se puede rellenar con scraping

Un scraper no puede saber el pH ni la profundidad efectiva del lote elegido sin polígono o análisis de campo. Para que el resultado deje de decir “sin medición de parcela”, el dato útil es: muestra compuesta de suelo con pH y método declarado (por ejemplo, relación suelo:agua), más calicata/sondeo hasta identificar capa limitante y napa estacional. Los datos anteriores dan contexto local verificable, pero no deben reemplazar esas mediciones.

Tampoco se creó un valor numérico para el método de pH de las tesis cuando no lo publican. Las dos fuentes citadas son registros universitarios y PDFs descargados desde el repositorio institucional; los valores se transcribieron de las tablas/conclusiones indicadas.

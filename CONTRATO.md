# Contrato común de datos

Todo dato que entre a `consolidado/` cumple esto. Si no lo cumple, no entra.

## Campos obligatorios por cifra
`variable, valor, valor_min, valor_max, unidad, cultivo, variedad, etapa, zona, lugar, lat, lon, fecha_o_periodo, fuente, url_o_doi, metodo, tipo_evidencia, estado, notas`

- `valor_min` y `valor_max` dan el rango de incertidumbre. Si no hay rango, quedan vacíos y `notas` dice por qué.
- `zona` es una de: `alto_piura`, `medio_piura`, `bajo_piura`, `chira`, `san_lorenzo`, `sierra_piura`, `medio_bajo_piura` (cuando la fuente reporta Medio y Bajo Piura juntos), `piura_region` (dato regional sin zona) o vacío si no aplica.
- Unidades SI o agrícolas estándar: mm, mm/día, kg/ha, t/ha, dS/m, cmol/kg, %, °C, días, ha, PEN/ha, PEN/kg, PEN/t, PEN/m3, USD/ha, m3/ha, m3/ha/año, hm3, meses, años, %/(dS/m) (pendiente de pérdida de rendimiento de Maas-Hoffman) y categoría (para valores categóricos como si/no/parcial; las categorías permitidas van en notas). Nada de unidades mezcladas en una columna.
- Columnas opcionales: `fuente_primaria` (cuando la fuente cita a otra), `subzona` (sector, comisión o caserío) y `zonas_aplicables` (códigos de zona del contrato separados por `;`, para un análogo que vale en varias zonas; si se usa, `zona` va vacía y cada código debe ser uno de los de la lista de zonas).

## tipo_evidencia (separación estricta, en este orden de prioridad)
1. `medicion_local`: medida en una parcela o estación de Piura.
2. `regional`: estadística o mapa oficial de Piura o la costa norte (MIDAGRI, SENAMHI, ANA, INEI, INIA).
3. `bibliografico`: parámetro de literatura o manual (FAO-56, fichas técnicas).
4. `analogo_externo`: resultado de otra región. Solo entra con la columna `notas` explicando por qué las condiciones son comparables y cuánto difiere de lo observado en Piura.
5. `prediccion`: salida de un modelo nuestro o de NASA. Siempre dice qué modelo y con qué entradas.

## estado
`observado`, `estimado` o `desconocido`. Si falta una medición de parcela se escribe `desconocido` con valor vacío. Nunca se rellena con una cifra que parezca exacta.

## Casos especiales
- Dotaciones o módulos de riego que no son entregas medidas: `estado` = `estimado` y `metodo` = `dotacion_asignada`. No se crea un estado nuevo.
- CE de suelo sin extracto declarado: `estado` = `observado`, `metodo` = `ce_extracto_no_declarado`. El motor no la usa como ECe de pasta saturada sin avisar.

## Validación
Train y test se separan por finca y por año. Un mismo año o finca no aparece en ambos lados.

## Registro
Cada decisión va al `decisions.tsv` de la carpeta del bot con `tools/log.sh` (show-me-your-work).

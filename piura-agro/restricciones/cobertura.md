# Cobertura de la evidencia (final, ronda 7)

Generado con `python3 tools/cobertura.py && python3 tools/cobertura_md.py` desde `evidencia_observada.csv` (11288 registros). El detalle por celda y grupo de variable está en `cobertura.csv`; la lista completa de huecos, en `anexos/huecos_priorizados.csv`.

**Cómo leer la matriz.** Cada fila es una combinación cultivo × suelo × zona. Las columnas cuentan registros por tipo_evidencia, sólo de los grupos de variable que usa el modelo (rendimiento, precio, costo, agua, eficiencia, CE de suelo, CE de agua, drenaje y sales, pendiente). ML = medición local, R = regional, B = bibliográfico, AE = análogo externo, P = predicción; "desc." = filas en estado desconocido (sin cifra). Los CDR del compendio INEI van a su zona; "CDR Piura" y toda fuente que junta Medio y Bajo Piura van a medio_bajo_piura. "fuera de Piura" = análogos de otros valles. "todos" = dato que vale para cualquier cultivo de la zona (CE de agua, pendiente, dotación).

**Suelo.** Casi ningún registro dice la clase de suelo. Se marca `salino_sódico` cuando la variable es CE o PSI del suelo, o el texto habla de suelo salino o sódico; `tablazo_arenoso` cuando dice tablazo o arenoso; el resto es `genérico`. Por eso la dimensión suelo está casi vacía: es un hueco en sí mismo, no un defecto del conteo.

## Matriz cultivo × suelo × zona

| cultivo | suelo | zona | ML | R | B | AE | P | desc. | total |
|---|---|---|---|---|---|---|---|---|---|
| arroz | genérico | chira | 0 | 165 | 0 | 0 | 0 | 0 | 165 |
| arroz | genérico | medio_piura | 0 | 22 | 0 | 0 | 0 | 0 | 22 |
| arroz | genérico | bajo_piura | 0 | 209 | 0 | 0 | 0 | 0 | 209 |
| arroz | genérico | medio_bajo_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| arroz | genérico | san_lorenzo | 0 | 44 | 0 | 0 | 0 | 0 | 44 |
| arroz | genérico | alto_piura | 1 | 97 | 0 | 0 | 0 | 0 | 98 |
| arroz | genérico | sierra_piura | 0 | 301 | 0 | 0 | 0 | 0 | 301 |
| arroz | genérico | piura_region | 0 | 36 | 0 | 0 | 0 | 0 | 36 |
| arroz | salino_sódico | alto_piura | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| maíz amarillo duro | genérico | chira | 0 | 201 | 0 | 0 | 0 | 0 | 201 |
| maíz amarillo duro | genérico | medio_piura | 0 | 40 | 0 | 0 | 0 | 0 | 40 |
| maíz amarillo duro | genérico | bajo_piura | 0 | 213 | 0 | 0 | 0 | 0 | 213 |
| maíz amarillo duro | genérico | medio_bajo_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| maíz amarillo duro | genérico | san_lorenzo | 0 | 43 | 0 | 0 | 0 | 0 | 43 |
| maíz amarillo duro | genérico | alto_piura | 0 | 113 | 0 | 0 | 0 | 0 | 113 |
| maíz amarillo duro | genérico | sierra_piura | 0 | 403 | 0 | 0 | 0 | 0 | 403 |
| maíz amarillo duro | genérico | piura_region | 0 | 27 | 0 | 0 | 0 | 0 | 27 |
| maíz amarillo duro | genérico | fuera de Piura | 0 | 0 | 0 | 2 | 0 | 0 | 2 |
| algodón | genérico | chira | 0 | 21 | 0 | 0 | 0 | 2 | 23 |
| algodón | genérico | medio_piura | 0 | 16 | 0 | 0 | 0 | 0 | 16 |
| algodón | genérico | bajo_piura | 0 | 198 | 0 | 0 | 0 | 0 | 198 |
| algodón | genérico | medio_bajo_piura | 0 | 2 | 0 | 0 | 0 | 0 | 2 |
| algodón | genérico | san_lorenzo | 0 | 15 | 0 | 0 | 0 | 0 | 15 |
| algodón | genérico | alto_piura | 0 | 14 | 0 | 0 | 0 | 2 | 16 |
| algodón | genérico | piura_region | 0 | 23 | 0 | 0 | 0 | 5 | 28 |
| algodón | genérico | fuera de Piura | 0 | 1 | 0 | 3 | 0 | 0 | 4 |
| frijol | genérico | san_lorenzo | 0 | 2 | 0 | 0 | 0 | 0 | 2 |
| frijol | genérico | sierra_piura | 0 | 365 | 0 | 0 | 0 | 1 | 366 |
| frijol | genérico | fuera de Piura | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| frijol caupí | genérico | chira | 0 | 105 | 0 | 0 | 0 | 0 | 105 |
| frijol caupí | genérico | medio_piura | 0 | 26 | 0 | 0 | 0 | 0 | 26 |
| frijol caupí | genérico | bajo_piura | 0 | 181 | 0 | 0 | 0 | 1 | 182 |
| frijol caupí | genérico | medio_bajo_piura | 0 | 2 | 0 | 0 | 0 | 1 | 3 |
| frijol caupí | genérico | san_lorenzo | 0 | 26 | 0 | 0 | 0 | 0 | 26 |
| frijol caupí | genérico | alto_piura | 0 | 90 | 0 | 0 | 0 | 0 | 90 |
| frijol caupí | genérico | sierra_piura | 0 | 29 | 0 | 0 | 0 | 1 | 30 |
| frijol caupí | genérico | piura_region | 0 | 10 | 0 | 0 | 0 | 1 | 11 |
| frijol caupí | genérico | fuera de Piura | 0 | 0 | 0 | 3 | 0 | 0 | 3 |
| frijol verde | genérico | fuera de Piura | 0 | 0 | 0 | 2 | 0 | 0 | 2 |
| frijol de palo | genérico | chira | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| frijol de palo | genérico | alto_piura | 0 | 2 | 0 | 0 | 0 | 0 | 2 |
| frijol de palo | genérico | sierra_piura | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| frijol de palo | genérico | piura_region | 0 | 8 | 0 | 0 | 0 | 1 | 9 |
| frijol de palo | genérico | fuera de Piura | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| papaya | genérico | chira | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| papaya | genérico | medio_bajo_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| papaya | genérico | san_lorenzo | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| papaya | genérico | alto_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| papaya | genérico | piura_region | 0 | 24 | 0 | 0 | 0 | 1 | 25 |
| papaya | genérico | fuera de Piura | 0 | 0 | 0 | 3 | 0 | 0 | 3 |
| camote | genérico | chira | 0 | 77 | 0 | 0 | 0 | 0 | 77 |
| camote | genérico | medio_piura | 0 | 4 | 0 | 0 | 0 | 0 | 4 |
| camote | genérico | bajo_piura | 0 | 42 | 0 | 0 | 0 | 0 | 42 |
| camote | genérico | medio_bajo_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| camote | genérico | san_lorenzo | 0 | 11 | 0 | 0 | 0 | 0 | 11 |
| camote | genérico | alto_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| camote | genérico | sierra_piura | 0 | 233 | 0 | 0 | 0 | 0 | 233 |
| camote | genérico | piura_region | 0 | 27 | 0 | 0 | 0 | 0 | 27 |
| camote | genérico | fuera de Piura | 0 | 0 | 0 | 5 | 0 | 0 | 5 |
| quinua | tablazo_arenoso | medio_piura | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| limón | genérico | chira | 0 | 136 | 0 | 0 | 0 | 2 | 138 |
| limón | genérico | medio_piura | 0 | 36 | 0 | 0 | 0 | 0 | 36 |
| limón | genérico | bajo_piura | 0 | 136 | 0 | 0 | 0 | 0 | 136 |
| limón | genérico | medio_bajo_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| limón | genérico | san_lorenzo | 0 | 41 | 0 | 0 | 0 | 0 | 41 |
| limón | genérico | alto_piura | 0 | 117 | 0 | 0 | 0 | 0 | 117 |
| limón | genérico | sierra_piura | 0 | 275 | 0 | 0 | 0 | 0 | 275 |
| limón | genérico | piura_region | 0 | 27 | 0 | 0 | 0 | 1 | 28 |
| limón | tablazo_arenoso | chira | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| mango | genérico | chira | 0 | 113 | 0 | 0 | 0 | 0 | 113 |
| mango | genérico | medio_piura | 0 | 37 | 0 | 0 | 0 | 1 | 38 |
| mango | genérico | bajo_piura | 0 | 111 | 0 | 0 | 0 | 3 | 114 |
| mango | genérico | medio_bajo_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| mango | genérico | san_lorenzo | 0 | 41 | 0 | 0 | 0 | 0 | 41 |
| mango | genérico | alto_piura | 0 | 117 | 0 | 0 | 0 | 0 | 117 |
| mango | genérico | sierra_piura | 0 | 189 | 0 | 0 | 0 | 1 | 190 |
| mango | genérico | piura_region | 0 | 24 | 1 | 0 | 0 | 1 | 26 |
| uva | genérico | chira | 0 | 35 | 0 | 0 | 0 | 0 | 35 |
| uva | genérico | medio_piura | 0 | 38 | 0 | 0 | 0 | 0 | 38 |
| uva | genérico | bajo_piura | 0 | 42 | 0 | 0 | 0 | 1 | 43 |
| uva | genérico | medio_bajo_piura | 0 | 3 | 0 | 0 | 0 | 0 | 3 |
| uva | genérico | san_lorenzo | 0 | 33 | 0 | 0 | 0 | 1 | 34 |
| uva | genérico | alto_piura | 0 | 47 | 0 | 0 | 0 | 0 | 47 |
| uva | genérico | piura_region | 0 | 20 | 0 | 0 | 0 | 1 | 21 |
| todos | genérico | chira | 11 | 4 | 0 | 0 | 6 | 1 | 22 |
| todos | genérico | medio_piura | 3 | 0 | 0 | 0 | 6 | 1 | 10 |
| todos | genérico | bajo_piura | 0 | 12 | 0 | 0 | 6 | 1 | 19 |
| todos | genérico | medio_bajo_piura | 1 | 6 | 0 | 0 | 0 | 0 | 7 |
| todos | genérico | san_lorenzo | 5 | 10 | 0 | 0 | 6 | 1 | 22 |
| todos | genérico | alto_piura | 5 | 7 | 0 | 0 | 6 | 1 | 19 |
| todos | genérico | sierra_piura | 10 | 0 | 0 | 0 | 12 | 0 | 22 |
| todos | genérico | piura_region | 0 | 5 | 0 | 0 | 0 | 0 | 5 |
| todos | genérico | fuera de Piura | 0 | 0 | 1 | 2 | 0 | 0 | 3 |
| todos | salino_sódico | medio_bajo_piura | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| todos | salino_sódico | fuera de Piura | 21 | 0 | 0 | 0 | 0 | 0 | 21 |
| todos | tablazo_arenoso | bajo_piura | 5 | 0 | 0 | 0 | 0 | 1 | 6 |
| todos | tablazo_arenoso | fuera de Piura | 0 | 0 | 0 | 3 | 0 | 0 | 3 |

Combinaciones de los cultivos del modelo en sus 5 zonas sin ningún registro de esos grupos: frijol en chira, frijol en medio_piura, frijol en bajo_piura, frijol en alto_piura (4 de 30).

## Huecos priorizados por el modelo

Una combinación cultivo × zona × feature es hueco cuando no hay ni una cifra en esa zona para el grupo de variable que alimenta el feature. Para CE de suelo, drenaje, eficiencia y pendiente cuenta cualquier registro de la zona; para agua cuenta el cultivo o "todos"; para rendimiento, precio y costo, sólo el cultivo. El orden sale de `modelo/ranking_features.csv` (ablación, escenario normal, importancia del feature para ese cultivo en esa zona). "Lo más cercano" dice dónde hay dato que el modelo puede usar de reemplazo. Features del modelo que no son de Restricciones (mes de siembra, TAW, NPK del suelo, precios de fertilizante, cultivo previo, sanidad) no entran en la lista.

| # | cultivo | zona | feature | rango del feature | importancia | lo más cercano |
|---|---|---|---|---|---|---|
| 1 | frijol | san_lorenzo | ece_ds_m | 1 | 286.7 | fuera de Piura |
| 2 | camote | san_lorenzo | ece_ds_m | 1 | 180.6 | fuera de Piura |
| 3 | maíz amarillo duro | san_lorenzo | ece_ds_m | 1 | 136.0 | fuera de Piura |
| 4 | arroz | san_lorenzo | ece_ds_m | 2 | 126.2 | fuera de Piura |
| 5 | algodón | alto_piura | factor_costo | 2 | 114.3 | piura_region |
| 6 | frijol | medio_piura | factor_costo | 2 | 111.9 | fuera de Piura |
| 7 | arroz | alto_piura | factor_costo | 4 | 111.4 | piura_region |
| 8 | algodón | bajo_piura | factor_costo | 3 | 110.9 | piura_region |
| 9 | algodón | san_lorenzo | factor_costo | 3 | 109.2 | piura_region |
| 10 | frijol | chira | factor_costo | 3 | 107.1 | fuera de Piura |
| 11 | frijol | san_lorenzo | factor_costo | 2 | 106.7 | fuera de Piura |
| 12 | frijol | bajo_piura | factor_costo | 1 | 104.3 | fuera de Piura |
| 13 | algodón | medio_piura | factor_costo | 3 | 103.3 | piura_region |
| 14 | arroz | bajo_piura | factor_costo | 3 | 102.7 | piura_region |
| 15 | arroz | medio_piura | factor_costo | 4 | 101.1 | piura_region |
| 16 | maíz amarillo duro | medio_piura | factor_costo | 2 | 97.5 | fuera de Piura |
| 17 | arroz | san_lorenzo | factor_costo | 4 | 96.7 | piura_region |
| 18 | maíz amarillo duro | alto_piura | factor_costo | 1 | 96.5 | fuera de Piura |
| 19 | arroz | chira | factor_costo | 10 | 94.8 | piura_region |
| 20 | frijol | alto_piura | factor_costo | 2 | 93.0 | fuera de Piura |
| 21 | maíz amarillo duro | chira | factor_costo | 3 | 91.1 | fuera de Piura |
| 22 | maíz amarillo duro | san_lorenzo | factor_costo | 2 | 88.3 | fuera de Piura |
| 23 | frijol caupí | san_lorenzo | factor_costo | 2 | 86.4 | fuera de Piura |
| 24 | frijol caupí | san_lorenzo | ece_ds_m | 1 | 85.4 | fuera de Piura |
| 25 | camote | san_lorenzo | factor_costo | 3 | 81.4 | fuera de Piura |
| 26 | camote | alto_piura | factor_costo | 2 | 78.6 | fuera de Piura |
| 27 | algodón | medio_piura | drenaje_malo | 2 | 64.5 | medio_bajo_piura |
| 28 | maíz amarillo duro | medio_piura | drenaje_malo | 3 | 62.6 | medio_bajo_piura |
| 29 | frijol | medio_piura | drenaje_malo | 3 | 60.8 | medio_bajo_piura |
| 30 | frijol | alto_piura | factor_rend | 3 | 60.2 | nada |

Se muestran 30 de 66; el resto está en `anexos/huecos_priorizados.csv`.

Resumen: factor_costo 28; agua_riego_mm 11; ece_ds_m 6; drenaje_malo 6; eficiencia_riego 6; factor_precio 5; factor_rend 4. Total 66 huecos; en 8 no hay ni un reemplazo.

## HWSD contra mediciones de chacra (CE de suelo, dS/m)

HWSD v2 da ECe de la capa superior (D1) promediada sobre el área cultivada de cada zona (`suelos/datos/ece_drenaje_hwsd_por_zona.csv`, media y P5-P95). Las mediciones de chacra son de tesis; ninguna declara el extracto, así que no son ECe de pasta saturada confirmada y no se convierten.

| zona | HWSD D1 media (P5-P95) | Medición de chacra | Fuente | Lectura |
|---|---|---|---|---|
| chira | 1,36 (1,0-4,3) | 0,103 (1 muestra, suelo arenoso, limón) | Atoche 2025, Sullana | HWSD queda muy por encima; una sola muestra |
| medio_piura | 2,74 (1,2-4,3) | 0,95 (parcela UNP) | Vite 2015 | HWSD por encima |
| bajo_piura | 1,51 (1,2-4,3) | 3,44-8,2 (8 puntos, 40 predios) | Mendoza 2025, Tablazo Sur | HWSD por debajo; coincide con FAO/UNALM 1990 (ECe 4-12) |
| alto_piura | 1,15 (0,8-4,3) | 0,46-0,6 (3 estaciones, arroz) | La Rosa 2021, El Huaro | HWSD por encima |
| san_lorenzo | 1,63 (0,6-4,3) | sin medición | — | no se puede contrastar |

Conclusión: HWSD no ordena bien las zonas. Subestima el Bajo Piura y sobrestima Chira, Medio y Alto. Para el modelo, usar la medición de chacra cuando exista y HWSD sólo donde no haya otra cosa, marcado como dudoso.

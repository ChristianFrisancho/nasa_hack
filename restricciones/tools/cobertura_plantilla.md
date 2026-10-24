# Cobertura de la evidencia (final, ronda 7)

Generado con `python3 tools/cobertura.py && python3 tools/cobertura_md.py` desde `evidencia_observada.csv` ({n} registros). El detalle por celda y grupo de variable está en `cobertura.csv`; la lista completa de huecos, en `anexos/huecos_priorizados.csv`.

**Cómo leer la matriz.** Cada fila es una combinación cultivo × suelo × zona. Las columnas cuentan registros por tipo_evidencia, sólo de los grupos de variable que usa el modelo (rendimiento, precio, costo, agua, eficiencia, CE de suelo, CE de agua, drenaje y sales, pendiente). ML = medición local, R = regional, B = bibliográfico, AE = análogo externo, P = predicción; "desc." = filas en estado desconocido (sin cifra). Los CDR del compendio INEI van a su zona; "CDR Piura" y toda fuente que junta Medio y Bajo Piura van a medio_bajo_piura. "fuera de Piura" = análogos de otros valles. "todos" = dato que vale para cualquier cultivo de la zona (CE de agua, pendiente, dotación).

**Suelo.** Casi ningún registro dice la clase de suelo. Se marca `salino_sódico` cuando la variable es CE o PSI del suelo, o el texto habla de suelo salino o sódico; `tablazo_arenoso` cuando dice tablazo o arenoso; el resto es `genérico`. Por eso la dimensión suelo está casi vacía: es un hueco en sí mismo, no un defecto del conteo.

## Matriz cultivo × suelo × zona

{matriz}

Combinaciones de los cultivos del modelo en sus 5 zonas sin ningún registro de esos grupos: {vacias}.

## Huecos priorizados por el modelo

Una combinación cultivo × zona × feature es hueco cuando no hay ni una cifra en esa zona para el grupo de variable que alimenta el feature. Para CE de suelo, drenaje, eficiencia y pendiente cuenta cualquier registro de la zona; para agua cuenta el cultivo o "todos"; para rendimiento, precio y costo, sólo el cultivo. El orden sale de `modelo/ranking_features.csv` (ablación, escenario normal, importancia del feature para ese cultivo en esa zona). "Lo más cercano" dice dónde hay dato que el modelo puede usar de reemplazo. Features del modelo que no son de Restricciones (mes de siembra, TAW, NPK del suelo, precios de fertilizante, cultivo previo, sanidad) no entran en la lista.

{huecos}

Resumen: {resumen}

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

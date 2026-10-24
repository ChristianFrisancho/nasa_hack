# Resultados, Piura Modelos ronda 1

Corrida reproducible con `bash run_all.sh` (semilla 42, salida idéntica en dos corridas, md5 de ranking_features.csv 634ec0c7). Log en `resultados/run_all.log`.

## 1. Demanda de agua FAO-56 (medido con POWER + FAO-56)

ET0 Penman-Monteith anual media 2000-2024 en mm: alto_piura 1756, bajo_piura 2129, chira_sullana 2168, medio_piura 2203, san_lorenzo 2168. Chira y San Lorenzo caen en la misma celda POWER, así que en la práctica hay 4 climas distintos.

Riego neto mediano por campaña (mm, sin eficiencia), rango según el mes de siembra (`resultados/riego_neto_mediana_mm.csv`).

| cultivo | bajo_piura | medio_piura | alto_piura |
|---|---|---|---|
| arroz (con 600 mm extra, hipótesis) | 1479-1639 | 1539-1678 | 1314-1458 |
| algodón | 900-1045 | 951-1067 | 715-855 |
| maíz amarillo duro | 603-734 | 644-755 | 489-611 |
| camote | 601-732 | 642-759 | 495-613 |
| frijol | 470-581 | 499-598 | 383-484 |
| caupí | 388-480 | 412-496 | 309-404 |

Sembrar en abril-junio en el Bajo Piura baja la demanda de maíz y camote cerca de 120 mm frente a sembrar en octubre-enero. La tabla completa por año está en `data/demanda_agua.csv`.

## 2. Importancia de features

Modelo mecánico con 5000 escenarios aleatorios por zona. La importancia es una salida del modelo y no está validada con rendimiento por parcela. "medido" quiere decir que el rango del feature tiene fuente. "hipótesis" quiere decir que el rango es supuesto.

Promedio de las 5 zonas, `ranking_features.csv` filas `zona=todas`.

| feature | permutación cambio top-1 % | ablación cambio top-1 % | estado |
|---|---|---|---|
| agua_riego_mm | 35.2 | 25.8 | hipótesis |
| ece_ds_m | 33.1 | 34.4 | hipótesis |
| drenaje_malo | 25.5 | 15.9 | hipótesis |
| eficiencia_riego | 10.0 | 8.4 | hipótesis |
| mes_siembra | 6.9 | 7.7 | medido |
| anio (clima) | 6.0 | 4.5 | medido |
| factor_costo | 4.0 | 3.4 | hipótesis |
| taw_mm_m | 3.9 | 3.0 | medido |
| factor_rend | 3.6 | 2.6 | hipótesis |
| factor_precio | 2.7 | 2.0 | hipótesis |
| cultivo_previo | 2.5 | 1.6 | medido |
| p_suelo | 1.5 | 1.3 | hipótesis |
| n_suelo | 0.9 | 0.8 | hipótesis |
| pendiente | 0.3 | 0.8 | hipótesis |
| k_suelo, crédito N leguminosa, precios de fertilizante | ≤ 1.1 | ≤ 0.9 | hipótesis |

Sobol total del margen por cultivo (promedio de zonas).
- arroz: agua 0.76, pendiente 0.76, ECe 0.66, eficiencia 0.39, rendimiento 0.29.
- maíz amarillo duro: ECe 0.59, drenaje 0.49, agua 0.36, rendimiento 0.29, costo 0.22.
- algodón: drenaje 0.64, agua 0.38, rendimiento 0.21. ECe solo 0.02 porque tolera hasta 7.7 dS/m.
- frijol: ECe 0.74, drenaje 0.46, agua 0.25.
- caupí: drenaje 0.61, ECe 0.41, agua 0.22.
- camote: drenaje 0.57, ECe 0.56, agua 0.30.

Lectura. Los tres datos que más mueven la recomendación son el agua real por campaña, la salinidad del suelo y el drenaje. Los tres actúan como filtros duros y hoy no tenemos medición por parcela de ninguno. El análisis de N-P-K y el cultivo previo pesan poco en la elección del cultivo porque se pagan con fertilizante. Sí cambian el margen. Los OAT desde el escenario central solo cambian el top-1 con drenaje, ECe y agua.

## 3. Escenario central (prueba, no es recomendación)

Con los valores centrales de `escenario_rangos.csv` (1000 mm de riego con eficiencia 0.5, ECe 2 dS/m) el top-3 en todas las zonas es camote, algodón y caupí, y el arroz no pasa el filtro de agua (`resultados/escenario_central_top3.csv`). Esto no coincide con lo que se siembra en Piura, donde el arroz domina el área. Hay tres causas conocidas.
- El rendimiento de camote de referencia (14.2 t/ha ponderado por producción) viene de distritos costeros como Colán y Arenal (24 t/ha). La mediana distrito-año es 4.0 t/ha.
- El arroz real recibe más agua que el escenario central, y los 600 mm extra son supuestos.
- El modelo no tiene profundidad de mercado, riesgo de precio, mano de obra ni crédito, que explican por qué el arroz domina.

## 4. Validación con rendimiento observado

No hay rendimientos por finca. Uso rendimientos regionales DRAP/MIDAGRI por distrito y año (2015-2024, `data/rendimientos_distrito_anio.csv`, distritos con al menos 10 ha cosechadas). Probé si el clima POWER del año (log lluvia, Tmax media, RH media) explica el rendimiento mejor que la media histórica del distrito (`resultados/validacion_drap.csv`).

| cultivo | n | LOYO MAE ref → con clima (t/ha) | skill LOYO | GroupKFold distrito skill |
|---|---|---|---|---|
| arroz | 286 | 0.772 → 0.826 | −6.9 % | +22.4 % |
| maíz amarillo duro | 323 | 0.498 → 0.530 | −6.4 % | −5.4 % |
| algodón | 89 | 1.473 → 1.407 | +4.5 % | −18.2 % |
| caupí | 180 | 0.498 → 0.526 | −5.6 % | −4.0 % |
| frijol | 37 | 0.314 → 0.370 | −17.8 % | −1.2 % |
| camote | 52 | 4.103 → 4.489 | −9.4 % | +37.2 % |

Lectura. Con años separados, el clima anual no mejora a la media del distrito en 5 de 6 anuales. La identidad del distrito (manejo, agua, suelo) explica más que el clima del año. Esto apoya que agua, sal y drenaje encabecen el ranking. Los años malos se ven en los datos (algodón 2015 0.85 t/ha y 2023 0.96 t/ha, arroz 2017 7.46 t/ha con el Niño costero), pero un promedio anual de lluvia no los captura. GroupKFold por distrito compara contra la media de otros distritos del mismo año y por eso no es comparable con LOYO.

## 5. Limitaciones

- La importancia depende de rangos supuestos. Si Piura Datos trae rangos reales de agua, ECe y drenaje, los números cambian.
- Ky de arroz, caupí y camote, NPK de caupí y camote, y costo de caupí son análogos.
- Costos de 2018 (ENA, promedio Perú) contra precios 2015-2024. El ESCO arroz Piura 2024 da S/ 9037/ha, 1.67 veces el ENA Piura.
- Perennes (limón, mango, banano, uva) no están en el ranking de rotación. Solo tienen rendimiento observado.

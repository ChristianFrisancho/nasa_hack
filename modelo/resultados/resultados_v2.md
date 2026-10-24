# Resultados, Piura Modelos ronda 2

Corrida reproducible con `bash run_all.sh` (semilla 42). Dos corridas dan el mismo md5 en ranking_features.csv (1eebb207), intervalo_margen.csv y adversarial.csv. Log en `resultados/run_all.log`. La ronda 1 queda en `resultados/resultados_v1.md`.

## 0. Qué cambió en el modelo

| cambio | antes (v1) | ahora (v2) | fuente |
|---|---|---|---|
| agua por zona | 0-2000 mm igual en todas | dotación ANA por zona × fracción 0.5-1.0 por campaña | ANA PGRH Chira-Piura p.155 (`params/zonas.csv`) |
| eficiencia | 0.35-0.75 | 0.6·ef a ef, con ef operativa ANA 0.52-0.60 | ANA PGRH; FAO Training Manual 4 Tabla 8 (superficie 60 %) |
| agua del arroz | dotación general + 600 mm extra supuestos | volumen en parcela 10000-18000 m³/ha + extra 150-780 mm | ESCO arroz Piura 2024 (MIDAGRI, cita INIA 2020); FAO Irrigation Water Needs |
| rendimiento de referencia | regional | por zona (producción/cosecha DRAP), regional si hay < 5 distrito-año o < 200 ha | DRAP 2015-2024 (`params/rend_zona.csv`) |
| sanidad | castigo por misma familia | castigo solo si previo y candidato comparten agente | `plagas_hospedantes_condiciones_v2.csv` |
| costos | factor 0.8-1.5 | 1.0-2.11 sobre ENA 2018 | ESCO 1.67×, estudio LATAM maíz 2.11× |
| salida | margen puntual | P10/P50/P90 del margen y P(top-1) con 20000 sorteos por zona y mes | `resultados/intervalo_margen.csv` |

La versión intermedia v2a (agua del arroz igual a la dotación general) queda en `resultados/*_v2a.csv`. La pasé a v2 porque falsaba lo observado (sección 4).

## 1. Ranking de features v2 frente a v1

Promedio de las 5 zonas, % de escenarios en que cambia el top-1 (`resultados/comparacion_v1_v2_permutacion.csv` y `_ablacion.csv`).

| feature | permutación v2 (puesto) | v1 (puesto) | ablación v2 (puesto) | v1 (puesto) | estado |
|---|---|---|---|---|---|
| ece_ds_m | 43.0 (1) | 33.1 (2) | 39.2 (1) | 34.4 (1) | hipótesis |
| drenaje_malo | 29.8 (2) | 25.5 (3) | 18.5 (2) | 15.9 (3) | hipótesis |
| agua_riego_mm | 15.4 (3) | 35.2 (1) | 11.3 (5) | 25.8 (2) | dato de zona + hipótesis |
| eficiencia_riego | 11.0 (4) | 10.0 (4) | 8.4 (7) | 8.4 (4) | dato de zona + hipótesis |
| mes_siembra | 8.9 (5) | 6.9 (5) | 9.6 (6) | 7.7 (5) | medido |
| anio (clima) | 7.5 (6) | 6.0 (6) | 5.6 (8) | 4.5 (6) | medido |
| factor_costo | 6.8 (7) | 4.0 (7) | 11.4 (4) | 3.4 (7) | dato parcial + hipótesis |
| factor_rend | 6.8 (8) | 3.6 (9) | 5.0 (9) | 2.7 (9) | hipótesis |
| taw_mm_m | 5.9 (9) | 3.9 (8) | 4.6 (10) | 3.0 (8) | bibliográfico |
| factor_precio | 5.2 (10) | 2.7 (10) | 3.9 (11) | 2.0 (10) | hipótesis |
| pendiente_pct | 5.1 (11) | 0.3 (17) | 13.2 (3) | 0.8 (14) | hipótesis |
| cultivo_previo | 0.5 (17) | 2.5 (11) | 0.7 (14) | 1.6 (11) | medido |
| agua_arroz_m3_ha (nuevo) | 0.6 | | 0.4 | | dato bibliográfico Piura |
| agua_extra_arroz_mm (nuevo) | 0.5 | | 0.4 | | acotado FAO |
| pen_sanidad (nuevo) | 0.07 | | 0.06 | | hipótesis |

Lectura.
- El agua baja del 1.º al 3.º puesto. Con la dotación ANA por zona el rango es más angosto (480-1540 mm frente a 0-2000), así que mueve menos escenarios. Sigue sin dato por campaña.
- ECe sube al 1.º puesto y drenaje se queda 2.º. Ninguno de los dos tiene dato agrícola de Piura. Son lo que más vale medir.
- La pendiente salta del 17.º al 3.º en ablación. Pasa porque el arroz ahora tiene agua suficiente y lo que lo saca es el tope de pendiente de 1 % (hipótesis) contra un rango de 0-5 % uniforme (hipótesis). Es un artefacto de dos supuestos sin dato, ver sección 4.
- factor_costo sube del 7.º al 4.º en ablación porque el rango ahora llega a 2.11× con fuente.
- cultivo_previo cae del 11.º al 17.º. Con plagas v2 solo arroz-arroz (Pomacea) y maíz-maíz (5 agentes) comparten agente. El castigo por familia de v1 no tenía fuente.

Sobol total del margen por cultivo (promedio de zonas, `resultados/importancia_detalle.csv`).
- arroz: pendiente 0.81, ECe 0.54, rendimiento 0.24, costo 0.20.
- maíz: ECe 0.55, drenaje 0.47, agua 0.24, eficiencia 0.16.
- algodón: drenaje 0.48, rendimiento 0.26, costo 0.23, agua 0.17.
- frijol: ECe 0.72, drenaje 0.38. caupí: drenaje 0.64, ECe 0.47. camote: drenaje 0.61, ECe 0.56.

## 2. Escenario central e intervalo del margen

Escenario central, previo = arroz (`resultados/escenario_central_top3.csv`, margen PEN/ha). Es una prueba del motor y no una recomendación.

| zona | top-3 con siembra en enero |
|---|---|
| Chira-Sullana | camote 13805, arroz 5609, caupí 5004 |
| Bajo Piura | camote 6805, arroz 4269, caupí 4169 |
| Medio Piura | camote 7730, caupí 4596, arroz 4575 |
| Alto Piura | algodón 3022, arroz 2975, caupí 2799 |
| San Lorenzo | camote 7210, arroz 4474, caupí 1853 |

En v1 el top-3 era camote, algodón y caupí en todas las zonas y el arroz no pasaba ningún filtro. En v2 el arroz entra 2.º o 3.º en las cinco zonas.

Intervalo con 20000 sorteos por zona y mes (`resultados/intervalo_margen.csv`, meses 12, 1, 3, 6 y 9). P(top-1) es la fracción de sorteos en que el cultivo gana.

| zona | líder por P(top-1) | 2.º | P(ningún cultivo viable) |
|---|---|---|---|
| Chira-Sullana | camote 0.31-0.37 (P50 5800-7100) | caupí 0.20-0.27 | 0.19-0.20 |
| Bajo Piura | caupí 0.29-0.37 (P50 2100-2500) | camote 0.18-0.26 | 0.20-0.24 |
| Medio Piura | caupí 0.32-0.40 (P50 2100-2600) | camote o algodón ~0.21 | 0.22-0.26 |
| Alto Piura | caupí 0.44-0.54 (P50 1300-1400) | algodón 0.25-0.35 | 0.17-0.19 |
| San Lorenzo | camote ~0.30 | caupí 0.27-0.34 | 0.25-0.31 |

El arroz gana solo en 2-3 % de los sorteos. Pasa el filtro en 11 % y su P50 de margen es negativo. El escenario central y el Monte Carlo no coinciden en el arroz porque el central fija pendiente 1 % (justo el tope del arroz) y el Monte Carlo sortea 0-5 %. El algodón llega a ser top-1 en 15-35 % de los sorteos aunque su P50 sea negativo: gana en los escenarios salinos donde los demás quedan fuera.

## 3. Agua de perennes (aparte del ranking de rotación)

FAO-56 con ET0 POWER 2000-2024, recorriendo los 12 meses de inicio (`resultados/perennes_agua.csv`). Riego neto en m³/ha/año contra la dotación ANA de la zona. Bruto con goteo = neto/0.90 (FAO TM4).

| zona | dotación ANA | banano año 2 neto | limón neto | uva de mesa neto (ciclo 240 d) |
|---|---|---|---|---|
| Chira-Sullana | 15399 | 23761-23974 (1.56×) | 14180-14228 (0.92×) | 9289-10408 (0.68×) |
| Bajo Piura | 11472 | 23410-23699 (2.07×) | 14002-14067 (1.23×) | 9173-10300 (0.90×) |
| Medio Piura | 11472 | 24145-24383 (2.13×) | 14406-14461 (1.26×) | 9425-10528 (0.92×) |
| Alto Piura | 11807 | 18709-18922 (1.60×) | 10966-11014 (0.93×) | 6967-8448 (0.72×) |
| San Lorenzo | 9528 | 23761-23974 (2.52×) | 14180-14228 (1.49×) | 9289-10408 (1.09×) |

Lectura.
- El banano no se cubre con la dotación promedio en ninguna zona, ni siquiera con goteo.
- El limón queda justo en Chira y Alto Piura y no se cubre en Bajo, Medio y San Lorenzo. San Lorenzo es zona limonera y mangera, así que la dotación ANA promedio no puede ser el agua real de esas parcelas (puede haber pozos). Pregunta 12 a Piura Datos.
- La uva con goteo (9400-11700 m³) queda por debajo de los 19000 m³ que Agraria.pe 2016 dice que se le asignan, y con gravedad (23000-33000) por encima.
- El mango queda desconocido porque `cultivos/perennes.csv` no trae Kc ni etapas.

## 4. Pasada adversarial

Hice la revisión cruzada yo mismo. Cambié un supuesto a la vez y miré si cambia el top-1 central y P(top-1) (`resultados/adversarial.csv`, mes 1, previo arroz, 20000 sorteos). Ordeno por cuánto mueve el resultado.

**A. v2a falsaba lo observado y por eso la cambié.** Con el arroz regado desde la dotación promedio ANA, el modelo decía que el arroz no era viable en ninguna zona (yw 0.10-0.49). El arroz es el cultivo dominante, con 7.2-9.5 t/ha observadas por zona. Calibré el agua que necesita el arroz central para pasar el filtro: 1200-1275 mm brutos (900 en Alto Piura) con 450 mm extra, y 1800-1875 mm para no tener déficit. Eso equivale a 12000-18750 m³/ha y coincide con el rango ESCO 10000-18000 m³/ha (el ESCO usa 18000 en su tabla de costos, y Agraria.pe 2018 cita 18000 con inundación). La dotación ANA es un promedio de todos los cultivos y no sirve para el arroz. En v2 el arroz usa el volumen ESCO.

**B. ECe es el supuesto que más mueve.** Con ECe fija en 0.5 dS/m el camote gana en 57-77 % de los sorteos en 4 zonas. Con 8 dS/m el camote desaparece, el caupí pasa a 0.48-0.72 de P(top-1) y el top-1 central es algodón o caupí en todas las zonas. Sin una sola medición agrícola de Piura, el ranking de cultivos es en buena parte la elección del rango de ECe.

**C. Pendiente.** Con pendiente fija en 0.3 % (valor por defecto del esquema) el arroz pasa de 2-3 % a 12-16 % de P(top-1). Con 0.3 % y ECe 2 dS/m sube a 20-30 %. El tope de 1 % para el arroz y el rango 0-5 % son hipótesis. El mapa SIAR del Bajo Piura tiene clases 0-2 % y 2-4 % como las más grandes, pero mezcla tierras no agrícolas.

**D. Rendimiento del camote.** Con la mediana en vez del promedio ponderado, el camote cae de 14.2 t/ha a la mediana local y deja de ganar fuera de Chira. El top-1 central pasa a arroz en Bajo, Medio y San Lorenzo, y P(top-1) del camote cae a 0 en esas zonas. El ponderado está dominado por Colán y Arenal (24 t/ha).

**E. Drenaje.** Si toda la parcela drena mal, solo queda el arroz y sale top-1 en las cinco zonas. Aun así P(ninguno) es 0.89 porque el arroz falla por pendiente o sal en el resto de sorteos. La P=0.2 de drenaje malo no tiene fuente y tapa la viabilidad del caupí en ~0.59.

**F. Corte de pérdida del filtro duro.** Con corte de 30 % el líder no cambia. Con 70 % el top-1 central pasa a arroz en Bajo Piura y San Lorenzo y P(ninguno) sube a 0.27-0.55 porque el margen negativo se vuelve visible. El 50 % es convención.

**G. Costos.** Con factor 1.67 o 2.11 fijo el top-1 central del Alto Piura pasa de algodón a caupí. Con 2.11 el caupí sube a 0.44 de P(top-1) en Bajo y Medio y pasa a liderar el Monte Carlo en San Lorenzo. El top-1 central de las otras zonas no cambia.

**H. Ky análogos ±20 %.** Con Ky ×1.2 el top-1 central del Alto Piura pasa de algodón a arroz y el caupí lidera el Monte Carlo en San Lorenzo. Con ×0.8 el algodón lidera el Monte Carlo en Bajo y Medio. Mueve más que el agua extra del arroz o la sanidad.

**I. Agua del arroz dentro del rango ESCO.** Entre 10000 y 18000 m³ el arroz casi no cambia (P(top-1) 0.02-0.04), salvo con 10000 m³ y 780 mm de extra, donde cae a 0.002. El volumen del arroz deja de ser crítico una vez que tiene fuente.

**J. Lo que el modelo no tiene.** Profundidad de mercado, riesgo de precio, mano de obra, crédito y acceso a molino explican por qué se siembra arroz aunque el camote y el caupí den más margen esperado. El ranking de cultivos de este modelo es margen esperado con filtros y no una predicción de lo que se siembra.

## 5. Validación con eventos (FEN 2017 y 2023, calor)

Agregué a la validación el ICEN máximo nov-abr (`suelos/datos/clima/clasificacion_campanias_icen.csv`), la lluvia dic-abr POWER por zona y los días con Tmax ≥ P90 del mes (2000-2024) entre febrero y abril. Las dummies de año no sirven en LOYO, porque el año que se deja fuera no tiene coeficiente. Por eso uso variables continuas que sí distinguen 2017 (lluvia dic-abr media 646 mm, ICEN 1.34) y 2023 (425 mm, ICEN 2.11) del resto (59-159 mm).

Skill frente a la media del distrito (`resultados/validacion_drap.csv`).

| cultivo | LOYO clima v1 | LOYO + eventos | GroupKFold v1 | GroupKFold + eventos |
|---|---|---|---|---|
| arroz | −6.9 % | −12.4 % | +22.4 % | +20.7 % |
| maíz amarillo duro | −6.4 % | −7.0 % | −5.4 % | +0.5 % |
| algodón | +4.5 % | −11.9 % | −18.2 % | −24.0 % |
| caupí | −5.6 % | −19.4 % | −4.0 % | −3.1 % |
| frijol | −17.8 % | −23.2 % | −1.2 % | +5.5 % |
| camote | −9.4 % | −14.7 % | +37.2 % | +36.3 % |

Lectura. Con 10 años y 2 eventos las variables de evento empeoran el LOYO en los 6 anuales. Es sobreajuste y no aprendizaje. Los eventos sí se ven en los datos. En 2017 el rendimiento mediano relativo a los años normales fue arroz 0.84, algodón 0.81, mango 0.82, limón 0.85 y maíz 0.90, y en 2023 algodón 0.26 (`resultados/validacion_eventos_2017_2023.csv`). Un modelo anual no puede aprender el efecto con tan pocos eventos. Hace falta un castigo de evento con fuente agronómica, no ajustado.

Calor. Los días calientes de feb-abr fueron 0 en 2017 y 5 en 2023, contra 23-27 en 2016 y 2024. En el FEN costero la nubosidad baja la Tmax de POWER. No encontré un umbral fisiológico verificado para Piura (por ejemplo 35 °C en floración del arroz), así que no lo uso y queda como desconocido.

Inconsistencia para Piura Suelos. `clasificacion_campanias_icen.csv` marca 2023 como `neutra` y `neutro` aunque su propio ICEN máximo nov-abr es 2.11 (más alto que 2017, que marca `el_nino`). ENFEN tuvo vigente la alerta de El Niño costero en 2023. Lo dejo escrito en para_piura_datos.md.

## 6. Limitaciones

- ECe, drenaje y pendiente siguen siendo rangos supuestos y son 3 de las 4 features que más mueven el resultado.
- Ky de arroz, caupí y camote, NPK de caupí y camote y costo de caupí son análogos.
- El rendimiento de referencia del camote y el corte del 50 % voltean el ganador en 3 zonas.
- Perennes fuera del ranking de rotación. Mango sin Kc.
- Créditos Tavily. No usé en esta parte. La suma registrada por todos los agentes (con la cota superior de tavily_research mini) supera el tope de 100. Lo aviso en el reporte.

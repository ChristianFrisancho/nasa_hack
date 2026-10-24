# Resultados, Piura Modelos ronda 3

Todo se reproduce con `bash run_all.sh` (semilla 42; la estabilidad usa semillas 100-119). La ronda 2 queda en `resultados/resultados_v2.md` y la ronda 1 en `resultados/resultados_v1.md`. La respuesta a la revisión de Piura Datos está en `respuesta_revision.md`.

## 0. Qué cambió frente a la ronda 2 (v2b)

| cambio | v2b | ronda 3 | fuente |
|---|---|---|---|
| entrada de evidencia | lectura ad hoc | cargador con lint del CONTRATO, 0 errores, 5375 avisos | `scripts/cargar_evidencia.py`, `resultados/lint_evidencia.csv` |
| algodón | solo ALGODON PIMA (n=89) | PIMA + ALGODON genérico (n=103); Medio 3.5 t/ha | DRAP; objeción 2 |
| camote fuera del Chira | regional 14.17 | mediana de la zona `n_bajo`: Bajo y Medio 12.0, San Lorenzo 7.8 | Piura Datos; objeción 3 |
| precios | nominales 2015-24 | soles de 2018 con IPC Lima BCRP PN01271PM | objeción 6 |
| agua | dotación × 0.5-1.0 | 0.5 × dotación a 1.0 × dotación máxima; San Lorenzo 9528-15191; marcada asignada | ANA PGRH p.155; Castillo Mimbela 2007 |
| drenaje malo | P=0.2 (hipótesis) | P=0.341 (Santayana 2012, costa peruana, drenaje o salinidad) | id edc6840d61e2 |
| año y FEN | `anio` como feature | campaña agrícola como ESCENARIO: normal, tipo 2017, tipo 2023 | ver sección 2 |
| métrica | cambio del top-1 en todos | además por cultivo: cambio de top-1, top-3, viabilidad | `ranking_features.csv` |
| etiquetas | "medido" en 3 variables | `variable_de_decision`, `dato_de_ubicacion`, reanálisis | objeción 5 |
| mango | desconocido | Kc análogo de Petrolina y conteo de calor en floración | sección 6 |

Hallazgo nuevo que afecta a todas las rondas. Chira-Sullana, Medio Piura y San Lorenzo caen en la misma celda MERRA-2 de NASA POWER. Temperatura, humedad, viento y lluvia diarios son idénticos en las tres; solo difiere un poco la radiación. El modelo tiene 3 climas, no 5. Lo que separa esas tres zonas es la dotación, la eficiencia y el rendimiento de referencia.

## 1. Ranking de features (escenario normal, promedio de las 5 zonas)

Ablación = el dato falta y se fija en el central; permutación = se baraja. % de escenarios en que cambia el cultivo top-1 (N=5000 por zona).

| puesto | feature | ablación r3 | ablación v2b | permutación r3 | estado |
|---|---|---|---|---|---|
| 1 | ece_ds_m | 33.4 | 39.2 | 36.2 | hipótesis |
| 2 | drenaje_malo | 31.8 | 18.5 | 42.3 | bibliográfico, no específico de zona |
| 3 | pendiente_pct | 18.5 | 13.2 | 7.4 | hipótesis |
| 4 | factor_costo | 10.3 | 11.4 | 5.1 | mixto observado + hipótesis |
| 5 | agua_riego_mm | 8.2 | 11.2 | 11.0 | dotación asignada + hipótesis |
| 6 | eficiencia_riego | 5.6 | 8.4 | 7.5 | observado regional + hipótesis |
| 7 | factor_rend | 4.1 | 5.0 | 5.3 | hipótesis |
| 8 | mes_siembra | 4.0 | 9.6 | 4.3 | variable de decisión |
| 9 | factor_precio | 3.0 | 3.9 | 4.1 | hipótesis |
| 10 | taw_mm_m | 2.7 | 4.6 | 3.6 | bibliográfico |
| | resto (11 features) | ≤ 1.0 | ≤ 1.4 | ≤ 1.1 | |

`anio` ya no es feature: pasó a escenario (sección 2).

Qué cambió frente a v2b.
- El drenaje sube de 18.5 a 31.8 en ablación porque su P pasó de 0.2 a 0.341. Con P mayor, fijarlo en "drena bien" cambia más escenarios.
- `mes_siembra` baja de 9.6 a 4.0. Parte de lo que antes cargaba era el clima del año, que ahora va en el escenario.
- El orden de los 5 primeros no cambia.

Por cultivo (ablación, cambio de top-1 cuando el cultivo entra o sale del 1.º puesto, promedio de zonas):
- algodón: ECe 16.2, drenaje 8.5, costo 5.0, agua 3.6.
- arroz: pendiente 18.5, ECe 4.4, drenaje 3.2. El tope de 1 % de pendiente del arroz es hipótesis.
- camote: ECe 20.9, drenaje 5.8, costo 4.4, agua 4.1.
- caupí: ECe 20.1, drenaje 17.5, costo 10.1, agua 5.6.
- frijol y maíz amarillo duro nunca quedan 1.º, así que su cambio de top-1 es 0. Su detalle de top-3 y viabilidad está en `ranking_features.csv`.

## 2. El FEN como escenario: año tipo 2017 y año tipo 2023

Campaña C = siembras de agosto de C-1 a julio de C. "Normal" = campañas 2001-2024 sin 2017 ni 2023. Advertencia: "normal" incluye otras campañas Niño (ICEN marca 2023-24 como fuerte). El modelo no tiene daño por inundación, así que un año FEN solo trae más lluvia y menos calor en POWER, y eso favorece cultivos sensibles al agua como el algodón. En la realidad el algodón de 2023 rindió 0.26 de su mediana (DRAP). Este es el límite más fuerte de la sección.

% de sorteos en que cada cultivo es top-1 (N=5000 por zona y escenario, `resultados/top_por_escenario.csv`).

| zona | normal | tipo 2017 | tipo 2023 |
|---|---|---|---|
| Chira-Sullana | camote 29, caupí 20, algodón 16 (ninguno 32) | camote 32, algodón 17, caupí 16 (ninguno 32) | camote 32, algodón 17, caupí 16 (ninguno 31) |
| Bajo Piura | caupí 37, algodón 14, camote 10 (ninguno 34) | algodón 26, caupí 20, camote 18 (ninguno 32) | caupí 25, algodón 23, camote 17 (ninguno 31) |
| Medio Piura | caupí 35, algodón 16, camote 7 (ninguno 37) | algodón 37, caupí 16, camote 11 (ninguno 33) | algodón 30, caupí 22, camote 10 (ninguno 33) |
| Alto Piura | caupí 45, algodón 21, arroz 4 (ninguno 29) | caupí 35, algodón 29, arroz 6 (ninguno 30) | caupí 37, algodón 26, arroz 5 (ninguno 32) |
| San Lorenzo | caupí 34, algodón 16, camote 10 (ninguno 34) | caupí 25, algodón 24, camote 14 (ninguno 32) | caupí 27, algodón 21, camote 14 (ninguno 32) |

Top-3 en normal (% de sorteos en que el cultivo queda entre los 3 primeros): caupí 47-50 en todas las zonas; algodón 33-52; camote 30-35 en la costa; maíz 20 en Alto Piura y Chira.

Ranking de features por escenario. Los tres primeros son los mismos en los tres escenarios y en todas las zonas: ECe, drenaje y pendiente. En FEN el costo sube un poco (Alto Piura 12.1 → 15.6-16.5).

## 3. Los 3 datos que más vale buscar en cada zona

Criterio: cambio del top-1 en ablación (normal; FEN igual salvo lo indicado), sin contar variables de decisión (mes de siembra, cultivo previo). El 4.º va como desempate porque cambia por zona.

| zona | 1.º | 2.º | 3.º | 4.º | por qué |
|---|---|---|---|---|---|
| Chira-Sullana | ECe 37.3 | drenaje 32.8 | pendiente 14.7 | agua por campaña 6.2 | la ECe decide si el camote, que lidera, pasa el filtro de sal |
| Bajo Piura | ECe 35.5 | drenaje 31.7 | pendiente 18.2 | costo actual 10.3 | zona salina conocida sin una sola ECe agrícola medida; con drenaje 0.75 el drenaje pasa a 1.º |
| Medio Piura | ECe 34.6 | drenaje 31.7 | pendiente 18.3 | costo actual 13.0 | igual que Bajo; el costo decide entre caupí y algodón |
| Alto Piura | drenaje 32.0 | ECe 22.9 | pendiente 18.7 | costo actual 12.1 | la ECe pesa menos porque el camote no compite; drenaje decide caupí frente a algodón |
| San Lorenzo | ECe 36.8 | drenaje 30.8 | pendiente 22.5 | agua por campaña 12.0 | la dotación tiene dos cifras (9528 y 15191) y eso mueve al arroz |

Los tres primeros son los mismos en las 5 zonas. Eso no es un artefacto del promedio: sale zona por zona y en los tres escenarios. Los tres son filtros duros (sal, anegamiento, nivelación) con rango supuesto o bibliográfico no local. Un dato de parcela de cualquiera de los tres vale más que mejorar precio, rendimiento o Kc.

## 4. Estabilidad del top-5

`scripts/estabilidad.py`: 20 semillas × N=2000 por zona, y 6 variantes de rangos (base; pendiente 0-2 %; drenaje P=0.20; drenaje P=0.75 en Bajo Piura; ECe 0.5-4 dS/m; costo hasta 1.67). Robusta = misma posición en ≥ 80 % de las semillas y dentro del top-5 en ≥ 90 % de todas las corridas (`resultados/estabilidad_top5.csv`, `estabilidad_corridas.csv`).

Todos los cultivos juntos:

| zona | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Chira-Sullana | ECe (no) | drenaje (sí) | pendiente (sí) | agua (sí) | eficiencia (no) |
| Bajo Piura | ECe (no) | drenaje (sí) | pendiente (sí) | costo (no) | agua (no) |
| Medio Piura | ECe (no) | drenaje (sí) | pendiente (sí) | costo (sí) | agua (sí) |
| Alto Piura | drenaje (sí) | ECe (no) | pendiente (sí) | costo (sí) | rendimiento (sí) |
| San Lorenzo | ECe (no) | drenaje (sí) | pendiente (sí) | agua (sí) | costo (sí) |

Lectura.
- Frente a las semillas, las posiciones 1-3 son estables en todas las zonas (95-100 % en la misma posición). El ruido de muestreo no mueve el top-3.
- La ECe sale "no robusta" por una sola variante: si su rango fuera 0.5-4 dS/m cae al puesto 9-20. Con el rango base queda 1.ª en 95-100 % de las semillas. O sea que el puesto de la ECe depende de un rango que nadie midió. Por eso es el dato que más vale buscar, no un motivo para descartarla.
- El drenaje queda 1.º o 2.º en todas las variantes y todas las zonas (peor puesto 2, salvo San Lorenzo 4 con P=0.20).
- La pendiente queda en el top-5 en el 100 % de las corridas. Con 0-2 % baja al 4.º o 5.º.
- Los puestos 4 y 5 no son robustos en Bajo Piura (costo y agua se alternan en 55 % de las semillas) ni en Chira (eficiencia sale del top-5 en 40 %).
- Por cultivo es más inestable: 34 % de los puestos 1 por cultivo y zona son robustos. Arroz siempre pone la pendiente 1.ª (5 de 5 zonas), los demás la ECe.

## 5. Escenario central e intervalo del margen

Escenario central, previo arroz, siembra en enero (`resultados/escenario_central_top3.csv`, PEN/ha de 2018). Es una prueba del motor, no una recomendación.

| zona | top-3 |
|---|---|
| Chira-Sullana | camote 10398, arroz 4590, caupí 4514 |
| Bajo Piura | camote 4067, caupí 3242, arroz 3000 |
| Medio Piura | camote 4318, caupí 3553, arroz 3269 |
| Alto Piura | caupí 2481, arroz 2312, algodón 1361 |
| San Lorenzo | arroz 3559, camote 2537, caupí 1609 |

Monte Carlo, 20000 sorteos por zona y mes (`resultados/intervalo_margen.csv`, meses 12, 1, 3, 6, 9).

| zona | líder por P(top-1) | P50 del margen del líder | P(ningún cultivo viable) |
|---|---|---|---|
| Chira-Sullana | camote 0.25-0.30 | 5200-6200 | 0.31-0.33 |
| Bajo Piura | caupí 0.35-0.40 | 1750-2100 | 0.33-0.36 |
| Medio Piura | caupí 0.34-0.39 | 1800-2200 | 0.34-0.37 |
| Alto Piura | caupí 0.43-0.46 | 1060-1160 | 0.30-0.32 |
| San Lorenzo | caupí 0.33-0.36 | 190-270 | 0.34-0.36 |

El arroz pasa los filtros en 10-12 % de los sorteos, gana en 4-5 % y su P50 es negativo (-2600 a -840). El central y el Monte Carlo difieren en el arroz porque el central fija pendiente 1 % (el tope del arroz) y el Monte Carlo sortea 0-5 %. En San Lorenzo el caupí lidera con un margen casi nulo: ahí ningún cultivo anual tiene margen esperado claro.

## 6. Mango: Kc, etapas y calor

No hay Kc de mango para Piura ni en FAO-56. Uso Silva Junior et al. 2023 (Engenharia Agrícola 43(3) e20220189, doi 10.1590/1809-4430-Eng.Agric.v43n3e20220189/2023), 'Palmer' en Petrolina, Brasil, con microaspersión y balance de energía de Bowen. Es `analogo_externo`: clima semiárido y riego localizado como la costa de Piura, pero otra variedad (en Piura se siembra Kent, Edward y criollo), otro suelo y otro manejo de inducción floral.

| fase | Kc | días ciclo I | días ciclo II |
|---|---|---|---|
| crecimiento vegetativo | 0.81 | 57 | 61 |
| reposo y maduración de ramas | 0.76 | 79 | 80 |
| inducción floral | 0.85 | 40 | 11 |
| floración | 0.90 | 18 | 15 |
| desarrollo del fruto | 0.95 | 110 | 94 |
| maduración | 0.91 | 59 | 34 |

Riego neto con ET0 POWER y los 12 meses de inicio (`resultados/perennes_agua.csv`), contra la dotación ANA asignada:

| zona | dotación ANA | neto ciclo I (363 d) | neto ciclo II (295 d, cota inferior) |
|---|---|---|---|
| Chira-Sullana | 15399 | 18262-18446 (1.20×) | 14347-15210 (0.99×) |
| Bajo Piura | 11472 | 17982-18223 (1.59×) | 14219-15056 (1.31×) |
| Medio Piura | 11472 | 18544-18761 (1.64×) | 14609-15369 (1.34×) |
| Alto Piura | 11807 | 14260-14449 (1.22×) | 11054-12184 (1.03×) |
| San Lorenzo | 9528 | 18262-18446 (1.94×) | 14347-15210 (1.60×) |

El mango demanda más que el limón (11000-14500) y no se cubre con la dotación promedio salvo en Chira con el ciclo corto. San Lorenzo, zona mangera, queda en 1.6-1.9× la dotación PGRH. Con el máximo de Castillo Mimbela (15191) quedaría en 0.94-1.21×.

Calor en floración (`resultados/mango_calor_floracion.csv`, POWER diario 2000-2024). Umbrales con fuente: germinación de polen < 10 % sobre 32 °C y Tmax cardinal 30.4-34.3 °C (PMC9837111); floración óptima 15-33 °C (Issarakraisila y Considine 1994, doi 10.1006/anbo.1994.1028). Días por mes con Tmax > 32 °C:

| mes | Alto Piura | Bajo Piura | Chira / Medio / San Lorenzo |
|---|---|---|---|
| mayo | 12.6 | 23.9 | 28.8 |
| junio | 13.1 | 11.6 | 20.7 |
| julio | 16.6 | 7.9 | 15.5 |
| agosto | 21.2 | 7.3 | 16.8 |
| septiembre | 19.8 | 8.9 | 19.2 |
| octubre | 10.0 | 12.0 | 21.2 |

Noches con Tmin < 10 °C: 0 en todas las zonas y meses. El frío no limita.

Lectura con cautela. POWER es reanálisis de celda gruesa y tiende a dar Tmax de 31-35 °C todo el año en la costa de Piura. Con esos valores casi todo mes tendría riesgo de calor en floración, y el mango se cosecha cada año en San Lorenzo y Chira. Yo no tomaría el conteo como un filtro duro. La fenología SENAMHI de Alto Piura pone la floración en mayo-junio, que es donde el Alto Piura tiene menos días calientes (12-13). Umbral de calor del resto de etapas: desconocido.

## 7. Validación

`resultados/validacion_drap.csv`. Habilidad frente a la referencia, clima v1.

| cultivo | n / distritos | LOYO | GroupKFold ref. distrito-año (v2) | GroupKFold ref. zona-año (r3) |
|---|---|---|---|---|
| algodón | 103 / 18 | +16.5 % | −16.0 % | 0.0 % |
| arroz | 286 / 31 | −6.9 % | +22.4 % | 0.0 % |
| maíz amarillo duro | 323 / 37 | −6.4 % | −5.4 % | 0.0 % |
| caupí | 180 / 31 | −5.6 % | −4.0 % | 0.0 % |
| frijol | 37 / 5 | −17.8 % | −1.2 % | 0.0 % |
| camote | 52 / 12 | −9.4 % | +37.2 % | 0.0 % |

El +22 % y el +37 % de la v2 eran diferencia entre zonas y no habilidad del clima (objeción 1, aceptada). El 0.0 % es estructural: dentro de una zona y un año el clima es el mismo para todos los distritos. Con 3 celdas POWER no se puede medir la habilidad del clima en el espacio. Agregar ICEN, lluvia dic-abr y días cálidos empeora el LOYO en los 6 anuales (sobreajuste con 2 eventos en 10 años).

## 8. Pasada adversarial (resumen; detalle en `resultados/adversarial.csv`)

Lo que más voltea el resultado, en orden: ECe fija (con 8 dS/m no queda arroz ni camote viable), drenaje (si todo drena mal solo queda arroz), pendiente fija en 0.3 % (el arroz sube a 12-16 % de P(top-1)), rendimiento del camote, corte de pérdida del filtro (70 % hace visible el margen negativo), costo fijo 1.67-2.11 y Ky ± 20 %. El volumen de agua del arroz dentro del rango ESCO casi no mueve nada.

## 9. Limitaciones

- ECe, drenaje y pendiente siguen sin dato agrícola de Piura y son las 3 primeras en todas las zonas y escenarios.
- 3 climas para 5 zonas (celda POWER compartida).
- El FEN entra solo por clima. Sin daño por inundación, el escenario tipo 2023 favorece al algodón, al revés de lo observado.
- Ky de arroz, caupí y camote, NPK de caupí y camote, costo del caupí y Kc del mango son análogos.
- El corte de la cosecha del algodón entre años calendario no está verificado.
- El margen esperado no incluye riesgo de precio, mercado, crédito ni mano de obra. No es una predicción de lo que se siembra.

## 10. Créditos Tavily

Corrección de la ronda 2. El tope de 100 créditos es por agente, no por equipo. Piura Modelos lleva 6 de 100 (`../creditos_tavily.tsv`), todos en la ronda 2. En la ronda 3 no usé Tavily: el mango salió de PDFs ya bajados y los demás datos de archivos del equipo.

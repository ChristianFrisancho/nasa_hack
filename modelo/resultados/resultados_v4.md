# Resultados, Piura Modelos ronda 4

Todo se reproduce con `bash run_all.sh` (semilla 42; la estabilidad usa semillas 100-119). La ronda 2 queda en `resultados/resultados_v2.md` y la ronda 1 en `resultados/resultados_v1.md`. La respuesta a la revisión de Piura Datos está en `respuesta_revision.md`.

## Ronda 4 (24-oct-2026)

La ronda 3 queda abajo y en `resultados/resultados_v3.md`; los CSV de la ronda 3 terminan en `_v3`.

### R4.0 Qué cambió

| cambio | ronda 3 | ronda 4 | fuente |
|---|---|---|---|
| clima | POWER, 3 climas para 5 zonas | 1 punto por zona: ERA5-Land (T, HR) + ERA5 (viento, radiación, lluvia), CHIRPS para la lluvia de Alto y San Lorenzo | `scripts/descargar_clima_zona.py` |
| ECe | rango regional | rango por zona | `params/zonas.csv` |
| drenaje | P = 0.341 en todas | P por zona 0.261-0.505 (DelaTorre 1986) | `params/zonas.csv` |
| pendiente | hipótesis global | Bajo 0.03-0.05 % (Banco Mundial 1979); resto hipótesis | `params/zonas.csv` |
| FEN | sin daño | `fen_2017` con pérdida por inundación en Chira, Medio y Bajo (cota inferior); Alto, San Lorenzo y 2023 no modelados | EMSR199 × WorldCover |
| etiqueta FEN | | 2016-17 moderado (ICEN 1.31), 2022-23 fuerte (ICEN 2.11) | IGP vía Territorio |
| intervalo | igual para todo n | W = CV/√n | `scripts/intervalo.py` |
| algodón Bajo | 2.75 t/ha (con 2015) | 3.09 t/ha (2016-2023) | DRAP; Piura Datos |
| evidencia | zona en notas | columna `zona` | `evidencia_observada.csv` r2 |

### R4.1 Ranking de features (escenario normal, promedio de las 5 zonas, % de sorteos en que cambia el top-1)

| puesto r4 | feature | ablación r3 | ablación r4 | permutación r3 | permutación r4 |
|---|---|---|---|---|---|
| 1 | drenaje_malo | 31.8 | 36.5 | 42.3 | 44.2 |
| 2 | pendiente_pct | 18.5 | 29.7 | 7.4 | 11.7 |
| 3 | factor_costo | 10.3 | 14.6 | 5.1 | 8.6 |
| 4 | ece_ds_m | 33.4 | 12.8 | 36.2 | 14.7 |
| 5 | agua_riego_mm | 8.2 | 7.6 | 11.0 | 9.8 |
| 6 | factor_rend | 4.1 | 7.0 | 5.3 | 9.1 |
| 7 | mes_siembra | 4.0 | 5.6 | 4.3 | 5.6 |
| 8 | factor_precio | 3.0 | 5.0 | 4.1 | 6.8 |
| 9 | eficiencia_riego | 5.6 | 4.8 | 7.5 | 6.4 |
| 10 | taw_mm_m | 2.7 | 2.4 | 3.6 | 3.0 |

Por zona (ablación, normal): ECe pesa 48.2 en Bajo Piura y 0.5-7.9 en las otras. Top-3 por zona:
- Bajo: ECe > drenaje > costo.
- Chira: drenaje > pendiente > mes de siembra.
- Medio: drenaje > pendiente > costo.
- Alto: pendiente > costo > drenaje.
- San Lorenzo: pendiente > drenaje > costo.

Sobol ST, top-1 por cultivo y zona (36 celdas): drenaje 27, ECe 4, pendiente 5 (r3: 16, 14, 6).

Lectura. La ECe deja de ser la primera porque el rango por zona la deja bajo el umbral de casi todos los cultivos fuera de Bajo Piura. La pendiente sube, pero fuera de Bajo sigue siendo un rango hipótesis: su peso es una pregunta abierta, no un hallazgo. El drenaje de DelaTorre mezcla salinidad y drenaje, así que cuenta en parte lo mismo que la ECe.

### R4.2 Estabilidad (20 semillas × 13 alternativas)

Alternativas nuevas: `ece_campo_alto_medio`, `ece_campo_bajo` (CE de campo leída como ECe), `drenaje_bajo_napa_perm_0212`, `drenaje_bajo_napa_total_0534` (estudio 1978 vía Castillo Albines), `clima_power`, `clima_zona`. Posiciones robustas: 102 de 175 (r3: 89 de 175).
- Drenaje: 1.º o 2.º robusto en Chira, Medio, Bajo y San Lorenzo; en Alto es 3.º y no robusto.
- ECe: 1.ª robusta en Bajo (84 % de las corridas en ese puesto, peor puesto 2).
- Pendiente: robusta en Chira, Medio, Alto y San Lorenzo, siempre sobre el rango hipótesis.

### R4.3 Top-1 por escenario (% de sorteos, N=5000)

| zona | normal r3 | normal r4 | fen_2017 r4 | fen_2023 r4 |
|---|---|---|---|---|
| Chira | camote 28.6, ninguno 31.5 | camote 49.0, ninguno 40.6 | camote 48.9 | camote 49.5 |
| Bajo | caupí 36.8 | caupí 24.6, arroz 22.7, algodón 21.0 | algodón 33.0 | algodón 26.6 |
| Medio | caupí 35.4 | camote 36.9, caupí 21.3 | camote 37.3 | camote 31.0 |
| Alto | caupí 45.2 | caupí 58.8 | caupí 46.8 | caupí 49.1 |
| San Lorenzo | caupí 34.2 | camote 44.9 | camote 45.5 | camote 43.6 |

Camote sube en Chira, Medio y San Lorenzo con el mismo rendimiento de referencia que en r3 (12.0 en Medio, 7.8 en San Lorenzo). Cambiaron a la vez el clima por zona (menos riego neto) y la ECe por zona (más baja). No separé cuál de los dos lo causa. Queda para revisar con Piura Agronomía. El algodón cae en Chira (1.0 t/ha, mediana de Piura Datos con n=9). La pérdida por inundación de `fen_2017` pesa igual en los 6 cultivos, así que no cambia el orden.

### R4.4 Clima y validación contra DRAP

- Riego neto con clima por zona frente a POWER: Alto -15.9 %, Bajo -17.1 %, Chira -19.8 %, Medio -21.7 %, San Lorenzo -31.1 %.
- Skill del clima, LOYO, clima_v1, mediana de 6 cultivos anuales: POWER -6.7 %, zona -2.5 %. Solo el algodón tiene skill positivo (19.9 %).
- Con GroupKFold y referencia distrito-año: POWER -2.6 %, zona -0.9 %.
- Conclusión: el clima por zona mejora un poco, pero el skill sigue en 0 o por debajo. El año de clima no explica el rendimiento distrital mejor que la media.
- Alto y San Lorenzo comparten celda ERA5 para viento y radiación.

### R4.5 Lo que no está modelado

- Daño por inundación en Alto, San Lorenzo y en `fen_2023`.
- Sodicidad (PSI 7.3-17.7 en Tablazo Sur).
- Pendiente medida fuera de Bajo Piura.
- CE de campo con método de extracto confirmado.
- CEw (CE del agua de riego): mi modelo propio (`modelo/scripts/modelo.py`) no la usa; el motor consolidado del equipo (`consolidado/motor`) sí la usa. Ver R4.6 y R5.1.

### R4.6 CEw (CE del agua de riego): valor frente a dato ausente

Pedido del coordinador. Script `experimentos/exp_cew.py`, salidas `experimentos/exp_cew_importancia.csv` y `experimentos/exp_cew_resumen.csv` (N=5000, semilla 42, escenario normal).

**Corrección de la ronda 5.** Todo este apartado R4.6 se midió contra MI MODELO PROPIO (`modelo/scripts/modelo.py`), no contra el motor consolidado del equipo (`consolidado/motor`, motor_rotacion v1). Decir «el motor ignora la CEw» fue un error: el motor consolidado sí la usa (ver R5.1). **Qué hacía mi modelo propio con la CEw en la ronda 4.** Nada. `scripts/modelo.py` no tiene entrada de CEw. La salinidad sale solo del rango de ECe del suelo por zona (Maas-Hoffman sobre `ece_ds_m`). Sin CEw, el motor no bloquea, no usa un valor por defecto y no ensancha el intervalo: la ignora. Por eso la ablación y la permutación de la ronda 4 no miden la CEw en ninguno de los dos sentidos. Ni el valor dentro del rango ni la ausencia del dato cambian el ranking oficial.

**Experimento.** Regla explícita, fuera del motor: ECe efectiva = max(ECe del suelo, 1.5·CEw). El 1.5 es FAO-29 (Ayers y Westcot 1985, Tabla 4 nota 2; fracción de lavado 0.15-0.20, no vale con napa somera). El max deja mandar a la CE medida del suelo salvo que el agua proyecte más sal. Rangos de CEw (dS/m) de `suelos/datos/cew_por_zona.csv`, río: Chira 0.373-4.98 (central 0.888), Medio 0.74-9.92 (3.32), Alto 0.345-0.741 (0.51), San Lorenzo 0.417-9.03 (1.384). Bajo sin dato. Variantes: Chira 0.373-1.167 (Coronel 2021), y Bajo con el rango de pozos Medio+Bajo 0.04-16.83 (ANA 2014).

**Valor de CEw dentro del rango (cambio del top-1 al fijarla en su central o permutarla, %)**

| zona | ablación | permutación | sorteos donde 1.5·CEw > ECe suelo |
|---|---|---|---|
| Chira (0.373-4.98) | 7.0 | 10.5 | 69.9 % |
| Chira (0.373-1.167) | 0.0 | 0.0 | 7.3 % |
| Bajo (sin dato) | no aplica | no aplica | 0 |
| Bajo (pozo 0.04-16.83) | 35.6 | 42.0 | 74.7 % |
| Medio | 36.5 | 33.0 | 88.4 % |
| Alto | 0.0 | 0.0 | 2.2 % |
| San Lorenzo | 44.8 | 38.8 | 86.9 % |

Control. Con la CEw vacía en todas las zonas, el script reproduce exactamente la ablación oficial de la ronda 4 (por ejemplo pendiente 28.5 / 45.2 en Alto / San Lorenzo). Los cambios que siguen vienen de la regla, no del script.

Ranking medio (ablación, ECe de la ronda 4). Ronda 4 oficial: drenaje 36.5, pendiente 29.7, costo 14.6, ECe 12.8. Con CEw: drenaje 36.7, CEw 22.1 (media de 4 zonas; Bajo sin dato), pendiente 19.9, costo 14.0, ECe 10.5. La CEw entra 2.ª y empuja pendiente, costo y ECe un puesto abajo. En permutación también queda 2.ª (20.6), detrás de drenaje (44.5). La caída se concentra en Medio y San Lorenzo: la ECe del suelo baja de 7.9 / 6.7 a 1.4 / 1.2 y la pendiente de 34.9 / 45.2 a 13.1 / 18.8, porque el agua domina la proyección de sal y deja menos candidatos que la pendiente pueda mover. Con el rango global de ECe de la ronda 3 (0.5-12 en todas las zonas, "v3"), la CEw queda 3.ª (11.9 / 12.0), detrás de drenaje y ECe. Con la CEw del Chira de Coronel 2021 (0.373-1.167), la CEw no mueve nada en el Chira: 1.5 × 1.167 = 1.75 dS/m queda bajo casi todos los umbrales de los cultivos.

**CEw ausente.** Comparo mi modelo propio sin CEw (la ignora) con mi modelo propio con la regla de CEw:

| zona | top-1 distinto, motor actual frente a CEw sorteada | top-1 distinto si la ausencia se rellena con el máximo de la zona | "ninguno apto" sin CEw → con CEw |
|---|---|---|---|
| Chira (0.373-4.98) | 7.0 % | 51.5 % | 40.6 → 41.1 % |
| Chira (0.373-1.167) | 0.0 % | 0.0 % | 40.6 → 40.6 % |
| Medio | 43.3 % | 31.3 % | 30.5 → 36.3 % |
| Alto | 0.0 % | 0.0 % | 20.9 → 20.9 % |
| San Lorenzo | 44.7 % | 38.0 % | 27.4 → 31.7 % |
| Bajo (pozo) | 48.8 % | 46.3 % | 19.0 → 53.7 % |

Lectura. Que falte la CEw solo importa donde su rango puede pasar la ECe del suelo: Medio, San Lorenzo, el Chira si se acepta el tramo bajo del río (Amotape, Vichayal, 4.1-4.98) y Bajo si riega con pozo. En Alto y en el Chira medido en Sullana, la ausencia no cambia nada. Coincide con lo que ve el coordinador en Tablazo Sur: cuando la CE medida del suelo es alta, domina, y lo decisivo es si hay o no CEw, no su valor exacto.

**Por qué no entra al ranking oficial.** Los rangos de Medio y San Lorenzo son `estimado` (unidad corregida µS→mS). Son puntos de estiaje en tramos con retorno de drenes. San Lorenzo riega con agua del Chira vía Poechos, no con el río Piura en Tambogrande (`restricciones/insumos/curado_r3.csv`). Bajo no tiene dato y el factor 1.5 no vale con napa somera, que es justo el caso de Bajo. Si Territorio da CEw de canal o toma por zona, la regla está lista para entrar al motor.

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

## Para Christian

1. Ya no uso HWSD como ECe. Contradice la CE medida en chacra (Piura Datos, Territorio). En Chira, Medio, Alto y San Lorenzo la ECe zonal queda desconocida y el modelo usa el rango hipótesis 0.5-2-12 dS/m. Solo Bajo tiene rango local (1.2-4-12).
2. Por eso la ECe vuelve a ser el dato que más mueve la recomendación (cambia el top-1 en 36.8 % de los sorteos, antes 12.8 %). El drenaje sigue segundo (36.6 %). La pendiente baja de 29.7 a 6.9 % con la pendiente DEM de Territorio. El camote que subía en r4 venía de la ECe baja de HWSD, no del clima.
3. El motor del equipo (`consolidado/motor`) no recomienda nada en 4 de 5 zonas con los datos de hoy. Necesita ECe medida, o bien CEw y napa a 2 m o más. Con napa a 1 m y sin ECe sigue sin poder decidir. Cuando decide, pone caupí primero y arveja en San Lorenzo.
4. Lo que más vale pedir por parcela es, en orden, ECe (análisis de suelo), CEw de la fuente de riego más profundidad de napa, y dotación de agua por mes.
5. CEw entra como "escenario, no dato". Los valores de canal (Chira 0.59, San Lorenzo 0.47) y de pozos de tesis casi no cambian nada. Todo lo medido es de estiaje (sep-nov); no hay medidas de avenida.
6. Lluvia con PISCOp. Las 5 zonas ya no comparten lluvia (0 pares idénticos; con POWER eran 3). El riego neto casi no cambia en la costa. Alto baja 39 mm. PISCOp acierta marzo de 2017 con ±15 % pero da la mitad en febrero; en la sierra es cota baja.
7. El clima del año sigue sin explicar el rendimiento distrital (skill LOYO mediano -1.2 %). Solo algodón (19.8 %) y limón (4.4 %) tienen skill positivo. Con la regla de atípicos 1.5 aceptada, el rescate cambia una sola fila de mi validación (maíz, Yamango 2019) y menos de 1.1 puntos de skill.
8. Qué tan seguro es esto. Mecánica del motor y de mi modelo, verificada. Rangos de ECe y pendiente fuera de Bajo, hipótesis o DEM 30 m. Los máximos de CEw del río en Medio y San Lorenzo (9.92 y 9.03) son lecturas ANA 2024 de unidad ambigua, estimadas por balance iónico. Territorio y Piura Datos las publican; el motor las rechaza.
9. Falta ECe por pasta saturada en 4 zonas, napa en Chira, Alto y San Lorenzo, dotación mensual y CEw de avenida.

## Ronda 5 (24-oct-2026)

### R5.0 Qué cambió

| cambio | ronda 4 | ronda 5 | fuente |
|---|---|---|---|
| ECe | HWSD v2 por zona en Chira, Medio, Alto, San Lorenzo | desconocida; rango hipótesis 0.5-2-12 (`escenario_rangos.csv`). Bajo sigue 1.2-4-12 | `suelos/datos/zonas_ece_drenaje_fen.csv` (ECe_0_20cm = desconocido); `restricciones/cobertura.md` |
| pendiente | hipótesis 0-1-5 fuera de Bajo | GLO-30 + WorldCover por zona (Chira 0-1.0-3.0, Medio 0-1.4-3.8, Alto 0-1.1-3.9, San Lorenzo 0-2.1-5.1); Bajo 0.03-0.05 (Banco Mundial 1979) | `suelos/datos/pendiente_por_zona.csv` |
| lluvia | ERA5 o CHIRPS en el punto | PISCOp v2.1 mensual por zona 1981-2019; 2020-2025 por mapeo de cuantiles desde POWER (error absoluto medio en log fuera de muestra 0.21) | `scripts/lluvia_mensual.py`, `resultados/lluvia_relleno_prueba.csv` |
| CEw | solo en mi modelo, regla fuera del motor | medida contra el motor consolidado; variantes a-d; canal, toma y pozo de `cew_por_zona.csv` | R5.1, R5.2 |
| tabla final | de mi modelo | del motor consolidado, por cultivo y zona | R5.7 |

### R5.1 CEw en el motor consolidado

Corrección. En la ronda 4 escribí que "el motor ignora la CEw". Eso vale para mi modelo propio (`modelo/scripts/modelo.py`), no para el motor del equipo. El motor consolidado sí usa la CEw. `filtros._f_salinidad_fao29` (l.121-139) toma max(ECe, 1.5·CEw) solo si la napa está a 2 m o más, y `estado_suelo.actualizar_tras_cosecha` (l.44-54) proyecta la ECe tras cada cosecha con 1.5·CEw. Si falta la CEw, la ECe de la segunda campaña queda desconocida. Todo R4.6 se midió contra mi modelo propio. Todo R5.1, R5.2 (parte del motor) y R5.7 se midió contra el motor consolidado.

Experimento `modelo/experimentos/cew_motor.py` (se corre desde `consolidado/motor`). Una parcela por zona, 30 secuencias de 2 cultivos, siembra en agosto, horizonte de 6 meses. Entradas:

| Entrada | Valor | Fuente |
|---|---|---|
| ECe, modo "zonal" | Bajo [1.2, 12]; las otras 4 zonas desconocida | `params/zonas.csv`, `zonas_ece_drenaje_fen.csv` (HWSD descartado) |
| ECe, modo "rango_global" | [0.5, 12] en las 4 zonas sin ECe, tipo "prediccion" (no es dato) | `params/escenario_rangos.csv` |
| pH | pH_rango_zona | `suelos/datos/profundidad_ph_por_zona.csv` |
| Profundidad | ≥ 100 cm, estimada (cota baja) | HWSD2 clase ">100 cm" vía `profundidad_ph_por_zona.csv` |
| Pendiente | [0, p90] | `suelos/datos/pendiente_por_zona.csv` |
| Napa | sin dato, 1 m o 3 m. Medio y Bajo figuran como "parcial" y Chira, Alto y San Lorenzo sin dato | `profundidad_ph_por_zona.csv` |
| Agua | sin dotación mensual | no se inventa |
| CEw río | Chira 0.373-4.98, Medio 0.74-9.92, Alto 0.345-0.741, San Lorenzo 0.417-9.03; Bajo sin dato. Los máximos de Medio y San Lorenzo son RPiur5 y RPiur4 (ANA 2024), "estimado" por balance iónico. Sin las 4 lecturas en disputa: Medio 0.74-5.98, San Lorenzo 0.417-2.32 | `cew_por_zona.csv` (ANA 2015, ANA 2024, Coronel 2021); `balance_ionico_ana2024.csv` |
| CEw canal, reservorio o toma | Chira 0.59 (reservorio, salida de Poechos), San Lorenzo 0.47 (reservorio) | `cew_por_zona.csv` |
| CEw pozo (tesis) | Bajo 0.13-1.12, Medio 0.16-3.83 | `cew_por_zona.csv` |

Todas las CEw son de estiaje (sep-nov) o de estación desconocida. No hay ninguna de avenida. Versión de `cew_por_zona.csv` usada: 24-oct 07:57 UTC (md5 248a862a). Desde 07:55 Territorio usa una sola variable, `ce_agua_riego`, con el origen en `fuente_agua`; mis scripts leen por `fuente_agua`.

Salidas `experimentos/cew_motor_resumen.csv` y `cew_motor_ablacion.csv` (modo zonal), y los mismos con sufijo `_eceglobal`.

Secuencias viables de 30 y top-1, modo zonal (lo que el motor puede decir hoy):

| Zona | CEw falta | Cualquier CEw, napa sin dato | Cualquier CEw, napa 1 m | Cualquier CEw, napa 3 m |
|---|---|---|---|---|
| Chira | sin_datos | sin_datos | sin_datos | caupí, 30 (CEw 3.0, 24) |
| Bajo | caupí, 0 | caupí, 30 | caupí, 25 | caupí, 30 (CEw 3.0, 25) |
| Medio | sin_datos | sin_datos | sin_datos | caupí, 30 (CEw 3.0, 24) |
| Alto | sin_datos | sin_datos | sin_datos | caupí, 25 (CEw 3.0, 23) |
| San Lorenzo | sin_datos | sin_datos | sin_datos | arveja, 30 (CEw 3.0, 24); con CEw 0.5 o el reservorio 0.47 el top-1 pasa a cebolla |

Modo rango_global: 30 de 30 con cualquier CEw y napa sin dato o a 3 m (Alto 25). Con napa 1 m, 30 (Bajo 25, Alto 21). CEw 3.0 con napa a 3 m baja a 25 (Alto 23). Con CEw ausente, 0 (Alto 5). Top-1 caupí, salvo San Lorenzo con arveja.

Respecto de la versión anterior de esta tabla (24 secuencias, maíz amarillo duro primero en San Lorenzo), el cambio viene del motor y no de la CEw. El motor de las 07:53 usa la Tmáx PISCOt por zona y la arveja, el frijol grano y la cebolla dejan de ser "probable no apto" (`consolidado/motor/README.md`, ronda 5).

Qué muestra.
1. **Con la ECe desconocida, el motor solo decide si tiene CEw y napa ≥ 2 m.** Es la única vía por la que obtiene una ECe (1.5·CEw). Con napa a 1 m la regla no vale y el motor, con razón, no la aplica. Sin ECe medida, esas parcelas quedan sin recomendación.
2. **Importa que la CEw exista, casi no su valor.** Entre 0.5 y 1.5 dS/m, canal, río o pozo de tesis, el número de secuencias no cambia. 3.0 con napa a 3 m quita de 2 a 6. La única excepción de orden es San Lorenzo con napa a 3 m, donde CEw 0.5 o 0.47 pone cebolla primero en lugar de arveja.
3. **El bloqueo viene de dos faltantes juntos.** El motor marca "sin_datos" cuando 2 o más filtros críticos (salinidad, agua, calendario) no son evaluables. Sin CEw la salinidad de la segunda campaña no se evalúa, y sin dotación el agua tampoco.
4. **Un rango de CEw se juzga por su cota baja.** El motor descarta solo si la cota baja ya pasa el umbral, así que un rango ancho nunca descarta. Agronomía (H06) advierte además que el rango entre puntos de una zona no es la incertidumbre de una parcela.
5. **La dotación ANA repartida en 12 meses iguales vacía la lista** (modo rango_global: Bajo, Medio y San Lorenzo sin cultivo, Chira 2 secuencias, Alto 9). Ese reparto es un supuesto mío. El motor necesita la dotación por mes.

Ablación "falta el dato", modo rango_global (base: napa sin dato, CEw del río publicado; Bajo, escenario 1.5):

| Falta | Chira | Bajo | Medio | Alto | San Lorenzo |
|---|---|---|---|---|---|
| ECe | sin cultivo | sin cultivo | sin cultivo | sin cultivo | sin cultivo |
| CEw | top-1 igual; secuencias 30 a 0 | igual; 30 a 0 | igual; 30 a 0 | igual; 25 a 5 | igual; 30 a 0 |
| pH | sin cambio | sin cambio | sin cambio | secuencias 25 a 28 | top-1 pasa a frijol verde |
| Profundidad | sin cambio | secuencias 30 a 28 | sin cambio | sin cambio | top-1 pasa a frijol verde |
| Pendiente | sin cambio | sin cambio | sin cambio | sin cambio | sin cambio |

En modo zonal la ablación no informa nada en 4 zonas, porque la base ya es sin_datos. En Bajo, quitar la ECe da sin cultivo y quitar la CEw deja 0 secuencias.

**Salvedad de la napa somera.** La regla ECe = 1.5·CEw de FAO-29 supone fracción de lavado de 0.15-0.20 y napa a 2 m o más (https://www.fao.org/4/t0234e/T0234E03.htm). En Bajo Piura, entre 49 y 80 % del área tiene la napa a menos de 2 m (FAO/UNALM 1990, de segunda mano). Los 41 SEV de ANA 2015 dan mediana 2.3 m y 20 de 41 por debajo de 2 m. Agronomía (H04) señala que el tope de 2.0 m de la napa de Bajo en Territorio contradice esos SEV (51 % sobre 2 m). En mi modelo la probabilidad de napa ≥ 2 m en Bajo se sortea en U(0.20, 0.51), que cubre las dos lecturas. Medio queda "parcial" y Chira, Alto y San Lorenzo sin dato. Con napa somera la sal sube por capilaridad y la ECe puede superar 1.5·CEw. Allí manda la ECe medida, no la CEw.

**Hueco de integración (H05 de Agronomía), cerrado en parte.** Desde las 07:55 Territorio usa el nombre del contrato, `ce_agua_riego`, con el origen en `fuente_agua` (`suelos/mapa_variables_motor.csv`). El motor lo reconoce (`catalogo.py`, VARIABLES_ZONA) y toma como valor de zona solo el agua de canal, reservorio o toma (hoy Chira 0.59 y San Lorenzo 0.47). Los puntos de río, quebrada y pozo quedan como aviso, y las 4 lecturas ANA 2024 en disputa se rechazan (CEW_EN_DISPUTA). Ese dato entra solo al integrar un CSV del contrato (`--integrar`, por ejemplo `datos_repo/evidencia_integrar_r5.csv`). La copia `datos_repo/cew_por_zona.csv` (07:50) aún trae los nombres viejos. Mis experimentos llaman a `evaluar` sin integrar y pasan la CEw a mano, incluido el rango del río, que el motor por sí solo no tomaría como valor de zona. Medio, Bajo y Alto no tienen agua de canal medida, así que ahí la CEw sigue faltando.

**Decisión.** La CEw entra al ranking oficial como "escenario, no dato", con dos números separados. Uno es la importancia por presencia (si falta, el motor pierde la segunda campaña) y el otro la importancia por valor (casi nula salvo napa ≥ 2 m y CEw ≥ 3 dS/m). No se le asigna un valor por defecto.

**Alineación con el motor consolidado.** Mantengo mi modelo propio para el ranking por sorteo, porque el motor consolidado es determinista por intervalos y no da la frecuencia con que cambia el top-1. Le alineo dos reglas: la CEw cuenta solo con napa ≥ 2 m (variantes b2, d2, d3) y la CEw ausente se informa como el motor la trata (variante c). La tabla final por cultivo y zona (R5.7) sale del motor consolidado, porque es lo que el equipo va a entregar.

### R5.2 Variantes de CEw (a, b, c, d)

Mismas variantes en los dos motores. La CEw se lee de `suelos/datos/cew_por_zona.csv`. **Todos los valores de CEw son de estiaje (sep-nov) o de estación desconocida; no hay ninguna medida de avenida.** Son un techo estacional y no describen la campaña de verano.

| variante | qué hace con la CEw |
|---|---|
| a | se ignora (ECe del suelo sola) |
| b1, b2 | valor conocido del río (central de la zona); b1 sin condición de napa, b2 solo con napa ≥ 2 m (regla del motor) |
| b3 | valor de canal, reservorio o toma: Chira 0.59 (reservorio, salida de Poechos, ANA oct-2024), San Lorenzo 0.47 (reservorio, UNP c. 2011, 1 muestra de copia de terceros, sin rango); Medio, Bajo y Alto sin dato de canal |
| c | falta y bloquea (lo que hace hoy el motor en la segunda campaña) |
| d1, d2 | falta y se sortea U(rango del río publicado, con los máximos estimados 9.92 y 9.03); d2 solo con napa ≥ 2 m |
| d1sd | d1 sin las 4 lecturas ANA 2024 en disputa (QCarn1, QSFran1, RPiur4, RPiur5), como las trata el motor: Medio U(0.74, 5.98), San Lorenzo U(0.417, 2.32) |
| d3 | falta y se sortea el rango de pozos de tesis con napa ≥ 2 m: Bajo 0.13-1.12 (Cura Mori, 5 pozos), Medio 0.16-3.83 (Castilla y Progreso Bajo, 7 pozos); solo resúmenes de tesis |

Mi modelo propio (`experimentos/exp_cew_variantes.py`, N=5000, PISCOp, ECe nueva). Celda: % de sorteos sin cultivo viable / % con top-1 distinto de a. El ruido entre corridas es de alrededor de 1 punto.

| zona | a | b1 | b2 | b3 | d1 | d1sd | d2 | d3 | c |
|---|---|---|---|---|---|---|---|---|---|
| Chira | 41.1 | 41.1 / 0.0 | 41.1 / 0.0 | 41.1 / 0.0 | 41.5 / 3.4 | 41.4 / 3.0 | 41.1 / 0.0 | 41.1 / 0.0 | 100.0 / 58.9 |
| Bajo | 19.2 | 19.2 / 0.0 | 19.2 / 0.0 | 19.2 / 0.0 | 54.8 / 50.6 | 54.8 / 50.6 | 32.0 / 18.0 | 19.2 / 0.0 | 100.0 / 80.8 |
| Medio | 35.3 | 35.3 / 10.5 | 35.3 / 8.0 | 35.3 / 0.0 | 39.0 / 23.4 | 36.6 / 10.7 | 38.0 / 17.8 | 35.3 / 3.2 | 100.0 / 64.7 |
| Alto | 22.9 | 22.9 / 0.0 | 22.9 / 0.0 | 22.9 / 0.0 | 22.9 / 0.0 | 22.9 / 0.0 | 22.9 / 0.0 | 22.9 / 0.0 | 100.0 / 77.1 |
| San Lorenzo | 30.5 | 30.5 / 0.1 | 30.5 / 0.0 | 30.5 / 0.0 | 33.2 / 24.0 | 30.5 / 0.7 | 30.5 / 0.0 | 30.5 / 0.0 | 100.0 / 69.5 |

Motor consolidado (`experimentos/cew_motor_variantes.py`). Con la ECe zonal de hoy, Chira, Medio, Alto y San Lorenzo quedan "sin_datos" en todas las variantes. Con el rango hipótesis de ECe, a, b y d dan 30 de 30 secuencias viables (Alto 25) y c da 0 (Alto 5). El top-1 no cambia en ninguna variante (caupí; San Lorenzo arveja).

Lectura.
1. c es la única variante que cambia mucho. Bloquear por CEw ausente deja sin cultivo el 100 % de los sorteos de mi modelo (en a tenían cultivo entre 59 y 81 %) y deja el motor en 0 secuencias.
2. Los valores de canal (b3) y los pozos de tesis (d3) no cambian nada, salvo Medio con pozos (3 %). Ambos quedan bajo los umbrales de casi todos los cultivos.
3. Lo que mueve d1 son los máximos del río, que son justo las lecturas en disputa. Sin ellas (d1sd), San Lorenzo pasa de 24.0 a 0.7 % de cambio y Medio de 23.4 a 10.7 %. Bajo sigue en 50.6 % porque el rango de pozos ANA 2014 llega a 16.83. En Medio, b1 y b2 también cambian el top-1 (10.5 y 8.0 %) porque el central del río, 3.32, es RPiur5 de 2015 (ANA, Cuadro 05), del mismo punto cuya lectura de 2024 está en disputa.
4. Con la condición de napa (d2) el efecto cae (Bajo de 50.6 a 18.0, Medio de 23.4 a 17.8) o desaparece (Chira, San Lorenzo), porque la napa somera es justo el caso donde la regla no vale.

### R5.3 ECe sin HWSD

Territorio y Piura Datos rebajaron HWSD como fuente de ECe (`restricciones/cobertura.md`). HWSD subestima Bajo y sobreestima Chira, Medio y Alto frente a la CE de campo. Verifiqué que ni `modelo.py` ni `params/zonas.csv` lo usan. Las columnas ece_min, ece_central y ece_max quedan vacías en 4 zonas y el modelo cae al rango global 0.5-2-12.

CE de campo puntual (`zonas_ece_drenaje_fen.csv`, ECe_medida_local), que no uso como ECe porque el método de extracto no está confirmado.

| zona | CE de campo (dS/m) | fuente |
|---|---|---|
| Chira | 0.103 | Atoche 2025 |
| Medio | 0.95 | Vite 2015 |
| Alto | 0.46-0.6 | La Rosa 2021 |
| Bajo | 3.44-8.2 | Mendoza 2025, Tablazo |
| San Lorenzo | sin dato | ninguna |

Si esa CE fuera de extracto 1:1, la ECe sería de 1.8 a 3 veces mayor (Territorio, decisión r5). Esa lectura entra como alternativa de estabilidad (`ece_campo_x1_x3`), y HWSD queda como alternativa de contexto (`ece_hwsd_contexto_r4`).

### R5.4 Lluvia: PISCOp, CHIRPS y POWER

Script `experimentos/comparar_lluvia.py`. Salidas `resultados/lluvia_correlacion_zonas.csv`, `lluvia_riego_neto.csv` y `lluvia_loyo.csv`.

**¿Siguen las zonas compartiendo clima?** No en la lluvia. Correlación de la lluvia mensual entre pares de zonas:

| fuente | r media | rango | pares idénticos (de 10) |
|---|---|---|---|
| PISCOp | 0.828 | 0.68-0.944 | 0 |
| CHIRPS | 0.716 | 0.413-0.984 | 0 |
| POWER | 0.958 | | 3 |
| r4 (ERA5 o CHIRPS en el punto) | 0.894 | | 0 |

Alto y San Lorenzo siguen compartiendo celda ERA5 para viento y radiación.

**Riego neto** (mm, media sobre cultivos y meses; PISCOp / CHIRPS / POWER / r4):

| zona | PISCOp | CHIRPS | POWER | r4 |
|---|---|---|---|---|
| Alto | 535 | 568 | 591 | 574 |
| Bajo | 692 | 695 | 691 | 687 |
| Chira | 693 | 698 | 693 | 677 |
| Medio | 698 | 696 | 695 | 672 |
| San Lorenzo | 587 | 582 | 614 | 589 |

En la costa la lluvia efectiva es tan baja que la fuente casi no cambia el riego. Alto es la excepción (39 mm menos que en r4).

**Skill LOYO** (clima_v1, % sobre la media distrital; PISCOp / CHIRPS / POWER / r4): algodón 19.8 / 27.0 / 12.3 / 19.9, limón 4.4 / 4.1 / 1.8 / 2.9, frijol -18.9 / -26.8 / -27.1 / -25.0. Mediana de cultivos -1.2 / -1.3 / -2.4 / -1.5. Con eventos e ICEN corregido (clima_mas_eventos), mediana -4.3 / -4.8 / -3.5 / -6.2; limón llega a 9.1. PISCOp no da skill al clima del año. Lo elijo por la evidencia de Piura Datos (R4-7, razón costera 1.29 frente a 0.63 de CHIRPS), no por skill. Reservas de Piura Datos que mantengo: PISCOp asimila las estaciones SENAMHI, su sesgo costero es en buena parte efecto de periodo y Chusis da 886.7 mm en marzo de 2017 sin contraste.

**Validación de PISCOp por Piura Datos** (`restricciones/anexos/validacion_pisco_2017.md`, R6-4). En marzo de 2017 PISCOp queda a ±15 % del registro público: Piura ciudad 481 mm (Rollenbeck et al. 2022) frente a 553.7 en San Miguel; Chulucanas 1130 frente a 957.5. En febrero da la mitad (205 frente a 98.8 mm). En sep-nov, en la costa, la diferencia es de 1-2 mm en la temporada. En la sierra, PISCOp da 15-35 % menos que la normal SENAMHI. Cómo lo uso:
1. **Sierra, cota baja.** Ninguna de mis 5 zonas es sierra, así que mi modelo no cambia. En la lluvia del motor, la fila `sierra_piura` de `lluvia_zona_pisco.csv` debe leerse como cota baja; la lluvia real puede ser hasta 1/0.65 ≈ 1.5 veces mayor. Alto Piura queda en medio: Chulucanas sale 15 % bajo en marzo de 2017.
2. **Sesgo de febrero en la lluvia del motor.** El motor usa la lluvia p90 del mes como techo de la lluvia efectiva (`motor_rotacion/agua.py`). Si febrero viene a la mitad, el caso bajo de riego neto de febrero sale alto, es decir, conservador. Pesa en los escenarios El Niño: la mediana de febrero en `el_nino_moderado` va de 17.5 mm (Bajo) a 102.6 (San Lorenzo), y en el año sin El Niño, de 4.9 a 53.2 mm (Alto). Recomiendo no leer al mes el escenario El Niño y mirar feb-mar juntos, que en Piura ciudad cuadran (ene-abr −5 %).
3. El 886.7 mm de Chusis queda desconocido; no entra en ninguna cifra mía.

### R5.5 Ranking de features (escenario normal, promedio de las 5 zonas, % de sorteos en que cambia el top-1)

| puesto r5 | feature | ablación r4 | ablación r5 | permutación r4 | permutación r5 |
|---|---|---|---|---|---|
| 1 | ece_ds_m | 12.8 | 36.8 | 14.7 | 39.1 |
| 2 | drenaje_malo | 36.5 | 36.6 | 44.2 | 44.5 |
| 3 | factor_costo | 14.6 | 13.2 | 8.6 | 7.4 |
| 4 | pendiente_pct | 29.7 | 6.9 | 11.7 | 7.4 |
| 5 | agua_riego_mm | 7.6 | 6.3 | 9.8 | 8.2 |
| 6 | factor_rend | 7.0 | 6.1 | 9.1 | 7.8 |
| 7 | factor_precio | 5.0 | 4.4 | 6.8 | 6.0 |
| 8 | mes_siembra | 5.6 | 4.4 | 5.6 | 4.4 |
| 9 | eficiencia_riego | 4.8 | 4.3 | 6.4 | 5.6 |
| 10 | taw_mm_m | 2.4 | 2.1 | 3.0 | 2.7 |

Por zona (ablación, normal, % de cambio del top-1):

| feature | Chira | Bajo | Medio | Alto | San Lorenzo |
|---|---|---|---|---|---|
| ECe | 31.4 | 47.8 | 39.9 | 22.4 | 42.5 |
| drenaje | 49.9 | 37.2 | 38.2 | 24.8 | 33.0 |
| pendiente | 18.6 | 0.0 | 6.2 | 4.1 | 5.8 |
| costo | 1.9 | 14.5 | 14.2 | 20.1 | 15.4 |
| agua de riego | 1.6 | 8.8 | 9.0 | 4.8 | 7.3 |

Sobol ST, feature con mayor índice por cultivo y zona (30 celdas): ECe 14, drenaje 12, pendiente 4 (r4: drenaje 22, pendiente 4, ECe 4).

Top-1 en escenario normal (% de sorteos, N=5000): Chira ninguno 41.1, camote 25.2; Bajo caupí 25.1, arroz 22.8, algodón 20.8; Medio ninguno 34.8, caupí 24.9; Alto caupí 39.0, algodón 35.3; San Lorenzo ninguno 30.5, algodón 24.1. El camote, que subía en r4 (Medio 36.9, San Lorenzo 44.9), deja de estar entre los 2 primeros en Medio y San Lorenzo. Con eso se responde la duda abierta de R4.3: la subida del camote venía sobre todo de la ECe baja de HWSD.

Lectura. La ECe sube porque su rango vuelve a ser el hipótesis ancho (0.5-12). No es que se haya medido más sal; es que ahora no sabemos cuánta hay, y el modelo lo refleja. La pendiente baja porque el DEM da rangos más estrechos que la hipótesis 0-1-5. Su peso alto en r4 venía del supuesto.

### R5.6 Estabilidad

`scripts/estabilidad.py`: 20 semillas (100-119), N=2000 por zona, 20 alternativas (base más 19). Base de la ronda 5: clima por zona, lluvia PISCOp, ECe 0.5-2-12 en las 4 zonas sin ECe, pendiente DEM. Una posición es robusta si en la base queda igual en al menos 80 % de las semillas y dentro del top-5 en al menos 90 % de todas las corridas. Salidas `resultados/estabilidad_top5.csv` y `estabilidad_corridas.csv`.

**Posiciones robustas: 116 de 175** (ronda 4: 102). Por cultivo, frijol 22, maíz amarillo duro 22, todos 17, camote 16, caupí 15, algodón 14, arroz 10, de 25 cada uno.

Top-5 por zona, todos los cultivos (✓ robusta):

| Zona | 1.º | 2.º | 3.º | 4.º | 5.º |
|---|---|---|---|---|---|
| Chira | drenaje ✓ | ECe ✓ | pendiente ✓ | costo | agua |
| Bajo | ECe ✓ | drenaje ✓ | costo ✓ | agua ✓ | eficiencia |
| Medio | ECe | drenaje ✓ | costo ✓ | agua ✓ | eficiencia |
| Alto | drenaje ✓ | ECe | costo ✓ | rendimiento ✓ | mes de siembra |
| San Lorenzo | ECe ✓ | drenaje ✓ | costo ✓ | rendimiento ✓ | agua |

Qué alternativas mueven el ranking (suma de |mediana de posición − posición base| sobre los 25 puestos "todos"):

| Alternativa | Movimiento total | Qué pasa |
|---|---|---|
| ece_campo_x1_x3 | 59.5 | con la CE de campo como ECe baja, la ECe cae al puesto 21 en Chira y Alto y al 10 en Medio |
| ece_campo_alto_medio | 45.0 | la ECe cae al 21 en Medio y Alto |
| ece_hwsd_contexto_r4 | 43.0 | la ECe cae al 6-8 en Chira, Medio y San Lorenzo y al 16.5 en Alto |
| pendiente_supuesta_r4 (0-1-5) | 14.0 | la pendiente vuelve al 3.º en Bajo, Medio y San Lorenzo |
| clima_power | 12.5 | mes de siembra y rendimiento bajan 2-3 puestos |
| lluvia_r4, lluvia_chirps, lluvia_power | 2.5 a 6.5 | solo cambian el 5.º puesto de Alto o Medio |
| drenaje y costo | 1.0 a 9.0 | 1 o 2 puestos |

Lectura.
1. **El ranking depende de la ECe que se suponga, no de la lluvia.** Las tres alternativas que sacan la ECe del top-5 son las que le dan una ECe baja a las zonas sin dato. Es la misma conclusión de la ronda 3: el puesto de la ECe mide cuánto no sabemos de ella.
2. **Drenaje y costo son estables.** El drenaje está en el top-2 en las 5 zonas y es robusto en todas. El costo, en el top-4 de 4 zonas.
3. **La lluvia PISCOp no cambia el ranking.** Con la lluvia de r4, CHIRPS o POWER, el top-4 queda igual en las 5 zonas.
4. **La pendiente baja porque el rango es otro.** Con la hipótesis 0-1-5 de la ronda 4 vuelve al 3.º puesto en Bajo, Medio y San Lorenzo. Con el DEM suavizado sube al 4.º-5.º, porque el p90 de 2.2-3.5 % deja más sorteos cerca del umbral de 2 % del arroz que el p90 de 3-5 %. En Bajo, el DEM (0-0.8-2.6) en lugar de Banco Mundial 1979 (0.03-0.05) la sube del 21.º al 3.º. La pendiente de Bajo sigue siendo la entrada más frágil del bloque.

**De dónde venía el ascenso del camote (pendiente de la ronda 4).** `experimentos/top1_por_alternativa.py`, cuota de top-1 en el escenario normal, N=5000, semilla 42 nueva en cada zona (por eso la base difiere en hasta 1 punto de `top_por_escenario.csv`):

| Zona | Base r5 | ECe HWSD (r4) | CE de campo x1-x3 | Lluvia r4 | Todo POWER |
|---|---|---|---|---|---|
| Chira | 25.2 | 48.9 | 49.5 | 25.4 | 21.7 |
| Medio | 13.5 | 35.8 | 43.7 | 14.4 | 6.4 |
| San Lorenzo | 16.7 | 45.4 | 16.7 (sin CE de campo) | 16.8 | 11.0 |
| Bajo | 12.7 | 12.7 | 12.7 | 13.0 | 6.5 |

El camote sube solo cuando la ECe de la zona es baja (HWSD o CE de campo). Con la lluvia de r4 queda igual que en la base. **Venía de la ECe, no del clima.** Con la CE de campo de Chira y Medio sube igual, así que si esa CE se confirma como ECe el camote vuelve.

### R5.6b Validación con los rendimientos rescatados (R6-1)

El coordinador aceptó con Piura Datos la regla A4 con factor 1.5: una cifra distrito-año descartada por atípica no se descarta si el mismo distrito repite el orden de magnitud en 3 años o más. Rescata 19 cifras, que pasan a estimado con marca; la uva de Las Lomas 2016 (64.47 t/ha) queda fuera hasta revisión manual (`restricciones/respuestas_a_modelos.md` R6-1, `anexos/rendimiento_desconocido_explicado.csv`, columna `variante_estricta_factor_1_5`).

Qué toca a mi validación. Mi validación (`scripts/validacion.py`) usaba el DRAP sin filtro de atípicos. Agregué `ATIPICOS` con tres modos: crudo (el de siempre), sin_rescate (quita las cifras A4 que Piura Datos deja desconocidas) y con_rescate (las devuelve con la marca `rescate_a4`, salvo la uva de Las Lomas). El cruce es por cultivo, distrito, año y cifra (±1 %). De las 41 cifras A4, 10 están en mi tabla. De las 19 rescatadas, 4: camote en Huarmaca 2019, 2023 y 2024 (sierra, fuera de mis zonas) y maíz amarillo duro en Yamango 2019 (Alto). Las otras 15 son de cultivos que no modelo (ají piquillo, caña etanol, plátano). En la práctica, el rescate cambia una sola fila.

Salida `resultados/validacion_atipicos_comparacion.csv` (`experimentos/validacion_atipicos.py`). Skill LOYO, clima_v1, %:

| cultivo | n crudo / sin / con | crudo | sin rescate | con rescate |
|---|---|---|---|---|
| algodón | 103 / 101 / 101 | 19.75 | 18.26 | 18.26 |
| frijol | 37 / 36 / 36 | -18.87 | -8.41 | -8.41 |
| maíz amarillo duro | 323 / 322 / 323 | -5.76 | -5.68 | -5.76 |
| mango | 104 / 103 / 103 | -0.09 | -1.01 | -1.01 |
| uva | 68 / 66 / 66 | -1.48 | 0.80 | 0.80 |

Arroz, camote, caupí y limón no cambian. Con y sin las rescatadas, la diferencia es solo del maíz amarillo duro: −0.08 puntos en LOYO clima_v1, −0.10 con eventos y +0.50 / +1.04 en GroupKFold con referencia del año. Lo que sí mueve la validación es quitar las otras 6 cifras descartadas: el frijol pasa de −18.9 a −8.4 por una sola fila (Yamango 2017, 4.43 t/ha). Ninguna variante le da skill positiva al clima fuera de algodón, uva y limón. Las salidas de siempre quedan en modo crudo; propongo pasar a con_rescate en la ronda 6, cuando Piura Datos publique la marca en `evidencia_observada.csv`.

### R5.7 Tabla final: recomendación por cultivo y zona si falta cada dato (motor consolidado)

Script `experimentos/motor_tabla_final.py` (se corre desde `consolidado/motor`). Salidas `experimentos/motor_tabla_final.csv` (los 14 cultivos anuales) y `motor_tabla_final_resumen.csv`. Base: parcela de 1 ha en el punto de la zona, siembra en agosto, horizonte 6 meses, escenario normal, napa sin dato, CEw del río publicado de la zona (Bajo, escenario 1.5 del motor; motor de las 07:53, `cew_por_zona.csv` de las 07:57), pH y profundidad de `profundidad_ph_por_zona.csv`, pendiente [0, p90] de `pendiente_por_zona.csv`, sin dotación. "Hoy" usa la ECe zonal tal como está (desconocida en 4 zonas). "Base" pone el rango hipótesis 0.5-12 en esas 4 zonas, que no es un dato. Celda: puesto en el ranking del motor; "s/d" = sin_datos; "sec a→b" = secuencias de 2 cultivos viables que lo incluyen, si cambian. Se muestran los 6 primeros de cada zona.

Lectura.
1. **Sin ECe no hay recomendación.** Quitar la ECe deja todos los cultivos en sin_datos en las 5 zonas. Hoy pasa en 4 zonas.
2. **CEw más napa a 3 m reemplaza a la ECe.** Con la ECe zonal de hoy y napa a 3 m, el motor da la misma lista que con el rango hipótesis (última columna).
3. **Sin CEw el orden no cambia, pero se caen las secuencias.** El cultivo aceptado sigue en su puesto. Las rotaciones de 2 campañas pasan de 10 a 0 (en Alto de 9 a 1; frijol de palo conserva 5), porque la ECe de la segunda campaña queda desconocida.
4. **pH y profundidad reordenan.** Sin pH o sin profundidad, el frijol verde sube al 2.º (al 1.º en San Lorenzo) y los demás bajan un puesto. Sin profundidad, el arroz pierde todas sus secuencias en Bajo (6.º a 7.º) y en Alto (5.º a 8.º).
5. **La pendiente no cambia nada.** El p90 de la pendiente DEM (≤ 5.1 %) queda bajo el umbral de todos los cultivos.
6. **Napa a 1 m** recorta secuencias solo en Bajo (10 a 9; arroz 10 a 5) y Alto (9 a 8; arroz 9 a 5), sin cambiar el orden.
7. El orden es casi igual en las 5 zonas porque el motor ordena por alertas y faltantes antes que por margen. Caupí, arveja y frijol grano encabezan en 4 zonas; en San Lorenzo, arveja, frijol grano y maíz amarillo duro. Las diferencias entre zonas salen de pH y profundidad.

| Zona | Cultivo | Hoy (ECe zonal) | Base (ECe 0.5-12) | Sin ECe | Sin pH | Sin profundidad | Sin pendiente | Sin CEw | Napa 1 m | Hoy + napa 3 m |
|---|---|---|---|---|---|---|---|---|---|---|
| Chira | caupi | s/d | 1/12 (sec 10) | s/d (sec 10→0) | 1 | 1 | 1 | 1 (sec 10→0) | 1 | 1 |
| Chira | arveja | s/d | 2/12 (sec 10) | s/d (sec 10→0) | 3 | 3 | 2 | 2 (sec 10→0) | 2 | 2 |
| Chira | frijol grano | s/d | 3/12 (sec 10) | s/d (sec 10→0) | 4 | 4 | 3 | 3 (sec 10→0) | 3 | 3 |
| Chira | maiz amarillo duro | s/d | 4/12 (sec 10) | s/d (sec 10→0) | 5 | 5 | 4 | 4 (sec 10→0) | 4 | 4 |
| Chira | cebolla | s/d | 5/12 (sec 10) | s/d (sec 10→0) | 6 | 6 | 5 | 5 (sec 10→0) | 5 | 5 |
| Chira | frijol verde | s/d | 6/12 (sec 10) | s/d (sec 10→0) | 2 | 2 | 6 | 6 (sec 10→0) | 6 | 6 |
| Bajo | caupi | 1 | 1/12 (sec 10) | s/d (sec 10→0) | 1 | 1 (sec 10→9) | 1 | 1 (sec 10→0) | 1 (sec 10→9) | 1 |
| Bajo | arveja | 2 | 2/12 (sec 10) | s/d (sec 10→0) | 3 | 3 | 2 | 2 (sec 10→0) | 2 (sec 10→9) | 2 |
| Bajo | frijol grano | 3 | 3/12 (sec 10) | s/d (sec 10→0) | 4 | 4 | 3 | 3 (sec 10→0) | 3 (sec 10→9) | 3 |
| Bajo | frijol verde | 4 | 4/12 (sec 10) | s/d (sec 10→0) | 2 | 2 | 4 | 4 (sec 10→0) | 4 (sec 10→9) | 4 |
| Bajo | maiz amarillo duro | 5 | 5/12 (sec 10) | s/d (sec 10→0) | 5 | 6 (sec 10→9) | 5 | 5 (sec 10→0) | 5 (sec 10→9) | 5 |
| Bajo | arroz | 6 | 6/12 (sec 10) | s/d (sec 10→0) | 6 | 7 (sec 10→0) | 6 | 6 (sec 10→0) | 6 (sec 10→5) | 6 |
| Medio | caupi | s/d | 1/12 (sec 10) | s/d (sec 10→0) | 1 | 1 | 1 | 1 (sec 10→0) | 1 | 1 |
| Medio | arveja | s/d | 2/12 (sec 10) | s/d (sec 10→0) | 3 | 3 | 2 | 2 (sec 10→0) | 2 | 2 |
| Medio | frijol grano | s/d | 3/12 (sec 10) | s/d (sec 10→0) | 4 | 4 | 3 | 3 (sec 10→0) | 3 | 3 |
| Medio | maiz amarillo duro | s/d | 4/12 (sec 10) | s/d (sec 10→0) | 5 | 5 | 4 | 4 (sec 10→0) | 4 | 4 |
| Medio | cebolla | s/d | 5/12 (sec 10) | s/d (sec 10→0) | 6 | 6 | 5 | 5 (sec 10→0) | 5 | 5 |
| Medio | frijol verde | s/d | 6/12 (sec 10) | s/d (sec 10→0) | 2 | 2 | 6 | 6 (sec 10→0) | 6 | 6 |
| Alto | caupi | s/d | 1/13 (sec 9) | s/d (sec 9→0) | 1 (sec 9→10) | 1 | 1 | 1 (sec 9→1) | 1 (sec 9→8) | 1 |
| Alto | frijol grano | s/d | 2/13 (sec 9) | s/d (sec 9→0) | 3 (sec 9→10) | 3 | 2 | 2 (sec 9→1) | 2 (sec 9→8) | 2 |
| Alto | maiz amarillo duro | s/d | 3/13 (sec 9) | s/d (sec 9→0) | 4 | 4 (sec 9→8) | 3 | 3 (sec 9→1) | 3 (sec 9→8) | 3 |
| Alto | frijol verde | s/d | 4/13 (sec 9) | s/d (sec 9→0) | 2 (sec 9→10) | 2 | 4 | 4 (sec 9→1) | 4 (sec 9→8) | 4 |
| Alto | arroz | s/d | 5/13 (sec 9) | s/d (sec 9→0) | 6 | 8 (sec 9→0) | 5 | 5 (sec 9→1) | 5 (sec 9→5) | 5 |
| Alto | frijol de palo | s/d | 6/13 (sec 5) | s/d (sec 5→0) | 7 (sec 5→0) | 5 (sec 5→6) | 6 | 6 | 6 | 6 |
| San Lorenzo | arveja | s/d | 1/12 (sec 10) | s/d (sec 10→0) | 2 | 2 | 1 | 1 (sec 10→0) | 1 | 1 |
| San Lorenzo | frijol grano | s/d | 2/12 (sec 10) | s/d (sec 10→0) | 3 | 3 | 2 | 2 (sec 10→0) | 2 | 2 |
| San Lorenzo | maiz amarillo duro | s/d | 3/12 (sec 10) | s/d (sec 10→0) | 4 | 4 | 3 | 3 (sec 10→0) | 3 | 3 |
| San Lorenzo | cebolla | s/d | 4/12 (sec 10) | s/d (sec 10→0) | 5 | 5 | 4 | 4 (sec 10→0) | 4 | 4 |
| San Lorenzo | caupi | s/d | 5/12 (sec 10) | s/d (sec 10→0) | 6 | 6 | 5 | 5 (sec 10→0) | 5 | 5 |
| San Lorenzo | frijol verde | s/d | 6/12 (sec 10) | s/d (sec 10→0) | 1 | 1 | 6 | 6 (sec 10→0) | 6 | 6 |

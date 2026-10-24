# Esquema del modelo de rotación (Piura Modelos, ronda 2)

Versión 2 (v2b), 24-oct-2026. La sección "Cambios de la ronda 2" manda sobre el texto de la versión 1 donde choquen. Código en `scripts/`, parámetros en `params/`, todo se reproduce con `bash run_all.sh` (semilla 42).

## Tipos

| objeto | dónde | contenido |
|---|---|---|
| Cultivo | `params/cultivos.csv` | fenología FAO-56 (L, Kc), Zr y p (T22), Ky (T24), umbral ECe y pendiente b (T23), NPK kg/t (FAO PNB16 T29), rendimiento y precio regional (DRAP 2015-2024), costo por ha (ENA 2018), tolerancia a mal drenaje, pendiente máxima. Cada grupo de columnas trae su fuente y su estado |
| Escenario de parcela | `params/escenario_rangos.csv` | lo que se le pide al usuario o se deduce del lugar, con rango y estado |
| Clima | `data/power/<zona>.csv` | NASA POWER diario 2000-2025 (T, Tmax, Tmin, RH, u2, Rs, lluvia, elevación) |
| Demanda de agua | `data/demanda_agua.csv` | ETc, Peff y riego neto por zona × cultivo × año × mes de siembra |

## Funciones

- `agua.et0_pm(df, lat)` ET0 Penman-Monteith FAO-56 diaria.
- `agua.curva_kc(cultivo)` Kc diario por etapas (ini, desarrollo, media, final).
- `agua.p_efectiva(lluvia)` lluvia confiable FAO/AGLW por bloques de 30 días.
- `modelo.evaluar(escenarios)` devuelve rendimiento, margen, viabilidad y el filtro que falla, por cultivo.
- `modelo.ranking(res)` ordena solo los viables. Si ninguno pasa, el top-1 es "ningún cultivo evaluado es viable" (código -1).

## Cálculo por cultivo

1. Agua. Oferta = Peff + riego bruto × eficiencia + 0.5 × TAW × Zr − agua extra (solo arroz, 600 mm, hipótesis por inundación y percolación). ETa = min(oferta, ETc). Yw = 1 − Ky (1 − ETa/ETc) (FAO-33).
2. Sal. Ys = 1 − b/100 × (ECe − umbral) (Maas-Hoffman, FAO-56 T23).
3. Sanidad. Repetir familia botánica resta 10 % al rendimiento (hipótesis; ronda 2 usa `plagas_hospedantes_condiciones_v2.csv`).
4. Rendimiento = rendimiento regional DRAP × factor_rend × Yw × Ys × Ysanidad.
5. NPK. Demanda = rendimiento × kg/t. Oferta N = N mineral del suelo + crédito si el previo es leguminosa. Las leguminosas no piden N. El déficit se divide por la eficiencia de recuperación (N 0.5, P 0.25, K 0.6, hipótesis) y se valoriza con el precio del fertilizante. Como el costo ENA ya incluye la fertilización típica, al margen solo entra la diferencia frente al suelo central.
6. Margen (PEN/ha) = rendimiento × precio en chacra × factor_precio − costo ENA × factor_costo − delta de fertilizante.

## Filtros duros (van antes del margen)

| filtro | regla | estado del umbral |
|---|---|---|
| salinidad | Ys < 0.5 (pérdida > 50 %) | umbral y pendiente medidos (FAO-56 T23); el corte en 50 % es hipótesis |
| agua | Yw < 0.5 | Ky de FAO-56 T24; el corte es hipótesis |
| drenaje | drenaje malo y cultivo que no lo tolera (solo arroz lo tolera) | hipótesis |
| pendiente | pendiente > máximo del cultivo (arroz 1 %, resto 8 %) | hipótesis |

Un cultivo que no pasa un filtro no se rankea aunque su precio sea alto. La sal y el agua no se compensan con precio, como pide `criterios_modelo.md`. Un dato faltante no se trata como cero. Hoy el modelo usa el valor central del rango y lo marca. En la ronda 2 debe propagar el rango completo y reportar el intervalo del margen.

## Cambios de la ronda 2

| pieza | dónde | qué hace | fuente o estado |
|---|---|---|---|
| zonas | `params/zonas.csv` | 5 zonas (Chira-Sullana, Bajo, Medio y Alto Piura, San Lorenzo) con dotación ANA m³/ha y eficiencia operativa | ANA PGRH Chira-Piura p.155 |
| agua de riego | `modelo.rango()` | agua_riego_mm = dotación × fracción U(0.5, 1.0); eficiencia U(0.6·ef, ef) | dato de zona + hipótesis de fracción |
| agua del arroz | `modelo.evaluar()` | riego en parcela = agua_arroz_m3_ha / 10, sin eficiencia; extra 150-780 mm | ESCO arroz Piura 2024 (10000-18000 m³); FAO Irrigation Water Needs |
| rendimiento por zona | `params/rend_zona.csv`, `scripts/rend_zona.py` | producción/cosecha DRAP por zona; regional si hay < 5 distrito-año o < 200 ha | DRAP 2015-2024 |
| sanidad | `modelo.evaluar()` | castigo pen_sanidad U(0.05, 0.20) solo si previo y candidato comparten agente | `plagas_hospedantes_condiciones_v2.csv`; magnitud hipótesis |
| costos | `params/escenario_rangos.csv` | factor_costo U(1.0, 2.11) sobre ENA 2018 | ESCO 1.67×, LATAM maíz 2.11× |
| intervalo | `scripts/intervalo.py` | 20000 sorteos por zona y mes; P10/P50/P90, P(viable), P(top-1), P(ninguno) | semilla 42 |
| escenario central | `scripts/central.py` | top-3 con valores centrales por zona y mes | prueba del motor |
| adversarial | `scripts/adversarial.py` | fija un supuesto a la vez y mide el cambio de ganador | `resultados/adversarial.csv` |
| perennes | `scripts/perennes_agua.py` | riego neto FAO-56 de banano, limón y uva contra la dotación; fuera del ranking | mango sin Kc |
| eventos | `scripts/validacion.py` | ICEN, lluvia dic-abr y días cálidos feb-abr en la validación | empeoran LOYO, no entran al modelo |

En el paso 1 del cálculo, para el arroz la oferta es Peff + agua_arroz_m3_ha/10 + 0.5·TAW·Zr − agua_extra_arroz_mm. Para el resto es Peff + agua_riego_mm × eficiencia + 0.5·TAW·Zr. El castigo por familia de la versión 1 ya no existe.

## Qué se le pide al usuario y qué sale de la ubicación

| feature | origen | permutación v2 (v1) | ablación v2 (v1) |
|---|---|---|---|
| CE del suelo (ECe) | usuario (análisis) o mapa | 43.0 % (33.1) | 39.2 % (34.4) |
| drenaje / napa freática | usuario | 29.8 % (25.5) | 18.5 % (15.9) |
| agua de riego por campaña | usuario, junta de usuarios o dotación ANA de la zona | 15.4 % (35.2) | 11.3 % (25.8) |
| eficiencia de riego | usuario o ANA por zona | 11.0 % (10.0) | 8.4 % (8.4) |
| mes de siembra | usuario | 8.9 % (6.9) | 9.6 % (7.7) |
| año climático | ubicación (POWER) | 7.5 % (6.0) | 5.6 % (4.5) |
| costo de producción | usuario o ENA/ESCO | 6.8 % (4.0) | 11.4 % (3.4) |
| rendimiento esperado | historial del usuario o DRAP por zona | 6.8 % (3.6) | 5.0 % (2.7) |
| textura del suelo (TAW) | usuario o mapa | 5.9 % (3.9) | 4.6 % (3.0) |
| precio esperado | DRAP o mercado | 5.2 % (2.7) | 3.9 % (2.0) |
| pendiente | usuario o DEM | 5.1 % (0.3) | 13.2 % (0.8) |
| cultivo previo | usuario | 0.5 % (2.5) | 0.7 % (1.6) |
| P, N, K del suelo | análisis de suelo | 1.5, 0.9, 0.3 % | 1.4, 0.9, 0.2 % |

Las ETc y la lluvia efectiva salen de la ubicación (POWER + FAO-56). Lo demás debe pedirse.

## Ronda 3

### Cadena

`rendimientos_observados` → `cargar_evidencia` (lint del CONTRATO, `data/evidencia_modelo.csv`) → `rend_zona` → `agua` → `importancia` → `publicar_ranking` → `central` → `intervalo` → `adversarial` → `perennes_agua` → `validacion` → `estabilidad`. Todo en `run_all.sh`.

### Cambios de componentes

| componente | ronda 3 | fuente |
|---|---|---|
| precios | soles de 2018 (IPC Lima BCRP PN01271PM, promedio anual, base 2018 = 1) para empatar con costos ENA 2018 | `data/ipc_lima_bcrp.csv` |
| algodón | ALGODON PIMA + ALGODON genérico | DRAP |
| rendimiento por zona | si la zona no llega a n ≥ 5 y 200 ha: mediana de Piura Datos de la zona con n ≥ 3 (`n_bajo`); si no, regional `n_bajo` | `scripts/rend_zona.py` |
| agua | U por zona entre 0.5 × dotación y 1.0 × dotación máxima, central 0.75 × promedio; dotación asignada, no entregada | ANA PGRH p.155; Castillo Mimbela 2007 (San Lorenzo 15191) |
| drenaje | binario con P = 0.341 | Santayana 2012 (costa peruana) |
| mango | Kc por fase y duraciones de 'Palmer' (Petrolina), `analogo_externo`; conteo de días > 32/33 °C por mes | Silva Junior et al. 2023; PMC9837111; Issarakraisila y Considine 1994 |

### El FEN como escenario y no como feature

El año climático dejó de ser una feature que se sortea. Ahora es un escenario fijo:
- `normal`: campañas 2001-2024 sin 2017 ni 2023 (se sortea una).
- `fen_2017`: campaña 2017 (siembras ago-2016 a jul-2017; ICEN costero moderado).
- `fen_2023`: campaña 2023 (siembras ago-2022 a jul-2023; ICEN fuerte).

Para cada siembra el año de clima es `campaña − 1` si el mes de siembra es agosto o después, y `campaña` si no (`MES_CORTE = 8`). La importancia y el top-1/top-3 se calculan por separado en cada escenario (`ranking_features.csv`, columna `escenario`; `resultados/top_por_escenario.csv`). OAT y Sobol solo en `normal`. Razón: el FEN no es algo que el agricultor desconozca y haya que medir; es una condición del año que se anuncia (ENFEN) y se elige como escenario.

Límite: el FEN entra solo por el clima POWER (más lluvia, menos Tmax). No hay daño por inundación, erosión ni plagas asociadas, así que el escenario FEN puede verse mejor que el normal para cultivos limitados por agua.

### Clima por zona

Las 5 zonas usan 5 puntos POWER, pero Chira-Sullana, Medio Piura y San Lorenzo caen en la misma celda MERRA-2. Temperatura, humedad, viento y lluvia son los mismos en las tres. Hay 3 climas distintos. Para separar las tres zonas hacen falta estaciones SENAMHI o CHIRPS para la lluvia.

### Qué se le pide al usuario (ronda 3, ablación, escenario normal, promedio de zonas)

| feature | origen | ablación r3 | estabilidad |
|---|---|---|---|
| CE del suelo (ECe) | análisis de suelo | 33.4 % | 1.ª en 4 zonas con el rango base; cae si el rango real fuera 0.5-4 |
| drenaje / napa | usuario | 31.8 % | 1.º o 2.º en todas las variantes |
| pendiente | usuario o DEM | 18.5 % | top-5 en el 100 % de las corridas |
| costo de producción | usuario o ESCO/ENA | 10.3 % | 4.º, no robusto en Bajo Piura |
| agua por campaña | junta de usuarios o dotación | 8.2 % | 4.º-5.º en Chira, Medio y San Lorenzo |
| eficiencia de riego | usuario o ANA | 5.6 % | |
| rendimiento esperado | historial o DRAP por zona | 4.1 % | |
| mes de siembra | decisión del usuario | 4.0 % | se recorre, no se pide como dato |
| precio esperado | DRAP o mercado | 3.0 % | |
| textura (TAW) | usuario o mapa | 2.7 % | |
| cultivo previo | decisión o historial | 0.6 % | |
| año FEN | escenario ENFEN | no aplica | ver tabla de escenarios |

## Ronda 4

### Cadena

`descargar_power` → `descargar_clima_zona` → `rendimientos_observados` → `cargar_evidencia` → `rend_zona` → `agua` y `validacion` con POWER (para comparar) → `agua` con el clima activo → `importancia` → `publicar_ranking` → `central` → `intervalo` → `adversarial` → `perennes_agua` → `validacion` → `estabilidad`. Clima activo por defecto `CLIMA=zona`; `CLIMA=power` reproduce la ronda 3.

### Cambios de componentes

| componente | ronda 4 | fuente |
|---|---|---|
| clima | un punto por zona (`data/clima_zona/`). T y HR de ERA5-Land; viento (10 m a 2 m, FAO-56 ec. 47), radiación y lluvia de ERA5 0.25°, salvo lluvia CHIRPS en Alto Piura y San Lorenzo. 2000-2025 | Open-Meteo archive; ClimateSERV; `scripts/descargar_clima_zona.py` |
| chequeo de lluvia | Miraflores 1-27 mar 2017 = 506.3 mm: ERA5 +23 %, POWER -33 %, CHIRPS -96 %. CHIRPS descartado en la costa | walac.pe; doi 10.1002/joc.7567 |
| ECe | rango por zona (antes uno regional). Bajo 1.2/4.0/12.0; Medio 1.2/2.74/4.3; Chira 1.0/1.36/4.3; Alto 0.8/1.15/4.3; San Lorenzo 0.6/1.63/4.3 | `params/zonas.csv`, columna `fuente_ece` |
| drenaje | P por zona, DelaTorre 1986 (ILRI): Chira 0.505, Medio y Bajo 0.386, Alto 0.261, San Lorenzo 0.342; alternativa baja = solo moderada a severa | `params/zonas.csv`, `fuente_drenaje` |
| pendiente | Bajo Piura 0.03-0.05 % (Banco Mundial 1979, Report 2539-PE); las otras zonas siguen con el rango global hipótesis | `params/zonas.csv`, `fuente_pendiente` |
| inundación FEN | solo `fen_2017`: P de perder la campaña Chira 0.004, Bajo 0.021, Medio 0.046 (EMSR199 × WorldCover, cota inferior). Alto, San Lorenzo y `fen_2023`: NO MODELADO | `suelos/datos/zonas_ece_drenaje_fen.csv`; `P_INUND` en `modelo.py` |
| intervalo | multiplicador de rendimiento 1 ± W, W = CV/√n (tope 0.9) por cultivo y zona | `scripts/intervalo.py`, columnas `n_rend`, `w_rend` |
| algodón 2015 | se excluye: año parcial en DRAP (0.71 t/ha frente a 2.71-4.33 en 2016-2022). Bajo Piura queda en 3.09 t/ha | Piura Datos, `respuestas_a_modelos.md`; recalculado acá |
| evidencia | se lee la columna `zona` nueva de `evidencia_observada.csv`; Medio y Bajo por separado, juntos solo si la zona sola tiene n < 3 | `scripts/cargar_evidencia.py` |

### Etiqueta FEN (corregida por Territorio desde IGP)

- `fen_2017` = campaña 2016-17, El Niño costero moderado, ICEN máx dic-abr 1.31.
- `fen_2023` = campaña 2022-23, El Niño costero fuerte, ICEN máx dic-abr 2.11.

Fuente: `suelos/datos/clima/clasificacion_campanias_icen.csv` (ICEN de http://met.igp.gob.pe/datos/ICEN.txt). El modelo elige el año por campaña, no por la etiqueta, así que la corrección no cambia ningún número. Cambia el texto de `publicar_ranking.py`. `validacion.py` lee `icen_max_dic_abr` y `enso_costero` del archivo corregido en cada corrida. "Normal" sigue incluyendo otras campañas Niño (2016 y 2024 fuertes).

### CE de campo no es ECe

Las CE de campo que trajo Piura Datos (Alto 0.46-0.6, Medio 0.95, Bajo 3.44-8.2 dS/m) no dicen el método de extracto. Una CE 1:1 o 1:2.5 no es ECe y la conversión depende de la textura, así que no convertí nada. Entran como alternativas de estabilidad (`ece_campo_alto_medio`, `ece_campo_bajo`), leídas como si fueran ECe, y no como rango base.

### Qué se le pide al usuario (ronda 4, ablación, escenario normal, promedio de zonas)

| feature | ablación r3 | ablación r4 | por qué cambió |
|---|---|---|---|
| drenaje / napa | 31.8 % | 36.5 % | P por zona, más alta en el Chira (0.505) |
| pendiente | 18.5 % | 29.7 % | sin dato fuera de Bajo: el rango global hipótesis pesa más cuando la ECe deja de pesar |
| costo de producción | 10.3 % | 14.6 % | |
| CE del suelo (ECe) | 33.4 % | 12.8 % | rango por zona: fuera de Bajo Piura la ECe queda bajo el umbral de casi todos los cultivos. En Bajo sigue 1.ª (48.2 %) |
| agua por campaña | 8.2 % | 7.6 % | riego neto con clima por zona 16-31 % menor que con POWER |
| rendimiento esperado | 4.1 % | 7.0 % | intervalo más ancho donde n es chico |
| mes de siembra | 4.0 % | 5.6 % | |

### CEw (ronda 4, pedido del coordinador)
Corrección ronda 5: esta frase describe MI MODELO PROPIO (`modelo/scripts/modelo.py`), no el motor consolidado del equipo (`consolidado/motor`), que sí usa la CEw (ver «CEw en el motor consolidado (ronda 5)»). Mi modelo no tiene entrada de CEw. Si falta, no bloquea, no pone un valor por defecto y no ensancha el intervalo; la salinidad viene solo de `ece_ds_m`. Regla probada aparte en `experimentos/exp_cew.py`: ECe efectiva = max(ECe suelo, 1.5·CEw) (FAO-29, Ayers y Westcot 1985, Tabla 4 nota 2, https://www.fao.org/4/t0234e/T0234E03.htm; LF 0.15-0.20; no vale con napa somera). Resultados en `resultados.md` R4.6. No entra al motor hasta tener CEw de canal por zona.

### Reproducibilidad (ronda 4)
Dos corridas limpias de `run_all.sh` en copias: 45 de 45 salidas con md5 idéntico entre ellas, incluido el clima descargado. El árbol principal difería solo en `data/evidencia_modelo.csv` y `resultados/lint_evidencia.csv`, porque Piura Datos actualizó `evidencia_observada.csv` después de mi corrida. Tras rehacer `cargar_evidencia.py`: 45 de 45 iguales.

## Ronda 5

### Cadena
Igual que la ronda 4, con tres cambios de entrada. La lluvia es PISCOp v2.1 mensual por zona (`scripts/lluvia_mensual.py`, LLUVIA=pisco), con CHIRPS, POWER y la lluvia de r4 como alternativas. La ECe zonal es desconocida en Chira, Medio, Alto y San Lorenzo y cae al rango hipótesis 0.5-2-12 de `escenario_rangos.csv` (HWSD descartado como fuente de ECe; queda solo como contexto). La pendiente sale de `suelos/datos/pendiente_por_zona.csv` (GLO-30 + WorldCover), salvo Bajo, que sigue con Banco Mundial 1979.

### Qué se le pide al usuario (ronda 5, ablación, escenario normal, promedio de zonas)

| feature | ablación r4 | ablación r5 | por qué cambió |
|---|---|---|---|
| CE del suelo (ECe) | 12.8 % | 36.8 % | sin HWSD no hay ECe zonal fuera de Bajo; vuelve el rango hipótesis ancho |
| drenaje / napa | 36.5 % | 36.6 % | |
| costo de producción | 14.6 % | 13.2 % | |
| pendiente | 29.7 % | 6.9 % | rango DEM más estrecho que la hipótesis 0-1-5 |
| agua por campaña | 7.6 % | 6.3 % | |

En el motor consolidado el orden es otro, porque allí un dato ausente no se sortea sino que deja el filtro sin evaluar. Lo que se pide por parcela, en orden, es la ECe (sin ella no hay recomendación), la CEw de la fuente de riego más la profundidad de napa (juntas reemplazan a la ECe solo si la napa está a 2 m o más) y la dotación de agua por mes.

### CEw en el motor consolidado (ronda 5)

Medido contra `consolidado/motor` (`experimentos/cew_motor.py`, `cew_motor_variantes.py`, `motor_tabla_final.py`) y contra mi modelo (`experimentos/exp_cew_variantes.py`). Detalle en `resultados.md` R5.1, R5.2 y R5.7.

Qué hace hoy el motor. Toma max(ECe, 1.5·CEw) solo con napa ≥ 2 m (`filtros._f_salinidad_fao29`) y proyecta la ECe de la campaña siguiente con 1.5·CEw (`estado_suelo.actualizar_tras_cosecha`). Si falta la CEw, la ECe de la segunda campaña queda desconocida. Si además falta la dotación, son 2 filtros críticos no evaluables y el cultivo queda "sin_datos". Es la variante c: deja 0 secuencias de 30.

Recomendación concreta.
1. **CEw conocida** (medida en la toma, canal o pozo de la parcela): usar b2, la regla del motor tal como está (1.5·CEw solo con napa ≥ 2 m). No cambiar nada.
2. **CEw ausente: no bloquear en silencio.** La variante c quita el 100 % de los casos viables en mi modelo (en a tenían cultivo entre 59 y 81 % de los sorteos) y todas las secuencias en el motor, sin que ningún valor de CEw lo justifique. Las variantes b y d no cambian el top-1 del motor en ninguna zona.
3. **En su lugar, escenario marcado por fuente de agua** (d2 o d3). Proyectar la segunda campaña con la CEw de la fuente probable de la zona, marcada `tipo_evidencia="prediccion"` y con aviso en la salida:
   - Chira: reservorio 0.59 (salida de Poechos, ANA oct-2024).
   - San Lorenzo: reservorio 0.47 (UNP c. 2011, 1 muestra, copia de terceros, sin rango).
   - Medio y Bajo: sin dato de canal. Se mantienen los escenarios 0.5 / 1.5 / 3.0 del motor y, si el usuario dice que riega con pozo, el rango de tesis (Bajo 0.13-1.12, Medio 0.16-3.83).
   - Alto: río 0.345-0.741 (ANA 2024).
4. **"No evaluable" solo si también falta el agua** y el usuario no puede dar ni la fuente. Ahí el bloqueo es honesto.
5. **Marcar la estación.** Todas las CEw de `cew_por_zona.csv` son de estiaje (sep-nov) o de estación desconocida; no hay ninguna de avenida. Son un techo estacional y la salida debe decirlo.
6. **No usar los máximos del río de Medio (9.92) y San Lorenzo (9.03)** mientras siga la disputa. Son lecturas ANA 2024 de unidad ambigua (RPiur5 y RPiur4) que Territorio publica desde las 07:57 como "estimado" por balance iónico (`balance_ionico_ana2024.csv`), y Piura Datos da cifras parecidas (≈5 en QSFran1, 9.03, 9.92). Agronomía estima otra cosa (RPiur4 ≈5.1-5.8, QCarn1 ≈3.0-3.3). El motor ya rechaza las 4 lecturas (CEW_EN_DISPUTA). Mi variante d1sd hace lo mismo: Medio U(0.74, 5.98), San Lorenzo U(0.417, 2.32). Con d1sd el top-1 cambia en 0.7 % de los casos en San Lorenzo (24.0 % con d1) y en 10.7 % en Medio (23.4 % con d1).
7. **Napa somera.** Con napa < 2 m la regla 1.5·CEw no vale (FAO-29). El motor ya no la aplica y debe pedir la ECe medida. Esto cubre buena parte de Bajo (49-80 % del área bajo 2 m según FAO/UNALM 1990; 20 de 41 SEV de ANA 2015).
8. **Hueco de integración (H05), cerrado en parte.** Territorio usa ya `ce_agua_riego` con `fuente_agua`, y el motor lo mapea a `ecw` (`catalogo.py`, VARIABLES_ZONA), tomando solo canal, reservorio o toma como valor de zona. Falta que la copia `consolidado/motor/datos_repo/cew_por_zona.csv` (07:50, nombres viejos) se reemplace por la de las 07:57 o que el dato entre por `--integrar`. Esto le toca al dueño del motor.

Mi modelo queda alineado con 1, 5 y 7: la CEw cuenta solo con napa ≥ 2 m y nunca recibe un valor por defecto.

Lluvia (validación de Piura Datos, R6-4). PISCOp acierta marzo de 2017 con ±15 % y da la mitad en febrero. En la sierra queda 15-35 % bajo la normal SENAMHI y se lee como cota baja; mis 5 zonas no son sierra. En el motor, la lluvia p90 de febrero es techo de la lluvia efectiva, así que el sesgo hace el riego neto de febrero conservador; los escenarios El Niño no deben leerse al mes. Detalle en `resultados.md` R5.4.

Rendimientos atípicos (R6-1, aceptada). `scripts/validacion.py` tiene `ATIPICOS=crudo|sin_rescate|con_rescate`. La regla A4 con factor 1.5 rescata 19 cifras; 4 están en mi tabla y solo 1 en mis zonas (maíz amarillo duro, Yamango 2019). La uva de Las Lomas 2016 queda fuera. Detalle en `resultados.md` R5.6b.

### Reproducibilidad (ronda 5)
`run_all.sh` corre la lluvia mensual, las 4 alternativas de lluvia y deja PISCOp como activa al final. Después corre los experimentos de CEw de los dos motores (el consolidado con `python3` del sistema desde `consolidado/motor`, en los dos modos de ECe) y la tabla final.

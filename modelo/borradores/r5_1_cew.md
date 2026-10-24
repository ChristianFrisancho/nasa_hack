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


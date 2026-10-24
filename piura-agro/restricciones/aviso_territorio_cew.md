# Aviso para Piura Territorio: cifra final de las 4 CE ambiguas del informe ANA (ronda 6, reconciliada con Agronomía)

Fuente: ANA-AAA Jequetepeque-Zarumilla, IT N.º 0076-2024 (UH Piura, oct-2024), cuadro de resultados, informes de ensayo MA2434827 y MA2434828. Todos los iones salen del mismo cuadro que la CE. Todas las muestras son de estiaje (sep-nov 2024).
Cálculos: `tools/balance_ionico_ana.py` → `anexos/balance_ionico_ana.csv`; `tools/cew_ana_puntos.py` → `insumos/cew_ana_r4.csv`; `tools/cew_resumen_zona.py` → `anexos/cew_resumen_zona.csv`.
Revisión que se reconcilia: `suelos/revision_agronomia_sobre_territorio_r1.csv`, hallazgos H01, H02, H03 y H06.

## Cifra final propuesta por punto (dS/m)

| Punto | Lectura impresa | Valor | Mín | Máx | Estado | Método |
|---|---|---|---|---|---|---|
| QSFran1 (Quebrada San Francisco) | 5 | **5** | — | — | estimado | balance_ionico |
| RPiur4 (Río Piura, Ocoto Bajo) | 9,03 | **7,86** | 5,56 | 9,03 | estimado | balance_ionico |
| RPiur5 (Río Piura, El Papayo) | 9,92 | **9,92** | — | — | estimado | balance_ionico |
| QCarn1 (Quebrada Los Carneros) | 10,4 | **3,23** | 1,94 | 3,23 | estimado | balance_ionico |

Las tres vías de cálculo de cada punto (USSL, Richards 1954):

| Punto | Error de balance | Cationes/10 | STD/640 | Aniones/10 |
|---|---|---|---|---|
| QCarn1 | −21,5 % | 1,94 | 3,23 | 3,00 |
| QSFran1 | +14,7 % | 5,34 | 5,01 | 3,97 |
| RPiur4 | +23,7 % | 9,00 | 7,86 | 5,56 |
| RPiur5 | −11,7 % | 9,73 | 10,63 | 12,32 |
| RPiur13 (control, µS/cm declarado) | −2,4 % | 6,02 | 5,88 | 6,31 |
| RPiur6 (control, µS/cm declarado) | +4,7 % | 0,71 | 0,71 | 0,64 |

## Punto por punto

- **RPiur4 = 7,86 [5,56-9,03].** El valor central es STD/640, que usa todos los iones a la vez. El mínimo es la vía de aniones (5,56). Coincide con el 5,1-5,8 de Agronomía (H02), pero es una cota baja porque el cloruro impreso (0,09 mg/L) es inverosímil en un agua con 5032 mg/L de sales. El máximo es la lectura impresa, 9,03. La vía de cationes da 9,00, casi lo mismo. Ustedes proponían 9,03 como máximo y lo mantengo: las tres vías tienen como máximo 9,00, pero la lectura impresa coincide con la vía de cationes, así que la tomo como techo. El error de balance es +23,7 %, el peor de los cuatro. Agronomía señala además un HCO3 de 2377 mg/L a pH 8,05, que es anómalo. Por eso el central no es la lectura.
- **QCarn1 = 3,23 [1,94-3,23]. La cifra de 10,4 NO tiene respaldo.** Leída en mS/cm, pediría unos 104 meq/L de cationes, y el cuadro da 19,4. Leída en µS/cm (0,0104 dS/m) es imposible para 2068 mg/L de sales. El valor central es STD/640. El mínimo es la vía de cationes. El máximo es 3,23 y no el 3,3 de Agronomía: el más alto de las tres vías es STD/640, y el 3,3 es el redondeo de HCO3 ~18,6 + SO4 ~11,4 meq/L. Mi vía de aniones da 3,00, dentro del 3,0-3,3 de H01. Aquí sobran aniones (−21,5 %), así que el cloruro bajo no explica el descuadre. Confianza baja (Agronomía propone ≤0,3), y así queda en notas.
- **QSFran1 = 5 y RPiur5 = 9,92** se quedan como estaban, tal como se pidió. Les aviso que **los dos también pasan del 10 % de error de balance** (+14,7 % y −11,7 %). Si en algún momento se les quiere dar rango, las tres vías dan 3,97-5,34 para QSFran1 y 9,73-12,32 para RPiur5. No lo cargué porque no se pidió.

## H03: el Gráfico 6.7 no sostiene el cambio de unidad

El Gráfico 6.7 del informe está en µS/cm, y ahí estos cuatro puntos aparecen casi en cero. El gráfico, entonces, no justifica leerlos en mS/cm; más bien muestra que el informe los graficó con la unidad equivocada. El orden de magnitud lo sostiene el balance iónico punto a punto, con los controles RPiur13 y RPiur6, que cierran con error ≤5 %. Esta nota va en las notas de los 4 puntos dentro de `insumos/cew_ana_r4.csv`. Dividir por 1000 sigue siendo imposible: daría entre 0,005 y 0,010 dS/m, como el agua de lluvia.

## H06: dispersión entre puntos no es incertidumbre de una parcela

El rango 0,42-9,03 que circulaba es la **dispersión entre puntos de monitoreo distintos**, no el error de la CE de una parcela. Para separarlo, el anexo nuevo `anexos/cew_resumen_zona.csv` da, por zona y **por tipo de fuente de agua** (`tipo_fuente_agua`: río, quebrada, canal, pozo, reservorio_canal, sin mezclarlos), n, mediana, P10-P90 (sólo si n≥5), mín y máx. Los estimados entran con su valor central.

| Zona | Tipo de fuente | n | Mediana | P10-P90 | Mín-máx |
|---|---|---|---|---|---|
| alto_piura | río | 5 | 0,51 | 0,40-0,69 | 0,345-0,741 |
| chira | río | 10 | 0,868 | 0,58-4,2 | 0,514-4,98 |
| medio_piura | río | 3 | 5,98 | — (n<5) | 0,74-9,92 |
| san_lorenzo | río | 3 | 0,449 | — (n<5) | 0,417-7,86 |
| san_lorenzo | quebrada | 2 | 4,12 | — (n<5) | 3,23-5 |
| sierra_piura | río | 6 | 0,281 | 0,144-0,441 | 0,0903-0,445 |
| sierra_piura | quebrada | 4 | 0,259 | — (n<5) | 0,061-0,348 |

En bajo_piura (pozo y río), medio_piura (canal) y san_lorenzo (reservorio_canal) no hay cifra: quedan como desconocido. Con RPiur4 corregido, el techo del río en San Lorenzo baja de 9,03 a 7,86 (valor central). Las quebradas (QCarn1, QSFran1) ya no se mezclan con el río.

## Para su cew_por_zona.csv
- QCarn1: reemplazar 10,4 por 3,23 [1,94-3,23], estimado, confianza baja. O dejarlo sin valor, pero no en 10,4.
- RPiur4: reemplazar 9,03 por 7,86 [5,56-9,03], estimado.
- QSFran1 = 5 y RPiur5 = 9,92: sin cambio, ambos estimados, con la advertencia del error de balance.
- Los 29 puntos con unidad declarada no cambian.
- Piura Modelos ya pide no usar los máximos 9,92 y 9,03 mientras siga la disputa. Con esta reconciliación, el 9,03 deja de ser valor central.

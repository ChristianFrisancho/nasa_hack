# Tablazo Sur: ¿una CE medida cambia el orden arveja / caupí?

Ronda 8 · 24-oct-2026 · Piura Territorio. Para el caso Tablazo Sur (Bajo Piura, distrito La Unión).

## Respuesta corta
Sí. La salinidad solo puede mover el orden **hacia el caupí**: el caupí tolera más que la arveja con los dos umbrales de arveja en discusión, así que no hay ninguna ECe en la que la sal favorezca a la arveja. Si el criterio es que la arveja pierda ≥ 10 % de rendimiento relativo, el orden se invierte (pasa a caupí) desde una **ECe de 4.34 dS/m con FAO-61** o de **2.21 dS/m con FAO-56**. En CEw equivalen a 2.89 y 1.47 dS/m, pero solo si se puede suponer ECe = 1.5·CEw. Las 8 ECe que ya hay del Tablazo Sur (3.44–8.2 dS/m, mediana 5.1) caen justo en esa franja: con FAO-56 se invierten los 8 puntos y con FAO-61, 5 de 8. **El escenario que se adopte sí cambia el resultado entre 2.2 y 4.3 dS/m de ECe.**

## Umbrales usados (Maas-Hoffman, Y = 100 − b·(ECe − a); no se inventa ninguno)
| Cultivo | a (dS/m ECe) | b (%/dS/m) | Archivo y fila |
|---|---|---|---|
| Caupí | 4.9 | 12 | `cultivos/fichas_anuales.csv` fila 136 (AN0135, FAO-29 T4) y fila 141 (AN0140, FAO-56 T23); `cultivos/reglas_rotacion.csv` fila 71 |
| Arveja, escenario A (valor principal R7) | 3.4 | 10.6 | `fichas_anuales.csv` filas 479–480 (R3A0001–R3A0002, FAO-61 Anexo 1; Cerda et al. 1982); `para_motor/umbrales_salinidad_propuesta.csv` fila 2 |
| Arveja, escenario B (alternativa rotulada R7) | 1.5 | 14 | `fichas_anuales.csv` filas 264–265 (AN0263–AN0264, FAO-56 T23) |

La CEw sale de ECe = 1.5·CEw, la convención de FAO-29 (FL 15–20 %, sin aporte de napa) que citan las notas de las filas 264 y 136. En el Tablazo, con napa somera, esa conversión no vale; ver más abajo.

## Rendimiento relativo (%) según la ECe
| ECe (dS/m) | CEw equiv. | Arveja A (3.4/10.6) | Arveja B (1.5/14) | Caupí (4.9/12) | ¿Se invierte? (arveja < 90 %) A / B |
|---|---|---|---|---|---|
| 1.5 | 1.00 | 100 | 100 | 100 | no / no |
| 2.21 | 1.47 | 100 | 90 | 100 | no / **sí** |
| 3.44 (mín. Tablazo) | 2.29 | 99.6 | 72.8 | 100 | no / sí |
| 4.34 | 2.89 | 90 | 60 | 100 | **sí** / sí |
| 5.1 (mediana Tablazo) | 3.40 | 82 | 50 | 98 | sí / sí |
| 8.2 (máx. Tablazo) | 5.47 | 49 | 6 | 60 | sí / sí |
| ≥ 13 | ≥ 8.7 | 0 | 0 | 0 (`fichas` fila 140) | ninguno de los dos es viable |

- El 90 % es un criterio mío para fijar dónde se invierte el orden. `cultivos/` no define ninguna regla de decisión por rendimiento relativo. Con otro corte, el cruce se mueve, aunque siempre queda en a_arveja ≤ ECe < 4.9. Con el criterio de «cualquier pérdida», el orden se invierte desde ECe > 3.4 (A) o > 1.5 (B).
- Datos de ECe en el Tablazo: Mendoza Flores 2025, tesis UCV (hdl 20.500.12692/170594), 8 puntos en 40 predios: 5.53, 3.44, 6.05, 3.60, 7.8, 8.2, 3.64 y 4.68 dS/m (fila `ECe_medida_local` de `suelos_piura.csv`). **No declara el extracto.** Si fuera 1:1, la ECe real sería unas 1.8–3.0 veces mayor (6.2–24.6), y entonces el orden se invertiría en todos los puntos con los dos escenarios, y en parte del rango no serviría ningún cultivo.
- Esto no mueve el resultado de r7: el calor de POWER en agosto sigue como nota. Lo que puede invertir el orden en el Tablazo es la sal, no la temperatura.

## Qué hay que medir para decidir
| Qué | Detalle |
|---|---|
| Variable | **ECe** (CE del extracto de pasta saturada, dS/m a 25 °C). Es la variable de los umbrales. La CEw sola no basta en el Tablazo: la napa del Bajo Piura tiene mediana de 2.3 m y el 48.8 % de los sondeos queda por debajo de 2 m (`datos/profundidad_ph_por_zona.csv`), y el ascenso capilar sube la ECe por encima de 1.5·CEw (notas de `fichas` fila 264). |
| Método | **Pasta saturada** (USDA Handbook 60). No 1:1 ni 1:2.5. Si el laboratorio solo hace 1:1, que mida un subconjunto en pasta saturada para calibrar el factor con el mismo suelo. |
| Profundidad | 0–30 cm (zona de raíces de arveja y caupí) y 30–60 cm (sal que sube desde la napa). |
| Época | Fin de estiaje, **abril–mayo, antes de sembrar la arveja**: ahí la sal acumulada en verano está en su punto más alto. Repetir a mitad del ciclo (jul–ago) si hay napa a menos de 2 m. |
| Número | Por predio, 1 muestra compuesta de 10–15 submuestras por profundidad (la decisión es por parcela). Para la zona, al menos los mismos 8 sectores de Mendoza 2025 (p. ej. Río M2 y Tendido medio M6), así se comparan directamente. Con la dispersión observada (DE ≈ 1.8 dS/m), 8 predios separan «por debajo de 2.2», «entre 2.2 y 4.3» y «por encima de 4.3», pero no dan una media zonal fina. |
| Dónde | Tablazo Sur, distrito La Unión (Sechura-La Unión), en los predios con arveja o caupí. |
| Con la misma visita | CEw de la fuente de riego (pozo o canal), profundidad de la napa y CE de la napa. Así se comprueba si vale ECe ≈ 1.5·CEw. |
| Paso más barato | Confirmar en la tesis de Mendoza 2025 qué extracto usó. Si fue pasta saturada, los 8 datos ya deciden con FAO-56 (los 8 se invierten) y dejan 3 de 8 en duda con FAO-61. |

## Para Agronomía (no lo toco)
En `cultivos/reglas_rotacion.csv`, la fila 75 (arveja) empieza su nota con «umbral a=1.5 dS/m (... AN0263)», pero la marca [R7] y el b = 10.6 de esa misma fila corresponden a 3.4/10.6. La cabecera de la nota mezcla los dos escenarios.

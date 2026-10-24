# Validación de PISCOp: marzo de 2017 y sep-nov (ronda 6)

Datos PISCOp y CHIRPS: `clima/pisco_vs_chirps_mensual.csv` y `clima/pisco_chirps_senamhi_estacion.csv`. Cifras públicas: `anexos/validacion_pisco_2017.csv`.

## Marzo de 2017 (Niño Costero)
- **Piura ciudad.** Rollenbeck et al. (2022, Remote Sensing 14:824) dan ene 78,6, feb 205, mar 481 y abr 6,5 mm. PISCOp en San Miguel da 75,9, 98,8, 553,7 y 0,5 mm. Marzo sale +15 %, febrero −52 %, y el total de ene-abr −5 % (729 frente a 771 mm). El artículo da 780 mm para todo 2017.
- **Chulucanas.** El artículo da 1130 mm, en el párrafo de marzo. PISCOp da 957,5 mm, un 15 % menos. Partidor tuvo 1277 mm en marzo, con 28 días de lluvia (no está entre mis estaciones).
- **Chusis, 886,7 mm: no verificado.** No encontré cifras públicas de Chusis, Bernal ni Sechura para marzo de 2017. Mi intento con el boletín de marzo de SENAMHI fue extraer su texto vía Tavily, porque el sitio corta TLS desde el box, y el texto no trae una tabla por estación. Sólo dice que el acumulado en las zonas bajas de Piura y Lambayeque fue "similar en varios puntos a lo acumulado en El Niño 1982-1983". El 886,7 es 1,6 veces el PISCOp de San Miguel y 1,8 veces el registro de Piura en el mismo mes. El orden de magnitud es plausible, pero la cifra exacta queda **desconocida**. CHIRPS da 4,1 mm en ese mes: falla del todo en la costa con FEN, como ya se vio.
- **Lectura.** PISCOp acierta el orden de magnitud del mes extremo en las dos estaciones contrastadas, con un error de ±15 %. Sin embargo, el reparto entre meses puede fallar por un factor de 2 (febrero). El escenario FEN del motor no debe leerse al mes.

## Sep-nov (la campaña de las CEw)
- No encontré boletines públicos con la lluvia de sep-nov de 2017 por estación. La validación usa las normales SENAMHI 1971-2000, que ya estaban en `clima/`.
- **Costa (11 estaciones).** La razón PISCOp/SENAMHI tiene mediana 0,55 y rango 0,16-1,40. En mm, la normal de sep-nov va de 0,9 a 8,4 mm en la temporada, y la media PISCOp de 0,3 a 6,4 mm: Bernal 1,39 frente a 0,3, Chusis 2,17 frente a 1,2, San Miguel 1,85 frente a 0,3. La diferencia absoluta es de 1-2 mm en tres meses, sin efecto para el riego.
- **Sierra (9 estaciones).** La razón mediana es 0,84 y el rango 0,58-1,05. Ahí sí pesa: Huarmaca 90 frente a 59 mm, Chalaco 66 frente a 51. PISCOp tiende a quedarse corto en sep-nov en la sierra. Ojo: el periodo PISCOp es 1981-2000 y el de SENAMHI 1971-2000.
- **Conclusión.** Para sep-nov en la costa, PISCOp vale como "casi cero". En la sierra conviene leer la mediana PISCOp como cota baja (un 15-35 % menos que la normal de estación).

**Ronda 7 (estado de las referencias).** Las cifras de Rollenbeck et al. 2022 están citadas en el texto del artículo, que no nombra la estación de Piura ni da la fuente primaria; la de Chulucanas no dice el mes con todas las letras. Por eso en `validacion_pisco_2017.csv` van con `estado_referencia=estimado` y `tipo_cifra_referencia=citada_en_texto_aproximada`: sirven para un contraste de orden de magnitud, no como medición exacta. Chusis queda `desconocido`: ni el Informe Técnico Extraordinario 001-2017/ENFEN ni el boletín SENAMHI publican su total. Lo regenera `tools/validacion_pisco_2017.py` y lo controla `tools/test_validacion_pisco_2017.py`.

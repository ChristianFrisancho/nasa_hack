# Respuestas de Piura Datos a Piura Modelos

La ronda 2 va al final (sección "Ronda 2"). Lo de la ronda 1 queda como estaba, con cifras ya superadas marcadas allí abajo.

# Ronda 1

Respondo las 9 preguntas de `modelo/para_piura_datos.md`. Cada cifra está en `restricciones/evidencia_observada.csv` (11134 registros), salvo que diga lo contrario. Tipos de evidencia: medicion_local > regional > bibliografico > analogo_externo. "Desconocido" significa que no encontré una cifra con fuente.

Aviso antes de empezar: corregí un error en mi extractor del DRAP (`tools/extraer_drap.py`). Solo sumaba la producción de los meses que también tenían área cosechada. La DRA anota la producción mes a mes y el área al cerrar la cosecha, así que el error bajaba mucho el algodón: la mediana del Medio y Bajo Piura pasaba de 3,50 a 1,00 t/ha. Ya está corregido y mis rendimientos por zona coinciden con `modelo/params/rend_zona.csv`.

## 1. Agua por campaña (mín, mediana y máx por zona y campaña)

**No existe un volumen entregado por campaña y zona que yo haya podido verificar.** Lo que hay es:

| Dato | Valor | Zona | Periodo | Tipo / estado | Fuente |
|---|---|---|---|---|---|
| Dotación anual | 15399 m3/ha/año | Chira regulado | c. 2013-14 | regional / observado | ANA, PGRH Chira-Piura p.155 |
| Dotación anual | 11472 | Medio y Bajo Piura regulado | c. 2013-14 | regional / observado | ANA, PGRH |
| Dotación anual | 9528 | San Lorenzo regulado | c. 2013-14 | regional / observado | ANA, PGRH |
| Dotación anual | 11807 | Alto Piura no regulado | c. 2013-14 | regional / observado | ANA, PGRH |
| Dotación de licencia | 15191 m3/ha/año | San Lorenzo | c. 2007 | regional / observado | Tesina Castillo Mimbela (2007) |
| Volumen de licencia | 578,4 hm3 para 38550 ha atendidas (64550 bajo riego) | San Lorenzo | c. 2007 | regional / observado | misma tesina |
| Volumen agrario programado | 2073,14 hm3 | Sistema Chira-Piura | ago-2025 a jul-2026 | regional / estimado | ANA, nota del 11-ago-2025 sobre el PADH (R.D. 1429-2025-ANA-AAA.JZ) |
| Disponibilidad para la campaña grande | 325,8 hm3 | Agencia Agraria Piura | campaña grande 2025-26 | regional / estimado | DRA Piura, nota del 18-nov-2025 sobre el calendario oficial de la campaña grande |

Lo que se puede decir con fuente:
- No hay cifras de campaña chica, ni mínimos o máximos por zona.
- Las cifras del PGRH las leí en fragmentos de búsqueda del PDF (dos consultas coinciden); el PDF no descarga desde la caja.
- El calendario oficial fija las fechas de la campaña grande 2025-26:
  - arroz: almácigo y siembra directa del 15-dic al 30-ene; trasplante del 10-ene al 28-feb;
  - algodón: siembra del 15-mar al 30-abr.

  La nota no da m3/ha.
- **Conflicto en San Lorenzo:** el PGRH da 9528 m3/ha/año y la tesina da 15191 (578,4 hm3 / 38550 ha ≈ 15000, cálculo mío). La tesina además dice que "en la práctica este parámetro no es utilizado": el personal de campo decide cuánta agua entrega. Recomiendo usar 9528-15191 como rango y no un valor fijo.
- Tu fracción por campaña de 0,5-1,0 sigue sin fuente.

**Respuesta:** desconocido por campaña. Por año y zona: regional, estimado u observado según la fila, con las cifras de la tabla.

## 2. Eficiencia de riego

| Zona | Eficiencia operativa | Riego tecnificado (ha) | Fuente |
|---|---|---|---|
| Chira | 52 % | 15664 | ANA PGRH, línea base c. 2013-14 |
| Medio y Bajo Piura | 57 % | 3469 | ídem |
| San Lorenzo | 59 % | 1058 | ídem |
| Alto Piura | 60 % | 2132 | ídem |
| Sechura | 60 % | 0 | ídem |

Tipo regional, estado observado. El PGRH no dice si la eficiencia operativa incluye la aplicación en parcela. Tu rango [0,6 × ef, ef] es razonable, pero el 0,6 es supuesto. Santayana (2012) dice que en la "zona baja" de los valles costeros la eficiencia es "<30 %". Es una afirmación general, sin dato de Piura.

El área de riego tecnificado está en ha y no como % del área. Para tener el % hay que dividir por el área regada. Las únicas áreas regadas que tengo son de otro año (c. 2001): Chira 33300, Medio y Bajo Piura 37400, San Lorenzo 43800 y Alto Piura 26500 ha. Por eso no calculo el %.

## 3. ECe del suelo agrícola

**Desconocido para Piura.** No encontré ninguna ECe medida en pasta saturada en parcelas agrícolas de Piura.
- siar_1997 (21 registros, medicion_local) es suelo del desierto Olmos-Sechura, no agrícola. Va en cobertura como "no agrícola".
- Lo más cercano es la tesis PUCP de Fox Llerena (2013) en San Pedro de Lloc, cuenca baja del Jequetepeque (costa norte). Mide CE en extracto 1:1, no en pasta saturada:
  - subsector alto: 0,1-2,4 dS/m;
  - subsector medio: 1,3-4,7;
  - subsector bajo: 4,8-9,5.

  Es regional/observado, pero con otro método. No lo convierto a ECe.
- Pista sin cifra: tesis UNP de Rabanal Yocya (2025) sobre salinidad en La Arena, con 8544 ha muestreadas. El repositorio de la UNP no respondió.
- CE del agua subterránea del Medio y Bajo Piura: 0,04-16,83 dS/m (pozos IRHS, estudio ERH de la ANA, medicion_local). Es agua, no suelo.

Tu rango de 0,5-12 dS/m no lo contradice ningún dato, pero tampoco lo respalda ningún dato de Piura.

## 4. Drenaje y napa freática

**Fracción medida por zona: desconocida.** Lo que hay:
- Bajo Piura: "75 % del área agrícola con problemas de sales por mal uso del agua de riego; exceso de áreas con arroz". Fuente: Santayana Vela (2012), presentación en congreso de la UNALM. Regional/estimado, sin método ni umbral. No separa sal de mal drenaje.
- La misma presentación dice que el drenaje parcelario del Medio y Bajo Piura (421 km construidos en la segunda etapa del Proyecto Chira-Piura) "no fue concluido satisfactoriamente" y no tiene mantenimiento.
- Costa peruana: 34,1 % del área bajo riego (298461 de 870000 ha) tiene problemas de drenaje y salinidad (INRENA - De La Torre 2007, citado por Santayana). Bibliográfico; promedio de toda la costa.
- Valle de Virú (costa norte): 11,2 % del área con napa <1 m y 24,8 % entre 1 y 1,5 m. Regional/estimado, otro valle.

Tu P = 0,2 queda por debajo del 34 % costero y muy por debajo del 75 % (sales) del Bajo Piura. Si usas el 75 %, recuerda que mide "problemas de sales", no napa alta.

## 5. Costos por ha

Todos son de la ENA 2018 (INEI, 2021). El costo no incluye depreciación ni gastos administrativos.

| Cultivo | Piura | Mejor análogo | Tipo |
|---|---|---|---|
| Maíz amarillo duro | desconocido | Costa (región natural): 5411,65 PEN/ha, 7551 kg/ha. Perú: 3067,23 (88-16450; n = 846) | analogo_externo |
| Algodón | desconocido | Lambayeque: 4599,14 PEN/ha (costa norte). Perú: 5003,86 (943,70-9842,91; n = 42) | regional (Lambayeque) |
| Frijol | desconocido | Costa: 1531,01 PEN/ha, 1510 kg/ha | analogo_externo |
| Caupí | **desconocido** | La ENA 2018 no lo incluye | — |
| Camote | desconocido | Perú: 3010,98 (649,29-9548,01; n = 37). Lima: 3893,55. Ica: 3013,33 | analogo_externo |
| Arroz (referencia) | 5409,66 PEN/ha (ENA 2018 Piura) | ESCO 2024 Piura: ingreso 10556 PEN/ha (8262-12851) | regional |

## 6. Precio en chacra del algodón

**Sí, es la misma fuente primaria (DRA Piura / SIEA) y el dato DRAP vale.** La fila 2020-24 del Compendio INEI 2025 es un error de copia: es idéntica a la de la alfalfa. Por eso la dejé como desconocida. El DRAP no tiene ese patrón.

Mediana anual por distrito (PEN/kg, sin IGV):

| Año | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|---|---|---|
| Mediana | 3,31 | 3,48 | 3,88 | 3,56 | 2,48 | 2,49 | 5,61 | 6,00 | 3,54 | 4,58 |

- **Unidad:** probablemente algodón en rama (con semilla). La ENA 2018 da un precio al productor nacional de 3,29 PEN/kg, del mismo orden que el DRAP 2018 (3,56). La fibra vale varias veces más. Ninguna fuente lo dice de forma literal, así que es una inferencia.
- **Tipo:** regional/observado. Año: el de la columna.
- El DRAP tiene dos cultivos: "ALGODON PIMA" y "ALGODON" (3404 ha cosechadas en 2015-24, sobre todo en Piura y Sechura). `rendimientos_observados.py` solo usa PIMA.

## 7. Camote por zona

**Sí, hay que separarlo.** Ya está separado en `evidencia_observada.csv`: la zona va en notas. Valores DRAP 2015-24 por distrito y año, en t/ha:

| Zona | n | Mediana | Rango | Ponderado | Ha cosechadas en 10 años |
|---|---|---|---|---|---|
| Valle del Chira | 37 | 16,24 | 11-25 | 17,26 | 5538 |
| Medio y Bajo Piura | 23 | 12,0 | 3-30 | 21,44 | 100 |
| San Lorenzo | 4 | 7,8 | 7,17-8 | 7,75 | 65 |
| Sierra | 109 | 3,0 | 0,67-9,17 | 3,82 | 1856 |

- El 14,2 regional lo domina el Chira, que tiene el 73 % del área cosechada.
- Tu "mediana 4,0" la arrastran los muchos distrito-años de sierra.
- Con menos de 200 ha en 10 años, el Medio y Bajo Piura y San Lorenzo no tienen una referencia de zona confiable.
- El rendimiento regional ponderado cae de 18,7 (2015) a 9,5 (2024). Coincide con la serie departamental del compendio.
- No verifiqué con el portal SIEA (MIDAGRI respondió 504). El DRAP usa los códigos SIEA.

## 8. Agua extra del arroz

No hay dato de la junta de usuarios ni del PGRH. Hay volumen total aplicado según dirigentes arroceros, recogido por agraria.pe:

| Dato | Valor | Periodo | Quién lo dice |
|---|---|---|---|
| Riego por inundación | 18000 m3/ha por campaña | campaña grande 2018 | dirigente gremial (agraria.pe, 21-mar-2018) |
| Secas intermitentes | 10000 m3/ha por campaña | 2018 | ídem |
| Consumo promedio | 12000 m3 "anuales" | c. 2016 | Ángel Zapata, APEAR (agraria.pe, 22-dic-2016) |
| Con secas intermitentes | 8000 m3/ha | c. 2016 | ídem |
| Cuota anual de licencia | 16000 m3/ha/año | c. 2016 | ídem |

Todo es regional/estimado: son declaraciones, no mediciones.
- El 12000 no es "dato DRA", como dice `escenario_rangos.csv`: lo dijo el presidente de APEAR.
- Es ambiguo si "anuales" significa por año o por campaña. En la misma nota, la cuota de 16000 cubre la campaña grande y la chica, lo que sugiere que el 12000 es por año.

Lámina, preparación y percolación por separado: desconocido.

## 9. Formato

`evidencia_observada.csv` tiene estas columnas:

`id_registro, variable, valor, valor_min, valor_max, unidad, cultivo, variedad, etapa, lugar, lat, lon, fecha_o_periodo, fuente, url_o_doi, metodo, tipo_evidencia, estado, notas, fecha_consulta, archivo_origen`

- **No hay columna zona.** En los 9514 registros DRAP, la zona va en `notas` con el formato "Zona: X." (regex `Zona: ([^.]+)\.`). Los valores posibles son Valle del Chira, Medio y Bajo Piura, San Lorenzo, Alto Piura y Sierra.
- En el resto de registros, la zona se deduce del `lugar`. `tools/cobertura.py` tiene la función que lo hace.
- Si estado = desconocido, `valor` va vacío.
- Las filas están ordenadas por tipo de evidencia.
- Propuesta para la ronda 2: añadir una columna `zona` al contrato y separar Medio Piura de Bajo Piura igual que en tu `validacion.py`.

## Las 4 preguntas anteriores

- **Rendimientos con año y zona:** DRAP 2015-24 por distrito, 4675 registros de rendimiento y 4839 de precio. Tienen zona y UBIGEO en notas, y 41 están marcados como atípicos (A4).
- **CE de suelo y de agua:** ver las preguntas 3 y 4.
- **Agua por turno:** desconocido. No encontré turnos por sector ni por mes.
- **Precios:** DRAP por distrito y año para 24 cultivos. Arroz ESCO 2024: 1,85 PEN/kg (1,78-1,92).

# Ronda 2

Tabla al cierre: `evidencia_observada.csv`, 11180 registros, 22 columnas (ahora con `zona`). `tools/test_limpiar.py`: 35 de 35 pasan. Lo nuevo de esta ronda está en `insumos/curado_r2.csv` (47 filas, `tools/insumos_curados_r2.py`). Correcciones a la ronda 1: las dotaciones del PGRH ahora son `estimado` (asignadas, no entregadas) y su línea base es de 2012-2013, no "c. 2013-14"; ya leí el PGRH completo.

## Desacuerdos

1. **Algodón de Bajo Piura (2,75 frente a 3,48).** Propongo **3,09 t/ha**: media ponderada por superficie de 2016-2023 (n = 82 distrito-años, 12403 ha cosechadas), con rango P25-P75 de 3,00 a 4,36. La mediana distrital del mismo periodo es 3,67. Tu 2,75 incluye 2015, que en el DRAP es un año parcial: con 2015 dentro, n = 93, la ponderada baja a 2,75 y el P25 a 1,76. Uso el mismo estadístico que en las otras zonas (ponderado) y solo cambio el periodo. Las dos filas están en `curado_r2.csv`.
2. **Separar Bajo y Medio Piura.** Ya están separados por distrito en el DRAP. Bajo: Catacaos, Cura Mori, El Tallán, La Arena, La Unión y Sechura. Medio: Piura, Castilla y Veintiséis de Octubre. Ahora hay además una razón de suelo para mantenerlos separados: la CE medida en chacra es 0,95 dS/m en el Medio (parcela UNP) y 3,44-8,2 dS/m en el Bajo (Tablazo Sur). El agua sigue sin separarse: la ANA reporta "Medio y Bajo Piura" como una sola unidad. Esas filas no las asigno a ninguno de los dos: quedan con zona vacía y "Zona en conflicto". Son 79 filas; el detalle y la propuesta de un código `medio_bajo_piura` están en `propuesta_contrato_zona.md`. *(Corrección r3: el CONTRATO adoptó `medio_bajo_piura`; las 79 filas ya llevan ese código.)*

## Sus pedidos 12-16 (ronda 3 de ustedes)

**12. ECe en parcelas, con zona.** Encontré las primeras CE de suelo agrícola de Piura. Las tres son `medicion_local` y `observado`. Aviso común: ninguna fuente dice el extracto, así que no están confirmadas como ECe de pasta saturada.

| Zona | CE (dS/m) | n | Lugar y año | Fuente |
|---|---|---|---|---|
| alto_piura | 0,46-0,6 | 3 estaciones | El Huaro, Buenos Aires (Morropón), arroz en monocultivo, 2021 | La Rosa Reyes 2021, tesis UCV (resumen) |
| medio_piura | 0,95 | 1 parcela | Parcela Túpac Amaru, UNP, 2013-14 | Vite Córdova 2015, tesis UNP (resumen) |
| bajo_piura | 3,44-8,2 | 40 predios en 8 grupos | Tablazo Sur, La Unión, 2024 | Mendoza Flores 2025, tesis UCV (tabla 2) |

En Tablazo Sur el PSI va de 7,30 a 17,73 %. Por la clasificación USDA, 5 % de los predios son salinos, 52,5 % sódicos y 42,5 % salino-sódicos. El problema de ese sector es más sodio que sal. Chira y San Lorenzo: sin dato. Es menos de la decena por zona que piden, pero ya alcanza para algo: los tres valores de Alto y Medio están por debajo de 1 dS/m y el Bajo llega a 8,2. El rango 0,5-12 sigue siendo amplio para el Bajo y parece ancho para Alto y Medio.

**13. Fracción con napa alta o mal drenaje por zona.**
- Bajo Piura (área neta 34721 ha, estudio de 1978 citado por Castillo Albines c. 2001): napa alta permanente 21,2 % y temporal 32,2 %; salinos 33 %, salino-alcalinos 59 % (92 % con sales). Es viejo y de fuente secundaria, pero es el único dato por zona que encontré. Napa alta, sumando permanente y temporal: ~53 %.
- Alto Piura: 6595 ha con salinidad leve a fuerte en 1987, 18 % del área cultivada (en 1972 eran 3365 ha).
- Toda la cuenca: 32000 ha con mal drenaje y salinidad (PGRH 2015, `estimado`). Sobre 177414,91 ha bajo riego es ~18 % (cálculo mío).
- Chira, San Lorenzo y Medio Piura: sin dato. La cifra PECHP de 7980 ha no la pude verificar; no está en el PGRH.
- Para tu P: 34,1 % costero queda entre el 18 % de cuenca y el ~53 % del Bajo Piura de 1978.

**14. Pendiente de las áreas bajo riego.** Sin dato. No encontré pendiente por zona de tierras bajo riego. El estudio de 1978 da clases de aptitud para riego del Bajo Piura: clase 2 con 14,9 %, clase 3 con 30,0 %, clase 4 con 32,0 % y clase 5 con 23,1 %. Esas clases combinan suelo, drenaje y topografía; no son pendiente sola, así que no las uses como 0-2 % frente a 2-4 %.

**15. Clima por zona.** No validé `chirps_mensual_zonas.csv` contra estaciones SENAMHI ni busqué esas series esta ronda: quedó fuera de la priorización v3. Lo dejo para la ronda 3.

**16. Kc o lámina del mango en San Lorenzo o Chira.** Sin dato de Kc. Lo más cercano es agua por ha de frutales en San Lorenzo (García Samamé 2024, citando a la supervisión ANA 2013-2018): el módulo es 9800 m3/ha/año y lo realmente distribuido es 6234 m3/ha/año. Es entrega en cabecera, no lámina en parcela. Si tu riego neto del mango sale 1,0-1,9 veces la dotación, la entrega real queda aún más corta.

## Sus puntos 1-11 (revisión de la tabla, ronda 3 de ustedes)

1. **Unidades fuera de la lista.** Hecho: se aceptan solo las de una lista explícita (PEN/kg, PEN/t, m3/ha, m3/ha/año, hm3, ha, PEN/m3 y ahora USD/ha), con aviso y conteo. Cualquier otra falla, y todas fallan con `--estricto`. Pido ampliar el CONTRATO en `propuesta_contrato_zona.md`.
2. **m3/ha frente a mm.** Pendiente de decisión. Propongo mm por campaña y mm/año; si aceptan, convierto las 20 filas.
3. **Duplicados con cifras distintas.** Hecho. Hoy hay 0 claves con cifras distintas, y `limpiar.py` falla si aparece una (hay test). Arroz 10000/18000 quedó como una fila con rango.
4. **Fuente primaria compartida.** Propuesta de columna `fuente_primaria`. Mientras tanto, hacen bien en usar solo DRAP para rendimientos.
5. **Cifras sin rango y sin explicación.** Hecho. Hoy son 0, y `limpiar.py` falla si una cifra sin rango no lo explica en notas.
6. **Dotación ANA como observado.** Hecho: pasó a `estimado` con nota, y `limpiar.py` falla si una dotación, módulo o licencia viene como `observado`. Propongo un estado `asignada`. *(Corrección r3: no se adoptó; quedan `estimado` con método `dotacion_asignada`, 16 filas.)*
7. **La Libertad como regional.** Hecho: Virú y San Pedro de Lloc son `analogo_externo` con "Comparabilidad:". Lambayeque queda `regional` con zona vacía.
8. **Zona en notas con dos formatos.** Hecho: ahora es una columna `zona` con uno de los 7 códigos del CONTRATO o vacía. Ojo, no son sus códigos: `chira` (no `chira_sullana`), `sierra_piura` y `piura_region`.
9. **744 filas sin zona.** Hecho. Quedan 95 vacías: 79 por conflicto Medio-Bajo y 16 fuera de Piura. *(Corrección r3: las 79 son ahora `medio_bajo_piura`; quedan 24 vacías, todas fuera de Piura con "Zona no aplica:".)* Las departamentales van como `piura_region`.
10. **"Medio y Bajo Piura".** No lo asignen a los dos sin marcarlo. Ver el desacuerdo 2 y la propuesta `medio_bajo_piura`.
11. **Frijol de costa.** Sí: en el DRAP el frijol de costa está como "FRIJOL CAUPI CHICLAYO CASTILLA CHILENO GRANO SECO", que en la tabla es `frijol caupí`. Tiene 223 distrito-años de rendimiento en costa (Bajo 91, Chira 51, Alto 42, Medio 13, San Lorenzo 12). "FRIJOL GRANO SECO" (`frijol`) es casi todo sierra: 183 de 184. Para la costa usen caupí.

## Sus P1-P18 (revisión de la ronda 2 de ustedes)

- **P1. Arroz ESCO 6641.** Es kg/ha y ahora tiene `unidad = kg/ha` explícita. No lo convierto.
- **P2. Caña etanol.** DRAP: 188 distrito-años, mediana 16,6 t/ha (0,81-47,45). INEI: 88-139 t/ha. No sé qué mide la fila DRAP (puede ser otra área o caña en otro estado); queda sin explicar. No usen DRAP para caña.
- **P3. Limón y plátano DRAP.** Con el extractor corregido, la mediana distrital del limón es 6,53 t/ha (n = 340) y la del plátano 8,0 (n = 424), no ~0,9. Sigue por debajo del INEI departamental (9-12 t/ha en limón). Sospecho que el DRAP divide por área sembrada y no solo por la cosechada, pero no lo verifiqué. Su decisión de no usar DRAP de perennes me parece prudente.
- **P4. Duplicados INEI.** Resuelto: 0 claves con cifras distintas (ver punto 3).
- **P5. DRAP e INEI.** Sí, comparten fuente primaria (DRA Piura / MIDAGRI-SIEA). No son evidencias independientes. Ver la propuesta de `fuente_primaria`.
- **P6. Rendimientos con valor nulo.** Quedan 76: 75 con `estado = desconocido` y valor vacío, como pide el CONTRATO, y 1 de limón `estimado` con solo rango (13,1-14,5). No se borran.
- **P7. Precio DRAP del algodón.** Sí, ya está en la tabla como fuente alternativa (ver ronda 1, punto 6).
- **P8. Año de la dotación PGRH p.155.** Línea base armada en talleres de 2012-2013; plan publicado por la ANA en octubre de 2015.
- **P9. Eficiencia operativa ANA.** El PGRH no dice si incluye la aplicación en parcela. Sí hay ahora un dato de distribución en San Lorenzo: 39 % de pérdidas en la zona regulada (2013-2018), o sea ~61 % de eficiencia de distribución (cálculo mío, `estimado`). Eso sugiere que el 59 % de la ANA para San Lorenzo es sobre todo conducción y distribución. Su rango 0,6·ef-ef sigue siendo razonable.
- **P10. San Lorenzo no regulado, 28000 m3/ha/año.** No es error de digitación nuestro: el PGRH lo imprime así y el promedio de los no regulados (19903,5) cuadra con 28000 y 11807. Es una dotación (`estimado`). Además, García Samamé (2024) da 143,76 hm3/año usados en la zona no regulada para 3759,95 ha, unos 38000 m3/ha (cálculo mío): ahí el agua usada es muy alta, sobre todo por pérdidas. Úsenlo como cota alta, no como entrega típica.
- **P11. Arroz por campaña.** En San Lorenzo hay cifra de la junta: módulo de 15000 m3/ha en campaña grande y 13500 en chica, y 13563 m3/ha realmente distribuidos (2013-2018, supervisión ANA, vía García Samamé 2024). Para el Bajo Piura (MAD, no arroz), la hoja de costos de la DRA presupuesta 7500 m3/ha. Su 10000-18000 sigue valiendo y San Lorenzo cae dentro.
- **P12. Perennes.** Frutales en San Lorenzo: módulo de 9800 m3/ha/año y 6234 entregados. No encontré la parte de agua subterránea en San Lorenzo ni en Chira.
- **P13. ECe.** Ver pedido 12.
- **P14. ESCO: gastos administrativos 1049 mayores que el indirecto total 780.** Está así en el PDF, no es error de extracción. El propio PDF lo explica: "La suma de los costos desagregados no coincide con el costo promedio directo ni indirecto, debido a que se obtienen a partir de cálculos de promedios individuales". Cada fila es un promedio sobre los productores que reportan ese gasto. Usen el total (780) y no sumen partidas.
- **P15. Costo por ha de Piura de 2022 en adelante.**
  - MAD, Bajo Piura (encuesta 2021, Rodríguez Valdez, tesis UNALM): 5253,2 PEN/ha, de 2470 a 8810, DE 1529, moda 6375. Agua 228 PEN/ha. Rendimiento declarado 7227,3 kg/ha. Es 0,97 veces la ENA 2018 de costa (5411,65): la encuesta no confirma el factor 2,11.
  - El artículo del mismo autor (LATAM 2025) da 1849,06 USD/ha con semilla común y 1994,23 con certificada. Lo dejo en USD porque la tabla mezcla S/ y US$. No cuadra con la tesis y no sé por qué.
  - Algodón Pima, región: 13500 PEN/ha (DRA Piura, marzo de 2022, cifra declarada, `estimado`). Es 2,9 veces la ENA de Lambayeque (4599).
  - Frijol, caupí y camote de Piura: sin dato. Siguen con el análogo ENA.
- **P16. Pendiente.** Ver pedido 14.
- **P17. Columnas.** `unidad` ya existe. `es_duplicado` ya no hace falta, porque no quedan claves con cifras distintas. `fuente_primaria` queda propuesta.
- **P18. ICEN 2023 (para Piura Suelos).** No es mi carpeta y no lo toco. No verifiqué la regla de clasificación. Se lo paso a Piura Suelos tal como lo plantean.

# Ronda 3

Tabla al cierre: `evidencia_observada.csv`, 11238 registros. `tools/test_limpiar.py`: 57 de 57 pasan. Lo nuevo está en `insumos/curado_r3.csv` (16 filas, `tools/insumos_curados_r3.py`) y en la pendiente de Piura Territorio (42 filas `prediccion`).

## Lo que les cambia en la tabla

1. **Zona `medio_bajo_piura`.** Las 79 filas de agua de la ANA para "Medio y Bajo Piura" ya tienen ese código. Si su modelo separa Medio y Bajo, repartan esas filas ustedes y díganlo.
2. **Dotaciones.** Son `estimado` con método `dotacion_asignada`, 16 filas. Son derechos de agua, no entregas.
3. **CE de suelo.** Las 4 filas de chacra llevan método `ce_extracto_no_declarado`. No las traten como ECe de pasta saturada sin un factor, y yo no tengo factor para darles.
4. **Pendiente.** 42 filas `prediccion` de Piura Territorio (DEM de 30 m, sólo píxeles de cultivo WorldCover). En la costa, el área de cultivo con pendiente mayor a 15 % va de 0,0 % a 0,3 %; en la sierra, 51-60 %.

## Costos por ha (todos `analogo_externo`, ninguno de Piura)

| Cultivo | PEN/ha | Fuente | Comparabilidad |
|---|---|---|---|
| papaya | 3940,3 (1092,1-9419,1) | ENA 2018, cuadro 55 | sólo selva; en Piura sería costa con riego |
| frijol verde (vainita, var. Venus) | 10327,07 | DRA Tacna 2014, vía Paxi Mamani 2022 (UNJBG), tabla 5 | costa sur, goteo con bombeo, costo presupuestado |
| frijol caupí | 1531,01 | ENA 2018, frijol grano seco de costa | es Phaseolus, no Vigna; proxy |
| camote | 16340 | MIDAGRI N.° 003-2026, citando a la Univ. Nac. de Cañete 2024 | Cañete; incluye alquiler de terreno (36 %) y gastos financieros (17 %) |
| frijol de palo | desconocido | — | no encontré ninguna hoja de costos |

El camote de Cañete (16340) es 4,2 veces la ENA 2018 de Lima (3893,55) y 5,4 veces la nacional (3010,98), que ya estaban en la tabla. Parte de la diferencia es que la ENA excluye gastos administrativos y financieros, y la cifra de Cañete incluye además el alquiler. Otra parte son seis años de inflación de insumos. No la usen como costo de Piura sin quitar esas partidas.

## CE del agua de riego (dS/m)

| Zona | Valor | Estado | Fuente |
|---|---|---|---|
| chira | 0,373-1,167 | observado, medicion_local | río Chira en Sullana, Coronel Chávez 2021 (UNP), publicado en µS/cm |
| chira (puntos RChir6-8) | sobre 2,5, sin cifra | desconocido | monitoreo ANA 2022 |
| medio_piura | — | desconocido | García Ramos 2022, canal Biaggio Arbulú; no pude leer la tesis |
| bajo_piura | — | desconocido | nota ANA de feb. 2024 (quebrada Sofía sobre el ECA), sin cifra |
| bajo_piura, Tablazo Sur | — | desconocido | la tesis del acuífero de Sechura está en CORE y me lo bloqueó |
| san_lorenzo | — | desconocido | nada encontrado |

Para pozos del Medio y Bajo Piura sigue la fila ANA de agua subterránea: 0,04-16,83 dS/m.

## HWSD contra chacra

HWSD no ordena bien las zonas. En el Bajo Piura da 1,51 dS/m y la chacra (Tablazo Sur) da 3,44-8,2. En Chira da 1,36, en el Medio 2,74 y en el Alto 1,15, y la chacra da 0,10, 0,95 y 0,46-0,6. Si usan HWSD como prior de ECe, en el Bajo Piura se quedan cortos y en las otras zonas se pasan. La tabla completa está en `cobertura.md`.

## Lo que sigue sin dato

- ECe con extracto declarado; CE de suelo en San Lorenzo.
- PECHP 7980 ha: no la encontré en ninguna fuente. Lo más cercano es 7451 ha de napa alta permanente en el Bajo Piura en 1978, que ya está en la tabla como fracción (21,2 %).
- Agua entregada por campaña en Chira y en el Medio y Bajo Piura.
- Kc del mango y CHIRPS contra SENAMHI.

# Ronda 4

Respuesta a sus objeciones R4-1 a R4-11 (`modelo/para_piura_datos.md`). Comprobé cada una con los datos antes de aceptarla o rechazarla. Al final dejo lo que no acepto y por qué.

## R4-1. CE del agua frente a la tabla de Territorio: aceptada en parte

Cargué los puntos de monitoreo ANA de 2024 con `tools/cew_ana_puntos.py` (sale `insumos/cew_ana_r4.csv`, 33 puntos). Antes de convertir revisé la unidad en los dos informes fuente (ANA IT 0076-2024, UH Piura, y IT 0074-2024, UH Chira; copias en `fuentes_r4/`). Las tablas dicen µS/cm. El script busca cada cifra en el texto del PDF y se detiene si no la encuentra. La cifra y la unidad originales quedan en `notas`.

29 puntos entran como `observado`/`medicion_local`. Cuatro no: QCarn1 (10,4), QSFran1 (5), RPiur4 (9,03) y RPiur5 (9,92), del Cuadro 6.3 del informe de Piura. Como µS/cm son imposibles, porque esos mismos puntos tienen bicarbonatos de 959 a 2377 mg/L y calcio de 97 a 506 mg/L. Tampoco cuadran del todo como dS/m: el balance de aniones de QCarn1 da unas 2,5 veces menos. El informe solo marca RPiur13 por encima del ECA, lo que no encaja con 10 dS/m. Los dejé con `valor` vacío, `estado=desconocido`, `metodo=ce_in_situ_unidad_ambigua` y la nota "agua salina > 1 dS/m". **La tabla de Territorio (`suelos/datos/cew_por_zona.csv`) usa esas cuatro cifras como dS/m.** Es probable que sea un error suyo, pero no puedo editar su carpeta. Corregí RPbla1 a 0,0903 dS/m (Territorio tiene 0,09). Los 4 puntos de 2015 (hdl 20.500.12543/2890) no se cargaron porque el repositorio no responde ni por curl ni por fetch.

Hay un test nuevo en `limpiar.py`: un `ce_agua_riego` en dS/m mayor que 30 o menor que 0,01 falla, salvo que `notas` diga "pozo".

## R4-2. Suelos del EIA Olmos-Sechura: aceptada; lo de los pares, no

Las 21 filas `ce_suelo` del EIA quedan con `zona` vacía, `subzona=eia_olmos_sechura_no_agricola` y la nota "Zona no aplica: unidad de suelo de desierto sin uso agrícola". La afirmación de "4 pares repetidos" es falsa. `etapa` distingue epipedón de subsuelo y el id de registro es distinto en cada caso. Las notas ya decían "NO agrícola" desde la ronda 3.

## R4-3. Filas fuera de Piura sin zona: rechazada la propuesta `zona=fuera_piura`

`fuera_piura` no es un valor de `zona` en el CONTRATO, y no lo cambio. Esas filas ya llevan "Zona no aplica:" en `notas`, y `limpiar.py` falla si una fila sin zona no la lleva. Ahora son 51: 21 del EIA, 28 `analogo_externo`, 1 `regional` (INEI Lambayeque, costa norte, que el CONTRATO admite como regional) y 1 `bibliografico` (Santayana 2012, costa peruana en conjunto). Para sacarlas de un agregado basta filtrar `zona != ""`. Los dos casos que no son `analogo_externo` están bien así y no los reetiqueto.

## R4-4. Filas sin cifra: rechazada

El CONTRATO pide que lo que no se sabe quede en la tabla como `desconocido` ("vacío + desconocido antes que un número dudoso"). Si las saco a otro archivo, el motor deja de ver el hueco. Ahora son 91: las 87 de antes más los 4 puntos ANA ambiguos. (Ronda 5: bajan a 88, porque 3 de los 4 puntos ANA pasan a estimado por balance iónico.) Todas son `desconocido`, y el test falla si una fila sin cifra trae otro `estado`. Las de rendimiento son 75.

Mantengo la regla de `valor` vacío con rango. 35 filas traen solo mínimo y máximo porque la fuente publica un rango (26 `observado`, 9 `estimado`). Inventar un punto medio sería poner una cifra que la fuente no da.

## R4-5. kg/ha a t/ha: hecho

`limpiar.py` convierte rendimiento de kg/ha a t/ha antes de validar y deja la cifra original en `notas`. Cambian los id de esas 12 filas. Un test nuevo falla si una variable tiene más de una unidad, salvo tres casos justificados: costo_produccion en PEN/ha y USD/ha (sin tipo de cambio fechado), y modulo_riego y agua_riego_consumo en m3/ha y m3/ha/año (por campaña frente a por año). Renombré el costo de papaya de 337,70 PEN/t a `costo_produccion_por_t`.

## R4-6. Algodón 3,09: de acuerdo, sin cambio.

## R4-7 a R4-11. Lluvia: PISCOp, CHIRPS y estaciones

Script `tools/pisco_vs_chirps.py`. Salidas en `clima/pisco_chirps_senamhi_estacion.csv`, `clima/pisco_vs_chirps_mensual.csv` y `clima/pisco_vs_chirps_resumen.txt`. Usé las mismas 20 estaciones (normal SENAMHI 1971-2000) con PISCOp v2.1 y CHIRPS de 1981-2000. La razón es producto / estación.

**R4-7 (PISCOp como referencia costera): aceptada con reservas.** Reproduje sus cifras. En la costa (n=11) la razón mediana anual es 1,29 para PISCOp y 0,63 para CHIRPS, y la de MAM es 1,14 y 0,17. En marzo de 2017, PISCOp da 336,6 mm en Miraflores y CHIRPS 21,3. En Mallares, 421,8 frente a 26,7. En Chulucanas, 957,5 frente a 543,4 (ustedes tenían 962; la diferencia viene de la celda tomada). Tengo tres reservas:
1. PISCOp asimila las estaciones SENAMHI, así que coincidir con ellas es en parte circular y no es una validación independiente.
2. ~~Su +29 % en la costa sale casi todo del periodo (1,05 reponderado).~~ **Corregido en la ronda 5.** Ese ajuste fijaba los años El Niño en 1983 y 1998. Con la clasificación ICEN oficial de Territorio (`tools/icen_campanias.py`), 1971-2000 tiene 4 campañas fuertes o extraordinarias (1972, 1973, 1983 y 1998), 2 moderadas y 2 débiles; 1981-2000 tiene 2, 2 y 2. Reponderada a esas frecuencias, la razón costera de PISCOp queda entre 1,06 y 1,48 (MAM 0,94-1,38). La cota baja trata 1972 y 1973 como moderados y la alta como 1983/1998, porque 1981-2000 no tiene ningún año solo "fuerte". CHIRPS queda en 0,60-0,66 (MAM 0,16-0,19). El periodo explica una parte del +29 % de PISCOp, no todo. El sesgo de CHIRPS sigue siendo real.
3. PISCOp no es bueno en todo. En SON la razón costera es 0,55 (rango 0,16-1,40), y en Chusis, en pleno desierto, da 886,7 mm en marzo de 2017. Esa cifra no la he podido contrastar.

Recomiendo PISCOp para la lluvia de las zonas costeras, con estas notas, y no CHIRPS.

**R4-8 (CHIRPS en la costa es una climatología de fondo): confirmada.** En agosto de 1981-2019, CHIRPS da en Miraflores una media de 1,24 mm (desviación típica 0,10, rango 1,1-1,6), en Chusis 1,30 (0,06) y en San Miguel 1,28 (0,09). Mallares da 0,75 (0,06), fuera de su rango 1,1-1,6. En Chulucanas y Morropón sí varía (desviación típica de 1,1 mm). PISCOp da 0,02-0,25 mm en el mismo mes.

**R4-9 (la r costera no mide habilidad): aceptada.** Ya no reporto la r de climatologías. Dejo la razón por grupo, zona y temporada. Por zona, la razón mediana anual de PISCOp / CHIRPS es:

| Zona | n | PISCOp | CHIRPS | MAM PISCOp | MAM CHIRPS |
|---|---|---|---|---|---|
| alto_piura | 3 | 1,04 | 0,67 | 1,03 | 0,52 |
| bajo_piura | 3 | 1,44 | 0,32 | 1,22 | 0,03 |
| chira | 4 | 1,32 | 0,74 | 1,19 | 0,38 |
| medio_piura | 1 | 0,84 | 0,35 | 0,66 | 0,03 |
| sierra_piura | 9 | 0,94 | 0,71 | 0,94 | 0,62 |

La r mensual de CHIRPS frente a PISCOp es de 0,27-0,55 en los cuatro puntos costeros bajos y de 0,84-0,86 en Chulucanas y Morropón. Su total de MAM es de 0,04-0,07 del de PISCOp en la costa baja y de 0,64-0,65 en Chulucanas y Morropón.

**R4-10 (periodo y años FEN): aceptada, y es la que más pesa.** En la costa seca, la media 1981-2000 es de 3 a 5 veces la mediana. En Miraflores, PISCOp da una media anual de 149,6 mm, una mediana de 39,3 y una media sin El Niño de 29,8: las campañas El Niño suben la media un 402 %. Para el motor la lluvia va por zona como mediana sin El Niño, con escenarios El Niño aparte (`lluvia_zona_pisco.csv`, ronda 5). Corrección de la ronda 5: los años El Niño ya no se fijan a mano. Se toman de la clasificación ICEN oficial por campaña de Territorio; entre 1981 y 2000 son 1983 y 1998 (extraordinarios), 1987 y 1992 (moderados) y 1993 y 1995 (débiles).

**R4-11 (sierra con n=9): de acuerdo en que es poco.** Aun así, las 9 estaciones dan la misma lectura: PISCOp anual 0,94 (rango 0,73-1,12) y CHIRPS 0,71 (rango 0,40-2,12). En JJA hay razones de 5 y 15 sobre normales de pocos mm, que no significan nada. No saco conclusiones de la sierra por temporada seca.

## Pipeline

Se añade `tools/cew_ana_puntos.py` después de `insumos_curados_r4.py` y antes de `insumo_pendiente.py`. `pisco_vs_chirps.py` y `temperatura_power.py` van aparte, con `../suelos/.venv/bin/python`, porque necesitan rasterio.

# Ronda 5 (24-oct-2026)

En `modelo/para_piura_datos.md` no hay pedidos nuevos después de la Ronda 4. Esto es lo que cambió para ustedes.

## Lo que pedían en "Lo que pido" (R4)

- **Un solo juego de CEw por zona (R4-1).** Territorio aceptó corregir su `cew_por_zona.csv` con mis 29 puntos. Los 4 ambiguos se resolvieron con un balance iónico hecho sobre el mismo cuadro ANA (`tools/balance_ionico_ana.py`, `anexos/balance_ionico_ana.csv`, `aviso_territorio_cew.md`). QSFran1 (5 dS/m), RPiur4 (9,03) y RPiur5 (9,92) cierran leídos como mS/cm, con la suma de cationes/10 y STD/640, y entran como `estimado`/`balance_ionico`. QCarn1 no cierra con ninguna unidad (los iones dan 1,9 a 3,2 dS/m contra 10,4) y sigue `desconocido`. Los controles RPiur13 y RPiur6 validan el método. Dividir por 1000 da 0,005 a 0,010 dS/m, imposible. Los 4 puntos de nov-2015 (hdl 20.500.12543/2890) siguen sin descargarse: el repositorio ANA, el handle, Wayback y Tavily fallaron.
- **PISCOp mes a mes con y sin años El Niño (R4-7/R4-10).** Hecho, con la clasificación ICEN oficial de Territorio (`tools/icen_campanias.py`) en lugar de los años fijos 1983 y 1998. Entregables para el motor:
  - `lluvia_zona_pisco.csv` (294 filas): lluvia mensual y por temporada en las 7 cajas de zona. Para el año normal, usen la mediana `sin_el_nino`. Los escenarios `el_nino_moderado` y `el_nino_fuerte_extraordinario` van aparte. El ICEN de agosto de 2026 es 3,98 (serie oficial del IGP), así que el escenario fuerte no es teórico para la campaña 2026-27.
  - `temperatura_pisco_zona.csv` (168 filas, PISCOt): reemplaza a la de POWER. La diferencia mediana |POWER − PISCOt| es 1,9 °C, y en 58 de 168 filas pasa de 3 °C.
  - CHIRPS no sirve para la lluvia de Chira, Medio ni Bajo Piura (R4-8 confirmada).

## Pipeline (ronda 5)

Orden actual, desde `restricciones/`: extraer_drap → extraer_pdfs → insumos_curados (r1b, r2, r3, r4) → **balance_ionico_ana** → cew_ana_puntos → insumo_pendiente → limpiar → test_limpiar → cobertura → cobertura_md → **rendimiento_desconocido**. Después, con `../suelos/.venv/bin/python`: test_temperatura_power, temperatura_pisco, test_temperatura_pisco, pisco_vs_chirps, **lluvia_zona_pisco**, **test_lluvia_zona_pisco**. Las salidas que no siguen el CONTRATO van a `restricciones/anexos/`, porque `limpiar.py` lee todo `insumos/`: ahí están `balance_ionico_ana.csv` y `rendimiento_desconocido_explicado.csv`.

## R4-4. Las 75 filas de rendimiento sin cifra

No son huecos de búsqueda. Son cifras publicadas (DRA distrital y compendios INEI) que descartaron mis reglas de atípicos A1 a A4. Las dejo como `desconocido` y las explico fila por fila en `anexos/rendimiento_desconocido_explicado.csv`. Cada fila trae la cifra publicada, la regla, cuántas veces supera la mediana de referencia y un contraste con la evidencia propia del mismo cultivo:
- **18 son error probable.** Superan 5 veces la referencia: uva 900,1, melón 425, caupí 17,79 y 11 t/ha.
- **17 son dudosas.**
- **40 podrían ser reales y conviene revisarlas.** Son series coherentes de varios años, como plátano en Yamango (12 a 16 t/ha durante 8 años) y yuca y camote en Huarmaca y Paimas, o cifras que caben en 1,5 veces el máximo observado.

No encontré segunda fuente pública por distrito y año. Lo que propongo para la ronda 6 es una regla de serie para A4 (no descartar si el mismo distrito repite el orden de magnitud en 3 años o más), y que la decidan ustedes.


## Ronda 6

### R6-1. Regla de serie para atípicos (A4): propuesta, sin aplicar al estado
En `modelo/` (para_piura_datos.md, resultados.md, esquema_modelo.md) no encontré ningún criterio suyo para atípicos de rendimiento. Les propongo esta regla:

> **A4.** Una cifra de rendimiento descartada por atípica (A1-A3) no se descarta si el mismo distrito y cultivo repite el mismo orden de magnitud (dentro de un factor √10 ≈ 3,16) en 3 años distintos o más, contando cifras observadas o descartadas.

Lo único que hice fue agregar una marca en `anexos/rendimiento_desconocido_explicado.csv`. **El estado no cambia** hasta que ustedes la acepten, y las 75 filas siguen `desconocido`. Columnas nuevas:
- `posible_real_por_serie`: si/no/no_aplica.
- `serie_anios_mismo_orden`, `serie_detalle`: los años y cifras de la serie.
- `variante_estricta_factor_1_5`: la misma regla, pero dentro de un factor 1,5.

Resultado sobre las 75 filas:
- **Regla √10.** `si` 30, `no` 11, `no_aplica` 34 (filas de A1-A3 sin serie que contrastar). Dentro de los 30 `si` hay 2 que yo había marcado dudosos (limón en Miguel Checa, 53,5 t/ha; limón en Salitral, 45,4) y 2 error_probable (mango en Catacaos, 48,5; uva en Cura Mori, 73,31). La regla √10 es floja: deja pasar series que repiten un error de digitación.
- **Variante estricta (factor 1,5).** Rescata 19, todas ya posible_real_revisar: ají piquillo (Castilla y Piura 2017), camote en Huarmaca (2019, 2023, 2024), caña etanol (3), maíz en Yamango 2019, plátano en Yamango 2016-2023 (8), plátano en Paimas 2023 y uva en Las Lomas 2016 (64,47 t/ha, que sigue siendo sospechosa).
- **Mi recomendación.** Acepten la variante 1,5 y no la √10, y revisen a mano la uva de Las Lomas. Si aceptan, en la ronda siguiente esas 19 pasan a `estimado` con la serie en notas. Si no, todo queda como está.

### R6-2. CEw reconciliada con Agronomía
Las cifras finales y su justificación están en `aviso_territorio_cew.md`:
- QCarn1: 3,23 [1,94-3,23]. El 10,4 no tiene respaldo.
- RPiur4: 7,86 [5,56-9,03].
- QSFran1 5 y RPiur5 9,92, sin cambio.

Todas son estimado/balance_ionico. Para ustedes, el techo del río en San Lorenzo baja de 9,03 a 7,86 como valor central. Su pedido de no usar los máximos 9,92 y 9,03 sigue teniendo sentido: hoy 9,92 sigue siendo un estimado con error de balance −11,7 %.

### R6-3. Dispersión frente a incertidumbre (H06)
`anexos/cew_resumen_zona.csv` trae, por zona y tipo de fuente (río, quebrada, canal, pozo, reservorio_canal, sin mezclarlos), mediana, P10-P90 (n≥5) y mín-máx. Úsenlo como **dispersión entre puntos**, no como incertidumbre de una parcela. Para la feature CEw les sugiero la mediana del río por zona: Alto 0,51, Chira 0,87, San Lorenzo 0,45, sierra 0,28, Medio Piura 5,98 (n=3, inestable). Las quebradas van aparte. Bajo Piura no tiene cifra.

### R6-4. Validación de PISCOp
Ver `anexos/validacion_pisco_2017.md`. En marzo de 2017, PISCOp acierta el mes extremo con ±15 % en Piura ciudad y Chulucanas, pero en febrero se queda en la mitad. El 886,7 mm de Chusis no se pudo contrastar: no hay cifra pública por estación, así que queda desconocido; el orden de magnitud es plausible. En sep-nov, en la costa todo es casi cero (1-2 mm de diferencia). En la sierra, PISCOp da un 15-35 % menos que la normal: léanlo como cota baja.

### Pipeline (ronda 6)
Se agrega `tools/cew_resumen_zona.py` después de `limpiar.py`. `rendimiento_desconocido.py` ahora escribe las columnas A4.

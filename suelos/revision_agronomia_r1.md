# Revisión cruzada de agronomía, ronda 1 (rol Territorio)

Fecha: 2026-10-24. Archivos revisados (sin modificar): `cultivos/fichas_anuales.csv`, `perennes.csv`, `reglas_rotacion.csv`, `recuperacion_suelo.csv`, `decisions.tsv`. El detalle fila por fila está en `revision_agronomia_r1.csv` (34 hallazgos: 8 altos, 18 medios y 8 bajos). Créditos Tavily gastados: 0.

## Conclusión

Las transcripciones de las tablas están bien. Comprobé que FAO-29 T4 y T5 coinciden valor por valor. Las fichas INIA que no se habían descargado y pude verificar dicen lo que el archivo afirma. El problema está en otra parte: el conjunto trata el Bajo Piura como un valle bien drenado con riego normal, y no lo es. Allí hay napa somera y salina, una parte importante del área tiene ECe de suelo entre 4 y 12 dS/m (FAO/UNALM 1990) y el FEN se repite. ENFEN además declara un Niño costero extraordinario para 2026-27. Los criterios de drenaje, anegamiento y rotación se tomaron de zonas templadas o húmedas y no cubren ese caso.

## (a) Datos de extracto (confianza ≤0.45) comparados con la fuente primaria

- **AN0423, INIA 510 Mallares.** El PDF INIA, recuperado de Wayback, dice "madura en 148 días". Se probó en Sullana con 15.5 t/ha experimentales y más de 12.9 t/ha comerciales. Correcto; la confianza puede subir a 0.7. El PDF no trae datos de salinidad.
- **AN0424, INIA 502 Pitipo.** El PDF confirma 150-155 d, un potencial de 10-13 t/ha y siembra de octubre a enero. Solo se evaluó en Lambayeque, La Libertad y Arequipa, no en Piura. La URL del repositorio no responde.
- **AN0420/0421, caupí INIA 432.** La reproducción del tríptico INIA (Semillas Piuranas) da 80-100 d y un rendimiento de 2000-2500 kg/ha. Consistente. El PDF primario dio error 504. **AN0422** pone "resistente" a sales, pero la fuente solo dice "mejor comportamiento en suelos en proceso de salinización" y no da cifra.
- **Páprika, AN0410-0419 y AN0446-0449.** El manual INIA/INCAGRO (Barranca) cuenta la cosecha desde 120 d *después del trasplante*, con 45-60 d de cosecha. El folleto INIA da de 150 a 210 d según el método de siembra. La nota "acumulados desde siembra" contradice la fuente, y el total de 175 d se queda corto: el ciclo real está entre 165 y 210 d. Las dos fuentes son de la costa de Lima.
- **PE0083/0084, palta.** No pude abrir el PDF de MIDAGRI, ni en la web ni en Wayback. Siguen sin verificar.

## (b) Análogos FAO usados como si fueran Piura

- **Umbrales de ECe (FAO-29 T4, en fichas y en RR065-RR080).** Los valores son correctos, pero FAO-29 supone una fracción de lavado del 15-20 % y que la napa no aporta sales. En el Bajo Piura no se puede estimar la ECe como 1.5·ECw. Hace falta la ECe medida. Además, la tolerancia baja en periodos cálidos y secos.
- **Insumo de suelos (HWSD).** HWSD da al Bajo Piura una ECe de 1.51 dS/m y lo clasifica como bien drenado. Eso contradice el estudio FAO/UNALM 1990, la SIAR 584 (Aquisalids) y el ANA, que mide CE del agua subterránea de hasta 16.83 dS/m. Con HWSD el motor declararía aptos el maíz, el frijol y el pimiento donde no lo son.
- **AN0463/0464, napa crítica de 0.8-0.9 m.** Es un criterio de aireación (FAO-62). En zona árida con napa salina, FAO-29 pide mantener la napa a 2 m o más. Hay que tratarlas como dos variables distintas.
- **AN0460/0461 (evacuar en 24 h) y AN0454-0459 (Tian 2021, máximo 15 d).** No representan el FEN. En 2017 el agua quedó estancada durante días en el Bajo Piura, con 8 733 ha perdidas y 15 342 afectadas. No encontré una cifra de duración en días.
- **AN0018, arroz.** FAO-29 T5 lo clasifica como MS, no S.
- **Algodón, umbral de 7.7 dS/m.** Es el valor de *G. hirsutum*, pero en Piura se siembra Pima (*G. barbadense*). La literatura no da un umbral propio para Pima.
- **Banano, PE0011/0027, clase MS.** El banano no aparece en FAO-29 T5.
- **AN0431/0432, caupí.** El pH de 5.5-6.6 viene de un manual de Loreto y no aplica a suelos alcalinos de costa.
- **RS007/RS008 y RS001-RS006.** Son análogos templados o chinos. No hay ninguna fila con datos de Piura, aunque existen fuentes peruanas que podrían usarse: FAO/UNALM 1990 Bajo Piura, UNALM 1968, la tesis UNP sobre Catacaos y la de pozos en Punta Arena.

## (c) Reglas de rotación y evidencia peruana

- **Con soporte peruano (normativa SENASA, RM 0251-94-AG y sus modificatorias):**
  - RR038, algodón→algodón. La norma obliga a dejar el campo limpio del 16 oct al 31 dic en el Medio y Bajo Piura y prohíbe las socas (Art. 13). En campos con infestación fuerte de gorgojo de la chupadera, se salta una campaña de algodón (Art. 11). Con eso RR038 puede dejar de estar en estado "desconocido".
  - La misma norma (Art. 12) **prohíbe incorporar rastrojos de algodón**. Contradice RS001-RS006 si se aplican al algodón (hallazgo alto).
  - La ventana de AN0452 (15 mar-30 abr) corresponde a híbridos en el Medio y Bajo Piura. Para Pima, la ventana de esa misma zona es del 1 ene al 28 feb, y Alto Piura, Chira y San Lorenzo tienen fechas propias.
- **Peruana pero débil:** RR001-RR025, leguminosa→arroz. En Chancay-Lambayeque se siembran leguminosas con la humedad que deja el arroz, y una nota de prensa les atribuye un aporte de 40-50 kg N/ha. No encontré ninguna cifra de rendimiento del arroz siguiente.
- **Corrección a RR001-RR025.** Zhao 2022 dice que el efecto cae cuando se fertiliza con mucho N. El arroz de la costa norte recibe unos 270 kg N/ha (INIA 502: 11 bolsas de urea + 2 de DAP), así que corresponde el extremo bajo, alrededor del 7 %. RR026-RR037 (Franke, sin N, África subsahariana) no aplican.
- **Sin soporte peruano:** RR058-RR061 (Zhou, Asia) y RR062-RR064 (alelopatía del sorgo). Las reglas SENASA de hospederos (RR039-RR053) tienen la dirección respaldada, pero no la magnitud.
- **Reglas que faltan:**
  - El efecto del arroz sobre la napa y las sales. Es condicional: con mal drenaje saliniza y con drenaje funcional lava.
  - Escenario FEN.
  - Barbecho de verano con napa alta (FAO-29).
  - Una regla de sales para la páprika, cuyo umbral de 1.5 dS/m es de los más bajos del conjunto.

## Método y límites

- Los dominios .gob.pe y archive.org por https fallan por TLS desde el box. Recuperé los PDF de INIA con WebFetch sobre Wayback `id_`.
- No pude abrir los PDF de MIDAGRI (palta), del caupí INIA y del estudio FAO 1990 completo. De ese estudio solo leí un extracto, y sin las hectáreas por clase de salinidad.
- La fuente de Scribd que atribuye el 75 % de área salinizada al exceso de arroz es secundaria. La cito solo como indicio.

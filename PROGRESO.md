# PROGRESO

## Agronomía (Agente 1)

### Ronda 1 — 2026-10-24
- `cultivos/fichas_anuales.csv` (453 filas): duración por etapa (FAO-56 T11 + INIA/MIDAGRI/DRA Piura), Kc, raíz/p, ECe Maas-Hoffman (FAO-29 T4, FAO-56 T23), absorción/exportación NPK (FPNB 16), anegamiento (Tian 2021, FAO-62), plagas clave (piura-data).
- `cultivos/perennes.csv` (167 filas): etapas del ciclo anual; años a producción y vida útil siguen `desconocido`.
- `cultivos/reglas_rotacion.csv` (80 reglas): leguminosa→cereal (Zhao 2022 +20%, rango 7–32%; Franke 2018 +0.49 t/ha), plagas compartidas (Pectinophora en algodón→algodón, Spodoptera, Elasmopalpus, Diatraea, Pomacea, R4T), sales (Maas-Hoffman, 16 cultivos), fangueo y alelopatía del sorgo (magnitud desconocida).
- `cultivos/recuperacion_suelo.csv` (17 filas): paja (SOC +12.8%, saturación ~12 años), cobertura (+0.32 Mg C/ha/año), lavado (70–80% / 80–90% de sales por lámina igual a profundidad), yeso (hasta 40 t/ha en 1 año), sódico sin enmienda (1–5+ años), barbecho (desconocido).
- Validación: `python3 cultivos/validar.py`. Los 4 CSV dan OK (lectura con pandas, columnas del contrato, cada número con fuente y URL).
- Tavily usado por Agronomía: 10 créditos.
- Vacíos: duraciones locales de zarandaja, caupí y amiláceo; años a producción y vida útil de los perennes; magnitud de las reglas de plagas; efecto del fangueo en el cultivo siguiente.

### Ronda 2 — 2026-10-24
- perennes.csv 168 filas: ciclo de vida con cifras textuales. Mango 3–4 años a 1.ª producción y vive 30 (MIDAGRI); palta Hass 2 y Fuerte 3, >25 años (MIDAGRI, extracto); cacao 20 años de vida útil (MIDAGRI); papaya 3–4 años, maracuyá 1–3 y 5–6, limón sutil de semilla 3–6 (Morton 1987, análogo). 15 filas siguen desconocido (banano, uva, café, piña, naranja, más los huecos de limón, papaya y cacao).
- fichas_anuales.csv 477 filas (+24): páprika MIDAGRI 175 d (25/60/45/45) y raíz por etapa; caupí INIA 432 con 80–100 d y 2000–2500 kg/ha; arroz INIA 510 Mallares 148 d e INIA 502 Pitipo 150–155 d; periodo vegetativo INEI ENA 2024 (meses) para 6 cultivos; zarandaja 3–6 meses (fuente débil, 0.35); caupí 18–34 °C y pH 5.5–6.6 (análogo, Loreto).
- reglas_rotacion.csv 80 y recuperacion_suelo.csv 17: sin cambios en esta ronda.
- validar.py: los 4 CSV pasan y no hay ids duplicados.
- Tavily Agronomía: 20 créditos acumulados (10 en esta ronda). INIA no descarga ni con curl ni con tavily_extract, así que se usan extractos de búsqueda con confianza de 0.45 o menos.

### Ronda 3 — 2026-10-24 (repriorizada por el coordinador)
- Script nuevo e idempotente `cultivos/build_ronda3.py` (ids R3*). Se corre después de build_fichas.py y build_reglas.py. Fuentes nuevas en fuentes.py.
- fichas_anuales.csv 646 filas (+169) y perennes.csv 265 (+97). motor_integracion.csv nuevo (2 filas). Propuestas en esquema del motor en `cultivos/para_motor/` (parámetros 115, salinidad 1+3, nutrientes 3, Kc 2).
- 1) ECe:
  - arveja 3.4 dS/m / 10.6 %/(dS/m), MS (FAO-61, Cerda 1982). Choca con FAO-56 (1.5, S).
  - Solo clase: yuca MS, frijol de palo S, mango S, banano S (choca con el MS de FAO-56), papaya MS (choca con el MT de FAO-29).
  - Valores por defecto de clase CPIC con confianza 0.3: frijol de palo y mango 1.3/17.5; papaya 6.0/5.6.
  - Café: CE de 1.1 dS/m para 90 % de crecimiento en almácigo y CEw ≥1.2 con daño en plántula.
  - Cacao: solo un criterio de aptitud de <1 dS/m.
  - Siguen desconocido: umbral de yuca, banano, cacao y café; pendiente de yuca, banano, cacao y café.
- 2) EcoCrop para 25 especies (18 anuales y 7 perennes): T óptima y absoluta, pH óptimo y absoluto, clase de profundidad óptima y mínima.
- 3) Kc de mango y papaya por cobertura (Paredes et al. 2024, T6). Papaya tarda ~9 meses a la 1.ª cosecha. Siguen desconocido: Kc y etapas de frijol de palo, días por etapa de mango y papaya. Calendario de Piura: caupí siembra en setiembre en el Medio Piura (extracto UNP, 0.3); los demás cultivos, salvo arroz y algodón, siguen desconocido porque INIA, DRA y gob.pe están inaccesibles.
- 4) Caupí (Embrapa, BRS Guariba):
  - exportación en grano: 33.0 N / 8.9 P2O5 / 19.2 K2O kg/t
  - absorción: 101.8 / 19.0 / 85.7
  - heno: 26.8 / 5.6 / 17.9 (PNB16)

  Zapallo: exportación 1.2 / 1.0 / 5.8 kg/t (NCSU, winter squash, análogo); absorción desconocido. Papa: notas rotuladas por tipo_coeficiente; decisión en decisions.tsv.
- 5) FBN:
  - %Ndfa por grupo (Herridge 2008): frijol 40, caupí/arveja/frijol de palo 63, soya/maní 68.
  - kg N/ha global: frijol 23, arveja 86, maní 88, soya 176, caupí ≈25 (derivado).
  - Manrique 1993 (costa de Lima, 15N): 20–80 kg N/ha, observado.
  - 30–40 kg N/t de MS aérea; abono verde de caupí 60 kg N/ha.
  - Frijol de palo en kg/ha y cualquier medición en Piura: desconocido.
- Motor: `--integrar` solo usa duracion_ciclo. En el dry run sobre /tmp, arroz pasa de 165 d (análogo FAO) a 148–155 d (regional INIA) y caupí queda en 80–100 d. Con las propuestas añadidas en una copia del motor pasan los 9 tests. No se escribió en datos_motor/.
- validar.py: los 5 CSV dan OK. Tavily de la ronda: 1 crédito; acumulado de Agronomía según creditos_tavily.tsv: 21.

### Ronda 4 — 2026-10-24 (revisión cruzada de Territorio sobre r1 y r3)
- Hecho: `cultivos/respuesta_revision_r1.csv` (34 hallazgos: 31 corregidos, 0 rechazados, 3 pendientes) y `respuesta_revision_r3.csv` (27 hallazgos: 25 corregidos, 0 rechazados, 2 pendientes). Builders nuevos: `build_ronda4.py` (corrige r1 y r3) y `build_respuestas.py`. Cadena: build_fichas → build_reglas → build_ronda3 → build_ronda4 → build_respuestas. Es idempotente.
- Los altos de r1, uno por uno:
  - H01: los umbrales de ECe valen solo si la ECe está medida, con napa de 2 m o más o con drenaje.
  - H02: pendiente (es un archivo de suelos/).
  - H03: napa crítica para aireación, más un mínimo de 2 m para controlar sales.
  - H04 y H05: confianza 0.4, y lo que pasa de 15 días queda desconocido.
  - H06: reglas para después del arroz.
  - H07: FEN 2017 y ENFEN 18-2026.
  - H08: la RM 0251-94-AG prohíbe incorporar el rastrojo de algodón.
- Los altos de r3:
  - Papaya: MS 3.0/7.7.
  - FBN: N total con raíz, por campaña.
  - Balance de caupí: +31 / -38, con crédito desconocido.
  - pH absoluto: pasa a advertencia.
  - DEP: pasa a profundidad favorable, con rampa hasta DEPR.
  - Respuesta a r1: creada.
- Cambios en para_motor:
  - parametros: de 115 a 138 filas. Las 23 filas de pH absoluto pasan a `pH_suelo_absoluto_ecocrop`, que es advertencia y no descarte. Se añaden 23 filas DEP `profundidad_suelo_favorable_minima`.
  - Defectos de salinidad: de 3 a 5 filas (papaya MS, yuca y banano), todas `analogo_externo`.
  - Nutrientes: se añade papa.
  - Kc: rotulado "no FAO-56 T12".
  - motor_integracion: R3M0001 pasa a INIA 510 (conf 0.6) y R3M0002 a SEMPIU (0.55).
  - Prueba en seco en /tmp/motor_dry: 9 tests pasan, y piquillo, papaya y cacao ya no se descartan por pH.
- `validar.py` ahora valida también el esquema de respuesta_*.csv. Todo da OK. Tavily: 24/700.
- Pendiente: hallazgos r1 M24 (evidencia peruana en recuperación) y L32 (palta), y r3 L22 (UNITRU) y M27 (ventanas fuera de algodón). Al dueño del motor le recomiendo implementar la rampa óptimo→absoluto de pH y DEPR→DEP de profundidad.

### Ronda 5 — 2026-10-24 (profundización)
- P1. Ventanas locales de siembra y cosecha:
  - Los PDF de MIDAGRI, SIEA y la DRA no descargaron. Las saqué de `raw/drap_dataset.csv` (DRAP 2016-2024, siembras y cosechas mensuales por distrito).
  - `calendario_drap_piura.csv` (2718 filas) da ventanas, meses pico y desfase siembra-cosecha por cultivo y zona: Chira, Medio Piura, Bajo Piura, Alto Piura, San Lorenzo y Sierra.
  - Nuevo `para_motor/calendario_siembra_cosecha_piura.csv` (120 filas).
  - Son meses observados (≥10 % de ha o t). No son fechas recomendadas.
- P2. Perennes, años a primera producción y vida útil:
  - Uva: 12-13 meses en Piura (Redagrícola 2021), 20-25 t/ha en la 1.ª cosecha.
  - Banano (Chira): 9-11 meses (CoopSuiza, edad en parcelas demo) y vida de 10-15 años (Huamán 2005).
  - Cacao: 3 años y vida económica ≤40 (CAT Tocache, análogo de selva).
  - Café: 2-3 años, inferido del manual VRAEM (0.35).
  - Piña: 12-15 meses (UNALM, selva).
  - Naranja y limón injertado siguen desconocidos.
- P3. Frijol de palo y yuca:
  - Frijol de palo INIA-Sipán (análogo de Pucallpa): floración a 130 d, cosecha escalonada desde 6-7 meses, período de 15 meses, 2.5 t/ha de grano seco.
  - Yuca: alerta de ECe 0.7 dS/m al 50 % (Shannon y Grieve 1999, cita de 3.ª mano). El umbral CPIC no cambia.
  - Siguen desconocidos: Kc de frijol de palo y de zarandaja, etapas de zarandaja, FBN en kg/ha y umbral de ECe de banano y cacao.
- P4. Pendientes de revisión:
  - M24: corregido en parte con R5S001-007 (Pasache 2021: campo en Mochumí, CE 1:1, lámina de 18 000 m3/ha en 8 meses, yeso 8-22 t/ha, PSI final 10.57 frente a 22.44; Sechura, laboratorio, conf 0.3).
  - L32: corregido (GORE La Libertad 2025 + Olmos, conf 0.5).
  - M27: corregido con el calendario.
  - L22: sigue pendiente.
- P5. Rotación:
  - R5R001-003: Meloidogyne en capsicum, en melón de Chulucanas y en uva de Piura (tesis UNP).
  - R5R004: frijol bayo después de arroz, maíz o algodón (MIDAGRI), sin magnitud.
  - No hallé ningún ensayo peruano de rotación con testigo.
- Filas nuevas: perennes +4, fichas +7, recuperación +7, reglas +4, calendario 2718.
- Cadena idempotente (md5 igual en dos corridas). `validar.py` da OK en todo.
- Prueba en seco del motor: 7 pasan y 2 fallan.
  - Fallan igual en una copia sin tocar del motor (cambio del motor de 06:30: la integración exige url_o_doi y frijol grano no se descarta a ECe 9-10).
  - No es regresión de cultivos/. Aviso al dueño del motor.
- motor_integracion.csv: sin cambios.
- Tavily: 48/700 en total para Agronomía (~25 en R5).

### Ronda 6 — 2026-10-24 (zona única + revisión r5)
- Zona: la única fuente es suelos/datos/distrito_zona.csv (cruce por UBIGEO). Paimas y Suyo pasan a san_lorenzo, Veintiséis de Octubre a medio_piura y los 6 distritos de Talara a piura_region. Rehíce calendario_drap_piura.csv (2876 filas) y para_motor/calendario_siembra_cosecha_piura.csv (126). Así queda la sierra: el arroz es marginal (2.3 %) y lleva una nota de "valles bajos interandinos".
- La columna `zona` va después de `etapa` en todos los CSV de cultivos/ y para_motor/, y `zonas_aplicables` va al final para análogos multizona: Olmos → chira;san_lorenzo;medio_piura y Mochumí → bajo_piura;chira. Cuando el dato es FAO genérico o extranjero, la zona queda vacía. validar.py exige la columna y comprueba los códigos y los 6 archivos de para_motor.
- Revisión r5: 23 hallazgos (3 altos, 10 medios y 10 bajos según el archivo del revisor). Corregí 22 y rechacé 1 (H12, porque es código de Territorio). Todo queda en cultivos/respuesta_revision_r5.csv. Corregí el banano PE0015 y el PE0031 a 1.0 año (0.85-1.2) con Swisscontact 2012, zona chira. También corregí r1 H03, M24 y L32 y r3 H06.
- C: cerré r1 H02 con FAO/UNALM 1990 y ANA ERH 2015 (R6S001-006); r3 L22 quedó cerrado solo en parte (cualitativo). Agregué el ECe de mango (R6P001-003), el Kc de mango Kent (R6P004-007), el Kc de banano de Ecuador (R6P008) y el daño por ECe en frijol de palo (R6A001-002). Siguen desconocidos el ECe de papaya y de yuca y el Kc y las etapas de frijol de palo y de zarandaja.
- Motor (prueba en seco en cultivos/_scratch/motor): con mis datos pasan 26 y falla 1, porque calendario_obs.ZONA_PREFIJO no reconoce los códigos. Con un parche de 2 líneas (_scratch/parche_calendario_obs_codigos.diff) pasan los 27. No toqué el motor.
- Cadena idempotente: los 15 CSV dan el mismo md5 en dos corridas, y validar.py da OK. Tavily: 15 créditos en esta ronda, 63/700 en total.

### Ronda 7 — 2026-10-24 (revisión cruzada de suelos + arveja + respuesta r6)
- Revisión cruzada de suelos/ (método interrogate adaptado, manual por lentes, sobre una copia congelada de las 07:17 porque Territorio editaba en vivo). 14 hallazgos: 4 altos, 6 medios, 4 bajos → suelos/revision_agronomia_sobre_territorio_r1.csv y .md. NO edité nada de Territorio. Altos: QCarn1 10.4→3.0–3.3 dS/m y RPiur4 9.03→5.1–5.8 dS/m por balance iónico (QSFran1 ~4.0–4.6 y RPiur5 ~11–12 son coherentes); la justificación de unidades debe ser el balance, no el Gráfico 6.7; napa Bajo Piura tope 2.0 m contradice SEV 2015 (p75 6.0 m, 51% >2 m).
- Arveja (salinidad): umbral principal ECe 3.4 dS/m, pendiente MS 10.6%/dS/m (FAO-61 Tanji y Kielen 2002; Cerda 1982 SP-290 2.5 / Durana 4.5; Grieve 2012 ASCE Manual 71). FAO-56 (1.5/14) queda como alternativa rotulada: FAO-48 Tabla 13 (p.30) marca Pea con * = estimación. RR074: valor 10.6, condición >3.4 (2.5 si SP-290/prudente, 4.5 si Durana). Filas R7A001=2.5, R7A002=4.5.
- Arveja (térmica): tras el arroz en bajo_piura la viabilidad es MARGINAL (confianza 0.3). Siembra en jul → floración ago–sep con Tmáx media SENAMHI 27.9–28.8 °C, por encima del umbral de estrés reproductivo 27–32 °C (Osorio 2023); SENASA BPA: óptimo 15–18 °C, calidad afectada >30 °C. Época local desconocida (la DRAP no registra arveja en el llano). Filas R7A003–R7A011; 51 filas MARGINAL con confianza >0.4 bajadas a 0.4.
- Respuesta a la r6 de Territorio: cultivos/respuesta_revision_r6.csv, 18 hallazgos (0 altos, 9 medios, 9 bajos), todos atendidos. Durán Zuazo corregido a 2004, Eur. J. Agron. 21(3):323-334 (doi 10.1016/j.eja.2003.10.004) en todas las filas. validar.py ahora exige zonas_aplicables cuando la zona está vacía y el dato no es genérico, y rechaza piura_region/medio_bajo_piura en zonas_aplicables; rellené 48 filas (33 en fichas, 15 en perennes) con las zonas de la DRAP por cultivo (piña con COSTA provisional, con nota).
- Cadena idempotente (build_fichas→…→build_ronda7): mismo md5 en dos corridas; validar.py da OK en los 15 CSV. Tavily: 7 créditos en esta ronda, 70/700 en total para Agronomía.

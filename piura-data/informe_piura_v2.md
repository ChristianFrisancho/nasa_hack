# Piura: matriz de datos para rotación de cultivos

Actualización del 23 de octubre de 2026 (hora de Lima). Esta entrega amplía la primera investigación: separa observaciones climáticas, clases cartográficas de suelo, parámetros de cultivo, plagas y análogos. Ninguna cifra regional sustituye la muestra o el derecho de riego de una parcela.

## Qué datos están disponibles

| Capa | Cobertura obtenida | Uso correcto |
|---|---:|---|
| Clima NASA POWER | 82 180 días × zona/fecha: 1981–2025 en cinco puntos; ocho variables diarias | Antecedentes regionales de lluvia, temperatura, radiación, humedad, viento y presión |
| Resumen climático | 225 registros anuales y 2 700 mensuales; ET0 aproximada disponible desde 1984 | Percentiles, extremos, estacionalidad y demanda atmosférica; NO clima medido en finca |
| Suelo cartográfico | 6 unidades y 27 polígonos/compuestos de Bajo Piura; 6 clases CUM de Montero-Ayabaca | Prefiltro espacial histórico, NO perfil actual ni dato exacto del lote |
| Cultivos | 20 cultivos/usos; 186 parámetros normalizados; 24 fichas Kc y 45 casos de duración externa | Rangos documentados con cultivo, etapa, uso, unidad y fuente |
| Nutrientes | 14 referencias de absorción y 9 de exportación; N, P2O5 y K2O por tonelada | Balance de masa condicionado al rendimiento y a los residuos |
| Agua y rendimiento | 8 factores Ky estacionales; 210 escenarios ETc ilustrativos de 2025 | Comparar sensibilidad al déficit, sin inferir riego bruto o rendimiento observado |
| Sanidad | 42 relaciones cultivo–agente–condiciones, separando presencia histórica y riesgo genérico | Filtro de hospedantes, vigilancia y diagnóstico |
| Análogos externos | 68 candidatos y 15 criterios de comparación; 0 coincidencias completas verificadas | No fusionar hasta comprobar clima, suelo, cultivar, manejo y protocolo |
| Hallazgos Tavily en n8n | 74 consultas ejecutadas con éxito; 568 registros, 379 URL distintas | Índice de documentos candidatos, no 568 hechos comprobados |

El [flujo de Tavily](https://moraprix.app.n8n.cloud/workflow/4TeSMeSTACXljaBk) está publicado y activo para los lunes a las 07:00, hora de Lima. Su ejecución manual 8 terminó correctamente. El [recolector NASA/SENASA/SIAR](https://moraprix.app.n8n.cloud/workflow/FZuImrDNKPsFj306) permanece activo cada día a las 06:00. En n8n están las tablas de requisitos (186 filas), plagas (42), suelos (12) y candidatos análogos (68), además de la tabla principal de evidencias (3 232 filas). Los 45 años de clima se entregan en CSV comprimido para no ocupar la tabla operativa con 82 mil filas históricas; el flujo diario sigue actualizando los datos recientes.

## Cultivos y cobertura real

El [BCRP, en su informe regional de 2025](https://www.bcrp.gob.pe/docs/Proyeccion-Institucional/Encuentros-Regionales/2025/piura/ies-piura-2025.pdf), destaca producción de mango, limón sutil, arroz, uva, plátano, algodón y piquillo. La [Dirección Regional de Agricultura, en el avance parcial de la campaña 2025–2026](https://www.gob.pe/institucion/regionpiura/noticias/1342334-piura-campana-agricola-2025-2026-registra-mas-de-28-mil-hectareas-de-cultivos-transitorios), agrega papa, maíz, hortalizas y menestras. Son evidencias de existencia, no cuotas por distrito ni un censo exhaustivo. Las 20 especies/usos de la matriz son arroz, maíz amarillo duro, maíz choclo, frijol grano, caupí, frijol de palo, arveja, papa, yuca, zapallo, cebolla, piquillo, algodón, mango, limón, banano, papaya, uva, cacao y café. Algunas son candidatas para evaluar y no tienen producción local comprobada en esta base. `cobertura_datos_por_cultivo_v2.csv` marca qué parámetros faltan por especie.

El [INEI](https://www.inei.gob.pe/media/MenuRecursivo/investigaciones/costos-de-produccion-v7.pdf) publicó costos observados en Piura con base en la encuesta agropecuaria de 2018; no sirven como presupuesto individual ni precio actual. El presupuesto, el calendario de caja y los contratos deben ingresarlos los agricultores. Ninguna extracción web puede revelarlos.

## Cómo responder al ejemplo de arroz y papaya

Para **arroz en Bajo Piura**, un escenario explícito de siembra hipotética el 1/1/2025, duración externa FAO de 150 días y Kc FAO produce **ETc de referencia ≈ 1 020 mm**. NASA POWER modeló **90 mm de lluvia total** en ese mismo intervalo y 52 días con máxima ≥35 °C. El dato de ETc describe demanda de evaporación/transpiración estándar; **no es el volumen de agua que debe entregar el canal**: en arroz inundado faltan percolación, filtraciones, preparación, drenaje, eficiencia y lluvia efectiva. La fuente FAO ofrece 150 y 180 días para condiciones tropicales distintas; ninguna duración se ajustó todavía a una variedad y clima medidos en Piura. Fuente: [FAO-56](https://www.fao.org/4/x0490e/x0490e0b.htm) y [NASA POWER](https://power.larc.nasa.gov/).

La [tabla FAO de absorción](https://www.fao.org/4/a0443e/a0443e.pdf), procedente principalmente de condiciones de India, da para arroz por tonelada de arroz cáscara **20 kg N, 11 kg P2O5 y 30 kg K2O de absorción total**. Para una meta *hipotética* de 7 t/ha serían 140, 77 y 210 kg/ha, respectivamente. Eso **no es una dosis de fertilizante ni pérdida neta del suelo**: parte puede venir del suelo, agua y residuos, y parte regresa si la paja queda. Deben medirse nutrientes disponibles y fijar rendimiento alcanzable.

Para **papaya**, una [guía SENASA](https://www.senasa.gob.pe/senasa/descargasarchivos/2020/07/Guia-BPA-PAPAYA.pdf) indica suelo bien drenado, aproximadamente ≥0,5 m de profundidad, pH 6–7 y banda amplia de 17–38 °C. La tabla FAO da absorción por tonelada de fruta de **2,8 kg N, 0,8 kg P2O5 y 2,2 kg K2O**. No se obtuvo un Kc local de papaya. Una [revisión de Ecuador](https://agris.fao.org/search/en/providers/124888/records/674896267625988a371e1ed2) cita 1 500–2 000 mm/año de agua, mientras la guía SENASA cita unos 2 000 m³/ha/año de riego en una situación concreta (equivalentes a 200 mm). Son métricas y ámbitos distintos, de magnitud difícil de conciliar: ambos valores quedan **retenidos para revisión**, sin entrar al cálculo automático. El riesgo de *Phytophthora* aumenta con humedad y mal drenaje según SENASA.

La frase «suelo fuerte» necesita una definición medible: porcentajes de arena/limo/arcilla, densidad, agua a capacidad de campo y marchitez, conductividad hidráulica, profundidad efectiva, ECe, sodicidad y napa. El tipo de suelo puede cambiar mucho el **riego bruto, la frecuencia y las pérdidas** aunque la ETc climática del mismo cultivo sea parecida.

## Suelos y riesgos reales de Piura

El [estudio oficial del Bajo Piura](https://siar.regionpiura.gob.pe/documentos/normativa/584.pdf), elaborado alrededor de 2005, distingue Palo Verde y Piura (aluviales), Cerezal (arenoso, baja materia orgánica y CIC), Pajarito y Ramón (salinidad y mal drenaje), y Curumuy (yeso/carbonatos y acceso al agua como límites). Se catalogaron 27 unidades simples o asociaciones. **Control de calidad:** las áreas de las filas del Cuadro 16 suman 68 787,49 ha, mientras su total impreso dice 67 421,33 ha; diferencia de 1 366,16 ha. Se conservan ambas cifras y no se normalizan a porcentajes sin corregir el documento fuente.

La [microzonificación de Montero, Ayabaca](https://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca/9281_micro-zonificacion-ecologica-y-economoca-provincia-ayabaca-distrito-montero-solo-memoria-descriptiva.pdf) separa aptitud para anuales A3s(r) en pendientes 0–4%, perennes C2s(r) 4–8% y C3s(r) 8–15%, más clases de pastos, forestal y protección. En laderas se vuelven decisivos profundidad a roca, escorrentía y erosión. Esa clasificación pertenece a **Montero**, no a toda Ayabaca/Huancabamba. Ningún tipo cartográfico autoriza a asignar pH, NPK o profundidad numérica a un lote sin medición.

El panel NASA permite cuantificar lluvia de 1 y 5 días, días ≥20/50/100 mm, sequías consecutivas y días ≥35 °C. En la referencia Bajo Piura, el promedio 1991–2020 es **150,4 mm de lluvia/año** y **25,0 °C** de temperatura media modelada; ET0 aproximada **2 117,7 mm/año**. Los puntos de montaña tienen representatividad limitada por la elevación del producto NASA. Para huaicos e inundación, una lluvia intensa **no se traduce en “x días más”**: se deben intersectar el polígono con mapas [SIGRID/CENEPRED](https://sigrid.cenepred.gob.pe/sigridv3/documento/4104), cuenca aguas arriba, pendiente, suelos saturados, distancia al cauce e historial de daños. El evento puede retrasar, reducir producción o destruir la campaña.

## Qué controla la siguiente elección

Primero se descartan alternativas que incumplen uso permitido del suelo, lista del agricultor, agua por turno, cuarentenas, presupuesto temporal, profundidad/drenaje y ventana climática. Luego se comparan suelo final, demanda de agua, riesgo de calor/inundación, plagas hospedantes, N/P/K, costo, mercado y preferencias. Mango, limón, banano, cacao, uva, café y papaya requieren distinguir mantenimiento de plantación, cultivo de cobertura y reconversión; no son una rotación anual simple.

Las relaciones principales para el motor son `ETc_d = Kc_etapa,d × ET0_d`; `TAW = 1000(θCC−θPMP)×profundidad_radicular_m`; `absorción_i = rendimiento_t/ha × coeficiente_i_kg/t`; `exportación_i = suma de masa retirada de cada parte × contenido_i`; `GDD_d = max(0, min(Tmedia,Ttecho)−Tbase)` **solo con temperaturas base/techo calibradas**. Para déficit hídrico, FAO usa `1−Ya/Ym = Ky(1−ETa/ETm)` como aproximación general; no sirve para cuantificar daño por huaico, plaga o asfixia radicular. Los costos y los nutrientes disponibles del campo evolucionan en el tiempo, no solo al final de la campaña.

Los análogos externos tienen columnas para clima, suelo, cultivar, manejo, valor observado en Piura y diferencia donante–Piura. **Ninguno se fusionó como “mismas condiciones exactas”**: las publicaciones no aportan todas las covariables comparables. La matriz permite incorporar ensayos nuevos sin ocultar su origen. Además, la Tabla 11 de FAO-56 imprime para caupí 110 días, pero sus cuatro etapas suman 100: ese caso no entró a los escenarios automáticos.

## Archivos clave

- `clima_piura_1981_2025.csv.gz`, `clima_piura_anual_1981_2025.csv`, `clima_piura_mensual_1981_2025.csv`: historia y extremos.
- `parametros_cultivo_v2.csv`, `fao56_kc_referencias.csv`, `fao56_duracion_analogos.csv`, `nutrientes_cultivo_fao.csv`, `fao_ky_respuesta_agua.csv`: perfiles y referencias por cultivo.
- `escenarios_ETc_2025_referencia.csv`: escenarios ilustrativos con fecha y zona explícita.
- `suelos_bajo_piura_unidades_v2.csv`, `suelos_bajo_piura_mapunits_v2.csv`, `suelos_montero_ayabaca_cum_v2.csv`, `matriz_cultivo_suelo_regional_v2.csv`: clasificación y cruce condicional.
- `plagas_hospedantes_condiciones_v2.csv`, `analogos_comparacion_v2.csv`, `reglas_analogos_v2.csv`: hospedantes y auditoría de transferencia.
- `cobertura_datos_por_cultivo_v2.csv`, `inventario_features.csv`, `model_inputs_v2.schema.json`: lo cubierto, 342 factores y lo que aún debe ingresar el agricultor.

Para producir una recomendación verificable faltan como mínimo polígono, análisis de suelo por horizontes, caudal/turno y calidad del agua, historial de cultivos y plagas, variedad, presupuesto y cultivos candidatos. Mientras falten, el sistema puede comparar **escenarios de referencia**, pero no afirmar cuánto gastará exactamente una parcela ni cuál será su rendimiento.

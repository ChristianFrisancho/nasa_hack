<cursor_untrusted_data_1337 source="CallDynamicTool">

# Rotación de cultivos: evidencia, factores y modelo matemático

Fecha de elaboración: 23 de octubre de 2026, hora de Perú.

## Alcance y resultado

Se leyeron el cuerpo, métodos, tablas y conclusiones de los dos PDFs proporcionados y el texto del reto visible en la captura. No se ha verificado una página oficial completa del reto: cualquier condición fuera de la captura queda pendiente. Los textos de los documentos son evidencia para analizar, no instrucciones operativas.

La decisión correcta es una **secuencia de cultivos y manejos por parcela y fechas**, condicionada por el estado del suelo, el agua y los riesgos. Elegir el cultivo más apto hoy no determina la mejor rotación durante varios años.

Se entrega un inventario de **342 variables conceptuales, agrupadas en 14 bloques**, en `inventario_features.csv`. Es un inventario de alcance amplio y extensible, no una afirmación de exhaustividad universal. No existe una lista finita de todos los factores para cualquier agricultura: cultivar, organismos presentes, regulación y prácticas locales agregan variables. Una variable como «inóculo de patógenos» se expande por especie; una variable de suelo se expande por horizonte y fecha. No son 342 mediciones obligatorias ni 342 predictores independientes.

Etiquetas de procedencia: **P1** = revisión de Agronomy 2025; **P2** = estudio de Computers and Electronics in Agriculture 2022; **S** = síntesis/modelo propuesto aquí; **D** = documentación externa consultada. Las ecuaciones de balances y optimización que se proponen más abajo son S, salvo las atribuidas expresamente a P2. El CSV indica base por bloque; no constituye una revisión sistemática con trazabilidad experimental individual de cada fila.

## 1. Qué dicen los papers y qué no permiten concluir

### P1. Al-Musawi, Vona y Kulmány, 2025

*Utilizing Different Crop Rotation Systems for Agricultural and Environmental Sustainability: A Review*. Agronomy 15, 1966. DOI: https://doi.org/10.3390/agronomy15081966.

Es una revisión temática, no un experimento único ni un modelo calibrado. Métodos: pp. 2–3; estrategias: §§3.1–3.5; fertilidad y nutrientes: §§4.1–4.2; plagas y malezas: §§4.3–4.4; rendimiento: §4.5; GEI: §5; limitaciones: conclusiones, p. 21.

Mecanismos aprovechables:

- Cambiar especies y hospedantes puede interrumpir ciclos de plagas y enfermedades.
- Leguminosas pueden incorporar N atmosférico mediante simbiosis; la cantidad depende de especie, ambiente y manejo.
- Raíces, residuos y actividad biológica cambian el reciclaje de nutrientes, agregación y dinámica del agua.
- Coberturas pueden capturar nutrientes, aportar biomasa y reducir erosión; también consumen agua y pueden dificultar el establecimiento siguiente.
- Pastoreo y estiércol reciclan nutrientes, con riesgos de compactación, distribución desigual e inocuidad.
- Efectos sobre rendimiento, rentabilidad y emisiones dependen del contexto y de la comparación de referencia.

Precauciones de lectura:

1. Las cifras «hasta 18% más SOC», «hasta 39% menos N2O» y los incrementos de rendimiento son resultados de estudios específicos recopilados. No son multiplicadores para cada parcela o campaña.
2. §3.2 menciona aproximadamente 75 kg N/ha de fijación en soja y 148 en alfalfa, y §3.3 describe 10–217 kg N/ha para coberturas leguminosas. Son ejemplos contextualizados. No equivalen a N residual disponible ni a una tasa universal de ahorro de fertilizante.
3. La tabla 4, p. 15, incluye soja rotada con rendimiento inferior al continuo en uno de los tratamientos. La rotación no garantiza una mejora en todos los escenarios.
4. Cambiar textura mineral no es el efecto normal de una rotación: arena/limo/arcilla son relativamente estables; estructura, porosidad, carbono e infiltración sí pueden cambiar.
5. Bajar pH no es automáticamente mejorar suelo; depende del pH inicial y del cultivo.
6. Menor flujo de CO2 del suelo no demuestra por sí solo mayor secuestro: hace falta balance de carbono y exportaciones. La revisión reconoce efectos variables y omite ciertas emisiones de maquinaria.
7. Hay una diferencia entre el intervalo temporal declarado en el resumen y métodos; y las conclusiones reconocen predominio de evidencia de regiones templadas. Para trópicos, zonas áridas y altoandinas se necesita validación específica.

### P2. Aggarwal, Srinivas, Puppala y Magner, 2022

*Integrated decision support for promoting crop rotation based sustainable agricultural management using geoinformatics and stochastic optimization*. Computers and Electronics in Agriculture 200, 107213. DOI: https://doi.org/10.1016/j.compag.2022.107213.

Caso: Muzaffarnagar, Uttar Pradesh, India. Considera arroz, trigo, maíz, mostaza, papa, caña y sorgo; usa 2.700 muestras de suelo, datos geográficos y clima histórico. Métodos: §§2.1–2.4, pp. 3–5; criterios: tabla 2; secuencias y agua: tabla 3; pesos arroz: tabla 6; limitaciones: §§4.5 y 5.

Pipeline:

1. Recoger propiedades del suelo, clima y terreno.
2. Seleccionar criterios y rangos con expertos y literatura.
3. Interpolar variables mediante kriging ordinario y semivariograma esférico.
4. Clasificar aptitud S1, S2, S3 o N.
5. Obtener pesos por comparación estocástica por pares —SPC— y revisión de consistencia.
6. Superponer capas para delimitar aptitud por cultivo.
7. Evaluar secuencias predefinidas compatibles con la aptitud y comparar ingreso y requerimiento de riego.

Los criterios no son los mismos para todos los cultivos. Por ejemplo, la tabla 2 selecciona pH, EC, N, P, K, OC y Zn para arroz, pero para papa solo pH, EC y OC entre los químicos. **Eso no significa que la papa no necesite NPK, ni que el maíz no necesite N porque no aparezca en su subconjunto.** Son decisiones del modelo del caso.

Límites para nuestro reto:

- La aptitud de capas y pesos no simula por sí sola balances diarios de agua, nutrientes, carbono o poblaciones de patógenos.
- La beta describe incertidumbre del juicio experto; no sustituye incertidumbre climática, error de medición ni incertidumbre de parámetros.
- Las medias climáticas de 1990–2019 no representan pronóstico futuro ni eventos en floración.
- Los valores de agua e ingresos de la tabla 3 son coeficientes de secuencias del caso, no funciones universales por especie.
- Los autores indican que no incluyeron producción/rendimiento como objetivo explícito y proponen incorporar mercado y trabajo.
- No se dispone aquí de los suplementos A1–A4; no se afirma reproducir completamente la optimización publicada.
- El artículo no expone en el cuerpo una formulación completa y reproducible del problema de asignación con todas sus restricciones y procedimiento de combinación de objetivos. Las restricciones propuestas en este informe son nuestras.
- NDVI de una fecha o año no debe usarse para descartar automáticamente barbecho agrícola: suelo temporalmente desnudo puede seguir siendo cultivable.

## 2. Matemática de la aptitud: cómo aprovechar P2 correctamente

Para un cultivo c y una parcela p, una aproximación multicriterio es:

\[
S_{p,c}=\sum_j w_{c,j}s_{c,j}(z_{p,j}),\quad w_{c,j}\ge0,\quad\sum_j w_{c,j}=1.
\]

Aquí `z` es la medición, `s` su función de aptitud y `w` un peso de importancia. No es una ecuación de rendimiento. Un peso de lluvia de 0,1694 no significa que la lluvia explique causalmente el 16,94% de la cosecha.

P2 tabla 6 reporta para arroz: temperatura 0,1745; lluvia 0,1694; textura 0,1316; pendiente 0,1351; EC 0,0932; pH 0,0842; N 0,0756; P 0,0291; K 0,0391; OC 0,0388; Zn 0,0293. Son pesos locales, no transferibles automáticamente.

No permitir que una suma compense una imposibilidad: si no cabe el ciclo entre heladas, falta agua legalmente disponible o hay una restricción de herbicida, el cultivo debe excluirse aunque tenga buen puntaje económico. Aplicar máscaras de viabilidad y umbrales antes del ranking.

### SPC y una corrección importante del artículo

Para una comparación incierta `A` en [l,u], se modela:

\[
A=l+(u-l)B,\qquad B\sim\mathrm{Beta}(\alpha,\beta).
\]

La forma correcta es:

\[
E[A]=l+(u-l)\frac{\alpha}{\alpha+\beta},
\qquad
\operatorname{Var}(A)=(u-l)^2\frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}.
\]

**En la ecuación (2), p. 5 del PDF, el factor (u−l) está impreso sin el cuadrado.** Se verificó visualmente la página, no solo la extracción de texto. No copiar esa errata en código.

Para un juicio triangular (l,m,u):

\[
\mu=(l+m+u)/3,
\qquad \sigma^2=(l^2+m^2+u^2-lm-lu-mu)/18.
\]

Definir `q=(μ−l)/(u−l)`, `v=σ²/(u−l)²`, `k=q(1−q)/v−1`; entonces `α=qk`, `β=(1−q)k`, verificando soporte, varianza y parámetros positivos. Juicios exactos o intervalos degenerados se manejan aparte. La restricción adicional de P2 `α,β≥1` tampoco debe asumirse satisfecha por todo juicio triangular.

P2 usa la aproximación a mediana:

\[
\widetilde B\simeq\frac{\alpha-1/3}{\alpha+\beta-2/3},\qquad
\widetilde A=l+(u-l)\widetilde B.
\]

Conviene calcular el cuantil beta numéricamente y tratar bordes/simetría explícitamente. Si se usan matrices recíprocas, imponer `a_ji=1/a_ij` después de convertir comparaciones y comprobar consistencia. El autovector principal se normaliza para obtener los pesos. Índice habitual `CI=(λmax−n)/(n−1)` y `CR=CI/RI`; el CR=0,099 de P2 no es una medida de precisión predictiva.

Otros detalles a resolver antes de implementar sus tablas: los intervalos impresos de temperatura de arroz no cubren claramente 20–25 °C; hay diferencias de redondeo en los puntajes de clases y los puntajes no forman una partición probabilística. Definir intervalos completos, límites inclusivos y tratamiento de datos faltantes. No copiar umbrales sin método de laboratorio, cultivar y región.

## 3. Inventario de factores

El CSV contiene nombres de máquina, unidad/formato, rol, grupo y procedencia/base. Muchos bloques incluyen extensiones de síntesis que no fueron medidos en los dos papers.

| Bloque | Variables conceptuales | Mecanismo principal |
|---|---:|---|
| Contexto y terreno | 15 | Área útil, altitud, pendiente, orientación, exposición y acceso |
| Suelo físico por horizonte | 24 | Reserva de agua, aireación, penetración de raíces, infiltración |
| Suelo químico por horizonte y método | 34 | Nutrientes disponibles, acidez, sales, sodicidad, toxicidad |
| Biología edáfica y sanidad | 18 | Fijación, reciclaje, hospedantes, plagas, malezas y resistencia |
| Clima y eventos por fase | 28 | Desarrollo, demanda atmosférica y estrés en fases sensibles |
| Agua disponible, riego y salinidad | 27 | Oferta real y legal, calidad, oportunidad y costo |
| Especie, cultivar y fenología | 38 | Calendario, raíces, demanda, tolerancias y uso cosechado |
| Demanda, extracción y fijación | 23 | Flujos de nutrientes y disponibilidad para el sucesor |
| Historia y transiciones | 20 | Memoria del suelo y riesgos de repetir hospedantes |
| Manejo, residuos y coberturas | 29 | Decisiones que modifican balances y establecimiento |
| Integración ganadera | 11 | Consumo de forraje, retornos, exportación y pisoteo |
| Economía y recursos | 31 | Rentabilidad, trabajo, maquinaria, mercado, liquidez y preferencias |
| Ambiente y regulación | 20 | Erosión, nutrientes perdidos, agua, biodiversidad, GEI y límites |
| Observaciones y calidad | 24 | Señales remotas, escala, incertidumbre y trazabilidad |
| **Total** | **342** | Variables expandibles por capa, fecha, especie y escenario |

### Variables especialmente fáciles de olvidar

- La especie y el cultivar, además de la familia botánica; dos familias distintas pueden compartir un patógeno de amplio rango de hospedantes.
- El uso cosechado: maíz para grano y maíz para ensilaje exportan cantidades de nutrientes muy distintas.
- Profundidad y distribución de las raíces frente a profundidad efectiva, compactación y nivel freático.
- Concentración de cada elemento en el producto y residuos, humedad comercial de la cosecha y rendimiento esperado.
- Cantidad, C:N, lignina, ubicación y fecha de incorporación de residuos; mineralización no es instantánea.
- La terminación de coberturas antes del cultivo comercial y su costo de agua, especialmente en secano.
- Fertilizantes, estiércol, enmiendas, agua de riego y nutrientes de origen atmosférico como aportes separados.
- P y K extraíbles dependen del método analítico; no se deben mezclar Olsen, Bray, Mehlich u otros como si fueran idénticos.
- Herbicida aplicado previamente y restricciones de resiembra de su etiqueta; la degradación depende de suelo y clima.
- Malezas voluntarias o vecinas que mantienen el «puente verde» de plagas durante una supuesta pausa.
- Años desde el último hospedante y supervivencia del patógeno, no únicamente último cultivo.
- Riesgo de lluvia o heladas en floración/cosecha, no solo promedios anuales.
- Tiempo para cosechar, preparar y sembrar; conflictos de maquinaria y trabajo entre parcelas.
- Mercado real, contratos, calidad, almacenamiento, secado, frío y pérdidas poscosecha.
- Tenencia de la tierra y horizonte económico: mejoras del suelo a diez años pueden no ser apropiables en un arriendo anual.
- Calidad de semilla, germinación y establecimiento, polinizadores y acceso a inoculantes como variables a desagregar localmente.
- Interacciones suelo × agua × clima × cultivar × manejo; no asumir que todas las contribuciones se suman.

Los 17 elementos esenciales son C, H, O, N, P, K, Ca, Mg, S, Fe, Mn, Zn, Cu, B, Mo, Cl y Ni. C/H/O entran principalmente por aire/agua; los otros 14 exigen considerar suministro mineral, disponibilidad o toxicidad según el caso. Silicio puede ser beneficioso y pertinente en ciertos cultivos, pero no se presenta aquí como nutriente esencial universal.

## 4. Tipos de suelo: cómo cambian la lógica

No hay un único «tipo de suelo» que determine la rotación. Textura, taxonomía, régimen hídrico, profundidad, química y estructura son dimensiones distintas que pueden coexistir.

| Condición | Consecuencia y decisión potencial | Lo que debe medirse |
|---|---|---|
| Arenoso | Drenaje rápido y generalmente baja retención; vigilar déficit y lixiviación; fertilización fraccionada/cobertura si hay agua | θFC, θWP, raíces, CEC, OC, nutrientes y riego |
| Franco | Puede ofrecer buen balance físico; su clase por sí sola no garantiza fertilidad | Perfil, drenaje, sales, nutrientes y manejo |
| Arcilloso | Puede almacenar bastante agua total, pero no toda es accesible; riesgo de aireación insuficiente y daño por tráfico húmedo | Curva de retención, estructura, Ksat, compactación |
| Limoso | Riesgo de sellado y erosión en condiciones expuestas; coberturas y conservación pueden ser prioritarias | Estabilidad, infiltración, pendiente, erosividad |
| Somero o pedregoso | Menor volumen explorable; un cultivo de raíz profunda no puede aprovechar un suelo inexistente | Profundidad efectiva, fragmentos y reserva hídrica |
| Salino | Estrés osmótico, tolerancias por cultivo y etapa; el lavado exige agua y drenaje | ECe, ECw, balance de sales y nivel freático |
| Sódico | Dispersión, mala infiltración y problemas estructurales; cambiar de cultivo puede ser insuficiente | ESP/SAR, Ca, estructura, agua y diagnóstico de recuperación |
| Ácido | Riesgo de toxicidad Al/Mn y limitaciones P/Mo o nodulación | pH con método, Al, P disponible, bases y necesidad de cal |
| Calcáreo/alcalino | Posibles limitaciones Fe/Zn/P; no se deducen solo del pH | Carbonatos, micronutrientes y pruebas locales |
| Hidromorfo/anegable | Falta de oxígeno; sistemas de arroz o drenaje requieren evaluarse como alternativas de manejo | Duración de inundación, redox, drenaje, calendario |
| Volcánico/ándico | A menudo alta retención y elevada fijación de P, con variación local | Retención, densidad y P disponible por método adecuado |
| Orgánico/turboso | Riesgo de subsidencia, oxidación y grandes pérdidas de C si se drena | Nivel freático, espesor, mineralización y protección ambiental |
| Compactado | Limita raíces/aire; raíces de cobertura no garantizan romper cualquier capa dura | Resistencia a humedad conocida y perfil compactado |
| Contaminado | Puede excluir producción alimentaria según contaminante/norma | Analítica específica y evaluación de inocuidad |

No asignar automáticamente «arroz a arcilla», «leguminosa a pobre» o «raíces profundas a seco». Son hipótesis que necesitan oferta de agua, clima, sanidad y datos del perfil.

## 5. Cuánto consume un cultivo: cinco cantidades diferentes

1. **Absorción total**: nutriente incorporado a toda la planta durante el ciclo.
2. **Extracción o exportación**: nutriente que abandona la parcela en producto, paja, forraje u otros materiales.
3. **Retorno**: nutriente en residuos/raíces que queda o regresa, con disponibilidad temporal.
4. **Dosis de fertilizante**: aporte de manejo calculado con diagnóstico, oferta del suelo, respuesta y recuperación; no igual a extracción.
5. **Consumo de agua**: evapotranspiración; no igual a riego aplicado ni a precipitación de aptitud.

Una ficha por especie/cultivar/uso/región debe registrar: duración y fases; Kc o Kcb; profundidad de raíces; tolerancias; rendimiento de referencia y humedad; coeficientes de extracción de N/P/K y otros elementos por tonelada; nutrientes de residuos y fracción retirada; fijación/retorno si es leguminosa; incertidumbre y fuente. Los dos PDFs no proporcionan esas fichas completas. No hay base para inventar una tabla universal de NPK por cultivo.

### Agua

Esquema FAO-56 de referencia (relaciones agronómicas estándar, no ecuaciones nuevas de los papers):

\[
ET_{c,pot}(d)=K_c(d)ET_0(d).
\]

En forma dual bajo estrés:

\[
ET_{a}(d)=\left[K_s(d)K_{cb}(d)+K_e(d)\right]ET_0(d).
\]

`ET0` depende de radiación, temperatura, humedad, viento y presión/altitud; `Kcb` depende del cultivo, fase y cobertura; `Ke` de evaporación del suelo; `Ks` del estrés. Esta forma no representa por sí sola todas las penalizaciones térmicas, salinas o nutricionales.

Penman–Monteith diaria de referencia:

\[
ET_0=\frac{0.408\Delta(R_n-G)+\gamma\frac{900}{T+273}u_2(e_s-e_a)}{\Delta+\gamma(1+0.34u_2)}.
\]

Unidades convencionales: ET0 mm/día; Rn y G MJ/m²/día; T °C; u2 m/s; presiones kPa. Calcular radiación neta y presión de vapor con convenciones correctas; no introducir radiación global como si ya fuera Rn.

Balance diario agregado de la zona radicular:

\[
W_{d+1}=W_d+P_d+I_{net,d}+CR_d-RO_d-DP_d-ET_{a,d}.
\]

Si se usa precipitación efectiva en vez de bruta, redefinir términos para no descontar dos veces escorrentía/drenaje. En un perfil multicapa distribuir entradas, flujos y absorción por capa; cuando crece la raíz, transferir explícitamente el agua de las nuevas capas exploradas.

\[
TAW=1000\sum_l(\theta_{FC,l}-\theta_{WP,l})\Delta z_l(1-f_{piedra,l}),\qquad RAW=p\,TAW.
\]

`Δz` en m y humedad volumétrica para tierra fina; aplicar la corrección por piedras solo si la medición no está ya referida al volumen total. Limitar las capas a la profundidad de raíces. La fracción p no es constante universal.

\[
I_{bruto}=I_{neto}/\eta,\qquad V=10A I_{bruto}.
\]

V en m³ si A está en ha e I en mm. Incorporar aparte lavado de sales, preparación/inundación de arroz y pérdidas de conducción según el límite del sistema.

**Ejemplo únicamente didáctico:** ET0=5 mm/día y Kc=1,1 durante 30 días ⇒ ET potencial=165 mm. Con lluvia efectiva 60 mm, agotamiento utilizable 25 mm y sin otros aportes, el déficit neto sería 80 mm. Con η=0,8 ⇒ 100 mm brutos, o 1.000 m³/ha. No es una estimación de una finca ni de un cultivo concreto.

### Lo cuantitativo verificable sobre agua en P2

Tabla 3, p. 5: **requerimiento de riego anualizado de secuencias**, no ET de especies individuales.

| Secuencia del caso de India | mm/año | m³/ha/año |
|---|---:|---:|
| Arroz–trigo–barbecho | 750 | 7.500 |
| Maíz–trigo–barbecho | 800 | 8.000 |
| Sorgo–mostaza–barbecho | 633,33 | 6.333,3 |
| Sorgo–trigo–barbecho | 733,33 | 7.333,3 |
| Arroz–mostaza–barbecho | 650 | 6.500 |
| Arroz–papa–maíz–papa–barbecho | 970 | 9.700 |
| Arroz–papa–caña–trigo–barbecho | 1.490 | 14.900 |

No deducir que maíz siempre consume más que arroz porque una secuencia tenga un coeficiente mayor: intervienen calendario, lluvia, manejo y anualización. Tampoco dividir una cifra de secuencia entre su número de cultivos para obtener necesidades individuales.

### Nutrientes y rendimientos

Para nutriente j, exportación con el producto:

\[
E_j=Y_{producto}\,r_{j,producto}+\sum_b B_{b,retirado}\,c_{j,b}.
\]

`Y` t/ha, `r` kg elemento/t producto; `B` t MS/ha y `c` kg elemento/t MS. Respetar base seca o humedad comercial. Si los residuos quedan, no contarlos como exportación.

Un ejemplo totalmente hipotético: cosechar 8 t/ha con coeficiente de exportación 15 kg N/t ⇒ 120 kg N/ha exportados en producto. Si el tejido aéreo residual contiene otros 50 kg N/ha y queda en campo, eso no implica que los 50 estén disponibles al sembrar el sucesor.

Conversión de concentración a stock de un horizonte:

\[
M_j=10C_j\rho_b z(1-f_{piedra})\quad[kg/ha],
\]

con C en mg/kg, ρb en Mg/m³ y z en m; mismas precauciones por tierra fina. **Un stock calculado a partir de una extracción química no es automáticamente un stock íntegramente absorbible.** El método y su calibración agronómica determinan la interpretación.

Las etiquetas comerciales suelen expresar P y K en óxidos:

\[
P=0.4364P_2O_5,\qquad K=0.8301K_2O.
\]

No mezclar kg P con kg P2O5 ni kg K con kg K2O en un balance.

Dos niveles de balance, que no se deben combinar sin cuidado:

**Sistema total suelo + biomasa dentro de parcela:**

\[
\Delta T_N=F_N+N_{fijado}+N_{riego}+N_{deposicion}+N_{importado}-E_N-L_N.
\]

Mineralización, inmovilización, absorción y retorno internos no crean/destruyen N total; son transferencias entre compartimentos. Para P y K no hay un término equivalente de fijación atmosférica biológica.

**Compartimento mineral disponible del suelo:**

\[
N^{min}_{d+1}=N^{min}_d+F_{min}+M_{org}+N_{riego}-U_{suelo}-I_{microb}-L_{lix}-L_{vol}-L_{den}.
\]

La fijación entra principalmente a la planta; sus residuos/rizodeposición entran después en los compartimentos correspondientes. No sumar todo el N fijado al N mineral del suelo durante el mismo ciclo.

La dosis de N puede aproximarse inicialmente con:

\[
F_N=\max\left(0,\frac{U_{objetivo}-S_{suelo}-C_{previo}-A_{otros}}{RE_N}\right).
\]

Debe calibrarse con respuesta a dosis, precios y riesgo; no es una receta agronómica. No contar dos veces el crédito del predecesor si ya está incluido en la mineralización estimada. Para P/K pueden corresponder estrategias de suficiencia, mantenimiento o construcción de fertilidad según el análisis local; no usar ciegamente esta ecuación de N.

### Leguminosas

\[
BNF=N_{acumulado}\,f_{Ndfa},
\]

siempre especificando si el N acumulado incluye raíces y rizodeposición. El beneficio para el siguiente cultivo depende de retorno, pérdidas, sincronía y nutrientes/agua limitantes. Una leguminosa cosechada para grano o forraje puede exportar mucho N, P y K. Puede reducir fertilización de N en ciertos sistemas y aun así agotar otros nutrientes. No existe la regla «leguminosa = suma fija de N disponible».

## 6. Lógica matemática de una rotación dinámica

Estado de la parcela:

\[
s_{p,t}=(agua_l,N_l,P_l,K_l,C_l,sales_l,estructura_l,patogenos_k,malezas_k,historial).
\]

Decisiones: cultivo/cultivar, siembra, riego, dosis y tiempos de fertilización, cobertura, terminación, labranza, retiro de residuos y pastoreo. Forzantes: clima, precios y disponibilidad de recursos.

\[
s_{p,t+1}=f(s_{p,t},c_{p,t},m_{p,t},\omega_t),\qquad
Y_{p,t}=g(s_{p,t},c_{p,t},m_{p,t},\omega_t).
\]

Un modelo solo del cultivo actual pierde memoria biológica, nutricional e hídrica. Una matriz de transición puede aproximar efectos, pero no sustituye estados cuando hay memoria de varios años.

### Calendario y fenología

\[
GDD_d=\max\{0,\min[(T_{max}+T_{min})/2,T_{cap}]-T_{base}\}.
\]

Es una aproximación: usar temperaturas base, techos y algoritmo calibrados por cultivar, no parámetros universales. Fotoperiodo y vernalización pueden requerir funciones adicionales. El tiempo de cosecha y preparación debe dejar una ventana real antes del sucesor; caña y perennes necesitan ocupación multitemporal, no «una casilla igual a cereal corto».

### Restricciones de asignación

Sea `x_pct ∈ {0,1}` y A_p área de parcela. En el esquema simple de una actividad por periodo:

\[
\sum_{c\in cultivos\cup\{barbecho,cobertura\}}x_{p,c,t}=1.
\]

El esquema debe ampliarse para cultivos simultáneos, franjas, mezclas o ciclos que cruzan periodos. Excluir cultivos inviables con `x_pct≤F_pct`, donde F codifica límites duros medidos/reglamentarios.

Para transiciones realmente incompatibles:

\[
x_{p,a,t}+x_{p,b,t+1}\le1.
\]

Para un patógeno k que exige una pausa de R periodos entre hospedantes, una representación simplificada es:

\[
\sum_{\tau=t}^{t+R-1}\sum_{c\in H_k}x_{p,c,\tau}\le1.
\]

R debe proceder de evidencia local y tiempos reales; no todos los patógenos se controlan con un intervalo fijo. Las malas hierbas hospedantes también deben manejarse.

Una dinámica conceptual de presión de organismo k:

\[
B_{k,t+1}=B_{k,t}\exp[r_k(c_t,clima,manejo)\Delta t]+\iota_{k,t}.
\]

`r` puede ser negativo en ausencia de hospedantes; `ι` representa entradas externas. Los parámetros requieren datos y deben incorporar adaptación o supervivencia prolongada cuando aplique.

Agua por turno o mes:

\[
\sum_p10A_pI_{p,t}\le V_t^{disponible}.
\]

No basta una restricción anual si la demanda se concentra en floración o no coincide con turnos. De forma análoga limitar trabajo, maquinaria, liquidez, insumos y capacidades de almacenamiento por periodo.

El estado final debe impedir «explotar y abandonar»:

\[
C_{p,T}\ge C_{min},\quad
W_{p,T}\ge W_{min},\quad
NPK_{p,T}\in\mathcal S_{segura},\quad
ECe_{p,T}\le ECe_{max}.
\]

Los umbrales son específicos y algunos se modelan como penalizaciones, no obligaciones rígidas.

### Objetivos y riesgo

Beneficio neto descontado:

\[
NPV=\sum_{p,t}\frac{A_p(Precio_{c,t}Y_{p,t}-Costo_{p,t})}{(1+r)^t}.
\]

Construir una frontera de Pareto con beneficio, uso de agua, pérdidas de nutrientes, erosión, GEI y calidad final del suelo. Para una suma ponderada normalizar cada indicador y explicar pesos al agricultor; no sumar dólares + mm + carbono sin normalización.

Una opción robusta y comunicable: maximizar `E[NPV] − λ CVaR_α(pérdida)` sujeto a límites de agua, sanidad y suelo, utilizando escenarios de clima/precios. CVaR necesita distribución, nivel α y suficiente muestreo; no es una garantía con pocos escenarios. Preservar correlaciones y separar incertidumbre de medición, clima y parámetros.

Para carbono, un esquema de compartimentos sería `C_(t+1)=C_t+entradas estabilizadas−descomposición−erosión/exportación`, con descomposición dependiente de temperatura, humedad, calidad de residuo y protección mineral. Un aumento porcentual de P1 no se aplica cada año como interés compuesto.

## 7. Datos NASA y locales para el reto

| Fuente | Qué aporta | Qué no demuestra |
|---|---|---|
| NASA POWER | Variables meteorológicas y radiación; se comprobó una consulta diaria real de T2M, PRECTOTCORR, radiación, RH2M y WS2M | No es estación de parcela ni pronóstico por el hecho de contener histórico |
| GPM IMERG | Series de precipitación y extremos, varios intervalos y versiones | Un pixel no representa necesariamente lluvia de cada ladera; requiere QA/sesgo local |
| SMAP L4 | Producto de humedad superficial y zona radicular, 3 horas, malla de 9 km en versión 8 consultada | La humedad radicular es una estimación modelada/asimilada; no es medición fina directa de cada raíz |
| HLS Landsat/Sentinel-2 | Reflectancia armonizada y series para cobertura, vigor y fenología; malla nominal 30 m | NDVI no mide directamente NPK, pH o especie patógena; nubes y mezclas afectan |
| ECOSTRESS | Temperatura/estrés y productos de ET cuando hay cobertura válida | No sustituye un balance continuo sin modelado, QA y validación |
| ISRIC SoilGrids, no NASA | Propiedades edáficas modeladas a 250 m, seis profundidades e incertidumbre | No equivale a laboratorio; N total no es N mineral disponible; no asumir mapas de P/K disponibles |
| Laboratorio/campo | pH, EC, nutrientes con método, profundidad, compactación, sanidad | Una muestra superficial aislada no representa todo el perfil ni futuras campañas |
| Agricultor/autoridad/mercado | Historia, riego, recursos, restricciones, costos, prioridades y precios | No deben inferirse automáticamente de la reflectancia |

Unir datos por polígono, fecha y soporte espacial. Remuestrear 9 km a 30 m no genera nueva información. Modelar y mostrar incertidumbre; registrar fechas de actualización, nubes, píxeles mixtos, imputación, método analítico y versión del producto. No asumir que promediar el pixel SMAP resuelve heterogeneidad de una finca pequeña.

## 8. Qué construir primero y cómo comprobarlo

Primero escoger una región, sistema de secano o riego y catálogo local de especies/cultivares; eso fija qué factores de los 342 son relevantes. No se necesita recoger todos desde el inicio.

Base mínima para recomendaciones condicionadas, no universales:

1. Polígono, área, altitud, calendario y sistema productivo.
2. Historia de campañas suficiente para los organismos y secuencias consideradas, con fechas y manejo de residuos.
3. Textura, profundidad efectiva, drenaje, pH, EC, carbono orgánico y N/P/K con método y fecha.
4. Clima diario, agua inicial por perfil o estimación con incertidumbre, oferta/cuotas/turnos y calidad del riego si existe.
5. Fichas de cultivos con fenología, Kc/raíces, rendimiento local, extracción, tolerancias y hospedantes.
6. Problemas sanitarios, malezas y restricciones de herbicidas del historial.
7. Costos, precios, trabajo, maquinaria y preferencias; todos pueden acotar viabilidad.

No disponer de alguna medición no autoriza inventarla. Usar un valor previo con intervalo y mostrar cómo cambia el ranking; excluir recomendaciones que dependan de un dato crítico desconocido o presentarlas expresamente condicionadas.

Resultados útiles: tres alternativas con fechas; agua neta/bruta y meses críticos; rendimiento y margen bajo escenarios; exportación y balance de nutrientes; tendencia del suelo; riesgos de sucesión; explicación de los factores que cambiaron la decisión; condiciones que invalidarían la recomendación.

Validación:

- Conservación de masa y unidades en balances, con pruebas de borde.
- Predicción de humedad, ET, rendimiento y nutrientes contra observaciones locales; separar calibración y validación.
- Comparar con la rotación actual, recomendación de agrónomo y un baseline de aptitud sin memoria.
- Validar fuera de muestra temporal y espacial, con varias campañas cuando sea posible.
- Medir errores y cobertura de intervalos; verificar ranking y factibilidad de secuencias, no únicamente ajuste de rendimiento.
- Comprobar sensibilidad a pesos, precios, lluvia, profundidad, Kc y extracción.
- Revisar todas las propuestas con conocimiento agronómico local antes de tratarlas como recomendaciones de campo.

No se ha desarrollado ni validado un predictor en esta entrega. Tampoco se creó o ejecutó ningún workflow de n8n: esta fase es investigación y especificación.

## 9. Fuentes y límites de acceso

### Leídas

- P1: PDF proporcionado por el usuario, DOI https://doi.org/10.3390/agronomy15081966.
- P2: PDF proporcionado por el usuario, DOI https://doi.org/10.1016/j.compag.2022.107213.
- NASA POWER documentación: https://power.larc.nasa.gov/docs/ y https://power.larc.nasa.gov/docs/services/api/temporal/daily/ . Se recibió HTTP 200 en documentación y en una consulta de API de dos días; no se usa esa muestra como clima representativo de una finca.
- SMAP L4 versión 8: https://nsidc.org/data/spl4smgp/versions/8 . Consultar versión vigente al implementar, sin cambiar silenciosamente parámetros/productos.
- GPM IMERG: https://gpm.nasa.gov/data/imerg . Ver unidades de tasa frente a acumulación y productos Early/Late/Final.
- HLS: https://hls.gsfc.nasa.gov/ y https://hls.gsfc.nasa.gov/products-description/ .
- ECOSTRESS: https://www.earthdata.nasa.gov/data/instruments/ecostress .
- ISRIC SoilGrids FAQ: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html .

### Referencia técnica y acceso no logrado

Allen et al. (1998), FAO Irrigation and Drainage Paper 56, *Crop Evapotranspiration*: https://www.fao.org/4/x0490e/x0490e00.htm . Las rutas FAO probadas devolvieron HTTP 403 en este entorno. Se presentan las relaciones estándar con atribución bibliográfica; no se afirma haber consultado en vivo sus tablas ni extraído de ellas coeficientes por especie. También hubo 403 en páginas de extensión de Minnesota. No se usaron como si se hubieran leído.

Un PDF de Purdue consultado durante la búsqueda resultó tratar malezas de césped y se descartó como fuente de extracción de nutrientes. La página de Iowa PM1688 se pudo abrir, pero eso no establece acceso al contenido descargable de su guía. No se copian coeficientes no comprobados.

Falta resolver la región y los cultivos objetivo, obtener sus tablas locales de demanda/extracción, y acceder a suplementos de P2 si se pretende replicar exactamente su optimización. Estos límites no impiden especificar el modelo, pero sí impiden dar dosis o consumos finales fiables por parcela.


</cursor_untrusted_data_1337>
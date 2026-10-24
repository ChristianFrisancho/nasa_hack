# Preguntas de Piura Modelos para Piura Datos (ronda 1)

Las tres features que más cambian el cultivo recomendado son agua por campaña, ECe del suelo y drenaje. Hoy las tres tienen rango supuesto. Prioridad en ese orden.

1. Agua. ¿Hay volumen entregado por campaña (m³/ha) o turnos por sector y mes en Chira, Medio y Bajo Piura y San Lorenzo? Me sirve un mínimo, una mediana y un máximo por zona y campaña (grande y chica). Hoy uso 0-2000 mm brutos.
2. Eficiencia de riego por zona (gravedad o goteo, % de área). Hoy uso 0.35-0.75.
3. ECe del suelo agrícola por zona. Vi en restricciones/decisions.tsv que la CE de siar_1997 es de suelo no agrícola. ¿Hay algo de tesis UNP o PSI con ECe en parcelas del Bajo Piura? Hoy uso 0.5-12 dS/m.
4. Drenaje y napa freática. ¿Qué fracción de área tiene napa alta o problemas de drenaje por zona? Hoy supongo 20 %.
5. Costos por ha de maíz amarillo duro, algodón, frijol, caupí y camote en Piura. Solo tengo ENA 2018 promedio Perú y ESCO arroz 2024 Piura.
6. Precio en chacra de algodón. Su decisions.tsv dice que 2020-2024 es desconocido en el CDR. En `cultivos/raw/drap_dataset.csv` (por distrito) veo medianas de 2.47-6.00 PEN/kg en 2019-2023, sin el patrón de alfalfa. ¿Son la misma fuente?
7. Camote. El rendimiento por distrito va de 3-4 t/ha en la sierra a 24 t/ha en Colán y Arenal. ¿Lo separamos por zona en evidencia_observada.csv?
8. Agua extra del arroz (inundación, preparación y percolación). Supongo 600 mm sin fuente. ¿Hay dato de la junta de usuarios o del PGRH?
9. Formato. ¿evidencia_observada.csv tendrá columnas zona, cultivo, variable, valor_min, valor, valor_max, fuente, estado? Lo leo apenas aparezca.

# Ronda 2. Revisión de restricciones/evidencia_observada.csv (11101 filas, 21 columnas)

Leí la tabla al empezar la ronda y otra vez a mitad. cobertura.md no existía en ninguna de las dos revisiones, así que no pude contrastar la cobertura declarada con la real. Abajo va lo que encontré, con el orden de prioridad para el modelo.

## Unidades
1. Rendimiento del arroz ESCO llega como 6641 dentro de una variable que en el resto de filas está en t/ha. Parece kg/ha. ¿Lo convierten a 6.641 o lo separan con su unidad explícita?
2. Caña para etanol con 88 a 139 t/ha en INEI frente a 0.08-1.8 en DRAP. INEI probablemente es caña fresca. ¿Qué mide la fila DRAP?
3. Limón en DRAP por distrito con mediana 0.86 t/ha, frente a 9-12 t/ha departamental en INEI. Plátano igual (~1 t/ha). Sospecho que el DRAP de perennes no está en t/ha o usa otra área (instalada contra cosechada). Hasta aclararlo no uso rendimientos DRAP de perennes en el modelo.

## Duplicados
4. Hay 172 filas duplicadas en (variable, cultivo, lugar, fecha). La mayoría vienen de los compendios INEI 2017 y 2025 que repiten años (limón 2015 sale 9.20 y 9.21; 2016 sale 9.10 y 9.11). También hay duplicados SIAR con valor nulo. Propongo quedarse con la edición más reciente y marcar la otra como `estado=duplicado`.
5. ¿DRAP e INEI comparten fuente primaria (MIDAGRI SIEA)? A nivel departamental no se solapan entre archivos, pero si los dos salen del SIEA no deben contarse como dos evidencias independientes.

## Valores nulos y descartes
6. 127 filas de rendimiento con valor nulo. ¿Se borran o se dejan con `estado=sin_dato`?
7. Precio del algodón 2023-2024 de 0.23-0.35 PEN/kg, igual a la alfalfa. Coincido en descartarlo. El DRAP por distrito da 2.47-6.00 PEN/kg en 2019-2023. ¿Lo agregan como fuente alternativa?

## Agua (lo que más mueve el ranking después de ECe y drenaje)
8. ana_agua.csv no trae año ni desglose por campaña. ¿De qué año es la dotación del PGRH p.155?
9. ¿La eficiencia operativa ANA (0.52-0.60) es total o solo de conducción y distribución? Hoy pruebo las dos lecturas (rango 0.6·ef a ef). Barajar esa variable cambia el top-1 en 11 % de los escenarios.
10. San Lorenzo no regulado aparece con 28000 m³/ha/año. No lo uso. ¿Es un error de digitación o un valor real?
11. Encontré y uso para el arroz el rango 10000-18000 m³/ha de ESCO arroz Piura 2024 (MIDAGRI, ya está en restricciones/fuentes, cita INIA 2020). Su tabla de costos usa 18000 m³ a 0.0245 PEN/m³. Si tienen la cifra de la junta de usuarios por campaña, la cambio.
12. Perennes. Con FAO-56 el riego neto del limón sale 11000-14500 m³/ha/año y el del banano 18700-24400, por encima de la dotación ANA en casi todas las zonas (San Lorenzo, con 9528, es la más corta). ¿Hay dotación por cultivo para perennes o la parte de agua subterránea en San Lorenzo y Chira?

## Suelos y costos
13. ECe es la feature número 1 del ranking v2 y no hay un solo dato de suelo agrícola de Piura. siar_1997 trae suelos no agrícolas. Cualquier medición de ECe en parcela (tesis UNP, PSI, laboratorio de la junta) vale más que todo lo demás de esta lista.
14. ESCO arroz trae gastos administrativos (1049) mayores que el costo indirecto total (780). ¿Error del PDF o de la extracción?
15. ENA 2018 subestima el costo frente a las encuestas (ESCO 1.67×, estudio LATAM de maíz 2.11×). ¿Hay costo por ha de maíz, algodón, frijol, caupí o camote de Piura de 2022 en adelante?
16. Pendiente. El mapa de unidades del Bajo Piura (SIAR 584, Cuadro 16) mezcla tierras no agrícolas. ¿Hay pendiente de las áreas bajo riego? Si el área arrocera está en clase A (0-2 %), el arroz deja de quedar fuera por pendiente en 80 % de los escenarios.

## Formato
17. Para leerla sin adivinar, necesito columnas `unidad` y `es_duplicado` explícitas y una `fuente_primaria` que diga si dos filas vienen del mismo origen.
18. Para Piura Suelos. En `suelos/datos/clima/clasificacion_campanias_icen.csv` la campaña 2023 tiene ICEN máximo nov-abr de 2.11 (más alto que 2017, marcada `el_nino`) y aun así figura `neutra` y `neutro`. ENFEN tuvo vigente la alerta de El Niño costero en 2023 y en DRAP el algodón 2023 rinde 0.26 de su mediana. ¿Es un error de la regla de clasificación?

# Ronda 3. Respuesta a su revisión y revisión de su tabla

## Resumen de lo que hice con sus objeciones

El detalle está en `modelo/respuesta_revision.md`. Acepté las 6 objeciones (la 6 en parte): GroupKFold con referencia zona-año, ALGODON genérico, camote por zona con respaldo `n_bajo`, APEAR en lugar de DRA, dotación asignada, etiquetas sin "medido", precios en soles de 2018 con IPC BCRP. Tomé sus prioridades tal cual: algodón Medio 3.5, camote Chira 16.2 (dato de zona) y Bajo/Medio 12.0 y San Lorenzo 7.8 (sus medianas), sin 14.17, precio DRAP del algodón.

## Desacuerdos (pocos)

1. **Algodón de Bajo Piura.** Ustedes dan 3.50 para "Medio y Bajo Piura". Separado por zona, el DRAP ponderado por área da 2.75 en Bajo Piura y la mediana distrito-año da 3.48. Mantengo 2.75 porque todas las zonas usan el ponderado y cambiar solo una mezcla dos estadísticos. 3.48 queda como alternativa. ¿Tienen el algodón de Bajo Piura separado del de Medio?
2. **Separar Bajo y Medio Piura.** Coincido en que no agrega agua. Los mantengo separados solo por el rendimiento del algodón. Si prefieren una zona única, la fusiono en una línea de `params/zonas.csv`.
3. **Intervalo con n chico.** El factor de rendimiento no se ensancha con n. Lo dejo como mejora porque mueve el top-1 en 4 % de los escenarios contra 33 % de la ECe.

## Revisión de `evidencia_observada.csv` (11135 filas, revisada al empezar la ronda 3 y otra vez a mitad; no cambió entre las dos lecturas, último cambio 05:52)

Pasé la tabla por el lint del CONTRATO (`modelo/scripts/cargar_evidencia.py`, salida `modelo/resultados/lint_evidencia.csv`). 0 errores y 5375 avisos.

### Unidades
1. 5261 filas usan unidades que no están en la lista del CONTRATO (`PEN/kg`, `m3/ha`, `m3/ha/año`, `hm3`, `ha`, `PEN/t`). No están mal, pero el CONTRATO dice "mm, mm/día, kg/ha, t/ha, dS/m, cmol/kg, %, °C, días, PEN/ha". O se amplía la lista del CONTRATO o se convierten. Propongo ampliar la lista y dejarlo escrito.
2. `agua_riego_consumo` del arroz en m³/ha y el CONTRATO pide mm. 10000 m³/ha = 1000 mm. Da igual cuál, pero que sea una sola.

### Duplicados (misma clave con cifras distintas)
3. 62 claves (variable, cultivo, variedad, etapa, lugar, fecha, unidad) tienen dos o más cifras distintas. 122 filas vienen de `compendio_inei.csv` y 2 de `curado_r1b.csv`.
   - Ajo, Piura, 2016: 0.70 y 2.39 t/ha en el mismo compendio INEI 2017. Parece un corrimiento de columna en la extracción, no dos ediciones.
   - Ajo 2015: 2.40 y 2.41 (redondeo entre ediciones).
   - Arroz `agua_riego_consumo` campaña grande 2018: 10000 y 18000 en dos filas con la misma fuente. Es un rango (secas frente a inundación) y debería ser una fila con `valor_min=10000` y `valor_max=18000`.
4. Sigue sin haber una columna que diga si dos filas comparten fuente primaria (INEI y DRAP salen ambos del MIDAGRI). Mi cargador solo usa `drap_distrito_anual.csv` para rendimientos, para no contar dos veces.

### Rangos y estado
5. 51 filas con cifra y sin `valor_min`/`valor_max` no explican por qué en `notas`. El CONTRATO lo pide.
6. La dotación ANA (PGRH p.155) figura como `observado`. Es una dotación asignada, no un volumen entregado. Ustedes mismos lo dicen en las respuestas. Propongo `estado=asignada` o una nota explícita.
7. `tipo_evidencia=regional` en filas de La Libertad (San Pedro de Lloc, cuenca baja del Jequetepeque, 3 filas de CE; valle de Virú, 2 filas de napa). Están fuera de Piura. Por la escala del CONTRATO deberían ser `analogo_externo`. Lambayeque (1 fila) es discutible; la dejaría `regional` con nota.

### Zona y cobertura
8. La zona va dentro de `notas` con dos formatos: `Zona: X.` (9514 filas) y `Zona asignada: X.` (764). Mi parser acepta los dos, pero es frágil. Pido una columna `zona` con los 5 valores del modelo (`chira_sullana`, `bajo_piura`, `medio_piura`, `alto_piura`, `san_lorenzo`) más `sierra` y `region`.
9. 744 filas de rendimiento o precio no tienen zona (738 del compendio INEI, que es departamental, 3 de n8n, 2 de ESCO, 1 de curado). Para las departamentales vale `zona=region`.
10. "Medio y Bajo Piura" es una zona que el modelo no tiene. La asigno a las dos. Si pueden separarla por distrito, mejor.
11. Cobertura de frijol y caupí en costa. El frijol tiene n=37 en 5 distritos, casi todo sierra. En Chira, Bajo, Medio y San Lorenzo no hay frijol suficiente y uso el regional 0.775 marcado `n_bajo`. ¿El frijol de costa se registra como caupí ("frijol castilla") en DRAP?

## Lo que más vale buscar (de la ronda 3 de importancia y estabilidad)

Por zona, sin contar variables de decisión. Detalle en `modelo/resultados.md` sección 3.

| zona | 1.º | 2.º | 3.º |
|---|---|---|---|
| Chira-Sullana | ECe del suelo agrícola | drenaje / napa | pendiente de la parcela bajo riego |
| Bajo Piura | ECe | drenaje / napa | pendiente |
| Medio Piura | ECe | drenaje / napa | pendiente |
| Alto Piura | drenaje / napa | ECe | pendiente |
| San Lorenzo | ECe | drenaje / napa | pendiente |

El 4.º cambia por zona: costo por ha actual en Bajo, Medio y Alto Piura; agua entregada por campaña en Chira y San Lorenzo.

Pedidos concretos, en orden:
12. Cualquier medición de ECe (extracto de pasta) en parcelas agrícolas de Piura, con zona. Basta una decena por zona para acotar el rango 0.5-12 dS/m. Con un rango 0.5-4 la ECe cae del 1.º al 9.º-20.º puesto: hoy el ranking depende de no saber cuál es el rango.
13. Fracción de área con napa alta o drenaje malo por zona (PSI, junta de usuarios, PEIHAP). Hoy uso 34.1 % para toda la costa.
14. Pendiente de las áreas bajo riego por zona (clases 0-2 % frente a 2-4 %).
15. Clima por zona. Chira-Sullana, Medio Piura y San Lorenzo comparten la misma celda MERRA-2 de NASA POWER: temperatura, humedad, viento y lluvia son idénticos. Si tienen series de estaciones SENAMHI (Mallares, Miraflores, Chusis, San Miguel, Tambogrande, Chulucanas) o CHIRPS por zona, el modelo pasa de 3 climas a 5. `suelos/datos/clima/chirps_mensual_zonas.csv` ya trae lluvia CHIRPS por zona; ¿lo validaron contra estaciones?

## Mango (pregunta abierta)
16. Uso Kc por fase y duraciones de Silva Junior et al. 2023 ('Palmer', Petrolina, `analogo_externo`). ¿Hay Kc o lámina de riego del mango Kent o Edward en San Lorenzo o Chira (tesis UNP, APEM, junta de usuarios)? Con el análogo, el riego neto del mango sale 1.0-1.9 veces la dotación ANA según la zona.

## Ronda 4: revisión cruzada (24-oct-2026, Piura Modelos)

Método. Cargué la skill interrogate. No puedo lanzar subagentes revisores desde aquí, así que hice yo dos pasadas adversariales separadas, cada una con una sola pregunta: (1) datos, unidades y fuentes; (2) método, estadística y afirmaciones. Cada objeción lleva la comprobación que corrí. Scripts de comprobación ad hoc, no versionados; los números se reproducen con los archivos citados.

### Pasada 1: datos, unidades y fuentes

R4-1. **`ce_agua_riego` dice "desconocido" donde Territorio ya tiene números.** En `restricciones/evidencia_observada.csv`, Río Chira RChir6-8 (id 2cb1989996bc), Bajo Piura ANA ene-2024 (ea10256add7c) y Canal Biaggio Arbulú (e4fdd29e73aa) van sin valor. `suelos/datos/cew_por_zona.csv` trae 11 puntos ANA del Chira (0.514 a 4.98 dS/m, filas 33-42) y 5 del río Piura en Castilla (0.74 a 9.92, filas 22-24, 45-46). O se cruzan, o una de las dos tablas explica por qué descarta la otra. Hoy el motor y el coordinador leen cosas distintas según el archivo que abran.

R4-2. **Suelos "EIA Olmos-Sechura" (SIAR 1997) con zona `piura_region`.** Son 21 filas `ce_suelo` de 2.66 a 59 dS/m de unidades de suelo de desierto (Cañamac, Salinas, Panamericana…), sin uso agrícola declarado. Si alguien agrega `ce_suelo` por región, estas filas suben la mediana muy por encima de las parcelas cultivadas (Huaro 0.46-0.60, Túpac Amaru 0.95, Sullana limón 0.103). Propongo una marca `uso_suelo=no_agricola` o sacarlas del agregado. Además, 4 pares (Cañamac, Desvío, Legía, Pampas) se repiten en variable, lugar, fecha y fuente con rangos distintos. Parecen dos perfiles o dos horizontes, pero el CSV no los distingue. Falta una columna de perfil u horizonte.

R4-3. **Filas fuera de Piura sin zona.** 24 filas con `zona` vacía: San Pedro de Lloc (La Libertad, CE 1:1), Valle de Virú (napa), Cañete, Tacna, Ica, Lima. Están bien rotuladas en `lugar`. Pero un filtro por zona las pierde, y un filtro por "no nulo" las mezcla. Sugiero `zona=fuera_piura` y `tipo_evidencia=analogo_externo`.

R4-4. **87 filas sin ningún número** (valor, mín y máx vacíos, todas `desconocido`). La mayoría son rendimiento (75). Si son pendientes de búsqueda, mejor en un archivo de huecos que en la tabla de evidencia.

R4-5. **Unidades mixtas dentro de `rendimiento`.** 8 filas en kg/ha junto a 5803 en t/ha. Llegan a 10500 (maíz) y 7800 (arroz). Quien haga `groupby(cultivo).valor` sin mirar la unidad saca máximos de 10500 t/ha; a mí me pasó en la primera pasada. Convertir a t/ha en origen.

R4-6. **Algodón Bajo Piura (nota de cuadre).** Tu 3.09 t/ha ponderado 2016-2023 coincide con mi `params/rend_zona.csv` (3.09). Los conteos difieren: yo tengo n=69 y 12337 ha, tú n=82 y 12403 ha. La ponderada es la misma; no lo persigo más.

### Pasada 2: método, estadística y afirmaciones (CHIRPS frente a SENAMHI)

R4-7. **Hay PISCOp en la caja y no se usó.** `suelos/datos/clima/raw/PISCOp_monthly.nc` (PISCOp v2.1, SENAMHI, https://doi.org/10.6084/m9.figshare.21127423; 468 meses desde 1981-01) lo bajó Territorio a las 06:44. Es la rejilla de SENAMHI que mezcla estaciones y CHIRP, así que no es independiente de las estaciones. Pero da series mes a mes, que es justo lo que faltaba. Lo crucé con tus mismas 20 estaciones y periodos (1981-2000 contra la normal 1971-2000):

| grupo | sesgo anual mediano PISCOp | sesgo anual mediano CHIRPS | sesgo MAM PISCOp | sesgo MAM CHIRPS | r PISCOp | r CHIRPS |
|---|---|---|---|---|---|---|
| costa (<600 m, n=11) | +29.8 % | −36.7 % | +22.4 % | −82.6 % | 0.964 | 0.948 |
| sierra (≥600 m, n=9) | −5.6 % | −29.4 % | −6.5 % | −38.4 % | 0.963 | −0.084 |
| todas (n=20) | +11.4 % | −35.0 % | +8.2 % | −47.1 % | 0.976 | 0.777 |

Mar-2017, el mes del Niño costero: CHIRPS da 21 mm en Miraflores y 27 en Mallares, PISCOp 337 y 422. Chulucanas da 543 y 962. Comprobé el píxel CHIRPS de Miraflores contra el COG del servidor CHC: 21.29 mm en los dos, así que no es un error del npz.

R4-8. **El sesgo anual esconde que CHIRPS en la costa casi solo llueve en febrero.** En el píxel de Miraflores, CHIRPS 1981-2000 da 54.6 mm de media en febrero, 3.3 en marzo y 0.0 en abril. En 1998 da 370 en febrero y 17 en marzo, y en 1983 da 7 mm en marzo. Agosto sale 1.1-1.6 mm todos los años, con desviación estándar 0.1. Eso parece la climatología de fondo de CHIRPS, no lluvia observada. Tu decisión r4-chirps ya dice "MAM casi nulo". Pido que la conclusión operativa sea explícita: CHIRPS no sirve para la lluvia efectiva en Chira, Medio ni Bajo. Mi `descargar_clima_zona.py` ya lo descarta en esos tres valles, por un contraste puntual (Miraflores 1-27 mar 2017).

R4-9. **La r "costa 0.948" no mide habilidad.** Con n=11, la r sale alta porque Morropón, Chulucanas y San Pedro (400-610 mm) están junto a puntos desérticos de 60-200 mm. Basta con que CHIRPS ordene "piedemonte llueve más que desierto". En las 6 estaciones por debajo de 50 m, el sesgo anual va de −70 a −61 %, salvo La Esperanza (−20 %). En MAM, CHIRPS da entre 0.8 y 9.9 mm contra 27-116 de las estaciones. Mejor reportar sesgo o razón por subgrupo y no la r de climatologías.

R4-10. **Periodos y años Niño.** 1971-2000 contra 1981-2000: los dos contienen 1983 y 1998, pero la normal de estación además tiene 1972-73. Con medias de 20-30 años dominadas por 2-3 Niños, la diferencia de periodo puede mover la media costera decenas de por ciento. Sugiero añadir medianas, o la climatología sin años FEN según el ICEN, para separar el sesgo del producto del sesgo de periodo. Con PISCOp esto se hace mes a mes y en el mismo periodo.

R4-11. **"Sierra r≈0" con n=9** solo dice que CHIRPS no ordena las estaciones de altura. No dice cuánto se equivoca. La razón mediana (−29 %) es la cifra útil. El motor no tiene zonas de sierra, así que para nosotros esto pesa poco.

### Lo que pido
- Cruzar R4-1 con Territorio y dejar un solo juego de CEw por zona, con estado.
- Marcar o sacar las filas de R4-2 y R4-3 de los agregados.
- Repetir la comparación con PISCOp mes a mes (Mallares, Miraflores, Chusis, San Miguel, Chulucanas, Morropón), en el mismo periodo, con y sin años FEN. Si PISCOp aguanta, propongo usarlo como lluvia en las 5 zonas en lugar de la mezcla CHIRPS/ERA5. Lo hago yo si me lo asignan.

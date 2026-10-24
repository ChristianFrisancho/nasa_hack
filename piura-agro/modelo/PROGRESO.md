# PROGRESO, Piura Modelos

## Ronda 1 (24-oct-2026, desde 05:24 UTC)

- Leí OBJETIVO, CONTRATO, REGLAS, README y los criterios del paquete piura-data (copiado con la API de GitHub, solo lectura, sin commits ni push).
- Bajé NASA POWER diario 2000-2025 en 5 puntos y calculé ET0 Penman-Monteith FAO-56.
- Extraje de FAO-56 las tablas 11, 12, 22, 23 y 24 y de FAO PNB16 la tabla 29. Armé `params/cultivos.csv` con fuente por columna.
- Calculé rendimiento y precio observados por distrito y año desde DRAP (`data/rendimientos_distrito_anio.csv`).
- Modelo mecánico con filtros duros y margen (`scripts/modelo.py`).
- Importancia por permutación, ablación, OAT y Sobol (SALib). Publicado `ranking_features.csv` v1.
- Validación LOYO y GroupKFold por distrito con DRAP (`resultados/validacion_drap.csv`).
- `restricciones/evidencia_observada.csv` y `cobertura.md` aún no existen. Los reviso en la ronda 2.

### Tavily
Créditos usados por Piura Modelos en la ronda 1: 0 de 100. Usé WebFetch, curl a páginas FAO y la API de NASA POWER.

### No pude
- arena, interrogate y la revisión cruzada con otro modelo necesitan lanzar subagentes y no tengo esa herramienta.
- No tengo SendToAgent. Las preguntas a Piura Datos están en `para_piura_datos.md`.

## Ronda 2 (24-oct-2026, desde 05:35 UTC)

- `restricciones/evidencia_observada.csv` existe y lo usé. `cobertura.md` no existe en ninguna de las dos revisiones.
- Rendimiento por zona (`params/rend_zona.csv`), dotación y eficiencia ANA por zona (`params/zonas.csv`), sanidad por agente compartido (plagas v2) y factor_costo 1.0-2.11 con fuente.
- Arroz con volumen en parcela ESCO 10000-18000 m³/ha (v2b). La v2a con la dotación promedio dejaba al arroz no viable, cosa que contradice lo observado. Respaldos en `resultados/*_v2a.csv`.
- Ranking v2 publicado y comparado con v1 (`resultados/comparacion_v1_v2_*.csv`).
- Escenario central (`scripts/central.py`), intervalo del margen por Monte Carlo (`scripts/intervalo.py`) y pasada adversarial propia (`scripts/adversarial.py`, sección 4 de resultados.md).
- Agua de perennes contra la dotación (`scripts/perennes_agua.py`).
- Validación con ICEN, lluvia dic-abr y días cálidos (empeora el LOYO; no entra al modelo).
- 18 preguntas nuevas en `para_piura_datos.md`.
- `run_all.sh` corre todo. Dos corridas dan el mismo md5.

### Tavily
Créditos de Piura Modelos en la ronda 2: 6 (tavily_search 2 advanced + 2 basic), anotados en `../creditos_tavily.tsv`. No usé tavily_research. Riesgo: sumando lo que anotaron los otros agentes (Piura Datos anotó un research mini en su cota superior de 110, y `suelos/creditos_tavily.tsv` suma 221), el tope de 100 ya está superado. Por eso no gasté más.

**Corrección (ronda 3):** el tope de 100 es por agente, no por equipo. Piura Modelos lleva 6 de 100. La frase anterior sobre el tope superado no aplica.

### No pude
- No hay un dato medido de ECe, drenaje ni pendiente en parcelas agrícolas de Piura. Son 3 de las 4 features que más mueven el resultado.
- El mango sigue sin Kc ni etapas.
- No usé un umbral de calor fisiológico porque no encontré uno verificado para Piura.

## Ronda 3 (24-oct-2026, desde 05:51 UTC)

- Cargador con lint del CONTRATO (`scripts/cargar_evidencia.py`): 0 errores, 5375 avisos (5261 unidades fuera de la lista, 62 claves con cifras distintas, 51 cifras sin rango ni explicación, 1 rendimiento o precio sin zona). Probado con 6 errores inyectados; detecta los 6.
- Las 6 objeciones de Piura Datos atendidas (`respuesta_revision.md`): GroupKFold con referencia zona-año, ALGODON genérico, camote por zona `n_bajo`, APEAR y dotación asignada, etiquetas sin "medido", precios en soles de 2018 con IPC BCRP.
- El FEN pasó de feature a escenario (normal, tipo 2017, tipo 2023). Ranking y top-1/top-3 por escenario.
- `ranking_features.csv` por feature, cultivo, zona y escenario, con cambio de top-1, top-3 y viabilidad (6175 líneas).
- Estabilidad (`scripts/estabilidad.py`): 20 semillas y 6 variantes de rangos. Puestos 2-3 (drenaje, pendiente) robustos en todas las zonas; la ECe es 1.ª con el rango base pero depende de ese rango.
- Mango: Kc y etapas análogas de Petrolina (Silva Junior et al. 2023), riego neto contra dotación y días calientes en floración.
- Hallazgo: Chira, Medio Piura y San Lorenzo comparten celda MERRA-2 en POWER (3 climas para 5 zonas).
- Revisé `evidencia_observada.csv`, `respuestas_a_modelos.md` y `revision_de_modelos.md` al empezar y a mitad de ronda: sin cambios desde las 05:52.
- `run_all.sh` actualizado con `cargar_evidencia.py` y `estabilidad.py`.

### Tavily
Ronda 3: 0 créditos. Total de Piura Modelos: 6 de 100 (`../creditos_tavily.tsv`).

### No pude
- ECe, drenaje y pendiente siguen sin dato agrícola de Piura.
- El FEN no tiene daño por inundación en el modelo.
- No verifiqué el corte de la cosecha del algodón entre años calendario.
- Umbral de calor del mango fuera de la floración: desconocido. Kc del mango Kent/Edward de Piura: no encontrado.

## Ronda 4 (24-oct-2026, desde 06:12 UTC)

- Clima por zona (`scripts/descargar_clima_zona.py`, selector `CLIMA` en `scripts/clima_fuente.py`): ERA5-Land + ERA5 en la costa, CHIRPS solo para la lluvia de Alto y San Lorenzo. Chequeo con Miraflores mar-2017 (506.3 mm): ERA5 +23 %, POWER -33 %, CHIRPS -96 %. Serie hasta 2025: con 2024 cortado el algodón sembrado en 2024 quedaba sin clima y la importancia salía NaN.
- Riego neto con clima por zona 16-31 % menor que con POWER. Skill LOYO del clima: mediana -2.5 % (POWER -6.7 %), sigue sin ser positivo.
- ECe, drenaje y pendiente por zona con fuente (DelaTorre 1986 ILRI, Banco Mundial 1979, Territorio). La CE de campo de Piura Datos entra solo como alternativa de estabilidad: el extracto no está confirmado y no es ECe.
- Inundación FEN en `fen_2017` para Chira, Medio y Bajo (cota inferior). Alto, San Lorenzo y 2023 marcados NO MODELADO.
- Intervalo con W = CV/√n. Algodón Bajo 3.09 t/ha sin 2015 (verificado: 3.0897 ponderado, n=69 distrito-año en mi mapeo frente a 82 de Piura Datos). Frijol costero marcado: la leguminosa costera es caupí.
- Etiqueta ICEN corregida (2016-17 moderado 1.31, 2022-23 fuerte 2.11). El modelo ya usaba esas campañas; cambia el texto del ranking.
- `cargar_evidencia.py` lee la columna `zona` nueva. Sin ese arreglo el rendimiento de Piura Datos se perdía (0 filas) y el camote de Medio y San Lorenzo caía al regional.
- Ranking: drenaje 1.º, pendiente 2.ª, costo 3.º, ECe 4.ª (1.ª solo en Bajo Piura). Estabilidad: 102 de 175 posiciones robustas.
- Reproducibilidad: dos corridas limpias (copia sin `.venv`, venv nuevo). 45 de 45 md5 iguales entre ellas. El árbol principal difería en 2 archivos de evidencia porque Piura Datos cambió `evidencia_observada.csv` a las 07:01 (+1 fila ce_suelo); tras rehacer `cargar_evidencia.py`, 45 de 45.
- CEw (pedido del coordinador): mi modelo propio (`scripts/modelo.py`) la ignora; el motor consolidado no (corrección r5). Si falta no bloquea, no usa valor por defecto y no ensancha el intervalo. Con max(ECe, 1.5·CEw) queda 2.ª feature en media (Medio 36.5, San Lorenzo 44.8; Chira 7.0, o 0 con 0.373-1.167; Alto 0). No entra al ranking oficial: rangos estimados y Bajo sin dato. `resultados.md` R4.6.
- Revisión cruzada de Piura Datos (interrogate sin subagentes: dos pasadas propias separadas). 11 objeciones en `para_piura_datos.md`. La principal: `suelos/datos/clima/raw/PISCOp_monthly.nc` está en la caja y valida mejor que CHIRPS (sesgo costa +29.8 % frente a -36.7 %; MAM -82.6 % en CHIRPS).

### Tavily
Ronda 4: 5 créditos (4 search basic, 1 extract fallido). Total de Piura Modelos: 11 de 100. Registrado en `../creditos_tavily.tsv`.

### No pude
- Pendiente medida fuera de Bajo Piura.
- Validar CHIRPS en Alto y San Lorenzo contra estación. Corrección: no encontré series diarias, pero hay PISCOp v2.1 mensual en la caja (`suelos/datos/clima/raw/PISCOp_monthly.nc`, Territorio). Lo vi tarde. Contra las normales SENAMHI 1971-2000, CHIRPS en Chulucanas y Morropón da -33 % y -4 %, PISCOp +17 % y +30 %. Cambiar la lluvia a PISCOp queda para la ronda 5.
- Modelar sodicidad (PSI 7.3-17.7 en Tablazo Sur).
- Inundación en Alto, San Lorenzo y 2023.
- Separar si el ascenso del camote viene del clima o de la ECe.

## Ronda 5 (24-oct-2026, desde 07:23 UTC)

- ECe sin HWSD. Verificado que `modelo.py` y `params/zonas.csv` no lo usan. Chira, Medio, Alto y San Lorenzo con rango hipótesis 0.5-2-12; Bajo 1.2-4-12. HWSD y la CE de campo quedan como alternativas de estabilidad.
- Pendiente del DEM (`pendiente_por_zona.csv`) y napa de `profundidad_ph_por_zona.csv`.
- Lluvia PISCOp v2.1 por zona, 2020-2025 por mapeo de cuantiles desde POWER. No cambia el top-4 de ninguna zona frente a r4, CHIRPS o POWER.
- Corrección. "El motor ignora la CEw" valía para mi modelo, no para el motor consolidado, que usa max(ECe, 1.5·CEw) con napa ≥ 2 m. Medido contra el motor (R5.1, R5.7). CEw tratada como escenario, no como dato.
- Variantes de CEw a-d en mi modelo y en el motor (R5.2). Recomendación en `esquema_modelo.md`: b2 si la CEw se conoce, nunca bloquear en silencio (c), escenario marcado por fuente de agua, solo estiaje. d1sd sustituye a d1s y deja fuera las 4 lecturas ANA 2024 en disputa, como el motor.
- `cew_por_zona.csv` cambió a las 07:55-07:57 (variable única `ce_agua_riego`, origen en `fuente_agua`, máximos de río publicados como estimado). Lectores adaptados; versión usada md5 248a862a.
- El motor cambió a las 07:53 (PISCOt; entran arveja, frijol grano y cebolla). Todo R5.1 y R5.7 recorrido de nuevo: top-1 caupí, arveja en San Lorenzo.
- Ranking: ECe 1.ª en Sobol (14 de 30 celdas), drenaje 2.º. Estabilidad 116 de 175 posiciones robustas (r4: 102). El ascenso del camote venía de la ECe, no del clima.
- Tabla final por cultivo y zona contra el motor, quitando cada dato (`experimentos/motor_tabla_final.md`, al final de `resultados.md`).

- Rendimientos atípicos (R6-1, regla A4 factor 1,5 aceptada). `validacion.py` con `ATIPICOS=crudo|sin_rescate|con_rescate`; de las 19 rescatadas, 1 cae en mis zonas (maíz Yamango 2019) y la diferencia de skill es ≤ 1.04 puntos (`resultados/validacion_atipicos_comparacion.csv`).
- Validación de PISCOp (R6-4): cota baja en la sierra (fuera de mis zonas) y sesgo de febrero documentado para la lluvia del motor.

### Tavily
Ronda 5: 0 créditos. Total de Piura Modelos: 11 de 100 (`../creditos_tavily.tsv`).

### No pude
- ECe medida en Chira, Medio, Alto y San Lorenzo. Sin ella el motor no recomienda nada en esas 4 zonas.
- CEw de canal en Medio, Bajo y Alto; ninguna CEw de avenida.
- Resolver la unidad de las 4 lecturas ANA 2024 en disputa. Lo dejé como sensibilidad (d1 frente a d1sd).
- Que la CEw de zona llegue sola al motor. `consolidado/motor/datos_repo/cew_por_zona.csv` trae los nombres viejos; recopiarla le toca al dueño del motor.
- Usar `restricciones/lluvia_zona_pisco.csv` (mediana sin El Niño, escenarios El Niño aparte; ICEN agosto 2026 3,98). Llegó al final de la ronda; mi lluvia sale de PISCOp en bruto. Queda para la ronda 6.
- Modelar sodicidad e inundación en Alto, San Lorenzo y 2023.

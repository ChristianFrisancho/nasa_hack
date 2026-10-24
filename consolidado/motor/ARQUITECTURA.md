# Motor de rotación v1: arquitectura (v0 + rondas 2 a 6)

## Problema
Dada una parcela de Piura, el cultivo anterior y un escenario climático, decir qué cultivos son viables, por qué se descartan los demás, cuánta agua y nutrientes pide cada uno, qué deja en el suelo y qué dato falta. Cada cifra lleva rango, unidad, fuente y `tipo_evidencia` (CONTRATO.md). Un dato ausente nunca se convierte en una cifra exacta.

## Uso (lo que ve quien llama)
```python
from motor_rotacion import Consulta, evaluar, comparar_secuencias
r = evaluar(Consulta.desde_dict(json))          # Resultado
s = comparar_secuencias(consulta, largo=3)       # lista de Secuencia
texto = r.a_texto(); datos = r.a_dict()
```
CLI: `python -m motor_rotacion ejemplos/bajo_piura_salino.json --formato texto --secuencias 2`

## Tipos centrales
- `Cifra`: valor, valor_min, valor_max, unidad, fuente, url_o_doi, tipo_evidencia, estado, notas. La aritmética de intervalos vive aquí. Si una entrada es `desconocido`, el resultado también lo es y `notas` dice cuál faltó.
- `Consulta`: parcela (punto o polígono, área, provincia), suelo (ECe, pH, profundidad, drenaje, pendiente: cada uno número, rango `[a, b]` o ausente), agua (m³ por mes, ECw, eficiencia, intervalo de turno), presupuesto, cultivo anterior, plagas presentes, escenario, mes de siembra, horizonte.
- `Ficha`: todo lo que el motor sabe de un cultivo (familia, módulo anual/perenne, Kc, etapas, umbrales de salinidad, pH, profundidad, temperaturas, NPK por t, rendimiento, precio, costo). La arma `Catalogo` desde CSV.
- `Veredicto`: filtro, resultado (`pasa`, `advierte`, `descarta`, `no_evaluable`), motivo, cifras, faltantes.
- `EvaluacionCultivo`: decisión, veredictos, duración, agua por etapa y por mes, nutrientes, rendimiento, costo, margen, lo que deja en el suelo y los datos que faltan.
- `EstadoSuelo`: ECe, balances acumulados de N, P2O5 y K2O, agua aplicada e historial. `actualizar_tras_cosecha` devuelve uno nuevo.

## Módulos
| módulo | dueño de |
|---|---|
| `cifra.py` | tipo Cifra e intervalos |
| `catalogo.py` | leer `datos_repo/`, `datos_motor/` y CSV con formato contrato de los otros bots (`integrar_csv_contrato`) |
| `clima.py` | zona NASA POWER más cercana y clima mensual p10-p90 por escenario |
| `entradas.py` | Consulta desde JSON |
| `agua.py` | FAO-56: curva de Kc diaria × ET0 mensual, lluvia, riego neto/bruto |
| `nutrientes.py` | absorción, exportación y residuo por rendimiento |
| `filtros.py` | filtros duros en una sola tupla ordenada `FILTROS_ANUALES` / `FILTROS_PERENNES` |
| `estado_suelo.py` | estado y actualización tras cosecha |
| `motor.py` | `evaluar`, `comparar_secuencias`, ranking |
| `perennes.py` | evaluación de instalación de perennes, aparte de la rotación |
| `reporte.py` | texto legible y JSON |
| `validacion.py` | reglas de CONTRATO.md por fila (zonas, unidades, métodos especiales) y registro aceptada/rechazada/ignorada |
| `reglas.py` | reglas de Piura Agronomía (arroz y drenaje, FEN, algodón, rastrojo) |
| `calendario_obs.py` | ventanas observadas DRAP 2016-2024 por cultivo y zona |
| `incertidumbre.py` | Monte Carlo del margen (P10/P50/P90, P(margen<0)) |

## Bocetos considerados
**A. Tubería de funciones sobre diccionarios.** Cada paso recibe y devuelve un dict (`cargar → filtrar → balancear → rankear`). Poco código, pero cada paso conoce la forma interna de los demás (fuga de información) y la fuente/rango de cada cifra se pierde fácil en un dict suelto.

**B. Núcleo tipado con módulo profundo `motor`.** `Cifra` es la única forma de transportar un número; los filtros son funciones puras `(Contexto) -> Veredicto` registradas en una tupla; `motor.evaluar` es la única puerta. Más tipos, pero la trazabilidad la impone la estructura y no la disciplina.

**Decisión: B.** La exigencia central del encargo (cada cifra con fuente, rango y estado) se cumple por construcción. Se evitaron: lista de filtros sincronizada a mano en dos lugares (una tupla por módulo), dos formas de representar un número (solo `Cifra`), y que el CLI conozca internals (solo llama `evaluar` y `comparar_secuencias`).

## Compromisos
- Clima mensual, no diario: suficiente para v0; el diario está en los JSON de POWER.
- La lluvia efectiva se trata como rango [0, lluvia total]; por eso el riego neto sale como intervalo ancho y honesto.
- El ranking es lexicográfico y explicable (advertencias, cambio de familia, margen, agua), no un óptimo.

## Preguntas abiertas
- Lista definitiva de años ENSO (Piura Territorio).
- Umbrales de salinidad para arveja, yuca, frijol de palo, mango, banano, papaya.
- Duración y calendario de siembra locales por campaña (INIA/DRAP).
- Pérdidas por percolación en arroz y eficiencia de riego por sistema.

## Cambios durante la implementación
- Tercera decisión `sin_datos`: si 2 o más filtros críticos (salinidad, agua, calendario) son `no_evaluable`, el cultivo no se descarta pero tampoco entra al ranking ni a las secuencias. Evita recomendar un cultivo solo porque no sabemos nada de él (caso frijol de palo).
- Ranking: total de alertas, luego advertencias reales, luego misma familia que el anterior, margen desconocido, margen medio y agua.
- Secuencias: primero viables, luego las que caben con certeza en el horizonte, luego alertas y margen.
- Faltantes globales agrupados por tipo (`umbral de pH de <cultivo>`, con cuántos cultivos afecta).

## Cambios de la ronda 2 (v1)
- `Veredicto.grave`: «probable no apto». Lo activan la sal no exacta con ECe mín ≥ ECe 50 % y el pH fuera del absoluto sin evidencia local. Ese cultivo no se descarta, porque el umbral no se puede aplicar como exacto, pero va primero en la clave de orden y se lista aparte. Sin este flag, una parcela salina sin napa aceptaba 13 de 14 cultivos como si nada.
- FAO-29 (R4A026): umbral exacto solo con ECe medida en pasta saturada, napa ≥ 2 m, extracto declarado y umbral no de clase. Si no, el filtro avisa y el límite inferior del rendimiento relativo baja un tramo por cada condición que falta.
- `Suelo.ce_metodo` (`pasta_saturada` | `ce_extracto_no_declarado`) y `Suelo.psi_pct`. La CE de extracto no declarado se trata como cota inferior de la ECe. No se inventa un factor de conversión.
- Rampas EcoCrop (`Rampa.aptitud_intervalo`) para pH y profundidad. Profundidad efectiva = mín(física, napa − franja capilar).
- Orden de secuencias: P10 de Monte Carlo redondeado a 100 PEN, con desempate por agua, ECe final, P+K y alertas. Se guardó `clave_secuencia_v0`: el test `test_orden_robusto_no_premia_rangos_anchos` falla si `ordenar_secuencias` vuelve a usarla (comprobado mutando el código).
- Orden de cultivos: graves → pérdida casi segura (P90 < 0) → alertas → familia → P10 → aptitud → agua.
- `integrar_csv_contrato`:
  - valida cada fila con CONTRATO.md, incluidas unidad, `dotacion_asignada`→estimado y `ce_extracto_no_declarado`→observado;
  - acepta `medio_bajo_piura`, que sirve de respaldo para parcelas medio/bajo, y las columnas opcionales `fuente_primaria` y `subzona`;
  - las filas de CE de suelo se ignoran con aviso, porque son de parcela y no de catálogo.
- Las reglas categóricas de Agronomía no pasan por la lista de unidades, que es para cifras. Si pasaran, se rechazarían R4R003/5/6 por unidades «categoría» o «campañas».

## Cambios de la ronda 3

- `motor.completar_con_zona` corre al inicio de `evaluar`. Rellena ECw y pendiente con el valor de zona etiquetado cuando falta el de la parcela. `comparar_secuencias` usa la consulta completada.
- `motor.escenarios_ecw` corre `evaluar` y `comparar_secuencias` por cada ECw de escenario. Devuelve `EscenarioAgua(ecw, etiqueta, resultado, secuencias)`. La CLI lo agrega cuando se piden secuencias y la ECw de la parcela es desconocida.
- `Catalogo` tiene ahora `contexto_zona` (cifras de zona que el motor puede usar como rango) y `contexto_regional` (solo avisos), y lee `perennes.csv`.
- `integrar_csv_contrato` hace cuatro cosas más:
  - mapea `costo_produccion` en PEN/ha;
  - descarta unidades que no son las del motor;
  - amplía los costos análogos;
  - rechaza la ECe de HWSD y reparte `zonas_aplicables`.
- Zonas con códigos de CONTRATO.md en todo el motor. Se quitó `calendario_obs.ZONA_PREFIJO`. El parche de Agronomía (`cultivos/_scratch/parche_calendario_obs_codigos.diff`) se revisó y no se aplicó: tapaba el síntoma y seguía adivinando nombres.

## Cambios de la ronda 4

- `filtros.termica_grave(ctx) -> str`. Devuelve el motivo o "". Se llama al final de `f_calendario`. Si hay motivo, el veredicto queda en `advierte` con `grave=True`, y el orden existente (`n_graves` primero) manda el cultivo al final. No hizo falta un tipo nuevo. Antes, los avisos por mes ("mes 6: Tmáx … alcanza TMAX") se escribían uno por uno y nunca formaban una decisión. Ahora se cuentan los meses del ciclo sin repetir y se comparan con `FRACCION_MESES_TERMICA`.
  - Mes caluroso: `Tmax.lo > TMAX`, todo el rango del escenario sobre el límite.
  - Mes frío: `Tmedia.hi < TMIN`. Se deduce porque Tmín ≤ Tmedia, y el repo no trae Tmín.
  - TMAX es el menor de los umbrales `tmax` absolutos del cultivo. TMIN es el mayor mínimo absoluto de `tmedia`.
- `Consulta.distrito: str | None`. `motor.zona_de_distrito(distrito, provincia) -> (zona | None, origen)` lee `datos_repo/distrito_zona.csv` una vez (`lru_cache`). Compara sin tildes, mayúsculas ni espacios.
  - Devuelve `None` si el distrito no está en la tabla, si está repetido y falta la provincia, o si su zona no está en `validacion.ZONAS_PARCELA`.
  - `zona_parcela` sigue este orden: zona del usuario, zona deducida del distrito, zona climática más cercana. Si el distrito no sirve, el motivo va delante del origen climático.
- Las constantes marcadas `# supuesto del motor` las revisa un test, que exige cada nombre en la tabla «Supuestos del motor» del README. Así un supuesto nuevo no puede quedar sin documentar.
- `test_ecw_desconocida_corre_tres_escenarios_etiquetados` comparaba los tres primeros puestos. Con la regla térmica, los tres primeros (caupí, algodón, yuca) son iguales con agua buena y con agua salina. La prueba ahora pide que el orden completo cambie y que los aceptados con agua salina sean un subconjunto estricto de los aceptados con agua buena. Sigue en pie la prueba de 23 frente a 19 secuencias viables.

## Cambios de la ronda 5

- `catalogo.variables_conocidas()` es la unión de cuatro conjuntos: `VARIABLES_CONTRATO`, `VARIABLES_ZONA`, `VARIABLES_CE_SUELO` y `VARIABLES_NO_USADAS`. `integrar_csv_contrato` rechaza cualquier otro nombre con `motivo_variable_desconocida`. Es la causa del hallazgo de Agronomía sobre los nombres de ECw: antes el nombre desconocido caía en «ignorada». No hay alias: un archivo con otro nombre se convierte fuera del motor, como hace `scripts/extraer_evidencia_r5.py`, que deja el nombre original en `notas`.
- `validacion.validar_fila_contrato` aplica R7 de `validar.py` cuando la fila trae la clave `zonas_aplicables`. `es_generica` copia la lista de fuentes genéricas de `validar.py` (`FUENTES_GENERICAS`).
- `Catalogo._integrar_agua(r)` separa la CEw por `fuente_agua`:
  - canal, reservorio o toma pasan por `_integrar_zona` como valor de zona y la nota lleva el tipo de agua y la estación;
  - río, quebrada o pozo van a `contexto_agua: list[AguaPunto]` y solo dan avisos (`motor.avisos_agua`, cuando falta la ECw de la parcela);
  - `CEW_EN_DISPUTA` con fecha 2024 se rechazaba con `MOTIVO_CEW_EN_DISPUTA` (borrado en la ronda 6).
- Costos: con la misma zona y la misma prioridad de evidencia, `_integrar_zona` arma la envolvente en vez de quedarse con la última fila. `CONFIANZA_BAJA` se eliminó.
- Salinidad de la arveja: `_agro_cultivares_salinidad` lee las cotas por variedad de `fichas_anuales.csv` en `s["cultivares"]`. `f_salinidad` advierte desde el umbral del cultivar menos tolerante y usa el ECe 50 % del más tolerante (`ece50_tolerante`) para el descarte y para «probable no apto».
- Temperatura: `Catalogo.tmax_pisco: dict[(zona, mes), Cifra]` se carga de `datos_repo/temperatura_pisco_zona.csv`. Si una zona trae varias celdas, se guarda la envolvente. `Contexto.tmax_media` recibe los doce meses de la zona de la parcela. `termica_grave` compara `tmax_media[mes].lo` con el TMAX absoluto. No hay vuelta a POWER: sin PISCOt, el mes no cuenta y el dato va a faltantes.

## Cambios de la ronda 6

- `catalogo.ESCENARIOS_ICEN` y `ESCENARIOS_NINO` reemplazan los escenarios viejos, que no eran ICEN, y a `datos_motor/escenarios_enso.csv`. `clima.validar_escenario` es la única puerta: un nombre fuera de la lista da `ValueError` con los tres nombres válidos. `Catalogo.anios_icen[esc]` guarda los años de campaña. `anios_del_mes(campanias, mes)` traduce una campaña a año calendario: Y para enero–julio, Y-1 para agosto–diciembre. `clima.clima_escenario(lat, lon, escenario, anios, …)` elige los años mes por mes.
- `Catalogo._cargar_lluvia_pisco()` llena `lluvia_pisco[(zona, esc, mes)]` y hace dos pasadas: primero toma las campañas de las filas de enero y después valida cada fila contra ellas. En la sierra se guarda la envolvente de las subzonas. `motor.lluvia_de_zona` y `clima.con_lluvia_pisco` cambian la lluvia de POWER por la de PISCOp y marcan `ClimaEscenario.fuente_lluvia`.
- `filtros.exceso_agua(ctx)` devuelve `(motivo, faltantes, pesa)` y reemplaza el bloque viejo de días con lluvia > 20 mm. `f_calendario` no deja que una advertencia tape la falta de duración: si el ciclo anual no tiene duración y el peor resultado es ADVIERTE, el filtro queda en NO_EVALUABLE. `Ficha.anegamiento` viene de `_agro_anegamiento` y solo se cita.
- `motor.evaluar_escenarios(consulta, catalogo) -> EscenariosClima` usa `replace(consulta, escenario=esc)` para cada escenario ICEN. `EscenariosClima.primeros` y `.primer_lugar_cambia` alimentan el texto y el JSON. El CLI lo corre siempre.
- Agua: se borró `CEW_EN_DISPUTA`. Las cuatro lecturas resueltas por Datos pasan por el camino normal de `contexto_agua` (punto, solo aviso). `motor.avisos_agua` nombra las que son estimadas.
- Arveja: `validacion` acepta `temperatura_umbral_estres_reproductivo` en °C. `filtros.floracion_calor` compara el umbral inferior con `Contexto.tmax_media` en `meses_floracion`. `UNIDADES_CONTRATO = unidades_de_contrato(CONTRATO.md)` lee la lista de CONTRATO.md, así que ya no hay una copia que se pueda desfasar.

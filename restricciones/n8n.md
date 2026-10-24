# Flujos n8n del sistema Piura (versión final, ronda 7)

Instancia: moraprix.app.n8n.cloud, proyecto personal aK2Uwj9OYONBsCPo. Revisado por última vez el 2026-10-24 a las 08:18 UTC con get_workflow_details: los tres flujos siguen con los mismos versionId y `updatedAt` que en la ronda 4 (03:17, 02:42 y el borrador sin publicar). En la ronda 7 no edité, dupliqué, activé, publiqué ni programé ninguno. Primera revisión: 2026-10-24 entre las 07:00 y las 07:10 UTC. Los dos flujos activos los leí y no los toqué: su `updatedAt` sigue en 03:17 y 02:42 UTC. Hay copias en `respaldo/n8n/`.

## 1. "Piura | Investigacion Tavily automatizada" (4TeSMeSTACXljaBk), activo
- versionId anotado para restaurar: 323ed9d6-b2f6-44a9-9858-106115183d07.
- Qué hace: el nodo manual "Investigar Piura ahora" o el horario "Actualizar lunes 07 Lima" arrancan el flujo. "Plan de busquedas Piura" (Code) arma las consultas. "Tavily buscar y extraer fuentes" (HTTP POST a api.tavily.com/search, credencial httpHeaderAuth) busca y extrae. "Normalizar evidencias sin inventar valores" (Code) da forma a lo que vuelve. "Guardar investigacion sin duplicados" hace upsert por `record_key` en la tabla Piura_agro_evidencia (SW9ZbPKCuDmDufK4).
- Entradas: el plan de consultas que está escrito dentro del nodo Code.
- Salidas: filas `record_type=fuente_descubierta` con `quality_status=texto_extraido_pendiente_validacion` y el texto en `payload_json`. No son filas del CONTRATO.
- Costo: cada corrida gasta créditos Tavily de la cuenta de Christian. No lo ejecuté.
- Últimas ejecuciones: la 7 y la 8, ambas correctas (02:55 y 03:17 UTC, manuales).

## 2. "Piura | Fuentes oficiales y clima NASA" (FZuImrDNKPsFj306), activo
- versionId anotado: 1bac625e-2b8e-43b7-9b31-36b8a81b769c.
- Qué hace: los disparadores son "Descarga inicial" (manual) y "Actualizar diario 06 Lima". Tiene tres ramas y las tres terminan en upsert a SW9ZbPKCuDmDufK4:
  - puntos y periodo → NASA POWER diario (HTTP sin credencial) → normalizar clima → guardar;
  - archivo SENASA paginado (API de WordPress) → normalizar documentos → guardar;
  - catálogo de mapas SIAR → extraer mapas → guardar.
- Salidas: filas de clima diario por punto (`power:<lat>:<lon>:<fecha>`), documentos SENASA y catálogo SIAR. Los puntos son regionales, no parcelas.
- Últimas ejecuciones: 2, 3, 5 y 6 correctas. La 4 terminó en error (02:38 UTC) y los metadatos no dicen la causa.

## 3. "Piura | Control de calidad evidencia" (l1rsZ0v2EsjlbDjm), NUEVO, borrador inactivo
- Creado en esta ronda con create_workflow_from_code, después de get_workflow_sdk_reference, get_workflow_best_practices (data_transformation), get_node_types y validate_workflow (resultado: valid, 6 nodos). No está publicado ni activado (`active=false`). No lleva credenciales ni nodos de pago.
- Nodos:
  1. "Recibir filas por webhook" (POST, ruta `piura-control-calidad-evidencia`, responde con el último nodo) → "Extraer filas del webhook" (Code). Acepta `{rows:[...]}`, `{filas:[...]}`, un arreglo o una fila suelta.
  2. "Revisar tabla n8n (manual)" → "Leer Piura_agro_evidencia (solo lectura)". Es un Data Table `get` con límite de 200 filas; lee, no escribe. Luego "Mapear tabla n8n a filas CONTRATO" (Code) usa `payload_json` si trae columnas del CONTRATO y, si no, pasa la fila tal cual.
  3. Las dos ramas desembocan en "Validar CONTRATO y resumir" (Code, una sola pasada sobre todas las filas). Es espejo de `tools/limpiar.py`, pero acumula los errores en vez de abortar en el primero.
- Qué revisa:
  - columnas del CONTRATO presentes y campos obligatorios no vacíos;
  - unidad dentro de la lista del CONTRATO;
  - estado y tipo_evidencia válidos;
  - valores numéricos;
  - `desconocido` sin cifra, y si hay cifra que haya valor o rango completo;
  - min ≤ valor ≤ max, y "rango" en notas cuando falta el rango;
  - zona permitida, y "Zona no aplica:" si va vacía;
  - dotación con estimado + dotacion_asignada;
  - CE de suelo con extracto declarado o `ce_extracto_no_declarado`;
  - analogo_externo con "Comparabilidad:";
  - deduplicación por `id_registro`. Si falta el id, usa la misma clave de texto que limpiar.py usa para el hash. Distingue duplicados idénticos de duplicados con cifras distintas.
- Salida: un ítem con `filas_recibidas`, `filas_validas`, `filas_con_error`, `ids_unicos`, `duplicados`, `duplicados_con_cifras_distintas`, `errores_por_regla`, `primeros_errores` (hasta 200) y `pasa`.
- Pruebas reales:
  - Ejecución 9, rama webhook, con pin data de 5 filas sintéticas: 1 válida, una con unidad µS/cm, una desconocido con cifra fuera de rango, una dotación mal marcada con zona inválida y un duplicado de la primera con otra cifra. Resultado `success`: 1 válida, 4 con error y las 6 reglas esperadas marcadas, es decir unidad_no_permitida, desconocido_con_cifra, valor_sobre_max, zona_invalida, dotacion_mal_marcada y duplicado_con_cifras_distintas. `pasa=false`, que es lo correcto.
  - Ejecución 10, rama manual, leyendo de verdad 200 filas de la tabla: `success`, 0 de 200 válidas, porque todas tienen columnas_faltantes. Es el resultado esperado: la tabla cruda no tiene el esquema del CONTRATO (limpiar.py ya la ignora por eso) y sus cifras útiles sólo entran curadas.
  - En local, con Node 20 y el mismo código (`n8n/validar_contrato.js`), las 11238 filas de `evidencia_observada.csv` dieron 11238 válidas (ronda 4; en la ronda 7, con 11288 filas, da 11288 válidas, 0 errores, 0 duplicados y `pasa=true`, y `tools/run_all.sh` lo corre al final de cada regeneración), 0 duplicados y `pasa=true`. El flujo coincide con limpiar.py.
- Cómo reproducir:
  - El código fuente está en `restricciones/n8n/` (`control_calidad_sdk.ts`, `extraer_webhook.js`, `mapear_tabla.js`, `validar_contrato.js`, `pin_malas.json`, `pin_buenas.json`).
  - Prueba local: `node n8n/harness.js filas.json`, donde filas.json es un arreglo de filas; el arnés emula `$input.all()`.
  - En n8n: test_workflow con pin data en "Recibir filas por webhook", del tipo `[{json:{body:{rows:[...]}}}]`.
  - Para usar el webhook de producción haría falta publicar el flujo. NO se publicó; sólo funciona en modo prueba desde el editor.

## Qué parte del pipeline hace cada flujo y cuál no
| Flujo | Hace | No hace |
|---|---|---|
| 4TeSMeSTACXljaBk Tavily | Descubre fuentes y guarda su texto crudo en la tabla n8n | No produce filas del CONTRATO ni lee cifras; todo lo que trae pasa por curado manual (`insumos_curados_*.py`) antes de entrar |
| FZuImrDNKPsFj306 NASA/SENASA/SIAR | Baja clima diario NASA POWER en 5 puntos, documentos SENASA y el catálogo SIAR | No calcula las temperaturas por zona (eso lo hace `tools/temperatura_power.py` con su caché propio) ni produce filas del CONTRATO |
| l1rsZ0v2EsjlbDjm Control de calidad | Valida filas contra los 19 campos y las reglas principales del CONTRATO (mismo código que el arnés local) | No escribe nada, no corrige filas, no corre el pipeline |

La fuente de verdad es el pipeline Python (`tools/run_all.sh` → `evidencia_observada.csv`). La exportación de la tabla n8n entra sólo como `insumos/evidencia_n8n.csv`, que `limpiar.py` ignora porque no tiene el esquema del CONTRATO; sus cifras útiles entraron curadas en `insumos/n8n_curado.csv`.

## Entradas, salidas y cómo correrlos a mano
- **Tavily (4TeS…)**: entrada, el plan de consultas escrito en el nodo Code; salida, filas `fuente_descubierta` en SW9ZbPKCuDmDufK4. A mano: abrir el flujo en el editor y pulsar "Investigar Piura ahora". Gasta créditos Tavily de la cuenta de Christian en cada corrida, así que no lo corrí.
- **NASA/SENASA/SIAR (FZuI…)**: entrada, la lista de puntos y el periodo en su nodo inicial; salida, filas `power:<lat>:<lon>:<fecha>`, documentos y mapas en la misma tabla. A mano: "Descarga inicial" en el editor. No usa credenciales de pago.
- **Control de calidad (l1rs…)**: entrada, filas por webhook de prueba (`https://moraprix.app.n8n.cloud/webhook-test/piura-control-calidad-evidencia`, sólo con el editor abierto) o las 200 primeras filas de la tabla (rama manual "Revisar tabla n8n (manual)"); salida, un resumen JSON (`filas_validas`, `errores_por_regla`, `pasa`). A mano sin n8n: `node n8n/harness.js filas.json`.

## Limitaciones conocidas del validador (ronda 7)
- Sólo exige los 19 campos base. Las columnas opcionales (`fuente_primaria`, `subzona` y `rescatado_por_serie`) pasan sin revisar: no rechaza columnas extra.
- No aplica la regla A4 de `rescatado_por_serie` (estimado y serie en notas); esa regla sólo está en `limpiar.py` y en `test_limpiar.py`. `rescatado_por_serie` no está en CONTRATO.md: es opcional y queda pendiente de aprobación.
- La lista de unidades está fija en el código; si el CONTRATO cambia, hay que copiarla a `n8n/validar_contrato.js` y al nodo.

## Análisis de impacto (antes de crear)
- Los dos flujos activos escriben en la misma tabla, SW9ZbPKCuDmDufK4, por upsert. Un flujo nuevo que escribiera ahí podría pisar `record_key` o mezclar esquemas. Por eso el nuevo sólo lee esa tabla (límite de 200) y no escribe en ninguna.
- El flujo Tavily gasta créditos de pago con credencial. El nuevo no usa HTTP, credenciales ni nodos de IA, así que su costo es cero salvo la ejecución de n8n misma, que en modo prueba no consume ejecuciones de producción.
- No edité, dupliqué ni reactivé los flujos existentes. Para restaurarlos están los versionId de arriba y los JSON de `respaldo/n8n/`.
- Riesgo pendiente: si alguien publica el flujo nuevo, el webhook quedaría público sin autenticación (opción por defecto de n8n). Antes de publicarlo convendría poner headerAuth, y eso requiere que Christian cree una credencial.

## Análisis de impacto (ronda 7)
- Cambios en n8n esta ronda: ninguno. Sólo lecturas (get_workflow_details) y el arnés local, que no toca la instancia.
- Los dos flujos activos siguen programados (lunes 07 y diario 06, hora de Lima) desde antes de mi trabajo. No los desactivo porque la regla es no tocar flujos activos; el de Tavily seguirá gastando créditos cada lunes. Si Christian quiere cortar ese gasto, tendría que desactivarlo él (versionId 323ed9d6-… para restaurar).
- Si alguien cambia el CONTRATO (por ejemplo, para aprobar `rescatado_por_serie`), lo único que se rompe en n8n es la lista fija del validador. Para actualizarlo convendría crear una versión nueva del borrador, no editar los activos.

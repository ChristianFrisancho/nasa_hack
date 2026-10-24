import { workflow, node, trigger } from '@n8n/workflow-sdk';

const webhookEntrada = trigger({
  type: 'n8n-nodes-base.webhook', version: 2.1,
  config: {
    name: 'Recibir filas por webhook',
    parameters: { httpMethod: 'POST', path: 'piura-control-calidad-evidencia', responseMode: 'lastNode', options: {} },
    position: [240, 200]
  },
  output: [{ body: { rows: [{ variable: 'ce_agua_riego', valor: '0.77', unidad: 'dS/m', zona: 'chira' }] } }]
});

const extraerWebhook = node({
  type: 'n8n-nodes-base.code', version: 2,
  config: { name: 'Extraer filas del webhook', parameters: { mode: 'runOnceForAllItems', jsCode: "// Code node \"Extraer filas del webhook\": acepta {rows:[...]}, {body:{rows:[...]}}, un arreglo o una fila suelta.\nconst salida = [];\n$input.all().forEach(function (it) {\n  const j = it.json || {};\n  const b = j.body !== undefined ? j.body : j;\n  const filas = Array.isArray(b) ? b : (Array.isArray(b.rows) ? b.rows : (Array.isArray(b.filas) ? b.filas : (b.variable !== undefined ? [b] : [])));\n  filas.forEach(function (r) { const o = Object.assign({}, r); o._origen = 'webhook'; salida.push({ json: o }); });\n});\nreturn salida.length ? salida : [{ json: { _sin_filas: true, _origen: 'webhook' } }];\n" }, position: [520, 200] },
  output: [{ variable: 'ce_agua_riego', _origen: 'webhook' }]
});

const manualEntrada = trigger({
  type: 'n8n-nodes-base.manualTrigger', version: 1,
  config: { name: 'Revisar tabla n8n (manual)', position: [240, 460] },
  output: [{}]
});

const leerTabla = node({
  type: 'n8n-nodes-base.dataTable', version: 1.1,
  config: {
    name: 'Leer Piura_agro_evidencia (solo lectura)',
    parameters: {
      resource: 'row', operation: 'get',
      dataTableId: { __rl: true, mode: 'id', value: 'SW9ZbPKCuDmDufK4' },
      returnAll: false, limit: 200
    },
    position: [520, 460]
  },
  output: [{ record_key: 'k1', record_type: 'clima', payload_json: '{}' }]
});

const mapearTabla = node({
  type: 'n8n-nodes-base.code', version: 2,
  config: { name: 'Mapear tabla n8n a filas CONTRATO', parameters: { mode: 'runOnceForAllItems', jsCode: "// Code node \"Mapear tabla n8n a filas CONTRATO\": la tabla Piura_agro_evidencia guarda payload_json; si el payload trae columnas\n// del CONTRATO se usan; si no, la fila pasa tal cual y el validador la marca (columnas_faltantes). No inventa valores.\nconst salida = [];\n$input.all().forEach(function (it) {\n  const j = it.json || {};\n  let p = {};\n  try { p = JSON.parse(j.payload_json || '{}'); } catch (e) { p = {}; }\n  const fila = (p && typeof p === 'object' && p.variable !== undefined) ? Object.assign({}, p) : { record_type: j.record_type, topic: j.topic, source_url: j.source_url };\n  if (!fila.id_registro) fila.id_registro = j.record_key || String(j.id);\n  fila._origen = 'tabla_n8n:SW9ZbPKCuDmDufK4';\n  salida.push({ json: fila });\n});\nreturn salida.length ? salida : [{ json: { _sin_filas: true, _origen: 'tabla_n8n:SW9ZbPKCuDmDufK4' } }];\n" }, position: [800, 460] },
  output: [{ id_registro: 'k1', _origen: 'tabla_n8n' }]
});

const validar = node({
  type: 'n8n-nodes-base.code', version: 2,
  config: { name: 'Validar CONTRATO y resumir', parameters: { mode: 'runOnceForAllItems', jsCode: "// Code node \"Validar CONTRATO y resumir\" (Run Once for All Items). Espejo de tools/limpiar.py, pero acumula errores en vez de abortar.\nconst CAMPOS = ['variable','valor','valor_min','valor_max','unidad','cultivo','variedad','etapa','zona','lugar','lat','lon','fecha_o_periodo','fuente','url_o_doi','metodo','tipo_evidencia','estado','notas'];\nconst OBLIG = ['variable','unidad','cultivo','lugar','fecha_o_periodo','fuente','url_o_doi','metodo','tipo_evidencia','estado','notas'];\nconst UNIDADES = ['mm','mm/día','kg/ha','t/ha','dS/m','cmol/kg','%','°C','días','ha','PEN/ha','PEN/kg','PEN/t','PEN/m3','USD/ha','m3/ha','m3/ha/año','hm3'];\nconst ESTADOS = ['observado','estimado','desconocido'];\nconst TIPOS = ['medicion_local','regional','bibliografico','analogo_externo','prediccion'];\nconst ZONAS = ['alto_piura','medio_piura','bajo_piura','chira','san_lorenzo','sierra_piura','medio_bajo_piura','piura_region'];\nconst DOTACION = /^(dotacion|modulo_riego|volumen_asignado|volumen_licencia)/;\nconst CE_SUELO = /^(ce_suelo|ece)/i;\nconst EXTRACTO = /pasta saturada|extracto de saturaci|1:1|1:2[.,]5|1:5/i;\nconst NO_DECLARA = /no declar|sin declarar|extracto desconocido/i;\nconst s = function (x) { return x === null || x === undefined ? '' : String(x).trim(); };\nconst num = function (x) { const t = s(x); if (t === '') return null; const n = Number(t); return Number.isFinite(n) ? n : NaN; };\nconst filas = $input.all().map(function (it) { return it.json; }).filter(function (r) { return r && !r._sin_filas; });\nconst errores = []; const porRegla = {}; const vistos = {}; let validas = 0; let nErr = 0; let duplicadas = 0; let conflictos = 0;\nconst marca = function (i, id, regla, detalle) { nErr += 1; porRegla[regla] = (porRegla[regla] || 0) + 1; if (errores.length < 200) errores.push({ fila: i + 1, id_registro: id, regla: regla, detalle: detalle }); };\nfilas.forEach(function (r, i) {\n  const clave = ['variable','cultivo','variedad','etapa','lugar','fecha_o_periodo','unidad','fuente'].map(function (c) { return s(r[c]); }).join('|');\n  const id = s(r.id_registro) || clave;\n  const n0 = nErr;\n  const faltan = CAMPOS.filter(function (c) { return !(c in r); });\n  if (faltan.length) marca(i, id, 'columnas_faltantes', faltan.join(','));\n  OBLIG.forEach(function (c) { if (s(r[c]) === '') marca(i, id, 'obligatorio_vacio', c); });\n  if (s(r.unidad) && UNIDADES.indexOf(s(r.unidad)) < 0) marca(i, id, 'unidad_no_permitida', s(r.unidad));\n  if (s(r.estado) && ESTADOS.indexOf(s(r.estado)) < 0) marca(i, id, 'estado_invalido', s(r.estado));\n  if (s(r.tipo_evidencia) && TIPOS.indexOf(s(r.tipo_evidencia)) < 0) marca(i, id, 'tipo_evidencia_invalido', s(r.tipo_evidencia));\n  const v = num(r.valor), lo = num(r.valor_min), hi = num(r.valor_max);\n  [['valor', v], ['valor_min', lo], ['valor_max', hi], ['lat', num(r.lat)], ['lon', num(r.lon)]].forEach(function (p) { if (Number.isNaN(p[1])) marca(i, id, 'no_numerico', p[0] + '=' + s(r[p[0]])); });\n  const ok = function (x) { return x !== null && !Number.isNaN(x); };\n  if (s(r.estado) === 'desconocido' && (ok(v) || ok(lo) || ok(hi))) marca(i, id, 'desconocido_con_cifra', 'valor/min/max deben ir vacíos');\n  if (s(r.estado) && s(r.estado) !== 'desconocido' && !ok(v) && !(ok(lo) && ok(hi))) marca(i, id, 'cifra_faltante', 'sin valor ni rango completo');\n  if (ok(lo) && ok(hi) && lo > hi) marca(i, id, 'min_mayor_que_max', lo + ' > ' + hi);\n  if (ok(v) && ok(lo) && v < lo) marca(i, id, 'valor_bajo_min', v + ' < ' + lo);\n  if (ok(v) && ok(hi) && v > hi) marca(i, id, 'valor_sobre_max', v + ' > ' + hi);\n  if (ok(v) && !ok(lo) && !ok(hi) && s(r.notas).toLowerCase().indexOf('rango') < 0) marca(i, id, 'sin_rango_sin_explicacion', 'notas debe explicar la falta de rango');\n  const z = s(r.zona);\n  if (z && ZONAS.indexOf(z) < 0) marca(i, id, 'zona_invalida', z);\n  if (!z && s(r.notas).indexOf('Zona no aplica:') < 0) marca(i, id, 'zona_vacia_sin_explicacion', 'falta \"Zona no aplica:\"');\n  if (DOTACION.test(s(r.variable)) && (s(r.estado) !== 'estimado' || s(r.metodo) !== 'dotacion_asignada')) marca(i, id, 'dotacion_mal_marcada', 'estado=estimado y metodo=dotacion_asignada');\n  if (CE_SUELO.test(s(r.variable))) {\n    const declara = EXTRACTO.test(s(r.metodo)) && !NO_DECLARA.test(s(r.metodo));\n    if (s(r.metodo) !== 'ce_extracto_no_declarado' && !declara) marca(i, id, 'ce_sin_extracto', 'declarar extracto o usar ce_extracto_no_declarado');\n    if (s(r.metodo) === 'ce_extracto_no_declarado' && s(r.estado) !== 'observado') marca(i, id, 'ce_estado', 'ce_extracto_no_declarado va con observado');\n  }\n  if (s(r.tipo_evidencia) === 'analogo_externo' && s(r.notas).indexOf('Comparabilidad:') < 0) marca(i, id, 'analogo_sin_comparabilidad', 'falta \"Comparabilidad:\"');\n  const huella = [s(r.valor), s(r.valor_min), s(r.valor_max)].join('|');\n  if (id in vistos) { duplicadas += 1; if (vistos[id] !== huella) { conflictos += 1; marca(i, id, 'duplicado_con_cifras_distintas', vistos[id] + ' vs ' + huella); } }\n  else vistos[id] = huella;\n  if (nErr === n0) validas += 1;\n});\nconst fuente = filas.length && filas[0]._origen ? filas[0]._origen : 'webhook';\nreturn [{ json: {\n  origen: fuente, filas_recibidas: filas.length, filas_validas: validas, filas_con_error: filas.length - validas,\n  ids_unicos: Object.keys(vistos).length, duplicados: duplicadas, duplicados_con_cifras_distintas: conflictos,\n  errores_por_regla: porRegla, primeros_errores: errores, pasa: filas.length > 0 && validas === filas.length,\n  revisado_en: new Date().toISOString()\n} }];\n" }, position: [1080, 330] },
  output: [{ filas_recibidas: 1, filas_validas: 1, pasa: true }]
});

export default workflow('piura-control-calidad', 'Piura | Control de calidad evidencia')
  .add(webhookEntrada)
  .to(extraerWebhook)
  .to(validar)
  .add(manualEntrada)
  .to(leerTabla)
  .to(mapearTabla)
  .to(validar);

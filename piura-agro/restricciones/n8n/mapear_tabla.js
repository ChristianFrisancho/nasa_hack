// Code node "Mapear tabla n8n a filas CONTRATO": la tabla Piura_agro_evidencia guarda payload_json; si el payload trae columnas
// del CONTRATO se usan; si no, la fila pasa tal cual y el validador la marca (columnas_faltantes). No inventa valores.
const salida = [];
$input.all().forEach(function (it) {
  const j = it.json || {};
  let p = {};
  try { p = JSON.parse(j.payload_json || '{}'); } catch (e) { p = {}; }
  const fila = (p && typeof p === 'object' && p.variable !== undefined) ? Object.assign({}, p) : { record_type: j.record_type, topic: j.topic, source_url: j.source_url };
  if (!fila.id_registro) fila.id_registro = j.record_key || String(j.id);
  fila._origen = 'tabla_n8n:SW9ZbPKCuDmDufK4';
  salida.push({ json: fila });
});
return salida.length ? salida : [{ json: { _sin_filas: true, _origen: 'tabla_n8n:SW9ZbPKCuDmDufK4' } }];

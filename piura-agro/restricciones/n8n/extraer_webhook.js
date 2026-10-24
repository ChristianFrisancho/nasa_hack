// Code node "Extraer filas del webhook": acepta {rows:[...]}, {body:{rows:[...]}}, un arreglo o una fila suelta.
const salida = [];
$input.all().forEach(function (it) {
  const j = it.json || {};
  const b = j.body !== undefined ? j.body : j;
  const filas = Array.isArray(b) ? b : (Array.isArray(b.rows) ? b.rows : (Array.isArray(b.filas) ? b.filas : (b.variable !== undefined ? [b] : [])));
  filas.forEach(function (r) { const o = Object.assign({}, r); o._origen = 'webhook'; salida.push({ json: o }); });
});
return salida.length ? salida : [{ json: { _sin_filas: true, _origen: 'webhook' } }];

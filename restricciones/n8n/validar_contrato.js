// Code node "Validar CONTRATO y resumir" (Run Once for All Items). Espejo de tools/limpiar.py, pero acumula errores en vez de abortar.
const CAMPOS = ['variable','valor','valor_min','valor_max','unidad','cultivo','variedad','etapa','zona','lugar','lat','lon','fecha_o_periodo','fuente','url_o_doi','metodo','tipo_evidencia','estado','notas'];
const OBLIG = ['variable','unidad','cultivo','lugar','fecha_o_periodo','fuente','url_o_doi','metodo','tipo_evidencia','estado','notas'];
const UNIDADES = ['mm','mm/día','kg/ha','t/ha','dS/m','cmol/kg','%','°C','días','ha','PEN/ha','PEN/kg','PEN/t','PEN/m3','USD/ha','m3/ha','m3/ha/año','hm3'];
const ESTADOS = ['observado','estimado','desconocido'];
const TIPOS = ['medicion_local','regional','bibliografico','analogo_externo','prediccion'];
const ZONAS = ['alto_piura','medio_piura','bajo_piura','chira','san_lorenzo','sierra_piura','medio_bajo_piura','piura_region'];
const DOTACION = /^(dotacion|modulo_riego|volumen_asignado|volumen_licencia)/;
const CE_SUELO = /^(ce_suelo|ece)/i;
const EXTRACTO = /pasta saturada|extracto de saturaci|1:1|1:2[.,]5|1:5/i;
const NO_DECLARA = /no declar|sin declarar|extracto desconocido/i;
const s = function (x) { return x === null || x === undefined ? '' : String(x).trim(); };
const num = function (x) { const t = s(x); if (t === '') return null; const n = Number(t); return Number.isFinite(n) ? n : NaN; };
const filas = $input.all().map(function (it) { return it.json; }).filter(function (r) { return r && !r._sin_filas; });
const errores = []; const porRegla = {}; const vistos = {}; let validas = 0; let nErr = 0; let duplicadas = 0; let conflictos = 0;
const marca = function (i, id, regla, detalle) { nErr += 1; porRegla[regla] = (porRegla[regla] || 0) + 1; if (errores.length < 200) errores.push({ fila: i + 1, id_registro: id, regla: regla, detalle: detalle }); };
filas.forEach(function (r, i) {
  const clave = ['variable','cultivo','variedad','etapa','lugar','fecha_o_periodo','unidad','fuente'].map(function (c) { return s(r[c]); }).join('|');
  const id = s(r.id_registro) || clave;
  const n0 = nErr;
  const faltan = CAMPOS.filter(function (c) { return !(c in r); });
  if (faltan.length) marca(i, id, 'columnas_faltantes', faltan.join(','));
  OBLIG.forEach(function (c) { if (s(r[c]) === '') marca(i, id, 'obligatorio_vacio', c); });
  if (s(r.unidad) && UNIDADES.indexOf(s(r.unidad)) < 0) marca(i, id, 'unidad_no_permitida', s(r.unidad));
  if (s(r.estado) && ESTADOS.indexOf(s(r.estado)) < 0) marca(i, id, 'estado_invalido', s(r.estado));
  if (s(r.tipo_evidencia) && TIPOS.indexOf(s(r.tipo_evidencia)) < 0) marca(i, id, 'tipo_evidencia_invalido', s(r.tipo_evidencia));
  const v = num(r.valor), lo = num(r.valor_min), hi = num(r.valor_max);
  [['valor', v], ['valor_min', lo], ['valor_max', hi], ['lat', num(r.lat)], ['lon', num(r.lon)]].forEach(function (p) { if (Number.isNaN(p[1])) marca(i, id, 'no_numerico', p[0] + '=' + s(r[p[0]])); });
  const ok = function (x) { return x !== null && !Number.isNaN(x); };
  if (s(r.estado) === 'desconocido' && (ok(v) || ok(lo) || ok(hi))) marca(i, id, 'desconocido_con_cifra', 'valor/min/max deben ir vacíos');
  if (s(r.estado) && s(r.estado) !== 'desconocido' && !ok(v) && !(ok(lo) && ok(hi))) marca(i, id, 'cifra_faltante', 'sin valor ni rango completo');
  if (ok(lo) && ok(hi) && lo > hi) marca(i, id, 'min_mayor_que_max', lo + ' > ' + hi);
  if (ok(v) && ok(lo) && v < lo) marca(i, id, 'valor_bajo_min', v + ' < ' + lo);
  if (ok(v) && ok(hi) && v > hi) marca(i, id, 'valor_sobre_max', v + ' > ' + hi);
  if (ok(v) && !ok(lo) && !ok(hi) && s(r.notas).toLowerCase().indexOf('rango') < 0) marca(i, id, 'sin_rango_sin_explicacion', 'notas debe explicar la falta de rango');
  const z = s(r.zona);
  if (z && ZONAS.indexOf(z) < 0) marca(i, id, 'zona_invalida', z);
  if (!z && s(r.notas).indexOf('Zona no aplica:') < 0) marca(i, id, 'zona_vacia_sin_explicacion', 'falta "Zona no aplica:"');
  if (DOTACION.test(s(r.variable)) && (s(r.estado) !== 'estimado' || s(r.metodo) !== 'dotacion_asignada')) marca(i, id, 'dotacion_mal_marcada', 'estado=estimado y metodo=dotacion_asignada');
  if (CE_SUELO.test(s(r.variable))) {
    const declara = EXTRACTO.test(s(r.metodo)) && !NO_DECLARA.test(s(r.metodo));
    if (s(r.metodo) !== 'ce_extracto_no_declarado' && !declara) marca(i, id, 'ce_sin_extracto', 'declarar extracto o usar ce_extracto_no_declarado');
    if (s(r.metodo) === 'ce_extracto_no_declarado' && s(r.estado) !== 'observado') marca(i, id, 'ce_estado', 'ce_extracto_no_declarado va con observado');
  }
  if (s(r.tipo_evidencia) === 'analogo_externo' && s(r.notas).indexOf('Comparabilidad:') < 0) marca(i, id, 'analogo_sin_comparabilidad', 'falta "Comparabilidad:"');
  const huella = [s(r.valor), s(r.valor_min), s(r.valor_max)].join('|');
  if (id in vistos) { duplicadas += 1; if (vistos[id] !== huella) { conflictos += 1; marca(i, id, 'duplicado_con_cifras_distintas', vistos[id] + ' vs ' + huella); } }
  else vistos[id] = huella;
  if (nErr === n0) validas += 1;
});
const fuente = filas.length && filas[0]._origen ? filas[0]._origen : 'webhook';
return [{ json: {
  origen: fuente, filas_recibidas: filas.length, filas_validas: validas, filas_con_error: filas.length - validas,
  ids_unicos: Object.keys(vistos).length, duplicados: duplicadas, duplicados_con_cifras_distintas: conflictos,
  errores_por_regla: porRegla, primeros_errores: errores, pasa: filas.length > 0 && validas === filas.length,
  revisado_en: new Date().toISOString()
} }];

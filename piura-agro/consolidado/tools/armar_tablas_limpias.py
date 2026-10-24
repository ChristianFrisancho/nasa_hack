"""Arma las 3 tablas legibles de consolidado/ a partir de los CSV del contrato y las salidas del motor.
Uso: python3 consolidado/tools/armar_tablas_limpias.py  (desde piura-agro/)"""
import csv, json, glob, os, re
from collections import defaultdict

def num(x):
    if x in (None, ''): return ''
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    if abs(v) >= 100: return f'{v:,.0f}'.replace(',', ' ')
    if abs(v) >= 10: return f'{v:.1f}'.rstrip('0').rstrip('.')
    return f'{v:.2f}'.rstrip('0').rstrip('.')

def cifra(q, unidad=True):
    """{'valor','valor_min','valor_max','unidad','estado'} -> '3 475 m3/ha (2 791–4 159)'"""
    if not isinstance(q, dict) or (q.get('valor') is None and q.get('valor_min') is None):
        return 'desconocido'
    v, a, b = num(q.get('valor')), num(q.get('valor_min')), num(q.get('valor_max'))
    u = (' ' + q['unidad']) if unidad and q.get('unidad') else ''
    u = '' if q.get('unidad') in ('adimensional', 'categoría', 'pH') else u
    s = (v or f'{a}–{b}') + u
    if a != '' and b != '' and v and (a != v or b != v): s += f' ({a}–{b})'
    return s

def guardar(ruta, filas, cols, lineas_lf=False):
    with open(ruta, 'w', newline='', encoding='utf-8-sig') as fh:
        options = {'lineterminator': '\n'} if lineas_lf else {}
        w = csv.DictWriter(fh, fieldnames=cols, **options); w.writeheader(); w.writerows(filas)
    print(ruta, len(filas), 'filas', len(cols), 'columnas')

# ---------- 1) recomendaciones por parcela (salidas del motor) ----------
NOMBRE = {'bajo_piura_tras_arroz': 'Bajo Piura después de arroz', 'tablazo_sur_ce_medida': 'Tablazo Sur (CE de suelo medida)',
          'sin_datos_suelo': 'Chira sin análisis de suelo', 'salino_napa_medida': 'Parcela salina con napa medida',
          'salino_sin_datos': 'Parcela salina sin datos', 'inviable': 'Parcela sin cultivo viable'}
rec = []
for f in sorted(glob.glob('consolidado/motor/salidas/*.json')):
    ej = os.path.basename(f)[:-5]
    d = json.load(open(f, encoding='utf-8'))
    ent = json.load(open(f'consolidado/motor/ejemplos/{ej}.json', encoding='utf-8'))
    esc = d.get('escenarios_climaticos', {})
    p10 = {}
    for e in esc.get('escenarios', []):
        for o in e.get('orden', []):
            if e['escenario'] == 'sin_el_nino': p10[o['cultivo']] = (o.get('p10'), o.get('p50'))
    primeros = '; '.join(f"{e['escenario']}: {e.get('primero') or 'ninguno'}" for e in esc.get('escenarios', []))
    sec = [s for s in d.get('secuencias', []) if s.get('viable')]
    mejor_sec = ' → '.join(sec[0]['cultivos']) if sec else 'ninguna viable'
    faltan_glob = '; '.join(d.get('datos_faltantes_globales', [])[:4])
    ranking = d.get('ranking', [])
    todos = [(c, 'aceptado') for c in d.get('aceptados', [])] + [(c, 'descartado') for c in d.get('descartados', [])] + [(c, 'sin datos') for c in d.get('sin_datos_suficientes', [])]
    for c, dec in todos:
        n = c['cultivo']
        ver = c.get('veredictos', [])
        malos = [f"{v['filtro']}: {v.get('motivo','')}" for v in ver if v.get('resultado') == 'advierte']
        noev = [v['filtro'] for v in ver if v.get('resultado') == 'no_evaluable']
        buenos = [v['filtro'] for v in ver if v.get('resultado') in ('pasa', 'ok')]
        if dec == 'descartado': porque = 'Descartado por ' + '; '.join(c.get('motivos', []))
        elif dec == 'sin datos': porque = 'No se recomienda: faltan ' + '; '.join(c.get('datos_faltantes', []))
        else:
            porque = ('Pasa ' + ', '.join(buenos) + '.') if buenos else ''
            if noev: porque += ' No se pudo evaluar por falta de datos: ' + ', '.join(noev) + '.'
            if malos: porque += ' Alertas: ' + ' | '.join(malos)
        nut = c.get('nutrientes', {}) or {}
        ab = nut.get('absorcion', {}) or {}
        ex = nut.get('exportacion', {}) or {}
        deja = c.get('deja_en_suelo', []) or []
        tras = c.get('estado_tras_cosecha', {}) or {}
        pp = p10.get(n, (None, None))
        rec.append({
            'parcela': NOMBRE.get(ej, ej), 'zona': ent.get('parcela', {}).get('zona', ''), 'cultivo_anterior': ent.get('cultivo_anterior', ''),
            'puesto': (ranking.index(n) + 1) if n in ranking else '', 'cultivo_siguiente': n, 'decision': dec,
            'resumen': (f"Puesto {ranking.index(n)+1} de {len(ranking)}; margen P50 {num(pp[1])} PEN/ha; P10 {num(pp[0])}; pasa {len(buenos)} de {len(ver)} filtros" + (f"; alerta en {', '.join(v['filtro'] for v in ver if v.get('resultado') == 'advierte')}" if malos else '') + (f"; sin datos para {', '.join(noev)}" if noev else '')) if n in ranking else porque[:160],
            'por_que': porque.strip(),
            'margen_PEN_ha': cifra(c.get('margen_ha'), False) if c.get('margen_ha') else '',
            'margen_P10_PEN_ha': num(pp[0]), 'margen_P50_PEN_ha': num(pp[1]),
            'rendimiento_t_ha': cifra(c.get('rendimiento'), False) if c.get('rendimiento') else '',
            'agua_riego_bruto_m3_ha': cifra((c.get('agua') or {}).get('riego_bruto_m3_ha'), False) if c.get('agua') else '',
            'saca_del_suelo_N_P2O5_K2O_kg_ha': ' / '.join(cifra(ex.get(k) or ab.get(k), False) for k in ('N', 'P2O5', 'K2O')) if (ex or ab) else '',
            'deja_en_el_suelo': '; '.join(f"{x['concepto']} {cifra(x.get('valor'))}" for x in deja if isinstance(x.get('valor'), dict) and x['valor'].get('valor') is not None) or 'sin cifra (residuo de N, P y K desconocido)',
            'ECe_tras_cosecha_dS_m': cifra(tras.get('ECe'), False) if tras.get('ECe') else '',
            'primero_por_escenario_climatico': primeros, 'mejor_secuencia': mejor_sec,
            'datos_que_cambiarian_la_recomendacion': '; '.join(c.get('datos_faltantes', []) or []) or faltan_glob,
        })
rec.sort(key=lambda r: (r['parcela'], r['puesto'] == '', r['puesto'] if r['puesto'] != '' else 99, r['decision']))
guardar('consolidado/recomendaciones_por_parcela.csv', rec, list(rec[0].keys()))

# ---------- 2) resumen por cultivo ----------
fichas = list(csv.DictReader(open('cultivos/fichas_anuales.csv', encoding='utf-8'))) + list(csv.DictReader(open('cultivos/perennes.csv', encoding='utf-8')))
tipo = {r['cultivo']: 'anual' for r in csv.DictReader(open('cultivos/fichas_anuales.csv', encoding='utf-8'))}
tipo.update({r['cultivo']: 'perenne' for r in csv.DictReader(open('cultivos/perennes.csv', encoding='utf-8'))})
LEGUMINOSAS = {'arveja','caupi','frijol castilla/grano seco','frijol caupi','frijol de palo','haba','mani','soya','zarandaja'}
por = defaultdict(lambda: defaultdict(list))
for r in fichas:
    if r['cultivo'] in ('', 'todos'): continue
    por[r['cultivo']][r['variable']].append(r)
ORD = {'observado': 0, 'estimado': 1, 'desconocido': 2}
def mejor(c, var, filtro=None):
    rows = [r for r in por[c].get(var, []) if (r.get('valor') or r.get('valor_min')) and (not filtro or filtro(r))]
    rows.sort(key=lambda r: (ORD.get(r['estado'], 3), -float(r.get('confianza') or 0)))
    if not rows: return '', ''
    r = rows[0]
    return cifra({'valor': r['valor'] or None, 'valor_min': r.get('valor_min') or None, 'valor_max': r.get('valor_max') or None, 'unidad': r['unidad']}), r['fuente'].split(',')[0]
def organo_principal(r):
    m = (r.get('metodo', '') + r.get('notas', '')).lower()
    return not any(k in m for k in ('rastrojo', 'paja', 'stover', 'straw', 'residuo'))
reglas = list(csv.DictReader(open('cultivos/reglas_rotacion.csv', encoding='utf-8')))
POS = re.compile(r'aument|mejor|reduce riesgo|disminuye riesgo|benefic', re.I)
CLASE = {'T':'tolerante','MT':'moderadamente tolerante','MS':'moderadamente sensible','S':'sensible'}
res = []
for c in sorted(por):
    fuentes = set()
    def g(var, filtro=None):
        v, f = mejor(c, var, filtro)
        if f: fuentes.add(f)
        return v
    despues_si, despues_no = [], []
    for r in reglas:
        if r.get('cultivo_previo') != c or not r.get('cultivo_siguiente'): continue
        txt = f"{r['cultivo_siguiente']} ({r.get('efecto','').strip()}"
        if r.get('valor'): txt += f", {num(r['valor'])} {r['unidad']}"
        txt += ')'
        (despues_no if (r.get('tipo_efecto') == 'plaga_compartida' or not POS.search(r.get('efecto', ''))) else despues_si).append(txt)
    deja = g('fbn_total_fijado_kg_N_ha') or g('fbn_kg_N_ha')
    if not deja:
        deja = 'fijación no cuantificada' if c in LEGUMINOSAS else ('no aplica (no leguminosa)' if c in tipo else '')
    res.append({
        'cultivo': c, 'tipo': tipo.get(c, ''),
        'ciclo': g('periodo_vegetativo') or g('anos_a_primera_produccion'),
        'kc_mitad_ciclo': g('kc', lambda r: 'med' in (r.get('etapa') or '').lower() or 'mitad' in (r.get('etapa') or '').lower()) or g('kc'),
        'tolerancia_sal': CLASE.get(g('clase_tolerancia_salinidad').split(' ')[0], g('clase_tolerancia_salinidad')),
        'ECe_sin_perdida_dS_m': g('ece_umbral'), 'perdida_por_dS_m': g('pendiente_salinidad_b'),
        'ECe_50pct_rendimiento': g('ece_rend_50pct'),
        'temperatura_optima': g('temperatura_optima'), 'pH_optimo': g('ph_optimo'),
        'raiz_max': g('profundidad_raiz_max'),
        'saca_del_suelo_N': g('exportacion_N', organo_principal) or g('absorcion_total_N'),
        'saca_del_suelo_P2O5': g('exportacion_P2O5', organo_principal) or g('absorcion_total_P2O5'),
        'saca_del_suelo_K2O': g('exportacion_K2O', organo_principal) or g('absorcion_total_K2O'),
        'absorcion_total_N': g('absorcion_total_N'),
        'deja_N_fijado_por_campana': deja,
        'plaga_clave': '; '.join(sorted({r['valor'] or r.get('notas', '')[:60] for r in por[c].get('plaga_clave', []) if r['valor']}))[:200],
        'conviene_despues': '; '.join(despues_si[:6]),
        'evitar_o_cuidar_despues': '; '.join(despues_no[:6]),
        'fuentes_principales': '; '.join(sorted(fuentes))[:300],
    })
cols = list(res[0].keys())
cols = [k for k in cols if any(r[k] for r in res)]
guardar('consolidado/cultivos_resumen.csv', [{k: r[k] for k in cols} for r in res], cols, lineas_lf=True)

# ---------- 3) super dataset compacto ----------
SRC = [('clima_lluvia','restricciones/lluvia_zona_pisco.csv'),('clima_temperatura','restricciones/temperatura_pisco_zona.csv'),('clima_temperatura_enso','restricciones/temperatura_pisco_zona_enso.csv'),
('evidencia','restricciones/evidencia_observada.csv'),('cultivo_anual','cultivos/fichas_anuales.csv'),('cultivo_perenne','cultivos/perennes.csv'),
('recuperacion_suelo','cultivos/recuperacion_suelo.csv'),('reglas_rotacion','cultivos/reglas_rotacion.csv'),('calendario_drap','cultivos/calendario_drap_piura.csv'),
('suelo','suelos/suelos_piura.csv'),('agua_riego_cew','suelos/datos/cew_por_zona.csv'),('pendiente','suelos/datos/pendiente_por_zona.csv'),
('profundidad_ph','suelos/datos/profundidad_ph_por_zona.csv'),('ece_drenaje_fen','suelos/datos/zonas_ece_drenaje_fen.csv'),('fen','suelos/datos/fen_por_zona.csv'),
('costos','consolidado/motor/datos_motor/costos_produccion.csv'),('rendimiento_precio','consolidado/motor/datos_motor/rendimiento_precio_drap.csv'),('modelo','modelo/data/evidencia_modelo.csv')]
MAIN = ['cultivo','zona','variable','valor','rango','unidad','estado','tipo_evidencia','etapa','variedad','fecha_o_periodo','lugar','fuente','metodo','url_o_doi']
EXTRA = ['subzona','zonas_aplicables','fuente_primaria','cultivo_previo','cultivo_siguiente','efecto']
seen, out = set(), []
for capa, f in SRC:
    for r in csv.DictReader(open(f, newline='', encoding='utf-8')):
        g = lambda k: (r.get(k) or '').strip()
        a, b = num(g('valor_min')), num(g('valor_max'))
        fila = {k: g(k) for k in MAIN if k != 'rango'}
        fila['valor'] = num(fila['valor']) if fila['valor'] else ''
        fila['rango'] = f'{a}–{b}' if a != '' and b != '' else (a or b)
        extra = '; '.join(f'{k}: {g(k)}' for k in EXTRA if g(k))
        fila['notas'] = ' | '.join(x for x in (extra, g('notas')) if x)
        key = tuple(fila[k] for k in MAIN)
        if key in seen: continue
        seen.add(key); fila['tema'] = capa; fila['archivo_origen'] = f; out.append(fila)
cols = ['tema'] + MAIN + ['notas', 'archivo_origen']
cols = [k for k in cols if sum(1 for r in out if r[k]) / len(out) >= 0.02]
out.sort(key=lambda r: (r['tema'], r['cultivo'], r['zona'], r['variable']))
guardar('consolidado/piura_super_dataset.csv', [{k: r[k] for k in cols} for r in out], cols)

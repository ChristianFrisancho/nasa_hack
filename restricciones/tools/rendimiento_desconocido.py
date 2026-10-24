"""Ronda 5, tarea 5: explicación fila por fila de los rendimientos con estado=desconocido.

No crea cifras. Por cada fila descartada toma la cifra publicada que dice la nota, la regla
que la descartó y la contrasta con los rendimientos observados del mismo cultivo que ya
están en evidencia_observada.csv (misma zona y región). El veredicto sólo orienta la
revisión; el estado de la fila no cambia.
Salida: anexos/rendimiento_desconocido_explicado.csv
"""
import csv, re, statistics as st, collections

E = list(csv.DictReader(open('evidencia_observada.csv', encoding='utf-8')))
OBS = collections.defaultdict(list)
for r in E:
    if r['variable'] == 'rendimiento' and r['estado'] == 'observado' and r['valor'] and r['unidad'] == 't/ha':
        try:
            v = float(r['valor'])
        except ValueError:
            continue
        OBS[(r['cultivo'], r['zona'])].append(v)
        OBS[(r['cultivo'], '*')].append(v)
        if r['zona'] == 'piura_region':
            OBS[(r['cultivo'], 'dep')].append(v)

def familia(c):
    return {'banano/plátano': 'plátano'}.get(c, c)

def ref(c, z):
    out = {}
    for k, lab in ((z, 'zona'), ('dep', 'departamento'), ('*', 'todas')):
        L = OBS.get((familia(c), k)) or OBS.get((c, k))
        if L:
            out[lab] = (len(L), st.median(L), max(L))
    return out

# Ronda 7: las rescatadas por serie (rescatado_por_serie=1, ahora 'estimado') siguen en el anexo para que Modelos valide con y sin ellas.
D = [r for r in E if r['variable'] == 'rendimiento' and (r['estado'] == 'desconocido' or r.get('rescatado_por_serie') == '1')]
# misma cifra repetida en >=3 años del mismo distrito = serie, no un error suelto
_s = collections.defaultdict(set)
for r in D:
    _s[(r['cultivo'], r['lugar'])].add(r['fecha_o_periodo'])
serie = {k: len(v) for k, v in _s.items()}

# Ronda 6, regla de serie propuesta a Piura Modelos (sólo flag; el estado NO cambia hasta que Modelos la acepte):
# una cifra A4 (distrito-año) es 'posible_real_por_serie' si el mismo distrito publica para el mismo cultivo cifras del mismo
# orden de magnitud (dentro de un factor raíz de 10 = 3,16, arriba o abajo) en >= 3 años distintos, contando ese año.
# Cuentan las cifras publicadas de la misma base, estén observadas o descartadas.
F_OM = 10 ** 0.5
PUBL = collections.defaultdict(list)  # (cultivo, lugar) -> [(año, cifra)]
for r in E:
    if r['variable'] == 'rendimiento' and r['estado'] == 'observado' and r['valor'] and r['unidad'] == 't/ha' and r.get('rescatado_por_serie') != '1':
        try: PUBL[(r['cultivo'], r['lugar'])].append((r['fecha_o_periodo'], float(r['valor'])))
        except ValueError: pass
def _cifra(n):
    m = re.search(r'Cifra publicada ([\d.]+) t/ha', n) or re.search(r'A4: ([\d.]+) t/ha', n)
    return float(m.group(1))
for r in D:
    PUBL[(r['cultivo'], r['lugar'])].append((r['fecha_o_periodo'], _cifra(r['notas'])))
def serie_om(r, cifra, f=F_OM):
    anios = sorted({a for a, v in PUBL[(r['cultivo'], r['lugar'])] if cifra / f <= v <= cifra * f})
    return anios

def flag_serie(r, regla, cifra):
    if regla != 'A4':
        return {'posible_real_por_serie': 'no_aplica', 'serie_anios_mismo_orden': '', 'variante_estricta_factor_1_5': '', 'serie_detalle': f'Regla {regla} (no es distrito-año); la regla de serie es sólo para A4.'}
    an = serie_om(r, cifra)
    ok = len(an) >= 3
    a2 = serie_om(r, cifra, 1.5)
    return {'posible_real_por_serie': 'si' if ok else 'no', 'serie_anios_mismo_orden': len(an),
            'variante_estricta_factor_1_5': ('si' if len(a2) >= 3 else 'no') + f" ({len(a2)} años)",
            'serie_detalle': (f"Años del mismo distrito y cultivo con cifra entre {cifra/F_OM:.2f} y {cifra*F_OM:.2f} t/ha: {', '.join(an)}."
                              + (" Ronda 7: Modelos aceptó sólo la variante factor 1,5; con √10 sola no entra." if ok else " Menos de 3 años: la regla no la rescata."))}

rows = []
for r in D:
    n = r['notas']
    regla = re.search(r'\b(A\d)\b', n).group(1)
    m = re.search(r'Cifra publicada ([\d.]+) t/ha', n) or re.search(r'A4: ([\d.]+) t/ha', n)
    cifra = float(m.group(1))
    mc = re.search(r'Cosecha (\d+) ha', n)
    ha = int(mc.group(1)) if mc else None
    R = ref(r['cultivo'], r['zona'])
    base = R.get('zona') or R.get('departamento') or R.get('todas')
    if base:
        nref, med, mx = base
        x = cifra / med if med else float('inf')
        contraste = '; '.join(f"{k}: n={a}, mediana {b:.2f}, máx {c:.2f} t/ha" for k, (a, b, c) in R.items())
    else:
        x, mx, contraste = None, None, 'sin rendimientos observados del cultivo'
    rep = serie[(r['cultivo'], r['lugar'])]
    if x is None:
        ver, por = 'sin_contraste', 'No hay otra cifra observada del cultivo para contrastar.'
    elif rep >= 3 and r['zona'] != 'piura_region':
        ver = 'posible_real_revisar'
        por = (f"El mismo distrito repite cifras de este orden en {rep} años; parece una serie coherente "
               f"(¿otra variedad o sistema?), no un error suelto. Hace falta una fuente local para validarla.")
    elif mx and cifra <= 1.5 * mx:
        ver = 'posible_real_revisar'
        por = f"Cabe dentro de 1,5 x el máximo observado del cultivo ({mx:.2f} t/ha); la regla pudo ser estricta."
    elif x >= 5:
        ver = 'error_probable'
        por = f"Es {x:.1f} veces la mediana de referencia; lo más probable es un error de transcripción, de unidad o de superficie."
    else:
        ver = 'dudoso'
        por = f"Es {x:.1f} veces la mediana de referencia y supera 1,5 x el máximo observado; sin fuente que lo confirme."
    if ha is not None and ha <= 10 and ver != 'posible_real_revisar':
        por += f" Superficie cosechada mínima ({ha} ha): una sola parcela o un mes mal registrado basta para distorsionarla."
    rows.append({'id': r.get('id', ''), 'cultivo': r['cultivo'], 'zona': r['zona'], 'lugar': r['lugar'],
                 'fecha_o_periodo': r['fecha_o_periodo'], 'fuente': r['fuente'], 'regla': regla,
                 'cifra_publicada_t_ha': cifra, 'superficie_cosechada_ha': ha if ha is not None else '',
                 'veces_mediana_ref': f"{x:.1f}" if x else '', 'contraste_evidencia_propia': contraste,
                 'busqueda_r5': 'DRAP/SIEA: misma base ya cargada (datos abiertos GORE Piura, corte 2025-05-27) y compendios INEI 2017/2025; no hay segunda fuente pública por distrito-año. Tesis: ninguna encontrada con ese cultivo, zona y año.',
                 'veredicto': ver, 'explicacion': por, 'estado_actual': r['estado'],
                 'rescatado_por_serie': r.get('rescatado_por_serie', ''),
                 **flag_serie(r, regla, cifra)})
    d = rows[-1]
    d['marca_r7'] = ('entra: rescatada por serie factor 1,5' if d['rescatado_por_serie'] == '1'
                     else 'excluida: pendiente revisión manual' if 'pendiente revisión manual' in n
                     else 'sólo √10 la rescataría: no entra' if d['posible_real_por_serie'] == 'si' else '')

rows.sort(key=lambda d: (d['veredicto'], d['cultivo'], d['zona'], d['fecha_o_periodo']))
with open('anexos/rendimiento_desconocido_explicado.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print('OK', len(rows), 'filas', dict(collections.Counter(d['veredicto'] for d in rows)), 'estado_actual', dict(collections.Counter(d['estado_actual'] for d in rows)))

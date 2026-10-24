"""Build the compact, static dashboard snapshot from the motor's published outputs."""
import csv
import json
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'piura-agro' / 'consolidado'
OUTPUT = Path(__file__).resolve().parent / 'data' / 'dashboard.json'

EXAMPLES = [
    ('bajo_piura_tras_arroz', 'Bajo Piura · después de arroz'),
    ('sin_datos_suelo', 'Chira · sin análisis de suelo'),
    ('tablazo_sur_ce_medida', 'Tablazo Sur · CE medida'),
    ('salino_napa_medida', 'Parcela salina · napa medida'),
    ('salino_sin_datos', 'Parcela salina · datos incompletos'),
    ('inviable', 'Parcela sin cultivo viable'),
]


def read_csv(name):
    with (SOURCE / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def canonical_crop(value):
    text = ''.join(c for c in unicodedata.normalize('NFKD', value.lower()) if not unicodedata.combining(c))
    aliases = {
        'frijol castilla/grano seco':'frijol grano', 'frijol caupi':'caupi',
        'uva de mesa':'uva', 'banano (ano 1)':'banano', 'banano (ano 2)':'banano',
        'naranja (referencia citricos)':'naranja', 'cana de azucar (planta)':'cana de azucar',
        'cana de azucar (soca)':'cana de azucar',
    }
    return aliases.get(text, text)


def crop_record(row):
    return {
        'variable': row.get('variable',''), 'value': row.get('valor',''),
        'min': row.get('valor_min',''), 'max': row.get('valor_max',''),
        'unit': row.get('unidad',''), 'variety': row.get('variedad',''),
        'stage': row.get('etapa',''), 'date': row.get('fecha_o_periodo',''),
        'zone': row.get('zona',''), 'place': row.get('lugar',''),
        'method': row.get('metodo',''),
        'status': row.get('estado',''), 'evidence': row.get('tipo_evidencia',''),
        'confidence': row.get('confianza',''), 'source': row.get('fuente',''),
        'url': row.get('url_o_doi',''), 'notes': row.get('notas',''),
    }


def number(value):
    if value in (None, ''):
        return None
    try:
        return float(str(value).replace(' ', '').replace(',', '.'))
    except ValueError:
        return None


def measure(raw):
    if not isinstance(raw, dict):
        return None
    return {
        'value': raw.get('valor'), 'min': raw.get('valor_min'),
        'max': raw.get('valor_max'), 'unit': raw.get('unidad', ''),
        'state': raw.get('estado', ''), 'evidence': raw.get('tipo_evidencia', ''),
        'source': raw.get('fuente', ''), 'url': raw.get('url_o_doi', ''),
        'note': raw.get('notas', ''),
    }


def candidate(raw, row, rank):
    water = raw.get('agua') or {}
    nutrients = raw.get('nutrientes') or {}
    after = raw.get('estado_tras_cosecha') or {}
    stages = []
    for name, stage in (water.get('etapas') or {}).items():
        stages.append({
            'name': name, 'days': measure(stage.get('dias')),
            'etc': measure(stage.get('ETc_mm')),
            'rain': measure(stage.get('lluvia_p90_mm')),
            'netIrrigation': measure(stage.get('riego_neto_mm')),
        })
    verdicts = []
    for verdict in raw.get('veredictos', []):
        figures = verdict.get('cifras') or {}
        urls = [x.get('url_o_doi') for x in figures.values() if isinstance(x, dict) and x.get('url_o_doi')]
        verdicts.append({
            'filter': verdict.get('filtro', ''), 'result': verdict.get('resultado', ''),
            'reason': verdict.get('motivo', ''), 'source': verdict.get('fuente', ''),
            'evidence': verdict.get('tipo_evidencia', ''), 'url': urls[0] if urls else '',
            'missing': verdict.get('faltantes', []),
        })
    return {
        'crop': raw['cultivo'], 'decision': row['decision'], 'rank': rank,
        'summary': row['resumen'], 'why': row['por_que'],
        'p10': number(row['margen_P10_PEN_ha']), 'p50': number(row['margen_P50_PEN_ha']),
        'margin': measure(raw.get('margen_ha')), 'yield': measure(raw.get('rendimiento')),
        'duration': measure(raw.get('duracion')),
        'grossWater': measure(water.get('riego_bruto_m3_ha')),
        'netWater': measure(water.get('riego_neto_m3_ha')),
        'etcTotal': measure(water.get('etc_total')),
        'stages': stages,
        'export': {key: measure((nutrients.get('exportacion') or {}).get(key)) for key in ('N', 'P2O5', 'K2O')},
        'uptake': {key: measure((nutrients.get('absorcion') or {}).get(key)) for key in ('N', 'P2O5', 'K2O')},
        'residue': {key: measure((nutrients.get('residuo_devuelto') or {}).get(key)) for key in ('N', 'P2O5', 'K2O')},
        'soilEce': measure(after.get('ECe')),
        'soilBalance': {key: measure((after.get('balance_kg_ha') or {}).get(key)) for key in ('N', 'P2O5', 'K2O')},
        'verdicts': verdicts, 'missing': raw.get('datos_faltantes', []),
        'rejectionReasons': raw.get('motivos') or raw.get('motivos_descarte') or [],
    }


def build():
    rows = read_csv('recomendaciones_por_parcela.csv')
    profiles = read_csv('cultivos_resumen.csv')
    crop_rows = []
    for filename, kind in [('../cultivos/fichas_anuales.csv','anual'),('../cultivos/perennes.csv','perenne')]:
        crop_rows.extend((canonical_crop(row.get('cultivo','')), kind, row)
                         for row in read_csv(filename) if row.get('cultivo','').strip() not in ('','todos'))
    crop_details = {}
    for canonical, kind, row in crop_rows:
        crop_details.setdefault(canonical, []).append({**crop_record(row), 'kind':kind, 'originalCrop':row['cultivo']})
    soil_units = read_csv('../../piura-data/suelos_bajo_piura_unidades_v2.csv')
    soil_cum = read_csv('../../piura-data/suelos_montero_ayabaca_cum_v2.csv')
    soil_map_units = read_csv('../../piura-data/suelos_bajo_piura_mapunits_v2.csv')
    soil_zone_rows = read_csv('../suelos/suelos_piura.csv')
    zone_vars = ['ECe_medida_local','clase_drenaje_local','pH_rango_zona','profundidad_efectiva_enraizamiento','pendiente_media_cultivo']
    soil_zones = []
    zone_names = sorted({r['zona'] for r in soil_zone_rows if r.get('zona')})
    evidence_priority = {'medicion_local':0,'observado':0,'regional':1,'bibliografico':2,'prediccion':3,'analogo_externo':4}
    for zone in zone_names:
        items=[]
        for variable in zone_vars:
            matches=[r for r in soil_zone_rows if r.get('zona')==zone and r.get('variable')==variable and (r.get('valor') or r.get('valor_min') or r.get('estado')=='desconocido')]
            matches.sort(key=lambda r:(evidence_priority.get(r.get('tipo_evidencia',''),9), not bool(r.get('valor')), r.get('fuente','')))
            for r in matches:
                items.append({'variable':variable,'value':r.get('valor',''),'min':r.get('valor_min',''),'max':r.get('valor_max',''),
                    'unit':r.get('unidad',''),'status':r.get('estado',''),'evidence':r.get('tipo_evidencia',''),
                    'source':r.get('fuente',''),'url':r.get('url_o_doi',''),'notes':r.get('notas',''),
                    'place':r.get('lugar',''),'method':r.get('metodo','')})
        soil_zones.append({'zone':zone,'measurements':items})
    parcel_names = {
        'bajo_piura_tras_arroz': 'Bajo Piura después de arroz',
        'sin_datos_suelo': 'Chira sin análisis de suelo',
        'tablazo_sur_ce_medida': 'Tablazo Sur (CE de suelo medida)',
        'salino_napa_medida': 'Parcela salina con napa medida',
        'salino_sin_datos': 'Parcela salina sin datos',
        'inviable': 'Parcela sin cultivo viable',
    }
    examples = []
    for slug, label in EXAMPLES:
        raw = json.loads((SOURCE / 'motor' / 'salidas' / f'{slug}.json').read_text(encoding='utf-8'))
        inputs = json.loads((SOURCE / 'motor' / 'ejemplos' / f'{slug}.json').read_text(encoding='utf-8'))
        mine = {row['cultivo_siguiente']: row for row in rows if row['parcela'] == parcel_names[slug]}
        all_candidates = raw.get('aceptados', []) + raw.get('descartados', []) + raw.get('sin_datos_suficientes', [])
        if set(mine) != {c['cultivo'] for c in all_candidates}:
            raise ValueError(f'CSV and motor output differ for {slug}')
        ranking = raw.get('ranking', [])
        candidates = [candidate(c, mine[c['cultivo']], ranking.index(c['cultivo']) + 1 if c['cultivo'] in ranking else None)
                      for c in all_candidates]
        candidates.sort(key=lambda c: (c['rank'] is None, c['rank'] or 999, c['crop']))
        scenarios = []
        for scenario in (raw.get('escenarios_climaticos') or {}).get('escenarios', []):
            scenarios.append({
                'id': scenario['escenario'], 'first': scenario.get('primero'),
                'order': [{'crop': r['cultivo'], 'p10': r.get('p10'), 'p50': r.get('p50')}
                          for r in scenario.get('orden', [])],
            })
        sequences = [{'crops': s.get('cultivos', []), 'viable': s.get('viable', False),
                      'margin': measure(s.get('margen_total_ha'))}
                     for s in raw.get('secuencias', [])[:5]]
        examples.append({
            'id': slug, 'label': label, 'zone': mine[all_candidates[0]['cultivo']]['zona'],
            'previousCrop': inputs.get('cultivo_anterior') or '',
            'lat': (raw.get('parcela') or {}).get('lat'), 'lon': (raw.get('parcela') or {}).get('lon'),
            'message': raw.get('mensaje', ''), 'warnings': raw.get('avisos', [])[:8],
            'candidates': candidates, 'scenarios': scenarios, 'sequences': sequences,
            'globalMissing': raw.get('datos_faltantes_globales', [])[:10],
        })
    if len(rows) != 84 or len(profiles) != 36 or any(len(e['candidates']) != 14 for e in examples):
        raise ValueError('Unexpected source coverage')
    with (SOURCE / 'piura_super_dataset.csv').open(encoding='utf-8-sig', newline='') as handle:
        evidence_count = sum(1 for _ in csv.DictReader(handle))
    try:
        source_commit = subprocess.check_output(
            ['git', 'log', '-1', '--format=%h', '--',
             'piura-agro/consolidado/recomendaciones_por_parcela.csv',
             'piura-agro/consolidado/cultivos_resumen.csv',
             'piura-agro/consolidado/piura_super_dataset.csv'],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        source_commit = 'desconocido'
    payload = {
        'sourceCommit': source_commit, 'examples': examples, 'profiles': profiles,
        'cropDetails': crop_details,
        'soilUnits': soil_units, 'soilCum': soil_cum, 'soilMapUnits': soil_map_units,
        'soilZones': soil_zones,
        'counts': {'examples': len(examples), 'candidates': len(rows), 'profiles': len(profiles),
                   'cropSpeciesWithDetails': len(crop_details), 'cropFichaRows': len(crop_rows),
                   'soilUnits': len(soil_units), 'soilMapUnits': len(soil_map_units),
                   'soilCumClasses': len(soil_cum), 'evidence': evidence_count},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{OUTPUT.relative_to(ROOT)}: {len(examples)} examples, {len(rows)} alternatives, '
          f'{len(profiles)} profiles, {evidence_count} evidence rows, {OUTPUT.stat().st_size} bytes')


if __name__ == '__main__':
    build()

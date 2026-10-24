"""Build the compact, static dashboard snapshot from the motor's published outputs."""
import csv
import json
import subprocess
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
        'counts': {'examples': len(examples), 'candidates': len(rows), 'profiles': len(profiles),
                   'evidence': evidence_count},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{OUTPUT.relative_to(ROOT)}: {len(examples)} examples, {len(rows)} alternatives, '
          f'{len(profiles)} profiles, {evidence_count} evidence rows, {OUTPUT.stat().st_size} bytes')


if __name__ == '__main__':
    build()

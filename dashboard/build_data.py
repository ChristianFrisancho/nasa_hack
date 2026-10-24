"""Build the compact, static dashboard snapshot from the motor's published outputs."""
import csv
import json
import math
import statistics
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


def normalized_text(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', value.lower()) if not unicodedata.combining(c)).split())


DRAP_CROP_ALIASES = {
    # These are explicit species/common-name matches used only to open an
    # existing agronomic profile. The DRAP labels and their statistics remain
    # separate records so variety/product differences are not silently merged.
    'algodon':'algodon', 'algodon pima':'algodon', 'arroz':'arroz',
    'arveja grano seco':'arveja', 'arveja grano verde':'arveja',
    'banano (musa acuminata)':'banano', 'frijol caupi chiclayo castilla chileno grano seco':'caupi',
    'frijol caupi chiclayo castilla chileno grano verde':'caupi', 'frijol de palo grano seco (t.)':'frijol de palo',
    'frijol grano seco':'frijol grano', 'haba grano seco':'haba', 'haba grano verde':'haba',
    'cacao':'cacao', 'cafeto':'cafe', 'camote':'camote', 'cana de azucar (para alcohol)':'cana de azucar',
    'cebolla':'cebolla', 'limon sutil':'limon', 'limon tahiti':'limon', 'maiz amarillo duro':'maiz amarillo duro',
    'maiz amilaceo':'maiz amilaceo', 'maiz choclo':'maiz choclo', 'mani para fruta':'mani',
    'mango':'mango', 'maracuya':'maracuya', 'naranjo':'naranja', 'palto':'palta',
    'papa (agrupa mejoradas y nativas)':'papa', 'papaya':'papaya', 'paprika':'pimiento/paprika',
    'pimiento':'pimiento/paprika', 'pina':'pina', 'piquillo (t.)':'piquillo', 'soya':'soya',
    'trigo blando':'trigo', 'vid':'uva', 'zapallo':'zapallo', 'zarandaja grano seco':'zarandaja',
    'yuca':'yuca',
}


def drap_crop_stats():
    """Resumir el registro oficial DRAP por etiqueta literal, sin unir cultivos de nombre parecido."""
    source = read_csv('../cultivos/raw/drap_dataset.csv')
    groups = {}
    for row in source:
        crop = row.get('CULTIVO','').strip()
        year = int(number(row.get('ANO')) or 0)
        if not crop or year < 2015 or year > 2024:
            continue
        item = groups.setdefault((crop, year), {'rows':0,'sown':0.0,'harvested':0.0,'production':0.0,'price_value':0.0,'price_weight':0.0})
        item['rows'] += 1
        item['sown'] += number(row.get('SIEMBRA')) or 0
        item['harvested'] += number(row.get('COSECHA')) or 0
        produced = number(row.get('PRODUCCION')) or 0
        item['production'] += produced
        price = number(row.get('PRECIO_CHACRA'))
        if price is not None and produced > 0:
            item['price_value'] += price * produced
            item['price_weight'] += produced
    by_crop = {}
    for (crop,year), stats in groups.items():
        annual = by_crop.setdefault(crop, [])
        annual.append({'year':year, **stats})
    results=[]
    for crop, years in sorted(by_crop.items()):
        valid=[r for r in years if r['harvested'] > 0 and r['production'] > 0]
        if not valid:
            continue
        yields=[r['production']/r['harvested'] for r in valid if r['harvested'] >= 5]
        prices=[r['price_value']/r['price_weight'] for r in years if r['price_weight'] > 0]
        latest=max(valid,key=lambda r:r['year'])
        canonical=DRAP_CROP_ALIASES.get(normalized_text(crop))
        results.append({
            'name':crop, 'profileCrop':canonical or '', 'years':len(valid),
            'fromYear':min(r['year'] for r in valid), 'toYear':max(r['year'] for r in valid),
            'harvestAreaMeanHa':statistics.mean(r['harvested'] for r in valid),
            'productionMeanT':statistics.mean(r['production'] for r in valid),
            'yieldP10':quantile(yields,.1), 'yieldP50':statistics.median(yields) if yields else None,
            'yieldP90':quantile(yields,.9), 'priceMedianNominal':statistics.median(prices) if prices else None,
            'latestYear':latest['year'], 'latestHarvestAreaHa':latest['harvested'],
            'latestProductionT':latest['production'],
            'recordMonths':sum(r['rows'] for r in years),
        })
    return results


def quantile(values, q):
    if not values:
        return None
    s=sorted(values)
    pos=(len(s)-1)*q; lo=math.floor(pos); hi=math.ceil(pos)
    return s[lo] + (s[hi]-s[lo])*(pos-lo)


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
    drap_crops = drap_crop_stats()
    motor_crop_catalog = read_csv('../consolidado/motor/datos_motor/catalogo_cultivos.csv')
    motor_crops = {canonical_crop(r['cultivo']):r for r in motor_crop_catalog}
    annual_choices = {canonical_crop(r['cultivo_siguiente']) for r in rows}
    for crop in drap_crops:
        key = crop['profileCrop'] or canonical_crop(crop['name'])
        motor = motor_crops.get(key)
        crop['motorCrop'] = motor.get('cultivo','') if motor else ''
        crop['motorRole'] = ('rotacion_anual' if motor.get('modulo')=='anual' else 'perenne') if motor else 'registro_drap'
        crop['rankedAsAnnual'] = key in annual_choices
    crop_rows = []
    for filename, kind in [('../cultivos/fichas_anuales.csv','anual'),('../cultivos/perennes.csv','perenne')]:
        crop_rows.extend((canonical_crop(row.get('cultivo','')), kind, row)
                         for row in read_csv(filename) if row.get('cultivo','').strip() not in ('','todos'))
    crop_details = {}
    for canonical, kind, row in crop_rows:
        crop_details.setdefault(canonical, []).append({**crop_record(row), 'kind':kind, 'originalCrop':row['cultivo']})
    family_by_crop = {
        'algodon':'Malvaceae','arroz':'Poaceae','arveja':'Fabaceae','banano':'Musaceae','cacao':'Malvaceae',
        'cafe':'Rubiaceae','camote':'Convolvulaceae','cana de azucar':'Poaceae','cebolla':'Amaryllidaceae',
        'frijol grano':'Fabaceae','caupi':'Fabaceae','frijol de palo':'Fabaceae','haba':'Fabaceae','limon':'Rutaceae',
        'maiz amarillo duro':'Poaceae','maiz amilaceo':'Poaceae','maiz choclo':'Poaceae','mango':'Anacardiaceae','mani':'Fabaceae',
        'maracuya':'Passifloraceae','naranja':'Rutaceae','palta':'Lauraceae','papa':'Solanaceae','papaya':'Caricaceae',
        'pimiento/paprika':'Solanaceae','pina':'Bromeliaceae','piquillo':'Solanaceae','sorgo':'Poaceae',
        'soya':'Fabaceae','trigo':'Poaceae','uva':'Vitaceae','yuca':'Euphorbiaceae','zapallo':'Cucurbitaceae',
        'zarandaja':'Fabaceae'
    }
    for profile in profiles:
        profile['familia_botanica'] = family_by_crop.get(canonical_crop(profile['cultivo']), '')
    drap_families = {
        'aji':'Solanaceae','ajo':'Amaryllidaceae','alfalfa':'Fabaceae','algodon':'Malvaceae','arroz':'Poaceae',
        'betarraga':'Amaranthaceae','cana de azucar (para alcohol)':'Poaceae','ca a de azucar (para alcohol)':'Poaceae','cacao':'Malvaceae','cafeto':'Rubiaceae',
        'camote':'Convolvulaceae','capuli (prunus serotina ssp. capuli)':'Rosaceae','cebada grano':'Poaceae',
        'cebolla':'Amaryllidaceae','chirimoyo':'Annonaceae','ciruelo (ciruela spondias)':'Anacardiaceae',
        'cocotero':'Arecaceae','col o repollo':'Brassicaceae','granadilla':'Passifloraceae','guanabano':'Annonaceae',
        'guayabo':'Myrtaceae','higuera':'Moraceae','lechuga':'Asteraceae','lima':'Rutaceae','limon dulce':'Rutaceae',
        'lucuma (producto)':'Sapotaceae','lucumo':'Sapotaceae','mamey':'Sapotaceae','mango':'Anacardiaceae',
        'mani para fruta':'Fabaceae','mani fruta':'Fabaceae','maiz choclo':'Poaceae','maracuya':'Passifloraceae','marigold':'Asteraceae',
        'melon':'Cucurbitaceae','nispero':'Rosaceae','oca':'Oxalidaceae','olluco':'Basellaceae','otros pastos':'Poaceae',
        'pacae o guabo':'Fabaceae','papaya':'Caricaceae','pasto elefante':'Poaceae','pasto sudan':'Poaceae',
        'pimiento':'Solanaceae','pitahaya':'Cactaceae','quinua':'Amaranthaceae','rabano':'Brassicaceae',
        'sandia':'Cucurbitaceae','sorgo escobero':'Poaceae','sorgo grano':'Poaceae','soya':'Fabaceae',
        'tamarindo':'Fabaceae','taperiba':'Anacardiaceae','tomate':'Solanaceae','tumbo':'Passifloraceae',
        'platanos y bananas para coccion (m x paradisiaca)':'Musaceae',
        'platanos y bananas para cocci n (m x paradisiaca)':'Musaceae',
        'zanahoria':'Apiaceae',
    }
    profiles_by_canonical = {canonical_crop(row['cultivo']): row for row in profiles}
    for crop in drap_crops:
        profile = profiles_by_canonical.get(crop['profileCrop']) if crop['profileCrop'] else None
        crop['family'] = (profile or {}).get('familia_botanica') or drap_families.get(normalized_text(crop['name']), '')
    soil_units = read_csv('../../piura-data/suelos_bajo_piura_unidades_v2.csv')
    soil_cum = read_csv('../../piura-data/suelos_montero_ayabaca_cum_v2.csv')
    soil_map_units = read_csv('../../piura-data/suelos_bajo_piura_mapunits_v2.csv')
    soil_cum_basins = read_csv('../../piura-data/suelos_cum_cuencas_v1.csv')
    soil_map_catalog = read_csv('../../piura-data/mapas_suelo_piura_catalogo.csv')
    soil_zone_rows = read_csv('../suelos/suelos_piura.csv')
    zone_vars = ['ECe_medida_local','clase_drenaje_local','pH_rango_zona','profundidad_efectiva_enraizamiento',
                 'profundidad_fisica_suelo_HWSD2','profundidad_napa_estacional','pendiente_media_cultivo','pendiente_p90_cultivo',
                 'area_cultivo_pendiente_mayor_2pct','area_cultivo_pendiente_mayor_5pct']
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
        'drapCrops': drap_crops, 'soilCumBasins': soil_cum_basins, 'soilMapCatalog': soil_map_catalog,
        'soilUnits': soil_units, 'soilCum': soil_cum, 'soilMapUnits': soil_map_units,
        'soilZones': soil_zones,
        'counts': {'examples': len(examples), 'candidates': len(rows), 'profiles': len(profiles),
                   'cropSpeciesWithDetails': len(crop_details), 'cropFichaRows': len(crop_rows),
                   'drapCrops': len(drap_crops), 'annualChoices': len(annual_choices),
                   'motorAnnuals': sum(r.get('modulo')=='anual' for r in motor_crop_catalog),
                   'motorPerennials': sum(r.get('modulo')=='perenne' for r in motor_crop_catalog),
                   'soilUnits': len(soil_units), 'soilMapUnits': len(soil_map_units),
                   'soilCumClasses': len(soil_cum), 'soilCumBasinRows': len(soil_cum_basins),
                   'soilMapSources': len(soil_map_catalog), 'evidence': evidence_count},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{OUTPUT.relative_to(ROOT)}: {len(examples)} examples, {len(rows)} alternatives, '
          f'{len(profiles)} profiles, {evidence_count} evidence rows, {OUTPUT.stat().st_size} bytes')


if __name__ == '__main__':
    build()

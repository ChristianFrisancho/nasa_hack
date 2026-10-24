"""Quality checks for the published Piura reference dataset."""
import csv
import gzip
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    'clima_piura_1981_2025.csv.gz': 82180,
    'clima_piura_anual_1981_2025.csv': 225,
    'clima_piura_mensual_1981_2025.csv': 2700,
    'parametros_cultivo_v2.csv': 186,
    'fao56_kc_referencias.csv': 24,
    'fao56_duracion_analogos.csv': 45,
    'nutrientes_cultivo_fao.csv': 23,
    'fao_ky_respuesta_agua.csv': 8,
    'plagas_hospedantes_condiciones_v2.csv': 42,
    'suelos_bajo_piura_unidades_v2.csv': 6,
    'suelos_bajo_piura_mapunits_v2.csv': 27,
    'suelos_montero_ayabaca_cum_v2.csv': 6,
    'matriz_cultivo_suelo_regional_v2.csv': 240,
    'analogos_comparacion_v2.csv': 68,
    'escenarios_ETc_2025_referencia.csv': 210,
    'fuentes_tavily.csv': 568,
}


def records(name):
    path = ROOT / name
    opener = gzip.open if name.endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def verify():
    for name, expected in EXPECTED.items():
        actual = len(records(name))
        assert actual == expected, (name, actual, expected)
    schema = json.loads((ROOT / 'model_inputs_v2.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    climate = records('clima_piura_1981_2025.csv.gz')
    assert len({(r['zone'], r['date']) for r in climate}) == len(climate)
    assert len({r['zone'] for r in climate}) == 5
    assert all(not r['ET0_approx_mm_day'] for r in climate if r['date'] < '1984-01-01')
    parameters = records('parametros_cultivo_v2.csv')
    assert len({r['parameter_key'] for r in parameters}) == len(parameters)
    analogs = records('analogos_comparacion_v2.csv')
    assert all(r['match_status'] == 'not_mergeable_missing_covariates' for r in analogs)
    assert all(not r['Piura_observed_value'] and not r['donor_minus_Piura'] for r in analogs)
    scenarios = records('escenarios_ETc_2025_referencia.csv')
    assert all(r['gross_irrigation_m3_ha'] == 'unknown' for r in scenarios)
    rice = [r for r in scenarios if r['crop'] == 'arroz' and
            r['zone_NASA'] == 'Bajo Piura - referencia regional' and
            r['start_date_hypothetical'] == '2025-01-01' and r['Kc_band'] == 'min']
    assert len(rice) == 1 and abs(float(rice[0]['ETc_reference_mm']) - 1020.4) < .1
    assert all(r['source_url'].startswith('https://') for r in parameters)
    print(f'OK: {len(EXPECTED)} datasets, schema, provenance flags, no fabricated field measurements')


if __name__ == '__main__':
    verify()

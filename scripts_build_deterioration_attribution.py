import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('.')
MANIFEST_FILE = ROOT / 'dashboard_manifest.json'
INPUTS_FILE = ROOT / 'dashboard_deterioration_attribution_inputs.csv'
OUTPUT_FILE = ROOT / 'dashboard_deterioration_attribution.json'
DEFLACTOR_FILE = ROOT / 'deflactor_mensual.csv'

FIELDS = [
    'province','period','income_total_current_millions','income_total_prev_year_millions',
    'auto_transfers_current_millions','auto_transfers_prev_year_millions',
    'tna_expected_current_millions','tna_received_current_millions',
    'own_base_proxy_current_millions','own_base_proxy_prev_year_millions',
    'primary_expenditure_current_millions','primary_expenditure_prev_year_millions',
    'macro_proxy_method','status','notes'
]


def to_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == '' or s.lower() == 'null':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def read_manifest():
    with MANIFEST_FILE.open(encoding='utf-8') as f:
        return json.load(f)


def ensure_inputs(manifest):
    if INPUTS_FILE.exists():
        return
    rows = []
    for province in manifest.get('province_universe', []):
        rows.append({
            'province': province,
            'period': '2026-03',
            'income_total_current_millions': '',
            'income_total_prev_year_millions': '',
            'auto_transfers_current_millions': '',
            'auto_transfers_prev_year_millions': '',
            'tna_expected_current_millions': '',
            'tna_received_current_millions': '',
            'own_base_proxy_current_millions': '',
            'own_base_proxy_prev_year_millions': '',
            'primary_expenditure_current_millions': '',
            'primary_expenditure_prev_year_millions': '',
            'macro_proxy_method': '',
            'status': 'missing',
            'notes': 'Plantilla inicial. Completar con fuente homogénea mensual para habilitar cálculo auditable.'
        })
    with INPUTS_FILE.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def read_deflator():
    if not DEFLACTOR_FILE.exists():
        return {}
    out = {}
    with DEFLACTOR_FILE.open(encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            p = (r.get('period') or '').strip()
            out[p] = to_float(r.get('factor_to_latest'))
    return out


def deflate(v, period, factors):
    if v is None:
        return None
    factor = factors.get(period)
    if factor is None:
        return None
    return v * factor


def bar_status(value, valid):
    if not valid:
        return 'missing'
    return 'ok' if value is not None else 'missing'


def compute_row(row, factors):
    period = (row.get('period') or '').strip()
    if not period or len(period) != 7 or '-' not in period:
        return None
    year, month = period.split('-')
    if not year.isdigit() or not month.isdigit():
        return None
    prev_period = f"{int(year)-1:04d}-{month}"

    vals = {k: to_float(row.get(k)) for k in FIELDS if k.endswith('_millions')}

    real = {
        'income_curr': deflate(vals['income_total_current_millions'], period, factors),
        'income_prev': deflate(vals['income_total_prev_year_millions'], prev_period, factors),
        'auto_curr': deflate(vals['auto_transfers_current_millions'], period, factors),
        'auto_prev': deflate(vals['auto_transfers_prev_year_millions'], prev_period, factors),
        'tna_exp': deflate(vals['tna_expected_current_millions'], period, factors),
        'tna_rec': deflate(vals['tna_received_current_millions'], period, factors),
        'own_curr': deflate(vals['own_base_proxy_current_millions'], period, factors),
        'own_prev': deflate(vals['own_base_proxy_prev_year_millions'], prev_period, factors),
        'prim_curr': deflate(vals['primary_expenditure_current_millions'], period, factors),
        'prim_prev': deflate(vals['primary_expenditure_prev_year_millions'], prev_period, factors),
    }

    income_curr = real['income_curr']
    income_prev = real['income_prev']
    if income_curr is None or income_curr <= 0:
        return {
            'period': period,
            'status': 'missing',
            'coverage_note': 'Sin dato suficiente. Faltan ingresos comparables deflactados para el período.',
            'bars': {
                'nation_effect_pct_income': {'value': None, 'status': 'missing', 'source': [INPUTS_FILE.name]},
                'macro_effect_pct_income': {'value': None, 'status': 'missing', 'source': [INPUTS_FILE.name]},
                'management_effect_pct_income': {'value': None, 'status': 'missing', 'source': [INPUTS_FILE.name]},
            },
            'inputs_used': {
                'income_total_current_millions': vals['income_total_current_millions'],
                'income_total_prev_year_millions': vals['income_total_prev_year_millions'],
                'auto_transfers_current_millions': vals['auto_transfers_current_millions'],
                'auto_transfers_prev_year_millions': vals['auto_transfers_prev_year_millions'],
                'tna_expected_current_millions': vals['tna_expected_current_millions'],
                'tna_received_current_millions': vals['tna_received_current_millions'],
                'own_base_proxy_current_millions': vals['own_base_proxy_current_millions'],
                'own_base_proxy_prev_year_millions': vals['own_base_proxy_prev_year_millions'],
                'primary_expenditure_current_millions': vals['primary_expenditure_current_millions'],
                'primary_expenditure_prev_year_millions': vals['primary_expenditure_prev_year_millions'],
                'macro_proxy_method': (row.get('macro_proxy_method') or None),
            }
        }

    nation_valid = all(v is not None for v in [real['auto_prev'], real['auto_curr'], real['tna_exp'], real['tna_rec']])
    macro_valid = all(v is not None for v in [real['own_prev'], real['own_curr']])
    mgmt_valid = all(v is not None for v in [real['prim_curr'], real['prim_prev'], income_prev]) and income_prev and income_prev > 0

    nation = None
    if nation_valid:
        nation_loss = max(0.0, real['auto_prev'] - real['auto_curr']) + max(0.0, real['tna_exp'] - real['tna_rec'])
        nation = round((nation_loss / income_curr) * 100, 1)

    macro = None
    if macro_valid:
        macro_loss = max(0.0, real['own_prev'] - real['own_curr'])
        macro = round((macro_loss / income_curr) * 100, 1)

    management = None
    if mgmt_valid:
        management_excess = max(0.0, real['prim_curr'] - real['prim_prev'] * (income_curr / income_prev))
        management = round((management_excess / income_curr) * 100, 1)

    statuses = [
        bar_status(nation, nation_valid),
        bar_status(macro, macro_valid),
        bar_status(management, mgmt_valid),
    ]
    non_missing = sum(1 for s in statuses if s != 'missing')
    p_status = 'ok' if non_missing == 3 else ('partial' if non_missing > 0 else 'missing')

    return {
        'period': period,
        'status': p_status,
        'coverage_note': 'Atribución parcial. El bloque depende de disponibilidad homogénea de ingresos, transferencias, proxy macro y gasto primario.' if p_status != 'ok' else 'Cobertura completa para las tres presiones en período homogéneo.',
        'bars': {
            'nation_effect_pct_income': {'value': nation, 'status': bar_status(nation, nation_valid), 'source': [INPUTS_FILE.name]},
            'macro_effect_pct_income': {'value': macro, 'status': bar_status(macro, macro_valid), 'source': [INPUTS_FILE.name]},
            'management_effect_pct_income': {'value': management, 'status': bar_status(management, mgmt_valid), 'source': [INPUTS_FILE.name]},
        },
        'inputs_used': {
            'income_total_current_millions': vals['income_total_current_millions'],
            'income_total_prev_year_millions': vals['income_total_prev_year_millions'],
            'auto_transfers_current_millions': vals['auto_transfers_current_millions'],
            'auto_transfers_prev_year_millions': vals['auto_transfers_prev_year_millions'],
            'tna_expected_current_millions': vals['tna_expected_current_millions'],
            'tna_received_current_millions': vals['tna_received_current_millions'],
            'own_base_proxy_current_millions': vals['own_base_proxy_current_millions'],
            'own_base_proxy_prev_year_millions': vals['own_base_proxy_prev_year_millions'],
            'primary_expenditure_current_millions': vals['primary_expenditure_current_millions'],
            'primary_expenditure_prev_year_millions': vals['primary_expenditure_prev_year_millions'],
            'macro_proxy_method': (row.get('macro_proxy_method') or None),
        }
    }


def build_output(manifest):
    factors = read_deflator()
    provinces = defaultdict(list)
    with INPUTS_FILE.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            provinces[(row.get('province') or '').strip()].append(row)

    payload = {
        'source': 'bloque atribución del deterioro',
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'methodology': {
            'unit': 'pct_of_current_income',
            'nation_effect': 'max(0, auto_transfers_prev_real - auto_transfers_current_real) + max(0, tna_expected_current_real - tna_received_current_real), todo dividido por income_total_current_real * 100',
            'macro_effect': 'max(0, own_base_proxy_prev_real - own_base_proxy_current_real), dividido por income_total_current_real * 100',
            'management_effect': 'max(0, primary_expenditure_current_real - primary_expenditure_prev_real * (income_total_current_real / income_total_prev_real)), dividido por income_total_current_real * 100'
        },
        'provinces': {}
    }

    for province in manifest.get('province_universe', []):
        rows = sorted(provinces.get(province, []), key=lambda r: (r.get('period') or ''))
        chosen = rows[-1] if rows else {'province': province, 'period': '2026-03'}
        result = compute_row(chosen, factors)
        if result is None:
            result = {
                'period': '2026-03',
                'status': 'missing',
                'coverage_note': 'Sin dato suficiente. No hay período válido en la capa de inputs.',
                'bars': {
                    'nation_effect_pct_income': {'value': None, 'status': 'missing', 'source': [INPUTS_FILE.name]},
                    'macro_effect_pct_income': {'value': None, 'status': 'missing', 'source': [INPUTS_FILE.name]},
                    'management_effect_pct_income': {'value': None, 'status': 'missing', 'source': [INPUTS_FILE.name]},
                },
                'inputs_used': {
                    'income_total_current_millions': None,
                    'income_total_prev_year_millions': None,
                    'auto_transfers_current_millions': None,
                    'auto_transfers_prev_year_millions': None,
                    'tna_expected_current_millions': None,
                    'tna_received_current_millions': None,
                    'own_base_proxy_current_millions': None,
                    'own_base_proxy_prev_year_millions': None,
                    'primary_expenditure_current_millions': None,
                    'primary_expenditure_prev_year_millions': None,
                    'macro_proxy_method': None
                }
            }
        payload['provinces'][province] = result

    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    manifest = read_manifest()
    ensure_inputs(manifest)
    build_output(manifest)


if __name__ == '__main__':
    main()

import csv
import json
from datetime import datetime, timezone

CROSS_FILE = 'dashboard_cross_section_1816.json'
BUDGET_FILE = 'budget_anchors_pba_2026.json'
SCENARIOS_INPUTS_FILE = 'dashboard_scenarios_inputs.csv'
OUTPUT_FILE = 'dashboard_liquidity_risk.json'


def round1(value):
    return round(float(value), 1)


def to_float(value):
    if value is None:
        return None
    txt = str(value).strip()
    if txt == '':
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def pick_base_scenario_inputs(province='Buenos Aires'):
    try:
        with open(SCENARIOS_INPUTS_FILE, encoding='utf-8', newline='') as f:
            rows = [r for r in csv.DictReader(f) if (r.get('province') or '').strip() == province and (r.get('scenario_name') or '').strip() == 'Base']
    except FileNotFoundError:
        return None, None

    if not rows:
        return None, None

    rows = sorted(rows, key=lambda r: (r.get('as_of_date') or '', r.get('horizon_days') or ''))
    row_90 = next((r for r in reversed(rows) if (r.get('horizon_days') or '').strip() == '90'), None)
    row_180 = next((r for r in reversed(rows) if (r.get('horizon_days') or '').strip() == '180'), None)
    row_latest = row_90 or row_180
    return row_latest, row_180


def build():
    with open(CROSS_FILE, encoding='utf-8') as f:
        cross = json.load(f).get('provinces', {})

    with open(BUDGET_FILE, encoding='utf-8') as f:
        budget = json.load(f)

    pba_cross = cross.get('Buenos Aires', {})
    rp = pba_cross.get('resultado_primario_ltm_pct')
    rf = pba_cross.get('resultado_financiero_ltm_pct')

    intereses_sobre_ingresos = None
    if rp is not None and rf is not None:
        intereses_sobre_ingresos = round1(rp - rf)

    row_base, row_180 = pick_base_scenario_inputs('Buenos Aires')
    caja_disponible = to_float(row_base.get('cash_start_millions')) * 1_000_000 if row_base and to_float(row_base.get('cash_start_millions')) is not None else None
    aguinaldo = to_float(row_base.get('expected_aguinaldo_outflow_millions')) * 1_000_000 if row_base and to_float(row_base.get('expected_aguinaldo_outflow_millions')) is not None else None
    cobertura_aguinaldo = round1((caja_disponible / aguinaldo) * 100) if caja_disponible is not None and aguinaldo not in (None, 0) else None
    venc_90 = to_float(row_base.get('expected_debt_maturities_millions')) * 1_000_000 if row_base and to_float(row_base.get('expected_debt_maturities_millions')) is not None else None
    venc_180 = to_float(row_180.get('expected_debt_maturities_millions')) * 1_000_000 if row_180 and to_float(row_180.get('expected_debt_maturities_millions')) is not None else None

    payload = {
        'source': 'capa liquidez y riesgo inmediato',
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'methodology': {
            'intereses_sobre_ingresos': 'resultado_primario_ltm_pct - resultado_financiero_ltm_pct',
            'ahorro_corriente': 'manual_or_external_source',
            'caja_disponible': 'manual_or_external_source',
            'cobertura_aguinaldo': 'manual_or_external_source',
            'vencimientos_90d': 'manual_or_external_source',
            'vencimientos_180d': 'manual_or_external_source',
        },
        'provinces': {
            'Buenos Aires': {
                'as_of': '2026-03',
                'coverage_note': (
                    'Bloque parcial. El repo actual permite derivar intereses/ingresos y anclas '
                    'presupuestarias, pero no trae aún caja, aguinaldo ni perfil de vencimientos '
                    'en formato normalizado.'
                ),
                'metrics': {
                    'ahorro_corriente_pct': {
                        'value': None,
                        'unit': 'pct',
                        'status': 'missing',
                        'source': None,
                    },
                    'intereses_sobre_ingresos_pct': {
                        'value': intereses_sobre_ingresos,
                        'unit': 'pct',
                        'status': 'derived',
                        'source': 'dashboard_cross_section_1816.json',
                    },
                    'caja_disponible_pesos': {
                        'value': caja_disponible,
                        'unit': 'ars',
                        'status': 'source' if caja_disponible is not None else 'missing',
                        'source': SCENARIOS_INPUTS_FILE if caja_disponible is not None else None,
                    },
                    'cobertura_aguinaldo_pct': {
                        'value': cobertura_aguinaldo,
                        'unit': 'pct',
                        'status': 'derived' if cobertura_aguinaldo is not None else 'missing',
                        'source': SCENARIOS_INPUTS_FILE if cobertura_aguinaldo is not None else None,
                    },
                    'vencimientos_90d_pesos': {
                        'value': venc_90,
                        'unit': 'ars',
                        'status': 'source' if venc_90 is not None else 'missing',
                        'source': SCENARIOS_INPUTS_FILE if venc_90 is not None else None,
                    },
                    'vencimientos_180d_pesos': {
                        'value': venc_180,
                        'unit': 'ars',
                        'status': 'source' if venc_180 is not None else 'missing',
                        'source': SCENARIOS_INPUTS_FILE if venc_180 is not None else None,
                    },
                    'necesidad_financiamiento_presupuestada_pesos': {
                        'value': budget.get('necesidad_financiamiento_pesos'),
                        'unit': 'ars',
                        'status': 'source',
                        'source': 'budget_anchors_pba_2026.json',
                    },
                    'fuentes_financieras_presupuestadas_pesos': {
                        'value': budget.get('fuentes_financieras_pesos'),
                        'unit': 'ars',
                        'status': 'source',
                        'source': 'budget_anchors_pba_2026.json',
                    },
                    'aplicaciones_financieras_presupuestadas_pesos': {
                        'value': budget.get('aplicaciones_financieras_pesos'),
                        'unit': 'ars',
                        'status': 'source',
                        'source': 'budget_anchors_pba_2026.json',
                    },
                },
            }
        },
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')


if __name__ == '__main__':
    build()

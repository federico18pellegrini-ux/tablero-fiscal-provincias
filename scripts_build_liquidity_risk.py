import json
from datetime import datetime, timezone

CROSS_FILE = 'dashboard_cross_section_1816.json'
BUDGET_FILE = 'budget_anchors_pba_2026.json'
OUTPUT_FILE = 'dashboard_liquidity_risk.json'


def round1(value):
    return round(float(value), 1)


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
                        'value': None,
                        'unit': 'ars',
                        'status': 'missing',
                        'source': None,
                    },
                    'cobertura_aguinaldo_pct': {
                        'value': None,
                        'unit': 'pct',
                        'status': 'missing',
                        'source': None,
                    },
                    'vencimientos_90d_pesos': {
                        'value': None,
                        'unit': 'ars',
                        'status': 'missing',
                        'source': None,
                    },
                    'vencimientos_180d_pesos': {
                        'value': None,
                        'unit': 'ars',
                        'status': 'missing',
                        'source': None,
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

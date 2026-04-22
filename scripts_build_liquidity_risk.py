import csv
import json
from datetime import datetime, timezone

CROSS_FILE = 'dashboard_cross_section_1816.json'
BUDGET_FILE = 'budget_anchors_pba_2026.json'
LIQUIDITY_INPUTS_FILE = 'dashboard_liquidity_risk_inputs.csv'
PBA_RON_MONTHLY_FILE = 'pba_ron_monthly.csv'
PBA_RON_DAILY_FILE = 'pba_ron_daily.csv'
PBA_BUDGET_QUARTERLY_FILE = 'pba_budget_execution_quarterly.csv'
NATIONAL_DEBT_MONTHLY_FILE = 'national_debt_monthly.csv'
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


def pick_liquidity_inputs(province='Buenos Aires'):
    try:
        with open(LIQUIDITY_INPUTS_FILE, encoding='utf-8', newline='') as f:
            rows = [r for r in csv.DictReader(f) if (r.get('province') or '').strip() == province]
    except FileNotFoundError:
        return None

    if not rows:
        return None

    rows = sorted(rows, key=lambda r: (r.get('as_of') or ''))
    return rows[-1]


def month_from_date(raw):
    txt = (raw or '').strip()
    return txt[:7] if len(txt) >= 7 else ''


def read_csv_optional(path):
    try:
        with open(path, encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


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

    row_base = pick_liquidity_inputs('Buenos Aires')
    caja_disponible = to_float(row_base.get('caja_disponible_pesos')) if row_base and to_float(row_base.get('caja_disponible_pesos')) is not None else None
    aguinaldo = to_float(row_base.get('aguinaldo_estimado_pesos')) if row_base and to_float(row_base.get('aguinaldo_estimado_pesos')) is not None else None
    cobertura_aguinaldo = round1((caja_disponible / aguinaldo) * 100) if caja_disponible is not None and aguinaldo not in (None, 0) else None
    venc_90 = to_float(row_base.get('vencimientos_90d_pesos')) if row_base and to_float(row_base.get('vencimientos_90d_pesos')) is not None else None
    venc_180 = to_float(row_base.get('vencimientos_180d_pesos')) if row_base and to_float(row_base.get('vencimientos_180d_pesos')) is not None else None

    ron_monthly_rows = read_csv_optional(PBA_RON_MONTHLY_FILE)
    ron_daily_rows = read_csv_optional(PBA_RON_DAILY_FILE)
    budget_quarterly_rows = read_csv_optional(PBA_BUDGET_QUARTERLY_FILE)
    national_debt_rows = read_csv_optional(NATIONAL_DEBT_MONTHLY_FILE)

    ron_monthly_sorted = sorted(ron_monthly_rows, key=lambda r: r.get('fecha_corte') or '')
    latest_ron_month = None
    latest_ron_month_xlsx = None
    for row in reversed(ron_monthly_sorted):
        if latest_ron_month is None and (
            to_float(row.get('total_ron_ars_m_xlsx')) is not None or to_float(row.get('total_ron_ars_m_daily')) is not None
        ):
            latest_ron_month = row
        if latest_ron_month_xlsx is None and to_float(row.get('total_ron_ars_m_xlsx')) is not None:
            latest_ron_month_xlsx = row
        if latest_ron_month is not None and latest_ron_month_xlsx is not None:
            break
    latest_budget = sorted(budget_quarterly_rows, key=lambda r: r.get('fecha_corte') or '')[-1] if budget_quarterly_rows else None
    latest_period = month_from_date((latest_ron_month or {}).get('fecha_corte'))
    latest_xlsx_period = month_from_date((latest_ron_month_xlsx or {}).get('fecha_corte'))
    ron_monthly_xlsx = to_float((latest_ron_month_xlsx or {}).get('total_ron_ars_m_xlsx'))
    ron_monthly_daily = to_float((latest_ron_month or {}).get('total_ron_ars_m_daily'))
    ron_monthly_daily_same_period = None
    if latest_xlsx_period:
        for row in ron_daily_rows:
            if month_from_date(row.get('fecha')) != latest_xlsx_period:
                continue
            val = to_float(row.get('total_ron_ars_m'))
            if val is None:
                continue
            ron_monthly_daily_same_period = (ron_monthly_daily_same_period or 0.0) + val
    ron_monthly_diff = (
        ron_monthly_xlsx - ron_monthly_daily_same_period
        if (ron_monthly_xlsx is not None and ron_monthly_daily_same_period is not None)
        else None
    )
    ron_daily_acc = 0.0
    ron_daily_count = 0
    for row in ron_daily_rows:
        if month_from_date(row.get('fecha')) != latest_period:
            continue
        val = to_float(row.get('total_ron_ars_m'))
        if val is None:
            continue
        ron_daily_acc += val
        ron_daily_count += 1
    ron_daily_total_month = ron_daily_acc if ron_daily_count else None
    resultado_financiero_trim = to_float((latest_budget or {}).get('resultado_financiero_ars_m'))
    debt_rows_2026 = sorted(
        [r for r in national_debt_rows if (r.get('fecha_corte') or '').startswith('2026-')],
        key=lambda r: r.get('fecha_corte') or ''
    )
    latest_debt_row = debt_rows_2026[-1] if debt_rows_2026 else None
    deuda_fx_pct = to_float((latest_debt_row or {}).get('pct_moneda_extranjera'))
    pagos_mes_ytd_usd = sum(to_float(r.get('pagos_mes_usd_m')) or 0.0 for r in debt_rows_2026)
    pagos_capital_ytd_usd = sum(to_float(r.get('pagos_capital_usd_m')) or 0.0 for r in debt_rows_2026)
    pagos_intereses_ytd_usd = sum(to_float(r.get('pagos_intereses_usd_m')) or 0.0 for r in debt_rows_2026)
    servicios_total_usd = pagos_mes_ytd_usd * 1_000_000 if pagos_mes_ytd_usd > 0 else None
    servicios_intereses_pct = round1((pagos_intereses_ytd_usd / pagos_mes_ytd_usd) * 100) if pagos_mes_ytd_usd > 0 else None
    servicios_amort_pct = round1((pagos_capital_ytd_usd / pagos_mes_ytd_usd) * 100) if pagos_mes_ytd_usd > 0 else None

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
                'ron_mensual_vs_diario': 'validación de consistencia entre fuentes mensual y acumulado diario',
                'resultado_financiero_trimestral': 'proxy de presión de caja cuando no hay caja bancaria auditada',
            },
        'provinces': {
            'Buenos Aires': {
                'as_of': '2026-03',
                'coverage_note': (
                    'Bloque parcial. El repositorio permite derivar intereses/ingresos y anclas '
                    'presupuestarias. Se incorporan referencias nacionales para moneda y servicios de deuda. '
                    'Para habilitar semáforo completo se requiere carga auditada en '
                    'dashboard_liquidity_risk_inputs.csv.'
                ),
                'metrics': {
                    'ahorro_corriente_pct': {
                        'value': None,
                        'unit': 'pct',
                        'status': 'missing',
                        'source': None,
                        'missing_detail': 'pendiente_integracion',
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
                        'source': LIQUIDITY_INPUTS_FILE if caja_disponible is not None else None,
                        'missing_detail': None if caja_disponible is not None else 'no_cargado_fuente_auditada',
                    },
                    'cobertura_aguinaldo_pct': {
                        'value': cobertura_aguinaldo,
                        'unit': 'pct',
                        'status': 'derived' if cobertura_aguinaldo is not None else 'missing',
                        'source': LIQUIDITY_INPUTS_FILE if cobertura_aguinaldo is not None else None,
                        'missing_detail': None if cobertura_aguinaldo is not None else 'no_derivable_respaldo_suficiente',
                    },
                    'vencimientos_90d_pesos': {
                        'value': venc_90,
                        'unit': 'ars',
                        'status': 'source' if venc_90 is not None else 'missing',
                        'source': LIQUIDITY_INPUTS_FILE if venc_90 is not None else None,
                        'missing_detail': None if venc_90 is not None else 'no_cargado_fuente_auditada',
                    },
                    'vencimientos_180d_pesos': {
                        'value': venc_180,
                        'unit': 'ars',
                        'status': 'source' if venc_180 is not None else 'missing',
                        'source': LIQUIDITY_INPUTS_FILE if venc_180 is not None else None,
                        'missing_detail': None if venc_180 is not None else 'no_cargado_fuente_auditada',
                    },
                    'ron_total_ultimo_mes_xlsx_ars_m': {
                        'value': ron_monthly_xlsx,
                        'unit': 'ars_m',
                        'status': 'source' if ron_monthly_xlsx is not None else 'missing',
                        'source': PBA_RON_MONTHLY_FILE if ron_monthly_xlsx is not None else None,
                        'as_of': latest_xlsx_period or None,
                        'missing_detail': None if ron_monthly_xlsx is not None else 'pendiente_integracion',
                    },
                    'ron_total_ultimo_mes_daily_ars_m': {
                        'value': ron_monthly_daily,
                        'unit': 'ars_m',
                        'status': 'source' if ron_monthly_daily is not None else 'missing',
                        'source': PBA_RON_MONTHLY_FILE if ron_monthly_daily is not None else None,
                    },
                    'ron_total_ultimo_mes_diff_xlsx_daily_ars_m': {
                        'value': ron_monthly_diff,
                        'unit': 'ars_m',
                        'status': 'derived' if ron_monthly_diff is not None else 'missing',
                        'source': f'{PBA_RON_MONTHLY_FILE}+{PBA_RON_DAILY_FILE}' if ron_monthly_diff is not None else None,
                        'as_of': latest_xlsx_period or None,
                        'missing_detail': None if ron_monthly_diff is not None else 'no_derivable_respaldo_suficiente',
                    },
                    'ron_diario_acumulado_ultimo_mes_ars_m': {
                        'value': ron_daily_total_month,
                        'unit': 'ars_m',
                        'status': 'derived' if ron_daily_total_month is not None else 'missing',
                        'source': PBA_RON_DAILY_FILE if ron_daily_total_month is not None else None,
                    },
                    'resultado_financiero_ultimo_trimestre_ars_m': {
                        'value': resultado_financiero_trim,
                        'unit': 'ars_m',
                        'status': 'derived' if resultado_financiero_trim is not None else 'missing',
                        'source': PBA_BUDGET_QUARTERLY_FILE if resultado_financiero_trim is not None else None,
                        'missing_detail': None if resultado_financiero_trim is not None else 'pendiente_integracion',
                    },
                    'deuda_moneda_extranjera_pct': {
                        'value': deuda_fx_pct,
                        'unit': 'pct',
                        'status': 'source' if deuda_fx_pct is not None else 'missing',
                        'source': NATIONAL_DEBT_MONTHLY_FILE if deuda_fx_pct is not None else None,
                        'as_of': month_from_date((latest_debt_row or {}).get('fecha_corte')) or None,
                        'missing_detail': None if deuda_fx_pct is not None else 'no_cargado_fuente_auditada',
                    },
                    'servicios_deuda_acumulados_pesos': {
                        'value': None,
                        'unit': 'ars',
                        'status': 'missing',
                        'source': None,
                        'missing_detail': 'pendiente_integracion',
                    },
                    'servicios_deuda_acumulados_usd': {
                        'value': servicios_total_usd,
                        'unit': 'usd',
                        'status': 'source' if servicios_total_usd is not None else 'missing',
                        'source': NATIONAL_DEBT_MONTHLY_FILE if servicios_total_usd is not None else None,
                        'as_of': month_from_date((latest_debt_row or {}).get('fecha_corte')) or None,
                        'missing_detail': None if servicios_total_usd is not None else 'no_cargado_fuente_auditada',
                    },
                    'servicios_intereses_pct': {
                        'value': servicios_intereses_pct,
                        'unit': 'pct',
                        'status': 'source' if servicios_intereses_pct is not None else 'missing',
                        'source': NATIONAL_DEBT_MONTHLY_FILE if servicios_intereses_pct is not None else None,
                        'as_of': month_from_date((latest_debt_row or {}).get('fecha_corte')) or None,
                        'missing_detail': None if servicios_intereses_pct is not None else 'no_cargado_fuente_auditada',
                    },
                    'servicios_amortizacion_pct': {
                        'value': servicios_amort_pct,
                        'unit': 'pct',
                        'status': 'source' if servicios_amort_pct is not None else 'missing',
                        'source': NATIONAL_DEBT_MONTHLY_FILE if servicios_amort_pct is not None else None,
                        'as_of': month_from_date((latest_debt_row or {}).get('fecha_corte')) or None,
                        'missing_detail': None if servicios_amort_pct is not None else 'no_cargado_fuente_auditada',
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

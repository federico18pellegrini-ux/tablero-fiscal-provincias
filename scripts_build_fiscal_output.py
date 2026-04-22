import csv
import json
from collections import defaultdict
from datetime import datetime, timezone

MANIFEST_FILE = 'dashboard_manifest.json'
CROSS_FILE = 'dashboard_cross_section_1816.json'
TOP_MENSUAL_FILE = 'top_mensual_2026_normalizado.csv'
INFO_2026_FILE = 'informacion_consolidada_2026_normalizado.csv'
SERIE_RON_FILE = 'serie_ron_2003_2025_normalizado.csv'
PBA_TOP_MONTHLY_FILE = 'pba_top_monthly.csv'
PBA_RON_MONTHLY_FILE = 'pba_ron_monthly.csv'
PBA_BUDGET_QUARTERLY_FILE = 'pba_budget_execution_quarterly.csv'
NATIONAL_DEBT_MONTHLY_FILE = 'national_debt_monthly.csv'
MUNICIPIOS_PBA_ANNUAL_FILE = 'municipios_pba_annual.csv'
OUTPUT_FILE = 'dashboard_fiscal_provincias.json'
RECLAMOS_FILE = 'dashboard_reclamos_nacion_provincias.json'

PROVINCE_MAP = {
    'C.A.B.A.': 'CABA',
    'C.A.B.A': 'CABA',
    'Ciudad Autónoma de Buenos Aires': 'CABA',
    'Sgo. del Estero': 'Santiago del Estero',
    'Sgo Del Estero': 'Santiago del Estero',
    'Stgo. del Estero': 'Santiago del Estero',
    'Tierra del Fuego, Antártida e Islas del Atlántico Sur': 'Tierra del Fuego',
}

YEAR_DEFLATOR = {
    2023: 3.8032155238550325,
    2024: 1.4297180188843337,
    2025: 1.088488548,
    2026: 1.0,
}


def normalize(name: str) -> str:
    key = (name or '').strip()
    return PROVINCE_MAP.get(key, key)


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def read_csv_optional(path):
    try:
        return read_csv(path)
    except FileNotFoundError:
        return []


def month_from_date(raw):
    txt = (raw or '').strip()
    return txt[:7] if len(txt) >= 7 else ''


def classify_dependencia(value):
    if value is None:
        return 'media'
    pct = value * 100
    if pct >= 60:
        return 'alta'
    if pct < 40:
        return 'baja'
    return 'media'


def classify_estres(score):
    if score is None:
        return 'medio'
    if score >= 0.30:
        return 'alto'
    if score >= 0.15:
        return 'medio'
    return 'bajo'


def classify_rigidez(gasto_personal_ratio):
    if gasto_personal_ratio is None:
        return 'intermedio'
    if gasto_personal_ratio >= 0.55:
        return 'rígido'
    if gasto_personal_ratio <= 0.45:
        return 'flexible'
    return 'intermedio'


def classify_riesgo_aguinaldo(meses_cobertura):
    if meses_cobertura is None:
        return 'medio'
    if meses_cobertura < 1:
        return 'alto'
    if meses_cobertura < 2:
        return 'medio'
    return 'bajo'


def classify_semaforo(resultado_ratio, ahorro_ratio):
    if resultado_ratio is None or ahorro_ratio is None:
        return 'amarillo'
    if resultado_ratio < -0.05 and ahorro_ratio < 0:
        return 'rojo'
    if -0.05 <= resultado_ratio <= -0.01:
        return 'amarillo'
    return 'verde'


def classify_level(value, high=-5, medium=-1):
    if value is None:
        return 'medio'
    if value <= high:
        return 'alto'
    if value <= medium:
        return 'medio'
    return 'bajo'


def annual_real_variation(series_by_year):
    # prefer 2025 vs 2024, fallback to latest two years
    years = sorted(y for y, v in series_by_year.items() if v is not None)
    pair = None
    if 2024 in series_by_year and 2025 in series_by_year:
        pair = (2024, 2025)
    elif len(years) >= 2:
        pair = (years[-2], years[-1])
    if not pair:
        return None
    y0, y1 = pair
    v0 = series_by_year.get(y0)
    v1 = series_by_year.get(y1)
    if not v0 or v1 is None:
        return None
    r0 = v0 * YEAR_DEFLATOR.get(y0, 1.0)
    r1 = v1 * YEAR_DEFLATOR.get(y1, 1.0)
    if r0 == 0:
        return None
    return ((r1 / r0) - 1) * 100


def classify_deterioro(coparticipacion_var, ingresos_var, propia_var, resultado_ratio, gasto_personal_ratio):
    nacion = 'alto' if (coparticipacion_var is not None and coparticipacion_var <= -5) else ('medio' if coparticipacion_var is not None and coparticipacion_var < -1 else 'bajo')

    gasto_presion = (resultado_ratio is not None and resultado_ratio < -0.01 and (gasto_personal_ratio or 0) >= 0.50)
    provincia = 'alto' if gasto_presion else 'medio'

    ambos_caen = (ingresos_var is not None and propia_var is not None and ingresos_var < -1 and propia_var < -1)
    macro = 'alto' if ambos_caen else 'medio'

    return {
        'nacion': nacion,
        'provincia': provincia,
        'macro': macro,
    }


def pick_main_driver(deterioro):
    if not deterioro:
        return 'macro'
    order = ['nacion', 'provincia', 'macro']
    score = {'alto': 3, 'medio': 2, 'bajo': 1}
    return sorted(order, key=lambda k: score.get(deterioro.get(k, 'medio'), 2), reverse=True)[0]


def fmt_pct(value):
    if value is None:
        return 'N/D'
    return f'{value*100:.1f}%'


def build():
    with open(MANIFEST_FILE, encoding='utf-8') as f:
        manifest = json.load(f)
    universe = [normalize(p) for p in manifest.get('province_universe', [])]

    with open(CROSS_FILE, encoding='utf-8') as f:
        cross = json.load(f).get('provinces', {})
    try:
        with open(RECLAMOS_FILE, encoding='utf-8') as f:
            reclamos_payload = json.load(f)
    except FileNotFoundError:
        reclamos_payload = {'provinces': {}, 'methodology': {}, 'integration_ready': {}}
    reclamos_by_province = reclamos_payload.get('provinces', {})

    top_rows = read_csv(TOP_MENSUAL_FILE)
    pba_top_rows = read_csv_optional(PBA_TOP_MONTHLY_FILE)
    info_rows = read_csv(INFO_2026_FILE)
    pba_ron_monthly_rows = read_csv_optional(PBA_RON_MONTHLY_FILE)
    ron_rows = read_csv(SERIE_RON_FILE)
    pba_budget_rows = read_csv_optional(PBA_BUDGET_QUARTERLY_FILE)
    national_debt_rows = read_csv_optional(NATIONAL_DEBT_MONTHLY_FILE)
    municipios_pba_rows = read_csv_optional(MUNICIPIOS_PBA_ANNUAL_FILE)

    top_2026 = defaultdict(float)
    info_nacional_2026 = defaultdict(float)
    info_tna_2026 = defaultdict(float)

    for row in top_rows:
        prov = normalize(row.get('province'))
        if row.get('period', '').startswith('2026-'):
            top_2026[prov] += to_float(row.get('value_millions')) or 0.0

    for row in info_rows:
        prov = normalize(row.get('province'))
        period = row.get('period', '')
        cat = (row.get('category_normalized') or row.get('category') or '').strip()
        if not period.startswith('2026-'):
            continue
        val = to_float(row.get('value_millions')) or 0.0
        if cat == 'Total | Recursos | Origen Nacional | (1)':
            info_nacional_2026[prov] += val
        if cat == 'Compensación Consenso Fiscal':
            info_tna_2026[prov] += val

    pba_top_total_2026 = 0.0
    for row in pba_top_rows:
        period = month_from_date(row.get('fecha_corte'))
        if not period.startswith('2026-'):
            continue
        total = to_float(row.get('top_total_ars_m'))
        if total is not None:
            pba_top_total_2026 += total
    if pba_top_total_2026 > 0:
        top_2026['Buenos Aires'] = pba_top_total_2026

    pba_total_nacional_2026 = 0.0
    pba_comp_2026 = 0.0
    for row in pba_ron_monthly_rows:
        period = month_from_date(row.get('fecha_corte'))
        if not period.startswith('2026-'):
            continue
        total = to_float(row.get('total_ron_ars_m_xlsx'))
        if total is None:
            total = to_float(row.get('total_ron_ars_m_daily'))
        comp = to_float(row.get('compensacion_consenso_fiscal_ars_m_xlsx'))
        if comp is None:
            comp = to_float(row.get('compensacion_consenso_fiscal_ars_m_daily'))
        if total is not None:
            pba_total_nacional_2026 += total
        if comp is not None:
            pba_comp_2026 += comp
    if pba_total_nacional_2026 > 0:
        info_nacional_2026['Buenos Aires'] = pba_total_nacional_2026
        info_tna_2026['Buenos Aires'] = pba_comp_2026

    ron_by_prov_cat_year = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for row in ron_rows:
        prov = normalize(row.get('province'))
        year = int(row['year']) if str(row.get('year', '')).isdigit() else None
        if year is None:
            continue
        cat = (row.get('category_normalized') or row.get('category') or '').strip()
        ron_by_prov_cat_year[prov][cat][year] += to_float(row.get('value_millions')) or 0.0

    latest_budget_quarter = sorted(pba_budget_rows, key=lambda r: r.get('fecha_corte') or '')[-1] if pba_budget_rows else None
    latest_debt_nation = sorted(national_debt_rows, key=lambda r: r.get('fecha_corte') or '')[-1] if national_debt_rows else None
    latest_municipios = sorted(municipios_pba_rows, key=lambda r: r.get('fecha_corte') or '')[-1] if municipios_pba_rows else None

    payload = {
        'source': 'pipeline_fiscal_v2',
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'integrations': {
            'reclamos_nacion': {
                'source_file': RECLAMOS_FILE,
                'selector_keys': (reclamos_payload.get('integration_ready') or {}).get('selector_keys', ['deuda_total_reclamada', 'deuda_total_robusta']),
                'future_block_key': (reclamos_payload.get('integration_ready') or {}).get('future_block_key', 'deuda_nacion_con_provincia'),
                'methodology_note': (
                    (reclamos_payload.get('methodology') or {}).get('deuda_total_robusta')
                    or 'deuda_total_robusta incluye solo observado/estimado_robusto.'
                ),
            }
        },
        'provinces': {}
    }

    for province in universe:
        base = dict(cross.get(province, {}))

        recaudacion_propia_2026 = top_2026.get(province, 0.0)
        impuestos_nacionales = max(info_nacional_2026.get(province, 0.0) - info_tna_2026.get(province, 0.0), 0.0)
        transferencias_no_auto = info_tna_2026.get(province, 0.0)
        ingresos_totales = recaudacion_propia_2026 + info_nacional_2026.get(province, 0.0)

        dependencia_nacion = None
        if ingresos_totales > 0:
            dependencia_nacion = (impuestos_nacionales + transferencias_no_auto) / ingresos_totales
        else:
            autonomia = to_float(base.get('autonomia_fiscal_pct'))
            if autonomia is not None:
                dependencia_nacion = max(0.0, min(1.0, 1 - (autonomia / 100.0)))

        gasto_personal_ratio = None
        if to_float(base.get('gasto_salarios_gasto_primario_ex_ss_pct')) is not None:
            gasto_personal_ratio = to_float(base.get('gasto_salarios_gasto_primario_ex_ss_pct')) / 100.0

        resultado_ratio = None
        if to_float(base.get('resultado_financiero_ltm_pct')) is not None:
            resultado_ratio = to_float(base.get('resultado_financiero_ltm_pct')) / 100.0

        ahorro_corriente_ratio = resultado_ratio
        ahorro_corriente = ingresos_totales * ahorro_corriente_ratio if (ingresos_totales and ahorro_corriente_ratio is not None) else None

        deuda_sobre_ingresos = None
        if to_float(base.get('deuda_total_sobre_ingresos_pct')) is not None:
            deuda_sobre_ingresos = to_float(base.get('deuda_total_sobre_ingresos_pct')) / 100.0

        stress_rf = max(0.0, -(resultado_ratio or 0.0))
        stress_deuda = max(0.0, deuda_sobre_ingresos or 0.0)
        stress_sueldos = max(0.0, gasto_personal_ratio or 0.0)
        estres_fiscal_score = 0.4 * stress_rf + 0.3 * stress_deuda + 0.3 * stress_sueldos
        estres_fiscal_categoria = classify_estres(estres_fiscal_score)

        meses_cobertura = None
        if ahorro_corriente_ratio is not None:
            # Proxy sin dato de caja: ahorro_corriente / 6 -> aproximado en meses sobre ingreso mensual
            meses_cobertura = ahorro_corriente_ratio * 2
        riesgo_aguinaldo = classify_riesgo_aguinaldo(meses_cobertura)

        total_series = ron_by_prov_cat_year[province].get('Total | (1) + (2)', {})
        copa_series = ron_by_prov_cat_year[province].get('CFI | Neta', {})
        ingresos_totales_var_real = annual_real_variation(total_series)
        coparticipacion_var_real = annual_real_variation(copa_series)
        recaudacion_propia_var_real = None

        deterioro = classify_deterioro(
            coparticipacion_var=coparticipacion_var_real,
            ingresos_var=ingresos_totales_var_real,
            propia_var=recaudacion_propia_var_real,
            resultado_ratio=resultado_ratio,
            gasto_personal_ratio=gasto_personal_ratio,
        )

        semaforo_fiscal = classify_semaforo(resultado_ratio, ahorro_corriente_ratio)
        dependencia_categoria = classify_dependencia(dependencia_nacion)
        rigidez = classify_rigidez(gasto_personal_ratio)

        signo = 'superávit' if (resultado_ratio is not None and resultado_ratio >= 0) else 'déficit'
        driver = pick_main_driver(deterioro)
        mensaje_clave = (
            f"Provincia con {signo} de {fmt_pct(resultado_ratio)}. "
            f"El desequilibrio se explica principalmente por {driver}. "
            f"El gasto es {rigidez} y la dependencia de Nación es {dependencia_categoria}. "
            f"El riesgo de caja es {riesgo_aguinaldo}."
        )

        base.update({
            'semaforo_fiscal': semaforo_fiscal,
            'riesgo_aguinaldo': riesgo_aguinaldo,
            'dependencia_nacion_pct': (dependencia_nacion * 100) if dependencia_nacion is not None else None,
            'gasto_personal_ratio': gasto_personal_ratio,
            'gasto_corriente_ratio': None,
            'ahorro_corriente': ahorro_corriente,
            'ahorro_corriente_ratio': ahorro_corriente_ratio,
            'estres_fiscal_score': estres_fiscal_score,
            'estres_fiscal_categoria': estres_fiscal_categoria,
            'meses_cobertura': meses_cobertura,
            'deterioro': deterioro,
            'variaciones_reales': {
                'ingresos_totales': ingresos_totales_var_real,
                'recaudacion_propia': recaudacion_propia_var_real,
                'coparticipacion': coparticipacion_var_real,
                'gasto_primario': None,
            },
            'mensaje_clave': mensaje_clave,
            'reclamos_nacion': {
                'deuda_total_reclamada': to_float((reclamos_by_province.get(province) or {}).get('deuda_total_reclamada')),
                'deuda_total_robusta': to_float((reclamos_by_province.get(province) or {}).get('deuda_total_robusta')),
                'estado_cobertura': (reclamos_by_province.get(province) or {}).get('estado_cobertura', 'sin_carga'),
                'porcentaje_cubierto_con_dato_robusto': to_float((reclamos_by_province.get(province) or {}).get('porcentaje_cubierto_con_dato_robusto')),
                'deuda_nacion_con_provincia': (reclamos_by_province.get(province) or {}).get('deuda_nacion_con_provincia', {
                    'status': 'pendiente_diseno_funcional',
                    'ready_for_render': False,
                    'component_key': 'deuda_nacion_con_provincia',
                    'cards': [],
                    'last_update': None,
                }),
            },
        })

        if province == 'Buenos Aires':
            base['pba_context_2025_2026'] = {
                'latest_budget_execution_quarter': {
                    'periodo': (latest_budget_quarter or {}).get('periodo'),
                    'fecha_corte': (latest_budget_quarter or {}).get('fecha_corte'),
                    'ingresos_totales_ars_m': to_float((latest_budget_quarter or {}).get('ingresos_totales_ars_m')),
                    'gastos_totales_ars_m': to_float((latest_budget_quarter or {}).get('gastos_totales_ars_m')),
                    'resultado_primario_ars_m': to_float((latest_budget_quarter or {}).get('resultado_primario_ars_m')),
                    'resultado_financiero_ars_m': to_float((latest_budget_quarter or {}).get('resultado_financiero_ars_m')),
                    'source': PBA_BUDGET_QUARTERLY_FILE if latest_budget_quarter else None,
                },
                'national_debt_context': {
                    'fecha_corte': (latest_debt_nation or {}).get('fecha_corte'),
                    'deuda_bruta_total_usd_m': to_float((latest_debt_nation or {}).get('deuda_bruta_total_usd_m')),
                    'pct_moneda_extranjera': to_float((latest_debt_nation or {}).get('pct_moneda_extranjera')),
                    'pagos_mes_usd_m': to_float((latest_debt_nation or {}).get('pagos_mes_usd_m')),
                    'source': NATIONAL_DEBT_MONTHLY_FILE if latest_debt_nation else None,
                },
                'municipal_context': {
                    'fecha_corte': (latest_municipios or {}).get('fecha_corte'),
                    'autonomia_pct': to_float((latest_municipios or {}).get('autonomia_pct')),
                    'gasto_personal_pct_gasto_corr': to_float((latest_municipios or {}).get('gasto_personal_pct_gasto_corr')),
                    'resultado_financiero_ars_m': to_float((latest_municipios or {}).get('resultado_financiero_ars_m')),
                    'deuda_consolidada_ars_m': to_float((latest_municipios or {}).get('deuda_consolidada_ars_m')),
                    'source': MUNICIPIOS_PBA_ANNUAL_FILE if latest_municipios else None,
                },
                'source_priority': {
                    'top': [PBA_TOP_MONTHLY_FILE, TOP_MENSUAL_FILE],
                    'ron': [PBA_RON_MONTHLY_FILE, INFO_2026_FILE, SERIE_RON_FILE],
                }
            }

        payload['provinces'][province] = base

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')

    manifest.setdefault('files', {})['fiscal_provincias'] = OUTPUT_FILE
    manifest['generated_at'] = payload['generated_at']
    notes = manifest.setdefault('notes', {})
    notes['fiscal_pipeline_v2'] = (
        'Se agregan indicadores de dependencia, rigidez, ahorro corriente, estrés fiscal, riesgo aguinaldo, '
        'atribución del deterioro y semáforo fiscal para consumo directo de frontend.'
    )
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')


if __name__ == '__main__':
    build()

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('.')
INDEX_HTML = ROOT / 'index.html'
TOP_FILE = ROOT / 'top_mensual_2026_normalizado.csv'
TOP_2025_FILE = ROOT / 'top_mensual_2025_normalizado.csv'
INFO_FILE = ROOT / 'informacion_consolidada_2026_normalizado.csv'
INFO_2025_FILE = ROOT / 'informacion_consolidada_2025_normalizado.csv'
EXPENSES_FILE = ROOT / 'gasto_mensual_2025_2026_normalizado.csv'
PBA_TOP_MONTHLY_FILE = ROOT / 'pba_top_monthly.csv'
PBA_RON_MONTHLY_FILE = ROOT / 'pba_ron_monthly.csv'
MANIFEST_FILE = ROOT / 'dashboard_manifest.json'
DEFLACTOR_CSV = ROOT / 'deflactor_mensual.csv'
INPUTS_CSV = ROOT / 'dashboard_real_dynamics_inputs.csv'
OUTPUT_JSON = ROOT / 'dashboard_real_dynamics_2026.json'

METRICS = [
    'own_revenue',
    'ron_total',
    'primary_expenditure',
    'wages',
    'capital_expenditure',
]


def parse_deflator_from_index_html():
    txt = INDEX_HTML.read_text(encoding='utf-8')
    m = re.search(r"const DEFLACTOR_MONTH = (\{.*?\});", txt, flags=re.S)
    if not m:
        raise RuntimeError('No se encontró DEFLACTOR_MONTH en index.html')
    return json.loads(m.group(1))


def build_deflator_csv(raw_map):
    periods = sorted(raw_map.keys())
    latest_period = periods[-1]
    latest_factor = raw_map[latest_period]

    rows = []
    base_index = 100.0
    first_factor = raw_map[periods[0]]

    prev_period = None
    for period in periods:
        factor = float(raw_map[period])
        ipc_index = base_index * (first_factor / factor)
        if prev_period is None:
            ipc_mom = ''
        else:
            prev_factor = float(raw_map[prev_period])
            ipc_mom = f"{(prev_factor / factor) - 1:.6f}"
        rows.append({
            'period': period,
            'ipc_mom': ipc_mom,
            'ipc_index': f"{ipc_index:.6f}",
            'factor_to_latest': f"{(factor / latest_factor):.6f}",
        })
        prev_period = period

    with DEFLACTOR_CSV.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['period', 'ipc_mom', 'ipc_index', 'factor_to_latest'])
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def to_float(value):
    if value is None:
        return None
    v = str(value).strip()
    if v == '' or v.lower() == 'null':
        return None
    try:
        return float(v)
    except ValueError:
        return None


def month_from_date(raw):
    txt = (raw or '').strip()
    return txt[:7] if len(txt) >= 7 else ''


def prefill_inputs():
    rows = []

    # A) own_revenue (2026 vs mismo período 2025)
    top_rows = read_csv(TOP_FILE)
    top_2025_rows = read_csv(TOP_2025_FILE) if TOP_2025_FILE.exists() else []
    own_totals = defaultdict(float)
    own_totals_2025 = defaultdict(float)
    for r in top_rows:
        if r.get('period_type') != 'month':
            continue
        province = (r.get('province') or '').strip()
        period = (r.get('period') or '').strip()
        val = to_float(r.get('value_millions'))
        if not province or not period or val is None:
            continue
        own_totals[(province, period)] += val

    for r in top_2025_rows:
        if r.get('period_type') != 'month':
            continue
        province = (r.get('province') or '').strip()
        period = (r.get('period') or '').strip()
        val = to_float(r.get('value_millions'))
        if not province or not period or val is None:
            continue
        own_totals_2025[(province, period)] += val

    for (province, period), value in sorted(own_totals.items()):
        prev_period = f"{int(period[:4]) - 1:04d}-{period[5:7]}"
        prev_value = own_totals_2025.get((province, prev_period))
        rows.append({
            'province': province,
            'period': period,
            'metric': 'own_revenue',
            'current_nominal_millions': f"{value:.6f}",
            'prev_year_nominal_millions': '' if prev_value is None else f"{prev_value:.6f}",
            'source_current': TOP_FILE.name,
            'source_prev_year': TOP_2025_FILE.name if prev_value is not None else '',
            'status': 'prefilled_current_only' if prev_value is None else 'prefilled_comparable',
            'notes': '',
        })

    if PBA_TOP_MONTHLY_FILE.exists():
        for r in read_csv(PBA_TOP_MONTHLY_FILE):
            period = month_from_date(r.get('fecha_corte'))
            if not period.startswith('2026-'):
                continue
            value = to_float(r.get('top_total_ars_m'))
            if value is None:
                continue
            prev_period = f"{int(period[:4]) - 1:04d}-{period[5:7]}"
            prev_value = own_totals_2025.get(('Buenos Aires', prev_period))
            rows = [x for x in rows if not (x['province'] == 'Buenos Aires' and x['period'] == period and x['metric'] == 'own_revenue')]
            rows.append({
                'province': 'Buenos Aires',
                'period': period,
                'metric': 'own_revenue',
                'current_nominal_millions': f"{value:.6f}",
                'prev_year_nominal_millions': '' if prev_value is None else f"{prev_value:.6f}",
                'source_current': PBA_TOP_MONTHLY_FILE.name,
                'source_prev_year': TOP_2025_FILE.name if prev_value is not None else '',
                'status': 'prefilled_current_only' if prev_value is None else 'prefilled_comparable',
                'notes': 'prioridad_fuente_pba_2026',
            })

    # B) ron_total (2026 vs mismo período 2025)
    info_rows = read_csv(INFO_FILE)
    info_2025_rows = read_csv(INFO_2025_FILE) if INFO_2025_FILE.exists() else []
    by_key_cat = defaultdict(list)
    by_key_cat_2025 = defaultdict(list)

    for r in info_rows:
        if r.get('period_type') != 'month':
            continue
        period = (r.get('period') or '').strip()
        if period == 'CONS' or not period:
            continue
        province = (r.get('province') or '').strip()
        cat = (r.get('category_normalized') or r.get('category') or '').strip()
        by_key_cat[(province, period, cat)].append(r)

    for r in info_2025_rows:
        if r.get('period_type') != 'month':
            continue
        period = (r.get('period') or '').strip()
        if period == 'CONS' or not period:
            continue
        province = (r.get('province') or '').strip()
        cat = (r.get('category_normalized') or r.get('category') or '').strip()
        by_key_cat_2025[(province, period, cat)].append(r)

    all_keys = sorted({(k[0], k[1]) for k in by_key_cat})
    for province, period in all_keys:
        pick = None
        for category in ['Total | (1) + (2)', 'Total | Recursos | Origen Nacional | (1)']:
            candidates = by_key_cat.get((province, period, category), [])
            if candidates:
                pick = candidates[0]
                break
        if not pick:
            continue

        value = to_float(pick.get('value_millions'))
        prev_period = f"{int(period[:4]) - 1:04d}-{period[5:7]}"
        prev_pick = None
        for category in ['Total | (1) + (2)', 'Total | Recursos | Origen Nacional | (1)']:
            candidates = by_key_cat_2025.get((province, prev_period, category), [])
            if candidates:
                prev_pick = candidates[0]
                break
        prev_value = to_float(prev_pick.get('value_millions')) if prev_pick else None

        rows.append({
            'province': province,
            'period': period,
            'metric': 'ron_total',
            'current_nominal_millions': '' if value is None else f"{value:.6f}",
            'prev_year_nominal_millions': '' if prev_value is None else f"{prev_value:.6f}",
            'source_current': INFO_FILE.name,
            'source_prev_year': INFO_2025_FILE.name if prev_value is not None else '',
            'status': 'prefilled_current_only' if prev_value is None else 'prefilled_comparable',
            'notes': '',
        })

    if PBA_RON_MONTHLY_FILE.exists():
        for r in read_csv(PBA_RON_MONTHLY_FILE):
            period = month_from_date(r.get('fecha_corte'))
            if not period.startswith('2026-'):
                continue
            value = to_float(r.get('total_ron_ars_m_xlsx'))
            if value is None:
                value = to_float(r.get('total_ron_ars_m_daily'))
            if value is None:
                continue
            prev_period = f"{int(period[:4]) - 1:04d}-{period[5:7]}"
            prev_pick = None
            for category in ['Total | (1) + (2)', 'Total | Recursos | Origen Nacional | (1)']:
                candidates = by_key_cat_2025.get(('Buenos Aires', prev_period, category), [])
                if candidates:
                    prev_pick = candidates[0]
                    break
            prev_value = to_float(prev_pick.get('value_millions')) if prev_pick else None
            rows = [x for x in rows if not (x['province'] == 'Buenos Aires' and x['period'] == period and x['metric'] == 'ron_total')]
            rows.append({
                'province': 'Buenos Aires',
                'period': period,
                'metric': 'ron_total',
                'current_nominal_millions': f"{value:.6f}",
                'prev_year_nominal_millions': '' if prev_value is None else f"{prev_value:.6f}",
                'source_current': PBA_RON_MONTHLY_FILE.name,
                'source_prev_year': INFO_2025_FILE.name if prev_value is not None else '',
                'status': 'prefilled_current_only' if prev_value is None else 'prefilled_comparable',
                'notes': 'prioridad_fuente_pba_2026',
            })

    # C) gastos (2026 vs 2025)
    metric_map = {
        'gasto_primario': 'primary_expenditure',
        'salarios': 'wages',
        'gasto_capital': 'capital_expenditure',
    }
    expense_rows = read_csv(EXPENSES_FILE) if EXPENSES_FILE.exists() else []
    exp = defaultdict(float)
    for r in expense_rows:
        if r.get('period_type') != 'month':
            continue
        province = (r.get('province') or '').strip()
        period = (r.get('period') or '').strip()
        metric = metric_map.get((r.get('metric') or '').strip())
        value = to_float(r.get('value_millions'))
        if not province or not period or not metric or value is None:
            continue
        exp[(province, period, metric)] += value

    for province, period, metric in sorted(exp):
        if not period.startswith('2026-'):
            continue
        curr = exp.get((province, period, metric))
        prev_period = f"{int(period[:4]) - 1:04d}-{period[5:7]}"
        prev = exp.get((province, prev_period, metric))
        rows.append({
            'province': province,
            'period': period,
            'metric': metric,
            'current_nominal_millions': '' if curr is None else f"{curr:.6f}",
            'prev_year_nominal_millions': '' if prev is None else f"{prev:.6f}",
            'source_current': EXPENSES_FILE.name if curr is not None else '',
            'source_prev_year': EXPENSES_FILE.name if prev is not None else '',
            'status': 'prefilled_current_only' if prev is None else 'prefilled_comparable',
            'notes': '',
        })

    with INPUTS_CSV.open('w', encoding='utf-8', newline='') as f:
        fields = [
            'province', 'period', 'metric', 'current_nominal_millions', 'prev_year_nominal_millions',
            'source_current', 'source_prev_year', 'status', 'notes'
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def calc_real_dynamics():
    deflactor = {r['period']: r for r in read_csv(DEFLACTOR_CSV)}
    inputs = read_csv(INPUTS_CSV)

    grouped = defaultdict(lambda: defaultdict(list))
    for r in inputs:
        province = r['province']
        metric = r['metric']
        grouped[province][metric].append(r)

    output = {
        'source': 'dinámica real 2026',
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'methodology': {
            'real_yoy_pct': '((nominal_current / nominal_prev_year) / (ipc_index_current / ipc_index_prev_year) - 1) * 100',
            'real_ytd_pct': 'sumas deflactadas a último mes disponible del período',
            'missing_rule': 'si falta current o prev_year comparable, devolver null'
        },
        'provinces': {}
    }

    for province, metric_rows in sorted(grouped.items()):
        p_out = {
            'coverage_note': (
                'La dinámica real 2026 requiere base mensual homogénea. '
                'Si falta la serie 2025 comparable del mismo período, el bloque queda compacto.'
            ),
            'metrics': {}
        }
        for metric in METRICS:
            rows = sorted(metric_rows.get(metric, []), key=lambda x: x['period'])
            comparable = []
            last_period = rows[-1]['period'] if rows else None
            yoy_by_period = {}
            for row in rows:
                period = row['period']
                c = to_float(row['current_nominal_millions'])
                p = to_float(row['prev_year_nominal_millions'])
                if c is None or p is None or p == 0:
                    continue
                y, m = period.split('-')
                prev_period = f"{int(y)-1:04d}-{m}"
                ic = to_float(deflactor.get(period, {}).get('ipc_index'))
                ip = to_float(deflactor.get(prev_period, {}).get('ipc_index'))
                if ic is None or ip is None or ip == 0:
                    continue
                yoy = ((c / p) / (ic / ip) - 1.0) * 100.0
                yoy_by_period[period] = round(yoy, 1)
                comparable.append((period, c, p))

            latest_comp_period = sorted(yoy_by_period)[-1] if yoy_by_period else None
            last_real = yoy_by_period.get(latest_comp_period)

            ytd_through = None
            ytd_val = None
            if comparable:
                by_year = defaultdict(list)
                for p, c, prev in comparable:
                    by_year[p[:4]].append((p, c, prev))
                curr_year = max(by_year)
                seq = sorted(by_year[curr_year], key=lambda x: x[0])
                months = [int(p.split('-')[1]) for p, _, _ in seq]
                expected = list(range(months[0], months[-1] + 1))
                if months == expected:
                    lastp = seq[-1][0]
                    f_last = to_float(deflactor.get(lastp, {}).get('factor_to_latest'))
                    if f_last:
                        sum_c = 0.0
                        sum_p = 0.0
                        ok = True
                        for period, c, prev in seq:
                            f_curr = to_float(deflactor.get(period, {}).get('factor_to_latest'))
                            py, pm = period.split('-')
                            prev_period = f"{int(py)-1:04d}-{pm}"
                            f_prev = to_float(deflactor.get(prev_period, {}).get('factor_to_latest'))
                            if not f_curr or not f_prev:
                                ok = False
                                break
                            sum_c += c * (f_curr / f_last)
                            sum_p += prev * (f_prev / f_last)
                        if ok and sum_p != 0:
                            ytd_val = round(((sum_c / sum_p) - 1.0) * 100.0, 1)
                            ytd_through = lastp

            status = 'calculated' if last_real is not None else ('current_without_homogeneous_base' if rows else 'missing')
            p_out['metrics'][metric] = {
                'last_available_period': last_period,
                'last_available_real_yoy_pct': last_real,
                'ytd_available_through': ytd_through,
                'real_ytd_pct': ytd_val,
                'status': status
            }

        output['provinces'][province] = p_out

    with OUTPUT_JSON.open('w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    if not DEFLACTOR_CSV.exists():
        raw = parse_deflator_from_index_html()
        build_deflator_csv(raw)

    if not INPUTS_CSV.exists() or INPUTS_CSV.stat().st_size == 0:
        prefill_inputs()
    else:
        # Re-sincroniza con fuentes 2025/2026 para mantener consistencia de esquema.
        prefill_inputs()

    calc_real_dynamics()

    if MANIFEST_FILE.exists():
        with MANIFEST_FILE.open(encoding='utf-8') as f:
            manifest = json.load(f)
        manifest.setdefault('files', {})['real_dynamics_2026'] = OUTPUT_JSON.name
        manifest.setdefault('files', {})['real_dynamics_inputs'] = INPUTS_CSV.name
        manifest['generated_at'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        with MANIFEST_FILE.open('w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            f.write('\n')


if __name__ == '__main__':
    main()

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('.')
INDEX_HTML = ROOT / 'index.html'
TOP_FILE = ROOT / 'top_mensual_2026_normalizado.csv'
INFO_FILE = ROOT / 'informacion_consolidada_2026_normalizado.csv'
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


def prefill_inputs():
    rows = []

    # A) own_revenue
    top_rows = read_csv(TOP_FILE)
    own_totals = defaultdict(float)
    for r in top_rows:
        if r.get('period_type') != 'month':
            continue
        province = (r.get('province') or '').strip()
        period = (r.get('period') or '').strip()
        val = to_float(r.get('value_millions'))
        if not province or not period or val is None:
            continue
        own_totals[(province, period)] += val

    for (province, period), value in sorted(own_totals.items()):
        rows.append({
            'province': province,
            'period': period,
            'metric': 'own_revenue',
            'current_nominal_millions': f"{value:.6f}",
            'prev_year_nominal_millions': '',
            'source_current': TOP_FILE.name,
            'source_prev_year': '',
            'status': 'prefilled_current_only',
            'notes': '',
        })

    # B) ron_total (prefer Total | (1) + (2), fallback Total | Recursos | Origen Nacional | (1))
    info_rows = read_csv(INFO_FILE)
    by_key_cat = defaultdict(list)
    for r in info_rows:
        if r.get('period_type') != 'month':
            continue
        period = (r.get('period') or '').strip()
        if period == 'CONS' or not period:
            continue
        province = (r.get('province') or '').strip()
        cat = (r.get('category_normalized') or r.get('category') or '').strip()
        by_key_cat[(province, period, cat)].append(r)

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
        rows.append({
            'province': province,
            'period': period,
            'metric': 'ron_total',
            'current_nominal_millions': '' if value is None else f"{value:.6f}",
            'prev_year_nominal_millions': '',
            'source_current': INFO_FILE.name,
            'source_prev_year': '',
            'status': 'prefilled_current_only',
            'notes': '',
        })

    # C) placeholders gastos for Buenos Aires 2026-01..03
    for period in ['2026-01', '2026-02', '2026-03']:
        for metric in ['primary_expenditure', 'wages', 'capital_expenditure']:
            rows.append({
                'province': 'Buenos Aires',
                'period': period,
                'metric': metric,
                'current_nominal_millions': '',
                'prev_year_nominal_millions': '',
                'source_current': '',
                'source_prev_year': '',
                'status': 'missing',
                'notes': 'Requiere fuente mensual de ejecución 2025-2026',
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
                'La dinámica real 2026 requiere base mensual homogénea. Hoy el repo prefill ingresos corrientes 2026, '
                'pero no trae aún base mensual comparable 2025 ni ejecución mensual de gasto normalizada.'
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

            if yoy_by_period:
                latest_comp_period = sorted(yoy_by_period)[-1]
                last_real = yoy_by_period[latest_comp_period]
            else:
                latest_comp_period = None
                last_real = None

            # ytd: only if comparable consecutive periods in same year
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

            if last_real is not None:
                status = 'calculated'
            elif rows and any(to_float(r['current_nominal_millions']) is not None for r in rows):
                status = 'current_without_homogeneous_base'
            else:
                status = 'missing'

            p_out['metrics'][metric] = {
                'last_available_period': latest_comp_period or last_period,
                'last_available_real_yoy_pct': last_real,
                'ytd_available_through': ytd_through,
                'real_ytd_pct': ytd_val,
                'status': status,
            }
        output['provinces'][province] = p_out

    OUTPUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def update_manifest():
    manifest = json.loads(MANIFEST_FILE.read_text(encoding='utf-8'))
    files = manifest.setdefault('files', {})
    files['deflactor_mensual'] = DEFLACTOR_CSV.name
    files['real_dynamics_inputs'] = INPUTS_CSV.name
    files['real_dynamics_2026'] = OUTPUT_JSON.name

    notes = manifest.setdefault('notes', {})
    notes['real_dynamics_scope'] = (
        'Bloque de dinámica real 2026. Requiere base mensual homogénea actual vs mismo período del año previo. '
        'El repo actual prefill ingresos 2026, pero no contiene aún toda la base comparable 2025 ni ejecución mensual de gasto 2026 normalizada.'
    )

    MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    raw = parse_deflator_from_index_html()
    build_deflator_csv(raw)
    prefill_inputs()
    calc_real_dynamics()
    update_manifest()


if __name__ == '__main__':
    main()

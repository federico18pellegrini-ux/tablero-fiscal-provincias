import csv
import json
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_PATH = Path('dashboard_manifest.json')
RON_PATH = Path('serie_ron_2003_2025_normalizado.csv')
TOP_MENSUAL_PATH = Path('top_mensual_2026_normalizado.csv')
INPUTS_PATH = Path('dashboard_federal_fairness_inputs.csv')
OUTPUT_PATH = Path('dashboard_federal_fairness.json')

RON_PRIMARY = 'Total | Recursos | Origen Nacional | (1)'
RON_FALLBACK = 'S U B - | T O T A L'
CABA_NAME = 'CABA'
DEFAULT_POPULATION_2022 = {
    'Buenos Aires': 17569053,
    'CABA': 3120612,
    'Catamarca': 429562,
    'Chaco': 1142963,
    'Chubut': 603120,
    'Corrientes': 1197553,
    'Córdoba': 3978984,
    'Entre Ríos': 1426426,
    'Formosa': 606041,
    'Jujuy': 811611,
    'La Pampa': 361859,
    'La Rioja': 384607,
    'Mendoza': 2014533,
    'Misiones': 1280960,
    'Neuquén': 726590,
    'Río Negro': 762067,
    'Salta': 1440672,
    'San Juan': 818234,
    'San Luis': 540905,
    'Santa Cruz': 337226,
    'Santa Fe': 3556522,
    'Santiago del Estero': 1060906,
    'Tierra del Fuego': 190641,
    'Tucumán': 1731820,
}


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


def safe_div(num, den):
    if num is None or den is None or den == 0:
        return None
    return num / den


def metric(value, status, source):
    return {
        'value': value,
        'status': status,
        'source': source,
    }


with MANIFEST_PATH.open(encoding='utf-8') as f:
    manifest = json.load(f)

province_universe = manifest.get('province_universe', [])

with RON_PATH.open(encoding='utf-8', newline='') as f:
    ron_rows = list(csv.DictReader(f))

top_2026_by_prov = {}
if TOP_MENSUAL_PATH.exists():
    with TOP_MENSUAL_PATH.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            province = row.get('province')
            period = (row.get('period') or '').strip()
            val = to_float(row.get('value_millions'))
            if not province or val is None or not period.startswith('2026-'):
                continue
            top_2026_by_prov[province] = top_2026_by_prov.get(province, 0.0) + val
top_2026_total = sum(v for v in top_2026_by_prov.values() if v is not None)

latest_year = max(int(r['year']) for r in ron_rows if str(r.get('year', '')).isdigit())

ron_by_prov_year = {}
for row in ron_rows:
    province = row.get('province')
    year_txt = row.get('year')
    cat = row.get('category_normalized')
    val = to_float(row.get('value_millions'))
    if not province or val is None:
        continue
    try:
        year = int(year_txt)
    except (TypeError, ValueError):
        continue
    key = (province, year)
    slot = ron_by_prov_year.setdefault(key, {'primary': 0.0, 'fallback': 0.0, 'has_primary': False, 'has_fallback': False})
    if cat == RON_PRIMARY:
        slot['primary'] += val
        slot['has_primary'] = True
    elif cat == RON_FALLBACK:
        slot['fallback'] += val
        slot['has_fallback'] = True

ron_selected = {}
for province in province_universe:
    slot = ron_by_prov_year.get((province, latest_year))
    if not slot:
        ron_selected[province] = None
    elif slot['has_primary']:
        ron_selected[province] = slot['primary']
    elif slot['has_fallback']:
        ron_selected[province] = slot['fallback']
    else:
        ron_selected[province] = None

if not INPUTS_PATH.exists():
    with INPUTS_PATH.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                'province',
                'year',
                'population',
                'estimated_contribution_share_pct',
                'contribution_method',
                'status',
                'source_population',
                'source_contribution',
                'notes',
            ],
        )
        writer.writeheader()
        for province in province_universe:
            writer.writerow(
                {
                    'province': province,
                    'year': latest_year,
                    'population': '',
                    'estimated_contribution_share_pct': '',
                    'contribution_method': 'Sin dato cargado (declarar criterio: PIB / recaudación / base tributaria / otro).',
                    'status': 'missing',
                    'source_population': '',
                    'source_contribution': '',
                    'notes': 'Input manual pendiente. El aporte estimado no equivale a una obligación legal de distribución.',
                }
            )

with INPUTS_PATH.open(encoding='utf-8', newline='') as f:
    input_rows = list(csv.DictReader(f))

input_map = {}
for row in input_rows:
    province = row.get('province')
    year = to_float(row.get('year'))
    if not province or year is None:
        continue
    population = to_float(row.get('population'))
    if population is None and province in DEFAULT_POPULATION_2022:
        row['population'] = str(DEFAULT_POPULATION_2022[province])
        row['source_population'] = row.get('source_population') or 'INDEC Censo 2022 (base)'
        row['notes'] = (row.get('notes') or '').strip() or 'Población base pre-cargada para habilitar comparaciones per cápita.'
    if to_float(row.get('estimated_contribution_share_pct')) is None:
        row['status'] = 'partial'
        row['source_contribution'] = row.get('source_contribution') or ''
        if province == 'Buenos Aires':
            share_proxy = safe_div(top_2026_by_prov.get('Buenos Aires', 0.0) * 100, top_2026_total)
            if share_proxy is not None:
                row['estimated_contribution_share_pct'] = f'{share_proxy:.4f}'
                row['contribution_method'] = (
                    'Proxy recaudación propia 2026 YTD: participación de Buenos Aires en la suma '
                    'provincial de top_mensual_2026_normalizado.csv.'
                )
                row['source_contribution'] = row.get('source_contribution') or 'top_mensual_2026_normalizado.csv'
                row['status'] = 'ok'
    if to_float(row.get('estimated_contribution_share_pct')) is None and not (row.get('contribution_method') or '').strip():
        row['contribution_method'] = ''
    input_map[(province, int(year))] = row

with INPUTS_PATH.open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            'province',
            'year',
            'population',
            'estimated_contribution_share_pct',
            'contribution_method',
            'status',
            'source_population',
            'source_contribution',
            'notes',
        ],
    )
    writer.writeheader()
    writer.writerows(input_rows)

ron_total_all = sum(v for v in ron_selected.values() if v is not None)

# Pre-cálculo para promedios per cápita
per_capita = {}
for province in province_universe:
    inp = input_map.get((province, latest_year), {})
    pop = to_float(inp.get('population'))
    ron_val = ron_selected.get(province)
    per_capita[province] = safe_div((ron_val * 1_000_000) if ron_val is not None else None, pop)

vals_23 = [v for p, v in per_capita.items() if p != CABA_NAME and v is not None]
vals_24 = [v for v in per_capita.values() if v is not None]
avg_23 = sum(vals_23) / len(vals_23) if vals_23 else None
avg_24 = sum(vals_24) / len(vals_24) if vals_24 else None

ranking_23 = {}
if vals_23:
    ordered = sorted(((p, v) for p, v in per_capita.items() if p != CABA_NAME and v is not None), key=lambda x: x[1], reverse=True)
    for idx, (province, _) in enumerate(ordered, start=1):
        ranking_23[province] = {'position': idx, 'total': len(ordered)}

provinces_out = {}
for province in province_universe:
    inp = input_map.get((province, latest_year), {})
    population = to_float(inp.get('population'))
    estimated_share = to_float(inp.get('estimated_contribution_share_pct'))
    contribution_method = (inp.get('contribution_method') or '').strip()

    ron_val = ron_selected.get(province)
    received_share = safe_div(ron_val * 100, ron_total_all) if ron_val is not None and ron_total_all > 0 else None
    ron_pc = per_capita.get(province)
    ratio_vs_avg = safe_div((ron_pc * 100) if ron_pc is not None else None, avg_23)
    gap_vs_avg = (ron_pc - avg_23) if (ron_pc is not None and avg_23 is not None) else None
    federal_gap = (received_share - estimated_share) if (received_share is not None and estimated_share is not None) else None
    return_ratio = safe_div((received_share * 100) if received_share is not None else None, estimated_share)

    input_status = (inp.get('status') or '').strip().lower()
    if input_status not in {'ok', 'partial', 'missing'}:
        input_status = 'missing'
    if estimated_share is None:
        input_status = 'partial'

    metrics = {
        'population': metric(population, 'ok' if population is not None else 'missing', ['dashboard_federal_fairness_inputs.csv']),
        'ron_per_capita_pesos': metric(ron_pc, 'ok' if ron_pc is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
        'avg_ron_per_capita_23_provinces_pesos': metric(avg_23, 'ok' if avg_23 is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
        'avg_ron_per_capita_24_jurisdictions_pesos': metric(avg_24, 'ok' if avg_24 is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
        'ratio_vs_avg_23_provinces_pct': metric(ratio_vs_avg, 'ok' if ratio_vs_avg is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
        'gap_vs_avg_23_provinces_pesos': metric(gap_vs_avg, 'ok' if gap_vs_avg is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
        'received_share_pct': metric(received_share, 'ok' if received_share is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv']),
        'estimated_contribution_share_pct': metric(estimated_share, 'ok' if estimated_share is not None else 'missing', ['dashboard_federal_fairness_inputs.csv']),
        'federal_gap_pp': metric(federal_gap, 'ok' if federal_gap is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
        'return_ratio_pct': metric(return_ratio, 'ok' if return_ratio is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
        'pesos_recibidos_cada_100_aportados': metric(return_ratio, 'ok' if return_ratio is not None else 'missing', ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv']),
    }

    if ranking_23.get(province):
        metrics['ron_per_capita_rank_23_provinces'] = {
            'value': ranking_23[province]['position'],
            'total': ranking_23[province]['total'],
            'status': 'ok',
            'source': ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv'],
        }
    else:
        metrics['ron_per_capita_rank_23_provinces'] = {
            'value': None,
            'total': None,
            'status': 'missing',
            'source': ['serie_ron_2003_2025_normalizado.csv', 'dashboard_federal_fairness_inputs.csv'],
        }

    metric_statuses = [v.get('status') for v in metrics.values() if isinstance(v, dict)]
    has_ok = any(st == 'ok' for st in metric_statuses)
    has_missing = any(st == 'missing' for st in metric_statuses)
    if input_status == 'ok' and has_ok and not has_missing:
        block_status = 'ok'
    elif has_ok and has_missing:
        block_status = 'partial'
    elif has_ok:
        block_status = 'ok'
    else:
        block_status = 'missing'

    provinces_out[province] = {
        'year': latest_year,
        'status': block_status,
        'coverage_note': 'La comparación federal usa RON anual por provincia y población. El aporte a la masa nacional es una estimación y debe mostrar siempre su método.',
        'metrics': metrics,
        'method': {
            'contribution_method': contribution_method,
        },
    }

output = {
    'source': 'bloque comparación federal justa',
    'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    'methodology': {
        'ron_per_capita': 'ron_total_annual_millions * 1000000 / population',
        'avg_ron_per_capita_23_provinces': 'promedio simple de las 23 provincias excluyendo CABA',
        'avg_ron_per_capita_24_jurisdictions': 'promedio simple incluyendo CABA',
        'received_share_pct': 'ron_total_province / suma_ron_total_all * 100',
        'return_ratio': 'received_share_pct / estimated_contribution_share_pct * 100',
        'federal_gap_pp': 'received_share_pct - estimated_contribution_share_pct',
    },
    'provinces': provinces_out,
}

with OUTPUT_PATH.open('w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
    f.write('\n')

print(f'Generated {INPUTS_PATH} and {OUTPUT_PATH} for year {latest_year}.')

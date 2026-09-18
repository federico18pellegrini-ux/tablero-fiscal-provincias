"""Import the audited 17/09 package; build the national management views.

python scripts_build_national_management.py --input-dir /path/nacion-datos-20260917
python scripts_build_national_management.py --check
"""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'nacion/data'
RAW = DATA / 'gestion'
EXCLUDED = 'historia_apn_pib_por_conciliar'

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'

def digest(path):
    return sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()

def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)

def total(rows, key):
    values = [r.get(key) for r in rows]
    return sum(values) if values and all(finite(v) for v in values) else None

def ratio(a, b):
    return a / b * 100 if finite(a) and finite(b) and b > 0 else None

def change(a, b):
    r = ratio(a, b)
    return r - 100 if r is not None else None

def import_package(folder):
    catalog, sources = load(folder / 'catalogo_datos.json'), load(folder / 'fuentes.json')
    validation = load(folder / 'validacion.json')
    if validation['failures']:
        raise ValueError('El paquete tiene controles requeridos sin aprobar')
    # Validate the actual archived originals, not just the saved PASS message.
    for source in sources:
        p = folder / 'originales' / source['file']
        if p.stat().st_size != source['bytes'] or sha256(p.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Original alterado: ' + source['file'])
    RAW.mkdir(parents=True, exist_ok=True)
    public = []
    for item in catalog:
        if item['dataset'] == EXCLUDED:
            continue
        entry = dict(item)
        entry['files'] = {}
        for ext in ('csv', 'json'):
            name = item['dataset'] + '.' + ext
            source = folder / 'datos' / name
            if ext == 'json' and len(load(source)) != item['rows']:
                raise ValueError('Cobertura modificada: ' + name)
            shutil.copyfile(source, RAW / name)
            entry['files'][ext] = {'path': 'data/gestion/' + name, 'sha256': digest(RAW / name)}
        public.append(entry)
    (RAW / 'catalogo.json').write_text(dump(public), encoding='utf-8')
    (RAW / 'fuentes.json').write_text(dump(sources), encoding='utf-8')
    (RAW / 'control.json').write_text(dump({
        'required_checks_passed': True, 'checks': validation['checks'],
        'exceptions': validation['exceptions'], 'excluded': [EXCLUDED],
        'reason': 'La serie de PIB e ingresos no concilia con los totales de ejecución; fuera de los cálculos y descargas públicas.'
    }), encoding='utf-8')

def build():
    catalog = load(RAW / 'catalogo.json')
    assert len(catalog) == 28 and EXCLUDED not in {r['dataset'] for r in catalog}
    for item in catalog:
        for entry in item['files'].values():
            assert digest(ROOT / 'nacion' / entry['path']) == entry['sha256'], entry['path']
    get = lambda name: load(RAW / (name + '.json'))
    budget = load(DATA / 'budget.json')
    stages = get('gasto_etapas_total')[0]
    for new, old in [('credito_presupuestado', 'law'), ('credito_vigente', 'current'), ('credito_devengado', 'accrued')]:
        assert abs(stages[new] - budget['total'][old]) < .01
    cash = get('resultado_fiscal_comparacion')
    cash_by = {r['indicador']: r for r in cash}
    for year in (2025, 2026):
        k = f'enero_julio_{year}'
        assert abs(cash_by['ingresos_totales'][k] - cash_by['gasto_primario'][k] - cash_by['resultado_primario'][k]) < 1
        assert abs(cash_by['resultado_primario'][k] - cash_by['intereses_netos'][k] - cash_by['resultado_financiero'][k]) < 1
    ron = get('ron_comparacion_provincias')
    population = {(r['provincia_id'], r['anio']): r['habitantes'] for r in get('poblacion_proyectada')}
    transfers = get('transferencias_presupuestarias_provincias')
    provincial = []
    for r in ron:
        pid = r['provincia_id']
        nominal = [v for v in transfers if v['ubicacion_geografica_id'] == pid and v['periodo'].startswith('2026-')]
        comparable = [v for v in nominal if v['periodo'] <= '2026-08']
        prior = [v for v in transfers if v['ubicacion_geografica_id'] == pid and '2025-01' <= v['periodo'] <= '2025-08']
        real26 = total(comparable, 'credito_devengado_real_agosto2026')
        real25 = total(prior, 'credito_devengado_real_agosto2026')
        provincial.append({**r, 'habitantes': population[(pid, 2026)],
            'presupuestarias_devengado': total(nominal, 'credito_devengado'),
            'presupuestarias_pagado': total(nominal, 'credito_pagado'),
            'presupuestarias_real_2026': real26, 'presupuestarias_real_2025': real25,
            'presupuestarias_variacion_real_pct': change(real26, real25)})
    resources = get('recursos_mensuales_tipo')
    revenue_comparison = []
    for r in get('recursos_etapas_tipo'):
        periods = {y: [m for m in resources if m['tipo_id'] == r['tipo_id'] and f'{y}-01' <= m['periodo'] <= f'{y}-08'] for y in (2025, 2026)}
        a, b = (total(periods[y], 'recurso_real_agosto2026') for y in (2026, 2025))
        revenue_comparison.append({**r, 'real_2026': a, 'real_2025': b, 'variacion_real_pct': change(a, b)})
    monthly = []
    flows = get('gasto_mensual_funcion')
    for period in sorted({r['periodo'] for r in flows}):
        rows = [r for r in flows if r['periodo'] == period]
        monthly.append({'periodo': period, 'nominal': total(rows, 'credito_devengado'),
                        'real': total(rows, 'credito_devengado_real_agosto2026'),
                        'mes_completo': all(r['mes_completo'] for r in rows)})
    # Historical annual amounts are kept nominal before a complete observed CPI year.
    ipc = {r['periodo']: r['indice'] for r in get('ipc_observado')}
    history = []
    for r in get('historia_ejecucion_presupuestaria'):
        year = r['ejercicio_presupuestario']
        indices = [ipc.get(f'{year}-{m:02d}') for m in range(1, 13)]
        factor = ipc['2026-08'] / (sum(indices) / 12) if all(finite(i) for i in indices) else None
        history.append({**r, 'factor_real_anual': factor,
                        'ejecucion_pct': ratio(r['credito_devengado'], r['credito_vigente']),
                        'modificacion_pct': change(r['credito_vigente'], r['credito_presupuestado'])})
    datasets = {r['dataset']: {'unit': r['unit'], 'scope': r['scope'], 'method': r['method'],
                 'sources': [{'url': s['url'], 'file': s['file']} for s in r['sources']], 'files': r['files'], 'rows': r['rows']} for r in catalog}
    return {
        'meta': {'reviewed': '2026-09-17', 'execution_cutoff': '2026-09-15', 'real_base': '2026-08',
                 'published_datasets': 28, 'pending_datasets': 1, 'money_unit': 'ARS millones',
                 'debt_unit': 'USD millones equivalentes', 'excluded': EXCLUDED},
        'datasets': datasets,
        'execution': {'total': stages, 'comparison': get('gasto_comparacion_real_total'),
            'functions_comparison': get('gasto_comparacion_real_funcion'), 'monthly': monthly,
            'groups': {k: get('gasto_etapas_' + k) for k in ['jurisdiccion','funcion','objeto','territorio','programa']}},
        'cash': {'comparison': cash, 'monthly': get('resultado_fiscal_caja_mensual')},
        'resources': revenue_comparison,
        'debt': {'monthly': get('deuda_stock_pagos'), 'schedule': get('vencimientos_perfil_marzo2026'),
                 'annual_schedule': get('vencimientos_anuales_perfil_marzo2026'), 'cutoff_schedule': '2026-03-31'},
        'provinces': {'comparison': provincial, 'monthly': get('ron_provincias_mensual'), 'history': get('ron_historia_provincias_anual')},
        'physical': {'coverage': get('metas_cobertura'), 'works_count': len(get('obras_ejecucion_fisica_financiera')),
                     'works_missing_physical': sum(r['ejecucion_fisica_1t2026_pct'] is None for r in get('obras_ejecucion_fisica_financiera'))},
        'history': history,
    }

def run(folder=None, check=False):
    if folder:
        import_package(folder)
    data = build()
    target = DATA / 'gestion.json'
    if check:
        assert load(target) == data, 'Regenerar gestion.json'
    else:
        target.write_text(dump(data), encoding='utf-8')
    print('Gestión nacional: 28 conjuntos incorporados; serie de PIB separada. Integridad y totales conciliados.')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir', type=Path)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    run(args.input_dir, args.check)

"""Package the audited municipal research for the static dashboard (stdlib only)."""
import argparse
import csv
import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def apply_verified_fiscal(municipalities, path):
    """Overlay official executions; reject inconsistent amounts or periods before publishing."""
    audit = json.loads(path.read_text(encoding='utf-8'))
    seen = set()
    for group, target in [('records', 'fiscal'), ('budgetExecutions', 'fiscalExecution')]:
        for record in audit[group]:
            ident = record['id']
            if ident not in municipalities or ident in seen:
                raise ValueError(f'Duplicate or unknown fiscal municipality: {ident}')
            seen.add(ident)
            if record['fin'] != audit['periodEnd'] or not record['inicio'].startswith('2026-01-'):
                raise ValueError(f'Non-comparable fiscal period: {ident}')
            amounts = {k: Decimal(v) for k, v in record['amounts'].items()}
            if not all(v.is_finite() for v in amounts.values()):
                raise ValueError(f'Non-finite fiscal amount: {ident}')
            if target == 'fiscal':
                checks = [
                    amounts['ingresos_corrientes'] + amounts['ingresos_capital'] - amounts['ingresos_totales'],
                    amounts['gastos_corrientes'] + amounts['gastos_capital'] - amounts['gastos_totales'],
                    amounts['ingresos_totales'] - amounts['gastos_totales'] - amounts['resultado_financiero'],
                ]
                if any(abs(v) > Decimal('0.01') for v in checks):
                    raise ValueError(f'Unreconciled fiscal account: {ident}')
            else:
                pending = amounts['gastos_presupuestarios_devengados'] - amounts['gastos_presupuestarios_pagados']
                if pending < 0:
                    raise ValueError(f'Negative unpaid execution: {ident}')
                amounts['devengado_no_pagado_del_periodo'] = pending
            municipalities[ident][target] = {
                **{k: v for k, v in record.items() if k not in ('id', 'amounts')},
                **{k: float(v) for k, v in amounts.items()},
                'url': record['landingUrl'], 'unidad': 'ARS corrientes',
                'verifiedAt': audit['verifiedAt'],
            }
    for m in municipalities.values():
        f = m['fiscal']
        if not f:
            continue
        f['ahorro_corriente'] = round(f['ingresos_corrientes'] - f['gastos_corrientes'], 2)
        f['resultado_sobre_ingresos_pct'] = f['resultado_financiero'] / f['ingresos_totales'] * 100
        f['resultado_por_habitante_base2022_ars_corrientes'] = f['resultado_financiero'] / m['poblacion_2022']
        f['capital_sobre_gasto_pct'] = f['gastos_capital'] / f['gastos_totales'] * 100
        f['personal_sobre_gasto_corriente_pct'] = f['personal_devengado'] / f['gastos_corrientes'] * 100 if f.get('personal_devengado') is not None else None
        f['ahorro_sobre_ingresos_corrientes_pct'] = f['ahorro_corriente'] / f['ingresos_corrientes'] * 100
        f['capital_por_habitante_base2022_ars_corrientes'] = f['gastos_capital'] / m['poblacion_2022']
    return {'fiscal': sum(bool(m['fiscal']) for m in municipalities.values()),
            'budgetOnly': sum(bool(m.get('fiscalExecution')) and not m['fiscal'] for m in municipalities.values()),
            'verifiedAt': audit['verifiedAt']}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def value(text):
    if text in ('', None):
        return None
    if text in ('True', 'False'):
        return text == 'True'
    try:
        n = float(text)
        return round(n, 6) if math.isfinite(n) else None
    except ValueError:
        return text


def build(folder):
    base = read_csv(folder / 'rankings_base_135_municipios.csv')
    municipalities = {}
    for row in base:
        ident = row.pop('municipality_id')
        municipalities[ident] = {'id': ident, **{k: value(v) for k, v in row.items()}, 'transfers': [], 'employment': [], 'sectors': [], 'fiscal': None}
    assert len(municipalities) == 135
    ipc = {r['period']: float(r['ipc_index']) for r in read_csv(folder / 'ipc_indec_verificado.csv')}
    for r in read_csv(folder / 'datos_de_entrada/transferencias_mensuales_2025_2026_muestra.csv'):
        factor = ipc['2026-07'] / ipc[r['period']]
        municipalities[r['municipality_id']]['transfers'].append([r['period'], round(float(r['total_transfers_ars']) * factor, 2), round(float(r['coparticipation_gross_ars']) * factor, 2)])
    employment = {i: {} for i in municipalities}
    for r in read_csv(folder / 'datos_de_entrada/empleo_salarios_oede_muestra.csv'):
        period = r['period']
        employment[r['municipality_id']].setdefault(period, {})[r['metric']] = float(r['value'])
    for ident, series in employment.items():
        municipalities[ident]['employment'] = [[p, r.get('employment'), round(r['wage_ars'] * ipc['2026-07'] / ipc[p], 2) if r.get('wage_ars') is not None else None] for p, r in sorted(series.items())]
    for r in read_csv(folder / 'empleo_sectorial_pba_2019_2025.csv'):
        if r['Periodo'] == '202512':
            municipalities[r['municipality_id']]['sectors'].append({'name': r['Sector'], 'jobs': value(r['empleo_num'])})
    for r in read_csv(folder / 'muestra_fiscal_junio2026.csv'):
        municipalities[r['municipality_id']]['fiscal'] = {k: value(v) for k, v in r.items() if k not in ('municipality_id', 'municipio')}
    fiscal_path = ROOT / 'municipios/data/fiscal_verified.json'
    fiscal_coverage = apply_verified_fiscal(municipalities, fiscal_path)
    for m in municipalities.values():
        m['transfers'].sort()
        assert len(m['transfers']) == 19 and len(m['employment']) == 84
        assert m['poblacion_2022'] > 0
    summary = json.loads((folder / 'resultados_verificados.json').read_text(encoding='utf-8'))
    controls = json.loads((folder / 'control_y_recaudacion.json').read_text(encoding='utf-8'))
    data = {'version': 2, 'generated': '2026-09-07', 'priceBase': '2026-07', 'populationYear': 2022, 'summary': summary, 'fiscalCoverage': fiscal_coverage, 'provincialRevenue': controls['recaudacion_real_ene_jul_2026_vs2025_pct'], 'municipalities': list(municipalities.values())}
    target = ROOT / 'municipios/data/dashboard.json'
    target.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    manifest = [{'file': str(p.relative_to(folder)).replace('\\', '/'), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*.csv')]
    overlay = {'file': str(fiscal_path.relative_to(ROOT)).replace('\\', '/'), 'sha256': hashlib.sha256(fiscal_path.read_bytes()).hexdigest()}
    (target.parent / 'build-manifest.json').write_text(json.dumps({'generated': '2026-09-07', 'inputs': manifest, 'repositoryInputs': [overlay], 'coverage': 135, 'fiscalCoverage': fiscal_coverage}, indent=2), encoding='utf-8')
    (target.parent / 'fuentes.csv').write_bytes((folder / 'fuentes_y_huellas.csv').read_bytes())
    fiscal_audit = json.loads(fiscal_path.read_text(encoding='utf-8'))
    with (target.parent / 'fuentes.csv').open('a', encoding='utf-8', newline='') as source_file:
        writer = csv.writer(source_file)
        for record in fiscal_audit['records'] + fiscal_audit['budgetExecutions']:
            for index, document in enumerate(record['documents'], 1):
                writer.writerow([f"municipio-{record['id']}-2026-06-{index}.pdf", document['url'], document['sha256'], document['bytes'], fiscal_audit['verifiedAt']])
    # Serve a conventional deferred script on static hosts, independent of .mjs MIME configuration.
    model = (ROOT / 'municipios/model.mjs').read_text(encoding='utf-8').replace('export ', '')
    app = (ROOT / 'municipios/app.mjs').read_text(encoding='utf-8').split('\n', 1)[1]
    (ROOT / 'municipios/app.js').write_text("/* Generated by scripts_build_municipal_dashboard.py. */\n(function(){'use strict';\n" + model + '\n' + app + '\n})();\n', encoding='utf-8')
    print(f'{target.name}: {len(municipalities)} municipalities; {target.stat().st_size:,} bytes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=Path, required=True)
    build(parser.parse_args().input_dir)

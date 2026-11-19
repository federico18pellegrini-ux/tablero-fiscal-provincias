"""Reconcile the last complete month from an archived Presupuesto Abierto vintage."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'nacion/data/execution-closed.json'
ARCHIVE = ROOT / 'nacion/data/execution-sources/2026-11-17'
GROUPS = {
    'funcion': ['finalidad_id', 'funcion_id', 'funcion_desc'],
    'jurisdiccion': ['jurisdiccion_id', 'jurisdiccion_desc'],
    'objeto': ['inciso_id', 'inciso_desc'],
    'territorio': ['ubicacion_geografica_id', 'ubicacion_geografica_desc'],
    'programa': ['jurisdiccion_id', 'servicio_id', 'servicio_desc', 'programa_id', 'programa_desc'],
}
FLOWS = ['credito_devengado', 'credito_pagado']


def build():
    source = ARCHIVE / 'credito-mensual-2026.zip'
    ipc_path = ROOT / 'nacion/data/gestion/ipc_observado.json'
    previous_path = ROOT / 'nacion/data/gestion/gasto_mensual_funcion.json'
    ipc = {r['periodo']: r['indice'] for r in json.loads(ipc_path.read_text(encoding='utf8'))}
    pieces = []
    with zipfile.ZipFile(source) as archive:
        members = [n for n in archive.namelist() if n.endswith('.csv')]
        assert members == ['credito-mensual-2026.csv']
        columns = list(dict.fromkeys(['impacto_presupuestario_mes', 'subsector_id',
                    'clasificador_economico_8_digitos_id', 'ultima_actualizacion_fecha',
                    *FLOWS, *sum(GROUPS.values(), [])]))
        for chunk in pd.read_csv(archive.open(members[0]), decimal=',', usecols=columns,
                                 chunksize=120000, low_memory=False):
            assert chunk.ultima_actualizacion_fecha.str.contains('17 Noviembre 2026').all()
            chunk = chunk[(chunk.subsector_id == 1) &
                          chunk.clasificador_economico_8_digitos_id.astype(str).str.startswith('2')]
            pieces.append(chunk.drop(columns=['ultima_actualizacion_fecha', 'subsector_id',
                                              'clasificador_economico_8_digitos_id']))
    rows = pd.concat(pieces, ignore_index=True)
    annual_source = ARCHIVE / 'credito-anual-2026.zip'
    totals_source = ARCHIVE / 'totales-de-presupuesto.zip'
    def archived_csv(path):
        with zipfile.ZipFile(path) as archive:
            members = [n for n in archive.namelist() if n.endswith('.csv')]
            assert len(members) == 1
            return pd.read_csv(archive.open(members[0]), decimal=',', low_memory=False)
    annual = archived_csv(annual_source)
    official_totals = archived_csv(totals_source).set_index('ejercicio_presupuestario').loc[2026]
    assert annual.ultima_actualizacion_fecha.str.contains('17 Noviembre 2026').all()
    assert set(annual.subsector_id) == {1}
    assert set(annual.clasificador_economico_8_digitos_id.astype(str).str[0]) == {'2'}
    stages = ['credito_presupuestado', 'credito_vigente', 'credito_comprometido', *FLOWS]
    latest_total = {k: float(annual[k].sum()) for k in stages}
    for key in ['credito_presupuestado', 'credito_vigente', 'credito_devengado']:
        assert abs(latest_total[key] - float(official_totals[key])) < .02, key
    for key in FLOWS:
        assert abs(float(rows[key].sum()) - latest_total[key]) < .02, key
    latest_total['porcentaje_ejecucion'] = latest_total['credito_devengado'] / latest_total['credito_vigente'] * 100
    latest_total['devengado_menos_pagado'] = latest_total['credito_devengado'] - latest_total['credito_pagado']
    latest_groups = {}
    for kind, keys in GROUPS.items():
        grouped = annual.groupby(keys, as_index=False, dropna=False)[stages].sum()
        latest_groups[kind] = json.loads(grouped.to_json(orient='records', force_ascii=False, double_precision=10))
    snapshot = []
    for group in [None, *latest_groups['jurisdiccion']]:
        detail = rows if group is None else rows[rows.jurisdiccion_id == group['jurisdiccion_id']]
        monthly = detail.groupby('impacto_presupuestario_mes', as_index=False).credito_devengado.sum()
        months = []
        for row in monthly.itertuples(index=False):
            month = int(row.impacto_presupuestario_mes)
            index = ipc.get(f'2026-{month:02}')
            amount = float(row.credito_devengado)
            months.append({'month': month, 'accrued': amount,
                           'real': amount * ipc['2026-08'] / index if index else None,
                           'partial': month == 11})
        snapshot.append({'name': 'Administración Nacional' if group is None else group['jurisdiccion_desc'],
                         'current': latest_total['credito_vigente'] if group is None else group['credito_vigente'],
                         'months': months})
    complete = rows[rows.impacto_presupuestario_mes <= 10].copy()
    complete['real'] = [amount * ipc['2026-08'] / ipc[f'2026-{month:02}']
                        for amount, month in zip(complete.credito_devengado,
                                                 complete.impacto_presupuestario_mes)]
    complete['paid_real'] = [amount * ipc['2026-08'] / ipc[f'2026-{month:02}']
                             for amount, month in zip(complete.credito_pagado,
                                                      complete.impacto_presupuestario_mes)]
    october = complete[complete.impacto_presupuestario_mes == 10]
    previous = pd.DataFrame(json.loads(previous_path.read_text(encoding='utf8')))
    previous = previous[(previous.anio == 2025) & (previous.impacto_presupuestario_mes <= 10)]
    groups = {}
    for kind, keys in GROUPS.items():
        grouped = complete.groupby(keys, as_index=False, dropna=False)[[*FLOWS, 'real', 'paid_real']].sum()
        month = october.groupby(keys, as_index=False, dropna=False)[[*FLOWS, 'real', 'paid_real']].sum()
        grouped = grouped.merge(month, on=keys, how='left', suffixes=('', '_octubre'), validate='one_to_one')
        # The complete ledger includes these groups, with no October transactions.
        for field in [*FLOWS, 'real', 'paid_real']:
            grouped[field + '_octubre'] = grouped[field + '_octubre'].fillna(0)
        if kind == 'funcion':
            # Function codes remain comparable. Program names alone cannot establish continuity.
            prior = previous.groupby(['finalidad_id', 'funcion_id'], as_index=False)[
                'credito_devengado_real_agosto2026'].sum()
            grouped = grouped.merge(prior, on=['finalidad_id', 'funcion_id'],
                                    validate='one_to_one')
            grouped['variacion_real_pct'] = (
                grouped.real / grouped.credito_devengado_real_agosto2026 - 1) * 100
        groups[kind] = json.loads(grouped.to_json(orient='records', force_ascii=False, double_precision=10))
    total = float(complete.credito_devengado.sum())
    total_real = float(complete.real.sum())
    previous_real = float(previous.credito_devengado_real_agosto2026.sum())
    for kind, records in groups.items():
        assert abs(sum(r['credito_devengado'] for r in records) - total) < .02, kind
        assert abs(sum(r['real'] for r in records) - total_real) < .02, kind
    return {
        'period': '2026-10', 'retrieved': '2026-11-19', 'source_cutoff': '2026-11-17',
        'real_base': '2026-08', 'unit': 'ARS millones',
        'latest_stages': latest_total, 'latest_groups': latest_groups,
        'latest_snapshot': {'cutoff': '2026-11-17', 'execution': snapshot},
        'scope': 'Administración Nacional, gastos corrientes y de capital devengados y pagados.',
        'method': 'Enero–octubre completo. Cada flujo mensual se ajusta por IPC observado antes de acumular. Las comparaciones interanuales corresponden a funciones; los programas conservan su identificación oficial de 2026.',
        'sources': [{'path': source.relative_to(ROOT).as_posix(),
                     'url': 'https://dgsiaf-repo.mecon.gob.ar/repository/pa/datasets/2026/credito-mensual-2026.zip',
                     'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
                    *[{'path': p.relative_to(ROOT).as_posix(),
                       'url': 'https://dgsiaf-repo.mecon.gob.ar/repository/pa/datasets/' + ('2026/' if p == annual_source else '') + p.name,
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                      for p in [annual_source, totals_source]],
                    {'path': previous_path.relative_to(ROOT).as_posix(),
                     'sha256': hashlib.sha256(previous_path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()},
                    {'path': ipc_path.relative_to(ROOT).as_posix(),
                     'sha256': hashlib.sha256(ipc_path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}],
        'total': {'credito_devengado': total, 'credito_pagado': float(complete.credito_pagado.sum()),
                  'october_accrued': float(october.credito_devengado.sum()),
                  'real': total_real, 'previous_real': previous_real,
                  'variacion_real_pct': (total_real / previous_real - 1) * 100},
        'groups': groups,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    if args.check:
        assert result == json.loads(OUT.read_text(encoding='utf8'))
        assert result['latest_snapshot'] == json.loads((ROOT / 'nacion/data/execution-latest.json').read_text(encoding='utf8'))
    else:
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf8')
        (ROOT / 'nacion/data/execution-latest.json').write_text(
            json.dumps(result['latest_snapshot'], ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8')
    print('Cierre de octubre: funciones, organismos, objetos y programas conciliados.')

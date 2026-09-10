"""Validate annual spending authorizations and publish their municipal coverage."""
import csv
import json
import re
from datetime import date
from decimal import Decimal
from html import escape


def apply_annual_budgets(municipalities, path):
    audit = json.loads(path.read_text(encoding='utf-8'))
    verified = date.fromisoformat(audit['verifiedAt'])
    year = audit['targetYear']
    if audit['currency'] != 'ARS' or audit['priceBasis'] != 'nominal' or audit['populationYear'] != 2022:
        raise ValueError('Annual budget units changed')
    for m in municipalities.values():
        m['annualBudget'] = None
    seen = set()
    for record in audit['records']:
        ident = record['id']
        if ident not in municipalities or ident in seen:
            raise ValueError('Duplicate or unknown annual budget: ' + ident)
        seen.add(ident)
        asof = date.fromisoformat(record['asOf'])
        budget_year = record['year']
        if type(budget_year) is not int or not 2020 <= budget_year <= year or asof > verified or asof.year not in (budget_year - 1, budget_year):
            raise ValueError('Invalid annual budget date: ' + ident)
        amounts = {key: Decimal(record[key]) if record.get(key) is not None else None for key in ('original', 'current', 'modifications')}
        if all(amounts[key] is None for key in ('original', 'current')) or any(v is not None and (not v.is_finite() or (v < 0 and key != 'modifications')) for key, v in amounts.items()):
            raise ValueError('Missing or invalid annual authorization: ' + ident)
        if amounts['current'] is not None:
            start = date.fromisoformat(record['periodStart'])
            # A quarterly movement must not be passed off as the annual ceiling.
            if start.year != budget_year or start.month != 1 or asof.year != budget_year or start > asof:
                raise ValueError('Annual opening balance not documented: ' + ident)
        if amounts['modifications'] is not None and (amounts['original'] is None or amounts['current'] is None or abs(amounts['original'] + amounts['modifications'] - amounts['current']) > Decimal('.01')):
            raise ValueError('Budget amendments do not reconcile: ' + ident)
        if not record.get('scope') or record.get('method') not in {'published_current', 'published_original', 'reconciled_objects', 'reconciled_visual', 'reconciled_economic', 'sum_disjoint_components'} or not record.get('documents'):
            raise ValueError('Missing annual budget scope or evidence: ' + ident)
        for doc in record['documents']:
            if not doc['url'].startswith(('https://', 'http://')) or not re.fullmatch('[a-f0-9]{64}', doc['sha256']) or doc['bytes'] <= 0 or not doc.get('locator'):
                raise ValueError('Invalid budget source: ' + ident)
            if doc.get('pages') is not None and (not doc['consultedPages'] or any(type(p) is not int or not 1 <= p <= doc['pages'] for p in doc['consultedPages'])):
                raise ValueError('Invalid budget source page: ' + ident)
        parts = record.get('components', [])
        if record['method'].startswith(('reconciled_', 'sum_')) and not parts:
            raise ValueError('Budget reconciliation missing: ' + ident)
        if parts:
            values = [Decimal(r['amount']) for r in parts]
            field = record['componentField']
            if field not in ('original', 'current') or amounts[field] is None or any(not v.is_finite() or v < 0 for v in values) or abs(sum(values) - amounts[field]) > Decimal('.02'):
                raise ValueError('Annual budget components do not reconcile: ' + ident)
        m = municipalities[ident]
        population = m['poblacion_2022']
        if not isinstance(population, (int, float)) or population <= 0:
            raise ValueError('Invalid population denominator: ' + ident)
        chosen = 'current' if amounts['current'] is not None else 'original'
        m['annualBudget'] = {**record, **{k: float(v) if v is not None else None for k, v in amounts.items()},
                             'amount': float(amounts[chosen]), 'basis': chosen,
                             'perCapita': float(amounts[chosen] / Decimal(str(population))),
                             'historical': budget_year < year, 'verifiedAt': audit['verifiedAt'],
                             'components': [{'label': p['label'], 'amount': float(p['amount'])} for p in parts]}
        # Keep the detailed accounts and the new summary on the same ceiling.
        detail = m.get('management', {}).get('budget') if m.get('management') else None
        if detail and detail['fin'] == record['asOf'] and abs(detail['current'] - float(amounts['current'])) > .02:
            raise ValueError('Annual budget disagrees with detailed accounts: ' + ident)
    pending = [r['id'] for r in audit['pending']]
    if len(set(pending)) != len(pending) or set(pending) & seen or seen | set(pending) != set(municipalities):
        raise ValueError('Annual budget coverage must identify every municipality exactly once')
    coverage = {'targetYear': year, 'verifiedAt': audit['verifiedAt'], 'available': len(seen),
                'currentYear': sum(r['year'] == year for r in audit['records']),
                'historical': sum(r['year'] < year for r in audit['records']), 'pending': len(pending)}
    return audit, coverage


def write_budget_catalog(root, municipalities, coverage):
    target = root / 'municipios/data/presupuestos_anuales.csv'
    def amount(v):
        return '' if v is None else f'{v:.2f}'
    def pretty(v, millions=False):
        if v is None:
            return 'Sin dato verificado'
        return '$' + f'{v / (1e6 if millions else 1):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    rows = sorted(municipalities.values(), key=lambda m: m['municipio'])
    with target.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id', 'Municipio', 'Estado', 'Ejercicio', 'Fecha del documento o corte', 'Original ARS', 'Vigente ARS', 'Dato destacado', 'ARS por habitante Censo 2022', 'Población Censo 2022', 'Alcance', 'Nota', 'Documentos'])
        for m in rows:
            b = m['annualBudget']
            writer.writerow([m['id'], m['municipio'], ('Histórico' if b['historical'] else '2026 verificado') if b else 'Pendiente',
                             b['year'] if b else '', b['asOf'] if b else '', amount(b['original']) if b else '', amount(b['current']) if b else '',
                             b['basis'] if b else '', amount(b['perCapita']) if b else '', m['poblacion_2022'], b['scope'] if b else '', b['note'] if b else '',
                             ' | '.join(d['url'] for d in b['documents']) if b else ''])
    cards = []
    for m in rows:
        b = m['annualBudget']
        heading = f'<h2><a href="./?municipio={m["id"]}&amp;vista=recursos#annual-budget-resources">{escape(m["municipio"])}</a></h2>'
        if b:
            label = 'Vigente' if b['basis'] == 'current' else 'Original publicado'
            status = ' · Dato histórico: falta 2026' if b['historical'] else ''
            body = f'<p><strong>{b["year"]} · {label}{status}</strong></p><p class="budget-catalog-value">{pretty(b["amount"], True)} millones</p><p>{pretty(b["perCapita"])} por habitante del Censo 2022.</p><p>Documento o corte: {b["asOf"]}. Pesos corrientes.</p>'
            links = ' · '.join(f'<a href="{escape(d["url"], quote=True)}" target="_blank" rel="noopener">Documento oficial {i}</a>' for i, d in enumerate(b['documents'], 1))
            body += f'<p>{escape(b["scope"])}</p><p>{escape(b["note"])}</p><p>{links}</p>'
        else:
            body = '<p><strong>Presupuesto anual pendiente de verificación</strong></p><p>No se incorporó un total anual respaldado por un documento oficial. Esto no significa que el municipio no tenga presupuesto.</p>'
        cards.append(f'<article class="coverage-card" id="m-{m["id"]}">{heading}{body}</article>')
    page = f'''<!doctype html><html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Presupuestos anuales · Municipios · Federico Pellegrini</title><link rel="stylesheet" href="styles.css?v=20260910-1"></head><body><main class="coverage-page">
<a class="button" href="./">← Volver al tablero municipal</a><h1>El presupuesto de los 135 municipios</h1>
<p>Revisión del {coverage['verifiedAt']}. El presupuesto indica cuánto está autorizado gastar durante el año. El original es el monto de partida; el vigente incorpora modificaciones hasta la fecha indicada. No representa gasto ejecutado ni dinero disponible.</p>
<div class="coverage-summary"><p><strong>{coverage['currentYear']}</strong> con presupuesto de 2026</p><p><strong>{coverage['historical']}</strong> con un presupuesto anterior</p><p><strong>{coverage['pending']}</strong> pendientes de verificación</p></div>
<p>Los importes están en pesos corrientes, sin ajustar por inflación. El dato por habitante divide el presupuesto destacado por la población del Censo 2022; no es dinero que recibe cada vecino ni mide calidad de gestión. Los cortes y organismos incluidos varían entre municipios. Este listado conserva esas diferencias y no ordena los montos como un ranking.</p>
<p><a class="button" href="data/presupuestos_anuales.csv" download>Descargar los 135 municipios (CSV) ↓</a></p>
<h2>Qué falta del ejercicio 2026</h2><p>{escape(', '.join(m['municipio'] for m in rows if not m['annualBudget'] or m['annualBudget']['historical']))}.</p>
<div class="coverage-list">{''.join(cards)}</div><p>Federico Pellegrini · <a href="./">Tablero municipal</a></p></main></body></html>'''
    (root / 'municipios/presupuestos.html').write_text(page, encoding='utf-8')

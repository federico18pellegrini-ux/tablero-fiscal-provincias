"""Build explicit municipal coverage and an INDEC index for the price comparator."""
import argparse
import csv
import hashlib
import html
import io
import json
from pathlib import Path
from scripts_municipal_coverage import enrich_coverage, matrix_csv

ROOT = Path(__file__).resolve().parent
M = ROOT / 'municipios'


def coverage(data):
    result = []
    for m in data['municipalities']:
        f, o, e = (m.get(k) for k in ['fiscal', 'fiscalOther', 'fiscalExecution'])
        status = 'Comparable a junio de 2026' if f else 'Otro período' if o else 'Ejecución parcial' if e else 'Cuenta no verificada'
        latest = max((x for x in [f, o, e] if x), key=lambda x: x['fin'], default=None)
        missing = []
        if not f:
            missing.append('Cuenta de ingresos y gastos, sin financiamiento, enero–junio de 2026')
        for group, account in [('junio de 2026', f), ('otro período', o)]:
            if account and account.get('personal_devengado') is None:
                missing.append('Gasto en personal: ' + group)
        for year in [2023, 2024]:
            for key, label in [('prestamos', 'Préstamos bancarios'), ('depositos', 'Depósitos bancarios')]:
                if m.get(f'{key}_{year}_ars') is None:
                    missing.append(f'{label} {year}: reservado o sin dato de origen')
        if m.get('empleo_industrial_dic2025') is None:
            missing.append('Empleo industrial diciembre de 2025: reservado o sin dato')
        if m.get('empleo_industrial_cambio_dic2023_dic2025_pct') is None:
            missing.append('Cambio industrial 2023–2025: falta al menos un corte publicado')
        reserved = [s['name'] for s in m['sectors'] if s['jobs'] is None]
        if reserved:
            missing.append('Sectores de empleo con reserva o sin cifra: ' + ', '.join(reserved))
        if m.get('crecimiento_poblacion_2010_2022_pct') is None:
            missing.append('Crecimiento de población 2010–2022: límites territoriales sin homologar')
        if not m.get('annualBudget') or m['annualBudget']['historical']:
            missing.append('Presupuesto anual 2026: pendiente de documento oficial verificado')
        if m.get('management'): missing.extend(m['management']['pending'])
        result.append({'id': m['id'], 'municipio': m['municipio'], 'fiscalStatus': status,
                       'comparable': bool(f), 'latestFiscalEnd': latest['fin'] if latest else None,
                       'missing': missing, 'portalReview': m['fiscalSearch']['reviewedAt'],
                       'portalStatus': m['fiscalSearch']['message']})
    return enrich_coverage(data, {'generated': data['generated'], 'scope': 'Datos incorporados; no certifica que un municipio no publique información en otro sitio.',
            'commonPending': ['Caja de libre disponibilidad, luego de obligaciones y fondos afectados.',
                              'Stock y calendario de deuda municipal comparables para los 135: se incorporaron pasivos de Las Heras (junio 2026) y deuda consolidada y flotante de Tigre (diciembre 2025), sin calendario futuro.',
                              'Ingresos y gastos fiscales mensuales para ajustar cada flujo por inflación.',
                              f"Presupuesto anual: {data['annualBudgetCoverage']['currentYear']} municipios con 2026 y {data['annualBudgetCoverage']['historical']} con años anteriores; {data['annualBudgetCoverage']['pending']} pendientes de verificación. Los cortes y organismos incluidos pueden diferir."],
            'municipalities': result})


def outputs():
    data = json.loads((M/'data/dashboard.json').read_text(encoding='utf-8'))
    cov = coverage(data)
    source = json.loads((ROOT/'data/ipc_source.json').read_text(encoding='utf-8'))
    raw = (ROOT/'data/ipc_national_index.csv').read_text(encoding='utf-8')
    indices = {r['period']: float(r['ipc_index']) for r in csv.DictReader(io.StringIO(raw))}
    assert indices['2016-12'] == 100 and all(v > 0 for v in indices.values())
    assert max(indices) == data['priceBase'] == source['latest_period']
    prices = {'generated': data['generated'], 'series': source['source'], 'source': source['url'],
              'sourceSha256': hashlib.sha256(raw.encode()).hexdigest(), 'latest': max(indices),
              'bases': ['2024-12', '2025-12', data['priceBase']], 'indices': indices}
    contents = {M/'data/deflator.json': json.dumps(prices, ensure_ascii=False, indent=2)+'\n',
                M/'data/cobertura.json': json.dumps(cov, ensure_ascii=False, indent=2)+'\n',
                M/'data/matriz_faltantes.csv': matrix_csv(cov)}
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, delimiter=';', lineterminator='\n')
    writer.writerow(['Código', 'Municipio', 'Estado fiscal', 'Último cierre incorporado', 'Comparable junio 2026', 'Faltantes específicos', 'Revisión de portal', 'Alcance de la búsqueda'])
    for r in cov['municipalities']:
        writer.writerow([r['id'], r['municipio'], r['fiscalStatus'], r['latestFiscalEnd'] or '', 'Sí' if r['comparable'] else 'No', ' | '.join(r['missing']), r['portalReview'], r['portalStatus']])
    contents[M/'data/cobertura.csv'] = '\ufeff'+buffer.getvalue()
    esc = html.escape
    cards = []
    for r in cov['municipalities']:
        issues = ''.join('<li>'+esc(v)+'</li>' for v in r['missing']) or '<li>Sin faltantes en las variables específicas de este listado.</li>'
        findings = ''.join(f'<p><strong>Hallazgo de la búsqueda:</strong> {esc(f["note"])} <a href="{esc(f["url"], quote=True)}">Abrir documento o portal</a></p>' for f in r['findings'])
        portal = f'<a href="{esc(r["portalUrl"], quote=True)}">Portal para buscar o solicitar los documentos</a>' if r['portalUrl'] else ''
        budget = f'Presupuesto {r["budgetYear"]} · corte {r["budgetAsOf"]}' if r['budgetYear'] else 'Presupuesto anual pendiente'
        cards.append(f'''<article id="m-{r['id']}" class="coverage-card"><h2><a href="./?municipio={r['id']}&amp;vista=recursos">{esc(r['municipio'])}</a></h2><p><strong>{esc(r['fiscalStatus'])}</strong> · Último cierre: {esc(r['latestFiscalEnd'] or 'sin cuenta incorporada')}</p><p>{esc(budget)}. Original 2026: {'incorporado' if r['budgetOriginal2026'] else 'pendiente'}; vigente 2026: {'incorporado' if r['budgetCurrent2026'] else 'pendiente'}.</p>{findings}<ul>{issues}</ul><p>{portal}</p><p class="chart-caption">Revisión del portal: {r['portalReview']}. {esc(r['portalStatus'])}</p></article>''')
    counts = {key: sum(r['fiscalStatus'] == key for r in cov['municipalities']) for key in ['Comparable a junio de 2026', 'Otro período', 'Ejecución parcial', 'Cuenta no verificada']}
    groups = []
    for label, title in [('Cuenta no verificada', 'Municipios sin cuenta ni ejecución incorporada'), ('Otro período', 'Municipios con cuentas de otro período'), ('Ejecución parcial', 'Ejecución parcial: falta separar las operaciones financieras')]:
        links = ', '.join(f"<a href='#m-{r['id']}'>{esc(r['municipio'])}</a>" for r in cov['municipalities'] if r['fiscalStatus'] == label)
        if not links: continue
        groups.append('<h3>'+title+'</h3><p>'+links+'.</p>')
    grouped_names = ''.join(groups)
    common = ''.join('<li>'+esc(v)+'</li>' for v in cov['commonPending'])
    topic_cards = ''.join(f'<article class="coverage-card"><h3>{esc(t["topic"])}</h3><p><strong>{t["available"]} de {t["total"]}</strong> con el dato incorporado en el alcance indicado.</p></article>' for t in cov['topics'])
    search = cov['research']
    findings_intro = f"Se revisaron {search['pagesReviewed']} direcciones de portales de los 135 municipios: {search['pagesResponded']} respondieron correctamente. Se recuperaron {search['downloadsRetrieved']} de {search['downloadsAttempted']} documentos candidatos. Localizar un archivo no significa que su contenido ya esté validado."
    contents[M/'cobertura.html'] = f'''<!doctype html><html lang="es-AR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Qué datos faltan · Municipios · Federico Pellegrini</title><link rel="stylesheet" href="styles.css?v=20260911-3"></head><body><main class="coverage-page"><a class="button" href="./">← Volver al tablero municipal</a><h1>Qué datos tenemos y qué falta</h1><p>Inventario del {data['generated']}. Cada dato conserva su período. Transferencias: julio de 2026; empleo y salarios: diciembre de 2025; población y condiciones de vida: Censo 2022; producto municipal: 2023; delitos registrados: 2025. Una cuenta no incorporada no significa que el municipio no la publique. Los valores reservados no se reemplazan por cero.</p><div class="coverage-summary"><p><strong>{counts['Comparable a junio de 2026']}</strong> municipios comparables a junio de 2026</p><p><strong>{counts['Otro período']}</strong> con cuentas solo de otro período</p><p><strong>{data['annualBudgetCoverage']['currentYear']}</strong> con presupuesto de 2026</p><p><strong>{counts['Cuenta no verificada']}</strong> sin una cuenta ni ejecución incorporada</p></div><p>El ranking fiscal no permite identificar el mayor déficit de los 135 municipios. Ayacucho ya tiene el gasto en personal del semestre completo. Baradero, General La Madrid y General Lavalle se incorporan al corte comparable de junio.</p><p>Hay cobertura de los 135 en transferencias, empleo total, salarios, producto municipal, población censal de 2022, NBI, salud, hacinamiento, delitos registrados, relevamiento externo de deuda personal y puntajes de publicación fiscal, cada bloque con su fecha y alcance.</p><p>{esc(findings_intro)}</p><p><a class="button" href="data/cobertura.csv" download>Listado de los 135 municipios (CSV)</a> <a class="button button-quiet" href="data/matriz_faltantes.csv" download>Qué documento falta por tema (CSV)</a></p><h2>La cobertura, tema por tema</h2><p>Estas cifras miden presencia de datos. No califican la gestión ni aseguran que todos los cortes sean iguales. Ningún municipio tiene completos todos los datos necesarios para evaluar caja y vencimientos.</p><div class="coverage-topics">{topic_cards}</div><p><a href="auditoria.html">Ver los controles de datos y metodología →</a></p><h2>Qué municipios faltan en el ranking fiscal</h2>{grouped_names}<p><a class="button button-quiet" href="presupuestos.html">Ver presupuesto anual y faltantes de los 135 municipios →</a></p><h2>Datos aún no incorporados de forma comparable</h2><ul>{common}</ul><p>La mayoría de los faltantes bancarios y sectoriales proviene de cifras reservadas o ausentes en las estadísticas de origen. Los indicadores de desempleo, informalidad y pobreza por ingresos tampoco están incorporados como series representativas de cada uno de los 135 municipios. No se deducen a partir del empleo registrado ni del Censo.</p><h2>El detalle de los 135 municipios</h2><p>El listado está desplegado completo. Para ubicar un nombre se puede usar la búsqueda de esta página del navegador.</p><div class="coverage-list">{''.join(cards)}</div><footer class="site-footer"><strong>Federico Pellegrini</strong><a href="metodologia.html">Fuentes, períodos y criterios</a></footer></main></body></html>'''
    return contents


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    expected = outputs()
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, text in expected.items() if not p.exists() or p.read_text(encoding='utf-8') != text]
        if stale: raise SystemExit('Municipal tools are stale: '+', '.join(stale))
    else:
        for path, text in expected.items(): path.write_text(text, encoding='utf-8', newline='\n')
    print('Cobertura de 135 municipios e IPC: verificados.')

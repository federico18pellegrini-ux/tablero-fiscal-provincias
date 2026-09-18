"""A brief federal sheet. Exact jurisdiction codes and normalized project names only."""
from xml.sax.saxutils import escape


def territory_data(budget, management, province_id):
    rows = [p for p in management['provinces']['comparison'] if p['provincia_id'] == province_id]
    assert len(rows) == 1, 'Unknown or duplicate jurisdiction'
    p = rows[0]
    geos = [g for g in budget['geographies'] if g['name'] == p['provincia']]
    observed = [g for g in management['execution']['groups']['territorio'] if g['ubicacion_geografica_id'] == province_id]
    assert len(geos) == len(observed) == 1, 'Ambiguous territorial link'
    for old, new in [('law', 'credito_presupuestado'), ('current', 'credito_vigente'), ('accrued', 'credito_devengado')]:
        assert abs(geos[0][old] - observed[0][new]) < .01
    works = sorted([w for w in budget['works'] if w['province'] == p['provincia']], key=lambda w: (-w['project'], w['id']))
    return dict(province=p, project=geos[0], observed=observed[0], works=works,
                worksTotal=sum(w['project'] for w in works), pending=p['presupuestarias_devengado']-p['presupuestarias_pagado'])


def province_page(r, management, province_id):
    from scripts_export_national_reports import WIDTH, SITE, money, num, pct
    t = territory_data(r.d, management, province_id)
    p, g, o, works = t['province'], t['project'], t['observed'], t['works']
    name = escape(p['provincia'])
    r.section('Ficha / Nación en la provincia', name,
              'DNAP: recursos nacionales enero-agosto 2026. Presupuesto Abierto: 15/09/2026. ONP: proyecto 2027, cuadros 6 y planilla 12.', first=True)
    r.add(f"Los recursos de origen nacional {'perdieron' if p['variacion_real_pct']<0 else 'ganaron'} <b>{num(abs(p['variacion_real_pct']))}% de poder de compra</b> frente a enero-agosto de 2025. Eso {'achica' if p['variacion_real_pct']<0 else 'amplía'} el margen para sostener servicios con esos fondos. El cambio real descuenta la inflación de cada mes.")
    r.add('Qué recibió el gobierno provincial', 'heading')
    r.table(['Concepto / período', 'Monto'], [
        ['Recursos nacionales / enero-agosto', money(p['ron_2026'])],
        ['Transferencias presupuestarias reconocidas / al 15/09', money(p['presupuestarias_devengado'])],
        ['Transferencias presupuestarias pagadas / al 15/09', money(p['presupuestarias_pagado'])],
        ['Diferencia pendiente de pago / al 15/09', money(t['pending'])],
    ], [WIDTH-140, 140], compact=True)
    r.note('Pesos corrientes. Recursos nacionales incluyen coparticipación y otros regímenes. Las transferencias son del presupuesto nacional. Pendiente de pago no identifica qué parte está vencida. Estos renglones no se suman.')
    r.add('El gasto de Nación en el territorio', 'heading')
    r.add(f"Nación reconoció gastos por <b>{money(o['credito_devengado'])}</b> al 15/09, sobre {money(o['credito_vigente'])} autorizados. Incluye jubilaciones, salarios, servicios y transferencias; no es dinero que recibe íntegramente el gobierno provincial.", 'small')
    r.add(f"Para 2027 propone <b>{money(g['project'])}</b> en esta ubicación. Dentro de ese monto figuran <b>{len(works)} partidas de inversión por {money(t['worksTotal'])}</b>.")
    r.table(['Base de comparación 2026', 'Cambio en pesos', 'Cambio real'], [
        [label, pct((g['project']/g[key]-1)*100, True), pct((g['project']*r.d['deflator']['annual_factors']['2027']/(g[key]*r.d['deflator']['annual_factors']['2026'])-1)*100, True)]
        for key,label in [('current','Vigente al 15/09'),('closing','Cierre estimado')]
    ], [WIDTH-190, 95, 95], compact=True)
    r.note('Real: escenario de inflación promedio anual del tablero. El proyecto 2027 es una propuesta; no es gasto ya realizado.')
    r.add('Las partidas de inversión de mayor monto', 'heading')
    r.table(['Partida propuesta para 2027', 'Monto'], [[w['name'], money(w['project'])] for w in works[:3]], [WIDTH-120, 120], compact=True)
    r.add('Recomendamos seguir por separado los fondos provinciales y la ejecución nacional. Para las obras, el monto propuesto tiene que contrastarse con el cronograma, los contratos y el costo pendiente antes de evaluar si alcanza.', 'small')
    sources = [(management['datasets']['ron_provincias_mensual']['sources'][0]['url'], 'Recursos nacionales'),
               (management['datasets']['transferencias_presupuestarias_provincias']['sources'][0]['url'], 'Transferencias y ejecución'),
               (next(s['url'] for s in r.d['sources'] if s['file']==g['source']), 'Proyecto 2027'),
               (SITE+f'?distrito={province_id}#provincias-nacion', 'Abrir esta provincia')]
    r.note(' · '.join(f'<link href="{escape(url)}" color="#254b73">{label}</link>' for url,label in sources))

"""Concise portfolio reports, generated from the same verified web package."""
from xml.sax.saxutils import escape
from urllib.parse import quote


def portfolio_pages(r,d,code):
    from scripts_export_national_reports import WIDTH,SITE,money,num,pct,ratio,change
    p=next(p for p in d['portfolios'] if p['id']==code)
    j,e=p['project'],p['execution'];f=r.d['deflator']['annual_factors']
    programs=[next(x for x in r.d['programs'] if x['id']==i) for i in p['program_ids']]
    works=[next(x for x in r.d['works'] if x['id']==i) for i in p['work_ids']]
    real=lambda row,base:change(row['project']*f['2027'] if row['project'] is not None else None,row[base]*f['2026'] if row.get(base) is not None else None)
    source='ONP: proyecto 2027, cuadro 4 y planillas 7 y 12. Presupuesto Abierto: finanzas al 15/09/2026; metas a junio.'
    r.s['title'].fontSize=22;r.s['title'].leading=27
    r.section('Informe ejecutivo / Ministerio o poder',escape(p['name']),source,first=True)
    if j['project'] is None:
        r.add('Interior no tiene una jurisdicción con el mismo nombre en el proyecto 2027. Sus funciones aparecen en otras áreas. La ausencia de esta fila no representa un recorte a cero.')
    else:
        r.add(f"El proyecto asigna <b>{money(j['project'])}</b>, el {num(ratio(j['project'],r.d['total']['project']),2)}% del gasto nacional. Frente al vigente de 2026, el monto {'sube' if real(j,'current')>=0 else 'baja'} {num(abs(real(j,'current')))}% después de descontar la inflación del escenario.")
        r.add(f"La partida de mayor monto es <b>{escape(programs[0]['name'])}</b>. Representa el {num(ratio(programs[0]['project'],j['project']))}% de esta cartera y explica dónde se concentra su presupuesto.",'small')
    r.table(['Base 2026','Monto / $ millones','Cambio nominal','Cambio real'],[
        [label,num(j.get(k),0),pct(change(j['project'],j.get(k)),True),pct(real(j,k),True)]
        for k,label in [('law','Inicial'),('current','Vigente al 15/09'),('closing','Cierre estimado')]
    ],[155,125,115,WIDTH-395])
    r.note(p['scope_note']+' Real: después de descontar inflación. Montos en pesos corrientes; s/c: sin comparación.')
    r.add('Cómo avanza el presupuesto de 2026','heading')
    r.table(['Etapa al 15/09/2026','Monto'],[[label,money(e[k])] for label,k in [
        ('Presupuesto vigente','credito_vigente'),('Comprometido','credito_comprometido'),
        ('Gasto reconocido','credito_devengado'),('Pagado','credito_pagado')]], [WIDTH-145,145])
    r.add(f"Se reconoció como gasto el <b>{num(ratio(e['credito_devengado'],e['credito_vigente']))}% del vigente</b>. La diferencia entre lo reconocido y lo pagado es {money(e['credito_devengado']-e['credito_pagado'])}. El registro no informa qué parte está vencida.")
    r.note('El porcentaje mide uso de la autorización anual, no calidad del servicio. Septiembre es parcial y el gasto no se distribuye uniformemente durante el año.')
    r.note(f'<link href="{SITE}?cartera={code}#carteras" color="#254b73">Abrir esta cartera en el tablero</link>')

    r.section('Prioridades / Programas','Dónde se concentra el gasto',source)
    if programs:
        r.table(['Principales partidas / organismo','Proyecto / $M','Cambio real'],[
            [x['name']+' / '+x['entity'],num(x['project'],0),pct(real(x,'current'),True)] for x in programs[:8]
        ],[WIDTH-165,85,80],compact=True)
        share=ratio(sum(x['project'] for x in programs[:8]),j['project'])
        n=min(8,len(programs))
        selection='Esta partida reúne' if n==1 else f'Estas {n} partidas reúnen'
        total='una partida' if len(programs)==1 else f'{len(programs)} partidas'
        r.add(f"{selection} el <b>{num(share)}% del presupuesto propuesto</b>. La cartera tiene {total} en total. La selección permite identificar dónde una modificación tiene mayor impacto presupuestario.")
        r.note('Cambio real: proyecto 2027 frente al vigente de 2026, descontando la inflación del escenario.')
        missing=[x for x in programs if not x['matched']]
        if missing:r.note(f"{len(missing)} partidas conservan su monto 2027 pero no una base individual comparable. Sus cambios de alcance están documentados en el tablero.")
    else:
        r.add('Las partidas del proyecto se consultan en las carteras que reciben las funciones. No corresponde convertir la ausencia de un programa en una caída de 100%.')
    physical=p['physical']
    r.add('Qué sabemos de las prestaciones','heading')
    if physical['count']:
        r.add(f"En enero-junio se informó ejecución en <b>{physical['reported']} de {physical['count']} mediciones físicas</b>. En {physical['comparable']} se puede contrastar la cantidad realizada con lo programado. Este conteo mide disponibilidad de información, no cumplimiento agregado ni calidad de los servicios.")
        r.note('Las mediciones conservan sus unidades y métodos. Los promedios de personas, las entregas acumuladas y los indicadores de corte no se suman entre sí.')
    else:r.add('El archivo de metas del segundo trimestre no incluye mediciones de esta jurisdicción. Eso no equivale a una ejecución nula.')
    linked=[x for x in d['policies'] if x['program']['id'] in p['program_ids']]
    if linked:
        r.add('Lecturas para profundizar','heading')
        r.note(' · '.join(f'<link href="{SITE}#politica-{x["slug"]}" color="#254b73">{escape(x["title"])}</link>' for x in linked))
    r.note(f'<link href="{SITE}?buscar={quote(p["name"])}#programas" color="#254b73">Consultar todos los programas y sus documentos</link>')

    if works:
        r.section('Continuidad / Inversión','Qué obras tienen presupuesto',source)
        selection='Las cinco de mayor monto se muestran abajo.' if len(works)>5 else 'El detalle se muestra abajo.'
        r.add(f"La planilla 12 incluye <b>{len(works)} partidas por {money(p['works_total'])}</b>. Son parte del presupuesto de la cartera y no deben sumarse de nuevo al total. {selection}")
        r.table(['Proyecto / ubicación','Proyecto 2027 / $M'],[[x['name']+' / '+x['province'],num(x['project'],0)] for x in works[:5]],[WIDTH-100,100],compact=True)
        r.add('Qué revisar antes de comprometer recursos','heading')
        r.add('La asignación anual permite identificar qué proyectos reciben recursos. Para evaluar si pueden terminarse, hace falta cruzarla con contratos, avance físico, cronograma y costo actualizado de terminación. Un porcentaje de avance no permite deducir cuánto dinero falta.')
        if code==50:
            r.note(f'<link href="{SITE}#obra-ra10" color="#254b73">RA-10: presupuesto, financiamiento, avance global y actualización del montaje</link>')
        r.note(f'<link href="{SITE}#obras" color="#254b73">Explorar la inversión y sus fuentes de financiamiento</link>')
    else:r.note('La planilla 12 no identifica proyectos para esta jurisdicción en 2027. No es una medición de todas sus compras de bienes de capital.')
    sources={x['file']:x for x in r.d['sources']}
    r.note(' · '.join(f'<link href="{sources[file]["url"]}" color="#254b73">{label}</link>' for file,label in [('cap1cu04.pdf','Totales por jurisdicción'),('cap1pla7.pdf','Programas'),('cap1pl12.pdf','Proyectos')]))
    r.note(' · '.join(f'<link href="{escape(d["policies"][0]["sources"][key]["url"])}" color="#254b73">{label}</link>' for key,label in [('execution','Ejecución y pagos'),('physical','Metas y prestaciones')]))

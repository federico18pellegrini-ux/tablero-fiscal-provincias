"""Brief, source-linked decision chapters and standalone one-page sheets."""
from xml.sax.saxutils import escape

def additional_policy_page(r,d,slug):
    from scripts_export_national_reports import WIDTH,SITE,money,num,pct,change,ratio
    p=next(p for p in d['policies'] if p['slug']==slug);e=p['execution'];f=r.d['deflator']['annual_factors']
    editorial=p['editorial'];real=lambda key:change(p['program']['project']*f['2027'],p['program'][key]*f['2026'])
    r.s['title'].fontSize=23;r.s['title'].leading=28
    r.section('Ficha / Política pública',p['title'],'ONP: proyecto 2027. Presupuesto Abierto: finanzas al 15/09/2026; prestaciones enero-junio 2026.',first=True)
    r.add(f"El proyecto destina <b>{money(p['program']['project'])}</b>. Frente al vigente de 2026, su poder de compra {'cae' if real('current')<0 else 'sube'} <b>{num(abs(real('current')))}%</b>, con la inflación del escenario del tablero.")
    r.table(['Base de comparación','Cambio nominal','Cambio real'],[[label,pct(change(p['program']['project'],p['program'][k]),True),pct(real(k),True)] for k,label in [('law','Inicial 2026'),('current','Vigente 2026')]], [WIDTH-180,90,90])
    r.note('Montos en pesos corrientes. Real: después de descontar inflación. El cierre estimado no está publicado para este programa.')
    r.add('Del presupuesto al pago','heading')
    r.table(['Vigente 2026','Gasto reconocido','Pagado'],[[money(e[k]) for k in ['credito_vigente','credito_devengado','credito_pagado']]],[WIDTH/3]*3)
    unpaid=e['credito_devengado']-e['credito_pagado']
    payment_reading='Al corte, todo el gasto reconocido figura pagado.' if unpaid==0 else f'La diferencia entre gasto reconocido y pagado es {money(unpaid)}; no identifica qué parte está vencida.'
    r.add(f"Se ejecutó el {num(ratio(e['credito_devengado'],e['credito_vigente']))}% del vigente. {payment_reading}",'small')
    r.add('Qué muestran las prestaciones','heading')
    r.add(escape(editorial['reading']))
    r.add('Qué revisar para decidir','heading')
    r.add(escape(editorial['recommendation']))
    reported=sum(x['ejecutado_acumulado_trim2'] is not None for x in p['physical'])
    missing=' Las restantes conservan el estado sin dato.' if reported<len(p['physical']) else ''
    r.note(f"{reported} de {len(p['physical'])} mediciones con ejecución informada.{missing} Organismo: {p['program']['entity']}. SAF {p['link']['servicio_id']}, programa {p['link']['programa_id']}.")
    links=[(p['sources']['project']['url']+'#page='+str(p['program']['page']),'Presupuesto'),(p['sources']['execution']['url'],'Ejecución'),(p['sources']['physical']['url'],'Prestaciones'),(SITE+'#politica-'+slug,'Ver todas las mediciones')]
    r.note(' · '.join(f'<link href="{escape(url)}" color="#254b73">{label}</link>' for url,label in links))

def policy_page(r,d,slug,first=False):
    from scripts_export_national_reports import WIDTH,money,num,pct,ratio,change,BASES,SITE
    p=next(p for p in d['policies'] if p['slug']==slug);e=p['execution'];f=r.d['deflator']['annual_factors']
    real=lambda base:change(p['program']['project']*f['2027'],p['program'][base]*f['2026'])
    vaccine=slug=='inmunizaciones';title='Vacunas e inmunizaciones' if vaccine else 'Universidades'
    r.section('Ficha / Política pública' if first else '17 / Política pública' if vaccine else '18 / Política pública',title,'ONP: proyecto 2027. Presupuesto Abierto: finanzas al 15/09/2026 y prestaciones enero-junio 2026.',first=first)
    r.note(p['program']['name']+' / '+p['program']['entity'])
    r.add(f"El proyecto destina <b>{money(r.value(p['program']['project']))}</b> a esta política. Frente al vigente, el poder de compra {'cae' if real('current')<0 else 'sube'} <b>{num(abs(real('current')))}%</b>, con la inflación del escenario del tablero.")
    r.table(['Base de 2026','Cambio en pesos','Cambio real'],
       [[BASES[k],pct(change(p['program']['project'],p['program'][k]),True),pct(real(k),True)] for k in ['law','current']]+[['Cierre estimado','No publicado','No publicado']], [WIDTH-190,95,95])
    r.note(f"Proyecto en {r.units.lower()}. Inicial: aprobado al empezar el año. Vigente: autorización al 15/09. Real: después de descontar inflación.")
    r.add('Del presupuesto al pago','heading')
    r.table(['2026 / pesos corrientes','Monto'],[[label,money(e[k])] for label,k in [('Presupuesto vigente','credito_vigente'),('Gasto reconocido','credito_devengado'),('Pagado','credito_pagado')]], [WIDTH-150,150])
    r.add(f"Se ejecutó el {num(ratio(e['credito_devengado'],e['credito_vigente']))}% del vigente. Quedan {money(e['credito_devengado']-e['credito_pagado'])} de gasto reconocido pendiente de pago. El registro no informa qué parte está vencida.",'small')
    r.add('Qué prestaciones se informaron','heading')
    if vaccine:
        m=next(x for x in p['physical'] if x['medicion_fisica_id']==1110)
        r.add(f"Entre enero y junio se distribuyeron <b>{num(m['ejecutado_acumulado_trim2'],0)} dosis</b> de las {num(m['programacion_acumulada_trim2'],0)} programadas. El organismo informó demoras en el ingreso de vacunas. Las dosis distribuidas no equivalen a personas vacunadas; parte de la información de vacunación de las jurisdicciones es parcial.")
        r.add('Recomendamos revisar compras, existencias y fechas de entrega. La caída real justifica mirar si el crédito propuesto alcanza para sostener el calendario de vacunación. No permite afirmar, por sí sola, que la cobertura sanitaria vaya a caer.')
    else:
        reported=sum(x['ejecutado_acumulado_trim2'] is not None for x in p['physical'])
        r.add(f"El segundo trimestre tiene ejecución informada en <b>{reported} de {len(p['physical'])} mediciones</b>. Las restantes quedan sin dato; no equivalen a prestaciones que no se realizaron. Este corte es anterior al financiero.")
        r.add('El proyecto prácticamente mantiene el poder de compra del vigente. Recomendamos contrastarlo con salarios, funcionamiento y prestaciones de las universidades. La variación presupuestaria no alcanza para evaluar la calidad educativa ni para saber si cubre los costos previstos.')
    links=[(p['sources']['project']['url']+'#page='+str(p['program']['page']),'Presupuesto'),(p['sources']['execution']['url'],'Ejecución'),(p['sources']['physical']['url'],'Prestaciones'),(SITE+'#politica-'+slug,'Ficha y todas las mediciones')]
    r.note(' · '.join(f'<link href="{escape(url)}" color="#254b73">{label}</link>' for url,label in links))

def work_page(r,d,first=False):
    from scripts_export_national_reports import WIDTH,money,num,SITE
    w=d['works']['pilot'];o=w['observed'];p=w['project']
    r.section('Ficha / Continuidad de obra' if first else '19 / Continuidad de obra','Reactor RA-10','ONP: proyecto 2027, planilla 12, p. 10. Inversión pública: primer trimestre 2026, pp. 7-8.',first=first)
    r.note('Buenos Aires / Comisión Nacional de Energía Atómica')
    r.add(f"La ONP informó <b>{num(w['progress_pct'],2)}% de avance físico a marzo de 2026</b>. El reactor está destinado a producir radioisótopos de uso médico y ampliar la investigación. El proyecto 2027 propone {money(r.value(p['project']))} para continuar la obra, financiados íntegramente por el Tesoro Nacional.")
    r.note(f"Proyecto en {r.units.lower()}. La información financiera de 2026 se conserva en pesos corrientes.")
    r.table(['Dato','Monto o estado'],[
       ['Presupuesto vigente al 31/03/2026',money(o['credito_vigente_marzo2026_millones'])],
       ['Gasto reconocido en enero-marzo 2026',money(o['devengado_1t2026_millones'])],
       ['Gasto acumulado hasta marzo de 2026',money(o['financiero_acumulado_2025_millones']+o['devengado_1t2026_millones'])],
       ['Costo de referencia del BAPIN',money(w['reference_cost'])],
       ['Costo actualizado para terminar y operar','No publicado en estas fuentes'],
       ['Puesta en marcha / objetivo anunciado','Primeros meses de 2027'],
       ['Cronograma contractual y compromisos pendientes','No publicados en estas fuentes']], [WIDTH-180,180])
    r.add('Qué significa para la continuidad','heading')
    r.add('El 04/09 la CNEA informó 96% de avance del montaje electromecánico y una puesta en marcha prevista para los primeros meses de 2027, sujeta a la licencia de la Autoridad Regulatoria Nuclear. El montaje es una parte de la obra; no reemplaza el avance físico global de marzo.')
    r.add('También anunció capital privado para la planta asociada de radioisótopos. El comunicado no cuantifica esa inversión ni el costo pendiente del reactor. Para evaluar si el presupuesto alcanza faltan contratos y costos de terminación y operación.', 'small')
    r.add('El costo del BAPIN es una referencia del Banco de Proyectos de Inversión Pública, publicada en el informe del primer trimestre. No es un presupuesto actualizado de terminación. Tampoco corresponde usar el porcentaje de avance físico para calcular cuánto dinero falta.')
    r.add('Recomendamos actualizar el costo y el cronograma con el organismo ejecutor. Eso permite evaluar qué asignación sostiene la continuidad y qué recursos necesitará el proyecto cuando empiece a operar.')
    r.note('Correspondencia revisada por denominación, organismo y ubicación. En 2026: SAF 105, programa 20, proyecto 22, obra 51. La planilla 2027 no publica códigos de obra.')
    r.note(f'<link href="{escape(w["sources"]["project"]["url"])}#page=10" color="#254b73">Presupuesto 2027</link> · <link href="{escape(w["sources"]["investment"]["url"])}#page=7" color="#254b73">Costo y avance físico</link> · <link href="https://www.argentina.gob.ar/node/512894" color="#254b73">CNEA 04/09</link> · <link href="{SITE}#obra-ra10" color="#254b73">Abrir la ficha de la obra</link>')

def finance_page(r,d):
    from scripts_export_national_reports import WIDTH,money,num,SITE
    rows={x['id']:x for x in d['finance']['rows']};v=lambda key,year='project':r.value(rows[key][year],2027 if year=='project' else 2026)
    r.section('16 / Cierre y financiamiento','El superávit no elimina los vencimientos','ONP: CAIF del proyecto 2027, cuadro comparativo 1. Administración Nacional. Millones de pesos.')
    r.add(f"El proyecto prevé ingresos por {money(v('VI'))} y gastos por {money(v('VII'))}. La diferencia deja un superávit de <b>{money(v('XI'))}</b>. Además, hay capital de deuda y otros pasivos a devolver por <b>{money(v('XIII.2'))}</b>.")
    r.note(f"Montos en {r.units.lower()}. Este cuadro compara siempre con el cierre estimado 2026, aunque el informe use otra base para las variaciones.")
    labels=[('I','Ingresos corrientes'),('II','Gastos corrientes'),('IV','Ingresos de capital'),('V','Gastos de capital'),('VI','Ingresos totales'),('VII','Gastos totales'),('XI','Resultado financiero')]
    r.table(['Concepto','Cierre 2026 / $M','Proyecto 2027 / $M'],[[label,num(v(key,'closing'),0),num(v(key),0)] for key,label in labels],[WIDTH-190,95,95])
    r.add('De dónde sale el financiamiento y en qué se usa','heading')
    labels=[('XII.1','Reducción de activos financieros'),('XII.2','Endeudamiento y otros pasivos'),('XII.3','Transferencias internas / fuentes'),('XII','Total de fuentes financieras'),('XIII.1','Inversión financiera'),('XIII.2','Amortización y reducción de otros pasivos'),('XIII.3','Transferencias internas / aplicaciones'),('XIII','Total de aplicaciones financieras')]
    r.table(['Concepto','Proyecto 2027 / $M'],[[label,num(v(key),0)] for key,label in labels],[WIDTH-140,140],compact=True)
    r.add('La devolución del capital aparece entre las aplicaciones financieras y no dentro del gasto. El endeudamiento previsto incluye renovaciones; no equivale al incremento neto de deuda. Las transferencias internas figuran a ambos lados y se compensan. El resultado financiero más las fuentes cubre las aplicaciones.','small')
    r.note(f'<link href="{escape(d["finance"]["source"]["url"])}" color="#254b73">Cuadro oficial completo</link> · <link href="{SITE}#escenarios" color="#254b73">Probar escenarios de inflación, ingresos y financiamiento</link>')

def append_decisions(r,d,focus=None):
    if focus in ['inmunizaciones','educacion-superior']:policy_page(r,d,focus,first=True)
    elif focus in ['jubilaciones','alimentacion','medicamentos','seguridad-federal']:additional_policy_page(r,d,focus)
    elif focus=='reactor-ra10':work_page(r,d,first=True)
    elif focus is None:
        finance_page(r,d)
        policy_page(r,d,'inmunizaciones');policy_page(r,d,'educacion-superior');work_page(r,d)
    else:raise ValueError('Ficha no válida')

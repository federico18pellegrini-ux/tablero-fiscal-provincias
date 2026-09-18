"""Observed management chapters, using the same data and scope as /nacion/."""
import json
from xml.sax.saxutils import escape

def append_management(report, data):
    # Imported here to share the report's formatting without a module cycle.
    from scripts_export_national_reports import ROOT, WIDTH, finite, num, money, pct, ratio
    r, g = report, data
    cash = {x['indicador']: x for x in g['cash']['comparison']}
    def cash_value(key):
        return cash[key]['enero_julio_real_2026' if r.mode == 'real' else 'enero_julio_2026']
    def link(key, label):
        url = g['datasets'][key]['sources'][0]['url']
        r.note(f'<link href="{escape(url)}" color="#254b73">{escape(label)}</link>')

    r.section('11 / Caja y pagos', 'La caja tiene superávit; el margen se achica', 'Hacienda: SPN, enero-julio 2026. Presupuesto Abierto: Administración Nacional, 15/09/2026. INDEC: IPC.')
    r.add(f"El Sector Público Nacional cobró {money(cash_value('ingresos_totales'))} y pagó {money(cash_value('gasto_primario'))} antes de intereses. Después de los intereses quedó un superávit de <b>{money(cash_value('resultado_financiero'))}</b>. Los montos de este cuadro están en {r.units.lower()}.")
    r.table(['Caja / enero-julio 2026', 'Monto / millones'],
        [[label, num(cash_value(key), 0)] for key, label in [('ingresos_totales','Ingresos cobrados'),('gasto_primario','Gasto antes de intereses'),('resultado_primario','Resultado antes de intereses'),('intereses_netos','Intereses pagados'),('resultado_financiero','Resultado después de intereses')]], [WIDTH-140,140])
    r.add(f"El dato que merece atención es el poder de compra. Los ingresos cayeron {num(abs(cash['ingresos_totales']['variacion_real_acumulada_pct']))}% real frente a enero-julio de 2025, mientras que el gasto primario cayó {num(abs(cash['gasto_primario']['variacion_real_acumulada_pct']))}%. La recaudación se achicó más rápido que el gasto: eso redujo el margen disponible.")
    r.add('Del gasto reconocido al pago', 'heading')
    t = g['execution']['total']
    r.add(f"En la Administración Nacional, al 15/09 se reconocieron gastos por {money(t['credito_devengado'])} y se pagaron {money(t['credito_pagado'])}. La diferencia es <b>{money(t['devengado_menos_pagado'])}</b>. Son obligaciones reconocidas pendientes de pago; para saber cuáles están vencidas hacen falta sus fechas.")
    r.table(['Etapa del presupuesto / al 15/09', 'Millones corrientes'],
        [[label,num(t[key],0)] for key,label in [('credito_presupuestado','Inicial'),('credito_vigente','Vigente'),('credito_comprometido','Comprometido'),('credito_devengado','Devengado'),('credito_pagado','Pagado')]], [WIDTH-140,140], compact=True)
    c = next(x for x in g['execution']['comparison'] if x['etapa']=='credito_devengado')
    r.note(f"El gasto devengado de enero-agosto fue {num(abs(c['variacion_real_pct']))}% menor en términos reales que un año antes. Se descuenta la inflación mes a mes. Caja del SPN y ejecución de la Administración Nacional tienen distinto alcance y registro; no se suman.")
    link('resultado_fiscal_comparacion','Hacienda: informe de ingresos y gastos')

    r.section('12 / Deuda nacional', 'El stock y los vencimientos responden preguntas distintas', 'Finanzas: deuda de Administración Central a agosto 2026. Vencimientos: stock al 31/03/2026.')
    d = g['debt']['monthly'][-1]
    fx = ratio(d['stock_moneda_extranjera'],d['stock_situacion_normal'])
    cer = ratio(d['stock_ajustable_cer'],d['stock_moneda_local'])
    r.add(f"La deuda bruta alcanzó <b>USD {num(d['stock_bruto'],0)} millones equivalentes</b> en agosto. Incluye títulos en pesos convertidos a dólares por la fuente. El {num(fx)}% de la deuda en situación de pago normal está en moneda extranjera. Dentro de la deuda en pesos, el {num(cer)}% ajusta por CER, un índice ligado a la inflación.")
    r.add(f"En agosto se pagaron USD {num(d['capital_pagado'],0)} millones de capital y USD {num(d['intereses_pagados'],0)} millones de intereses. El stock aumentó USD {num(d['variacion_stock'],0)} millones: hubo USD {num(d['transacciones_netas'],0)} millones de transacciones netas, USD {num(d['ajustes_valuacion'],0)} millones por valuación y USD {num(d['ajustes_elegible'],0)} millones de ajustes de deuda elegible, USD {num(d['ajustes_avales'],1)} millones por avales y USD {num(d['consolidacion_deudas'],1)} millones por consolidación. Un cambio del stock no equivale automáticamente a deuda nueva.")
    r.add('Calendario publicado con stock a marzo', 'heading')
    r.note('USD millones equivalentes. El calendario usa la deuda y los tipos de cambio al 31/03/2026. No incorpora las operaciones posteriores. El renglón 2026 sólo comprende abril-diciembre.')
    r.table(['Período','Capital','Intereses','Total'],
        [[('2026 / abr-dic' if x['periodo']=='2026' else '2036-2089 / 54 años' if x['agrupa_varios_anios'] else x['periodo']), num(x['capital_usd_millones'],0),num(x['intereses_usd_millones'],0),num(x['total_usd_millones'],0)] for x in g['debt']['annual_schedule']], [WIDTH-255,85,85,85], compact=True)
    r.add('La prioridad es seguir el calendario junto con la moneda y la posibilidad de refinanciar. El stock describe la escala de la deuda; el calendario muestra cuándo puede presionar sobre la caja. Para actualizar esa presión hacen falta las nuevas emisiones y los canjes posteriores a marzo.', 'small')
    link('deuda_stock_pagos','Finanzas: stock, pagos y movimientos mensuales')
    link('vencimientos_perfil_marzo2026','Finanzas: perfil de vencimientos')

    r.section('13 / Nación y provincias', 'Cuánto llega y cuánto permite financiar', 'DNAP: recursos de origen nacional, enero-agosto 2026. PA: transferencias al 15/09. INDEC: población proyectada 2026.')
    ba = next(x for x in g['provinces']['comparison'] if x['provincia_id']==6)
    r.add(f"Buenos Aires recibió {money(ba['ron_2026'])} de recursos de origen nacional en enero-agosto, en pesos corrientes. Después de descontar inflación, esos fondos compraron <b>{num(abs(ba['variacion_real_pct']))}% menos</b> que un año antes. La suba del monto nominal no alcanzó para preservar su poder de compra.")
    r.note('RON = coparticipación y otros recursos de origen nacional. RON y transferencias presupuestarias se muestran por separado. RON y transferencias: millones de pesos corrientes; por habitante: pesos. Orden: mayor variación real de RON.')
    rows = sorted(g['provinces']['comparison'],key=lambda x:-x['variacion_real_pct'])
    r.table(['Provincia','RON','Por habitante','Cambio real','Transfer. presupuesto'],
        [[x['provincia'],num(x['ron_2026'],0),num(x['pesos_por_habitante_2026'],0),pct(x['variacion_real_pct'],True),num(x['presupuestarias_devengado'],0)] for x in rows], [WIDTH-306,78,78,64,86], compact=True)
    r.note('Por habitante usa la proyección INDEC de 2026. Las transferencias del presupuesto son obligaciones reconocidas a administraciones provinciales al 15/09; no todo el gasto nacional localizado. No se califican como discrecionales sin revisar su norma.')
    link('ron_comparacion_provincias','DNAP: recursos nacionales distribuidos a provincias')

    r.section('14 / Prestaciones y obras', 'El gasto tiene que traducirse en servicios y obras', 'ONP / Presupuesto Abierto: metas, segundo trimestre 2026; obras, primer trimestre 2026. Unidades propias de cada medición.')
    coverage = next(x for x in g['physical']['coverage'] if x['trimestre']==2)
    r.add(f"El segundo trimestre reúne {num(coverage['mediciones'],0)} mediciones de prestaciones. En {num(coverage['mediciones_sin_ejecucion'],0)} falta ejecución acumulada informada. No corresponde convertir esos faltantes en cero ni sumar vacunas, personas y controles como si fueran una misma unidad.")
    metas = json.loads((ROOT/'nacion/data/gestion/metas_fisicas_trimestre_2.json').read_text(encoding='utf-8'))
    examples=[]
    for word in ['vacuna','jubilaciones','tratamiento']:
        item=next((x for x in metas if word in x['medicion_fisica_desc'].lower() and finite(x['ejecutado_acumulado_trim2']) and finite(x['programacion_acumulada_trim2']) and x not in examples),None)
        if item: examples.append(item)
    r.table(['Medición / unidad / forma de acumulación','Previsto','Realizado'],
        [[x['medicion_fisica_desc']+' / '+x['servicio_desc']+' / '+x['programa_desc']+' / '+x['unidad_medida_desc']+' / '+x['totalizador_avance_fisico'].split(':')[0],num(x['programacion_acumulada_trim2'],1),num(x['ejecutado_acumulado_trim2'],1)] for x in examples], [WIDTH-160,80,80], compact=True)
    r.note('Ejemplos del segundo trimestre: se compara programación acumulada con ejecución acumulada del mismo período. Una prestación por encima de lo previsto puede responder a más demanda; por sí sola no prueba una mejora de calidad.')
    r.add('Obras: gasto y avance físico', 'heading')
    works=json.loads((ROOT/'nacion/data/gestion/obras_ejecucion_fisica_financiera.json').read_text(encoding='utf-8'))
    r.add(f"El informe de inversión publica {len(works)} aperturas de obras. En {g['physical']['works_missing_physical']} no se informa avance físico del trimestre. Se muestran cinco aperturas con mayor gasto reconocido; el porcentaje físico mide avance durante el primer trimestre, no ejecución del presupuesto.", 'small')
    examples=sorted(works,key=lambda x:-(x['devengado_1t2026_millones'] or 0))[:5]
    r.table(['Obra','Gasto / $M','Avance físico'],[[x['obra'],num(x['devengado_1t2026_millones'],0),pct(x['ejecucion_fisica_1t2026_pct'])] for x in examples],[WIDTH-150,80,70],compact=True)
    r.note('Gasto en millones de pesos corrientes al 31/03/2026. Los indicadores financieros y físicos se leen juntos; no son intercambiables. El tablero permite buscar las 446 aperturas y las prestaciones de ambos trimestres.')
    link('metas_fisicas_trimestre_2','Programación y ejecución física: segundo trimestre')
    link('obras_ejecucion_fisica_financiera','ONP: obras e inversión pública, primer trimestre')

    r.section('15 / Historia desde 2007', 'Cómo cambiaron las autorizaciones y la ejecución', 'Presupuesto Abierto: totales de ejecución 2007-2025. INDEC: IPC promedio anual observado para el ajuste desde 2017.')
    r.add('La historia permite distinguir tres cosas: lo que se aprobó al inicio, lo que se autorizó después de las modificaciones y lo que efectivamente se reconoció como gasto. Acá se muestran ejercicios cerrados. Los ingresos cobrados y el gasto reconocido tienen distinto registro: su diferencia no se presenta como resultado de caja.')
    def value(x,key):
        if r.mode=='nominal':return x[key]
        return x[key]*x['factor_real_anual'] if finite(x['factor_real_anual']) else None
    r.table(['Año','Inicial','Vigente','Gasto reconocido','Ingresos cobrados'],[[str(x['ejercicio_presupuestario']),*[num(value(x,k),0) for k in ['credito_presupuestado','credito_vigente','credito_devengado','recurso_ingresado_percibido']]] for x in g['history']],[43,117,117,117,WIDTH-394],compact=True)
    r.note(f"Montos en millones · {r.units}. En constantes se usa IPC promedio anual observado; antes de 2017 falta un año completo de la serie de IPC utilizada y los montos quedan sin ajuste.")
    r.add('Qué corregimos en esta lectura', 'heading')
    r.add('La serie de totales presupuestarios concilia con la ejecución corriente del tablero. La serie alternativa asociada al PIB presenta diferencias y queda fuera de los cálculos. Por eso este informe no publica un porcentaje gasto/PIB con bases que todavía no son comparables.', 'small')
    link('historia_ejecucion_presupuestaria','Presupuesto Abierto: historia de presupuesto y ejecución')
    r.note('<link href="https://tablero.federicopellegrini.com.ar/nacion/#metodo" color="#254b73">Descargar los 28 conjuntos de gestión y sus fuentes en el tablero</link>')

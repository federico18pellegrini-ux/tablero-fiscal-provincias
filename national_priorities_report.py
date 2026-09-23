"""Two editorial pages for the general report, using the published priorities inputs."""
import json
from xml.sax.saxutils import escape


def spending_rows(budget, management):
    from scripts_export_national_reports import change, ratio
    actual = {(str(r['finalidad_id']), r['funcion_desc_2026']): r for r in management['execution']['functions_comparison']}
    rows = []
    for f in budget['functions']:
        r = actual[(f['purpose'], f['name'])]
        a, b = r['credito_devengado_real_agosto2026_2025'], r['credito_devengado_real_agosto2026_2026']
        rows.append(dict(id=f['id'], name=f['name'], before=a, after=b, change=change(b, a)))
    totals = [sum(r[k] for r in rows) for k in ('before', 'after')]
    for r in rows:
        r['share_before'], r['share_after'] = ratio(r['before'], totals[0]), ratio(r['after'], totals[1])
    return rows, totals


def append_priorities(r, management, decisions, benefits):
    from scripts_export_national_reports import WIDTH, num, pct, change, finite, SITE
    rows, (before, after) = spending_rows(r.d, management)
    by_id = {x['id']: x for x in rows}
    interest = by_id['5-29']
    rest_change = change(after-interest['after'], before-interest['before'])
    billions = lambda v: '$' + num(v / 1e6, 2) + ' billones'
    r.section('Lectura del gasto / 2026', 'Qué cambia detrás del gasto total', 'Presupuesto Abierto: devengado enero-agosto 2025/2026. IPC nacional observado, aplicado mes a mes.')
    r.note('Administración Nacional: administración central, organismos descentralizados y seguridad social. Gastos corrientes y de capital.')
    r.add('<b>Enero–agosto de cada año · pesos de agosto de 2026.</b> Esta comparación usa inflación observada, independientemente de la unidad elegida para el proyecto 2027.', 'small')
    r.add(f"El gasto reconocido pasa de <b>{billions(before)} a {billions(after)}</b>: {pct(change(after,before),True)} real. Dentro de ese total, los intereses y otros gastos de deuda crecen {pct(interest['change'],True)}. El resto del gasto cae {num(abs(rest_change))}% en términos reales.")
    r.add('Cuánto absorben los intereses', 'heading')
    r.table(['Intereses y otros gastos de deuda', 'Ene–ago 2025', 'Ene–ago 2026'], [
        ['Monto real', billions(interest['before']), billions(interest['after'])],
        ['Participación en el gasto', num(interest['share_before'],2)+'%', num(interest['share_after'],2)+'%']], [WIDTH-210,105,105])
    r.add(f"El aumento es de <b>{billions(interest['after']-interest['before'])}</b>. Su peso pasa de {num(interest['share_before'],2)} a {num(interest['share_after'],2)} de cada $100 del gasto. Este cuadro no incluye devolución de capital; las amortizaciones se muestran en el capítulo de financiamiento.", 'small')
    r.add('Menos recursos no siempre significa menor participación', 'heading')
    selected = [by_id[k] for k in ['3-15','3-13','3-16','3-14','2-12']]
    r.table(['Función', 'Cambio real', 'Peso 2025', 'Peso 2026'], [[x['name'],pct(x['change'],True),num(x['share_before'],2)+'%',num(x['share_after'],2)+'%'] for x in selected], [WIDTH-180,60,60,60])
    social = by_id['3-15']
    r.add(f"Seguridad Social cae {num(abs(social['change']))}% real, pero gana participación porque el total cae más. <b>Ganar peso dentro del presupuesto no significa recibir más recursos.</b> En Salud y Educación, la caída del gasto permite identificar una pérdida de recursos reales; para conocer las prestaciones hay que mirar también los registros de cada programa.")
    r.note(f'<link href="{SITE}#prioridades" color="#254b73">Ver las 29 funciones, las modificaciones de 2026 y la propuesta 2027 en el tablero</link>.')

    r.section('Ingresos y prestaciones / 2026', 'Del presupuesto a las personas', 'IMSS: prestaciones mensuales. INDEC: IPC observado. ONP: metas físicas acumuladas o promedio a junio 2026.')
    r.add('Cuánto compran la jubilación mínima y la AUH', 'heading')
    a = next(x for x in benefits['rows'] if x['period']=='2025-08')
    b = next(x for x in benefits['rows'] if x['period']=='2026-08')
    real = lambda k: change(b[k]/b['ipc'], a[k]/a['ipc'])
    r.note('Agosto de 2026 contra agosto de 2025. Importes mensuales en pesos corrientes; variación real ajustada por IPC observado.')
    labels = [('minimum','Mínima sin bono'),('minimum_bonus','Mínima con bono completo'),('bonus','Bono previsional'),('auh','AUH general por hijo')]
    r.table(['Prestación', 'Agosto 2025', 'Agosto 2026', 'Cambio real'], [[label,'$'+num(a[k],0),'$'+num(b[k],0),pct(0 if abs(real(k))<.05 else real(k),True)] for k,label in labels], [WIDTH-225,75,75,75])
    r.add(f"La mínima con bono perdió <b>{num(abs(real('minimum_bonus')))}% de poder de compra</b>. La mínima sin bono y la AUH prácticamente lo mantuvieron. El bono siguió en ${num(b['bonus'],0)} mientras los precios subieron: por eso perdió {num(abs(real('bonus')))}% de poder de compra y afectó el ingreso total de quienes lo cobran.")
    r.note('Mínima con bono completo para quien cumple el tope; sin aguinaldo. AUH al 100% del derecho mensual, no necesariamente lo depositado. Septiembre tiene monto nominal publicado, pero aún no IPC observado en esta serie.')
    r.add('Qué prestaciones se registraron', 'heading')
    specs = [('inmunizaciones',1110,'Dosis','Vacunas distribuidas','Dosis acumuladas'),('educacion-superior',4883,'Becario','Becarios Manuel Belgrano','Promedio de becarios'),('alimentacion',685,'Persona','Asistencia en espacios comunitarios','Promedio de personas')]
    physical = []
    for slug, identity, unit, label, method in specs:
        p = next(p for p in decisions['policies'] if p['slug']==slug)
        matches = [x for x in p['physical'] if x['medicion_fisica_id']==identity and x['unidad_medida_desc']==unit and x['ejercicio_presupuestario']==2026 and x['trimestre']==2]
        assert len(matches)==1 and not matches[0]['requiere_revision_clave']
        value=matches[0]['ejecutado_acumulado_trim2']
        physical.append([label,num(value,0) if finite(value) else 'Sin dato',method])
    r.table(['Programa / enero–junio 2026', 'Registro', 'Unidad y acumulación'],physical,[WIDTH-215,75,140])
    r.add('Son prestaciones de programas específicos, no toda la actividad de cada área ni resultados finales en salud, educación o bienestar. Las dosis distribuidas no equivalen a personas vacunadas. Los promedios no se suman como personas únicas. El gasto llega a agosto y estas prestaciones, a junio: no se calcula un costo por prestación mezclando ambos períodos.','small')
    r.note(f'<link href="{escape(b["source"])}" color="#254b73">IMSS: agosto 2026</link> · <link href="{SITE}#prioridades" color="#254b73">Series, fuentes y fichas de cada programa</link>.')

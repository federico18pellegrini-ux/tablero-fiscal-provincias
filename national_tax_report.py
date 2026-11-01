"""Dos páginas de debate fiscal, con los mismos datos y criterios que la web."""
from xml.sax.saxutils import escape
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.colors import HexColor

def composition_chart(years,width):
    chart=Drawing(width,88)
    blue,gold,ink=map(HexColor,['#3576a6','#b48a45','#0a192f'])
    chart.add(Rect(48,80,8,8,fillColor=blue,strokeColor=None))
    chart.add(String(61,80,'Normas de impuestos',fontName='Manrope',fontSize=8,fillColor=ink))
    chart.add(Rect(205,80,8,8,fillColor=gold,strokeColor=None))
    chart.add(String(218,80,'Regímenes de promoción',fontName='Manrope',fontSize=8,fillColor=ink))
    for i,row in enumerate(years):
        y=55-i*23;scale=(width-130)/4
        a,b=row['norms_pct']*scale,row['promotion_pct']*scale
        chart.add(String(0,y+5,str(row['year']),fontName='ManropeBold',fontSize=9,fillColor=ink))
        chart.add(Rect(48,y,a,19,fillColor=blue,strokeColor=None))
        chart.add(Rect(48+a,y,b,19,fillColor=gold,strokeColor=None))
        for value,x,color in [(row['norms_pct'],48+a/2,HexColor('#ffffff')),(row['promotion_pct'],48+a+b/2,ink)]:
            chart.add(String(x,y+6,f'{value:.2f}'.replace('.',','),fontName='ManropeBold',fontSize=8,fillColor=color,textAnchor='middle'))
        chart.add(String(width-3,y+5,f'{row["total_pct"]:.2f}%'.replace('.',','),fontName='ManropeBold',fontSize=10,fillColor=ink,textAnchor='end'))
    return chart

def append_tax(r,d):
    from scripts_export_national_reports import WIDTH, num
    c=d['comparison'];years=c['years'];a,b=years[0],years[-1]
    pp=lambda v:('+' if v>0 else '')+num(v,2)+' pp'
    links={s['file']:s['url'] for s in d['sources']}
    link=lambda file,label:f'<link href="{escape(links[file])}" color="#254b73">{label}</link>'
    r.section('Debate presupuestario / Gasto tributario','Beneficios con costo fiscal','ONP: Mensaje 2027, cuadro 1 (p. PDF 44). DNIyAF: informe 2024–2026. Mensaje y Separata 2024.',first=not r.story)
    r.add('Una dispensa deja recursos a sus beneficiarios. Su evaluación debe explicar cuánto cuesta, a quién alcanza y qué resultado produce. El control fiscal también debe mirar los ingresos resignados.','lead')
    r.add(f'<b>{num(b["total_pct"],2)}% del PIB en 2027 · ${num(b["total"]/1e6,2)} billones corrientes.</b> Frente al {num(a["total_pct"],2)}% estimado para 2025, el agregado baja {num(-c["total_delta_pp"],2)} puntos del PIB.')
    r.add('Qué cambia dentro del total','heading')
    r.note('Misma publicación: estimaciones 2025–2027 del Mensaje 2027. % del PIB mide la relación con el tamaño de la economía; pp indica puntos porcentuales.')
    r.story.append(composition_chart(years,WIDTH))
    r.add('El total disminuye, pero cambia su composición: las normas impositivas suben 0,03 puntos del PIB y los regímenes de promoción bajan 0,08 puntos. El agregado solo no permite identificar a los beneficiarios.')
    r.add('Impuestos y regímenes: qué cambia','heading')
    selected=[dict(x,name=x['name']+' · normas') for x in c['norms_by_tax'] if x['name'] not in ['Internos','Bienes personales']]+[dict(x,name=x['name']+' · promoción') for x in c['promotion_selection']]
    r.table(['Selección de beneficios / % PIB','2025','2027','Cambio'],[[x['name'],num(x['before'],2),num(x['after'],2),pp(x['delta_pp'])] for x in selected],[WIDTH-180,50,50,80])
    r.note('Normas: excluye regímenes. Promoción: beneficios seleccionados del cuadro 3. No es una apertura exhaustiva; porcentajes oficiales redondeados.')
    r.add('Por qué 2024 requiere otra lectura','heading')
    r.add('El proyecto original estimó 2,34% del PIB para 2024. El informe posterior 2024–2026 lo revisó a 3,45%, con Monotributo por 1,13% del PIB. Comparar directamente aquel 2,34% con 2027 mezcla publicaciones y cobertura. No demuestra nuevas dispensas por 1,33 puntos del PIB.','small')
    r.add('La Separata 2024 propuso revisar un subtotal de 1,47% del PIB, ya incluido en el gasto tributario. Su valor en 2027 exige revisar cada beneficio; mantener aquel porcentaje fijo sería un supuesto.','small')
    r.note(link('mensaje2027.pdf','Mensaje 2027')+' · '+link('gastos-2024-2026.pdf','Estimación revisada de 2024')+' · '+link('mensaje2024.pdf','Mensaje y Separata 2024'))

    r.section('Debate presupuestario / RIGI','Inversión y costo fiscal: qué falta medir','Economía: planes sectoriales RIGI, consultados 01/11/2026. ONP: Mensaje 2027, sección 4.2 (p. PDF 42).')
    r.add('El Gobierno publica compromisos de inversión, pero todavía no cuantifica el gasto tributario del RIGI en el Mensaje 2027. La evaluación necesita comparar los beneficios por impuesto y año con inversión efectivamente realizada, empleo y exportaciones.','lead')
    plans=d['rigi']['plans']
    r.add('Qué inversiones están programadas','heading')
    r.note('Millones de USD. Suma de los seis sectores del portal oficial, incluida Tecnología. Son planes, no ejecución observada; los subsectores pueden tener diferencias de redondeo.')
    r.table(['Sector','2026','2027'],[[x['name'],num(x['usd_millions'],0),num(plans[1]['sectors'][i]['usd_millions'],0)] for i,x in enumerate(plans[0]['sectors'])]+[['Total sectorial',*[num(x['total_usd_millions'],0) for x in plans]]],[WIDTH-160,80,80])
    r.add('Qué hace falta para calcular el beneficio','heading')
    r.table(['Impuesto','Información necesaria'],[[x['tax'],x['need']] for x in d['rigi']['measurement']],[115,WIDTH-115])
    r.add('Aplicar 5% o 50% al monto invertido no mide el costo fiscal. Hay que comparar cuánto tributarían las mismas operaciones bajo el régimen general y bajo el RIGI, distinguiendo reducción definitiva, diferimiento y momento del pago.')
    r.add('Qué pedir durante el debate','heading')
    r.add('Recomendamos publicar el costo anual por impuesto y proyecto, el calendario de inversión y los resultados comprometidos y alcanzados. Para cada beneficio, explicitar objetivo, beneficiarios, plazo y mecanismo de revisión. Así puede evaluarse si el incentivo cumple su propósito y a qué costo.')
    r.note('El gasto tributario es una estimación de tratamientos diferenciales; eliminar un beneficio no recupera automáticamente todo su valor. Un costo fiscal aún no publicado tampoco equivale a cero.')
    r.note(link('rigi-2026-11-01.html','Planes de inversión RIGI')+' · '+link('mensaje2027.pdf','Mensaje 2027: costo pendiente de estimación')+' · <link href="https://tablero.federicopellegrini.com.ar/nacion/#gasto-tributario" color="#254b73">Datos y análisis en el tablero</link>')

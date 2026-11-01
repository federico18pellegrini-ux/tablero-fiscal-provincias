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

    e=d['rigi']['estimate'];c=e['customs'];registry=e['registry'];middle=c['scenarios'][1]
    r.section('Debate presupuestario / RIGI','Cuánto podemos estimar','Economía: planes y registro oficial. ARCA: 27 resoluciones y beneficios RIGI. Corte de consulta: 01/11/2026.')
    r.add('El costo fiscal total sigue sin cuantificación oficial. Con los datos públicos podemos simular una parte: los derechos de importación que se dejarían de cobrar bajo supuestos explícitos.','lead')
    r.add(f'<b>{registry["project_count"]} proyectos aprobados · USD {num(registry["investment_usd_millions"],0)} millones comprometidos.</b> Se cuenta cada proyecto una vez, aunque abarque varias provincias. Son planes completos, no desembolsos. El calendario sectorial prevé USD {num(c["investment_2027_usd_millions"],0)} millones para 2027.')
    r.add('Tres hipótesis para derechos de importación','heading')
    r.note('Costo en millones de USD de 2027. Los porcentajes son supuestos de sensibilidad, no observaciones. No forman un intervalo estadístico ni una previsión central.')
    r.table(['Escenario','Importado','Pagaría sin RIGI','Arancel medio','Costo USD M'],[[x['name'],num(x['import_share']*100,0)+'%',num(x['incremental_share']*100,0)+'%',num(x['tariff']*100,0)+'%',num(x['cost_usd_millions'])] for x in c['scenarios']],[55,70,130,90,WIDTH-345])
    r.add(f'En B, se supone que se importa 35% del plan, que la mitad de esas compras pagaría arancel sin RIGI y que la tasa media sería 7%. El resultado es <b>USD {num(middle["cost_usd_millions"])} millones de renuncia aduanera</b>. Es un componente parcial condicionado a esos supuestos; no el costo total del régimen.')
    r.note('Fórmula: plan anual × parte importada × parte que pagaría sin RIGI × arancel medio. Se descuentan compras con arancel cero y beneficios previos, como Ley 24.196. Se excluye tasa de estadística y el resto de los impuestos; no se suma automáticamente al 3,67% del PIB.')
    r.add('Qué puede calcularse por impuesto','heading')
    r.table(['Beneficio','Lectura para el debate'],[
        ['Ganancias','RIGI: 25%. Régimen general: escala 25/30/35%. El ahorro marginal llega a USD 10 por USD 100 adicionales en el tramo de 35%, con la misma base; no es 10% de la inversión ni de toda la utilidad.'],
        ['Amortización','Adelanta deducciones. Su efecto depende de activos, vida útil, utilidades y quebrantos; no es íntegramente una pérdida definitiva.'],
        ['IVA',f'Adelantar seis meses un crédito hipotético de USD 100 millones, con tasa anual de 8%, tiene valor financiero de USD {num(e["vat_example"]["financial_value_usd_millions"])} millones. No sumarlo a la renuncia aduanera.'],
        ['Exportaciones','Exención luego de dos o tres años desde la adhesión. Faltan exportaciones propias y derechos vigentes por producto para cuantificar.'],
        ['Dividendos','La baja de 7% a 3,5% exige siete años desde adhesión. Ninguno de los 27 proyectos cumple ese plazo en 2027; solo ese beneficio tiene costo cero para ese año.']],[100,WIDTH-100])
    r.add('Qué falta para cerrar la estimación','heading')
    r.add('Faltan compras por NCM y origen, beneficios previos, utilidades y quebrantos, créditos IVA, exportaciones y pagos bancarios/al exterior. Recomendamos publicar las bases y el costo anual por impuesto y proyecto.')
    r.note('<link href="https://www.arca.gob.ar/rigi/incentivos/default.asp" color="#254b73">ARCA: beneficios por impuesto</link> · <link href="https://biblioteca.afip.gob.ar/cuadroslegislativos/cuadroLegislativo.aspx?i=541" color="#254b73">ARCA: proyectos y resoluciones</link> · <link href="https://tablero.federicopellegrini.com.ar/nacion/#gasto-tributario" color="#254b73">Registro, fuentes y simulador</link>')

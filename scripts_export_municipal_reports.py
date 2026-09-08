"""Complete municipal PDF reports, built from the same data/model as the dashboard.

python scripts_export_municipal_reports.py [--municipality 06329] [--output PATH]
python scripts_export_municipal_reports.py --check
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, KeepTogether
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'municipios/reports'
SITE = 'https://tablero.federicopellegrini.com.ar/municipios/'
INPUTS = ['municipios/data/dashboard.json', 'municipios/data/geografia_original.geojson',
          'municipios/model.mjs', 'scripts_municipal_report_data.mjs', 'scripts_export_municipal_reports.py',
          'municipios/assets/manrope-400.ttf', 'municipios/assets/manrope-700.ttf']
INK = colors.HexColor('#203331'); TEAL = colors.HexColor('#14695c')
MUTED = colors.HexColor('#586963'); LINE = colors.HexColor('#d8e2dc')
PALE = colors.HexColor('#edf3ee'); RED = colors.HexColor('#b42318'); BLUE = colors.HexColor('#315e8c')
WIDTH, HEIGHT = A4
MARGIN = 42
CONTENT = WIDTH - 2 * MARGIN
MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

def finite(v):
    return isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)

def number(v, digits=1):
    if not finite(v): return 'Sin dato'
    # Avoid a negative zero after display rounding.
    if abs(v) < .5 * 10 ** -digits: v = 0
    return f'{v:,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')

def money(v, digits=1, millions=True):
    if not finite(v): return 'Sin dato'
    return ('-' if v < 0 else '') + '$' + number(abs(v) / (1e6 if millions else 1), digits)

def pct(v, digits=1):
    return number(v, digits) + '%' if finite(v) else 'Sin dato'

def ratio(a, b):
    return 100 * a / b if finite(a) and finite(b) and b > 0 else None

def date(s):
    return '/'.join(reversed(s.split('-'))) if s else 'Sin fecha'

def month(s):
    return f'{MONTHS[int(s[5:7])-1]} {s[:4]}'

def clean(s):
    return str(s).replace('\u2013', '-').replace('\u2014', '-').replace('\u2011', '-').replace('\u2212', '-')

def escaped(s):
    return escape(clean(s))

def red_negatives(text):
    # Only text nodes: do not alter dates, identifiers, links or markup attributes.
    pieces=re.split(r'(<[^>]+>)',text)
    return ''.join(piece if piece.startswith('<') else re.sub(r'(?<![\w/])-(?:\$)?\d[\d.,]*(?:%| pp)?',lambda match:'<font color="#b42318">'+match.group()+'</font>',piece) for piece in pieces)

def direction(v, positive='aumentó', negative='cayó'):
    return positive if finite(v) and v > 0 else negative if finite(v) and v < 0 else 'no cambió' if v == 0 else 'no tiene variación verificable'

def fingerprint():
    return {f: hashlib.sha256((ROOT/f).read_bytes() if f.endswith('.ttf') else (ROOT/f).read_text(encoding='utf-8').encode()).hexdigest() for f in INPUTS}

def load_models():
    result = subprocess.run(['node', str(ROOT/'scripts_municipal_report_data.mjs')], cwd=ROOT, check=True, stdout=subprocess.PIPE)
    return json.loads(result.stdout)

def register_fonts():
    for name, filename in [('Municipal', 'manrope-400.ttf'), ('MunicipalBold', 'manrope-700.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(ROOT/'municipios/assets'/filename)))
    pdfmetrics.registerFontFamily('Municipal', normal='Municipal', bold='MunicipalBold', italic='Municipal', boldItalic='MunicipalBold')

def styles():
    return {
      'body': ParagraphStyle('Body', fontName='Municipal', fontSize=10.1, leading=15.2, textColor=INK, spaceAfter=9),
      'small': ParagraphStyle('Small', fontName='Municipal', fontSize=8.3, leading=11.8, textColor=MUTED, spaceAfter=8),
      'h1': ParagraphStyle('Title', fontName='MunicipalBold', fontSize=25, leading=30, textColor=INK, spaceAfter=12, keepWithNext=True),
      'h2': ParagraphStyle('Section', fontName='MunicipalBold', fontSize=15.2, leading=20, textColor=TEAL, spaceBefore=10, spaceAfter=8, keepWithNext=True),
      'cell': ParagraphStyle('Cell', fontName='Municipal', fontSize=8.5, leading=11.4, textColor=INK),
      'head': ParagraphStyle('TableHead', fontName='MunicipalBold', fontSize=8.3, leading=11, textColor=colors.white),
      'kpi': ParagraphStyle('KPI', fontName='MunicipalBold', fontSize=21, leading=27, textColor=INK),
      'kpilabel': ParagraphStyle('KPILabel', fontName='Municipal', fontSize=9, leading=12.4, textColor=MUTED),
    }

class LineChart(Flowable):
    def __init__(self, dates, values, height=155):
        Flowable.__init__(self); self.width=CONTENT; self.height=height; self.dates=dates; self.values=values
    def draw(self):
        c=self.canv; left=46; bottom=22; top=self.height-20; right=self.width-16
        vals=[v for v in self.values if finite(v)]; maxv=max(vals, default=1)*1.12 or 1
        c.setFont('Municipal',8)
        for i in range(5):
            y=bottom+(top-bottom)*i/4; c.setStrokeColor(LINE); c.setLineWidth(.4); c.line(left,y,right,y)
            c.setFillColor(MUTED); c.drawRightString(left-7,y-3,number(maxv*i/4,0))
        x=lambda i:left+(right-left)*i/max(1,len(self.values)-1)
        y=lambda v:bottom+(top-bottom)*v/maxv
        c.setStrokeColor(TEAL); c.setLineWidth(2); path=None
        for i,v in enumerate(self.values):
            if not finite(v):
                if path is not None:c.drawPath(path)
                path=None;continue
            if path is None:path=c.beginPath();path.moveTo(x(i),y(v))
            else:path.lineTo(x(i),y(v))
        if path is not None:c.drawPath(path)
        for i in sorted(set([0, len(self.values)//3, 2*len(self.values)//3, len(self.values)-1])):
            c.setFillColor(MUTED); c.drawCentredString(x(i),5,month(self.dates[i]))
        if self.values and finite(self.values[-1]):
            v=self.values[-1];c.setFillColor(TEAL);c.circle(x(len(self.values)-1),y(v),3,stroke=0,fill=1)
            c.setFont('MunicipalBold',9);c.drawRightString(right,y(v)+9,number(v,0))

class TransferChart(Flowable):
    def __init__(self, rows):
        Flowable.__init__(self);self.rows=rows;self.width=CONTENT;self.height=163
    def draw(self):
        c=self.canv;left=44;bottom=24;top=137;right=self.width-10
        series=[[next((r[1]/1e6 for r in self.rows if r[0]==f'{year}-{i:02d}'),None) for i in range(1,8)] for year in [2025,2026]]
        cap=max([v for seq in series for v in seq if finite(v)],default=1)*1.1 or 1
        c.setFont('Municipal',8)
        for i in range(4):
            y=bottom+(top-bottom)*i/3;c.setStrokeColor(LINE);c.setLineWidth(.4);c.line(left,y,right,y)
            c.setFillColor(MUTED);c.drawRightString(left-6,y-3,number(cap*i/3,0))
        step=(right-left)/7
        for i in range(7):
            x=left+i*step+step*.2
            for k,col in enumerate([colors.HexColor('#b8cec3'),TEAL]):
                v=series[k][i]
                if finite(v):c.setFillColor(col);c.rect(x+k*step*.29,bottom,step*.25,(top-bottom)*v/cap,stroke=0,fill=1)
            c.setFillColor(MUTED);c.drawCentredString(left+(i+.5)*step,7,MONTHS[i])
        for x,col,label in [(left,colors.HexColor('#b8cec3'),'2025'),(left+75,TEAL,'2026')]:
            c.setFillColor(col);c.rect(x,151,9,6,stroke=0,fill=1);c.setFillColor(MUTED);c.drawString(x+14,149,label)

class LocationMap(Flowable):
    def __init__(self, geography, municipality):
        Flowable.__init__(self);self.width=130;self.height=132;self.geography=geography;self.id=municipality
    def draw(self):
        c=self.canv
        def polygons(f):
            g=f['geometry'];return [g['coordinates']] if g['type']=='Polygon' else g['coordinates']
        pts=[p for f in self.geography['features'] for poly in polygons(f) for ring in poly for p in ring]
        project=lambda p:(p[0]*math.cos(math.radians(-37)),p[1])
        projected=[project(p) for p in pts];xs,ys=zip(*projected)
        scale=min((self.width-12)/(max(xs)-min(xs)),(self.height-12)/(max(ys)-min(ys)))
        xy=lambda p:((project(p)[0]-min(xs))*scale+6,(project(p)[1]-min(ys))*scale+6)
        selected=None
        for f in self.geography['features']:
            active=f['properties']['id']==self.id
            c.setFillColor(TEAL if active else PALE);c.setStrokeColor(LINE);c.setLineWidth(.2)
            for poly in polygons(f):
                path=c.beginPath()
                for ring in poly:
                    for i,p in enumerate(ring):
                        if i==0:path.moveTo(*xy(p))
                        else:path.lineTo(*xy(p))
                    path.close()
                c.drawPath(path,fill=1,stroke=1)
            if active:selected=f['properties']['centroide']
        if selected:
            x,y=xy([selected['lon'],selected['lat']]);c.setStrokeColor(TEAL);c.setLineWidth(1);c.circle(x,y,4,stroke=1,fill=0)

class Report:
    def __init__(self,path,m,data,geography):
        self.path=path;self.m=m;self.data=data;self.geography=geography;self.styles=styles();self.story=[];self.pages=0;self.layouts=[]
    def p(self,text,style='body'):
        self.story.append(Paragraph(red_negatives(clean(text)),self.styles[style]))
    def section(self,title,new=True):
        if new and self.story:self.story.append(PageBreak())
        self.p(title,'h1')
    def h(self,title):self.p(title,'h2')
    def table(self,head,rows,widths=None,small=False):
        def cell(v,header=False):
            s=escaped(v).replace('\n','<br/>');style=self.styles['head' if header else 'cell']
            if not header and re.match(r'^-\$?\d',str(v)):s=f'<font color="#b42318">{s}</font>'
            return Paragraph(s,style)
        grid=[[cell(v,True) for v in head]]+[[cell(v) for v in row] for row in rows]
        t=Table(grid,colWidths=widths or [CONTENT/len(head)]*len(head),repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
                              ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                              ('TOPPADDING',(0,0),(-1,-1),4 if small else 6),('BOTTOMPADDING',(0,0),(-1,-1),4 if small else 6),
                              ('LINEBELOW',(0,0),(-1,0),.6,TEAL)]))
        self.story.extend([t,Spacer(1,10)])
    def panel(self,title,text):
        t=Table([[Paragraph(escaped(title),self.styles['h2'])],[Paragraph(clean(text),self.styles['body'])]],colWidths=[CONTENT])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('LEFTPADDING',(0,0),(-1,-1),13),('RIGHTPADDING',(0,0),(-1,-1),13),('TOPPADDING',(0,0),(-1,0),4),('BOTTOMPADDING',(0,-1),(-1,-1),10)]))
        self.story.extend([t,Spacer(1,10)])
    def footer(self,c,doc):
        self.pages=doc.page;c.saveState();c.setStrokeColor(LINE);c.setLineWidth(.6);c.line(MARGIN,38,WIDTH-MARGIN,38)
        c.setFillColor(MUTED);c.setFont('Municipal',8);c.drawString(MARGIN,25,'Federico Pellegrini')
        c.drawRightString(WIDTH-MARGIN,25,f'Página {doc.page}')
        if doc.page>1:
            c.setFont('MunicipalBold',8);c.drawString(MARGIN,HEIGHT-24,self.m['municipio'])
            c.setFont('Municipal',8);c.drawRightString(WIDTH-MARGIN,HEIGHT-24,'Informe municipal completo')
        c.restoreState()
    def overview(self):
        m=self.m;f=max([x for x in [m.get('fiscal'),m.get('fiscalOther')] if x],key=lambda x:x['fin'],default=None)
        self.p('PROVINCIA DE BUENOS AIRES / INFORME MUNICIPAL','small');self.section(escaped(m['municipio']),False)
        self.p('Las cuentas, los recursos y el trabajo','h2')
        text=f"<b>{number(m['poblacion_2022'],0)} habitantes</b> según el Censo 2022. Superficie: {number(m['superficie_km2'],0)} km². Cada bloque conserva su propio período y su unidad monetaria.<br/><br/>Base del tablero actualizada el {date(self.data['generated'])}."
        t=Table([[Paragraph(text,self.styles['body']),LocationMap(self.geography,m['id'])]],colWidths=[CONTENT-150,150]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0)]));self.story.extend([t,Spacer(1,8)])
        r=m['variacion_transferencias_real_pct'];j=m['empleo_promedio_cambio_2024_2025_pct']
        kpis=[('Transferencias reales',pct(r),'Ene-jul 2026 vs. 2025'),('Empleo privado formal',pct(j),'Promedio 2025 vs. 2024'),('Resultado financiero',money(f['resultado_financiero'])+' M' if f else 'Sin dato',f"Cierre {date(f['fin'])}" if f else 'Sin cuenta fiscal comparable')]
        cells=[]
        for label,v,note in kpis:
            color='#b42318' if v.startswith('-') else '#203331'
            cells.append([Paragraph(escaped(label),self.styles['kpilabel']),Paragraph(f'<font color="{color}">{escaped(v)}</font>',self.styles['kpi']),Paragraph(escaped(note),self.styles['kpilabel'])])
        t=Table([cells],colWidths=[CONTENT/3]*3);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.5,LINE),('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));self.story.extend([t,Spacer(1,14)])
        self.h('La lectura central')
        self.p(f"Las transferencias provinciales {direction(r,'ganaron','perdieron')} {number(abs(r),1)}% de poder de compra en enero-julio de 2026 frente al mismo período de 2025. El empleo privado formal promedio {direction(j,'creció','se redujo')} {number(abs(j),1)}% en 2025 frente a 2024. Son ventanas distintas: conviene leerlas por separado antes de vincular sus movimientos.")
        if m['caen_empleo_y_transferencias_misma_ventana_2025_vs2024']:
            self.p(f"Al comparar el mismo año, 2025 frente a 2024, también aparecen menos recursos reales y menos empleo: las transferencias anuales bajaron {number(abs(m['transferencias_anual_2024_2025_real_pct']),1)}%. Esto combina presión sobre los recursos municipales con una menor cantidad de puestos privados registrados. No alcanza para cuantificar cuánto afectó a las tasas municipales.")
        if f:
            b=f['resultado_financiero'];self.p(f"La cuenta fiscal al {date(f['fin'])} muestra un {'déficit' if b<0 else 'superávit' if b>0 else 'equilibrio'} de {money(abs(b))} millones, equivalente al {pct(abs(f['resultado_sobre_ingresos_pct']),2)} de los ingresos. {'El faltante requiere identificar su financiamiento y las obligaciones pendientes.' if b<0 else 'Ese resultado necesita contrastarse con pagos pendientes, deudas y fondos con destino asignado antes de definir nuevas erogaciones.'}")
        else:self.p('Todavía no hay una cuenta fiscal homologada para determinar el resultado con el mismo criterio del ranking. Las transferencias y el empleo permiten describir parte de la situación, pero no reemplazan los ingresos y gastos completos.')
        self.panel('Tres prioridades para ordenar la gestión',
          '<b>Recursos:</b> seguir la recaudación propia y distinguir el efecto del reparto provincial.<br/>'
          '<b>Cuentas:</b> conciliar ejecución, pagos pendientes y fondos afectados antes de ampliar compromisos.<br/>'
          '<b>Actividad:</b> revisar los sectores que explican el empleo y definir medidas con objetivos verificables.')
        self.p('Contenido: cuentas municipales; transferencias; empleo; población, actividad y bancos; transparencia; los 27 indicadores de ranking; escenarios y anexos mensuales. El ranking informa la posición del municipio seleccionado, con su universo de comparación.','small')
    def accounts(self):
        m=self.m;accounts=[x for x in [m.get('fiscal'),m.get('fiscalOther')] if x]
        for i,f in enumerate(sorted(accounts,key=lambda x:x['fin'])):
            self.section('Las cuentas municipales' if not i else 'Cuentas de otro período')
            self.p(f"Del {date(f['inicio'])} al {date(f['fin'])}. Millones de pesos corrientes, sin ajuste por inflación. Ingresos cobrados y gastos devengados; se excluyen operaciones de financiamiento.")
            self.p(escaped(f.get('scope','Cuenta municipal publicada.')),'small')
            if f is m.get('fiscalOther'):self.p('Este corte se conserva en la ficha, pero no integra el ranking de enero-junio de 2026. No se compara directamente con períodos de distinta duración.','small')
            fields=[('Ingresos corrientes','ingresos_corrientes'),('Ingresos de capital','ingresos_capital'),('Ingresos totales','ingresos_totales'),('Gastos corrientes','gastos_corrientes'),('Gastos de capital','gastos_capital'),('Gastos totales','gastos_totales'),('Resultado financiero','resultado_financiero'),('Gasto en personal','personal_devengado'),('Ahorro corriente','ahorro_corriente')]
            self.table(['Concepto','Millones de pesos corrientes'],[(label,money(f.get(key),2)) for label,key in fields],[CONTENT*.62,CONTENT*.38])
            self.h('Qué explica el resultado')
            current=f['ingresos_corrientes']-f['gastos_corrientes'];capital=f['ingresos_capital']-f['gastos_capital'];balance=f['resultado_financiero']
            self.table(['Margen corriente','Saldo de capital','Resultado financiero'],[[money(current,2),money(capital,2),money(balance,2)]])
            self.p(f"Por cada $100 de ingresos, se registraron ${number(ratio(f['gastos_totales'],f['ingresos_totales']),1)} de gastos. "+(f"Los ingresos corrientes alcanzaron para cubrir el gasto corriente y dejaron {money(current)} millones antes de la cuenta de capital. " if current>=0 else f"El gasto corriente superó a los ingresos corrientes en {money(abs(current))} millones. El desequilibrio ya aparece en el funcionamiento corriente. ")+(f"La cuenta de capital absorbió {money(abs(capital))} millones de ese margen." if capital<0 and current>=0 else f"La cuenta de capital agregó un déficit de {money(abs(capital))} millones." if capital<0 else f"La cuenta de capital aportó un saldo positivo de {money(capital)} millones."))
            self.p('El resultado no informa por sí solo cuánto hay disponible en caja. Para evaluar nuevas decisiones hace falta revisar pagos pendientes, saldos anteriores, fondos afectados y vencimientos. Un semestre tampoco permite concluir que el resultado sea permanente.')
            self.table(['Indicador de este período','Valor'],[
              ('Resultado financiero / ingresos',pct(f.get('resultado_sobre_ingresos_pct'),2)),('Capital / gasto total',pct(f.get('capital_sobre_gasto_pct'),2)),
              ('Personal / gasto corriente',pct(f.get('personal_sobre_gasto_corriente_pct'),2)),('Ahorro corriente / ingresos corrientes',pct(f.get('ahorro_sobre_ingresos_corrientes_pct'),2)),
              ('Capital por habitante del Censo 2022',money(f.get('capital_por_habitante_base2022_ars_corrientes'),0,False))],[CONTENT*.68,CONTENT*.32],True)
        e=m.get('fiscalExecution')
        if e:
            self.section('Ejecución presupuestaria')
            self.p(f"Del {date(e['inicio'])} al {date(e['fin'])}. Millones de pesos corrientes. El presupuesto vigente es una autorización anual; los gastos y recursos corresponden al período informado.")
            fields=[('Presupuesto vigente','presupuesto_vigente'),('Recursos presupuestarios cobrados','recursos_presupuestarios_percibidos'),('Gastos devengados','gastos_presupuestarios_devengados'),('Gastos pagados','gastos_presupuestarios_pagados'),('Devengado del período sin pagar','devengado_no_pagado_del_periodo')]
            self.table(['Concepto','Millones de pesos corrientes'],[(label,money(e.get(key),2)) for label,key in fields],[CONTENT*.65,CONTENT*.35])
            self.panel('Qué significa para la gestión',f"De los gastos registrados, {money(e.get('devengado_no_pagado_del_periodo'))} millones permanecían sin pagar al cierre. Esto permite seguir obligaciones del período; no representa toda la deuda municipal ni demuestra que todos esos pagos estén vencidos.")
            self.p('Los totales presupuestarios incluyen operaciones financieras que deben separarse antes de calcular el resultado fiscal. Por ese motivo, estos datos no se usan como un déficit o superávit en el ranking.')
        if not accounts and not e:
            self.section('Las cuentas que faltan verificar')
            self.p(escaped(m.get('fiscalSearch',{}).get('message','Todavía no hay una cuenta completa verificada para este municipio.')))
            self.panel('Lo que todavía no podemos concluir','Las transferencias provinciales son sólo una parte de los ingresos. Con esa información no se puede calcular el déficit, el gasto de capital total ni la caja disponible. Los espacios sin información se mantienen como tales.')
            self.p('Para completar la cuenta hacen falta ingresos y gastos corrientes y de capital del mismo período, con identificación de los organismos incluidos. Para evaluar liquidez, además, se necesitan saldos, fondos afectados y obligaciones pendientes.')
        self.p(f"El ranking fiscal reúne {self.data['fiscalCoverage']['fiscal']} municipios con cierre a junio de 2026. Es una muestra parcial. Las funciones y los organismos incluidos pueden diferir entre municipios.",'small')
    def resources(self):
        m=self.m;self.section('Transferencias y reparto provincial')
        r=m['variacion_transferencias_real_pct'];diff=r-self.data['summary']['transfer_real_change_pct']
        self.p(f"En enero-julio de 2026 el municipio recibió {money(m['transferencias_2026_ene_jul_ars_jul26'])} millones a precios de julio. Su poder de compra {direction(r)} {number(abs(r),1)}% frente a los mismos meses de 2025. La variación quedó {number(abs(diff),1)} puntos porcentuales {'por encima' if diff>=0 else 'por debajo'} del conjunto bonaerense.")
        self.table(['Enero-julio','2025','2026'],[
            ('Transferencias totales, pesos corrientes (M)',money(m['transferencias_2025_ene_jul_ars']),money(m['transferencias_2026_ene_jul_ars'])),
            ('Transferencias totales, pesos de julio de 2026 (M)',money(m['transferencias_2025_ene_jul_ars_jul26']),money(m['transferencias_2026_ene_jul_ars_jul26'])),
            ('Coparticipación, pesos corrientes (M)',money(m['copart_2025_ene_jul_ars']),money(m['copart_2026_ene_jul_ars'])),
            ('Coparticipación, pesos de julio de 2026 (M)',money(m['copart_2025_ene_jul_ars_jul26']),money(m['copart_2026_ene_jul_ars_jul26'])),
            ('Participación observada en la coparticipación',pct(m['participacion_copart_2025_pct'],5),pct(m['participacion_copart_2026_pct'],5))],[CONTENT*.48,CONTENT*.26,CONTENT*.26],True)
        self.h('Cómo evolucionó mes a mes');self.story.append(TransferChart(m['transfers']))
        self.p('Transferencias totales. Millones de pesos de julio de 2026. Cada mes se ajusta por inflación antes de acumularlo. Los importes completos figuran en el anexo.','small')
        self.h('Qué explica el cambio de coparticipación')
        self.table(['Componente','Cambio real en millones'],[
            ('Cambio del total repartido, con la participación de 2025',money(m['efecto_masa_observada_ars_jul26'],2)),
            ('Cambio de participación, sobre el total repartido en 2026',money(m['efecto_participacion_observada_ars_jul26'],2)),
            ('Diferencia total, enero-julio 2026 menos 2025',money(m['copart_2026_ene_jul_ars_jul26']-m['copart_2025_ene_jul_ars_jul26'],2))],[CONTENT*.70,CONTENT*.30],True)
        self.p('La descomposición separa cuánto cambió la masa repartida y cuánto cambió la participación observada del municipio. Esa participación no reemplaza una tabla oficial de coeficientes CUD.','small')
        self.table(['Vínculo provincial: variación real enero-julio 2026 vs. 2025','Cambio'],[
            ('Recaudación propia de la provincia',pct(self.data['provincialRevenue']['total_provincial'])),('Ingresos Brutos provincial',pct(self.data['provincialRevenue']['ingresos_brutos'])),('Coparticipación al conjunto de municipios',pct(self.data['summary']['copart_real_change_pct']))],[CONTENT*.76,CONTENT*.24],True)
        self.p('La masa coparticipable combina impuestos provinciales y recursos federales. Una caída de un impuesto no se traslada automáticamente en el mismo porcentaje a todas las transferencias.','small')
    def employment(self):
        m=self.m;self.section('Trabajo, salarios y sectores')
        j=m['empleo_promedio_cambio_2024_2025_pct'];change=m['empleos_cambio_dic2023_dic2025']
        self.p(f"El empleo privado formal promedio {direction(j)} {number(abs(j),1)}% en 2025 frente a 2024. Entre diciembre de 2023 y diciembre de 2025, el saldo fue de {number(abs(change),0)} puestos {'menos' if change<0 else 'más' if change>0 else 'de diferencia'}. Promedios anuales y cierres de diciembre permiten dos lecturas distintas; no deben confundirse.")
        self.h('Historia completa del empleo registrado')
        self.story.append(LineChart([r[0] for r in m['employment']],[r[1] for r in m['employment']]))
        self.p('Puestos por lugar del establecimiento. Incluye trabajadores que pueden vivir en otro municipio. No mide desempleo, informalidad ni empleo público.','small')
        self.table(['Año','Empleo promedio','Puestos en diciembre','Salario real medio mensual'],[[str(y),number(m[f'empleo_promedio_{y}'],1),number(m[f'empleo_dic{y}'],0),money(m[f'salario_real_promedio_{y}_ars_jul26'],0,False)] for y in [2023,2024,2025]],[CONTENT*.10,CONTENT*.25,CONTENT*.25,CONTENT*.40],True)
        self.p('Remuneración media mensual en pesos de julio de 2026. Los aguinaldos y la composición del empleo también influyen en los promedios.','small')
        self.h('Dónde están los puestos privados formales')
        def sector_name(s):return {'Explotacion de minas y canteras':'Explotación de minas y canteras','Electircidad, gas y agua':'Electricidad, gas y agua','Construccion':'Construcción','Agricultura, ganaderia y pesca':'Agricultura, ganadería y pesca'}.get(s,s)
        self.table(['Sector, diciembre de 2025','Puestos','Sobre el total'],[[sector_name(s['name']),number(s['jobs'],0),pct(ratio(s['jobs'],m['empleo_dic2025']),1)] for s in m['sectors']],[CONTENT*.60,CONTENT*.20,CONTENT*.20],True)
        self.p('Los sectores reservados se dejan sin dato. Los sectores publicados pueden no sumar el total; no se completa el residual con una estimación.','small')
        salary=m['salario_real_promedio_cambio_2023_2025_pct'];mass=m['masa_salarial_formal_aprox_cambio_2023_2025_pct']
        self.p(f"El salario real promedio {direction(salary)} {number(abs(salary),1)}% entre 2023 y 2025. La masa salarial formal aproximada {direction(mass)} {number(abs(mass),1)}%. Esta última combina puestos y remuneraciones; no es una medición de ventas ni de consumo local. Para evaluar el impacto fiscal hace falta observar también la recaudación de las tasas.")
    def territory(self):
        m=self.m;self.section('Población, actividad y bancos')
        self.p('El tamaño, la estructura productiva y los servicios a cargo condicionan las comparaciones. Los datos por habitante usan una población censal fija: no son una proyección demográfica a 2026.')
        self.h('Población y condiciones estructurales')
        self.table(['Indicador','Valor'],[
            ('Población, Censo 2022',number(m['poblacion_2022'],0)),('Población, Censo 2010',number(m.get('poblacion_2010'),0)),('Cambio poblacional 2010-2022',pct(m.get('crecimiento_poblacion_2010_2022_pct'),2)),
            ('Superficie (km²)',number(m['superficie_km2'],1)),('Densidad 2022 (habitantes por km²)',number(m['densidad_2022'],1)),('Hogares, Censo 2022',number(m['hogares_2022'],0)),('Hogares con NBI',number(m['hogares_nbi_2022'],0)),('Hogares con NBI / hogares totales',pct(m['hogares_nbi_2022_pct'],2))],[CONTENT*.67,CONTENT*.33],True)
        self.p('Las necesidades básicas insatisfechas (NBI) describen carencias estructurales en 2022. No equivalen a pobreza monetaria actual. Chascomús y Lezama no tienen crecimiento intercensal comparable en esta base.','small')
        self.h('Actividad económica localizada')
        self.table(['Producto bruto municipal','Millones de pesos constantes de 2004'],[[str(y),money(m.get(f'pbg_constante_2004_{y}_ars'),2)] for y in [2021,2022,2023]],[CONTENT*.45,CONTENT*.55],True)
        self.p(f"El producto local varió {pct(m.get('pbg_real_cambio_2021_2023_pct'),2)} entre 2021 y 2023. Este es el último corte de actividad incorporado; no describe directamente la coyuntura de 2026.",'small')
        self.h('Crédito, depósitos y presencia financiera')
        self.table(['Indicador','2023','2024'],[
            ('Préstamos, millones de pesos corrientes',money(m.get('prestamos_2023_ars'),2),money(m.get('prestamos_2024_ars'),2)),('Depósitos, millones de pesos corrientes',money(m.get('depositos_2023_ars'),2),money(m.get('depositos_2024_ars'),2)),
            ('Sucursales','Sin dato',number(m.get('sucursales_2024'),0))],[CONTENT*.54,CONTENT*.23,CONTENT*.23],True)
        self.p(f"Cambio real de préstamos: {pct(m.get('prestamos_real_cambio_2023_2024_pct'),2)}. Cambio real de depósitos: {pct(m.get('depositos_real_cambio_2023_2024_pct'),2)}. Préstamos sobre depósitos en el cuarto trimestre de 2024: {pct(m.get('prestamos_sobre_depositos_2024_pct'),2)}.")
        self.p('Los saldos se asignan por localización financiera y se ajustan con IPC de cierre para medir su variación real. No identifican exclusivamente residentes o pymes ni permiten inferir fuga de ahorros. Los datos reservados permanecen sin valor.','small')
    def transparency(self):
        m=self.m;t=m['transparency'];self.section('Publicación de información fiscal')
        self.p(f"ASAP asignó {number(t['score'],0)} puntos sobre 100 en mayo de 2026, frente a {number(t['previousScore'],0)} en noviembre de 2025. El cambio fue de {number(t['change'],0)} puntos. El índice evalúa la información disponible en esas fechas, no el resultado de las cuentas ni la calidad general de la gestión.")
        self.table(['Componente','Nov. 2025','Mayo 2026','Máximo'],[[c['label'],number(c['history'][0],0),number(c['history'][1],0),str(c['max'])] for c in m['reportTransparency']]+[['Total',str(t['previousScore']),str(t['score']),'100']],[CONTENT*.52,CONTENT*.16,CONTENT*.16,CONTENT*.16])
        self.h('Cómo interpretar los componentes')
        for c in m['reportTransparency']:self.p(f"<b>{escaped(c['label'])}:</b> {escaped(c['status'])}")
        for h in t['history']:
            if h.get('note'):self.p(escaped(h['note']),'small')
        self.panel('Publicar y gestionar son dimensiones distintas','Un municipio puede publicar toda su información y registrar déficit. También puede haber incorporado documentos después del relevamiento. La baja de un puntaje puede reflejar que informes anteriores quedaron fuera del período admitido; no demuestra un deterioro financiero.')
        self.p('Relevamientos: al 8 de noviembre de 2025 y del 1 al 8 de mayo de 2026. Los componentes tienen pesos distintos y suman el total.','small')
    def rankings(self):
        m=self.m;self.section('Los 27 indicadores en comparación')
        self.p('La posición corresponde al municipio seleccionado. Cada indicador conserva el orden inicial del tablero, indicado en la tabla. El puesto 1 puede ser el menor o el mayor valor según ese orden; no significa automáticamente mejor gestión.')
        self.p(f"La comparación de población similar incluye municipios entre {number(m['poblacion_2022']/2,0)} y {number(m['poblacion_2022']*2,0)} habitantes del Censo 2022. Los empates comparten puesto. Los faltantes quedan fuera. El filtro aproxima tamaños; no iguala servicios ni estructura productiva.",'small')
        rows=[]
        for r in m['reportRankings']:
            v=r['value'];unit=r['unit']
            formatted=money(v,0,False) if unit=='money' else money(v,2)+' M' if unit=='millions' and finite(v) else pct(v,2) if unit=='%' else number(v,5)+' pp' if unit=='pp' and finite(v) else number(v,0)+' / 100' if unit=='score' and finite(v) else number(v,0)+' puntos' if unit=='points' and finite(v) else number(v,1 if unit in ['density','branches'] else 0)
            position=lambda n,c:f'{n} de {c}' if n is not None else f'Sin dato ({c} con dato)'
            label='Sucursales por 10.000 habitantes' if r['unit']=='branches' else r['label']
            rows.append([label+'\n'+r['period'],formatted,'Menor primero' if r['ascending'] else 'Mayor primero',position(r['rank'],r['count']),position(r['peerRank'],r['peerCount'])])
        self.table(['Indicador y período','Valor','Orden','Todos con dato','Población similar'],rows,[CONTENT*.39,CONTENT*.17,CONTENT*.14,CONTENT*.15,CONTENT*.15],True)
        self.p('Las cuentas fiscales del ranking corresponden al cierre de junio de 2026 y tienen cobertura parcial. Un municipio con otra fecha de ejecución puede tener su cuenta en este informe y quedar fuera de ese ranking.','small')
    def scenarios(self):
        m=self.m;self.section('Escenarios de coparticipación')
        s=m['reportScenarios'][20]
        self.p(f"Una caída hipotética del 10% de la masa coparticipable restaría {money(s['loss'])} millones al municipio, o {money(s['perCapita'],0,False)} por habitante censal. La base observada es la coparticipación bruta de enero-julio de 2026: {money(s['baseline'])} millones a precios de julio.")
        self.panel('Qué supone el ejercicio','Se mantiene la participación municipal y se dejan constantes los demás fondos. La caída se aplica sobre toda la masa elegible, no sobre un impuesto aislado. Es un escenario sobre un período observado, no un pronóstico del cierre anual ni una estimación del déficit.')
        self.p('Se incluyen todos los valores del control del tablero, de 0% a 20% en pasos de 0,5 puntos. El cambio negativo representa recursos que se perderían. La caída elegida puede localizarse en esta tabla.','small')
        self.table(['Caída supuesta','Cambio de recursos (M)','Coparticipación resultante (M)','Pérdida por habitante ($)'],[[pct(s['shock'],1),money(-s['loss'],2),money(s['after'],2),money(s['perCapita'],0,False)] for s in m['reportScenarios']],[CONTENT*.16,CONTENT*.29,CONTENT*.30,CONTENT*.25],True)
        self.p('Los importes están en pesos de julio de 2026. No se suman directamente a un resultado fiscal en pesos corrientes o de otro período. Para decidir cómo absorber un desvío hacen falta caja, vencimientos, ingresos propios y prioridades de gasto.','small')
    def annexes(self):
        m=self.m;self.section('Anexo / transferencias mensuales')
        self.p('Serie completa incorporada. Millones de pesos de julio de 2026. El total incluye la coparticipación; no corresponde sumar ambas columnas.')
        self.table(['Mes','Transferencias totales','Coparticipación bruta'],[[month(r[0]),money(r[1],2),money(r[2],2)] for r in m['transfers']],[CONTENT*.24,CONTENT*.38,CONTENT*.38],True)
        self.table(['Totales anuales comparables','Millones de pesos de julio de 2026'],[['2024',money(m['transferencias_anual_2024_ars_jul26'],2)],['2025',money(m['transferencias_anual_2025_ars_jul26'],2)],['Variación real 2025 / 2024',pct(m['transferencias_anual_2024_2025_real_pct'],2)]],[CONTENT*.53,CONTENT*.47],True)
        self.p('Los totales anuales cubren doce meses y se informan por separado del acumulado enero-julio. Los cocientes por habitante usan la población del Censo 2022.','small')
        self.p(f"En el conjunto provincial, {self.data['summary']['municipalities_falling_transfers']} de 135 municipios tuvieron menos transferencias reales en enero-julio de 2026 frente al mismo período de 2025. Al comparar el año 2025 con 2024, {self.data['summary']['same_window_2025_vs2024_both_falling']} municipios registraron una caída tanto del empleo formal promedio como de las transferencias reales anuales.",'small')
        self.section('Anexo / empleo y salarios mensuales')
        self.p('Toda la historia del tablero. Puestos privados registrados por establecimiento y remuneración media mensual en pesos de julio de 2026. Los saltos de junio y diciembre pueden reflejar aguinaldos y otros pagos estacionales.')
        self.table(['Mes','Puestos privados formales','Remuneración media real ($)'],[[month(r[0]),number(r[1],0),money(r[2],0,False)] for r in m['employment']],[CONTENT*.24,CONTENT*.36,CONTENT*.40],True)
        self.h('Masa salarial formal aproximada')
        self.table(['Año','Millones de pesos de julio de 2026'],[[str(y),money(m[f'masa_salarial_formal_aprox_{y}_ars_jul26'],2)] for y in [2023,2024,2025]],[CONTENT*.3,CONTENT*.7],True)
        self.p('Aproximación calculada como puestos por remuneración media de cada mes, luego acumulada en el año. No equivale a facturación, consumo ni ingreso disponible de los residentes.','small')
        self.h('Criterios para leer el informe')
        self.p('Los datos faltantes se informan como "Sin dato". Las cifras negativas conservan signo y color rojo. Los importes se redondean sólo para su presentación; pequeñas diferencias en sumas visibles pueden responder a ese redondeo. El documento reúne todas las vistas para el municipio seleccionado; no es una captura de la página ni cambia según la vista que estuviera abierta.','small')
        self.p(f'<link href="{SITE}?municipio={m["id"]}&amp;vista=panorama" color="#14695c">Abrir la ficha de {escaped(m["municipio"])}</link> · <link href="{SITE}metodologia.html" color="#14695c">Criterios y fechas de los datos</link>','small')
    def build(self):
        for method in [self.overview,self.accounts,self.resources,self.employment,self.territory,self.transparency,self.rankings,self.scenarios,self.annexes]:method()
        doc=SimpleDocTemplate(str(self.path),pagesize=A4,rightMargin=MARGIN,leftMargin=MARGIN,topMargin=45,bottomMargin=54,
                              title=f'{self.m["municipio"]} - Informe municipal completo',author='Federico Pellegrini',pageCompression=1)
        def deterministic_canvas(*args,**kwargs):kwargs['invariant']=1;return Canvas(*args,**kwargs)
        doc.build(self.story,onFirstPage=self.footer,onLaterPages=self.footer,canvasmaker=deterministic_canvas)
        return self.pages

def build(output=OUTPUT, municipality=None):
    register_fonts();data=load_models();geography=json.loads((ROOT/'municipios/data/geografia_original.geojson').read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=True);entries=[]
    chosen=[m for m in data['municipalities'] if municipality is None or m['id']==municipality]
    if not chosen:raise ValueError('Municipio no encontrado')
    for m in chosen:
        filename=f'informe-{m["id"]}.pdf';path=output/filename;pages=Report(path,m,data,geography).build()
        entries.append({'id':m['id'],'municipality':m['municipio'],'file':filename,'pages':pages,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'metrics':len(m['reportRankings']),'transferMonths':len(m['transfers']),'employmentMonths':len(m['employment']),'scenarios':len(m['reportScenarios'])})
    manifest={'version':1,'generated':data['generated'],'input_sha256':fingerprint(),'reports':entries}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'reports':len(entries),'pages':sorted({e['pages'] for e in entries}),'bytes':sum(e['bytes'] for e in entries)},ensure_ascii=False))
    return manifest

def check(output=OUTPUT):
    manifest=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    if manifest['input_sha256']!=fingerprint():raise ValueError('Los informes municipales deben regenerarse: cambiaron sus datos o su generador.')
    data=json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
    if len(manifest['reports'])!=len(data['municipalities']) or {r['id'] for r in manifest['reports']}!={m['id'] for m in data['municipalities']}:raise ValueError('Cobertura incompleta de informes municipales.')
    for r in manifest['reports']:
        if r['file']!=f'informe-{r["id"]}.pdf':raise ValueError('Nombre de informe incorrecto.')
        path=output/r['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('PDF alterado: '+r['file'])
        pdf=PdfReader(path)
        if len(pdf.pages)!=r['pages']:raise ValueError('Paginado incorrecto: '+r['file'])
    print(f'{len(manifest["reports"])} informes municipales vigentes y verificados.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--municipality');parser.add_argument('--output',type=Path,default=OUTPUT);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check:check(args.output)
    else:build(args.output,args.municipality)

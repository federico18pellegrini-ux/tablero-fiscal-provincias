"""Complete municipal PDF reports, built from the same data/model as the dashboard.

python scripts_export_municipal_reports.py [--municipality 06329] [--output PATH]
python scripts_export_municipal_reports.py --check
"""
import argparse
import csv
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
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, KeepTogether
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'municipios/reports'
SITE = 'https://tablero.federicopellegrini.com.ar/municipios/'
INPUTS = ['municipios/data/dashboard.json', 'municipios/data/geografia_original.geojson',
          'municipios/data/fuentes.csv', 'scripts_export_municipal_reports.py',
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
    return json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))


def source_link(url, label):
    return f'<link href="{escape(url, {chr(34): "&quot;"})}" color="#14695c">{escaped(label)}</link>'


def source_catalog():
    with (ROOT/'municipios/data/fuentes.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.reader(stream))
    def find(name):return next(r[1] for r in rows if r[0]==name)
    return {
        'population':source_link(find('poblacion-total-superficie.xlsx'),'INDEC / DPE, censos y población'),
        'nbi':source_link(find('nbi-catalog-1.xlsx'),'INDEC / DPE, NBI 2022'),
        'pbg':source_link(find('pbg-data.xlsx'),'DPE Buenos Aires, producto municipal 2021-2023'),
        'oede':source_link('https://www.argentina.gob.ar/sites/default/files/departamento_serie_empleo_remuneraciones_3.xlsx','OEDE / SIPA, empleo privado y remuneraciones 2019-2025'),
        'ipc':source_link('https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_08_26.xls','INDEC, IPC nacional, julio de 2026'),
        'transfers':source_link('https://www.gba.gob.ar/node/11822','Ministerio de Economía PBA, transferencias municipales 2025-2026'),
        'banks':'DPE / BCRA, 2023-2024: '+source_link(find('bancos-1.xlsx'),'préstamos')+', '+source_link(find('bancos-2.xlsx'),'depósitos')+' y '+source_link(find('bancos-0.xlsx'),'sucursales'),
        'credit':source_link('https://mapadeladeuda.ar/','CEC / FES, Mapa de la Deuda, sobre Central de Deudores del BCRA, julio de 2026'),
        'health':source_link('https://anuario2024.estadistica.ec.gba.gov.ar/wp-content/uploads/2026/04/SALUD-Y-SOC3.xlsx','INDEC / DPE, cobertura de salud, Censo 2022'),
        'crowding':source_link('https://anuario2024.estadistica.ec.gba.gov.ar/wp-content/uploads/2025/12/CARACT-HOG-12.xlsx','INDEC / DPE, personas por cuarto, Censo 2022'),
        'crime':source_link('https://cloud-snic.minseg.gob.ar/Bases/SNIC/snic-departamentos-anual.csv','Ministerio de Seguridad Nacional, SNIC 2024-2025'),
    }


class PageSources(Flowable):
    def __init__(self, text):
        super().__init__();self.text=text;self.width=0;self.height=0;self.keepWithNext=True
    def draw(self):self.canv.report_sources=self.text

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
        self.path=path;self.m=m;self.data=data;self.geography=geography;self.styles=styles();self.story=[];self.pages=0;self.layouts=[];self.sources=source_catalog()
    def p(self,text,style='body'):
        self.story.append(Paragraph(red_negatives(clean(text)),self.styles[style]))
    def section(self,title,new=True,sources=None):
        if new and self.story:self.story.append(PageBreak())
        if sources:self.story.append(PageSources('Fuentes: '+sources))
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
    def refs(self,*keys):return ' · '.join(self.sources[k] for k in keys)
    def fiscal_refs(self,f):
        def pages(d):
            values=d['consultedPages']
            return f'{min(values)}-{max(values)}' if len(values)>8 and values==list(range(min(values),max(values)+1)) else ', '.join(map(str,values))
        return f"Municipalidad de {escaped(self.m['municipio'])}, cuenta al {date(f['fin'])}: "+' · '.join(source_link(d['url'],f"documento {i}, págs. {pages(d)}") for i,d in enumerate(f['documents'],1))
    def footer(self,c,doc):
        self.pages=doc.page;c.saveState()
        sources=Paragraph(getattr(c,'report_sources',''),self.styles['small'])
        _,height=sources.wrap(CONTENT,65)
        if height>59.1:raise ValueError('Source footer too tall: '+self.m['id'])
        sources.drawOn(c,MARGIN,43)
        c.setStrokeColor(LINE);c.setLineWidth(.6);c.line(MARGIN,39,WIDTH-MARGIN,39)
        c.setFillColor(TEAL);c.setFont('Municipal',8)
        c.drawString(MARGIN,27,'tablero.federicopellegrini.com.ar/municipios/')
        c.linkURL(SITE+f'?municipio={self.m["id"]}&vista=panorama',(MARGIN,24,WIDTH-MARGIN,37),relative=0)
        c.setFillColor(MUTED);c.drawString(MARGIN,14,'Federico Pellegrini')
        c.drawRightString(WIDTH-MARGIN,14,f'Página {doc.page}')
        if doc.page>1:
            c.setFont('MunicipalBold',8);c.drawString(MARGIN,HEIGHT-24,self.m['municipio'])
            c.setFont('Municipal',8);c.drawRightString(WIDTH-MARGIN,HEIGHT-24,'Informe municipal')
        c.restoreState()
    def overview(self):
        m=self.m;f=max([x for x in [m.get('fiscal'),m.get('fiscalOther')] if x],key=lambda x:x['fin'],default=None)
        refs=self.refs('population','transfers','ipc','oede')+((' · '+self.fiscal_refs(f)) if f else '')
        self.section(escaped(m['municipio']),False,refs)
        self.p('INFORME MUNICIPAL / PROVINCIA DE BUENOS AIRES','small')
        self.p('Los recursos, el trabajo y la vida cotidiana','h2')
        self.p(f"{number(m['poblacion_2022'],0)} habitantes según el Censo 2022. Base del tablero actualizada el {date(self.data['generated'])}. Cada tema conserva su fecha: este informe reúne los últimos datos incorporados, aunque correspondan a años distintos.")
        r=m['variacion_transferencias_real_pct'];j=m['empleo_promedio_cambio_2024_2025_pct']
        kpis=[('Transferencias, sin el efecto de la inflación',pct(r),'Ene-jul 2026 vs. 2025'),('Puestos privados registrados',pct(j),'Promedio 2025 vs. 2024'),('Ingresos menos gastos',money(f['resultado_financiero'])+' M' if f else 'Sin dato',f"Cierre {date(f['fin'])}" if f else 'Cuenta fiscal sin verificar')]
        cells=[]
        for label,v,note in kpis:
            color='#b42318' if v.startswith('-') else '#203331'
            cells.append([Paragraph(escaped(label),self.styles['kpilabel']),Paragraph(f'<font color="{color}">{escaped(v)}</font>',self.styles['kpi']),Paragraph(escaped(note),self.styles['kpilabel'])])
        t=Table([cells],colWidths=[CONTENT/3]*3);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));self.story.extend([t,Spacer(1,14)])
        self.h('La lectura central')
        self.p(f"<b>Los recursos que llegan de la Provincia {direction(r,'ganaron','perdieron')} poder de compra.</b> En enero-julio de 2026 las transferencias {direction(r,'aumentaron','cayeron')} {number(abs(r),1)}% después de descontar la inflación, frente a los mismos meses de 2025. "+('Con esos fondos se puede comprar menos, aunque el monto en pesos haya aumentado. Esto presiona sobre el dinero para sostener servicios y obras.' if r<0 else 'La mejora permite comprar más que un año antes con esos fondos. Para saber si amplía el margen de gestión, hay que ver también cómo cambiaron los gastos.'))
        self.p(f"<b>El trabajo da otra señal.</b> El promedio de puestos privados registrados {direction(j)} {number(abs(j),1)}% en 2025 frente a 2024. "+('Menos puestos pueden debilitar los ingresos de las familias vinculadas a esas empresas y el movimiento comercial.' if j<0 else 'Más puestos pueden sostener los ingresos de las familias vinculadas a esas empresas y el movimiento comercial.')+' El dato cuenta empleos en establecimientos del municipio; no mide cuántos vecinos están desocupados. El corte es 2025 y no alcanza para describir el empleo de 2026.')
        if f:
            b=f['resultado_financiero'];spending=ratio(f['gastos_totales'],f['ingresos_totales'])
            self.p(f"<b>Las cuentas muestran un {'déficit' if b<0 else 'superávit' if b>0 else 'equilibrio'}.</b> Del {date(f['inicio'])} al {date(f['fin'])}, por cada $100 cobrados se registraron ${number(spending,1)} de gastos. La diferencia fue de {money(abs(b))} millones. "+('Los gastos superaron a los ingresos. Hace falta identificar cómo se cubrió esa diferencia y cuánto quedó pendiente de pago.' if b<0 else 'Los ingresos alcanzaron para cubrir los gastos registrados. Ese saldo no equivale automáticamente a dinero libre: puede haber pagos pendientes y fondos que ya tienen un destino asignado.'))
        else:self.p('<b>La cuenta fiscal todavía está incompleta.</b> No hay ingresos y gastos verificados con el mismo criterio para calcular el resultado. Las transferencias provinciales son sólo una parte de los recursos: con ellas solas no se puede afirmar que el municipio tiene déficit o superávit.')
        self.p('M significa millones de pesos. La cuenta fiscal usa los pesos de su período; transferencias y salarios se ajustan por inflación cuando así se indica.','small')
    def priorities(self):
        m=self.m;f=max([x for x in [m.get('fiscal'),m.get('fiscalOther')] if x],key=lambda x:x['fin'],default=None)
        self.section('Tres prioridades para la gestión',sources=self.refs('transfers','ipc','oede')+((' · '+self.fiscal_refs(f)) if f else ''))
        self.p('Las prioridades surgen de los recursos disponibles, el resultado de las cuentas y la evolución del trabajo. El objetivo es ordenar decisiones concretas con la información de este municipio.')
        r=m['variacion_transferencias_real_pct'];j=m['empleo_promedio_cambio_2024_2025_pct']
        self.h('1. Cuidar los recursos para sostener los servicios')
        self.p(f"<b>Por qué la elegimos.</b> Las transferencias perdieron {number(abs(r),1)}% de poder de compra en enero-julio de 2026. Cuando esos fondos alcanzan para menos, el municipio necesita revisar qué gastos puede sostener con ingresos habituales." if r<0 else f"<b>Por qué la elegimos.</b> Las transferencias ganaron {number(abs(r),1)}% de poder de compra en enero-julio de 2026. Antes de convertir esa mejora en nuevos gastos permanentes, conviene verificar si se mantiene y qué fondos tienen un destino específico.")
        self.p('<b>Qué recomendamos.</b> Comparar todos los meses lo que se esperaba cobrar con lo efectivamente cobrado, separando tasas propias y fondos provinciales. Actualizar el costo de los servicios esenciales. Así se detecta antes si hace falta reprogramar una compra o una obra, en vez de enterarse cuando llega el vencimiento.')
        self.h('2. Distinguir el resultado de la plata disponible')
        if f:
            b=f['resultado_financiero']
            self.p(f"<b>Por qué la elegimos.</b> El último cierre muestra un {'déficit' if b<0 else 'superávit'} de {money(abs(b))} millones. "+('Ese faltante exige saber si se usaron ahorros anteriores, se tomó deuda o quedaron gastos sin pagar.' if b<0 else 'Tener superávit no alcanza para saber cuánto puede gastarse. Hay que mirar el saldo bancario, los pagos pendientes y el destino de cada fondo. Los gastos ya registrados no se restan otra vez del resultado.'))
        else:self.p('<b>Por qué la elegimos.</b> Todavía falta una cuenta fiscal completa y verificada. Sin saber cuánto ingresó, cuánto se gastó y cuánto queda por pagar, no hay una base firme para asumir nuevos compromisos.')
        self.p('<b>Qué recomendamos.</b> Reunir el saldo bancario, los fondos con destino obligatorio, las facturas pendientes y los próximos vencimientos en una misma planilla. Esto permite separar el resultado contable del dinero que realmente se puede usar y ordenar los pagos por fecha y prioridad.')
        self.h('3. Entender qué está pasando con el trabajo')
        self.p(f"<b>Por qué la elegimos.</b> El empleo privado registrado promedio {direction(j)} {number(abs(j),1)}% en 2025. "+('La caída puede afectar a las familias y a los comercios que dependen de esos ingresos.' if j<0 else 'El crecimiento abre oportunidades, aunque puede concentrarse en pocos sectores o empresas.')+' El total por sí solo no permite identificar dónde está el problema o la oportunidad.')
        self.p('<b>Qué recomendamos.</b> Revisar los sectores con mayor peso y contrastar su evolución con habilitaciones, actividad comercial y cobranza de tasas. Priorizar formación laboral, trámites o infraestructura cuando se identifique una necesidad concreta. Luego medir si mejoran el empleo y la actividad; el dato agregado no alcanza para prometer ese resultado.')
    def accounts(self):
        m=self.m;accounts=[x for x in [m.get('fiscal'),m.get('fiscalOther')] if x]
        for i,f in enumerate(sorted(accounts,key=lambda x:x['fin'])):
            self.section('Las cuentas municipales' if not i else 'Cuentas de otro período',sources=self.fiscal_refs(f))
            self.p(f"Del {date(f['inicio'])} al {date(f['fin'])}. Millones de pesos corrientes, sin ajuste por inflación. Los ingresos son lo cobrado. Los gastos devengados son obligaciones registradas, aunque todavía no se hayan pagado. Se excluyen préstamos recibidos y otras operaciones de financiamiento.")
            self.p(escaped(f.get('scope','Cuenta municipal publicada.')).replace('Informe municipal publicado. No se presume consolidación de todos los organismos descentralizados.','Cuenta municipal publicada. El documento puede no incluir todos los hospitales y entes con cuentas separadas.'),'small')
            self.p('Corriente es lo que sostiene el funcionamiento habitual, como salarios y servicios. Capital incluye obras y equipamiento. El resultado financiero es ingresos totales menos gastos totales.','small')
            if f is m.get('fiscalOther'):self.p('Este corte se conserva en la ficha, pero no integra el ranking de enero-junio de 2026. No se compara directamente con períodos de distinta duración.','small')
            fields=[('Ingresos corrientes','ingresos_corrientes'),('Ingresos de capital','ingresos_capital'),('Ingresos totales','ingresos_totales'),('Gastos corrientes','gastos_corrientes'),('Gastos de capital','gastos_capital'),('Gastos totales','gastos_totales'),('Resultado financiero','resultado_financiero'),('Gasto en personal','personal_devengado'),('Ahorro corriente','ahorro_corriente')]
            self.table(['Concepto','Millones de pesos corrientes'],[(label,money(f.get(key),2)) for label,key in fields],[CONTENT*.62,CONTENT*.38])
            self.h('Qué explica el resultado')
            current=f['ingresos_corrientes']-f['gastos_corrientes'];capital=f['ingresos_capital']-f['gastos_capital'];balance=f['resultado_financiero']
            self.table(['Margen corriente','Saldo de capital','Resultado financiero'],[[money(current,2),money(capital,2),money(balance,2)]])
            self.p(f"Por cada $100 de ingresos, se registraron ${number(ratio(f['gastos_totales'],f['ingresos_totales']),1)} de gastos. "+(f"Los ingresos corrientes alcanzaron para cubrir el gasto corriente y dejaron {money(current)} millones antes de la cuenta de capital. " if current>=0 else f"El gasto corriente superó a los ingresos corrientes en {money(abs(current))} millones. El desequilibrio ya aparece en el funcionamiento corriente. ")+(f"La cuenta de capital absorbió {money(abs(capital))} millones de ese margen." if capital<0 and current>=0 else f"La cuenta de capital agregó un déficit de {money(abs(capital))} millones." if capital<0 else f"La cuenta de capital aportó un saldo positivo de {money(capital)} millones."))
            self.p('El resultado no informa por sí solo cuánto hay disponible en caja. Para evaluar nuevas decisiones hace falta revisar pagos pendientes, saldos anteriores, fondos afectados y vencimientos. Un solo período tampoco permite concluir que el resultado sea permanente.')
            self.p(f"El resultado representa {pct(f['resultado_sobre_ingresos_pct'],2)} de los ingresos. El gasto de capital equivale al {pct(f['capital_sobre_gasto_pct'],2)} del gasto total y a {money(f['capital_por_habitante_base2022_ars_corrientes'],0,False)} por habitante del Censo 2022. {('El gasto en personal representa '+pct(f['personal_sobre_gasto_corriente_pct'],2)+' del gasto corriente. ') if finite(f.get('personal_sobre_gasto_corriente_pct')) else 'Falta el desglose de personal para calcular su peso en el gasto corriente. '}El ahorro corriente equivale al {pct(f['ahorro_sobre_ingresos_corrientes_pct'],2)} de los ingresos corrientes.",'small')
        e=m.get('fiscalExecution')
        if e:
            self.section('Ejecución presupuestaria',sources=self.fiscal_refs(e))
            self.p(f"Del {date(e['inicio'])} al {date(e['fin'])}. Millones de pesos corrientes. El presupuesto vigente es una autorización anual; los gastos y recursos corresponden al período informado.")
            self.p('Gasto devengado es una obligación registrada, aunque siga sin pagarse. Gasto pagado es lo efectivamente cancelado. El presupuesto vigente indica cuánto está autorizado gastar en el año; no es dinero disponible en el banco.')
            fields=[('Presupuesto vigente','presupuesto_vigente'),('Recursos presupuestarios cobrados','recursos_presupuestarios_percibidos'),('Gastos devengados','gastos_presupuestarios_devengados'),('Gastos pagados','gastos_presupuestarios_pagados'),('Devengado del período sin pagar','devengado_no_pagado_del_periodo')]
            self.table(['Concepto','Millones de pesos corrientes'],[(label,money(e.get(key),2)) for label,key in fields],[CONTENT*.65,CONTENT*.35])
            self.panel('Qué significa para la gestión',f"De los gastos registrados, {money(e.get('devengado_no_pagado_del_periodo'))} millones permanecían sin pagar al cierre. Esto permite seguir obligaciones del período; no representa toda la deuda municipal ni demuestra que todos esos pagos estén vencidos.")
            self.p('Los totales presupuestarios incluyen operaciones financieras que deben separarse antes de calcular el resultado fiscal. Por ese motivo, estos datos no se usan como un déficit o superávit en el ranking.')
        if not accounts and not e:
            self.section('Las cuentas que faltan verificar',sources=source_link(SITE+'data/fiscal_verified.json','Registro de cuentas municipales verificadas y documentos disponibles'))
            self.p(escaped(m.get('fiscalSearch',{}).get('message','Todavía no hay una cuenta completa verificada para este municipio.')))
            self.panel('Lo que todavía no podemos concluir','Las transferencias provinciales son sólo una parte de los ingresos. Con esa información no se puede calcular el déficit, el gasto de capital total ni la caja disponible. Los espacios sin información se mantienen como tales.')
            self.p('Para completar la cuenta hacen falta ingresos y gastos corrientes y de capital del mismo período, con identificación de los organismos incluidos. Para evaluar liquidez, además, se necesitan saldos, fondos afectados y obligaciones pendientes.')
    def management(self):
        g=self.m.get('management')
        if not g:return
        b,t,d=g['budget'],g['treasury'],g['debt']
        def refs(documents):return 'Municipalidad de '+escaped(self.m['municipio'])+' · '+' · '.join(source_link(x['url'],'documento '+str(i)) for i,x in enumerate(documents,1))+' · '+source_link(SITE+'auditoria-distritos.html#'+self.m['id'],'criterios y conciliaciones')
        self.section('Presupuesto y pagos',sources=refs(b['documents']))
        self.p(f"Del {date(b['inicio'])} al {date(b['fin'])}. Millones de pesos corrientes. El presupuesto es la autorización anual para gastar. Devengado es un gasto registrado; pagado es lo efectivamente cancelado.")
        labels={'original':'Presupuesto original del año','modifications':'Modificaciones presupuestarias','current':'Presupuesto vigente del año','received':'Recursos cobrados en el período','accrued':'Gastos presupuestarios devengados','paid':'Gastos presupuestarios pagados','unpaid':'Devengado del período sin pagar'}
        self.table(['Concepto','Millones de pesos'],[(label,money(b[key],2)) for key,label in labels.items() if finite(b.get(key))],[CONTENT*.66,CONTENT*.34],True)
        self.p(escaped(b['reading']))
        self.h('En qué se registran los gastos')
        self.table(['Objeto del gasto','Vigente','Devengado','Pagado'],[(r['label'],money(r['current'],2),money(r['accrued'],2),money(r['paid'],2)) for r in b['objects']],[CONTENT*.37,CONTENT*.21,CONTENT*.21,CONTENT*.21],True)
        self.p('Bienes de uso incluye obras y equipamiento, pero no agota el gasto de capital: también hay insumos de obras y transferencias. Ejecutar presupuesto no demuestra que una obra esté terminada ni exige gastar la mitad del presupuesto a mitad de año.','small')
        self.section('Los ingresos y el resultado',sources=refs(b['documents']))
        self.h(b['receiptTitle'])
        self.table(['Concepto','Millones de pesos','Parte del total'],[(r['label'],money(r['received'],2),pct(ratio(r['received'],b['received']),1)) for r in b['receipts']],[CONTENT*.5,CONTENT*.3,CONTENT*.2])
        self.p('Origen municipal incluye tasas, derechos y otros recursos propios, incluso ventas de activos. No equivale solamente a impuestos ni asegura que los ingresos se repitan.' if b['receiptTitle'].startswith('Origen') else 'Un recurso sin afectación específica puede usarse para distintas finalidades. De todos modos, primero debe atender las obligaciones del municipio. Esa clasificación describe los ingresos cobrados; no identifica cuánto queda hoy en el banco para nuevas decisiones.')
        if b.get('reconciliation'):
            r=b['reconciliation'];self.h('Cómo se llega al gasto fiscal')
            self.table(['Paso de la conciliación','Millones de pesos'],[(label,money(value,2)) for label,value in [('Gasto presupuestario devengado',r['budgetAccrued']),('Menos devolución del capital de préstamos',-r['amortization']),('Menos cancelación de pasivos anteriores',-r['priorLiabilities']),('Gasto fiscal del período',r['fiscalExpenditure']),('Intereses, ya incluidos en el gasto fiscal',r['interestIncluded'])]],[CONTENT*.68,CONTENT*.32])
            self.p('Pagar una obligación de un año anterior consume dinero, pero no constituye un nuevo gasto fiscal de este semestre. La devolución del capital de un préstamo también se separa del gasto; sus intereses permanecen incluidos. Por eso no se calcula déficit restando sin más los totales presupuestarios.')
            self.p('La reconstrucción cruza objeto del gasto y programa para incluir los insumos de obras dentro del capital. Antes de aplicar el criterio a junio de 2026, conciliamos todos los componentes con la cuenta anual oficial de 2025.','small')
        else:
            self.p('Para leer el resultado se utiliza la Cuenta Ahorro Inversión Financiamiento publicada por el municipio. Esa cuenta separa las operaciones financieras del gasto corriente y de capital. El presupuesto y la tesorería aportan otra parte del análisis: autorizaciones, pagos y saldos.')
        self.section('Caja y obligaciones',sources=refs(t['documents']))
        self.p(f"Cierre al {date(t['date'])}. Millones de pesos corrientes. Cada saldo corresponde a esa fecha; no se combina con obligaciones de otro cierre.")
        labels={'closing':'Saldo total de tesorería','available':'Disponibilidades, incluidas en el total','transitory':'Movimientos transitorios, incluidos en el total','budgetCash':'Cuentas presupuestarias, incluidas en el total','unearmarkedAccounts':'De ellas: cuentas sin afectación','earmarkedAccounts':'De ellas: cuentas con destino asignado','thirdPartyAndSpecial':'Terceros y cuentas especiales','liabilities':'Pasivos contables totales','currentLiabilities':'De ellos: pasivos corrientes','nonCurrentLiabilities':'De ellos: pasivos no corrientes'}
        self.table(['Concepto','Millones de pesos'],[(label,money(t[key],2)) for key,label in labels.items() if finite(t.get(key))],[CONTENT*.67,CONTENT*.33],True)
        self.p(escaped(t['reading']))
        self.p('Los pasivos son obligaciones registradas. Corrientes son los de corto plazo; no corrientes, los de mayor plazo. Esa clasificación no identifica qué factura ya venció. Los subtotales están incluidos en los totales: no se suman otra vez. El resultado financiero tampoco se suma al saldo bancario para estimar dinero disponible.')
        self.h('Qué falta para completar la lectura')
        for item in g['pending']:self.p(escaped(item),'small')
        if d:
            self.section('La deuda del municipio',sources=refs(d['documents']))
            self.p(f"Cierre al {date(d['date'])}. Millones de pesos corrientes. Son obligaciones del municipio, distintas de las deudas de las personas.")
            self.table(['Tipo de obligación','Millones de pesos'],[(label,money(d[key],2)) for key,label in [('consolidated','Deuda consolidada'),('current','De ella: corriente'),('nonCurrent','De ella: no corriente'),('floating','Deuda flotante')]])
            self.p(escaped(d['reading']))
            self.h('Deuda flotante al cierre de cada año')
            self.table(['Año','Millones de pesos corrientes'],[(str(r['year']),money(r['floating'],2)) for r in d['floatingHistory']],small=True)
            self.p('Los importes no están ajustados por inflación. Un aumento nominal no mide por sí solo cuánto creció la carga real de la deuda. La publicación no contiene un calendario futuro de vencimientos.','small')
        bank=g['banking']
        if any(r['status']=='verified' for r in bank['records']):
            self.section('Crédito y depósitos: el último corte',sources='BCRA · '+ ' · '.join(source_link(x['url'],x['file']) for x in bank['documents'])+' · '+self.refs('ipc'))
            self.p(escaped(bank['note']))
            self.p('Millones de pesos. Los corrientes muestran el saldo de cada fecha. Los ajustados por inflación expresan todos los cierres a precios de julio de 2026.')
            self.table(['Fecha','Préstamos corrientes','Depósitos corrientes','Préstamos ajustados','Depósitos ajustados'],[(date(r['date']),money(r.get('loans'),1),money(r.get('deposits'),1),money(r.get('loansReal'),1),money(r.get('depositsReal'),1)) for r in bank['records']],[CONTENT*.18,CONTENT*.205,CONTENT*.205,CONTENT*.205,CONTENT*.205])
            self.h('Qué permite leer este dato')
            self.p('Los saldos describen el crédito y los depósitos registrados en las sucursales del distrito. Ayudan a seguir la actividad financiera local, pero no permiten atribuir todo el crédito a vecinos ni toda la financiación a pymes. Tampoco representan solamente deudas o depósitos del gobierno municipal.')
            self.p('El ajuste usa el IPC nacional del mes de cada cierre. Como son saldos en una fecha, no corresponde tratarlos igual que ingresos acumulados durante un semestre. Los préstamos y depósitos en moneda extranjera ya están convertidos por el BCRA; un cambio en el tipo de cambio también mueve su valor en pesos.')
            self.p('Las cifras de diciembre de 2023 y 2024 coinciden con los agregados DPE/BCRA que ya contenía el tablero. Se agregan diciembre de 2025 y junio de 2026. Los rankings bancarios generales mantienen el corte común de 2024 para evitar comparar municipios con fechas distintas.','small')
        history_refs=source_link(SITE+'auditoria-distritos.html#'+self.m['id'],'Municipalidad de '+self.m['municipio']+': documentos históricos y períodos exactos')
        portal='https://gobiernodelasheras.com/category/documentos/' if self.m['id']=='06329' else 'https://www.tigre.gob.ar/gobierno/informacion_gestion'
        history_refs+=' · '+source_link(portal,'Publicaciones oficiales')+' · '+source_link(SITE+'data/management_verified.json','registro de cifras y evidencia')
        self.section('Historia de las cuentas',sources=history_refs)
        self.p(escaped(g['historyReading']))
        for month,label in [(6,'Primer semestre de cada año'),(12,'Cierres de enero a diciembre')]:
            history=[f for f in g['history'] if int(f['fin'][5:7])==month and int(f['inicio'][5:7])==1]
            if not history:continue
            self.h(label)
            self.table(['Período exacto','Ingresos','Gastos','Resultado','% de ingresos'],[(date(f['inicio'])+' a '+date(f['fin']),money(f['ingresos_totales'],1),money(f['gastos_totales'],1),money(f['resultado_financiero'],1),pct(f['resultado_sobre_ingresos_pct'],2)) for f in history],[CONTENT*.29,CONTENT*.18,CONTENT*.18,CONTENT*.18,CONTENT*.17],True)
        self.p('Millones de pesos corrientes. Se conservan los días informados por cada publicación. '+('El cierre 2025 suma los dos semestres sin superponerlos; no se suman otra vez a ese cierre. ' if self.m['id']=='06329' else '')+'Un porcentaje de superávit o déficit no mide por sí solo la calidad de los servicios.','small')
        self.section('El detalle fiscal histórico',sources=history_refs)
        self.p('Millones de pesos corrientes. Cada fila es un período: no se suman los cortes que se superponen. El detalle también permite consultar por separado julio-diciembre cuando está publicado.')
        for category,fields in [('Ingresos y personal',[('ingresos_corrientes','Ingresos corrientes'),('ingresos_capital','Ingresos de capital'),('personal_devengado','Personal')]),('Gastos corrientes y de capital',[('gastos_corrientes','Gastos corrientes'),('gastos_capital','Gastos de capital')])]:
            self.h(category)
            self.table(['Período exacto']+[l for _,l in fields],[(date(f['inicio'])+' a '+date(f['fin']),*[money(f[k],1) for k,_ in fields]) for f in g['history']],small=True)
    def resources(self):
        m=self.m;self.section('Lo que llega de la Provincia',sources=self.refs('transfers','ipc'))
        r=m['variacion_transferencias_real_pct']
        self.p('<b>Transferencias</b> es el dinero que la Provincia gira al municipio. Incluye la <b>coparticipación</b>, el reparto de parte de los impuestos, y otros fondos. Por eso, no hay que sumar las dos filas: la coparticipación ya está dentro del total.')
        self.p('<b>Real significa ajustado por inflación.</b> Los pesos corrientes muestran el monto de cada momento. Los pesos de julio de 2026 llevan todos los meses al mismo nivel de precios: permiten comparar cuánto se puede comprar con ese dinero.')
        self.table(['Enero-julio de cada año','2025','2026'],[
            ('Transferencias totales, millones de pesos corrientes',money(m['transferencias_2025_ene_jul_ars']),money(m['transferencias_2026_ene_jul_ars'])),
            ('Transferencias totales, millones de pesos de julio de 2026',money(m['transferencias_2025_ene_jul_ars_jul26']),money(m['transferencias_2026_ene_jul_ars_jul26'])),
            ('Coparticipación, millones de pesos corrientes',money(m['copart_2025_ene_jul_ars']),money(m['copart_2026_ene_jul_ars'])),
            ('Coparticipación, millones de pesos de julio de 2026',money(m['copart_2025_ene_jul_ars_jul26']),money(m['copart_2026_ene_jul_ars_jul26']))],[CONTENT*.5,CONTENT*.25,CONTENT*.25],True)
        self.p(f"Después de descontar la inflación, el total {direction(r)} {number(abs(r),1)}%. En términos de poder de compra, cada $100 del período anterior equivalen a ${number(100+r,1)} en el período actual.")
        self.h('Las transferencias, mes a mes');self.story.append(TransferChart(m['transfers']))
        self.p('Millones de pesos de julio de 2026. Se ajusta cada mes con el IPC nacional antes de sumar el período. Así no se confunde un aumento de precios con una mejora de recursos.','small')
        self.h('Por qué cambió la coparticipación')
        self.table(['Explicación del cambio real, enero-julio','Millones de pesos de julio de 2026'],[
            ('Efecto del total repartido a todos los municipios',money(m['efecto_masa_observada_ars_jul26'],2)),
            ('Efecto del cambio en la porción recibida por el municipio',money(m['efecto_participacion_observada_ars_jul26'],2)),
            ('Cambio total de la coparticipación del municipio',money(m['copart_2026_ene_jul_ars_jul26']-m['copart_2025_ene_jul_ars_jul26'],2))],[CONTENT*.68,CONTENT*.32],True)
        self.p('El primer efecto mantiene la participación del año anterior; el segundo recoge su cambio sobre el reparto actual. Son participaciones observadas, no los coeficientes legales de reparto. La recaudación provincial influye, pero también hay recursos nacionales: la baja de un impuesto no se traslada automáticamente en igual porcentaje.','small')
    def employment(self):
        m=self.m;self.section('El trabajo y los sectores',sources=self.refs('oede')+' · '+source_link('https://www.argentina.gob.ar/sites/default/files/departamento_series_empleo_y_salarios_mensual_sector_1.csv','OEDE, empleo sectorial, diciembre de 2025'))
        j=m['empleo_promedio_cambio_2024_2025_pct'];change=m['empleos_cambio_dic2023_dic2025']
        self.p(f"El empleo privado registrado promedio {direction(j)} {number(abs(j),1)}% en 2025 frente a 2024. Entre diciembre de 2023 y diciembre de 2025 hubo {number(abs(change),0)} puestos {'menos' if change<0 else 'más' if change>0 else 'de diferencia'}.")
        self.p('<b>Qué se cuenta.</b> Puestos de trabajo declarados por empresas privadas ante la seguridad social, ubicados según el establecimiento. Un trabajador puede vivir en otro municipio. Quedan fuera el empleo público, el trabajo informal y los trabajadores independientes; esta serie no mide la desocupación local.')
        self.h('Cómo evolucionó el empleo registrado')
        self.story.append(LineChart([r[0] for r in m['employment']],[r[1] for r in m['employment']],145))
        self.table(['Año','Promedio mensual de puestos','Puestos en diciembre'],[[str(y),number(m[f'empleo_promedio_{y}'],1),number(m[f'empleo_dic{y}'],0)] for y in [2023,2024,2025]],[CONTENT*.15,CONTENT*.43,CONTENT*.42],True)
        self.p('El promedio resume los doce meses. Diciembre muestra el cierre del año. Pueden cambiar en distinta dirección si hubo contrataciones o bajas durante el año.','small')
        self.h('Dónde están los puestos, a diciembre de 2025')
        names={'Explotacion de minas y canteras':'Explotación de minas y canteras','Electircidad, gas y agua':'Electricidad, gas y agua','Construccion':'Construcción','Agricultura, ganaderia y pesca':'Agricultura, ganadería y pesca'}
        self.table(['Sector','Puestos','Parte del total'],[[names.get(s['name'],s['name']),number(s['jobs'],0),pct(ratio(s['jobs'],m['empleo_dic2025']),1)] for s in m['sectors']],[CONTENT*.60,CONTENT*.20,CONTENT*.20],True)
        self.p('Los sectores reservados se dejan sin dato para respetar la confidencialidad estadística. Las filas visibles pueden no sumar el total; no se estima el faltante.','small')
    def wages(self):
        m=self.m;w=m['community']['wage'];self.section('Cuánto significa el salario publicado',sources=self.refs('oede','ipc'))
        self.p(f"El promedio mensual de 2025 fue de <b>{money(w['annual']['2025']['nominal'],0,False)} brutos</b>, en los pesos de ese año. Al ajustar cada mes por inflación, equivale a <b>{money(w['annual']['2025']['real'],0,False)} a precios de julio de 2026</b>.")
        self.h('Qué incluye ese número')
        self.p('Es la remuneración bruta promedio que los empleadores privados declararon al Sistema Integrado Previsional Argentino (SIPA), a través de ARCA. Incluye conceptos remunerativos y no remunerativos, aguinaldo y pagos por vacaciones. <b>No es el salario de bolsillo:</b> no se descontaron aportes ni otras deducciones.')
        self.p('Tampoco es el sueldo de un vecino típico. Es un promedio de puestos localizados en el municipio: algunos trabajadores pueden vivir afuera, y los salarios altos o el peso de determinadas actividades pueden elevarlo. La base no publica aquí una mediana, que sería el valor que deja a la mitad de los salarios por debajo y a la mitad por encima.')
        self.table(['Promedio mensual del año','Bruto en pesos de cada año','Bruto ajustado a julio de 2026'],[[str(y),money(w['annual'][str(y)]['nominal'],0,False),money(w['annual'][str(y)]['real'],0,False)] for y in [2023,2024,2025]],[CONTENT*.28,CONTENT*.36,CONTENT*.36])
        self.h('Por qué diciembre puede parecer muy alto')
        self.table(['Mes de 2025','Bruto del mes, sin ajuste','Bruto a precios de julio de 2026'],[[label,money(w['months'][p]['nominal'],0,False),money(w['months'][p]['real'],0,False)] for p,label in [('2025-11','Noviembre'),('2025-12','Diciembre')]], [CONTENT*.28,CONTENT*.36,CONTENT*.36])
        self.p('Diciembre puede incluir el aguinaldo y otros pagos estacionales. Noviembre sirve como referencia de otro mes, pero tampoco equivale necesariamente al sueldo habitual ni al importe neto. No corresponde convertir el dato bruto en un sueldo de bolsillo con un descuento único: depende de cada trabajador.')
        self.h('Cómo se calcula el ajuste por inflación')
        self.p('Para cada mes se toma el salario publicado y se multiplica por el IPC de julio de 2026 dividido por el IPC de ese mes. El IPC es el índice de precios al consumidor del INDEC. Después se promedian los doce meses ya ajustados: así todos quedan expresados con el mismo poder de compra.')
        self.p(f"Con ese criterio, el salario promedio ajustado por inflación cambió {pct(m['salario_real_promedio_cambio_2023_2025_pct'],1)} entre 2023 y 2025. Esto describe al conjunto de puestos; no implica que cada trabajador haya tenido ese mismo cambio.")
        refs=', '.join(f"hoja {r['sheet']}, fila {r['row']}" for r in w['references'])
        self.p(f"Dato original: planilla OEDE, {refs}. Auditoría: los 84 meses por municipio y los promedios 2023-2025 coinciden con la planilla oficial y el IPC nacional. Sólo se redondea al mostrar los importes.",'small')
    def territory(self):
        m=self.m;self.section('La economía local y los bancos',sources=self.refs('pbg','banks','ipc','credit'))
        self.h('Producto bruto municipal: qué produce el territorio')
        self.p('El producto bruto municipal estima el valor de los bienes y servicios generados dentro del municipio, evitando contar dos veces los insumos. Describe el tamaño de la actividad económica. <b>No es la recaudación ni el presupuesto del gobierno municipal</b>, y tampoco mide cuánto gana cada vecino.')
        self.table(['Año','Producto municipal, millones de pesos constantes de 2004'],[[str(y),money(m.get(f'pbg_constante_2004_{y}_ars'),2)] for y in [2021,2022,2023]],[CONTENT*.18,CONTENT*.82])
        self.p(f"La Dirección Provincial de Estadística de Buenos Aires publica esta estimación. Al usar precios de 2004, el cambio refleja producción y no inflación. Entre 2021 y 2023 el producto varió {pct(m.get('pbg_real_cambio_2021_2023_pct'),2)}. El último año incorporado es 2023: este dato no describe por sí solo la actividad de 2026.")
        self.h('Préstamos, depósitos y sucursales')
        self.table(['Indicador','2023','2024'],[
            ('Préstamos, millones de pesos corrientes',money(m.get('prestamos_2023_ars'),2),money(m.get('prestamos_2024_ars'),2)),('Depósitos, millones de pesos corrientes',money(m.get('depositos_2023_ars'),2),money(m.get('depositos_2024_ars'),2)),
            ('Sucursales bancarias','Sin dato',number(m.get('sucursales_2024'),0))],[CONTENT*.54,CONTENT*.23,CONTENT*.23])
        if all(finite(m.get(k)) for k in ['prestamos_real_cambio_2023_2024_pct','depositos_real_cambio_2023_2024_pct','prestamos_sobre_depositos_2024_pct']):
            self.p(f"Al descontar la inflación entre los cierres de 2023 y 2024, los préstamos cambiaron {pct(m['prestamos_real_cambio_2023_2024_pct'],2)} y los depósitos, {pct(m['depositos_real_cambio_2023_2024_pct'],2)}. En el cuarto trimestre de 2024 había {number(m['prestamos_sobre_depositos_2024_pct'],2)} pesos prestados por cada $100 depositados.")
        else:self.p('Los saldos bancarios disponibles no permiten calcular una variación comparable ni la relación entre préstamos y depósitos para este municipio. Las celdas sin dato no significan que el monto sea cero.')
        self.p('Los saldos se asignan por la localización financiera informada y pueden incluir operaciones de empresas y personas de otros lugares. No permiten afirmar que los ahorros de los vecinos se prestan dentro o fuera del municipio. Los valores reservados quedan como «Sin dato».','small')
        self.p('Para mirar las deudas de las personas se utiliza el relevamiento territorial CEC/FES de la página siguiente, con una base y un período distintos de estos saldos bancarios.')
    def debt(self):
        d=self.m['community']['debt'];self.section('Deudas de las personas',sources=self.refs('credit'))
        self.p('RELEVAMIENTO EXTERNO / JULIO DE 2026','small')
        self.p(f"El Mapa de la Deuda del CEC/FES ubica <b>{number(d['peopleWithDebt'],0)} personas con deuda</b> en este municipio. De ellas, <b>{number(d['peopleInArrears'],0)} figuran en mora</b>: {pct(d['peopleInArrearsPct'],1)} del grupo con deuda informada.")
        self.p('<b>Tener deuda no significa estar atrasado.</b> Una persona puede usar una tarjeta o pagar un préstamo al día. Aquí se considera mora a las situaciones 3, 4 y 5 de la clasificación utilizada por el relevamiento, asociadas a atrasos de unos tres meses o más. Los atrasos más cortos quedan fuera de este indicador.')
        self.table(['Personas y montos del relevamiento','Julio de 2026'],[
            ('Personas con deuda informada',number(d['peopleWithDebt'],0)),('Personas en mora',number(d['peopleInArrears'],0)),
            ('Personas en mora / personas con deuda',pct(d['peopleInArrearsPct'],2)),
            ('Deuda total, millones de pesos corrientes',money(d['debtARS'],2)),('Deuda en mora, millones de pesos corrientes',money(d['debtInArrearsARS'],2)),
            ('Deuda en mora / deuda total',pct(d['debtInArrearsPct'],2)),('Deuda promedio por persona con deuda, pesos corrientes',money(d['averageDebtARS'],0,False))],[CONTENT*.7,CONTENT*.3])
        self.h('Dos porcentajes que responden preguntas distintas')
        self.p(f"<b>{pct(d['peopleInArrearsPct'],1)} de las personas con deuda está en mora.</b> Ese porcentaje cuenta personas, no pesos. <b>{pct(d['debtInArrearsPct'],1)} del monto adeudado está en mora.</b> Ese segundo porcentaje mide dinero. Pueden ser diferentes porque no todas las personas deben el mismo monto.")
        self.p('Ninguno de los dos porcentajes se calcula sobre toda la población municipal. Tampoco cuentan hogares: una misma familia puede tener varias personas con deuda. El promedio de deuda divide el monto total por las personas con deuda informada; no indica cuánto debe un vecino típico.')
        self.h('Qué aporta a la gestión')
        self.p('Los pagos atrasados permiten reconocer una presión sobre las finanzas de las personas alcanzadas por el relevamiento. Conviene contrastarla con empleo, ingresos y consultas de defensa del consumidor. Puede orientar información sobre crédito y atención de reclamos; no permite atribuir por sí sola la mora a una causa ni estimar cuánto caerá el consumo local.')
        self.p('<b>Alcance del dato.</b> Procesamiento y asignación territorial del CEC/FES a partir de la Central de Deudores del BCRA; no es una serie municipal publicada directamente por el Banco Central. Se incluyen todas las entidades, edades y géneros del relevamiento, que excluye sociedades de garantía recíproca y fondos públicos de garantía. La localización se toma del proveedor: no se verificaron domicilios individuales. No cubre toda la deuda informal ni demuestra que los préstamos hayan financiado solamente consumo.','small')
    def community(self):
        m=self.m;c=m['community'];h=c['health'];crime=c['crime'];self.section('La población y la vida cotidiana',sources=self.refs('population','nbi','health','crowding','crime'))
        self.table(['Población y hogares','Dato'],[
            ('Habitantes, Censo 2022',number(m['poblacion_2022'],0)),('Cambio de población entre 2010 y 2022',pct(m.get('crecimiento_poblacion_2010_2022_pct'),1)),
            ('Superficie / habitantes por km²',number(m['superficie_km2'],0)+' km² / '+number(m['densidad_2022'],1)),
            ('Hogares, Censo 2022',number(m['hogares_2022'],0)),('Hogares con necesidades básicas insatisfechas',number(m['hogares_nbi_2022'],0)+' / '+pct(m['hogares_nbi_2022_pct'],1)),
            ('Hogares con más de 3 personas por cuarto',pct(c['crowding']['over3PersonsPerRoomPct'],1)),
            ('Personas sin obra social, prepaga ni plan estatal de salud',number(h['withoutCoverage'],0)+' / '+pct(h['withoutCoveragePct'],1))],[CONTENT*.70,CONTENT*.30],True)
        self.p('<b>NBI significa necesidades básicas insatisfechas.</b> Identifica hogares con al menos una carencia: vivienda inadecuada, hacinamiento, falta de retrete, niños en edad escolar que no asisten o baja capacidad de subsistencia según el criterio censal. No es una medición actual de pobreza por ingresos.')
        self.p(f"La cobertura de salud se calcula sobre {number(h['populationPrivateDwellings'],0)} personas en viviendas particulares del Censo 2022. No tener obra social, prepaga o plan estatal <b>no significa quedar sin atención pública</b>. El dato ayuda a dimensionar la población que puede necesitar esa red. El hacinamiento identifica hogares donde conviven más de tres personas por cuarto; puede orientar la política habitacional.")
        self.h('Seguridad: qué dicen los registros')
        self.table(['Registro del SNIC','2024','2025','Tasa 2025 por 100.000 habitantes'],[
            ('Víctimas de homicidios dolosos',number(crime['2024']['homicideVictims'],0),number(crime['2025']['homicideVictims'],0),number(crime['2025']['homicideRate'],1)),
            ('Hechos de robo consumado',number(crime['2024']['robberies'],0),number(crime['2025']['robberies'],0),number(crime['2025']['robberyRate'],1)),
            ('Hechos de hurto consumado',number(crime['2024']['thefts'],0),number(crime['2025']['thefts'],0),number(crime['2025']['theftRate'],1))],[CONTENT*.44,CONTENT*.13,CONTENT*.13,CONTENT*.30],True)
        self.p('El Sistema Nacional de Información Criminal (SNIC) reúne hechos registrados por las fuerzas de seguridad. Robo implica fuerza o violencia; hurto, sustracción sin esos medios. Homicidio doloso refiere a una muerte intencional. Los robos incluyen los agravados y excluyen las tentativas.','small')
        a,b=crime['2024']['robberies'],crime['2025']['robberies']
        self.p(f"Se registraron {number(b,0)} robos en 2025, frente a {number(a,0)} en 2024. Conviene contrastar el cambio con zonas, horarios y canales de denuncia antes de definir medidas. Estos registros no captan todos los delitos ni miden la sensación de inseguridad. Más denuncias también pueden modificar el total.")
        self.p('Las tasas son las publicadas por el SNIC, con su población de referencia; no se recalculan con el Censo 2022. En municipios pequeños, pocos hechos pueden mover mucho la tasa. Se muestran junto a las cantidades para evitar lecturas engañosas.','small')
    def build(self):
        for method in [self.overview,self.priorities,self.accounts,self.management,self.resources,self.employment,self.wages,self.territory,self.debt,self.community]:method()
        doc=BaseDocTemplate(str(self.path),pagesize=A4,rightMargin=MARGIN,leftMargin=MARGIN,topMargin=45,bottomMargin=104,
                              title=f'{self.m["municipio"]} - Informe municipal completo',author='Federico Pellegrini',pageCompression=1)
        def deterministic_canvas(*args,**kwargs):kwargs['invariant']=1;return Canvas(*args,**kwargs)
        frame=Frame(MARGIN,104,CONTENT,HEIGHT-45-104,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        doc.addPageTemplates(PageTemplate(id='municipal',frames=frame,onPageEnd=self.footer))
        doc.build(self.story,canvasmaker=deterministic_canvas)
        return self.pages

def build(output=OUTPUT, municipality=None):
    register_fonts();data=load_models();geography=json.loads((ROOT/'municipios/data/geografia_original.geojson').read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=True);entries=[]
    chosen=[m for m in data['municipalities'] if municipality is None or m['id']==municipality]
    if not chosen:raise ValueError('Municipio no encontrado')
    for m in chosen:
        filename=f'informe-{m["id"]}.pdf';path=output/filename;pages=Report(path,m,data,geography).build()
        entries.append({'id':m['id'],'municipality':m['municipio'],'file':filename,'pages':pages,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'sections':['lectura','prioridades','cuentas']+(['presupuesto','caja','deuda-municipal','historia-fiscal'] if m.get('management') else [])+['transferencias','empleo','salarios','actividad','deudas','poblacion'],'populationYear':2022,'crimeYears':[2024,2025]})
    manifest={'version':2,'generated':data['generated'],'input_sha256':fingerprint(),'reports':entries}
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

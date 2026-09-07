"""Three-page, province-specific reports from the dashboard's verified datasets.

python scripts_export_management_reports.py [--output DIR] [--province NAME]
python scripts_export_management_reports.py --check
All calculations preserve period, coverage, missing values and price basis.
"""
import argparse, csv, hashlib, json, math, tempfile, unicodedata
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

ROOT=Path(__file__).resolve().parent
INPUTS=['data/annual_fiscal_accounts.json','data/budget_execution_2026.json',
 'data/fiscal_history.json','data/provincial_debt_services.json','data/debt_history.json',
 'data/government_results_provinces.json','informacion_consolidada_2026_normalizado.csv',
 'informacion_consolidada_2025_normalizado.csv','data/ipc_national_index.csv',
 'data/ron_2025_import.json','data/meta.json']
BUILD_INPUTS=INPUTS+['scripts_export_management_reports.py','assets/report-fonts/Lato-Regular.ttf','assets/report-fonts/Lato-Bold.ttf']
INK='#172E46';TEAL='#14796F';BLUE='#3679AA';MUTED='#536578';PALE='#EDF4F6';LINE='#D5E1E6';RUST='#A94F38';GOLD='#BB8B3A'
MM=72/25.4;W,H=A4
SITE='https://tablero.federicopellegrini.com.ar/'
MONTHS=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']

def number(v,d=1):
 if v is None or not math.isfinite(v):return 'Sin dato'
 return f'{v:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')
def pct(v,d=1):return number(v,d)+'%' if v is not None else 'Sin dato'
def ratio(n,d):return 100*n/d if n is not None and d is not None and d>0 else None
def slug(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c)).replace(' ','-')
def amount(v):
 if v is None:return 'Sin dato'
 return '$'+number(v/1e6,2)+' billones' if abs(v)>=1e6 else '$'+number(v/1e3,1)+' mil millones'
def per100(v):return '$'+number(abs(v),2)
def jsonfile(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def csvfile(name):return list(csv.DictReader((ROOT/name).read_text(encoding='utf-8').splitlines()))
def quarter_label(period):return f'{period[-1]}T{period[2:4]}'
def clean_text(text):return str(text).replace('\u2013','-').replace('\u2014','-').replace('\u2011','-')
def date_label(raw):
 if not raw:return 'sin fecha de valuación'
 return '/'.join(reversed(raw[:10].split('-')))

def editorial_reading(m):
 """Professional interpretation follows the observed balance, never the province name."""
 f=m['metrics']['financial'];p=m['metrics']['primary'];qf=m['qfinancial'];qp=m['qprimary']
 if f is None:
  opening='Sin ese cierre, no se puede afirmar cuánto margen hay para nuevas decisiones. Recomendamos reunir la ejecución, la caja y los pagos pendientes: son tres datos distintos y hacen falta los tres para ordenar una gestión.'
  mechanism=''
 elif f<0:
  opening='Ese faltante debe cubrirse con financiamiento, uso de caja o pagos que quedan pendientes. Cada alternativa condiciona las decisiones siguientes. Recomendamos corregir el desbalance con prioridades explícitas, para que el ajuste no recaiga por inercia sobre la inversión o los servicios.'
  mechanism=('Por eso, una refinanciación puede aliviar los vencimientos, pero por sí sola no corrige el desbalance antes de intereses. Hace falta revisar los compromisos recurrentes y la recaudación, identificando qué medidas sostienen los servicios y cuáles sólo trasladan el problema.' if p<0 else 'La prioridad es cuidar ese resultado antes de intereses y revisar el costo y el calendario de la deuda. Cubrir el rojo con nuevos compromisos, sin evaluar cómo se pagarán, puede agrandar la presión sobre los presupuestos siguientes.')
 elif f>0:
  opening='Ese saldo abre un margen para financiar prioridades o reducir obligaciones. Antes de comprometerlo en gastos permanentes, hay que comprobar qué parte se apoya en ingresos que se repetirán y qué pagos siguen pendientes. El superávit de un año necesita sostenerse en el tiempo.'
  mechanism='Recomendamos identificar qué explica el saldo antes de ampliar compromisos. Si depende de recursos extraordinarios o de una inversión postergada, el margen puede achicarse. Si se sostiene con ingresos recurrentes, permite planificar con mayor previsibilidad.'
 else:
  opening='El cierre no deja un excedente para absorber imprevistos. Una caída de ingresos o un gasto adicional puede llevarlo a déficit. Recomendamos ordenar los compromisos y construir una reserva de liquidez antes de sumar gastos permanentes.'
  mechanism='El equilibrio contable deja poco espacio para absorber un desvío. Recomendamos seguir la recaudación y los compromisos de pago durante el año, y definir qué medidas se activarían si los ingresos quedan por debajo de lo previsto.'
 if qf is None:
  quarter='Sin ese dato no podemos saber si la situación anual se sostiene. La prioridad es contar con una ejecución actualizada para decidir sobre salarios, proveedores e inversión con información del mismo período.'
 elif qf<0 and qp is not None and qp>=0:
  quarter='Los ingresos alcanzaron para el gasto sin intereses, pero el pago de intereses llevó el cierre a déficit. La gestión tiene que cuidar ese margen operativo y ordenar el financiamiento.'
 elif qf<0:
  quarter='Los recursos tampoco cubrieron el gasto antes de intereses. La prioridad es revisar ese desbalance y el orden de los pagos, junto con las condiciones de financiamiento.'
 elif qf>0:
  quarter='El saldo favorable permite programar prioridades, siempre que se contraste con la caja y los pagos pendientes. No conviene convertir un buen comienzo en nuevos compromisos permanentes sin mirar el resto del año.'
 else:
  quarter='El corte no deja un excedente. Conviene revisar cómo se distribuyen ingresos y pagos durante el resto del año antes de asumir compromisos nuevos.'
 if m['transfers']['real_pct'] is None:
  federal='Sin una comparación real completa, el aumento en pesos no alcanza para decir que hay más recursos disponibles para prestar servicios.'
 elif m['transfers']['real_pct']<0:
  federal='Eso significa que estos fondos compran menos que un año atrás. La caída le pone un límite al presupuesto y exige revisar las previsiones de recursos y pagos.'
 elif m['transfers']['real_pct']>0:
  federal='Estos fondos ganaron poder de compra. Ese alivio mejora el punto de partida, aunque por sí solo no permite concluir que todos los ingresos de la provincia crecieron al mismo ritmo.'
 else:
  federal='El poder de compra de estos fondos se mantuvo estable. Eso no garantiza que alcance para cubrir nuevas obligaciones ni que el resto de los ingresos haya seguido el mismo recorrido.'
 closing=('Corregir el déficit exige explicar qué se prioriza, cómo se financia y qué mejora concreta se espera. Recomendamos evaluar cada medida con esos tres criterios.' if f is not None and f<0 else 'El margen fiscal tiene que traducirse en servicios que funcionen y compromisos que se puedan sostener. Recomendamos evaluar cada decisión por su costo, financiamiento y resultado.' if f is not None else 'La información que falta le pone un límite al diagnóstico. Completarla permite discutir prioridades y asumir compromisos con costos y financiamiento verificables.')
 return dict(opening=opening,mechanism=mechanism,quarter=quarter,federal=federal,closing=closing)

class ReportData:
 def __init__(self):
  self.annual=jsonfile(INPUTS[0]);self.budget=jsonfile(INPUTS[1]);self.history=jsonfile(INPUTS[2]);self.services=jsonfile(INPUTS[3]);self.debt=jsonfile(INPUTS[4]);self.results=jsonfile(INPUTS[5])
  self.provinces=self.results['province_universe'];self.year=max(r['year'] for r in self.annual['rows']);self.quarter=max(r['period'] for r in self.budget['executions'])
  self.ipc={r['period']:float(r['ipc_index']) for r in csvfile('data/ipc_national_index.csv')}
  self.ron={}
  for file in INPUTS[6:8]:
   for r in csvfile(file):
    if r['period_type']!='month' or not r['value_millions']:continue
    k=(r['province'],r['period'],r['category_normalized'])
    if r['category_normalized'] in ['Total | (1) + (2)','CFI | Neta','Financiamiento Educativo','Compensación Consenso Fiscal']:
     if k in self.ron:raise ValueError(f'Duplicate RON aggregate: {k}')
     self.ron[k]=float(r['value_millions'])
  self.transfer_cut=max(k[1] for k in self.ron);self.reviewed=max(self.annual['reviewed_at'],self.budget['reviewed_at'],self.services['reviewed_at'])
 def annual_row(self,province,year):
  return next((r for r in self.annual['rows'] if r['province']==province and r['year']==year and r['status']=='observed'),None)
 def transfers(self,province,through=None,category='Total | (1) + (2)'):
  through=through or self.transfer_cut;year=int(through[:4]);end=int(through[-2:])
  now=[self.ron.get((province,f'{year}-{m:02}',category)) for m in range(1,end+1)]
  prev=[self.ron.get((province,f'{year-1}-{m:02}',category)) for m in range(1,end+1)]
  complete=all(v is not None for v in now)
  comparable=complete and all(v is not None for v in prev) and all(f'{y}-{m:02}' in self.ipc for y in [year,year-1] for m in range(1,end+1))
  real=nominal=None;current=sum(now) if complete else None
  if comparable and sum(prev)>0:
   # Deflate each monthly flow before adding. A common base cancels in the ratio.
   real_now=sum(v/self.ipc[f'{year}-{m:02}'] for m,v in enumerate(now,1))
   real_prev=sum(v/self.ipc[f'{year-1}-{m:02}'] for m,v in enumerate(prev,1))
   real=100*(real_now/real_prev-1) if real_prev>0 else None
   nominal=100*(sum(now)/sum(prev)-1)
  return dict(current=current,previous=sum(prev) if all(v is not None for v in prev) else None,real_pct=real,nominal_pct=nominal,through=through,complete=complete)
 def model(self,province):
  if province not in self.provinces:raise ValueError('Unknown province')
  annual=self.annual_row(province,self.year)
  # An older year is never silently substituted for an unavailable current year.
  history=[self.annual_row(province,y) for y in range(self.year-2,self.year+1)]
  q=next((r for r in self.budget['executions'] if r['province']==province and r['period']==self.quarter and r['income'] is not None),None)
  previous=self.quarter.replace(str(int(self.quarter[:4])),str(int(self.quarter[:4])-1),1)
  qp=next((r for r in self.budget['executions'] if r['province']==province and r['period']==previous and r['income'] is not None),None)
  metrics=dict(financial=ratio(annual['financial'],annual['income']),primary=ratio(annual['primary'],annual['income']),capital=ratio(annual['capital'],annual['spending'])) if annual else dict(financial=None,primary=None,capital=None)
  qfinancial=ratio(q['income']-q['spending'],q['income']) if q else None
  qprimary=ratio(q['income']-q['primary'],q['income']) if q else None
  qcapital=ratio(q['capital'],q['spending']) if q else None
  qpcapital=ratio(qp['capital'],qp['spending']) if qp else None
  comparisons=[r for r in self.annual['rows'] if r['year']==self.year and r['status']=='observed' and r['basis']=='devengado']
  benchmark=ratio(sum(r['capital'] for r in comparisons),sum(r['spending'] for r in comparisons))
  debt=next((r for r in self.debt['rows'] if r['province']==province and r['period']==self.quarter),None)
  pillars=self.results['provinces'][province]['pillars']
  return dict(province=province,annual=annual,history=history,quarter=q,previous_quarter=qp,qfinancial=qfinancial,qprimary=qprimary,qcapital=qcapital,qpcapital=qpcapital,
   metrics=metrics,benchmark=benchmark,benchmark_n=len(comparisons),debt=debt,projection=self.services['projections'].get(province),pillars=pillars,transfers=self.transfers(province))

class Report:
 def __init__(self,path,model,data):
  self.m=model;self.d=data;self.editorial=editorial_reading(model);self.page=0;self.layouts=[]
  self.c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1,invariant=1)
  self.c.setTitle(f'{model["province"]} | Informe de gestión | Frente Renovador')
  self.c.setAuthor('Federico Pellegrini');self.c.setSubject('Diagnóstico fiscal, inversión y agenda de gestión provincial. Documento de trabajo.');self.c.setCreator('Tablero de Federico Pellegrini')
 def text(self,text,x,y,size=10.5,bold=False,color=INK):
  self.c.setFont('LatoBold' if bold else 'Lato',size);self.c.setFillColor(HexColor(color));self.c.drawString(x*MM,H-y*MM,clean_text(text))
 def right(self,text,x,y,size=10,bold=False,color=INK):
  self.c.setFont('LatoBold' if bold else 'Lato',size);self.c.setFillColor(HexColor(color));self.c.drawRightString(x*MM,H-y*MM,str(text))
 def rect(self,x,y,w,h,fill=PALE,stroke=None,r=0):
  self.c.setFillColor(HexColor(fill));self.c.setStrokeColor(HexColor(stroke or fill))
  radius=max(0,min(r,w/2,h/2))
  self.c.roundRect(x*MM,H-(y+h)*MM,w*MM,h*MM,radius*MM,fill=1,stroke=bool(stroke))
 def line(self,x,y,w,color=LINE):
  self.c.setStrokeColor(HexColor(color));self.c.setLineWidth(.6);self.c.line(x*MM,H-y*MM,(x+w)*MM,H-y*MM)
 def paragraph(self,text,x,y,w=174,size=10.5,leading=14.7,color=INK,bold=False,max_end=275):
  style=ParagraphStyle('report',fontName='LatoBold' if bold else 'Lato',fontSize=size,leading=leading,textColor=HexColor(color),spaceAfter=0)
  p=Paragraph(clean_text(text),style);_,h=p.wrap(w*MM,1000)
  end=y+h/MM
  if end>max_end+.05:raise ValueError(f'Page {self.page} overflow {self.m["province"]}: {end:.1f}>{max_end}: {text[:80]}')
  p.drawOn(self.c,x*MM,H-y*MM-h);self.layouts.append(dict(page=self.page,start=y,end=end,text=text));return end
 def section(self,num,title,y):
  self.text(num,18,y,10,True,TEAL);self.text(title,28,y,14,True);return y+5
 def header(self,topic):
  if self.page:self.c.showPage()
  self.page+=1;self.rect(0,0,210,3,TEAL)
  self.text('FRENTE RENOVADOR  /  AGENDA PROVINCIAL',18,14,8.7,True,TEAL)
  self.right('DOCUMENTO DE TRABAJO',192,14,7.8,color=MUTED)
  name=self.m['province'];size=29 if len(name)<21 else 25
  self.text(name,18,29,size,True);self.text(topic,18,37,11,color=MUTED);self.line(18,42,174)
  self.line(18,282,174)
  self.text('Federico Pellegrini',18,289,9,True)
  self.right(f'{self.page} / 3',192,289,9,True)
 def kpi(self,x,y,w,label,value,detail,color=TEAL):
  self.rect(x,y,w,31,PALE,r=2);self.text(label,x+4,y+6,8.7,True,MUTED)
  self.text(value,x+4,y+17,21,True,color)
  self.paragraph(detail,x+4,y+21,w-8,8.4,10.5,color=MUTED,max_end=y+30)
 def note(self,text,y,max_end=279):return self.paragraph(text,18,y,174,8.2,10.5,MUTED,max_end=max_end)
 def link(self,label,url,x,y):
  self.text(label,x,y,8.1,False,BLUE);width=pdfmetrics.stringWidth(label,'Lato',8.1)
  self.c.linkURL(url,(x*MM,H-(y+1)*MM,x*MM+width,H-(y-3)*MM),relative=0,thickness=0)
 def bar(self,label,value,y,max_value=110,color=TEAL,value_label=None):
  self.text(label,18,y,9.4);self.rect(71,y-3.6,101,4.7,PALE,r=1)
  if value is not None:self.rect(71,y-3.6,101*min(abs(value)/max_value,1),4.7,color,r=1)
  self.right(value_label or (number(value,1) if value is not None else 'Sin dato'),192,y,9.6,True,color)

 def page_accounts(self):
  m=self.m;a=m['annual'];f=m['metrics']['financial'];p=m['metrics']['primary'];yyear=self.d.year
  self.header('01  Las cuentas y el margen de maniobra')
  if a:
   title='Los ingresos no alcanzan para cubrir el gasto' if f<0 else 'Hay superávit. Ahora hay que sostenerlo'
   if f==0:title='Las cuentas cierran sin margen de sobra'
   self.paragraph(title,18,49,174,18,22,bold=True,max_end=68)
   lead=f'En {yyear}, por cada $100 de ingresos, '+(f'faltaron {per100(f)} para cubrir los gastos y los intereses.' if f<0 else f'quedaron {per100(f)} después de cubrir los gastos y los intereses.')
   self.paragraph(lead+' '+self.editorial['opening'],18,67,174,11,15,max_end=91)
  else:
   self.paragraph(f'Falta el cierre {yyear} para evaluar las cuentas',18,49,174,18,22,bold=True,max_end=68)
   self.paragraph(f'La fuente comparable no informa la ejecución completa de {m["province"]} para {yyear}. Un casillero vacío no indica equilibrio ni gasto cero. '+self.editorial['opening'],18,67,174,11,15,max_end=91)
  self.kpi(18,94,55,'INGRESOS '+str(yyear),amount(a['income']).split(' ')[0] if a else 'Sin dato',('billones de pesos corrientes' if a and a['income']>=1e6 else 'mil millones de pesos corrientes'))
  self.kpi(77.5,94,55,'GASTO TOTAL '+str(yyear),amount(a['spending']).split(' ')[0] if a else 'Sin dato',('billones de pesos corrientes' if a and a['spending']>=1e6 else 'mil millones de pesos corrientes'))
  self.kpi(137,94,55,'SALDO / INGRESOS',pct(f,2),'Después de intereses',RUST if f is not None and f<0 else TEAL)
  self.section('A','De dónde sale ese resultado',136)
  if a:
   interest=a['spending']-a['primary_spend'];primary_spend=ratio(a['primary_spend'],a['income']);interest_pct=ratio(interest,a['income'])
   scale=max(100,primary_spend,interest_pct)*1.08
   self.bar('Ingresos',100,148,max_value=scale,value_label='$100,00')
   self.bar('Gasto sin intereses',primary_spend,159,max_value=scale,color=BLUE,value_label=per100(primary_spend))
   self.bar('Intereses',interest_pct,170,max_value=scale,color=GOLD,value_label=per100(interest_pct))
   explanation=(f'El desequilibrio empieza antes de los intereses: faltaron {per100(p)} por cada $100 ingresados. La deuda suma presión, pero no explica todo el déficit.' if p<0 else f'Antes de los intereses quedaron {per100(p)} por cada $100 ingresados. '+('Los intereses absorbieron ese margen y el cierre terminó en déficit.' if f<0 else 'Ese margen permitió afrontar los intereses y conservar un saldo positivo.' if f>0 else 'Los intereses absorbieron ese margen y el cierre quedó equilibrado.'))
   self.paragraph(explanation+' '+self.editorial['mechanism'],18,177,174,10.5,14.3,max_end=203)
  else:
   self.paragraph('No calculamos una composición del gasto ni un saldo con información incompleta. La primera decisión es obtener el cierre, la caja disponible y las obligaciones pendientes.',18,146,174,11,15,max_end=174)
  self.section('B','Qué muestra el comienzo de '+self.d.quarter[:4],211)
  if m['quarter']:
   qp=m['qprimary'];qf=m['qfinancial']
   text=f'En enero-marzo de {self.d.quarter[:4]}, el saldo antes de intereses fue {pct(qp)} de los ingresos y después de intereses, {pct(qf)}. '+self.editorial['quarter']+' Es un corte de tres meses: no permite anticipar por sí solo el resultado de todo el año.'
  else:text=f'Todavía no hay ejecución comparable de enero-marzo de {self.d.quarter[:4]}. No usamos un trimestre anterior como si fuera actual. '+self.editorial['quarter']
  self.paragraph(text,18,219,174,10.5,14.3,max_end=245)
  self.rect(18,248,174,20,PALE,r=2)
  decision=('Ordenar los pagos y corregir el desequilibrio sin interrumpir los servicios esenciales.' if f is not None and f<0 else 'Preservar el margen fiscal y asignar recursos a prioridades con resultados medibles.' if f is not None else 'Completar la información antes de comprometer nuevos gastos permanentes.')
  self.paragraph('<b>Decisión de gestión.</b> '+decision+' El saldo fiscal no equivale a dinero disponible en la cuenta bancaria.',22,251,166,10.2,13.2,max_end=266)
  basis='Santiago del Estero 2025 registra compromiso. Trimestre según DNAP.' if m['province']=='Santiago del Estero' else 'Ingresos percibidos; gastos devengados.'
  self.note('DNAP. Administración Pública no Financiera (APNF), incluye seguridad social. '+basis+' Datos provisorios.',271)

 def page_investment(self):
  m=self.m;a=m['annual'];year=self.d.year;cap=m['metrics']['capital']
  self.header('02  Gasto, inversión y resultados')
  self.paragraph('Invertir más exige elegir mejor',18,49,174,20,24,bold=True,max_end=62)
  lead=(f'En {year}, ${number(cap)} de cada $100 gastados se destinaron a capital. Esa partida incluye obras, equipamiento, transferencias e inversión financiera. Su tamaño muestra una prioridad presupuestaria; la calidad se mide por lo que mejora.' if a else f'No hay un cierre {year} comparable para medir cuánto se destinó a capital. Las prioridades deben apoyarse en proyectos, costos y resultados verificables.')
  lead+=' Recomendamos elegir inversiones que resuelvan problemas concretos y prever cuánto costará sostenerlas. Terminar una obra sin recursos para que funcione deja una necesidad sin resolver.'
  self.paragraph(lead,18,65,174,11,15,max_end=94)
  self.section('A','Cómo se distribuye el gasto '+str(year),102)
  if a:
   known=sum(a[k] for k in ['personnel','pensions','current_transfers','capital']);interest=a['spending']-a['primary_spend']
   composition=[('Personal',a['personnel'],BLUE),('Seguridad social',a['pensions'],BLUE),('Transferencias',a['current_transfers'],BLUE),('Capital',a['capital'],TEAL),('Intereses',interest,GOLD),('Otros gastos',a['spending']-known-interest,MUTED)]
   for i,(label,value,color) in enumerate(composition):self.bar(label,ratio(value,a['spending']),113+i*9,max_value=100,color=color,value_label=pct(ratio(value,a['spending'])))
  else:
   self.paragraph('Sin información anual homogénea. No se clasifica a la provincia en un ranking con datos de otro año.',18,108,174,11,15,max_end=132)
  self.section('B','Capital: comparar el mismo período',171)
  self.text('Año',18,177,9.5,True,MUTED);self.text('Capital / gasto total',60,177,9.5,True,MUTED)
  for i,row in enumerate(m['history']):
   self.text(str(year-2+i),18,187+i*8,10.5);self.text(pct(ratio(row['capital'],row['spending'])) if row else 'Sin dato',60,187+i*8,10.5,True)
  if a and a['basis']=='devengado':
   comparison='por debajo' if cap<m['benchmark'] else 'por encima' if cap>m['benchmark'] else 'al mismo nivel'
   comparator=f'La provincia está {comparison} del {pct(m["benchmark"])} del agregado de {m["benchmark_n"]} jurisdicciones. Eso describe cuánto pesa la inversión, no su eficiencia. Con gasto total constante, sumar un punto a capital exige reasignar {amount(a["spending"]/100)}. La meta necesita proyectos y financiamiento.'
  else:comparator='La comparación exige el mismo año y criterio de registro. La Pampa no informa 2025 y Santiago del Estero registra compromiso; se excluyen del agregado comparable.'
  self.paragraph(comparator,106,179,86,9.5,12.4,max_end=211)
  qtext=(f'Enero-marzo: {pct(m["qpcapital"])} en {int(self.d.quarter[:4])-1} y {pct(m["qcapital"])} en {self.d.quarter[:4]}. '+('La inversión perdió participación en el gasto.' if m['qcapital']<m['qpcapital'] else 'La inversión ganó participación en el gasto.' if m['qcapital']>m['qpcapital'] else 'La participación no cambió.')+' Esto no mide la variación real de los montos.' if m['qcapital'] is not None and m['qpcapital'] is not None else 'Sin dos primeros trimestres completos, no se calcula una variación comparable.')
  self.paragraph(qtext,18,215,174,10.3,14,max_end=231)
  self.section('C','El presupuesto tiene que mejorar servicios',238)
  edu=next(p for p in m['pillars'] if p['id']=='education');math_metric=next(r for r in edu['metrics'] if r['id']=='math_high')
  health=next(p for p in m['pillars'] if p['id']=='health');infant=next(r for r in health['metrics'] if r['id']=='infant_mortality')
  self.paragraph(f'<b>Aprendizaje.</b> {pct(math_metric["value"])} de los estudiantes evaluados alcanzó nivel satisfactorio o avanzado en Matemática ({escape(math_metric["period"])}). Participación: {pct(edu["participation"]["students_pct"])}.',18,244,84,9.6,12.7,max_end=266)
  self.paragraph(f'<b>Salud.</b> {number(infant["value"])} muertes infantiles por cada 1.000 nacidos vivos ({infant["period"]}). El seguimiento del gasto tiene que incluir cobertura y resultados: ejecutar una partida no prueba que el servicio haya mejorado.',108,244,84,9.6,12.7,max_end=268)
  self.note('APNF. Agregado comparable sin La Pampa y Santiago del Estero. Aprender y DEIS: años propios; no se atribuye un resultado al gasto de otro período.',271)

 def page_agenda(self):
  m=self.m;t=m['transfers'];year=t['through'][:4];month=MONTHS[int(t['through'][-2:])-1]
  self.header('03  Recursos, deuda y agenda de gestión')
  self.section('A','La relación con Nación, con números claros',54)
  if t['current'] is not None:
   transfer=f'Entre enero y {month} de {year}, ingresaron {amount(t["current"])} por transferencias automáticas nacionales.'
   if t['real_pct'] is not None:transfer+=f' Frente a los mismos meses de {int(year)-1}, '+(f'crecieron {pct(t["real_pct"])}' if t['real_pct']>=0 else f'cayeron {pct(abs(t["real_pct"]))}')+' después de descontar la inflación mes a mes.'
   else:transfer+=' No hay una base mensual completa para afirmar cuánto variaron en términos reales.'
  else:transfer='Falta un acumulado mensual completo de transferencias automáticas. No sumamos períodos sueltos como si fueran el total del año.'
  self.paragraph(transfer+' '+self.editorial['federal'],18,62,174,10.5,14.3,max_end=89)
  federal='Son fondos distribuidos por ley. Los envíos discrecionales y los reclamos pendientes deben analizarse por separado. Recomendamos defender los reclamos documentados y, al mismo tiempo, ordenar las cuentas propias. Presupuestar como disponible lo que todavía no se cobró puede dejar pagos sin respaldo.'
  self.paragraph(federal,18,92,174,10.5,14.3,max_end=113)
  self.section('B','La deuda importa por cuánto y cuándo se paga',120)
  projection=m['projection'];debt=m['debt'];debt_ratio=debt.get('ratios',{}).get('debt_income_pct') if debt else None
  stock=(f'Por cada $100 de ingresos de doce meses, había ${number(debt_ratio)} de deuda al {quarter_label(self.d.quarter)}. Ese dato no dice cuánto hay que pagar este año. ' if debt_ratio is not None else 'Falta el monto total de deuda comparable al último corte. ')
  if projection:
   rows=projection['rows'];shown=rows[:5];maxval=max(r['total_ars_m'] for r in shown);unit='millones de pesos'
   self.paragraph(stock+'El gráfico muestra el calendario publicado; hay que descontar lo ya pagado y actualizar refinanciaciones y tipo de cambio.',18,128,174,10.2,13.6,max_end=147)
   labels=projection.get('interest_label','Intereses')
   chart_title='Amortizaciones, otros pasivos, intereses y gastos' if m['province']=='Entre Ríos' else 'Servicios anuales: capital + '+labels.lower()
   self.text(chart_title,18,155,8.5,True,MUTED)
   for i,r in enumerate(shown):
    x=22+i*34;bh=19*r['total_ars_m']/maxval
    self.rect(x,181-bh,23,bh,TEAL,r=.8)
    self.text(str(r['year']),x+5,187,8.5,True)
    self.text(number(r['total_ars_m']/1000,1),x+1,180-bh,8.1,True,TEAL)
   source_date='Valuación: '+date_label(projection['as_of']) if projection.get('as_of') else 'Valuación no informada; publicado '+date_label(projection.get('publication_date'))
   self.note('Miles de millones de pesos. '+projection.get('scope','')+'. '+source_date+'.',190,max_end=202)
  else:
   self.paragraph(stock+'La serie histórica muestra capital e intereses registrados en años anteriores. Todavía falta un calendario futuro verificado: con esos datos no se puede saber qué año concentrará más vencimientos.',18,128,174,10.5,14.3,max_end=155)
   self.rect(18,162,174,35,PALE,r=2)
   self.paragraph('<b>Qué hace falta para decidir.</b> Reunir vencimientos por mes y moneda, caja de libre disponibilidad y financiamiento confirmado. Así se puede detectar si los pagos de deuda compiten con salarios, proveedores o inversión.',22,166,166,10.5,14.3,max_end=193)
  self.section('C','Una agenda para los primeros 100 días',211)
  f=m['metrics']['financial'];cap=m['metrics']['capital']
  one=('Separar el déficit fiscal de los vencimientos de capital.' if f is not None and f<0 else 'Distinguir el superávit de la caja de libre disponibilidad.' if f is not None else 'Obtener el cierre fiscal y las obligaciones pendientes.')
  agenda='<b>En los primeros 30 días:</b> '+one[0].lower()+one[1:]+' Armar un plan de caja semanal de 13 semanas, con prioridad para servicios esenciales. <b>A los 60 días,</b> presentar una cartera de obras y equipamiento ordenada por impacto, costo total y financiamiento. <b>A los 100 días,</b> publicar metas de aprendizaje y salud, con responsables y plazos, e informar su avance junto con el presupuesto.'
  y=self.paragraph(agenda,18,219,174,10.3,13.7,max_end=245)+3
  self.paragraph('<b>Nuestra lectura.</b> '+self.editorial['closing'],18,y,174,10.3,13.7,max_end=259)
  self.note('Base: tablero provincial, DNAP, 1816, IPC INDEC, Aprender y DEIS. Pesos corrientes salvo variaciones reales de transferencias. Montos anuales sin ajuste por IPC; no hay proyecciones de ingresos. Cortes propios en cada bloque.',262,max_end=275)
  self.link('Datos y método del informe',SITE+'reports/metodologia.html',18,279)
  self.link('Abrir el tablero',SITE,152,279)
 def build(self):
  self.page_accounts();self.page_investment();self.page_agenda();self.c.save()
  return self.layouts

def fingerprints():
 # Text newlines are canonicalized so Windows and CI validate the same content.
 return {name:hashlib.sha256((ROOT/name).read_bytes() if name.endswith('.ttf') else (ROOT/name).read_text(encoding='utf-8').encode('utf-8')).hexdigest() for name in BUILD_INPUTS}
def build(output,province=None):
 for name,file in [('Lato','Lato-Regular.ttf'),('LatoBold','Lato-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(ROOT/'assets/report-fonts'/file)))
 pdfmetrics.registerFontFamily('Lato',normal='Lato',bold='LatoBold',italic='Lato',boldItalic='LatoBold')
 output.mkdir(parents=True,exist_ok=True);data=ReportData();entries=[];layouts={}
 for name in ([province] if province else data.provinces):
  model=data.model(name);file=f'informe-{slug(name)}.pdf';layouts[name]=Report(output/file,model,data).build()
  entries.append(dict(province=name,file=file,pages=3,sha256=hashlib.sha256((output/file).read_bytes()).hexdigest(),annual_year=data.year,quarter=data.quarter,transfer_cutoff=data.transfer_cut,annual_available=model['annual'] is not None,forward_debt_calendar=model['projection'] is not None))
 manifest=dict(schema_version=1,author='Federico Pellegrini',title='Informe de gestión provincial',reviewed_at=data.reviewed,method='Tres páginas por jurisdicción. Se usa el último año completo común, sin sustituir faltantes por años anteriores. Cuentas APNF y trimestres separados. Transferencias: total legal (1)+(2), mes a mes en pesos constantes con IPC nacional observado para variaciones reales. No equivale a la vista, unidad o perfil transitorios de la pantalla. Los informes se regeneran desde los archivos de datos del tablero.',input_sha256=fingerprints(),sources=[dict(label='Cuentas anuales APNF',url=data.annual['source_url']),dict(label='Ejecución trimestral APNF',url='https://www.argentina.gob.ar/economia/sechacienda/coordinacion-fiscal-provincial/ejecucion-presupuestaria-provincial/ejecuciones'),dict(label='Recursos nacionales 2025',url=jsonfile('data/ron_2025_import.json')['source_url']),dict(label='Recursos nacionales 2026',url=jsonfile('data/meta.json')['sources']['transferencias_nacion_2026']['url']),dict(label='Datos de deuda y calendarios',url=SITE+'data/provincial_debt_services.json'),dict(label='Resultados y referencias por indicador',url=SITE+'data/government_results_provinces.json'),dict(label='IPC observado',url=SITE+'data/ipc_national_index.csv')],reports=entries)
 (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 links=''.join(f'<li><a href="{escape(s["url"])}">{escape(s["label"])}</a></li>' for s in manifest['sources'])
 method='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cómo leer el informe · Federico Pellegrini</title>
<style>body{margin:0;background:#f3f6f8;color:#172e46;font:17px/1.65 system-ui,sans-serif}main{max-width:760px;padding:32px 24px;margin:auto}h1{font-size:34px;line-height:1.2}h2{font-size:22px;margin-top:30px}a{color:#175c91}li{margin:9px 0}.credit{color:#14796f;font-weight:650}footer{border-top:1px solid #d5e1e6;margin-top:30px;padding-top:16px;font-size:14px}</style>
<main><p class="credit">Federico Pellegrini · Informe de gestión provincial</p><h1>Qué datos usa el informe y cómo se comparan</h1>
<p>El informe tiene tres páginas para cada provincia. Cada bloque indica su período. El cierre anual, el primer trimestre y las transferencias mensuales responden a preguntas distintas; no se suman entre sí.</p>
<h2>Cuentas y gasto</h2><p>Se utiliza la Administración Pública no Financiera (APNF), que incluye seguridad social. Los ingresos se registran cuando se perciben y los gastos cuando se devengan. El resultado primario excluye intereses; el financiero los incluye. Ninguno acredita por sí solo caja disponible.</p>
<p>La Pampa no tiene cierre 2025 completo. Santiago del Estero informa compromiso en vez de devengado. Por eso el agregado comparable de gasto de capital incluye 22 jurisdicciones. Es la suma de su gasto de capital dividida por la suma de su gasto total. No mide eficiencia y las responsabilidades provinciales pueden diferir.</p>
<h2>Pesos e inflación</h2><p>Los montos fiscales se muestran en pesos corrientes de cada período. Para medir la variación real de las transferencias, cada mes se lleva a precios de una misma fecha con el IPC nacional observado; después se suman los mismos meses de ambos años. Si falta un mes o un índice, no se completa con cero ni con un supuesto.</p>
<h2>Deuda y resultados de gobierno</h2><p>El stock no es lo que vence este año. Los calendarios conservan la fecha de valuación o publicación, y no descuentan automáticamente pagos posteriores. Los registros históricos no se convierten en proyecciones. En Entre Ríos, el presupuesto plurianual incluye otros pasivos y gastos además de capital e intereses.</p>
<p>Aprender y las estadísticas de mortalidad infantil conservan sus propios años. Se informa la participación estudiantil. No se atribuye un resultado social al gasto de un período diferente. Las recomendaciones son una agenda de trabajo, no un presupuesto aprobado.</p>
<h2>Referencias y respaldo</h2><ul>'''+links+'''</ul><p><a href="../">Volver al tablero</a></p><footer>Federico Pellegrini · Los informes se actualizan junto con los datos publicados del tablero.</footer></main></html>'''
 (output/'metodologia.html').write_text(method,encoding='utf-8')
 return manifest,layouts

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'reports');parser.add_argument('--province');parser.add_argument('--check',action='store_true');args=parser.parse_args()
 if args.check:
  manifest=json.loads((args.output/'manifest.json').read_text(encoding='utf-8'))
  if manifest['input_sha256']!=fingerprints():raise SystemExit('Reports are stale: run python scripts_export_management_reports.py')
  for entry in manifest['reports']:
   if hashlib.sha256((args.output/entry['file']).read_bytes()).hexdigest()!=entry['sha256']:raise SystemExit('PDF hash mismatch: '+entry['file'])
  print(f'Fresh reports: {len(manifest["reports"])}; all input and PDF hashes verified.')
 else:
  manifest,_=build(args.output,args.province);print(f'Generated {len(manifest["reports"])} reports, exactly 3 pages each.')

if __name__=='__main__':main()

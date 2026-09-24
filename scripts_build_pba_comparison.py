"""PBA comparisons from official originals; no inferred monthly expenditure."""
import csv, hashlib, json
from pathlib import Path
import openpyxl

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'data/pba_sources'
URL='https://www.ec.gba.gov.ar/areas/hacienda/PolTributaria/Recaudacion/'

def read_rows(path):
 return list(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()))

def monthly(path,year):
 sheet=openpyxl.load_workbook(path,data_only=True)[str(year)]
 assert 'MILLONES DE PESOS' in sheet['B4'].value
 rows=[]
 for row in sheet.iter_rows(min_row=7,max_row=18,values_only=True):
  month=row[2]
  if row[3] is None:continue # Future spreadsheet totals may contain formula zeros.
  values={'Iibb':row[3],'Inmobiliario':row[7],'Automotores':row[8],'Sellos':row[10],
          'Otros':sum(row[i] for i in [9,11,12,14]),'Total':row[15]}
  assert abs(sum(v for k,v in values.items() if k!='Total')-values['Total'])<.02
  for tax,value in values.items():
   assert isinstance(value,(int,float)) and value>=0
   rows.append(dict(province='Buenos Aires',source=path.name,year=year,period_type='month',period=f'{year}-{month:02}',tax=tax,value_millions=value))
 return rows

def build():
 old=monthly(SOURCE/'recaudacion-2025.xlsx',2025);new=monthly(SOURCE/'recaudacion-2026.xlsx',2026)
 assert len(old)==72
 # Current PBA and national collector must reconcile before linking vintages.
 existing=read_rows(ROOT/'pba_top_monthly.csv')
 for row in existing:
  for tax,col in [('Total','top_total_ars_m'),('Iibb','iibb_ars_m'),('Inmobiliario','inmobiliario_ars_m'),('Automotores','automotores_ars_m'),('Sellos','sellos_ars_m'),('Otros','otros_top_ars_m')]:
   actual=next(x['value_millions'] for x in new if x['period']==row['fecha_corte'][:7] and x['tax']==tax)
   assert abs(actual-float(row[col]))<.02
 path=ROOT/'top_mensual_2025_normalizado.csv';rows=[x for x in read_rows(path) if x['province']!='Buenos Aires']+old
 with path.open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 ipc={r['period']:float(r['ipc_index']) for r in read_rows(ROOT/'data/ipc_national_index.csv')}
 months=sorted({r['period'][5:] for r in new});base=ipc['2026-06']
 taxes=[]
 for tax in ['Total','Iibb','Sellos','Inmobiliario','Automotores','Otros']:
  series={r['period']:r['value_millions'] for r in old+new if r['tax']==tax}
  nominal={y:sum(series[f'{y}-{m}'] for m in months) for y in [2025,2026]}
  real={y:sum(series[f'{y}-{m}']*base/ipc[f'{y}-{m}'] for m in months) for y in [2025,2026]}
  taxes.append(dict(tax=tax,previous=nominal[2025],current=nominal[2026],real_change_pct=(real[2026]/real[2025]-1)*100,
   monthly=[dict(period=f'2026-{m}',real_change_pct=(series[f'2026-{m}']/series[f'2025-{m}']*ipc[f'2025-{m}']/ipc[f'2026-{m}']-1)*100) for m in months]))
 execution=json.loads((ROOT/'data/pba_execution_latest.json').read_text(encoding='utf8'))
 # Official APNF page 13. Expenses are mutually exclusive; tolerate rounding.
 for row,extras in zip(execution['rows'],[(871058,2123153,2321),(1085872,2787650,2)]):
  row.update(zip(['operating','other_transfers','other_losses'],extras))
  keys=['personnel','pensions','municipal_current_transfers','other_transfers','operating','capital','interest','other_losses']
  assert abs(sum(row[k] for k in keys)-row['spending'])<=3
 execution['reviewed_at']='2026-09-24'
 (ROOT/'data/pba_execution_latest.json').write_text(json.dumps(execution,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 ratio=sum(ipc[f'2026-{m:02}'] for m in range(1,7))/sum(ipc[f'2025-{m:02}'] for m in range(1,7))
 a,b=execution['rows'];spending=[]
 for key,label in [('income','Ingresos'),('spending','Gasto total'),('personnel','Personal'),('pensions','Jubilaciones'),('municipal_current_transfers','Transferencias a municipios'),('other_transfers','Otras transferencias corrientes'),('operating','Bienes y servicios'),('capital','Gasto de capital'),('interest','Intereses'),('other_losses','Otras pérdidas')]:
  spending.append(dict(key=key,label=label,previous=a[key],current=b[key],real_change_pct=(b[key]/a[key]/ratio-1)*100,share_pct=b[key]/b['spending']*100 if key!='income' else None))
 sources=[dict(file=f,url=URL+u,sha256=hashlib.sha256((SOURCE/f).read_bytes()).hexdigest()) for f,u in [('recaudacion-2025.xlsx','Recursos_OrigenProvincial_anosanteriores.xlsx'),('recaudacion-2026.xlsx','Recaudaci%C3%B3n%20Provincial%202026_Prensa.xlsx')]]
 data=dict(reviewed_at='2026-09-24',revenue_period='Enero–julio 2026',revenue_cutoff='2026-07',revenue=taxes,spending_period='Enero–junio 2026',spending=spending,
  revenue_method='Variación interanual del acumulado: cada flujo mensual se ajusta por IPC nacional observado a pesos de junio de 2026 antes de sumar. No se usa el promedio simple de variaciones.',
  spending_method='Variación interanual del acumulado semestral ajustada por la relación de IPC promedio de enero–junio de cada año. Es una aproximación con datos semestrales; no una deflación de flujos mensuales.',
  semester_ipc_ratio=ratio,sources=sources,execution_source=execution['source'],ipc_source=json.loads((ROOT/'data/ipc_source.json').read_text(encoding='utf8')))
 (ROOT/'data/pba_comparison.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Imported 12 months / 72 observations in 2025; reconciled 2026; built comparisons.')

if __name__=='__main__':build()

"""Import official provincial accrued debt services and verified projected schedules.
Sources are cached outside the repository; never infer payments from accrued values.
"""
import csv,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def build(cache):
 import pandas as pd,pdfplumber
 sources=json.loads((cache/'province-sources.json').read_text(encoding='utf-8'));history=[];catalog=[]
 for source in sources:
  p=cache/(source['province']+'.xlsx');d=pd.read_excel(p,header=None)
  h=next(i for i,r in d.iterrows() if any(str(v).strip().upper().startswith('TOTAL') for v in r))
  total=next(c for c,v in enumerate(d.iloc[h]) if str(v).strip().upper().startswith('TOTAL'));yc=next(c for c,v in enumerate(d.iloc[h]) if str(v).strip()=='Año')
  thousands='Miles' in str(d.iloc[3].to_list());div=1000 if thousands else 1
  def number(v):return None if pd.isna(v) else float(v)/div
  for _,r in d.iterrows():
   year=r.iloc[yc]
   if not isinstance(year,(int,float)) or pd.isna(year) or not 2005<=year<=2025:continue
   capital=number(r.iloc[total]);interest=number(r.iloc[total+1]);history.append(dict(province=source['province'],period=str(int(year)),period_type='year',amortization_ars_m=capital,interest_ars_m=interest,total_ars_m=None if capital is None or interest is None else capital+interest,source_url=source['url']))
  catalog.append(dict(province=source['province'],url=source['url'],sha256=hashlib.sha256(p.read_bytes()).hexdigest(),original_unit='ARS miles' if thousands else 'ARS millones'))
 differences=[]
 for name,period,kind,url in [('services2025.xlsx','2025','year','https://www.argentina.gob.ar/sites/default/files/servicios_iv_trim_2025.xlsx'),('services2026.xlsx','2026-Q1','quarter','https://www.argentina.gob.ar/sites/default/files/ev._de_servicios_-_consolidado_2026_-_trim._i.xlsx')]:
  d=pd.read_excel(cache/name,header=None)
  for _,r in d.iloc[14:38].iterrows():
   province=str(r.iloc[1]).strip().replace('Santa Fé','Santa Fe');capital=None if pd.isna(r.iloc[2]) else float(r.iloc[2]);interest=None if pd.isna(r.iloc[3]) else float(r.iloc[3]);row=dict(province=province,period=period,period_type=kind,amortization_ars_m=capital,interest_ars_m=interest,total_ars_m=None if capital is None or interest is None else capital+interest,source_url=url)
   if kind=='quarter':history.append(row)
   else:
    prev=next((x for x in history if x['province']==province and x['period']==period),None)
    if prev is None:history.append(row)
    elif capital is not None and interest is not None:
     delta=max(abs(prev['amortization_ars_m']-capital),abs(prev['interest_ars_m']-interest))
     if delta>1e-6:differences.append(dict(province=province,period=period,max_difference_ars_m=delta,note='Se conserva la serie por provincia; difiere del consolidado de la misma fuente.'))
 projections={}
 with (ROOT/'data/debt/pba_debt_service_schedule_2026_2041.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
 projections['Buenos Aires']=dict(as_of='2025-12-31',scope='Perfil oficial de deuda provincial',interest_label='Intereses',note='Valuado al 31/12/2025. Es el calendario publicado para todo el año; no descuenta pagos posteriores.',sources=[{'label':'Informe de deuda PBA, página 6','url':'https://www.ec.gba.gov.ar/areas/finanzas/deuda/archivos/Informe%20de%20Deuda%20PBA%20al%2031-dic-2025.pdf'}],rows=[dict(year=int(r['year']),amortization_ars_m=float(r['amortization_ars_m']),interest_ars_m=float(r['interest_ars_m']),total_ars_m=float(r['total_service_ars_m'])) for r in rows])
 values={}
 for kind,key,url in [('capital','cordoba-capital.pdf','https://economiaygestionpublica.cba.gov.ar/download/7738/'),('interest','cordoba-interest.pdf','https://economiaygestionpublica.cba.gov.ar/download/7733/')]:
  with pdfplumber.open(cache/key) as pdf:text=pdf.pages[0].extract_text()
  line=next(l for l in text.splitlines() if l.startswith('TOTAL'))
  values[kind]=[int(v.replace('.',''))/1e6 for v in re.findall(r'\d[\d.]+',line)];assert len(values[kind])==7
 projections['Córdoba']=dict(as_of='2026-01-02',scope='Administración Central + ACIF · Presupuesto 2026',interest_label='Intereses y gastos',note='Proyección presupuestaria actualizada el 02/01/2026, expresada en pesos. Incluye gastos junto con intereses. No descuenta los pagos posteriores.',sources=[{'label':'Proyección de amortizaciones, página 1','url':'https://economiaygestionpublica.cba.gov.ar/download/7738/'},{'label':'Proyección de intereses y gastos, página 1','url':'https://economiaygestionpublica.cba.gov.ar/download/7733/'}],rows=[dict(year=2026+i,amortization_ars_m=values['capital'][i],interest_ars_m=values['interest'][i],total_ars_m=values['capital'][i]+values['interest'][i]) for i in range(7)])
 er_path=cache.parent/'completion-sources/presupuesto_provincial_-_entre_rios_1.xls'
 er=pd.read_excel(er_path,sheet_name='2026',header=None)
 with pdfplumber.open(cache/'entrerios.pdf') as pdf:er_text=pdf.pages[0].extract_text()
 capital=[432894374000,233465554000,176202015000];interest=[104373076000,61524642000,35882884000]
 for value in capital+interest:assert f'{value:,}'.replace(',','.') in er_text
 reconciliation=[]
 for label,row,value in [('Intereses y otros gastos',28,interest[0]),('Amortización y disminución de otros pasivos',74,capital[0])]:
  official=float(er.iloc[row,8]);delta=value/1e6-official;assert abs(delta)<.01
  reconciliation.append(dict(label=label,cell=f'I{row+1}',budget_ars_m=official,annex_ars=value,difference_ars_m=delta))
 projections['Entre Ríos']=dict(as_of=None,publication_date='2025-11-28',scope='Sector Público No Financiero Provincial · Presupuesto plurianual 2026–2028',interest_label='Intereses y otros gastos',note='Proyección orientativa presentada el 28/11/2025. Unidad conciliada con el presupuesto oficial 2026; incluye otros pasivos y gastos. No equivale a deuda pendiente de hoy ni descuenta pagos posteriores.',sources=[{'label':'Anexo I · servicios 2026–2028','url':'https://www.entrerios.gov.ar/presupuesto/leypres/p26-28/pdf/ANEXO1.pdf'},{'label':'Presupuesto 2026 · conciliación de unidad, columna Sector Público','url':'https://www.argentina.gob.ar/sites/default/files/presupuesto_provincial_-_entre_rios_1.xls'},{'label':'Mensaje del presupuesto plurianual','url':'https://www.entrerios.gov.ar/presupuesto/leypres/p26-28/pdf/MENSAJE.pdf'}],unit_reconciliation=reconciliation,source_hashes={'annex':hashlib.sha256((cache/'entrerios.pdf').read_bytes()).hexdigest(),'budget':hashlib.sha256(er_path.read_bytes()).hexdigest()},rows=[dict(year=2026+i,amortization_ars_m=capital[i]/1e6,interest_ars_m=interest[i]/1e6,total_ars_m=(capital[i]+interest[i])/1e6) for i in range(3)])
 payload=dict(reviewed_at='2026-09-06',unit='ARS millions',history_basis='Servicios devengados, preliminares, netos de deuda indirecta. No equivalen a pagos de caja ni a vencimientos futuros. Pesos corrientes de cada período, sin ajuste por inflación.',history=history,sources=catalog,source_differences=differences,projections=projections,coverage=[dict(province=s['province'],schedule_status='verified' if s['province'] in projections else 'not_loaded',schedule_note='Calendario incorporado con fuente y fecha de referencia.' if s['province'] in projections else 'El enlace oficial al perfil 30/06/2026 devolvió HTTP 404 el 06/09/2026.' if s['province']=='CABA' else 'No hay un calendario futuro verificado cargado; no implica ausencia de deuda ni de publicaciones.') for s in sources])
 assert len({r['province'] for r in history})==24
 (ROOT/'data/provincial_debt_services.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 with (ROOT/'data/provincial_debt_services.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(history[0]));w.writeheader();w.writerows(history)
 print('History',len(history),'projections',list(projections),'source differences',differences)
if __name__=='__main__':build(Path(sys.argv[1]))


"""Build source-traceable 2026 budgets and Q1 executions; preserve source scopes."""
import json,re,hashlib,unicodedata,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
COLS={'Buenos Aires':1,'CABA':5,'Catamarca':5,'Chaco':1,'Chubut':3,'Córdoba':5,'Corrientes':2,'Entre Ríos':4,'Formosa':4,'Jujuy':4,'La Pampa':1,'La Rioja':4,'Mendoza':1,'Misiones':2,'Neuquén':5,'Río Negro':6,'Salta':3,'San Juan':6,'San Luis':2,'Santa Cruz':4,'Santa Fe':4,'Santiago del Estero':1,'Tierra del Fuego':1,'Tucumán':1}
LEGAL={'Chaco':'https://contaduriageneral.chaco.gob.ar/leyes','Santa Cruz':'https://boletinoficial.santacruz.gob.ar/legislacion/leyes/52781','Tucumán':'https://presupuesto.mecontuc.gob.ar/presupuestoGrales.html'}
def norm(s):return re.sub(r'\s+',' ',''.join(c for c in unicodedata.normalize('NFD',str(s).upper()) if not unicodedata.combining(c))).strip()
def build(cache):
 links=json.loads((cache/'links.json').read_text(encoding='utf-8'));budgets=[];sources=[]
 for link in [r for r in links if r['kind']=='presupuestos']:
  province=link['label'].split(' Descargar')[0].strip();assert province in COLS,province
  path=cache/link['url'].split('/')[-1];d=pd.read_excel(path,sheet_name='2026',header=None);col=COLS[province];header=' | '.join(str(v).strip() for r in d.head(9).values for v in r if isinstance(v,str));factor=1000 if 'MILES DE PESOS' in norm(header) else 1;assert 'MILLONES' in norm(header) or factor==1000
  labels={i:norm(next((v for v in r if isinstance(v,str) and v.strip()),'')) for i,r in d.iterrows()}
  trace={}
  def val(metric,indices,signs=None):
   if isinstance(indices,int):indices=[indices]
   signs=signs or [1]*len(indices);values=[d.iloc[i,col] for i in indices];trace[metric]=[dict(cell=f'{chr(65+col)}{i+1}',label=labels[i],multiplier=sign,original_value=None if pd.isna(v) else float(v)) for i,sign,v in zip(indices,signs,values)]
   return None if any(pd.isna(v) for v in values) else sum(float(v)*sg for v,sg in zip(values,signs))/factor
  def find(pattern):
   found=[i for i,l in labels.items() if re.search(pattern,l) and pd.notna(d.iloc[i,col])];return found[0] if found else None
  if province=='Buenos Aires':ir=[9,46];gr=25;cr=54;income=val('income',ir);spend=val('spending',[25,54]);capital=val('capital',cr)
  elif province=='Chaco':income=val('income',17);spend=val('spending',9);capital=val('capital',11)
  elif province=='Misiones':income=val('income',[13,14]);spend=val('spending',9);capital=val('capital',11)
  elif province=='Tucumán':income=val('income',[39,14,29],[1,-1,-1]);spend=val('spending',[40,22,36],[1,-1,-1]);capital=val('capital',[38,36],[1,-1])
  else:
   ir=find(r'INGRESOS TOTALES|TOTAL DE RECURSOS');gr=find(r'GASTOS TOTALES|EGRESOS TOTALES|TOTAL DE GASTOS');cr=find(r'(GASTOS|EROGACIONES) DE CAPITAL');assert None not in [ir,gr,cr],(province,ir,gr,cr)
   income=val('income',ir);spend=val('spending',gr);capital=val('capital',cr)
  eligible=province in ['CABA','Chubut','Córdoba','Entre Ríos','Formosa','Jujuy','Santa Cruz']
  note='Presupuesto inicial, no crédito vigente. Los ajustes metodológicos de DNAP pueden diferir de la presentación provincial.'
  if province in LEGAL:note+=' El encabezado del archivo tiene un año inconsistente; la norma oficial confirma el ejercicio 2026.'
  if province=='Tierra del Fuego':note+=' Presupuesto 2025 prorrogado para 2026 por Decreto 32/2026.'
  if province=='Tucumán':note+=' Se restan recursos y gastos figurativos internos para evitar duplicación.'
  if province=='Misiones':note+=' Original en miles de pesos, convertido a millones. Se excluye financiamiento de los ingresos.'
  budgets.append(dict(province=province,year=2026,unit='ARS millions',income=income,spending=spend,capital=capital,source_header=header,source_url=link['url'],law_source_url=LEGAL.get(province),selected_column=col+1,scope_comparison=eligible,note=note,trace=trace))
  sources.append(dict(url=link['url'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),kind='Presupuesto 2026',province=province))
 executions=[]
 for period,file in [('2026-Q1','ejecuciones_presupuestarias_apnf_2026_-_trim._i.xls'),('2025-Q1','ejecuciones_presupuestarias_apnf_2025_-_trim._i.xls')]:
  path=cache/file;d=pd.read_excel(path,header=None);header=next(i for i,r in d.iterrows() if str(r.iloc[0]).strip()=='Concepto');mapping={str(v).strip():c for c,v in enumerate(d.iloc[header]) if str(v).strip() in COLS};assert len(mapping)==24
  labels={i:norm(r.iloc[0]) for i,r in d.iterrows()};indices={k:next(i for i,l in labels.items() if re.search(p,l)) for k,p in {'income':r'^VI\. INGRESOS TOTALES','spending':r'^VII\. GASTOS TOTALES','capital':r'^V\. GASTOS DE CAPITAL','primary':r'^VIII\. GASTOS PRIMARIOS'}.items()}
  url=next(r['url'] for r in links if r['url'].endswith('/'+file))
  for province,col in mapping.items():
   values={k:None if pd.isna(d.iloc[i,col]) else float(d.iloc[i,col]) for k,i in indices.items()};executions.append(dict(province=province,period=period,scope='APNF',basis='Ingresos percibidos; gastos devengados; datos provisorios',source_url=url,trace={k:f'{chr(65+col)}{i+1}' for k,i in indices.items()},**values))
  sources.append(dict(url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),kind='Ejecución '+period,province='24 jurisdicciones'))
 payload=dict(reviewed_at='2026-09-06',unit='ARS millions',budgets=budgets,executions=executions,sources=sources,methodology='Presupuesto inicial anual 2026 frente a ejecución acumulada del primer trimestre. El avance se calcula solo para las siete coberturas APNF identificadas y es orientativo: no mide desvío contra una programación mensual ni crédito vigente. No se supone que 25% sea la meta trimestral.')
 (ROOT/'data/budget_execution_2026.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print('Budgets',len(budgets),'execution rows',len(executions),'comparable',sum(b['scope_comparison'] for b in budgets))
if __name__=='__main__':build(Path(sys.argv[1]))

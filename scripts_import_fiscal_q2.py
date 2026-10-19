"""Import the supplied 2T26 tables, with rounding checks and official H1 evidence.

python scripts_import_fiscal_q2.py supplied.pdf official_cache
The licensed PDF stays local. Public metadata retains its hash and page references.
"""
import csv,hashlib,json,re,sys,shutil
from pathlib import Path
import pdfplumber,pandas as pd
from scripts_build_fiscal_history import ALIASES,FIELDS
from scripts_build_budget_execution import norm
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,v):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def update_histories(rank,debt,sha):
 d=read('data/debt_history.json');d['rows']=[r for r in d['rows'] if r['period']!='2026-Q2'];d['reports']=[r for r in d['reports'] if r['period']!='2026-Q2']
 mapping=dict(salary_share_ex_ss='salary_primary_ex_ss_pct',capital_share_ex_ss='capital_primary_ex_ss_pct',autonomy_ex_ss='autonomy_ex_ss_pct',iibb_own_share='iibb_own_tax_pct',debt_income_pct='debt_income_pct',market_debt_share='bonds_banks_debt_pct',financial_pct='financial_result_pct')
 for row in rank:
  p=row['province'];d['rows'].append(dict(**debt[p],province=p,period='2026-Q2',currency='USD',unit='millions',source_title='Informe fiscal provincias 2T26',source_page=21,ratio_source_page=23,publication_date=None,received_at='2026-10-19',ratios={k:row[v] for k,v in mapping.items()}))
 d['reports'].append(dict(period='2026-Q2',currency='USD',debt_rows=23,ratio_rows=23,sha256=sha));write('data/debt_history.json',d)
 new=[dict(report_period='2026-Q2',publication_date=None,received_at='2026-10-19',source_sha256=sha,province=row['province'],period='2026-Q2',rank=row['general_rank'],source_page=23) for row in rank]
 new.append(dict(report_period='2026-Q2',publication_date=None,received_at='2026-10-19',source_sha256=sha,province='La Pampa',period='2026-Q2',rank=None,source_page=24))
 for path,key in [('data/fiscal_archive.json','rank_history'),('data/fiscal_archive_vintages.json','rank_vintages')]:
  d=read(path);d[key]=[x for x in d[key] if x.get('report_period')!='2026-Q2']+new;write(path,d)
 p=ROOT/'data/fiscal_rank_history.csv';rows=list(csv.DictReader(p.read_text(encoding='utf8').splitlines()));keys=list(rows[0]);rows=[x for x in rows if x['report_period']!='2026-Q2']+[{k:x.get(k) for k in keys} for x in new]
 with p.open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rows)
def build(pdf_path,cache):
 sha=hashlib.sha256(pdf_path.read_bytes()).hexdigest()
 with pdfplumber.open(pdf_path) as pdf:
  fiscal=[]
  for line in pdf.pages[7].extract_text().splitlines():
   m=re.match(r'^(.+?)\s+(-?[\d.]+(?:\s+-?[\d.]+){14})$',line)
   if not m or m[1]=='TOTAL':continue
   v=dict(zip(FIELDS,[int(x.replace('.','')) for x in m[2].split()]))
   residuals=[sum(v[k] for k in FIELDS[:5])-v['income'],sum(v[k] for k in FIELDS[6:11])-v['primary_spend'],v['income']-v['primary_spend']-v['primary'],v['primary']+v['interest_signed']-v['financial']]
   assert max(map(abs,residuals))<=2,(m[1],residuals)
   v.update(province=ALIASES.get(m[1],m[1]),period='2026-Q2',publication_date=None,received_at='2026-10-19',source_title='Informe fiscal provincias 2T26',source_page=8,source_sha256=sha,primary_pct=100*v['primary']/v['income'],financial_pct=100*v['financial']/v['income'])
   fiscal.append(v)
  assert len(fiscal)==23
  rank=[];headers=next(csv.reader((ROOT/'data/fiscal/ranking_1t26.csv').read_text().splitlines()))
  for line in pdf.pages[22].extract_text().splitlines():
   m=re.match(r'^(.+?)\s+(\d+)\s+((?:-?[\d,]+%\s+\d+\s*){7})$',line)
   if not m:continue
   vals=[int(m[2])]+[float(x.replace('%','').replace(',','.')) if '%' in x else int(x) for x in m[3].split()]
   rank.append(dict(zip(headers,[ALIASES.get(m[1],m[1])]+vals)))
  assert len(rank)==23 and {r['general_rank'] for r in rank}==set(range(1,24))
  debt={}
  for line in pdf.pages[20].extract_text().splitlines():
   m=re.match(r'^(.+?)\s+(\d[\d.]*(?:\s+\d[\d.]*){5})\s+\D',line)
   if not m or m[1]=='TOTAL':continue
   vals=[int(x.replace('.','')) for x in m[2].split()];assert abs(vals[0]-sum(vals[1:]))<=2
   debt[ALIASES.get(m[1],m[1])]=dict(zip(['total','bonds','nation','multilateral','banks','consolidated'],vals))
  assert len(debt)==23
  p=pdf.pages[5];words=p.extract_words();names={}
  for w in words:
   if 325<w['top']<398 and w['x0']>105 and '%' not in w['text']:names.setdefault(round(w['x0'],1),[]).append(w['text'][::-1])
  ordered=[ALIASES.get(' '.join(reversed(parts)),' '.join(reversed(parts))) for x,parts in sorted(names.items())]
  vals=[float(w['text'][::-1].replace('%','').replace(',','.')) for w in sorted(words,key=lambda w:w['x0']) if '%' in w['text'] and w['x0']>105 and w['top']>p.height*.55]
  assert len(ordered)==23 and len(vals)==46
  quarters={name:dict(primary_pct=vals[i*2],financial_pct=vals[i*2+1]) for i,name in enumerate(ordered)}
  assert quarters['Buenos Aires']==dict(primary_pct=-2.8,financial_pct=-4.9),quarters['Buenos Aires']
 for r in rank:
  f=next(v for v in fiscal if v['province']==r['province']);assert abs(f['financial_pct']-r['financial_result_pct'])<.051
 sources=json.loads((cache/'sources.json').read_text());executions=[]
 for s in sources:
  name=s['url'].split('/')[-1];dest=ROOT/'data/fiscal/official-q2'/name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(cache/name,dest);s['archive']=str(dest.relative_to(ROOT)).replace('\\','/')
  if not name.startswith('ejecuciones'):continue
  year='2026' if '_2026_' in name else '2025';d=pd.read_excel(dest,header=None)
  labels={i:norm(r.iloc[0]) for i,r in d.iterrows()}
  patterns={'income':r'^VI\. INGRESOS TOTALES','spending':r'^VII\. GASTOS TOTALES','capital':r'^V\. GASTOS DE CAPITAL','primary_spend':r'^VIII\. GASTOS PRIMARIOS','financial':r'^IX\. RESULTADO FINANCIERO','primary':r'^X\. RESULTADO PRIMARIO'}
  ix={k:next(i for i,l in labels.items() if re.search(p,l)) for k,p in patterns.items()}
  universe=read('data/government_results_provinces.json')['province_universe']
  for c,p in enumerate(d.iloc[8]):
   p=str(p).strip()
   if p not in universe:continue
   missing=p=='La Pampa' or pd.isna(d.iloc[ix['income'],c])
   v={k:None if missing or pd.isna(d.iloc[i,c]) else float(d.iloc[i,c]) for k,i in ix.items()}
   if not missing:
    assert abs(v['income']-v['spending']-v['financial'])<.01
    assert abs(v['income']-v['primary_spend']-v['primary'])<.01
   executions.append(dict(province=p,period=year+'-H1',start=year+'-01-01',end=year+'-06-30',source_url=s['url'],trace={k:f'{chr(65+c)}{i+1}' for k,i in ix.items()},**v))
 assert len(executions)==48
 # Keep different vintages distinct: DNAP adjusts the provincial presentation.
 write('data/fiscal_q2_2026.json',dict(period='2026-Q2',cutoff='2026-06-30',reviewed_at='2026-10-19',scope='APNF',unit='ARS millions',source_sha256=sha,source_pages=[6,8,21,23],ltm=fiscal,ranking=rank,quarters=quarters,debt=debt,official_semesters=executions,sources=sources,excluded=[dict(province='Neuquén',page=15,field='quarter_real_tax_change',reported=-228.4,reason='Variación inferior a -100%; requiere conciliación del dato base. No incorporada.'),dict(province='La Pampa',reason='La fuente no publica ejecución completa; no se imputa cero.')],methodology='LTM: julio 2025-junio 2026. Trimestre: abril-junio 2026. DNAP semestral: enero-junio, con adecuaciones metodológicas; no se intercambian sus cifras con la ejecución provincial. El documento recibido se conserva localmente; no se distribuye el PDF.'))
 hist=read('data/fiscal_history.json');hist['rows']=[r for r in hist['rows'] if r['period']!='2026-Q2']+fiscal;write('data/fiscal_history.json',hist)
 with (ROOT/'data/fiscal/ranking_2t26.csv').open('w',encoding='utf-8',newline='') as out:
  w=csv.DictWriter(out,fieldnames=headers,lineterminator='\n');w.writeheader();w.writerows(rank)
 update_histories(rank,debt,sha)
 print('Validated: 23 LTM identities, 23 rankings, 23 quarterly results, 23 debt compositions, 48 official semester records including explicit missing La Pampa')
if __name__=='__main__':build(Path(sys.argv[1]),Path(sys.argv[2]))

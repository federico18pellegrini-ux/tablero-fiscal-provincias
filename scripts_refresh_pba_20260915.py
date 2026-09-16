"""Audited September refresh. Originals remain in the supplied external cache.

Usage: python scripts_refresh_pba_20260915.py CACHE
The common March ranking is preserved. June PBA data have a separate vintage.
"""
import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path
import pandas as pd
import scripts_regenerate_2026 as monthly
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
def save(name,data):(ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def refresh(cache):
 sources=json.loads((cache/'latest-sources.json').read_text(encoding='utf8'))
 source=lambda name:next(s for s in sources if s['file']==name)
 debt_url='https://www.ec.gba.gov.ar/areas/finanzas/deuda/archivos/Informe%20de%20Deuda%20PBA%20al%2030-Jun-2026.pdf'
 debt_source=dict(publisher='Dirección Provincial de Deuda y Crédito Público, PBA',title='Informe de deuda al 30/06/2026',url=debt_url,sha256=hashlib.sha256((cache/'pba-debt-2026q2.pdf').read_bytes()).hexdigest())
 profile=read('data/debt/pba_debt_profile_2026q1.json')
 profile['latest_official_stock']=dict(cutoff='2026-06-30',total_ars_m=17950608.4,total_usd_m_equivalent=12112.4,ars_per_usd=1482,debt_to_ltm_income_pct=45.5,ratio_basis='Recursos de los últimos doce meses; indicador publicado por PBA, anexo p. 7',change_vs_2025q4_nominal_pct=0.2,change_vs_2026q1_nominal_pct=100*(17950608.4/16672419.6-1),fx_share_of_quarter_increase_pct=83.4,creditors=[dict(label='Bonos',pct=80.3),dict(label='Préstamos',pct=19.7)],source=debt_source)
 profile['currency_composition']=dict(cutoff='2026-06-30',payable_foreign_currency_pct=79.2,usd_payable_usd_pct=73.6,eur_pct=5.2,other_foreign_pct=.4,usd_payable_ars_pct=9.6,ars_pct=6.2,ars_cer_pct=5.0,source=debt_source)
 profile['latest_official_indicators']=dict(cutoff='2026-06-30',interest_paid_to_total_resources_pct=3.7,debt_service_paid_to_total_resources_pct=10.3,debt_to_total_resources_pct=45.5,average_life_including_interest_years=5.2,rollover_next_year_pct=12.7,period_basis='Últimos doce meses cuando corresponde, según anexo oficial p. 7',source=debt_source)
 profile['methodology_note']='El ranking conserva DNAP al 31/03/2026. Stock, moneda y perfil de vencimientos más recientes: PBA al 30/06/2026. La conversión del informe provincial usa $1.482 por USD. El stock excluye intereses devengados e impagos. Las dos fuentes tienen distintos criterios de valuación y no se empalman.'
 save('data/debt/pba_debt_profile_2026q1.json',profile)
 capital=[995864,1945000,1985691,1427107,1496156,1158914,1178899,1193786,1216111,1247045,1276703,1307039,136614,112530,111936,111936]
 interest=[683125,1120573,903908,745550,660832,577270,505874,432036,357520,281098,202837,122160,58768,51629,45791,39712]
 totals=[1678989,3065573,2889600,2172657,2156988,1736185,1684773,1625823,1573631,1528143,1479540,1429199,195382,164159,157726,151647]
 rows=[dict(year=2026+i,period_label='Jul–dic 2026' if i==0 else str(2026+i),period_start='2026-07-01' if i==0 else f'{2026+i}-01-01',period_end=f'{2026+i}-12-31',amortization_ars_m=a,interest_ars_m=b,total_ars_m=t) for i,(a,b,t) in enumerate(zip(capital,interest,totals))]
 assert all(abs(r['total_ars_m']-r['amortization_ars_m']-r['interest_ars_m'])<=1 for r in rows)
 projection=dict(as_of='2026-06-30',scope='Perfil oficial de deuda provincial',interest_label='Intereses',note='2026 incluye sólo julio–diciembre; desde 2027 son años completos. Valuación al 30/06/2026, con tipos de cambio y últimas tasas variables de esa fecha.',sources=[dict(label='Informe de deuda PBA, página 6',url=debt_url)],source_sha256=debt_source['sha256'],rows=rows)
 save('data/debt/pba_forward_schedule.json',projection)
 services=read('data/provincial_debt_services.json');services['projections']['Buenos Aires']=projection;services['reviewed_at']='2026-09-15';save('data/provincial_debt_services.json',services)
 with (ROOT/'data/debt/pba_debt_service_schedule_2026_2041.csv').open('w',encoding='utf8',newline='') as f:
  fields=['year','amortization_ars_m','interest_ars_m','total_service_ars_m','valuation_date','status','source','period_label'];w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader()
  for r in rows:w.writerow({k:r[k] for k in fields if k in r}|dict(total_service_ars_m=r['total_ars_m'],valuation_date=projection['as_of'],status='official_schedule',source='Informe de Deuda PBA al 30/06/2026, p. 6'))
 latest=dict(province='Buenos Aires',reviewed_at='2026-09-15',period='2026-H1',period_label='Enero–junio 2026',scope='Administración Pública no Financiera (APNF)',basis='Gasto devengado',unit='ARS millions',status='provisorio',source={**source('execution-pba-q2.pdf'), 'publisher':'Dirección Provincial de Presupuesto Público, PBA','page':13},rows=[dict(year=2025,income=15837261,spending=16698747,financial=-861486,primary=-404992,interest=456494,capital=1056035,personnel=6878339,pensions=3172905,own_tax=6392766,national_tax=5837908,municipal_current_transfers=2138442),dict(year=2026,income=20743442,spending=21619499,financial=-876057,primary=-149297,interest=726760,capital=971008,personnel=9069150,pensions=4204316,own_tax=8362281,national_tax=7507420,municipal_current_transfers=2774742)],methodology='Importes corrientes del cuadro de la página 13. Comparación entre primeros semestres; no reemplaza el ranking común al 1T26. El RON presupuestario no es el mismo total bruto de distribución automática del registro nacional. Diferencias de componentes de hasta $1 millón por redondeo.')
 for r in latest['rows']:
  assert r['income']-r['spending']==r['financial'];assert r['financial']+r['interest']==r['primary']
  r.update(financial_pct=100*r['financial']/r['income'],primary_pct=100*r['primary']/r['income'],capital_pct=100*r['capital']/r['spending'])
 save('data/pba_execution_latest.json',latest)
 universe=monthly.manifest_universe();top,tc=monthly.import_top(cache/'top-latest.xlsx',universe);ron,rc=monthly.import_ron(cache/'ron-latest.xlsx',universe)
 monthly.write_csv(monthly.TOP_OUTPUT,list(top[0]),top);monthly.write_csv(monthly.RON_OUTPUT,list(ron[0]),ron)
 monthly.write_pba_files(top,ron,cache/'top-latest.xlsx',cache/'ron-latest.xlsx');monthly.write_canonical_files(top,ron,tc,rc,universe);monthly.update_manifest(tc,rc,universe)
 meta=read('data/meta.json');meta['sources']['pba_debt_service_schedule'].update(url=debt_url,valuation_date='2026-06-30',period='Julio–diciembre 2026 y años 2027–2041');meta['sources']['pba_execution_latest']=latest['source'];save('data/meta.json',meta)
 manifest=read('dashboard_manifest.json');manifest['as_of_by_block'].update(debt_stock_pba='2026-06-30',debt_currency_composition_pba='2026-06-30',debt_service_schedule_pba='2026-06-30',execution_pba='2026-06-30');manifest['files']['pba_execution_latest']='data/pba_execution_latest.json';manifest['notes']['debt_schedule_scope']='PBA: julio–diciembre de 2026 y años completos 2027–2041, valuados al 30/06/2026. El documento no contiene una apertura mensual.';save('dashboard_manifest.json',manifest)
 school_rows=list(csv.DictReader((cache/'schools.csv').read_text(encoding='utf-8-sig').splitlines()));counts=Counter(r['tipo'] for r in school_rows);assert len({r['establecimiento_id'] for r in school_rows})==len(school_rows)
 school_metadata=json.loads((cache/'school-metadata.json').read_text(encoding='utf8'));resource=next(r for r in school_metadata['resources'] if r['url'].endswith('.csv'))
 pba=read('data/government_results_pba.json');pillar=next(p for p in pba['pillars'] if p['id']=='infrastructure');n=len(school_rows);created=counts['Creación'];replaced=counts['Sustitución'];assert n==created+replaced
 for m in pillar['metrics']:m.update(value=n,period='actualizado el 09/09/2026',source_url=resource['url'])
 pillar['metrics'][0].update(display=f'{n} edificios',interpretation=f'Incluye {created} creaciones y {replaced} sustituciones. Es el acumulado del registro, no obras realizadas sólo en 2026.')
 pillar['metrics'][1]['display']=f'{created} / {replaced}';pba['generated_at']='2026-09-15';pba['school_source_sha256']=hashlib.sha256((cache/'schools.csv').read_bytes()).hexdigest();save('data/government_results_pba.json',pba)
 print('PBA TOP',max(tc['Buenos Aires']),'RON',max(rc['Buenos Aires']),'school',n,counts)
 # Audit unchanged annual figures against the re-downloaded official workbook.
 d=pd.read_excel(cache/'annual-apnf.xlsx',sheet_name='Buenos Aires',header=None);a=next(r for r in read('data/annual_fiscal_accounts.json')['rows'] if r['province']=='Buenos Aires' and r['year']==2025);col=next(c for c in d.columns if d.iloc[8,c]==2025)
 from scripts_import_report_sources import FIELDS
 for field,row in FIELDS.items():assert abs(float(d.iloc[row,col])-a[field])<.02,(field,d.iloc[row,col],a[field])
 print('Annual PBA: all 16 fields reconciled with current official source.')
if __name__=='__main__':refresh(Path(sys.argv[1]))

"""Append official PBA 2025 revenue; keep the existing historical series intact."""
import csv,json,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
def main(source):
 path=ROOT/'serie_top_1984_2024_normalizado.csv'
 with path.open(encoding='utf8',newline='') as f:rows=list(csv.DictReader(f))
 added=[]
 for tax in ['Automotores','Ingresos Brutos','Inmobiliario','Otros','Sellos','Total']:
  sheet=pd.read_excel(source,sheet_name=tax,header=None)
  row=next(i for i in sheet.index if str(sheet.iloc[i,1]).strip()=='Buenos Aires')
  col=lambda year:next(c for c in sheet.columns if sheet.iloc[7,c]==year)
  previous=next(r for r in rows if r['province']=='Buenos Aires' and r['tax']==tax and r['year']=='2024')
  assert abs(float(previous['value_millions'])-float(sheet.iloc[row,col(2024)]))<.02
  added.append(dict(province='Buenos Aires',source='serie_top_1984_2025_0.xlsx',year='2025',tax=tax,value_millions=float(sheet.iloc[row,col(2025)])))
 assert abs(sum(r['value_millions'] for r in added if r['tax']!='Total')-next(r['value_millions'] for r in added if r['tax']=='Total'))<.02
 rows=[r for r in rows if not(r['province']=='Buenos Aires' and r['year']=='2025')]+added
 with path.open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 mpath=ROOT/'dashboard_manifest.json';m=json.loads(mpath.read_text(encoding='utf8'));m['as_of_by_block']['debt_service_schedule_pba']='2026-06-30';m['as_of_by_block']['historical_own_revenue_pba']='2025';m['notes']['debt_schedule_scope']='PBA: julio–diciembre de 2026 y años completos 2027–2041, valuados al 30/06/2026. El documento no contiene una apertura mensual.'
 mpath.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 p=ROOT/'data/meta.json';m=json.loads(p.read_text(encoding='utf8'));m['sources']['historical_own_revenue_pba']={'url':'https://www.argentina.gob.ar/sites/default/files/serie_top_1984_2025_0.xlsx','period':'1984–2025','scope':'Ampliación PBA 2025; las restantes provincias conservan la serie histórica previa.'};p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PBA 2025: six taxes/total reconciled; prior 2024 cells match; historical rows preserved.')
if __name__=='__main__':main(Path(sys.argv[1]))

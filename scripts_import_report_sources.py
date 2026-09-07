"""Import official annual accounts and the missing 2025 RON comparison base.

Usage: python scripts_import_report_sources.py CACHE_DIR
Cache must contain the two files specified in SOURCES. No originals are edited.
"""
import csv, hashlib, json, sys
from pathlib import Path
import pandas as pd
from scripts_regenerate_2026 import import_ron

ROOT = Path(__file__).resolve().parent
SOURCES = {
 'serie_aif-apnf-2025.xlsx': 'https://www.argentina.gob.ar/sites/default/files/serie_aif-apnf-2025.xlsx',
 'informacion_consolidada2025_5.xlsx': 'https://www.argentina.gob.ar/sites/default/files/informacion_consolidada2025_5.xlsx',
}
FIELDS = {'income':48,'spending':49,'financial':50,'primary':51,'primary_spend':52,
 'personnel':26,'pensions':30,'current_transfers':31,'capital':41,'direct_investment':42,
 'capital_transfers':43,'financial_investment':47,'national_tax':12,'provincial_tax':11,'royalties':19}

def build(cache):
 universe=json.loads((ROOT/'data/government_results_provinces.json').read_text(encoding='utf-8'))['province_universe']
 path=cache/'serie_aif-apnf-2025.xlsx';book=pd.ExcelFile(path);rows=[]
 for province in universe:
  sheet={'CABA':'Ciudad','Santiago del Estero':'Santiago del  Estero'}.get(province,province)
  df=pd.read_excel(book,sheet_name=sheet,header=None)
  assert 'NO FINANCIERA' in ' '.join(str(x) for x in df.iloc[:8,0])
  for col in range(1,len(df.columns)):
   year=df.iloc[8,col]
   if pd.isna(year):continue
   year=int(year);income=df.iloc[48,col];spending=df.iloc[49,col]
   # The official series encodes La Pampa's unavailable 2025 column as zeros.
   missing=pd.isna(income) or pd.isna(spending) or (income==0 and spending==0)
   values={key:None if missing or pd.isna(df.iloc[idx,col]) else float(df.iloc[idx,col]) for key,idx in FIELDS.items()}
   rows.append(dict(province=province,year=year,scope='APNF',status='missing' if missing else 'observed',
    basis='compromiso' if province=='Santiago del Estero' and year==2025 else 'devengado',
    source_sheet=sheet,source_column=col+1,**values))
 out=dict(reviewed_at='2026-09-06',unit='ARS millions',source_url=SOURCES[path.name],
  source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_rows={k:i+1 for k,i in FIELDS.items()},
  methodology='APNF: Administración Pública no Financiera. Ingresos percibidos y gastos devengados; Santiago del Estero 2025 informa compromiso. Datos provisorios, versión única de la serie DNAP. La Pampa 2025 no está disponible; sus ceros de origen se preservan como faltantes. No se calculan variaciones reales a partir de totales anuales sin apertura mensual.',rows=rows)
 (ROOT/'data/annual_fiscal_accounts.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n',encoding='utf-8')
 path=cache/'informacion_consolidada2025_5.xlsx';ron,coverage=import_ron(path,universe,2025)
 assert all(len(coverage[p])==12 for p in universe)
 with (ROOT/'informacion_consolidada_2025_normalizado.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(ron[0]),lineterminator='\n');writer.writeheader();writer.writerows(ron)
 audit=dict(reviewed_at='2026-09-06',source_url=SOURCES[path.name],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
  coverage=coverage,method='Se importa cada hoja mensual con los mismos clasificadores de 2026. Para totales se usa solo Total (1)+(2), sin sumar nuevamente sus componentes. IPC observado nacional, mes a mes.',rows=len(ron))
 (ROOT/'data/ron_2025_import.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'Annual observations: {len(rows)}; RON 2025: {len(ron)} rows, 24 provinces x 12 months.')

if __name__=='__main__':build(Path(sys.argv[1]))

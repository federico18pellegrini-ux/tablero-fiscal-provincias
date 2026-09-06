"""Build numerical fiscal history from audited extraction CSV. No PDFs distributed.
Usage: python scripts_build_fiscal_history.py extraction.csv
Values: ARS millions, rolling twelve months, as originally published.
"""
import csv
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
ALIASES = {'S. del Estero':'Santiago del Estero','T. Fuego':'Tierra del Fuego','PBA':'Buenos Aires','Cordoba':'Córdoba','Neuquen':'Neuquén','Entre Rios':'Entre Ríos','Tucuman':'Tucumán','Rio Negro':'Río Negro','Sgo del Estero':'Santiago del Estero','Sgo. del Estero':'Santiago del Estero','T. del Fuego':'Tierra del Fuego'}
FIELDS = 'tax royalties national_tax social_income other_income income personnel current_transfers capital social_spend other_spend primary_spend primary interest_signed financial'.split()
def build(source):
    rows=[]
    for raw in csv.DictReader(source):
        v={k:int(raw[k]) for k in FIELDS}
        residuals=[sum(v[k] for k in FIELDS[:5])-v['income'],sum(v[k] for k in FIELDS[6:11])-v['primary_spend'],v['income']-v['primary_spend']-v['primary'],v['primary']+v['interest_signed']-v['financial']]
        if max(map(abs,residuals))>2 or v['income']<=0:raise ValueError('Fiscal identity failed')
        p=raw['period']
        v.update(province=ALIASES.get(raw['province_source'],raw['province_source']),period=f'20{p[-2:]}-Q{p[0]}',publication_date=raw['publication_date'],source_title=f'1816 · Informe fiscal provincias {p}',source_page=8,primary_pct=100*v['primary']/v['income'],financial_pct=100*v['financial']/v['income'])
        rows.append(v)
    keys=[(r['province'],r['period']) for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate province-period')
    return {'schema_version':1,'unit':'ARS millions','frequency':'rolling_12_months','vintage_policy':'Valores publicados en cada informe; las revisiones pueden afectar las variaciones.','source':'1816, compilación de ejecuciones fiscales provinciales.','rows':sorted(rows,key=lambda r:(r['period'],r['province']))}
if __name__=='__main__':
    with open(sys.argv[1],encoding='utf-8-sig',newline='') as source:payload=build(source)
    (ROOT/'data/fiscal_history.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f"Validated {len(payload['rows'])} observations")

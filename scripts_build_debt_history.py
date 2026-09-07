"""Extract debt stocks and structural ratios from supplied fiscal reports.
Usage: python scripts_build_debt_history.py /path/to/reports
Requires pdfplumber. Never distributes source PDFs or converts currencies.
"""
import json,re,sys,hashlib
from pathlib import Path
from scripts_build_fiscal_history import ALIASES

def extract_report(path):
    import pdfplumber
    label=re.search(r'Provincias (\d)T(\d{2})',path.name)
    if not label:raise ValueError(f'Unknown period: {path.name}')
    period=f'20{label[2]}-Q{label[1]}'
    with pdfplumber.open(path) as pdf:
        debt_text=pdf.pages[20].extract_text()
        currency='USD' if 'millones de Dólares' in debt_text else 'ARS' if 'millones de Pesos' in debt_text else None
        if currency is None:raise ValueError(f'Unknown debt unit: {period}')
        ratios={}
        for line in pdf.pages[22].extract_text().splitlines():
            match=re.match(r'^(.+?)\s+(\d+)\s+(-?\d+,\d+%.*)$',line)
            if not match:continue
            vals=re.findall(r'(-?\d+,\d+)%',match[3])
            if len(vals)!=7:raise ValueError(f'Expected seven ratios: {period} {line}')
            ratios[ALIASES.get(match[1],match[1])]=dict(zip(['salary_share_ex_ss','capital_share_ex_ss','autonomy_ex_ss','iibb_own_share','debt_income_pct','market_debt_share','financial_pct'],[float(v.replace(',','.')) for v in vals]))
        rows=[]
        for line in debt_text.splitlines():
            match=re.match(r'^(.+?)\s+(\d[\d.]*(?:\s+\d[\d.]*){5})\s+\D',line)
            if not match or match[1]=='TOTAL':continue
            province=ALIASES.get(match[1],match[1]);values=[int(v.replace('.','')) for v in match[2].split()]
            if abs(values[0]-sum(values[1:]))>2:raise ValueError(f'Debt reconciliation failed: {period} {province}')
            row=dict(zip(['total','bonds','nation','multilateral','banks','consolidated'],values))
            row.update(province=province,period=period,currency=currency,unit='millions',source_title=f'Informe fiscal provincias {label[1]}T{label[2]}',source_page=21,ratio_source_page=23,publication_date=path.name[:10],ratios=ratios.get(province))
            rows.append(row)
        if not 20<=len(rows)<=24:raise ValueError(f'Unexpected row count: {period}: {len(rows)}')
        return rows,{'period':period,'currency':currency,'debt_rows':len(rows),'ratio_rows':len(ratios),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

if __name__=='__main__':
    rows=[];reports=[]
    for path in sorted(Path(sys.argv[1]).glob('*.pdf')):
        batch,report=extract_report(path);rows.extend(batch);reports.append(report)
    if len({(r['province'],r['period']) for r in rows})!=len(rows):raise ValueError('Duplicate observations')
    payload={'schema_version':1,'method':'Stock in original currency and unit; debt/income ratios as published. No currency conversion or missing-value imputation.','rows':rows,'reports':reports}
    (Path(__file__).parent/'data/debt_history.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'rows':len(rows),'reports':reports},ensure_ascii=False))

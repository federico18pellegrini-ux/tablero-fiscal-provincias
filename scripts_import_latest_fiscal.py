"""Extract quarterly balances and debt from the 1T26 report supplied locally.
Usage: python scripts_import_latest_fiscal.py report.pdf
Requires pdfplumber. Layout and PBA controls deliberately fail on new layouts.
"""
import json,re,sys
from pathlib import Path
from scripts_build_fiscal_history import ALIASES
def extract(path):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        p=pdf.pages[5]
        words=p.extract_words()
        names={}
        for w in words:
            if 325<w['top']<398 and w['x0']>105 and '%' not in w['text']:
                names.setdefault(round(w['x0'],1),[]).append(w['text'][::-1])
        ordered=[]
        for x,parts in sorted(names.items()):
            n=' '.join(reversed(parts));ordered.append(ALIASES.get(n,n))
        values=[float(w['text'][::-1].replace('%','').replace(',','.')) for w in sorted(words,key=lambda w:w['x0']) if '%' in w['text'] and w['x0']>105 and w['top']>p.height*.55]
        if len(ordered)!=23 or len(values)!=46:raise ValueError('Quarter chart layout changed')
        quarters={name:{'primary_pct':values[i*2],'financial_pct':values[i*2+1]} for i,name in enumerate(ordered)}
        if quarters.get('Buenos Aires')!={'primary_pct':1.7,'financial_pct':-3.9}:raise ValueError('PBA quarter control failed')
        debt={};text=pdf.pages[20].extract_text()
        if 'millones de Dólares' not in text:raise ValueError('Debt currency/unit changed')
        for line in text.splitlines():
            m=re.match(r'^(.+?)\s+(\d[\d.]*(?:\s+\d[\d.]*){5})\s+\D',line)
            if not m or m[1]=='TOTAL':continue
            n=ALIASES.get(m[1],m[1]);v=[int(x.replace('.','')) for x in m[2].split()]
            if abs(v[0]-sum(v[1:]))>2:raise ValueError('Debt components do not reconcile')
            debt[n]=dict(zip(['total','bonds','nation','multilateral','banks','consolidated'],v))
        if len(debt)!=23:raise ValueError('Incomplete debt extraction')
        return {'period':'2026-Q1','source':'1816, Informe fiscal provincias 1T26','quarter_source_page':6,'debt_source_page':21,'debt_unit':'USD millions, translated at quarter-end official exchange rate','quarters':quarters,'debt':debt}
if __name__=='__main__':
    result=extract(sys.argv[1]);(Path(__file__).parent/'data/fiscal_latest_details.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8');print('23 quarterly results and 23 debt compositions validated')

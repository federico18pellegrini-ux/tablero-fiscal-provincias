"""Integra impuestos provinciales verificados sin imputar rubros ausentes."""
import csv, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
TAXES={'Iibb','Inmobiliario','Automotores','Sellos','Otros'}

def observations():
    return json.loads((ROOT/'data/provincial_recent_sources_review.json').read_text(encoding='utf8'))['observations']

def verified_subtotal(province,period,taxes):
    for item in observations():
        if (item['province'],item['period'])!=(province,period):continue
        expected={k:v/1e6 for k,v in item.items() if k in TAXES}
        if set(taxes)!=set(expected):return None
        if any(abs(taxes[k]-v)>.000001 for k,v in expected.items()):return None
        return sum(expected.values())
    return None

def read(name):
    with (ROOT/name).open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))

def write(name,rows):
    with (ROOT/name).open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def build():
    normalized=read('top_mensual_2026_normalizado.csv');canonical=read('data/recaudacion_propia.csv');coverage=read('data/cobertura.csv')
    for item in observations():
        source=ROOT/Path(item['source_file'].replace('\\','/'))
        assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
        for tax in sorted(TAXES & item.keys()):
            value=item[tax]/1e6
            key=(item['province'],item['period'],tax)
            for rows in [normalized,canonical]:
                prior=[r for r in rows if (r['province'],r['period'],r['tax'])==key]
                assert not prior or (len(prior)==1 and abs(float(prior[0]['value_millions'])-value)<1e-6)
            if not any((r['province'],r['period'],r['tax'])==key for r in normalized):
                normalized.append(dict(province=key[0],source=source.name,year=2026,period_type='month',period=key[1],tax=tax,value_millions=value))
                canonical.append(dict(province=key[0],period=key[1],tax=tax,value_millions=value,price_basis='pesos_corrientes',evidence_status='auditado',source_file=source.name,source_url=item['source_url']))
        for r in coverage:
            if r['dataset']=='recaudacion_propia_2026' and r['province']==item['province']:
                periods={r['period'] for r in normalized if r['province']==item['province']}
                r.update(last_period=max(periods),months_count=len(periods),coverage_status='completa' if max(periods)==r['expected_through'] else 'rezagada')
    for name,rows in [('top_mensual_2026_normalizado.csv',normalized),('data/recaudacion_propia.csv',canonical)]:
        write(name,sorted(rows,key=lambda r:(r['province'],r['period'],r['tax'])))
    write('data/cobertura.csv',coverage)
    meta_path=ROOT/'data/meta.json'
    meta=json.loads(meta_path.read_text(encoding='utf8'))
    meta['sources']['recaudacion_propia_provincial_supplement']={'file':'data/provincial_recent_sources_review.json','provinces':sorted({r['province'] for r in observations()}),'period':'2026-09'}
    meta['rules']['top_reconciliation']='DNAP: total mensual reconciliado con cinco componentes. Suplementos provinciales: conjunto exacto de impuestos provinciales verificados, sin ingresos no tributarios ni imputación de rubros ausentes.'
    meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    data=json.loads((ROOT/'data/ipc_san_luis_2014_2016_review.json').read_text(encoding='utf8'))
    source=ROOT/Path(data['source_file'].replace('\\','/'))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==data['sha256']
    indices={r['period']:r['index_base_2003'] for r in data['observations']}
    assert len(indices)==36
    path=ROOT/'index.html';html=path.read_text(encoding='utf8')
    match=re.search(r'const DEFLACTOR_MONTH = (\{.*?\});',html)
    factors=json.loads(match[1]);anchor=factors['2016-12']
    for period,index in indices.items():
        if period<'2016-12':factors[period]=anchor*indices['2016-12']/index
    historical={k:v for k,v in sorted(factors.items()) if k<'2016-12'}
    constant='const HISTORICAL_DEFLATOR = '+json.dumps(historical)+';'
    if 'const HISTORICAL_DEFLATOR = ' in html:
        html=re.sub(r'const HISTORICAL_DEFLATOR = \{.*?\};',constant,html)
    else:
        html=html.replace('const DISPLAY_REBASE_FACTOR =',constant+'\nconst DISPLAY_REBASE_FACTOR =')
    path.write_text(html,encoding='utf8')

if __name__=='__main__':build()

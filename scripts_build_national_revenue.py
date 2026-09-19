"""Reconcile observed monthly revenue and isolate BCRA profits before forecasting."""
import argparse,csv,hashlib,io,json,zipfile
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'nacion/data/revenue-planning.json'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def build():
    source_list=load(ROOT/'nacion/data/gestion/fuentes.json')
    ipc={x['periodo']:x['factor_a_agosto_2026'] for x in load(ROOT/'nacion/data/gestion/ipc_observado.json')}
    types=defaultdict(Decimal); groups=defaultdict(Decimal); extras=defaultdict(Decimal); counts=defaultdict(int);sources=[]
    for year in [2025,2026]:
        name=f'recursos-mensual-{year}.zip';source=next(s for s in source_list if s['file']==name);p=ROOT/'nacion/data/revenue-sources'/name
        raw=p.read_bytes();assert len(raw)==source['bytes'] and hashlib.sha256(raw).hexdigest()==source['sha256']
        sources.append({**source,'path':'data/revenue-sources/'+name})
        with zipfile.ZipFile(p) as z:
            rows=list(csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig'))))
        for r in rows:
            period=f"{year}-{int(r['impacto_presupuestario_mes']):02d}";t=int(r['tipo_id']);value=Decimal(r['recurso_ingresado_percibido'].replace(',','.'))
            assert r['clasificador_economico_8_digitos_id'].startswith('1')
            types[(period,t)]+=value
            if year==2026 and period>'2026-08':continue
            bcra=(t,int(r['clase_id']),int(r['concepto_id']),int(r['subconcepto_id']))==(16,4,2,1)
            if bcra:
                assert 'Banco Central' in r['subconcepto_desc'];extras[period]+=value
            else:
                group={11:'tax',13:'social',16:'property'}.get(t,'other');groups[(period,group)]+=value;counts[(period,group)]+=1
    monthly=load(ROOT/'nacion/data/gestion/recursos_mensuales_tipo.json')
    assert set(types)=={(r['periodo'],r['tipo_id']) for r in monthly}
    for r in monthly:assert abs(float(types[(r['periodo'],r['tipo_id'])])-r['recurso_ingresado_percibido'])<.00001
    periods=[f'{y}-{m:02d}' for y,n in [(2025,12),(2026,8)] for m in range(1,n+1)]
    names={'tax':'Impuestos','social':'Aportes y contribuciones','property':'Rentas sin utilidades del BCRA','other':'Otros ingresos corrientes y de capital'}
    result=[]
    for period in periods:
        assert all(counts[(period,k)]>0 for k in names),period
        values=[{'id':k,'name':name,'nominal':float(groups[(period,k)]),'real':float(groups[(period,k)])*ipc[period]} for k,name in names.items()]
        total=sum(x['nominal'] for x in values)+float(extras[period]);expected=sum(r['recurso_ingresado_percibido'] for r in monthly if r['periodo']==period)
        assert abs(total-expected)<.00001
        result.append({'period':period,'groups':values,'bcra':float(extras[period]),'total':total})
    return {'reviewed':'2026-09-18','cutoff':'2026-08','unit':'ARS millones; reales a agosto 2026','scope':'Administración Nacional, ingresos presupuestarios percibidos, incluidos recursos de capital; no es caja SPN','sources':sources,'inputs':{name:digest(ROOT/name) for name in ['nacion/data/gestion/recursos_mensuales_tipo.json','nacion/data/gestion/ipc_observado.json']},'bcra_code':{'tipo':16,'clase':4,'concepto':2,'subconcepto':1},'months':result}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();d=build()
    if a.check:assert d==load(OUT)
    else:OUT.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print('20 meses conciliados; BCRA separado por código presupuestario; septiembre parcial excluido.')

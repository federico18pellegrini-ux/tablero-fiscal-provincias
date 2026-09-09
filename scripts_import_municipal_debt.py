"""Validate public CEC/FES aggregates; never fetch or reconstruct personal records."""
import argparse
import hashlib
import json
import math
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = 'https://datos.mapadeladeuda.ar/v3/'

def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.lower()) if not unicodedata.combining(c))

def build(folder):
    data = json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
    municipalities = {m['id']:m for m in data['municipalities']}
    payload = json.loads((folder/'debt-municipal.json').read_text(encoding='utf-8'))
    index = json.loads((folder/'debt-index.json').read_text(encoding='utf-8'))
    geography = {g['geo_id']:g for g in json.loads((folder/'debt-geo.json').read_text(encoding='utf-8'))['features']}
    period = payload['period']
    assert payload['level']=='municipio' and payload['scope']=='06' and not payload['filters'] and not payload['activeFilters']
    source = next(s for s in index['availableSlices'] if s['level']=='municipio' and s['scope']=='06' and not s['filters'])
    assert source['geographies']==len(payload['rows'])==135 and index['period']==period
    for field in ['monto_total','monto_mora']:
        assert payload['metrics'][field]['format']=='currency_thousands'
    records=[]
    for line,row in enumerate(payload['rows'],1):
        raw = {payload['aliases'].get(k,k):v for k,v in zip(payload['columns'],row)}
        geo = geography[raw['geo_id']]
        assert geo['level']=='municipio' and geo['scope']=='06'
        ident = '06'+raw['geo_id'][-3:]
        assert ident in municipalities
        expected = 'Coronel de Marina Leonardo Rosales' if ident=='06182' else municipalities[ident]['municipio']
        assert normalized(geo['nombre'])==normalized(expected)
        values=[raw[k] for k in ['deudores_unicos_total','deudores_unicos_mora','monto_total','monto_mora']]
        assert all(type(v) in [float,int] and math.isfinite(v) and v>=0 for v in values)
        people,late,total,overdue=values
        # Never expose suppressed small cells as zeros or reconstruct them.
        assert people>=5 and late>=5 and late<=people and overdue<=total and total>0
        assert abs(raw['tasa_mora']-100*overdue/total)<.000001
        assert abs(raw['ticket_promedio']-total/people)<.000001
        records.append({'id':ident,'municipality':municipalities[ident]['municipio'],'period':period,
            'peopleWithDebt':people,'peopleInArrears':late,'peopleInArrearsPct':100*late/people,
            'debtARS':total*1000,'debtInArrearsARS':overdue*1000,'debtInArrearsPct':raw['tasa_mora'],
            'averageDebtARS':total*1000/people,'sourceRow':line,'sourceGeography':geo,'sourceRecord':raw})
    assert {r['id'] for r in records}==set(municipalities)
    for field in ['deudores_unicos_total','deudores_unicos_mora','monto_total','monto_mora']:
        assert sum(r['sourceRecord'][field] for r in records)==payload['kpis'][field]
    evidence=[]
    for file,path in [('debt-municipal.json',source['path']),('debt-index.json',f'periods/{period}/index.json'),('debt-geo.json','geo/lookup.json'),('debt-manifest.json','manifest.json')]:
        raw=(folder/file).read_bytes()
        evidence.append({'file':file,'url':BASE+path,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    result={'provider':'CEC / FES, Mapa de la Deuda, sobre Central de Deudores del BCRA','url':'https://mapadeladeuda.ar/',
        'verifiedAt':'2026-09-09','period':period,'classification':'Relevamiento externo; asignación territorial según CEC/FES',
        'verificationScope':'Identidades geográficas publicadas, unidades, filtros y conciliación de agregados; no se verificaron domicilios individuales ni se reconstruyó el proceso territorial del proveedor.',
        'universe':'Personas físicas con deuda informada; todas las entidades, edades y géneros. Excluye SGR y FGCP según la fuente.',
        'arrears':'Situaciones 3, 4 y 5 según el relevamiento; no incluye todos los atrasos de hasta 90 días.',
        'populationDenominator':False,'sources':evidence,'provincialTotals':payload['kpis'],'municipalities':records}
    (ROOT/'municipios/data/debt_cec.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'coverage':len(records),'period':period,'lasHeras':next({k:v for k,v in r.items() if not k.startswith('source')} for r in records if r['id']=='06329')},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input-dir',type=Path,required=True);build(parser.parse_args().input_dir)

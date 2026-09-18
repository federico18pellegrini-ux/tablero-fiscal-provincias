"""Extract original amendment tables, map documented codes, reconcile each act."""
import argparse,csv,hashlib,io,json,re,zipfile
from collections import defaultdict
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parent
FOLDER=ROOT/'nacion/data/act-sources'
OUT=ROOT/'nacion/data/acts.json'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def amount(s):return 0 if s=='-' else int(s.replace('.','').replace('(','-').replace(')',''))
def da(source):
    rows=[]
    for i,p in enumerate(pymupdf.open(FOLDER/source['file'])):
        if 'Detalle por Finalidades del Gasto y Programa Presupuestario' not in p.get_text():continue
        words=p.get_text('words');width=p.rect.width
        for anchor in words:
            if not (.018*width<anchor[0]<.035*width and re.fullmatch(r'\d{3}',anchor[4])):continue
            same=[w for w in words if abs((w[1]+w[3]-anchor[1]-anchor[3])/2)<(anchor[3]-anchor[1])*.3]
            prog=[w for w in same if .13*width<w[0]<.174*width and w[4].isdigit()]
            assert len(prog)==1,(source['id'],i+1,'program',anchor[4])
            other=prog[0][0]/width<.15
            values=[w for w in same if (.29 if other else .30)*width<w[0]<(.36 if other else .39)*width and re.fullmatch(r'[-\d.()]+',w[4]) and ('.' in w[4] or w[4]=='-')]
            assert len(values)==1,(source['id'],i+1,'value',anchor[4])
            rows.append({'saf':int(anchor[4]),'program':int(prog[0][4]),'pesos':amount(values[0][4]),'page':i+1,'article':'otras normas' if other else 'artículo 37'})
    return rows
def dnu(source,mapping):
    rows=[]
    for i,p in enumerate(pymupdf.open(FOLDER/source['file'])):
        text=p.get_text(sort=True)
        if 'CREDITOS (GASTOS CORRIENTES Y DE CAPITAL)' not in text:continue
        total=re.search(r'TOTAL PROGRAMA\s+(-?[\d.]+)',text)
        if not total:continue
        def field(name,default=None):
            m=re.search(name+r'\s*:\s*(\d+)',text)
            assert m or default is not None,(source['id'],i+1,name)
            return int(m[1]) if m else default
        entity=field('Entidad',0)
        if entity:
            candidates=[k for k in mapping if k[0]==field('Jurisdicción') and k[2]==entity and k[3]==field(r'\n Programa')]
            assert len(candidates)==1,(source['id'],i+1,candidates)
            key=candidates[0]
        else:key=(field('Jurisdicción'),field('Sub-Jurisdicción'),0,field(r'\n Programa'))
        assert key in mapping,(source['id'],i+1,key)
        rows.append({'jurisdiction':key[0],'subjurisdiction':key[1],'entity':key[2],'saf':mapping[key],'program':key[3],'pesos':amount(total[1]),'page':i+1,'article':'artículo 1'})
    return rows
def build():
    sources=load(FOLDER/'sources.json')
    for s in sources:
        raw=(FOLDER/s['file']).read_bytes();assert len(raw)==s['bytes'] and hashlib.sha256(raw).hexdigest()==s['sha256'],s['file']
    mapping={}
    with zipfile.ZipFile(FOLDER/'credito-anual-2026.zip') as z:
        for r in csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode('utf-8-sig'))):
            key=tuple(int(r[k]) for k in ['jurisdiccion_id','subjurisdiccion_id','entidad_id','programa_id']);saf=int(r['servicio_id'])
            assert key not in mapping or mapping[key]==saf;mapping[key]=saf
    stages=load(ROOT/'nacion/data/gestion/gasto_etapas_programa.json');lookup={(r['servicio_id'],r['programa_id']):r for r in stages}
    assert len(lookup)==len(stages)
    official=load(ROOT/'nacion/data/management-sources/evidence.json')['modifications']['acts']
    acts=[]
    for act in official:
        source=next(s for s in sources if s['id']==act['id']);rows=da(source) if act['id'].startswith('da') else dnu(source,mapping)
        total=sum(r['pesos'] for r in rows)/1e6
        assert abs(total-act['spending_ars_millions'])<=.5,(act['id'],total)
        linked=[]
        for row in rows:
            key=(row['saf'],row['program'])
            if key not in lookup:
                if row['pesos']==0:continue # Financing applications outside this expenditure scope.
                # DA 26, page 2: official labels survive even where the current code does not.
                names={(322,54):'Deporte Comunitario y Competencias',(322,55):'Deporte Federado e Iniciación Deportiva'}
                linked.append({**row,'jurisdiction':None,'name':names.get(key,f"Programa {row['program']}"),'entity_name':'Secretaría de Turismo y Ambiente' if key in names else f"SAF {row['saf']}",'millions':row['pesos']/1e6,'matched':False})
                continue
            s=lookup[key];linked.append({**row,'jurisdiction':s['jurisdiccion_id'],'name':s['programa_desc'],'entity_name':s['servicio_desc'],'millions':row['pesos']/1e6,'matched':True})
        assert sum(r['pesos'] for r in linked)==sum(r['pesos'] for r in rows)
        acts.append({**act,'source_url':source['url'],'source_path':'data/act-sources/'+source['file'],'exact_millions':total,'rows':linked})
    net=defaultdict(float)
    for act in acts:
        for r in act['rows']:net[(r['saf'],r['program'])]+=r['millions']
    balance=[{'saf':r['servicio_id'],'program':r['programa_id'],'name':r['programa_desc'],'entity_name':r['servicio_desc'],'net':r['credito_vigente']-r['credito_presupuestado'],'documented':net[(r['servicio_id'],r['programa_id'])],'residual':r['credito_vigente']-r['credito_presupuestado']-net[(r['servicio_id'],r['programa_id'])]} for r in stages]
    return {'reviewed':'2026-09-18','unit':'ARS millones corrientes','scope':'Gastos corrientes y de capital, sin figurativas ni aplicaciones financieras','mapping_note':'Códigos jurisdicción/subjurisdicción/entidad/programa de los decretos vinculados a SAF con el archivo PA actualizado al 16/09. Solo se usa su nomenclador; los saldos comparados conservan el corte 15/09.','sources':sources,'acts':acts,'program_balance':balance,'reconciliation':{'documented_net':sum(a['exact_millions'] for a in acts),'net':sum(r['net'] for r in balance),'remaining_net':sum(r['residual'] for r in balance),'reconciled_programs':sum(abs(r['residual'])<.00001 for r in balance),'total_programs':len(balance)}}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();result=build()
    if args.check:assert result==load(OUT),'Regenerar acts.json'
    else:OUT.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(result['reconciliation'])

import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def build():
    data=json.loads((ROOT/'dashboard_federal_fairness.json').read_text(encoding='utf-8'))
    rows=[]
    for name,p in data['provinces'].items():
        if name=='CABA':continue
        m=p['metrics'];population=m['population']['value'];pc=m['ron_per_capita_pesos']['value']
        if p['year']!=2025 or not isinstance(pc,(int,float)) or not isinstance(population,(int,float)) or population<=0:raise ValueError('Incomplete comparable universe')
        rows.append({'province':name,'population':population,'per_capita':pc})
    assert len(rows)==23
    return {'flow_period':'2025','population_period':'Censo 2022','scope':'23 provincias, sin CABA','simple_mean':statistics.mean(r['per_capita'] for r in rows),'median':statistics.median(r['per_capita'] for r in rows),'population_weighted_mean':sum(r['population']*r['per_capita'] for r in rows)/sum(r['population'] for r in rows),'unit':'Pesos corrientes de 2025 por habitante del Censo 2022','rows':rows,'source_files':['dashboard_federal_fairness.json','dashboard_federal_fairness_inputs.csv','serie_ron_2003_2025_normalizado.csv']}
if __name__=='__main__':(ROOT/'data/federal_benchmarks.json').write_text(json.dumps(build(),ensure_ascii=False,indent=2),encoding='utf-8')

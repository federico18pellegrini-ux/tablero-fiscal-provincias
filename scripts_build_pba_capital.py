"""Reconcile CGP capital by institution and direct investment by function.

CGP's function/object table mixes current and capital transfers. Never allocate
that mixed column to capital or confuse project costs with semester execution.
"""
import hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'data/pba_sources/cgp-1s'

def read_rows(path):
    soup=BeautifulSoup(path.read_bytes().decode('windows-1252'),'html.parser')
    return [[' '.join(c.get_text(' ',strip=True).split()) for c in t.find_all(['td','th'],recursive=False)] for t in soup.select('tr')]

def number(s):
    return float(s.replace('.','').replace(',','.')) if s else 0.

def economic(rows):
    result={}
    for row in rows:
        for label,key in [('GASTOS DE CAPITAL','capital'),('INVERSION REAL DIRECTA','direct'),('TRANSFERENCIAS DE CAPITAL','transfers'),('INVERSION FINANCIERA','financial')]:
            if label in row and key not in result: result[key]=number(row[row.index(label)+1])
    assert len(result)==4
    assert abs(result['capital']-sum(result[k] for k in ('direct','transfers','financial'))) < .04
    return result

def functions(rows):
    result=[];purpose=None
    for original in rows:
        row=original[:]
        if len(row)==11 and re.match(r'^[1-5]-',row[0]):purpose=row.pop(0)[0]
        # Parent function rows already contain their subfunctions: exclude children.
        if len(row)==10 and re.match(r'^\d0-',row[0]):
            result.append(dict(id=purpose+'-'+row[0][:2],name=row[0][3:].strip(),direct=number(row[5]),financial=number(row[7])))
    assert len(result)==28 and len({r['id'] for r in result})==28
    return result

def build():
    manifest=json.loads((SOURCE/'sources.json').read_text('utf8'))
    for s in manifest:
        assert hashlib.sha256((SOURCE/s['file']).read_bytes()).hexdigest()==s['sha256']
    ratio=json.loads((ROOT/'data/pba_comparison.json').read_text('utf8'))['semester_ipc_ratio']
    totals={};func={};org={};checks=[]
    for year in (2025,2026):
        totals[year]=economic(read_rows(SOURCE/f'{year}-APNF-Econ2.html'))
        func[year]=functions(read_rows(SOURCE/f'{year}-APNF-FinFun.html'))
        org[year]=[]
        for s in manifest:
            if s['year']==year and s['kind']=='Econ2' and s['id']!='APNF':
                rows=read_rows(SOURCE/s['file']);org[year].append(dict(id=s['id'],name=rows[3][0],**economic(rows)))
        for key in ('direct','financial'):
            diff=sum(r[key] for r in func[year])-totals[year][key]
            assert abs(diff)<.15,(year,key,diff)
            checks.append(dict(year=year,dimension='function',component=key,difference=diff))
        for key in ('capital','direct','transfers','financial'):
            diff=sum(r[key] for r in org[year])-totals[year][key]
            assert abs(diff)<.3,(year,key,diff)
            checks.append(dict(year=year,dimension='institution',component=key,difference=diff))
    def change(a,b):
        return dict(previous=a,current=b,previous_real=a*ratio,real_change=b-a*ratio,real_change_pct=(b/a/ratio-1)*100 if a else None)
    def compare(groups,keys):
        old={r['id']:r for r in groups[2025]};new={r['id']:r for r in groups[2026]}
        assert old.keys()==new.keys()
        return [dict(id=k,name=new[k]['name'],**{key:change(old[k][key],new[k][key]) for key in keys}) for k in new]
    data=dict(reviewed='2026-10-04',period='Enero–junio 2026 contra enero–junio 2025',unit='ARS millones',scope='Administración Pública No Financiera',basis='Devengado',semester_ipc_ratio=ratio,
        totals={k:change(totals[2025][k],totals[2026][k]) for k in totals[2025]},
        functions=compare(func,('direct','financial')),institutions=compare(org,('capital','direct','transfers','financial')),checks=checks,
        method='Montos nominales publicados por la CGP. El semestre 2025 se lleva a precios promedio del primer semestre de 2026 mediante IPC nacional promedio. Las diferencias de suma menores a $0,3 millones son redondeos de la fuente.',
        coverage={'institution_capital':'complete','function_direct_investment':'complete','function_financial_investment':'complete','function_capital_transfers':'not_separated_in_source','project_execution':'not_published_in_these_tables'},
        project_note='El mapa provincial permite identificar obras, pero su monto actualizado no informa cuánto se devengó en cada primer semestre. Falta esa serie comparable por proyecto para repartir el recorte obra por obra.',
        projects_url='https://mapainversionespba.minfra.gba.gob.ar/Mapview',sources=manifest)
    (ROOT/'data/pba_capital_detail.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PBA capital:',len(data['institutions']),'institutions;',len(data['functions']),'functions; 12 reconciliations passed')
if __name__=='__main__':build()

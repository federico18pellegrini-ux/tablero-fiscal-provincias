"""Build the two documented policy links and the complete official CAIF.

python scripts_build_national_decisions.py [--check]
Only archived official inputs are used; no fuzzy matches or estimated gaps.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from national_work_sources import build_works

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'nacion/data'
OUTPUT = DATA / 'decisions.json'
INPUTS = ['nacion/data/budget.json', 'nacion/data/gestion/gasto_etapas_programa.json',
          'nacion/data/gestion/metas_fisicas_trimestre_2.json', 'nacion/data/gestion/catalogo.json',
          'nacion/data/decision-sources/caif-2027.pdf', 'nacion/data/decision-sources/proyectos-2027.pdf',
          'nacion/data/decision-sources/inversion-1t26.pdf', 'nacion/data/gestion/obras_ejecucion_fisica_financiera.json']
POLICIES = [
    ('inmunizaciones', 'Vacunas e inmunizaciones', 'Prevención y Control de Enfermedades Transmisible e Inmunoprevenibles', 'Ministerio de Salud', (80, 310, 20)),
    ('educacion-superior', 'Universidades', 'Desarrollo de la Educación Superior', 'Secretaría de Educación', (88, 330, 26)),
]

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def digest(path):
    raw = path.read_bytes()
    return hashlib.sha256(raw.replace(b'\r\n', b'\n') if path.suffix == '.json' else raw).hexdigest()

def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s).lower() if not unicodedata.combining(c))

def near(a, b, tolerance=2):
    assert abs(a-b) <= tolerance, (a, b)

def parse_caif(path):
    rows, section, count = [], None, 0
    for line in PdfReader(path).pages[0].extract_text().splitlines():
        match = re.match(r'^(.+?)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+-?[\d.,]+)?\s*$', line.strip())
        if not match:
            continue
        label, a, b, _ = match.groups()
        major = re.match(r'^(XIII|XII|XI|VIII|VII|VI|IV|III|II|IX|X|V|I)\)\s*(.*)', label)
        if major:
            section, label = major.groups()
            count, key = 0, section
        else:
            assert section, label
            count += 1
            key = f'{section}.{count}'
        rows.append({'id': key, 'section': section, 'label': label.strip(), 'closing': int(a.replace('.', '')), 'project': int(b.replace('.', ''))})
    by = {r['id']: r for r in rows}
    assert len(rows) == len(by) and set('I II III IV V VI VII VIII IX X XI XII XIII'.split()) <= by.keys()
    for year in ['closing', 'project']:
        v = lambda key: by[key][year]
        near(v('I')-v('II'), v('III'))
        near(v('I')+v('IV'), v('VI'))
        near(v('II')+v('V'), v('VII'))
        near(v('VI')-v('VII'), v('VIII'))
        near(v('VIII')+v('IX')-v('X'), v('XI'))
        near(v('XI')+v('XII'), v('XIII'))
        for section in ['I', 'IV', 'V', 'XII', 'XIII']:
            near(sum(r[year] for r in rows if r['id'].startswith(section+'.')), v(section), 3)
        # Interest in pesos / foreign currency / other are children of II.2.
        near(sum(v('II.'+str(i)) for i in [1,2,6,7,8,9]),v('II'),3)
        near(v('II.3')+v('II.4')+v('II.5'),v('II.2'),2)
    return rows

def build():
    b = load(DATA/'budget.json')
    stages = load(DATA/'gestion/gasto_etapas_programa.json')
    metas = load(DATA/'gestion/metas_fisicas_trimestre_2.json')
    catalog = {x['dataset']: x for x in load(DATA/'gestion/catalogo.json')}
    inputs = {p: digest(ROOT/p) for p in INPUTS}
    source = next(s for s in b['sources'] if s['file']=='cap1cu01.pdf')
    assert inputs['nacion/data/decision-sources/caif-2027.pdf'] == source['sha256'], 'CAIF differs from the verified project source'
    caif = parse_caif(DATA/'decision-sources/caif-2027.pdf')
    by = {r['id']: r for r in caif}
    near(by['VII']['project'],b['total']['project'],0)
    near(by['VII']['closing'],b['total']['closing'],0)
    near(by['VI']['project'],b['resources_total'],0)
    policies = []
    for slug, title, name, entity, key in POLICIES:
        matches = [p for p in b['programs'] if fold(p['name'])==fold(name) and fold(p['entity'])==fold(entity)]
        assert len(matches)==1 and matches[0]['matched'], slug
        program = matches[0]
        keys = lambda r: tuple(r[k] for k in ['jurisdiccion_id','servicio_id','programa_id'])
        execution = [r for r in stages if keys(r)==key]
        assert len(execution)==1, slug
        execution = execution[0]
        assert fold(execution['programa_desc'])==fold(name) and fold(execution['servicio_desc'])==fold(entity)
        for old, new in [('law','credito_presupuestado'),('current','credito_vigente'),('accrued','credito_devengado')]:
            near(program[old],execution[new],.01)
        physical = [r for r in metas if keys(r)==key]
        assert physical and all(r['ejercicio_presupuestario']==2026 and r['trimestre']==2 for r in physical)
        assert all(not r['requiere_revision_clave'] for r in physical), slug
        policies.append({'slug':slug,'title':title,'program':program,'execution':execution,'physical':physical,
            'link': {'jurisdiccion_id':key[0],'servicio_id':key[1],'programa_id':key[2],
                     'method':'Proyecto 2027 vinculado por denominación y organismo exactos; inicial, vigente y devengado 2026 conciliados. Ejecución y metas 2026 vinculadas por jurisdicción, SAF y programa.'},
            'sources': {'project':next(s for s in b['sources'] if s['file']==program['source']),
                        'execution':catalog['gasto_etapas_programa']['sources'][0],
                        'physical':catalog['metas_fisicas_trimestre_2']['sources'][0]}})
    work_sources={'project':next(s for s in b['sources'] if s['file']=='cap1pl12.pdf'),
                  'physical':catalog['obras_ejecucion_fisica_financiera']['sources'][0],
                  'investment':catalog['obras_ejecucion_fisica_financiera']['sources'][1]}
    assert inputs['nacion/data/decision-sources/proyectos-2027.pdf']==work_sources['project']['sha256']
    assert inputs['nacion/data/decision-sources/inversion-1t26.pdf']==work_sources['investment']['sha256']
    works=build_works(b,load(DATA/'gestion/obras_ejecucion_fisica_financiera.json'),DATA/'decision-sources/proyectos-2027.pdf',DATA/'decision-sources/inversion-1t26.pdf',work_sources)
    return {'meta':{'reviewed':'2026-09-18','unit':'ARS millones','execution_cutoff':b['meta']['execution_cutoff'],
                    'physical_period':'enero-junio 2026','inputs':inputs},
            'finance':{'scope':'Administración Nacional','base':'Cierre estimado 2026','project':'Proyecto de ley 2027',
                       'source':source,'page':1,'rows':caif}, 'policies':policies,'works':works}

def run(check=False):
    result = build()
    if check:
        assert load(OUTPUT)==result, 'Regenerar decisions.json'
    else:
        OUTPUT.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n',encoding='utf-8')
    print(f"Decisiones: {len(result['finance']['rows'])} renglones CAIF conciliados y dos políticas vinculadas.")

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)

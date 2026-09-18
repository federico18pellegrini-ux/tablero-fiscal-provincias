"""Official work funding columns and a deliberately reviewed RA-10 correspondence."""
import re
import unicodedata
import pymupdf
from pypdf import PdfReader

FUNDING = ['tesoro', 'propios', 'afectados', 'transferencias_internas', 'credito_interno',
           'internas', 'transferencias_externas', 'credito_externo', 'externas', 'total']
LABELS = ['Tesoro Nacional', 'Recursos propios', 'Recursos con destino específico', 'Transferencias internas',
          'Crédito interno', 'Fuentes internas', 'Transferencias externas', 'Crédito externo', 'Fuentes externas', 'Total']

def normalized(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower())

def funding_rows(path):
    rows=[]
    for page,pg in enumerate(pymupdf.open(path),1):
        lines=[]
        for block in pg.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                text=''.join(s['text'] for s in line['spans']).strip()
                x,y,_,_=line['bbox']
                if text and 203<=y<550:lines.append((y,x,text))
        groups=[]
        for y,x,text in sorted(lines):
            if not groups or abs(y-groups[-1][0])>2:groups.append([y,[]])
            groups[-1][1].append((x,text))
        for _,items in groups:
            label=[(x,s) for x,s in items if x<190]
            values=[int(s.replace('.','')) for x,s in items if x>=190 and re.fullmatch(r'-?[\d.]+',s)]
            if not label:continue
            name=' '.join(s for _,s in label)
            if values:
                assert len(values)==10,(page,name,values)
                rows.append({'name':name,'x':label[0][0],'funding':dict(zip(FUNDING,values)),'page':page})
            elif rows and not name.startswith('Nota:') and abs(label[0][0]-rows[-1]['x'])<2:rows[-1]['name']+=' '+name
    return rows

def build_works(budget,observed,project_pdf,investment_pdf,sources):
    parsed=funding_rows(project_pdf)
    total=next(r['funding'] for r in parsed if r['name']=='TOTAL')
    projects=[r for r in parsed if r['x']>=70]
    assert len(projects)==len(budget['works'])==435
    rows=[]
    for project,existing in zip(projects,budget['works']):
        assert normalized(project['name'])==normalized(existing['name']) and project['page']==existing['page']
        f=project['funding'];assert f['total']==existing['project']
        assert abs(sum(f[k] for k in FUNDING[:5])-f['internas'])<=2
        assert abs(f['transferencias_externas']+f['credito_externo']-f['externas'])<=1
        assert abs(f['internas']+f['externas']-f['total'])<=1
        rows.append({**existing,'funding':f})
    # Official rounded column totals are retained, never silently replaced by row sums.
    differences={k:sum(r['funding'][k] for r in rows)-total[k] for k in FUNDING}
    assert all(abs(x)<=12 for x in differences.values()),differences
    pilot=next(r for r in rows if normalized(r['name'])==normalized('Construcción de Reactor RA-10'))
    key=(50,105,20,0,22,51)
    keys=['jurisdiccion_id','servicio_id','programa_id','subprograma_id','proyecto_id','obra_id']
    matches=[r for r in observed if tuple(r[k] for k in keys)==key]
    assert len(matches)==1 and normalized(matches[0]['obra'])==normalized(pilot['name'])
    assert pilot['entity']=='Comisión Nacional de Energía Atómica (CNEA)' and pilot['province']=='Buenos Aires'
    assert len([r for r in rows if normalized(r['name'])==normalized(pilot['name'])])==1
    physical=matches[0]
    pdf=PdfReader(investment_pdf)
    table=pdf.pages[6].extract_text();detail=pdf.pages[7].extract_text()
    match=re.search(r'Construcción de Reactor RA-10\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',table)
    assert match and 'BAPIN' in table
    parse=lambda s:float(s.replace('.','').replace(',','.'))
    cost,previous,accrued=map(parse,match.groups())
    progress=parse(re.search(r'avance físico acumulado de\s+([\d,]+)%',detail[detail.index('Construcción Reactor'):]).group(1))
    assert abs(previous-physical['financiero_acumulado_2025_millones'])<.1
    assert abs(accrued-physical['devengado_1t2026_millones'])<.1
    assert abs(progress-(physical['avance_fisico_acumulado_2025_pct']+physical['ejecucion_fisica_1t2026_pct']))<.01
    return {'source':sources['project'],'columns':dict(zip(FUNDING,LABELS)),'rows':rows,'totals':total,
            'rounding_differences':differences,'pilot':{'slug':'reactor-ra10','title':'Reactor RA-10','project':pilot,
            'observed':physical,'progress_pct':progress,'reference_cost':cost,'updated_completion_cost':None,
            'completion_date':None,'operating_cost':None,'contract_commitments':None,
            'link':{'keys':dict(zip(keys,key)),'method':'Denominación y organismo revisados; una sola apertura territorial 2027 y una sola obra 2026. La planilla 2027 no publica códigos de obra.'},
            'sources':sources,'cost_page':7,'progress_page':8}}

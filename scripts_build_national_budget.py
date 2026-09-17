"""Build /nacion from archived ONP PDFs and Presupuesto Abierto CSVs.
Usage: python scripts_build_national_budget.py --cache PATH
See nacion/README.md for source acquisition and units. No reference-site data.
"""
import argparse, collections, csv, hashlib, json, re, unicodedata
from pathlib import Path
import pandas as pd
import pymupdf as fitz

ROOT = Path(__file__).resolve().parent
def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', str(s)).encode('ascii','ignore').decode().lower())
def pdf_rows(path, start=150, left=310):
    out=[]
    for pi, pg in enumerate(fitz.open(path)):
        lines=[]
        for b in pg.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                s=''.join(x['text'] for x in l['spans']).strip(); x,y,_,_=l['bbox']
                if s and start<=y<(550 if start>180 else 780): lines.append((y,x,s))
        groups=[]
        for y,x,s in sorted(lines):
            if not groups or abs(y-groups[-1][0])>2: groups.append([y,[]])
            groups[-1][1].append((x,s))
        for y,ls in groups:
            label=[(x,s) for x,s in ls if x<left]
            nums=[s for x,s in ls if x>=left and re.fullmatch(r'-?[\d.]+(?:,\d+)?',s)]
            if not label: continue
            text=' '.join(s for x,s in label)
            if nums: out.append(dict(name=text,x=label[0][0],values=[float(s.replace('.','').replace(',','.')) for s in nums],page=pi+1))
            elif out and not text.startswith('Nota:') and abs(label[0][0]-out[-1]['x'])<2: out[-1]['name']+=' '+text
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cache',type=Path,required=True); args=ap.parse_args(); c=args.cache
    out=ROOT/'nacion/data'; out.mkdir(parents=True,exist_ok=True)
    a=pd.read_csv(c/'credito-anual-2026.csv',decimal=',',low_memory=False)
    assert set(a['ejercicio_presupuestario'])=={2026} and set(a['subsector_id'])=={1}
    assert set(a.clasificador_economico_8_digitos_id.astype(str).str[0])=={'2'}
    cols=['credito_presupuestado','credito_vigente','credito_devengado']
    names=['law','current','accrued']
    def vals(frame): return {n:round(float(frame[col].sum()),6) for n,col in zip(names,cols)}
    def group(col):return {norm(k):vals(g) for k,g in a.groupby(col)}
    total=vals(a); total.update(project=202101433.0,closing=161428086.0)
    official=pd.read_csv(c/'totales-de-presupuesto.csv',decimal=',').set_index('ejercicio_presupuestario').loc[2026]
    for col,key in zip(cols,names): assert abs(total[key]-official[col])<0.02,(col,total[key],official[col])
    def comparisons(file,col):
        current=group(col); result=[]
        for i,r in enumerate(pdf_rows(c/file)):
            if r['name'].startswith('TOTAL'):continue
            v=dict(id=str(i+1),name=r['name'],project=r['values'][1],closing=r['values'][0],source=file,page=r['page'])
            v.update(current.get(norm(r['name']),dict(law=None,current=None,accrued=None)));result.append(v)
        return result
    jurisdictions=comparisons('cap1cu04.pdf','jurisdiccion_desc')
    # Interior is present only in the current classification. Do not label a reorganization as a cut to zero.
    for name,g in a.groupby('jurisdiccion_desc'):
        if norm(name) not in {norm(x['name']) for x in jurisdictions}:
            jurisdictions.append(dict(id='j'+str(len(jurisdictions)),name=name,project=None,closing=None,**vals(g),note='Sin jurisdicción homónima en el proyecto 2027. No se interpreta como eliminación de sus políticas.'))
    purposes=[]; functions=[]; curfun=group('funcion_desc'); curpur=group('finalidad_desc'); pid=0
    for r in pdf_rows(c/'cap1cu02.pdf'):
        if r['name'].startswith('TOTAL'):continue
        ispurpose=r['x']<92
        if ispurpose:pid+=1
        purpose_names=['Administración gubernamental','Servicios de defensa y seguridad','Servicios sociales','Servicios económicos','Deuda pública']
        rec=dict(id=str(pid) if ispurpose else f'{pid}-{len(functions)+1}',name=purpose_names[pid-1] if ispurpose else r['name'],purpose=str(pid),project=r['values'][1],closing=r['values'][0],source='cap1cu02.pdf',page=1)
        rec.update((curpur if ispurpose else curfun).get(norm(r['name']),dict(law=None,current=None,accrued=None)))
        (purposes if ispurpose else functions).append(rec)
    geos=comparisons('cap1cu06.pdf','ubicacion_geografica_desc')
    for r in geos:
        r['name']=re.sub(r'^Provincia (de |del )','',r['name']).replace('Ciudad Autónoma de Buenos Aires','CABA').replace('Tierra del Fuego, Antártida e Islas del Atlántico Sur','Tierra del Fuego')
        # Official geography names sometimes omit the prefix in PA.
        g=a[a.ubicacion_geografica_desc.map(norm).isin([norm(r['name']),norm('Provincia de '+r['name']),norm('Provincia del '+r['name']),norm('Ciudad Autónoma de Buenos Aires') if r['name']=='CABA' else ''])]
        if len(g):r.update(vals(g))
    # PA labels code 99 "No Clasificado"; the 2027 annex labels "Exterior".
    # Preserve both rather than silently equating two geographic definitions.
    unclassified=a[a.ubicacion_geografica_id==99]
    if len(unclassified):geos.append(dict(id='g99',name='No clasificado · 2026',project=None,closing=None,source='credito-anual-2026.zip',**vals(unclassified)))
    prows=pdf_rows(c/'cap1pla7.pdf',203,190); programs=[]; j=e=''
    # A join is accepted only for a unique (jurisdiction, entity, program name) on each side.
    pc=collections.defaultdict(list)
    for key,g in a.groupby(['jurisdiccion_desc','entidad_desc','programa_desc']):pc[tuple(map(norm,key))].append((g,vals(g)))
    for r in prows:
        if r['x']<60:j=r['name']
        elif r['x']<67:e=r['name']
        else:programs.append(dict(id=f'p{len(programs)+1}',name=r['name'],jurisdiction=j,entity=e,project=r['values'][-1],capital=r['values'][-2],source='cap1pla7.pdf',page=r['page'],law=None,current=None,accrued=None))
    counts=collections.Counter((norm(p['jurisdiction']),norm(p['entity']),norm(p['name'])) for p in programs)
    for p in programs:
        key=(norm(p['jurisdiction']),norm(p['entity']),norm(p['name']))
        if counts[key]==1 and len(pc[key])==1:
            g,v=pc[key][0];p.update(v);p['matched']=True
            p['current_functions']=sorted(g.funcion_desc.unique().tolist())
        else:p['matched']=False
    works=[]; wg=[]; geo=j=e=''
    for r in pdf_rows(c/'cap1pl12.pdf',203,190):
        if r['name']=='TOTAL':works_total=r['values'][-1];continue
        if r['x']<60:
            geo=re.sub(r'^Provincia (de |del )','',r['name']).replace('Ciudad Autónoma de Buenos Aires','CABA').replace('Tierra del Fuego, Antártida e Islas del Atlántico Sur','Tierra del Fuego');wg.append(dict(name=geo,project=r['values'][-1]))
        elif r['x']<65:j=r['name']
        elif r['x']<70:e=r['name']
        else:works.append(dict(id=f'w{len(works)+1}',name=r['name'],province=geo,jurisdiction=j,entity=e,project=r['values'][-1],source='cap1pl12.pdf',page=r['page']))
    resources=[]
    for r in pdf_rows(c/'cap1cu08.pdf'):
        if 92<r['x']<96:resources.append(dict(name=r['name'],project=r['values'][1],closing=r['values'][0],source='cap1cu08.pdf',page=1))
    assert abs(sum(r['project'] for r in resources)-202348174)<12
    # Exact ONP function crosswalk for editorial topics: every function appears once.
    topics_map=[('Jubilaciones y pensiones',['Seguridad Social']),('Salud',['Salud']),('Educación y cultura',['Educación y Cultura']),('Asistencia social y trabajo',['Promoción y Asistencia Social','Trabajo']),('Ciencia y tecnología',['Ciencia, Tecnología e Innovación']),('Defensa y seguridad',[x['name'] for x in functions if x['purpose']=='2']),('Energía',['Energía, Combustibles y Minería']),('Transporte',['Transporte']),('Vivienda, agua y ambiente',['Vivienda y Urbanismo','Agua Potable y Alcantarillado','Ecología y Desarrollo Sostenible']),('Producción y comunicaciones',['Agricultura, Ganadería y Pesca','Industria','Comercio, Turismo y Otros Servicios','Seguros y Finanzas','Comunicaciones']),('Justicia',['Judicial']),('Gobierno',[x['name'] for x in functions if x['purpose']=='1' and x['name']!='Judicial']),('Intereses de la deuda',['Servicio de la Deuda Pública (intereses y gastos)'])]
    topics=[]
    for i,(name,fnames) in enumerate(topics_map):
        fs=[x for x in functions if x['name'] in fnames]
        assert len(fs)==len(fnames)
        topics.append(dict(id=f't{i}',name=name,functions=[x['id'] for x in fs],**{k:sum(x[k] for x in fs) if all(x[k] is not None for x in fs) else None for k in ['project','law','current','accrued','closing']}))
    assert sorted(fid for t in topics for fid in t['functions'])==sorted(f['id'] for f in functions)
    ipc=pd.read_csv(ROOT/'data/ipc_national_index.csv').set_index('period').ipc_index.to_dict();anchor=ipc['2026-08']
    # Explicit scenario: observed through Aug 2026, geometric path to ONP Dec/Dec assumptions. Not a published monthly forecast.
    dec26=ipc['2025-12']*1.29
    for m in range(9,13):ipc[f'2026-{m:02}']=anchor*(dec26/anchor)**((m-8)/4)
    for m in range(1,13):ipc[f'2027-{m:02}']=dec26*1.18**(m/12)
    averages={y:sum(ipc[f'{y}-{m:02}'] for m in range(1,13))/12 for y in range(2023,2028)}
    factors={str(y):anchor/v for y,v in averages.items()}
    monthly=pd.read_csv(c/'credito-mensual-2026.csv',decimal=',',usecols=['impacto_presupuestario_mes','jurisdiccion_desc','credito_devengado','ultima_actualizacion_fecha'])
    assert abs(float(monthly.credito_devengado.sum())-total['accrued'])<.05
    execution=[]
    for j,g in [('Total',monthly),*list(monthly.groupby('jurisdiccion_desc'))]:
        series=[dict(month=int(m),accrued=round(float(v.credito_devengado.sum()),6),real=round(float(v.credito_devengado.sum())*anchor/ipc[f'2026-{int(m):02}'],6) if m<=8 else None,partial=bool(m==9)) for m,v in g.groupby('impacto_presupuestario_mes')]
        budget=total['current'] if j=='Total' else group('jurisdiccion_desc')[norm(j)]['current']
        execution.append(dict(name=j,current=budget,months=series))
    history=[]; hist=pd.read_csv(c/'serie_pib_anual.csv'); hfun=pd.read_csv(c/'serie_finfun_anual.csv').set_index('ejercicio_presupuestario')
    for _,r in hist[hist.ejercicio_presupuestario.between(2023,2025)].iterrows():
        year=int(r.ejercicio_presupuestario)
        history.append(dict(year=year,stage='Devengado anual',amount=r.gasto/1e6,gdp_share=r.gasto/r.pib*100,purposes=[sum(float(v) for k,v in hfun.loc[year].items() if k.startswith(f'finalidad{p}_'))/1e6 for p in range(1,6)]))
    history.extend([dict(year=2026,stage='Crédito vigente · 15/09',amount=total['current'],gdp_share=None,purposes=[p['current'] for p in purposes]),dict(year=2027,stage='Proyecto de ley',amount=total['project'],gdp_share=None,purposes=[p['project'] for p in purposes])])
    # Reconcile rounded PDF subtotals; rounding tolerance is <= half a million per printed row.
    checks={}
    for label,items,target in [('programs',programs,total['project']),('works',works,works_total),('functions',functions,total['project']),('purposes',purposes,total['project']),('geographies',[g for g in geos if g['project'] is not None],total['project']),('jurisdictions',[j for j in jurisdictions if j['project'] is not None],total['project'])]:
        diff=sum(x['project'] for x in items)-target
        assert abs(diff)<=len(items)*.51,(label,diff)
        checks[label]=dict(rows=len(items),sum_millions=sum(x['project'] for x in items),official_total_millions=target,rounding_difference_millions=diff)
    sources=json.loads((c/'manifest.json').read_text('utf-8'))
    for s in sources:
        assert not s.get('error'),s
        assert hashlib.sha256((c/s['file']).read_bytes()).hexdigest()==s['sha256']
    data=dict(meta=dict(reviewed='2026-09-17',execution_cutoff='2026-09-15',project_year=2027,base_year=2026,unit='ARS millones',scope='Administración Nacional · gastos corrientes y de capital',project_stage='Proyecto de ley',base_stage='Crédito vigente al 15/09/2026',monthly_real_last='2026-08',program_join_matched=sum(p['matched'] for p in programs),program_join_total=len(programs)),total=total,jurisdictions=jurisdictions,purposes=purposes,functions=functions,topics=topics,geographies=geos,programs=programs,works=works,works_geographies=wg,works_total=works_total,resources=resources,resources_total=202348174,history=history,execution=execution,deflator=dict(anchor='2026-08',annual_factors=factors,annual_average_index=averages,monthly_index={k:v for k,v in ipc.items() if k>='2026-01'},assumptions=dict(inflation_dec_2026=29,inflation_dec_2027=18),method='IPC INDEC observado hasta agosto 2026. Proyección propia: variación mensual constante hasta alcanzar los supuestos ONP de diciembre (29% en 2026; 18% en 2027). Montos anuales divididos por IPC promedio anual y multiplicados por IPC agosto 2026. No usa IPC de diciembre como deflactor anual.',source='../data/ipc_source.json'),macro=[dict(name='Crecimiento del PIB',unit='%',values=[4.5,3,4]),dict(name='Inflación · diciembre contra diciembre',unit='%',values=[31.5,29,18]),dict(name='Dólar · diciembre',unit='ARS/USD',values=[1447.8,1600,1847.6]),dict(name='Consumo privado',unit='%',values=[8.6,3.1,3.4]),dict(name='Inversión',unit='%',values=[16.2,-2.1,9.2]),dict(name='Exportaciones · volumen',unit='%',values=[8.1,7.7,8.5]),dict(name='Importaciones · volumen',unit='%',values=[28,1,8.2])],sources=sources,validation=checks)
    (out/'budget.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n','utf-8')
    (out/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(dict(checks=checks,matched=data['meta']['program_join_matched'],total=total,factors=factors),indent=2))
if __name__=='__main__':main()

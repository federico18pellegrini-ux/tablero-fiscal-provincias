"""Reproducible normalization of the official execution archive, adapted from the audited 17/09 parser."""
import csv,datetime as dt,hashlib,json,math
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
RAW=OUT=None
SOURCES={};CATALOG=[];CHECKS=[];IPC={};ANCHOR=None;CUTOFF=None
NAMES={2:'CABA',6:'Buenos Aires',10:'Catamarca',14:'Córdoba',18:'Corrientes',22:'Chaco',26:'Chubut',30:'Entre Ríos',34:'Formosa',38:'Jujuy',42:'La Pampa',46:'La Rioja',50:'Mendoza',54:'Misiones',58:'Neuquén',62:'Río Negro',66:'Salta',70:'San Juan',74:'San Luis',78:'Santa Cruz',82:'Santa Fe',86:'Santiago del Estero',90:'Tucumán',94:'Tierra del Fuego'}
def clean(v):
    if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    if hasattr(v,'item'): return clean(v.item())
    if isinstance(v,float): return None if not math.isfinite(v) else round(v,8)
    if isinstance(v,(dt.datetime,dt.date)): return v.isoformat()
    return v

def save(name,rows,sources,unit,scope,method='',status='listo_para_integrar'):
    if isinstance(rows,pd.DataFrame): rows=rows.to_dict('records')
    rows=clean(rows)
    path=OUT/(name+'.json')
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False),'utf-8')
    if rows and isinstance(rows,list) and isinstance(rows[0],dict):
        keys=list(dict.fromkeys(k for r in rows for k in r))
        with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
            for r in rows: w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
    lineage=[]
    for file in sources:
        archive=file if file in SOURCES else file.removesuffix('.csv')+'.zip'
        r=dict(SOURCES[archive]);r['member']=file if archive!=file else None
        if (RAW/file).exists(): r['normalized_from_sha256']=hashlib.sha256((RAW/file).read_bytes()).hexdigest()
        lineage.append(r)
    CATALOG.append(dict(dataset=name,rows=len(rows),unit=unit,scope=scope,method=method,status=status,sources=lineage))
    print(name,len(rows),flush=True)
    return rows

def check(name,actual,expected,tolerance=0.02,required=True):
    error=abs(float(actual)-float(expected))
    CHECKS.append(dict(check=name,actual=float(actual),expected=float(expected),tolerance=tolerance,pass_=bool(error<=tolerance),required=required))


def ratio(a,b):return a/b*100 if a is not None and b not in (None,0) else None
def yoy(a,b):return (a/b-1)*100 if a is not None and b not in (None,0) else None
def readcsv(name,**kwargs):return pd.read_csv(RAW/name,decimal=',',low_memory=False,**kwargs)
def grouped(d,keys,cols):return d.groupby(keys,dropna=False,as_index=False)[cols].sum(min_count=1)


AMOUNTS=['credito_presupuestado','credito_vigente','credito_comprometido','credito_devengado','credito_pagado']
FLOWS=AMOUNTS[2:]
DIMS={'jurisdiccion':['jurisdiccion_id','jurisdiccion_desc'], 'funcion':['finalidad_id','finalidad_desc','funcion_id','funcion_desc'], 'territorio':['ubicacion_geografica_id','ubicacion_geografica_desc'], 'objeto':['inciso_id','inciso_desc'], 'programa':['jurisdiccion_id','jurisdiccion_desc','servicio_id','servicio_desc','programa_id','programa_desc']}

def build_budget():
    a=readcsv('credito-anual-2026.csv')
    assert set(a.subsector_id)=={1} and set(a.clasificador_economico_8_digitos_id.astype(str).str[0])=={'2'}
    off=readcsv('totales-de-presupuesto.csv').set_index('ejercicio_presupuestario')
    total={c:float(a[c].sum()) for c in AMOUNTS}
    for c in [AMOUNTS[0],AMOUNTS[1],AMOUNTS[3]]:check('APN anual 2026 '+c,total[c],off.loc[2026,c])
    total.update(corte=CUTOFF,devengado_menos_pagado=total['credito_devengado']-total['credito_pagado'],porcentaje_ejecucion=ratio(total['credito_devengado'],total['credito_vigente']))
    save('gasto_etapas_total',[total],['credito-anual-2026.csv','totales-de-presupuesto.csv'],'ARS millones corrientes','Administración Nacional, gasto corriente y de capital','Devengado menos pagado identifica gasto reconocido aún no pagado de estas partidas; no equivale por sí solo a mora o deuda flotante total.')
    for name,keys in DIMS.items():
        d=grouped(a,keys,AMOUNTS);d['devengado_menos_pagado']=d.credito_devengado-d.credito_pagado
        d['corte']=CUTOFF
        save('gasto_etapas_'+name,d,['credito-anual-2026.csv'],'ARS millones corrientes','Administración Nacional, gasto corriente y de capital','Ubicación geográfica del gasto no equivale a dinero transferido al gobierno de la provincia.')
    monthly=[];transfers=[]
    cols=list(dict.fromkeys(['impacto_presupuestario_mes','subsector_id','clasificador_economico_8_digitos_id']+sum(DIMS.values(),[])+['principal_id','parcial_id']+FLOWS))
    for year in [2025,2026]:
        print('reading monthly',year,flush=True)
        pieces=[];tpieces=[];jpieces=[]
        for d in pd.read_csv(RAW/f'credito-mensual-{year}.csv',usecols=cols,decimal=',',chunksize=120000,low_memory=False):
            d=d[(d.subsector_id==1)&d.clasificador_economico_8_digitos_id.astype(str).str.startswith('2')]
            keys=['impacto_presupuestario_mes']+DIMS['funcion']
            pieces.append(grouped(d,keys,FLOWS))
            if year==2026:jpieces.append(grouped(d,['impacto_presupuestario_mes']+DIMS['jurisdiccion'],FLOWS))
            t=d[(d.inciso_id==5)&d.principal_id.isin([7,8])&(d.parcial_id==1)]
            if len(t):tpieces.append(grouped(t,['impacto_presupuestario_mes']+DIMS['territorio']+['principal_id'],FLOWS))
        m=grouped(pd.concat(pieces),keys,FLOWS);m['anio']=year
        m['periodo']=m.impacto_presupuestario_mes.map(lambda v:f'{year}-{int(v):02}')
        m['mes_completo']=m.periodo<CUTOFF[:7]
        m['ipc']=m.periodo.map(IPC)
        for c in FLOWS:m[c+'_real_agosto2026']=m[c]*ANCHOR/m.ipc
        for c in FLOWS:
            if year==2026:check('Flujos mensuales 2026 vs anual '+c,m[c].sum(),total[c])
        monthly.append(m)
        if year==2026:
            j=grouped(pd.concat(jpieces),['impacto_presupuestario_mes']+DIMS['jurisdiccion'],FLOWS)
            execution=[]
            for name,code,current in [('TOTAL',None,total['credito_vigente'])]+[(r['jurisdiccion_desc'],r['jurisdiccion_id'],r['credito_vigente']) for r in grouped(a,DIMS['jurisdiccion'],AMOUNTS).to_dict('records')]:
                subset=j if code is None else j[j.jurisdiccion_id==code]
                months=[]
                for month,group in subset.groupby('impacto_presupuestario_mes'):
                    period=f'2026-{int(month):02}';v=float(group.credito_devengado.sum());index=IPC.get(period)
                    months.append({'month':int(month),'accrued':v,'real':v*ANCHOR/index if index else None,'partial':period==CUTOFF[:7]})
                execution.append({'name':'Administración Nacional' if code is None else name,'current':current,'months':months})
            (OUT/'execution-latest.json').write_text(json.dumps(clean({'cutoff':CUTOFF,'execution':execution}),ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')
        t=grouped(pd.concat(tpieces),['impacto_presupuestario_mes']+DIMS['territorio']+['principal_id'],FLOWS)
        t['anio']=year;t['periodo']=t.impacto_presupuestario_mes.map(lambda v:f'{year}-{int(v):02}')
        t['tipo_transferencia']=t.principal_id.map({7:'corriente',8:'capital'})
        t['destino_provincia_identificada']=t.ubicacion_geografica_id.isin(NAMES)
        t['mes_completo']=t.periodo<CUTOFF[:7]
        for c in FLOWS:t[c+'_real_agosto2026']=t[c]*ANCHOR/t.periodo.map(IPC)
        transfers.append(t)
    m=pd.concat(monthly,ignore_index=True)
    save('gasto_mensual_funcion',m,['credito-mensual-2025.csv','credito-mensual-2026.csv','ipc-original.xls'],'ARS millones corrientes y constantes de agosto 2026','Administración Nacional','Octubre 2026 parcial hasta el día 4, sin deflactor observado. Solo se suman flujos; no se suman créditos mensuales repetidos.')
    cmpkeys=['finalidad_id','funcion_id'];valcols=FLOWS+[c+'_real_agosto2026' for c in FLOWS]
    yearframes={y:grouped(m[(m.anio==y)&(m.impacto_presupuestario_mes<=8)],cmpkeys,valcols).set_index(cmpkeys) for y in [2025,2026]}
    cmp=yearframes[2026].join(yearframes[2025],how='outer',lsuffix='_2026',rsuffix='_2025').reset_index()
    for year in [2025,2026]:
        labels=m[m.anio==year][DIMS['funcion']].drop_duplicates()
        assert not labels.duplicated(cmpkeys).any()
        labels=labels.rename(columns={'finalidad_desc':f'finalidad_desc_{year}','funcion_desc':f'funcion_desc_{year}'})
        cmp=cmp.merge(labels,on=cmpkeys,how='left',validate='one_to_one')
    for c in FLOWS:
        cmp[c+'_variacion_nominal_pct']=(cmp[c+'_2026']/cmp[c+'_2025']-1)*100
        cmp[c+'_variacion_real_pct']=(cmp[c+'_real_agosto2026_2026']/cmp[c+'_real_agosto2026_2025']-1)*100
    cmp['periodo_comparacion']='Enero–agosto de cada año'
    save('gasto_comparacion_real_funcion',cmp,['credito-mensual-2025.csv','credito-mensual-2026.csv','ipc-original.xls'],'ARS millones y porcentaje','Mismas funciones presupuestarias, enero–agosto','Cada mes se deflacta por su IPC antes de acumular. Unión por finalidad y función; conserva ambos nombres. La función 5.1 agrega la aclaración intereses y gastos en 2026, sin cambiar de código.')
    totals=[]
    for c in FLOWS:
        x=m[(m.anio==2026)&(m.impacto_presupuestario_mes<=8)];y=m[(m.anio==2025)&(m.impacto_presupuestario_mes<=8)]
        totals.append(dict(etapa=c,nominal_2026=x[c].sum(),nominal_2025=y[c].sum(),real_2026=x[c+'_real_agosto2026'].sum(),real_2025=y[c+'_real_agosto2026'].sum(),variacion_real_pct=yoy(x[c+'_real_agosto2026'].sum(),y[c+'_real_agosto2026'].sum()),periodo='enero–agosto'))
    save('gasto_comparacion_real_total',totals,['credito-mensual-2025.csv','credito-mensual-2026.csv','ipc-original.xls'],'ARS millones y porcentaje','Administración Nacional','Comparación enero–agosto de 2025 y 2026, precios de agosto 2026.')
    save('transferencias_presupuestarias_provincias',pd.concat(transfers),['credito-mensual-2025.csv','credito-mensual-2026.csv','ipc-original.xls'],'ARS millones','Transferencias presupuestarias a administraciones públicas provinciales','Objeto 5.7.1 y 5.8.1. Excluye transferencias a municipios y otros destinatarios. Conserva destinos sin provincia identificada. No se las denomina discrecionales sin identificar su norma.')
    for part in [7,8]:
        x=a[(a.inciso_id==5)&(a.principal_id==part)&(a.parcial_id==1)].credito_devengado.sum()
        y=transfers[1].query('principal_id==@part').credito_devengado.sum()
        check('Transferencias provinciales anual vs mensual '+str(part),x,y)

def build_revenue():
    cols=['recurso_inicial','recurso_vigente','recurso_ingresado_percibido']
    a=readcsv('recursos-anual-2026.csv');off=readcsv('totales-de-presupuesto.csv').set_index('ejercicio_presupuestario')
    assert set(a.subsector_id)=={1} and set(a.clasificador_economico_8_digitos_id.astype(str).str[0])=={'1'}
    for c in cols:check('Recursos APN anual '+c,a[c].sum(),off.loc[2026,c])
    save('recursos_etapas_tipo',grouped(a,['tipo_id','tipo_desc'],cols),['recursos-anual-2026.csv'],'ARS millones corrientes','Recursos de Administración Nacional al 04/10/2026','Estimación inicial, vigente y recaudación percibida. No se combina con gasto devengado para construir el resultado fiscal de caja del SPN.')
    months=[]
    for y in [2025,2026]:
        d=readcsv(f'recursos-mensual-{y}.csv');assert set(d.subsector_id)=={1}
        g=grouped(d,['impacto_presupuestario_mes','tipo_id','tipo_desc'],[cols[-1]])
        g['periodo']=g.impacto_presupuestario_mes.map(lambda m:f'{y}-{int(m):02}');g['mes_completo']=g.periodo<CUTOFF[:7]
        g['recurso_real_agosto2026']=g[cols[-1]]*ANCHOR/g.periodo.map(IPC);months.append(g)
        if y==2026:check('Recursos mensual vs anual',g[cols[-1]].sum(),a[cols[-1]].sum())
    save('recursos_mensuales_tipo',pd.concat(months),['recursos-mensual-2025.csv','recursos-mensual-2026.csv','ipc-original.xls'],'ARS millones corrientes y constantes de agosto 2026','Recursos de Administración Nacional','Octubre 2026 es parcial, sin ajuste real hasta contar con IPC observado.')


def build_physical():
    out=[];coverage=[]
    keys=['ejercicio_presupuestario','trimestre','jurisdiccion_id','subjurisdiccion_id','servicio_id','programa_id','subprograma_id','tipo_medicion_fisica','medicion_fisica_id','unidad_medida_id']
    for q in [1,2]:
        file=f'ejecucion-fisica-trimestre-{q}-2026.csv';d=readcsv(file)
        for col in d.columns:
            if col.startswith(('programacion_','ejecutado_','porc_desvio_')):
                if d[col].dtype.kind not in 'fi':
                    original=d[col].astype(str).str.strip()
                    converted=pd.to_numeric(original.str.replace(',','.',regex=False),errors='coerce')
                    assert set(original[converted.isna()])<={'-','nan',''},(col,set(original[converted.isna()]))
                    d[col]=converted
        allcols=[c for c in d.columns if not c.startswith('causa_desvio')]
        # Group identical measurements; multiple cause records are not additional output.
        g=d.groupby(allcols,dropna=False,sort=False)
        rows=[]
        for values,group in g:
            rec=dict(zip(allcols,values));rec['filas_csv']=(group.index+2).tolist()
            rec['causas']=group[[c for c in d.columns if c.startswith('causa_desvio')]].drop_duplicates().to_dict('records')
            rows.append(rec)
        n=pd.DataFrame(rows)
        duplicate=n.duplicated(keys,keep=False)
        n['requiere_revision_clave']=duplicate
        missing=n[f'ejecutado_acumulado_trim{q}'].isna().sum()
        coverage.append(dict(trimestre=q,filas_fuente=len(d),mediciones=len(n),filas_repetidas_por_causa=len(d)-len(n),mediciones_sin_ejecucion=int(missing),mediciones_con_clave_conflictiva=int(duplicate.sum())))
        save(f'metas_fisicas_trimestre_{q}',n,[file,'documentacion-metas.pdf'],'Unidad específica de cada medición','Administración Nacional, programación y ejecución física','Se conserva totalizador (suma, promedio, stock o transversal). No se suman unidades incompatibles ni se reemplaza ejecución faltante con cero. Causas múltiples reunidas sin duplicar producción.')
    save('metas_cobertura',coverage,['ejecucion-fisica-trimestre-1-2026.csv','ejecucion-fisica-trimestre-2-2026.csv'],'conteos','Cobertura de programación y ejecución física')

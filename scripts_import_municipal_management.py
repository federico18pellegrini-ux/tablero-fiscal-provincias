"""Reproduce the Las Heras/Tigre audit from hash-verified primary documents.

Usage: python scripts_import_municipal_management.py --input-dir /path/to/research
Requires PyMuPDF, openpyxl and xlrd only for importing; dashboard builds use stdlib.
"""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LANDINGS = {'06329': 'https://gobiernodelasheras.com/category/documentos/',
            '06805': 'https://www.tigre.gob.ar/gobierno/informacion_gestion'}
FIELDS = [('I. INGRESOS CORRIENTES', 'ingresos_corrientes'), ('II. GASTOS CORRIENTES', 'gastos_corrientes'),
          ('IV. RECURSOS DE CAPITAL', 'ingresos_capital'), ('V. GASTOS', 'gastos_capital'),
          ('VI. INGRESOS TOTALES', 'ingresos_totales'), ('VII. GASTOS TOTALES', 'gastos_totales'),
          ('VIII. RESULTADO FINANCIERO', 'resultado_financiero')]


def reconcile(a):
    a = {k: D(str(v)) for k, v in a.items()}
    for delta in [a['ingresos_corrientes']+a['ingresos_capital']-a['ingresos_totales'],
                  a['gastos_corrientes']+a['gastos_capital']-a['gastos_totales'],
                  a['ingresos_totales']-a['gastos_totales']-a['resultado_financiero']]:
        if abs(delta) > D('.01'): raise ValueError('Fiscal account does not reconcile')


def parse_execution(path, kind):
    import pymupdf
    ends = [317,374,430,486,542,597,652,708,762,813] if kind == 'expense' else [428,484,540,597,654,712,765,821]
    labels = ['original','modifications','current','preventive','commitment','accrued','paid','available','notAccrued','unpaid'] if kind == 'expense' else ['original','modifications','current','accrued','notAccrued','received','unreceived','unreceivedBudget']
    records = []; jurisdiction = program = ''
    for pno, page in enumerate(pymupdf.open(path), 1):
        lines = []
        for word in page.get_text('words', sort=True):
            y = (word[1]+word[3])/2
            line = next((line for line in lines[-5:] if abs(line[0]-y)<2), None)
            if line is None: line = [y,[]]; lines.append(line)
            line[1].append(word)
        for y, words in sorted(lines):
            words.sort(key=lambda w:w[0]); text = ' '.join(w[4] for w in words)
            if text.startswith('Jurisdicción:'): jurisdiction = text.split(':',1)[1].strip()
            if re.match(r'^\d{2}(?:\.\d{2}){0,2} - ',text): program = text
            code = re.match(r'^([1-9](?:\.\d+)+) - ',text)
            nums = [w for w in words if re.fullmatch(r'-?\d[\d,]*\.\d{2}',w[4]) and w[0]>(260 if kind=='expense' else 365)]
            if not code or not nums: continue
            # RAFAM prints empty cells for zero execution; leaf and grand totals
            # below independently control every monetary column we publish.
            values = {k:D(0) for k in labels}; seen=set()
            for w in nums:
                col = min(range(len(ends)),key=lambda i:abs(w[2]-ends[i]))
                if abs(w[2]-ends[col])>14 or col in seen: raise ValueError('Ambiguous execution cell')
                seen.add(col); values[labels[col]]=D(w[4].replace(',',''))
            # The PDF clips leading digits/signs in this unused income column.
            # Do not retain its extracted values or present them as verified.
            if kind == 'income': values.pop('unreceived')
            records.append({'page':pno,'code':code[1],'program':program,'jurisdiction':jurisdiction,
                            'label':' '.join(w[4] for w in words if w[0]<(260 if kind=='expense' else 365)), 'amounts':values})
    return records


def tigre_account(expenses, income):
    e = lambda prefix: sum((r['amounts']['accrued'] for r in expenses if r['code'].startswith(prefix)),D(0))
    i = lambda prefix: sum((r['amounts']['received'] for r in income if r['code'].startswith(prefix)),D(0))
    # RAFAM's economic/object mapping: inputs assigned to projects form own
    # construction, not current consumption. Validate against published 2025 CAIF.
    works = [r for r in expenses if r['code'][0] in '123' and len(r['program'].split(' ')[0].split('.'))==3]
    inputs = sum((r['amounts']['accrued'] for r in works),D(0))
    current = e('1.')+e('2.')+e('3.')+e('5.1.')+e('5.3.')+e('7.3.')-inputs
    capital = e('4.')+e('5.2.')+e('6.2.')+inputs
    a = {'ingresos_corrientes':i('1.'),'ingresos_capital':i('2.')+i('3.3.'),
         'gastos_corrientes':current,'gastos_capital':capital,'gastos_totales':current+capital,
         'ingresos_totales':i('1.')+i('2.')+i('3.3.'),'personal_devengado':e('1.')}
    a['resultado_financiero']=a['ingresos_totales']-a['gastos_totales']; reconcile(a)
    if e('')-e('7.4.')-e('7.6.') != a['gastos_totales'] or i('') != a['ingresos_totales']:
        raise ValueError('New financial classification requires review')
    bridge={'budgetAccrued':e(''),'amortization':e('7.4.'),'priorLiabilities':e('7.6.'),
            'interestIncluded':e('7.3.'),'projectInputsIncludedInCapital':inputs,'fiscalExpenditure':a['gastos_totales']}
    return a, bridge


def build(folder):
    import pymupdf
    import openpyxl
    import xlrd
    sources=json.loads((folder/'sources.json').read_text(encoding='utf-8'))
    sources={Path(s['file'].replace('\\','/')).name:s for s in sources if s['status']=='ok'}
    used={}
    def source(name,pages=(1,)):
        s=sources[name];path=folder/Path(s['file'].replace('\\','/'))
        if hashlib.sha256(path.read_bytes()).hexdigest()!=s['sha256']:raise ValueError('Source hash changed: '+name)
        d={k:s[k] for k in ['url','sha256','bytes']};d['file']=name;d['title']=s['title'];d['retrieved']='2026-09-09'
        if 'pages' in s:d.update(pages=s['pages'],consultedPages=list(pages))
        used[name]=d
        return path,d
    def caif(name):
        path,doc=source(name);page=pymupdf.open(path)[0];t=page.get_text(sort=True)
        ident=name[:5]
        if name=='06329--sitecofin-1sem-2022.pdf':
            # Image-only original, page 1 visually transcribed and reconciled.
            start,end='2022-01-03','2022-06-30'
            vals=['843401150.44','542548806.57','7748329.46','206097896.24','851149479.90','748646702.81','102502777.09']
            a={key:D(v) for (_,key),v in zip(FIELDS,vals)};a['personal_devengado']=D('306745759.27')
        else:
            dates=re.search(r'DEL\s+(\d{2}/\d{2}/\d{4})\s+AL\s+(\d{2}/\d{2}/\d{4})',t,re.I)
            if not dates:raise ValueError('Missing account dates: '+name)
            start,end=('-'.join(reversed(x.split('/'))) for x in dates.groups())
            def numbers(s):
                tokens=re.findall(r'-?\d[\d.,]*[.,]\d{2}',s)
                return [D(x[:-3].replace('.','').replace(',','')+'.'+x[-2:]) for x in tokens]
            a={}; account_text=page.get_text(sort=True,clip=pymupdf.Rect(page.rect.width*.55,0,page.rect.width,page.rect.height)) if ident=='06329' else t
            for marker,key in FIELDS:
                line=next(x for x in account_text.splitlines() if marker in x.upper())
                a[key]=numbers(line)[-1]
            line=next(x for x in t.splitlines() if re.search(r'GASTOS EN PERSONAL',x,re.I))
            a['personal_devengado']=numbers(line)[-2]
        try: reconcile(a)
        except ValueError as error: raise ValueError(f'{name}: {a}') from error
        return {'inicio':start,'fin':end,'method':'published_caif','landingUrl':sources[name].get('landingUrl',LANDINGS[ident]),
                'documents':[doc],'scope':'Cuenta municipal publicada; se conserva el período exacto del original. No se presume consolidación de entes con cuentas separadas.', 'amounts':a}
    histories={ident:[] for ident in LANDINGS}
    for name in sources:
        if any(x in name.upper() for x in ['SITECOFIN','STIECOFIN','SIT-ECON-FIN','SITUACION-ECON-FIN','SITUACION_ECONOMICO','SIUACION_ECONOMICO']):
            histories[name[:5]].append(caif(name))
    lh=histories['06329'];parts=[r for r in lh if r['inicio'].startswith('2025')]
    assert len(parts)==2 and sorted(r['fin'] for r in parts)==['2025-06-30','2025-12-31']
    parts.sort(key=lambda r:r['inicio'])
    annual={**parts[0],'fin':parts[1]['fin'],'method':'sum_semesters','documents':parts[0]['documents']+parts[1]['documents'],
            'components':parts,'amounts':{k:sum(r['amounts'][k] for r in parts) for k in parts[0]['amounts']},
            'scope':'Suma de 02/01–30/06 y 01/07–31/12 de 2025, sin superposición. No se presume actividad del 1 de enero.'}
    reconcile(annual['amounts']);lh.append(annual)
    parsed={}
    for period in ['31-12-2025','30-06-2026']:
        rows={}
        for kind,prefix in [('expense','PRESUPUESTO_DE_GASTOS'),('income','CALCULO_DE_RECURSOS')]:
            name=f'06805--EJECUCION_{prefix}_AL_{period}.pdf';path,doc=source(name,range(1,sources[name]['pages']+1))
            rows[kind]=parse_execution(path,kind)
        a,bridge=tigre_account(rows['expense'],rows['income']);parsed[period]=(rows,a,bridge)
    official=next(r for r in histories['06805'] if r['fin']=='2025-12-31')['amounts']
    assert parsed['31-12-2025'][1]==official,'Reconstructed 2025 differs from official CAIF'
    rows,a,bridge=parsed['30-06-2026']
    # Independent published grand totals for all ten expense columns.
    totals={k:sum(r['amounts'][k] for r in rows['expense']) for k in rows['expense'][0]['amounts']}
    expected=['578906001955.00','32388556667.66','611294558622.66','17391743185.38','301914171435.11','239430557656.92','231010667809.66','291988644002.17','371864000965.74','8419889847.26']
    assert list(totals.values())==[D(v) for v in expected]
    assert sum(r['amounts']['received'] for r in rows['income'])==D('218657322550.68')
    tg={'inicio':'2026-01-01','fin':'2026-06-30','verifiedAt':'2026-09-09','method':'reconstructed_programmatic','landingUrl':LANDINGS['06805'],
        'amounts':a,'documents':[used[f'06805--EJECUCION_{p}_AL_30-06-2026.pdf'] for p in ['PRESUPUESTO_DE_GASTOS','CALCULO_DE_RECURSOS']],
        'scope':'Reconstrucción de las ejecuciones oficiales por objeto y programa. Se excluyen amortizaciones y cancelaciones de pasivos anteriores; se conservan intereses e insumos de obras. Método conciliado con la cuenta anual oficial 2025.'}
    histories['06805'].append(tg)
    fiscalpath=ROOT/'municipios/data/fiscal_verified.json';fiscal=json.loads(fiscalpath.read_text(encoding='utf-8'))
    fiscal['records']=[r for r in fiscal['records'] if r['id']!='06805']+[{'id':'06805',**tg}]
    fiscal['budgetExecutions']=[r for r in fiscal['budgetExecutions'] if r['id']!='06805'];fiscal['updatedAt']='2026-09-09'
    next(r for r in fiscal['records'] if r['id']=='06329')['verifiedAt']='2026-09-09'
    lhdoc=used['06329--SITECOFIN-1SEM-2026.pdf'];lhdoc['consultedPages']=[1,3]
    lhobjects=[('Personal','9658128700.00','4727411019.57','4623367471.88'),('Bienes de consumo','3148991822.13','999519289.64','971552759.97'),('Servicios','4195150798.41','1719094560.12','1700699919.89'),('Bienes de uso','1703144874.71','1171848925.01','1171651925.01'),('Transferencias','781132877.97','226304138.04','213504882.89'),('Activos financieros','26600000.00','9262425.93','9262425.93'),('Deuda y otros pasivos','780813130.74','883935014.98','882949519.98')]
    def obj(label,budget,accrued,paid):return {'label':label,'amounts':{'current':D(budget),'accrued':D(accrued),'paid':D(paid)}}
    byobject=defaultdict(lambda:defaultdict(D))
    for r in rows['expense']:
        for k in ['current','accrued','paid']:byobject[r['code'][0]][k]+=r['amounts'][k]
    labels={str(i+1):r[0] for i,r in enumerate(lhobjects)}
    tgobjects=[obj(labels[k],v['current'],v['accrued'],v['paid']) for k,v in sorted(byobject.items())]
    origins=defaultdict(D)
    for r in rows['income']:
        key=next((k for k in ['MUNICIPAL','PROVINCIAL','NACIONAL'] if 'ORIGEN '+k in r['label']),'OTRO')
        origins[key]+=r['amounts']['received']
    assert origins['OTRO']==0
    budgets={
      '06329':{'inicio':'2026-01-01','fin':'2026-06-30','documents':[lhdoc],
               'amounts':{'current':D('20293962203.96'),'received':D('10441008325.60'),'accrued':D('9737375373.29'),'paid':D('9572988905.55'),'unpaid':D('164386467.74')},
               'objects':[obj(*r) for r in lhobjects], 'receiptTitle':'Destino de los recursos cobrados',
               'receipts':[{'label':'De libre disponibilidad (ingresos)','amounts':{'received':D('7942857342.65')}},{'label':'Con destino asignado (afectados)','amounts':{'received':D('2498150982.95')}}],
               'reading':'Al cierre de junio se había devengado el 48,0% del presupuesto anual vigente. Quedaban $164,4 millones de esos gastos sin pagar. Esa cifra mide obligaciones registradas en el semestre; no toda la deuda municipal. Los ingresos de libre disponibilidad tampoco equivalen al saldo de caja que queda libre.'},
      '06805':{'inicio':'2026-01-01','fin':'2026-06-30','documents':tg['documents'],
               'amounts':{k:totals[k] for k in ['original','modifications','current','accrued','paid','unpaid']},
               'objects':tgobjects,'receiptTitle':'Origen de los recursos cobrados',
               'receipts':[{'label':'Origen '+k.lower(),'amounts':{'received':v}} for k,v in origins.items() if k!='OTRO'],
               'reconciliation':{'amounts':bridge},
               'reading':'El presupuesto registra $239.430,6 millones de gastos, pero incluye $33.637,1 millones de amortizaciones y cancelación de pasivos anteriores. Al separarlos, el gasto fiscal del semestre queda en $205.793,5 millones. Los intereses permanecen dentro del gasto. Los pagos pendientes del período son $8.419,9 millones y no representan por sí solos toda la deuda.'}}
    budgets['06805']['amounts']['received']=a['ingresos_totales']
    path,consolidated=source('06805--SALDO_DEUDA_CONSOLIDADA_2025.xlsx');sheet=openpyxl.load_workbook(path,data_only=True).worksheets[0]
    loans={key:D(str(sheet[cell].value)) for key,cell in [('consolidated','F27'),('current','F20'),('nonCurrent','F25')]}
    assert loans['current']+loans['nonCurrent']==loans['consolidated']==D('1502037.70')
    _,floating=source('06805--EVOLUCION_DE_LA_DEUDA_FLOTANTE_2025.docx')
    _,summary=source('06805--RESUMEN_PRESUPUESTARIO_2025.xlsx')
    source('06329--BALTES-1SEM-2026.pdf',[7])
    debt={'date':'2025-12-31','documents':[consolidated,floating], 'amounts':{**loans,'floating':D('33832574642.10')},
          'floatingHistory':[{'year':y,'amounts':{'floating':D(v)}} for y,v in [(2019,'453791177'),(2020,'913193979'),(2021,'1229009881'),(2022,'1798793295'),(2023,'4181054967'),(2024,'12646084652'),(2025,'33832574642')]],
          'reading':'La deuda consolidada corresponde a préstamos y convenios; la deuda flotante, a gastos registrados que quedaban sin pagar. En Tigre el mayor monto está en esta segunda categoría. No se deben confundir $1,5 millones de deuda consolidada con toda la deuda del municipio. La serie de deuda flotante está publicada en pesos corrientes, redondeados a pesos enteros; el cierre 2025 con centavos se concilia con la ejecución. No informa el vencimiento de cada factura.'}
    treasuries={
      '06329':{'date':'2026-06-30','documents':[lhdoc], 'amounts':{'closing':D('1718889847.93'),'available':D('1637017470.98'),'transitory':D('81872376.95'),'liabilities':D('574895931.29'),'currentLiabilities':D('574895931.29'),'nonCurrentLiabilities':D(0)},
               'reading':'Tesorería informa $1.718,9 millones: $1.637,0 millones de disponibilidades y $81,9 millones de movimientos transitorios. Incluye fondos afectados, como educación, y valores en cartera. Por eso no se puede disponer libremente de todo ese saldo. Los pasivos contables suman $574,9 millones; el informe no los desglosa por fecha de vencimiento. No se suman a los gastos pendientes del semestre: pueden superponerse.'},
      '06805':{'date':'2025-12-31','documents':[used['06805--SITUACION_ECONOMICO_FINANCIERA_AL_31-12-2025.pdf'],summary],
               'amounts':{'closing':D('49608076288.69'),'budgetCash':D('43532075335.91'),'unearmarkedAccounts':D('22978118240.65'),'earmarkedAccounts':D('20553957095.26'),'thirdPartyAndSpecial':D('6076000952.78'),'liabilities':D('40079689651.22'),'currentLiabilities':D('40078641766.74'),'nonCurrentLiabilities':D('1047884.48')},
               'reading':'El cierre de 2025 informa $49.608,1 millones en tesorería. De ese total, $43.532,1 millones corresponden a cuentas presupuestarias y $6.076,0 millones a terceros y cuentas especiales. Hay fondos afectados y obligaciones pendientes: el total no es caja libre. Este saldo es de diciembre de 2025; no describe la caja de junio de 2026 ni se resta de deudas de otra fecha.'}}
    treasuries['06805']['documents'][0]={**treasuries['06805']['documents'][0],'consultedPages':[3]}
    banking={ident:{'records':[],'documents':[],'note':'BCRA: saldos por ubicación de la casa o sucursal bancaria, en pesos. Se suman sectores público, privado no financiero y residentes del exterior. La moneda extranjera ya está convertida a pesos por el BCRA. No identifica solamente habitantes, pymes ni depósitos del gobierno municipal.'} for ident in LANDINGS}
    for year in [2023,2024,2025,2026]:
        path,doc=source(f'BCRA-Loc{year}.xls');sheet=xlrd.open_workbook(path).sheet_by_name('Datos')
        cut=year*10000+(630 if year==2026 else 1231);found={}
        for idx in range(sheet.nrows):
            row=sheet.row_values(idx);district=str(row[1]).strip();locality=str(row[2]).strip()
            if row[3]!=cut or row[4]!=0:continue
            ident='06805' if district=='TIGRE' and not locality else '06329' if district==locality=='GENERAL LAS HERAS' else None
            if not ident:continue
            if ident in found:raise ValueError('Ambiguous banking geography')
            loans=sum(D(str(row[k])) for k in [7,9,11])*1000
            deposits=sum(D(str(row[k])) for k in [8,10,12])*1000
            valid=ident=='06805'
            if not valid and (loans!=0 or deposits!=0):raise ValueError('Review newly published Las Heras banking figures')
            found[ident]={'date':f'{year}-'+('06-30' if year==2026 else '12-31'),'status':'verified' if valid else 'reserved_or_unverified',
                          'sourceRow':idx+1,'sourceFile':doc['file'],'sheet':'Datos','columns':{'loans':['H','J','L'],'deposits':['I','K','M']},
                          'amounts':{'loans':loans.quantize(D('.01')),'deposits':deposits.quantize(D('.01'))} if valid else {},
                          'rawValues':{'loansThousands':str(loans/1000),'depositsThousands':str(deposits/1000)}}
        if set(found)!=set(LANDINGS):raise ValueError('Missing banking district/cutoff')
        for ident,row in found.items():banking[ident]['records'].append(row);banking[ident]['documents'].append(doc)
    baseline=json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
    old=next(m for m in baseline['municipalities'] if m['id']=='06805')
    for r in banking['06805']['records'][:2]:
        year=r['date'][:4]
        for field,original in [('loans','prestamos'),('deposits','depositos')]:
            if abs(r['amounts'][field]-D(str(old[f'{original}_{year}_ars'])))>D('.01'):raise ValueError('BCRA no longer agrees with original DPE bank series')
    pending=['Caja de libre disponibilidad conciliada, descontando fondos afectados y todas las obligaciones exigibles.',
             'Calendario futuro de capital e intereses, por contrato, moneda y fecha.',
             'Antigüedad y vencimiento de la deuda con proveedores; distinguir pendiente de vencida.',
             'Ingresos y gastos mensuales para ajustar cada flujo fiscal por inflación.']
    municipalities=[]
    for ident in LANDINGS:
        h=sorted(histories[ident],key=lambda r:(r['fin'],r['inicio']))
        municipalities.append({'id':ident,'history':h,'budget':budgets[ident],'treasury':treasuries[ident],'banking':banking[ident],
                              'debt':debt if ident=='06805' else None,
                              'pending':pending+(['Cierre fiscal anual de 2023. Los datos disponibles del primer semestre no se anualizan.','Desglose contractual del stock de deuda; los pasivos contables no identifican por sí solos préstamos.','Presupuesto original de 2026 y detalle de sus modificaciones; el presupuesto vigente sí está incorporado.','Préstamos y depósitos bancarios 2025 y junio de 2026: sin cifras verificables para Las Heras.'] if ident=='06329' else ['Estado de tesorería y stock completo de pasivos a junio de 2026.']),
                              'historyReading':'Los cortes de mitad de año y los cierres anuales se leen por separado. Un superávit en junio no asegura cerrar el año con superávit. Los importes históricos están en pesos de cada período: para seguir el equilibrio se muestra el resultado como porcentaje de los ingresos, sin presentarlo como una variación real.'})
    audit={'version':1,'verifiedAt':'2026-09-09','classification':{'url':'https://normas.gba.gob.ar/documentos/VW5JbhYx.pdf','pages':[225,226],
            'method':'Matriz de conversión objeto/carácter económico; insumos de proyectos como producción propia. Conciliación íntegra con CAIF Tigre 2025 antes de aplicar a junio de 2026.'},
           'controls':{'tigre2025MatchesPublishedCAIF':True,'tigre2026ExpenseLeafRows':len(rows['expense']),'tigre2026IncomeLeafRows':len(rows['income']),
                       'tigre2025Bridge':{'amounts':parsed['31-12-2025'][2]},
                       'incomeExtractionLimit':'La columna Devengado no percibido recorta dígitos y signos en el PDF; no se incorpora. Los totales cobrados, devengados y presupuestados utilizados concilian.'},
           'sources':list(used.values()),'municipalities':municipalities}
    encode=lambda x:format(x,'.2f') if isinstance(x,D) else str(x)
    for path,value in [(fiscalpath,fiscal),(ROOT/'municipios/data/management_verified.json',audit)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=encode)+'\n',encoding='utf-8')
    print(json.dumps({'sources':len(used),'history':{k:len(v) for k,v in histories.items()},'tigre2026':a},default=encode))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input-dir',required=True,type=Path)
    build(parser.parse_args().input_dir)

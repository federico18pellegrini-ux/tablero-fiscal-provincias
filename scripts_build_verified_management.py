"""Rebuild verified management additions from preserved official files.

Usage: python scripts_build_verified_management.py ../management-research
The cache contains originals, never edited. Scanned schedules were visually
transcribed; their reference and evidence hashes are retained below.
"""
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REVIEWED = '2026-09-07'

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def build(cache):
    import pandas as pd
    from pypdf import PdfReader
    def source(name, label, trace, unit='ARS pesos'):
        meta = json.loads((cache/(name+'.json')).read_text(encoding='utf-8'))
        digest = hashlib.sha256((cache/meta['file']).read_bytes()).hexdigest()
        assert digest == meta['sha256'], name
        return dict(url=meta.get('final_url', meta['url']), label=label, sha256=digest, original_unit=unit, trace=trace)
    def budget(province, date, scope, note, sources, **metrics):
        return dict(province=province, as_of=date, period_start='2026-01-01', year=2026,
                    scope=scope, unit='ARS millions', note=note, sources=sources,
                    credit_ars_m=None, accrued_ars_m=None, committed_ars_m=None,
                    paid_ars_m=None, **metrics)
    # Update a fixed schema without treating absent stages as zero.
    def row(province, date, scope, note, sources, **metrics):
        b=budget(province,date,scope,note,sources); b.update(metrics); return b
    records=[]
    records.append(row('Neuquén','2026-06-30','APNF, incluido el Instituto de Seguridad Social',
        'Datos provisorios. Crédito anual y devengado acumulado a junio, de igual cobertura. Excluye gastos figurativos del total consolidado.',
        [source('nqn-vigente','Crédito vigente AIF, segundo trimestre 2026','Página 1, columna (6), filas VI, VII y V','ARS millions'),
         source('nqn-devengado','AIF devengado, segundo trimestre 2026','Página 1, columna (6), filas VI, VII y V','ARS millions')],
        credit_ars_m=10108919.7, accrued_ars_m=4786043.2, income_budget_ars_m=9762226.6,
        income_collected_ars_m=4915131.7, capital_credit_ars_m=1508977.2, capital_accrued_ars_m=449052.0))
    rn=PdfReader(cache/'rn-july.pdf').pages[0].extract_text()
    for number in ['3,748,997,524,226.70','2,312,245,187,213.20','1,750,183,942,875.55']:
        assert number in rn.replace(' ','') or number.replace(',','.') in rn.replace(' ',''), number
    records.append(row('Río Negro','2026-07-31','Administración Provincial; incluye aplicaciones financieras',
        'Incluye reservas y remanentes; excluye figurativos. Compromiso es gasto comprometido, no devengado. El saldo del presupuesto es autorización sin comprometer, no dinero en el banco.',
        [source('rn-july','Ejecución por objeto del gasto, enero–julio 2026','Página 1, fila TOTAL ADMINISTRACIÓN PROVINCIAL, columnas (2), (3), (4) y (5)')],
        credit_ars_m=3748997.5242267, committed_ars_m=2312245.1872132,
        ordered_for_payment_ars_m=1982418.61329802, paid_ars_m=1750183.94287555))
    ch=pd.ExcelFile(cache/'chubut-q1.xls')
    def ch_value(sheet, label):
        frame=pd.read_excel(ch,sheet,header=None)
        selected=frame[frame.iloc[:,0].astype(str).str.strip().str.startswith(label)]
        assert len(selected)==1, (sheet,label)
        return float(selected.iloc[0,4])/1e6
    ch_credit=ch_value('CTA.FINANCIAMIENTO Vigente','VIII. GASTOS TOTALES')
    ch_accrued=ch_value('CTA.FINANCIAMIENTO Devengado','VIII. GASTOS TOTALES')
    ch_capital=ch_value('CTA.CAPITAL Devengado','VI. GASTOS DE CAPITAL')
    old=json.loads((ROOT/'data/budget_execution_2026.json').read_text(encoding='utf-8'))
    comparable=next(r for r in old['executions'] if r['province']=='Chubut' and r['period']=='2026-Q1')
    assert abs(ch_capital-comparable['capital'])<.0001 # Independent unit reconciliation.
    records.append(row('Chubut','2026-03-31','Administración Provincial, incluido ISSyS',
        'Crédito vigente y devengado de la misma planilla. Incluye ISSyS; no se mezcla con el presupuesto inicial de otra cobertura. La unidad se concilió con el gasto de capital de la planilla nacional.',
        [source('chubut-q1','Información fiscal provincial, marzo 2026','Hojas CTA.FINANCIAMIENTO Vigente y Devengado, columna TOTAL; VIII GASTOS TOTALES. Unidad: gasto de capital / 1.000.000 = 50.562,86313353 millones en DNAP.')],
        credit_ars_m=ch_credit, accrued_ars_m=ch_accrued,
        capital_credit_ars_m=ch_value('CTA.CAPITAL Vigente','VI. GASTOS DE CAPITAL'), capital_accrued_ars_m=ch_capital))
    cba=PdfReader(cache/'cba-q1-report.pdf').pages[17].extract_text()
    assert '12.048.593.176.000' in cba and '2.577.785.334.966' in cba
    records.append(row('Córdoba','2026-03-31','Administración General Centralizada (cobertura parcial de la provincia)',
        'Informe de ejecución de la Administración Central: rentas generales y recursos afectados. No es el total de la APNF. Se usa el total del informe, que excluye amortizaciones; no se suma con el archivo de entidades descentralizadas.',
        [source('cba-q1-report','Informe de ejecución presupuestaria, marzo 2026','Página 18: Crédito Vigente, Total Devengado y cobertura; utilización publicada 21,39%.')],
        credit_ars_m=12048593.176, accrued_ars_m=2577785.334966))
    cat=pd.read_csv(cache/'cat-aug-gasto.html',decimal=',',thousands='.')
    detail=cat[cat.Ejer.eq('2026')].copy()
    assert len(detail)==10384 and not detail.duplicated().any()
    total=cat[cat.Ejer.eq('Totales Generales')].iloc[0]
    for col in cat.columns[-5:]: assert abs(detail[col].sum()-total[col])<.02, col
    # Do not add the published total row to its components. Remove internal
    # transfers and financial applications from BOTH credit and expenditure.
    selected=detail[detail['In'].ne(9)&detail['Econ. Créd.'].astype(int).astype(str).str.startswith(('21','22'))]
    initial=next(r for r in old['budgets'] if r['province']=='Catamarca')
    assert abs(selected['Crédito Inicial'].sum()/1e6-initial['spending'])<.01
    records.append(row('Catamarca','2026-08-31','Administración Provincial; sin figurativos ni aplicaciones financieras',
        'Acumulado a agosto. Se excluyen las transferencias entre organismos y las aplicaciones financieras tanto del crédito como de la ejecución. El total general del archivo no se vuelve a sumar.',
        [source('cat-aug-gasto','Gastos a agosto 2026, datos abiertos de Contaduría','10.384 filas Ejer=2026; excluir In=9 y económico distinto de 21/22. Columnas Crédito Vigente, Devengado Consumido, Compromiso Consumido y Pagado. Inicial conciliado con presupuesto nacional.')],
        credit_ars_m=selected['Crédito Vigente'].sum()/1e6, accrued_ars_m=selected['Devengado Consumido'].sum()/1e6,
        committed_ars_m=selected['Compromiso Consumido'].sum()/1e6, paid_ars_m=selected.Pagado.sum()/1e6))
    tuc='\n'.join(p.extract_text() for p in PdfReader(cache/'tuc-current.pdf').pages)
    assert '5.027.538' in tuc and '30/04/2,026' in tuc and 'MILLONES DE PESOS' in tuc
    records.append(row('Tucumán','2026-04-30','APNF; esquema Ahorro–Inversión–Financiamiento',
        'Se verificó el crédito anual vigente a abril. No se calcula un porcentaje de ejecución sin un devengado del mismo período y cobertura conciliados.',
        [source('tuc-current','Planilla 1.4, instancia vigente al 30/04/2026','Página 2, última columna; filas VI, VII y V','ARS millions')],
        credit_ars_m=5027538, income_budget_ars_m=4987660, capital_credit_ars_m=457662))
    caba=pd.read_excel(cache/'caba-q2-current.xlsx').dropna(how='all')
    assert len(caba)==38756 and not caba.duplicated().any()
    selected=caba[caba.Eco.astype(int).astype(str).str.startswith(('21','22'))]
    records.append(row('CABA','2026-06-30','Administración Central y organismos descentralizados',
        'Acumulado al segundo trimestre. Se excluyen aplicaciones financieras (económico 23) de ambos importes. Se compara el crédito y el devengado del mismo archivo; no se mezcla con la presentación nacional del presupuesto inicial.',
        [source('caba-q2-current','Presupuesto ejecutado 2026, segundo trimestre','Hoja BASE 2T Gestion 2026; 38.756 partidas sin duplicados; Eco empieza en 21/22; columnas Vigente_Trim2_CONT y Devengado_Trim2_CONT.')],
        credit_ars_m=selected.Vigente_Trim2_CONT.sum()/1e6, accrued_ars_m=selected.Devengado_Trim2_CONT.sum()/1e6))
    save('data/current_budget_execution.json',dict(schema_version=1,reviewed_at=REVIEWED,unit='ARS millions',
        method='Crédito anual vigente y etapas acumuladas a la fecha indicada, en pesos corrientes. Cortes y coberturas propios: no constituye un ranking provincial ni acredita caja libre. Faltante es null, nunca cero.',records=records))
    # Official future projections. No inflation adjustment or invented FX rate.
    projections={}
    def projection(name,scope,note,sources,capital,interest,years,**extra):
        projections[name]=dict(as_of=None,reference_label='Presupuesto 2026 · proyección 2026–2028',scope=scope,
            interest_label='Intereses',note=note,sources=sources,
            rows=[dict(year=y,amortization_ars_m=c,interest_ars_m=i,total_ars_m=round(c+i,6)) for y,c,i in zip(years,capital,interest)])
        projections[name].update(extra)
    projection('Neuquén','Administración Provincial, sin ISSN · Presupuesto 2026',
        'Proyección presupuestaria 2026–2028, con intereses y comisiones. Usa los tipos de cambio del presupuesto; no descuenta pagos ni refinanciaciones posteriores. No hay fecha de valuación informada en esta tabla.',
        [source('nqn-message','Mensaje del presupuesto 2026, página PDF 96 (impresa 94)','Tabla Perfil de la Deuda Pública 2026–2028, fila TOTAL; transcripción visual, contrastada con AIF página PDF 103 (redondeado a millones).','ARS millions')],
        [307755.9,232813.2,209543.4],[125195.3,137471.4,130305.8],[2026,2027,2028],interest_label='Intereses y comisiones')
    sf=PdfReader(cache/'sf-pluri-official.pdf').pages[19].extract_text()
    for val in ['232.571.108.000','410.094.184.673','239.152.359.536']: assert val in sf
    projection('Santa Fe','Deuda pública provincial · Presupuesto plurianual 2026–2028',
        'Perfil publicado en el presupuesto plurianual. Capital e intereses del Anexo XVI; no se reemplazan por las aplicaciones financieras del AIF. No descuenta pagos posteriores ni constituye un flujo mensual actualizado.',
        [source('sf-pluri-official','Presupuesto plurianual 2026–2028, Anexo XVI','Páginas PDF 19–20, fila TOTAL SERVICIOS DE LA DEUDA. Importes en pesos; el documento explicita la moneda en el Anexo IV.')],
        [163330.371,199780.180211,44707.075211],[69240.737,210314.004462,194445.284325],[2026,2027,2028])
    save('data/debt/verified_forward_schedules.json',dict(reviewed_at=REVIEWED,projections=projections))
    print('Current budgets:',len(records),'Additional schedules:',len(projections))

if __name__=='__main__': build(Path(sys.argv[1]))

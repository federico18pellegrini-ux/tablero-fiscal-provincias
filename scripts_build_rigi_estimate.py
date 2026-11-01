"""Escenarios parciales RIGI: registro oficial, actos individuales y bases tributarias explícitas."""
import argparse
import datetime as dt
import hashlib
import html
import json
import re
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'nacion/data/rigi-sources'
OUT=ROOT/'nacion/data/rigi-estimate.json'
MONTHS={'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'setiembre':9,'octubre':10,'noviembre':11,'diciembre':12}
# Correspondencia revisada: orden del cuadro ARCA -> identificador Infoleg del registro Economía.
IDS=[431646,431504,431356,431089,429717,429238,428465,428357,428274,427918,427059,426429,426315,425734,425673,424514,424457,422390,420421,418673,416924,416877,415410,413550,412353,410830,408210]

def plain(raw):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]*>',' ',raw))).strip()

def customs_cost(investment,import_share,incremental_share,tariff):
    values=[investment,import_share,incremental_share,tariff]
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):return None
    if investment<0 or not all(0<=x<=1 for x in values[1:]):return None
    return investment*import_share*incremental_share*tariff

def build():
    sources=json.loads((SRC/'sources.json').read_text(encoding='utf8'))
    for x in sources:
        assert hashlib.sha256((SRC/x['file']).read_bytes()).hexdigest()==x['sha256'],x['file']
        x['path']='data/rigi-sources/'+x['file']
    urls={x['file']:x['url'] for x in sources}
    raw=(SRC/'registry-gviz.json').read_text(encoding='utf8')
    g,_=json.JSONDecoder().raw_decode(raw[raw.index('{'):])
    rows=[[c.get('v') if c else None for c in row['c']] for row in g['table']['rows']]
    headers=rows[0];registry={}
    for row in rows[2:]:
        r=dict(zip(headers,row));url=r['enlace'];identity=int(url.rsplit('-',1)[1])
        if identity not in registry:
            registry[identity]=dict(id=identity,name=r['nombre'].strip(),company=r['empresa'],sector=r['sector'],
                investment_usd_millions=float(r['inv-comprometida']),provinces=[],source_url=url)
        current=registry[identity]
        assert current['investment_usd_millions']==float(r['inv-comprometida'])
        if r['provincia'] not in current['provinces']:current['provinces'].append(r['provincia'])
    index=(SRC/'arca-projects.html').read_text(encoding='utf8')
    approved=[r for r in re.findall(r'<tr\b.*?</tr>',index,re.I|re.S) if 'norma.aspx' in r]
    assert len(approved)==len(IDS)==len(registry)==27
    for i,row in enumerate(approved):
        text=plain((SRC/f'arca-res-{i}.html').read_text(encoding='utf8'))
        cells=[plain(x) for x in re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.I|re.S)]
        assert len(cells)==6
        number=re.search(r'Resoluci[oó]n N[°º] ?(\d+/\d{4})',cells[-1]).group(1)
        assert number in text and 'ARTÍCULO 1' in text and 'APR' in text.upper()
        pub=re.search(r'B\.O\.:\s*(\d{2}/\d{2}/\d{4})',text).group(1)
        article2=re.search(r'ARTÍCULO 2.*?(?=ARTÍCULO 3|$)',text).group(0)
        match=re.search(r'(\d{1,2})[°º]? de ([a-z]+) (?:de )?(\d{4})',article2)
        date=dt.date(int(match[3]),MONTHS[match[2]],int(match[1])).isoformat() if match else None
        r=registry[IDS[i]]
        r.update(resolution=number,published=dt.datetime.strptime(pub,'%d/%m/%Y').date().isoformat(),
            accession_date=date,arca_project_name=cells[3],arca_province=cells[4],
            resolution_url=urls[f'arca-res-{i}.html'],resolution_file='data/rigi-sources/'+f'arca-res-{i}.html',
            checked_status='Registro y resolución ARCA conciliados',
            fiscal_cost_2027=None,annual_investment_2027_usd_millions=None)
        r['dividend_reduction_from']=dt.date(int(date[:4])+7,int(date[5:7]),int(date[8:10])).isoformat() if date else None
    projects=sorted(registry.values(),key=lambda x:(x['published'],x['id']))
    assert all(p['accession_date'] for p in projects)
    assert min(p['dividend_reduction_from'] for p in projects)>='2031-01-01'
    incentives=plain((SRC/'arca-incentives.html').read_text(encoding='utf8'))
    assert '25%' in incentives and '3,5%' in incentives and 'siete (7)' in incentives
    mining=plain((SRC/'mining-law.html').read_text(encoding='utf8'))
    assert re.search(r'ART[IÍ]CULO 21',mining) and 'importación' in mining
    scale=plain((SRC/'corporate-scale.html').read_text(encoding='utf8'))
    assert '2026' in scale and '73' in scale
    assert '94.076.795' in plain((SRC/'arca-res-26.html').read_text(encoding='utf8'))
    assert re.search(r'1[°º]? de octubre del? 2031',plain((SRC/'arca-res-0.html').read_text(encoding='utf8')))
    # Plan anual oficial sectorial; no se distribuye a cada proyecto por su peso en el stock.
    raw=plain((SRC/'official-rigi.html').read_text(encoding='utf8'))
    start=raw.rfind('[',0,raw.index('"year": "2024-01-02"'))
    plans,_=json.JSONDecoder().raw_decode(raw[start:])
    plan=next(p for p in plans if p['year'].startswith('2027'))
    keys=['energia','petroleo','mineria','siderurgia','infra','tecnologia']
    annual=sum(plan[k]['total'] for k in keys)
    scenarios=[]
    for name,imports,additional,rate in [('A',.20,.25,.02),('B',.35,.50,.07),('C',.50,.75,.14)]:
        scenarios.append(dict(name=name,import_share=imports,incremental_share=additional,tariff=rate,
            import_base_usd_millions=annual*imports*additional,
            cost_usd_millions=customs_cost(annual,imports,additional,rate)))
    return dict(schema_version=1,reviewed='2026-11-01',year=2027,
        estimate_status='Escenarios condicionales de derechos de importación; no estimación del costo total',
        official_fiscal_cost_2027=None,total_estimated_cost_2027=None,
        registry=dict(raw_territorial_rows=len(rows)-2,project_count=len(projects),
            investment_usd_millions=sum(p['investment_usd_millions'] for p in projects),
            last_publication=max(p['published'] for p in projects),projects=projects,
            method='Se cuenta cada resolución una vez. Los montos de Economía están publicados en millones de USD redondeados, son inversión comprometida total y no ejecución ni bases imponibles anuales.'),
        customs=dict(investment_2027_usd_millions=annual,scenarios=scenarios,
            formula='Plan anual × proporción importada × proporción que pagaría arancel sin RIGI × arancel medio contrafactual',
            assumptions='Las tres proporciones/tasas son supuestos de sensibilidad, no datos observados ni un intervalo estadístico. La proporción que pagaría descuenta arancel cero, origen Mercosur y exenciones previas, entre ellas Ley 24.196. No incluye tasa de estadística ni otros impuestos.',
            scope='Solo derechos de importación de las compras supuestas del plan sectorial 2027. No se reparte el monto por proyecto sin cronograma y NCM.'),
        tax_components=[
            dict(name='Derechos de importación',kind='Renuncia definitiva condicionada',value=None,reading='Se simulan con base importada y arancel incremental; requieren NCM, origen y beneficios previos.'),
            dict(name='Ganancias',kind='Menor alícuota y diferencias de base',value=None,reading='RIGI 25%; régimen general con escala 25/30/35%. Hasta USD 10 por USD 100 adicionales de ganancia imponible ubicada en el tramo marginal del 35%, manteniendo la base. No equivale a 10% de toda utilidad ni de la inversión.'),
            dict(name='Amortización acelerada',kind='Diferimiento',value=None,reading='Adelanta deducciones; depende de activos, vida útil, quebrantos y ganancias disponibles. No sumar el adelanto como pérdida definitiva.'),
            dict(name='IVA',kind='Diferimiento y efecto financiero',value=None,reading='Certificados evitan financiar ciertos créditos. Hace falta el saldo y el plazo de recupero sin RIGI; no imputar 21% de la inversión como costo definitivo.'),
            dict(name='Derechos de exportación',kind='Renuncia luego del plazo legal',value=None,reading='Dos años desde adhesión para exportación estratégica y tres para los demás. Además hacen falta exportaciones propias y alícuota vigente por producto.'),
            dict(name='Dividendos: baja de 7% a 3,5%',kind='Beneficio futuro',value=0,reading='La reducción requiere siete años desde adhesión. Ninguno de estos 27 proyectos cumple ese plazo en 2027. Este cero se limita a esa reducción, no al costo del RIGI.'),
            dict(name='Crédito por débitos y créditos y pagos al exterior',kind='Base adicional pendiente',value=None,reading='Requiere pagos bancarios, créditos computables bajo el régimen general, contratos y convenios; no sumar beneficios sin conciliar su interacción con Ganancias.')],
        vat_example=dict(credit_usd_millions=100,annual_discount_rate=.08,months_advanced=6,
            financial_value_usd_millions=100*(1-1.08**(-.5)),
            label='Ejemplo financiero hipotético sobre USD 100 millones de créditos, no costo observado ni sumable al escenario aduanero'),
        evidence_cases=[dict(project='Parque Solar El Quemado',resolution='1/2025',source_file='arca-res-26.html',
            foreign_supplier_payment_usd=94076795,reading='La resolución publica pagos previstos al exterior por USD 94.076.795; eso no identifica NCM ni prueba el arancel incremental.'),
            dict(project='Agua Rica',resolution='1854/2026',source_file='arca-res-0.html',
                construction_start='2027-11-01',operation_start='2031-10-01',reading='El inicio de operación previsto en 2031 impide inferir ganancias operativas de 2027 a partir del monto de inversión.')],
        missing=['Cronograma anual por proyecto y ejecución efectiva','Importaciones por NCM, origen y beneficios alternativos','Bases imponibles y quebrantos','Saldos IVA y plazos de recupero','Exportaciones propias y derechos vigentes'],sources=sources)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();data=build()
    if args.check:
        assert json.loads(OUT.read_text(encoding='utf8'))==data,'Regenerar estimación RIGI'
        print('RIGI: 27 resoluciones, registro sin duplicados y escenarios tributarios verificados.')
    else:OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Generado',OUT)

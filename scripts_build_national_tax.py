"""Gasto tributario: una misma publicación para comparar; originales y revisiones separados."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT/'nacion/data/tax-sources'
OUTPUT = ROOT/'nacion/data/tax-expenditures.json'

def build():
    sources = json.loads((SOURCES/'sources.json').read_text(encoding='utf8'))
    for s in sources:
        raw = (SOURCES/s['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == s['sha256'], s['file']
        s['path'] = 'data/tax-sources/'+s['file']
    # Millones de pesos y % PIB, cuadro 1 del Mensaje 2027, página PDF 44.
    series = [
        dict(year=2025,total=31609867.7,total_pct=3.72,norms=27231103.8,norms_pct=3.20,promotion=4378764.0,promotion_pct=.52),
        dict(year=2026,total=42153585.8,total_pct=3.69,norms=36669940.8,norms_pct=3.21,promotion=5483645.0,promotion_pct=.48),
        dict(year=2027,total=51914317.8,total_pct=3.67,norms=45692398.7,norms_pct=3.23,promotion=6221919.1,promotion_pct=.44)]
    text = PdfReader(SOURCES/'mensaje2027.pdf').pages[43].extract_text()
    for row in series:
        for k in ['total','norms','promotion']:
            assert f'{row[k]:,.1f}'.replace(',','X').replace('.',',').replace('X','.') in text
        assert abs(row['total']-row['norms']-row['promotion']) <= .11
        assert abs(row['total_pct']-row['norms_pct']-row['promotion_pct']) < .011
    # Normas del impuesto, no el total que también incluye regímenes promocionales.
    norms = [dict(name=n,before=a,after=b,delta_pp=round(b-a,2)) for n,a,b in [
        ('IVA',1.32,1.23),('Ganancias',.36,.41),('Seguridad social',.13,.19),
        ('Combustibles',.22,.32),('Internos',.01,.01),('Bienes personales',.03,.01),('Monotributo',1.13,1.07)]]
    promotion_text=PdfReader(SOURCES/'mensaje2027.pdf').pages[48].extract_text()
    for amount in ['1.790.257,3','1.846.643,0','377.380,6','842.556,0','1.560.295,4','2.496.746,3']:
        assert amount in promotion_text
    promotion=[dict(name=n,before=a,after=b,delta_pp=round(b-a,2)) for n,a,b in [
        ('Tierra del Fuego',.21,.13),('Economía del Conocimiento',.04,.06),('Fortalecimiento MiPyME',.18,.18)]]
    old = PdfReader(SOURCES/'mensaje2024.pdf')
    old_text = '\n'.join(p.extract_text() for p in old.pages)
    assert '8.234.343,0' in old_text and '2,34' in old_text and '5.166.420' in old_text
    revised = PdfReader(SOURCES/'gastos-2024-2026.pdf').pages[4].extract_text()
    assert '20.158.605,7' in revised and '3,45' in revised and '1,13' in revised
    assert 'etapas posteriores' in PdfReader(SOURCES/'mensaje2027.pdf').pages[41].extract_text()
    # HTML oficial: se toma la lista sectorial de planes aprobados, no los contadores
    # animados inicializados en cero ni la suma de subsectores redondeados por separado.
    raw = (SOURCES/'rigi-2026-11-01.html').read_text(encoding='utf8')
    plain = html.unescape(re.sub('<[^>]+>','',raw))
    start = plain.rfind('[',0,plain.index('"year": "2024-01-02"'))
    plans, _ = json.JSONDecoder().raw_decode(plain[start:])
    sectors = [('energia','Electricidad'),('petroleo','Petróleo y gas'),('mineria','Minería'),
               ('siderurgia','Siderurgia'),('infra','Infraestructura'),('tecnologia','Tecnología')]
    rows=[]
    for year in [2026,2027]:
        r=next(x for x in plans if x['year'].startswith(str(year)))
        values=[dict(id=k,name=n,usd_millions=r[k]['total']) for k,n in sectors]
        rows.append(dict(year=year,sectors=values,total_usd_millions=sum(x['usd_millions'] for x in values)))
    return dict(schema_version=1,reviewed='2026-11-01',unit='ARS millones corrientes; porcentajes del PIB',
        scope='Estimaciones nacionales de gasto tributario, no gasto devengado de la Administración Nacional',
        comparison=dict(publication='Mensaje del Proyecto de Presupuesto 2027',pdf_page=44,years=series,norms_by_tax=norms,promotion_selection=promotion,
            total_delta_pp=round(series[-1]['total_pct']-series[0]['total_pct'],2),
            rounding='Las sumas de porcentajes publicados pueden diferir por redondeo; el total conserva la cifra oficial.'),
        reference_2024=dict(original=dict(total_pct=2.34,norms_pct=1.73,promotion_pct=.61,publication='Proyecto 2024, septiembre 2023'),
            revised=dict(total_pct=3.45,norms_pct=2.98,promotion_pct=.47,monotributo_pct=1.13,publication='Informe 2024–2026, septiembre 2025'),
            comparable_growth=False,reading='El 2,34% y el 3,45% son estimaciones distintas de 2024. El cambio de cobertura y las revisiones impiden tratar su diferencia como nuevas exenciones. El Monotributo ya figura en 2024 revisado.',
            separata=dict(subset_pct=1.47,amount_ars_millions=5166420,updated_2027_amount=None,
                reading='Subtotal propuesto para revisión legislativa en el proyecto 2024. Ya forma parte del gasto tributario: no se suma de nuevo ni se traslada a 2027 manteniendo 1,47% fijo.')),
        rigi=dict(fiscal_cost_2027=None,status='Sin cuantificación oficial en el Mensaje 2027',investment_status='Planes de inversión publicados; no ejecución observada',
            plans=rows,method='Total calculado sumando los seis sectores publicados, incluida Tecnología. No se suman subsectores: pueden tener diferencias de redondeo. La inversión no es una base para aplicar una tasa fiscal arbitraria.',
            measurement=[dict(tax='Ganancias',need='Utilidades imponibles, alícuotas, amortización acelerada, quebrantos y año de inicio de producción.'),
                dict(tax='IVA',need='Compras, certificados y recuperos; distinguir alivio definitivo de adelantos o diferimientos.'),
                dict(tax='Aduana y exportaciones',need='Importaciones, aranceles, exportaciones y fecha de vigencia de cada beneficio.')],
            conclusion='Para evaluar el régimen hay que medir el beneficio por impuesto y año, y contrastarlo con inversión efectivamente realizada, empleo y exportaciones. Un costo sin publicar no equivale a cero.'),
        debate='La evaluación fiscal debe abarcar tanto las partidas que se pagan como los beneficios que reducen ingresos. Recomendamos revisar cada beneficio por objetivo, beneficiarios, costo, plazo y resultados; el monto estimado no es recaudación automáticamente recuperable.',sources=sources)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    value=build()
    if args.check:
        assert json.loads(OUTPUT.read_text(encoding='utf8'))==value,'Regenerar gasto tributario'
        print('Gasto tributario: originales, períodos, apertura, planes RIGI y faltantes verificados.')
    else:
        OUTPUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('Generado',OUTPUT)

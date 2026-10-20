"""Fill historical gaps from preserved official originals; never replace existing observations."""
import csv, hashlib, json, unicodedata, re
from collections import defaultdict
from pathlib import Path
import openpyxl

ROOT=Path(__file__).resolve().parent
SOURCES=ROOT/'data/revenue-history-sources'
def read(path,**kwargs):
    with path.open(newline='',**kwargs) as f:return list(csv.DictReader(f,delimiter=';' if kwargs.get('encoding')=='latin1' else ','))
def write(path,rows):
    with path.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
def build():
    universe=json.loads((ROOT/'dashboard_manifest.json').read_text(encoding='utf8'))['province_universe']
    names={norm(p):p for p in universe};names.update({'c.a.b.a':'CABA','sgo. del estero':'Santiago del Estero'})
    original=read(SOURCES/'serie_ron_2003_2025.csv',encoding='latin1')
    groups=defaultdict(list)
    for r in original:
        if r['provincia'] in names:groups[names[r['provincia']],r['ano']].append(r)
    path=ROOT/'serie_ron_2003_2025_normalizado.csv';rows=read(path,encoding='utf8')
    totals={'T O T A L','T O T A L | (1) + (2)','T O T A L | (1) + (2) + (3)','Total | (1) + (2)'}
    checked=0
    for r in rows:
        if r['category'] not in totals:continue
        expected=sum(float(x['monto'].replace(',','.')) for x in groups[r['province'],r['year']])
        assert abs(expected-float(r['value_millions']))<.02,(r,expected)
        checked+=1
    additions=[]
    for (province,year),group in groups.items():
        existing=[r for r in rows if r['province']==province and r['year']==year]
        total=sum(float(x['monto'].replace(',','.')) for x in group)
        cfi=[x for x in group if x['impuesto'].startswith('coparticipacion federal de impuestos')]
        assert len(cfi)==1,(province,year)
        for category,value in [('Total | (1) + (2)',total),('CFI | Neta',float(cfi[0]['monto'].replace(',','.')))]:
            present=any((r['category'] in totals if category in totals else r['category_normalized']==category) for r in existing)
            if not present:additions.append(dict(province=province,source='serie_ron_2003_2025.csv',category=category,value_millions=value,year=year,period_type='year',period=year,category_normalized=category))
    write(path,rows+additions)
    workbook=openpyxl.load_workbook(SOURCES/'SP_IP_Reca_concepto.xlsx',read_only=True,data_only=True)
    annual=defaultdict(list);year=None
    months=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    monthly=[]
    for row in workbook.worksheets[0].values:
        row=list(row)
        if isinstance(row[0],str):row[0]=re.sub(r'2$', '', row[0].strip())
        if isinstance(row[0],int) and 1900<=row[0]<=2026:year=row[0]
        elif year is not None and year>=1997 and row[0] in months and isinstance(row[1],(int,float)):
            annual[year].append(row[0]);monthly.append(dict(province='CABA',period=f'{year}-{months.index(row[0])+1:02}',value_millions=row[1]))
    assert all(len(set(ms))==len(ms) for ms in annual.values())
    write(ROOT/'data/caba_historical_revenue_monthly.csv',monthly)
    path=ROOT/'serie_top_1984_2024_normalizado.csv';rows=read(path,encoding='utf8');own=[]
    book=openpyxl.load_workbook(SOURCES/'serie_top_1984_2025_0.xlsx',read_only=True,data_only=True)
    cells={};aliases={'C.A.B.A.':'CABA','Sgo. del Estero':'Santiago del Estero','Tierra Del Fuego':'Tierra del Fuego'}
    for tax in book.sheetnames:
        sheet=list(book[tax].values);years={i:int(y) for i,y in enumerate(sheet[7]) if isinstance(y,(int,float)) and 1984<=y<=2025}
        for row in sheet[8:]:
            province=aliases.get(row[1],row[1])
            if province not in universe:continue
            for col,year in years.items():
                value=row[col]
                if isinstance(value,(int,float)):cells[province,str(year),tax]=float(value)
    for (province,year,tax),value in cells.items():
        if tax=='Total':
            components=[cells.get((province,year,k)) for k in book.sheetnames if k!='Total']
            if all(v is not None for v in components):assert abs(sum(components)-value)<.02,(province,year)
        previous=next((r for r in rows if r['province']==province and r['year']==year and r['tax']==tax),None)
        if previous:continue
        own.append(dict(province=province,source='serie_top_1984_2025_0.xlsx',year=year,tax=tax,value_millions=value))
    write(path,rows+own)
    audit={'date':'2026-10-20','ron_existing_totals_checked':checked,'ron_added':additions,'own_observations_added':len(own),'own_totals_added':[{'province':r['province'],'year':r['year']} for r in own if r['tax']=='Total'],
           'sources':[{'file':p.name,'url':('https://www.estadisticaciudad.gob.ar/eyc/wp-content/uploads/2026/07/' if p.suffix=='.xlsx' and p.name.startswith('SP_') else 'https://www.argentina.gob.ar/sites/default/files/')+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in SOURCES.iterdir() if p.is_file()],
           'caba_scope':'Histórico publicado: DNAP 1984–2025, coherente con las otras provincias. IDECBA preservado como contraste, sin mezclar bases. Rótulo 1988 entre 1997 y 1999 en IDECBA: excluido de su extracción mensual.',
           'ron_scope':'Suma de regímenes del archivo DNAP; incluye compensación cuando existe. CFI anterior a 2006 conserva la definición legal del año.',
           'retrieval':'RON: copia oficial preservada y verificada el 19/10. CABA: descargada el 20/10. No se agregaron meses 2026.'}
    (ROOT/'data/revenue_history_completion.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'checked':checked,'ron_added':len(additions),'own_observations_added':len(own)}))
if __name__=='__main__':build()

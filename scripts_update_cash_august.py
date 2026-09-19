"""Import the official August SPN cash workbook; preserve monthly CPI and vintages."""
import csv
import hashlib
import json
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'nacion/data/gestion'
SOURCE = ROOT / 'nacion/data/management-sources/imig-agosto2026.xlsx'
URL = 'https://www.argentina.gob.ar/sites/default/files/2026/09/imig_agosto_2026_0.xlsx'
ROWS = dict(zip(['ingresos_totales','ingresos_tributarios','rentas_propiedad','otros_ingresos_corrientes','ingresos_capital','gasto_primario','prestaciones_sociales','subsidios_economicos','funcionamiento_y_otros','transferencias_corrientes_provincias','universidades','otros_gastos_corrientes','gasto_capital','resultado_primario','intereses_netos','resultado_financiero'],[8,9,19,22,26,28,30,37,41,44,49,50,52,72,74,76]))

def run():
    load=lambda n:json.loads((RAW/(n+'.json')).read_text(encoding='utf8'))
    workbook=openpyxl.load_workbook(SOURCE,data_only=True)
    monthly_sheet=workbook['Mensualizacion']; comparison_sheet=workbook['Agosto']
    assert comparison_sheet['G6'].value.strftime('%Y-%m')=='2026-08'
    ipc={r['periodo']:r['indice'] for r in load('ipc_observado')}
    monthly=[r for r in load('resultado_fiscal_caja_mensual') if r['periodo']<'2026-01']
    for key,row in ROWS.items():
        for month in range(1,9):
            cell=monthly_sheet.cell(row,month+6); value=cell.value; period=f'2026-{month:02}'
            assert isinstance(value,(int,float)),cell.coordinate
            monthly.append(dict(periodo=period,indicador=key,nominal_millones=value,
                real_agosto2026=value*ipc['2026-08']/ipc[period],celda=f'Mensualizacion!{cell.coordinate}',
                archivo=SOURCE.name,comparable_2025_2026=key not in ['transferencias_corrientes_provincias','otros_gastos_corrientes']))
    comparisons=[]
    for key,row in ROWS.items():
        item={'indicador':key}; real={}; comparable=True
        for year,col,acc in [(2026,7,12),(2025,8,13)]:
            selected=[r for r in monthly if r['indicador']==key and f'{year}-01'<=r['periodo']<=f'{year}-08']
            assert len(selected)==8
            published=comparison_sheet.cell(row,acc).value
            delta=sum(r['nominal_millones'] for r in selected)-published
            if abs(delta)>1:
                assert key in ['transferencias_corrientes_provincias','otros_gastos_corrientes'],(key,year,delta)
                comparable=False
            item[f'agosto_{year}']=comparison_sheet.cell(row,col).value
            item[f'enero_agosto_{year}']=published
            real[year]=sum(r['real_agosto2026'] for r in selected)
        for year in (2025,2026):item[f'enero_agosto_real_{year}']=real[year] if comparable else None
        item['cambio_real_acumulado_millones']=real[2026]-real[2025] if comparable else None
        item['variacion_real_acumulada_pct']=(real[2026]/real[2025]-1)*100 if comparable and real[2025]>0 and not key.startswith('resultado_') else None
        item['estado_comparacion_real_acumulada']='Comparable' if comparable else 'Reclasificación pendiente de conciliación'
        comparisons.append(item)
    by={r['indicador']:r for r in comparisons}
    for year in (2025,2026):
        k=f'enero_agosto_{year}'
        assert abs(by['ingresos_totales'][k]-by['gasto_primario'][k]-by['resultado_primario'][k])<1
        assert abs(by['resultado_primario'][k]-by['intereses_netos'][k]-by['resultado_financiero'][k])<1
    catalog=load('catalogo')
    source={'file':SOURCE.name,'url':URL,'bytes':SOURCE.stat().st_size,'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'retrieved_at':'2026-09-19','path':'data/management-sources/'+SOURCE.name}
    for name,rows in [('resultado_fiscal_caja_mensual',monthly),('resultado_fiscal_comparacion',comparisons)]:
        (RAW/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
        with (RAW/(name+'.csv')).open('w',encoding='utf8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        entry=next(r for r in catalog if r['dataset']==name)
        entry['method']=entry['method'].replace('y julio utilizan','y agosto utilizan')
        entry['rows']=len(rows);entry['scope']='Sector Público Nacional, base caja. Comparación enero–agosto 2026/2025.'
        entry['sources']=[source]+[s for s in entry['sources'] if s['file']!=SOURCE.name]
        for ext in ('json','csv'):entry['files'][ext]['sha256']=hashlib.sha256((RAW/(name+'.'+ext)).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    (RAW/'catalogo.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    print('August cash imported and reconciled:',by['resultado_financiero']['enero_agosto_2026'])

if __name__=='__main__':run()

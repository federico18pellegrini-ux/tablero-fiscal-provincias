"""Extract all supplied fiscal reports, preserving source vintages and units.
Usage: python scripts_build_fiscal_archive.py REPORT_FOLDER CACHE_FOLDER
Source PDFs remain local. Annual annex ratios are not monetary flows.
"""
import csv,hashlib,json,re,sys,unicodedata
from pathlib import Path
from scripts_build_fiscal_history import ALIASES,FIELDS
ROOT=Path(__file__).resolve().parent
ORDER=['Buenos Aires','Catamarca','CABA','Córdoba','Corrientes','Chaco','Chubut','Entre Ríos','Formosa','Jujuy','La Pampa','La Rioja','Mendoza','Misiones','Neuquén','Río Negro','Salta','San Juan','San Luis','Santa Cruz','Santa Fe','Santiago del Estero','Tierra del Fuego','Tucumán']
def plain(x):return ''.join(c for c in unicodedata.normalize('NFD',x.lower()) if unicodedata.category(c)!='Mn')
def canonical(x):return ALIASES.get(x,x)
def latest(rows,keys):
    selected={}
    for r in sorted(rows,key=lambda r:r['publication_date']):selected[tuple(r[k] for k in keys)]=r
    return list(selected.values())

def build(folder,cache):
    import pdfplumber
    cache.mkdir(parents=True,exist_ok=True)
    ranks=[];annual=[];ltm=[];reports=[];exceptions=[]
    for path in sorted(folder.glob('*.pdf')):
        label=re.search(r'Provincias (\d)T(\d{2})',path.name)
        if not label:raise ValueError('Unrecognized report '+path.name)
        period=f'20{label[2]}-Q{label[1]}';digest=hashlib.sha256(path.read_bytes()).hexdigest()
        saved=cache/(digest+'.json')
        if saved.exists():pages=json.loads(saved.read_text(encoding='utf-8'))
        else:
            with pdfplumber.open(path) as pdf:pages=[p.extract_text() or '' for p in pdf.pages]
            saved.write_text(json.dumps(pages,ensure_ascii=False),encoding='utf-8')
        meta=dict(report_period=period,publication_date=path.name[:10],source_sha256=digest)
        report=dict(**meta,filename=path.name,pages=len(pages));before=(len(ranks),len(annual),len(ltm))
        for line in pages[7].splitlines():
            m=re.match(r'^(.+?)\s+(-?\d[\d.]*(?:\s+-?\d[\d.]*){14})$',line)
            if not m or m[1]=='TOTAL':continue
            province=canonical(m[1]);assert province in ORDER,province
            values=[int(v.replace('.','')) for v in m[2].split()];assert len(values)==15
            v=dict(zip(FIELDS,values));residuals=[sum(values[:5])-v['income'],sum(values[6:11])-v['primary_spend'],v['income']-v['primary_spend']-v['primary'],v['primary']+v['interest_signed']-v['financial']]
            assert max(map(abs,residuals))<=2,(period,province,residuals)
            ltm.append(dict(**meta,province=province,period=period,source_page=8,**v))
        ranklines=pages[23].splitlines();header=next(l for l in ranklines if l.startswith('Provincia '));quarters=re.findall(r'([1-4])T',header)
        end=int(label[2])+2000;end_index=end*4+int(label[1])-1
        periods=[f'{i//4}-Q{i%4+1}' for i in range(end_index-len(quarters)+1,end_index+1)]
        assert [str(int(p[-1])) for p in periods]==quarters
        for line in ranklines:
            m=re.match(r'^(.+?)\s+((?:\d+\s+){20,}\d+)$',line)
            if not m:continue
            province=canonical(m[1]);assert province in ORDER,province
            values=list(map(int,m[2].split()));assert len(values)==len(periods),(period,province,len(values))
            for p,v in zip(periods,values):
                assert 0<=v<=24
                if v==0:exceptions.append(dict(**meta,province=province,period=p,source_page=24,reason="Source rank is zero: unavailable, not a valid rank"))
                ranks.append(dict(**meta,province=province,period=p,rank=v or None,source_page=24))
        for i,text in enumerate(pages[26:]):
            # Four source pages have rows closer than the default PDF text tolerance.
            # Preserve a separate fine-layout cache and reparse the actual PDF.
            fine=cache/(digest+f'.annex-{27+i}.txt')
            if fine.exists():text=fine.read_text(encoding='utf-8')
            elif (period,27+i) in {('2021-Q4',49),('2022-Q4',33),('2023-Q2',46),('2024-Q1',35)}:
                with pdfplumber.open(path) as pdf:text=pdf.pages[26+i].extract_text(y_tolerance=1) or ''
                fine.write_text(text,encoding='utf-8')
            heading=plain(' '.join(text.splitlines()[:9]))
            if not text.strip():continue
            if 'datos homogeneos' not in heading:continue
            if 'ciudad de buenos aires' in heading:province='CABA'
            else:province=next((p for p in ORDER if plain(p) in heading),None)
            if province is None:raise ValueError(f'Unknown annex jurisdiction: {period} page {27+i}: {heading}')
            header=next((l for l in text.splitlines() if 'Concepto' in l and 'LTM' in l),None)
            if not header:
                exceptions.append(dict(**meta,province=province,source_page=27+i,reason='No annual annex table header'));continue
            years=re.findall(r'\b(20\d{2})\b',header);assert 3<=len(years)<=6,(period,header)
            # All fifteen table rows precede the lower charts; extra chart labels
            # at right are excluded by taking only the annual columns, before LTM.
            lines=[]
            for line in text.splitlines()[text.splitlines().index(header)+1:]:
                vals=re.findall(r'(-?\d+,\d+)%',line)
                if len(vals)>=len(years)+1:lines.append(vals[:len(years)])
                if len(lines)==15:break
            if len(lines)!=15:
                exceptions.append(dict(**meta,province=province,source_page=27+i,reason=f'Incomplete annual table: {len(lines)} of 15 rows'));continue
            for j,year in enumerate(years):
                values=[float(v[j].replace(',','.')) for v in lines];v=dict(zip(FIELDS,values))
                residuals=[sum(values[:5])-100,sum(values[6:11])-v['primary_spend'],100-v['primary_spend']-v['primary'],v['primary']+v['interest_signed']-v['financial']]
                if max(map(abs,residuals))>.31:
                    exceptions.append(dict(**meta,province=province,year=year,source_page=27+i,reason='Annex identity discrepancy',residuals=residuals));continue
                annual.append(dict(**meta,province=province,year=year,source_page=27+i,**v))
        report.update(rank_observations=len(ranks)-before[0],annual_observations=len(annual)-before[1],ltm_observations=len(ltm)-before[2]);reports.append(report)
        print(period,report['rank_observations'],report['annual_observations'],report['ltm_observations'],flush=True)
    existing=json.loads((ROOT/'data/fiscal_history.json').read_text(encoding='utf-8'))['rows'];index={(r['province'],r['period']):r for r in existing}
    assert len(ltm)==len(existing),(len(ltm),len(existing))
    for r in ltm:
        assert all(r[k]==index[r['province'],r['period']][k] for k in FIELDS),(r['province'],r['period'])
    payload=dict(reviewed_at='2026-09-06',method='Última versión disponible por indicador y período; se conservan todas las versiones extraídas. Ranking: posición publicada, no mide calidad de gobierno. Anexos: componentes como porcentaje de ingresos totales nominales de cada año completo; no son pesos ni tasas de crecimiento real. No se digitalizan puntos sin cifra explícita de los gráficos.',reports=reports,annual_ratios=latest(annual,['province','year']),rank_history=latest(ranks,['province','period']),annual_vintages=annual,rank_vintages=ranks,exceptions=exceptions,ltm_reconciliation='All 15 fields match the existing fiscal history exactly')
    vintages={key:payload.pop(key) for key in ['annual_vintages','rank_vintages']}
    (ROOT/'data/fiscal_archive_vintages.json').write_text(json.dumps(vintages,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (ROOT/'data/fiscal_archive.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    for name,key in [('fiscal_annual_history.csv','annual_ratios'),('fiscal_rank_history.csv','rank_history')]:
        with (ROOT/'data'/name).open('w',encoding='utf-8-sig',newline='') as output:
            writer=csv.DictWriter(output,fieldnames=list(payload[key][0]));writer.writeheader();writer.writerows(payload[key])
    print('TOTAL',len(payload['annual_ratios']),len(payload['rank_history']),'exceptions',len(exceptions))
    return payload
if __name__=='__main__':build(Path(sys.argv[1]),Path(sys.argv[2]))

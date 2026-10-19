"""Import validated monthly TOP vintages, preserving PBA's reconciled 2025 source."""
import argparse,csv,hashlib,json,shutil,calendar
from pathlib import Path
import scripts_regenerate_2026 as base
ROOT=Path(__file__).resolve().parent
def read(name):return list(csv.DictReader((ROOT/name).open(encoding='utf-8')))
def save(name,data):(ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def build(old_path,new_path,reviewed):
 universe=base.manifest_universe();old,cov25=base.import_top(old_path,universe,2025);new,cov26=base.import_top(new_path,universe,2026)
 assert all(len(cov25[p])==12 for p in universe)
 prior=read('top_mensual_2025_normalizado.csv');pba=[r for r in prior if r['province']=='Buenos Aires'];lookup={(r['period'],r['tax']):float(r['value_millions']) for r in pba}
 for r in old:
  if r['province']=='Buenos Aires':assert abs(lookup[r['period'],r['tax']]-r['value_millions'])<.02
 old=[r for r in old if r['province']!='Buenos Aires']+pba
 sources=[]
 folder=ROOT/'data/top_sources';folder.mkdir(exist_ok=True)
 for p in [old_path,new_path]:
  dest=folder/p.name;shutil.copyfile(p,dest);raw=dest.read_bytes();sources.append(dict(file=dest.relative_to(ROOT).as_posix(),url='https://www.argentina.gob.ar/sites/default/files/'+p.name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
 before=read('top_mensual_2026_normalizado.csv');prior_values={(r['province'],r['period'],r['tax']):float(r['value_millions']) for r in before}
 changes=[dict(province=r['province'],period=r['period'],tax=r['tax'],before=prior_values.get((r['province'],r['period'],r['tax'])),after=r['value_millions']) for r in new if (r['province'],r['period'],r['tax']) not in prior_values or abs(prior_values[r['province'],r['period'],r['tax']]-r['value_millions'])>.01]
 base.write_csv(base.TOP_OUTPUT,list(new[0]),new);base.write_csv(ROOT/'top_mensual_2025_normalizado.csv',list(old[0]),old)
 base.write_pba_files(new,[],new_path,Path('unused'),write_ron=False)
 url=sources[1]['url'];canonical=[dict(province=r['province'],period=r['period'],tax=r['tax'],value_millions=r['value_millions'],price_basis='pesos_corrientes',evidence_status='auditado',source_file=r['source'],source_url=url) for r in new]
 base.write_csv(ROOT/'data/recaudacion_propia.csv',list(canonical[0]),canonical)
 cov=read('data/cobertura.csv')
 for r in cov:
  if r['dataset']=='recaudacion_propia_2026':
   periods=cov26[r['province']];r.update(first_period=min(periods),last_period=max(periods),months_count=len(periods),coverage_status='completa' if max(periods)==r['expected_through'] else 'rezagada')
 base.write_csv(ROOT/'data/cobertura.csv',list(cov[0]),cov)
 meta=json.loads((ROOT/'data/meta.json').read_text(encoding='utf-8'));meta['sources']['recaudacion_propia_2026'].update(url=url,max_period=max(p for ps in cov26.values() for p in ps),pba_max_period=max(cov26['Buenos Aires']));meta['sources']['recaudacion_propia_2025']=sources[0];save('data/meta.json',meta)
 manifest=json.loads((ROOT/'dashboard_manifest.json').read_text(encoding='utf-8'));manifest['as_of_by_block']['recaudacion_propia_pba']='2026-08-31';manifest['notes']['monthly_scope_2025_prepared']='RON y recaudación propia 2025: 24 jurisdicciones y 12 meses conciliados. Gasto mensual comparable pendiente, sin imputaciones.';save('dashboard_manifest.json',manifest)
 save('data/top_comparable_import.json',dict(reviewed_at=reviewed,sources=sources,coverage2025=cov25,coverage2026=cov26,changes=changes,method='Cinco componentes mutuamente excluyentes conciliados con TOTAL. Base 2025 PBA conserva su original provincial, conciliado con DNAP. Importes en millones de pesos corrientes.'))
 print('TOP 2025: 24 x 12 meses. TOP 2026:',len(new),'filas. Nuevas/revisadas:',len(changes))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--previous',type=Path,required=True);p.add_argument('--current',type=Path,required=True);p.add_argument('--reviewed',required=True);a=p.parse_args();build(a.previous,a.current,a.reviewed)

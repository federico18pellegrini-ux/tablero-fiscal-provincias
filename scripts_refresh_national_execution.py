"""Refresh execution independently of the frozen project comparison baseline."""
import argparse,hashlib,json,os,shutil,zipfile
from pathlib import Path
import national_execution_import as parser
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'nacion/data';RAW=DATA/'gestion'
def load(p):return json.loads(p.read_text('utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def run(originals,downloads,work,cutoff):
 work.mkdir(parents=True,exist_ok=True);out=work/'normalized';out.mkdir(exist_ok=True)
 archive=DATA/'execution-sources';archive.mkdir(exist_ok=True)
 old_sources=load(RAW/'fuentes.json');sources={s['file']:s.copy() for s in old_sources}
 names=['credito-anual-2026.zip','credito-mensual-2026.zip','recursos-anual-2026.zip','recursos-mensual-2026.zip','totales-de-presupuesto.zip','ejecucion-fisica-trimestre-1-2026.zip','ejecucion-fisica-trimestre-2-2026.zip']
 for name in names:
  matches=list(downloads.glob('*'+name));assert len(matches)==1,(name,matches)
  p=archive/name;shutil.copyfile(matches[0],p);s=sources[name];s.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),retrieved_at=cutoff,path='data/execution-sources/'+name)
  with zipfile.ZipFile(p) as z:
   members=[n for n in z.namelist() if n.endswith('.csv')];assert len(members)==1
   (work/(name[:-4]+'.csv')).write_bytes(z.read(members[0]))
 for name in ['credito-mensual-2025.csv','recursos-mensual-2025.csv']:
  dest=work/name
  if not dest.exists():os.link(originals/name,dest)
 parser.RAW=work;parser.OUT=out;parser.SOURCES=sources;parser.CUTOFF=cutoff
 parser.IPC={r['periodo']:r['indice'] for r in load(RAW/'ipc_observado.json')};parser.ANCHOR=parser.IPC['2026-08']
 parser.build_budget();parser.build_revenue();parser.build_physical()
 failures=[r for r in parser.CHECKS if r['required'] and not r['pass_']];assert not failures,failures
 shutil.copyfile(out/'execution-latest.json',DATA/'execution-latest.json')
 # Retain the archived 15/09 program identities and amounts for 2027 mapping checks.
 baseline=archive/'project-baseline-execution.json'
 if not baseline.exists():save(baseline,{'total':load(RAW/'gasto_etapas_total.json'),'programs':load(RAW/'gasto_etapas_programa.json'),'jurisdictions':load(RAW/'gasto_etapas_jurisdiccion.json'),'territories':load(RAW/'gasto_etapas_territorio.json')})
 catalog={r['dataset']:r for r in load(RAW/'catalogo.json')}
 for item in parser.CATALOG:
  name=item['dataset'];entry={**catalog[name],**item,'files':{}}
  for ext in ['csv','json']:
   p=RAW/(name+'.'+ext);shutil.copyfile(out/p.name,p);entry['files'][ext]={'path':'data/gestion/'+p.name,'sha256':digest(p)}
  catalog[name]=entry
 save(RAW/'catalogo.json',list(catalog.values()));save(RAW/'fuentes.json',list(sources.values()))
 shutil.copyfile(archive/'recursos-mensual-2026.zip',DATA/'revenue-sources/recursos-mensual-2026.zip')
 save(archive/'refresh.json',{'reviewed':cutoff,'execution_cutoff':cutoff,'partial_month':cutoff[:7],'real_comparison_through':'2026-08','checks':parser.CHECKS,'sources':[sources[n] for n in names]})
 print('Execution datasets refreshed:',len(parser.CATALOG),'checks:',len(parser.CHECKS))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--originals',type=Path,required=True);p.add_argument('--downloads',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--cutoff',required=True);a=p.parse_args();run(a.originals,a.downloads,a.work,a.cutoff)

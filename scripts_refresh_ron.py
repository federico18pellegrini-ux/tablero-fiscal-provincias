"""Refresh the shared RON series without replacing TOP or inventing monthly IPC."""
import argparse,calendar,csv,hashlib,io,json,re,shutil
from datetime import datetime,timezone
from collections import defaultdict
from pathlib import Path
import scripts_regenerate_2026 as importer
ROOT=Path(__file__).resolve().parent
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def save(p,d):
 (ROOT/p).parent.mkdir(parents=True,exist_ok=True)
 (ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def readcsv(p):return list(csv.DictReader((ROOT/p).open(encoding='utf8')))
def build(source,url,reviewed):
 universe=importer.manifest_universe(); rows,coverage=importer.import_ron(source,universe)
 cutoff=max(p for periods in coverage.values() for p in periods)
 expected=[f'2026-{m:02}' for m in range(1,int(cutoff[-2:])+1)]
 assert len(coverage)==24 and all(sorted(set(v))==expected for v in coverage.values())
 totals={}
 for province in universe:
  for period in expected:
   get=lambda k:importer.select_ron(rows,province,period,k)
   total,base,comp=[get(k) for k in ['Total | (1) + (2)','Total | Recursos | Origen Nacional | (1)','Compensación Consenso Fiscal']]
   assert total is not None and base is not None,(province,period)
   # CABA has no compensation cell; retain that absence in the published records.
   assert abs(total-base-(comp if comp is not None else 0))<.01,(province,period)
   totals[province,period]=total
  consolidated=importer.select_ron(rows,province,'CONS','Total | (1) + (2)')
  assert abs(sum(totals[province,p] for p in expected)-consolidated)<.1,province
 original=ROOT/'data/ron_sources'/source.name;original.parent.mkdir(exist_ok=True)
 if source.resolve()!=original.resolve():shutil.copyfile(source,original)
 info={'url':url,'path':str(original.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'bytes':original.stat().st_size,'reviewed':reviewed,'period':cutoff,'unit':'ARS millones'}
 importer.write_csv(importer.RON_OUTPUT,list(rows[0]),rows)
 # The existing helper also writes TOP: preserve its bytes and provenance exactly.
 top_bytes=importer.PBA_TOP_OUTPUT.read_bytes()
 try:importer.write_pba_files(readcsv('top_mensual_2026_normalizado.csv'),rows,Path('unchanged'),original)
 finally:importer.PBA_TOP_OUTPUT.write_bytes(top_bytes)
 selected={'CFI | Neta','Compensación Consenso Fiscal','Total | (1) + (2)'}
 canonical=[{'province':r['province'],'period':r['period'],'category':r['category_normalized'],'value_millions':r['value_millions'],'price_basis':'pesos_corrientes','evidence_status':'auditado','source_file':original.name,'source_url':url} for r in rows if r['period_type']=='month' and r['category_normalized'] in selected]
 importer.write_csv(importer.CANONICAL_RON_OUTPUT,list(canonical[0]),canonical)
 cov=readcsv('data/cobertura.csv')
 for r in cov:
  if r['dataset']=='transferencias_nacion_2026':r.update(last_period=cutoff,months_count=len(expected),expected_through=cutoff,coverage_status='completa')
 importer.write_csv(importer.COVERAGE_OUTPUT,list(cov[0]),cov)
 stamp=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
 meta=load('data/meta.json');meta['generated_at']=stamp;meta['sources']['transferencias_nacion_2026'].update(url=url,max_period=cutoff,pba_max_period=cutoff,reviewed_at=reviewed,original=info);save('data/meta.json',meta)
 manifest=load('dashboard_manifest.json');date=cutoff+'-'+str(calendar.monthrange(2026,int(cutoff[-2:]))[1])
 manifest['data_cutoff']=max(manifest['data_cutoff'],date);manifest['as_of_by_block']['transferencias_nacion_2026']=date
 manifest['generated_at']=stamp
 save('dashboard_manifest.json',manifest)
 index=ROOT/'index.html';s=index.read_text(encoding='utf8')
 s=re.sub(r'^const EMBEDDED_MANIFEST = .*$',lambda m:'const EMBEDDED_MANIFEST = '+json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+';',s,flags=re.M);index.write_text(s,encoding='utf8')
 ipc={r['period'] for r in readcsv('data/ipc_national_index.csv')}
 previous={(r['province'],r['period']):float(r['value_millions']) for r in readcsv('informacion_consolidada_2025_normalizado.csv') if r['category_normalized']=='Total | (1) + (2)'}
 latest=[]
 for province in universe:
  current=sum(totals[province,p] for p in expected);prev=[previous.get((province,p.replace('2026','2025'))) for p in expected]
  latest.append({'province':province,'month_nominal':totals[province,cutoff],'ytd_nominal':current,'ytd_nominal_change_pct':100*(current/sum(prev)-1) if all(v is not None for v in prev) and sum(prev)>0 else None})
 save('data/ron_latest.json',{'reviewed':reviewed,'period':cutoff,'real_available_through':max(p for p in expected if p in ipc),'source':info,'rows':latest})
 print(f'{len(universe)} jurisdicciones, {len(expected)} meses, {len(rows)} filas conciliadas; IPC observado hasta {max(ipc)}')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--url',required=True);p.add_argument('--reviewed',required=True);a=p.parse_args();build(a.source,a.url,a.reviewed)

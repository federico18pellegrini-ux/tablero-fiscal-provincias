"""Import official own-tax workbook, preserving independently updated RON."""
import argparse,collections,hashlib,json,re,shutil
from pathlib import Path
import scripts_regenerate_2026 as imp
from scripts_refresh_ron import readcsv,load,save

def build(source,url,reviewed):
 universe=imp.manifest_universe();rows,coverage=imp.import_top(source,universe)
 ron=readcsv('informacion_consolidada_2026_normalizado.csv');rc=collections.defaultdict(list)
 for r in ron:
  r['value_millions']=float(r['value_millions'])
  if r['period_type']=='month' and r['category_normalized']=='Total | (1) + (2)':rc[r['province']].append(r['period'])
 original=imp.ROOT/'data/top_sources'/source.name;original.parent.mkdir(exist_ok=True)
 if original.resolve()!=source.resolve():shutil.copyfile(source,original)
 ron_meta=load('data/meta.json')['sources']['transferencias_nacion_2026']
 imp.TOP_URL=url
 imp.RON_URL=load('data/meta.json')['sources']['transferencias_nacion_2026']['url']
 preserved={p:p.read_bytes() for p in [imp.CANONICAL_RON_OUTPUT,imp.PBA_RON_OUTPUT]}
 imp.write_csv(imp.TOP_OUTPUT,list(rows[0]),rows)
 imp.write_pba_files(rows,ron,original,Path(load('data/ron_latest.json')['source']['path']))
 imp.write_canonical_files(rows,ron,coverage,rc,universe)
 for p,b in preserved.items():p.write_bytes(b)
 imp.update_manifest(coverage,rc,universe)
 meta=load('data/meta.json');meta['sources']['transferencias_nacion_2026']=ron_meta;meta['sources']['recaudacion_propia_2026'].update(reviewed_at=reviewed,original={'path':str(original.relative_to(imp.ROOT)).replace('\\','/'),'sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'bytes':original.stat().st_size});save('data/meta.json',meta)
 import scripts_build_real_dynamics as real
 real.main()
 manifest=load('dashboard_manifest.json');p=imp.ROOT/'index.html';s=p.read_text('utf8');s=re.sub(r'^const EMBEDDED_MANIFEST = .*$',lambda m:'const EMBEDDED_MANIFEST = '+json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+';',s,flags=re.M);p.write_text(s,encoding='utf8')
 print(json.dumps({p:max(v) for p,v in coverage.items()},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--url',required=True);p.add_argument('--reviewed',required=True);a=p.parse_args();build(a.source,a.url,a.reviewed)

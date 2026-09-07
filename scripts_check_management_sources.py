"""Read-only URL/hash check. Changed bytes require review, never automatic import."""
import argparse,concurrent.futures,datetime,hashlib,json,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def check(source):
 result={k:v for k,v in source.items() if k!='sha256'}
 try:
  request=urllib.request.Request(source['url'],headers={'User-Agent':'FiscalSourceReview/1.0'})
  with urllib.request.urlopen(request,timeout=30) as response:
   content=response.read(30_000_001)
   if len(content)>30_000_000:raise ValueError('Archivo supera 30 MB; revisar por separado')
   digest=hashlib.sha256(content).hexdigest()
   result.update(http_status=response.status,current_sha256=digest,status='unchanged' if source.get('sha256')==digest else 'changed' if source.get('sha256') else 'reachable_unvalidated')
 except (urllib.error.URLError,TimeoutError,ValueError,OSError) as error:
  result.update(status='unavailable',error=str(error),http_status=getattr(error,'code',None))
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 sources=json.loads((ROOT/'data/budget_execution_2026.json').read_text(encoding='utf-8'))['sources']
 debt=json.loads((ROOT/'data/provincial_debt_services.json').read_text(encoding='utf-8'))['projections']['Entre Ríos']
 sources.append(dict(url=debt['sources'][0]['url'],sha256=debt['source_hashes']['annex'],kind='Calendario Entre Ríos 2026–2028'))
 sources+=json.loads((ROOT/'data/management_source_gaps.json').read_text(encoding='utf-8'))['checks']
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(check,sources))
 payload=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),method='Control a pedido de disponibilidad y cambios en archivos. No verifica por sí solo cifras, actualidad ni cobertura. No actualiza los datos publicados.',sources=rows)
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({status:sum(r['status']==status for r in rows) for status in sorted({r['status'] for r in rows})}))
if __name__=='__main__':main()

import csv,json,unittest,hashlib
from pathlib import Path
from scripts_build_pba_comparison import monthly
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]

class PbaComparison(unittest.TestCase):
 def test_official_monthly_values_and_missing_future_months(self):
  old=monthly(ROOT/'data/pba_sources/recaudacion-2025.xlsx',2025)
  new=monthly(ROOT/'data/pba_sources/recaudacion-2026.xlsx',2026)
  self.assertEqual(len(old),72);self.assertEqual(len(new),42)
  self.assertEqual(max(r['period'] for r in new),'2026-07')
  imported=list(csv.DictReader((ROOT/'top_mensual_2025_normalizado.csv').read_text(encoding='utf8').splitlines()))
  imported={(r['period'],r['tax']):float(r['value_millions']) for r in imported if r['province']=='Buenos Aires'}
  self.assertEqual(imported,{(r['period'],r['tax']):r['value_millions'] for r in old})
 def test_real_comparisons_recomputed_from_originals(self):
  d=json.loads((ROOT/'data/pba_comparison.json').read_text(encoding='utf8'))
  ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader((ROOT/'data/ipc_national_index.csv').read_text().splitlines())}
  records=monthly(ROOT/'data/pba_sources/recaudacion-2025.xlsx',2025)+monthly(ROOT/'data/pba_sources/recaudacion-2026.xlsx',2026)
  for r in d['revenue']:
   totals={y:sum(x['value_millions']/ipc[x['period']] for x in records if x['tax']==r['tax'] and x['year']==y and x['period'][5:]<='07') for y in [2025,2026]}
   self.assertAlmostEqual(r['real_change_pct'],100*(totals[2026]/totals[2025]-1))
  ratio=sum(ipc[f'2026-{m:02}'] for m in range(1,7))/sum(ipc[f'2025-{m:02}'] for m in range(1,7))
  for r in d['spending']:self.assertAlmostEqual(r['real_change_pct'],100*(r['current']/r['previous']/ratio-1))
  parts=[r for r in d['spending'] if r['key'] not in ['income','spending']]
  for col in ['previous','current']:self.assertAlmostEqual(sum(r[col] for r in parts),next(r[col] for r in d['spending'] if r['key']=='spending'),delta=3)
  for s in d['sources']:self.assertEqual(hashlib.sha256((ROOT/'data/pba_sources'/s['file']).read_bytes()).hexdigest(),s['sha256'])
 def test_pdf_includes_real_reading_without_extra_pages(self):
  p=PdfReader(ROOT/'reports/informe-buenos-aires.pdf');self.assertEqual(len(p.pages),3)
  text=p.pages[0].extract_text()
  for phrase in ['Detrás del ajuste','-30,8%','19,8%','IPC promedio semestral']:self.assertIn(phrase,text)

if __name__=='__main__':unittest.main()

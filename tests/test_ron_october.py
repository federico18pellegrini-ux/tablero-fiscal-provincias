import hashlib,json,unittest,csv
from pathlib import Path
import scripts_export_management_reports as reports
ROOT=Path(__file__).resolve().parents[1]
class OctoberRON(unittest.TestCase):
 def test_original_and_24_complete_series(self):
  latest=json.loads((ROOT/'data/ron_latest.json').read_text(encoding='utf8'))
  self.assertEqual(latest['period'],'2026-10');self.assertEqual(latest['real_available_through'],'2026-09');self.assertEqual(len(latest['rows']),24)
  self.assertEqual(hashlib.sha256((ROOT/latest['source']['path']).read_bytes()).hexdigest(),latest['source']['sha256'])
  data=reports.ReportData()
  for r in latest['rows']:
   t=data.transfers(r['province']);self.assertTrue(t['complete']);self.assertAlmostEqual(t['current'],r['ytd_nominal'],places=5)
   self.assertEqual(t['through'],'2026-10');self.assertEqual(t['real_through'],'2026-09')
   self.assertAlmostEqual(t['real_pct'],data.transfers(r['province'],'2026-09')['real_pct'],places=8)
  self.assertNotIn('2026-10',data.ipc)
 def test_real_dynamics_preserves_observed_comparison(self):
  dynamics=json.loads((ROOT/'dashboard_real_dynamics_2026.json').read_text(encoding='utf8'))
  data=reports.ReportData()
  for province,row in dynamics['provinces'].items():
   t=row['metrics']['ron_total'];self.assertEqual(t['last_available_period'],'2026-10');self.assertEqual(t['ytd_available_through'],'2026-09')
   self.assertAlmostEqual(t['real_ytd_pct'],round(data.transfers(province,'2026-09')['real_pct'],1))
 def test_all_pdfs_identify_the_two_cuts(self):
  from pypdf import PdfReader
  manifest=json.loads((ROOT/'reports/manifest.json').read_text(encoding='utf8'))
  for r in manifest['reports']:
   pages=PdfReader(ROOT/'reports'/r['file']).pages;self.assertEqual(len(pages),3)
   text=' '.join(pages[2].extract_text().split());self.assertIn('octubre de 2026',text);self.assertIn('septiembre',text);self.assertIn('Octubre aún no tiene IPC publicado.',text)
if __name__=='__main__':unittest.main()

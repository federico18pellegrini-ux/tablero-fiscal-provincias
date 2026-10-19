import csv,hashlib,json,unittest
from pathlib import Path
from scripts_regenerate_2026 import import_top,manifest_universe
from scripts_build_real_dynamics import own_revenue_totals
from pypdf import PdfReader
R=Path(__file__).resolve().parents[1]
class ComparableTOP(unittest.TestCase):
 def test_both_originals_reconcile_and_have_correct_year(self):
  meta=json.loads((R/'data/top_comparable_import.json').read_text(encoding='utf-8'))
  for year,source in zip([2025,2026],meta['sources']):
   p=R/source['file'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),source['sha256'])
   rows,cov=import_top(p,manifest_universe(),year)
   self.assertEqual(len(cov),24);self.assertTrue(all(str(r['year'])==str(year) and r['period'].startswith(str(year)) for r in rows))
   if year==2025:self.assertEqual({len(v) for v in cov.values()},{12})
 def test_real_revenue_for_all_provinces_and_pdf_agrees(self):
  d=json.loads((R/'dashboard_real_dynamics_2026.json').read_text(encoding='utf-8'))
  for p in manifest_universe():self.assertIsNotNone(d['provinces'][p]['metrics']['own_revenue']['real_ytd_pct'])
  metric=d['provinces']['Buenos Aires']['metrics']['own_revenue']
  self.assertEqual(metric['ytd_available_through'],'2026-08');self.assertEqual(metric['real_ytd_pct'],-2.8)
  text=PdfReader(R/'reports/informe-buenos-aires.pdf').pages[2].extract_text()
  self.assertIn('2,8%',text);self.assertIn('enero-agosto',text.replace('–','-'))

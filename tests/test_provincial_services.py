import json,unittest
from pathlib import Path
D=json.loads((Path(__file__).resolve().parents[1]/'data/provincial_debt_services.json').read_text(encoding='utf-8'))
class ProvincialServices(unittest.TestCase):
 def test_coverage_and_unique_periods(self):
  self.assertEqual(len(D['coverage']),24)
  self.assertEqual(len({(r['province'],r['period']) for r in D['history']}),528)
  for c in D['coverage']:
   self.assertEqual(len([r for r in D['history'] if r['province']==c['province']]),22)
 def test_missing_is_not_zero(self):
  rows=D['history']
  self.assertTrue(any(r['total_ars_m'] is None for r in rows))
  self.assertTrue(any(r['total_ars_m']==0 for r in rows))
  for r in rows:
   if r['amortization_ars_m'] is None or r['interest_ars_m'] is None:self.assertIsNone(r['total_ars_m'])
   else:self.assertAlmostEqual(r['total_ars_m'],r['amortization_ars_m']+r['interest_ars_m'],places=6)
 def test_units_and_projection(self):
  self.assertEqual(next(s for s in D['sources'] if s['province']=='CABA')['original_unit'],'ARS miles')
  self.assertAlmostEqual(D['projections']['Córdoba']['rows'][0]['total_ars_m'],634650.115306,places=6)
  self.assertEqual(D['projections']['Buenos Aires']['rows'][0]['total_ars_m'],3637755)
  for p in D['projections'].values():
   for r in p['rows']:self.assertAlmostEqual(r['total_ars_m'],r['amortization_ars_m']+r['interest_ars_m'],delta=1)
 def test_periods_and_sources(self):
  for r in D['history']:
   self.assertEqual(r['period_type'],'quarter' if r['period']=='2026-Q1' else 'year')
   self.assertTrue(r['source_url'].startswith('https://www.argentina.gob.ar/'))
  self.assertEqual(len(D['source_differences']),4)

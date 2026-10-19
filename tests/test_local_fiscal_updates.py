import csv, hashlib, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LocalFiscalUpdates(unittest.TestCase):
 def test_observed_deflation_and_archives(self):
  d=json.loads((ROOT/'data/fiscal_local_updates.json').read_text(encoding='utf8'))
  ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader((ROOT/'data/ipc_national_index.csv').read_text().splitlines())}
  n=d['neuquen'];self.assertEqual(len(n['rows']),6)
  sums={2025:0,2026:0}
  for r in n['rows']:
   self.assertIn(r['period'][5:],['04','05','06']);v=r['nominal_millions']/ipc[r['period']]*ipc['2026-06'];self.assertAlmostEqual(v,r['real_june2026_millions'],places=6);sums[int(r['period'][:4])]+=v
  self.assertAlmostEqual(n['real_change_pct'],(sums[2026]/sums[2025]-1)*100,places=8)
  for r in n['rows']+d['lapampa']['rows']:
   doc=r['document'];self.assertEqual(hashlib.sha256((ROOT/doc['archive']).read_bytes()).hexdigest(),doc['sha256'])
  for r in d['lapampa']['rows']:
   self.assertAlmostEqual(r['current_millions']+r['capital_millions'],r['nonfinancial_millions'],places=6)
   self.assertAlmostEqual(r['nonfinancial_millions']+r['figurative_millions']+r['financial_applications_millions'],r['gross_millions'],places=6)
  self.assertEqual(d['lapampa']['basis'],'compromiso')
 def test_partial_accounts_stay_out_of_rankings(self):
  d=json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf8'))
  m=next(m for m in d['municipalities'] if m['id']=='06760');self.assertIsNone(m['fiscal'])
  b=m['fiscalExecution']['financialBreakdown'];self.assertEqual(b['prior_liabilities'],'16647521570.98')

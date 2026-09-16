import json,unittest
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf8'))
class PbaSeptemberRefresh(unittest.TestCase):
 def test_semester_identities_and_comparable_vintage(self):
  d=read('data/pba_execution_latest.json');self.assertEqual(d['period'],'2026-H1')
  old,now=d['rows'];self.assertEqual(now['financial'],-876057)
  for r in d['rows']:
   self.assertEqual(r['income']-r['spending'],r['financial'])
   self.assertEqual(r['financial']+r['interest'],r['primary'])
   self.assertAlmostEqual(r['financial_pct'],100*r['financial']/r['income'])
  self.assertGreater(now['financial_pct'],old['financial_pct'])
  common=read('data/budget_execution_2026.json');self.assertEqual(max(r['period'] for r in common['executions']),'2026-Q1')
 def test_debt_does_not_mix_march_denominator_with_june_stock(self):
  p=read('data/debt/pba_debt_profile_2026q1.json');old=p['latest_stock'];new=p['latest_official_stock']
  self.assertEqual(old['cutoff'],'2026-03-31');self.assertEqual(new['cutoff'],'2026-06-30')
  self.assertAlmostEqual(old['total_ars_m']/old['ltm_total_income_ars_m']*100,old['debt_to_ltm_income_pct'],places=5)
  self.assertEqual(new['total_ars_m'],17950608.4);self.assertEqual(new['debt_to_ltm_income_pct'],45.5)
  self.assertAlmostEqual(new['total_ars_m']/new['ars_per_usd'],new['total_usd_m_equivalent'],delta=.1)
  self.assertNotIn('ltm_total_income_ars_m',new)
  schedule=read('data/debt/pba_forward_schedule.json');self.assertEqual(schedule,read('data/provincial_debt_services.json')['projections']['Buenos Aires'])
  self.assertEqual(schedule['rows'][0]['period_start'],'2026-07-01');self.assertEqual(schedule['rows'][1]['period_start'],'2027-01-01')
  self.assertEqual(max(schedule['rows'],key=lambda r:r['total_ars_m'])['year'],2027)
 def test_export_contains_updates_and_monthly_claim_basis(self):
  pdf=PdfReader(ROOT/'reports/informe-buenos-aires.pdf');text=' '.join(' '.join(p.extract_text().split()) for p in pdf.pages)
  for expected in ['primer semestre de 2026','4,22%','30/06/2026','17,95 billones','19,10 billones','julio-diciembre de 2026','enero y agosto']:
   self.assertIn(expected,text)
  for page in pdf.pages:self.assertIn('tablero.federicopellegrini.com.ar',page.extract_text())
  lp=' '.join(PdfReader(ROOT/'reports/informe-la-pampa.pdf').pages[2].extract_text().split());self.assertIn('por mes',lp)
 def test_august_price_update_keeps_municipal_price_base(self):
  self.assertEqual(read('data/ipc_source.json')['latest_period'],'2026-08')
  self.assertEqual(read('municipios/data/dashboard.json')['priceBase'],'2026-07')
  self.assertEqual(read('municipios/data/deflator.json')['latest'],'2026-08')

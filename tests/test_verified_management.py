import json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))

class VerifiedManagement(unittest.TestCase):
 def test_coverage_is_explicit_and_cash_is_never_inferred(self):
  audit=read('data/management_evidence_audit.json');rows=audit['jurisdictions']
  budgets=read('data/current_budget_execution.json')['records']
  debt=read('data/provincial_debt_services.json')
  self.assertEqual({r['province'] for r in rows},{r['province'] for r in debt['coverage']})
  self.assertEqual(len(rows),24);self.assertEqual(len(budgets),7)
  self.assertEqual(sum(r['budget_status']=='verified_partial' for r in rows),1)
  self.assertEqual(sum(r['debt_status']=='verified' for r in rows),len(debt['projections']))
  for row in rows:
   self.assertIsNone(row['free_cash_ars_m']);self.assertEqual(row['cash_status'],'not_verified')
   self.assertTrue(row['sources'],row['province'])
  mendoza=next(r for r in rows if r['province']=='Mendoza')
  self.assertEqual(mendoza['debt_status'],'located_pending_reconciliation')
  self.assertNotIn('Mendoza',debt['projections'])

 def test_accounting_stages_scopes_and_units(self):
  records={r['province']:r for r in read('data/current_budget_execution.json')['records']}
  for b in records.values():
   self.assertEqual(b['unit'],'ARS millions')
   self.assertGreater(b['credit_ars_m'],0)
   self.assertLessEqual(b['as_of'],'2026-09-07')
   for source in b['sources']:
    self.assertEqual(len(source['sha256']),64);self.assertTrue(source['trace'])
  rn=records['Río Negro'];self.assertIsNone(rn['accrued_ars_m'])
  self.assertAlmostEqual(rn['committed_ars_m']/rn['credit_ars_m']*100,61.67636,places=3)
  self.assertIsNone(records['Tucumán']['accrued_ars_m']);self.assertIsNone(records['Tucumán']['paid_ars_m'])
  self.assertIn('parcial',records['Córdoba']['scope'])
  self.assertAlmostEqual(records['Córdoba']['accrued_ars_m']/records['Córdoba']['credit_ars_m']*100,21.3949,places=3)
  self.assertAlmostEqual(records['CABA']['credit_ars_m'],19877152.039294,places=5)
  self.assertAlmostEqual(records['CABA']['accrued_ars_m'],7104105.89057616,places=5)
  self.assertAlmostEqual(records['Chubut']['capital_accrued_ars_m'],50562.86313353,places=5)
  self.assertAlmostEqual(records['Neuquén']['credit_ars_m'],10108919.7)

 def test_official_forward_schedules_not_history_extrapolation(self):
  additional=read('data/debt/verified_forward_schedules.json')['projections']
  full=read('data/provincial_debt_services.json')['projections']
  for province,p in additional.items():
   self.assertEqual(full[province],p)
   self.assertIsNone(p['as_of']);self.assertTrue(p['reference_label'])
   self.assertEqual([r['year'] for r in p['rows']],[2026,2027,2028])
   for r in p['rows']:
    self.assertAlmostEqual(r['total_ars_m'],r['amortization_ars_m']+r['interest_ars_m'],places=6)
  self.assertAlmostEqual(additional['Neuquén']['rows'][0]['total_ars_m'],432951.2)
  self.assertAlmostEqual(additional['Santa Fe']['rows'][1]['total_ars_m'],410094.184673)

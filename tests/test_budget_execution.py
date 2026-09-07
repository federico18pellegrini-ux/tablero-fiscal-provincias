import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/budget_execution_2026.json').read_text(encoding='utf-8'))
class BudgetExecution(unittest.TestCase):
 def test_coverage_and_missing(self):
  self.assertEqual(len(D['budgets']),24)
  self.assertEqual(len({b['province'] for b in D['budgets']}),24)
  self.assertEqual(len({(e['province'],e['period']) for e in D['executions']}),48)
  missing=[e['province'] for e in D['executions'] if e['period']=='2026-Q1' and e['income'] is None]
  self.assertEqual(missing,['La Pampa'])
  self.assertEqual(sum(b['scope_comparison'] for b in D['budgets']),7)
 def test_trace_rebuild_and_units(self):
  for b in D['budgets']:
   factor=1000 if b['province']=='Misiones' else 1
   for key in ['income','spending','capital']:
    reconstructed=sum(t['original_value']*t['multiplier'] for t in b['trace'][key])/factor
    self.assertAlmostEqual(b[key],reconstructed,places=6)
    self.assertGreaterEqual(b[key],0)
   self.assertLessEqual(b['capital'],b['spending'])
   self.assertEqual(b['unit'],'ARS millions')
 def test_internal_transfers_are_deducted(self):
  b=next(b for b in D['budgets'] if b['province']=='Tucumán')
  self.assertEqual([t['multiplier'] for t in b['trace']['income']],[1,-1,-1])
  self.assertEqual([t['multiplier'] for t in b['trace']['spending']],[1,-1,-1])
 def test_sources(self):
  self.assertEqual(len(D['sources']),26)
  for s in D['sources']:
   self.assertTrue(s['url'].startswith('https://www.argentina.gob.ar/'))
   self.assertEqual(len(s['sha256']),64)
 def test_entre_rios_reconciliation(self):
  er=json.loads((ROOT/'data/provincial_debt_services.json').read_text(encoding='utf-8'))['projections']['Entre Ríos']
  self.assertEqual([r['year'] for r in er['rows']],[2026,2027,2028])
  self.assertAlmostEqual(er['rows'][0]['total_ars_m'],537267.45)
  self.assertEqual(len(er['unit_reconciliation']),2)
  for r in er['unit_reconciliation']:
   self.assertLess(abs(r['annex_ars']/1e6-r['budget_ars_m']),.01)

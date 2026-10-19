import unittest
from scripts_build_real_dynamics import own_revenue_totals,read_csv,TOP_2025_FILE
class OwnRevenueTotals(unittest.TestCase):
 def test_total_is_not_added_to_its_components(self):
  rows=read_csv(TOP_2025_FILE)
  actual=own_revenue_totals(rows)[('Buenos Aires','2025-01')]
  self.assertAlmostEqual(actual,950706.1411869786,places=5)
  with self.assertRaises(ValueError):own_revenue_totals(rows+ [next(r for r in rows if r['province']=='Buenos Aires' and r['tax']=='Iibb')])
 def test_partial_components_do_not_become_total(self):
  self.assertEqual(own_revenue_totals([{'province':'X','period':'2025-01','period_type':'month','tax':'Iibb','value_millions':'10'}]),{})

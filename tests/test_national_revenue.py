import unittest
from scripts_build_national_revenue import build,load,OUT
class RevenuePlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=build()
    def test_reproducible_originals_and_published_totals(self):self.assertEqual(self.data,load(OUT))
    def test_bcra_is_identified_by_code_not_total_property_income(self):
        rows={m['period']:m for m in self.data['months']}
        self.assertEqual(rows['2026-05']['bcra'],24400000)
        self.assertAlmostEqual(rows['2025-04']['bcra'],11976386.676207)
        self.assertGreater(next(g for g in rows['2026-05']['groups'] if g['id']=='property')['nominal'],0)
    def test_complete_months_groups_and_identity(self):
        self.assertEqual(len(self.data['months']),20)
        for m in self.data['months']:
            self.assertEqual(len(m['groups']),4)
            self.assertAlmostEqual(m['total'],sum(g['nominal'] for g in m['groups'])+m['bcra'],places=5)
        self.assertEqual(self.data['months'][-1]['period'],'2026-08')

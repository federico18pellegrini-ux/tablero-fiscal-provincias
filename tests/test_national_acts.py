import unittest
from scripts_build_national_acts import build,load,OUT
class ActsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.d=build()
    def test_sources_and_package(self):self.assertEqual(self.d,load(OUT))
    def test_total_and_individual_residuals(self):
        r=self.d['reconciliation'];self.assertAlmostEqual(r['documented_net'],r['net'],places=5)
        self.assertEqual(len(self.d['acts']),5)
        for p in self.d['program_balance']:self.assertAlmostEqual(p['net'],p['documented']+p['residual'],places=5)
        missing=[r for a in self.d['acts'] for r in a['rows'] if not r['matched']]
        self.assertEqual({(r['saf'],r['program']) for r in missing},{(322,54),(322,55)})
        self.assertAlmostEqual(sum(r['millions'] for r in missing),r['remaining_net'],places=5)
    def test_known_vaccine_reinforcement_has_original_page(self):
        a=next(a for a in self.d['acts'] if a['id']=='da26')
        r=next(r for r in a['rows'] if r['saf']==310 and r['program']==20)
        self.assertEqual(r['millions'],283146);self.assertEqual(r['page'],2)

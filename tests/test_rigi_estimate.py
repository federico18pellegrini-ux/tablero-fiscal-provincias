import json
import math
import unittest
from pathlib import Path
from scripts_build_rigi_estimate import build,customs_cost

ROOT=Path(__file__).resolve().parents[1]

class RigiEstimateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((ROOT/'nacion/data/rigi-estimate.json').read_text(encoding='utf8'))

    def test_registry_deduplicates_territorial_rows_and_links_all_27_resolutions(self):
        d=self.data
        self.assertEqual(build(),d)
        r=d['registry'];self.assertEqual(r['raw_territorial_rows'],33)
        self.assertEqual(r['project_count'],27);self.assertEqual(r['investment_usd_millions'],76173)
        self.assertEqual(len({p['id'] for p in r['projects']}),27)
        self.assertEqual(len({p['resolution'] for p in r['projects']}),27)
        for p in r['projects']:
            self.assertTrue((ROOT/'nacion'/p['resolution_file']).exists())
            self.assertIsNone(p['annual_investment_2027_usd_millions'])
            self.assertIsNone(p['fiscal_cost_2027'])
            self.assertGreaterEqual(p['published'],p['accession_date'])
        self.assertEqual(max(p['published'] for p in r['projects']),'2026-10-27')

    def test_customs_scenarios_are_not_total_cost_or_a_statistical_interval(self):
        d=self.data;c=d['customs']
        self.assertIsNone(d['official_fiscal_cost_2027']);self.assertIsNone(d['total_estimated_cost_2027'])
        self.assertEqual(c['investment_2027_usd_millions'],7827)
        expected=[7.827,95.88075,410.9175]
        for row,value in zip(c['scenarios'],expected):
            self.assertAlmostEqual(row['cost_usd_millions'],value)
            self.assertAlmostEqual(row['cost_usd_millions'],customs_cost(7827,row['import_share'],row['incremental_share'],row['tariff']))
        self.assertEqual(customs_cost(7827,.35,0,.07),0)
        self.assertEqual(customs_cost(7827,.35,.5,0),0)
        for values in [(None,.2,.5,.1),(7827,-.1,.5,.1),(7827,.5,1.1,.1),(7827,.5,.5,float('nan')),(True,.5,.5,.1)]:
            self.assertIsNone(customs_cost(*values))

    def test_dividend_zero_is_only_for_rate_reduction_and_vat_is_financial(self):
        d=self.data
        self.assertTrue(all(p['dividend_reduction_from']>'2027-12-31' for p in d['registry']['projects']))
        dividend=next(x for x in d['tax_components'] if x['name'].startswith('Dividendos'))
        self.assertEqual(dividend['value'],0)
        self.assertTrue(all(x['value'] is None for x in d['tax_components'] if not x['name'].startswith('Dividendos')))
        vat=d['vat_example'];self.assertAlmostEqual(vat['financial_value_usd_millions'],100*(1-1.08**(-.5)))
        self.assertLess(vat['financial_value_usd_millions'],vat['credit_usd_millions'])

if __name__=='__main__':unittest.main()

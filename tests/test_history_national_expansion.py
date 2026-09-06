import csv,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
class HistoryNationalExpansionTests(unittest.TestCase):
    def test_debt_history_units_and_reconciliation(self):
        d=read('debt_history.json');rows=d['rows'];self.assertEqual(len(rows),420)
        self.assertEqual(len({(r['province'],r['period']) for r in rows}),420)
        self.assertEqual(len(d['reports']),18)
        history={(r['province'],r['period']):r for r in read('fiscal_history.json')['rows']}
        for r in rows:
            self.assertEqual(r['currency'],'ARS' if r['period']<='2024-Q2' else 'USD')
            self.assertLessEqual(abs(r['total']-sum(r[k] for k in ['bonds','nation','multilateral','banks','consolidated'])),2)
            self.assertIsNotNone(r['ratios'])
            if r['currency']=='ARS':
                income=history[r['province'],r['period']]['income']
                self.assertAlmostEqual(100*r['total']/income,r['ratios']['debt_income_pct'],delta=.06)
    def test_latest_matches_existing_debt(self):
        latest=read('fiscal_latest_details.json')['debt']
        rows=[r for r in read('debt_history.json')['rows'] if r['period']=='2026-Q1']
        self.assertEqual({r['province'] for r in rows},set(latest))
        for r in rows:
            for key,value in latest[r['province']].items():self.assertEqual(r[key],value)
    def test_composition_reconciles(self):
        for r in read('fiscal_history.json')['rows']:
            self.assertLessEqual(abs(sum(r[k] for k in ['tax','royalties','national_tax','social_income','other_income'])-r['income']),2)
            self.assertLessEqual(abs(sum(r[k] for k in ['personnel','current_transfers','capital','social_spend','other_spend'])-r['primary_spend']),2)
    def test_national_identities_dates_and_sources(self):
        d=read('national_management.json');metrics={m['id']:m for s in d['sections'] for m in s['metrics']}
        self.assertEqual(metrics['exports']['value']-metrics['imports']['value'],metrics['trade_balance']['value'])
        self.assertEqual(metrics['capital_paid']['value']+metrics['interest_paid']['value'],metrics['debt_paid']['value'])
        self.assertEqual(metrics['poverty']['period'],'2° semestre 2025')
        self.assertEqual(metrics['bcra_1']['period'],'2026-09-02')
        self.assertIn('brutas',metrics['bcra_1']['label'])
        for s in d['sections']:
            self.assertTrue(s['source_url'].startswith('https://'))
            self.assertTrue(s['scope'])
            for m in s['metrics']:self.assertTrue(m['period']);self.assertTrue(m['unit'])
    def test_activity_history_and_real_salary(self):
        d=read('national_management.json');rows=d['activity_history']['rows'];self.assertEqual(len(rows),270)
        self.assertEqual(rows[0]['period'],'2004-01');self.assertEqual(rows[-1]['period'],'2026-06')
        self.assertAlmostEqual(100*(rows[-1]['seasonally_adjusted']/rows[-2]['seasonally_adjusted']-1),rows[-1]['mom'])
        metrics={m['id']:m for s in d['sections'] for m in s['metrics']}
        with (ROOT/'data/ipc_national_index.csv').open() as f:ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader(f)}
        self.assertAlmostEqual(metrics['salary_real_mom']['value'],100*(1.029/(ipc['2026-06']/ipc['2026-05'])-1))

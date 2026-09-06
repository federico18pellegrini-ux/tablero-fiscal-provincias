import csv,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
class ManagementOperationsTests(unittest.TestCase):
    def test_federal_benchmarks_have_one_comparable_universe(self):
        d=read('federal_benchmarks.json');rows=d['rows'];self.assertEqual(len(rows),23);self.assertNotIn('CABA',{r['province'] for r in rows})
        values=sorted(r['per_capita'] for r in rows);self.assertEqual(d['median'],values[11]);self.assertAlmostEqual(d['simple_mean'],sum(values)/23)
        self.assertAlmostEqual(d['population_weighted_mean'],sum(r['per_capita']*r['population'] for r in rows)/sum(r['population'] for r in rows));self.assertEqual(d['population_period'],'Censo 2022')
    def test_spending_components_and_real_change(self):
        s=read('national_operations.json')['spending'];rows={r['id']:r for r in s['rows']}
        self.assertAlmostEqual(sum(r['value'] for r in rows.values() if r['composition']),rows['primary_spend']['value'],places=3)
        self.assertAlmostEqual(rows['income']['value']-rows['primary_spend']['value'],rows['primary']['value'],places=3)
        self.assertAlmostEqual(rows['primary']['value']-rows['interest']['value'],rows['financial']['value'],places=3)
        with (ROOT/'data/ipc_national_index.csv').open() as f:ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader(f)}
        for r in rows.values():
            self.assertAlmostEqual(r['real_yoy_pct'],100*((r['value']/r['previous'])/(ipc['2026-07']/ipc['2025-07'])-1))
        for r in s['monthly_2026']:
            self.assertAlmostEqual(r['real_july2026'],r['value']*ipc['2026-07']/ipc[r['period']])
        for id,r in rows.items():self.assertAlmostEqual(sum(m['value'] for m in s['monthly_2026'] if m['id']==id),r['ytd'],places=3)
    def test_debt_profile_is_historical_and_correct_units(self):
        d=read('national_operations.json')['maturities'];self.assertEqual(d['as_of'],'2026-03-31');self.assertEqual(d['unit'],'USD millones equivalentes');self.assertTrue(d['includes_bcra_advances'])
        self.assertEqual(len(d['rows']),12);self.assertEqual(d['rows'][0]['period'],'2026-04');self.assertEqual(d['rows'][-1]['period'],'2027-03')
        self.assertAlmostEqual(sum(r['total'] for r in d['rows']),160934.8616527081)
        for r in d['rows']:self.assertAlmostEqual(r['total'],r['capital']+r['interest'])
    def test_treasury_coverage_and_no_free_cash_imputation(self):
        d=read('treasury_obligations.json');p=d['payables'];self.assertAlmostEqual(sum(r['value'] for r in p['components']),p['total'],delta=.02)
        self.assertEqual(p['monthly'][-1]['value'],p['total']);self.assertIn('Excluye deuda pública',p['limitation'])
        a=d['bcra_advances'];self.assertEqual(a['september_2026']+a['q4_2026'],a['remaining_2026']);self.assertIsNone(d['free_cash']['value'])
    def test_targets_preserve_baselines_and_leave_decisions_empty(self):
        with (ROOT/'data/management_targets_template.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),96);self.assertEqual(len({r['provincia'] for r in rows}),24)
        for r in rows:
            self.assertTrue(r['valor_base']);self.assertTrue(r['fuente']);self.assertFalse(r['meta']);self.assertFalse(r['responsable']);self.assertFalse(r['fecha_objetivo'])

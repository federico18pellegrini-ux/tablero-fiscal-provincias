import csv,json,unittest,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FederalManagementTests(unittest.TestCase):
    def test_history_coverage_identities_and_latest(self):
        d=json.loads((ROOT/'data/fiscal_history.json').read_text(encoding='utf-8'))
        rows=d['rows'];self.assertEqual(len(rows),422)
        self.assertEqual(len({r['period'] for r in rows}),18)
        self.assertEqual(len({r['province'] for r in rows}),24)
        self.assertEqual(len({(r['province'],r['period']) for r in rows}),422)
        for r in rows:
            self.assertLessEqual(abs(r['income']-r['primary_spend']-r['primary']),2)
            self.assertLessEqual(abs(r['primary']+r['interest_signed']-r['financial']),2)
            self.assertAlmostEqual(r['primary_pct'],r['primary']/r['income']*100)
        latest={r['province']:r for r in rows if r['period']=='2026-Q1'}
        self.assertNotIn('La Pampa',latest)
        self.assertAlmostEqual(latest['Córdoba']['primary_pct'],2.1146,places=4)
        self.assertAlmostEqual(latest['Santa Fe']['financial_pct'],-5.6522,places=4)
    def test_latest_quarter_and_debt_universe(self):
        d=json.loads((ROOT/'data/fiscal_latest_details.json').read_text(encoding='utf-8'))
        self.assertEqual(set(d['quarters']),set(d['debt']))
        self.assertEqual(len(d['quarters']),23)
        self.assertEqual(d['quarters']['Buenos Aires']['financial_pct'],-3.9)
        self.assertEqual(d['quarters']['Córdoba']['primary_pct'],13.1)
        self.assertEqual(d['debt']['Córdoba']['total'],3092)
        for r in d['debt'].values():self.assertLessEqual(abs(r['total']-sum(v for k,v in r.items() if k!='total')),2)
    def test_official_ipc_alignment_and_coverage(self):
        with (ROOT/'deflactor_mensual.csv').open(encoding='utf-8') as f:rows={r['period']:r for r in csv.DictReader(f)}
        self.assertAlmostEqual(float(rows['2024-01']['ipc_mom']),.206,delta=.0005)
        self.assertAlmostEqual(float(rows['2024-02']['ipc_mom']),.132,delta=.0005)
        self.assertLess(float(rows['2026-07']['factor_to_latest']),1)
        self.assertEqual(float(rows['2026-06']['factor_to_latest']),1)
        self.assertNotIn('2015-12',rows)
    def test_sync_is_idempotent(self):
        for name in ['scripts_update_deflator.py','scripts_sync_deflator_html.py']:
            subprocess.run([sys.executable,str(ROOT/name)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        before=hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()
        subprocess.run([sys.executable,str(ROOT/'scripts_sync_deflator_html.py')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        self.assertEqual(before,hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest())
    def test_national_accounts_reconcile(self):
        d=json.loads((ROOT/'data/national_management.json').read_text(encoding='utf-8'))
        primary,interest,financial,_=d['metrics'];self.assertEqual(primary['value']-interest['value'],financial['value'])
    def test_geometry_covers_all_jurisdictions(self):
        d=json.loads((ROOT/'data/province_geometry.json').read_text(encoding='utf-8'))
        self.assertEqual(len(d['features']),24)
        self.assertEqual(len({f['province'] for f in d['features']}),24)
        self.assertTrue(all(f['path'].startswith('M') for f in d['features']))

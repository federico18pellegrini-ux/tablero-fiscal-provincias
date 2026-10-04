import hashlib,json,unittest
from pathlib import Path
from scripts_build_pba_capital import economic,functions,read_rows,SOURCE
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text('utf8'))

class OctoberIntegration(unittest.TestCase):
    def test_capital_closes_without_counting_subfunctions_twice(self):
        d=load('data/pba_capital_detail.json')
        for year in (2025,2026):
            total=economic(read_rows(SOURCE/f'{year}-APNF-Econ2.html'))
            rows=functions(read_rows(SOURCE/f'{year}-APNF-FinFun.html'))
            key='previous' if year==2025 else 'current'
            self.assertAlmostEqual(total['capital'],d['totals']['capital'][key],places=2)
            self.assertLess(abs(sum(r['direct'] for r in rows)-total['direct']),.15)
            self.assertLess(abs(sum(r['capital'][key] for r in d['institutions'])-total['capital']),.3)
        self.assertEqual(len(d['functions']),28)
        self.assertEqual(len(d['institutions']),53)
        self.assertEqual(d['coverage']['project_execution'],'not_published_in_these_tables')
        self.assertEqual(d['coverage']['function_capital_transfers'],'not_separated_in_source')
        education=next(r for r in d['functions'] if r['id']=='3-40')['direct']
        self.assertGreater(education['real_change_pct'],0)
        for s in d['sources']:
            self.assertEqual(hashlib.sha256((SOURCE/s['file']).read_bytes()).hexdigest(),s['sha256'])

    def test_current_execution_and_frozen_project_baseline_have_distinct_dates(self):
        g=load('nacion/data/gestion.json');e=load('nacion/data/execution-latest.json')
        self.assertEqual(e['cutoff'],'2026-10-04')
        self.assertEqual(g['execution']['project_baseline']['total'][0]['corte'],'2026-09-15')
        self.assertAlmostEqual(sum(m['accrued'] for m in e['execution'][0]['months']),g['execution']['total']['credito_devengado'],places=5)
        self.assertEqual(len(e['execution'][0]['months']),10)
        for row in e['execution']:
            for m in row['months']:
                self.assertEqual(m['partial'],m['month']==10)
                if m['month']>8:self.assertIsNone(m['real'])

    def test_new_municipal_accounts_keep_originals_and_do_not_mix_periods(self):
        a=load('municipios/data/fiscal_verified.json')
        current={'06448','06609','06638','06665'};other={'06511','06182','06875','06770'}
        for group,ids in [('records',current),('otherPeriods',other)]:
            rows=[r for r in a[group] if r['id'] in ids];self.assertEqual(len(rows),4)
            for r in rows:
                self.assertEqual(r['fin']=='2026-06-30',group=='records')
                for doc in r['documents']:
                    self.assertEqual(hashlib.sha256((ROOT/doc['archive']).read_bytes()).hexdigest(),doc['sha256'])

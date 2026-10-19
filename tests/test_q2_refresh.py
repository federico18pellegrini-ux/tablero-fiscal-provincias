import hashlib,json,unittest
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
class Q2Refresh(unittest.TestCase):
 def test_ltm_conciles_with_official_annual_and_semesters(self):
  d=read('data/fiscal_q2_2026.json');annual=read('data/annual_fiscal_accounts.json')['rows'];self.assertEqual(len(d['ltm']),23)
  for row in d['ltm']:
   a=next(r for r in annual if r['province']==row['province'] and r['year']==2025)
   semesters=[next(r for r in d['official_semesters'] if r['province']==row['province'] and r['period']==y+'-H1') for y in ['2025','2026']]
   for field in ['income','primary_spend','primary','financial','capital']:
    self.assertAlmostEqual(row[field],a[field]+semesters[1][field]-semesters[0][field],delta=2,msg=f'{row["province"]} {field}')
 def test_originals_missingness_and_scale(self):
  d=read('data/fiscal_q2_2026.json');self.assertEqual(len(d['official_semesters']),48)
  for s in d['sources']:self.assertEqual(hashlib.sha256((ROOT/s['archive']).read_bytes()).hexdigest(),s['sha256'])
  for s in d['official_semesters']:
   if s['province']=='La Pampa':self.assertIsNone(s['income']);continue
   self.assertAlmostEqual(s['income']-s['spending'],s['financial'],delta=.01)
  pba=next(r for r in d['ranking'] if r['province']=='Buenos Aires');self.assertEqual(pba['debt_rank'],22);self.assertEqual(pba['debt_income_pct'],45.6)
  self.assertEqual(d['quarters']['Buenos Aires']['financial_pct'],-4.9)
 def test_report_and_web_use_new_period(self):
  html=(ROOT/'index.html').read_text(encoding='utf-8');self.assertIn('ranking_2t26.csv',html);self.assertIn("if(row.period==='2026-Q2'",html)
  for p in read('reports/manifest.json')['reports']:
   text=PdfReader(ROOT/'reports'/p['file']).pages[0].extract_text()
   self.assertIn('junio',text)
   if p['province']!='La Pampa':self.assertIn('doce meses a junio de 2026',text)
 def test_partial_municipal_executions_never_become_fiscal_balances(self):
  d=read('municipios/data/dashboard.json');ms={m['id']:m for m in d['municipalities']}
  for code in ['06351','06693','06760']:
   m=ms[code];self.assertIsNone(m['fiscal']);self.assertIsNone(m['fiscalOther']);self.assertIsNotNone(m['fiscalExecution']);self.assertNotIn('resultado_financiero',m['fiscalExecution'])
  self.assertEqual(ms['06693']['fiscalExecution']['inicio'],'2026-04-01')
  belgrano=ms['06301']['fiscalOther'];self.assertEqual(belgrano['fin'],'2026-09-30');self.assertAlmostEqual(belgrano['ingresos_totales']-belgrano['gastos_totales'],belgrano['resultado_financiero'],places=2)

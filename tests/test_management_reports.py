import csv, hashlib, json, math, tempfile, unittest
from pathlib import Path
from pypdf import PdfReader
from scripts_export_management_reports import ReportData, ROOT, build, fingerprints, ratio

class ManagementReportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=ReportData()
  cls.manifest=json.loads((ROOT/'reports/manifest.json').read_text(encoding='utf-8'))

 def test_all_provinces_three_pages_and_attributed_footer(self):
  entries=self.manifest['reports'];self.assertEqual(len(entries),24)
  self.assertEqual({r['province'] for r in entries},set(self.data.provinces))
  for entry in entries:
   path=ROOT/'reports'/entry['file'];pdf=PdfReader(path)
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),entry['sha256'])
   self.assertEqual(len(pdf.pages),3);self.assertEqual(pdf.metadata.author,'Federico Pellegrini')
   for n,page in enumerate(pdf.pages,1):
    text=page.extract_text();self.assertIn(entry['province'],text);self.assertIn('Federico Pellegrini',text);self.assertIn(f'{n} / 3',text)
    self.assertNotRegex(text,r'\b(?:NaN|nan|None)\b')
   # Missing calendars must not become projections of the historical series.
   page3=' '.join(pdf.pages[2].extract_text().split())
   self.assertEqual('Todavía falta un calendario futuro verificado' in page3,not entry['forward_debt_calendar'])

 def test_fiscal_identities_and_capital_components(self):
  for row in self.data.annual['rows']:
   if row['status']=='missing':
    self.assertIsNone(row['income']);self.assertIsNone(row['spending']);continue
   self.assertAlmostEqual(row['income']-row['spending'],row['financial'],delta=.02)
   self.assertAlmostEqual(row['income']-row['primary_spend'],row['primary'],delta=.02)
   self.assertAlmostEqual(row['direct_investment']+row['capital_transfers']+row['financial_investment'],row['capital'],delta=.02)
  ba=self.data.model('Buenos Aires')
  self.assertAlmostEqual(ba['metrics']['financial'],-5.93683,places=4)
  self.assertAlmostEqual(ba['metrics']['capital'],100*2406109/36572407.413723,places=6)
  self.assertAlmostEqual(ba['qcapital'],4.35390,places=3)
  self.assertAlmostEqual(ba['qpcapital'],5.06288,places=3)
  self.assertEqual(ba['benchmark_n'],22)

 def test_missing_and_incompatible_observations_not_backfilled(self):
  lp=self.data.model('La Pampa');self.assertIsNone(lp['annual']);self.assertIsNone(lp['quarter']);self.assertIsNone(lp['metrics']['capital'])
  self.assertIsNotNone(lp['history'][1]);self.assertIsNone(lp['history'][2])
  sde=self.data.model('Santiago del Estero');self.assertEqual(sde['annual']['basis'],'compromiso')
  excluded={r['province'] for r in self.data.annual['rows'] if r['year']==2025 and (r['status']=='missing' or r['basis']!='devengado')}
  self.assertEqual(excluded,{'La Pampa','Santiago del Estero'})

 def test_monthly_deflation_and_source_report_reconciliation(self):
  d=self.data
  semester=d.transfers('Buenos Aires','2026-06')
  self.assertAlmostEqual(semester['current'],8472533.557958,places=4)
  self.assertAlmostEqual(semester['previous'],6505185.188668,places=4)
  self.assertAlmostEqual(semester['real_pct'],-2.12401058,places=6)
  self.assertAlmostEqual(d.transfers('Buenos Aires','2026-06','Financiamiento Educativo')['real_pct'],18.865246,places=5)
  dashboard=json.loads((ROOT/'dashboard_real_dynamics_2026.json').read_text(encoding='utf-8'))
  for province in d.provinces:
   report=d.transfers(province);metric=dashboard['provinces'][province]['metrics']['ron_total']
   self.assertEqual(round(report['real_pct'],1),metric['real_ytd_pct'])
  # A missing January or a missing IPC must not produce a partial "annual" total.
  own=ReportData();del own.ron[('Buenos Aires','2025-01','Total | (1) + (2)')]
  self.assertIsNone(own.transfers('Buenos Aires')['real_pct'])
  own=ReportData();del own.ipc['2026-02'];self.assertIsNone(own.transfers('Buenos Aires')['real_pct'])

 def test_regeneration_bounds_and_freshness(self):
  self.assertEqual(fingerprints(),self.manifest['input_sha256'])
  with tempfile.TemporaryDirectory() as tmp:
   generated,layouts=build(Path(tmp))
   self.assertEqual(len(generated['reports']),24)
   for name,blocks in layouts.items():
    self.assertEqual({b['page'] for b in blocks},{1,2,3})
    self.assertTrue(all(b['end']<280 for b in blocks),name)
    self.assertEqual(len(PdfReader(Path(tmp)/next(e['file'] for e in generated['reports'] if e['province']==name)).pages),3)

if __name__=='__main__':unittest.main()

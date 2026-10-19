import hashlib,json,unittest
from pathlib import Path
from decimal import Decimal as D
R=Path(__file__).resolve().parents[1]
class RecoveredAccounts(unittest.TestCase):
 def test_hurlingham_historical_image_is_not_current_ranking(self):
  d=json.loads((R/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
  m=next(m for m in d['municipalities'] if m['id']=='06408')
  self.assertIsNone(m['fiscal']);self.assertIsNone(m['fiscalExecution'])
  self.assertEqual(m['fiscalOther']['fin'],'2021-12-31')
  self.assertEqual(m['fiscalOther']['resultado_financiero'],261377713.70)
  self.assertEqual(m['fiscalOther']['gastos_totales'],6523739600.91)
  self.assertNotEqual(m['fiscalOther']['gastos_totales'],9831009574.81)
 def test_signed_caif_replaces_partial_without_mixing_periods(self):
  d=json.loads((R/'municipios/data/dashboard.json').read_text(encoding='utf-8'));m={r['id']:r for r in d['municipalities']}
  p=m['06351'];r=m['06693'];self.assertIsNone(p['fiscal']);self.assertIsNone(p['fiscalExecution']);self.assertEqual(p['fiscalOther']['fin'],'2026-09-30')
  self.assertIsNone(r['fiscalExecution']);self.assertEqual(r['fiscal']['fin'],'2026-06-30');self.assertEqual(r['fiscal']['resultado_financiero'],884705476.44)
  self.assertEqual(p['fiscalOther']['resultado_financiero'],838838880.39)
  self.assertEqual(D('17835150905.27')-D(str(p['fiscalOther']['gastos_totales'])),D('58501838.99'))
  self.assertIsNotNone(m['06760']['fiscalExecution']);self.assertIsNone(m['06760']['fiscal'])
 def test_image_and_zip_originals_preserve_bytes(self):
  d=json.loads((R/'municipios/data/fiscal_verified.json').read_text(encoding='utf-8'))
  for r in d['records']+d['otherPeriods']:
   if r['id'] not in ['06351','06693','06408']:continue
   for s in r['documents']:
    self.assertEqual(hashlib.sha256((R/s['archive']).read_bytes()).hexdigest(),s['sha256'])
    if 'containerArchive' in s:self.assertEqual(hashlib.sha256((R/s['containerArchive']).read_bytes()).hexdigest(),s['containerSha256'])

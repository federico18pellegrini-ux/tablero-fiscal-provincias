import unittest,json,csv,hashlib
from pathlib import Path
from decimal import Decimal
from scripts_update_national_price_scenario import scenario
R=Path(__file__).resolve().parents[1]
class SeptemberOfficialVerification(unittest.TestCase):
 def test_official_cpi_and_observed_scenario(self):
  p=R/'data/ipc-sources/2026-09-divisiones.csv';source=json.loads((R/'data/ipc_source.json').read_text(encoding='utf-8'))
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),source['sha256'])
  rows=list(csv.DictReader(p.read_text(encoding='latin1').splitlines(),delimiter=';'))
  row=next(r for r in rows if r['Codigo']=='0' and r['Region']=='Nacional' and r['Periodo']=='202609')
  self.assertEqual(Decimal(row['Indice_IPC'].replace(',','.')),Decimal('12514.1508'))
  ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader((R/'data/ipc_national_index.csv').read_text().splitlines())}
  latest,indices,_,_=scenario(ipc);self.assertEqual(latest,'2026-09');self.assertEqual(indices['2026-09'],12514.1508)
  self.assertAlmostEqual(indices['2026-12']/ipc['2025-12'],1.29)
 def test_new_accounts_match_archived_evidence_and_do_not_replace_common_semester(self):
  data=json.loads((R/'municipios/data/fiscal_verified.json').read_text(encoding='utf-8'))
  ids={'06077','06105','06112','06196','06476','06581','06638','06714','06742','06784','06728'}
  records=[r for r in data['otherPeriods'] if r['id'] in ids];self.assertEqual(len(records),11)
  for r in records:
   self.assertEqual(r['fin'],'2026-09-30');a={k:Decimal(v) for k,v in r['amounts'].items()}
   self.assertEqual(a['ingresos_totales']-a['gastos_totales'],a['resultado_financiero'])
   for d in r['documents']:self.assertEqual(hashlib.sha256((R/d['archive']).read_bytes()).hexdigest(),d['sha256'])
  self.assertTrue(all(r['fin']=='2026-06-30' for r in data['records']))
  self.assertEqual(next(r for r in records if r['id']=='06728')['amounts']['resultado_financiero'],'-735917635.27')
 def test_treasury_reconciles_without_importing_old_liabilities(self):
  a=json.loads((R/'municipios/data/management_verified.json').read_text(encoding='utf-8'))
  t=next(r for r in a['municipalities'] if r['id']=='06329')['treasury']
  self.assertEqual(sum(Decimal(x) for x in t['reconciliation'].values()),Decimal(t['amounts']['closing']))
  self.assertNotIn('liabilities',t['amounts'])

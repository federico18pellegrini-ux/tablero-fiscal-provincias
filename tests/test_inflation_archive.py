import csv,json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class InflationArchiveTests(unittest.TestCase):
 def test_ipc_factor_and_embedded_series(self):
  ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader((ROOT/'data/ipc_national_index.csv').read_text(encoding='utf-8').splitlines())}
  factors={r['period']:float(r['factor_to_latest']) for r in csv.DictReader((ROOT/'deflactor_mensual.csv').read_text(encoding='utf-8').splitlines())}
  embedded=json.loads(re.search(r'const DEFLACTOR_MONTH = (\{.*?\});',(ROOT/'index.html').read_text(encoding='utf-8'))[1])
  self.assertEqual(embedded,factors)
  self.assertEqual(set(ipc),set(factors))
  for month,value in ipc.items():self.assertAlmostEqual(factors[month],ipc['2026-06']/value,places=8)
 def test_annual_identities_and_latest_vintage(self):
  a=json.loads((ROOT/'data/1816_archive.json').read_text(encoding='utf-8'));v=json.loads((ROOT/'data/1816_archive_vintages.json').read_text(encoding='utf-8'))
  self.assertEqual(len(a['reports']),18);self.assertEqual(len(a['annual_ratios']),214)
  self.assertEqual(len(v['annual_vintages']),1983)
  selected={}
  for row in sorted(v['annual_vintages'],key=lambda x:x['publication_date']):
   selected[row['province'],row['year']]=row
   self.assertLessEqual(abs(sum(row[k] for k in ['tax','royalties','national_tax','social_income','other_income'])-100),.31)
   self.assertLessEqual(abs(100-row['primary_spend']-row['primary']),.31)
   self.assertLessEqual(abs(row['primary']+row['interest_signed']-row['financial']),.31)
  self.assertEqual(selected,{(r['province'],r['year']):r for r in a['annual_ratios']})
 def test_rank_gaps_are_not_zero_or_backfilled(self):
  a=json.loads((ROOT/'data/1816_archive.json').read_text(encoding='utf-8'));v=json.loads((ROOT/'data/1816_archive_vintages.json').read_text(encoding='utf-8'))
  self.assertEqual(len(a['rank_history']),1080)
  self.assertEqual(min(r['period'] for r in a['rank_history']),'2015-Q1')
  self.assertEqual(len({(r['province'],r['period']) for r in a['rank_history']}),1080)
  self.assertTrue(all(r['rank'] is None or 1<=r['rank']<=24 for r in v['rank_vintages']))
  self.assertTrue(all('Source rank is zero' in e['reason'] for e in a['exceptions']))
  lp=next(r for r in a['rank_history'] if r['province']=='La Pampa' and r['period']=='2026-Q1');self.assertIsNone(lp['rank'])
 def test_national_constant_flows_and_real_yoy(self):
  ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader((ROOT/'data/ipc_national_index.csv').read_text(encoding='utf-8').splitlines())}
  spending=json.loads((ROOT/'data/national_operations.json').read_text(encoding='utf-8'))['spending']
  for r in spending['monthly_2026']:self.assertAlmostEqual(r['real_july2026'],r['value']*ipc['2026-07']/ipc[r['period']],places=6)
  for r in spending['rows']:self.assertAlmostEqual(r['real_yoy_pct'],100*((r['value']/r['previous'])/(ipc['2026-07']/ipc['2025-07'])-1),places=8)

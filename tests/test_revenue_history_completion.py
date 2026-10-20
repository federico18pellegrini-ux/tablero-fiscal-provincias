import csv, hashlib, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class HistoryCompletion(unittest.TestCase):
    def test_preserved_evidence_matches_hashes(self):
        audit=json.loads((ROOT/'data/revenue_history_completion.json').read_text(encoding='utf8'))
        self.assertEqual(audit['ron_existing_totals_checked'],494)
        for source in audit['sources']:
            self.assertEqual(hashlib.sha256((ROOT/'data/revenue-history-sources'/source['file']).read_bytes()).hexdigest(),source['sha256'])
            self.assertTrue(source['url'].startswith('https://'))
    def test_every_jurisdiction_has_complete_ron_total_and_cfi_history(self):
        with (ROOT/'serie_ron_2003_2025_normalizado.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
        provinces=json.loads((ROOT/'dashboard_manifest.json').read_text(encoding='utf8'))['province_universe']
        totals={'T O T A L','T O T A L | (1) + (2)','T O T A L | (1) + (2) + (3)','Total | (1) + (2)'}
        for province in provinces:
            for year in range(2003,2026):
                subset=[r for r in rows if r['province']==province and r['year']==str(year)]
                total=[r for r in subset if r['category'] in totals]
                cfi=[r for r in subset if r['category_normalized']=='CFI | Neta']
                self.assertEqual(len(total),1,(province,year))
                self.assertEqual(len(cfi),1,(province,year))
                self.assertLessEqual(float(cfi[0]['value_millions']),float(total[0]['value_millions'])+.02)
    def test_own_history_preserves_lapampa_missing_2025(self):
        with (ROOT/'serie_top_1984_2024_normalizado.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
        for province in ['CABA','Santiago del Estero']:
            self.assertEqual({int(r['year']) for r in rows if r['province']==province and r['tax']=='Total'},set(range(1984,2026)))
        self.assertFalse(any(r['province']=='La Pampa' and r['year']=='2025' for r in rows))

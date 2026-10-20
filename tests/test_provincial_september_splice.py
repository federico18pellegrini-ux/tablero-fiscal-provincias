import csv, json, re, unittest
from pathlib import Path
from scripts_build_real_dynamics import own_revenue_totals
ROOT=Path(__file__).resolve().parents[1]

class ProvincialSeptember(unittest.TestCase):
    def test_verified_totals_exclude_non_tax_and_do_not_impute(self):
        with (ROOT/'top_mensual_2026_normalizado.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
        totals=own_revenue_totals(rows)
        for province,total,count in [('Mendoza',153095.2925684,4),('Jujuy',30779.771797,3),('Neuquén',213019.87103239,4),('San Juan',34109.99712059,5),('Tucumán',122739.639219,5)]:
            subset=[r for r in rows if r['province']==province and r['period']=='2026-09']
            self.assertEqual(len(subset),count)
            self.assertTrue(all(float(r['value_millions'])>0 for r in subset))
            self.assertAlmostEqual(totals[province,'2026-09'],total,places=6)
            self.assertNotIn((province,'2026-09'),own_revenue_totals(subset[:-1]))
        dynamics=json.loads((ROOT/'dashboard_real_dynamics_2026.json').read_text(encoding='utf8'))
        for province in ['Mendoza','Jujuy','Neuquén','San Juan','Tucumán']:
            self.assertEqual(dynamics['provinces'][province]['metrics']['own_revenue']['ytd_available_through'],'2026-09')

    def test_new_provincial_sources_reconcile_and_preserve_missingness(self):
        import hashlib
        review=json.loads((ROOT/'data/provincial_recent_sources_review.json').read_text(encoding='utf8'))
        with (ROOT/'top_mensual_2026_normalizado.csv').open(encoding='utf8') as f: rows=list(csv.DictReader(f))
        totals=own_revenue_totals(rows)
        expected={('Chaco','2026-09'):49647427929.12,('Río Negro','2026-09'):81165178752.70,('La Rioja','2026-09'):17346453062.33,('Salta','2026-08'):82325496441.11,('Salta','2026-09'):81832989100.03,('La Pampa','2026-08'):50753032618.22}
        for item in review['observations']:
            key=(item['province'],item['period'])
            if key not in expected: continue
            self.assertEqual(hashlib.sha256((ROOT/item['source_file']).read_bytes()).hexdigest(),item['sha256'])
            self.assertAlmostEqual(totals[key],expected[key]/1e6,places=6)
        salta=[r for r in rows if r['province']=='Salta' and r['period']=='2026-08']
        self.assertEqual(next(float(r['value_millions']) for r in salta if r['tax']=='Otros'),0)
        self.assertFalse(any(r['tax']=='Automotores' for r in salta))
        self.assertNotIn(('La Pampa','2026-09'),totals)

    def test_splice_preserves_anchor_and_relative_prices(self):
        html=(ROOT/'index.html').read_text(encoding='utf8')
        factors=json.loads(re.search(r'const DEFLACTOR_MONTH = (\{.*?\});',html)[1])
        observations=json.loads((ROOT/'data/ipc_san_luis_2014_2016_review.json').read_text(encoding='utf8'))['observations']
        anchor=observations[-1]['index_base_2003']
        historical=json.loads(re.search(r'const HISTORICAL_DEFLATOR = (\{.*?\});',html)[1])
        factors.update(historical)
        self.assertEqual(factors['2016-12'],118.264103)
        self.assertNotIn('2013-12',factors)
        for r in observations:
            self.assertAlmostEqual(factors[r['period']]/factors['2016-12'],anchor/r['index_base_2003'],places=10)
        self.assertIn('IPC San Luis empalmado con IPC nacional en diciembre de 2016',html)


import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ManagementClosureTest(unittest.TestCase):
    def test_proposals_preserve_coverage_and_observed_bases(self):
        d=json.loads((ROOT/'data/management_proposals.json').read_text(encoding='utf-8'))
        self.assertEqual(len(d['rows']),96)
        self.assertEqual(len({r['provincia'] for r in d['rows']}),24)
        for r in d['rows']:
            self.assertIn('no aprobada',r['estado'])
            if r['meta_propuesta'] is None:
                self.assertIn('cobertura suficiente',r['criterio'])
            else:
                lo,hi=sorted([r['valor_base'],r['referencia_mediana']])
                self.assertGreaterEqual(r['meta_propuesta'],lo-.01)
                self.assertLessEqual(r['meta_propuesta'],hi+.01)
            self.assertTrue(r['fuente'].startswith('https://'))

    def test_opc_currency_units_and_documented_rounding(self):
        d=json.loads((ROOT/'data/maturities_opc.json').read_text(encoding='utf-8'))
        self.assertEqual([r['period'] for r in d['rows']],[f'2026-{m:02d}' for m in range(7,13)])
        self.assertEqual(sum(r['ars_millions'] for r in d['rows']),d['published_totals']['ars_millions'])
        self.assertEqual(sum(r['usd_millions'] for r in d['rows']),d['published_totals']['usd_millions']-1)
        self.assertIn('redondeo',d['reconciliation_note'])
        self.assertEqual(len(d['source_sha256']),64)

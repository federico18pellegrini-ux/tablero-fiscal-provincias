import unittest
from scripts_build_national_benefits import build


class NationalBenefitsTests(unittest.TestCase):
    def test_archived_extractions_and_source_hashes_reproduce_series(self):
        data = build()
        self.assertEqual(len(data['rows']), 32)
        self.assertEqual(data['rows'][0]['period'], '2023-12')
        self.assertEqual(data['rows'][-1]['period'], '2026-09')
        self.assertEqual(data['rows'][-1]['minimum_bonus'], 498633)
        self.assertEqual(data['rows'][-1]['auh'], 154031)
        self.assertIsNone(data['rows'][-1]['ipc'])
        corrections = {r['period']: r for r in data['meta']['corrections']}
        self.assertEqual(corrections['2026-09']['printed_total'], 498663)
        self.assertEqual(corrections['2026-03']['calculated_total'], 439601)

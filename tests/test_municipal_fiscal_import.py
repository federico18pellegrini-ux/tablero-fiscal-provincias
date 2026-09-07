"""Reject fiscal source errors before the published data file is written."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts_build_municipal_dashboard import ROOT, apply_verified_fiscal


class MunicipalFiscalImportTests(unittest.TestCase):
    def setUp(self):
        self.audit = json.loads((ROOT / 'municipios/data/fiscal_verified.json').read_text(encoding='utf-8'))
        self.rows = {m['id']: m for m in json.loads((ROOT / 'municipios/data/dashboard.json').read_text(encoding='utf-8'))['municipalities']}

    def apply(self, audit):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'audit.json'
            path.write_text(json.dumps(audit), encoding='utf-8')
            return apply_verified_fiscal(copy.deepcopy(self.rows), path)

    def test_wrong_total_is_rejected(self):
        self.audit['records'][0]['amounts']['gastos_totales'] = '9000000000.00'
        with self.assertRaisesRegex(ValueError, 'Unreconciled'):
            self.apply(self.audit)

    def test_different_period_cannot_enter_semester_ranking(self):
        self.audit['records'][0]['fin'] = '2026-03-31'
        with self.assertRaisesRegex(ValueError, 'Non-comparable'):
            self.apply(self.audit)

    def test_duplicate_municipality_is_rejected(self):
        self.audit['records'].append(copy.deepcopy(self.audit['records'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.apply(self.audit)


if __name__ == '__main__':
    unittest.main()

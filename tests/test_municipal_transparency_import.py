"""Reject incomplete coverage and transcription errors in ASAP publication scores."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts_build_municipal_dashboard import ROOT, apply_transparency


class MunicipalTransparencyImportTests(unittest.TestCase):
    def setUp(self):
        self.audit = json.loads((ROOT / 'municipios/data/transparency_asap.json').read_text(encoding='utf-8'))
        self.rows = {m['id']: m for m in json.loads((ROOT / 'municipios/data/dashboard.json').read_text(encoding='utf-8'))['municipalities']}

    def apply(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'asap.json'
            path.write_text(json.dumps(self.audit), encoding='utf-8')
            return apply_transparency(copy.deepcopy(self.rows), path)

    def test_total_must_reconcile_with_components(self):
        self.audit['editions'][0]['records'][0]['score'] -= 1
        with self.assertRaisesRegex(ValueError, 'Unreconciled'):
            self.apply()

    def test_missing_or_duplicate_municipality_is_rejected(self):
        records = self.audit['editions'][1]['records']
        removed = records.pop()
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.apply()
        records.append(copy.deepcopy(records[0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.apply()
        records[-1] = removed
        self.assertEqual(self.apply()['coverage'], 135)

    def test_component_points_must_follow_methodology(self):
        record = self.audit['editions'][0]['records'][0]
        record['components']['accesibilidad'] = 3
        record['score'] = sum(record['components'].values())
        with self.assertRaisesRegex(ValueError, 'Invalid ASAP components'):
            self.apply()


if __name__ == '__main__':
    unittest.main()

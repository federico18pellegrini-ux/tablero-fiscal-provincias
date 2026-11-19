import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ClosedExecution(unittest.TestCase):
    def test_complete_october_reconciles_every_breakdown_and_preserves_scope(self):
        data = json.loads((ROOT / 'nacion/data/execution-closed.json').read_text(encoding='utf8'))
        self.assertEqual(data['period'], '2026-10')
        self.assertEqual(len(data['groups']['funcion']), 29)
        self.assertEqual(len(data['groups']['programa']), 410)
        self.assertAlmostEqual(data['total']['credito_devengado'], 128237280.51381895, places=5)
        self.assertAlmostEqual(data['total']['october_accrued'], 12385713.0390578, places=5)
        self.assertAlmostEqual(data['total']['variacion_real_pct'], -.9413068788, places=7)
        for kind, rows in data['groups'].items():
            self.assertAlmostEqual(sum(r['credito_devengado'] for r in rows), data['total']['credito_devengado'], places=4)
            self.assertAlmostEqual(sum(r['credito_devengado_octubre'] for r in rows), data['total']['october_accrued'], places=4)
            if kind != 'funcion':
                self.assertTrue(all('variacion_real_pct' not in r for r in rows))
        for source in data['sources']:
            raw = (ROOT / source['path']).read_bytes()
            if source['path'].endswith('.json'):
                raw = raw.replace(b'\r\n', b'\n')
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
        management = json.loads((ROOT / 'nacion/data/gestion.json').read_text(encoding='utf8'))
        self.assertEqual(management['execution']['closed'], data)


if __name__ == '__main__':
    unittest.main()

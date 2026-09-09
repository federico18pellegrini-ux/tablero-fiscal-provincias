import json
import unittest
from scripts_build_municipal_tools import ROOT, coverage, outputs


class MunicipalTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
        cls.coverage=coverage(cls.data)

    def test_status_is_mutually_exclusive_and_missing_does_not_mean_zero(self):
        rows=self.coverage['municipalities']
        self.assertEqual(len(rows),135)
        self.assertEqual(sum(r['comparable'] for r in rows),72)
        counts={label:sum(r['fiscalStatus']==label for r in rows) for label in ['Comparable a junio de 2026','Otro período','Ejecución parcial','Cuenta no verificada']}
        self.assertEqual(list(counts.values()),[72,18,1,44])
        heras=next(r for r in rows if r['id']=='06329')
        self.assertTrue(heras['comparable'])
        self.assertTrue(any('Préstamos bancarios 2024' in v for v in heras['missing']))
        self.assertTrue(any('Gasto en personal' in v for v in next(r for r in rows if r['id']=='06042')['missing']))
        self.assertFalse(next(r for r in rows if r['id']=='06805')['comparable'])

    def test_every_missing_sector_and_unavailable_period_is_identified(self):
        by_id={r['id']:r for r in self.coverage['municipalities']}
        for m in self.data['municipalities']:
            text=' '.join(by_id[m['id']]['missing'])
            for s in m['sectors']:
                if s['jobs'] is None:self.assertIn(s['name'],text)
            if m['crecimiento_poblacion_2010_2022_pct'] is None:self.assertIn('límites territoriales',text)
        self.assertIn('2026-08-31',next(r for r in self.coverage['municipalities'] if r['id']=='06112')['latestFiscalEnd'])

    def test_checked_in_outputs_are_current(self):
        for p,expected in outputs().items():
            self.assertEqual(p.read_text(encoding='utf-8'),expected,str(p))

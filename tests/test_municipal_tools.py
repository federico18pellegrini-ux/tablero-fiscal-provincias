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
        self.assertEqual(sum(r['comparable'] for r in rows),76)
        counts={label:sum(r['fiscalStatus']==label for r in rows) for label in ['Comparable a junio de 2026','Otro período','Ejecución parcial','Cuenta no verificada']}
        self.assertEqual(list(counts.values()),[76,15,0,44])
        heras=next(r for r in rows if r['id']=='06329')
        self.assertTrue(heras['comparable'])
        self.assertTrue(any('Préstamos bancarios 2024' in v for v in heras['missing']))
        self.assertFalse(any('Gasto en personal' in v for v in next(r for r in rows if r['id']=='06042')['missing']))
        self.assertTrue(next(r for r in rows if r['id']=='06805')['comparable'])

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

    def test_global_gaps_are_also_identified_for_each_municipality(self):
        for row in self.coverage['municipalities']:
            topics = {r['topic'] for r in row['documentsNeeded']}
            self.assertTrue({'Caja libre', 'Calendario futuro de deuda', 'Flujos fiscales mensuales'} <= topics)
        topics = {r['topic']: r['available'] for r in self.coverage['topics']}
        self.assertEqual(topics['Presupuesto vigente 2026'], 85)
        self.assertEqual(topics['Presupuesto original 2026'], 22)
        self.assertEqual(topics['Saldo de tesorería'], 2)
        self.assertEqual(topics['Caja libre'], 0)

    def test_matrix_preserves_reserved_zero_and_historical_states(self):
        matrix = self.coverage['matrix']
        self.assertEqual(len({(r['id'], r['tema']) for r in matrix}), len(matrix))
        self.assertEqual(len(matrix), 135 * len(self.coverage['topics']))
        heras = {r['tema']: r for r in matrix if r['id'] == '06329'}
        self.assertEqual(heras['Préstamos y depósitos bancarios']['estado'], 'Reservado o sin cifra de origen')
        self.assertEqual(heras['Cierres fiscales anuales 2021–2025']['estado'], 'Historia parcial')
        self.assertEqual(heras['Delitos registrados']['estado'], 'Incorporado')
        self.assertEqual(heras['Presupuesto original 2026']['estado'], 'Pendiente')
        self.assertEqual(heras['Presupuesto vigente 2026']['estado'], 'Incorporado')

    def test_located_draft_and_broken_link_are_not_verified_data(self):
        by_id = {r['id']: r for r in self.coverage['municipalities']}
        self.assertFalse(by_id['06252']['budgetOriginal2026'])
        self.assertTrue(any(f['state'] == 'draft_not_approved' for f in by_id['06252']['findings']))
        self.assertFalse(by_id['06270']['comparable'])
        self.assertTrue(any(f['state'] == 'broken_link' for f in by_id['06270']['findings']))

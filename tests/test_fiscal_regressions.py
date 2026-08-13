import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FiscalRegressionTests(unittest.TestCase):
    def test_pba_nation_flow_is_presented_as_territorial_comparison(self):
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('national_collection_registered_millions:25805282', html)
        self.assertIn('ron_received_millions:9990745', html)
        self.assertIn('No equivale al aporte jurídico a la masa coparticipable', html)
        self.assertIn('ARCA incluye seguridad social y aduana', html)

    def test_federal_fairness_uses_ron_with_consensus_compensation(self):
        with (ROOT / 'serie_ron_2003_2025_normalizado.csv').open(encoding='utf-8', newline='') as source:
            expected_millions = sum(
                float(row['value_millions'])
                for row in csv.DictReader(source)
                if row['province'] == 'Buenos Aires'
                and row['year'] == '2025'
                and row['category_normalized'] == 'Total | (1) + (2)'
            )
        payload = json.loads((ROOT / 'dashboard_federal_fairness.json').read_text(encoding='utf-8'))
        pba = payload['provinces']['Buenos Aires']
        population = pba['metrics']['population']['value']
        actual = pba['metrics']['ron_per_capita_pesos']['value']
        self.assertAlmostEqual(actual, expected_millions * 1_000_000 / population, places=6)

    def test_federal_contribution_is_not_proxied_with_own_revenue(self):
        payload = json.loads((ROOT / 'dashboard_federal_fairness.json').read_text(encoding='utf-8'))
        pba = payload['provinces']['Buenos Aires']
        self.assertIsNone(pba['metrics']['estimated_contribution_share_pct']['value'])
        self.assertEqual(pba['status'], 'partial')

    def test_aguinaldo_and_current_savings_are_not_inferred_from_financial_result(self):
        payload = json.loads((ROOT / 'dashboard_fiscal_provincias.json').read_text(encoding='utf-8'))
        pba = payload['provinces']['Buenos Aires']
        self.assertIsNone(pba['ahorro_corriente'])
        self.assertIsNone(pba['ahorro_corriente_ratio'])
        self.assertIsNone(pba['meses_cobertura'])
        self.assertEqual(pba['riesgo_aguinaldo'], 'sin_dato')

    def test_claims_cutoff_comes_from_source_rows(self):
        with (ROOT / 'data/reclamos_nacion/reclamos_nacion_provincias_maestra.csv').open(encoding='utf-8', newline='') as source:
            expected = max(row['fecha_corte_monto'] for row in csv.DictReader(source) if row['fecha_corte_monto'])
        payload = json.loads((ROOT / 'dashboard_reclamos_nacion_provincias.json').read_text(encoding='utf-8'))
        self.assertEqual(payload['cutoff_date'], expected)


if __name__ == '__main__':
    unittest.main()

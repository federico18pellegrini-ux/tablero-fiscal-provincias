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

    def test_federal_fairness_has_all_23_provinces_and_caba(self):
        payload = json.loads((ROOT / 'dashboard_federal_fairness.json').read_text(encoding='utf-8'))
        pba = payload['provinces']['Buenos Aires']['metrics']
        self.assertEqual(pba['ron_per_capita_rank_23_provinces']['value'], 23)
        self.assertEqual(pba['ron_per_capita_rank_23_provinces']['total'], 23)
        self.assertAlmostEqual(pba['received_share_pct']['value'], 22.71180315445706, places=6)
        self.assertEqual(pba['population']['value'], 17523996)
        with (ROOT / 'serie_ron_2003_2025_normalizado.csv').open(encoding='utf-8', newline='') as source:
            rows = list(csv.DictReader(source))
        provinces = {
            row['province'] for row in rows
            if row['year'] == '2025' and row['category_normalized'] == 'Total | (1) + (2)'
        }
        self.assertIn('CABA', provinces)
        self.assertIn('Santiago del Estero', provinces)

    def test_dependency_never_combines_incompatible_monthly_windows(self):
        payload = json.loads((ROOT / 'dashboard_fiscal_provincias.json').read_text(encoding='utf-8'))
        self.assertIsNone(payload['provinces']['Buenos Aires']['dependencia_nacion_pct'])
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('ron2025.value/ingresosTot', frontend)
        self.assertIn("national_tax_share_pct", frontend)
        self.assertNotIn('calcIANDebug', frontend)
        self.assertNotIn('shareAportaNacion', frontend)
        self.assertIn('PBA_AUDITED_FEDERAL_FALLBACK', frontend)
        self.assertIn('national_tax_share_ltm_1t26_pct:39.3', frontend)
        self.assertIn('ron_per_capita_2025_pesos:781320.3070780153', frontend)

    def test_pba_debt_has_audited_local_fallback(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('|| EMBEDDED_PBA_DEBT_PROFILE', frontend)
        self.assertIn('total_usd_m_equivalent:12056.758559', frontend)
        self.assertIn('debt_to_ltm_income_pct:45.232757', frontend)
        self.assertIn('payable_foreign_currency_pct:78.6', frontend)
        self.assertIn('interest_paid_to_total_resources_pct:3.5', frontend)
        self.assertIn('debt_service_paid_to_total_resources_pct:7.0', frontend)

    def test_executive_balance_uses_same_period_ranks_as_structural_cards(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn("storedOrCalculatedRank(c.rank_autonomia_fiscal", frontend)
        self.assertIn("storedOrCalculatedRank(c.rank_resultado_financiero", frontend)
        self.assertIn("storedOrCalculatedRank(c.rank_deuda_total", frontend)

    def test_deflator_uses_official_2026_ipc_and_april_base(self):
        with (ROOT / 'deflactor_mensual.csv').open(encoding='utf-8', newline='') as source:
            rows = {row['period']: row for row in csv.DictReader(source)}
        self.assertEqual(float(rows['2026-01']['ipc_mom']), 0.029)
        self.assertEqual(float(rows['2026-02']['ipc_mom']), 0.029)
        self.assertEqual(float(rows['2026-03']['ipc_mom']), 0.034)
        self.assertEqual(float(rows['2026-04']['ipc_mom']), 0.026)
        self.assertEqual(float(rows['2026-04']['factor_to_latest']), 1.0)
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn("let displayMode = 'nominal'", frontend)
        self.assertIn("if(!factor || isNaN(factor)) return null", frontend)
        self.assertNotIn("if(!factor || isNaN(factor)) return value", frontend)

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

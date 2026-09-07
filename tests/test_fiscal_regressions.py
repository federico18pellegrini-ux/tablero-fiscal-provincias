import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FiscalRegressionTests(unittest.TestCase):
    def test_pba_nation_flow_answers_contribution_and_return_question(self):
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('pba_generated_national_taxes_millions:76100000', html)
        self.assertIn('pba_automatic_resources_received_millions:13691853.935953911', html)
        self.assertIn('¿Cuánto aporta Buenos Aires y cuánto vuelve?', html)
        self.assertIn('Vuelven ${shown}', html)
        self.assertNotIn('Nación registra en PBA', html)
        self.assertNotIn('$38,7 de cada $100', html)

        with (ROOT / 'data/federal/pba_aporte_asignacion_2025.csv').open(encoding='utf-8', newline='') as source:
            row = next(csv.DictReader(source))
        generated = float(row['pba_generated_national_taxes_millions'])
        received = float(row['pba_automatic_resources_received_millions'])
        self.assertAlmostEqual(received / generated * 100, float(row['return_to_pba_per_100']), places=9)
        self.assertAlmostEqual(received / generated * 100, 17.991923700333654, places=9)

        with (ROOT / 'serie_ron_2003_2025_normalizado.csv').open(encoding='utf-8', newline='') as source:
            official_ron = next(
                float(item['value_millions'])
                for item in csv.DictReader(source)
                if item['province'] == 'Buenos Aires'
                and item['year'] == '2025'
                and item['category_normalized'] == 'Total | (1) + (2)'
            )
        self.assertAlmostEqual(received, official_ron, places=6)

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
        self.assertIn('"total_usd_m_equivalent":12056.758559', frontend)
        self.assertIn('"debt_to_ltm_income_pct":45.232757', frontend)
        self.assertIn('"payable_foreign_currency_pct":78.6', frontend)
        self.assertIn('"interest_paid_to_total_resources_pct":3.5', frontend)
        self.assertIn('"debt_service_paid_to_total_resources_pct":7.0', frontend)

    def test_executive_balance_uses_same_period_ranks_as_structural_cards(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn("storedOrCalculatedRank(c.rank_autonomia_fiscal", frontend)
        self.assertIn("storedOrCalculatedRank(c.rank_resultado_financiero", frontend)
        self.assertIn("storedOrCalculatedRank(c.rank_deuda_total", frontend)
        self.assertIn("ocupa el puesto ${nRank(rankAutonomia)} de 23", frontend)
        self.assertIn("los impuestos de origen nacional todavía equivalen al", frontend)

    def test_flow_values_separate_amount_from_period(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn("periodo:ownRevenuePeriod,periodoEnFila:true", frontend)
        self.assertIn("periodo:transferPeriod,periodoEnFila:true", frontend)
        self.assertNotIn("province!=='Buenos Aires'||r.period<='2026-03'", frontend)
        self.assertNotIn("`${fmtPesosKPI(topYtdResolved)} · ${ownRevenuePeriod}`", frontend)
        self.assertNotIn("`${fmtPesosKPI(ronYtdResolved)} · ${transferPeriod}`", frontend)

        with (ROOT / 'deflactor_mensual.csv').open(encoding='utf-8', newline='') as source:
            factors = {row['period']: float(row['factor_to_latest']) for row in csv.DictReader(source)}
        with (ROOT / 'informacion_consolidada_2026_normalizado.csv').open(encoding='utf-8', newline='') as source:
            pba_q1 = [
                row for row in csv.DictReader(source)
                if row['province'] == 'Buenos Aires'
                and row['period_type'] == 'month'
                and row['period'] <= '2026-03'
                and row['category_normalized'] == 'Total | (1) + (2)'
            ]
        q1_constant_june = sum(float(row['value_millions']) * factors[row['period']] for row in pba_q1)
        self.assertEqual(round(q1_constant_june), 4_191_433)

    def test_deflator_uses_official_2026_ipc_and_june_base(self):
        with (ROOT / 'deflactor_mensual.csv').open(encoding='utf-8', newline='') as source:
            rows = {row['period']: row for row in csv.DictReader(source)}
        self.assertAlmostEqual(float(rows['2026-01']['ipc_mom']), 0.029, delta=0.0005)
        self.assertAlmostEqual(float(rows['2026-02']['ipc_mom']), 0.029, delta=0.0005)
        self.assertAlmostEqual(float(rows['2026-03']['ipc_mom']), 0.034, delta=0.0005)
        self.assertAlmostEqual(float(rows['2026-04']['ipc_mom']), 0.026, delta=0.0005)
        self.assertAlmostEqual(float(rows['2026-05']['ipc_mom']), 0.021, delta=0.0005)
        self.assertAlmostEqual(float(rows['2026-06']['ipc_mom']), 0.019, delta=0.0005)
        self.assertEqual(float(rows['2026-06']['factor_to_latest']), 1.0)
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn("let displayMode = 'nominal'", frontend)
        self.assertIn("!Number.isFinite(factor)||factor<=0", frontend)
        self.assertNotIn("if(!factor || isNaN(factor)) return value", frontend)

    def test_current_2026_sources_reconcile_and_do_not_impute_missing_months(self):
        with (ROOT / 'top_mensual_2026_normalizado.csv').open(encoding='utf-8', newline='') as source:
            top = list(csv.DictReader(source))
        by_province_period = {}
        for row in top:
            by_province_period.setdefault((row['province'], row['period']), 0.0)
            by_province_period[(row['province'], row['period'])] += float(row['value_millions'])
        self.assertAlmostEqual(by_province_period[('Chubut', '2026-01')], 67605.819445, places=6)
        caba_january = {
            row['tax']: float(row['value_millions'])
            for row in top if row['province'] == 'CABA' and row['period'] == '2026-01'
        }
        self.assertAlmostEqual(caba_january['Iibb'], 759579.1, places=6)
        self.assertAlmostEqual(sum(caba_january.values()), 1124942.9, places=6)
        self.assertNotEqual(caba_january['Iibb'], sum(caba_january.values()))
        self.assertEqual(max(row['period'] for row in top if row['province'] == 'Buenos Aires'), '2026-06')

        with (ROOT / 'informacion_consolidada_2026_normalizado.csv').open(encoding='utf-8', newline='') as source:
            ron = list(csv.DictReader(source))
        ron_by_province_period = {}
        for row in ron:
            if row['period_type'] != 'month':
                continue
            key = (row['province'], row['period'])
            ron_by_province_period.setdefault(key, {})[row['category_normalized']] = float(row['value_millions'])
        for key, values in ron_by_province_period.items():
            total = values.get('Total | (1) + (2)')
            base = values.get('Total | Recursos | Origen Nacional | (1)')
            if total is None or base is None:
                continue
            compensation = values.get('Compensación Consenso Fiscal', 0.0)
            self.assertAlmostEqual(total, base + compensation, places=5, msg=f'RON no reconcilia para {key}')
        monthly_totals = {
            (row['province'], row['period']) for row in ron
            if row['period_type'] == 'month' and row['category_normalized'] == 'Total | (1) + (2)'
        }
        self.assertEqual({province for province, period in monthly_totals if period == '2026-07'}, {
            'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Corrientes', 'Córdoba',
            'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja', 'Mendoza', 'Misiones',
            'Neuquén', 'Río Negro', 'Salta', 'San Juan', 'San Luis', 'Santa Cruz', 'Santa Fe',
            'Santiago del Estero', 'Tierra del Fuego', 'Tucumán'
        })

    def test_modular_decision_views_and_rigid_floor_are_explicit(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        for view in ('summary', 'debt', 'income', 'federal', 'comparison', 'results'):
            self.assertIn(f'data-view="{view}"', frontend)
            self.assertIn(view, frontend)
        self.assertIn("localStorage.setItem('dashboard_profile'", frontend)
        self.assertIn("localStorage.setItem('dashboard_modules_v2'", frontend)
        self.assertIn('Cuánto del ingreso ya está comprometido', frontend)
        with (ROOT / 'data/gasto_rigido.csv').open(encoding='utf-8', newline='') as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(rows), 23)
        row = rows[0]
        self.assertEqual(row['evidence_status'], 'auditado_ampliado')
        self.assertAlmostEqual(float(row['observed_floor_pct']), 66.399937, places=6)
        self.assertAlmostEqual(float(row['automatic_transfers_pct']), 13.342013, places=6)
        self.assertAlmostEqual(float(row['total_rigid_pct']), 79.741950, places=6)

        with (ROOT / 'data/fiscal/rigid_spending_components_1t26.csv').open(encoding='utf-8', newline='') as source:
            raw = next(csv.DictReader(source))
        numerator = sum(float(raw[key]) for key in (
            'personnel_ars_m', 'social_security_spending_ars_m', 'interest_ars_m'
        ))
        self.assertAlmostEqual(
            numerator / float(raw['total_income_ars_m']) * 100,
            float(row['observed_floor_pct']),
            places=6,
        )
        rigid_by_province = {item['province']: item for item in rows}
        with (ROOT / 'data/fiscal/rigid_spending_components_1t26.csv').open(encoding='utf-8', newline='') as source:
            raw_rows = list(csv.DictReader(source))
        self.assertEqual(set(rigid_by_province), {item['province'] for item in raw_rows})
        for raw_item in raw_rows:
            result = rigid_by_province[raw_item['province']]
            income = float(raw_item['total_income_ars_m'])
            expected_components = {
                'personnel_pct': float(raw_item['personnel_ars_m']) / income * 100,
                'social_security_spending_pct': float(raw_item['social_security_spending_ars_m']) / income * 100,
                'interest_pct': float(raw_item['interest_ars_m']) / income * 100,
            }
            for field, expected in expected_components.items():
                self.assertAlmostEqual(float(result[field]), expected, places=6)
            expected_floor = sum(expected_components.values())
            self.assertAlmostEqual(float(result['observed_floor_pct']), expected_floor, places=6)
        self.assertEqual(round(float(row['interest_pct']), 1), 3.8)

    def test_profiles_have_distinct_modules_order_and_detail(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        for profile in ('governor', 'hacienda', 'press'):
            self.assertIn(f'{profile}:{{', frontend)
            self.assertIn(f'value="{profile}"', frontend)
        self.assertIn("governor:{label:'Gobernador'", frontend)
        self.assertIn("views:['summary','debt','income','federal','comparison','results']", frontend)
        self.assertIn("views:['summary','debt','income','comparison','federal','results']", frontend)
        self.assertIn("views:['summary','federal','comparison','debt','income','results']", frontend)
        self.assertIn('id="governorDecisionPanel"', frontend)
        self.assertIn('id="governorRiskPanel"', frontend)
        self.assertLess(frontend.index('id="governorDecisionPanel"'), frontend.index('id="governorRiskPanel"'))
        self.assertIn('data-press-source="financial"', frontend)
        self.assertIn('id="pressQuoteGrid"', frontend)

    def test_coverage_gaps_and_unified_flow_format_are_visible(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn("CROSS_SECTION_GAPS_3T25=new Set(['Santiago del Estero','La Pampa','Neuquén'])", frontend)
        self.assertIn("HISTORICAL_REVENUE_GAPS=new Set(['CABA','Santiago del Estero'])", frontend)
        self.assertIn('cada bloque informa su fuente, fecha y datos faltantes', frontend)
        self.assertIn('return `AR$ ${fmtNum(billones,2)} billones`', frontend)
        self.assertNotIn('millones (= ${fmtNum(bn,2)} Bn)', frontend)

    def test_charts_are_lazy_and_province_rows_are_cached(self):
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('const provinceRenderCache=new Map()', frontend)
        self.assertIn('function renderActiveViewCharts()', frontend)
        self.assertIn("if(dashboardView==='income')", frontend)
        self.assertNotIn('function destroyCharts()', frontend)
        render_body = frontend[frontend.index('function render(province)'):frontend.index('function liquiditySemaphore')]
        self.assertNotIn("chartTopMensual(topMensualRowsValid)", render_body)
        self.assertNotIn('buildComparativo();', render_body)

    def test_pba_municipal_transfer_extension_reconciles(self):
        with (ROOT / 'data/pba_municipal_transfers_ltm_1t26.csv').open(encoding='utf-8', newline='') as source:
            rows = list(csv.DictReader(source))
        detail = [row for row in rows if row['category'] != 'TOTAL']
        total = next(row for row in rows if row['category'] == 'TOTAL')
        self.assertAlmostEqual(
            sum(float(row['amount_ars_m']) for row in detail),
            float(total['amount_ars_m']),
            delta=0.002,
        )
        self.assertAlmostEqual(float(total['pct_ltm_total_income']), 13.342013, places=6)

    def test_pba_debt_schedule_reconciles_and_is_not_called_monthly_cash(self):
        with (ROOT / 'data/debt/pba_debt_service_schedule_2026_2041.csv').open(encoding='utf-8', newline='') as source:
            rows = list(csv.DictReader(source))
        self.assertEqual([int(row['year']) for row in rows], list(range(2026, 2042)))
        for row in rows:
            self.assertAlmostEqual(
                float(row['amortization_ars_m']) + float(row['interest_ars_m']),
                float(row['total_service_ars_m']),
                delta=1,
            )
        first = rows[0]
        self.assertEqual(float(first['total_service_ars_m']), 3637755)
        with (ROOT / 'data/gasto_rigido.csv').open(encoding='utf-8', newline='') as source:
            rigid = next(csv.DictReader(source))
        income = 36_857_309
        amortization_pct = float(first['amortization_ars_m']) / income * 100
        indicative_residual = 100 - float(rigid['total_rigid_pct']) - amortization_pct
        self.assertEqual(round(amortization_pct, 1), 6.2)
        self.assertEqual(round(indicative_residual, 1), 14.1)
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('Calendario anual de servicios de deuda', frontend)
        self.assertIn('no el calendario mensual', frontend)
        self.assertIn('31/12/2025</span>', frontend)
        self.assertIn('Es una referencia de presión, no un porcentaje discrecional', frontend)

    def test_government_results_preserve_scope_and_missing_social_outcome(self):
        payload = json.loads((ROOT / 'data/government_results_pba.json').read_text(encoding='utf-8'))
        pillars = {pillar['id']: pillar for pillar in payload['pillars']}
        self.assertAlmostEqual(pillars['security']['metrics'][0]['value'], 4.44294830150959)
        self.assertEqual(pillars['education']['metrics'][0]['value'], 5001493)
        self.assertEqual(pillars['health']['metrics'][0]['value'], 100061869)
        self.assertEqual(pillars['infrastructure']['metrics'][0]['value'], 315)
        self.assertEqual(pillars['social']['status'], 'faltante')
        self.assertEqual(payload['cost_per_result']['status'], 'not_calculated')
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('Resultados de gobierno', frontend)
        self.assertIn('CABA y Santiago del Estero', frontend)

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
        frontend = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('todavía no podemos calcular cómo llegará la caja a los próximos 90 o 180 días', frontend)
        self.assertNotIn('90 días: administrable', frontend)

    def test_claims_cutoff_comes_from_source_rows(self):
        with (ROOT / 'data/reclamos_nacion/reclamos_nacion_provincias_maestra.csv').open(encoding='utf-8', newline='') as source:
            expected = max(row['fecha_corte_monto'] for row in csv.DictReader(source) if row['fecha_corte_monto'])
        payload = json.loads((ROOT / 'dashboard_reclamos_nacion_provincias.json').read_text(encoding='utf-8'))
        self.assertEqual(payload['cutoff_date'], expected)
        self.assertEqual(payload['provinces']['Buenos Aires']['deuda_total_reclamada'], 319680000000.0)


if __name__ == '__main__':
    unittest.main()

import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GovernorBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "scripts_build_governor_brief.py"], cwd=ROOT, check=True)
        cls.payload = json.loads((ROOT / "dashboard_governor_brief.json").read_text(encoding="utf-8"))

    def test_latest_snapshot_reconciles(self):
        with (ROOT / "data/1816/pba_fiscal_snapshots.csv").open(encoding="utf-8", newline="") as source:
            latest = list(csv.DictReader(source))[-1]
        income = float(latest["total_income_m"])
        spending = float(latest["primary_spending_m"])
        primary = float(latest["primary_result_m"])
        interest = float(latest["interest_m"])
        financial = float(latest["financial_result_m"])
        self.assertAlmostEqual(income - spending, primary, delta=1)
        self.assertAlmostEqual(primary + interest, financial, delta=1)

    def test_quarter_and_ltm_are_explicitly_separated(self):
        metrics = {item["id"]: item for item in self.payload["key_metrics"]}
        self.assertEqual(metrics["financial_ltm"]["window"], "últimos 12 meses")
        self.assertEqual(metrics["quarter_financial"]["window"], "enero-marzo 2026")
        self.assertEqual(metrics["financial_ltm"]["value"], -6.6)
        self.assertEqual(metrics["quarter_financial"]["value"], -3.9)

    def test_decision_layer_has_required_shape(self):
        self.assertEqual(self.payload["status"], "se_deteriora")
        self.assertIn("gradual, productiva y federal", self.payload["plain_language_verdict"])
        self.assertIn("37", self.payload["federal_reading"])
        self.assertIn("problema federal real", self.payload["federal_conclusion"])
        self.assertEqual(len(self.payload["risks"]), 3)
        self.assertEqual(len(self.payload["decisions"]), 3)
        self.assertGreaterEqual(len(self.payload["missing_for_decision"]), 3)

    def test_each_metric_declares_measurement_basis(self):
        for metric in self.payload["key_metrics"]:
            self.assertTrue(metric["measurement"])
            self.assertTrue(
                any(word in metric["measurement"].lower() for word in ("nominal", "relativo")),
                metric["measurement"],
            )

    def test_ranking_universe_is_complete(self):
        with (ROOT / "data/1816/ranking_1t26.csv").open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(rows), 23)
        self.assertEqual({int(row["general_rank"]) for row in rows}, set(range(1, 24)))
        pba = next(row for row in rows if row["province"] == "Buenos Aires")
        self.assertEqual(int(pba["general_rank"]), 16)
        self.assertEqual(int(pba["debt_rank"]), 23)

    def test_frontend_uses_latest_ranking_and_full_width_structural_layout(self):
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("ranking_1816_1t26", frontend)
        self.assertIn("key-indicators-row{grid-template-columns:minmax(0,1fr)!important", frontend)
        self.assertIn("#metricsDetails:not([open]) #metricsDetailsTableWrap{display:none}", frontend)
        self.assertIn("Situación fiscal de la Provincia de Buenos Aires", frontend)
        self.assertIn("CONCLUSIÓN · SE DETERIORA", frontend)
        self.assertIn("prepareInfoDots", frontend)
        self.assertIn("gov-federal-summary", frontend)
        self.assertNotIn('id="federalSectionReading"', frontend)
        self.assertNotIn("Análisis integral IA · inferencia político-fiscal", frontend)
        self.assertIn("Recursos que llegan desde Nación", frontend)
        self.assertIn("% nominal", frontend)
        self.assertIn("Esto no permite afirmar una mejora real", frontend)
        self.assertIn('id="exResFinRank"', frontend)
        self.assertIn('id="exAutonomiaRank"', frontend)
        self.assertIn('id="exRigidezRank"', frontend)
        self.assertIn('id="exCapitalRank"', frontend)
        self.assertIn("Puesto ${Math.round(rank)} de ${Math.round(total)}", frontend)
        self.assertIn("Ranking comparable: 23 jurisdicciones", frontend)
        self.assertIn('id="debtCreditorsDonut"', frontend)
        self.assertIn('id="debtProfileInterest"', frontend)
        self.assertIn('id="debtProfileService"', frontend)
        self.assertIn("pba_debt_profile_2026q1", frontend)
        self.assertIn("estos indicadores ya están explicados dentro de la ficha principal de deuda", frontend)
        self.assertIn('id="executivePulseTitle"', frontend)
        self.assertIn('id="genericKpiSection"', frontend)
        self.assertLess(frontend.index('id="kRank"'), frontend.index('id="governorVerdict"'))
        self.assertIn("latestPbaDebt.total_usd_m_equivalent", frontend)
        self.assertNotIn('<div class="sh">Indicadores clave</div>\n<div class="kpi-grid">', frontend)
        self.assertNotIn("Lectura rápida · provincia", frontend)
        self.assertNotIn("Metodología rápida · indicadores compuestos", frontend)
        self.assertNotIn("Advertencia de comparabilidad 2026", frontend)
        self.assertNotIn("Marco presupuestario 2026", frontend)
        self.assertNotIn('id="budgetSection"', frontend)

    def test_latest_pba_debt_profile_reconciles(self):
        profile = json.loads((ROOT / "data/debt/pba_debt_profile_2026q1.json").read_text(encoding="utf-8"))
        stock = profile["latest_stock"]
        creditor_total = sum(item["ars_m"] for item in stock["creditors"])
        creditor_pct = sum(item["pct"] for item in stock["creditors"])
        self.assertAlmostEqual(creditor_total, stock["total_ars_m"], delta=0.01)
        self.assertAlmostEqual(creditor_pct, 100, delta=0.001)
        self.assertAlmostEqual(
            stock["total_ars_m"] / stock["a3500_ars_per_usd"],
            stock["total_usd_m_equivalent"],
            delta=0.01,
        )
        self.assertAlmostEqual(
            stock["total_ars_m"] / stock["ltm_total_income_ars_m"] * 100,
            stock["debt_to_ltm_income_pct"],
            delta=0.001,
        )


if __name__ == "__main__":
    unittest.main()

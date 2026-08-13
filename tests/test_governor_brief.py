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
        self.assertIn("productiva, federal y gradual", self.payload["political_reading"])
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


if __name__ == "__main__":
    unittest.main()

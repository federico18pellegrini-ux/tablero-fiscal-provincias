import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data/government_results_provinces.json"
CSV_PATH = ROOT / "data/government_results/official_metrics.csv"


class GovernmentResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        with CSV_PATH.open(encoding="utf-8", newline="") as source:
            cls.rows = list(csv.DictReader(source))

    def test_covers_exactly_the_24_jurisdictions(self):
        expected = set(self.payload["province_universe"])
        self.assertEqual(len(expected), 24)
        self.assertEqual(set(self.payload["provinces"]), expected)
        self.assertEqual({row["province"] for row in self.rows}, expected)
        self.assertEqual(len(self.rows), 24)
        for province in expected:
            pillar_ids = {pillar["id"] for pillar in self.payload["provinces"][province]["pillars"]}
            self.assertEqual(
                pillar_ids,
                {"security", "education", "health", "social", "infrastructure", "effort"},
            )

    def test_official_metrics_have_no_silent_gaps(self):
        required = {
            "security_rate_2024",
            "security_rate_2025",
            "education_language_high_2024",
            "education_math_high_2024",
            "education_student_participation_pct",
            "health_infant_mortality_2022",
            "health_infant_mortality_2023",
            "health_infant_mortality_2024",
            "population_2024",
            "nbi_households_pct_2010",
            "nbi_households_pct_2022",
            "spend_security_pc_2024",
            "spend_health_pc_2024",
            "spend_education_culture_pc_2024",
            "spend_social_assistance_pc_2024",
        }
        for row in self.rows:
            self.assertFalse([field for field in required if row.get(field, "") == ""], row["province"])
            for field in required:
                self.assertGreaterEqual(float(row[field]), 0, f"{row['province']} {field}")

    def test_changes_and_three_year_average_reconcile(self):
        rows = {row["province"]: row for row in self.rows}
        for province, row in rows.items():
            expected_security = (float(row["security_rate_2025"]) / float(row["security_rate_2024"]) - 1) * 100
            self.assertAlmostEqual(float(row["security_change_pct"]), expected_security, places=10)
            expected_health = sum(float(row[f"health_infant_mortality_{year}"]) for year in (2022, 2023, 2024)) / 3
            self.assertAlmostEqual(float(row["health_infant_mortality_avg_2022_2024"]), expected_health, places=10)
            security_metric = self.payload["provinces"][province]["pillars"][0]["metrics"][0]
            self.assertAlmostEqual(security_metric["change"], expected_security, places=10)

    def test_competition_ranks_reconcile_and_education_quality_is_visible(self):
        def ranks(field, reverse=False, eligible=lambda row: True):
            rows = [row for row in self.rows if eligible(row)]
            ordered = sorted(rows, key=lambda row: float(row[field]), reverse=reverse)
            return {
                row["province"]: 1 + sum(
                    float(other[field]) < float(row[field]) if not reverse
                    else float(other[field]) > float(row[field])
                    for other in ordered
                )
                for row in ordered
            }

        security_ranks = ranks("security_rate_2025")
        health_ranks = ranks("health_infant_mortality_2024")
        nbi_ranks = ranks("nbi_households_pct_2022")
        eligible = lambda row: row["education_rank_eligible"] == "True"
        language_ranks = ranks("education_language_high_2024", reverse=True, eligible=eligible)
        excluded = {row["province"] for row in self.rows if not eligible(row)}
        self.assertEqual(excluded, {"Neuquén", "Santa Cruz"})
        self.assertEqual(len(language_ranks), 22)

        for province, province_data in self.payload["provinces"].items():
            pillars = {pillar["id"]: pillar for pillar in province_data["pillars"]}
            self.assertEqual(pillars["security"]["metrics"][0]["rank"], security_ranks[province])
            self.assertEqual(pillars["health"]["metrics"][0]["rank"], health_ranks[province])
            self.assertEqual(pillars["social"]["metrics"][0]["rank"], nbi_ranks[province])
            education = pillars["education"]
            self.assertEqual(education["metrics"][0]["rank"], language_ranks.get(province))
            self.assertEqual(education["metrics"][0]["rank_total"], 22)
            if province in excluded:
                self.assertEqual(education["status"], "parcial")
                self.assertIn("excluye del ranking", education["quality_note"])

    def test_result_context_and_effort_are_not_collapsed(self):
        self.assertNotIn("composite", self.payload)
        self.assertIn("no se calcula un ranking general", self.payload["rank_rules"]["no_composite"])
        pba = {pillar["id"]: pillar for pillar in self.payload["provinces"]["Buenos Aires"]["pillars"]}
        self.assertEqual(pba["security"]["indicator_type"], "resultado")
        self.assertEqual(pba["social"]["indicator_type"], "contexto_estructural")
        self.assertEqual(pba["effort"]["indicator_type"], "esfuerzo_fiscal")
        self.assertIn("no demuestra", pba["effort"]["quality_note"])
        self.assertTrue(self.payload["provinces"]["Buenos Aires"]["local_detail"])
        self.assertFalse(self.payload["provinces"]["Córdoba"]["local_detail"])
        local_labels = {
            metric["label"]
            for pillar in self.payload["provinces"]["Buenos Aires"]["local_detail"]
            for metric in pillar.get("metrics", [])
        }
        self.assertTrue({
            "Víctimas registradas",
            "Matrícula total",
            "Unidades de servicio",
            "Consultas médicas",
            "Egresos hospitalarios",
            "Edificios escolares finalizados",
            "Creaciones / sustituciones",
        }.issubset(local_labels))

    def test_manifest_and_frontend_use_the_federal_layer(self):
        manifest = json.loads((ROOT / "dashboard_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["files"]["government_results"], "data/government_results_provinces.json")
        frontend = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("government_results_provinces.json", frontend)
        self.assertNotIn("Esta primera versión está auditada sólo para Buenos Aires", frontend)
        self.assertIn("Sin ranking · baja participación", frontend)
        self.assertIn("No se construye un ranking político compuesto", frontend)


if __name__ == "__main__":
    unittest.main()

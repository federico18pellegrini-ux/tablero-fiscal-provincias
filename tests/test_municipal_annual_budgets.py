import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader
from scripts_municipal_budgets import apply_annual_budgets
from scripts_export_municipal_reports import money

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / 'municipios/data/annual_budgets_verified.json'


class AnnualBudgets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(REGISTER.read_text(encoding='utf-8'))
        cls.data = json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
        cls.municipalities = {m['id']: m for m in cls.data['municipalities']}

    def test_complete_coverage_and_authoritative_missingness(self):
        municipalities = copy.deepcopy(self.municipalities)
        municipalities['06028']['annualBudget'] = {'amount': 1}
        _, coverage = apply_annual_budgets(municipalities, REGISTER)
        self.assertEqual(coverage, self.data['annualBudgetCoverage'])
        self.assertEqual((coverage['available'], coverage['currentYear'], coverage['historical'], coverage['pending']), (107, 100, 7, 28))
        self.assertIsNone(municipalities['06028']['annualBudget'])
        for m in municipalities.values():
            b = m['annualBudget']
            if b:
                self.assertAlmostEqual(b['perCapita']*m['poblacion_2022'], b['amount'], delta=.001)
                self.assertEqual(b['amount'], b[b['basis']])

    def test_year_cutoff_and_spending_authorization_remain_distinct(self):
        b = self.municipalities['06756']['annualBudget']  # San Isidro: Q2 has movements only.
        self.assertEqual((b['asOf'], b['current']), ('2026-03-31', 333076160469.20))
        self.assertIsNone(b['original'])
        self.assertEqual(self.municipalities['06270']['annualBudget']['year'], 2025)
        self.assertTrue(self.municipalities['06270']['annualBudget']['historical'])
        b = self.municipalities['06805']['annualBudget']
        self.assertEqual(b['original'], 578906001955)
        self.assertEqual(b['current'], 611294558622.66)
        b = self.municipalities['06638']['annualBudget']
        self.assertEqual(b['original'], 488609779242)
        self.assertIsNone(b['current'])

    def test_reject_quarter_movements_bad_reconciliation_and_missing_source(self):
        for mutation in ['quarter', 'sum', 'source', 'coverage']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                audit = copy.deepcopy(self.audit)
                r = next(r for r in audit['records'] if r['current'] is not None and r['components'])
                if mutation == 'quarter': r['periodStart'] = f"{r['year']}-04-01"
                if mutation == 'sum': r['current'] = str(float(r['current'])+1000)
                if mutation == 'source': r['documents'][0]['sha256'] = ''
                if mutation == 'coverage': audit['pending'].pop()
                path = Path(tmp)/'audit.json'
                path.write_text(json.dumps(audit), encoding='utf-8')
                with self.assertRaises(ValueError): apply_annual_budgets(copy.deepcopy(self.municipalities), path)

    def test_catalog_preserves_unknowns_and_pdf_matches_budget(self):
        with (ROOT/'municipios/data/presupuestos_anuales.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 135)
        self.assertEqual(next(r for r in rows if r['id']=='06028')['Vigente ARS'], '')
        for ident in ['06329', '06805', '06638', '06270', '06371', '06756']:
            with self.subTest(id=ident):
                b = self.municipalities[ident]['annualBudget']
                pdf = PdfReader(ROOT/f'municipios/reports/informe-{ident}.pdf')
                text = ' '.join(p.extract_text() for p in pdf.pages)
                self.assertIn(money(b['perCapita'], 0, False), text)
                self.assertIn('Censo 2022', text)
                self.assertIn(money(b['amount'])+' millones', text)
                if b['historical']: self.assertIn('falta verificar el presupuesto de 2026', text)

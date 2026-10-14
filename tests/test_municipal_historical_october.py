import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HistoricalMunicipalAccounts(unittest.TestCase):
    def test_originals_reconcile_and_never_enter_semester_ranking(self):
        records = json.loads((ROOT/'municipios/data/fiscal-sources/2026-10-14/register.json').read_text(encoding='utf8'))
        data = json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf8'))
        municipalities = {m['id']:m for m in data['municipalities']}
        self.assertEqual(len(records), 14)
        for r in records:
            m = municipalities[r['id']]
            self.assertIsNone(m['fiscal'])
            self.assertEqual(m['fiscalOther']['fin'], r['fin'])
            a = {k:Decimal(v) for k,v in r['amounts'].items()}
            self.assertEqual(a['ingresos_corrientes']+a['ingresos_capital'], a['ingresos_totales'])
            self.assertEqual(a['gastos_corrientes']+a['gastos_capital'], a['gastos_totales'])
            self.assertEqual(a['ingresos_totales']-a['gastos_totales'], a['resultado_financiero'])
            for d in r['documents']:
                self.assertEqual(hashlib.sha256((ROOT/d['archive']).read_bytes()).hexdigest(), d['sha256'])

    def test_berazategui_uses_fiscal_not_budgetary_expenditure(self):
        data = json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf8'))
        f = next(m for m in data['municipalities'] if m['id']=='06091')['fiscalOther']
        self.assertAlmostEqual(f['gastos_totales'], 147215721606.73)
        self.assertNotEqual(f['gastos_totales'], 153105592089.46)
        self.assertAlmostEqual(f['resultado_financiero'], 8516665231.16)

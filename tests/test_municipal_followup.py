import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MunicipalFollowup(unittest.TestCase):
    def test_six_accounts_reconcile_and_keep_original_evidence(self):
        records = json.loads((ROOT/'municipios/data/fiscal-sources/2026-10-04-seguimiento/register.json').read_text(encoding='utf-8'))
        self.assertEqual({r['id'] for r in records}, {'06056','06505','06547','06553','06763','06861'})
        for r in records:
            a = {k: Decimal(v) for k,v in r['amounts'].items()}
            self.assertEqual(a['ingresos_corrientes']+a['ingresos_capital'], a['ingresos_totales'])
            self.assertEqual(a['gastos_corrientes']+a['gastos_capital'], a['gastos_totales'])
            self.assertEqual(a['ingresos_totales']-a['gastos_totales'], a['resultado_financiero'])
            for d in r['documents']:
                self.assertEqual(hashlib.sha256((ROOT/d['archive']).read_bytes()).hexdigest(),d['sha256'])

    def test_mislabeled_monte_link_cannot_enter_semester_ranking(self):
        data = json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
        m = next(m for m in data['municipalities'] if m['id']=='06547')
        self.assertIsNone(m.get('fiscal'))
        self.assertEqual(m['fiscalOther']['fin'],'2026-03-31')
        self.assertAlmostEqual(m['fiscalOther']['resultado_financiero'],-5960749.37)
        self.assertEqual(m['annualBudget']['asOf'],'2026-03-31')

    def test_vicente_lopez_excludes_financing_and_preserves_verified_zero(self):
        data = json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
        m = next(m for m in data['municipalities'] if m['id']=='06861')
        self.assertEqual(m['fiscal']['ingresos_capital'],0)
        self.assertAlmostEqual(m['fiscal']['ingresos_totales'],167860564729.38)
        self.assertAlmostEqual(m['fiscal']['gastos_totales'],151027246618.55)
        self.assertAlmostEqual(m['annualBudget']['current'],362143765971.00)

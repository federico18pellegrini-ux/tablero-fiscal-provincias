import copy
import json
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path
from scripts_build_municipal_dashboard import ROOT, apply_management
from scripts_import_municipal_management import tigre_account, reconcile


class MunicipalManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=json.loads((ROOT/'municipios/data/management_verified.json').read_text(encoding='utf-8'))
        cls.data=json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
        cls.rows={r['id']:r for r in cls.data['municipalities']}

    def test_primary_history_reconciles_and_keeps_exact_dates(self):
        for m in self.audit['municipalities']:
            for f in m['history']:
                reconcile(f['amounts'])
                self.assertTrue(f['documents'])
                for doc in f['documents']:
                    self.assertRegex(doc['sha256'],r'^[a-f0-9]{64}$')
                    self.assertTrue(all(1<=p<=doc['pages'] for p in doc['consultedPages']))
        h=self.rows['06329']['management']['history']
        annual=next(f for f in h if f['inicio']=='2025-01-02' and f['fin']=='2025-12-31')
        self.assertEqual(annual['resultado_financiero'],-1594242085.78)
        self.assertEqual(annual['ingresos_totales'],15002958521.83)
        self.assertEqual(annual['gastos_totales'],16597200607.61)
        self.assertEqual(annual['method'],'sum_semesters')
        self.assertFalse(any(f['fin']=='2023-12-31' for f in h))
        self.assertEqual(next(f for f in h if f['fin']=='2022-12-30')['inicio'],'2022-01-03')

    def test_published_2025_bridge_reproduces_caif_including_project_inputs(self):
        c={k:D(v) for k,v in self.audit['controls']['tigre2025Bridge']['amounts'].items()}
        f=next(f for f in self.rows['06805']['management']['history'] if f['fin']=='2025-12-31')
        self.assertEqual(c['projectInputsIncludedInCapital'],D('6495045905.14'))
        self.assertEqual(c['budgetAccrued']-c['amortization']-c['priorLiabilities'],D(str(f['gastos_totales'])))
        self.assertEqual(f['resultado_financiero'],-1710500560.20)
        self.assertEqual(f['gastos_corrientes'],332237618608.56)
        self.assertEqual(f['gastos_capital'],55314299340.96)

    def test_project_inputs_interest_and_previous_liabilities_have_different_treatment(self):
        def e(code,value,program='01.01 - Gestión'):
            return {'code':code,'program':program,'amounts':{'accrued':D(value)}}
        expense=[e('1.1.1',50),e('2.1.1',10),e('2.9.3',20,'51.51.99 - Construcción'),e('4.2.1',30),e('5.1.1',5),e('5.2.1',7),e('6.2.3',3),e('7.3.3',2),e('7.4.3',11),e('7.6.1',100)]
        income=[{'code':'1.1.4','amounts':{'received':D(150)}},{'code':'2.1.1','amounts':{'received':D(10)}},{'code':'3.3.2','amounts':{'received':D(5)}}]
        f,bridge=tigre_account(expense,income)
        self.assertEqual(f['gastos_corrientes'],67)
        self.assertEqual(f['gastos_capital'],60)
        self.assertEqual(f['resultado_financiero'],38)
        self.assertEqual(bridge['priorLiabilities'],100)

    def test_treasury_components_and_liabilities_do_not_invent_free_cash(self):
        for ident in ['06329','06805']:
            t=self.rows[ident]['management']['treasury']
            self.assertAlmostEqual(t['currentLiabilities']+t['nonCurrentLiabilities'],t['liabilities'],places=2)
            self.assertNotIn('freeCash',t)
        h=self.rows['06329']['management']['treasury']
        self.assertAlmostEqual(h['available']+h['transitory'],h['closing'],places=2)
        t=self.rows['06805']['management']['treasury']
        self.assertEqual(t['date'],'2025-12-31')
        self.assertAlmostEqual(t['unearmarkedAccounts']+t['earmarkedAccounts'],t['budgetCash'],places=2)
        self.assertAlmostEqual(t['budgetCash']+t['thirdPartyAndSpecial'],t['closing'],places=2)
        debt=self.rows['06805']['management']['debt']
        self.assertEqual(debt['consolidated'],1502037.70)
        self.assertEqual(debt['floating'],33832574642.10)
        self.assertNotIn('schedule',debt)

    def test_import_rejects_overlap_and_unreconciled_budget(self):
        for kind in ['overlap','budget']:
            data=copy.deepcopy(self.audit)
            if kind=='overlap':
                f=next(f for f in data['municipalities'][0]['history'] if f['method']=='sum_semesters')
                f['components'][1]['inicio']='2025-06-30'
            else:data['municipalities'][0]['budget']['amounts']['unpaid']='0.00'
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'audit.json';p.write_text(json.dumps(data),encoding='utf-8')
                with self.assertRaises(ValueError):apply_management(copy.deepcopy(self.rows),p)

    def test_bcra_matches_existing_totals_and_preserves_reserved_raw_zeros(self):
        t=self.rows['06805']
        for r in t['management']['banking']['records'][:2]:
            for key,old in [('loans','prestamos'),('deposits','depositos')]:
                self.assertAlmostEqual(r[key],t[f'{old}_{r["date"][:4]}_ars'],places=2)
        for r in self.rows['06329']['management']['banking']['records']:
            self.assertEqual(r['status'],'reserved_or_unverified')
            self.assertNotIn('loans',r)
            self.assertNotIn('depositsReal',r)
        from scripts_build_municipal_dashboard import read_csv
        indices={r['period']:D(r['ipc_index']) for r in read_csv(ROOT/'data/ipc_national_index.csv')}
        for r in t['management']['banking']['records']:
            self.assertAlmostEqual(r['loansReal'],float(D(str(r['loans']))*indices['2026-07']/indices[r['date'][:7]]),places=2)


if __name__=='__main__':unittest.main()

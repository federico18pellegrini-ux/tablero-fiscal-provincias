import copy
import json
import unittest
from scripts_build_nacion_reclamos import ROOT, EVIDENCE_FILE, build_payload, build_outputs, validate_evidence

class ReclamosPipelineTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(EVIDENCE_FILE.read_text(encoding='utf-8'))
        self.universe=json.loads((ROOT/'dashboard_manifest.json').read_text(encoding='utf-8'))['province_universe']

    def test_missing_amounts_remain_unknown_and_all_provinces_exist(self):
        out=build_payload(self.data,self.universe)
        self.assertEqual(len(out['provinces']),24)
        self.assertEqual(out['coverage']['with_amounts'],12)
        self.assertEqual(out['coverage']['documents_without_amounts'],6)
        for province in out['provinces'].values():
            self.assertIsNone(province['saldo_actual_verificado'])
            self.assertNotIn('deuda_total_reclamada',province)
        self.assertEqual(out['provinces']['Catamarca']['records'],[])

    def test_no_aggregate_of_claims_currencies_agreements_or_payments(self):
        out=build_payload(self.data,self.universe)
        caba=out['provinces']['CABA']
        self.assertEqual([r['amount']['currency'] for r in caba['records']],['USD','ARS'])
        self.assertEqual([r['kind'] for r in caba['records']],['reclamo','acuerdo'])
        self.assertNotIn('total',out)
        self.assertNotIn('total',caba)
        self.assertEqual(out['provinces']['Santa Fe']['records'][0]['amount']['upper'],2e12)

    def test_pba_components_reconcile_without_being_added_twice(self):
        pba=self.data['provinces']['Buenos Aires']['records'][0]
        self.assertEqual(pba['amount']['value'],19.1e12)
        self.assertEqual(sum(p['value'] for p in pba['components']),19.1e12)
        pba['components'][0]['value']+=1e9
        self.assertTrue(any('no concilian' in e for e in validate_evidence(self.data,self.universe)))

    def test_rejects_duplicates_undocumented_amounts_and_invalid_dates(self):
        record=self.data['provinces']['Buenos Aires']['records'][0]
        self.data['provinces']['Buenos Aires']['records'].append(copy.deepcopy(record))
        record['source']['url']='https://example.com/informe'
        record['published_at']='2027-01-01'
        errors=' '.join(validate_evidence(self.data,self.universe))
        self.assertIn('duplicado',errors)
        self.assertIn('documento oficial',errors)
        self.assertIn('posterior',errors)

    def test_rejects_missing_jurisdictions_and_fabricated_balances(self):
        del self.data['provinces']['Catamarca']
        self.data['provinces']['Buenos Aires']['saldo_actual_verificado']=19.1e12
        errors=' '.join(validate_evidence(self.data,self.universe))
        self.assertIn('24 jurisdicciones',errors)
        self.assertIn('no verifica saldos',errors)

    def test_published_outputs_are_current(self):
        for path,expected in build_outputs(self.data,self.universe).items():
            self.assertEqual((ROOT/path).read_text(encoding='utf-8'),expected,path)
        fiscal=json.loads((ROOT/'dashboard_fiscal_provincias.json').read_text(encoding='utf-8'))
        for row in fiscal['provinces'].values():
            self.assertNotIn('deuda_total_reclamada',row['reclamos_nacion'])

    def test_monthly_amount_basis_is_explicit_and_requires_a_valid_amount(self):
        record=self.data['provinces']['La Pampa']['records'][0]
        self.assertEqual(record['amount_basis'],'mensual')
        self.assertEqual(record['amount']['value'],5e9)
        self.assertEqual(validate_evidence(self.data,self.universe),[])
        record['amount_basis']='anual_inferida'
        self.assertTrue(any('base temporal' in e for e in validate_evidence(self.data,self.universe)))
        record['amount_basis']='mensual'
        record['amount']=None
        record['kind']='sin_monto'
        self.assertTrue(any('base temporal' in e for e in validate_evidence(self.data,self.universe)))

if __name__=='__main__':
    unittest.main()

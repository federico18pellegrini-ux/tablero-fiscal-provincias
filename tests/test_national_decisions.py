import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scripts_build_national_decisions as subject


class NationalDecisionsTest(unittest.TestCase):
    def test_published_output_matches_archived_official_inputs(self):
        self.assertEqual(subject.build(), subject.load(subject.OUTPUT))

    def test_caif_separates_operating_result_and_financial_operations(self):
        rows={r['id']:r for r in subject.parse_caif(subject.DATA/'decision-sources/caif-2027.pdf')}
        self.assertEqual(len(rows),40)
        expected={'VI':202348174,'VII':202101433,'XI':246741,'XII':325784467,
                  'XII.2':324050562,'XIII':326031208,'XIII.2':306864929}
        for key,value in expected.items():self.assertEqual(rows[key]['project'],value)
        for year in ['closing','project']:
            self.assertLessEqual(abs(rows['XI'][year]+rows['XII'][year]-rows['XIII'][year]),1)
            self.assertEqual(rows['XII.3'][year],rows['XIII.3'][year])

    def test_policy_links_retain_periods_units_partial_information_and_missing_values(self):
        policies=subject.build()['policies']
        self.assertEqual([len(p['physical']) for p in policies],[14,13,4,11,11,7])
        for p in policies:
            self.assertEqual(p['execution']['corte'],'2026-09-15')
            self.assertTrue(all(m['trimestre']==2 for m in p['physical']))
            self.assertAlmostEqual(p['program']['accrued'],p['execution']['credito_devengado'],places=2)
            self.assertTrue(all(m['servicio_id']==p['link']['servicio_id'] and m['programa_id']==p['link']['programa_id'] for m in p['physical']))
        self.assertTrue(any(m['ejecutado_acumulado_trim2'] is None for m in policies[1]['physical']))
        self.assertTrue(any('parciales' in c['causa_desvio_comentario'] for m in policies[0]['physical'] for c in m['causas']))

    def test_wrong_or_ambiguous_correspondence_is_rejected(self):
        specs=copy.deepcopy(subject.POLICIES)
        item=list(specs[0]);item[-1]=(80,310,99);specs[0]=tuple(item)
        with patch.object(subject,'POLICIES',specs), self.assertRaises(AssertionError):subject.build()

    def test_additional_policies_distinguish_subprograms_units_and_methods(self):
        policies={p['slug']:p for p in subject.build()['policies']}
        for slug in ['jubilaciones','alimentacion','medicamentos','seguridad-federal']:
            p=policies[slug]
            for selected in p['editorial']['selection']:
                found=[r for r in p['physical'] if all(r[k]==v for k,v in selected.items())]
                self.assertEqual(len(found),1)
        self.assertEqual({k['subprograma_id'] for k in policies['jubilaciones']['editorial']['selection']},{1,3})
        self.assertEqual(len({k['unidad_medida_id'] for k in policies['medicamentos']['editorial']['selection'][:2]}),2)
        self.assertIn('promedios',policies['jubilaciones']['editorial']['reading'])
        self.assertIn('tasa de delitos',policies['seguridad-federal']['editorial']['recommendation'])
        self.assertIn('no informa una ejecución acumulada',policies['alimentacion']['editorial']['recommendation'])

    def test_portfolio_scope_and_actual_codes_reconcile_without_inventing_interior(self):
        from national_portfolios import build_portfolios
        b=subject.load(subject.DATA/'budget.json');g=subject.load(subject.DATA/'gestion.json');m=subject.load(subject.DATA/'gestion/metas_fisicas_trimestre_2.json')
        rows=build_portfolios(b,g,m)
        self.assertEqual(next(r for r in rows if r['name']=='Ministerio de Economía')['id'],50)
        interior=next(r for r in rows if r['id']==30)
        self.assertIsNone(interior['project']['project']);self.assertIsNone(interior['works_total'])
        self.assertGreater(interior['execution']['credito_devengado'],0)
        self.assertEqual(sum(r['physical']['count'] for r in rows),1889)
        self.assertEqual(sum(len(r['program_ids']) for r in rows),394)
        self.assertEqual(sum(len(r['work_ids']) for r in rows),435)
        bad=copy.deepcopy(g);bad['execution']['groups']['jurisdiccion'][0]['credito_vigente']+=1
        with self.assertRaises(AssertionError):build_portfolios(b,bad,m)
        bad=copy.deepcopy(b);bad['programs'][0]['project']+=100
        with self.assertRaises(AssertionError):build_portfolios(bad,g,m)

    def test_work_financing_reconciles_and_ra10_preserves_cost_vintage(self):
        w=subject.build()['works']
        self.assertEqual(len(w['rows']),435)
        self.assertEqual(w['totals']['total'],1317609)
        self.assertEqual(w['totals']['credito_externo'],276136)
        self.assertEqual(w['rounding_differences']['total'],6)
        for row in w['rows']:
            f=row['funding']
            self.assertLessEqual(abs(f['internas']+f['externas']-f['total']),1)
        p=w['pilot']
        self.assertEqual(p['project']['project'],39690)
        self.assertEqual(p['project']['funding']['tesoro'],39690)
        self.assertEqual(p['progress_pct'],85.47)
        self.assertEqual(p['reference_cost'],232217.6)
        self.assertEqual(p['observed']['corte'],'2026-03-31')
        self.assertIsNone(p['updated_completion_cost'])
        self.assertIsNone(p['completion_date'])
        a=p['announcement']
        self.assertEqual(a['source']['published'],'2026-09-04')
        self.assertEqual(a['assembly_pct'],96)
        self.assertEqual(a['assembly_scope'],'Montaje electromecánico')
        self.assertIn('2027',a['commissioning_completion_target'])
        self.assertIn('licencia',a['condition'])
        self.assertIsNone(a['updated_completion_cost'])


if __name__=='__main__':unittest.main()

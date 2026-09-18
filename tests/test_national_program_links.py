import copy
import hashlib
import json
import unittest
from pathlib import Path
from national_program_links import norm, verify_project_row, verify_context

ROOT = Path(__file__).resolve().parents[1]


class NationalProgramLinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((ROOT / 'nacion/data/program-sources/crosswalk.json').read_text(encoding='utf8'))
        cls.budget = json.loads((ROOT / 'nacion/data/budget.json').read_text(encoding='utf8'))
        cls.current = json.loads((ROOT / 'nacion/data/gestion/gasto_etapas_programa.json').read_text(encoding='utf8'))
        cls.sources = {s['file']: s for s in cls.evidence['sources']}

    def test_archived_originals_and_same_row_codes_names_amounts(self):
        for source in self.sources.values():
            raw = (ROOT / 'nacion' / source['path']).read_bytes()
            self.assertEqual(len(raw), source['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
        for entry in self.evidence['links']:
            verify_project_row(ROOT / 'nacion' / self.sources[entry['source']]['path'], entry)
        wrong = copy.deepcopy(self.evidence['links'][0])
        wrong['project'] += 1
        with self.assertRaises(AssertionError):
            verify_project_row(ROOT / 'nacion' / self.sources[wrong['source']]['path'], wrong)

    def test_baselines_reconcile_with_independently_normalized_execution(self):
        programs = {p['id']: p for p in self.budget['programs']}
        atoms = json.loads((ROOT/'nacion/data/program-sources/segemar-2026-activities.json').read_text(encoding='utf8'))
        for entry in self.evidence['links']:
            parts = entry.get('current_parts') or [{'key':entry['current_key']}]
            keys = {tuple(p['key']) for p in parts}
            rows = [r for r in self.current if tuple(r[k] for k in ['jurisdiccion_id','servicio_id','programa_id']) in keys]
            if entry['id'] in ['p279','p280']:
                # Independent arithmetic: Geology retains base activity and repository;
                # Geo-hazards gets seismic prevention, geological risks and the observatory.
                retained = [r for r in atoms if r['programa_id']==19 and (r['proyecto_id']==3 or (r['proyecto_id']==0 and r['actividad_id']==1))]
                rows = retained if entry['id']=='p279' else [r for r in atoms if r not in retained]
            program = programs[entry['id']]
            for current, target in [('credito_presupuestado','law'),('credito_vigente','current'),('credito_devengado','accrued')]:
                self.assertAlmostEqual(sum(row[current] for row in rows), program[target], places=5)
            self.assertTrue(program['matched'])
            self.assertEqual(program['project_code'], entry['project_code'])
            self.assertEqual(program['project'], entry['project'])
        self.assertEqual(set(self.budget['program_join']['ids']), {e['id'] for e in self.evidence['links']})
        self.assertEqual(26, self.budget['program_join']['documented_count'])

    def test_groups_reconcile_with_whole_organisms_and_never_add_to_national_total(self):
        programs = {p['id']:p for p in self.budget['programs']}
        for group in self.budget['program_join']['groups']:
            self.assertEqual(group['project'],sum(programs[pid]['project'] for pid in group['program_ids']))
            keys={tuple(p['key']) for p in group['current_parts']}
            rows=[r for r in self.current if tuple(r[k] for k in ['jurisdiccion_id','servicio_id','programa_id']) in keys]
            self.assertAlmostEqual(group['current'],sum(r['credito_vigente'] for r in rows),places=5)
            if group['id'] in ['cnea','enacom','segemar']:
                saf={'cnea':105,'enacom':207,'segemar':624}[group['id']]
                self.assertAlmostEqual(group['current'],sum(r['credito_vigente'] for r in self.current if r['servicio_id']==saf),places=5)
        self.assertEqual(self.budget['total']['project'],202101433)
        self.assertEqual(len(self.budget['programs']),394)

    def test_every_original_case_has_a_specific_documented_disposition(self):
        original={'p42','p52','p58','p59','p60','p67','p69','p71','p77','p103','p105','p107','p221','p228','p246','p252','p277','p280','p288','p342'}
        reviews=self.budget['program_join']['reviews']
        self.assertEqual({r['id'] for r in reviews},original)
        self.assertEqual(sum(r['status']=='comparable' for r in reviews),8)
        for r in reviews:
            self.assertTrue(r['reason'] and r['evidence'])
            if r['status']!='comparable':self.assertTrue(r['needed'])
        by_id={p['id']:p for p in self.budget['programs']}
        for pid in ['p63','p73','p248']:
            self.assertFalse(by_id[pid]['matched'])
            self.assertIsNone(by_id[pid]['current'])
            self.assertTrue(by_id[pid]['review']['group'])

    def test_unresolved_scope_changes_keep_missing_bases(self):
        missing = [p for p in self.budget['programs'] if not p['matched']]
        self.assertEqual(len(missing), 15)
        for program in missing:
            for key in ['law','current','accrued']:
                self.assertIsNone(program[key])
        self.assertTrue({'p103','p252','p248','p277'} <= {p['id'] for p in missing})

    def test_electoral_concentration_comes_from_official_activity_table(self):
        p = next(p for p in self.budget['programs'] if p['id'] == 'p78')
        c = p['comparison_context']
        verify_context(ROOT / 'nacion' / self.sources[c['source']]['path'], c)
        self.assertEqual(c['program_project'], p['project'])
        self.assertAlmostEqual(c['activity_project']/p['project']*100, 99.3, delta=.05)
        self.assertLess(p['current'], c['activity_project']/100)

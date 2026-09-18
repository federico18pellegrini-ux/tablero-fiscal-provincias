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
        keys = set()
        for entry in self.evidence['links']:
            key = tuple(entry['current_key'])
            self.assertNotIn(key, keys)
            keys.add(key)
            rows = [r for r in self.current if tuple(r[k] for k in ['jurisdiccion_id','servicio_id','programa_id']) == key]
            self.assertEqual(len(rows), 1)
            row, program = rows[0], programs[entry['id']]
            self.assertEqual(norm(row['programa_desc']), norm(entry['current_name']))
            for current, target in [('credito_presupuestado','law'),('credito_vigente','current'),('credito_devengado','accrued')]:
                self.assertAlmostEqual(row[current], program[target], places=5)
            self.assertTrue(program['matched'])
            self.assertEqual(program['current_key'], list(key))
            self.assertEqual(program['project_code'], entry['project_code'])
            self.assertEqual(program['project'], entry['project'])
        self.assertEqual(set(self.budget['program_join']['ids']), {e['id'] for e in self.evidence['links']})
        self.assertEqual(len(keys), self.budget['program_join']['documented_count'])

    def test_unresolved_scope_changes_keep_missing_bases(self):
        missing = [p for p in self.budget['programs'] if not p['matched']]
        self.assertEqual(len(missing), 20)
        for program in missing:
            for key in ['law','current','accrued']:
                self.assertIsNone(program[key])
        self.assertTrue({'p58','p77','p103','p252','p288'} <= {p['id'] for p in missing})

    def test_electoral_concentration_comes_from_official_activity_table(self):
        p = next(p for p in self.budget['programs'] if p['id'] == 'p78')
        c = p['comparison_context']
        verify_context(ROOT / 'nacion' / self.sources[c['source']]['path'], c)
        self.assertEqual(c['program_project'], p['project'])
        self.assertAlmostEqual(c['activity_project']/p['project']*100, 99.3, delta=.05)
        self.assertLess(p['current'], c['activity_project']/100)

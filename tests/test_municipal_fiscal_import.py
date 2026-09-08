"""Reject fiscal source errors before the published data file is written."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts_build_municipal_dashboard import ROOT, apply_verified_fiscal


class MunicipalFiscalImportTests(unittest.TestCase):
    def setUp(self):
        self.audit = json.loads((ROOT / 'municipios/data/fiscal_verified.json').read_text(encoding='utf-8'))
        self.rows = {m['id']: m for m in json.loads((ROOT / 'municipios/data/dashboard.json').read_text(encoding='utf-8'))['municipalities']}

    def apply(self, audit):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'audit.json'
            path.write_text(json.dumps(audit), encoding='utf-8')
            return apply_verified_fiscal(copy.deepcopy(self.rows), path)

    def test_wrong_total_is_rejected(self):
        self.audit['records'][0]['amounts']['gastos_totales'] = '9000000000.00'
        with self.assertRaisesRegex(ValueError, 'Unreconciled'):
            self.apply(self.audit)

    def test_every_semester_account_is_in_the_verified_register(self):
        published = {ident for ident, row in self.rows.items() if row.get('fiscal')}
        self.assertEqual(published, {record['id'] for record in self.audit['records']})

    def test_removed_record_cannot_survive_from_old_dashboard(self):
        removed = self.audit['records'].pop(0)['id']
        rows = copy.deepcopy(self.rows)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'audit.json'
            path.write_text(json.dumps(self.audit), encoding='utf-8')
            apply_verified_fiscal(rows, path)
        self.assertIsNone(rows[removed]['fiscal'])

    def test_missing_source_or_out_of_bounds_page_is_rejected(self):
        for documents in [[], [{**self.audit['records'][0]['documents'][0], 'consultedPages': [999]}]]:
            audit = copy.deepcopy(self.audit)
            audit['records'][0]['documents'] = documents
            with self.assertRaisesRegex(ValueError, 'Missing or invalid fiscal evidence'):
                self.apply(audit)

    def test_different_period_cannot_enter_semester_ranking(self):
        self.audit['records'][0]['fin'] = '2026-03-31'
        with self.assertRaisesRegex(ValueError, 'Non-comparable'):
            self.apply(self.audit)

    def test_duplicate_municipality_is_rejected(self):
        self.audit['records'].append(copy.deepcopy(self.audit['records'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.apply(self.audit)

    def test_other_period_keeps_its_dates_without_becoming_a_semester(self):
        self.audit['otherPeriods'][0]['fin'] = '2026-06-30'
        with self.assertRaisesRegex(ValueError, 'Comparable account placed outside'):
            self.apply(self.audit)

    def test_future_period_is_rejected(self):
        self.audit['otherPeriods'][0]['fin'] = '2026-12-31'
        with self.assertRaisesRegex(ValueError, 'Invalid fiscal period'):
            self.apply(self.audit)

    def test_overlapping_or_missing_quarter_is_rejected(self):
        for start in ['2026-03-31', '2026-04-02']:
            audit = copy.deepcopy(self.audit)
            summed = next(r for r in audit['records'] if r['method'] == 'sum_quarters')
            summed['components'][1]['inicio'] = start
            with self.assertRaisesRegex(ValueError, 'Non-contiguous'):
                self.apply(audit)

    def test_component_totals_must_match_the_promoted_semester(self):
        summed = next(r for r in self.audit['records'] if r['method'] == 'sum_quarters')
        component = summed['components'][0]['amounts']
        # The component still reconciles, but the semester no longer equals its two parts.
        from decimal import Decimal
        for key in ['ingresos_corrientes', 'ingresos_totales', 'resultado_financiero']:
            component[key] = str(Decimal(component[key]) + 100)
        with self.assertRaisesRegex(ValueError, 'Unreconciled fiscal components'):
            self.apply(self.audit)

    def test_opposite_errors_in_components_cannot_cancel_out(self):
        summed = next(r for r in self.audit['records'] if r['method'] == 'sum_quarters')
        from decimal import Decimal
        for component, change in zip(summed['components'], [100, -100]):
            a = component['amounts']
            a['ingresos_totales'] = str(Decimal(a['ingresos_totales']) + change)
        with self.assertRaisesRegex(ValueError, 'Unreconciled fiscal component:'):
            self.apply(self.audit)


if __name__ == '__main__':
    unittest.main()

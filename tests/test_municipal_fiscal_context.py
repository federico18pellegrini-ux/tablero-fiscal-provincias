import copy
import json
import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader
from scripts_build_municipal_dashboard import ROOT, valid_fiscal_location
from scripts_municipal_fiscal_context import apply_fiscal_context


class FiscalContext(unittest.TestCase):
    def setUp(self):
        self.audit = json.loads((ROOT/'municipios/data/fiscal_context_verified.json').read_text(encoding='utf8'))
        self.rows = {m['id']:m for m in json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf8'))['municipalities']}

    def apply(self, audit):
        rows = copy.deepcopy(self.rows)
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'context.json'
            p.write_text(json.dumps(audit),encoding='utf8')
            apply_fiscal_context(rows,p,valid_fiscal_location)
        return rows

    def test_history_and_secondary_figures_never_promote_a_common_ranking_account(self):
        rows = self.apply(self.audit)
        for ident in ['06028','06252']:
            self.assertIsNone(rows[ident]['fiscal'])
            self.assertEqual(rows[ident]['fiscalOther']['fin'],'2025-12-31')
        self.assertEqual([r['fin'][:4] for r in rows['06028']['fiscalHistory']],['2021','2022','2024'])
        self.assertEqual(rows['06252']['fiscalSupplement']['figures']['resultado_financiero'],26853)
        self.assertNotEqual(rows['06252']['fiscalSupplement']['figures']['resultado_financiero'],26852)

    def test_bad_identity_rounding_or_evidence_are_rejected(self):
        for change in ['identity','rounding','hash','precision','period']:
            a=copy.deepcopy(self.audit)
            if change=='identity':a['history'][0]['amounts']['ingresos_totales']='1'
            if change=='rounding':a['supplements'][0]['figures']['resultado_financiero']=26800
            if change=='hash':a['history'][0]['documents'][0]['sha256']='0'*64
            if change=='precision':a['supplements'][0]['precision']='exact'
            if change=='period':a['history'][0]['fin']='2026-06-30'
            with self.subTest(change=change),self.assertRaises(ValueError):self.apply(a)

    def test_removed_context_cannot_survive_a_previous_build(self):
        rows=self.apply({**self.audit,'history':[],'supplements':[]})
        self.assertNotIn('fiscalHistory',rows['06028'])
        self.assertNotIn('fiscalSupplement',rows['06252'])

    def test_full_pdf_preserves_source_scope_and_historical_dates(self):
        p=PdfReader(ROOT/'municipios/reports/informe-06252.pdf')
        text=' '.join(' '.join(page.extract_text() for page in p.pages).split())
        self.assertIn('157.885',text)
        self.assertIn('26.853',text)
        self.assertIn('fuente secundaria',text)
        self.assertIn('redondeados',text)
        self.assertIn('Fuentes: Moody',text)
        p=PdfReader(ROOT/'municipios/reports/informe-06028.pdf')
        text=' '.join(' '.join(page.extract_text() for page in p.pages).split())
        for year in ['2021','2022','2024','2025']:self.assertIn(year,text)
        self.assertIn('Historia de las cuentas',text)
        self.assertEqual(len(PdfReader(ROOT/'municipios/reports/informe-06252-breve.pdf').pages),3)

import json
import math
import re
import sys
import unittest
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts_export_national_reports as reports


class NationalReportsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reports.register_fonts()
        cls.data = json.loads((ROOT / 'nacion/data/budget.json').read_text(encoding='utf-8'))
        cls.catalog = json.loads((ROOT / 'nacion/reports/manifest.json').read_text(encoding='utf-8'))

    def test_annual_comparisons_use_average_cpi_and_preserve_missing_values(self):
        d = self.data
        for base in reports.BASES:
            r = reports.Report(d, 'real', base)
            expected = ((d['total']['project'] / d['deflator']['annual_average_index']['2027']) /
                        (d['total'][base] / d['deflator']['annual_average_index']['2026']) - 1) * 100
            self.assertAlmostEqual(r.variation(d['total']), expected, places=8)
            self.assertAlmostEqual(r.variation(d['total'], True), expected, places=8)
            self.assertIsNone(r.value(None))
            self.assertEqual(r.value(0), 0)
        self.assertIsNone(reports.change(100, 0))
        self.assertIsNone(reports.change(None, 100))
        self.assertEqual(reports.change(0, 100), -100)
        self.assertEqual(reports.num(None), 's/d')
        self.assertEqual(reports.pct(None), 's/c')

    def test_unmatched_programs_and_closing_base_never_invent_a_comparison(self):
        missing = [p for p in self.data['programs'] if not p['matched']]
        self.assertEqual(len(missing), 14)
        for base in reports.BASES:
            r = reports.Report(self.data, 'real', base)
            for program in missing:
                self.assertIsNone(r.variation(program, True))
        r = reports.Report(self.data, 'nominal', 'closing')
        self.assertTrue(all(r.variation(p) is None for p in self.data['programs']))

    def test_catalog_contains_every_price_and_base_and_matches_source(self):
        self.assertEqual(self.catalog['inputs'], reports.fingerprint())
        self.assertEqual({(r['price'], r['base']) for r in self.catalog['reports']},
                         {(p, b) for p in ['nominal', 'real'] for b in reports.BASES})
        for entry in self.catalog['reports']:
            self.assertEqual(entry['main']['pages'], 21)
            self.assertGreater(entry['full']['pages'], entry['main']['pages'])

    def test_pdfs_have_all_chapters_units_sources_numbering_and_selected_base(self):
        for entry in self.catalog['reports']:
            reader = PdfReader(ROOT / 'nacion/reports' / entry['main']['file'])
            texts = [p.extract_text() for p in reader.pages]
            for i, text in enumerate(texts):
                self.assertIn('Federico Pellegrini', text)
                self.assertIn(f'Página {i+1}', text)
                self.assertIn('tablero.federicopellegrini.com.ar/nacion/', text)
                self.assertIn(reports.BASES[entry['base']], text)
            all_text = ' '.join('\n'.join(texts).split())
            self.assertIn('IPC promedio', all_text)
            self.assertIn('no significa necesariamente haberla pagado', all_text)
            self.assertIn('69,1%', texts[7])
            self.assertIn('Septiembre (parcial)', texts[7])
            if entry['price'] == 'real':
                self.assertRegex(texts[7], r'Septiembre \(parcial\)\s+s/d')
            self.assertGreater(len(reader.pages[9].get('/Annots', [])), 9)
            for phrase in ['LECTURA CENTRAL', 'PRIORIDADES', 'ORGANISMOS', 'FUNCIONES', 'PROGRAMAS', 'TERRITORIO', 'INGRESOS Y ECONOMÍA', 'EJECUCIÓN', 'HISTORIA Y LECTURA FINAL', 'MÉTODO Y FUENTES']:
                self.assertIn(phrase, all_text)
            self.assertEqual(reader.metadata.author, 'Federico Pellegrini')
            self.assertIn('484.917', all_text)
            self.assertIn('2007', all_text)
            self.assertIn('1.889', all_text)
            self.assertIn('31/03/2026', all_text)
            self.assertIn('28 conjuntos', all_text)
            self.assertIn('DA 20/2026', texts[10])
            self.assertIn('DNU 867/2026', texts[10])
            for value in ['105.025', '5.080', '31/07', '31/03', 'Pesos / miles de millones']:
                self.assertIn(value, texts[11])

    def test_annex_preserves_every_program_and_project_exactly_once(self):
        # Each variant includes all source rows, not just the current UI search/page.
        for entry in self.catalog['reports']:
            reader = PdfReader(ROOT / 'nacion/reports' / entry['full']['file'])
            text = '\n'.join(p.extract_text() for p in reader.pages[19:])
            for prefix, key in [('p', 'programs'), ('w', 'works')]:
                ids = re.findall(r'\b(' + prefix + r'\d+)\s*·', text)
                self.assertEqual(len(ids), len(self.data[key]))
                self.assertEqual(set(ids), {r['id'] for r in self.data[key]})
            self.assertIn('El detalle de cada jurisdicción', text)

    def test_decision_sheets_match_the_full_report_and_keep_their_scope(self):
        text='\n'.join(p.extract_text() for p in PdfReader(ROOT/'nacion/reports/informe-nacional-nominal-current.pdf').pages[15:])
        for phrase in ['Cierre y financiamiento','Vacunas e inmunizaciones','Universidades','Reactor RA-10','85,47%','18.254.178','7 de 13','No publicado']:
            self.assertIn(phrase.upper() if phrase=='Cierre y financiamiento' else phrase,text)
        self.assertEqual(len(self.catalog['focused']),7)
        for entry in self.catalog['focused']:
            reader=PdfReader(ROOT/'nacion/reports'/entry['file'])
            self.assertEqual(len(reader.pages),1)
            page=reader.pages[0].extract_text()
            self.assertIn('Federico Pellegrini',page)
            self.assertIn('Página 1',page)
            self.assertGreaterEqual(len(reader.pages[0].get('/Annots',[])),3)

    def test_24_territorial_sheets_reconcile_and_keep_different_scopes_separate(self):
        from national_territory_report import territory_data
        from scripts_export_national_reports import money
        management=json.loads((ROOT/'nacion/data/gestion.json').read_text(encoding='utf-8'))
        self.assertEqual(len(self.catalog['territories']),24)
        for entry in self.catalog['territories']:
            t=territory_data(self.data,management,entry['province_id'])
            reader=PdfReader(ROOT/'nacion/reports'/entry['file'])
            self.assertEqual(len(reader.pages),1)
            text=reader.pages[0].extract_text()
            for term in [entry['province'],'Federico Pellegrini','Página 1','no se suman','Cierre estimado',money(t['province']['ron_2026']),money(t['worksTotal'])]:
                self.assertIn(term,text)
            self.assertGreaterEqual(len(reader.pages[0].get('/Annots',[])),4)
        with self.assertRaises(AssertionError):territory_data(self.data,management,999)

    def test_portfolio_reports_keep_the_selected_jurisdiction_money_and_short_length(self):
        decisions=json.loads((ROOT/'nacion/data/decisions.json').read_text(encoding='utf-8'))
        self.assertEqual(len(self.catalog['portfolios']),16)
        for entry in self.catalog['portfolios']:
            p=next(r for r in decisions['portfolios'] if r['id']==entry['portfolio_id'])
            pdf=PdfReader(ROOT/'nacion/reports'/entry['file'])
            self.assertIn(len(pdf.pages),[2,3])
            pages=[x.extract_text() for x in pdf.pages]
            text=' '.join(' '.join(pages).split())
            for term in [p['name'],reports.money(p['execution']['credito_pagado']),'15/09/2026','Cambio real']:
                self.assertIn(term,text)
            for i,page in enumerate(pages):
                self.assertIn(f'Página {i+1}',page)
                self.assertIn('Federico Pellegrini',page)
                self.assertIn('tablero.federicopellegrini.com.ar/nacion/',page)
            if p['id']==30:
                self.assertIn('no representa un recorte a cero',text)
                self.assertNotIn('-100,0%',text)
            else:self.assertIn(reports.money(p['project']['project']),text)
            self.assertGreater(sum(len(page.get('/Annots',[])) for page in pdf.pages),3)




class PrioritiesPdfTests(unittest.TestCase):
    def test_published_general_variants_include_observed_spending_and_deliveries(self):
        manifest=json.loads((ROOT/'nacion/reports/manifest.json').read_text(encoding='utf-8'))
        for entry in manifest['reports']:
            for variant in ['main','full']:
                pdf=PdfReader(ROOT/'nacion/reports'/entry[variant]['file'])
                text=' '.join(' '.join(p.extract_text() for p in pdf.pages[19:21]).split())
                for phrase in ['Qué cambia detrás del gasto total','109,66','108,57','10,21','13,19','12,15','4,1%',
                               'Ganar peso dentro del presupuesto no significa recibir más recursos',
                               'Del presupuesto a las personas','18.254.178','35.966','443.768','Promedio de becarios',
                               'enero–junio 2026','mínima con bono perdió','4,6%','25,1%','IPC observado']:
                    self.assertIn(phrase,text)
                self.assertGreater(len(pdf.pages[20].get('/Annots',[])),1)

    def test_spending_function_identity_matches_observed_denominator(self):
        from national_priorities_report import spending_rows
        b=json.loads((ROOT/'nacion/data/budget.json').read_text(encoding='utf-8'))
        g=json.loads((ROOT/'nacion/data/gestion.json').read_text(encoding='utf-8'))
        rows,totals=spending_rows(b,g)
        self.assertEqual(len(rows),29)
        self.assertAlmostEqual(totals[1],108570251.22678363,places=5)
        intel=next(r for r in rows if r['id']=='2-12')
        self.assertAlmostEqual(intel['after'],228915.62002183,places=5)
        self.assertAlmostEqual(sum(r['share_after'] for r in rows),100)

if __name__ == '__main__':
    unittest.main()

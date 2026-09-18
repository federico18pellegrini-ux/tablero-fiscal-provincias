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
        self.assertEqual(len(missing), 38)
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
            self.assertEqual(entry['main']['pages'], 15)
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

    def test_annex_preserves_every_program_and_project_exactly_once(self):
        # Each variant includes all source rows, not just the current UI search/page.
        for entry in self.catalog['reports']:
            reader = PdfReader(ROOT / 'nacion/reports' / entry['full']['file'])
            text = '\n'.join(p.extract_text() for p in reader.pages[15:])
            for prefix, key in [('p', 'programs'), ('w', 'works')]:
                ids = re.findall(r'\b(' + prefix + r'\d+)\s*·', text)
                self.assertEqual(len(ids), len(self.data[key]))
                self.assertEqual(set(ids), {r['id'] for r in self.data[key]})
            self.assertIn('El detalle de cada jurisdicción', text)


if __name__ == '__main__':
    unittest.main()

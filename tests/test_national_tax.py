import json
import unittest
from pathlib import Path
from pypdf import PdfReader
from scripts_build_national_tax import build

ROOT=Path(__file__).resolve().parents[1]

class NationalTaxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'nacion/data/tax-expenditures.json').read_text(encoding='utf8'))

    def test_same_publication_reconciles_and_2024_is_not_a_growth_base(self):
        self.assertEqual(build(),self.data)
        c=self.data['comparison']
        self.assertEqual(c['total_delta_pp'],-.05)
        self.assertEqual([r['year'] for r in c['years']],[2025,2026,2027])
        for row in c['years']:
            self.assertAlmostEqual(row['total'],row['norms']+row['promotion'],delta=.11)
        self.assertFalse(self.data['reference_2024']['comparable_growth'])
        self.assertEqual(self.data['reference_2024']['revised']['monotributo_pct'],1.13)
        self.assertIsNone(self.data['reference_2024']['separata']['updated_2027_amount'])

    def test_rigi_uses_six_sector_totals_and_keeps_fiscal_cost_missing(self):
        r=self.data['rigi']
        self.assertIsNone(r['fiscal_cost_2027'])
        self.assertEqual([x['total_usd_millions'] for x in r['plans']],[7612,7827])
        for year in r['plans']:
            self.assertEqual(len(year['sectors']),6)
            self.assertEqual(year['total_usd_millions'],sum(x['usd_millions'] for x in year['sectors']))
            self.assertIn('tecnologia',[x['id'] for x in year['sectors']])

    def test_every_general_pdf_and_focused_analysis_use_the_same_figures(self):
        m=json.loads((ROOT/'nacion/reports/manifest.json').read_text(encoding='utf8'))
        for item in m['reports']:
            for kind in ['main','full']:
                pages=PdfReader(ROOT/'nacion/reports'/item[kind]['file']).pages
                text=' '.join(' '.join(p.extract_text() for p in pages[21:23]).split())
                for phrase in ['3,67%','3,72%','0,05','3,45%','1,13%','7.827','76.173','95,9','componente parcial','supuestos']:
                    self.assertIn(phrase,text)
        focused=next(x for x in m['focused'] if x['scope']=='gasto-tributario')
        self.assertEqual(focused['pages'],2)
        pages=PdfReader(ROOT/'nacion/reports'/focused['file']).pages
        self.assertEqual(len(pages),2)
        self.assertGreaterEqual(len(pages[0].get('/Annots',[])),3)

if __name__=='__main__':unittest.main()

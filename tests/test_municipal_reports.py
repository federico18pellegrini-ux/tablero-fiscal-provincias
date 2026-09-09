import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader
from scripts_export_municipal_reports import ROOT, OUTPUT, fingerprint, build, money, number, month


class MunicipalReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'municipios/data/dashboard.json').read_text(encoding='utf-8'))
        cls.manifest=json.loads((OUTPUT/'manifest.json').read_text(encoding='utf-8'))
        cls.m=next(m for m in cls.data['municipalities'] if m['id']=='06329')
        cls.pdf=PdfReader(OUTPUT/'informe-06329.pdf')
        cls.text='\n'.join(p.extract_text() for p in cls.pdf.pages)

    def test_complete_current_catalog_and_documents(self):
        self.assertEqual(self.manifest['input_sha256'],fingerprint())
        entries=self.manifest['reports']
        self.assertEqual(len(entries),135)
        self.assertEqual({r['id'] for r in entries},{m['id'] for m in self.data['municipalities']})
        for r in entries:
            with self.subTest(id=r['id']):
                raw=(OUTPUT/r['file']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
                self.assertEqual(len(raw),r['bytes'])
                pdf=PdfReader(OUTPUT/r['file'])
                self.assertEqual(len(pdf.pages),r['pages'])
                self.assertEqual(pdf.metadata.author,'Federico Pellegrini')
                self.assertIn(r['municipality'],pdf.pages[0].extract_text())
                self.assertEqual(r['sections'],['lectura','prioridades','cuentas','transferencias','empleo','salarios','actividad','poblacion'])
                self.assertEqual(r['crimeYears'],[2024,2025])

    def test_general_las_heras_fiscal_money_and_price_bases(self):
        fiscal=self.m['fiscal']
        self.assertAlmostEqual(fiscal['ingresos_totales']-fiscal['gastos_totales'],1587567967.29,places=2)
        for key in ['ingresos_corrientes','ingresos_capital','ingresos_totales','gastos_corrientes','gastos_capital','gastos_totales','resultado_financiero','personal_devengado']:
            self.assertIn(money(fiscal[key],2),self.text)
        self.assertIn('$5.474,5',self.text)  # Nominal transfers, Jan-Jul 2026.
        self.assertIn('$5.842,9',self.text)  # Same flows in July 2026 purchasing power.
        self.assertIn('pesos corrientes, sin ajuste por inflación',self.text)
        self.assertIn('pesos constantes de 2004',self.text)

    def test_editorial_report_contains_verified_salary_and_context_not_removed_sections(self):
        for forbidden in ['Publicación de información fiscal','Los 27 indicadores en comparación','Escenarios de coparticipación','Anexo / transferencias','Anexo / empleo']:
            self.assertNotIn(forbidden,self.text)
        for value in ['$1.577.097','$2.117.275','$1.561.205','$2.377.942','5.038','37','22','58','28,0%']:
            self.assertIn(value,self.text)
        for definition in ['Real significa ajustado por inflación','necesidades básicas insatisfechas','SIPA','aguinaldo','No es el salario de bolsillo','Por qué la elegimos','Qué recomendamos']:
            self.assertIn(definition,self.text)
        self.assertIn('salario bruto publicado', (ROOT/'municipios/metodologia.html').read_text(encoding='utf-8').lower())
        self.assertNotIn('había Sin dato',self.text)
        self.assertIn('no significan que el monto sea cero',self.text)

    def test_footer_and_missing_data_are_explicit(self):
        for i,p in enumerate(self.pdf.pages,1):
            text=p.extract_text()
            self.assertIn('Federico Pellegrini',text)
            self.assertIn(f'Página {i}',text)
            self.assertGreater(len(text),500)
            self.assertIn('Fuentes:',text)
            self.assertIn('tablero.federicopellegrini.com.ar/municipios/',text)
            links=[a.get_object().get('/A',{}).get('/URI','') for a in p.get('/Annots',[])]
            self.assertTrue(any('?municipio=06329' in link for link in links))
            self.assertTrue(any(link.startswith('https://') and 'tablero.federico' not in link for link in links))
        self.assertIn('Sin dato',self.text)
        self.assertIn('Los sectores reservados',self.text)
        self.assertIn('No encontramos una serie municipal comparable',' '.join(self.text.split()))

    def test_execution_and_different_periods_do_not_become_comparable_deficits(self):
        tigre='\n'.join(p.extract_text() for p in PdfReader(OUTPUT/'informe-06805.pdf').pages)
        self.assertIn('Ejecución presupuestaria',tigre)
        self.assertIn('no se usan como un déficit o superávit en el ranking',tigre)
        bragado='\n'.join(p.extract_text() for p in PdfReader(OUTPUT/'informe-06112.pdf').pages)
        self.assertIn('30/06/2026',bragado)
        self.assertIn('31/08/2026',bragado)
        self.assertIn('no integra el ranking',bragado)
        missing=next(m for m in self.data['municipalities'] if not any(m.get(k) for k in ['fiscal','fiscalOther','fiscalExecution']))
        missing_text='\n'.join(p.extract_text() for p in PdfReader(OUTPUT/f'informe-{missing["id"]}.pdf').pages)
        self.assertIn('Las cuentas que faltan verificar',missing_text)

    def test_report_regeneration_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            generated=build(Path(tmp),'06329')['reports'][0]
            stored=next(r for r in self.manifest['reports'] if r['id']=='06329')
            self.assertEqual(generated,stored)


if __name__=='__main__':unittest.main()

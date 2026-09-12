import hashlib
import json
import tempfile
import subprocess
import re
import unittest
from pathlib import Path
from pypdf import PdfReader
from scripts_export_municipal_reports import ROOT, OUTPUT, fingerprint, build, money, number, month
from scripts_municipal_editorial import TOPICS,latest_fiscal


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
                self.assertEqual(r['sections'],[m['id'] for m in r['modules']])
                self.assertEqual([p for m in r['modules'] for p in m['pages']],list(range(r['pages'])))
                self.assertEqual([p for m in r['modules'] if m['default'] for p in m['pages']],[0,1,2])
                self.assertEqual(r['modules'][0]['id'],'lectura')
                brief=PdfReader(OUTPUT/r['brief']['file'])
                self.assertEqual(len(brief.pages),3)
                self.assertEqual(hashlib.sha256((OUTPUT/r['brief']['file']).read_bytes()).hexdigest(),r['brief']['sha256'])
                for i,page in enumerate(brief.pages):
                    self.assertEqual(page.extract_text(),pdf.pages[i].extract_text())
                    self.assertEqual(re.findall(r'Página \d+',page.extract_text()),[f'Página {i+1}'])
                self.assertLessEqual(r['pages'],10)
                self.assertEqual(r['crimeYears'],[2024,2025])

    def test_general_las_heras_fiscal_money_and_price_bases(self):
        fiscal=self.m['fiscal']
        self.assertAlmostEqual(fiscal['ingresos_totales']-fiscal['gastos_totales'],1587567967.29,places=2)
        for key in ['ingresos_corrientes','ingresos_capital','ingresos_totales','gastos_corrientes','gastos_capital','gastos_totales','resultado_financiero','personal_devengado']:
            self.assertIn(money(fiscal[key],2),self.text)
        self.assertIn('$5.474,5',self.text)  # Nominal transfers, Jan-Jul 2026.
        self.assertIn('$5.842,9',self.text)  # Same flows in July 2026 purchasing power.
        self.assertIn('pesos corrientes, sin ajuste por inflación',self.text)
        self.assertIn('precios constantes de 2004',self.text)

    def test_editorial_report_contains_verified_salary_and_context_not_removed_sections(self):
        for forbidden in ['Publicación de información fiscal','Los 27 indicadores en comparación','Escenarios de coparticipación','Anexo / transferencias','Anexo / empleo']:
            self.assertNotIn(forbidden,self.text)
        for value in ['$1.577.097','$2.117.275','5.038','37','22','58','28,0%']:
            self.assertIn(value,self.text)
        for definition in ['Real significa ajustado por inflación','necesidades básicas insatisfechas','SIPA','aguinaldo','no es el sueldo de bolsillo','Tres decisiones que conviene ordenar']:
            self.assertIn(definition,self.text)
        self.assertIn('salario bruto publicado', (ROOT/'municipios/metodologia.html').read_text(encoding='utf-8').lower())
        self.assertNotIn('había Sin dato',self.text)
        self.assertIn('no se completan con cero',self.text)
        brief=' '.join(p.extract_text() for p in PdfReader(OUTPUT/'informe-06329-breve.pdf').pages)
        self.assertLess(len(brief.split()),1300)
        for omitted in ['Historia de las cuentas','Deudas de las personas','Población y hogares','Caja y deuda municipal']:
            self.assertNotIn(omitted,brief)

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
        self.assertIn('no se verificaron domicilios individuales',' '.join(self.text.lower().split()))
        for value in ['13.565','4.035','29,75%','22,81%','$52.962,48','$12.083,31']:
            self.assertIn(value,self.text)

    def test_execution_and_different_periods_do_not_become_comparable_deficits(self):
        tigre='\n'.join(p.extract_text() for p in PdfReader(OUTPUT/'informe-06805.pdf').pages)
        self.assertIn('Detalle de presupuesto y pagos',tigre)
        self.assertIn('Menos cancelación de pasivos anteriores',tigre)
        self.assertIn('$12.863,85',tigre)
        self.assertIn('$33.832,57',tigre)
        self.assertIn('31/12/2025',tigre)
        bragado='\n'.join(p.extract_text() for p in PdfReader(OUTPUT/'informe-06112.pdf').pages)
        self.assertIn('31/08/2026',bragado)
        self.assertIn('no integra el ranking',bragado)
        missing=next(m for m in self.data['municipalities'] if not any(m.get(k) for k in ['fiscal','fiscalOther','fiscalExecution']))
        missing_text='\n'.join(p.extract_text() for p in PdfReader(OUTPUT/f'informe-{missing["id"]}.pdf').pages)
        self.assertIn('Faltan ingresos y gastos comparables',missing_text)

    def test_brief_values_follow_the_latest_verified_cutoff_in_all_municipalities(self):
        for m in self.data['municipalities']:
            text=' '.join(page.extract_text() for page in PdfReader(OUTPUT/f'informe-{m["id"]}-breve.pdf').pages)
            f=latest_fiscal(m);b=m.get('annualBudget')
            with self.subTest(id=m['id']):
                if f:
                    self.assertIn(date_string(f['fin']),text)
                    for key in ['ingresos_totales','gastos_totales','resultado_financiero']:
                        self.assertIn(money(f[key],2),text)
                else:self.assertIn('cuenta fiscal está pendiente',text)
                if b:
                    self.assertIn(money(b['amount']),text)
                    self.assertIn(str(b['year']),text)
                    self.assertIn(date_string(b['asOf']),text)
                    if b['historical']:self.assertIn('dato histórico',text)
                else:self.assertIn('Presupuesto anual pendiente',text)
                self.assertIn(money(m['community']['wage']['annual']['2025']['real'],0,False),text)
                self.assertIn('millones de pesos de julio 2026',' '.join(text.split()))

    def test_selected_pdf_pages_keep_sources_and_remove_the_old_page_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            script="""
const fs=require('node:fs');
(async()=>{
const {composeMunicipalPdf}=await import('./municipios/report.mjs');
const lib=require('./municipios/vendor/pdf-lib.min.js');
const manifest=JSON.parse(fs.readFileSync('./municipios/reports/manifest.json'));
for(const [id,topics] of [['06329',['lectura','poblacion','caja']],['06805',['lectura','economia','bancos']]]){
 const e=manifest.reports.find(r=>r.id===id),bytes=fs.readFileSync('./municipios/reports/'+e.file);
 const result=await composeMunicipalPdf(bytes,e,topics,lib);
 fs.writeFileSync(process.argv[1]+'/'+id+'.pdf',result);
}
})().catch(e=>{console.error(e);process.exit(1)});
"""
            subprocess.run(['node','-e',script,tmp],cwd=ROOT,check=True,capture_output=True)
            for id in ['06329','06805']:
                pdf=PdfReader(Path(tmp)/(id+'.pdf'))
                self.assertEqual(len(pdf.pages),3)
                self.assertEqual(pdf.metadata.author,'Federico Pellegrini')
                for i,page in enumerate(pdf.pages,1):
                    text=page.extract_text()
                    self.assertEqual(re.findall(r'Página \d+',text),[f'Página {i}'])
                    self.assertIn('Fuentes:',text)
                    self.assertIn('Federico Pellegrini',text)
                    self.assertTrue(any(a.get_object().get('/A',{}).get('/URI','').startswith('https://') for a in page.get('/Annots',[])))

    def test_report_regeneration_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            generated=build(Path(tmp),'06329')['reports'][0]
            stored=next(r for r in self.manifest['reports'] if r['id']=='06329')
            self.assertEqual(generated,stored)


def date_string(value):return '/'.join(reversed(value.split('-')))

if __name__=='__main__':unittest.main()

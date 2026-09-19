import json
import unittest
from pathlib import Path
import openpyxl
from scripts_municipal_public_debt import apply_public_debt
from scripts_update_cash_august import ROWS

ROOT=Path(__file__).resolve().parents[1]

class SeptemberDataUpdate(unittest.TestCase):
    def test_cash_matches_august_original_and_preserves_missing_comparisons(self):
        raw=ROOT/'nacion/data/gestion'
        sheet=openpyxl.load_workbook(ROOT/'nacion/data/management-sources/imig-agosto2026.xlsx',data_only=True)['Agosto']
        comparison=json.loads((raw/'resultado_fiscal_comparacion.json').read_text(encoding='utf8'))
        for record in comparison:
            row=ROWS[record['indicador']]
            for year,col in [(2026,12),(2025,13)]:
                self.assertAlmostEqual(record[f'enero_agosto_{year}'],sheet.cell(row,col).value,places=4)
            if record['indicador'] in ['transferencias_corrientes_provincias','otros_gastos_corrientes']:
                self.assertIsNone(record['enero_agosto_real_2025'])
        monthly=json.loads((raw/'resultado_fiscal_caja_mensual.json').read_text(encoding='utf8'))
        result=next(r for r in monthly if r['periodo']=='2026-08' and r['indicador']=='resultado_financiero')
        self.assertAlmostEqual(result['nominal_millones'],635528.6,places=4)
        self.assertAlmostEqual(result['nominal_millones'],result['real_agosto2026'],places=4)

    def test_municipal_stocks_keep_leasing_separate_and_future_profile_partial(self):
        municipalities={'06042':{},'06693':{}}
        apply_public_debt(municipalities,ROOT/'municipios/data/public_debt_verified.json')
        roque=municipalities['06693']['publicDebt']
        self.assertAlmostEqual(roque['consolidated']+roque['floating'],473299043.79,places=2)
        self.assertEqual(roque['leasing'],322363236.31)
        self.assertIsNone(roque['schedule'][-1]['leasing'])
        for item in municipalities.values():
            debt=item['publicDebt']
            self.assertEqual(debt['scheduleStatus'],'partial_published')
            self.assertNotIn(2026,[r['year'] for r in debt['schedule']])

if __name__=='__main__':unittest.main()

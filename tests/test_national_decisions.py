import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scripts_build_national_decisions as subject


class NationalDecisionsTest(unittest.TestCase):
    def test_published_output_matches_archived_official_inputs(self):
        self.assertEqual(subject.build(), subject.load(subject.OUTPUT))

    def test_caif_separates_operating_result_and_financial_operations(self):
        rows={r['id']:r for r in subject.parse_caif(subject.DATA/'decision-sources/caif-2027.pdf')}
        self.assertEqual(len(rows),40)
        expected={'VI':202348174,'VII':202101433,'XI':246741,'XII':325784467,
                  'XII.2':324050562,'XIII':326031208,'XIII.2':306864929}
        for key,value in expected.items():self.assertEqual(rows[key]['project'],value)
        for year in ['closing','project']:
            self.assertLessEqual(abs(rows['XI'][year]+rows['XII'][year]-rows['XIII'][year]),1)
            self.assertEqual(rows['XII.3'][year],rows['XIII.3'][year])

    def test_policy_links_retain_periods_units_partial_information_and_missing_values(self):
        policies=subject.build()['policies']
        self.assertEqual([len(p['physical']) for p in policies],[14,13])
        for p in policies:
            self.assertEqual(p['execution']['corte'],'2026-09-15')
            self.assertTrue(all(m['trimestre']==2 for m in p['physical']))
            self.assertAlmostEqual(p['program']['accrued'],p['execution']['credito_devengado'],places=2)
            self.assertTrue(all(m['servicio_id']==p['link']['servicio_id'] and m['programa_id']==p['link']['programa_id'] for m in p['physical']))
        self.assertTrue(any(m['ejecutado_acumulado_trim2'] is None for m in policies[1]['physical']))
        self.assertTrue(any('parciales' in c['causa_desvio_comentario'] for m in policies[0]['physical'] for c in m['causas']))

    def test_wrong_or_ambiguous_correspondence_is_rejected(self):
        specs=copy.deepcopy(subject.POLICIES)
        item=list(specs[0]);item[-1]=(80,310,99);specs[0]=tuple(item)
        with patch.object(subject,'POLICIES',specs), self.assertRaises(AssertionError):subject.build()


if __name__=='__main__':unittest.main()

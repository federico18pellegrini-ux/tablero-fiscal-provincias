import unittest

from scripts_build_nacion_reclamos import aggregate_province_claims


class ReclamosPipelineTests(unittest.TestCase):
    def test_deduplicate_by_expediente(self):
        claims = [
            {
                'provincia': 'Buenos Aires',
                'expediente_o_causa': 'EXP-1',
                'tipo_reclamo': 'Coparticipación',
                'estado_reclamo': 'judicializado',
                'fecha_corte_monto': '2026-01-15',
                'calidad_dato': 'proxy',
                'monto_actualizado_calculado': 100.0,
            },
            {
                'provincia': 'Buenos Aires',
                'expediente_o_causa': 'EXP-1',
                'tipo_reclamo': 'Coparticipación',
                'estado_reclamo': 'judicializado',
                'fecha_corte_monto': '2026-01-15',
                'calidad_dato': 'observado',
                'monto_actualizado_calculado': 120.0,
            },
        ]

        out = aggregate_province_claims(claims)

        self.assertEqual(out['cantidad_de_reclamos'], 1)
        self.assertEqual(out['deuda_total_reclamada'], 120.0)
        self.assertEqual(out['deuda_total_robusta'], 120.0)

    def test_marks_insufficient_coverage_when_missing_robust_data(self):
        claims = [
            {
                'provincia': 'Córdoba',
                'expediente_o_causa': 'EXP-2',
                'tipo_reclamo': 'Caja',
                'estado_reclamo': 'administrativo',
                'fecha_corte_monto': '2026-02-01',
                'calidad_dato': 'proxy',
                'monto_actualizado_calculado': 50.0,
            }
        ]

        out = aggregate_province_claims(claims)

        self.assertTrue(out['cobertura_insuficiente'])
        self.assertEqual(out['estado_cobertura'], 'cobertura_insuficiente')
        self.assertEqual(out['porcentaje_cubierto_con_dato_robusto'], 0.0)


if __name__ == '__main__':
    unittest.main()

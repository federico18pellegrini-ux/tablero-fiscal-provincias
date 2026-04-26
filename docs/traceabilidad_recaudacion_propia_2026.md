# Trazabilidad de recaudación propia 2026 (TOP mensual)

Fecha de auditoría: 2026-04-26.

## Resultado Buenos Aires

- Valor publicado y reconstruido para `2026-01`: **$1.314.352,33 M**.
- Reconstrucción: suma de componentes (`Iibb + Sellos + Inmobiliario + Automotores + Otros`) en `top_mensual_2026_normalizado.csv`, con fuente declarada `top_mensual_20262.xlsx`.
- El valor **$1.391.690 M** no surge de los archivos normalizados vigentes del repositorio.
- Verificación de consistencia del ratio: `IIBB / recaudación propia = 1.086.193,53 / 1.314.352,33 = 82,6%` (redondeo a 1 decimal).
- Los dos KPIs del informe para Buenos Aires que usan este total quedan en **AR$ 1.314.352 M · ene 2026**:
  - `Indicadores clave → Recaudación propia 2026`
  - `Dinámica fiscal 2026 → Recaudación propia 2026 acum. ene`

## Verificación nacional (24 jurisdicciones)

Se auditó la trazabilidad de todas las filas `metric=own_revenue` en `dashboard_real_dynamics_inputs.csv` contra la reconstrucción directa desde `top_mensual_2026_normalizado.csv`.

Comando:

```bash
python scripts_validate_top_traceability.py
```

Salida esperada:

- `Diferencias: 0`
- `Buenos Aires 2026-01 IIBB/total: ... = 82,6%`
- Reporte detallado: `outputs/top_2026_traceability_report.csv`

## Criterio

- `status=ok`: valor publicado coincide exactamente con la suma de impuestos del TOP mensual para provincia/período.
- `status=mismatch`: valor publicado no reconstruible desde archivos cargados y requiere corrección o nota de fuente alternativa explícita.

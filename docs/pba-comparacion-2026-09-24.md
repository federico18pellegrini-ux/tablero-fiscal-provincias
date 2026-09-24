# Comparación de recursos y gastos de Buenos Aires

Revisión: 24/09/2026. Alcance: PBA, recaudación 2025–2026 y ejecución del primer semestre de 2026. No es una actualización integral de las 24 jurisdicciones.

- Se recuperaron 12 meses oficiales de recaudación 2025, con cinco componentes y total: 72 observaciones. Original y hash en `data/pba_sources` y `data/pba_comparison.json`.
- La planilla provincial 2026 sigue informando enero–julio. Sus 42 observaciones coinciden con la base utilizada por el tablero, con tolerancia de $0,02 millones. Los meses siguientes contienen celdas vacías y fórmulas en cero: no se importan.
- El ajuste de recaudación aplica el IPC a cada mes antes de sumar ambos años. No se promedian porcentajes mensuales. Se mantiene la separación con los ingresos APNF, que tienen otra cobertura.
- Se completó la composición del gasto APNF con bienes y servicios, otras transferencias corrientes y otras pérdidas, según página 13 del documento oficial. Otras pérdidas 2026: $2 millones, no $1 millón como en el informe de Daletto. La suma de componentes admite hasta $3 millones de redondeo.
- La comparación de gasto semestral divide la variación nominal por la relación entre IPC promedio de ambos semestres. No equivale a deflactar el gasto mes a mes, que requiere otra apertura.
- La planilla INDEC `sh_ipc_09_26.xls`, descargada nuevamente, llega a agosto 2026. No se agrega IPC proyectado. El portal de deuda provincial mantiene junio 2026 como último informe.
- Las descargas directas de TOP/RON nacionales devolvieron HTTP 403 durante esta revisión. Se conservaron los datos nacionales existentes y su corte de agosto; no se declara una nueva conciliación de esa planilla.
- El PDF bonaerense mantiene tres páginas y agrega las variaciones reales principales. El ranking federal conserva marzo y no se reemplaza por el semestre bonaerense.

Reproducción: `python scripts_build_pba_comparison.py`; luego `python scripts_export_management_reports.py`. Pruebas: `tests/test_pba_comparison.py`.

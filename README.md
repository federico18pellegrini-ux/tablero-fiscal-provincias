# tablero-fiscal-provincias
Tablero dinámico fiscal de provincias.

## Estado para cierre interno v1

### Bloques sólidos
- **Base comparativa estructural (1816)**: ranking fiscal, resultado financiero/primario, autonomía, rigidez, gasto de capital y perfil de deuda con corte metodológico homogéneo en 3T 2025.
- **Series históricas normalizadas**: RON anual 2003–2025 y recaudación/transferencias con pipeline de lectura desde CSV/JSON embebidos.
- **Presupuesto PBA 2026**: lectura de recursos, erogaciones y necesidad de financiamiento (Ley 15.557).

### Bloques en construcción
- **Dinámica real 2026**: lectura preliminar con cobertura parcial por provincia/mes.
- **Matriz de reclamos Nación → provincia**: cobertura parcial y profundización metodológica en curso.
- **Escenarios 90/180 y atribución de deterioro**: operativos, pero aún en fase de calibración para cierre analítico final.

### Fuentes nuevas integradas (PBA 2025–2026)
- `pba_top_monthly.csv` (recaudación mensual PBA, integración prioritaria 2025–2026).
- `pba_ron_monthly.csv` y `pba_ron_daily.csv` (transferencias nacionales mensuales/diarias).
- `pba_budget_execution_quarterly.csv` (ejecución trimestral PBA).
- `national_debt_monthly.csv` (contexto de deuda nacional para lectura comparada).
- `municipios_pba_annual.csv` (contexto municipal agregado para PBA).

## Nombre de versión propuesto
**`v1-interna · Línea de base consolidada`**

## Changelog corto de esta iteración
- Se consolidó la redacción de estado del tablero para cierre interno sin cambios estructurales.
- Se depuró etiquetado textual/metodológico en `index.html` para evitar superposición de mensajes.
- Se documentó en este README el estado de madurez por bloque y las fuentes PBA 2025–2026 integradas.

## Capa de reclamos Nación → provincias
- Tabla maestra: `data/reclamos_nacion/reclamos_nacion_provincias_maestra.csv`
- Catálogo de tipos: `data/reclamos_nacion/catalogo_tipos_reclamo.csv`
- Esquema de datos (JSON): `data/reclamos_nacion/esquema_datos_reclamos_nacion.json`
- README metodológico corto: `data/reclamos_nacion/README_metodologico.md`
- Validador de filas: `python scripts_validate_reclamos_nacion.py`
- Pipeline: `python scripts_build_nacion_reclamos.py`
- Salidas:
  - `outputs/reclamos_nacion_agregado_provincial.csv`
  - `dashboard_reclamos_nacion_provincias.json`
  - `outputs/reclamos_nacion_resumen_ba_resto.json`
- Metodología: `docs/reclamos_nacion_metodologia.md`

# tablero-fiscal-provincias
Tablero dinámico fiscal de provincias

## Capa de reclamos Nación → provincias
- Tabla maestra: `data/reclamos_nacion/reclamos_nacion_provincias_maestra.csv`
- Catálogo de tipos: `data/reclamos_nacion/catalogo_tipos_reclamo.csv`
- Pipeline: `python scripts_build_nacion_reclamos.py`
- Salidas:
  - `outputs/reclamos_nacion_agregado_provincial.csv`
  - `dashboard_reclamos_nacion_provincias.json`
  - `outputs/reclamos_nacion_resumen_ba_resto.json`
- Metodología: `docs/reclamos_nacion_metodologia.md`

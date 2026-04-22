# README metodológico corto · Reclamos Nación → provincias

## Objetivo
Estandarizar una capa de datos para estimar deuda reclamada por provincias al Estado nacional, con trazabilidad por expediente y tipo de reclamo.

## Tablas fuente
1. `reclamos_nacion_provincias_maestra.csv`: una fila por reclamo/expediente.
2. `catalogo_tipos_reclamo.csv`: catálogo de categorías habilitadas y su fórmula base.

## Criterio de cómputo
- `deuda_total_reclamada`: suma de `monto_actualizado` (o monto actualizado desde nominal cuando aplica).
- `deuda_total_robusta`: solo filas con `calidad_dato` en `observado` o `estimado_robusto`.
- Regla anti-doble-conteo: no duplicar expedientes que representen el mismo hecho generador.

## Ejemplos mínimos cargados
Se dejan tres filas de ejemplo para Buenos Aires:
- ANSES / cajas no transferidas (`observado`)
- FONID (`estimado_robusto`)
- Transporte interior (`proxy`)

## Validación de filas
- Función: `validate_master_row` en `scripts_build_nacion_reclamos.py`.
- Runner CLI: `python scripts_validate_reclamos_nacion.py`.
- Reglas: campos obligatorios, enums válidos, fechas ISO, montos no negativos y consistencia entre calidad y disponibilidad de monto.

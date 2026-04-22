# Metodología · Matriz de reclamos Nación → provincias

## Qué entra en `deuda_total_reclamada`
- Suma de `monto_actualizado` por provincia cuando existe dato trazable.
- Si no existe `monto_actualizado`, el pipeline intenta actualizar `monto_nominal` con `indexador` y `tasa_interes`.
- Incluye reclamos con calidad `observado`, `estimado_robusto`, `proxy` y `no_disponible` (estos dos últimos solo cuando tengan monto cargado).

## Qué entra en `deuda_total_robusta`
- Solo reclamos con `calidad_dato = observado` o `estimado_robusto`.
- Se excluyen explícitamente `proxy` y `no_disponible`.

## Cómo se actualizan montos
- `indexador = ipc_nacional`: se aplica factor de `deflactor_mensual.csv` entre `fecha_corte_monto` y último mes disponible.
- `indexador = sin_actualizacion`: mantiene monto nominal.
- `tasa_interes` (si existe) se aplica como factor adicional multiplicativo simple.

## Calidad de dato
- `observado`: monto en fuente primaria y expediente/convenio identificable.
- `estimado_robusto`: monto calculado con regla homogénea y base auditada.
- `proxy`: aproximación parcial con cobertura o homogeneidad incompleta.
- `no_disponible`: existe reclamo, pero no hay monto válido al corte.

## Reclamos que requieren carga manual
- Obras con certificaciones no digitalizadas de forma homogénea.
- Programas discontinuados sin tablero nacional abierto por provincia.
- Reclamos judiciales sin sentencia o sin cuantificación pública homogénea.

## Regla anti doble conteo
No sumar dos filas si comparten mismo hecho generador, expediente y período base.
Primero se consolida por `expediente_o_causa` y luego se agrega por tipo/provincia.

## Integración con tablero fiscal provincial (sin rediseño)
- Dataset agregado por provincia: `dashboard_reclamos_nacion_provincias.json` (objeto `provinces`).
- Selectores/hook esperados por front:
  - `deuda_total_reclamada`
  - `deuda_total_robusta`
- Espacio futuro reservado para bloque visual:
  - `deuda_nacion_con_provincia.status`
  - `deuda_nacion_con_provincia.ready_for_render`
  - `deuda_nacion_con_provincia.component_key`

### Ejemplo de lectura (Buenos Aires)
- `deuda_total_reclamada`: total de montos actualizados trazables al corte.
- `deuda_total_robusta`: subcomponente robusto (observado + estimado_robusto).
- Referencia lista para UI: `example_buenos_aires` dentro del JSON de salida.

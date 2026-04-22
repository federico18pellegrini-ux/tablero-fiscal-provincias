# Nota metodológica · Caso testigo Buenos Aires (matriz Nación → provincias)

## Alcance
Este caso testigo organiza los principales reclamos de la Provincia de Buenos Aires frente al Estado nacional usando exclusivamente evidencia ya cargada en el proyecto (tabla maestra y salidas del pipeline).

## Criterio de construcción de filas
Cada fila del archivo `reclamos_nacion_buenos_aires_caso_testigo.csv` incluye:
- provincia
- tipo_reclamo
- organismo_nacional
- expediente o referencia
- monto
- fecha de corte
- calidad_dato
- observaciones

Reglas aplicadas:
1. Si existe `monto_actualizado`, se prioriza ese valor.
2. Si no existe `monto_actualizado`, se usa `monto_nominal` solamente cuando está cargado.
3. Si no hay monto validado, el campo `monto` queda vacío (no se imputa).
4. Cuando la cobertura es parcial o no homogénea, se conserva `calidad_dato = proxy`.

## Límites de evidencia (explícitos)
- Hay reclamos con existencia documental, pero sin cuantificación pública homogénea al corte.
- En esos casos, la serie no asigna monto y no fuerza estimaciones.
- `proxy` se usa para señalar precisamente ese límite: hay indicios y trazas administrativas, pero no una base cerrada y auditada para cuantificar sin riesgo de sesgo o doble conteo.
- `no_disponible` se conserva cuando el reclamo está identificado pero sin monto computable con la evidencia actual.

## Efecto sobre agregados de Buenos Aires
- `deuda_total_reclamada` suma únicamente filas con monto.
- `deuda_total_robusta` suma solo filas con `calidad_dato` observado o estimado_robusto.
- Por diseño metodológico, estos agregados pueden subestimar el universo total reclamado cuando persisten filas `proxy` o `no_disponible` sin monto.

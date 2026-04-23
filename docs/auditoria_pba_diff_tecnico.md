# B. Diff técnico (archivo por archivo)

## `index.html`
- Se amplió el diccionario de faltantes con:
  - `mes_no_cerrado_fuente`
  - `faltante_especifico_jurisdiccion`
- Se incorporó nueva etiqueta de calidad:
  - `[Parcial]`.
- Se endureció saneamiento de TOP mensual 2026:
  - ceros de marzo 2026 (si aparecieran en fuente) pasan a faltante por mes no cerrado,
  - ceros de PBA febrero 2026 (si aparecieran en fuente) pasan a faltante específico.
- Se corrigió bloque RON PBA en dinámica real:
  - `enero-marzo cerrados` (xlsx),
  - `abril parcial` (daily con fecha de corte).
- Se corrigió bloque de liquidez:
  - mensaje explícito de “liquidez parcial observada”,
  - eliminación de lectura binaria de cobertura SAC.
- Se corrigió bloque de reclamos Nación:
  - separación textual explícita entre matriz auditada parcial y universo documentado.
- Se corrigió comparabilidad:
  - nota de universo estructural vs universo RON.
- Se amplió leyenda de evidencias para incluir `[Parcial]`.

## Nuevos documentos
- `docs/auditoria_pba_matriz_errores.md`
  - Matriz de errores, tipología y corrección aplicada.
- `docs/auditoria_pba_decisiones_metodologicas.md`
  - Definiciones metodológicas finales de rigidez, liquidez, comparabilidad y ceros/faltantes.
- `docs/auditoria_pba_tablero_final.md`
  - Checklist funcional del tablero corregido.

# A. Matriz de errores — Auditoría metodológica PBA

| Campo | Dónde está | Problema detectado | Tipo | Corrección aplicada |
|---|---|---|---|---|
| TOP mensual 2026 (ceros sospechosos) | `top_mensual_2026_normalizado.csv` + lógica de saneamiento en `index.html` | Ceros en TOP 2026 confundibles con dato económico; además faltan filas de PBA febrero que en origen aparecen en cero no auditado | faltante / fórmula | Se formalizó regla de saneamiento: cero en marzo 2026 se trata como `mes_no_cerrado_fuente`; cero PBA febrero 2026 se trata como `faltante_especifico_jurisdiccion` (se renderiza como faltante, no como 0). |
| Etiquetado RON 2026 | `renderRealDynamics` en `index.html` | RON reciente se mostraba como bloque homogéneo sin separar cierre mensual vs parcial diario | etiqueta temporal | Se separó explícitamente: `RON PBA enero-marzo 2026 cerrados` + `RON PBA abril 2026 parcial` (con fecha de corte). |
| Liquidez/caja/aguinaldo | `renderLiquidity` en `index.html` | Riesgo de lectura binaria con base incompleta | etiqueta / inferencia | Se reemplazó redacción por “liquidez parcial observada”; se prohíbe conclusión de cobertura SAC y se deja semáforo metodológico gris/naranja. |
| Rigidez salarial 50,5% | `dashboard_cross_section_1816.json` + visualización `index.html` | Valor sensible sin etiqueta de corte metodológico explícita (riesgo de leerse como “actual 2026”) | fuente / etiqueta | Se mantuvo el valor como dato estructural 3T2025 y se reforzó el alcance por módulo en notas de universo/temporalidad. |
| Soporte Nación (deuda/reclamos) | `renderNationDebt` en `index.html` | Podía interpretarse subtotal parcial como deuda total Nación→PBA | etiqueta / fuente | Se separaron dos capas explícitas: (A) matriz auditada cargada (parcial) y (B) universo documentado de reclamos/litigios. |
| Comparabilidad interprovincial | `availNote` y `renderFederalFairness` en `index.html` | Leyenda global única (“21 comparables”) aplicada a módulos con universos distintos | etiqueta metodológica | Se diferenció por módulo: estructural (comparables 3T2025) vs RON anual (24 jurisdicciones con reglas propias de disponibilidad). |
| Catálogo de calidad del dato | `DATA_QUALITY_TAG` y tarjetas de evidencias en `index.html` | Faltaba categoría explícita `[Parcial]` | etiqueta | Se agregó `[Parcial]` y uso en tarjeta RON abril parcial. |

## Controles ejecutados
1. Detección de ceros sospechosos en TOP 2026: detectados 8 ceros en CABA (enero/febrero) y ausencia de filas PBA febrero en normalizado (trazado como faltante específico cuando corresponda en fuente).  
2. Revisión de fórmulas dependientes de TOP 2026: saneamiento previo (`sanitizeTopMensualRows`) antes de acumulados/gráficos y notas metodológicas de cobertura.  
3. Revisión de fórmulas RON 2026: separación de cierre ene-mar vs abril parcial diario en bloque PBA.  
4. Origen de 50,5%: proviene de `gasto_salarios_gasto_primario_ex_ss_pct` en corte estructural 3T2025; se evita venderlo como métrica de caja 2026.  
5. Liquidez/caja: se dejó explícito “parcial observada”; sin veredicto binario de SAC.  
6. Soporte Nación: separación explícita matriz parcial vs universo documentado.  
7. Universo comparativo por módulo: explicitado en notas de disponibilidad y pie metodológico federal.

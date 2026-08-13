# Auditoría integral del tablero fiscal provincial

Fecha: 13 de agosto de 2026. Revisión base: `main` en `7648501`.

## Juicio ejecutivo

El tablero tiene una base valiosa: cobertura interprovincial, trazabilidad explícita, separación entre datos auditados y parciales, y una interfaz publicada que funciona sin errores visibles. Sin embargo, todavía no debe presentarse como un sistema completo de alerta fiscal 90/180 días. La principal restricción no es visual: faltan series homogéneas de gasto, caja, aguinaldo y vencimientos, y algunos pipelines transformaban esos faltantes en señales aparentes.

Juicio final: **se estanca hasta corregir la metodología y completar datos críticos**. Con las correcciones de esta iteración, deja de publicar varias inferencias no respaldadas, pero aún no alcanza la cobertura necesaria para el objetivo completo.

## Hallazgos priorizados

| Prioridad | Hallazgo | Impacto | Estado local |
|---|---|---|---|
| P0 | El generador de equidad federal tomaba RON sin Compensación Consenso Fiscal, aunque la interfaz declaraba usar `Total (1)+(2)`. | Distorsionaba RON per cápita, promedios y brechas. | Corregido y cubierto por prueba. |
| P0 | `ahorro_corriente_ratio = resultado_financiero_ratio`. | Confundía dos conceptos contables distintos. | Corregido: queda `N/D` sin fuente corriente. |
| P0 | El riesgo de aguinaldo se infería desde el resultado financiero mediante un proxy de meses de cobertura. | Podía producir una alerta política falsa sin caja ni necesidad SAC. | Corregido: `sin_dato`. |
| P0 | El output versionado de atribución mostraba proxies 68/61/54 para PBA, pero su propio generador devuelve faltante por ausencia de inputs. | El repositorio no era reproducible y atribuía deterioro sin evidencia suficiente. | Regenerado: los tres efectos quedan faltantes. |
| P1 | El proxy de “aporte a la masa nacional” usaba participación en recaudación propia provincial 2026 con cobertura mensual desigual. | No mide aporte a la masa federal y podía inducir un “retorno por cada 100” inválido. | Retirado; queda parcial hasta contar con método homogéneo. |
| P1 | El modo “pesos constantes” no transformaba la recaudación propia PBA, aunque sí transformaba RON. | Comparaba magnitudes con distinto criterio dentro de la misma vista. | Corregido. |
| P1 | El mapa declaraba “Dinámica fiscal 2026: completo” aunque no existe base 2025 homogénea ni gasto mensual válido. | Sobreestimaba la madurez del tablero. | Corregido: queda parcial. |
| P1 | `generated_at` se mostraba como actualización de datos. | Ejecutar un script podía hacer parecer nuevos datos viejos. | Separado: la interfaz muestra `data_cutoff`. |
| P1 | El pipeline de reclamos usaba la fecha del día como corte, no la fecha máxima de las filas fuente. | Falsa apariencia de actualización. | Corregido y cubierto por prueba. |
| P1 | No había CI propia; GitHub sólo desplegaba Pages. | Un merge podía publicar errores de cálculo sin control. | Agregado workflow de validación. |
| P2 | `index.html` concentra más de 4.000 líneas y duplica datos embebidos/externos. | Alto riesgo de divergencia, estado residual y regresiones. | Pendiente de refactor modular. |
| P2 | En móvil la tabla estructural expandía el ancho de página; al cambiar a CABA persistía una nota de PBA. | Deterioro de usabilidad y trazabilidad. | Corregido localmente. |
| P2 | Librerías de exportación y gráficos se cargan desde CDN sin SRI y sin política de contenido. | Riesgo de cadena de suministro; moderado por ser sitio estático. | Pendiente. |

## Cobertura frente a indicadores obligatorios

| Indicador | Estado actual |
|---|---|
| Crecimiento real de ingresos totales | Parcial/histórico; no homogéneo mensual 2026. |
| Crecimiento real de recaudación propia | Faltante para PBA por ausencia de base comparable 2025. |
| Crecimiento real de coparticipación | Disponible en algunas ventanas, con cortes distintos. |
| Crecimiento real de TNA | No cerrado de forma homogénea. |
| Crecimiento real del gasto primario | Faltante; archivo mensual es scaffold sin valores. |
| Personal / ingresos | No disponible con esa definición; existe personal / gasto primario ex SS. |
| Ahorro corriente | Faltante; ya no se aproxima con resultado financiero. |
| Resultado primario / ingresos | Disponible estructural LTM 3T25. |
| Resultado financiero / ingresos | Disponible estructural LTM 3T25. |
| Deuda / ingresos | Disponible estructural 3T25. |
| Intereses / ingresos | Disponible para PBA estructural; cobertura desigual en pares. |
| Caja y cobertura de aguinaldo | Faltante. |
| Concentración en IIBB | Disponible estructural; 2026 PBA sólo enero. |
| Gasto de capital / gasto total | No exacto; existe capital / gasto primario ex SS. |

## Tres riesgos principales

1. **Riesgo de decisión falsa:** convertir faltantes en amarillo/medio o en proxies numéricos da una precisión que los datos no sostienen.
2. **Riesgo de mezcla temporal:** conviven LTM 3T25, anual 2025, enero 2026, enero-marzo cerrado y abril parcial.
3. **Riesgo de mantenimiento:** cálculo, narrativa, visualización y datos embebidos viven en un único HTML, mientras los generadores externos pueden producir resultados distintos.

## Tres decisiones sugeridas

1. Publicar una versión `v1.1 metodológicamente segura` con estas correcciones y sin semáforo de aguinaldo/atribución cuando falten datos.
2. Completar primero PBA con una tabla mensual 2025-2026 de recursos, gasto primario, personal, capital, caja y vencimientos; recién después calibrar 90/180 días.
3. Modularizar en una segunda etapa: datos JSON únicos, funciones fiscales probadas, componentes de interfaz separados y CI que regenere y compare salidas.

## Validación ejecutada

- Compilación de todos los scripts Python.
- Cinco pruebas automáticas, incluidas regresiones de RON, ahorro/aguinaldo y fecha de corte de reclamos.
- Validador TOP: 38 filas, 0 diferencias.
- Validador de reclamos: 31 filas sin errores.
- Prueba publicada/local en cuatro provincias, cambio nominal/real y ancho móvil.
- GitHub Pages estaba operativo; sus ejecuciones de despliegue estaban en verde, pero no había controles fiscales propios.

## Pendientes antes de publicar

- Revisión política de los textos de escenario cualitativo: hoy no se calculan desde caja ni vencimientos.
- Definir una fuente oficial y periódica para caja/FUCO, SAC y cronograma de deuda.
- Agregar pruebas de navegador para selector de provincias, cobertura, nominal/real y exportación PDF.
- Resolver o cerrar las propuestas abiertas #70 y #90, ambas en conflicto con `main` y parcialmente superadas por cambios posteriores.

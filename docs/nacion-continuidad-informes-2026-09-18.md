# Financiamiento de obras, escenarios e informes por tema

Segunda entrega del 18/09/2026, posterior a las fichas de inmunizaciones y universidades.

## Datos incorporados

La planilla 12 del proyecto 2027 se volvió a descargar de la ONP. Coincide con la huella del documento ya usado por el tablero. Se extraen las diez columnas de financiamiento para las 435 partidas, manteniendo subtotales internos, externos y total separados de sus componentes. Los totales oficiales se conservan; las diferencias por redondeo de la suma de filas quedan en `works.rounding_differences` de `decisions.json`.

La ficha RA-10 vincula una única apertura del proyecto 2027 con una única obra de la ejecución del primer trimestre 2026: jurisdicción 50, SAF 105, programa 20, subprograma 0, proyecto 22, obra 51. La correspondencia de 2027 se revisó por denominación, organismo y ubicación; esa planilla no publica códigos de obra. No se generaliza este cruce a otras obras.

Se volvió a descargar el informe oficial de inversión del primer trimestre. Su huella coincide con la registrada. En su página 7 publica el costo de referencia BAPIN de $232.217,6 millones; en la 8 informa el avance físico acumulado de 85,47%. Ambos valores se extraen del documento y se contrastan con los datos financieros y físicos de la apertura. El presupuesto 2027 es $39.690 millones, íntegramente Tesoro. El costo actualizado de terminación, cronograma, contratos y operación siguen ausentes: no se estiman con el avance físico ni restando montos de distinta antigüedad.

## Uso

- `#inicio`: tres asuntos elegidos editorialmente por caída real, magnitud del financiamiento y continuidad de obra. No es un ranking exhaustivo ni un diagnóstico automático de calidad de gestión.
- `#obras`: financiamiento de cada partida y filtros por presencia de recursos externos, Tesoro o financiación exclusivamente interna. Las fuentes mixtas conservan todos sus componentes.
- `#obra-ra10`: ficha integrada y descarga de una página.
- `#escenarios`: sensibilidad del poder de compra a inflación promedio anual; resultado financiero ante una caída de ingresos con gasto fijo; capital y otros pasivos no cubiertos por el porcentaje de financiamiento supuesto. Los tres cálculos son separados, con fórmulas y unidades visibles. No proyectan recaudación a partir del PIB, no modelan respuestas automáticas del gasto y no constituyen una proyección completa de caja ni de cierre 2026.

El escenario reproduce la comparación real del tablero con sus índices medios anuales. El selector de precios general se oculta allí porque los resultados fiscales están identificados en pesos corrientes y el escenario tiene sus propios supuestos. Valores vacíos o fuera de rango no producen resultados numéricos.

## Exportación y verificaciones

El informe general tiene 19 páginas: conserva las 15 anteriores e incorpora financiamiento, inmunizaciones, universidades y RA-10. El anexo opcional mantiene todas las partidas y llega a 65 páginas. Además se generan tres fichas de una página, en pesos corrientes y con cambios reales explícitos. La descarga se valida contra las huellas del presupuesto, gestión y decisiones para impedir PDF atrasados.

Analytics registra las dos nuevas secciones y las descargas breves. No recibe búsquedas, supuestos de escenarios ni datos escritos por el usuario.

Pruebas de datos: conciliación de las 435 partidas y columnas, fuente y antigüedad de costo RA-10, inexistencia de costo actualizado inferido, ecuaciones de sensibilidad, límites de entrada, filtros, correspondencia de PDF, navegación y privacidad. Revisión visual de las nuevas páginas en las seis combinaciones y de las tres fichas breves; las primeras 15 páginas conservan su texto original. Navegador en 320, 390, 768 y 1440 píxeles, con PDF, modo claro y oscuro y errores de datos controlados.

## Límites de esta entrega

Quedan para datos adicionales los costos actuales y contratos de las obras, las elasticidades por tipo de gasto e ingreso para una proyección macroeconómica y la conciliación del gasto/PIB. Se conserva el calendario de deuda con su fecha declarada. No se presenta ninguna de esas ampliaciones como ya resuelta.

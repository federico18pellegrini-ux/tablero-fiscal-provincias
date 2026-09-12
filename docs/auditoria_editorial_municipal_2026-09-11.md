# Auditoría editorial del informe y del tablero municipal

La exportación anterior mezclaba una lectura para tomar decisiones con el detalle de consulta. General Las Heras tenía 14 páginas y Tigre, 16. De los 135 informes, 100 tenían 10 páginas, 32 tenían 9 y uno tenía 11, además de esos dos distritos. La extensión no respondía a una elección del lector.

## Decisión de contenido

La versión recomendada tiene tres páginas para los 135 municipios:

1. Diagnóstico y tres decisiones explicadas, con indicadores, fechas y concentración sectorial propia del municipio.
2. Presupuesto anual, cuenta fiscal y transferencias, distinguiendo autorización, ejecución y fondos provinciales.
3. Empleo, salarios y actividad: puestos, sectores, remuneraciones brutas ajustadas por inflación y producto municipal.

El selector muestra todos los temas disponibles, sus páginas y la extensión final. Permite quitar cuentas o economía y agregar población y seguridad, deudas de las personas, ejecución, caja, historia y saldos bancarios. El diagnóstico queda incluido. Los módulos que requieren detalle municipal se ofrecen sólo cuando hay respaldo. El informe con todos los temas ocupa entre 5 y 9 páginas; Las Heras, 8, y Tigre, 9.

No se redujo la tipografía para comprimir el contenido: el cuerpo principal pasó de 10,1 a 10,5 puntos. Cada tema conserva sus fuentes, unidades, fechas, enlace al tablero y pie firmado por Federico Pellegrini. La selección vuelve a numerar las páginas; no conserva números de la versión extensa debajo de una cobertura visual.

## Repeticiones corregidas

| Problema | Cambio |
|---|---|
| Diagnóstico y prioridades repetían números y conclusiones en páginas separadas. | Se reúnen en la primera página; las prioridades explican para qué actuar. |
| El detalle de Tigre dejaba una conciliación en una página casi vacía. | Se integra al cuadro de ejecución, sin perder sus ajustes contables. |
| El presupuesto completo aparecía en Panorama y Recursos, y sus totales se repetían en ejecución. | Panorama conserva un resumen y acceso al detalle. Recursos concentra autorización y ejecución. |
| Saldos bancarios dispersos en Recursos y Empleo. | Un bloque bancario en Empleo; el comparador de inflación permite explorar sus valores. |
| Párrafos de salarios, deuda y prioridades volvían a narrar los números de los cuadros. | Se conserva la interpretación y se quita la repetición literal. |
| El comparador repetía seis tarjetas extensas simultáneamente. | Seis botones visibles para elegir una comparación, con descarga de esa variable. |

Se mantienen repeticiones que cumplen una función: los indicadores del Panorama anticipan el tema y cada cuadro de detalle sigue identificando su unidad y período. Los datos originales, las series y los rankings permanecen en el tablero.

## Validación

- Los 135 informes breves tienen exactamente tres páginas y coinciden con las primeras tres de su versión extensa.
- Las cifras de presupuesto, resultado fiscal y salarios se contrastaron con los datos y cortes que usa el tablero para los 135 municipios. Los faltantes siguen explícitos.
- Se validaron todas las combinaciones de módulos disponibles: orden, páginas, diagnóstico obligatorio y exclusión de temas sin respaldo.
- 111 pruebas de Python y 57 de JavaScript aprobadas; validadores de datos, cobertura, IPC y vigencia de informes aprobados.
- Revisión de límites de texto sobre 1.192 páginas generadas: sin texto fuera de página. Inspección visual de ambas versiones de Las Heras y Tigre y casos con distinta cobertura.
- Pruebas del flujo en anchos de 320, 390, 768 y 1.280 píxeles, incluyendo cuatro municipios y las vistas del tablero: sin desbordes horizontales. Controles nuevos de al menos 16 píxeles.
- Descarga real de documentos breves y seleccionados en Chrome. Pruebas de cambio de municipio durante la preparación, archivo desactualizado, reintento y catálogo temporalmente no disponible.

Esta revisión audita selección editorial, repeticiones, presentación y coherencia del PDF con la base vigente. No sustituye una nueva lectura de todos los documentos primarios de los 135 municipios. Los cortes de la base se mantienen: la fecha de esta mejora no convierte sus series en datos de septiembre de 2026.

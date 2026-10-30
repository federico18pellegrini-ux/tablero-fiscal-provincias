# Recaudación provincial: septiembre — 30/10/2026

## Incorporaciones verificadas

- Córdoba: DNAP `top_mensual_2026_20.xlsx`, columna K, cinco impuestos y total conciliados: 364.794,59102537 millones. Original preservado y SHA-256 en `data/provincial_recent_sources_review.json`.
- Tierra del Fuego: AREF `Salida-web-2026-Sep.pdf`, cuadro anual enlazado desde Estadística Tributaria. Septiembre: IIBB 17.339.720.763,21 pesos; Inmobiliario 353.205,06; Sellos 1.961.307.742,93; fondos sociales/previsionales 12.803.424.572,01. Total comparable 32.104.806.283,21 pesos. Fondos en Otros conserva la taxonomía DNAP: agosto concilia exactamente. No usar el total general 41.826.860.177,34 porque incluye regalías y otros ingresos. Automotores no imputado. El cuadro fue revisado visualmente.
- Santa Cruz: el nuevo portal ASIP publica septiembre con apertura en los datos públicos que alimentan la pantalla. Total general 39.612.046.014,81 pesos; se excluyen tasas varias 784.921.910,61 y pesca 3.025.042,46. Total comparable 38.824.099.061,74. Otros = rifas, igual alcance DNAP 2025.

## Corrección de agosto de Santa Cruz

Las revisiones DNAP 19 y 20 repiten en agosto los componentes de abril. ASIP publica agosto: IIBB 35.376.833.478,94; Sellos 4.101.247.573,33; Inmobiliario rural 839.260,01; rifas 14.850.000; pesca 0. Total comparable 39.493.770.312,28 pesos, excluidas tasas varias. Se reemplaza agosto; las filas anteriores quedan conservadas en `data/revenue-history-sources/santa-cruz-august-revision-2026-10-30.json`. No se revisaron exhaustivamente otros años.

Además, el contraste de enero-septiembre de 2025 con ASIP demuestra que DNAP 2025 incluye rifas, pero no pesca, en Otros. Para comparar el mismo perímetro, todos los meses de 2026 se reconstruyen desde ASIP con IIBB, Sellos, Inmobiliario rural y rifas; se excluyen pesca y tasas varias. Se preservan las filas originales de enero-agosto. No es una revisión de la recaudación total de ASIP sino una normalización explícita del conjunto comparable.

## Comparaciones y controles

Acumulado enero-septiembre real frente a 2025, deflactado mes a mes con el IPC del tablero: Córdoba -4,0%; Tierra del Fuego -6,3%; Santa Cruz -3,6%. Septiembre interanual real: -7,7%, -12,8% y -5,2%, respectivamente.

Se regeneraron los 24 informes desde los mismos insumos; cambiaron los tres PDF afectados. Se revisaron sus nueve páginas visualmente. Controles: 213 observaciones mensuales de recaudación conciliadas sin diferencias entre componentes y cálculos; 19 pruebas Python de fuentes, empalme e informes; ocho controles de cobertura/interfaz; 24 provincias a 390 píxeles sin errores de JavaScript ni desbordamiento horizontal. Estos controles no certifican todos los registros contra todos los documentos originales.

## Pendientes

- Buenos Aires: catálogo oficial continúa hasta agosto (`011999_082026`), aunque la actualización sea de octubre.
- La Pampa: Contaduría General sigue enlazando informes 01 a 08/2026.
- Santa Fe: API provincial mantiene agosto y acumulado a agosto.

La nueva planilla DNAP 20 tampoco contiene septiembre para estas tres jurisdicciones. Sus ceros de relleno no se incorporan como observaciones.

Cobertura resultante: 21 jurisdicciones hasta septiembre; tres hasta agosto. Las transferencias nacionales conservan su corte separado.

## Fuentes oficiales consultadas

- https://www.argentina.gob.ar/sites/default/files/top_mensual_2026_20.xlsx
- https://www.aref.gob.ar/estadistica-tributaria
- https://www.aref.gob.ar/wp-content/uploads/2026/10/Salida-web-2026-Sep.pdf
- https://www.asip.gob.ar/recaudacion/
- https://catalogo.datos.gba.gob.ar/api/3/action/package_show?id=recaudacion
- https://contaduriageneral.lapampa.gob.ar/ejecucion-presupuestaria/ano-2026/informe-de-recursos-mensual
- https://www.santafe.gob.ar/index.php/web/content/view/full/259564/%28subtema%29/217070

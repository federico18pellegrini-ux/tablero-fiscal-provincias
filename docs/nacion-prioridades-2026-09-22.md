# Prioridades y efectos del presupuesto

Nueva vista pública `nacion/#prioridades`, accesible desde el menú y Panorama.

## Comparaciones

- Cambios durante 2026: inicial contra vigente al 15/09, nominal; mide autorización, no gasto realizado.
- Gasto real 2026: devengado enero–agosto de 2025/2026, deflactado mes a mes con IPC observado de la base de gestión.
- Proyecto 2027: comparación a precios de agosto de 2026, con las tres bases 2026 visibles (inicial, vigente, cierre estimado). Usa los factores anuales del tablero; no IPC diciembre como promedio.
- Ranking completo de 29 funciones. Orden por diferencia absoluta o porcentual; participación y diferencia en puntos porcentuales. Subas y bajas reciben el mismo tratamiento.
- Las funciones de Presupuesto Abierto tienen códigos que recomienzan dentro de cada finalidad; los identificadores visuales de budget.json son consecutivos. La unión usa finalidad más nombre oficial exacto. Los tests exigen cobertura 29/29 y conciliación del denominador.
- Inteligencia incluye toda la función. El programa Información e Inteligencia de SIDE se identifica aparte, sin sumarlo a la función. No se inventa su cierre estimado.

## Prestaciones por mes

32 fichas de Indicadores Monetarios de la Seguridad Social, de diciembre de 2023 y marzo de 2024 a septiembre de 2026. Enero/febrero de 2024 no están en el archivo IMSS utilizado: permanecen ausentes, y el gráfico no une ese intervalo.

Mínima sin bono, bono, mínima con bono completo y AUH general al 100% del derecho. No es depósito neto, ni importe por hogar, ni promedio por persona, ni incorpora aguinaldo. Importes publicados redondeados al peso.

Se guarda cada extracción, URL oficial y SHA256 del PDF descargado, más cinco originales representativos. `scripts_build_national_benefits.py --check` valida extracciones, originales archivados y serie contra IPC observado. No se incorpora inflación proyectada a las prestaciones de septiembre.

Correcciones registradas en `benefits.json`:

- Marzo 2024: la cabecera redondea mal la mínima; se usa $134.445, redondeo de $134.445,30 en nota 3.
- Julio 2025: cabecera dice junio, pero archivo, nota 2 y resolución corresponden a julio. Se contrastó con ANSES, resolución 251/2025 y comunicado de julio: mínima $309.294,79 y AUH $111.141.
- Marzo 2026 y septiembre 2026: sumas inconsistentes de la tabla oficial. Se calcula mínima más bono ($439.601 y $498.633 respectivamente, redondeados).

La comparación real se calcula como `(monto final / monto inicial) / (IPC final / IPC inicial) - 1`. Septiembre queda nominal; último IPC observado agosto. Las variaciones menores a 0,05% se describen como poder de compra prácticamente sin cambios, coherente con la visualización a un decimal.

## Acceso y verificación

CSV con todas las funciones, unidades y períodos, CSV mensual de prestaciones y lectura copiable con fuente/corte. Los informes PDF existentes conservan su alcance; esta nueva vista se exporta por CSV/texto, no se presenta como incluida en esos PDF.

Nueva ruta admitida en Analytics, sin enviar selecciones personales o parámetros de búsqueda. Opt-out activado durante QA.

Validación local: 155 tests Python; 141 tests Node, 11 validadores de datos/reportes; navegador 320, 390, 768 y 1440 px, claro/oscuro, tres modos y bases, ranking completo, descargas, copia, navegación y discontinuidad de la serie. Sin errores de página ni desbordamiento horizontal. Se corrigió el menú en tablet al sumar la séptima opción.

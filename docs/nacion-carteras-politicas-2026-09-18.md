# Carteras y políticas integradas

## Resultado

La vista `#carteras` permite elegir entre las 16 jurisdicciones del registro 2026. Reúne proyecto 2027, cambios frente al inicial, vigente y cierre estimado, ejecución y pagos de 2026, programas principales, obras y disponibilidad de mediciones físicas. El enlace conserva la selección y cada cartera tiene un PDF de dos o tres páginas.

Se agregan cuatro fichas integradas, con un PDF de una página por política:

| Política | Jurisdicción / SAF / programa 2026 | Partida 2027 |
|---|---|---|
| Jubilaciones y pensiones de ANSES | 88 / 850 / 16 | p365 |
| Asistencia alimentaria | 88 / 311 / 26 | p337 |
| Acceso a medicamentos | 80 / 310 / 29 | p303 |
| Seguridad federal | 41 / 326 / 28 | p148 |

Las fichas de inmunizaciones, universidades y RA-10 permanecen disponibles. El catálogo contiene 12 versiones generales, siete fichas temáticas, 24 provinciales y 16 carteras: 59 PDF. Los informes generales conservan 19 páginas y 66 con anexo.

## Correspondencias y medidas

- Se verifica nombre y organismo del proyecto, y se concilian inicial, vigente y devengado 2026 con Presupuesto Abierto. La sigla PFA se resuelve explícitamente; no se usa coincidencia aproximada.
- La ejecución y las metas se relacionan por jurisdicción, SAF y programa. La clave de cada medición incluye subprograma, tipo, indicador y unidad. Esto distingue jubilaciones y pensiones de reparto/moratoria y pacientes/unidades de medicamentos.
- Los promedios semestrales de prestaciones previsionales no se presentan como altas o personas únicas. Las entregas acumuladas y los promedios de asistencia alimentaria no se suman. La actividad policial no se interpreta como incidencia del delito.
- Las 16 carteras cubren una vez cada una de las 394 partidas, 435 obras y 1.889 mediciones. Los totales de programas toleran únicamente el redondeo en millones de las planillas originales.
- Los IDs secuenciales de las filas PDF no se interpretan como códigos de jurisdicción. Se usan los códigos reales de PA. Interior tiene ejecución 2026 y ninguna fila homónima 2027: se conserva el dato faltante sin calcular una caída de 100%.
- Los cambios reales usan el deflactor anual ya documentado en el tablero. Los pagos y prestaciones mantienen sus propios períodos. No se construyen costos unitarios con gasto de septiembre y prestaciones de junio.
- La cobertura de comparaciones individuales sigue en 380/394: estas fichas integran datos disponibles y no resuelven los 14 casos que requieren distribución documentada de costos.

## Fuentes

Proyecto ONP: cuadro 4 por jurisdicción, planilla 7 por programa y planilla 12 de proyectos, conservados con fuente y huella en `budget.json`. Finanzas de Presupuesto Abierto al 15/09/2026; metas acumuladas al segundo trimestre. `decisions.json` conserva las fuentes y los insumos usados; PDF y web comparten la misma lectura editorial y datos.

La comprobación de disponibilidad en [ONP Evaluación 2026](https://www.mecon.gob.ar/onp/evaluacion/2026), [Finanzas: datos trimestrales de deuda](https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda) y [OPC: operaciones de deuda pública](https://opc.gob.ar/operaciones-de-deuda-publica/) no encontró un corte posterior al primer trimestre para los dos primeros ni posterior a julio para el último. No se reemplazan faltantes por proyecciones.

## Validación

- 146 pruebas Python y 127 Node aprobadas; controles adicionales sobre claves de medidas, totales por cartera, límites de selección y versiones de PDF.
- Ocho validadores de datos e informes, incluidas las provincias y los 135 municipios.
- 46 páginas nuevas renderizadas y revisadas. Los informes incluyen nombre, página, enlace al tablero y fuentes.
- Prueba de 16 selecciones y descargas, seis políticas, vínculos desde programas, tema claro/oscuro y pantallas de 320, 390, 768 y 1440 píxeles. Sin errores JavaScript ni desbordamiento horizontal.
- Google Analytics registra las nuevas vistas y descargas permitidas; conserva la exclusión de parámetros de búsqueda y otros filtros de las rutas enviadas.

Los pendientes restantes se mantienen en [el registro de trabajo](nacion-pendientes-2026-09-18.md). La solicitud externa a ONP fue descartada por el usuario y no se presentó.

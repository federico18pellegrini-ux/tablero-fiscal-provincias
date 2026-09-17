# Presupuesto Nacional: identidad municipal

Revisión de diseño y navegación, 17/09/2026. Datos y archivos de fuentes sin modificaciones.

## Diagnóstico y decisiones

| Problema observado | Cambio aplicado |
| --- | --- |
| La portada de tres líneas demoraba el acceso al primer dato y recordaba demasiado a la referencia. | Entrada compacta con gasto propuesto, comparación y una lectura propia de la diferencia entre variación nominal y real. En celular, la cifra precede al texto. |
| Fondo negro, amarillo, tres familias tipográficas y barras tramadas rompían la continuidad con Municipios. | Manrope compartida, fondo claro, verde petróleo, marca fp., tarjetas con esquinas redondeadas y gráficos de colores sólidos. Modo oscuro verde opcional. |
| Once capítulos y dos índices llevaban a un recorrido largo. | Cinco vistas: Panorama, Gasto, Obras, Economía y Ejecución. Se conservan los once contenidos y todas las anclas anteriores; metodología y descargas tienen acceso propio. |
| El mismo total aparecía en la portada y en las cuatro cifras de escala. | Se elimina esa repetición y se usan intereses, gasto de capital e inflación para explicar lo que condiciona el total. |
| Comparar 2027 con 2026 no corresponde a la vista de ejecución mensual 2026. | La base comparativa aparece sólo en Panorama y Gasto. La explicación de precios distingue escenario anual e IPC mensual observado. |
| Había números y rótulos pequeños, además de unidades que exigían volver a otra sección. | Cuerpo de 16 px, notas de 14 px, valores principales mayores y leyendas independientes para montos y participaciones. `bill.` identifica billones. |

La redacción de títulos, introducciones y lectura central responde a las preguntas de gestión. Los nombres oficiales de programas y organismos se conservan para mantener su trazabilidad. El brief original permanece documentado como antecedente, no como la identidad vigente.

## Validación de esta revisión

- 94 pruebas Node aprobadas; se agregaron casos de navegación a secciones históricas y del contraste nominal/real según la base seleccionada.
- Verificación de referencias HTML/JavaScript y ausencia de identificadores duplicados.
- Navegador real a 360, 390, 768 y 1440 px. Las cinco vistas a 360 px no desbordan horizontalmente. A 390 px, la cifra principal queda en el primer pantallazo de 844 px de alto.
- Comprobados ambos temas, bases inicial/vigente/cierre, corrientes/constantes, selección de Buenos Aires, búsqueda y ficha de universidades, vistas históricas, ejecución por jurisdicción y acceso al exportador CSV desde metodología.
- El enlace antiguo `?precios=real&base=law&vista=functions#comparacion` abre Gasto con la base y unidades correctas. Se corrigió y verificó Atrás para restaurar tanto la vista como los filtros.
- El porcentaje de ejecución se mantiene en 69,1% nacional al cambiar unidades; Ministerio de Economía muestra 69,5%. Las faltas de correspondencia y de IPC observado permanecen declaradas.

No se modificaron los importadores, la base normalizada ni los informes provinciales o municipales. La revisión no equivale a una nueva auditoría o actualización de fuentes fiscales.

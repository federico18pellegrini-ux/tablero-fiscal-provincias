# Informe provincial de tres páginas

El botón visible «Exportar informe (PDF)» descarga el informe de la provincia elegida en el menú fijo. Las 24 jurisdicciones tienen el mismo diseño y estructura; los números, diagnóstico, disponibilidad y recomendaciones dependen de cada provincia. El documento tiene un alcance propio: cierre anual, comienzo del año siguiente, transferencias mensuales, deuda y resultados de gobierno. No replica filtros transitorios de una sola vista.

La lectura editorial conecta el dato con su consecuencia y una recomendación. Distingue déficit antes de intereses, déficit por intereses, superávit, equilibrio y falta de información. El trimestre conserva su diagnóstico propio; las transferencias se interpretan según su variación real. La agenda de 100 días cierra con un juicio profesional ligado a las cuentas de la provincia. Las recomendaciones no se presentan como hechos observados ni como medidas presupuestadas. Se conserva el límite de tres páginas, los gráficos y el pie con autor y numeración.

## Generación y actualización

Instalar `requirements-reports.txt` y ejecutar `python scripts_export_management_reports.py`. Produce los 24 PDF en `reports/` y un manifiesto con períodos, referencias, huellas de los datos y de cada archivo. La importación ordinaria `scripts_regenerate_2026.py` también regenera estos informes. Si se actualiza otra fuente, ejecutar el generador antes de publicar. CI rechaza informes que no correspondan a los datos del tablero.

Para inspección local se admite `--province "Buenos Aires" --output RUTA`. La opción `--check` verifica la vigencia de todas las entradas. Los archivos son estáticos y livianos, con gráficos vectoriales y texto seleccionable. No requieren un servicio externo de IA ni enviar datos a terceros para descargarlos.

## Decisiones metodológicas

- El cierre completo usa la serie APNF de DNAP, una única versión, con identidad ingresos menos gastos igual a resultado financiero. Se agrega `data/annual_fiscal_accounts.json` con 504 observaciones de 2005 a 2025, hoja, columna y filas de origen.
- La Pampa 2025 aparece con ceros de origen, pero la nota oficial la excluye por falta de información completa. Se muestra como faltante; no se sustituye por 2024. Santiago del Estero 2025 informa compromiso y se identifica. El agregado de gasto de capital usa 22 jurisdicciones con el mismo año y registro, sin La Pampa ni Santiago del Estero. Mide composición del gasto, no eficiencia; las responsabilidades de cada jurisdicción también pueden diferir.
- Enero-marzo se compara con enero-marzo. No se interpreta la diferencia entre un trimestre y un año entero como una caída interanual. No se publican variaciones reales de ejecución anual sin detalle mensual.
- Se incorporó la base oficial mensual RON 2025, 24 jurisdicciones por 12 meses, con los clasificadores ya utilizados en 2026. Para totales se toma únicamente `Total (1)+(2)`. No se suman nuevamente CFI, fondos o subtotales. El IPC observado se aplica a cada mes antes de sumar; la falta de un mes o índice impide calcular la variación acumulada real.
- Los datos de stock y los calendarios de servicios tienen fechas propias. Los servicios pasados no se proyectan. PBA y Córdoba conservan sus valuaciones; Entre Ríos identifica el presupuesto plurianual, otros pasivos y gastos, y la fecha de publicación cuando no consta una fecha de valuación.
- Los resultados de Aprender y DEIS conservan su año. Se indica participación estudiantil y no se atribuye causalidad entre gasto de un año y resultados de otro.
- La reasignación equivalente a un punto porcentual de capital es un ejercicio aritmético con gasto total constante; no supone recursos adicionales ni es una propuesta de piso obligatorio.

## Fuentes nuevas

- [Serie anual APNF 2005-2025](https://www.argentina.gob.ar/sites/default/files/serie_aif-apnf-2025.xlsx).
- [Recursos nacionales, información consolidada 2025](https://www.argentina.gob.ar/sites/default/files/informacion_consolidada2025_5.xlsx).
- [Notas metodológicas y ejecuciones DNAP](https://www.argentina.gob.ar/economia/sechacienda/coordinacion-fiscal-provincial/ejecucion-presupuestaria-provincial/ejecuciones).

Los originales se mantienen intactos. El importador `scripts_import_report_sources.py` usa copias locales y registra sus SHA-256. Las referencias de los informes se conservan en el manifiesto, sin añadir carteles «Fuente» a la lectura del tablero.

## Verificación

La validación automática revisa 24 provincias, tres páginas, atribución y numeración, identidad fiscal, componentes de capital, criterios de exclusión, IPC mes a mes, coincidencia con la dinámica real del tablero, ausencia de proyecciones cuando falta calendario y vigencia de archivos. Los límites de cada bloque impiden generar texto que invada el pie de página. La revisión visual se realiza sobre los PDF renderizados y sobre el botón en tamaños de celular y tableta.

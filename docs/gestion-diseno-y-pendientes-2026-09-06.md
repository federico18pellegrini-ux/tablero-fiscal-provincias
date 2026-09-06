# Gestión, diseño y cobertura operativa

## Diseño

La portada anterior desplazaba el diagnóstico debajo de varias barras y mensajes repetidos. El nuevo diseño conserva la identidad de Federico Pellegrini, reduce la portada, organiza la información en superficies azul oscuro y reserva el color de alerta para el dato que lo requiere. La provincia permanece visible; perfil, período y unidades se agrupan en un desplegable.

En celulares, un selector reúne las once vistas y herramientas. El diagnóstico y los primeros dos resultados fiscales se ven completos en una pantalla de 390 × 844. Las vistas nacionales ocultan los controles provinciales para hacer explícito su ámbito. Se conserva el acceso a las 24 jurisdicciones, las fuentes, las tablas, la historia y los PDF existentes. Los controles conservan etiquetas accesibles y foco visible.

## Incorporaciones de datos

- Gasto nacional: Hacienda, IMIG julio 2026. Se importan componentes de gasto primario, aperturas sociales, ingresos e intereses; valores de julio de 2025 y 2026 y siete observaciones mensuales de 2026. La variación real julio/julio usa los índices nacionales sin redondear. La serie de 2026 deflacta cada mes a precios de julio; no elimina estacionalidad. No se calcula un acumulado real interanual sin todos los meses del año anterior.
- Vencimientos: Finanzas, cuadro A.3.1 del stock al 31/03/2026. Abril 2026–marzo 2027, capital e intereses. Conversión de miles de USD a millones de USD. Incluye adelantos BCRA. Se muestra como perfil estático histórico, no calendario vigente: no incorpora nuevas emisiones, canjes y pagos posteriores.
- Tesorería: deuda exigible de julio de 2026 por clase de gasto y serie enero–julio. Excluye deuda pública y registros previos a 2025. Incluye gastos figurativos. Son stocks mensuales, no flujos sumables ni atrasos consolidados de todo el Estado.
- Adelantos BCRA: calendario al 31/08/2026, septiembre y 4T26. Septiembre y 3T26 son la misma observación; no se duplican. No se adicionan al perfil histórico, por superposición de cobertura y diferencia de fecha y moneda.
- Comparación federal: promedio simple, mediana y agregado por habitante para las mismas 23 provincias sin CABA. Flujo RON 2025 y población del Censo 2022. Ninguno se presenta como una proyección de población de 2025.

Cada archivo de datos identifica sus fuentes. `scripts_import_national_operations.py` recibe los dos Excel oficiales sin modificarlos y guarda referencias de hojas, celdas y hashes. `scripts_build_federal_benchmarks.py` usa la base federal existente y exige las 23 provincias comparables.

## Herramientas listas, inputs que requieren a la gestión

El escenario de caja permite trabajar con Nación o una provincia a 30, 90 o 365 días. Exige fecha y seis importes no negativos; un casillero vacío no equivale a cero. Separa caja libre, ingresos, pagos primarios incluida inversión, capital de deuda, intereses y financiamiento confirmado. Al cambiar jurisdicción u horizonte se borran importes para impedir reutilizar supuestos de otro escenario. No guarda ni envía los datos ingresados.

La caja libre no puede acreditarse con los informes revisados. Requiere conciliación bancaria, afectaciones, compromisos exigibles y financiamiento desembolsable. El saldo fiscal y las reservas del BCRA no la sustituyen.

La matriz de metas incluye 96 líneas de base observadas para 24 jurisdicciones, con período y fuente: homicidios, Lengua, Matemática y mortalidad infantil. Las metas, fechas y responsables están vacíos: son decisiones de la gestión, no observaciones estadísticas. Se ofrece su descarga en Resultados de gobierno.

## Correcciones complementarias

El período y la referencia del resultado primario estructural ahora usan el corte 1T26 para todas las jurisdicciones con esa información. Se explican los denominadores de autonomía, personal y capital. Se corrige la definición de billón: un millón de millones. Se reemplazan abreviaturas y etiquetas técnicas en varias explicaciones visibles.

## Verificación

51 pruebas Python y 3 pruebas JavaScript; conciliación de componentes, resultados, acumulados, vencimientos, IPC y escenarios. Las 150 filas TOP mantienen cero diferencias y los 31 reclamos nacionales pasan su validación. Navegación de once vistas, 24 provincias, ocho series mensuales de gasto y limpieza de escenarios. Revisión visual en escritorio y celular.

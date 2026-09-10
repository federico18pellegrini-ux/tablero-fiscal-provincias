# Presupuesto anual de los municipios

Se agrega una autorización anual de gasto independiente de las cuentas fiscales y de las transferencias provinciales. El bloque aparece en Panorama y Recursos. El informe PDF y las descargas conservan año, corte, unidad y población de referencia.

## Cobertura al 10 de septiembre de 2026

- 103 municipios con un presupuesto anual respaldado por documentos oficiales.
- 93 corresponden al ejercicio 2026; 10 son históricos de 2024 o 2025.
- 32 pendientes de incorporar un total anual verificable. No se completa con cero ni se afirma que no publiquen presupuesto.
- El presupuesto original y el vigente se mantienen separados. Un original publicado no se presenta como si fuera el vigente de septiembre.

El registro `municipios/data/annual_budgets_verified.json` contiene cada cifra decimal, URL, SHA-256, tamaño del documento, páginas consultadas y ubicación de la cifra. El catálogo público `municipios/presupuestos.html` identifica los 135 municipios, los faltantes y el alcance de cada presupuesto. La descarga `municipios/data/presupuestos_anuales.csv` conserva los importes en pesos con dos decimales.

## Criterios

1. Se utiliza el crédito de **gastos**. No se sustituye por recursos, ejecución semestral, déficit ni saldo bancario. En Pinamar y Campana, por ejemplo, los totales vigentes de recursos y gastos difieren.
2. Para los cuadros RAFAM de situación financiera, se concilia el total vigente con objetos del gasto. Se acepta el corte exacto del documento, aunque sea anterior al de las cuentas fiscales del municipio.
3. Se excluyen los cuadros cuyo período comienza después de enero cuando no acreditan un saldo inicial anual. San Isidro conserva $333.076.160.469,20 a marzo; los $2.621.942.061,46 del cuadro abril–junio no se presentan como presupuesto anual ni se suman automáticamente. General Guido, General Viamonte y 25 de Mayo también conservan el corte verificable de marzo. Ayacucho permanece pendiente.
4. Las ordenanzas se usan por su artículo de aprobación, no por el importe de una licitación, una propuesta o una noticia periodística. Ensenada y Pilar se cotejaron visualmente con la norma firmada.
5. San Nicolás conserva el total explícito del artículo 4 de la Ordenanza 10681 y señala diferencias entre sus subtotales impresos. No se publica una desagregación con esos subtotales ni se suma el presupuesto separado de Aguas de San Nicolás.
6. Los presupuestos municipales pueden incluir diferentes organismos y transferencias internas. El catálogo no los convierte en un ranking homogéneo. Bahía Blanca conserva una advertencia específica por los gastos figurativos.
7. El dato por habitante divide el monto destacado (vigente cuando está disponible; en su defecto, original) por la población del Censo 2022. No es una transferencia al vecino ni una medida de desempeño.
8. Los importes son pesos corrientes. No se infiere ejecución mensual para ajustar por inflación una autorización anual.

## Controles

El constructor valida los 135 estados, fechas, faltantes, evidencia, sumas por componentes, modificaciones y coherencia con los presupuestos detallados de General Las Heras y Tigre. Se agregan pruebas contra la aceptación de movimientos trimestrales y de cifras sin respaldo. Los controles de navegador recorren los 135 municipios en Panorama y Recursos, verifican valores, fuentes, informes seleccionados, letras y desbordes en 390 y 768 píxeles. Los 135 PDF se regeneran desde el mismo conjunto de datos y pasan revisión de cajas de texto y márgenes.

La incorporación del presupuesto no amplía por sí sola la cobertura del ranking fiscal. Los ingresos, gastos y resultados mantienen sus períodos y validaciones anteriores.

# Presupuesto, ejecución y fuentes pendientes

Incorporación del 06/09/2026. Los archivos descargados se conservan fuera del repositorio; las publicaciones incluyen celdas de origen, unidad y huellas SHA-256.

## Incorporado

- Presupuestos iniciales 2026 de 24 jurisdicciones, fuente DNAP. Misiones pasa de miles a millones. En Tucumán se restan operaciones figurativas internas; en Buenos Aires se suman ingresos corrientes y de capital, y gastos corrientes y de capital. Financiamiento no se suma a ingresos.
- Ejecución APNF de enero–marzo de 2025 y 2026: 48 observaciones. La Pampa no tiene importes informados para 2026 y conserva valores nulos.
- Avance respecto del presupuesto inicial solamente para CABA, Chubut, Córdoba, Entre Ríos, Formosa, Jujuy y Santa Cruz, con cobertura identificada APNF. Es orientativo: la homogeneidad institucional no elimina ajustes metodológicos DNAP. No mide desvío frente a crédito vigente ni programación trimestral. No se compara automáticamente contra 25%.
- El resto presenta ambas fuentes con advertencia de cobertura y sin porcentaje. Los encabezados erróneos de año en Chaco, Santa Cruz y Tucumán quedan advertidos junto a la fuente legal 2026. Tierra del Fuego conserva la aclaración de prórroga 2025 para 2026.
- “Qué cambió” compara resultado financiero/ingresos y gasto de capital/gasto total entre primeros trimestres. Cambios en puntos porcentuales; no se afirman variaciones reales a partir de valores nominales.
- Gráfico de composición trimestral y tarjetas legibles en móvil. Los controles generales no alteran período ni unidad de este bloque, señalado explícitamente.
- Entre Ríos: calendario orientativo 2026–2028, Sector Público No Financiero provincial. El Anexo I no explicita unidad; los importes 2026 se concilian con I29 e I75 del presupuesto oficial en millones, con diferencia de redondeo de 0,004 millones por concepto. Incluye otros gastos y pasivos. Se registra fecha de presentación, no una fecha de valuación inventada. Son tres calendarios futuros verificados, junto con PBA y Córdoba.
- Simulador de costo de propuesta: cantidad × costo mensual × meses + costo inicial. Financiamiento separado. Campos vacíos no equivalen a cero; meses enteros entre 1 y 12. Sin persistencia ni importes inventados.
- Control de 30 enlaces: 27 archivos iguales a los importados, dos accesibles sin validación de cifras y uno inaccesible. El informe fecha el control; no es una actualización automática.

## Pendiente por fuente o definición

La caja libre de todas las provincias requiere conciliación de fondos utilizables, afectados y pagos exigibles; no se obtiene del superávit fiscal. El archivo Santa Cruz publicado como junio 2026 contiene encabezado septiembre 2024 y diferentes totales de deuda exigible entre hojas; no se carga como caja actual. Su deuda flotante de marzo 2026 no explicita unidad y no se convierte por conjetura. CABA mantiene error 404 en el enlace de perfil junio 2026. No se afirma que esos datos no existan.

Faltan crédito presupuestario vigente, metas trimestrales, calendario futuro verificado para 21 jurisdicciones y costos respaldados de cada programa. El simulador permite ordenar supuestos, no reemplaza esos faltantes.

## Reproducción y controles

`scripts_build_budget_execution.py <carpeta de fuentes>` reconstruye los presupuestos y ejecución; `scripts_build_provincial_debt_services.py <carpeta de deuda>` incorpora el anexo de Entre Ríos y busca el presupuesto conciliador en la carpeta hermana `completion-sources`.

`scripts_check_management_sources.py --output <informe.json>` controla enlaces y cambios sin importar datos. También se puede ejecutar a pedido desde la acción “Revisar fuentes de gestión”; entrega un artefacto y no modifica producción.

Pruebas: cobertura y datos faltantes, reconstrucción por celdas y unidades, deducción de figurativos, conciliación de Entre Ríos, razones fiscales y cálculo de costos. Verificación visual en 390 y 768 píxeles y cambio de las 24 provincias.

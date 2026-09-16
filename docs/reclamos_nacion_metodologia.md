# Reclamos de las provincias a Nación

Revisión documental: 15 de septiembre de 2026. La revisión no certifica un saldo contable, judicialmente exigible ni actualizado a esa fecha.

## Qué se publica

La base canónica es `data/reclamos_nacion/evidencia_verificada.json`. Cada registro corresponde a una publicación oficial identificada por URL, organismo y título. Conserva la moneda original, el importe (exacto, aproximado, mínimo o rango), la fecha de publicación y, cuando existe, la fecha de valuación. La fecha de publicación nunca se usa como valuación común.

Se distinguen reclamo provincial, anticipo acordado, acuerdo de pago, crédito reconocido para compensar, cobro informado y documento sin monto. Los componentes de un reclamo ya están incluidos en su total. Los registros NO se suman entre sí. No se convierte moneda, no se aplica IPC ni se deducen cuotas acordadas como si fueran pagos.

En particular, la pérdida de recaudación, una obra nacional no ejecutada y una transferencia devengada e impaga son conceptos distintos. Su inclusión en un reclamo político provincial no prueba un crédito reconocido por Nación. Tampoco el déficit de una caja previsional equivale automáticamente a deuda de ANSES.

## Cobertura y límites

Se muestran las 24 jurisdicciones. Doce tienen importes documentados: Buenos Aires, CABA, Chubut, Córdoba, Corrientes, Entre Ríos, La Pampa, Mendoza, Neuquén, Santa Fe, Tierra del Fuego y Tucumán. Los importes incluyen distintos tipos de evidencia; no todos son reclamos. Córdoba incorpora el convenio de 2026. La Pampa informa cuotas acordadas y cobros, sin un monto total de deuda.

Chaco, Formosa, La Rioja, Misiones, Salta y Santa Cruz tienen documentos sin un monto incorporable. Permanecen pendientes Catamarca, Jujuy, Río Negro, San Juan, San Luis y Santiago del Estero. El estado describe la cobertura de esta base, no la existencia o ausencia de acreencias.

El Resumen prioriza el último reclamo cuantificado y lo atribuye con «Según la Provincia» y fecha. Si no hay un reclamo cuantificado, destaca el importe del documento más reciente con monto y un título acorde a su tipo: acuerdo, anticipo, crédito para compensar o cobro. Los reclamos se muestran en rojo; acuerdos y compensaciones en azul; los cobros en verde. La Pampa muestra su cuota de $5 mil millones con «por mes» visible, sin multiplicarla ni restarle cobros. El campo amount_basis=mensual identifica estas cuotas; también se aplica al antecedente de Córdoba de 2025. Los documentos sin importe muestran «Monto no publicado»; las jurisdicciones sin documentación incorporada muestran «Sin dato documentado»; un error de carga muestra «Datos no disponibles». Los importes conservan su moneda original y no responden al selector de ingresos en pesos constantes.

No se publica un saldo actual conciliado para ninguna jurisdicción. Se necesita reconstruir, para cada concepto, saldo inicial, actualización conforme al instrumento aplicable, reconocimiento, pagos efectivos y compensaciones. Un anticipo aprobado o un bono autorizado no acredita por sí solo un cobro. No corresponde construir un ranking de deudas ni un total nacional con estas referencias.

## Reproducción y controles

`python scripts_build_nacion_reclamos.py` genera el JSON de consumo y las salidas CSV/JSON. `python scripts_validate_reclamos_nacion.py` verifica procedencia, universo, montos, fechas, componentes y coincidencia de los derivados. `python scripts_sync_embedded_data.py` sincroniza el respaldo del HTML. Las pruebas incluyen unidades argentinas, separación de monedas, ausencia de sumas incompatibles y faltantes como nulos.

El nombre histórico del CSV “agregado provincial” se conserva por compatibilidad de rutas, pero ahora solo contiene estado de cobertura y saldo no verificado. No agrega montos.

## Corrección de la versión anterior

Se retiraron filas que se identificaban como ejemplos y usaban enlaces genéricos, junto con los subtotales que se calculaban a partir de ellas. Esa base no respaldaba una deuda provincial verificada. También se retiraron los ceros derivados de provincias sin carga. Las versiones anteriores permanecen en el historial del repositorio; no son evidencia vigente.

# Reclamos de las provincias a Nación

Revisión documental: 15 de septiembre de 2026. La revisión no certifica un saldo contable, judicialmente exigible ni actualizado a esa fecha.

## Qué se publica

La base canónica es `data/reclamos_nacion/evidencia_verificada.json`. Cada registro corresponde a una publicación oficial identificada por URL, organismo y título. Conserva la moneda original, el importe (exacto, aproximado, mínimo o rango), la fecha de publicación y, cuando existe, la fecha de valuación. La fecha de publicación nunca se usa como valuación común.

Se distinguen reclamo provincial, anticipo acordado, acuerdo de pago, crédito reconocido para compensar, cobro informado y documento sin monto. Los componentes de un reclamo ya están incluidos en su total. Los registros NO se suman entre sí. No se convierte moneda, no se aplica IPC ni se deducen cuotas acordadas como si fueran pagos.

En particular, la pérdida de recaudación, una obra nacional no ejecutada y una transferencia devengada e impaga son conceptos distintos. Su inclusión en un reclamo político provincial no prueba un crédito reconocido por Nación. Tampoco el déficit de una caja previsional equivale automáticamente a deuda de ANSES.

## Cobertura y límites

Se muestran las 24 jurisdicciones. Ocho tienen montos documentados: Buenos Aires, CABA, Córdoba, Corrientes, Entre Ríos, Mendoza, Neuquén y Santa Fe. El registro de Córdoba es un antecedente de 2025, expresamente marcado como pendiente de actualización con el convenio de 2026. Misiones y Santa Cruz tienen documentos sin un monto incorporable.

Quedan pendientes de documentación cuantificable Chubut, Catamarca, Chaco, Formosa, Jujuy, La Pampa, La Rioja, Río Negro, Salta, San Juan, San Luis, Santiago del Estero, Tierra del Fuego y Tucumán. Esto NO certifica ausencia de acreencias: es el estado de cobertura de esta base.

No se publica un saldo actual conciliado para ninguna jurisdicción. Se necesita reconstruir, para cada concepto, saldo inicial, actualización conforme al instrumento aplicable, reconocimiento, pagos efectivos y compensaciones. Un anticipo aprobado o un bono autorizado no acredita por sí solo un cobro. No corresponde construir un ranking de deudas ni un total nacional con estas referencias.

## Reproducción y controles

`python scripts_build_nacion_reclamos.py` genera el JSON de consumo y las salidas CSV/JSON. `python scripts_validate_reclamos_nacion.py` verifica procedencia, universo, montos, fechas, componentes y coincidencia de los derivados. `python scripts_sync_embedded_data.py` sincroniza el respaldo del HTML. Las pruebas incluyen unidades argentinas, separación de monedas, ausencia de sumas incompatibles y faltantes como nulos.

El nombre histórico del CSV “agregado provincial” se conserva por compatibilidad de rutas, pero ahora solo contiene estado de cobertura y saldo no verificado. No agrega montos.

## Corrección de la versión anterior

Se retiraron filas que se identificaban como ejemplos y usaban enlaces genéricos, junto con los subtotales que se calculaban a partir de ellas. Esa base no respaldaba una deuda provincial verificada. También se retiraron los ceros derivados de provincias sin carga. Las versiones anteriores permanecen en el historial del repositorio; no son evidencia vigente.

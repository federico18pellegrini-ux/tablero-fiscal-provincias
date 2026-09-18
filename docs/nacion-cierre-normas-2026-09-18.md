# Cierre integrado y normas — 18/09/2026

## Entrega

- `/nacion/#escenarios`: gasto mensual 2026 proyectado y resultado/financiamiento 2027 con nueve supuestos editables. Descarga JSON con resultados, hipótesis y huellas de las bases.
- `/nacion/#normas`: cinco documentos oficiales, 520 registros, buscador por programa/organismo/código y enlaces a las páginas originales.
- Informes: enlaces actualizados en capítulos 11 y 16, sin agregar páginas ni incorporar una simulación particular como dato oficial.

## Método del cierre

Para cada una de las 29 funciones se conservan los ocho meses completos de 2026. Se calcula el cambio real enero–agosto frente a 2025. Ese factor escala los meses septiembre–diciembre de 2025, expresados en pesos de agosto de 2026. Solo a los meses futuros se aplican la inflación mensual elegida y el cambio adicional del ritmo real de gasto. No se usa septiembre parcial. Las funciones se vinculan por finalidad y función, no por el ID secuencial de la planilla del proyecto. No se estima el ingreso 2026 por este procedimiento.

El escenario 2027 parte de CAIF: impuestos y aportes responden al PIB real y al nivel de precios; prestaciones y resto primario tienen traslados separados; intereses tienen un supuesto propio. Otros ingresos, amortizaciones y aplicaciones financieras conservan los importes nominales del proyecto. El financiamiento requerido suma aplicaciones financieras, resta resultado financiero y reducción de activos; las transferencias financieras internas se compensan. El escenario inicial reproduce exactamente el cuadro oficial y una brecha de financiamiento cero. No simula la movilidad legal, contratos ni rezagos de indexación.

## Normas y conciliación

Los archivos oficiales y sus URL, tamaño y SHA-256 están en `nacion/data/act-sources/sources.json`. Los importes originales en pesos se convierten a millones. Se excluyen subtotales repetidos y aplicaciones financieras. Las comunicaciones DA usan la tabla por programa y finalidad; los DNU usan el total de programa del gasto corriente y de capital.

| Norma | Millones de pesos |
|---|---:|
| DA 2 | 42,570000 |
| DA 20 | -2.439.415,516143 |
| DNU 594 | 4.448.995,993497 |
| DA 26 | 2.161.929,975993 |
| DNU 867 | 234.122,290520 |
| Total | 4.405.675,313867 |

El total coincide con vigente menos inicial de PA. Hay registros originales para 306 aperturas actuales; 143 de las 410 concilian su cambio neto con estas normas (99 con cambios y 44 sin cambio). Otras 267 tienen residuales: las reasignaciones internas pueden compensarse en el total. No se atribuyen a una norma por intuición.

Dos códigos de la DA 26, SAF 322 programas 54 y 55, conservan su nombre original y no se asignan a códigos actuales. Sus importes suman $4.968,412784 millones. Esto explica el residual neto del universo de programas vinculados; no es una diferencia del total global.

El nomenclador PA actualizado al 16/09 solo vincula jurisdicción/subjurisdicción/entidad/programa a SAF. Los saldos comparados siguen al 15/09; no se actualizó silenciosamente la ejecución. La extracción es reproducible con `scripts_build_national_acts.py --check` y forma parte del control de integración.

## Límites pendientes

Se mantienen las 14 comparaciones de programas sin distribución de costos documentada, las mediciones físicas faltantes y los costos de terminación de obras. Los costos por prestación requieren gasto atribuible y períodos compatibles. El seguimiento de responsables e hitos requiere decisiones reales del equipo de gestión. No se presentó el pedido de acceso a la información, por decisión del usuario.

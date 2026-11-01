# RIGI: registro y escenarios parciales — 01/11/2026

Se incorporan 27 proyectos registrados como aprobados por Economía, por USD 76.173 millones de inversión comprometida total (montos de origen redondeados). Las 33 filas territoriales se deduplican por acto normativo. Se cruzan con las 27 aprobaciones de la biblioteca ARCA y se preservan las resoluciones completas. Última publicación: Agua Rica, 27/10/2026. La fecha de adhesión se extrae del artículo correspondiente y se distingue de la publicación; P.E. Olavarría y San Matías omiten “de” antes del año, variante controlada por prueba.

## Estimación condicionada

Referencia oficial: plan sectorial de inversión 2027, USD 7.827 millones. No se reparte por proyecto según el stock de inversión comprometida ni se confunde con ejecución.

Solo derechos de importación: plan × parte importada × parte que pagaría arancel sin RIGI × arancel contrafactual. Los tres últimos factores son supuestos de sensibilidad, no datos observados. Se considera el componente importado como valor aduanero. No se estima reacción de los inversores ni efectos macroeconómicos inducidos.

| Escenario | Importado | Pagaría sin RIGI | Arancel | Renuncia aduanera, USD millones |
|---|---:|---:|---:|---:|
| A | 20% | 25% | 2% | 7,827 |
| B | 35% | 50% | 7% | 95,88075 |
| C | 50% | 75% | 14% | 410,9175 |

No es un intervalo de confianza ni una estimación central. La segunda proporción descuenta arancel cero y beneficios alternativos, incluidos los de Ley 24.196. Se excluye tasa de estadística. No se agregan estos resultados al 3,67% del PIB de gasto tributario oficial sin conciliar bases y alcance.

El costo total 2027 permanece nulo (desconocido), no cero. Ganancias requiere base imponible, escala, deducciones y quebrantos; amortización e IVA tienen componentes de diferimiento. El ejemplo de IVA es exclusivamente financiero: adelantar seis meses USD 100 millones de crédito a una tasa hipotética de 8% tiene valor actual aproximado USD 3,8 millones, no sumable al escenario aduanero. No se agrega un diferencial del 10% a toda utilidad: 35% es una tasa marginal de la escala general.

El único cero estructural identificado es la reducción de dividendos de 7% a 3,5% en 2027: requiere siete años desde adhesión y ninguno de los 27 proyectos cumple ese plazo. Otros beneficios siguen sin base suficiente; exportaciones requieren además esperar dos o tres años según el encuadre y conocer producto, derechos y operaciones propias.

## Entrega y controles

Módulo editable en `#rigi-estimation`, con selector para las 27 fichas y enlace individual a ARCA. El PDF conserva los tres escenarios publicados y continúa en dos páginas; las doce versiones generales también incorporan el análisis. El usuario puede modificar los supuestos en pantalla sin alterar el corte oficial ni atribuir la simulación a Economía.

Fuentes: `nacion/data/rigi-sources/sources.json`, 33 originales con hash y bytes preservados, incluidas las 27 resoluciones. Validador offline `scripts_build_rigi_estimate.py --check`; tax-expenditures incorpora la misma estructura. Los enlaces Infoleg de los textos devolvieron error; se recuperaron los actos completos mediante ARCA.

Controles locales: 16 pruebas Python sobre fuentes/modelo/PDF, 22 pruebas JavaScript de cálculo/navegación/selección, validadores de datos y PDF. Prueba funcional a 390/768/1440 px: selección de 27 proyectos, cero y campo vacío distintos, ausencia de errores/desbordamientos y descarga de PDF. Revisión visual del PDF de dos páginas. No se afirma haber conciliado importaciones, utilidades o ejecución de los proyectos con información que no está publicada.

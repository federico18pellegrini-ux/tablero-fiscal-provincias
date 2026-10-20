# Recaudación: revisión de pendientes del 20 de octubre

## La Pampa 2025: cierre recuperado

La planilla histórica anual DNAP deja vacío 2025. Sin embargo, el archivo mensual oficial `top_mensual_2025_12.xlsx` contiene los doce meses, incluidos noviembre y diciembre. Su descarga actual coincide byte por byte con el original preservado.

Se sumaron los doce meses después de reconciliar cada total con los cinco impuestos. Resultado: **$431.096,382111 millones corrientes**. Se incorporan seis observaciones al histórico (total y cinco componentes). No es una estimación ni una cifra de presupuesto. Procedencia, hash y cálculo: `data/lapampa_2025_annual.json`; importador reproducible: `scripts_complete_lapampa_2025.py`.

Corrige el pendiente registrado en `historicos-verificados-2026-10-20.md`: faltaba integrar el cierre mensual, no obtenerlo. Los informes PDF actuales no incluyen este histórico y no cambian sus insumos.

## Meses nuevos encontrados, pendientes de integración

- Mendoza: ATM publica septiembre 2026. Los cuatro impuestos suman **$153.095,292568 millones**. “Ingresos varios”, $3.421,805589 millones, queda separado. Se comprobó que las cifras de agosto de los cuatro impuestos coinciden con las cargadas desde DNAP.
- Jujuy: Rentas publica septiembre 2026 como imagen. IIBB, Inmobiliario y Sellos suman **$30.779,771797 millones**. Los mismos tres conceptos de septiembre 2025 coinciden con DNAP. La placa totaliza $36.153,301824 millones porque incorpora derechos mineros y otros ingresos no tributarios: ese total no se debe trasladar a la serie tributaria.

Originales y transcripción preservados en `data/revenue-history-sources/` y `data/provincial_recent_sources_review.json`. No se incorporaron todavía a las series productivas: resta adaptar la carga provincial para conservar componentes no publicados sin imputar ceros, y actualizar conjuntamente dinámicas, cobertura y exportables.

La búsqueda en DGR, Estadística y Contaduría de La Pampa no encontró meses adicionales 2026 en las páginas consultadas. Esto no prueba que no existan en otras publicaciones. No se recorrieron exhaustivamente los 24 portales en esta revisión.

## Pesos constantes antes de 2017

El IPC nacional actual comienza en diciembre de 2016. El [archivo oficial de San Luis](https://estadistica.sanluis.gov.ar/Categorias/economia/precios/ipc-sanluis) ofrece los informes mensuales de 2016. Es un índice de la ciudad de San Luis, no nacional.

Puede construirse una serie empalmada como aproximación identificada: fijar diciembre 2016=100, llevar hacia atrás los índices de San Luis con su cociente respecto de diciembre, y usar desde entonces el nacional. Para flujos anuales se requiere verificar los doce niveles mensuales; no alcanza la inflación diciembre contra diciembre.

No se activa todavía: falta extraer y conciliar todos los niveles, revisar la continuidad anterior a 2016 y elegir/documentar el alcance histórico. No sería correcto etiquetar ese resultado como una serie nacional homogénea ni extender automáticamente el ajuste hasta 1984.

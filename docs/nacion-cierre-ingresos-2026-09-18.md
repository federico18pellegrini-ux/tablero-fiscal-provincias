# Ingresos y resultado proyectado 2026 — 18/09/2026

## Datos y conciliación

Se utilizan los ZIP originales de recursos mensuales de Presupuesto Abierto 2025 y 2026, archivados con sus huellas en el paquete de gestión. El original 2026 conserva corte 15/09. Se publican las copias en `nacion/data/revenue-sources/` y la procedencia en `revenue-planning.json`. Todos los importes por tipo y mes concilian con la serie ya publicada. El modelo usa los doce meses de 2025 y enero–agosto de 2026; excluye septiembre parcial.

El clasificador económico de los registros comienza por 1 (ingresos corrientes y de capital). No se añade endeudamiento a estos ingresos. La clasificación por rubro incluye ventas de acciones y recuperación de préstamos: se conserva la clasificación económica del original, sin reclasificar por el número del rubro.

Las utilidades BCRA se identifican por tipo 16, clase 4, concepto 2 y subconcepto 1. Se verifica además la denominación Banco Central. Abril 2025: $11.976.386,676207 millones. Mayo 2026: $24.400.000 millones. Se conservan como ingresos observados y se excluyen del factor de crecimiento de las rentas restantes.

## Proyección

Se agrupan impuestos, aportes/contribuciones, rentas sin utilidades BCRA y otros ingresos corrientes/de capital. Para cada grupo se escala el patrón real septiembre–diciembre de 2025 por la variación real enero–agosto 2026/2025. Se aplica la inflación futura y el cambio real adicional elegido solamente a los meses proyectados. Cada grupo tiene registros en los 20 meses; una ausencia o dato no numérico impide calcular el modelo.

Las nuevas utilidades BCRA tienen un campo separado en billones de pesos. El valor inicial cero es una hipótesis explícita de no nuevos giros, no la sustitución de información faltante. Si se ingresa un importe, se suma al total anual sin inventar un mes de cobro. La descarga registra ese monto como futuro sin asignación mensual.

El resultado presupuestario se calcula como ingresos percibidos menos gasto devengado de Administración Nacional. Se muestra con y sin utilidades BCRA. No equivale al saldo de caja SPN ni a disponibilidades de Tesorería. El escenario 2027 sigue usando como base el proyecto oficial, no hereda automáticamente la simulación 2026.

## Controles y límites

El modelo es reproducible con `scripts_build_national_revenue.py --check`. Los originales se validan por tamaño y SHA-256; los datos derivados concilian por tipo/mes. En el navegador se exige que las huellas de recursos e IPC correspondan al paquete de gestión cargado. La exportación JSON conserva supuestos, fuentes y ambos resultados.

Es una proyección mecánica con un solo año de estacionalidad: no modela cambios tributarios particulares ni identifica todos los demás ingresos extraordinarios dentro de cada grupo. La separación de BCRA corrige el mayor movimiento identificado, pero no convierte el resto en una recaudación estructural certificada.

## Otros pendientes revisados

La estructura organizativa del Decreto 581/2026 confirma dependencias y transferencias institucionales, pero no aporta una matriz de importes que permita asignar sin dudas los dos códigos deportivos originales a las aperturas actuales. No se redujo artificialmente la lista de residuales ni la de 14 comparaciones pendientes.

Fuente de la revisión organizativa: https://www.argentina.gob.ar/normativa/nacional/norma-427568/texto

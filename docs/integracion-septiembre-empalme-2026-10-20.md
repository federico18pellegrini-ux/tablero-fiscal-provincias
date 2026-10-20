# Integración de septiembre y empalme histórico — 20/10/2026

Se incorporaron siete observaciones tributarias: cuatro de Mendoza y tres de Jujuy. Se conservan los originales y sus hashes. No se agregaron ceros para categorías que no aparecen en las publicaciones.

Mendoza: $153.095,292568 millones en septiembre. Jujuy: $30.779,771797 millones. Sus subtotales excluyen, respectivamente, ingresos varios y derechos mineros/no tributarios. El cálculo acepta únicamente el conjunto exacto de impuestos verificados; un componente ausente invalida el subtotal. Septiembre se compara con los mismos conceptos DNAP de 2025.

Se recalcularon las dinámicas y la cobertura: ambas provincias llegan a septiembre. Enero–septiembre: Mendoza −2,8% real; Jujuy −3,7% real. Los 24 informes se regeneraron y se revisaron visualmente las páginas modificadas de Mendoza y Jujuy, con sus fuentes provinciales identificadas.

## Empalme

El histórico real se extiende a enero 2014 usando IPC San Luis hasta noviembre 2016. Diciembre 2016 conserva el ancla del IPC nacional. Factor anterior = factor nacional de diciembre 2016 × índice San Luis diciembre 2016 / índice San Luis del mes. Los factores históricos se mantienen separados de la serie nacional observada. Se conserva la base de visualización septiembre 2026.

El flujo anual usa el promedio de los doce índices. Es una aproximación al ajuste mensual, no una serie nacional homogénea antes de 2017. Ambas notas de gráfico indican el empalme. Los PDF ejecutivos no incluyen estos históricos largos; sus variaciones recientes continúan usando exclusivamente IPC nacional.

## Verificación y búsqueda adicional

Pruebas de subtotales, componentes faltantes, ancla y continuidad del empalme; 200 registros de trazabilidad sin diferencias. Prueba de gráficos para 24 provincias a 390×844: ambos históricos empiezan en 2014, sin valores no finitos ni desborde horizontal; revisión visual de Mendoza/Jujuy. Se verificó vigencia de los 24 PDF.

La suite local general tiene un fallo de reproducibilidad binaria del informe municipal de una muestra, previamente observado con el runtime local actualizado; los controles específicos provinciales pasan. Se requiere CI antes de publicación.

Búsqueda adicional preservada en `data/recent_provincial_search_20261020.json`: Santa Fe publica agosto, Córdoba devuelve HTTP 403, la página tributaria de ARBA enlaza informes antiguos, y la portada de Rentas Salta no ofrece un mes reciente verificable. No es una búsqueda exhaustiva en las 24 jurisdicciones.

Pendientes: 12 provincias hasta agosto (Buenos Aires, CABA, Chaco, Córdoba, La Rioja, Neuquén, Río Negro, San Juan, Santa Cruz, Santa Fe, Tierra del Fuego, Tucumán); La Pampa y Salta hasta julio. Antes de 2014 no se aplica un deflactor sin respaldo documentado.

# Gasto tributario y RIGI — 01/11/2026

## Alcance incorporado

Economía > Gasto tributario y RIGI, con enlace desde Panorama. Comparación principal 2025–2027 del cuadro 1 del Mensaje 2027, usando la misma publicación y las mismas definiciones. Se muestra el total, normas de impuestos, promoción y apertura de normas por impuesto. Selección de promoción: Tierra del Fuego, Economía del Conocimiento y fortalecimiento MiPyME, cuadro 3. Porcentajes redondeados conservados, sin forzar su suma.

El 2,34% de 2024 y el 3,45% revisado quedan como antecedentes de distintas publicaciones. No se presentan 1,33 puntos de diferencia con 2027 como nuevas dispensas. La Separata 2024 (1,47% del PIB) se identifica como subtotal ya incluido y no se traslada a 2027 por regla proporcional.

El costo fiscal RIGI 2027 conserva valor nulo y estado explícito: no cuantificado oficialmente en el Mensaje. Se incorporan los seis sectores del plan oficial, con Tecnología: suma sectorial 2026 USD 7.612 millones, 2027 USD 7.827 millones. Son planes, no inversión ejecutada. No se suman subsectores con redondeos distintos y no se convierte inversión en costo tributario mediante porcentajes arbitrarios. La guía de medición distingue Ganancias, IVA y aduana/exportaciones, y solicita costos por impuesto, proyecto y año junto a resultados.

## Informes

Las doce variantes generales incorporan dos páginas nuevas al final del cuerpo, antes del anexo: 23 páginas de cuerpo y 71 con anexo. Se agrega ficha temática específica de dos páginas, disponible en el módulo y en el selector de informes. Mismos insumos `nacion/data/tax-expenditures.json`, controlados por huella del contenido antes de descargar. El alcance propio (% del PIB y USD de planes) permanece independiente de los selectores del gasto presupuestario.

## Evidencia y validación

Originales oficiales y SHA-256: `nacion/data/tax-sources/sources.json`. El constructor `scripts_build_national_tax.py --check` verifica archivos, cifras de los cuadros, sumas, ausencia de estimación fiscal y planes extraídos del HTML oficial. No requiere red para reproducir el corte. Los originales se preservan con `-text`.

13 pruebas Python de informes y nueva fuente; 33 controles JavaScript de selección PDF, navegación, presupuesto y prioridades. Se verifican los textos nuevos en las doce variantes generales y la ficha. Revisión visual de las dos páginas; prueba funcional y descarga PDF a 390, 768 y 1440 píxeles, sin desbordamiento ni errores JavaScript. Selector de pesos/base no altera este módulo; fuentes oficiales enlazadas y números de página/autor conservados.

## Límites

No se obtuvo un costo fiscal oficial del RIGI ni se lo estimó sin bases por impuesto. No se construyó un puente causal 2024–2027 ni una desagregación exhaustiva de beneficiarios individuales. El documento evalúa estimaciones presupuestarias y planes, no certifica la ejecución de inversiones ni los resultados de cada incentivo.

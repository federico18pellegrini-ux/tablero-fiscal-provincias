# Tablero municipal: verificación del 7 de septiembre de 2026

## Alcance

Nueva ruta `/municipios/`, conectada al tablero provincial. Cinco vistas visibles: Panorama, Rankings, Recursos, Empleo y Simular. Mapa de 135 municipios con geometrías oficiales; selección persistente y enlaces directos. Diecinueve indicadores generales de ranking y tres indicadores fiscales con cobertura parcial explícita.

## Verificación de datos y cálculos

- 135 identificadores únicos y correspondencia completa con las geometrías.
- Transferencias mensuales, variaciones reales y descomposición de coparticipación reconciliadas para los 135 municipios.
- Las 41 coincidencias de caída de recursos y empleo usan el mismo período anual: 2025 frente a 2024.
- Los valores faltantes no entran como ceros ni reciben una posición. Los empates comparten puesto.
- La comparación por población toma municipios entre la mitad y el doble de habitantes del seleccionado, con población del Censo 2022.
- El simulador aplica una caída de 0% a 20% a la coparticipación bruta observada de enero a julio de 2026, en pesos de julio. Mantiene la participación municipal y los demás fondos constantes. No estima presupuesto ni caja libre.
- Las cuentas fiscales individuales cubren tres municipios al primer semestre de 2026. Se presenta esa muestra, sin extrapolar un ranking fiscal de los 135 municipios.
- Los eventos de Analytics distinguen las vistas municipales sin enviar el municipio seleccionado ni el valor de la simulación.

## Pruebas automáticas locales

- 76 pruebas Python aprobadas.
- 31 pruebas Node aprobadas, incluidas las seis nuevas de cálculos y cobertura municipal.
- Compilación Python y sintaxis del archivo JavaScript de publicación correctas.
- Trazabilidad TOP: 150 registros sin diferencias. Reclamos nacionales: 31 registros válidos.
- Los 24 informes provinciales conservan sus huellas de datos y PDF vigentes.

## Navegador

Se verificaron selección por mapa y por lista, ubicación y zoom, filtros de rankings, muestra fiscal, series de recursos y empleo, y extremos del simulador. La descarga efectiva de Pila se comprobó en disco: CSV UTF-8 con 22 indicadores y valores ausentes conservados como vacíos. El enlace desde el tablero provincial abre la nueva portada correctamente. Sin errores de consola en el recorrido revisado.

Revisión visual en escritorio y tamaños de 390 × 844, 768 × 1024, 320 × 740 y 1024 × 768. Se corrigieron el desborde del mapa al ampliar y las cifras largas en pantallas pequeñas. En los casos comprobados, el documento no requiere desplazamiento horizontal. Se agregó el resultado de la simulación junto al control para verlo durante el ajuste. Los tamaños son pruebas de navegador; no equivalen a pruebas en dispositivos físicos.

## Criterios de actualización

Los datos son una fotografía auditada, no una conexión automática a las fuentes. Cada indicador informa su período. La metodología y los enlaces públicos están disponibles en `municipios/metodologia.html`; el manifiesto conserva las huellas de los archivos de entrada. El generador recompone tanto los datos como el JavaScript de publicación.

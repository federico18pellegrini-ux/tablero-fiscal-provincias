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

## Ajuste de legibilidad móvil

La revisión posterior unifica explicaciones en 16 px, referencias y controles en 14 px, ejes en 13 px y encabezados de contexto en 12 px. Solo la navegación de pantallas menores a 360 px baja a 13 px para mantener visibles las cinco vistas. Las tarjetas y rankings redistribuyen su contenido antes de reducir la letra. Se comprobaron las cinco vistas a 320 px, la portada y Recursos a 390 px, y la portada a 768 px: sin desplazamiento horizontal ni desborde de cifras. Se revisaron capturas y tamaños efectivos del navegador. Los datos y cálculos permanecen iguales.


## Ampliación desde portales municipales

La cobertura fiscal pasa de 3 a 17 municipios con cierre en junio de 2026. Se incorporan General Las Heras, General Belgrano, Florencio Varela, General Alvear, Necochea, Chascomús, Olavarría, Tres Arroyos, Exaltación de la Cruz, Junín, Malvinas Argentinas, Lanús, Zárate y General San Martín. Tigre agrega ejecución presupuestaria separada, sin asignarle un resultado fiscal no homologado. Los otros 117 casos permanecen sin ejecución individual incorporada; no se afirma que sus municipios no publiquen datos.

Las transcripciones, fechas originales, alcance institucional, páginas, enlaces y huellas de los PDF quedan en `municipios/data/fiscal_verified.json`. Los originales descargados y las extracciones se conservan en la carpeta de investigación `outputs/municipios-fiscal-web-20260907` del espacio de trabajo, fuera del sitio. Los documentos fuente no son instrucciones para el tablero.

- Las 17 cuentas concilian ingresos corrientes más capital, gastos corrientes más capital y resultado financiero. El importador verifica centavos con Decimal antes de generar la publicación y rechaza cuentas inconsistentes, períodos distintos e identificadores repetidos.
- En General San Martín se reconstruye el resultado con dos ejecuciones por carácter económico. Se excluyen 28.491.663.843,39 pesos de aplicaciones financieras del total presupuestario de gastos. El resultado calculado es 14.367.303.346,81 pesos.
- Tres Arroyos conserva explícitamente la cobertura de administración central. No se sumaron los organismos descentralizados sin eliminar transferencias internas.
- Zárate se transcribe de la imagen del documento escaneado; se mantiene el inicio declarado del 5 de enero, igual que en Olavarría.
- En Tigre se verificaron los títulos dentro de los PDF, ya que los enlaces del portal están intercambiados. Se incorporaron los totales de recursos (página 13) y gastos (página 296). La diferencia devengado-pagado de 8.419.889.847,26 pesos se identifica como ejecución del período sin pagar, no como deuda total.
- Los seis indicadores fiscales abarcan resultado relativo y absoluto, capital sobre gasto, personal sobre gasto corriente, ahorro corriente relativo e inversión por habitante. La cobertura del ranking se calcula con los valores disponibles. Los faltantes no reciben ceros ni puestos.
- La ficha muestra barras de ingresos y gastos, resultado, capital y personal, con explicación del mecanismo fiscal. El acceso desde Panorama lleva directamente a las cuentas, debajo del encabezado fijo.

Validación local: 79 pruebas Python y 34 Node aprobadas; compilación y sintaxis correctas; controles de trazabilidad y reclamos sin diferencias; los 24 informes provinciales conservan sus huellas. Se verificaron las pantallas nuevas a 320, 390 y 768 px, sin desplazamiento horizontal ni tarjetas desbordadas; explicaciones de 16 px. Se revisaron Las Heras (superávit), Malvinas (déficit), Tigre (ejecución parcial), Zárate (fecha original) y La Matanza (faltante), y los rankings fiscales. Sin errores de consola en el recorrido. Son pruebas de navegador, no de dispositivos físicos.


## Separación del ranking general y la ficha municipal

El último botón de navegación se llama «Ranking general» y utiliza azul para distinguir la comparación provincial. Esa vista muestra un encabezado general y elimina la presentación duplicada que comenzaba con el nombre y la población del municipio. El selector superior se identifica como referencia, y una tarjeta explica su posición en el ranking con acceso a «Ver ficha municipal». Al volver a Panorama, Recursos, Empleo o Simular se recupera el encabezado individual. La descarga de datos municipales identifica el municipio para distinguirla de la descarga del ranking.

Se verificaron el enlace directo a densidad de empleo, cambios de referencia, comparación por población similar, regreso a la ficha y cobertura fiscal parcial. Revisión visual a 390 y 768 px; comprobación adicional de navegación y desbordes a 320 px. No hubo desbordes horizontales ni errores de consola. Pasaron 79 pruebas Python, 34 Node y los controles de publicación. Los datos e indicadores no cambian.

## Transparencia de ASAP y cuentas de La Matanza

Se incorporan las 270 observaciones publicadas por ASAP para los 135 municipios en noviembre de 2025 y mayo de 2026. El archivo `municipios/data/transparency_asap.json` conserva componentes, puntajes totales, páginas, ediciones, huellas de los documentos y el directorio de portales. El generador rechaza identificadores repetidos, cobertura incompleta, puntajes fuera de escala y totales que no concilien. El relevamiento de mayo (1 al 8) se distingue del corte posterior de las cuentas incorporadas al tablero.

La vista Ranking general suma el tema Transparencia, con puntaje y cambio entre ediciones. Los ceros son observaciones válidas y los 65 municipios con 100 comparten puesto. Las diferencias se expresan en puntos: 20 suben, 23 bajan y 92 conservan su puntaje. El filtro de población vuelve a calcular el universo y sus conteos. Panorama incorpora el mapa de transparencia y una sección desplegada con dos barras históricas y seis rubros, más acceso directo al ranking y a las cuentas. El índice no se interpreta como resultado fiscal ni calidad de gestión.

Se preservan dos salvedades del material original: General Viamonte tiene 100 puntos conforme a la corrección de ASAP; Morón conserva 15 puntos por presupuesto y 45 totales en noviembre de 2025 (p. 24), aunque los 15 no figuran en la escala metodológica. Esta excepción se comprobó visualmente, se admite solo para ese municipio y edición y se muestra en su ficha. La columna que el PDF de mayo titula «ene-26» se identifica por la fecha del informe y del relevamiento, no por ese error editorial. No se construyó una serie homogénea desde 2019.

La Matanza agrega su CAIF al 30 de junio de 2026, emitida el 7 de julio. Se verificaron visualmente la página 1, los ingresos y gastos de la CAIF y la columna devengado de personal. Ingresos: 383.274.207.057,99 pesos; gastos: 273.688.321.997,90; resultado: 109.585.885.060,09; personal: 58.753.633.542,65. No se usa el total presupuestario con operaciones financieras como gasto fiscal ni el resultado como caja libre. La cobertura pasa a 18 cuentas más la ejecución parcial de Tigre; los demás 116 conservan el faltante.

Pasaron 82 pruebas Python y 36 Node, compilación, sintaxis, trazabilidad TOP (150 registros sin diferencias), reclamos nacionales (31 registros) y vigencia de los 24 informes provinciales. Se comprobaron navegación entre ranking, transparencia y cuentas; filtro por población; mapa de 135 polígonos; ceros (Cañuelas), saldo histórico sin cambio (Las Heras), descenso con ejecución posterior (Tigre), excepción documental (Morón) y nueva cuenta fiscal (La Matanza).

Se revisaron capturas a 320, 390 y 768 px: sin desbordes horizontales en los casos comprobados, seis rubros visibles y texto explicativo de 16 px. El gráfico conserva la escala 0–100 y respeta la preferencia de movimiento reducido mediante la regla global. Descarga efectiva desde el botón: CSV UTF-8 con 135 municipios, cambios negativos y ceros preservados, unidad en puntos. Sin errores de página o consola en el recorrido. Son verificaciones de navegador, no pruebas sobre dispositivos físicos.

# Historia provincial y economía nacional

Verificación de fuentes: 6 de septiembre de 2026.

## Historia provincial

`data/fiscal_history.json`: 422 observaciones de ejecuciones de los últimos 12 meses, en 18 cortes (4T21–1T26). El explorador calcula cada componente sobre ingresos totales, incluida seguridad social. No convierte montos anuales a pesos constantes sin flujos mensuales. Personal, transferencias, capital, seguridad social y otros gastos explican el gasto primario; intereses se muestran aparte.

`data/debt_history.json`: 420 observaciones, de las páginas 21 y 23 de los 18 informes 1816 aportados por el titular. El importador `scripts_build_debt_history.py` requiere pdfplumber y recibe el directorio de los informes. Guarda la referencia y el hash de cada documento; no distribuye los PDF. Verifica componentes, unidades, filas y duplicados.

Los stocks hasta 2T24 están expresados en millones de ARS. Desde 3T24 están en millones de USD equivalentes al tipo de cambio oficial del cierre. El gráfico utiliza el cociente deuda / ingresos publicado por 1816; los montos originales permanecen en la tabla con su moneda. No se une una serie de pesos con una de dólares. El cociente no mide vencimientos ni liquidez. Los faltantes no se imputan.

## Fuentes nacionales

`data/national_management.json` contiene una fotografía revisada y referencias por bloque e indicador. No es una conexión en tiempo real. Mantiene el dato fiscal del SPN y agrega:

- Actividad: INDEC, EMAE junio 2026, publicado el 20/08. Historia completa enero 2004–junio 2026 (270 observaciones), serie desestacionalizada e índices originales. La versión de la serie y su hash están en el archivo.
- Inflación: índices nacionales INDEC ya auditados en `data/ipc_national_index.csv`, hasta julio 2026. Variaciones calculadas con índices sin redondear.
- Salarios: índice total INDEC junio 2026, publicado el 20/08. Variación real mensual estimada con la tasa nominal publicada (2,9%, redondeada) y el IPC del mismo mes. Se identifica explícitamente como cálculo aproximado.
- Empleo y desocupación: EPH 1T26, publicado el 22/06. Pobreza e indigencia: segundo semestre de 2025, publicado el 31/03. Universo: 31 aglomerados urbanos, no la población censal total.
- Comercio: INDEC, bienes, julio 2026; exportaciones, importaciones y saldo. El saldo de bienes no equivale a reservas.
- Reservas brutas, tipo de cambio mayorista y TAMAR privada: API BCRA v4, variables 1, 5 y 44. Cada una conserva su última fecha observada. La API anterior v3 devuelve 410 y no se utiliza.
- Deuda: Finanzas, informe mensual de julio 2026. Stock bruto de la Administración Central y pagos efectivamente realizados, con capital e intereses. Cobertura distinta del SPN; no se confunden pagos pasados con vencimientos futuros.

Para actualizar, conservar las fechas, unidades y coberturas de cada publicación; revisar sus revisiones y reconciliar las identidades. La fecha de revisión general no reemplaza el período del indicador ni acredita una actualización automática.

## Pendientes de información

Caja libre y calendario integrado de vencimientos a 30/90/365 días; composición real de subsidios, prestaciones y transferencias; y metas y resultados de servicios públicos. La interfaz los identifica como pendientes, sin pronósticos ni cifras sustitutas.

## Validación

46 pruebas: identidades fiscales y de deuda, historia y unidades, cobertura, última observación y salario real. Verificaciones adicionales de trazabilidad TOP (150 filas sin diferencias) y reclamos Nación (31 filas). Navegación histórica: 24 jurisdicciones por tres modos; 72 combinaciones sin errores. Revisión visual de escritorio y móvil (390 px), incluido el gráfico histórico de actividad.

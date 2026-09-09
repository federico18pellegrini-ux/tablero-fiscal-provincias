# Auditoría municipal — 9 de septiembre de 2026

## Resultado y alcance

Se revisaron las series y fórmulas publicadas para los 135 municipios, la evidencia fiscal, el mapa, las vistas, los rankings, las descargas y los PDF. No se detectaron diferencias numéricas en los controles realizados. Esto no certifica la integridad de la contabilidad interna municipal. Las pruebas provinciales de regresión aprobaron; no se realizó una nueva auditoría documental de las 24 jurisdicciones provinciales en esta tarea.

Resultado público: [auditoria.html](../municipios/auditoria.html). Inventario completo y nombres: [cobertura.html](../municipios/cobertura.html) y [CSV de los 135 municipios](../municipios/data/cobertura.csv).

## Cobertura

| Estado fiscal, sin duplicar municipios | Cantidad |
| --- | ---: |
| Comparable enero–junio de 2026 | 72 |
| Cuenta solo de otro período | 18 |
| Ejecución parcial: Tigre | 1 |
| Sin cuenta ni ejecución incorporada | 44 |

Ayacucho carece de personal devengado. Bragado tiene junio y agosto: el ranking utiliza junio. No se transforma ausencia en cero ni se mezclan cortes en el ranking. Faltan saldos bancarios de 2024 para 29 municipios, empleo industrial de diciembre de 2025 para cuatro y cambio industrial 2023–2025 para cinco. Chascomús y Lezama no tienen crecimiento poblacional homologado. Faltan además series comparables de caja libre, presupuesto vigente (Tigre solo tiene un total incorporado), ingresos y gastos fiscales mensuales, stock y calendario futuro de deuda del gobierno municipal. Los faltantes específicos y los sectores reservados figuran por municipio en el inventario.

## Evidencia y correcciones

- 70.783 comparaciones numéricas independientes de las series principales: ninguna diferencia.
- 5.516 comparaciones adicionales de salud, hacinamiento, SNIC, deuda CEC/FES, ASAP e IPC: ninguna diferencia. Total: 76.299.
- 92 registros fiscales principales y cinco componentes trimestrales adicionales; 100 PDF. Se contrastaron 720 importes por extracción, 48 por lectura visual de escaneos y tres totales derivados con sus componentes. Los períodos, coberturas institucionales y faltantes se preservan.
- 135 identificadores y geometrías confrontados con el archivo de origen.
- 125 archivos de respaldo actuales; 124 accesibles nuevamente y verificados. Exaltación de la Cruz no respondió: se conserva su PDF archivado. Bolívar y General Pueyrredon fueron recuperados por navegador y sus huellas coincidieron con las archivadas.
- 25 de Mayo: el enlace semestral devolvía 404. Se reemplazó por los PDF oficiales de Q1 y Q2. Sus ocho sumas coinciden al centavo con los importes anteriores. Se conserva la referencia retirada en `replacedEvidence`. Solo cambió la evidencia del municipio y su PDF; ningún valor numérico del dashboard se modificó.
- El CSV individual omitía los bloques sociales, de deuda personal y el detalle salarial. Se agregaron 43 filas de contexto y una por sector, conservando unidades, períodos, denominadores, referencias y valores ausentes.

## Deflactor

IPC nacional INDEC, 116 meses desde diciembre de 2016 hasta julio de 2026. `scripts_build_municipal_tools.py` toma la serie verificada `data/ipc_national_index.csv`, conserva su huella y comprueba la base contra `dashboard.json` y `ipc_source.json`. La modificación preexistente en `deflactor_mensual.csv` quedó excluida de esta implementación.

Comparador de seis variables, nominal/real, bases diciembre 2024, diciembre 2025 y julio 2026. Calculadora mensual sin extrapolaciones. Flujos ajustados por mes; saldos ajustados al cierre. Las cuentas fiscales semestrales no se deflactan sin apertura mensual. PBG conserva precios de 2004. Un único corte de deuda personal no produce una variación. Los controles del comparador no cambian las unidades explícitas del resto de la web ni de los PDF.

## Validación

- Python: 99 pruebas aprobadas. JavaScript: 50 aprobadas.
- Interfaz en celular/tablet: 540 vistas municipales y 108 combinaciones de ranking por tamaño; 20.574 comprobaciones en cada tamaño, sin errores.
- Comparador en 320 y 768 px: 540 combinaciones por tamaño y 3.361 comprobaciones por tamaño, sin errores.
- CSV: 135 municipios + 27 rankings; 7.737 comprobaciones, sin errores. Se verifica contenido generado y preservación de faltantes. El navegador automatizado canceló el guardado nativo; no se afirma que se haya guardado un archivo mediante esa herramienta.
- 135 informes, 1.216 páginas; control geométrico sin contenido fuera de márgenes. Revisión visual del PDF modificado de 25 de Mayo y de los controles/páginas en celular.

La evidencia de ejecución, archivos de origen y resultados JSON permanecen en `outputs/municipios-auditoria-20260909` del espacio de trabajo. La verificación pública se realiza después de publicar y se conserva allí; las pruebas locales no se presentan como evidencia de despliegue.

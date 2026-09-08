# Auditoría de datos del tablero municipal

**Federico Pellegrini · 7 de septiembre de 2026**

## Resultado

No detectamos diferencias en los importes recalculados del tablero municipal ni en el ajuste por inflación. Los datos publicados coinciden con los archivos originales revisados y las cuentas fiscales concilian. Corregimos dos debilidades de la carga y una omisión en el contenido de la exportación de Tigre.

El límite más importante es la cobertura: **el ranking fiscal reúne 72 municipios con cierre en junio de 2026. No alcanza para identificar el mayor déficit de los 135 municipios.** Además, compartir fecha de cierre no implica que todas las cuentas incluyan los mismos organismos y servicios.

Esta revisión comprende el módulo **Municipios de la provincia de Buenos Aires**: Panorama, Recursos, Empleo, Simular y Ranking general. Los controles existentes del tablero provincial y sus 24 informes también pasaron, pero eso no sustituye una nueva revisión documental integral de ese otro módulo.

## Qué verificamos

| Bloque | Verificación | Resultado |
|---|---|---|
| Transferencias y coparticipación | Archivos originales, componentes, totales provinciales, importes mensuales, participación municipal y valores por habitante | Sin diferencias detectadas |
| Inflación y pesos constantes | 116 observaciones del IPC; ajuste mensual antes de sumar; comparación de períodos equivalentes | Cálculo correcto |
| Empleo y salarios | Series mensuales originales, promedios, variaciones, puestos por habitante y masa salarial aproximada | Sin diferencias detectadas |
| Actividad, industria y banca | PBG, empleo por sector, sucursales, préstamos y depósitos; unidades y datos reservados | Sin diferencias detectadas |
| Población y carencias | Población censal, superficie, hogares con NBI y denominadores | Sin diferencias detectadas |
| Cuentas fiscales | 91 observaciones fiscales y una ejecución presupuestaria; 99 PDF; ingresos, gastos, resultado, personal y períodos | Las identidades concilian; sin diferencias detectadas en la revisión documental |
| Transparencia | Dos ediciones de ASAP, 135 municipios por edición, seis componentes y puntaje total | 1.890 comprobaciones sin diferencias |
| Mapa | Descarga vigente de Georef, códigos, límites y validez de las geometrías | Los 135 partidos coinciden con la cartografía original |
| Rankings y pantallas | 27 indicadores, orden ascendente y descendente, empates, población similar, faltantes, colores y simulación | Sin errores en el recorrido automatizado a 390 y 768 píxeles |

La revisión independiente de las planillas originales acumuló **70.783 comprobaciones numéricas**. No son 70.783 fuentes distintas: incluyen celdas, fórmulas, períodos y conciliaciones. Se volvieron a obtener **111 archivos de origen** y todos coincidieron por contenido con los originales conservados. La cartografía se verificó por separado.

En los PDF fiscales, 712 importes coincidieron con la extracción de las páginas relevantes. Otros 48 importes de seis documentos escaneados o con extracción defectuosa se comprobaron visualmente. Tres totales de General San Martín se verificaron mediante sus componentes. Se revisaron también las sumas trimestrales y los cortes originales; no se proyectaron meses faltantes.

## Correcciones realizadas

1. **Unificamos el respaldo de las 72 cuentas del semestre.** Trenque Lauquen, General Rodríguez y Carmen de Areco todavía entraban por una carga inicial. Sus importes eran correctos. Ahora pasan por el mismo registro de documentos, páginas, fechas y huellas digitales que el resto.
2. **Impedimos que una cuenta retirada sobreviva a una actualización.** La reconstrucción elimina los registros anteriores antes de aplicar el registro verificado. También rechaza cuentas sin respaldo documental válido.
3. **Completamos el contenido del CSV de Tigre.** Incorpora presupuesto vigente, recursos cobrados, gastos devengados, gastos pagados y obligaciones del período aún no pagadas. Conserva sus fechas y unidades, sin convertir esos totales presupuestarios en un resultado fiscal.

Los importes del tablero y las posiciones de los rankings se mantienen. La corrección fortalece la trazabilidad y completa la exportación.

## Cómo interpretar los pesos

Las transferencias comparan enero–julio de 2026 con enero–julio de 2025. Para descontar inflación, cada importe mensual se multiplica por el IPC de julio de 2026 y se divide por el IPC de su propio mes. Después se suman los meses. Así se evita tratar un peso de enero como si tuviera el mismo poder de compra que uno de julio.

Los salarios reales también se ajustan mes a mes. La masa salarial es una aproximación construida con empleo y remuneración media; no mide ventas locales. Los saldos financieros se ajustan al cierre correspondiente. El PBG utiliza la serie oficial a precios constantes de 2004: no se vuelve a ajustar como si fuera una serie nominal.

**Las cuentas fiscales están en pesos corrientes.** Sus ingresos y gastos pertenecen al mismo período y el tablero lo aclara. El resultado es recursos percibidos menos gastos devengados, excluyendo fuentes y aplicaciones financieras. Un superávit no permite afirmar que ese dinero esté libre para gastar.

## Cobertura y límites para la lectura política

| Situación fiscal incorporada | Municipios |
|---|---:|
| Cuenta con cierre en junio de 2026 | 72 |
| Cuenta disponible solamente para otro corte | 18 |
| Ejecución presupuestaria parcial, sin resultado fiscal homologado: Tigre | 1 |
| Sin cuenta fiscal incorporada y verificada | 44 |
| Total | 135 |

Bragado tiene junio y agosto: el ranking usa junio y la ficha conserva ambos. Por eso existen 19 observaciones de otros períodos, aunque solamente 18 municipios dependan exclusivamente de esos otros cortes. El gasto en personal cubre 71 municipios del semestre: en Ayacucho falta el desglose del primer trimestre y se mantiene sin dato.

- **Fecha común no equivale a cobertura institucional idéntica.** La administración central, los hospitales, los entes y los servicios prestados pueden diferir. Esto afecta especialmente las comparaciones de personal, inversión y resultado.
- **Por habitante significa por habitante censado en 2022.** No es una estimación de la población de 2026. Chascomús y Lezama quedan fuera de la variación intercensal hasta homologar la separación territorial.
- **Empleo formal no es desempleo.** Los puestos se asignan por establecimiento y pueden estar ocupados por personas que viven en otro municipio. El último corte incorporado es diciembre de 2025.
- **Actividad no equivale a coyuntura de 2026.** El PBG incorporado llega a 2023; la información bancaria utilizada llega a 2024. Cada indicador conserva su período.
- **ASAP mide publicación y acceso a información.** No mide solvencia ni calidad de gobierno. Se conservan las salvedades documentadas de Morón y General Viamonte.
- **El simulador es un escenario proporcional.** Aplica una caída de hasta 20% a la coparticipación bruta observada, manteniendo la participación municipal y los demás fondos. No demuestra que una caída de la recaudación propia provincial se traslade automáticamente en igual porcentaje a cada municipio.
- **La ausencia de una cuenta incorporada no demuestra que el municipio no publique información.** Describe lo recuperado y verificado en las páginas recorridas.

Recomendamos utilizar los rankings como punto de partida para el análisis. Antes de sostener una conclusión sobre desempeño de gestión, hay que considerar el período, la cobertura institucional y los servicios a cargo. Para extender el ranking fiscal a los 135, faltan cuentas homologadas de junio en 63 municipios, incluidos quienes hoy tienen otro corte o información presupuestaria parcial.

## Evidencia y límites de la verificación

Se recorrieron las cuatro vistas individuales de los 135 municipios y 108 combinaciones de rankings en cada uno de los dos tamaños de pantalla. Son pruebas en navegador con dimensiones simuladas, no en dispositivos físicos. Se comprobaron los contenidos generados por los 135 CSV municipales y los 27 CSV de ranking: 7.737 verificaciones, sin diferencias. **La entrega del archivo al disco no quedó validada en esta corrida:** el navegador de prueba canceló las descargas tanto en la versión local como en el sitio publicado. Esto queda separado de la validación del contenido de los CSV.

Los enlaces directos de Tandil y Exaltación de la Cruz dependen de sesiones o tokens temporales. Bolívar y General Pueyrredon también requirieron entrar desde el portal para recuperar sus documentos. Se accedió por las páginas públicas y se confirmó el mismo contenido en los cuatro casos. Para repetir la revisión conviene usar el portal de entrada, no conservar únicamente una dirección temporal.

Pasaron 90 pruebas Python, 41 pruebas JavaScript y los controles de trazabilidad, reclamos nacionales y vigencia de los 24 informes provinciales. Los documentos, extracciones, comprobaciones independientes y capturas quedan conservados en la carpeta local de esta auditoría.

Esta revisión verifica la correspondencia con los documentos publicados y la consistencia de los cálculos. No reemplaza una auditoría contable sobre los registros internos de cada municipio ni certifica operaciones que los documentos no muestran. La base es una fotografía con fechas explícitas; no se actualiza automáticamente por la publicación de un nuevo informe municipal.

## Referencias

- [Tablero municipal y criterios de medición](https://tablero.federicopellegrini.com.ar/municipios/metodologia.html).
- [Registro de cuentas verificadas, períodos y documentos originales](https://tablero.federicopellegrini.com.ar/municipios/data/fiscal_verified.json).
- [Estado de revisión de los 135 portales](https://tablero.federicopellegrini.com.ar/municipios/data/revision_portales.csv).
- [Archivos originales y huellas de contenido](https://tablero.federicopellegrini.com.ar/municipios/data/fuentes.csv).
- [OEDE: estadísticas provinciales y departamentales](https://www.argentina.gob.ar/trabajo/estadisticas/oede-estadisticas-provinciales).
- [ASAP: cumplimiento de municipios](https://www.asap.org.ar/informes-detalle/cumplimiento-municipios/8).
- [Georef: descarga de la base completa](https://www.argentina.gob.ar/georef/descarga-de-la-base-completa).

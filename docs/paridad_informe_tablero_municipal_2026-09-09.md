# Informe municipal y tablero: revisión de contenido

Se comparó el generador vigente de los 135 informes con las vistas de la web. Salud, hacinamiento, seguridad, NBI, deuda personal, salarios brutos y las explicaciones del IPC ya estaban publicados. Había detalles visibles en el PDF o en el CSV que todavía no se mostraban completos en las vistas individuales.

| Contenido del informe | Dónde se consulta en el tablero | Resultado de esta revisión |
| --- | --- | --- |
| Lectura central y tres prioridades | Panorama | Las prioridades ahora explican por qué se eligen y qué se recomienda, según los datos de cada municipio. |
| Ingresos, gastos y resultado fiscal | Recursos | Se agregan componentes corrientes y de capital, ahorro corriente, saldo de capital y gasto de capital por habitante. Se mantienen los distintos cierres y el caso parcial de Tigre. |
| Transferencias y coparticipación | Recursos | Ya estaban los montos, variaciones, gráficos, descomposición y comparador nominal/real. |
| Empleo de 2023, 2024 y 2025 | Empleo | Se agrega el cuadro con promedio anual y puestos en diciembre. El gráfico conserva la historia desde 2019. |
| Sectores del empleo | Empleo | Se agrega la participación de cada sector en el total y se corrigen sus nombres visibles. Los sectores reservados siguen sin dato. |
| Salarios de 2023–2025 y noviembre/diciembre de 2025 | Empleo | Se muestran todos los valores brutos nominales y ajustados que figuran en los cuadros del PDF. Se explican promedio, mediana y pagos estacionales. |
| Producto municipal 2021–2023 | Empleo | Se agregan los niveles de los tres años a precios de 2004, junto con la explicación y su origen. |
| Sucursales, préstamos y depósitos | Empleo / Recursos | Se muestran sucursales y relación préstamos/depósitos en Empleo, con acceso directo al comparador de saldos 2023–2024 en Recursos. |
| Deudas de las personas | Empleo | Ya estaban los siete indicadores del informe y sus denominadores y límites. |
| Población, hogares, NBI, salud, vivienda y seguridad | Panorama | Se completan hogares, hogares con NBI, superficie, densidad y cambio poblacional. Salud y delitos ya estaban. |

La web adapta la narración a la lectura en pantalla; no reproduce cada párrafo del PDF. Los datos y las explicaciones centrales quedan dentro de sus secciones, desplegados. No se agregan de nuevo al PDF las secciones que el usuario había excluido.

## Verificación

- Se contrastaron 3.830 valores nuevos en pantalla, su formato y su tratamiento de faltantes y negativos para los 135 municipios y 91 cuentas fiscales: 13.516 comprobaciones, sin diferencias.
- Se descargó el PDF público de General Las Heras, se verificó su huella y se compararon sus 13 valores de los cuadros salariales y de producto con la web.
- Se verificaron 21 vistas de siete municipios en 320 y 768 píxeles: 486 comprobaciones por tamaño, sin errores. Incluye cuentas comparables, otro período, dos cierres, ejecución parcial, ausencia de cuenta y crecimiento poblacional sin homologar.
- Se revisó visualmente la lectura en celular de salarios y prioridades y en tablet del desglose fiscal. Los negativos conservan el color rojo y las tablas no requieren desplazamiento horizontal.
- Aprobaron las 50 pruebas JavaScript del proyecto. La publicación debe superar también el flujo completo de validación de CI.
- No se modifican datos de origen, cálculos económicos, archivos PDF ni su manifiesto. La modificación preexistente en `deflactor_mensual.csv` queda fuera de este cambio.

Evidencia de ejecución: `outputs/municipal-parity-20260909` del espacio de trabajo. La comprobación pública se guarda después del despliegue.

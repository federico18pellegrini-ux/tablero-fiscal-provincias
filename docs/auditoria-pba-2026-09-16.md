# Auditoría de Buenos Aires y presentación provincial

Revisión del 15–16 de septiembre de 2026. Alcance: datos de Buenos Aires, coherencia entre web y PDF, cálculos compartidos y presentación de las once vistas provinciales. Los indicadores conservan períodos distintos; el ranking usa un corte común.

## Actualizaciones y conciliación

| Bloque | Resultado | Evidencia y criterio |
|---|---|---|
| Ejecución 2026 | Incorporado enero–junio: ingresos $20.743.442 millones, gasto $21.619.499 millones, déficit $876.057 millones, 4,22% de ingresos | [PBA, segundo trimestre, página 13](https://www.ec.gba.gov.ar/areas/hacienda/Presupuesto/ejecucion_presupuestaria/Ejecuci%C3%B3n%20Presupuestaria%20II%20trim%202026.pdf). Son seis meses acumulados, no el segundo trimestre aislado. |
| Deuda | Stock al 30/06/2026: $17.950.608,4 millones. Deuda/recursos: 45,5%. Moneda extranjera pagadera en divisas: 79,2% | [Informe PBA de junio, cuadros de stock y perfil](https://www.ec.gba.gov.ar/areas/finanzas/deuda/archivos/Informe%20de%20Deuda%20PBA%20al%2030-Jun-2026.pdf). Ratios oficiales del mismo corte. |
| Vencimientos | Reemplazada la proyección de diciembre por junio. Primera barra: julio–diciembre de 2026. Pico anual: 2027 | Mismo informe; importes de capital, intereses y total conservados, incluidos redondeos de hasta $1 millón. |
| Ranking | Se conserva marzo: deuda/ingresos 45,23%, puesto 23 de 23 | No se divide el stock de junio por los ingresos usados para marzo. La Pampa continúa sin posición comparable. |
| Cierre 2025 | Los 16 campos APNF de PBA coinciden con la planilla oficial descargada nuevamente | [DNAP, serie APNF 2025](https://www.argentina.gob.ar/sites/default/files/serie_aif-apnf-2025.xlsx). Déficit $2.049.562,65 millones. |
| Presupuesto | Presupuesto inicial 2026 sin cambios; gasto $43,02 billones | No equivale al crédito vigente. El reporte semestral no permite completar ese faltante. |
| Recaudación propia | PBA hasta julio: $9,82 billones acumulados | [TOP mensual oficial](https://www.argentina.gob.ar/sites/default/files/top_mensual_2026_16.xlsx). Total conciliado con sus cinco componentes. Las otras provincias conservan sus propios cortes. |
| Recursos nacionales | Hasta agosto: $11,66 billones acumulados; −0,9% real interanual | [RON oficial](https://www.argentina.gob.ar/sites/default/files/informacion_consolidada_2026_5.xlsx). Se compara enero–agosto contra enero–agosto, deflactando cada mes. |
| Serie histórica propia | Agregado PBA 2025: $14.036.638,5 millones | [TOP 1984–2025](https://www.argentina.gob.ar/sites/default/files/serie_top_1984_2025_0.xlsx). Las seis celdas de 2024 coinciden con la serie previa; las cinco categorías suman el total 2025. Las demás provincias no se reimportaron en esta ampliación. |
| Inflación | IPC nacional hasta agosto de 2026 | [INDEC](https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_09_26.xls). Se mantiene la base provincial junio y municipal julio; actualizar el índice no cambia automáticamente la base. |
| Deuda de Nación | Se mantiene el reclamo provincial publicado por $19,1 billones el 14/09 | [Gobierno PBA](https://gba.gob.ar/gobierno/noticias/bianco_%E2%80%9Cla_situaci%C3%B3n_econ%C3%B3mica_productiva_y_social_en_argentina_es_asfixiante%E2%80%9D). Componentes: $4,7 directas, $10,1 obras y $4,3 programas. Atribución visible: según la Provincia. |
| Escuelas | 317 edificios: 112 creaciones y 205 sustituciones | [Registro provincial](https://catalogo.datos.gba.gob.ar/dataset/nuevos-edificios-escolares), actualización 09/09. Son edificios acumulados, no obras ejecutadas sólo en 2026. |
| Seguridad | Se confirman 775 víctimas y tasa 4,442948 cada 100.000 en 2025 | API oficial SNIC consultada nuevamente; caída de 5,55% frente a 2024. |
| Matrícula | Se confirman 5.001.493 estudiantes y 21.519 unidades de servicio en 2025 | Catálogo y CSV DGCyE vigentes: último año publicado 2025. |
| Salud, aprendizaje y carencias | Se mantienen sus cortes: actividad sanitaria 2024, Aprender 2024, mortalidad infantil 2024, NBI 2022 | Comprobadas disponibilidad de fuentes y consistencia de las series cargadas. El catálogo sanitario sigue publicando 2024 como último año. No se presentan estos datos como mediciones de 2026. |

## Correcciones de lectura

- Eliminada la resta de servicios de deuda a un margen fiscal calculado con otro período. Ese resultado no demostraba disponibilidad de caja.
- Los acumulados destacados muestran su último mes disponible. Los cálculos que combinan ingresos propios y nacionales mantienen meses comunes.
- Los servicios de deuda históricos siguen separados de los vencimientos futuros documentados.
- Resúmenes breves por perfil; menos reiteraciones y tablas duplicadas. Se mantienen fechas, unidades, atribución y evidencia en los archivos de datos y metodología.
- Tipografía de lectura de 16 px y referencias/tablas de 14 px; corregido el ancho de las tarjetas federales en celular y aumentada la letra de los gráficos.
- Los 24 PDF conservan tres páginas, con más espacio, textos más cortos, enlace al tablero, nombre y número de página. Buenos Aires incluye semestre y deuda actualizados.

## Verificación

- 123 pruebas de Python y 77 de JavaScript.
- 179 totales mensuales TOP conciliados, sin diferencias.
- Cálculos de deuda, identidad ingreso menos gasto y deflación mensual contrastados; faltantes preservados como faltantes.
- 24 informes de tres páginas, 72 páginas renderizadas; texto dentro del área de página y revisión visual de composiciones.
- Informes municipales y cobertura de 135 municipios siguen vigentes; sólo se amplió la disponibilidad del IPC compartido.
- Verificación de navegación y lecturas en las 24 jurisdicciones y los tres perfiles; tamaños de celular, tablet y escritorio.

## Faltantes que no se pueden completar con estos documentos

Caja libre conciliada, presupuesto vigente con sus modificaciones y calendario mensual futuro para calcular vencimientos a 30/90/180 días. El presupuesto inicial, los saldos contables y una proyección anual no sustituyen esos datos.

La auditoría revisa los datos publicados y sus cálculos; no certifica cuentas de Tesorería ni presupone actualizaciones de fuentes que todavía no publicaron un período nuevo.

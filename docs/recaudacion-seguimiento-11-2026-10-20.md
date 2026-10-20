# Seguimiento de las once jurisdicciones — 20/10/2026

Incorporados seis meses: Chaco septiembre; Río Negro septiembre; La Rioja septiembre; Salta agosto y septiembre; La Pampa agosto. Se preserva el perímetro tributario DNAP y se conservan originales, URL y SHA-256 en data/provincial_recent_sources_review.json.

## Corrección del diagnóstico anterior
Salta no carecía de publicaciones: el acceso directo a la ruta anual falla, pero desde el índice de Estadísticas se accede a 2026 y a los PDF mensuales. El dominio api-test2.dgrsalta.gov.ar es el servidor de archivos enlazado por la página pública DGR. No se usó información de prueba ajena al portal.

## Conciliación
- Chaco: servicio público /verMontoNuevo?mes=9&anio=2026 identificado en el HTML. Total visible 54.928.545.250,76; subtotal comparable 49.647.427.929,12. Se excluyen recargos/intereses y corresponsabilidad gremial, que tampoco integran la serie DNAP de agosto. Otros se construye con los mismos cuatro componentes que reconcilian agosto exactamente.
- Río Negro: PDF de una página con imagen. Transcripción visual; total septiembre 81.165.178.752,70. Los cinco conceptos de agosto concilian con DNAP.
- La Rioja: cuatro impuestos, suma 17.346.453.062,33; coincide con total publicado. No se crea un rubro Otros en cero.
- Salta: subtotal tributario 82.325.496.441,11 en agosto y 81.832.989.100,03 en septiembre. Excluye tasa de justicia y multas. Agosto presenta puntuación defectuosa en inmobiliario: 82.611.225,12 reconcilia el subtotal. Otros agosto es cero expresamente publicado, no faltante imputado.
- La Pampa: agosto 50.753.032.618,22. Otros respeta la combinación de rubros que concilia con DNAP en julio; no se incorpora el agregado contable de tasas como si fuera todo tributario comparable. No incluye recursos nacionales ni regalías.

## Pendientes revisados
- La Pampa: portal de Transparencia remite a Contaduría, Informes de Recursos Mensuales 2026. Último enlace agosto; falta septiembre.
- Córdoba: Economía, portal provincial y Prensa devuelven 403; también se comprobó en navegador. La nota periodística sobre septiembre no permite reconstruir montos tributarios. Conserva agosto.
- Buenos Aires: planilla oficial Recaudación Provincial 2026_Prensa.xlsx descargada; septiembre vacío (fórmulas con cero no son observaciones). Conserva agosto.
- CABA: planilla SP_IP_Reca_concepto.xlsx descargada; última fila agosto.
- Santa Fe: página oficial Recaudación 2026 y acumulado hasta agosto.
- Santa Cruz: ASIP mantiene septiembre vacío y agosto como último importe.
- Tierra del Fuego: AREF devuelve 403; búsqueda indexada no recuperó septiembre tributario verificable.

Fuentes: https://atp.chaco.gob.ar/recaudacion ; https://agencia.rionegro.gov.ar/?contID=60047 ; https://www.dgrsalta.gov.ar/Inicio/OtrasGestiones/Estadisticas ; https://contaduriageneral.lapampa.gob.ar/ejecucion-presupuestaria/ano-2026/informe-de-recursos-mensual ; https://www.gba.gob.ar/economia/direccion_provincial_de_politica_tributaria/recaudacion_provincial ; https://www.asip.gob.ar/recaudacion/ . Los enlaces de archivos individuales están en el registro de fuentes.

Alcance: búsqueda de los meses pendientes, no auditoría integral de todos los registros históricos. Quedan siete jurisdicciones sin septiembre, todas ahora con enero-agosto.

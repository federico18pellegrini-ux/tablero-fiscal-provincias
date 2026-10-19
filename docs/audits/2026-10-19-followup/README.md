# Seguimiento de pendientes · 19/10/2026

## Incorporaciones verificadas

- Neuquén: seis informes de recaudación provincial (abril, mayo y junio de 2025 y 2026), originales archivados con SHA-256. Totales nominales 406.801 y 595.880 millones. Ajuste de cada mes por IPC nacional observado: +10,0794% real, presentado como aproximadamente 10,1% por redondeo de origen y carácter provisorio. No reproduce el -228,4% de la fuente recibida. No se reemplaza la cobertura APNF por esta serie provincial.
- La Pampa: compromisos de junio y agosto de 2026, por clasificación económica. Corriente, capital, contribuciones figurativas y aplicaciones financieras suman el total publicado. El cuadro por jurisdicción corrobora el total. Son meses aislados y etapa compromiso, no devengado: no se incorporan al ranking APNF ni se calcula resultado con la recaudación tributaria parcial. El informe provincial y la sección de ingresos muestran estas observaciones separadas.
- San Miguel: apertura documentada de fuentes financieras (1.065.321.903,89 pesos), cancelación de cuentas a pagar (16.647.521.570,98) y adelantos a proveedores (5.266.544.986,17). Se muestra en ficha y detalle fiscal del PDF completo. Falta conciliar corriente/capital, incluyendo insumos de obras. Sigue excluido del ranking semestral; el documento corresponde a enero-marzo.

## Municipios sin cuenta completa nueva

Se revisaron nuevamente los 13 portales listados en `portal-checks.json`, búsquedas indexadas y referencias oficiales alternativas. No constituye una conciliación exhaustiva de todos los documentos municipales.

Cañuelas; Esteban Echeverría; General Arenales; General Paz; Hurlingham; La Costa; Leandro N. Alem; Lomas de Zamora; Mar Chiquita; Merlo; Pila; Punta Indio; Tordillo.

- General Arenales: redirección inválida a 0.0.0.0.
- Lomas de Zamora: error de certificado en el portal. El Concejo es accesible; lo localizado no aporta la ejecución buscada.
- Tordillo: portal recuperado; transparencia ofrece ordenanzas fiscal/impositiva, no cuenta de ejecución.
- General Paz: el Concejo confirma el presupuesto original de 17.792.227.114,79 pesos, ya cargado. No es un dato nuevo ni una ejecución. La página municipal de transparencia continúa sin una cuenta utilizable.
- Los restantes enlaces no aportaron una ejecución nueva verificable. Noticias sobre aprobación de rendiciones no reemplazan las planillas.

## Parciales que continúan

- General Pinto: enero-septiembre, 64 páginas por programa hasta inciso. Faltan aperturas económicas verificables de transferencias y servicios de deuda; no se asigna todo el inciso 7 a gasto fiscal ni todo el inciso 5 a corriente.
- Roque Pérez: abril-junio aislado, 260 páginas. Sigue pendiente clasificación económica y conciliación con enero-marzo antes de armar el semestre. Los saldos de disponibilidades no se tratan como ingresos nuevos.
- San Miguel: apertura financiera ampliada, pero cuenta económica aún incompleta. No se atribuye un superávit a la diferencia bruta.

Cobertura conservada: 84 cuentas comparables del primer semestre; 35 municipios adicionales con otro período; 3 ejecuciones parciales; 13 sin ejecución verificada. No se completan faltantes con ceros.

## Otros límites

La Pampa sigue sin cierre APNF comparable. Se localizó además la cuenta de inversión 2025; no se incorporó sin conciliar organismos y etapas. Neuquén publica un informe rotulado septiembre cuyo resumen dice agosto y usa IPC estimado: no se actualizó automáticamente la serie mensual con ese documento ambiguo.

## Validación

175 pruebas Python existentes y 2 nuevas; 151 pruebas JavaScript. Validación de PDF provinciales y municipales contra los mismos datos. Inspección visual de páginas afectadas de Neuquén, La Pampa y San Miguel. Pruebas por muestra, no certificación de cada registro contra cada original.

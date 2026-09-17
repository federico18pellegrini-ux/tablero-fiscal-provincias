# Presupuesto Nacional

Página estática `/nacion/`, integrada al sitio existente. Sin framework, servicios nuevos ni claves. HTML, CSS, JavaScript y datos normalizados; tipografías alojadas localmente con licencia OFL.

## Ejecutar y verificar

Desde la raíz: `python -m http.server 8765 --bind 127.0.0.1`. Abrir `http://127.0.0.1:8765/nacion/`.

Pruebas: `node --test tests/national_budget.test.cjs tests/analytics.test.cjs`.

## Informe editorial en PDF

El botón **Informe PDF** está disponible en las cinco vistas y en Metodología. Abre un diálogo accesible que toma los precios y la base de comparación del tablero; permite cambiarlos antes de descargar. El informe siempre cubre todo el país: los filtros locales de obras/programas no recortan el documento.

- Informe principal: 10 páginas, con lectura editorial, prioridades, organismos, funciones, programas, territorio, recursos/supuestos macro, ejecución, historia y metodología.
- Anexo opcional: todas las 394 filas programáticas, 435 partidas de proyectos y ejecución mensual de las 16 jurisdicciones más el total. Con el informe: 56 páginas.
- Seis combinaciones: pesos corrientes/constantes y base inicial/vigente/cierre estimado. Fuentes, autor, enlace público y numeración en cada página; fuentes originales enlazadas al final.
- Redacción propia, vinculada a las cifras y a la base seleccionada. No requiere llamar a un servicio de IA ni enviar datos o preferencias a terceros al exportar.
- Los porcentajes de ejecución son nominales; septiembre real queda sin dato. Los cierres estimados no se inventan para programas. Los números negativos son rojos.

Generación: `python scripts_export_national_reports.py`. Comprobación de vigencia: `python scripts_export_national_reports.py --check`. El catálogo guarda hashes de fuentes, generador, tipografías y PDF. CI exige regenerar ante cambios, y el navegador verifica que el catálogo corresponda exactamente al JSON que está mostrando antes de ofrecer una descarga.

Pruebas: `python -m unittest discover -s tests -p test_national_reports.py` y `node --test tests/national_report.test.cjs`. Los PDF son texto y gráficos vectoriales, no capturas de la web.

Para reconstruir (dependencias en `requirements-national-budget.txt`):

```
python -m pip install -r requirements-national-budget.txt
python scripts_fetch_national_budget.py --cache ../presupuesto-nacional-20260917
python scripts_build_national_budget.py --cache ../presupuesto-nacional-20260917
```

El registro `data/sources.json` fija URL oficial, fecha de recuperación, tamaño y SHA-256. El importador exige esos bytes: si el sitio oficial actualiza el recurso, requiere revisar la nueva versión o utilizar la copia archivada. No actualiza silenciosamente el corte. Los originales de esta versión están conservados en la carpeta de trabajo indicada arriba.

## Cobertura y conciliación

- Proyecto de ley 2027 de la ONP: 202.101.433 millones de pesos. Es una propuesta, no una ley sancionada ni ejecución.
- 15 jurisdicciones del proyecto; 16 en Presupuesto Abierto 2026. No se interpreta la ausencia de una jurisdicción como un gasto cero.
- 5 finalidades y 29 funciones. Los 13 temas editoriales particionan las funciones sin duplicarlas.
- 28 ubicaciones del proyecto: 24 jurisdicciones, Nacional, Interprovincial, Binacional y Exterior. El código 99 de PA dice «No Clasificado» y no se equipara a Exterior.
- 394 filas programáticas con página de origen. Dos filas se llaman Revisión de Cuentas Nacionales; se preservan por separado. No se afirma que el número de filas sea el de políticas nuevas o programas institucionalmente únicos.
- 356 cruces por nombre normalizado, entidad y jurisdicción con PA 2026; 38 quedan sin comparación. Las coincidencias ambiguas se rechazan. No se trasladan funciones 2026 a programas 2027.
- 435 partidas geográficas de proyectos de inversión. Pueden incluir equipamiento y una obra distribuida en más de una ubicación. No son 435 obras físicamente distintas. Buenos Aires: 72 partidas; total oficial 321.085 millones.
- Recursos corrientes y de capital: 202.348.174 millones. No se confunden con el total consolidado del Mensaje, que excluye rentas del FGS/BCRA.
- PA 15/09/2026: inicial 148.069.293,526549; vigente 152.474.968,840416; devengado 105.365.152,015092 millones. Conciliados contra descarga independiente de totales y contra flujos mensuales por jurisdicción.
- La base «cierre estimado» es la de los cuadros comparativos oficiales: 161.428.086 millones de gasto. No es el vigente. Se conserva el mismo alcance con intereses intra-Administración Nacional.
- Serie devengada 2023–2025 de Presupuesto Abierto, vigente 2026 y proyecto 2027 con sus etapas identificadas.

El JSON incluye resultados de conciliación. Diferencias por redondeo del PDF: programas +1 millón; obras +6 millones; finalidades y jurisdicciones −1 millón. Las funciones y ubicaciones concilian exactamente. La tolerancia máxima es medio millón por fila publicada.

## Precios, porcentajes y unidades

Todo monto en el JSON está en **ARS millones**. Las series históricas originales están en pesos: se dividen por 1.000.000. Un billón argentino es 10^12 pesos. bill. = billones; M = millones en las etiquetas breves.

Modo constante: base agosto 2026. IPC INDEC observado hasta agosto; proyección propia de septiembre–diciembre compatible con 29% diciembre/diciembre 2026 y doce tasas mensuales iguales compatibles con 18% en 2027, según supuestos ONP. Se usa IPC **promedio anual** para presupuestos anuales. Los períodos históricos usan los doce IPC observados. La senda mensual proyectada no es un pronóstico oficial mensual.

La ejecución real mensual se ajusta con el IPC de cada mes. Septiembre no tiene IPC observado en esta versión: su importe real queda ausente. El porcentaje devengado/vigente usa siempre pesos nominales y no cambia al alternar unidades. Septiembre es parcial al 15/09 y no se contrapone a nueve meses completos ni a un umbral uniforme de subejecución.

Variación con base cero o ausente: sin comparación. Cambios de participación: puntos porcentuales, no pesos. El signo de una variación presupuestaria no califica su conveniencia.

## Pendientes explícitos

1. Correspondencia institucional/códigos para 38 filas programáticas, antes de clasificarlas como nuevas/eliminadas o incorporarlas al ranking de cambios.
2. PIB nominal 2026–2027 conciliado con el universo de gasto de los anexos para extender la serie gasto/PIB. No se empalma el 14% consolidado del Mensaje con el gasto bruto de los anexos.
3. IPC observado de septiembre y meses siguientes para el gasto real ejecutado.
4. Equivalencia oficial entre ubicación «Exterior» del proyecto y «No Clasificado» de PA 2026.

## Diseño, navegación y estadísticas

La primera entrega se basó en el brief y nueve capturas de Presupuesto OpenArg suministrados por Federico. La revisión de identidad del 17/09/2026 adopta el sistema visual del tablero municipal: Manrope alojada en `/municipios/assets/`, fondo claro, verde petróleo, marca fp., tarjetas redondeadas y modo oscuro verde opcional. Se reemplazó la portada editorial y los capítulos numerados por cinco vistas: Panorama, Gasto, Obras, Economía y Ejecución.

El Panorama integra una lectura propia que contrasta cambio nominal y real, sin confundir el proyecto 2027 con la ejecución 2026. Los controles se muestran donde aplican. Todas las secciones y enlaces anteriores siguen accesibles; la navegación Atrás/Adelante restaura también los filtros. La metodología tiene un acceso específico. No se modificaron datos, fuentes, fechas ni fórmulas de ajuste. El detalle de la revisión está en `docs/rediseno-nacion-identidad-municipal-2026-09-17.md`.

La ruta propia de GA4 es `/nacion/`. Sólo se registran anclas de una lista permitida. No se envían búsquedas, provincia seleccionada ni parámetros arbitrarios; se respeta la exclusión existente. La descarga CSV identifica unidades y conserva nulos vacíos; los grupos son distintas aperturas del mismo gasto y **no deben sumarse entre sí**.

## Verificación de la primera entrega

- 92 pruebas Node y 123 pruebas Python aprobadas; controles de vigencia de 24 informes provinciales y 135 municipales, cobertura municipal, reclamos y trazabilidad TOP aprobados.
- Navegador real: tamaños 390×844, 768×1024 y 1440×1000, ambos temas, cuatro aperturas de distribución, tres bases comparativas, precios corrientes/constantes, mapa por clic y teclado, búsquedas de obras/programas, expansión y carga adicional de programas, rankings y tres vistas históricas.
- Verificado que ejecución siga en 69,1% al cambiar de precios, que septiembre se identifique como parcial y que los tooltips de participación expresen porcentajes.
- CSV nominal y real descargados mediante el botón y comprobados como archivos. Enlaces entre Provincias, Municipios y Nación probados en celular. Sin desbordamiento horizontal de página a 390 y 768 px; las tablas tienen desplazamiento propio.
- Las limitaciones de datos enumeradas arriba permanecen visibles donde afectan una comparación; los tests no reemplazan esa evidencia pendiente.

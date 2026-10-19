# Recuperación de cuentas municipales · 19/10/2026

## Dos cuentas completas incorporadas

General Pinto: la tercera página del portal oficial contiene el ZIP de situación económico-financiera a septiembre. La revisión anterior se había detenido en los enlaces iniciales y omitido esta paginación. CAIF: ingresos 18.615.487.946,67; gastos fiscales 17.776.649.066,28; resultado 838.838.880,39 pesos. El devengado presupuestario bruto es 17.835.150.905,27: la diferencia de 58.501.838,99 no se incorpora al gasto fiscal. Cuenta en otros períodos; no entra en el ranking de junio.

Roque Pérez: la página oficial de situación económica-financiera publica una imagen JPEG firmada, omitida al buscar principalmente PDF. Encabezado 02/01/2026–30/06/2026. Ingresos 9.570.490.496,34; gastos fiscales 8.685.785.019,90; resultado 884.705.476,44. Corriente/capital y resultado conciliados al centavo. Integra el ranking semestral. No se sumó la ejecución abril–junio ni se confundió con el acumulado.

Originales archivados, SHA-256 y ubicación en fiscal_verified.json. Ejecuciones parciales reemplazadas conservadas en superseded-partial-executions.json. No se infiere caja libre del resultado.

## San Miguel

Se revisaron nuevamente todos los enlaces del portal de transparencia (HTML conservado). Publica recursos por carácter económico y gastos por objeto/programa, sin CAIF ni cuadro económico de gastos. La cuenta sigue parcial: falta validar la clasificación de insumos de proyectos entre corriente y capital. Los pagos de pasivos anteriores y adelantos ya están separados en la ficha y el PDF. No se atribuye resultado fiscal a la diferencia bruta. Último encabezado verificable: primer trimestre de 2026, pese a enlaces mal rotulados como cuarto trimestre.

## Búsquedas alternativas de los 13 faltantes

Se hicieron búsquedas indexadas dirigidas a concejos, SIBOM, Boletín Oficial provincial y portales municipales. Alcance acotado: no es una lectura exhaustiva de todos los boletines ni prueba de inexistencia de cuentas.

- Cañuelas y General Arenales: búsquedas de rendición/situación financiera y SIBOM sin una nueva cuenta utilizable.
- Esteban Echeverría: https://boletinoficial.gba.gob.ar/secciones/13445/descargar contiene resoluciones del Tribunal sobre ejercicios anteriores (incluido 2017), no la ejecución 2026 buscada.
- General Paz: https://www.hcdgeneralpaz.gob.ar/2026/05/ordenanza-n-222026.html aprueba compensaciones de 2025 y remite a Anexo I; no ofrece el anexo ni la CAIF en los enlaces de la página.
- Hurlingham: búsquedas en el Concejo y por CAIF devolvieron principalmente cuentas de la Universidad, que no corresponden al municipio. La referencia provincial https://www.ec.gba.gov.ar/Evoluci%C3%B3n%20Econ%C3%B3mica-Financiera%20Municipios.pdf se recuperó por descarga directa: 337 páginas, publicado en noviembre de 2019, con serie 2009–2018. No completa la ejecución actual; no se atribuye una fecha actual por la fecha del buscador.
- La Costa: https://martinfernandezok.com.ar/html/rendicion_cuentas.html ofrece un análisis y copias de supuestos anexos 2025. Es un sitio personal de un concejal, no el repositorio municipal. Se conserva como pista pendiente de validación de origen, cobertura e identidades; no se cargan sus cifras como verificadas.
- Leandro N. Alem y Lomas de Zamora: búsquedas dirigidas a rendiciones, SIBOM y Concejo de Lomas sin planillas nuevas localizadas.
- Mar Chiquita: SIBOM devuelve boletines históricos y actos sobre rendiciones, sin una cuenta reciente conciliada en esta revisión.
- Merlo: https://www.merlo.gob.ar/sesion-ordinaria-en-el-concejo-deliberante/ confirma aprobación de 2024; la noticia no publica las planillas.
- Pila: búsquedas en el Tribunal y municipio devolvieron presupuesto 2024 y referencias a un fallo; no ejecución actual. Presupuesto original no reemplaza cuenta ejecutada.
- Punta Indio: boletín de julio 2025 y búsquedas SIBOM sin cuenta reciente verificable. No se cursaron pedidos externos.
- Tordillo: https://tordillomunicipio.org/index.php/2026/04/08/el-concejo-deliberante-de-tordillo-aprobo-una-resolucion-en-reclamo-por-fondos-nacionales/ menciona documentación para analizar 2025, sin publicar la cuenta.

Cobertura posterior: 85 cuentas semestrales, 36 municipios adicionales con otro período, uno parcial (San Miguel), 13 sin cuenta completa. Total con cuentas: 121/135; no equivale a 121 cuentas de 2026 ni a cobertura semestral universal.

Presupuesto vigente de Roque Pérez actualizado a junio: 19.763.071.313,44 pesos; original anual 17.050.281.000,00. Se conserva el corte de marzo en roque-budget-march.json.

Validación local: 179 pruebas Python y 151 JavaScript aprobadas. 135 paquetes PDF comprobados contra datos vigentes; inspección visual de páginas de cuentas de Pinto y Roque Pérez. No se modificó la eliminación preexistente de tests/test_ron_september.py.

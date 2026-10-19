# Recuperación de cuentas en imágenes y páginas secundarias — 19/10/2026

## Incorporación verificable

Hurlingham: cuenta completa del 01/01/2021 al 31/12/2021, recuperada en dos PNG oficiales mediante el índice público de medios de WordPress. Se transcribió la CAIF de la primera imagen y se corroboró el resultado financiero con el artículo 43 de la segunda. Originales y SHA-256 en `municipios/data/fiscal-sources/2026-10-19-media/` y `fiscal_verified.json`.

Importes corrientes de 2021, en pesos: ingresos 6.785.117.314,61; gastos fiscales 6.523.739.600,91; resultado 261.377.713,70. Las sumas corriente + capital y la resta ingresos - gastos concilian al centavo. El gasto presupuestario bruto de 9.831.009.574,81 incluye activos financieros y cancelación de pasivos; no se usa como gasto fiscal. Tampoco se sustituye el resultado CAIF por el del artículo 44.

Se agrega como antecedente histórico, con período visible, al tablero y los informes. No integra el ranking comparable del primer semestre de 2026. No se afirma que estén actualizadas las cuentas de Hurlingham.

## Búsqueda y límites

- San Miguel: reexaminados enlaces y medios del portal. Los documentos disponibles mantienen el corte 02/01–31/03/2026, aunque algunos nombres de archivo dicen cuarto trimestre. Se revisó la apertura programática de 170 páginas; sus actividades y obras requieren una correspondencia económica verificable para repartir insumos corrientes y capital. No se incorporó una CAIF reconstruida sin validar esa correspondencia. Se conservan la ejecución parcial y las tres partidas financieras ya verificadas.
- General Paz: se abrió el iframe `transparencia/navega.html`, su script y `transparencia/scan.php`. El índice ofrece ordenanzas fiscales, decretos y resoluciones, sin una cuenta completa identificada. Se corrige la descripción del pendiente: el explorador sí es accesible.
- Punta Indio: se descargaron y revisaron los textos de ocho boletines enero–agosto de 2026 y cinco de 2025. No se identificó una CAIF o ejecución consolidada en esos textos. No se certifica inexistencia de información en cualquier otra publicación o imagen.
- Leandro N. Alem: la imagen del apartado Gobierno Abierto es un banner; no contiene una cuenta.
- Esteban Echeverría: el archivo «Anexo III - Rendición de cuentas» es un formulario vacío para entidades receptoras de subsidios, no la cuenta municipal.
- Los inventarios de páginas, imágenes, iframes y búsquedas públicas de medios quedan en `inventory.json` y `wp-media.json`. `more-downloads.json` conserva URL, estado HTTP, hash y páginas de los documentos adicionales; las copias de trabajo permanecen en `../municipal-media-oct19/`.

La revisión abarcó los portales de San Miguel y los 13 municipios pendientes, con profundidad adicional en los hallazgos anteriores. No equivale a una conciliación exhaustiva de todos los documentos de cada portal.

## Cobertura resultante

85 municipios con cuenta comparable del primer semestre; 37 con cuentas de otros períodos; San Miguel con ejecución parcial; 12 sin cuenta completa incorporada. Los 122 municipios con cuenta incluyen antecedentes históricos: esa cifra no representa actualización a 2026.

Pendientes sin cuenta: Cañuelas, Esteban Echeverría, General Arenales, General Paz, La Costa, Leandro N. Alem, Lomas de Zamora, Mar Chiquita, Merlo, Pila, Punta Indio y Tordillo. Hurlingham sigue pendiente de una cuenta reciente. General Arenales mantiene un redireccionamiento inválido; Lomas presenta un problema de certificado en el portal municipal. No se reemplazaron fuentes oficiales por copias de terceros sin corroboración.

## Controles de publicación

Se regeneran tablero, cobertura y PDF desde la misma cuenta verificada. La prueba de regresión comprueba que Hurlingham conserva el corte 2021, no ingresa al ranking 1S2026 y no usa el total presupuestario bruto. Ver resultados de pruebas y hashes públicos en el registro de esta ejecución.

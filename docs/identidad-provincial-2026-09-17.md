# Tablero Provincial: identidad compartida

17/09/2026. Adaptación visual a los tableros Municipal y Nacional.

## Cambios

- Manrope local compartida, marca `fp.`, fondo claro y verde petróleo. Tema oscuro con superficies verdes y colores de contraste propios.
- Encabezado fijo de una fila, navegación liviana, selector provincial y accesos a Municipios y Presupuesto Nacional.
- Se conserva el menú desplegable en teléfonos, incluido paisaje. Los tres perfiles y las unidades siguen disponibles fuera del menú.
- Controles compactos, informe PDF accesible, cifras principales grandes, tarjetas redondeadas y lectura editorial con una línea lateral.
- Las cifras secundarias se presentan sobre el fondo, sin repetir cajas. En teléfonos, cada indicador estructural usa todo el ancho y los gráficos se apilan también en tablets angostas.
- Gráficos con Manrope, ejes y series adaptados al tema. Las leyendas externas conservan la correspondencia de colores. Los negativos siguen en rojo.

La capa `provincial-identity.css` concentra la identidad vigente, después de los estilos funcionales anteriores. No cambia fuentes, cortes, valores, fórmulas ni PDFs.

## Corrección visual encontrada

El anillo de acreedores usa los porcentajes oficiales de Buenos Aires. Al cambiar de jurisdicción, la ficha actualizaba los importes pero podía conservar ese anillo anterior. Ahora sólo aparece cuando corresponde a la provincia y fuente que lo alimentan; las otras composiciones mantienen sus datos disponibles. También se separaron los colores de bonos y préstamos para que el nuevo acento verde no los vuelva indistinguibles.

## Verificación

- 98 pruebas Node y 128 Python aprobadas. Se actualizó una expectativa del título inicial, que todavía buscaba el nombre anterior.
- Sintaxis de los 18 bloques de scripts del HTML y del script de presentación. Paleta de siete colores reversible entre temas, manteniendo opacidad y distinciones.
- Las once vistas verificadas en navegador real a 390 y 768 px, con cierre del menú tras navegar y sin desbordamiento horizontal del documento. Las tablas extensas conservan su desplazamiento interno.
- Revisión visual del resumen a 1440 px, controles y resumen a 320 px, modo oscuro, perfiles Gobernador/Ministro de Economía/Prensa, pesos constantes, y cambio Buenos Aires/Córdoba con enlace PDF correspondiente.
- Comprobados los gráficos de deuda, series de ingresos y tablas estructurales; corregido el ancho heredado de las celdas móviles que cortaba las explicaciones en columnas demasiado angostas.
- Consola sin errores durante el recorrido de las once secciones.

La validación de datos y la vigencia de los informes se vuelven a ejecutar en la integración continua antes de publicar.

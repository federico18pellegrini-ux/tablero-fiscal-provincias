# Identidad PELLEGRINI en los tres tableros

Fecha: 17/09/2026. Referencia: Manual de Marca y Criterios y Prompt v1 suministrados por Federico Pellegrini.

## Aplicación

- Provincias, Municipios y Presupuesto Nacional comparten `brand.css`, el logo tipográfico PELLEGRINI y el favicon con una P trazada de Playfair Display.
- Azul marino #0A192F, dorado #B8924A en detalles, blanco y fondos neutros. El dorado no se utiliza para texto pequeño sobre blanco.
- Playfair Display para marca y títulos; Geist para lectura, cifras, controles y gráficos; Geist Mono para el descriptor de marca.
- Fuentes variables originales alojadas localmente, con licencia OFL y huellas de los archivos en `assets/brand/fonts.json`. No se modifican ni renombran las familias.
- Rojo #B91C1C y verde #047857 conservan el significado de los indicadores. Series sin juicio de valor usan azul, gris, dorado y violeta, con variantes de contraste para modo oscuro.
- El cambio afecta la presentación web. No modifica fórmulas, datos, cortes ni contenidos de los PDF exportables.
- Las páginas municipales auxiliares y sus generadores incluyen la misma hoja de marca.

## Verificación local

- 98 pruebas JavaScript y 128 pruebas Python aprobadas.
- Comprobación de cobertura e IPC municipal aprobada; sin cambios de datos.
- Inspección visual de los tres tableros a 390 px y 768 px, además de escritorio; verificación adicional a 320 px sin desbordamiento horizontal de la página.
- Menú provincial móvil abre, cambia de vista y se cierra. Navegación y ranking municipal conservan funcionamiento y colores: negativos rgb(185,28,28), positivos rgb(4,120,87).
- Modos claro y oscuro verificados en Provincias y Nación; la paleta de los gráficos acompaña el cambio de tema.
- A 320 px se acomodan los enlaces municipales para no tapar el logo y los controles nacionales se ordenan en filas sin solapamientos.
- Revisión de diferencias para evitar cambios involuntarios de texto y preservar UTF-8.

La publicación requiere los controles automáticos de la rama y comprobación posterior de los archivos servidos por el dominio público.

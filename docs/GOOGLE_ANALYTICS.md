# Estadísticas de uso de los tres tableros

Alta: 7 de septiembre de 2026. Cuenta: Federico Pellegrini (194596609).
Propiedad: **Tableros · Federico Pellegrini** (553016633; nombre actualizado el 17/09/2026, sin cambiar la propiedad ni su historial).
Flujo: **Tablero Fiscal — Web** (15730871499). ID público de medición: `G-H3P727GYS0`.
Horario: Buenos Aires (UTC−3). Moneda: ARS.

[Abrir estadísticas](https://analytics.google.com/analytics/web/#/a194596609p553016633/reports/intelligenthome).
En Inicio → Ver en tiempo real se ven los usuarios activos recientes.
Informes permite consultar usuarios, sesiones, origen, dispositivos y páginas por período.
Las estadísticas empiezan con esta instalación: no recuperan las visitas anteriores.

## Cómo comparar Nación, Provincias y Municipios

- Los tres tableros usan la misma propiedad y el mismo identificador de medición.
- En **Páginas y pantallas**, seleccionar **Grupo de contenido** para comparar
  **Nación**, **Provincias** y **Municipios**. El agrupamiento se envía desde el
  17/09/2026; no reclasifica eventos anteriores.
- Seleccionar **Título de página y clase de pantalla** para ver las secciones
  consultadas, incluidas las visitas históricas. Los títulos distinguen los tableros.
- **Tiempo real** permite verificar visitas recientes; **Adquisición de tráfico**
  muestra la procedencia y los informes de tecnología permiten comparar dispositivos.
- Las vistas no equivalen a visitantes únicos. Las pruebas en `localhost` y
  `127.0.0.1` no se envían a Google: la medición funciona en el sitio publicado.

## Implementación

- `analytics.js` sólo carga la etiqueta en HTTPS y en el dominio de producción. Desarrollo y copias de prueba no envían eventos.
- `page_view` inicial y por cada cambio efectivo entre las once vistas. Se deduplican las notificaciones repetidas de una misma vista. Los filtros, la provincia y el perfil de lectura no generan vistas extra.
- Municipios registra sus seis vistas y Nación sus secciones al navegar. Todos
  incluyen el parámetro estándar `content_group`; no requiere una dimensión personalizada.
- `file_download` registra el clic en el PDF de la provincia seleccionada; no certifica que el navegador haya terminado de guardar el archivo.
- La medición mejorada del flujo está **desactivada** y `send_page_view` es `false`. Mantener ambas configuraciones para no duplicar las vistas manuales.
- Se excluyen parámetros de URL, rutas externas del referente, perfiles de lectura, escenarios y textos libres. No se configuran User-ID, Google Signals ni publicidad personalizada.
- Las cookies usan el prefijo `tablero` y el dominio del tablero. `privacidad.html` informa el uso y permite desactivar la carga de Analytics en ese navegador.
- Usuarios y sesiones son estimaciones del navegador. Bloqueadores y preferencias de privacidad pueden reducir el conteo. Las vistas y las descargas no equivalen a personas distintas.

## Verificación

### Revisión del 17/09/2026

- Acceso confirmado en la interfaz de Analytics a la propiedad y a visitas
  históricas de Provincias y Municipios.
- Se configuró el **Informe panorámico** con la plantilla de comportamiento de
  usuarios: visitantes, interacción, páginas consultadas y procedencia.
- La configuración remota tenía medición mejorada activa, incluido el cambio de
  historial, pese a lo indicado antes en este documento. Se desactivó para evitar
  vistas automáticas adicionales al cambiar filtros y mantener el conteo manual.
  No se borró ni se recalculó el historial anterior; podría incluir duplicaciones.
- **Grupo de contenido** ya existe entre las dimensiones de Páginas y pantallas.
  La separación en tres grupos comienza con la nueva etiqueta y no es retroactiva.

Pruebas: `node --test tests/analytics.test.cjs`.
Tras publicar, abrir el tablero y cambiar entre Resumen, Solvencia y deuda, e Historia fiscal.
En Analytics → Tiempo real comprobar los títulos correspondientes y la llegada de `page_view`.
La instalación se puede revisar desde Administrar → Flujos de datos → Tablero Fiscal — Web → Instrucciones de etiquetado → Probar instalación.

Documentación oficial: [medición de vistas](https://developers.google.com/analytics/devguides/collection/ga4/views), [aplicaciones de una sola página](https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications) y [grupos de contenido](https://support.google.com/analytics/answer/11523339?hl=es).

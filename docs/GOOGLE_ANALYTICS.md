# Estadísticas de uso del tablero

Alta: 7 de septiembre de 2026. Cuenta: Federico Pellegrini (194596609).
Propiedad: **Tablero Fiscal · Federico Pellegrini** (553016633).
Flujo: **Tablero Fiscal — Web** (15730871499). ID público de medición: `G-H3P727GYS0`.
Horario: Buenos Aires (UTC−3). Moneda: ARS.

[Abrir estadísticas](https://analytics.google.com/analytics/web/#/a194596609p553016633/reports/intelligenthome).
En Inicio → Ver en tiempo real se ven los usuarios activos recientes.
Informes permite consultar usuarios, sesiones, origen, dispositivos y páginas por período.
Las estadísticas empiezan con esta instalación: no recuperan las visitas anteriores.

## Implementación

- `analytics.js` sólo carga la etiqueta en HTTPS y en el dominio de producción. Desarrollo y copias de prueba no envían eventos.
- `page_view` inicial y por cada cambio efectivo entre las once vistas. Se deduplican las notificaciones repetidas de una misma vista. Los filtros, la provincia y el perfil de lectura no generan vistas extra.
- `file_download` registra el clic en el PDF de la provincia seleccionada; no certifica que el navegador haya terminado de guardar el archivo.
- La medición mejorada del flujo está **desactivada** y `send_page_view` es `false`. Mantener ambas configuraciones para no duplicar las vistas manuales.
- Se excluyen parámetros de URL, rutas externas del referente, perfiles de lectura, escenarios y textos libres. No se configuran User-ID, Google Signals ni publicidad personalizada.
- Las cookies usan el prefijo `tablero` y el dominio del tablero. `privacidad.html` informa el uso y permite desactivar la carga de Analytics en ese navegador.
- Usuarios y sesiones son estimaciones del navegador. Bloqueadores y preferencias de privacidad pueden reducir el conteo. Las vistas y las descargas no equivalen a personas distintas.

## Verificación

Pruebas: `node --test tests/analytics.test.cjs`.
Tras publicar, abrir el tablero y cambiar entre Resumen, Solvencia y deuda, e Historia fiscal.
En Analytics → Tiempo real comprobar los títulos correspondientes y la llegada de `page_view`.
La instalación se puede revisar desde Administrar → Flujos de datos → Tablero Fiscal — Web → Instrucciones de etiquetado → Probar instalación.

Documentación oficial: [medición de vistas](https://developers.google.com/analytics/devguides/collection/ga4/views) y [aplicaciones de una sola página](https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications).

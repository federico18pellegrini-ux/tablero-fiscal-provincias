# Un cruce adicional resuelto; once casos originales pendientes

Revisión del 18/09/2026. Se incorporó la comparación de **Planificación y Sostenibilidad Energética (p221)**. El tablero pasa de 379 a **380 partidas comparables sobre 394**, con 28 correspondencias documentadas por códigos. Quedan 11 de los 12 casos originales; junto con las tres comparaciones relacionadas, son 14 partidas sin base individual, equivalentes al 0,139% del gasto del proyecto.

## Qué permitió cerrar Energía

La AGN, en su informe 154/2026 aprobado el 14/07, describe la decisión de adelantar el cierre del préstamo BIRF 9521 y la liquidación de obras pendientes. Ese antecedente permitió localizar dos documentos posteriores a la reestructuración de 2025 que se había revisado antes:

- [Reestructuración del Banco Mundial, 29/06/2026](https://documents.worldbank.org/curated/en/099062926080015341/pdf/P178553-019d915d-c981-4b10-a83d-96a1a227b4a4.pdf), páginas PDF 6 y 7: reducción adicional de USD 13 millones y cierre anticipado.
- [Enmienda firmada, carta del 30/06/2026](https://documents.worldbank.org/curated/en/099091726160039524/pdf/P178553-13e3a3a3-b4a7-4e99-bae9-cd4a97f5fd98.pdf), páginas 1, 2 y 6: fija el cierre para el **20/12/2026**, acredita la devolución previa y la cancelación adicional de USD 13 millones. La aceptación argentina está fechada el 19/08/2026. La ficha del Banco Mundial registra la publicación el 17/09/2026.
- [AGN 154/2026](https://www.agn.gob.ar/sites/default/files/informes/2026-154-Informe.pdf), páginas PDF 16 a 18: detalle de la reestructuración y de las obras pendientes de liquidación. Es una auditoría de los estados financieros 2025 con hechos posteriores, no una ejecución presupuestaria de todo 2026.

La fecha de cierre está aprobada, pero todavía es futura. No se afirma que el préstamo ya esté cerrado ni que sus cuentas estén conciliadas a septiembre.

La consulta inicial a la API v2 del Banco Mundial devolvía 42 documentos y no mostraba novedades posteriores a enero de 2025. La ficha oficial utiliza la API v3: allí aparecen 52 documentos, incluida la enmienda. Se verificó el PDF firmado, no solamente el resultado del buscador. Los originales incorporados al repositorio conservan tamaño y SHA-256 en `crosswalk.json`.

## Cómo se reconstruye la base

La comparación del programa 72 de 2027 se reconstruye desde el programa 75 de 2026, SAF 357, jurisdicción 50. Se excluye únicamente la actividad 40, subsidio a garrafas, que se suma a Hidrocarburos. Se conservan las actividades 1, 30, 31 y 48. El cierre del BIRF 9521 explica una finalización de gasto dentro de la política energética: quitar también su gasto histórico inflaría artificialmente el crecimiento.

| Base 2026, millones de pesos | Inicial | Vigente al 15/09 | Devengado al 15/09 |
|---|---:|---:|---:|
| Conducción, BIRF 9747 y BID 5952 | 32.195,73 | 13.747,86 | 2.743,58 |
| BIRF 9521, con cierre fijado para diciembre | 0,00 | 20.361,44 | 18.508,59 |
| **Base de Planificación Energética** | **32.195,73** | **34.109,30** | **21.252,17** |

El cero inicial es el registro de la base oficial, no la sustitución de un dato faltante. La apertura 2027 conserva conducción y los préstamos BIRF 9747 y BID 5952 e incorpora apoyo a la focalización de subsidios; asigna **$33.633 millones** al programa. [ONP, páginas 72 a 74](https://www.mecon.gob.ar/onp/documentos/presutexto/proy2027/jurent/pdf/P27J50.pdf#page=72).

La variación es **-1,4% nominal y -18,2% real frente al vigente**. Contra el inicial es +4,5% nominal y -13,3% real. Se mantiene el deflactor promedio anual del tablero. El cierre estimado individual sigue sin dato: la nueva evidencia no autoriza a calcularlo.

Las bases de Planificación e Hidrocarburos suman exactamente los anteriores programas 75 y 73. Cada registro se utiliza una sola vez. No cambian el total nacional, la ejecución agregada ni la base de Hidrocarburos ya corregida.

## Estado de los otros once casos

| Casos | Documento o apertura que sigue faltando |
|---|---|
| p42 y p52 · Vocería y Comunicación | Costos de las unidades trasladadas entre ambas áreas y las incorporaciones desde otras oficinas. |
| p59 · Apoyo a Turismo, Ambiente y Deporte | Origen de los gastos comunes de Deportes que pasan a la nueva categoría 4, sin duplicar los de la categoría 11. |
| p60 · Apoyo al financiamiento externo | Distribución de contratos y gastos administrativos entre los dos programas 10 de 2027. Afecta también p73. |
| p69 · Ambiente | Reparto de educación, información ambiental y coordinación entre los programas 14 y 80. Afecta también p63. |
| p103, p105 y p107 · ENACOM | Separación de los costos 2026 de fiscalización, autorizaciones y seguimiento de proyectos. El portal propio remite al presupuesto ONP 2026 y no aporta ese reparto. |
| p228 · Hábitat | Origen de las actividades GEF 4861 y destino de las tareas y gastos de los antiguos programas 40 y 83. El cierre de un préstamo, por sí solo, no resuelve las demás incorporaciones. |
| p252 · Investigación y grandes proyectos de CNEA | Reparto completo del personal y apoyo entre investigación, enriquecimiento y energía nuclear. Afecta también p248. El portal propio y su catálogo no agregan esa distribución. |
| p277 · Actividades comunes de SEGEMAR | Gasto 2026 de las funciones de la nueva Dirección Nacional. El PDF publicado por el organismo conserva la apertura 2026 anterior. |

La revisión conserva las cinco comparaciones de conjuntos que permiten analizar estas reorganizaciones sin atribuir un importe a cada programa por suposición. La documentación consultada y sus huellas se registran en [el archivo de evidencia](nacion-tercera-busqueda-2026-09-18.json). Los portales inspeccionados se archivaron en el paquete local de investigación; sus referencias en el registro no son rutas públicas.

Se actualizó el [pedido de documentación a la ONP](nacion-pedido-correspondencias-2026-09-18.md), retirando Energía de los pendientes. La presentación y su constancia se registran aparte: este documento no acredita que el pedido haya sido recibido.

## Validación

- Conciliación independiente de las cuatro actividades retenidas, exclusión de garrafas y suma de ambos programas de Energía; comprobación del cierre contra la enmienda archivada.
- Pruebas de cálculo, controles de datos y consistencia de los informes. El corte productivo sigue siendo el 15/09/2026.
- Navegación y descargas en 320, 390, 768 y 1440 píxeles, con precios, bases y temas claro/oscuro; revisión de los 24 casos documentados y las 12 variantes del informe general.
- Los informes generales conservan 19 páginas; los anexos completos, 66. Las otras 27 fichas de una página conservan su contenido. Se revisó visualmente la nueva fila de Energía y sus referencias.

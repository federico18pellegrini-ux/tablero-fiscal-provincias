# Históricos incorporados — 20/10/2026

Actualización posterior: se recuperó La Pampa 2025 sumando los doce meses oficiales. Ver [seguimiento y nuevos hallazgos](recaudacion-seguimiento-2026-10-20.md). El pendiente de La Pampa que se describe abajo corresponde al estado previo.

Se preservaron los originales oficiales y sus hashes en `data/revenue-history-sources/` y `data/revenue_history_completion.json`.

## Incorporaciones

- Recaudación propia: 624 observaciones. CABA y Santiago del Estero incorporan 1984–2025, con total y cinco categorías. Otras 20 provincias incorporan 2025. Buenos Aires ya tenía ese año; La Pampa no publica un dato completo.
- Transferencias: 140 observaciones de total y CFI. Se completan 2003–2024 de CABA y Santiago del Estero y 2018–2024 de La Pampa y Santa Fe. Se normaliza además la CFI de 2005 para las 24 jurisdicciones. Las 24 tienen total y CFI 2003–2025.
- Los 494 totales de transferencias que ya existían concilian con la suma de regímenes del CSV oficial, con tolerancia de 0,02 millones por redondeo. Se comprueba la suma de los cinco impuestos contra el total de la planilla TOP cuando están todos publicados.
- Se conservan los valores previos; las importaciones agregan observaciones ausentes.

## Fuentes y meses recientes

- [DNAP, TOP histórico](https://www.argentina.gob.ar/sites/default/files/serie_top_1984_2025_0.xlsx), descargado el 20/10.
- [DNAP, RON histórico](https://www.argentina.gob.ar/sites/default/files/serie_ron_2003_2025.csv), original preservado y contrastado el 19/10.
- [IDECBA, recaudación mensual](https://www.estadisticaciudad.gob.ar/eyc/banco-datos/recaudacion-impositiva-de-fuente-propia-mensual-millones-de-pesos-por-concepto-ciudad-de-buenos-aires-anos-19972014/): llega a agosto 2026, ya cubierto. Se preserva como contraste, sin mezclarlo con la serie nacional. Su encabezado 1988 entre 1997 y 1999 se excluye de la extracción auxiliar; el histórico publicado usa DNAP.
- La descarga actual de TOP mensual 2026_19 es idéntica al original importado: sin meses nuevos. Santa Fe publica hasta agosto; el índice localizado de Córdoba también llega a agosto. ARBA enlaza un PDF antiguo (2018), descartado para actualizar 2026. ATM Mendoza requiere resolver acceso y confirmar período y cobertura antes de incorporarlo.

No se encontraron meses adicionales verificables en estas consultas. No se afirma búsqueda exhaustiva en todos los portales tributarios. Siguen pendientes los meses rezagados, el año 2025 de La Pampa y el empalme documentado del IPC anterior a 2017.

## Pruebas y lectura móvil

Se comprobaron los históricos constantes en las 24 jurisdicciones a 390 × 844: sin errores JavaScript, sin desborde horizontal y con ambos gráficos dibujados. Revisión visual de CABA en celular y La Pampa a 768 × 1024. Los años faltantes quedan como interrupciones de la línea, sin convertirlos en ceros.

Los exportables provinciales actuales no incluyen estas dos series largas y sus insumos numéricos no cambian. No se regeneraron PDF sin cambios de contenido.

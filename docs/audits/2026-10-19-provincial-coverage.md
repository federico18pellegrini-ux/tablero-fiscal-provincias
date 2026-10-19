# Cobertura provincial y dinámica real — 19/10/2026

## Correcciones reproducibles

1. `scripts_build_real_dynamics.py` sumaba los cinco componentes tributarios y la fila `Total` de la base bonaerense 2025. Duplicaba el denominador. Se suman exclusivamente los cinco componentes y se reconcilian contra el total publicado; las observaciones duplicadas o totales discordantes provocan un error. Componentes incompletos sin total no se convierten en una recaudación total.
2. PBA enero–julio: la variación real acumulada pasa de -51,2% a -2,5%; julio de -54,3% a -8,5%. Esto corrige el JSON de dinámica; la comparación detallada `data/pba_comparison.json` ya informaba -2,48808696% usando el original provincial y los informes exportables utilizaban esa comparación correcta. No se modifica la fuente ni su corte julio de 2026.
3. El acumulado anual exige meses consecutivos desde enero y hasta el último mes disponible; no llama acumulado enero–X a una secuencia que comienza más tarde o excluye meses finales sin base comparable.
4. El mapa anterior consideraba completas sólo las celdas `numerico`, por lo que una estimación oficial o cálculo documentado aparecía como faltante. Además no reconocía los ratios bonaerenses porque el panel duplicado de liquidez se oculta: los datos están en la ficha de deuda. Se conectan los ratios oficiales publicados al 30/06/2026: intereses pagados / recursos 3,7%; servicios / recursos 10,3%; stock / recursos 45,5%. Original y hash en `data/debt/pba_debt_profile_2026q1.json`.
5. La columna que describía la finalidad del bloque ahora indica disponibilidad y faltantes concretos, y devuelve esos pendientes en la exportación de cobertura. El cálculo filtra por provincia para no heredar controles de otras jurisdicciones.

## Qué significa completo

Completo refiere a los indicadores definidos y a sus cortes explícitos, no a toda la información necesaria para administrar una provincia. El perfil cubre stock y composición; no certifica un cronograma mensual. La presión de deuda cubre ratios sobre recursos totales; no caja libre, aguinaldo ni una simulación de pagos. La dependencia cubre impuestos nacionales y transferencias automáticas; la estimación territorial se mantiene identificada.

Para Buenos Aires quedan cuatro bloques completos en ese alcance y dos parciales:

- **Equidad federal**: RON per cápita disponible; falta una estimación homogénea de aportes tributarios territoriales para todas las provincias. La estimación oficial de PBA no se extrapola ni convierte una brecha per cápita en incumplimiento legal.
- **Dinámica fiscal**: recaudación propia comparable a julio y RON a septiembre disponibles. Faltan series mensuales comparables 2025–2026 de gasto primario, personal e inversión. Hay cuentas semestrales verificadas en otro bloque; no se reparten artificialmente entre meses.

No se completaron estas variables con proxies. Para avanzar se requieren planillas mensuales oficiales comparables y una metodología territorial nacional; no se encontraron nuevas fuentes verificables en esta ronda. Las búsquedas de la página DNAP de recursos provinciales no devolvieron una base mensual 2025 adicional. No se afirma que esa base no exista.

## Verificación

Pruebas específicas de doble conteo, datos parciales, duplicados, cobertura de ratios y separación de provincias. Navegación local por las 24 jurisdicciones; Buenos Aires muestra cuatro completos y dos parciales, el resto conserva sus faltantes. Se verifica la vigencia de los 24 informes provinciales: usan el cálculo correcto ya incorporado, por lo que no necesitan un cambio de importes por esta corrección.

## Reclamo bonaerense a Nación

Revisada nuevamente la publicación oficial del 14/09/2026: $19,1 billones, integrados por $4,7 billones directos, $10,1 billones de obras y $4,3 billones de programas. No se encontró una publicación oficial posterior que permita reemplazarlo ni un saldo conciliado al 19/10/2026. Se conserva el monto y la fecha originales; esta búsqueda no prueba que el saldo actual sea idéntico.

# Políticas públicas y financiamiento nacional

Primera entrega del 18/09/2026: búsqueda con palabras habituales, comparación simultánea contra tres bases de 2026, cierre fiscal y financiamiento 2027, fichas de inmunizaciones y educación superior.

## Accesos

- `/nacion/#financiamiento`
- `/nacion/#politica-inmunizaciones`
- `/nacion/#politica-educacion-superior`
- `/nacion/?buscar=vacunas#programas`

Las fichas están en la portada y en la búsqueda de programas. Cada programa permite copiar un enlace que conserva búsqueda, programa abierto, precios y base. Los nuevos recorridos se registran en Analytics sin transmitir palabras buscadas.

## Datos y cálculos

`scripts_build_national_decisions.py` genera `nacion/data/decisions.json` exclusivamente desde fuentes oficiales archivadas. `--check` verifica que la versión publicada coincide con los insumos. El CAIF completo se conserva en `nacion/data/decision-sources/caif-2027.pdf`; su huella debe coincidir con la registrada en el presupuesto. Se concilian ingresos, gastos, resultado y fuentes y aplicaciones financieras en ambos años, admitiendo únicamente el redondeo de la planilla.

Las dos políticas se vinculan por denominación y organismo exactos entre 2027 y 2026. Se verifican inicial, vigente y devengado. Dentro de 2026, ejecución y metas usan jurisdicción, SAF y programa. No se emplean coincidencias aproximadas.

Las variaciones reales usan los factores anuales medios del escenario de inflación del tablero. En la portada aparecen inicial, vigente y cierre estimado juntos, tanto nominales como reales. El cierre estimado por programa permanece ausente porque no está publicado.

El módulo financiero compara el proyecto 2027 con el cierre estimado 2026, independientemente del selector de base de otras secciones. La amortización no se suma al gasto presupuestario y las fuentes financieras no se presentan como incremento neto de deuda. Las transferencias figurativas se identifican como operaciones internas compensadas.

Los pagos y la ejecución corresponden al 15/09/2026; las prestaciones, a enero–junio de 2026. Estas etapas se muestran en pesos corrientes, sin aplicar un deflactor anual a flujos parciales. Gasto reconocido pendiente de pago no se interpreta como mora. Las 14 mediciones de inmunizaciones y las 13 de universidades conservan unidad, datos faltantes y comentarios oficiales sobre cobertura parcial. No se suman prestaciones de distinta naturaleza.

Si la huella del presupuesto cambia sin regenerar las fichas, se bloquea su lectura y se muestra un aviso de actualización. El presupuesto general sigue disponible.

## Alcance y validación

Esta entrega modifica la web; no agrega las fichas a los informes PDF existentes. Quedan fuera de este alcance la continuidad y financiación de obras, nuevos escenarios macroeconómicos y fichas para todos los programas.

Se verificaron las identidades contables, correspondencias, datos ausentes, alias de búsqueda, privacidad de Analytics y enlaces. La prueba de navegador cubre 320, 390, 768 y 1440 píxeles, temas claro y oscuro, estados conservados, exportación existente y ausencia de errores. Las tablas financieras se adaptan en tarjetas por concepto en celulares, mostrando ambos años sin desplazamiento horizontal.

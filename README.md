# Tablero fiscal de provincias

## Tablero municipal

El botón **Exportar informe completo** descarga un PDF del municipio seleccionado desde cualquiera de las vistas. Incluye una síntesis narrativa, cuentas fiscales o ejecución disponible, gráficos, los 27 indicadores con posición provincial y entre poblaciones similares, los 41 escenarios del simulador y todas las series mensuales. Los documentos conservan períodos, unidades, datos faltantes y el pie Federico Pellegrini / página. Los 135 PDF se preparan desde la misma base y el mismo modelo de cálculo del tablero.

Después de actualizar datos o el generador, ejecutar `python scripts_export_municipal_reports.py` y verificar con `python scripts_export_municipal_reports.py --check`. CI impide publicar informes desactualizados. El botón también contrasta la huella de la base cargada con el manifiesto antes de habilitar la descarga. Para recompilar sólo la aplicación, usar `python scripts_build_municipal_dashboard.py --bundle-only`. Las regresiones de exportación corren con `node --test tests/municipal_reports.test.mjs` y `python -m unittest discover -s tests -p test_municipal_reports.py -v`.

`/municipios/` reúne los 135 municipios bonaerenses en cinco vistas: Panorama, Recursos, Empleo, Simular y Ranking general. Incluye mapa Georef/IGN, selección persistente, enlaces directos, 27 indicadores de ranking: 19 de contexto, seis fiscales con cobertura parcial y dos de transparencia, descargas CSV y escenarios sobre coparticipación observada. La interfaz y los recursos visuales se sirven localmente; los datos faltantes quedan fuera de los rankings.

La base de esta versión proviene de la investigación auditada del 7 de septiembre de 2026. Transferencias: 2025 y enero–julio 2026; empleo: 2019–2025; población y NBI: Censo 2022; producto municipal: 2021–2023; bancos: 2024. Cuentas individuales: 18 municipios al primer semestre de 2026 y ejecución parcial de Tigre. Transparencia: puntajes ASAP de los 135 municipios para noviembre de 2025 y mayo de 2026, con sus seis componentes y fechas de relevamiento. `municipios/metodologia.html` documenta definiciones, diferencias de cobertura y enlaces; `municipios/data/build-manifest.json` conserva las huellas de los CSV de entrada.

Para regenerar el paquete desde el directorio de investigación, usar `python scripts_build_municipal_dashboard.py --input-dir /ruta/municipios-rankings-20260907`. El generador también compone `municipios/app.js` a partir de `model.mjs` y `app.mjs`. Las pruebas de cálculo, cobertura y geografía corren con `node --test tests/municipal_dashboard.test.mjs`. La medición GA4 distingue las vistas municipales y excluye municipio, simulaciones y parámetros libres.

Tablero fiscal para gobernadores y ministros. Las 24 jurisdicciones comparten navegación; las cifras conservan sus cortes y faltantes. El módulo nacional distingue al Sector Público Nacional de la suma de provincias.

## Actualización federal del 6 de septiembre de 2026

- Historia: 422 observaciones de 18 informes, desde 4T21 hasta 1T26. Cada punto es una ventana de últimos 12 meses, no un trimestre aislado. Los valores conservan la versión publicada en cada informe.
- Mapa interactivo IGN/Georef con selección de provincia, corte e indicador. Resultado agregado ponderado por ingresos; faltantes en gris, tabla y teclado como alternativas.
- Primario, financiero, resultado trimestral y composición de deuda: 23 jurisdicciones al 1T26. La Pampa queda sin dato en este corte.
- IPC nacional reconstruido desde los índices publicados por INDEC, diciembre de 2016 a julio de 2026. Base de pesos constantes: junio de 2026. No se deflactan totales anuales con el IPC de diciembre.
- Exportación PDF con texto seleccionable, datos, períodos y referencias; incluye opción de las 24 jurisdicciones.
- Vista nacional inicial: resultado fiscal SPN de julio de 2026, base caja. Caja, vencimientos, actividad, empleo y sector externo requieren una ampliación de fuentes; su ausencia se muestra explícitamente.

La implementación mantiene el trabajo anterior sobre resultados de gobierno, reclamos nacionales y fuentes oficiales. Los informes PDF suministrados localmente no se publican. Se incorporan los datos numéricos con referencia al informe y página.

### Importaciones reproducibles

```bash
python scripts_build_fiscal_history.py /ruta/extraccion_auditada.csv
python scripts_import_latest_fiscal.py /ruta/informe_1T26.pdf
python scripts_update_deflator.py /ruta/sh_ipc_08_26.xls
python scripts_sync_deflator_html.py
```

El importador del IPC requiere pandas/xlrd; el del PDF requiere pdfplumber. Sin argumento, el actualizador del IPC usa la serie oficial incluida en `data/ipc_national_index.csv`. La extracción trimestral verifica el diseño del informe 1T26; una edición con otro diseño exige revisión, no importación automática.

## Cortes vigentes

- Resultados y ranking homogéneo: últimos 12 meses al 31/03/2026, 23 jurisdicciones. La Pampa no integra el informe fiscal 1T26.
- Deuda PBA: stock al 31/03/2026; composición por moneda al 31/12/2025.
- Recaudación propia 2026: hasta julio según provincia; Buenos Aires hasta junio.
- Recursos de origen nacional 2026: 24 jurisdicciones hasta julio.
- Pesos constantes: base junio de 2026, con IPC nacional INDEC.
- Resultados de gobierno: seguridad 2025, Aprender 2024, mortalidad infantil 2024, NBI 2022 y gasto por finalidad 2024 para las 24 jurisdicciones.

Cada vista muestra su fecha de corte. Los flujos con meses distintos no se comparan directamente y los faltantes no se completan con cero.

## Experiencia de uso

- Perfil **Gobernador / decisor**: síntesis, riesgos y decisiones.
- Perfil **Ministro de Hacienda**: caja, estructura, deuda y flujos.
- Perfil **Analista / prensa**: metodología y detalle.
- Selector de últimos 12 meses o trimestre para las 23 jurisdicciones comparables.
- Selector de pesos corrientes o constantes.
- Módulos visibles y perfil guardados en el navegador.
- Enlaces directos: `#summary`, `#debt`, `#income`, `#federal` y `#comparison`.

## Capa canónica de datos

- `data/recaudacion_propia.csv`: impuesto, provincia, mes, monto, estado y fuente.
- `data/transferencias_nac.csv`: CFI, Compensación y RON total por provincia y mes.
- `data/cobertura.csv`: primer/último mes y estado de cobertura por jurisdicción.
- `data/gasto_rigido.csv`: piso observable PBA; se mantiene **parcial** porque faltan transferencias automáticas y otros compromisos no discrecionales.
- `data/meta.json`: fuentes, fechas de corte y reglas de faltantes.
- `dashboard_manifest.json`: inventario de archivos consumidos por el frente.
- `data/government_results_provinces.json`: capa federal comparable de resultados, contexto estructural y esfuerzo presupuestario.
- `data/government_results/official_metrics.csv`: base auditable de las 24 jurisdicciones utilizada para fórmulas y rankings.

Los CSV históricos y archivos especializados anteriores siguen disponibles por compatibilidad.

## Actualización 2026

El importador lee directamente las planillas oficiales DNAP, reconcilia el total de recaudación propia con IIBB + Sellos + Automotores + Inmobiliario + Otros, normaliza provincias y genera la capa canónica.

```bash
python3 scripts_regenerate_2026.py \
  --top-source /ruta/top_mensual_2026.xlsx \
  --ron-source /ruta/informacion_consolidada_2026.xlsx
python3 scripts_update_deflator.py
python3 scripts_sync_deflator_html.py
python3 scripts_build_fiscal_output.py
python3 scripts_build_liquidity_risk.py
python3 scripts_build_real_dynamics.py
python3 scripts_build_governor_brief.py
python3 scripts_build_nacion_reclamos.py
python3 scripts_build_government_results.py
python3 scripts_sync_embedded_data.py
```

Los fallbacks embebidos se sincronizan al final para que una falla de red o caché no vuelva a mostrar cifras antiguas.

## Controles de calidad

```bash
python3 scripts_validate_reclamos_nacion.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Las pruebas cubren reconciliaciones, universo y ranking, identidad RON, composición tributaria, IPC, deuda PBA, separación trimestre/LTM, falta de inferencias de caja/aguinaldo y navegación modular.

La solapa **Resultados de gobierno** no calcula un puntaje político general. Separa resultados sociales, carencias estructurales y gasto por habitante. Aprender se publica para las 24 jurisdicciones, pero Neuquén y Santa Cruz quedan fuera del ranking educativo por participación estudiantil inferior al 50%.

## Límites de decisión todavía abiertos

- Caja consolidada y fondos con afectación específica.
- Cobertura exacta de salarios y aguinaldo.
- Vencimientos de capital e intereses a 90/180 días.
- Transferencias automáticas necesarias para completar el gasto rígido total.
- Series mensuales 2025 homogéneas para medir variaciones reales 2026 en todas las provincias.

Los escenarios 90/180 días permanecen deshabilitados mientras esos datos sigan faltando; no se presentan como proyecciones de caja.

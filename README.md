# Tablero fiscal de provincias

Tablero político-fiscal orientado a un decisor no técnico. La portada prioriza Buenos Aires y separa cinco preguntas: diagnóstico, solvencia y deuda, ingresos y gasto, relación con Nación y comparación interprovincial.

## Cortes vigentes

- Resultados y ranking homogéneo: últimos 12 meses al 31/03/2026, 23 jurisdicciones. La Pampa no integra el informe 1816 1T26.
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
- Selector de últimos 12 meses o trimestre para el resultado PBA.
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

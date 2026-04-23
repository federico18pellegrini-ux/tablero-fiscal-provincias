# C. Decisiones metodológicas finales

## 1) Definición final de rigidez salarial
**Definición adoptada:** `gasto en personal / gasto primario (ex SS)`.

- Campo operativo: `gasto_salarios_gasto_primario_ex_ss_pct`.
- Corte: estructural (3T 2025), no caja 2026.
- Uso: comparabilidad interprovincial estructural.
- Regla de prudencia: no extrapolar automáticamente a diagnóstico de liquidez/SAC 2026.

## 2) Definición final de cobertura/liquidez observada
**Definición adoptada:** `liquidez parcial observada`.

Incluye solo señales observadas/derivadas con respaldo parcial (depósitos disponibles cuando existan, servicios de deuda observados, composición de servicios, RON mensual/diario de control).

**Prohibición metodológica activa:**
- no afirmar “aguinaldo cubierto / no cubierto”
- no afirmar “faltan X meses”
si no existe base completa de Tesorería + Letras + vencimientos + flujo salarial.

## 3) Regla de comparabilidad por módulo
- **Módulo estructural 1816 (3T2025):** universo comparable restringido (jurisdicciones con dato estructural completo).
- **Módulo RON anual:** universo nacional (24 jurisdicciones) con reglas de disponibilidad propias del módulo.
- **Módulo dinámico mensual 2026:** comparabilidad por cobertura efectiva (mes/provincia), sin forzar universo único.

## 4) Regla de ceros vs faltantes
- Cero solo se muestra cuando está auditado como valor económico real.
- Si el cero proviene de no cierre/no carga, se recodifica como faltante (`null`) y se rotula:
  - `mes no cerrado` (faltante general),
  - `dato faltante específico` (faltante por jurisdicción/tributo).
- Nunca completar faltantes con cero.

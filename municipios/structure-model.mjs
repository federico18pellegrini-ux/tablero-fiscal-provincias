export const isNumber = value => typeof value === 'number' && Number.isFinite(value);

// Size is a transparent starting point, not a claim of identical responsibilities.
export function populationPeers(selected, rows, limit = 5) {
  const population = selected.poblacion_2022;
  if (!isNumber(population) || population <= 0) return [];
  return rows.filter(m => m.id !== selected.id && isNumber(m.poblacion_2022) &&
    m.poblacion_2022 >= population / 2 && m.poblacion_2022 <= population * 2)
    .sort((a, b) => Math.abs(Math.log(a.poblacion_2022 / population)) - Math.abs(Math.log(b.poblacion_2022 / population)) || a.id.localeCompare(b.id))
    .slice(0, limit);
}

export function peerMedian(rows, value) {
  const values = rows.map(value).filter(isNumber).sort((a, b) => a - b);
  const n = values.length;
  return {n, value: n < 3 ? null : (values[Math.floor((n - 1) / 2)] + values[Math.floor(n / 2)]) / 2};
}

export function comparableFiscalResult(m) {
  return m.fiscal?.inicio === '2026-01-01' && m.fiscal?.fin === '2026-06-30'
    ? m.fiscal.resultado_sobre_ingresos_pct : null;
}

export function workforceDisplay(workforce) {
  if (!workforce) return {label: 'Personal municipal', value: null, partial: false};
  const labels = {o: 'Personas en la nómina', c: 'Cargos presupuestados', x: 'Cargos ocupados · RAFAM'};
  return {label: labels[workforce.type], value: isNumber(workforce.total) ? workforce.total : null,
    partial: !isNumber(workforce.total)};
}

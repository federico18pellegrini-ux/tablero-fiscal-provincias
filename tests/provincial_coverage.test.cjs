const test=require('node:test'),assert=require('node:assert/strict');
const {build}=require('../provincial-coverage.js');
test('coverage uses official PBA ratios even when duplicate liquidity panel is hidden',()=>{
 const pbaDebt={latest_official_indicators:{cutoff:'2026-06-30',interest_paid_to_total_resources_pct:3.7,debt_service_paid_to_total_resources_pct:10.3,debt_to_total_resources_pct:45.5}};
 const r=build({province:'Buenos Aires',pbaDebt,dynamics:{own_revenue:{status:'calculated',real_ytd_pct:-2.5,ytd_available_through:'2026-07'}}});
 assert.equal(r.bloques[3].estado,'COMPLETO');assert.match(r.bloques[3].motivo,/2026-06-30/);
 assert.equal(r.bloques[1].estado,'PARCIAL');assert.match(r.bloques[1].motivo,/gasto primario/);
 assert.ok(r.campos_criticos_faltantes.length>0);
});
test('an estimate is identified without treating it as missing; another province cannot complete this one',()=>{
 const rows=[{provincia:'Buenos Aires',bloque:'Dependencia de transferencias Nación',tipo_dato:'estimación oficial',kpi:'Aporte'},{provincia:'CABA',bloque:'Perfil de deuda',tipo_dato:'numérico',kpi:'Stock'}];
 const r=build({province:'Buenos Aires',rows});assert.equal(r.bloques[4].estado,'COMPLETO');assert.equal(r.bloques[2].estado,'PARCIAL');
});

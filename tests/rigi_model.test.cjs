const test=require('node:test'),assert=require('node:assert/strict');
const M=require('../nacion/rigi-model.js'),d=require('../nacion/data/rigi-estimate.json');
test('browser matches published customs scenarios and preserves unknown versus zero',()=>{
  for(const r of d.customs.scenarios)assert.ok(Math.abs(M.customsCost(7827,r.import_share,r.incremental_share,r.tariff)-r.cost_usd_millions)<1e-9);
  assert.equal(M.customsCost(7827,.35,0,.07),0);
  for(const x of [null,'0.5',NaN,Infinity,-1,1.1])assert.equal(M.customsCost(7827,.35,x,.07),null);
  assert.equal(d.total_estimated_cost_2027,null);assert.equal(d.official_fiscal_cost_2027,null);
});

const test=require('node:test'),assert=require('node:assert/strict');
const {fiscalExecutionRatios,proposalCost}=require('../budget-execution.js');
const {currentBudgetRatio}=require('../verified-management.js');
test('RON real change retains its own cutoff when nominal coverage advances',()=>{
 const html=require('node:fs').readFileSync(require('node:path').join(__dirname,'../index.html'),'utf8');
 const block=html.slice(html.indexOf('  const ronReal='),html.indexOf("  const ronPeriod="));
 const run=metric=>require('node:vm').runInNewContext(block+';({value:ronVar,period:ronRealPeriod})',{realDynamics:{provinces:{PBA:{metrics:{ron_total:metric}}}},province:'PBA',toN:x=>x==null?null:Number(x),fullMonthLabel:x=>x});
 const result=run({real_ytd_pct:-.9,ytd_available_through:'2026-08'});
 assert.equal(result.value,-.9);assert.equal(result.period,'Enero–2026-08');
 assert.equal(run({real_ytd_pct:-.9}).value,null);
 const card=html.match(/\{label:'Variación RON 2026 vs 2025 \(%\)'[^\n]+/)[0];
 assert.match(card,/period:ronRealPeriod\+/);
});

test('current credit ratios retain accounting stage and missing values',()=>{
 assert.equal(currentBudgetRatio({credit_ars_m:100,accrued_ars_m:null,committed_ars_m:null}),null);
 assert.equal(currentBudgetRatio({credit_ars_m:0,accrued_ars_m:10}),null);
 assert.deepEqual(currentBudgetRatio({credit_ars_m:100,accrued_ars_m:30,committed_ars_m:50}),{value:30,basis:'devengado'});
 assert.deepEqual(currentBudgetRatio({credit_ars_m:100,accrued_ars_m:null,committed_ars_m:50}),{value:50,basis:'compromiso'});
 assert.deepEqual(currentBudgetRatio({credit_ars_m:100,accrued_ars_m:0}),{value:0,basis:'devengado'});
 assert.deepEqual(currentBudgetRatio({credit_ars_m:100,accrued_ars_m:120}),{value:120,basis:'devengado'});
});
test('ratios preserve missing data, deficit and zero balance',()=>{
 assert.equal(fiscalExecutionRatios({income:null,spending:100,capital:10}),null);
 assert.equal(fiscalExecutionRatios({income:0,spending:100,capital:10}),null);
 assert.deepEqual(fiscalExecutionRatios({income:100,spending:120,capital:30}),{balance:-20,capital:25});
 assert.equal(fiscalExecutionRatios({income:100,spending:100,capital:0}).balance,0);
});
test('costs distinguish startup, recurring and funding without blank assumptions',()=>{
 const v={quantity:100,unit:.2,months:6,startup:10,funding:40};
 assert.deepEqual(proposalCost(v),{recurring:120,total:130,gap:90});
 assert.equal(proposalCost({...v,funding:200}).gap,0);
 for(const patch of [{unit:null},{months:0},{months:13},{months:1.5},{funding:-1},{quantity:Infinity}])assert.equal(proposalCost({...v,...patch}),null);
 assert.deepEqual(proposalCost({quantity:0,unit:0,months:1,startup:0,funding:0}),{recurring:0,total:0,gap:0});
});

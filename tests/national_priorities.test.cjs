const test=require('node:test');
const assert=require('node:assert/strict');
const M=require('../nacion/priorities-model.js');
const B=require('../nacion/data/budget.json');
const G=require('../nacion/data/gestion.json');
const H=require('../nacion/data/benefits.json');
const near=(a,b,t=1e-6)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);

test('all 29 functions use the same denominator and initial/current totals reconcile',()=>{
  const m=M.comparisons(B,G,'amendments');
  assert.equal(m.rows.length,29);assert.equal(new Set(m.rows.map(r=>r.id)).size,29);
  near(m.total.before,B.total.law,.02);near(m.total.after,B.total.current,.02);
  near(m.rows.reduce((s,r)=>s+r.shareAfter,0),100);
  near(m.rows.reduce((s,r)=>s+r.shareChange,0),0);
});
test('intelligence function does not substitute or add the SIDE program',()=>{
  const r=M.comparisons(B,G,'amendments').rows.find(r=>r.id==='2-12');
  near(r.after,372552.250782);near(r.before,288930.537429);
  const side=B.programs.find(p=>p.id==='p44');
  near(side.current,176915.846746);assert.ok(r.after>side.current);
  near(M.change(side.current,side.law),82.1332,1e-5);
});
test('execution uses full matched months and observed monthly deflation',()=>{
  const model=M.comparisons(B,G,'execution');
  assert.equal(model.rows.filter(r=>r.change!==null).length,29);
  near(model.total.after,G.execution.functions_comparison.reduce((s,r)=>s+r.credito_devengado_real_agosto2026_2026,0));
  const intel=model.rows.find(r=>r.id==='2-12');near(intel.after,228915.62002183);
  const r=model.rows.find(r=>r.id==='1-1');
  near(r.before,394357.83383495);near(r.after,381661.67835499);
  near(r.change,-3.21945056,1e-7);
  assert.notEqual(r.after,B.functions.find(f=>f.id===r.id).accrued);
});
test('project can be compared to each of three annual bases, using annual mean inflation',()=>{
  for(const base of ['law','current','closing']){
    const r=M.comparisons(B,G,'project',base).rows.find(r=>r.id==='2-12');
    const f=B.functions.find(f=>f.id===r.id);
    near(r.change,((f.project/f[base])/(B.deflator.annual_average_index['2027']/B.deflator.annual_average_index['2026'])-1)*100);
  }
  assert.notEqual(M.comparisons(B,G,'project','current').total.change,M.comparisons(B,G,'project','closing').total.change);
});
test('missing and zero bases cannot manufacture percentage changes or total shares',()=>{
  assert.equal(M.change(1,0),null);assert.equal(M.change(null,10),null);
  const b=structuredClone(B);b.functions[0].current=null;
  const m=M.comparisons(b,G,'amendments');assert.equal(m.total.after,null);
  assert.equal(m.rows[0].delta,null);assert.equal(m.rows[1].shareAfter,null);
  assert.equal(M.ranked(m.rows).at(-1).id,b.functions[0].id);
});
test('benefits preserve nominal September without inventing observed September inflation',()=>{
  assert.equal(H.rows.length,32);assert.equal(H.meta.latest_real,'2026-08');
  assert.equal(H.rows.at(-1).ipc,null);
  assert.equal(M.benefitChange(H.rows,'2025-08','2026-09','auh'),null);
  assert.equal(H.rows.find(r=>r.period==='2024-01'),undefined);
});
test('minimum and bonus are summed; official table typos do not enter the result',()=>{
  assert.equal(H.rows.at(-1).minimum_bonus,498633);
  assert.equal(H.rows.find(r=>r.period==='2026-03').minimum_bonus,439601);
  for(const r of H.rows)assert.equal(r.minimum_bonus,r.minimum+r.bonus);
  const dec=H.rows.find(r=>r.period==='2023-12');assert.equal(dec.bonus,55000);assert.equal(dec.auh,20661);
});
test('a nominally frozen bonus loses purchasing power, separately from minimum and AUH',()=>{
  const a=H.rows.find(r=>r.period==='2025-08'),b=H.rows.find(r=>r.period==='2026-08');
  assert.equal(a.bonus,b.bonus);assert.ok(b.ipc>a.ipc);
  near(M.benefitChange(H.rows,a.period,b.period,'bonus'),(a.ipc/b.ipc-1)*100);
  assert.ok(M.benefitChange(H.rows,a.period,b.period,'minimum_bonus')<M.benefitChange(H.rows,a.period,b.period,'minimum'));
  near(M.benefitIndex(H.rows,a.period,'auh')[0].value,100);
});
test('priorities is an independent navigable page',()=>{
  assert.equal(require('../nacion/math.js').pageForAnchor('prioridades'),'prioridades');
});

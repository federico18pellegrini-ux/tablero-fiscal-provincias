const test=require('node:test');
const assert=require('node:assert/strict');
const D=require('../nacion/data/budget.json');
const M=require('../nacion/math.js');
const sum=(rows,key)=>rows.reduce((a,r)=>a+(r[key]??0),0);
const near=(a,b,t=.03)=>assert.ok(Math.abs(a-b)<=t,`${a} != ${b} (tol ${t})`);

test('ONP annex totals reconcile independently across all views without double counting',()=>{
  const total=202101433;
  for(const name of ['jurisdictions','geographies','programs','functions','purposes','topics'])near(sum(D[name],'project'),total,D[name].length*.51);
  near(sum(D.works,'project'),1317609,D.works.length*.51);
  near(sum(D.resources,'project'),202348174,5);
  assert.equal(D.works.length,435);assert.equal(D.programs.length,394);
});
test('all current-year groupings reconcile with the independently downloaded PA total',()=>{
  for(const k of ['law','current','accrued'])for(const name of ['jurisdictions','geographies','functions','purposes','topics'])near(sum(D[name],k),D.total[k]);
  near(D.total.current,152474968.840416);
});
test('topics form a partition of official functions',()=>{
  const ids=D.topics.flatMap(t=>t.functions);
  assert.equal(ids.length,29);assert.equal(new Set(ids).size,29);
  assert.deepEqual([...ids].sort(),D.functions.map(f=>f.id).sort());
});
test('each province project list matches its own PDF subtotal within rounding',()=>{
  for(const g of D.works_geographies){const rows=D.works.filter(w=>w.province===g.name);near(sum(rows,'project'),g.project,Math.max(1,rows.length*.51));}
  const pba=D.works.filter(w=>w.province==='Buenos Aires');assert.equal(pba.length,72);near(sum(pba,'project'),321085,36);
});
test('missing geographic and institutional correspondences never turn into zero',()=>{
  const exterior=D.geographies.find(r=>r.name==='Exterior'),unc=D.geographies.find(r=>r.name==='No clasificado · 2026');
  assert.equal(exterior.current,null);assert.equal(unc.project,null);assert.ok(unc.current>0);
  assert.equal(D.jurisdictions.find(r=>r.name==='Ministerio del Interior').project,null);
});
test('unique program keys and withheld ambiguous matches',()=>{
  assert.equal(new Set(D.programs.map(p=>p.id)).size,D.programs.length);
  const matched=D.programs.filter(p=>p.matched);assert.equal(matched.length,D.meta.program_join_matched);
  for(const p of D.programs.filter(p=>!p.matched)){assert.equal(p.current,null);assert.equal(p.accrued,null);}
  const revisions=D.programs.filter(p=>p.name==='Revisión de Cuentas Nacionales');
  assert.equal(revisions.length,2);assert.ok(revisions.every(p=>p.matched));
  assert.deepEqual(revisions.map(p=>p.current_key),[[1,312,22],[1,313,23]]);
  assert.deepEqual(revisions.map(p=>p.project_code),[22,23]);
});
test('monthly flows reconcile with yearly accrued totals by jurisdiction and nationally',()=>{
  for(const r of D.execution){const target=r.name==='Total'?D.total:D.jurisdictions.find(j=>j.name===r.name);near(sum(r.months,'accrued'),target.accrued);near(r.current,target.current);}
  near(sum(D.execution.slice(1),'current'),D.total.current);
});
test('September remains a partial month without an invented observed CPI',()=>{
  assert.equal(D.meta.execution_cutoff,'2026-09-15');
  for(const r of D.execution){assert.equal(r.months.at(-1).month,9);assert.equal(r.months.at(-1).partial,true);assert.equal(r.months.at(-1).real,null);assert.ok(r.months.slice(0,-1).every(m=>!m.partial&&M.finite(m.real)));}
});
test('real annual amounts use an annual average, not December CPI',()=>{
  const ipc=D.deflator.monthly_index;
  for(const year of [2026,2027]){
    const avg=Array.from({length:12},(_,i)=>ipc[`${year}-${String(i+1).padStart(2,'0')}`]).reduce((a,b)=>a+b,0)/12;
    near(avg,D.deflator.annual_average_index[year],1e-7);
    near(D.deflator.annual_factors[year],ipc['2026-08']/avg,1e-10);
    assert.notEqual(avg,ipc[`${year}-12`]);
  }
  near(ipc['2027-12']/ipc['2026-12'],1.18,1e-10);
});
test('a nominal increase can become a real cut; shares and nominal execution remain unchanged',()=>{
  assert.equal(M.change(110,100),10.000000000000014);
  assert.ok(M.change(M.price(110,2027,'real',{'2027':.8}),M.price(100,2026,'real',{'2026':1}))<0);
  const ex=D.execution[0],nominal=M.ratio(sum(ex.months,'accrued'),ex.current);
  near(nominal,69.10324286,.00001);
  near(M.ratio(M.price(50,2027,'real',D.deflator.annual_factors),M.price(100,2027,'real',D.deflator.annual_factors)),50);
});
test('zero, missing values and percentage points have separate meanings',()=>{
  for(const v of [null,undefined,NaN])assert.equal(M.change(v,100),null);
  assert.equal(M.change(100,0),null);assert.equal(M.change(0,100),-100);
  assert.equal(M.price(null,2027,'real',D.deflator.annual_factors),null);
  assert.equal(M.shareChange(40,100,35,100),5);
});
test('sources have official URLs and immutable content fingerprints',()=>{
  for(const s of D.sources){assert.match(s.url,/^https:\/\/(www\.mecon\.gob\.ar|dgsiaf-repo\.mecon\.gob\.ar)\//);assert.match(s.sha256,/^[a-f0-9]{64}$/);assert.ok(s.bytes>0);}
  for(const p of [...D.programs,...D.works]){assert.ok(p.page>0);assert.ok(D.sources.some(s=>s.file===p.source));}
});
test('CSV preserves decimals, blank missing fields and quotes',()=>{
  assert.equal(M.csvCell(null),'""');assert.equal(M.csvCell('A "B"'),'"A ""B"""');assert.equal(M.csvCell(1.25),'"1.25"');
});
test('common searches find the official program wording',()=>{
  assert.ok(D.programs.filter(p=>M.searchText(p).includes('universidades')).some(p=>p.name==='Desarrollo de la Educación Superior'));
  assert.ok(D.programs.filter(p=>M.searchText(p).includes('anses')).some(p=>p.name==='Prestaciones Previsionales'));
});

test('legacy deep links resolve to a visible view and unknown anchors safely open Panorama',()=>{
  for(const name of ['distribucion','comparacion','cambios','programas','finalidades'])assert.equal(M.pageForAnchor(name),'gasto');
  assert.equal(M.pageForAnchor('macro'),'economia');assert.equal(M.pageForAnchor('obras'),'obras');
  assert.equal(M.pageForAnchor('ejecucion'),'ejecucion');assert.equal(M.pageForAnchor('metodo'),'metodo');
  for(const name of ['','desconocido','__proto__','toString'])assert.equal(M.pageForAnchor(name),'panorama');
});
test('overview contrasts nominal and real changes against the selected base while keeping execution fixed',()=>{
  const current=M.budgetOverview(D.total,'current',D.deflator.annual_factors),closing=M.budgetOverview(D.total,'closing',D.deflator.annual_factors);
  near(current.nominalChange,32.547,.001);near(current.realChange,10.001,.01);
  assert.ok(closing.realChange<current.realChange);near(current.execution,closing.execution);
  const fall=M.budgetOverview({project:110,current:100,accrued:50},'current',{'2026':1,'2027':.8});
  assert.ok(fall.nominalChange>0);assert.ok(fall.realChange<0);assert.equal(fall.execution,50);
});

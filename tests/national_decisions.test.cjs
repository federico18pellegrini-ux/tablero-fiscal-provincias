const test=require('node:test'),assert=require('node:assert/strict');
const B=require('../nacion/data/budget.json'),D=require('../nacion/data/decisions.json');
const M=require('../nacion/math.js'),N=require('../nacion/decision-model.js');
const P=require('../nacion/planning-model.js'),monthly=require('../nacion/data/gestion/gasto_mensual_funcion.json');
const near=(a,b,t=.001)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
test('integrated scenario reconciles all funding and fiscal flows at official baseline',()=>{
 const o={inflation:(B.deflator.annual_average_index['2027']/B.deflator.annual_average_index['2026']-1)*100,growth:4,elasticity:1,pensionPass:100,otherPass:0,interestChange:0,financing:100};
 const r=P.integrated(B,D,o);near(r.balance,246741);near(r.need,324050562);near(r.gap,0);near(r.primary,r.balance+r.interest);
 const stress=P.integrated(B,D,{...o,growth:2,financing:90});assert(stress.resources<r.resources);assert(stress.gap>32405056);near(stress.gap,stress.need-stress.available);
 const inflation=P.integrated(B,D,{...o,inflation:30});assert(inflation.pensions>r.pensions);near(inflation.otherPrimary,r.otherPrimary);near(inflation.otherRevenue,r.otherRevenue);
 const interest=P.integrated(B,D,{...o,interestChange:10});near(interest.need-r.need,r.interest*.1);
 for(const bad of [{growth:null},{elasticity:4},{financing:151},{pensionPass:-1},{inflation:NaN}])assert.equal(P.integrated(B,D,{...o,...bad}),null);
});
test('closing forecast preserves actual months, seasonality and excludes partial September',()=>{
 const o={monthlyInflation:1.55,pace:0},r=P.closing(B,monthly,o);assert.equal(r.groups.length,29);near(r.observed,101224608.370245);near(r.total,161754185.478218);
 near(r.total,r.observed+r.remaining);near(r.total,r.months.reduce((s,x)=>s+x.value,0));assert.equal(r.months.filter(r=>r.observed).length,8);
 const tampered=monthly.map(r=>r.periodo==='2026-09'?{...r,credito_devengado:1e15}:r);near(P.closing(B,tampered,o).total,r.total);
 const high=P.closing(B,monthly,{...o,pace:10});near(high.observed,r.observed);near(high.remaining,r.remaining*1.1);
 assert.equal(P.closing(B,monthly.slice(1),o),null);assert.equal(P.closing(B,monthly,{...o,monthlyInflation:null}),null);
 const names=monthly.map(r=>r.anio===2025?{...r,funcion_desc:'Previous denomination'}:r);near(P.closing(B,names,o).total,r.total);
 assert.equal(M.pageForAnchor('normas'),'actos');
});
test('habitual terms and multiple accented words find the intended official program',()=>{
  for(const [q,id] of [['vacunas','p297'],['VACUNACIÓN salud','p297'],['universidades','p350']])assert.ok(B.programs.filter(p=>M.matchesSearch(p,q)).some(p=>p.id===id));
  const retirement=B.programs.filter(p=>M.matchesSearch(p,'jubilaciones'));
  assert.ok(retirement.some(p=>p.name==='Prestaciones Previsionales'));
  assert.ok(retirement.every(p=>/previsionales|jubilaciones/i.test(p.name+' '+p.entity)));
  assert.equal(M.matchesSearch(B.programs[0],'zzzzinexistente'),false);
});
test('all bases are shown simultaneously without inventing a program closing estimate',()=>{
  const total=M.comparisonRows(B.total,B.deflator.annual_factors);
  near(total[1].real,10.009724);near(total[2].real,3.908370);
  const vaccine=M.comparisonRows(D.policies[0].program,B.deflator.annual_factors);
  near(vaccine[0].real,42.662761);near(vaccine[1].real,-26.951375);
  assert.equal(vaccine[2].real,null);assert.equal(vaccine[2].nominal,null);
  near(vaccine[1].nominal,-11.985990);
});
test('partial physical records remain labelled and missing values are never a zero outcome',()=>{
  const vaccines=D.policies[0];const doses=vaccines.physical.find(r=>r.medicion_fisica_id===1110);
  const v=N.physicalValue(doses);near(v.change,-3.925379,.0001);assert.equal(v.partial,false);
  assert.ok(vaccines.physical.some(r=>N.physicalValue(r).partial));
  const missing=D.policies[1].physical.find(r=>r.ejecutado_acumulado_trim2===null);
  assert.equal(N.physicalValue(missing).actual,null);assert.equal(N.physicalValue(missing).change,null);
  const zero={...doses,ejecutado_acumulado_trim2:0};assert.equal(N.physicalValue(zero).change,-100);
  assert.equal(N.physicalValue({...doses,programacion_acumulada_trim2:0}).change,null);
});
test('payments and coverage use their documented program scope',()=>{
  const v=N.policyStats(D.policies[0]),u=N.policyStats(D.policies[1]);
  near(v.unpaid,17912.108039);near(v.execution,36.597);assert.equal(v.count,14);
  assert.equal(u.count,13);assert.equal(u.reported,7);assert.equal(u.comparable,6);
});
test('stale policy packages are blocked and new routes preserve old navigation',()=>{
  assert.equal(N.inputMatches(D,D.meta.inputs['nacion/data/budget.json']),true);
  assert.equal(N.inputMatches(D,'wrong'),false);assert.equal(N.inputMatches(D,null),false);
  assert.equal(M.pageForAnchor('financiamiento'),'economia');
  for(const slug of D.policies.map(p=>p.slug))assert.equal(M.pageForAnchor('politica-'+slug),'politicas');
  assert.equal(M.pageForAnchor('programas'),'gasto');assert.equal(M.pageForAnchor('__proto__'),'panorama');
  assert.equal(M.pageForAnchor('escenarios'),'economia');assert.equal(M.pageForAnchor('obra-ra10'),'obra-ficha');
});

test('scenarios reproduce the annual base and separate revenue stress from uncovered principal',()=>{
  const rows=Object.fromEntries(D.finance.rows.map(r=>[r.id,r.project]));
  const options={project:B.total.project,base:B.total.current,resources:rows.VI,expenses:rows.VII,capital:rows['XIII.2'],inflation:(B.deflator.annual_average_index['2027']/B.deflator.annual_average_index['2026']-1)*100,revenueDrop:0,coverage:100};
  const initial=N.scenario(options);near(initial.realChange,10.009724);near(initial.balance,246741);assert.equal(initial.uncovered,0);
  const stressed=N.scenario({...options,revenueDrop:1,coverage:90});near(stressed.balance,-1776740.74);near(stressed.uncovered,30686492.9);
  assert.ok(N.scenario({...options,inflation:30}).realChange<initial.realChange);
  for(const bad of [{inflation:null},{coverage:101},{revenueDrop:-1},{base:0},{inflation:Infinity}])assert.equal(N.scenario({...options,...bad}),null);
});

test('funding filters include mixed projects without counting subtotal columns twice',()=>{
  const rows=D.works.rows;
  assert.equal(rows.filter(w=>N.fundingMatches(w.funding,'all')).length,435);
  const external=rows.filter(w=>N.fundingMatches(w.funding,'external'));
  assert.ok(external.length>0&&external.length<435);
  assert.equal(N.fundingMatches(undefined,'external'),false);
  assert.equal(N.fundingMatches({externas:0,tesoro:100},'internal'),true);
  assert.equal(N.fundingMatches({externas:10,tesoro:100},'internal'),false);
  assert.equal(N.fundingMatches({externas:10,tesoro:100},'treasury'),true);
});
const R=require('../nacion/data/revenue-planning.json');
test('revenue forecast preserves observations and never rolls BCRA profits into recurring income',()=>{
 const o={monthlyInflation:1.55,revenuePace:0,bcraFuture:0},r=P.revenue(R,o);
 near(r.observed,128822516.26388761);near(r.bcraObserved,24400000);near(r.total,183324830.67410213);near(r.total,r.withoutBcra+r.bcraObserved);
 near(r.months.reduce((s,x)=>s+x.value,0),r.total);assert.equal(r.months.filter(x=>x.observed).length,8);
 const noBcra={...R,months:R.months.map(m=>({...m,total:m.total-m.bcra,bcra:0}))};const without=P.revenue(noBcra,o);near(without.remaining,r.remaining);near(without.total,r.withoutBcra);
 const extra=P.revenue(R,{...o,bcraFuture:1});near(extra.total-r.total,1e6);near(extra.unallocatedFuture,1e6);near(extra.withoutBcra,r.withoutBcra);
 near(extra.months.reduce((s,x)=>s+x.value,0)+extra.unallocatedFuture,extra.total);
});
test('revenue stresses affect only future ordinary flows and missing inputs are not zero',()=>{
 const o={monthlyInflation:1.55,revenuePace:0,bcraFuture:0},r=P.revenue(R,o),stress=P.revenue(R,{...o,revenuePace:-10});
 near(stress.observed,r.observed);near(stress.bcraObserved,r.bcraObserved);near(stress.remaining,r.remaining*.9);
 assert.equal(P.revenue({...R,months:R.months.slice(1)},o),null);
 const incomplete={...R,months:R.months.map((m,i)=>i?m:{...m,groups:m.groups.slice(1)})};assert.equal(P.revenue(incomplete,o),null);
 for(const bad of [{bcraFuture:null},{revenuePace:NaN},{monthlyInflation:-1},{bcraFuture:101}])assert.equal(P.revenue(R,{...o,...bad}),null);
 const partial={...R,months:[...R.months,{period:'2026-09',total:1e15}]};near(P.revenue(partial,o).total,r.total);
});

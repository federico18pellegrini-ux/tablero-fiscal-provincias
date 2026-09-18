const test=require('node:test'),assert=require('node:assert/strict');
const B=require('../nacion/data/budget.json'),D=require('../nacion/data/decisions.json');
const M=require('../nacion/math.js'),N=require('../nacion/decision-model.js');
const near=(a,b,t=.001)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
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
});

const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {overviewCommittedDescription,overviewServiceMetric}=require('../provincial-overview.js');
test('spending floor never claims free cash or includes zero/unobserved components',()=>{
 const rows=fs.readFileSync('data/gasto_rigido.csv','utf8').trim().split(/\r?\n/);const keys=rows.shift().split(',');
 for(const line of rows){const row=Object.fromEntries(line.split(',').map((v,i)=>[keys[i],v]));const text=overviewCommittedDescription(row);
 assert.match(text,/Como mínimo/);assert.match(text,/otros gastos/);
 assert.equal(text.includes('jubilaciones'),Number(row.social_security_spending_pct)>0,row.province);
 assert.equal(text.includes('transferencias a municipios'),Number(row.automatic_transfers_pct)>0,row.province);
 }
 assert.match(overviewCommittedDescription(null),/Faltan/);
});
test('all 24 jurisdictions show their own verified service metric',()=>{
 const provinces=JSON.parse(fs.readFileSync('data/government_results_provinces.json','utf8')).provinces;
 assert.equal(Object.keys(provinces).length,24);
 for(const [province,row] of Object.entries(provinces)){
 const metric=overviewServiceMetric(row.pillars);assert.ok(metric,province);assert.equal(metric.id,'homicide_rate',province);assert.equal(metric.status,'auditado');assert.equal(metric.direction,'lower_is_better');
 }
 assert.equal(overviewServiceMetric([{indicator_type:'resultado',metrics:[{value:0,display:'0',status:'pendiente'}]}]),null);
 assert.equal(overviewServiceMetric([{indicator_type:'resultado',metrics:[{value:0,display:'0',status:'auditado'}]}]).value,0);
});

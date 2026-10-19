const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('rebasing preserves real growth and makes September pesos the unit',()=>{
 const html=fs.readFileSync('index.html','utf8');
 const original=JSON.parse(html.match(/const DEFLACTOR_MONTH = (\{.*?\});/s)[1]);
 const ctx={};vm.createContext(ctx);
 const code=html.match(/const DEFLACTOR_MONTH = .*?const DEFLACTOR_YEAR = \{\};/s)[0];
 vm.runInContext(code+'; this.factors=DEFLACTOR_MONTH;',ctx);
 assert.ok(Math.abs(ctx.factors['2026-09']-1)<1e-12);
 for(const key of Object.keys(original))assert.ok(Math.abs(ctx.factors[key]/ctx.factors['2026-08']-original[key]/original['2026-08'])<1e-10);
});
test('headline peak uses annual schedule and never treats half-year as full year',()=>{
 const rows=fs.readFileSync('data/debt/pba_debt_service_schedule_2026_2041.csv','utf8').trim().split(/\r?\n/).slice(1).map(x=>x.split(','));
 const annual=rows.filter(x=>+x[0]>=2027);const peak=annual.reduce((a,b)=>+b[3]>+a[3]?b:a);
 assert.equal(+peak[0],2027);assert.equal(+peak[3],3065573);assert.equal(peak[4],'2026-06-30');
});

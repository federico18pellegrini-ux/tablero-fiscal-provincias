const test=require('node:test'),assert=require('node:assert/strict');
const N=require('../nacion/navigation-model.js'),M=require('../nacion/math.js');
test('the dashboard has five canonical sections and each existing root has one home',()=>{
 assert.deepEqual(N.sections.map(s=>s.label),['Resumen','Presupuesto','Ejecución','Territorio','Ingresos y deuda']);
 const roots=N.sections.flatMap(s=>s.views.flatMap(v=>v.roots));assert.equal(new Set(roots).size,roots.length);
 for(const id of roots){const route=N.resolve(id);assert.ok(N.sections.some(s=>s.id===route.section));assert.ok(N.viewFor(id).roots.includes(id));}
});
test('old policy, provincial, financing, RIGI and methodology links remain resolvable',()=>{
 for(const [anchor,section] of Object.entries({inicio:'resumen',comparacion:'presupuesto',cambios:'presupuesto',carteras:'presupuesto','politica-inmunizaciones':'presupuesto',prioridades:'ejecucion','priority-income':'ejecucion',normas:'ejecucion',caja:'ejecucion','historia-ejecucion':'ejecucion',obras:'territorio','obra-ra10':'territorio','provincias-nacion':'territorio','deuda-nacional':'finanzas','rigi-estimation':'finanzas',escenarios:'finanzas',metodo:'finanzas'}))assert.equal(M.pageForAnchor(anchor),section);
 for(const invalid of ['__proto__','constructor','toString','',undefined])assert.deepEqual(N.resolve(invalid),{section:'resumen',view:'overview'});
});
test('each section links to an existing default view and auxiliary sources do not become a sixth section',()=>{
 for(const section of N.sections){const route=N.resolve(section.anchor);assert.equal(route.section,section.id);assert.ok(section.views.some(v=>v.id===route.view));}
 assert.equal(N.viewFor('metodo').auxiliary,true);assert.equal(N.sections.length,5);
 assert.equal(N.resolve('prioridades-2027').section,'presupuesto');
});

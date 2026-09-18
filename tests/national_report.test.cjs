const test=require('node:test');
const assert=require('node:assert/strict');
const {selectReport}=require('../nacion/report.js');
const manifest=require('../nacion/reports/manifest.json');
const hash=manifest.inputs['nacion/data/budget.json'];
const managementHash=manifest.inputs['nacion/data/gestion.json'];

test('exports the selected annual comparison and price basis, with optional full detail',()=>{
  for(const price of ['nominal','real'])for(const base of ['current','law','closing'])for(const annex of [false,true]){
    const result=selectReport(manifest,{price,base,annex},hash,managementHash);
    assert.equal(result.file,`informe-nacional-${price}-${base}${annex?'-anexo':''}.pdf`);
    assert.equal(result.href,'reports/'+result.file+'?v='+result.sha256.slice(0,16));
    assert.equal(result.pages,annex?61:15);
  }
});
test('refuses outdated reports and unexpected paths instead of exporting wrong data',()=>{
  assert.throws(()=>selectReport(manifest,{price:'real',base:'law'},'outdated',managementHash),/actualizando/);
  assert.throws(()=>selectReport(manifest,{price:'real',base:'law'},hash,'old-management'),/actualizando/);
  assert.throws(()=>selectReport(manifest,{price:'real',base:'private'},hash,managementHash),/válidas/);
  const bad=structuredClone(manifest);bad.reports[0].main.file='https://example.com/not-the-report.pdf';
  assert.throws(()=>selectReport(bad,{price:'nominal',base:'current'},hash,managementHash),/validar/);
});

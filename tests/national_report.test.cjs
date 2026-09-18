const test=require('node:test');
const assert=require('node:assert/strict');
const {selectReport}=require('../nacion/report.js');
const manifest=require('../nacion/reports/manifest.json');
const hash=manifest.inputs['nacion/data/budget.json'];
const decisionHash=manifest.inputs['nacion/data/decisions.json'];
const managementHash=manifest.inputs['nacion/data/gestion.json'];

test('exports the selected annual comparison and price basis, with optional full detail',()=>{
  for(const price of ['nominal','real'])for(const base of ['current','law','closing'])for(const annex of [false,true]){
    const result=selectReport(manifest,{price,base,annex},hash,managementHash,decisionHash);
    assert.equal(result.file,`informe-nacional-${price}-${base}${annex?'-anexo':''}.pdf`);
    assert.equal(result.href,'reports/'+result.file+'?v='+result.sha256.slice(0,16));
    assert.equal(result.pages,annex?66:19);
  }
});
test('refuses outdated reports and unexpected paths instead of exporting wrong data',()=>{
  assert.throws(()=>selectReport(manifest,{price:'real',base:'law'},'outdated',managementHash,decisionHash),/actualizando/);
  assert.throws(()=>selectReport(manifest,{price:'real',base:'law'},hash,'old-management',decisionHash),/actualizando/);
  assert.throws(()=>selectReport(manifest,{price:'real',base:'private'},hash,managementHash,decisionHash),/válidas/);
  const bad=structuredClone(manifest);bad.reports[0].main.file='https://example.com/not-the-report.pdf';
  assert.throws(()=>selectReport(bad,{price:'nominal',base:'current'},hash,managementHash,decisionHash),/validar/);
});

test('focused reports stay brief and must match the decisions currently displayed',()=>{
  for(const scope of ['inmunizaciones','educacion-superior','reactor-ra10']){
    const r=selectReport(manifest,{price:'real',base:'closing',annex:true,scope},hash,managementHash,decisionHash);
    assert.equal(r.file,`ficha-nacional-${scope}.pdf`);assert.equal(r.pages,1);
  }
  assert.throws(()=>selectReport(manifest,{price:'nominal',base:'current'},hash,managementHash,'stale'),/actualizando/);
  assert.throws(()=>selectReport(manifest,{price:'nominal',base:'current',scope:'unknown'},hash,managementHash,decisionHash),/válido/);
});

test('every provincial PDF matches its selected code and rejects unknown paths or IDs',()=>{
  assert.equal(manifest.territories.length,24);
  for(const t of manifest.territories){
    const r=selectReport(manifest,{price:'real',base:'closing',scope:'provincia',provinceId:t.province_id},hash,managementHash,decisionHash);
    assert.equal(r.file,`ficha-nacional-provincia-${t.province_id}.pdf`);assert.equal(r.pages,1);
  }
  for(const provinceId of [999,'6',null,undefined])assert.throws(()=>selectReport(manifest,{price:'nominal',base:'current',scope:'provincia',provinceId},hash,managementHash,decisionHash),/provincia válida/);
  const bad=structuredClone(manifest);bad.territories[0].file='../../private.pdf';
  assert.throws(()=>selectReport(bad,{price:'nominal',base:'current',scope:'provincia',provinceId:2},hash,managementHash,decisionHash),/validar/);
});

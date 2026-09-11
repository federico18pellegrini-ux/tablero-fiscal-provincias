import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {webcrypto, createHash} from 'node:crypto';
import {reportModels} from '../scripts_municipal_report_data.mjs';
import {METRICS,metricValue} from '../municipios/model.mjs';
const dashboardText=fs.readFileSync(new URL('../municipios/data/dashboard.json',import.meta.url),'utf8');
const data=JSON.parse(dashboardText),models=reportModels(data);

test('report covers every municipality and all observed months without replacing reserved values',()=>{
  assert.equal(models.length,135);
  for(const m of models){
    const raw=data.municipalities.find(r=>r.id===m.id);
    assert.equal(m.reportRankings.length,METRICS.length);
    assert.deepEqual(m.employment,raw.employment);
    assert.deepEqual(m.transfers,raw.transfers);
    assert.deepEqual(m.sectors,raw.sectors);
    for(const r of m.reportRankings){
      const available=data.municipalities.map(row=>metricValue(row,r)).filter(v=>typeof v==='number'&&Number.isFinite(v));
      assert.equal(r.count,available.length);
      assert.equal(r.rank,r.value===null?null:1+available.filter(v=>r.ascending?v<r.value:v>r.value).length);
    }
  }
});
test('scenarios reconcile the real coparticipation base and retain the complete slider range',()=>{
  for(const m of models){
    assert.equal(m.reportScenarios.length,41);
    for(const [i,s] of m.reportScenarios.entries()){
      assert.equal(s.shock,i/2);
      assert.ok(Math.abs(s.loss-m.copart_2026_ene_jul_ars_jul26*i/200)<.001);
      assert.ok(Math.abs(s.after+s.loss-s.baseline)<.001);
      assert.ok(Math.abs(s.perCapita*m.poblacion_2022-s.loss)<.001);
    }
  }
  assert.ok(Math.abs(models.find(m=>m.id==='06329').reportScenarios[20].loss-444783420.066004)<.001);
});

const source=fs.readFileSync(new URL('../municipios/app.mjs',import.meta.url),'utf8').replace(/^import[^\n]+\n/,'').replace(/\binit\(\);\s*$/,'');
function browserHarness(manifest,failed=false){
  const elements=new Map();
  function element(id){
    if(!elements.has(id))elements.set(id,{attributes:{},textContent:'',setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this[k];delete this.attributes[k];}});
    return elements.get(id);
  }
  const context=vm.createContext({document:{getElementById:element},crypto:webcrypto,TextEncoder,console:{warn(){}},fetch:async()=>({ok:!failed,json:async()=>manifest})});
  vm.runInContext(source,context);
  vm.runInContext(`rows=${JSON.stringify(data.municipalities)};byId=new Map(rows.map(m=>[m.id,m]));state={id:'06329'};`,context);
  return {context,element,prepare:()=>vm.runInContext(`prepareReports(${JSON.stringify(dashboardText)})`,context)};
}
const manifest=JSON.parse(fs.readFileSync(new URL('../municipios/reports/manifest.json',import.meta.url)));
test('download follows the selected municipality, contains the editorial analysis and uses a fingerprinted PDF',async()=>{
  const h=browserHarness(manifest);await h.prepare();
  assert.equal(h.element('export-report').download,'informe-general-las-heras.pdf');
  assert.match(h.element('export-report').href,/informe-06329\.pdf\?v=[a-f0-9]{64}$/);
  vm.runInContext("state.id='06805';updateReportLink(current());",h.context);
  assert.equal(h.element('export-report').download,'informe-tigre.pdf');
  assert.match(h.element('report-scope').textContent,/Tigre.*Análisis y datos principales/);
});
test('stale, duplicate, malformed or unavailable manifests cannot offer a wrong report',async()=>{
  const stale=structuredClone(manifest);stale.input_sha256['municipios/data/dashboard.json']=createHash('sha256').update('old data').digest('hex');
  const duplicate=structuredClone(manifest);duplicate.reports[1]=duplicate.reports[0];
  const wrong=structuredClone(manifest);wrong.reports[0].file='../../other.pdf';
  for(const [value,failed] of [[stale,false],[duplicate,false],[wrong,false],[manifest,true]]){
    const h=browserHarness(value,failed);await h.prepare();
    assert.equal(h.element('export-report').attributes['aria-disabled'],'true');
    assert.equal(h.element('export-report').href,undefined);
    assert.match(h.element('report-scope').textContent,/datos del tablero siguen disponibles/);
  }
});

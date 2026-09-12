import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {webcrypto, createHash} from 'node:crypto';
import {reportModels} from '../scripts_municipal_report_data.mjs';
import {METRICS,metricValue} from '../municipios/model.mjs';
import {validReportEntry,reportSelection,DEFAULT_REPORT_TOPICS,REPORT_TOPICS} from '../municipios/report.mjs';
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

const source=fs.readFileSync(new URL('../municipios/app.mjs',import.meta.url),'utf8').replace(/^import[^\n]+\n/gm,'').replace(/\binit\(\);\s*$/,'');
function browserHarness(manifest,failed=false){
  const elements=new Map();
  function element(id){
    if(!elements.has(id))elements.set(id,{attributes:{},textContent:'',setAttribute(k,v){this.attributes[k]=v;},removeAttribute(k){delete this[k];delete this.attributes[k];}});
    return elements.get(id);
  }
  const context=vm.createContext({document:{getElementById:element},crypto:webcrypto,TextEncoder,DEFAULT_REPORT_TOPICS,REPORT_TOPICS,validReportEntry,console:{warn(){}},fetch:async()=>({ok:!failed,json:async()=>manifest})});
  vm.runInContext(source,context);
  vm.runInContext(`rows=${JSON.stringify(data.municipalities)};byId=new Map(rows.map(m=>[m.id,m]));state={id:'06329'};`,context);
  return {context,element,prepare:()=>vm.runInContext(`prepareReports(${JSON.stringify(dashboardText)})`,context)};
}
const manifest=JSON.parse(fs.readFileSync(new URL('../municipios/reports/manifest.json',import.meta.url)));
test('the report entry point follows the municipality and opens visible content choices',async()=>{
  const h=browserHarness(manifest);await h.prepare();
  assert.equal(h.element('export-report').download,undefined);
  assert.equal(h.element('export-report').href,'?municipio=06329&vista=informe');
  vm.runInContext("state.id='06805';updateReportLink(current());",h.context);
  assert.equal(h.element('export-report').href,'?municipio=06805&vista=informe');
  assert.match(h.element('report-scope').textContent,/Tigre.*3 páginas/);
});
test('stale, duplicate, malformed or unavailable manifests cannot offer a wrong report',async()=>{
  const stale=structuredClone(manifest);stale.input_sha256['municipios/data/dashboard.json']=createHash('sha256').update('old data').digest('hex');
  const duplicate=structuredClone(manifest);duplicate.reports[1]=duplicate.reports[0];
  const wrong=structuredClone(manifest);wrong.reports[0].file='../../other.pdf';
  for(const [value,failed] of [[stale,false],[duplicate,false],[wrong,false],[manifest,true]]){
    const h=browserHarness(value,failed);await h.prepare();
    assert.equal(vm.runInContext('reportManifest',h.context),null);
    assert.equal(vm.runInContext('reportUnavailable',h.context),true);
    assert.doesNotMatch(h.element('export-report').href,/\.pdf/);
  }
});
test('all available topic combinations keep the required diagnosis and correct page counts',()=>{
  for(const entry of manifest.reports){
    assert.equal(validReportEntry(entry),true);
    assert.deepEqual(reportSelection(entry).pages,[0,1,2]);
    assert.equal(reportSelection(entry).mode,'brief');
    assert.equal(reportSelection(entry,REPORT_TOPICS).mode,'full');
    const optional=entry.modules.filter(m=>!m.required);
    for(let bits=0;bits<(1<<optional.length);bits++){
      const chosen=optional.filter((_,i)=>bits&(1<<i)).map(m=>m.id),selected=reportSelection(entry,chosen);
      assert.equal(selected.modules[0].id,'lectura');
      assert.equal(new Set(selected.pages).size,selected.count);
      assert.equal(selected.count,1+optional.filter(m=>chosen.includes(m.id)).reduce((sum,m)=>sum+m.pages.length,0));
      assert.deepEqual(selected.pages,[...selected.pages].sort((a,b)=>a-b));
    }
    assert.deepEqual(reportSelection(entry,['bad','__proto__']).pages,[0]);
  }
});
test('malformed page maps, unavailable briefs and unknown topics cannot offer a PDF',()=>{
  const entry=manifest.reports[0];
  for(const mutate of [r=>r.modules[1].pages=[0],r=>r.modules[1].pages=[999],r=>r.brief.file='../wrong.pdf',r=>r.brief.sha256='bad',r=>r.modules[0].required=false,r=>r.modules[1].id='bad',r=>r.modules[1].default=false]){
    const invalid=structuredClone(entry);mutate(invalid);assert.equal(validReportEntry(invalid),false);assert.throws(()=>reportSelection(invalid));
  }
});

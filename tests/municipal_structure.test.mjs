import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {populationPeers,peerMedian,workforceDisplay,comparableFiscalResult} from '../municipios/structure-model.mjs';

test('partial workforce categories are never added into a fabricated total',()=>{
  const display=workforceDisplay({type:'c',categories:[['permanente',3670]],total:null});
  assert.equal(display.value,null);assert.equal(display.partial,true);
  assert.match(display.label,/presupuestados/);
});
test('population peers exclude self, missing values and municipalities outside the size band',()=>{
  const own={id:'a',poblacion_2022:100};
  const peers=populationPeers(own,[own,{id:'b',poblacion_2022:90},{id:'c',poblacion_2022:1000},{id:'d',poblacion_2022:null},{id:'e',poblacion_2022:110}]);
  assert.deepEqual(peers.map(p=>p.id),['e','b']);
  assert.deepEqual(populationPeers({poblacion_2022:0},[]),[]);
});
test('medians preserve missingness and require three observations',()=>{
  assert.deepEqual(peerMedian([0,null,2],x=>x),{n:2,value:null});
  assert.deepEqual(peerMedian([0,null,2,10],x=>x),{n:3,value:2});
  assert.equal(peerMedian([0,2,10,12],x=>x).value,6);
});
test('fiscal comparisons exclude annual and partial periods',()=>{
  assert.equal(comparableFiscalResult({fiscal:{inicio:'2025-01-01',fin:'2025-12-31',resultado_sobre_ingresos_pct:5}}),null);
  assert.equal(comparableFiscalResult({fiscal:{inicio:'2026-01-01',fin:'2026-06-30',resultado_sobre_ingresos_pct:-2}}),-2);
});
test('external data remains attributed and distinct from verified fiscal accounts',()=>{
  const d=JSON.parse(readFileSync(new URL('../municipios/data/structure.json',import.meta.url)));
  assert.equal(d.municipalities.length,135);assert.equal(d.verification,'external_survey');
  for(const m of d.municipalities){
    for(const x of Object.values(m.indicators)){
      assert.ok(['external_survey','primary_document'].includes(x.verification));assert.ok(x.period);assert.ok(Number.isFinite(x.value));
      assert.ok(x.sources.length);assert.ok(x.sources.every(s=>s.official));
    }
    assert.ok(m.decisions.every(d=>d.url.startsWith('https://sistemas.htc.gba.gov.ar/')));
  }
  assert.equal(d.municipalities.find(m=>m.id==='06805').workforce.total,null);
  for(const m of d.municipalities)for(const x of [m.workforce,...Object.values(m.indicators)]){
    if(!x?.evidence)continue;
    const proof=x.evidence;
    assert.equal(createHash('sha256').update(readFileSync(new URL('../municipios/data/'+proof.file,import.meta.url))).digest('hex'),proof.sha256);
    for(const [key,value] of Object.entries(proof.expected))assert.deepEqual(x[key],value);
  }
});

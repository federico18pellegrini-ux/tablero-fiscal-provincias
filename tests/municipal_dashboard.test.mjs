import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
import {METRICS,metricValue,rankMunicipalities,peers,simulate,readState,csv} from '../municipios/model.mjs';
const require=createRequire(import.meta.url),d3=require('../municipios/vendor/d3.v7.min.js');
const data=JSON.parse(fs.readFileSync(new URL('../municipios/data/dashboard.json',import.meta.url)));
const geometry=JSON.parse(fs.readFileSync(new URL('../municipios/data/geografia_original.geojson',import.meta.url)));
const rows=data.municipalities,metric=id=>METRICS.find(m=>m.id===id);
test('all 135 municipalities join to actual polygons; geometry covers Buenos Aires',()=>{
  assert.equal(rows.length,135);assert.equal(new Set(rows.map(m=>m.id)).size,135);
  assert.deepEqual(new Set(rows.map(m=>m.id)),new Set(geometry.features.map(f=>f.properties.id)));
  assert.ok(geometry.features.every(f=>['Polygon','MultiPolygon'].includes(f.geometry.type)));
  const [[x0,y0],[x1,y1]]=d3.geoBounds(geometry);assert.ok(x0>-64&&x1<-56&&y0>-42&&y1<-32);
});
test('real transfer change reconciles to published research and months stay comparable',()=>{
  for(const m of rows){assert.equal(m.transfers.length,19);assert.equal(m.employment.length,84);const total=year=>m.transfers.filter(r=>r[0].startsWith(year)&&Number(r[0].slice(5))<=7).reduce((s,r)=>s+r[1],0);assert.ok(Math.abs((total('2026')/total('2025')-1)*100-m.variacion_transferencias_real_pct)<.00001);assert.ok(Math.abs(m.efecto_masa_observada_ars_jul26+m.efecto_participacion_observada_ars_jul26-(m.copart_2026_ene_jul_ars_jul26-m.copart_2025_ene_jul_ars_jul26))<.1);}
  assert.equal(rows.filter(m=>m.caen_empleo_y_transferencias_misma_ventana_2025_vs2024).length,41);
});
test('reserved observations never become zeros or ranking positions',()=>{
  assert.equal(rankMunicipalities(rows,metric('industria')).length,131);
  assert.equal(rankMunicipalities(rows,metric('industria-cambio')).length,130);
  assert.equal(rankMunicipalities(rows,metric('credito')).length,106);
  assert.equal(rankMunicipalities(rows,metric('poblacion')).length,133);
  assert.equal(rankMunicipalities(rows,metric('deficit')).length,3);
  const missing=rows.find(m=>!m.fiscal);assert.equal(metricValue(missing,metric('deficit')),null);
});
test('ranking preserves ties and recomputes within the chosen population cohort',()=>{
  const meta={field:'v',ascending:true},sample=[{municipio:'A',v:2},{municipio:'B',v:2},{municipio:'C',v:4},{municipio:'D',v:null}];
  assert.deepEqual(rankMunicipalities(sample,meta).map(r=>r.rank),[1,1,3]);
  const selected=rows.find(m=>m.id==='06805'),cohort=peers(rows,selected,true);assert.ok(cohort.some(m=>m.id===selected.id));assert.ok(cohort.length<135);assert.ok(cohort.every(m=>m.poblacion_2022>=selected.poblacion_2022/2&&m.poblacion_2022<=selected.poblacion_2022*2));
});
test('simulation uses gross coparticipation and remains bounded, per capita reconciles',()=>{
  const m=rows.find(m=>m.id==='06427'),s=simulate(m,20);assert.ok(Math.abs(s.loss-35603549875.6)<1);assert.ok(Math.abs(s.after+s.loss-s.baseline)<.001);assert.equal(s.perCapita,s.loss/m.poblacion_2022);assert.equal(simulate(m,-10).loss,0);assert.equal(simulate(m,100).shock,20);assert.equal(simulate(m,'bad').shock,0);
});
test('direct links reject unknown state and CSV preserves missing values',()=>{
  const s=readState('?municipio=bad&vista=bad&indicador=bad',rows);assert.equal(s.id,'06805');assert.equal(s.view,'panorama');assert.equal(s.metric,'recursos');
  assert.equal(readState('?municipio=06427&vista=empleo',rows).id,'06427');
  assert.equal(csv([['Faltante',null]]),'\ufeff"Faltante";""');
});

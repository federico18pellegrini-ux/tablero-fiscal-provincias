import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {METRICS,TRANSPARENCY_COMPONENTS,transparencyStatus,metricValue,rankMunicipalities,peers,simulate,readState,csv,fiscalExportRows,adjustPrice,priceComparisons,municipalContextExportRows} from '../municipios/model.mjs';
const require=createRequire(import.meta.url),d3=require('../municipios/vendor/d3.v7.min.js');
const data=JSON.parse(fs.readFileSync(new URL('../municipios/data/dashboard.json',import.meta.url)));
const geometry=JSON.parse(fs.readFileSync(new URL('../municipios/data/geografia_original.geojson',import.meta.url)));
const rows=data.municipalities,metric=id=>METRICS.find(m=>m.id===id);

test('published input manifest matches the committed text on Windows and Linux',()=>{
  const manifest=JSON.parse(fs.readFileSync(new URL('../municipios/data/build-manifest.json',import.meta.url)));
  for(const input of manifest.repositoryInputs){
    const text=fs.readFileSync(new URL('../'+input.file,import.meta.url),'utf8').replace(/\r\n/g,'\n');
    assert.equal(createHash('sha256').update(text).digest('hex'),input.sha256,input.file);
  }
});
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
  assert.equal(rankMunicipalities(rows,metric('deficit')).length,72);
  const missing=rows.find(m=>!m.fiscal);assert.equal(metricValue(missing,metric('deficit')),null);
});

test('municipal fiscal accounts reconcile without including financing or treating gaps as zero',()=>{
  const audited=rows.filter(m=>m.fiscal);
  assert.equal(data.fiscalCoverage.fiscal,audited.length);
  for(const m of audited){
    const f=m.fiscal;
    assert.equal(f.fin,'2026-06-30');
    assert.match(f.inicio,/^2026-01-0[125]$/);
    assert.ok(Math.abs(f.ingresos_corrientes+f.ingresos_capital-f.ingresos_totales)<.011);
    assert.ok(Math.abs(f.gastos_corrientes+f.gastos_capital-f.gastos_totales)<.011);
    assert.ok(Math.abs(f.ingresos_totales-f.gastos_totales-f.resultado_financiero)<.011);
    assert.ok(Math.abs(f.resultado_financiero/f.ingresos_totales*100-f.resultado_sobre_ingresos_pct)<.00001);
    assert.ok(Math.abs(f.gastos_capital/m.poblacion_2022-f.capital_por_habitante_base2022_ars_corrientes)<.00001);
    if(f.personal_devengado==null)assert.equal(f.personal_sobre_gasto_corriente_pct,null);
    else assert.ok(Math.abs(f.personal_devengado/f.gastos_corrientes*100-f.personal_sobre_gasto_corriente_pct)<.00001);
  }
  for(const id of ['deficit','resultado-pesos','inversion','ahorro-corriente','inversion-habitante'])assert.equal(rankMunicipalities(rows,metric(id)).length,72);
  assert.equal(rankMunicipalities(rows,metric('personal')).length,71);
  const lasHeras=rows.find(m=>m.id==='06329').fiscal;
  assert.equal(lasHeras.ingresos_totales,10441008325.60);
  assert.equal(lasHeras.gastos_totales,8853440358.31);
  assert.equal(lasHeras.resultado_financiero,1587567967.29);
  const martin=rows.find(m=>m.id==='06371').fiscal;
  assert.equal(martin.method,'economic_execution');
  assert.equal(martin.resultado_financiero,14367303346.81);
  assert.notEqual(martin.gastos_totales,176554014228.48); // Budget total includes financial applications.
  assert.match(rows.find(m=>m.id==='06833').fiscal.scope,/No consolida el Centro Municipal de Salud/);
  const matanza=rows.find(m=>m.id==='06427').fiscal;
  assert.equal(matanza.ingresos_totales,383274207057.99);
  assert.equal(matanza.gastos_totales,273688321997.90);
  assert.equal(matanza.resultado_financiero,109585885060.09);
  assert.equal(matanza.personal_devengado,58753633542.65); // Devengado, not compromiso or pagado.
  assert.notEqual(matanza.gastos_totales,293676011453.75); // Budget total includes financing operations.
});

test('Tigre budget execution stays separate from the fiscal deficit ranking',()=>{
  const tigre=rows.find(m=>m.id==='06805'),e=tigre.fiscalExecution;
  assert.equal(tigre.fiscal,null);
  assert.equal(metricValue(tigre,metric('deficit')),null);
  assert.equal(e.presupuesto_vigente,611294558622.66);
  assert.equal(e.recursos_presupuestarios_percibidos,218657322550.68);
  assert.equal(e.devengado_no_pagado_del_periodo,8419889847.26);
  assert.ok(Math.abs(e.gastos_presupuestarios_devengados-e.gastos_presupuestarios_pagados-e.devengado_no_pagado_del_periodo)<.01);
  assert.equal(data.fiscalCoverage.budgetOnly,1);
  const exported=fiscalExportRows(tigre);
  assert.equal(exported.length,5);
  assert.equal(exported.find(r=>r[1]==='Gastos del período devengados y no pagados')[2],8419889847.26);
  assert.ok(exported.every(r=>r[3]==='ARS corrientes'&&r[4]==='2026-01-01 / 2026-06-30'));
  assert.ok(!exported.some(r=>r[1]==='Resultado financiero'));
});

test('all fiscal observations retain primary documents, page locations and content hashes',()=>{
  const audit=JSON.parse(fs.readFileSync(new URL('../municipios/data/fiscal_verified.json',import.meta.url)));
  assert.equal(audit.records.length,72);
  assert.deepEqual(audit.records.map(r=>r.id).sort(),rows.filter(m=>m.fiscal).map(m=>m.id).sort());
  assert.equal(audit.otherPeriods.length,19);
  for(const r of [...audit.records,...audit.budgetExecutions,...audit.otherPeriods]){
    assert.match(r.landingUrl,/^https?:\/\//);
    assert.ok(r.documents.length>0);
    for(const d of r.documents){
      assert.match(d.url,/^https?:\/\//);
      assert.match(d.sha256,/^[0-9a-f]{64}$/);
      assert.ok(d.consultedPages.every(p=>p>=1&&p<=d.pages));
      assert.ok(d.bytes>0);
    }
  }
});

test('quarter sums exclude overlapping periods and do not invent personnel',()=>{
  const a=rows.find(m=>m.id==='06042').fiscal;
  assert.equal(a.resultado_financiero,-478052216.13);
  assert.equal(a.personal_devengado,undefined);
  assert.equal(a.personal_sobre_gasto_corriente_pct,null);
  const si=rows.find(m=>m.id==='06756').fiscal;
  assert.equal(si.method,'sum_quarters');
  assert.equal(si.resultado_financiero,-11956211531.15);
  assert.equal(si.personal_devengado,74667170776.53);
});

test('accounts belong to the municipality, not the separately published agency',()=>{
  assert.equal(rows.find(m=>m.id==='06357').fiscal.ingresos_totales,211223436093.38);
  assert.equal(rows.find(m=>m.id==='06672').fiscal.resultado_financiero,551633002.17);
  const azul=rows.find(m=>m.id==='06049').fiscalOther;
  assert.equal(azul.ingresos_totales,15237040168.17);
  assert.match(azul.scope,/No consolida la Dirección de Vialidad Rural/);
});

test('other periods stay visible and downloadable without entering June rankings',()=>{
  assert.equal(data.fiscalCoverage.withAccounts,90);
  assert.equal(data.fiscalCoverage.otherPeriods,19);
  const lp=rows.find(m=>m.id==='06441'),b=rows.find(m=>m.id==='06112');
  assert.equal(lp.fiscal,null);
  assert.equal(lp.fiscalOther.fin,'2026-03-31');
  assert.equal(metricValue(lp,metric('deficit')),null);
  assert.equal(b.fiscal.fin,'2026-06-30');
  assert.equal(b.fiscalOther.fin,'2026-08-31');
  assert.notEqual(b.fiscal.resultado_financiero,b.fiscalOther.resultado_financiero);
  assert.equal(metricValue(b,metric('resultado-pesos')),b.fiscal.resultado_financiero);
  assert.equal(fiscalExportRows(lp).length,8);
  assert.ok(fiscalExportRows(lp).every(r=>r[4].endsWith('2026-03-31')));
  assert.equal(fiscalExportRows(b).length,16);
  assert.equal(fiscalExportRows(rows.find(m=>m.id==='06042')).find(r=>r[1]==='Personal devengado')[2],null);
});

test('portal review covers every municipality and preserves pending accounts',()=>{
  const review=JSON.parse(fs.readFileSync(new URL('../municipios/data/fiscal_search.json',import.meta.url)));
  assert.equal(review.municipalities.length,135);
  assert.equal(review.municipalities.filter(r=>r.searchedThisRound).length,117);
  assert.deepEqual(new Set(review.municipalities.map(r=>r.id)),new Set(rows.map(r=>r.id)));
  for(const m of rows){
    assert.ok(m.fiscalSearch.message.length>20);
    if(m.fiscalSearch.status==='comparable_account')assert.ok(m.fiscal);
    if(m.fiscalSearch.status==='other_period'){assert.ok(m.fiscalOther);assert.equal(m.fiscal,null);}
  }
  assert.equal(rows.filter(m=>!m.fiscal&&!m.fiscalOther&&!m.fiscalExecution).length,44);
});

test('ASAP scores retain all 135 municipalities, zero scores, ties, and point changes',()=>{
  const ranked=rankMunicipalities(rows,metric('transparencia'));
  assert.equal(data.transparency.coverage,135);
  assert.equal(ranked.length,135);
  assert.equal(ranked.filter(r=>r.rank===1&&r.value===100).length,65);
  assert.equal(ranked.filter(r=>r.value===0).length,9);
  assert.equal(metric('cambio-transparencia').unit,'points');
  for(const m of rows){
    const t=m.transparency;
    assert.deepEqual(t.history.map(h=>h.edition),['2025-11','2026-05']);
    assert.equal(t.change,t.score-t.previousScore);
    for(const h of t.history)assert.equal(h.score,Object.values(h.components).reduce((a,b)=>a+b,0));
  }
  assert.equal(rows.filter(m=>m.transparency.change>0).length,20);
  assert.equal(rows.filter(m=>m.transparency.change<0).length,23);
  assert.equal(rows.filter(m=>m.transparency.change===0).length,92);
  assert.equal(readState('?vista=rankings&indicador=transparencia',rows).metric,'transparencia');
});

test('publication snapshot remains separate from later accounts and ambiguous component scores',()=>{
  const lasHeras=rows.find(m=>m.id==='06329'),tigre=rows.find(m=>m.id==='06805');
  assert.equal(lasHeras.transparency.score,30);
  assert.equal(lasHeras.fiscal.fin,'2026-06-30');
  assert.equal(tigre.transparency.score,5);
  assert.equal(tigre.transparency.change,-33);
  assert.ok(tigre.fiscalExecution);
  assert.equal(tigre.fiscal,null);
  assert.equal(data.transparency.editions.at(-1).observedThrough,'2026-05-08');
  assert.equal(rows.find(m=>m.id==='06385').transparency.score,100); // Corrected General Viamonte score.
  const sef=TRANSPARENCY_COMPONENTS.find(c=>c.id==='situacion_economico_financiera');
  assert.match(transparencyStatus(sef,15),/parcial o de un trimestre anterior/);
  assert.match(transparencyStatus(sef,0),/ausente o fuera del período/);
  assert.equal(transparencyStatus(sef,null),'Sin dato');
  const moron=rows.find(m=>m.id==='06568').transparency;
  assert.equal(moron.history[0].components.presupuesto,15);
  assert.match(moron.history[0].note,/no figuran en su escala/);
  assert.match(transparencyStatus(TRANSPARENCY_COMPONENTS.find(c=>c.id==='presupuesto'),15),/fuera de la escala/);
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


test('census context uses its own denominators and preserves official crime categories',()=>{
  const audit=JSON.parse(fs.readFileSync(new URL('../municipios/data/community_verified.json',import.meta.url)));
  assert.equal(audit.salaryAudit.monthlyObservations,11340);
  assert.equal(audit.householdDebt.municipalAvailable,false);
  assert.equal(audit.householdDebt.geographicLevel,'province');
  for(const m of rows){
    const c=m.community,h=c.health,raw=audit.municipalities.find(r=>r.id===m.id);
    assert.equal(h.populationPrivateDwellings,h.socialInsuranceOrPrivate+h.statePlan+h.withoutCoverage);
    assert.equal(h.withoutCoveragePct,100*h.withoutCoverage/h.populationPrivateDwellings);
    assert.equal(c.crowding.households,m.hogares_2022);
    assert.ok(c.crowding.over3PersonsPerRoomPct>=0&&c.crowding.over3PersonsPerRoomPct<=100);
    for(const year of ['2023','2024','2025'])assert.ok(Math.abs(c.wage.annual[year].real-m[`salario_real_promedio_${year}_ars_jul26`])<.00001);
    for(const year of ['2024','2025']){
      const original=raw.crime[year].sourceRows,published=c.crime[year];
      assert.equal(published.robberies,Number(original['15'].cantidad_hechos)+Number(original['17'].cantidad_hechos));
      assert.equal(published.homicideVictims,Number(original['1'].cantidad_victimas));
      assert.equal(published.thefts,Number(original['19'].cantidad_hechos));
      assert.ok(Math.abs(published.robberyRate-(Number(original['15'].tasa_hechos.replace(',','.'))+Number(original['17'].tasa_hechos.replace(',','.'))))<1e-8);
    }
  }
  const h=rows.find(r=>r.id==='06329').community;
  assert.equal(h.health.withoutCoverage,5038);assert.equal(h.health.populationPrivateDwellings,17980);
  assert.equal(h.crime['2025'].homicideVictims,0);assert.equal(h.crime['2024'].robberies,22);assert.equal(h.crime['2025'].robberies,37);
  assert.equal(Math.round(h.wage.annual['2025'].real),2117275);
  for(const [id,original] of [['06658','06058'],['06218','06217']])assert.equal(audit.municipalities.find(r=>r.id===id).crime['2025'].sourceRows['1'].departamento_id,original);
});


test('external debt aggregates preserve attribution, persons and money denominators and thousand-peso units',()=>{
 const audit=JSON.parse(fs.readFileSync(new URL('../municipios/data/debt_cec.json',import.meta.url)));
 assert.equal(audit.period,'2026-07');assert.equal(audit.populationDenominator,false);
 assert.match(audit.classification,/CEC/);assert.match(audit.verificationScope,/no se verificaron domicilios/);
 assert.equal(audit.municipalities.length,135);
 for(const m of rows){
  const d=m.community.debt,raw=audit.municipalities.find(r=>r.id===m.id).sourceRecord;
  assert.equal(d.period,'2026-07');assert.ok(d.peopleInArrears>=5&&d.peopleInArrears<=d.peopleWithDebt);
  assert.equal(d.debtARS,raw.monto_total*1000);assert.equal(d.debtInArrearsARS,raw.monto_mora*1000);
  assert.equal(d.peopleInArrearsPct,100*d.peopleInArrears/d.peopleWithDebt);
  assert.ok(Math.abs(d.debtInArrearsPct-100*d.debtInArrearsARS/d.debtARS)<.000001);
 }
 assert.equal(rows.reduce((sum,m)=>sum+m.community.debt.peopleWithDebt,0),7395124);
 const h=rows.find(m=>m.id==='06329').community.debt;
 assert.equal(h.peopleWithDebt,13565);assert.equal(h.peopleInArrears,4035);assert.equal(h.debtARS,52962481000);
 assert.ok(Math.abs(h.peopleInArrearsPct-h.debtInArrearsPct)>6);
});

test('deflator preserves zero, negative values and missing months without extrapolation',()=>{
  const ix={'2024-12':100,'2025-12':150};
  assert.equal(adjustPrice(100,'2024-12','2025-12',ix),150);
  assert.equal(adjustPrice(-100,'2024-12','2025-12',ix),-150);
  assert.equal(adjustPrice(0,'2024-12','2025-12',ix),0);
  assert.equal(adjustPrice(null,'2024-12','2025-12',ix),null);
  assert.equal(adjustPrice(100,'2024-12','2026-12',ix),null);
  assert.equal(adjustPrice(100,'2024-12','2025-12',{'2024-12':0,'2025-12':150}),null);
  assert.ok(Math.abs(adjustPrice(adjustPrice(1234,'2024-12','2025-12',ix),'2025-12','2024-12',ix)-1234)<1e-9);
});

test('all municipalities retain real changes under a different base and nominal transfers use original pesos',()=>{
  const deflator=JSON.parse(fs.readFileSync(new URL('../municipios/data/deflator.json',import.meta.url)));
  for(const m of rows){
    const nominal=priceComparisons(m,'nominal','2024-12',deflator);
    assert.equal(nominal[0].current,m.transferencias_2026_ene_jul_ars);
    assert.equal(nominal[2].current,m.community.wage.annual['2025'].nominal);
    for(const base of deflator.bases){
      const real=priceComparisons(m,'real',base,deflator);
      assert.ok(Math.abs(real[0].change-m.variacion_transferencias_real_pct)<0.00000051);
      assert.ok(Math.abs(real[1].change-m.variacion_copart_real_pct)<0.00000051);
      for(const [n,key] of [[3,'prestamos_real_cambio_2023_2024_pct'],[4,'depositos_real_cambio_2023_2024_pct']]){
        if(m[key]===null)assert.equal(real[n].change,null);
        else assert.ok(Math.abs(real[n].change-m[key])<0.00000051);
      }
      assert.equal(real[5].previous,null);assert.equal(real[5].change,null);
      assert.equal(real[5].current,adjustPrice(m.community.debt.debtARS,'2026-07',base,deflator.indices));
    }
  }
  const h=rows.find(m=>m.id==='06329');
  assert.ok(Math.abs(priceComparisons(h,'real','2026-07',deflator)[0].current-priceComparisons(h,'nominal','2026-07',deflator)[0].current)>1e8);
});

test('municipal CSV includes new displayed context with original denominators and missingness',()=>{
  for(const m of rows){
    const out=municipalContextExportRows(m),get=label=>out.find(r=>r[1]===label);
    assert.equal(get('Deuda total registrada de personas')[2],m.community.debt.debtARS);
    assert.equal(get('Personas en mora sobre personas con deuda')[2],m.community.debt.peopleInArrearsPct);
    assert.equal(get('Población en viviendas particulares')[2],m.community.health.populationPrivateDwellings);
    assert.equal(get('Población')[2],m.poblacion_2022);
    assert.equal(out.filter(r=>r[1]==='Robos registrados').length,2);
    assert.equal(out.filter(r=>r[1]==='Salario bruto mensual promedio').length,3);
    for(const s of m.sectors)assert.equal(get('Empleo privado formal: '+s.name)[2],s.jobs);
    assert.ok(out.every(r=>r.length===6&&r[0]===m.municipio));
  }
});

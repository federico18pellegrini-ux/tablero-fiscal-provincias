const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const crypto=require('node:crypto');
const M=require('../nacion/management-model.js');
const B=require('../nacion/math.js');
const G=require('../nacion/data/gestion.json');
const D=require('../nacion/data/budget.json');
const read=name=>JSON.parse(fs.readFileSync(`${__dirname}/../nacion/data/gestion/${name}.json`,'utf8'));
const near=(a,b,eps=.01)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
const sum=(rows,key)=>rows.reduce((n,r)=>n+r[key],0);

test('OPC acts reconcile the current authorization within documented rounding',()=>{
  const m=G.updates.modifications,r=m.reconciliation;
  assert.deepEqual(m.acts.map(x=>x.id),['da2','da20','dnu594','da26','dnu867']);
  assert.equal(sum(m.acts,'spending_ars_millions'),4405675);
  near(r.current-r.initial,r.acts_total+r.rounding_residual);
  assert(Math.abs(r.rounding_residual)<=r.tolerance_ars_millions);
  assert.equal(r.current,G.execution.total.credito_vigente);
  for(const s of G.updates.sources){
    const raw=fs.readFileSync(`${__dirname}/../nacion/${s.path}`);
    assert.equal(crypto.createHash('sha256').update(raw).digest('hex'),s.sha256);
    assert.equal(raw.length,s.bytes);
  }
});

test('July OPC schedule keeps currencies separate and preserves the published rounding',()=>{
  const d=G.updates.debt;
  assert.equal(d.stock_cutoff,'2026-07-31');assert.equal(d.pdf_page,17);
  assert.equal(sum(d.months,'ars_thousand_millions'),105025);
  assert.equal(sum(d.months,'fx_usd_millions'),5079);
  assert.equal(d.totals.fx_usd_millions,5080);
  assert.equal(d.totals.fx_usd_millions_rounding_difference,1);
  assert.equal(d.months.reduce((a,b)=>a.ars_thousand_millions>b.ars_thousand_millions?a:b).period,'2026-12');
  assert.equal(d.months.reduce((a,b)=>a.fx_usd_millions>b.fx_usd_millions?a:b).period,'2026-09');
  assert.equal(G.debt.cutoff_schedule,'2026-03-31');
});

test('physical comparisons distinguish absent realization, actual zero and unusable plans',()=>{
  const row=(a,p)=>({ejecutado_acumulado_trim2:a,programacion_acumulada_trim2:p});
  assert.equal(M.metaStatus(row(null,100),2).key,'missing');
  assert.equal(M.metaStatus(row(0,100),2).deviation,-100);
  assert.equal(M.metaStatus(row(0,100),2).key,'below');
  for(const plan of [null,0,-1])assert.equal(M.metaStatus(row(50,plan),2).deviation,null);
  assert.equal(M.metaStatus(row(100,100),2).key,'equal');
  assert.equal(M.metaStatus(row(120,100),2).key,'above');
  for(const q of [1,2]){
    const rows=read('metas_fisicas_trimestre_'+q);
    assert.equal(rows.filter(r=>M.metaStatus(r,q).key==='missing').length,G.physical.coverage.find(r=>r.trimestre===q).mediciones_sin_ejecucion);
    assert(rows.some(r=>B.matchesSearch({name:r.programa_desc,entity:r.servicio_desc},'vacunas')));
  }
});

test('28 published datasets retain sealed CSV and JSON; unreconciled GDP stays out',()=>{
  const catalog=read('catalogo');assert.equal(catalog.length,28);
  assert(!catalog.some(r=>r.dataset.includes('pib')));
  for(const r of catalog){
    assert.equal(read(r.dataset).length,r.rows);
    for(const f of Object.values(r.files)){
      const text=fs.readFileSync(`${__dirname}/../nacion/${f.path}`,'utf8').replace(/\r\n/g,'\n');
      assert.equal(crypto.createHash('sha256').update(text).digest('hex'),f.sha256);
    }
  }
});
test('all execution classifications independently reconcile with the budget already displayed',()=>{
  for(const rows of Object.values(G.execution.groups)){
    near(sum(rows,'credito_devengado'),D.total.accrued);
    near(sum(rows,'credito_vigente'),D.total.current);
    near(sum(rows,'credito_pagado'),G.execution.total.credito_pagado);
  }
  near(G.execution.total.devengado_menos_pagado,D.total.accrued-G.execution.total.credito_pagado);
});
test('real year-on-year execution uses each observed month and excludes partial September',()=>{
  const rows=read('gasto_mensual_funcion'),ipc=Object.fromEntries(read('ipc_observado').map(r=>[r.periodo,r.indice]));
  for(const r of rows){
    if(r.periodo==='2026-09'){assert.equal(r.credito_devengado_real_agosto2026,null);continue;}
    near(r.credito_devengado_real_agosto2026,r.credito_devengado*ipc['2026-08']/ipc[r.periodo]);
  }
  const actual=G.execution.comparison.find(r=>r.etapa==='credito_devengado');
  const year=y=>sum(rows.filter(r=>r.periodo>=`${y}-01`&&r.periodo<=`${y}-08`),'credito_devengado_real_agosto2026');
  near(actual.variacion_real_pct,M.change(year(2026),year(2025)),1e-7);
  near(sum(G.execution.functions_comparison,'credito_devengado_real_agosto2026_2026'),year(2026));
});
test('cash reconciles and revised provincial categories never acquire invented real comparisons',()=>{
  const rows=G.cash.comparison,find=k=>rows.find(r=>r.indicador===k);
  for(const price of ['nominal','real'])for(const year of [2025,2026]){
    const v=k=>M.cashValue(find(k),year,price);
    near(v('ingresos_totales')-v('gasto_primario'),v('resultado_primario'),1);
    near(v('resultado_primario')-v('intereses_netos'),v('resultado_financiero'),1);
  }
  for(const k of ['transferencias_corrientes_provincias','otros_gastos_corrientes']){
    assert.equal(M.cashValue(find(k),2025,'real'),null);
    assert.equal(find(k).variacion_real_acumulada_pct,null);
  }
  for(const r of rows.filter(r=>r.indicador.startsWith('resultado_')))assert.equal(r.variacion_real_acumulada_pct,null);
});
test('all 24 provinces preserve population denominators and separate budget transfers',()=>{
  const rows=G.provinces.comparison;assert.equal(rows.length,24);
  assert.equal(new Set(rows.map(r=>r.provincia_id)).size,24);
  const transfers=read('transferencias_presupuestarias_provincias');
  for(const r of rows){
    near(r.pesos_por_habitante_2026,r.ron_2026*1e6/r.habitantes);
    const own=transfers.filter(t=>t.ubicacion_geografica_id===r.provincia_id&&t.anio===2026);
    near(sum(own,'credito_devengado'),r.presupuestarias_devengado);
    near(sum(own,'credito_pagado'),r.presupuestarias_pagado);
  }
  assert.equal(M.rankProvinces([{provincia:'A',x:0},{provincia:'B',x:0},{provincia:'C',x:null}], 'x')[1].rank,1);
});
test('debt currency uses normal debt denominator; schedules preserve March vintage and partial year',()=>{
  const d=G.debt.monthly.at(-1);
  assert.equal(G.debt.monthly.length,92);assert.equal(d.periodo,'2026-08');assert.equal(d.stock_bruto,484917);
  near(d.stock_moneda_local+d.stock_moneda_extranjera,d.stock_situacion_normal,.2);
  near(d.capital_pagado+d.intereses_pagados,d.pagos_totales,.2);
  near(d.transacciones_netas+d.ajustes_valuacion+d.ajustes_elegible+d.ajustes_avales+d.consolidacion_deudas,d.variacion_stock,.2);
  for(const r of G.debt.schedule){assert.equal(r.corte_stock,'2026-03-31');near(r.capital_usd_millones+r.intereses_usd_millones,r.total_usd_millones);}
  const year=G.debt.annual_schedule.find(r=>r.periodo==='2026');assert(year.periodo_parcial);
  near(sum(G.debt.schedule.filter(r=>r.periodo.startsWith('2026')),'total_usd_millones'),year.total_usd_millones);
  assert(G.debt.annual_schedule.at(-1).agrupa_varios_anios);
});
test('quarterly physical measures keep their own units and missing actuals distinct from zero',()=>{
  for(const quarter of [1,2]){
    const rows=read('metas_fisicas_trimestre_'+quarter),coverage=G.physical.coverage.find(r=>r.trimestre===quarter);
    assert.equal(rows.length,coverage.mediciones);
    assert.equal(rows.filter(r=>M.metaValues(r,quarter).actual===null).length,coverage.mediciones_sin_ejecucion);
    assert(rows.some(r=>M.metaValues(r,quarter).actual===0));
    assert(rows.every(r=>r.unidad_medida_desc&&r.totalizador_avance_fisico));
  }
  const works=read('obras_ejecucion_fisica_financiera');assert.equal(works.length,446);
  assert.equal(works.filter(r=>r.ejecucion_fisica_1t2026_pct===null).length,103);
});
test('history uses reconciled annual totals and observed annual average CPI only',()=>{
  assert.equal(G.history.length,19);assert.equal(G.history[0].ejercicio_presupuestario,2007);
  const ipc=Object.fromEntries(read('ipc_observado').map(r=>[r.periodo,r.indice]));
  for(const r of G.history){
    const y=r.ejercicio_presupuestario;
    if(y<2017)assert.equal(M.historyValue(r,'credito_devengado','real'),null);
    else{const mean=Array.from({length:12},(_,i)=>ipc[`${y}-${String(i+1).padStart(2,'0')}`]).reduce((a,b)=>a+b,0)/12;near(M.historyValue(r,'credito_devengado','real'),r.credito_devengado*ipc['2026-08']/mean);}
  }
  for(const r of D.history.filter(r=>r.year<2026)){near(r.amount,G.history.find(x=>x.ejercicio_presupuestario===r.year).credito_devengado);assert.equal(r.gdp_share,null);assert.equal(r.purposes,null);}
});
test('management deep links stay in the right page and missing values remain absent',()=>{
  for(const anchor of ['caja','deuda-nacional','provincias-nacion','metas','obras-ejecucion','historia-ejecucion'])assert.equal(B.pageForAnchor(anchor),'ejecucion');
  assert.equal(M.sum([{x:null}],'x'),null);assert.equal(M.sum([{x:0}],'x'),0);assert.equal(M.sum([],'x'),null);
  assert.equal(M.ratio(20,0),null);assert.equal(M.ratio(null,50),null);
});

test('net changes reconcile at every level without treating zero initial credit as a new policy',()=>{
  const total=G.execution.total,net=total.credito_vigente-total.credito_presupuestado;
  near(net,4405675.31386698);
  for(const rows of Object.values(G.execution.groups)){
    const bridge=M.modificationBalance(rows);
    near(bridge.increases+bridge.reductions,net);
    near(M.sum(M.modifications(rows),'modification'),net);
  }
  const rows=M.modifications([{credito_presupuestado:0,credito_vigente:100},{credito_presupuestado:100,credito_vigente:0},{credito_presupuestado:null,credito_vigente:100}]);
  assert.equal(rows[0].modification,100);assert.equal(rows[0].modification_pct,null);
  assert.equal(rows[1].modification_pct,-100);assert.equal(rows[2].modification,null);
  assert.equal(M.modificationBalance(rows),null);assert.equal(M.modificationBalance([]),null);
  assert.equal(B.pageForAnchor('modificaciones'),'ejecucion');
});

test('all provincial sheets join IDs only within PA and names only within the project',()=>{
  const seen=new Set();
  for(const p of G.provinces.comparison){
    const t=M.territory(D,G,p.provincia_id);assert(t);seen.add(t.province.provincia_id);
    assert.equal(t.project.name,p.provincia);
    for(const [a,b] of [['law','credito_presupuestado'],['current','credito_vigente'],['accrued','credito_devengado']])near(t.project[a],t.observed[b]);
    near(t.pending,p.presupuestarias_devengado-p.presupuestarias_pagado);
    near(t.worksTotal,D.works.filter(w=>w.province===p.provincia).reduce((s,w)=>s+w.project,0));
    assert(t.works.every(w=>w.province===p.provincia));
    assert(!Object.hasOwn(t,'total')); // RON, transfers and localized spending must never be summed.
  }
  assert.equal(seen.size,24);
  assert.equal(M.territory(D,G,999),null);assert.equal(M.territory(D,G,'6'),null);
  assert.equal(M.territory({...D,geographies:[...D.geographies,D.geographies[1]]},G,6),null);
  const noTransfer=structuredClone(G);noTransfer.provinces.comparison[1].presupuestarias_pagado=null;
  assert.equal(M.territory(D,noTransfer,6).pending,null);
});

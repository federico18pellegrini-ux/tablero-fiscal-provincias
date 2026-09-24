/* Initial budgets and accrued execution keep their original dates and scopes. */
let budgetExecutionData=null,budgetExecutionRequest=null,budgetCompositionChart=null;
function fiscalExecutionRatios(row){
 if(!row||!Number.isFinite(row.income)||row.income<=0||!Number.isFinite(row.spending)||row.spending<=0||!Number.isFinite(row.capital))return null;
 return {balance:(row.income-row.spending)/row.income*100,capital:row.capital/row.spending*100};
}
function proposalCost(v){
 if(['quantity','unit','months','startup','funding'].some(k=>!Number.isFinite(v[k])||v[k]<0)||!Number.isInteger(v.months)||v.months<1||v.months>12)return null;
 const recurring=v.quantity*v.unit*v.months,total=recurring+v.startup;
 return Number.isFinite(total)?{recurring,total,gap:Math.max(0,total-v.funding)}:null;
}
function budgetParagraph(host,text,className='federal-note'){const p=document.createElement('p');p.className=className;p.textContent=text;host.append(p);return p;}
function completionTable(caption,headers,rows){const box=managementTable(caption,headers,rows);box.classList.add('completion-table');box.querySelectorAll('tbody tr').forEach(tr=>Array.from(tr.children).forEach((cell,i)=>cell.dataset.label=headers[i]));return box;}
function renderBudgetExecution(){
 if(!document.getElementById('incomeView'))return;
 if(!budgetExecutionData){
  if(!budgetExecutionRequest)budgetExecutionRequest=fetch('data/budget_execution_2026.json?v=20260906-13').then(r=>{if(!r.ok)throw Error('budget');return r.json();}).then(d=>{budgetExecutionData=d;renderBudgetExecution();}).catch(()=>{budgetExecutionRequest=null;let h=document.getElementById('budgetExecution');if(!h){h=document.createElement('section');h.id='budgetExecution';document.getElementById('incomeView').append(h);}h.textContent='No se pudo cargar presupuesto y ejecución. Cambiá de provincia para reintentar.';});
  return;
 }
 renderLatestPbaUpdate();
 const semester=currentProvince==='Buenos Aires'?pbaExecutionLatest:null;
 const periodText=semester?'Enero–junio':'Enero–marzo';
 const province=currentProvince,b=budgetExecutionData.budgets.find(r=>r.province===province),e=semester?{...semester.rows[1],source_url:semester.source.url}:budgetExecutionData.executions.find(r=>r.province===province&&r.period==='2026-Q1'),old=semester?{...semester.rows[0],source_url:semester.source.url}:budgetExecutionData.executions.find(r=>r.province===province&&r.period==='2025-Q1');
 if(!b)return;
 let host=document.getElementById('budgetExecution');if(!host){host=document.createElement('section');host.id='budgetExecution';host.className='national-section completion-card';document.getElementById('incomeView').append(host);}host.replaceChildren();
 const title=document.createElement('h2');title.textContent='Presupuesto inicial y ejecución · '+province;host.append(title);
 budgetParagraph(host,'Presupuesto anual inicial y ejecución '+periodText.toLowerCase()+' de 2026 · millones de pesos corrientes.');
 const valid=b.scope_comparison&&fiscalExecutionRatios(e);
 host.append(completionTable('Importes de distinto horizonte temporal',['Concepto','Presupuesto anual inicial','Ejecutado '+periodText.toLowerCase(),'% del inicial¹'],[['income','Ingresos'],['spending','Gasto total'],['capital','Gasto de capital']].map(([key,label])=>[label,fnum(b[key]),Number.isFinite(e?.[key])?fnum(e[key]):'Sin dato',valid&&b[key]>0?fnum(e[key]/b[key]*100)+'%':'No calculado'])));
 budgetParagraph(host,valid?'¹ Porcentaje orientativo para coberturas identificadas como Administración Pública No Financiera (APNF). El denominador es el presupuesto inicial. El crédito vigente verificado tiene su propio bloque y corte. Sin programación trimestral no mide atrasos ni adelantos de gestión: el 25% no es una meta automática.':'¹ No se calcula el porcentaje: '+(!fiscalExecutionRatios(e)?'falta ejecución completa del período.':'presupuesto y ejecución tienen coberturas pendientes de conciliación.'));
 budgetParagraph(host,'Ejecución APNF: ingresos cobrados y gastos devengados. Presupuesto inicial, sin modificaciones del año.');
 const ratios=fiscalExecutionRatios(e),previous=fiscalExecutionRatios(old);
 budgetCompositionChart?.destroy();budgetCompositionChart=null;
 if(ratios){
  const h=document.createElement('h3');h.textContent='Cómo se distribuye el gasto ejecutado';host.append(h);
  const box=document.createElement('div');box.className='budget-composition-chart';const canvas=document.createElement('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Composición del gasto '+periodText.toLowerCase()+' de '+province);box.append(canvas);host.append(box);
  const periods=[...(previous?[{label:periodText+' 2025',r:previous}]:[]),{label:periodText+' 2026',r:ratios}];
  if(typeof Chart!=='undefined')budgetCompositionChart=new Chart(canvas,{type:'bar',data:{labels:periods.map(p=>p.label),datasets:[{label:'Gasto corriente',data:periods.map(p=>100-p.r.capital),backgroundColor:'#60a5fa'},{label:'Gasto de capital',data:periods.map(p=>p.r.capital),backgroundColor:'#fbbf24'}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{position:'bottom'},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fnum(c.raw)+'%'}}},scales:{x:{stacked:true,min:0,max:100,ticks:{callback:v=>v+'%',maxTicksLimit:5}},y:{stacked:true}}}});
  budgetParagraph(host,'Gasto de capital: obras, equipamiento, transferencias de capital e inversión financiera. El gráfico muestra su peso en el gasto total.');
 }
 managementSource(host,b.source_url,'Fuente: presupuesto provincial 2026 · archivo oficial');managementSource(host,e.source_url,semester?'PBA · ejecución APNF, primer semestre de 2026':'DNAP · ejecución APNF, primer trimestre de 2026');if(!semester)managementSource(host,old.source_url,'DNAP · ejecución APNF, primer trimestre de 2025');managementSource(host,'data/budget_execution_2026.json','Ver coberturas, celdas de origen y metodología');
 renderExecutionChanges(province,ratios,previous,semester);renderPbaComparison();renderProposalEstimator(province);renderManagementSourceReview();renderVerifiedManagement();
}
let managementReviewRequest=null;
function renderManagementSourceReview(){
 if(managementReviewRequest||!document.getElementById('fiscalGuide'))return;
 managementReviewRequest=Promise.all(['management_source_review.json','management_source_gaps.json'].map(name=>fetch('data/'+name+'?v=20260907-9').then(r=>{if(!r.ok)throw Error('review');return r.json();}))).then(([review,gaps])=>{
  const host=document.createElement('section');host.id='managementSourceReview';host.className='national-section completion-card';const h=document.createElement('h2');h.textContent='Datos que faltan para decidir';host.append(h);
  budgetParagraph(host,'Revisión del '+gaps.reviewed_at.split('-').reverse().join('/')+'. Los datos pendientes no se interpretan como cero.');
  const list=document.createElement('ul');for(const text of gaps.pending){const li=document.createElement('li');li.textContent=text;list.append(li);}host.append(list);
  document.getElementById('fiscalGuide').append(host);
 }).catch(()=>{managementReviewRequest=null;});
}
function renderExecutionChanges(province,now,previous,semester=null){
 const periodText=semester?'Enero–junio':'Enero–marzo';
 let host=document.getElementById('executionChanges');if(!host){host=document.createElement('section');host.id='executionChanges';host.className='national-section completion-card';document.getElementById('incomeView').append(host);}host.replaceChildren();const h=document.createElement('h2');h.textContent='Qué cambió · '+province;host.append(h);
 budgetParagraph(host,periodText+' de 2026 contra los mismos meses de 2025 · APNF. El ranking conserva el corte común de marzo.');
 if(!now||!previous){budgetParagraph(host,'Faltan datos para comparar ambos trimestres. La ausencia de información no se interpreta como cero ni como mejora.');return;}
 const rows=[['Resultado financiero / ingresos',previous.balance,now.balance],['Gasto de capital / gasto total',previous.capital,now.capital]];
 const table=completionTable('Cambios en puntos porcentuales (pp)',['Indicador',periodText+' 2025',periodText+' 2026','Cambio'],rows.map(([label,a,b])=>[label,fnum(a)+'%',fnum(b)+'%',(b-a>0?'+':'')+fnum(b-a)+' pp']));
 table.querySelectorAll('tbody tr').forEach((tr,i)=>{
  const [,a,b]=rows[i];
  [a,b,b-a].forEach((value,j)=>tr.children[j+1].classList.toggle('negative-value',value<0));
 });
 host.append(table);
 budgetParagraph(host,semester?'El déficit pasó de '+fnum(previous.balance)+'% a '+fnum(now.balance)+'% de los ingresos: el desequilibrio se achicó, aunque los recursos todavía no cubren el gasto. Capital mide la participación de la inversión, no su crecimiento real.':'Resultado financiero: ingresos menos gastos, incluidos los intereses. El cambio se expresa en puntos porcentuales (pp).');
 const source=semester?{source_url:semester.source.url}:budgetExecutionData.executions.find(r=>r.province===province&&r.period==='2026-Q1');managementSource(host,source.source_url,semester?'PBA · ejecución APNF, primeros semestres de 2025 y 2026':'DNAP · datos provisorios de ejecución');managementSource(host,'data/budget_execution_2026.json','Ver ambos períodos y cálculos de origen');
}
function renderProposalEstimator(province){
 let host=document.getElementById('proposalEstimator');if(host?.dataset.province===province)return;if(!host){host=document.createElement('section');host.id='proposalEstimator';host.className='national-section completion-card';document.getElementById('resultsView').append(host);}host.replaceChildren();host.dataset.province=province;
 const h=document.createElement('h2');h.textContent='Cuánto costaría una propuesta · '+province;host.append(h);
 budgetParagraph(host,'Cargá alcance, costos y financiamiento en millones de pesos del mismo año. Los supuestos se limpian al cambiar de provincia.');
 const grid=document.createElement('div');grid.className='scenario-grid';host.append(grid);
 const label=document.createElement('label');label.textContent='Propuesta y fuente de los costos';const description=document.createElement('input');description.type='text';description.placeholder='Ej.: programa, cotización y fecha';description.maxLength=500;label.append(description);grid.append(label);
 const fields=[['quantity','Cantidad de unidades o beneficiarios'],['unit','Costo mensual por unidad · $ millones'],['months','Meses del año (1 a 12)'],['startup','Costo inicial único · $ millones'],['funding','Financiamiento confirmado · $ millones']],inputs={};
 for(const [key,title] of fields){const label=document.createElement('label');label.textContent=title;const input=document.createElement('input');input.type='number';input.min=key==='months'?'1':'0';input.step=key==='months'?'1':'any';if(key==='months')input.max='12';input.placeholder='Sin cargar';label.append(input);grid.append(label);inputs[key]=input;}
 const output=budgetParagraph(host,'Completá todos los campos; ingresá 0 cuando corresponda.','scenario-output');output.setAttribute('aria-live','polite');
 const update=()=>{const v=Object.fromEntries(Object.entries(inputs).map(([k,i])=>[k,i.value.trim()===''?null:Number(i.value)])),r=proposalCost(v);if(!r||!description.value.trim()){output.textContent='Faltan la descripción, la fuente o supuestos válidos. Los meses deben ser enteros entre 1 y 12.';return;}output.textContent='Costo del período: $ '+fnum(r.total)+' millones. Costo recurrente: $ '+fnum(r.recurring)+' millones. Monto todavía sin financiamiento: $ '+fnum(r.gap)+' millones. Es una simulación; no acredita disponibilidad de caja ni autorización presupuestaria.';};grid.addEventListener('input',update);
 const reset=document.createElement('button');reset.type='button';reset.className='management-action';reset.textContent='Limpiar supuestos';reset.onclick=()=>{description.value='';Object.values(inputs).forEach(i=>i.value='');update();};host.append(reset);
}
if(typeof module!=='undefined')module.exports={fiscalExecutionRatios,proposalCost};

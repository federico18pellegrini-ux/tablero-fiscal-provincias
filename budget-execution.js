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
 const province=currentProvince,b=budgetExecutionData.budgets.find(r=>r.province===province),e=budgetExecutionData.executions.find(r=>r.province===province&&r.period==='2026-Q1'),old=budgetExecutionData.executions.find(r=>r.province===province&&r.period==='2025-Q1');
 if(!b)return;
 let host=document.getElementById('budgetExecution');if(!host){host=document.createElement('section');host.id='budgetExecution';host.className='national-section completion-card';document.getElementById('incomeView').append(host);}host.replaceChildren();
 const title=document.createElement('h2');title.textContent='Presupuesto y ejecución · '+province;host.append(title);
 budgetParagraph(host,'Presupuesto inicial de todo 2026 y ejecución de enero a marzo de 2026. Millones de pesos corrientes. Este bloque conserva su período y unidad aunque cambies los controles generales.');
 const valid=b.scope_comparison&&fiscalExecutionRatios(e);
 host.append(completionTable('Importes de distinto horizonte temporal',['Concepto','Presupuesto anual inicial','Ejecutado enero–marzo','% del inicial¹'],[['income','Ingresos'],['spending','Gasto total'],['capital','Gasto de capital']].map(([key,label])=>[label,fnum(b[key]),Number.isFinite(e?.[key])?fnum(e[key]):'Sin dato',valid&&b[key]>0?fnum(e[key]/b[key]*100)+'%':'No calculado'])));
 budgetParagraph(host,valid?'¹ Porcentaje orientativo para coberturas identificadas como Administración Pública No Financiera (APNF). No mide sobreejecución ni subejecución: faltan crédito vigente y programación trimestral. El 25% no es una meta automática.':'¹ No se calcula el porcentaje: '+(!fiscalExecutionRatios(e)?'falta ejecución completa del período.':'la cobertura institucional del presupuesto todavía debe conciliarse con la ejecución APNF. Mostrar ambos importes no los vuelve comparables.'));
 budgetParagraph(host,b.note+' La ejecución usa ingresos percibidos y gastos devengados: no representa pagos de caja.');
 const ratios=fiscalExecutionRatios(e),previous=fiscalExecutionRatios(old);
 budgetCompositionChart?.destroy();budgetCompositionChart=null;
 if(ratios){
  const h=document.createElement('h3');h.textContent='Cómo se distribuye el gasto ejecutado';host.append(h);
  const box=document.createElement('div');box.className='budget-composition-chart';const canvas=document.createElement('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Composición porcentual del gasto del primer trimestre de '+province);box.append(canvas);host.append(box);
  const periods=[...(previous?[{label:'Enero–marzo 2025',r:previous}]:[]),{label:'Enero–marzo 2026',r:ratios}];
  if(typeof Chart!=='undefined')budgetCompositionChart=new Chart(canvas,{type:'bar',data:{labels:periods.map(p=>p.label),datasets:[{label:'Gasto corriente',data:periods.map(p=>100-p.r.capital),backgroundColor:'#60a5fa'},{label:'Gasto de capital',data:periods.map(p=>p.r.capital),backgroundColor:'#fbbf24'}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{position:'bottom'},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fnum(c.raw)+'%'}}},scales:{x:{stacked:true,min:0,max:100,ticks:{callback:v=>v+'%',maxTicksLimit:5}},y:{stacked:true}}}});
  budgetParagraph(host,'Participación del gasto de capital: '+(previous?fnum(previous.capital)+'% en enero–marzo de 2025; ':'')+fnum(ratios.capital)+'% en enero–marzo de 2026. Es composición del gasto, no crecimiento real ni avance físico de las obras.');
 }
 budgetParagraph(host,profileWording('El presupuesto muestra qué se autorizó para el año. La ejecución permite ver qué empezó a concretarse. Para decidir si una política viene atrasada, hay que mirar además su calendario, las obras terminadas y las obligaciones que todavía faltan pagar.','El siguiente paso es conciliar cobertura, crédito vigente, devengado y pagado por programa. Recién con esa apertura se puede medir el desvío frente a lo programado y estimar cuánto queda por financiar.','Al comunicar estos datos, separá el presupuesto anual del gasto de tres meses. Un porcentaje bajo no demuestra por sí solo un recorte. También puede responder al calendario de pagos o de las obras.'),'profile-explanation');
 managementSource(host,b.source_url,'Fuente: presupuesto provincial 2026 · archivo oficial');managementSource(host,e.source_url,'Fuente: DNAP · ejecución APNF, primer trimestre de 2026');managementSource(host,old.source_url,'Fuente: DNAP · ejecución APNF, primer trimestre de 2025');managementSource(host,'data/budget_execution_2026.json','Ver coberturas, celdas de origen y metodología');
 renderExecutionChanges(province,ratios,previous);renderProposalEstimator(province);renderManagementSourceReview();
}
let managementReviewRequest=null;
function renderManagementSourceReview(){
 if(managementReviewRequest||!document.getElementById('fiscalGuide'))return;
 managementReviewRequest=Promise.all(['management_source_review.json','management_source_gaps.json'].map(name=>fetch('data/'+name+'?v=20260906-13').then(r=>{if(!r.ok)throw Error('review');return r.json();}))).then(([review,gaps])=>{
  const host=document.createElement('section');host.id='managementSourceReview';host.className='national-section completion-card';const h=document.createElement('h2');h.textContent='Fuentes revisadas y datos que faltan';host.append(h);
  budgetParagraph(host,'Revisión del '+new Date(review.checked_at).toLocaleDateString('es-AR')+'. Control a pedido; no es una actualización automática. Se verificaron '+review.sources.length+' enlaces: '+review.sources.filter(s=>s.status==='unchanged').length+' archivos coinciden con los importados. Que un enlace funcione no garantiza que el dato sea actual ni comparable.');
  const list=document.createElement('ul');for(const text of gaps.pending){const li=document.createElement('li');li.textContent=text;list.append(li);}host.append(list);
  for(const source of gaps.checks){budgetParagraph(host,source.province+' · '+source.kind+': '+source.note);managementSource(host,source.url,'Consultar archivo observado');}
  managementSource(host,'data/management_source_review.json','Ver resultado del control de enlaces y cambios');document.getElementById('fiscalGuide').append(host);
 }).catch(()=>{managementReviewRequest=null;});
}
function renderExecutionChanges(province,now,previous){
 let host=document.getElementById('executionChanges');if(!host){host=document.createElement('section');host.id='executionChanges';host.className='national-section completion-card';document.getElementById('summaryView').append(host);}host.replaceChildren();const h=document.createElement('h2');h.textContent='Qué cambió · '+province;host.append(h);
 budgetParagraph(host,'Primer trimestre de 2026 contra el mismo trimestre de 2025 · APNF. Esta comparación tiene un corte distinto del informe 1816 y no reemplaza su ranking.');
 if(!now||!previous){budgetParagraph(host,'Faltan datos para comparar ambos trimestres. La ausencia de información no se interpreta como cero ni como mejora.');return;}
 host.append(completionTable('Cambios en puntos porcentuales (pp)',['Indicador','Enero–marzo 2025','Enero–marzo 2026','Cambio'],[['Resultado financiero / ingresos',previous.balance,now.balance],['Gasto de capital / gasto total',previous.capital,now.capital]].map(([label,a,b])=>[label,fnum(a)+'%',fnum(b)+'%',(b-a>0?'+':'')+fnum(b-a)+' pp'])));
 budgetParagraph(host,'El resultado financiero es la diferencia entre ingresos y gastos, incluidos los intereses. '+(now.balance>0?'En este trimestre los ingresos superan al gasto devengado.':now.balance<0?'En este trimestre el gasto devengado supera a los ingresos.':'En este trimestre los ingresos y el gasto devengado están equilibrados.')+' Eso no alcanza para saber cuánta caja libre hay. La participación del gasto de capital muestra cuánto pesa dentro del gasto total; para saber si la inversión creció hay que descontar inflación y revisar qué obras se ejecutaron.');
 const source=budgetExecutionData.executions.find(r=>r.province===province&&r.period==='2026-Q1');managementSource(host,source.source_url,'DNAP · datos provisorios de ejecución');managementSource(host,'data/budget_execution_2026.json','Ver ambos períodos y cálculos de origen');
}
function renderProposalEstimator(province){
 let host=document.getElementById('proposalEstimator');if(host?.dataset.province===province)return;if(!host){host=document.createElement('section');host.id='proposalEstimator';host.className='national-section completion-card';document.getElementById('resultsView').append(host);}host.replaceChildren();host.dataset.province=province;
 const h=document.createElement('h2');h.textContent='Cuánto costaría una propuesta · '+province;host.append(h);
 budgetParagraph(host,'Este ejercicio no asigna costos inventados a las propuestas. Cargá alcance, costo mensual por unidad y meses dentro de un año. Todos los importes están en millones de pesos nominales del mismo año. Los supuestos quedan en esta pantalla y se limpian al cambiar de provincia.');
 const grid=document.createElement('div');grid.className='scenario-grid';host.append(grid);
 const label=document.createElement('label');label.textContent='Propuesta y fuente de los costos';const description=document.createElement('input');description.type='text';description.placeholder='Ej.: programa, cotización y fecha';description.maxLength=500;label.append(description);grid.append(label);
 const fields=[['quantity','Cantidad de unidades o beneficiarios'],['unit','Costo mensual por unidad · $ millones'],['months','Meses del año (1 a 12)'],['startup','Costo inicial único · $ millones'],['funding','Financiamiento confirmado · $ millones']],inputs={};
 for(const [key,title] of fields){const label=document.createElement('label');label.textContent=title;const input=document.createElement('input');input.type='number';input.min=key==='months'?'1':'0';input.step=key==='months'?'1':'any';if(key==='months')input.max='12';input.placeholder='Sin cargar';label.append(input);grid.append(label);inputs[key]=input;}
 const output=budgetParagraph(host,'Completá todos los campos; ingresá 0 cuando corresponda.','scenario-output');output.setAttribute('aria-live','polite');
 const update=()=>{const v=Object.fromEntries(Object.entries(inputs).map(([k,i])=>[k,i.value.trim()===''?null:Number(i.value)])),r=proposalCost(v);if(!r||!description.value.trim()){output.textContent='Faltan la descripción, la fuente o supuestos válidos. Los meses deben ser enteros entre 1 y 12.';return;}output.textContent='Costo del período: $ '+fnum(r.total)+' millones. Costo recurrente: $ '+fnum(r.recurring)+' millones. Monto todavía sin financiamiento: $ '+fnum(r.gap)+' millones. Es una simulación; no acredita disponibilidad de caja ni autorización presupuestaria.';};grid.addEventListener('input',update);
 const reset=document.createElement('button');reset.type='button';reset.className='management-action';reset.textContent='Limpiar supuestos';reset.onclick=()=>{description.value='';Object.values(inputs).forEach(i=>i.value='');update();};host.append(reset);
}
if(typeof module!=='undefined')module.exports={fiscalExecutionRatios,proposalCost};

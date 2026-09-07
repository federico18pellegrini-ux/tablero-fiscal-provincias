let provincialServicesData=null,provincialServicesRequest=null;
function renderProvinceServices(province){
 const card=document.getElementById('debtScheduleCard');if(!card)return;card.style.display='block';
 if(!provincialServicesData){
  document.getElementById('debtScheduleReading').textContent='Cargando calendarios y servicios registrados…';
  if(!provincialServicesRequest)provincialServicesRequest=fetch('data/provincial_debt_services.json?v=20260906-13').then(r=>{if(!r.ok)throw Error('debt services');return r.json();}).then(d=>{provincialServicesData=d;renderProvinceServices(currentProvince);}).catch(()=>{provincialServicesRequest=null;document.getElementById('debtScheduleReading').textContent='No se pudo cargar la fuente. Cambiá de provincia para reintentar.';});
  return;
 }
 const data=provincialServicesData,projection=data.projections[province],canvas=document.getElementById('cDebtSchedule');
 if(charts.cDebtSchedule){charts.cDebtSchedule.destroy();delete charts.cDebtSchedule;}
 document.getElementById('debtScheduleDescription').textContent=projection?projection.scope+' · '+projection.note:'Todavía no hay un calendario futuro verificado para esta jurisdicción en el tablero. Esto no significa que no tenga vencimientos.';
 canvas.parentElement.hidden=!projection;card.querySelector('.debt-schedule-legend').hidden=!projection;
 const coverage=data.coverage.find(r=>r.province===province);
 document.getElementById('debtSchedule2026').textContent=projection?fmtPesosExecutive(projection.rows[0].total_ars_m):'Sin dato';
 document.getElementById('debtScheduleHighlightLabel').textContent=projection?'servicios previstos 2026':'calendario futuro';
 document.getElementById('debtScheduleReading').textContent=projection?profileWording('Los años con mayores vencimientos requieren anticipar cómo se van a sostener los servicios y la inversión. Este calendario no descuenta los pagos posteriores a la publicación.','Reconciliar esta proyección con pagos realizados, refinanciaciones y nueva deuda. Abrir los vencimientos por mes y moneda antes de incorporarlos a la programación de caja.','Estos importes son vencimientos previstos en una publicación, no deuda impaga ni saldo pendiente de hoy. Al citarlos, indicá fecha de referencia, moneda y si incluyen gastos además de intereses.'):coverage?.schedule_note||'No hay calendario cargado.';
 const sources=document.getElementById('debtScheduleSources');sources.replaceChildren();
 if(projection){
  for(const source of projection.sources)managementSource(sources,source.url,source.label);
  canvas.setAttribute('aria-label','Calendario anual de servicios de deuda de '+province);
  card.querySelector('.debt-schedule-legend').lastElementChild.innerHTML='<span class="ld" style="background:#fbbf24"></span>'+projection.interest_label;
  canvas.parentElement.style.height=Math.max(310,projection.rows.length*30+85)+'px';
  if(typeof Chart!=='undefined')charts.cDebtSchedule=new Chart(canvas,{type:'bar',data:{labels:projection.rows.map(r=>r.year),datasets:[{label:'Amortización',data:projection.rows.map(r=>r.amortization_ars_m),backgroundColor:'#60a5fa',stack:'services'},{label:projection.interest_label,data:projection.rows.map(r=>r.interest_ars_m),backgroundColor:'#fbbf24',stack:'services'}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fnum(c.raw)+' millones de pesos'}}},scales:{x:{stacked:true,ticks:{maxTicksLimit:4,callback:v=>new Intl.NumberFormat('es-AR',{maximumFractionDigits:0}).format(v)},title:{display:true,text:'Millones de pesos · proyección'}},y:{stacked:true,ticks:{autoSkip:false,font:{size:12}}}}}});
  const details=document.createElement('details');details.className='history-values';details.innerHTML='<summary>Ver importes del calendario</summary>';details.append(managementTable('Proyección publicada · millones de pesos',['Año','Capital',projection.interest_label,'Total'],projection.rows.map(r=>[r.year,fnum(r.amortization_ars_m),fnum(r.interest_ars_m),fnum(r.total_ars_m)])));sources.append(details);
 }
 document.getElementById('debtDecisionGap').textContent=profileWording('Para sostener los pagos hay que reunir caja utilizable, salarios, aguinaldo, deuda y financiamiento disponible.','Armar un flujo de caja que integre fechas de cobro y pago. Mantener separados capital, intereses y refinanciaciones para identificar el faltante efectivo.','Un calendario anual no permite afirmar si habrá problemas de pago en un mes. Para eso hacen falta caja utilizable y obligaciones con fecha.');
 let history=document.getElementById('provincialServicesHistory');if(!history){history=document.createElement('section');history.id='provincialServicesHistory';card.append(history);}
 if(charts.cDebtHistory){charts.cDebtHistory.destroy();delete charts.cDebtHistory;}
 history.replaceChildren();const title=document.createElement('h3');title.textContent='Servicios de deuda registrados · '+province;history.append(title);
 const method=document.createElement('p');method.className='federal-note';method.textContent='Capital e intereses devengados: obligaciones registradas en cada período. Datos preliminares, netos de deuda indirecta. No son un calendario futuro ni prueban que todo se haya pagado. Millones de pesos corrientes; la historia no está ajustada por inflación.';history.append(method);
 const rows=data.history.filter(r=>r.province===province).sort((a,b)=>a.period.localeCompare(b.period));
 renderDebtHistoryChart(history,rows,province);
 const recent=rows.filter(r=>['2025','2026-Q1'].includes(r.period));
 const formatRows=rs=>rs.map(r=>[r.period_type==='quarter'?'Enero–marzo 2026':r.period,fnum(r.amortization_ars_m),fnum(r.interest_ars_m),fnum(r.total_ars_m)]);
 history.append(managementTable('Año completo y trimestre: no se comparan como períodos iguales',['Período','Capital','Intereses','Total'],formatRows(recent)));
 const details=document.createElement('details');details.className='history-values';details.innerHTML='<summary>Ver historia desde 2005 y fuentes</summary>';details.append(managementTable('Servicios devengados · millones de pesos corrientes',['Período','Capital','Intereses','Total'],formatRows(rows)));
 for(const url of [...new Set(rows.map(r=>r.source_url))])managementSource(details,url,'Abrir planilla oficial de origen');history.append(details);
 const diff=data.source_differences.find(r=>r.province===province);if(diff){const p=document.createElement('p');p.className='federal-note';p.textContent='La serie provincial y el consolidado nacional presentan diferencias en 2025. Se conserva la serie provincial; el detalle de conciliación está en la descarga.';details.append(p);}
 managementSource(history,'data/provincial_debt_services.csv','Descargar servicios de las 24 jurisdicciones (CSV)');managementSource(history,'data/provincial_debt_services.json','Ver cobertura, fuentes y conciliación');
}

function renderDebtHistoryChart(host,rows,province){
 const controls=document.createElement('div');controls.className='choice-buttons';controls.setAttribute('role','group');controls.setAttribute('aria-label','Período del gráfico de servicios históricos');
 const box=document.createElement('div');box.className='debt-history-chart';const canvas=document.createElement('canvas');canvas.id='cDebtHistory';canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Capital e intereses devengados por año en '+province);box.append(canvas);
 const note=document.createElement('p');note.className='chart-touch-note';note.textContent='Tocá una barra para ver capital e intereses. Millones de pesos corrientes: el crecimiento nominal también refleja inflación. El trimestre 2026 se muestra aparte.';
 host.append(controls,box,note);
 const annual=rows.filter(r=>r.period_type==='year');
 const draw=all=>{for(const b of controls.children)b.setAttribute('aria-pressed',String((b.dataset.range==='all')===all));const shown=all?annual:annual.filter(r=>Number(r.period)>=2020);box.style.height=(Math.max(300,shown.length*32+70))+'px';const missing=shown.filter(r=>r.total_ars_m===null).map(r=>r.period),zero=shown.filter(r=>r.total_ars_m===0).map(r=>r.period);note.textContent='Tocá una barra para ver capital e intereses. Millones de pesos corrientes: el crecimiento nominal también refleja inflación. El trimestre 2026 se muestra aparte.'+(missing.length?' Sin total disponible: '+missing.join(', ')+'.':'')+(zero.length?' La fuente informa cero en: '+zero.join(', ')+'.':'');charts.cDebtHistory?.destroy();if(typeof Chart==='undefined')return;
 charts.cDebtHistory=new Chart(canvas,{type:'bar',data:{labels:shown.map(r=>r.period),datasets:[{label:'Capital',data:shown.map(r=>r.amortization_ars_m),backgroundColor:'#3675bd',stack:'services'},{label:'Intereses',data:shown.map(r=>r.interest_ars_m),backgroundColor:'#d79720',stack:'services'}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{position:'bottom',labels:{boxWidth:12,padding:16}},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fnum(c.raw)+' millones de pesos'}}},scales:{x:{stacked:true,ticks:{maxTicksLimit:4,callback:v=>new Intl.NumberFormat('es-AR',{maximumFractionDigits:0}).format(v)},title:{display:true,text:'Millones de pesos corrientes'}},y:{stacked:true,ticks:{autoSkip:false,font:{size:12}}}}}});
 };
 for(const [key,label] of [['recent','2020–2025'],['all','Historia desde 2005']]){const b=document.createElement('button');b.type='button';b.dataset.range=key;b.textContent=label;b.onclick=()=>draw(key==='all');controls.append(b);}draw(false);
}

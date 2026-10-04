/* Comparisons retain separate revenue and expenditure deflation methods. */
let pbaComparison=null,pbaComparisonRequest=null,pbaSpendingChart=null;
function renderPbaComparison(){
 let host=document.getElementById('pbaComparison');
 if(currentProvince!=='Buenos Aires'){if(host)host.hidden=true;return;}
 if(!pbaComparison){
  if(!pbaComparisonRequest)pbaComparisonRequest=Promise.all(['pba_comparison','pba_capital_detail'].map(name=>fetch(`data/${name}.json?v=20261004`).then(r=>{if(!r.ok)throw Error('PBA comparison');return r.json();}))).then(([data,capital])=>{pbaComparison={...data,capital};renderPbaComparison();}).catch(()=>{pbaComparisonRequest=null;});
  return;
 }
 if(!host){host=document.createElement('section');host.id='pbaComparison';host.className='national-section completion-card';document.getElementById('executionChanges').after(host);}
 host.hidden=false;host.replaceChildren();const d=pbaComparison;
 const heading=text=>{const h=document.createElement('h2');h.textContent=text;host.append(h);};
 const table=(caption,headers,rows,index)=>{const t=completionTable(caption,headers,rows);t.querySelectorAll('tbody tr').forEach(tr=>{const cell=tr.children[index];cell.classList.add(cell.textContent.startsWith('-')?'negative-value':'pba-positive');});host.append(t);};
 heading('Dónde se ajustó y qué aumentó');
 budgetParagraph(host,d.spending_period+' frente al mismo semestre de 2025 · APNF, incluida seguridad social.');
 const by=Object.fromEntries(d.spending.map(r=>[r.key,r]));
 budgetParagraph(host,`Los ingresos perdieron ${fnum(Math.abs(by.income.real_change_pct))}% de poder de compra y el gasto cayó ${fnum(Math.abs(by.spending.real_change_pct))}%. El déficit se achicó en relación con los recursos. El recorte fue especialmente fuerte en el gasto de capital (${fnum(by.capital.real_change_pct)}%), mientras los intereses aumentaron ${fnum(by.interest.real_change_pct)}%.`,'profile-reading');
 const components=d.spending.filter(r=>!['income','spending','other_losses'].includes(r.key));
 const box=document.createElement('div');box.style.height='310px';const canvas=document.createElement('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Variación real del gasto por componente, primer semestre 2026 frente a 2025. Los valores también están en el cuadro siguiente.');box.append(canvas);host.append(box);
 pbaSpendingChart?.destroy();
 if(typeof Chart!=='undefined')pbaSpendingChart=new Chart(canvas,{type:'bar',data:{labels:components.map(r=>r.key==='municipal_current_transfers'?['Transferencias','a municipios']:r.key==='other_transfers'?['Otras transferencias','corrientes']:r.label),datasets:[{data:components.map(r=>r.real_change_pct),backgroundColor:components.map(r=>r.real_change_pct<0?'#b84242':'#14796f'),borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:350},plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fnum(c.raw)+'% real'}}},scales:{x:{grid:{color:()=>document.documentElement.dataset.theme==='dark'?'#30465e':'#dce5ee'},ticks:{color:()=>document.documentElement.dataset.theme==='dark'?'#c9d7e5':'#536578',callback:v=>v+'%'}},y:{grid:{color:()=>document.documentElement.dataset.theme==='dark'?'#30465e':'#dce5ee'},ticks:{color:()=>document.documentElement.dataset.theme==='dark'?'#c9d7e5':'#536578',font:{size:13}}}}}});
 table('Gasto e ingresos del semestre',['Concepto','2026 · $ millones','Cambio real','% del gasto'],d.spending.map(r=>[r.label,fnum(r.current),fnum(r.real_change_pct)+'%',r.share_pct===null?'—':fnum(r.share_pct)+'%']),2);
 budgetParagraph(host,'Real significa descontando inflación. El gasto semestral se ajusta por el IPC promedio de cada semestre. Personal mide la masa salarial, no el sueldo de cada empleado; capital incluye obras, equipamiento e inversión financiera. Rojo indica caída y verde aumento, no una evaluación de la gestión.');
 const cap=d.capital;
 heading('La inversión, abierta por destino');
 budgetParagraph(host,`En el primer semestre, el gasto de capital cayó ${fnum(Math.abs(cap.totals.capital.real_change_pct))}% real. La inversión directa —obras y equipamiento— explica ${fnum(cap.totals.direct.real_change/cap.totals.capital.real_change*100)}% de esa reducción. Educación y energía aumentaron su inversión directa; transporte, vivienda y saneamiento la redujeron.`,'profile-reading');
 const chosen=['4-30','3-80','3-70','3-40','4-40','3-10','4-10'];
 table('Obras y equipamiento por función · primer semestre',['Función','2026 · $ millones','Cambio real'],chosen.map(id=>{const r=cap.functions.find(x=>x.id===id);return [r.name,fnum(r.direct.current),fnum(r.direct.real_change_pct)+'%'];}),2);
 budgetParagraph(host,'El cuadro muestra siete destinos de la inversión directa. La apertura completa incluye 28 funciones. Las transferencias de capital y los aportes financieros se muestran por separado: no se suman como si fueran obras ejecutadas por la Provincia.');
 table('Componentes del gasto de capital',['Componente','2026 · $ millones','Cambio real'],[['direct','Obras y equipamiento'],['transfers','Transferencias de capital'],['financial','Inversión financiera']].map(([k,label])=>[label,fnum(cap.totals[k].current),fnum(cap.totals[k].real_change_pct)+'%']),2);
 const orgNames={'55':'Vialidad','84':'Cultura y Educación','57':'Instituto de la Vivienda','53':'Infraestructura','137':'Cuenca del río Luján','62':'Cuenca del río Reconquista'};
 table('Gasto de capital por organismo · otra apertura del mismo total',['Organismo','2026 · $ millones','Cambio real'],Object.entries(orgNames).map(([id,label])=>{const r=cap.institutions.find(x=>x.id===id);return [label,fnum(r.capital.current),fnum(r.capital.real_change_pct)+'%'];}),2);
 budgetParagraph(host,'Por obra: el mapa provincial permite identificar proyectos y avances. Todavía falta una ejecución semestral comparable por proyecto para cuantificar cuánto se recortó en cada ruta, escuela u obra hidráulica.');
 for(const [url,label] of [[cap.projects_url,'Explorar las obras de la Provincia'],['data/pba_capital_detail.json','Apertura completa · 28 funciones y 53 organismos']]){const p=document.createElement('p'),a=document.createElement('a');a.href=url;a.textContent=label;a.target='_blank';a.rel='noopener';p.append(a);host.append(p);}
 managementSource(host,cap.sources.find(s=>s.year===2026&&s.id==='APNF'&&s.kind==='FinFun').url,'CGP · ejecución oficial por función');
 heading('Qué impuestos explican la recaudación');
 budgetParagraph(host,d.revenue_period+' frente a los mismos meses de 2025 · ajuste por inflación mes a mes. Los importes del cuadro son pesos corrientes.');
 const labels={Total:'Recaudación propia total',Iibb:'Ingresos Brutos',Sellos:'Sellos',Inmobiliario:'Inmobiliario',Automotores:'Automotor',Otros:'Otros impuestos y planes'};
 table('Recaudación acumulada por impuesto',['Impuesto','2025 · $ millones','2026 · $ millones','Cambio real'],d.revenue.map(r=>[labels[r.tax],fnum(r.previous),fnum(r.current),fnum(r.real_change_pct)+'%']),3);
 budgetParagraph(host,'Una suba nominal puede esconder una caída del poder de compra. Las diferencias entre impuestos también pueden responder al calendario de vencimientos y a planes de regularización.');
 managementSource(host,d.sources[0].url,'PBA · recaudación mensual 2025');managementSource(host,d.sources[1].url,'PBA · recaudación mensual 2026');managementSource(host,d.execution_source.url,'PBA · ejecución del primer semestre, página 13');managementSource(host,'data/pba_comparison.json','Ver datos y método de cálculo');
}

// Keep an observed spending floor distinct from money available to spend.
function overviewCommittedDescription(row){
 const number=value=>value===null||value===undefined||String(value).trim()===''?null:Number(value);
 if(!row||[row.total_rigid_pct,row.observed_floor_pct].every(v=>number(v)===null))return 'Faltan componentes comparables del gasto.';
 const components=[['personal',row.personnel_pct],['jubilaciones',row.social_security_spending_pct],['intereses',row.interest_pct],['transferencias a municipios',row.automatic_transfers_pct]].filter(([,v])=>number(v)>0).map(([name])=>name);
 const names=components.length>1?components.slice(0,-1).join(', ')+(components.at(-1)==='intereses'?' e ':' y ')+components.at(-1):components[0]||'los componentes informados';
 return 'Como mínimo, esta parte de los ingresos se destina a '+names+'. El resto debe cubrir otros gastos.';
}
function overviewServiceMetric(pillars){
 for(const pillar of pillars||[]){
  if(pillar.indicator_type!=='resultado')continue;
  const metric=(pillar.metrics||[]).find(m=>m.value!==null&&m.value!==undefined&&m.display&&m.status==='auditado');
  if(metric)return {...metric,pillarLabel:pillar.label};
 }
 return null;
}
/* Executive reading uses the same observations as the detailed sections. */
function initProvincialOverview(){
 const labels={summary:'Resumen',income:'Ingresos y gasto',debt:'Deuda y vencimientos',federal:'Relación con Nación',results:'Servicios y resultados',comparison:'Comparación'};
 const parents={openHistory:'comparison',openMap:'comparison',openOperations:'debt'};
 const navigation=document.querySelector('.visible-navigation nav'),picker=document.getElementById('mobileViewPicker');
 for(const button of [...navigation.children]){if(button.dataset.page.startsWith('open'))button.remove();else button.textContent=labels[button.dataset.page];}
 for(const key of Object.keys(labels))navigation.append(navigation.querySelector(`[data-page="${key}"]`));
 const route=key=>{picker.value=key;picker.dispatchEvent(new Event('change'));};
 const sub=document.createElement('nav');sub.className='province-subnav';sub.setAttribute('aria-label','Vistas de la sección');document.querySelector('.dashboard-command-bar').after(sub);
 function syncRoute(active=dashboardView){
  const parent=parents[active]||active;
  navigation.querySelectorAll('button').forEach(b=>b.setAttribute('aria-current',b.dataset.page===parent?'page':'false'));
  const context=document.querySelector('.mobile-navigation-context');context.textContent=[currentProvince,labels[parent]||'Ayuda'].join(' · ');
  sub.replaceChildren();const items=parent==='comparison'?[['comparison','Indicadores'],['openMap','Mapa'],['openHistory','Historia fiscal']]:parent==='debt'?[['debt','Deuda y pagos'],['openOperations','Caja y escenarios']]:[];
  sub.hidden=!items.length;
  for(const [key,label] of items){const b=document.createElement('button');b.type='button';b.textContent=label;b.setAttribute('aria-current',key===active?'page':'false');b.onclick=()=>route(key);sub.append(b);}
 }
 window.addEventListener('dashboard:view',e=>syncRoute(e.detail.view));syncRoute();
 const compact=matchMedia('(max-width:640px), (max-width:950px) and (max-height:500px)');
 const command=document.querySelector('.dashboard-command-bar'),commandAnchor=document.createComment('reading-controls');command.before(commandAnchor);
 let exportAnchor=null;
 function reflow(){
  const menu=document.getElementById('visibleNavigationContent'),report=document.querySelector('.management-report-export');
  if(report&&!exportAnchor){exportAnchor=document.createComment('report-controls');report.before(exportAnchor);}
  if(compact.matches){menu.append(command);if(report)menu.append(report);}else{commandAnchor.after(command);if(report&&exportAnchor)exportAnchor.after(report);}
 }
 compact.addEventListener('change',reflow);reflow();requestAnimationFrame(reflow);
 const help=document.createElement('button');help.className='province-help';help.type='button';help.textContent='Cómo leer los datos';help.onclick=()=>route('openGuide');document.querySelector('.footer')?.append(help);
 if(!help.isConnected)document.querySelector('.dashboard-command-bar').append(help);
 const grid=document.createElement('section');grid.id='provinceDecisionCards';grid.setAttribute('aria-label','Cinco claves de la provincia');document.querySelector('.executive-pulse').before(grid);
 const text=id=>document.getElementById(id)?.textContent.trim()||'Sin dato';
 const date=x=>x?x.split('-').reverse().join('/'):'Corte no disponible';
 function refresh(){
  const province=currentProvince,rigid=rigidSpendRows.find(r=>canonicalProvinceName(r.province)===province);
  const floor=rigid?toN(rigid.total_rigid_pct)??toN(rigid.observed_floor_pct):null;
  const peak=(province==='Buenos Aires'?debtScheduleRows:[]).filter(r=>Number(r.year)>=2027).reduce((a,b)=>Number(b.total_service_ars_m)>Number(a?.total_service_ars_m||0)?b:a,null);
  const pillars=governmentResults?.provinces?.[province]?.pillars||[];
  const metric=overviewServiceMetric(pillars);
  const rows=[
   {key:'accounts',q:'¿Alcanzan los ingresos?',value:text('kResFin'),description:text('kResFinReading'),period:document.querySelector('#kResFin')?.closest('.kcard')?.querySelector('.pulse-tag')?.textContent||'',view:'income',link:'Ver ingresos y gasto',tone:/[-−]/.test(text('kResFin'))?'negative':/[1-9]/.test(text('kResFin'))?'positive':'neutral'},
   {key:'margin',q:'¿Cuánto ingreso está comprometido?',value:floor===null?'Sin dato':floor.toLocaleString('es-AR',{maximumFractionDigits:1})+'%',description:overviewCommittedDescription(rigid),period:rigid?'Doce meses al '+date(rigid.cutoff):'',view:'income',target:'rigidSpendSection',link:'Ver composición del gasto'},
   {key:'debt',q:peak?'¿Qué vence y cuándo?':'¿Cuánto pesa la deuda?',value:peak?'$'+(Number(peak.total_service_ars_m)/1e6).toLocaleString('es-AR',{maximumFractionDigits:2})+' billones':text('kDebt'),description:peak?'Capital e intereses previstos para '+peak.year+'.':(/[0-9]/.test(text('kDebt'))?'Deuda acumulada como porcentaje de los ingresos de un año. No es lo que vence este año.':'No hay un stock de deuda comparable para esta provincia.'),period:peak?'Valuación al '+date(peak.valuation_date):(/[0-9]/.test(text('kDebt'))?'Stock al '+date(latestFiscalDetails?.cutoff)+' · ingresos de doce meses':'Sin stock comparable disponible'),view:'debt',link:'Ver deuda y vencimientos'},
   {key:'nation',q:'¿Qué recibe de Nación?',value:text('kRonYtd'),description:'Fondos recibidos de Nación durante el período indicado.',period:[document.getElementById('kRonYtd')?.closest('.kcard')?.querySelector('.k-lbl')?.textContent,document.getElementById('kRonYtd')?.closest('.kcard')?.querySelector('.pulse-tag')?.textContent].filter(Boolean).join(' · '),view:'federal',link:'Ver relación con Nación'},
   {key:'services',q:metric?.id==='homicide_rate'?'Seguridad: homicidios':metric?.pillarLabel||'Servicios y resultados',value:metric?.display||'Sin dato comparable',description:metric?(metric.id==='homicide_rate'?'Víctimas por cada 100.000 habitantes. Una tasa más baja es mejor.':metric.label):'Faltan resultados oficiales comparables para esta provincia.',period:metric?metric.period+(metric.rank?' · Puesto '+metric.rank+' de '+metric.rank_total+(metric.direction==='lower_is_better'?' · 1 = menor tasa':metric.direction==='higher_is_better'?' · 1 = mayor valor':''):''):'',view:'results',link:'Ver salud, educación y seguridad'}
  ];
  for(const row of rows){
   let card=grid.querySelector(`[data-key="${row.key}"]`);
   if(!card){
    card=document.createElement('article');card.className='province-decision-card';card.dataset.key=row.key;
    for(const tag of ['h3','strong','p','small','button'])card.append(document.createElement(tag));
    card.lastElementChild.type='button';grid.append(card);
   }
   const [h,value,description,period,link]=card.children;
   h.textContent=row.q;value.className='decision-value '+(row.tone||'neutral');value.textContent=row.value;
   description.textContent=row.description;period.textContent=row.period;link.textContent=row.link+' →';
   link.onclick=()=>{route(row.view);(row.target?document.getElementById(row.target):document.querySelector(`[data-view-panel="${row.view}"]`))?.scrollIntoView({block:'start',behavior:'instant'});};
  }
 }
 const observer=new MutationObserver(refresh);
 for(const id of ['kResFin','kDebt','kRonYtd','rigidSpendValue','governmentResultsGrid']){const node=document.getElementById(id);if(node)observer.observe(node,{subtree:true,childList:true,characterData:true});}
 document.addEventListener('change',refresh);refresh();
}

if(typeof module!=='undefined')module.exports={overviewCommittedDescription,overviewServiceMetric};

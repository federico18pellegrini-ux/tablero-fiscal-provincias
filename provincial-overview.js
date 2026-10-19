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
  const metric=pillars.filter(p=>p.indicator_type==='resultado').flatMap(p=>p.metrics||[]).find(m=>m.value!==null&&m.display);
  const rows=[
   {key:'accounts',q:'¿Alcanzan los ingresos?',value:text('kResFin'),description:text('kResFinReading'),period:document.querySelector('#kResFin')?.closest('.kcard')?.querySelector('.pulse-tag')?.textContent||'',view:'income',link:'Ver ingresos y gasto',tone:/[-−]/.test(text('kResFin'))?'negative':/[1-9]/.test(text('kResFin'))?'positive':'neutral'},
   {key:'margin',q:'¿Cuánto margen hay?',value:floor===null?'Sin dato':floor.toLocaleString('es-AR',{maximumFractionDigits:1})+'%',description:floor===null?'Faltan componentes comparables del gasto.':'De los ingresos destinados a personal, jubilaciones e intereses'+(toN(rigid.automatic_transfers_pct)!==null?' y transferencias a municipios.':'.')+' El resto también debe cubrir otros gastos.',period:rigid?'Doce meses al '+date(rigid.cutoff):'',view:'income',link:'Ver composición del gasto'},
   {key:'debt',q:peak?'¿Qué vence y cuándo?':'¿Cuánto pesa la deuda?',value:peak?'$'+(Number(peak.total_service_ars_m)/1e6).toLocaleString('es-AR',{maximumFractionDigits:2})+' billones':text('kDebt'),description:peak?peak.year+': el mayor pago anual del calendario publicado. Incluye capital e intereses.':'Deuda provincial respecto de los ingresos de un año. El detalle distingue stock y calendario disponible.',period:peak?'Valuación al '+date(peak.valuation_date):(/[0-9]/.test(text('kDebt'))?'Stock al 30/06/2026 · comparación provincial':'Sin stock comparable disponible'),view:'debt',link:'Ver deuda y vencimientos'},
   {key:'nation',q:'¿Qué recibe de Nación?',value:text('kRonYtd'),description:'Transferencias nacionales acumuladas. En el detalle: evolución, comparación por habitante y reclamos publicados.',period:[document.getElementById('kRonYtd')?.closest('.kcard')?.querySelector('.k-lbl')?.textContent,document.getElementById('kRonYtd')?.closest('.kcard')?.querySelector('.pulse-tag')?.textContent].filter(Boolean).join(' · '),view:'federal',link:'Ver relación con Nación'},
   {key:'services',q:'¿Cómo están los servicios?',value:metric?.display||'Sin dato comparable',description:metric?metric.label:'Faltan resultados oficiales comparables para esta provincia.',period:metric?metric.period+(metric.rank?' · Puesto '+metric.rank+' de '+metric.rank_total:''):'',view:'results',link:'Ver salud, educación y seguridad'}
  ];
  grid.replaceChildren();
  for(const row of rows){const card=document.createElement('article');card.className='province-decision-card';card.dataset.key=row.key;const h=document.createElement('h3');h.textContent=row.q;const value=document.createElement('strong');value.className='decision-value '+(row.tone||'neutral');value.textContent=row.value;const description=document.createElement('p');description.textContent=row.description;const period=document.createElement('small');period.textContent=row.period;const link=document.createElement('button');link.type='button';link.textContent=row.link+' →';link.onclick=()=>{route(row.view);document.querySelector(`[data-view-panel="${row.view}"]`)?.scrollIntoView({block:'start',behavior:'instant'});};card.append(h,value,description,period,link);grid.append(card);}
 }
 const observer=new MutationObserver(refresh);
 for(const id of ['kResFin','kDebt','kRonYtd','rigidSpendValue','governmentResultsGrid']){const node=document.getElementById(id);if(node)observer.observe(node,{subtree:true,childList:true,characterData:true});}
 document.addEventListener('change',refresh);refresh();
}

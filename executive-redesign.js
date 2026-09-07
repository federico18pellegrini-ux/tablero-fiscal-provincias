/* Presentation only: reuse the observed data and existing navigation actions. */
function initExecutiveRedesign(){
  const header=document.querySelector('.header'),title=document.getElementById('heroTitle');
  title.classList.add('fixed-dashboard-title');header.append(title);document.querySelector('.hero').classList.add('title-relocated');
  const measureHeader=()=>document.documentElement.style.setProperty('--fixed-header-height',header.getBoundingClientRect().height+'px');
  new ResizeObserver(measureHeader).observe(header);measureHeader();
  const aside=document.createElement('aside');aside.className='executive-sidebar';aside.setAttribute('aria-label','Secciones del tablero');
  const heading=document.createElement('p');heading.className='sidebar-title';heading.textContent='Explorar la gestión';aside.append(heading);
  const nav=document.querySelector('.dashboard-nav'),tools=document.querySelector('.federal-shortcuts');
  aside.append(nav,tools);tools.append(tools.querySelector('#openGuide'));document.body.append(aside);
  const picker=document.querySelector('.mobile-view-picker');document.querySelector('.hero').after(picker);
  const theme=document.createElement('button');theme.type='button';theme.id='themeToggle';theme.className='theme-toggle';aside.append(theme);
  let stored='light';try{stored=localStorage.getItem('fiscal-theme')||'light';}catch{}
  const setTheme=value=>{document.documentElement.dataset.theme=value;theme.textContent=value==='dark'?'Usar fondo claro':'Usar fondo oscuro';theme.setAttribute('aria-pressed',String(value==='dark'));try{localStorage.setItem('fiscal-theme',value);}catch{}if(typeof Chart!=='undefined')Object.values(Chart.instances).forEach(c=>c.update('none'));};
  theme.onclick=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');setTheme(stored==='dark'?'dark':'light');
  const mobileTheme=document.createElement('button');mobileTheme.type='button';mobileTheme.className='mobile-theme';mobileTheme.textContent='Cambiar tema';mobileTheme.onclick=()=>theme.click();document.querySelector('.header').append(mobileTheme);
  const sync=()=>{const opened=document.querySelector('#federalTools > details[open]');document.body.classList.toggle('tool-context',!!opened);nav.querySelectorAll('button').forEach(b=>b.setAttribute('aria-current',!opened&&b.classList.contains('active')?'page':'false'));};
  document.querySelectorAll('#federalTools > details').forEach(p=>p.addEventListener('toggle',sync));
  nav.addEventListener('click',e=>{if(!e.target.closest('[data-view]'))return;document.querySelectorAll('#federalTools > details').forEach(p=>p.open=false);sync();window.scrollTo({top:0,behavior:'smooth'});});
  const extras=document.createElement('section');extras.className='overview-extra';extras.innerHTML='<h3>Resultado primario y posición en el ranking</h3><div class="overview-extra-grid"></div>';
  for(const id of ['kResPri','kRank'])extras.lastElementChild.append(document.getElementById(id).closest('.kcard'));
  const pulse=document.querySelector('.executive-pulse');pulse.append(extras);
  const overview=document.createElement('section');overview.className='overview-charts';overview.setAttribute('aria-label','Evolución y comparación');overview.innerHTML='<article><h3>¿Cómo evolucionó?</h3><p>Resultado financiero por cada $100 de ingresos. Cada punto acumula doce meses.</p><div class="overview-canvas"><canvas id="overviewTrend" role="img" aria-label="Evolución del resultado financiero"></canvas></div><p id="overviewTrendReading"></p><button type="button" id="overviewHistoryLink">Explorar la historia →</button></article><article><h3>¿Cómo se compara?</h3><p>Mismo indicador y cierre para las jurisdicciones con dato. La seleccionada aparece en azul.</p><div class="overview-canvas"><canvas id="overviewPeers" role="img" aria-label="Comparación provincial del resultado financiero"></canvas></div><p id="overviewPeersReading"></p><button type="button" id="overviewCompareLink">Ver la comparación completa →</button></article>';pulse.after(overview);
  document.getElementById('overviewHistoryLink').onclick=()=>document.getElementById('openHistory').click();document.getElementById('overviewCompareLink').onclick=()=>{applyDashboardView('comparison');sync();window.scrollTo({top:0,behavior:'smooth'});};
  document.getElementById('psel').addEventListener('change',renderExecutiveOverview);renderExecutiveOverview();sync();initInflationHistory();initVisibleControls();
  document.addEventListener('click',event=>{const link=event.target.closest('[data-editorial-view]');if(!link)return;const picker=document.getElementById('mobileViewPicker');picker.value=link.dataset.editorialView;picker.dispatchEvent(new Event('change'));window.scrollTo({top:0,behavior:'smooth'});});
}
let overviewTrend=null,overviewPeers=null;
function renderExecutiveOverview(){
  if(typeof Chart==='undefined'||!fiscalHistory?.rows)return;
  const province=document.getElementById('psel').value,rows=fiscalHistory.rows.filter(r=>r.province===province).sort((a,b)=>a.period.localeCompare(b.period));
  const last=historyPeriods().at(-1),peers=fiscalHistory.rows.filter(r=>r.period===last&&Number.isFinite(r.financial_pct)).sort((a,b)=>b.financial_pct-a.financial_pct);
  overviewTrend?.destroy();overviewPeers?.destroy();
  const options={responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{maxTicksLimit:6}},y:{title:{display:true,text:'% de ingresos'}}}};
  overviewTrend=new Chart(document.getElementById('overviewTrend'),{type:'line',data:{labels:historyPeriods().map(periodName),datasets:[{label:'Resultado financiero',data:historyPeriods().map(p=>rows.find(r=>r.period===p)?.financial_pct??null),borderColor:'#2863aa',backgroundColor:'#2863aa',pointRadius:2,borderWidth:2,spanGaps:false}]},options});
  overviewPeers=new Chart(document.getElementById('overviewPeers'),{type:'bar',data:{labels:peers.map(r=>r.province),datasets:[{label:'Resultado financiero',data:peers.map(r=>r.financial_pct),backgroundColor:peers.map(r=>r.province===province?'#2863aa':'#899eb7')}]},options:{...options,indexAxis:'y',scales:{x:{title:{display:true,text:'% de ingresos'}},y:{ticks:{autoSkip:false,font:{size:10}}}}}});
  const latest=rows.find(r=>r.period===last);document.getElementById('overviewTrendReading').textContent=latest?`${province}: ${fnum(latest.financial_pct)}% al ${periodName(last)}.`:`${province}: sin observación en ${periodName(last)}. No se prolonga el último dato.`;
  document.getElementById('overviewPeersReading').textContent=`${peers.length} jurisdicciones · ${periodName(last)}. Un saldo mayor no mide por sí solo la calidad de gestión.`;
}
if(typeof Chart!=='undefined')Chart.register({id:'executiveTheme',beforeUpdate(chart){
  const dark=document.documentElement.dataset.theme==='dark',text=dark?'#c2cede':'#475569',grid=dark?'#29394e':'#e3e9f0';
  for(const scale of Object.values(chart.options.scales||{})){if(scale.ticks)scale.ticks.color=text;if(scale.title)scale.title.color=text;if(scale.grid)scale.grid.color=grid;}
  const legend=chart.options.plugins?.legend;if(legend?.labels)legend.labels.color=text;
}});

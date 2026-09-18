/* Presentation only: reuse the observed data and existing navigation actions. */
function initExecutiveRedesign(){
  const header=document.querySelector('.header'),title=document.getElementById('heroTitle');
  title.classList.add('fixed-dashboard-title');header.querySelector('.brand-text').prepend(title);document.querySelector('.hero').classList.add('title-relocated');
  const measureHeader=()=>document.documentElement.style.setProperty('--fixed-header-height',header.getBoundingClientRect().height+'px');
  new ResizeObserver(measureHeader).observe(header);measureHeader();
  const aside=document.createElement('aside');aside.className='executive-sidebar';aside.setAttribute('aria-label','Secciones del tablero');
  const heading=document.createElement('p');heading.className='sidebar-title';heading.textContent='Explorar la gestión';aside.append(heading);
  const nav=document.querySelector('.dashboard-nav'),tools=document.querySelector('.federal-shortcuts');
  aside.append(nav,tools);tools.append(tools.querySelector('#openGuide'));document.body.append(aside);
  const picker=document.querySelector('.mobile-view-picker');document.querySelector('.hero').after(picker);
  const theme=document.createElement('button');theme.type='button';theme.id='themeToggle';theme.className='theme-toggle';aside.append(theme);
  const mobileTheme=document.createElement('button');mobileTheme.type='button';mobileTheme.className='mobile-theme';document.querySelector('.header').append(mobileTheme);
  const setTheme=value=>{
    const dark=value==='dark',action=dark?'claro':'oscuro';
    document.documentElement.dataset.theme=value;
    theme.textContent='Usar fondo '+action;mobileTheme.textContent=dark?'☀ Claro':'☾ Oscuro';
    for(const button of [theme,mobileTheme]){button.setAttribute('aria-label','Cambiar a modo '+action);button.title='Cambiar a modo '+action;button.setAttribute('aria-pressed',String(dark));}
    document.querySelector('meta[name="theme-color"]').content='#0A192F';
    if(typeof Chart!=='undefined')Object.values(Chart.instances).forEach(c=>c.update('none'));
  };
  theme.onclick=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');
  mobileTheme.onclick=()=>theme.click();setTheme('light');
  const sync=()=>{const opened=document.querySelector('#federalTools > details[open]');document.body.classList.toggle('tool-context',!!opened);nav.querySelectorAll('button').forEach(b=>b.setAttribute('aria-current',!opened&&b.classList.contains('active')?'page':'false'));};
  document.querySelectorAll('#federalTools > details').forEach(p=>p.addEventListener('toggle',sync));
  nav.addEventListener('click',e=>{if(!e.target.closest('[data-view]'))return;document.querySelectorAll('#federalTools > details').forEach(p=>p.open=false);sync();window.scrollTo({top:0,behavior:'smooth'});});
  const extras=document.createElement('section');extras.className='overview-extra';extras.setAttribute('aria-label','Ingresos y contexto fiscal');extras.innerHTML='<h3>Ingresos y contexto fiscal</h3><div class="overview-extra-grid"></div>';
  for(const id of ['kTopYtd','kRonYtd','kResPri','kRank'])extras.lastElementChild.append(document.getElementById(id).closest('.kcard'));
  extras.append(document.getElementById('fiscalRatiosMethodNote'));
  const pulse=document.querySelector('.executive-pulse');pulse.after(extras);
  for(const [id,label,view] of [['kResFin','Ver ingresos y gasto','income'],['kDebt','Ver deuda y vencimientos','debt']]){
    const link=document.createElement('button');link.type='button';link.className='summary-detail-link';link.dataset.editorialView=view;link.textContent=label+' →';document.getElementById(id).closest('.kcard').append(link);
  }
  const compare=document.createElement('button');compare.type='button';compare.id='overviewCompareLink';compare.className='summary-detail-link';compare.textContent='Abrir comparación →';document.getElementById('kRank').closest('.kcard').append(compare);
  const overview=document.createElement('section');overview.className='overview-charts summary-trend';overview.setAttribute('aria-label','Evolución del resultado fiscal');overview.innerHTML='<article><div class="summary-trend-heading"><div><h3>¿El resultado mejora o empeora?</h3><p>Resultado financiero por cada $100 de ingresos. Cada punto acumula doce meses.</p></div><button type="button" id="overviewHistoryLink">Explorar la historia →</button></div><div class="overview-canvas"><canvas id="overviewTrend" role="img" aria-label="Evolución del resultado financiero"></canvas></div><p id="overviewTrendReading"></p></article>';extras.after(overview);
  document.getElementById('overviewHistoryLink').onclick=()=>document.getElementById('openHistory').click();document.getElementById('overviewCompareLink').onclick=()=>{applyDashboardView('comparison');sync();window.scrollTo({top:0,behavior:'smooth'});};
  document.getElementById('psel').addEventListener('change',renderExecutiveOverview);renderExecutiveOverview();renderProfileReadings();sync();initInflationHistory();initVisibleControls();
  document.addEventListener('click',event=>{const link=event.target.closest('[data-editorial-view]');if(!link)return;const picker=document.getElementById('mobileViewPicker');picker.value=link.dataset.editorialView;picker.dispatchEvent(new Event('change'));if(link.hasAttribute('data-summary-claim-link')){const section=document.getElementById('nationDebtSection'),heading=section.querySelector('h2');heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true});section.scrollIntoView({block:'start',behavior:'instant'});}else window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});});
}
let overviewTrend=null;
function renderExecutiveOverview(){
  if(typeof Chart==='undefined'||!fiscalHistory?.rows)return;
  const province=document.getElementById('psel').value,rows=fiscalHistory.rows.filter(r=>r.province===province).sort((a,b)=>a.period.localeCompare(b.period));
  const last=historyPeriods().at(-1);
  overviewTrend?.destroy();
  const options={responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{maxTicksLimit:6}},y:{title:{display:true,text:'% de ingresos'}}}};
  overviewTrend=new Chart(document.getElementById('overviewTrend'),{type:'line',data:{labels:historyPeriods().map(periodName),datasets:[{label:'Resultado financiero',data:historyPeriods().map(p=>rows.find(r=>r.period===p)?.financial_pct??null),borderColor:'#2863aa',backgroundColor:'#2863aa',pointRadius:2,borderWidth:2,spanGaps:false}]},options});
  const latest=rows.find(r=>r.period===last);document.getElementById('overviewTrendReading').textContent=latest?`${province}: ${fnum(latest.financial_pct)}% al ${periodName(last)}.`:`${province}: sin observación en ${periodName(last)}. No se prolonga el último dato.`;
}
// Keep the original series distinctions while matching the shared dashboard palette.
// Values, signs, chart types and the correspondence with external legends are unchanged.
function provincialChartColor(value,dark){
  if(Array.isArray(value))return value.map(color=>provincialChartColor(color,dark));
  if(typeof value!=='string')return value;
  const groups=[
    [['#60a5fa','#68b7ff','#2863aa','#3675bd','#327f88','#82c5c8','#254b73','#8eaed1'],'#254b73','#8eaed1'],
    [['#4ade80','#6bd5b5','#14695c','#8ed2b5','#8398b1','#8b99ad'],'#8398b1','#8b99ad'],
    [['#fbbf24','#ffb05c','#f6d273','#d79720','#a5782d','#e3bd75','#b8924a','#dfba77'],'#b8924a','#dfba77'],
    [['#a78bfa','#d6a3ff','#817699','#bcadd9','#756587','#baabd0'],'#756587','#baabd0'],
    [['#f87171','#ff5f5f','#b42318','#ff9b91','#b91c1c'],'#b91c1c','#ff9b91'],
    [['#64748b','#7c9088','#aabeb5','#94a3b8','#a6b5ca'],'#94a3b8','#a6b5ca'],
    [['#111827','#ffffff','#1c302c','#12253e'],'#ffffff','#12253e']
  ];
  const match=value.toLowerCase().match(/^(#[\da-f]{6})([\da-f]{2})?$/);
  if(match){const group=groups.find(([colors])=>colors.includes(match[1]));return group?group[dark?2:1]+(match[2]||''):value;}
  return value;
}
if(typeof Chart!=='undefined'){
 Chart.defaults.font.family='Geist, system-ui, sans-serif';
 Chart.defaults.font.size=14;
 Chart.register({id:'executiveTheme',beforeUpdate(chart){
  const dark=document.documentElement.dataset.theme==='dark',text=dark?'#a6b5ca':'#64748b',grid=dark?'#31465e':'#e2e8f0';
  for(const scale of Object.values(chart.options.scales||{})){if(scale.ticks){scale.ticks.color=text;scale.ticks.font={...scale.ticks.font,family:'Geist',size:14};}if(scale.title)scale.title.color=text;if(scale.grid)scale.grid.color=grid;if(scale.border)scale.border.color=grid;}
  const legend=chart.options.plugins?.legend;if(legend?.labels)legend.labels.color=text;
  for(const dataset of chart.data.datasets)for(const key of ['borderColor','backgroundColor','pointBackgroundColor','pointBorderColor','hoverBackgroundColor'])if(dataset[key])dataset[key]=provincialChartColor(dataset[key],dark);
 }});
}

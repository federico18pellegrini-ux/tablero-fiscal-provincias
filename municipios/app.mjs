import {METRICS, BUDGET_BASES, rankingMetric, rankingExportRows, metricExportUnit, TRANSPARENCY_COMPONENTS, transparencyStatus, VALID_VIEWS, finite, metricValue, rankMunicipalities, peers, simulate, csv, fiscalExportRows, annualBudgetExportRows, fiscalPeriods, readState, adjustPrice, priceComparisons, municipalContextExportRows} from './model.mjs';

const $=id=>document.getElementById(id);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=(v,d=0)=>finite(v)?new Intl.NumberFormat('es-AR',{maximumFractionDigits:d,minimumFractionDigits:d}).format(v):'Sin dato';
const pct=(v,d=1)=>finite(v)?`${v>0?'+':''}${num(v,d)}%`:'Sin dato';
const money=v=>finite(v)?'$'+num(v):'Sin dato';
const millions=v=>finite(v)?'$'+num(v/1e6,1)+' M':'Sin dato';
const tone=v=>!finite(v)?'muted':v<0?'negative':v>0?'positive':'neutral';
const negativeClass=v=>finite(v)&&v<0?'negative':'';
const signedMillions=v=>finite(v)?(v<0?'−':v>0?'+':'')+millions(Math.abs(v)):'Sin dato';
const motion=()=>matchMedia('(prefers-reduced-motion: reduce)').matches?0:300;
const monthLabels=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const formatMetric=(v,meta)=>!finite(v)?'Sin dato':meta.unit==='score'?num(v)+' / 100':meta.unit==='points'?(v>0?'+':'')+num(v)+' puntos':meta.unit==='money'?money(v):meta.unit==='millions'?millions(v):meta.unit==='%'?num(v,2)+'%':meta.unit==='pp'?(v>0?'+':'')+num(v,3)+' pp':num(v,['density','branches','rate'].includes(meta.unit)?1:0);
let data,geography,rows,byId,state,mapMetric='recursos',scopePeers=false,rankAscending=true,showAll=false,fullHistory=false,mapZoom,mapProjection,mapPath,mapWidth=0;
let toastTimer;
let reportManifest=null,reportUnavailable=false;
let deflator,priceMode='real',priceBase='2026-07';
const priceMonth=p=>new Intl.DateTimeFormat('es-AR',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(p+'-15T12:00:00Z'));
function updateReportLink(m){
  const link=$('export-report'),entry=reportManifest?.reports.find(r=>r.id===m.id);
  link.setAttribute('aria-label',`Exportar informe completo de ${m.municipio}`);
  link.setAttribute('aria-disabled',String(!entry));
  $('export-report-label').textContent=reportUnavailable?'Informe en actualización':'Exportar informe completo';
  $('report-scope').textContent=entry?`${m.municipio} · PDF de ${entry.pages} páginas · Análisis y datos principales.`:reportUnavailable?'El informe está en actualización. Los datos del tablero siguen disponibles.':`Preparando el informe completo de ${m.municipio}…`;
  if(entry){link.href=`reports/${entry.file}?v=${entry.sha256}`;link.download=`informe-${m.municipio.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-')}.pdf`;}
  else link.removeAttribute('href');
}
async function prepareReports(dashboardText){
  try{
    const response=await fetch('reports/manifest.json',{cache:'no-cache'});
    if(!response.ok)throw new Error('No se pudo consultar el informe.');
    const manifest=await response.json();
    const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(dashboardText.replace(/\r\n?/g,'\n')));
    const hash=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
    if(manifest.input_sha256?.['municipios/data/dashboard.json']!==hash||!Array.isArray(manifest.reports)||manifest.reports.length!==rows.length||new Set(manifest.reports.map(r=>r.id)).size!==rows.length||manifest.reports.some(r=>r.file!==`informe-${r.id}.pdf`||!byId.has(r.id)||!Number.isInteger(r.pages)||r.pages<1||!/^[a-f0-9]{64}$/.test(r.sha256)))throw new Error('Los informes están en actualización.');
    reportManifest=manifest;
  }catch(error){reportUnavailable=true;console.warn('Informe municipal:',error.message);}
  updateReportLink(current());
}
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,3500);}
const current=()=>byId.get(state.id);
const currentMetric=()=>rankingMetric(METRICS.find(m=>m.id===state.metric),state.budgetBasis);
const latestFiscal=m=>[m.fiscal,m.fiscalOther].filter(Boolean).sort((a,b)=>b.fin.localeCompare(a.fin))[0];
function persist(){
  const url=new URL(location.href);url.search='';url.searchParams.set('municipio',state.id);url.searchParams.set('vista',state.view);if(state.view==='rankings')url.searchParams.set('indicador',state.metric);url.hash='';
  if(state.view==='rankings'&&currentMetric().budget)url.searchParams.set('presupuesto',state.budgetBasis);
  if(state.view==='recursos'){url.searchParams.set('pesos',priceMode==='real'?'reales':'corrientes');url.searchParams.set('base',priceBase);}
  history.replaceState(null,'',url);
  try{localStorage.setItem('pellegrini_municipio',state.id);}catch{}
}
function navigate(view,scroll=true){
  if(!VALID_VIEWS.includes(view))return;
  state.view=view;persist();renderView();
  window.dispatchEvent(new CustomEvent('dashboard:view',{detail:{view}}));
  if(scroll)window.scrollTo({top:0,behavior:motion()?'smooth':'instant'});
}
function selectMunicipality(id){if(!byId.has(id))return;state.id=id;persist();renderView();}
function card(label,value,context,cls=''){return `<div class="stat-card"><span class="stat-label">${label}</span><strong class="stat-value ${cls}">${value}</strong><span class="stat-context">${context}</span></div>`;}
function bindMunicipalButtons(container){container.querySelectorAll('[data-municipality]').forEach(b=>b.addEventListener('click',()=>selectMunicipality(b.dataset.municipality)));}
function renderHeader(){
  const m=current(),ranking=state.view==='rankings';
  document.body.classList.toggle('ranking-view',ranking);
  $('municipality').value=m.id;
  $('municipality-picker-label').textContent=ranking?'Referencia':'Tu municipio';
  $('municipality').setAttribute('aria-label',ranking?'Elegir municipio de referencia':'Elegir municipio');
  $('view-context').textContent=ranking?'Provincia de Buenos Aires':'Buenos Aires / 135 municipios';
  $('municipality-name').textContent=ranking?'Ranking general':m.municipio;
  $('municipality-context').textContent=ranking?'Elegí un indicador para ordenar y comparar los municipios bonaerenses.':`${num(m.poblacion_2022)} habitantes · Censo 2022 · ${num(m.superficie_km2)} km²`;
  $('share').setAttribute('aria-label',ranking?'Copiar enlace a este ranking':'Copiar enlace a esta vista');
  $('download-municipality').textContent=ranking?`Descargar datos de ${m.municipio} ↓`:'Descargar datos ↓';
  updateReportLink(m);
  document.title=ranking?'Ranking general · Municipios · Federico Pellegrini':`${m.municipio} · Municipios · Federico Pellegrini`;
}
function renderView(){
  renderHeader();
  for(const view of VALID_VIEWS){$(view).hidden=view!==state.view;document.querySelector(`[data-view="${view}"]`).setAttribute('aria-current',view===state.view?'page':'false');}
  if(state.view==='panorama')renderOverview();
  if(state.view==='rankings')renderRanking();
  if(state.view==='recursos')renderResources();
  if(state.view==='empleo')renderEmployment();
  if(state.view==='simular')renderSimulation();
}

function detailValue(value,format='number',digits=0){
  const text=!finite(value)?'Sin dato':format==='money'?'$'+num(value,digits):format==='millions'?'$'+num(value/1e6,digits)+' M':format==='share'?num(value,digits)+'%':format==='change'?pct(value,digits):num(value,digits);
  return `<span class="detail-value ${negativeClass(value)}" data-value="${finite(value)?value:''}" data-format="${format}" data-digits="${digits}">${text}</span>`;
}
function detailTable(id,caption,headers,records){
  return `<table id="${id}" class="detail-table"><caption>${escape(caption)}</caption><thead><tr>${headers.map(h=>`<th scope="col">${escape(h)}</th>`).join('')}</tr></thead><tbody>${records.map(([label,...cells])=>`<tr><th scope="row">${escape(label)}</th>${cells.map((cell,i)=>`<td data-label="${escape(headers[i+1])}">${cell}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
const sectorName=name=>({'Explotacion de minas y canteras':'Explotación de minas y canteras','Electircidad, gas y agua':'Electricidad, gas y agua','Construccion':'Construcción','Agricultura, ganaderia y pesca':'Agricultura, ganadería y pesca'}[name]||name);

function renderOverview(){
  const m=current(),r=m.variacion_transferencias_real_pct,j=m.empleo_promedio_cambio_2024_2025_pct;
  renderAnnualBudget(m,'annual-budget-overview',false);
  $('overview-headline').textContent=m.caen_empleo_y_transferencias_misma_ventana_2025_vs2024?'Menos empleo y menos recursos en 2025.':r<0?'Los recursos compran menos que hace un año.':'Las transferencias ganan poder de compra.';
  $('overview-copy').textContent=m.caen_empleo_y_transferencias_misma_ventana_2025_vs2024?`En 2025, las transferencias reales cayeron ${num(Math.abs(m.transferencias_anual_2024_2025_real_pct),1)}% y el empleo formal promedio, ${num(Math.abs(j),1)}%, frente a 2024. El último corte de recursos, enero–julio de 2026, muestra ${r<0?'una baja':'una suba'} real de ${num(Math.abs(r),1)}% frente a los mismos meses de 2025.`:`En enero–julio de 2026, las transferencias provinciales ${r<0?'cayeron':'aumentaron'} ${num(Math.abs(r),1)}% después de descontar la inflación. El empleo privado formal ${j<0?'bajó':'subió'} ${num(Math.abs(j),1)}% en el promedio de 2025 frente a 2024.`;
  const stats=[['Transferencias ajustadas por inflación',pct(r),'Ene–jul 2026 vs. 2025',tone(r)],['Empleo privado formal',pct(j),'Promedio 2025 vs. 2024',tone(j)],['Transferencias por habitante',money(m.transferencias_por_habitante_base2022_ars_jul26),'Ene–jul 2026 · pesos de julio · población 2022','currency-value'],['Hogares con carencias',num(m.hogares_nbi_2022_pct,1)+'%','Necesidades básicas insatisfechas · Censo 2022','']];
  $('overview-stats').innerHTML=stats.map(([l,v,c,t])=>`<div class="overview-stat"><span class="stat-label">${l}</span><strong class="stat-value ${t}">${v}</strong><span class="stat-context">${c}</span></div>`).join('');
  $('overview-note').textContent='Cada cifra conserva su período. Las transferencias son una parte de los ingresos; las carencias censales no son una medición actual de pobreza.';
  const diff=r-data.summary.transfer_real_change_pct;
  const fiscal=latestFiscal(m);
  const priorities=[
    ['01','Cuidar los recursos para sostener los servicios',
      `Las transferencias ${r<0?'perdieron':'ganaron'} ${num(Math.abs(r),1)}% de poder de compra en enero–julio de 2026 frente a los mismos meses de 2025. ${r<0?'Esos fondos alcanzan para menos y presionan sobre los servicios y las obras.':'Antes de convertir esa mejora en gastos permanentes, conviene verificar si se mantiene y qué fondos tienen un destino específico.'} La variación está ${num(Math.abs(diff),1)} puntos porcentuales ${diff>=0?'por encima':'por debajo'} del conjunto bonaerense.`,
      'Comparar cada mes lo que se esperaba cobrar con lo efectivamente cobrado, separando tasas propias y fondos provinciales. Actualizar el costo de los servicios esenciales permite detectar antes si hace falta reprogramar una compra o una obra.', 'Abrir los recursos','recursos',''],
    ['02','Distinguir el resultado de la plata disponible',
      fiscal?`Del ${fiscalDate(fiscal.inicio)} al ${fiscalDate(fiscal.fin)}, por cada $100 cobrados se registraron $${num(fiscal.gastos_totales/fiscal.ingresos_totales*100,1)} de gastos. ${fiscal.resultado_financiero<0?`El déficit de ${millions(Math.abs(fiscal.resultado_financiero))} exige identificar si se usaron ahorros, se tomó deuda o quedaron gastos sin pagar.`:fiscal.resultado_financiero>0?`El superávit de ${millions(fiscal.resultado_financiero)} no equivale a caja libre: puede haber obligaciones pendientes y fondos con un destino asignado.`:'Los ingresos igualaron a los gastos registrados. Eso no informa por sí solo cuánto dinero se puede usar.'}`:m.fiscalExecution?`La ejecución informa gastos devengados por ${millions(m.fiscalExecution.gastos_presupuestarios_devengados)} y pagados por ${millions(m.fiscalExecution.gastos_presupuestarios_pagados)}. Falta separar las operaciones financieras para calcular un resultado comparable.`:'Todavía falta una cuenta fiscal completa y verificada. Las transferencias provinciales son solo una parte de los ingresos y no permiten calcular déficit, inversión total ni caja libre.',
      'Reunir saldos bancarios, fondos con destino obligatorio, facturas pendientes y próximos vencimientos en una misma planilla. Así se ordenan los pagos y se distingue el resultado contable del dinero disponible. Los gastos ya registrados no se restan otra vez del resultado.', 'Ver las cuentas','recursos','fiscal-panel'],
    ['03','Entender qué está pasando con el trabajo',
      `El empleo privado registrado promedio ${j<0?'cayó':'creció'} ${num(Math.abs(j),1)}% en 2025 frente a 2024. ${j<0?'La caída puede afectar a las familias y a los comercios que dependen de esos ingresos.':'El crecimiento abre oportunidades, aunque puede concentrarse en pocos sectores o empresas.'} Son puestos en establecimientos del municipio; no mide desocupación ni describe el empleo de 2026.`,
      'Revisar los sectores de mayor peso y contrastarlos con habilitaciones, actividad comercial y cobranza de tasas. Priorizar formación laboral, trámites o infraestructura cuando se identifique una necesidad concreta. Después, medir si mejoran el empleo y la actividad.', 'Mirar el empleo','empleo','']
  ];
  $('insights').innerHTML=priorities.map(([n,t,why,next,label,view,target])=>`<article class="insight"><span class="number">${n} /</span><h3>${t}</h3><p><strong>Por qué la elegimos.</strong> ${why}</p><p><strong>Qué recomendamos.</strong> ${next}</p><button class="text-button" data-insight-view="${view}" data-insight-target="${target}">${label} →</button></article>`).join('');
  $('insights').querySelectorAll('button').forEach(b=>b.onclick=()=>{navigate(b.dataset.insightView,!b.dataset.insightTarget);if(b.dataset.insightTarget)$(b.dataset.insightTarget).scrollIntoView({behavior:motion()?'smooth':'instant',block:'start'});});
  $('pulse-transfers').textContent=num(data.summary.municipalities_falling_transfers);$('pulse-both').textContent=num(data.summary.same_window_2025_vs2024_both_falling);
  renderCommunity();
  renderTransparency();
  drawMap();
}
function renderCommunity(){
  const m=current(),c=m.community,h=c.health,a=c.crime['2024'],b=c.crime['2025'];
  $('community-panel').innerHTML=`<div class="eyebrow">La vida cotidiana</div><h2>Población, salud, vivienda y seguridad</h2><p>Estas cifras ayudan a entender necesidades de la población. Cada tema tiene su propia fecha.</p>${detailTable('population-detail','Población y hogares',['Indicador','Censo 2022'],[
    ['Habitantes',detailValue(m.poblacion_2022)],['Hogares',detailValue(m.hogares_2022)],['Hogares con necesidades básicas insatisfechas',detailValue(m.hogares_nbi_2022)],['Superficie, km²',detailValue(m.superficie_km2)],['Habitantes por km²',detailValue(m.densidad_2022,'number',1)],['Cambio de población entre 2010 y 2022',detailValue(m.crecimiento_poblacion_2010_2022_pct,'change',1)]
  ])}<p class="chart-caption">El porcentaje de hogares con carencias utiliza el total de hogares. El cambio de población queda sin dato cuando no se homologaron los límites territoriales entre censos.</p><div class="stats-grid community-social">${card('Sin obra social, prepaga ni plan estatal',num(h.withoutCoveragePct,1)+'%',`${num(h.withoutCoverage)} personas · Censo 2022`)}${card('Más de 3 personas por cuarto',num(c.crowding.over3PersonsPerRoomPct,1)+'%','Porcentaje de hogares · Censo 2022')}</div><p>La cobertura se calcula sobre ${num(h.populationPrivateDwellings)} personas en viviendas particulares. No tener esa cobertura no significa quedar sin atención pública. Permite dimensionar la población que puede necesitar esa red. Más de tres personas por cuarto indica hacinamiento y puede orientar la política de vivienda.</p><p class="chart-caption">NBI significa <strong>necesidades básicas insatisfechas</strong>: hogares con al menos una carencia de vivienda, hacinamiento, retrete, escolaridad o capacidad de subsistencia, según el criterio censal. No equivale a pobreza actual por ingresos.</p><h3>Delitos registrados, 2024 y 2025</h3><div class="stats-grid">${card('Robos consumados',num(b.robberies),`2025 · ${num(a.robberies)} en 2024<br>${num(b.robberyRate,1)} por 100.000 habitantes en 2025`)}${card('Hurtos consumados',num(b.thefts),`2025 · ${num(a.thefts)} en 2024<br>${num(b.theftRate,1)} por 100.000 habitantes en 2025`)}${card('Víctimas de homicidios dolosos',num(b.homicideVictims),`2025 · ${num(a.homicideVictims)} en 2024<br>${num(b.homicideRate,1)} por 100.000 habitantes en 2025`)}</div><p>Robo implica fuerza o violencia; hurto, sustracción sin esos medios. Homicidio doloso refiere a una muerte intencional. Los robos incluyen los agravados y excluyen las tentativas. Son registros de las fuerzas de seguridad: no captan todos los delitos ni miden la sensación de inseguridad. Los cambios también pueden reflejar diferencias en la denuncia. Antes de definir medidas, conviene contrastar los hechos con zonas, horarios y canales de denuncia.</p><p class="chart-caption">Se conservan las tasas oficiales del SNIC, con su población de referencia. En municipios pequeños, pocos hechos pueden cambiar mucho la tasa: por eso mostramos también las cantidades.</p><p class="data-sources">Datos: <a href="https://anuario2024.estadistica.ec.gba.gov.ar/soc2025/" target="_blank" rel="noopener">INDEC / DPE, Censo 2022</a> · <a href="https://www.argentina.gob.ar/seguridad/estadisticascriminales/bases-de-datos" target="_blank" rel="noopener">Ministerio de Seguridad Nacional, SNIC</a> · <a href="metodologia.html#poblacion-seguridad">Cómo se construyen</a></p>`;
}
function openTransparency(){navigate('panorama',false);$('transparency-panel').scrollIntoView({behavior:motion()?'smooth':'instant',block:'start'});}
function renderTransparency(){
  const m=current(),t=m.transparency,editions=data.transparency.editions,latest=editions.at(-1),f=latestFiscal(m)||m.fiscalExecution;
  const change=t.change===0?'El puntaje se mantuvo entre las dos ediciones.':`El puntaje ${t.change>0?'subió':'bajó'} ${num(Math.abs(t.change))} puntos entre noviembre de 2025 y mayo de 2026.`;
  const sourceNotes=t.history.filter(h=>h.note).map(h=>`<p class="chart-caption">${escape(h.note)}</p>`).join('');
  const accounts=f?`Las ${latestFiscal(m)?'cuentas fiscales':'ejecuciones presupuestarias'} que incorporamos para ${m.municipio} llegan al ${fiscalDate(f.fin)}. El período de estas cuentas se informa por separado de la fecha del relevamiento de ASAP.`:`Todavía no incorporamos una ejecución fiscal individual de ${m.municipio}. Eso no significa que el municipio no la publique.`;
  $('transparency-panel').innerHTML=`<div class="section-heading"><div><div class="eyebrow">Información pública · ASAP</div><h2>Transparencia fiscal</h2><p>${escape(latest.fieldworkLabel)}.</p></div><button class="button button-quiet" id="transparency-ranking">Comparar los 135 municipios →</button></div><div class="transparency-overview"><div class="transparency-history"><h3>Qué cambió en la publicación</h3>${t.history.map((h,i)=>`<div class="transparency-period"><div><span>${escape(editions[i].label)}</span><strong>${num(h.score)} / 100</strong></div><div class="transparency-track" aria-hidden="true"><span style="width:${h.score}%"></span></div></div>`).join('')}<p>${change}</p></div><div class="transparency-reading"><h3>${t.score===100?'Publicó toda la información evaluada.':t.score<=5?'ASAP encontró muy poca información utilizable.':'La publicación de información era parcial.'}</h3><p>El puntaje resume qué información fiscal se podía consultar y cuán actualizada estaba. Un municipio puede publicar sus cuentas y tener déficit: son dos datos distintos.</p><p>La comparación exige documentos actualizados en cada edición. Una baja del puntaje puede aparecer cuando los informes anteriores quedan fuera del período admitido.</p></div></div><div class="transparency-components">${TRANSPARENCY_COMPONENTS.map(c=>{const v=t.components[c.id];return `<article class="transparency-component"><h3>${c.label}</h3><strong>${num(v)} / ${c.max} puntos</strong><div class="transparency-track" aria-hidden="true"><span style="width:${v/c.max*100}%"></span></div><p>${transparencyStatus(c,v)}</p></article>`;}).join('')}</div><div class="transparency-current"><div><h3>Qué tenemos hoy en el tablero</h3><p>${escape(accounts)}</p>${sourceNotes}</div><button class="text-button" id="transparency-accounts">Ver las cuentas municipales →</button></div><p class="chart-caption">Los puntos de cada rubro suman el total; cada rubro tiene un peso distinto. La evaluación corresponde a mayo de 2026. <a href="metodologia.html#transparencia">Cómo se interpreta el índice ↗</a></p>`;
  $('transparency-ranking').onclick=()=>{scopePeers=false;state.metric='transparencia';rankAscending=false;showAll=false;navigate('rankings');};
  $('transparency-accounts').onclick=()=>{navigate('recursos',false);$('fiscal-panel').scrollIntoView({behavior:motion()?'smooth':'instant',block:'start'});};
}
function mapScale(meta){
  const vals=rows.map(m=>metricValue(m,meta)).filter(finite);
  if(meta.id==='transparencia')return {scale:d3.scaleLinear().domain([0,100]).range(['#eef1f8','#3455a0']).clamp(true),low:'0 puntos',high:'100 puntos'};
  if(['recursos','empleo'].includes(meta.id)){const edge=Math.max(...vals.map(Math.abs));return {scale:d3.scaleLinear().domain([-edge,0,edge]).range(['#d5886e','#edf1e6','#288676']).clamp(true),low:'Mayor caída',high:'Mayor suba'};}
  return {scale:d3.scaleLinear().domain([Math.min(...vals),Math.max(...vals)]).range(meta.id==='carencias'?['#eff1e7','#b36d51']:['#eef2e9','#2a766b']).clamp(true),low:meta.id==='carencias'?'Menos carencias':'Menor peso',high:meta.id==='carencias'?'Más carencias':'Mayor peso'};
}
function drawMap(){
  if(state.view!=='panorama')return;
  const meta=METRICS.find(m=>m.id===mapMetric),colors=mapScale(meta),svg=d3.select('#map'),w=$('map').clientWidth,h=$('map').clientHeight;
  if(!w||!h)return;
  const changed=w!==mapWidth;mapWidth=w;
  svg.attr('viewBox',`0 0 ${w} ${h}`);
  mapProjection=d3.geoMercator().fitExtent([[24,12],[w-42,h-30]],geography);mapPath=d3.geoPath(mapProjection);
  let group=svg.select('g.map-shapes');if(group.empty())group=svg.append('g').attr('class','map-shapes');
  const features=geography.features;
  const paths=group.selectAll('path.municipality-path').data(features,d=>d.properties.id).join('path').attr('class',d=>'municipality-path'+(d.properties.id===state.id?' selected':'')).attr('d',mapPath).attr('data-municipality',d=>d.properties.id).attr('fill',d=>{const v=metricValue(byId.get(d.properties.id),meta);return finite(v)?colors.scale(v):'#dce2db';}).attr('role','button').attr('tabindex',d=>d.properties.id===state.id?0:-1).attr('aria-pressed',d=>String(d.properties.id===state.id)).attr('aria-label',d=>`${byId.get(d.properties.id).municipio}: ${formatMetric(metricValue(byId.get(d.properties.id),meta),meta)}. ${meta.period}`);
  function tip(event,d){const m=byId.get(d.properties.id),value=metricValue(m,meta);$('map-tooltip').innerHTML=`<strong>${escape(m.municipio)}</strong><span class="${negativeClass(value)}">${formatMetric(value,meta)}</span>`;$('map-tooltip').hidden=false;}
  paths.on('pointerenter',tip).on('pointerleave',()=>$('map-tooltip').hidden=true).on('focus',tip).on('blur',()=>$('map-tooltip').hidden=true).on('click',(event,d)=>{event.stopPropagation();$('map-tooltip').hidden=true;selectMunicipality(d.properties.id);}).on('keydown',(event,d)=>{
    if(event.key==='Enter'||event.key===' '){event.preventDefault();selectMunicipality(d.properties.id);}
    if(['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'].includes(event.key)){event.preventDefault();const sorted=rows.slice().sort((a,b)=>a.municipio.localeCompare(b.municipio,'es'));const i=sorted.findIndex(m=>m.id===d.properties.id),next=sorted[(i+(['ArrowRight','ArrowDown'].includes(event.key)?1:sorted.length-1))%sorted.length];selectMunicipality(next.id);svg.select(`[data-municipality="${next.id}"]`).node().focus();}
  });
  const selected=features.find(f=>f.properties.id===state.id),centroid=selected.properties.centroide;
  group.selectAll('circle.selected-ring').data([selected]).join('circle').attr('class','selected-ring').attr('cx',mapProjection([centroid.lon,centroid.lat])[0]).attr('cy',mapProjection([centroid.lon,centroid.lat])[1]).attr('r',8);
  group.selectAll('.municipality-path.selected').raise();group.select('circle').raise();
  if(!mapZoom){mapZoom=d3.zoom().scaleExtent([1,12]).filter(event=>event.type==='wheel'?event.ctrlKey:event.type==='touchstart'?event.touches.length===2:!event.button).on('zoom',event=>{svg.select('g.map-shapes').attr('transform',event.transform);$('map-tooltip').hidden=true;});svg.call(mapZoom);}
  if(changed)svg.call(mapZoom.transform,d3.zoomIdentity);
  document.querySelectorAll('[data-map]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.map===mapMetric)));
  $('legend-low').textContent=colors.low;$('legend-high').textContent=colors.high;
  const gradient=document.querySelector('.legend-gradient');gradient.style.background=mapMetric==='transparencia'?'linear-gradient(90deg,#eef1f8,#3455a0)':['recursos','empleo'].includes(mapMetric)?'linear-gradient(90deg,#d5886e,#edf1e6,#288676)':mapMetric==='carencias'?'linear-gradient(90deg,#eff1e7,#b36d51)':'linear-gradient(90deg,#eef2e9,#2a766b)';
  $('map-selection').innerHTML=`<strong>${escape(current().municipio)}</strong><span class="${negativeClass(metricValue(current(),meta))}">${formatMetric(metricValue(current(),meta),meta)}</span>`;
  $('map-caption').textContent=meta.period+' · '+meta.note;
}
function zoomSelected(){const f=geography.features.find(f=>f.properties.id===state.id),[[x0,y0],[x1,y1]]=mapPath.bounds(f),w=$('map').clientWidth,h=$('map').clientHeight;const k=Math.min(12,.65/Math.max((x1-x0)/w,(y1-y0)/h));d3.select('#map').transition().duration(motion()).call(mapZoom.transform,d3.zoomIdentity.translate(w/2,h/2).scale(k).translate(-(x0+x1)/2,-(y0+y1)/2));}
function rankingRows(){return rankMunicipalities(peers(rows,current(),scopePeers),currentMetric(),rankAscending);}
function rankingRowContext(m,meta){
  if(meta.budget){const date=m.annualBudget?.asOf?.split('-').reverse().join('/');return (meta.budgetBasis==='original'?'Original · documento ':'Vigente al ')+date;}
  if(meta.id==='robos')return num(m.community.crime['2025'].robberies)+' robos registrados en 2025';
  if(meta.id==='deudas-atrasadas')return num(m.community.debt.peopleInArrears)+' en mora de '+num(m.community.debt.peopleWithDebt)+' personas con deuda';
  return '';
}
function renderRanking(){
  const meta=currentMetric(),groups=[...new Set(METRICS.map(m=>m.group))];
  $('ranking-groups').innerHTML=groups.map(g=>`<button data-group="${g}" aria-pressed="${g===meta.group}">${g}</button>`).join('');
  $('ranking-groups').querySelectorAll('button').forEach(b=>b.onclick=()=>chooseMetric(METRICS.find(m=>m.group===b.dataset.group).id));
  $('ranking-metrics').innerHTML=METRICS.filter(m=>m.group===meta.group).map(m=>`<button data-metric="${m.id}" aria-pressed="${m.id===meta.id}">${m.label}</button>`).join('');
  $('ranking-metrics').querySelectorAll('button').forEach(b=>b.onclick=()=>chooseMetric(b.dataset.metric));
  $('budget-ranking-controls').hidden=!meta.budget;
  if(meta.budget){
    $('budget-ranking-choices').innerHTML=Object.entries(BUDGET_BASES).map(([id,b])=>`<button data-budget-basis="${id}" aria-pressed="${id===state.budgetBasis}">${b.label}</button>`).join('');
    $('budget-ranking-choices').querySelectorAll('button').forEach(b=>b.onclick=()=>{state.budgetBasis=b.dataset.budgetBasis;showAll=false;persist();renderRanking();});
    $('budget-ranking-note').textContent=BUDGET_BASES[state.budgetBasis].note;
  }
  const ranked=rankingRows(),m=current(),selected=ranked.find(r=>r.m.id===m.id);
  $('ranking-title').textContent=meta.label;$('ranking-period').textContent=meta.period+(meta.unit==='millions'?' · M = millones de pesos':'');
  $('ranking-coverage').textContent=`${ranked.length} ${ranked.length===1?'municipio':'municipios'} con datos${meta.group==='Cuentas'||meta.budget?' · Muestra parcial, no ranking de los 135':''}${scopePeers?` · Entre ${num(m.poblacion_2022/2)} y ${num(m.poblacion_2022*2)} habitantes (Censo 2022)`:''}`;
  $('ranking-direction').textContent=rankAscending?'Menor a mayor ↑':'Mayor a menor ↓';
  $('scope-peers').setAttribute('aria-label',`Comparar municipios con población similar a ${m.municipio}`);
  $('scope-all').setAttribute('aria-pressed',String(!scopePeers));$('scope-peers').setAttribute('aria-pressed',String(scopePeers));
  const transparency=meta.group==='Transparencia';
  $('ranking-summary').hidden=!(transparency||meta.budget);
  if(meta.budget)$('ranking-summary').textContent=meta.perCapita?'El presupuesto por habitante ayuda a comparar municipios de distinto tamaño. Es una autorización anual dividida por la población del Censo 2022; no es dinero que recibe cada vecino. Los servicios y organismos incluidos pueden diferir.':'El presupuesto total muestra cuánto tiene autorizado gastar cada municipio en el año. No es lo que ya gastó ni la plata disponible en caja. Para comparar distritos de distinto tamaño, mirá también el presupuesto por habitante.';
  if(transparency)$('ranking-summary').textContent=meta.id==='transparencia'?`${ranked.filter(r=>r.value===100).length} de ${ranked.length} municipios de esta comparación alcanzaron los 100 puntos. El índice evalúa publicación de información fiscal.`:`En esta comparación, ${ranked.filter(r=>r.value>0).length} municipios subieron, ${ranked.filter(r=>r.value<0).length} bajaron y ${ranked.filter(r=>r.value===0).length} mantuvieron su puntaje. Son cambios en publicación, no en resultado fiscal.`;
  $('ranking-selected').innerHTML=`<div class="rank-reference-info"><span class="rank-reference-label">Municipio de referencia</span><strong>${escape(m.municipio)}</strong><span>${selected?`Posición ${selected.rank} de ${ranked.length} en esta comparación`:meta.budget?'Sin presupuesto verificado para el tipo y corte elegidos':'Sin dato para este indicador'}</span>${selected&&meta.budget?`<span>${escape(rankingRowContext(m,meta))}</span>`:''}</div><div class="rank-reference-detail"><strong class="${negativeClass(metricValue(m,meta))}">${formatMetric(metricValue(m,meta),meta)}</strong><button class="text-button" id="open-reference">${transparency?'Ver detalle de transparencia':meta.budget?'Ver presupuesto y documento':'Ver ficha municipal'} →</button></div>`;
  $('open-reference').onclick=()=>{if(transparency)openTransparency();else if(meta.budget){navigate('recursos',false);$('annual-budget-resources').scrollIntoView({behavior:motion()?'smooth':'instant',block:'start'});}else navigate('panorama');};
  const vals=ranked.map(r=>r.value),lo=Math.min(0,...vals),hi=Math.max(0,...vals),span=hi-lo||1,zero=(0-lo)/span*100;
  $('ranking-rows').innerHTML=(showAll?ranked:ranked.slice(0,10)).map(r=>{const pos=(r.value-lo)/span*100,left=Math.min(pos,zero),width=Math.max(Math.abs(pos-zero),.4),context=rankingRowContext(r.m,meta);return `<button class="rank-row ${r.m.id===m.id?'is-selected':''}" data-municipality="${r.m.id}" aria-label="${escape(r.m.municipio)}, puesto ${r.rank}, ${formatMetric(r.value,meta)}. ${escape(context)}. Seleccionar municipio"><span class="rank-number">${r.rank.toString().padStart(2,'0')}</span><span class="rank-name">${escape(r.m.municipio)}${context?`<small class="rank-row-context">${escape(context)}</small>`:''}</span><span class="rank-track" aria-hidden="true"><span class="rank-zero" style="left:${zero}%"></span><span class="rank-fill ${r.value<0?'down':'single'}" style="left:${left}%;width:${width}%"></span></span><span class="rank-value ${negativeClass(r.value)}">${formatMetric(r.value,meta)}</span></button>`;}).join('');
  bindMunicipalButtons($('ranking-rows'));
  $('ranking-more').hidden=ranked.length<=10;$('ranking-more').textContent=showAll?'Mostrar los primeros 10':`Ver los ${ranked.length} municipios`;
  $('ranking-note').textContent=meta.note+' Los empates comparten puesto. La posición corresponde al orden y al grupo elegidos; no es una calificación general de gestión.';
}
function chooseMetric(id){state.metric=id;rankAscending=currentMetric().ascending;showAll=false;persist();renderRanking();}
function renderResources(){
  const m=current();
  renderAnnualBudget(m,'annual-budget-resources',true);
  renderPrices();
  $('resource-stats').innerHTML=card('Transferencias provinciales',millions(m.transferencias_2026_ene_jul_ars_jul26),'Ene–jul 2026 · millones de pesos de julio')+card('Variación real',pct(m.variacion_transferencias_real_pct),'Ene–jul 2026 vs. igual período de 2025',tone(m.variacion_transferencias_real_pct))+card('Por habitante',money(m.transferencias_por_habitante_base2022_ars_jul26),'Ene–jul 2026 · pesos de julio · población 2022');
  drawTransferChart();
  const parts=[['Cambio del total repartido','Con la participación de 2025',m.efecto_masa_observada_ars_jul26],['Cambio de participación','Sobre el total repartido en 2026',m.efecto_participacion_observada_ars_jul26],['Diferencia total de coparticipación','Ene–jul 2026 menos ene–jul 2025',m.copart_2026_ene_jul_ars_jul26-m.copart_2025_ene_jul_ars_jul26]];
  $('decomposition').innerHTML=parts.map(([l,c,v],i)=>`<div class="decomp-row ${i===2?'total':''}"><span>${l}<small>${c}</small></span><strong class="${tone(v)}">${signedMillions(v)}</strong></div>`).join('');
  $('revenue-stats').innerHTML=[['Recaudación propia PBA',data.provincialRevenue.total_provincial],['Ingresos Brutos PBA',data.provincialRevenue.ingresos_brutos],['Coparticipación a municipios',data.summary.copart_real_change_pct]].map(([l,v])=>`<div><span class="stat-label">${l}</span><strong class="stat-value ${tone(v)}">${pct(v)}</strong><span class="stat-context">Real · ene–jul 2026 vs. 2025</span></div>`).join('');
  renderFiscal(m);
  renderManagement(m);
}
function renderPrices(){
  const real=priceMode==='real',unit=real?'pesos de '+priceMonth(priceBase):'pesos corrientes de cada período';
  $('price-current-unit').textContent='Este comparador muestra '+unit+'. Los demás cuadros conservan la unidad indicada en cada uno.';
  document.querySelectorAll('[data-price-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.priceMode===priceMode)));
  document.querySelectorAll('[data-price-base]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.priceBase===priceBase));b.disabled=!real;});
  $('price-cards').innerHTML=priceComparisons(current(),priceMode,priceBase,deflator).map(r=>{
    const format=r.unit==='millions'?millions:money;
    return `<article class="price-card" data-price-row="${r.id}"><h3>${escape(r.label)}</h3><p class="small-note">${r.unit==='millions'?'Millones de '+unit:unit}</p><div class="price-values">${r.previousPeriod?`<div><span>${r.previousPeriod}</span><strong class="${negativeClass(r.previous)}" data-previous>${format(r.previous)}</strong></div>`:''}<div><span>${r.currentPeriod}</span><strong class="${negativeClass(r.current)}" data-current>${format(r.current)}</strong></div></div><p class="price-change"><strong class="${negativeClass(r.change)}" data-change>${finite(r.change)?pct(r.change):'Sin comparación'}</strong> ${finite(r.change)?(real?'de cambio, descontada la inflación':'de cambio en pesos, sin descontar inflación'):'· falta un período comparable con dato publicado'}</p><p class="chart-caption">${escape(r.method)}</p></article>`;
  }).join('');
  $('municipal-coverage-link').href=`cobertura.html#m-${state.id}`;
  renderPriceCalculator();
}
function renderPriceCalculator(){
  const input=$('price-amount'),from=$('price-from').value,to=$('price-to').value,amount=input.value.trim()===''?null:Number(input.value);
  const value=adjustPrice(amount,from,to,deflator.indices);
  if(!finite(value)){$('price-calculation').textContent='Ingresá un importe y meses dentro de la serie disponible: diciembre de 2016 a '+priceMonth(deflator.latest)+'.';return;}
  const factor=deflator.indices[to]/deflator.indices[from];
  $('price-calculation').innerHTML=`<strong class="${negativeClass(value)}">${money(amount)} de ${priceMonth(from)} equivalen a ${money(value)} de ${priceMonth(to)}.</strong><span>Se multiplica el importe por ${num(factor,4)}: IPC de ${priceMonth(to)} dividido por IPC de ${priceMonth(from)}. Es una equivalencia de poder de compra; no suma intereses.</span>`;
}
function priceExport(){
  const unit=priceMode==='real'?'ARS de '+priceBase:'ARS corrientes';
  return [['Municipio','Indicador','Valor anterior','Período anterior','Valor actual','Período actual','Unidad de importes','Variación %','Criterio'],...priceComparisons(current(),priceMode,priceBase,deflator).map(r=>[current().municipio,r.label,r.previous,r.previousPeriod,r.current,r.currentPeriod,unit,r.change,r.method])];
}
function fiscalDate(date){return new Intl.DateTimeFormat('es-AR',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(date+'T12:00:00Z'));}
function renderFiscal(m,chosen){
  const f=chosen||latestFiscal(m),e=m.fiscalExecution,count=data.fiscalCoverage.fiscal,periods=fiscalPeriods(m);
  if(f){
    const max=Math.max(f.ingresos_totales,f.gastos_totales,1),balance=f.resultado_financiero,spending=f.gastos_totales/f.ingresos_totales*100;
    const bars=[['Ingresos cobrados',f.ingresos_totales],['Gastos devengados',f.gastos_totales]].map(([label,value])=>`<div class="sim-bar-row"><div><span>${label}</span><strong>${millions(value)}</strong></div><div class="sim-track" aria-hidden="true"><div style="width:${value/max*100}%"></div></div></div>`).join('');
    const currentReading=f.ahorro_corriente>=0?`Los ingresos corrientes alcanzaron para cubrir el gasto corriente y dejaron un margen contable de ${millions(f.ahorro_corriente)} antes de la cuenta de capital.`:`El gasto corriente superó a los ingresos corrientes en ${millions(Math.abs(f.ahorro_corriente))}. El desequilibrio ya aparece antes de la cuenta de capital.`;
    const capitalReading=f.gastos_capital>f.ingresos_capital?`La inversión y las transferencias de capital superaron a los ingresos de capital en ${millions(f.gastos_capital-f.ingresos_capital)}.`:`Los ingresos de capital superaron al gasto de capital en ${millions(f.ingresos_capital-f.gastos_capital)}.`;
    $('fiscal-panel').innerHTML=`<span class="coverage-tag">${f===m.fiscal?'Cuenta comparable · enero–junio de 2026':'Cuenta de otro período'}</span><h3>Las cuentas de ${escape(m.municipio)}</h3>${periods.length>1?`<div class="fiscal-periods" aria-label="Período de las cuentas">${periods.map((p,i)=>`<button data-fiscal-period="${i}" aria-pressed="${p===f}">${p.inicio.slice(0,4)} · ${monthLabels[Number(p.inicio.slice(5,7))-1]}–${monthLabels[Number(p.fin.slice(5,7))-1]}</button>`).join('')}</div>`:''}${f!==m.fiscal?'<p class="period-notice">Este período se muestra en la ficha. El ranking fiscal compara enero–junio de 2026 y utiliza solamente las cuentas de ese semestre.</p>':''}<p>Del ${fiscalDate(f.inicio)} al ${fiscalDate(f.fin)}. Importes en millones de pesos corrientes, sin ajuste por inflación. Los ingresos son lo cobrado; los gastos devengados son obligaciones registradas, aunque todavía no se hayan pagado. Se excluyen fuentes y aplicaciones financieras.</p><div class="fiscal-bars">${bars}</div><div class="stats-grid">${card(balance<0?'Déficit financiero':balance>0?'Superávit financiero':'Resultado equilibrado',millions(Math.abs(balance)),num(Math.abs(f.resultado_sobre_ingresos_pct),2)+'% de los ingresos',tone(balance))}${card('Gasto de capital',millions(f.gastos_capital),num(f.capital_sobre_gasto_pct,1)+'% del gasto total')}${card('Gasto en personal',millions(f.personal_devengado),finite(f.personal_sobre_gasto_corriente_pct)?num(f.personal_sobre_gasto_corriente_pct,1)+'% del gasto corriente':'Sin desglose verificado para este período')}</div>${detailTable('fiscal-detail','Cómo se compone el resultado',['Concepto','Millones de pesos corrientes'],[
      ['Ingresos corrientes',detailValue(f.ingresos_corrientes,'millions',2)],['Ingresos de capital',detailValue(f.ingresos_capital,'millions',2)],['Gastos corrientes',detailValue(f.gastos_corrientes,'millions',2)],['Ahorro corriente: ingresos menos gastos corrientes',detailValue(f.ahorro_corriente,'millions',2)],['Saldo de capital: ingresos menos gastos de capital',detailValue(f.ingresos_capital-f.gastos_capital,'millions',2)]
    ])}<p>Corriente es el funcionamiento habitual, como salarios y servicios. Capital incluye obras y equipamiento. El ahorro corriente equivale al ${detailValue(f.ahorro_sobre_ingresos_corrientes_pct,'share',2)} de los ingresos corrientes. El gasto de capital fue de ${detailValue(f.capital_por_habitante_base2022_ars_corrientes,'money')} por habitante del Censo 2022; no equivale a obras terminadas.</p><div class="fiscal-reading"><h3>Qué significa para la gestión</h3><p>Por cada $100 que ingresaron, se registraron $${num(spending,1)} de gastos. ${currentReading} ${capitalReading}</p><p>${balance<0?'La diferencia exige mirar cómo se financia el gasto: uso de saldos anteriores, endeudamiento o pagos que quedan pendientes. Este cuadro por sí solo no identifica cuánto aportó cada mecanismo.':'El superávit muestra que los ingresos superaron a los gastos de este período. Para saber cuánto se puede destinar a nuevas decisiones, hay que revisar también pagos pendientes, deudas anteriores y fondos que ya tienen un destino asignado.'}</p></div><p class="chart-caption">${escape(f.scope||'Informe municipal publicado. Las funciones, servicios y organismos incluidos pueden diferir entre municipios.')} ${f.method==='economic_execution'?'Resultado calculado a partir de la ejecución oficial por carácter económico.':f.method==='sum_quarters'?'El semestre suma los informes de enero–marzo y abril–junio, sin superponer períodos.':''} El resultado financiero y el ahorro corriente no son caja libre.</p>`;
    $('fiscal-panel').querySelectorAll('[data-fiscal-period]').forEach(b=>b.onclick=()=>renderFiscal(m,periods[Number(b.dataset.fiscalPeriod)]));
  }else if(e){
    $('fiscal-panel').innerHTML=`<span class="coverage-tag">Ejecución presupuestaria disponible</span><h3>Las cuentas de ${escape(m.municipio)}</h3><p>Del ${fiscalDate(e.inicio)} al ${fiscalDate(e.fin)}. Millones de pesos corrientes. El presupuesto vigente es la autorización anual; la ejecución corresponde al período informado.</p><div class="stats-grid">${card('Presupuesto vigente',millions(e.presupuesto_vigente),'Autorización anual al cierre de junio')}${card('Recursos cobrados',millions(e.recursos_presupuestarios_percibidos),'Total presupuestario percibido')}${card('Gastos devengados',millions(e.gastos_presupuestarios_devengados),'Obligaciones registradas del período')}${card('Gastos pagados',millions(e.gastos_presupuestarios_pagados),'Pagos de la ejecución del período')}</div><div class="fiscal-reading"><h3>Qué significa para la gestión</h3><p>De los gastos registrados en el semestre, ${millions(e.devengado_no_pagado_del_periodo)} seguían sin pagarse al cierre. Esa diferencia ayuda a seguir los pagos pendientes del período; no representa toda la deuda municipal.</p><p>Estos totales incluyen operaciones que deben separarse para calcular el resultado fiscal. Restar directamente los recursos cobrados y los gastos devengados podría confundir gasto corriente o inversión con movimientos financieros. Por eso, ${escape(m.municipio)} conserva estos datos visibles y todavía no integra el ranking de déficit.</p></div>`;
  }else{
    $('fiscal-panel').innerHTML=`<span class="coverage-tag">Cuenta pendiente de verificación</span><h3>Qué falta para completar las cuentas</h3><p>${escape(m.fiscalSearch?.message||`Todavía no verificamos una cuenta completa de ${m.municipio}.`)} Con las transferencias solas no podemos calcular el déficit ni la inversión total.</p><p>El ranking compara ${count} municipios en enero–junio de 2026. Las fichas también conservan ${data.fiscalCoverage.otherPeriods} cuentas de otros períodos, siempre con sus fechas.</p><div class="fiscal-choices"><button id="fiscal-ranking">Ver el ranking de cuentas →</button><a class="text-button" href="metodologia.html#revision-portales">Ver el alcance de la revisión ↗</a></div>`;
    $('fiscal-ranking').onclick=()=>{scopePeers=false;state.metric='deficit';rankAscending=true;showAll=false;navigate('rankings');};
  }

}
function renderAnnualBudget(m,id,detailed){
  const host=$(id),b=m.annualBudget,coverage=data.annualBudgetCoverage;
  const catalog=`<a class="text-button" href="presupuestos.html#m-${m.id}">Ver los presupuestos de los 135 municipios →</a>`;
  if(!b){
    host.innerHTML=`<div class="eyebrow">Presupuesto anual</div><h2>Falta verificar el presupuesto de ${escape(m.municipio)}</h2><p>Todavía no incorporamos un documento oficial con el monto anual. Eso no significa que el municipio no tenga presupuesto. Las transferencias recibidas o los gastos de un semestre no permiten reconstruirlo.</p>${catalog}`;
    return;
  }
  const label=b.basis==='current'?'Presupuesto vigente':'Presupuesto original publicado';
  const dateLabel=b.basis==='current'?'Vigente al':'Documento del';
  const headline=b.historical?`Último presupuesto verificado · ${b.year}`:`Presupuesto anual ${b.year}`;
  const cards=`<div class="annual-budget-grid"><div><span class="stat-label">${label}</span><strong class="annual-budget-amount" data-budget-amount><span data-budget-raw="${b.amount}">$${num(b.amount/1e6,1)}</span> <span>millones</span></strong><span class="stat-context">Pesos corrientes, sin ajustar por inflación</span></div><div><span class="stat-label">Presupuesto por habitante</span><strong class="annual-budget-per-capita">${detailValue(b.perCapita,'money',0)}</strong><span class="stat-context">Presupuesto ${b.year} ÷ ${num(m.poblacion_2022)} habitantes del Censo 2022</span></div></div>`;
  const status=b.historical?`<p class="budget-status">Este dato es de ${b.year}. Todavía falta verificar el presupuesto de ${coverage.targetYear}.</p>`:'';
  let detail='';
  if(detailed){
    detail=detailTable('annual-authorization','El monto completo, en pesos corrientes',['Concepto','Pesos'],[
      ['Presupuesto original del año',finite(b.original)?detailValue(b.original,'money',2):'Todavía no incorporado'],
      ...(finite(b.modifications)?[['Modificaciones registradas',detailValue(b.modifications,'money',2)]]:[]),
      ['Presupuesto vigente al corte informado',finite(b.current)?detailValue(b.current,'money',2):'Todavía no incorporado']
    ])+`<p>El original es el monto de partida para el año. El vigente incorpora las modificaciones conocidas hasta el corte indicado. ${b.basis==='original'?'Aquí se muestra el original porque todavía no incorporamos una actualización del vigente.':''}</p><p>${escape(b.scope)} ${escape(b.note)}</p><p class="annual-budget-links">${b.documents.map((d,i)=>`<a href="${escape(d.url)}" target="_blank" rel="noopener">Documento oficial${b.documents.length>1?' '+(i+1):''}${d.consultedPages?.length===1?' · página '+d.consultedPages[0]:''} ↗</a>`).join(' · ')} · <a href="data/presupuestos_anuales.csv" download>Descargar los presupuestos (CSV) ↓</a></p>`;
  }
  host.innerHTML=`<div class="eyebrow">Cuánto tiene autorizado gastar</div><h2>${headline}</h2><p class="annual-budget-date">${dateLabel} ${fiscalDate(b.asOf)}. Verificado el ${fiscalDate(b.verifiedAt)}.</p>${status}${cards}<p>Es la autorización para gastar durante todo el año. No indica cuánto se gastó ni cuánto dinero queda disponible. El monto por habitante sirve para dimensionarlo; no es una suma que recibe cada vecino.</p>${detail}<div class="annual-budget-links">${detailed?catalog:'<button class="text-button" data-open-budget>Ver el detalle del presupuesto →</button>'}</div>`;
  const open=host.querySelector('[data-open-budget]');
  if(open)open.onclick=()=>{navigate('recursos');requestAnimationFrame(()=>$('annual-budget-resources').scrollIntoView({block:'start',behavior:'smooth'}));};
}

function renderManagement(m){
  const g=m.management,host=$('management-panel'),nav=$('management-shortcuts');
  host.innerHTML='';nav.innerHTML='';nav.hidden=!g;if(!g)return;
  nav.innerHTML=[['fiscal-panel','Las cuentas'],['municipal-budget','Presupuesto y pagos'],['municipal-treasury','Caja y deuda'],['municipal-banking','Crédito y depósitos'],['municipal-history','Historia fiscal']].map(([id,label])=>`<a class="button button-quiet" href="#${id}">${label}</a>`).join('');
  const b=g.budget,t=g.treasury,d=g.debt,bank=g.banking,v=n=>detailValue(n,'millions',2);
  const budgetRows=[['Presupuesto original del año',b.original],['Modificaciones del presupuesto',b.modifications],['Presupuesto vigente del año',b.current],['Recursos cobrados en el período',b.received],['Gastos presupuestarios devengados',b.accrued],['Gastos presupuestarios pagados',b.paid],['Devengado del período sin pagar',b.unpaid]].filter(r=>finite(r[1]));
  const bridge=b.reconciliation;
  host.innerHTML=`<section class="panel section-block" id="municipal-budget"><div class="eyebrow">Autorización y ejecución</div><h2>Presupuesto y pagos</h2><p>Del ${fiscalDate(b.inicio)} al ${fiscalDate(b.fin)}. Millones de pesos corrientes. El presupuesto es la autorización anual para gastar. Devengado es un gasto registrado; pagado es lo efectivamente cancelado.</p>${detailTable('budget-totals','Cuánto se autorizó y cuánto se ejecutó',['Concepto','Millones de pesos'],budgetRows.map(([l,n])=>[l,v(n)]))}<p>${escape(b.reading)}</p>${detailTable('budget-objects','En qué se registran los gastos',['Concepto','Presupuesto vigente','Devengado','Pagado'],b.objects.map(r=>[r.label,v(r.current),v(r.accrued),v(r.paid)]))}<p class="chart-caption">Clasificación por objeto del gasto. Los bienes de uso no son todo el gasto de capital: también puede haber insumos de obras y transferencias de capital. La ejecución no mide el avance físico de las obras ni exige gastar la mitad del presupuesto a mitad de año.</p>${detailTable('budget-receipts',b.receiptTitle,['Concepto','Millones de pesos','Parte del total'],b.receipts.map(r=>[r.label,v(r.received),detailValue(100*r.received/b.received,'share',1)]))}<p class="chart-caption">${b.receiptTitle.startsWith('Origen')?'Origen municipal incluye tasas, derechos y otros recursos propios, incluso ventas de activos. No equivale solamente a impuestos ni permite suponer que todos esos ingresos se repiten.':'Un ingreso sin afectación específica puede usarse para distintas finalidades, pero primero debe atender las obligaciones del municipio. No es lo mismo que caja libre.'}</p>${bridge?detailTable('budget-reconciliation','Cómo se llega al gasto fiscal',['Concepto','Millones de pesos'],[['Gasto presupuestario',v(bridge.budgetAccrued)],['Menos devolución de capital de préstamos',v(-bridge.amortization)],['Menos cancelación de pasivos anteriores',v(-bridge.priorLiabilities)],['Gasto fiscal del período',v(bridge.fiscalExpenditure)],['Intereses, ya incluidos en el gasto fiscal',v(bridge.interestIncluded)]]):''}</section>
  <section class="panel section-block" id="municipal-treasury"><div class="eyebrow">Saldos y obligaciones</div><h2>Qué muestra la caja y qué deuda queda</h2><p>Cierre al ${fiscalDate(t.date)}. Millones de pesos corrientes. Cada saldo corresponde a esa fecha; no se combina con gastos o deudas de otro cierre.</p>${detailTable('treasury-detail','Tesorería y pasivos contables',['Concepto','Millones de pesos'],Object.entries({closing:'Saldo total de tesorería',available:'Disponibilidades, incluidas en el total',transitory:'Movimientos transitorios, incluidos en el total',budgetCash:'Cuentas presupuestarias, incluidas en el total',unearmarkedAccounts:'De ellas: cuentas sin afectación',earmarkedAccounts:'De ellas: cuentas con destino asignado',thirdPartyAndSpecial:'Terceros y cuentas especiales',liabilities:'Pasivos contables totales',currentLiabilities:'De ellos: pasivos corrientes',nonCurrentLiabilities:'De ellos: pasivos no corrientes'}).filter(([k])=>finite(t[k])).map(([k,l])=>[l,v(t[k])]))}<p>${escape(t.reading)}</p><p>Los pasivos son obligaciones registradas. Corrientes son las de corto plazo; no corrientes, las de mayor plazo. Esta clasificación no permite conocer qué factura ya venció. Los subtotales están incluidos en los totales: no se suman otra vez.</p>${d?`<h3>Deuda municipal al ${fiscalDate(d.date)}</h3>${detailTable('municipal-debt','Préstamos y gastos pendientes de pago',['Concepto','Millones de pesos'],[['Deuda consolidada',v(d.consolidated)],['De ella: corriente',v(d.current)],['De ella: no corriente',v(d.nonCurrent)],['Deuda flotante',v(d.floating)]])}<p>${escape(d.reading)}</p>${detailTable('floating-history','Deuda flotante al cierre de cada año',['Año','Millones de pesos corrientes'],d.floatingHistory.map(r=>[String(r.year),v(r.floating)]))}<p class="chart-caption">Estos montos no están ajustados por inflación. Una suba nominal no mide por sí sola cuánto aumentó la carga real de la deuda. Son obligaciones del municipio, distintas de las deudas de las personas que muestra la sección Empleo.</p>`:''}</section>
  <section class="panel section-block" id="municipal-banking"><div class="eyebrow">Actualización del BCRA</div><h2>Crédito y depósitos hasta junio de 2026</h2><p>${escape(bank.note)}</p>${bank.records.some(r=>r.status==='verified')?detailTable('banking-latest','Saldos al cierre: millones de pesos',['Fecha','Préstamos corrientes','Depósitos corrientes','Préstamos a precios de julio 2026','Depósitos a precios de julio 2026'],bank.records.map(r=>[fiscalDate(r.date),v(r.loans),v(r.deposits),v(r.loansReal),v(r.depositsReal)])):'<p>La revisión de los archivos 2023–2026 mantiene los importes de Las Heras sin dato verificable. Los ceros de esas planillas no se interpretan como ausencia de préstamos o depósitos. Tampoco se usan los datos de calles o localidades homónimas.</p>'}<p class="chart-caption">La conversión a pesos de julio de 2026 utiliza el IPC nacional de cada cierre. Los montos incluyen préstamos y depósitos en moneda extranjera ya convertidos por el BCRA: el tipo de cambio también puede afectar su evolución. No se infiere que los depósitos de las sucursales sean dinero disponible para el municipio.</p></section>
  <section class="panel section-block" id="municipal-history"><div class="eyebrow">Mirar más de un cierre</div><h2>Historia fiscal</h2><p>${escape(g.historyReading)}</p>${[6,12].map(month=>{const history=g.history.filter(f=>Number(f.fin.slice(5,7))===month && Number(f.inicio.slice(5,7))===1);return detailTable('fiscal-history-'+month,month===6?'Primer semestre de cada año':'Cierres de enero a diciembre',['Período exacto','Ingresos','Gastos','Resultado','Resultado / ingresos'],history.map(f=>[`${fiscalDate(f.inicio)} a ${fiscalDate(f.fin)}`,v(f.ingresos_totales),v(f.gastos_totales),v(f.resultado_financiero),detailValue(f.resultado_sobre_ingresos_pct,'share',2)]));}).join('')}<p>Millones de pesos corrientes. Los botones de “Las cuentas” permiten ver el detalle de cada período, incluidos los cortes parciales. No se suman un cierre anual y su primer semestre. El resultado y su proporción sobre ingresos no miden calidad de servicios ni caja libre.</p></section>
  <section class="panel section-block" id="municipal-pending"><h2>Lo que todavía falta para decidir con más precisión</h2><ul>${g.pending.map(x=>`<li>${escape(x)}</li>`).join('')}</ul><p class="chart-caption">Revisión del ${fiscalDate(g.verifiedAt)}. <a href="auditoria-distritos.html#${m.id}">Ver documentos y conciliaciones de este municipio</a>.</p></section>`;
}
function chartBase(id){const host=$(id);host.innerHTML='';const width=host.clientWidth,height=host.clientHeight;const margin={top:24,right:10,bottom:29,left:57};const svg=d3.select(host).append('svg').attr('viewBox',`0 0 ${width} ${height}`).attr('role','img');const tip=document.createElement('div');tip.className='chart-tip';tip.hidden=true;host.append(tip);return {host,width,height,margin,svg,tip};}
function drawTransferChart(){
  if(state.view!=='recursos')return;const c=chartBase('transfers-chart'),m=current(),{width:w,height:h,margin:a,svg,tip}=c;
  const values=Array.from({length:7},(_,i)=>({month:monthLabels[i],previous:m.transfers.find(r=>r[0]===`2025-${String(i+1).padStart(2,'0')}`)?.[1]/1e6,current:m.transfers.find(r=>r[0]===`2026-${String(i+1).padStart(2,'0')}`)?.[1]/1e6}));
  svg.attr('aria-label','Transferencias provinciales de enero a julio de 2025 y 2026 en millones de pesos de julio de 2026.');
  const x=d3.scaleBand().domain(values.map(d=>d.month)).range([a.left,w-a.right]).padding(.27),y=d3.scaleLinear().domain([0,d3.max(values,d=>Math.max(d.previous,d.current))*1.08]).nice().range([h-a.bottom,a.top]);
  svg.append('g').attr('class','grid').attr('transform',`translate(${a.left},0)`).call(d3.axisLeft(y).ticks(4).tickSize(-(w-a.left-a.right)).tickFormat(v=>num(v)));
  svg.append('g').attr('class','axis').attr('transform',`translate(0,${h-a.bottom})`).call(d3.axisBottom(x).tickSize(0).tickPadding(12));
  for(const key of ['previous','current'])svg.selectAll('.bar-'+key).data(values).join('rect').attr('x',d=>x(d.month)+(key==='current'?x.bandwidth()/2:0)).attr('y',d=>y(d[key])).attr('height',d=>y(0)-y(d[key])).attr('width',Math.max(1,x.bandwidth()/2-2)).attr('rx',2).attr('fill',key==='current'?'#14695c':'#cdd8cf');
  svg.selectAll('.month-hit').data(values).join('rect').attr('class','month-hit').attr('x',d=>x(d.month)-x.step()*.1).attr('y',a.top).attr('width',x.step()).attr('height',h-a.top-a.bottom).attr('fill','transparent').attr('tabindex',0).attr('role','img').attr('aria-label',d=>`${d.month}: 2025, ${num(d.previous,1)} millones; 2026, ${num(d.current,1)} millones.`).on('pointerenter',(_,d)=>show(d)).on('focus',(_,d)=>show(d)).on('click',(_,d)=>show(d)).on('pointerleave',()=>tip.hidden=true).on('blur',()=>tip.hidden=true);
  function show(d){tip.textContent=`${d.month.toUpperCase()} · 2025: $${num(d.previous,1)} M · 2026: $${num(d.current,1)} M`;tip.hidden=false;}
}
function renderEmployment(){
  const m=current();$('employment-stats').innerHTML=card('Puestos privados registrados',num(m.empleo_dic2025),'Diciembre de 2025')+card('Cambio del empleo promedio',pct(m.empleo_promedio_cambio_2024_2025_pct),'Promedio 2025 vs. promedio 2024',tone(m.empleo_promedio_cambio_2024_2025_pct))+card('Cambio del salario bruto, ajustado por inflación',pct(m.salario_real_promedio_cambio_2023_2025_pct),'Promedio mensual 2025 vs. 2023',tone(m.salario_real_promedio_cambio_2023_2025_pct));
  $('employment-detail').innerHTML=detailTable('employment-years','Promedio del año y puestos al cierre',['Año','Promedio mensual de puestos','Puestos en diciembre'],[2023,2024,2025].map(y=>[String(y),detailValue(m[`empleo_promedio_${y}`],'number',1),detailValue(m[`empleo_dic${y}`])]))+'<p class="chart-caption">El promedio resume los doce meses. Diciembre muestra el cierre: pueden cambiar en distinta dirección si hubo contrataciones o bajas durante el año. OEDE / SIPA, puestos privados registrados por establecimiento.</p>';
  renderDebt(m);
  const wage=m.community.wage;
  $('salary-panel').innerHTML=`<div class="eyebrow">Entender el dato</div><h2>El salario publicado es bruto y promedio</h2>${detailTable('salary-years','Salario bruto mensual promedio de cada año',['Año','Pesos de cada mes, sin ajuste','Pesos de julio de 2026'],[2023,2024,2025].map(y=>[String(y),detailValue(wage.annual[String(y)].nominal,'money'),detailValue(wage.annual[String(y)].real,'money')]))}<p>El OEDE calcula la remuneración bruta promedio que las empresas privadas declaran al SIPA, a través de ARCA. Incluye aguinaldo, conceptos no remunerativos y pagos por vacaciones. <strong>No es el sueldo de bolsillo</strong>: todavía no se descontaron aportes ni otras deducciones.</p>${detailTable('salary-months','Por qué diciembre puede parecer más alto',['Mes de 2025','Bruto del mes, sin ajuste','Bruto a precios de julio de 2026'],[['2025-11','Noviembre'],['2025-12','Diciembre']].map(([period,label])=>[label,detailValue(wage.months[period].nominal,'money'),detailValue(wage.months[period].real,'money')]))}<p>Por ejemplo, en noviembre de 2025 el promedio bruto fue de ${money(wage.months['2025-11'].nominal)}, frente a ${money(wage.months['2025-12'].nominal)} en diciembre. El aguinaldo y otros pagos pueden elevar el cierre del año. Noviembre tampoco representa necesariamente el sueldo habitual de cada trabajador.</p><p>El promedio corresponde a puestos en establecimientos del municipio, cuyos trabajadores pueden vivir en otro lugar. Los salarios altos y el peso de cada sector pueden moverlo: no describe al vecino típico ni es la mediana, que dejaría a la mitad de los salarios por debajo y a la mitad por encima. Tampoco corresponde convertirlo a sueldo de bolsillo con un descuento único: depende de cada trabajador.</p><p class="chart-caption">Real significa ajustado por inflación. Para calcularlo multiplicamos cada salario mensual por IPC de julio de 2026 / IPC del mes y después promediamos los doce meses. El IPC es el índice de precios al consumidor del INDEC. Se verificaron los 84 meses por municipio contra las planillas originales.</p><p class="data-sources">Datos: <a href="https://www.argentina.gob.ar/sites/default/files/departamento_serie_empleo_remuneraciones_3.xlsx" target="_blank" rel="noopener">OEDE / SIPA, empleo y remuneraciones</a> · <a href="https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_08_26.xls" target="_blank" rel="noopener">INDEC, IPC nacional</a></p><h3>Producto bruto municipal: qué produce el territorio</h3>${detailTable('product-years','El tamaño de la producción local',['Año','Millones de pesos constantes de 2004'],[2021,2022,2023].map(y=>[String(y),detailValue(m[`pbg_constante_2004_${y}_ars`],'millions',2)]))}<p>La Dirección Provincial de Estadística estima el valor de los bienes y servicios generados en el municipio, evitando contar dos veces los insumos. Es actividad económica, no recaudación ni presupuesto municipal. Entre 2021 y 2023 varió <span class="${negativeClass(m.pbg_real_cambio_2021_2023_pct)}">${pct(m.pbg_real_cambio_2021_2023_pct)}</span>, a precios constantes de 2004, es decir, sin el efecto de la inflación. El último año incorporado es 2023.</p><p class="data-sources"><a href="metodologia.html#actividad">Ver el origen del producto municipal</a></p><h3>Los bancos en el territorio</h3><div class="stats-grid">${card('Sucursales bancarias',num(m.sucursales_2024),'2024 · locales informados')}${card('Préstamos por cada $100 depositados',finite(m.prestamos_sobre_depositos_2024_pct)?'$'+num(m.prestamos_sobre_depositos_2024_pct,2):'Sin dato','Cierre de 2024 · relación entre saldos')}</div><p>Los préstamos y depósitos se asignan por localización financiera. Pueden incluir operaciones de empresas y personas de otros lugares: no indican que el ahorro de los vecinos se preste dentro o fuera del municipio. Los importes reservados no se reemplazan por cero.</p><button class="button button-quiet" id="open-bank-prices">Comparar préstamos y depósitos de 2023 y 2024 →</button><p class="data-sources"><a href="metodologia.html#actividad">Origen de las estadísticas bancarias</a>. Las deudas de las personas se muestran a continuación con otra base y otro período.</p>`;
  if(m.management?.banking){$('salary-panel').innerHTML+='<button class="button button-quiet" id="open-latest-banks">Ver actualización del BCRA a junio de 2026 →</button>';$('open-latest-banks').onclick=()=>{navigate('recursos',false);$('municipal-banking').scrollIntoView({behavior:motion()?'smooth':'instant',block:'start'});};}
  $('open-bank-prices').onclick=()=>{navigate('recursos',false);$('price-panel').scrollIntoView({behavior:motion()?'smooth':'instant',block:'start'});};
  $('history-short').setAttribute('aria-pressed',String(!fullHistory));$('history-full').setAttribute('aria-pressed',String(fullHistory));drawEmploymentChart();
  const sectors=m.sectors.slice().sort((a,b)=>(b.jobs??-1)-(a.jobs??-1)),max=Math.max(...sectors.map(s=>s.jobs??0),1);
  $('sectors').innerHTML=sectors.map(s=>`<div class="sector-row"><span class="sector-name">${escape(sectorName(s.name))}</span><span class="sector-value">${finite(s.jobs)?num(s.jobs):'Reservado / sin dato'}${finite(s.jobs)?`<small>${num(s.jobs/m.empleo_dic2025*100,1)}% del total</small>`:''}</span>${finite(s.jobs)?`<div class="sector-track" aria-hidden="true"><span style="width:${s.jobs/max*100}%"></span></div>`:''}</div>`).join('');
  const jobs=m.empleos_cambio_dic2023_dic2025,industry=m.peso_industria_empleo_formal_dic2025_pct;
  $('employment-reading').innerHTML=`<div class="eyebrow">Qué significa para la gestión</div><h3>${jobs<0?'La pérdida de trabajo también afecta a la economía local.':'El empleo formal amplía la base de la economía local.'}</h3><p>Entre diciembre de 2023 y diciembre de 2025, el municipio registró ${num(Math.abs(jobs))} puestos netos ${jobs<0?'menos':'más'}. ${finite(industry)?`La industria representa ${num(industry,1)}% del empleo formal localizado en el último corte. `:''}Para evaluar el impacto sobre consumo y tasas municipales, hay que mirar también salarios, facturación y cobranza.</p><p>Los trabajadores pueden vivir en otro municipio. Por eso, los puestos localizados y la población residente responden preguntas distintas.</p>`;
}
function renderDebt(m){
 const d=m.community.debt;
 $('debt-panel').innerHTML=`<div class="eyebrow">Relevamiento CEC/FES · base BCRA · julio de 2026</div><h2>Deudas de las personas</h2><p>El Mapa de la Deuda ubica ${num(d.peopleWithDebt)} personas con deuda en este municipio. De ellas, ${num(d.peopleInArrears)} figuran en mora. Tener una deuda no significa estar atrasado: se puede pagar un préstamo o una tarjeta al día.</p><div class="stats-grid">${card('Personas con atrasos',num(d.peopleInArrearsPct,1)+'%',`${num(d.peopleInArrears)} de ${num(d.peopleWithDebt)} personas con deuda`)}${card('Deuda en mora',num(d.debtInArrearsPct,1)+'%','Sobre el monto total adeudado')}${card('Deuda promedio por persona con deuda',money(d.averageDebtARS),'Pesos corrientes · julio de 2026')}</div><p>El primer porcentaje cuenta personas; el segundo, dinero. Ninguno se calcula sobre toda la población ni cuenta hogares. Una familia puede tener varias personas con deuda.</p><div class="stats-grid community-social">${card('Deuda total',millions(d.debtARS),'Millones de pesos corrientes')}${card('Deuda en mora',millions(d.debtInArrearsARS),'Millones de pesos corrientes')}</div><p>Mora significa aquí situaciones 3, 4 y 5 del relevamiento, asociadas a atrasos de unos tres meses o más. Los atrasos más cortos quedan fuera. El dato permite reconocer presión sobre las finanzas de las personas alcanzadas; conviene contrastarlo con empleo, ingresos y reclamos de defensa del consumidor.</p><p class="chart-caption">Procesamiento y asignación territorial del CEC/FES sobre la Central de Deudores del BCRA. Es un relevamiento externo, no una serie municipal publicada directamente por el Banco Central. Se toman todas las entidades, edades y géneros disponibles. La localización es la del proveedor: no se verificaron domicilios individuales. No cubre toda la deuda informal ni exclusivamente préstamos para consumo.</p><p class="data-sources"><a href="https://mapadeladeuda.ar/" target="_blank" rel="noopener">CEC/FES, Mapa de la Deuda</a> · <a href="metodologia.html#deuda-personas">Definiciones y alcance</a></p>`;
}
function drawEmploymentChart(){
  if(state.view!=='empleo')return;const c=chartBase('employment-chart'),{width:w,height:h,margin:a,svg,tip}=c;
  const values=current().employment.filter(r=>finite(r[1])&&(fullHistory||r[0]>='2024-01')).map(r=>({date:new Date(r[0]+'-15T12:00:00Z'),period:r[0],jobs:r[1]}));
  svg.attr('aria-label',`Serie mensual de empleo privado formal de ${current().municipio}, ${fullHistory?'2019':'2024'} a 2025.`);
  const x=d3.scaleUtc().domain(d3.extent(values,d=>d.date)).range([a.left,w-a.right]),extent=d3.extent(values,d=>d.jobs),pad=Math.max((extent[1]-extent[0])*.16,extent[1]*.025,1),y=d3.scaleLinear().domain([Math.max(0,extent[0]-pad),extent[1]+pad]).nice().range([h-a.bottom,a.top]);
  svg.append('g').attr('class','grid').attr('transform',`translate(${a.left},0)`).call(d3.axisLeft(y).ticks(4).tickSize(-(w-a.left-a.right)).tickFormat(v=>num(v)));
  const indexes=[0,Math.floor((values.length-1)/3),Math.floor((values.length-1)*2/3),values.length-1];
  const ticks=indexes.map(i=>values[i].date);svg.append('g').attr('class','axis').attr('transform',`translate(0,${h-a.bottom})`).call(d3.axisBottom(x).tickValues(ticks).tickFormat(d=>monthLabels[d.getUTCMonth()]+' '+String(d.getUTCFullYear()).slice(2)).tickSize(0).tickPadding(12));
  svg.append('path').datum(values).attr('fill','#eaf2e9').attr('d',d3.area().x(d=>x(d.date)).y0(h-a.bottom).y1(d=>y(d.jobs)));
  svg.append('path').datum(values).attr('fill','none').attr('stroke','#14695c').attr('stroke-width',2.4).attr('stroke-linejoin','round').attr('d',d3.line().x(d=>x(d.date)).y(d=>y(d.jobs)));
  const marker=svg.append('circle').attr('r',4).attr('fill','#14695c').attr('stroke','white').attr('stroke-width',2).style('display','none');
  const overlay=svg.append('rect').attr('x',a.left).attr('y',a.top).attr('width',w-a.left-a.right).attr('height',h-a.top-a.bottom).attr('fill','transparent').attr('tabindex',0).attr('role','img').attr('aria-label','Gráfico de empleo. Use flechas izquierda y derecha para recorrer los meses.');
  let selectedIndex=values.length-1;
  function show(i){selectedIndex=Math.min(values.length-1,Math.max(0,i));const d=values[selectedIndex];tip.textContent=`${monthLabels[d.date.getUTCMonth()]} ${d.date.getUTCFullYear()} · ${num(d.jobs)} puestos`;tip.hidden=false;marker.attr('cx',x(d.date)).attr('cy',y(d.jobs)).style('display',null);}
  overlay.on('pointermove',event=>{const [px]=d3.pointer(event);show(d3.bisector(d=>d.date).center(values,x.invert(px)));}).on('click',event=>{const [px]=d3.pointer(event);show(d3.bisector(d=>d.date).center(values,x.invert(px)));}).on('focus',()=>show(selectedIndex)).on('keydown',event=>{if(['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();show(selectedIndex+(event.key==='ArrowRight'?1:-1));}}).on('pointerleave',()=>{tip.hidden=true;marker.style('display','none');}).on('blur',()=>{tip.hidden=true;marker.style('display','none');});
}
function renderSimulation(){
  const m=current(),s=simulate(m,$('shock').value);$('shock-output').textContent=num(s.shock,s.shock%1?1:0);$('shock').setAttribute('aria-valuetext',`${num(s.shock,1)} por ciento de caída`);
  $('sim-live').textContent=`Pérdida simulada: ${millions(s.loss)}`;
  document.querySelectorAll('[data-shock]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.shock)===s.shock)));
  $('sim-name').textContent=m.municipio;$('simulation-stats').innerHTML=card('Recursos que perdería',millions(s.loss),'Millones de pesos de julio de 2026')+card('Pérdida por habitante',money(s.perCapita),'Pesos de julio · población 2022');
  $('simulation-bars').innerHTML=[['Coparticipación observada',s.baseline,100],['Con la caída simulada',s.after,100-s.shock]].map(([l,v,p])=>`<div class="sim-bar-row"><div><span>${l}</span><strong>${millions(v)}</strong></div><div class="sim-track" role="img" aria-label="${l}: ${millions(v)}"><div style="width:${p}%"></div></div></div>`).join('');
  $('simulation-headline').textContent=s.shock?`Una caída de ${num(s.shock,1)}% restaría ${millions(s.loss)} al municipio.`:'Sin caída de la masa, este escenario no resta recursos.';
  $('simulation-reading').textContent=`El cálculo aplica el cambio sobre la coparticipación bruta de enero–julio de 2026. Mantiene la participación del municipio y los demás fondos constantes. ${s.shock?'La pérdida tendría que absorberse con otros ingresos, menor gasto, uso de disponibilidades o financiamiento, según la situación fiscal.':'No supone una mejora de otros recursos ni cambios en el gasto.'}`;
}
function download(filename,text){const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8;'})),a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('La descarga está preparada.');}
function attachEvents(){
  document.querySelectorAll('[data-price-mode]').forEach(b=>b.onclick=()=>{priceMode=b.dataset.priceMode;persist();renderPrices();});
  document.querySelectorAll('[data-price-base]').forEach(b=>b.onclick=()=>{priceBase=b.dataset.priceBase;persist();renderPrices();});
  for(const id of ['price-amount','price-from','price-to'])$(id).addEventListener('input',renderPriceCalculator);
  $('download-prices').onclick=()=>download(`comparacion-pesos-${state.id}-${priceMode}-${priceBase}.csv`,csv(priceExport()));
  $('municipality').addEventListener('change',event=>selectMunicipality(event.target.value));
  document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>navigate(b.dataset.view));document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>navigate(b.dataset.go));
  document.querySelectorAll('[data-map]').forEach(b=>b.onclick=()=>{mapMetric=b.dataset.map;drawMap();});
  $('zoom-in').onclick=()=>d3.select('#map').transition().duration(motion()).call(mapZoom.scaleBy,1.6);$('zoom-out').onclick=()=>d3.select('#map').transition().duration(motion()).call(mapZoom.scaleBy,1/1.6);$('zoom-reset').onclick=()=>d3.select('#map').transition().duration(motion()).call(mapZoom.transform,d3.zoomIdentity);$('zoom-selected').onclick=zoomSelected;
  $('scope-all').onclick=()=>{scopePeers=false;showAll=false;renderRanking();};$('scope-peers').onclick=()=>{scopePeers=true;showAll=false;renderRanking();};$('ranking-direction').onclick=()=>{rankAscending=!rankAscending;renderRanking();};$('ranking-more').onclick=()=>{showAll=!showAll;renderRanking();};
  $('history-short').onclick=()=>{fullHistory=false;renderEmployment();};$('history-full').onclick=()=>{fullHistory=true;renderEmployment();};
  $('shock').addEventListener('input',renderSimulation);document.querySelectorAll('[data-shock]').forEach(b=>b.onclick=()=>{$('shock').value=b.dataset.shock;renderSimulation();});
  $('share').onclick=async()=>{try{await navigator.clipboard.writeText(location.href);toast('Enlace copiado con el municipio y la vista elegidos.');}catch{toast('Podés copiar el enlace desde la barra del navegador.');}};
  $('export-report').onclick=event=>{if($('export-report').getAttribute('aria-disabled')==='true'){event.preventDefault();toast(reportUnavailable?'El informe está en actualización. Volvé a cargar la página en unos minutos.':'Estamos preparando el enlace al informe.');}};
  $('download-ranking').onclick=()=>{const meta=currentMetric();download(`ranking-${meta.id}${meta.budget?'-'+state.budgetBasis:''}.csv`,csv(rankingExportRows(rankingRows(),meta)));};
  $('download-municipality').onclick=()=>{const m=current();download(`municipio-${m.id}.csv`,csv([['Municipio','Indicador','Valor','Unidad','Período','Criterio'],...METRICS.map(meta=>[m.municipio,meta.label,metricValue(m,meta),metricExportUnit(meta),meta.period,meta.note]),...fiscalExportRows(m),...annualBudgetExportRows(m),...municipalContextExportRows(m)]));};
  let resizeTimer;new ResizeObserver(()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(state.view==='panorama')drawMap();if(state.view==='recursos')drawTransferChart();if(state.view==='empleo')drawEmploymentChart();},80);}).observe(document.querySelector('main'));
  new ResizeObserver(()=>document.documentElement.style.setProperty('--header-height',document.querySelector('.site-header').getBoundingClientRect().height+'px')).observe(document.querySelector('.site-header'));
}
async function init(){
  try{
    const responses=await Promise.all([fetch('data/dashboard.json?v=20260910-1'),fetch('data/geografia_original.geojson'),fetch('data/deflator.json?v=20260909-2')]);
    if(responses.some(r=>!r.ok))throw new Error('No se pudieron leer los datos municipales.');
    const [dashboardText,geo,prices]=await Promise.all([responses[0].text(),responses[1].json(),responses[2].json()]);data=JSON.parse(dashboardText);geography=geo;deflator=prices;rows=data.municipalities;byId=new Map(rows.map(m=>[m.id,m]));
    const params=new URLSearchParams(location.search);priceMode=params.get('pesos')==='corrientes'?'nominal':'real';priceBase=deflator.bases.includes(params.get('base'))?params.get('base'):deflator.latest;
    for(const id of ['price-from','price-to']){$(id).min=Object.keys(deflator.indices).sort()[0];$(id).max=deflator.latest;}
    if(rows.length!==135||geography.features.length!==135||geography.features.some(f=>!byId.has(f.properties.id)))throw new Error('La cobertura geográfica no coincide con los datos.');
    let saved;try{saved=localStorage.getItem('pellegrini_municipio');}catch{}
    state=readState(location.search,rows,saved);rankAscending=currentMetric().ascending;
    $('municipality').innerHTML=rows.slice().sort((a,b)=>a.municipio.localeCompare(b.municipio,'es')).map(m=>`<option value="${m.id}">${escape(m.municipio)}</option>`).join('');$('municipality').disabled=false;
    $('loading').hidden=true;$('dashboard').hidden=false;attachEvents();persist();renderView();window.dispatchEvent(new CustomEvent('dashboard:view',{detail:{view:state.view}}));
    prepareReports(dashboardText);
  }catch(error){$('loading').hidden=true;$('dashboard').hidden=true;$('error').hidden=false;console.error('Error al iniciar el tablero municipal:',error.message);}
}
init();

/* All displayed money is stored in ARS millions. No figures from the reference site. */
(() => {
  'use strict';
  const M=window.BudgetMath, $=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fold=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const nf=(v,d=1)=>new Intl.NumberFormat('es-AR',{minimumFractionDigits:d,maximumFractionDigits:d}).format(v);
  const pct=v=>M.finite(v)?`${v>0?'+':''}${nf(v)}%`:'Sin comparación';
  const sign=v=>!M.finite(v)?'':v<0?'negative':v>0?'positive':'';
  const currency=v=>v<0?'−$':'$';
  const money=v=>!M.finite(v)?'Sin dato':Math.abs(v)>=1e6?`${currency(v)}${nf(Math.abs(v)/1e6)} billones`:Math.abs(v)>=1000?`${currency(v)}${nf(Math.abs(v)/1000)} mil millones`:`${currency(v)}${nf(Math.abs(v),0)} ${Math.abs(v)===1?'millón':'millones'}`;
  const short=v=>!M.finite(v)?'—':Math.abs(v)>=1e6?`${currency(v)}${nf(Math.abs(v)/1e6)} bill.`:Math.abs(v)>=1000?`${currency(v)}${nf(Math.abs(v)/1000)} mil M`:`${currency(v)}${nf(Math.abs(v),0)} M`;
  const params=new URLSearchParams(location.search);
  const state={price:params.get('precios')==='real'?'real':'nominal',base:['law','current','closing'].includes(params.get('base'))?params.get('base'):'current',lens:['topics','jurisdictions','functions','geographies'].includes(params.get('vista'))?params.get('vista'):'topics',rank:'jurisdictions',history:'amount',province:params.get('provincia')||'',programLimit:16};
  let D,G,dataHash,reportManifest;
  const baseLabel=()=>({law:'Inicial 2026',current:'Vigente 2026 · 15/09',closing:'Cierre estimado 2026'})[state.base];
  const unit=()=>state.price==='real'?'Pesos de agosto 2026 · escenario':'Pesos corrientes';
  const val=(v,year=2027)=>M.price(v,year,state.price,D.deflator.annual_factors);
  const ch=r=>M.change(val(r.project),val(r[state.base],2026));
  const diff=r=>M.delta(val(r.project),val(r[state.base],2026));
  const source=(name,page)=>{const s=D.sources.find(s=>s.file===name);return s?`${s.url}${page?'#page='+page:''}`:'https://www.mecon.gob.ar/onp/presupuestos/2027';};
  const origin=(file,page,label='Documento oficial ↗')=>`<a href="${esc(source(file,page))}" target="_blank" rel="noopener">${label}</a>`;
  const byProject=a=>[...a].sort((a,b)=>(b.project??-1)-(a.project??-1));
  const width=(v,max)=>M.finite(v)&&max>0?Math.max(0,Math.min(100,v/max*100)):0;
  function readingControls(){
    const page=M.pageForAnchor(location.hash.slice(1));
    document.querySelector('.controls').hidden=page==='metodo';
    $('base-select').closest('label').hidden=!['panorama','gasto'].includes(page);
    $('base-select').value=state.base;
    $('unit-context').textContent=state.price==='real'?(page==='ejecucion'?'Cada mes, a pesos de agosto de 2026. IPC observado.':'Pesos de agosto 2026 · escenario de inflación.'):'Montos de cada año, sin descontar inflación.';
  }
  function sync(){
    document.querySelectorAll('[data-price],[data-base],[data-lens],[data-rank],[data-history]').forEach(b=>{const k=['price','base','lens','rank','history'].find(k=>b.dataset[k]);b.setAttribute('aria-pressed',String(state[k]===b.dataset[k]));});
    const u=new URL(location.href);u.searchParams.set('precios',state.price);u.searchParams.set('base',state.base);u.searchParams.set('vista',state.lens);if(state.province)u.searchParams.set('provincia',state.province);else u.searchParams.delete('provincia');history.replaceState(null,'',u);
    readingControls();
    document.querySelectorAll('.base-key').forEach(el=>el.textContent=baseLabel());
  }
  function pair(name,a,b,max,changeText='',changeClass='',unitType='money'){
    const format=v=>unitType==='share'?`${nf(v)}%`:short(v), title=v=>unitType==='share'?`${nf(v)}% del total`:money(v);
    return `<div class="bar-row"><div class="bar-heading"><span>${esc(name)}</span><span class="${changeClass}">${esc(changeText)}</span></div><div class="bar-pair"><div class="bar-line"><div class="plot"><div class="bar" style="width:${width(a,max)}%" title="${esc(baseLabel()+': '+(M.finite(a)?title(a):'Sin dato'))}"></div></div><span>${M.finite(a)?format(a):'—'}</span></div><div class="bar-line project"><div class="plot"><div class="bar" style="width:${width(b,max)}%" title="${esc('Proyecto 2027: '+(M.finite(b)?title(b):'Sin dato'))}"></div></div><span>${M.finite(b)?format(b):'—'}</span></div></div></div>`;
  }
  function hero(){
    const amount=val(D.total.project), change=ch(D.total);
    $('headline-total').innerHTML=`$${nf(amount/1e6)} <small>billones</small>`;
    $('headline-unit').textContent=`Proyecto 2027 · ${unit()}`;
    const o=M.budgetOverview(D.total,state.base,D.deflator.annual_factors);
    const comparisonLabel=({law:'el presupuesto inicial de 2026',current:'el presupuesto vigente de 2026 al 15/09',closing:'el cierre estimado de 2026'})[state.base];
    $('overview-title').textContent=o.realChange<0?'El presupuesto pierde poder de compra.':'El gasto crece. La inflación achica esa suba.';
    $('headline-reading').innerHTML=`Comparado con ${comparisonLabel}, el proyecto ${o.nominalChange<0?'baja':'sube'} <strong>${nf(Math.abs(o.nominalChange))}% en pesos</strong>. Al descontar la inflación del escenario, ${o.realChange<0?'la caída es':'el aumento queda en'} <strong>${nf(Math.abs(o.realChange))}%</strong>. La diferencia importa: una cosa es asignar más pesos y otra es cuánto permiten financiar.`;
    $('headline-change').textContent=pct(change);$('headline-change').className=sign(change);
    $('headline-base').textContent=`frente a ${baseLabel().toLowerCase()} · ${state.price==='real'?'variación real':'variación nominal'}`;
    const social=D.functions.find(f=>f.name==='Seguridad Social');
    $('overview-stats').innerHTML=[['Cambio real',pct(o.realChange),sign(o.realChange),'Poder de compra frente a la base 2026 elegida. Escenario de inflación.','comparacion','Comparar las áreas'],['Seguridad social',`${nf(M.ratio(social.project,D.total.project))}%`,'','del gasto propuesto. Incluye jubilaciones, pensiones y otras prestaciones.','distribucion','Ver la distribución'],['Ejecución 2026',`${nf(o.execution)}%`,'','del presupuesto vigente devengado al 15/09. Septiembre es parcial.','ejecucion','Seguir la ejecución']].map(([label,value,cls,detail,anchor,link])=>`<article class="overview-stat"><h3>${label}</h3><span class="stat-value ${cls}">${value}</span><p>${detail}</p><a href="#${anchor}">${link} →</a></article>`).join('');
    $('real-note').hidden=state.price!=='real';
  }
  const topicText={t0:'Jubilaciones, pensiones y otras prestaciones de la seguridad social. Es el principal componente del gasto.',t1:'Atención, prevención y programas sanitarios de alcance nacional.',t2:'Incluye educación superior, políticas educativas y cultura. El gasto educativo de provincias queda fuera de este universo.',t3:'Transferencias sociales y políticas de empleo. Su alcance depende de los beneficiarios y las prestaciones financiadas.',t4:'Investigación, desarrollo y organismos del sistema científico.',t5:'Defensa nacional, seguridad interior, sistema penal e inteligencia.',t6:'Energía, combustibles y minería, incluidos los subsidios presupuestados en estas funciones.',t7:'Infraestructura, servicios y políticas de transporte.',t8:'Vivienda, agua, saneamiento y cuidado ambiental.',t9:'Políticas productivas, regulación económica y comunicaciones.',t10:'Administración de justicia. No incluye toda la política de seguridad.',t11:'Funciones legislativas, administración pública, relaciones interiores y exteriores y controles.',t12:'Intereses y gastos del servicio de la deuda. Las amortizaciones de capital son aplicaciones financieras y no integran este total.'};
  function detailsFor(r){
    let text='',items=[];
    if(state.lens==='topics'){text=topicText[r.id];items=D.functions.filter(f=>r.functions.includes(f.id));}
    if(state.lens==='jurisdictions'){text=r.note||'Las siguientes partidas pertenecen a esta jurisdicción en el proyecto 2027.';items=byProject(D.programs.filter(p=>p.jurisdiction===r.name));}
    if(state.lens==='functions'){text='La función clasifica el objetivo del gasto. Este mismo dinero también aparece agrupado por ministerio: son distintas lecturas, no importes que deban sumarse.';}
    if(state.lens==='geographies'){text='Gasto nacional localizado presupuestariamente en esta jurisdicción. No equivale a fondos transferidos al gobierno provincial.';items=byProject(D.works.filter(w=>w.province===r.name));}
    return `<p>${esc(text)}</p>${items.map(x=>`<div class="mini-row"><span>${esc(x.name)}</span><strong>${short(val(x.project))}</strong></div>`).join('')}${r.source?`<p class="note">${origin(r.source,r.page)}</p>`:''}`;
  }
  function distribution(){
    const rows=byProject(D[state.lens]).filter(r=>M.finite(r.project));
    $('distribution-note').textContent=({topics:'13 temas · agrupación editorial de las funciones oficiales.',jurisdictions:'15 jurisdicciones en el proyecto. Incluye poderes del Estado, ministerios y obligaciones del Tesoro.',functions:'29 funciones oficiales · cada gasto se cuenta una sola vez.',geographies:'24 jurisdicciones y 4 ubicaciones adicionales. La ubicación no identifica necesariamente al beneficiario.'})[state.lens];
    $('composition').innerHTML=rows.map(r=>`<span style="width:${width(r.project,D.total.project)}%" title="${esc(r.name)}: ${nf(M.ratio(r.project,D.total.project))}%"></span>`).join('');
    $('cards').innerHTML=rows.map((r,i)=>`<article class="card"><div class="card-top"><span>${String(i+1).padStart(2,'0')}</span><span class="${sign(ch(r))}" title="Variación respecto de ${esc(baseLabel())}">${pct(ch(r))}</span></div><h3>${esc(r.name)}</h3><div class="card-value">${money(val(r.project))}</div><div class="card-share">${nf(M.ratio(r.project,D.total.project))}% del proyecto · ${esc(unit())}</div><div class="track"><span style="width:${width(r.project,rows[0].project)}%"></span></div><details><summary>Entender esta partida</summary>${detailsFor(r)}</details></article>`).join('');
  }
  function buildMap(){
    const max=Math.max(...D.works_geographies.map(r=>r.project));
    // Keep all source polygons; remote South Atlantic islands occupy a labelled inset.
    const mapPath=f=>f.province!=='Tierra del Fuego'?f.path:(f.path.match(/M[^M]+/g)||[]).map(part=>Number(part.match(/^M([\d.]+)/)?.[1])>300?part.replace(/([ML])([\d.]+),([\d.]+)/g,(_,command,x,y)=>`${command}${(170+(Number(x)-350)*.6).toFixed(2)},${(602+(Number(y)-550)*.35).toFixed(2)}`):part).join('');
    $('map').innerHTML=`<svg viewBox="0 0 300 665" role="group" aria-label="Mapa de obras por provincia, con islas del Atlántico Sur en recuadro">${G.features.map(f=>{const r=D.works_geographies.find(r=>r.name===f.province);return `<path d="${esc(mapPath(f))}" data-province="${esc(f.province)}" tabindex="0" role="button" aria-label="${esc(f.province)}: ${r?money(val(r.project)):'sin partida localizada'}" style="fill-opacity:${r?.project?.toString()?0.28+0.72*Math.sqrt(r.project/max):.18}"><title>${esc(f.province)} · ${r?money(val(r.project)):'sin dato'}</title></path>`;}).join('')}<rect x="158" y="580" width="128" height="76" fill="none" stroke="var(--border)"/><text x="164" y="594" fill="var(--muted)" font-size="8">Islas del Atlántico Sur · recuadro</text></svg>`;
    $('map').querySelectorAll('[data-province]').forEach(p=>{p.addEventListener('click',()=>selectProvince(p.dataset.province));p.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectProvince(p.dataset.province);}});});
  }
  function selectProvince(name){state.province=name;$('province').value=name;sync();works();}
  function works(){
    const q=fold($('work-search').value);const rows=byProject(D.works.filter(w=>(!state.province||w.province===state.province)&&fold([w.name,w.entity,w.jurisdiction,w.province].join(' ')).includes(q)));
    $('works-reading').innerHTML=`<strong>${D.works.length} partidas</strong> de proyectos de inversión por <strong>${money(val(D.works_total))}</strong> en el proyecto 2027. Buscá qué obras tienen presupuesto en cada provincia.`;
    const sum=rows.reduce((a,r)=>a+r.project,0);
    $('works-count').textContent=`${rows.length} partidas · ${money(val(sum))}${state.province?' · '+state.province:''}`;
    $('works-list').innerHTML=rows.length?rows.map(w=>`<article class="work"><small>${esc(w.province)} · ${esc(w.entity)}</small><h3>${esc(w.name)}</h3><span class="amount">${money(val(w.project))}</span><small>${origin(w.source,w.page,'Ver partida ↗')}</small></article>`).join(''):'<p class="empty">No hay partidas que coincidan con esta búsqueda.</p>';
    $('map').querySelectorAll('[data-province]').forEach(p=>{const active=p.dataset.province===state.province;p.classList.toggle('selected',active);p.setAttribute('aria-pressed',String(active));});
  }
  function programs(){
    const q=fold($('program-search').value);const rows=byProject(D.programs.filter(p=>M.searchText(p).includes(q)));
    $('program-count').textContent=`${rows.length} de ${D.programs.length} partidas programáticas · proyecto 2027`;
    $('program-list').innerHTML=rows.slice(0,state.programLimit).map(p=>`<details class="program"><summary><span class="program-name">${esc(p.name)}<small>${esc(p.entity)} · ${esc(p.jurisdiction)}</small></span><span class="program-amount">${short(val(p.project))}<small>Ver detalle +</small></span></summary><div class="program-detail"><p>El proyecto asigna <strong>${money(val(p.project))}</strong>${p.matched?`. Frente al crédito vigente de 2026, cambia <span class="${sign(M.change(val(p.project),val(p.current,2026)))}">${pct(M.change(val(p.project),val(p.current,2026)))}</span>.`:'. Falta verificar una correspondencia única con 2026; no se clasifica como un programa nuevo.'}</p><dl><dt>Inicial 2026</dt><dd>${short(val(p.law,2026))}</dd><dt>Vigente 2026 · 15/09</dt><dd>${short(val(p.current,2026))}</dd><dt>Proyecto 2027</dt><dd>${short(val(p.project))}</dd><dt>Ejecución 2026 · nominal</dt><dd>${M.ratio(p.accrued,p.current)===null?'—':nf(M.ratio(p.accrued,p.current))+'%'}</dd></dl><p class="note">${unit()}. ${origin(p.source,p.page)}</p></div></details>`).join('')||'<p class="empty">No encontramos coincidencias. Probá con otra palabra.</p>';
    $('program-more').hidden=rows.length<=state.programLimit;
  }
  function scale(){
    const interest=D.functions.find(f=>f.name==='Servicio de la Deuda Pública (intereses y gastos)');
    const items=[['Intereses de la deuda',`${nf(M.ratio(interest.project,D.total.project))}%`,'del gasto propuesto. Son intereses y gastos de la deuda, sin devolución de capital.'],['Gasto de capital',`${nf(M.ratio(3768279,D.total.project))}%`,'del total. Incluye inversión real, transferencias de capital e inversión financiera.'],['Inflación prevista','18,0%','Diciembre de 2027 contra diciembre de 2026. Este supuesto influye en cuánto alcanza el presupuesto.']];
    $('scale').innerHTML=items.map(([a,b,c])=>`<article class="scale-item"><h3>${a}</h3><div class="metric">${b}</div><p>${c}</p></article>`).join('');
  }
  function comparison(){
    const rows=byProject(D.jurisdictions);const max=Math.max(...rows.flatMap(r=>[val(r.project)||0,val(r[state.base],2026)||0]));
    $('base-note').textContent=({law:'Inicial: crédito presupuestado que publica Presupuesto Abierto para 2026.',current:'Vigente: autorización actual, después de las modificaciones presupuestarias. Corte 15/09/2026.',closing:'Cierre estimado: base 2026 de los cuadros comparativos del proyecto 2027. No es el crédito vigente ni lo ejecutado.'})[state.base]+' · '+unit()+'.';
    $('comparison-chart').innerHTML=rows.map(r=>pair(r.name,val(r[state.base],2026),val(r.project),max,pct(ch(r)),sign(ch(r)))).join('');
    $('purpose-chart').innerHTML=byProject(D.purposes).map(p=>{const a=M.ratio(p[state.base],D.total[state.base]),b=M.ratio(p.project,D.total.project),delta=M.delta(b,a);return `<details class="purpose"><summary>${esc(p.name)}</summary>${D.functions.filter(f=>f.purpose===p.id).map(f=>`<div class="mini-row"><span>${esc(f.name)}</span><strong>${nf(M.ratio(f.project,D.total.project))}% del total</strong></div>`).join('')}</details>${pair('',a,b,100,delta===null?'Sin comparación':`${delta>0?'+':''}${nf(delta)} pp`,sign(delta),'share')}`;}).join('');
  }
  function changes(){
    const all=D[state.rank];const rows=all.filter(r=>M.finite(diff(r)));const up=[...rows].filter(r=>diff(r)>0).sort((a,b)=>diff(b)-diff(a)).slice(0,5);const down=[...rows].filter(r=>diff(r)<0).sort((a,b)=>diff(a)-diff(b)).slice(0,5);
    const list=(label,rows)=>`<div><h3>${label}</h3>${rows.length?rows.map(r=>`<article class="change-row"><strong class="${sign(diff(r))}">${diff(r)>0?'+':''}${short(diff(r))}</strong><p>${esc(r.name)}</p><small>${pct(ch(r))} respecto de ${esc(baseLabel().toLowerCase())}</small></article>`).join(''):'<p class="empty">No hay variaciones en este sentido entre las partidas comparables.</p>'}</div>`;
    $('changes').innerHTML=list('Mayores subas',up)+list('Mayores bajas',down);
    $('ranking-note').textContent=`${unit()} · ${rows.length} partidas comparables de ${all.length}. ${state.rank==='programs'&&state.base==='closing'?'El anexo programático no publica una base de cierre 2026; elegí Inicial o Vigente en la sección V.':'Las partidas sin correspondencia verificada quedan fuera del ranking.'} Los colores indican aumento o reducción del monto; no califican la calidad del gasto.`;
  }
  function resources(){
    const rows=byProject(D.resources),max=Math.max(...rows.map(r=>val(r.project)));
    $('resources-reading').innerHTML=`El proyecto estima <strong>${money(val(D.resources_total))}</strong> de ingresos corrientes y de capital. Esta clasificación incluye rentas de la propiedad; por eso no coincide con el total consolidado que excluye rentas del FGS y del BCRA.`;
    $('resources-chart').innerHTML=rows.map(r=>`<div class="bar-row"><div class="bar-heading"><span>${esc(r.name)}</span><span>${nf(M.ratio(r.project,D.resources_total))}%</span></div><div class="bar-line project"><div class="plot"><div class="bar" style="width:${width(val(r.project),max)}%" title="${esc(money(val(r.project)))}"></div></div><span>${short(val(r.project))}</span></div></div>`).join('');
    const pension=D.functions.find(f=>f.name==='Seguridad Social'),contrib=rows.find(r=>r.name.startsWith('Aportes'));
    $('pension-reading').innerHTML=`<p><strong>Los aportes no son el único sostén de la seguridad social.</strong> El proyecto prevé ${money(val(contrib.project))} de aportes y contribuciones y ${money(val(pension.project))} de gasto en la función Seguridad Social. El resto se financia también con impuestos y otros recursos. Esta relación orienta sobre la escala; no mide por sí sola el déficit de ANSES.</p>`;
  }
  function macro(){
    $('macro-table').innerHTML=`<table><caption class="sr-only">Supuestos oficiales del Mensaje del presupuesto</caption><thead><tr><th>Variable</th><th>2025</th><th>2026</th><th>2027</th></tr></thead><tbody>${D.macro.map(r=>`<tr><td>${esc(r.name)}</td>${r.values.map((v,i)=>`<td class="${v<0?'negative':i===2?'project-col':''}">${r.unit==='ARS/USD'?'$':''}${nf(v)}${r.unit==='%'?'%':''}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }
  const purposeColors=['var(--project)','var(--chart-secondary)','var(--base)','var(--chart-amber)','var(--chart-purple)'];
  function historyChart(){
    const rows=D.history,max=Math.max(...rows.map(r=>state.history==='gdp'?(r.gdp_share||0):val(r.amount,r.year)));
    $('history-chart').innerHTML=rows.map(r=>{let graph;if(state.history==='composition'){const sum=r.purposes.reduce((a,b)=>a+b,0);graph=`<div class="history-stack">${r.purposes.map((v,i)=>`<span style="width:${width(v,sum)}%;background:${purposeColors[i]}" title="${esc(D.purposes[i].name)}: ${nf(M.ratio(v,sum))}%"></span>`).join('')}</div><div class="note">${r.purposes.map((v,i)=>`${esc(D.purposes[i].name)}: ${nf(M.ratio(v,sum))}%`).join(' · ')}</div>`;}else{const v=state.history==='gdp'?r.gdp_share:val(r.amount,r.year);graph=M.finite(v)?`<div class="bar-line ${r.year===2027?'project':''}"><div class="plot"><div class="bar" style="width:${width(v,max)}%"></div></div><span>${state.history==='gdp'?nf(v)+'%':short(v)}</span></div>`:'<span class="note">Pendiente de una base comparable</span>';}
    return `<div class="history-item"><div><strong>${r.year}</strong><small>${esc(r.stage)}</small></div><div>${graph}</div></div>`;}).join('');
    $('history-note').textContent=state.history==='gdp'?'Gasto devengado / PIB nominal, según la serie oficial. Para 2026–2027 falta una base del PIB conciliada con el mismo alcance presupuestario. No se empalma el 14% consolidado del Mensaje con este universo.':state.history==='composition'?'Participación de las cinco finalidades. Los porcentajes no cambian al descontar inflación.':`${unit()}. 2023–2025: ejecución observada. 2026–2027: autorizaciones y proyecto; no son resultados anuales realizados.${state.price==='real'?' El ajuste anual usa IPC promedio de cada año; 2026 y 2027 incluyen proyecciones.':''}`;
  }
  function execution(){
    const r=D.execution.find(r=>r.name===$('execution-jurisdiction').value)||D.execution[0],cum=M.cumulative(r.months),total=cum.at(-1).cumulative,percent=M.ratio(total,r.current);
    $('execution-reading').innerHTML=`<div class="metric">${nf(percent)}%</div><p>Se reconocieron gastos por <strong>${money(total)}</strong> sobre ${money(r.current)} de crédito vigente. Por cada $100 autorizados, se devengaron <strong>$${nf(percent)}</strong>.</p><p class="note">Importes nominales. Este porcentaje conserva su significado al cambiar el selector de precios.</p>`;
    const W=Math.max(320,Math.min(900,$('execution-chart').clientWidth||900)),H=280,L=40,R=20,T=25,B=42,ys=v=>T+(100-v)*(H-T-B)/100,xs=i=>L+i*(W-L-R)/8;
    const points=cum.map((m,i)=>`${xs(i)},${ys(M.ratio(m.cumulative,r.current))}`);
    const months=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep*'];
    $('execution-chart').innerHTML=`<svg class="execution-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Gasto devengado acumulado como porcentaje del crédito vigente. Datos completos en la tabla siguiente.">${[0,25,50,75,100].map(v=>`<line class="gridline" x1="${L}" x2="${W-R}" y1="${ys(v)}" y2="${ys(v)}"/><text x="3" y="${ys(v)+4}">${v}%</text>`).join('')}<polyline class="line" points="${points.slice(0,8).join(' ')}"/><polyline class="line partial-line" points="${points.slice(7).join(' ')}"/>${cum.map((m,i)=>`<circle cx="${xs(i)}" cy="${ys(M.ratio(m.cumulative,r.current))}" r="5"><title>${months[i]}: ${nf(M.ratio(m.cumulative,r.current))}%${m.partial?' · mes parcial':''}</title></circle><text x="${xs(i)}" y="${H-12}" text-anchor="middle">${months[i]}</text>`).join('')}</svg>`;
    $('execution-table').innerHTML=`<table><caption class="sr-only">Detalle mensual 2026 de ${esc(r.name)}</caption><thead><tr><th>Mes</th><th>${state.price==='real'?'Mes · pesos ago. 2026':'Gasto del mes'}</th><th>Acumulado / vigente</th></tr></thead><tbody>${cum.map((m,i)=>`<tr><td>${months[i]}${m.partial?' · parcial':''}</td><td class="${sign(state.price==='real'?m.real:m.accrued)}">${short(state.price==='real'?m.real:m.accrued)}</td><td>${nf(M.ratio(m.cumulative,r.current))}%</td></tr>`).join('')}</tbody></table>${state.price==='real'?'<p class="note">Cada mes se ajusta con su propio IPC. Septiembre queda sin monto real hasta contar con el IPC observado; no se usa la proyección para medir ejecución realizada.</p>':''}`;
  }
  function methodology(){
    $('deflator-method').textContent=D.deflator.method;
    $('coverage-method').textContent=`Se extrajeron ${D.programs.length} partidas programáticas y ${D.works.length} partidas de proyectos. ${D.meta.program_join_matched} partidas programáticas tienen correspondencia por nombre, entidad y jurisdicción con 2026. Las restantes requieren revisar códigos o cambios institucionales: no se presentan como programas nuevos ni se completan con cero.`;
    const links=[['mensaje2027.pdf','Mensaje del proyecto 2027'],['cap1cu02.pdf','Finalidades y funciones'],['cap1cu04.pdf','Jurisdicciones y comparación 2026'],['cap1cu06.pdf','Distribución geográfica'],['cap1pla7.pdf','Detalle de programas'],['cap1pl12.pdf','Obras por ubicación'],['cap1cu08.pdf','Recursos del presupuesto'],['credito-anual-2026.zip','Presupuesto y ejecución 2026 · anual'],['credito-mensual-2026.zip','Ejecución 2026 · mensual'],['serie_pib_anual.csv','Serie histórica y PIB']];
    $('source-links').innerHTML=links.map(([f,t])=>origin(f,null,esc(t)+' ↗')).join('')+'<a href="../data/ipc_source.json">IPC INDEC · trazabilidad ↗</a>';
  }
  function download(){
    const header=['grupo','id','nombre','etapa_2027','unidad','proyecto_2027','inicial_2026','vigente_2026_2026-09-15','cierre_estimado_2026','devengado_2026_nominal','fuente'];
    const rows=[header];
    for(const group of ['jurisdictions','functions','geographies','programs','works','resources'])for(const r of D[group])rows.push([group,r.id||'',r.name,'Proyecto de ley','ARS millones · '+unit(),val(r.project),val(r.law,2026),val(r.current,2026),val(r.closing,2026),r.accrued,source(r.source,r.page)]);
    const blob=new Blob(['\ufeff'+rows.map(r=>r.map(M.csvCell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8;'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`presupuesto-nacional-2027-${state.price}-ARS-millones.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function render(){sync();hero();distribution();buildMap();works();programs();scale();comparison();changes();resources();macro();historyChart();execution();}
  const header=document.querySelector('.site-header');
  const measureHeader=()=>document.documentElement.style.setProperty('--national-header-height',header.getBoundingClientRect().height+'px');
  new ResizeObserver(measureHeader).observe(header);measureHeader();
  $('theme').addEventListener('click',()=>{const light=document.documentElement.dataset.theme!=='light';document.documentElement.dataset.theme=light?'light':'dark';$('theme').setAttribute('aria-label',light?'Cambiar a modo oscuro':'Cambiar a modo claro');document.querySelector('meta[name="theme-color"]').content='#0A192F';try{localStorage.setItem('national-budget-theme-v2',light?'light':'dark');}catch{}});
  try{if(localStorage.getItem('national-budget-theme-v2')==='dark')$('theme').click();}catch{}
  document.querySelectorAll('[data-price],[data-base],[data-lens],[data-rank],[data-history]').forEach(b=>b.addEventListener('click',()=>{const key=['price','base','lens','rank','history'].find(k=>b.dataset[k]);state[key]=b.dataset[key];if(D)render();else sync();}));
  function route(focus=false){
    const anchor=location.hash.slice(1)||'inicio',page=M.pageForAnchor(anchor);
    if(D){
      const query=new URLSearchParams(location.search);
      const next={price:query.get('precios')==='real'?'real':'nominal',base:['law','current','closing'].includes(query.get('base'))?query.get('base'):'current',lens:['topics','jurisdictions','functions','geographies'].includes(query.get('vista'))?query.get('vista'):'topics',province:query.get('provincia')||''};
      if(!Array.from($('province').options).some(o=>o.value===next.province))next.province='';
      if(Object.entries(next).some(([key,value])=>state[key]!==value)){Object.assign(state,next);$('province').value=state.province;render();}
    }
    document.querySelectorAll('[data-page]').forEach(el=>el.hidden=el.dataset.page!==page);
    document.querySelectorAll('[data-page-link]').forEach(el=>{if(el.dataset.pageLink===page)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
    readingControls();
    if(!D)return;
    if(page==='ejecucion')execution();
    window.dispatchEvent(new CustomEvent('dashboard:view',{detail:{view:anchor}}));
    const target=document.getElementById(anchor)||$('inicio');
    const scrollTarget=['inicio','distribucion','obras','recursos','ejecucion','metodo'].includes(anchor)?$('contenido'):target;
    requestAnimationFrame(()=>{scrollTarget.scrollIntoView({block:'start',behavior:'instant'});if(focus)(target.querySelector('h2[tabindex]')||target.querySelector('h1'))?.focus({preventScroll:true});});
  }
  window.addEventListener('hashchange',()=>route(true));
  window.addEventListener('popstate',()=>route(true));
  document.querySelectorAll('[data-page-link]').forEach(link=>link.addEventListener('click',event=>{if(link.hash===location.hash){event.preventDefault();route(true);}}));
  $('base-select').addEventListener('change',()=>{state.base=$('base-select').value;if(D)render();else sync();});
  $('province').addEventListener('change',()=>selectProvince($('province').value));$('work-search').addEventListener('input',works);
  $('program-search').addEventListener('input',()=>{state.programLimit=16;programs();});$('program-more').addEventListener('click',()=>{state.programLimit+=24;programs();});
  $('execution-jurisdiction').addEventListener('change',execution);$('download').addEventListener('click',download);
  function updateReport(){
    $('download-national-report').hidden=true;
    $('report-unit-note').textContent=$('report-price').value==='real'?'El ajuste anual usa IPC promedio. Para 2026 y 2027 incluye el escenario de inflación del tablero.':'Los montos corresponden a los precios de cada año. El análisis también muestra el cambio real, ajustado por inflación.';
    if(!reportManifest)return;
    try{
      const pdf=window.NationalReport.selectReport(reportManifest,{price:$('report-price').value,base:$('report-base').value,annex:$('report-annex').checked},dataHash);
      $('download-national-report').href=pdf.href;$('download-national-report').download=pdf.file;$('download-national-report').hidden=false;
      $('report-status').textContent=`${pdf.pages} páginas · ${$('report-annex').checked?'Informe y anexo detallado':'Informe con todos los capítulos'} · Federico Pellegrini`;
    }catch(error){$('report-status').textContent=error.message;}
  }
  $('export-report').addEventListener('click',async()=>{
    $('report-price').value=state.price;$('report-base').value=state.base;
    $('report-status').textContent='Preparando el informe…';$('download-national-report').hidden=true;
    $('report-dialog').showModal();updateReport();
    try{
      const response=await fetch('reports/manifest.json',{cache:'no-cache'});if(!response.ok)throw Error('No se pudo cargar el informe. Cerrá esta ventana y volvé a intentarlo.');
      reportManifest=await response.json();updateReport();
    }catch(error){$('report-status').textContent=error.message;}
  });
  $('close-report').addEventListener('click',()=>$('report-dialog').close());
  ['report-price','report-base','report-annex'].forEach(id=>$(id).addEventListener('change',updateReport));
  window.addEventListener('resize',()=>{if(D)execution();});
  Promise.all([fetch('data/budget.json').then(async r=>{if(!r.ok)throw Error(r.status);const text=await r.text();dataHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text.replace(/\r\n/g,'\n')))),b=>b.toString(16).padStart(2,'0')).join('');return JSON.parse(text);}),fetch('../data/province_geometry.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json();})]).then(([data,geo])=>{
    D=data;G=geo;
    const locations=[...new Set([...D.works_geographies.map(r=>r.name),...G.features.map(f=>f.province)])].sort((a,b)=>a.localeCompare(b,'es'));
    $('province').innerHTML='<option value="">Todo el país</option>'+locations.map(s=>`<option value="${esc(s)}">${esc(s)}</option>`).join('');if(!locations.includes(state.province))state.province='';$('province').value=state.province;
    $('execution-jurisdiction').innerHTML=D.execution.map(r=>`<option value="${esc(r.name)}">${esc(r.name)}</option>`).join('');
    $('load-state').hidden=true;$('dashboard').hidden=false;$('export-report').disabled=false;render();methodology();
    route();
  }).catch(error=>{console.error('No se pudo cargar el presupuesto',error);$('load-state').innerHTML='No se pudieron cargar los datos. <a href="">Reintentar</a> o consultar los <a href="https://www.mecon.gob.ar/onp/presupuestos/2027">documentos oficiales</a>.';});
})();

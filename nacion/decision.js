/* Policy links use verified identities; no model-generated matches or forecasts. */
(() => {
  'use strict';
  const M=window.BudgetMath,N=window.NationalDecisionMath,$=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=(v,d=1)=>M.finite(v)?new Intl.NumberFormat('es-AR',{maximumFractionDigits:d,minimumFractionDigits:d}).format(v):'Sin dato';
  const pct=v=>M.finite(v)?`${v>0?'+':''}${num(v)}%`:'No publicado';
  const money=v=>!M.finite(v)?'Sin dato':`${v<0?'−':''}$${num(Math.abs(v)/(Math.abs(v)>=1e6?1e6:Math.abs(v)>=1000?1000:1))} ${Math.abs(v)>=1e6?'billones':Math.abs(v)>=1000?'mil millones':'millones'}`;
  const sign=v=>M.finite(v)?v<0?'negative':v>0?'positive':'':'';
  let D,B,price=new URLSearchParams(location.search).get('precios')==='real'?'real':'nominal';
  const expanded=new Set();
  const val=(v,y=2027)=>M.price(v,y,price,B.deflator.annual_factors);
  const unit=()=>price==='real'?'Pesos de agosto de 2026 · escenario de inflación':'Pesos corrientes';
  const labels={law:'Inicial 2026',current:'Vigente 2026 · 15/09',closing:'Cierre estimado 2026'};
  const table=(head,rows,caption)=>`<div class="decision-table-wrap"><table><caption>${esc(caption)}</caption><thead><tr>${head.map(x=>`<th scope="col">${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map((c,i)=>`<${i?`td data-label="${esc(head[i])}"`:'th scope="row"'}>${c}</${i?'td':'th'}>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  const figure=(title,value,note,cls='')=>`<article><h3>${esc(title)}</h3><strong class="decision-number ${cls}">${value}</strong><p>${esc(note)}</p></article>`;
  const official=(url,label)=>`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)} ↗</a>`;
  function route(){
    const slug=location.hash.replace('#politica-','');
    for(const id of ['inmunizaciones','educacion-superior'])$('politica-'+id).hidden=id!==slug;
  }
  function finance(){
    const f=D.finance,by=Object.fromEntries(f.rows.map(r=>[r.id,r]));
    const names={'I':'Ingresos corrientes','II':'Gastos corrientes','III':'Ahorro corriente','IV':'Ingresos de capital','V':'Gastos de capital','VI':'Ingresos totales','VII':'Gastos totales','XI':'Resultado financiero','XII.1':'Reducción de activos financieros','XII.2':'Endeudamiento y aumento de otros pasivos','XII.3':'Transferencias internas para financiar operaciones','XII':'Total de fuentes financieras','XIII.1':'Inversión financiera','XIII.2':'Amortización de deuda y reducción de otros pasivos','XIII.3':'Transferencias internas para operaciones financieras','XIII':'Total de aplicaciones financieras'};
    const amount=id=>val(by[id].project);
    const rows=ids=>ids.map(id=>[esc(names[id]||by[id].label),`<span class="${by[id].closing<0?'negative':''}">${money(val(by[id].closing,2026))}</span>`,`<span class="${by[id].project<0?'negative':''}">${money(amount(id))}</span>`]);
    $('financiamiento').innerHTML=`<p class="eyebrow">Economía / Cierre y financiamiento</p><h2 tabindex="-1">El superávit no elimina los vencimientos</h2><p>El proyecto prevé ingresos por <strong>${money(amount('VI'))}</strong> y gastos por <strong>${money(amount('VII'))}</strong>. La diferencia deja ${by.XI.project>=0?'un superávit':'un déficit'} de <strong class="${sign(by.XI.project)}">${money(amount('XI'))}</strong>. Además, hay capital de deuda y otros pasivos que devolver.</p><p class="note">Administración Nacional · Proyecto 2027 frente al cierre estimado 2026 · ${unit()}.</p>
      <div class="decision-stats">${figure('Resultado financiero',money(amount('XI')),'Ingresos menos gastos, incluidos los intereses.',sign(by.XI.project))}${figure('Capital y otros pasivos a devolver',money(amount('XIII.2')),'Amortización de deuda y disminución de otros pasivos.')}${figure('Financiamiento previsto',money(amount('XII')),'Fuentes financieras del cuadro oficial.')}</div>
      <h3>Cómo cierran los ingresos y gastos</h3>${table(['Concepto','Cierre estimado 2026','Proyecto 2027'],rows(['I','II','III','IV','V','VI','VII','XI']),'Cuenta de ahorro, inversión y financiamiento · '+unit())}
      <p class="decision-reading">El gasto corriente incluye los intereses. La devolución del capital aparece abajo, entre las aplicaciones financieras. Para cubrirla, el Gobierno prevé renovar deuda y obtener otros recursos financieros. El monto de endeudamiento incluye renovaciones y otros pasivos; no equivale al aumento neto de la deuda.</p>
      <div class="finance-columns"><div><h3>De dónde sale el financiamiento</h3>${table(['Concepto','Cierre 2026','Proyecto 2027'],rows(['XII.1','XII.2','XII.3','XII']),'Fuentes financieras · '+unit())}</div><div><h3>En qué se usa</h3>${table(['Concepto','Cierre 2026','Proyecto 2027'],rows(['XIII.1','XIII.2','XIII.3','XIII']),'Aplicaciones financieras · '+unit())}</div></div>
      <p class="finance-equation"><strong>${money(amount('XI'))}</strong> de resultado financiero + <strong>${money(amount('XII'))}</strong> de fuentes financieras = <strong>${money(amount('XIII'))}</strong> de aplicaciones financieras.</p><p class="note">Las contribuciones y los gastos figurativos son transferencias dentro de la Administración Nacional. Figuran a ambos lados y se compensan. Este cuadro anual tiene un alcance distinto de la caja del Sector Público Nacional.</p>
      <div class="decision-links">${official(f.source.url+'#page=1','Cuadro oficial completo')}<a href="data/decisions.json" download>Descargar las cuentas y las fichas</a><a href="#caja">Ver la caja de 2026 →</a></div>`;
  }
  function physicalCard(r){
    const v=N.physicalValue(r);
    return `<article class="policy-measure"><h4>${esc(r.medicion_fisica_desc)}</h4><p class="note">${esc(r.unidad_medida_desc)} · ${esc(r.totalizador_avance_fisico)}</p><dl><div><dt>Previsto a junio</dt><dd>${num(v.planned,1)}</dd></div><div><dt>Realizado a junio</dt><dd>${num(v.actual,1)}</dd></div></dl>${v.partial?'<p class="information-status">Información parcial de las jurisdicciones</p>':''}${v.change!==null?`<p class="note">Desvío frente a lo programado: <strong class="${v.change<0?'negative':''}">${pct(v.change)}</strong>.</p>`:'<p class="note">Falta información para comparar lo previsto y lo realizado.</p>'}${v.comments.length?`<p class="official-cause"><strong>Explicación del organismo.</strong> ${v.comments.map(esc).join(' ')}</p>`:''}</article>`;
  }
  function policy(p){
    const s=N.policyStats(p),comparisons=M.comparisonRows(p.program,B.deflator.annual_factors),real=comparisons.find(r=>r.base==='current').real;
    const vaccines=p.slug==='inmunizaciones';
    const distribution=p.physical.find(r=>r.medicion_fisica_id===1110);
    const ordered=[...p.physical].sort((a,b)=>{const score=r=>(r.medicion_fisica_id===1110?10:0)+(N.physicalValue(r).percent!==null?2:M.finite(r.ejecutado_acumulado_trim2)?1:0);return score(b)-score(a);});
    const measures=expanded.has(p.slug)?ordered:ordered.slice(0,3);
    const trend=real<0?'pierde':'gana';
    const narrative=vaccines?`El proyecto ${trend} <strong>${num(Math.abs(real))}% de poder de compra frente al vigente</strong>. El presupuesto vigente de 2026 fue ampliado respecto del inicial; por eso ambas comparaciones dan una lectura distinta. Al segundo trimestre se distribuyeron <strong>${num(distribution.ejecutado_acumulado_trim2,0)} dosis</strong> de las ${num(distribution.programacion_acumulada_trim2,0)} programadas. El organismo informó demoras en el ingreso de vacunas.`:`El proyecto ${Math.abs(real)<1?'mantiene prácticamente el poder de compra del vigente':trend+' '+num(Math.abs(real))+'% de poder de compra frente al vigente'}. La suba en pesos debe leerse junto con la inflación y con las prestaciones que financia. Hay ejecución informada en <strong>${s.reported} de ${s.count} mediciones</strong> del segundo trimestre.`;
    const next=vaccines?'Revisar las compras previstas, las existencias y las fechas de entrega para saber si alcanzan para sostener el calendario de vacunación. Las dosis distribuidas y las personas vacunadas son mediciones distintas; parte de la información de vacunación está incompleta.':'Revisar si las transferencias previstas alcanzan para sostener salarios, funcionamiento y prestaciones de las universidades. La lectura necesita sumar los costos previstos y la información física que falta; la variación del presupuesto por sí sola no mide la calidad educativa.';
    $('politica-'+p.slug).innerHTML=`<div class="policy-heading"><div><p class="eyebrow">Gasto / Ficha de política pública</p><h2 tabindex="-1">${esc(p.title)}</h2></div><button class="button button-quiet" data-copy-policy="${p.slug}">Copiar enlace</button></div><p class="note">${esc(p.program.name)} · ${esc(p.program.entity)}</p><nav class="decision-links" aria-label="Otras políticas"><a href="#programas">← Buscar programas</a><a href="#politica-${vaccines?'educacion-superior':'inmunizaciones'}">${vaccines?'Universidades':'Vacunas e inmunizaciones'} →</a></nav>
      <div class="decision-stats">${figure('Proyecto 2027',money(val(p.program.project)),unit())}${figure('Cambio real frente al vigente',pct(real),'Con el escenario de inflación del tablero.',sign(real))}${figure('Ejecutado en 2026',num(s.execution)+'%','Gasto reconocido sobre vigente al 15/09.')}</div>
      <p class="decision-reading">${narrative}</p>
      <h3>La comparación cambia según el punto de partida</h3>${table(['Base de 2026','Cambio en pesos','Cambio real'],comparisons.map(r=>[labels[r.base],`<span class="${sign(r.nominal)}">${pct(r.nominal)}</span>`,`<strong class="${sign(r.real)}">${pct(r.real)}</strong>`]),'Proyecto 2027 · Cambio real: después de descontar inflación')}<p class="note">El cierre estimado no está publicado para este programa. Los colores indican suba o baja del monto.</p>
      <h3>Del presupuesto al pago</h3><p class="note">2026 al 15/09 · Pesos corrientes · Las etapas corresponden al mismo gasto.</p><div class="policy-stages">${[['Inicial','credito_presupuestado'],['Vigente','credito_vigente'],['Comprometido','credito_comprometido'],['Gasto reconocido','credito_devengado'],['Pagado','credito_pagado']].map(([label,key])=>`<div><span>${label}</span><strong>${money(p.execution[key])}</strong></div>`).join('')}</div><p>Quedan <strong>${money(s.unpaid)}</strong> de gasto reconocido pendiente de pago. El registro no informa qué parte está vencida.</p>
      <h3>Qué prestaciones se informaron</h3><p class="note">Enero–junio 2026 · ${s.reported} de ${s.count} mediciones con ejecución informada${s.partial?` · ${s.partial} con información parcial`:''}. El corte físico es anterior al financiero.</p><div class="policy-measures">${measures.map(physicalCard).join('')}</div><button class="more" data-policy-more="${p.slug}" aria-expanded="${expanded.has(p.slug)}">${expanded.has(p.slug)?'Mostrar sólo la selección':'Ver las '+s.count+' mediciones'}</button>
      <div class="policy-next"><h3>Qué revisar para decidir</h3><p>${next}</p></div><div class="decision-links">${official(p.sources.project.url+'#page='+p.program.page,'Presupuesto 2027')}${official(p.sources.execution.url,'Ejecución y pagos')}${official(p.sources.physical.url,'Prestaciones y explicaciones')}<a href="data/decisions.json" download>Descargar la información</a><button class="button" data-export-focus="${p.slug}">Exportar esta ficha</button></div><p class="note">Correspondencia verificada entre organismo y programa. SAF ${p.link.servicio_id} · programa ${p.link.programa_id}. Las mediciones conservan su unidad y no se suman entre sí.</p>`;
  }
  function render(){
    B=window.nationalBudgetContext?.data;
    if(!D||!B)return;
    if(!N.inputMatches(D,window.nationalBudgetContext.hash)){showError('Estas fichas se están actualizando para coincidir con el presupuesto. Recargá el tablero.');return;}
    finance();D.policies.forEach(policy);route();
    window.nationalDecisionContext=D;window.dispatchEvent(new Event('national:decisions-ready'));
  }
  function showError(message){
    for(const id of ['financiamiento','politica-inmunizaciones','politica-educacion-superior','obra-ra10','escenarios','attention'])$(id).innerHTML=`<p role="status">${esc(message)} <a href="">Reintentar</a>.</p>`;
    route();
  }
  document.addEventListener('click',async e=>{
    const more=e.target.closest('[data-policy-more]');
    if(more){const slug=more.dataset.policyMore;expanded.has(slug)?expanded.delete(slug):expanded.add(slug);policy(D.policies.find(p=>p.slug===slug));$(`politica-${slug}`).querySelector('[data-policy-more]').focus({preventScroll:true});}
    const copy=e.target.closest('[data-copy-policy]');
    if(copy){const u=new URL(location.href);u.search='';u.searchParams.set('precios',price);u.hash='politica-'+copy.dataset.copyPolicy;try{await navigator.clipboard.writeText(u.href);copy.textContent='Enlace copiado';}catch(_){copy.textContent='Copiá la dirección del navegador';}}
  });
  window.addEventListener('hashchange',route);
  window.addEventListener('national:budget-ready',render);
  window.addEventListener('national:state',e=>{price=e.detail.price;render();});
  fetch('data/decisions.json?v=20260918-programas',{cache:'no-cache'}).then(async r=>{if(!r.ok)throw Error('No se pudieron cargar las fichas y el financiamiento.');const text=await r.text();window.nationalDecisionHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text.replace(/\r\n/g,'\n')))),b=>b.toString(16).padStart(2,'0')).join('');return JSON.parse(text);}).then(data=>{D=data;render();}).catch(e=>showError(e.message));
  route();
})();

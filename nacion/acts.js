(()=>{
  'use strict';
  const $=id=>document.getElementById(id),M=window.BudgetMath;
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=v=>new Intl.NumberFormat('es-AR',{maximumFractionDigits:2}).format(v);
  const money=v=>`${v<0?'−':v>0?'+':''}$${number(Math.abs(v))} millones`;
  let D,act='da26',query='',limit=12;
  function listing(){
    const a=D.acts.find(r=>r.id===act),q=M.fold(query),balance=new Map(D.program_balance.map(r=>[`${r.saf}-${r.program}`,r]));
    const rows=a.rows.filter(r=>M.fold(`${r.name} ${r.entity_name} ${r.saf} ${r.program}`).includes(q)).sort((a,b)=>Math.abs(b.millions)-Math.abs(a.millions));
    $('act-summary').innerHTML=`<p class="decision-reading">${esc(a.reading)}</p><p>La norma cambia el gasto total en <strong class="${a.exact_millions<0?'negative':''}">${money(a.exact_millions)}</strong>. Montos corrientes de 2026.</p><a href="${esc(a.source_path)}" target="_blank" rel="noopener">Ver anexo oficial completo ↗</a>`;
    $('act-count').textContent=`${rows.length} registros del anexo · se muestran ${Math.min(limit,rows.length)}`;
    $('act-list').innerHTML=rows.slice(0,limit).map(r=>{const b=balance.get(`${r.saf}-${r.program}`);return `<article class="policy-next"><p class="eyebrow">SAF ${r.saf} · programa ${r.program} · ${esc(r.article)}</p><h3>${esc(r.name)}</h3><p>${esc(r.entity_name)}</p><strong class="decision-number ${r.millions<0?'negative':''}">${money(r.millions)}</strong><p><a href="${esc(a.source_path)}#page=${r.page}" target="_blank" rel="noopener">Anexo · página ${r.page} ↗</a></p>${b?`<p class="note">Cambio neto del programa al 15/09: ${money(b.net)}. Las cinco normas documentan ${money(b.documented)}.${Math.abs(b.residual)>.00001?` Quedan ${money(b.residual)} de diferencia por conciliar con otras reasignaciones.`:' Coinciden dentro de la precisión del registro.'}</p>`:'<p class="note">El anexo identifica este código, pero el registro de ejecución al 15/09 no conserva la misma apertura. No se asigna a otro programa.</p>'}</article>`;}).join('')||'<p>No hay coincidencias.</p>';
    $('act-more').hidden=limit>=rows.length;
  }
  fetch('data/acts.json?v=20260918',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('No se pudieron cargar los anexos.');return r.json();}).then(d=>{
    D=d;$('normas').innerHTML=`<p class="eyebrow">Gestión 2026 / Normas y partidas</p><h2 tabindex="-1">Qué modificó cada norma</h2><p>Los cinco anexos oficiales explican el cambio total de ${money(d.reconciliation.documented_net)}. Este detalle permite separar la modificación de una norma del cambio neto que terminó teniendo cada programa.</p><div class="scenario-fields"><label>Norma<select id="act-select">${d.acts.map(a=>`<option value="${a.id}">${esc(a.title)}</option>`).join('')}</select></label><label>Buscar programa u organismo<input id="act-search" type="search" placeholder="Salud, energía, SAF o programa"></label></div><div id="act-summary"></div><p id="act-count" role="status"></p><div id="act-list"></div><button class="button button-quiet" id="act-more">Ver más partidas</button><div class="decision-links"><a href="#modificaciones">Volver al cambio neto por área →</a><a href="data/acts.json" download>Descargar detalle y conciliación ↓</a></div><p class="note">Importes extraídos de los anexos en pesos y convertidos a millones. Se excluyen aplicaciones financieras y subtotales repetidos. Los movimientos internos pueden compensarse en el total y aun así cambiar programas.</p>`;
    $('act-select').value=act;$('act-select').addEventListener('change',e=>{act=e.target.value;limit=12;listing();});$('act-search').addEventListener('input',e=>{query=e.target.value;limit=12;listing();});$('act-more').addEventListener('click',()=>{limit+=12;listing();});listing();
  }).catch(e=>{$('normas').innerHTML=`<p role="alert">${esc(e.message)}</p>`;});
})();

(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.NationClaims=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const kinds={reclamo:'Reclamo provincial',acuerdo:'Acuerdo de pago',anticipo:'Anticipo acordado',credito_compensable:'Crédito para compensar',pago:'Cobro informado',sin_monto:'Documento sin monto'};
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const date=value=>value?value.split('-').reverse().join('/'):'No informada';
  const number=value=>new Intl.NumberFormat('es-AR',{maximumFractionDigits:3}).format(value);
  function money(amount){
    if(!amount||!Number.isFinite(amount.value))return 'Monto no publicado';
    const scale=amount.value>=1e12?1e12:amount.value>=1e9?1e9:1e6;
    const unit=scale===1e12?'billones':scale===1e9?'mil millones':'millones';
    const currency=amount.currency==='USD'?'USD ':'$';
    const quantity=amount.qualifier==='rango'?`${number(amount.value/scale)} a ${number(amount.upper/scale)}`:number(amount.value/scale);
    const rounded=amount.qualifier==='exacto'&&Number((amount.value/scale).toFixed(3))!==amount.value/scale;
    return `${amount.qualifier==='mas_de'?'Más de ':amount.qualifier==='aproximado'||rounded?'≈ ':''}${currency}${quantity} ${unit}`;
  }
  function sourceLink(source){
    if(!source||!/^https:\/\//.test(source.url||''))return '';
    return `<a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title||'Ver documento oficial')} ↗</a>`;
  }
  function summaryModel(data,province){
    const item=data?.schema_version===2?data.provinces?.[province]:null;
    const records=[...(item?.records||[])].sort((a,b)=>(b.published_at||'').localeCompare(a.published_at||''));
    const claim=records.find(r=>r.kind==='reclamo'&&r.amount);
    const reference=claim||records.find(r=>r.amount)||records[0];
    if(claim)return {
      state:'claim',title:'Deuda de Nación',value:money(claim.amount),recordId:claim.id,
      context:claim.summary_context||claim.title,
      publishedAt:claim.published_at,attribution:'Según la Provincia',link:'Ver detalle',
    };
    return {
      state:reference?.amount?'reference':'missing',title:'Deuda de Nación',value:'Sin monto total',recordId:reference?.id||null,
      context:reference?.amount?(reference.summary_context||`${kinds[reference.kind]}: ${money(reference.amount)}${reference.period?' · '+reference.period:''}.`):(reference?reference.title:'Sin documentación oficial incorporada.'),
      publishedAt:reference?.published_at||null,attribution:'Documento oficial',link:'Ver detalle',
    };
  }
  function summaryHTML(data,province){
    const model=summaryModel(data,province);
    return `<div class="k-lbl" id="summaryNationTitle">${esc(model.title)}</div>
      <div class="summary-nation-value ${model.state==='claim'?'has-claim':'is-pending'}" data-claim-state="${model.state}">${esc(model.value)}</div>
      <p class="pulse-reading">${esc(model.context)}</p>
      ${model.publishedAt?`<div class="pulse-tag">${esc(model.attribution)} · ${esc(date(model.publishedAt))}</div>`:''}
      <button type="button" class="summary-detail-link" data-editorial-view="federal" data-summary-claim-link>${esc(model.link)} <span aria-hidden="true">→</span></button>`;
  }
  function recordHTML(record){
    const components=(record.components||[]).map(part=>`<div class="nation-claim-part"><div><h4>${esc(part.label)}</h4><p>${esc(part.explanation)}</p></div><strong>${esc(money({value:part.value,currency:record.amount.currency,qualifier:'aproximado'}))}</strong></div>`).join('');
    return `<article class="claim-card nation-claim-record" data-claim-id="${esc(record.id)}" data-claim-kind="${esc(record.kind)}">
      <div class="nation-claim-meta"><span class="nation-claim-kind">${esc(kinds[record.kind]||record.kind)}</span><span>Publicado: ${esc(date(record.published_at))}</span></div>
      <h3>${esc(record.title)}</h3>
      <div class="nation-claim-value">${esc(money(record.amount))}</div>
      ${record.period?`<p class="nation-claim-period">${esc(record.period)}</p>`:''}
      <p>${esc(record.explanation)}</p>
      ${components?`<div class="nation-claim-parts" aria-label="Componentes incluidos en el total">${components}</div>`:''}
      <p class="nation-claim-document">${esc(record.source.institution)} · ${sourceLink(record.source)}</p>
      ${record.valuation_date?`<p class="nation-claim-date">Valuación: ${esc(date(record.valuation_date))}.</p>`:''}
    </article>`;
  }
  function render(data,province,managementReading){
    const item=data?.schema_version===2?data.provinces?.[province]:null;
    if(!item)return '<div class="claim-card"><p>No se pudo cargar la documentación.</p></div>';
    const count=data.coverage;
    const overview=Object.entries(data.provinces).map(([name,row])=>{
      const status=row.coverage==='con_montos_publicados'?'Montos publicados':row.coverage==='documento_sin_monto'?'Documento sin monto':'Falta documentación';
      return `<button type="button" class="nation-claim-province" data-claim-province="${esc(name)}" aria-pressed="${name===province}"><strong>${esc(name)}</strong><span>${esc(status)}</span></button>`;
    }).join('');
    const records=item.records.length?item.records.map(recordHTML).join(''):'<article class="claim-card"><h3>Sin monto oficial incorporado</h3><p>La cuantificación está pendiente de documentación.</p></article>';
    return `<h2 class="sh sh-gold">Deuda de Nación con ${esc(province)}</h2>
      <div class="nation-claim-records">${records}</div>
      ${item.reading?`<div class="claim-card nation-claim-context"><h3>Para entender la cifra</h3><p>${esc(item.reading)}</p>${(item.context_sources||[]).map(s=>`<p>${sourceLink(s)}</p>`).join('')}</div>`:''}
      <div class="claim-card nation-claim-reading"><h3>Qué implica para la gestión</h3><p>${esc(managementReading)}</p></div>
      <p class="nation-claim-method">Importes en la moneda y fecha del documento. Reclamos, acuerdos y cobros se presentan por separado. Un billón equivale a un millón de millones.</p>
      <div class="claim-card nation-claim-overview"><h3>Consultar otra provincia</h3><p>${count.with_amounts} jurisdicciones con montos · ${count.documents_without_amounts} con documentos sin monto · ${count.pending_documentation} pendientes. Revisión: ${esc(date(data.reviewed_at))}.</p><div class="nation-claim-provinces">${overview}</div></div>`;
  }
  return {money,render,recordHTML,esc,summaryModel,summaryHTML};
});

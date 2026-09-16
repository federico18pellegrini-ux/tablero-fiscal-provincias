(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.NationClaims=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const kinds={reclamo:'Reclamo provincial',acuerdo:'Acuerdo de pago',anticipo:'Anticipo acordado',credito_compensable:'Crédito para compensar',pago:'Cobro informado',sin_monto:'Documento sin monto'};
  const summaryTitles={reclamo:'Deuda de Nación',acuerdo:'Acuerdo de pago con Nación',anticipo:'Anticipos acordados con Nación',credito_compensable:'Crédito para compensar con Nación',pago:'Cobros de Nación',sin_monto:'Deuda de Nación'};
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
    const base={title:'Deuda de Nación',hasAmount:false,valueSuffix:'',kind:null,tone:'neutral',recordId:null,publishedAt:null,attribution:'Documento oficial',link:'Ver detalle'};
    if(!item)return {...base,state:'unavailable',value:'Datos no disponibles',context:'No se pudo cargar el registro.'};
    const records=[...(item?.records||[])].sort((a,b)=>(b.published_at||'').localeCompare(a.published_at||''));
    const claim=records.find(r=>r.kind==='reclamo'&&r.amount);
    const reference=claim||records.find(r=>r.amount)||records[0];
    if(!reference)return {...base,state:'missing',value:'Sin dato documentado',context:'Documentación pendiente de incorporar.'};
    return {
      ...base,state:claim?'claim':reference.amount?'reference':'missing',kind:reference.kind,
      title:reference.summary_title||summaryTitles[reference.kind],hasAmount:!!reference.amount,
      value:reference.amount?money(reference.amount):'Monto no publicado',
      valueSuffix:reference.amount_basis==='mensual'?'por mes':'',
      tone:reference.amount?(claim?'negative':reference.kind==='pago'?'positive':'informative'):'neutral',
      recordId:reference.id,context:reference.summary_context||reference.period||reference.title,
      publishedAt:reference.published_at,attribution:claim?'Según la Provincia':'Documento oficial',
    };
  }
  function summaryHTML(data,province){
    const model=summaryModel(data,province);
    return `<div class="k-lbl" id="summaryNationTitle">${esc(model.title)}</div>
      <div class="summary-nation-value ${model.hasAmount?'has-amount':'is-pending'}" data-claim-state="${model.state}" data-tone="${model.tone}">${esc(model.value)}${model.valueSuffix?` <span class="summary-nation-unit">${esc(model.valueSuffix)}</span>`:''}</div>
      <p class="pulse-reading">${esc(model.context)}</p>
      ${model.publishedAt?`<div class="pulse-tag">${esc(model.attribution)} · ${esc(date(model.publishedAt))}</div>`:''}
      <button type="button" class="summary-detail-link" data-editorial-view="federal" data-summary-claim-link>${esc(model.link)} <span aria-hidden="true">→</span></button>`;
  }
  function recordHTML(record){
    const components=(record.components||[]).map(part=>`<div class="nation-claim-part"><div><h4>${esc(part.label)}</h4></div><strong>${esc(money({value:part.value,currency:record.amount.currency,qualifier:'aproximado'}))}</strong></div>`).join('');
    return `<article class="claim-card nation-claim-record" data-claim-id="${esc(record.id)}" data-claim-kind="${esc(record.kind)}">
      <div class="nation-claim-meta"><span class="nation-claim-kind">${esc(kinds[record.kind]||record.kind)}</span><span>Publicado: ${esc(date(record.published_at))}</span></div>
      <h3>${esc(record.title)}</h3>
      <div class="nation-claim-value">${esc(money(record.amount))}${record.amount_basis==='mensual'?' <span class="nation-claim-unit">por mes</span>':''}</div>
      ${record.period?`<p class="nation-claim-period">${esc(record.period)}</p>`:''}
      ${components?'':`<p>${esc(record.explanation)}</p>`}
      ${components?`<div class="nation-claim-parts" aria-label="Componentes incluidos en el total">${components}</div>`:''}
      <p class="nation-claim-document">${esc(record.source.institution)} · ${sourceLink(record.source)}</p>
      ${record.valuation_date?`<p class="nation-claim-date">Valuación: ${esc(date(record.valuation_date))}.</p>`:''}
    </article>`;
  }
  function render(data,province){
    const item=data?.schema_version===2?data.provinces?.[province]:null;
    if(!item)return '<div class="claim-card"><p>No se pudo cargar la documentación.</p></div>';
    const records=item.records.length?item.records.map(recordHTML).join(''):'<article class="claim-card"><h3>Sin monto oficial incorporado</h3><p>La cuantificación está pendiente de documentación.</p></article>';
    return `<h2 class="sh sh-gold">${esc(summaryModel(data,province).title)} · ${esc(province)}</h2>
      <div class="nation-claim-records">${records}</div>
      <p class="nation-claim-method">Un billón equivale a un millón de millones. Los reclamos, acuerdos y cobros conservan el alcance del documento.</p>`;
  }
  return {money,render,recordHTML,esc,summaryModel,summaryHTML};
});

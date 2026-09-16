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
  function recordHTML(record){
    const components=(record.components||[]).map(part=>`<div class="nation-claim-part"><div><h4>${esc(part.label)}</h4><p>${esc(part.explanation)}</p></div><strong>${esc(money({value:part.value,currency:record.amount.currency,qualifier:'aproximado'}))}</strong></div>`).join('');
    return `<article class="claim-card nation-claim-record" data-claim-id="${esc(record.id)}">
      <div class="nation-claim-meta"><span class="nation-claim-kind">${esc(kinds[record.kind]||record.kind)}</span><span>Publicado: ${esc(date(record.published_at))}</span></div>
      <h3>${esc(record.title)}</h3>
      <div class="nation-claim-value">${esc(money(record.amount))}</div>
      ${record.period?`<p class="nation-claim-period">${esc(record.period)}</p>`:''}
      <p>${esc(record.explanation)}</p>
      ${components?`<div class="nation-claim-parts" aria-label="Componentes incluidos en el total">${components}</div>`:''}
      <p class="nation-claim-document">${esc(record.source.institution)} · ${sourceLink(record.source)}</p>
      <p class="nation-claim-date">${record.valuation_date?`Monto valuado al ${esc(date(record.valuation_date))}.`:'La fecha de publicación no equivale a una fecha de valuación común.'}</p>
    </article>`;
  }
  function render(data,province,managementReading){
    const item=data?.schema_version===2?data.provinces?.[province]:null;
    if(!item)return '<div class="claim-card"><p>No se pudo cargar la documentación de reclamos. No se interpreta como deuda cero.</p></div>';
    const count=data.coverage;
    const overview=Object.entries(data.provinces).map(([name,row])=>{
      const status=row.coverage==='con_montos_publicados'?'Montos publicados':row.coverage==='documento_sin_monto'?'Documento sin monto':'Falta documentación';
      return `<button type="button" class="nation-claim-province" data-claim-province="${esc(name)}" aria-pressed="${name===province}"><strong>${esc(name)}</strong><span>${esc(status)}</span></button>`;
    }).join('');
    const records=item.records.length?item.records.map(recordHTML).join(''):'<article class="claim-card"><h3>Importe pendiente de documentar</h3><p>No hay un monto oficial incorporado para esta jurisdicción. Eso no significa que Nación no le deba: falta el respaldo para cuantificarlo.</p></article>';
    return `<h2 class="sh sh-gold">Qué le reclama ${esc(province)} a Nación</h2>
      <p class="nation-claim-intro">Un monto reclamado es lo que la provincia sostiene que le corresponde. Para saber cuánto queda por cobrar, también hay que verificar qué reconoce Nación, cómo se acordó pagarlo y cuánto se pagó.</p>
      <div class="nation-claim-records">${records}</div>
      ${item.reading?`<div class="claim-card nation-claim-context"><h3>Para entender la cifra</h3><p>${esc(item.reading)}</p>${(item.context_sources||[]).map(s=>`<p>${sourceLink(s)}</p>`).join('')}</div>`:''}
      <div class="claim-card nation-claim-reading"><h3>Qué implica para la gestión</h3><p>${esc(managementReading)}</p><h4>Qué falta verificar en ${esc(province)}</h4><p>${esc(item.pending)}</p></div>
      <div class="claim-card nation-claim-method"><h3>Cómo leer estos montos</h3><p><strong>Saldo total pendiente de cobro: no verificado.</strong> Los importes conservan la moneda y la fecha de cada publicación. No se ajustan por inflación ni cambian con el selector general de unidades. Un billón equivale a un millón de millones de pesos.</p><p>Los reclamos, acuerdos y cobros se muestran por separado: no se suman ni se restan automáticamente. Las obras y los programas reclamados tampoco equivalen necesariamente a efectivo disponible. Por esas diferencias, no armamos un ranking ni un total nacional.</p></div>
      <div class="claim-card nation-claim-overview"><h3>Consultar otra provincia</h3><p>Revisión documental: ${esc(date(data.reviewed_at))}. ${count.with_amounts} jurisdicciones con montos publicados · ${count.documents_without_amounts} con documentos sin monto · ${count.pending_documentation} pendientes de documentación. Los montos pueden corresponder a reclamos o acuerdos de distintas fechas; no son saldos actuales comparables.</p><div class="nation-claim-provinces">${overview}</div></div>`;
  }
  return {money,render,recordHTML,esc};
});

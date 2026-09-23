(function(root){
  'use strict';
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const change=(a,b)=>finite(a)&&finite(b)&&b>0?(a/b-1)*100:null;
  const delta=(a,b)=>finite(a)&&finite(b)?a-b:null;
  const share=(a,total)=>finite(a)&&finite(total)&&total>0?a/total*100:null;
  const bases=['law','current','closing'];
  function comparisons(budget,management,mode='execution',base='closing'){
    if(!['execution','amendments','project'].includes(mode))throw new Error('Unknown comparison');
    if(!bases.includes(base))throw new Error('Unknown base');
    // Budget IDs are display IDs (global sequence), while PA function codes restart
    // inside each purpose. Join on the official name AND purpose, never the display ID.
    const actual=new Map(management.execution.functions_comparison.map(r=>[`${r.finalidad_id}|${r.funcion_desc_2026}`,r]));
    const factors=budget.deflator.annual_factors;
    let rows=budget.functions.map(r=>{
      const e=actual.get(`${r.purpose}|${r.name}`);
      let before,after;
      if(mode==='execution'){
        before=e?.credito_devengado_real_agosto2026_2025??null;
        after=e?.credito_devengado_real_agosto2026_2026??null;
      }else if(mode==='amendments'){
        before=r.law;after=r.current;
      }else{
        before=finite(r[base])&&finite(factors['2026'])?r[base]*factors['2026']:null;
        after=finite(r.project)&&finite(factors['2027'])?r.project*factors['2027']:null;
      }
      return {id:r.id,name:r.name,before,after,change:change(after,before),delta:delta(after,before)};
    });
    // Missing functions must never silently disappear from the denominator.
    const sum=key=>rows.every(r=>finite(r[key]))?rows.reduce((s,r)=>s+r[key],0):null;
    const before=sum('before'),after=sum('after');
    rows=rows.map(r=>({...r,shareBefore:share(r.before,before),shareAfter:share(r.after,after),shareChange:delta(share(r.after,after),share(r.before,before))}));
    return {rows,total:{before,after,change:change(after,before),delta:delta(after,before)}};
  }
  function ranked(rows,sort='cuts'){
    const key=sort==='percent'?'change':'delta',direction=sort==='increases'?-1:1;
    return [...rows].sort((a,b)=>!finite(a[key])?(!finite(b[key])?a.name.localeCompare(b.name):1):!finite(b[key])?-1:direction*(a[key]-b[key])||a.name.localeCompare(b.name));
  }
  function benefitChange(rows,start,end,key){
    const a=rows.find(r=>r.period===start),b=rows.find(r=>r.period===end);
    if(!a||!b||!finite(a[key])||!finite(b[key])||!finite(a.ipc)||!finite(b.ipc)||a.ipc<=0||b.ipc<=0)return null;
    return change(b[key]/b.ipc,a[key]/a.ipc);
  }
  function benefitIndex(rows,start,key){
    return rows.filter(r=>r.period>=start).map(r=>({period:r.period,value:benefitChange(rows,start,r.period,key)}))
      .map(r=>({...r,value:r.value===null?null:100+r.value}));
  }
  function shareReading(row,mode='execution'){
    if(!row||!finite(row.change)||!finite(row.shareChange))return '';
    const subject=mode==='project'?'El gasto propuesto':mode==='amendments'?'El crédito autorizado':'El gasto';
    const unit=mode==='amendments'?'en pesos corrientes':'en términos reales';
    if(row.change<=-.05&&row.shareChange>=.005)return `${subject} cae ${unit}, pero gana participación porque el total cae más.`;
    if(row.change>=.05&&row.shareChange<=-.005)return `${subject} sube ${unit}, pero pierde participación porque el total crece más.`;
    return '';
  }
  function interestComparison(model){
    const row=model.rows.find(r=>r.id==='5-29');
    if(!row)return null;
    const before=delta(model.total.before,row.before),after=delta(model.total.after,row.after);
    return {row,rest:{before,after,change:change(after,before)}};
  }
  function delivery(decisions,slug,id,unit){
    const policy=decisions?.policies?.find(p=>p.slug===slug);
    const rows=policy?.physical?.filter(r=>r.medicion_fisica_id===id&&r.unidad_medida_desc===unit&&r.ejercicio_presupuestario===2026&&r.trimestre===2)||[];
    if(rows.length!==1||rows[0].requiere_revision_clave||!finite(rows[0].ejecutado_acumulado_trim2))return null;
    const r=rows[0],comments=(r.causas||[]).map(c=>c.causa_desvio_comentario||'').join(' ');
    return {value:r.ejecutado_acumulado_trim2,average:r.totalizador_avance_fisico.startsWith('Promedio'),partial:/parcial|provisori|sujet[oa]s? a.*modific/i.test(comments)};
  }
  const api={finite,change,delta,share,comparisons,ranked,benefitChange,benefitIndex,shareReading,interestComparison,delivery};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalPriorities=api;
})(typeof globalThis!=='undefined'?globalThis:this);

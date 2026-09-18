(function(root){
  'use strict';
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const ratio=(a,b)=>finite(a)&&finite(b)&&b>0?a/b*100:null;
  function physicalValue(r){
    const planned=r.programacion_acumulada_trim2,actual=r.ejecutado_acumulado_trim2;
    const comments=r.causas.map(c=>c.causa_desvio_comentario).filter(c=>c&&c.trim()!=='-');
    const partial=comments.some(c=>/parcial|provisori|sujet[oa]s? a.*modific/i.test(c));
    const percent=ratio(actual,planned);
    return {planned,actual,percent,change:percent===null?null:percent-100,partial,comments};
  }
  function inputMatches(d,hash){return !!hash&&d?.meta?.inputs?.['nacion/data/budget.json']===hash;}
  function policyStats(p){
    const rows=p.physical.map(physicalValue);
    return {count:rows.length,reported:rows.filter(r=>finite(r.actual)).length,
      comparable:rows.filter(r=>r.percent!==null).length,partial:rows.filter(r=>r.partial).length,
      execution:ratio(p.execution.credito_devengado,p.execution.credito_vigente),
      unpaid:p.execution.credito_devengado-p.execution.credito_pagado};
  }
  const api={physicalValue,policyStats,inputMatches};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalDecisionMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);

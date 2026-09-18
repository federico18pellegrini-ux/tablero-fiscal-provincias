(function(root){
  'use strict';
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const ratio=(a,b)=>finite(a)&&finite(b)&&b>0?a/b*100:null;
  const change=(a,b)=>{const r=ratio(a,b);return r===null?null:r-100;};
  const cashValue=(r,year,price)=>r[price==='real'?`enero_julio_real_${year}`:`enero_julio_${year}`]??null;
  const metaValues=(r,quarter)=>({planned:r[`programacion_acumulada_trim${quarter}`]??null,actual:r[`ejecutado_acumulado_trim${quarter}`]??null,annual:r[`programacion_anual_vig_trim${quarter}`]??null,method:r.totalizador_avance_fisico});
  const metaStatus=(r,quarter)=>{
    const v=metaValues(r,quarter);
    if(!finite(v.actual))return {key:'missing',label:'Sin dato de realización',deviation:null};
    if(!finite(v.planned)||v.planned<=0)return {key:'uncomparable',label:'Sin base positiva para comparar',deviation:null};
    const deviation=change(v.actual,v.planned);
    return {key:v.actual<v.planned?'below':v.actual>v.planned?'above':'equal',label:v.actual<v.planned?'Por debajo de lo previsto':v.actual>v.planned?'Por encima de lo previsto':'Igual a lo previsto',deviation};
  };
  const historyValue=(r,key,price)=>!finite(r[key])?null:price==='real'?(finite(r.factor_real_anual)?r[key]*r.factor_real_anual:null):r[key];
  const rankProvinces=(rows,key)=>[...rows].filter(r=>finite(r[key])).sort((a,b)=>b[key]-a[key]||a.provincia.localeCompare(b.provincia,'es')).map((r,i,all)=>({...r,rank:i>0&&r[key]===all[i-1][key]?all.findIndex(x=>x[key]===r[key])+1:i+1}));
  // Zero is data; a missing series cannot become a fiscal saving or a completed goal.
  const sum=(rows,key)=>rows.length&&rows.every(r=>finite(r[key]))?rows.reduce((a,r)=>a+r[key],0):null;
  const delta=(a,b)=>finite(a)&&finite(b)?a-b:null;
  const modifications=rows=>rows.map(r=>({...r,modification:delta(r.credito_vigente,r.credito_presupuestado),modification_pct:change(r.credito_vigente,r.credito_presupuestado)}));
  const modificationBalance=rows=>{
    const values=modifications(rows).map(r=>r.modification);
    if(!values.length||values.some(v=>!finite(v)))return null;
    const increases=values.filter(v=>v>0).reduce((a,b)=>a+b,0),reductions=values.filter(v=>v<0).reduce((a,b)=>a+b,0);
    return {increases,reductions,net:increases+reductions};
  };
  // PA uses INDEC jurisdiction codes; the project's row IDs are not those codes.
  // Link its already-normalized names exactly, never by numeric row or fuzzy match.
  const territory=(budget,management,id)=>{
    if(!budget||!management||!Number.isInteger(id))return null;
    const candidates=management.provinces.comparison.filter(r=>r.provincia_id===id);
    if(candidates.length!==1)return null;
    const province=candidates[0],geos=budget.geographies.filter(r=>r.name===province.provincia),observed=management.execution.groups.territorio.filter(r=>r.ubicacion_geografica_id===id);
    if(geos.length!==1||observed.length!==1)return null;
    const works=budget.works.filter(r=>r.province===province.provincia).sort((a,b)=>b.project-a.project||a.id.localeCompare(b.id));
    return {province,project:geos[0],observed:observed[0],works,worksTotal:works.length?sum(works,'project'):0,pending:delta(province.presupuestarias_devengado,province.presupuestarias_pagado)};
  };
  const api={finite,ratio,change,cashValue,metaValues,metaStatus,historyValue,rankProvinces,sum,delta,modifications,modificationBalance,territory};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalManagementMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);

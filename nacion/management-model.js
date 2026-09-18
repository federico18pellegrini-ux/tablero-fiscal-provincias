(function(root){
  'use strict';
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const ratio=(a,b)=>finite(a)&&finite(b)&&b>0?a/b*100:null;
  const change=(a,b)=>{const r=ratio(a,b);return r===null?null:r-100;};
  const cashValue=(r,year,price)=>r[price==='real'?`enero_julio_real_${year}`:`enero_julio_${year}`]??null;
  const metaValues=(r,quarter)=>({planned:r[`programacion_acumulada_trim${quarter}`]??null,actual:r[`ejecutado_acumulado_trim${quarter}`]??null,annual:r[`programacion_anual_vig_trim${quarter}`]??null,method:r.totalizador_avance_fisico});
  const historyValue=(r,key,price)=>!finite(r[key])?null:price==='real'?(finite(r.factor_real_anual)?r[key]*r.factor_real_anual:null):r[key];
  const rankProvinces=(rows,key)=>[...rows].filter(r=>finite(r[key])).sort((a,b)=>b[key]-a[key]||a.provincia.localeCompare(b.provincia,'es')).map((r,i,all)=>({...r,rank:i>0&&r[key]===all[i-1][key]?all.findIndex(x=>x[key]===r[key])+1:i+1}));
  // Zero is data; a missing series cannot become a fiscal saving or a completed goal.
  const sum=(rows,key)=>rows.length&&rows.every(r=>finite(r[key]))?rows.reduce((a,r)=>a+r[key],0):null;
  const api={finite,ratio,change,cashValue,metaValues,historyValue,rankProvinces,sum};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalManagementMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);

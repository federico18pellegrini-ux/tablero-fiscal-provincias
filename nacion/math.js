(function(root){
  'use strict';
  const finite = v => typeof v === 'number' && Number.isFinite(v);
  const ratio = (a,b) => finite(a) && finite(b) && b > 0 ? a/b*100 : null;
  const change = (a,b) => {const r=ratio(a,b);return r===null?null:r-100;};
  const price = (v,year,mode,factors) => !finite(v)?null:mode==='real'?(finite(factors[String(year)])?v*factors[String(year)]:null):v;
  const delta = (a,b) => finite(a)&&finite(b)?a-b:null;
  const shareChange = (a,at,b,bt) => delta(ratio(a,at),ratio(b,bt));
  const cumulative = rows => {let sum=0;return rows.map(r=>({...r,cumulative:sum+=r.accrued}));};
  const csvCell = v => '"'+String(v??'').replace(/"/g,'""')+'"';
  const searchText = p => {
    let text=[p.name,p.jurisdiction,p.entity].join(' ');
    if(/Educación Superior/i.test(p.name))text+=' universidades universitario';
    if(/Administración Nacional de la Seguridad Social/i.test(p.entity))text+=' ANSES';
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  };
  const api={finite,ratio,change,price,delta,shareChange,cumulative,csvCell,searchText};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.BudgetMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);

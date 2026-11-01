(function(root){
  'use strict';
  const valid=v=>typeof v==='number'&&Number.isFinite(v);
  function customsCost(investment,importShare,incrementalShare,tariff){
    const fractions=[importShare,incrementalShare,tariff];
    if(!valid(investment)||investment<0||fractions.some(v=>!valid(v)||v<0||v>1))return null;
    return investment*importShare*incrementalShare*tariff;
  }
  const api={customsCost};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RigiModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);

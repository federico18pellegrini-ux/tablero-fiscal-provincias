(function(root){
  'use strict';
  function selectReport(manifest, options, dataHash, managementHash,decisionHash){
    const {price,base,annex=false,scope='general',provinceId}=options;
    if(!['nominal','real'].includes(price)||!['current','law','closing'].includes(base))throw Error('Elegí una unidad y una base de comparación válidas.');
    if(!dataHash||manifest?.inputs?.['nacion/data/budget.json']!==dataHash||!managementHash||manifest?.inputs?.['nacion/data/gestion.json']!==managementHash)throw Error('Los informes se están actualizando. Recargá el tablero para descargar la versión que coincide con estos datos.');
    if(!decisionHash||manifest?.inputs?.['nacion/data/decisions.json']!==decisionHash)throw Error('Las fichas se están actualizando. Recargá el tablero para descargar el informe actualizado.');
    if(!['general','inmunizaciones','educacion-superior','reactor-ra10','provincia'].includes(scope))throw Error('Seleccioná un contenido válido.');
    if(scope==='provincia'&&(!Number.isInteger(provinceId)||!manifest.territories?.some(p=>p.province_id===provinceId)))throw Error('Seleccioná una provincia válida.');
    const entry=manifest.reports?.find(r=>r.price===price&&r.base===base),pdf=scope==='general'?entry?.[annex?'full':'main']:scope==='provincia'?manifest.territories.find(p=>p.province_id===provinceId):manifest.focused?.find(r=>r.scope===scope);
    const expected=scope==='general'?`informe-nacional-${price}-${base}${annex?'-anexo':''}.pdf`:`ficha-nacional-${scope==='provincia'?'provincia-'+provinceId:scope}.pdf`;
    if(!pdf||pdf.file!==expected||!Number.isInteger(pdf.pages)||pdf.pages<1||pdf.pages>200||!/^[a-f0-9]{64}$/.test(pdf.sha256))throw Error('No se pudo validar este informe. Volvé a intentarlo.');
    return {...pdf,href:'reports/'+expected+'?v='+pdf.sha256.slice(0,16)};
  }
  const api={selectReport};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalReport=api;
})(typeof globalThis!=='undefined'?globalThis:this);

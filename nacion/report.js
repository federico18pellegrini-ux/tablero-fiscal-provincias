(function(root){
  'use strict';
  function selectReport(manifest, options, dataHash){
    const {price,base,annex=false}=options;
    if(!['nominal','real'].includes(price)||!['current','law','closing'].includes(base))throw Error('Elegí una unidad y una base de comparación válidas.');
    if(!dataHash||manifest?.inputs?.['nacion/data/budget.json']!==dataHash)throw Error('Los informes se están actualizando. Recargá el tablero para descargar la versión que coincide con estos datos.');
    const entry=manifest.reports?.find(r=>r.price===price&&r.base===base),pdf=entry?.[annex?'full':'main'];
    const expected=`informe-nacional-${price}-${base}${annex?'-anexo':''}.pdf`;
    if(!pdf||pdf.file!==expected||!Number.isInteger(pdf.pages)||pdf.pages<1||pdf.pages>200||!/^[a-f0-9]{64}$/.test(pdf.sha256))throw Error('No se pudo validar este informe. Volvé a intentarlo.');
    return {...pdf,href:'reports/'+expected+'?v='+pdf.sha256.slice(0,16)};
  }
  const api={selectReport};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalReport=api;
})(typeof globalThis!=='undefined'?globalThis:this);

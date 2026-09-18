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
  const fold = s => String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const searchAliases = p => {
    const name=fold(p.name), aliases=[];
    for(const [pattern,words] of [
      [/inmunoprevenibles/,'vacunas vacunacion inmunizaciones'],
      [/educacion superior/,'universidades universidad universitario universitarios'],
      [/prestaciones previsionales/,'jubilaciones jubilados jubilacion'],
      [/pensiones no contributivas/,'pensiones pension discapacidad'],
      [/asignaciones familiares/,'auh asignacion universal hijo asignaciones'],
      [/politicas alimentarias/,'alimentos comedores tarjeta alimentar'],
      [/construccion.*rutas|mantenimiento.*rutas|conservacion.*rutas/,'rutas caminos vialidad'],
      [/medicamentos/,'remedios']
    ])if(pattern.test(name))aliases.push(words);
    if(/administracion nacional de la seguridad social/.test(fold(p.entity)))aliases.push('anses');
    return aliases.join(' ');
  };
  const searchText = p => fold([p.name,p.jurisdiction,p.entity,searchAliases(p)].join(' '));
  const matchesSearch = (p,q) => fold(q).trim().split(/\s+/).every(word=>searchText(p).includes(word));
  const comparisonRows = (row,factors) => ['law','current','closing'].map(base=>({base,
    nominal:change(row.project,row[base]),real:change(price(row.project,2027,'real',factors),price(row[base],2026,'real',factors))}));
  const anchorPages = Object.freeze({inicio:'panorama',escala:'panorama',historia:'panorama',distribucion:'gasto',comparacion:'gasto',cambios:'gasto',programas:'gasto',finalidades:'gasto',obras:'obras',recursos:'economia',macro:'economia',financiamiento:'economia',escenarios:'economia','obra-ra10':'obra-ficha','politica-inmunizaciones':'politicas','politica-educacion-superior':'politicas',ejecucion:'ejecucion',modificaciones:'ejecucion',caja:'ejecucion','deuda-nacional':'ejecucion','provincias-nacion':'ejecucion',metas:'ejecucion','obras-ejecucion':'ejecucion','historia-ejecucion':'ejecucion',metodo:'metodo'});
  const pageForAnchor = anchor => Object.hasOwn(anchorPages,anchor)?anchorPages[anchor]:'panorama';
  const budgetOverview = (total,base,factors) => ({
    nominalChange:change(total.project,total[base]),
    realChange:change(price(total.project,2027,'real',factors),price(total[base],2026,'real',factors)),
    execution:ratio(total.accrued,total.current)
  });
  const api={finite,ratio,change,price,delta,shareChange,cumulative,csvCell,fold,searchText,searchAliases,matchesSearch,comparisonRows,pageForAnchor,budgetOverview};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.BudgetMath=api;
})(typeof globalThis!=='undefined'?globalThis:this);

(function(root){
  'use strict';
  const sections=[
    {id:'resumen',label:'Resumen',anchor:'inicio',title:'Resumen nacional',views:[{id:'overview',label:'Resumen',anchor:'inicio',roots:['inicio','escala','historia']}]},
    {id:'presupuesto',label:'Presupuesto',anchor:'distribucion',title:'Presupuesto 2027',views:[
      {id:'distribution',label:'Comparar áreas',anchor:'distribucion',roots:['distribucion','comparacion','cambios']},
      {id:'programs',label:'Programas',anchor:'programas',roots:['programas','politica-jubilaciones','politica-alimentacion','politica-medicamentos','politica-seguridad-federal','politica-inmunizaciones','politica-educacion-superior']},
      {id:'portfolios',label:'Ministerios y poderes',anchor:'carteras',roots:['carteras']},
      {id:'purposes',label:'Composición',anchor:'finalidades',roots:['finalidades']}]},
    {id:'ejecucion',label:'Ejecución',anchor:'ejecucion',title:'Ejecución 2026',views:[
      {id:'spending',label:'Gasto y caja',anchor:'ejecucion',roots:['ejecucion','caja']},
      {id:'changes',label:'Cambios y normas',anchor:'modificaciones',roots:['modificaciones','normas']},
      {id:'benefits',label:'Prestaciones',anchor:'priority-income',roots:['household-benefits','metas']},
      {id:'delivery',label:'Obras e historia',anchor:'obras-ejecucion',roots:['obras-ejecucion','historia-ejecucion']}]},
    {id:'territorio',label:'Territorio',anchor:'obras',title:'Nación en el territorio',views:[
      {id:'works',label:'Obras y mapa',anchor:'obras',roots:['obras','obra-ra10']},
      {id:'provinces',label:'Recursos por provincia',anchor:'provincias-nacion',roots:['provincias-nacion']},
      {id:'geography',label:'Ubicación del gasto',anchor:'geografia',roots:['geografia']}]},
    {id:'finanzas',label:'Ingresos y deuda',anchor:'recursos',title:'Ingresos y deuda',views:[
      {id:'income',label:'Ingresos',anchor:'recursos',roots:['recursos']},
      {id:'financing',label:'Deuda y financiamiento',anchor:'financiamiento',roots:['financiamiento','deuda-nacional']},
      {id:'tax',label:'Gasto tributario y RIGI',anchor:'gasto-tributario',roots:['gasto-tributario']},
      {id:'scenario',label:'Supuestos y escenarios',anchor:'macro',roots:['macro','escenarios']},
      {id:'sources',label:'Fuentes y método',anchor:'metodo',roots:['metodo'],auxiliary:true}]}];
  const routes=Object.create(null);
  for(const section of sections)for(const view of section.views)for(const anchor of view.roots)routes[anchor]={section:section.id,view:view.id};
  Object.assign(routes,{
    prioridades:{section:'ejecucion',view:'spending'},
    'priority-comparison':{section:'ejecucion',view:'spending'},
    'priority-interest':{section:'ejecucion',view:'spending'},
    'priority-next':{section:'ejecucion',view:'spending'},
    'priority-income':{section:'ejecucion',view:'benefits'},
    'prioridades-2027':{section:'presupuesto',view:'distribution'},
    'tax-rigi':{section:'finanzas',view:'tax'},
    'rigi-estimation':{section:'finanzas',view:'tax'},
    territorio:{section:'territorio',view:'works'},
    presupuesto:{section:'presupuesto',view:'distribution'},
    ingresos:{section:'finanzas',view:'income'}
  });
  const resolve=anchor=>Object.hasOwn(routes,anchor)?{...routes[anchor]}:{section:'resumen',view:'overview'};
  const viewFor=anchor=>{const r=resolve(anchor);return sections.find(s=>s.id===r.section).views.find(v=>v.id===r.view);};
  const api={sections,routes,resolve,viewFor};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalNavigationModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);

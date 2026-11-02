/* Move the existing, independently sourced modules. No figures are copied here. */
(()=>{
  'use strict';
  const M=window.NationalNavigationModel,$=id=>document.getElementById(id),dashboard=$('dashboard');
  const oldPages=[...dashboard.querySelectorAll('[data-page]')];
  const originalIds=[...dashboard.querySelectorAll('[id]')].map(e=>e.id);
  const pages=new Map(),views=new Map(),rootIds=new Set();
  let routing=false,active=null,lastView='';
  const create=(tag,attrs={})=>Object.assign(document.createElement(tag),attrs);
  const households=create('section',{id:'household-benefits',className:'chapter'});
  dashboard.append(households);
  const geography=$('geografia')||create('section',{id:'geografia',className:'chapter'});
  geography.innerHTML='<p class="eyebrow">Territorio / Proyecto 2027</p><h2 tabindex="-1">Dónde se registra el gasto</h2><p>Incluye las 24 jurisdicciones y las ubicaciones nacional, interprovincial, binacional y exterior. No equivale a transferencias al gobierno provincial.</p><div id="geography-cards" class="budget-rows"></div>';
  dashboard.append(geography);
  for(const section of M.sections){
    const page=create('div',{className:'national-page',hidden:true});page.dataset.page=section.id;pages.set(section.id,page);dashboard.append(page);
    if(section.id!=='resumen'){
      const heading=create('header',{className:'national-section-heading'});
      heading.innerHTML=`<p class="eyebrow">Nación / ${section.label}</p><h1 tabindex="-1">${section.title}</h1>`;page.append(heading);
      const nav=create('nav',{className:'section-switch'});nav.setAttribute('aria-label','Explorar '+section.label.toLowerCase());
      for(const view of section.views.filter(v=>!v.auxiliary)){const a=create('a',{href:'#'+view.anchor,textContent:view.label});a.dataset.sectionView=view.id;nav.append(a);}page.append(nav);
    }
    for(const view of section.views){
      const box=create('div',{className:'national-view',hidden:true});box.dataset.nationalView=view.id;views.set(section.id+'/'+view.id,box);page.append(box);
      for(const id of view.roots){const node=$(id);if(!node)throw Error('Falta el bloque '+id);rootIds.add(id);box.append(node);}
    }
  }
  const fold=(id,label)=>{
    const node=$(id),details=create('details',{className:'section-detail'}),summary=create('summary',{textContent:label});
    node.before(details);details.append(summary,node);return details;
  };
  fold('comparacion','Comparación detallada entre las bases');
  fold('cambios','Mayores cambios en pesos por organismo, función o programa');
  fold('caja','Resultado de caja mes a mes');
  fold('normas','Normas y anexos oficiales');
  fold('historia-ejecucion','Historia completa desde 2007');
  fold('escenarios','Simular cambios en los supuestos');
  const fiscalFold=create('details',{className:'section-detail'}),fiscalSummary=create('summary',{textContent:'Lectura por función: gasto, intereses y prestaciones'});
  fiscalFold.append(fiscalSummary,$('prioridades'));views.get('ejecucion/spending').append(fiscalFold);
  const projectFold=create('details',{className:'section-detail'});projectFold.append(create('summary',{textContent:'Lectura del proyecto por función y prestaciones'}));views.get('presupuesto/distribution').append(projectFold);
  const status=$('management-status');if(status)views.get('ejecucion/spending').prepend(status);
  for(const old of oldPages){
    old.querySelectorAll('.section-nav,.management-nav').forEach(n=>n.remove());
    if(old.querySelector('[id]'))throw Error('Quedó un bloque sin asignar: '+old.querySelector('[id]').id);
    old.remove();
  }
  // Monthly detail is available, but does not repeat the execution headline by default.
  const monthly=create('details',{className:'monthly-execution section-detail'}),monthlySummary=create('summary',{textContent:'Ritmo mensual y detalle por organismo'});
  $('management-execution').after(monthly);monthly.append(monthlySummary);
  for(const node of [...$('ejecucion').children])if(node!==monthly&&node.id!=='management-execution')monthly.append(node);
  const missing=originalIds.filter(id=>!$(id));if(missing.length)throw Error('Se perdieron bloques: '+missing.join(', '));
  function moveHouseholds(){const node=$('priority-income');if(node&&node.parentElement!==households)households.replaceChildren(node);}
  function openParents(node){for(let p=node?.parentElement;p&&p!==dashboard;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}
  function updateHeading(){
    const heading=pages.get('presupuesto').querySelector('.national-section-heading h1');
    heading.textContent=active?.section==='presupuesto'&&active.view==='distribution'?$('distribution-title').textContent:'Presupuesto 2027';
    pages.get('presupuesto').querySelector('.national-section-heading .eyebrow').textContent='Nación / Presupuesto 2027';
  }
  function route(anchor=location.hash.slice(1)||'inicio'){
    if(routing)return; routing=true;
    try{
      const selected=M.resolve(anchor),view=M.viewFor(anchor);active={...selected,anchor};
      for(const [id,node] of pages)node.hidden=id!==selected.section;
      for(const [key,node] of views)node.hidden=key!==selected.section+'/'+selected.view;
      document.querySelectorAll('[data-page-link]').forEach(a=>{if(a.dataset.pageLink===selected.section)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
      for(const a of pages.get(selected.section).querySelectorAll('[data-section-view]')){if(a.dataset.sectionView===selected.view)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}
      document.body.dataset.nationalSection=selected.section;updateHeading();
      const priorityProject=anchor==='prioridades-2027';
      (priorityProject?projectFold:fiscalFold).append($('prioridades'));
      projectFold.hidden=!priorityProject&&selected.section!=='presupuesto';
      if(selected.section==='presupuesto'&&selected.view==='distribution'){
        projectFold.append($('prioridades'));
        window.NationalPrioritiesView?.setMode('project');
      }else if(selected.section==='ejecucion'&&selected.view==='spending'){
        const mode=new URLSearchParams(location.search).get('lectura');window.NationalPrioritiesView?.setMode(mode==='amendments'?'amendments':'execution');
      }
      moveHouseholds();
      for(const id of rootIds){const node=$(id);if(!node)continue;
        node.hidden=!view.roots.includes(id);
        if(id.startsWith('politica-'))node.hidden=id!==anchor;
        if(id==='programas'&&anchor.startsWith('politica-'))node.hidden=true;
        if(id==='obra-ra10')node.hidden=anchor!=='obra-ra10';
        if(id==='obras'&&anchor==='obra-ra10')node.hidden=true;
      }
      $('prioridades').hidden=false;
      if(anchor.startsWith('politica-')||anchor==='obra-ra10'){
        let back=views.get(selected.section+'/'+selected.view).querySelector('.detail-back');
        if(!back){back=create('a',{className:'detail-back'});views.get(selected.section+'/'+selected.view).prepend(back);}
        back.href=anchor==='obra-ra10'?'#obras':'#programas';back.textContent=anchor==='obra-ra10'?'← Volver a obras y mapa':'← Volver a programas';back.hidden=false;
      }else document.querySelectorAll('.detail-back').forEach(n=>n.hidden=true);
      window.NationalManagementView?.activate(view.roots,anchor);
      if(anchor==='prioridades'||anchor.startsWith('priority-')||priorityProject)openParents($(priorityProject?'prioridades':anchor));
      else if(!M.sections.some(s=>s.anchor===anchor))openParents($(anchor));
      lastView=selected.section+'/'+selected.view;
    }finally{routing=false;}
  }
  const isRootVisible=id=>{const node=$(id);return !!node&&!node.hidden&&!node.closest('.national-view')?.hidden&&!node.closest('.national-page')?.hidden;};
  window.NationalNavigation={route,updateHeading,refresh:()=>route(),moveHouseholds,isRootVisible,get active(){return active;},get lastView(){return lastView;}};
  window.addEventListener('national:priorities-rendered',moveHouseholds);
  route();
})();

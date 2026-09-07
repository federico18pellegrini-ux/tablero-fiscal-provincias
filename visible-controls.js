/* Visible controls delegate to the existing source controls; one state per choice. */
function initVisibleControls(){
 const selectors=['profileSelector','periodSelector','valueModeSelector'],groups=[];
 for(const id of selectors){
  const select=document.getElementById(id),group=document.createElement('div');group.className='choice-buttons';group.setAttribute('role','group');group.setAttribute('aria-label',select.closest('.command-field').querySelector('.ctrl-lbl').textContent);
  select.classList.add('control-source');select.setAttribute('aria-hidden','true');select.tabIndex=-1;
  for(const option of select.options){const button=document.createElement('button');button.type='button';button.textContent=option.textContent;button.dataset.choice=option.value;button.onclick=()=>{select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));sync();};group.append(button);}
  select.after(group);groups.push([select,group]);
 }
 const picker=document.getElementById('mobileViewPicker');picker.closest('.mobile-view-picker').classList.add('control-source');
 const section=document.createElement('section');section.className='visible-navigation';section.setAttribute('aria-label','Provincia y vista del tablero');section.innerHTML='<div class="visible-navigation-heading"><h2>Vista del tablero</h2></div><nav aria-label="Cambiar página del tablero"></nav>';
 const provinceField=document.getElementById('psel').closest('.command-field');provinceField.classList.add('fixed-province-picker');section.firstElementChild.append(provinceField);
 for(const option of picker.options){const button=document.createElement('button');button.type='button';button.dataset.page=option.value;button.textContent=option.textContent.replace(' provincial','').replace(' de Argentina','');button.onclick=()=>{const alreadyOpen=option.value.startsWith('open')&&document.querySelector('#federalTools > details[open]')?.id===panelKeys[option.value];if(!alreadyOpen){picker.value=option.value;picker.dispatchEvent(new Event('change'));}sync();const target=option.value.startsWith('open')?document.getElementById(panelKeys[option.value]):document.querySelector('[data-view-panel="'+dashboardView+'"]');target?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});};section.lastElementChild.append(button);}
 document.querySelector('.dashboard-command-bar').before(section);
 const panelKeys={openHistory:'fiscalHistoryPanel',openMap:'fiscalMapPanel',openNation:'nationalPanel',openOperations:'operationsPanel',openGuide:'fiscalGuide'};
 function sync(){
  for(const [select,group] of groups)for(const button of group.children){button.setAttribute('aria-pressed',String(button.dataset.choice===select.value));button.disabled=select.querySelector('option[value="'+button.dataset.choice+'"]')?.disabled||false;}
  const open=document.querySelector('#federalTools > details[open]');const active=open?Object.keys(panelKeys).find(k=>panelKeys[k]===open.id):dashboardView;
  for(const button of section.querySelectorAll('button'))button.setAttribute('aria-current',button.dataset.page===active?'page':'false');
 }
 document.addEventListener('change',sync);for(const panel of document.querySelectorAll('#federalTools > details'))panel.addEventListener('toggle',sync);
 new MutationObserver(sync).observe(document.querySelector('.dashboard-nav'),{subtree:true,attributes:true,attributeFilter:['class','aria-current']});
 new MutationObserver(sync).observe(document.getElementById('periodSelector'),{subtree:true,attributes:true,attributeFilter:['disabled']});
 new ResizeObserver(()=>document.documentElement.style.setProperty('--visible-nav-height',section.getBoundingClientRect().height+'px')).observe(section);
 sync();
}
if(typeof Chart!=='undefined')Chart.register({id:'touchFriendlyCharts',beforeInit(chart){
 const options=chart.config.options;
 options.animation=matchMedia('(prefers-reduced-motion: reduce)').matches?false:{duration:450,easing:'easeOutQuart'};
 options.interaction={mode:'index',intersect:false};
 options.plugins=options.plugins||{};options.plugins.tooltip={...options.plugins.tooltip,displayColors:true,padding:12,titleFont:{size:13},bodyFont:{size:13}};
},beforeUpdate(chart){
 for(const dataset of chart.data.datasets){if(chart.config.type==='bar'){dataset.borderRadius=4;dataset.maxBarThickness=40;}if(chart.config.type==='line'){dataset.pointHitRadius=18;dataset.pointHoverRadius=5;}}
}});

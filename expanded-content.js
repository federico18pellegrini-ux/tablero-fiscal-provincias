/* Internal content stays expanded; top-level details still route between views. */
function initExpandedContent(){
 const prepare=detail=>{
  if(detail.matches('.module-preferences'))return;
  const page=detail.parentElement?.id==='federalTools';
  detail.classList.add(page?'view-container':'expanded-content');
  const summary=detail.querySelector(':scope > summary');
  if(summary){
   summary.setAttribute('role','heading');summary.setAttribute('aria-level',page?'2':detail.classList.contains('gov-panel')?'4':'3');summary.tabIndex=-1;
   const first=summary.firstChild;
   if(!page&&first?.nodeType===Node.TEXT_NODE&&/^Ver\s/.test(first.textContent))first.textContent=first.textContent.replace(/^Ver\s+(.)/,(_,letter)=>letter.toLocaleUpperCase('es-AR'));
  }
  if(!page&&!detail.open)detail.open=true;
 };
 const scan=node=>{if(!(node instanceof Element))return;if(node.matches('details'))prepare(node);node.querySelectorAll('details').forEach(prepare);};
 scan(document.body);
 // Preserve existing toggle listeners that load historical charts and data.
 new MutationObserver(records=>{
  for(const record of records){
   if(record.type==='attributes')prepare(record.target);
   else record.addedNodes.forEach(scan);
  }
 }).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['open']});
 document.addEventListener('click',event=>{
  const summary=event.target.closest('summary');
  if(summary?.parentElement.matches('.expanded-content,.view-container'))event.preventDefault();
 });
}

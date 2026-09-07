/* Reports are generated from the dashboard datasets and checked before publication. */
function initManagementReportExport(){
 const old=document.getElementById('downloadPdf');
 const panel=document.createElement('section');panel.className='management-report-export';panel.setAttribute('aria-label','Informe de gestión de la provincia');
 const copy=document.createElement('div'),title=document.createElement('h2'),detail=document.createElement('p'),status=document.createElement('p');
 title.textContent='Informe de gestión';detail.id='managementReportDescription';status.id='managementReportStatus';status.setAttribute('role','status');
 const download=document.createElement('a');download.id='downloadPdf';download.className='management-report-download';download.textContent='Exportar informe (PDF)';download.setAttribute('aria-describedby',detail.id);
 const retry=document.createElement('button');retry.type='button';retry.textContent='Reintentar';retry.hidden=true;
 copy.append(title,detail,status);panel.append(copy,download,retry);old?.remove();document.getElementById('profilePurpose').before(panel);
 let manifest;
 function sync(){
  const province=document.getElementById('psel').value,report=manifest?.reports.find(r=>r.province===province);
  if(!report){download.removeAttribute('href');download.setAttribute('aria-disabled','true');download.tabIndex=-1;detail.textContent=province+' · Preparando el informe…';return;}
  const url=new URL('reports/'+report.file,location.href);url.searchParams.set('v',report.sha256.slice(0,12));
  download.href=url.href;download.download=report.file;download.removeAttribute('aria-disabled');download.removeAttribute('tabindex');
  detail.textContent=`${province} · ${report.pages} páginas · Datos, análisis editorial y prioridades de gestión. Cuentas ${report.annual_year} y señales ${report.quarter.slice(0,4)}.`;
  status.textContent=report.annual_available?'':`El cierre ${report.annual_year} no está disponible: el informe lo identifica y conserva los demás indicadores.`;
 }
 async function load(){
  retry.hidden=true;status.textContent='';
  try{
   const response=await fetch('reports/manifest.json?v=20260907-9',{cache:'no-cache'});if(!response.ok)throw Error('manifest');
   const data=await response.json();
   const expected=[...document.getElementById('psel').options].map(o=>o.value);
   if(!Array.isArray(data.reports)||data.reports.length!==expected.length||!expected.every(p=>data.reports.filter(r=>r.province===p&&r.pages===3&&/^informe-[a-z-]+\.pdf$/.test(r.file)&&/^[a-f0-9]{64}$/.test(r.sha256)).length===1))throw Error('coverage');
   manifest=data;sync();
  }catch{detail.textContent='No se pudo cargar el informe.';status.textContent='Reintentá la descarga en unos segundos.';retry.hidden=false;}
 }
 download.addEventListener('click',event=>{if(download.getAttribute('aria-disabled')==='true'){event.preventDefault();return;}status.textContent='Descarga solicitada para '+document.getElementById('psel').value+'.';});
 retry.addEventListener('click',load);document.getElementById('psel').addEventListener('change',sync);sync();load();
}

/* Provincial updates have their own period and never replace the common ranking. */
let pbaExecutionLatest=null,pbaExecutionRequest=null;
if(typeof Chart!=='undefined')Chart.defaults.font.size=14;
function renderLatestPbaUpdate(){
 let note=document.getElementById('pbaLatestSummary');
 if(currentProvince!=='Buenos Aires'){if(note)note.hidden=true;return;}
 if(!pbaExecutionLatest){
  if(!pbaExecutionRequest)pbaExecutionRequest=fetch('data/pba_execution_latest.json?v=20260915-9').then(r=>{if(!r.ok)throw Error('PBA execution');return r.json();}).then(d=>{pbaExecutionLatest=d;renderBudgetExecution();}).catch(()=>{pbaExecutionRequest=null;});
  return;
 }
 if(!note){note=document.createElement('p');note.id='pbaLatestSummary';note.className='latest-update';document.querySelector('#governorRoom > .profile-reading')?.after(note);}
 note.hidden=false;
 const row=pbaExecutionLatest.rows.find(r=>r.year===2026);
 note.replaceChildren();const title=document.createElement('strong');title.textContent='Último dato · enero–junio 2026: ';
 const value=document.createElement('span');value.className='negative-value';value.textContent='déficit de '+fnum(Math.abs(row.financial_pct))+'% de los ingresos.';
 const link=document.createElement('button');link.type='button';link.className='text-action';link.textContent='Ver el semestre →';link.onclick=()=>{applyDashboardView('income');document.getElementById('budgetExecution')?.scrollIntoView({behavior:'smooth',block:'start'});};
 note.append(title,value,document.createTextNode(' '),link);
}

/* Official observations keep their own cutoff, accounting stage and scope. */
let verifiedManagementData=null,verifiedManagementRequest=null;
function currentBudgetRatio(row){
 if(!Number.isFinite(row?.credit_ars_m)||row.credit_ars_m<=0)return null;
 if(Number.isFinite(row.accrued_ars_m))return {value:row.accrued_ars_m/row.credit_ars_m*100,basis:'devengado'};
 if(Number.isFinite(row.committed_ars_m))return {value:row.committed_ars_m/row.credit_ars_m*100,basis:'compromiso'};
 return null;
}
function renderVerifiedManagement(){
 if(!verifiedManagementData){
  if(!verifiedManagementRequest)verifiedManagementRequest=Promise.all(['current_budget_execution.json','management_evidence_audit.json'].map(f=>fetch('data/'+f+'?v=20260907-9').then(r=>{if(!r.ok)throw Error(f);return r.json();}))).then(([budgets,audit])=>{verifiedManagementData={budgets,audit};renderVerifiedManagement();}).catch(()=>{verifiedManagementRequest=null;const parent=document.getElementById('budgetExecution');if(parent&&!parent.querySelector('#currentBudgetExecution')){const p=document.createElement('p');p.id='currentBudgetExecution';p.textContent='No se pudo cargar la revisión del presupuesto vigente. Cambiá de provincia para reintentar.';parent.prepend(p);}});
  return;
 }
 const province=currentProvince,{budgets,audit}=verifiedManagementData,b=budgets.records.find(r=>r.province===province),a=audit.jurisdictions.find(r=>r.province===province);
 if(!a)return;
 const date=v=>v.split('-').reverse().join('/');
 const parent=document.getElementById('budgetExecution');
 if(parent){
  let host=document.getElementById('currentBudgetExecution');if(!host){host=document.createElement('section');host.id='currentBudgetExecution';parent.prepend(host);}host.replaceChildren();
  const title=document.createElement('h2');title.textContent='Presupuesto vigente · '+province;host.append(title);
  if(b){
   budgetParagraph(host,'Corte: '+date(b.as_of)+' · '+b.scope+'. Millones de pesos corrientes. El crédito corresponde a todo el año.'+([b.accrued_ars_m,b.committed_ars_m,b.paid_ars_m].some(Number.isFinite)?' La ejecución muestra el acumulado desde enero hasta ese corte.':''));
   const values=[['Crédito vigente: autorizado para gastar',b.credit_ars_m],['Devengado: obligaciones registradas',b.accrued_ars_m],['Comprometido: gasto reservado mediante un compromiso',b.committed_ars_m],['Pagado: desembolsos registrados',b.paid_ars_m]].filter(([,value])=>Number.isFinite(value));
   host.append(completionTable('Presupuesto actualizado y etapas verificadas',['Concepto','Millones de pesos'],values.map(([label,value])=>[label,fnum(value)])));
   const ratio=currentBudgetRatio(b);
   if(ratio){
    const text=ratio.basis==='devengado'?'De cada $100 autorizados para el año, se registraron $'+fnum(ratio.value)+' de gasto hasta este corte. Registrar una obligación no significa haberla pagado.':'De cada $100 autorizados para el año, $'+fnum(ratio.value)+' ya estaban comprometidos. Este porcentaje mide compromisos; no prueba que esos bienes o servicios se hayan recibido o pagado.';
    budgetParagraph(host,text+' Para saber si una política está atrasada hay que compararla con su programación. El paso de los meses no fija una meta automática.','profile-explanation');
   }
   budgetParagraph(host,b.note);
   budgetParagraph(host,'El crédito vigente es una autorización de gasto. La caja libre es el dinero conciliado que puede usarse después de identificar fondos afectados y pagos exigibles. Son datos distintos.');
  }else budgetParagraph(host,a.budget_finding+' El presupuesto inicial se conserva abajo, con su nombre y fecha.');
 }
 const operations=document.getElementById('operationsContent');
 if(operations&&document.getElementById('scenarioJurisdiction')){
  let host=document.getElementById('provincialEvidenceStatus');if(!host){host=document.createElement('section');host.id='provincialEvidenceStatus';host.className='national-section completion-card';operations.prepend(host);}host.replaceChildren();
  const h=document.createElement('h3');h.textContent='Qué sabemos de la caja y los vencimientos · '+province;host.append(h);
  budgetParagraph(host,'Revisión del '+date(audit.reviewed_at)+'. Elegí la provincia en el menú superior.');
  budgetParagraph(host,'Caja libre: todavía no hay un saldo conciliado verificable. '+a.cash_finding);
  budgetParagraph(host,a.debt_status==='located_pending_reconciliation'?'Se localizó el calendario oficial 2026–2029. Antes de mostrar sus importes, falta confirmar si la cifra de 2026 corresponde al año completo o sólo a lo que queda por pagar. Esa diferencia cambia la lectura de los próximos vencimientos.':a.debt_finding);
  if(a.debt_document_url&&a.debt_status!=='verified'){
   const link=document.createElement('a');link.className='management-action';link.href=a.debt_document_url;link.target='_blank';link.rel='noopener';link.textContent='Abrir calendario localizado · pendiente de conciliación';host.append(link);
  }
  budgetParagraph(host,'Para cerrar este punto hace falta una foto de Tesorería de la misma fecha: bancos conciliados, fondos afectados, obligaciones con fecha de pago y vencimientos por moneda. Un superávit fiscal, un depósito o un crédito sin ejecutar no reemplazan esa información.');
  const link=document.createElement('a');link.className='management-action';link.href='data/management_evidence_audit.csv';link.download='';link.textContent='Descargar revisión de las 24 jurisdicciones';host.append(link);
 }
}
if(typeof module!=='undefined')module.exports={currentBudgetRatio};

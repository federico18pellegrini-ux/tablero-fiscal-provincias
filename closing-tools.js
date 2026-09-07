/* Work proposals and local calculations do not certify Treasury balances. */
function reconcileCash(gross, restricted, blocked) {
  if (![gross,restricted,blocked].every(x=>typeof x==='number'&&Number.isFinite(x)&&x>=0)) return null;
  if (restricted+blocked>gross) return null;
  return gross-restricted-blocked;
}
if(typeof module!=='undefined'&&module.exports)module.exports={reconcileCash};

async function renderManagementProposals(host){
  host.replaceChildren();
  const title=document.createElement('h3');title.textContent='Metas propuestas para una futura gestión';host.append(title);
  try{
    const d=await operationFile('management_proposals.json');
    const note=document.createElement('p');note.textContent=d.methodology;host.append(note);
    const label=document.createElement('label');label.textContent='Jurisdicción de las metas ';const select=document.createElement('select');select.id='proposalProvince';label.append(select);host.append(label);
    for(const name of [...new Set(d.rows.map(r=>r.provincia))]){const o=document.createElement('option');o.value=name;o.textContent=name;select.append(o);}
    const rows=document.createElement('div');host.append(rows);
    const render=()=>{rows.replaceChildren(managementTable('Propuesta de trabajo · no aprobada',['Indicador y base','Meta y plazo','Responsabilidad y seguimiento'],d.rows.filter(r=>r.provincia===select.value).map(r=>[`${r.indicador}: ${fnum(r.valor_base)} ${r.unidad} · ${r.periodo_base}`,`${r.meta_propuesta===null?'Requiere nueva medición':fnum(r.meta_propuesta)+' '+r.unidad}. ${r.criterio}. ${r.horizonte}`,`${r.responsable_funcional}. ${r.seguimiento}${r.nota_cobertura?' · '+r.nota_cobertura:''}`])));};
    const sync=()=>{select.value=document.querySelector('#psel').value;render();};select.onchange=render;document.querySelector('#psel').addEventListener('change',sync);sync();
    managementSource(host,'data/management_proposals.csv','Descargar las 96 propuestas');
    managementSource(host,'data/management_targets_template.csv','Descargar matriz vacía para definir objetivos propios');
  }catch{const p=document.createElement('p');p.textContent='No se pudieron cargar las propuestas de metas. Reintentá al recargar.';host.append(p);}
}

async function renderUpdatedMaturities(host){
  const section=document.createElement('section');section.className='national-section';section.id='updatedMaturities';
  section.innerHTML='<h3>Vencimientos nacionales: actualización OPC</h3>';
  host.prepend(section);
  try{const d=await operationFile('maturities_opc.json');const p=document.createElement('p');p.textContent=d.reading;section.append(p);
    const hint=document.createElement('p');hint.className='federal-note';hint.textContent='En pantallas pequeñas, deslizá la tabla para ver ambas monedas.';section.append(hint);section.append(managementTable('Proyección de julio a diciembre de 2026 · capital e intereses',['Mes','Pagaderos en pesos · millones de ARS','Moneda extranjera · millones de USD equivalentes'],d.rows.map(r=>[r.period,fnum(r.ars_millions),fnum(r.usd_millions)])));
    const note=document.createElement('p');note.className='federal-note';note.textContent=d.reconciliation_note;section.append(note);managementSource(section,d.source_url,'OPC · informe junio 2026, cuadro 6, página 13 (página 16 del PDF)');
  }catch{section.append(document.createTextNode('No se pudo cargar la actualización OPC. El perfil anterior conserva su fecha de referencia.'));}
}

function initCashReconciliation(section){
  const details=document.createElement('details');details.className='history-values';details.id='cashReconciliation';
  details.innerHTML='<summary>Calcular caja inicial y descargar el escenario</summary><p>Trabajá con la misma jurisdicción y fecha del escenario. Ingresá saldos bancarios ya conciliados, expresados en millones de pesos. Las deducciones deben ser distintas entre sí.</p><div class="scenario-grid" id="reconciliationInputs"></div><p class="federal-note">Fondos afectados: tienen destino específico. Fondos bloqueados: no están disponibles por otra restricción. No restes aquí pagos futuros: van en los casilleros de pagos del escenario para evitar contarlos dos veces. Si hay moneda extranjera, documentá el tipo de cambio y la posibilidad de convertirla.</p><label>Referencia de los saldos y restricciones<input id="cashEvidence" type="text" placeholder="Documento, fecha de corte y criterio de conversión"></label><p id="reconciliationOutput" aria-live="polite">Completá los tres importes y la referencia documental.</p><button type="button" class="management-action" id="applyReconciledCash">Usar como caja inicial del escenario</button><button type="button" class="management-action" id="exportCashScenario">Descargar escenario con sus supuestos</button><p id="exportCashStatus" aria-live="polite"></p><p class="federal-note">Los datos permanecen en esta pantalla. La descarga se guarda en el dispositivo; no certifica los saldos ni los publica.</p>';
  section.append(details);
  for(const [id,label] of [['gross','Saldos conciliados brutos'],['restricted','Fondos afectados'],['blocked','Otros fondos bloqueados']]){const el=document.createElement('label');el.textContent=label;const input=document.createElement('input');input.id='reconcile_'+id;input.type='number';input.min=0;input.step='any';el.append(input);details.querySelector('#reconciliationInputs').append(el);}
  const read=id=>{const text=document.getElementById(id).value;return text.trim()===''?null:Number(text);};
  const compute=()=>reconcileCash(...['gross','restricted','blocked'].map(k=>read('reconcile_'+k)));
  const output=details.querySelector('#reconciliationOutput'),status=details.querySelector('#exportCashStatus');let applied=null;
  const invalidate=()=>{if(applied!==null){document.querySelector('#cash_cash').value='';document.querySelector('#cash_cash').dispatchEvent(new Event('input',{bubbles:true}));applied=null;}status.textContent='';const value=compute();output.textContent=value===null?'Completá importes válidos: las deducciones no pueden superar los saldos.':'Caja utilizable calculada: $ '+fnum(value)+' millones. Falta validar la documentación de respaldo.';};
  details.addEventListener('input',invalidate);
  const reset=()=>{details.querySelectorAll('input').forEach(i=>i.value='');applied=null;status.textContent='';output.textContent='Conciliación vacía para esta jurisdicción, fecha y horizonte.';};
  for(const id of ['scenarioJurisdiction','scenarioHorizon'])document.getElementById(id).addEventListener('change',reset);
  document.getElementById('scenarioDate').addEventListener('change',()=>{invalidate();reset();});document.getElementById('clearScenario').addEventListener('click',reset);
  document.getElementById('applyReconciledCash').onclick=()=>{const value=compute();if(value===null||!document.getElementById('cashEvidence').value.trim()||!document.getElementById('scenarioDate').value){output.textContent='Completá fecha, importes y referencia documental antes de usar el cálculo.';return;}document.getElementById('cash_cash').value=value;applied=value;document.getElementById('cash_cash').dispatchEvent(new Event('input',{bubbles:true}));output.textContent='Se incorporó el cálculo a la caja inicial. Verificá los pagos del horizonte para completar el escenario.';};
  document.getElementById('exportCashScenario').onclick=()=>{
    const inputs=Object.fromEntries(['cash','revenue','spending','principal','interest','financing'].map(k=>[k,read('cash_'+k)]));
    const result=calculateCashScenario(inputs),date=document.getElementById('scenarioDate').value,evidence=document.getElementById('cashEvidence').value.trim();
    if(!result||!date||!evidence){status.textContent='Para descargar, completá el escenario, la fecha y la referencia de sus supuestos.';return;}
    const data={schema_version:1,status:'Escenario ingresado por el usuario; no certificado',jurisdiction:document.getElementById('scenarioJurisdiction').value,as_of:date,horizon_days:Number(document.getElementById('scenarioHorizon').value),unit:'ARS millones nominales',evidence,inputs,result,reconciliation:applied!==null&&inputs.cash===applied?{gross:read('reconcile_gross'),restricted:read('reconcile_restricted'),blocked:read('reconcile_blocked'),available:applied}:null};
    const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='escenario-caja-'+date+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent='Escenario descargado con fecha, jurisdicción, supuestos y resultado.';
  };
}

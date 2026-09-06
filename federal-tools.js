/* Federal management tools. Observations remain separate from interpretation. */
let fiscalHistoryChart=null, provinceGeometry=null;
const fiscalNumber=new Intl.NumberFormat('es-AR',{maximumFractionDigits:2});
const fnum=value=>Number.isFinite(value)?fiscalNumber.format(value):'Sin dato';
const historyPeriods=()=>[...new Set((fiscalHistory?.rows||[]).map(r=>r.period))].sort();
const historyRow=(province,period)=>fiscalHistory?.rows.find(r=>r.province===province&&r.period===period);
const periodName=p=>p?`${p.slice(-1)}T${p.slice(2,4)}`:'Sin corte';
function fiscalChange(province,period){
  const periods=historyPeriods(),i=periods.indexOf(period);
  const row=historyRow(province,period),previous=historyRow(province,periods[i-1]);
  return row&&previous?row.financial_pct-previous.financial_pct:null;
}

function initFederalTools(){
  const rank=document.querySelector('.pulse-rank');if(rank)rank.parentElement.append(rank);
  const host=document.createElement('section');host.id='federalTools';host.className='federal-tools';
  host.innerHTML=`<nav class="federal-shortcuts" aria-label="Herramientas de gestión"><button type="button" id="openHistory">Historia fiscal</button><button type="button" id="openMap">Mapa y comparación</button><button type="button" id="openNation">Economía nacional</button><button type="button" id="openGuide">Cómo leer los datos</button></nav>
  <details id="fiscalHistoryPanel"><summary>Historia fiscal · <span id="historyProvince"></span></summary><div class="federal-content"><p>¿La provincia está mejorando o empeorando? Cada punto muestra los <strong>últimos 12 meses</strong> al cierre indicado. No es el resultado de ese trimestre.</p><div class="history-chart"><canvas id="fiscalHistoryChart" aria-label="Evolución del resultado primario y financiero" role="img"></canvas></div><p id="historyReading" aria-live="polite"></p><div class="federal-table"><table><caption>Resultados por cada $100 de ingresos · última versión publicada en cada informe</caption><thead><tr><th>Cierre</th><th>Primario</th><th>Financiero</th><th>Cambio financiero</th></tr></thead><tbody id="historyRows"></tbody></table></div><p class="federal-note">Fuente: 1816, informes fiscales provinciales, cuadro de la página 8. Compilación de ejecuciones provinciales. Los cambios pueden incluir revisiones de la fuente. Un espacio sin dato no representa cero.</p><a href="data/fiscal_history.json" download>Descargar datos y referencias</a></div></details>
  <details id="fiscalMapPanel"><summary>Argentina · comparación fiscal</summary><div class="federal-content"><div class="federal-filter"><label>Cierre <select id="mapPeriod"></select></label><label>Indicador <select id="mapMetric"><option value="financial_pct">Resultado después de intereses</option><option value="primary_pct">Resultado antes de intereses</option></select></label></div><p>Por cada $100 de ingresos, últimos 12 meses. Seleccioná una jurisdicción para abrir su tablero.</p><div class="federal-map-grid"><div><div id="argentinaFiscalMap"></div><p class="federal-note">Azul: superávit · naranja: déficit · gris: sin dato. El color muestra el saldo, no la calidad de gestión. CABA tiene acceso separado por su tamaño.</p></div><div><p id="federalAggregate"></p><div class="federal-table"><table><thead><tr><th>Jurisdicción</th><th>Saldo / ingresos</th></tr></thead><tbody id="mapRanking"></tbody></table></div></div></div></div></details>
  <details id="nationalPanel"><summary>Economía nacional · situación fiscal y agenda del ministro</summary><div class="federal-content" id="nationalContent"><p>Cargando fuentes nacionales…</p></div></details>
  <details id="fiscalGuide"><summary>Cómo leer el tablero y preparar una gestión</summary><div class="federal-content"><div class="federal-guide-grid"><div><h3>1. El punto de partida</h3><p>El resultado primario compara ingresos con gastos antes de intereses. El financiero incorpora los intereses. Un déficit es un nivel; para afirmar que la situación empeoró hay que compararlo con otro período.</p></div><div><h3>2. La capacidad de pagar</h3><p>Un superávit no garantiza dinero disponible. Para decidir hacen falta caja libre, vencimientos, deuda flotante y compromisos de salarios y transferencias. Donde no hay información, el tablero debe decirlo.</p></div><div><h3>3. La calidad del gasto</h3><p>El gasto en salud, educación o seguridad debe leerse junto con cobertura y resultados. Un ranking fiscal no mide por sí solo el desempeño de un gobernador.</p></div><div><h3>4. Una comparación válida</h3><p>Comparar la misma fecha, unidad y cobertura. Los pesos corrientes incorporan inflación. Los flujos mensuales reales usan el IPC nacional del mes; los totales anuales sin apertura mensual no tienen una conversión real validada.</p></div></div><p><strong>Primeros 100 días:</strong> reconciliar caja y obligaciones; identificar servicios críticos; construir escenarios con supuestos explícitos; fijar metas de ejecución y resultados con responsables.</p></div></details>`;
  document.getElementById('summaryView').before(host);
  for(const [button,panel] of [['openHistory','fiscalHistoryPanel'],['openMap','fiscalMapPanel'],['openNation','nationalPanel'],['openGuide','fiscalGuide']]){
    document.getElementById(button).onclick=()=>{const p=document.getElementById(panel);p.open=!p.open;if(p.open)p.scrollIntoView({behavior:'smooth',block:'start'});};
  }
  const periods=historyPeriods();document.getElementById('mapPeriod').innerHTML=periods.map(p=>`<option value="${p}">${periodName(p)}</option>`).join('');document.getElementById('mapPeriod').value=periods.at(-1)||'';
  document.getElementById('mapPeriod').onchange=renderFiscalMap;
  document.getElementById('mapMetric').onchange=renderFiscalMap;
  renderFiscalHistory(currentProvince);renderFiscalMap();renderNationalPanel();
  for(const [id,all] of [['downloadPdf',false],['downloadPdfAll',true]]){
    const old=document.getElementById(id);if(!old)continue;
    const button=old.cloneNode(true);old.replaceWith(button);
    button.addEventListener('click',()=>exportFiscalTextPdf(all));
  }
  fetch('data/province_geometry.json').then(r=>{if(!r.ok)throw Error('map');return r.json();}).then(d=>{provinceGeometry=d;renderFiscalMap();}).catch(()=>{document.getElementById('argentinaFiscalMap').textContent='Geometría no disponible. La tabla permite seleccionar las 24 jurisdicciones.';});
}

function renderFiscalHistory(province){
  const name=document.getElementById('historyProvince');if(!name)return;name.textContent=province;
  const periods=historyPeriods(), rows=periods.map(p=>historyRow(province,p));
  const latest=rows.at(-1),change=fiscalChange(province,periods.at(-1));
  document.getElementById('historyReading').textContent=latest?`Al ${periodName(latest.period)}, el saldo después de intereses fue ${fnum(latest.financial_pct)}% de los ingresos. ${change===null?'No hay un corte anterior comparable.':`Cambió ${fnum(change)} puntos porcentuales frente al corte anterior (${change>0?'mejoró':change<0?'empeoró':'sin cambio'}).`}`:'Sin información para esta jurisdicción en el último corte. Los datos anteriores se conservan abajo.';
  document.getElementById('historyRows').innerHTML=periods.map((p,i)=>`<tr><th scope="row">${periodName(p)}</th><td>${fnum(rows[i]?.primary_pct)}</td><td>${fnum(rows[i]?.financial_pct)}</td><td>${fnum(fiscalChange(province,p))} ${fiscalChange(province,p)===null?'':'pp'}</td></tr>`).join('');
  fiscalHistoryChart?.destroy();
  if(typeof Chart!=='undefined')fiscalHistoryChart=new Chart(document.getElementById('fiscalHistoryChart'),{type:'line',data:{labels:periods.map(periodName),datasets:[{label:'Antes de intereses',data:rows.map(r=>r?.primary_pct??null),borderColor:'#68b7ff',spanGaps:false},{label:'Después de intereses',data:rows.map(r=>r?.financial_pct??null),borderColor:'#ffb05c',spanGaps:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#d9e1ee'}}},scales:{x:{ticks:{color:'#c4ccd8'}},y:{title:{display:true,text:'% de ingresos',color:'#c4ccd8'},ticks:{color:'#c4ccd8'}}}}});
}

function chooseFiscalProvince(province){
  const sel=document.getElementById('psel');sel.value=province;sel.dispatchEvent(new Event('change'));applyDashboardView('summary');
  document.getElementById('fiscalMapPanel').open=false;document.getElementById('summaryView').scrollIntoView({behavior:'smooth'});
}
function renderFiscalMap(){
  const period=document.getElementById('mapPeriod').value,metric=document.getElementById('mapMetric').value;
  const provinces=[...document.getElementById('psel').options].map(o=>o.value);
  const rows=provinces.map(p=>({province:p,row:historyRow(p,period)})).sort((a,b)=>(b.row?.[metric]??-Infinity)-(a.row?.[metric]??-Infinity));
  const valid=rows.filter(r=>r.row),income=valid.reduce((s,r)=>s+r.row.income,0),numerator=valid.reduce((s,r)=>s+r.row[metric==='financial_pct'?'financial':'primary'],0);
  document.getElementById('federalAggregate').textContent=`Saldo conjunto: ${income?fnum(100*numerator/income):'Sin dato'}% de ingresos. Cobertura: ${valid.length} de 24 jurisdicciones. Calculado sumando los montos; no es un promedio simple ni el resultado del Gobierno nacional.`;
  const tbody=document.getElementById('mapRanking');tbody.replaceChildren();
  for(const {province,row} of rows){const tr=document.createElement('tr'),th=document.createElement('th'),td=document.createElement('td'),button=document.createElement('button');button.textContent=province;button.onclick=()=>chooseFiscalProvince(province);th.append(button);td.textContent=row?`${fnum(row[metric])}%`:'Sin dato';tr.append(th,td);tbody.append(tr);}
  if(!provinceGeometry)return;
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 400 660');svg.setAttribute('aria-label','Mapa fiscal de Argentina');
  for(const feature of provinceGeometry.features){const p=feature.province,path=document.createElementNS(svg.namespaceURI,'path'),row=historyRow(p,period);path.setAttribute('d',feature.path);path.setAttribute('fill',!row?'#707887':row[metric]>=0?'#2879ae':'#a75e24');path.setAttribute('stroke','#101924');path.setAttribute('stroke-width','1');path.setAttribute('tabindex','0');path.setAttribute('role','button');path.setAttribute('aria-label',`${p}: ${row?fnum(row[metric])+'%':'sin dato'}`);const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=path.getAttribute('aria-label');path.append(title);path.onclick=()=>chooseFiscalProvince(p);path.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();chooseFiscalProvince(p);}};svg.append(path);}
  const host=document.getElementById('argentinaFiscalMap');host.replaceChildren(svg);const caba=document.createElement('button');caba.textContent='Abrir CABA';caba.onclick=()=>chooseFiscalProvince('CABA');host.append(caba);const note=document.createElement('p');note.className='federal-note';note.textContent='Geometría: IGN / Georef. Vista continental e insular próxima; el sector antártico se omite de este encuadre estadístico.';host.append(note);
}

async function renderNationalPanel(){
  const host=document.getElementById('nationalContent');
  try{const r=await fetch('data/national_management.json');if(!r.ok)throw Error('source');const d=await r.json();
    host.innerHTML=`<p><strong>${d.scope}</strong> · ${d.period_label}. Base caja, pesos corrientes. No se suma a los resultados provinciales sin consolidar las transferencias entre gobiernos.</p><div class="national-kpis">${d.metrics.map(m=>`<article><h3>${m.label}</h3><strong>${fnum(m.value)} ${m.unit}</strong><p>${m.meaning}</p></article>`).join('')}</div><p>${d.reading}</p><p><a href="${d.source_url}" target="_blank" rel="noopener">Hacienda · publicación del ${d.publication_date}</a></p><h3>Para completar la decisión del ministro</h3><ul><li>Caja del Tesoro, vencimientos y refinanciación: calendario de los próximos 30, 90 y 365 días.</li><li>Actividad, empleo, pobreza y salarios reales: recuperar cobertura nacional comparable.</li><li>Reservas, sector externo y tasas: evaluar restricciones al financiamiento.</li><li>Subsidios, prestaciones sociales y transferencias: identificar compromisos y sensibilidad a inflación y actividad.</li></ul><p class="federal-note">Estos cuatro bloques aún no cuentan con una base nacional integrada en el tablero. No se generan pronósticos ni recomendaciones de financiamiento con esos faltantes.</p>`;
  }catch{host.textContent='No se pudo cargar la fuente nacional. No se reemplaza por el agregado de provincias.';}
}

async function exportFiscalTextPdf(all=false){
  const trigger=document.getElementById(all?'downloadPdfAll':'downloadPdf');trigger.disabled=true;
  setExportStatus('Preparando informe con texto seleccionable…','loading');
  try{
    await ensurePdfDependencies();
    const doc=new window.jspdf.jsPDF({unit:'mm',format:'a4'});
    const provinces=all?[...document.getElementById('psel').options].map(o=>o.value):[currentProvince];
    const period=historyPeriods().at(-1);let y=20;
    const line=(text,size=11,bold=false)=>{
      doc.setFont('helvetica',bold?'bold':'normal');doc.setFontSize(size);
      for(const part of doc.splitTextToSize(text,174)){
        if(y>272){doc.addPage();y=20;}
        doc.text(part,18,y);y+=size*.45+1.5;
      }
      y+=3;
    };
    for(const [index,province] of provinces.entries()){
      if(index)doc.addPage();y=20;
      const row=historyRow(province,period),quarter=latestFiscalDetails?.quarters?.[province],debt=latestFiscalDetails?.debt?.[province];
      line('CONSULTORA PELLEGRINI | TABLERO DE GESTIÓN',10,true);
      line(province,21,true);line(`Resultados: últimos 12 meses al ${periodName(period)}.`,11);
      line('Diagnóstico fiscal',14,true);
      if(row){
        line(`Antes de intereses: ${fnum(row.primary_pct)}% de ingresos. Después de intereses: ${fnum(row.financial_pct)}%.`);
        line(`Por cada $100 ingresados, ${row.financial_pct<0?'faltaron':'quedaron'} $${fnum(Math.abs(row.financial_pct))} después de intereses.`);
        const change=fiscalChange(province,period);line(change===null?'Sin corte anterior comparable.':`Cambio frente al corte anterior: ${fnum(change)} puntos porcentuales. Las revisiones de la fuente pueden afectar esta variación.`);
      }else line('Sin información homogénea para el último corte. No se completa con cero ni con datos de un período anterior.');
      if(quarter)line(`Trimestre enero-marzo de 2026: primario ${fnum(quarter.primary_pct)}%; financiero ${fnum(quarter.financial_pct)}%. Este dato no debe confundirse con los últimos 12 meses.`);
      line('Deuda y capacidad de pago',14,true);
      line(debt?`Stock al 1T26: USD ${fnum(debt.total)} millones, convertido al tipo de cambio oficial del cierre. Bonos: ${fnum(debt.bonds)}; Nación: ${fnum(debt.nation)}; organismos: ${fnum(debt.multilateral)}; bancos: ${fnum(debt.banks)} millones.`:'Stock homogéneo no disponible para este corte.');
      line('El saldo fiscal no acredita caja disponible. Completar caja libre, deuda flotante, vencimientos y financiamiento efectivamente utilizable antes de definir compromisos.');
      line('Evolución de los últimos cuatro cortes',14,true);
      for(const p of historyPeriods().slice(-4)){const r=historyRow(province,p);line(`${periodName(p)} | primario: ${fnum(r?.primary_pct)}% | financiero: ${fnum(r?.financial_pct)}%`,10);}
      line('Fuentes y alcance',14,true);line('1816, informes fiscales provinciales: resultados anuales, página 8; trimestre, página 6; deuda, página 21 del informe 1T26. La historia conserva los valores publicados en cada informe.',9);
      line('Montos de deuda en millones de dólares; resultados en porcentaje de ingresos. La Pampa no integra el corte comparable 1T26. Este informe separa datos observados de necesidades de información para la gestión.',9);
      line('https://tablero.federicopellegrini.com.ar/',9);
    }
    const pages=doc.getNumberOfPages();for(let i=1;i<=pages;i++){doc.setPage(i);doc.setFontSize(8);doc.text(`Consultora Pellegrini | ${i} / ${pages}`,18,287);}
    doc.save(all?'informe-fiscal-24-jurisdicciones.pdf':`informe-fiscal-${currentProvince}.pdf`);
    setExportStatus(`Informe generado: ${pages} páginas con texto seleccionable.`,'success');
  }catch(error){setExportStatus(`No se pudo generar el informe: ${error.message}`,'error');}
  finally{trigger.disabled=false;}
}


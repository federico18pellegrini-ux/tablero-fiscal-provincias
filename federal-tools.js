/* Federal management tools. Observations remain separate from interpretation. */
let fiscalHistoryChart=null, provinceGeometry=null, debtHistory=null, compositionChart=null, nationalActivityChart=null;
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
  <details id="fiscalHistoryPanel"><summary>Historia fiscal · <span id="historyProvince"></span></summary><div class="federal-content"><p>Para ver si las cuentas mejoran, seguí la evolución del resultado. Cada punto suma los <strong>últimos 12 meses</strong> hasta esa fecha; no muestra solamente lo que pasó en el trimestre.</p><div class="history-chart"><canvas id="fiscalHistoryChart" aria-label="Evolución del resultado primario y financiero" role="img"></canvas></div><p id="historyReading" aria-live="polite"></p><details class="history-values"><summary>Ver los valores de cada período</summary><div class="federal-table"><table><caption>Resultados por cada $100 de ingresos · última versión publicada en cada informe</caption><thead><tr><th>Cierre</th><th>Primario</th><th>Financiero</th><th>Cambio financiero</th></tr></thead><tbody id="historyRows"></tbody></table></div></details><p class="federal-note">Fuente: 1816, informes fiscales provinciales, cuadro de la página 8. Compilación de ejecuciones provinciales. Los cambios pueden incluir revisiones de la fuente. Un espacio sin dato no representa cero.</p><a href="data/fiscal_history.json" download>Descargar datos y referencias</a></div></details>
  <details id="fiscalMapPanel"><summary>Argentina · comparación fiscal</summary><div class="federal-content"><div class="federal-filter"><label>Cierre <select id="mapPeriod"></select></label><label>Indicador <select id="mapMetric"><option value="financial_pct">Resultado después de intereses</option><option value="primary_pct">Resultado antes de intereses</option></select></label></div><p>Por cada $100 de ingresos, últimos 12 meses. Seleccioná una jurisdicción para abrir su tablero.</p><div class="federal-map-grid"><div><div id="argentinaFiscalMap"></div><p class="federal-note">Azul: superávit · naranja: déficit · gris: sin dato. El color muestra el saldo, no la calidad de gestión. CABA tiene acceso separado por su tamaño.</p></div><div><p id="federalAggregate"></p><div class="federal-table"><table><thead><tr><th>Jurisdicción</th><th>Saldo / ingresos</th></tr></thead><tbody id="mapRanking"></tbody></table></div></div></div></div></details>
  <details id="nationalPanel"><summary>Economía nacional · situación fiscal y agenda del ministro</summary><div class="federal-content" id="nationalContent"><p>Cargando fuentes nacionales…</p></div></details>
  <details id="fiscalGuide"><summary>Cómo leer el tablero y preparar una gestión</summary><div class="federal-content"><div class="federal-guide-grid"><div><h3>1. El punto de partida</h3><p>Primero mirá si los ingresos alcanzan para cubrir los gastos sin intereses: ese es el resultado primario. Después restá los intereses y tenés el resultado financiero. Si da déficit, se gastó más de lo que ingresó. Para saber si empeoró, hay que compararlo con otro período.</p></div><div><h3>2. La capacidad de pagar</h3><p>Podés tener superávit y no tener la plata disponible para pagar mañana. El tema es cuánto dinero podés usar y cuándo vencen los pagos. Por eso hay que mirar la caja, los salarios, las transferencias, los vencimientos y las obligaciones que quedaron pendientes.</p></div><div><h3>3. La calidad del gasto</h3><p>Gastar más en salud, educación o seguridad no alcanza para saber si el servicio mejoró. Hay que mirar a cuánta gente llega y qué resultados consigue. El ranking fiscal ayuda a entender las cuentas; por sí solo no te dice cómo está gobernada una provincia.</p></div><div><h3>4. Una comparación válida</h3><p>Si la recaudación sube, primero hay que ver cuánto subieron los precios. Puede entrar más plata y que alcance para comprar menos. Para comparar, llevamos cada mes a los precios de una misma fecha con el IPC nacional. Si sólo tenemos el total anual, falta el detalle mensual para hacer ese ajuste correctamente.</p></div></div><p><strong>Primeros 100 días:</strong> comprobar cuánta caja hay y qué pagos vienen, identificar los servicios que no pueden esperar y ponerle un responsable y una fecha a cada objetivo. Después, ver cómo cambia la caja si los ingresos o los pagos se apartan de lo previsto.</p></div></details>`;
  document.getElementById('summaryView').before(host);
  for(const [button,panel] of [['openHistory','fiscalHistoryPanel'],['openMap','fiscalMapPanel'],['openNation','nationalPanel'],['openGuide','fiscalGuide']]){
    const trigger=document.getElementById(button);trigger.setAttribute('aria-controls',panel);trigger.setAttribute('aria-expanded','false');
    document.getElementById(panel).addEventListener('toggle',()=>trigger.setAttribute('aria-expanded',String(document.getElementById(panel).open)));
    trigger.onclick=()=>{const p=document.getElementById(panel),open=!p.open;for(const other of host.querySelectorAll(':scope > details'))other.open=false;p.open=open;if(open)p.scrollIntoView({behavior:'smooth',block:'start'});};
  }
  const periods=historyPeriods();document.getElementById('mapPeriod').innerHTML=periods.map(p=>`<option value="${p}">${periodName(p)}</option>`).join('');document.getElementById('mapPeriod').value=periods.at(-1)||'';
  document.getElementById('mapPeriod').onchange=renderFiscalMap;
  document.getElementById('mapMetric').onchange=renderFiscalMap;
  initCompositionExplorer();
  initManagementDesign();
  renderProfileReadings();
  renderFiscalHistory(currentProvince);renderFiscalMap();renderNationalPanel();
  fetch('data/debt_history.json').then(r=>{if(!r.ok)throw Error('debt');return r.json();}).then(d=>{debtHistory=d;renderComposition(currentProvince);}).catch(()=>{debtHistory={rows:[],failed:true};renderComposition(currentProvince);});
  for(const [id,all] of [['downloadPdf',false],['downloadPdfAll',true]]){
    const old=document.getElementById(id);if(!old)continue;
    const button=old.cloneNode(true);old.replaceWith(button);
    button.addEventListener('click',()=>exportFiscalTextPdf(all));
  }
  fetch('data/province_geometry.json').then(r=>{if(!r.ok)throw Error('map');return r.json();}).then(d=>{provinceGeometry=d;renderFiscalMap();}).catch(()=>{document.getElementById('argentinaFiscalMap').textContent='Geometría no disponible. La tabla permite seleccionar las 24 jurisdicciones.';});
}

function renderFiscalHistory(province){
  const name=document.getElementById('historyProvince');if(!name)return;name.textContent=province;
  renderComposition(province);
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
  try{
    const response=await fetch('data/national_management.json?v=20260906-9');if(!response.ok)throw Error('source');const d=await response.json();nationalReadingData=d;
    host.replaceChildren();
    const paragraph=(parent,text)=>{const p=document.createElement('p');p.textContent=text;parent.append(p);return p;};
    const source=(parent,url,date,label='Fuente oficial')=>{const p=document.createElement('p');p.className='federal-note';const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener';a.textContent=date?`${label} · publicación: ${date}`:label;p.append(a);parent.append(p);};
    const cards=(parent,metrics,fallback)=>{const grid=document.createElement('div');grid.className='national-kpis';parent.append(grid);for(const m of metrics){const card=document.createElement('article'),title=document.createElement('h3'),value=document.createElement('strong');title.textContent=m.label;value.textContent=`${fnum(m.value)} ${m.unit}`;card.append(title,value);paragraph(card,m.period||fallback);paragraph(card,m.meaning);if(m.source_url)source(card,m.source_url,m.publication_date);grid.append(card);}};
    paragraph(host,`Lectura para la gestión · fuentes revisadas al ${d.reviewed_at}. Cada bloque tiene su propio período y cobertura. Las cifras son observadas, salvo el cálculo salarial identificado como estimación.`);
    const title=document.createElement('h3');title.textContent='Resultado fiscal: ingresos, gastos e intereses';host.append(title);
    paragraph(host,`${d.scope} · ${d.period_label}. Base caja, pesos corrientes. No se suma a las provincias sin consolidar transferencias entre gobiernos.`);
    cards(host,d.metrics,d.period_label);paragraph(host,d.reading);source(host,d.source_url,d.publication_date,'Hacienda');
    await renderNationalOperations(host);
    for(const s of d.sections||[]){const section=document.createElement('section');section.id='national-'+s.id;section.className='national-section';const h=document.createElement('h3');h.textContent=s.title;section.append(h);paragraph(section,s.scope);cards(section,s.metrics);paragraph(section,s.reading);source(section,s.source_url,s.publication_date);host.append(section);
      if(s.id==='activity'&&d.activity_history?.rows.length){const detail=document.createElement('details');detail.className='national-history';const summary=document.createElement('summary');summary.textContent='Ver historia de actividad desde 2004';detail.append(summary);paragraph(detail,'EMAE desestacionalizado, índice 2004=100. Permite comparar niveles entre meses. Versión de la serie publicada el 20/08/2026.');const box=document.createElement('div');box.className='history-chart';const canvas=document.createElement('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Historia mensual de actividad económica desde 2004');box.append(canvas);detail.append(box);source(detail,d.activity_history.source_url,d.activity_history.publication_date,'Serie INDEC');section.append(detail);
        detail.addEventListener('toggle',()=>{if(!detail.open||nationalActivityChart||typeof Chart==='undefined')return;const rows=d.activity_history.rows;nationalActivityChart=new Chart(canvas,{type:'line',data:{labels:rows.map(r=>r.period),datasets:[{label:'Actividad sin estacionalidad',data:rows.map(r=>r.seasonally_adjusted),borderColor:'#68b7ff',pointRadius:0,spanGaps:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#d9e1ee'}}},scales:{x:{ticks:{color:'#c4ccd8',maxTicksLimit:12}},y:{ticks:{color:'#c4ccd8'}}}}});});
      }
    }
    const nav=document.createElement('nav');nav.className='national-section-nav';nav.setAttribute('aria-label','Temas de economía nacional');for(const section of host.querySelectorAll('.national-section')){const a=document.createElement('a');a.href='#'+section.id;a.textContent=section.querySelector('h3').textContent.split(':')[0];nav.append(a);}host.firstElementChild.after(nav);
    const h=document.createElement('h3');h.textContent='Qué falta actualizar para tomar decisiones';host.append(h);const ul=document.createElement('ul');for(const item of d.missing_blocks||[]){const li=document.createElement('li');li.textContent=item;ul.append(li);}host.append(ul);source(host,'data/national_management.json',null,'Descargar indicadores, historia y referencias');renderProfileReadings();
  }catch{host.textContent='No se pudo cargar la fuente nacional. No se reemplaza por el agregado de provincias.';}
}

async function exportFiscalTextPdf(all=false){
  const trigger=document.getElementById(all?'downloadPdfAll':'downloadPdf');trigger.disabled=true;
  setExportStatus('Preparando informe con texto seleccionable…','loading');
  try{
    if(!window.jspdf?.jsPDF)await loadScriptOnce(EXPORT_LIB_URLS.jspdf);
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

function initCompositionExplorer(){
  const section=document.createElement('section');section.className='composition-explorer';
  section.innerHTML=`<h3>Qué explica el resultado y cuánto pesa la deuda</h3><label>Explorar <select id="compositionMode"><option value="income">De dónde vienen los ingresos</option><option value="spend">En qué se gasta</option><option value="debt">Deuda y capacidad de pago</option></select></label><p id="compositionReading" aria-live="polite"></p><div class="history-chart"><canvas id="compositionChart" role="img" aria-label="Evolución de la composición fiscal"></canvas></div><details class="history-values"><summary>Ver datos y composición por período</summary><div class="federal-table"><table id="compositionTable"></table></div></details><p id="compositionSource" class="federal-note"></p>`;
  document.querySelector('#fiscalHistoryPanel .federal-content').append(section);
  document.getElementById('compositionMode').onchange=()=>renderComposition(currentProvince);
}
function renderComposition(province){
  const select=document.getElementById('compositionMode');if(!select)return;
  const mode=select.value,periods=historyPeriods(),debt=mode==='debt';
  const rows=periods.map(p=>debt?debtHistory?.rows.find(r=>r.province===province&&r.period===p):historyRow(province,p));
  const fields=mode==='income'?[['tax','Tributos propios'],['royalties','Regalías'],['national_tax','Tributos nacionales'],['social_income','Seguridad social'],['other_income','Otros ingresos']]:[['personnel','Personal'],['current_transfers','Transferencias corrientes'],['capital','Capital'],['social_spend','Seguridad social'],['other_spend','Otros gastos']];
  const ratio=(r,k)=>r&&r.income>0&&Number.isFinite(r[k])?100*r[k]/r.income:null;
  const series=debt?[{label:'Deuda / ingresos',data:rows.map(r=>r?.ratios?.debt_income_pct??null)}]:fields.map(([key,label])=>({label,data:rows.map(r=>ratio(r,key))}));
  const colors=['#68b7ff','#ffb05c','#6bd5b5','#d6a3ff','#f6d273'];
  compositionChart?.destroy();
  if(typeof Chart!=='undefined')compositionChart=new Chart(document.getElementById('compositionChart'),{type:'line',data:{labels:periods.map(periodName),datasets:series.map((s,i)=>({...s,borderColor:colors[i],spanGaps:false,pointRadius:2}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#d9e1ee'}}},scales:{x:{ticks:{color:'#c4ccd8'}},y:{title:{display:true,text:'% de ingresos',color:'#c4ccd8'},ticks:{color:'#c4ccd8'}}}}});
  document.getElementById('compositionReading').textContent=debt?(debtHistory?.failed?'No se pudo cargar la historia de deuda. No se reemplaza por cero.':!debtHistory?'Cargando historia de deuda…':'El gráfico compara el stock de deuda con los ingresos de los últimos 12 meses. Un 50% equivale a la mitad de los ingresos de un año; no indica cuánto vence ni qué caja hay disponible.'):mode==='income'?'Por cada $100 de ingresos, cuánto aporta cada fuente. La dependencia de tributos nacionales ayuda a evaluar la exposición a cambios en la recaudación y distribución federal.':'Por cada $100 de ingresos, cuánto se destina a cada componente del gasto primario. La suma puede superar $100 si hay déficit; los intereses se muestran aparte. Capital no equivale exclusivamente a obra pública.';
  const headers=debt?['Cierre','Deuda / ingresos (%)','Stock (millones)','Moneda del stock','Bonos','Nación','Organismos','Bancos','Consolidada']:['Cierre',...fields.map(f=>f[1]),...(mode==='spend'?['Intereses']:[])];
  const table=document.getElementById('compositionTable');table.replaceChildren();
  const caption=table.createCaption();caption.textContent=debt?'Stock al cierre y composición por acreedor, en millones de la moneda indicada':'Últimos 12 meses · por cada $100 de ingresos';
  const head=table.createTHead().insertRow();for(const title of headers){const th=document.createElement('th');th.scope='col';th.textContent=title;head.append(th);}
  const body=table.createTBody();
  periods.forEach((p,i)=>{const r=rows[i],tr=body.insertRow(),th=document.createElement('th');th.scope='row';th.textContent=periodName(p);tr.append(th);
    const values=debt?[fnum(r?.ratios?.debt_income_pct),fnum(r?.total),r?.currency??'Sin dato',...['bonds','nation','multilateral','banks','consolidated'].map(k=>fnum(r?.[k]))]:[...fields.map(([k])=>fnum(ratio(r,k))),...(mode==='spend'?[fnum(r? -ratio(r,'interest_signed'):null)]:[])];
    for(const v of values)tr.insertCell().textContent=v;
  });
  const source=document.getElementById('compositionSource');source.textContent=debt?'Fuente: 1816, páginas 21 (stock) y 23 (deuda / ingresos) de cada informe. Hasta 2T24 el stock se publica en ARS; desde 3T24, en USD equivalentes. No se comparan ni se suman montos de distinta moneda. Los huecos conservan faltantes de la fuente. ':'Fuente: 1816, página 8 de cada informe. Cociente de cada componente sobre ingresos totales, incluida seguridad social. No es una variación real del gasto ni una apertura por función (salud, educación o seguridad). ';
  const link=document.createElement('a');link.href=debt?'data/debt_history.json':'data/fiscal_history.json';link.download='';link.textContent='Descargar datos y referencias';source.append(link);
}

import {populationPeers, peerMedian, comparableFiscalResult, workforceDisplay, isNumber} from './structure-model.mjs';

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = (v, digits = 1) => isNumber(v) ? new Intl.NumberFormat('es-AR', {maximumFractionDigits:digits}).format(v) : 'Sin dato';
const money = v => isNumber(v) ? '$' + number(v / 1e6) + ' millones' : 'Sin dato';
const sourceLinks = sources => (sources || []).map(s => `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)} ↗</a>`).join(' · ');
const verifiedNote = observation => observation?.evidence ? `<p class="small-note">Contrastado con el original · página ${observation.evidence.page}${observation.evidence.periodEnd?" · cierre "+observation.evidence.periodEnd.split("-").reverse().join("/"):""}. <a href="data/${esc(observation.evidence.file)}" target="_blank" rel="noopener">Documento conservado ↗</a></p>` : '';
let structure, failure;
const ready = fetch('data/structure.json?v=20261014-verificados').then(r => {if (!r.ok) throw Error('datos'); return r.json();}).then(d => {structure=d;}).catch(() => {failure=true;});

function metricCard(label, value, period, explanation, sources) {
  return `<article class="panel structure-card"><h3>${esc(label)}</h3><strong class="structure-value">${value}</strong><p class="small-note">${esc(period || 'Sin período disponible')}</p><p>${esc(explanation)}</p><p class="structure-source">${sourceLinks(sources)}</p></article>`;
}

function exportStructure(m, extra) {
  const rows = [['Municipio','Indicador','Valor','Unidad','Período','Verificación','Documento']];
  const add = (label,value,unit,period,sources,verified=false) => rows.push([m.municipio,label,value ?? '',unit,period,verified?'Contrastado con documento original':'Relevamiento externo; pendiente de contraste independiente',sources.map(s=>s.url).join(' | ')]);
  const e = extra.workforce;
  if(e) {
    const display = workforceDisplay(e);
    add(display.label,display.value,e.type==='o'?'personas':'cargos',e.period,e.sources,!!e.evidence);
    e.categories.forEach(([label,value])=>add(display.label+' · '+label,value,e.type==='o'?'personas':'cargos',e.period,e.sources,!!e.evidence));
  }
  for (const [key,label,unit] of [['flo','Deuda flotante','ARS corrientes'],['hcd','Concejo / gasto presupuestario devengado','%'],['pub','Publicidad','ARS corrientes']]) {
    const x=extra.indicators[key]; if(x)add(label,x.value,unit,x.period,x.sources,!!x.evidence);
  }
  const contents='\uFEFF'+rows.map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(';')).join('\r\n');
  const url=URL.createObjectURL(new Blob([contents],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=`gestion-${m.id}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
}

async function render(context) {
  if(!context || context.view!=='gestion')return;
  const container=document.getElementById('structure-content');
  container.innerHTML='<p role="status">Cargando información de gestión…</p>';
  await ready;
  if(window.municipalStructureContext!==context)return;
  if(failure){container.innerHTML='<p role="alert">No se pudieron cargar estos datos. Volvé a abrir la página para reintentar.</p>';return;}
  const {municipality:m,rows}=context, extra=structure.municipalities.find(x=>x.id===m.id);
  if(!extra){container.textContent='No hay un relevamiento disponible para este municipio.';return;}
  const e=extra.workforce, employee=workforceDisplay(e);
  const categories=e?.categories.map(([name,v])=>`${esc(name)}: ${number(v,0)}`).join(' · ') || '';
  let employeeValue=employee.partial?'Dato parcial':number(employee.value,0);
  if(!e)employeeValue='Sin dato relevado';
  const explanations={o:'Personas o legajos registrados en la nómina. El alcance depende de los organismos incluidos.',c:'Puestos autorizados en el presupuesto. Pueden incluir vacantes; no es la cantidad de personas que trabajan.',x:'Cargos ocupados informados por RAFAM. Una persona puede ocupar más de un cargo.'};
  const cardEmployee=metricCard(employee.label,employeeValue,e?.period,e?explanations[e.type]:'Todavía no incorporamos un documento con la cantidad de personal.',e?.sources)
    .replace('</article>',`${categories?`<p>${categories}</p>`:''}${verifiedNote(e)}</article>`);
  const debt=extra.indicators.flo, council=extra.indicators.hcd, advertising=extra.indicators.pub;
  const cohort=populationPeers(m,rows);
  const comparisons=[
    ['Hogares con necesidades básicas insatisfechas','Censo 2022','%',x=>x.hogares_nbi_2022_pct],
    ['Empleo privado formal por 1.000 habitantes','Diciembre 2025 · población Censo 2022','',x=>x.empleos_formales_dic2025_por_1000_hab_base2022],
    ['Resultado financiero / ingresos','Enero–junio 2026','%',comparableFiscalResult]
  ];
  const tableRows=comparisons.map(([label,period,unit,value])=>{
    const median=peerMedian(cohort,value), own=value(m);
    const show=v=>isNumber(v)?number(v)+unit:'Sin dato';
    return `<tr><th scope="row">${esc(label)}<small>${esc(period)}</small></th><td data-label="Este municipio" class="${own<0?'negative':''}">${show(own)}</td><td data-label="Mediana de pares" class="${median.value<0?'negative':''}">${median.n<3?'Menos de 3 pares':show(median.value)}<small>${median.n} con datos</small></td></tr>`;
  }).join('');
  container.innerHTML=`<section class="panel structure-peers"><div class="eyebrow">Comparar con una referencia cercana</div><h2>Municipios de tamaño similar</h2><p>Los cinco más cercanos por población dentro de un rango entre la mitad y el doble de ${esc(m.municipio)}. Se compara cada indicador en el mismo período.</p><div class="structure-peer-links">${cohort.map(p=>`<a class="button button-quiet" href="?municipio=${p.id}&vista=gestion">${esc(p.municipio)} · ${number(p.poblacion_2022,0)} hab.</a>`).join('')}</div><table class="detail-table"><caption>${esc(m.municipio)} frente a sus pares por población</caption><thead><tr><th>Indicador</th><th>Este municipio</th><th>Mediana de pares</th></tr></thead><tbody>${tableRows}</tbody></table><p class="small-note">La mediana es el valor del medio: evita que un caso extremo distorsione la referencia. Se calcula con al menos tres pares. El tamaño no iguala los servicios a cargo, la actividad económica ni la superficie.</p></section>
    <section class="structure-survey"><div class="section-heading"><div><div class="eyebrow">Ampliar la información</div><h2>Personal y compromisos municipales</h2><p>Relevamiento de <a href="https://municipiosargentinos.net/" target="_blank" rel="noopener">Municipios Argentinos</a> con documentos oficiales enlazados. Los registros confirmados están identificados; los demás siguen en revisión. Cada dato conserva su fecha.</p></div></div><div class="structure-grid">${cardEmployee}
    ${metricCard('Deuda flotante',money(debt?.value),debt?.period,'Gastos registrados que siguen pendientes de pago a la fecha del documento. No se suman otra vez al déficit: ya pueden estar incluidos en el gasto.',debt?.sources).replace('</article>',verifiedNote(debt)+'</article>')}
    ${metricCard('Concejo Deliberante',council?number(council.value,2)+'% del gasto':'Sin dato relevado',council?.period,'Participación del Concejo sobre el gasto presupuestario devengado del mismo período. Ese total puede incluir aplicaciones financieras y diferir del gasto fiscal de la sección Recursos.',council?.sources).replace('</article>',verifiedNote(council)+'</article>')}
    ${metricCard('Publicidad',money(advertising?.value),advertising?.period,'Importe identificado como publicidad en el relevamiento. La clasificación y el alcance pueden variar; un dato faltante no significa gasto cero.',advertising?.sources).replace('</article>',verifiedNote(advertising)+'</article>')}</div><button class="button button-quiet" id="download-structure">Descargar estos datos y documentos ↓</button><p class="small-note">Los datos contrastados ya integran el ranking de Gestión y el apartado seleccionable Gestión municipal verificada del PDF. Los pendientes quedan afuera.</p></section>
    <section class="panel structure-control"><div class="eyebrow">Control de cuentas</div><h2>Documentos del Tribunal de Cuentas</h2><p>Permiten revisar qué observó el organismo en cada ejercicio y las respuestas del municipio. Una observación administrativa no equivale a una condena penal; el fallo puede tener revisiones posteriores.</p><div class="structure-peer-links">${extra.decisions.length?extra.decisions.map(d=>`<a class="button button-quiet" href="${esc(d.url)}" target="_blank" rel="noopener">Consultar ejercicio ${esc(d.year)} ↗</a>`).join(''):'<p>Sin enlaces a fallos específicos incorporados para este municipio.</p>'}</div><p class="small-note">Enlaces identificados en el relevamiento externo. No reproducimos montos de sanciones sin verificar el fallo y sus revisiones. <a href="https://www.htc.gba.gov.ar/fallos" target="_blank" rel="noopener">Buscador oficial ↗</a></p></section>`;
  document.getElementById('download-structure').onclick=()=>exportStructure(m,extra);
}
window.addEventListener('municipal:structure',event=>render(event.detail));
if(window.municipalStructureContext)render(window.municipalStructureContext);

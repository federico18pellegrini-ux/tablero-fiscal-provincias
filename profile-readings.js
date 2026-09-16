/* Profile changes affect interpretation, never the observations or source units. */
function normalizeReadingProfile(value){return value==='deep'?'hacienda':value==='analyst'?'press':['governor','hacienda','press'].includes(value)?value:'governor';}
function profileWording(governor,hacienda,press){return {governor,hacienda,press}[normalizeReadingProfile(dashboardProfile)];}
function readingPeriod(value){
 return /^\d{4}-Q[1-4]$/.test(value||'')?`${value.slice(-1)}T${value.slice(0,4)}`:value||'el período informado';
}
function buildProfileReadings(profile,c={}){
 const role=normalizeReadingProfile(profile),choose=(g,m,p)=>({governor:g,hacienda:m,press:p}[role]);
 const {province='La provincia',rf=null,rp=null,debt=null,period='últimos 12 meses al 31/03/2026'}=c;
 const n=v=>v.toLocaleString('es-AR',{maximumFractionDigits:2});
 const financial=Number.isFinite(rf)?`${province}: resultado financiero de ${n(rf)}% de los ingresos (${period}).`:`${province}: falta un resultado financiero comparable para ${period}.`;
 const debtFact=Number.isFinite(debt)?`Por cada $100 de ingresos anuales, la deuda equivale a $${n(debt)}. Ese total se devuelve a lo largo del tiempo.`:'Falta el dato para comparar la deuda total con los ingresos de un año.';
 const scheduleRows=(c.projection?.rows||[]).filter(r=>Number.isFinite(r.year)&&Number.isFinite(r.total_ars_m)&&r.total_ars_m>=0);
 const peak=scheduleRows.length?scheduleRows.reduce((a,b)=>b.total_ars_m>a.total_ars_m?b:a):null;
 const schedule=peak?`El calendario publicado tiene su mayor importe anual en ${peak.year}. Incluye el año completo, sin descontar los pagos posteriores.`:c.debtScheduleStatus==='loading'?'Estamos cargando el calendario de pagos.':'Las barras muestran capital e intereses registrados en años anteriores. Falta el calendario de próximos pagos.';
 const debtFocus=choose(
  'La clave es cuánto vence en cada fecha: esos pagos compiten por recursos con salarios, servicios y obras. Anticiparlos permite organizar cómo cubrirlos.',
  'Para organizar los pagos, separar capital —el dinero que se devuelve— e intereses —el costo de financiarse—. Revisar fechas, monedas y financiamiento disponible.',
  'La deuda total mide cuánto se debe. Los vencimientos indican cuándo hay que pagarlo. Esa diferencia permite explicar la presión sobre las cuentas.');
 const own=Number.isFinite(c.autonomy)?`Los recursos propios —impuestos y regalías— aportan $${n(c.autonomy)} de cada $100 de ingresos, sin contar los recursos de seguridad social.`:'Los impuestos propios y las transferencias de Nación financian buena parte de los servicios provinciales.';
 const prices=c.priceMode==='real'?'La vista en pesos constantes descuenta la inflación para comparar poder de compra.':'La vista en pesos corrientes muestra los importes de cada fecha. Para comparar poder de compra, usar pesos constantes, que descuentan la inflación.';
 const claim=c.claim||{};
 const federalFact=claim.kind==='reclamo'?'Además de las transferencias habituales, la Provincia tiene un reclamo publicado por fondos de Nación. El detalle separa los conceptos y los acuerdos alcanzados.':claim.kind==='anticipo'?'El importe destacado corresponde a anticipos acordados con Nación: fondos que se adelantan y luego se ajustan según lo que corresponda financiar.':claim.kind==='credito_compensable'?'El importe destacado es un crédito para compensar obligaciones: permite reducir lo que la Provincia debe pagar a Nación.':claim.kind==='acuerdo'?'El importe destacado corresponde a un acuerdo de pago con Nación. El detalle muestra la forma de cancelación prevista.':claim.kind==='pago'?'El importe destacado corresponde a un cobro informado: fondos que la Provincia ya recibió de Nación.':claim.state==='unavailable'?'No se pudo cargar la documentación de los fondos reclamados a Nación.':claim.kind==='sin_monto'?'Hay documentación sobre fondos reclamados o acuerdos con Nación, pero todavía no tenemos un importe publicado.':'La sección muestra los recursos recibidos de Nación. Todavía falta documentación para cuantificar los fondos pendientes.';
 const hasRank=Number.isInteger(c.rank)&&Number.isInteger(c.rankTotal)&&c.rank>0&&c.rank<=c.rankTotal;
 const rank=hasRank?`${province} ocupa el puesto ${c.rank} de ${c.rankTotal} en el ranking fiscal, que combina siete indicadores de las cuentas públicas.`:`${province} no tiene una posición comparable en el ranking fiscal actual.`;
 const result=(c.results||[]).find(m=>Number.isFinite(m.value)&&m.display&&m.period);
 const resultLabel=result?.id==='homicide_rate'?'Homicidios intencionales':result?.label?.replace(/\bNBI\b/g,'necesidades básicas insatisfechas');
 const resultValue=result?.display+(result?.id==='homicide_rate'&&!/habitantes/.test(result.display)?' habitantes':'');
 const resultFact=result?`${resultLabel}: ${resultValue} (${result.period}). Estos datos permiten mirar qué pasa con los servicios y las condiciones de vida.`:'El presupuesto muestra cuánto se gasta. Los indicadores de seguridad, educación y salud ayudan a ver qué resultados se obtienen.';
 const history=(c.history||[]).filter(r=>Number.isFinite(r.financial_pct)).slice().sort((a,b)=>a.period.localeCompare(b.period));
 const first=history[0],last=history.at(-1);
 const historyFact=history.length>1?`Entre ${readingPeriod(first.period)} y ${readingPeriod(last.period)}, el resultado financiero pasó de ${n(first.financial_pct)}% a ${n(last.financial_pct)}% de los ingresos. Cada punto suma doce meses.`:last?`Hay un dato de resultado financiero en ${readingPeriod(last.period)}: ${n(last.financial_pct)}% de los ingresos. Hace falta otro período para comparar su evolución.`:'Todavía faltan resultados comparables para describir la evolución de esta provincia.';
 const mapMetric=c.mapMetric==='primary_pct'?'antes de intereses':'después de intereses';
 const mapFact=`El mapa compara cómo cierran las cuentas ${mapMetric}${c.mapPeriod?' al '+readingPeriod(c.mapPeriod):''}, sumando doce meses por provincia.`+(Number.isFinite(c.mapValue)?` ${province}: ${n(c.mapValue)}% de los ingresos.`:' La provincia seleccionada no tiene dato en ese corte.');
 const national=c.national, nationalBalance=national?.metrics?.find(m=>m.label==='Resultado financiero mensual'&&m.unit==='millones de $');
 const nationalFact=Number.isFinite(nationalBalance?.value)?`En ${national.period_label||'el mes informado'}, el Sector Público Nacional no Financiero ${nationalBalance.value>0?'tuvo superávit: los ingresos cobrados superaron al gasto pagado, incluidos los intereses':nationalBalance.value<0?'tuvo déficit: los ingresos cobrados no cubrieron el gasto pagado, incluidos los intereses':'cerró en equilibrio: los ingresos cobrados igualaron al gasto pagado, incluidos los intereses'}.`:'La economía nacional influye en la recaudación provincial, el costo del crédito y la demanda de servicios públicos.';
 return {
  summary:[financial,buildFiscalSummaryReading(role,{rf,rp})],
  debt:[debtFact+' '+schedule,debtFocus],
  income:[own+' '+prices,choose(
   'Si los ingresos pierden contra la inflación, alcanzan para sostener menos servicios. Antes de ampliar un programa, importa saber si sus recursos van a mantenerse.',
   'Comparar ingresos y gastos de los mismos meses, ajustados por inflación. Si el gasto crece más que los recursos, se achica el margen para financiarlo.',
   'Que entren más pesos no significa que se pueda comprar más. Para explicar una mejora, hay que mostrar cuánto cambió la recaudación después de descontar la inflación.')],
  federal:[federalFact,choose(
   claim.kind==='credito_compensable'?'La compensación alivia obligaciones provinciales. La gestión debe identificar qué pagos se reducen y qué recursos quedan disponibles para otros destinos.':'Para sostener servicios y obras, importa cuánto se cobra y en qué fecha. La negociación debe traducirse en recursos que puedan incorporarse al presupuesto.',
   'Ordenar cada concepto por monto, forma y fecha de cancelación. Una transferencia incorpora fondos; una compensación cancela obligaciones.',
   'Un reclamo es lo solicitado; un acuerdo fija cómo cancelarlo y un cobro registra lo recibido. Explicar en qué etapa está cada concepto.')],
  comparison:[rank,choose(
   hasRank?'El puesto ayuda a ubicar la provincia. Para decidir qué mejorar, hay que abrir la comparación: cómo cierran las cuentas, cuánto depende de Nación y cuánto pesa la deuda.':'La comparación puede avanzar con los indicadores disponibles: cómo cierran las cuentas, cuánto depende de Nación y cuánto pesa la deuda. Completar esos datos permitirá ubicarla en el ranking.',
   'Usar provincias de estructura similar como referencia. El objetivo es identificar qué diferencia viene de los ingresos, del gasto o de los intereses y puede corregirse.',
   'El ranking compara cuentas públicas; no mide la calidad de todos los servicios. Un cambio de puesto también puede deberse a que otras provincias mejoraron o empeoraron.')],
  results:[resultFact,choose(
   'La gestión necesita elegir qué resultado mejorar, fijar una meta y seguir su evolución. Aumentar el gasto ayuda solamente si se traduce en un mejor servicio.',
   'Para cada meta, vincular presupuesto, ejecución y resultado. Eso permite revisar qué programas funcionan y cuánto cuesta sostenerlos.',
   'Cada indicador tiene su fecha. Una mejora muestra un cambio en el resultado, pero para atribuirlo a una política hay que explicar qué se hizo y cómo pudo influir.')],
  history:[historyFact,choose(
   history.length>1?'La curva permite ver si la mejora se sostiene o si el déficit se repite. Eso ayuda a distinguir una dificultad transitoria de un problema que exige cambios duraderos.':'Para distinguir un problema persistente de un cambio reciente, hacen falta varios períodos comparables. Completar la serie permitirá evaluar ese recorrido.',
   'El acumulado de doce meses suaviza los cambios estacionales. Compararlo con el trimestre ayuda a detectar un giro reciente antes de proyectar el presupuesto.',
   'Explicar de dónde parte la provincia y cómo llega al último dato. Un trimestre aislado y un acumulado de doce meses cuentan partes distintas de esa historia.')],
  map:[mapFact,choose(
   'Sirve para ubicar diferencias y elegir provincias con las que compararse. El tamaño del territorio no indica cuánta población vive allí ni cuántos recursos necesita.',
   'El porcentaje permite comparar provincias de distinto tamaño. Después hay que revisar los ingresos y gastos que explican cada resultado.',
   'Un saldo positivo indica superávit y uno negativo, déficit. El mapa muestra ese indicador, no una calificación general de cada gestión.')],
  nation:[nationalFact,choose(
   'Para la provincia, importa cómo la actividad y los precios afectan sus recursos. Menos recaudación o mayores costos pueden reducir el margen para sostener servicios y obras.',
   'El resultado después de intereses es un punto de partida. Para organizar el financiamiento también hay que sumar las devoluciones de capital y mirar las fechas de pago.',
   'El resultado mensual explica cómo cerró ese mes. El acumulado permite evaluar el año; la actividad y la inflación ayudan a entender qué está pasando con ingresos y gastos.')],
  operations:['Puede haber superávit y faltar dinero el día de un vencimiento: los ingresos y los pagos no siempre ocurren al mismo tiempo. La caja libre es el dinero disponible para usar, sin fondos reservados a un destino específico.',choose(
   'El escenario permite anticipar fechas en las que falta dinero y ordenar cómo cubrir salarios, servicios y deuda. El saldo depende de los ingresos y pagos que se carguen.',
   'Partir de la caja utilizable, sumar cobros y financiamiento, y restar pagos. Separar capital e intereses permite identificar qué genera el faltante y cuándo aparece.',
   'El escenario calcula qué pasaría con los supuestos cargados. No informa un saldo oficial ni demuestra que haya pagos incumplidos.')],
  guide:['El resultado fiscal dice si los ingresos cubren los gastos. La deuda dice cuánto se debe. La caja dice cuánto dinero puede usarse hoy. Cada dato responde una pregunta distinta.',choose(
   'Para decidir, unir esas tres miradas: qué recursos se generan, qué obligaciones vienen y qué servicios hay que sostener.',
   'Comparar siempre el mismo período y la misma unidad. Los pesos constantes descuentan inflación y permiten evaluar poder de compra.',
   'Empezar por el dato, explicar qué significa y después plantear la conclusión. Mantener visible el período evita comparar cifras que cuentan momentos distintos.')]
 };
}
function buildFiscalSummaryReading(profile,{rf=null,rp=null}={}){
 const role=normalizeReadingProfile(profile),choose=(g,m,p)=>({governor:g,hacienda:m,press:p}[role]);
 if(!Number.isFinite(rf))return 'Falta un resultado financiero comparable. Los ingresos observados ayudan a seguir la actividad, pero no alcanzan para saber cómo cierran las cuentas.';
 if(!Number.isFinite(rp))return 'El resultado financiero está disponible, pero falta el resultado antes de intereses. Ese dato permite distinguir cuánto del cierre se explica por el gasto de funcionamiento y cuánto por los intereses.';
 if(rf<0&&rp<0)return choose('Los ingresos no alcanzan para cubrir los gastos, incluso antes de pagar intereses. Para sostener servicios y obras, la prioridad es corregir esa diferencia y ordenar los pagos.','El déficit empieza antes de intereses. Hay que revisar la recaudación y el gasto primario —los gastos sin intereses—, además del costo del financiamiento.','El déficit no se explica solamente por los intereses: el gasto antes de intereses también supera a los ingresos. Esa es la clave para explicar por qué las cuentas cierran en rojo.');
 if(rf<0)return choose('Los ingresos alcanzan para el gasto antes de intereses, pero el costo financiero deja las cuentas en rojo. La prioridad es cubrir esa diferencia sin acumular atrasos.','El resultado primario no es negativo y el financiero sí: la diferencia aparece al pagar intereses. Revisar el costo y las condiciones del financiamiento.','Las cuentas pasan al déficit cuando se incorporan los intereses. Esa diferencia permite explicar qué parte del problema corresponde al costo financiero.');
 if(rp<0)return 'El resultado financiero no es negativo, pero el resultado primario sí. Hay que conciliar ambos conceptos antes de explicar el origen del saldo.';
 if(rf===0)return choose('Los ingresos y los gastos del período están equilibrados. Para sostener ese cierre, importa cómo evolucionan los recursos y qué obligaciones quedan pendientes.','El resultado financiero es cero. Revisar estacionalidad y obligaciones pendientes antes de incorporar gastos permanentes.','Los ingresos alcanzaron justo para cubrir el gasto, incluidos los intereses. Es un cierre en equilibrio.');
 return choose('Los ingresos alcanzan para cubrir los gastos y los intereses. Ese margen mejora el punto de partida para sostener servicios y obras. Antes de ampliarlos, conviene revisar los próximos vencimientos.','El superávit mejora el resultado fiscal. Para decidir su destino, contrastarlo con el dinero disponible, las devoluciones de capital y los pagos pendientes.','Los ingresos superaron al gasto, incluso después de pagar intereses. Las cuentas cierran con superávit; para evaluar los servicios hay que mirar también sus resultados.');
}
function debtRankingLabel(rank,total){
 if(!Number.isInteger(rank)||!Number.isInteger(total)||rank<1||rank>total)return 'Sin posición en el ranking actual.';
 const meaning=total===1?'única jurisdicción con dato':rank===total?'la mayor carga de deuda sobre ingresos':rank===1?'la menor carga de deuda sobre ingresos':'de menor a mayor carga de deuda sobre ingresos';
 return `Ranking provincial: puesto ${rank} de ${total} · ${meaning}.`;
}
function buildSummaryReading(profile,context={}){
 const base=buildFiscalSummaryReading(profile,context),{debtRank:rank,debtTotal:total}=context;
 if(!Number.isFinite(context.rf)||!Number.isInteger(rank)||!Number.isInteger(total)||total<2||rank<1||rank>total)return base;
 const high=rank>total*2/3,low=rank<=total/3;
 if(high)return base+' '+(rank===total?'Además, tiene la mayor carga de deuda sobre ingresos del conjunto comparado.':'Además, está entre las provincias con mayor carga de deuda sobre ingresos.')+' El calendario de vencimientos es clave para organizar la gestión.';
 if(low)return base+' '+(rank===1?'Tiene la menor carga de deuda sobre ingresos del conjunto comparado.':'Está entre las provincias con menor carga de deuda sobre ingresos.');
 return base+' La carga de deuda sobre ingresos se ubica en el tramo intermedio del conjunto comparado.';
}
function renderProfileReadings(){
 if(typeof document==='undefined'||typeof manifest==='undefined'||!manifest)return;
 const cross={...(crossFiscal?.[currentProvince]||{}),...(latestFiscalRanking?.[currentProvince]||{})};
 const q=dashboardPeriod==='quarter'?latestFiscalDetails?.quarters?.[currentProvince]:null;
 const rf=toN(q?q.financial_pct:cross.resultado_financiero_ltm_pct),rp=toN(q?q.primary_pct:cross.resultado_primario_ltm_pct);
 const debt=toN(currentProvince==='Buenos Aires'?pbaDebtProfile?.latest_stock?.debt_to_ltm_income_pct:cross.deuda_total_sobre_ingresos_pct);
 const kicker=document.querySelector('.gov-kicker');if(kicker)kicker.textContent=PROFILE_CONFIG[dashboardProfile].label;
 const headline=document.getElementById('governorRoomTitle');if(headline){headline.textContent=currentProvince+': '+(rf===null?'resultado fiscal sin dato comparable':rf<0?'las cuentas cierran con déficit':rf>0?'las cuentas cierran con superávit':'las cuentas cierran en equilibrio');headline.dataset.tone=rf===null?'neutral':rf<0?'negative':rf>0?'positive':'neutral';}
 const debtRank=toN(latestFiscalRanking?.[currentProvince]?.rank_deuda_total),debtTotal=Object.values(latestFiscalRanking||{}).filter(row=>toN(row.rank_deuda_total)!==null).length;
 const status=document.getElementById('governorStatus');if(status){status.textContent=rf===null?'Resultado comparable pendiente':q?'Resultado de enero–marzo de 2026':'Resultado de los últimos 12 meses al 31/03/2026';status.className='gov-status';}
 const debtData=typeof provincialServicesData!=='undefined'?provincialServicesData:null;
 const projection=debtData?.projections?.[currentProvince];
 const debtScheduleStatus=debtData?(projection?'verified':'missing'):'loading';
 const mapPeriod=document.getElementById('mapPeriod')?.value,mapMetric=document.getElementById('mapMetric')?.value;
 const context={province:currentProvince,rf,rp,debt,projection,debtScheduleStatus,
  period:q?'enero–marzo 2026':'últimos 12 meses al 31/03/2026',
  autonomy:toN(cross.autonomia_fiscal_pct),priceMode:displayMode,
  rank:isPartialStructural(cross)?null:toN(cross.ranking_general),rankTotal:structuralUniverseCount(),
  claim:NationClaims.summaryModel(reclamosNacionData,currentProvince),
  results:governmentResults?.provinces?.[currentProvince]?.pillars?.map(p=>p.metrics?.[0]).filter(Boolean),
  history:typeof fiscalHistory!=='undefined'?fiscalHistory?.rows?.filter(r=>r.province===currentProvince):[],
  mapPeriod,mapMetric,mapValue:typeof historyRow==='function'?historyRow(currentProvince,mapPeriod)?.[mapMetric]:null,
  national:nationalReadingData};
 const readings=buildProfileReadings(dashboardProfile,context);
 const targets={summary:'#governorRoom',debt:'#layer3',income:'#incomeView',federal:'#layer1',comparison:'#layer2',results:'#resultsView',history:'#fiscalHistoryPanel',map:'#fiscalMapPanel',nation:'#nationalPanel',operations:'#operationsPanel',guide:'#fiscalGuide'};
 for(const [key,selector] of Object.entries(targets)){
  const host=document.querySelector(selector);if(!host)continue;
  let card=host.querySelector(':scope > .profile-reading');
  if(!card){
   card=document.createElement('section');card.className='profile-reading';card.dataset.reading=key;
   const h=document.createElement('h3'),p=document.createElement('p'),focus=document.createElement('p');focus.className='profile-conclusion';card.append(h,p,focus);
   const anchor=host.tagName==='DETAILS'?host.querySelector(':scope > summary'):key==='summary'?host.querySelector('.gov-head'):host.firstElementChild;
   if(anchor)anchor.after(card);else host.prepend(card);
  }
  card.dataset.profile=dashboardProfile;card.children[0].textContent='La lectura central';
  card.children[1].textContent=key==='summary'?buildSummaryReading(dashboardProfile,{rf,rp,debtRank,debtTotal}):readings[key][0];
  card.children[2].textContent=key==='summary'?'':readings[key][1];
  card.children[2].hidden=key==='summary';
  if(key==='summary')host.querySelector('.gov-head')?.after(card);
 }
 const picker=document.getElementById('mobileViewPicker');if(picker){for(const option of picker.options){if(VIEW_LABELS[option.value])option.hidden=!enabledDashboardViews().has(option.value);}if(!picker.value.startsWith('open'))picker.value=dashboardView;}
}
if(typeof module!=='undefined')module.exports={normalizeReadingProfile,buildProfileReadings,buildSummaryReading,debtRankingLabel};
let nationalReadingData=null;

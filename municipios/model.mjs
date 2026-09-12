const metric = (id, label, group, field, unit, period, note, ascending = true) => ({id, label, group, field, unit, period, note, ascending});
export const METRICS = [
  {...metric('presupuesto-total', 'Presupuesto total', 'Presupuesto', 'annualBudget.current', 'millions', 'Ejercicio 2026 · vigente al 30 de junio', 'Autorización anual para gastar, en pesos corrientes. No es gasto ejecutado ni dinero disponible. Los organismos y servicios incluidos pueden diferir entre municipios.', false), budget:true},
  {...metric('presupuesto-habitante', 'Presupuesto por habitante', 'Presupuesto', 'annualBudget.current', 'money', 'Ejercicio 2026 · vigente al 30 de junio · población 2022', 'Presupuesto anual dividido por la población del Censo 2022. Ayuda a comparar municipios de distinto tamaño; los organismos y servicios incluidos pueden diferir. No es dinero que recibe cada vecino.', false), budget:true, perCapita:true},
  metric('recursos', 'Cambio de transferencias', 'Recursos', 'variacion_transferencias_real_pct', '%', 'Ene–jul 2026 vs. ene–jul 2025', 'Transferencias provinciales totales, descontando la inflación mes a mes. No son todos los ingresos municipales.'),
  metric('por-habitante', 'Transferencias por habitante', 'Recursos', 'transferencias_por_habitante_base2022_ars_jul26', 'money', 'Ene–jul 2026 · población 2022', 'Pesos de julio de 2026 por habitante del Censo 2022. El reparto también contempla servicios y superficie.', false),
  metric('copart', 'Cambio de coparticipación', 'Recursos', 'variacion_copart_real_pct', '%', 'Ene–jul 2026 vs. ene–jul 2025', 'Variación real de la coparticipación bruta. Los demás fondos se contabilizan por separado.'),
  metric('reparto', 'Cambio de participación', 'Recursos', 'cambio_participacion_copart_pp', 'pp', 'Ene–jul 2026 vs. ene–jul 2025', 'Participación observada en la coparticipación bruta. No equivale a una tabla oficial de CUD validada.', false),
  metric('empleo', 'Cambio del empleo', 'Empleo', 'empleo_promedio_cambio_2024_2025_pct', '%', 'Promedio de 2025 vs. 2024', 'Empleo privado registrado por lugar del establecimiento. No es la tasa de empleo de los residentes.', false),
  metric('puestos', 'Puestos ganados o perdidos', 'Empleo', 'empleos_cambio_dic2023_dic2025', 'jobs', 'Diciembre 2025 vs. diciembre 2023', 'Cambio neto de puestos privados formales. Las variaciones absolutas reflejan también el tamaño del municipio.'),
  metric('caida-empleo', 'Cambio del empleo desde 2023', 'Empleo', 'empleo_cambio_dic2023_dic2025_pct', '%', 'Diciembre 2025 vs. diciembre 2023', 'Cambio porcentual de puestos privados formales entre dos cortes de diciembre.'),
  metric('densidad-empleo', 'Puestos por 1.000 habitantes', 'Empleo', 'empleos_formales_dic2025_por_1000_hab_base2022', 'density', 'Diciembre 2025 · población 2022', 'Puestos localizados por 1.000 habitantes censales. Incluye trabajadores que pueden vivir en otro municipio.', false),
  metric('salarios', 'Cambio del salario bruto real', 'Empleo', 'salario_real_promedio_cambio_2023_2025_pct', '%', 'Promedio mensual 2025 vs. 2023', 'Salario bruto promedio del empleo privado registrado, ajustado por inflación. Incluye aguinaldo y otros pagos; no es sueldo de bolsillo. La composición del empleo modifica el promedio.', false),
  metric('salario-nivel', 'Salario bruto promedio', 'Empleo', 'community.wage.annual.2025.real', 'money', 'Promedio mensual de 2025 · pesos de julio de 2026', 'OEDE/SIPA e IPC nacional INDEC: cada mes se ajusta por inflación y luego se promedian los doce meses. Empleo privado formal por lugar del establecimiento; incluye aguinaldo y otros pagos. No es sueldo de bolsillo, salario municipal ni ingreso medio de los vecinos.', false),
  metric('masa-salarial', 'Cambio de masa salarial', 'Empleo', 'masa_salarial_formal_aprox_cambio_2023_2025_pct', '%', 'Año 2025 vs. año 2023', 'Aproximación: puestos por remuneración media, sumados mes a mes a precios constantes. No mide ventas locales.'),
  metric('industria', 'Peso de la industria', 'Economía', 'peso_industria_empleo_formal_dic2025_pct', '%', 'Diciembre 2025', 'Empleo manufacturero sobre empleo privado formal total. Los registros reservados quedan sin dato.', false),
  metric('industria-cambio', 'Cambio del empleo industrial', 'Economía', 'empleo_industrial_cambio_dic2023_dic2025_pct', '%', 'Diciembre 2025 vs. diciembre 2023', 'Variación de puestos manufactureros; se comparan solamente municipios con ambos cortes publicados.'),
  metric('actividad', 'Crecimiento de la actividad', 'Economía', 'pbg_real_cambio_2021_2023_pct', '%', 'PBG 2023 vs. 2021', 'Valor de bienes y servicios producidos en el municipio, estimado por la DPE a precios constantes de 2004 (sin inflación). No es recaudación ni presupuesto. Último año: 2023.', false),
  metric('carencias', 'Hogares con carencias · %', 'Población', 'hogares_nbi_2022_pct', '%', 'Censo 2022', 'Hogares con necesidades básicas insatisfechas (NBI). Son carencias estructurales, no pobreza monetaria actual.', false),
  metric('hogares', 'Hogares con carencias · cantidad', 'Población', 'hogares_nbi_2022', 'households', 'Censo 2022', 'Número de hogares con NBI. Una mayor cantidad puede reflejar una población más grande.', false),
  metric('poblacion', 'Crecimiento de población', 'Población', 'crecimiento_poblacion_2010_2022_pct', '%', 'Censos 2010–2022', 'Chascomús y Lezama quedan fuera hasta homologar la separación territorial en la base de 2010.', false),
  metric('salud', 'Sin obra social, prepaga ni plan estatal', 'Población', 'community.health.withoutCoveragePct', '%', 'Censo 2022 · población en viviendas particulares', 'INDEC/DPE: personas sin obra social, prepaga ni plan estatal, sobre la población en viviendas particulares. Pueden atenderse en el sistema público; no significa falta de atención médica. Es una referencia de 2022, no una medición actual.', false),
  metric('hacinamiento', 'Hogares con hacinamiento crítico', 'Población', 'community.crowding.over3PersonsPerRoomPct', '%', 'Censo 2022 · porcentaje de hogares', 'INDEC/DPE: hogares con más de tres personas por cuarto, sobre el total de hogares. Muestra una carencia habitacional; no equivale a pobreza por ingresos ni describe por sí sola la situación actual.', false),
  metric('sucursales', 'Sucursales por habitante', 'Finanzas', 'sucursales_por_10000_hab_base2022', 'branches', '2024 · población 2022', 'Locales financieros por 10.000 habitantes. No incluye una medición de cobertura bancaria digital.', false),
  metric('credito', 'Cambio real del crédito', 'Finanzas', 'prestamos_real_cambio_2023_2024_pct', '%', 'Diciembre 2024 vs. diciembre 2023', 'Préstamos registrados por localización financiera, deflactados con IPC de cierre. No identifica solamente pymes o residentes.', false),
  metric('prestamos-depositos', 'Préstamos sobre depósitos', 'Finanzas', 'prestamos_sobre_depositos_2024_pct', '%', 'Cuarto trimestre 2024', 'Relación de saldos por localización financiera. No mide fuga de ahorros ni permite seguir el destino de cada depósito.', false),
  metric('deudas-atrasadas', 'Personas con deudas atrasadas', 'Finanzas', 'community.debt.peopleInArrearsPct', '%', 'Julio de 2026 · sobre personas con deuda registrada', 'CEC/FES, Mapa de la Deuda, sobre registros del BCRA: personas en mora divididas por personas con deuda registrada. La fuente cuenta las situaciones 3, 4 y 5; no incluye todos los atrasos más cortos. No es el porcentaje de todos los habitantes ni deuda del gobierno municipal. La localización sigue el criterio del proveedor.', false),
  metric('deficit', 'Resultado sobre ingresos', 'Cuentas', 'fiscal.resultado_sobre_ingresos_pct', '%', 'Acumulado al 30 de junio de 2026', 'Muestra parcial con cierre en junio. Negativo: déficit; positivo: superávit. Recursos percibidos menos gastos devengados, sin aplicaciones financieras. Los servicios y organismos incluidos pueden diferir. No es caja libre.'),
  metric('resultado-pesos', 'Resultado en pesos', 'Cuentas', 'fiscal.resultado_financiero', 'millions', 'Acumulado al 30 de junio de 2026', 'Resultado financiero en pesos corrientes. El monto refleja también el tamaño del municipio. La muestra no permite identificar el mayor déficit de los 135.'),
  metric('inversion', 'Inversión sobre gasto', 'Cuentas', 'fiscal.capital_sobre_gasto_pct', '%', 'Acumulado al 30 de junio de 2026', 'Gasto de capital sobre gasto total sin aplicaciones financieras. Incluye inversión y transferencias de capital; no mide avance físico ni calidad de las obras.', false),
  metric('personal', 'Personal sobre gasto corriente', 'Cuentas', 'fiscal.personal_sobre_gasto_corriente_pct', '%', 'Acumulado al 30 de junio de 2026', 'Gasto devengado en personal sobre gasto corriente. Los servicios prestados, la tercerización y los organismos incluidos afectan la comparación.', false),
  metric('ahorro-corriente', 'Ahorro corriente sobre ingresos', 'Cuentas', 'fiscal.ahorro_sobre_ingresos_corrientes_pct', '%', 'Acumulado al 30 de junio de 2026', 'Ingresos corrientes percibidos menos gastos corrientes devengados, como porcentaje de los ingresos corrientes. Muestra el margen antes de la cuenta de capital. No es dinero libre.', false),
  metric('inversion-habitante', 'Inversión por habitante', 'Cuentas', 'fiscal.capital_por_habitante_base2022_ars_corrientes', 'money', 'Acumulado al 30 de junio de 2026 · población 2022', 'Gasto de capital en pesos corrientes por habitante del Censo 2022. La cobertura institucional y los servicios a cargo pueden diferir.', false),
  {...metric('ingresos-habitante', 'Ingresos por habitante', 'Cuentas', 'fiscal.ingresos_totales', 'money', 'Acumulado al 30 de junio de 2026 · población 2022', 'Recursos corrientes y de capital percibidos, divididos por habitantes del Censo 2022. Pesos corrientes del período informado, sin anualizar. No incluye fuentes financieras; los organismos y servicios incluidos pueden diferir.', false), perCapita:true},
  {...metric('gasto-habitante', 'Gasto por habitante', 'Cuentas', 'fiscal.gastos_totales', 'money', 'Acumulado al 30 de junio de 2026 · población 2022', 'Gastos corrientes y de capital devengados, divididos por habitantes del Censo 2022. Pesos corrientes del período informado, sin anualizar. Devengado significa que se generó la obligación de pagar; no incluye aplicaciones financieras. Más gasto no prueba mejores servicios.', false), perCapita:true},
  metric('robos', 'Robos por 100.000 habitantes', 'Seguridad', 'community.crime.2025.robberyRate', 'rate', 'Año 2025 · tasa oficial SNIC', 'SNIC: robos registrados, incluidos los agravados y excluidas las tentativas. La tasa usa la población de referencia oficial del SNIC, no el Censo 2022 del tablero. No incluye todos los delitos ni mide percepción de inseguridad. En municipios pequeños, pocos hechos pueden cambiar mucho la tasa.', false),
  metric('transparencia', 'Publicación de información fiscal', 'Transparencia', 'transparency.score', 'score', 'ASAP · relevamiento del 1 al 8 de mayo de 2026', 'Puntaje de 0 a 100 por publicación, actualidad, integridad y acceso a información fiscal. Describe lo observado por ASAP en esa fecha; no mide el resultado fiscal ni acredita la calidad de gestión.', false),
  metric('cambio-transparencia', 'Cambio del puntaje', 'Transparencia', 'transparency.change', 'points', 'ASAP · mayo de 2026 vs. noviembre de 2025', 'Diferencia en puntos del índice publicado. Cada edición exige información del período correspondiente: una baja puede reflejar documentos que quedaron desactualizados. No mide cambios en la situación financiera.', false)
];
export const TRANSPARENCY_COMPONENTS = [
  {id:'presupuesto',label:'Presupuesto',max:30},
  {id:'situacion_economico_financiera',label:'Situación económica y financiera',max:35},
  {id:'ejecucion',label:'Ejecución de ingresos y gastos',max:10},
  {id:'gasto_finalidad_funcion',label:'Gasto por finalidad y función',max:10},
  {id:'deuda',label:'Información de deuda',max:10},
  {id:'accesibilidad',label:'Facilidad de acceso',max:5}
];
export function transparencyStatus(component, score) {
  if(!finite(score))return 'Sin dato';
  if(component.id==='accesibilidad')return score===5?'Acceso fácil en el relevamiento.':'Acceso confuso o nulo según ASAP.';
  if(component.id==='presupuesto')return score===30?'Presupuesto vigente publicado.':score===20?'Presupuesto publicado de forma parcial.':score===0?'No recibió puntos por presupuesto vigente.':'Puntaje publicado fuera de la escala metodológica.';
  return score===component.max?'Información completa y al día en el relevamiento.':score===0?'Sin puntaje: información ausente o fuera del período admitido.':'Información parcial o de un trimestre anterior.';
}
export const VALID_VIEWS = ['panorama', 'rankings', 'recursos', 'empleo', 'simular', 'informe'];
export const BUDGET_BASES = {
  junio:{field:'current',asOf:'2026-06-30',label:'Vigente · junio 2026',period:'Ejercicio 2026 · vigente al 30 de junio',note:'Compara presupuestos anuales vigentes en la misma fecha: 30 de junio de 2026. Quedan fuera los que sólo tienen otro corte o el presupuesto original.'},
  vigente:{field:'current',label:'Vigente · último corte 2026',period:'Ejercicio 2026 · último vigente disponible de cada municipio',note:'Amplía la muestra usando el último presupuesto vigente verificado de 2026. Los cortes son distintos: mirá la fecha debajo de cada municipio. No representa una comparación a una misma fecha.'},
  original:{field:'original',label:'Original · 2026',period:'Ejercicio 2026 · presupuesto original',note:'Compara la autorización inicial para 2026, antes de las modificaciones del año. La fecha debajo de cada municipio corresponde al documento consultado.'}
};
export function rankingMetric(meta, basis='junio') {
  if(!meta.budget)return meta;
  const budgetBasis=Object.hasOwn(BUDGET_BASES,basis)?basis:'junio',config=BUDGET_BASES[budgetBasis];
  return {...meta,budgetBasis,period:config.period+(meta.perCapita?' · población 2022':'')};
}
export function metricValue(m, meta) {
  let value;
  if(meta.budget){
    const b=m.annualBudget,config=BUDGET_BASES[meta.budgetBasis]||BUDGET_BASES.junio;
    if(!b||b.year!==2026||(config.asOf&&b.asOf!==config.asOf))return null;
    value=b[config.field];
  }else value=meta.field.split('.').reduce((v,k)=>v?.[k],m);
  if(!finite(value))return null;
  return meta.perCapita?(finite(m.poblacion_2022)&&m.poblacion_2022>0?value/m.poblacion_2022:null):value;
}
export function metricExportUnit(meta) {
  if(meta.budget||meta.perCapita)return meta.perCapita?'ARS corrientes por habitante Censo 2022':'ARS corrientes';
  if(meta.id==='salario-nivel')return 'ARS de julio de 2026';
  return ({millions:'ARS corrientes',money:'ARS (ver período y criterio)',rate:'hechos por 100.000 habitantes',density:'puestos por 1.000 habitantes',branches:'locales por 10.000 habitantes',jobs:'puestos',households:'hogares',score:'puntaje sobre 100',points:'puntos'})[meta.unit]||meta.unit;
}
export function rankingExportRows(ranked,meta) {
  return [['Municipio','Puesto','Valor','Unidad','Período','Municipios con datos','Criterio','Tipo de presupuesto','Corte o fecha del documento','Cobertura institucional','Documento'],...ranked.map(r=>{
    const b=meta.budget?r.m.annualBudget:null,config=meta.budget?(BUDGET_BASES[meta.budgetBasis]||BUDGET_BASES.junio):null;
    return [r.m.municipio,r.rank,r.value,metricExportUnit(meta),meta.period,ranked.length,meta.note+(config?' '+config.note:''),b?(config.field==='original'?'Original':'Vigente'):'',b?.asOf??'',b?.scope??(meta.group==='Cuentas'?r.m.fiscal?.scope:'')??'',b?.documents?.map(d=>d.url).join(' | ')??''];
  })];
}
export function finite(v) { return typeof v === 'number' && Number.isFinite(v); }
export function rankMunicipalities(rows, meta, ascending = meta.ascending) {
  const valid = rows.map(m => ({m, value:metricValue(m, meta)})).filter(r => finite(r.value));
  valid.sort((a,b) => (ascending ? a.value-b.value : b.value-a.value) || a.m.municipio.localeCompare(b.m.municipio,'es'));
  let rank=0, previous;
  return valid.map((r,i) => { if(i===0 || r.value!==previous) rank=i+1; previous=r.value; return {...r, rank}; });
}
export function peers(rows, selected, enabled) { return enabled ? rows.filter(m=>m.poblacion_2022 >= selected.poblacion_2022/2 && m.poblacion_2022 <= selected.poblacion_2022*2) : rows; }
export function simulate(m, shockPercent) {
  const shock=Math.min(20,Math.max(0,Number(shockPercent)||0));
  const baseline=m.copart_2026_ene_jul_ars_jul26;
  const loss=baseline*shock/100;
  return {shock,baseline,loss,after:baseline-loss,perCapita:loss/m.poblacion_2022};
}
export function csv(rows) {
  return '\ufeff'+rows.map(row=>row.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(';')).join('\r\n');
}
export function fiscalPeriods(m) {
  const unique=new Map();
  for(const f of [m.fiscal,m.fiscalOther,...(m.management?.history||[])].filter(Boolean)) {
    const key=f.inicio+'/'+f.fin;if(!unique.has(key))unique.set(key,f);
  }
  return [...unique.values()].sort((a,b)=>b.fin.localeCompare(a.fin)||a.inicio.localeCompare(b.inicio));
}
export function managementExportRows(m) {
  if(!m.management)return [];
  const g=m.management,rows=[];
  const add=(label,value,period,note='')=>{if(finite(value))rows.push([m.municipio,label,value,'ARS corrientes',period,note]);};
  const b=g.budget,p=b.inicio+' / '+b.fin;
  for(const [key,label] of Object.entries({original:'Presupuesto original',modifications:'Modificaciones presupuestarias',current:'Presupuesto vigente',received:'Recursos presupuestarios cobrados',accrued:'Gastos presupuestarios devengados',paid:'Gastos presupuestarios pagados',unpaid:'Gastos del período devengados y no pagados'}))add(label,b[key],p,'El presupuesto vigente es anual. La ejecución incluye operaciones financieras.');
  for(const r of b.objects)for(const [key,label] of [['current','Presupuesto vigente'],['accrued','Devengado'],['paid','Pagado']])add(r.label+' · '+label,r[key],p);
  for(const r of b.receipts)add(b.receiptTitle+' · '+r.label,r.received,p);
  for(const [key,label] of Object.entries({closing:'Saldo de tesorería',available:'Disponibilidades',transitory:'Movimientos transitorios',budgetCash:'Cuentas presupuestarias',unearmarkedAccounts:'Cuentas sin afectación',earmarkedAccounts:'Cuentas con afectación',thirdPartyAndSpecial:'Terceros y cuentas especiales',liabilities:'Pasivos contables',currentLiabilities:'Pasivos corrientes',nonCurrentLiabilities:'Pasivos no corrientes'}))add(label,g.treasury[key],g.treasury.date,'Los saldos no equivalen a caja libre; no sumar categorías que se contienen.');
  if(g.debt){for(const [key,label] of [['consolidated','Deuda consolidada'],['floating','Deuda flotante'],['current','Deuda consolidada corriente'],['nonCurrent','Deuda consolidada no corriente']])add(label,g.debt[key],g.debt.date);for(const r of g.debt.floatingHistory)add('Deuda flotante histórica',r.floating,r.year+'-12-31','Importe publicado redondeado a pesos enteros.');}
  for(const r of g.banking.records){for(const [key,label] of [['loans','Préstamos bancarios · actualización BCRA'],['deposits','Depósitos bancarios · actualización BCRA']]){
    rows.push([m.municipio,label,r[key]??null,'ARS corrientes',r.date,g.banking.note]);
    rows.push([m.municipio,label+' · ajustados por inflación',r[key+'Real']??null,'ARS de julio de 2026',r.date,'IPC nacional del mes de cierre; misma localización financiera.']);
  }}
  return rows;
}
export function annualBudgetExportRows(m) {
  const b=m.annualBudget;
  if(!b)return [[m.municipio,'Presupuesto anual',null,'ARS corrientes','Sin ejercicio verificado','Pendiente de documento oficial; no equivale a cero.']];
  const period=`Ejercicio ${b.year} · documento o corte ${b.asOf}`;
  const note=`Autorización anual; no es gasto ejecutado ni caja libre. ${b.scope} ${b.documents.map(d=>d.url).join(' | ')}`;
  return [['Presupuesto anual original',b.original,'ARS corrientes'],['Presupuesto anual vigente',b.current,'ARS corrientes'],['Presupuesto anual por habitante',b.perCapita,'ARS corrientes por habitante Censo 2022']].map(([label,value,unit])=>[m.municipio,label,value??null,unit,period,label.endsWith('por habitante')?`Presupuesto ${b.basis==='current'?'vigente':'original'} dividido por ${m.poblacion_2022} habitantes del Censo 2022. ${note}`:note]);
}
export function fiscalExportRows(m) {
  const fields=[['ingresos_corrientes','Ingresos corrientes'],['ingresos_capital','Recursos de capital'],['ingresos_totales','Ingresos totales'],['gastos_corrientes','Gastos corrientes'],['gastos_capital','Gastos de capital'],['gastos_totales','Gastos totales'],['resultado_financiero','Resultado financiero'],['personal_devengado','Personal devengado']];
  const rows=fiscalPeriods(m).flatMap(f=>fields.map(([key,label])=>[m.municipio,label,f[key]??null,'ARS corrientes',`${f.inicio} / ${f.fin}`,`${f.scope||'Cuenta municipal publicada.'} ${f===m.fiscal?'Período del ranking fiscal.':'Fuera del período del ranking fiscal.'}`]));
  const e=m.fiscalExecution;
  if(e){
    const budgetFields=[['presupuesto_vigente','Presupuesto vigente'],['recursos_presupuestarios_percibidos','Recursos presupuestarios cobrados'],['gastos_presupuestarios_devengados','Gastos presupuestarios devengados'],['gastos_presupuestarios_pagados','Gastos presupuestarios pagados'],['devengado_no_pagado_del_periodo','Gastos del período devengados y no pagados']];
    rows.push(...budgetFields.map(([key,label])=>[m.municipio,label,e[key]??null,'ARS corrientes',`${e.inicio} / ${e.fin}`,key==='presupuesto_vigente'?'Autorización anual vigente al cierre informado.':'Ejecución presupuestaria del período. Incluye operaciones financieras; no integra el ranking fiscal ni mide deuda total.']));
  }
  return rows.concat(managementExportRows(m));
}
export function readState(search, municipalities, savedId) {
  const p=new URLSearchParams(search), id=p.get('municipio') || savedId;
  return {id:municipalities.some(m=>m.id===id)?id:'06805',view:VALID_VIEWS.includes(p.get('vista'))?p.get('vista'):'panorama',metric:METRICS.some(m=>m.id===p.get('indicador'))?p.get('indicador'):'recursos',budgetBasis:Object.hasOwn(BUDGET_BASES,p.get('presupuesto'))?p.get('presupuesto'):'junio'};
}

export function adjustPrice(value, period, base, indices) {
  if (!finite(value) || !finite(indices?.[period]) || indices[period] <= 0 || !finite(indices?.[base]) || indices[base] <= 0) return null;
  return value * indices[base] / indices[period];
}

export function priceComparisons(m, mode, base, deflator) {
  const real = mode === 'real', ix = deflator.indices;
  const atBase = value => real ? adjustPrice(value, '2026-07', base, ix) : value;
  const stock = (value, period) => real ? adjustPrice(value, period, base, ix) : value;
  const rows = [];
  for (const [prefix, label] of [['transferencias','Transferencias provinciales'],['copart','Coparticipación bruta']]) {
    const key = year => `${prefix}_${year}_ene_jul_ars${real ? '_jul26' : ''}`;
    rows.push({id:prefix,label,previous:atBase(m[key(2025)]),current:atBase(m[key(2026)]),previousPeriod:'Enero–julio de 2025',currentPeriod:'Enero–julio de 2026',unit:'millions',method:'El ajuste real se hace mes a mes, antes de sumar los siete meses.'});
  }
  const wage = m.community.wage.annual;
  rows.push({id:'salario',label:'Salario bruto mensual promedio',previous:atBase(wage['2024'][real?'real':'nominal']),current:atBase(wage['2025'][real?'real':'nominal']),previousPeriod:'Promedio de 2024',currentPeriod:'Promedio de 2025',unit:'money',method:'Para calcular el promedio real se ajusta cada mes y luego se promedian los doce meses. Incluye aguinaldo y otros pagos; no es salario de bolsillo.'});
  for (const [prefix,label] of [['prestamos','Préstamos bancarios'],['depositos','Depósitos bancarios']]) {
    rows.push({id:prefix,label,previous:stock(m[`${prefix}_2023_ars`],'2023-12'),current:stock(m[`${prefix}_2024_ars`],'2024-12'),previousPeriod:'Cierre de 2023',currentPeriod:'Cierre de 2024',unit:'millions',method:'El ajuste real de los saldos usa el IPC del cierre. Localización bancaria: no identifica exclusivamente residentes ni pymes.'});
  }
  rows.push({id:'deuda-personas',label:'Deuda registrada de las personas',previous:null,current:stock(m.community.debt.debtARS,m.community.debt.period),previousPeriod:null,currentPeriod:'Julio de 2026',unit:'millions',method:'Relevamiento externo CEC/FES basado en el BCRA. Hay un solo corte incorporado: no permite calcular una variación. No es deuda del gobierno municipal.'});
  return rows.map(row=>({...row,change:finite(row.previous)&&row.previous!==0&&finite(row.current)?(row.current/row.previous-1)*100:null}));
}

export function municipalContextExportRows(m) {
  const rows=[], add=(label,value,unit,period,note)=>rows.push([m.municipio,label,value??null,unit,period,note]);
  add('Población',m.poblacion_2022,'personas','Censo 2022','INDEC/DPE.');
  add('Superficie',m.superficie_km2,'km²','Base territorial DPE','No es superficie urbanizada.');
  add('Total de hogares',m.hogares_2022,'hogares','Censo 2022','Denominador de NBI y hacinamiento.');
  for(const s of m.sectors)add('Empleo privado formal: '+s.name,s.jobs,'puestos','2025-12','OEDE; lugar del establecimiento. Los registros reservados quedan vacíos.');
  for(const y of [2021,2022,2023])add('Producto bruto municipal',m[`pbg_constante_2004_${y}_ars`],'ARS constantes de 2004',String(y),'DPE; producción del territorio, no ingresos municipales.');
  for(const y of [2023,2024])for(const [key,label] of [['prestamos','Préstamos bancarios'],['depositos','Depósitos bancarios']])add(label,m[`${key}_${y}_ars`],'ARS corrientes',`Cierre ${y}`,'DPE/BCRA; localización financiera, no deuda exclusiva de residentes.');
  for(const [y,w] of Object.entries(m.community.wage.annual)){
    add('Salario bruto mensual promedio',w.nominal,'ARS corrientes',y,'OEDE/SIPA; promedio de 12 meses, incluye aguinaldo.');
    add('Salario bruto mensual promedio ajustado',w.real,'ARS de julio de 2026',y,'OEDE/SIPA e INDEC; ajuste mensual antes de promediar.');
  }
  for(const [p,w] of Object.entries(m.community.wage.months)){
    add('Salario bruto mensual',w.nominal,'ARS corrientes',p,'OEDE/SIPA; bruto, incluye pagos estacionales.');
    add('Salario bruto mensual ajustado',w.real,'ARS de julio de 2026',p,'OEDE/SIPA e IPC nacional INDEC.');
  }
  const h=m.community.health;
  add('Personas sin obra social, prepaga ni plan estatal',h.withoutCoverage,'personas','Censo 2022','DPE/INDEC; no significa quedar sin acceso al sistema público.');
  add('Población en viviendas particulares',h.populationPrivateDwellings,'personas','Censo 2022','Denominador del indicador de cobertura de salud.');
  add('Sin cobertura de salud',h.withoutCoveragePct,'%','Censo 2022','Sobre población en viviendas particulares.');
  add('Hogares con más de tres personas por cuarto',m.community.crowding.over3PersonsPerRoomPct,'%','Censo 2022','DPE/INDEC; denominador: hogares.');
  for(const [y,c] of Object.entries(m.community.crime))for(const [key,label,unit] of [['homicideVictims','Víctimas de homicidio doloso','personas'],['homicideRate','Tasa de víctimas de homicidio doloso','por 100.000 habitantes'],['robberies','Robos registrados','hechos'],['robberyRate','Tasa de robos registrados','por 100.000 habitantes'],['thefts','Hurtos registrados','hechos'],['theftRate','Tasa de hurtos registrados','por 100.000 habitantes']])add(label,c[key],unit,y,'SNIC; hechos registrados, tasas oficiales con su propia población de referencia.');
  const d=m.community.debt;
  for(const [key,label,unit] of [['peopleWithDebt','Personas con deuda','personas'],['peopleInArrears','Personas en mora','personas'],['peopleInArrearsPct','Personas en mora sobre personas con deuda','%'],['debtARS','Deuda total registrada de personas','ARS corrientes'],['debtInArrearsARS','Deuda de personas en mora','ARS corrientes'],['debtInArrearsPct','Deuda en mora sobre deuda total','%'],['averageDebtARS','Deuda promedio por persona con deuda','ARS corrientes']])add(label,d[key],unit,d.period,'CEC/FES, Mapa de la Deuda sobre base BCRA. Localización del proveedor; no describe a toda la población ni a hogares.');
  return rows;
}

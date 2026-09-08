const metric = (id, label, group, field, unit, period, note, ascending = true) => ({id, label, group, field, unit, period, note, ascending});
export const METRICS = [
  metric('recursos', 'Cambio de transferencias', 'Recursos', 'variacion_transferencias_real_pct', '%', 'Ene–jul 2026 vs. ene–jul 2025', 'Transferencias provinciales totales, descontando la inflación mes a mes. No son todos los ingresos municipales.'),
  metric('por-habitante', 'Transferencias por habitante', 'Recursos', 'transferencias_por_habitante_base2022_ars_jul26', 'money', 'Ene–jul 2026 · población 2022', 'Pesos de julio de 2026 por habitante del Censo 2022. El reparto también contempla servicios y superficie.', false),
  metric('copart', 'Cambio de coparticipación', 'Recursos', 'variacion_copart_real_pct', '%', 'Ene–jul 2026 vs. ene–jul 2025', 'Variación real de la coparticipación bruta. Los demás fondos se contabilizan por separado.'),
  metric('reparto', 'Cambio de participación', 'Recursos', 'cambio_participacion_copart_pp', 'pp', 'Ene–jul 2026 vs. ene–jul 2025', 'Participación observada en la coparticipación bruta. No equivale a una tabla oficial de CUD validada.', false),
  metric('empleo', 'Cambio del empleo', 'Empleo', 'empleo_promedio_cambio_2024_2025_pct', '%', 'Promedio de 2025 vs. 2024', 'Empleo privado registrado por lugar del establecimiento. No es la tasa de empleo de los residentes.', false),
  metric('puestos', 'Puestos ganados o perdidos', 'Empleo', 'empleos_cambio_dic2023_dic2025', 'jobs', 'Diciembre 2025 vs. diciembre 2023', 'Cambio neto de puestos privados formales. Las variaciones absolutas reflejan también el tamaño del municipio.'),
  metric('caida-empleo', 'Cambio del empleo desde 2023', 'Empleo', 'empleo_cambio_dic2023_dic2025_pct', '%', 'Diciembre 2025 vs. diciembre 2023', 'Cambio porcentual de puestos privados formales entre dos cortes de diciembre.'),
  metric('densidad-empleo', 'Puestos por 1.000 habitantes', 'Empleo', 'empleos_formales_dic2025_por_1000_hab_base2022', 'density', 'Diciembre 2025 · población 2022', 'Puestos localizados por 1.000 habitantes censales. Incluye trabajadores que pueden vivir en otro municipio.', false),
  metric('salarios', 'Cambio del salario real', 'Empleo', 'salario_real_promedio_cambio_2023_2025_pct', '%', 'Promedio mensual 2025 vs. 2023', 'Remuneración media privada formal, ajustada por IPC. La composición del empleo también modifica el promedio.', false),
  metric('masa-salarial', 'Cambio de masa salarial', 'Empleo', 'masa_salarial_formal_aprox_cambio_2023_2025_pct', '%', 'Año 2025 vs. año 2023', 'Aproximación: puestos por remuneración media, sumados mes a mes a precios constantes. No mide ventas locales.'),
  metric('industria', 'Peso de la industria', 'Economía', 'peso_industria_empleo_formal_dic2025_pct', '%', 'Diciembre 2025', 'Empleo manufacturero sobre empleo privado formal total. Los registros reservados quedan sin dato.', false),
  metric('industria-cambio', 'Cambio del empleo industrial', 'Economía', 'empleo_industrial_cambio_dic2023_dic2025_pct', '%', 'Diciembre 2025 vs. diciembre 2023', 'Variación de puestos manufactureros; se comparan solamente municipios con ambos cortes publicados.'),
  metric('actividad', 'Crecimiento de la actividad', 'Economía', 'pbg_real_cambio_2021_2023_pct', '%', 'PBG 2023 vs. 2021', 'Producto municipal a precios constantes de 2004. Mide producción localizada y su último corte es 2023.', false),
  metric('carencias', 'Hogares con carencias · %', 'Población', 'hogares_nbi_2022_pct', '%', 'Censo 2022', 'Hogares con necesidades básicas insatisfechas (NBI). Son carencias estructurales, no pobreza monetaria actual.', false),
  metric('hogares', 'Hogares con carencias · cantidad', 'Población', 'hogares_nbi_2022', 'households', 'Censo 2022', 'Número de hogares con NBI. Una mayor cantidad puede reflejar una población más grande.', false),
  metric('poblacion', 'Crecimiento de población', 'Población', 'crecimiento_poblacion_2010_2022_pct', '%', 'Censos 2010–2022', 'Chascomús y Lezama quedan fuera hasta homologar la separación territorial en la base de 2010.', false),
  metric('sucursales', 'Sucursales por habitante', 'Finanzas', 'sucursales_por_10000_hab_base2022', 'branches', '2024 · población 2022', 'Locales financieros por 10.000 habitantes. No incluye una medición de cobertura bancaria digital.', false),
  metric('credito', 'Cambio real del crédito', 'Finanzas', 'prestamos_real_cambio_2023_2024_pct', '%', 'Diciembre 2024 vs. diciembre 2023', 'Préstamos registrados por localización financiera, deflactados con IPC de cierre. No identifica solamente pymes o residentes.', false),
  metric('prestamos-depositos', 'Préstamos sobre depósitos', 'Finanzas', 'prestamos_sobre_depositos_2024_pct', '%', 'Cuarto trimestre 2024', 'Relación de saldos por localización financiera. No mide fuga de ahorros ni permite seguir el destino de cada depósito.', false),
  metric('deficit', 'Resultado sobre ingresos', 'Cuentas', 'fiscal.resultado_sobre_ingresos_pct', '%', 'Acumulado al 30 de junio de 2026', 'Muestra parcial con cierre en junio. Negativo: déficit; positivo: superávit. Recursos percibidos menos gastos devengados, sin aplicaciones financieras. Los servicios y organismos incluidos pueden diferir. No es caja libre.'),
  metric('resultado-pesos', 'Resultado en pesos', 'Cuentas', 'fiscal.resultado_financiero', 'millions', 'Acumulado al 30 de junio de 2026', 'Resultado financiero en pesos corrientes. El monto refleja también el tamaño del municipio. La muestra no permite identificar el mayor déficit de los 135.'),
  metric('inversion', 'Inversión sobre gasto', 'Cuentas', 'fiscal.capital_sobre_gasto_pct', '%', 'Acumulado al 30 de junio de 2026', 'Gasto de capital sobre gasto total sin aplicaciones financieras. Incluye inversión y transferencias de capital; no mide avance físico ni calidad de las obras.', false),
  metric('personal', 'Personal sobre gasto corriente', 'Cuentas', 'fiscal.personal_sobre_gasto_corriente_pct', '%', 'Acumulado al 30 de junio de 2026', 'Gasto devengado en personal sobre gasto corriente. Los servicios prestados, la tercerización y los organismos incluidos afectan la comparación.', false),
  metric('ahorro-corriente', 'Ahorro corriente sobre ingresos', 'Cuentas', 'fiscal.ahorro_sobre_ingresos_corrientes_pct', '%', 'Acumulado al 30 de junio de 2026', 'Ingresos corrientes percibidos menos gastos corrientes devengados, como porcentaje de los ingresos corrientes. Muestra el margen antes de la cuenta de capital. No es dinero libre.', false),
  metric('inversion-habitante', 'Inversión por habitante', 'Cuentas', 'fiscal.capital_por_habitante_base2022_ars_corrientes', 'money', 'Acumulado al 30 de junio de 2026 · población 2022', 'Gasto de capital en pesos corrientes por habitante del Censo 2022. La cobertura institucional y los servicios a cargo pueden diferir.', false),
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
export const VALID_VIEWS = ['panorama', 'rankings', 'recursos', 'empleo', 'simular'];
export function metricValue(m, meta) { return meta.field.split('.').reduce((v, k) => v?.[k], m) ?? null; }
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
export function fiscalExportRows(m) {
  const fields=[['ingresos_corrientes','Ingresos corrientes'],['ingresos_capital','Recursos de capital'],['ingresos_totales','Ingresos totales'],['gastos_corrientes','Gastos corrientes'],['gastos_capital','Gastos de capital'],['gastos_totales','Gastos totales'],['resultado_financiero','Resultado financiero'],['personal_devengado','Personal devengado']];
  return [m.fiscal,m.fiscalOther].filter(Boolean).flatMap(f=>fields.map(([key,label])=>[m.municipio,label,f[key]??null,'ARS corrientes',`${f.inicio} / ${f.fin}`,`${f.scope||'Cuenta municipal publicada.'} ${f===m.fiscal?'Período del ranking fiscal.':'Fuera del período del ranking fiscal.'}`]));
}
export function readState(search, municipalities, savedId) {
  const p=new URLSearchParams(search), id=p.get('municipio') || savedId;
  return {id:municipalities.some(m=>m.id===id)?id:'06805',view:VALID_VIEWS.includes(p.get('vista'))?p.get('vista'):'panorama',metric:METRICS.some(m=>m.id===p.get('indicador'))?p.get('indicador'):'recursos'};
}

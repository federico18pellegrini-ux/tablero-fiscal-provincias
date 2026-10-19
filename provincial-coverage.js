(function(root){
 'use strict';
 const names=['Equidad federal (RON, castigo, IAN)','Dinámica fiscal 2026','Perfil de deuda','Sostenibilidad y presión de deuda','Dependencia de transferencias Nación','Indicadores clave'];
 const number=x=>typeof x==='number'&&Number.isFinite(x);
 function build({province,rows=[],dynamics={},pbaDebt=null}){
  const accepted=new Set(['numérico','numerico','cálculo','estimación oficial']);
  const blocks=names.map(nombre=>{
   const cells=rows.filter(r=>r.provincia===province&&r.bloque===nombre);
   const missing=cells.filter(r=>!accepted.has(r.tipo_dato));
   if(cells.length&&cells.every(r=>r.tipo_dato==='no_comparable'))return {nombre,estado:'NO APLICA',motivo:'El indicador no es comparable para esta jurisdicción con el criterio publicado.'};
   return {nombre,estado:cells.length&&!missing.length?'COMPLETO':'PARCIAL',motivo:missing.length?'Falta verificar: '+[...new Set(missing.map(r=>r.kpi))].join('; ')+'.':cells.length?'Indicadores disponibles; cada dato conserva su corte.':'Faltan indicadores verificados para este bloque.'};
  });
  const metricNames={own_revenue:'recaudación propia',ron_total:'recursos nacionales',primary_expenditure:'gasto primario',wages:'personal',capital_expenditure:'inversión'};
  const missing=Object.keys(metricNames).filter(k=>!number(dynamics[k]?.real_ytd_pct)||!dynamics[k]?.ytd_available_through);
  const available=Object.keys(metricNames).filter(k=>!missing.includes(k)).map(k=>metricNames[k]+' hasta '+dynamics[k].ytd_available_through);
  Object.assign(blocks[1],{estado:missing.length?'PARCIAL':'COMPLETO',motivo:(available.length?'Variación real: '+available.join('; ')+'. ':'')+(missing.length?'Falta serie mensual comparable de '+missing.map(k=>metricNames[k]).join(', ')+'.':'Series mensuales comparables completas para los cortes indicados.')});
  if(province==='Buenos Aires'&&pbaDebt){
   const i=pbaDebt.latest_official_indicators||pbaDebt.official_pba_2025_indicators;
   const complete=i&&['interest_paid_to_total_resources_pct','debt_service_paid_to_total_resources_pct','debt_to_total_resources_pct'].every(k=>number(i[k]));
   Object.assign(blocks[3],{estado:complete?'COMPLETO':'PARCIAL',motivo:complete?'Intereses, servicios y stock sobre recursos totales: informe oficial al '+i.cutoff+'. Estos ratios no miden caja libre ni cobertura de aguinaldo.':'Faltan ratios oficiales de intereses, servicios y stock sobre recursos.'});
  }
  const b=blocks[4];
  if(b.estado==='COMPLETO')b.motivo='Peso de los impuestos nacionales y evolución de giros automáticos disponibles. El aporte territorial se muestra como estimación, no como faltante ni derecho de cobro.';
  if(blocks[0].estado==='PARCIAL')blocks[0].motivo='RON por habitante disponible. Falta una estimación homogénea del aporte tributario territorial para comparar retorno y brecha entre provincias; recibir menos que el promedio no prueba un incumplimiento legal.';
  if(blocks[2].estado==='COMPLETO')blocks[2].motivo='Stock y composición disponibles para el corte indicado. El estado no certifica un calendario mensual de pagos ni disponibilidad de caja.';
  return {provincia:province,bloques:blocks,campos_criticos_faltantes:blocks.filter(b=>b.estado==='PARCIAL').map(b=>({bloque:b.nombre,detalle:b.motivo})),tiene_alerta_critica:blocks.some(b=>b.estado==='PARCIAL')};
 }
 if(typeof module==='object'&&module.exports)module.exports={build};else root.FiscalCoverage={build};
})(typeof window==='object'?window:globalThis);

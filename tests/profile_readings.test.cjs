const test=require('node:test');const assert=require('node:assert/strict');
const {normalizeReadingProfile,buildProfileReadings}=require('../profile-readings.js');
const roles=['governor','hacienda','press'];
test('only three profiles, including migration of saved legacy choices',()=>{assert.equal(normalizeReadingProfile('deep'),'hacienda');assert.equal(normalizeReadingProfile('analyst'),'press');assert.equal(normalizeReadingProfile('unknown'),'governor');});
test('every section changes interpretation across all three profiles while keeping facts',()=>{const all=roles.map(r=>buildProfileReadings(r,{province:'Córdoba',rf:-2,rp:1,debt:20,period:'enero–marzo 2026'}));assert.equal(Object.keys(all[0]).length,11);for(const section of Object.keys(all[0]))assert.equal(new Set(all.map(r=>r[section][1])).size,3,section);for(const r of all){assert.match(r.summary[0],/Córdoba.*-2%.*enero–marzo 2026/);assert.match(r.debt[0],/\$100.*\$20/);}});
test('missing fiscal observations do not become a diagnosis or numeric zero',()=>{for(const role of roles){const r=buildProfileReadings(role,{province:'La Pampa'});assert.match(r.summary[0],/falta un resultado/);assert.doesNotMatch(r.summary[0],/0%/);assert.match(r.debt[0],/Falta/);}});
test('zero, deficit and surplus have distinct conclusions',()=>{for(const role of roles){const conclusions=[-1,0,1].map(rf=>buildProfileReadings(role,{province:'Prueba',rf,rp:0}).summary[1]);assert.equal(new Set(conclusions).size,3);}});
test('minister differentiates a primary deficit from interest pressure',()=>{const primary=buildProfileReadings('hacienda',{province:'Prueba',rf:-5,rp:-2});const interest=buildProfileReadings('hacienda',{province:'Prueba',rf:-5,rp:2});assert.match(primary.summary[1],/empieza antes de intereses/);assert.match(interest.summary[1],/diferencia aparece al pagar intereses/);});
const {buildSummaryReading}=require('../profile-readings.js');
test('short summary distinguishes fiscal mechanisms without repeating the KPI percentages',()=>{
 for(const role of roles){
  const cases=[{rf:null,rp:null},{rf:-5,rp:null},{rf:-5,rp:-2},{rf:-5,rp:2},{rf:0,rp:1},{rf:4,rp:6}];
  const readings=cases.map(c=>buildSummaryReading(role,c));
  assert.equal(new Set(readings).size,cases.length);
  for(const text of readings){assert.ok(text.split(/\s+/).length<=55);assert.doesNotMatch(text,/%|undefined|NaN/);}
  assert.match(readings[0],/Falta/);assert.match(readings[2],/antes de|gasto primario/);
  assert.match(readings[3],/intereses|costo financiero/);
 }
 assert.equal(new Set(roles.map(r=>buildSummaryReading(r,{rf:-5,rp:-2}))).size,3);
 assert.match(buildSummaryReading('governor',{rf:1,rp:-1}),/conciliar/);
});
test('debt narrative separates recorded services from a published annual calendar',()=>{
 const text=buildProfileReadings('governor',{services:{total_ars_m:100}}).debt.join(' ');
 assert.match(text,/registrados en años anteriores/);assert.match(text,/Falta el calendario de próximos pagos/);
 assert.doesNotMatch(text,/mayor importe.*2026/);
 const projected=buildProfileReadings('governor',{projection:{rows:[{year:2026,total_ars_m:10},{year:2027,total_ars_m:20},{year:2028,total_ars_m:null}]}}).debt.join(' ');
 assert.match(projected,/mayor importe anual en 2027/);assert.match(projected,/sin descontar los pagos posteriores/);
});
test('debt reading preserves missing, loading and zero observations',()=>{
 const pending=buildProfileReadings('governor',{debt:45.23});
 assert.match(pending.debt[0],/\$100.*\$45,23/);
 assert.match(pending.debt[0],/Falta el calendario/);
 assert.doesNotMatch(pending.debt[1],/años de mayor vencimiento/);
 const loading=buildProfileReadings('governor',{debtScheduleStatus:'loading'}).debt[0];
 assert.match(loading,/Estamos cargando/);assert.doesNotMatch(loading,/Falta el calendario/);
 assert.match(buildProfileReadings('governor',{debt:0}).debt[0],/\$100.*\$0/);
});

test('federal reading describes the documented instrument rather than assuming a cash claim',()=>{
 const cases=[['reclamo',/reclamo publicado/],['anticipo',/anticipos acordados/],['credito_compensable',/reducir lo que la Provincia debe pagar/],['acuerdo',/acuerdo de pago/],['pago',/ya recibió/],['sin_monto',/no tenemos un importe/]];
 for(const [kind,expected] of cases)assert.match(buildProfileReadings('governor',{claim:{kind}}).federal[0],expected);
 assert.match(buildProfileReadings('governor',{}).federal[0],/falta documentación/);
 assert.match(buildProfileReadings('governor',{claim:{state:'unavailable'}}).federal[0],/No se pudo cargar/);
 assert.doesNotMatch(buildProfileReadings('governor',{claim:{kind:'credito_compensable'}}).federal.join(' '),/cobrar|ya recibió/);
});

test('income and map explain the selected unit and period without turning missing data into zero',()=>{
 const real=buildProfileReadings('governor',{priceMode:'real',autonomy:0});
 assert.match(real.income[0],/aportan \$0 de cada \$100/);assert.match(real.income[0],/constantes descuenta la inflación/);
 const nominal=buildProfileReadings('governor',{priceMode:'nominal'});
 assert.match(nominal.income[0],/corrientes muestra/);assert.doesNotMatch(nominal.income[0],/aportan \$0/);
 const map=buildProfileReadings('governor',{province:'Córdoba',mapMetric:'primary_pct',mapPeriod:'2024-Q4',mapValue:0}).map[0];
 assert.match(map,/antes de intereses al 4T2024/);assert.match(map,/Córdoba: 0%/);
 assert.match(buildProfileReadings('governor',{mapMetric:'financial_pct'}).map[0],/después de intereses/);
 assert.doesNotMatch(buildProfileReadings('governor',{}).map[0],/0%/);
});

test('history uses dated observations and does not invent a trend from one observation',()=>{
 const one=buildProfileReadings('governor',{history:[{period:'2026-Q1',financial_pct:null},{period:'2025-Q4',financial_pct:0}]}).history[0];
 assert.match(one,/Hay un dato.*4T2025: 0%/);assert.doesNotMatch(one,/pasó de|1T2026/);
 const series=[{period:'2026-Q1',financial_pct:-2},{period:'2025-Q4',financial_pct:3}];
 assert.match(buildProfileReadings('governor',{history:series}).history[0],/4T2025 y 1T2026.*3% a -2%/);
 assert.equal(series[0].period,'2026-Q1');
 assert.doesNotMatch(buildProfileReadings('governor',{}).history[1],/La curva permite/);
 assert.doesNotMatch(buildProfileReadings('governor',{}).comparison[1],/El puesto ayuda/);
});

test('national monthly reading distinguishes surplus, deficit, balance and missing observations',()=>{
 for(const [value,word] of [[1,'superávit'],[-1,'déficit'],[0,'equilibrio']]){
  const national={period_label:'julio de 2026',metrics:[{label:'Resultado financiero mensual',unit:'millones de $',value}]};
  assert.match(buildProfileReadings('governor',{national}).nation[0],new RegExp('julio de 2026.*'+word));
 }
 assert.doesNotMatch(buildProfileReadings('governor',{}).nation[0],/superávit|déficit|equilibrio/);
});

const {debtRankingLabel}=require('../profile-readings.js');
test('debt rank is interpreted from its observed position and coverage',()=>{
 assert.match(debtRankingLabel(23,23),/puesto 23 de 23.*mayor carga/);
 assert.match(debtRankingLabel(1,23),/puesto 1 de 23.*menor carga/);
 assert.match(debtRankingLabel(8,23),/puesto 8 de 23.*de menor a mayor/);
 for(const rank of [null,0,24,NaN])assert.equal(debtRankingLabel(rank,23),'Sin posición en el ranking actual.');
 assert.match(buildSummaryReading('governor',{rf:-5,rp:-2,debtRank:23,debtTotal:23}),/mayor carga de deuda/);
 assert.doesNotMatch(buildSummaryReading('governor',{rf:null,rp:null,debtRank:23,debtTotal:23}),/mayor carga de deuda/);
});

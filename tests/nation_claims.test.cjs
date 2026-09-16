const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const Claims=require('../nation-claims.js');
const data=require('../dashboard_reclamos_nacion_provincias.json');
test('Spanish units distinguish trillions from billions and preserve USD',()=>{
  assert.equal(Claims.money({value:19.1e12,currency:'ARS',qualifier:'aproximado'}),'≈ $19,1 billones');
  assert.equal(Claims.money({value:15e9,currency:'ARS',qualifier:'exacto'}),'$15 mil millones');
  assert.equal(Claims.money({value:300e6,currency:'USD',qualifier:'mas_de'}),'Más de USD 300 millones');
  assert.equal(Claims.money({value:1.5e12,upper:2e12,currency:'ARS',qualifier:'rango'}),'$1,5 a 2 billones');
  assert.equal(Claims.money(null),'Monto no publicado');
});
test('all jurisdictions render dates, missingness and no collapsed content',()=>{
  for(const name of Object.keys(data.provinces)){
    const html=Claims.render(data,name,'Lectura según perfil');
    assert.match(html,/Saldo total pendiente de cobro: no verificado/);
    assert.equal((html.match(/data-claim-province=/g)||[]).length,24);
    assert.doesNotMatch(html,/<details|<select/);
    assert.match(html,/Lectura según perfil/);
    if(data.provinces[name].records.length===0)assert.match(html,/no significa que Nación no le deba/);
  }
});
test('source text is escaped and unsafe URLs are never rendered',()=>{
  const copy=structuredClone(data);
  const record=copy.provinces['Buenos Aires'].records[0];
  record.title='<img onerror=alert(1)>';
  record.source.url='javascript:alert(1)';
  const html=Claims.render(copy,'Buenos Aires','<script>');
  assert.doesNotMatch(html,/<img|<script>|href="javascript:/);
  assert.match(html,/&lt;img/);
});
test('agreements are not labelled as current total debt',()=>{
  const html=Claims.render(data,'CABA','lectura');
  assert.match(html,/Reclamo provincial/);
  assert.match(html,/Acuerdo de pago/);
  assert.match(html,/USD 6 mil millones/);
  assert.match(html,/813,443 mil millones/);
  assert.doesNotMatch(html,/subtotal robusto|deuda total reclamada/i);
});
test('embedded fallback matches the verified dataset',()=>{
  const html=fs.readFileSync(require('node:path').join(__dirname,'../index.html'),'utf8');
  const match=html.match(/^const EMBEDDED_RECLAMOS_NACION = (.*);$/m);
  assert.deepEqual(JSON.parse(match[1]),data);
});
test('summary only presents claims as the headline amount, never advances or agreements',()=>{
  const pba=Claims.summaryModel(data,'Buenos Aires');
  assert.equal(pba.value,'≈ $19,1 billones');
  assert.match(pba.context,/4,7 billones/);
  assert.match(pba.caution,/no es un saldo actual conciliado/);
  for(const province of ['Corrientes','Córdoba','Entre Ríos','Mendoza']){
    const model=Claims.summaryModel(data,province);
    assert.equal(model.state,'reference');
    assert.equal(model.value,'Saldo sin verificar');
    assert.match(model.caution,/no representa toda la deuda/);
    assert.ok(model.publishedAt);
  }
  assert.equal(Claims.summaryModel(data,'CABA').value,'≈ USD 6 mil millones');
  assert.equal(Claims.summaryModel(data,'Santa Fe').value,'$1,5 a 2 billones');
});
test('summary picks the latest claim without summing references or mutating data',()=>{
  const copy=structuredClone(data),pba=copy.provinces['Buenos Aires'];
  const old=structuredClone(pba.records[0]);old.id='older';old.published_at='2026-01-01';old.amount.value=15e12;pba.records.unshift(old);
  const before=JSON.stringify(copy);
  assert.equal(Claims.summaryModel(copy,'Buenos Aires').recordId,'pba-20260914');
  assert.equal(JSON.stringify(copy),before);
});
test('summary preserves missingness, dates, evidence type and the detail route for all provinces',()=>{
  for(const province of Object.keys(data.provinces)){
    const model=Claims.summaryModel(data,province),html=Claims.summaryHTML(data,province);
    assert.ok(model.value);assert.match(html,/data-summary-claim-link/);
    assert.match(html,/data-editorial-view="federal"/);
    assert.doesNotMatch(html,/\$0(?:\s|<)|undefined|null|NaN/);
    if(model.publishedAt)assert.ok(html.includes(model.publishedAt.split('-').reverse().join('/')));
  }
  for(const province of ['Catamarca','Misiones','Santa Cruz'])assert.equal(Claims.summaryModel(data,province).state,'missing');
  assert.equal(Claims.summaryModel(null,'Buenos Aires').value,'Monto sin documentar');
});

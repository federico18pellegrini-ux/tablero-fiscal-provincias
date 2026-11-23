const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.join(__dirname,'..'),data=JSON.parse(fs.readFileSync(path.join(root,'data/authorities.json'),'utf8'));
const {authorityText,affiliation}=require('../authorities.js');
test('all municipal and provincial selectors have sourced authorities, without mixing geographical IDs',()=>{
 const municipalities=JSON.parse(fs.readFileSync(path.join(root,'municipios/data/dashboard.json'),'utf8')).municipalities;
 assert.equal(Object.keys(data.municipalities).length,135);assert.equal(Object.keys(data.provinces).length,24);
 for(const m of municipalities)assert.equal(data.municipalities[m.id].district,m.municipio);
 for(const record of [...Object.values(data.municipalities),...Object.values(data.provinces)]){
  assert.ok(record.name&&record.role&&record.politicalLabel);assert.match(data.sources[record.nameSource].url,/^https?:\/\//);assert.match(data.sources[record.politicalSource].url,/^https?:\/\//);
  assert.ok(authorityText(record).includes(record.name));
  if(record.politicalKind==='electoral_alliance'){assert.equal(record.politicalYear,2023);assert.match(affiliation(record),/elección 2023/);}
 }
 for(const source of Object.values(data.sources))if(source.archive){const b=fs.readFileSync(path.join(root,source.archive));assert.equal(crypto.createHash('sha256').update(b).digest('hex'),source.sha256);}
});
test('successors and the two different Frente Renovador spaces are preserved',()=>{
 const municipal=Object.values(data.municipalities),find=n=>municipal.find(x=>x.district===n);
 assert.equal(find('Almirante Brown').name,'Juan José Fabiani');assert.equal(find('Daireaux').name,'María Alejandra Serra');assert.equal(find('General Las Heras').name,'Juan Manuel Cerezo');
 assert.equal(find('Berazategui').name,'Carlos Eduardo Balor');assert.equal(find('Quilmes').name,'Eva Mieri');assert.equal(find('Tigre').name,'Julio Zamora');
 assert.equal(find('General Las Heras').politicalLabel,'Frente Renovador');assert.equal(data.provinces.Misiones.politicalLabel,'Frente Renovador de la Concordia');
 assert.equal(data.provinces.CABA.role,'Jefe de Gobierno');assert.equal(data.provinces.Corrientes.name,'Juan Pablo Valdés');assert.equal(data.provinces['Santiago del Estero'].name,'Elías Suárez');assert.equal(data.provinces['San Juan'].politicalLabel,'Producción y Trabajo');
});

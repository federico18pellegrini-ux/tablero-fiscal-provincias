const test=require('node:test'),assert=require('node:assert/strict');
const M=require('../nacion/management-model.js');
test('signed cash bars put deficits to the left of zero, with the same scale as surpluses',()=>{
 const deficit=M.barGeometry(-100,200,true),surplus=M.barGeometry(100,200,true);
 assert.equal(deficit.left+deficit.width,50);assert.equal(surplus.left,50);assert.equal(deficit.width,surplus.width);
 assert.deepEqual(M.barGeometry(null,200,true),{left:50,width:0});
 assert.deepEqual(M.barGeometry(0,200,true),{left:50,width:0});
 assert.deepEqual(M.barGeometry(100,200,false),{left:0,width:50});
});
test('physical-measure reading order preserves every official row and never ranks unlike units by size',()=>{
 const senate={funcion_desc:'Legislativa',ejecutado:1e12},health={funcion_desc:'Salud',ejecutado:1},retirement={funcion_desc:'Seguridad Social',ejecutado:2};const rows=[senate,health,retirement];
 const ordered=M.orderPhysical(rows);assert.deepEqual(ordered,[retirement,health,senate]);assert.equal(ordered.length,rows.length);assert.deepEqual(rows,[senate,health,retirement]);
});

test('the social-security introduction leads with ANSES without removing the other pension systems',()=>{
 const police={funcion_desc:'Seguridad Social',servicio_desc:'Caja de Retiros de la Policía Federal'},anses={funcion_desc:'Seguridad Social',servicio_desc:'Administración Nacional de la Seguridad Social'};
 assert.deepEqual(M.orderPhysical([police,anses]),[anses,police]);
});

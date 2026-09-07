const test=require('node:test'),assert=require('node:assert/strict');
const {fiscalExecutionRatios,proposalCost}=require('../budget-execution.js');
test('ratios preserve missing data, deficit and zero balance',()=>{
 assert.equal(fiscalExecutionRatios({income:null,spending:100,capital:10}),null);
 assert.equal(fiscalExecutionRatios({income:0,spending:100,capital:10}),null);
 assert.deepEqual(fiscalExecutionRatios({income:100,spending:120,capital:30}),{balance:-20,capital:25});
 assert.equal(fiscalExecutionRatios({income:100,spending:100,capital:0}).balance,0);
});
test('costs distinguish startup, recurring and funding without blank assumptions',()=>{
 const v={quantity:100,unit:.2,months:6,startup:10,funding:40};
 assert.deepEqual(proposalCost(v),{recurring:120,total:130,gap:90});
 assert.equal(proposalCost({...v,funding:200}).gap,0);
 for(const patch of [{unit:null},{months:0},{months:13},{months:1.5},{funding:-1},{quantity:Infinity}])assert.equal(proposalCost({...v,...patch}),null);
 assert.deepEqual(proposalCost({quantity:0,unit:0,months:1,startup:0,funding:0}),{recurring:0,total:0,gap:0});
});

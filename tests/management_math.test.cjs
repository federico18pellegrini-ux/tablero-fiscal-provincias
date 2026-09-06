const {test}=require('node:test');
const assert=require('node:assert/strict');
const {calculateCashScenario:calculate}=require('../management-tools.js');
const {reconcileCash}=require('../closing-tools.js');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const monetaryCode=html.slice(html.indexOf('function deflateValue('),html.indexOf('function valueForMode('));
const monetary=vm.createContext({});vm.runInContext(monetaryCode,monetary);
test('monthly cash flows are adjusted before aggregation, preserving signed flows',()=>{
 const {deflateValue:adjust,sumConvertedValues:sum}=monetary;
 assert.equal(sum([adjust(100,2),adjust(300,1)]),500);
 assert.notEqual(sum([adjust(100,2),adjust(300,1)]),adjust(400,1));
 assert.equal(adjust(-100,2),-200);assert.equal(adjust(0,2),0);
});
test('a missing CPI never becomes a nominal fallback or a partial real total',()=>{
 const {deflateValue:adjust,sumConvertedValues:sum}=monetary;
 for(const bad of [null,undefined,0,-1,NaN,Infinity,'2'])assert.equal(adjust(100,bad),null);
 assert.equal(sum([adjust(100,2),adjust(300,null)]),null);
 assert.equal(sum([]),null);assert.equal(sum([0,0]),0);
});
test('reconciliation deducts disjoint restrictions and rejects excess deductions',()=>{
 assert.equal(reconcileCash(100,25,15),60);
 assert.equal(reconcileCash(100,75,30),null);
 for(const invalid of [null,undefined,'',NaN,Infinity,-1])assert.equal(reconcileCash(invalid,0,0),null);
 assert.equal(reconcileCash(0,0,0),0);
});
test('does not turn missing or invalid inputs into zero',()=>{
 const input={cash:100,revenue:200,spending:150,principal:30,interest:10,financing:0};
 for(const value of [null,undefined,'',NaN,Infinity,-1])assert.equal(calculate({...input,cash:value}),null);
});
test('separates operating payments, principal and interest',()=>{
 assert.deepEqual(calculate({cash:100,revenue:200,spending:250,principal:80,interest:20,financing:10}),{available:310,payments:350,closing:-40,gap:40});
});
test('explicit zeros are legitimate observations',()=>{
 assert.deepEqual(calculate({cash:0,revenue:0,spending:0,principal:0,interest:0,financing:0}),{available:0,payments:0,closing:0,gap:0});
});

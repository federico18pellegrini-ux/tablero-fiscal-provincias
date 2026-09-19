/* Conditional scenarios. Official observations are never overwritten. */
(function(root){
  'use strict';
  const finite=x=>typeof x==='number'&&Number.isFinite(x),sum=a=>a.reduce((s,x)=>s+x,0);
  const fold=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  function closing(b,rows,{monthlyInflation,pace}){
    if(!finite(monthlyInflation)||monthlyInflation<0||monthlyInflation>25||!finite(pace)||pace< -50||pace>50)return null;
    const anchor=b.deflator.monthly_index['2026-08'];
    const observed=Array.from({length:8},(_,i)=>({month:i+1,observed:true,value:0}));
    const future=Array.from({length:4},(_,i)=>({month:i+9,observed:false,value:0}));
    const groups=[];
    for(const f of b.functions){
      const named=rows.filter(r=>r.anio===2026&&fold(r.funcion_desc)===fold(f.name));
      const keys=new Set(named.map(r=>r.finalidad_id+'-'+r.funcion_id));
      if(keys.size!==1)return null;
      const rr=rows.filter(r=>keys.has(r.finalidad_id+'-'+r.funcion_id));
      const get=(year,m)=>rr.filter(r=>r.periodo===`${year}-${String(m).padStart(2,'0')}`&&r.mes_completo);
      const old=Array.from({length:12},(_,i)=>get(2025,i+1)),now=Array.from({length:8},(_,i)=>get(2026,i+1));
      if([...old,...now].some(a=>a.length!==1))return null;
      const prior=old.map(a=>a[0].credito_devengado_real_agosto2026),current=now.map(a=>a[0].credito_devengado_real_agosto2026);
      if(![...prior,...current].every(finite)||sum(prior.slice(0,8))<=0)return null;
      const growth=sum(current)/sum(prior.slice(0,8));
      const actual=sum(now.map((a,i)=>{const v=a[0].credito_devengado;observed[i].value+=v;return v;}));
      const projected=prior.slice(8).map((v,i)=>v*growth*(1+pace/100)*Math.pow(1+monthlyInflation/100,i+1));
      projected.forEach((v,i)=>future[i].value+=v);
      groups.push({name:f.name,observed:actual,remaining:sum(projected),total:actual+sum(projected),official:f.closing,current:f.current});
    }
    const total=sum(groups.map(g=>g.total));
    const average=(sum(Object.entries(b.deflator.monthly_index).filter(([k])=>/^2026-0[1-8]$/.test(k)).map(([,v])=>v))+sum(future.map((r,i)=>anchor*Math.pow(1+monthlyInflation/100,i+1))))/12;
    return {total,observed:sum(observed.map(r=>r.value)),remaining:sum(future.map(r=>r.value)),months:[...observed,...future],groups,average,vsOfficial:total-b.total.closing,vsCredit:total-b.total.current};
  }
  function revenue(data,{monthlyInflation,revenuePace,bcraFuture}){
    if(!finite(monthlyInflation)||monthlyInflation<0||monthlyInflation>25||!finite(revenuePace)||revenuePace< -50||revenuePace>50||!finite(bcraFuture)||bcraFuture<0||bcraFuture>100)return null;
    const ids=['tax','social','property','other'],get=p=>data.months.filter(m=>m.period===p);
    const old=Array.from({length:12},(_,i)=>get(`2025-${String(i+1).padStart(2,'0')}`)),now=Array.from({length:8},(_,i)=>get(`2026-${String(i+1).padStart(2,'0')}`));
    if([...old,...now].some(a=>a.length!==1))return null;
    const past=old.map(a=>a[0]),actual=now.map(a=>a[0]);
    if(actual.some(m=>!finite(m.total)||!finite(m.bcra)))return null;
    const months=actual.map((m,i)=>({month:i+1,observed:true,value:m.total,bcra:m.bcra}));
    const future=Array.from({length:4},(_,i)=>({month:i+9,observed:false,value:0})),groups=[];
    for(const id of ids){
      const a=actual.map(m=>m.groups.filter(g=>g.id===id)),p=past.map(m=>m.groups.filter(g=>g.id===id));
      if([...a,...p].some(x=>x.length!==1||!finite(x[0].real)||!finite(x[0].nominal)))return null;
      const prior=p.map(x=>x[0]),current=a.map(x=>x[0]),denom=sum(prior.slice(0,8).map(x=>x.real));
      if(denom<=0)return null;
      const factor=sum(current.map(x=>x.real))/denom;
      const projected=prior.slice(8).map((x,i)=>x.real*factor*(1+revenuePace/100)*Math.pow(1+monthlyInflation/100,i+1));
      projected.forEach((v,i)=>future[i].value+=v);
      const observed=sum(current.map(x=>x.nominal));groups.push({id,name:current[0].name,observed,remaining:sum(projected),total:observed+sum(projected)});
    }
    const observed=sum(actual.map(x=>x.total)),bcraObserved=sum(actual.map(x=>x.bcra)),additional=bcraFuture*1e6,remaining=sum(future.map(x=>x.value))+additional;
    // New BCRA funds have no assumed month; keep them outside the monthly series.
    return {observed,bcraObserved,bcraFuture:additional,remaining,total:observed+remaining,withoutBcra:observed+remaining-bcraObserved-additional,groups,months:[...months,...future],unallocatedFuture:additional};
  }
  function integrated(b,d,o){
    const limits={inflation:[0,300],growth:[-20,20],elasticity:[0,3],pensionPass:[0,100],otherPass:[0,100],interestChange:[-50,100],financing:[0,150]};
    if(Object.entries(limits).some(([k,[lo,hi]])=>!finite(o[k])||o[k]<lo||o[k]>hi))return null;
    const f=Object.fromEntries(d.finance.rows.map(r=>[r.id,r.project]));
    if(!['VI','VII','I.1','I.2','II.2','II.6','XII.1','XII.2','XIII.1','XIII.2'].every(k=>finite(f[k])))return null;
    const baseInflation=b.deflator.annual_average_index['2027']/b.deflator.annual_average_index['2026'];
    const baseGrowth=b.macro.find(r=>fold(r.name)==='crecimiento del pib').values[2];
    const prices=(1+o.inflation/100)/baseInflation;
    const taxFactor=Math.pow((1+o.growth/100)/(1+baseGrowth/100),o.elasticity)*prices;
    const taxes=(f['I.1']+f['I.2'])*taxFactor,otherRevenue=f.VI-f['I.1']-f['I.2'];
    const pensions=f['II.6']*(1+(prices-1)*o.pensionPass/100);
    const otherPrimary=(f.VII-f['II.2']-f['II.6'])*(1+(prices-1)*o.otherPass/100);
    const interest=f['II.2']*(1+o.interestChange/100),expenses=pensions+otherPrimary+interest;
    const resources=taxes+otherRevenue,balance=resources-expenses;
    const applications=f['XIII.1']+f['XIII.2'],otherSources=f['XII.1'];
    const need=applications-balance-otherSources,available=f['XII.2']*o.financing/100;
    const residual=(f['XIII.1']+f['XIII.2'])-(f.VI-f.VII)-f['XII.1']-f['XII.2'];
    return {resources,expenses,pensions,otherPrimary,interest,taxes,otherRevenue,balance,primary:balance+interest,need,available,gap:need-available,roundingResidual:residual,vsOfficialBalance:balance-(f.VI-f.VII),applications,otherSources};
  }
  const api={closing,integrated,revenue};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NationalPlanning=api;
})(typeof globalThis!=='undefined'?globalThis:this);

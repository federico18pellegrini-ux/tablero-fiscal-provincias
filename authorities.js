(function(root){
 'use strict';
 function affiliation(record){
  if(!record)return '';
  return record.politicalLabel+(record.politicalKind==='electoral_alliance'?` · elección ${record.politicalYear}`:'');
 }
 function authorityText(record){
  return record?`${record.role}${record.interim?' en ejercicio':''}: ${record.name} · ${affiliation(record)}`:'';
 }
 if(typeof module!=='undefined')module.exports={affiliation,authorityText};
 if(typeof document==='undefined')return;
 const script=document.currentScript,sourceUrl=new URL('data/authorities.json',script.src);
 let data=null,municipal=null,province=null;
 function paint(id,record,hidden=false){
  const node=document.getElementById(id);if(!node)return;
  node.replaceChildren();node.hidden=hidden||!record;if(node.hidden)return;
  const role=document.createElement('span');role.className='authority-role';role.textContent=record.role+(record.interim?' en ejercicio':'')+': ';
  const name=document.createElement('a');name.className='authority-name';name.textContent=record.name;
  const source=data.sources[record.nameSource];name.href=source.url;name.target='_blank';name.rel='noopener noreferrer';name.title='Autoridad · fuente consultada el '+data.reviewedAt;
  const separator=document.createElement('span');separator.className='authority-separator';separator.textContent=' · ';separator.setAttribute('aria-hidden','true');
  const party=document.createElement('a');party.className='authority-party';party.textContent=affiliation(record);party.href=data.sources[record.politicalSource].url;party.target='_blank';party.rel='noopener noreferrer';
  party.title=(record.politicalKind==='electoral_alliance'?'Alianza ganadora de la elección municipal de 2023; no acredita afiliación personal actual.':'Partido o espacio político · referencia '+record.politicalYear)+ ' · Abrir fuente';
  node.append(role,name,separator,party);
 }
 function refresh(){
  if(!data)return;
  if(municipal)paint('municipality-authority',data.municipalities[municipal.municipality.id],municipal.view==='rankings');
  const selected=province||document.getElementById('psel')?.value;
  if(selected)paint('province-authority',data.provinces[selected]);
 }
 root.addEventListener('municipal:structure',event=>{municipal=event.detail;refresh();});
 root.addEventListener('province:selection',event=>{province=event.detail.province;refresh();});
 fetch(sourceUrl).then(response=>{if(!response.ok)throw new Error('HTTP '+response.status);return response.json();}).then(value=>{
  data=value;municipal=root.municipalStructureContext||municipal;refresh();
 }).catch(error=>console.warn('No se pudo cargar la identificación de autoridades:',error.message));
})(typeof window!=='undefined'?window:globalThis);

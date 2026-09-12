export const REPORT_TOPICS=['lectura','cuentas','economia','poblacion','deudas','detalle-fiscal','caja','historia','bancos'];
export const DEFAULT_REPORT_TOPICS=['lectura','cuentas','economia'];
export function validReportEntry(entry){
  if(!entry||!/^06\d{3}$/.test(entry.id)||entry.file!==`informe-${entry.id}.pdf`||!Number.isInteger(entry.pages)||entry.pages<3||entry.pages>100||!/^[a-f0-9]{64}$/.test(entry.sha256))return false;
  const brief=entry.brief;
  if(!brief||brief.file!==`informe-${entry.id}-breve.pdf`||brief.pages!==3||!/^[a-f0-9]{64}$/.test(brief.sha256))return false;
  const modules=entry.modules;
  if(!Array.isArray(modules)||modules.length<3||new Set(modules.map(m=>m.id)).size!==modules.length||modules.some(m=>!REPORT_TOPICS.includes(m.id)||typeof m.label!=='string'||typeof m.description!=='string'||!Array.isArray(m.pages)||!m.pages.length||m.pages.some(p=>!Number.isInteger(p))))return false;
  if(modules.some((m,i)=>i&&REPORT_TOPICS.indexOf(m.id)<REPORT_TOPICS.indexOf(modules[i-1].id)))return false;
  if(modules.map(m=>m.required?m.id:'').filter(Boolean).join(',')!=='lectura')return false;
  if(modules.filter(m=>m.default).map(m=>m.id).join(',')!==DEFAULT_REPORT_TOPICS.join(','))return false;
  if(modules.filter(m=>m.default).flatMap(m=>m.pages).join(',')!=='0,1,2')return false;
  return modules.flatMap(m=>m.pages).join(',')===Array.from({length:entry.pages},(_,i)=>i).join(',');
}
export function reportSelection(entry,topics=DEFAULT_REPORT_TOPICS){
  if(!validReportEntry(entry))throw new Error('El catálogo de informes está en actualización.');
  const wanted=new Set(['lectura',...topics]);
  const modules=entry.modules.filter(m=>wanted.has(m.id)),pages=modules.flatMap(m=>m.pages);
  const mode=modules.map(m=>m.id).join(',')===DEFAULT_REPORT_TOPICS.join(',')?'brief':pages.length===entry.pages?'full':'custom';
  return {modules,pages,mode,key:entry.id+':'+modules.map(m=>m.id).join(','),count:pages.length};
}
export async function composeMunicipalPdf(bytes,entry,topics,pdfLib){
  const selected=reportSelection(entry,topics),{PDFDocument,PDFName,PDFDict,StandardFonts,rgb}=pdfLib;
  const source=await PDFDocument.load(bytes),output=await PDFDocument.create();
  if(source.getPageCount()!==entry.pages)throw new Error('La cantidad de páginas no coincide con el catálogo.');
  const pages=await output.copyPages(source,selected.pages),font=await output.embedFont(StandardFonts.Helvetica);
  const blankNumber=output.context.register(output.context.flateStream(new Uint8Array(),{Type:'XObject',Subtype:'Form',BBox:[0,0,0,0]}));
  pages.forEach((page,i)=>{
    const resources=page.node.Resources(),xobjects=resources.lookup(PDFName.of('XObject'),PDFDict);
    if(!xobjects.has(PDFName.of('FPPageNumber')))throw new Error('El informe no permite actualizar la numeración.');
    // The source number is an isolated form; replace it instead of covering stale text.
    xobjects.set(PDFName.of('FPPageNumber'),blankNumber);
    const label=`Página ${i+1}`;
    page.drawText(label,{x:page.getWidth()-42-font.widthOfTextAtSize(label,8),y:14,size:8,font,color:rgb(.345,.412,.388)});
    output.addPage(page);
  });
  output.setTitle(`${entry.municipality} - Informe municipal`);output.setAuthor('Federico Pellegrini');
  output.setSubject(selected.modules.map(m=>m.label).join(' · '));output.setCreator('Tablero municipal de Federico Pellegrini');
  return output.save();
}

"""Interactive, private visual promotional-text mapping canvas."""
STYLE = r"""
.raster-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(345px,.9fr);gap:20px;align-items:start}
.raster-canvas-shell{border:1px solid var(--border);border-radius:16px;overflow:hidden;background:var(--surface);min-width:0}
.raster-canvas-top{padding:16px 19px;display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--border)}
.raster-stage{background:repeating-conic-gradient(#e9eaf0 0% 25%,#fff 0% 50%) 50%/20px 20px;min-height:310px;padding:24px;display:flex;align-items:center;justify-content:center}
.raster-stage canvas{max-width:100%;display:block;touch-action:none;user-select:none;cursor:crosshair;border-radius:5px;box-shadow:0 12px 50px #0004}
.raster-canvas-footer{padding:14px 18px;display:flex;align-items:center;gap:12px;justify-content:space-between;flex-wrap:wrap;font-size:11px;color:var(--muted)}
.raster-side{display:grid;gap:16px;align-content:start}
.raster-help{font-size:11px;color:var(--sub);line-height:1.6}
.raster-toolbar{display:flex;flex-wrap:wrap;gap:9px}
.raster-toolbar button{min-height:36px}
.raster-layer-list{max-height:250px;overflow:auto;display:grid;gap:6px;margin-top:8px}
.raster-layer{border:1px solid var(--border);border-radius:10px;background:var(--surface2);width:100%;display:flex;justify-content:space-between;align-items:center;gap:9px;padding:10px;text-align:left;color:var(--sub);font-size:12px;cursor:pointer}
.raster-layer:hover{border-color:var(--accent)}
.raster-layer.is-active{border-color:var(--accent);background:var(--accent-low);color:var(--text)}
.raster-layer strong{font-size:12px;color:var(--text);display:block}
.raster-layer small{font-size:10px;display:block;margin-top:4px}
.raster-layer .layer-sw{height:11px;width:11px;border-radius:3px;flex-shrink:0;border:1px solid #aaa7}
.raster-properties{margin-top:12px}
.raster-properties[hidden]{display:none}
.raster-property-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.raster-property-grid .field{margin:0}
.raster-property-grid input[type=color]{height:42px;width:100%;padding:4px;background:var(--input);border-radius:9px;border:1px solid var(--border)}
.raster-checkbox{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:650;color:var(--sub)}
.raster-checkbox input{accent-color:var(--accent)}
.raster-notice{padding:12px 13px;border:1px solid var(--border);background:var(--surface2);border-radius:10px;line-height:1.55;font-size:11px;color:var(--sub)}
.raster-empty{text-align:center;padding:17px 12px;color:var(--muted);font-size:11px;background:var(--surface2);border-radius:10px}
.raster-tip{display:flex;gap:8px;align-items:flex-start;color:var(--muted);font-size:11px;line-height:1.6}
.raster-field-picker{margin-top:7px}
.raster-status{min-height:34px;font-size:12px;color:var(--muted);display:flex;align-items:center}
.raster-status.ok{color:var(--green)}.raster-status.bad{color:var(--red)}
.raster-canvas-shell .toolbar-button{min-height:37px}
.raster-divider{height:1px;background:var(--border);margin:15px 0}
@media(max-width:1230px){.raster-grid{grid-template-columns:1fr}.raster-side{grid-template-columns:1fr 1fr}.raster-editor-actions{grid-column:1/-1}}
@media(max-width:720px){.raster-side{grid-template-columns:1fr}.raster-stage{padding:12px}.raster-property-grid{grid-template-columns:1fr 1fr}}
"""

SCRIPT = r"""
(function(){
'use strict';
const root=document.querySelector('[data-raster-editor]');
if(!root)return;
const q=(s)=>root.querySelector(s);
const canvas=q('[data-raster-canvas]');
if(!canvas)return;
const ctx=canvas.getContext('2d');
const image=new Image();
const fields=JSON.parse(root.dataset.fields||'{}');
const info=JSON.parse(root.dataset.config||'{}');
let layers=Array.isArray(info.overlays)?JSON.parse(JSON.stringify(info.overlays)):[];
let selected=layers.length?layers[0].id:null;
let mode='select', drag=null, preview=false, imageReady=false, history=[];
const range=(a,b,v)=>Math.min(b,Math.max(a,v));
const toNum=(v,d)=>Number.isFinite(Number(v))?Number(v):d;
const status=q('[data-raster-status]');
const saveBtn=q('[data-raster-save]');
const name=root.dataset.name;
const csrf=root.dataset.csrf;
const imageSrc=root.dataset.image;
const colorDefault='#FFFFFF';

function note(s,ok){
 if(!status)return;
 status.textContent=s||'';
 status.classList.toggle('ok',ok===true);
 status.classList.toggle('bad',ok===false);
}
function remember(){history.push(JSON.stringify(layers));if(history.length>35)history.shift();}
function byId(id){return layers.find(l=>l.id===id);}
function active(){return byId(selected);}
function uid(){return 'ly_'+Math.random().toString(36).slice(2,11);}
function setMode(value){mode=value;note(mode==='draw'?'Drag on the artwork to draw an editable text area.':'Select and drag a region to move it. Drag the bottom-right square to resize.');canvas.style.cursor=mode==='draw'?'crosshair':'default';}
function canvasPoint(event){
 const box=canvas.getBoundingClientRect();
 return {x:range(0,1000,(event.clientX-box.left)/box.width*1000),
         y:range(0,1000,(event.clientY-box.top)/box.height*1000)};
}
function regionPx(box){return {
 x:box.x/1000*canvas.width,y:box.y/1000*canvas.height,
 w:box.w/1000*canvas.width,h:box.h/1000*canvas.height
};}
function sample(field){return ({
 title:'YOUR HEADLINE',subtitle:'Promotional subtitle',brand:'YOUR BRAND',product:'PRODUCT NAME',
 price:'$49.00',date:'SALE ENDS SOON',contact_email:'contact@example.com',
 description:'Write the campaign description here',cta:'SHOP NOW',campaign_name:'CAMPAIGN',offer_text:'SPECIAL OFFER',website:'example.com',discount_label:'SAVE 20%',custom_1:'EXTRA MESSAGE',custom_2:'NEW ARRIVAL',custom_3:'FEATURED',custom_4:'YOUR MESSAGE'
})[field]||'PROMOTIONAL TEXT';}
function shapePath(layer){
 ctx.beginPath();
 if(Array.isArray(layer.points)&&layer.points.length>=3){
  for(let i=0;i<layer.points.length;i++){
   const p=layer.points[i];
   const x=p.x/1000*canvas.width,y=p.y/1000*canvas.height;
   if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);
  }
  ctx.closePath();
 }else{
  const r=regionPx(layer);ctx.rect(r.x,r.y,r.w,r.h);
 }
}
function drawText(layer,alpha){
 const r=regionPx(layer);
 const px=Math.max(10,layer.size/1000*canvas.width);
 ctx.save();ctx.globalAlpha=alpha;
 if(Array.isArray(layer.points)&&layer.points.length>=3){shapePath(layer);ctx.clip();}
 ctx.fillStyle=layer.color||colorDefault;
 ctx.font=(layer.bold?'700 ':'500 ')+px+'px system-ui,Arial,sans-serif';
 const text=sample(layer.field);
 const parts=text.split(' ');
 let lines=[], line='';
 for(const word of parts){
  const candidate=(line?line+' ':'')+word;
  if(ctx.measureText(candidate).width>r.w&&line){lines.push(line);line=word;}
  else{line=candidate;}
 }
 if(line)lines.push(line);
 ctx.textAlign=layer.align||'left';ctx.textBaseline='top';
 let tx=r.x;
 if(layer.align==='center')tx=r.x+r.w/2;
 if(layer.align==='right')tx=r.x+r.w;
 const lh=px*1.25;
 lines.slice(0,Math.floor(r.h/lh)||1).forEach((str,i)=>ctx.fillText(str,tx,r.y+i*lh,r.w));
 ctx.restore();
}
function draw(){
 if(!imageReady)return;
 ctx.clearRect(0,0,canvas.width,canvas.height);
 ctx.drawImage(image,0,0,canvas.width,canvas.height);
 for(const layer of layers){
  if(preview){drawText(layer,.95);continue;}
  const r=regionPx(layer),isActive=layer.id===selected;
  ctx.save();
  ctx.fillStyle=isActive?'rgba(131,119,255,.13)':'rgba(68,210,171,.07)';
  shapePath(layer);ctx.fill();
  ctx.setLineDash(isActive?[]:[7,5]);
  ctx.lineWidth=Math.max(1.5,canvas.width/600);
  ctx.strokeStyle=isActive?'#7865ff':'#2bb895';
  ctx.stroke();
  ctx.setLineDash([]);
  const title=fields[layer.field]||layer.field;
  const font=Math.max(12,canvas.width/78);
  ctx.font='700 '+font+'px system-ui,Arial,sans-serif';
  const capWidth=Math.min(r.w,ctx.measureText(title).width+font*1.2);
  const capHeight=font*1.6;
  ctx.fillStyle=isActive?'#6452dc':'#168f75';
  ctx.fillRect(r.x,r.y-capHeight>0?r.y-capHeight:r.y,capWidth,capHeight);
  ctx.fillStyle='#fff';ctx.textBaseline='middle';
  ctx.fillText(title,r.x+font*.45,r.y-capHeight>0?r.y-capHeight*.5:r.y+capHeight*.5,capWidth-font*.6);
  if(isActive){
   const handle=Math.max(11,canvas.width/70);
   ctx.fillStyle='#fff';ctx.fillRect(r.x+r.w-handle/2,r.y+r.h-handle/2,handle,handle);
   ctx.strokeStyle='#6452dc';ctx.strokeRect(r.x+r.w-handle/2,r.y+r.h-handle/2,handle,handle);
  }
  ctx.restore();
 }
}
function syncList(){
 const host=q('[data-raster-layers]');if(!host)return;
 host.textContent='';
 if(!layers.length){const empty=document.createElement('div');empty.className='raster-empty';empty.textContent='No regions yet. Draw manually or detect existing marketing text with OCR.';host.appendChild(empty);}
 layers.forEach((item,i)=>{
  const button=document.createElement('button');button.type='button';
  button.className='raster-layer'+(selected===item.id?' is-active':'');
  const left=document.createElement('span');
  const title=document.createElement('strong');title.textContent=(i+1)+'. '+(fields[item.field]||item.field);
  const desc=document.createElement('small');
  const origin=item.detected?(' · OCR '+Math.round(item.confidence*100)+'%: '+item.detected):'';
  desc.textContent=(item.shape||'rect').toUpperCase()+' · X '+Math.round(item.x/10)+'% · Y '+Math.round(item.y/10)+'%'+origin;
  left.append(title,desc);
  const sw=document.createElement('span');sw.className='layer-sw';sw.style.background=item.color||colorDefault;
  button.append(left,sw);
  button.addEventListener('click',()=>{selected=item.id;sync();});
  host.appendChild(button);
 });
}
function syncProps(){
 const l=active(), panel=q('[data-raster-props]');if(!panel)return;
 panel.hidden=!l;
 if(!l)return;
 q('[data-field]').value=l.field;
 q('[data-color]').value=l.color||colorDefault;
 q('[data-size]').value=l.size||30;
 q('[data-align]').value=l.align||'left';
 q('[data-bold]').checked=!!l.bold;
 q('[data-selected-label]').textContent=fields[l.field]||l.field;
}
function sync(){syncList();syncProps();draw();}
function newLayer(box,field,shape='rect',points=null){
 if(layers.length>=32){note('A template supports up to 32 text areas.',false);return;}
 remember();
 const layer={id:uid(),field:field||'title',x:Math.round(box.x*100)/100,y:Math.round(box.y*100)/100,
              w:Math.round(box.w*100)/100,h:Math.round(box.h*100)/100,
              size:34,color:colorDefault,align:'left',bold:true};
 if(shape!=='rect'&&Array.isArray(points)){layer.shape=shape;layer.points=points;}
 layers.push(layer);selected=layer.id;
 sync();note('Text region added. Select a field and adjust formatting.');
}
function hitTest(pt){
 for(let i=layers.length-1;i>=0;i--){
  const l=layers[i],inside=pt.x>=l.x&&pt.y>=l.y&&pt.x<=l.x+l.w&&pt.y<=l.y+l.h;
  if(inside){
   const handle=Math.abs(pt.x-(l.x+l.w))<25&&Math.abs(pt.y-(l.y+l.h))<25;
   let contained=!Array.isArray(l.points);
   if(!contained){
    let odd=false;
    for(let k=0,j=l.points.length-1;k<l.points.length;j=k++){
     const a=l.points[k],b=l.points[j];
     if((a.y>pt.y)!==(b.y>pt.y)&&pt.x<(b.x-a.x)*(pt.y-a.y)/(b.y-a.y)+a.x)odd=!odd;
    }
    contained=odd;
   }
   if(handle||contained)return {l,handle};
  }
 }
 return null;
}
canvas.addEventListener('pointerdown',(e)=>{
 if(!imageReady||preview)return;
 const pt=canvasPoint(e);
 if(mode==='draw'){
  drag={type:'create',start:pt,current:pt};canvas.setPointerCapture(e.pointerId);return;
 }
 const hit=hitTest(pt);
 if(!hit){selected=null;sync();return;}
 selected=hit.l.id;remember();
 drag={type:hit.handle?'resize':'move',start:pt,original:JSON.parse(JSON.stringify(hit.l))};
 canvas.setPointerCapture(e.pointerId);sync();
});
canvas.addEventListener('pointermove',(e)=>{
 if(!drag)return;
 const pt=canvasPoint(e);
 if(drag.type==='create'){drag.current=pt;draw();
  ctx.save();ctx.strokeStyle='#7865ff';ctx.lineWidth=3;ctx.setLineDash([8,5]);
  const a=regionPx({x:Math.min(pt.x,drag.start.x),y:Math.min(pt.y,drag.start.y),w:Math.abs(pt.x-drag.start.x),h:Math.abs(pt.y-drag.start.y)});
  ctx.strokeRect(a.x,a.y,a.w,a.h);ctx.restore();return;}
 const l=active();if(!l)return;
 const dx=pt.x-drag.start.x,dy=pt.y-drag.start.y;
 if(drag.type==='move'){
  l.x=Math.round(range(0,1000-l.w,drag.original.x+dx)*100)/100;
  l.y=Math.round(range(0,1000-l.h,drag.original.y+dy)*100)/100;
  if(Array.isArray(drag.original.points))l.points=drag.original.points.map(p=>({
   x:Math.round((p.x+l.x-drag.original.x)*100)/100,
   y:Math.round((p.y+l.y-drag.original.y)*100)/100
  }));
 }else{
  l.w=Math.round(range(15,1000-l.x,drag.original.w+dx)*100)/100;
  l.h=Math.round(range(15,1000-l.y,drag.original.h+dy)*100)/100;
  if(Array.isArray(drag.original.points)){
   const orig=drag.original;
   l.points=orig.points.map(p=>({
    x:Math.round((l.x+(p.x-orig.x)*l.w/orig.w)*100)/100,
    y:Math.round((l.y+(p.y-orig.y)*l.h/orig.h)*100)/100
   }));
  }
 }
 draw();
});
canvas.addEventListener('pointerup',finish);
canvas.addEventListener('pointercancel',finish);
function finish(){
 if(!drag)return;
 if(drag.type==='create'){
  const start=drag.start,end=drag.current;
  const box={x:Math.min(start.x,end.x),y:Math.min(start.y,end.y),w:Math.abs(start.x-end.x),h:Math.abs(start.y-end.y)};
  if(box.w>=15&&box.h>=15)newLayer(box,q('[data-add-field]').value||'title');
  else note('Draw a larger text area (at least 1.5% of image).',false);
  setMode('select');
 }
 drag=null;sync();
}
q('[data-draw]').addEventListener('click',()=>{preview=false;setMode('draw');});
window.DigiRasterEditor={
 canvas,ctx,
 isReady:()=>imageReady,
 addFreeRegion(points,shape){
  if(!imageReady||!Array.isArray(points)||points.length<3||layers.length>=32)return false;
  const step=Math.max(1,Math.ceil(points.length/78));
  const simplified=points.filter((_,i)=>i%step===0||i===points.length-1).slice(0,80);
  const xs=simplified.map(p=>p.x),ys=simplified.map(p=>p.y);
  const x=Math.min(...xs),y=Math.min(...ys);
  const w=Math.max(...xs)-x,h=Math.max(...ys)-y;
  if(w<15||h<15)return false;
  preview=false;
  newLayer({x,y,w,h},q('[data-add-field]').value||'title',shape,simplified);
  return true;
 },
 point(e){
  const r=canvas.getBoundingClientRect();
  return {x:range(0,1000,(e.clientX-r.left)/r.width*1000),
          y:range(0,1000,(e.clientY-r.top)/r.height*1000)};
 },
 draw, note
};
q('[data-preview]').addEventListener('click',()=>{
 preview=!preview;q('[data-preview]').setAttribute('aria-pressed',String(preview));
 note(preview?'Sample preview enabled. Downloaded output uses actual PostgreSQL data.':'Region outlines restored.');
 draw();
});
q('[data-delete]').addEventListener('click',()=>{
 if(!active())return;remember();layers=layers.filter(l=>l.id!==selected);
 selected=layers.length?layers[layers.length-1].id:null;sync();note('Selected region removed. Save mapping to persist.');
});
const clearRegions=q('[data-clear-regions]');
if(clearRegions)clearRegions.addEventListener('click',()=>{
 if(!layers.length)return;
 if(!window.confirm('Clear all text regions from the editor? The saved mapping stays unchanged until you save again.'))return;
 remember();layers=[];selected=null;preview=false;sync();
 note('Regions cleared in the editor. Draw new text regions and save to replace the previous mapping.');
});
q('[data-undo]').addEventListener('click',()=>{
 if(!history.length){note('No changes to undo.');return;}
 layers=JSON.parse(history.pop());selected=layers.length?layers[layers.length-1].id:null;sync();note('Last change undone.');
});
function update(prop,parse){
 const el=q('[data-'+prop+']');
 el.addEventListener('change',()=>{const l=active();if(!l)return;remember();l[prop]=parse?parse(el):el.value;sync();});
}
update('field');update('color');update('align');
update('size',(el)=>range(8,120,Math.round(toNum(el.value,30))));
update('bold',(el)=>el.checked);
q('[data-save-json]').addEventListener('click',async ()=>{
 if(!layers.length){note('Draw at least one text area before saving.',false);return;}
 note('Saving your visual mapping...');saveBtn.disabled=true;
 try{
  const response=await fetch('/admin/templates/raster/save',{
   method:'POST',credentials:'same-origin',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({name,checksum:root.dataset.checksum,csrf,layers})
  });
  let result={};try{result=await response.json();}catch(e){}
  if(!response.ok)throw new Error(result.error||'Save failed ('+response.status+')');
  note('Saved successfully. Open Content records to add values and generate images.',true);
  const link=q('[data-continue]');if(link)link.style.display='';
 }catch(e){note(e.message||'Unable to save',false);}
 finally{saveBtn.disabled=false;}
});
q('[data-auto]').addEventListener('click',async ()=>{
 if(!imageReady)return;
 const button=q('[data-auto]');
 if(layers.length>=32){note('A template supports up to 32 regions. Remove some before scanning.',false);return;}
 button.disabled=true;
 note('Reading visible promotional text with local OCR. No regions will be added unless text is recognized.');
 try{
  const response=await fetch('/admin/templates/raster/suggest?name='+encodeURIComponent(name),{
   method:'GET',credentials:'same-origin',headers:{'Accept':'application/json'},
   cache:'no-store'
  });
  const info=await response.json();
  if(!response.ok)throw new Error(info.error||'Text detection unavailable');
  if(!Array.isArray(info.suggestions)||!info.suggestions.length){
   note(info.message||'No eligible text was detected. No labels were placed.',false);
   return;
  }
  let added=0,skipped=0;
  const proposed=[];
  for(const item of info.suggestions){
   if(!Object.prototype.hasOwnProperty.call(fields,item.field)){
    skipped++;continue;
   }
   if(layers.some(l=>l.field===item.field)||proposed.some(l=>l.field===item.field)){
    skipped++;continue;
   }
   if(layers.length+proposed.length>=32)break;
   const box={x:item.x,y:item.y,w:item.w,h:item.h};
   if(!['x','y','w','h'].every(k=>Number.isFinite(box[k]))||
      box.w<15||box.h<15||box.x<0||box.y<0||
      box.x+box.w>1000.01||box.y+box.h>1000.01){
    skipped++;continue;
   }
   const overlaps=layers.concat(proposed).some(l=>{
    const x=Math.max(l.x,box.x),y=Math.max(l.y,box.y);
    const area=Math.max(0,Math.min(l.x+l.w,box.x+box.w)-x)*
               Math.max(0,Math.min(l.y+l.h,box.y+box.h)-y);
    return area>box.w*box.h*.2;
   });
   if(overlaps){skipped++;continue;}
   const layer={
    id:uid(),field:item.field,shape:'rect',
    x:box.x,y:box.y,w:box.w,h:box.h,
    size:range(8,120,item.size||34),
    color:item.color||colorDefault,
    align:item.align||'left',bold:!!item.bold,
    detected:typeof item.detected==='string'?item.detected.slice(0,80):'',
    confidence:typeof item.confidence==='number'?item.confidence:0
   };
   proposed.push(layer);
  }
  if(!proposed.length){
   note('Detected text did not provide new valid, non-overlapping promotional regions. Existing work was kept.',false);
   return;
  }
  remember();
  layers=layers.concat(proposed);added=proposed.length;
  selected=proposed[0].id;preview=false;setMode('select');sync();
  note('OCR found '+added+' matching promotional text region'+(added===1?'':'s')+
      ' at the actual text coordinates. Check and save the mapping.',true);
 }catch(err){
  note((err&&err.message)||'Could not read the uploaded artwork.',false);
 }finally{button.disabled=false;}
});
window.addEventListener('resize',draw);
image.onload=()=>{
 imageReady=true;
 const ratio=Math.min(1,1600/image.naturalWidth,1200/image.naturalHeight);
 canvas.width=Math.max(1,Math.round(image.naturalWidth*ratio));
 canvas.height=Math.max(1,Math.round(image.naturalHeight*ratio));
 canvas.style.aspectRatio=canvas.width+'/'+canvas.height;
 note(layers.length?'Existing text regions loaded. Drag or resize to adjust.':'Draw regions manually or detect existing marketing text with OCR.');
 sync();
};
image.onerror=()=>note('Unable to load image preview. Check file access.',false);
image.src=imageSrc;
syncList();syncProps();
})();
"""

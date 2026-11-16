"""Freehand and polygon selection controls for promotional text-only artwork.

Uses the existing canvas editor's data model and respects its field allowlist.
"""
SCRIPT = r"""
(function(){
'use strict';
const root=document.querySelector('[data-raster-editor]');
const editor=window.DigiRasterEditor;
if(!root||!editor)return;
const q=s=>root.querySelector(s);
const canvas=editor.canvas,ctx=editor.ctx;
const polygon=q('[data-polygon]'),lasso=q('[data-lasso]'),
      finish=q('[data-finish-shape]'),cancel=q('[data-cancel-shape]'),
      rectangle=q('[data-draw]'),preview=q('[data-preview]');
let tool='select',points=[],hover=null,drawing=false;
function message(s,ok){editor.note(s,ok);}
function reset(){
 tool='select';points=[];hover=null;drawing=false;
 canvas.style.cursor='default';editor.draw();
}
function start(name){
 tool=name;points=[];hover=null;drawing=false;
 canvas.style.cursor='crosshair';editor.draw();
 message(name==='polygon'
  ? 'Polygon: click around the area. Finish with the button or by clicking the first point.'
  : 'Freehand: press and draw a closed lasso with the pointer.');
}
function path(){
 editor.draw();
 if(!editor.isReady()||points.length===0)return;
 ctx.save();
 ctx.beginPath();
 points.forEach((pt,i)=>{
  const x=pt.x/1000*canvas.width,y=pt.y/1000*canvas.height;
  if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
 });
 if(tool==='polygon'&&hover)
  ctx.lineTo(hover.x/1000*canvas.width,hover.y/1000*canvas.height);
 ctx.strokeStyle='#a48fff';ctx.lineWidth=Math.max(2,canvas.width/700);
 ctx.setLineDash([7,5]);ctx.stroke();ctx.setLineDash([]);
 if(tool==='polygon'){
  points.forEach(p=>{
   ctx.beginPath();ctx.arc(p.x/1000*canvas.width,p.y/1000*canvas.height,5,0,Math.PI*2);
   ctx.fillStyle='#a48fff';ctx.fill();
  });
 }
 ctx.restore();
}
function complete(kind){
 if(points.length<3){message('Select at least 3 points.',false);return;}
 const ok=editor.addFreeRegion(points,kind);
 reset();
 message(ok?'Freeform text area added. Assign its marketing field and save the mapping.':
  'The area is too small or the layer limit was reached.',ok);
}
function take(e){
 if(tool==='select')return false;
 e.preventDefault();e.stopImmediatePropagation();
 return true;
}
canvas.addEventListener('pointerdown',e=>{
 if(!take(e)||!editor.isReady())return;
 const pt=editor.point(e);
 if(tool==='polygon'){
  if(points.length>=3&&Math.hypot(pt.x-points[0].x,pt.y-points[0].y)<14){
   complete('polygon');return;
  }
  if(points.length>=80){message('Maximum 80 vertices. Finish this polygon.',false);return;}
  points.push(pt);hover=pt;path();
  message(points.length+' vertices selected · Click first point to close or Finish polygon.');
 }else{
  points=[pt];drawing=true;
  canvas.setPointerCapture(e.pointerId);
  path();
 }
},true);
canvas.addEventListener('pointermove',e=>{
 if(!take(e)||!editor.isReady())return;
 const pt=editor.point(e);
 if(tool==='polygon'){
  hover=pt;
  if(points.length)path();
 }else if(drawing){
  const previous=points[points.length-1];
  if(Math.hypot(previous.x-pt.x,previous.y-pt.y)>3&&points.length<490)points.push(pt);
  path();
 }
},true);
canvas.addEventListener('pointerup',e=>{
 if(!take(e))return;
 if(tool==='lasso'&&drawing){
  drawing=false;complete('freehand');
 }
},true);
canvas.addEventListener('pointercancel',e=>{
 if(!take(e))return;
 reset();message('Selection canceled.');
},true);
if(polygon)polygon.addEventListener('click',()=>start('polygon'));
if(lasso)lasso.addEventListener('click',()=>start('lasso'));
if(finish)finish.addEventListener('click',()=>{
 if(tool==='polygon')complete('polygon');
 else message('Select Polygon and click at least 3 vertices first.',false);
});
if(cancel)cancel.addEventListener('click',()=>{
 reset();message('Free selection canceled.');
});
if(rectangle)rectangle.addEventListener('click',()=>reset());
if(preview)preview.addEventListener('click',()=>reset());
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'&&tool!=='select'){reset();message('Free selection canceled.');}
 if(e.key==='Enter'&&tool==='polygon'){
  e.preventDefault();complete('polygon');
 }
});
})();
"""

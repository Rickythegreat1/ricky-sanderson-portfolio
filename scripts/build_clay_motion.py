#!/usr/bin/env python3
"""Create edition-specific motion from the preserved case implementation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'case.js').read_text()
def replace(old,new):
 global s
 if s.count(old)!=1:raise ValueError('Expected one preserved case motion block: '+old[:70])
 s=s.replace(old,new)
replace("press:120, feedback:220, dialog:380, exit:220, page:460", "press:120, feedback:180, dialog:260, exit:160, page:260")
replace("  const running = new WeakMap();", "  const reduced = matchMedia('(prefers-reduced-motion: reduce)');\n  const running = new WeakMap();")
replace("  let resizeFrame;", "  document.fonts?.ready.then(()=>galleries.forEach(measure=>measure()));\n  let resizeFrame;")
replace("  function revealLinkedMotion(){", "  document.querySelectorAll('details').forEach(details=>details.addEventListener('toggle',()=>{if(details.open)galleries.forEach(measure=>measure());}));\n  function revealLinkedMotion(){")
replace("  if(screenshotLinks.length){", "  screenshotLinks.forEach(link=>{link.setAttribute('role','button');link.setAttribute('aria-haspopup','dialog');link.addEventListener('keydown',event=>{if(event.key===' '){event.preventDefault();link.click();}});});\n  if(screenshotLinks.length){")
replace("    if (!element.animate) return Promise.resolve();", "    if (reduced.matches || !element.animate) return Promise.resolve();")
replace("  function stopVideos(scope=document) {", "  reduced.addEventListener('change',event=>{if(event.matches)[...activeAnimations].forEach(finishAnimation);});\n  function stopVideos(scope=document) {")
replace("const hidden=panels.map(panel=>panel.hidden);let height=0;\n      panels.forEach(panel=>{panel.hidden=false;height=Math.max(height,panel.scrollHeight);});\n      panels.forEach((panel,i)=>{panel.hidden=hidden[i];});wrap.style.minHeight=`${Math.ceil(height)}px`;marker();", "wrap.style.minHeight='0px';wrap.style.height='auto';marker();")
replace("animate(panel,wasHidden?{opacity:0,transform:`translateX(${direction*32}px)`}:{opacity:getComputedStyle(panel).opacity,transform:getComputedStyle(panel).transform},{opacity:1,transform:'translateX(0)'},'page');", "animate(panel,{boxShadow:'inset 0 2px 0 rgba(6,7,10,.24)'},{boxShadow:'inset 0 2px 0 rgba(6,7,10,0)'},'page');")
replace("animate(panel,{opacity:getComputedStyle(panel).opacity,transform:getComputedStyle(panel).transform},{opacity:0,transform:`translateX(${-direction*24}px)`},'exit').then(()=>{if(generations[i]===generation&&selected!==i)panel.hidden=true;});", "panel.hidden=true; // Replace overlapping crossfade with an immediate semantic switch and incoming slide.")
replace("      });marker();\n    }\n    gallery.classList", "      });measure();\n    }\n    gallery.classList")
replace("const box=dialog.getBoundingClientRect();const style=getComputedStyle(dialog);const from={opacity:style.opacity,transform:style.transform};", "const box=dialog.getBoundingClientRect();const style=getComputedStyle(dialog);const from={opacity:1,transform:style.transform,clipPath:'inset(0 0 0 0)'};")
replace("animate(ghost,from,{opacity:0,transform:'translateY(8px) scale(.985)'},'exit')", "animate(ghost,from,{opacity:1,transform:'translateY(8px) scale(.99)',clipPath:'inset(0 0 100% 0)'},'exit')")
replace("const from=departing?{opacity:getComputedStyle(departing).opacity,transform:getComputedStyle(departing).transform}:{opacity:0,transform:'translateY(14px) scale(.985)'};", "const from=departing?{opacity:1,transform:getComputedStyle(departing).transform}:{opacity:1,transform:'translateY(12px) scale(.99)'};")
# Replace the departing surface with a focus-return microinteraction.
start=s.index('    function close(){')
end=s.index("    closeButton.addEventListener",start)
s=s[:start]+"""    function close(){
      if(!dialog.open)return;
      ++exitGeneration;departing?.remove();departing=null;
      dialog.close();document.body.classList.remove('viewer-open');
      const returned=opener;returned?.focus({preventScroll:true});
      if(returned){returned.classList.add('inspection-return');animate(returned,{outlineOffset:'1px'},{outlineOffset:'5px'},'exit').then(()=>returned.classList.remove('inspection-return'));}
    }
"""+s[end:]
replace("caption.textContent=link.closest('figure').querySelector('figcaption')?.textContent||'';", "caption.textContent=(link.closest('figure').querySelector('figcaption')?.innerText||'').replace(/\\s+/g,' ').trim();")
replace("viewport.scrollTop=0;viewport.scrollLeft=0;", "const factor=value==='fit'?0:Number(value);const x=Number(opener?.dataset.zoomFocusX||0),y=Number(opener?.dataset.zoomFocusY||0);\n      viewport.scrollLeft=factor&&x?Math.max(0,width*factor*x-viewport.clientWidth/2):0;viewport.scrollTop=factor&&y?Math.max(0,(picture.naturalHeight||0)*factor*y-viewport.clientHeight/2):0;")
replace('data-zoom="fit" aria-pressed="true">Fit</button>', 'data-zoom="fit" aria-pressed="true">Fit width</button>')
replace("zoomButtons.forEach(button=>button.addEventListener('click',()=>applyZoom(button.dataset.zoom)));", "zoomButtons.forEach(button=>button.addEventListener('click',()=>{applyZoom(button.dataset.zoom);viewport.focus({preventScroll:true});}));")
replace('Open original <span aria-hidden="true">↗</span>', 'Original <span aria-hidden="true">↗</span>')
replace('Choose 100% or 200%, then scroll to pan. Arrow keys work in the image area.', 'Zoom, then scroll or use arrow keys to pan.')
replace("caption.textContent=(link.closest('figure').querySelector('figcaption')?.innerText||'').replace(/\\s+/g,' ').trim();", "caption.textContent=link.dataset.viewerCaption||(link.closest('figure').querySelector('figcaption')?.innerText||'').replace(/\\s+/g,' ').trim();")
# Editorial diagrams can open their source without embedding a duplicate bitmap.
replace("originalWidth=Number(link.querySelector('img').getAttribute('width'))||link.querySelector('img').naturalWidth;", "const thumbnail=link.querySelector('img');originalWidth=Number(link.dataset.sourceWidth||thumbnail?.getAttribute('width'))||thumbnail?.naturalWidth||0;")
replace("picture.src=link.href;picture.alt=link.querySelector('img').alt;", "picture.src=link.href;picture.alt=link.dataset.sourceAlt||link.querySelector('img')?.alt||'Source image';")
replace("const after=details.getBoundingClientRect().height;\n      details.style.overflow='clip';\n      animate(details,{height:`${before}px`},{height:`${after}px`},'dialog').then(()=>{if(current===generation){details.style.height='';details.style.overflow='';}});", "details.style.overflow='';\n      animate(summary,{backgroundColor:'#f0f0f2'},{backgroundColor:'transparent'},'feedback');")
replace("dialog.querySelector('.viewer-original').href=link.href;applyZoom('fit');", "dialog.querySelector('.viewer-original').href=link.href;applyZoom(link.dataset.viewerStart||'fit');")
(ROOT/'versions/clay-case.js').write_text(s)
print('Built versions/clay-case.js')

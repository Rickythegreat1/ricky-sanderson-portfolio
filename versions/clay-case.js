(() => {
  'use strict';
  // Shared Taska motion vocabulary. State, navigation and focus never wait for pixels.
  const MOTION = Object.freeze({press:120, feedback:180, dialog:260, exit:160, page:260, easing:'cubic-bezier(.2,.8,.2,1)'});
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const running = new WeakMap();
  const deadlines = new WeakMap(), finishResolvers = new WeakMap();
  const activeAnimations = new Set();
  function clearDeadline(animation){const timer=deadlines.get(animation);if(timer!==undefined){clearTimeout(timer);deadlines.delete(animation);}}
  function cancelAnimation(animation){
    if(!animation)return;
    clearDeadline(animation);activeAnimations.delete(animation);
    try{animation.cancel();}catch{}
    finishResolvers.get(animation)?.();
  }
  function finishAnimation(animation){
    if(!animation)return;
    clearDeadline(animation);
    try{animation.finish();}catch{try{animation.cancel();}catch{}}
    finishResolvers.get(animation)?.();
  }
  function animate(element, from, to, kind='feedback') {
    const old = running.get(element);
    if (old) {
      const current = getComputedStyle(element);
      from = Object.fromEntries(Object.keys(to).map(key => [key, current[key]]));
      cancelAnimation(old);
    }
    if (reduced.matches || !element.animate) return Promise.resolve();
    const animation = element.animate([from,to], {duration:MOTION[kind], easing:MOTION.easing, fill:'none'});
    const timelineTime=element.ownerDocument?.timeline?.currentTime;
    if(Number.isFinite(timelineTime))animation.startTime=timelineTime;
    running.set(element,animation);
    activeAnimations.add(animation);
    let resolveDeadline;
    const deadlinePromise=new Promise(resolve=>{resolveDeadline=resolve;});
    finishResolvers.set(animation,resolveDeadline);
    deadlines.set(animation,setTimeout(()=>{if(running.get(element)===animation)finishAnimation(animation);},MOTION[kind]+80));
    return Promise.race([animation.finished.catch(()=>{}),deadlinePromise]).finally(()=>{
      clearDeadline(animation);activeAnimations.delete(animation);finishResolvers.delete(animation);
      if(running.get(element)===animation)running.delete(element);
    });
  }
  reduced.addEventListener('change',event=>{if(event.matches)[...activeAnimations].forEach(finishAnimation);});
  function stopVideos(scope=document) {
    scope.querySelectorAll('video').forEach(video=>{video.pause();try{video.currentTime=0;}catch{}});
  }
  const galleries=[];
  document.querySelectorAll('[data-tabs]').forEach(gallery=>{
    const tablist=gallery.querySelector('[data-tablist]');
    const tabs=[...gallery.querySelectorAll('[data-tab]')];
    const panels=[...gallery.querySelectorAll('[data-panel]')];
    const wrap=gallery.querySelector('.gallery-panels');
    if(!tablist||!wrap||tabs.length<2||tabs.length!==panels.length)return;
    let selected=Math.max(0,tabs.findIndex(tab=>tab.hash===location.hash));
    const generations=panels.map(()=>0);
    function marker(){const tab=tabs[selected];gallery.style.setProperty('--rail-x',`${tab.offsetLeft}px`);gallery.style.setProperty('--rail-width',`${tab.offsetWidth}px`);}
    function measure(){
      wrap.style.minHeight='0px';wrap.style.height='auto';marker();
    }
    function activate(index){
      if(index<0||index>=tabs.length||index===selected)return;
      const direction=index>selected?1:-1;selected=index;stopVideos(gallery);
      tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===selected));tab.tabIndex=i===selected?0:-1;});
      panels.forEach((panel,i)=>{
        const generation=++generations[i];const active=i===selected;const wasHidden=panel.hidden;
        panel.inert=!active;panel.setAttribute('aria-hidden',String(!active));
        if(active){
          panel.hidden=false;
          animate(panel,{boxShadow:'inset 0 2px 0 rgba(6,7,10,.24)'},{boxShadow:'inset 0 2px 0 rgba(6,7,10,0)'},'page');
        }else if(!wasHidden){
          panel.hidden=true; // Replace overlapping crossfade with an immediate semantic switch and incoming slide.
        }
      });measure();
    }
    gallery.classList.add('is-enhanced');tablist.setAttribute('role','tablist');
    tabs.forEach((tab,i)=>{
      const panel=panels[i];tab.id||=`${gallery.dataset.tabs}-tab-${i+1}`;
      tab.setAttribute('role','tab');tab.setAttribute('aria-controls',panel.id);tab.setAttribute('aria-selected',String(i===selected));tab.tabIndex=i===selected?0:-1;
      panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',tab.id);panel.tabIndex=0;panel.hidden=i!==selected;panel.inert=i!==selected;panel.setAttribute('aria-hidden',String(i!==selected));
      tab.addEventListener('click',event=>{event.preventDefault();activate(i);});
      tab.addEventListener('keydown',event=>{
        let next=i;
        if(event.key==='ArrowRight')next=(i+1)%tabs.length;
        else if(event.key==='ArrowLeft')next=(i+tabs.length-1)%tabs.length;
        else if(event.key==='Home')next=0;
        else if(event.key==='End')next=tabs.length-1;
        else if(event.key===' '){event.preventDefault();activate(i);return;}
        else return;
        event.preventDefault();tabs[next].focus();tabs[next].scrollIntoView({block:'nearest',inline:'nearest'});activate(next);
      });
    });
    tablist.addEventListener('scroll',marker,{passive:true});
    gallery.querySelectorAll('img').forEach(img=>img.addEventListener('load',measure));
    measure();galleries.push(measure);
  });

  // Native details keeps its immediate keyboard and accessibility semantics.
  // Measured layout follows the new state; no delayed semantic collapse.
  document.querySelectorAll('details').forEach(details=>{
    const summary=details.querySelector('summary');let generation=0;
    summary.addEventListener('click',event=>{
      event.preventDefault();const before=details.getBoundingClientRect().height;
      const current=++generation;const prior=running.get(details);if(prior)cancelAnimation(prior);
      details.style.height='';
      if(details.open&&details.contains(document.activeElement)&&document.activeElement!==summary)summary.focus();
      details.open=!details.open;
      if(details.open)galleries.forEach(measure=>measure());
      details.style.overflow='';
      animate(summary,{backgroundColor:'#f0f0f2'},{backgroundColor:'transparent'},'feedback');
    });
  });

  // Screenshot inspection stays in context. Native dialog owns focus and modality.
  const screenshotLinks=[...document.querySelectorAll('.omni-hero>a,.omni-screen>a,.omni-mobile>a,[data-screenshot]')];
  screenshotLinks.forEach(link=>{link.setAttribute('role','button');link.setAttribute('aria-haspopup','dialog');link.addEventListener('keydown',event=>{if(event.key===' '){event.preventDefault();link.click();}});});
  if(screenshotLinks.length){
    const dialog=document.createElement('dialog');dialog.className='image-viewer';dialog.setAttribute('aria-labelledby','viewer-title');
    dialog.innerHTML='<header><h2 id="viewer-title">Image inspection</h2><button type="button" class="viewer-close" aria-label="Close screenshot">Close <span aria-hidden="true">×</span></button></header><div class="viewer-tools" role="group" aria-label="Image zoom"><button type="button" data-zoom="fit" aria-pressed="true">Fit width</button><button type="button" data-zoom="1" aria-pressed="false">100%</button><button type="button" data-zoom="2" aria-pressed="false">200%</button><a class="viewer-original" target="_blank" rel="noopener">Original <span aria-hidden="true">↗</span><span class="sr-only"> (opens in a new tab)</span></a></div><p class="viewer-help" id="viewer-help">Zoom, then scroll or use arrow keys to pan.</p><div class="viewer-scroll" tabindex="0" role="region" aria-label="Image area" aria-describedby="viewer-help"><img alt=""></div><p class="viewer-caption"></p>';
    document.body.append(dialog);
    const picture=dialog.querySelector('img'), caption=dialog.querySelector('.viewer-caption'), viewport=dialog.querySelector('.viewer-scroll'), closeButton=dialog.querySelector('.viewer-close');
    const zoomButtons=[...dialog.querySelectorAll('[data-zoom]')];
    let opener=null,departing=null,exitGeneration=0,zoom='fit',originalWidth=0;
    function applyZoom(value){
      zoom=value;
      zoomButtons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.zoom===value)));
      const width=originalWidth||picture.naturalWidth;
      picture.style.width=value==='fit'?'100%':`${width*Number(value)}px`;
      const factor=value==='fit'?0:Number(value);const x=Number(opener?.dataset.zoomFocusX||0),y=Number(opener?.dataset.zoomFocusY||0);
      viewport.scrollLeft=factor&&x?Math.max(0,width*factor*x-viewport.clientWidth/2):0;viewport.scrollTop=factor&&y?Math.max(0,(picture.naturalHeight||0)*factor*y-viewport.clientHeight/2):0;
    }
    zoomButtons.forEach(button=>button.addEventListener('click',()=>{applyZoom(button.dataset.zoom);viewport.focus({preventScroll:true});}));
    picture.addEventListener('load',()=>applyZoom(zoom));
    function close(){
      if(!dialog.open)return;
      ++exitGeneration;departing?.remove();departing=null;
      dialog.close();document.body.classList.remove('viewer-open');
      const returned=opener;returned?.focus({preventScroll:true});
      if(returned){returned.classList.add('inspection-return');animate(returned,{outlineOffset:'1px'},{outlineOffset:'5px'},'exit').then(()=>returned.classList.remove('inspection-return'));}
    }
    closeButton.addEventListener('click',close);
    dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
    dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)close();}});
    screenshotLinks.forEach(link=>link.addEventListener('click',event=>{
      if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
      event.preventDefault();opener=link;
      const from=departing?{opacity:1,transform:getComputedStyle(departing).transform}:{opacity:1,transform:'translateY(12px) scale(.99)'};
      ++exitGeneration;departing?.remove();departing=null;
      originalWidth=Number(link.querySelector('img').getAttribute('width'))||link.querySelector('img').naturalWidth;
      picture.src=link.href;picture.alt=link.querySelector('img').alt;caption.textContent=link.dataset.viewerCaption||(link.closest('figure').querySelector('figcaption')?.innerText||'').replace(/\s+/g,' ').trim();
      dialog.querySelector('.viewer-original').href=link.href;applyZoom('fit');
      dialog.showModal();document.body.classList.add('viewer-open');closeButton.focus();
      animate(dialog,from,{opacity:1,transform:'translateY(0) scale(1)'},'dialog');
    }));
  }
  document.querySelectorAll('details').forEach(details=>details.addEventListener('toggle',()=>{if(details.open)galleries.forEach(measure=>measure());}));
  function revealLinkedMotion(){
    if(location.hash!=='#motion-reference')return;
    const target=document.getElementById('motion-reference');
    if(target){target.open=true;galleries.forEach(measure=>measure());target.scrollIntoView({block:'start'});}
  }
  document.querySelectorAll('a[href="#motion-reference"]').forEach(link=>link.addEventListener('click',()=>{const target=document.getElementById('motion-reference');if(target){target.open=true;galleries.forEach(measure=>measure());}}));
  window.addEventListener('hashchange',revealLinkedMotion);revealLinkedMotion();
  document.fonts?.ready.then(()=>galleries.forEach(measure=>measure()));
  let resizeFrame;
  window.addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>galleries.forEach(measure=>measure()));});
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'){stopVideos();[...activeAnimations].forEach(finishAnimation);}});
})();

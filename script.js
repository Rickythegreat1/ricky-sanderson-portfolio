(() => {
  'use strict';
  // Shared Taska motion vocabulary. State, navigation and focus never wait for pixels.
  const MOTION = Object.freeze({press:120, feedback:220, dialog:380, exit:220, page:460, easing:'cubic-bezier(.2,.8,.2,1)'});
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
    if (!element.animate) return Promise.resolve();
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
      const hidden=panels.map(panel=>panel.hidden);let height=0;
      panels.forEach(panel=>{panel.hidden=false;height=Math.max(height,panel.scrollHeight);});
      panels.forEach((panel,i)=>{panel.hidden=hidden[i];});wrap.style.minHeight=`${Math.ceil(height)}px`;marker();
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
          animate(panel,wasHidden?{opacity:0,transform:`translateX(${direction*32}px)`}:{opacity:getComputedStyle(panel).opacity,transform:getComputedStyle(panel).transform},{opacity:1,transform:'translateX(0)'},'page');
        }else if(!wasHidden){
          animate(panel,{opacity:getComputedStyle(panel).opacity,transform:getComputedStyle(panel).transform},{opacity:0,transform:`translateX(${-direction*24}px)`},'exit').then(()=>{if(generations[i]===generation&&selected!==i)panel.hidden=true;});
        }
      });marker();
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
      const after=details.getBoundingClientRect().height;
      details.style.overflow='clip';
      animate(details,{height:`${before}px`},{height:`${after}px`},'dialog').then(()=>{if(current===generation){details.style.height='';details.style.overflow='';}});
    });
  });

  // Screenshot inspection stays in context. Native dialog owns focus and modality.
  const screenshotLinks=[...document.querySelectorAll('.omni-hero>a,.omni-screen>a,.omni-mobile>a')];
  if(screenshotLinks.length){
    const dialog=document.createElement('dialog');dialog.className='image-viewer';dialog.setAttribute('aria-labelledby','viewer-title');
    dialog.innerHTML='<header><h2 id="viewer-title">Application screenshot</h2><button type="button" aria-label="Close screenshot">Close <span aria-hidden="true">×</span></button></header><div class="viewer-scroll"><img alt=""></div><p class="viewer-caption"></p>';
    document.body.append(dialog);const picture=dialog.querySelector('img');const caption=dialog.querySelector('.viewer-caption');let opener=null,departing=null,exitGeneration=0;
    function close(){
      if(!dialog.open)return;
      const box=dialog.getBoundingClientRect();const style=getComputedStyle(dialog);const from={opacity:style.opacity,transform:style.transform};
      const ghost=dialog.cloneNode(true);ghost.removeAttribute('open');ghost.removeAttribute('aria-labelledby');ghost.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));ghost.setAttribute('aria-hidden','true');ghost.inert=true;ghost.classList.add('viewer-departing');
      Object.assign(ghost.style,{position:'fixed',left:`${box.left}px`,top:`${box.top}px`,width:`${box.width}px`,height:`${box.height}px`,margin:'0',display:'flex'});
      ghost.querySelector('.viewer-scroll').scrollTop=dialog.querySelector('.viewer-scroll').scrollTop;
      departing?.remove();departing=ghost;document.body.append(ghost);
      const generation=++exitGeneration;dialog.close();document.body.classList.remove('viewer-open');opener?.focus({preventScroll:true});
      animate(ghost,from,{opacity:0,transform:'translateY(8px) scale(.985)'},'exit').then(()=>{if(exitGeneration===generation){ghost.remove();departing=null;}});
    }
    dialog.querySelector('button').addEventListener('click',close);
    dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
    dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)close();}});
    screenshotLinks.forEach(link=>link.addEventListener('click',event=>{
      if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
      event.preventDefault();opener=link;
      const from=departing?{opacity:getComputedStyle(departing).opacity,transform:getComputedStyle(departing).transform}:{opacity:0,transform:'translateY(14px) scale(.985)'};
      ++exitGeneration;departing?.remove();departing=null;
      picture.src=link.href;picture.alt=link.querySelector('img').alt;caption.textContent=link.closest('figure').querySelector('figcaption')?.textContent||'';
      dialog.showModal();document.body.classList.add('viewer-open');dialog.querySelector('button').focus();dialog.querySelector('.viewer-scroll').scrollTop=0;
      animate(dialog,from,{opacity:1,transform:'translateY(0) scale(1)'},'dialog');
    }));
  }
  let resizeFrame;
  window.addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>galleries.forEach(measure=>measure()));});
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'){stopVideos();[...activeAnimations].forEach(finishAnimation);}});
})();

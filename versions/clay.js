/* Additive edition choreography. Existing case galleries, zoom, motion examples,
   local demos and native video controls are preserved by the shared scripts. */
(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const sections=document.getElementById('case-sections'), sectionReturn=document.querySelector('.case-section-return');
  if(sections&&sectionReturn&&'IntersectionObserver' in window){
    new IntersectionObserver(entries=>{const above=entries[0].boundingClientRect.bottom<0;const entering=above&&sectionReturn.hidden;sectionReturn.hidden=!above;if(entering&&!reduced.matches)sectionReturn.animate([{opacity:0,transform:'translateY(8px)'},{opacity:1,transform:'translateY(0)'}],{duration:180,easing:'ease-out'});},{threshold:0}).observe(sections);
  }
  const targets = [...document.querySelectorAll('.featured-grid, .decision-strip, .method-card, .support-card, .contact-section, .case-feature-figure, .interaction-pair')];
  if (!reduced.matches && 'IntersectionObserver' in window) {
    targets.forEach(el => el.classList.add('reveal-target'));
    document.documentElement.classList.add('motion-ready');
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) { entry.target.classList.add('is-revealed'); observer.unobserve(entry.target); }
      });
    }, {threshold:.08, rootMargin:'0px 0px 20px 0px'});
    targets.forEach(el => observer.observe(el));
    reduced.addEventListener('change',event => { if(event.matches) { observer.disconnect(); targets.forEach(el=>el.classList.add('is-revealed')); } });
  }
  document.querySelectorAll('details').forEach(details=>details.addEventListener('toggle',()=>{if(!details.open)details.querySelectorAll('video').forEach(video=>video.pause());}));
  document.querySelectorAll('.evidence-inspect').forEach(details => {
    const summary=details.querySelector('summary'), content=details.querySelector('.evidence-content');
    if(!summary||!content)return;
    summary.addEventListener('click',event=>{
      if(reduced.matches||!summary.animate)return;
      event.preventDefault();
      details.open=!details.open;
      summary.animate([{backgroundColor:'#f0f0f2'},{backgroundColor:'transparent'}],{duration:180,easing:'ease-out'});
    });
  });
})();
(() => {
  function revealDisclosure() {
    const id=decodeURIComponent(location.hash.slice(1));
    if(!id)return;
    const target=document.getElementById(id);
    if(target?.tagName==='DETAILS')target.open=true;
  }
  addEventListener('hashchange',revealDisclosure);
  revealDisclosure();
})();

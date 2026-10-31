(()=>{'use strict';
 const $=s=>document.querySelector(s), all=s=>[...document.querySelectorAll(s)];
 const check='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4 10-10"/></svg>';
 const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let storage;try{storage=localStorage;}catch{}
 let store=MACState.create(storage),pendingTimer=null,operation=0;
 const ease='cubic-bezier(.22,1,.36,1)',reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
 function animate(el,frames,options){const a=el.animate(frames,{duration:240,easing:ease,...options,...(reducedMotion?{duration:1,delay:0}:{})});a.finished.catch(()=>{});return a;}
 function paint(el,html,focus){const height=el.getBoundingClientRect().height;el.getAnimations().forEach(a=>a.cancel());el.innerHTML=html;const next=el.getBoundingClientRect().height;el.style.overflow='';if(height&&Math.abs(height-next)>2){const sizing=animate(el,[{height:height+'px'},{height:next+'px'}],{duration:320});if(document.body.dataset.app==='student'){el.style.overflow='clip';sizing.finished.then(()=>el.style.overflow='').catch(()=>{});}}animate(el,[{opacity:.3,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}],{duration:260});if(focus)requestAnimationFrame(()=>el.querySelector(focus)?.focus({preventScroll:true}));}
 function cancelJob(){operation++;clearTimeout(pendingTimer);pendingTimer=null;}
 const app=document.body.dataset.app;
 if(app==='student'){
  let student='01',selected='',phase='choose',busy=false,error='',lastUndo=null,identityDraft='';
  const panel=$('#student-panel'),say=t=>{$('#student-status').textContent=t;};
  const person=()=>store.get().find(r=>r.id===student);
  function render(focus){
   all('.step-indicator i').forEach((el,i)=>el.classList.toggle('active',i<({identify:1,choose:2,done:3}[phase])));
   if(phase==='identify'){
    paint(panel,`<h1 class="student-title" tabindex="-1">Start check-in.</h1><p class="subtitle">Enter your student number.</p><form id="identify-form" novalidate><label class="field-label" for="student-number">Student number</label><input class="text-input" id="student-number" name="student" inputmode="numeric" autocomplete="off" placeholder="01" value="${escape(identityDraft)}" maxlength="2" aria-describedby="number-help${error?' identity-error':''}" ${error?'aria-invalid="true"':''}><p class="field-help" id="number-help">Two-digit student number.</p>${error?`<p class="status-error" id="identity-error" role="alert">${escape(error)}</p>`:''}<div class="action-stack"><button class="button primary" type="submit">Continue <span aria-hidden="true">→</span></button><button class="text-button" type="button" id="back-to-choices">Back to class selection</button></div></form>`,focus||'#student-number');
    $('#identify-form').addEventListener('submit',e=>{e.preventDefault();identityDraft=$('#student-number').value;const value=identityDraft.trim().padStart(2,'0');if(!store.get().some(r=>r.id===value)){error='Enter a student number from 01 to 08.';render('#student-number');return;}student=value;selected='';error='';lastUndo=null;phase=person().present?'done':'choose';render('h1');});
    $('#back-to-choices').onclick=()=>{error='';phase=person().present?'done':'choose';render('h1');};return;
   }
   if(phase==='done'){
    const p=person();paint(panel,`<div class="success-view"><div class="success-symbol">${check}</div><h1 class="student-title" tabindex="-1">You're checked in.</h1><p class="subtitle">Your visit has been recorded.</p><dl class="receipt"><div><dt>Student</dt><dd>${p.name}</dd></div><div><dt>Class / reason</dt><dd>${escape(p.reason)}</dd></div></dl><div class="action-stack"><button class="button primary" id="next-student">Next student <span aria-hidden="true">→</span></button>${lastUndo?'<button class="text-button" id="undo-student">Undo check-in</button>':''}</div>${error?`<p class="status-error" role="alert">${escape(error)}</p>`:''}</div>`,focus||'h1');
    $('#next-student').onclick=()=>{phase='identify';selected='';identityDraft='';lastUndo=null;error='';render();};
    if($('#undo-student'))$('#undo-student').onclick=()=>{try{store.undo(lastUndo);lastUndo=null;error='';phase='choose';render('h1');say('Check-in undone. Your class selection is preserved.');}catch{error='Couldn’t undo the check-in. Try again.';render('h1');}};return;
   }
   const choice=(v)=>`<label class="choice"><input type="radio" name="course" value="${v}" ${selected===v?'checked':''} ${busy?'disabled':''}><span class="choice-surface"><span>${v}</span><span class="choice-check">${check}</span></span></label>`;
   paint(panel,`<h1 class="student-title" tabindex="-1">Check in.</h1><p class="subtitle">Choose a class or reason for your visit.</p><div class="visitor"><span><b class="avatar">${student}</b>${person().name}</span><button class="text-button" id="change-student" ${busy?'disabled':''}>Change</button></div><form id="class-form"><fieldset><legend>Classes</legend><div class="course-grid">${MACState.courses.slice(0,5).map(choice).join('')}</div></fieldset><fieldset><legend>Other reasons</legend><div class="reason-grid">${MACState.courses.slice(5).map(choice).join('')}</div></fieldset>${error?`<p class="status-error" role="alert">${escape(error)}</p>`:''}<div class="checkin-action ${busy?'busy':''}"><p class="selection-note" id="selected-class">${selected?escape(selected):'Select one option to continue.'}</p><button class="button primary" id="confirm-student" type="submit" ${!selected||busy?'disabled':''}><span>${busy?'Checking in…':'Check in'}</span>${busy?'<span class="spinner" aria-hidden="true"></span>':'<span aria-hidden="true">→</span>'}</button>${busy?'<button class="text-button" type="button" id="cancel-student">Cancel check-in</button>':''}</div></form>`,focus);
   $('#change-student').onclick=()=>{cancelJob();phase='identify';error='';render();};
   $('#class-form').onchange=e=>{if(e.target.name!=='course')return;selected=e.target.value;error='';$('#selected-class').textContent=selected;$('#confirm-student').disabled=false;say(`${selected} selected.`);};
   $('#class-form').onsubmit=e=>{e.preventDefault();if(!selected||busy)return;busy=true;error='';setStudentBusy(true);say('Checking in.');const id=++operation;pendingTimer=setTimeout(()=>{if(id!==operation)return;try{store=MACState.create(storage);lastUndo=store.signIn([student],selected);phase='done';busy=false;render();say(`${person().name} checked in for ${selected}.`);}catch(err){busy=false;error=err.message.includes('already')?'You are already checked in. Change students to start another visit.':'Couldn’t save your check-in. Try again.';render('#confirm-student');}},520);};
   if($('#cancel-student'))$('#cancel-student').onclick=()=>{cancelJob();busy=false;error='';setStudentBusy(false);say('Check-in canceled. Your selection is preserved.');};
  }
  function setStudentBusy(on){
   all('#class-form input').forEach(x=>x.disabled=on);$('#change-student').disabled=on;const button=$('#confirm-student');button.disabled=on||!selected;button.innerHTML=on?'<span>Checking in…</span><span class="spinner" aria-hidden="true"></span>':'<span>Check in</span><span aria-hidden="true">→</span>';$('.checkin-action').classList.toggle('busy',on);
   if(on){const b=document.createElement('button');b.type='button';b.className='text-button';b.id='cancel-student';b.textContent='Cancel check-in';b.onclick=()=>{cancelJob();busy=false;setStudentBusy(false);say('Check-in canceled. Your selection is preserved.');};$('.checkin-action').append(b);animate(b,[{opacity:0},{opacity:1}],{duration:150});b.focus({preventScroll:true});}
   else{$('#cancel-student')?.remove();button.focus({preventScroll:true});}
  }
  if(person().present)phase='done';render();
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&busy){e.preventDefault();$('#cancel-student')?.click();}});
 }else if(app==='staff'){
  let selected=new Set(),query='',reason='MATH 15400',busy=false,error='',lastUndo=null,lastMessage='',dialogPhase='review',savedCount=0,savedIds=[],dialogMotion=null;
  const dialog=$('#batch-dialog'),panel=$('#batch-panel'),say=t=>{$('#staff-status').textContent=t;};
  const visible=()=>store.get().filter(r=>`${r.name} ${r.group} ${r.id}`.toLowerCase().includes(query.toLowerCase()));
  function renderRoster(highlight=[]){
   const rows=store.get(),shown=visible();selected=new Set([...selected].filter(id=>rows.some(r=>r.id===id&&!r.present)));
   $('#attendance-count').textContent=`${rows.filter(r=>r.present).length} signed in · ${rows.length} students`;
   $('#review-batch').disabled=!selected.size;$('#review-batch').innerHTML=`Bulk sign-in${selected.size?` <span>(${selected.size})</span>`:' <span aria-hidden="true">↗</span>'}`;
   $('#selection-count').textContent=selected.size?`${selected.size} selected`:'Select students to sign in';
   $('#roster').innerHTML=shown.map(r=>`<tr data-id="${r.id}" class="${selected.has(r.id)?'selected ':''}${highlight.includes(r.id)?'highlight':''}"><td><label class="check-hit"><input type="checkbox" value="${r.id}" aria-label="Select ${r.name}" ${r.present?'disabled':''} ${selected.has(r.id)?'checked':''}></label></td><td class="student-name">${r.name}<span>${r.group}${r.present?' · '+escape(r.reason):''}</span></td><td class="table-muted">${r.group}</td><td class="table-muted">${r.present?escape(r.reason):'—'}</td><td><span class="presence ${r.present?'in':''}"><i aria-hidden="true"></i>${r.present?'Signed in':'Not signed in'}</span></td><td>${r.present?`<button class="row-action" data-signout="${r.id}" aria-label="Sign out ${r.name}">Sign out</button>`:''}</td></tr>`).join('');
   $('#empty-search').hidden=!!shown.length;document.querySelector('table').hidden=!shown.length;
   const available=shown.filter(r=>!r.present),picked=available.filter(r=>selected.has(r.id));$('#select-all').disabled=!available.length;$('#select-all').checked=!!available.length&&picked.length===available.length;$('#select-all').indeterminate=!!picked.length&&picked.length<available.length;
   all('#roster input').forEach(el=>el.onchange=()=>{el.checked?selected.add(el.value):selected.delete(el.value);syncSelection();say(`${selected.size} selected.`);});
   all('[data-signout]').forEach(el=>el.onclick=()=>{const id=el.dataset.signout;try{lastUndo=store.signOut(id);lastMessage=`Student ${id} signed out.`;renderRoster([id]);renderNotice();say(lastMessage);$('#undo-batch')?.focus({preventScroll:true});}catch{lastMessage='Couldn’t save the change. Try again.';renderNotice();}});
  }
  function syncSelection(){
   all('#roster tr').forEach(tr=>tr.classList.toggle('selected',selected.has(tr.dataset.id)));
   $('#review-batch').disabled=!selected.size;$('#review-batch').innerHTML=`Bulk sign-in${selected.size?` <span>(${selected.size})</span>`:' <span aria-hidden="true">↗</span>'}`;
   $('#selection-count').textContent=selected.size?`${selected.size} selected`:'Select students to sign in';
   const available=visible().filter(r=>!r.present),picked=available.filter(r=>selected.has(r.id));$('#select-all').checked=!!available.length&&picked.length===available.length;$('#select-all').indeterminate=!!picked.length&&picked.length<available.length;
  }
  function renderNotice(){const n=$('#staff-notice');n.innerHTML=lastMessage?`<span>${escape(lastMessage)}</span>${lastUndo?'<button id="undo-batch">Undo</button>':''}`:'';if(lastMessage)animate(n,[{opacity:0,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}]);if($('#undo-batch'))$('#undo-batch').onclick=()=>{try{const ids=lastUndo.map(r=>r.id);store.undo(lastUndo);lastUndo=null;lastMessage='Change undone.';renderRoster(ids);renderNotice();say(lastMessage);($('#review-batch').disabled?$('#student-search'):$('#review-batch')).focus({preventScroll:true});}catch{lastMessage='Couldn’t undo the change. Try again.';renderNotice();}};}
  function closeDialog(){
   cancelJob();busy=false;error='';const completed=dialogPhase==='done',style=getComputedStyle(dialog),from=style.transform,opacity=style.opacity;
   dialogMotion?.cancel();dialog.classList.remove('is-open');const to=innerWidth<=760?'translateY(32px)':'translateX(40px)';
   dialogMotion=animate(dialog,[{opacity,transform:from},{opacity:0,transform:to}],{duration:320});
   dialogMotion.finished.then(()=>{dialog.close();dialogMotion?.cancel();dialogMotion=null;
    if(completed){all('#roster tr').forEach(row=>{if(savedIds.includes(row.dataset.id)){row.classList.remove('highlight');void row.offsetWidth;row.classList.add('highlight');}});savedIds=[];renderNotice();}
    ($('#review-batch').disabled?$('#student-search'):$('#review-batch')).focus({preventScroll:true});
   }).catch(err=>{if(err?.name!=='AbortError')console.error('Drawer return failed:',err);});
  }
  function renderDialog(){
   if(dialogPhase==='done'){paint(panel,`<div class="dialog-success"><div class="success-symbol">${check}</div><h2 id="batch-title" tabindex="-1">${savedCount} student${savedCount===1?'':'s'} signed in.</h2><p class="dialog-caption">${escape(reason)} · Attendance updated</p><button class="button primary" id="close-success">Done</button></div>`,'#close-success');$('#close-success').onclick=closeDialog;return;}
   const rows=store.get().filter(r=>selected.has(r.id));
   paint(panel,`<div class="dialog-top"><span class="context-label">Bulk sign-in</span><button class="close-button" id="close-dialog" aria-label="Cancel bulk sign-in">×</button></div><h2 id="batch-title" tabindex="-1">Sign in ${rows.length} student${rows.length===1?'':'s'}.</h2><p class="dialog-caption">Review the selection before saving.</p><ul class="batch-list">${rows.map(r=>`<li>${r.name}<span>${r.group}</span></li>`).join('')}</ul><label class="field-label" for="batch-reason">Class / reason for visit</label><select id="batch-reason" ${busy?'disabled':''}>${MACState.courses.map(c=>`<option ${c===reason?'selected':''}>${c}</option>`).join('')}</select>${error?`<p class="status-error" role="alert">${escape(error)}</p>`:''}<div class="dialog-actions ${busy?'busy':''}"><button class="button secondary" id="cancel-batch">Cancel</button><button class="button primary" id="confirm-batch" ${busy||!rows.length?'disabled':''}>${busy?'<span class="spinner" aria-hidden="true"></span> Saving…':`Sign in ${rows.length}`}</button></div>`,busy?'#cancel-batch':'#batch-title');
   $('#close-dialog').onclick=closeDialog;$('#cancel-batch').onclick=closeDialog;$('#batch-reason').onchange=e=>reason=e.target.value;
   $('#confirm-batch').onclick=()=>{if(busy||!selected.size)return;busy=true;error='';$('#batch-reason').disabled=true;$('#confirm-batch').disabled=true;$('#confirm-batch').innerHTML='<span class="spinner" aria-hidden="true"></span> Saving…';$('.dialog-actions').classList.add('busy');$('#cancel-batch').focus({preventScroll:true});const ids=[...selected],job=++operation;say('Saving attendance.');pendingTimer=setTimeout(()=>{if(job!==operation)return;try{store=MACState.create(storage);lastUndo=store.signIn(ids,reason);savedCount=ids.length;savedIds=ids;selected.clear();busy=false;dialogPhase='done';lastMessage=`${savedCount} student${savedCount===1?'':'s'} signed in.`;renderRoster();renderDialog();say(lastMessage);}catch(err){busy=false;error=err.message.includes('already')?'Attendance changed. Close this panel and review your selection.':'Couldn’t save attendance. Your selection is still here. Try again.';renderRoster();renderDialog();}},520);};
  }
  $('#student-search').oninput=e=>{query=e.target.value;renderRoster();};$('#clear-search').onclick=()=>{query='';$('#student-search').value='';renderRoster();$('#student-search').focus();};
  $('#select-all').onchange=e=>{visible().filter(r=>!r.present).forEach(r=>e.target.checked?selected.add(r.id):selected.delete(r.id));renderRoster();say(`${selected.size} selected.`);};
  $('#review-batch').onclick=()=>{if(!selected.size)return;dialogPhase='review';busy=false;error='';dialogMotion?.cancel();dialog.classList.remove('is-open');renderDialog();dialog.showModal();void getComputedStyle(dialog,'::backdrop').opacity;requestAnimationFrame(()=>dialog.classList.add('is-open'));dialogMotion=animate(dialog,[{opacity:0,transform:innerWidth<=760?'translateY(24px)':'translateX(32px)'},{opacity:1,transform:'translate(0)'}],{duration:320});};
  dialog.addEventListener('cancel',e=>{e.preventDefault();closeDialog();});
  window.addEventListener('storage',e=>{if(e.key===MACState.key){store=MACState.create(storage);renderRoster();}});renderRoster();
  // Establish the list as one surface; stable headers arrive before its rows.
  [$('.staff-heading'),$('.roster-toolbar'),$('.table-shell')].forEach((el,i)=>animate(el,[{opacity:0,transform:`translateY(${i===2?14:7}px)`},{opacity:1,transform:'translateY(0)'}],{duration:i===2?460:340,delay:i*55,fill:'backwards'}));
 }
})();

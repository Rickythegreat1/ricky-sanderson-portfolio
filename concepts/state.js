/* Local synthetic data only. No network, account or production integration. */
(function(root){
  const courses=['MATH 15400','HER-V 131','HER-V 135','CSCI-N 241','SCI-I 225','Research','Grant','Other'];
  const key='ricky-mac-concept-v1';
  const seed=()=>Array.from({length:8},(_,i)=>({id:String(i+1).padStart(2,'0'),name:`Student ${String(i+1).padStart(2,'0')}`,group:i<4?'Group A':'Group B',present:[2,6].includes(i),reason:[2,6].includes(i)?'MATH 15400':''}));
  function create(storage){
    let rows=seed();
    try{const s=JSON.parse(storage?.getItem(key)||'null');if(Array.isArray(s)&&s.length===8&&s.every((r,i)=>r.id===seed()[i].id&&typeof r.present==='boolean'&&courses.concat('').includes(r.reason)))rows=seed().map((r,i)=>({...r,present:s[i].present,reason:s[i].reason}));}catch{}
    function save(next){storage?.setItem(key,JSON.stringify(next));rows=next;}
    return {get:()=>rows.map(r=>({...r})),signIn(ids,reason){if(!courses.includes(reason))throw Error('Choose a class or reason.');if(!ids.length)throw Error('Select at least one student.');const picked=rows.filter(r=>ids.includes(r.id));if(picked.length!==new Set(ids).size)throw Error('Student not found.');if(picked.some(r=>r.present))throw Error('A selected student is already signed in.');const before=picked.map(r=>({...r}));save(rows.map(r=>ids.includes(r.id)?{...r,present:true,reason}:r));return before;},signOut(id){const before=rows.filter(r=>r.id===id);if(!before.length)throw Error('Student not found.');save(rows.map(r=>r.id===id?{...r,present:false,reason:''}:r));return before;},undo(before){save(rows.map(r=>before.find(b=>b.id===r.id)||r));}};
  }
  const api={courses,key,seed,create};if(typeof module!=='undefined')module.exports=api;else root.MACState=api;
})(typeof window!=='undefined'?window:globalThis);

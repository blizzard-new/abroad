/* Phase 1, revision 2. Local-only task interactions; no account or upload API writes. */
(() => {
'use strict';
history.scrollRestoration='manual';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=n=>'<i data-lucide="'+esc(n)+'" aria-hidden="true"></i>';
const icons=()=>{window.lucide?.createIcons();refreshMotion();};
const motionTargets=new Set();
const motionObserver=new IntersectionObserver(entries=>entries.forEach(e=>e.target.classList.toggle('motion-visible',e.isIntersecting)),{threshold:.05});
function refreshMotion(){
  for(const el of motionTargets)if(!el.isConnected){motionObserver.unobserve(el);motionTargets.delete(el);}
  $$('.meter.animate,.node.done').forEach(el=>{if(!motionTargets.has(el)){motionTargets.add(el);motionObserver.observe(el);}});
}
const sources=window.UNIWAY_PREVIEW_SOURCES, storageKey='uniway.design.application-path.v2';
const writingIds=['motivation','school-reason','learning-goals','course-plan','expected-outcomes','return-plan'];
const fileIds=['transcript','rank','language-file','signed-form'];
const oneStep=new Set(['home','term','target','language','preferences']);
const seed=()=>({selected:'v2-plan-1',plans:sources.map((s,i)=>({id:'v2-plan-'+(i+1),sourceIndex:i,term:i?'上學期':'下學期',steps:i?{}:{home:{value:s.home_university,confirmed:true},term:{value:'下學期',confirmed:true}}}))});
let state;
try { const cached=JSON.parse(localStorage.getItem(storageKey)); state=cached?.plans?.length&&cached.plans.every(p=>p.steps&&sources[p.sourceIndex])?cached:seed(); } catch {state=seed();}
let activeId=null, dirty=false, lastHash='', filter='all', scenario='active', toastTimer, successId=null;
let mapPosition=null, mapPositionPlan=null, firstMap=true;
const plan=()=>state.plans.find(p=>p.id===state.selected)||state.plans[0];
const src=()=>sources[plan().sourceIndex];
const stages=()=>window.UniWayPreviewLevels(src());
const levels=()=>stages().flatMap(s=>s.levels).map((l,i)=>({...l,number:i+1,stageTitle:stages()[l.stage].title}));
const find=id=>levels().find(l=>l.id===id);
const record=id=>plan().steps[id]||{};
const name=s=>s.split(/[（(]/)[0].trim();
const safeUrls=l=>(l.rule?.source_urls||[]).filter(u=>/^https:\/\//.test(u));
function hasContent(l,r=record(l.id)) {
  if(l.kind==='checks')return (r.checks||[]).some(Boolean);
  if(l.kind==='file')return !!r.file?.name;
  if(l.kind==='course')return !!r.course?.name?.trim()&&!!r.course?.reason?.trim();
  if(l.kind==='assemble')return writingIds.every(id=>hasContent(find(id)));
  if(l.kind==='packet')return fileIds.concat('assemble').every(id=>isDone(find(id)));
  return !!String(r.value||'').trim();
}
function progress(l) {
  const r=record(l.id);
  if(l.external)return {value:r.value?.trim()?1:0,total:1};
  if(oneStep.has(l.kind))return {value:r.confirmed&&hasContent(l)?1:0,total:1};
  if(l.kind==='checks')return {value:(r.checks||[]).filter(Boolean).length+(r.confirmed?1:0),total:l.checks.length+1};
  return {value:Number(hasContent(l))+Number(!!r.confirmed&&hasContent(l)),total:2};
}
function isDone(l){const p=progress(l);return !l.external&&p.value===p.total;}
function status(l){return l.external?(hasContent(l)?'recorded':'external'):isDone(l)?'done':progress(l).value?'started':'todo';}
function missing(l) {
  if(l.kind==='assemble')return writingIds.filter(id=>!hasContent(find(id)));
  if(l.kind==='packet')return fileIds.concat('assemble').filter(id=>!isDone(find(id)));
  return [];
}
const next=()=>levels().find(l=>!l.external&&!isDone(l)&&!missing(l).length);
function totals(list=levels()){const counted=list.filter(l=>!l.external);return {value:counted.reduce((n,l)=>n+progress(l).value,0),total:counted.reduce((n,l)=>n+progress(l).total,0),done:counted.filter(isDone).length,count:counted.length,started:counted.filter(l=>status(l)==='started').length};}
const pct=p=>p.total?Math.round(p.value/p.total*100):0;
function meter(p,label,{small=false,big=false,animate=true,gold=false}={}) {
  return '<div class="meter '+(small?'small ':'')+(big?'big ':'')+(animate?'animate ':'')+(gold?'gold':'')+'" role="progressbar" data-empty="'+(p.value===0)+'" aria-label="'+esc(label)+'" aria-valuemin="0" aria-valuemax="'+p.total+'" aria-valuenow="'+p.value+'" aria-valuetext="'+p.value+' / '+p.total+' 個準備步驟"><span class="meter-fill" style="--progress:'+pct(p)+'%">'+[0,.4,.8].map((d,i)=>'<i class="particle '+(i===1?'star':'')+'" style="--delay:'+d+'s" aria-hidden="true"></i>').join('')+'</span></div>';
}
function toast(message,error=false){clearTimeout(toastTimer);const el=$('#toast');el.textContent=message;el.classList.toggle('error',error);el.hidden=false;toastTimer=setTimeout(()=>el.hidden=true,4500);}
function saveState(proposed) {
  if(scenario==='error')return false;
  try {localStorage.setItem(storageKey,JSON.stringify(proposed));state=proposed;return true;}catch{return false;}
}
function commitStep(id,data) {
  const proposed=structuredClone(state), p=proposed.plans.find(p=>p.id===plan().id);
  p.steps[id]=data;
  if(id==='term'&&data.confirmed)p.term=data.value;
  return saveState(proposed);
}
function renderHub(){
  const t=totals(),n=next(),p=plan();
  $('#plan-select').innerHTML=state.plans.map(p=>'<option value="'+esc(p.id)+'" '+(p.id===plan().id?'selected':'')+'>'+esc(name(sources[p.sourceIndex].school_name))+' · '+esc(p.term)+'</option>').join('');
  $('#plan-meta').textContent=src().home_university+' · '+src().academic_year+' 學年度資料';
  $('#overall-caption').textContent=pct(t)+'%';
  $('#overall-meter').innerHTML=meter(t,'整體個人準備',{animate:true});
  $('#stage-select').innerHTML=stages().map(s=>'<option value="'+s.index+'" '+(n?.stage===s.index?'selected':'')+'>'+String(s.index+1).padStart(2,'0')+' · '+esc(s.title)+'</option>').join('');
  stagePicker.sync();
  $('#next-stage').textContent=n?'第 '+(n.stage+1)+' 階段 · 第 '+n.number+' 關':'個人準備已完成';
  $('#next-title').textContent=n?.title||'接下來，留意校方通知';
  $('#next-prompt').textContent=n?.prompt||'自己的準備已完成，正式審查與錄取仍以校方通知為準。';
  $('#next-link').href=n?'#level/'+n.id:'#progress';
  $('#next-link').innerHTML=(n?'繼續這一關':'查看進度總覽')+icon('arrow-right');
  $('#next-meter').innerHTML=n?'<div class="meter-label"><span>這一關</span><strong>'+progress(n).value+' / '+progress(n).total+'</strong></div>'+meter(progress(n),'下一關準備進度',{animate:true}):'';
}
function renderMap(){
  const all=levels(),n=next();
  $('#path-stages').innerHTML=stages().map(s=>{
    const t=totals(s.levels),h=s.levels.length*152+123;
    return '<section class="path-stage" id="stage-'+s.index+'" aria-label="第 '+(s.index+1)+' 階段 '+esc(s.title)+'" style="height:'+h+'px"><svg class="path-svg" aria-hidden="true"></svg><div class="stage-divider"><svg class="stage-wave" viewBox="0 0 640 100" preserveAspectRatio="none" aria-hidden="true"><path d="M0 22 C95 -14 170 42 280 18 S470 -5 640 22 L640 80 C525 115 445 65 330 85 S110 110 0 80Z" fill="#c8eaf3"/><path d="M0 36 C100 5 185 55 290 32 S480 15 640 34 L640 80 C525 115 445 65 330 85 S110 110 0 80Z" fill="#e0f3f8"/></svg><span>'+String(s.index+1).padStart(2,'0')+'</span><h3>'+esc(s.title)+'</h3><small>'+(t.count?t.done+' / '+t.count+' 關':s.levels.filter(l=>hasContent(l)).length+' / '+s.levels.length+' 筆通知')+'</small></div>'+s.levels.map(l=>{
      const level=all.find(x=>x.id===l.id),i=s.levels.indexOf(l),st=status(l),p=progress(l),isCurrent=n?.id===l.id,locked=missing(l).length>0;
      // Reverse lateral direction at every step, continuing across chapter boundaries.
      const x=[.24,.72,.38,.77,.28,.66][(level.number-1)%6]*100;
      const label=l.title+'，'+(locked?'可查看，完成前需先備齊內容':isCurrent?'建議下一步':st==='done'?'已完成':l.external?'外部通知':p.value?'進行中':'可提前辦理');
      return '<div class="level-stop" data-stop="'+l.id+'" style="left:'+x+'%;bottom:'+(122+i*152)+'px"><a class="node '+st+' '+(isCurrent?'current ':'')+(locked?'locked':'')+'" href="#level/'+l.id+'" aria-label="'+esc(label)+'" '+(isCurrent?'aria-current="step"':'')+'>'+(isCurrent?'<span class="current-flag">繼續</span>':'')+icon(st==='done'?'check':locked?'lock-keyhole':l.icon)+'<span class="node-order" aria-hidden="true">'+level.number+'</span></a><span class="node-title">'+esc(l.title)+'</span><div class="node-progress">'+meter(p,l.title+(l.external?'紀錄進度':'進度'),{small:true,gold:st==='done',animate:isCurrent&&p.value>0})+'</div><span class="node-caption">'+(l.external?(p.value?'自行記錄':'等待通知'):p.value+' / '+p.total+' 步')+'</span></div>';
    }).join('')+'</section>';
  }).join('');
  icons();requestAnimationFrame(drawPaths);
}
function drawPaths(){
  const sections=$$('.path-stage');
  sections.forEach((section,sectionIndex)=>{
    const rect=section.getBoundingClientRect(),nodes=$$('.node',section),svg=$('.path-svg',section);
    if(!rect.width||!rect.height)return;
    const nextNode=sections[sectionIndex+1]?.querySelector('.node');
    if(nextNode)nodes.push(nextNode);
    svg.setAttribute('viewBox','0 0 '+rect.width+' '+rect.height);
    svg.innerHTML=nodes.slice(0,-1).map((a,i)=>{
      const b=nodes[i+1],ar=a.getBoundingClientRect(),br=b.getBoundingClientRect();
      const x1=ar.left-rect.left+ar.width/2,y1=ar.top-rect.top+ar.height/2,x2=br.left-rect.left+br.width/2,y2=br.top-rect.top+br.height/2;
      const mid=(y1+y2)/2;
      const st=a.classList.contains('done')?'done':a.classList.contains('started')?'partial':'';
      return '<path class="path-line '+st+'" d="M '+x1+' '+y1+' C '+x1+' '+mid+', '+x2+' '+mid+', '+x2+' '+y2+'"/>';
    }).join('');
  });
}
function scrollMap(id,behavior='smooth'){
  const box=$('#map-scroll'),node=id?$('#path-stages [data-stop="'+id+'"]'):null;
  if(!node){box.scrollTo({top:box.scrollHeight,behavior});return;}
  const a=node.getBoundingClientRect(),b=box.getBoundingClientRect();
  box.scrollTo({top:box.scrollTop+a.top-b.top-box.clientHeight*.48+50,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':behavior});
}
function renderOverview(){
  const t=totals(),todo=t.count-t.done-t.started;
  $('#overview-summary').innerHTML='<div class="overview-stats"><div class="stat-card overall-stat"><span>這份計畫的個人準備</span><strong>'+pct(t)+'%</strong><small>'+t.value+' / '+t.total+' 個小步驟</small>'+meter(t,'進度總覽總進度',{big:true,animate:true})+'</div><div class="stat-card"><span>已完成</span><strong>'+t.done+'</strong><small>關卡</small></div><div class="stat-card"><span>進行中</span><strong>'+t.started+'</strong><small>關卡</small></div><div class="stat-card"><span>尚未開始</span><strong>'+todo+'</strong><small>關卡</small></div></div>';
  let shown=0;
  $('#overview-stages').innerHTML=stages().map(s=>{
    const rows=s.levels.filter(l=>filter==='all'||status(l)===filter);
    if(!rows.length)return '';
    shown+=rows.length;
    const st=totals(s.levels);
    return '<section class="stage-card"><header><span class="square-icon">'+icon(s.icon)+'</span><div><small>第 '+(s.index+1)+' 階段</small><h3>'+esc(s.title)+'</h3></div><span>'+ (st.total?pct(st)+'%':'外部通知')+'</span></header>'+(st.total?meter(st,s.title+'進度'):'')+rows.map(l=>{
      const p=progress(l),s=status(l),num=levels().find(x=>x.id===l.id).number;
      return '<a class="stage-level '+(s==='done'?'is-done':'')+'" href="#level/'+l.id+'"><span>'+(s==='done'?icon('check'):String(num).padStart(2,'0'))+'</span><span><b>'+esc(l.title)+'</b><small>'+(l.external?(hasContent(l)?'學生自行記錄':'未記錄正式通知'):s==='done'?'個人已完成':s==='started'?'已留下內容，待確認':'隨時可以開始')+'</small></span><span class="row-progress">'+(p.value+' / '+p.total+meter(p,l.title+'總覽進度',{small:true,gold:s==='done'}))+'</span></a>';
    }).join('')+'</section>';
  }).join('');
  if(!shown)$('#overview-stages').innerHTML='<div class="overview-empty">'+icon('circle-check')+'<p>這個分類目前沒有關卡。</p></div>';
  icons();
}
function readDraft(){
  const l=find(activeId),form=$('#level-form');if(!l||!form)return null;
  const r={...record(l.id),confirmed:false};
  if(l.kind==='file')return {...r,confirmed:!!$('#self-confirm')?.checked};
  if(l.kind==='checks')r.checks=$$('[data-check]',form).map(el=>el.checked);
  else if(l.kind==='course')r.course={name:$('#course-name').value,reason:$('#course-reason').value,credits:$('#course-credits').value};
  else if(l.kind==='home')r.value=src().home_university;
  else if(l.kind==='target')r.value=src().school_name;
  else if(['term','language'].includes(l.kind))r.value=$('input[name="choice"]:checked',form)?.value||'';
  else if(l.kind==='preferences')r.value=$('#level-input').value;
  else if(['assemble','packet'].includes(l.kind))r.value=hasContent(l)?'reviewed':'';
  else r.value=$('#level-input')?.value||'';
  r.confirmed=!!$('#self-confirm')?.checked;
  return r;
}
function showSaveError(message='這次沒有保存成功，進度尚未更新。你的輸入還在，可以重試。'){
  const error=$('#level-error');if(error){error.hidden=false;error.textContent=message;}
  const note=$('#save-note');if(note)note.textContent='尚未保存';
}
function saveDraft({silent=false}={}){
  const l=find(activeId),r=readDraft();if(!r)return true;
  r.confirmed=false;
  if(!commitStep(l.id,r)){showSaveError();return false;}
  dirty=false;updateLevelProgress();if(!silent)toast('已暫存這一關，之後可以接著完成。');return true;
}
function updateLevelProgress(){
  const l=find(activeId),p=progress(l);
  $('#level-meter').innerHTML=meter(p,l.title+'關卡進度',{animate:true,big:true,gold:isDone(l)});
  $('#level-step-caption').textContent=p.value+' / '+p.total+' 步';
  $('#save-note').textContent='已存於本機預覽';
  icons();
}
function field(l,r){
  const value=esc(r.value||'');
  if(l.kind==='home'||l.kind==='target')return '<div class="choice-box">'+icon(l.icon)+'<div><strong>'+esc(l.kind==='home'?src().home_university:name(src().school_name))+'</strong><small>'+src().academic_year+' 學年度資料 · '+esc(plan().term)+'</small></div></div><p class="preview-hint">目前計畫的學校設定。換目標時，從上方建立另一份獨立計畫。</p>';
  if(l.kind==='term'||l.kind==='language'){
    const choices=l.kind==='term'?['上學期','下學期','尚未決定']:['英語組','日語組','中文組'];
    return '<fieldset style="border:0;margin:0;padding:0"><legend class="input-meta">'+(l.kind==='term'?'出國學期與校內申請梯次分開記錄':'以下為既有母校資料列出的語組，適用性仍需核對')+'</legend><div class="option-grid">'+choices.map(c=>'<label class="option-card"><input type="radio" name="choice" value="'+c+'" '+((r.value||(l.kind==='term'?plan().term:''))===c?'checked':'')+'>'+c+'</label>').join('')+'</div></fieldset>';
  }
  if(l.kind==='checks')return l.checks.map((c,i)=>'<label class="check-row"><input type="checkbox" data-check="'+i+'" '+(r.checks?.[i]?'checked':'')+'><span>'+esc(c)+'</span></label>').join('');
  if(l.kind==='write'||l.kind==='note'||l.kind==='notice'||l.kind==='submission'){
    let intro='';
    if(l.external)intro='<div class="external-notice">'+icon('clock-3')+'<div><strong>沒有通知，就保持未記錄。</strong><br>這裡是學生自行紀錄，不會變成校方已確認的結果。</div></div>';
    if(l.kind==='submission')intro='<a class="official-link" href="'+esc(safeUrls(l)[0]||'#')+'" target="_blank" rel="noopener noreferrer">查看校方公告與入口'+icon('arrow-up-right')+'</a><p class="small-warning">UniWay 不代送申請。開過連結不代表送件成功。</p>';
    return intro+'<label for="level-input">'+(l.kind==='write'?'先留下你的想法':l.external?'通知內容或下一步':l.kind==='submission'?'你的送件紀錄':'這一關的筆記')+'</label><textarea id="level-input" placeholder="'+(l.kind==='write'?'先寫一兩句就好，之後還能修改。':l.kind==='notice'?'收到通知後，再填寫內容與來源。':'寫下目前情況，以及下一個要做的動作。')+'">'+value+'</textarea><div class="input-meta">'+(l.example?'<button type="button" class="hint-toggle" id="show-example" aria-expanded="false">'+icon('lightbulb')+'需要一點提示？</button>':'<span>只存於這份示意計畫</span>')+'<span id="character-count">'+Array.from(r.value||'').length+' 字</span></div>'+(l.example?'<div class="example-note" id="example-copy" hidden>'+esc(l.example)+'<br><small>寫作提示，不是校方指定答案。</small></div>':'');
  }
  if(l.kind==='file')return (r.file?'<div class="file-receipt">'+icon('file-check-2')+'<div><b>'+esc(r.file.name)+'</b><small>示意檔名已記錄 · 尚未上傳檔案</small></div><button type="button" id="remove-file">移除</button></div>':'')+'<div class="upload-box">'+icon('cloud-upload')+'<h3>'+esc(l.title)+'</h3><p>預覽只記住檔名，不會讀取或上傳內容。</p><button type="button" class="outline-button" id="sample-file">'+icon('file-plus-2')+'用示意檔案試試</button></div>';
  if(l.kind==='course')return '<div class="course-fields"><div class="field-row"><div><label for="course-name">想修的課程或領域</label><input id="course-name" type="text" placeholder="例如：你查到的課名" value="'+esc(r.course?.name||'')+'"></div><div><label for="course-credits">學分（選填）</label><input id="course-credits" type="number" min="0" max="100" step=".5" value="'+esc(r.course?.credits||'')+'"></div></div><div><label for="course-reason">為什麼想修這門課？</label><textarea id="course-reason" placeholder="想學什麼、如何連結目前的學習？">'+esc(r.course?.reason||'')+'</textarea></div><a class="official-link" href="'+esc(safeUrls({rule:src().steps[3]}).find(u=>!u.includes('ntpu.edu.tw'))||safeUrls(l)[0])+'" target="_blank" rel="noopener noreferrer">查交換校官方課程資訊'+icon('arrow-up-right')+'</a></div>';
  if(l.kind==='preferences')return '<label for="level-input">這所學校的預計志願序</label><select id="level-input">'+['','1','2','3','4','5'].map(v=>'<option value="'+v+'" '+(r.value===v?'selected':'')+'>'+(v?'第 '+v+' 志願':'請選擇')+'</option>').join('')+'</select><p class="preview-hint">這是個人規劃，不會改動校方系統。正式名額與可填志願數依當期規定。</p>';
  if(l.kind==='assemble')return '<div class="document-preview">'+writingIds.map(id=>{const section=find(id),v=record(id);const text=id==='course-plan'?(v.course?.name? v.course.name+(v.course.credits?'（'+v.course.credits+' 學分）':'')+'\n'+v.course.reason:''):v.value;return '<section><h3>'+esc(section.title)+'</h3><p class="'+(!text?'missing-copy':'')+'">'+esc(text||'這一段還沒寫，點下方關卡接著完成。')+'</p></section>';}).join('')+'</div><div class="next-step-links">'+writingIds.filter(id=>!hasContent(find(id))).map(id=>'<a href="#level/'+id+'">'+esc(find(id).title)+icon('arrow-right')+'</a>').join('')+'</div><button type="button" id="download-draft" class="quiet-button">'+icon('download')+'下載目前的文字草稿</button>';
  if(l.kind==='packet')return fileIds.concat('assemble').map(id=>'<a class="packet-row" href="#level/'+id+'">'+icon(isDone(find(id))?'circle-check':'circle-dashed')+esc(find(id).title)+'<span>'+(isDone(find(id))?'個人已準備':'前往準備')+'</span>'+icon('chevron-right')+'</a>').join('');
  return '';
}
function renderLevel(id,{success=false}={}){
  const l=find(id);if(!l){location.hash='map';return;}
  activeId=id;dirty=false;
  const r=record(id),p=progress(l),missingIds=missing(l);
  const points=l.kind==='write'?['草稿會帶入研修計畫預覽','分段是寫作輔助，格式依當期規定']:l.kind==='file'?['確認文件清楚、版本與申請年度相符','這份預覽只記錄示意檔名']:l.external?['收到正式通知後再填寫','此紀錄不計入個人準備比例']:[];
  $('#level-view').innerHTML='<div class="level-topline"><a href="#map" class="back-link">'+icon('arrow-left')+'回到申請地圖</a><span>'+esc(name(src().school_name))+' · '+esc(plan().term)+'</span></div><div class="level-layout"><div class="level-card"><div class="level-heading"><span class="square-icon">'+icon(l.icon)+'</span><div><p class="eyebrow">第 '+l.number+' 關 · '+esc(l.stageTitle)+'</p><h2 id="level-title">'+esc(l.title)+'</h2>'+(l.external?'<p>學生自行記錄 · 不計入個人準備比例</p>':'')+'</div></div><div class="level-progress"><div><span>這一關的進度</span><strong id="level-step-caption">'+p.value+' / '+p.total+' 步</strong></div><div id="level-meter">'+meter(p,l.title+'關卡進度',{big:true,animate:true,gold:isDone(l)})+'</div></div>'+(success?successMarkup(l):'<form id="level-form" novalidate><div class="level-body"><p class="task-question">'+esc(l.prompt)+'</p>'+(l.warning?'<p class="small-warning">'+esc(l.warning)+'</p>':'')+field(l,r)+(missingIds.length?'<p class="small-warning">'+icon('lock-keyhole')+'可以先查看；完成這關前，還需要 '+missingIds.length+' 項內容。這是此整理工具的前置需求。</p>':'')+(!l.external?'<div class="confirmation"><label class="check-row"><input type="checkbox" id="self-confirm" '+(r.confirmed?'checked':'')+'><span>'+(l.kind==='submission'?'我已自行到校方系統送件，這是我的個人紀錄':l.kind==='file'?'我已確認這份文件的內容與適用版本（示意）':oneStep.has(l.kind)?'我已確認這個選擇':'我已確認這一小步準備好了')+'</span></label></div>':'')+'<p id="level-error" class="error-box" role="alert" hidden></p></div><footer class="level-actions"><span id="save-note">本機示意資料</span><button type="button" id="save-draft" class="outline-button">暫存</button><button type="submit" class="primary-button" id="complete-level">'+(l.external?'保存通知紀錄':'完成這一關')+icon('check')+'</button></footer></form>')+'</div><aside class="level-support"><section class="support-card">'+(points.length?'<h3>'+icon('lightbulb')+'辦理提醒</h3><ul class="support-points">'+points.map(p=>'<li>'+icon('check')+'<span>'+esc(p)+'</span></li>').join('')+'</ul>':'')+'<details class="source-details"><summary>完整規則與官方來源'+icon('chevron-down')+'</summary><p>'+esc(l.rule?.summary||'')+'</p><p>既有 '+src().academic_year+' 學年度資料。本期適用性仍待核對；本次沒有新增資料查核。</p>'+safeUrls(l).slice(0,3).map((url,i)=>'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+(i?'相關官方文件':'官方來源')+icon('arrow-up-right')+'</a>').join('')+'</details></section><div class="context-card"><strong>'+esc(src().home_university)+'</strong>'+esc(name(src().school_name))+' · '+esc(plan().term)+'<br>個人準備 ≠ 校方受理或錄取</div></aside></div>';
  icons();
  if(!success)bindLevel(l);
}
function successMarkup(l){
  const n=next(),t=totals(stages()[l.stage].levels),stageComplete=t.count>0&&t.done===t.count;
  return '<div class="success-state celebration"><div class="success-emblem">'+icon('check')+'</div><h3>'+(l.external?'通知紀錄已留下':stageComplete?'完成「'+esc(l.stageTitle)+'」！':'又完成一小步！')+'</h3><p>'+esc(l.title)+'<br>'+(l.external?'這是學生自行記錄，並非校方驗證。':'已存於這份本機示意計畫。')+'</p>'+meter(progress(l),l.title+'完成進度',{big:true,gold:true,animate:true})+(n?'<a class="primary-button" href="#level/'+n.id+'">下一小步'+icon('arrow-right')+'</a>':'<a class="primary-button" href="#progress">看看全部進度'+icon('arrow-right')+'</a>')+'<button type="button" id="edit-level" class="quiet-button">回頭看看／修改這一關</button></div>';
}
function bindLevel(l){
  const form=$('#level-form');
  form.addEventListener('input',()=>{
    dirty=true;$('#save-note').textContent='尚未暫存';
    const count=$('#character-count');if(count)count.textContent=Array.from($('#level-input').value).length+' 字';
  });
  $('#save-draft').addEventListener('click',()=>saveDraft());
  $('#show-example')?.addEventListener('click',e=>{const box=$('#example-copy');box.hidden=!box.hidden;e.currentTarget.setAttribute('aria-expanded',!box.hidden);});
  $('#sample-file')?.addEventListener('click',()=>setFile({name:l.filename,sample:true}));
  $('#remove-file')?.addEventListener('click',()=>setFile(null));
  function setFile(file){if(!commitStep(l.id,{file,confirmed:false})){showSaveError();return;}renderLevel(l.id);toast(file?'示意檔名已記錄，沒有上傳任何檔案。':'已移除本關示意檔名。');}
  $('#download-draft')?.addEventListener('click',()=>{
    const text='UniWay 研修計畫 · 預覽草稿\n\n'+writingIds.map(id=>{const item=find(id),r=record(id);return item.title+'\n'+(id==='course-plan'?[r.course?.name,r.course?.reason].filter(Boolean).join('\n'):r.value||'（待補）');}).join('\n\n');
    const a=document.createElement('a'),url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));a.href=url;a.download='UniWay-研修計畫-預覽草稿.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  form.addEventListener('submit',e=>{
    e.preventDefault();const r=readDraft();
    let error='';
    if(missing(l).length)error='還有內容未備齊。先點上面的項目完成，再回來確認。';
    else if(l.kind==='checks'&&!l.checks.every((_,i)=>r.checks?.[i]))error='請逐項核對；尚未確認的項目可以先留待準備。';
    else if(!hasContent(l,r))error=l.kind==='file'?'請先用示意檔案試試。':l.external?'有收到通知再記錄，沒有通知不需要完成這關。':'先留下一點內容，再完成這一關。';
    else if(!l.external&&!r.confirmed)error='請先勾選你的個人確認。';
    if(l.kind==='term'&&state.plans.some(p=>p.id!==plan().id&&p.sourceIndex===plan().sourceIndex&&p.term===r.value))error='此學期已有獨立計畫，請回到地圖，從上方切換。';
    if(error){showSaveError(error);$('#level-error').scrollIntoView({block:'nearest',behavior:'instant'});return;}
    if(!commitStep(l.id,r)){showSaveError();return;}
    dirty=false;successId=l.id;renderLevel(l.id,{success:true});window.scrollTo({top:0,behavior:'instant'});
    $('#level-title').setAttribute('tabindex','-1');$('#level-title').focus({preventScroll:true});
  });
}
function showRoute(){
  const hash=location.hash||'#map';
  stagePicker.close(false);
  if(activeId&&dirty&&hash!==lastHash&&!saveDraft({silent:true})){history.replaceState(null,'',lastHash);return;}
  if(lastHash==='#map'){mapPosition=$('#map-scroll').scrollTop;mapPositionPlan=plan().id;}
  activeId=null;dirty=false;successId=null;lastHash=hash;
  const levelId=hash.startsWith('#level/')?hash.slice(7):null;
  $('#hub').hidden=!!levelId;$('#level-view').hidden=!levelId;
  if(levelId){renderLevel(levelId);window.scrollTo({top:0,behavior:'instant'});const title=$('#level-title');if(title){title.setAttribute('tabindex','-1');title.focus({preventScroll:true});}return;}
  const tab=hash==='#progress'?'progress':'map';
  $('#map-view').hidden=tab!=='map';$('#progress-view').hidden=tab!=='progress';
  $$('[data-tab]').forEach(a=>{a.classList.toggle('active',a.dataset.tab===tab);if(a.dataset.tab===tab)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  renderHub();
  if(tab==='progress'){renderOverview();window.scrollTo({top:0,behavior:'instant'});}
  else {renderMap();requestAnimationFrame(()=>{if(mapPosition!==null&&mapPositionPlan===plan().id)$('#map-scroll').scrollTop=mapPosition;else if(firstMap){scrollMap(next()?.id,'instant');window.scrollTo({top:0,behavior:'instant'});firstMap=false;}else scrollMap(next()?.id,'instant');});}
  icons();
}
const stagePicker=new window.UniWayGlideSelect($('#stage-select'));
const motionPreference=matchMedia('(prefers-reduced-motion: reduce)');
let manualMotion=false;
function setMotion(paused){
  document.documentElement.dataset.motion=paused?'paused':'running';
  const button=$('#motion-toggle');
  button.setAttribute('aria-pressed',paused);button.setAttribute('aria-label',paused?'播放動畫':'暫停動畫');button.title=paused?'播放動畫':'暫停動畫';button.innerHTML=icon(paused?'play':'pause');icons();
}
setMotion(motionPreference.matches);
motionPreference.addEventListener('change',e=>{if(!manualMotion)setMotion(e.matches);});
$('#motion-toggle').addEventListener('click',()=>{manualMotion=true;setMotion(document.documentElement.dataset.motion!=='paused');});
$('#level-view').addEventListener('click',e=>{if(e.target.closest('#edit-level'))renderLevel(activeId);});
$('#plan-select').addEventListener('change',e=>{
  const previous=state.selected,proposed=structuredClone(state);proposed.selected=e.target.value;
  if(!saveState(proposed)){$('#plan-select').value=previous;toast('切換尚未保存，請重試。',true);return;}
  mapPosition=null;mapPositionPlan=null;firstMap=false;lastHash='';showRoute();
});
$('#stage-select').addEventListener('change',e=>{const stage=stages()[Number(e.target.value)];scrollMap(stage.levels[0].id);});
$('#go-origin').addEventListener('click',()=>{scrollMap(null);$('#stage-select').value='0';stagePicker.sync();});
$('#go-current').addEventListener('click',()=>{const n=next();if(n){scrollMap(n.id);$('#stage-select').value=n.stage;stagePicker.sync();}});
$$('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;$$('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',x===b));renderOverview();}));
$('#scenario').addEventListener('change',e=>scenario=e.target.value);
$('#reset-demo').addEventListener('click',()=>{
  const fresh=seed();scenario='active';$('#scenario').value='active';
  if(!saveState(fresh)){toast('本機示意資料無法重設。',true);return;}
  activeId=null;dirty=false;mapPosition=null;mapPositionPlan=null;firstMap=true;lastHash='';filter='all';
  $$('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.filter==='all'));
  location.hash='map';showRoute();toast('V2 示意進度已重設，正式帳號未變更。');
});
const planDialog=$('#plan-dialog'),infoDialog=$('#info-dialog'),navDialog=$('#nav-dialog');
$('#mobile-nav').addEventListener('click',()=>navDialog.showModal());
$('#new-plan').addEventListener('click',()=>{$('#create-target').innerHTML=sources.map((s,i)=>'<option value="'+i+'">'+esc(name(s.school_name))+'</option>').join('');planDialog.showModal();});
$('#source-info').addEventListener('click',()=>infoDialog.showModal());
$$('.close-dialog').forEach(b=>b.addEventListener('click',()=>b.closest('dialog').close()));
[planDialog,infoDialog,navDialog].forEach(dialog=>dialog.addEventListener('keydown',e=>{
  if(e.key!=='Tab')return;const controls=$$('button,a[href],select',dialog).filter(el=>el.getClientRects().length);const first=controls[0],last=controls.at(-1);
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
}));
$('#plan-form').addEventListener('submit',e=>{
  e.preventDefault();if(activeId&&dirty&&!saveDraft({silent:true}))return;
  const sourceIndex=Number($('#create-target').value),term=$('#create-term').value,proposed=structuredClone(state);
  let p=proposed.plans.find(p=>p.sourceIndex===sourceIndex&&p.term===term);
  if(!p){p={id:crypto.randomUUID(),sourceIndex,term,steps:{}};proposed.plans.push(p);}
  proposed.selected=p.id;if(!saveState(proposed)){toast('計畫未保存，請重試。',true);return;}
  planDialog.close();activeId=null;dirty=false;mapPosition=null;mapPositionPlan=null;firstMap=true;lastHash='';location.hash='map';showRoute();
});
new ResizeObserver(()=>requestAnimationFrame(drawPaths)).observe($('#map-scroll'));
addEventListener('hashchange',showRoute);
showRoute();
})();

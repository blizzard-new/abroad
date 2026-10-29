/* Account-backed application map. Private edits stay in memory until server CAS succeeds. */
window.UniWayApplicationPath = (() => {
'use strict';
let root, picker, view=null, listing=null, owner='', epoch=0, loading=false, saving=false, active=false;
let activeId=null, dirty=false, filter='all', mapPosition=null, mapPositionPlan=null, toastTimer;
const $=(s,r=root)=>r?.querySelector(s), $$=(s,r=root)=>[...(r?.querySelectorAll(s)||[])];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=n=>'<i data-lucide="'+esc(n)+'" aria-hidden="true"></i>';
const termName=t=>({fall:'上學期',spring:'下學期',full_year:'全學年',undecided:'尚未決定'}[t]||t);
const route=()=>new URLSearchParams(location.hash.split('?')[1]||'');
const href=(tab='map',id='')=>'#my-application?'+new URLSearchParams({plan:view?.plan.id||'',view:tab,...(id?{level:id}:{})});
const plan=()=>view.plan, stages=()=>view?.stages||[];
const levels=()=>stages().flatMap(s=>s.levels.map(l=>({...l,stageTitle:s.title})));
const find=id=>levels().find(l=>l.id===id), record=id=>plan().steps[id]||{};
const progress=l=>l.progress, hasContent=l=>Boolean(record(l.id).value||record(l.id).version_id);
const isDone=l=>l.counted!==false&&!l.external&&l.progress.value===l.progress.total;
const status=l=>l.conditional&&record(l.id).applicable===false?'skipped':l.external?(hasContent(l)?'recorded':'external'):isDone(l)?'done':l.progress.value?'started':'todo';
const missing=l=>l.blocked_by||[], next=()=>levels().find(l=>!l.external&&status(l)!=='skipped'&&!isDone(l)&&!missing(l).length);
const pct=p=>p.total?Math.round(p.value/p.total*100):0;
function totals(list=levels()){const counted=list.filter(l=>!l.external&&l.counted!==false);return {value:counted.reduce((n,l)=>n+progress(l).value,0),total:counted.reduce((n,l)=>n+progress(l).total,0),done:counted.filter(isDone).length,count:counted.length,started:counted.filter(l=>status(l)==='started').length};}
const key=()=>[state.account?.id||'',state.authSessionEpoch,activeHomeSchool()].join('|');
const query=()=>'?'+new URLSearchParams({home_school:activeHomeSchool()});
const pathUrl=()=>'/account/application-paths/'+encodeURIComponent(plan().id);
const urls=l=>(l.source_urls||[]).filter(u=>/^https?:\/\//i.test(u));
const targets=new Set();
const observer=new IntersectionObserver(entries=>entries.forEach(e=>e.target.classList.toggle('motion-visible',e.isIntersecting)),{threshold:.05});
function icons(){
  $$('a[href^="#level/"]').forEach(a=>a.href=href('level',a.getAttribute('href').slice(7)));
  $$('a[href="#map"]').forEach(a=>a.href=href());
  $$('a[href="#progress"]').forEach(a=>a.href=href('progress'));
  window.lucide?.createIcons();
  for(const el of targets)if(!el.isConnected){observer.unobserve(el);targets.delete(el);}
  $$('.meter.animate,.node.done').forEach(el=>{if(!targets.has(el)){targets.add(el);observer.observe(el);}});
}
function meter(p,label,{small=false,big=false,animate=true,gold=false}={}){
  return '<div class="meter '+(small?'small ':'')+(big?'big ':'')+(animate?'animate ':'')+(gold?'gold':'')+'" data-empty="'+!p.value+'" role="progressbar" aria-label="'+esc(label)+'" aria-valuemin="0" aria-valuemax="'+p.total+'" aria-valuenow="'+p.value+'"><span class="meter-fill" style="--progress:'+pct(p)+'%">'+[0,.4,.8].map((d,i)=>'<i class="particle '+(i===1?'star':'')+'" style="--delay:'+d+'s" aria-hidden="true"></i>').join('')+'</span></div>';
}
function toast(text,error=false){clearTimeout(toastTimer);$('#toast').textContent=text;$('#toast').hidden=false;$('#toast').classList.toggle('error',error);toastTimer=setTimeout(()=>$('#toast').hidden=true,5000);}
function message(text,action=''){
  $('#hub').hidden=true;$('#level-view').hidden=true;$('#path-message').hidden=false;$('#archive-plan').hidden=true;
  $('#path-message').innerHTML='<div class="ap-empty">'+icon('route')+'<p>'+esc(text)+'</p>'+action+'</div>';icons();
}
function clear(){epoch++;loading=false;saving=false;view=null;listing=null;dirty=false;activeId=null;mapPosition=null;mapPositionPlan=null;
  if(root){$$('dialog[open]').forEach(d=>d.close());$('#level-view').replaceChildren();$('#plan-select').replaceChildren();$('#path-stages').replaceChildren();$('#overview-summary').replaceChildren();$('#overview-stages').replaceChildren();$('#plan-form').reset();['#plan-meta','#overall-caption','#overall-meter','#next-stage','#next-title','#next-prompt','#next-meter','#deadline-card','#create-target'].forEach(selector=>$(selector)?.replaceChildren());$('#toast').hidden=true;message('登入後，接著完成你的申請。','<button data-path-login class="primary-button">登入</button>');}}
function init(){
  if(root)return;
  root=document.querySelector('#application-path');root.innerHTML=window.UniWayApplicationPathTemplate;
  picker=new window.UniWayGlideSelect($('#stage-select'));
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');let manual=false;
  function motion(paused){root.dataset.motion=paused?'paused':'running';const b=$('#motion-toggle');b.setAttribute('aria-label',paused?'播放動畫':'暫停動畫');b.setAttribute('aria-pressed',paused);b.title=paused?'播放動畫':'暫停動畫';b.innerHTML=icon(paused?'play':'pause');icons();}
  motion(reduced.matches);reduced.addEventListener('change',e=>{if(!manual)motion(e.matches);});
  $('#motion-toggle').onclick=()=>{manual=true;motion(root.dataset.motion!=='paused');};
  $('#refresh-path').onclick=()=>{if(!dirty||confirm('目前文字尚未保存，重新載入會捨棄這次輸入。繼續？'))load(true);};
  $('#new-plan').onclick=openNew;
  $('#archive-plan').onclick=archive;
  $('#source-info').onclick=()=>$('#info-dialog').showModal();
  $$('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());
  $('#plan-form').onsubmit=create;
  $('#plan-select').onchange=e=>{location.hash='#my-application?'+new URLSearchParams({plan:e.target.value,view:'map'});};
  $('#stage-select').onchange=e=>scrollMap(stages()[Number(e.target.value)]?.levels[0]?.id);
  $('#go-origin').onclick=()=>{scrollMap(null);$('#stage-select').value='0';picker.sync();};
  $('#go-current').onclick=()=>{const n=next();if(n){scrollMap(n.id);$('#stage-select').value=n.stage;picker.sync();}};
  $$('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;$$('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',x===b));renderOverview();});
  root.addEventListener('click',e=>{
    if(e.target.closest('[data-path-login]'))openAuthDialog();
    if(e.target.closest('[data-path-new]'))openNew();
    if(e.target.closest('[data-path-retry]'))load(true);
  });
  document.addEventListener('click',e=>{
    if(!active||!dirty||!e.target.closest('a[href]'))return;
    if(!confirm('尚有未保存的修改。確定離開這一關？')){e.preventDefault();e.stopImmediatePropagation();}
    else dirty=false;
  },true);
  addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
  new ResizeObserver(()=>requestAnimationFrame(drawPaths)).observe($('#map-scroll'));
}
function refresh(){if(!root)return;if(owner!==key()){owner=key();clear();if(active)load();}}
function show(page){init();active=page==='my-application';picker.close();if(owner!==key()){owner=key();clear();}
  if(!active)return;
  if(!state.account){message(state.authRestoreState==='pending'?'正在確認登入狀態…':'登入後，接著完成你的申請。','<button data-path-login class="primary-button">登入</button>');return;}
  const requested=route().get('plan');
  if(!view||requested&&view.plan.id!==requested){if(!loading)load();return;}
  render();
}
async function load(force=false){
  if(!state.account)return show('my-application');
  const run=++epoch, captured=key();loading=true;
  message('正在載入你的申請進度…');$('#path-message').classList.add('ap-loading');
  try{
    const list=await fetchJson('/account/application-paths'+query());
    if(run!==epoch||captured!==key())return;
    listing=list;
    const requested=route().get('plan');
    const selected=list.items.find(p=>p.id===requested)||list.items.find(p=>!p.archived)||list.items[0];
    if(!selected){view=null;$('#sync-message').textContent='已連接帳號';message('建立第一份申請計畫','<button data-path-new class="primary-button">'+icon('plus')+'新增計畫</button><a href="#overview" class="quiet-button">查看原有申請紀錄</a>');return;}
    const data=await fetchJson('/account/application-paths/'+selected.id+query());
    if(run!==epoch||captured!==key())return;
    if(route().get('plan')!==requested){load();return;}
    view=data;dirty=false;activeId=null;
    if(mapPositionPlan!==selected.id)mapPosition=null;
    render();
  }catch(e){if(run===epoch&&captured===key()){message(e.message,'<button data-path-retry class="outline-button">重新載入</button>');}}
  finally{if(run===epoch){loading=false;$('#path-message').classList.remove('ap-loading');}}
}
function render(){
  if(!active||!view)return;
  $('#path-message').hidden=true;
  const id=route().get('level'), tab=route().get('view')||'map';
  $('#hub').hidden=tab==='level';$('#level-view').hidden=tab!=='level';
  $('#sync-message').textContent=plan().archived?'已封存 · 紀錄保留':'已同步至帳號';
  $('#archive-plan').hidden=false;$('#archive-plan').textContent=plan().archived?'恢復計畫':'封存計畫';
  const c=plan().context;
  $('#plan-select').innerHTML=listing.items.map(p=>'<option value="'+p.id+'" '+(p.id===plan().id?'selected':'')+'>'+esc(p.context.target_school.split(/[（(]/)[0].trim()+' · '+p.context.departure_year+' '+termName(p.context.semester)+(p.archived?'（已封存）':''))+'</option>').join('');
  $('#plan-meta').textContent=c.home_school+' · '+c.academic_year+' 學年度 · '+(c.application_round||'梯次待確認');
  const t=totals();$('#overall-caption').textContent=pct(t)+'%';$('#overall-meter').innerHTML=meter(t,'整體個人準備');
  $$('[data-tab]').forEach(a=>{a.href=href(a.dataset.tab);a.classList.toggle('active',a.dataset.tab===tab);});
  const n=next();$('#stage-select').innerHTML=stages().map(s=>'<option value="'+s.index+'" '+(n?.stage===s.index?'selected':'')+'>'+String(s.index+1).padStart(2,'0')+' · '+esc(s.title)+'</option>').join('');picker.sync();
  $('#next-stage').textContent=n?'第 '+(n.stage+1)+' 階段 · 第 '+n.number+' 關':'';
  $('#next-title').textContent=n?.title||'個人準備已完成';$('#next-prompt').textContent=n?.prompt||'校方受理與錄取仍以正式通知為準。';
  $('#next-link').href=n?href('level',n.id):href('progress');$('#next-link').innerHTML=(n?'繼續這一關':'查看總覽')+icon('arrow-right');
  $('#next-meter').innerHTML=n?meter(n.progress,'下一關進度'):'';
  const due=levels().filter(l=>l.official_deadline_at&&!isDone(l)).sort((a,b)=>a.official_deadline_at.localeCompare(b.official_deadline_at))[0];
  $('#deadline-card').innerHTML=icon('calendar-search')+'<div><h3>'+(due?'官方期限':'官方日期待確認')+'</h3><p>'+esc(due?new Date(due.official_deadline_at).toLocaleDateString('zh-TW')+(new Date(due.official_deadline_at)<new Date()?' · 已過期':''):'有確切來源，才會顯示期限。')+'</p>'+(due?'<a href="'+href('level',due.id)+'">'+esc(due.title)+icon('arrow-right')+'</a>':'')+'</div>';
  $('#map-view').hidden=tab!=='map';$('#progress-view').hidden=tab!=='progress';
  if(tab==='level'){if(!dirty||activeId!==id)renderLevel(id);}
  else if(tab==='progress'){activeId=null;renderOverview();}
  else{activeId=null;renderMap();requestAnimationFrame(()=>{if(mapPosition!==null&&mapPositionPlan===plan().id)$('#map-scroll').scrollTop=mapPosition;else scrollMap(n?.id,'instant');});}
  icons();
}
function error(text){const el=$('#level-error');if(el){el.hidden=false;el.textContent=text;}else toast(text,true);}
function readStep(){return {value:$('#level-input')?.value||'',confirmed:!!$('#self-confirm')?.checked,version_id:$('#file-version')?.value||null,applicable:$('#file-applicable')?($('#file-applicable').value===''?null:$('#file-applicable').value==='yes'):null};}
async function save(complete=false){
  if(saving||!view||plan().archived)return false;
  const l=find(activeId), data=readStep(), run=epoch,captured=key(),id=plan().id;
  if(complete&&!l.external&&!data.confirmed){error('請先勾選個人確認。');return false;}
  if(!complete)data.confirmed=false;
  saving=true;$$('#level-form button').forEach(b=>b.disabled=true);$('#save-note').textContent='正在同步…';
  try{
    const saved=await fetchJson(pathUrl()+'/steps/'+encodeURIComponent(l.id)+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,step:data})});
    if(run!==epoch||captured!==key()||view?.plan.id!==id)return false;
    view=saved;listing.revision=saved.revision;
    if(active&&activeId===l.id&&route().get('view')==='level'){
      dirty=false;renderLevel(l.id,complete);
    }else if(active){render();}
    toast(complete?'這一關已保存':'草稿已同步');return true;
  }catch(e){if(run===epoch&&captured===key()){error(e.message);$('#save-note').textContent='尚未確認保存';if(e.status===409)$('#conflict-reload').hidden=false;}return false;}
  finally{if(run===epoch){saving=false;$$('#level-form button').forEach(b=>b.disabled=false);}}
}
function field(l,r){
  if(l.kind==='confirm')return '<div class="choice-box">'+icon(l.icon)+'<strong>'+esc(l.prompt)+'</strong></div>';
  if(l.kind==='assemble')return '<div class="document-preview">'+levels().filter(x=>x.kind==='write').map(x=>'<section><h3>'+esc(x.title)+'</h3><p>'+esc(record(x.id).value||'尚未填寫')+'</p><a href="'+href('level',x.id)+'">編輯這一段</a></section>').join('')+'</div><button type="button" id="download-writing" class="outline-button">'+icon('download')+'下載文字草稿</button><a class="outline-button" href="'+pathUrl()+'/writing.docx'+query()+'">'+icon('file-down')+'下載 Word 草稿</a>';
  return (l.conditional?'<label for="file-applicable">這份條件式文件適用於你嗎？</label><select id="file-applicable"><option value="">待確認（暫不計入進度）</option><option value="yes" '+(r.applicable===true?'selected':'')+'>適用</option><option value="no" '+(r.applicable===false?'selected':'')+'>不適用</option></select>':'')+(l.external?'<div class="external-notice">學生自行記錄，不代表校方確認。</div>':'')+
    (l.kind==='submission'?'<p class="small-warning">請在官方系統送件；UniWay 不代送申請。</p>':'')+
    (l.kind==='file'?'<label for="file-version">連結私人文件</label><select id="file-version"><option value="">自行保管（在下方記錄位置）</option>'+(r.version_id?'<option selected value="'+esc(r.version_id)+'">'+esc(r.file_name||'已連結文件')+'</option>':'')+'</select><button type="button" id="load-files" class="quiet-button">'+icon('folder-open')+'選擇我的文件</button><details class="ap-upload"><summary>上傳到私人文件庫</summary><label for="path-file">選擇檔案</label><input type="file" id="path-file"><label class="check-row"><input type="checkbox" id="file-consent"><span>同意加密保存 30 天，用於申請準備；可在私人文件庫撤回。</span></label><button type="button" id="upload-file" class="outline-button">上傳並連結</button></details>':'')+
    '<label for="level-input">'+(l.kind==='write'?'你的想法':l.kind==='file'?'文件位置／備註':'目前紀錄與下一步')+'</label><textarea id="level-input" maxlength="20000" placeholder="先記下一小段，之後還能修改。">'+esc(r.value||'')+'</textarea>';
}
function renderLevel(id,success=false){
  const l=find(id);if(!l){location.hash=href();return;}
  activeId=id;dirty=false;const r=record(id),c=plan().context;
  mapPosition=$('#map-scroll').scrollTop;mapPositionPlan=plan().id;
  const dependencies=missing(l);
  $('#level-view').innerHTML='<div class="level-topline"><a class="back-link" href="'+href()+'">'+icon('arrow-left')+'回到申請地圖</a><span>'+esc(c.target_school+' · '+c.departure_year+' '+termName(c.semester))+'</span></div><div class="level-layout"><div class="level-card"><div class="level-heading"><span class="square-icon">'+icon(l.icon)+'</span><div><p class="eyebrow">第 '+l.number+' 關</p><h2 id="level-title">'+esc(l.title)+'</h2></div></div><div class="level-progress"><div><span>這一關的進度</span><strong>'+l.progress.value+' / '+l.progress.total+'</strong></div>'+meter(l.progress,l.title+'進度',{big:true,gold:isDone(l)})+'</div>'+
    (success?'<div class="success-state celebration"><div class="success-emblem">'+icon('check')+'</div><h3>'+esc(l.external?'通知紀錄已保存':totals(stages()[l.stage].levels).done===totals(stages()[l.stage].levels).count?'完成「'+l.stageTitle+'」！':'又完成一小步！')+'</h3><p>已同步至這份申請計畫</p><a class="primary-button" href="'+(next()?href('level',next().id):href('progress'))+'">'+(next()?'下一小步':'查看總覽')+icon('arrow-right')+'</a><button id="edit-level" class="quiet-button">回頭查看／修改</button></div>':
    '<form id="level-form"><div class="level-body">'+(l.kind==='confirm'?'':'<p class="task-question">'+esc(l.prompt)+'</p>')+(l.warning?'<details class="ap-warning"><summary>需要確認的事項</summary><p>'+esc(l.warning)+'</p></details>':'')+field(l,r)+(dependencies.length?'<div class="small-warning">先完成以下前置事項：'+dependencies.map(k=>'<a href="'+href('level',k)+'">'+esc(find(k)?.title||'前置資料尚未取得')+'</a>').join('')+'</div>':'')+(!l.external?'<label class="check-row confirmation"><input type="checkbox" id="self-confirm" '+(r.confirmed?'checked':'')+'><span>'+(l.kind==='submission'?'我已自行送件，這是個人紀錄':'我已確認這一小步準備好了')+'</span></label>':'')+'<p id="level-error" class="error-box" role="alert" hidden></p><button type="button" id="conflict-reload" class="outline-button" hidden>保留輸入並載入最新進度</button></div><footer class="level-actions"><span id="save-note">已同步至帳號</span><button type="button" id="save-draft" class="outline-button">暫存</button><button type="submit" class="primary-button" '+(plan().archived?'disabled':'')+'>'+esc(l.external?'保存通知紀錄':'完成這一關')+icon('check')+'</button></footer></form>')+'</div><aside class="level-support"><section class="support-card"><details class="source-details"><summary>完整規則與官方來源'+icon('chevron-down')+'</summary><p>'+esc(l.prompt)+'</p>'+urls(l).map((u,i)=>'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">'+(i?'相關官方文件':'官方來源')+icon('arrow-up-right')+'</a>').join('')+'</details>'+(l.official_deadline_at?'<p class="ap-deadline">官方期限：'+esc(new Date(l.official_deadline_at).toLocaleString('zh-TW'))+(new Date(l.official_deadline_at)<new Date()?'（已過期）':'')+'</p>':'')+(l.action_url&&/^https?:\/\//i.test(l.action_url)?'<a class="outline-button" href="'+esc(l.action_url)+'" target="_blank" rel="noopener noreferrer">開啟官方表格'+icon('external-link')+'</a>':'')+(l.kind==='submission'&&urls(l).length?'<a class="outline-button" href="'+esc(urls(l)[0])+'" target="_blank" rel="noopener noreferrer">校方公告與入口'+icon('external-link')+'</a>':'')+'</section><div class="context-card"><strong>'+esc(c.home_school)+'</strong>'+esc(c.academic_year)+' 學年度 · '+esc(c.application_round||'梯次待確認')+'<br>個人準備 ≠ 校方受理或錄取</div></aside></div>';
  if(success)$('#edit-level').onclick=()=>renderLevel(id);
  else{
    $('#level-form').oninput=()=>{dirty=true;$('#save-note').textContent='尚未保存';};
    $('#level-form').onsubmit=e=>{e.preventDefault();save(true);};
    $('#save-draft').onclick=()=>save(false);
    $('#conflict-reload').onclick=async()=>{
      const draft=readStep(),run=epoch,captured=key();
      try{const latest=await fetchJson(pathUrl()+query());if(run!==epoch||captured!==key())return;view=latest;renderLevel(id);if($('#level-input'))$('#level-input').value=draft.value;if($('#self-confirm'))$('#self-confirm').checked=false;if($('#file-applicable'))$('#file-applicable').value=draft.applicable===null?'':draft.applicable?'yes':'no';if(draft.version_id&&$('#file-version')){$('#file-version').add(new Option('這次選擇的文件（保存時重新驗證）',draft.version_id,true,true));}dirty=true;error('已載入最新進度並保留你的文字。請比較後再保存；尚未覆寫其他視窗。');}
      catch(e){if(run===epoch)error(e.message);}
    };
    if(plan().archived){$$('#level-form input,#level-form textarea,#level-form select,#level-form button').forEach(el=>el.disabled=true);$('#save-note').textContent='已封存，恢復計畫後可繼續';}
    if($('#load-files'))$('#load-files').onclick=loadFiles;
    if($('#upload-file'))$('#upload-file').onclick=uploadFile;
    if($('#download-writing'))$('#download-writing').onclick=()=>{
      const text=levels().filter(x=>x.kind==='write').map(x=>x.title+'\n'+(record(x.id).value||'')).join('\n\n');
      const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='UniWay-研修計畫草稿.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    };
  }
  icons();
}
async function loadFiles(){const captured=key(),id=activeId,run=epoch;try{
  const data=await fetchJson('/account/vault/documents');if(captured!==key()||id!==activeId||run!==epoch)return;
  const selected=$('#file-version').value;$('#file-version').innerHTML='<option value="">自行保管（在下方記錄位置）</option>'+data.items.flatMap(d=>d.versions.map(v=>'<option value="'+esc(v.id)+'" '+(v.id===selected?'selected':'')+'>'+esc(v.file_name)+'</option>')).join('');
}catch(e){if(captured===key()&&id===activeId)error(e.message);}}
async function uploadFile(){
  const file=$('#path-file').files[0];if(!file||!$('#file-consent').checked){error('請選擇檔案並確認保存同意。');return;}
  const captured=key(),id=activeId,run=epoch,b=$('#upload-file');b.disabled=true;
  const data=new FormData();Object.entries({label:find(id).title,category:'other',purpose:'application_preparation',retention_days:'30',consent:'true'}).forEach(([k,v])=>data.append(k,v));data.append('file',file);
  try{const saved=await fetchJson('/account/vault/documents',{method:'POST',body:data});if(captured!==key()||id!==activeId||run!==epoch)return;
    const v=saved.versions.at(-1);await loadFiles();if(captured!==key()||id!==activeId||run!==epoch)return;$('#file-version').value=v.id;dirty=true;$('#save-note').textContent='檔案已上傳，正在保存連結';await save(false);
  }catch(e){if(captured===key()&&id===activeId)error(e.message);}finally{if(b.isConnected)b.disabled=false;}
}
async function archive(){
  if(!view||saving)return;
  const archived=!plan().archived;
  if(!confirm(archived?'封存這份計畫？進度與文件會保留，之後可以恢復。':'恢復這份計畫？'))return;
  if(dirty&&!confirm('目前文字尚未保存。確定捨棄這次輸入？'))return;
  const run=epoch,captured=key();saving=true;$('#archive-plan').disabled=true;
  try{
    const saved=await fetchJson(pathUrl()+'/archive'+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,archived})});
    if(run!==epoch||captured!==key())return;
    view=saved;dirty=false;await load();
  }catch(e){if(run===epoch&&captured===key())toast(e.message,true);}
  finally{saving=false;$('#archive-plan').disabled=false;}
}
async function openNew(){
  if(!state.account){openAuthDialog();return;}
  if(dirty&&!confirm('目前文字尚未保存。確定新增其他計畫？'))return;
  const captured=key();$('#create-error').hidden=true;
  try{
    const dashboard=state.dashboard?.school_name===activeHomeSchool()?state.dashboard:await fetchJson('/student-dashboard?school='+encodeURIComponent(activeHomeSchool()));
    if(captured!==key())return;
    const old=listing?.legacy?.context||{}, profile=state.selectionConditions?.profile||{};
    $('#create-home').value=activeHomeSchool();$('#create-target').innerHTML=dashboard.partner_universities.map(p=>'<option '+(p.school_name===old.target_school?'selected':'')+'>'+esc(p.school_name)+'</option>').join('');
    for(const [id,value] of Object.entries({'create-year':old.academic_year||'','create-round':old.application_round||'','create-college':old.college||profile.college||'','create-department':old.department||profile.department||'','create-degree':old.degree_level||profile.degree_level||''}))$('#'+id).value=value;
    $('#plan-dialog').showModal();
  }catch(e){if(captured===key())toast(e.message,true);}
}
async function create(e){
  e.preventDefault();const captured=key(),run=epoch,button=$('#plan-form button[type=submit]');button.disabled=true;
  const payload={revision:listing?.revision||0,home_school:activeHomeSchool(),target_school:$('#create-target').value,academic_year:$('#create-year').value,application_round:$('#create-round').value,departure_year:$('#create-departure').value,semester:$('#create-term').value,college:$('#create-college').value,department:$('#create-department').value,degree_level:$('#create-degree').value,import_existing:$('#import-existing').checked};
  try{const saved=await fetchJson('/account/application-paths',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(captured!==key()||run!==epoch)return;
    $('#plan-dialog').close();view=null;location.hash='#my-application?'+new URLSearchParams({plan:saved.plan.id,view:'map'});load();
  }catch(error){if(captured===key()){$('#create-error').textContent=error.message;$('#create-error').hidden=false;}}
  finally{button.disabled=false;}
}
// The approved map renderer is shared in appearance, never in preview storage.
function renderMap(){
  const all=levels(),n=next();
  $('#path-stages').innerHTML=stages().map(s=>{
    const t=totals(s.levels),h=s.levels.length*152+123;
    return '<section class="path-stage" id="stage-'+s.index+'" aria-label="第 '+(s.index+1)+' 階段 '+esc(s.title)+'" style="height:'+h+'px"><svg class="path-svg" aria-hidden="true"></svg><div class="stage-divider"><svg class="stage-wave" viewBox="0 0 640 100" preserveAspectRatio="none" aria-hidden="true"><path d="M0 22 C95 -14 170 42 280 18 S470 -5 640 22 L640 80 C525 115 445 65 330 85 S110 110 0 80Z" fill="#c8eaf3"/><path d="M0 36 C100 5 185 55 290 32 S480 15 640 34 L640 80 C525 115 445 65 330 85 S110 110 0 80Z" fill="#e0f3f8"/></svg><span>'+String(s.index+1).padStart(2,'0')+'</span><h3>'+esc(s.title)+'</h3><small>'+(t.count?t.done+' / '+t.count+' 關':s.levels.filter(l=>hasContent(l)).length+' / '+s.levels.length+' 筆通知')+'</small></div>'+s.levels.map(l=>{
      const level=all.find(x=>x.id===l.id),i=s.levels.indexOf(l),st=status(l),p=progress(l),isCurrent=n?.id===l.id,locked=missing(l).length>0;
      // Reverse lateral direction at every step, continuing across chapter boundaries.
      const x=[.24,.72,.38,.77,.28,.66][(level.number-1)%6]*100;
      const label=l.title+'，'+(locked?'可查看，完成前需先備齊內容':isCurrent?'建議下一步':st==='done'?'已完成':l.external?'外部通知':p.value?'進行中':'可提前辦理');
      return '<div class="level-stop" data-stop="'+l.id+'" style="left:'+x+'%;bottom:'+(122+i*152)+'px"><a class="node '+st+' '+(isCurrent?'current ':'')+(locked?'locked':'')+'" href="#level/'+l.id+'" aria-label="'+esc(label)+'" '+(isCurrent?'aria-current="step"':'')+'>'+(isCurrent?'<span class="current-flag">繼續</span>':'')+icon(st==='done'?'check':locked?'lock-keyhole':l.icon)+'<span class="node-order" aria-hidden="true">'+level.number+'</span></a><span class="node-title">'+esc(l.title)+'</span><div class="node-progress">'+meter(p,l.title+(l.external?'紀錄進度':'進度'),{small:true,gold:st==='done',animate:isCurrent&&p.value>0})+'</div><span class="node-caption">'+(l.external?(p.value?'自行記錄':'等待通知'):st==='skipped'?'不適用':l.conditional&&l.counted===false?'待確認適用性':p.value+' / '+p.total+' 步')+'</span></div>';
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
      return '<a class="stage-level '+(s==='done'?'is-done':'')+'" href="#level/'+l.id+'"><span>'+(s==='done'?icon('check'):String(num).padStart(2,'0'))+'</span><span><b>'+esc(l.title)+'</b><small>'+(l.external?(hasContent(l)?'學生自行記錄':'未記錄正式通知'):s==='skipped'?'個人記錄：不適用':l.conditional&&l.counted===false?'適用性待確認，暫不計入':s==='done'?'個人已完成':s==='started'?'已留下內容，待確認':'隨時可以開始')+'</small></span><span class="row-progress">'+(p.value+' / '+p.total+meter(p,l.title+'總覽進度',{small:true,gold:s==='done'}))+'</span></a>';
    }).join('')+'</section>';
  }).join('');
  if(!shown)$('#overview-stages').innerHTML='<div class="overview-empty">'+icon('circle-check')+'<p>這個分類目前沒有關卡。</p></div>';
  icons();
}

return {init,show,refresh,clear};
})();

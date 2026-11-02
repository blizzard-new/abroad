/* Account-backed application map. Private edits stay in memory until server CAS succeeds. */
window.UniWayApplicationPath = (() => {
'use strict';
let root, picker, view=null, listing=null, owner='', epoch=0, loading=false, saving=false, active=false;
let activeId=null, dirty=false, filter='all', mapPosition=null, mapPositionPlan=null, toastTimer;
// Unsynced content stays in this tab only, scoped to account + home + plan + task.
const drafts=new Map();
let draftOwner='', autosaveTimer, recoveryTimer, editVersion=0, creating=false;
let oauthTimer, oauthPopup, oauthRun=0;
const track=(event,props={})=>window.UniWayAnalytics?.track(event,props);
const draftKey=(id=activeId)=>JSON.stringify([view?.plan.context.home_school,view?.plan.id,id]);
const stepContent=s=>JSON.stringify([s.value||'',s.version_id||null,s.applicable??null]);
function stash(){
  if(!view||!activeId||!$('#level-form')||!state.account||!dirty||owner.split('|')[0]!==state.account.id)return;
  if(draftOwner&&draftOwner!==state.account.id)drafts.clear();
  draftOwner=state.account.id;
  drafts.set(draftKey(),{...drafts.get(draftKey()),step:readStep(),version:editVersion,editedAt:Date.now()});
}
function edit(event){
  // Upload consent and the final self-submission checkbox are explicit actions,
  // not draft edits. Saving a draft must never silently uncheck confirmation.
  if(event?.target.matches('#self-confirm,#file-consent,#path-file'))return;
  dirty=true;editVersion++;stash();$('#save-note').textContent='尚未儲存';clearTimeout(autosaveTimer);
  autosaveTimer=setTimeout(()=>{if(dirty&&active&&state.account)save(false,{quiet:true});},900);
}
function stopOAuthRecovery(){
  oauthRun++;clearTimeout(oauthTimer);
  try{oauthPopup?.close();}catch{}oauthPopup=null;
  document.querySelector('#path-reauth-status')?.remove();
}
function resetDrafts(){drafts.clear();draftOwner='';clearTimeout(recoveryTimer);clearTimeout(autosaveTimer);stopOAuthRecovery();}
function recoveryStatus(text){
  let el=document.querySelector('#path-reauth-status');
  if(!el){el=document.createElement('p');el.id='path-reauth-status';el.setAttribute('role','status');document.querySelector('#oauth-provider-list').after(el);}
  el.textContent=text;
}
function resumeOAuth(url){
  if(state.account||!drafts.size)return false;
  stopOAuthRecovery();
  // Keep this tab alive through the real Google redirect. No draft or account
  // data crosses to the popup; /auth/me verifies the new HttpOnly session.
  oauthPopup=window.open('about:blank','_blank','popup,width=480,height=720');
  if(!oauthPopup){recoveryStatus('請允許開啟登入視窗，再試一次。草稿仍留在此分頁。');return true;}
  oauthPopup.opener=null;oauthPopup.location.href=url;
  recoveryStatus('請在新視窗登入原帳號，完成後會自動續接。請保留此分頁。');
  const run=oauthRun;
  async function check(){
    if(run!==oauthRun||!drafts.size||state.account)return;
    try{
      const response=await fetch('/auth/me',{credentials:'same-origin',cache:'no-store'});
      if(response.ok){
        const profile=await response.json();
        if(run!==oauthRun||!drafts.size||state.account)return;
        stopOAuthRecovery();
        await acceptAccountSession({profile});closeAuthDialog();return;
      }
    }catch{/* Keep the draft and allow another login attempt after a network error. */}
    if(run===oauthRun)oauthTimer=setTimeout(check,3000);
  }
  oauthTimer=setTimeout(check,1500);return true;
}
function completeLabel(l){return l.external?'儲存通知紀錄':l.kind==='submission'?'記錄我已送件':l.kind==='file'?'標記文件備妥':l.kind==='confirm'?'確認內容':'標記準備完成';}
function successLabel(l){
  if(l.external)return '通知紀錄已保存';
  const stage=totals(levels().filter(x=>x.stageTitle===l.stageTitle));
  return required(l)&&stage.count>0&&stage.done===stage.count?'完成「'+l.stageTitle+'」！':'已完成這項準備';
}

const $=(s,r=root)=>r?.querySelector(s), $$=(s,r=root)=>[...(r?.querySelectorAll(s)||[])];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=n=>'<i data-lucide="'+esc(n)+'" aria-hidden="true"></i>';
const termName=t=>({fall:'上學期',spring:'下學期',full_year:'全學年',undecided:'尚未決定'}[t]||t);
const route=()=>new URLSearchParams(location.hash.split('?')[1]||'');
const href=(tab='progress',id='')=>'#my-application?'+new URLSearchParams({plan:view?.plan.id||'',view:tab,...(id?{level:id}:{})});
const plan=()=>view.plan, stages=()=>view?.stages||[];
const levels=()=>stages().flatMap(s=>s.levels.map(l=>({...l,stageTitle:s.title})));
const find=id=>levels().find(l=>l.id===id), record=id=>plan().steps[id]||{};
const progress=l=>l.progress, hasContent=l=>Boolean(record(l.id).value||record(l.id).version_id);
const isDone=l=>l.counted!==false&&!l.external&&l.progress.value===l.progress.total;
const status=l=>l.conditional&&record(l.id).applicable===false?'skipped':l.external?(hasContent(l)?'recorded':'external'):isDone(l)?'done':l.progress.value?'started':'todo';
const missing=l=>l.blocked_by||[];
const setup=l=>['home','term','target'].includes(l.id);
const assistance=l=>['write','assemble'].includes(l.kind);
const required=l=>!setup(l)&&!assistance(l)&&!l.external&&l.counted!==false;
const confirmedDeadline=l=>Boolean(l.official_deadline_at&&l.deadline_confirmed);
function next(){
  const available=levels().filter(l=>!l.external&&!setup(l)&&!assistance(l)&&status(l)!=='skipped'&&!isDone(l)&&!missing(l).length);
  const pending=levels().filter(l=>drafts.has(draftKey(l.id))&&!missing(l).length)
    .sort((a,b)=>(drafts.get(draftKey(b.id)).editedAt||0)-(drafts.get(draftKey(a.id)).editedAt||0));
  if(pending.length)return pending[0];
  const now=Date.now(), urgent=available.filter(l=>confirmedDeadline(l)&&Date.parse(l.official_deadline_at)>=now&&Date.parse(l.official_deadline_at)-now<=14*86400000).sort((a,b)=>Date.parse(a.official_deadline_at)-Date.parse(b.official_deadline_at));
  if(urgent.length)return urgent[0];
  const unfinished=levels().filter(l=>!l.external&&!setup(l)&&!isDone(l)&&!missing(l).length&&(drafts.has(draftKey(l.id))||status(l)==='started'));
  unfinished.sort((a,b)=>(record(b.id).updated_at||'').localeCompare(record(a.id).updated_at||''));
  return unfinished.find(l=>drafts.has(draftKey(l.id)))||unfinished[0]||available[0];
}
function nextReason(l){return !l?'校方結果請以正式通知為準。':drafts.has(draftKey(l.id))?'接著處理尚未儲存的內容。':confirmedDeadline(l)&&Date.parse(l.official_deadline_at)>=Date.now()&&Date.parse(l.official_deadline_at)-Date.now()<=14*86400000?'官方期限將近，先處理這項。':status(l)==='started'?'接著完成上次的草稿。':'下一項可開始的準備。';}

const pct=p=>p.total?Math.round(p.value/p.total*100):0;
function totals(list=levels()){
  const counted=list.filter(required),done=counted.filter(isDone).length;
  return {value:done,total:counted.length,done,count:counted.length,started:counted.filter(l=>status(l)==='started').length,pending:list.filter(l=>!l.external&&l.conditional&&record(l.id).applicable==null).length};
}
const key=()=>[state.account?.id||'',state.authSessionEpoch,activeHomeSchool()].join('|');
const query=()=>'?'+new URLSearchParams({home_school:activeHomeSchool()});
const pathUrl=()=>'/account/application-paths/'+encodeURIComponent(plan().id);
const urls=l=>(l.source_urls||[]).filter(u=>/^https?:\/\//i.test(u));
const targets=new Set();
const observer=new IntersectionObserver(entries=>entries.forEach(e=>e.target.classList.toggle('motion-visible',e.isIntersecting)),{threshold:.05});
function icons(){
  $$('a[href^="#level/"]').forEach(a=>a.href=href('level',a.getAttribute('href').slice(7)));
  $$('a[href="#map"]').forEach(a=>a.href=href('map'));
  $$('a[href="#progress"]').forEach(a=>a.href=href('progress'));
  window.lucide?.createIcons();
  for(const el of targets)if(!el.isConnected){observer.unobserve(el);targets.delete(el);}
  $$('.meter.animate,.node.done').forEach(el=>{if(!targets.has(el)){targets.add(el);observer.observe(el);}});
}
function meter(p,label,{small=false,big=false,animate=true,gold=false}={}){
  return '<div class="meter '+(small?'small ':'')+(big?'big ':'')+(animate?'animate ':'')+(gold?'gold':'')+'" data-empty="'+!p.value+'" role="progressbar" aria-label="'+esc(label)+'" aria-valuemin="0" aria-valuemax="'+p.total+'" aria-valuenow="'+p.value+'"><span class="meter-fill" style="--progress:'+pct(p)+'%">'+[0,.4,.8].map((d,i)=>'<i class="particle '+(i===1?'star':'')+'" style="--delay:'+d+'s" aria-hidden="true"></i>').join('')+'</span></div>';
}
function toast(text,error=false,action=null){
  clearTimeout(toastTimer);const el=$('#toast');el.replaceChildren(document.createTextNode(text));
  if(action){const b=document.createElement('button');b.type='button';b.className='toast-action';b.textContent=action.label;b.onclick=()=>{el.hidden=true;action.run();};el.append(b);}
  el.hidden=false;el.classList.toggle('error',error);toastTimer=setTimeout(()=>el.hidden=true,action?9000:5000);
}
function message(text,action=''){
  $('#hub').hidden=true;$('#level-view').hidden=true;$('#schedule-view').hidden=true;$('#path-message').hidden=false;$('#archive-plan').hidden=true;
  $('#path-message').innerHTML='<div class="ap-empty">'+icon('route')+'<p>'+esc(text)+'</p>'+action+'</div>';icons();
}
function clear({preserveDrafts=false}={}){
  stash();clearTimeout(autosaveTimer);
  if(state.account)stopOAuthRecovery();
  if(!preserveDrafts||(state.account&&draftOwner&&draftOwner!==state.account.id))resetDrafts();
  if(state.account&&state.account.id===draftOwner)clearTimeout(recoveryTimer);
  if(preserveDrafts&&!state.account&&drafts.size){clearTimeout(recoveryTimer);recoveryTimer=setTimeout(resetDrafts,15*60*1000);}
  window.UniWayApplicationWorkspace?.release();epoch++;loading=false;saving=false;view=null;listing=null;dirty=false;activeId=null;mapPosition=null;mapPositionPlan=null;
  if(root){$$('dialog[open]').forEach(d=>d.close());$('#level-view').replaceChildren();$('#plan-select').replaceChildren();$('#path-stages').replaceChildren();$('#overview-summary').replaceChildren();$('#overview-stages').replaceChildren();$('#plan-form').reset();['#plan-meta','#overall-caption','#overall-meter','#next-stage','#next-title','#next-prompt','#next-meter','#deadline-card','#create-target'].forEach(selector=>$(selector)?.replaceChildren());$('#toast').hidden=true;message('登入後保存你的準備進度','<button data-path-login class="primary-button">登入並繼續</button><a href="#partners" class="quiet-button">先找交換學校</a>');}}
function init(){
  if(root)return;
  root=document.querySelector('#application-path');root.innerHTML=window.UniWayApplicationPathTemplate;
  picker=new window.UniWayGlideSelect($('#stage-select'));
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  function motion(paused){root.dataset.motion=paused?'paused':'running';}
  motion(reduced.matches);reduced.addEventListener('change',e=>motion(e.matches));
  $('#refresh-path').onclick=()=>{stash();load(true);};
  $('#new-plan').onclick=openNew;
  $('#archive-plan').onclick=archive;
  $('#source-info').onclick=()=>$('#info-dialog').showModal();
  $$('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());
  $('#plan-form').onsubmit=create;
  $('#plan-select').onchange=e=>{location.hash='#my-application?'+new URLSearchParams({plan:e.target.value,view:'today'});};
  $('#stage-select').onchange=e=>scrollMap(stages()[Number(e.target.value)]?.levels[0]?.id);
  $('#go-origin').onclick=()=>{scrollMap(null);$('#stage-select').value='0';picker.sync();};
  $('#go-current').onclick=()=>{const n=next();if(n)location.hash=href('level',n.id);};
  $$('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;$$('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',x===b));renderOverview();});
  root.addEventListener('click',e=>{
    if(e.target.closest('[data-path-login]'))openAuthDialog();
    if(e.target.closest('[data-path-new]'))openNew();
    if(e.target.closest('[data-path-retry]'))load(true);
    if(e.target.closest('[data-open-info]'))$('#info-dialog').showModal();
    if(e.target.closest('[data-use-plan-context]')){applyPlanContext().then(ok=>{if(ok&&active&&route().get('view')==='schedule')renderSchedule();}).catch(err=>toast(err.message,true));}
    const restoreBtn=e.target.closest('[data-restore-plan]');if(restoreBtn)restorePlan(restoreBtn.dataset.restorePlan);
    if(e.target.closest('.ap-menu-list button'))e.target.closest('.ap-menu').open=false;
    const link=e.target.closest('#path-tool-host a[href^="#"]');
    if(link){const url=toolHref(link.getAttribute('href').slice(1));if(url){e.preventDefault();location.hash=url;}}
  });
  // History/hash navigation is also safe: show() snapshots before replacing any form.
  addEventListener('beforeunload',e=>{stash();if(drafts.size||saving){e.preventDefault();e.returnValue='';}});
  addEventListener('online',()=>{if(dirty&&active&&state.account)save(false,{quiet:true});});
  document.addEventListener('click',e=>{const m=root&&$('.ap-menu');if(m?.open&&!m.contains(e.target))m.open=false;});
  root.addEventListener('submit',e=>{
    const f=e.target.closest('[data-today-quick]');if(!f)return;e.preventDefault();
    if(addCalendarEvent(f)){f.reset();f.elements.date.value=localDateKey();if(active&&route().get('view')==='today')renderToday();window.UniWayTracker?.render();toast('已加入待辦。');}
  });
  new ResizeObserver(()=>requestAnimationFrame(drawPaths)).observe($('#map-scroll'));
}
function refresh(){if(!root)return;if(owner!==key()){clear({preserveDrafts:true});owner=key();if(active)load();}}
function show(page){init();stash();clearTimeout(autosaveTimer);active=page==='my-application';picker.close();if(owner!==key()){clear({preserveDrafts:true});owner=key();}
  if(!active)return;
  if(!state.account){message(state.authRestoreState==='pending'?'正在確認登入狀態…':'登入後，接著完成你的申請。','<button data-path-login class="primary-button">登入並繼續</button><a href="#partners" class="quiet-button">先找交換學校</a>');if(route().get('view')==='schedule')showScheduleWithoutPlan(true);return;}
  const requested=route().get('plan');
  if(!view&&route().get('view')==='schedule'&&listing&&!listing.items.length){showScheduleWithoutPlan();return;}
  if(!view||requested&&view.plan.id!==requested){if(!loading)load();return;}
  render();maybeOpenTarget();
}
async function load(force=false){
  if(!state.account)return show('my-application');
  const run=++epoch, captured=key();loading=true;
  message('正在載入你的申請進度…');$('#path-message').classList.add('ap-loading');
  try{
    const list=await fetchJson('/account/application-paths'+query());
    if(run!==epoch||captured!==key())return;
    listing=list;window.UniWayPlanIndex?.accept(list);
    const requested=route().get('plan');
    const selected=list.items.find(p=>p.id===requested)||list.items.filter(p=>!p.archived).sort((a,b)=>(b.updated_at||'').localeCompare(a.updated_at||''))[0]||list.items[0];
    if(!selected&&route().get('view')==='schedule'){view=null;$('#sync-message').textContent='已連接帳號';showScheduleWithoutPlan();return;}
    if(!selected){view=null;$('#sync-message').textContent='已連接帳號';message('從你的交換目標開始','<a href="#partners" class="primary-button next-action">找適合的學校</a><button data-path-new class="outline-button">我已有目標</button>'+((listing.legacy?.schools||[]).length?'<a href="#my-application?view=schedule" class="quiet-button">查看時程</a>':''));maybeOpenTarget();return;}
    const data=await fetchJson('/account/application-paths/'+selected.id+query());
    if(run!==epoch||captured!==key())return;
    if(route().get('plan')!==requested){load();return;}
    view=data;dirty=false;activeId=null;
    if(mapPositionPlan!==selected.id)mapPosition=null;
    render();maybeOpenTarget();window.UniWayTracker?.render();
  }catch(e){if(run===epoch&&captured===key()){message(e.message,'<button data-path-retry class="outline-button">重新載入</button>');}}
  finally{if(run===epoch){loading=false;$('#path-message').classList.remove('ap-loading');}}
}
function render(){
  if(!active||!view)return;
  window.UniWayApplicationWorkspace?.release();
  $('#path-message').hidden=true;
  const id=route().get('level'), tab=route().get('view')||'today';
  
  $('#hub').hidden=tab==='level';$('#level-view').hidden=tab!=='level';
  $('#sync-message').textContent=plan().archived?'已封存 · 紀錄保留':'已同步至帳號';
  $('#archive-plan').hidden=false;$('#archive-plan').textContent=plan().archived?'恢復計畫':'封存計畫';
  const c=plan().context;
  $('#plan-select').innerHTML=listing.items.map(p=>'<option value="'+p.id+'" '+(p.id===plan().id?'selected':'')+'>'+esc(p.context.target_school.split(/[（(]/)[0].trim()+' · '+p.context.departure_year+' '+termName(p.context.semester)+(p.archived?'（已封存）':''))+'</option>').join('');
  $('#plan-meta').textContent=c.home_school+' · '+c.academic_year+' 學年度 · '+(c.application_round||'梯次待確認');
  const t=totals();$('#overall-caption').textContent=t.done+' / '+t.count+' 項';$('#overall-meter').innerHTML=meter(t,'整體個人準備');
  const activeTab=tab==='progress'||tab==='map'?'plans':tab;
  $$('[data-tab]').forEach(a=>{a.href=href(a.dataset.tab);a.classList.toggle('active',a.dataset.tab===activeTab);if(a.dataset.tab===activeTab)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  const back=$('#subview-back');back.hidden=!(tab==='progress'||tab==='map');back.href=href('plans');back.innerHTML=icon('arrow-left')+'回到計畫';
  const n=next();$('#stage-select').innerHTML=stages().map(s=>'<option value="'+s.index+'" '+(n?.stage===s.index?'selected':'')+'>'+String(s.index+1).padStart(2,'0')+' · '+esc(s.title)+'</option>').join('');picker.sync();
  $('#next-stage').textContent='接下來';
  $('#next-title').textContent=n?.title||(t.count?'已完成已知準備事項':'確認當期申請要求');$('#next-prompt').textContent=nextReason(n);
  $('#next-link').href=n?href('level',n.id):href('progress');$('#next-link').innerHTML=(n?(status(n)==='started'?'繼續填寫':'開始準備'):'查看清單')+icon('arrow-right');
  $('#next-meter').replaceChildren();
  const due=levels().filter(l=>confirmedDeadline(l)&&!l.external&&status(l)!=='skipped'&&!isDone(l)).sort((a,b)=>a.official_deadline_at.localeCompare(b.official_deadline_at))[0];
  $('#deadline-card').innerHTML=icon('calendar-search')+'<div><h3>'+(due?'官方期限':'官方日期待確認')+'</h3><p>'+esc(due?new Date(due.official_deadline_at).toLocaleString('zh-TW',{timeZone:'Asia/Taipei',month:'long',day:'numeric',hour:'2-digit',minute:'2-digit'})+'（臺灣時間）'+(new Date(due.official_deadline_at)<new Date()?' · 已過期':''):'請核對當期官方公告。')+'</p>'+(due?'<a href="'+href('level',due.id)+'">'+esc(due.title)+icon('arrow-right')+'</a>':'')+'</div>';
  $('#hub').dataset.tab=tab;$('#today-view').hidden=tab!=='today';$('#plans-view').hidden=tab!=='plans';$('#schedule-view').hidden=tab!=='schedule';$('#map-tools').hidden=tab!=='map';$('#map-view').hidden=tab!=='map';$('#progress-view').hidden=tab!=='progress';
  if(tab==='level'){if(!dirty||activeId!==id)renderLevel(id);}
  else if(tab==='today'){activeId=null;renderToday();}
  else if(tab==='plans'){activeId=null;renderPlans();}
  else if(tab==='schedule'){activeId=null;renderSchedule();}
  else if(tab==='progress'){activeId=null;renderOverview();}
  else{activeId=null;renderMap();requestAnimationFrame(()=>{if(mapPosition!==null&&mapPositionPlan===plan().id)$('#map-scroll').scrollTop=mapPosition;else scrollMap(n?.id,'instant');});}
  icons();
}
function error(text){const el=$('#level-error');if(el){el.hidden=false;el.textContent=text;el.tabIndex=-1;el.focus();}else toast(text,true);}
function readStep(){return {value:$('#level-input')?.value||'',confirmed:$('#self-confirm')?$('#self-confirm').checked:!!record(activeId).confirmed,version_id:$('#file-version')?.value||null,applicable:$('#file-applicable')?($('#file-applicable').value===''?null:$('#file-applicable').value==='yes'):null};}
async function save(complete=false,{quiet=false}={}){
  clearTimeout(autosaveTimer);
  if(saving||!view||plan().archived)return false;
  const l=find(activeId);if(!l||!$('#level-form'))return false;
  if(quiet&&drafts.get(draftKey())?.conflict)return false;
  const data=readStep(), run=epoch,captured=key(),id=plan().id,cacheKey=draftKey(),version=editVersion;
  if(complete&&l.kind==='submission'&&!data.confirmed){error('請先確認你已在校方系統送件。');return false;}
  if(complete&&!l.external)data.confirmed=true;
  else data.confirmed=!!record(l.id).confirmed&&stepContent(data)===stepContent(record(l.id));
  const wasDone=isDone(l),before={...record(l.id)};
  stash();saving=true;$$('#save-draft,#level-form button[type=submit],#conflict-reload').forEach(b=>b.disabled=true);$('#save-note').textContent='正在儲存…';
  try{
    const saved=await fetchJson(pathUrl()+'/steps/'+encodeURIComponent(l.id)+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,step:data})});
    if(run!==epoch||captured!==key()||view?.plan.id!==id)return false;
    const pending=drafts.get(cacheKey),unchanged=!pending||pending.version===version;
    if(unchanged)drafts.delete(cacheKey);
    view=saved;listing.revision=saved.revision;
    if(active&&activeId===l.id&&route().get('view')==='level'){
      dirty=!unchanged;
      if(complete&&unchanged)renderLevel(l.id,true);
      else {
        $('#save-note').textContent=unchanged?(wasDone&&!isDone(find(l.id))?'已儲存 · 修改後請重新確認':'已儲存'):'還有新修改，正在儲存…';
        $('.level-progress strong').textContent=isDone(find(l.id))?'已完成':hasContent(find(l.id))?'進行中':'尚未開始';
        if(unchanged){$('#level-error').hidden=true;$('#conflict-reload').hidden=true;$('.conflict-comparison')?.remove();}
      }
      if(!unchanged)autosaveTimer=setTimeout(()=>save(false,{quiet:true}),900);
    }
    track('draft_save_result',{result:'success',kind:l.kind});
    if(!quiet){if(complete&&!l.external&&!wasDone){const t=totals();toast('已完成「'+l.title+'」。準備進度 '+t.done+' / '+t.count,false,{label:'撤銷',run:()=>undoStep(l.id,before)});}else toast(complete?'已記錄準備成果':'草稿已儲存');}return true;
  }catch(e){
    track('draft_save_result',{result:'failed',status:e.status||0,kind:l.kind});
    if(run===epoch&&captured===key()){
      if(e.status===409){
        const pending=drafts.get(cacheKey)||{step:data,version};
        drafts.set(cacheKey,{...pending,conflict:true});draftOwner=state.account.id;
      }
      if(activeId!==l.id||!$('#level-form'))return false;
      const msg=e.status===409?'其他分頁已更新。保留你的內容，載入最新進度後再儲存。':e.message+'；內容仍保留在此分頁。';
      if(!quiet)error(msg);else {$('#level-error').hidden=false;$('#level-error').textContent=msg;}
      $('#save-note').textContent='尚未儲存，請重試';if(e.status===409)$('#conflict-reload').hidden=false;
    }return false;
  }finally{if(run===epoch){saving=false;$$('#save-draft,#level-form button[type=submit],#conflict-reload').forEach(b=>b.disabled=plan().archived);}}
}
const CHECK_TEXT={pass:['符合','pass','規則比對通過，仍以校方審核為準。'],
  fail:['不符合','fail','目前條件不符合這項規則。你仍可以記下「已看過」，但這不會改變資格判斷。'],
  needs_confirmation:['待確認','needs','系統還無法判斷。先補齊你的條件，或向承辦單位確認。']};
const CHECK_STANDARD=new Set(['規則比對通過，仍以校方審核為準。','目前條件不符合此項規則；個人確認不會改變資格判斷。','資料或個人條件待確認。']);
function checkStatus(l){const c=CHECK_TEXT[l.check_status];return c?'<p class="check-status '+c[1]+'" role="status"><b>'+c[0]+'</b>'+esc(c[2])+'</p>':'';}
function field(l,r){
  if(l.kind==='confirm')return checkStatus(l)+'<div class="choice-box">'+icon(l.icon)+'<strong>'+esc(l.prompt)+'</strong></div>';
  if(l.kind==='assemble')return '<div class="document-preview">'+levels().filter(x=>x.kind==='write').map(x=>'<section><h3>'+esc(x.title)+'</h3><p>'+esc(record(x.id).value||'尚未填寫')+'</p><a href="'+href('level',x.id)+'">編輯這一段</a></section>').join('')+'</div><button type="button" id="download-writing" class="outline-button">'+icon('download')+'下載文字草稿</button><a class="outline-button" href="'+pathUrl()+'/writing.docx'+query()+'">'+icon('file-down')+'下載 Word 草稿</a>';
  return (l.conditional?'<label for="file-applicable">這份條件式文件適用於你嗎？</label><select id="file-applicable"><option value="">待確認（暫不計入進度）</option><option value="yes" '+(r.applicable===true?'selected':'')+'>適用</option><option value="no" '+(r.applicable===false?'selected':'')+'>不適用</option></select>':'')+(l.external?'<div class="external-notice">學生自行記錄，不代表校方確認。</div>':'')+
    (l.kind==='submission'?'<p class="small-warning">請在官方系統送件；UniWay 不代送申請。</p>':'')+
    (l.kind==='file'?'<label for="file-version">連結私人文件</label><select id="file-version"><option value="">自行保管（在下方記錄位置）</option>'+(r.version_id?'<option selected value="'+esc(r.version_id)+'">'+esc(r.file_name||'已連結文件')+'</option>':'')+'</select><button type="button" id="load-files" class="quiet-button">'+icon('folder-open')+'選擇我的文件</button><details class="ap-upload"><summary>上傳到私人文件庫</summary><label for="path-file">選擇檔案</label><input type="file" id="path-file"><label class="check-row"><input type="checkbox" id="file-consent"><span>同意加密保存 30 天，用於申請準備；可在私人文件庫撤回。</span></label><button type="button" id="upload-file" class="outline-button">上傳並連結</button></details>':'')+
    '<label for="level-input">'+(l.kind==='write'?'你的想法':l.kind==='file'?'文件位置／備註':'目前紀錄與下一步')+'</label><textarea id="level-input" maxlength="20000" placeholder="先記下一小段，之後還能修改。">'+esc(r.value||'')+'</textarea>';
}
function renderLevel(id,success=false){
  window.UniWayApplicationWorkspace?.release();
  const l=find(id);if(!l){location.hash=href();return;}
  activeId=id;const cached=draftOwner===state.account?.id?drafts.get(draftKey(id)):null;dirty=!!cached;const r=cached?.step||record(id),c=plan().context;
  mapPosition=$('#map-scroll').scrollTop;mapPositionPlan=plan().id;
  const dependencies=missing(l);
  $('#level-view').innerHTML='<div class="level-topline"><a class="back-link" href="'+href()+'">'+icon('arrow-left')+'回到準備清單</a><span>'+esc(c.target_school+' · '+c.departure_year+' '+termName(c.semester))+'</span></div><div class="level-layout"><div class="level-card"><div class="level-heading"><span class="square-icon">'+icon(l.icon)+'</span><div><p class="eyebrow">'+esc(l.stageTitle)+'</p><h2 id="level-title" tabindex="-1">'+esc(l.title)+'</h2></div></div><div class="level-progress"><div><span>準備狀態</span><strong>'+(isDone(l)?'已完成':hasContent(l)?'進行中':'尚未開始')+'</strong></div>'+meter(l.progress,l.title+'進度',{big:true,gold:isDone(l)})+'</div>'+
    (success?'<div class="success-state" tabindex="-1" role="status"><div class="success-emblem">'+icon('check')+'</div><h3>'+esc(successLabel(l))+'</h3><p>已同步至這份申請計畫 · 準備進度 '+totals().done+' / '+totals().count+'</p><a class="primary-button" href="'+(next()?href('level',next().id):href('progress'))+'">'+(next()?'下一項準備':'查看總覽')+icon('arrow-right')+'</a><button id="edit-level" class="quiet-button">回頭查看／修改</button></div>':
    '<form id="level-form"><div class="level-body">'+(l.kind==='confirm'?'':'<p class="task-question">'+esc(l.prompt)+'</p>')+(l.warning&&!(l.check_status&&CHECK_STANDARD.has(l.warning))?'<details class="ap-warning"><summary>需要確認的事項</summary><p>'+esc(l.warning)+'</p></details>':'')+field(l,r)+(dependencies.length?'<div class="small-warning">先完成以下前置事項：'+dependencies.map(k=>'<a href="'+href('level',k)+'">'+esc(find(k)?.title||'前置資料尚未取得')+'</a>').join('')+'</div>':'')+(l.kind==='submission'?'<label class="check-row confirmation"><input type="checkbox" id="self-confirm" '+(r.confirmed?'checked':'')+'><span>'+(l.kind==='submission'?'我已自行送件，這是個人紀錄':'我已確認這一小步準備好了')+'</span></label>':'')+'<p id="level-error" class="error-box" role="alert" hidden></p><button type="button" id="conflict-reload" class="outline-button" hidden>保留輸入並載入最新進度</button></div><footer class="level-actions"><span id="save-note" role="status">'+(dirty?'已恢復未儲存內容':isDone(l)?'已完成 · 已儲存':'輸入後自動儲存')+'</span><button type="button" id="save-draft" class="outline-button">儲存草稿</button><button type="submit" class="primary-button" '+(plan().archived?'disabled':'')+'>'+esc(completeLabel(l))+icon('check')+'</button></footer></form>')+'</div><aside class="level-support"><section class="support-card"><details class="source-details"><summary>完整規則與官方來源'+icon('chevron-down')+'</summary><p>'+esc(l.prompt)+'</p>'+urls(l).map((u,i)=>'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">'+(i?'相關官方文件':'官方來源')+icon('arrow-up-right')+'</a>').join('')+'</details>'+(l.official_deadline_at?'<p class="ap-deadline">'+(confirmedDeadline(l)?'官方期限：':'參考日期（待核對）：')+esc(new Date(l.official_deadline_at).toLocaleString('zh-TW',{timeZone:'Asia/Taipei'}))+'（臺灣時間）'+(new Date(l.official_deadline_at)<new Date()?'（已過期）':'')+'</p>':'')+(l.action_url&&/^https?:\/\//i.test(l.action_url)?'<a class="outline-button" href="'+esc(l.action_url)+'" target="_blank" rel="noopener noreferrer">開啟官方表格'+icon('external-link')+'</a>':'')+(l.kind==='submission'&&urls(l).length?'<a class="outline-button" href="'+esc(urls(l)[0])+'" target="_blank" rel="noopener noreferrer">校方公告與入口'+icon('external-link')+'</a>':'')+'</section><div class="context-card"><strong>'+esc(c.home_school)+'</strong>'+esc(c.academic_year)+' 學年度 · '+esc(c.application_round||'梯次待確認')+'<br>個人準備 ≠ 校方受理或錄取</div></aside></div>';
  if(success)$('#edit-level').onclick=()=>renderLevel(id);
  else{
    $('#level-form').oninput=edit;
    $('#level-form').onsubmit=e=>{e.preventDefault();save(true);};
    $('#save-draft').onclick=()=>save(false);
    $('#conflict-reload').onclick=async()=>{
      clearTimeout(autosaveTimer);
      const run=epoch,captured=key(),planId=plan().id;
      try{
        const latest=await fetchJson(pathUrl()+query());
        if(run!==epoch||captured!==key()||view?.plan.id!==planId||activeId!==id||!active)return;
        dirty=true;stash();view=latest;listing.revision=latest.revision;renderLevel(id);
        const remote=latest.plan.steps[id]||{},comparison=document.createElement('details');
        comparison.className='conflict-comparison';comparison.open=true;
        comparison.innerHTML='<summary>其他分頁已儲存的內容</summary><p>'+esc(remote.value||'沒有文字紀錄')+'</p>'+(remote.version_id?'<p>已連結私人文件</p>':'');
        $('#level-error').after(comparison);
        error('你的輸入已保留。請比對版本，再按「儲存草稿」。');
      }
      catch(e){if(run===epoch)error(e.message);}
    };
    if(cached?.conflict){$('#conflict-reload').hidden=false;$('#level-error').hidden=false;$('#level-error').textContent='其他分頁已更新。先載入最新進度，再確認要保存的內容。';}
    if(plan().archived){$$('#level-form input,#level-form textarea,#level-form select,#level-form button').forEach(el=>el.disabled=true);$('#save-note').textContent='已封存，恢復計畫後可繼續';}
    if($('#load-files'))$('#load-files').onclick=loadFiles;
    if($('#upload-file'))$('#upload-file').onclick=uploadFile;
    if($('#download-writing'))$('#download-writing').onclick=()=>{
      const text=levels().filter(x=>x.kind==='write').map(x=>x.title+'\n'+(record(x.id).value||'')).join('\n\n');
      const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='UniWay-研修計畫草稿.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    };
  }
  if(!success)renderTools(l);
  icons();
  if(success)requestAnimationFrame(()=>$('.success-state')?.focus());
  else if(!route().get('tool'))requestAnimationFrame(()=>$('#level-title')?.focus({preventScroll:true}));
  if(cached)track('draft_resume_result',{result:'restored',kind:l.kind});
}
const embeddedTools=new Set(['advisor','favorites','eligibility','application-center','document-check','documents','writing-assistant']);
function toolHref(tool){
  if(!active||!view||route().get('view')!=='level'||!find(route().get('level')))return null;
  if(!embeddedTools.has(tool)&&!/^application-form=[\w%-]+$/.test(tool))return null;
  try{decodeURIComponent(tool);}catch{return null;}
  return href('level',route().get('level'))+'&'+new URLSearchParams({tool});
}
function formToolActive(){return active&&route().get('view')==='level'&&(route().get('tool')||'').startsWith('application-form=');}
async function selectTarget(schoolName){
  if(!toolHref('advisor')||schoolName===plan().context.target_school)return false;
  await openNew(schoolName);
  return true;
}
function toolsFor(l){
  if(['home','term','target'].includes(l.id))return [['advisor','sliders-horizontal','條件與推薦'],['favorites','heart','收藏與比較'],['eligibility','badge-check','資格與志願']];
  if(l.id.startsWith('check-')||(l.kind==='note'&&/資格|志願|語組/.test(l.title)))return [['eligibility','badge-check','核對資格與志願'],['advisor','sliders-horizontal','修改我的條件']];
  const templates=(l.templates||[]).map(id=>['application-form='+encodeURIComponent(id),'file-pen-line',applicationTemplateById(id)?.name||'填寫相關表格']);
  return [...templates,['application-center','files','填表與列印'],['document-check','scan-line','檢查文件'],['documents','folder-lock','文件庫']];
}
function renderTools(l){
  const section=document.createElement('section');section.className='path-level-tools';
  const links=toolsFor(l),tool=route().get('tool')||'';
  section.innerHTML='<nav aria-label="這一關的工具">'+links.map(([page,i,title])=>'<a class="outline-button" href="'+toolHref(page)+'"'+(page===tool?' aria-current="page"':'')+'>'+icon(i)+esc(title)+'</a>').join('')+'<a class="quiet-button" href="#my-application?view=schedule">'+icon('calendar-clock')+'時程</a></nav><div id="path-tool-panel" hidden><header class="path-tool-heading"><span id="path-tool-scope"></span><a class="quiet-button" href="'+href('level',l.id)+'">收合工具'+icon('x')+'</a></header><div id="path-tool-host"></div></div>';
  $('#level-view').append(section);
  if(!toolHref(tool))return;
  $('#path-tool-panel').hidden=false;
  if(plan().archived){$('#path-tool-host').textContent='恢復計畫後即可使用編輯工具。';return;}
  const sharedSelection=['advisor','favorites','eligibility'].includes(tool);
  $('#path-tool-scope').textContent=sharedSelection?'條件與志願沿用帳號資料；這一關的完成紀錄獨立保存。':'表單沿用帳號的共用草稿；各計畫的關卡、分段寫作與文件連結分別保存。';
  const c=plan().context;
  const toolContext={...c,semester:({fall:'第一學期',spring:'第二學期',full_year:'一學年',undecided:''})[c.semester]};
  const matching=['target_school','academic_year','application_round','semester','college','department','degree_level'].every(k=>(state.applicationContext[k]||'')===(toolContext[k]||''));
  if(!sharedSelection&&!matching){
    $('#path-tool-host').innerHTML='<div class="path-context-gate"><p>使用 '+esc(c.target_school)+' · '+esc(c.academic_year)+' · '+esc(termName(c.semester))+' 的文件規則</p><button id="path-use-context" class="primary-button">載入本計畫的文件工具</button><small>切換工具的查看目標，保留現有草稿與其他計畫進度。</small><p id="path-tool-error" role="alert"></p></div>';
    $('#path-use-context').onclick=async()=>{
      const captured=key(),run=epoch,url=location.hash,b=$('#path-use-context');b.disabled=true;
      try{
        if(!await confirmPlanningTargetChange(c.target_school)||run!==epoch||captured!==key()||location.hash!==url)return;
        state.planningRequestId++;state.planningLoading=false;state.planningPreview=null;
        invalidateAllApplicationReviews();
        state.applicationContext={...state.applicationContext,school_name:c.home_school,program_type:'exchange',...Object.fromEntries(['target_school','academic_year','application_round','semester','college','department','degree_level'].map(k=>[k,toolContext[k]||'']))};
        persistApplicationContext();restoreApplicationContextForm();
        await loadApplicationTemplates();
        if(run===epoch&&captured===key()&&location.hash===url)mountTool(tool);
      }catch(e){if(run===epoch&&captured===key()&&location.hash===url)$('#path-tool-error').textContent=e.message;}
      finally{if(b.isConnected)b.disabled=false;}
    };
  }else mountTool(tool);
  queueMicrotask(()=>requestAnimationFrame(()=>{if(active&&route().get('tool')===tool)$('#path-tool-panel')?.scrollIntoView({block:'start',behavior:'instant'});}));
}
function mountTool(tool){
  const host=$('#path-tool-host');if(!host)return;
  window.UniWayApplicationWorkspace?.release();host.replaceChildren();
  if(tool.startsWith('application-form=')&&!applicationDocumentGenerationEnabled())tool='application-center';
  window.UniWayApplicationWorkspace?.mount(tool,host);
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
    const v=saved.versions.at(-1);await loadFiles();if(captured!==key()||id!==activeId||run!==epoch)return;$('#file-version').value=v.id;edit();$('#save-note').textContent=drafts.get(draftKey())?.conflict?'檔案已上傳，請比對版本後儲存連結':'檔案已上傳，正在保存連結';await save(false,{quiet:true});
  }catch(e){if(captured===key()&&id===activeId)error(e.message);}finally{if(b.isConnected)b.disabled=false;}
}
async function archive(){
  if(!view||saving)return;
  const archived=!plan().archived;
  stash();
  const pending=[...drafts.keys()].map(k=>JSON.parse(k)).find(([home,id])=>home===plan().context.home_school&&id===plan().id);
  if(archived&&pending){location.hash=href('level',pending[2]);toast('先儲存這項草稿，再封存計畫。',true);return;}
  const run=epoch,captured=key(),id=plan().id,name=plan().context.target_school.split(/[（(]/)[0].trim();
  saving=true;$('#archive-plan').disabled=true;
  try{
    const saved=await fetchJson(pathUrl()+'/archive'+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,archived})});
    if(run!==epoch||captured!==key())return;
    view=saved;dirty=false;saving=false;await load();
    toast(archived?'已封存「'+name+'」。進度與文件都保留。':'已恢復「'+name+'」。',false,archived?{label:'復原',run:()=>restorePlan(id)}:null);
  }catch(e){if(run===epoch&&captured===key())toast(e.message,true);}
  finally{saving=false;$('#archive-plan').disabled=false;}
}
async function restorePlan(id){
  if(saving||!state.account)return;
  saving=true;
  try{
    const saved=await fetchJson('/account/application-paths/'+encodeURIComponent(id)+'/archive'+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view?.revision||listing?.revision||0,archived:false})});
    saving=false;view=null;location.hash='#my-application?'+new URLSearchParams({plan:saved.plan.id,view:'today'});await load(true);
    toast('已恢復這份計畫。');
  }catch(e){toast(e.message,true);}
  finally{saving=false;}
}
async function undoStep(id,before){
  if(!view||saving)return;
  saving=true;
  try{
    const prior={value:before.value||'',confirmed:false,version_id:before.version_id||null,applicable:before.applicable??null};
    const saved=await fetchJson(pathUrl()+'/steps/'+encodeURIComponent(id)+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,step:prior})});
    view=saved;listing.revision=saved.revision;dirty=false;saving=false;render();toast('已撤銷，回到完成前的狀態。');
  }catch(e){toast(e.message,true);}
  finally{saving=false;}
}
async function openNew(preferredTarget=''){
  if(typeof preferredTarget!=='string')preferredTarget='';
  if(!state.account){openAuthDialog();return;}
  stash();
  const captured=key();$('#create-error').hidden=true;
  try{
    const dashboard=state.dashboard?.school_name===activeHomeSchool()?state.dashboard:await fetchJson('/student-dashboard?school='+encodeURIComponent(activeHomeSchool()));
    if(captured!==key())return;
    const old=preferredTarget?{...(view?.plan.context||{}),target_school:preferredTarget}:listing?.legacy?.context||{}, profile=state.selectionConditions?.profile||{};
    $('#create-home').value=activeHomeSchool();$('#create-target').innerHTML='<option value="">選擇交換學校</option>'+dashboard.partner_universities.map(p=>'<option '+(p.school_name===old.target_school?'selected':'')+'>'+esc(p.school_name)+'</option>').join('');
    for(const [id,value] of Object.entries({'create-year':old.academic_year||'','create-round':old.application_round||'','create-college':old.college||profile.college||'','create-department':old.department||profile.department||'','create-degree':old.degree_level||profile.degree_level||''}))$('#'+id).value=value;
    $('#import-existing').checked=false;buildSemesterChoices(old);
    $('#plan-dialog').showModal();
  }catch(e){if(captured===key())toast(e.message,true);}
}
async function create(e){
  e.preventDefault();if(creating)return;
  if(!$('#create-departure').value){$('#create-error').textContent='請選擇預計出發學期。';$('#create-error').hidden=false;return;}creating=true;const captured=key(),run=epoch,button=$('#plan-form button[type=submit]');button.disabled=true;
  const payload={revision:listing?.revision||0,home_school:activeHomeSchool(),target_school:$('#create-target').value,academic_year:$('#create-year').value,application_round:$('#create-round').value,departure_year:$('#create-departure').value,semester:$('#create-term').value,college:$('#create-college').value,department:$('#create-department').value,degree_level:$('#create-degree').value,import_existing:$('#import-existing').checked};
  try{const saved=await fetchJson('/account/application-paths',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(captured!==key()||run!==epoch)return;
    track('plan_create_result',{result:'success'});$('#plan-dialog').close();view=null;location.hash='#my-application?'+new URLSearchParams({plan:saved.plan.id,view:'today'});load();
  }catch(error){track('plan_create_result',{result:'failed',status:error.status||0});if(captured===key()){$('#create-error').textContent=error.message;$('#create-error').hidden=false;}}
  finally{creating=false;button.disabled=false;}
}
// The approved map renderer is shared in appearance, never in preview storage.
function renderMap(){
  const all=levels(),n=next();
  $('#path-stages').innerHTML=stages().map(s=>{
    const t=totals(s.levels),h=s.levels.length*152+123;
    return '<section class="path-stage" id="stage-'+s.index+'" aria-label="第 '+(s.index+1)+' 階段 '+esc(s.title)+'" style="height:'+h+'px"><svg class="path-svg" aria-hidden="true"></svg><div class="stage-divider"><svg class="stage-wave" viewBox="0 0 640 100" preserveAspectRatio="none" aria-hidden="true"><path d="M0 22 C95 -14 170 42 280 18 S470 -5 640 22 L640 80 C525 115 445 65 330 85 S110 110 0 80Z" fill="#c8eaf3"/><path d="M0 36 C100 5 185 55 290 32 S480 15 640 34 L640 80 C525 115 445 65 330 85 S110 110 0 80Z" fill="#e0f3f8"/></svg><span>'+String(s.index+1).padStart(2,'0')+'</span><h3>'+esc(s.title)+'</h3><small>'+(t.count?t.done+' / '+t.count+' 項':s.levels.every(l=>l.external)?s.levels.filter(l=>hasContent(l)).length+' / '+s.levels.length+' 筆通知':'設定與選用')+'</small></div>'+s.levels.map(l=>{
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
// ---- semester choices for a new plan: students pick when they leave; the academic year (民國) is worked out ----
function semesterChoices(){
  const now=new Date(),y=now.getFullYear(),m=now.getMonth()+1;
  let year=m<=8?y:y+1,term=m<=1||m>8?'spring':'fall';
  const out=[];
  for(let i=0;i<4;i++){out.push({year,term});if(term==='spring')term='fall';else{term='spring';year++;}}
  return out;
}
const rocYear=(year,term)=>term==='spring'?year-1912:year-1911;
function buildSemesterChoices(old){
  const options=semesterChoices().map(o=>({...o,label:o.year+' 年'+(o.term==='fall'?'秋季出發（上學期）':'春季出發（下學期）')}));
  const fall=options.find(o=>o.term==='fall');
  options.push({year:fall.year,term:'full_year',label:fall.year+' 年秋季出發・全學年'},{year:fall.year,term:'undecided',label:'還沒決定'});
  const keyOf=o=>o.term+':'+o.year;
  const match=options.find(o=>String(o.year)===String(old.departure_year||'')&&o.term===(old.semester||''))||options[0];
  $('#create-semesters').innerHTML=options.map(o=>'<label class="ap-semester-option"><input type="radio" name="create-semester" value="'+keyOf(o)+'" required '+(o===match?'checked':'')+'><span>'+esc(o.label)+'</span></label>').join('');
  const apply=()=>{
    const picked=options.find(o=>keyOf(o)===($('#create-semesters input:checked')?.value||''));
    if(!picked){$('#create-year').value='';$('#create-departure').value='';$('#create-term').value='undecided';$('#create-derived').textContent='';return;}
    const roc=rocYear(picked.year,picked.term);
    $('#create-year').value=String(roc);$('#create-departure').value=String(picked.year);$('#create-term').value=picked.term;
    $('#create-derived').textContent=picked.term==='undecided'?'先以 '+roc+' 學年度規劃，決定後可新增正式的計畫。':'對應 '+roc+' 學年度的申請，實際日期以學校公告為準。';
  };
  $('#create-semesters').onchange=apply;apply();
}

// ---- numbers for any loaded plan (the 計畫 view compares several) ----
function statsFor(data){
  const steps=data.plan.steps||{},rec=id=>steps[id]||{};
  const all=data.stages.flatMap(s=>s.levels.map(l=>({...l,stageTitle:s.title})));
  const req=l=>!['home','term','target'].includes(l.id)&&!['write','assemble'].includes(l.kind)&&!l.external&&l.counted!==false;
  const done=l=>l.counted!==false&&!l.external&&l.progress.value===l.progress.total;
  const counted=all.filter(req),finished=counted.filter(done);
  const deadline=all.filter(l=>l.official_deadline_at&&l.deadline_confirmed&&!l.external&&!done(l)&&rec(l.id).applicable!==false).sort((a,b)=>a.official_deadline_at.localeCompare(b.official_deadline_at))[0];
  const stageOrder=[...new Set(counted.map(l=>l.stageTitle))];
  const stage=stageOrder.find(t=>counted.filter(l=>l.stageTitle===t).some(l=>!done(l)));
  return {done:finished.length,total:counted.length,deadline,stage:stage||'',files:counted.filter(l=>l.kind==='file'),missingFiles:counted.filter(l=>l.kind==='file'&&!done(l)),next:counted.find(l=>!done(l)&&!(l.blocked_by||[]).length)};
}
const planName=p=>p.context.target_school.split(/[（(]/)[0].trim();
const planTerm=p=>p.context.departure_year+' '+termName(p.context.semester);
function deadlineText(d){
  if(!d)return '尚未公布';
  const when=new Date(d.official_deadline_at),left=Math.ceil((when-Date.now())/86400000);
  return when.toLocaleDateString('zh-TW',{timeZone:'Asia/Taipei',month:'numeric',day:'numeric'})+(when<new Date()?'（已過期）':left<=0?'（今天）':'（還有 '+left+' 天）');
}
const planLink=(tab,planId,id='')=>'#my-application?'+new URLSearchParams({plan:planId,view:tab,...(id?{level:id}:{})});
let plansRun=0;
async function renderPlans(){
  const host=$('#plans-dynamic'),run=++plansRun;
  const active=listing.items.filter(p=>!p.archived),archivedPlans=listing.items.filter(p=>p.archived);
  host.innerHTML='<p class="today-empty" role="status">正在整理各份計畫…</p>';
  const entries=await Promise.all(active.map(async p=>({p,data:p.id===plan().id?view:await fetchJson('/account/application-paths/'+encodeURIComponent(p.id)+query()).catch(()=>null)})));
  if(run!==plansRun||route().get('view')!=='plans')return;
  const ok=entries.filter(x=>x.data).map(x=>({...x,s:statsFor(x.data)}));
  const card=({p,s})=>'<article class="plan-card'+(p.id===plan().id?' current':'')+'"><h3>'+esc(planName(p))+'</h3><p class="today-hint">'+esc(planTerm(p))+' · '+esc(p.context.academic_year)+' 學年度</p><dl class="plan-nums"><div><dt>準備進度</dt><dd>'+s.done+' / '+s.total+'</dd></div><div><dt>下個期限</dt><dd>'+esc(deadlineText(s.deadline))+'</dd></div></dl><p class="today-hint">目前階段：'+esc(s.stage||'已完成已知準備事項')+'</p><a class="today-primary dark" href="'+planLink('today',p.id)+'">'+(p.id===plan().id?'回到今天':'繼續')+icon('arrow-right')+'</a></article>';
  const failed=entries.filter(x=>!x.data).map(({p})=>'<article class="plan-card"><h3>'+esc(planName(p))+'</h3><p class="today-hint">暫時讀不到這份計畫，請稍後重新載入。</p></article>');
  let compare='';
  if(ok.length>1){
    const row=(label,fn)=>'<tr><th scope="row">'+label+'</th>'+ok.map(x=>'<td>'+fn(x)+'</td>').join('')+'</tr>';
    compare='<table class="plan-compare" aria-label="計畫比較"><thead><tr><th scope="col"></th>'+ok.map(x=>'<th scope="col">'+esc(planName(x.p))+'<br><small>'+esc(planTerm(x.p))+'</small></th>').join('')+'</tr></thead><tbody>'+
      row('下個期限',x=>esc(deadlineText(x.s.deadline)))+row('準備進度',x=>x.s.done+' / '+x.s.total)+row('還缺的文件',x=>x.s.missingFiles.length+' 份')+row('目前階段',x=>esc(x.s.stage||'已完成'))+
      row('下一步',x=>x.s.next?'<a href="'+planLink('level',x.p.id,x.s.next.id)+'">'+esc(x.s.next.title)+'</a>':'—')+'</tbody></table>';
    const counts=new Map();ok.forEach(x=>new Set(x.s.files.map(l=>l.title)).forEach(t=>counts.set(t,(counts.get(t)||0)+1)));
    const shared=[...counts].filter(([,n])=>n===ok.length).map(([t])=>t);
    if(shared.length)compare+='<p class="plan-shared">'+icon('info')+'<span><b>每份計畫都需要 '+shared.length+' 份相同名稱的文件：</b>'+esc(shared.slice(0,4).join('、'))+(shared.length>4?' 等':'')+'。各計畫分開記錄，備妥後請在每份計畫都標記。</span></p>';
  }
  host.innerHTML='<div class="plans"><div class="plan-cards">'+ok.map(card).join('')+failed.join('')+'</div>'+compare+
    '<div class="plan-links"><a class="today-link" href="'+href('progress')+'">'+icon('list-checks')+'完整準備清單</a><a class="today-link" href="'+href('map')+'">'+icon('route')+'申請路徑地圖</a><button type="button" class="today-text" data-path-new>'+icon('plus')+'新增計畫</button></div>'+
    (archivedPlans.length?'<details class="plan-archived"><summary>已封存的計畫（'+archivedPlans.length+'）</summary><ul>'+archivedPlans.map(p=>'<li><span>'+esc(planName(p))+' · '+esc(planTerm(p))+'</span><button type="button" class="today-text" data-restore-plan="'+esc(p.id)+'">復原</button></li>').join('')+'</ul></details>':'')+'</div>';
  icons();
}

// ---- 時程: confirmed deadlines of this plan on top, then the existing scheduling tools, reorganised ----
function adoptSchedule(){
  const host=$('#schedule-legacy');if(host.dataset.ready)return;
  const page=document.querySelector('#overview');
  if(!page){host.textContent='時程工具暫時無法載入。';return;}
  page.removeAttribute('data-university-page');page.hidden=false;page.classList.add('in-workbench');
  page.querySelector('#application-plan-index')?.remove();
  const tracker=page.querySelector('#tracker-title');
  if(tracker){const h=document.createElement('h2');h.id='tracker-title';h.textContent='待辦與期限';tracker.replaceWith(h);}
  const legacy=document.querySelector('#application-plan-details');
  if(legacy){const name=legacy.querySelector('summary strong');if(name)name.textContent='選校條件與志願順序';}
  host.append(page);host.dataset.ready='1';
  window.UniWayTracker?.render();
}
// The scheduling tools read one shared target (state.applicationContext). Follow the open plan; ask before replacing another target.
function planContextMatches(){
  const c=plan().context,term=({fall:'第一學期',spring:'第二學期',full_year:'一學年',undecided:''})[c.semester];
  const want={...c,semester:term};
  return ['target_school','academic_year','application_round','semester','college','department','degree_level'].every(k=>(state.applicationContext[k]||'')===(want[k]||''));
}
async function applyPlanContext(){
  const c=plan().context,term=({fall:'第一學期',spring:'第二學期',full_year:'一學年',undecided:''})[c.semester];
  if(!await confirmPlanningTargetChange(c.target_school))return false;
  state.planningRequestId++;state.planningLoading=false;state.planningPreview=null;
  invalidateAllApplicationReviews();
  state.applicationContext={...state.applicationContext,school_name:c.home_school,program_type:'exchange',...Object.fromEntries(['target_school','academic_year','application_round','semester','college','department','degree_level'].map(k=>[k,(k==='semester'?term:c[k])||'']))};
  persistApplicationContext();restoreApplicationContextForm();
  await loadApplicationTemplates();
  if(typeof renderPlanningWorkspace==='function')renderPlanningWorkspace();
  return true;
}
function showScheduleWithoutPlan(loggedOut=false){
  $('#hub').hidden=true;$('#level-view').hidden=true;$('#path-message').hidden=!loggedOut;$('#archive-plan').hidden=true;
  $('#schedule-view').hidden=false;adoptSchedule();
  if(loggedOut){$('#schedule-dynamic').replaceChildren();icons();return;}
  $('#schedule-dynamic').innerHTML='<section class="sched-deadlines"><div class="today-head"><h2>還沒有申請計畫</h2></div><p class="today-hint">建立計畫後，這裡會列出已確認的官方期限與每項準備的待辦。你也可以先在下面記自己的待辦。</p><button type="button" class="today-primary dark" data-path-new>建立計畫'+icon('arrow-right')+'</button><a class="today-link" href="#partners">先找適合的學校'+icon('arrow-right')+'</a></section>';
  icons();
}
function renderSchedule(){
  adoptSchedule();
  const settings=document.querySelector('#planning-deadline-settings');
  if(settings&&!settings.dataset.opened){settings.open=true;settings.dataset.opened='1';}
  const list=levels().filter(l=>confirmedDeadline(l)&&!l.external&&status(l)!=='skipped'&&!isDone(l)).sort((a,b)=>a.official_deadline_at.localeCompare(b.official_deadline_at)).slice(0,5);
  const source=levels().flatMap(urls)[0];
  const fmt=(d,o)=>d.toLocaleDateString('zh-TW',{timeZone:'Asia/Taipei',...o});
  const mismatch=!planContextMatches();
  if(mismatch&&!state.applicationContext.target_school)applyPlanContext().then(()=>{if(active&&route().get('view')==='schedule')renderSchedule();}).catch(()=>{});
  $('#schedule-dynamic').innerHTML=(mismatch&&state.applicationContext.target_school?'<div class="sched-context"><p>排時程的目標目前是「'+esc(state.applicationContext.target_school.split(/[（(]/)[0].trim())+'」。要改用這份計畫嗎？</p><button type="button" class="today-add" data-use-plan-context>改用「'+esc(planName(plan()))+'」排時程</button></div>':'')+'<section class="sched-deadlines" aria-labelledby="sched-deadlines-title"><div class="today-head"><h2 id="sched-deadlines-title">已確認的官方期限</h2><p>'+esc(planName(plan()))+' · '+esc(planTerm(plan()))+'</p></div>'+
    (list.length?'<ol>'+list.map(l=>{const d=new Date(l.official_deadline_at),left=Math.ceil((d-Date.now())/86400000);return '<li><a href="'+href('level',l.id)+'"><span class="sched-date"><b>'+fmt(d,{month:'numeric',day:'numeric'})+'</b><small>'+fmt(d,{weekday:'short'})+'</small></span><span class="today-row"><b>'+esc(l.title)+'</b><small>'+esc(l.stageTitle)+'</small></span><span class="today-pill '+(d<new Date()?'late':left<=14?'soon':'')+'">'+(d<new Date()?'已過期':left<=0?'今天':'還有 '+left+' 天')+'</span></a></li>';}).join('')+'</ol>':
      '<p class="today-empty">目前沒有已確認的期限。</p><p class="today-hint">UniWay 只倒數有官方來源、已確認的日期，不會猜。查到日期後，可以在下面「待辦與期限」記一則個人提醒。</p>'+(source?'<a class="today-link" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">查看官方公告'+icon('arrow-up-right')+'</a>':''))+'</section>';
  icons();
}
// Tasks of the open plan for the list on 時程: what is in progress, the next few that can start, and what is done.
function workbenchTotals(){if(!view||plan().archived)return null;const t=totals();return {done:t.done,total:t.count};}
function workbenchRows(){
  if(!view||plan().archived)return [];
  const school=plan().context.target_school;
  const all=levels().filter(l=>required(l)&&status(l)!=='skipped'),open=all.filter(l=>!isDone(l));
  const started=open.filter(l=>status(l)==='started'||drafts.has(draftKey(l.id)));
  const ready=open.filter(l=>!started.includes(l)&&!missing(l).length).slice(0,12);
  const dateOf=l=>confirmedDeadline(l)?new Date(l.official_deadline_at).toLocaleDateString('sv-SE',{timeZone:'Asia/Taipei'}):'';
  const order=new Map(levels().map((l,i)=>[l.id,i]));
  const row=(l,state)=>({key:'path-'+l.id,title:l.title,status:state,school,date:dateOf(l),plan:false,href:href('level',l.id),order:order.get(l.id)});
  return [...started.map(l=>row(l,'preparing')),...ready.map(l=>row(l,'todo')),...all.filter(isDone).map(l=>row(l,'ready'))];
}
// 今天: one task to do now, the next confirmed deadline, where the student is, and what comes next.
// It reads the same plan as the checklist and the map; nothing here is stored separately.
const KIND_LABEL={confirm:'條件確認',write:'寫作',file:'文件',note:'事項',submission:'送件',assemble:'整理',notice:'通知'};
function stageGroups(){
  const groups=[];
  for(const s of stages()){const last=groups[groups.length-1];if(last&&last.title===s.title)last.levels.push(...s.levels);else groups.push({title:s.title,levels:[...s.levels]});}
  return groups.map(g=>({...g,...totals(g.levels)})).filter(g=>g.count>0);
}
function deadlineHtml(due,source){
  if(!due)return '<h3>下一個已確認的官方期限</h3><p class="today-empty">目前沒有已確認的期限。</p><p class="today-hint">UniWay 只倒數有官方來源、已確認的日期，不會猜。</p>'+(source?'<a class="today-link" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">查看官方公告'+icon('arrow-up-right')+'</a>':'');
  const d=new Date(due.official_deadline_at),tz={timeZone:'Asia/Taipei'},past=d<new Date(),left=Math.ceil((d-Date.now())/86400000);
  return '<h3>下一個已確認的官方期限</h3><p class="today-date">'+d.toLocaleDateString('zh-TW',{...tz,month:'numeric',day:'numeric'})+'</p><p><b>'+d.toLocaleDateString('zh-TW',{...tz,weekday:'short'})+' '+d.toLocaleTimeString('zh-TW',{...tz,hour:'2-digit',minute:'2-digit',hour12:false})+'</b> <span class="today-pill '+(past?'late':left<=14?'soon':'')+'">'+(past?'已過期':left<=0?'今天截止':'還有 '+left+' 天')+'</span></p><p>'+esc(due.title)+'</p><a class="today-link" href="'+href('level',due.id)+'">前往這一項'+icon('arrow-right')+'</a>';
}
function personalTasks(){
  const own=(state.calendarEvents||[]).filter(e=>e.origin!=='official'&&e.title&&e.status!=='ready').sort((a,b)=>(a.date||'').localeCompare(b.date||'')).slice(0,4);
  return '<div class="today-own"><h3>我加的待辦</h3>'+(own.length?'<ul>'+own.map(e=>'<li><span>'+esc(e.title)+'</span><small>'+esc(e.date||'')+'</small></li>').join('')+'</ul>':'<p class="today-hint">還沒有。記下你自己要做的小事，例如請系主任簽名。</p>')+
    '<form class="today-quick" data-today-quick><input name="title" maxlength="80" required aria-label="新增待辦" placeholder="新增待辦，例如：請系主任簽名…"><input name="date" type="date" required aria-label="日期" value="'+localDateKey()+'"><button type="submit" class="today-add">加入</button><span class="form-status" role="status"></span></form></div>';
}
function renderToday(){
  const n=next(),t=totals(),all=levels(),groups=stageGroups();
  let current=groups.findIndex(g=>g.levels.some(l=>l.id===n?.id));
  if(current<0)current=Math.max(0,groups.findIndex(g=>g.done<g.count));
  const g=groups[current],resume=n&&(status(n)==='started'||drafts.has(draftKey(n.id)));
  const due=all.filter(l=>confirmedDeadline(l)&&!l.external&&status(l)!=='skipped'&&!isDone(l)).sort((a,b)=>a.official_deadline_at.localeCompare(b.official_deadline_at))[0];
  const source=urls(n||{})[0]||all.flatMap(urls)[0];
  const queue=all.filter(l=>l.id!==n?.id&&!l.external&&!setup(l)&&!assistance(l)&&status(l)!=='skipped'&&!isDone(l)&&!missing(l).length).slice(0,5);
  const checks=all.filter(l=>l.check_status),counts={pass:0,fail:0,needs_confirmation:0};
  checks.forEach(l=>counts[l.check_status]++);
  const open=checks.find(l=>l.check_status!=='pass');
  const tag=l=>drafts.has(draftKey(l.id))?'草稿未儲存':status(l)==='started'?'進行中':l.conditional&&record(l.id).applicable==null?'待確認適用性':'';
  $('#today-view').innerHTML='<div class="today">'+
    '<div class="today-top"><section class="today-focus" aria-labelledby="today-focus-title"><span class="today-label">'+(n?'現在做這件事':'目前進度')+'</span><h2 id="today-focus-title">'+esc(n?n.title:'已完成已知的準備事項')+'</h2>'+(n&&n.prompt?'<p>'+esc(n.prompt.length>110?n.prompt.slice(0,110)+'…':n.prompt)+'</p>':'')+'<p class="today-why">'+esc(nextReason(n))+'</p>'+
      (n?'<div class="today-meta"><span>'+esc(KIND_LABEL[n.kind]||'事項')+'</span><span>'+esc(n.stageTitle)+'</span>'+(urls(n)[0]?'<a href="'+esc(urls(n)[0])+'" target="_blank" rel="noopener noreferrer">官方來源'+icon('arrow-up-right')+'</a>':'')+'</div>':'')+
      '<div class="today-actions"><a class="today-primary" href="'+(n?href('level',n.id):href('progress'))+'">'+(n?(resume?'繼續填寫':'開始'):'查看清單')+icon('arrow-right')+'</a></div></section>'+
      '<aside class="today-panel" aria-label="期限">'+deadlineHtml(due,source)+'</aside></div>'+
    '<section class="today-stages" aria-labelledby="today-stages-title"><div class="today-head"><h2 id="today-stages-title">申請階段</h2><p>個人準備進度 <b>'+t.done+' / '+t.count+'</b> 項 <button type="button" class="today-text" data-open-info>這怎麼計算？</button></p></div>'+
      '<ol class="today-track" aria-label="各階段進度">'+groups.map((x,i)=>'<li data-s="'+(x.done===x.count?'done':i===current?'now':'todo')+'"><span class="visually-hidden">'+esc(x.title)+'：'+x.done+' / '+x.count+'</span></li>').join('')+'</ol>'+
      (g?'<p class="today-stage-now">目前階段：<b>'+esc(g.title)+'</b>（'+g.done+' / '+g.count+'）· 第 '+(current+1)+' / '+groups.length+' 階段</p>':'')+'</section>'+
    '<div class="today-bottom"><section class="today-queue" aria-labelledby="today-queue-title"><h2 id="today-queue-title">接下來</h2>'+
      (queue.length?'<ul>'+queue.map(l=>'<li><a href="'+href('level',l.id)+'"><span class="today-row"><b>'+esc(l.title)+'</b><small>'+esc(l.stageTitle)+' · '+esc(KIND_LABEL[l.kind]||'事項')+'</small></span>'+(tag(l)?'<span class="today-tag">'+tag(l)+'</span>':'')+icon('chevron-right')+'</a></li>').join('')+'</ul>':'<p class="today-empty">沒有其他可以現在開始的項目。</p>')+
      '<a class="today-link" href="'+href('progress')+'">查看全部準備清單'+icon('arrow-right')+'</a>'+personalTasks()+'</section>'+
      (checks.length?'<aside class="today-panel" aria-labelledby="today-checks-title"><h3 id="today-checks-title">資格條件檢查</h3><ul class="today-counts"><li class="pass"><b>'+counts.pass+'</b>符合</li><li class="fail"><b>'+counts.fail+'</b>不符合</li><li class="needs"><b>'+counts.needs_confirmation+'</b>待確認</li></ul><p class="today-hint">依已查核的規則比對，仍以校方審核為準。</p>'+(open?'<a class="today-link" href="'+href('level',open.id)+'">查看需要處理的條件'+icon('arrow-right')+'</a>':'')+'</aside>':'')+'</div>'+
    '<p class="today-boundary">'+icon('info')+'圓圈與進度只代表你自己的準備，不代表校方受理或錄取。</p></div>';
}
function renderOverview(){
  const t=totals();
  $('#overview-summary').innerHTML='<h2>準備清單</h2><p>'+t.done+' / '+t.count+' 項已完成'+(t.pending?' · '+t.pending+' 項待確認適用性':'')+'</p>';
  const groups=new Map();
  for(const l of levels()){
    const group=l.external?'校方通知紀錄':setup(l)?'計畫設定':assistance(l)?'選用寫作協助':l.stageTitle;
    if(!groups.has(group))groups.set(group,[]);groups.get(group).push(l);
  }
  let shown=0;const n=next();
  const groupOrder=([title])=>title==='校方通知紀錄'?1:title==='選用寫作協助'?2:title==='計畫設定'?3:0;
  $('#overview-stages').innerHTML=[...groups].sort((a,b)=>groupOrder(a)-groupOrder(b)).map(([title,items])=>{
    const optional=title==='計畫設定'||title==='選用寫作協助',external=items.every(l=>l.external);
    const rows=items.filter(l=>filter==='all'||(filter==='pending'?l.conditional&&record(l.id).applicable==null:filter==='external'?l.external:filter==='skipped'?status(l)==='skipped':!l.external&&!optional&&status(l)===filter));
    if(!rows.length)return '';shown+=rows.length;
    const st=totals(items),open=!optional&&!external&&(filter!=='all'||items.some(l=>l.id===n?.id)||(!n&&st.done<st.count));
    return '<details class="task-stage" '+(open?'open':'')+'><summary><h3>'+esc(title)+'</h3><span>'+(external?'自行記錄':optional?'選用':st.done+' / '+st.count+' 項')+'</span></summary>'+(external?'<p>由你記錄，不代表平台已核實校方結果。</p>':'')+rows.map(l=>{
      const s=status(l),pending=l.conditional&&record(l.id).applicable==null;
      const label=l.external?(hasContent(l)?'已記錄':'等待通知'):s==='skipped'?'不適用':pending?'待確認':s==='done'?'已完成':s==='started'?'進行中':'尚未開始';
      return '<a class="task-row '+(s==='done'?'is-done':'')+'" href="'+href('level',l.id)+'">'+icon(s==='done'?'circle-check':missing(l).length?'lock-keyhole':'circle')+'<strong>'+esc(l.title)+'</strong><span>'+label+'</span>'+icon('chevron-right')+'</a>';
    }).join('')+'</details>';
  }).join('');
  if(!shown)$('#overview-stages').innerHTML='<div class="overview-empty"><p>這個分類目前沒有項目。</p><button data-clear-filter class="outline-button">查看全部</button></div>';
  $('[data-clear-filter]')?.addEventListener('click',()=>{$('[data-filter="all"]').click();});icons();
}

function maybeOpenTarget(){
  const target=route().get('target');if(!target||!listing)return;
  history.replaceState(null,'',href());openNew(target);
}
function startTarget(schoolName){
  if(!state.account){openAuthDialog();return;}
  const existing=(window.UniWayPlanIndex?.current()?.items||[]).find(p=>!p.archived&&p.context.target_school===schoolName);
  location.hash='#my-application?'+new URLSearchParams(existing?{plan:existing.id,view:'today'}:{target:schoolName});
}

return {init,show,refresh,clear,toolHref,formToolActive,selectTarget,startTarget,resumeOAuth,workbenchRows,workbenchTotals,hasRecoverableDrafts:()=>drafts.size>0};
})();

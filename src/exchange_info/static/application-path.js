/* Account-backed application map. Private edits stay in memory until server CAS succeeds. */
window.UniWayApplicationPath = (() => {
'use strict';
let root, picker, view=null, listing=null, owner='', epoch=0, loading=false, saving=false, wsSaving=false, active=false;
let activeId=null, dirty=false, mapPosition=null, mapPositionPlan=null, toastTimer;
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
  dirty=true;editVersion++;stash();if($('#save-note'))$('#save-note').textContent='尚未儲存';clearTimeout(autosaveTimer);
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
function completeLabel(l){
  if(l.cgu_level_type==='reading')return '我已讀完申請須知並確認';
  return l.external?'儲存通知紀錄':l.kind==='checks'?'我已看過，完成資格確認':l.kind==='submission'?'我已送件':l.kind==='file'?'文件已備妥':l.kind==='confirm'?'確認內容':'完成';
}

const $=(s,r=root)=>r?.querySelector(s), $$=(s,r=root)=>[...(r?.querySelectorAll(s)||[])];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=n=>'<i data-lucide="'+esc(n)+'" aria-hidden="true"></i>';
const hasDraftInput=l=>!['confirm','checks','assemble'].includes(l.kind)&&!l.no_draft_input;
const termName=t=>({fall:'上學期',spring:'下學期',full_year:'全學年',undecided:'尚未決定'}[t]||t);
function defaultRoundFor(home,year,departureYear,semester){
  if(home!=='長庚大學')return '';
  const y=String(year||'').trim(),dep=String(departureYear||'').trim();
  if(!y)return '';
  if(semester==='spring')return y+'-2'+(dep?'（'+dep+' 春季出國）':'');
  if(semester==='fall')return y+'-1'+(dep?'（'+dep+' 秋季出國）':'');
  if(semester==='full_year')return y+'-1'+(dep?'（'+dep+' 秋季・全學年出國）':'');
  return '';
}
function roundConflictsWithContext(roundText,academicYear,semester){
  const r=String(roundText||'').trim(),ay=String(academicYear||'').trim();
  if(!r)return false;
  const m=r.match(/(?<!\d)(\d{2,3})\s*[-–]\s*([12])(?!\d)/);
  if(m){
    if(ay&&m[1]!==ay)return true;
    if(m[2]==='1'&&semester==='spring')return true;
    if(m[2]==='2'&&(semester==='fall'||semester==='full_year'))return true;
    if(semester==='undecided')return true;
  }
  if(semester==='spring'&&/第\s*[1一]\s*學期|上學期|秋季/.test(r))return true;
  if((semester==='fall'||semester==='full_year')&&/第\s*[2二]\s*學期|下學期|春季/.test(r))return true;
  if(semester==='undecided'&&/第\s*[12一二]\s*學期|[上下]學期|春季|秋季/.test(r))return true;
  return false;
}
const planRoundLabel=c=>{
  const raw=c.application_round||'';
  if(raw&&!roundConflictsWithContext(raw,c.academic_year,c.semester))return raw;
  return defaultRoundFor(c.home_school,c.academic_year,c.departure_year,c.semester)||'梯次待確認';
};
function formatContextTerm(c){
  const y=c?.departure_year||'',s=c?.semester||'',ay=c?.academic_year||(y?String(s==='spring'?Number(y)-1912:Number(y)-1911):'');
  if(window.cguDemoStorageIsolated||c?.home_school==='長庚大學'){
    if(s==='fall')return (y?y+' ':'')+'秋季'+(ay?'（'+ay+'-1）':'');
    if(s==='spring')return (y?y+' ':'')+'春季'+(ay?'（'+ay+'-2）':'');
    if(s==='full_year')return (y?y+' ':'')+'秋季・全學年'+(ay?'（'+ay+'-1）':'');
    return (y?y+' ':'')+'尚未決定';
  }
  return y+' '+termName(s);
}
const route=()=>new URLSearchParams(location.hash.split('?')[1]||'');
const FROM_LABELS={today:'總覽',plans:'計畫比較',progress:'總覽',workspace:'我的待辦',schedule:'時程',map:'路徑地圖'};
const href=(tab='progress',id='',from='')=>'#my-application?'+new URLSearchParams({plan:view?.plan.id||'',view:tab,...(id?{level:id}:{}),...(from&&FROM_LABELS[from]&&from!==tab?{from}:{})});
const WORKSPACE_TASK_FIELDS=['id','title','stage','kind','status','action','optional','notes','due_date','date_kind','date_reviewed','recipient','batch','signers','waiting_for','depends_on','source_label','source_url','source_excerpt','origin','file_version_id','file_location','course'];
const cleanWorkspaceTask=t=>Object.fromEntries(WORKSPACE_TASK_FIELDS.filter(k=>k in t).map(k=>[k,t[k]]));
const hasActivePlan=()=>Boolean(view&&!plan()?.archived&&state.account);
async function saveWorkspaceTasks(nextTasks,creditGoal=view?.workspace?.credit_goal??null){
  if(!hasActivePlan()||wsSaving)return false;
  const captured=key(),run=epoch,id=plan().id;wsSaving=true;
  try{
    const saved=await fetchJson(pathUrl()+'/workspace'+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,tasks:nextTasks.map(cleanWorkspaceTask),credit_goal:creditGoal})});
    if(captured!==key()||run!==epoch||view?.plan.id!==id)return false;
    view=saved;renderApplicationCalendar();if(active)render();window.UniWayTracker?.render();return true;
  }finally{wsSaving=false;}
}
async function addPersonalTodo({title='',dueDate=''}={}){
  const cleanTitle=String(title||'').trim();if(!cleanTitle||!hasActivePlan())return false;
  const validDate=dueDate&&parseLocalDate(dueDate)?String(dueDate):null;
  const id=(window.crypto?.randomUUID?.()||'todo'+Date.now()+Math.random().toString(16).slice(2)).replaceAll('-','').slice(0,32);
  const newTask={id,title:cleanTitle.slice(0,160),stage:'departure',kind:'task',status:'todo',action:'prepare',optional:false,notes:'',due_date:validDate,date_kind:validDate?'personal':'unknown',date_reviewed:false,recipient:'',batch:'',signers:'',waiting_for:'',depends_on:[],source_label:'',source_url:'',source_excerpt:'',origin:'manual',file_version_id:null,file_location:'',course:null};
  return saveWorkspaceTasks([...(view.workspace?.tasks||[]),newTask]);
}
async function togglePersonalTodo(taskId){
  const t=(view?.workspace?.tasks||[]).find(x=>x.id===taskId);if(!t||!hasActivePlan())return false;
  const nextStatus=t.effective_status==='done'?'todo':'done';
  if(nextStatus==='done'&&t.waiting_for){toast('此任務尚有等待事項，請開啟任務清除等待原因後再完成。',true);return false;}
  return saveWorkspaceTasks((view.workspace?.tasks||[]).map(x=>x.id===taskId?{...x,status:nextStatus}:x));
}
const plan=()=>view.plan, stages=()=>view?.stages||[];
const rawLevels=()=>stages().flatMap(s=>s.levels.map(l=>({...l,stageTitle:s.title})));
// A rule the system already judged as met needs nothing from the student.
const checkOk=l=>l.check_status==='pass'||l.progress.value===l.progress.total;
// The rule checks are one step for the student (申請資格): one screen, one form, one confirmation.
function collapse(list){
  const checks=list.filter(l=>l.check_status);if(!checks.length)return list;
  const first=checks[0],fields=[...new Set(checks.flatMap(c=>c.input_fields||[]))];
  const group={id:'checks',title:'申請資格',kind:'checks',icon:'badge-check',prompt:'',warning:'',stageTitle:first.stageTitle,stage:first.stage,stage_key:first.stage_key,
    children:checks,source_urls:[...new Set(checks.flatMap(c=>c.source_urls||[]))],dependency_ids:[],blocked_by:[],counted:true,external:false,
    progress:{value:checks.filter(checkOk).length,total:checks.length},
    input_fields:fields,input_values:Object.assign({},...checks.map(c=>c.input_values||{})),missing_inputs:[...new Set(checks.flatMap(c=>c.missing_inputs||[]))]};
  return list.flatMap(l=>l===first?[group]:l.check_status?[]:[l]);
}
const levels=()=>collapse(rawLevels());
const find=id=>(id==='checks'?levels():rawLevels()).find(l=>l.id===id), record=id=>plan().steps[id]||{};
const progress=l=>l.progress, hasContent=l=>Boolean(record(l.id).value||record(l.id).version_id);
const isDone=l=>(l.counted!==false||setup(l))&&!l.external&&l.progress.value===l.progress.total;
const status=l=>l.conditional&&record(l.id).applicable===false?'skipped':l.external?(hasContent(l)?'recorded':'external'):isDone(l)?'done':l.progress.value?'started':'todo';
const missing=l=>l.blocked_by||[];
const setup=l=>['home','term','target'].includes(l.id);
const assistance=l=>['write','assemble'].includes(l.kind);
const required=l=>!setup(l)&&!assistance(l)&&!l.external&&l.counted!==false;
const confirmedDeadline=l=>Boolean(l.official_deadline_at&&l.deadline_confirmed);
const waitingOnData=l=>l.kind==='checks'&&gateBlocked(l)&&Object.keys(plan().profile||{}).length>0;
function next(){
  const available=levels().filter(l=>!l.external&&!setup(l)&&!assistance(l)&&status(l)!=='skipped'&&!isDone(l)&&!missing(l).length&&!waitingOnData(l));
  const pending=levels().filter(l=>drafts.has(draftKey(l.id))&&!missing(l).length)
    .sort((a,b)=>(drafts.get(draftKey(b.id)).editedAt||0)-(drafts.get(draftKey(a.id)).editedAt||0));
  if(pending.length)return pending[0];
  const now=Date.now(), urgent=available.filter(l=>confirmedDeadline(l)&&Date.parse(l.official_deadline_at)>=now&&Date.parse(l.official_deadline_at)-now<=14*86400000).sort((a,b)=>Date.parse(a.official_deadline_at)-Date.parse(b.official_deadline_at));
  if(urgent.length)return urgent[0];
  const unfinished=levels().filter(l=>!l.external&&!setup(l)&&!isDone(l)&&!missing(l).length&&l.kind!=='checks'&&(drafts.has(draftKey(l.id))||status(l)==='started'));
  unfinished.sort((a,b)=>(record(b.id).updated_at||'').localeCompare(record(a.id).updated_at||''));
  return unfinished.find(l=>drafts.has(draftKey(l.id)))||unfinished[0]||available[0];
}
// "Synced" is the normal state and says nothing; only a state the student should know about is written out.
function setSync(text){const el=$('#sync-message');if(!el)return;el.textContent=text;const box=el.closest('.ap-status');if(box)box.hidden=text==='已同步至帳號'||text==='已連接帳號';}
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
  const curTab=route().get('view')||'today',curFrom=FROM_LABELS[curTab]&&curTab!=='progress'?curTab:'';
  $$('a[href^="#level/"]').forEach(a=>a.href=href('level',a.getAttribute('href').slice(7),curFrom));
  $$('a[href="#map"]').forEach(a=>a.href=href('map','',curFrom));
  $$('a[href="#progress"]').forEach(a=>a.href=href('progress','',curFrom));
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
  window.UniWayExchangeWorkspace?.clear();
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
  $('#source-info').onclick=()=>{$('#source-info').closest('details')?.removeAttribute('open');$('#info-dialog').showModal();};
  $$('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());
  $('#plan-form').onsubmit=create;
  if($('#create-round'))$('#create-round').oninput=()=>{ $('#create-round').dataset.userEdited='1'; };
  $('#plan-select').onchange=e=>{location.hash='#my-application?'+new URLSearchParams({plan:e.target.value,view:'today'});};
  $('#stage-select').onchange=e=>scrollMap(stages()[Number(e.target.value)]?.levels[0]?.id);
  $('#go-origin').onclick=()=>{scrollMap(null);$('#stage-select').value='0';picker.sync();};
  $('#go-current').onclick=()=>{const n=next();if(n)location.hash=href('level',n.id,'map');};
  root.addEventListener('click',e=>{
    if(e.target.closest('[data-path-login]'))openAuthDialog();
    if(e.target.closest('[data-path-new]'))openNew();
    if(e.target.closest('[data-path-retry]'))load(true);
    if(e.target.closest('[data-open-info]'))$('#info-dialog').showModal();
    if(e.target.closest('[data-use-plan-context]')){applyPlanContext().then(ok=>{if(ok&&active&&route().get('view')==='schedule')renderSchedule();}).catch(err=>toast(err.message,true));}
    const wsToggle=e.target.closest('[data-workspace-todo-toggle]');
    if(wsToggle){togglePersonalTodo(wsToggle.dataset.workspaceTodoToggle).catch(err=>toast(err.message,true));return;}
    const calToggle=e.target.closest('[data-calendar-todo-toggle]');
    if(calToggle){if(typeof updateCalendarTaskStatus==='function')updateCalendarTaskStatus(calToggle.dataset.calendarTodoToggle,'ready');if(active&&route().get('view')==='today')renderToday();window.UniWayTracker?.render();return;}
    const restoreBtn=e.target.closest('[data-restore-plan]');if(restoreBtn)restorePlan(restoreBtn.dataset.restorePlan);
    if(e.target.closest('.ap-menu-list button'))e.target.closest('.ap-menu').open=false;
    const link=e.target.closest('#path-tool-host a[href^="#"]');
    if(link){const url=toolHref(link.getAttribute('href').slice(1));if(url){e.preventDefault();location.hash=url;}}
  });
  // History/hash navigation is also safe: show() snapshots before replacing any form.
  addEventListener('beforeunload',e=>{stash();if(drafts.size||saving){e.preventDefault();e.returnValue='';}});
  addEventListener('online',()=>{if(dirty&&active&&state.account)save(false,{quiet:true});});
  document.addEventListener('click',e=>{const m=root&&$('.ap-menu');if(m?.open&&!m.contains(e.target))m.open=false;});
  new ResizeObserver(()=>requestAnimationFrame(drawPaths)).observe($('#map-scroll'));
}
function refresh(){if(!root)return;if(owner!==key()){clear({preserveDrafts:true});owner=key();if(active)load();}}
function show(page){init();stash();window.UniWayExchangeWorkspace?.snapshot();clearTimeout(autosaveTimer);active=page==='my-application';picker.close();if(owner!==key()){clear({preserveDrafts:true});owner=key();}
  if(!active)return;
  if(!state.account){message(state.authRestoreState==='pending'?'正在確認登入狀態…':'登入後，接著完成你的申請。','<button data-path-login class="primary-button">登入並繼續</button><a href="#partners" class="quiet-button">先找交換學校</a>');if(route().get('view')==='schedule')showScheduleWithoutPlan(true);return;}
  const requested=route().get('plan');
  if(!view&&route().get('view')==='schedule'&&listing&&!listing.items.length){showScheduleWithoutPlan();return;}
  if(!view||requested&&view.plan.id!==requested){if(!loading)load();return;}
  render();maybeOpenTarget();
}
function ensureTargetPreference(targetSchool){
  if(!targetSchool||typeof state!=='object'||!(state.applications instanceof Set)||state.applications.size)return;
  state.applications.add(targetSchool);
  if(typeof persistAccountWorkspaceLocally==='function')persistAccountWorkspaceLocally();
  if(typeof scheduleAccountWorkspaceSync==='function')scheduleAccountWorkspaceSync();
}
function syncPreferences(list){
  if(typeof state!=='object'||!(state.applications instanceof Set))return;
  const clean=[];
  for(const item of (list||[])){const s=String(item||'').trim();if(s&&!clean.includes(s))clean.push(s);}
  state.applications=new Set(clean);
  if(typeof persistAccountWorkspaceLocally==='function')persistAccountWorkspaceLocally();
  if(typeof scheduleAccountWorkspaceSync==='function')scheduleAccountWorkspaceSync();
  window.UniWayTracker?.render?.();
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
    if(!selected&&route().get('view')==='schedule'){view=null;setSync('已連接帳號');showScheduleWithoutPlan();return;}
    if(!selected){view=null;setSync('已連接帳號');message('從你的交換目標開始','<a href="#partners" class="primary-button next-action">找適合的學校</a><button data-path-new class="outline-button">我已有目標</button>'+((listing.legacy?.schools||[]).length?'<a href="#my-application?view=schedule" class="quiet-button">查看時程</a>':''));maybeOpenTarget();return;}
    const data=await fetchJson('/account/application-paths/'+selected.id+query());
    if(run!==epoch||captured!==key())return;
    if(route().get('plan')!==requested){load();return;}
    view=data;dirty=false;activeId=null;
    if(!data.plan?.archived)ensureTargetPreference(data.plan?.context?.target_school);
    if(mapPositionPlan!==selected.id)mapPosition=null;
    render();maybeOpenTarget();window.UniWayTracker?.render();
  }catch(e){if(run===epoch&&captured===key()){message(e.message,'<button data-path-retry class="outline-button">重新載入</button>');}}
  finally{if(run===epoch){loading=false;$('#path-message').classList.remove('ap-loading');}}
}
function render(){
  if(!active||!view)return;
  window.UniWayApplicationWorkspace?.release();
  $('#path-message').hidden=true;
  const id=route().get('level'), rawTab=route().get('view')||'today', tab=rawTab==='progress'?'today':rawTab;
  
  $('#hub').hidden=tab==='level';$('#level-view').hidden=tab!=='level';
  setSync(plan().archived?'已封存 · 紀錄保留':'已同步至帳號');
  $('#archive-plan').hidden=false;$('#archive-plan').textContent=plan().archived?'恢復計畫':'封存計畫';
  const c=plan().context;
  $('#plan-select').innerHTML=listing.items.map(p=>'<option value="'+p.id+'" '+(p.id===plan().id?'selected':'')+'>'+esc(shortSchool(p.context.target_school)+' · '+formatContextTerm(p.context)+(p.archived?'（已封存）':''))+'</option>').join('');
  $('#plan-meta').textContent=c.home_school+' · '+c.academic_year+' 學年度 · '+planRoundLabel(c);
  const plansTab=$('[data-tab="plans"]');if(plansTab)plansTab.hidden=tab!=='plans'&&tab!=='map'&&listing.items.filter(p=>!p.archived).length<2;
  const t=totals();$('#overall-caption').textContent=t.done+' / '+t.count+' 項';$('#overall-meter').innerHTML=meter(t,'整體個人準備');
  const curFrom=FROM_LABELS[tab]?tab:'';
  const overallLink=$('#overall-progress-link');if(overallLink)overallLink.href=href('today');
  const activeTab=tab==='map'?'plans':tab;
  $$('[data-tab]').forEach(a=>{a.href=href(a.dataset.tab);a.classList.toggle('active',a.dataset.tab===activeTab);if(a.dataset.tab===activeTab)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  const rawFrom=route().get('from')||'',validFrom=FROM_LABELS[rawFrom]&&rawFrom!==tab?rawFrom:'';
  const back=$('#subview-back');
  if(tab==='map'){const bt=validFrom||'plans';back.hidden=false;back.href=href(bt);back.innerHTML=icon('arrow-left')+'回到'+FROM_LABELS[bt];}
  else if(validFrom&&['workspace','schedule'].includes(tab)){back.hidden=false;back.href=href(validFrom);back.innerHTML=icon('arrow-left')+'回到'+FROM_LABELS[validFrom];}
  else{back.hidden=true;}
  const n=next();$('#stage-select').innerHTML=stages().map(s=>'<option value="'+s.index+'" '+(n?.stage===s.index?'selected':'')+'>'+String(s.index+1).padStart(2,'0')+' · '+esc(s.title)+'</option>').join('');picker.sync();
  $('#hub').dataset.tab=tab;$('#today-view').hidden=tab!=='today';$('#plans-view').hidden=tab!=='plans';$('#schedule-view').hidden=tab!=='schedule';$('#map-tools').hidden=tab!=='map';$('#map-view').hidden=tab!=='map';$('#progress-view').hidden=tab!=='today';
  $('#exchange-workspace-view').hidden=tab!=='workspace';
  if(tab==='level'){if(!dirty||activeId!==id)renderLevel(id);}
  else if(tab==='today'){activeId=null;renderToday();renderOverview();}
  else if(tab==='plans'){activeId=null;renderPlans();}
  else if(tab==='schedule'){activeId=null;renderSchedule();}
  else if(tab==='workspace'){activeId=null;renderExchangeWorkspace();}
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
  if(l.kind==='checks')return complete?confirmChecks():false;
  if(complete&&gateBlocked(l)){error('請先在上方補齊資料並儲存，系統才能判斷這一關。');return false;}
  if(complete&&!l.external)data.confirmed=true;
  else data.confirmed=!!record(l.id).confirmed&&stepContent(data)===stepContent(record(l.id));
  const wasDone=isDone(l),before={...record(l.id)};
  stash();saving=true;$$('#save-draft,#level-form button[type=submit],#conflict-reload').forEach(b=>b.disabled=true);if($('#save-note'))$('#save-note').textContent='正在儲存…';
  try{
    const saved=await fetchJson(pathUrl()+'/steps/'+encodeURIComponent(l.id)+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,step:data})});
    if(run!==epoch||captured!==key()||view?.plan.id!==id)return false;
    const pending=drafts.get(cacheKey),unchanged=!pending||pending.version===version;
    if(unchanged)drafts.delete(cacheKey);
    view=saved;listing.revision=saved.revision;
    if(active&&activeId===l.id&&route().get('view')==='level'){
      dirty=!unchanged;
      if(complete&&unchanged){const from=route().get('from')||'';activeId=null;dirty=false;location.hash=href(FROM_LABELS[from]?from:'today');}
      else {
        if($('#save-note'))$('#save-note').textContent=unchanged?(wasDone&&!isDone(find(l.id))?'已儲存 · 修改後請重新確認':'已儲存'):'還有新修改，正在儲存…';
        const st=isDone(find(l.id))?'已完成':hasContent(find(l.id))?'進行中':'';$('.level-progress').hidden=!st;$('.level-progress strong').textContent=st;
        if(unchanged){$('#level-error').hidden=true;$('#conflict-reload').hidden=true;$('.conflict-comparison')?.remove();}
      }
      if(!unchanged)autosaveTimer=setTimeout(()=>save(false,{quiet:true}),900);
    }
    track('draft_save_result',{result:'success',kind:l.kind});
    if(!quiet){if(complete&&l.check_status&&!wasDone)toast('已確認「'+l.title+'」。',false,{label:'撤銷',run:()=>undoStep(l.id,before)});else if(complete&&!l.external&&!wasDone){const t=totals();toast('已完成「'+l.title+'」。準備進度 '+t.done+' / '+t.count,false,{label:'撤銷',run:()=>undoStep(l.id,before)});}else toast(complete?'已記錄準備成果':'草稿已儲存');}return true;
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
      if($('#save-note'))$('#save-note').textContent='尚未儲存，請重試';if(e.status===409)$('#conflict-reload').hidden=false;
    }return false;
  }finally{if(run===epoch){saving=false;$$('#save-draft,#level-form button[type=submit],#conflict-reload').forEach(b=>b.disabled=plan().archived||(b.type==='submit'&&gateBlocked(find(activeId))));}}
}
const CHECK_TEXT={pass:['符合','pass','規則比對通過，仍以校方審核為準。'],
  fail:['不符合','fail','目前條件不符合這項規則。你仍可以記下「已看過」，但這不會改變資格判斷。'],
  needs_confirmation:['待確認','needs','系統還無法判斷。先補齊你的條件，或向承辦單位確認。']};
const CHECK_STANDARD=new Set(['規則比對通過，仍以校方審核為準。','目前條件不符合此項規則；個人確認不會改變資格判斷。','資料或個人條件待確認。']);
function checkStatus(l){const c=CHECK_TEXT[l.check_status];return c?'<p class="check-status '+c[1]+'" role="status"><b>'+c[0]+'</b>'+esc(c[2])+'</p>':'';}
// A gate that cannot be judged says what it lacks and lets the student supply it here, then judges again.
const YEARS=['大一','大二','大三','大四','碩士班','博士班'];
const GATE_FIELDS={
  college:{label:'學院',type:'text',hint:'例如：管理學院'},
  department:{label:'學系',type:'text',hint:'例如：資訊管理學系'},
  degree_level:{label:'學制',type:'select',options:[['大學部'],['碩士班'],['博士班'],['研究所','研究所（尚未區分碩博士）']]},
  current_year:{label:'年級',type:'select',options:YEARS.map(y=>[y])},
  academic_score:{label:'學業平均',type:'number',min:0,max:100,hint:'例如 82'},
  academic_gpa:{label:'適用學年 GPA（4.3 制）',type:'number',min:0,max:4.3,hint:'例如 2.44；與排名擇一'},
  class_rank_percent:{label:'適用學年班排名（前幾 %）',type:'number',min:0.01,max:100,hint:'例如前 30% 填 30'},
  language_test:{label:'語言測驗',type:'select',options:[['toeic','TOEIC'],['ielts','IELTS Academic'],['toefl','TOEFL iBT（舊制 120 分）'],['toefl_new','TOEFL iBT（新制 6 分）'],['duolingo','Duolingo'],['other','其他']]},
  language_score:{label:'語言分數',type:'number',min:0,max:1000,hint:'尚未考請留空'},
  jlpt_level:{label:'JLPT 級別',type:'select',options:['N1','N2','N3','N4','N5'].map(n=>[n])},
  application_round:{label:'申請梯次',type:'select',options:[['第一梯次'],['第二梯次'],['其他／尚未公告']]}
};
// Where the same condition already lives in 我的條件, so it can be offered instead of typed again.
const GLOBAL_KEY={college:'college',department:'department',degree_level:'degree',current_year:'currentYear',academic_score:'academicScore',academic_gpa:'academicGpa',class_rank_percent:'classRankPercent',language_test:'languageTest',language_score:'languageScore',jlpt_level:'jlptLevel',application_round:'applicationRound'};
const GATE_TITLE={checks:'你的條件',college:'補上你的學院與學系',degree_level:'補上你的學制與年級',partner_degree_level:'補上你的學制與年級',home_year:'補上你的年級',home_language_score:'補上你的語言成績',language_score:'補上你的語言成績',application_round:'選擇你要申請的梯次',academic_score:'補上你的學業成績',academic_gpa:'補上你的學業成績'};
const gateBlocked=l=>!!l&&(l.kind==='confirm'||l.kind==='checks')&&(l.missing_inputs||[]).length>0;
function gateValue(l,key){
  const saved=l.input_values?.[key];
  if(saved!==null&&saved!==undefined&&saved!=='')return {value:saved,offered:false};
  const global=state.eligibilityProfile?.[GLOBAL_KEY[key]];
  return global===null||global===undefined||global===''?{value:'',offered:false}:{value:global,offered:true};
}
function gateControl(l,key){
  const d=GATE_FIELDS[key],{value}=gateValue(l,key),id='gate-'+key,lacking=(l.missing_inputs||[]).includes(key);
  const attrs=' id="'+id+'" name="'+key+'"'+(lacking?' data-missing="true" aria-required="true"':'');
  let control;
  if(d.type==='select'){
    const options=d.options.slice();
    if(value!==''&&!options.some(o=>o[0]===String(value)))options.unshift([String(value)]);
    control='<select'+attrs+'><option value="">尚未提供</option>'+options.map(o=>'<option value="'+esc(o[0])+'"'+(String(value)===o[0]?' selected':'')+'>'+esc(o[1]||o[0])+'</option>').join('')+'</select>';
  }else if(d.type==='number'){
    control='<input type="number"'+attrs+' inputmode="decimal" min="'+d.min+'" max="'+d.max+'" step="any" placeholder="'+esc(d.hint||'')+'" value="'+esc(value)+'">';
  }else control='<input type="text"'+attrs+' maxlength="120" autocomplete="off" placeholder="'+esc(d.hint||'')+'" value="'+esc(value)+'">';
  return '<label for="'+id+'"><span>'+esc(d.label)+'</span>'+control+'</label>';
}
function gateInputs(l){
  const fields=(l.input_fields||[]).filter(k=>GATE_FIELDS[k]);
  if(!fields.length)return '';
  const lacking=(l.missing_inputs||[]).length>0;
  const body='<div class="gate-grid">'+fields.map(k=>gateControl(l,k)).join('')+'</div><p id="gate-error" class="error-box" role="alert" hidden></p>'+
    '<div class="gate-actions"><button type="button" id="gate-save" class="primary-button">儲存並判斷</button></div>';
  const title=GATE_TITLE[(l.id||'').replace(/^check-/,'')]||'補上需要的資料';
  return lacking?'<fieldset id="gate-inputs" class="gate-inputs" data-state="missing"><legend>'+esc(title)+'</legend>'+body+'</fieldset>':
    '<details class="gate-details"><summary>我填的資料（可修改）'+icon('chevron-down')+'</summary><fieldset id="gate-inputs" class="gate-inputs" data-state="given"><legend>'+esc(title)+'</legend>'+body+'</fieldset></details>';
}
function gateValues(l){return Object.fromEntries((l.input_fields||[]).map(k=>[k,$('#gate-'+k)?.value??'']));}
function gateError(text,control=null){
  const el=$('#gate-error');if(!el)return;
  el.hidden=false;el.textContent=text;
  (control||el).focus?.();
}
async function saveGate(){
  const l=find(activeId);if(!l||!view||saving||plan().archived||!$('#gate-inputs'))return;
  const body={revision:view.revision};
  for(const key of l.input_fields||[]){
    const input=$('#gate-'+key),d=GATE_FIELDS[key];if(!input)continue;
    const raw=input.value.trim();
    if(d.type==='number'&&raw!==''){
      const n=Number(raw);
      if(!Number.isFinite(n)||n<d.min||n>d.max){gateError(d.label+'需要介於 '+d.min+' 到 '+d.max+' 之間。',input);return;}
      body[key]=n;
    }else body[key]=raw;
  }
  const given=(l.input_fields||[]).filter(k=>body[k]!==undefined&&body[k]!=='');
  if(!given.length&&gateBlocked(l)){gateError('請先填寫至少一項資料，系統才能判斷這一關。',$('#gate-'+l.input_fields[0]));return;}
  const run=epoch,captured=key(),id=plan().id,button=$('#gate-save');
  $('#gate-error').hidden=true;button.disabled=true;button.textContent='正在判斷…';saving=true;
  try{
    const saved=await fetchJson(pathUrl()+'/profile'+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(run!==epoch||captured!==key()||view?.plan.id!==id)return;
    view=saved;listing.revision=saved.revision;saving=false;
    track('gate_input_saved',{check:l.id,result:find(l.id)?.check_status||''});
    if(!active||activeId!==l.id||route().get('view')!=='level')return;
    renderLevel(l.id);
    const after=find(l.id);
    $('.check-status')?.setAttribute('tabindex','-1');$('.check-status')?.focus();
    toast(l.kind==='checks'?(isDone(after)?'已儲存。申請資格全部符合。':'已儲存，已重新判斷。'):after?.check_status==='pass'?'已儲存。這一關現在判斷為「符合」。':after?.check_status==='fail'?'已儲存。這一關現在判斷為「不符合」。':'已儲存。系統仍無法判斷，請向承辦單位確認。');
  }catch(e){
    if(run!==epoch||captured!==key())return;
    saving=false;
    if(e.status===409){
      // Another tab saved first: take its state, keep what was typed, and let the student press save again.
      const typed=gateValues(l);
      try{
        const latest=await fetchJson(pathUrl()+query());
        if(run!==epoch||captured!==key()||view?.plan.id!==id)return;
        view=latest;listing.revision=latest.revision;renderLevel(l.id);
        for(const [k,v] of Object.entries(typed)){const input=$('#gate-'+k);if(input)input.value=v;}
        gateError('其他分頁已更新這份計畫。你填的內容還在，請再按一次儲存。');
      }catch(err){gateError(err.message);}
      return;
    }
    if(!$('#gate-error'))return;
    button.disabled=false;button.textContent='儲存並判斷';
    gateError(e.message);
  }finally{if(run===epoch)saving=false;}
}
// One confirmation covers every rule the system could not mark as met by itself.
async function confirmChecks(){
  const g=find('checks');if(!g||saving||!view||plan().archived)return false;
  if(gateBlocked(g)){error('請先填好上方資料並儲存，系統才能判斷。');return false;}
  const run=epoch,captured=key(),id=plan().id,buttons=()=>$$('#level-form button');
  saving=true;buttons().forEach(b=>b.disabled=true);
  try{
    for(const c of g.children.filter(c=>!checkOk(c))){
      const saved=await fetchJson(pathUrl()+'/steps/'+encodeURIComponent(c.id)+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:view.revision,step:{value:'',confirmed:true,version_id:null,applicable:null}})});
      if(run!==epoch||captured!==key()||view?.plan.id!==id)return false;
      view=saved;listing.revision=saved.revision;
    }
    const t=totals(),from=route().get('from')||'';
    toast('已完成「申請資格」。準備進度 '+t.done+' / '+t.count);
    activeId=null;location.hash=href(FROM_LABELS[from]?from:'today');
    return true;
  }catch(e){
    if(run===epoch&&captured===key()){buttons().forEach(b=>b.disabled=false);error(e.status===409?'其他分頁已更新這份計畫，請重新載入後再試。':e.message);}
    return false;
  }finally{if(run===epoch)saving=false;}
}
function wireGate(){
  const box=$('#gate-inputs');if(!box)return;
  // These fields are not the step's own text: they must not start the step autosave or submit the form.
  box.addEventListener('input',e=>{e.stopPropagation();if($('#gate-error'))$('#gate-error').hidden=true;});
  box.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.matches('input')){e.preventDefault();saveGate();}});
  $('#gate-save').onclick=saveGate;
}
function renderGuideSummary(l){
  const g=l.guide_summary;if(!g)return '';
  const docs=(g.required_documents||[]).map(d=>'<li><strong>'+esc(d.title)+'</strong><span>'+esc(d.desc)+'</span></li>').join('');
  const links=(g.official_links||[]).map(x=>'<a class="outline-button" href="'+esc(x.url)+'" target="_blank" rel="noopener noreferrer">'+esc(x.label)+icon('arrow-up-right')+'</a>').join('');
  return '<section class="cgu-guide-summary" aria-label="校內申請須知重點摘要">'+
    '<div class="cgu-guide-head"><h3>重點摘要</h3><span class="cgu-guide-term">'+esc(g.term_label||g.term_code||'')+'</span></div>'+
    '<dl class="cgu-guide-meta-grid">'+
      '<div><dt>校內申請期間</dt><dd>'+esc(g.application_period||'依國際處公告')+'</dd></div>'+
      '<div><dt>校內申請截止</dt><dd>'+esc(g.deadline||'依國際處公告')+'</dd></div>'+
      '<div><dt>志願數上限</dt><dd>'+esc(g.preference_limit||'')+'</dd></div>'+
      '<div><dt>基本申請門檻</dt><dd>'+esc(g.eligibility_summary||'')+'</dd></div>'+
    '</dl>'+
    (docs?'<div class="cgu-guide-docs"><h4>校內應備 5 份文件</h4><ol class="cgu-guide-doc-list">'+docs+'</ol></div>':'')+
    (links?'<div class="cgu-guide-links">'+links+'</div>':'')+
  '</section>';
}
function field(l,r){
  if(l.kind==='checks')return '<ul class="check-list">'+l.children.map(c=>{const k=CHECK_TEXT[checkOk(c)&&c.check_status!=='fail'?'pass':c.check_status]||CHECK_TEXT.needs_confirmation;
    return '<li class="'+k[1]+'" data-check="'+esc(c.id)+'"><b>'+k[0]+'</b><div><strong>'+esc(c.title)+'</strong><p>'+esc(c.prompt)+'</p></div>'+(urls(c)[0]?'<a href="'+esc(urls(c)[0])+'" target="_blank" rel="noopener noreferrer" aria-label="'+esc(c.title)+'的官方來源">官方來源'+icon('arrow-up-right')+'</a>':'')+'</li>';}).join('')+'</ul>'+gateInputs(l);
  if(l.kind==='confirm')return checkStatus(l)+gateInputs(l)+renderGuideSummary(l)+'<div class="choice-box">'+icon(l.icon)+'<strong>'+esc(l.prompt)+'</strong></div>';
  if(l.kind==='assemble')return '<div class="document-preview">'+levels().filter(x=>x.kind==='write').map(x=>'<section><h3>'+esc(x.title)+'</h3><p>'+esc(record(x.id).value||'尚未填寫')+'</p><a href="'+href('level',x.id)+'">編輯這一段</a></section>').join('')+'</div><button type="button" id="download-writing" class="outline-button">'+icon('download')+'下載文字草稿</button><a class="outline-button" href="'+pathUrl()+'/writing.docx'+query()+'">'+icon('file-down')+'下載 Word 草稿</a>';
  return (l.conditional?'<label for="file-applicable">這份條件式文件適用於你嗎？</label><select id="file-applicable"><option value="">待確認（暫不計入進度）</option><option value="yes" '+(r.applicable===true?'selected':'')+'>適用</option><option value="no" '+(r.applicable===false?'selected':'')+'>不適用</option></select>':'')+(l.external?'<div class="external-notice">學生自行記錄，不代表校方確認。</div>':'')+
    (l.kind==='submission'?'<p class="small-warning">請在官方系統送件；UniWay 不代送申請。</p>':'')+
    (l.kind==='file'?'<label for="file-version">連結私人文件</label><select id="file-version"><option value="">自行保管（在下方記錄位置）</option>'+(r.version_id?'<option selected value="'+esc(r.version_id)+'">'+esc(r.file_name||'已連結文件')+'</option>':'')+'</select><button type="button" id="load-files" class="quiet-button">'+icon('folder-open')+'選擇我的文件</button><details class="ap-upload"><summary>上傳到私人文件庫</summary><label for="path-file">選擇檔案</label><input type="file" id="path-file"><label class="check-row"><input type="checkbox" id="file-consent"><span>同意加密保存 30 天，用於申請準備；可在私人文件庫撤回。</span></label><button type="button" id="upload-file" class="outline-button">上傳並連結</button></details>':'')+
    '<label for="level-input">'+(l.kind==='write'?'你的想法':l.external?'通知內容':'備註（選填）')+'</label><textarea id="level-input" maxlength="20000">'+esc(r.value||'')+'</textarea>';
}
function renderLevel(id){
  window.UniWayApplicationWorkspace?.release();
  const l=find(id);if(!l){location.hash=href();return;}
  activeId=id;const cached=draftOwner===state.account?.id?drafts.get(draftKey(id)):null;dirty=!!cached;const r=cached?.step||record(id),c=plan().context;
  mapPosition=$('#map-scroll').scrollTop;mapPositionPlan=plan().id;
  const dependencies=missing(l),draftable=hasDraftInput(l),isNoticePanel=l.cgu_level_type==='oia_notice'||l.cgu_level_type==='partner_notice';
  const rawFrom=route().get('from')||'',backTab=FROM_LABELS[rawFrom]?rawFrom:'today';
  const noteText=gateBlocked(l)&&l.kind!=='checks'?'補齊上方資料後，才能確認這一關':dirty?'已恢復未儲存內容':'';
  const supportInner=(l.guide_summary||l.kind==='checks'||(!urls(l).length&&l.kind!=='confirm')?'':'<details class="source-details"><summary>官方來源'+icon('chevron-down')+'</summary>'+(l.kind==='confirm'?'<p>'+esc(l.prompt)+'</p>':'')+urls(l).map((u,i)=>'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">'+(i?'相關官方文件':'官方來源')+icon('arrow-up-right')+'</a>').join('')+'</details>')+(l.official_deadline_at?'<p class="ap-deadline">'+(confirmedDeadline(l)?'官方期限：':'參考日期（待核對）：')+esc(new Date(l.official_deadline_at).toLocaleString('zh-TW',{timeZone:'Asia/Taipei'}))+'（臺灣時間）'+(new Date(l.official_deadline_at)<new Date()?'（已過期）':'')+'</p>':'')+(l.action_url&&/^https?:\/\//i.test(l.action_url)?'<a class="outline-button" href="'+esc(l.action_url)+'" target="_blank" rel="noopener noreferrer">開啟官方表格'+icon('external-link')+'</a>':'')+(l.kind==='submission'&&urls(l).length?'<a class="outline-button" href="'+esc(urls(l)[0])+'" target="_blank" rel="noopener noreferrer">校方公告與入口'+icon('external-link')+'</a>':'');
  const progressHtml=isNoticePanel?'<div class="level-progress"><div><span>通知狀態</span><strong>'+esc(r.value||(l.cgu_level_type==='oia_notice'?'待國際處更新':'待合作校通知'))+'</strong></div></div>':'<div class="level-progress" data-s="'+(isDone(l)?'done':'started')+'"'+(isDone(l)||hasContent(l)||(l.kind==='checks'&&l.progress.value)?'':' hidden')+'><strong>'+(isDone(l)?'已完成':l.kind==='checks'?l.progress.value+' / '+l.progress.total+' 項符合':'進行中')+'</strong></div>';
  $('#level-view').innerHTML='<div class="level-topline"><a class="back-link" href="'+href(backTab)+'">'+icon('arrow-left')+'回到'+FROM_LABELS[backTab]+'</a><span class="level-plan-name">'+esc(shortSchool(c.target_school)+' · '+formatContextTerm(c))+'</span></div><div class="level-layout"><div class="level-card"><div class="level-heading"><span class="square-icon">'+icon(l.icon)+'</span><h2 id="level-title" tabindex="-1">'+esc(l.title)+'</h2>'+progressHtml+'</div>'+
    '<form id="level-form"><div class="level-body">'+(l.kind==='confirm'||l.kind==='checks'||!l.prompt?'':'<p class="task-question">'+esc(l.prompt)+'</p>')+(l.warning&&l.warning!==l.prompt&&!(l.check_status&&CHECK_STANDARD.has(l.warning))?'<p class="ap-warning">'+esc(l.warning)+'</p>':'')+field(l,r)+(dependencies.length?'<div class="small-warning">先完成以下前置事項：'+dependencies.map(k=>'<a href="'+href('level',k)+'">'+esc(find(k)?.title||'前置資料尚未取得')+'</a>').join('')+'</div>':'')+'<p id="level-error" class="error-box" role="alert" hidden></p><button type="button" id="conflict-reload" class="outline-button" hidden>保留輸入並載入最新進度</button></div><footer class="level-actions"><span id="save-note" role="status">'+esc(noteText)+'</span>'+(draftable?'<button type="button" id="save-draft" class="outline-button">儲存草稿</button>':'')+(l.kind==='checks'&&gateBlocked(l)?'':l.kind==='checks'&&isDone(l)?'<a class="primary-button" href="'+href(backTab)+'">回到'+FROM_LABELS[backTab]+icon('arrow-right')+'</a>':'<button type="submit" class="primary-button" '+(plan().archived||gateBlocked(l)?'disabled':'')+'>'+esc(completeLabel(l))+icon('check')+'</button>')+'</footer></form>'+'</div><aside class="level-support">'+(supportInner?'<section class="support-card">'+supportInner+'</section>':'')+'</aside></div>';
  {
    $('#level-form').oninput=edit;
    $('#level-form').onsubmit=e=>{e.preventDefault();save(true);};
    if($('#save-draft'))$('#save-draft').onclick=()=>save(false);
    wireGate();
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
  renderTools(l);
  icons();
  if(!route().get('tool'))requestAnimationFrame(()=>$('#level-title')?.focus({preventScroll:true}));
  if(cached)track('draft_resume_result',{result:'restored',kind:l.kind});
}
const embeddedTools=new Set(['advisor','favorites','eligibility','application-center','document-check','documents','writing-assistant']);
function toolHref(tool){
  if(!active||!view||route().get('view')!=='level'||!find(route().get('level')))return null;
  if(!embeddedTools.has(tool)&&!/^application-form=[\w%-]+$/.test(tool))return null;
  try{decodeURIComponent(tool);}catch{return null;}
  return href('level',route().get('level'),route().get('from')||'')+'&'+new URLSearchParams({tool});
}
function formToolActive(){return active&&route().get('view')==='level'&&(route().get('tool')||'').startsWith('application-form=');}
async function selectTarget(schoolName){
  if(!toolHref('advisor')||schoolName===plan().context.target_school)return false;
  await openNew(schoolName);
  return true;
}
function toolsFor(l){
  const isCgu=Boolean(window.cguDemoStorageIsolated)||activeHomeSchool()==='長庚大學';
  if(isCgu){
    if(l.id==='home')return {links:[],showSchedule:false};
    if(l.id==='term')return {links:[],showSchedule:true};
    if(l.id==='target'||l.id==='cgu-shortlist')return {links:[['advisor','sliders-horizontal','條件與推薦'],['favorites','heart','收藏與比較']],showSchedule:false};
    if(l.id==='cgu-read-guide')return {links:[['#scholarships','award','查看出國補助'],['#ask-oia','message-circle-question','問國際處']],showSchedule:true};
    if(l.id.startsWith('check-'))return {links:[['advisor','sliders-horizontal','修改我的條件']],showSchedule:false};
    if(l.id==='cgu-doc-parent_consent')return {links:[['application-form=guardian-consent','file-pen-line','家長同意書整理與列印']],showSchedule:false};
    if(l.id==='cgu-doc-study_plan')return {links:[['application-form=study-plan','file-pen-line','分段欄位輔助產出列印版']],showSchedule:false};
    if(['cgu-doc-online_form','cgu-doc-language_proof','cgu-doc-transcript','cgu-internal-result','cgu-interview'].includes(l.id))return {links:[['#ask-oia','message-circle-question','問國際處']],showSchedule:false};
    if(l.id==='cgu-partner-instructions')return {links:[['#partners','globe','查看合作校資訊']],showSchedule:true};
    if(l.id==='cgu-housing-insurance')return {links:[['application-form=overseas-affidavit','file-pen-line','出國研修切結書整理']],showSchedule:false};
    if(l.id==='cgu-courses')return {links:[['application-form=course-preapproval','file-pen-line','課程預選與抵免整理']],showSchedule:false};
    return {links:[],showSchedule:false};
  }
  if(['home','term','target'].includes(l.id))return {links:[['advisor','sliders-horizontal','條件與推薦'],['favorites','heart','收藏與比較'],['eligibility','badge-check','資格與志願']],showSchedule:true};
  if(l.id.includes('shortlist')||(l.kind==='note'&&/選校|志願/.test(l.title)))return {links:[['advisor','sliders-horizontal','條件與推薦'],['favorites','heart','收藏與比較'],['eligibility','badge-check','核對資格與志願']],showSchedule:true};
  if(l.id.startsWith('check-')||(l.kind==='note'&&/資格|語組/.test(l.title)))return {links:[['eligibility','badge-check','核對資格與志願'],['advisor','sliders-horizontal','修改我的條件']],showSchedule:true};
  const templates=(l.templates||[]).map(id=>['application-form='+encodeURIComponent(id),'file-pen-line',applicationTemplateById(id)?.name||'填寫相關表格']);
  return {links:[...templates,['application-center','files','填表與列印'],['document-check','scan-line','檢查文件'],['documents','folder-lock','文件庫']],showSchedule:true};
}
function renderTools(l){
  const {links,showSchedule}=toolsFor(l),tool=route().get('tool')||'';
  if(!links.length&&!showSchedule&&!toolHref(tool))return;
  const section=document.createElement('section');section.className='path-level-tools';
  const navHtml=links.map(([page,i,title])=>{
    const h=page.startsWith('#')?page:toolHref(page);
    return h?'<a class="outline-button" href="'+esc(h)+'"'+(page===tool?' aria-current="page"':'')+'>'+icon(i)+esc(title)+'</a>':'';
  }).join('')+(showSchedule?'<a class="quiet-button" href="#my-application?view=schedule">'+icon('calendar-clock')+'時程</a>':'');
  section.innerHTML='<nav aria-label="這一關的工具">'+navHtml+'</nav><div id="path-tool-panel" hidden><header class="path-tool-heading"><span id="path-tool-scope"></span><a class="quiet-button" href="'+href('level',l.id)+'">收合工具'+icon('x')+'</a></header><div id="path-tool-host"></div></div>';
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
    $('#path-tool-host').innerHTML='<div class="path-context-gate"><p>使用 '+esc(c.target_school)+' · '+esc(c.academic_year)+' · '+esc(formatContextTerm(c))+' 的文件規則</p><button id="path-use-context" class="primary-button">載入本計畫的文件工具</button><p id="path-tool-error" role="alert"></p></div>';
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
  if(window.UniWayExchangeWorkspace?.hasDrafts()||window.UniWayExchangeWorkspace?.isSaving()){toast('請先保存準備工作台的內容，再封存計畫。',true);return;}
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
    $('#create-round').dataset.userEdited='';
    $('#import-existing').checked=false;buildSemesterChoices(old);
    $('#plan-dialog').showModal();
  }catch(e){if(captured===key())toast(e.message,true);}
}
async function create(e){
  e.preventDefault();if(creating)return;
  if(!$('#create-departure').value){$('#create-error').textContent='請選擇預計出發學期。';$('#create-error').hidden=false;return;}creating=true;const captured=key(),run=epoch,button=$('#plan-form button[type=submit]');button.disabled=true;
  const payload={revision:listing?.revision||0,home_school:activeHomeSchool(),target_school:$('#create-target').value,academic_year:$('#create-year').value,application_round:$('#create-round').value,departure_year:$('#create-departure').value,semester:$('#create-term').value,college:$('#create-college').value,department:$('#create-department').value,degree_level:$('#create-degree').value,import_existing:$('#import-existing').checked};
  if(!payload.application_round&&(Boolean(window.cguDemoStorageIsolated)||activeHomeSchool()==='長庚大學'))payload.application_round=defaultRoundFor('長庚大學',payload.academic_year,payload.departure_year,payload.semester);
  try{const saved=await fetchJson('/account/application-paths',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(captured!==key()||run!==epoch)return;
    ensureTargetPreference(saved.plan?.context?.target_school);
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
      return '<div class="level-stop" data-stop="'+l.id+'" style="left:'+x+'%;bottom:'+(122+i*152)+'px"><a class="node '+st+' '+(isCurrent?'current ':'')+(locked?'locked':'')+'" href="#level/'+l.id+'" aria-label="'+esc(label)+'" '+(isCurrent?'aria-current="step"':'')+'>'+(isCurrent?'<span class="current-flag">繼續</span>':'')+icon(st==='done'?'check':locked?'lock-keyhole':l.icon)+'<span class="node-order" aria-hidden="true">'+level.number+'</span></a><span class="node-title">'+esc(l.title)+'</span><div class="node-progress">'+meter(p,l.title+(l.external?'紀錄進度':'進度'),{small:true,gold:st==='done',animate:isCurrent&&p.value>0})+'</div><span class="node-caption">'+(l.external?(l.id.startsWith('cgu-')?(p.value?'已同步狀態':'待通知'):(p.value?'自行記錄':'等待通知')):st==='skipped'?'不適用':l.conditional&&l.counted===false?'待確認適用性':p.value+' / '+p.total+' 步')+'</span></div>';
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
  const isCgu=Boolean(window.cguDemoStorageIsolated)||activeHomeSchool()==='長庚大學';
  const options=semesterChoices().map(o=>{
    const roc=rocYear(o.year,o.term);
    return {...o,label:isCgu?o.year+' '+(o.term==='fall'?'秋季（'+roc+'-1）':'春季（'+roc+'-2）'):o.year+' 年'+(o.term==='fall'?'秋季出發（上學期）':'春季出發（下學期）')};
  });
  const fall=options.find(o=>o.term==='fall');
  const fallRoc=rocYear(fall.year,'fall');
  options.push({year:fall.year,term:'full_year',label:isCgu?fall.year+' 秋季・全學年（'+fallRoc+'-1）':fall.year+' 年秋季出發・全學年'},{year:fall.year,term:'undecided',label:'還沒決定'});
  const keyOf=o=>o.term+':'+o.year;
  const match=options.find(o=>String(o.year)===String(old.departure_year||'')&&o.term===(old.semester||''))||(isCgu?(options.find(o=>o.year===2027&&o.term==='fall')||options.find(o=>o.term==='fall')||options[0]):options[0]);
  $('#create-semesters').innerHTML=options.map(o=>'<label class="ap-semester-option"><input type="radio" name="create-semester" value="'+keyOf(o)+'" required '+(o===match?'checked':'')+'><span>'+esc(o.label)+'</span></label>').join('');
  let lastAutoRound=$('#create-round')?.value||'';
  const apply=()=>{
    const picked=options.find(o=>keyOf(o)===($('#create-semesters input:checked')?.value||''));
    if(!picked){$('#create-year').value='';$('#create-departure').value='';$('#create-term').value='undecided';$('#create-derived').textContent='';return;}
    const roc=rocYear(picked.year,picked.term);
    $('#create-year').value=String(roc);$('#create-departure').value=String(picked.year);$('#create-term').value=picked.term;
    const roundEl=$('#create-round');
    if(roundEl){
      const cur=roundEl.value.trim();
      const autoRound=isCgu?defaultRoundFor('長庚大學',roc,picked.year,picked.term):'';
      const userEdited=roundEl.dataset.userEdited==='1';
      if(isCgu&&(!userEdited||!cur||cur===lastAutoRound||roundConflictsWithContext(cur,roc,picked.term))){
        roundEl.value=autoRound;
        lastAutoRound=autoRound;
        roundEl.dataset.userEdited='';
      }else if(!isCgu&&!userEdited&&roundConflictsWithContext(cur,roc,picked.term)){
        roundEl.value='';
      }
    }
    $('#create-derived').textContent=picked.term==='undecided'?'先以 '+roc+' 學年度規劃，決定後可新增正式的計畫。':'對應 '+roc+' 學年度的申請，實際日期以學校公告為準。';
  };
  $('#create-semesters').onchange=apply;apply();
}

// ---- numbers for any loaded plan (the 計畫 view compares several) ----
function statsFor(data){
  const steps=data.plan.steps||{},rec=id=>steps[id]||{};
  const all=collapse(data.stages.flatMap(s=>s.levels.map(l=>({...l,stageTitle:s.title}))));
  const req=l=>!['home','term','target'].includes(l.id)&&!['write','assemble'].includes(l.kind)&&!l.external&&l.counted!==false;
  const done=l=>l.counted!==false&&!l.external&&l.progress.value===l.progress.total;
  const counted=all.filter(req),finished=counted.filter(done);
  const deadline=all.filter(l=>l.official_deadline_at&&l.deadline_confirmed&&!l.external&&!done(l)&&rec(l.id).applicable!==false).sort((a,b)=>a.official_deadline_at.localeCompare(b.official_deadline_at))[0];
  const stageOrder=[...new Set(counted.map(l=>l.stageTitle))];
  const stage=stageOrder.find(t=>counted.filter(l=>l.stageTitle===t).some(l=>!done(l)));
  return {done:finished.length,total:counted.length,deadline,stage:stage||'',files:counted.filter(l=>l.kind==='file'),missingFiles:counted.filter(l=>l.kind==='file'&&!done(l)),next:counted.find(l=>!done(l)&&!(l.blocked_by||[]).length)};
}
const shortSchool=name=>String(name||'').split(/[（(]/)[0].replace(/\s+[A-Za-z].*$/,'').trim()||String(name||'');
const planName=p=>shortSchool(p.context.target_school);
const planTerm=p=>formatContextTerm(p.context);
function deadlineTimePart(when){
  const hm=when.toLocaleTimeString('zh-TW',{timeZone:'Asia/Taipei',hour:'2-digit',minute:'2-digit',hour12:false});
  return hm&&hm!=='00:00'?' '+hm:'';
}
function deadlineText(d){
  if(!d)return '尚未公布';
  const when=new Date(d.official_deadline_at),left=Math.ceil((when-Date.now())/86400000);
  return when.toLocaleDateString('zh-TW',{timeZone:'Asia/Taipei',month:'numeric',day:'numeric'})+deadlineTimePart(when)+(when<new Date()?'（已過期）':left<=0?'（今天）':'（還有 '+left+' 天）');
}
const planLink=(tab,planId,id='',from='')=>'#my-application?'+new URLSearchParams({plan:planId,view:tab,...(id?{level:id}:{}),...(from&&FROM_LABELS[from]&&from!==tab?{from}:{})});
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
      row('下一步',x=>x.s.next?'<a href="'+planLink('level',x.p.id,x.s.next.id,'plans')+'">'+esc(x.s.next.title)+'</a>':'—')+'</tbody></table>';
    const counts=new Map();ok.forEach(x=>new Set(x.s.files.map(l=>l.title)).forEach(t=>counts.set(t,(counts.get(t)||0)+1)));
    const shared=[...counts].filter(([,n])=>n===ok.length).map(([t])=>t);
    if(shared.length)compare+='<p class="plan-shared">'+icon('info')+'<span><b>每份計畫都需要 '+shared.length+' 份相同名稱的文件：</b>'+esc(shared.slice(0,4).join('、'))+(shared.length>4?' 等':'')+'。各計畫分開記錄，備妥後請在每份計畫都標記。</span></p>';
  }
  host.innerHTML='<div class="plans"><div class="plan-cards">'+ok.map(card).join('')+failed.join('')+'</div>'+compare+
    '<div class="plan-links"><a class="today-link" href="'+href('progress','','plans')+'">'+icon('list-checks')+'完整準備清單</a><a class="today-link" href="'+href('map','','plans')+'">'+icon('route')+'申請路徑地圖</a><button type="button" class="today-text" data-path-new>'+icon('plus')+'新增計畫</button></div>'+
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
    (list.length?'<ol>'+list.map(l=>{const d=new Date(l.official_deadline_at),left=Math.ceil((d-Date.now())/86400000);return '<li><a href="'+href('level',l.id,'schedule')+'"><span class="sched-date"><b>'+fmt(d,{month:'numeric',day:'numeric'})+'</b><small>'+fmt(d,{weekday:'short'})+deadlineTimePart(d)+'</small></span><span class="today-row"><b>'+esc(l.title)+'</b><small>'+esc(l.stageTitle)+'</small></span><span class="today-pill '+(d<new Date()?'late':left<=14?'soon':'')+'">'+(d<new Date()?'已過期':left<=0?'今天':'還有 '+left+' 天')+'</span></a></li>';}).join('')+'</ol>':
      '<p class="today-empty">目前沒有已確認的期限。</p>'+(source?'<a class="today-link" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">查看官方公告'+icon('arrow-up-right')+'</a>':''))+'</section>';
  icons();
}

function cohortContext(){
  const c=plan().context,label=formatContextTerm(c);
  return {title:('【'+label+'同梯】'+c.target_school).slice(0,120),prefix:'交換目的校：'+c.target_school+'\n出發學期：'+label+'\n\n'};
}
function renderExchangeWorkspace(){
  window.UniWayExchangeWorkspace.mount($('#exchange-workspace-view'),{
    get:()=>view,render,
    save:async payload=>{
      const captured=key(),run=epoch,id=plan().id;
      const saved=await fetchJson(pathUrl()+'/workspace'+query(),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      if(captured!==key()||run!==epoch||view?.plan.id!==id)throw new Error('目前已切換帳號或計畫，請回原計畫查看保存結果。');
      view=saved;renderApplicationCalendar();window.UniWayTracker?.render();
    },
    peers:async()=>{
      const c=cohortContext(),rows=await fetchJson('/community/posts?'+new URLSearchParams({board_id:'public-study-abroad',topic:'pre_departure',q:c.title.slice(0,80),limit:'120'}));
      return rows.map(r=>r.post).filter(p=>p.title===c.title&&p.body.startsWith(c.prefix)).map(p=>({...p,url:'/?'+new URLSearchParams({discussion:p.id})+'#public-board'}));
    },
    postPeer:async body=>{
      const captured=key(),c=cohortContext();
      await ensureAnonymousIdentity();
      if(captured!==key())throw new Error('登入狀態已改變，請重新確認後發布。');
      return submitCommunityJson('/community/posts',{board_id:'public-study-abroad',post_type:'discussion',topic:'pre_departure',title:c.title,body:c.prefix+body,identity_mode:'anonymous'});
    }
  });
}
// Tasks of the open plan for the list on 時程: what is in progress, the next few that can start, and what is done.
function workbenchTotals(){if(!view||plan().archived)return null;const t=totals(),own=(view.workspace?.tasks||[]).filter(x=>!x.optional);return {done:t.done+own.filter(x=>x.effective_status==='done').length,total:t.count+own.length};}
function workspaceCalendarEvents(){
  if(!view||plan().archived||owner!==key())return [];
  return (view.workspace?.tasks||[]).filter(t=>t.due_date).map(t=>({
    id:'workspace-'+plan().id+'-'+t.id,title:t.title,date:t.due_date,
    category:t.kind==='document'?'documents':t.kind==='interview'?'home':'other',
    status:t.effective_status==='done'?'ready':t.effective_status==='doing'?'preparing':'todo',
    note:(t.waiting_for?'等待：'+t.waiting_for+'。':'')+t.notes,sourceUrl:t.source_url,
    schoolName:plan().context.target_school,origin:'personal',reminderDays:0,
    workspaceTaskHref:href('workspace','','schedule')+'&task='+encodeURIComponent(t.id),
    workspaceDateLabel:t.date_kind==='notice'?'通知期限・本人核對':'個人目標'
  }));
}
function workbenchRows(){
  if(!view||plan().archived)return [];
  const school=plan().context.target_school;
  const all=levels().filter(l=>required(l)&&status(l)!=='skipped'),open=all.filter(l=>!isDone(l));
  const started=open.filter(l=>status(l)==='started'||drafts.has(draftKey(l.id)));
  const ready=open.filter(l=>!started.includes(l)&&!missing(l).length).slice(0,12);
  const dateOf=l=>confirmedDeadline(l)?new Date(l.official_deadline_at).toLocaleDateString('sv-SE',{timeZone:'Asia/Taipei'}):'';
  const order=new Map(levels().map((l,i)=>[l.id,i]));
  const row=(l,state)=>({key:'path-'+l.id,title:l.title,status:state,school,date:dateOf(l),plan:false,href:href('level',l.id,'schedule'),order:order.get(l.id)});
  const own=(view.workspace?.tasks||[]).map(t=>({key:'workspace-'+plan().id+'-'+t.id,workspaceTaskId:t.id,
    title:(t.optional?'自選 · ':'')+t.title+(t.effective_status==='waiting'?'（等待中）':''),
    status:t.effective_status==='done'?'ready':t.effective_status==='doing'?'preparing':'todo',
    school,date:t.due_date||'',plan:false,href:href('workspace','','schedule')+'&task='+encodeURIComponent(t.id)}));
  return [...started.map(l=>row(l,'preparing')),...ready.map(l=>row(l,'todo')),...all.filter(isDone).map(l=>row(l,'ready')),...own];
}
// 今天: one task to do now, the next confirmed deadline, where the student is, and what comes next.
// It reads the same plan as the checklist and the map; nothing here is stored separately.
function deadlineHtml(due,source){
  if(!due)return '<h3>下一個已確認的官方期限</h3><p class="today-empty">目前沒有已確認的期限。</p>'+(source?'<a class="today-link" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">查看官方公告'+icon('arrow-up-right')+'</a>':'');
  const d=new Date(due.official_deadline_at),tz={timeZone:'Asia/Taipei'},past=d<new Date(),left=Math.ceil((d-Date.now())/86400000);
  return '<h3>下一個已確認的官方期限</h3><p class="today-date">'+d.toLocaleDateString('zh-TW',{...tz,month:'numeric',day:'numeric'})+'</p><p><b>'+d.toLocaleDateString('zh-TW',{...tz,weekday:'short'})+' '+d.toLocaleTimeString('zh-TW',{...tz,hour:'2-digit',minute:'2-digit',hour12:false})+'</b> <span class="today-pill '+(past?'late':left<=14?'soon':'')+'">'+(past?'已過期':left<=0?'今天截止':'還有 '+left+' 天')+'</span></p><p>'+esc(due.title)+'</p><a class="today-link" href="'+href('level',due.id,'today')+'">前往這一項'+icon('arrow-right')+'</a>';
}
function renderToday(){
  const n=next(),all=levels(),resume=n&&n.kind!=='checks'&&(status(n)==='started'||drafts.has(draftKey(n.id)));
  const due=all.filter(l=>confirmedDeadline(l)&&!l.external&&status(l)!=='skipped'&&!isDone(l)).sort((a,b)=>a.official_deadline_at.localeCompare(b.official_deadline_at))[0];
  const source=urls(n||{})[0]||all.flatMap(urls)[0],why=nextReason(n);
  $('#today-view').innerHTML='<div class="today"><div class="today-top"><section class="today-focus" aria-labelledby="today-focus-title"><span class="today-label">'+(n?'現在做這件事':'目前進度')+'</span><h2 id="today-focus-title">'+esc(n?n.title:'已完成已知的準備事項')+'</h2>'+
      (n&&n.prompt?'<p>'+esc(n.prompt.length>110?n.prompt.slice(0,110)+'…':n.prompt):n?.kind==='checks'?'<p>'+(n.progress.total-n.progress.value)+' 項條件還需要你的資料或確認。':'')+(why==='下一項可開始的準備。'?'':'<p class="today-why">'+esc(why)+'</p>')+
      '<div class="today-actions">'+(n?'<a class="today-primary" href="'+href('level',n.id,'today')+'">'+(resume?'繼續':'開始')+icon('arrow-right')+'</a>':'')+(n&&urls(n)[0]?'<a class="today-source" href="'+esc(urls(n)[0])+'" target="_blank" rel="noopener noreferrer">官方來源'+icon('arrow-up-right')+'</a>':'')+'</div></section>'+
      '<aside class="today-panel" aria-label="期限">'+deadlineHtml(due,source)+'</aside></div></div>';
}
function renderOverview(){
  $('#overview-summary').innerHTML='<h2>準備清單</h2>';
  const groups=new Map();
  for(const l of levels()){
    if(setup(l))continue;
    const group=(l.external&&!l.id.startsWith('cgu-'))?'校方通知紀錄':assistance(l)?'選用寫作協助':l.stageTitle;
    if(!groups.has(group))groups.set(group,[]);groups.get(group).push(l);
  }
  const n=next();
  const groupOrder=([title])=>title==='校方通知紀錄'?1:title==='選用寫作協助'?2:0;
  $('#overview-stages').innerHTML=[...groups].sort((a,b)=>groupOrder(a)-groupOrder(b)).map(([title,items])=>{
    const optional=title==='選用寫作協助',external=items.every(l=>l.external);
    const st=totals(items),open=!optional&&!external&&(items.some(l=>l.id===n?.id)||(!n&&st.done<st.count));
    return '<details class="task-stage" '+(open?'open':'')+'><summary><h3>'+esc(title)+'</h3><span>'+(external?'自行記錄':optional?'選用':st.done+' / '+st.count)+'</span></summary>'+items.map(l=>{
      const s=status(l),pending=l.conditional&&record(l.id).applicable==null;
      const isCguNotice=l.external&&l.id.startsWith('cgu-');
      const label=isCguNotice?(hasContent(l)?record(l.id).value:(l.cgu_level_type==='oia_notice'?'待國際處更新':'待合作校通知')):l.external?(hasContent(l)?'已記錄':'等待通知'):s==='skipped'?'不適用':pending?'待確認適用性':s==='done'?'':l.kind==='checks'&&l.progress.value?l.progress.value+' / '+l.progress.total+' 符合':s==='started'?'進行中':missing(l).length?'待前置事項':'';
      return '<a class="task-row '+(s==='done'?'is-done':'')+(l.id===n?.id?' is-next':'')+'" href="'+href('level',l.id,'today')+'">'+icon(s==='done'?'circle-check':isCguNotice?(hasContent(l)?'bell-ring':'bell'):missing(l).length?'lock-keyhole':s==='started'?'circle-dot':'circle')+'<strong>'+esc(l.title)+'</strong><span>'+esc(label)+'</span>'+icon('chevron-right')+'</a>';
    }).join('')+'</details>';
  }).join('');
  icons();
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

return {init,show,refresh,clear,toolHref,formToolActive,selectTarget,startTarget,resumeOAuth,workbenchRows,workbenchTotals,workspaceCalendarEvents,syncPreferences,ensureTargetPreference,hasActivePlan,addPersonalTodo,togglePersonalTodo,hasRecoverableDrafts:()=>drafts.size>0};
})();

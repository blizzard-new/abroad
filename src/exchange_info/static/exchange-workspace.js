/* One student-owned workspace per exchange plan. All saves use the plan's server revision. */
window.UniWayExchangeWorkspace = (() => {
  'use strict';
  const STAGES={selection:'選校與探索',home:'校內申請',interview:'面試準備',nomination:'錄取與提名',host:'合作校申請',departure:'出發準備',arrival:'抵達與安頓',abroad:'交換生活',return:'返國與學分'};
  const KINDS={task:'一般待辦',document:'文件',interview:'面試練習',course:'課程',life:'生活準備',travel:'旅行',internship:'實習',community:'同梯交流'};
  const STATUS={todo:'尚未開始',doing:'準備中',waiting:'等待中',done:'已完成'};
  const FIELDS=['id','title','stage','kind','status','action','optional','notes','due_date','date_kind','date_reviewed','recipient','batch','signers','waiting_for','depends_on','source_label','source_url','source_excerpt','origin','file_version_id','file_location','course'];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clean=t=>Object.fromEntries(FIELDS.filter(k=>k in t).map(k=>[k,t[k]]));
  const safe=u=>{try{const p=new URL(u);return ['https:','http:'].includes(p.protocol)&&!p.username&&!p.password?p.href:'';}catch{return '';}};
  let host, bridge, scope='', account='', tab='tasks', kind='', stage='', status='', packData=null, previews=[], saving=false, editor=null, changed=false, saveRun=0;
  const drafts=new Map(),noticeDrafts=new Map();
  const $=s=>host?.querySelector(s), $$=s=>[...(host?.querySelectorAll(s)||[])];
  const view=()=>bridge?.get(), data=()=>view()?.workspace||{tasks:[]}, tasks=()=>data().tasks||[];
  const scopeNow=()=>[state.account?.id,view()?.plan.context.home_school,view()?.plan.id].join('|');
  const link=(id='')=>'#my-application?'+new URLSearchParams({plan:view()?.plan.id||'',view:'workspace',...(id?{task:id}:{})});
  const endpoint=s=>'/account/application-paths/'+encodeURIComponent(view().plan.id)+'/workspace'+s+'?'+new URLSearchParams({home_school:view().plan.context.home_school});
  const option=(items,value)=>Object.entries(items).map(([k,label])=>'<option value="'+esc(k)+'" '+(k===value?'selected':'')+'>'+esc(label)+'</option>').join('');
  const dateLabel=t=>t.due_date?`${t.date_kind==='notice'?'通知期限・本人核對':'個人目標'} ${t.due_date}`:'日期待確認';
  const base=()=>({id:crypto.randomUUID().replaceAll('-',''),title:'',stage:'departure',kind:'task',status:'todo',action:'prepare',optional:false,notes:'',due_date:null,date_kind:'unknown',date_reviewed:false,recipient:'',batch:'',signers:'',waiting_for:'',depends_on:[],source_label:'',source_url:'',source_excerpt:'',origin:'manual',file_version_id:null,file_location:'',course:null});
  function message(text,error=false){const el=$('#exchange-message');if(el){el.textContent=text;el.classList.toggle('is-error',error);el.focus({preventScroll:true});}}
  function snapshot(){
    if(!scope||!host)return;
    if(changed&&$('#exchange-task-form'))drafts.set(scope,{type:'task',task:readTask(),tab,kind,stage,status});
    else if(tab==='notice'&&$('#exchange-notice-form')){
      const f=$('#exchange-notice-form');
      const values=Object.fromEntries(new FormData(f));
      $$('[data-ex-preview]').forEach(row=>{const p=previews[Number(row.dataset.exPreview)],get=n=>row.querySelector('[name='+n+']').value;if(p){p.task={...p.task,...Object.fromEntries(['title','batch','recipient','signers','stage'].map(n=>[n,get(n)]))};p.candidate_date=get('due_date')||null;p.included=row.querySelector('[name=include]').checked;}});
      if(values.text||previews.length)noticeDrafts.set(scope,{type:'notice',values,previews,tab,kind,stage,status});
    }
  }
  function clear(){
    host?.querySelectorAll('dialog[open]').forEach(d=>d.close());
    if(host)host.replaceChildren();
    drafts.clear();noticeDrafts.clear();scope='';account='';editor=null;previews=[];packData=null;changed=false;saving=false;saveRun++;
  }
  function mount(target, callbacks){
    snapshot();host=target;bridge=callbacks;
    const nextAccount=state.account?.id||'';
    if(account&&account!==nextAccount)clear();
    account=nextAccount;
    const next=scopeNow(),switched=next!==scope;
    if(switched){scope=next;tab='tasks';kind='';stage='';status='';packData=null;previews=[];editor=null;changed=false;}
    const draft=drafts.get(scope)||(switched?noticeDrafts.get(scope):null);
    if(draft){tab=draft.tab;kind=draft.kind;stage=draft.stage;status=draft.status;}
    render();
    const wanted=new URLSearchParams(location.hash.split('?')[1]||'').get('task');
    if(draft?.type==='task')openEditor(draft.task,true);
    else if(wanted&&tasks().some(t=>t.id===wanted))openEditor(tasks().find(t=>t.id===wanted));
  }
  function summary(value, schedule=false){
    const rows=(value?.workspace?.tasks||[]).filter(t=>t.effective_status!=='done');
    if(!rows.length)return '<section class="ex-summary"><h3>從申請到交換生活</h3><a href="#my-application?'+new URLSearchParams({plan:value?.plan.id||'',view:'workspace'})+'">開啟準備工作台 →</a></section>';
    const ready=rows.filter(t=>t.status!=='waiting'&&!t.waiting_for&&!(t.action==='submit'&&t.blocked_by?.length));
    const waiting=rows.filter(t=>!ready.includes(t));
    const listed=(schedule?rows.filter(t=>t.due_date):ready).sort((a,b)=>(a.due_date||'9999').localeCompare(b.due_date||'9999')).slice(0,schedule?12:4);
    const href=t=>'#my-application?'+new URLSearchParams({plan:value.plan.id,view:'workspace',task:t.id});
    return '<section class="ex-summary"><div class="ex-head"><h3>'+ (schedule?'通知期限與個人目標':'我的準備與生活待辦')+'</h3><a href="'+href({id:''})+'">全部 '+rows.length+' 項 →</a></div><ul>'+listed.map(t=>'<li><a href="'+href(t)+'"><strong>'+esc(t.title)+'</strong><span>'+esc(dateLabel(t))+(t.optional?' · 自選':'')+'</span></a></li>').join('')+'</ul>'+(waiting.length?'<p>正在等待 '+waiting.length+' 項：'+esc(waiting.slice(0,2).map(t=>t.waiting_for||t.title).join('、'))+'</p>':'')+'</section>';
  }
  function render(){
    const locked=view().plan.archived;
    if(locked)tab='tasks';
    host.innerHTML='<div class="exchange-workspace"><div class="ex-head"><div><h2>準備工作台</h2></div><button class="primary-button" data-ex-new '+(locked?'disabled':'')+'>新增待辦</button></div><p id="exchange-message" role="status" tabindex="-1"></p>'+
      '<nav class="ex-tabs" aria-label="準備工作台工具">'+Object.entries({tasks:'我的任務',notice:'通知轉待辦',library:'加入準備清單',peers:'同梯交流'}).map(([key,name])=>'<button data-ex-tab="'+key+'" aria-pressed="'+(tab===key)+'" '+(locked&&key!=='tasks'?'disabled':'')+'>'+name+'</button>').join('')+'</nav>'+
      (locked?'<p>這份計畫已封存，恢復後可繼續編輯。</p>':'')+'<div id="exchange-content"></div><dialog id="exchange-task-dialog" aria-labelledby="exchange-task-title"></dialog></div>';
    if(tab==='tasks')renderTasks();
    if(tab==='notice')renderNotice();
    if(tab==='library')renderLibrary();
    if(tab==='peers')renderPeers();
    if(!host.dataset.exchangeBound){host.dataset.exchangeBound='1';host.addEventListener('click',click);host.addEventListener('submit',submit);host.addEventListener('change',change);host.addEventListener('input',e=>{if(e.target.closest('#exchange-task-form'))changed=true;});}
  }
  function renderTasks(){
    const all=tasks(), needed=all.filter(t=>!t.optional), optional=all.filter(t=>t.optional);
    const rows=all.filter(t=>(!kind||t.kind===kind)&&(!stage||t.stage===stage)&&(!status||t.effective_status===status));
    const done=xs=>xs.filter(t=>t.effective_status==='done').length;
    $('#exchange-content').innerHTML='<div class="ex-counts"><span>準備任務 <b>'+done(needed)+' / '+needed.length+'</b></span><span>自選目標 <b>'+done(optional)+' / '+optional.length+'</b></span><span>個人紀錄，不代表校方受理或錄取</span></div>'+
      '<div class="ex-filters"><label>階段<select id="exchange-stage"><option value="">全部階段</option>'+option(STAGES,stage)+'</select></label><label>類型<select id="exchange-kind"><option value="">全部類型</option>'+option(KINDS,kind)+'</select></label><label>狀態<select id="exchange-status"><option value="">全部狀態</option>'+option(STATUS,status)+'</select></label><div class="ex-actions"><button data-ex-export="text">下載準備筆記</button><button data-ex-export="calendar">匯出日期到行事曆</button></div></div>'+
      (kind==='course'?courseSummary():kind==='interview'?'<p class="ex-note">寫下自介、選校研究與回答，完成後可下載練習稿。練習題不代表校方考古題。<button data-ex-pack="interview">加入面試練習清單</button></p>':'')+
      '<div class="ex-task-list">'+(rows.length?rows.map(t=>'<article class="ex-task" data-ex-task="'+esc(t.id)+'"><div><div class="ex-meta">'+esc(STAGES[t.stage])+' · '+esc(KINDS[t.kind])+(t.batch?' · '+esc(t.batch):'')+(t.optional?' · 自選':'')+'</div><h3><button data-ex-edit="'+esc(t.id)+'">'+esc(t.title)+'</button></h3><p>'+esc(dateLabel(t))+'</p>'+(t.waiting_for?'<p class="ex-wait">等待：'+esc(t.waiting_for)+'</p>':'')+(t.blocked_by?.length?'<p class="ex-wait">'+(t.action==='submit'?'送件前須完成：':'可先準備；前置事項：')+esc(t.blocked_by.map(id=>all.find(x=>x.id===id)?.title||id).join('、'))+'</p>':'')+(t.file_unavailable?'<p class="is-error">文件已過期或移除，請重新連結並核對。</p>':'')+(t.recipient||t.signers?'<p>'+esc([t.recipient&&'交給 '+t.recipient,t.signers&&'簽名 '+t.signers].filter(Boolean).join(' · '))+'</p>':'')+'</div><div class="ex-task-action"><span>'+esc(STATUS[t.effective_status])+'</span><button class="outline-button" data-ex-edit="'+esc(t.id)+'">'+(t.kind==='interview'?'寫下回答':'開啟任務')+'</button></div></article>').join(''):'<div class="ex-empty"><h3>'+ (all.length?'此分類沒有任務':'先放進你正在準備的事')+'</h3><p>可以貼上校方通知、選擇適合的清單，或自己新增一項。</p><button class="outline-button" data-ex-tab="library">查看準備清單</button></div>')+'</div>';
  }
  function courseSummary(){
    const all=tasks().filter(t=>t.kind==='course'),conflicts=data().course_conflicts||[];
    return '<section class="ex-course"><h3>我的課程安排</h3><p>已記錄 '+data().credits+' 學分；認列狀態由你記錄，仍須向母校確認。</p><form data-ex-credit><label>個人學分目標<input type="number" name="credit_goal" min="0" max="120" step="0.5" value="'+esc(data().credit_goal??'')+'" placeholder="依自己的目標填寫"></label><button class="outline-button">保存目標</button><button type="button" data-ex-course>新增課程</button></form>'+
      (data().credit_goal!=null?'<p>距離個人目標：'+Math.max(0,data().credit_goal-data().credits)+' 學分</p>':'')+
      (conflicts.length?'<p class="is-error">時間衝突：'+esc(conflicts.map(pair=>pair.map(id=>all.find(t=>t.id===id)?.title).join('／')).join('、'))+'</p>':'')+
      '<ul>'+all.map(t=>'<li>'+esc(t.title)+' · '+esc(t.course?.credits??'待確認')+' 學分 · '+(t.course?.weekday?'週'+['','一','二','三','四','五','六','日'][t.course.weekday]+' '+esc((t.course.start||'').slice(0,5))+'–'+esc((t.course.end||'').slice(0,5)):'時間待確認')+'</li>').join('')+'</ul></section>';
  }
  function input(name,label,value='',extra=''){return '<label>'+label+'<input name="'+name+'" value="'+esc(value??'')+'" '+extra+'></label>';}
  function openEditor(task=base(),recover=false){
    editor=clean(task);changed=recover;
    const c=task.course||{}, f=$('#exchange-task-dialog');
    f.innerHTML='<form id="exchange-task-form"><div class="ex-head"><h2 id="exchange-task-title">'+(tasks().some(t=>t.id===task.id)?'編輯任務':'新增待辦')+'</h2><button type="button" data-ex-close aria-label="關閉任務">關閉</button></div><p role="alert" id="exchange-edit-error"></p><fieldset '+(view().plan.archived?'disabled':'')+'>'+input('title','要做的事',task.title,'required maxlength="160"')+
      '<div class="ex-grid"><label>階段<select name="stage">'+option(STAGES,task.stage)+'</select></label><label>類型<select name="kind">'+option(KINDS,task.kind)+'</select></label><label>狀態<select name="status">'+option(STATUS,task.status)+'</select></label><label>日期類型<select name="date_kind">'+option({unknown:'日期待確認',personal:'個人目標',notice:'通知期限（自行核對）'},task.date_kind)+'</select></label>'+input('due_date','日期',task.due_date,'type="date"')+input('waiting_for','正在等誰／什麼通知',task.waiting_for,'maxlength="300"')+'</div><label class="ex-check"><input type="checkbox" name="optional" '+(task.optional?'checked':'')+'>這是自選目標，不計入準備任務進度</label>'+
      '<label>'+(task.kind==='interview'?'我的回答／自我介紹':'準備內容與筆記')+'<textarea name="notes" rows="6" maxlength="12000">'+esc(task.notes)+'</textarea></label>'+
      '<div data-ex-course-fields '+(task.kind==='course'?'':'hidden')+'><h3>課程資訊</h3><div class="ex-grid">'+input('credits','學分',c.credits,'type="number" min="0" max="60" step="0.5"')+'<label>星期<select name="weekday"><option value="">待確認</option>'+option({1:'星期一',2:'星期二',3:'星期三',4:'星期四',5:'星期五',6:'星期六',7:'星期日'},String(c.weekday||''))+'</select></label>'+input('start','開始時間',c.start?.slice(0,5),'type="time"')+input('end','結束時間',c.end?.slice(0,5),'type="time"')+'<label>學分認列（自行記錄）<select name="recognition">'+option({unknown:'待確認',asking:'已向母校詢問',confirmed:'已收到確認',not_recognized:'不認列'},c.recognition||'unknown')+'</select></label></div></div>'+
      '<details '+(task.origin==='notice'||task.date_kind==='notice'?'open':'')+'><summary>來源、日期核對與原文</summary>'+input('source_label','來源名稱',task.source_label,'maxlength="200"')+input('source_url','來源或辦理網址',task.source_url,'type="url" maxlength="2000"')+'<label>通知原文／來源摘錄<textarea name="source_excerpt" maxlength="6000" rows="3">'+esc(task.source_excerpt)+'</textarea></label><label class="ex-check"><input name="date_reviewed" type="checkbox" '+(task.date_reviewed?'checked':'')+'>我已核對通知的適用對象、年份與期限</label>'+(safe(task.source_url)?'<a href="'+esc(safe(task.source_url))+'" target="_blank" rel="noopener noreferrer">開啟來源／辦理入口 ↗</a>':'')+'</details>'+
      '<details '+(task.batch||task.action==='submit'?'open':'')+'><summary>分批文件、送件與前置事項</summary><div class="ex-grid">'+input('batch','批次',task.batch,'maxlength="80" placeholder="例如：第二批補件"')+input('recipient','交給誰／收件單位',task.recipient,'maxlength="200"')+input('signers','需要誰簽名',task.signers,'maxlength="200"')+'<label>這項任務是<select name="action">'+option({prepare:'準備工作（可提前進行）',submit:'正式送件（完成前須滿足前置事項）'},task.action)+'</select></label></div><label>前置事項（可複選）<select multiple name="depends_on" size="3">'+tasks().filter(t=>t.id!==task.id).map(t=>'<option value="'+esc(t.id)+'" '+(task.depends_on?.includes(t.id)?'selected':'')+'>'+esc(t.title)+'</option>').join('')+'</select></label><p>前置事項尚未完成時，仍可先保存草稿與準備內容。</p></details>'+
      '<div data-ex-file-fields '+(task.kind==='document'?'':'hidden')+'><details><summary>連結或保存文件</summary>'+input('file_location','自行保管的文件位置／版本說明',task.file_location,'maxlength="500"')+'<label>私人文件庫中的版本<select name="file_version_id"><option value="">不連結檔案</option>'+(task.file_version_id?'<option selected value="'+esc(task.file_version_id)+'">已連結的文件版本</option>':'')+'</select></label><button type="button" data-ex-files>載入我的文件</button><button type="button" data-ex-download-file>下載選取版本</button><input type="file" id="exchange-upload"><label class="ex-check"><input type="checkbox" id="exchange-upload-consent">同意將選取檔案加密保存 30 天</label><button type="button" data-ex-upload>保存並連結檔案</button><p id="exchange-file-status" role="status"></p></details></div>'+
      '<div class="ex-actions"><button class="primary-button" type="submit">保存任務</button><button type="button" data-ex-discard>捨棄這次編輯</button>'+(tasks().some(t=>t.id===task.id)?'<button type="button" data-ex-delete="'+esc(task.id)+'">移除此任務</button>':'')+'</div></fieldset></form>';
    f.addEventListener('cancel',()=>snapshot(),{once:true});f.showModal();
  }
  function readTask(){
    const f=$('#exchange-task-form');if(!f)return editor;
    const v=Object.fromEntries(new FormData(f));
    const t={...editor,...Object.fromEntries(['title','stage','kind','status','date_kind','notes','waiting_for','source_label','source_url','source_excerpt','batch','recipient','signers','action','file_location'].map(k=>[k,v[k]||''])),due_date:v.due_date||null,optional:!!v.optional,date_reviewed:!!v.date_reviewed,depends_on:new FormData(f).getAll('depends_on'),file_version_id:v.kind==='document'?(v.file_version_id||null):null};
    t.course=v.kind==='course'?{credits:v.credits===''?null:Number(v.credits),weekday:v.weekday?Number(v.weekday):null,start:v.start||null,end:v.end||null,recognition:v.recognition}:null;
    return t;
  }
  async function persist(next,goal=data().credit_goal,source='task'){
    if(saving||view().plan.archived)return false;
    const captured=scope,run=++saveRun;saving=true;
    const buttons=$$('button[type="submit"],.ex-actions .primary-button').filter(b=>!b.disabled);
    buttons.forEach(b=>b.disabled=true);
    try{
      await bridge.save({revision:view().revision,tasks:next.map(clean),credit_goal:goal??null});
      if(captured!==scope||scopeNow()!==captured)return false;
      changed=false;if(source==='task')drafts.delete(scope);
      if(source==='notice')noticeDrafts.delete(scope);
      editor=null;previews=[];
      $('#exchange-task-dialog')?.close();
      history.replaceState(history.state,'',link());
      if(host.contains(document.activeElement))document.activeElement.blur();
      host.replaceChildren();bridge.render();message('已保存至這份交換計畫。');return true;
    }catch(e){
      if(captured===scope){snapshot();const el=$('#exchange-edit-error');if(el)el.textContent=e.message;else message(e.message,true);}
      return false;
    }finally{if(run===saveRun)saving=false;buttons.forEach(b=>{if(b.isConnected)b.disabled=false;});}
  }
  function renderNotice(){
    const draft=noticeDrafts.get(scope),v=draft?.values||{};
    if(draft?.type==='notice'&&!previews.length)previews=draft.previews||[];
    $('#exchange-content').innerHTML='<section class="ex-notice"><h3>把校方通知整理成可執行的任務</h3><form id="exchange-notice-form">'+input('source_label','通知名稱',v.source_label,'required maxlength="200" placeholder="例如：合作校第二批補件通知"')+input('source_url','原始公告網址（選填）',v.source_url,'type="url" maxlength="2000"')+'<label>貼上通知內容<textarea name="text" maxlength="80000" rows="7" required>'+esc(v.text||'')+'</textarea></label><details><summary>或從 PDF／DOCX／TXT 讀取文字</summary><input type="file" id="exchange-notice-file" accept=".pdf,.docx,.txt"><label class="ex-check"><input type="checkbox" id="exchange-extract-consent">同意解析文字，原檔不保存</label><button type="button" data-ex-extract>讀取附件文字</button><p>最多 5 MB；掃描圖片需先轉為文字。擷取後可先移除不需要保存的個人資料。</p></details><button class="primary-button" type="submit">整理待辦草稿</button><button type="button" data-ex-clear-notice>清除這份通知草稿</button></form><div id="exchange-preview"></div></section>';
    if(previews.length)renderPreview();
  }
  function renderPreview(){
    $('#exchange-preview').innerHTML='<form id="exchange-review-form"><h3>逐項核對，再加入計畫</h3>'+previews.map((p,i)=>'<article class="ex-preview" data-ex-preview="'+i+'"><label class="ex-check"><input type="checkbox" name="include" '+(p.included===false?'':'checked')+'>加入這項</label>'+input('title','任務名稱',p.task.title,'required maxlength="160"')+'<div class="ex-grid">'+input('due_date','候選日期（未確認可留空）',p.candidate_date,'type="date"')+input('batch','批次',p.task.batch,'maxlength="80"')+input('recipient','收件對象',p.task.recipient,'maxlength="200"')+input('signers','簽名',p.task.signers,'maxlength="200"')+'<label>階段<select name="stage">'+option(STAGES,p.task.stage)+'</select></label></div><details open><summary>原文與需要確認的地方</summary><blockquote>'+esc(p.task.source_excerpt)+'</blockquote><p>'+esc(p.warnings.join(' '))+'</p></details></article>').join('')+'<label class="ex-check"><input type="checkbox" name="reviewed" required>我已逐項核對來源、適用學期與日期；這些是我的通知紀錄</label><button class="primary-button" type="submit">加入選取的待辦</button></form>';
  }
  async function loadPacks(country){
    const captured=scope;
    const selected=country??state.dashboard?.partner_universities?.find(t=>t.school_name===view().plan.context.target_school)?.country??'';
    const loaded=await fetchJson(endpoint('/suggestions')+'&'+new URLSearchParams({country:selected}));
    if(scope!==captured)return;
    packData={...loaded,country:selected};return packData;
  }
  async function renderLibrary(){
    const captured=scope;$('#exchange-content').innerHTML='<p role="status">正在載入適合的準備清單…</p>';
    try{
      if(!packData)await loadPacks();if(scope!==captured||tab!=='library')return;
      const existing=new Set(tasks().map(t=>t.id));
      $('#exchange-content').innerHTML='<p>依需要選取；未載明的日期保留待確認。通用建議不等於校方要求。</p><label>目的地行前提醒<select id="exchange-country"><option value="">選擇目的地</option>'+packData.countries.map(c=>'<option value="'+esc(c.value)+'" '+(c.value===packData.country?'selected':'')+'>'+esc(c.label)+'</option>').join('')+'</select></label><form id="exchange-library-form">'+packData.packs.map(p=>'<details class="ex-pack"><summary>'+esc(p.title)+' · '+p.tasks.length+' 項</summary><button type="button" data-ex-select-pack="'+esc(p.id)+'">選取本組尚未加入的項目</button>'+p.tasks.map(t=>'<label class="ex-check"><input type="checkbox" name="task" value="'+esc(t.id)+'" data-pack="'+esc(p.id)+'" '+(existing.has(t.id)?'disabled':'')+'><span><strong>'+esc(t.title)+(existing.has(t.id)?'（已加入）':'')+'</strong><small>'+esc(t.notes)+'</small>'+(t.source_url?'<small>'+esc(t.source_label)+'</small>':'')+'</span></label>').join('')+'</details>').join('')+'<button class="primary-button" type="submit">加入選取項目</button></form>';
    }catch(e){if(scope===captured)message(e.message,true);}
  }
  function renderPeers(){
    const captured=scope;
    $('#exchange-content').innerHTML='<section class="ex-peers"><h3>同校、同學期的交流</h3><p>'+esc(view().plan.context.target_school)+' · '+esc(view().plan.context.departure_year)+' · '+esc({fall:'上學期',spring:'下學期',full_year:'全學年',undecided:'學期未定'}[view().plan.context.semester])+'</p><p>自願發布邀請後，同梯可以在站內回覆；不會公開你的文件或私人任務。</p><div id="exchange-peers-list" role="status">正在讀取交流…</div><form id="exchange-peer-form"><label>想和同梯聊什麼？<textarea name="body" rows="3" minlength="10" maxlength="1200" required placeholder="例如：想一起確認宿舍報到與抵達交通，歡迎在這裡交流。"></textarea></label><label class="ex-check"><input type="checkbox" name="consent" required>我同意將這段文字與計畫的目的校、學期發布到站內公共討論</label><button class="primary-button" type="submit">發布同梯邀請</button></form></section>';
    bridge.peers?.().then(rows=>{if(scope!==captured||tab!=='peers'||!$('#exchange-peers-list'))return;$('#exchange-peers-list').innerHTML=rows.length?rows.map(p=>'<article class="ex-task"><div><h4>'+esc(p.title)+'</h4><p>'+esc(p.body)+'</p><a href="'+esc(p.url)+'">查看討論與回覆 →</a></div></article>').join(''):'<p>目前沒有這個學期的邀請。你可以留下第一則。</p>';}).catch(e=>{if(scope===captured)message(e.message,true);});
  }
  async function click(e){
    const b=e.target.closest('button');if(!b)return;
    if(b.dataset.exTab){snapshot();tab=b.dataset.exTab;editor=null;changed=false;render();return;}
    if(b.hasAttribute('data-ex-new'))return openEditor();
    if(b.hasAttribute('data-ex-course'))return openEditor({...base(),kind:'course',stage:'abroad'});
    if(b.dataset.exEdit)return openEditor(tasks().find(t=>t.id===b.dataset.exEdit));
    if(b.hasAttribute('data-ex-close')){snapshot();$('#exchange-task-dialog').close();return;}
    if(b.hasAttribute('data-ex-discard')){changed=false;drafts.delete(scope);editor=null;$('#exchange-task-dialog').close();history.replaceState(history.state,'',link());return;}
    if(b.hasAttribute('data-ex-clear-notice')){noticeDrafts.delete(scope);previews=[];renderNotice();message('已清除尚未加入計畫的通知草稿。');return;}
    if(b.dataset.exDelete){
      if(tasks().some(t=>t.depends_on?.includes(b.dataset.exDelete))){$('#exchange-edit-error').textContent='其他任務仍依賴此項，請先解除前置關係。';return;}
      return persist(tasks().filter(t=>t.id!==b.dataset.exDelete));
    }
    if(b.dataset.exExport)return download(b.dataset.exExport);
    if(b.dataset.exSelectPack){$$('input[data-pack="'+b.dataset.exSelectPack+'"]').filter(x=>!x.disabled).forEach(x=>x.checked=true);return;}
    if(b.dataset.exPack){const captured=scope;try{if(!packData)await loadPacks();if(scope!==captured)return;await addTasks(packData.packs.find(p=>p.id===b.dataset.exPack).tasks);}catch(error){if(scope===captured)message(error.message,true);}return;}
    if(b.hasAttribute('data-ex-files'))return files();
    if(b.hasAttribute('data-ex-download-file'))return downloadFile(b);
    if(b.hasAttribute('data-ex-upload'))return upload();
    if(b.hasAttribute('data-ex-extract'))return extract();
  }
  async function addTasks(rows){
    const existing=new Set(tasks().map(t=>t.id)),fresh=rows.filter(t=>!existing.has(t.id));
    if(!fresh.length){message('沒有新的項目可加入；已有紀錄保持原樣。');return;}
    const before=tab;tab='tasks';if(!await persist([...tasks(),...fresh],data().credit_goal,before))tab=before;
  }
  async function submit(e){
    const f=e.target;if(!host.contains(f))return;
    if(!['exchange-task-form','exchange-notice-form','exchange-review-form','exchange-library-form','exchange-peer-form'].includes(f.id)&&!f.hasAttribute('data-ex-credit'))return;
    e.preventDefault();if(saving||view().plan.archived)return;
    if(f.id==='exchange-task-form'){const t=readTask();changed=true;return persist([...tasks().filter(x=>x.id!==t.id),t]);}
    if(f.hasAttribute('data-ex-credit'))return persist(tasks(),f.elements.credit_goal.value===''?null:Number(f.elements.credit_goal.value),'credit');
    if(f.id==='exchange-library-form'){const ids=new Set(new FormData(f).getAll('task'));return addTasks(packData.packs.flatMap(p=>p.tasks).filter(t=>ids.has(t.id)));}
    if(f.id==='exchange-review-form'){
      const rows=$$('[data-ex-preview]').filter(row=>row.querySelector('[name=include]').checked).map(row=>{const p=previews[Number(row.dataset.exPreview)],get=n=>row.querySelector('[name='+n+']').value,d=get('due_date');return {...p.task,title:get('title'),stage:get('stage'),batch:get('batch'),recipient:get('recipient'),signers:get('signers'),due_date:d||null,date_kind:d?'notice':'unknown',date_reviewed:!!d};});
      return addTasks(rows);
    }
    if(f.dataset.pending)return;
    const captured=scope,values=Object.fromEntries(new FormData(f));
    const button=f.querySelector('button[type="submit"]');
    f.dataset.pending='true';if(button)button.disabled=true;
    try{
      if(f.id==='exchange-peer-form'){await bridge.postPeer(values.body);if(scope===captured&&tab==='peers'){renderPeers();message('同梯邀請已送出，依論壇發布狀態顯示。');}return;}
      const result=await fetchJson(endpoint('/preview'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)});
      if(scope!==captured)return;previews=result.items;
      noticeDrafts.set(scope,{type:'notice',values,previews,tab:'notice',kind,stage,status});
      if(tab==='notice'){renderPreview();message(result.message);}
    }catch(error){if(scope===captured)message(error.message,true);}
    finally{delete f.dataset.pending;if(button?.isConnected)button.disabled=false;}
  }
  function change(e){
    if(e.target.id==='exchange-stage'){stage=e.target.value;renderTasks();}
    if(e.target.id==='exchange-kind'){kind=e.target.value;renderTasks();}
    if(e.target.id==='exchange-status'){status=e.target.value;renderTasks();}
    if(e.target.id==='exchange-country'){const captured=scope;loadPacks(e.target.value).then(()=>{if(scope===captured&&tab==='library')renderLibrary();}).catch(error=>message(error.message,true));}
    if(e.target.closest('#exchange-task-form')){
      changed=true;
      if(e.target.name==='kind'){$('[data-ex-course-fields]').hidden=e.target.value!=='course';$('[data-ex-file-fields]').hidden=e.target.value!=='document';}
      if(e.target.name==='date_kind'&&e.target.value==='unknown')$('#exchange-task-form').elements.due_date.value='';
    }
  }
  async function files(){
    const captured=scope,id=editor?.id;
    try{const r=await fetchJson('/account/vault/documents');if(scope!==captured||editor?.id!==id)return;
      const s=$('[name=file_version_id]'),selected=s.value;
      s.innerHTML='<option value="">不連結檔案</option>'+r.items.flatMap(d=>d.versions.filter(v=>Date.parse(v.expires_at)>Date.now()).map(v=>'<option value="'+esc(v.id)+'" '+(v.id===selected?'selected':'')+'>'+esc(v.file_name)+'</option>')).join('');
    }catch(error){if(scope===captured&&editor?.id===id)$('#exchange-edit-error').textContent=error.message;}
  }
  async function downloadFile(button){
    const id=$('[name=file_version_id]').value,captured=scope;
    if(!id){$('#exchange-edit-error').textContent='請先選擇要下載的文件版本。';return;}
    button.disabled=true;
    try{
      const grant=await fetchJson('/account/vault/versions/'+encodeURIComponent(id)+'/download-grant',{method:'POST'});
      if(scope!==captured)return;
      const response=await fetch(grant.download_url,{method:'POST',cache:'no-store',credentials:'same-origin',headers:{'X-Vault-Download-Token':grant.token}});
      if(!response.ok)throw new Error('文件無法下載，請確認版本是否仍在保存期限內。');
      const blob=await response.blob();if(scope!==captured)return;
      const name=(response.headers.get('Content-Disposition')||'').match(/filename\*=UTF-8''([^;]+)/i)?.[1];
      const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name?decodeURIComponent(name):'交換文件';a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);
    }catch(error){if(scope===captured){const alert=$('#exchange-task-dialog[open] #exchange-edit-error');if(alert)alert.textContent=error.message;else message(error.message,true);}}
    finally{button.disabled=false;}
  }
  async function upload(){
    const file=$('#exchange-upload').files[0];if(!file||!$('#exchange-upload-consent').checked){$('#exchange-edit-error').textContent='請選擇檔案並勾選保存同意。';return;}
    const captured=scope,id=editor.id,fd=new FormData();
    Object.entries({label:$('#exchange-task-form').elements.title.value||'交換文件',category:'other',purpose:'application_preparation',retention_days:'30',consent:'true'}).forEach(([k,v])=>fd.append(k,v));fd.append('file',file);
    try{const r=await fetchJson('/account/vault/documents',{method:'POST',body:fd});if(scope!==captured||editor?.id!==id)return;
      await files();if(scope!==captured||editor?.id!==id)return;$('[name=file_version_id]').value=r.versions.at(-1).id;changed=true;snapshot();$('#exchange-file-status').textContent='檔案已保存；請保存任務以完成連結。';
    }catch(error){if(scope===captured&&editor?.id===id)$('#exchange-edit-error').textContent=error.message;}
  }
  async function extract(){
    const file=$('#exchange-notice-file').files[0];if(!file||!$('#exchange-extract-consent').checked){message('請選擇通知檔案並勾選解析同意。',true);return;}
    if(file.size>5*1024*1024){message('通知檔案上限為 5 MB。',true);return;}
    const fd=new FormData(),captured=scope;fd.append('file',file);fd.append('consent','true');
    try{const result=await fetchJson(endpoint('/extract'),{method:'POST',body:fd});if(scope!==captured||tab!=='notice')return;
      const f=$('#exchange-notice-form');f.elements.text.value=result.text;if(!f.elements.source_label.value)f.elements.source_label.value=file.name;snapshot();message('已讀取文字，請先核對，再整理待辦草稿。原檔未保存。');
    }catch(error){if(scope===captured)message(error.message,true);}
  }
  function download(type){
    const c=view().plan.context;
    let text=c.home_school+' → '+c.target_school+'\n'+c.departure_year+' · '+c.semester+'\n個人準備紀錄；不代表校方受理或錄取。\n\n';
    for(const t of tasks())text+=`${t.title}\n${STAGES[t.stage]} · ${STATUS[t.effective_status]}${t.optional?' · 自選':''}\n${dateLabel(t)}\n${t.batch?'批次：'+t.batch+'\n':''}${t.recipient?'交給：'+t.recipient+'\n':''}${t.signers?'簽名：'+t.signers+'\n':''}${t.waiting_for?'等待：'+t.waiting_for+'\n':''}${t.notes}\n${t.file_location?'文件位置：'+t.file_location+'\n':''}${t.source_label} ${t.source_url}\n\n`;
    if(type==='calendar'){
      const escI=v=>String(v||'').replace(/\\/g,'\\\\').replace(/\r?\n/g,'\\n').replace(/,/g,'\\,').replace(/;/g,'\\;');
      const stamp=new Date().toISOString().replace(/[-:]/g,'').split('.')[0]+'Z';
      const rows=tasks().filter(t=>t.due_date&&t.effective_status!=='done');
      if(!rows.length){message('目前沒有可匯出的日期，先設定個人目標或核對通知期限。');return;}
      const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//UniWay//Exchange Workspace//ZH-TW',...rows.flatMap(t=>['BEGIN:VEVENT','UID:'+view().plan.id+'-'+t.id+'@uniway','DTSTAMP:'+stamp,'DTSTART;VALUE=DATE:'+t.due_date.replaceAll('-',''),'SUMMARY:'+escI((t.date_kind==='notice'?'[通知期限・本人核對] ':'[個人目標] ')+t.title),'DESCRIPTION:'+escI(t.notes+'\n'+t.source_label+'\n'+t.source_url),'END:VEVENT']),'END:VCALENDAR'];
      const encoder=new TextEncoder();text=lines.map(line=>{let out='',size=0;for(const ch of line){const n=encoder.encode(ch).length;if(size+n>74){out+='\r\n ';size=1;}out+=ch;size+=n;}return out;}).join('\r\n')+'\r\n';
    }
    const url=URL.createObjectURL(new Blob([text],{type:type==='calendar'?'text/calendar;charset=utf-8':'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=type==='calendar'?'UniWay-preparation.ics':'UniWay-preparation.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  addEventListener('beforeunload',e=>{snapshot();if(drafts.size||noticeDrafts.size||saving){e.preventDefault();e.returnValue='';}});
  return {mount,clear,snapshot,summary,hasDrafts:()=>changed||drafts.size>0||noticeDrafts.size>0,isSaving:()=>saving};
})();

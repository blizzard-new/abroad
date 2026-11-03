/* Existing forms stay mounted once: levels own the entry; scheduling has its own page. */
window.UniWayApplicationWorkspace = (() => {
  const selection = ['advisor', 'favorites', 'eligibility'];
  const documents = ['application-center', 'application-form', 'document-check', 'documents', 'writing-assistant'];
  const schedule = [['overview','時程'], ['calendar','日曆'], ['deadlines','官方期限'], ['budget','預算'], ['scholarships','補助']];
  let root, activePage, mounted = null, validationFrame = 0;
  function syncConditions() {
    const form = document.querySelector('#advisor-form');
    const eligibility = activePage === 'eligibility';
    const parent = document.querySelector(eligibility ? '#eligibility .eligibility-layout' : '#advisor .advisor-layout');
    if (form.parentElement !== parent) parent.prepend(form);
    form.dataset.mode = eligibility ? 'eligibility' : 'advisor';
    if (eligibility) document.querySelector('#advisor-qualification-fields').open = true;
    const period = document.querySelector('#application-period-fields');
    period.hidden = !eligibility; period.disabled = !eligibility;
    ['college','department','degree','academic-score','language-test'].forEach(id => {
      document.querySelector(`#advisor-${id}`).required = eligibility;
    });
    renderAdvisorAccessState();
  }
  function init() {
    const first = document.querySelector('#overview');
    if (!first || root) return;
    root = document.createElement('section'); root.id = 'application-workspace'; root.hidden = true;
    first.before(root);
    root.innerHTML = '<header class="application-tools-heading"><a href="#my-application"><i data-lucide="route" aria-hidden="true"></i>我的申請</a><nav aria-label="我的申請工具"></nav></header>';
    [...selection, ...documents, ...schedule.map(x=>x[0])].forEach(id => {
      const page = document.querySelector(`[data-university-page="${id}"]`);
      if (page) root.append(page);
    });
    const planning = document.querySelector('#planning-workspace');
    const details = document.createElement('details'); details.id='planning-deadline-settings'; details.className='journey-settings planning-deadline-settings';
    details.innerHTML='<summary>依官方期限預留準備天數<i data-lucide="calendar-range" aria-hidden="true"></i></summary>';
    planning.before(details); details.append(planning);
    planning.querySelector('#planning-title').textContent='依期限預留準備天數';
    for(const [selector,label] of [['.application-center-setup','申請設定與共用資料'],['#staged-network-effects-hub','更多申請資源']]) {
      const content=root.querySelector(selector); if(!content)continue;
      const disclosure=document.createElement('details');disclosure.className='level-tool-disclosure';disclosure.open=true;
      const summary=document.createElement('summary');summary.textContent=label;disclosure.append(summary);
      content.before(disclosure);disclosure.append(content);
    }
    document.querySelector('#advisor-form').addEventListener('invalid', event => {
      for (let p=event.target.parentElement; p; p=p.parentElement) if (p.tagName==='DETAILS') p.open=true;
      if (!validationFrame) validationFrame=requestAnimationFrame(()=>{
        validationFrame=0;
        const field=document.querySelector('#advisor-form input:invalid, #advisor-form select:invalid');
        if (field) (field.uniwayGlide?.trigger || field).focus();
      });
    }, true);
    render();
  }
  function release() {
    if (!mounted) return;
    mounted.querySelectorAll('.level-tool-disclosure').forEach(d=>d.open=true);
    mounted.hidden=true; root.append(mounted); mounted=null;
  }
  function show(page) { release(); activePage=page; render(); }
  function render() {
    if (!root) return;
    syncConditions();
    const scheduling=schedule.some(x=>x[0]===activePage);
    root.hidden=!!mounted || !(scheduling || selection.includes(activePage) || documents.includes(activePage));
    const nav=root.querySelector('.application-tools-heading nav');
    nav.hidden=!scheduling;
    if (nav.dataset.page!==activePage) {
      nav.dataset.page=activePage;
      nav.innerHTML=schedule.map(([id,label])=>`<a href="#${id}"${id===activePage?' aria-current="page"':''}>${label}</a>`).join('');
      initIcons();
    }
    document.querySelector('#application-schedule-details').hidden=document.querySelector('#journey-workspace').hidden;
    const legacy=document.querySelector('#planning-deadline-settings'), advanced=document.querySelector('#application-schedule-details');
    if (legacy.nextElementSibling!==advanced) advanced.before(legacy);
  }
  function mount(tool, host) {
    release();
    const page=tool.startsWith('application-form=')?'application-form':tool;
    if (![...selection,...documents].includes(page)) return false;
    mounted=root.querySelector(`[data-university-page="${page}"]`);
    if (!mounted) return false;
    activePage=page; host.append(mounted); mounted.hidden=false; render();
    mounted.querySelectorAll('.level-tool-disclosure').forEach(d=>d.open=false);
    if (page==='application-form') {
      state.activeApplicationTemplateId=decodeURIComponent(tool.slice('application-form='.length));
      const template=applicationTemplateById(state.activeApplicationTemplateId);
      if (template) renderApplicationFormPage(template);
      else { release(); host.textContent='找不到這份表格，請從「填表與列印」選擇可用的文件。'; return false; }
    }
    window.UniWayDocumentWorkbench?.route(page);
    return true;
  }
  function openDeadlineSettings() { const details=document.querySelector('#planning-deadline-settings'); if(details)details.open=true; }
  return {init, show, render, mount, release, openDeadlineSettings};
})();

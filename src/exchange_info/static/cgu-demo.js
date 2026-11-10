(() => {
  'use strict';
  const KEY = 'uniway-cgu-demo:v1';
  const $ = (selector) => document.querySelector(selector);
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let content, plan = null, chosen = '', viewedStage = 0, corrupt = false, memoryOnly = false, stale = false;
  const allTasks = () => content.stages.flatMap((stage) => stage.tasks);
  const announce = (message) => { $('#announcement').textContent = message; };
  function notice(message) { $('#storage-notice').textContent = message; $('#storage-notice').hidden = !message; }
  function sourceLink(id, label = '官方來源 ↗') {
    const source = content.sources.find((item) => item.id === id);
    return source ? external(source.url, label, 'source-link') : '<span class="micro">來源待確認</span>';
  }
  function external(url, label, className = '') {
    try {
      if (new URL(url).protocol !== 'https:') return '<span class="micro">官方 HTTPS 來源待確認</span>';
      return `<a class="${esc(className)}" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`;
    } catch { return '<span class="micro">來源待確認</span>'; }
  }
  function validDate(value) {
    if (value === '') return true;
    if (!/^20\d{2}-\d{2}-\d{2}$/.test(value)) return false;
    const parsed = new Date(`${value}T00:00:00Z`);
    return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
  }
  function readPlan() {
    let raw;
    try { raw = localStorage.getItem(KEY); }
    catch { memoryOnly = true; notice('瀏覽器儲存無法使用。本次操作僅暫存在此頁，重新整理後不會保留。'); return; }
    if (!raw) return;
    try {
      const saved = JSON.parse(raw);
      const ids = new Set(allTasks().map((task) => task.id));
      if (saved.version !== 1 || !content.schools.some((school) => school.id === saved.schoolId)
        || !Array.isArray(saved.completed) || saved.completed.some((id) => !ids.has(id))
        || !saved.dates || typeof saved.dates !== 'object' || Array.isArray(saved.dates)
        || Object.entries(saved.dates).some(([id, date]) => !ids.has(id) || typeof date !== 'string' || !validDate(date))) throw new Error('invalid plan');
      plan = {version: 1, schoolId: saved.schoolId, completed: [...new Set(saved.completed)], dates: {...saved.dates}};
      chosen = plan.schoolId;
    } catch {
      corrupt = true;
      notice('展示資料版本不符、內容損壞或參考學校暫時無法載入。原資料未覆寫；請先重設展示資料，或稍後重新載入。');
    }
  }
  function persist() {
    if (corrupt) return;
    try {
      localStorage.setItem(KEY, JSON.stringify(plan));
      memoryOnly = false;
      notice('展示進度已保存在這個瀏覽器。這是個人手動紀錄，不會送至校方或正式帳號。');
    } catch {
      memoryOnly = true;
      notice('無法保存至瀏覽器。本次變更僅暫存在此頁，重新整理後可能遺失；請勿把它當成已保存。');
    }
  }
  function scopedTask(task) {
    if (task.source === 'lincoln' && plan.schoolId !== 'school-0') {
      return {...task, source: null, detail: '此目標校的當期要求與來源待確認。請依母校提名信及目的校正式通知核對；本項僅為準備提醒。'};
    }
    return task;
  }
  function nextTask() {
    for (let index = 0; index < content.stages.length; index++) {
      const task = content.stages[index].tasks.find((item) => !plan.completed.includes(item.id));
      if (task) return {task: scopedTask(task), index};
    }
    return null;
  }
  function renderSchools() {
    const query = $('#school-search').value.trim().toLocaleLowerCase();
    const visible = content.schools.filter((school) => `${school.name} ${school.country}`.toLocaleLowerCase().includes(query));
    $('#school-count').textContent = `顯示 ${visible.length} / ${content.schools.length} 所歷史參考校`;
    $('#schools').innerHTML = visible.length ? visible.map((school) => `<article class="school-card">
      <p class="country">${esc(school.country)} / REFERENCE</p><h3>${esc(school.name)}</h3><p class="micro">${esc(school.status)}</p>
      <details><summary>申請條件與來源</summary><dl>
        <dt>學院／學制（快照參考）</dt><dd>${esc(school.colleges || '待確認')} / ${esc(school.degree_levels || '待確認')}</dd>
        <dt>研修期間（快照參考）</dt><dd>${esc(school.study_period || '待確認')}</dd>
        <dt>語言與資格（非當期確認）</dt><dd>${esc(school.eligibility || '待確認')}${school.eligibility?.includes('...') ? '［快照文字截斷，完整條件待確認］' : ''}</dd>
        <dt>歷史名額（不是當期名額）</dt><dd>${esc(school.reference_quota || '未收錄')}；當期名額待確認</dd>
        <dt>歷史申請日（不是個人截止日）</dt><dd>${esc(school.reference_deadline || '未收錄')}；適用學期待確認</dd>
      </dl>${external(school.source_url, '長庚資料來源 ↗', 'source-link')}${external(school.website, '合作校官方網站 ↗', 'source-link')}<p class="micro">快照擷取：${esc(content.snapshot_at?.slice(0,10) || '待確認')}；本次未逐筆核實。不以勾選待辦判定符合資格。</p></details>
      <button class="secondary" data-school="${esc(school.id)}" ${plan ? 'disabled' : ''}>${school.id === chosen ? '已選為研究目標 ✓' : '作為研究目標'}</button>
      </article>`).join('') : `<div class="empty-panel"><h3>${content.schools.length ? '沒有符合的參考學校' : '參考學校暫時無法載入'}</h3><p>${content.schools.length ? '試試其他校名或國家。' : '仍可閱讀官方申請資訊；暫時無法建立選校計畫。'}</p>${sourceLink('partners','查看長庚官方學校資訊 ↗')}</div>`;
    $('#schools').querySelectorAll('[data-school]').forEach((button) => button.addEventListener('click', () => {
      chosen = button.dataset.school;
      renderSchools(); renderPlanControls();
      announce('已選為研究目標，接著可載入示範計畫。');
      $('#chosen-school').scrollIntoView({block: 'center'});
      // Preserve keyboard focus when replacing the list.
      $(`[data-school="${chosen}"]`)?.focus({preventScroll:true});
    }));
  }
  function renderPlanControls() {
    const school = content.schools.find((item) => item.id === (plan?.schoolId || chosen));
    $('#chosen-school').textContent = school ? `研究目標：${school.name}${plan ? '。若要換校，請先重設展示資料。' : ''}` : '研究目標尚未選擇';
    document.querySelectorAll('[data-open-plan]').forEach((button) => {
      button.textContent = plan ? '繼續我的示範計畫' : '載入示範計畫';
      button.disabled = !plan && (corrupt || !school);
    });
    $('#blank-plan').hidden = !!plan;
    $('#blank-plan').disabled = corrupt || !school;
  }
  function startPlan(blank = false) {
    if (!plan) {
      if (corrupt || !content.schools.some((school) => school.id === chosen)) return;
      plan = {version:1, schoolId:chosen, completed:blank ? [] : ['read-guide', 'shortlist'], dates:{}};
      persist();
    }
    viewedStage = nextTask()?.index ?? 0;
    renderSchools(); renderPlanControls(); renderJourney();
    location.hash = 'journey';
    showPanel();
    announce(memoryOnly ? '展示計畫已載入，僅暫存在此頁。' : '展示計畫已載入，進度只存在此瀏覽器。');
  }
  function renderJourney() {
    $('#plan-empty').hidden = !!plan;
    $('#plan-content').hidden = !plan;
    $('#reset').disabled = !plan && !corrupt;
    if (!plan) return;
    const school = content.schools.find((item) => item.id === plan.schoolId);
    $('#plan-school').textContent = school?.name || '研究目標待確認';
    const next = nextTask();
    $('#current-stage').textContent = next ? `目前待辦階段 ${String(next.index + 1).padStart(2,'0')} / ${content.stages[next.index].title}` : '展示清單已完成';
    $('#next-task').textContent = next ? next.task.title : '準備紀錄完成，仍請核對官方通知';
    $('#next-detail').textContent = next ? next.task.detail : '所有待辦皆已手動勾選。這不代表資格核准、正式送件、錄取或學分抵免通過。';
    $('#go-next').hidden = !next;
    $('#progress-label').textContent = `${plan.completed.length} / ${allTasks().length} 項完成`;
    $('#progress').max = allTasks().length; $('#progress').value = plan.completed.length;
    $('#stage-nav').innerHTML = content.stages.map((stage,index) => {
      const count = stage.tasks.filter((task) => plan.completed.includes(task.id)).length;
      return `<button data-stage="${index}" ${index === viewedStage ? 'aria-current="step"' : ''}><span class="stage-num">${String(index+1).padStart(2,'0')}</span><span><strong>${esc(stage.title)}</strong><small>${count} / ${stage.tasks.length} 完成${next?.index === index ? '・目前待辦' : ''}</small></span></button>`;
    }).join('');
    $('#stage-nav').querySelectorAll('button').forEach((button) => button.addEventListener('click', () => {
      viewedStage = Number(button.dataset.stage); renderJourney();
      $(`[data-stage="${viewedStage}"]`).focus({preventScroll:true});
    }));
    const stage = content.stages[viewedStage];
    $('#stage-content').innerHTML = `<span class="badge">階段 ${String(viewedStage+1).padStart(2,'0')}・個人手動紀錄</span><h2>${esc(stage.title)}</h2><p>${esc(stage.description)}</p>${stage.source === 'lincoln' && plan.schoolId !== 'school-0' ? '<span class="micro">目的校當期流程與官方來源待確認</span>' : sourceLink(stage.source)}${stage.tasks.map(scopedTask).map((task) => `<div class="task ${plan.completed.includes(task.id) ? 'complete' : ''}">
      <div class="task-top"><input type="checkbox" id="task-${esc(task.id)}" data-task="${esc(task.id)}" ${stale ? 'disabled' : ''} ${plan.completed.includes(task.id) ? 'checked' : ''} aria-describedby="detail-${esc(task.id)}"><label for="task-${esc(task.id)}">${esc(task.title)}</label></div>
      <p id="detail-${esc(task.id)}">${esc(task.detail)}</p>${task.source ? sourceLink(task.source) : '<span class="recommendation">個人準備建議・正式要求待確認</span>'}
      <div class="target-date"><label for="date-${esc(task.id)}">個人目標日期（非官方期限）</label><input id="date-${esc(task.id)}" type="date" min="2000-01-01" max="2099-12-31" data-date="${esc(task.id)}" ${stale ? 'disabled' : ''} value="${esc(plan.dates[task.id] || '')}"></div></div>`).join('')}`;
    $('#stage-content').querySelectorAll('[data-task]').forEach((checkbox) => checkbox.addEventListener('change', () => {
      if (stale) return;
      const id = checkbox.dataset.task;
      plan.completed = checkbox.checked ? [...new Set([...plan.completed,id])] : plan.completed.filter((item) => item !== id);
      persist(); renderJourney();
      $(`#task-${id}`).focus({preventScroll:true});
      announce(`待辦已更新。${nextTask() ? `下一步：${nextTask().task.title}` : '展示清單已完成，仍需核對官方通知。'}`);
    }));
    $('#stage-content').querySelectorAll('[data-date]').forEach((input) => input.addEventListener('change', () => {
      if (stale) return;
      input.setCustomValidity('');
      if (!validDate(input.value) || !input.validity.valid) { input.setCustomValidity('請選擇 2000 至 2099 年間的有效日期'); input.reportValidity(); return; }
      input.setCustomValidity('');
      if (input.value) plan.dates[input.dataset.date] = input.value; else delete plan.dates[input.dataset.date];
      persist(); announce('個人目標日期已更新，不是官方截止日。');
    }));
  }
  function showPanel() {
    if (!content) return;
    const raw = location.hash.slice(1);
    const section = ['journey','sources','future'].includes(raw) ? raw : 'explore';
    document.querySelectorAll('.page-panel').forEach((panel) => { panel.hidden = panel.id !== section; });
    document.querySelectorAll('.site-header nav a').forEach((link) => {
      if (link.hash === `#${section}`) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
    });
    if (raw === 'school-list') { $('#school-list').scrollIntoView(); return; }
    // Internal page navigation lands on the heading for keyboard/screen reader users.
    $(`#${section}-title`).setAttribute('tabindex','-1');
    $(`#${section}-title`).focus({preventScroll:true});
    window.scrollTo(0,0);
  }
  async function load() {
    $('#loading').hidden = false; $('#load-error').hidden = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/demo/content', {credentials:'omit', signal:controller.signal, cache:'no-store'});
      if (!response.ok) throw new Error('unavailable');
      const result = await response.json();
      if (result.version !== 1 || !Array.isArray(result.stages) || result.stages.length !== 6 || !Array.isArray(result.schools) || !Array.isArray(result.sources) || !Array.isArray(result.rules)) throw new Error('invalid content');
      content = result;
      chosen = content.schools[0]?.id || '';
      readPlan();
      $('#rules').innerHTML = content.rules.map((rule) => `<article class="rule-card"><h3>${esc(rule.title)}</h3><p>${esc(rule.body)}</p>${sourceLink(rule.source)}</article>`).join('');
      $('#source-list').innerHTML = content.sources.map((source) => `<article class="source-card"><span class="badge">公開官方來源</span><h2>${esc(source.title)}</h2><p>實際讀取查核：${esc(source.checked_on || '待確認')}（台北時間）；不是校方背書。</p><p>${esc(source.scope)}</p>${external(source.url,source.url,'url')}</article>`).join('') + `<article class="source-card"><span class="badge">既有資料・歷史參考</span><h2>UniWay 長庚選校快照</h2><p>快照擷取：${esc(content.snapshot_at?.slice(0,10) || '無可用快照')}；本展示顯示 ${content.schools.length} 所參考校。不等於本期開放或已確認名額。</p><p>學校條件與歷史名額在「交換探索」逐校展開；當期學期、資格、名額與期限仍待確認。</p>${sourceLink('partners')}</article>`;
      renderSchools(); renderPlanControls(); renderJourney(); showPanel();
    } catch {
      content = null;
      document.querySelectorAll('.page-panel').forEach((panel) => { panel.hidden = true; });
      $('#load-error').hidden = false;
    } finally { clearTimeout(timeout); $('#loading').hidden = true; }
  }
  document.querySelectorAll('[data-open-plan]').forEach((button) => button.addEventListener('click', () => startPlan()));
  $('#blank-plan').addEventListener('click', () => startPlan(true));
  $('#school-search').addEventListener('input', renderSchools);
  $('#retry').addEventListener('click', load);
  $('#go-next').addEventListener('click', () => {
    const next = nextTask(); if (!next) return;
    viewedStage = next.index; renderJourney();
    $(`#task-${next.task.id}`).focus();
  });
  $('#reset').addEventListener('click', () => { $('#reset-dialog').showModal(); $('#cancel-reset').focus(); });
  $('#cancel-reset').addEventListener('click', () => $('#reset-dialog').close());
  $('#confirm-reset').addEventListener('click', () => {
    try { localStorage.removeItem(KEY); }
    catch { notice('瀏覽器拒絕刪除展示儲存，重設未完成。請允許儲存後重試，或在瀏覽器設定刪除本站展示資料。'); $('#reset-dialog').close(); return; }
    plan = null; corrupt = false; memoryOnly = false; stale = false; viewedStage = 0;
    chosen = content.schools[0]?.id || '';
    $('#reset-dialog').close();
    notice('展示資料已重設。可重新載入固定情境，其他 UniWay 儲存未變更。');
    renderSchools(); renderPlanControls(); renderJourney();
    $('#plan-empty [data-open-plan]').focus();
  });
  window.addEventListener('hashchange', showPanel);
  window.addEventListener('storage', (event) => {
    if (event.key === KEY || event.key === null) {
      notice('另一個分頁已變更或移除展示資料。請重新整理載入最新進度，避免覆寫。');
      // Stop stale writes until the user reloads.
      corrupt = true; stale = true;
      document.querySelectorAll('[data-task],[data-date]').forEach((input) => { input.disabled = true; });
      renderPlanControls();
    }
  });
  load();
})();

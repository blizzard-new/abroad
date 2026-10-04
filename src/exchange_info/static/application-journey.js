/* Shared student preparation desk. Data lives in the account workspace. */
window.UniWayJourney = (() => {
  let settingsOwner = "";
  let editorKey = "";
  let pendingDocument = null;
  let focusRevision = 0;

  function sanitizeAvailability(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const weekly = Number(value.weekly_hours);
    const days = [...new Set((Array.isArray(value.weekdays) ? value.weekdays : []).map(Number))].filter(day=>Number.isInteger(day) && day >= 1 && day <= 7).sort();
    const horizon = Number(value.horizon_days || 180);
    if (!Number.isFinite(weekly) || weekly < 0.5 || weekly > 60 || !days.length || !Number.isInteger(horizon) || horizon < 1 || horizon > 365) return null;
    return {weekly_hours:weekly, weekdays:days, horizon_days:horizon};
  }

  const ownerKey = () => JSON.stringify([state.account?.id || "", activeHomeSchool()]);
  const tasks = () => [...window.UniWayMultiPlan.workRows(), ...state.calendarEvents.filter(row=>!row.generatedFromEventId && (row.preparationDays > 0 || row.effortHours != null || row.dependsOn?.length))];
  const hoursLabel = value => Number(value || 0).toLocaleString("zh-TW", {maximumFractionDigits:2});
  const action = row => row?.documentId && (row.documentTargetSchool || applicationTemplateById(row.documentId))
    ? `<button type="button" class="text-action" data-journey-document="${escapeHtml(row.documentId)}" data-journey-document-school="${escapeHtml(row.documentTargetSchool || "")}">繼續填寫</button>` : "";

  function renderEditors(rows) {
    const container = document.querySelector("#journey-task-editors");
    const key = JSON.stringify([ownerKey(), rows, state.applicationTemplates.map(item=>item.id)]);
    if (key === editorKey || container.contains(document.activeElement)) return;
    editorKey = key;
    container.innerHTML = rows.length ? rows.map(row=>`<details class="journey-task-row" data-journey-task-row="${escapeHtml(row.id)}">
      <summary><strong>${escapeHtml(row.title)}</strong><small>${escapeHtml(row.schoolName || "共用準備")} · ${escapeHtml(row.date)} · ${row.waitingReason ? "等待中" : ({todo:"待開始",preparing:"準備中",ready:"已完成"}[row.status] || "待開始")} · ${row.effortHours != null ? `${hoursLabel(row.effortHours)} 小時` : "工時待設定"}</small></summary>
      <form class="journey-task-editor" data-journey-task="${escapeHtml(row.id)}">
        <label><span>預估工作時數</span><input name="effort_hours" type="number" min="0.1" max="1000" step="0.1" value="${row.effortHours ?? ""}" placeholder="例如 3" required /></label>
        <label><span>剩餘工作時數（可留空）</span><input name="remaining_hours" type="number" min="0" max="1000" step="0.1" value="${row.remainingHours ?? ""}" placeholder="未開始可留空" /></label>
        <label><span>前置任務（可複選）</span><select name="depends_on" multiple aria-label="${escapeHtml(row.title)}前置任務">${rows.filter(other=>other.id !== row.id).map(other=>`<option value="${escapeHtml(other.id)}" ${(row.dependsOn || []).includes(other.id) ? "selected" : ""}>${escapeHtml(other.title)}</option>`).join("")}</select><small>只有前置工作完成後才安排這一項。循環關係會提示修正。</small></label>
        <label><span>對應文件</span><select name="document_id"><option value="">不連結文件</option>${state.applicationTemplates.map(template=>`<option value="${escapeHtml(template.id)}" ${row.documentId === template.id ? "selected" : ""}>${escapeHtml(template.short_title || template.title)}</option>`).join("")}</select></label>
        <label><span>最早可開始日期（可留空）</span><input name="available_from" type="date" value="${escapeHtml(row.availableFrom || "")}" /></label>
        <label><span>等待原因（等待中暫不排工作）</span><input name="waiting_reason" maxlength="240" value="${escapeHtml(row.waitingReason || "")}" placeholder="例如：等系辦確認表格" /></label>
        <label><span>工作進度</span><select name="status">${[["todo","待開始"],["preparing","準備中"],["ready","已完成"]].map(([value,label])=>`<option value="${value}" ${row.status === value ? "selected" : ""}>${label}</option>`).join("")}</select><small>完成工作不代表已送件、校方受理或錄取。</small></label>
        <button type="submit" class="secondary-button">保存這項工作並重排</button>
      </form></details>`).join("") : '<p class="workspace-empty">先從官方時程建立準備任務，或到日曆加入自己的任務並設定準備天數。</p>';
  }

  function render() {
    window.UniWayMultiPlan?.render();
    const root = document.querySelector("#journey-workspace");
    if (!root) return;
    root.hidden = !calendarTaskFeatureEnabled();
    window.UniWayApplicationWorkspace?.render();
    if (root.hidden) { pendingDocument = null; settingsOwner = ""; editorKey = ""; return; }
    const rows = tasks();
    const form = document.querySelector("#journey-availability-form");
    const owner = ownerKey();
    const settingsKey = JSON.stringify([owner, state.planningAvailability]);
    if (settingsOwner !== settingsKey && !form.contains(document.activeElement)) {
      const settings = state.planningAvailability || {weekly_hours:6, weekdays:[1,3,6], horizon_days:180};
      form.elements.weekly_hours.value = settings.weekly_hours;
      form.elements.horizon_days.value = settings.horizon_days;
      form.querySelectorAll('[name="weekdays"]').forEach(input=>input.checked = settings.weekdays.includes(Number(input.value)));
      settingsOwner = settingsKey;
    }
    renderEditors(rows.filter(row=>!row.fromApplicationPlan));
    const report = state.calendarTaskScheduleReport;
    const sessions = report?.mode === "workload" ? report.work_sessions || [] : [];
    const today = sessions.filter(row=>row.date === localDateKey());
    const waiting = rows.filter(row=>row.status !== "ready" && row.waitingReason);
    document.querySelector("#journey-today").innerHTML = `<article><strong>今天可以做什麼</strong>${today.length ? `<ul>${today.map(session=>{const row = rows.find(item=>item.id === session.event_id);return `<li>${escapeHtml(row?.title || "準備工作")} · ${hoursLabel(session.hours)} 小時 ${action(row)}</li>`;}).join("")}</ul>` : `<p>${state.calendarTaskScheduleLoading ? "正在更新安排…" : state.planningAvailability ? "今天沒有可執行的工作安排，查看下面的日期或阻礙事項。" : "先設定每週可投入時間與各項工作時數，系統會安排今天與後續的工作。"}</p>`}</article>
      <article><strong>正在等待 ${waiting.length} 項</strong>${waiting.length ? `<ul>${waiting.map(row=>`<li>${escapeHtml(row.title)}：${escapeHtml(row.waitingReason)}</li>`).join("")}</ul>` : '<p>目前沒有記錄等待事項。等校方或他人回覆時，可在任務內填寫原因。</p>'}</article>`;
    const result = document.querySelector("#journey-schedule-result");
    if (state.calendarTaskScheduleLoading) { result.innerHTML = '<p role="status">正在依可用時間與前置關係重新安排…</p>'; return; }
    if (state.calendarTaskScheduleError) { result.innerHTML = `<p>${escapeHtml(state.calendarTaskScheduleError)}</p><button type="button" class="secondary-button" data-journey-retry>重新嘗試</button>`; return; }
    if (!state.planningAvailability) { result.innerHTML = '<p>目前沿用準備天數倒推。設定可投入時間後，才會產生逐日工作安排。</p>'; return; }
    if (report?.mode !== "workload") { result.innerHTML = '<p>尚無可安排的工作，加入任務後會依你的時間設定計算。</p>'; return; }
    const allIssues = report.issues || [];
    const suggestedCount = allIssues.filter(issue=>issue.code === "suggested_effort").length;
    const issues = allIssues.filter(issue=>issue.code !== "suggested_effort");
    const sessionMarkup = session => { const row = rows.find(item=>item.id === session.event_id); return `<div class="journey-session"><time>${escapeHtml(session.date)}</time><strong>${escapeHtml(row?.title || "準備工作")}</strong><span>${hoursLabel(session.hours)} 小時 ${action(row)}</span></div>`; };
    result.innerHTML = `<strong>你的工作安排 · ${report.analyzed_event_count} 項工作</strong><p>依剩餘工時重新計算；同一天的前置工作會先安排。官方期限與已完成狀態不會被修改。</p>
      ${suggestedCount ? `<p class="journey-suggested-note">${suggestedCount} 項工作先用系統建議的工時安排（通用估計，不是校方規定）；到各項工作的「安排工時與文件」填入實際時數後會重新計算。</p>` : ""}${issues.length ? `<ul class="journey-issue-list">${issues.map(issue=>`<li><strong>${escapeHtml(rows.find(row=>row.id === issue.event_id)?.title || issue.event_id)}</strong>：${escapeHtml(issue.detail)}</li>`).join("")}</ul>` : ""}
      <div class="journey-sessions">${sessions.slice(0,8).map(sessionMarkup).join("") || '<p>目前沒有可以安排的工作，請先處理上方的阻礙。</p>'}</div>
      ${sessions.length > 8 ? `<details class="journey-more-sessions"><summary>查看其餘 ${sessions.length - 8} 個工作安排</summary><div class="journey-sessions">${sessions.slice(8).map(sessionMarkup).join("")}</div></details>` : ""}`;
    initIcons();
  }

  function openDocument(templateId) {
    if (!requireAccountForPrivateAction("登入後繼續填寫這份文件。")) return;
    const template = applicationTemplateById(templateId);
    if (!template) { announce("這份文件尚未載入，請先核對適用的目標與年度。", "info"); return; }
    pendingDocument = {templateId, owner:ownerKey()};
    const route = `#application-form=${encodeURIComponent(templateId)}`;
    if (window.location.hash === route) renderApplicationFormPage(template);
    else window.location.hash = route;
  }

  function focusDocumentGap(template) {
    if (!pendingDocument || pendingDocument.templateId !== template.id || pendingDocument.owner !== ownerKey()) return;
    window.UniWayDocumentWorkbench?.select("edit");
    const revision = ++focusRevision;
    const field = template.fields.find(item=>item.required && !applicationFieldHasValue(template, item));
    // Both hashchange and popstate can render this route. Focus the settled
    // field tree rather than a node replaced by the second route render.
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      if (revision !== focusRevision || !pendingDocument || pendingDocument.owner !== ownerKey()
        || window.location.hash !== `#application-form=${encodeURIComponent(template.id)}`) return;
      const input = field ? document.querySelector(`#application-document-fields [data-application-field="${CSS.escape(field.id)}"]`) : document.querySelector("#application-document-fields input, #application-document-fields textarea, #application-document-fields select");
      if (input) { input.focus(); input.scrollIntoView({block:"center", behavior:window.UniWayMotion?.reduced ? "instant" : "smooth"}); }
      pendingDocument = null;
    }));
  }

  function bind() {
    window.UniWayMultiPlan?.bind();
    // Glass/animated page containers create stacking contexts. Account dialogs
    // belong to the viewport so the navigation cannot cover their controls.
    document.querySelectorAll(".account-dialog").forEach(dialog=>document.body.append(dialog));
    document.querySelector("#journey-availability-form").addEventListener("submit", async event=>{
      event.preventDefault();
      if (!calendarTaskFeatureEnabled()) return;
      const form = event.currentTarget;
      if (!form.reportValidity()) return;
      const values = new FormData(form);
      const settings = sanitizeAvailability({weekly_hours:values.get("weekly_hours"), weekdays:values.getAll("weekdays"), horizon_days:values.get("horizon_days")});
      const message = document.querySelector("#journey-settings-status");
      if (!settings) { message.textContent = "請至少選一個可準備的星期，並填寫有效時數。"; return; }
      state.planningAvailability = settings;
      persistAccountWorkspaceLocally();
      scheduleAccountWorkspaceSync();
      message.textContent = "可用時間已保存，正在重新安排。";
      await loadCalendarTaskSchedule();
      render();
    });
    document.querySelector("#journey-task-editors").addEventListener("submit", async event=>{
      const form = event.target.closest("[data-journey-task]");
      if (!form) return;
      event.preventDefault();
      if (!calendarTaskFeatureEnabled() || !form.reportValidity()) return;
      const row = state.calendarEvents.find(item=>item.id === form.dataset.journeyTask);
      if (!row) return;
      const values = new FormData(form);
      const doc = String(values.get("document_id") || "");
      if (doc && !applicationTemplateById(doc)) return;
      Object.assign(row, {effortHours:Number(values.get("effort_hours")), remainingHours:values.get("remaining_hours") === "" ? null : Number(values.get("remaining_hours")), dependsOn:values.getAll("depends_on").map(String), availableFrom:String(values.get("available_from") || ""), waitingReason:String(values.get("waiting_reason") || "").trim(), documentId:doc, status:String(values.get("status"))});
      editorKey = "";
      document.activeElement?.blur();
      persistCalendarEvents();
      render();
      announce("工作設定已保存，依剩餘工時重新安排。", "success");
    });
    document.addEventListener("click", async event=>{
      const documentButton = event.target.closest("[data-journey-document]");
      if (documentButton) {
        if (documentButton.closest("#notification-dialog") && typeof closeNotificationDialog === "function") closeNotificationDialog();
        const owner=ownerKey(), school=documentButton.dataset.journeyDocumentSchool;
        if (school && school !== state.applicationContext.target_school) await selectPlanningTarget(school);
        if (owner !== ownerKey() || school && school !== state.applicationContext.target_school) return;
        openDocument(documentButton.dataset.journeyDocument);
      }
      if (event.target.closest("[data-journey-retry]")) loadCalendarTaskSchedule();
    });
  }
  return {sanitizeAvailability, render, bind, openDocument, focusDocumentGap};
})();

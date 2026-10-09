/* One saved preference order and one preparation checklist across schools. */
window.UniWayMultiPlan = (() => {
  let loadedKey = "", loadingKey = "", loadedPlan = null, formKey = "", requestId = 0;
  let tasksKey = "";
  let inputKey = "";
  let scheduleKey = "";
  const owner = () => JSON.stringify([state.account?.id || "", activeHomeSchool()]);
  function payload() {
    const profile = state.eligibilityProfile || {}, context = state.applicationContext;
    return {home_school:activeHomeSchool(), college:profile.college || context.college || null,
      department:profile.department || context.department || null, degree_level:profile.degree || context.degree_level || null,
      academic_score:profile.academicScore ?? null, language_test:profile.languageTest || null,
      language_score:profile.languageScore ?? null, academic_year:context.academic_year || profile.academicYear || null,
      application_round:context.application_round || profile.applicationRound || null,
      preferences:[...state.applications].map((school_name,index)=>({rank:index+1,school_name, ...(activeHomeSchool() === "國立中央大學" ? {document_preparation_state:ncuDocumentState(school_name,context.academic_year || profile.academicYear,context.application_round || profile.applicationRound)} : {})}))};
  }
  const bucket = task => task.task_scope === "home" ? activeHomeSchool() : task.school_names[0];
  function sanitizeSettings(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    const number = (value, min) => value != null && value !== "" && Number.isFinite(Number(value)) && Number(value) >= min && Number(value) <= 1000 ? Number(value) : null;
    const day = value => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) && parseLocalDate(value) ? value : null;
    return Object.fromEntries(Object.entries(value).slice(0,500).filter(([key,row])=>key.startsWith("application-task-") && row && typeof row === "object" && !Array.isArray(row)).map(([key,row])=>[key, {
      status:["todo","preparing","ready"].includes(row.status) ? row.status : "todo",
      effort_hours:number(row.effort_hours, 0.000001), remaining_hours:number(row.remaining_hours,0),
      depends_on:Array.isArray(row.depends_on) ? [...new Set(row.depends_on.map(String))].slice(0,30) : null,
      available_from:day(row.available_from), personal_due_date:day(row.personal_due_date),
      waiting_reason:String(row.waiting_reason || "").slice(0,240) || null,
      document_id:String(row.document_id || "").slice(0,180) || null,
      document_target_school:String(row.document_target_school || "").slice(0,200) || null,
    }]));
  }
  const currentPlan = () => loadedKey === JSON.stringify([owner(),payload()]) ? loadedPlan : null;
  const settingsFor = task => state.preparationTasks[task.id] || {status:state.applicationProgress[bucket(task)]?.[task.id] ? "ready" : "todo"};
  // The matching tool comes from the step's own document names; a student's
  // explicit choice always wins over it.
  function suggestedTemplate(task) {
    // Templates belong to the home school; opening one from a partner task first
    // switches the planning target through the existing confirmation flow.
    const id = (task.document_link?.template_ids || []).find(value=>applicationTemplateById(value));
    return id ? applicationTemplateById(id) : null;
  }
  function workRows() {
    return (currentPlan()?.tasks || []).map(task=>{
      const settings=settingsFor(task), official=task.official_deadline_at?.slice(0,10);
      const dates=[official,settings.personal_due_date].filter(Boolean).sort();
      const suggested=settings.document_id ? null : suggestedTemplate(task);
      return {id:task.id, title:task.title, schoolName:bucket(task), date:dates[0] || "", status:settings.status,
        effortHours:settings.effort_hours ?? null, remainingHours:settings.remaining_hours,
        suggestedEffortHours:task.suggested_effort_hours ?? null,
        dependsOn:settings.depends_on ?? task.dependency_ids ?? [], availableFrom:settings.available_from,
        waitingReason:settings.waiting_reason, documentId:settings.document_id || suggested?.id || "",
        documentTargetSchool:settings.document_id ? settings.document_target_school : suggested && task.task_scope !== "home" ? task.school_names[0] : "",
        documentSuggested:Boolean(suggested), preparationDays:0, fromApplicationPlan:true,
        estimated:task.task_origin === "reference_year"};
    });
  }
  function scheduleRequest() {
    const plan=currentPlan();
    return plan && state.planningAvailability ? {plan:payload(), availability:state.planningAvailability,
      task_settings:Object.fromEntries(plan.tasks.map(task=>[task.id,settingsFor(task)]))} : null;
  }
  function taskEditor(task, tasks) {
    const settings=settingsFor(task), dependencies=settings.depends_on ?? task.dependency_ids ?? [];
    const canLink=task.task_scope === "home" || task.school_names.includes(state.applicationContext.target_school);
    return `<details class="multi-task-settings" data-multi-editor="${escapeHtml(task.id)}"><summary>安排工時與文件</summary>
      <p>${task.official_deadline_at ? `來源記載期限：${escapeHtml(task.official_deadline_at.slice(0,10))}；準備安排以日期為單位，送件時間仍須核對原公告。` : "尚無可採用的官方期限，可先安排個人準備。"}</p>
      <form class="journey-task-editor" data-multi-settings="${escapeHtml(task.id)}">
        <label><span>預估工作時數</span><input name="effort_hours" type="number" min="0.1" max="1000" step="0.1" value="${settings.effort_hours ?? ""}" ${task.suggested_effort_hours ? `placeholder="系統建議約 ${task.suggested_effort_hours} 小時" ` : "required "}/>${task.suggested_effort_hours ? `<small>留空會先用系統建議的 ${task.suggested_effort_hours} 小時（依文件數量與類型的通用估計，不是校方規定）。</small>` : ""}</label>
        <label><span>剩餘工作時數（可留空）</span><input name="remaining_hours" type="number" min="0" max="1000" step="0.1" value="${settings.remaining_hours ?? ""}" /></label>
        <label><span>個人完成目標（非官方期限）</span><input name="personal_due_date" type="date" value="${escapeHtml(settings.personal_due_date || "")}" /><small>可留空，依預覽期間安排；有官方期限時，個人目標不能把它往後移。</small></label>
        <label><span>最早開始日</span><input name="available_from" type="date" value="${escapeHtml(settings.available_from || "")}" /></label>
        <label><span>前置任務（可複選）</span><select name="depends_on" multiple>${tasks.filter(row=>row.id !== task.id).map(row=>`<option value="${escapeHtml(row.id)}" ${dependencies.includes(row.id) ? "selected" : ""}>${escapeHtml(row.title)} · ${escapeHtml(bucket(row))}</option>`).join("")}${dependencies.filter(id=>!tasks.some(row=>row.id === id)).map(id=>`<option value="${escapeHtml(id)}" selected>待核對的前置任務：${escapeHtml(id)}</option>`).join("")}</select><small>來源明確記載的前置關係會帶入；其他關係由你設定。</small></label>
        <label><span>等待原因</span><input name="waiting_reason" maxlength="240" value="${escapeHtml(settings.waiting_reason || "")}" placeholder="等待回覆時暫不排工作" /></label>
        <label><span>工作進度</span><select name="status">${[["todo","待開始"],["preparing","準備中"],["ready","已完成"]].map(([value,label])=>`<option value="${value}" ${settings.status === value ? "selected" : ""}>${label}</option>`).join("")}</select></label>
        <label><span>對應文件</span><select name="document_id" ${!canLink ? "disabled" : ""}><option value="">${suggestedTemplate(task) && !settings.document_id ? `使用系統建議：${escapeHtml(suggestedTemplate(task).short_title || suggestedTemplate(task).title)}` : "不連結文件"}</option>${canLink && settings.document_id && settings.document_target_school !== state.applicationContext.target_school ? `<option value="__retain__" selected>保留已連結文件 · ${escapeHtml(settings.document_target_school || "校內")}</option>` : ""}${canLink ? state.applicationTemplates.map(row=>`<option value="${escapeHtml(row.id)}" ${settings.document_id === row.id && settings.document_target_school === state.applicationContext.target_school ? "selected" : ""}>${escapeHtml(row.short_title || row.title)}</option>`).join("") : ""}</select><small>${canLink ? "連結目前目標校及年度載入的文件。" : "先以此校準備文件，再選擇適用表格；既有連結仍保留。"}</small></label>
        <button type="submit" class="secondary-button">保存並重新安排</button>
      </form></details>`;
  }
  function documentLine(task) {
    const link = task.document_link, settings = settingsFor(task);
    if (!link || (!link.requirement_names?.length && !link.template_ids?.length)) return "";
    const chosen = settings.document_id ? applicationTemplateById(settings.document_id) : null;
    const tool = chosen || suggestedTemplate(task);
    const school = settings.document_id ? settings.document_target_school || "" : task.task_scope === "home" ? "" : task.school_names[0];
    const button = tool ? `<button type="button" class="text-action" data-journey-document="${escapeHtml(tool.id)}" data-journey-document-school="${escapeHtml(school || "")}">${chosen ? "繼續填寫" : "開啟"}「${escapeHtml(tool.short_title || tool.title)}」</button>` : "";
    const missing = (link.unmapped_requirement_names || []).length ? `<small>需自備、尚無填寫工具：${link.unmapped_requirement_names.map(escapeHtml).join("、")}</small>` : "";
    const names = link.requirement_names?.length ? `<details class="multi-plan-documents"><summary>這項要準備的文件（${link.requirement_names.length}）</summary><ul>${link.requirement_names.map(name=>`<li>${escapeHtml(name)}</li>`).join("")}</ul>${missing}<small>對應工具是依文件名稱比對；是否符合校方要求仍須核對來源。</small></details>` : "";
    return `<div class="multi-plan-document-line">${button}${names}</div>`;
  }
  const sourceLink = urls => {
    const url = (urls || []).find(value=>typeof value === "string" && /^https?:\/\//i.test(value));
    return url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">核對來源</a>` : "";
  };
  function renderTasks(plan) {
    const list = document.querySelector("#multi-plan-tasks");
    const tasks = plan.tasks || [];
    const key=JSON.stringify([loadedKey, state.preparationTasks, state.applicationProgress, state.applicationContext.target_school, state.applicationTemplates]);
    if (tasksKey === key || list.querySelector("form:focus-within")) return;
    tasksKey=key;
    const open=[...list.querySelectorAll("details[open]")].map(row=>row.dataset.multiEditor || row.dataset.multiSchool);
    const markup = rows => rows.map(task=>`<li class="multi-plan-task">
      <label><input type="checkbox" data-multi-task="${escapeHtml(task.id)}" ${settingsFor(task).status === "ready" ? "checked" : ""} /><span><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(task.phase)} · ${escapeHtml(task.responsible_unit)}${task.task_origin === "reference_year" ? ` · <b class="multi-plan-estimate-badge">預估，非官方期限</b>` : ""}</small></span></label>
      <p>${escapeHtml(task.detail)}</p>${task.task_scope === "home" ? `<small>共用於 ${task.school_names.length} 個志願</small>` : ""}
      ${documentApplicabilityMarkup(task.document_applicability)}${documentLine(task)}${sourceLink(task.source_urls)}${taskEditor(task,tasks)}</li>`).join("");
    const shared = tasks.filter(task=>task.task_scope === "home");
    list.innerHTML = `<p>勾選只記錄個人的準備進度；不代表正式送件、校方受理或錄取。來源或規定不同的工作會分開顯示。</p>
      ${shared.length ? `<section class="multi-plan-shared"><h3>共用的校內準備 · ${shared.length} 項</h3><ul>${markup(shared)}</ul></section>` : '<p class="workspace-empty">目前沒有能確認為共用的步驟，保留各校清單以便核對。</p>'}
      ${plan.choices.map(choice=>{const rows=tasks.filter(task=>task.task_scope === "partner" && task.school_names.includes(choice.school_name));return `<details class="multi-plan-branch" data-multi-school="${escapeHtml(choice.school_name)}"><summary><span>第 ${choice.rank} 志願 · ${escapeHtml(choice.school_name)}</span><small>${escapeHtml(applicationPlanStatusMeta(choice.status).label)}</small></summary><p>${escapeHtml(choice.summary)}</p>${choice.checks.filter(check=>check.status !== "pass").length ? `<ul class="multi-plan-checks">${choice.checks.filter(check=>check.status !== "pass").map(check=>`<li><strong>${escapeHtml(check.title)}</strong>：${escapeHtml(check.detail)}</li>`).join("")}</ul>` : ""}<ul>${markup(rows)}</ul>${!rows.length ? '<p>目前沒有可建立的工作項目；請先核對上方的年度、梯次或流程缺口，再安排正式時程。</p>' : ""}<button type="button" class="secondary-button" data-planning-target="${escapeHtml(choice.school_name)}" ${["ineligible","unavailable"].includes(choice.status) ? "disabled" : ""}>${state.applicationContext.target_school === choice.school_name ? "繼續此校規劃" : "以此校準備文件與時程"}</button></details>`;}).join("")}`;
    list.querySelectorAll("details").forEach(row=>{ row.open=open.includes(row.dataset.multiEditor || row.dataset.multiSchool); });
  }
  function render() {
    const root = document.querySelector("#multi-plan-workspace");
    if (!root) return;
    root.hidden = !state.account;
    if (root.hidden) { loadedKey=""; loadedPlan=null; loadingKey=""; formKey=""; tasksKey=""; inputKey=""; scheduleKey=""; requestId++; return; }
    const input = payload(), key = JSON.stringify([owner(),input]);
    if (inputKey !== key) {
      inputKey=key; tasksKey="";
      state.calendarTaskScheduleReport=null;
      scheduleCalendarTaskAnalysis();
      renderCalendarTaskScheduleCenter(); renderApplicationCalendar();
    }
    const form = document.querySelector("#multi-plan-preferences");
    const currentFormKey = JSON.stringify([owner(), [...state.applications], state.dashboard?.partner_universities.map(row=>row.school_name)]);
    if (formKey !== currentFormKey && !form.contains(document.activeElement)) {
      formKey = currentFormKey;
      const schools=(state.dashboard?.partner_universities || []).filter(row=>(row.availability_status || "open") === "open" || (activeHomeSchool() === "國立中央大學" && partnerAvailabilityMeta(row).pending));
      const saved=[...state.applications];
      const names=[...new Set([...schools.map(row=>row.school_name),...saved])];
      form.querySelectorAll("select").forEach((select,index)=>{
        select.innerHTML=`<option value="">${index ? "暫不設定" : "請選擇學校"}</option>${names.map(name=>`<option value="${escapeHtml(name)}">${escapeHtml(name)}${activeHomeSchool() === "國立中央大學" && partnerAvailabilityMeta(partnerByName(name)).pending ? " · 本期名額待公告" : ""}</option>`).join("")}`;
        select.value=saved[index] || "";
      });
    }
    const status=document.querySelector("#multi-plan-status");
    form.querySelectorAll("select, button").forEach(control=>control.disabled = !state.dashboard);
    if (!state.dashboard) {
      status.textContent="正在載入本校合作校，完成後即可設定志願。";
      document.querySelector("#multi-plan-tasks").replaceChildren();
      return;
    }
    if (!input.preferences.length) { status.textContent="從候選學校確認志願，這裡會整理成同一份準備清單。"; document.querySelector("#multi-plan-tasks").replaceChildren(); return; }
    if (input.preferences.length > 5) { status.textContent="目前保留超過 5 所學校；請確認本次最多 5 個志願，原有任務與進度仍保留。"; document.querySelector("#multi-plan-tasks").replaceChildren(); return; }
    if (loadedKey === key && loadedPlan) {
      status.textContent=`${input.preferences.length} 個志願 · ${loadedPlan.tasks?.length || 0} 項準備工作`;
      const signature=JSON.stringify([key,state.planningAvailability,state.preparationTasks,state.applicationProgress,state.calendarEvents]);
      if (signature !== scheduleKey) { scheduleKey=signature; scheduleCalendarTaskAnalysis(); }
      renderTasks(loadedPlan); return;
    }
    if (loadingKey === key || !state.dashboard) return;
    loadingKey=key; const sequence=++requestId;
    status.textContent="正在整理各校與共用步驟…";
    document.querySelector("#multi-plan-tasks").replaceChildren();
    fetchJson("/application-plan/evaluate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(input)})
      .then(plan=>{
        if (sequence !== requestId || key !== JSON.stringify([owner(),payload()])) return;
        loadedKey=key; loadedPlan=plan; loadingKey=""; tasksKey=""; render();
      }).catch(error=>{
        if (sequence !== requestId || key !== JSON.stringify([owner(),payload()])) return;
        loadingKey=""; status.textContent=error.message;
        document.querySelector("#multi-plan-tasks").innerHTML='<button type="button" class="secondary-button" data-multi-retry>重新整理清單</button>';
      }).finally(()=>{ if (sequence === requestId && loadingKey === key) loadingKey=""; });
  }
  function bind() {
    document.querySelector("#multi-plan-preferences").addEventListener("submit",event=>{
      event.preventDefault(); if (!requireAccountForPrivateAction("登入後保存志願。")) return;
      const values=[...event.currentTarget.querySelectorAll("select")].map(input=>input.value).filter(Boolean);
      if (!values.length || new Set(values).size !== values.length) { document.querySelector("#multi-plan-status").textContent="至少選一所學校，同一所學校不能重複。"; return; }
      state.applications=new Set(values);
      state.personalApplicationPlan=null;
      loadedKey=""; loadedPlan=null;
      persistAccountWorkspaceLocally(); scheduleAccountWorkspaceSync();
      renderEligibilityOptions({preserveDraft:true});
      render(); announce("志願順序已保存，既有任務與準備進度仍保留。","success");
    });
    document.querySelector("#multi-plan-tasks").addEventListener("change",event=>{
      const input=event.target.closest("[data-multi-task]"); if (!input || !state.account) return;
      if (loadedKey !== JSON.stringify([owner(),payload()])) return;
      const task=loadedPlan?.tasks.find(row=>row.id === input.dataset.multiTask); if (!task) return;
      const key=bucket(task);
      state.applicationProgress[key]={...(state.applicationProgress[key] || {}),[task.id]:input.checked};
      state.preparationTasks[task.id]={...settingsFor(task), status:input.checked ? "ready" : "todo"};
      persistAccountWorkspaceLocally(); scheduleAccountWorkspaceSync();
      scheduleCalendarTaskAnalysis();
    });
    document.querySelector("#multi-plan-tasks").addEventListener("submit",event=>{
      const form=event.target.closest("[data-multi-settings]");
      if (!form) return;
      event.preventDefault();
      if (!state.account || !form.reportValidity()) return;
      const task=currentPlan()?.tasks.find(row=>row.id === form.dataset.multiSettings);
      if (!task) return;
      const values=new FormData(form), previous=settingsFor(task);
      const canLink=task.task_scope === "home" || task.school_names.includes(state.applicationContext.target_school);
      const selection=canLink ? String(values.get("document_id") || "") : "__retain__";
      const retaining=selection === "__retain__";
      const selected=retaining ? previous.document_id : selection;
      if (selected && !retaining && !applicationTemplateById(selected)) return;
      state.preparationTasks[task.id]={
        status:String(values.get("status")), effort_hours:values.get("effort_hours") === "" ? null : Number(values.get("effort_hours")),
        remaining_hours:values.get("remaining_hours") === "" ? null : Number(values.get("remaining_hours")),
        depends_on:values.getAll("depends_on").map(String),
        personal_due_date:String(values.get("personal_due_date") || "") || null,
        available_from:String(values.get("available_from") || "") || null,
        waiting_reason:String(values.get("waiting_reason") || "").trim() || null,
        document_id:selected || null,
        document_target_school:retaining ? previous.document_target_school || null : selected ? state.applicationContext.target_school || null : null,
      };
      const key=bucket(task);
      state.applicationProgress[key]={...(state.applicationProgress[key] || {}),[task.id]:state.preparationTasks[task.id].status === "ready"};
      document.activeElement?.blur();
      persistAccountWorkspaceLocally(); scheduleAccountWorkspaceSync();
      scheduleCalendarTaskAnalysis(); render();
      announce("工作進度與時數已保存，正在更新同一份準備安排。","success");
    });
    document.querySelector("#multi-plan-tasks").addEventListener("click",event=>{if(event.target.closest("[data-multi-retry]")) render();});
  }
  return {render,bind,sanitizeSettings,workRows,scheduleRequest};
})();

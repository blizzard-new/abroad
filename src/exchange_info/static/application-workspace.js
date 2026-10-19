/* One application workspace; existing URLs retain their individual destinations.
   The heading is the student's map: where they are, which steps are behind them, and the one thing to do next. */
window.UniWayApplicationWorkspace = (() => {
  const groups = [
    {id:"selection", label:"選校與確認", hint:"填條件、挑學校", summary:"填寫條件，選出想去的學校並核對資格", icon:"school", href:"#advisor", pages:["advisor", "favorites", "eligibility"], links:[["advisor","條件與推薦"],["favorites","候選與比較"],["eligibility","當期資格與志願"]]},
    {id:"preparation", label:"準備與時程", hint:"排時程、追期限", summary:"依官方期限，排好每項準備的時間", icon:"route", href:"#overview", pages:["overview", "calendar", "deadlines", "budget", "scholarships"], links:[["overview","我的準備"],["calendar","日曆"],["deadlines","官方期限"],["budget","預算"],["scholarships","補助"]]},
    {id:"documents", label:"文件與送件", hint:"填表、檢查、列印", summary:"逐份填寫文件，檢查後列印，再依校方方式送件", icon:"folder-check", href:"#application-center", pages:["application-center", "application-form", "document-check", "documents", "writing-assistant"], links:[["application-center","填寫與列印"],["document-check","檢查文件"],["documents","官方說明與私人文件"]]},
  ];
  const statusLabels = {done:"已完成", next:"建議下一步", todo:"尚未開始"};
  // The month view must fit the first screen, and a document being filled needs the student's full attention.
  const quietPages = ["calendar", "application-form"];
  let root, context, navigation, next, activePage = null, toolsGroup = null, validationFrame = 0, nextKey = "";

  function syncConditions() {
    const form = document.querySelector("#advisor-form");
    const eligibility = activePage === "eligibility";
    const parent = document.querySelector(eligibility ? "#eligibility .eligibility-layout" : "#advisor .advisor-layout");
    if (form.parentElement !== parent) parent.prepend(form);
    form.dataset.mode = eligibility ? "eligibility" : "advisor";
    // Qualification is optional while exploring, but must be visible when checking eligibility.
    if (eligibility) document.querySelector("#advisor-qualification-fields").open = true;
    const period = document.querySelector("#application-period-fields");
    period.hidden = !eligibility;
    period.disabled = !eligibility;
    ["college", "department", "degree", "academic-score", "language-test"].forEach(id=>{
      document.querySelector(`#advisor-${id}`).required = eligibility;
    });
    renderAdvisorAccessState();
  }

  function init() {
    const first = document.querySelector("#overview");
    if (!first || root) return;
    root = document.createElement("section");
    root.id = "application-workspace";
    root.setAttribute("aria-label", "我的申請工作區");
    root.hidden = true;
    first.before(root);
    root.innerHTML = `<header class="application-workspace-heading glass-panel">
      <div class="application-workspace-context"><div><span class="section-kicker">我的申請 · 共 3 步</span><strong id="application-workspace-stage-summary"></strong></div><p id="application-workspace-context" aria-live="polite"></p></div>
      <nav id="application-journey-steps" class="application-workspace-stages" aria-label="申請三步驟">${groups.map((group,index)=>`<a href="${group.href}" data-workspace-stage="${group.id}" data-stage-status="todo" data-requires-home-school aria-label="${group.label}" aria-describedby="application-stage-${group.id}-note"><span class="application-stage-number" aria-hidden="true">${index + 1}</span><span class="application-stage-copy"><span>${group.label}</span><small>${group.hint}</small></span><span id="application-stage-${group.id}-note" class="visually-hidden" data-stage-status-label>${group.hint}（${statusLabels.todo}）</span></a>`).join("")}</nav>
      <div id="planning-next-action" class="planning-next-action" aria-live="polite" hidden></div>
      <details id="application-workspace-tool-menu" class="application-tool-menu"><summary><span id="application-workspace-tool-label"></span><span>本階段其他頁面<i data-lucide="chevron-down" aria-hidden="true"></i></span></summary><nav id="application-workspace-tools" class="application-workspace-tools" aria-label="本階段的頁面"></nav></details>
    </header>`;
    context = root.querySelector("#application-workspace-context");
    navigation = root.querySelector("#application-workspace-tools");
    next = root.querySelector("#planning-next-action");
    next.addEventListener("click", event=>{
      const button = event.target.closest("[data-next-action-focus]");
      if (button) focusOnPage(button.dataset.nextActionFocus);
    });
    document.querySelector("#advisor-form").addEventListener("invalid", event=>{
      // Native validation must be able to focus invalid fields inside optional sections.
      for (let parent = event.target.parentElement; parent; parent = parent.parentElement) {
        if (parent.tagName === "DETAILS") parent.open = true;
      }
      // Chromium can try to focus before the newly opened details has a layout.
      // Focus the first invalid field once, after layout, even if several are invalid.
      if (!validationFrame) validationFrame = requestAnimationFrame(()=>{
        validationFrame = 0;
        document.querySelector("#advisor-form input:invalid, #advisor-form select:invalid, #advisor-form textarea:invalid")?.focus();
      });
    }, true);
    groups.flatMap(group=>group.pages).forEach(id=>{
      const page = document.querySelector(`[data-university-page="${id}"]`);
      if (page) root.append(page); // Keep the same forms, listeners and unfinished input.
    });
    const planning = document.querySelector("#planning-workspace");
    const legacy = document.createElement("details");
    legacy.id = "planning-deadline-settings";
    legacy.className = "journey-settings planning-deadline-settings";
    legacy.innerHTML = '<summary>依官方期限預留準備天數<i data-lucide="calendar-range" aria-hidden="true"></i></summary>';
    planning.before(legacy);
    legacy.append(planning);
    planning.querySelector("#planning-title").textContent = "依期限預留準備天數";
    render();
  }

  function show(page) {
    activePage = page;
    render();
  }

  function render() {
    if (!root) return;
    syncConditions();
    root.dataset.page = activePage || "";
    const group = groups.find(item=>item.pages.includes(activePage));
    root.hidden = !group;
    if (!group) { context.textContent = ""; navigation.replaceChildren(); delete navigation.dataset.route; return; }
    const profile = state.eligibilityProfile;
    const year = state.applicationContext.academic_year || profile?.academicYear;
    const round = state.applicationContext.application_round || profile?.applicationRound;
    const target = state.applicationContext.target_school;
    context.textContent = [activeHomeSchool(), year && `${year} 學年度`, round, target && `文件與時程目標：${target}`].filter(Boolean).join(" · ");
    root.querySelector("#application-workspace-stage-summary").textContent = `第 ${groups.indexOf(group) + 1} 步：${group.summary}`;
    // Before the catalogue loads there is nothing to judge progress by.
    const action = state.dashboard ? planningNextAction() : null;
    renderStages(action);
    renderNext(action);
    root.querySelectorAll("[data-workspace-stage]").forEach(link=>{
      if (link.dataset.workspaceStage === group.id) link.setAttribute("aria-current","step");
      else link.removeAttribute("aria-current");
    });
    // Do not replace links on every workspace sync while a keyboard user is on one.
    const key = `${group.id}:${activePage}`;
    if (navigation.dataset.route !== key) {
      navigation.dataset.route = key;
      const links = activePage === "application-form" ? [["application-center", "返回文件清單與列印包"]] : group.links;
      const menu = root.querySelector("#application-workspace-tool-menu");
      // Keep the tools open while switching within a stage; a new stage starts simply.
      if (toolsGroup !== group.id) menu.open = false;
      toolsGroup = group.id;
      root.querySelector("#application-workspace-tool-label").textContent = `這一頁：${links.find(([id])=>id === activePage)?.[1]
        || (activePage === "application-form" ? "填寫文件" : "寫作協助")}`;
      navigation.innerHTML = links.map(([id,label])=>`<a href="#${id}" data-requires-home-school${id === activePage ? ' aria-current="page"' : ""}>${label}</a>`).join("");
      if (typeof initIcons === "function") initIcons();
    }
    const legacy = document.querySelector("#planning-deadline-settings");
    // Deadline planning remains directly reachable even with advanced workload tools closed.
    const advanced = document.querySelector("#application-schedule-details");
    advanced.hidden = document.querySelector("#journey-workspace").hidden;
    if (legacy.nextElementSibling !== advanced) advanced.before(legacy);
  }

  // Steps before the recommended one are behind the student; the documents step is done once every form is ready.
  function renderStages(action) {
    const nextIndex = action ? groups.findIndex(item=>item.id === action.stage) : -1;
    let changed = false;
    root.querySelectorAll("[data-workspace-stage]").forEach((link, index)=>{
      const done = nextIndex > index || (groups[index].id === "documents" && action?.documentsDone);
      const status = done ? "done" : index === nextIndex ? "next" : "todo";
      if (link.dataset.stageStatus === status) return;
      link.dataset.stageStatus = status;
      link.querySelector(".application-stage-number").innerHTML = done ? '<i data-lucide="check" aria-hidden="true"></i>' : String(index + 1);
      link.querySelector("[data-stage-status-label]").textContent = `${groups[index].hint}（${statusLabels[status]}）`;
      changed = true;
    });
    if (changed && typeof initIcons === "function") initIcons();
  }

  function renderNext(action) {
    const quiet = !action || quietPages.includes(activePage);
    next.hidden = quiet;
    if (quiet) return;
    const key = JSON.stringify([action, activePage]);
    if (key === nextKey) return;
    nextKey = key;
    const index = groups.findIndex(item=>item.id === action.stage);
    // A link to the page the student is already on would do nothing; take them to the spot instead.
    const here = action.href === `#${activePage}` && action.focus;
    const button = action.planning
      ? '<button type="button" class="primary-button" data-open-planning>預覽準備時程<i data-lucide="arrow-right" aria-hidden="true"></i></button>'
      : here
        ? `<button type="button" class="primary-button" data-next-action-focus="${escapeHtml(action.focus)}">就在這一頁，開始<i data-lucide="arrow-down" aria-hidden="true"></i></button>`
        : `<a class="primary-button" href="${action.href}">${escapeHtml(action.label)}<i data-lucide="arrow-right" aria-hidden="true"></i></a>`;
    const browse = action.browse && groups[0].pages.includes(activePage) ? '<a class="text-action" href="#partners" data-requires-home-school>還沒有方向？先逛交換學校<i data-lucide="arrow-right" aria-hidden="true"></i></a>' : "";
    next.innerHTML = `<span class="next-action-icon"><i data-lucide="${action.icon}" aria-hidden="true"></i></span><div><small>現在，先做這一件事 · 第 ${index + 1} 步「${groups[index].label}」</small><strong>${escapeHtml(action.title)}</strong><p>${escapeHtml(action.detail)}</p></div><div class="next-action-buttons">${button}${browse}</div>`;
    if (typeof initIcons === "function") initIcons();
  }

  function focusOnPage(selector) {
    const target = document.querySelector(selector);
    if (!target) return;
    const field = target.matches("input, select, textarea") ? target
      : target.querySelector("input:invalid:not([disabled]), select:invalid:not([disabled]), textarea:invalid:not([disabled])");
    const focusable = field || target;
    for (let parent = focusable.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === "DETAILS") parent.open = true;
    }
    if (!field && !target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
    focusable.scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block:"center"});
    focusable.focus({preventScroll:true});
  }

  function openDeadlineSettings() {
    const details = document.querySelector("#planning-deadline-settings");
    if (details) details.open = true;
  }
  return {init, show, render, openDeadlineSettings};
})();

/* One application workspace; existing URLs retain their individual destinations. */
window.UniWayApplicationWorkspace = (() => {
  const groups = [
    {id:"selection", label:"選校與確認", icon:"school", href:"#advisor", pages:["advisor", "favorites", "eligibility"], links:[["advisor","條件與推薦"],["favorites","候選與比較"],["eligibility","當期資格與志願"]]},
    {id:"preparation", label:"準備與時程", icon:"route", href:"#overview", pages:["overview", "calendar", "deadlines", "budget", "scholarships"], links:[["overview","我的準備"],["calendar","日曆"],["deadlines","官方期限"],["budget","預算"],["scholarships","補助"]]},
    {id:"documents", label:"文件與送件", icon:"folder-check", href:"#application-center", pages:["application-center", "application-form", "document-check", "documents", "writing-assistant"], links:[["application-center","填寫與列印"],["document-check","檢查文件"],["documents","官方說明與私人文件"]]},
  ];
  let root, context, navigation, activePage = null, toolsGroup = null, validationFrame = 0;

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
      <div class="application-workspace-context"><div><span class="section-kicker">我的申請</span><strong>從找學校到備齊文件，一步一步完成</strong></div><p id="application-workspace-context" aria-live="polite"></p></div>
      <nav id="application-journey-steps" class="application-workspace-stages" aria-label="申請工作區階段">${groups.map((group,index)=>`<a href="${group.href}" data-workspace-stage="${group.id}" data-requires-home-school><span class="application-stage-number" aria-hidden="true">${index + 1}</span><span>${group.label}</span></a>`).join("")}</nav>
      <details id="application-workspace-tool-menu" class="application-tool-menu"><summary><span id="application-workspace-tool-label"></span><span>切換工具<i data-lucide="chevron-down" aria-hidden="true"></i></span></summary><nav id="application-workspace-tools" class="application-workspace-tools" aria-label="本階段的頁面"></nav></details>
    </header>`;
    context = root.querySelector("#application-workspace-context");
    navigation = root.querySelector("#application-workspace-tools");
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
      root.querySelector("#application-workspace-tool-label").textContent = links.find(([id])=>id === activePage)?.[1]
        || (activePage === "application-form" ? "填寫文件" : "寫作協助");
      navigation.innerHTML = links.map(([id,label])=>`<a href="#${id}" data-requires-home-school${id === activePage ? ' aria-current="page"' : ""}>${label}</a>`).join("");
      if (typeof initIcons === "function") initIcons();
    }
    const legacy = document.querySelector("#planning-deadline-settings");
    // Deadline planning remains directly reachable even with advanced workload tools closed.
    const advanced = document.querySelector("#application-schedule-details");
    advanced.hidden = document.querySelector("#journey-workspace").hidden;
    if (legacy.nextElementSibling !== advanced) advanced.before(legacy);
  }

  function openDeadlineSettings() {
    const details = document.querySelector("#planning-deadline-settings");
    if (details) details.open = true;
  }
  return {init, show, render, openDeadlineSettings};
})();

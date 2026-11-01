/* My applications (#overview): a flat task board over the student's real data.
   Rows are the preparation tasks of the saved preferences (UniWayMultiPlan.workRows), plus personal calendar
   entries; the stat strip, preferences and deadlines read the same state the rest of the app uses. */
window.UniWayTracker = (() => {
  "use strict";
  const VIEW_KEY = "uniway-tracker-view-v1";
  const GROUPS = [
    { status: "preparing", title: "進行中" },
    { status: "todo", title: "待辦" },
    { status: "ready", title: "已完成" },
  ];
  const VIEWS = [["list", "list-checks", "列表"], ["board", "layers", "看板"], ["timeline", "calendar-range", "時程"]];
  let view = "list", schoolFilter = "", scheduled = 0;
  try { view = VIEWS.some(([id]) => id === localStorage.getItem(VIEW_KEY)) ? localStorage.getItem(VIEW_KEY) : "list"; } catch (_) { view = "list"; }

  const root = () => document.querySelector("#my-applications");
  const pad = (value) => String(value).padStart(2, "0");
  // Catalogue names pair the Chinese name with the English one; the chip keeps the part a student recognises.
  const shortName = (name) => truncate(String(name || "").replace(/\s+[A-Za-z].*$/, ""), 12);
  const shortDate = (key) => { const date = parseLocalDate(key); return date ? `${date.getMonth() + 1}/${pad(date.getDate())}` : ""; };

  function taskRows() {
    const rows = [];
    let plan = [];
    try { plan = window.UniWayMultiPlan?.workRows?.() || []; } catch (_) { plan = []; }
    plan.forEach((task) => rows.push({ key: task.id, title: task.title, status: ["todo", "preparing", "ready"].includes(task.status) ? task.status : "todo", school: task.schoolName || "", date: task.date || "", plan: true }));
    (state.calendarEvents || []).filter((event) => event.origin !== "official" && event.title && parseLocalDate(event.date)).forEach((event) => {
      rows.push({ key: `event-${event.id || `${event.title}-${event.date}`}`, title: event.title, status: "todo", school: event.schoolName || "", date: event.date, plan: false });
    });
    rows.sort((a, b) => (a.date || "9999").localeCompare(b.date || "9999") || a.title.localeCompare(b.title, "zh-Hant"));
    rows.forEach((row, index) => { row.number = `UW-${pad(index + 1)}`; });
    return rows;
  }

  function priority(row) {
    if (row.status === "ready" || !row.date) return { icon: "layers", tone: "normal", label: "一般" };
    const days = calendarDaysUntil(row.date);
    if (days !== null && days <= 7) return { icon: "clock-alert", tone: "urgent", label: "緊急" };
    if (days !== null && days <= 21) return { icon: "flag", tone: "high", label: "優先" };
    return { icon: "layers", tone: "normal", label: "一般" };
  }

  function dueHtml(row) {
    if (!row.date) return "";
    const days = calendarDaysUntil(row.date);
    return `<small class="due${row.status !== "ready" && days !== null && days <= 7 ? " soon" : ""}">${shortDate(row.date)}</small>`;
  }

  function rowHtml(row) {
    const level = priority(row);
    const ring = row.plan
      ? `<button type="button" class="pr-ring ${row.status}" role="checkbox" aria-checked="${row.status === "ready"}" aria-label="${escapeHtml(row.title)}：${row.status === "ready" ? "已完成，點擊改回待辦" : "標記為已完成"}" data-tracker-toggle="${escapeHtml(row.key)}"></button>`
      : `<span class="pr-ring ${row.status}" aria-hidden="true"></span>`;
    return `<li class="pr-task ${row.status}" data-tracker-row>
      <span class="pr-prio ${level.tone}" title="${level.label}"><i data-lucide="${level.icon}" aria-hidden="true"></i><span class="visually-hidden">${level.label}</span></span>
      <code>${row.number}</code>${ring}
      <span class="pr-task-title">${escapeHtml(row.title)}</span>
      ${row.school ? `<span class="pr-task-chip">${escapeHtml(shortName(row.school))}</span>` : ""}${dueHtml(row)}</li>`;
  }

  function listHtml(rows) {
    return GROUPS.map((group) => {
      const items = rows.filter((row) => row.status === group.status);
      return `<section class="pr-group ${group.status}" aria-label="${group.title}"><header><i data-lucide="chevron-down" aria-hidden="true"></i><span class="pr-ring ${group.status}" aria-hidden="true"></span><strong>${group.title}</strong><small>${items.length}</small></header>${items.length ? `<ul>${items.map(rowHtml).join("")}</ul>` : '<p class="pr-group-empty">沒有任務</p>'}</section>`;
    }).join("");
  }

  function boardHtml(rows) {
    return `<div class="pr-kanban">${GROUPS.map((group) => {
      const items = rows.filter((row) => row.status === group.status);
      return `<section class="pr-column ${group.status}" aria-label="${group.title}"><header><span class="pr-ring ${group.status}" aria-hidden="true"></span><strong>${group.title}</strong><small>${items.length}</small></header><ul>${items.map((row) => `<li class="pr-card"><code>${row.number}</code><span>${escapeHtml(row.title)}</span><footer>${row.school ? `<span class="pr-task-chip">${escapeHtml(shortName(row.school))}</span>` : ""}${dueHtml(row)}</footer></li>`).join("") || '<li class="pr-group-empty">沒有任務</li>'}</ul></section>`;
    }).join("")}</div>`;
  }

  function timelineHtml(rows) {
    const dated = rows.filter((row) => row.date);
    if (!dated.length) return '<p class="pr-group-empty pr-pad">還沒有排上日期的任務。</p>';
    const byMonth = new Map();
    dated.forEach((row) => { const month = row.date.slice(0, 7); byMonth.set(month, [...(byMonth.get(month) || []), row]); });
    return [...byMonth].map(([month, items]) => `<section class="pr-group"><header><strong>${month.replace("-", " / ")}</strong><small>${items.length}</small></header><ul>${items.map(rowHtml).join("")}</ul></section>`).join("");
  }

  function emptyHtml() {
    if (!state.account) return `<div class="pr-empty"><i data-lucide="log-in" aria-hidden="true"></i><div><strong>登入後，這裡會列出你的準備任務</strong><p>把學校加入志願，系統會整理成同一份任務清單，並記錄你的進度。</p></div><button type="button" class="pr-navy-button" data-tracker-login>登入</button></div>`;
    if (window.UniWayPlanIndex?.current()?.items?.length) return `<div class="pr-empty"><div><strong>繼續上方的申請計畫</strong><p>這裡可安排額外待辦與個人時程。</p></div><button type="button" data-tracker-add>新增待辦</button></div>`;
    if (!state.applications.size) return `<div class="pr-empty"><i data-lucide="bookmark" aria-hidden="true"></i><div><strong>還沒有志願</strong><p>先到「找交換學校」把想去的學校加入志願，任務就會出現在這裡。</p></div><a class="pr-navy-button" href="#partners">找交換學校</a></div>`;
    return `<div class="pr-empty"><i data-lucide="loader-circle" aria-hidden="true"></i><div><strong>正在整理你的準備任務</strong><p>完成後會依期限與狀態分組顯示。</p></div></div>`;
  }

  function statsHtml(rows) {
    const done = rows.filter((row) => row.status === "ready").length;
    let next = null;
    try { next = upcomingDeadlines(1)[0] || null; } catch (_) { next = null; }
    const days = next ? calendarDaysUntil(localDateKey(next.date)) : null;
    const docs = state.dashboard ? documentChecklistItems() : [];
    const missing = docs.filter((item) => readinessStatus(item.id) !== "ready").length;
    const picks = state.applications.size;
    const cells = [
      { label: "已完成任務", value: rows.length ? `${done} / ${rows.length}` : "—", pct: rows.length ? done / rows.length : 0, tone: "navy" },
      { label: "下一個截止", value: next ? `${shortDate(localDateKey(next.date))} ${truncate(next.scope || next.title, 8)}` : "—", pct: days === null ? 0 : Math.max(0.08, 1 - Math.min(days, 60) / 60), tone: "coral" },
      { label: "我的志願", value: picks ? `${picks} 間` : "—", pct: Math.min(1, picks / 5), tone: "blue" },
      { label: "待補文件", value: docs.length ? `${missing} 份` : "—", pct: docs.length ? missing / docs.length : 0, tone: "amber" },
    ];
    return cells.map((cell) => `<div class="pr-stat ${cell.tone}"><small>${cell.label}</small><strong>${escapeHtml(cell.value)}</strong><span class="bar"><span style="width:${Math.round(cell.pct * 100)}%"></span></span></div>`).join("");
  }

  function picksHtml() {
    const names = [...state.applications];
    const rows = names.map((name, index) => {
      const item = partnerByName(name);
      if (!item) return "";
      const match = partnerMatch(item);
      const ok = match.tone === "strong";
      const chip = state.eligibilityProfile ? `<span class="pr-pick-state ${ok ? "ok" : "warn"}">${ok ? "符合資格" : escapeHtml(truncate(match.label, 8))}</span>` : "";
      return `<li><span class="pr-rank">${index + 1}</span><span class="pr-pick-name"><strong>${escapeHtml(item.school_name)}</strong><small>${escapeHtml([item.country, item.location?.city].filter(Boolean).join("・"))}</small></span>${chip}</li>`;
    }).join("");
    return `<section class="pr-side-card"><header><strong>我的志願</strong><a href="#favorites">調整順序</a></header>${rows ? `<ol>${rows}</ol>` : '<p class="pr-group-empty pr-pad">還沒有志願。</p>'}</section>`;
  }

  function deadlinesHtml() {
    let list = [];
    try { list = upcomingDeadlines(3); } catch (_) { list = []; }
    const items = list.map((event, index) => {
      const key = localDateKey(event.date), days = calendarDaysUntil(key);
      return `<li><span class="pr-date ${index === 0 ? "hot" : ""}"><small>${event.date.getMonth() + 1}月</small><strong>${pad(event.date.getDate())}</strong></span><span class="pr-deadline-copy"><strong>${escapeHtml(truncate(event.title, 26))}</strong><small>${days === 0 ? "就是今天" : `還有 ${days} 天`}</small></span></li>`;
    }).join("");
    return `<section class="pr-side-card pr-pad"><strong>接下來的期限</strong>${items ? `<ol class="pr-deadlines">${items}</ol>` : '<p class="pr-group-empty">目前沒有已確認的官方期限。</p>'}</section>`;
  }

  function render() {
    scheduled = 0;
    const host = root();
    if (!host || !state.dashboard) return;
    window.UniWayPlanIndex?.refresh();
    const all = taskRows();
    host.dataset.empty = String(all.length === 0);
    host.dataset.signedOut = String(!state.account);
    const rows = schoolFilter ? all.filter((row) => row.school === schoolFilter) : all;
    const term = state.eligibilityProfile?.targetTerm ? targetTermLabel(state.eligibilityProfile.targetTerm) : "";
    host.querySelector("#tracker-pill").textContent = [term, activeHomeSchool()].filter(Boolean).join(" · ");
    host.querySelectorAll("[data-tracker-view]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.trackerView === view)));
    const filter = host.querySelector("#tracker-filter");
    const schools = [...new Set(all.map((row) => row.school).filter(Boolean))];
    if (filter.dataset.options !== schools.join("|")) {
      filter.dataset.options = schools.join("|");
      filter.innerHTML = `<option value="">全部學校</option>${schools.map((name) => `<option>${escapeHtml(name)}</option>`).join("")}`;
    }
    filter.value = schools.includes(schoolFilter) ? schoolFilter : "";
    host.querySelector("#tracker-stats").innerHTML = statsHtml(all);
    const main = host.querySelector("#tracker-main");
    const body = !all.length ? emptyHtml() : view === "board" ? boardHtml(rows) : view === "timeline" ? timelineHtml(rows) : listHtml(rows);
    main.querySelector("#tracker-body").innerHTML = body;
    host.querySelector("#tracker-side").innerHTML = picksHtml() + deadlinesHtml();
    initIcons();
  }

  function schedule() { if (!scheduled) scheduled = window.requestAnimationFrame(render); }

  function addTask() {
    window.addEventListener("hashchange", () => window.requestAnimationFrame(() => {
      const panel = document.querySelector("#calendar-quick-add");
      if (panel) { panel.open = true; panel.querySelector("input, select")?.focus(); }
    }), { once: true });
    window.location.hash = "#calendar";
  }

  document.addEventListener("click", (event) => {
    const host = root();
    if (!host || !host.contains(event.target)) return;
    const viewButton = event.target.closest("[data-tracker-view]");
    if (viewButton) {
      view = viewButton.dataset.trackerView;
      try { localStorage.setItem(VIEW_KEY, view); } catch (_) { /* the view still switches for this visit */ }
      render();
      return;
    }
    if (event.target.closest("#tracker-add, [data-tracker-add]")) { addTask(); return; }
    if (event.target.closest("[data-tracker-login]")) { openAuthDialog("login"); return; }
    const toggle = event.target.closest("[data-tracker-toggle]");
    if (toggle) {
      const checkbox = document.querySelector(`[data-multi-task="${CSS.escape(toggle.dataset.trackerToggle)}"]`);
      if (checkbox) checkbox.click();
      else announce("這項任務要在下方「我的志願與共用準備」更新。", "info");
      window.setTimeout(render, 60);
    }
  });
  document.addEventListener("change", (event) => {
    if (event.target.id !== "tracker-filter") return;
    schoolFilter = event.target.value;
    render();
  });
  document.addEventListener("keydown", (event) => {
    const host = root();
    if (!host || host.closest("[hidden]") || event.metaKey || event.ctrlKey || event.altKey) return;
    if (event.target.closest?.("input, textarea, select, [contenteditable]") || document.querySelector('[aria-modal="true"]:not([hidden]), dialog[open]')) return;
    if (event.key.toLowerCase() === "c") { event.preventDefault(); addTask(); }
    else if (event.key.toLowerCase() === "f") { event.preventDefault(); host.querySelector("#tracker-filter")?.focus(); }
  });

  return { render: schedule };
})();

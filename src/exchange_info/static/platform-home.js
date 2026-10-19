/* Home landing (#home): product story, supported schools, plan collage, partner map and the five tool tiles.
   Nothing on the page is a fixed sample: every school, count, date, document and amount comes from the loaded
   catalogue and, when someone is signed in, from their own saved data. app.js calls UniWayHome.render() whenever
   the school, dashboard, account or saved schools change. */
window.UniWayHome = (() => {
  "use strict";
  const LAND_URL = "/static/assets/home/world-land.json?v=20261015-redesign-1";
  const STAGES = ["找到想去的學校", "準備校內甄選", "完成合作校申請", "安排出發與生活"];
  // The student's own "目前階段" decides how many steps are behind them.
  const STAGE_PROGRESS = { exploring: 0, preparing: 1, submitted: 2, accepted: 3, abroad: 4, returned: 4 };
  const TAIWAN = [121.56, 25.04];
  const MAX_ARCS = 22;
  let land = null, landPromise = null, scheduled = 0, lastKey = "";

  const root = () => document.querySelector("#home-landing");
  const formatNumber = (value) => Number(value || 0).toLocaleString("en-US");

  function loadLand() {
    landPromise ||= fetch(LAND_URL).then((response) => {
      if (!response.ok) throw new Error("map outline unavailable");
      return response.json();
    }).then((data) => { land = data; render(); }).catch(() => { landPromise = null; });
    return landPromise;
  }

  function project(lon, lat) {
    // d3.geoNaturalEarth1, matching scripts/build_home_world_map.py.
    const shifted = ((lon - land.center + 540) % 360) - 180;
    const lam = shifted * Math.PI / 180, phi = lat * Math.PI / 180;
    const p2 = phi * phi, p4 = p2 * p2;
    const x = lam * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)));
    const y = phi * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)));
    return [land.width / 2 + x * land.scale, land.top - y * land.scale];
  }

  function partnerCities() {
    const dashboard = state.dashboard;
    if (!dashboard?.partner_universities) return [];
    const cities = new Map();
    for (const item of dashboard.partner_universities) {
      const place = item.location;
      if (place?.geocode_status !== "verified" || !Number.isFinite(place.latitude) || !Number.isFinite(place.longitude)) continue;
      const key = `${place.latitude.toFixed(1)},${place.longitude.toFixed(1)}`;
      const entry = cities.get(key) || { lon: place.longitude, lat: place.latitude, weight: 0 };
      entry.weight += 1;
      cities.set(key, entry);
    }
    return [...cities.values()].sort((a, b) => b.weight - a.weight);
  }

  function mapSvg(cities) {
    const [tx, ty] = project(...TAIWAN);
    const arcs = cities.filter((city) => city.weight >= 2).slice(0, MAX_ARCS);
    for (const city of cities) if (arcs.length < 8 && !arcs.includes(city)) arcs.push(city);
    const arcPaths = arcs.map((city) => {
      const [x, y] = project(city.lon, city.lat);
      const mx = (tx + x) / 2, my = (ty + y) / 2 - Math.hypot(x - tx, y - ty) * 0.28;
      return `<path d="M${tx.toFixed(1)} ${ty.toFixed(1)}Q${mx.toFixed(1)} ${my.toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)}"/>`;
    }).join("");
    const dots = cities.map((city) => {
      const [x, y] = project(city.lon, city.lat);
      const r = (1.6 + Math.min(city.weight, 6) * 0.9) * 1.5;
      return `<circle class="halo" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(r * 2.4).toFixed(1)}"/><circle class="dot" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}"/>`;
    }).join("");
    return `<svg viewBox="0 0 ${land.width} ${land.height}" preserveAspectRatio="xMidYMid meet" focusable="false" aria-hidden="true">
      <use href="#pr-world-land"/><use href="#pr-world-taiwan"/>
      <g class="arcs">${arcPaths}</g><g>${dots}</g>
      <circle class="tw-ring" cx="${tx.toFixed(1)}" cy="${ty.toFixed(1)}" r="13"/><circle class="tw-dot" cx="${tx.toFixed(1)}" cy="${ty.toFixed(1)}" r="5.5"/>
    </svg>`;
  }

  function renderMaps(host) {
    // The globe behind the hero needs only the cities; the flat maps also wait for the land outline.
    window.UniWayGlobeBackdrop?.setMarkers(partnerCities());
    if (!land) { loadLand(); return; }
    let sprite = host.querySelector("#pr-world-sprite");
    if (!sprite) {
      host.insertAdjacentHTML("afterbegin", `<svg id="pr-world-sprite" class="pr-sprite" width="0" height="0" aria-hidden="true" focusable="false"><defs><path id="pr-world-land" d="${land.land}"/><path id="pr-world-taiwan" d="${land.taiwan}"/></defs></svg>`);
    }
    const cities = partnerCities();
    const total = cities.reduce((sum, city) => sum + city.weight, 0);
    host.querySelectorAll("[data-home-map]").forEach((node) => {
      node.innerHTML = mapSvg(cities);
      node.setAttribute("aria-label", total
        ? `${state.dashboard.school_name || activeHomeSchool()}的合作校分布：${total} 間合作校，分布在 ${cities.length} 個城市`
        : "合作校分布地圖");
    });
  }

  // The supported schools always drift to the left and come back in from the right, so the row keeps working as schools are
  // added; copies of the row (hidden from assistive technology) fill the width and make the loop seamless.
  const MARQUEE_PX_PER_SECOND = 38;
  let marqueeWidth = 0;
  function layoutMarquee(host) {
    const box = host.querySelector("#home-supported-marquee"), track = host.querySelector("#home-supported-list");
    const toggle = host.querySelector("#home-supported-toggle");
    if (!box || !track) return;
    track.querySelectorAll("[data-marquee-copy]").forEach((item) => item.remove());
    track.classList.remove("is-moving");
    toggle.hidden = true;
    const available = box.clientWidth;
    if (!available || !track.children.length) return;
    marqueeWidth = available;
    const natural = track.scrollWidth;
    if (!natural) return;
    const originals = [...track.children];
    // One more copy than the row is wide, so the gap never shows while one set slides out and the next slides in.
    for (let copy = 0; copy < Math.ceil(available / natural) + 1; copy += 1) {
      originals.forEach((item) => {
        const clone = item.cloneNode(true);
        clone.setAttribute("aria-hidden", "true");
        clone.dataset.marqueeCopy = "";
        track.append(clone);
      });
    }
    track.style.setProperty("--pr-marquee-shift", `${-natural}px`);
    track.style.setProperty("--pr-marquee-duration", `${Math.max(12, Math.round(natural / MARQUEE_PX_PER_SECOND))}s`);
    track.classList.add("is-moving");
    toggle.hidden = false;
  }

  function renderSchools(host) {
    const schools = state.supportedUniversities || [];
    const total = schools.reduce((sum, item) => sum + (item.partner_count || 0), 0);
    const count = String(schools.length || 6);
    const set = (selector, text) => { const node = host.querySelector(selector); if (node && node.textContent !== text) node.textContent = text; };
    set("#home-stat-schools", count);
    set("#home-stat-partners", total ? formatNumber(total) : "—");
    set("#home-band-total-line", total ? `看見 ${formatNumber(total)} 個選擇。` : "看見更多選擇。");
    set("#home-supported-count", `${count} 所大學`);
    const list = host.querySelector("#home-supported-list");
    // Rewriting the row restarts the drift, so it is only rewritten when a school or its count actually changed.
    const signature = JSON.stringify(schools.map((item) => [item.school_name, item.partner_count || 0]));
    if (list.dataset.signature !== signature) {
      list.dataset.signature = signature;
      list.innerHTML = schools.map((item) => `<li><strong>${escapeHtml(item.school_name)}</strong><span>${item.partner_count ? `${formatNumber(item.partner_count)} 間合作校` : "資料建置中"}</span></li>`).join("");
      layoutMarquee(host);
    }
    const buttons = host.querySelector("#home-school-buttons");
    buttons.innerHTML = schools.map((item) => {
      const badge = schoolBadge(item);
      const selected = item.school_name === state.homeSchool;
      return `<button type="button" class="pr-school-button" data-home-landing-school="${escapeHtml(item.school_name)}" style="--school-tint:${badge.tint}"${selected ? ' aria-current="true"' : ""}>
        <span class="pr-school-tile" aria-hidden="true">${escapeHtml(badge.text)}</span>
        <span><strong>${escapeHtml(item.school_name)}</strong><small>${item.partner_count ? `${formatNumber(item.partner_count)} 間合作校` : "資料建置中"}</small></span>
        <i data-lucide="arrow-right" aria-hidden="true"></i></button>`;
    }).join("");
  }

  function completedSteps() {
    if (!state.homeSchool) return -1;
    const stage = state.account?.application_stage;
    if (stage in STAGE_PROGRESS) return STAGE_PROGRESS[stage];
    return state.applications?.size ? 1 : 0;
  }

  function renderPlan(host) {
    const done = completedSteps();
    const badge = host.querySelector("#home-plan-badge");
    badge.textContent = done < 0 ? "共 4 步" : done >= STAGES.length ? "已完成 4 步" : `第 ${done + 1} 步 / 共 4 步`;
    host.querySelector("#home-plan-steps").innerHTML = STAGES.map((stage, index) => {
      const state_ = done < 0 || index > done ? "todo" : index < done ? "done" : "now";
      const icon = state_ === "done" ? "check" : state_ === "now" ? "notebook-pen" : "plus";
      const label = state_ === "done" ? "已完成" : state_ === "now" ? "進行中" : "未開始";
      return `<li class="${state_}"><span class="pr-step-ring"><i data-lucide="${icon}" aria-hidden="true"></i></span><span class="pr-step-title">${stage}</span><small>${label}</small></li>`;
    }).join("");
  }

  const html = (value) => escapeHtml(String(value ?? ""));
  const shortName = (name) => String(name || "").replace(/\s+[A-Za-z].*$/, "") || String(name || "");
  const monthDay = (date) => `${date.getMonth() + 1}/${String(date.getDate()).padStart(2, "0")}`;
  const icon = (name) => `<i data-lucide="${name}" aria-hidden="true"></i>`;

  // Partners of the school that is open, or of the default catalogue while none is chosen.
  function currentPartners() {
    if (!state.dashboard) return [];
    return !state.homeSchool || state.dashboard.school_name === state.homeSchool ? state.dashboard.partner_universities || [] : [];
  }

  function availabilityGroup(item) {
    const meta = partnerAvailabilityMeta(item);
    return meta.pending ? "pending" : meta.blocked ? "blocked" : "open";
  }

  // Schools worth showing first: open ones, then the nearest deadline, then the most places.
  function featured(list, limit) {
    const rank = (item) => ({ open: 0, pending: 1, blocked: 2 })[availabilityGroup(item)];
    return [...list].sort((a, b) => rank(a) - rank(b)
      || (partnerNextDeadline(a)?.getTime() ?? Infinity) - (partnerNextDeadline(b)?.getTime() ?? Infinity)
      || (partnerQuotaNumber(b) ?? -1) - (partnerQuotaNumber(a) ?? -1)).slice(0, limit);
  }

  function emptyTile(message, withPicker) {
    return `<div class="pr-tile-empty"><p>${html(message)}</p>${withPicker ? `<button type="button" class="pr-link" data-home-pick-school>選擇就讀學校${icon("arrow-right")}</button>` : ""}</div>`;
  }

  function renderSearch(host, list) {
    const rows = host.querySelector("#home-search-rows"), foot = host.querySelector("#home-search-foot");
    const lede = host.querySelector("#home-search-lede");
    if (!list.length) {
      rows.innerHTML = emptyTile(state.homeSchool ? "合作校資料載入中…" : "選擇就讀學校後，這裡會列出你能申請的合作校。", !state.homeSchool);
      foot.innerHTML = "";
      return;
    }
    const profile = state.eligibilityProfile;
    const groups = { open: 0, pending: 0, blocked: 0 };
    list.forEach((item) => { groups[availabilityGroup(item)] += 1; });
    lede.textContent = `${state.homeSchool || "目前"}的 ${formatNumber(list.length)} 間合作校，${groups.open ? `${formatNumber(groups.open)} 間本期可申請` : "可依國家與學期篩選"}。`;
    rows.innerHTML = featured(list, 3).map((item) => {
      const meta = partnerAvailabilityMeta(item);
      const match = profile ? partnerMatch(item) : null;
      const ok = match ? match.tone !== "blocked" : !meta.blocked;
      const label = match ? match.label : meta.shortLabel;
      const image = schoolImageFor(item.school_name, item.country)?.local_path;
      const deadline = partnerNextDeadline(item), quota = partnerQuotaNumber(item);
      const facts = [quota ? `名額 ${quota}` : "", deadline ? `截止 ${monthDay(deadline)}` : ""].filter(Boolean).join(" · ");
      return `<a class="pr-mini-row" href="#school=${encodeURIComponent(item.school_name)}">
        <span class="pr-mini-thumb"${image ? ` style="background-image:url('${html(image)}')"` : ""}></span>
        <span class="pr-mini-text"><strong>${html(shortName(item.school_name))}</strong><small>${html([item.country, item.location?.city].filter(Boolean).join("・"))}${facts ? ` · ${html(facts)}` : ""}</small></span>
        <span class="pr-tag ${ok ? "pr-tag-ok" : "pr-tag-warn"}">${html(label)}</span></a>`;
    }).join("");
    const countries = new Map();
    list.forEach((item) => { if (item.country) countries.set(item.country, (countries.get(item.country) || 0) + 1); });
    const top = [...countries].sort((a, b) => b[1] - a[1]).slice(0, 5);
    foot.innerHTML = `<span class="pr-mini-label">熱門國家</span>${top.map(([country, count]) => `<button type="button" class="pr-mini-chip" data-home-country="${html(country)}">${html(country)} <b>${count}</b></button>`).join("")}`;
  }

  function renderFit(host, list) {
    const body = host.querySelector("#home-tile-fit");
    if (!list.length) { body.innerHTML = emptyTile("選擇就讀學校後，這裡會依你的條件列出符合與待確認的學校。", !state.homeSchool); return; }
    const profile = state.eligibilityProfile;
    const picks = [...(state.applications || [])].map((name) => partnerByName(name)).filter(Boolean);
    if (picks.length || profile) {
      // Someone's own picks (or, with conditions filled in, the schools that suit them best) instead of school-wide counts.
      const pool = (picks.length ? picks : featured(list, 4)).slice(0, 4);
      body.innerHTML = `<small class="pr-tile-note">${picks.length ? `我的志願 · ${picks.length} 間` : "依你的條件優先看這些"}</small><div class="pr-mini-checks">${pool.map((item) => {
        const meta = partnerAvailabilityMeta(item);
        const match = profile ? partnerMatch(item) : null;
        const ok = match ? match.tone !== "blocked" : !meta.blocked;
        return `<a class="${ok ? "ok" : "warn"}" href="#school=${encodeURIComponent(item.school_name)}">${icon(ok ? "circle-check" : "clock-alert")}<span>${html(shortName(item.school_name))}</span><small>${html(match ? match.label : meta.shortLabel)}</small></a>`;
      }).join("")}</div><a class="pr-link" href="${profile ? "#eligibility" : "#advisor"}" data-requires-home-school>${profile ? "查看完整初判" : "填寫條件，看你符合哪些"}${icon("arrow-right")}</a>`;
      return;
    }
    const groups = { open: 0, pending: 0, blocked: 0 };
    list.forEach((item) => { groups[availabilityGroup(item)] += 1; });
    const row = (cls, glyph, label, count) => `<div class="${cls}">${icon(glyph)}<span>${label}</span><small>${formatNumber(count)} 間</small></div>`;
    body.innerHTML = `<small class="pr-tile-note">${html(state.homeSchool || "目前")}的合作校狀態</small><div class="pr-mini-checks">${row("ok", "circle-check", "本期可申請", groups.open)}${row("warn", "clock-alert", "名額或期間待確認", groups.pending)}${row("muted", "circle-slash", "目前不開放", groups.blocked)}</div><a class="pr-link" href="#advisor" data-requires-home-school>填寫條件，看你符合哪些${icon("arrow-right")}</a>`;
  }

  function upcomingEvents() {
    const today = localDateKey();
    const list = [];
    try {
      upcomingDeadlines(40).forEach((event) => { if (event.date) list.push({ date: event.date, title: event.title, scope: event.scope || "官方期限", personal: false }); });
    } catch (_) { /* no workflow loaded yet */ }
    (state.calendarEvents || []).filter((event) => event.origin !== "official" && event.title && event.date >= today).forEach((event) => {
      const date = parseLocalDate(event.date);
      if (date) list.push({ date, title: event.title, scope: "我的行程", personal: true });
    });
    if (list.length < 3) {
      // No workflow is loaded for a visitor, so fall back to the partner schools' own application deadlines.
      const byDay = new Map();
      currentPartners().forEach((item) => {
        const date = partnerNextDeadline(item);
        if (!date) return;
        const key = localDateKey(date);
        const entry = byDay.get(key) || { date, names: [] };
        entry.names.push(shortName(item.school_name));
        byDay.set(key, entry);
      });
      byDay.forEach(({ date, names }) => list.push({
        date,
        title: names.length > 1 ? `${names.length} 間合作校申請截止` : `${names[0]} 申請截止`,
        scope: names.length > 1 ? `${names.slice(0, 2).join("、")}等` : "合作校",
        personal: false,
      }));
    }
    return list.sort((a, b) => a.date - b.date);
  }

  function renderCalendar(host) {
    const strip = host.querySelector("#home-week"), body = host.querySelector("#home-tile-calendar");
    const events = upcomingEvents();
    const today = new Date();
    const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - ((today.getDay() + 6) % 7), 12);
    const marked = new Set(events.map((event) => localDateKey(event.date)));
    strip.removeAttribute("aria-hidden");
    strip.setAttribute("role", "group");
    strip.setAttribute("aria-label", "本週");
    strip.innerHTML = ["一", "二", "三", "四", "五", "六", "日"].map((name, index) => {
      const day = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + index, 12);
      const key = localDateKey(day);
      const cls = marked.has(key) ? "hot" : key === localDateKey(today) ? "today" : "";
      return `<div class="${cls}"><small>${name}</small><strong>${day.getDate()}</strong><span></span></div>`;
    }).join("");
    if (!events.length) {
      body.innerHTML = emptyTile(state.homeSchool ? "目前沒有已確認的官方期限，公告更新後會出現在這裡。" : "選擇就讀學校後，這裡會列出該校的申請期限。", !state.homeSchool);
      return;
    }
    body.innerHTML = `<ol class="pr-mini-dates">${events.slice(0, 3).map((event) => {
      const days = calendarDaysUntil(localDateKey(event.date));
      return `<li><span class="pr-mini-date"><small>${event.date.getMonth() + 1} 月</small><strong>${String(event.date.getDate()).padStart(2, "0")}</strong></span><span class="pr-mini-text"><strong>${html(truncate(event.title, 28))}</strong><small>${days === null ? "" : `<b>${days === 0 ? "就是今天" : `還有 ${days} 天`}</b> · `}${html(event.scope)}</small></span></li>`;
    }).join("")}</ol><a class="pr-link" href="#calendar" data-requires-home-school>開啟申請日曆${icon("arrow-right")}</a>`;
  }

  function renderDocuments(host, list) {
    const body = host.querySelector("#home-tile-documents");
    const items = list.length ? documentChecklistItems() : [];
    if (!items.length) {
      const notes = (list.length && (state.dashboard.document_explanations || state.dashboard.rule_explanations)) || [];
      if (notes.length) {
        body.innerHTML = `<small class="pr-tile-note">${html(state.homeSchool || "")}的官方文件重點 · 共 ${notes.length} 份</small>
          <ul class="pr-mini-docs">${notes.slice(0, 4).map((note) => `<li><a href="#documents" data-requires-home-school>${icon("file-text")}<span>${html(truncate(note.title, 26))}<em>${html(note.document_type || "官方文件")}</em></span></a></li>`).join("")}</ul>
          <a class="pr-link" href="#document-check" data-requires-home-school>檢查我的文件${icon("arrow-right")}</a>`;
        return;
      }
      body.innerHTML = emptyTile(state.homeSchool ? "這間學校的文件清單整理中，請先看官方公告。" : "選擇就讀學校後，這裡會列出該校要準備的文件。", !state.homeSchool);
      return;
    }
    const ready = items.filter((item) => readinessStatus(item.id) === "ready").length;
    const glyph = { ready: "circle-check", preparing: "clock", todo: "circle" };
    const label = { ready: "已備妥", preparing: "準備中", todo: "待準備" };
    body.innerHTML = `<small class="pr-tile-note">${state.account ? `${ready} / ${items.length} 已備妥` : `共 ${items.length} 份文件 · 登入後可記錄進度`}</small>
      <ul class="pr-mini-docs">${items.slice(0, 4).map((item) => {
        const status = readinessStatus(item.id);
        return `<li class="${status}">${icon(glyph[status])}<span>${html(truncate(item.title, 22))}${item.conditional ? "<em>符合身分才需要</em>" : ""}</span><small>${state.account ? label[status] : "待準備"}</small></li>`;
      }).join("")}</ul><a class="pr-link" href="#documents" data-requires-home-school>查看文件說明${icon("arrow-right")}</a>`;
  }

  function renderBudget(host, list) {
    const body = host.querySelector("#home-tile-budget");
    const school = state.homeSchool ? preferredBudgetSchool() : "";
    const plan = school ? budgetPlanForSchool(school) : null;
    if (plan) {
      const months = plan.months || 1;
      const parts = [["住宿", (plan.housing || 0) * months, "c1"], ["餐飲", (plan.food || 0) * months, "c2"], ["交通", (plan.transport || 0) * months, "c3"], ["其他", (plan.other || 0) * months, "c4"], ["一次性費用", plan.oneTime || 0, "c5"]].filter(([, amount]) => amount > 0);
      const total = parts.reduce((sum, [, amount]) => sum + amount, 0);
      const net = Math.max(0, total - (plan.scholarship || 0));
      body.innerHTML = `<small class="pr-tile-note">${html(shortName(school))} · ${months} 個月</small><div class="pr-budget-total"><strong>${html(formatBudgetAmount(net, plan.currency))}</strong><span>扣除補助後的預估總支出</span></div>
        ${total ? `<div class="pr-budget-bar">${parts.map(([, amount, cls]) => `<span class="${cls}" style="flex:${amount}"></span>`).join("")}</div>
        <ul class="pr-budget-legend">${parts.map(([name, amount, cls]) => `<li><i class="${cls}"></i>${name}<b>${html(formatBudgetAmount(amount, plan.currency))}</b></li>`).join("")}</ul>` : ""}
        <a class="pr-link" href="#budget" data-requires-home-school>調整我的預算${icon("arrow-right")}</a>`;
      return;
    }
    const sample = list.map((item) => ({ item, profile: destinationProfileForSchool(item.school_name) })).find((entry) => entry.profile?.cost_summary);
    if (!sample) { body.innerHTML = emptyTile(state.homeSchool ? "官方生活費資料整理中；你也可以直接輸入自己的估算。" : "選擇就讀學校後，這裡會顯示合作校的官方生活費資料。", !state.homeSchool); return; }
    const { item, profile } = sample;
    body.innerHTML = `<small class="pr-tile-note">官方生活費參考 · ${html(shortName(item.school_name))}</small>
      <p class="pr-budget-source"><span><i data-lucide="map-pin" aria-hidden="true"></i>${html(profile.city || profile.country || item.country || "")}</span>${html(truncate(profile.cost_summary, 96))}</p>
      <small class="pr-tile-fine">${profile.last_checked ? `最後查核 ${html(formatDate(profile.last_checked).slice(0, 10))}；` : ""}幣別依學校公告，估算前請統一換算。</small>
      <a class="pr-link" href="#budget" data-requires-home-school>開始估算我的預算${icon("arrow-right")}</a>`;
  }

  function renderTiles(host) {
    const list = currentPartners();
    renderSearch(host, list);
    renderFit(host, list);
    renderCalendar(host);
    renderDocuments(host, list);
    renderBudget(host, list);
  }

  function render() {
    scheduled = 0;
    const host = root();
    if (!host || !state.supportedUniversities) return;
    const key = JSON.stringify([
      state.supportedUniversities.map((item) => [item.school_name, item.partner_count]), state.homeSchool,
      state.dashboard?.school_name, state.dashboard?.partner_universities?.length, Boolean(land),
      state.account?.id || "", state.account?.application_stage || "", [...(state.applications || [])], Boolean(state.eligibilityProfile),
      localDateKey(), state.calendarEvents?.length || 0, state.destinationProfiles?.length || 0, state.workflowCache?.size || 0,
      state.documentReadiness, state.budgetPlans, state.budgetSchool || "",
    ]);
    if (key === lastKey) return;
    lastKey = key;
    renderSchools(host);
    renderPlan(host);
    renderTiles(host);
    renderMaps(host);
    const schoolCard = host.querySelector("#home-board-school-description");
    if (schoolCard) schoolCard.textContent = `${activeUniversityProfile().short_name || "校內"}學生的交換申請資訊與討論。`;
    initIcons();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = window.requestAnimationFrame(render);
  }

  // The same address the explore page writes for its own filters, so back and reload behave as usual.
  function goPartners({ q = "", country = "" } = {}) {
    const url = new URL(window.location.href);
    url.hash = "#partners";
    url.searchParams.set("view", "list");
    for (const [key, value] of [["q", q], ["country", country]]) {
      if (value) url.searchParams.set(key, value);
      else url.searchParams.delete(key);
    }
    if (state.homeSchool) url.searchParams.set("home", activeHomeSchool());
    window.UniWayNavigation.pushState({}, "", url);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  }

  function openMap(event) {
    event.preventDefault();
    state.partnerView = "map";
    const url = new URL(window.location.href);
    url.hash = "#partners";
    url.searchParams.set("view", "map");
    if (state.homeSchool) url.searchParams.set("home", activeHomeSchool());
    window.UniWayNavigation.pushState({}, "", url);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  }

  document.addEventListener("click", (event) => {
    const host = root();
    if (!host || !host.contains(event.target)) return;
    const toggle = event.target.closest("#home-supported-toggle");
    if (toggle) {
      const paused = toggle.getAttribute("aria-pressed") !== "true";
      toggle.setAttribute("aria-pressed", String(paused));
      toggle.setAttribute("aria-label", paused ? "繼續學校名單捲動" : "暫停學校名單捲動");
      host.querySelector("#home-supported-list").classList.toggle("is-paused", paused);
      toggle.innerHTML = `<i data-lucide="${paused ? "play" : "pause"}" aria-hidden="true"></i>`;
      initIcons();
      return;
    }
    const school = event.target.closest("[data-home-landing-school]");
    if (school) { chooseHomeSchool(school.dataset.homeLandingSchool); return; }
    const map = event.target.closest("[data-home-open-map]");
    if (map) { openMap(event); return; }
    if (event.target.closest("[data-home-pick-school]")) { openSchoolOnboarding(); return; }
    const country = event.target.closest("[data-home-country]");
    if (country) goPartners({ country: country.dataset.homeCountry });
  });
  document.addEventListener("submit", (event) => {
    if (event.target.id !== "home-search-form") return;
    event.preventDefault();
    goPartners({ q: event.target.elements.q.value.trim() });
  });

  // Re-measure when the row changes width (a window resize, or the page being shown after it was hidden).
  const marqueeBox = document.querySelector("#home-supported-marquee");
  if (marqueeBox && "ResizeObserver" in window) {
    let resizeTimer = 0;
    new ResizeObserver(() => {
      if (!marqueeBox.clientWidth || Math.abs(marqueeBox.clientWidth - marqueeWidth) < 2) return;
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(() => layoutMarquee(root()), 150);
    }).observe(marqueeBox);
  }

  loadLand();
  // Schools, destination notes and a signed-in student's saved data arrive at different times; the render key makes this cheap.
  window.setInterval(() => { const host = root(); if (host && !host.hidden && !document.hidden) schedule(); }, 1500);
  return { render: schedule };
})();

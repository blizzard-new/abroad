/* Home landing (#home): product story, supported schools, plan collage and partner map preview.
   Every number and sample row on the page follows the loaded catalogue; app.js calls UniWayHome.render()
   whenever the school, dashboard, account or saved schools change. */
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

  function schoolCountFor(name) {
    const entry = state.supportedUniversities.find((item) => item.school_name === name);
    return entry?.partner_count || 0;
  }

  function renderSchools(host) {
    const schools = state.supportedUniversities || [];
    const total = schools.reduce((sum, item) => sum + (item.partner_count || 0), 0);
    const count = String(schools.length || 6);
    const set = (selector, text) => { const node = host.querySelector(selector); if (node && node.textContent !== text) node.textContent = text; };
    set("#home-pill-count", `${count} 所大學`);
    set("#home-pill-text", total ? `已整理 ${formatNumber(total)} 間合作校資料` : "合作校資料整理中");
    set("#home-stat-schools", count);
    set("#home-stat-partners", total ? formatNumber(total) : "—");
    set("#home-band-total-line", total ? `看見 ${formatNumber(total)} 個選擇。` : "看見更多選擇。");
    const list = host.querySelector("#home-supported-list");
    list.innerHTML = schools.map((item) => `<li><strong>${escapeHtml(item.school_name)}</strong><span>${item.partner_count ? `${formatNumber(item.partner_count)} 間合作校` : "資料建置中"}</span></li>`).join("");
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
    const school = state.homeSchool;
    const done = completedSteps();
    const loaded = state.dashboard?.school_name === school ? state.dashboard.partner_universities.length : 0;
    const partnerCount = loaded || schoolCountFor(school);
    const title = host.querySelector("#home-map-card-title");
    title.textContent = school ? `${school}${partnerCount ? ` · ${formatNumber(partnerCount)} 間合作校` : ""}` : "合作校分布";
    const badge = host.querySelector("#home-plan-badge");
    badge.textContent = done < 0 ? "共 4 步" : done >= STAGES.length ? "已完成 4 步" : `第 ${done + 1} 步 / 共 4 步`;
    host.querySelector("#home-plan-steps").innerHTML = STAGES.map((stage, index) => {
      const state_ = done < 0 || index > done ? "todo" : index < done ? "done" : "now";
      const icon = state_ === "done" ? "check" : state_ === "now" ? "notebook-pen" : "plus";
      const label = state_ === "done" ? "已完成" : state_ === "now" ? "進行中" : "未開始";
      return `<li class="${state_}"><span class="pr-step-ring"><i data-lucide="${icon}" aria-hidden="true"></i></span><span class="pr-step-title">${stage}</span><small>${label}</small></li>`;
    }).join("");
  }

  function renderSamples(host) {
    const partners = state.dashboard?.school_name === state.homeSchool || !state.homeSchool ? state.dashboard?.partner_universities || [] : [];
    const rows = host.querySelectorAll(".pr-mini-row");
    const profile = state.eligibilityProfile;
    rows.forEach((row, index) => {
      const item = partners[index];
      row.hidden = !item;
      if (!item) return;
      const strong = row.querySelector("strong"), small = row.querySelector("small"), tag = row.querySelector(".pr-tag");
      strong.textContent = (item.school_name || "").replace(/\s+[A-Za-z].*$/, "") || item.school_name;
      small.textContent = [item.country, item.location?.city].filter(Boolean).join("・");
      let ok, label;
      if (profile) { const match = partnerMatch(item); ok = match.tone !== "blocked"; label = match.label; }
      else { const availability = partnerAvailabilityMeta(item); ok = !availability.blocked; label = availability.shortLabel; }
      tag.textContent = label;
      tag.className = `pr-tag ${ok ? "pr-tag-ok" : "pr-tag-warn"}`;
    });
    host.querySelector(".pr-mini-search")?.classList.toggle("is-empty", !partners.length);
  }

  function renderWeek(host) {
    const strip = host.querySelector("#home-week"), banner = host.querySelector("#home-week-banner");
    const today = new Date();
    const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - ((today.getDay() + 6) % 7), 12);
    let deadline = null;
    try { deadline = upcomingDeadlines(1)[0] || null; } catch (_) { deadline = null; }
    const deadlineKey = deadline ? localDateKey(deadline.date) : "";
    strip.innerHTML = ["一", "二", "三", "四", "五", "六", "日"].map((name, index) => {
      const day = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + index, 12);
      const key = localDateKey(day);
      const cls = key === deadlineKey ? "hot" : key === localDateKey(today) ? "today" : "";
      return `<div class="${cls}"><small>${name}</small><strong>${day.getDate()}</strong><span></span></div>`;
    }).join("");
    if (deadline) {
      const days = calendarDaysUntil(localDateKey(deadline.date));
      banner.hidden = false;
      banner.querySelector("span").textContent = `${truncate(deadline.title, 18)}，${days === 0 ? "就是今天" : `還有 ${days} 天`}`;
    } else banner.hidden = true;
  }

  function render() {
    scheduled = 0;
    const host = root();
    if (!host || !state.supportedUniversities) return;
    const key = JSON.stringify([
      state.supportedUniversities.map((item) => [item.school_name, item.partner_count]), state.homeSchool,
      state.dashboard?.school_name, state.dashboard?.partner_universities?.length, Boolean(land),
      state.account?.application_stage || "", state.applications?.size || 0, Boolean(state.eligibilityProfile), localDateKey(),
    ]);
    if (key === lastKey) return;
    lastKey = key;
    renderSchools(host);
    renderPlan(host);
    renderSamples(host);
    renderWeek(host);
    renderMaps(host);
    const schoolCard = host.querySelector("#home-board-school-description");
    if (schoolCard) schoolCard.textContent = `${activeUniversityProfile().short_name || "校內"}學生的交換申請資訊與討論。`;
    initIcons();
  }

  function schedule() {
    if (scheduled) return;
    scheduled = window.requestAnimationFrame(render);
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
    const school = event.target.closest("[data-home-landing-school]");
    if (school) { chooseHomeSchool(school.dataset.homeLandingSchool); return; }
    const map = event.target.closest("[data-home-open-map]");
    if (map) openMap(event);
  });

  loadLand();
  return { render: schedule };
})();

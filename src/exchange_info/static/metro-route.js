/* Home route map. The student's own school is the origin station, each region of the world is a coloured line and each
   partner country on it is a station. Everything is drawn from the loaded catalogue (state.dashboard.partner_universities):
   no sample stations, no invented counts. A station is filled when at least one of its partner schools is open this cycle and
   hollow when the schools are only on file or unconfirmed; the numbers under every name say the same thing in words.
   platform-home.js calls UniWayMetro.render(host) whenever the school or the catalogue changes. */
window.UniWayMetro = (() => {
  "use strict";
  // Drawing units. The canvas keeps this aspect ratio, so station buttons can be placed in percentages of it.
  const W = 1000, H = 500, ORIGIN = { x: 96, y: H / 2 }, TRUNK_X = 150, FIRST_X = 276, STEP = 78, LAST_X = 780;
  const GAP_MAX = 100, PAD_Y = 52, BUNDLE = 11, AFTER_BEND = 44, TAG_GAP = 46;
  const LINES = [
    { id: "east-asia", name: "東亞線", en: "East Asia", regions: ["east-asia"] },
    { id: "southeast", name: "東南亞・南亞線", en: "SE & S Asia", regions: ["southeast-asia", "south-asia"] },
    { id: "europe", name: "歐洲線", en: "Europe", regions: ["eastern-europe", "western-europe", "northern-europe", "southern-europe"] },
    { id: "americas", name: "美洲線", en: "Americas", regions: ["north-america", "latin-america"] },
    { id: "elsewhere", name: "大洋洲・非洲・西亞線", en: "Oceania, Africa & W Asia", regions: ["oceania", "africa", "west-asia", "other"] },
  ];
  const english = new Map();
  let signature = "", focusLine = "";

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  const pct = (value, whole) => `${((value / whole) * 100).toFixed(3)}%`;

  function loadEnglish() {
    if (english.size) return;
    for (const list of Object.values(window.UniWayRegions?.COUNTRIES || {})) {
      for (const [zh, en] of list) if (!english.has(zh)) english.set(zh, en);
    }
  }

  const lineIdOf = (country) => {
    const region = window.UniWayRegions?.regionOf(country) || "other";
    return (LINES.find((line) => line.regions.includes(region)) || LINES.at(-1)).id;
  };

  // Countries on one line, biggest first, with how many of their schools are open, unconfirmed, or not open.
  function buildModel(partners) {
    const byCountry = new Map();
    for (const item of partners) {
      const country = String(item.country || "").trim() || "其他";
      const entry = byCountry.get(country) || { country, total: 0, open: 0, pending: 0, blocked: 0 };
      const meta = partnerAvailabilityMeta(item);
      entry.total += 1;
      entry[meta.pending ? "pending" : meta.blocked ? "blocked" : "open"] += 1;
      byCountry.set(country, entry);
    }
    const lines = LINES.map((line) => ({ ...line, stops: [], total: 0, open: 0 }));
    for (const entry of byCountry.values()) {
      const line = lines.find((candidate) => candidate.id === lineIdOf(entry.country));
      line.stops.push(entry);
      line.total += entry.total;
      line.open += entry.open;
    }
    for (const line of lines) line.stops.sort((a, b) => b.total - a.total || a.country.localeCompare(b.country, "zh-Hant"));
    return lines.filter((line) => line.stops.length);
  }

  // Lanes are spread evenly around the origin. A line bends toward its lane at 45 degrees, so its first station sits
  // past the bend; labels step away from the lines that cross the corridor (the first label of an upper lane goes
  // below it, of a lower lane above it) and then alternate.
  function layout(lines) {
    const count = lines.length;
    const gap = count > 1 ? Math.min(GAP_MAX, (H - 2 * PAD_Y) / (count - 1)) : 0;
    lines.forEach((line, index) => {
      const lane = index - (count - 1) / 2;
      line.y = H / 2 + lane * gap;
      line.offset = lane * BUNDLE;
      const bendEnd = TRUNK_X + Math.abs(line.y - (ORIGIN.y + line.offset));
      line.startX = Math.max(FIRST_X, bendEnd + AFTER_BEND);
      const room = Math.floor((LAST_X - line.startX) / STEP) + 1;
      line.shown = line.stops.slice(0, Math.max(1, room));
      line.more = line.stops.length - line.shown.length;
      const firstSide = lane < 0 ? "down" : lane > 0 ? "up" : "down";
      line.shown.forEach((stop, j) => {
        stop.x = line.startX + j * STEP;
        stop.y = line.y;
        stop.side = j % 2 === 0 ? firstSide : firstSide === "down" ? "up" : "down";
      });
      line.endX = line.shown.at(-1).x + TAG_GAP;
    });
  }

  function pathOf(line) {
    const startY = ORIGIN.y + line.offset, drop = line.y - startY, run = Math.abs(drop);
    const diagonal = run > 0.5 ? `L${TRUNK_X + run} ${line.y.toFixed(1)}` : "";
    return `M${ORIGIN.x} ${startY.toFixed(1)}H${TRUNK_X}${diagonal}H${line.endX}`;
  }

  function stationLabel(stop) {
    const filled = stop.open > 0;
    // Every open: solid. Some open: ringed with a dot. None open: hollow. The words under the name say the same.
    const fill = stop.open === 0 ? "none" : stop.open === stop.total ? "all" : "some";
    const second = filled ? `<em>${stop.open}</em> / ${stop.total} 本期開放` : stop.pending ? `待確認 ${stop.pending} 間` : `合作備查 ${stop.total} 間`;
    const spoken = [`${stop.country}：${stop.total} 間合作校`, stop.open ? `本期開放 ${stop.open} 間` : "", stop.pending ? `名額或期間待確認 ${stop.pending} 間` : "", stop.blocked ? `目前不開放 ${stop.blocked} 間` : ""].filter(Boolean).join("，");
    return { filled, fill, second, spoken };
  }

  function stationHtml(line, stop) {
    const { filled, fill, second, spoken } = stationLabel(stop);
    const style = `--x:${stop.x};--y:${stop.y.toFixed(1)}`;
    return `<li class="mt-stop is-${stop.side}" style="${style}"><button type="button" class="mt-station" data-home-country="${esc(stop.country)}" data-filled="${filled}" data-fill="${fill}" aria-label="${esc(spoken)}，查看這個國家的合作校">
      <span class="mt-dot" aria-hidden="true"></span><span class="mt-label"><b>${esc(stop.country)}</b><small>${second}</small></span></button></li>`;
  }

  function lineHtml(line) {
    const tagStyle = `--x:${line.endX};--y:${line.y.toFixed(1)}`;
    const countries = line.more > 0 ? `前 ${line.shown.length} / ${line.stops.length} 國` : `${line.stops.length} 國`;
    const summary = `${countries} · ${line.total} 間`;
    return `<div class="mt-line" data-line="${line.id}">
      <button type="button" class="mt-line-tag" style="${tagStyle}" data-line-tag="${line.id}" aria-pressed="false" aria-label="${esc(`${line.name}：${summary}。按下聚焦這條路線，再按一次取消`)}">
        <span class="mt-line-name">${esc(line.name)}</span><span class="mt-line-meta"><small>${esc(line.en)}</small><span class="mt-line-sum">${esc(summary)}</span></span></button>
      <ol class="mt-stops" aria-label="${esc(line.name)}的國家">${line.shown.map((stop) => stationHtml(line, stop)).join("")}</ol></div>`;
  }

  function originHtml(name, chosen) {
    const caption = chosen ? "你的學校" : "先以此校為例";
    return `<div class="mt-origin" style="--x:${ORIGIN.x};--y:${ORIGIN.y}" aria-hidden="true"><span class="mt-origin-ring"></span></div>
      <button type="button" class="mt-origin-label" data-home-pick-school aria-haspopup="dialog" aria-label="${esc(`出發學校：${name}。按下更換就讀學校`)}"><small>${caption}</small><strong>${esc(name)}</strong><span class="mt-origin-edit">更換</span></button>`;
  }

  const briefName = (name) => String(name || "").replace(/\s+[A-Za-z].*$/, "") || String(name || "");

  // The nearest deadline among this school's partners, read from the same dates the calendar uses.
  function nextStopHtml(partners) {
    if (typeof partnerNextDeadline !== "function" || typeof localDateKey !== "function") return "";
    const today = localDateKey();
    const byDay = new Map();
    let unconfirmed = 0;
    for (const item of partners) {
      const date = partnerNextDeadline(item);
      if (!date) { unconfirmed += 1; continue; }
      const key = localDateKey(date);
      if (key < today) continue;
      const entry = byDay.get(key) || { date, key, names: [] };
      entry.names.push(briefName(item.school_name));
      byDay.set(key, entry);
    }
    const first = [...byDay.values()].sort((a, b) => a.date - b.date)[0];
    const pending = unconfirmed ? `<span class="mt-next-pending">另有 ${unconfirmed} 間期限待確認</span>` : "";
    if (!first) {
      return unconfirmed ? `<span class="mt-next-label">下一站</span><span class="mt-next-text">期限都還在待確認，公布後會出現在這裡</span>${pending}` : "";
    }
    const days = typeof calendarDaysUntil === "function" ? calendarDaysUntil(first.key) : null;
    const when = `${first.date.getMonth() + 1}/${String(first.date.getDate()).padStart(2, "0")}`;
    const away = days === null ? "" : days === 0 ? "就是今天" : `還有 ${days} 天`;
    const who = first.names.length > 1 ? `${first.names.length} 間合作校申請截止` : `${first.names[0]} 申請截止`;
    return `<span class="mt-next-label">下一站</span><b class="mt-next-date">${when}</b><span class="mt-next-text">${[away, who].filter(Boolean).map(esc).join(" · ")}</span>${pending}`;
  }

  function sync(canvas, model) {
    const route = canvas.closest("[data-metro-route]");
    for (const tag of canvas.querySelectorAll("[data-line-tag]")) tag.setAttribute("aria-pressed", String(tag.dataset.lineTag === focusLine));
    route.dataset.focus = focusLine;
    if (focusLine && !model.some((line) => line.id === focusLine)) { focusLine = ""; route.dataset.focus = ""; }
  }

  function render(host) {
    loadEnglish();
    const route = (host || document).querySelector("[data-metro-route]");
    if (!route) return;
    const canvas = route.querySelector("[data-metro-canvas]");
    const chosen = Boolean(state.homeSchool);
    const name = (chosen ? state.homeSchool : state.dashboard?.school_name) || "選擇就讀學校";
    const partners = state.dashboard?.partner_universities && (!state.homeSchool || state.dashboard.school_name === state.homeSchool) ? state.dashboard.partner_universities : [];
    const key = JSON.stringify([name, chosen, state.dashboard?.last_checked, partners.map((item) => [item.school_name, item.country, item.availability_status, item.application_deadline])]);
    const label = document.querySelector("#mt-board-school-name");
    const boardName = chosen ? name : "選擇就讀學校";
    if (label && label.textContent !== boardName) label.textContent = boardName;
    if (key === signature) return;
    signature = key;
    const next = route.querySelector("[data-metro-next]");
    if (next) { next.innerHTML = partners.length ? nextStopHtml(partners) : ""; next.hidden = !next.innerHTML; }
    if (!partners.length) {
      canvas.innerHTML = `<p class="mt-empty">${chosen ? "合作校資料載入中…" : "選擇就讀學校後，這裡會畫出你能去的合作校路線。"}</p>`;
      route.dataset.state = "empty";
      return;
    }
    const model = buildModel(partners);
    layout(model);
    route.dataset.state = "ready";
    const paths = model.map((line) => `<path class="mt-path" data-line="${line.id}" d="${pathOf(line)}"/>`).join("");
    canvas.innerHTML = `<div class="mt-map" style="aspect-ratio:${W} / ${H}">
      <svg class="mt-lines" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">${paths}</svg>
      ${originHtml(name, chosen)}${model.map(lineHtml).join("")}</div>`;
    sync(canvas, model);
  }

  // A line tag focuses that line (the others dim); pressing it again clears the focus.
  document.addEventListener("click", (event) => {
    const tag = event.target.closest?.("[data-line-tag]");
    if (!tag) return;
    const route = tag.closest("[data-metro-route]");
    const next = tag.dataset.lineTag;
    focusLine = focusLine === next ? "" : next;
    route.dataset.focus = focusLine;
    for (const other of route.querySelectorAll("[data-line-tag]")) other.setAttribute("aria-pressed", String(other.dataset.lineTag === focusLine));
  });

  // The conditions bar fills the explore page's own criteria fields, then opens it, so both pages always agree.
  document.addEventListener("submit", (event) => {
    if (event.target.id !== "mt-board") return;
    event.preventDefault();
    const form = event.target.elements;
    for (const [tile, value] of [["#partner-term-tile", form.term.value], ["#partner-test-tile", form.test.value]]) {
      const field = document.querySelector(tile);
      if (field && field.value !== value) { field.value = value; field.dispatchEvent(new Event("change", { bubbles: true })); }
    }
    window.UniWayHome?.goPartners({ q: form.q.value.trim() });
  });

  // The language-test options come from the explore page's own list, so the two never drift apart.
  function mirrorTestOptions() {
    const source = document.querySelector("#partner-test-tile"), target = document.querySelector("#mt-board-test");
    if (!source || !target || target.options.length > 1) return;
    target.innerHTML = source.innerHTML;
  }
  mirrorTestOptions();
  document.addEventListener("DOMContentLoaded", mirrorTestOptions);
  window.addEventListener("load", mirrorTestOptions);

  return { render, mirrorTestOptions };
})();

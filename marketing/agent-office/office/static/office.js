// UniWay 行銷辦公室 — draws the office from /api/state and animates /api/events.
// Every event is one visible step: a pose change, a new screen, or a sheet of paper flying to the next desk.
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

const CHANNEL = {
  threads: { label: "Threads", color: "#111827" },
  instagram: { label: "Instagram", color: "#d6336c" },
  youtube: { label: "YouTube", color: "#e02424" },
};
const FORMAT = { text: "貼文", reply: "留言回覆", carousel: "輪播", reel: "Reels", story: "限動", short: "Shorts", long: "長影片" };
const STATUS = { pending_approval: "待審核", needs_changes: "需修改", approved: "已核准", publishing: "發佈中", published: "已發佈", failed: "發佈失敗", rejected: "已退回" };
// The departures board speaks airport.
const BOARD = {
  pending_approval: ["待審", "#ffcf5a"], needs_changes: ["需修改", "#ff8b7b"], approved: ["準時", "#8fd0ff"],
  publishing: ["登機中", "#8fd0ff"], published: ["已起飛", "#8ff0bf"], failed: ["延誤", "#ff8b7b"], rejected: ["取消", "#8d97a5"],
};
// Which AI a desk thinks with, printed on the monitor's chin like a brand name.
const BRAIN = {
  "claude-code": { label: "Claude Code", color: "#e08a5c" },
  codex: { label: "Codex", color: "#4fd1a5" },
  antigravity: { label: "Antigravity", color: "#6aa8ff" },
  api: { label: "Claude API", color: "#c9a7ff" },
  offline: { label: "離線範本", color: "#9fb0c8" },
};
const SKIN = ["#f1c7a5", "#e0ac83", "#c98e62", "#f5d0b5", "#d79f76", "#eab894", "#b97d55", "#f0c39f"];
const PENDING = new Set(["pending_approval", "needs_changes"]);

const S = { agents: new Map(), drafts: new Map(), settings: {}, run: null, tz: "Asia/Taipei", tab: "chat", log: [], chat: [], busy: false, typing: new Map() };

// ---------------------------------------------------------------- time
const fmt = (opts) => new Intl.DateTimeFormat("zh-TW", { timeZone: S.tz, hour12: false, ...opts });
const hhmm = (iso) => (iso ? fmt({ hour: "2-digit", minute: "2-digit" }).format(new Date(iso)) : "--:--");
const mmdd = (iso) => (iso ? fmt({ month: "2-digit", day: "2-digit" }).format(new Date(iso)) : "");
function taipeiParts() {
  const parts = Object.fromEntries(fmt({ hour: "numeric", minute: "numeric", second: "numeric" }).formatToParts(new Date()).map((p) => [p.type, p.value]));
  return { h: Number(parts.hour) % 24, m: Number(parts.minute), s: Number(parts.second) };
}

function tickClock() {
  const { h, m } = taipeiParts();
  $("#clock-text").textContent = `台北 ${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
  $("#hand-h").setAttribute("transform", `rotate(${(h % 12) * 30 + m * 0.5} 50 50)`);
  $("#hand-m").setAttribute("transform", `rotate(${m * 6} 50 50)`);
  const win = $("#window");
  const sky =
    h < 5 || h >= 19 ? ["linear-gradient(#0b1730, #1d3560)", "#2a4168", "#17294a", 1]
    : h < 7 ? ["linear-gradient(#f7b267, #f4845f 45%, #8fb8de)", "#8a97b8", "#5c6e94", 0]
    : h < 16 ? ["linear-gradient(#7fbff0, #d6ecfb)", "#9bb6cf", "#6f8fb0", 0]
    : ["linear-gradient(#ff9a62, #c86b98 55%, #4c5c9c)", "#5a5f86", "#3d4470", 0.2];
  win.style.setProperty("--sky", sky[0]);
  win.style.setProperty("--city-far", sky[1]);
  win.style.setProperty("--city-near", sky[2]);
  win.style.setProperty("--stars", sky[3]);
}

function buildClockTicks() {
  const g = $("#wall-clock .ticks");
  g.innerHTML = Array.from({ length: 12 }, (_, i) => `<line x1="50" y1="8" x2="50" y2="${i % 3 ? 12 : 15}" transform="rotate(${i * 30} 50 50)" />`).join("");
}

// ---------------------------------------------------------------- people
function workerSVG(p, index) {
  const skin = SKIN[index % SKIN.length];
  const hair = p.hair_color;
  const shirt = p.shirt;
  const shortHair = `<circle cx="60" cy="41" r="21.5" fill="${hair}" />`;
  const shapes = {
    short: shortHair,
    messy: `${shortHair}<path d="M44 27 L48 15 L53 25 L58 12 L63 24 L68 14 L72 27Z" fill="${hair}" />`,
    bob: `<path d="M35 61 V44 A25 25 0 0 1 85 44 V61 Z" fill="${hair}" />`,
    bun: `${shortHair}<circle cx="60" cy="19" r="9" fill="${hair}" />`,
    long: shortHair,
    ponytail: `${shortHair}<rect x="55" y="57" width="10" height="5" rx="2" fill="#e2574a" />`,
    curly: Array.from({ length: 11 }, (_, i) => {
      const a = (Math.PI * (i - 0.5)) / 9 + Math.PI;
      return `<circle cx="${60 + 17 * Math.cos(a)}" cy="${42 + 17 * Math.sin(a) * 1.05}" r="8" fill="${hair}" />`;
    }).join("") + `<circle cx="60" cy="40" r="16" fill="${hair}" />`,
    cap: `${shortHair}<path d="M37 41 A23 23 0 0 1 83 41 Z" fill="${shirt}" /><path d="M54 41 A6 5 0 0 1 66 41" fill="none" stroke="#1d2433" stroke-width="2.5" /><circle cx="60" cy="19" r="2.5" fill="#fff" />`,
  };
  const over = {
    long: `<path d="M37 44 Q34 78 44 94 L76 94 Q86 78 83 44 Z" fill="${hair}" />`,
    ponytail: `<ellipse cx="60" cy="76" rx="7.5" ry="15" fill="${hair}" />`,
  };
  const acc = {
    headphones: `<path d="M36 44 A24 24 0 0 1 84 44" fill="none" stroke="#1d2433" stroke-width="4.5" /><rect x="30" y="37" width="10" height="17" rx="4" fill="#1d2433" /><rect x="80" y="37" width="10" height="17" rx="4" fill="#1d2433" />`,
    glasses: `<path d="M37 45 L45 44 M83 45 L75 44" stroke="#1d2433" stroke-width="2" />`,
    beret: `<ellipse cx="63" cy="23" rx="22" ry="7" fill="#2b2f45" transform="rotate(-10 63 23)" /><rect x="61" y="13" width="3" height="5" rx="1.5" fill="#2b2f45" />`,
    hoodie: "",
  };
  const hood = p.accessory === "hoodie" ? `<path d="M38 72 Q60 92 82 72 Q80 63 60 63 Q40 63 38 72Z" fill="${shade(shirt, -18)}" />` : "";
  // Elbows out, hands on the keyboard just past the ears, so both arms show around the head.
  const arm = (side, x1, x2) =>
    `<g class="arm ${side}"><path d="M${x1} 78 Q${x1 + (x2 > 60 ? 6 : -6)} 50 ${x2} 22" fill="none" stroke="${shade(shirt, 12)}" stroke-width="12" stroke-linecap="round" /><circle class="hand ${side}" cx="${x2}" cy="18" r="6.5" fill="${skin}" /></g>`;
  return `<svg viewBox="0 0 120 112" aria-hidden="true">
    ${arm("l", 28, 31)}${arm("r", 92, 89)}
    <path d="M14 114 C14 82 30 66 60 66 C90 66 106 82 106 114Z" fill="${shirt}" />
    ${hood}
    <g class="head">
      <rect x="53" y="55" width="14" height="14" rx="4" fill="${skin}" />
      <circle cx="38.5" cy="46" r="5" fill="${skin}" /><circle cx="81.5" cy="46" r="5" fill="${skin}" />
      <circle cx="60" cy="44" r="21" fill="${skin}" />
      ${shapes[p.hair] || shortHair}${acc[p.accessory] || ""}
    </g>
    ${over[p.hair] || ""}
    <rect x="20" y="82" width="80" height="34" rx="14" class="chair" />
    <rect x="26" y="85" width="68" height="7" rx="3.5" class="chair-top" />
  </svg>`;
}

function shade(hex, amount) {
  const n = parseInt(hex.slice(1), 16);
  const ch = (v) => Math.max(0, Math.min(255, v + amount));
  return `rgb(${ch(n >> 16)}, ${ch((n >> 8) & 255)}, ${ch(n & 255)})`;
}

const DECOR = {
  notes: `<svg class="decor" viewBox="0 0 34 34"><rect x="4" y="8" width="16" height="16" fill="#ffd166" transform="rotate(-8 12 16)" /><rect x="13" y="6" width="16" height="16" fill="#9be7c4" transform="rotate(6 21 14)" /></svg>`,
  tea: `<svg class="decor" viewBox="0 0 34 34"><path d="M9 10 H25 L22 31 H12 Z" fill="#e9d6bf" /><rect x="8" y="7" width="18" height="4" rx="2" fill="#fff" /><circle cx="14" cy="27" r="2" fill="#3b2a20" /><circle cx="19" cy="25" r="2" fill="#3b2a20" /><rect x="18" y="0" width="3" height="11" fill="#e2574a" transform="rotate(12 19 6)" /></svg>`,
  palette: `<svg class="decor" viewBox="0 0 34 34"><path d="M17 4 C27 4 32 11 30 18 C28 23 22 20 20 24 C18 29 13 31 9 28 C3 24 4 12 9 8 C11 6 14 4 17 4Z" fill="#f4e4c9" /><circle cx="12" cy="13" r="3" fill="#e2574a" /><circle cx="19" cy="10" r="3" fill="#2f7de1" /><circle cx="25" cy="14" r="3" fill="#ffd166" /><circle cx="11" cy="21" r="3" fill="#1f9d68" /></svg>`,
  clapper: `<svg class="decor" viewBox="0 0 34 34"><rect x="5" y="13" width="24" height="16" rx="2" fill="#1d2433" /><path d="M5 8 L28 4 L29 10 L6 14Z" fill="#fff" /><path d="M9 7 L12 13 M15 6 L18 12 M21 5 L24 11" stroke="#1d2433" stroke-width="2.5" /></svg>`,
  magnifier: `<svg class="decor" viewBox="0 0 34 34"><circle cx="14" cy="14" r="8" fill="#dff1ff" stroke="#1d2433" stroke-width="3" /><path d="M20 20 L29 29" stroke="#8a5a2b" stroke-width="5" stroke-linecap="round" /></svg>`,
  rocket: `<svg class="decor" viewBox="0 0 34 34"><path d="M17 3 C23 8 24 17 21 25 H13 C10 17 11 8 17 3Z" fill="#e8edf4" /><circle cx="17" cy="13" r="3" fill="#2f7de1" /><path d="M13 21 L8 27 L13 26Z M21 21 L26 27 L21 26Z" fill="#e2574a" /><path d="M14 26 L17 32 L20 26Z" fill="#ffb347" /></svg>`,
  chart: `<svg class="decor" viewBox="0 0 34 34"><rect x="4" y="5" width="26" height="22" rx="2" fill="#fff" /><rect x="8" y="17" width="4" height="7" fill="#17b5d8" /><rect x="15" y="12" width="4" height="12" fill="#2f7de1" /><rect x="22" y="8" width="4" height="16" fill="#e2574a" /><rect x="15" y="27" width="4" height="5" fill="#9aa5b3" /></svg>`,
  walkie: `<svg class="decor" viewBox="0 0 34 34"><rect x="10" y="9" width="14" height="23" rx="3" fill="#1d2433" /><rect x="13" y="13" width="8" height="6" rx="1" fill="#8ff0bf" /><rect x="19" y="1" width="3" height="9" rx="1.5" fill="#1d2433" /><circle cx="17" cy="25" r="2.5" fill="#56637a" /></svg>`,
  heart: `<svg class="decor" viewBox="0 0 34 34"><rect x="9" y="20" width="16" height="12" rx="2" fill="#c98e62" /><path d="M17 20 C10 14 8 9 12 6 C15 4 17 7 17 8 C17 7 19 4 22 6 C26 9 24 14 17 20Z" fill="#ff6b8a" /></svg>`,
};

function buildDesks(agents) {
  const host = $("#desks");
  host.innerHTML = "";
  $(".boss-row .desk[data-agent='chief']")?.remove();
  agents.forEach((a, i) => {
    const desk = document.createElement("article");
    desk.className = "desk";
    desk.dataset.agent = a.id;
    desk.dataset.state = a.state || "idle";
    desk.tabIndex = 0;
    desk.setAttribute("aria-label", `${a.name}，${a.title}`);
    desk.innerHTML = `
      <div class="bubble"><span class="bubble-text"></span></div>
      <div class="monitor"><div class="screen"></div><span class="brain-tag"><i></i><span></span></span></div>
      <div class="table"><div class="mug"></div><div class="keyboard"></div>${DECOR[a.decor] || ""}</div>
      <div class="worker">${workerSVG(a, i)}</div>
      <div class="plate"><b>${esc(a.name)}</b><span>${esc(a.title)}</span></div>`;
    desk.addEventListener("click", () => openAgent(a.id));
    desk.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), openAgent(a.id)));
    // The chief sits beside your desk: everything you ask goes through them.
    if (a.id === "chief") $(".boss-row").prepend(desk);
    else host.appendChild(desk);
    updateDesk(a.id);
  });
}

function updateDesk(id) {
  const a = S.agents.get(id);
  const desk = $(`.desk[data-agent="${id}"]`);
  if (!a || !desk) return;
  desk.dataset.state = a.state || "idle";
  const text = a.message || "待命中";
  $(".bubble-text", desk).textContent = text;
  $(".bubble", desk).title = text;
  const brain = BRAIN[a.brain] || null;
  const tag = $(".brain-tag", desk);
  tag.hidden = !brain;
  if (brain) {
    $("span", tag).textContent = brain.label;
    tag.style.setProperty("--bc", brain.color);
    tag.title = `這台電腦現在用 ${brain.label}`;
  }
  renderScreen($(".screen", desk), a.screen, id);
}

// ---------------------------------------------------------------- monitors
function renderScreen(el, screen, id, big = false) {
  if (!screen) {
    el.innerHTML = `<div class="scr scr-empty"><div><img src="/brand/uniway-logo.webp" alt="" /><span>待命中</span></div></div>`;
    return;
  }
  const media = (ref) => `/media/${ref.split("/").map(encodeURIComponent).join("/")}`;
  switch (screen.type) {
    case "lines":
      el.innerHTML = `<div class="scr scr-lines"><h4>${esc(screen.title)}</h4><ul>${(screen.lines || []).map((l) => `<li>${esc(l)}</li>`).join("")}</ul></div>`;
      break;
    case "compose": {
      el.innerHTML = `<div class="scr scr-compose"><div class="who"><i></i>uniway</div><p></p><div class="reply">↳ 第一則留言：${esc(screen.reply || "")}</div></div>`;
      typeInto($("p", el), screen.text || "", big ? null : id);
      break;
    }
    case "images": {
      const imgs = (screen.images || []).slice(-6);
      el.innerHTML = `<div class="scr scr-images">${imgs.map((r) => `<img src="${media(r)}" alt="" loading="lazy" />`).join("") || '<div class="scr-empty">構圖中</div>'}<span class="label">${esc(screen.label || "")}</span></div>`;
      break;
    }
    case "video": {
      const pct = Math.round((screen.progress || 0) * 100);
      el.innerHTML = `<div class="scr scr-video">${screen.poster ? `<img src="${media(screen.poster)}" alt="" />` : ""}<span class="label">${esc(screen.label || "")}</span><div class="bar"><i style="width:${pct}%"></i></div></div>`;
      break;
    }
    case "checklist":
      el.innerHTML = `<div class="scr scr-checklist"><h4>審稿清單</h4><ul style="list-style:none;margin:0;padding:0">${(screen.items || [])
        .map((it) => `<li><span class="${it.ok === true ? "ok" : it.ok === false ? "bad" : "wait"}">${it.ok === true ? "✓" : it.ok === false ? "✗" : "○"}</span>${esc(it.label)}</li>`)
        .join("")}</ul></div>`;
      break;
    case "terminal":
      el.innerHTML = `<div class="scr scr-terminal">${(screen.lines || []).map((l) => `<div>$ ${esc(l)}</div>`).join("") || "<div>$ 等待排程…</div>"}</div>`;
      break;
    case "chart": {
      const bars = screen.bars || [];
      const max = Math.max(1, ...bars.map((b) => b.value));
      el.innerHTML = bars.length
        ? `<div class="scr scr-chart">${bars.map((b) => `<div class="col"><i style="height:${Math.max(4, (b.value / max) * 64)}px;--c:${CHANNEL[b.channel]?.color || "#2f7de1"}"></i>${esc(b.label.slice(0, 4))}</div>`).join("")}</div>`
        : `<div class="scr scr-empty">還沒有成效數據</div>`;
      break;
    }
    case "chat":
      el.innerHTML = `<div class="scr scr-chat">${(screen.messages || []).map((m) => `<div class="${m.from === "我們" ? "us" : ""}">${esc(m.from)}：${esc(m.text)}</div>`).join("")}</div>`;
      break;
    default:
      el.innerHTML = `<div class="scr scr-empty">${esc(screen.type)}</div>`;
  }
}

// Threads drafts appear as if typed, so you can watch the writer write.
function typeInto(el, text, key) {
  if (key) {
    const previous = S.typing.get(key);
    if (previous) cancelAnimationFrame(previous.frame);
  }
  if (reduceMotion || !key) {
    el.textContent = text;
    return;
  }
  const duration = Math.min(2200, 30 * text.length);
  const start = performance.now();
  const step = (now) => {
    const n = Math.round((text.length * Math.min(1, (now - start) / duration)));
    el.innerHTML = `${esc(text.slice(0, n))}${n < text.length ? '<span class="caret"></span>' : ""}`;
    if (n < text.length) S.typing.set(key, { frame: requestAnimationFrame(step) });
  };
  S.typing.set(key, { frame: requestAnimationFrame(step) });
}

// ---------------------------------------------------------------- paper flights
async function fly(from, to, label) {
  const src = $(`.desk[data-agent="${from}"] .monitor`);
  const dst = $(`.desk[data-agent="${to}"] .monitor`);
  if (!src || !dst) return;
  const target = dst.closest(".desk");
  if (reduceMotion) {
    target.classList.add("receiving");
    setTimeout(() => target.classList.remove("receiving"), 600);
    return;
  }
  const a = src.getBoundingClientRect();
  const b = dst.getBoundingClientRect();
  const paper = document.createElement("div");
  paper.className = "paper";
  paper.innerHTML = `<span>${esc(label)}</span>`;
  $("#flights").appendChild(paper);
  const x0 = a.left + a.width / 2 - 27, y0 = a.top + a.height / 2 - 33;
  const x1 = b.left + b.width / 2 - 27, y1 = b.top + b.height / 2 - 33;
  const lift = Math.min(160, 40 + Math.hypot(x1 - x0, y1 - y0) * 0.25);
  const frames = Array.from({ length: 13 }, (_, i) => {
    const t = i / 12;
    const x = x0 + (x1 - x0) * t;
    const y = y0 + (y1 - y0) * t - Math.sin(Math.PI * t) * lift;
    return { transform: `translate(${x}px, ${y}px) rotate(${Math.sin(Math.PI * t * 2) * 10}deg) scale(${1 - Math.sin(Math.PI * t) * -0.08})`, opacity: t > 0.92 ? 0.3 : 1 };
  });
  await paper.animate(frames, { duration: 900, easing: "ease-in-out" }).finished.catch(() => {});
  paper.remove();
  target.classList.add("receiving");
  setTimeout(() => target.classList.remove("receiving"), 600);
}

// ---------------------------------------------------------------- the boss desk, the board and the whiteboard
function todayDrafts() {
  const day = S.run?.day;
  return [...S.drafts.values()].filter((d) => d.day === day && d.format !== "reply").sort((x, y) => (x.scheduled_at || "").localeCompare(y.scheduled_at || "") || x.id - y.id);
}

function renderBoard(changedId) {
  const rows = todayDrafts();
  const host = $("#board-rows");
  if (!rows.length) {
    host.innerHTML = `<li class="board-empty">今天還沒有發文。按右上角「開始今天的工作」，或等 ${esc(S.settings.daily_at || "07:30")} 自動開工。</li>`;
    return;
  }
  host.innerHTML = rows.slice(0, 8).map((d) => {
    const [word, color] = BOARD[d.status] || [d.status, "#ffcf5a"];
    const time = hhmm(d.scheduled_at).replace(":", "");
    const ch = CHANNEL[d.channel];
    return `<li class="board-row${d.id === changedId ? " flip" : ""}">
      <span class="flaps">${[...time].map((c, i) => `${i === 2 ? '<span class="flap">:</span>' : ""}<span class="flap">${esc(c)}</span>`).join("")}</span>
      <span class="platform" title="${ch.label} ${FORMAT[d.format] || ""}"><i style="--c:${ch.color === "#111827" ? "#e6edf7" : ch.color}"></i><span class="pl-label">${ch.label} ${FORMAT[d.format] || ""}</span></span>
      <span class="title">${esc(d.title)}</span>
      <span class="status-word" style="--sc:${color}">${word}</span>
    </li>`;
  }).join("");
}

function renderWhiteboard() {
  const plan = S.run?.plan;
  $("#wb-theme").textContent = plan?.theme || (S.run ? "排程中" : "還沒開工");
  $("#wb-notes").innerHTML = (plan?.whiteboard || []).map((n) => `<li>${esc(n)}</li>`).join("");
}

function renderBoss() {
  const pending = [...S.drafts.values()].filter((d) => PENDING.has(d.status));
  const needs = pending.filter((d) => d.status === "needs_changes").length;
  $("#boss-bubble").textContent = pending.length ? `${pending.length} 則等你審核${needs ? `（${needs} 則需修改）` : ""}` : "審核匣是空的";
  $("#boss-screen").innerHTML = `<div class="scr scr-boss"><div><b>${pending.length}</b></div><div>則待審</div></div>`;
  $("#tray").innerHTML = pending.slice(0, 6).map((_, i) => `<b style="top:${10 - i * 3}px;transform:rotate(${(i % 2 ? 4 : -3)}deg)"></b>`).join("");
  $('.desk[data-agent="boss"]').dataset.state = pending.length ? "waiting" : "idle";
  const count = $("#inbox-count");
  count.textContent = pending.length;
  count.toggleAttribute("data-zero", !pending.length);
}

// ---------------------------------------------------------------- inbox (boarding passes)
function renderPanel() {
  renderInbox();
  renderSchedule();
  renderLog();
}

function renderInbox() {
  const host = $("#view-inbox");
  const items = [...S.drafts.values()].filter((d) => PENDING.has(d.status)).sort((x, y) => (x.scheduled_at || "9").localeCompare(y.scheduled_at || "9") || x.id - y.id);
  const editing = host.querySelector(".pass.editing")?.dataset.id;
  if (!items.length) {
    host.innerHTML = `<p class="empty">沒有等你審核的內容。<br />新的草稿會像登機證一樣送到這裡。</p>`;
    return;
  }
  host.innerHTML = items.map(passHTML).join("");
  if (editing) host.querySelector(`.pass[data-id="${editing}"]`)?.classList.add("editing");
}

function passHTML(d) {
  const ch = CHANNEL[d.channel];
  const review = d.review || {};
  const issues = review.issues || [];
  const future = d.scheduled_at && new Date(d.scheduled_at) > new Date();
  const approveLabel = d.format === "reply" ? "核准並回覆" : future ? `核准，${hhmm(d.scheduled_at)} 發佈` : "核准並發佈";
  return `<article class="pass" data-id="${d.id}">
    <div class="pass-main">
      <div class="pass-head"><span class="chip"><i style="--c:${ch.color}"></i>${ch.label}</span><span>${FORMAT[d.format] || d.format}</span><span class="chip state-${d.status}">${STATUS[d.status]}</span></div>
      <h3>${esc(d.title)}</h3>
      <div class="preview">${previewHTML(d)}</div>
      ${issues.length ? `<ul class="issues">${issues.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : ""}
      ${(review.notes || []).length ? `<p class="notes">審稿備註：${esc(review.notes.join("；"))}</p>` : ""}
      <div class="editor"></div>
      <div class="actions">
        <button class="btn primary" data-act="approve" type="button">${approveLabel}</button>
        ${future ? '<button class="btn" data-act="now" type="button">立即發佈</button>' : ""}
        ${editableFields(d).length ? '<button class="btn" data-act="edit" type="button">修改文字</button>' : ""}
        <button class="btn danger" data-act="reject" type="button">退回</button>
      </div>
    </div>
    <div class="pass-stub"><span class="time">${d.scheduled_at ? hhmm(d.scheduled_at) : "回覆"}</span><span class="date">${mmdd(d.scheduled_at)}</span><span class="no">#${d.id}</span></div>
  </article>`;
}

function previewHTML(d) {
  const p = d.payload || {};
  const m = d.media || {};
  const media = (ref) => `/media/${ref.split("/").map(encodeURIComponent).join("/")}`;
  if (d.format === "reply") {
    return `<p class="sub"><b>@${esc(p.username || "訪客")} 的留言</b>\n${esc(p.comment_text)}</p><p class="post" style="margin-top:8px">${esc(p.text)}</p>`;
  }
  if (d.channel === "threads") {
    return `<p class="post">${esc(p.text)}</p><p class="sub"><b>第一則留言</b>\n${esc(p.first_reply)}</p><p class="sub">主題標籤：${esc(p.topic_tag)}${p.source_url ? `｜<a href="${esc(p.source_url)}" target="_blank" rel="noopener">官方來源</a>` : ""}</p>`;
  }
  if (d.format === "carousel") {
    const thumbs = (m.images || []).map((r) => `<button type="button" data-zoom="${media(r)}"><img src="${media(r)}" alt="輪播圖" loading="lazy" /></button>`).join("");
    return `${thumbs ? `<div class="thumbs">${thumbs}</div>` : ""}<p class="sub">${esc(p.caption_full || p.caption)}</p>`;
  }
  if (d.format === "story") {
    return m.image ? `<div class="thumbs story"><button type="button" data-zoom="${media(m.image)}"><img src="${media(m.image)}" alt="限時動態" /></button></div>` : "";
  }
  const video = m.video ? `<video controls preload="none" playsinline ${m.poster ? `poster="${media(m.poster)}"` : ""} src="${media(m.video)}"></video>` : "";
  if (d.channel === "youtube") {
    return `${video}<p class="sub"><b>${esc(p.title)}</b>\n${esc(p.description)}</p>`;
  }
  return `${video}<p class="sub">${esc(p.caption_full || p.caption)}</p>`;
}

function editableFields(d) {
  if (d.format === "reply") return [["text", "回覆內容"]];
  if (d.channel === "threads") return [["text", "主文"], ["first_reply", "第一則留言"]];
  if (d.channel === "instagram" && d.format !== "story") return [["caption_full", "說明欄"]];
  if (d.channel === "youtube") return [["title", "標題"], ["description", "描述"]];
  return [];
}

async function api(path, body, method = "POST") {
  const res = await fetch(path, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

async function onPassClick(e) {
  const zoom = e.target.closest("[data-zoom]");
  if (zoom) {
    $("#lightbox-img").src = zoom.dataset.zoom;
    $("#lightbox").showModal();
    return;
  }
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const pass = btn.closest(".pass");
  const id = Number(pass.dataset.id);
  const d = S.drafts.get(id);
  try {
    if (btn.dataset.act === "approve" || btn.dataset.act === "now") {
      btn.disabled = true;
      upsertDraft(await api(`/api/drafts/${id}/approve`, { now: btn.dataset.act === "now" || !d.scheduled_at }));
      toast(btn.dataset.act === "now" ? "已核准，馬上發佈" : `已核准，${hhmm(d.scheduled_at)} 發佈`);
    } else if (btn.dataset.act === "reject") {
      const note = prompt("退回原因（可留白）", "") ;
      if (note === null) return;
      upsertDraft(await api(`/api/drafts/${id}/reject`, { note }));
      toast("已退回");
    } else if (btn.dataset.act === "edit") {
      pass.classList.add("editing");
      $(".editor", pass).innerHTML = editableFields(d).map(([key, label]) =>
        `<label for="f-${id}-${key}">${label}</label><textarea id="f-${id}-${key}" data-key="${key}">${esc(d.payload[key] || "")}</textarea>`).join("") +
        `<div class="actions"><button class="btn primary" data-act="save" type="button">儲存修改</button><button class="btn" data-act="cancel" type="button">取消</button></div>`;
      $("textarea", pass)?.focus();
    } else if (btn.dataset.act === "save") {
      const changes = Object.fromEntries([...pass.querySelectorAll("textarea")].map((t) => [t.dataset.key, t.value]));
      pass.classList.remove("editing");
      upsertDraft(await api(`/api/drafts/${id}`, changes, "PATCH"));
      toast("已儲存修改");
    } else if (btn.dataset.act === "cancel") {
      pass.classList.remove("editing");
      renderInbox();
    }
  } catch (err) {
    btn.disabled = false;
    toast(err.message);
  }
}

// ---------------------------------------------------------------- schedule and log
function renderSchedule() {
  const host = $("#view-schedule");
  const items = [...S.drafts.values()].filter((d) => !PENDING.has(d.status));
  if (!items.length) {
    host.innerHTML = `<p class="empty">核准後的內容會排在這裡，發佈後可以直接點開貼文。</p>`;
    return;
  }
  const groups = new Map();
  items.sort((x, y) => (y.scheduled_at || y.updated_at || "").localeCompare(x.scheduled_at || x.updated_at || ""));
  for (const d of items) {
    const key = d.day;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(d);
  }
  host.innerHTML = [...groups].map(([day, list]) => `<section class="sched-group"><h3>${esc(day)}</h3>${list.map((d) => {
    const ch = CHANNEL[d.channel];
    const link = d.remote_url ? `<a href="${esc(d.remote_url)}" target="_blank" rel="noopener">查看貼文</a>` : d.note ? `<span class="chip">${esc(d.note.slice(0, 6))}</span>` : "";
    return `<div class="sched-item"><span class="t">${d.scheduled_at ? hhmm(d.scheduled_at) : "--:--"}</span><span class="ttl"><span class="chip"><i style="--c:${ch.color}"></i>${ch.label} ${FORMAT[d.format] || ""}</span> ${esc(d.title)}</span><span class="chip state-${d.status}">${STATUS[d.status]}</span>${link ? `<span></span><span style="grid-column:2/-1;font-size:13px">${link}</span>` : ""}${d.error ? `<span class="err">${esc(d.error)}</span>` : ""}</div>`;
  }).join("")}</section>`).join("");
}

function who(agentId) {
  if (agentId === "boss") return "辦公室";
  const a = S.agents.get(agentId);
  return a ? a.name : agentId;
}

function logLine(e) {
  if (e.kind === "draft" || e.kind === "chat") return null;
  const to = e.kind === "handoff" ? ` → ${who(e.to || e.data?.to)}` : "";
  return { ts: e.ts, agent: e.agent, text: `${e.message}${to}` };
}

function renderLog() {
  $("#log").innerHTML = S.log.slice(-200).reverse().map((l) => `<li><time>${hhmm(l.ts)}</time><span class="who">${esc(who(l.agent))}</span><span>${esc(l.text)}</span></li>`).join("");
}

// ---------------------------------------------------------------- the chief's chat
function renderChat() {
  const host = $("#chat");
  if (!S.chat.length) {
    host.innerHTML = `<li class="msg chief"><p>我是總管 Leo。你直接跟我說要做什麼就好：開工、問進度、請某位同事重寫某一則（用審核匣上的 #編號）、加做一則、改發文時間，或記給明天的企劃。核准和發文還是由你自己按。</p></li>`;
    return;
  }
  host.innerHTML = S.chat.map((m) => {
    const who = m.sender === "boss" ? "boss" : "chief";
    const body = esc(m.text).replace(/#(\d+)/g, '<button type="button" class="ref" data-draft="$1">#$1</button>');
    return `<li class="msg ${who}"><p>${body}</p><time>${hhmm(m.ts)}</time></li>`;
  }).join("");
  host.lastElementChild?.scrollIntoView({ block: "end", behavior: reduceMotion ? "auto" : "smooth" });
}

async function sendChat(text) {
  text = text.trim();
  if (!text) return;
  $("#chat-input").value = "";
  try {
    await api("/api/chat", { text });
  } catch (err) {
    toast(err.message);
  }
}

function showDraft(id) {
  const d = S.drafts.get(Number(id));
  if (!d) return toast(`找不到 #${id}`);
  selectTab(PENDING.has(d.status) ? "inbox" : "schedule");
  const pass = $(`.pass[data-id="${id}"]`);
  pass?.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
  pass?.classList.add("flash");
  setTimeout(() => pass?.classList.remove("flash"), 1200);
}

// ---------------------------------------------------------------- agent card
function openAgent(id) {
  if (id === "boss") {
    selectTab("inbox");
    $(".panel").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    return;
  }
  const a = S.agents.get(id);
  const lines = S.log.filter((l) => l.agent === id).slice(-30).reverse();
  const roles = id === "strategist" ? [["research", "查資料"], ["strategist", "企劃"]] : [[id, ""]];
  const chains = roles
    .filter(([role]) => S.settings.brains?.[role])
    .map(([role, what]) => `${what ? `${what}：` : ""}${S.settings.brains[role][0]}${S.settings.brains[role].length > 1 ? `（不行時改用 ${S.settings.brains[role].slice(1).join(" → ")}）` : ""}`);
  $("#agent-card-body").innerHTML = `<h2>${esc(a.name)}｜${esc(a.title)}</h2><p class="duty">${esc(a.duty)}</p>
    ${chains.length ? `<p class="duty">這台電腦用 ${esc(chains.join("；"))}</p>` : ""}
    <div class="big-screen"></div>
    <ol>${lines.map((l) => `<li><time>${hhmm(l.ts)}</time><span>${esc(l.text)}</span></li>`).join("") || "<li><time></time><span>今天還沒有動作</span></li>"}</ol>`;
  renderScreen($("#agent-card-body .big-screen"), a.screen, id, true);
  $("#agent-card").showModal();
}

// ---------------------------------------------------------------- events
function upsertDraft(d) {
  S.drafts.set(d.id, d);
  renderBoss();
  renderBoard(d.id);
  renderPanel();
}

const queue = [];
let playing = false;
function enqueue(e) {
  queue.push(e);
  if (!playing) play();
}
async function play() {
  playing = true;
  while (queue.length) {
    const e = queue.shift();
    const wait = apply(e);
    if (wait) await (wait.then ? wait : sleep(queue.length > 40 ? wait / 5 : wait));
  }
  playing = false;
}

// Apply one event; returns how long to hold before the next, so a fast run is still watchable.
function apply(e) {
  const line = logLine(e);
  if (line) S.log.push(line);
  if (S.tab === "log" && line) renderLog();
  switch (e.kind) {
    case "status": {
      const a = S.agents.get(e.agent);
      if (!a) return 0;
      a.state = e.state;
      a.message = e.message;
      if (e.screen) a.screen = e.screen;
      updateDesk(e.agent);
      if (e.agent === "chief") $("#chat-typing").hidden = e.state !== "thinking";
      return 260;
    }
    case "chat":
      S.chat.push(e.chat);
      renderChat();
      if (S.tab !== "chat" && e.sender === "chief") $("#chat-unread").hidden = false;
      return 120;
    case "brain": {
      const a = S.agents.get(e.agent);
      if (!a) return 0;
      a.brain = e.brain;
      if (e.fallback) a.message = e.message;
      updateDesk(e.agent);
      return e.fallback ? 600 : 120;
    }
    case "handoff":
      return queue.length > 40 ? 0 : fly(e.agent, e.to, e.message);
    case "draft":
      upsertDraft(e.draft);
      return 80;
    case "whiteboard":
      S.run = { ...(S.run || {}), plan: { ...(S.run?.plan || {}), theme: e.message, whiteboard: e.notes } };
      renderWhiteboard();
      return 300;
    case "run":
      if (e.state === "running") {
        S.run = { id: e.run_id, day: S.today, plan: null };
        S.busy = true;
        renderWhiteboard();
        renderBoard();
        toast("開工了：企劃先排今天的內容");
      } else {
        S.busy = false;
        toast(e.message);
      }
      $("#run-btn").disabled = S.busy;
      return 0;
    default:
      return 0;
  }
}

function connect() {
  const source = new EventSource("/api/events");
  let dropped = false;
  source.onmessage = (msg) => enqueue(JSON.parse(msg.data));
  source.onerror = () => { dropped = true; };
  source.onopen = () => {
    if (dropped) load();
    dropped = false;
  };
}

async function load() {
  const res = await fetch("/api/state");
  if (!res.ok) {
    document.body.innerHTML = `<p class="empty">辦公室打不開（HTTP ${res.status}）。如果有設定通行碼，請用 ?token=… 開啟。</p>`;
    return false;
  }
  const state = await res.json();
  S.tz = state.timezone || S.tz;
  S.today = state.today;
  S.settings = state.settings;
  S.run = state.run;
  S.busy = state.busy;
  S.agents = new Map(state.agents.map((a) => [a.id, a]));
  S.drafts = new Map(state.drafts.map((d) => [d.id, d]));
  S.log = state.events.map(logLine).filter(Boolean);
  S.chat = state.chat || [];
  renderModes();
  buildDesks(state.agents);
  renderWhiteboard();
  renderBoard();
  renderBoss();
  renderPanel();
  renderChat();
  $("#run-btn").disabled = S.busy;
  return true;
}

function renderModes() {
  const s = S.settings;
  const modes = [
    s.dry_run ? ["warn", "模擬發佈：不會真的送出"] : ["live", "正式發佈"],
    s.approval === "auto" ? ["live", "審稿通過就自動排程"] : ["", "每則都等你核准"],
    brainMode(s),
  ];
  if (s.images) modes.push(["live", `插圖：${s.images}`]);
  $("#modes").innerHTML = modes.map(([cls, text]) => `<span class="mode ${cls}"><i></i>${esc(text)}</span>`).join("");
}

function brainMode(s) {
  const first = [...new Set(Object.values(s.brains || {}).map((chain) => chain[0]))];
  if (first.length === 1 && first[0] === "離線範本") return ["warn", "AI：離線範本"];
  return ["live", `AI：${first.filter((label) => label !== "離線範本").join("、")}`];
}

function selectTab(tab) {
  S.tab = tab;
  document.querySelectorAll(".tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== `view-${tab}`));
  if (tab === "log") renderLog();
  if (tab === "chat") {
    $("#chat-unread").hidden = true;
    renderChat();
  }
}

let toastTimer;
function toast(text) {
  const el = $("#toast");
  el.textContent = text;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
}

async function startDay() {
  const ranToday = S.run && S.run.day === S.today;
  if (ranToday && !confirm("今天已經跑過一次了，要讓大家再做一份嗎？")) return;
  $("#run-btn").disabled = true;
  try {
    await api("/api/run", { force: Boolean(ranToday) });
  } catch (err) {
    $("#run-btn").disabled = false;
    toast(err.message);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  document.body.classList.toggle("tv", new URLSearchParams(location.search).has("tv"));
  buildClockTicks();
  tickClock();
  setInterval(tickClock, 15000);
  document.querySelector(".tabs").addEventListener("click", (e) => e.target.closest("button[data-tab]") && selectTab(e.target.closest("button[data-tab]").dataset.tab));
  $("#view-inbox").addEventListener("click", onPassClick);
  $("#chat-form").addEventListener("submit", (e) => (e.preventDefault(), sendChat($("#chat-input").value)));
  $("#chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) (e.preventDefault(), sendChat(e.target.value));
  });
  $("#chat-chips").addEventListener("click", (e) => e.target.closest("button") && sendChat(e.target.textContent));
  $("#chat").addEventListener("click", (e) => e.target.closest("[data-draft]") && showDraft(e.target.closest("[data-draft]").dataset.draft));
  $("#run-btn").addEventListener("click", startDay);
  const boss = $('.desk[data-agent="boss"]');
  boss.addEventListener("click", () => openAgent("boss"));
  boss.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), openAgent("boss")));
  if (await load()) connect();
});

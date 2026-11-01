// UniWay 辦公室，手機版：跟 Leo 說話、審核匣、已排程、動態。資料全部來自 /api/state 和 /api/events，跟電腦版同一份。
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const CHANNEL = { threads: "Threads", instagram: "Instagram", youtube: "YouTube", github: "GitHub" };
const FORMAT = { text: "貼文", reply: "留言回覆", carousel: "輪播", reel: "Reels", story: "限動", short: "Shorts", long: "長影片", data_update: "資料更新提案" };
const STATUS = { pending_approval: "待審核", needs_changes: "需修改", approved: "已核准", publishing: "發佈中", published: "已發佈", failed: "發佈失敗", rejected: "已退回" };
const PENDING = new Set(["pending_approval", "needs_changes"]);

const S = { drafts: new Map(), chat: [], log: [], agents: new Map(), run: null, today: "", tz: "Asia/Taipei", tab: "chat", armedRun: false };

// ---------------------------------------------------------------- time
const fmt = (opts) => new Intl.DateTimeFormat("zh-TW", { timeZone: S.tz, hour12: false, ...opts });
const hhmm = (iso) => (iso ? fmt({ hour: "2-digit", minute: "2-digit" }).format(new Date(iso)) : "--:--");
const mmdd = (iso) => (iso ? fmt({ month: "2-digit", day: "2-digit" }).format(new Date(iso)) : "");

// ---------------------------------------------------------------- talking to the office
async function api(path, body, method = "POST") {
  const res = await fetch(path, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

let toastTimer;
function toast(text) {
  const el = $("#toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 3400);
}

function setStatus(text, kind = "") {
  const el = $("#status");
  el.textContent = text;
  el.className = kind;
}

// ---------------------------------------------------------------- chat
function renderChat(toEnd = false) {
  const host = $("#chat");
  const view = $("#view-chat");
  const stick = toEnd || view.scrollHeight - view.scrollTop - view.clientHeight < 120 || !host.children.length;
  if (!S.chat.length) {
    host.innerHTML = `<li class="msg chief"><p>我是總管 Leo。直接跟我說要做什麼：開工、問進度、請同事重寫某一則（用編號，例如 #3）、加做一則、改發文時間、記給明天的企劃。核准和發文還是由你自己按。</p></li>`;
    return;
  }
  host.innerHTML = S.chat.map((m) => {
    const who = m.sender === "boss" ? "boss" : "chief";
    const body = esc(m.text).replace(/#(\d+)/g, '<button type="button" class="ref" data-draft="$1">#$1</button>');
    return `<li class="msg ${who}"><p>${body}</p><time>${hhmm(m.ts)}</time></li>`;
  }).join("");
  if (stick) view.scrollTop = view.scrollHeight;
}

async function sendChat(text) {
  text = text.trim();
  if (!text) return;
  const input = $("#chat-input");
  input.value = "";
  grow(input);
  try {
    await api("/api/chat", { text });
  } catch (err) {
    input.value = text;
    toast(err.message);
  }
}

function grow(el) {
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
}

// ---------------------------------------------------------------- the inbox
function sortedPending() {
  return [...S.drafts.values()].filter((d) => PENDING.has(d.status)).sort((x, y) => (x.scheduled_at || "9").localeCompare(y.scheduled_at || "9") || x.id - y.id);
}

function renderBadge() {
  const n = sortedPending().length;
  const badge = $("#badge");
  badge.textContent = n;
  badge.hidden = n === 0;
}

function renderInbox() {
  const host = $("#view-inbox");
  const open = host.querySelector(".card.working")?.dataset.id;
  const items = sortedPending();
  renderBadge();
  if (!items.length) {
    host.innerHTML = `<p class="empty"><b>沒有等你審核的內容</b>新的草稿會出現在這裡，也會跳通知。</p>`;
    return;
  }
  host.innerHTML = items.map(cardHTML).join("");
  if (open) host.querySelector(`.card[data-id="${open}"]`)?.classList.add("working");
}

function cardHTML(d) {
  const review = d.review || {};
  const issues = review.issues || [];
  const future = d.scheduled_at && new Date(d.scheduled_at) > new Date();
  const proposal = d.format === "data_update";
  const approve = proposal ? "核准並開 draft PR" : d.format === "reply" ? "核准並回覆" : future ? `核准，${hhmm(d.scheduled_at)} 發佈` : "核准並發佈";
  const when = d.scheduled_at ? `${mmdd(d.scheduled_at)} ${hhmm(d.scheduled_at)}` : proposal ? "提案" : "回覆";
  return `<article class="card" data-id="${d.id}" id="draft-${d.id}">
    <div class="head"><span class="chip">${esc(CHANNEL[d.channel] || d.channel)}</span><span>${esc(FORMAT[d.format] || d.format)}</span><span class="chip ${d.status}">${esc(STATUS[d.status] || d.status)}</span><span>#${d.id}｜${when}</span></div>
    <h3>${esc(d.title)}</h3>
    ${previewHTML(d)}
    ${issues.length ? `<ul class="issues">${issues.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : ""}
    ${(review.notes || []).length ? `<p class="sub">審稿備註：${esc(review.notes.join("；"))}</p>` : ""}
    <div class="editor"></div>
    <div class="actions">
      <button class="btn primary" data-act="approve" type="button">${approve}</button>
      ${future && !proposal ? '<button class="btn" data-act="now" type="button">立即發佈</button>' : ""}
      ${editableFields(d).length ? '<button class="btn" data-act="edit" type="button">修改文字</button>' : ""}
      <button class="btn" data-act="ask" type="button">請 Leo 改</button>
      <button class="btn danger" data-act="reject" type="button">退回</button>
    </div>
  </article>`;
}

const media = (ref) => `/media/${String(ref).split("/").map(encodeURIComponent).join("/")}`;
const safeLink = (url, text) => (/^https?:\/\//i.test(url || "") ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(text || url)}</a>` : esc(url || "（沒有附）"));
const zoomable = (ref, alt) => `<button type="button" data-zoom="${esc(media(ref))}"><img src="${esc(media(ref))}" alt="${esc(alt)}" loading="lazy" /></button>`;

function previewHTML(d) {
  const p = d.payload || {};
  const m = d.media || {};
  if (d.format === "data_update") {
    // The finding is text a colleague read off a web page: escaped like everything else, and only an http(s) link is clickable.
    const verification = p.verified_by
      ? `<p class="sub"><b>${esc(p.verified_by)} 重新打開官網驗證：需要更新平台</b>\n${esc(p.verdict_reason)}</p>`
      : p.verification_note ? `<p class="sub"><b>⚠️ 沒有完成二次驗證</b>\n${esc(p.verification_note)}</p>` : `<p class="sub">沒有指定驗證員，這份只有巡查同事的說法。</p>`;
    const edits = (p.edits || []).length
      ? p.edits.map((e, i) => `<p class="sub"><b>修改 ${i + 1}：${esc(e.target)}</b>\n目前：${esc(e.current)}\n建議：${esc(e.proposed)}\n依據：${esc(e.basis)}</p>`).join("")
      : p.suggested_update ? `<p class="sub"><b>${esc(p.author)} 的建議</b>\n${esc(p.suggested_update)}</p>` : `<p class="sub">沒有具體的修改清單，請依官方來源確認要改什麼。</p>`;
    return `<p class="post">${esc(p.detail)}</p>${verification}${edits}<p class="sub"><b>官方來源</b>\n${safeLink(p.source_url)}</p>` +
      `<p class="sub">核准後 Pat 會開一個 draft PR（只新增一個提案檔，不改平台資料），合併由你在 GitHub 按。</p>`;
  }
  if (d.format === "reply") {
    return `<p class="sub"><b>@${esc(p.username || "訪客")} 的留言</b>\n${esc(p.comment_text)}</p><p class="post">${esc(p.text)}</p>`;
  }
  if (d.channel === "threads") {
    // A multi-image post (format carousel) has several pictures; a plain post has one card.
    const pictures = m.images && m.images.length ? m.images : m.image ? [m.image] : [];
    const card = pictures.length ? `<div class="thumbs">${pictures.map((r) => zoomable(r, "Threads 配圖")).join("")}</div>` : "";
    return `${card}<p class="post">${esc(p.text)}</p><p class="sub"><b>第一則留言</b>\n${esc(p.first_reply)}</p><p class="sub">主題標籤：${esc(p.topic_tag)}${p.source_url ? `｜${safeLink(p.source_url, "官方來源")}` : ""}</p>`;
  }
  if (d.format === "carousel") {
    const thumbs = (m.images || []).map((r) => zoomable(r, "輪播圖")).join("");
    return `${thumbs ? `<div class="thumbs">${thumbs}</div>` : ""}<p class="sub">${esc(p.caption_full || p.caption)}</p>`;
  }
  if (d.format === "story") return m.image ? `<div class="thumbs">${zoomable(m.image, "限時動態")}</div>` : "";
  const video = m.video ? `<video controls preload="none" playsinline ${m.poster ? `poster="${esc(media(m.poster))}"` : ""} src="${esc(media(m.video))}"></video>` : "";
  if (d.channel === "youtube") return `${video}<p class="sub"><b>${esc(p.title)}</b>\n${esc(p.description)}</p>`;
  return `${video}<p class="sub">${esc(p.caption_full || p.caption)}</p>`;
}

function editableFields(d) {
  if (d.format === "reply") return [["text", "回覆內容"]];
  if (d.channel === "threads") return [["text", "主文"], ["first_reply", "第一則留言"]];
  if (d.channel === "instagram" && d.format !== "story") return [["caption_full", "說明欄"]];
  if (d.channel === "youtube") return [["title", "標題"], ["description", "描述"]];
  return [];
}

async function onCardClick(e) {
  const zoom = e.target.closest("[data-zoom]");
  if (zoom) {
    $("#zoom img").src = zoom.dataset.zoom;
    $("#zoom").hidden = false;
    return;
  }
  const ref = e.target.closest("[data-draft]");
  if (ref) return focusDraft(ref.dataset.draft);
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const card = btn.closest(".card");
  const id = Number(card.dataset.id);
  const d = S.drafts.get(id);
  const editor = $(".editor", card);
  try {
    switch (btn.dataset.act) {
      case "approve":
      case "now": {
        btn.disabled = true;
        const now = btn.dataset.act === "now" || !d.scheduled_at;
        upsert(await api(`/api/drafts/${id}/approve`, { now }));
        toast(d.format === "data_update" ? "已核准，Pat 馬上開 draft PR" : now ? "已核准，馬上發佈" : `已核准，${hhmm(d.scheduled_at)} 發佈`);
        break;
      }
      case "reject":
        card.classList.add("working");
        editor.innerHTML = `<label for="note-${id}">退回原因（可留白）</label><textarea id="note-${id}" rows="3"></textarea>` +
          `<div class="actions"><button class="btn danger" data-act="reject-go" type="button">確認退回</button><button class="btn" data-act="cancel" type="button">取消</button></div>`;
        $("textarea", card).focus();
        break;
      case "reject-go":
        btn.disabled = true;
        upsert(await api(`/api/drafts/${id}/reject`, { note: $("textarea", card).value }));
        toast("已退回");
        break;
      case "edit":
        card.classList.add("working");
        editor.innerHTML = editableFields(d).map(([key, label]) => `<label for="f-${id}-${key}">${label}</label><textarea id="f-${id}-${key}" data-key="${key}">${esc(d.payload[key] || "")}</textarea>`).join("") +
          `<div class="actions"><button class="btn primary" data-act="save" type="button">儲存修改</button><button class="btn" data-act="cancel" type="button">取消</button></div>`;
        $("textarea", card).focus();
        break;
      case "save": {
        const changes = Object.fromEntries([...card.querySelectorAll("textarea[data-key]")].map((t) => [t.dataset.key, t.value]));
        btn.disabled = true;
        card.classList.remove("working");
        upsert(await api(`/api/drafts/${id}`, changes, "PATCH"));
        toast("已儲存修改");
        break;
      }
      case "cancel":
        card.classList.remove("working");
        renderInbox();
        break;
      case "ask": {
        selectTab("chat");
        const input = $("#chat-input");
        input.value = `#${id} `;
        grow(input);
        input.focus();
        break;
      }
    }
  } catch (err) {
    btn.disabled = false;
    toast(err.message);
  }
}

function focusDraft(id) {
  id = Number(id);
  const d = S.drafts.get(id);
  if (!d) return toast(`找不到 #${id}`);
  selectTab(PENDING.has(d.status) ? "inbox" : "sched");
  const card = $(`#view-${PENDING.has(d.status) ? "inbox" : "sched"} #draft-${id}`);
  card?.scrollIntoView({ block: "center" });
  card?.classList.add("flash");
  setTimeout(() => card?.classList.remove("flash"), 1300);
}

// ---------------------------------------------------------------- schedule and log
function renderSched() {
  const host = $("#view-sched");
  const items = [...S.drafts.values()].filter((d) => !PENDING.has(d.status));
  if (!items.length) {
    host.innerHTML = `<p class="empty"><b>還沒有排程</b>核准後的內容會排在這裡，發佈後可以直接點開貼文。</p>`;
    return;
  }
  items.sort((x, y) => (y.scheduled_at || y.updated_at || "").localeCompare(x.scheduled_at || x.updated_at || ""));
  const groups = new Map();
  for (const d of items) groups.set(d.day, [...(groups.get(d.day) || []), d]);
  host.innerHTML = [...groups].map(([day, list]) => `<h4 class="day">${esc(day)}</h4>${list.map((d) => {
    const link = d.remote_url ? `<span class="more">${safeLink(d.remote_url, d.channel === "github" ? "查看 draft PR" : "查看貼文")}</span>` : d.note ? `<span class="more">${esc(d.note)}</span>` : "";
    return `<div class="row-item" id="draft-${d.id}" data-id="${d.id}"><span class="t">${d.scheduled_at ? hhmm(d.scheduled_at) : "--:--"}</span>` +
      `<span class="ttl"><span class="chip">${esc(CHANNEL[d.channel] || d.channel)} ${esc(FORMAT[d.format] || "")}</span> ${esc(d.title)}</span>` +
      `<span class="chip ${d.status}">${esc(STATUS[d.status] || d.status)}</span>${link}${d.error ? `<span class="err">${esc(d.error)}</span>` : ""}</div>`;
  }).join("")}`).join("");
}

function who(id) {
  return id === "boss" ? "辦公室" : S.agents.get(id)?.name || id;
}

function logLine(e) {
  if (e.kind === "draft" || e.kind === "chat") return null;
  const to = e.kind === "handoff" ? ` → ${who(e.to || e.data?.to)}` : "";
  return { ts: e.ts, agent: e.agent, text: `${e.message}${to}` };
}

function renderLog() {
  const lines = S.log.slice(-150).reverse();
  $("#view-log").innerHTML = lines.length
    ? `<ol class="log">${lines.map((l) => `<li><time>${hhmm(l.ts)}</time><span class="who">${esc(who(l.agent))}</span><span>${esc(l.text)}</span></li>`).join("")}</ol>`
    : `<p class="empty"><b>今天還沒有動作</b>同事們開工後，這裡會一行一行出現。</p>`;
}

// ---------------------------------------------------------------- tabs, menu
function selectTab(tab) {
  S.tab = tab;
  document.querySelectorAll(".tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== `view-${tab}`));
  $("#composer").hidden = tab !== "chat";
  if (tab === "chat") {
    $("#unread").hidden = true;
    renderChat(true);
  }
  if (tab === "inbox") renderInbox();
  if (tab === "sched") renderSched();
  if (tab === "log") renderLog();
}

function toggleMenu(open) {
  const menu = $("#menu");
  menu.hidden = !open;
  $("#menu-btn").setAttribute("aria-expanded", String(open));
}

async function onMenu(act) {
  toggleMenu(false);
  try {
    if (act === "reload") return void (await load(), toast("已更新"));
    if (act === "settings") return void window.UniWayApp?.openSettings?.();
    if (act === "publish") {
      await api("/api/publish");
      return toast("已請 Pat 檢查要發的貼文");
    }
    if (act === "run") {
      const ranToday = S.run && S.run.day === S.today;
      if (ranToday && !S.armedRun) {
        S.armedRun = true;
        setTimeout(() => (S.armedRun = false), 6000);
        return toast("今天已經跑過一次了。要再做一份，請在 6 秒內再按一次「開工」");
      }
      S.armedRun = false;
      await api("/api/run", { force: Boolean(ranToday) });
    }
  } catch (err) {
    toast(err.message);
  }
}

// ---------------------------------------------------------------- events
function upsert(d) {
  S.drafts.set(d.id, d);
  renderBadge();
  if (S.tab === "inbox") renderInbox();
  if (S.tab === "sched") renderSched();
}

function apply(e) {
  const line = logLine(e);
  if (line) {
    S.log.push(line);
    if (S.tab === "log") renderLog();
  }
  switch (e.kind) {
    case "status": {
      const a = S.agents.get(e.agent);
      if (a) a.state = e.state;
      if (e.agent === "chief") $("#typing").hidden = e.state !== "thinking";
      break;
    }
    case "chat":
      if (S.chat.some((m) => m.id === e.chat.id)) break;
      S.chat.push(e.chat);
      if (S.tab === "chat") renderChat();
      else if (e.sender === "chief") $("#unread").hidden = false;
      break;
    case "draft":
      upsert(e.draft);
      break;
    case "staff":
      toast(e.message);
      load();
      break;
    case "run":
      if (e.state === "running") {
        S.run = { day: S.today };
        toast("開工了：企劃先排今天的內容");
      } else {
        toast(e.message);
      }
      break;
  }
}

let source;
function connect() {
  source?.close();
  source = new EventSource("/api/events");
  let dropped = false;
  source.onmessage = (msg) => apply(JSON.parse(msg.data));
  source.onerror = () => {
    dropped = true;
    setStatus("重新連線中…", "bad");
  };
  source.onopen = () => {
    setStatus("已連線", "ok");
    if (dropped) load();
    dropped = false;
  };
}

// ---------------------------------------------------------------- loading
function signIn(message) {
  source?.close();
  $("#composer").hidden = true;
  document.querySelector(".tabs").hidden = true;
  $("#main").innerHTML = `<form class="signin" id="signin"><p><b>需要辦公室通行碼</b><br />${esc(message)}</p>` +
    `<label class="sr" for="token">通行碼</label><input id="token" type="password" autocomplete="current-password" placeholder="OFFICE_ACCESS_TOKEN" />` +
    `<button class="btn primary" type="submit">進入辦公室</button></form>`;
  $("#signin").addEventListener("submit", (e) => {
    e.preventDefault();
    location.href = `/m?token=${encodeURIComponent($("#token").value)}`;
  });
}

let loading = null;
function load() {
  loading ||= (async () => {
    try {
      const res = await fetch("/api/state");
      if (res.status === 401 || res.status === 429) {
        const detail = (await res.json().catch(() => ({}))).detail || "";
        signIn(res.status === 429 ? detail : "請輸入 .env 裡的 OFFICE_ACCESS_TOKEN。");
        return false;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const state = await res.json();
      S.tz = state.timezone || S.tz;
      S.today = state.today;
      S.run = state.run;
      S.agents = new Map(state.agents.map((a) => [a.id, a]));
      S.drafts = new Map(state.drafts.map((d) => [d.id, d]));
      S.log = state.events.map(logLine).filter(Boolean);
      S.chat = state.chat || [];
      const mode = state.settings.dry_run ? "模擬發佈" : "正式發佈";
      setStatus(source?.readyState === 1 ? `已連線｜${mode}` : "連線中…", source?.readyState === 1 ? "ok" : "");
      selectTab(S.tab);
      renderBadge();
      if (!source) connect();
      openHash();
      return true;
    } catch (err) {
      setStatus("連不上辦公室，稍後重試…", "bad");
      setTimeout(load, 8000);
      return false;
    } finally {
      loading = null;
    }
  })();
  return loading;
}

// A notification opens /m#draft-12.
function openHash() {
  const m = /^#draft-(\d+)$/.exec(location.hash);
  if (!m) return;
  history.replaceState(null, "", location.pathname);
  focusDraft(m[1]);
}

document.addEventListener("DOMContentLoaded", async () => {
  if (window.UniWayApp?.openSettings) $("#menu-settings").hidden = false;
  document.querySelector(".tabs").addEventListener("click", (e) => e.target.closest("button[data-tab]") && selectTab(e.target.closest("button[data-tab]").dataset.tab));
  $("#view-inbox").addEventListener("click", onCardClick);
  $("#view-sched").addEventListener("click", onCardClick);
  $("#chat").addEventListener("click", (e) => e.target.closest("[data-draft]") && focusDraft(e.target.closest("[data-draft]").dataset.draft));
  $("#composer").addEventListener("submit", (e) => (e.preventDefault(), sendChat($("#chat-input").value)));
  $("#chat-input").addEventListener("input", (e) => grow(e.target));
  $("#chips").addEventListener("click", (e) => e.target.closest("button") && sendChat(e.target.textContent));
  $("#menu-btn").addEventListener("click", (e) => (e.stopPropagation(), toggleMenu($("#menu").hidden)));
  $("#menu").addEventListener("click", (e) => e.target.closest("button[data-do]") && onMenu(e.target.closest("button[data-do]").dataset.do));
  document.addEventListener("click", (e) => !e.target.closest("#menu, #menu-btn") && toggleMenu(false));
  $("#zoom").addEventListener("click", () => ($("#zoom").hidden = true));
  addEventListener("hashchange", openHash);
  document.addEventListener("visibilitychange", () => document.visibilityState === "visible" && load());
  load();
});

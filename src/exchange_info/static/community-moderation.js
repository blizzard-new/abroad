/* Moderator tools use the same authenticated transport as the student Web. */
(() => {
  "use strict";
  let api;
  let owner = "";
  let version = 0;
  let allowed = false;
  let checking = false;
  let readerWasOpen = false;
  const $ = (selector) => document.querySelector(selector);
  const esc = (value) => api.escape(String(value ?? ""));
  const statusLabel = (value) => ({pending:"待審核",approved:"已公開",hidden:"已隱藏",resolved:"已處理",dismissed:"已駁回",active:"可發言",suspended:"暫停發言"}[value] || value);
  const typeLabel = (value) => ({post:"文章",comment:"留言",report:"檢舉",identity:"發言資格",chat:"公開聊天",message:"私訊"}[value] || value);
  const pending = new Map();
  async function sync() {
    const currentOwner = api.accountId();
    if (currentOwner !== owner) {
      owner = currentOwner; ++version; allowed = false; checking = false;
      $("#discussion-moderation-open").hidden = true;
      $("#discussion-moderation").close();
      $("#discussion-moderation-body").replaceChildren();
      pending.clear();
    }
    if (!owner || allowed || checking) return;
    checking = true;
    const stamp = version;
    try {
      await api.fetch("/admin/community/session");
      if (stamp === version) { allowed = true; $("#discussion-moderation-open").hidden = false; }
    } catch (_) { /* Regular students have no moderation controls. */ }
    finally { if (stamp === version) checking = false; }
  }
  async function load() {
    if (!allowed) return;
    const stamp = ++version;
    const body = $("#discussion-moderation-body");
    body.textContent = "正在載入內容與處理紀錄…";
    try {
      const [content, reports, audits] = await Promise.all([
        api.fetch(`/admin/community/content?status=${$("#discussion-moderation-filter").value}`),
        api.fetch("/admin/community/reports"), api.fetch("/admin/community/moderation-audits")]);
      if (stamp !== version) return;
      const reason = '<label>處理原因<input name="note" minlength="2" maxlength="500" required placeholder="請記下查核結果或違規原因" /></label>';
      body.innerHTML = `<section><h3>討論內容（最近 100 筆）</h3>${content.items.map((row) => `<article class="discussion-moderation-card"><strong>${esc(row.title || "文章留言")}</strong><small>${esc(row.school_name || "")} · ${esc(row.display_name)} · ${esc(statusLabel(row.status))}</small><p>${esc(row.body)}</p><form data-moderate-type="${esc(row.resource_type)}" data-moderate-id="${esc(row.id)}" data-expected-status="${esc(row.status)}">${reason}<div class="discussion-actions">${row.status !== "approved" ? '<button type="submit" name="action" value="approved" class="secondary-button">核准公開</button>' : ""}${row.status !== "hidden" ? '<button type="submit" name="action" value="hidden" class="secondary-button">隱藏內容</button>' : ""}</div><p class="form-status" role="status"></p></form>${row.author_id ? `<details><summary>限制此帳號發言</summary><form data-suspend-identity="${esc(row.author_id)}"><label>停權時間<select name="days"><option value="1">1 天</option><option value="7">7 天</option><option value="30">30 天</option></select></label>${reason}<button type="submit" class="secondary-button">確認停權</button><p class="form-status" role="status"></p></form></details>` : ""}</article>`).join("") || "<p>此狀態沒有內容。</p>"}</section>
      <section><h3>待處理檢舉（最近 100 筆）</h3>${reports.map((row) => `<article class="discussion-moderation-card"><p>${esc(row.reason)}</p><small>${esc(typeLabel(row.resource_type))} · ${esc(row.resource_id)}</small>${row.content ? `<details><summary>檢視被檢舉內容</summary><strong>${esc(row.content.title || "文章留言")}</strong><p>${esc(row.content.body)}</p></details>${row.content.status !== "hidden" ? `<form data-moderate-type="${esc(row.resource_type)}" data-moderate-id="${esc(row.resource_id)}" data-expected-status="${esc(row.content.status)}">${reason}<button type="submit" name="action" value="hidden" class="secondary-button">隱藏被檢舉內容</button><p class="form-status" role="status"></p></form>` : ""}` : "<p>原文已移除，或屬於其他管理流程的內容。</p>"}<form data-review-report="${esc(row.id)}">${reason}<div class="discussion-actions"><button type="submit" name="action" value="resolved" class="secondary-button">標記已處理</button><button type="submit" name="action" value="dismissed" class="secondary-button">駁回檢舉</button></div><p class="form-status" role="status"></p></form><p class="discussion-source-note">處理檢舉不會自動隱藏內容；請先核對原文，必要時使用上方的隱藏操作。</p></article>`).join("") || "<p>沒有待處理檢舉。</p>"}</section>
      <section><h3>最近 100 筆處理紀錄</h3><ol class="discussion-audits">${audits.map((row) => `<li><strong>${esc(statusLabel(row.previous_status))} → ${esc(statusLabel(row.new_status))}</strong><p>${esc(row.note)}</p><small>${esc(row.created_at)} · ${esc(typeLabel(row.resource_type))} · ${esc(row.resource_id)}</small></li>`).join("") || "<li>尚無處理紀錄。</li>"}</ol></section>`;
    } catch (error) {
      if (stamp !== version) return;
      body.innerHTML = `<p role="alert">${esc(error.message)}</p><button type="button" data-moderation-retry class="secondary-button">重新載入工作台</button>`;
    }
  }
  async function submit(event) {
    const form = event.target.closest("form");
    if (!form) return;
    event.preventDefault();
    const values = new FormData(form);
    const note = String(values.get("note") || "").trim();
    const status = form.querySelector(".form-status");
    if (note.length < 2) { status.textContent = "請填寫至少兩個字的處理原因。"; return; }
    let url, method, payload;
    if (form.dataset.suspendIdentity) {
      url = `/admin/community/identities/${encodeURIComponent(form.dataset.suspendIdentity)}/suspend`;
      method = "POST";
      const key = `${owner}:${url}:${values.get("days")}:${note}`;
      // Keep the exact future timestamp and receipt key across ambiguous retries.
      let command = pending.get(key);
      if (!command) { command = { id: crypto.randomUUID(), until: new Date(Date.now() + Number(values.get("days")) * 86400000).toISOString() }; pending.set(key, command); }
      payload = { suspended_until: command.until, reason: note };
    } else if (form.dataset.reviewReport) {
      url = `/admin/community/reports/${encodeURIComponent(form.dataset.reviewReport)}`;
      method = "PATCH"; payload = { status: event.submitter.value, note };
    } else {
      url = `/admin/community/${form.dataset.moderateType}/${encodeURIComponent(form.dataset.moderateId)}`;
      method = "PATCH"; payload = { status: event.submitter.value, expected_status: form.dataset.expectedStatus, note };
    }
    const key = `${owner}:${url}:${JSON.stringify(payload)}`;
    const command = pending.get(key) || { id: crypto.randomUUID() };
    pending.set(key, command);
    const stamp = version;
    form.querySelectorAll("button").forEach((button) => { button.disabled = true; });
    status.textContent = "正在儲存操作與稽核紀錄…";
    try {
      await api.fetch(url, { method, headers: { "Content-Type": "application/json", "X-Community-Mutation-ID": command.id }, body: JSON.stringify(payload) });
      pending.delete(key);
      if (stamp !== version) return;
      api.announce("操作已儲存，並保留處理紀錄。", "success");
      api.refreshed(); await load();
    } catch (error) {
      if (error.status && error.status < 500) pending.delete(key);
      if (stamp === version) status.textContent = error.message;
    } finally { if (form.isConnected) form.querySelectorAll("button").forEach((button) => { button.disabled = false; }); }
  }
  function init(adapters) {
    api = adapters;
    $("#discussion-moderation-open").addEventListener("click", async () => {
      readerWasOpen = $("#discussion-reader").open;
      if (readerWasOpen) $("#discussion-reader").close();
      $("#discussion-moderation").showModal(); await load();
    });
    const close = () => { $("#discussion-moderation").close(); if (readerWasOpen) window.UniWayCommunity.syncDetail(); };
    $("#discussion-moderation-close").addEventListener("click", close);
    $("#discussion-moderation").addEventListener("cancel", (event) => { event.preventDefault(); close(); });
    $("#discussion-moderation-filter").addEventListener("change", load);
    $("#discussion-moderation").addEventListener("submit", submit);
    $("#discussion-moderation").addEventListener("click", (event) => { if (event.target.closest("[data-moderation-retry]")) load(); });
  }
  window.UniWayModeration = { init, sync };
})();

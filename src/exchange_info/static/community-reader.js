/* UniWay discussion browsing. Shares the application's transport and account gates. */
(() => {
  "use strict";
  let api;
  let feedVersion = 0;
  let detailVersion = 0;
  let current = null;
  let detail = null;
  let detailId = "";
  let detailPermissionKey = "";
  let comments = [];
  let commentCursor = null;
  let commentSort = "oldest";
  let commentLoading = false;
  let openedHere = false;
  let returnFocus = null;
  let feedController;
  let draftOwner = "";
  let observer;
  let replyTarget = "";
  let threads = new Map();
  let cloudOwner = "";
  let cloudSaved = null;
  let bookmarkVersion = 0;
  const bookmarkBusy = new Set();
  const cache = new Map();
  const $ = (selector) => document.querySelector(selector);
  const escape = (value) => api.escape(String(value ?? ""));
  const storageKey = (kind) => `uniway-discussion-${kind}:${api.context().accountId || "guest"}`;

  function saved() {
    if (api.context().accountId) return cloudOwner === api.context().accountId ? new Set(cloudSaved || []) : new Set();
    try {
      const ids = JSON.parse(localStorage.getItem(storageKey("saved")) || "[]");
      return new Set(Array.isArray(ids) ? ids.filter((id) => typeof id === "string").slice(0, 100) : []);
    } catch (_) { return new Set(); }
  }
  async function syncBookmarks(context) {
    if (cloudOwner !== context.accountId) { cloudOwner = context.accountId; cloudSaved = null; ++bookmarkVersion; bookmarkBusy.clear(); }
    $("#discussion-bookmark-status").textContent = context.accountId ? "收藏同步到登入帳號" : "收藏保存在此瀏覽器";
    let legacy = [];
    try { legacy = JSON.parse(localStorage.getItem(storageKey("saved")) || "[]"); } catch (_) {}
    $("#discussion-import-saved").hidden = !context.accountId || !Array.isArray(legacy) || !legacy.length;
    if (!context.accountId) return true;
    const stamp = bookmarkVersion;
    try {
      const result = await api.fetch("/community/bookmarks");
      if (context.accountId !== api.context().accountId) return false;
      if (stamp !== bookmarkVersion) return cloudSaved !== null;
      cloudSaved = new Set(result.ids);
      patchBookmarks();
      return true;
    } catch (error) {
      if (context.accountId === api.context().accountId) $("#discussion-bookmark-status").textContent = "帳號收藏暫時無法同步；請重新整理後重試";
      return false;
    }
  }
  function patchBookmarks() {
    const ids = saved();
    document.querySelectorAll("[data-discussion-save]").forEach((button) => {
      const active = ids.has(button.dataset.discussionSave);
      button.setAttribute("aria-pressed", String(active));
      button.querySelector("span").textContent = active ? "已收藏" : "收藏";
      button.disabled = Boolean(api.context().accountId && cloudSaved === null);
    });
  }
  function filters() {
    const params = new URLSearchParams(location.search);
    const sort = params.get("discussion_sort") || "latest";
    return { q: (params.get("discussion_q") || "").slice(0, 80),
      topic: params.get("discussion_topic") || "",
      sort: ["latest", "oldest", "unanswered"].includes(sort) ? sort : "latest",
      saved: params.get("discussion_saved") === "1" };
  }
  function updateFilters(values) {
    const url = new URL(location.href);
    for (const [key, value] of Object.entries(values)) {
      const param = "discussion_" + key;
      if (value) url.searchParams.set(param, value);
      else url.searchParams.delete(param);
    }
    window.UniWayNavigation.replaceState(history.state, "", url);
    load();
  }
  function meta(post) {
    return [api.topicLabel(post.topic), post.country, post.academic_year,
      api.stageLabel(post.application_stage)].filter(Boolean);
  }
  function bookmarkButton(post) {
    const active = saved().has(post.id);
    return `<button type="button" class="text-action discussion-save" data-discussion-save="${escape(post.id)}" ${api.context().accountId && cloudSaved === null ? "disabled" : ""} aria-pressed="${active}" aria-label="${active ? "取消收藏" : "收藏文章"}：${escape(post.title)}"><i data-lucide="bookmark" aria-hidden="true"></i><span>${active ? "已收藏" : "收藏"}</span></button>`;
  }
  function card(post) {
    const url = new URL(location.href);
    url.searchParams.set("discussion", post.id);
    return `<article class="community-post-card discussion-summary">
      <div class="discussion-card-byline"><span class="discussion-board-label"><i data-lucide="messages-square" aria-hidden="true"></i>${escape(post.school_name)}</span><time datetime="${escape(post.created_at)}">${escape(api.date(post.created_at))}</time></div>
      <h3><a href="${escape(url.pathname + url.search + url.hash)}" data-discussion-open="${escape(post.id)}">${escape(post.title)}</a></h3>
      <p class="discussion-excerpt">${escape(post.excerpt)}</p>
      <div class="discussion-context">${meta(post).map((label) => `<span>${escape(label)}</span>`).join("")}</div>
      <div class="discussion-card-footer"><span class="discussion-card-author"><i data-lucide="user-round" aria-hidden="true"></i>${escape(post.display_name)}</span><div><a class="text-action" href="${escape(url.pathname + url.search + url.hash)}" data-discussion-open="${escape(post.id)}"><i data-lucide="message-circle" aria-hidden="true"></i><span>${post.comment_count} 則回覆</span></a>${bookmarkButton(post)}</div></div>
    </article>`;
  }
  function message(title, text, retry = false) {
    return `<div class="discussion-message" role="status"><strong>${escape(title)}</strong><p>${escape(text)}</p>${retry ? '<button type="button" class="secondary-button" data-discussion-retry>重新載入</button>' : ""}</div>`;
  }
  function renderFeed() {
    const feed = $("#global-community-feed");
    if (!feed || !current) return;
    feed.innerHTML = current.items.map(card).join("") || api.empty(current.filters, api.context());
    $("#discussion-feed-status").textContent = current.items.length ? `已載入 ${current.items.length} 篇文章` : "";
    const more = $("#discussion-feed-more");
    delete more.dataset.reset;
    more.hidden = !current.cursor;
    more.disabled = false;
    more.textContent = "載入更多文章";
    api.icons();
    observer?.disconnect();
    if (current.cursor && observer) observer.observe(more);
  }
  async function load({ force = false } = {}) {
    if (!api) return;
    const context = api.context();
    if (draftOwner !== context.accountId) {
      const form = $("#global-community-form");
      form.reset();
      form.hidden = true;
      draftOwner = context.accountId;
    }
    const selected = filters();
    const version = ++feedVersion;
    api.syncFilters(selected);
    $("#discussion-sort").value = selected.sort;
    $("#discussion-saved-filter").setAttribute("aria-pressed", String(selected.saved));
    const bookmarksReady = await syncBookmarks(context);
    if (version !== feedVersion || context.accountId !== api.context().accountId) return;
    const params = new URLSearchParams({ limit: "20", sort: selected.sort });
    if (selected.q) params.set("q", selected.q);
    if (selected.topic) params.set("topic", selected.topic);
    if (context.boards.length) params.set("boards", context.boards.join(","));
    if (selected.saved) params.set("ids", [...saved()].join(","));
    const key = `${context.key}:${params}`;
    feedController?.abort();
    observer?.disconnect();
    current = null;
    $("#discussion-feed-more").hidden = true;
    $("#discussion-feed-status").textContent = "";
    syncDetail();
    window.UniWayModeration?.sync();
    if (selected.saved && context.accountId && !bookmarksReady) {
      $("#global-community-feed").setAttribute("aria-busy", "false");
      $("#global-community-feed").innerHTML = message("帳號收藏暫時無法載入", "請保留目前內容，稍後重新載入收藏。", true);
      return;
    }
    if (!force && cache.has(key)) {
      current = cache.get(key);
      $("#global-community-feed").setAttribute("aria-busy", "false");
      renderFeed();
      return;
    }
    current = { key, params, items: [], cursor: null, filters: selected };
    if (context.emptyFollowing || (selected.saved && !saved().size)) {
      $("#global-community-feed").setAttribute("aria-busy", "false");
      renderFeed();
      return;
    }
    const feed = $("#global-community-feed");
    feed.setAttribute("aria-busy", "true");
    feed.innerHTML = '<div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div>';
    feedController = new AbortController();
    try {
      const result = await api.fetch(`/community/feed?${params}`, { signal: feedController.signal });
      if (version !== feedVersion) return;
      current.items = result.items;
      current.cursor = result.next_cursor;
      cache.set(key, current);
      if (cache.size > 12) cache.delete(cache.keys().next().value);
      renderFeed();
    } catch (error) {
      if (version !== feedVersion || error.name === "AbortError") return;
      feed.innerHTML = message("文章暫時無法載入", error.message, true);
    } finally {
      if (version === feedVersion) feed.setAttribute("aria-busy", "false");
    }
  }
  async function moreFeed() {
    if ($("#discussion-feed-more").dataset.reset) { await load({ force: true }); return; }
    if (!current?.cursor || $("#discussion-feed-more").disabled) return;
    const target = current;
    const version = feedVersion;
    const button = $("#discussion-feed-more");
    button.disabled = true;
    button.textContent = "載入中…";
    observer?.disconnect();
    try {
      const params = new URLSearchParams(target.params);
      params.set("cursor", target.cursor);
      const result = await api.fetch(`/community/feed?${params}`);
      if (version !== feedVersion || current !== target) return;
      const seen = new Set(target.items.map((row) => row.id));
      target.items.push(...result.items.filter((row) => !seen.has(row.id)));
      target.cursor = result.next_cursor;
      renderFeed();
    } catch (error) {
      if (version !== feedVersion) return;
      button.disabled = false;
      button.textContent = error.status === 422 ? "分頁已失效，重新載入列表" : "載入失敗，點此重試";
      if (error.status === 422) button.dataset.reset = "1";
      $("#discussion-feed-status").textContent = error.message;
    }
  }
  function openPost(id, trigger) {
    api.beforeOpen();
    const typedQuery = $("#global-community-search").value.trim();
    if (typedQuery !== filters().q) updateFilters({ q: typedQuery });
    returnFocus = trigger;
    openedHere = true;
    const url = new URL(location.href);
    url.searchParams.set("discussion", id);
    window.UniWayNavigation.pushState(history.state, "", url);
    syncDetail();
  }
  function closePost() {
    if (openedHere) {
      openedHere = false;
      window.UniWayNavigation.back();
    } else {
      const url = new URL(location.href);
      url.searchParams.delete("discussion");
      window.UniWayNavigation.replaceState(history.state, "", url);
      syncDetail();
    }
  }
  function syncDetail() {
    const id = api.context().active ? new URLSearchParams(location.search).get("discussion") || "" : "";
    const dialog = $("#discussion-reader");
    if (!id) {
      ++detailVersion;
      detailId = "";
      detail = null;
      if (dialog.open) dialog.close();
      if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
      else if (returnFocus) $("#community-hub-title").focus({ preventScroll: true });
      returnFocus = null;
      return;
    }
    // Account dialogs use the existing app surface; avoid covering them with
    // a native top-layer dialog while authentication requests are settling.
    if (!$("#auth-dialog").hidden || !$("#profile-dialog").hidden || $("#discussion-moderation").open) return;
    const permissionKey = api.context().permissionKey;
    if (id === detailId && permissionKey === detailPermissionKey && dialog.open) return;
    detailPermissionKey = permissionKey;
    detailId = id;
    comments = [];
    threads = new Map();
    replyTarget = "";
    commentCursor = null;
    commentLoading = false;
    commentSort = "oldest";
    detail = null;
    const version = ++detailVersion;
    $("#discussion-reader-body").innerHTML = message("正在載入文章", "稍後會顯示內容與回覆。");
    if (!dialog.open) dialog.showModal();
    api.fetch(`/community/posts/${encodeURIComponent(id)}`).then((post) => {
      if (version !== detailVersion) return;
      detail = post;
      renderDetail();
      loadComments();
    }).catch((error) => {
      if (version !== detailVersion) return;
      $("#discussion-reader-body").innerHTML = message("無法開啟文章", error.message) + '<button type="button" class="secondary-button" data-discussion-detail-retry>重新載入文章</button>';
    });
  }
  function renderDetail() {
    const post = detail;
    $("#discussion-reader-body").innerHTML = `<article class="discussion-article">
      <div class="discussion-card-byline"><span>${escape(post.school_name)} · ${escape(post.display_name)}</span><time datetime="${escape(post.created_at)}">${escape(api.date(post.created_at))}</time></div>
      <h2 id="discussion-article-title">${escape(post.title)}</h2>
      <div class="discussion-context">${meta(post).map((label) => `<span>${escape(label)}</span>`).join("")}</div>
      <p class="discussion-body">${escape(post.body)}</p>
      <p class="discussion-source-note">同學的經驗分享；申請資格與截止日期請再對照官方公告。</p>
      <div class="discussion-actions">${reactions(post, "post")}${bookmarkButton(post)}<button type="button" class="text-action" data-discussion-share><i data-lucide="share-2" aria-hidden="true"></i><span>分享連結</span></button><button type="button" class="text-action" data-report-resource="post" data-resource-id="${escape(post.id)}"><i data-lucide="flag" aria-hidden="true"></i><span>檢舉</span></button>${removeButton(post, "post")}</div>
      <section class="discussion-replies" aria-labelledby="discussion-replies-title"><div class="discussion-reply-heading"><h3 id="discussion-replies-title">${post.comment_count} 則回覆</h3><label>留言排序<select id="discussion-comment-sort"><option value="oldest">由舊到新</option><option value="latest">由新到舊</option></select></label></div><div id="discussion-comments" aria-live="polite"></div><button type="button" class="secondary-button" id="discussion-comments-more" hidden>載入更多回覆</button></section>
      ${api.composer(post)}
    </article>`;
    restoreDraft($("#discussion-reader-body .post-comment-form"), `reply:${post.id}`);
    $("#discussion-comment-sort").addEventListener("change", (event) => {
      commentSort = event.target.value;
      ++detailVersion;
      commentLoading = false;
      comments = [];
      threads.clear();
      commentCursor = null;
      loadComments();
    });
    $("#discussion-comments-more").addEventListener("click", () => loadComments(true));
    api.icons();
  }
  function renderComments() {
    $("#discussion-comments").innerHTML = comments.map((row) => commentCard(row, false)).join("") || message("還沒有回覆", "分享你的實際年份與經驗，幫下一位同學少走一點彎路。");
    const button = $("#discussion-comments-more");
    button.hidden = !commentCursor;
    button.disabled = false;
    button.textContent = "載入更多回覆";
  }
  function reactions(row, type) {
    if (row.deleted) return "";
    const value = row.reactions || { counts: {}, viewer_reaction: null };
    return `<span class="discussion-reactions" data-reactions="${escape(type)}:${escape(row.id)}">${[["helpful", "有幫助"], ["thanks", "感謝"]].map(([key, label]) => `<button type="button" class="text-action" data-discussion-react="${key}" data-resource-type="${type}" data-resource-id="${escape(row.id)}" aria-pressed="${value.viewer_reaction === key}">${label} <span>${value.counts[key] || 0}</span></button>`).join("")}</span>`;
  }
  function removeButton(row, type) {
    return row.viewer_can_delete && !row.deleted ? `<button type="button" class="text-action" data-discussion-delete="${type}" data-resource-id="${escape(row.id)}">刪除${type === "post" ? "文章" : "留言"}</button>` : "";
  }
  function commentCard(row, child) {
    const floor = child ? `${row.parent_floor}-${row.floor}` : row.floor;
    const root = row.parent_id || row.id;
    const thread = threads.get(root);
    return `<article class="discussion-comment ${child ? "discussion-child" : ""}" id="discussion-comment-${escape(row.id)}"><div><strong>${escape(row.display_name)}</strong><span>B${floor} · ${escape(api.date(row.created_at))}</span></div><p>${escape(row.body)}</p><div class="discussion-actions">${reactions(row, "comment")}${!row.deleted ? `<button type="button" class="text-action" data-discussion-quote="${escape(row.id)}">引用回覆</button>` : ""}<button type="button" class="text-action" data-discussion-reply="${escape(root)}">回覆此串</button>${removeButton(row, "comment")}${!row.deleted ? `<button type="button" class="text-action" data-report-resource="comment" data-resource-id="${escape(row.id)}">檢舉</button>` : ""}</div>${!child && row.reply_count ? `<button type="button" class="text-action" data-discussion-thread="${escape(root)}" aria-expanded="${Boolean(thread?.open)}">${thread?.open ? "收起" : "查看"} ${row.reply_count} 則串內回覆</button>` : ""}${!child && thread?.open ? `<div class="discussion-thread">${thread.items.map((item) => commentCard(item, true)).join("")}${thread.loading ? message("正在載入串內回覆", "稍後顯示這一串的對話。") : ""}${thread.error ? message("串內回覆載入失敗", thread.error) : ""}${thread.cursor || thread.error ? `<button type="button" class="secondary-button" data-discussion-thread-more="${escape(root)}">${thread.error ? "重試串內回覆" : "載入更多串內回覆"}</button>` : ""}</div>` : ""}</article>`;
  }
  function findComment(id) {
    return comments.find((row) => row.id === id) || [...threads.values()].flatMap((thread) => thread.items).find((row) => row.id === id);
  }
  async function loadThread(root, more = false) {
    let thread = threads.get(root);
    if (!thread) { thread = { items: [], cursor: null, open: true }; threads.set(root, thread); }
    if (thread.loading) return;
    if (!more && thread.items.length) { thread.open = !thread.open; renderComments(); return; }
    thread.open = true; thread.loading = true; thread.error = "";
    const version = detailVersion;
    renderComments();
    const params = new URLSearchParams({ parent_id: root, sort: "oldest", limit: "20" });
    if (more && thread.cursor) params.set("cursor", thread.cursor);
    try {
      const result = await api.fetch(`/community/posts/${encodeURIComponent(detailId)}/comments?${params}`);
      if (version !== detailVersion) return;
      const seen = new Set(thread.items.map((row) => row.id));
      thread.items.push(...result.items.filter((row) => !seen.has(row.id)));
      thread.cursor = result.next_cursor;
    } catch (error) { if (version === detailVersion) thread.error = error.message; }
    finally { if (version === detailVersion) { thread.loading = false; renderComments(); } }
  }
  function replyDraftKind() { return `reply:${detailId}${replyTarget ? ":" + replyTarget : ""}`; }
  function setReplyTarget(root) {
    const form = $("#discussion-reader .post-comment-form");
    if (!form) { $("#discussion-reader").close(); api.commentGate(detail); return; }
    saveDraft(form, replyDraftKind());
    replyTarget = root;
    form.elements.body.value = "";
    form.elements.parent_id.value = root;
    restoreDraft(form, replyDraftKind());
    form.elements.parent_id.value = root;
    const target = form.querySelector("[data-discussion-reply-target]");
    target.hidden = !root;
    target.querySelector("span").textContent = root ? `正在回覆 B${comments.find((row) => row.id === root)?.floor || ""} 這一串` : "";
    form.elements.body.focus();
  }
  async function react(button) {
    if (!api.context().accountId) { $("#discussion-reader").close(); api.commentGate(detail); return; }
    const version = detailVersion;
    const row = button.dataset.resourceType === "post" ? detail : findComment(button.dataset.resourceId);
    const group = button.closest("[data-reactions]");
    if (!row || group.dataset.busy) return;
    group.dataset.busy = "1";
    group.querySelectorAll("button").forEach((item) => { item.disabled = true; });
    const next = row.reactions?.viewer_reaction === button.dataset.discussionReact ? null : button.dataset.discussionReact;
    try {
      const result = await api.fetch(`/community/${button.dataset.resourceType}/${encodeURIComponent(row.id)}/reaction`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reaction: next }) });
      if (version !== detailVersion) return;
      row.reactions = result;
      group.outerHTML = reactions(row, button.dataset.resourceType);
    } catch (error) { if (version === detailVersion) api.announce(error.message, "error"); }
    finally { if (group.isConnected) { delete group.dataset.busy; group.querySelectorAll("button").forEach((item) => { item.disabled = false; }); } }
  }
  async function remove(button) {
    const type = button.dataset.discussionDelete;
    const version = detailVersion;
    const url = `/community/posts/${encodeURIComponent(detailId)}` + (type === "comment" ? `/comments/${encodeURIComponent(button.dataset.resourceId)}` : "");
    button.disabled = true;
    if (await api.deleteResource(url, type === "post" ? "刪除文章也會移除全部留言，確定刪除？" : "確定刪除自己的留言？若已有回覆，會留下刪除標示與後續對話。")) {
      cache.clear();
      if (version !== detailVersion) return;
      if (type === "post") { closePost(); load({ force: true }); }
      else { threads.clear(); await loadComments(); }
    }
    if (button.isConnected) button.disabled = false;
  }
  async function loadComments(more = false) {
    if (!detail || commentLoading) return;
    commentLoading = true;
    const version = detailVersion;
    const params = new URLSearchParams({ sort: commentSort, limit: "20" });
    if (more && commentCursor) params.set("cursor", commentCursor);
    if (!more) $("#discussion-comments").innerHTML = message("正在載入回覆", "文章可以先閱讀。");
    $("#discussion-comments-more").disabled = true;
    try {
      const result = await api.fetch(`/community/posts/${encodeURIComponent(detailId)}/comments?${params}`);
      if (version !== detailVersion) return;
      const seen = new Set(comments.map((row) => row.id));
      comments = more ? [...comments, ...result.items.filter((row) => !seen.has(row.id))] : result.items;
      commentCursor = result.next_cursor;
      detail.comment_count = result.discussion_total;
      $("#discussion-replies-title").textContent = `${result.discussion_total} 則回覆`;
      renderComments();
    } catch (error) {
      if (version !== detailVersion) return;
      if (!more) $("#discussion-comments").innerHTML = message("回覆暫時無法載入", error.message) + '<button type="button" class="secondary-button" data-discussion-comments-retry>重試回覆</button>';
      else {
        $("#discussion-comments-more").disabled = false;
        $("#discussion-comments-more").textContent = "載入失敗，點此重試";
      }
    } finally { if (version === detailVersion) commentLoading = false; }
  }
  function draftKey(kind) { return storageKey("draft") + ":" + kind; }
  function saveDraft(form, kind) {
    if (!form || !api.context().accountId) return;
    const payload = Object.fromEntries(new FormData(form));
    try {
      sessionStorage.setItem(draftKey(kind), JSON.stringify(payload));
      form.querySelector("[data-discussion-draft-status]")?.replaceChildren(document.createTextNode("草稿已保存在此分頁"));
    } catch (_) {
      form.querySelector("[data-discussion-draft-status]")?.replaceChildren(document.createTextNode("無法保存草稿，關閉前請自行複製內容"));
    }
  }
  function restoreDraft(form, kind) {
    if (!form || !api.context().accountId) return;
    try {
      const payload = JSON.parse(sessionStorage.getItem(draftKey(kind)) || "null");
      if (!payload || typeof payload !== "object") return;
      for (const [name, value] of Object.entries(payload)) {
        const input = form.elements.namedItem(name);
        if (input && typeof value === "string" && !input.disabled
            && (!input.options || [...input.options].some((option) => option.value === value && !option.disabled))) input.value = value;
      }
      form.querySelector("[data-discussion-draft-status]")?.replaceChildren(document.createTextNode("已接續此分頁的草稿"));
    } catch (_) { /* Malformed or unavailable storage never blocks writing. */ }
  }
  function clearDraft(kind) { try { sessionStorage.removeItem(draftKey(kind)); } catch (_) {} }
  async function toggleSave(id) {
    const owner = api.context().accountId;
    if (bookmarkBusy.has(id)) return;
    const ids = saved();
    if (ids.has(id)) ids.delete(id);
    else if (ids.size >= 100) { api.announce(`${owner ? "帳號" : "此瀏覽器"}最多收藏 100 篇，請先移除一些文章。`, "error"); return; }
    else ids.add(id);
    try {
      if (owner) {
        if (cloudSaved === null) { api.announce("帳號收藏尚未載入，請稍後重試。", "error"); return; }
        bookmarkBusy.add(id);
        await api.fetch(`/community/posts/${encodeURIComponent(id)}/bookmark`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ saved: ids.has(id) }) });
        if (owner !== api.context().accountId) return;
        if (ids.has(id)) cloudSaved.add(id); else cloudSaved.delete(id);
        ++bookmarkVersion;
      } else localStorage.setItem(storageKey("saved"), JSON.stringify([...ids]));
    }
    catch (error) { api.announce(owner ? `收藏暫時無法儲存：${error.message}` : "無法保存收藏，請檢查瀏覽器儲存設定。", "error"); return; }
    finally { bookmarkBusy.delete(id); }
    for (const [key, entry] of cache) if (entry.filters.saved) cache.delete(key);
    // Patch only bookmark controls; preserve an in-progress reply and its caret.
    document.querySelectorAll("[data-discussion-save]").forEach((button) => {
      if (button.dataset.discussionSave !== id) return;
      const active = ids.has(id);
      button.setAttribute("aria-pressed", String(active));
      button.querySelector("span").textContent = active ? "已收藏" : "收藏";
      button.setAttribute("aria-label", active ? "取消收藏文章" : "收藏文章");
    });
    if (filters().saved) await load({ force: true });
    api.announce(ids.has(id) ? (owner ? "已收藏到登入帳號" : "已收藏在此瀏覽器") : "已移除收藏", "success");
  }
  async function importSaved() {
    const owner = api.context().accountId;
    if (!owner || cloudSaved === null) return;
    const key = storageKey("saved");
    let remaining;
    try { remaining = JSON.parse(localStorage.getItem(key) || "[]"); } catch (_) { return; }
    if (!Array.isArray(remaining)) return;
    const button = $("#discussion-import-saved");
    button.disabled = true;
    try {
      for (const id of [...remaining].slice(0, 100)) {
        if (owner !== api.context().accountId) return;
        await api.fetch(`/community/posts/${encodeURIComponent(id)}/bookmark`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ saved: true }) });
        if (owner !== api.context().accountId) return;
        cloudSaved.add(id); ++bookmarkVersion;
        remaining = remaining.filter((item) => item !== id);
        localStorage.setItem(key, JSON.stringify(remaining));
      }
      api.announce("此瀏覽器的舊收藏已同步到帳號。", "success");
    } catch (error) { api.announce(`部分收藏尚未同步：${error.message}，可稍後重試。`, "error"); }
    finally { button.disabled = false; cache.clear(); load({ force: true }); }
  }
  async function share() {
    try {
      if (navigator.share) await navigator.share({ title: detail.title, url: location.href });
      else { await navigator.clipboard.writeText(location.href); api.announce("文章連結已複製", "success"); }
    } catch (error) {
      if (error.name !== "AbortError") {
        const field = $("#discussion-share-link");
        field.hidden = false;
        field.value = location.href;
        field.focus();
        field.select();
        api.announce("請複製選取的文章連結。", "error");
      }
    }
  }
  function init(adapters) {
    api = adapters;
    const dialog = $("#discussion-reader");
    dialog.addEventListener("cancel", (event) => { event.preventDefault(); closePost(); });
    $("#discussion-reader-close").addEventListener("click", closePost);
    $("#discussion-sort").addEventListener("change", (event) => updateFilters({ sort: event.target.value }));
    $("#discussion-saved-filter").addEventListener("click", () => updateFilters({ saved: filters().saved ? "" : "1" }));
    $("#discussion-import-saved").addEventListener("click", importSaved);
    $("#discussion-feed-more").addEventListener("click", moreFeed);
    document.addEventListener("click", (event) => {
      const open = event.target.closest("[data-discussion-open]");
      if (open && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) {
        event.preventDefault(); openPost(open.dataset.discussionOpen, open); return;
      }
      const save = event.target.closest("[data-discussion-save]");
      if (save) { toggleSave(save.dataset.discussionSave); return; }
      const reaction = event.target.closest("[data-discussion-react]");
      if (reaction) { react(reaction); return; }
      const deletion = event.target.closest("[data-discussion-delete]");
      if (deletion) { remove(deletion); return; }
      const thread = event.target.closest("[data-discussion-thread]");
      if (thread) { loadThread(thread.dataset.discussionThread); return; }
      const moreThread = event.target.closest("[data-discussion-thread-more]");
      if (moreThread) { loadThread(moreThread.dataset.discussionThreadMore, true); return; }
      const reply = event.target.closest("[data-discussion-reply]");
      if (reply) { setReplyTarget(reply.dataset.discussionReply); return; }
      if (event.target.closest("[data-discussion-reply-cancel]")) { setReplyTarget(""); return; }
      if (event.target.closest("[data-discussion-retry]")) load({ force: true });
      if (event.target.closest("[data-discussion-detail-retry]")) { detailId = ""; syncDetail(); }
      if (event.target.closest("[data-discussion-comments-retry]")) loadComments();
      if (event.target.closest("[data-discussion-share]")) share();
      const quote = event.target.closest("[data-discussion-quote]");
      if (quote) {
        const form = dialog.querySelector(".post-comment-form");
        if (!form) { dialog.close(); api.commentGate(detail); return; }
        const row = findComment(quote.dataset.discussionQuote);
        const input = form.elements.body;
        const floor = row.parent_id ? `${row.parent_floor}-${row.floor}` : row.floor;
        const prefix = `引用 B${floor}：${row.body.slice(0, 180)}\n\n`;
        if ((prefix + input.value).length > 800) { api.announce("引用後會超過 800 字，請先縮短回覆。", "error"); return; }
        input.value = prefix + input.value;
        input.focus(); input.setSelectionRange(input.value.length, input.value.length);
        saveDraft(form, replyDraftKind());
      }
    });
    dialog.addEventListener("click", (event) => {
      if (event.target.closest("[data-open-auth], [data-open-verification]")) {
        event.stopPropagation();
        dialog.close();
        api.commentGate(detail);
        return;
      }
      const report = event.target.closest("[data-report-resource]");
      if (report) api.report(report);
    });
    dialog.addEventListener("input", (event) => saveDraft(event.target.closest(".post-comment-form"), replyDraftKind()));
    dialog.addEventListener("submit", async (event) => {
      const form = event.target.closest(".post-comment-form");
      if (!form) return;
      event.preventDefault();
      const id = detailId;
      const owner = api.context().accountId;
      const version = detailVersion;
      const root = replyTarget;
      const kind = replyDraftKind();
      if (await api.submitReply(form)) {
        if (owner !== api.context().accountId) return;
        clearDraft(kind);
        cache.clear();
        if (version !== detailVersion) return;
        ++detailVersion;
        comments = []; commentCursor = null; commentLoading = false;
        commentSort = "latest";
        $("#discussion-comment-sort").value = "latest";
        replyTarget = "";
        form.querySelector("[data-discussion-reply-target]").hidden = true;
        threads.clear();
        await loadComments();
        if (root && version + 1 === detailVersion) loadThread(root);
      }
    });
    const form = $("#global-community-form");
    form.addEventListener("input", () => saveDraft(form, "post"));
    form.addEventListener("change", () => saveDraft(form, "post"));
    if ("IntersectionObserver" in window) observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) moreFeed();
    }, { rootMargin: "120px" });
    window.addEventListener("storage", (event) => {
      if (event.key === storageKey("saved")) { cache.clear(); load(); }
    });
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && api.context().active && api.context().accountId) { cache.clear(); load(); }
    });
  }
  window.UniWayCommunity = { init, load, updateFilters, syncDetail, clearDraft,
    refresh: () => { cache.clear(); detailId = ""; load({ force: true }); },
    restorePostDraft: () => restoreDraft($("#global-community-form"), "post") };
})();

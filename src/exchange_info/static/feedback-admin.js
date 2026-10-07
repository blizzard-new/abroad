/* The feedback inbox. Every row is shown as text (textContent), never as markup, because anyone can write a message. */
(function () {
  "use strict";
  var KINDS = { suggestion: "建議", bug: "問題回報", praise: "稱讚", other: "其他" };
  var STATUSES = { new: "新的", read: "已讀", done: "已處理" };
  var statusBox = document.getElementById("status");
  var list = document.getElementById("list");

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function when(iso) {
    return new Date(iso).toLocaleString("zh-TW", { timeZone: "Asia/Taipei", hour12: false });
  }

  function kpi(label, value) {
    var card = el("div", "card kpi");
    card.appendChild(el("div", "label", label));
    card.appendChild(el("div", "value", String(value)));
    return card;
  }

  function post(url, body) {
    return fetch(url, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    }).then(function (response) {
      if (!response.ok) throw new Error("儲存失敗（" + response.status + "）。");
      return response.json();
    });
  }

  function item(row) {
    var card = el("article", "feedback-item");
    card.dataset.status = row.status;
    var meta = el("div", "feedback-meta");
    var kind = el("span", "feedback-kind", KINDS[row.kind] || row.kind);
    kind.dataset.kind = row.kind;
    meta.appendChild(kind);
    if (row.rating) meta.appendChild(el("span", "feedback-stars", "★".repeat(row.rating) + "☆".repeat(5 - row.rating)));
    meta.appendChild(el("span", "", when(row.created_at)));
    if (row.home_school) meta.appendChild(el("span", "", row.home_school));
    if (row.route) meta.appendChild(el("span", "", "頁面：" + row.route));
    meta.appendChild(el("span", "", row.signed_in ? "已登入" : "未登入"));
    card.appendChild(meta);
    card.appendChild(el("p", "feedback-message", row.message));
    if (row.contact) card.appendChild(el("p", "feedback-contact", "聯絡方式：" + row.contact));

    var actions = el("div", "feedback-actions");
    var select = el("select");
    select.setAttribute("aria-label", "狀態");
    Object.keys(STATUSES).forEach(function (key) {
      var option = el("option", "", STATUSES[key]);
      option.value = key;
      option.selected = key === row.status;
      select.appendChild(option);
    });
    var note = el("input");
    note.type = "text";
    note.maxLength = 1000;
    note.placeholder = "備註（只有管理員看得到）";
    note.value = row.admin_note || "";
    note.setAttribute("aria-label", "備註");
    var save = el("button", "", "儲存");
    save.type = "button";
    var saved = el("span", "feedback-saved");
    save.addEventListener("click", function () {
      save.disabled = true;
      saved.textContent = "";
      post("/admin/feedback/" + encodeURIComponent(row.id) + "/status", { status: select.value, note: note.value })
        .then(function (updated) {
          card.dataset.status = updated.status;
          saved.textContent = "已儲存";
          loadCounts();
        })
        .catch(function (error) { saved.textContent = error.message; })
        .then(function () { save.disabled = false; });
    });
    actions.appendChild(select);
    actions.appendChild(note);
    actions.appendChild(save);
    actions.appendChild(saved);
    card.appendChild(actions);
    return card;
  }

  function renderCounts(data) {
    document.getElementById("kpis").replaceChildren(
      kpi("全部", data.total), kpi("新的", data.counts.new), kpi("已讀", data.counts.read), kpi("已處理", data.counts.done),
      kpi(data.rating_count ? "平均評分（" + data.rating_count + " 則）" : "平均評分", data.average_rating === null ? "—" : data.average_rating + " / 5")
    );
    document.getElementById("summary-line").textContent = data.total
      ? "共 " + data.total + " 則，其中 " + data.counts.new + " 則還沒看。" +
        (data.truncated ? "（只顯示最新的 500 則，更多請匯出 CSV 或到 Supabase 查看）" : "")
      : "還沒有人留言。";
  }

  function render(data) {
    renderCounts(data);
    statusBox.hidden = true;
    list.replaceChildren();
    if (!data.items.length) {
      list.appendChild(el("p", "feedback-empty", data.total ? "這個篩選下沒有留言。" : "還沒有人留言。"));
      return;
    }
    data.items.forEach(function (row) { list.appendChild(item(row)); });
  }

  function fetchList() {
    var params = new URLSearchParams();
    var status = document.getElementById("status-filter").value;
    var kind = document.getElementById("kind-filter").value;
    if (status) params.set("status", status);
    if (kind) params.set("kind", kind);
    return fetch("/admin/feedback/list?" + params.toString(), { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (response) {
        if (response.status === 401) throw new Error("請先登入管理員帳號：到首頁登入後，重新整理此頁。");
        if (response.status === 403) throw new Error("這個帳號沒有管理員權限。");
        if (!response.ok) throw new Error("讀取失敗（" + response.status + "）。");
        return response.json();
      });
  }

  // After saving one row only the totals are refreshed, so the rest of the list does not jump around under the reader.
  function loadCounts() {
    fetchList().then(renderCounts).catch(function () { /* the saved note is already on screen */ });
  }

  function load() {
    statusBox.hidden = false;
    statusBox.className = "notice";
    statusBox.textContent = "正在讀取…";
    return fetchList().then(render).catch(function (error) {
      statusBox.hidden = false;
      statusBox.className = "notice error";
      statusBox.textContent = error.message;
    });
  }

  document.getElementById("controls").addEventListener("submit", function (event) { event.preventDefault(); load(); });
  ["status-filter", "kind-filter"].forEach(function (id) { document.getElementById(id).addEventListener("change", load); });
  load();
})();

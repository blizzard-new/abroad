/* Admin analytics dashboard. Every number comes from GET /admin/analytics/report (admin only). */
(function () {
  "use strict";

  var ROUTES = {
    home: "首頁", partners: "找交換學校", "partners:list": "找學校（列表）", "partners:map": "找學校（地圖）",
    school: "學校詳情", favorites: "我的選校", overview: "申請總覽", guide: "申請指南", advisor: "智慧顧問",
    calendar: "申請日曆", deadlines: "截止日", documents: "文件", "application-center": "申請文件中心",
    "document-check": "文件檢查", "writing-assistant": "寫作助手", scholarships: "獎學金", budget: "預算",
    eligibility: "資格初判", board: "討論板", "university-posts": "校內討論", community: "社群",
  };
  var FEATURES = {
    school_open: "打開學校頁", favorite_toggle: "收藏／取消收藏", search: "搜尋", filter_change: "篩選",
    view_switch: "切換列表／地圖", advisor_submit: "顧問分析", planning_action: "規劃操作", document_action: "文件操作",
    calendar_action: "日曆操作", outbound_click: "點外部連結", file_download: "下載檔案",
    community_composer_open: "開啟發文", community_topic: "點社群主題", board_follow: "追蹤討論板",
    school_pick: "選擇學校", theme_toggle: "切換主題",
  };
  var CHANNELS = {
    direct: "直接進站", search: "搜尋引擎", social: "社群／通訊軟體內開啟", referral: "其他網站",
    campaign: "活動連結（UTM）", paid: "廣告",
  };
  var DAYS = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"];
  var METRIC_UNITS = { lcp: "毫秒", fcp: "毫秒", ttfb: "毫秒", inp: "毫秒", load: "毫秒", cls: "" };

  var main = document.getElementById("main");
  var statusBox = document.getElementById("status");

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function num(value) { return value == null ? "—" : Number(value).toLocaleString("zh-TW"); }
  function dec(value, digits) { return value == null ? "—" : Number(value).toFixed(digits == null ? 1 : digits); }
  function metricValue(metric, value) {
    if (value == null) return "—";
    return metric === "cls" ? Number(value).toFixed(3) : Math.round(value).toLocaleString("zh-TW");
  }
  function seconds(value) {
    if (value == null) return "—";
    if (value < 60) return Math.round(value) + " 秒";
    return Math.floor(value / 60) + " 分 " + Math.round(value % 60) + " 秒";
  }
  function routeName(route) { return ROUTES[route] || route; }

  function delta(change, higherIsBetter) {
    if (change == null) return '<span class="delta flat">—</span>';
    if (change === 0) return '<span class="delta flat">持平</span>';
    var up = change > 0;
    var good = higherIsBetter === false ? !up : up;
    return '<span class="delta ' + (good ? (up ? "up" : "good-down") : (up ? "bad-up" : "down")) + '">' +
      (up ? "▲ " : "▼ ") + Math.abs(change) + "% 對比前一期</span>";
  }
  function kpi(label, value, change, higherIsBetter) {
    return '<div class="card kpi"><div class="label">' + esc(label) + '</div><div class="value">' + value +
      "</div>" + (change === undefined ? "" : delta(change, higherIsBetter)) + "</div>";
  }
  function card(title, body, extra) {
    return '<section class="card' + (extra ? " " + extra : "") + '"><h2>' + esc(title) + "</h2>" + body + "</section>";
  }
  function bars(rows, nameKey, valueKey, format, labeler) {
    if (!rows || !rows.length) return '<p class="muted">目前沒有資料。</p>';
    var max = Math.max.apply(null, rows.map(function (r) { return r[valueKey] || 0; })) || 1;
    return '<div class="bars">' + rows.map(function (r) {
      var name = labeler ? labeler(r[nameKey]) : r[nameKey];
      var value = r[valueKey] || 0;
      return '<div class="bar"><span class="name" title="' + esc(name) + '">' + esc(name) +
        '</span><span class="track"><span class="fill" style="width:' + (value / max * 100).toFixed(1) +
        '%"></span></span><span class="n">' + (format ? format(r) : num(value)) + "</span></div>";
    }).join("") + "</div>";
  }
  function shareBars(rows, nameKey, labeler) {
    return bars(rows, nameKey || "key", "count", function (r) { return num(r.count) + "（" + r.share + "%）"; }, labeler);
  }
  function table(headers, rows) {
    if (!rows.length) return '<p class="muted">目前沒有資料。</p>';
    return '<div class="scroll"><table><thead><tr>' + headers.map(function (h, i) {
      return '<th class="' + (i ? "num" : "") + '">' + esc(h) + "</th>";
    }).join("") + "</tr></thead><tbody>" + rows.map(function (row) {
      return "<tr>" + row.map(function (cell, i) {
        return '<td class="' + (i ? "num" : "") + '">' + cell + "</td>";
      }).join("") + "</tr>";
    }).join("") + "</tbody></table></div>";
  }

  function lineChart(days, series) {
    var width = 640, height = 220, left = 38, bottom = 24, top = 10, right = 8;
    var max = Math.max(1, Math.max.apply(null, series.reduce(function (all, s) { return all.concat(s.values); }, [])));
    var n = Math.max(days.length - 1, 1);
    function x(i) { return left + (width - left - right) * (i / n); }
    function y(v) { return top + (height - top - bottom) * (1 - v / max); }
    var grid = [0, 0.5, 1].map(function (f) {
      var gy = y(max * f);
      return '<line x1="' + left + '" x2="' + (width - right) + '" y1="' + gy + '" y2="' + gy + '" stroke="var(--line)"/>' +
        '<text x="' + (left - 6) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="10" fill="var(--muted)">' + Math.round(max * f) + "</text>";
    }).join("");
    var labels = days.map(function (d, i) {
      var step = Math.ceil(days.length / 8);
      return i % step === 0 || i === days.length - 1
        ? '<text x="' + x(i) + '" y="' + (height - 6) + '" text-anchor="middle" font-size="10" fill="var(--muted)">' + esc(d.slice(5)) + "</text>" : "";
    }).join("");
    var lines = series.map(function (s) {
      var points = s.values.map(function (v, i) { return x(i).toFixed(1) + "," + y(v).toFixed(1); }).join(" ");
      return '<polyline fill="none" stroke="' + esc(s.color) + '" stroke-width="2.2" stroke-linejoin="round" points="' + points + '"/>' +
        s.values.map(function (v, i) {
          return '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="2.6" fill="' + esc(s.color) + '"><title>' +
            esc(days[i] + " " + s.name + " " + v) + "</title></circle>";
        }).join("");
    }).join("");
    return '<svg class="chart" viewBox="0 0 ' + width + " " + height + '" role="img" aria-label="每日趨勢">' + grid + labels + lines + "</svg>" +
      '<div class="legend">' + series.map(function (s) { return '<span><i style="background:' + esc(s.color) + '"></i>' + esc(s.name) + "</span>"; }).join("") + "</div>";
  }

  function heatmap(grid) {
    var max = Math.max(1, Math.max.apply(null, grid.map(function (row) { return Math.max.apply(null, row); })));
    var head = '<span></span>' + Array.apply(null, Array(24)).map(function (_, h) { return "<span>" + (h % 3 === 0 ? h : "") + "</span>"; }).join("");
    var rows = grid.map(function (row, d) {
      return "<span>" + DAYS[d] + "</span>" + row.map(function (v, h) {
        return '<span class="cell" style="--a:' + (0.04 + 0.96 * v / max).toFixed(2) + '" title="' + DAYS[d] + " " + h + ":00 ・ " + v + ' 次瀏覽"></span>';
      }).join("");
    }).join("");
    return '<div class="heat" role="img" aria-label="一週中各時段瀏覽量">' + head + rows + "</div>";
  }

  function funnel(rows) {
    return '<div class="funnel">' + rows.map(function (r) {
      return '<div class="step"><div class="head"><span>' + esc(r.label) + "</span><span>" + num(r.visitors) +
        " 人（" + r.pct_of_first + '%）' + (r.dropped ? ' <span class="muted">流失 ' + num(r.dropped) + "</span>" : "") +
        '</span></div><div class="track"><div class="fill" style="width:' + Math.max(r.pct_of_first, r.visitors ? 2 : 0) + '%"></div></div></div>';
    }).join("") + "</div>";
  }

  function render(report) {
    var o = report.overview.current, c = report.overview.change_pct, q = report.data_quality;
    var out = [];
    var notes = [];
    if (q.truncated) notes.push('<span class="chip warn">資料量過大，只讀取了前 20 萬筆事件，數字偏低</span>');
    if (!q.client_events) notes.push('<span class="chip warn">這段期間還沒有瀏覽事件</span>');
    notes.push('<span class="chip">事件 ' + num(q.client_events) + " 筆</span>", '<span class="chip">伺服器事件 ' + num(q.server_events) + " 筆</span>");
    notes.push('<span class="chip">機器人事件 ' + num(q.bot_events_in_range) + (q.bots_excluded ? "（已排除）" : "（已包含）") + "</span>");
    out.push('<div class="chips">' + notes.join("") + "</div>");

    out.push('<div class="grid kpis">' +
      kpi("訪客", num(o.visitors), c.visitors) + kpi("造訪次數", num(o.sessions), c.sessions) +
      kpi("頁面瀏覽", num(o.pageviews), c.pageviews) + kpi("每次瀏覽頁數", dec(o.pages_per_session, 2), c.pages_per_session) +
      kpi("平均停留（實際操作）", seconds(o.avg_engaged_seconds), c.avg_engaged_seconds) +
      kpi("跳出率", dec(o.bounce_rate) + "%", c.bounce_rate, false) +
      kpi("新訪客", num(o.new_visitors)) + kpi("新帳號（伺服器紀錄）", num(report.signup.accounts_created_by_server)) + "</div>");

    var t = report.timeseries;
    out.push(card("每日趨勢", lineChart(t.days, [
      { name: "訪客", color: "var(--c1)", values: t.visitors }, { name: "造訪次數", color: "var(--c2)", values: t.sessions },
      { name: "頁面瀏覽", color: "var(--c3)", values: t.pageviews },
    ])));

    out.push('<div class="grid two">' +
      card("轉換漏斗（依訪客，須依序發生）", funnel(report.funnel)) +
      card("什麼時候有人來（台北時間）", heatmap(report.heatmap)) + "</div>");

    out.push('<div class="grid three">' +
      card("熱門頁面", table(["頁面", "瀏覽", "訪客", "跳出", "平均操作", "捲動"], report.pages.slice(0, 12).map(function (p) {
        return [esc(routeName(p.route)), num(p.views), num(p.visitors), dec(p.bounce_rate) + "%",
          p.avg_engaged_seconds == null ? "—" : seconds(p.avg_engaged_seconds), p.avg_scroll_pct == null ? "—" : Math.round(p.avg_scroll_pct) + "%"];
      }))) +
      card("流量來源", table(["來源", "造訪", "跳出", "註冊"], report.traffic.channels.map(function (r) {
        return [esc(CHANNELS[r.channel] || r.channel), num(r.sessions) + "（" + r.share + "%）", dec(r.bounce_rate) + "%", num(r.signups)];
      })) + "<h3>推薦網站</h3>" + shareBars(report.traffic.referrers.slice(0, 8), "host") +
        "<h3>UTM 活動</h3>" + shareBars(report.traffic.utm_campaign.slice(0, 8), "campaign")) +
      card("功能使用", table(["功能", "次數", "人數"], report.features.usage.map(function (f) {
        return [esc(FEATURES[f.feature] || f.feature), num(f.count), num(f.visitors)];
      }))) + "</div>");

    var s = report.schools;
    out.push('<div class="grid two">' +
      card("最多人看的學校", table(["學校", "國家", "開啟", "人數", "收藏", "收藏率", "外連"], s.top.slice(0, 15).map(function (r) {
        return [esc(r.school), esc(r.country || "—"), num(r.opens), num(r.visitors), num(r.favorites_added), r.favorite_rate + "%", num(r.outbound_clicks)];
      }))) +
      card("熱門國家", bars(s.countries, "country", "opens", function (r) { return num(r.opens) + "（" + num(r.visitors) + " 人）"; })) + "</div>");

    var se = report.search;
    out.push('<div class="grid two">' +
      card("搜尋", '<div class="chips"><span class="chip">共 ' + num(se.total) + ' 次</span><span class="chip">無結果率 ' + se.zero_result_rate +
        '%</span><span class="chip">搜尋後打開學校 ' + se.to_school_open_rate + '%</span><span class="chip">已遮蔽個資 ' + num(se.redacted) + "</span></div>" +
        table(["搜尋詞", "次數", "人數", "平均結果"], se.top_terms.slice(0, 12).map(function (r) {
          return [esc(r.term), num(r.searches), num(r.visitors), dec(r.avg_results)];
        }))) +
      card("找不到結果的搜尋（該補資料）", table(["搜尋詞", "次數", "無結果"], se.zero_result_terms.map(function (r) {
        return [esc(r.term), num(r.searches), num(r.zero_results)];
      })) + "<h3>篩選器使用</h3>" + shareBars(report.filters_used.usage, "filter")) + "</div>");

    var a = report.audience;
    out.push('<div class="grid three">' +
      card("裝置", shareBars(a.device)) + card("瀏覽器", shareBars(a.browser)) + card("作業系統", shareBars(a.os)) +
      card("螢幕寬度", shareBars(a.viewport)) + card("語言", shareBars(a.language)) + card("國家（需 CDN 提供）", shareBars(a.country)) +
      card("新訪客／回訪", shareBars(a.new_vs_returning)) + card("登入狀態", shareBars(a.signed_in)) + card("目前檢視的學校", shareBars(a.viewing_school)) + "</div>");

    var su = report.signup;
    out.push('<div class="grid two">' +
      card("註冊與登入", '<div class="chips"><span class="chip">開啟登入視窗 ' + num(su.dialog_opens) + '</span><span class="chip">開始 Google 登入 ' + num(su.starts) +
        '</span><span class="chip">登入成功 ' + num(su.successes) + '</span><span class="chip">成功率 ' + su.start_to_success_rate + '%</span></div>' +
        "<h3>新帳號的學校依據（伺服器紀錄）</h3>" + shareBars(su.accounts_created_by_school_basis, "basis") +
        "<h3>登入後選擇的學校</h3>" + shareBars(su.school_chosen, "school") +
        '<p class="muted">首次造訪到註冊的中位天數：' + (su.median_days_first_visit_to_signup == null ? "—" : su.median_days_first_visit_to_signup) + "</p>") +
      card("回訪率（首次造訪的訪客）", table(["第 N 天", "樣本", "回訪", "回訪率"], ["day_1", "day_7", "day_14", "day_30"].map(function (k) {
        var r = report.retention.summary[k];
        return ["第 " + k.slice(4) + " 天", num(r.cohort), num(r.retained), r.rate == null ? "—" : r.rate + "%"];
      })) + '<p class="muted">' + esc(report.retention.note) + "</p>" +
        table(["週", "人數", "D1", "D7", "D30"], report.retention.weekly.slice(-8).map(function (w) {
          return [esc(w.week_start), num(w.size), w.day_1 == null ? "—" : w.day_1 + "%", w.day_7 == null ? "—" : w.day_7 + "%", w.day_30 == null ? "—" : w.day_30 + "%"];
        }))) + "</div>");

    var en = report.engagement;
    out.push('<div class="grid three">' +
      card("單次造訪長度", shareBars(en.session_duration)) + card("單次造訪頁數", shareBars(en.pages_per_session)) +
      card("頁面捲動深度", shareBars(en.scroll_depth)) + "</div>");

    var pf = report.performance;
    out.push('<div class="grid two">' +
      card("網頁速度（真實使用者）", table(["指標", "樣本", "p50", "p75", "p95", "良好", "不佳"], pf.vitals.map(function (v) {
        var unit = METRIC_UNITS[v.metric] || "";
        return [esc(v.metric.toUpperCase() + (unit ? "（" + unit + "）" : "")), num(v.samples), metricValue(v.metric, v.p50), metricValue(v.metric, v.p75), metricValue(v.metric, v.p95),
          v.good_share == null ? "—" : v.good_share + "%", v.poor_share == null ? "—" : v.poor_share + "%"];
      })) + "<h3>LCP p75（依裝置）</h3>" + bars(pf.lcp_p75_by_device, "device", "p75", function (r) { return metricValue("lcp", r.p75) + " ms"; })) +
      card("前端錯誤", '<div class="chips"><span class="chip">錯誤 ' + num(report.errors.js_errors) + '</span><span class="chip">受影響造訪 ' +
        report.errors.sessions_affected_share + "%</span></div>" + table(["訊息", "次數", "造訪", "頁面"], report.errors.top_messages.slice(0, 8).map(function (m) {
          return [esc(m.message), num(m.count), num(m.sessions), esc(routeName(m.top_route))];
        })) + "<h3>瀏覽器看到的失敗請求</h3>" + shareBars(report.errors.failing_requests_seen_by_browser, "request")) + "</div>");

    var api = report.api;
    out.push(card("伺服器健康（API 請求）", '<div class="chips"><span class="chip">請求 ' + num(api.total_requests) + "</span>" +
      api.status_classes.map(function (r) { return '<span class="chip">' + esc(r.status) + " " + r.share + "%</span>"; }).join("") + "</div>" +
      table(["端點", "請求", "平均 ms", "p50*", "p95*", "≥1 秒", "5xx", "4xx"], api.routes.slice(0, 15).map(function (r) {
        return [esc(r.route), num(r.requests), dec(r.avg_ms), dec(r.p50_ms_estimate, 0), dec(r.p95_ms_estimate, 0), r.slow_share + "%",
          '<span class="' + (r.error_5xx ? "pill-bad" : "") + '">' + num(r.error_5xx) + "</span>", num(r.error_4xx)];
      })) + '<p class="muted">' + esc(api.note) + "</p>"));

    var cm = report.community;
    out.push('<div class="grid two">' +
      card("社群（伺服器紀錄）", '<div class="chips"><span class="chip">貼文 ' + num(cm.posts) + '</span><span class="chip">留言 ' + num(cm.comments) + "</span></div>" +
        "<h3>貼文：各版</h3>" + shareBars(cm.posts_by_board, "board") + "<h3>貼文：署名方式</h3>" + shareBars(cm.posts_by_identity, "identity") +
        "<h3>貼文：發文者學校依據</h3>" + shareBars(cm.posts_by_account_verification, "basis")) +
      card("最常被點的按鈕", table(["元件", "標籤", "點擊", "人數"], report.features.top_clicks.slice(0, 12).map(function (r) {
        return [esc(r.target), esc(r.label), num(r.clicks), num(r.visitors)];
      })) + "<h3>連續猛點（可能卡住或沒反應）</h3>" + shareBars(report.features.rage_clicks, "target")) + "</div>");

    main.innerHTML = out.join("");
  }

  function query() {
    var params = new URLSearchParams({
      days: document.getElementById("days").value,
      include_bots: document.getElementById("bots").checked ? "true" : "false",
    });
    var school = document.getElementById("school").value;
    if (school) params.set("school", school);
    return params;
  }

  function load() {
    var params = query();
    document.getElementById("export").href = "/admin/analytics/export.csv?" + params.toString();
    statusBox.textContent = "正在讀取統計…";
    fetch("/admin/analytics/report?" + params.toString(), { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (response) {
        if (response.status === 401 || response.status === 403) {
          throw new Error(response.status === 401
            ? "請先登入管理員帳號：到首頁登入後，重新整理此頁。"
            : "這個帳號沒有管理員權限。");
        }
        if (response.status === 503) throw new Error("使用統計目前已關閉（EXCHANGE_ANALYTICS=off）。");
        if (!response.ok) throw new Error("讀取失敗（" + response.status + "）。");
        return response.json();
      })
      .then(function (report) {
        var start = new Date(report.range.start), end = new Date(report.range.end - 1);
        document.getElementById("range-label").textContent =
          start.toLocaleDateString("zh-TW", { timeZone: "Asia/Taipei" }) + " – " +
          new Date(report.range.end).toLocaleDateString("zh-TW", { timeZone: "Asia/Taipei", month: "numeric", day: "numeric" }) +
          "（" + report.range.days + " 天，台北時間）・更新於 " +
          new Date(report.generated_at).toLocaleTimeString("zh-TW", { timeZone: "Asia/Taipei", hour: "2-digit", minute: "2-digit" });
        void end;
        render(report);
      })
      .catch(function (error) {
        main.innerHTML = '<p class="notice error">' + esc(error.message) + "</p>";
      });
  }

  document.getElementById("controls").addEventListener("submit", function (event) { event.preventDefault(); load(); });
  ["days", "school", "bots"].forEach(function (id) { document.getElementById(id).addEventListener("change", load); });
  load();
})();

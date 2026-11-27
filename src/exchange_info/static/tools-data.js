/* Progressive enhancement for UniWay Public Tools (/tools/...) and Open Data Pages (/data/...).
   Strictly CSP-safe: no eval, no inline handlers; pages remain 100% usable without JS. */
(function () {
  "use strict";

  document.documentElement.classList.add("js-tools");

  function copyText(text, button) {
    if (!text) return;
    var orig = button.textContent;
    function markDone() {
      button.textContent = "已複製！";
      setTimeout(function () {
        button.textContent = orig;
      }, 1800);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(markDone).catch(function () {});
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        markDone();
      } catch (_e) {}
      document.body.removeChild(ta);
    }
  }

  function bindCopyButtons() {
    document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var targetId = btn.getAttribute("data-copy-target");
        var target = targetId ? document.getElementById(targetId) : null;
        if (target) copyText(target.textContent.trim(), btn);
      });
    });

    document.querySelectorAll("[data-copy-share-url]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var form = document.querySelector("form[data-tool-form], form[data-data-filter]");
        var url = new URL(window.location.href);
        if (form) {
          var fd = new FormData(form);
          url.search = "";
          fd.forEach(function (val, key) {
            if (String(val).trim() !== "") {
              url.searchParams.set(key, String(val).trim());
            }
          });
          window.history.replaceState(null, "", url.toString());
        }
        copyText(url.toString(), btn);
      });
    });
  }

  function setText(selector, value) {
    document.querySelectorAll(selector).forEach(function (el) {
      el.textContent = value;
    });
  }

  function fmtNum(n, digits) {
    var d = typeof digits === "number" ? digits : 2;
    return Number(n.toFixed(d)).toString();
  }

  function fmtInt(n) {
    return Math.round(n).toLocaleString("en-US");
  }

  /* 1. ECTS Credit Converter */
  function initEctsTool() {
    var form = document.querySelector('form[data-tool-form="ects"]');
    if (!form) return;
    var sysEl = document.getElementById("ects-system");
    var amtEl = document.getElementById("ects-amount");
    var ratioEl = document.getElementById("ects-ratio");
    var minTwEl = document.getElementById("ects-min-tw");

    function update() {
      var sys = sysEl.value || "ects";
      var amt = Math.max(0, Math.min(240, parseFloat(amtEl.value) || 0));
      var ratio = Math.max(1, Math.min(4, parseFloat(ratioEl.value) || 2));
      var minTw = Math.max(0, Math.min(30, parseFloat(minTwEl.value) || 0));
      var ects = sys === "tw" ? amt * ratio : (sys === "us" || sys === "jp" ? amt * 2 : amt);
      var tw = ects / ratio;
      var us = ects / 2;
      var usQ = us * 1.5;
      var jp = ects / 2;
      var reqEcts = minTw * ratio;

      setText('[data-out="ects"]', fmtNum(ects, 2) + " ECTS");
      setText('[data-out="workload"]', Math.round(ects * 25) + "–" + Math.round(ects * 30) + " 小時");
      setText('[data-out="tw"]', fmtNum(tw, 2) + " 學分");
      setText('[data-out="ratio-note"]', fmtNum(ratio, 2) + " ECTS = 1 學分");
      setText('[data-out="us"]', fmtNum(us, 2) + " 學分");
      setText('[data-out="us-q"]', "學季制 " + fmtNum(usQ, 2) + " 學分");
      setText('[data-out="jp"]', fmtNum(jp, 2) + " 単位");
      setText('[data-out="req-ects"]', fmtNum(reqEcts, 1) + " ECTS");
      setText('[data-out="buf-ects"]', fmtNum(reqEcts + 5, 1) + " ECTS");
      setText(
        '[data-out="min-status"]',
        ects >= reqEcts
          ? "已達母校最低門檻（至少 " + fmtNum(reqEcts, 1) + " ECTS）"
          : "尚未達母校最低門檻（需至少 " + fmtNum(reqEcts, 1) + " ECTS）"
      );
    }

    [sysEl, amtEl, ratioEl, minTwEl].forEach(function (el) {
      if (el) el.addEventListener("input", update);
      if (el) el.addEventListener("change", update);
    });
  }

  /* 2. GPA & Bavarian Converter */
  function scoreTo43(s) {
    if (s >= 90) return 4.3;
    if (s >= 85) return 4.0;
    if (s >= 80) return 3.7;
    if (s >= 77) return 3.3;
    if (s >= 73) return 3.0;
    if (s >= 70) return 2.7;
    if (s >= 67) return 2.3;
    if (s >= 63) return 2.0;
    if (s >= 60) return 1.7;
    return 0.0;
  }

  function bavarian(val, nmax, nmin) {
    if (nmax <= nmin || val < nmin) return null;
    var c = Math.min(nmax, val);
    var raw = 1 + (3 * (nmax - c)) / (nmax - nmin);
    var trunc = Math.floor((raw + 1e-9) * 10) / 10;
    return Math.max(1.0, Math.min(4.0, trunc)).toFixed(1);
  }

  function initGpaTool() {
    var form = document.querySelector('form[data-tool-form="gpa"]');
    if (!form) return;
    var scaleEl = document.getElementById("gpa-scale");
    var valEl = document.getElementById("gpa-value");
    var maxEl = document.getElementById("gpa-max");
    var minEl = document.getElementById("gpa-min");

    function updateSummary() {
      var sc = scaleEl.value || "percent";
      var val = parseFloat(valEl.value) || 0;
      var nmax = parseFloat(maxEl.value) || 100;
      var nmin = parseFloat(minEl.value) || 60;
      var pct, g43, g40pm, g40std, bav;

      if (sc === "gpa43") {
        g43 = Math.max(0, Math.min(4.3, val));
        pct = g43 >= 4.15 ? 92 : g43 >= 3.85 ? 87 : g43 >= 3.5 ? 82 : g43 >= 3.15 ? 78 : g43 >= 2.85 ? 75 : g43 >= 2.5 ? 71 : g43 >= 2.15 ? 68 : g43 >= 1.85 ? 65 : g43 >= 1.5 ? 61 : 50;
        g40pm = Math.min(4.0, g43);
        g40std = pct >= 80 ? 4.0 : pct >= 70 ? 3.0 : pct >= 60 ? 2.0 : 0.0;
        bav = bavarian(g43, 4.3, 1.7);
      } else if (sc === "gpa40") {
        g40pm = Math.max(0, Math.min(4.0, val));
        pct = g40pm >= 3.85 ? 88 : g40pm >= 3.5 ? 82 : g40pm >= 3.15 ? 78 : g40pm >= 2.85 ? 75 : g40pm >= 2.5 ? 71 : g40pm >= 2.15 ? 68 : g40pm >= 1.85 ? 65 : g40pm >= 1.5 ? 61 : 50;
        g43 = g40pm;
        g40std = g40pm;
        bav = bavarian(g40pm, 4.0, 2.0);
      } else {
        pct = Math.max(0, Math.min(100, val));
        g43 = scoreTo43(pct);
        g40pm = Math.min(4.0, g43);
        g40std = pct >= 80 ? 4.0 : pct >= 70 ? 3.0 : pct >= 60 ? 2.0 : 0.0;
        bav = bavarian(pct, nmax, nmin);
      }

      setText('[data-gpa-out="gpa40pm"]', g40pm.toFixed(2) + " / 4.0");
      setText('[data-gpa-out="gpa40std"]', "四等第 " + g40std.toFixed(2));
      setText('[data-gpa-out="gpa43"]', g43.toFixed(2) + " / 4.3");
      setText('[data-gpa-out="pct"]', "約 " + pct.toFixed(1) + " 分");
      setText('[data-gpa-out="bavarian"]', bav !== null ? bav : "不及格");
    }

    [scaleEl, valEl, maxEl, minEl].forEach(function (el) {
      if (el) el.addEventListener("input", updateSummary);
      if (el) el.addEventListener("change", updateSummary);
    });

    var tbody = document.getElementById("gpa-course-tbody");
    var addBtn = document.getElementById("gpa-add-row");
    var weightedSummary = document.getElementById("gpa-weighted-summary");

    function strongNode(txt) {
      var s = document.createElement("strong");
      s.textContent = txt;
      return s;
    }

    function recalcCourses() {
      if (!tbody || !weightedSummary) return;
      var totalCr = 0;
      var sumPct = 0;
      var sum43 = 0;
      var sum40 = 0;
      tbody.querySelectorAll("tr").forEach(function (tr) {
        var crInput = tr.querySelector(".gpa-c-credit");
        var scInput = tr.querySelector(".gpa-c-score");
        var cr = Math.max(0, parseFloat(crInput ? crInput.value : "0") || 0);
        var sc = Math.max(0, Math.min(100, parseFloat(scInput ? scInput.value : "0") || 0));
        var p43 = scoreTo43(sc);
        var p40 = Math.min(4.0, p43);
        var c43 = tr.querySelector(".gpa-c-43");
        var c40 = tr.querySelector(".gpa-c-40");
        if (c43) c43.textContent = p43.toFixed(1);
        if (c40) c40.textContent = p40.toFixed(1);
        totalCr += cr;
        sumPct += sc * cr;
        sum43 += p43 * cr;
        sum40 += p40 * cr;
      });
      if (totalCr <= 0) {
        weightedSummary.textContent = "請輸入至少一門學分數大於 0 的課程。";
        return;
      }
      var avgPct = sumPct / totalCr;
      var avg43 = sum43 / totalCr;
      var avg40 = sum40 / totalCr;
      var bav = bavarian(avgPct, 100, 60) || "不及格";
      weightedSummary.innerHTML = "";
      weightedSummary.append(
        "總學分 ",
        strongNode(totalCr.toFixed(1)),
        " ｜ 平均 ",
        strongNode(avgPct.toFixed(2)),
        " ｜ 4.3 制 ",
        strongNode(avg43.toFixed(2)),
        " ｜ 4.0 制 ",
        strongNode(avg40.toFixed(2)),
        " ｜ 德制 ",
        strongNode(bav)
      );
    }

    if (tbody) tbody.addEventListener("input", recalcCourses);
    if (addBtn && tbody) {
      addBtn.addEventListener("click", function () {
        var idx = tbody.querySelectorAll("tr").length + 1;
        var tr = document.createElement("tr");
        tr.innerHTML =
          '<td><input type="text" value="科目 ' + idx + '" aria-label="課程名稱"></td>' +
          '<td><input type="number" class="gpa-c-credit" value="3" min="0.5" max="15" step="0.5" aria-label="學分數"></td>' +
          '<td><input type="number" class="gpa-c-score" value="80" min="0" max="100" step="1" aria-label="百分制成績"></td>' +
          '<td class="gpa-c-43">3.7</td><td class="gpa-c-40">3.7</td>';
        tbody.appendChild(tr);
        recalcCourses();
      });
    }
  }

  /* 3. Language Score Converter + Live Real DB Fetch */
  function initLanguageTool() {
    var form = document.querySelector('form[data-tool-form="language"]');
    if (!form) return;
    var homeEl = document.getElementById("lang-home");
    var testEl = document.getElementById("lang-test");
    var scoreEl = document.getElementById("lang-score");
    var timer = null;

    var defaultScores = { ielts: "6.5", toefl: "85", toeic: "800", cefr: "B2", jlpt: "N2" };

    testEl.addEventListener("change", function () {
      var t = testEl.value;
      if (defaultScores[t]) scoreEl.value = defaultScores[t];
      scheduleFetch();
    });
    homeEl.addEventListener("change", scheduleFetch);
    scoreEl.addEventListener("input", scheduleFetch);

    function renderMiniList(containerId, items, emptyText) {
      var container = document.getElementById(containerId);
      if (!container) return;
      container.innerHTML = "";
      if (!items || !items.length) {
        var p = document.createElement("p");
        p.textContent = emptyText;
        container.appendChild(p);
        return;
      }
      var ul = document.createElement("ul");
      ul.className = "uw-partner-mini-grid";
      items.forEach(function (item) {
        var li = document.createElement("li");
        li.className = "uw-partner-mini-card";
        var top = document.createElement("div");
        top.className = "uw-partner-mini-top";
        var a = document.createElement("a");
        a.href = item.partner_url;
        var st = document.createElement("strong");
        st.textContent = item.school_name;
        a.appendChild(st);
        var cSpan = document.createElement("span");
        cSpan.className = "uw-mini-country";
        cSpan.textContent = item.country;
        top.appendChild(a);
        top.appendChild(cSpan);

        var pRule = document.createElement("p");
        pRule.className = "uw-mini-rule";
        var tag = document.createElement("span");
        tag.className = "uw-tag-ok";
        tag.textContent = item.matched_rule;
        pRule.appendChild(tag);
        pRule.append(" · " + item.availability);

        li.appendChild(top);
        li.appendChild(pRule);
        ul.appendChild(li);
      });
      container.appendChild(ul);
    }

    function scheduleFetch() {
      if (timer) clearTimeout(timer);
      timer = setTimeout(function () {
        var params = new URLSearchParams({
          home: homeEl.value,
          test: testEl.value,
          score: scoreEl.value.trim() || "6.5"
        });
        fetch("/tools/language-score-converter.json?" + params.toString(), { headers: { Accept: "application/json" } })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (data) {
            if (!data) return;
            var conv = data.conversion;
            var m = data.match;
            setText('[data-lang-out="cefr"]', conv.cefr);
            setText('[data-lang-out="input-display"]', conv.input_display);
            setText('[data-lang-out="ielts"]', conv.ielts_range);
            setText('[data-lang-out="toefl"]', conv.toefl_range);
            setText('[data-lang-out="toefl-new"]', "新制 " + conv.toefl_new);
            setText('[data-lang-out="toeic"]', conv.toeic_range);
            setText('[data-lang-out="home-name"]', m.home_name);
            setText('[data-lang-out="total-pages"]', String(m.total_partner_pages));
            setText('[data-lang-out="direct-count"]', m.direct_match_count + " 所");
            setText('[data-lang-out="equiv-stat"]', m.equiv_match_count + " 所");
            setText('[data-lang-out="equiv-count"]', String(m.equiv_match_count));
            setText('[data-lang-out="below-count"]', m.below_threshold_count + " 所");
            setText('[data-lang-out="unconfirmed-count"]', m.unconfirmed_or_other_count + " 所");

            var homeLink = document.getElementById("lang-home-link");
            if (homeLink) {
              homeLink.href = m.home_school_url;
              homeLink.textContent = m.home_short_name + "完整名單";
            }
            var plannerLink = document.getElementById("lang-planner-link");
            if (plannerLink) plannerLink.href = m.home_planner_url;

            renderMiniList(
              "lang-direct-list",
              m.direct_samples,
              "目前無單獨列載此檢定且低於此分數的合作校條目，可展開同級參考或查看母校完整名單。"
            );
            var eqBlock = document.getElementById("lang-equiv-block");
            if (eqBlock) {
              eqBlock.hidden = Boolean(conv.is_japanese);
              if (!conv.is_japanese) {
                renderMiniList("lang-equiv-list", m.equiv_samples, "目前無其他同級英語檢定合作校條目。");
              }
            }
          })
          .catch(function () {});
      }, 220);
    }
  }

  /* 4. Exchange Budget Calculator */
  function initBudgetTool() {
    var form = document.querySelector('form[data-tool-form="budget"]');
    var tplNode = document.getElementById("uw-budget-templates");
    if (!form || !tplNode) return;
    var templates = {};
    try {
      templates = JSON.parse(tplNode.textContent);
    } catch (_e) {
      return;
    }

    var countryEl = document.getElementById("b-country");
    var monthsEl = document.getElementById("b-months");
    var rateEl = document.getElementById("b-rate");
    var housingEl = document.getElementById("b-housing");
    var foodEl = document.getElementById("b-food");
    var transportEl = document.getElementById("b-transport");
    var otherEl = document.getElementById("b-other");
    var oneTimeEl = document.getElementById("b-onetime");
    var scholEl = document.getElementById("b-scholarship");
    var tbody = document.getElementById("b-scenario-tbody");
    var previewEl = document.getElementById("budget-summary-copy");

    countryEl.addEventListener("change", function () {
      var tpl = templates[countryEl.value];
      if (!tpl) return;
      monthsEl.value = tpl.months;
      rateEl.value = tpl.bundled_rate;
      housingEl.value = tpl.housing;
      foodEl.value = tpl.food;
      transportEl.value = tpl.transport;
      otherEl.value = tpl.other;
      oneTimeEl.value = tpl.one_time_twd;
      recalc();
    });

    function recalc() {
      var tpl = templates[countryEl.value] || templates.japan;
      var cur = tpl ? tpl.currency : "JPY";
      var m = Math.max(1, Math.min(12, parseInt(monthsEl.value, 10) || 5));
      var r = Math.max(0.0001, parseFloat(rateEl.value) || 1);
      var h = Math.max(0, parseFloat(housingEl.value) || 0);
      var f = Math.max(0, parseFloat(foodEl.value) || 0);
      var t = Math.max(0, parseFloat(transportEl.value) || 0);
      var o = Math.max(0, parseFloat(otherEl.value) || 0);
      var oneTime = Math.max(0, parseFloat(oneTimeEl.value) || 0);
      var schol = Math.max(0, parseFloat(scholEl.value) || 0);

      var mForeign = h + f + t + o;
      var semForeign = mForeign * m;
      var factors = [
        ["匯率 -10%", 0.9],
        ["基準匯率（0%）", 1.0],
        ["匯率 +10%", 1.1]
      ];
      if (tbody) tbody.innerHTML = "";
      var baseMonthly = 0, baseGross = 0, baseNet = 0, highGross = 0;

      factors.forEach(function (pair) {
        var sr = r * pair[1];
        var mTwd = Math.round(mForeign * sr);
        var livTwd = Math.round(semForeign * sr);
        var grossTwd = Math.round(livTwd + oneTime);
        var netTwd = Math.max(0, Math.round(grossTwd - schol));
        if (pair[1] === 1.0) {
          baseMonthly = mTwd;
          baseGross = grossTwd;
          baseNet = netTwd;
        }
        if (pair[1] === 1.1) highGross = grossTwd;

        if (tbody) {
          var tr = document.createElement("tr");
          if (pair[1] === 1.0) tr.className = "uw-row-highlight";
          tr.innerHTML =
            '<th scope="row">' + pair[0] + "</th>" +
            "<td>1 " + cur + " = " + Number(sr.toFixed(4)) + " TWD</td>" +
            "<td>NT$ " + fmtInt(mTwd) + "</td>" +
            "<td>NT$ " + fmtInt(livTwd) + "</td>" +
            "<td>NT$ " + fmtInt(grossTwd) + "</td>" +
            "<td><strong>NT$ " + fmtInt(netTwd) + "</strong></td>";
          tbody.appendChild(tr);
        }
      });

      setText('[data-b-out="cur-code"]', cur);
      setText('[data-b-out="cur-code-2"]', cur);
      setText('[data-b-out="monthly-foreign"]', cur + " " + fmtInt(mForeign));
      setText('[data-b-out="monthly-twd"]', "約 NT$ " + fmtInt(baseMonthly) + "／月");
      setText('[data-b-out="gross-twd"]', "NT$ " + fmtInt(baseGross));
      setText('[data-b-out="months-label"]', m + " 個月＋行前費用");
      setText('[data-b-out="net-twd"]', "NT$ " + fmtInt(baseNet));
      setText('[data-b-out="fx-delta"]', "匯率 +10% 多備 NT$ " + fmtInt(highGross - baseGross));
      setText('[data-b-out="reserve-twd"]', "NT$ " + fmtInt(baseMonthly));

      if (previewEl && tpl) {
        previewEl.textContent =
          "【UniWay 交換預算試算】" + tpl.name + "（" + m + " 個月）\n" +
          "・每月外幣生活費：" + cur + " " + fmtInt(mForeign) + "\n" +
          "・基準匯率（1 " + cur + " = " + Number(r.toFixed(4)) + " TWD）總支出：NT$ " + fmtInt(baseGross) + "（含機票簽證等一次性 NT$ " + fmtInt(oneTime) + "）\n" +
          "・扣除預估補助 NT$ " + fmtInt(schol) + " 後淨自備款：NT$ " + fmtInt(baseNet) + "\n" +
          "・匯率 +10% 安全緩衝需多準備：NT$ " + fmtInt(highGross - baseGross) + "\n" +
          "・試算工具：https://app.uniway-tw.com/tools/exchange-budget-calculator（實際資格、名額與期限以各校最新官方公告為準。）";
      }
    }

    [monthsEl, rateEl, housingEl, foodEl, transportEl, otherEl, oneTimeEl, scholEl].forEach(function (el) {
      if (el) el.addEventListener("input", recalc);
    });
  }

  /* 5. Timeline Generator */
  function addDaysIso(isoDate, deltaDays) {
    var parts = isoDate.split("-");
    var d = new Date(Date.UTC(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10)));
    d.setUTCDate(d.getUTCDate() + deltaDays);
    return d.toISOString().slice(0, 10);
  }

  function initTimelineTool() {
    var form = document.querySelector('form[data-tool-form="timeline"]');
    var dataNode = document.getElementById("uw-timeline-schools");
    if (!form || !dataNode) return;
    var payload = null;
    try {
      payload = JSON.parse(dataNode.textContent);
    } catch (_e) {
      return;
    }

    var schoolEl = document.getElementById("tl-school");
    var termEl = document.getElementById("tl-term");
    var dlEl = document.getElementById("tl-deadline");
    var listEl = document.getElementById("tl-milestone-list");
    var icsLink = document.getElementById("tl-ics-link");
    var offLink = document.getElementById("tl-official-link");
    var pageLink = document.getElementById("tl-school-page-link");

    function syncDefaultAnchor() {
      var s = payload.schools[schoolEl.value];
      var t = payload.terms[termEl.value];
      if (!s || !t) return;
      if (termEl.value === "2027-fall" && s.deadline_iso && s.date_status_code === "verified_exact" && s.deadline_iso >= "2026-08-01") {
        dlEl.value = s.deadline_iso;
      } else {
        dlEl.value = t.default_anchor;
      }
      renderTimeline();
    }

    function renderTimeline() {
      var sid = schoolEl.value;
      var tk = termEl.value;
      var s = payload.schools[sid];
      var t = payload.terms[tk];
      if (!s || !t) return;
      var anchor = dlEl.value || t.default_anchor;

      setText('[data-tl-out="school-name"]', s.school_name);
      setText('[data-tl-out="rec-deadline"]', s.deadline_display);
      setText('[data-tl-out="rec-status"]', s.status_label);

      if (offLink && s.official_url) offLink.href = s.official_url;
      if (pageLink) pageLink.href = "/schools/" + sid;
      if (icsLink) {
        var qp = new URLSearchParams({ school: sid, term: tk, deadline: anchor });
        icsLink.href = "/tools/timeline-generator.ics?" + qp.toString();
      }

      var dep = t.departure_date <= addDaysIso(anchor, 60) ? addDaysIso(anchor, 240) : t.departure_date;
      var steps = [
        ["截止前 180 天", addDaysIso(anchor, -180), "確認語檢門檻並報考檢定"],
        ["截止前 90 天", addDaysIso(anchor, -90), "盤點 " + s.short_name + " 合作校清單與學分規定"],
        ["截止前 45 天", addDaysIso(anchor, -45), "邀約師長推薦信、擬定志願序與讀書計畫大綱"],
        ["截止前 21 天", addDaysIso(anchor, -21), "完成中／外文讀書計畫與履歷初稿"],
        ["截止前 10 天", addDaysIso(anchor, -10), "申請歷年成績單、在學證明與系所核章"],
        ["截止前 3 天", addDaysIso(anchor, -3), "完成線上報名填寫與檔案檢查"],
        ["校內截止基準日", anchor, s.short_name + " 校內交換申請截止基準日"],
        ["出發前 120 天", addDaysIso(dep, -120), "完成姊妹校網報、宿舍登記與簽證申辦"]
      ];

      if (listEl) {
        listEl.innerHTML = "";
        steps.forEach(function (st) {
          var li = document.createElement("li");
          li.className = "uw-timeline-step";
          var dDiv = document.createElement("div");
          dDiv.className = "uw-timeline-date";
          var offSpan = document.createElement("span");
          offSpan.className = "uw-timeline-offset";
          offSpan.textContent = st[0];
          var tNode = document.createElement("time");
          tNode.setAttribute("datetime", st[1]);
          tNode.textContent = st[1];
          dDiv.appendChild(offSpan);
          dDiv.appendChild(tNode);

          var cDiv = document.createElement("div");
          cDiv.className = "uw-timeline-content";
          var h4 = document.createElement("h4");
          h4.textContent = st[2];
          cDiv.appendChild(h4);

          li.appendChild(dDiv);
          li.appendChild(cDiv);
          listEl.appendChild(li);
        });
      }
    }

    schoolEl.addEventListener("change", syncDefaultAnchor);
    termEl.addEventListener("change", syncDefaultAnchor);
    dlEl.addEventListener("change", renderTimeline);
  }

  /* 6. Instant Client-Side Filter/Sort for /data/taiwan-exchange-overview & /data/deadlines */
  function initDataFilters() {
    var ovForm = document.querySelector('form[data-data-filter="overview"]');
    if (ovForm) {
      var qEl = document.getElementById("ov-q");
      var secEl = document.getElementById("ov-sector");
      var sortEl = document.getElementById("ov-sort");
      var tbody = document.getElementById("overview-tbody");
      var countEl = document.getElementById("overview-visible-count");

      function filterOverview() {
        if (!tbody) return;
        var q = (qEl.value || "").trim().toLowerCase();
        var sec = secEl.value;
        var sortKey = sortEl.value;
        var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr[data-row-name]"));

        rows.sort(function (a, b) {
          if (sortKey === "countries") return Number(b.dataset.countries) - Number(a.dataset.countries);
          if (sortKey === "toeic") return Number(b.dataset.toeic) - Number(a.dataset.toeic);
          if (sortKey === "jlpt") return Number(b.dataset.jlpt) - Number(a.dataset.jlpt);
          if (sortKey === "name") return (a.dataset.rowName || "").localeCompare(b.dataset.rowName || "", "zh-Hant");
          return Number(b.dataset.partners) - Number(a.dataset.partners);
        });

        var visible = 0;
        rows.forEach(function (tr) {
          var matchSec = sec === "all" || (sec === "public" && tr.dataset.rowSector === "公立") || (sec === "private" && tr.dataset.rowSector === "私立");
          var matchQ = !q || (tr.dataset.rowName || "").toLowerCase().indexOf(q) !== -1;
          var show = matchSec && matchQ;
          tr.hidden = !show;
          if (show) {
            visible += 1;
            if (tr.firstElementChild) tr.firstElementChild.textContent = String(visible);
          }
          tbody.appendChild(tr);
        });
        if (countEl) countEl.textContent = visible + " 校";
      }

      [qEl, secEl, sortEl].forEach(function (el) {
        if (el) el.addEventListener("input", filterOverview);
        if (el) el.addEventListener("change", filterOverview);
      });
    }

    var dlForm = document.querySelector('form[data-data-filter="deadlines"]');
    if (dlForm) {
      var dlQ = document.getElementById("dl-q");
      var dlMonth = document.getElementById("dl-month");
      var dlStatus = document.getElementById("dl-status");
      var dlTbody = document.getElementById("deadlines-tbody");
      var dlCount = document.getElementById("dl-visible-count");

      function filterDeadlines() {
        if (!dlTbody) return;
        var q = (dlQ.value || "").trim().toLowerCase();
        var m = dlMonth.value;
        var st = dlStatus.value;
        var visible = 0;
        dlTbody.querySelectorAll("tr[data-dl-name]").forEach(function (tr) {
          var mList = (tr.dataset.dlMonths || "").split(",");
          var code = tr.dataset.dlStatus || "";
          var matchM = m === "all" || mList.indexOf(m) !== -1;
          var matchSt =
            st === "all" ||
            (st === "active" && (code === "open" || code === "upcoming" || code === "action_required")) ||
            (st === "pending" && code === "needs_confirmation") ||
            (st === "closed" && (code === "closed" || code === "reference_only"));
          var matchQ = !q || (tr.dataset.dlName || "").toLowerCase().indexOf(q) !== -1;
          var show = matchM && matchSt && matchQ;
          tr.hidden = !show;
          if (show) visible += 1;
        });
        if (dlCount) dlCount.textContent = String(visible);
      }

      [dlQ, dlMonth, dlStatus].forEach(function (el) {
        if (el) el.addEventListener("input", filterDeadlines);
        if (el) el.addEventListener("change", filterDeadlines);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var activeNav = document.querySelector('.reading-header nav a[aria-current="page"]');
    if (activeNav && activeNav.parentElement && activeNav.parentElement.scrollWidth > activeNav.parentElement.clientWidth) {
      activeNav.parentElement.scrollLeft = Math.max(0, activeNav.offsetLeft - 24);
    }
    bindCopyButtons();
    initEctsTool();
    initGpaTool();
    initLanguageTool();
    initBudgetTool();
    initTimelineTool();
    initDataFilters();
  });
})();

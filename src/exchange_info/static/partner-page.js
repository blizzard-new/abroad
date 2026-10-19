(function () {
  "use strict";

  function parseJsonScript(id) {
    var node = document.getElementById(id);
    if (!node || !node.textContent) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (_err) {
      return null;
    }
  }

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text || "";
  }

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderNetworkHeatStateBox(entry) {
    if (!entry || !entry.status || !entry.heat) return "";
    var st = entry.status;
    var ht = entry.heat;
    if (!ht.heat_unlocked) {
      var pillarsHtml = (st.solo_tool_pillars || [])
        .map(function (p) {
          return (
            '<a class="cs-solo-pillar-card" href="' +
            escapeHtml(p.action_url) +
            '">' +
            "<strong>" +
            escapeHtml(p.title) +
            "</strong>" +
            "<span>" +
            escapeHtml(p.subtitle) +
            "</span>" +
            '<em class="cs-pillar-cta">' +
            escapeHtml(p.action_label) +
            " →</em>" +
            "</a>"
          );
        })
        .join("");
      return (
        '<div class="cs-heat-locked-box" id="cs-heat-state-box" data-heat-unlocked="false">' +
        '<div class="cs-heat-locked-header">' +
        '<span class="cs-stage-badge is-solo">' +
        escapeHtml(st.stage_label) +
        "</span>" +
        '<span class="cs-plan-progress-pill" id="cs-plan-progress-pill">' +
        "目前同校申請計畫：" +
        st.active_plan_count +
        " / " +
        st.unlock_threshold_min +
        " 份（再 " +
        st.plans_needed_to_unlock +
        " 份解鎖匿名搓湯圓）" +
        "</span>" +
        "</div>" +
        '<p class="cs-heat-headline" id="cs-heat-headline">' +
        escapeHtml(st.public_status_headline) +
        "</p>" +
        '<p class="cs-heat-desc" id="cs-heat-desc">' +
        escapeHtml(st.public_status_description) +
        "</p>" +
        '<div class="cs-solo-pillars-grid" aria-label="單人使用即具完整價值的三大工具">' +
        pillarsHtml +
        "</div>" +
        "</div>"
      );
    }

    var tagsHtml = (ht.anonymous_applicant_tags || [])
      .map(function (tag) {
        return '<span class="cs-anon-tag">' + escapeHtml(tag) + "</span>";
      })
      .join("");
    return (
      '<div class="cs-heat-unlocked-box" id="cs-heat-state-box" data-heat-unlocked="true">' +
      '<div class="cs-heat-unlocked-header">' +
      '<span class="cs-stage-badge is-unlocked">' +
      escapeHtml(st.stage_label) +
      "</span>" +
      '<span class="cs-plan-progress-pill is-unlocked" id="cs-plan-progress-pill">' +
      escapeHtml(st.short_name) +
      " 本季已累積 " +
      st.active_plan_count +
      " 份申請計畫（已超過 " +
      st.unlock_threshold_min +
      " 份解鎖門檻）" +
      "</span>" +
      "</div>" +
      '<p class="cs-heat-headline" id="cs-heat-headline">' +
      escapeHtml(ht.competition_status_label) +
      "</p>" +
      '<div class="cs-heat-metrics-grid" id="cs-heat-metrics-grid">' +
      '<div class="cs-heat-metric"><span>同校列入志願總人數</span><strong id="cs-heat-total">' +
      ht.total_interested_count +
      " 人</strong></div>" +
      '<div class="cs-heat-metric"><span>列為「第 1 志願」</span><strong id="cs-heat-first">' +
      ht.first_choice_count +
      " 人</strong></div>" +
      '<div class="cs-heat-metric"><span>列為「第 2–3 志願」</span><strong id="cs-heat-other">' +
      ht.second_or_third_choice_count +
      " 人</strong></div>" +
      '<div class="cs-heat-metric"><span>當期名額對照</span><strong id="cs-heat-quota">' +
      escapeHtml(ht.quota_hint) +
      "</strong></div>" +
      "</div>" +
      '<div class="cs-anon-tags-row" id="cs-anon-tags-row"><strong>匿名申請者背景分布：</strong>' +
      tagsHtml +
      "</div>" +
      "</div>"
    );
  }

  function applyHomeSelection(homeId, agreements, networkHeatMap) {
    if (!agreements || !agreements[homeId]) return;
    var row = agreements[homeId];

    var card = document.getElementById("selected-home-rule-card");
    if (card) card.setAttribute("data-selected-home", row.home_id);

    var admittedForm = document.getElementById("cs-admitted-connect-form");
    if (admittedForm) admittedForm.setAttribute("data-selected-home", row.home_id);

    setText("cs-home-badge", row.home_school_name);
    setText("cs-availability-label", row.availability_label);
    setText("cs-quota-summary", row.quota_summary);
    setText("cs-language-summary", row.language_requirement_summary);
    setText("cs-online-deadline", row.internal_online_deadline);
    setText("cs-paper-deadline", row.internal_paper_deadline);
    setText("cs-study-plan-limit", row.study_plan_limit);
    setText("cs-deadline-checked-at", "最後查核日期：" + row.deadline_last_checked_at);
    setText("cs-deadline-checked-inline", row.deadline_last_checked_at);

    var eligEl = document.getElementById("cs-eligibility-summary");
    if (eligEl) {
      eligEl.textContent = row.eligibility_summary || "";
      if (row.degree_levels) {
        var br1 = document.createElement("br");
        var sm1 = document.createElement("small");
        sm1.textContent = "學制：" + row.degree_levels;
        eligEl.appendChild(br1);
        eligEl.appendChild(sm1);
      }
      if (row.colleges) {
        var br2 = document.createElement("br");
        var sm2 = document.createElement("small");
        sm2.textContent = "學院：" + row.colleges;
        eligEl.appendChild(br2);
        eligEl.appendChild(sm2);
      }
    }

    var partnerLink = document.getElementById("cs-partner-source-link");
    if (partnerLink) {
      partnerLink.setAttribute("href", row.partner_source_url || row.deadline_source_url);
    }
    var deadlineLink = document.getElementById("cs-deadline-source-link");
    if (deadlineLink) {
      deadlineLink.setAttribute("href", row.deadline_source_url);
    }
    var icsBtn = document.getElementById("cs-btn-download-ics");
    if (icsBtn) {
      icsBtn.setAttribute("href", "/calendar/school-window.ics?school=" + encodeURIComponent(row.home_id));
    }

    var selectEl = document.getElementById("partner-home-switcher");
    if (selectEl && selectEl.value !== row.home_id) {
      selectEl.value = row.home_id;
    }

    var pills = document.querySelectorAll(".cs-home-pill[data-home-switch]");
    for (var i = 0; i < pills.length; i++) {
      var pill = pills[i];
      if (pill.getAttribute("data-home-switch") === row.home_id) {
        pill.classList.add("is-active");
      } else {
        pill.classList.remove("is-active");
      }
    }

    if (networkHeatMap && networkHeatMap[homeId]) {
      var entry = networkHeatMap[homeId];
      var netWrap = document.getElementById("preference-heat");
      if (netWrap && entry.status && entry.heat) {
        netWrap.setAttribute("data-school-stage", entry.status.stage);
        setText(
          "cs-network-effect-title",
          entry.status.short_name + " × " + entry.heat.partner_name_zh + "：站內志願熱度與單人備審工具"
        );
        var copyBtn = document.getElementById("cs-btn-copy-viral-heat");
        if (copyBtn) copyBtn.setAttribute("data-share-text", entry.heat.viral_share_text || "");
        var oldBox = document.getElementById("cs-heat-state-box");
        if (oldBox) {
          oldBox.outerHTML = renderNetworkHeatStateBox(entry);
        }
      }
    }
  }

  function recordConversionIntent(actionType, partnerSchool, partnerCountry, homeId) {
    try {
      var payload = {
        action: actionType,
        partner_school: partnerSchool || "",
        partner_country: partnerCountry || "",
        home_id: homeId || "",
        saved_at: new Date().toISOString(),
      };
      window.localStorage.setItem("uniway_pending_partner_intent", JSON.stringify(payload));
    } catch (_err) {
      // Ignore storage quota errors in private browsing
    }
  }

  function showFeedback(elId, message) {
    var el = document.getElementById(elId);
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var agreements = parseJsonScript("cs-home-agreements-data");
    var networkHeatMap = parseJsonScript("cs-home-network-heat-data") || {};
    if (!agreements) return;

    var selectEl = document.getElementById("partner-home-switcher");
    if (selectEl) {
      selectEl.addEventListener("change", function () {
        var nextHome = selectEl.value;
        applyHomeSelection(nextHome, agreements, networkHeatMap);
        if (window.history && window.history.replaceState) {
          var url = new URL(window.location.href);
          url.searchParams.set("home", nextHome);
          window.history.replaceState({}, "", url.toString());
        }
      });
    }

    var pills = document.querySelectorAll(".cs-home-pill[data-home-switch]");
    for (var i = 0; i < pills.length; i++) {
      pills[i].addEventListener("click", function (ev) {
        var nextHome = this.getAttribute("data-home-switch");
        if (!nextHome || !agreements[nextHome]) return;
        ev.preventDefault();
        applyHomeSelection(nextHome, agreements, networkHeatMap);
        if (window.history && window.history.replaceState) {
          var url = new URL(window.location.href);
          url.searchParams.set("home", nextHome);
          window.history.replaceState({}, "", url.toString());
        }
      });
    }

    var compareBtn = document.getElementById("cs-btn-save-compare");
    if (compareBtn) {
      compareBtn.addEventListener("click", function () {
        var card = document.getElementById("selected-home-rule-card");
        var homeId = card ? card.getAttribute("data-selected-home") : "";
        recordConversionIntent(
          "save_compare",
          compareBtn.getAttribute("data-partner-school"),
          compareBtn.getAttribute("data-partner-country"),
          homeId
        );
      });
    }

    var draftBtn = document.getElementById("cs-btn-save-draft");
    if (draftBtn) {
      draftBtn.addEventListener("click", function () {
        var card = document.getElementById("selected-home-rule-card");
        var homeId = card ? card.getAttribute("data-selected-home") : "";
        recordConversionIntent(
          "save_study_plan_draft",
          draftBtn.getAttribute("data-partner-school"),
          "",
          homeId
        );
      });
    }

    var joinHeatBtn = document.getElementById("cs-btn-join-preference-heat");
    if (joinHeatBtn) {
      joinHeatBtn.addEventListener("click", function () {
        var card = document.getElementById("selected-home-rule-card");
        var homeId = card ? card.getAttribute("data-selected-home") : "ntu";
        var partnerName = joinHeatBtn.getAttribute("data-partner-name") || "";
        fetch("/network-effects/preference-signal", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            home_school: homeId,
            first_choice_partner: partnerName,
            college_or_major: "跨院系申請者",
            language_score_tag: "語檢達標",
          }),
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (updatedStatus) {
            if (updatedStatus && updatedStatus.school_id) {
              showFeedback(
                "cs-preference-heat-feedback",
                "✅ 已匿名計入 " +
                  updatedStatus.short_name +
                  " 志願統計（目前同校累積 " +
                  updatedStatus.active_plan_count +
                  " 份申請計畫）！"
              );
            }
          })
          .catch(function () {
            showFeedback("cs-preference-heat-feedback", "已記錄你的志願偏好於本機瀏覽器。");
          });
      });
    }

    var copyViralBtn = document.getElementById("cs-btn-copy-viral-heat");
    if (copyViralBtn) {
      copyViralBtn.addEventListener("click", function () {
        var text = copyViralBtn.getAttribute("data-share-text") || "";
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text);
        }
        showFeedback("cs-preference-heat-feedback", "📣 已複製最後一週搓湯圓轉發文案！可直接貼上 Dcard 校板或系級群組。");
      });
    }

    var copyDcardAdmittedBtn = document.getElementById("cs-btn-copy-dcard-admitted-post");
    if (copyDcardAdmittedBtn) {
      copyDcardAdmittedBtn.addEventListener("click", function () {
        var text = copyDcardAdmittedBtn.getAttribute("data-dcard-template") || "";
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text);
        }
        showFeedback("cs-admitted-connect-feedback", "📋 已複製 Dcard 留學板放榜跨校認親貼文模板！");
      });
    }

    var admittedForm = document.getElementById("cs-admitted-connect-form");
    if (admittedForm) {
      admittedForm.addEventListener("submit", function (ev) {
        ev.preventDefault();
        var homeId = admittedForm.getAttribute("data-selected-home") || "ntu";
        var country = admittedForm.getAttribute("data-country") || "";
        var institution = admittedForm.getAttribute("data-institution") || "";
        var termEl = document.getElementById("cs-admitted-term");
        var aliasEl = document.getElementById("cs-admitted-alias");
        var majorEl = document.getElementById("cs-admitted-major");
        var tagsEl = document.getElementById("cs-admitted-tags");
        var introEl = document.getElementById("cs-admitted-intro");
        var tagsList = ((tagsEl && tagsEl.value) || "選課討論")
          .split(/[,，、]/)
          .map(function (s) {
            return s.trim();
          })
          .filter(Boolean);

        fetch("/network-effects/admitted-connect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            home_school: homeId,
            country: country,
            institution: institution,
            exchange_term: (termEl && termEl.value) || "115-1（2026 秋季班）",
            display_alias: (aliasEl && aliasEl.value) || "匿名錄取生",
            major_or_college: (majorEl && majorEl.value) || "跨院系",
            looking_for_tags: tagsList.length ? tagsList : ["選課討論"],
            intro_note_zh: (introEl && introEl.value) || "歡迎同屆跨校錄取生一起連線討論行前準備！",
          }),
        })
          .then(function (r) {
            if (!r.ok) {
              return r.json().then(function (err) {
                throw new Error((err && err.detail) || "登記失敗");
              });
            }
            return r.json();
          })
          .then(function (hub) {
            var grid = document.getElementById("cs-admitted-connect-grid");
            if (grid && hub && Array.isArray(hub.connections)) {
              grid.innerHTML = hub.connections
                .map(function (c) {
                  var tHtml = (c.looking_for_tags || [])
                    .map(function (t) {
                      return '<span class="cs-looking-tag">#' + escapeHtml(t) + "</span>";
                    })
                    .join("");
                  return (
                    '<article class="cs-admitted-card" data-connection-id="' +
                    escapeHtml(c.connection_id) +
                    '">' +
                    '<div class="cs-admitted-card-head">' +
                    '<span class="cs-admitted-home-badge">' +
                    escapeHtml(c.home_short_name) +
                    "</span>" +
                    "<strong>" +
                    escapeHtml(c.display_alias) +
                    "</strong>" +
                    '<span class="cs-admitted-term">' +
                    escapeHtml(c.exchange_term) +
                    "</span>" +
                    "</div>" +
                    '<p class="cs-admitted-major">主修／學院：' +
                    escapeHtml(c.major_or_college) +
                    "</p>" +
                    '<div class="cs-admitted-tags">' +
                    tHtml +
                    "</div>" +
                    '<p class="cs-admitted-intro">' +
                    escapeHtml(c.intro_note_zh) +
                    "</p>" +
                    "</article>"
                  );
                })
                .join("");
            }
            showFeedback("cs-admitted-connect-feedback", "🎉 已成功加入本屆跨校錄取生連線！");
            if (introEl) introEl.value = "";
          })
          .catch(function (err) {
            showFeedback("cs-admitted-connect-feedback", "⚠️ " + (err.message || "請確認未包含私人聯絡方式"));
          });
      });
    }
  });
})();

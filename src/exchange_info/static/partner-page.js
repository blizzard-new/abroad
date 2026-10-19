(function () {
  "use strict";

  function parseAgreements() {
    var node = document.getElementById("cs-home-agreements-data");
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

  function applyHomeSelection(homeId, agreements) {
    if (!agreements || !agreements[homeId]) return;
    var row = agreements[homeId];

    var card = document.getElementById("selected-home-rule-card");
    if (card) card.setAttribute("data-selected-home", row.home_id);

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

  document.addEventListener("DOMContentLoaded", function () {
    var agreements = parseAgreements();
    if (!agreements) return;

    var selectEl = document.getElementById("partner-home-switcher");
    if (selectEl) {
      selectEl.addEventListener("change", function () {
        var nextHome = selectEl.value;
        applyHomeSelection(nextHome, agreements);
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
        applyHomeSelection(nextHome, agreements);
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
  });
})();

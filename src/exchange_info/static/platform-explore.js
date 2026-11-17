/* Explore schools (#partners): sort tabs, program/college/department strip, prominent criteria bar, facet panel, search tiles and compare tray.
   app.js renders the grid; it calls UniWayExplore.render() after every partner render. */
window.UniWayExplore = (() => {
  "use strict";
  const SORTS = [
    { id: "match", label: "最符合條件" },
    { id: "deadline", label: "截止最近" },
    { id: "quota", label: "名額最多" },
  ];
  const CGU_PROGRAM_TABS = [
    { id: "", label: "全部計畫" },
    { id: "exchange", label: "交換學生" },
    { id: "dual_degree", label: "雙學位" },
  ];
  const PRIMARY_PROGRAM_DEFS = [
    { id: "exchange", label: "交換學生" },
    { id: "dual_degree", label: "雙學位" },
    { id: "short_term", label: "短期研修" },
    { id: "internship", label: "海外實習" },
    { id: "fee_paying", label: "自費研修" },
  ];
  const LANG_GROUP_DEFS = [
    { id: "lang_en", label: "英語組" },
    { id: "lang_ja", label: "日語組" },
    { id: "lang_zh", label: "中文組" },
    { id: "lang_other", label: "其他語組" },
  ];
  const UNIT_COLLEGE_ALIASES = {
    "外語學院": ["外國語文學院"],
    "外國語文學院": ["外語學院"],
    "海洋科學學院": ["海洋科學院"],
    "海洋科學院": ["海洋科學學院"],
    "醫學工程學院": ["生醫工程學院"],
    "生醫工程學院": ["醫學工程學院"],
  };
  const CRITERIA_TEST_LABELS = {
    ielts: "IELTS",
    toefl: "TOEFL iBT",
    toeic: "TOEIC",
    jlpt: "日檢 N",
    topik: "TOPIK ",
    duolingo: "Duolingo",
  };
  const GRADE_SCALE_META = {
    "100": { max: "100", step: "0.01", placeholder: "例如 78" },
    "4": { max: "4", step: "0.01", placeholder: "例如 3.4" },
    "4.3": { max: "4.3", step: "0.01", placeholder: "例如 3.6" },
    "5": { max: "5", step: "0.01", placeholder: "例如 4.2" },
  };
  const COUNTRY_FACETS = 8;
  const narrow = window.matchMedia("(max-width: 900px)");
  let scheduled = 0, drawerSynced = false;

  const root = () => document.querySelector("#partners");
  const shortDate = (date) => `${date.getMonth() + 1}/${String(date.getDate()).padStart(2, "0")}`;

  function sortMetrics(list) {
    const profile = Boolean(state.eligibilityProfile);
    const fit = profile ? list.filter((item) => partnerMatch(item).tone === "strong").length : 0;
    const openList = list.filter((item) => !partnerAvailabilityMeta(item).blocked);
    const quotas = openList.map(partnerQuotaNumber).filter((value) => value !== null);
    let deadline = "依官方公告";
    try {
      const partnerDates = openList.map(partnerNextDeadline).filter(Boolean).sort((a, b) => a - b);
      const official = upcomingDeadlines(1)[0];
      if (activeHomeSchool() === "長庚大學" && partnerDates.length) {
        deadline = `校內 12/21 · 合作校 ${partnerDates.length} 間有時程`;
      } else if (official && partnerDates.length) {
        deadline = `校內 ${shortDate(official.date)} · 合作校 ${partnerDates.length} 間有時程`;
      } else if (partnerDates.length) {
        deadline = `最近 ${shortDate(partnerDates[0])} · ${partnerDates.length} 間有時程`;
      } else if (official) {
        deadline = `最近 ${shortDate(official.date)} ${official.scope}`;
      }
    } catch (_) { /* the tab then says the deadline follows the official notice */ }
    const picked = UniWayDiscovery.hasCriteria(discoveryCriteria);
    const fits = picked ? list.filter((item) => UniWayDiscovery.assess(item, discoveryCriteria).matched).length : 0;
    return {
      match: picked ? `${fits} 間符合所選條件` : profile ? `${fit} 間已知條件相符` : "填寫條件後可比對",
      deadline,
      quota: quotas.length ? `最多 ${Math.max(...quotas)} 名 · ${quotas.length} 間已列` : "依官方公告",
    };
  }

  function resolveAcademicUnits(home = activeHomeSchool(), colleges = homeCollegeOptions()) {
    const rawUnits = window.UniWayAcademicUnits?.[home]?.colleges || {};
    const unitsByCollege = {};
    const deptToCollege = new Map();
    const usedRawKeys = new Set();
    colleges.forEach((col) => {
      let matchedKey = Object.prototype.hasOwnProperty.call(rawUnits, col) ? col : "";
      if (!matchedKey) {
        matchedKey = (UNIT_COLLEGE_ALIASES[col] || []).find((alias) => Object.prototype.hasOwnProperty.call(rawUnits, alias)) || "";
      }
      if (matchedKey) {
        usedRawKeys.add(matchedKey);
        const depts = Array.isArray(rawUnits[matchedKey]) ? rawUnits[matchedKey].filter(Boolean) : [];
        if (depts.length) {
          unitsByCollege[col] = depts;
          depts.forEach((dept) => deptToCollege.set(dept, col));
        }
      }
    });
    Object.entries(rawUnits).forEach(([rawCol, rawDepts]) => {
      if (usedRawKeys.has(rawCol)) return;
      const canonical = colleges.includes(rawCol)
        ? rawCol
        : (UNIT_COLLEGE_ALIASES[rawCol] || []).find((alias) => colleges.includes(alias)) || "";
      if (!canonical) return;
      const depts = Array.isArray(rawDepts) ? rawDepts.filter(Boolean) : [];
      if (!depts.length) return;
      unitsByCollege[canonical] = [...(unitsByCollege[canonical] || []), ...depts];
      depts.forEach((dept) => deptToCollege.set(dept, canonical));
    });
    const totalDepts = Object.values(unitsByCollege).reduce((sum, depts) => sum + depts.length, 0);
    return { unitsByCollege, deptToCollege, totalDepts };
  }

  function computeProgramTabs(allPartners = state.dashboard?.partner_universities || []) {
    const home = activeHomeSchool();
    if (home === "長庚大學") return CGU_PROGRAM_TABS;
    const all = Array.isArray(allPartners) ? allPartners : [];
    if (!all.length) return [];
    const total = all.length;
    const countKind = (id) => all.filter((item) => cguProgramKindMatches(item, id)).length;

    const primaryCounts = PRIMARY_PROGRAM_DEFS.map((def) => ({ ...def, count: countKind(def.id) }));
    const nonEmptyPrimary = primaryCounts.filter((d) => d.count > 0);
    if (nonEmptyPrimary.length >= 2 && nonEmptyPrimary.some((d) => d.count < total)) {
      const ordered = [
        ...nonEmptyPrimary.filter((d) => d.id === "exchange"),
        ...nonEmptyPrimary.filter((d) => d.id !== "exchange").sort((a, b) => b.count - a.count),
      ].slice(0, 3);
      return [{ id: "", label: "全部計畫" }, ...ordered.map(({ id, label }) => ({ id, label }))];
    }

    const univCount = countKind("level_univ");
    const deptCount = countKind("level_dept");
    if (univCount > 0 && deptCount > 0 && univCount < total && deptCount < total) {
      return [
        { id: "", label: "全部計畫" },
        { id: "level_univ", label: "校級交換" },
        { id: "level_dept", label: "院系級" },
      ];
    }

    const langGroups = LANG_GROUP_DEFS
      .map((def) => ({ ...def, count: countKind(def.id) }))
      .filter((d) => d.count > 0 && d.count < total);
    if (langGroups.length >= 2) {
      const pickedLangs = langGroups.sort((a, b) => b.count - a.count).slice(0, 3);
      return [{ id: "", label: "全部計畫" }, ...pickedLangs.map(({ id, label }) => ({ id, label }))];
    }

    const intlCount = countKind("region_intl");
    const csCount = countKind("region_cross_strait");
    if (intlCount > 0 && csCount > 0 && intlCount < total && csCount < total) {
      return [
        { id: "", label: "全部計畫" },
        { id: "region_intl", label: "國際交換" },
        { id: "region_cross_strait", label: "兩岸港澳" },
      ];
    }

    const openCount = countKind("status_open");
    const refCount = countKind("status_ref");
    if (openCount > 0 && refCount > 0 && openCount < total && refCount < total) {
      return [
        { id: "", label: "全部計畫" },
        { id: "status_open", label: "本期開放" },
        { id: "status_ref", label: "備查待確認" },
      ];
    }

    return [];
  }

  function renderCguProgramTabs(host, tabs) {
    const bar = host.querySelector("#cgu-program-tabs");
    if (!bar) return;
    if (!tabs.length) {
      if (state.cguProgramTab) state.cguProgramTab = "";
      bar.hidden = true;
      bar.innerHTML = "";
      return;
    }
    if (state.cguProgramTab && !tabs.some((t) => t.id === state.cguProgramTab)) {
      state.cguProgramTab = "";
    }
    bar.hidden = false;
    const pool = filteredPartners({ ignore: "program", sort: false });
    const countFor = (tabId) => (tabId ? pool.filter((item) => cguProgramKindMatches(item, tabId)).length : pool.length);
    const buttonsHtml = tabs.map(({ id, label }) => {
      const active = (state.cguProgramTab || "") === id;
      const count = countFor(id);
      const isDual = id === "dual_degree";
      return `<button type="button" role="tab" aria-selected="${active}" class="cgu-program-tab${active ? " on" : ""}${isDual ? " is-dual" : ""}" data-cgu-program="${escapeHtml(id)}"><strong>${escapeHtml(label)}</strong><span>${count} 所</span></button>`;
    }).join("");
    let note = "";
    if (activeHomeSchool() === "長庚大學") {
      note = state.cguProgramTab === "dual_degree"
        ? "長庚雙學位計畫：修業年限、學費與學位授予規定與交換不同（多為醫／工／管院限定）"
        : state.cguProgramTab === "exchange"
          ? "交換學生計畫（含國際處中央名單與管理學院院級參考）"
          : "雙學位與交換分開檢視：點選「雙學位」單獨查看 14 個雙聯計畫";
    } else {
      const activeObj = tabs.find((t) => t.id === (state.cguProgramTab || ""));
      note = activeObj && activeObj.id ? `目前檢視：${activeObj.label}` : "依計畫類別快速切換檢視";
    }
    bar.innerHTML = `<div class="cgu-program-tabs-row">${buttonsHtml}</div><small class="cgu-program-tabs-note">${escapeHtml(note)}</small>`;
  }

  function shortPartnerAnchorLabel(name) {
    const text = String(name || "").trim();
    const zhPrefix = text.match(/^([\u4e00-\u9fff·・A-Za-z0-9]{2,14}?)(?:\s+[A-Za-z(])/);
    if (zhPrefix) return zhPrefix[1];
    return text.length > 16 ? `${text.slice(0, 15)}…` : text;
  }

  function renderCguMgmtNotice(host) {
    const notice = host.querySelector("#cgu-mgmt-channel-notice");
    if (!notice) return;
    const home = activeHomeSchool();
    if (home === "長庚大學") {
      const query = String(state.partnerQuery || "");
      const show = state.college === "管理學院"
        || (Boolean(state.partnerFit) && state.eligibilityProfile?.college === "管理學院")
        || state.availability === "departmental_reference"
        || /管理學院|商學|iae|aix|marseille|艾克斯|馬賽|rennes|雷恩/i.test(query);
      notice.hidden = !show;
      if (!show) {
        notice.innerHTML = "";
        return;
      }
      notice.innerHTML = `
        <span class="cgu-mgmt-badge">院級管道提示</span>
        <div class="cgu-mgmt-copy">
          <strong>管理學院另有院級交換，請洽院國際辦公室</strong>
          <span>法國 IAE 艾克斯馬賽大學管理研究所、雷恩商學院共 2 所屬於管理學院自有管道，不在國際事務處中央當期名單上。</span>
        </div>
        <div class="cgu-mgmt-links">
          <a href="#school=${encodeURIComponent("法國艾克斯馬賽大學管理研究所 IAE Aix-Marseille Graduate School of Management")}">IAE 艾克斯馬賽</a>
          <a href="#school=${encodeURIComponent("雷恩商學院 Rennes School of Business")}">雷恩商學院</a>
        </div>`;
      return;
    }

    const all = state.dashboard?.partner_universities || [];
    const deptChannelPartners = all.filter((item) => item.availability_status === "departmental_reference"
      || /院級|院系級|系級|系所級|\bOIP\b/i.test(item.program_type || ""));
    if (!deptChannelPartners.length) {
      notice.hidden = true;
      notice.innerHTML = "";
      return;
    }
    const scopedByCollege = state.college
      ? deptChannelPartners.filter((item) => !academicScopeNeedsConfirmation(item, "colleges") && collegeMatches(item.colleges, state.college))
      : [];
    const show = state.cguProgramTab === "level_dept"
      || state.availability === "departmental_reference"
      || scopedByCollege.length > 0;
    notice.hidden = !show;
    if (!show) {
      notice.innerHTML = "";
      return;
    }
    const displayPartners = scopedByCollege.length ? scopedByCollege : deptChannelPartners;
    const heading = state.college && scopedByCollege.length
      ? `${state.college}另有 ${scopedByCollege.length} 所院系級交換管道，請依院系公告辦理`
      : `本名單收錄 ${deptChannelPartners.length} 所院系級交換管道，請洽所屬院系辦公室確認`;
    const linksHtml = displayPartners.slice(0, 3)
      .map((item) => `<a href="#school=${encodeURIComponent(item.school_name)}">${escapeHtml(shortPartnerAnchorLabel(item.school_name))}</a>`)
      .join("");
    notice.innerHTML = `
      <span class="cgu-mgmt-badge">院級管道提示</span>
      <div class="cgu-mgmt-copy">
        <strong>${escapeHtml(heading)}</strong>
        <span>院系級交換由各學院或系所獨立受理甄選與提名，申請期限與應備文件請以該院系公告為準。</span>
      </div>
      ${linksHtml ? `<div class="cgu-mgmt-links">${linksHtml}</div>` : ""}`;
  }

  function partitionCollegesForRow(colleges, progTabCount, hasDepts) {
    const totalChars = colleges.reduce((sum, name) => sum + name.length, 0);
    const allFitInline = (colleges.length <= 4 && totalChars <= 18 && progTabCount <= 3)
      || (colleges.length <= 5 && totalChars <= 20 && (progTabCount === 0 || !hasDepts));
    if (allFitInline) {
      return { inlineColleges: colleges, moreColleges: [] };
    }
    const maxInlineCount = progTabCount >= 4 ? 2 : 3;
    const maxInlineChars = progTabCount >= 4 ? 11 : 15;
    const inlineColleges = [];
    let usedChars = 0;
    for (const col of colleges) {
      if (inlineColleges.length >= maxInlineCount) break;
      if (inlineColleges.length > 0 && usedChars + col.length > maxInlineChars) break;
      inlineColleges.push(col);
      usedChars += col.length;
    }
    const moreColleges = colleges.slice(inlineColleges.length);
    if (moreColleges.length === 1 && usedChars + moreColleges[0].length <= (progTabCount >= 4 ? 14 : 18)) {
      return { inlineColleges: colleges, moreColleges: [] };
    }
    return { inlineColleges, moreColleges };
  }

  function renderCguCollegeBar(host, list, progTabs) {
    const bar = host.querySelector("#cgu-college-quick-bar");
    if (!bar) return;
    const home = activeHomeSchool();
    const colleges = homeCollegeOptions();
    if (!colleges.length) {
      bar.hidden = true;
      bar.innerHTML = "";
      return;
    }
    bar.hidden = false;
    const { unitsByCollege, deptToCollege, totalDepts } = resolveAcademicUnits(home, colleges);
    if (state.cguDepartment) {
      const mappedCol = deptToCollege.get(state.cguDepartment);
      if (!mappedCol || (state.college && mappedCol !== state.college)) {
        state.cguDepartment = "";
      }
    }

    const pool = filteredPartners({ ignore: "college", sort: false });
    const countFor = (collegeName) => pool.filter((item) => cguOptionScopeMatches(item, collegeName, "", state.cguProgramTab)).length;
    const { inlineColleges, moreColleges } = partitionCollegesForRow(colleges, progTabs.length, totalDepts > 0);

    const allActive = !state.college && !state.cguDepartment;
    const resetHtml = `<button type="button" class="cgu-college-btn is-all${allActive ? " on" : ""}" data-cgu-college="" aria-pressed="${allActive}"><strong>全部學院</strong><span>${pool.length} 所</span></button>`;
    const inlineButtonsHtml = inlineColleges.map((collegeName) => {
      const active = state.college === collegeName;
      const count = countFor(collegeName);
      return `<button type="button" class="cgu-college-btn${active ? " on" : ""}" data-cgu-college="${escapeHtml(collegeName)}" aria-pressed="${active}"><strong>${escapeHtml(collegeName)}</strong><span>${count} 所</span></button>`;
    }).join("");

    let moreCollegeHtml = "";
    if (moreColleges.length) {
      const inMore = Boolean(state.college && moreColleges.includes(state.college));
      const moreOpts = moreColleges.map((col) => `<option value="${escapeHtml(col)}"${state.college === col ? " selected" : ""}>${escapeHtml(col)}</option>`).join("");
      moreCollegeHtml = `<label class="cgu-more-college-wrap${inMore ? " has-more-college" : ""}" for="cgu-more-college-select"><span>更多學院</span><select id="cgu-more-college-select" aria-label="更多學院篩選"><option value="">更多學院（${moreColleges.length}）</option>${moreOpts}</select></label>`;
    }

    let deptSelectHtml = "";
    if (totalDepts > 0) {
      const collegeKeys = state.college && unitsByCollege[state.college] ? [state.college] : Object.keys(unitsByCollege);
      const optgroups = collegeKeys.map((col) => {
        const opts = (unitsByCollege[col] || []).map((dept) => `<option value="${escapeHtml(dept)}"${state.cguDepartment === dept ? " selected" : ""}>${escapeHtml(dept)}</option>`).join("");
        return `<optgroup label="${escapeHtml(col)}">${opts}</optgroup>`;
      }).join("");
      const shortSchool = home === "長庚大學" ? "長庚" : (activeUniversityProfile()?.short_name || home);
      const hasDept = Boolean(state.cguDepartment);
      deptSelectHtml = `<label class="cgu-dept-inline-select${hasDept ? " has-dept" : ""}" for="cgu-partner-dept-select"><span>系所</span><select id="cgu-partner-dept-select" aria-label="依${escapeHtml(shortSchool)} ${totalDepts} 系所篩選"><option value="">${state.college ? `全部${escapeHtml(state.college)}系所` : `全部 ${totalDepts} 系所`}</option>${optgroups}</select></label>`;
    }

    const shortLabel = home === "長庚大學" ? "長庚學院" : `${activeUniversityProfile()?.short_name || home}學院`;
    const liveHtml = state.college && state.cguDepartment
      ? `<b>${escapeHtml(state.college)}・${escapeHtml(state.cguDepartment)}</b>可申請：共 <b>${list.length} 所</b>`
      : state.college
        ? `<b>${escapeHtml(state.college)}</b>可申請：共 <b>${list.length} 所</b>`
        : `點選學院直接顯示可申請校數（共 <b>${pool.length} 所</b>）`;
    bar.innerHTML = `<div class="cgu-college-bar-main"><span class="cgu-college-bar-label"><i data-lucide="graduation-cap" aria-hidden="true"></i>${escapeHtml(shortLabel)}</span><div class="cgu-college-buttons" role="group" aria-label="依${escapeHtml(shortLabel)}篩選">${resetHtml}${inlineButtonsHtml}</div>${moreCollegeHtml}${deptSelectHtml}</div><p id="cgu-college-live-count" class="cgu-college-live" role="status">${liveHtml}</p>`;
  }

  function syncTermOptionLabels() {
    const isCgu = Boolean(window.cguDemoStorageIsolated);
    const fallLabel = isCgu ? "2027 秋季（116-1）" : "秋季／上學期";
    const springLabel = isCgu ? "2027 春季（115-2）" : "春季／下學期";
    document.querySelectorAll('#partner-term-tile, #discovery-criteria-form select[name="term"]').forEach((sel) => {
      let changed = false;
      const fallOpt = sel.querySelector('option[value="fall"]');
      const springOpt = sel.querySelector('option[value="spring"]');
      if (fallOpt && fallOpt.textContent !== fallLabel) { fallOpt.textContent = fallLabel; changed = true; }
      if (springOpt && springOpt.textContent !== springLabel) { springOpt.textContent = springLabel; changed = true; }
      if (changed) sel.uniwayGlide?.sync?.();
    });
  }

  function syncCriteriaGradeScale(clearOutOfRange = false) {
    const form = document.querySelector("#discovery-criteria-form");
    if (!form) return;
    const scaleSel = form.querySelector('select[name="scale"]');
    const gradeInp = form.querySelector('input[name="grade"]');
    if (!scaleSel || !gradeInp) return;
    const meta = GRADE_SCALE_META[scaleSel.value] || GRADE_SCALE_META["100"];
    if (gradeInp.max !== meta.max) gradeInp.max = meta.max;
    if (gradeInp.step !== meta.step) gradeInp.step = meta.step;
    if (gradeInp.placeholder !== meta.placeholder) gradeInp.placeholder = meta.placeholder;
    if (clearOutOfRange && gradeInp.value !== "" && Number(gradeInp.value) > Number(meta.max)) {
      gradeInp.value = "";
    }
  }

  function syncCriteriaBanner() {
    const details = document.querySelector("#discovery-criteria");
    if (!details) return;
    const summarySpan = document.querySelector("#cgu-criteria-summary");
    const ctaLabel = document.querySelector("#cgu-criteria-cta-label");
    const c = (typeof discoveryCriteria === "object" && discoveryCriteria) ? discoveryCriteria : {};
    const active = Boolean(window.UniWayDiscovery?.hasCriteria?.(c))
      || Boolean((document.querySelector("#discovery-criteria-count")?.textContent || "").trim());
    const isCgu = Boolean(window.cguDemoStorageIsolated);

    const parts = [];
    if (active) {
      if (c.test || c.score) {
        const tLabel = CRITERIA_TEST_LABELS[c.test] || (c.test ? String(c.test).toUpperCase() : "檢定");
        if (c.test === "jlpt" && c.score) parts.push(`JLPT N${c.score}`);
        else if (c.test === "topik" && c.score) parts.push(`TOPIK ${c.score} 級`);
        else parts.push([tLabel.trim(), c.score].filter(Boolean).join(" "));
      }
      if (c.grade) {
        const prefix = (!c.scale || c.scale === "100") ? "平均" : "GPA";
        parts.push(`${prefix} ${c.grade}`);
      }
      if (c.degree === "undergraduate") parts.push("大學部");
      else if (c.degree === "graduate") parts.push("研究所");
      if (c.term === "fall") parts.push(isCgu ? "2027 秋季" : "秋季／上學期");
      else if (c.term === "spring") parts.push(isCgu ? "2027 春季" : "春季／下學期");
    }

    const nextSummary = parts.length ? parts.join(" · ") : "檢定成績 · 學業成績 · 學制";
    const nextCta = details.open ? "收合條件" : active ? "修改條件" : "設定條件";

    if (details.classList.contains("has-active-criteria") !== active) {
      details.classList.toggle("has-active-criteria", active);
    }
    if (summarySpan && summarySpan.textContent !== nextSummary) {
      summarySpan.textContent = nextSummary;
    }
    if (ctaLabel && ctaLabel.textContent !== nextCta) {
      ctaLabel.textContent = nextCta;
    }
  }

  function syncPartnersRecentsPopover() {
    const details = document.querySelector("#partners .cgu-explore-head-actions [data-discovery-recents]");
    if (!details || !details.open || details.hidden) return;
    const vw = document.documentElement.clientWidth || window.innerWidth || 1024;
    const menuW = Math.min(320, Math.max(200, vw - 32));
    const rect = details.getBoundingClientRect();
    const idealLeft = rect.right - menuW;
    const clampedLeft = Math.min(Math.max(16, idealLeft), Math.max(16, vw - menuW - 16));
    details.style.setProperty("--cgu-recents-left", `${Math.round(clampedLeft - rect.left)}px`);
    details.style.setProperty("--cgu-recents-right", "auto");
  }

  function renderSortTabs(host, list) {
    const metrics = sortMetrics(list);
    host.querySelector("#partner-sort-tabs").innerHTML = SORTS.map(({ id, label }) => {
      const active = state.partnerSort === id;
      return `<button type="button" role="tab" aria-selected="${active}" data-partner-sort="${id}" class="${active ? "on" : ""}"><strong>${label}</strong><span>${escapeHtml(metrics[id])}</span></button>`;
    }).join("");
  }

  function checkRow(group, value, label, count, checked) {
    return `<label class="pr-check"><input type="checkbox" data-pr-facet="${group}" value="${escapeHtml(value)}"${checked ? " checked" : ""} /><span class="pr-check-box" aria-hidden="true"><i data-lucide="check"></i></span><span>${escapeHtml(label)}</span><small>${count}</small></label>`;
  }

  function renderFacets(host) {
    const focus = document.activeElement?.matches?.("[data-pr-facet]") ? [document.activeElement.dataset.prFacet, document.activeElement.value] : null;
    const groups = [];
    const byCountry = new Map();
    filteredPartners({ ignore: "country", sort: false }).forEach((item) => byCountry.set(item.country || "未標示國家", (byCountry.get(item.country || "未標示國家") || 0) + 1));
    let countries = [...byCountry].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "zh-Hant")).slice(0, COUNTRY_FACETS);
    if (state.country && !countries.some(([name]) => name === state.country)) countries = [[state.country, byCountry.get(state.country) || 0], ...countries];
    if (countries.length) groups.push(`<fieldset class="pr-facet"><legend>國家</legend>${countries.map(([name, count]) => checkRow("country", name, name, count, state.country === name)).join("")}</fieldset>`);

    const quotaList = filteredPartners({ ignore: "quota", sort: false });
    const twoPlus = quotaList.filter((item) => (partnerQuotaNumber(item) ?? 0) >= 2).length;
    const one = quotaList.filter((item) => partnerQuotaNumber(item) === 1).length;
    if (twoPlus || one || state.partnerQuota) {
      groups.push(`<fieldset class="pr-facet"><legend>交換名額</legend>${checkRow("quota", "2plus", "2 名以上", twoPlus, state.partnerQuota === "2plus")}${checkRow("quota", "1", "1 名", one, state.partnerQuota === "1")}</fieldset>`);
    }
    if (state.eligibilityProfile) {
      const fitList = filteredPartners({ ignore: "fit", sort: false });
      const count = (bucket) => fitList.filter((item) => partnerFitBucket(item) === bucket).length;
      groups.push(`<fieldset class="pr-facet"><legend>我的條件</legend>${checkRow("fit", "fit", "符合資格", count("fit"), state.partnerFit === "fit")}${checkRow("fit", "review", "仍須確認", count("review"), state.partnerFit === "review")}</fieldset>`);
    }
    host.querySelector("#partner-facet-groups").innerHTML = groups.join("");
    if (focus) host.querySelector(`[data-pr-facet="${focus[0]}"][value="${CSS.escape(focus[1])}"]`)?.focus({ preventScroll: true });
  }

  function appliedFilters() {
    const labels = [];
    if (state.cguProgramTab) {
      const activeTab = computeProgramTabs().find((t) => t.id === state.cguProgramTab);
      labels.push(activeTab ? activeTab.label : (state.cguProgramTab === "dual_degree" ? "雙學位" : "交換學生"));
    }
    if (state.region) labels.push(state.region);
    if (state.country) labels.push(state.country);
    if (state.college) labels.push(state.college);
    if (state.cguDepartment) labels.push(state.cguDepartment);
    if (state.degree) labels.push(state.degree);
    if (state.availability) labels.push(host_text("#availability-filter", state.availability));
    if (state.partnerQuota) labels.push(state.partnerQuota === "2plus" ? "名額 2 名以上" : "名額 1 名");
    if (state.partnerFit) labels.push(state.partnerFit === "fit" ? "符合資格" : "仍須確認");
    const picked = discoveryCriteria;
    if (UniWayDiscovery.hasCriteria(picked)) {
      if (picked.term) labels.push(`出發學期：${host_text("#partner-term-tile", picked.term)}`);
      if (picked.test) labels.push(`語言檢定：${host_text("#partner-test-tile", picked.test)}`);
      if (picked.score || picked.grade || picked.degree) labels.push("我的條件");
    }
    return labels;
  }
  function host_text(selector, value) {
    return document.querySelector(`${selector} option[value="${CSS.escape(value)}"]`)?.textContent || value;
  }

  function renderSummary(host) {
    const labels = appliedFilters();
    host.querySelector("#partner-applied").textContent = labels.length ? `已套用：${labels.join("、")}` : "";
    const count = host.querySelector("#partner-filter-count");
    count.textContent = labels.length ? `· ${labels.length}` : "";
    const context = host.querySelector("#partners-context");
    const total = state.dashboard?.partner_universities?.length;
    context.textContent = `${activeHomeSchool()}${total ? ` · ${total} 間合作校` : ""}`;
  }

  function syncTiles(host) {
    host.querySelectorAll("[data-criteria-tile]").forEach((tile) => {
      const value = discoveryCriteria[tile.dataset.criteriaTile] || "";
      if (tile.value !== value && document.activeElement !== tile) tile.value = value;
    });
  }

  // On a phone the query bar keeps only the search box; the term and language fields live in the 篩選 drawer, one tap away.
  // They are the same elements (same ids, same listeners), moved, so nothing that reads them changes.
  function placeTiles(host) {
    const bar = host.querySelector(".pr-search"), panel = host.querySelector(".pr-facets .filter-panel");
    const tiles = ["#partner-term-tile", "#partner-test-tile"].map((selector) => host.querySelector(selector)?.closest(".pr-field")).filter(Boolean);
    if (!bar || !panel || tiles.length < 2) return;
    if (narrow.matches) {
      let slot = panel.querySelector(".pr-facet-tiles");
      if (!slot) {
        slot = document.createElement("div");
        slot.className = "pr-facet-tiles";
        panel.querySelector(".pr-facets-head")?.after(slot);
      }
      if (tiles[0].parentElement !== slot) tiles.forEach((tile) => slot.append(tile));
    } else if (tiles[0].parentElement !== bar) {
      const submit = bar.querySelector("#partner-search-submit");
      tiles.forEach((tile) => bar.insertBefore(tile, submit));
    }
  }

  function syncDrawer(host) {
    const drawer = host.querySelector(".journey-filter-drawer");
    if (!drawer) return;
    // The panel is always open beside the cards; on a phone it opens from the 篩選 pill.
    if (!narrow.matches && state.partnerView !== "map") drawer.open = true;
    else if (!drawerSynced) drawer.open = false;
    drawerSynced = true;
  }

  function renderTray(host) {
    let tray = host.querySelector("#partner-compare-tray");
    if (!tray) {
      host.insertAdjacentHTML("beforeend", '<div id="partner-compare-tray" class="pr-compare-tray" hidden></div>');
      tray = host.querySelector("#partner-compare-tray");
    }
    const names = state.dashboard ? [...discoveryCompare].filter((name) => partnerByName(name)) : [];
    tray.hidden = !names.length || state.partnerView === "map";
    if (tray.hidden) return;
    const thumbs = names.slice(0, 3).map((name) => {
      const item = partnerByName(name);
      const image = schoolImageFor(item.school_name, item.country)?.local_path;
      return `<span class="pr-tray-thumb"${image ? ` style="background-image:url('${escapeHtml(image)}')"` : ""}></span>`;
    }).join("");
    const ready = names.length > 1;
    tray.innerHTML = `<span class="pr-tray-thumbs" aria-hidden="true">${thumbs}</span>
      <span class="pr-tray-text"><strong>已選 ${names.length} 間</strong><span>${escapeHtml(names.slice(0, 2).join("、"))}${names.length > 2 ? "…" : ""}</span></span>
      <button type="button" data-open-compare${ready ? "" : " disabled"}>${ready ? "並排比較" : "再選 1 間"}<i data-lucide="arrow-right" aria-hidden="true"></i></button>`;
  }

  function render() {
    scheduled = 0;
    const host = root();
    if (!host || !state.dashboard) return;
    syncTermOptionLabels();
    window.UniWayDiscoveryUI?.prefillCriteriaFormFromProfile?.();
    syncCriteriaGradeScale(false);
    syncCriteriaBanner();
    const progTabs = computeProgramTabs();
    renderCguProgramTabs(host, progTabs);
    const list = filteredPartners({ sort: false });
    renderCguCollegeBar(host, list, progTabs);
    const strip = host.querySelector("#cgu-partner-filter-strip");
    if (strip) {
      const progHidden = Boolean(host.querySelector("#cgu-program-tabs")?.hidden);
      const colHidden = Boolean(host.querySelector("#cgu-college-quick-bar")?.hidden);
      strip.hidden = progHidden && colHidden;
    }
    renderCguMgmtNotice(host);
    renderSortTabs(host, list);
    renderFacets(host);
    renderSummary(host);
    placeTiles(host);
    syncTiles(host);
    syncDrawer(host);
    renderTray(host);
    initIcons();
  }

  function schedule() {
    if (!scheduled) scheduled = window.requestAnimationFrame(render);
  }

  function refilter() {
    state.partnerLimit = partnerPageSize();
    renderPartnerFilters();
    renderPartnerTable();
  }

  document.addEventListener("click", (event) => {
    const recents = document.querySelector("#partners .cgu-explore-head-actions [data-discovery-recents]");
    if (recents?.open && !recents.contains(event.target)) recents.open = false;

    const host = root();
    if (!host || !host.contains(event.target)) return;
    if (event.target.closest("[data-partner-clear-all]")) { document.querySelector("#clear-partner-filters")?.click(); return; }
    if (event.target.closest("#discovery-clear-criteria, #clear-partner-filters")) {
      window.requestAnimationFrame(() => {
        syncCriteriaGradeScale(false);
        syncCriteriaBanner();
      });
    }
    const cguProg = event.target.closest("[data-cgu-program]");
    if (cguProg) {
      state.cguProgramTab = cguProg.dataset.cguProgram || "";
      refilter();
      return;
    }
    const cguCollege = event.target.closest("[data-cgu-college]");
    if (cguCollege) {
      const picked = cguCollege.dataset.cguCollege || "";
      state.college = picked && state.college === picked && !state.cguDepartment ? "" : picked;
      state.cguDepartment = "";
      const select = document.querySelector("#college-filter");
      if (select) select.value = state.college;
      refilter();
      return;
    }
    const tab = event.target.closest("[data-partner-sort]");
    if (tab) { state.partnerSort = tab.dataset.partnerSort; state.partnerLimit = partnerPageSize(); renderPartnerTable(); return; }
    if (event.target.closest("#partner-search-submit")) {
      state.partnerQuery = host.querySelector("#partner-search").value;
      state.partnerLimit = partnerPageSize();
      renderPartnerTable();
      host.querySelector("#partner-table")?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      return;
    }
    if (event.target.closest("[data-open-compare]")) {
      window.addEventListener("hashchange", () => window.requestAnimationFrame(() => document.querySelector("#discovery-comparison")?.scrollIntoView({ block: "start" })), { once: true });
      window.location.hash = "#favorites";
    }
  });

  document.addEventListener("change", (event) => {
    const host = root();
    if (!host || !host.contains(event.target)) return;
    if (event.target.matches('#discovery-criteria-form select[name="scale"]')) {
      syncCriteriaGradeScale(true);
      return;
    }
    const moreColSelect = event.target.closest("#cgu-more-college-select");
    if (moreColSelect) {
      state.college = moreColSelect.value || "";
      state.cguDepartment = "";
      const select = document.querySelector("#college-filter");
      if (select) select.value = state.college;
      refilter();
      return;
    }
    const deptSelect = event.target.closest("#cgu-partner-dept-select");
    if (deptSelect) {
      const dept = deptSelect.value || "";
      state.cguDepartment = dept;
      if (dept) {
        const { deptToCollege } = resolveAcademicUnits();
        const col = deptToCollege.get(dept);
        if (col) {
          state.college = col;
          const select = document.querySelector("#college-filter");
          if (select) select.value = state.college;
        }
      }
      refilter();
      return;
    }
    const facet = event.target.closest("[data-pr-facet]");
    if (facet) {
      const next = facet.checked ? facet.value : "";
      if (facet.dataset.prFacet === "country") state.country = next;
      else if (facet.dataset.prFacet === "quota") state.partnerQuota = next;
      else if (facet.dataset.prFacet === "fit") state.partnerFit = next;
      refilter();
      return;
    }
    const tile = event.target.closest("[data-criteria-tile]");
    if (tile) {
      const field = document.querySelector(`#discovery-criteria-form [name="${tile.dataset.criteriaTile}"]`);
      if (field) { field.value = tile.value; field.form.requestSubmit(); }
      return;
    }
    const pick = event.target.closest("[data-compare-pick]");
    if (pick) {
      const name = pick.dataset.comparePick;
      if (pick.checked) {
        if (discoveryCompare.size >= 3) { pick.checked = false; announce("一次比較最多 3 所", "info"); return; }
        discoveryCompareScope = discoveryKey();
        discoveryCompare.add(name);
        if (!activeSchoolSelections().has(name)) toggleFavorite(name);
        else renderFavorites();
        if (discoveryCompare.size >= 2) document.dispatchEvent(new CustomEvent("uniway:compare", {detail: {school_count: discoveryCompare.size}}));
      } else {
        discoveryCompare.delete(name);
        renderFavorites();
      }
      renderPartnerTable();
    }
  });

  document.addEventListener("submit", (event) => {
    if (event.target.id === "discovery-criteria-form") {
      window.requestAnimationFrame(syncCriteriaBanner);
    }
  });

  document.addEventListener("reset", (event) => {
    if (event.target.id === "discovery-criteria-form") {
      window.setTimeout(() => {
        syncCriteriaGradeScale(false);
        syncCriteriaBanner();
      }, 0);
    }
  });

  document.querySelector("#discovery-criteria")?.addEventListener("toggle", syncCriteriaBanner);
  document.querySelector("#partners .cgu-explore-head-actions [data-discovery-recents]")?.addEventListener("toggle", syncPartnersRecentsPopover);
  window.addEventListener("resize", syncPartnersRecentsPopover);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      const recents = document.querySelector("#partners .cgu-explore-head-actions [data-discovery-recents]");
      if (recents?.open) recents.open = false;
    }
  });

  syncCriteriaGradeScale(false);
  syncCriteriaBanner();
  narrow.addEventListener("change", () => { drawerSynced = false; schedule(); });
  return { render: schedule, refilter };
})();

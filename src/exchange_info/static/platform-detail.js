/* School detail: breadcrumb, gallery, requirement comparison and the sticky application card.
   app.js fills the tabbed panels; it calls UniWayDetail.render(item) when a school opens and whenever
   favourites, the application list or the student's conditions change. */
window.UniWayDetail = (() => {
  "use strict";
  const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];
  const GALLERY_MAX = 5;

  const formatFull = (date) => `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, "0")}/${String(date.getDate()).padStart(2, "0")}（${WEEKDAYS[date.getDay()]}）`;

  function formatTaipeiTimestamp(isoValue) {
    const parsed = new Date(isoValue);
    if (Number.isNaN(parsed.getTime())) return null;
    const dateStr = parsed.toLocaleDateString("sv-SE", { timeZone: "Asia/Taipei" });
    if (dateStr < localDateKey()) return null;
    const localDate = parseLocalDate(dateStr);
    if (!localDate) return null;
    const timeStr = parsed.toLocaleTimeString("en-GB", { timeZone: "Asia/Taipei", hour: "2-digit", minute: "2-digit", hour12: false });
    return {
      dateKey: dateStr,
      text: `${formatFull(localDate)}${timeStr && timeStr !== "00:00" ? ` ${timeStr}` : ""}`,
    };
  }

  function homeDeadlineDisplay() {
    const periods = state.dashboard?.application_periods || [];
    const verifiedPeriods = periods
      .filter((period) => period.scope === "home_application" && period.date_status === "verified_exact" && period.deadline_at && period.status !== "closed")
      .map((period) => formatTaipeiTimestamp(period.deadline_at))
      .filter(Boolean)
      .sort((a, b) => a.dateKey.localeCompare(b.dateKey));
    if (verifiedPeriods.length) return verifiedPeriods[0].text;
    try {
      const home = workflowDeadlineEvents()
        .filter((event) => event.category === "home" && event.date >= localDateKey())
        .sort((a, b) => a.date.localeCompare(b.date))[0] || null;
      const homeDate = home ? parseLocalDate(home.date) : null;
      return homeDate ? formatFull(homeDate) : "依官方公告";
    } catch (_) {
      return "依官方公告";
    }
  }

  function requirementRows(item) {
    const profile = state.eligibilityProfile;
    const rows = [];
    const availability = partnerAvailabilityMeta(item);
    if (availability.blocked) return [{ tone: "blocked", text: availability.reason, state: availability.cardLabel }];
    if (availability.pending) rows.push({ tone: "wait", text: availability.reason, state: availability.cardLabel });
    if (profile) {
      const match = partnerMatch(item, profile);
      if (match.tone === "blocked") rows.push({ tone: "blocked", text: match.label, state: "不符合" });
      // Reasons also include country preferences and research coverage, not just eligibility rules.
      match.reasons.forEach((text) => rows.push({ tone: "ok", text, state: "已知資訊" }));
      match.risks.filter(Boolean).forEach((text) => rows.push({ tone: "wait", text, state: "待確認" }));
    }
    return rows;
  }

  function requirementsHtml(item) {
    const profile = state.eligibilityProfile;
    const rows = requirementRows(item);
    const points = partnerSummaryPoints(item, "eligibility_points").slice(0, 6);
    const own = rows.length
      ? rows.map((row) => `<li class="${row.tone}"><span class="pr-req-icon"><i data-lucide="${row.tone === "ok" ? "check" : row.tone === "blocked" ? "circle-minus" : "clock"}" aria-hidden="true"></i></span><span class="pr-req-text">${escapeHtml(row.text)}</span><span class="pr-req-state">${escapeHtml(row.state)}</span></li>`).join("")
      : `<li class="empty"><span class="pr-req-icon"><i data-lucide="circle-help" aria-hidden="true"></i></span><span class="pr-req-text">${profile ? "這所學校目前沒有可逐項對照的條件" : "填寫學院、學制與語言成績後，這裡會逐項對照你的條件"}</span><a class="pr-req-state" href="#advisor">${profile ? "更新條件" : "填寫條件"}</a></li>`;
    const rules = points.length
      ? `<h3>合作校公開條件</h3><ul class="pr-req-list pr-req-rules">${points.map((text) => `<li><span class="pr-req-icon"><i data-lucide="list" aria-hidden="true"></i></span><span class="pr-req-text">${highlightHtml(text)}</span></li>`).join("")}</ul>` : "";
    return `<section class="pr-requirements" aria-labelledby="pr-requirements-title">
      <h2 id="pr-requirements-title">申請條件</h2>
      <p>依你填寫的條件初步對照。資格初判供參考，正式結果以校方認定為準。</p>
      <ul class="pr-req-list">${own}</ul>${rules}</section>`;
  }

  function renderGallery(item, profile) {
    const gallery = document.querySelector("#school-detail-gallery");
    if (!gallery || state.activeSchool !== item.school_name) return;
    const extras = (profile?.guide_photos || []).filter((photo) => photo.image_url).slice(0, GALLERY_MAX - 1);
    const extra = gallery.querySelector("#school-detail-gallery-extra");
    extra.innerHTML = extras.map((photo) => `<figure><img src="${escapeHtml(photo.image_url)}" alt="${escapeHtml(photo.alt || photo.caption || item.school_name)}" loading="lazy" decoding="async" data-remove-figure-on-error="true" /><figcaption>${escapeHtml(photo.caption || "")}</figcaption></figure>`).join("");
    gallery.dataset.count = String(1 + extras.length);
  }

  function renderBooking(item) {
    const profile = state.eligibilityProfile;
    const term = profile?.targetTerm ? targetTermLabel(profile.targetTerm) : "";
    document.querySelector("#booking-term").textContent = `${term ? `${term}交換` : "交換申請"} · ${activeHomeSchool()}`;
    const fit = document.querySelector("#booking-fit");
    const availability = partnerAvailabilityMeta(item);
    if (availability.blocked) {
      fit.className = "pr-booking-fit blocked";
      fit.dataset.status = "not_open";
      fit.innerHTML = `<i data-lucide="circle-minus" aria-hidden="true"></i><span><strong>${escapeHtml(availability.cardLabel)}</strong><small>${escapeHtml(availability.reason)}</small></span>`;
    } else if (availability.pending) {
      fit.className = "pr-booking-fit wait";
      fit.dataset.status = "needs_confirmation";
      fit.innerHTML = `<i data-lucide="clock" aria-hidden="true"></i><span><strong>${escapeHtml(availability.cardLabel)}</strong><small>${escapeHtml(availability.reason)}</small></span>`;
    } else if (profile) {
      const match = partnerMatch(item, profile);
      const blocked = match.tone === "blocked", matched = match.tone === "strong";
      fit.className = `pr-booking-fit ${blocked ? "blocked" : matched ? "ok" : "wait"}`;
      fit.dataset.status = blocked ? "does_not_match" : matched ? "matches_known" : "needs_confirmation";
      const label = blocked ? "目前條件不符" : matched ? "已知條件初步相符" : "資格待確認";
      const reason = blocked ? match.label : matched ? "仍須核對當期公告，正式資格以校方認定為準。" : match.risks.filter(Boolean)[0] || match.label;
      fit.innerHTML = `<i data-lucide="${blocked ? "circle-minus" : matched ? "circle-check" : "clock"}" aria-hidden="true"></i><span><strong>${label}</strong><small>${escapeHtml(reason)}</small></span>`;
    } else {
      fit.className = "pr-booking-fit neutral";
      fit.dataset.status = "unassessed";
      fit.innerHTML = `<i data-lucide="circle-help" aria-hidden="true"></i><span>尚未比對你的條件 · <a href="#advisor">填寫條件</a></span>`;
    }
    document.querySelector("#booking-home-deadline").textContent = homeDeadlineDisplay();
    const next = partnerNextDeadline(item);
    document.querySelector("#booking-partner-deadline").textContent = next
      ? `${formatFull(next)}${activeHomeSchool() === "長庚大學" ? "（適用已獲提名者）" : ""}`
      : truncate(partnerDeadlineReference(item).value, 36);
    if (activeHomeSchool() === "國立臺灣大學") {
      const homeReference = String(item.application_deadline || "").split("；")[0];
      document.querySelector("#booking-home-deadline").textContent = homeReference.includes("校內報名") ? homeReference : "依臺大官方公告";
      document.querySelector("#booking-partner-deadline").textContent = "依提名通知及接待校當期規定；參考期限見下方各欄";
    }
    const compare = document.querySelector("#detail-compare-button");
    const comparing = discoveryCompare.has(item.school_name);
    compare.dataset.schoolName = item.school_name;
    compare.setAttribute("aria-pressed", String(comparing));
    compare.querySelector("span").textContent = comparing ? "移出比較" : "加入比較";
  }

  function renderHeader(item) {
    const place = [item.country, item.location?.city].filter(Boolean).join("・");
    document.querySelector("#detail-crumb-country").textContent = item.country || "—";
    document.querySelector("#detail-crumb-school").textContent = item.school_name;
    const rating = state.schoolRatings?.[item.school_name];
    document.querySelector("#school-detail-subline").innerHTML = [
      place && `<span>${escapeHtml(place)}</span>`,
      rating && `<span class="pr-rating"><i data-lucide="star" aria-hidden="true"></i>${escapeHtml(String(rating.average))} · ${escapeHtml(String(rating.count))} 則學長姐心得</span>`,
      `<span class="pr-chip-home">${escapeHtml(activeHomeSchool())}合作校</span>`,
    ].filter(Boolean).join("");
  }

  function render(item = partnerByName(state.activeSchool)) {
    if (!item || state.activeSchool !== item.school_name) return;
    renderHeader(item);
    renderBooking(item);
    const overview = document.querySelector("#detail-overview");
    if (overview && !overview.querySelector(".pr-requirements")) overview.insertAdjacentHTML("afterbegin", requirementsHtml(item));
    renderGallery(item, state.destinationCache.get(item.school_name));
    initIcons();
  }

  // Requirements depend on the student's conditions, so they are rebuilt when those change.
  function refresh() {
    const item = partnerByName(state.activeSchool);
    if (!item) return;
    document.querySelector("#detail-overview .pr-requirements")?.remove();
    render(item);
  }

  async function share() {
    const item = partnerByName(state.activeSchool);
    if (!item) return;
    const url = window.location.href;
    try {
      if (navigator.share) { await navigator.share({ title: `${item.school_name} | UniWay`, url }); return; }
      await navigator.clipboard.writeText(url);
      announce("已複製這所學校的連結。", "success");
    } catch (error) {
      if (error?.name !== "AbortError") announce("無法分享，請直接複製網址列的連結。", "info");
    }
  }

  document.addEventListener("click", (event) => {
    if (event.target.closest("#detail-share-button")) { share(); return; }
    const compare = event.target.closest("#detail-compare-button");
    if (!compare) return;
    const name = compare.dataset.schoolName;
    if (!name) return;
    if (discoveryCompare.has(name)) discoveryCompare.delete(name);
    else {
      if (discoveryCompare.size >= 3) { announce("一次比較最多 3 所", "info"); return; }
      if (!activeSchoolSelections().has(name)) toggleFavorite(name);
      discoveryCompare.add(name);
    }
    render();
  });

  document.addEventListener("error", (event) => {
    const image = event.target;
    if (image instanceof HTMLImageElement && image.dataset.removeFigureOnError === "true") image.closest("figure")?.remove();
  }, true);

  return { render, refresh, gallery: renderGallery };
})();

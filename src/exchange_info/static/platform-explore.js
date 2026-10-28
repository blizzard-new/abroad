/* Explore schools (#partners): sort tabs, facet panel, search tiles and the compare tray around the card grid.
   app.js renders the grid; it calls UniWayExplore.render() after every partner render. */
window.UniWayExplore = (() => {
  "use strict";
  const SORTS = [
    { id: "match", label: "最符合條件" },
    { id: "deadline", label: "截止最近" },
    { id: "quota", label: "名額最多" },
  ];
  const COUNTRY_FACETS = 8;
  const narrow = window.matchMedia("(max-width: 900px)");
  let scheduled = 0, drawerSynced = false;

  const root = () => document.querySelector("#partners");
  const shortDate = (date) => `${date.getMonth() + 1}/${String(date.getDate()).padStart(2, "0")}`;

  function sortMetrics(list) {
    const profile = Boolean(state.eligibilityProfile);
    const fit = profile ? list.filter((item) => partnerMatch(item).tone === "strong").length : 0;
    const quotas = list.map(partnerQuotaNumber).filter((value) => value !== null);
    let deadline = "依官方公告";
    try {
      const official = upcomingDeadlines(1)[0];
      const partner = list.map(partnerNextDeadline).filter(Boolean).sort((a, b) => a - b)[0];
      if (official) deadline = `最近 ${shortDate(official.date)} ${official.scope}`;
      else if (partner) deadline = `最近 ${shortDate(partner)} 合作校申請`;
    } catch (_) { /* the tab then says the deadline follows the official notice */ }
    const picked = UniWayDiscovery.hasCriteria(discoveryCriteria);
    const fits = picked ? list.filter((item) => UniWayDiscovery.assess(item, discoveryCriteria).matched).length : 0;
    return {
      match: picked ? `${fits} 間符合所選條件` : profile ? `${fit} 間符合資格` : "尚未填寫條件",
      deadline,
      quota: quotas.length ? `最多 ${Math.max(...quotas)} 名` : "依官方公告",
    };
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
    if (state.region) labels.push(state.region);
    if (state.country) labels.push(state.country);
    if (state.college) labels.push(state.college);
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
    if (!narrow.matches) drawer.open = true;
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
    const list = filteredPartners({ sort: false });
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
    const host = root();
    if (!host || !host.contains(event.target)) return;
    if (event.target.closest("[data-partner-clear-all]")) { document.querySelector("#clear-partner-filters")?.click(); return; }
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
        if (!activeSchoolSelections().has(name)) toggleFavorite(name);
        discoveryCompare.add(name);
        if (discoveryCompare.size >= 2) document.dispatchEvent(new CustomEvent("uniway:compare", {detail: {school_count: discoveryCompare.size}}));
      } else discoveryCompare.delete(name);
      renderPartnerTable();
    }
  });

  narrow.addEventListener("change", () => { drawerSynced = false; schedule(); });
  return { render: schedule };
})();

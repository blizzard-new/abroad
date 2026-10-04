/* Progressive enhancement only: never delay routing, focus, saving or dismissal. */
(() => {
  "use strict";
  if (window.UniWayMotion) return;
  const media = matchMedia("(prefers-reduced-motion: reduce)");
  const active = new Map();
  const pending = new Map();
  const resultKeys = new WeakMap();
  const resultSelector = "#partner-table, #search-results, #global-community-feed, #selection-workspace, #advisor-result-content, #eligibility-result, #document-check-result, #writing-assistant-result, #notification-center-list, #life-content, #experience-content, #application-template-list, #private-vault-list, #document-workspace-list, #application-calendar-grid, #calendar-agenda-list";
  const itemSelector = ".partner-table tbody tr, .partner-card, .discovery-candidate, .discovery-experience-card, .community-post-card, .search-result-card, .notification-center-item";
  const panelSelector = '[role="tabpanel"], #partner-map-panel, #partner-table, #partner-map-preview';
  let frame = 0, routeFrame = 0, lastRoute = "", lastRoot = null, lastIndex = null;
  const tokens = getComputedStyle(document.documentElement);
  const duration = (name) => parseFloat(tokens.getPropertyValue(`--uw-motion-${name}`)) || 240;
  const easing = tokens.getPropertyValue("--uw-motion-out").trim() || "ease-out";
  const allowed = () => !media.matches && !document.hidden;
  const visible = (el) => {
    if (!(el instanceof HTMLElement) || !el.isConnected || el.closest('[hidden], dialog:not([open])')) return false;
    const box = el.getBoundingClientRect();
    return box.width > 0 && box.height > 0 && box.bottom > 0 && box.top < innerHeight;
  };

  function cancel(el) {
    const animation = active.get(el);
    if (!animation) return;
    active.delete(el);
    animation.cancel();
  }
  function cancelAll() {
    [...active.keys()].forEach(cancel);
    pending.clear();
    cancelAnimationFrame(frame); frame = 0;
  }
  function play(el, kind = "arrive", delay = 0) {
    if (!allowed() || !visible(el) || typeof el.animate !== "function") return;
    cancel(el);
    const keyframes = kind === "route" || (kind === "result" && el.matches("tr")) ? [{ opacity: .65 }, { opacity: 1 }]
      : kind === "confirm" ? [{ scale: "1" }, { scale: "1.035", offset: .45 }, { scale: "1" }]
      : kind === "dialog" ? [{ opacity: .3, translate: "0 14px", scale: ".985" }, { opacity: 1, translate: "0 0", scale: "1" }]
      : kind === "back" ? [{ opacity: .65, translate: "-8px 0" }, { opacity: 1, translate: "0 0" }]
      : [{ opacity: .55, translate: `0 ${kind === "result" ? 5 : 8}px` }, { opacity: 1, translate: "0 0" }];
    const animation = el.animate(keyframes, { duration: duration(kind === "dialog" ? "arrive" : kind === "confirm" ? "fast" : "standard"), easing, delay, fill: "none" });
    animation.id = `uniway:${kind}`;
    active.set(el, animation);
    animation.finished.then(() => {
      if (active.get(el) === animation) active.delete(el);
      animation.cancel();
    }, () => { if (active.get(el) === animation) active.delete(el); });
  }
  function enqueue(el, kind) {
    if (!allowed() || !(el instanceof HTMLElement)) return;
    pending.set(el, kind);
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      const entries = [...pending]; pending.clear();
      entries.slice(0, 12).forEach(([target, type]) => {
        if (!visible(target)) return;
        if (type === "results") revealResults(target);
        else play(target, type);
      });
    });
  }
  function revealResults(region) {
    const items = [...region.querySelectorAll(itemSelector)].filter(visible);
    // Re-rendering a note/heart must not replay every saved card.
    const signature = items.map(el => el.dataset.postId || el.dataset.notificationId || el.querySelector("[data-school-name]")?.dataset.schoolName || el.textContent.trim().slice(0, 100)).join("|");
    if (resultKeys.get(region) === signature && items.length) return;
    resultKeys.set(region, signature);
    const targets = items.length ? items.slice(0, 6) : [region];
    targets.forEach((el, i) => play(el, "result", i * 18));
  }
  function route(hash = location.hash || "#home") {
    cancelAnimationFrame(routeFrame);
    routeFrame = requestAnimationFrame(() => {
      routeFrame = 0;
      const root = hash.startsWith("#school=") ? document.querySelector("#school-detail-view")
        : document.body.classList.contains("global-home-mode") || document.body.classList.contains("cgu-community-mode") ? document.querySelector("#community-hub")
        : document.querySelector('#dashboard-view > section[data-university-page]:not([hidden])');
      if (!root || !root.getClientRects().length || root.hidden) return;
      if (hash === lastRoute && root === lastRoot) return;
      const index = history.state?.uniwayNavigation?.index ?? null;
      const backward = lastIndex !== null && index !== null && index < lastIndex;
      lastRoute = hash; lastRoot = root; lastIndex = index;
      cancelAll();
      play(root, "route");
      // Keep restored scroll and sticky positioning stable: never transform the page itself.
      if (!window.UniWayNavigation?.isRestoring) {
        const heading = root.querySelector(".school-detail-copy, .guide-intro, .section-heading, .community-home-heading");
        play(heading, backward ? "back" : "arrive");
        if (hash === "#guide") [...root.querySelectorAll(".guide-stage")].slice(0, 4).forEach((el, i) => play(el, "arrive", i * 25));
      }
    });
  }
  function dialogSurface(el) {
    return el.matches("dialog") ? el : el.querySelector(".account-dialog-shell, .onboarding-shell") || el;
  }
  function stopHidden() {
    [...active.keys()].forEach(el => { if (!visible(el)) cancel(el); });
  }
  const observer = new MutationObserver(records => {
    if (!allowed()) return;
    const results = new Set();
    for (const record of records) {
      const el = record.target;
      if (!(el instanceof HTMLElement)) continue;
      if (record.type === "childList") {
        // Ignore icon SVG replacement and text/attribute churn outside known results.
        if (![...record.addedNodes].some(node => node instanceof HTMLElement)) continue;
        const region = el.closest(resultSelector);
        if (region) results.add(region);
        for (const node of record.addedNodes) {
          if (!(node instanceof HTMLElement)) continue;
          if (node.matches(".status-message, .form-status > *, .workspace-empty, .empty-state")) enqueue(node, "arrive");
        }
      } else if (record.attributeName === "hidden" || record.attributeName === "open") {
        if (el.matches('dialog, [role="dialog"]') && !el.hidden && (!el.matches("dialog") || el.open)) enqueue(dialogSurface(el), "dialog");
        else if (el.id === "application-tools" && el.open) enqueue(el.querySelector(".application-tools-panel"), "arrive");
        else if (el.matches(panelSelector) && !el.hidden && record.oldValue !== null) enqueue(el, "arrive");
      } else if (record.oldValue !== null && record.oldValue !== el.getAttribute(record.attributeName) && el.getAttribute(record.attributeName) === "true" && el.matches("button, [role='checkbox']")) {
        enqueue(el, "confirm");
      }
    }
    results.forEach(el => enqueue(el, "results"));
    stopHidden();
  });
  observer.observe(document.body, { subtree: true, childList: true, attributes: true, attributeOldValue: true, attributeFilter: ["hidden", "open", "aria-pressed", "aria-checked", "aria-selected"] });
  function preferenceChanged() { if (media.matches) cancelAll(); }
  function visibilityChanged() {
    document.documentElement.toggleAttribute("data-motion-suspended", document.hidden);
    if (document.hidden) cancelAll();
  }
  media.addEventListener("change", preferenceChanged);
  document.addEventListener("visibilitychange", visibilityChanged);
  window.addEventListener("pagehide", cancelAll);
  document.documentElement.classList.add("uw-motion-ready");
  window.UniWayMotion = Object.freeze({
    route,
    duration,
    get reduced() { return media.matches; },
    destroy() {
      observer.disconnect(); cancelAll(); cancelAnimationFrame(routeFrame);
      media.removeEventListener("change", preferenceChanged);
      document.removeEventListener("visibilitychange", visibilityChanged);
      window.removeEventListener("pagehide", cancelAll);
      document.documentElement.classList.remove("uw-motion-ready");
    },
  });
})();

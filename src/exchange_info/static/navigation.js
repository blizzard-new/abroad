/* Shared, same-document navigation. An untracked entry is always a safe boundary. */
(() => {
  "use strict";
  const key = "uniwayNavigation";
  const valid = (entry) => entry && typeof entry.id === "string" && Number.isInteger(entry.index) && entry.index >= 0;
  let current = valid(history.state?.[key]) ? history.state[key] : { id: crypto.randomUUID(), index: 0, scroll: 0 };
  let currentUrl = location.href;
  let restoring = false;
  let restoreFrame = 0;
  let backPending = false;

  function stamp(data = history.state) {
    return { ...data, [key]: { ...current } };
  }
  function saveScroll() {
    if (restoring || location.href !== currentUrl) return;
    current.scroll = window.scrollY;
    history.replaceState(stamp(), "");
  }
  function sync() {
    const activeBack = location.hash.startsWith("#school=") ? "back-to-schools"
      : location.hash.startsWith("#application-form=") ? "back-to-application-center" : "page-back";
    document.querySelectorAll(".route-back").forEach((button) => {
      button.hidden = button.id !== activeBack;
      button.disabled = current.index === 0 && (!location.hash || location.hash === "#home");
      button.setAttribute("aria-label", current.index > 0 ? "返回上一頁" : "返回首頁");
    });
    document.querySelector("#application-tools")?.removeAttribute("open");
  }
  function replaceState(data, title, url) {
    observe();
    history.replaceState(stamp(data), title, url);
    currentUrl = location.href;
    sync();
  }
  function pushState(data, title, url) {
    observe();
    saveScroll();
    current = { ...current, index: current.index + 1, scroll: 0 };
    history.pushState(stamp(data), title, url);
    currentUrl = location.href;
    sync();
  }
  function observe() {
    const entry = history.state?.[key];
    if (location.href === currentUrl && entry?.id === current.id && entry?.index === current.index) return;
    if (valid(entry) && entry.id === current.id) {
      current = entry;
      restoring = true;
      const scroll = current.scroll || 0;
      cancelAnimationFrame(restoreFrame);
      // Both popstate and hashchange run the app router; restore after its rendering.
      restoreFrame = requestAnimationFrame(() => {
        restoreFrame = requestAnimationFrame(() => {
          window.scrollTo({ top: scroll, behavior: "instant" });
          restoring = false;
        });
      });
    } else {
      current = { ...current, index: current.index + 1, scroll: 0 };
      history.replaceState(stamp(), "");
    }
    currentUrl = location.href;
    backPending = false;
    sync();
  }
  function back() {
    if (backPending) return;
    saveScroll();
    if (current.index > 0) {
      backPending = true;
      history.back();
    } else if (location.hash !== "#home") {
      // Replace a direct-entry detail/tool URL so Back never leaves the app.
      replaceState({}, "", "#home");
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    }
  }

  history.scrollRestoration = "manual";
  history.replaceState(stamp(), "");
  document.querySelectorAll(".route-back").forEach((button) => button.addEventListener("click", back));
  document.querySelector('.skip-link[href="#main-content"]')?.addEventListener("click", (event) => {
    event.preventDefault();
    const main = document.querySelector("#main-content");
    main.setAttribute("tabindex", "-1");
    main.focus({ preventScroll: true });
  });
  window.addEventListener("scroll", saveScroll, { passive: true });
  window.addEventListener("pagehide", saveScroll);
  window.addEventListener("popstate", observe);
  window.addEventListener("hashchange", observe);
  document.addEventListener("click", (event) => {
    const menu = document.querySelector("#application-tools");
    if (menu?.open && (!menu.contains(event.target) || event.target.closest("a"))) menu.open = false;
  });
  document.addEventListener("keydown", (event) => {
    const menu = document.querySelector("#application-tools");
    if (event.key === "Escape" && menu?.open) {
      event.preventDefault();
      menu.open = false;
      menu.querySelector("summary").focus();
    }
  });
  const rail = document.querySelector("#glass-navigation");
  const toggle = document.querySelector("#glass-menu-toggle");
  const close = document.querySelector("#glass-menu-close");
  const backdrop = document.querySelector("#glass-menu-backdrop");
  const mobile = window.matchMedia("(max-width: 900px)");
  const tools = document.querySelector("#application-tools");
  const toolsPanel = tools?.querySelector(".application-tools-panel");
  // Top-layer disclosures escape the scrolling rail without covering its controls.
  function syncToolsPanel() {
    if (!toolsPanel || !toolsPanel.showPopover) return;
    if (mobile.matches) {
      if (toolsPanel.matches(":popover-open")) toolsPanel.hidePopover();
      toolsPanel.removeAttribute("popover");
      return;
    }
    toolsPanel.setAttribute("popover", "manual");
    if (tools.open) {
      if (!toolsPanel.matches(":popover-open")) toolsPanel.showPopover();
      const anchor = tools.getBoundingClientRect();
      const height = toolsPanel.getBoundingClientRect().height;
      toolsPanel.style.setProperty("--rail-panel-left", `${rail.getBoundingClientRect().right + 12}px`);
      toolsPanel.style.setProperty("--rail-panel-top", `${Math.max(16, Math.min(anchor.top, innerHeight - height - 16))}px`);
    } else if (toolsPanel.matches(":popover-open")) toolsPanel.hidePopover();
  }
  new MutationObserver(syncToolsPanel).observe(tools, { subtree: true, attributes: true, attributeFilter: ["open"] });
  mobile.addEventListener("change", syncToolsPanel);
  window.addEventListener("resize", syncToolsPanel);
  rail?.addEventListener("scroll", syncToolsPanel, { passive: true });
  syncToolsPanel();

  const tip = document.createElement("div");
  tip.className = "glass-rail-tooltip";
  tip.setAttribute("aria-hidden", "true");
  document.body.append(tip);
  let tipTarget = null;
  function hideTip() { tip.classList.remove("is-visible"); tipTarget = null; }
  function showTip(control) {
    if (mobile.matches || control.closest(".application-tools-panel")) return;
    const label = control.querySelector("#account-workspace-sync-label")?.textContent
      || control.getAttribute("aria-label") || control.textContent.trim();
    if (!label) return;
    tipTarget = control;
    tip.textContent = label;
    const rect = control.getBoundingClientRect();
    tip.style.left = `${rail.getBoundingClientRect().right + 12}px`;
    tip.style.top = `${Math.max(24, Math.min(rect.top + rect.height / 2, innerHeight - 24))}px`;
    tip.classList.add("is-visible");
  }
  rail?.querySelectorAll('.uniway-header-brand, [data-public-route], .application-nav-chevron, .route-back, #school-switcher, .topbar-actions button, .workspace-sync-status').forEach(control => {
    if (!control.hasAttribute("aria-label") && control.matches("[data-public-route]")) control.setAttribute("aria-label", control.textContent.trim());
    if (control.matches(".application-nav-chevron")) control.setAttribute("aria-label", "展開我的申請工具");
    control.addEventListener("pointerenter", () => showTip(control));
    control.addEventListener("pointerleave", hideTip);
    control.addEventListener("focus", () => showTip(control));
    control.addEventListener("blur", hideTip);
  });
  tools?.querySelector("summary")?.setAttribute("aria-label", "展開我的申請工具");
  tools?.querySelector("summary")?.addEventListener("focus", event => showTip(event.currentTarget));
  tools?.querySelector("summary")?.addEventListener("blur", hideTip);
  document.addEventListener("keydown", event => { if (event.key === "Escape") hideTip(); });
  window.addEventListener("hashchange", hideTip);
  window.addEventListener("resize", hideTip);
  rail?.addEventListener("scroll", hideTip, { passive: true });
  // Account, school and theme names can change after the first render.
  new MutationObserver(() => { if (tipTarget) showTip(tipTarget); }).observe(rail, { subtree: true, childList: true, attributes: true, attributeFilter: ["aria-label"] });
  function setSidebar(open, { restoreFocus = false } = {}) {
    if (!rail || !toggle || !backdrop) return;
    const expanded = mobile.matches && open;
    document.body.classList.toggle("glass-menu-open", expanded);
    toggle.setAttribute("aria-expanded", String(expanded));
    backdrop.hidden = !expanded;
    rail.inert = mobile.matches && !expanded;
    document.querySelector("#main-content").inert = expanded;
    if (expanded) {
      rail.setAttribute("role", "dialog");
      rail.setAttribute("aria-modal", "true");
      // Wait for the drawer's visibility transition to begin before focusing it.
      requestAnimationFrame(() => {
        if (document.body.classList.contains("glass-menu-open")) close?.focus();
      });
    } else {
      rail.removeAttribute("role");
      rail.removeAttribute("aria-modal");
      if (restoreFocus && mobile.matches) toggle.focus();
    }
  }
  rail?.addEventListener("transitionend", event => {
    if (event.target === rail && event.propertyName === "transform"
      && document.body.classList.contains("glass-menu-open") && !rail.contains(document.activeElement)) close?.focus();
  });
  toggle?.addEventListener("click", () => setSidebar(true));
  close?.addEventListener("click", () => setSidebar(false, { restoreFocus: true }));
  backdrop?.addEventListener("click", () => setSidebar(false, { restoreFocus: true }));
  mobile.addEventListener("change", () => setSidebar(false));
  window.addEventListener("hashchange", () => setSidebar(false));
  document.addEventListener("click", (event) => {
    if (rail?.contains(event.target) && event.target.closest("a[href], .route-back, #account-button, #notification-button, #school-switcher")) setSidebar(false);
  });
  document.addEventListener("keydown", (event) => {
    if (!document.body.classList.contains("glass-menu-open") || event.defaultPrevented) return;
    if (event.key === "Escape") {
      event.preventDefault();
      setSidebar(false, { restoreFocus: true });
    } else if (event.key === "Tab") {
      const controls = [...rail.querySelectorAll('a[href], button:not([disabled]), summary')].filter(el => el.getClientRects().length && !el.hidden);
      const first = controls[0], last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });
  setSidebar(false);
  window.UniWayNavigation = { pushState, replaceState, back, sync, get isRestoring() { return restoring; } };
  sync();
})();

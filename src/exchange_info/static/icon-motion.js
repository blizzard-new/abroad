(() => {
  "use strict";

  const GLOBAL_KEY = "__exchangeGuideIconMotion";
  if (window[GLOBAL_KEY]) {
    window.IconMotion = window[GLOBAL_KEY];
    window[GLOBAL_KEY].refresh(document);
    return;
  }

  const VERSION = "1.0.0";
  const MORPHICONS_VERSION = "1.7.0";
  const MORPHICONS_URL = `/static/vendor/morphicons/${MORPHICONS_VERSION}/dist/dom.js`;
  const ICON_SELECTOR = "svg.lucide, svg[data-lucide]";
  const INTERACTIVE_SELECTOR = [
    "button",
    "a[href]",
    "summary",
    "label[for]",
    "[role='button']",
    "[role='link']",
    "[role='tab']",
    "[role='menuitem']",
    "[role='checkbox']",
    "[role='radio']",
    "[tabindex]:not([tabindex='-1'])",
  ].join(",");

  const MORPH_GROUPS = [
    ["sun", "moon"],
    ["bookmark", "bookmark-check"],
    ["plus", "check"],
    ["circle", "circle-check"],
    ["clipboard-plus", "clipboard-x", "badge-alert"],
    ["calendar-plus", "calendar-check-2"],
    ["file", "file-clock", "file-check-2"],
    ["circle-alert", "badge-check"],
    ["school", "graduation-cap"],
    ["bell", "bell-dot", "bell-ring"],
    ["cloud-upload", "cloud-off", "cloud"],
    ["eye", "eye-off"],
    ["lock", "unlock"],
    ["play", "pause"],
    ["volume-2", "volume-x"],
  ];
  const MORPH_NAMES = new Set(MORPH_GROUPS.flat());
  const STATE_ATTRIBUTES = new Set([
    "aria-checked",
    "aria-current",
    "aria-expanded",
    "aria-pressed",
    "aria-selected",
    "open",
  ]);
  const REFRESH_ATTRIBUTES = [
    ...STATE_ATTRIBUTES,
    "aria-busy",
    "data-loading",
    "data-icon-loading",
    "data-lucide",
    "hidden",
  ];
  const STABLE_ATTRIBUTES = [
    "data-icon-motion-key",
    "data-school-name",
    "data-follow-board",
    "data-home-school",
    "data-section",
    "data-detail-target",
    "data-community-route",
    "data-calendar-provider",
    "data-document-id",
    "data-document-status",
    "data-submission-action",
  ];

  const seenEntrances = new Set();
  const stateHistory = new Map();
  const morphHandles = new WeakMap();
  const preparedMorphs = new WeakSet();
  const pendingRoots = new Set();
  const reducedMotion = typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : null;

  let observer = null;
  let refreshFrame = 0;
  let createMorph = null;
  let iconIndex = null;
  let warnedAboutMorphicons = false;

  function motionIsReduced() {
    return Boolean(reducedMotion?.matches);
  }

  function iconName(icon) {
    const declared = icon.getAttribute("data-lucide") || icon.dataset.iconName;
    if (declared) return declared.toLowerCase();
    const iconClass = Array.from(icon.classList).find(
      (name) => name.startsWith("lucide-") && name !== "lucide-icon",
    );
    return iconClass ? iconClass.slice(7).toLowerCase() : "";
  }

  function visible(icon) {
    if (!icon.isConnected || icon.closest("[hidden]")) return false;
    return typeof icon.getClientRects !== "function" || icon.getClientRects().length > 0;
  }

  function stableAttribute(element) {
    for (const name of STABLE_ATTRIBUTES) {
      const value = element.getAttribute(name);
      if (value) return `${name}=${value}`;
    }
    return "";
  }

  function pathSegment(element) {
    if (element.id) return `#${element.id}`;
    const stable = stableAttribute(element);
    if (stable) return `${element.localName}[${stable}]`;
    const parent = element.parentElement;
    if (!parent) return element.localName;
    const siblings = Array.from(parent.children).filter((item) => item.localName === element.localName);
    return `${element.localName}:nth-of-type(${siblings.indexOf(element) + 1})`;
  }

  function elementPath(element) {
    const segments = [];
    let current = element;
    while (current && current !== document.documentElement && segments.length < 7) {
      segments.unshift(pathSegment(current));
      if (current.id) break;
      current = current.parentElement;
    }
    return segments.join(">");
  }

  function logicalKey(icon) {
    const owner = icon.closest(INTERACTIVE_SELECTOR);
    const scope = owner || icon.parentElement || icon;
    const icons = owner ? Array.from(owner.querySelectorAll(ICON_SELECTOR)) : [icon];
    const position = Math.max(0, icons.indexOf(icon));
    return `${elementPath(scope)}::icon-${position}`;
  }

  function semanticMotion(name) {
    if (/^(arrow|chevron)-right$/.test(name) || name === "send") return "forward";
    if (/^(arrow|chevron)-left$/.test(name)) return "back";
    if (name.includes("upload") || name === "arrow-up") return "upload";
    if (name.includes("download") || name === "arrow-down") return "download";
    if (/^(refresh|rotate)-/.test(name)) return "refresh";
    if (/^(bookmark|heart|star)/.test(name)) return "favorite";
    if (/^bell/.test(name)) return "notification";
    if (/^(check|circle-check|badge-check)/.test(name)) return "select";
    return "lift";
  }

  function loadingContext(icon, name) {
    if (/^(loader|loader-circle|circle-dashed)$/.test(name)) return true;
    if (!/^(refresh-cw|rotate-cw)$/.test(name)) return false;
    return Boolean(icon.closest("[aria-busy='true'], [data-loading='true'], [data-icon-loading='true'], .is-loading"));
  }

  function syncLoading(icon, name) {
    if (loadingContext(icon, name)) icon.dataset.iconMotionLoop = "spin";
    else delete icon.dataset.iconMotionLoop;
  }

  function markEntrance(icon, key) {
    icon.classList.add("icon-motion-ready");
    if (seenEntrances.has(key) || !visible(icon)) {
      // Lucide copies classes when a later initIcons() call replaces an SVG.
      // Strip a copied entrance marker so the logical icon never replays it.
      icon.classList.remove("icon-motion-enter");
      return;
    }
    seenEntrances.add(key);
    if (motionIsReduced()) return;
    icon.classList.add("icon-motion-enter");
    const finish = () => icon.classList.remove("icon-motion-enter");
    icon.addEventListener("animationend", finish, { once: true });
    window.setTimeout(finish, 500);
  }

  function play(icon, kind = "confirm") {
    if (!(icon instanceof SVGElement) || motionIsReduced() || !visible(icon)) return;
    icon.removeAttribute("data-icon-motion-play");
    void icon.getBoundingClientRect();
    icon.setAttribute("data-icon-motion-play", kind);
    const finish = () => icon.removeAttribute("data-icon-motion-play");
    icon.addEventListener("animationend", finish, { once: true });
    window.setTimeout(finish, 550);
  }

  function normalizeExportName(value) {
    return String(value || "").replace(/[^a-z0-9]/gi, "").toLowerCase();
  }

  function buildIconIndex() {
    const icons = window.lucide?.icons;
    if (!icons) return null;
    const next = new Map();
    Object.entries(icons).forEach(([name, data]) => {
      const normalized = normalizeExportName(name);
      if (!next.has(normalized)) next.set(normalized, data);
    });
    return next;
  }

  function iconNode(name) {
    if (!window.lucide?.icons) return null;
    if (!iconIndex) iconIndex = buildIconIndex();
    const value = iconIndex?.get(normalizeExportName(name));
    if (!Array.isArray(value)) return null;
    if (value[0] === "svg" && Array.isArray(value[2])) return value[2];
    return Array.isArray(value[0]) ? value : null;
  }

  function sameMorphGroup(from, to) {
    return MORPH_GROUPS.some((group) => group.includes(from) && group.includes(to));
  }

  function transitionFrom(key, name) {
    const now = performance.now();
    const history = stateHistory.get(key);
    if (!history) {
      stateHistory.set(key, { current: name, previous: "", changedAt: 0 });
      return "";
    }
    if (history.current !== name) {
      history.previous = history.current;
      history.current = name;
      history.changedAt = now;
      return history.previous;
    }
    if (history.previous && now - history.changedAt < 450) return history.previous;
    return "";
  }

  function prepareMorph(icon, key, name) {
    if (!createMorph || preparedMorphs.has(icon) || !MORPH_NAMES.has(name)) return false;
    const currentNode = iconNode(name);
    if (!currentNode) return false;
    const previousName = transitionFrom(key, name);
    const previousNode = previousName && sameMorphGroup(previousName, name)
      ? iconNode(previousName)
      : null;
    const originalMarkup = icon.innerHTML;
    try {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      icon.replaceChildren(path);
      const handle = createMorph(path, previousNode || currentNode, { reducedMotion: "user" });
      morphHandles.set(icon, handle);
      preparedMorphs.add(icon);
      icon.dataset.iconName = name;
      icon.dataset.iconMotionEngine = "morphicons";
      icon.dataset.morphiconsVersion = MORPHICONS_VERSION;
      icon.removeAttribute("data-lucide");
      if (previousNode) handle.morphTo(currentNode, "snappy");
      return Boolean(previousNode);
    } catch (error) {
      icon.innerHTML = originalMarkup;
      if (!warnedAboutMorphicons) {
        warnedAboutMorphicons = true;
        console.warn("Morphicons could not enhance an icon; the Lucide fallback remains active.", error);
      }
      return false;
    }
  }

  function rememberUnpreparedState(key, name) {
    if (!createMorph || !MORPH_NAMES.has(name)) transitionFrom(key, name);
  }

  function enhanceIcon(icon) {
    if (!(icon instanceof SVGElement) || !icon.matches(ICON_SELECTOR)) return;
    const name = iconName(icon);
    if (!name) return;
    const key = logicalKey(icon);
    icon.dataset.iconMotion = icon.dataset.iconMotion || semanticMotion(name);
    syncLoading(icon, name);
    markEntrance(icon, key);
    rememberUnpreparedState(key, name);
    prepareMorph(icon, key, name);
  }

  function collectIcons(root) {
    if (!(root instanceof Element || root instanceof Document || root instanceof DocumentFragment)) return [];
    const icons = [];
    if (root instanceof Element && root.matches(ICON_SELECTOR)) icons.push(root);
    root.querySelectorAll?.(ICON_SELECTOR).forEach((icon) => icons.push(icon));
    return icons;
  }

  function refresh(root = document) {
    const icons = collectIcons(root);
    icons.forEach(enhanceIcon);
    return icons.length;
  }

  function queueRefresh(root) {
    if (!root) return;
    pendingRoots.add(root);
    if (refreshFrame) return;
    refreshFrame = window.requestAnimationFrame(() => {
      refreshFrame = 0;
      const icons = new Set();
      pendingRoots.forEach((pending) => collectIcons(pending).forEach((icon) => icons.add(icon)));
      pendingRoots.clear();
      icons.forEach(enhanceIcon);
    });
  }

  function relatedIcons(target) {
    if (!(target instanceof Element)) return [];
    if (target.matches(ICON_SELECTOR)) return [target];
    if (target.matches("details")) {
      const summary = target.querySelector(":scope > summary");
      return summary ? collectIcons(summary) : [];
    }
    return collectIcons(target);
  }

  function cleanup(root) {
    if (!(root instanceof Element || root instanceof DocumentFragment)) return;
    const icons = [];
    if (root instanceof Element && morphHandles.has(root)) icons.push(root);
    root.querySelectorAll?.("[data-icon-motion-engine='morphicons']").forEach((icon) => icons.push(icon));
    icons.forEach((icon) => {
      morphHandles.get(icon)?.destroy();
      morphHandles.delete(icon);
    });
  }

  function handleMutations(mutations) {
    mutations.forEach((mutation) => {
      if (mutation.type === "childList") {
        mutation.removedNodes.forEach(cleanup);
        mutation.addedNodes.forEach((node) => {
          if (node instanceof Element || node instanceof DocumentFragment) queueRefresh(node);
        });
        return;
      }
      const target = mutation.target;
      if (!(target instanceof Element)) return;
      queueRefresh(target);
      if (STATE_ATTRIBUTES.has(mutation.attributeName)) {
        relatedIcons(target).forEach((icon) => play(icon, "confirm"));
      }
    });
  }

  function clickIcon(event) {
    const target = event.target instanceof Element ? event.target : null;
    const control = target?.closest(INTERACTIVE_SELECTOR);
    if (!control || control.matches(":disabled") || control.getAttribute("aria-disabled") === "true") return;
    const direct = target.closest(ICON_SELECTOR);
    const icons = direct && control.contains(direct) ? [direct] : collectIcons(control);
    icons.forEach((icon) => play(icon, icon.dataset.iconMotion === "notification" ? "ring" : "confirm"));
  }

  function onPreferenceChange() {
    if (!motionIsReduced()) return;
    document.querySelectorAll(".icon-motion-enter, [data-icon-motion-play]").forEach((icon) => {
      icon.classList.remove("icon-motion-enter");
      icon.removeAttribute("data-icon-motion-play");
    });
  }

  const morphiconsReady = import(MORPHICONS_URL)
    .then((module) => {
      if (typeof module.createMorph !== "function") throw new TypeError("createMorph export is missing");
      createMorph = module.createMorph;
      document.documentElement.dataset.iconMotionEngine = `morphicons@${MORPHICONS_VERSION}`;
      refresh(document);
      return true;
    })
    .catch((error) => {
      document.documentElement.dataset.iconMotionEngine = "css-fallback";
      if (!warnedAboutMorphicons) {
        warnedAboutMorphicons = true;
        console.warn("Morphicons failed to load; icon motion is using the CSS fallback.", error);
      }
      return false;
    });

  observer = new MutationObserver(handleMutations);
  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeOldValue: true,
    attributeFilter: REFRESH_ATTRIBUTES,
  });
  document.addEventListener("click", clickIcon);
  reducedMotion?.addEventListener?.("change", onPreferenceChange);

  const api = Object.freeze({
    version: VERSION,
    morphiconsVersion: MORPHICONS_VERSION,
    ready: morphiconsReady,
    refresh,
    animate(target, kind = "confirm") {
      const root = typeof target === "string" ? document.querySelector(target) : target;
      if (!(root instanceof Element)) return 0;
      const icons = root.matches(ICON_SELECTOR) ? [root] : collectIcons(root);
      icons.forEach((icon) => play(icon, kind));
      return icons.length;
    },
    destroy() {
      observer?.disconnect();
      observer = null;
      document.removeEventListener("click", clickIcon);
      reducedMotion?.removeEventListener?.("change", onPreferenceChange);
      cleanup(document.documentElement);
    },
  });

  window[GLOBAL_KEY] = api;
  window.IconMotion = api;
  queueRefresh(document);
})();

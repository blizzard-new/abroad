/* UniWay anonymous usage analytics (first party). See docs/analytics.md.
 *
 * - Stores a random visitor id in localStorage; no cookies, no account id, no IP, no form contents.
 * - Off when the browser sends Do Not Track / Global Privacy Control, when the visitor opts out
 *   (footer button, or ?analytics=off once to exclude your own browser), and in automated browsers.
 * - Never throws and never blocks the page: every failure is swallowed.
 */
(function () {
  "use strict";

  var ENDPOINT = "/analytics/events";
  var OPT_OUT_KEY = "uniway-analytics-optout";
  var VISITOR_KEY = "uniway-analytics-visitor";
  var FORCE_KEY = "uniway-analytics-force";
  var SESSION_KEY = "uniway-analytics-session";
  var SESSION_IDLE_MS = 30 * 60 * 1000;
  var FLUSH_MS = 5000;
  var MAX_QUEUE = 200;
  var BATCH = 30;
  var IDLE_MS = 10000;

  function store(kind) {
    try { return window[kind]; } catch (_) { return null; }
  }
  function read(kind, key) {
    try { var s = store(kind); return s ? s.getItem(key) : null; } catch (_) { return null; }
  }
  function write(kind, key, value) {
    try { var s = store(kind); if (s) s.setItem(key, value); } catch (_) { /* private mode */ }
  }
  function erase(kind, key) {
    try { var s = store(kind); if (s) s.removeItem(key); } catch (_) { /* ignore */ }
  }
  function randomId() {
    try {
      var bytes = new Uint8Array(12);
      window.crypto.getRandomValues(bytes);
      return Array.prototype.map.call(bytes, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
    } catch (_) {
      return (Date.now().toString(16) + Math.random().toString(16).slice(2)).padEnd(24, "0").slice(0, 24);
    }
  }

  // One-time switches carried in the address bar: ?analytics=off / ?analytics=on
  try {
    var flag = new URLSearchParams(window.location.search).get("analytics");
    if (flag === "off") write("localStorage", OPT_OUT_KEY, "1");
    if (flag === "on") erase("localStorage", OPT_OUT_KEY);
  } catch (_) { /* ignore */ }

  function browserDoesNotWantTracking() {
    return navigator.doNotTrack === "1" || window.doNotTrack === "1" || navigator.msDoNotTrack === "1"
      || navigator.globalPrivacyControl === true;
  }
  function optedOut() { return read("localStorage", OPT_OUT_KEY) === "1"; }
  function automated() { return navigator.webdriver === true && read("localStorage", FORCE_KEY) !== "1"; }
  function active() { return !optedOut() && !browserDoesNotWantTracking() && !automated(); }

  // ---- identity
  var newVisitor = false;
  function visitorId() {
    var id = read("localStorage", VISITOR_KEY);
    if (!id || !/^[A-Za-z0-9_-]{8,64}$/.test(id)) {
      id = randomId();
      write("localStorage", VISITOR_KEY, id);
      newVisitor = true;
    }
    return id;
  }
  var session = null;
  function touchSession() {
    var now = Date.now();
    if (!session) {
      try { session = JSON.parse(read("sessionStorage", SESSION_KEY) || "null"); } catch (_) { session = null; }
    }
    if (!session || now - session.last > SESSION_IDLE_MS) {
      session = { id: randomId(), last: now, fresh: true, entry: true };
      queueRaw("session_start", "", {}, now);
    }
    session.last = now;
    write("sessionStorage", SESSION_KEY, JSON.stringify({ id: session.id, last: session.last }));
    return session;
  }

  // ---- context
  var provider = null;
  var utm = {};
  var referrerHost = "";
  (function captureSource() {
    try {
      var params = new URLSearchParams(window.location.search);
      ["source", "medium", "campaign", "term", "content"].forEach(function (key) {
        var v = params.get("utm_" + key);
        if (v) utm[key] = v.slice(0, 80);
      });
      if (document.referrer) {
        var host = new URL(document.referrer).hostname;
        if (host && host !== window.location.hostname) referrerHost = host.slice(0, 120);
      }
    } catch (_) { /* ignore */ }
  })();

  function viewportBucket() {
    var w = window.innerWidth || 0;
    return w < 480 ? "xs<480" : w < 768 ? "sm<768" : w < 1024 ? "md<1024" : w < 1440 ? "lg<1440" : "xl>=1440";
  }
  function displayMode() {
    try { return window.matchMedia("(display-mode: standalone)").matches ? "standalone" : "browser"; } catch (_) { return ""; }
  }
  function context() {
    var extra = {};
    try { extra = (provider && provider()) || {}; } catch (_) { extra = {}; }
    var conn = navigator.connection && navigator.connection.effectiveType;
    return {
      visitor_id: visitorId(), session_id: touchSession().id, new_visitor: newVisitor,
      language: navigator.language || "",
      timezone: (function () { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (_) { return ""; } })(),
      viewport: viewportBucket(), display_mode: displayMode(), connection: conn || "",
      referrer_host: referrerHost, utm: utm, automated: navigator.webdriver === true,
      school: extra.school || "", signed_in: Boolean(extra.signedIn), school_basis: extra.schoolBasis || "",
    };
  }

  // ---- queue and transport
  var queue = [];
  var timer = null;
  function queueRaw(name, route, props, at) {
    if (queue.length >= MAX_QUEUE) queue.shift();
    queue.push({ n: name, r: route || "", ts: at || Date.now(), p: props || {} });
  }
  function track(name, props, route) {
    if (!active()) return false;
    try {
      touchSession();
      queueRaw(name, route === undefined ? currentRoute() : route, props || {});
      if (queue.length >= BATCH) flush(false); else schedule();
      return true;
    } catch (_) { return false; }
  }
  function schedule() {
    if (timer) return;
    timer = window.setTimeout(function () { timer = null; flush(false); }, FLUSH_MS);
  }
  function flush(useBeacon) {
    if (!queue.length || !active()) { queue = active() ? queue : []; return; }
    var taken = queue.splice(0, BATCH);
    var now = Date.now();
    var body = JSON.stringify({
      v: 1, context: context(),
      events: taken.map(function (e) { return { n: e.n, r: e.r, a: Math.max(0, now - e.ts), p: e.p }; }),
    });
    var sent = false;
    if (useBeacon && navigator.sendBeacon) {
      try { sent = navigator.sendBeacon(ENDPOINT, new Blob([body], { type: "application/json" })); } catch (_) { sent = false; }
    }
    if (!sent) {
      try {
        window.fetch(ENDPOINT, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: body,
          keepalive: Boolean(useBeacon), credentials: "omit",
        }).then(function (response) {
          if (response.status >= 500) requeue(taken);
        }, function () { requeue(taken); });
      } catch (_) { requeue(taken); }
    }
    if (queue.length) schedule();
  }
  var retries = 0;
  function requeue(events) {
    if (retries++ > 3) return;
    queue = events.concat(queue).slice(-MAX_QUEUE);
    schedule();
  }

  // ---- routes, page views, engagement
  function currentRoute() {
    var hash = (window.location.hash || "").replace(/^#/, "");
    var name = hash.split(/[=?&/]/)[0] || "home";
    var view = "";
    try { view = new URLSearchParams(window.location.search).get("view") || ""; } catch (_) { view = ""; }
    return name === "partners" && view ? "partners:" + view.slice(0, 16) : name.slice(0, 60);
  }
  function routeProps() {
    var hash = decodeURIComponent((window.location.hash || "").replace(/^#/, "")).split(/[?&]/)[0];
    var props = {};
    var m = /^(school|board)=(.+)$/.exec(hash);
    if (m) props[m[1]] = m[2].slice(0, 80);
    return props;
  }
  var page = null;
  var lastActivity = Date.now();
  var maxScroll = 0;
  function startPage() {
    touchSession();
    page = { route: currentRoute(), hash: window.location.hash || "", active: 0 };
    maxScroll = 0;
    var props = routeProps();
    props.title = (document.title || "").slice(0, 100);
    props.entry = Boolean(session && session.entry);
    if (session) session.entry = false;
    track("page_view", props, page.route);
  }
  // Reports the time and scroll depth gathered so far and starts counting again, so a visitor who
  // switches tabs and comes back is still measured.
  function reportEngagement() {
    if (!page) return;
    if (page.active >= 1000 || maxScroll > 0) {
      track("engagement", { active_ms: page.active, max_scroll_pct: maxScroll }, page.route);
    }
    page.active = 0;
    maxScroll = 0;
  }
  function endPage() {
    reportEngagement();
    page = null;
  }
  function routeChanged() {
    var next = currentRoute();
    var hash = window.location.hash || "";
    if (page && page.route === next && (next !== "school" || page.hash === hash)) return;
    endPage();
    startPage();
  }
  window.setInterval(function () {
    if (page && document.visibilityState === "visible" && Date.now() - lastActivity < IDLE_MS) page.active += 1000;
  }, 1000);
  ["mousemove", "keydown", "touchstart", "wheel"].forEach(function (type) {
    window.addEventListener(type, function () { lastActivity = Date.now(); }, { passive: true, capture: true });
  });
  var scrollTick = 0;
  window.addEventListener("scroll", function () {
    lastActivity = Date.now();
    var now = Date.now();
    if (now - scrollTick < 250) return;
    scrollTick = now;
    var height = Math.max(document.documentElement.scrollHeight, 1);
    var depth = Math.round(((window.scrollY || 0) + window.innerHeight) / height * 100);
    if (depth > maxScroll) maxScroll = Math.min(100, depth);
  }, { passive: true });

  var routeTimer = null;
  function scheduleRouteChanged() {
    if (routeTimer) return;
    routeTimer = window.setTimeout(function () {
      routeTimer = null;
      routeChanged();
    }, 30);
  }
  function patchHistory(method) {
    var original = window.history[method];
    if (typeof original !== "function") return;
    window.history[method] = function () {
      var before = currentRoute();
      var result = original.apply(this, arguments);
      if (currentRoute() !== before || (arguments.length >= 3 && arguments[2])) scheduleRouteChanged();
      return result;
    };
  }
  patchHistory("pushState");
  patchHistory("replaceState");
  window.addEventListener("hashchange", scheduleRouteChanged);
  window.addEventListener("popstate", scheduleRouteChanged);

  // ---- clicks
  // Attribute values can be record ids (a post, a conversation), so only these harmless ones are kept.
  var SAFE_VALUE_KEYS = { "data-detail-target": 1, "data-community-view": 1, "data-calendar-provider": 1,
    "data-document-type": 1, "data-partner-view": 1, "data-home-school": 1, "data-home-landing-school": 1,
    "data-partner-sort": 1 };
  var DATA_NOISE = { "data-tooltip": 1, "data-lucide": 1, "data-icon": 1, "data-school-name": 1 };
  function dataKey(el) {
    for (var i = 0; i < el.attributes.length; i += 1) {
      var attr = el.attributes[i];
      if (attr.name.indexOf("data-") === 0 && !DATA_NOISE[attr.name]) return { key: attr.name, value: attr.value };
    }
    return null;
  }
  function label(el) {
    var text = el.getAttribute("aria-label") || el.getAttribute("title") || el.textContent || "";
    return text.replace(/\s+/g, " ").trim().slice(0, 40);
  }
  function surface(el) {
    if (el.closest("#partner-map-preview, .partner-map")) return "map";
    if (el.closest(".discovery-candidate, #favorite-list")) return "favorites";
    if (el.closest("#school-detail-view, #school-detail-content")) return "school_page";
    if (el.closest("#partner-table")) return "list";
    if (el.closest("#home-landing")) return "home";
    if (el.closest("#community-hub")) return "forum";
    return "other";
  }
  var SEMANTIC = [
    [".school-detail-trigger, a[href^='#school=']", "school_open", function (el) {
      var name = el.getAttribute("data-school-name");
      if (!name) {
        try { name = decodeURIComponent((el.getAttribute("href") || "").replace(/^#school=/, "")); } catch (_) { name = ""; }
      }
      return { school: name, surface: surface(el) };
    }],
    [".favorite-toggle", "favorite_toggle", function (el) { return { school: el.getAttribute("data-school-name"), saved: el.getAttribute("aria-pressed") !== "true", surface: surface(el) }; }],
    ["[data-partner-view]", "view_switch", function (el) { return { view: el.getAttribute("data-partner-view") }; }],
    ["[data-oauth-provider]", "auth_start", function (el) { return { provider: el.getAttribute("data-oauth-provider") }; }],
    ["[data-open-auth], #account-button, #mobile-account-button, #global-mobile-account-button", "auth_dialog_open", function () { return {}; }],
    ["[data-home-school], [data-home-landing-school]", "school_pick", function (el) { return { school: el.getAttribute("data-home-school") || el.getAttribute("data-home-landing-school") }; }],
    ["#advisor-submit", "advisor_submit", function () { return {}; }],
    ["[data-generated-document-action], [data-download-application-again], [data-application-packet-template], [data-application-review-template], [data-open-application-template], [data-application-copy-template], [data-application-status-template]", "document_action", function (el) { var d = dataKey(el); return { action: d ? d.key.slice(5) : "unknown" }; }],
    ["[data-enable-calendar-sync], [data-download-calendar-event], [data-calendar-provider], [data-copy-calendar-url], [data-calendar-sync-now]", "calendar_action", function (el) { var d = dataKey(el); return { action: d ? d.key.slice(5) : "unknown" }; }],
    ["[data-open-planning], [data-planning-target]", "planning_action", function (el) { var d = dataKey(el); return { action: d ? d.key.slice(5) : "unknown" }; }],
    ["[data-open-global-community-composer]", "community_composer_open", function () { return {}; }],
    ["[data-global-community-topic]", "community_topic", function (el) { return { topic: el.getAttribute("data-global-community-topic") }; }],
    ["[data-follow-board]", "board_follow", function (el) { return { board: el.getAttribute("data-follow-board") }; }],
    ["#theme-toggle", "theme_toggle", function () { return {}; }],
  ];
  var DOWNLOAD = /\.(pdf|docx?|xlsx?|pptx?|zip|csv|ics)$/i;
  var recentClicks = [];
  var lastRage = 0;

  function onClick(event) {
    if (!active() || !(event.target instanceof Element)) return;
    var el = event.target;
    if (el.closest("[data-analytics-ignore]") || el.closest("input[type=password], textarea")) return;
    for (var i = 0; i < SEMANTIC.length; i += 1) {
      var hit = el.closest(SEMANTIC[i][0]);
      if (hit) {
        if (SEMANTIC[i][1] === "auth_start") {
          var consent = document.getElementById("terms-consent");
          if (hit.disabled || (consent && !consent.checked)) return;
        }
        var props = SEMANTIC[i][2](hit);
        var key = dataKey(hit);
        props.target = hit.id || (key ? key.key : hit.tagName.toLowerCase());
        track(SEMANTIC[i][1], props);
        if (SEMANTIC[i][1] === "auth_start") flush(true);
        return;
      }
    }
    var anchor = el.closest("a[href]");
    if (anchor) {
      try {
        var url = new URL(anchor.href, window.location.href);
        if (/^(mailto|tel):/i.test(anchor.href)) return;
        var path = url.pathname.slice(0, 100);
        if (url.origin !== window.location.origin) {
          var school = (window.__uniwayCurrentSchool && window.__uniwayCurrentSchool()) || "";
          track("outbound_click", { host: url.hostname, path: path, school: school, label: label(anchor) });
          if (DOWNLOAD.test(url.pathname)) track("file_download", { ext: url.pathname.split(".").pop().toLowerCase(), host: url.hostname, path: path, school: school });
          return;
        }
        if (anchor.hasAttribute("download") || DOWNLOAD.test(url.pathname)) {
          track("file_download", { ext: url.pathname.split(".").pop().toLowerCase(), host: url.hostname, path: path });
          return;
        }
      } catch (_) { /* fall through to a plain click */ }
    }
    var target = el.closest("button, a, summary, [role=button], [role=tab], [role=link], label[for]");
    if (!target) return;
    var d = dataKey(target);
    var descriptor = target.id || (d ? d.key : "") || (target.className && String(target.className).split(" ")[0]) || target.tagName.toLowerCase();
    track("click", { target: descriptor, value: d && SAFE_VALUE_KEYS[d.key] ? d.value.slice(0, 60) : "", label: label(target) });
    var now = Date.now();
    recentClicks = recentClicks.filter(function (c) { return now - c.at < 1000; });
    recentClicks.push({ at: now, target: descriptor });
    var same = recentClicks.filter(function (c) { return c.target === descriptor; }).length;
    if (same >= 3 && now - lastRage > 3000) {
      lastRage = now;
      track("rage_click", { target: descriptor });
    }
  }
  document.addEventListener("click", onClick, true);

  // ---- search and filters
  var searchTimer = null;
  var lastSearch = "";
  document.addEventListener("input", function (event) {
    var el = event.target;
    if (!active() || !el || el.id !== "partner-search") return;
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(function () {
      var q = (el.value || "").trim();
      if (q.length < 2 || q === lastSearch) return;
      lastSearch = q;
      window.setTimeout(function () {
        var table = document.getElementById("partner-table");
        var results = table && table.dataset.resultCount !== undefined ? Number(table.dataset.resultCount) : null;
        track("search", { q: q, results: results, surface: "partners" });
      }, 200);
    }, 900);
  }, true);
  document.addEventListener("change", function (event) {
    var el = event.target;
    if (!active() || !el) return;
    if (/^(availability|country|college|degree)-filter$/.test(el.id || "")) {
      track("filter_change", { filter: el.id.replace(/-filter$/, ""), value: (el.value || "all").slice(0, 60) });
      return;
    }
    var facet = el.getAttribute && el.getAttribute("data-pr-facet");
    if (facet) {
      track("filter_change", { filter: facet, value: el.checked ? String(el.getAttribute("value") || "all").slice(0, 60) : "all" });
    }
  }, true);

  // ---- errors and performance
  var errorCount = 0;
  window.addEventListener("error", function (event) {
    if (!active() || errorCount >= 10 || !event.message || /ResizeObserver loop/i.test(event.message)) return;
    var source = String(event.filename || "").split("?")[0].split("/").pop();
    if (/^Script error\.?$/i.test(event.message) && !source && !event.lineno) return;
    errorCount += 1;
    track("js_error", { message: String(event.message).slice(0, 200), source: source, line: event.lineno || 0 });
  });
  window.addEventListener("unhandledrejection", function (event) {
    if (!active() || errorCount >= 10) return;
    errorCount += 1;
    var reason = event.reason;
    track("unhandled_rejection", { message: String((reason && reason.message) || reason || "").slice(0, 200) });
  });
  (function watchFetch() {
    var native = window.fetch;
    if (typeof native !== "function") return;
    window.fetch = function (input) {
      var promise = native.apply(this, arguments);
      try {
        var raw = typeof input === "string" ? input : (input && input.url) || "";
        var url = new URL(raw, window.location.href);
        if (url.origin === window.location.origin && url.pathname !== ENDPOINT) {
          promise.then(function (response) {
            if (response.status >= 500) track("api_error", { path: url.pathname.slice(0, 100), status: response.status });
          }, function (error) {
            if (!error || error.name !== "AbortError") track("api_error", { path: url.pathname.slice(0, 100), status: 0 });
          });
        }
      } catch (_) { /* never interfere with the real request */ }
      return promise;
    };
  })();

  var vitals = {};
  var vitalsSent = false;
  // Use Google's maintained algorithms: CLS session windows and INP interaction handling
  // differ from a lifetime sum of shifts / the longest event duration.
  if (active()) {
    import("/static/vendor/web-vitals/4.2.4/web-vitals.js").then(function (library) {
      var report = function (metric) {
        track("web_vitals", {metric: metric.name.toLowerCase(), value: metric.value});
        flush(document.visibilityState === "hidden");
      };
      library.onLCP(report); library.onINP(report); library.onCLS(report); library.onFCP(report);
    }).catch(function () {});
  }
  function sendVitals() {
    if (vitalsSent) return;
    try {
      var nav = performance.getEntriesByType("navigation")[0];
      if (nav) {
        vitals.ttfb = nav.responseStart;
        if (nav.loadEventEnd > 0) vitals.load = nav.loadEventEnd;
      }
    } catch (_) { /* ignore */ }
    var keys = Object.keys(vitals);
    if (!keys.length) return;
    vitalsSent = true;
    keys.forEach(function (metric) { track("web_vitals", { metric: metric, value: Math.round(vitals[metric] * 1000) / 1000 }, page ? page.route : ""); });
  }

  function leave() {
    sendVitals();
    reportEngagement();
    flush(true);
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") leave();
  });
  window.addEventListener("pagehide", leave);

  // ---- public API and opt-out control
  function updateToggles() {
    var out = optedOut();
    Array.prototype.forEach.call(document.querySelectorAll("[data-analytics-toggle]"), function (button) {
      button.textContent = out ? "已停用匿名使用統計，點此重新啟用" : "停用匿名使用統計";
    });
  }
  document.addEventListener("click", function (event) {
    var button = event.target instanceof Element && event.target.closest("[data-analytics-toggle]");
    if (!button) return;
    if (optedOut()) {
      erase("localStorage", OPT_OUT_KEY);
      updateToggles();
      if (active()) { startPage(); }
    } else {
      queueRaw("optout", currentRoute(), {});
      flush(true);
      write("localStorage", OPT_OUT_KEY, "1");
      queue = [];
      updateToggles();
    }
  });

  window.UniWayAnalytics = {
    track: track,
    enabled: active,
    optOut: function () { write("localStorage", OPT_OUT_KEY, "1"); queue = []; updateToggles(); },
    optIn: function () { erase("localStorage", OPT_OUT_KEY); updateToggles(); },
    setContextProvider: function (fn) { provider = typeof fn === "function" ? fn : null; },
    flush: function () { flush(false); },
  };

  function begin() {
    updateToggles();
    if (!active()) return;
    startPage();
    // The visitor's first batch always reports the page they landed on, even if they leave quickly.
    schedule();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", begin);
  else begin();
})();

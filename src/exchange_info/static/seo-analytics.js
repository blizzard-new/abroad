/* Optional GA4: no Google script, cookies or requests before explicit consent.
 * Never send account data, school selections, raw query/hash/referrer or form text. */
(function () {
  "use strict";
  var node = document.querySelector('meta[name="uniway-ga4-id"]');
  var id = node && node.content;
  if (!/^G-[A-Z0-9]{6,20}$/.test(id || "")) return;
  var KEY = "uniway-ga4-consent-v1", MAX_AGE = 180 * 86400000;
  var approved = false, loaded = false, started = false, panel;
  function read(key) { try { return localStorage.getItem(key); } catch (_) { return null; } }
  function blocked() {
    return navigator.globalPrivacyControl === true || navigator.doNotTrack === "1"
      || window.doNotTrack === "1" || read("uniway-analytics-optout") === "1";
  }
  function consent() {
    try { var v = JSON.parse(read(KEY)); return v && v.allowed === true && Date.now() - v.at < MAX_AGE && Date.now() >= v.at; }
    catch (_) { return false; }
  }
  function path() {
    // Only known public route shapes; private URL fragments and query strings are never sent.
    var p = location.pathname;
    return /^(\/|\/schools(?:\/[a-z]+(?:\/partners\/[a-f0-9]{20})?)?|\/destinations(?:\/[a-z-]+)?|\/guides(?:\/[a-z-]+)?|\/editorial-policy)$/.test(p) ? p : "/";
  }
  function routeType() {
    var p = path();
    return p.indexOf("/partners/") >= 0 ? "partner" : p.split("/")[1] || "home";
  }
  function referrerOrigin() {
    try { return document.referrer ? new URL(document.referrer).origin + "/" : ""; }
    catch (_) { return ""; }
  }
  var allowedEvents = {open_school_planner: 1, compare_universities: 1, click_official_source: 1, view_application_guide: 1, web_vitals: 1};
  function send(name, values) {
    if (!approved || blocked() || !loaded || !allowedEvents[name]) return;
    var safe = {page_location: location.origin + path(), page_referrer: referrerOrigin(), page_title: "UniWay " + routeType(), page_type: routeType()};
    if (name === "compare_universities") safe.school_count = Math.max(2, Math.min(3, Number(values && values.school_count) || 2));
    if (name === "click_official_source" && values && /^[a-z0-9.-]+$/.test(values.source_host || "")) safe.source_host = values.source_host;
    if (name === "web_vitals" && values && /^(LCP|INP|CLS)$/.test(values.metric) && Number.isFinite(values.value)) {
      safe.metric_name = values.metric; safe.metric_value = values.value;
    }
    window.gtag("event", name, safe);
  }
  function start() {
    if (!approved || blocked() || started) return;
    started = true;
    window["ga-disable-" + id] = false;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("consent", "default", {analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied"});
    window.gtag("js", new Date());
    window.gtag("config", id, {send_page_view: false, allow_google_signals: false, allow_ad_personalization_signals: false,
      page_location: location.origin + path(), page_referrer: referrerOrigin(), page_title: "UniWay " + routeType(), cookie_expires: MAX_AGE / 1000, cookie_flags: "SameSite=Lax;Secure"});
    var script = document.createElement("script");
    script.async = true; script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
    // Queue only sanitized page data. GA4 enhanced measurement must be disabled in the stream.
    document.head.appendChild(script); loaded = true;
    window.gtag("event", "page_view", {page_location: location.origin + path(), page_referrer: referrerOrigin(), page_title: "UniWay " + routeType(), page_type: routeType()});
    if (path().indexOf("/guides/") === 0) send("view_application_guide");
    import("/static/vendor/web-vitals/4.2.4/web-vitals.js").then(function (vitals) {
      var report = function (m) { send("web_vitals", {metric: m.name, value: m.value}); };
      vitals.onLCP(report); vitals.onINP(report); vitals.onCLS(report);
    }).catch(function () {});
  }
  function clearCookies() {
    var domains = ["", location.hostname, "." + location.hostname];
    var parts = location.hostname.split(".");
    while (parts.length > 2) { parts.shift(); domains.push("." + parts.join(".")); }
    document.cookie.split(";").forEach(function (cookie) {
      var name = cookie.trim().split("=")[0];
      if (!/^_ga(?:_|$)/.test(name)) return;
      domains.forEach(function (domain) { document.cookie = name + "=; Max-Age=0; path=/; SameSite=Lax; Secure" + (domain ? "; domain=" + domain : ""); });
    });
  }
  function revoke() {
    approved = false; window["ga-disable-" + id] = true;
    if (window.dataLayer) window.dataLayer.length = 0;
    clearCookies();
  }
  function update() {
    panel.querySelector("[data-ga-status]").textContent = blocked() ? "依你的隱私設定，Google 使用分析已停用。" : approved ? "你已允許 Google 使用分析，可隨時撤回。" : "Google 使用分析未啟用；你仍可使用所有功能。";
    panel.querySelector("[data-ga-allow]").disabled = blocked() || approved;
  }
  function choose(allow) {
    approved = Boolean(allow) && !blocked();
    try { localStorage.setItem(KEY, JSON.stringify({allowed: approved, at: Date.now()})); } catch (_) {}
    if (approved) {
      if (started) location.reload(); else start();
    } else revoke();
    update();
  }
  panel = document.createElement("section"); panel.className = "seo-analytics-preferences";
  panel.setAttribute("aria-label", "Google 使用分析偏好");
  panel.innerHTML = '<p>選擇是否允許 Google Analytics 使用 Cookie 記錄公開頁面瀏覽、選校功能使用與效能，協助改善網站。資料會傳送給 Google，可能於境外處理。<a href="/privacy#optional-ga4">了解隱私說明</a></p><p data-ga-status role="status"></p><button type="button" data-ga-allow>允許 Google 使用分析</button><button type="button" data-ga-deny>不允許／撤回同意</button>';
  (document.querySelector("footer") || document.body).appendChild(panel);
  panel.querySelector("[data-ga-allow]").addEventListener("click", function () { choose(true); });
  panel.querySelector("[data-ga-deny]").addEventListener("click", function () { choose(false); });
  approved = consent() && !blocked(); update(); if (approved) start(); else revoke();
  document.addEventListener("click", function (event) {
    var target = event.target instanceof Element && event.target.closest("a,[data-analytics-toggle]");
    if (!target) return;
    if (target.hasAttribute("data-analytics-toggle")) { setTimeout(function () { if (blocked()) { revoke(); update(); } }, 0); return; }
    var url; try { url = new URL(target.href, location.href); } catch (_) { return; }
    if (url.origin === location.origin && url.pathname === "/" && /^(#partners|#school=)/.test(url.hash)) send("open_school_planner");
    if (target.hasAttribute("data-official-source") && /https?:/.test(url.protocol)) send("click_official_source", {source_host: url.hostname});
  });
  document.addEventListener("uniway:compare", function (event) {
    if (event.detail && event.detail.school_count >= 2) send("compare_universities", {school_count: event.detail.school_count});
  });
  window.addEventListener("storage", function () { if (!consent() || blocked()) revoke(); update(); });
})();

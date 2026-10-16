/* Half-globe backdrop for the first screen of #home.
   COBE (vendored, window.UniWayCobe) draws the partner cities of the chosen school as dots on a slowly turning globe whose
   lower half sits below the hero. The globe fades away as the page scrolls down. Nothing here is needed to read the page:
   without WebGL, on a software renderer, or on a machine that cannot keep up, the hero keeps its flat SVG map
   (data-state="fallback" on the host, and data-reason says why, also logged to the console).
   platform-home.js calls UniWayGlobeBackdrop.setMarkers() whenever the partner list changes. */
window.UniWayGlobeBackdrop = (() => {
  "use strict";
  // COBE phi that brings Taiwan (121.6°E) to the middle of the globe. The globe sits on the hero's bottom edge, so the tilt
  // leans its top away to lift Taiwan well above the horizon line instead of leaving it right on it.
  const FACE_TAIWAN = 2.591;
  const TILT = -0.3;
  const TAIWAN = [25.04, 121.56];
  // Radians per millisecond: a full turn takes about 35 seconds.
  const SPIN = 0.00018;
  // The shader holds 64 markers.
  const MAX_MARKERS = 63;
  const MAX_DPR = 1.25;
  // The globe is scenery, so it draws at 30 frames a second, and it gives way to the flat map when a machine cannot keep up
  // (no GPU, or a software renderer). That is judged on a calm page: draws while the loading screen is up, and the first
  // second after it, are not counted, because the page boots with long stalls of its own and one of them must never take
  // the globe away; the verdict is the median gap between SAMPLE_INTERVALS draws, which is above SLOW_MEDIAN_MS only when
  // the globe is sustainably slower than about 13 frames a second.
  const FRAME_MS = 33;
  const SETTLE_MS = 1200;
  const SAMPLE_INTERVALS = 30;
  const SLOW_MEDIAN_MS = 75;
  const SOFTWARE_RENDERER = /swiftshader|llvmpipe|softpipe|software|basic render/i;
  // COBE draws its sphere with a radius of 0.4 × the canvas height × scale.
  const RADIUS_PER_HEIGHT = 0.4;
  const PALETTE = {
    light: { dark: 0, base: [0.9, 0.96, 0.99], glow: [1, 1, 1], marker: [0.09, 0.48, 0.63], taiwan: [0.66, 0.24, 0.22], map: 0.62, diffuse: 1.1, size: 1.4 },
    dark: { dark: 1, base: [0.1, 0.2, 0.32], glow: [0.1, 0.28, 0.42], marker: [0.5, 0.82, 0.93], taiwan: [1, 0.71, 0.65], map: 3, diffuse: 1.2, size: 1 },
  };
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  let host = null, canvas = null, globe = null, markers = [], phi = FACE_TAIWAN;
  let theme = "light", sized = "", resizeTimer = 0, scrollFrame = 0, visible = false, failed = false, last = 0;
  let loop = 0, running = false, lastDraw = 0, prevDraw = 0, settledAt = 0, judged = false, rendererName = "";
  const intervals = [];

  const currentTheme = () => (document.documentElement.dataset.theme === "dark" ? "dark" : "light");

  function markerList() {
    const palette = PALETTE[theme];
    const list = markers.slice(0, MAX_MARKERS).map((city) => ({
      location: [city.lat, city.lon],
      size: (0.04 + Math.min(city.weight, 6) * 0.012) * palette.size,
    }));
    list.push({ location: TAIWAN, size: 0.09 * palette.size, color: palette.taiwan });
    return list;
  }

  // Software rasterisers (SwiftShader, llvmpipe) would spend the CPU on a sphere shader, so they get the flat map.
  let hardware = null;
  function hasHardwareGl() {
    if (hardware !== null) return hardware;
    hardware = false;
    try {
      const gl = document.createElement("canvas").getContext("webgl");
      if (!gl) return hardware;
      const info = gl.getExtension("WEBGL_debug_renderer_info");
      const renderer = info ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)) : "";
      gl.getExtension("WEBGL_lose_context")?.loseContext();
      rendererName = renderer;
      hardware = !SOFTWARE_RENDERER.test(renderer);
    } catch { /* no usable WebGL */ }
    return hardware;
  }

  function stop() {
    window.cancelAnimationFrame(loop);
    loop = 0;
    running = false;
    if (!globe) return;
    try { globe.destroy(); } catch { /* the context may already be gone */ }
    globe = null;
    sized = "";
  }

  function fallBack(reason) {
    failed = true;
    stop();
    host?.setAttribute("data-state", "fallback");
    host?.setAttribute("data-reason", reason);
    console.info(`[UniWayGlobeBackdrop] showing the flat map: ${reason}`);
  }

  const median = (list) => { const sorted = [...list].sort((a, b) => a - b); return sorted[Math.floor(sorted.length / 2)]; };
  // Too slow only when there are enough draws to tell and half of them were later than SLOW_MEDIAN_MS.
  const isTooSlow = (gaps) => gaps.length >= SAMPLE_INTERVALS && median(gaps) > SLOW_MEDIAN_MS;

  // Called with each draw's time; decides once, after the page has settled, whether this machine keeps up.
  function judge(now) {
    if (document.getElementById("boot-splash")) { settledAt = 0; prevDraw = 0; return; }
    if (!settledAt) settledAt = now + SETTLE_MS;
    if (now < settledAt) { prevDraw = 0; return; }
    if (prevDraw) intervals.push(now - prevDraw);
    prevDraw = now;
    if (intervals.length >= SAMPLE_INTERVALS) {
      judged = true;
      if (isTooSlow(intervals)) fallBack(`slow:${Math.round(median(intervals))}ms`);
    }
  }

  function start() {
    if (failed || !host || !visible) return;
    const width = host.clientWidth, height = host.clientHeight;
    if (width < 40 || height < 40) return;
    const key = `${width}x${height}x${window.devicePixelRatio}`;
    if (globe && key === sized) return;
    stop();
    if (typeof window.UniWayCobe !== "function") { fallBack("no-cobe"); return; }
    if (!hasHardwareGl()) { fallBack(`software:${rendererName.slice(0, 60) || "no-webgl"}`); return; }
    const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
    // The globe's centre sits on the bottom edge of the canvas, so only its upper half is drawn.
    const radius = Math.min(width * 0.49, height / 1.05);
    const scale = radius / (RADIUS_PER_HEIGHT * height);
    const palette = PALETTE[theme];
    try {
      globe = window.UniWayCobe(canvas, {
        width: width * dpr,
        height: height * dpr,
        devicePixelRatio: dpr,
        phi,
        theta: TILT,
        dark: palette.dark,
        diffuse: palette.diffuse,
        // Dense enough that the dots stay small on a globe this large.
        mapSamples: 40000,
        mapBrightness: palette.map,
        // COBE leaves these undefined unless they are given, and some GL drivers then draw a black disc.
        mapBaseBrightness: 0.05,
        opacity: 1,
        baseColor: palette.base,
        markerColor: palette.marker,
        glowColor: palette.glow,
        scale,
        // COBE applies the offset after scaling, so a centre on the bottom edge needs offset = height / scale.
        offset: [0, (height * dpr) / scale],
        markers: markerList(),
        onRender: (frame) => {
          const now = performance.now();
          // It holds still behind the loading screen, so the first thing anyone sees is Taiwan facing them.
          if (!reduceMotion.matches && last && !document.getElementById("boot-splash")) phi += Math.min(now - last, 64) * SPIN;
          last = now;
          const current = PALETTE[theme];
          frame.phi = phi;
          frame.dark = current.dark;
          frame.diffuse = current.diffuse;
          frame.mapBrightness = current.map;
          frame.baseColor = current.base;
          frame.markerColor = current.marker;
          frame.glowColor = current.glow;
          frame.markers = markerList();
        },
      });
    } catch (error) {
      fallBack(`error:${String(error?.message || error).slice(0, 60)}`);
      return;
    }
    // COBE starts its own animation loop; this file paces the frames itself, so that one is switched off.
    globe.toggle(false);
    sized = key;
    host.setAttribute("data-state", "ready");
    canvas.style.opacity = "1";
    last = 0;
    prevDraw = 0;
    // A still frame is enough for people who asked for less motion.
    globe.render();
    applyRunState();
  }

  function tick(now) {
    loop = 0;
    if (!running || !globe) return;
    if (now - lastDraw >= FRAME_MS - 2) {
      if (!judged) {
        judge(now);
        if (!globe) return;
      }
      lastDraw = now;
      globe.render();
    }
    loop = window.requestAnimationFrame(tick);
  }

  function applyRunState() {
    if (!globe) return;
    const progress = Number(host.style.getPropertyValue("--globe-progress")) || 0;
    const shouldRun = visible && !document.hidden && progress < 1 && !reduceMotion.matches;
    if (shouldRun === running) return;
    running = shouldRun;
    window.cancelAnimationFrame(loop);
    loop = 0;
    if (running) {
      last = 0;
      // The gap across a pause is not a draw time.
      prevDraw = 0;
      loop = window.requestAnimationFrame(tick);
    }
  }

  // One redraw after something changed while the globe was standing still.
  function redrawOnce() {
    if (globe && !running) globe.render();
  }

  function updateFade() {
    scrollFrame = 0;
    if (!host) return;
    const scrolled = window.scrollY || document.documentElement.scrollTop || 0;
    // Gone once the page has moved about two thirds of a screen.
    const progress = Math.min(1, Math.max(0, scrolled / (window.innerHeight * 0.66)));
    host.style.setProperty("--globe-progress", progress.toFixed(3));
    applyRunState();
  }

  function onScroll() {
    if (!scrollFrame) scrollFrame = window.requestAnimationFrame(updateFade);
  }

  function onResize() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(start, 140);
  }

  function setMarkers(cities) {
    markers = [...cities].sort((a, b) => b.weight - a.weight);
    if (globe && reduceMotion.matches) redrawOnce();
  }

  function init() {
    host = document.querySelector("[data-home-globe]");
    canvas = host?.querySelector("canvas");
    if (!host || !canvas) return;
    theme = currentTheme();
    host.setAttribute("data-state", "idle");
    new IntersectionObserver((entries) => {
      visible = entries.some((entry) => entry.isIntersecting);
      if (visible) start();
      applyRunState();
    }).observe(host);
    new ResizeObserver(onResize).observe(host);
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("visibilitychange", applyRunState);
    reduceMotion.addEventListener?.("change", () => { stop(); start(); });
    new MutationObserver(() => {
      const next = currentTheme();
      if (next === theme) return;
      theme = next;
      redrawOnce();
    }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    updateFade();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
  return { setMarkers, isTooSlow };
})();

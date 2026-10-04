/* Loaded only when the partner map is visible. The app owns all filter state. */
const VENDOR = "/static/vendor/maplibre/5.24.0";
const ASSETS = "/static/assets/partner-map";
const LAND_COLORS = {
  Asia: ["#add3a1", "#c8db97", "#91c9b4", "#bad8a7"],
  Europe: ["#c2b4df", "#d4c3e4", "#b5c5e3", "#c9bee8"],
  Africa: ["#ecd08b", "#e4ba82", "#edda9e", "#dbbc8d"],
  "North America": ["#e9afa0", "#ebc296", "#e5b7bc", "#edc7b1"],
  "South America": ["#99c9ad", "#b8d49b", "#91c5b8", "#b2d1ac"],
  Oceania: ["#e9bf85", "#d3d29b", "#bbd2ac", "#e3cc9d"],
  Antarctica: ["#ecf4f7", "#ecf4f7", "#ecf4f7", "#ecf4f7"],
};
const EMPTY = () => ({ type: "FeatureCollection", features: [] });
let enginePromise;

function graticule() {
  const features = [];
  const line = (coordinates) => features.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates } });
  for (let lat = -60; lat <= 60; lat += 30) line(Array.from({ length: 181 }, (_, i) => [-180 + i * 2, lat]));
  for (let lng = -180; lng < 180; lng += 30) line(Array.from({ length: 85 }, (_, i) => [lng, -84 + i * 2]));
  return { type: "FeatureCollection", features };
}

export function hasCoordinates(item) {
  const p = item?.location;
  return p?.geocode_status === "verified" && Number.isFinite(p.latitude) && Number.isFinite(p.longitude)
    && Math.abs(p.latitude) <= 90 && Math.abs(p.longitude) <= 180;
}

export function pointsFor(partners) {
  return {
    type: "FeatureCollection",
    features: partners.filter(hasCoordinates).map((item) => ({
      type: "Feature", id: item.school_name,
      properties: { name: item.school_name, country: item.country || "", city: item.location.city || "" },
      geometry: { type: "Point", coordinates: [item.location.longitude, item.location.latitude] },
    })),
  };
}

// Smallest longitudinal interval, including countries across the date line.
export function coordinateBounds(points) {
  if (!points.length) return null;
  const lngs = points.map(([lng]) => (lng + 360) % 360).sort((a, b) => a - b);
  let gap = -1, start = lngs[0];
  for (let i = 0; i < lngs.length; i++) {
    const next = lngs[(i + 1) % lngs.length] + (i === lngs.length - 1 ? 360 : 0);
    if (next - lngs[i] > gap) { gap = next - lngs[i]; start = next % 360; }
  }
  if (start > 180) start -= 360;
  const lats = points.map((p) => p[1]);
  return [[start, Math.min(...lats)], [start + 360 - gap, Math.max(...lats)]];
}

function loadEngine(fresh = false) {
  if (enginePromise) return enginePromise;
  enginePromise = Promise.all([
    new Promise((resolve, reject) => {
      if (window.maplibregl && !fresh) return resolve(window.maplibregl);
      const script = document.createElement("script");
      script.src = `${VENDOR}/maplibre-gl-csp.js`;
      const timer = setTimeout(() => { script.remove(); reject(new Error("地圖引擎載入逾時")); }, 20000);
      script.onload = () => { clearTimeout(timer); resolve(window.maplibregl); };
      script.onerror = () => { clearTimeout(timer); script.remove(); reject(new Error("地圖引擎無法載入")); };
      document.head.append(script);
    }),
    new Promise((resolve, reject) => {
      if (document.querySelector("link[data-maplibre-css]")?.sheet) return resolve();
      const link = document.createElement("link");
      link.rel = "stylesheet"; link.href = `${VENDOR}/maplibre-gl.css`; link.dataset.maplibreCss = "true";
      const timer = setTimeout(() => { link.remove(); reject(new Error("地圖樣式載入逾時")); }, 20000);
      link.onload = () => { clearTimeout(timer); resolve(); };
      link.onerror = () => { clearTimeout(timer); link.remove(); reject(new Error("地圖樣式無法載入")); };
      document.head.append(link);
    }),
  ]).then(([engine]) => engine).catch((error) => { enginePromise = null; throw error; });
  return enginePromise;
}

export async function createPartnerMap({ renderPreview, onSchoolSelect = () => {}, onList, onRetry, onIcons, freshEngine = false }) {
  const $ = (selector) => document.querySelector(selector);
  const canvasHost = $("#partner-globe");
  const status = $("#partner-map-status");
  const preview = $("#partner-map-preview");
  const select = $("#map-school-select");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const duration = () => reducedMotion.matches ? 0 : (window.UniWayMotion?.duration("map") || 700);
  const lib = await loadEngine(freshEngine);
  lib.setWorkerUrl(`${VENDOR}/maplibre-gl-csp-worker.js`);
  lib.setWorkerCount(2);
  const abort = new AbortController();
  const fetchTimeout = setTimeout(() => abort.abort(), 15000);
  let countries, lakes, rivers;
  try {
    const read = async (name) => {
      const response = await fetch(`${ASSETS}/${name}.geojson`, { signal: abort.signal });
      if (!response.ok) throw new Error("底圖無法載入");
      return response.json();
    };
    [countries, lakes, rivers] = await Promise.all([read("countries"), read("lakes").catch(EMPTY), read("rivers").catch(EMPTY)]);
  } finally { clearTimeout(fetchTimeout); }
  countries.features.forEach(({ properties: p }) => {
    p.day = (LAND_COLORS[p.continent] || LAND_COLORS.Asia)[Math.abs(p.tone || 0) % 4];
    // Keep the regional hue in dark mode, with lower luminance behind the labels.
    p.night = "#" + p.day.slice(1).match(/../g).map((v) => Math.round(parseInt(v, 16) * .51).toString(16).padStart(2, "0")).join("");
  });
  const labels = { type: "FeatureCollection", features: countries.features.filter((f) => f.properties.name !== "Antarctica").map((f) => ({
    type: "Feature", properties: { name: f.properties.name.normalize("NFD").replace(/[^\x20-\x7E]/g, "") },
    geometry: { type: "Point", coordinates: [f.properties.label_lon, f.properties.label_lat] },
  })) };
  const dark = () => document.documentElement.dataset.theme === "dark";
  const palette = () => dark()
    ? { sea: "#183e60", land: ["get", "night"], border: "#b4cbd3", label: "#f1f6fa", halo: "#243a44", water: "#376784", coast: "#77bbcf", grid: "#9fcce3", sky: "#152b44", horizon: "#6390b2" }
    : { sea: "#79b5d6", land: ["get", "day"], border: "#f7f3dc", label: "#324a59", halo: "#f7f4df", water: "#6aadc9", coast: "#d8efe5", grid: "#eff9ff", sky: "#edf4fa", horizon: "#b7d7e8" };
  const atmosphere = (p) => ({ "sky-color": p.sky, "horizon-color": p.horizon, "sky-horizon-blend": .8, "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, .65, 3, .4, 5, 0] });
  const colors = palette();
  const globalCamera = () => ({ center: [105, 24], zoom: Math.max(.1, 1.68 + Math.log2(Math.min(canvasHost.clientWidth || 580, canvasHost.clientHeight || 580) / 580)), bearing: 0, pitch: 0 });
  let map;
  try {
    map = new lib.Map({
      container: canvasHost, ...globalCamera(), minZoom: .1, maxZoom: 12,
      maxPitch: 45, attributionControl: false, renderWorldCopies: false,
      locale: {
        "Map.Title": "互動地圖", "Marker.Title": "地圖標記", "Popup.Close": "關閉預覽",
        "NavigationControl.ZoomIn": "放大地圖", "NavigationControl.ZoomOut": "縮小地圖",
        "NavigationControl.ResetBearing": "拖曳旋轉地圖，點擊重設北方",
        "AttributionControl.ToggleAttribution": "顯示或收合地圖來源",
        "CooperativeGesturesHandler.WindowsHelpText": "按住 Ctrl 並捲動以縮放地圖",
        "CooperativeGesturesHandler.MacHelpText": "按住 ⌘ 並捲動以縮放地圖",
        "CooperativeGesturesHandler.MobileHelpText": "使用雙指移動地圖"
      },
      canvasContextAttributes: { antialias: true },
      style: {
        version: 8, projection: { type: "globe" }, sky: atmosphere(colors), glyphs: `${ASSETS}/fonts/{fontstack}/{range}.pbf`,
        sources: { countries: { type: "geojson", data: countries }, labels: { type: "geojson", data: labels }, lakes: { type: "geojson", data: lakes }, rivers: { type: "geojson", data: rivers }, graticule: { type: "geojson", data: graticule() } },
        layers: [
          { id: "ocean", type: "background", paint: { "background-color": colors.sea } },
          { id: "graticule", type: "line", source: "graticule", maxzoom: 5, paint: { "line-color": colors.grid, "line-width": .65, "line-opacity": .2 } },
          { id: "coast-shelf", type: "line", source: "countries", paint: { "line-color": colors.coast, "line-width": 5, "line-blur": 2, "line-opacity": .48 } },
          { id: "land", type: "fill", source: "countries", paint: { "fill-color": colors.land } },
          { id: "country-hover", type: "fill", source: "countries", filter: ["==", ["get", "name"], ""], paint: { "fill-color": "#ffffff", "fill-opacity": .18, "fill-opacity-transition": { duration: 180 } } },
          { id: "lakes", type: "fill", source: "lakes", paint: { "fill-color": colors.water } },
          { id: "rivers", type: "line", source: "rivers", minzoom: 1.6, paint: { "line-color": colors.water, "line-width": ["interpolate", ["linear"], ["zoom"], 1, .4, 5, 1.1], "line-opacity": .65 } },
          { id: "borders", type: "line", source: "countries", paint: { "line-color": colors.border, "line-width": ["interpolate", ["linear"], ["zoom"], 1, .55, 5, 1.2], "line-opacity": .85 } },
          { id: "country-labels", type: "symbol", source: "labels", minzoom: 2.2, layout: { "text-field": ["get", "name"], "text-font": ["Poppins Medium"], "text-size": 11, "text-max-width": 8 }, paint: { "text-color": colors.label, "text-halo-color": colors.halo, "text-halo-width": 1.2 } },
        ],
      },
    });
  } catch (error) { canvasHost.replaceChildren(); throw error; }
  let loaded = false, disposed = false, visible = true, failed = false;
  let current = { partners: [], home: null, filterKey: "", country: "" };
  let dataKey = "", cameraKey = null, selectedName = "", lastFocus = null, homeMarker = null, homeKey = "", hoveredName = "";
  let animationFrame = 0, lastFrame = 0, inViewport = true, motionPaused = false, hoveredCountry = "";
  const motionButton = $("#map-motion");
  const panel = $("#partner-map-panel");
  const popup = new lib.Popup({ closeButton: false, closeOnClick: false, offset: 12, maxWidth: "240px" });
  const navigation = new lib.NavigationControl({ showCompass: true, visualizePitch: false });
  map.addControl(navigation, "top-right");
  map.addControl(new lib.AttributionControl({ compact: true, customAttribution: '<a href="https://www.naturalearthdata.com/about/terms-of-use/" target="_blank" rel="noreferrer">Natural Earth</a> · <a href="https://www.wikidata.org/" target="_blank" rel="noreferrer">Wikidata</a> / <a href="https://ror.org/" target="_blank" rel="noreferrer">ROR</a>' }), "bottom-right");
  map.getCanvas().setAttribute("aria-label", "互動全球地圖。方向鍵平移，加减鍵縮放；也可用下方快速定位選單選校。");
  const controlLabels = { ".maplibregl-ctrl-zoom-in": "放大地圖", ".maplibregl-ctrl-zoom-out": "縮小地圖", ".maplibregl-ctrl-compass": "重設北方" };
  Object.entries(controlLabels).forEach(([selector, label]) => { canvasHost.querySelector(selector)?.setAttribute("aria-label", label); });

  function stopMotion() {
    cancelAnimationFrame(animationFrame); animationFrame = 0;
    if (loaded && !disposed) {
      if (map.getLayer("selected-halo")) map.setPaintProperty("selected-halo", "circle-radius", 17);
    }
  }
  function syncMotion() {
    const enabled = !motionPaused && !reducedMotion.matches;
    const active = enabled && visible && inViewport && !document.hidden && !failed;
    panel.dataset.motion = active ? "running" : "paused";
    motionButton.setAttribute("aria-pressed", String(enabled));
    motionButton.textContent = enabled ? "動態效果：開" : "動態效果：關";
    motionButton.disabled = reducedMotion.matches;
    motionButton.title = reducedMotion.matches ? "已依系統偏好減少動態效果" : "切換學校標記的呼吸動畫";
    if (!active || !loaded || !selectedName) return stopMotion();
    if (animationFrame) return;
    const frame = (now) => {
      animationFrame = requestAnimationFrame(frame);
      if (now - lastFrame < 65 || map.isMoving()) return;
      lastFrame = now;
      if (selectedName) map.setPaintProperty("selected-halo", "circle-radius", 17 + Math.sin(now / 550) * 3);
    };
    animationFrame = requestAnimationFrame(frame);
  }
  const toggleMotion = () => { motionPaused = !motionPaused; syncMotion(); };
  motionButton.addEventListener("click", toggleMotion);
  reducedMotion.addEventListener("change", syncMotion);
  document.addEventListener("visibilitychange", syncMotion);
  const intersection = new IntersectionObserver(([entry]) => { inViewport = entry.isIntersecting; syncMotion(); });
  intersection.observe(canvasHost);
  syncMotion();

  function showStatus(title, message, retry = false) {
    status.replaceChildren(); status.hidden = false;
    const strong = document.createElement("strong"); strong.textContent = title;
    const p = document.createElement("p"); p.textContent = message;
    status.append(strong, p);
    const actions = document.createElement("div"); actions.className = "map-status-actions";
    if (retry) {
      const button = document.createElement("button"); button.type = "button"; button.className = "primary-button"; button.textContent = "重新載入地圖"; button.onclick = onRetry; actions.append(button);
    }
    const list = document.createElement("button"); list.type = "button"; list.className = "secondary-button"; list.textContent = "返回列表"; list.onclick = onList; actions.append(list); status.append(actions);
  }

  function closePreview({ restoreFocus = false } = {}) {
    selectedName = ""; preview.hidden = true; select.value = "";
    if (loaded && !disposed) ["selected-school", "selected-halo"].forEach((id) => map.setFilter(id, ["==", ["get", "name"], ""]));
    syncMotion();
    if (restoreFocus) (lastFocus?.isConnected ? lastFocus : map.getCanvas()).focus({ preventScroll: true });
  }

  function drawPreview(item, focus = false) {
    if (!item) return closePreview();
    preview.innerHTML = renderPreview(item); preview.hidden = false;
    preview.querySelector("[data-close-map-preview]").onclick = () => closePreview({ restoreFocus: true });
    onIcons();
    if (focus) preview.querySelector("[data-close-map-preview]")?.focus({ preventScroll: true });
  }

  function selectSchool(name, focus = true) {
    const item = current.partners.find((p) => p.school_name === name && hasCoordinates(p));
    if (!item || !loaded || failed) return;
    lastFocus = document.activeElement;
    selectedName = name; select.value = name; popup.remove();
    drawPreview(item, focus);
    onSchoolSelect(item);
    ["selected-school", "selected-halo"].forEach((id) => map.setFilter(id, ["==", ["get", "name"], name]));
    syncMotion();
    const mobile = window.matchMedia("(max-width: 700px)").matches;
    const point = [item.location.longitude, item.location.latitude];
    const targetZoom = Math.max(5, Math.min(map.getZoom(), 7));
    // Compute an unobscured center before flying. flyTo's offset is ignored by
    // its reduced-motion jump path, which otherwise hides the mobile marker.
    const camera = map.cameraForBounds([point, point], {
      maxZoom: targetZoom,
      padding: mobile
        ? { top: 20, bottom: canvasHost.clientHeight * .59, left: 25, right: 25 }
        : { top: 25, bottom: 30, left: 25, right: Math.min(355, canvasHost.clientWidth * .43) },
    });
    map.flyTo({ ...camera, duration: duration(), essential: false });
  }

  function flyToResults() {
    const points = current.partners.filter(hasCoordinates).map((p) => [p.location.longitude, p.location.latitude]);
    if (!points.length) return;
    if (!current.filterKey) return globalView();
    const bounds = coordinateBounds(points);
    if (points.length === 1) map.flyTo({ center: points[0], zoom: 4, duration: duration() });
    else map.fitBounds(bounds, { padding: 70, maxZoom: 5, duration: duration() });
  }

  function globalView() { if (loaded && !failed) map.flyTo({ ...globalCamera(), duration: duration() }); }

  function renderHome() {
    const nextKey = JSON.stringify([current.home?.school_name, current.home?.location, current.homeSelected]);
    if (homeKey === nextKey) return;
    homeKey = nextKey;
    homeMarker?.remove(); homeMarker = null;
    const home = current.home;
    const usable = hasCoordinates(home);
    $("#map-home").disabled = !usable;
    $("#map-home").title = usable ? home.school_name : "所屬大學座標待確認";
    if (!usable) return;
    const button = document.createElement("button"); button.type = "button"; button.className = "map-home-marker";
    const star = document.createElement("span"); star.textContent = "★"; star.setAttribute("aria-hidden", "true");
    const text = document.createElement("span"); text.textContent = home.short_name || home.school_name;
    button.append(star, text); button.setAttribute("aria-label", `${current.homeSelected ? "我的大學" : "瀏覽中的出發學校"}：${home.school_name}`);
    button.onclick = homeView;
    homeMarker = new lib.Marker({ element: button, anchor: "center" }).setLngLat([home.location.longitude, home.location.latitude]).addTo(map);
  }
  function homeView() {
    if (loaded && hasCoordinates(current.home)) map.flyTo({ center: [current.home.location.longitude, current.home.location.latitude], zoom: 5, duration: duration() });
  }

  function applyData() {
    if (!loaded || disposed || failed) return;
    const key = JSON.stringify(current.partners.map((p) => [p.school_name, p.location]));
    if (key !== dataKey) { map.getSource("schools").setData(pointsFor(current.partners)); dataKey = key; }
    if (selectedName) {
      const item = current.partners.find((p) => p.school_name === selectedName && hasCoordinates(p));
      if (!item) closePreview();
      else {
        const focused = preview.contains(document.activeElement)
          ? document.activeElement.matches(".favorite-toggle") ? ".favorite-toggle" : document.activeElement.matches("[data-close-map-preview]") ? "[data-close-map-preview]" : ".school-detail-trigger"
          : null;
        drawPreview(item);
        if (focused) preview.querySelector(focused)?.focus({ preventScroll: true });
      }
    }
    const nextCameraKey = `${current.home?.school_name}|${current.filterKey}`;
    if (nextCameraKey !== cameraKey) {
      const first = cameraKey === null; cameraKey = nextCameraKey;
      if (current.filterKey) flyToResults();
      else if (!first) globalView();
    }
    const count = current.partners.filter(hasCoordinates).length;
    if (!current.partners.length) showStatus("沒有符合條件的學校", "試著調整上方篩選，或清除條件重新探索。");
    else if (!count) showStatus("這些學校的位置還在確認中", "學校的申請資訊仍可在列表查看。確認座標後就會出現在地圖上。");
    else status.hidden = true;
    renderHome(); syncMotion();
  }

  function update(next) {
    current = next;
    const located = current.partners.filter(hasCoordinates);
    $("#partner-map-context").textContent = `${current.home?.school_name || "目前學校"}${current.homeSelected ? " · 你的交換起點" : " · 目前瀏覽的合作網絡"}`;
    $("#partner-map-count").textContent = `${located.length} 所已定位 / ${current.partners.length} 所符合條件`;
    $("#partner-map-missing").textContent = current.partners.length > located.length
      ? `${current.partners.length - located.length} 所座標待確認，仍保留在列表中。地圖位置為校級代表點，實際校區請以錄取資訊為準。`
      : "地圖位置為校級代表點；實際交換校區請以錄取資訊為準。";
    select.replaceChildren(new Option("選擇地圖上的學校", ""), ...located.map((p) => new Option(`${p.school_name} · ${p.country || ""}`, p.school_name)));
    select.value = selectedName;
    applyData();
  }

  const timer = setTimeout(() => failMap("地圖載入逾時"), 20000);
  function failMap(message) {
    if (disposed || failed) return;
    failed = true; clearTimeout(timer); closePreview();
    showStatus("地圖暫時無法使用", `${message}。你可以重新嘗試，或回到列表繼續探索。`, true);
  }
  map.on("error", () => { failMap("地圖資源暫時無法載入"); });
  map.on("webglcontextlost", () => failMap("瀏覽器的圖形資源已中斷"));
  map.on("load", () => {
    if (disposed || failed) return;
    clearTimeout(timer); loaded = true;
    map.addSource("schools", { type: "geojson", data: EMPTY(), cluster: true, clusterMaxZoom: 9, clusterRadius: 42 });
    map.addLayer({ id: "cluster-halo", type: "circle", source: "schools", filter: ["has", "point_count"], paint: { "circle-color": "#ffffff", "circle-radius": ["step", ["get", "point_count"], 23, 10, 27, 50, 32], "circle-opacity": .2 } });
    map.addLayer({ id: "clusters", type: "circle", source: "schools", filter: ["has", "point_count"], paint: { "circle-color": ["step", ["get", "point_count"], "#167e85", 10, "#326cb0", 30, "#6b5b9d"], "circle-radius": ["step", ["get", "point_count"], 17, 10, 21, 50, 26], "circle-stroke-width": 2.5, "circle-stroke-color": "#ffffff", "circle-stroke-opacity": .95 } });
    map.addLayer({ id: "cluster-count", type: "symbol", source: "schools", filter: ["has", "point_count"], layout: { "text-field": ["get", "point_count_abbreviated"], "text-font": ["Poppins Medium"], "text-size": 12, "text-allow-overlap": true }, paint: { "text-color": "#ffffff" } });
    map.addLayer({ id: "school-points", type: "circle", source: "schools", filter: ["!", ["has", "point_count"]], paint: { "circle-color": "#197483", "circle-radius": ["interpolate", ["linear"], ["zoom"], 0, 5, 5, 8], "circle-stroke-width": 2.5, "circle-stroke-color": "#ffffff" } });
    map.addLayer({ id: "school-hit-area", type: "circle", source: "schools", filter: ["!", ["has", "point_count"]], paint: { "circle-radius": 20, "circle-color": "#197483", "circle-opacity": 0 } });
    map.addLayer({ id: "selected-halo", type: "circle", source: "schools", filter: ["==", ["get", "name"], ""], paint: { "circle-color": "#f3bd55", "circle-radius": 17, "circle-opacity": .3, "circle-stroke-width": 1, "circle-stroke-color": "#fff3cc", "circle-stroke-opacity": .8, "circle-radius-transition": { duration: 0 } } });
    map.addLayer({ id: "selected-school", type: "circle", source: "schools", filter: ["==", ["get", "name"], ""], paint: { "circle-color": "#b7802c", "circle-radius": 10, "circle-stroke-width": 3, "circle-stroke-color": "#ffffff" } });
    applyData();
    canvasHost.dataset.ready = "true";
  });
  map.on("click", async (event) => {
    if (!loaded || failed) return;
    const features = map.queryRenderedFeatures(event.point, { layers: ["clusters", "school-hit-area"] });
    const names = [...new Set(features.filter((f) => !f.properties.cluster).map((f) => f.properties.name))];
    if (names.length === 1) return selectSchool(names[0]);
    if (names.length > 1) {
      closePreview(); popup.remove(); lastFocus = map.getCanvas();
      preview.replaceChildren(); preview.hidden = false;
      const top = document.createElement("div"); top.className = "map-preview-top";
      const title = document.createElement("h4"); title.textContent = `附近有 ${names.length} 所學校`;
      const close = document.createElement("button"); close.type = "button"; close.className = "map-preview-close"; close.textContent = "×"; close.setAttribute("aria-label", "關閉鄰近學校"); close.onclick = () => closePreview({ restoreFocus: true });
      top.append(title, close);
      const body = document.createElement("div"); body.className = "map-preview-body map-preview-actions";
      names.slice(0, 25).forEach((name) => {
        const button = document.createElement("button"); button.type = "button"; button.className = "secondary-button"; button.textContent = name; button.onclick = () => selectSchool(name); body.append(button);
      });
      if (names.length > 25) {
        const note = document.createElement("p"); note.className = "map-location-note"; note.textContent = "更多學校請使用地圖下方的快速定位選單。"; body.append(note);
      }
      preview.append(top, body); close.focus({ preventScroll: true }); return;
    }
    const cluster = features[0];
    if (!cluster) return;
    try {
      const zoom = await map.getSource("schools").getClusterExpansionZoom(cluster.properties.cluster_id);
      if (!disposed && visible && !failed) { closePreview(); map.flyTo({ center: cluster.geometry.coordinates, zoom: Math.min(zoom + .3, 10.5), duration: duration() }); }
    } catch (_) { /* A filter update can invalidate an in-flight cluster. */ }
  });
  map.on("mousemove", (event) => {
    if (!loaded || failed) return;
    const country = map.queryRenderedFeatures(event.point, { layers: ["land"] })[0]?.properties.name || "";
    if (country !== hoveredCountry) { hoveredCountry = country; map.setFilter("country-hover", ["==", ["get", "name"], country]); }
    const feature = map.queryRenderedFeatures(event.point, { layers: ["clusters", "school-hit-area"] })[0];
    map.getCanvas().style.cursor = feature ? "pointer" : "";
    if (!feature || feature.properties.cluster) { hoveredName = ""; return popup.remove(); }
    if (hoveredName === feature.properties.name && popup.isOpen()) return;
    hoveredName = feature.properties.name;
    const content = document.createElement("div"); content.className = "map-tooltip";
    const name = document.createElement("strong"); name.textContent = feature.properties.name;
    const place = document.createElement("small"); place.textContent = [feature.properties.city, feature.properties.country].filter(Boolean).join(", ");
    content.append(name, place); popup.setLngLat(feature.geometry.coordinates).setDOMContent(content).addTo(map);
  });
  const leave = () => { popup.remove(); if (loaded && !failed) { hoveredCountry = ""; map.setFilter("country-hover", ["==", ["get", "name"], ""]); } }; canvasHost.addEventListener("mouseleave", leave);
  const escape = (event) => { if (event.key === "Escape" && !preview.hidden) { event.preventDefault(); closePreview({ restoreFocus: true }); } };
  $("#partner-map-panel").addEventListener("keydown", escape);
  const onSelect = () => selectSchool(select.value);
  select.addEventListener("change", onSelect);
  $("#map-global").addEventListener("click", globalView);
  $("#map-home").addEventListener("click", homeView);
  const resize = new ResizeObserver(() => { if (visible && !disposed) map.resize(); }); resize.observe(canvasHost);
  const theme = new MutationObserver(() => {
    if (!loaded || disposed || failed) return;
    const p = palette(); map.setPaintProperty("ocean", "background-color", p.sea); map.setPaintProperty("land", "fill-color", p.land);
    map.setPaintProperty("borders", "line-color", p.border); map.setPaintProperty("country-labels", "text-color", p.label); map.setPaintProperty("country-labels", "text-halo-color", p.halo);
    map.setPaintProperty("lakes", "fill-color", p.water); map.setPaintProperty("rivers", "line-color", p.water);
    map.setPaintProperty("coast-shelf", "line-color", p.coast); map.setPaintProperty("graticule", "line-color", p.grid); map.setSky(atmosphere(p));
  }); theme.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return {
    update,
    refreshPreview() {
      const item = current.partners.find(p => p.school_name === selectedName);
      if (!item || disposed) return;
      const active = preview.contains(document.activeElement) ? document.activeElement : null;
      const controls = [...preview.querySelectorAll("button, a, summary")];
      const index = controls.indexOf(active);
      drawPreview(item);
      if (index >= 0) preview.querySelectorAll("button, a, summary")[index]?.focus({preventScroll:true});
    },
    setVisible(next) { visible = next; if (next) { map.resize(); } else { map.stop(); popup.remove(); } syncMotion(); },
    destroy() {
      stopMotion(); disposed = true; clearTimeout(timer); resize.disconnect(); theme.disconnect(); intersection.disconnect(); homeMarker?.remove(); popup.remove();
      motionButton.removeEventListener("click", toggleMotion); reducedMotion.removeEventListener("change", syncMotion); document.removeEventListener("visibilitychange", syncMotion);
      canvasHost.removeEventListener("mouseleave", leave); $("#partner-map-panel").removeEventListener("keydown", escape);
      select.removeEventListener("change", onSelect); $("#map-global").removeEventListener("click", globalView); $("#map-home").removeEventListener("click", homeView);
      map.remove(); delete canvasHost.dataset.ready; preview.hidden = true;
    },
  };
}

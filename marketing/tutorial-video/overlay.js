// Drawn on top of the real site while the tutorial is recorded (record.py adds it to every page): the mouse pointer,
// a ripple on each click, a ring around what the caption talks about, the caption itself and the title cards.
// None of it takes clicks, so the site underneath behaves exactly as it does for a visitor.
//
// The recording runs in slow motion (window.__TUT_SLOW, set by record.py) so that a software-rendered browser still
// paints enough frames; the video is sped back up afterwards. Here the page's clock slows by that factor: timers,
// requestAnimationFrame and performance.now (record.py slows CSS animations through the DevTools protocol).
(() => {
  const slow = window.__TUT_SLOW || 1;
  if (slow === 1 || window.__tutWarp) return;
  window.__tutWarp = true;
  const realNow = performance.now.bind(performance);
  const origin = realNow();
  const warp = (t) => origin + (t - origin) / slow;
  performance.now = () => warp(realNow());
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (callback) => raf((t) => callback(warp(t)));
  const timeout = window.setTimeout.bind(window);
  const interval = window.setInterval.bind(window);
  window.setTimeout = (fn, ms = 0, ...rest) => timeout(fn, ms * slow, ...rest);
  window.setInterval = (fn, ms = 0, ...rest) => interval(fn, ms * slow, ...rest);
})();

// The browser's own smooth scrolling would not slow down with the clock above, so the page scrolls with a tween.
(() => {
  if (window.__tutScroll) return;
  window.__tutScroll = true;
  const jump = window.scrollTo.bind(window);
  const glide = (top) => {
    const from = window.scrollY;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const to = Math.max(0, Math.min(max, top));
    const distance = to - from;
    if (Math.abs(distance) < 1) return;
    const duration = Math.min(1100, 380 + Math.abs(distance) * 0.5);
    const start = performance.now();
    const step = () => {
      const p = Math.min(1, (performance.now() - start) / duration);
      const e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
      jump({ top: from + distance * e, behavior: "instant" });
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  const smooth = (options) => options && typeof options === "object" && options.behavior === "smooth";
  window.scrollTo = function (a, b) {
    if (smooth(a) && a.top !== undefined) return glide(a.top);
    return jump(a, b);
  };
  window.scrollBy = function (a, b) {
    if (smooth(a)) return glide(window.scrollY + (a.top || 0));
    return typeof a === "object" ? jump({ ...a, top: window.scrollY + (a.top || 0), left: window.scrollX + (a.left || 0) }) : jump(window.scrollX + a, window.scrollY + b);
  };
  const intoView = Element.prototype.scrollIntoView;
  const ownScroller = (el) => {
    for (let node = el.parentElement; node && node !== document.body && node !== document.documentElement; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (/(auto|scroll)/.test(style.overflowY) && node.scrollHeight > node.clientHeight + 1) return true;
    }
    return false;
  };
  const pinned = (el) => {
    for (let node = el; node; node = node.parentElement) if (/fixed|sticky/.test(getComputedStyle(node).position)) return true;
    return false;
  };
  Element.prototype.scrollIntoView = function (options) {
    if (!smooth(options) || ownScroller(this) || pinned(this)) return intoView.call(this, options);
    const box = this.getBoundingClientRect();
    const margin = parseFloat(getComputedStyle(this).scrollMarginTop) || 0;
    const block = options.block || "start";
    let top = window.scrollY + box.top - margin;
    if (block === "center") top = window.scrollY + box.top + box.height / 2 - window.innerHeight / 2;
    else if (block === "end") top = window.scrollY + box.bottom - window.innerHeight;
    else if (block === "nearest") {
      if (box.top >= 0 && box.bottom <= window.innerHeight) return;
      top = box.top < 0 ? window.scrollY + box.top - margin : window.scrollY + box.bottom - window.innerHeight;
    }
    glide(top);
  };
})();

(() => {
  if (window.__tut) return;
  const css = `
    #tut-layer, #tut-layer * { box-sizing: border-box; }
    #tut-layer { all: initial; display: block; position: fixed; inset: 0; width: 100vw; height: 100vh; margin: 0; padding: 0; border: 0;
      background: transparent; overflow: visible; pointer-events: none; z-index: 2147483647;
      font-family: var(--uw-font-ui, "Poppins", "GenJyuuGothic", "Noto Sans TC", sans-serif); color: #10243a; }
    #tut-layer::backdrop { background: transparent; }
    .tut-cursor { position: fixed; left: 0; top: 0; width: 30px; height: 30px; transform: translate(-3px, -2px);
      filter: drop-shadow(0 3px 5px rgba(8, 24, 48, .35)); transition: opacity .25s; will-change: left, top; }
    .tut-ripple { position: fixed; width: 18px; height: 18px; margin: -9px 0 0 -9px; border-radius: 50%;
      border: 3px solid #e0524a; background: rgba(224, 82, 74, .18); animation: tut-ripple .6s ease-out forwards; }
    @keyframes tut-ripple { from { transform: scale(.6); opacity: 1; } to { transform: scale(3.4); opacity: 0; } }
    .tut-ring { position: fixed; border-radius: 16px; border: 3px solid #e0524a; opacity: 0;
      box-shadow: 0 0 0 6px rgba(224, 82, 74, .18), 0 0 28px rgba(224, 82, 74, .35);
      transition: opacity .3s, left .35s, top .35s, width .35s, height .35s; }
    .tut-ring.on { opacity: 1; animation: tut-pulse 1.6s ease-in-out infinite; }
    @keyframes tut-pulse { 50% { box-shadow: 0 0 0 11px rgba(224, 82, 74, .10), 0 0 34px rgba(224, 82, 74, .45); } }
    .tut-caption { position: fixed; left: 50%; bottom: 26px; display: flex; gap: 18px; align-items: center;
      width: max-content; max-width: min(1080px, calc(100vw - 80px)); padding: 16px 26px 16px 16px; border-radius: 22px;
      background: rgba(255, 255, 255, .94); border: 1px solid rgba(16, 36, 58, .08);
      box-shadow: 0 18px 50px rgba(10, 30, 60, .22), 0 2px 6px rgba(10, 30, 60, .08);
      transform: translate(-50%, 18px); opacity: 0; transition: opacity .35s, transform .35s; }
    .tut-caption.top { top: 22px; bottom: auto; transform: translate(-50%, -18px); }
    .tut-caption.on { opacity: 1; transform: translate(-50%, 0); }
    .tut-step { flex: none; display: grid; place-items: center; min-width: 74px; height: 64px; padding: 0 12px;
      border-radius: 16px; background: #10243a; color: #fff; text-align: center; line-height: 1.05; }
    .tut-step b { font-size: 26px; font-weight: 700; }
    .tut-step small { display: block; font-size: 12px; letter-spacing: .08em; opacity: .7; }
    .tut-text strong { display: block; font-size: 22px; font-weight: 700; letter-spacing: .02em; }
    .tut-text span { display: block; margin-top: 4px; font-size: 18px; line-height: 1.5; color: #34495e; }
    .tut-text em { font-style: normal; color: #c2413a; font-weight: 700; }
    .tut-card { position: fixed; inset: 0; display: grid; place-items: center; opacity: 0; transition: opacity .6s;
      background: radial-gradient(1200px 700px at 18% 12%, #c9ecf5 0%, transparent 60%),
                  radial-gradient(1000px 700px at 90% 95%, #f8e3d8 0%, transparent 60%), #eef5fb; }
    .tut-card.on { opacity: 1; }
    .tut-card-inner { display: grid; justify-items: center; gap: 18px; text-align: center; transform: translateY(14px);
      transition: transform .8s cubic-bezier(.2, .8, .2, 1); }
    .tut-card.on .tut-card-inner { transform: none; }
    .tut-card img.mark { width: 96px; height: 96px; }
    .tut-card .mascot { position: relative; display: block; width: 150px; margin-top: 6px; animation: tut-bob 2.4s ease-in-out infinite; }
    .tut-card .mascot img { display: block; width: 100%; height: auto; }
    .tut-card .mascot i { position: absolute; top: 42%; width: 9%; height: 13%; border-radius: 50%; background: #14171f; animation: tut-blink 4s infinite; }
    .tut-card .mascot i:first-of-type { left: 34%; }
    .tut-card .mascot i:last-of-type { left: 57%; }
    @keyframes tut-bob { 50% { transform: translateY(-6px) rotate(-2deg); } }
    @keyframes tut-blink { 0%, 92%, 100% { transform: scaleY(1); } 95% { transform: scaleY(.1); } }
    .tut-card .eyebrow { font-size: 18px; font-weight: 700; letter-spacing: .2em; color: #1f6f8b; }
    .tut-card h1 { margin: 0; font-size: 58px; font-weight: 800; letter-spacing: .02em; color: #10243a; }
    .tut-card p { margin: 0; font-size: 22px; color: #34495e; }
    .tut-card .route { display: flex; gap: 12px; align-items: center; margin-top: 10px; font-size: 19px; font-weight: 700; }
    .tut-card .route span { padding: 10px 18px; border-radius: 999px; background: #fff; box-shadow: 0 6px 18px rgba(10, 30, 60, .1); }
    .tut-card .route i { font-style: normal; color: #c2413a; }
  `;

  const layer = document.createElement("div");
  layer.id = "tut-layer";
  layer.setAttribute("popover", "manual");
  layer.innerHTML = `<style>${css}</style>
    <div class="tut-card" data-tut-card></div>
    <div class="tut-ring" data-tut-ring></div>
    <div class="tut-caption" data-tut-caption><div class="tut-step" data-tut-step></div><div class="tut-text"><strong data-tut-title></strong><span data-tut-body></span></div></div>
    <svg class="tut-cursor" data-tut-cursor viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2.5 L4 19.5 L8.6 15.4 L11.6 22 L14.6 20.7 L11.7 14.2 L18 14.2 Z" fill="#fff" stroke="#10243a" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
  const $ = (sel) => layer.querySelector(sel);
  const cursor = $("[data-tut-cursor]");
  const ring = $("[data-tut-ring]");
  let ringTargets = null;
  let ringPad = 8;

  let saved = { x: -60, y: -60 };
  try { saved = JSON.parse(sessionStorage.getItem("tut-cursor")) || saved; } catch (_) { /* first page */ }
  const place = (x, y) => { cursor.style.left = `${x}px`; cursor.style.top = `${y}px`; };
  place(saved.x, saved.y);

  // A dialog the site opens later goes into the top layer above this one; put this one back on top.
  const raise = () => {
    if (!layer.isConnected || !layer.showPopover) return;
    try { layer.hidePopover(); } catch (_) { /* not shown yet */ }
    try { layer.showPopover(); } catch (_) { /* popover unsupported */ }
  };
  const mount = () => {
    document.documentElement.appendChild(layer);
    raise();
    new MutationObserver((records) => {
      if (records.some((r) => r.target.tagName === "DIALOG" && r.target.open)) raise();
    }).observe(document.documentElement, { subtree: true, attributes: true, attributeFilter: ["open"] });
  };
  if (document.documentElement) mount(); else document.addEventListener("DOMContentLoaded", mount, { once: true });

  addEventListener("mousemove", (event) => {
    place(event.clientX, event.clientY);
    try { sessionStorage.setItem("tut-cursor", JSON.stringify({ x: event.clientX, y: event.clientY })); } catch (_) { /* private mode */ }
  }, true);
  const ripple = (x, y) => {
    const dot = document.createElement("div");
    dot.className = "tut-ripple";
    dot.style.left = `${x}px`;
    dot.style.top = `${y}px`;
    layer.appendChild(dot);
    setTimeout(() => dot.remove(), 700);
  };
  addEventListener("mousedown", (event) => ripple(event.clientX, event.clientY), true);

  const track = () => {
    if (ringTargets) {
      const boxes = ringTargets.map((el) => el.getBoundingClientRect()).filter((r) => r.width || r.height);
      if (boxes.length) {
        const left = Math.min(...boxes.map((r) => r.left)) - ringPad;
        const top = Math.min(...boxes.map((r) => r.top)) - ringPad;
        const right = Math.max(...boxes.map((r) => r.right)) + ringPad;
        const bottom = Math.max(...boxes.map((r) => r.bottom)) + ringPad;
        Object.assign(ring.style, { left: `${left}px`, top: `${top}px`, width: `${right - left}px`, height: `${bottom - top}px` });
      }
    }
    requestAnimationFrame(track);
  };
  requestAnimationFrame(track);

  window.__tut = {
    caption(step, title, body, where = "bottom") {
      const box = $("[data-tut-caption]");
      $("[data-tut-step]").innerHTML = step ? `<div><small>STEP</small><b>${step}</b></div>` : `<b>✓</b>`;
      $("[data-tut-title]").textContent = title;
      $("[data-tut-body]").innerHTML = body;
      box.classList.toggle("top", where === "top");
      box.classList.add("on");
    },
    hideCaption() { $("[data-tut-caption]").classList.remove("on"); },
    ring(selectors, pad = 8) {
      const shown = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden"; };
      const list = (Array.isArray(selectors) ? selectors : [selectors]).map((s) => [...document.querySelectorAll(s)].find(shown)).filter(Boolean);
      ringTargets = list.length ? list : null;
      ringPad = pad;
      ring.classList.toggle("on", Boolean(ringTargets));
    },
    clearRing() { ringTargets = null; ring.classList.remove("on"); },
    ripple,
    card(html) { const card = $("[data-tut-card]"); card.innerHTML = `<div class="tut-card-inner">${html}</div>`; requestAnimationFrame(() => card.classList.add("on")); },
    hideCard() { $("[data-tut-card]").classList.remove("on"); },
    cursor(show) { cursor.style.opacity = show ? "1" : "0"; },
    raise,
  };
})();

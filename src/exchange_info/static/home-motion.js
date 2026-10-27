/* Scroll tells the homepage story; it never changes a student's actual progress.
   No scroll interception, timers, dependency or initially hidden content. */
(() => {
  "use strict";
  const root = document.querySelector("#home-landing");
  if (!root || window.UniWayHomeMotion || !("IntersectionObserver" in window)) return;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const desktop = matchMedia("(min-width: 701px)");
  const hero = root.querySelector(".pr-hero");
  const collage = root.querySelector(".pr-collage");
  const map = root.querySelector(".pr-map-band");
  const journey = root.querySelector(".pr-journey");
  const stages = [...root.querySelectorAll(".pr-stages > li")];
  const route = root.querySelector(".hm-route-trace");
  const plane = root.querySelector(".hm-route-plane");
  const index = root.querySelector(".hm-route-index");
  const title = root.querySelector(".hm-route-title");
  const revealTargets = [...root.querySelectorAll(
    ".pr-hero-copy, .pr-plan-card, .pr-collage-mascot, .pr-supported, .pr-editorial .pr-section-head, .pr-guide-card, .pr-features .pr-section-head, .pr-tile, .pr-map-band-copy, .pr-forum-preview .pr-section-head, .pr-board, .pr-social-banner"
  )];
  const seen = new WeakSet();
  const animations = new Map();
  let active = false, frame = 0, reading = -1, destroyed = false;
  const clamp = value => Math.min(1, Math.max(0, value));
  const visible = () => !document.hidden && !root.closest("[hidden]") && root.getClientRects().length > 0;
  const ready = () => visible() && !document.getElementById("boot-splash");
  const set = (element, key, value) => element?.style.setProperty(key, value);

  function cancelAnimations() {
    animations.forEach(animation => animation.cancel());
    animations.clear();
  }
  function reveal(element) {
    if (!ready() || reduce.matches || seen.has(element) || typeof element.animate !== "function") return;
    seen.add(element);
    // Children in the same row arrive in reading order; long columns never accrue delays.
    const siblings = [...element.parentElement.children].filter(child => revealTargets.includes(child));
    const delay = Math.min(siblings.indexOf(element), 2) * 80;
    const animation = element.animate([
      { opacity: .18, transform: "translateY(28px) scale(.985)" },
      { opacity: 1, transform: "translateY(0) scale(1)" },
    ], { duration: 760, delay: Math.max(0, delay), easing: "cubic-bezier(.22,1,.36,1)", fill: "backwards" });
    animation.id = "uniway:home-reveal";
    animations.set(element, animation);
    animation.finished.then(() => {
      if (animations.get(element) === animation) animations.delete(element);
      animation.cancel();
    }, () => {});
  }
  const entrances = new IntersectionObserver(entries => {
    if (!active) return;
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        reveal(entry.target);
        if (seen.has(entry.target)) entrances.unobserve(entry.target);
      }
    });
  }, { threshold: .08, rootMargin: "0px 0px -24px 0px" });

  function update() {
    frame = 0;
    if (!active || !ready()) return;
    // Read geometry together, then write only compositor/SVG properties.
    const heroBox = hero.getBoundingClientRect();
    const mapBox = map.getBoundingClientRect();
    const stageBoxes = stages.map(stage => stage.getBoundingClientRect());
    const focus = innerHeight * .52;
    const heroProgress = clamp(-heroBox.top / Math.max(heroBox.height, 1));
    set(collage, "--hm-hero-offset", `${desktop.matches ? -heroProgress * 56 : 0}px`);
    set(root, "--hm-plan-rotate", `${desktop.matches ? 1.5 * (1 - heroProgress) : 0}deg`);
    if (mapBox.bottom > 0 && mapBox.top < innerHeight) {
      const progress = clamp((innerHeight - mapBox.top) / (innerHeight + mapBox.height));
      set(map, "--hm-map-offset", `${desktop.matches ? (progress - .5) * -64 : 0}px`);
      set(map, "--hm-map-scale", `${desktop.matches ? 1.02 + progress * .035 : 1}`);
      set(map, "--hm-arc-offset", `${1 - clamp((innerHeight * .9 - mapBox.top) / Math.min(mapBox.height, innerHeight * .65))}`);
    }
    if (!stages.length) return;
    const first = stageBoxes[0], last = stageBoxes.at(-1);
    const progress = clamp((focus - (first.top + first.height / 2)) /
      Math.max(1, last.top + last.height / 2 - first.top - first.height / 2));
    const next = stageBoxes.reduce((closest, box, i) =>
      Math.abs(box.top + box.height / 2 - focus) <
      Math.abs(stageBoxes[closest].top + stageBoxes[closest].height / 2 - focus) ? i : closest, 0);
    set(journey, "--hm-route-progress", progress.toFixed(4));
    if (desktop.matches && route && plane) {
      const point = route.getPointAtLength(progress * route.getTotalLength());
      plane.setAttribute("transform", `translate(${point.x.toFixed(2)} ${point.y.toFixed(2)})`);
    }
    if (next !== reading) {
      reading = next;
      stages.forEach((stage, i) => stage.toggleAttribute("data-reading", i === next));
      index.textContent = `${String(next + 1).padStart(2, "0")} / 04`;
      title.textContent = stages[next].querySelector("h3").textContent;
    }
  }
  function schedule() {
    if (active && !frame) frame = requestAnimationFrame(update);
  }
  function reset() {
    [root, collage, map, journey].forEach(element => {
      ["--hm-hero-offset", "--hm-plan-rotate", "--hm-map-offset", "--hm-map-scale", "--hm-arc-offset", "--hm-route-progress"]
        .forEach(key => element?.style.removeProperty(key));
    });
    stages.forEach(stage => stage.removeAttribute("data-reading"));
    reading = -1;
    plane?.setAttribute("transform", "translate(50 185)");
    index.textContent = "01 — 04";
    title.textContent = "從選校到出發，一步一步來";
  }
  function sync() {
    if (destroyed) return;
    const enabled = ready() && !reduce.matches;
    if (enabled !== active) {
      active = enabled;
      if (active) {
        window.addEventListener("scroll", schedule, { passive: true });
        revealTargets.forEach(element => { if (!seen.has(element)) entrances.observe(element); });
      } else {
        window.removeEventListener("scroll", schedule);
        entrances.disconnect();
        cancelAnimationFrame(frame); frame = 0;
        cancelAnimations();
      }
    }
    if (reduce.matches) reset();
    schedule();
  }
  // The map is rendered again when a visitor changes schools.
  function prepareArcs() {
    map.querySelectorAll(".arcs path").forEach(path => path.setAttribute("pathLength", "1"));
    schedule();
  }
  const mapObserver = new MutationObserver(prepareArcs);
  mapObserver.observe(map.querySelector("[data-home-map]"), { childList: true });
  prepareArcs();
  const visibility = new MutationObserver(sync);
  for (let node = root; node; node = node.parentElement) {
    visibility.observe(node, { attributes: true, attributeFilter: ["hidden"] });
  }
  // Boot removes its overlay. Don't let the first entrance finish behind it.
  const bootObserver = new MutationObserver(() => {
    if (!document.getElementById("boot-splash")) { bootObserver.disconnect(); sync(); }
  });
  if (document.getElementById("boot-splash")) bootObserver.observe(document.body, { childList: true });
  const sizeObserver = typeof ResizeObserver === "function" ? new ResizeObserver(sync) : null;
  sizeObserver?.observe(root);
  function focusChanged(event) {
    for (const [element, animation] of animations) {
      if (element.contains(event.target)) { animation.cancel(); animations.delete(element); }
    }
  }
  function discover() {
    root.querySelector(".pr-editorial").scrollIntoView({ behavior: reduce.matches ? "instant" : "smooth", block: "start" });
  }
  function suspend() {
    window.removeEventListener("scroll", schedule);
    active = false;
    cancelAnimationFrame(frame); frame = 0;
    cancelAnimations();
    entrances.disconnect();
  }
  root.addEventListener("focusin", focusChanged);
  root.querySelector("[data-home-discover]")?.addEventListener("click", discover);
  root.querySelector("[data-home-discover]")?.removeAttribute("hidden");
  reduce.addEventListener("change", sync);
  desktop.addEventListener("change", sync);
  document.addEventListener("visibilitychange", sync);
  window.addEventListener("resize", sync, { passive: true });
  window.addEventListener("pagehide", suspend);
  window.addEventListener("pageshow", sync);
  sync();
  window.UniWayHomeMotion = Object.freeze({
    destroy() {
      destroyed = true;
      suspend(); reset();
      visibility.disconnect(); bootObserver.disconnect(); mapObserver.disconnect(); sizeObserver?.disconnect();
      root.removeEventListener("focusin", focusChanged);
      root.querySelector("[data-home-discover]")?.removeEventListener("click", discover);
      root.querySelector("[data-home-discover]")?.setAttribute("hidden", "");
      reduce.removeEventListener("change", sync); desktop.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
      window.removeEventListener("resize", sync);
      window.removeEventListener("pagehide", suspend); window.removeEventListener("pageshow", sync);
    },
  });
})();

/* Guide index (/guides): on wide screens the stage being read keeps its cards in view beside the scrolling stage list.
   The page is complete without this script: every stage and card is ordinary stacked content. The script only marks
   which stage is current (IntersectionObserver) and lets a click or keyboard focus bring a stage into view. */
(() => {
  "use strict";
  const root = document.querySelector("[data-stage-scroll]");
  if (!root || !("IntersectionObserver" in window) || !window.matchMedia) return;
  const blocks = [...root.querySelectorAll("[data-stage-block]")];
  if (blocks.length < 2) return;
  const copies = blocks.map((block) => block.querySelector("[data-stage-copy]"));
  const wide = window.matchMedia("(min-width: 64rem)");
  const calm = window.matchMedia("(prefers-reduced-motion: reduce)");
  let active = -1;
  let observer = null;
  let listeners = null;

  function setActive(index) {
    if (index === active) return;
    active = index;
    blocks.forEach((block, i) => block.toggleAttribute("data-active", i === index));
  }

  // Centre the stage's copy in the viewport, the same place the observer reads the current stage from.
  function show(index) {
    copies[index].scrollIntoView({ block: "center", behavior: calm.matches ? "auto" : "smooth" });
  }

  function enable() {
    if (observer) return;
    root.dataset.stageScroll = "ready";
    setActive(0);
    // A one-percent band at the middle of the viewport: the stage that crosses it is the one being read.
    observer = new IntersectionObserver((entries) => {
      entries.filter((entry) => entry.isIntersecting).forEach((entry) => setActive(copies.indexOf(entry.target)));
    }, { rootMargin: "-50% 0px -49% 0px" });
    copies.forEach((copy) => observer.observe(copy));
    listeners = new AbortController();
    const { signal } = listeners;
    root.addEventListener("click", (event) => {
      if (event.target.closest("a, button")) return;
      const index = copies.indexOf(event.target.closest("[data-stage-copy]"));
      if (index >= 0) show(index);
    }, { signal });
    // Cards of other stages are only faded out, so keyboard focus can still reach them: reveal the stage it lands in.
    root.addEventListener("focusin", (event) => {
      const panel = event.target.closest("[data-stage-cards]");
      const index = panel ? blocks.indexOf(panel.closest("[data-stage-block]")) : -1;
      if (index < 0 || index === active) return;
      setActive(index);
      show(index);
    }, { signal });
  }

  function disable() {
    if (!observer) return;
    observer.disconnect();
    observer = null;
    listeners.abort();
    listeners = null;
    active = -1;
    root.dataset.stageScroll = "";
    blocks.forEach((block) => block.removeAttribute("data-active"));
  }

  const sync = () => (wide.matches ? enable() : disable());
  wide.addEventListener("change", sync);
  sync();
})();

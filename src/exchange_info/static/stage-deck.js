/* The four-stage deck in the application guide (#guide=how-to-use). One card is open at a time. The open card moves on
   every few seconds, but only while the deck is on screen, the tab is visible, nobody is pointing at it or focused inside
   it and the reader has not paused it. Picking a card yourself pauses it for good (until you press play), and with
   "reduce motion" it never plays at all. The pause button is always there while it could play (WCAG 2.2.2).
   platform-guide.js renders the markup and calls init() after every render. */
window.UniWayStageDeck = (() => {
  "use strict";
  const INTERVAL = 8000;
  let current = null;

  function init(scope = document) {
    current?.destroy();
    current = null;
    const deck = scope.querySelector("[data-stage-deck]");
    const cards = deck ? [...deck.querySelectorAll("[data-deck-card]")] : [];
    if (cards.length < 2) return;
    const pause = deck.querySelector("[data-deck-pause]");
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)");
    const abort = new AbortController();
    const { signal } = abort;
    let active = 0;
    let timer = 0;
    let userPaused = false;
    let onScreen = false;
    let pointing = false;
    let focusInside = false;

    const playing = () => !calm.matches && !userPaused && onScreen && !pointing && !focusInside && document.visibilityState === "visible";

    function select(index) {
      active = index;
      cards.forEach((card, i) => {
        card.toggleAttribute("data-active", i === index);
        card.querySelector(".pr-deck-head").setAttribute("aria-expanded", String(i === index));
      });
    }

    function schedule() {
      clearTimeout(timer);
      const run = playing();
      deck.classList.toggle("is-playing", run);
      if (run) timer = setTimeout(() => { select((active + 1) % cards.length); schedule(); }, INTERVAL);
    }

    function setPaused(value) {
      userPaused = value;
      pause.setAttribute("aria-pressed", String(value));
      pause.textContent = value ? "繼續自動播放" : "暫停自動播放";
      schedule();
    }

    const refreshButton = () => { pause.hidden = calm.matches; schedule(); };
    refreshButton();
    calm.addEventListener("change", refreshButton, { signal });
    document.addEventListener("visibilitychange", schedule, { signal });

    pause.addEventListener("click", () => setPaused(!userPaused), { signal });
    deck.addEventListener("click", (event) => {
      const head = event.target.closest(".pr-deck-head");
      if (!head) return;
      select(cards.indexOf(head.closest("[data-deck-card]")));
      // The reader chose a card, so the deck stops choosing for them.
      setPaused(true);
    }, { signal });
    // Holding still while someone reads a card: the cards only, so pressing play (the button sits outside them) takes
    // effect at once. Only a mouse hovering counts; a touch has no "leave" to resume from.
    const surface = deck.querySelector(".pr-deck-cards");
    surface.addEventListener("pointerenter", (event) => { if (event.pointerType === "mouse") { pointing = true; schedule(); } }, { signal });
    surface.addEventListener("pointerleave", () => { pointing = false; schedule(); }, { signal });
    surface.addEventListener("focusin", () => { focusInside = true; schedule(); }, { signal });
    surface.addEventListener("focusout", (event) => {
      if (surface.contains(event.relatedTarget)) return;
      focusInside = false;
      schedule();
    }, { signal });

    const observer = new IntersectionObserver((entries) => {
      onScreen = entries.some((entry) => entry.isIntersecting);
      schedule();
    }, { threshold: 0.4 });
    observer.observe(deck);

    current = { destroy() { clearTimeout(timer); observer.disconnect(); abort.abort(); } };
  }

  return { init };
})();

/* The mascot's tap moves and the loading screen.
 *
 * Loaded as a plain (not deferred) script right after the loading screen's markup, so the loading screen is controlled
 * before the page's other scripts run. The page's CSP forbids inline scripts, which is why this is its own file. */
(() => {
  "use strict";

  // The page script applies the saved theme only after it loads; do it now so a dark-mode visitor is not shown a light screen.
  try {
    const saved = window.localStorage.getItem("exchange-guide-theme") || "light";
    if (saved !== "light") document.documentElement.dataset.theme = "dark";
  } catch (_) {
    /* private mode: keep the default */
  }

  // Only now may the loading screen appear (see mascot.css): the theme above is already in place.
  if (document.getElementById("boot-splash")) document.documentElement.classList.add("splash-on");

  const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- the loading screen -------------------------------------------------------------------------------------
  const SHOW_AFTER_MS = 260; // the CSS keeps it invisible this long, so a load that fast never shows it
  const SHOW_FOR_MS = 700; // once it appears it stays long enough to read, instead of flickering
  const GIVE_UP_MS = 22000; // matches the CSS, which hides it by itself at this point
  const SLOW_AFTER_MS = 8000; // after this long, say that the server may just be waking up

  const splash = document.getElementById("boot-splash");
  let leaving = false;

  function remove() {
    splash?.remove();
  }

  function done() {
    if (!splash || leaving) return;
    leaving = true;
    const age = splash.getAnimations?.()[0]?.currentTime;
    const shown = typeof age === "number" ? age : SHOW_AFTER_MS + SHOW_FOR_MS;
    if (shown <= SHOW_AFTER_MS || reduced()) {
      remove();
      return;
    }
    window.setTimeout(() => {
      splash.classList.add("is-leaving");
      splash.addEventListener("animationend", remove, { once: true });
      window.setTimeout(remove, 700);
    }, Math.max(0, SHOW_AFTER_MS + SHOW_FOR_MS - shown));
  }

  if (splash) {
    window.setTimeout(() => splash.classList.add("is-slow"), SLOW_AFTER_MS);
    window.setTimeout(done, GIVE_UP_MS);
  }
  window.UniWaySplash = { done };

  // ---- tapping the mascot: hop, then a turn, then a wink -------------------------------------------------------
  const MOVES = ["hop", "spin", "wink"];

  document.addEventListener("pointerdown", (event) => {
    const mascot = event.target instanceof Element ? event.target.closest(".uw-mascot[data-play]") : null;
    if (!mascot || reduced()) return;
    const taps = Number(mascot.dataset.taps || 0);
    mascot.dataset.taps = String(taps + 1);
    const move = MOVES[taps % MOVES.length];
    MOVES.forEach((name) => mascot.classList.remove(`is-${name}`));
    void mascot.offsetWidth; // restart the animation if it was still running
    mascot.classList.add(`is-${move}`);
    const body = mascot.querySelector(".uw-mascot-body");
    const finish = (finished) => {
      if (finished.target === body && finished.animationName.startsWith("uw-mascot-")) {
        mascot.classList.remove(`is-${move}`);
        mascot.removeEventListener("animationend", finish);
      }
    };
    mascot.addEventListener("animationend", finish);
  });
})();

/* Share the platform's saved preference without loading its application bundle. */
(() => {
  const key = "exchange-guide-theme";
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  let preference = "light";
  let button;
  try { preference = localStorage.getItem(key) || "light"; } catch (_) { /* Storage is optional. */ }
  function apply() {
    const dark = preference === "dark" || (preference === "system" && system.matches);
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    if (button) {
      button.textContent = dark ? "淺色" : "深色";
      button.setAttribute("aria-label", dark ? "切換為淺色模式" : "切換為深色模式");
    }
  }
  apply();
  system.addEventListener("change", apply);
  window.addEventListener("storage", event => {
    if (event.key === key || event.key === null) { preference = event.newValue || "light"; apply(); }
  });
  document.addEventListener("DOMContentLoaded", () => {
    button = document.querySelector(".reading-theme-toggle");
    if (!button) return;
    button.hidden = false;
    apply();
    button.addEventListener("click", () => {
      preference = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      try { localStorage.setItem(key, preference); } catch (_) { /* Keep the choice in this tab. */ }
      apply();
    });
  });
})();

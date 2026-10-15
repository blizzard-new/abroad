/* Profile page (#profile): the account settings that used to live in a dialog.
   The form (#profile-form) and its save, sign-out and delete handlers are still app.js's. This file adds what the redesign
   needs around them: the side menu, target-country chips, the three-way appearance choice, the data export and the
   summary lines. app.js calls refresh() whenever the account changes and refreshTheme() whenever the theme changes. */
window.UniWayProfile = (() => {
  "use strict";
  const MAX_COUNTRIES = 8;
  const root = () => document.querySelector("#profile");
  const form = () => document.querySelector("#profile-form");
  const countryField = () => form()?.elements.target_countries;

  const countries = () => String(countryField()?.value || "").split(/[、,，]+/).map((item) => item.trim()).filter(Boolean);

  function writeCountries(list) {
    const unique = [...new Set(list)].slice(0, MAX_COUNTRIES);
    countryField().value = unique.join("、");
    renderChips();
  }

  function renderChips() {
    const host = document.querySelector("#profile-country-chips");
    if (!host) return;
    const list = countries();
    host.innerHTML = list.length
      ? list.map((name) => `<span class="pr-chip-item">${escapeHtml(name)}<button type="button" data-remove-country="${escapeHtml(name)}" aria-label="移除 ${escapeHtml(name)}"><i data-lucide="x" aria-hidden="true"></i></button></span>`).join("")
      : '<span class="pr-chip-empty">尚未選擇</span>';
    const add = document.querySelector("#profile-country-add");
    if (add) add.hidden = list.length >= MAX_COUNTRIES;
    initIcons();
  }

  function renderCountryOptions() {
    const list = document.querySelector("#profile-country-options");
    if (!list) return;
    const names = [...new Set((state.dashboard?.partner_universities || state.coverage?.partners || []).map((item) => item.country).filter(Boolean))];
    list.innerHTML = names.sort((a, b) => a.localeCompare(b, "zh-Hant")).map((name) => `<option value="${escapeHtml(name)}"></option>`).join("");
  }

  function commitCountryInput() {
    const input = document.querySelector("#profile-country-input");
    const value = input.value.trim();
    if (value) writeCountries([...countries(), value]);
    input.value = "";
  }

  function toggleCountryInput(open) {
    const input = document.querySelector("#profile-country-input");
    const button = document.querySelector("#profile-country-add");
    input.hidden = !open;
    button.setAttribute("aria-expanded", String(open));
    if (open) {
      renderCountryOptions();
      input.focus();
    } else {
      input.value = "";
    }
  }

  function renderUser() {
    const account = state.account;
    const name = account?.display_name || "我的帳號";
    document.querySelector("#profile-nav-name").textContent = name;
    document.querySelector("#profile-nav-school").textContent = account?.catalog_home_university || "尚未選擇學校";
    const avatar = document.querySelector("#profile-avatar");
    // With no picture the avatar shows the first character of the nickname, as the design does.
    if (avatar && !account?.avatar_url) avatar.textContent = [...name][0] || "我";
    const chip = document.querySelector("#profile-email-chip");
    if (chip) {
      chip.hidden = !account;
      const verified = account?.email_verified === true;
      chip.textContent = verified ? "已驗證" : "待驗證";
      chip.classList.toggle("is-pending", !verified);
    }
    const favorites = document.querySelector("#profile-favorites-summary");
    if (favorites) {
      const count = state.favorites?.size || 0;
      favorites.textContent = count ? `已收藏 ${count} 所合作校，可在收藏頁比較。` : "你收藏的合作校與比較清單。";
    }
  }

  function refreshTheme() {
    const preference = state.themePreference || "light";
    document.querySelectorAll("#profile-section-appearance [data-theme-choice]").forEach((button) => {
      const active = button.dataset.themeChoice === preference;
      button.setAttribute("aria-checked", String(active));
      button.tabIndex = active ? 0 : -1;
    });
  }

  function refresh() {
    if (!root()) return;
    renderUser();
    renderChips();
    refreshTheme();
  }

  function jump(id) {
    const target = document.getElementById(id);
    if (!target) return;
    target.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    document.querySelectorAll("#profile .pr-profile-nav [data-profile-jump]").forEach((button) => {
      if (button.dataset.profileJump === id) button.setAttribute("aria-current", "true");
      else button.removeAttribute("aria-current");
    });
    const field = target.matches("input, select") ? target : target.querySelector("input:not([type=hidden]):not(:disabled), select:not(:disabled)");
    if (field && id.startsWith("profile-row")) field.focus({ preventScroll: true });
  }

  async function exportData(button) {
    const note = document.querySelector("#profile-export-note");
    button.disabled = true;
    try {
      const data = await fetchJson("/auth/me/export");
      const stamp = new Date().toISOString().slice(0, 10);
      downloadApplicationBlob(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), `uniway-我的資料-${stamp}.json`);
      announce("資料已匯出", "success");
    } catch (error) {
      if (note) note.textContent = error.message || "目前無法匯出，請稍後再試。";
      announce(error.message || "目前無法匯出，請稍後再試。", "error");
    } finally {
      button.disabled = false;
    }
  }

  function init() {
    const page = root();
    if (!page) return;
    page.addEventListener("click", (event) => {
      const jumpButton = event.target.closest("[data-profile-jump]");
      if (jumpButton) { jump(jumpButton.dataset.profileJump); return; }
      const choice = event.target.closest("[data-theme-choice]");
      if (choice) { applyTheme(choice.dataset.themeChoice); return; }
      const remove = event.target.closest("[data-remove-country]");
      if (remove) { writeCountries(countries().filter((name) => name !== remove.dataset.removeCountry)); return; }
      if (event.target.closest("#profile-country-add")) {
        toggleCountryInput(document.querySelector("#profile-country-input").hidden);
        return;
      }
      const exportButton = event.target.closest("#profile-export-button");
      if (exportButton) void exportData(exportButton);
    });
    const input = page.querySelector("#profile-country-input");
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") { event.preventDefault(); commitCountryInput(); }
      if (event.key === "Escape") { event.stopPropagation(); toggleCountryInput(false); page.querySelector("#profile-country-add").focus(); }
    });
    input.addEventListener("change", commitCountryInput);
    // Arrow keys move through the appearance choices, like any radio group.
    page.querySelector("#profile-section-appearance").addEventListener("keydown", (event) => {
      const keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (!(event.key in keys)) return;
      const options = [...event.currentTarget.querySelectorAll("[data-theme-choice]")];
      const next = options[(options.indexOf(document.activeElement) + keys[event.key] + options.length) % options.length];
      event.preventDefault();
      next.focus();
      applyTheme(next.dataset.themeChoice);
    });
    // Resetting the form (a fresh fill) must redraw the chips from the hidden field.
    form().addEventListener("reset", () => window.setTimeout(renderChips));
    refresh();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
  return { refresh, refreshTheme };
})();

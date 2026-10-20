/* Forum (#forum): the 心得 / 提問 / 看板 switch, the poster row of schools with the most student stories and the
   strip of approved write-ups (story-carousel.js).
   The feed itself is rendered by community-reader.js, which asks UniWayForum.accepts(post) for each item. */
window.UniWayForum = (() => {
  "use strict";
  const KEY = "uniway-forum-mode-v1";
  const MODES = ["story", "question", "boards"];
  const POSTER_MAX = 10;
  let mode = "story";
  try { const stored = sessionStorage.getItem(KEY); if (MODES.includes(stored)) mode = stored; } catch (_) { mode = "story"; }

  const root = () => document.querySelector("#community-hub");
  // 心得 keeps every post that is not a question, so no discussion disappears behind the switch.
  const accepts = (post) => mode === "question" ? post.post_type === "question" : mode === "story" ? post.post_type !== "question" : true;

  function posters() {
    const partners = state.coverage?.partners || [];
    return partners
      .filter((row) => Number(row.experience_source_count) > 0)
      .sort((a, b) => b.experience_source_count - a.experience_source_count || a.school_name.localeCompare(b.school_name, "zh-Hant"))
      .slice(0, POSTER_MAX);
  }

  function renderPosters(host) {
    const section = host.querySelector("#forum-posters");
    const rows = posters();
    const visible = rows.length > 0 && mode === "story" && state.globalCommunityFeed === "all";
    section.hidden = !visible;
    if (!visible) return;
    host.querySelector("#forum-poster-row").innerHTML = rows.map((row) => {
      const item = partnerByName(row.school_name);
      const image = item ? schoolImageFor(item.school_name, item.country)?.local_path : "";
      const name = row.school_name.replace(/\s+[A-Za-z].*$/, "");
      return `<a class="pr-poster" href="#school=${encodeURIComponent(row.school_name)}"><span class="pr-poster-art"${image ? ` style="background-image:url('${escapeHtml(image)}')"` : ""}><span class="pr-poster-name">${escapeHtml(name)}</span></span><span class="pr-poster-meta"><span>${row.experience_source_count} 則</span></span></a>`;
    }).join("");
  }

  function applyMode(host) {
    host.dataset.forumMode = mode;
    host.querySelectorAll("[data-forum-mode]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.forumMode === mode)));
  }

  function render() {
    const host = root();
    if (!host) return;
    applyMode(host);
    renderPosters(host);
    window.UniWayStories?.render();
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-forum-mode]");
    if (!button || !root()?.contains(button)) return;
    mode = button.dataset.forumMode;
    try { sessionStorage.setItem(KEY, mode); } catch (_) { /* the switch still works for this visit */ }
    render();
    if (mode !== "boards") window.UniWayCommunity?.rerender();
  });

  return { accepts, render, get mode() { return mode; } };
})();

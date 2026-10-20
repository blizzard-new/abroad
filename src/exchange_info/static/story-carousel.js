/* Forum (#forum, 心得 view): a strip of approved student write-ups. Every story comes from GET /experience-stories, which
   only returns submissions whose author agreed to publish a summary and that a moderator approved. The strip moves
   only when the reader asks it to (arrow buttons, swipe, or arrow keys on the focused strip); nothing auto-plays, and
   nothing is shown when there are no approved stories. UniWayForum.render() calls render(). */
window.UniWayStories = (() => {
  "use strict";
  const LIMIT = 12;
  const FRESH_MS = 60 * 1000;
  // The themes the submission form offers; anything else is not displayed.
  const THEMES = { housing: "住宿", cost: "生活費", transport: "交通", academics: "課業", social: "社交", support: "醫療／支援", travel: "旅行", challenges: "踩雷提醒" };
  let stories = [];
  let loadedAt = 0;
  let pending = null;
  let painted = "";

  const section = () => document.querySelector("#forum-stories");
  const track = () => section()?.querySelector("#forum-story-track");
  const calm = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const visible = () => window.UniWayForum?.mode === "story" && state.globalCommunityFeed === "all";

  function load() {
    if (pending) return pending;
    if (loadedAt && Date.now() - loadedAt < FRESH_MS) return Promise.resolve(stories);
    pending = fetchJson(`/experience-stories?limit=${LIMIT}`)
      .then((rows) => { stories = Array.isArray(rows) ? rows : []; loadedAt = Date.now(); return stories; })
      .catch(() => stories)
      .finally(() => { pending = null; });
    return pending;
  }

  const httpUrl = (value) => (/^https?:\/\//i.test(value || "") ? value : "");

  function cardHtml(story, index, total) {
    const themes = (story.themes || []).filter((key) => THEMES[key]);
    const source = httpUrl(story.source_url);
    const id = `story-summary-${index}`;
    return `<li class="pr-story" role="group" aria-roledescription="slide" aria-label="第 ${index + 1} 則，共 ${total} 則">
      <article>
        <p class="pr-story-school"><a href="#school=${encodeURIComponent(story.school_name)}">${escapeHtml(story.school_name.replace(/\s+[A-Za-z].*$/, ""))}</a><span>${escapeHtml(story.exchange_year)} 交換 · ${escapeHtml(story.home_university)}</span></p>
        <h3>${escapeHtml(story.title)}</h3>
        <p id="${id}" class="pr-story-summary">${escapeHtml(story.summary)}</p>
        <button type="button" class="pr-story-more" data-story-more aria-expanded="false" aria-controls="${id}" hidden>閱讀全文</button>
        ${themes.length ? `<ul class="pr-story-themes" aria-label="內容面向">${themes.map((key) => `<li>${THEMES[key]}</li>`).join("")}</ul>` : ""}
        <p class="pr-story-by"><span>${escapeHtml(story.display_name)}</span><small>作者同意公開，經審核</small></p>
        ${source ? `<a class="pr-story-source" href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer nofollow ugc">原始連結<i data-lucide="arrow-up-right" aria-hidden="true"></i></a>` : ""}
      </article>
    </li>`;
  }

  // Which cards are in view decides the counter and whether either arrow can still move.
  function sync() {
    const host = section();
    const strip = track();
    const cards = strip ? [...strip.children] : [];
    if (!host || !cards.length) return;
    const pitch = cards[1] ? cards[1].offsetLeft - cards[0].offsetLeft : cards[0].offsetWidth;
    const first = Math.min(cards.length - 1, Math.round(strip.scrollLeft / pitch));
    const shown = Math.max(1, Math.round(strip.clientWidth / pitch));
    const last = Math.min(cards.length, first + shown);
    const overflows = strip.scrollWidth > strip.clientWidth + 2;
    host.querySelector("#forum-stories-count").textContent = `${first + 1}${last > first + 1 ? `–${last}` : ""} / ${cards.length}`;
    // When every story already fits, the arrows have nothing to do.
    host.querySelectorAll("[data-stories-step]").forEach((arrow) => { arrow.hidden = !overflows; });
    host.querySelector('[data-stories-step="-1"]').disabled = strip.scrollLeft <= 2;
    host.querySelector('[data-stories-step="1"]').disabled = strip.scrollLeft >= strip.scrollWidth - strip.clientWidth - 2;
    // Offer the full text only for summaries the card actually clamps.
    strip.querySelectorAll(".pr-story-summary:not(.is-open)").forEach((summary) => {
      summary.parentElement.querySelector("[data-story-more]").hidden = summary.scrollHeight <= summary.clientHeight + 1;
    });
  }

  function paint(rows) {
    const host = section();
    if (!host) return;
    if (!visible() || !rows.length) { host.hidden = true; return; }
    const signature = rows.map((story) => story.id).join(",");
    if (signature !== painted) {
      painted = signature;
      const strip = track();
      strip.innerHTML = rows.map((story, index) => cardHtml(story, index, rows.length)).join("");
      strip.scrollLeft = 0;
      if (typeof initIcons === "function") initIcons();
    }
    host.hidden = false;
    sync();
  }

  function render() {
    const host = section();
    if (!host) return;
    if (!visible()) { host.hidden = true; return; }
    load().then(paint);
  }

  // Quick clicks add up: each one aims from where the previous click was heading, not from the strip's position
  // part-way through a smooth scroll.
  let aim = null;
  let aimTimer = 0;
  function move(direction) {
    const strip = track();
    const cards = [...strip.children];
    const pitch = cards[1] ? cards[1].offsetLeft - cards[0].offsetLeft : cards[0].offsetWidth;
    const max = strip.scrollWidth - strip.clientWidth;
    aim = Math.max(0, Math.min(max, (aim ?? strip.scrollLeft) + direction * pitch));
    strip.scrollTo({ left: aim, behavior: calm() ? "auto" : "smooth" });
    clearTimeout(aimTimer);
    aimTimer = setTimeout(() => { aim = null; }, 800);
  }

  document.addEventListener("click", (event) => {
    const host = section();
    if (!host || !host.contains(event.target)) return;
    const arrow = event.target.closest("[data-stories-step]");
    if (arrow) {
      move(Number(arrow.dataset.storiesStep));
      return;
    }
    const more = event.target.closest("[data-story-more]");
    if (more) {
      const summary = document.getElementById(more.getAttribute("aria-controls"));
      const open = more.getAttribute("aria-expanded") !== "true";
      summary.classList.toggle("is-open", open);
      more.setAttribute("aria-expanded", String(open));
      more.textContent = open ? "收合" : "閱讀全文";
    }
  });

  // Scrolling (swipe, wheel, keys or the arrows) updates the counter once per frame.
  let frame = 0;
  document.addEventListener("scroll", (event) => {
    if (event.target.id !== "forum-story-track" || frame) return;
    frame = requestAnimationFrame(() => { frame = 0; sync(); });
  }, { capture: true, passive: true });
  window.addEventListener("resize", () => { if (section() && !section().hidden) sync(); });

  return { render };
})();

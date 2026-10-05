/* "出發前提醒": country-level things to sort out before leaving, from the bundled source-backed guides. */
window.UniWayDestinationTips = (() => {
  const guides = new Map(); // country -> guide, or null while we have none for it
  const BOCA_ENTRY = "https://www.boca.gov.tw/sp-foof-countrylp-03-1.html";
  const IMPORTANCE = { must: "出發前先處理", should: "建議", good_to_know: "補充" };
  const safeUrl = (value) => { try { const url = new URL(value); return url.protocol === "https:" && !url.username && !url.password ? url.href : ""; } catch (_) { return ""; } };

  function sourceLinks(tip) {
    return tip.sources.map((source) => {
      const href = safeUrl(source.url);
      return href ? `<a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(source.name)}<span class="visually-hidden">（另開新視窗）</span></a>` : escapeHtml(source.name);
    }).join("、");
  }

  function tipMarkup(tip) {
    return `<article class="tip" data-importance="${escapeHtml(tip.importance)}">
      <div class="tip-head"><span class="tip-level">${escapeHtml(IMPORTANCE[tip.importance] || "建議")}</span><h4>${escapeHtml(tip.title)}</h4></div>
      <p>${escapeHtml(tip.detail)}</p>
      <p class="tip-sources">來源：${sourceLinks(tip)}<span>查證 ${escapeHtml(tip.checked_at)}</span></p>
    </article>`;
  }

  function guideMarkup(guide) {
    const count = guide.topics.reduce((sum, topic) => sum + topic.tips.length, 0);
    const draft = guide.review_status !== "reviewed";
    return `<div class="tips-banner${draft ? " is-draft" : ""}">
        <strong>${escapeHtml(guide.display_name)}　共 ${count} 項提醒${draft ? "　·　整理中，尚待人工審核" : "　·　已人工審核"}</strong>
        <p>${escapeHtml(guide.disclaimer)}</p>
        ${guide.last_checked ? `<small>最近查證：${escapeHtml(guide.last_checked)}</small>` : ""}
      </div>
      ${guide.intro ? `<p class="tips-intro">${escapeHtml(guide.intro)}</p>` : ""}
      <nav class="tips-topic-nav" aria-label="提醒主題">${guide.topics.map((topic) => `<button type="button" data-tips-topic="${escapeHtml(topic.topic)}">${escapeHtml(topic.title)}<span>${topic.tips.length}</span></button>`).join("")}</nav>
      ${guide.topics.map((topic) => `<section class="tips-topic" id="tips-topic-${escapeHtml(topic.topic)}" aria-labelledby="tips-heading-${escapeHtml(topic.topic)}">
        <h3 id="tips-heading-${escapeHtml(topic.topic)}" tabindex="-1">${escapeHtml(topic.title)}</h3>
        ${topic.tips.map(tipMarkup).join("")}
      </section>`).join("")}`;
  }

  function emptyMarkup(item) {
    return `<div class="tips-empty"><i data-lucide="luggage" aria-hidden="true"></i>
      <div><strong>${escapeHtml(item.country || "這個國家")}的出發前提醒還在整理中</strong>
      <p>先到外交部領事事務局查這個國家的簽證與入境須知，再向合作校國際處確認落地後要辦的事。</p>
      <a class="secondary-button" href="${BOCA_ENTRY}" target="_blank" rel="noreferrer"><span>各國簽證及入境須知</span><i data-lucide="external-link" aria-hidden="true"></i></a></div></div>`;
  }

  // The site routes on the URL hash, so topic chips scroll in place instead of linking to a #fragment.
  function bindTopicNav(host) {
    if (host.dataset.tipsBound) return;
    host.dataset.tipsBound = "1";
    host.addEventListener("click", (event) => {
      const chip = event.target.closest("[data-tips-topic]");
      if (!chip) return;
      const section = host.querySelector(`#tips-topic-${CSS.escape(chip.dataset.tipsTopic)}`);
      if (!section) return;
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      section.scrollIntoView({ behavior: reduced ? "instant" : "smooth", block: "start" });
      section.querySelector("h3")?.focus({ preventScroll: true });
    });
  }

  function paint(item, guide) {
    const host = document.querySelector("#prep-content");
    if (!host || state.activeSchool !== item.school_name) return;
    bindTopicNav(host);
    host.setAttribute("aria-busy", "false");
    host.innerHTML = guide ? guideMarkup(guide) : emptyMarkup(item);
    const title = document.querySelector("#destination-prep-title");
    if (title) title.textContent = guide ? `${guide.display_name}　出發前提醒` : "出發前提醒";
    initIcons();
  }

  async function load(item) {
    const host = document.querySelector("#prep-content");
    if (!host || !item) return;
    const country = (item.country || "").trim();
    if (!country) { paint(item, null); return; }
    if (guides.has(country)) { paint(item, guides.get(country)); return; }
    host.setAttribute("aria-busy", "true");
    try {
      const guide = await fetchJson(`/destination-tips?country=${encodeURIComponent(country)}`);
      guides.set(country, guide);
    } catch (error) {
      if (error.status !== 404 && !/還在整理中/.test(error.message || "")) {
        host.setAttribute("aria-busy", "false");
        host.innerHTML = '<div class="tips-empty"><div><strong>暫時讀不到出發前提醒</strong><p>請稍後重新整理，或先到外交部領事事務局查詢。</p></div></div>';
        return;
      }
      guides.set(country, null);
    }
    paint(item, guides.get(country));
  }

  return { load };
})();

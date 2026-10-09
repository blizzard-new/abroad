/* Web selection flow; account data is scoped by owner AND home university. */
const discoveryStores = new Map();
let discoveryGuestScope = "", discoveryCriteria = {}, discoveryCompare = new Set();
let discoveryShelf = "schools", discoveryTheme = "all", discoverySavedCountry = "", discoverySavedSchool = "";
const discoveryPreviewRequests = new Map();
const discoveryPreviewErrors = new Set();
const discoverySourceRegistry = new Map();
let discoveryReaderSource = null, discoveryReaderReturn = null;
let discoveryCompareScope = "";

function clearDiscoveryAccountData(owner) {
  const prefix = `uniway-discovery-v1:${owner}:`;
  for (const key of discoveryStores.keys()) if (key.startsWith(prefix)) discoveryStores.delete(key);
  try { Object.keys(localStorage).filter(key => key.startsWith(prefix)).forEach(key => localStorage.removeItem(key)); } catch (_) { /* memory is cleared */ }
  discoveryGuestScope = ""; discoveryCompareScope = ""; discoveryCompare.clear();
  discoverySavedCountry = ""; discoverySavedSchool = "";
  discoveryReaderSource = null; discoveryReaderReturn = null;
  const reader = $("#discovery-reader");
  if (reader?.open) reader.close();
  if (reader) reader.replaceChildren();
}

function discoveryKey(home = activeHomeSchool()) { return `uniway-discovery-v1:${state.account?.id || "guest"}:${home}`; }
function discoveryData(home = activeHomeSchool()) {
  const key = discoveryKey(home);
  if (!discoveryStores.has(key)) {
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem(key) || "{}"); } catch (_) { /* session remains usable */ }
    discoveryStores.set(key, UniWayDiscovery.sanitize(saved.data));
  }
  if (!state.account && discoveryGuestScope !== key) {
    let schools = [];
    try { schools = JSON.parse(localStorage.getItem(key) || "{}").schools || []; } catch (_) { /* empty */ }
    state.guestComparisons = new Set(Array.isArray(schools) ? schools.filter(s => typeof s === "string").slice(0, 500) : []);
    discoveryGuestScope = key;
    discoveryCompare.clear();
  }
  return discoveryStores.get(key);
}
function applyDiscoveryWorkspace(value, home = activeHomeSchool()) {
  discoveryStores.set(discoveryKey(home), UniWayDiscovery.sanitize(value));
}
function persistDiscovery({ sync = true } = {}) {
  const data = discoveryData();
  try { localStorage.setItem(discoveryKey(), JSON.stringify({ data, schools: [...activeSchoolSelections()] })); }
  catch (_) { announce("瀏覽器無法保存，這次操作仍可繼續。", "info"); }
  if (sync && state.account && state.accountWorkspaceLoadedSchool === activeHomeSchool()) scheduleAccountWorkspaceSync();
}
function mergeDiscoveryWorkspace(base, remote, local) {
  const b = UniWayDiscovery.sanitize(base), r = UniWayDiscovery.sanitize(remote), l = UniWayDiscovery.sanitize(local);
  return UniWayDiscovery.sanitize({
    school_preferences: mergeWorkspaceRecord(b.school_preferences, r.school_preferences, l.school_preferences, { recursive: true }),
    saved_experiences: mergeWorkspaceRecord(b.saved_experiences, r.saved_experiences, l.saved_experiences),
    preference_order: workspaceValuesEqual(b.preference_order, l.preference_order) ? r.preference_order : l.preference_order,
    recent_views: [...l.recent_views, ...r.recent_views].sort((a,b) => b.viewed_at.localeCompare(a.viewed_at)),
  });
}
function rememberDiscovery(kind, source) {
  const data = discoveryData(), row = { ...UniWayDiscovery.sourceSnapshot(source), kind, viewed_at: new Date().toISOString() };
  data.recent_views = UniWayDiscovery.sanitize({ recent_views: [row, ...data.recent_views] }).recent_views;
  persistDiscovery(); renderDiscoveryRecents();
}
function registerDiscoverySource(source) {
  const key = UniWayDiscovery.sourceKey(source);
  discoverySourceRegistry.set(key, source);
  return key;
}
function discoveryBookmarkButton(source) {
  const key = registerDiscoverySource(source), saved = Boolean(discoveryData().saved_experiences[key]);
  return `<button type="button" class="discovery-bookmark ${saved ? "saved" : ""}" data-save-experience="${escapeHtml(key)}" aria-pressed="${saved}" aria-label="${saved ? "取消收藏心得" : "收藏心得"}"><i data-lucide="bookmark${saved ? "-check" : ""}" aria-hidden="true"></i><span>${saved ? "已收藏" : "收藏心得"}</span></button>`;
}
function discoveryChineseSummary(source) {
  if (source.summary_zh) return source.summary_zh;
  if (source.translation_status === "pending") return "";
  const value = source.summary || "";
  return window.UniWayChinese && !window.UniWayChinese.needsTranslation(value) ? window.UniWayChinese.normalizeTerms(value) : "";
}
const DISCOVERY_FILLER = /^(這個來源主要談到|這個公開來源|來源談到|\d+\s*個來源)/;
const DISCOVERY_KIND_LABELS = { personal_story: "學生分享", review_collection: "評論彙整頁", community_thread: "社群討論串", video: "影片", directory: "學校介紹、排名或課程目錄", other: "其他來源" };
const discoveryDigestCache = new Map();
// A sentence that only says which topics a source mentions tells the student nothing, so it is never shown as a summary.
function discoveryUsefulSummary(source) {
  const value = discoveryChineseSummary(source);
  return value && !DISCOVERY_FILLER.test(value) ? value : "";
}
async function discoveryDigestFor(source) {
  if (source.digest_zh) return source.digest_zh;
  const url = UniWayDiscovery.safeUrl(source.source_url);
  if (!url) return null;
  if (discoveryDigestCache.has(url)) return discoveryDigestCache.get(url);
  let digest = null;
  try { digest = await fetchJson(`/experience-digest?source_url=${encodeURIComponent(url)}`); } catch (_) { digest = null; }
  discoveryDigestCache.set(url, digest);
  return digest;
}
function discoverySourceCard(source, { theme = "all" } = {}) {
  const key = registerDiscoverySource(source);
  const digest = source.digest_zh;
  const summary = digest ? digest.overview : (theme !== "all" && source.theme_summaries_zh?.[theme]) || discoveryUsefulSummary(source);
  const kind = DISCOVERY_KIND_LABELS[source.source_kind] || "";
  return `<article class="discovery-experience-card${digest ? " has-digest" : ""}" data-experience-key="${escapeHtml(key)}">
    <small>${digest ? '<span class="discovery-digest-badge">中文整理</span> ' : ""}${escapeHtml(source.exchange_term || "交換學期未標示")}${source.published_at ? ` · 發表 ${escapeHtml(source.published_at)}` : ""}</small>
    <h4><button type="button" data-read-experience="${escapeHtml(key)}">${escapeHtml(digest ? digest.title_zh : source.title)}</button></h4>
    ${digest && digest.title_zh !== source.title ? `<p class="discovery-original-title">原標題：${escapeHtml(source.title)}</p>` : ""}
    <p>${escapeHtml(truncate(summary || "這篇還沒有中文整理，可以先看原文。", digest ? 200 : 150))}</p>
    <div class="discovery-source-footer"><span class="discovery-tags">${kind && !digest ? `<span>${escapeHtml(kind)}</span>` : ""}${(source.themes || []).slice(0,3).map(t => `<span>${escapeHtml(UniWayDiscovery.THEMES[t] || t)}</span>`).join("")}</span>${discoveryBookmarkButton(source)}</div>
  </article>`;
}
function discoveryOtherSources(sources) {
  if (!sources.length) return "";
  const groups = Object.keys(DISCOVERY_KIND_LABELS).map(kind => [kind, sources.filter(s => (DISCOVERY_KIND_LABELS[s.source_kind] ? s.source_kind : "other") === kind)]).filter(([, rows]) => rows.length);
  return `<details class="discovery-other-sources"><summary>其他參考來源 <span>${sources.length}</span></summary><p class="discovery-muted">這些網頁還沒有中文整理，或不是學生本人寫的心得（例如排名、課程目錄）。</p>
    ${groups.map(([kind, rows]) => `<section><h4>${escapeHtml(DISCOVERY_KIND_LABELS[kind])} <span>${rows.length}</span></h4><ul>${rows.map(s => `<li><a href="${escapeHtml(UniWayDiscovery.safeUrl(s.source_url))}" target="_blank" rel="noreferrer">${escapeHtml(truncate(s.title, 90))}</a><small>${escapeHtml(s.platform || "")}${s.language && s.language !== "unknown" ? ` · ${escapeHtml(String(s.language).toUpperCase())}` : ""}</small></li>`).join("")}</ul></section>`).join("")}</details>`;
}
function renderDiscoveryRecents() {
  const rows = discoveryData().recent_views;
  document.querySelectorAll("[data-discovery-recents]").forEach(host => {
    host.hidden = !rows.length;
    host.innerHTML = `<summary>最近看過 <span>${rows.length}</span></summary><div class="discovery-recent-list">${rows.slice(0, 8).map(row => {
      const key = registerDiscoverySource(row);
      return `<button type="button" ${row.kind === "school" ? `data-recent-school="${escapeHtml(row.school_name)}"` : `data-read-experience="${escapeHtml(key)}"`}><i data-lucide="${row.kind === "school" ? "school" : "book-open"}" aria-hidden="true"></i><span>${escapeHtml(row.kind === "school" ? row.school_name : row.title)}<small>${escapeHtml(row.kind === "school" ? row.country : row.school_name)}</small></span></button>`;
    }).join("")}</div>`;
  });
  initIcons();
}
function renderDiscoveryWorkspace() {
  const host = $("#selection-workspace");
  if (!host || !state.dashboard) return;
  const data = discoveryData(), selections = activeSchoolSelections();
  const schools = state.dashboard.partner_universities.filter(p => selections.has(p.school_name));
  $("#discovery-selection-count").textContent = schools.length || "";
  const available = new Set(schools.map(p => p.school_name));
  discoveryCompare = new Set([...discoveryCompare].filter(n => available.has(n)));
  if (discoveryCompareScope !== discoveryKey() && schools.length) {
    discoveryCompare = new Set(schools.slice(0,3).map(p => p.school_name));
    discoveryCompareScope = discoveryKey();
  }
  $("#favorite-list").hidden = true; $("#compare-panel").hidden = true;
  $("#favorites-title").textContent = "我的選校";
  $("#discovery-save-note").textContent = state.account ? "帳號同步" : "儲存在此裝置";
  const bookmarks = Object.values(data.saved_experiences);
  host.innerHTML = `<div class="discovery-shelf-tabs" role="group" aria-label="收藏類型"><button type="button" data-discovery-shelf="schools" aria-pressed="${discoveryShelf === "schools"}">學校 <span>${schools.length}</span></button><button type="button" data-discovery-shelf="experiences" aria-pressed="${discoveryShelf === "experiences"}">心得 <span>${bookmarks.length}</span></button><a href="#partners">繼續找學校 ↗</a></div>
    <div class="discovery-workspace-grid" ${discoveryShelf !== "schools" ? "hidden" : ""}>
    <section class="discovery-candidates" aria-label="候選學校">${schools.length ? schools.map((item, index) => {
      const pref = data.school_preferences[item.school_name] || { interest: 0, note: "" }, name = escapeHtml(item.school_name), inOrder = data.preference_order.includes(item.school_name);
      return `<article class="discovery-candidate travel-saved-ticket"><div class="travel-ticket-heading" aria-hidden="true"><span><i data-lucide="plane"></i> 下一站收藏</span><span class="travel-ticket-number">${String(index + 1).padStart(2, "0")}</span></div><header>${renderSchoolPhoto(item, "favorite")}<div><small>${escapeHtml(item.country || "")}</small><h3><button type="button" class="school-detail-trigger" data-school-name="${name}">${name}</button></h3></div>${renderFavoriteButton(item,true)}</header>
      <div class="discovery-candidate-facts"><span>名額 ${escapeHtml(item.quota || "待公告")}</span><span>${escapeHtml(truncate(localizedPartnerValue(item, "study_period", "study_period"), 32))}</span></div>
      <div class="discovery-interest" role="group" aria-label="${name}的喜愛度">${[1,2,3,4,5].map(n => `<button type="button" data-interest-school="${name}" data-interest="${n}" aria-pressed="${pref.interest >= n}" aria-label="${n} 顆愛心">♥</button>`).join("")}<small>${pref.interest >= 4 ? "很想去" : pref.interest ? "考慮中" : "我的喜愛度"}</small></div>
      <label class="discovery-note-label"><span class="visually-hidden">${name}的私人備註</span><textarea data-school-note="${name}" maxlength="1000" rows="2" placeholder="留下選校理由…">${escapeHtml(pref.note)}</textarea></label>
      <footer><label><input type="checkbox" data-compare-school="${name}" ${discoveryCompare.has(item.school_name) ? "checked" : ""}> 比較</label><button type="button" class="secondary-button" data-preference-toggle="${name}" aria-pressed="${inOrder}">${inOrder ? "移出志願" : "加入志願"}</button></footer></article>`;
    }).join("") : '<div class="discovery-empty"><i data-lucide="heart" aria-hidden="true"></i><p>把想去的學校留在這裡。</p><a href="#partners">開始找學校 ↗</a></div>'}</section>
    <aside class="discovery-ranking"><div class="discovery-ranking-title"><h3>我的志願</h3><span>${data.preference_order.length} 所</span></div><ol id="discovery-preference-list">${data.preference_order.map((name,i) => `<li draggable="true" data-rank-school="${escapeHtml(name)}" tabindex="0" aria-label="第 ${i+1} 志願 ${escapeHtml(name)}，Alt 加上下鍵調整"><span class="discovery-rank-number">${i+1}</span><div><strong>${escapeHtml(name)}</strong><small>${escapeHtml(partnerByName(name)?.country || "資料待更新")}</small></div><div class="discovery-rank-controls"><button type="button" data-rank-up="${escapeHtml(name)}" aria-label="上移${escapeHtml(name)}" ${i === 0 ? "disabled" : ""}>↑</button><button type="button" data-rank-down="${escapeHtml(name)}" aria-label="下移${escapeHtml(name)}" ${i === data.preference_order.length-1 ? "disabled" : ""}>↓</button><button type="button" data-preference-toggle="${escapeHtml(name)}" aria-label="移出志願${escapeHtml(name)}">×</button></div></li>`).join("")}</ol>${!data.preference_order.length ? '<p class="discovery-muted">從候選學校加入志願。</p>' : '<small class="discovery-muted">拖曳或使用上下箭頭調整</small><button type="button" class="primary-button" id="discovery-use-preferences">帶入申請清單</button>'}</aside>
    <section class="discovery-comparison" id="discovery-comparison" aria-label="學校比較">${schools.length > 1 ? renderComparison(schools.filter(p => discoveryCompare.has(p.school_name))) : ""}</section></div>
    <section id="discovery-saved-experiences" ${discoveryShelf !== "experiences" ? "hidden" : ""}></section>`;
  renderSavedDiscoveryExperiences(); updateFavoriteCounts(); initIcons();
}
async function renderSavedDiscoveryExperiences() {
  const host = $("#discovery-saved-experiences"); if (!host) return;
  const scope = discoveryKey();
  let sources = Object.values(discoveryData().saved_experiences);
  if (window.UniWayChinese) sources = (await window.UniWayChinese.localize("/student-experiences", { sources })).sources;
  // Saved copies keep only a short snapshot, so each one's Chinese write-up is looked up by its address.
  sources = await Promise.all(sources.map(async s => ({ ...s, digest_zh: (await discoveryDigestFor(s)) || undefined })));
  if (!host.isConnected || scope !== discoveryKey()) return;
  const countries = unique(sources.map(s => s.country || "未標示國家"));
  const inCountry = sources.filter(s => !discoverySavedCountry || (s.country || "未標示國家") === discoverySavedCountry);
  const schools = unique(inCountry.map(s => s.school_name));
  if (discoverySavedCountry && !countries.includes(discoverySavedCountry)) { discoverySavedCountry = ""; return renderSavedDiscoveryExperiences(); }
  if (!schools.includes(discoverySavedSchool)) discoverySavedSchool = "";
  const filtered = inCountry.filter(s => !discoverySavedSchool || s.school_name === discoverySavedSchool);
  host.innerHTML = `<div class="discovery-saved-filters"><label>國家<select id="discovery-saved-country"><option value="">全部國家</option>${countries.map(c => `<option ${c === discoverySavedCountry ? "selected" : ""}>${escapeHtml(c)}</option>`).join("")}</select></label><label>學校<select id="discovery-saved-school"><option value="">全部學校</option>${schools.map(s => `<option ${s === discoverySavedSchool ? "selected" : ""}>${escapeHtml(s)}</option>`).join("")}</select></label></div>
    ${filtered.length ? unique(filtered.map(s => s.school_name)).map(school => `<section class="discovery-saved-group"><h3>${escapeHtml(school)}</h3><div class="discovery-experience-grid">${filtered.filter(s => s.school_name === school).map(discoverySourceCard).join("")}</div></section>`).join("") : '<div class="discovery-empty"><p>還沒有收藏心得。</p><a href="#partners">找一間學校，看看大家怎麼說 ↗</a></div>'}`;
  initIcons();
}
function renderDiscoveryExperiences(digest) {
  const host = $("#experience-content"); if (!host) return;
  host.setAttribute("aria-busy", "false");
  const all = digest.sources || [];
  // A student's account is shown as an experience when we wrote it up in Chinese, or when it is a personal story with a summary
  // that says something. Ranking pages, review listings, threads and videos with nothing to read are references.
  const isStory = s => Boolean(s.digest_zh) || ((!s.source_kind || s.source_kind === "personal_story") && Boolean(discoveryUsefulSummary(s)));
  const sources = all.filter(isStory), others = all.filter(s => !isStory(s));
  const themes = Object.keys(UniWayDiscovery.THEMES).filter(t => sources.some(s => s.themes?.includes(t)));
  if (discoveryTheme !== "all" && !themes.includes(discoveryTheme)) discoveryTheme = "all";
  const filtered = sources.filter(s => discoveryTheme === "all" || s.themes?.includes(discoveryTheme));
  host.innerHTML = `<div class="discovery-topic-bar" role="group" aria-label="心得主題"><button type="button" data-experience-theme="all" aria-pressed="${discoveryTheme === "all"}">全部 ${sources.length}</button>${themes.map(t => `<button type="button" data-experience-theme="${t}" aria-pressed="${discoveryTheme === t}">${UniWayDiscovery.THEMES[t]}</button>`).join("")}<button type="button" id="refresh-experiences" class="discovery-refresh">更新心得</button></div>
    ${sources.length ? `<div class="discovery-experience-grid">${filtered.map(source => discoverySourceCard(source, { theme: discoveryTheme })).join("")}</div>` : `<div class="discovery-empty"><p>${others.length ? "這所學校還沒有整理成中文的學生心得。下方有找到的參考網頁，可以先看原文。" : "還沒有公開學生心得。"}</p><button type="button" data-open-life>查看生活情報</button></div>`}
    ${discoveryOtherSources(others)}
    <details class="discovery-source-note"><summary>資料與來源</summary><p>${escapeHtml(digest.disclaimer || "學生個人經驗，依年份與科系而異。")}</p><p>${escapeHtml(digest.coverage_note || "")}</p></details>`;
  initIcons();
}
async function openDiscoveryReader(source) {
  if (!source) return;
  const scope = discoveryKey();
  if (window.UniWayChinese) source = (await window.UniWayChinese.localize("/student-experiences", { sources: [source] })).sources[0];
  if (scope !== discoveryKey()) return;
  const digest = await discoveryDigestFor(source);
  if (scope !== discoveryKey()) return;
  discoveryReaderSource = source; discoveryReaderReturn = document.activeElement;
  rememberDiscovery("experience", source);
  const dialog = $("#discovery-reader");
  const heading = digest ? digest.title_zh : source.title;
  const byline = [source.platform, source.author_name, source.language && source.language !== "unknown" ? `原文 ${String(source.language).toUpperCase()}` : ""].filter(Boolean).join(" · ");
  const body = digest
    ? `<p class="discovery-reader-summary">${escapeHtml(digest.overview)}</p>
      <div class="discovery-reader-themes">${digest.sections.map(section => `<section><h3>${escapeHtml(section.heading)}</h3><ul>${section.points.map(point => `<li>${escapeHtml(point)}</li>`).join("")}</ul></section>`).join("")}
      ${digest.tips.length ? `<section class="discovery-reader-tips"><h3>給之後要去的人</h3><ul>${digest.tips.map(point => `<li>${escapeHtml(point)}</li>`).join("")}</ul></section>` : ""}</div>
      <details class="discovery-reader-original" open><summary>這份中文整理怎麼來的</summary><p>${escapeHtml(digest.basis)}${digest.written_at ? ` 整理日期：${escapeHtml(digest.written_at)}。` : ""}${heading !== source.title ? ` 原標題：${escapeHtml(source.title)}。` : ""}</p></details>`
    : `${source.translation_status === "machine" ? '<span class="life-kind">機器翻譯</span>' : ""}<p class="discovery-reader-summary">${escapeHtml(discoveryUsefulSummary(source) || "這篇還沒有中文整理，請先看原文。")}</p>
      <div class="discovery-reader-themes">${Object.entries(source.theme_summaries_zh || {}).filter(([,v]) => v && !DISCOVERY_FILLER.test(v)).map(([t,v]) => `<section><h3>${escapeHtml(UniWayDiscovery.THEMES[t] || t)}</h3><p>${escapeHtml(v)}</p></section>`).join("")}</div>
      <details class="discovery-reader-original"><summary>原文與來源</summary><p>${escapeHtml(source.original_summary || source.summary || "尚無原文摘要，請至來源核對。")}</p><p>內容以繁體中文呈現，專有名詞保留原文。機器翻譯未經人工審核，完整內容可至來源核對。</p></details>`;
  dialog.innerHTML = `<div class="discovery-reader-heading"><div><small>${escapeHtml(source.school_name)}</small><h2 id="discovery-reader-title">${escapeHtml(heading)}</h2></div><button type="button" data-close-reader aria-label="關閉心得">×</button></div>
    <div class="discovery-reader-meta"><span>${escapeHtml(source.exchange_term || "交換學期未標示")}</span>${source.published_at ? `<span>發表 ${escapeHtml(source.published_at)}</span>` : ""}${byline ? `<span>${escapeHtml(byline)}</span>` : ""}${discoveryBookmarkButton(source)}</div>
    ${body}
    <a class="primary-button" data-experience-original href="${escapeHtml(UniWayDiscovery.safeUrl(source.source_url))}" target="_blank" rel="noreferrer">${source.source_type === "video" ? "觀看原始影片" : "閱讀完整原文"} ↗</a>`;
  if (!dialog.open) dialog.showModal();
  dialog.querySelector("[data-close-reader]").focus(); initIcons();
}
function closeDiscoveryReader() { $("#discovery-reader").close(); discoveryReaderReturn?.isConnected && discoveryReaderReturn.focus(); }
function renderDiscoveryCriteria() {
  const c = discoveryCriteria, active = UniWayDiscovery.hasCriteria(c);
  $("#discovery-criteria-count").textContent = active ? "已套用" : "";
  $("#discovery-criteria-result").textContent = active ? "依已公開的合作校條件初篩；待確認不代表不符合。" : "";
}
function discoveryCriteriaMatch(item) {
  const result = UniWayDiscovery.assess(item, discoveryCriteria);
  return result.status === "none" || (discoveryCriteria.mode === "confirmed" ? result.status === "match" : result.status !== "mismatch");
}
function discoveryMatchBadge(item) {
  const match = UniWayDiscovery.assess(item, discoveryCriteria);
  return match.label ? `<details class="discovery-match ${match.status}"><summary>${match.label}</summary><ul>${match.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul></details>` : "";
}
function moveDiscoveryPreference(name, delta, targetName) {
  const order = discoveryData().preference_order, index = order.indexOf(name);
  const target = targetName ? order.indexOf(targetName) : index + delta;
  if (index < 0 || target < 0 || target >= order.length) return;
  order.splice(index,1); order.splice(target,0,name); persistDiscovery(); renderDiscoveryWorkspace();
  [...document.querySelectorAll("[data-rank-school]")].find(el => el.dataset.rankSchool === name)?.focus();
  announce(`${name}已移到第 ${target+1} 志願`, "success");
}
function discoveryCostInfo(item) {
  const profile = destinationProfileForSchool(item.school_name);
  const officialCostUrl = profile?.sources?.find(source => /費用|預算|生活費|cost|budget|fee/i.test(source.title || ""))?.source_url;
  const candidates = [{text:profile?.cost_summary, url:officialCostUrl || profile?.sources?.[0]?.source_url},
    ...[...(item.student_summary_zh?.tuition_points || []), item.tuition_info].map(text => ({text, url:item.source_url}))];
  const cost = candidates.find(row => discoveryChineseSummary({summary:row.text}) && /費|房租|住宿|預算|免繳|每月|每年|\$|€|£/i.test(row.text));
  return {text:cost ? truncate(cost.text, 150) : "費用資料待確認", url:UniWayDiscovery.safeUrl(cost?.url || officialCostUrl)};
}
function discoveryCostSummary(item) { return discoveryCostInfo(item).text; }
function discoveryPreviewExtras(item) {
  const key = `${activeHomeSchool()}::${item.school_name}`, digest = state.experienceCache.get(item.school_name);
  const cost = discoveryCostInfo(item);
  const source = digest?.sources?.find(s => s.summary_zh) || digest?.sources?.[0];
  const failed = discoveryPreviewErrors.has(key);
  const experience = source
    ? `<p>${escapeHtml(truncate(discoveryChineseSummary(source) || "中文摘要待補", 130))}</p><button type="button" class="text-action" data-read-experience="${escapeHtml(registerDiscoverySource(source))}">閱讀心得 ↗</button>`
    : `<p>${digest ? "尚無公開心得" : failed ? "心得載入失敗" : "正在讀取心得…"}</p>${failed ? `<button type="button" data-preview-retry="${escapeHtml(item.school_name)}">重試</button>` : ""}`;
  return `<div class="discovery-preview-extras">
    <section><h5>費用</h5><p>${escapeHtml(cost.text)}</p>${cost.url ? `<a href="${escapeHtml(cost.url)}" target="_blank" rel="noreferrer">費用來源 ↗</a>` : ""}</section>
    <section><h5>學生心得 ${digest ? `<span>${digest.total_sources}</span>` : ""}</h5>${experience}</section>
  </div>`;
}
function loadDiscoveryPreview(item) {
  if (!item) return;
  rememberDiscovery("school", item);
  const home = activeHomeSchool(), key = `${home}::${item.school_name}`;
  if (state.experienceCache.has(item.school_name) || discoveryPreviewRequests.has(key)) return;
  discoveryPreviewErrors.delete(key);
  const request = fetchJson(`/student-experiences?school=${encodeURIComponent(item.school_name)}&home_school=${encodeURIComponent(home)}`)
    .then(digest => { if (activeHomeSchool() === home) state.experienceCache.set(item.school_name, digest); })
    .catch(() => discoveryPreviewErrors.add(key))
    .finally(() => { discoveryPreviewRequests.delete(key); if (activeHomeSchool() === home) partnerMapController?.refreshPreview(); });
  discoveryPreviewRequests.set(key, request);
}
function initDiscovery() {
  discoveryData(); renderDiscoveryRecents();
  document.addEventListener("input", event => {
    const el = event.target;
    if (!el.dataset.schoolNote) return;
    const data = discoveryData(), old = data.school_preferences[el.dataset.schoolNote] || {interest:0};
    data.school_preferences[el.dataset.schoolNote] = {...old, note:el.value.slice(0,1000)};
    persistDiscovery();
  });
  $("#discovery-criteria-form").addEventListener("submit", event => {
    event.preventDefault(); discoveryCriteria = Object.fromEntries(new FormData(event.currentTarget));
    renderDiscoveryCriteria(); renderPartnerTable();
    $("#discovery-criteria").open = false;
  });
  $("#discovery-clear-criteria").addEventListener("click", () => { discoveryCriteria = {}; $("#discovery-criteria-form").reset(); renderDiscoveryCriteria(); renderPartnerTable(); });
  $("#discovery-test").addEventListener("change", event => {
    const input = $("#discovery-score"), limits = { ielts: [0,9,.5], jlpt:[1,5,1], topik:[1,6,1], toefl:[0,120,1], toeic:[0,990,1], duolingo:[0,160,5] };
    const [min,max,step] = limits[event.target.value] || [0,990,.5]; input.min = min; input.max = max; input.step = step; input.value = ""; input.placeholder = event.target.value === "jlpt" ? "N2 請填 2" : "成績";
  });
  $("#discovery-reader").addEventListener("cancel", event => { event.preventDefault(); closeDiscoveryReader(); });
  document.addEventListener("click", event => {
    const target = event.target.closest("button, a"); if (!target) return;
    const d = target.dataset;
    if (d.discoveryShelf) { discoveryShelf = d.discoveryShelf; renderDiscoveryWorkspace(); }
    if (d.interestSchool) {
      const data = discoveryData(), old = data.school_preferences[d.interestSchool] || { note:"", interest:0 };
      data.school_preferences[d.interestSchool] = { ...old, interest: old.interest === Number(d.interest) ? 0 : Number(d.interest) }; persistDiscovery(); renderDiscoveryWorkspace();
      [...document.querySelectorAll("[data-interest-school]")].find(el => el.dataset.interestSchool === d.interestSchool && el.dataset.interest === d.interest)?.focus({preventScroll:true});
    }
    if (d.preferenceToggle) {
      const data = discoveryData(), exists = data.preference_order.includes(d.preferenceToggle);
      if (!exists && data.preference_order.length >= 30) { announce("最多保留 30 個候選志願", "info"); return; }
      data.preference_order = exists ? data.preference_order.filter(n => n !== d.preferenceToggle) : [...data.preference_order, d.preferenceToggle];
      persistDiscovery(); renderDiscoveryWorkspace();
    }
    if (d.rankUp) moveDiscoveryPreference(d.rankUp, -1);
    if (d.rankDown) moveDiscoveryPreference(d.rankDown, 1);
    if (d.experienceTheme) { discoveryTheme = d.experienceTheme; renderDiscoveryExperiences(state.experienceCache.get(state.activeSchool) || {sources:[]}); document.querySelector(`[data-experience-theme="${discoveryTheme}"]`)?.focus({preventScroll:true}); }
    if (d.readExperience) openDiscoveryReader(discoverySourceRegistry.get(d.readExperience) || discoveryData().saved_experiences[d.readExperience]);
    if (d.saveExperience) {
      const data = discoveryData(), source = discoverySourceRegistry.get(d.saveExperience);
      if (data.saved_experiences[d.saveExperience]) delete data.saved_experiences[d.saveExperience];
      else if (source && Object.keys(data.saved_experiences).length < 300) data.saved_experiences[d.saveExperience] = UniWayDiscovery.sourceSnapshot(source);
      persistDiscovery();
      document.querySelectorAll("[data-save-experience]").forEach(button => { if (button.dataset.saveExperience === d.saveExperience) button.outerHTML = discoveryBookmarkButton(source); });
      renderDiscoveryWorkspace(); initIcons();
    }
    if ("closeReader" in d) closeDiscoveryReader();
    if ("openLife" in d) activateDetailTab("detail-life", {focus:true});
    if (d.previewRetry) loadDiscoveryPreview(partnerByName(d.previewRetry));
    if (d.recentSchool) {
      if (!$("#profile-dialog").hidden) closeProfileDialog();
      if (!$("#auth-dialog").hidden) closeAuthDialog();
      const item = partnerByName(d.recentSchool); if (item) openUniversityDetail(item); else announce("此校目前未列於這所母校的合作名單。", "info");
    }
    if (target.id === "discovery-use-preferences") {
      const order = discoveryData().preference_order.filter(n => partnerByName(n)?.availability_status === "open" || partnerByName(n) && !partnerByName(n).availability_status).slice(0,5);
      if (!order.length) { announce("目前志願的本期名額都待確認。", "info"); return; }
      window.location.hash = "#eligibility"; renderEligibilityOptions();
      order.forEach((name,i) => { $(`#eligibility-preference-${i+1}`).value = name; });
      for(let i=order.length;i<5;i++) $(`#eligibility-preference-${i+1}`).value = "";
      announce("已帶入前五個本期開放志願，補齊資料後即可建立申請清單。", "success");
    }
  });
  document.addEventListener("change", event => {
    const el = event.target;
    if (el.dataset.schoolNote) {
      const data = discoveryData(), old = data.school_preferences[el.dataset.schoolNote] || { interest:0 };
      data.school_preferences[el.dataset.schoolNote] = {...old, note:el.value.slice(0,1000)}; persistDiscovery();
      const items = state.dashboard.partner_universities.filter(p => discoveryCompare.has(p.school_name));
      $("#discovery-comparison").innerHTML = items.length ? renderComparison(items) : "";
    }
    if (el.dataset.compareSchool) {
      if (el.checked && discoveryCompare.size >= 3) { el.checked = false; announce("一次比較最多 3 所", "info"); return; }
      el.checked ? discoveryCompare.add(el.dataset.compareSchool) : discoveryCompare.delete(el.dataset.compareSchool);
      const items = state.dashboard.partner_universities.filter(p => discoveryCompare.has(p.school_name));
      $("#discovery-comparison").innerHTML = items.length ? renderComparison(items) : "";
    }
    if (el.id === "discovery-saved-country") { discoverySavedCountry = el.value; discoverySavedSchool = ""; renderSavedDiscoveryExperiences(); }
    if (el.id === "discovery-saved-school") { discoverySavedSchool = el.value; renderSavedDiscoveryExperiences(); }
  });
  let dragged = "";
  document.addEventListener("dragstart", event => { const row = event.target.closest("[data-rank-school]"); if (row) { dragged = row.dataset.rankSchool; event.dataTransfer.setData("text/plain", dragged); } });
  document.addEventListener("dragover", event => { if (dragged && event.target.closest("[data-rank-school]")) event.preventDefault(); });
  document.addEventListener("drop", event => { const row = event.target.closest("[data-rank-school]"); if (dragged && row) { event.preventDefault(); moveDiscoveryPreference(dragged,0,row.dataset.rankSchool); } dragged = ""; });
  document.addEventListener("dragend", () => { dragged = ""; });
  document.addEventListener("keydown", event => { const row = event.target.closest("[data-rank-school]"); if (row && event.altKey && ["ArrowUp","ArrowDown"].includes(event.key)) { event.preventDefault(); moveDiscoveryPreference(row.dataset.rankSchool, event.key === "ArrowUp" ? -1 : 1); } });
}

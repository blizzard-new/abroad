/* Application guide (#guide, #guide=<article>): a three-column docs layout. The articles are authored copy about
   how to use UniWay and how an exchange application is usually organised; anything school-specific (documents,
   deadlines, eligibility) is read from the loaded catalogue or left to the official notice. */
window.UniWayGuide = (() => {
  "use strict";
  const UPDATED = "2026/10/15";
  const STORAGE = "uniway-guide-feedback-v1";
  const DEFAULT_SLUG = "how-to-use";
  const FAQ = { title: "校內甄選和合作校申請有什麼不同？", text: "一般先由就讀學校甄選與提名，再向合作校申請。兩邊的文件與期限可能不同，請分別確認當期公告。" };

  const ARTICLES = [
    {
      slug: "how-to-use", group: "開始之前", title: "UniWay 怎麼用",
      lead: "UniWay 把交換申請拆成四個階段：找學校、準備校內甄選、完成合作校申請、安排出發。每個階段都有對應的工具，公開資料不用登入就能看。",
      callout: { title: "不登入也能開始", text: "瀏覽公開資料不需要登入；收藏、進度與社群功能才需要帳號。" },
      sections: [
        { h: "1. 先選你的就讀學校", p: ["點畫面左上的「切換就讀學校」，選你目前就讀的臺灣大學。UniWay 會依這所學校顯示合作校、資格規則與申請時程。", "學校會顯示在你的帳號與貼文上，選定後 3 天內不能更換。"] },
        { h: "2. 照階段往下走", steps: ["找學校：在「找交換學校」比較國家、語言門檻與名額。", "準備校內甄選：用「資格與志願」對照你的成績與語言檢定，再排志願。", "完成合作校申請：在「申請文件」整理文件，並用「申請日曆」追蹤期限。", "安排出發：用「交換預算」估算費用，再確認簽證、住宿與保險。"] },
        { h: "3. 資料與判斷", p: ["資格初判供參考，正式結果以校方認定為準。每筆合作校資料都附官方來源，送件前請再核對當期公告。"] },
      ],
      links: [["找交換學校", "#partners"], ["資格與志願", "#eligibility"]],
    },
    {
      slug: "exchange-vs-study", group: "開始之前", title: "交換和留學的差別",
      lead: "交換生仍是原就讀學校的學生，到合作校修一學期或一學年的課；學位留學則是直接申請外國學校，取得該校學位。兩條路的申請方式和費用差很多。",
      sections: [
        { h: "1. 一張表看差別", table: { head: ["項目", "交換", "學位留學"], rows: [["註冊學校", "仍在原就讀學校註冊", "外國學校"], ["申請對象", "先向原就讀學校申請，通過後由學校提名", "直接向外國學校申請入學"], ["學費", "多數依與合作校的協議，常以本校學費為主", "繳外國學校學費"], ["學分與學位", "學分是否採計依本校規定，學位仍是本校", "取得外國學校學位"], ["時間", "通常一學期至一學年", "一個學程的完整年限"]] }, note: "各校協議不同，表中是常見情形，實際以就讀學校與合作校當期公告為準。" },
        { h: "2. 該選哪一條？", p: ["想先體驗國外生活、保留本校學籍，交換通常是起點。想取得外國學位或長期留在當地，才需要直接申請學位課程。"] },
      ],
      links: [["找交換學校", "#partners"]],
    },
    {
      slug: "compare-schools", group: "01 找到想去的學校", title: "比較課程與語言門檻",
      lead: "同一所合作校可能有不同的語言方案與名額限制。先看清楚門檻，再決定要不要補成績。",
      sections: [
        { h: "1. 用篩選縮小範圍", p: ["在「找交換學校」先選國家，再依學院、學制與名額狀態縮小範圍。填好「我的條件」後，卡片會標示你是否符合資格。"] },
        { h: "2. 看哪些欄位", table: { head: ["要確認的事", "在哪裡看"], rows: [["語言門檻", "學校詳細資料的「語言門檻」與申請條件"], ["名額與可申請學期", "卡片標籤與學校詳細資料"], ["申請與截止日", "學校詳細資料的「申請方式」"], ["資料來源", "詳細資料中的官方來源連結"]] } },
        { h: "3. 語言成績差一點怎麼辦", p: ["先確認截止日前還來得及補考，再決定是否排進志願。不同方案的門檻可能不同，以合作校當期公告為準。"] },
      ],
      links: [["找交換學校", "#partners"]],
    },
    {
      slug: "living-costs", group: "01 找到想去的學校", title: "估算生活費",
      lead: "每所學校公布的生活費幣別與算法不同，直接比較容易失真。先看官方來源，再用同一幣別估算總成本。",
      sections: [
        { h: "1. 先看學校怎麼說", p: ["學校詳細資料的「生活費參考」會附官方來源。它是規劃用的區間，不是校方報價。"] },
        { h: "2. 再用同一個幣別算", p: ["到「交換預算」輸入住宿、餐飲、交通、保險、簽證與機票，系統會用同一幣別加總，方便比較不同學校。"] },
        { h: "3. 別漏掉這些", list: ["押金與到校第一個月的開銷", "簽證、保險與醫療", "機票與當地交通", "課本、旅遊與突發支出"] },
      ],
      links: [["交換預算", "#budget"]],
    },
    {
      slug: "eligibility", group: "02 準備校內甄選", title: "確認資格與排志願", stage: "02 準備校內甄選",
      lead: "確認資格、排志願，再準備文件。校內甄選通過後，學校會把你提名給合作校，接著才是合作校的正式申請。",
      callout: FAQ,
      sections: [
        { h: "1. 確認資格", p: ["打開「資格與志願」，系統會用你的成績與語言檢定對照每間合作校的門檻。資格初判供參考，正式結果以校方認定為準。"] },
        { h: "2. 準備文件清單", checklist: true },
        { h: "3. 排志願", table: { head: ["順序", "考量", "建議"], rows: [["1", "最想去、條件也符合", "放第一志願，名額少也值得試"], ["2", "條件符合、名額較多", "作為穩定的備案"], ["3", "語言門檻差一點", "確認截止前能補上成績再填"]] }, note: "這是個人準備順序；正式志願數與分發規定仍以本校當期公告為準。" },
      ],
      links: [["資格與志願", "#eligibility"]],
    },
    {
      slug: "study-plan", group: "02 準備校內甄選", title: "讀書計畫怎麼寫",
      lead: "讀書計畫要讓審查的人看懂：你為什麼去、要修什麼、回來後打算怎麼用。具體比華麗重要。",
      sections: [
        { h: "1. 常見的結構", steps: ["動機：為什麼選這個國家與學校，而不是別的地方。", "課程：想修的課，以及它們和你的主修怎麼接起來。", "準備：語言、財務與生活上已經做了哪些準備。", "回國後：學到的東西會怎麼用在學業或職涯。"] },
        { h: "2. 寫之前先查", list: ["字數、格式與語言以當期簡章為準", "合作校實際開的課程與學期", "審查會看哪些面向"] },
        { h: "3. 寫完再檢查", p: ["用「文件檢查」找出漏填、字數與簽名風險，再請指導老師或學長姐看過。"] },
      ],
      links: [["文件檢查", "#document-check"]],
    },
    {
      slug: "interview", group: "02 準備校內甄選", title: "面試準備",
      lead: "校內面試通常圍繞你的讀書計畫與準備程度。把自己寫過的內容講順，比背標準答案有用。",
      sections: [
        { h: "1. 先把自己的文件讀熟", p: ["面試問題多半從讀書計畫與成績延伸。每個你寫下的理由，都要能多說兩句。"] },
        { h: "2. 常被問到的方向", list: ["為什麼想去這所學校", "語言能力與適應計畫", "預算與生活安排", "回國後的規劃"] },
        { h: "3. 時間與地點", p: ["面試時間、地點與形式以學校通知為準，記得把日期排進「申請日曆」。"] },
      ],
      links: [["申請日曆", "#calendar"]],
    },
    {
      slug: "partner-documents", group: "03 完成合作校申請", title: "合作校申請文件",
      lead: "通過校內提名後，合作校會通知你要補哪些文件。文件清單依學校與當期規定不同，先用 UniWay 整理，再對照合作校通知。",
      sections: [
        { h: "1. 先列出清單", p: ["到「申請文件」選目標學校，系統會帶入該校的文件與表單；常見的有申請表、成績單、語言成績與推薦信，實際以合作校通知為準。"] },
        { h: "2. 逐項確認", list: ["份數、簽章與是否需要紙本", "檔案格式與大小限制", "每份文件的截止日"] },
        { h: "3. 送出前", p: ["用「文件檢查」再看一次，確認沒有漏填或過期的文件。"] },
      ],
      links: [["申請文件", "#application-center"], ["文件檢查", "#document-check"]],
    },
    {
      slug: "submit-track", group: "03 完成合作校申請", title: "送件與追蹤",
      lead: "送件不是結束。記下送件方式與日期，才不會在等待期間錯過補件通知。",
      sections: [
        { h: "1. 先搞清楚送件方式", p: ["有的學校線上送件，有的要寄紙本，有的由學校統一轉送。紙本通常以送達日計算，記得預留郵寄時間。"] },
        { h: "2. 記錄進度", p: ["在「申請文件」更新每份文件的狀態；有收據或寄送證明就一併保存。"] },
        { h: "3. 之後的通知", p: ["留意信箱與合作校網站。UniWay 的通知中心會提醒你已排入日曆的期限。"] },
      ],
      links: [["申請日曆", "#calendar"]],
    },
    {
      slug: "visa", group: "04 安排出發與生活", title: "簽證與在留資格",
      lead: "錄取之後，要依目的國規定辦理入境許可。每個國家名稱與流程不同，越早開始越安心。",
      sections: [
        { h: "1. 先查目的國官方規定", p: ["用目的國移民或外交機關的官方網站確認簽證類型、費用與所需時間。有些國家的名稱不同，例如日本會用在留資格。"] },
        { h: "2. 常見要備的文件", list: ["合作校的錄取通知或入學許可", "護照與照片", "財力或保險證明", "學校要求的其他文件"] },
        { h: "3. 時程", p: ["把簽證預約與審查時間排進「申請日曆」，避免出發前才發現來不及。"] },
      ],
      links: [["申請日曆", "#calendar"]],
    },
    {
      slug: "housing-insurance", group: "04 安排出發與生活", title: "住宿與保險",
      lead: "住宿常有申請期限，保險則可能是簽證或入學的條件。兩件事都要早點問清楚。",
      sections: [
        { h: "1. 住宿", p: ["先看合作校是否提供國際生宿舍與申請連結，再考慮校外租屋。宿舍往往要在錄取後很短的時間內申請。"] },
        { h: "2. 保險", p: ["確認合作校與目的國是否要求投保、保障範圍與期間，並了解就醫與理賠流程。"] },
        { h: "3. 抵達前後", list: ["第一晚的落腳處", "接機或交通方式", "當地銀行、手機與生活用品"] },
      ],
      links: [["交換預算", "#budget"]],
    },
  ];

  const bySlug = new Map(ARTICLES.map((article) => [article.slug, article]));
  let currentSlug = DEFAULT_SLUG, filter = "";

  const root = () => document.querySelector("#guide");
  const html = (value) => escapeHtml(String(value));
  const readFeedback = () => { try { return JSON.parse(localStorage.getItem(STORAGE) || "{}"); } catch (_) { return {}; } };
  const writeFeedback = (data) => { try { localStorage.setItem(STORAGE, JSON.stringify(data)); } catch (_) { /* feedback stays on screen */ } };
  const textOf = (article) => [article.title, article.lead, ...article.sections.flatMap((s) => [s.h, ...(s.p || []), ...(s.list || []), ...(s.steps || [])])].join(" ");
  const minutes = (article) => Math.max(1, Math.round(textOf(article).length / 380));
  const slugHref = (slug) => `#guide=${encodeURIComponent(slug)}`;

  function renderToc() {
    const groups = [...new Set(ARTICLES.map((article) => article.group))];
    const query = normalize(filter);
    const html_ = groups.map((group) => {
      const items = ARTICLES.filter((article) => article.group === group && (!query || normalize(textOf(article)).includes(query)));
      if (!items.length) return "";
      return `<div class="pr-toc-group"><small>${html(group)}</small>${items.map((article) => `<a href="${slugHref(article.slug)}"${article.slug === currentSlug ? ' aria-current="page"' : ""}>${html(article.title)}</a>`).join("")}</div>`;
    }).join("");
    root().querySelector("#guide-toc").innerHTML = html_ || '<p class="pr-toc-empty">沒有符合的文章。</p>';
  }

  function checklistHtml() {
    const items = state.dashboard ? documentChecklistItems() : [];
    if (!items.length) return `<p class="pr-guide-note">選好就讀學校後，這裡會列出你的文件清單，並記錄準備進度。</p>`;
    const note = state.account ? "" : '<p class="pr-guide-note">登入後才能記錄準備狀態；清單內容仍可直接查看。</p>';
    return `${note}<div class="pr-todos">${items.map((item) => {
      const done = readinessStatus(item.id) === "ready";
      return `<label class="pr-todo${done ? " done" : ""}"><input type="checkbox" class="document-readiness-checkbox" data-document-id="${html(item.id)}"${done ? " checked" : ""}${state.account ? "" : " disabled"} /><span class="pr-todo-box" aria-hidden="true"><i data-lucide="check"></i></span><span class="pr-todo-label">${html(item.title)}</span><small>${item.conditional ? "符合特定身分時才需要" : ""}</small></label>`;
    }).join("")}</div>`;
  }

  function sectionHtml(section, index, article) {
    const id = `guide-s${index + 1}`;
    const body = [];
    (section.p || []).forEach((text) => body.push(`<p>${html(text)}</p>`));
    if (section.steps) body.push(`<ol class="pr-steps">${section.steps.map((text) => `<li>${html(text)}</li>`).join("")}</ol>`);
    if (section.list) body.push(`<ul class="pr-bullets">${section.list.map((text) => `<li>${html(text)}</li>`).join("")}</ul>`);
    if (section.checklist) body.push(`<div data-guide-checklist>${checklistHtml()}</div>`);
    if (section.table) {
      const { head, rows } = section.table;
      body.push(`<div class="pr-table" role="table" style="--cols:${head.length}"${head[0] === "順序" ? " data-narrow" : ""}><div role="row" class="head">${head.map((cell) => `<span role="columnheader">${html(cell)}</span>`).join("")}</div>${rows.map((row) => `<div role="row">${row.map((cell, i) => `<${i === 0 && head.length > 2 ? "strong" : "span"} role="cell">${html(cell)}</${i === 0 && head.length > 2 ? "strong" : "span"}>`).join("")}</div>`).join("")}</div>`);
    }
    if (section.note) body.push(`<p class="pr-guide-note">${html(section.note)}</p>`);
    return `<h2 id="${id}">${html(section.h)}</h2>${body.join("")}`;
  }

  function neighbours(article) {
    const index = ARTICLES.indexOf(article);
    const card = (target, dir) => target
      ? `<a class="pr-guide-nav ${dir}" href="${slugHref(target.slug)}"><small>${dir === "prev" ? '<i data-lucide="arrow-left" aria-hidden="true"></i>上一篇' : '下一篇<i data-lucide="arrow-right" aria-hidden="true"></i>'}</small><strong>${html(target.title)}</strong></a>`
      : "<span></span>";
    return `<div class="pr-guide-pager">${card(ARTICLES[index - 1], "prev")}${card(ARTICLES[index + 1], "next")}</div>`;
  }

  function schoolLine() {
    const term = state.eligibilityProfile?.targetTerm ? ` ${targetTermLabel(state.eligibilityProfile.targetTerm)}` : "";
    return `適用：${activeHomeSchool()}${term}`;
  }

  function renderArticle(article) {
    const feedback = readFeedback()[article.slug];
    const callout = article.callout ? `<div class="pr-callout"><span><i data-lucide="sparkles" aria-hidden="true"></i></span><div><strong>${html(article.callout.title)}</strong><p>${html(article.callout.text)}</p></div></div>` : "";
    const links = (article.links || []).length ? `<div class="pr-guide-tools">${article.links.map(([label, href]) => `<a class="pr-link" href="${href}"${href !== "#partners" && href !== "#guide" ? " data-requires-home-school" : ""}>${html(label)}<i data-lucide="arrow-up-right" aria-hidden="true"></i></a>`).join("")}</div>` : "";
    root().querySelector("#guide-article").innerHTML = `
      <button id="guide-toc-toggle" type="button" class="pr-toc-toggle" aria-expanded="false" aria-controls="guide-toc-panel"><i data-lucide="book-open" aria-hidden="true"></i><span>目錄 · ${html(article.title)}</span><i data-lucide="chevron-down" aria-hidden="true"></i></button>
      <nav class="pr-crumbs" aria-label="路徑"><a href="#guide">申請指南</a><span aria-hidden="true">/</span><span>${html(article.group)}</span></nav>
      <h1 id="guide-title">${html(article.title)}</h1>
      <p class="pr-guide-meta"><span><i data-lucide="clock" aria-hidden="true"></i>閱讀約 ${minutes(article)} 分鐘</span><span>更新於 ${UPDATED}</span><span>${html(schoolLine())}</span></p>
      <p class="pr-guide-lead">${html(article.lead)}</p>
      ${callout}
      ${article.sections.map((section, index) => sectionHtml(section, index, article)).join("")}
      ${links}
      ${neighbours(article)}
      <p class="pr-guide-feedback">這篇有幫助嗎？
        <button type="button" data-guide-vote="yes" aria-pressed="${feedback === "yes"}">有</button>
        <button type="button" data-guide-vote="no" aria-pressed="${feedback === "no"}">沒有</button>
        <span role="status">${feedback ? "謝謝你的回饋。" : ""}</span>
        <button type="button" class="pr-report" data-guide-report>回報規定錯誤</button></p>`;
  }

  function renderOutline(article) {
    const deadline = (() => { try { return upcomingDeadlines(1)[0]; } catch (_) { return null; } })();
    const days = deadline ? calendarDaysUntil(localDateKey(deadline.date)) : null;
    root().querySelector("#guide-outline").innerHTML = `
      <small>本頁內容</small>
      <nav>${article.sections.map((section, index) => `<a href="#guide-s${index + 1}" data-guide-anchor="guide-s${index + 1}">${html(section.h)}</a>`).join("")}</nav>
      ${deadline ? `<div class="pr-deadline"><strong>${html(deadline.scope || "下一個截止")}</strong><span>${days === 0 ? "就是今天" : `還有 ${days} 天`}</span><small>${html(truncate(deadline.title, 28))}</small><a href="#calendar">加到申請日曆<i data-lucide="arrow-right" aria-hidden="true"></i></a></div>` : ""}`;
  }

  function show(slug = "") {
    const host = root();
    if (!host) return;
    currentSlug = bySlug.has(slug) ? slug : DEFAULT_SLUG;
    const article = bySlug.get(currentSlug);
    renderToc();
    renderArticle(article);
    renderOutline(article);
    document.title = `${article.title}｜申請指南 | UniWay`;
    initIcons();
    watchOutline();
  }

  function watchOutline() {
    const links = [...root().querySelectorAll("[data-guide-anchor]")];
    if (!links.length || !("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver((entries) => {
      entries.filter((entry) => entry.isIntersecting).forEach((entry) => {
        links.forEach((link) => link.classList.toggle("on", link.dataset.guideAnchor === entry.target.id));
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    root().querySelectorAll("#guide-article h2[id]").forEach((heading) => observer.observe(heading));
  }

  document.addEventListener("click", (event) => {
    const host = root();
    if (!host || !host.contains(event.target)) return;
    const toggle = event.target.closest("#guide-toc-toggle");
    if (toggle) {
      const open = toggle.getAttribute("aria-expanded") !== "true";
      toggle.setAttribute("aria-expanded", String(open));
      host.classList.toggle("toc-open", open);
      return;
    }
    if (event.target.closest("#guide-toc a")) host.classList.remove("toc-open");
    const vote = event.target.closest("[data-guide-vote]");
    if (vote) {
      const data = readFeedback();
      data[currentSlug] = vote.dataset.guideVote;
      writeFeedback(data);
      host.querySelectorAll("[data-guide-vote]").forEach((button) => button.setAttribute("aria-pressed", String(button === vote)));
      host.querySelector(".pr-guide-feedback [role='status']").textContent = "謝謝你的回饋。";
      return;
    }
    const report = event.target.closest("[data-guide-report]");
    if (report) {
      if (state.activeWorkflow?.workflow_id) openWorkflowIssueReport(report);
      else announce("規定錯誤要針對某所學校的申請流程回報：請先在「找交換學校」打開該校，到「申請方式」按「回報」。", "info", true);
      return;
    }
    const anchor = event.target.closest("[data-guide-anchor]");
    if (anchor) {
      event.preventDefault();
      document.getElementById(anchor.dataset.guideAnchor)?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    }
  });

  document.addEventListener("input", (event) => {
    if (event.target.id !== "guide-search") return;
    filter = event.target.value;
    renderToc();
  });

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && root() && !root().hidden) {
      event.preventDefault();
      root().querySelector("#guide-search")?.focus();
    }
  });

  // The checklist is re-read when the student ticks a document elsewhere or the catalogue finishes loading.
  function refresh() {
    const host = root();
    if (!host || host.hidden) return;
    const list = host.querySelector("[data-guide-checklist]");
    if (!list) return;
    const focused = document.activeElement?.dataset?.documentId;
    list.innerHTML = checklistHtml();
    if (focused) list.querySelector(`[data-document-id="${CSS.escape(focused)}"]`)?.focus({ preventScroll: true });
    initIcons();
  }

  return { show, refresh, watchOutline, articles: ARTICLES };
})();

(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  function syncStripClearance() {
    const strip = $('#cgu-demo-strip');
    if (!strip) return;
    const h = Math.ceil(strip.getBoundingClientRect().height);
    if (h > 0) {
      document.documentElement.style.setProperty('--cgu-strip-height', `${h}px`);
      document.documentElement.style.setProperty('--cgu-strip-clearance', `${h + 24}px`);
    }
  }
  if (!window.cguDemoStorageIsolated) {
    $('#cgu-demo-strip').textContent = '展示隔離載入失敗，請重新整理；展示重設已停用。';
    syncStripClearance();
    return;
  }
  if (window.cguDemoStorageLimited) $('#cgu-demo-strip span').textContent += '・瀏覽器儲存受限，本機偏好不會保留';
  syncStripClearance();
  if (typeof ResizeObserver === 'function' && $('#cgu-demo-strip')) {
    new ResizeObserver(syncStripClearance).observe($('#cgu-demo-strip'));
  }
  window.addEventListener('resize', syncStripClearance);

  const SIM_BADGE = '模擬・尚未與校方串接';
  const UPLOAD_NOTICE = '展示版不保存檔案內容，請勿上傳真實個資';
  const SELECTION_SOURCE_URL = 'https://www.cgu.edu.tw/oia-ch/Subject/Detail/85785?nodeId=15817';

  const REQUIRED_DOCS = [
    { key: 'online_form', title: '線上申請表', desc: '校內交換／雙聯線上申請表（最多 2 個志願）' },
    { key: 'parent_consent', title: '家長同意書', desc: '依國際處規定格式填寫並經家長／監護人簽章' },
    { key: 'language_proof', title: '語文證明', desc: '多益 700 分（或同等檢定）及合作校要求之語文證明' },
    { key: 'transcript', title: '含排名的中文歷年成績單', desc: '含歷年學業平均與大學部班級排名百分比' },
    { key: 'study_plan', title: '一頁讀書計畫', desc: '以 1 頁為原則，說明選校動機與修課規劃' },
  ];

  const REPORT_SECTIONS = [
    { key: 'preparation', title: '出國前準備' },
    { key: 'academics', title: '上課情形' },
    { key: 'daily_life', title: '日常生活' },
    { key: 'extracurricular', title: '課外活動及其他' },
  ];

  const SAMPLE_REPORT_PARAGRAPHS = {
    preparation: '【虛構示範草稿】出發交換前最重要的準備工作涵蓋語文檢定成績核對、簽證體檢時程規劃、住宿預算評估以及系所專業學分抵免預審。完成長庚大學校內甄選並獲國際事務處正式提名後，我立即依照合作校國際辦公室寄發的入學申請指引，依序完成線上學籍註冊、校內學生宿舍志願填寫、必修疫苗接種證明上傳及全期醫療旅遊保險投保。出發前兩個月我也主動下載目標選修課程的英文教學大綱，與本系導師及系辦確認返國後每學期至少採認三學分專業課程之審查標準，同時完成領航者補助行政契約書簽署、開通海外信用卡動態驗證與當地電信預付方案，並整理好緊急聯絡人名冊與常備藥品英文處方說明，確保抵達當地第一週即可順利安頓生活並準時出席國際新生導向說明會。',
    academics: '【虛構示範草稿】合作校的課堂教學非常重視問題導向式小組討論、實驗室跨領域專題實作以及每週指定期刊文獻的批判性閱讀反思。本學期我共修讀生醫感測工程導論、醫療訊號處理實務與跨文化科技溝通等三門全英文授課專業課程，課程評量方式多元，包含期中實驗架構設計提案、雙週程式模擬進度審查、團隊技術報告撰寫以及期末公開海報口頭發表。授課教授與實驗助教在每週固定的課後諮詢時間都十分親切且具耐心，經常協助國際交換生釐清儀器操作規範、統計分析方法與學術論文引用格式。透過與來自不同學術背景的當地學生共同分工完成專題原型測試，我不僅大幅強化了生醫工程專業英文詞彙的臨場表達流暢度，也深刻體會到主動提問與嚴謹實驗紀錄在國際學術環境中的核心價值。',
    daily_life: '【虛構示範草稿】合作校園區與周邊城鎮的日常生活機能相當完善便利，從我入住的校內單人雅房學生宿舍步行約十分鐘即可抵達總圖書館、生醫工程實驗大樓、學生活動中心與室內運動場館；若需前往市中心大型連鎖超市或亞洲食材行採購日常用品，憑國際學生證搭乘市區公車與輕軌亦享有學生票價優惠。由於當地餐廳外食費用明顯高於台灣，平日我多半與同樓層來自歐洲及大洋洲的室友在宿舍公共廚房輪流下廚準備早晚餐與隔日午餐便當，不僅能將每月伙食與生活開銷穩定控制在原先規劃的領航者補助與個人預算範圍內，更常透過分享滷肉飯、蛋餅等台灣家常料理拉近彼此距離。此外，校內健康照護中心與國際學生輔導室在迎新週便清楚說明預約看診流程、夜間校園安全專線與心理支持管道，讓整學期的海外居住既充實又安心。',
    extracurricular: '【虛構示範草稿】在課業與實驗室時間之外，我也積極參與合作校國際學生會籌辦的歷史城區文化導覽、每週語言交換下午茶會以及戶外自然步道健行社團，結識了許多來自德國、瑞典、紐西蘭、日本與韓國姊妹校的交換夥伴。期中教學休息週期間，我們更自行組成六人小隊共同規劃跨城市鐵路與長途巴士考察行程，從青年旅館比價、交通轉乘時刻銜接到突發天候備案皆由團隊分工合作完成，實際鍛鍊了跨文化協調與海外旅途風險應變能力。學期末校園舉辦國際文化嘉年華時，我與幾位台灣同學合力設置文化攤位，向當地師生介紹台灣特色飲食與長庚大學校園學習環境，獲得現場熱烈迴響。這趟珍貴的海外交換研修不僅拓展了生醫工程國際視野，更培養出獨立解決問題的自信，非常鼓勵學弟妹提早準備語文檢定並善用校內資源勇敢提出申請。',
  };

  // Register custom CGU demo pages into UniWay's route sets
  if (typeof UNIVERSITY_PAGE_ROUTES !== 'undefined') {
    for (const [route, title] of [
      ['school-connector', '校方介接'],
      ['ask-oia', '問國際處'],
      ['return-report', '返國心得'],
      ['oia-view', '國際處視角（模擬）'],
    ]) {
      UNIVERSITY_PAGE_ROUTES.add(route);
      if (typeof UNIVERSITY_PAGE_TITLES === 'object') UNIVERSITY_PAGE_TITLES[route] = title;
      if (typeof METRO_PAGES !== 'undefined') METRO_PAGES.add(route);
    }
  }

  const HIDDEN_COMMUNITY_HASHES = new Set([
    '#forum', '#feedback', '#public-board', '#language-school-board', '#following',
    '#university-posts', '#cgu-posts', '#cgu-feed', '#university-feed', '#community-hub',
  ]);

  function isHiddenCommunityHash(hash = window.location.hash) {
    return HIDDEN_COMMUNITY_HASHES.has(hash)
      || hash.startsWith('#board=')
      || hash.startsWith('#post=');
  }

  function guardHiddenRoutes() {
    if (isHiddenCommunityHash(window.location.hash)) {
      history.replaceState(history.state, '', '#home');
      if (typeof applyAppRoute === 'function') applyAppRoute({ loadFeed: false, resetScroll: true });
      return true;
    }
    return false;
  }

  // Keep shared platform private uploads disabled while allowing our metadata-only [data-cgu-sim-upload] inputs.
  const lockSchoolSwitcher = () => {
    const switcher = $('#school-switcher');
    if (switcher) {
      switcher.disabled = true;
      switcher.removeAttribute('aria-haspopup');
      switcher.removeAttribute('aria-controls');
      switcher.removeAttribute('aria-expanded');
      switcher.setAttribute('aria-label', '長庚大學');
      switcher.querySelectorAll('small, [data-lucide="chevron-down"], .lucide-chevron-down').forEach(el => el.remove());
    }
    const switcherLabel = $('#school-switcher-label');
    if (switcherLabel && switcherLabel.textContent !== '長庚大學') switcherLabel.textContent = '長庚大學';
    const mobileLabel = $('#mobile-school-label');
    if (mobileLabel && mobileLabel.textContent !== '長庚大學') mobileLabel.textContent = '長庚大學';
    document.querySelectorAll('input[name="home_university"]').forEach(inp => {
      if (inp.value !== '長庚大學') inp.value = '長庚大學';
      inp.readOnly = true;
      inp.setAttribute('aria-readonly', 'true');
    });
  };

  if (typeof setHomeSchool === 'function') {
    const origSetHomeSchool = setHomeSchool;
    setHomeSchool = function (schoolName, ...rest) {
      return origSetHomeSchool.call(this, '長庚大學', ...rest);
    };
  }

  if (typeof updateSchoolContext === 'function') {
    const origUpdateSchoolContext = updateSchoolContext;
    updateSchoolContext = function (...args) {
      const res = origUpdateSchoolContext.apply(this, args);
      lockSchoolSwitcher();
      return res;
    };
  }

  if (typeof applyAppRoute === 'function') {
    const origApplyAppRoute = applyAppRoute;
    applyAppRoute = function (opts) {
      if (isHiddenCommunityHash(window.location.hash)) {
        history.replaceState(history.state, '', '#home');
        return origApplyAppRoute.call(this, { ...(opts || {}), loadFeed: false });
      }
      return origApplyAppRoute.call(this, opts);
    };
  }

  const restrictControls = () => {
    document.querySelectorAll(
      'input[type="file"]:not([data-cgu-sim-upload]), [data-ex-upload], [data-ex-extract], [data-ex-files], [data-ex-download-file], #exchange-peer-form button[type="submit"]'
    ).forEach(control => {
      control.disabled = true;
      control.title = '展示未開放私人文件上傳、附件解析或公開發布；請使用虛構文字情境。';
    });
    lockSchoolSwitcher();
  };
  restrictControls();

  // Block any programmatic or keyboard attempt to open school onboarding
  $('#school-switcher')?.addEventListener('click', event => {
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);

  const dialog = $('#cgu-demo-dialog');
  const body = $('#cgu-demo-dialog-body');
  const status = $('#cgu-demo-status');
  const confirmBtn = $('#cgu-demo-confirm');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const shortSchool = name => String(name || '').replace(/\s+[A-Za-z(（].*$/, '').trim() || String(name || '');
  const countChars = text => String(text || '').replace(/\s+/g, '').length;
  const formatBytes = bytes => {
    const n = Number(bytes || 0);
    if (n < 1024) return `${n} B`;
    return `${(n / 1024).toFixed(1)} KB`;
  };
  const formatTime = iso => {
    if (!iso) return '待處理';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso);
    return d.toLocaleString('zh-TW', {
      timeZone: 'Asia/Taipei',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  async function apiJson(url, options = {}) {
    const res = await fetch(url, {
      credentials: 'same-origin',
      headers: {
        ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
      },
      ...options,
    });
    let data = {};
    try {
      data = await res.json();
    } catch (_) {
      data = {};
    }
    if (!res.ok) {
      const err = new Error(typeof data.detail === 'string' ? data.detail : '操作失敗，請稍後再試');
      err.payload = data;
      err.status = res.status;
      throw err;
    }
    return data;
  }

  const show = (title, html) => {
    $('#cgu-demo-dialog-title').textContent = title;
    body.innerHTML = html;
    status.textContent = '';
    confirmBtn.hidden = true;
    if (!dialog.open) dialog.showModal();
    $('#cgu-demo-close').focus();
  };
  $('#cgu-demo-close').onclick = () => dialog.close();
  $('#cgu-demo-info').onclick = async () => {
    show('來源與展示說明', '<p>正在載入來源…</p>');
    try {
      const response = await fetch('/demo/content');
      if (!response.ok) throw new Error('來源暫時無法載入');
      const data = await response.json();
      body.innerHTML = '<p>此站共用 UniWay 原平台介面與功能，固定為長庚大學。林小程（生物醫學工程學系 大三・多益 750）為虛構示範學生，未經校方身分驗證。展示不代表校方採用、認證或背書。</p><p>每個瀏覽器有獨立展示工作區。進度暫存在此展示服務，重新整理可保留；24 小時後或服務重啟會清除。不要輸入真實個資或上傳私人文件。</p><p>合作校名冊（78 所）、表列名額、合作校參考截止日、語言門檻、領航者補助要點與 116-1 校內申請時程已與 UniWay 主站同步；送件前仍請核對長庚國際事務處最新公告與目的校提名信。</p>' + data.rules.map(rule => `<h3>${esc(rule.title)}</h3><p>${esc(rule.body)}</p>`).join('') + data.sources.map(source => `<p><a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗</a><br>查核：${esc(source.checked_on)}；${esc(source.scope)}</p>`).join('') + '<h3>三階段合作架構（模擬・尚未與校方串接）</h3><p>目前以抽象介面 SchoolConnector 搭配 MockCguConnector 模擬校內送件、規則式問答、返國心得與國際處承辦收件匣。第一階段：不需校方配合（公開資料整理與自我預檢）；第二階段：小型試辦（檢核表與 FAQ 試用）；第三階段：需校方資訊單位（SSO 與正式 API 替換）。錄取與抵免均由校方決定。</p>';
    } catch (error) {
      body.textContent = error.message + '，請稍後再試。';
    }
  };
  $('#cgu-demo-reset').onclick = () => {
    show('重設我的展示資料', '<p>只刪除這個瀏覽器的虛構學生申請紀錄、模擬送件、詢問單、返國心得、承辦操作、通知與本機變更（並還原林小程預設示範系所條件），其他訪客及正式 UniWay 資料不受影響。</p>');
    confirmBtn.hidden = false;
  };
  confirmBtn.onclick = async () => {
    confirmBtn.disabled = true;
    try {
      const response = await fetch('/demo/reset', { method: 'POST' });
      if (!response.ok) throw new Error('重設失敗，請稍後再試');
      window.localStorage.clear();
      window.sessionStorage.clear();
      location.href = '/';
    } catch (error) {
      status.textContent = error.message;
    } finally {
      confirmBtn.disabled = false;
    }
  };
  $('#cgu-demo-seed').onclick = async () => {
    show('載入示範申請', '<p>以原平台的申請流程建立林小程（生物醫學工程學系 大三）的 2027 秋季（116-1）研究目標；當期資格與名額待確認。已有相同計畫時直接開啟。</p>');
    try {
      const response = await fetch('/account/application-paths?home_school=' + encodeURIComponent('長庚大學'));
      if (!response.ok) throw new Error('無法載入展示工作區');
      const registry = await response.json();
      const made = await fetch('/account/application-paths', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          revision: registry.revision,
          home_school: '長庚大學',
          target_school: '林肯大學 Lincoln University',
          academic_year: '116',
          application_round: '116-1（2027 秋季出國）',
          departure_year: '2027',
          semester: 'fall',
        }),
      });
      if (!made.ok) {
        const error = await made.json();
        throw new Error(typeof error.detail === 'string' ? error.detail : '建立失敗，請稍後再試');
      }
      const expectedSearch = '?home=' + encodeURIComponent('長庚大學');
      const targetUrl = '/' + expectedSearch + '#my-application';
      if (location.pathname === '/' && location.search === expectedSearch) {
        location.hash = '#my-application';
        location.reload();
      } else {
        location.assign(targetUrl);
      }
    } catch (error) {
      status.textContent = error.message;
    }
  };

  // ──────────────────────────────────────────────────────────────
  // OIA Perspective Switcher in #cgu-demo-strip
  // ──────────────────────────────────────────────────────────────
  let lastStudentHash = '#my-application';

  function syncPerspectiveButton() {
    const btn = $('#cgu-demo-oia-toggle');
    if (!btn) return;
    const isOia = window.location.hash === '#oia-view';
    document.body.dataset.cguPerspective = isOia ? 'oia' : 'student';
    btn.setAttribute('aria-pressed', String(isOia));
    btn.textContent = isOia ? '切換回學生視角' : '切換為國際處視角';
    btn.classList.toggle('is-active-oia', isOia);
    syncStripClearance();
  }

  $('#cgu-demo-oia-toggle')?.addEventListener('click', () => {
    if (window.location.hash === '#oia-view') {
      window.location.hash = lastStudentHash || '#my-application';
    } else {
      if (window.location.hash && window.location.hash !== '#oia-view') {
        lastStudentHash = window.location.hash;
      }
      window.location.hash = '#oia-view';
    }
  });

  // ──────────────────────────────────────────────────────────────
  // Enhance「我的申請」->「下一個已確認的官方期限」with 116-1 2026/12/21 17:00 + source
  // ──────────────────────────────────────────────────────────────
  function enhanceMyApplicationDeadline() {
    const panel = document.querySelector('#today-view .today-panel[aria-label="期限"]');
    if (panel && !panel.querySelector('.cgu-deadline-source-link')) {
      const existingStepLink = panel.querySelector('a[href^="#my-application"]');
      const existingPill = panel.querySelector('.today-pill');
      const pillHtml = existingPill ? existingPill.outerHTML : '<span class="today-pill">校內截止</span>';
      const stepLinkHtml = existingStepLink
        ? `<a class="today-link" href="${esc(existingStepLink.getAttribute('href') || '#my-application')}">前往這一項 →</a>`
        : '';
      panel.innerHTML = `
        <h3>下一個已確認的官方期限</h3>
        <p class="today-date">2026/12/21 17:00</p>
        <p><b>116-1 校內申請截止</b> ${pillHtml}</p>
        <p>2026/11/02 開放線上表單，2026/12/21 17:00 校內截止（紙本資料須於截止前送交國際事務處）。</p>
        <div class="cgu-deadline-links">
          ${stepLinkHtml}
          <a class="today-link cgu-deadline-source-link" href="${esc(SELECTION_SOURCE_URL)}" target="_blank" rel="noopener noreferrer">公告來源：116-1 交換及雙聯申請公告 ↗</a>
        </div>`;
    }
    const headerCard = document.querySelector('#application-path #deadline-card');
    if (headerCard && headerCard.innerHTML.trim() && !headerCard.querySelector('.cgu-deadline-source-link')) {
      const link = document.createElement('a');
      link.className = 'cgu-deadline-inline-source cgu-deadline-source-link';
      link.href = SELECTION_SOURCE_URL;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = '116-1 校內申請截止 2026/12/21 17:00（查看官方公告 ↗）';
      headerCard.querySelector('div')?.appendChild(link);
    }
  }

  // ──────────────────────────────────────────────────────────────
  // Sync Notification Bell Badge & Simulated Notification Labels
  // ──────────────────────────────────────────────────────────────
  function enhanceNotificationItems() {
    const badge = $('#notification-badge');
    const button = $('#notification-button');
    if (typeof state === 'object' && state) {
      if (button && state.account && button.hidden) button.hidden = false;
      if (badge) {
        const count = Number(state.notificationUnreadCount || 0);
        const shouldHide = count < 1;
        const nextText = count > 0 ? String(count) : '';
        if (badge.hidden !== shouldHide) badge.hidden = shouldHide;
        if (badge.textContent !== nextText) badge.textContent = nextText;
      }
    }
    document.querySelectorAll('#notification-center-list .notification-center-item').forEach(card => {
      const metaSpan = card.querySelector('.notification-center-item-meta span');
      if (metaSpan && /截止前\s*0\s*天/.test(metaSpan.textContent || '')) {
        metaSpan.innerHTML = `<strong class="cgu-sim-badge-inline">${esc(SIM_BADGE)}</strong>`;
      }
    });
  }

  async function refreshNotificationsNow() {
    if (typeof loadNotifications === 'function') {
      try {
        await loadNotifications({ quiet: true });
      } catch (_) { /* ignore transient error */ }
    }
    enhanceNotificationItems();
  }

  // Close notification dialog cleanly when clicking an internal hash action link
  $('#notification-center-list')?.addEventListener('click', event => {
    const openLink = event.target.closest('[data-open-notification]');
    if (openLink && typeof closeNotificationDialog === 'function') {
      const href = openLink.getAttribute('href') || '';
      if (href.startsWith('#')) {
        closeNotificationDialog();
      }
    }
  });

  // ──────────────────────────────────────────────────────────────
  // Shared Connector State & Partner Options Helper
  // ──────────────────────────────────────────────────────────────
  const simState = {
    spec: null,
    status: null,
    oia: null,
    oiaFilter: 'all',
    selectedPref1: '林肯大學 Lincoln University',
    selectedPref2: '',
    lastAskQuestion: '',
    lastAskResult: null,
    reportDraft: {
      partner_school: '林肯大學 Lincoln University',
      term: '116-1（2027 秋季）',
      author_title: '工學院・生物醫學工程學系 大三（示範資料）',
      sections: { preparation: '', academics: '', daily_life: '', extracurricular: '' },
      video_url: '',
      public_consent: true,
    },
  };

  function getPartnerSchoolNames() {
    const list = (typeof state === 'object' && state.dashboard?.partner_universities) || [];
    const names = list.map(p => p.school_name).filter(Boolean);
    if (!names.length) {
      return [
        '林肯大學 Lincoln University',
        '明尼蘇達大學 University of Minnesota',
        '瑞典皇家理工學院 KTH Royal Institute of Technology',
        '韓國嘉泉大學 Gachon University',
      ];
    }
    return names;
  }

  function renderPartnerOptions(selected, includeEmpty = false) {
    const schools = getPartnerSchoolNames();
    const head = includeEmpty ? `<option value=""${!selected ? ' selected' : ''}>（不選填第二志願）</option>` : '';
    return head + schools.map(name => `<option value="${esc(name)}"${name === selected ? ' selected' : ''}>${esc(name)}</option>`).join('');
  }

  // ──────────────────────────────────────────────────────────────
  // Feature 2: 校方介接規格頁 (#cgu-connector-spec-page)
  // ──────────────────────────────────────────────────────────────
  async function renderConnectorSpecPage() {
    const host = $('#cgu-connector-spec-page');
    if (!host) return;
    if (!simState.spec) {
      host.innerHTML = `<div class="cgu-sim-card"><span class="cgu-sim-badge">${esc(SIM_BADGE)}</span><h1 id="cgu-connector-spec-title">校方介接規格載入中…</h1></div>`;
      try {
        simState.spec = await apiJson('/demo/connector/spec');
      } catch (err) {
        host.innerHTML = `<div class="cgu-sim-card"><span class="cgu-sim-badge">${esc(SIM_BADGE)}</span><h1 id="cgu-connector-spec-title">校方介接規格</h1><p class="cgu-sim-error">${esc(err.message)}</p></div>`;
        return;
      }
    }
    const spec = simState.spec;
    const rowsHtml = (spec.interfaces || []).map(row => `
      <tr>
        <td><code>${esc(row.method)}</code></td>
        <td>${esc(row.purpose)}</td>
        <td><small>${esc(row.request_fields)}</small></td>
        <td><small>${esc(row.response_fields)}</small></td>
        <td>${esc(row.school_requirements)}</td>
        <td><span class="cgu-status-chip is-sim">${esc(row.current_status)}</span></td>
      </tr>`).join('');

    const phasesHtml = (spec.collaboration_phases || []).map((p, idx) => `
      <article class="cgu-phase-card">
        <span class="cgu-phase-step">階段 ${idx + 1}</span>
        <h3>${esc(p.phase)}</h3>
        <strong class="cgu-phase-scope">${esc(p.scope || '')}</strong>
        <p>${esc(p.details)}</p>
      </article>`).join('');

    host.innerHTML = `
      <div class="cgu-sim-card">
        <header class="cgu-sim-head">
          <div>
            <div class="cgu-sim-badges-row">
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <span class="cgu-arch-pill">介面：<code>${esc(spec.interface_class || 'SchoolConnector')}</code> → 目前實作：<code>${esc(spec.connector_class || 'MockCguConnector')}</code></span>
            </div>
            <h1 id="cgu-connector-spec-title">長庚大學校方介接規格與合作分期</h1>
            <p class="cgu-sim-lead">${esc(spec.summary || '')}</p>
          </div>
          <div class="cgu-sim-head-actions">
            <a class="cgu-pill-action is-solid" href="#my-application">前往學生端模擬送件 →</a>
            <button type="button" class="cgu-pill-action" data-cgu-open-oia="1">查看國際處視角（模擬）</button>
          </div>
        </header>

        <section class="cgu-spec-block" aria-labelledby="cgu-spec-table-title">
          <h2 id="cgu-spec-table-title">一、SchoolConnector 四項標準介接方法</h2>
          <div class="cgu-table-wrap">
            <table id="cgu-connector-spec-table" class="cgu-spec-table">
              <thead>
                <tr>
                  <th scope="col">接口方法</th>
                  <th scope="col">用途</th>
                  <th scope="col">送出欄位</th>
                  <th scope="col">回傳欄位</th>
                  <th scope="col">需要校方提供的項目</th>
                  <th scope="col">目前狀態</th>
                </tr>
              </thead>
              <tbody>${rowsHtml}</tbody>
            </table>
          </div>
        </section>

        <section class="cgu-spec-block" aria-labelledby="cgu-spec-phases-title">
          <h2 id="cgu-spec-phases-title">二、三階段合作規劃</h2>
          <div class="cgu-phases-grid">${phasesHtml}</div>
        </section>
      </div>`;
  }

  // ──────────────────────────────────────────────────────────────
  // Feature 3: 學生端「送交國際處（模擬）」inside #my-application
  // ──────────────────────────────────────────────────────────────
  async function loadConnectorStatus() {
    simState.status = await apiJson('/demo/connector/status');
    return simState.status;
  }

  function renderTimelineHtml(timeline = []) {
    return `<ol class="cgu-sim-timeline" aria-label="申請狀態時間軸">
      ${timeline.map(step => {
        const st = step.state || 'pending';
        return `<li class="cgu-tl-step is-${esc(st)}">
          <div class="cgu-tl-dot" aria-hidden="true"></div>
          <div class="cgu-tl-body">
            <strong>${esc(step.label)}</strong>
            <small>${step.at ? esc(formatTime(step.at)) : '尚未到達'}</small>
            ${step.note ? `<p>${esc(step.note)}</p>` : ''}
          </div>
        </li>`;
      }).join('')}
    </ol>`;
  }

  async function renderMyApplicationSim(forceReload = false) {
    const host = $('#cgu-my-application-sim');
    if (!host) return;
    if (!simState.status || forceReload) {
      try {
        await loadConnectorStatus();
      } catch (err) {
        host.innerHTML = `<div class="cgu-sim-card"><span class="cgu-sim-badge">${esc(SIM_BADGE)}</span><p class="cgu-sim-error">${esc(err.message)}</p></div>`;
        return;
      }
    }
    const st = simState.status;
    const precheck = st.precheck || { complete: false, missing_documents: REQUIRED_DOCS, provided_count: 0, required_count: 5 };
    const draftFiles = st.draft_files || {};
    const missingNames = (precheck.missing_documents || []).map(d => d.title);

    const docRowsHtml = REQUIRED_DOCS.map((doc, idx) => {
      const uploaded = draftFiles[doc.key];
      return `
        <li class="cgu-doc-check-row ${uploaded ? 'is-ready' : 'is-missing'}" data-doc-row="${esc(doc.key)}">
          <div class="cgu-doc-check-info">
            <div class="cgu-doc-check-title">
              <span class="cgu-doc-num">${idx + 1}</span>
              <strong>${esc(doc.title)}</strong>
              <span class="cgu-doc-status-pill ${uploaded ? 'is-ok' : 'is-lack'}">${uploaded ? '已備齊（僅存雜湊）' : '缺件'}</span>
            </div>
            <p class="cgu-doc-desc">${esc(doc.desc)}</p>
            ${uploaded ? `
              <div class="cgu-file-meta-box">
                <span><b>檔名：</b>${esc(uploaded.filename)}</span>
                <span><b>大小：</b>${esc(formatBytes(uploaded.size))}（${esc(uploaded.size)} bytes）</span>
                <span><b>類型：</b>${esc(uploaded.content_type)}</span>
                <span class="cgu-sha-line"><b>SHA-256：</b><code title="${esc(uploaded.sha256)}">${esc(uploaded.sha256)}</code></span>
              </div>
            ` : ''}
          </div>
          <div class="cgu-doc-check-actions">
            <label class="cgu-upload-btn">
              <span>${uploaded ? '重新選檔' : '選擇檔案'}</span>
              <input type="file" data-cgu-sim-upload="${esc(doc.key)}" aria-label="選擇${esc(doc.title)}檔案（僅計算雜湊）" />
            </label>
            <button type="button" class="cgu-sample-btn" data-cgu-sim-sample="${esc(doc.key)}">帶入示範檔</button>
            ${uploaded ? `<button type="button" class="cgu-remove-file-btn" data-cgu-sim-remove="${esc(doc.key)}">移除</button>` : ''}
          </div>
        </li>`;
    }).join('');

    const apps = st.applications || [];
    const appCardsHtml = apps.length
      ? apps.map(app => `
        <article class="cgu-submitted-card" data-receipt-id="${esc(app.receipt_id)}">
          <header class="cgu-submitted-head">
            <div>
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <strong class="cgu-receipt-code">收件編號：${esc(app.receipt_id)}</strong>
            </div>
            <span class="cgu-status-chip status-${esc(app.status)}">${esc(app.status_label)}</span>
          </header>
          <p class="cgu-submitted-meta">
            <span>送出時間：<b>${esc(formatTime(app.submitted_at))}</b></span>
            <span>第一志願：<b>${esc(app.preference_1)}</b></span>
            ${app.preference_2 ? `<span>第二志願：<b>${esc(app.preference_2)}</b></span>` : ''}
          </p>
          ${app.supplement_reason ? `<div class="cgu-supplement-alert" role="alert"><strong>國際處要求補件原因：</strong>${esc(app.supplement_reason)}</div>` : ''}
          ${renderTimelineHtml(app.timeline || [])}
        </article>`).join('')
      : '<p class="cgu-empty-hint">目前尚無模擬送件紀錄。完成上方 5 項應備文件完整性預檢後即可送出取得 <code>SIM-</code> 開頭編號。</p>';

    host.innerHTML = `
      <div class="cgu-sim-card">
        <div class="cgu-my-app-deadline-bar" aria-label="下一個已確認的官方期限摘要">
          <div>
            <span class="cgu-dl-kicker">下一個已確認的官方期限</span>
            <strong>116-1 校內申請截止：2026/12/21 17:00</strong>
          </div>
          <a href="${esc(SELECTION_SOURCE_URL)}" target="_blank" rel="noopener noreferrer">官方公告來源：116 學年度第 1 學期交換及雙聯申請公告 ↗</a>
        </div>

        <header class="cgu-sim-head">
          <div>
            <div class="cgu-sim-badges-row">
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <span class="cgu-paper-reminder">實際申請仍須依國際處公告填線上表單並繳交紙本。</span>
            </div>
            <h2 id="cgu-sim-submit-heading">送交國際處（模擬）— 校內五項應備文件預檢</h2>
            <p class="cgu-sim-lead">依長庚國際事務處規定逐項預檢 5 份校內應備文件；缺件時列出缺漏項目且不可送出。齊全後可模擬送件取得 <code>SIM-</code> 收件編號與狀態時間軸。</p>
          </div>
          <div class="cgu-sim-head-actions">
            <a class="cgu-pill-action" href="#ask-oia">問國際處（FAQ／詢問）</a>
            <a class="cgu-pill-action" href="#return-report">填寫返國心得</a>
            <a class="cgu-pill-action" href="#school-connector">校方介接規格</a>
          </div>
        </header>

        <div class="cgu-upload-privacy-banner" role="note">
          <strong>檔案雜湊保護機制：</strong>${esc(UPLOAD_NOTICE)}（檔案於記憶體計算 SHA-256 後即刻丟棄，單檔上限 250 KB，磁碟絕不留存檔案內容）。
        </div>

        <div class="cgu-pref-grid">
          <label>
            <span>第一志願合作校（必選）</span>
            <select id="cgu-sim-pref1">${renderPartnerOptions(simState.selectedPref1, false)}</select>
          </label>
          <label>
            <span>第二志願合作校（選填，最多 2 個志願）</span>
            <select id="cgu-sim-pref2">${renderPartnerOptions(simState.selectedPref2, true)}</select>
          </label>
        </div>

        <div class="cgu-doc-toolbar">
          <strong>官方應備 5 項文件（目前已備齊 ${precheck.provided_count} / ${precheck.required_count} 項）</strong>
          <button type="button" id="cgu-sim-fill-all" class="cgu-pill-action">一鍵帶入全部示範測試檔</button>
        </div>

        <ul id="cgu-sim-doc-list" class="cgu-doc-check-list">${docRowsHtml}</ul>

        <div id="cgu-sim-precheck-box" class="cgu-precheck-box ${precheck.complete ? 'is-complete' : 'is-incomplete'}" role="status" aria-live="polite">
          ${precheck.complete
            ? '<strong>完整性預檢通過：</strong>5 項官方應備文件均已登錄雜湊，可送交模擬收件匣。'
            : `<strong>完整性預檢未通過（缺件不可送出）：</strong>尚缺 <b>${missingNames.length}</b> 項文件 — <span class="cgu-missing-names">${esc(missingNames.join('、'))}</span>`
          }
        </div>

        <p id="cgu-sim-submit-feedback" class="cgu-sim-feedback" role="status" aria-live="polite"></p>

        <div class="cgu-sim-submit-bar">
          <button type="button" id="cgu-sim-precheck-btn" class="cgu-pill-action">執行完整性預檢</button>
          <button type="button" id="cgu-sim-submit-btn" class="cgu-pill-action is-solid" ${precheck.complete ? '' : 'disabled'}>送交國際處（模擬）</button>
          <span class="cgu-paper-side-note">註：實際申請仍須依國際處公告填線上表單並繳交紙本。</span>
        </div>

        <section class="cgu-submitted-section" aria-labelledby="cgu-submitted-list-title">
          <div class="cgu-submitted-section-head">
            <h3 id="cgu-submitted-list-title">我的模擬送件與狀態時間軸</h3>
            <button type="button" class="cgu-text-btn" data-cgu-refresh-status="1">重新同步狀態</button>
          </div>
          <div id="cgu-sim-app-records">${appCardsHtml}</div>
        </section>
      </div>`;
  }

  async function uploadMetadataFile(docKey, file) {
    const fd = new FormData();
    fd.append('doc_key', docKey);
    fd.append('file', file, file.name);
    await apiJson('/demo/connector/files', { method: 'POST', body: fd });
  }

  function buildSyntheticSampleFile(docKey) {
    const doc = REQUIRED_DOCS.find(d => d.key === docKey) || { key: docKey, title: docKey };
    const content = `CGU-DEMO-SYNTHETIC-SAMPLE\ndoc_key=${doc.key}\ntitle=${doc.title}\nstudent=林小程（展示資料）\nnotice=${UPLOAD_NOTICE}\n`;
    return new File([content], `林小程_${doc.title}_示範檔.pdf`, { type: 'application/pdf' });
  }

  // ──────────────────────────────────────────────────────────────
  // Feature 4: 學生端「問國際處」(#cgu-ask-oia-page)
  // ──────────────────────────────────────────────────────────────
  async function renderAskOiaPage(forceReload = false) {
    const host = $('#cgu-ask-oia-page');
    if (!host) return;
    if (!simState.status || forceReload) {
      try {
        await loadConnectorStatus();
      } catch (_) { /* handled gracefully */ }
    }
    const inquiries = simState.status?.inquiries || [];
    const res = simState.lastAskResult;

    let resultHtml = '';
    if (res) {
      if (res.matched && (res.matches || []).length) {
        resultHtml = `
          <div id="cgu-ask-result-box" class="cgu-ask-result is-hit" role="region" aria-label="規則比對結果">
            <div class="cgu-sim-badges-row">
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <span class="cgu-rule-mode-badge">${esc(res.mode_label || '規則式比對，非 AI')}</span>
            </div>
            <h3>已命中收錄規則／FAQ（共 ${res.matches.length} 筆相關說明）</h3>
            <div class="cgu-faq-hits">
              ${res.matches.map(m => `
                <article class="cgu-faq-hit-card">
                  <strong>${esc(m.topic || m.question)}</strong>
                  <p>${esc(m.answer)}</p>
                  <div class="cgu-faq-hit-foot">
                    <span>命中關鍵字：${esc((m.matched_keywords || []).join('、'))}</span>
                    <a href="${esc(m.source_url)}" target="_blank" rel="noopener noreferrer">官方來源：${esc(m.source_title)} ↗</a>
                  </div>
                </article>`).join('')}
            </div>
            <div class="cgu-ask-escalate-bar">
              <span>若上述規則仍無法解答你的特殊情境：</span>
              <button type="button" id="cgu-ask-escalate-btn" class="cgu-pill-action is-solid">仍要詢問承辦</button>
            </div>
          </div>`;
      } else if (res.inquiry) {
        resultHtml = `
          <div id="cgu-ask-result-box" class="cgu-ask-result is-escalated" role="status">
            <div class="cgu-sim-badges-row">
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <span class="cgu-rule-mode-badge">${esc(res.mode_label || '規則式比對，非 AI')}</span>
            </div>
            <h3>${res.inquiry.escalated_from_faq ? '已轉送模擬承辦收件匣' : '未命中現有規則與 FAQ，已建立詢問單送交模擬收件匣'}</h3>
            <p>模擬收件編號：<strong>${esc(res.inquiry.receipt_id)}</strong> · 狀態：<b>${esc(res.inquiry.status_label)}</b></p>
            <p class="cgu-ask-tip">可切換底部「切換為國際處視角」體驗承辦回覆或將回覆加入 FAQ。</p>
          </div>`;
      }
    }

    const inquiriesHtml = inquiries.length
      ? inquiries.map(inq => `
        <article class="cgu-inquiry-card" data-receipt-id="${esc(inq.receipt_id)}">
          <header class="cgu-submitted-head">
            <div>
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <strong class="cgu-receipt-code">${esc(inq.receipt_id)}</strong>
            </div>
            <span class="cgu-status-chip status-${esc(inq.status)}">${esc(inq.status_label)}</span>
          </header>
          <p class="cgu-inq-q"><b>提問內容：</b>${esc(inq.question)}</p>
          <small class="cgu-inq-time">建立時間：${esc(formatTime(inq.created_at))}${inq.added_to_faq ? ' · 已收錄至工作區 FAQ' : ''}</small>
          ${inq.reply ? `<div class="cgu-inq-reply"><strong>國際處承辦回覆（模擬・${esc(formatTime(inq.replied_at))}）：</strong><p>${esc(inq.reply)}</p></div>` : '<p class="cgu-inq-waiting">等待承辦於模擬收件匣回覆…</p>'}
        </article>`).join('')
      : '<p class="cgu-empty-hint">目前尚無詢問單紀錄。</p>';

    host.innerHTML = `
      <div class="cgu-sim-card">
        <header class="cgu-sim-head">
          <div>
            <div class="cgu-sim-badges-row">
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <span class="cgu-rule-mode-badge">規則式比對，非 AI</span>
            </div>
            <h1 id="cgu-ask-oia-title">問國際處（規則庫關鍵字比對與模擬詢問單）</h1>
            <p class="cgu-sim-lead">輸入問題後，系統先以關鍵字比對 <code>demo_data</code> 已收錄之官方規則與 FAQ（不呼叫任何 AI 模型）；未命中或點選「仍要詢問承辦」時，將建立 <code>SIM-</code> 詢問單送入模擬收件匣。</p>
          </div>
          <div class="cgu-sim-head-actions">
            <a class="cgu-pill-action" href="#my-application">返回我的申請</a>
          </div>
        </header>

        <div class="cgu-quick-q-row" aria-label="常見測試問題範例">
          <span>快速測試：</span>
          <button type="button" class="cgu-chip-btn" data-cgu-sample-q="116-1 校內申請什麼時候截止？紙本也要交嗎？">截止日與紙本（命中）</button>
          <button type="button" class="cgu-chip-btn" data-cgu-sample-q="領航者補助金額多少？班排前 30% 有加碼嗎？">領航者補助（命中）</button>
          <button type="button" class="cgu-chip-btn" data-cgu-sample-q="請問基督城機場接機預約跟特殊飲食宿舍怎麼登記？">特殊住宿接機（未命中轉承辦）</button>
        </div>

        <form id="cgu-ask-form" class="cgu-ask-form">
          <label for="cgu-ask-input" class="cgu-field-label">輸入你想詢問國際事務處的問題（請勿填寫真實學號或個資）</label>
          <textarea id="cgu-ask-input" rows="3" maxlength="1000" required placeholder="例如：校內申請需要哪五份文件？成績單一定要有班級排名嗎？">${esc(simState.lastAskQuestion)}</textarea>
          <p id="cgu-ask-error" class="cgu-sim-error" role="alert" hidden></p>
          <div class="cgu-ask-actions">
            <button type="submit" id="cgu-ask-submit-btn" class="cgu-pill-action is-solid">送出問題（先比對 FAQ）</button>
          </div>
        </form>

        ${resultHtml}

        <section class="cgu-submitted-section" aria-labelledby="cgu-inq-list-title">
          <div class="cgu-submitted-section-head">
            <h2 id="cgu-inq-list-title">我的模擬詢問紀錄與承辦回覆</h2>
            <button type="button" class="cgu-text-btn" data-cgu-refresh-ask="1">重新整理回覆</button>
          </div>
          <div id="cgu-ask-inquiries-list">${inquiriesHtml}</div>
        </section>
      </div>`;
  }

  // ──────────────────────────────────────────────────────────────
  // Feature 5: 學生端「返國心得」(#cgu-return-report-page) + 學校頁公開區塊
  // ──────────────────────────────────────────────────────────────
  function syncReportSectionCounters() {
    let allValid = true;
    REPORT_SECTIONS.forEach(sec => {
      const ta = document.querySelector(`[data-cgu-report-sec="${sec.key}"]`);
      const counter = document.querySelector(`[data-cgu-report-count="${sec.key}"]`);
      if (!ta || !counter) return;
      simState.reportDraft.sections[sec.key] = ta.value;
      const cnt = countChars(ta.value);
      const ok = cnt >= 300;
      if (!ok) allValid = false;
      counter.textContent = `目前 ${cnt} 字 ／ 至少 300 字${ok ? '（已達標）' : `（尚差 ${300 - cnt} 字）`}`;
      counter.classList.toggle('is-ok', ok);
      counter.classList.toggle('is-lack', !ok);
    });
    return allValid;
  }

  async function renderReturnReportPage(forceReload = false) {
    const host = $('#cgu-return-report-page');
    if (!host) return;
    if (!simState.status || forceReload) {
      try {
        await loadConnectorStatus();
      } catch (_) { /* ignore */ }
    }
    const reports = simState.status?.return_reports || [];
    const draft = simState.reportDraft;

    const sectionFieldsHtml = REPORT_SECTIONS.map((sec, idx) => {
      const val = draft.sections[sec.key] || '';
      const cnt = countChars(val);
      const ok = cnt >= 300;
      return `
        <div class="cgu-report-field">
          <div class="cgu-report-field-head">
            <label for="cgu-report-sec-${esc(sec.key)}"><strong>${idx + 1}. ${esc(sec.title)}</strong>（必填，至少 300 字）</label>
            <span class="cgu-char-counter ${ok ? 'is-ok' : 'is-lack'}" data-cgu-report-count="${esc(sec.key)}">目前 ${cnt} 字 ／ 至少 300 字${ok ? '（已達標）' : `（尚差 ${300 - cnt} 字）`}</span>
          </div>
          <textarea id="cgu-report-sec-${esc(sec.key)}" data-cgu-report-sec="${esc(sec.key)}" rows="5" required placeholder="請填寫${esc(sec.title)}（至少 300 字，請使用虛構示範內容，勿填真實個資）…">${esc(val)}</textarea>
        </div>`;
    }).join('');

    const reportsListHtml = reports.length
      ? reports.map(r => `
        <article class="cgu-submitted-card" data-receipt-id="${esc(r.receipt_id)}">
          <header class="cgu-submitted-head">
            <div>
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <strong class="cgu-receipt-code">${esc(r.receipt_id)}</strong>
            </div>
            <span class="cgu-status-chip status-${esc(r.status)}">${esc(r.status_label)}</span>
          </header>
          <p class="cgu-submitted-meta">
            <span>合作校：<b>${esc(r.partner_school)}</b></span>
            <span>學期：<b>${esc(r.term)}</b></span>
            <span>公開授權：<b>${r.public_consent ? '同意公開給學弟妹' : '不同意公開'}</b></span>
          </p>
          <div class="cgu-report-card-actions">
            <a class="cgu-pill-action is-solid" href="${esc(r.print_url || `/demo/connector/return-reports/${r.receipt_id}/print`)}" target="_blank" rel="noopener noreferrer">匯出列印版 ↗</a>
            ${r.published ? `<a class="cgu-pill-action" href="#school=${encodeURIComponent(r.partner_school)}">前往合作校頁查看公開心得 →</a>` : ''}
          </div>
        </article>`).join('')
      : '<p class="cgu-empty-hint">目前尚無已送出的返國心得。送出後可匯出列印版並進入國際處模擬收件匣審核。</p>';

    host.innerHTML = `
      <div class="cgu-sim-card">
        <header class="cgu-sim-head">
          <div>
            <div class="cgu-sim-badges-row">
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
            </div>
            <h1 id="cgu-return-report-title">返國心得（國際處學期報告表四段式模擬送審）</h1>
            <p class="cgu-sim-lead">依長庚國際事務處學期報告表分為四段（出國前準備、上課情形、日常生活、課外活動及其他），每段至少 300 字；送出後可匯出列印版。經承辦核可且勾選「同意公開給學弟妹」者，將顯示於該合作校詳細頁「學長姐心得（示範資料）」區塊。</p>
          </div>
          <div class="cgu-sim-head-actions">
            <button type="button" id="cgu-report-fill-sample" class="cgu-pill-action">帶入虛構 300 字示範草稿</button>
            <a class="cgu-pill-action" href="#my-application">返回我的申請</a>
          </div>
        </header>

        <form id="cgu-return-report-form" class="cgu-report-form" novalidate>
          <div class="cgu-pref-grid">
            <label>
              <span>研修合作校</span>
              <select id="cgu-report-school">${renderPartnerOptions(draft.partner_school, false)}</select>
            </label>
            <label>
              <span>研修學期</span>
              <input type="text" id="cgu-report-term" maxlength="40" value="${esc(draft.term)}" required />
            </label>
            <label>
              <span>顯示身分標示（勿填真實姓名學號）</span>
              <input type="text" id="cgu-report-author" maxlength="80" value="${esc(draft.author_title)}" required />
            </label>
            <label>
              <span>分享影片網址（選填，展示版不上傳影片檔案）</span>
              <input type="url" id="cgu-report-video" maxlength="500" value="${esc(draft.video_url)}" placeholder="https://..." />
            </label>
          </div>

          ${sectionFieldsHtml}

          <label class="cgu-consent-check">
            <input type="checkbox" id="cgu-report-consent" ${draft.public_consent ? 'checked' : ''} />
            <span><strong>同意公開給學弟妹</strong>（經國際處模擬收件匣核可後，顯示於該合作校詳細頁「學長姐心得（示範資料）」區塊）</span>
          </label>

          <p id="cgu-report-feedback" class="cgu-sim-feedback" role="alert"></p>

          <div class="cgu-sim-submit-bar">
            <button type="submit" id="cgu-report-submit-btn" class="cgu-pill-action is-solid">送出返國心得（模擬）</button>
          </div>
        </form>

        <section class="cgu-submitted-section" aria-labelledby="cgu-report-list-title">
          <div class="cgu-submitted-section-head">
            <h2 id="cgu-report-list-title">我的返國心得紀錄與列印匯出</h2>
          </div>
          <div id="cgu-report-records">${reportsListHtml}</div>
        </section>
      </div>`;
  }

  // Inject approved & consented return reports into Partner School Detail Page
  let publicReportSeq = 0;
  let renderedPublicReportSchool = '';

  async function syncSchoolDetailPublicReports(schoolItemOrName) {
    const schoolName = typeof schoolItemOrName === 'string'
      ? schoolItemOrName
      : (schoolItemOrName?.school_name || (typeof state === 'object' && state.activeSchool) || '');
    if (!schoolName) return;
    const detailContent = $('#school-detail-content');
    if (!detailContent) return;
    if (renderedPublicReportSchool && renderedPublicReportSchool !== schoolName) {
      document.querySelectorAll('.cgu-public-reports-block').forEach(el => el.remove());
    }
    const seq = ++publicReportSeq;
    try {
      const data = await apiJson('/demo/connector/public-reports?school=' + encodeURIComponent(schoolName));
      if (seq !== publicReportSeq) return;
      if (typeof state === 'object' && state.activeSchool && state.activeSchool !== schoolName) return;
      document.querySelectorAll('.cgu-public-reports-block').forEach(el => el.remove());
      renderedPublicReportSchool = schoolName;
      const items = data.items || [];
      if (!items.length) return;

      const buildBlock = idAttr => {
        const wrapper = document.createElement('section');
        if (idAttr) wrapper.id = idAttr;
        wrapper.className = 'cgu-public-reports-block';
        wrapper.setAttribute('aria-label', '學長姐心得（示範資料）');
        wrapper.innerHTML = `
          <header class="cgu-public-reports-head">
            <div>
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <h3>學長姐心得（示範資料）</h3>
            </div>
            <small>僅顯示學生勾選「同意公開給學弟妹」並經模擬國際處核可之報告</small>
          </header>
          <div class="cgu-public-reports-list">
            ${items.map(r => `
              <article class="cgu-public-report-item" data-public-report="${esc(r.receipt_id)}">
                <div class="cgu-public-report-meta">
                  <strong>${esc(r.author_title || r.student_name)}</strong>
                  <span>學期：${esc(r.term)} · 編號：<code>${esc(r.receipt_id)}</code></span>
                </div>
                <div class="cgu-public-report-grid">
                  ${REPORT_SECTIONS.map(sec => `
                    <div class="cgu-public-sec">
                      <h4>${esc(sec.title)}</h4>
                      <p>${esc(r.sections?.[sec.key] || '')}</p>
                    </div>`).join('')}
                </div>
                ${r.video_url ? `<p class="cgu-public-video"><a href="${esc(r.video_url)}" target="_blank" rel="noopener noreferrer">觀看經驗分享影片連結 ↗</a></p>` : ''}
              </article>`).join('')}
          </div>`;
        return wrapper;
      };

      const overviewPanel = detailContent.querySelector('#detail-overview');
      if (overviewPanel) {
        overviewPanel.prepend(buildBlock('cgu-approved-return-reports'));
      } else {
        detailContent.prepend(buildBlock('cgu-approved-return-reports'));
      }
      const expPanel = detailContent.querySelector('#detail-experiences');
      if (expPanel) {
        expPanel.prepend(buildBlock('cgu-approved-return-reports-experiences'));
      }
    } catch (_) { /* ignore transient error */ }
  }

  if (window.UniWayDetail && typeof window.UniWayDetail.render === 'function') {
    const origDetailRender = window.UniWayDetail.render.bind(window.UniWayDetail);
    window.UniWayDetail.render = function (item) {
      const result = origDetailRender(item);
      if (item) syncSchoolDetailPublicReports(item);
      return result;
    };
  }

  // ──────────────────────────────────────────────────────────────
  // Feature 6: 國際處視角（模擬）(#cgu-oia-console-page)
  // ──────────────────────────────────────────────────────────────
  async function renderOiaConsolePage(forceReload = true) {
    const host = $('#cgu-oia-console-page');
    if (!host) return;
    if (!simState.oia || forceReload) {
      try {
        simState.oia = await apiJson('/demo/connector/oia/dashboard');
      } catch (err) {
        host.innerHTML = `<div class="cgu-sim-card"><span class="cgu-sim-badge">${esc(SIM_BADGE)}</span><h1 id="cgu-oia-console-title">國際處視角（模擬）</h1><p class="cgu-sim-error">${esc(err.message)}</p></div>`;
        return;
      }
    }
    const dash = simState.oia;
    const stats = dash.stats || {};
    const apps = dash.inboxes?.applications || [];
    const inqs = dash.inboxes?.inquiries || [];
    const rpts = dash.inboxes?.return_reports || [];
    const filter = simState.oiaFilter || 'all';

    const prefSummary = (stats.school_preferences || []).length
      ? stats.school_preferences.map(row => `<li><span>${esc(shortSchool(row.school))}</span><b>${row.count} 志願</b></li>`).join('')
      : '<li>暫無資料</li>';
    const topQSummary = (stats.top_questions || []).length
      ? stats.top_questions.map(row => `<li><span>${esc(row.topic)}</span><b>${row.count} 次</b></li>`).join('')
      : '<li>暫無資料</li>';

    const appsHtml = apps.map(app => `
      <article class="cgu-oia-item" data-oia-card="${esc(app.receipt_id)}">
        <header class="cgu-submitted-head">
          <div class="cgu-sim-badges-row">
            <strong class="cgu-receipt-code">${esc(app.receipt_id)}</strong>
            <span class="cgu-fictional-tag">${esc(app.fictional_label || '虛構示範資料')}</span>
            <span>${esc(app.student_name)} · ${esc(app.department)}</span>
          </div>
          <span class="cgu-status-chip status-${esc(app.status)}">${esc(app.status_label)}</span>
        </header>
        <p class="cgu-submitted-meta">
          <span>第一志願：<b>${esc(app.preference_1)}</b></span>
          ${app.preference_2 ? `<span>第二志願：<b>${esc(app.preference_2)}</b></span>` : ''}
          <span>送出時間：${esc(formatTime(app.submitted_at))}</span>
        </p>
        <div class="cgu-oia-doc-chips">
          ${(app.documents || []).map(d => `<span class="cgu-mini-pill is-general" title="SHA-256: ${esc(d.sha256)}">${esc(d.doc_title)}（${esc(d.filename)} · ${esc(d.sha256.slice(0, 8))}…）</span>`).join('')}
        </div>
        ${app.supplement_reason ? `<p class="cgu-oia-reason-note">目前補件原因：${esc(app.supplement_reason)}</p>` : ''}
        <div class="cgu-oia-action-row">
          <button type="button" class="cgu-pill-action" data-oia-act="confirm_receipt" data-receipt="${esc(app.receipt_id)}">確認收件</button>
          <div class="cgu-oia-inline-input">
            <input type="text" data-oia-reason-for="${esc(app.receipt_id)}" maxlength="300" placeholder="填寫補件原因，例：成績單未含班級排名百分比" value="${esc(app.supplement_reason || '')}" aria-label="補件原因（${esc(app.receipt_id)}）" />
            <button type="button" class="cgu-pill-action is-warn" data-oia-act="request_supplement" data-receipt="${esc(app.receipt_id)}">要求補件</button>
          </div>
          <button type="button" class="cgu-pill-action is-approve" data-oia-act="approve_initial" data-receipt="${esc(app.receipt_id)}">初審通過</button>
        </div>
      </article>`).join('');

    const customFaqMap = new Map((dash.custom_faqs || []).map(f => [f.id, f]));
    const inqsHtml = inqs.map(inq => {
      const existingFaq = customFaqMap.get(`faq-custom-${String(inq.receipt_id || '').toLowerCase()}`);
      const kwValue = existingFaq ? (existingFaq.keywords || []).slice(0, 6).join('、') : '';
      return `
      <article class="cgu-oia-item" data-oia-card="${esc(inq.receipt_id)}">
        <header class="cgu-submitted-head">
          <div class="cgu-sim-badges-row">
            <strong class="cgu-receipt-code">${esc(inq.receipt_id)}</strong>
            <span class="cgu-fictional-tag">${esc(inq.fictional_label || '虛構示範資料')}</span>
            <span>${esc(inq.student_name)} · ${esc(inq.department)}</span>
          </div>
          <span class="cgu-status-chip status-${esc(inq.status)}">${esc(inq.status_label)}${inq.added_to_faq ? '・已入 FAQ' : ''}</span>
        </header>
        <p class="cgu-inq-q"><b>學生詢問：</b>${esc(inq.question)}</p>
        <div class="cgu-oia-reply-box">
          <textarea data-oia-reply-for="${esc(inq.receipt_id)}" rows="2" maxlength="1200" placeholder="輸入承辦回覆內容（送出後即時同步至學生端狀態與通知鈴鐺）…" aria-label="回覆詢問（${esc(inq.receipt_id)}）">${esc(inq.reply || '')}</textarea>
          <div class="cgu-oia-action-row">
            <button type="button" class="cgu-pill-action is-solid" data-oia-act="reply_inquiry" data-receipt="${esc(inq.receipt_id)}">回覆詢問</button>
            <div class="cgu-oia-inline-input">
              <input type="text" data-oia-keywords-for="${esc(inq.receipt_id)}" maxlength="200" placeholder="選填 FAQ 關鍵字（留空將自動擷取問題詞彙）" value="${esc(kwValue)}" aria-label="FAQ 關鍵字（${esc(inq.receipt_id)}）" />
              <button type="button" class="cgu-pill-action" data-oia-act="add_to_faq" data-receipt="${esc(inq.receipt_id)}">將回覆加入 FAQ</button>
            </div>
          </div>
        </div>
      </article>`;
    }).join('');

    const rptsHtml = rpts.map(rpt => `
      <article class="cgu-oia-item" data-oia-card="${esc(rpt.receipt_id)}">
        <header class="cgu-submitted-head">
          <div class="cgu-sim-badges-row">
            <strong class="cgu-receipt-code">${esc(rpt.receipt_id)}</strong>
            <span class="cgu-fictional-tag">${esc(rpt.fictional_label || '虛構示範資料')}</span>
            <span>${esc(rpt.student_name)} · ${esc(rpt.partner_school)}</span>
          </div>
          <span class="cgu-status-chip status-${esc(rpt.status)}">${esc(rpt.status_label)}</span>
        </header>
        <p class="cgu-submitted-meta">
          <span>學期：${esc(rpt.term)}</span>
          <span>同意公開給學弟妹：<b>${rpt.public_consent ? '是' : '否'}</b></span>
          ${rpt.video_url ? `<a href="${esc(rpt.video_url)}" target="_blank" rel="noopener noreferrer">分享影片連結 ↗</a>` : ''}
        </p>
        <details class="cgu-oia-report-preview">
          <summary>展開檢視四段報告內容（均滿 300 字）</summary>
          <div class="cgu-public-report-grid">
            ${REPORT_SECTIONS.map(sec => `<div><h4>${esc(sec.title)}（${countChars(rpt.sections?.[sec.key] || '')} 字）</h4><p>${esc(rpt.sections?.[sec.key] || '')}</p></div>`).join('')}
          </div>
        </details>
        <div class="cgu-oia-action-row">
          <button type="button" class="cgu-pill-action is-solid" data-oia-act="approve_report" data-receipt="${esc(rpt.receipt_id)}">核可心得公開</button>
          <a class="cgu-pill-action" href="/demo/connector/return-reports/${esc(rpt.receipt_id)}/print" target="_blank" rel="noopener noreferrer">檢視列印版 ↗</a>
        </div>
      </article>`).join('');

    host.innerHTML = `
      <div class="cgu-sim-card cgu-oia-shell">
        <header class="cgu-sim-head">
          <div>
            <div class="cgu-sim-badges-row">
              <span class="cgu-sim-badge">${esc(SIM_BADGE)}</span>
              <span class="cgu-fictional-tag">預載 ${esc(dash.seed_count || 5)} 筆明確標示之虛構示範資料</span>
            </div>
            <h1 id="cgu-oia-console-title">國際處視角（模擬）— 承辦收件匣與統計工作台</h1>
            <p class="cgu-sim-lead">承辦於此處執行的每項動作（確認收件、要求補件、回覆詢問、將回覆加入 FAQ、核可心得公開）皆即時同步至本瀏覽器學生端狀態與右上角／側欄通知鈴鐺。</p>
          </div>
          <div class="cgu-sim-head-actions">
            <button type="button" class="cgu-pill-action is-solid" data-cgu-back-student="1">切回學生端查看通知與狀態 →</button>
          </div>
        </header>

        <p id="cgu-oia-feedback" class="cgu-sim-feedback" role="status" aria-live="polite"></p>

        <section id="cgu-oia-stats-row" class="cgu-oia-stats-grid" aria-label="模擬承辦統計">
          <article class="cgu-oia-stat-card">
            <span class="cgu-stat-label">各校志願數</span>
            <ul class="cgu-stat-list">${prefSummary}</ul>
          </article>
          <article class="cgu-oia-stat-card is-alert">
            <span class="cgu-stat-label">缺件／要求補件數</span>
            <strong id="cgu-oia-missing-count" class="cgu-stat-big">${esc(stats.missing_count ?? 0)} <small>件</small></strong>
            <p>目前處於「要求補件」狀態之申請案件數</p>
          </article>
          <article class="cgu-oia-stat-card">
            <span class="cgu-stat-label">最常被問的問題</span>
            <ul class="cgu-stat-list">${topQSummary}</ul>
          </article>
        </section>

        <div class="cgu-oia-tabs" role="tablist" aria-label="收件匣篩選">
          <button type="button" class="cgu-program-tab ${filter === 'all' ? 'on' : ''}" data-oia-filter="all">全部收件匣</button>
          <button type="button" class="cgu-program-tab ${filter === 'applications' ? 'on' : ''}" data-oia-filter="applications">申請收件匣 <span>${apps.length}</span></button>
          <button type="button" class="cgu-program-tab ${filter === 'inquiries' ? 'on' : ''}" data-oia-filter="inquiries">詢問收件匣 <span>${inqs.length}</span></button>
          <button type="button" class="cgu-program-tab ${filter === 'reports' ? 'on' : ''}" data-oia-filter="reports">返國心得收件匣 <span>${rpts.length}</span></button>
        </div>

        <section id="cgu-oia-inbox-apps" class="cgu-oia-inbox-sec" ${filter !== 'all' && filter !== 'applications' ? 'hidden' : ''} aria-labelledby="cgu-oia-apps-title">
          <h2 id="cgu-oia-apps-title">一、申請收件匣（${apps.length} 筆）</h2>
          <div class="cgu-oia-list">${appsHtml}</div>
        </section>

        <section id="cgu-oia-inbox-inquiries" class="cgu-oia-inbox-sec" ${filter !== 'all' && filter !== 'inquiries' ? 'hidden' : ''} aria-labelledby="cgu-oia-inqs-title">
          <h2 id="cgu-oia-inqs-title">二、詢問收件匣（${inqs.length} 筆）</h2>
          <div class="cgu-oia-list">${inqsHtml}</div>
        </section>

        <section id="cgu-oia-inbox-reports" class="cgu-oia-inbox-sec" ${filter !== 'all' && filter !== 'reports' ? 'hidden' : ''} aria-labelledby="cgu-oia-rpts-title">
          <h2 id="cgu-oia-rpts-title">三、返國心得收件匣（${rpts.length} 筆）</h2>
          <div class="cgu-oia-list">${rptsHtml}</div>
        </section>
      </div>`;
  }

  // ──────────────────────────────────────────────────────────────
  // Item 7: Verified《長庚大學領航者補助作業要點》（規章 2B00004）說明卡
  // ──────────────────────────────────────────────────────────────
  function navigatorCardMarkup(compact = false) {
    return `
      <article class="cgu-navigator-box${compact ? ' is-compact' : ''}">
        <header class="cgu-navigator-head">
          <div>
            <span class="cgu-section-kicker">69 所合作校資格欄引用 · 規章編號 2B00004（114/10/28 修正）</span>
            <h2 ${compact ? '' : 'id="cgu-navigator-title" '}class="cgu-navigator-heading">「領航者補助作業要點」是什麼？金額與資格一次核對</h2>
            <p class="cgu-navigator-lead">長庚 78 所合作校中有 <strong>69 所</strong>在申請資格寫明「符合領航者補助作業要點」。這份要點結合教育部學海飛颺經費與長庚校內預算，支持在學學生出國修讀學分（交換或雙聯）；<strong>完成校內甄選並獲外校錄取且符合資格者，由國際事務處直接送補助金審查，不需另外單獨填表申請</strong>。</p>
          </div>
          ${compact ? '' : '<a class="cgu-pill-action" href="#scholarships">前往補助資訊頁 →</a>'}
        </header>
        <div class="cgu-navigator-grid">
          <div class="cgu-nav-tier is-tier1">
            <span class="cgu-nav-tier-tag">第一類地區補助上限</span>
            <strong>NT$75,000 <small>／1 學期</small></strong>
            <span class="cgu-nav-year">一學年上限 <b>NT$150,000</b></span>
            <p>適用美、加、智利、墨西哥、英、法、德、荷、比、盧、瑞、奧、義、西、葡、北歐五國、匈牙利、斯洛維尼亞、以色列、新加坡、澳洲、紐西蘭。</p>
          </div>
          <div class="cgu-nav-tier is-tier2">
            <span class="cgu-nav-tier-tag">第二類地區補助上限</span>
            <strong>NT$60,000 <small>／1 學期</small></strong>
            <span class="cgu-nav-year">一學年上限 <b>NT$120,000</b></span>
            <p>適用日、韓、捷克、波蘭、立陶宛、拉脫維亞、泰、馬、印、巴西、哥倫比亞、俄、土、蒙、南非及大陸港澳地區（教育部學海飛颺經費不含大陸及港澳，實際適用經費依國際處審查核定）。</p>
          </div>
          <div class="cgu-nav-tier is-bonus">
            <span class="cgu-nav-tier-tag">優秀加碼與審核重點</span>
            <strong>+NT$10,000 <small>／每學期</small></strong>
            <span class="cgu-nav-year">歷年成績<b>班排名前 30%</b> 得加碼</span>
            <p>複審配分：在校成績 30%、外語能力 30%、讀書計畫與就讀學校國際聲望 30%、特殊表現 10%。實際名額與核定金額依當年度教育部與本校預算核定。</p>
          </div>
        </div>
        <div class="cgu-navigator-rules">
          <div>
            <strong>申請資格（第 3 點）</strong>
            <ul>
              <li>具中華民國國籍且在臺設戶籍、於長庚就讀滿 <b>1 學期以上</b>在學生（不含在職專班）。</li>
              <li>歷年學業平均達 <b>70 分以上</b>為原則；英文等同<b>多益 700 分</b>、IELTS 5.5、TOEFL iBT 72 或 Duolingo 105 以上（日、法、德、西語依附件一標準；合作校更高者從其規定）。</li>
              <li>不得同時領取我國政府其他出國研修補助；同一學制曾領本校短期學分或其他出國研修／實習補助者，已領金額自額度扣除。</li>
            </ul>
          </div>
          <div>
            <strong>修課與返國義務（第 9–11 點）</strong>
            <ul>
              <li>出國前簽訂《行政契約書》；每學期至少修讀 1 門專業科目，返校每學期至少採認 <b>3 學分</b>（未滿一學期不得領取；以中文修課組別不予補助）。</li>
              <li>返國後 <b>2 週內</b>繳交返校手續單至系所，並上傳問卷、心得報告及經驗分享短片至教育部網站與國際處。</li>
            </ul>
          </div>
        </div>
        <footer class="cgu-navigator-foot">
          <span>官方原文與查核（2026-11-12）：</span>
          <a href="https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/b85add3b-7d9e-43ff-b22f-f0657e11765c" target="_blank" rel="noopener noreferrer">長庚法規彙編 2B00004 ↗</a>
          <a href="https://www.cgu.edu.tw/regulation/ServerFile/Get/e3b68a9a-e820-4614-a799-e88023a40161" target="_blank" rel="noopener noreferrer">下載官方要點 PDF（含附件一、二）↗</a>
          <a href="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15724" target="_blank" rel="noopener noreferrer">國際事務處補助說明頁 ↗</a>
        </footer>
      </article>`;
  }

  function renderNavigatorCards() {
    const homeHost = $('#cgu-navigator-card');
    if (homeHost && !homeHost.dataset.rendered) {
      homeHost.innerHTML = navigatorCardMarkup(false);
      homeHost.dataset.rendered = '1';
    }
    const pageHost = $('#cgu-scholarships-navigator-card');
    if (pageHost && !pageHost.dataset.rendered) {
      pageHost.innerHTML = navigatorCardMarkup(true);
      pageHost.dataset.rendered = '1';
    }
  }

  // ──────────────────────────────────────────────────────────────
  // Search Page (#partners): Prominent「我的條件」& Single-Row Clean Filter Strip
  // ──────────────────────────────────────────────────────────────
  const COLLEGE_FULL_LABELS = {
    '': '全部學院',
    '醫學院': '醫學院',
    '工學院': '工學院',
    '管理學院': '管理學院',
    '智慧運算學院': '智慧運算學院',
  };

  const CRITERIA_TEST_LABELS = {
    ielts: 'IELTS',
    toefl: 'TOEFL iBT',
    toeic: 'TOEIC',
    jlpt: '日檢 N',
    topik: 'TOPIK ',
    duolingo: 'Duolingo',
  };

  const GRADE_SCALE_META = {
    '100': { max: '100', step: '0.01', placeholder: '例如 78' },
    '4': { max: '4', step: '0.01', placeholder: '例如 3.4' },
    '4.3': { max: '4.3', step: '0.01', placeholder: '例如 3.6' },
    '5': { max: '5', step: '0.01', placeholder: '例如 4.2' },
  };

  function syncCriteriaGradeScale(clearOutOfRange = false) {
    const form = $('#discovery-criteria-form');
    if (!form) return;
    const scaleSel = form.querySelector('select[name="scale"]');
    const gradeInp = form.querySelector('input[name="grade"]');
    if (!scaleSel || !gradeInp) return;
    const meta = GRADE_SCALE_META[scaleSel.value] || GRADE_SCALE_META['100'];
    if (gradeInp.max !== meta.max) gradeInp.max = meta.max;
    if (gradeInp.step !== meta.step) gradeInp.step = meta.step;
    if (gradeInp.placeholder !== meta.placeholder) gradeInp.placeholder = meta.placeholder;
    if (clearOutOfRange && gradeInp.value !== '' && Number(gradeInp.value) > Number(meta.max)) {
      gradeInp.value = '';
    }
  }

  function syncPartnersRecentsPopover() {
    const details = $('#partners .cgu-explore-head-actions [data-discovery-recents]');
    if (!details || !details.open || details.hidden) return;
    const vw = document.documentElement.clientWidth || window.innerWidth || 1024;
    const menuW = Math.min(320, Math.max(200, vw - 32));
    const rect = details.getBoundingClientRect();
    const idealLeft = rect.right - menuW;
    const clampedLeft = Math.min(Math.max(16, idealLeft), Math.max(16, vw - menuW - 16));
    details.style.setProperty('--cgu-recents-left', `${Math.round(clampedLeft - rect.left)}px`);
    details.style.setProperty('--cgu-recents-right', 'auto');
  }

  function syncPartnersCleanRow() {
    const collegeBar = $('#cgu-college-quick-bar');
    if (!collegeBar) return;
    const buttonsWrap = collegeBar.querySelector('.cgu-college-buttons');
    if (buttonsWrap) {
      const allBtn = buttonsWrap.querySelector('[data-cgu-college=""]');
      if (allBtn && buttonsWrap.firstElementChild !== allBtn) {
        buttonsWrap.prepend(allBtn);
      }
      buttonsWrap.querySelectorAll('[data-cgu-college]').forEach(btn => {
        const key = btn.dataset.cguCollege ?? '';
        const targetLabel = COLLEGE_FULL_LABELS[key];
        const strong = btn.querySelector('strong');
        if (targetLabel && strong && strong.textContent !== targetLabel) {
          strong.textContent = targetLabel;
        }
      });
    }
    const deptWrap = collegeBar.querySelector('.cgu-dept-inline-select');
    const deptSelect = collegeBar.querySelector('#cgu-partner-dept-select');
    if (deptWrap && deptSelect) {
      const hasDept = Boolean(deptSelect.value);
      if (deptWrap.classList.contains('has-dept') !== hasDept) {
        deptWrap.classList.toggle('has-dept', hasDept);
      }
    }
  }

  function syncCriteriaBanner() {
    const details = $('#discovery-criteria');
    if (!details) return;
    const summarySpan = $('#cgu-criteria-summary');
    const ctaLabel = $('#cgu-criteria-cta-label');
    const c = (typeof discoveryCriteria === 'object' && discoveryCriteria) ? discoveryCriteria : {};
    const active = Boolean(window.UniWayDiscovery?.hasCriteria?.(c))
      || Boolean(($('#discovery-criteria-count')?.textContent || '').trim());

    const parts = [];
    if (active) {
      if (c.test || c.score) {
        const tLabel = CRITERIA_TEST_LABELS[c.test] || (c.test ? String(c.test).toUpperCase() : '檢定');
        if (c.test === 'jlpt' && c.score) parts.push(`JLPT N${c.score}`);
        else if (c.test === 'topik' && c.score) parts.push(`TOPIK ${c.score} 級`);
        else parts.push([tLabel.trim(), c.score].filter(Boolean).join(' '));
      }
      if (c.grade) {
        const prefix = (!c.scale || c.scale === '100') ? '平均' : 'GPA';
        parts.push(`${prefix} ${c.grade}`);
      }
      if (c.degree === 'undergraduate') parts.push('大學部');
      else if (c.degree === 'graduate') parts.push('研究所');
      if (c.term === 'fall') parts.push('2027 秋季');
      else if (c.term === 'spring') parts.push('2027 春季');
    }

    const nextSummary = parts.length ? parts.join(' · ') : '檢定成績 · 學業成績 · 學制';
    const nextCta = details.open ? '收合條件' : active ? '修改條件' : '設定條件';

    if (details.classList.contains('has-active-criteria') !== active) {
      details.classList.toggle('has-active-criteria', active);
    }
    if (summarySpan && summarySpan.textContent !== nextSummary) {
      summarySpan.textContent = nextSummary;
    }
    if (ctaLabel && ctaLabel.textContent !== nextCta) {
      ctaLabel.textContent = nextCta;
    }
  }

  $('#discovery-criteria')?.addEventListener('toggle', () => {
    syncCriteriaBanner();
  });

  $('#partners .cgu-explore-head-actions [data-discovery-recents]')?.addEventListener('toggle', () => {
    syncPartnersRecentsPopover();
  });
  window.addEventListener('resize', syncPartnersRecentsPopover);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const recents = $('#partners .cgu-explore-head-actions [data-discovery-recents]');
      if (recents?.open) recents.open = false;
    }
  });

  function syncAdvisorMgmtNote() {
    const collegeSelect = $('#advisor-college');
    const noteAnchor = $('#advisor-department-note')?.parentElement;
    if (!collegeSelect || !noteAnchor) return;
    let tip = $('#cgu-advisor-mgmt-note');
    if (collegeSelect.value === '管理學院') {
      if (!tip) {
        tip = document.createElement('p');
        tip.id = 'cgu-advisor-mgmt-note';
        tip.className = 'cgu-advisor-mgmt-note';
        tip.textContent = '管理學院另有院級交換，請洽院國際辦公室（法國 IAE 艾克斯馬賽大學管理研究所、雷恩商學院屬院級管道，不在國際處中央名單上）。';
        noteAnchor.insertAdjacentElement('afterend', tip);
      }
      tip.hidden = false;
    } else if (tip) {
      tip.hidden = true;
    }
  }

  // ──────────────────────────────────────────────────────────────
  // Route Sync & Delegated Event Handlers
  // ──────────────────────────────────────────────────────────────
  async function syncActiveDemoRoute() {
    if (guardHiddenRoutes()) return;
    syncPerspectiveButton();
    renderNavigatorCards();
    syncPartnersCleanRow();
    syncCriteriaBanner();
    syncAdvisorMgmtNote();
    enhanceMyApplicationDeadline();

    const hash = window.location.hash || '#home';
    if (hash === '#school-connector') {
      await renderConnectorSpecPage();
    } else if (/^#my-application(?:\?|$)/.test(hash)) {
      await renderMyApplicationSim(true);
      await refreshNotificationsNow();
    } else if (hash === '#ask-oia') {
      await renderAskOiaPage(true);
      await refreshNotificationsNow();
    } else if (hash === '#return-report') {
      await renderReturnReportPage(true);
      await refreshNotificationsNow();
    } else if (hash === '#oia-view') {
      await renderOiaConsolePage(true);
    } else if (hash.startsWith('#school=')) {
      const schoolName = decodeURIComponent(hash.slice('#school='.length));
      await syncSchoolDetailPublicReports(schoolName);
    }
  }

  document.addEventListener('click', async event => {
    const recentsDetails = $('#partners .cgu-explore-head-actions [data-discovery-recents]');
    if (recentsDetails?.open) {
      if (!recentsDetails.contains(event.target)) {
        recentsDetails.open = false;
      } else if (event.target.closest('.discovery-recent-list button')) {
        window.requestAnimationFrame(() => {
          recentsDetails.open = false;
        });
      }
    }

    const scrollBtn = event.target.closest('[data-cgu-scroll]');
    if (scrollBtn) {
      const target = document.querySelector(scrollBtn.dataset.cguScroll);
      if (target) {
        event.preventDefault();
        target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      }
      return;
    }

    if (event.target.closest('[data-cgu-open-oia]')) {
      lastStudentHash = window.location.hash !== '#oia-view' ? (window.location.hash || '#my-application') : lastStudentHash;
      window.location.hash = '#oia-view';
      return;
    }

    if (event.target.closest('[data-cgu-back-student]')) {
      window.location.hash = lastStudentHash || '#my-application';
      return;
    }

    // Simulated file sample & remove actions
    const sampleDocBtn = event.target.closest('[data-cgu-sim-sample]');
    if (sampleDocBtn) {
      const docKey = sampleDocBtn.dataset.cguSimSample;
      sampleDocBtn.disabled = true;
      try {
        await uploadMetadataFile(docKey, buildSyntheticSampleFile(docKey));
        await renderMyApplicationSim(true);
      } catch (err) {
        const fb = $('#cgu-sim-submit-feedback');
        if (fb) fb.textContent = err.message;
      } finally {
        sampleDocBtn.disabled = false;
      }
      return;
    }

    if (event.target.closest('#cgu-sim-fill-all')) {
      const btn = $('#cgu-sim-fill-all');
      if (btn) btn.disabled = true;
      try {
        const draftFiles = simState.status?.draft_files || {};
        for (const doc of REQUIRED_DOCS) {
          if (!draftFiles[doc.key]) {
            await uploadMetadataFile(doc.key, buildSyntheticSampleFile(doc.key));
          }
        }
        await renderMyApplicationSim(true);
      } catch (err) {
        const fb = $('#cgu-sim-submit-feedback');
        if (fb) fb.textContent = err.message;
      } finally {
        if (btn) btn.disabled = false;
      }
      return;
    }

    const removeDocBtn = event.target.closest('[data-cgu-sim-remove]');
    if (removeDocBtn) {
      const docKey = removeDocBtn.dataset.cguSimRemove;
      removeDocBtn.disabled = true;
      try {
        await apiJson(`/demo/connector/files/${encodeURIComponent(docKey)}`, { method: 'DELETE' });
        await renderMyApplicationSim(true);
      } catch (err) {
        const fb = $('#cgu-sim-submit-feedback');
        if (fb) fb.textContent = err.message;
      } finally {
        removeDocBtn.disabled = false;
      }
      return;
    }

    if (event.target.closest('#cgu-sim-precheck-btn')) {
      await renderMyApplicationSim(true);
      const box = $('#cgu-sim-precheck-box');
      box?.scrollIntoView({ behavior: 'auto', block: 'nearest' });
      return;
    }

    if (event.target.closest('#cgu-sim-submit-btn')) {
      const btn = $('#cgu-sim-submit-btn');
      const fb = $('#cgu-sim-submit-feedback');
      if (!btn || btn.disabled) return;
      btn.disabled = true;
      if (fb) fb.textContent = '正在送出模擬申請…';
      try {
        const res = await apiJson('/demo/connector/applications', {
          method: 'POST',
          body: JSON.stringify({
            preference_1: simState.selectedPref1,
            preference_2: simState.selectedPref2,
            academic_year: '116',
            semester: '116-1（2027 秋季出國）',
          }),
        });
        await renderMyApplicationSim(true);
        const afterFb = $('#cgu-sim-submit-feedback');
        if (afterFb) {
          afterFb.textContent = `已建立模擬申請，收件編號：${res.application.receipt_id}（狀態：${res.application.status_label}）`;
        }
      } catch (err) {
        if (fb) fb.textContent = err.message;
        btn.disabled = false;
      }
      return;
    }

    if (event.target.closest('[data-cgu-refresh-status]')) {
      await renderMyApplicationSim(true);
      await refreshNotificationsNow();
      return;
    }

    // Ask OIA sample chips & escalate button
    const sampleQBtn = event.target.closest('[data-cgu-sample-q]');
    if (sampleQBtn) {
      const q = sampleQBtn.dataset.cguSampleQ || '';
      simState.lastAskQuestion = q;
      const input = $('#cgu-ask-input');
      if (input) {
        input.value = q;
        input.focus();
      }
      return;
    }

    if (event.target.closest('#cgu-ask-escalate-btn')) {
      const btn = $('#cgu-ask-escalate-btn');
      if (btn) btn.disabled = true;
      try {
        const matchedIds = (simState.lastAskResult?.matches || []).map(m => m.id);
        const res = await apiJson('/demo/connector/inquiries', {
          method: 'POST',
          body: JSON.stringify({
            question: simState.lastAskQuestion || $('#cgu-ask-input')?.value || '',
            escalated_from_faq: true,
            matched_faq_ids: matchedIds,
          }),
        });
        simState.lastAskResult = {
          mode_label: '規則式比對，非 AI',
          matched: false,
          matches: [],
          inquiry: res.inquiry,
        };
        await renderAskOiaPage(true);
      } catch (err) {
        const errEl = $('#cgu-ask-error');
        if (errEl) {
          errEl.hidden = false;
          errEl.textContent = err.message;
        }
      } finally {
        if (btn) btn.disabled = false;
      }
      return;
    }

    if (event.target.closest('[data-cgu-refresh-ask]')) {
      await renderAskOiaPage(true);
      await refreshNotificationsNow();
      return;
    }

    // Return report sample fill
    if (event.target.closest('#cgu-report-fill-sample')) {
      simState.reportDraft.sections = { ...SAMPLE_REPORT_PARAGRAPHS };
      await renderReturnReportPage(false);
      return;
    }

    // OIA filter tabs & actions
    const oiaFilterBtn = event.target.closest('[data-oia-filter]');
    if (oiaFilterBtn) {
      simState.oiaFilter = oiaFilterBtn.dataset.oiaFilter || 'all';
      await renderOiaConsolePage(false);
      return;
    }

    const oiaActBtn = event.target.closest('[data-oia-act]');
    if (oiaActBtn) {
      const action = oiaActBtn.dataset.oiaAct;
      const receipt = oiaActBtn.dataset.receipt;
      const reasonInput = document.querySelector(`[data-oia-reason-for="${CSS.escape(receipt)}"]`);
      const replyInput = document.querySelector(`[data-oia-reply-for="${CSS.escape(receipt)}"]`);
      const kwInput = document.querySelector(`[data-oia-keywords-for="${CSS.escape(receipt)}"]`);
      const payload = {
        action,
        receipt_id: receipt,
        reason: reasonInput ? reasonInput.value : '',
        reply: replyInput ? replyInput.value : '',
        ...(kwInput && kwInput.value.trim() ? { keywords: kwInput.value.trim() } : {}),
      };
      oiaActBtn.disabled = true;
      try {
        await apiJson('/demo/connector/oia/actions', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        await loadConnectorStatus();
        await renderOiaConsolePage(true);
        await refreshNotificationsNow();
        const fb = $('#cgu-oia-feedback');
        if (fb) fb.textContent = `已完成承辦動作（案件 ${receipt}），學生端狀態與通知鈴鐺已即時更新。`;
      } catch (err) {
        const fb = $('#cgu-oia-feedback');
        if (fb) fb.textContent = err.message;
      } finally {
        oiaActBtn.disabled = false;
      }
      return;
    }

    if (event.target.closest('#discovery-clear-criteria, #clear-partner-filters')) {
      window.requestAnimationFrame(() => {
        syncCriteriaGradeScale(false);
        syncCriteriaBanner();
      });
    }
  });

  document.addEventListener('reset', event => {
    if (event.target.id === 'discovery-criteria-form') {
      window.setTimeout(() => {
        syncCriteriaGradeScale(false);
        syncCriteriaBanner();
      }, 0);
    }
  });

  document.addEventListener('change', async event => {
    const fileInput = event.target.closest('[data-cgu-sim-upload]');
    if (fileInput && fileInput.files && fileInput.files[0]) {
      const docKey = fileInput.dataset.cguSimUpload;
      const selectedFile = fileInput.files[0];
      try {
        await uploadMetadataFile(docKey, selectedFile);
        fileInput.value = '';
        await renderMyApplicationSim(true);
      } catch (err) {
        fileInput.value = '';
        const fb = $('#cgu-sim-submit-feedback');
        if (fb) fb.textContent = err.message;
      }
      return;
    }
    if (event.target.id === 'cgu-sim-pref1') {
      simState.selectedPref1 = event.target.value;
      return;
    }
    if (event.target.id === 'cgu-sim-pref2') {
      simState.selectedPref2 = event.target.value;
      return;
    }
    if (event.target.id === 'cgu-report-school') {
      simState.reportDraft.partner_school = event.target.value;
      return;
    }
    if (event.target.id === 'cgu-report-consent') {
      simState.reportDraft.public_consent = event.target.checked;
      return;
    }
    if (event.target.matches('#discovery-criteria-form select[name="scale"]')) {
      syncCriteriaGradeScale(true);
      return;
    }
    if (event.target.id === 'advisor-college') {
      syncAdvisorMgmtNote();
    }
  });

  document.addEventListener('input', event => {
    if (event.target.matches('[data-cgu-report-sec]')) {
      syncReportSectionCounters();
      return;
    }
    if (event.target.id === 'cgu-report-term') {
      simState.reportDraft.term = event.target.value;
    } else if (event.target.id === 'cgu-report-author') {
      simState.reportDraft.author_title = event.target.value;
    } else if (event.target.id === 'cgu-report-video') {
      simState.reportDraft.video_url = event.target.value;
    } else if (event.target.id === 'cgu-ask-input') {
      simState.lastAskQuestion = event.target.value;
    }
  });

  document.addEventListener('submit', async event => {
    if (event.target.id === 'cgu-ask-form') {
      event.preventDefault();
      const input = $('#cgu-ask-input');
      const errEl = $('#cgu-ask-error');
      const btn = $('#cgu-ask-submit-btn');
      const question = (input?.value || '').trim();
      simState.lastAskQuestion = question;
      if (errEl) errEl.hidden = true;
      if (btn) btn.disabled = true;
      try {
        simState.lastAskResult = await apiJson('/demo/connector/ask', {
          method: 'POST',
          body: JSON.stringify({ question, force_inquiry: false }),
        });
        await renderAskOiaPage(true);
      } catch (err) {
        if (errEl) {
          errEl.hidden = false;
          errEl.textContent = err.message;
        }
      } finally {
        if (btn) btn.disabled = false;
      }
      return;
    }

    if (event.target.id === 'discovery-criteria-form') {
      window.requestAnimationFrame(syncCriteriaBanner);
      return;
    }

    if (event.target.id === 'cgu-return-report-form') {
      event.preventDefault();
      const fb = $('#cgu-report-feedback');
      const btn = $('#cgu-report-submit-btn');
      const valid = syncReportSectionCounters();
      if (!valid) {
        if (fb) fb.textContent = '請確認「出國前準備、上課情形、日常生活、課外活動及其他」四段均已滿 300 字後再送出。';
        return;
      }
      if (btn) btn.disabled = true;
      if (fb) fb.textContent = '正在送出返國心得…';
      try {
        const res = await apiJson('/demo/connector/return-reports', {
          method: 'POST',
          body: JSON.stringify({
            partner_school: $('#cgu-report-school')?.value || simState.reportDraft.partner_school,
            term: $('#cgu-report-term')?.value || simState.reportDraft.term,
            author_title: $('#cgu-report-author')?.value || simState.reportDraft.author_title,
            video_url: $('#cgu-report-video')?.value || '',
            public_consent: Boolean($('#cgu-report-consent')?.checked),
            sections: { ...simState.reportDraft.sections },
          }),
        });
        simState.reportDraft.sections = { preparation: '', academics: '', daily_life: '', extracurricular: '' };
        simState.reportDraft.video_url = '';
        await renderReturnReportPage(true);
        const afterFb = $('#cgu-report-feedback');
        if (afterFb) {
          afterFb.textContent = `已送出返國心得，收件編號：${res.report.receipt_id}（可於下方點選「匯出列印版」）。`;
        }
      } catch (err) {
        if (fb) fb.textContent = err.message;
      } finally {
        if (btn) btn.disabled = false;
      }
    }
  });

  function ensureTopbarTooltips() {
    $$('#glass-navigation .uniway-public-nav a[data-public-route]').forEach(link => {
      const label = (link.getAttribute('aria-label') || link.querySelector('span')?.textContent || '').trim();
      if (label && link.getAttribute('title') !== label) link.setAttribute('title', label);
    });
    const syncStatus = $('#account-workspace-sync-control .workspace-sync-status');
    const syncLabel = $('#account-workspace-sync-control .workspace-sync-status-label')?.textContent?.trim();
    if (syncStatus && syncLabel && syncStatus.getAttribute('title') !== syncLabel) {
      syncStatus.setAttribute('title', syncLabel);
    }
    const syncRetry = $('#account-workspace-sync-retry');
    if (syncRetry) {
      const retryLabel = (syncRetry.getAttribute('aria-label') || syncRetry.querySelector('span')?.textContent || '重試同步').trim();
      if (syncRetry.getAttribute('title') !== retryLabel) syncRetry.setAttribute('title', retryLabel);
      if (!syncRetry.getAttribute('aria-label')) syncRetry.setAttribute('aria-label', retryLabel);
    }
  }

  // Observe DOM mutations for dynamic shared renders (application-path deadline panel, notifications, file inputs, partner bars)
  new MutationObserver(() => {
    restrictControls();
    ensureTopbarTooltips();
    enhanceMyApplicationDeadline();
    enhanceNotificationItems();
    syncPartnersCleanRow();
    syncCriteriaBanner();
  }).observe(document.body, { childList: true, subtree: true });

  ensureTopbarTooltips();
  renderNavigatorCards();
  syncPartnersCleanRow();
  syncCriteriaGradeScale(false);
  syncCriteriaBanner();
  syncPerspectiveButton();

  // If loaded directly on one of our custom routes, re-apply route now that sets include them
  if (['#school-connector', '#ask-oia', '#return-report', '#oia-view'].includes(window.location.hash) && typeof applyAppRoute === 'function') {
    applyAppRoute({ loadFeed: false, resetScroll: false });
  }
  void syncActiveDemoRoute();

  if (typeof appReady !== 'undefined' && appReady?.then) {
    appReady.then(() => {
      lockSchoolSwitcher();
      syncStripClearance();
      renderNavigatorCards();
      syncPartnersCleanRow();
      syncCriteriaGradeScale(false);
      syncCriteriaBanner();
      syncAdvisorMgmtNote();
      if (['#school-connector', '#ask-oia', '#return-report', '#oia-view'].includes(window.location.hash) && typeof applyAppRoute === 'function') {
        applyAppRoute({ loadFeed: false, resetScroll: false });
      }
      void syncActiveDemoRoute();
      void refreshNotificationsNow();
    });
  }
  window.addEventListener('hashchange', () => {
    void syncActiveDemoRoute();
  });
})();

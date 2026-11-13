(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  if (!window.cguDemoStorageIsolated) {
    $('#cgu-demo-strip').textContent = '展示隔離載入失敗，請重新整理；展示重設已停用。';
    return;
  }
  if (window.cguDemoStorageLimited) $('#cgu-demo-strip span').textContent += '・瀏覽器儲存受限，本機偏好不會保留';

  // Shared workspaces render their controls later. Keep private upload and public
  // posting visibly disabled as well as denied by the server allowlist.
  const restrictControls = () => document.querySelectorAll('input[type="file"], [data-ex-upload], [data-ex-extract], [data-ex-files], [data-ex-download-file], #exchange-peer-form button[type="submit"]').forEach(control => {
    control.disabled = true;
    control.title = '展示未開放私人文件上傳、附件解析或公開發布；請使用虛構文字情境。';
  });
  restrictControls();
  new MutationObserver(restrictControls).observe(document.body, { childList: true, subtree: true });

  const dialog = $('#cgu-demo-dialog');
  const body = $('#cgu-demo-dialog-body');
  const status = $('#cgu-demo-status');
  const confirm = $('#cgu-demo-confirm');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const shortSchool = name => String(name || '').replace(/\s+[A-Za-z(（].*$/, '').trim() || String(name || '');

  const show = (title, html) => {
    $('#cgu-demo-dialog-title').textContent = title;
    body.innerHTML = html;
    status.textContent = '';
    confirm.hidden = true;
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
      body.innerHTML = '<p>此站共用 UniWay 原平台介面與功能，固定為長庚大學。林小程（生物醫學工程學系 大三・多益 750）為虛構示範學生，未經校方身分驗證。展示不代表校方採用、認證或合作。</p><p>每個瀏覽器有獨立展示工作區。進度暫存在此展示服務，重新整理可保留；24 小時後或服務重啟可能消失。不要輸入真實個資或上傳私人文件。</p><p>合作校名冊（78 所）、表列名額、合作校參考截止日、語言門檻、領航者補助要點與 116-1 校內申請時程已與 UniWay 主站同步；送件前仍請核對長庚國際事務處最新公告與目的校提名信。</p>' + data.rules.map(rule => `<h3>${esc(rule.title)}</h3><p>${esc(rule.body)}</p>`).join('') + data.sources.map(source => `<p><a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗</a><br>查核：${esc(source.checked_on)}；${esc(source.scope)}</p>`).join('') + '<h3>未來校方合作構想・規劃中</h3><p>尚未與校方串接，AI 問答亦規劃中。第一階段研究授權的公告、表格及附來源 FAQ；第二階段在學生同意與校方提供介面時研究登入和狀態；第三階段有正式接收 API 時研究文件送達及收件編號。需校方授權、最小權限、加密、保存及刪除政策；錄取與抵免由校方決定。</p>';
    } catch (error) {
      body.textContent = error.message + '，請稍後再試。';
    }
  };
  $('#cgu-demo-reset').onclick = () => {
    show('重設我的展示資料', '<p>只刪除這個瀏覽器的虛構學生申請紀錄與本機變更（並還原林小程預設示範系所條件），其他訪客及正式 UniWay 資料不受影響。</p>');
    confirm.hidden = false;
  };
  confirm.onclick = async () => {
    confirm.disabled = true;
    try {
      const response = await fetch('/demo/reset', { method: 'POST' });
      if (!response.ok) throw new Error('重設失敗，請稍後再試');
      window.localStorage.clear(); // bootstrap scopes both stores to the demo namespace
      window.sessionStorage.clear();
      location.href = '/';
    } catch (error) {
      status.textContent = error.message;
    } finally {
      confirm.disabled = false;
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
      location.href = '/?home=' + encodeURIComponent('長庚大學') + '#my-application';
      location.reload();
    } catch (error) {
      status.textContent = error.message;
    }
  };

  // 「合作構想示意」 menu is a native <details>; only add Escape / outside-click close.
  const previewMenu = $('#cgu-preview-menu');
  if (previewMenu) {
    document.addEventListener('click', event => {
      if (previewMenu.open && !previewMenu.contains(event.target)) previewMenu.open = false;
    });
    previewMenu.addEventListener('keydown', event => {
      if (event.key !== 'Escape' || !previewMenu.open) return;
      previewMenu.open = false;
      previewMenu.querySelector('summary').focus();
    });
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
  // Item 2:「我是哪個系？」4 個學院、36 個系所互動選校入口
  // ──────────────────────────────────────────────────────────────
  const finderState = {
    college: '工學院',
    department: '生物醫學工程學系',
    userPicked: false,
    showAllExchange: false,
  };

  function getAcademicUnits() {
    return window.UniWayAcademicUnits?.['長庚大學']?.colleges || {};
  }

  function isFourCollegesScope(text) {
    const raw = String(text || '');
    return raw.includes('四院皆可') || raw.includes('全校') || raw.includes('不限');
  }

  function dualDegreeLevelLabel(item, college) {
    const opts = (item.program_options || []).filter(opt =>
      String(opt.program_type || '').includes('雙學位')
      && (typeof academicScopeNeedsConfirmation === 'function' && academicScopeNeedsConfirmation(opt, 'colleges')
        || typeof collegeMatches === 'function' && collegeMatches(opt.colleges, college))
    );
    const raw = (opts.length ? opts.map(o => o.degree_levels || '').join('、') : (item.degree_levels || '')).normalize('NFKC');
    const levels = [];
    if (/學士|大學部/.test(raw)) levels.push('學士');
    if (/碩士/.test(raw)) levels.push('碩士');
    if (/博士/.test(raw)) levels.push('博士');
    return levels.length ? levels.join('／') : (raw || '依簡章');
  }

  function dualOptionNote(item, college) {
    const opts = (item.program_options || []).filter(opt =>
      String(opt.program_type || '').includes('雙學位')
      && (typeof collegeMatches === 'function' ? collegeMatches(opt.colleges, college) : true)
    );
    const text = opts.map(o => `${o.colleges || ''} ${o.eligibility || ''} ${o.application_info || ''}`).join(' ');
    if (/護理學系/.test(text) || /School of Nursing/i.test(item.school_name)) return '護理學系相關';
    if (/奈米/.test(text)) return '奈米學程辦理';
    if (/電子工程學系/.test(text)) return '電子／電機／資工相關';
    if (/嵌入式|電腦工程/.test(text)) return '電機／資工／AI 相關';
    if (opts.some(o => String(o.colleges || '').includes('全校'))) return '全校皆可申請';
    return '';
  }

  function sortExchangeForDept(list) {
    return [...list].sort((a, b) => {
      const ruleA = typeof cguDepartmentRestriction === 'function' && cguDepartmentRestriction(a) ? 0 : isFourCollegesScope(a.colleges) ? 2 : 1;
      const ruleB = typeof cguDepartmentRestriction === 'function' && cguDepartmentRestriction(b) ? 0 : isFourCollegesScope(b.colleges) ? 2 : 1;
      if (ruleA !== ruleB) return ruleA - ruleB;
      const deptRefA = a.availability_status === 'departmental_reference' ? 1 : 0;
      const deptRefB = b.availability_status === 'departmental_reference' ? 1 : 0;
      if (deptRefA !== deptRefB) return deptRefA - deptRefB;
      return String(a.school_name).localeCompare(String(b.school_name), 'zh-Hant');
    });
  }

  function sortDualForCollege(list, college) {
    return [...list].sort((a, b) => {
      const aAll = (a.program_options || []).some(o => String(o.program_type || '').includes('雙學位') && isFourCollegesScope(o.colleges)) ? 1 : 0;
      const bAll = (b.program_options || []).some(o => String(o.program_type || '').includes('雙學位') && isFourCollegesScope(o.colleges)) ? 1 : 0;
      if (aAll !== bAll) return aAll - bAll;
      return 0; // preserve official CGU dual-degree table order (e.g. 明尼蘇達 -> 內布拉斯加醫學中心 -> 馬里蘭巴爾的摩)
    });
  }

  function renderDeptFinder() {
    const host = $('#cgu-dept-finder');
    if (!host) return;
    const units = getAcademicUnits();
    const colleges = Object.keys(units);
    if (!colleges.length) return;

    if (!finderState.userPicked && typeof state === 'object' && state.eligibilityProfile?.college && units[state.eligibilityProfile.college]) {
      finderState.college = state.eligibilityProfile.college;
      if (state.eligibilityProfile.department && units[finderState.college].includes(state.eligibilityProfile.department)) {
        finderState.department = state.eligibilityProfile.department;
      }
    }
    if (!units[finderState.college]) finderState.college = colleges[0];
    const depts = units[finderState.college] || [];
    if (!depts.includes(finderState.department)) finderState.department = depts[0] || '';

    const partners = (typeof state === 'object' && state.dashboard?.partner_universities) || [];
    const totalDepts = colleges.reduce((sum, col) => sum + (units[col]?.length || 0), 0);

    if (!partners.length) {
      host.innerHTML = `<div class="cgu-dept-box"><span class="cgu-section-kicker">長庚 4 個學院 · ${totalDepts} 個系所</span><h2 id="cgu-dept-title">我是哪個系？正在載入合作校名冊…</h2></div>`;
      return;
    }

    const exchangeRaw = partners.filter(item =>
      cguProgramKindMatches(item, 'exchange') && cguOptionScopeMatches(item, finderState.college, finderState.department, 'exchange')
    );
    const dualRaw = partners.filter(item =>
      cguProgramKindMatches(item, 'dual_degree') && cguOptionScopeMatches(item, finderState.college, finderState.department, 'dual_degree')
    );
    const exchangeList = sortExchangeForDept(exchangeRaw);
    const dualList = sortDualForCollege(dualRaw, finderState.college);
    const uniqueCount = new Set([...exchangeList, ...dualList].map(item => item.school_name)).size;
    const overlapCount = exchangeList.length + dualList.length - uniqueCount;

    const collegeTabsHtml = colleges.map(col => {
      const active = col === finderState.college;
      const count = units[col]?.length || 0;
      return `<button type="button" class="cgu-finder-college-btn${active ? ' on' : ''}" data-cgu-finder-college="${esc(col)}" aria-pressed="${active}"><strong>${esc(col)}</strong><span>${count} 系所</span></button>`;
    }).join('');

    const deptChipsHtml = depts.map(dept => {
      const active = dept === finderState.department;
      return `<button type="button" class="cgu-finder-dept-chip${active ? ' on' : ''}" data-cgu-finder-dept="${esc(dept)}" aria-pressed="${active}">${esc(dept)}</button>`;
    }).join('');

    const previewCount = finderState.showAllExchange ? exchangeList.length : Math.min(8, exchangeList.length);
    const visibleExchange = exchangeList.slice(0, previewCount);

    const renderExchangeRow = item => {
      const rule = typeof cguDepartmentRestriction === 'function' ? cguDepartmentRestriction(item) : null;
      const toeic = typeof cguPartnerToeicStatus === 'function' ? cguPartnerToeicStatus(item, 'exchange') : 'unspecified';
      const isMgmtRef = item.availability_status === 'departmental_reference';
      const collegeScopeBadge = rule
        ? `<em class="cgu-mini-pill is-exclusive">${esc(rule.badge)}</em>`
        : isMgmtRef
          ? '<em class="cgu-mini-pill is-mgmt">管理學院院級管道</em>'
          : !isFourCollegesScope(item.colleges)
            ? `<em class="cgu-mini-pill is-college">${esc(item.colleges)}</em>`
            : '<em class="cgu-mini-pill is-general">四院皆可</em>';
      const toeicBadge = toeic === 'no_toeic'
        ? '<em class="cgu-mini-pill is-no-toeic">此校未列多益</em>'
        : toeic === 'has_toeic'
          ? '<em class="cgu-mini-pill is-has-toeic">有列多益</em>'
          : '';
      return `<li>
        <a href="#school=${encodeURIComponent(item.school_name)}" class="cgu-dept-school-row">
          <div class="cgu-dept-school-main">
            <strong>${esc(shortSchool(item.school_name))}</strong>
            <small>${esc([item.country, item.degree_levels].filter(Boolean).join(' · '))}</small>
          </div>
          <div class="cgu-dept-school-badges">${collegeScopeBadge}${toeicBadge}</div>
        </a>
      </li>`;
    };

    const renderDualRow = item => {
      const degLabel = dualDegreeLevelLabel(item, finderState.college);
      const note = dualOptionNote(item, finderState.college);
      const toeic = typeof cguPartnerToeicStatus === 'function' ? cguPartnerToeicStatus(item, 'dual_degree') : 'unspecified';
      return `<li>
        <a href="#school=${encodeURIComponent(item.school_name)}" class="cgu-dept-school-row is-dual">
          <div class="cgu-dept-school-main">
            <strong>${esc(shortSchool(item.school_name))}</strong>
            <small>${esc(item.country || '')}${note ? ` · ${esc(note)}` : ''}</small>
          </div>
          <div class="cgu-dept-school-badges">
            <em class="cgu-mini-pill is-degree">${esc(degLabel)}</em>
            ${toeic === 'no_toeic' ? '<em class="cgu-mini-pill is-no-toeic">此校未列多益</em>' : toeic === 'has_toeic' ? '<em class="cgu-mini-pill is-has-toeic">有列多益</em>' : ''}
          </div>
        </a>
      </li>`;
    };

    const mgmtBannerHtml = finderState.college === '管理學院'
      ? `<div class="cgu-mgmt-notice is-inline" role="note">
          <span class="cgu-mgmt-badge">院級管道提示</span>
          <div class="cgu-mgmt-copy">
            <strong>管理學院另有院級交換，請洽院國際辦公室</strong>
            <span>法國 IAE 艾克斯馬賽大學管理研究所、雷恩商學院共 2 所屬管理學院自辦管道，不在國際處中央當期名單上。</span>
          </div>
        </div>`
      : '';

    host.innerHTML = `
      <div class="cgu-dept-box">
        <header class="cgu-dept-head">
          <div>
            <span class="cgu-section-kicker">長庚專屬選校入口 · 4 個學院、${totalDepts} 個系所</span>
            <h2 id="cgu-dept-title">我是哪個系？選系直接看你能申請哪幾間</h2>
            <p>78 所合作校中僅 35 所標示「四院皆可」；先選學院與系所，系統自動過濾院系限制，並把「交換」與「雙學位」分開列出。</p>
          </div>
        </header>
        <div class="cgu-finder-step">
          <span class="cgu-step-label">1. 選擇學院</span>
          <div class="cgu-finder-colleges" role="group" aria-label="選擇長庚學院">${collegeTabsHtml}</div>
        </div>
        <div class="cgu-finder-step">
          <div class="cgu-step-row">
            <span class="cgu-step-label">2. 選擇系所（${esc(finderState.college)}共 ${depts.length} 個系所）</span>
            <label class="cgu-sr-select">
              <span class="visually-hidden">快速切換系所</span>
              <select id="cgu-finder-dept-select" aria-label="選擇系所">
                ${depts.map(d => `<option value="${esc(d)}"${d === finderState.department ? ' selected' : ''}>${esc(d)}</option>`).join('')}
              </select>
            </label>
          </div>
          <div class="cgu-finder-depts" role="group" aria-label="選擇系所">${deptChipsHtml}</div>
        </div>
        <div id="cgu-dept-result-summary" class="cgu-dept-summary" role="status" aria-live="polite">
          <div class="cgu-dept-summary-copy">
            <span class="cgu-dept-picked">${esc(finderState.college)} · ${esc(finderState.department)}</span>
            <h3>你可以申請 <strong>${uniqueCount}</strong> 所合作校</h3>
            <p>交換計畫 <b>${exchangeList.length}</b> 所 · 雙學位計畫 <b>${dualList.length}</b> 所${overlapCount > 0 ? `（其中 ${overlapCount} 所同時提供交換與雙學位）` : ''}</p>
          </div>
          <div class="cgu-dept-summary-actions">
            <button type="button" class="cgu-pill-action is-solid" data-cgu-apply-search="all">去搜尋頁看這 ${uniqueCount} 所 →</button>
            <button type="button" class="cgu-pill-action" data-cgu-apply-search="dual_degree">只看雙學位（${dualList.length} 所）</button>
            <button type="button" class="cgu-pill-action" data-cgu-sync-eligibility="1">帶入資格初判</button>
          </div>
        </div>
        ${mgmtBannerHtml}
        <div class="cgu-dept-columns">
          <section class="cgu-dept-col" aria-labelledby="cgu-col-exchange-title">
            <header class="cgu-dept-col-head">
              <div>
                <span class="cgu-col-tag is-exchange">交換學生 / 自費研修</span>
                <h4 id="cgu-col-exchange-title">交換計畫（${exchangeList.length} 所）</h4>
              </div>
              <button type="button" class="cgu-text-btn" data-cgu-apply-search="exchange">在搜尋頁篩選 →</button>
            </header>
            <ul id="cgu-dept-exchange-list" class="cgu-dept-list">${visibleExchange.map(renderExchangeRow).join('')}</ul>
            ${exchangeList.length > 8 ? `<button type="button" class="cgu-expand-btn" data-cgu-toggle-exchange="1">${finderState.showAllExchange ? '收合交換清單' : `展開全部 ${exchangeList.length} 所交換校`}</button>` : ''}
          </section>
          <section class="cgu-dept-col is-dual-col" aria-labelledby="cgu-col-dual-title">
            <header class="cgu-dept-col-head">
              <div>
                <span class="cgu-col-tag is-dual">雙聯學位專區</span>
                <h4 id="cgu-col-dual-title">雙學位計畫（${dualList.length} 所）</h4>
              </div>
              <button type="button" class="cgu-text-btn" data-cgu-apply-search="dual_degree">在搜尋頁篩選 →</button>
            </header>
            <ul id="cgu-dept-dual-list" class="cgu-dept-list">${dualList.map(renderDualRow).join('')}</ul>
            <p class="cgu-dual-footnote">雙學位之修業年限、學費減免與學位授予條件與一般交換不同，點選學校可檢視各院所簡章連結。</p>
          </section>
        </div>
      </div>`;
  }

  // Sync Management College inline reminder inside #advisor / #eligibility form
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

  document.addEventListener('click', event => {
    const scrollBtn = event.target.closest('[data-cgu-scroll]');
    if (scrollBtn) {
      const target = document.querySelector(scrollBtn.dataset.cguScroll);
      if (target) {
        event.preventDefault();
        target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      }
      return;
    }
    const colBtn = event.target.closest('[data-cgu-finder-college]');
    if (colBtn) {
      const col = colBtn.dataset.cguFinderCollege;
      const units = getAcademicUnits();
      if (col && units[col]) {
        finderState.userPicked = true;
        finderState.college = col;
        finderState.department = units[col][0] || '';
        finderState.showAllExchange = false;
        renderDeptFinder();
      }
      return;
    }
    const deptBtn = event.target.closest('[data-cgu-finder-dept]');
    if (deptBtn) {
      finderState.userPicked = true;
      finderState.department = deptBtn.dataset.cguFinderDept || '';
      renderDeptFinder();
      return;
    }
    if (event.target.closest('[data-cgu-toggle-exchange]')) {
      finderState.showAllExchange = !finderState.showAllExchange;
      renderDeptFinder();
      return;
    }
    const applyBtn = event.target.closest('[data-cgu-apply-search]');
    if (applyBtn && typeof state === 'object') {
      const mode = applyBtn.dataset.cguApplySearch;
      state.college = finderState.college;
      state.cguDepartment = finderState.department;
      state.cguProgramTab = mode === 'all' ? '' : mode;
      state.partnerView = 'list';
      const select = $('#college-filter');
      if (select) select.value = state.college;
      window.UniWayExplore?.refilter?.();
      window.location.hash = '#partners';
      return;
    }
    if (event.target.closest('[data-cgu-sync-eligibility]') && typeof state === 'object') {
      state.eligibilityProfile = {
        ...(state.eligibilityProfile || {}),
        college: finderState.college,
        department: finderState.department,
        degree: state.eligibilityProfile?.degree || '大學部',
        currentYear: state.eligibilityProfile?.currentYear || '大三',
        academicScore: state.eligibilityProfile?.academicScore ?? 78,
        languageTest: state.eligibilityProfile?.languageTest || 'toeic',
        languageScore: state.eligibilityProfile?.languageScore ?? 750,
        targetTerm: state.eligibilityProfile?.targetTerm || '2027-fall',
        academicYear: state.eligibilityProfile?.academicYear || '116',
        applicationRound: state.eligibilityProfile?.applicationRound || '第1學期',
      };
      const form = $('#advisor-form');
      if (form) delete form.dataset.draftOwner;
      if (typeof renderAdvisorForm === 'function') renderAdvisorForm();
      if (typeof restoreEligibilityForm === 'function') restoreEligibilityForm();
      if (typeof renderPartnerTable === 'function') renderPartnerTable();
      syncAdvisorMgmtNote();
      window.location.hash = '#eligibility';
    }
  });

  document.addEventListener('change', event => {
    if (event.target.id === 'cgu-finder-dept-select') {
      finderState.userPicked = true;
      finderState.department = event.target.value || '';
      renderDeptFinder();
      return;
    }
    if (event.target.id === 'advisor-college') {
      syncAdvisorMgmtNote();
    }
  });

  renderNavigatorCards();
  renderDeptFinder();
  if (typeof appReady !== 'undefined' && appReady?.then) {
    appReady.then(() => {
      renderNavigatorCards();
      renderDeptFinder();
      syncAdvisorMgmtNote();
    });
  }
  window.addEventListener('hashchange', () => {
    renderNavigatorCards();
    syncAdvisorMgmtNote();
  });
})();

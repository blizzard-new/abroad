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
  new MutationObserver(restrictControls).observe(document.body, {childList:true, subtree:true});
  const dialog = $('#cgu-demo-dialog');
  const body = $('#cgu-demo-dialog-body');
  const status = $('#cgu-demo-status');
  const confirm = $('#cgu-demo-confirm');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const show = (title, html) => {
    $('#cgu-demo-dialog-title').textContent = title; body.innerHTML = html;
    status.textContent = ''; confirm.hidden = true;
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
      body.innerHTML = '<p>此站共用 UniWay 原平台介面與功能，固定為長庚大學。林小程為虛構學生，未經校方身分驗證。展示不代表校方採用、認證或合作。</p><p>每個瀏覽器有獨立展示工作區。進度暫存在此展示服務，重新整理可保留；24 小時後或服務重啟可能消失。不要輸入真實個資或上傳私人文件。</p><p>合作校是 2026-10-11 歷史資料，包含不同方案，不等於當期開放名額。官方截止日與個人目標日期應分別確認。</p>' + data.rules.map(rule => `<h3>${esc(rule.title)}</h3><p>${esc(rule.body)}</p>`).join('') + data.sources.map(source => `<p><a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗</a><br>查核：${esc(source.checked_on)}；${esc(source.scope)}</p>`).join('') + '<h3>未來校方合作構想・規劃中</h3><p>尚未與校方串接，AI 問答亦規劃中。第一階段研究授權的公告、表格及附來源 FAQ；第二階段在學生同意與校方提供介面時研究登入和狀態；第三階段有正式接收 API 時研究文件送達及收件編號。需校方授權、最小權限、加密、保存及刪除政策；錄取與抵免由校方決定。</p>';
    } catch (error) { body.textContent = error.message + '，請稍後再試。'; }
  };
  $('#cgu-demo-reset').onclick = () => {
    show('重設我的展示資料', '<p>只刪除這個瀏覽器的虛構學生工作區與展示本機紀錄，其他訪客及正式 UniWay 資料不受影響。</p>');
    confirm.hidden = false;
  };
  confirm.onclick = async () => {
    confirm.disabled = true;
    try {
      const response = await fetch('/demo/reset', {method:'POST'});
      if (!response.ok) throw new Error('重設失敗，請稍後再試');
      window.localStorage.clear(); // bootstrap scopes both stores to the demo namespace
      window.sessionStorage.clear();
      location.href = '/';
    } catch (error) { status.textContent = error.message; }
    finally { confirm.disabled = false; }
  };
  $('#cgu-demo-seed').onclick = async () => {
    show('載入示範申請', '<p>以原平台的申請流程建立林小程的 2027 秋季研究目標；當期資格與名額待確認。已有相同計畫時直接開啟。</p>');
    try {
      const response = await fetch('/account/application-paths?home_school=' + encodeURIComponent('長庚大學'));
      if (!response.ok) throw new Error('無法載入展示工作區');
      const registry = await response.json();
      const made = await fetch('/account/application-paths', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({revision:registry.revision, home_school:'長庚大學', target_school:'林肯大學 Lincoln University', academic_year:'116', departure_year:'2027', semester:'fall'})});
      if (!made.ok) { const error = await made.json(); throw new Error(typeof error.detail === 'string' ? error.detail : '建立失敗，請稍後再試'); }
      location.href = '/?home=' + encodeURIComponent('長庚大學') + '#my-application';
      location.reload();
    } catch (error) { status.textContent = error.message; }
  };
})();

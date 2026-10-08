(function () {
  "use strict";
  const labels = {
    program_scope: "接收計畫、學制與校區", eligibility: "合作校接收資格",
    language: "合作校語言與替代證明", nomination_deadline: "合作校提名截止",
    application_deadline: "合作校申請截止", documents: "合作校文件要求（已查項目）",
    application_forms: "合作校申請表", academic_calendar: "校曆與考試",
    course_restrictions: "課程及學分限制", housing: "住宿與床位",
    housing_deadline: "住宿申請／付款截止", costs: "住宿與生活費用",
    insurance: "保險", visa: "簽證及居留", arrival: "抵達與迎新",
    host_tuition: "合作校學費", exchange_duration: "交換期間及延長",
  };
  const statuses = {
    verified_current: "當期已核實", reference_only: "歷史參考，不能作本期申請依據",
    missing: "本期未核實／來源未載", needs_confirmation: "適用年度或條件待確認",
    conflict: "來源矛盾，待確認", explicit_not_announced: "官方明示尚未公告",
  };
  function render(partner, escapeHtml, keys) {
    const fields = partner.partner_exchange_details;
    if (!fields || !Object.keys(fields).length) return "";
    return `<section class="partner-student-summary ccu-receiving-school-details" aria-label="合作校接收資料">
      <h3>合作校接收資料 · ${escapeHtml(partner.application_round || "")}</h3>
      <p>以下是合作校接收交換生的規定。中正的校內資格、名額及截止須分別符合；每欄的適用年度、未核實新版及矛盾另標示。</p>
      ${(keys || Object.keys(labels)).map(key => {
        const field = fields[key];
        if (!field) return "";
        return `<details class="overview-more" data-ccu-field="${escapeHtml(key)}"><summary>${escapeHtml(labels[key])} · ${escapeHtml(statuses[field.status] || field.status)}</summary>
          <p>${escapeHtml(field.value || field.reason)}</p>
          ${field.value ? `<p>${escapeHtml(field.reason)}</p>` : ""}
          ${(field.evidence || []).map(ev => {
            const pages = ev.source_pages?.length ? ` · PDF第${ev.source_pages.join("、")}頁` : " · 官方文件／網頁原文";
            return `<a href="${escapeHtml(ev.source_url)}" target="_blank" rel="noreferrer">資料來源${escapeHtml(pages)}</a>
              <p>適用：${escapeHtml(ev.academic_year || "年度未核實")} · 查核${escapeHtml((ev.checked_at || "").slice(0, 10))}</p>
              <details><summary>查核原文與適用限制</summary><p>${escapeHtml(ev.excerpt || "")}</p><p>${escapeHtml(ev.note || "")}</p></details>`;
          }).join("")}</details>`;
      }).join("")}</section>`;
  }
  window.UniWayCcuDetails = { render };
}());

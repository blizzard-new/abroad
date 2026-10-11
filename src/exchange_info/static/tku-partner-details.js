(function () {
  "use strict";
  const labels = {
    home_eligibility: "淡江校內資格", home_language: "淡江校內語言", quota: "淡江名額",
    home_deadline: "淡江校內期限", documents: "淡江申請文件", latest_forms: "接待校表格與程序",
    host_eligibility: "接待校資格與計畫範圍", host_language: "接待校語言與待確認差異",
    host_deadline: "接待校申請期限", host_nomination_deadline: "接待校提名期限",
    study_period: "交換期間", department_scope: "院系及學制範圍", campus: "校區",
    course_restrictions: "課程限制", housing: "住宿", housing_costs: "住宿費用",
    costs: "費用", insurance: "保險", living_costs: "生活費參考", transport: "交通",
    eligibility: "接待校資格", language_requirement: "接待校語言",
    application_deadline: "淡江校內期限", partner_application_deadline: "接待校申請期限",
    partner_documents: "接待校文件", partner_application_prerequisite: "提名及申請前提",
    semester_dates: "學期日期", tuition_info: "費用", housing_info: "住宿",
  };
  function render(partner, escapeHtml) {
    const fields = partner.field_evidence || {};
    const entries = Object.entries(fields).filter(([key]) => labels[key]);
    if (!entries.length) return "";
    return `<details class="overview-more tku-source-details"><summary>淡江與接待校資料、適用年度及來源</summary>
      <p>接待校參考與淡江本期甄選分開核對；來源學年度已確認仍不代表淡江本期適用。未核實新版不等於官方明示尚未公告。</p>
      ${entries.map(([key, e]) => {
        const state = e.status === "verified_current" ? "當期已核實"
          : e.status === "conflict" ? "來源矛盾，待確認"
          : e.status === "explicit_not_announced" ? "官方明示尚未公告"
          : e.status === "reference_only" ? "接待校／歷史參考，本期適用未核實" : "本期未核實／待確認";
        const url = e.source_pages?.length ? `${e.source_url.split("#")[0]}#page=${e.source_pages[0]}` : e.source_url;
        return `<article class="university-fact" data-tku-field="${escapeHtml(key)}"><strong>${escapeHtml(labels[key])} · ${escapeHtml(state)}</strong>
          <p>${escapeHtml(e.excerpt || e.reference_excerpt || "適用本期的內容未核實")}</p>
          <p>適用：${escapeHtml(e.academic_year || "來源年度未核實")} · 查核${escapeHtml((e.checked_at || "").slice(0, 10))}</p>
          <p>${escapeHtml(e.note || "")}</p><a href="${escapeHtml(url || partner.source_url)}" target="_blank" rel="noreferrer">官方來源</a></article>`;
      }).join("")}</details>`;
  }
  function agreementMeta(partner) {
    if (partner.availability_status !== "agreement_only") return null;
    return { status: "agreement_only", shortLabel: "協議參考／本期未核實", cardLabel: "協議參考／本期未核實",
      hint: "須另核對淡江本期名額、院系計畫與申請期間", matchLabel: "本期名額待確認",
      reason: "姊妹校協議參考；本期名額與開放尚未核實", blocked: true };
  }
  window.UniWayTkuDetails = { render, agreementMeta };
}());

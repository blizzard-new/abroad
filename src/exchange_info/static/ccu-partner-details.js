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
    host_tuition: "合作校學費", exchange_duration: "交換期間及延長", application_fee: "合作校申請費",
  };
  const statuses = {
    verified_current: "當期已核實", reference_only: "其他年度／梯次參考，不能作本期申請依據",
    missing: "本期未核實／來源未載", needs_confirmation: "適用年度或條件待確認",
    conflict: "來源矛盾，待確認", explicit_not_announced: "官方明示尚未公告",
  };
  const researchLabels = {
    verified_supported: "已有當期依據", official_not_announced: "官方明示尚未公告",
    unresolved_source_conflict: "來源矛盾尚未釐清，公開依據續查",
    login_or_school_confirmation: "須個別通知或校方釐清", source_technical_failure: "已查入口技術失敗，替代來源續查",
    alternative_official_sources_not_fully_checked: "官方替代來源尚待補查",
  };
  function render(partner, escapeHtml, keys, homeSchool) {
    const isNtu = homeSchool === "國立臺灣大學";
    const homeLabel = isNtu ? "臺大" : homeSchool || "中正";
    const isOtherHome = Boolean(homeSchool) && !["國立臺灣大學", "國立中正大學"].includes(homeSchool);
    const fieldLabels = isNtu ? { ...labels, calendar: "校曆與考試", deadlines: "合作校提名與申請期限",
      courses: "課程及學分限制", cost: "費用與生活預算", insurance_visa: "保險與簽證" } : labels;
    let assets = {};
    try { assets = JSON.parse(partner.reference_data?.ccu_campus_assets || "{}"); } catch (_) { /* Missing metadata stays absent. */ }
    const photo = assets.photo;
    const campus = photo ? `<section class="ccu-campus-attribution" aria-label="校園照片與授權"><h3>校園照片來源</h3>
      <p>${escapeHtml(photo.campus_caption)}</p><p>${escapeHtml(photo.artist)} · <a href="${escapeHtml(photo.license_url)}" target="_blank" rel="noreferrer">${escapeHtml(photo.license_name)}</a> · <a href="${escapeHtml(photo.source_page_url)}" target="_blank" rel="noreferrer">照片原頁 ↗</a></p>
      <p>${escapeHtml(photo.modifications)} ${escapeHtml(photo.applicability)} 查核${escapeHtml(photo.checked_at.slice(0, 10))}。</p>
      ${assets.coordinates ? `<p>${escapeHtml(assets.coordinates.note)}</p>` : ""}</section>` : "";
    let completion = {};
    try { completion = JSON.parse(partner.reference_data?.ccu_completion || "{}"); } catch (_) { /* Absent data stays absent. */ }
    const profileLabels = { city: "校園所在城市", location: "官方聯絡地址", website: "官方網站", degree_levels: "學制參考", colleges: "院系參考", transport: "交通公開入口", campus_life: "校園服務公開入口" };
    const referenceFields = completion.reference_host_fields || {};
    const showEvidence = field => (field.evidence || []).map(ev => {
      const source = ev.source_pages?.length ? `${ev.source_url.split("#")[0]}#page=${ev.source_pages[0]}` : ev.source_url;
      return `<p><a href="${escapeHtml(source)}" target="_blank" rel="noreferrer">${escapeHtml(ev.source_pages?.length ? `PDF第${ev.source_pages.join("、")}頁` : "來源原頁")} ↗</a>${ev.service_url ? ` · <a href="${escapeHtml(ev.service_url)}" target="_blank" rel="noreferrer">服務入口 ↗</a>` : ""}</p><p>適用：${escapeHtml(ev.academic_year || "年度未核實")}；查核${escapeHtml((ev.checked_at || "").slice(0, 10))}</p><details><summary>查核原文</summary><p>${escapeHtml(ev.excerpt || ev.reference_excerpt || "")}</p></details>`;
    }).join("");
    const generalFields = completion.general_campus_fields || {};
    const general = Object.keys(generalFields).length ? `<section class="ccu-general-campus" aria-label="一般校園公開資料"><h3>一般校園公開資料</h3><p>校園位置與服務入口不代表2027春季可申請、住宿保證或個人接收校區。</p>${Object.entries(generalFields).filter(([, f]) => f.value).map(([key, field]) => `<details data-ccu-general="${escapeHtml(key)}"><summary>${escapeHtml(profileLabels[key] || key)} · 查核日已核實</summary><p>${escapeHtml(field.value)}</p><p>${escapeHtml(field.reason)}</p>${showEvidence(field)}</details>`).join("")}</section>` : "";
    const reference = Object.keys(referenceFields).length ? `<section class="ccu-reference-host" aria-label="未開放參考校接待資料"><h3>參考校接待資料 · 中正本期未開放</h3><p>以下保留接待校各年度依據。接待校規定即使載明2027，也不變更中正名冊的本期未開放狀態。</p>${Object.entries(referenceFields).map(([key, field]) => `<details data-ccu-reference-field="${escapeHtml(key)}"><summary>${escapeHtml(labels[key] || key)} · ${escapeHtml(statuses[field.status] || field.status)}</summary><p>${escapeHtml(field.value || field.reason)}</p>${field.value ? `<p>${escapeHtml(field.reason)}</p>` : ""}${showEvidence(field)}</details>`).join("")}</section>` : "";
    const supplement = campus + general + reference;
    const fields = partner.partner_exchange_details;
    if (!fields || !Object.keys(fields).length) return supplement;
    return `${supplement}<section class="partner-student-summary ccu-receiving-school-details" aria-label="合作校接收資料">
      <h3>合作校接收資料 · ${escapeHtml(partner.application_round || "")}</h3>
      <p>以下是合作校接收交換生的規定。${escapeHtml(homeLabel)}的校內資格、名額及截止須分別符合；每欄的適用年度、未核實新版及矛盾另標示。</p>
      ${(keys || Object.keys(fieldLabels)).map(key => {
        const field = fields[key];
        if (!field) return "";
        const status = (isNtu || isOtherHome) && field.status === "reference_only" ? `接待校／欄位參考，尚未確認${homeLabel}本期適用` : statuses[field.status] || field.status;
        const research = (isNtu || isOtherHome) && field.research_category === "verified_supported" ? "已有原文依據，適用範圍另列" : researchLabels[field.research_category];
        return `<details class="overview-more" data-ccu-field="${escapeHtml(key)}"><summary>${escapeHtml(fieldLabels[key])} · ${escapeHtml(status)}</summary>
          <p>${escapeHtml(field.value || field.reason)}</p>
          ${field.value ? `<p>${escapeHtml(field.reason)}</p>` : ""}
          ${field.research_category ? `<p>查核進度：${escapeHtml(research)}。${escapeHtml(field.research_note || "")}</p>` : ""}
          ${(field.evidence || []).map(ev => {
            const pages = ev.source_pages?.length ? ` · PDF第${ev.source_pages.join("、")}頁` : " · 官方文件／網頁原文";
            const sourceUrl = ev.source_pages?.length ? `${ev.source_url.split("#")[0]}#page=${ev.source_pages[0]}` : ev.source_url;
            return `<a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">資料來源${escapeHtml(pages)}</a>
              <p>適用：${escapeHtml(ev.academic_year || "年度未核實")} · 查核${escapeHtml((ev.checked_at || "").slice(0, 10))}</p>
              <details><summary>查核原文與適用限制</summary><p>${escapeHtml(ev.excerpt || "")}</p><p>${escapeHtml(ev.note || "")}</p></details>`;
          }).join("")}
          ${field.source_checks?.length ? `<details><summary>已查來源與實際結果</summary>${field.source_checks.map(check => `<p><a href="${escapeHtml(check.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(check.source_id)}</a> · ${escapeHtml(check.timestamp_precision === "date" ? check.checked_at.slice(0, 10) : check.checked_at)} · ${escapeHtml(check.result)}</p>`).join("")}</details>` : ""}
          </details>`;
      }).join("")}</section>`;
  }
  function renderProfileLife(profile, escapeHtml) {
    const sections = profile.student_guide_sections || [];
    const visible = [
      ["transport", "交通與通勤"], ["campus_life", "校園生活與支援"],
      ...sections.filter(section => ["healthcare_reference", "return_preparation"].includes(section.key))
        .map(section => [section.key, section.title]),
    ];
    return `<section class="ccu-profile-life" aria-label="交通與校園生活">${visible.map(([key, title]) => {
      const section = sections.find(item => item.key === key);
      return `<article class="overview-more" data-ccu-life-field="${escapeHtml(key)}"><h4>${escapeHtml(title)}</h4>${section
        ? `${section.points.some(point => point.startsWith(section.summary)) ? "" : `<p>${escapeHtml(section.summary)}</p>`}${section.points.map(point => `<p>${escapeHtml(point)}</p>`).join("")}<p>${escapeHtml(section.caution || "")}</p>${section.source_urls.map(url => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">官方資料來源 ↗</a>`).join(" ")}`
        : `<p>本平台尚未核實此項內容，官方公開來源仍在續查。</p>`}</article>`;
    }).join("")}</section>`;
  }
  window.UniWayCcuDetails = { render, renderProfileLife };
}());

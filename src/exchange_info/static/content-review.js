"use strict";

const initialQueryParams = new URLSearchParams(window.location.search);
const destinationReviewHomeUniversities = ["長庚大學", "國立臺北大學", "淡江大學", "天主教輔仁大學", "東吳大學", "國立臺灣師範大學", "中原大學", "國立臺灣科技大學", "元智大學", "逢甲大學", "國立中山大學", "國立中興大學", "國立臺北科技大學", "國立政治大學", "國立成功大學", "國立陽明交通大學", "國立清華大學", "中國文化大學", "文藻外語大學", "國立高雄科技大學", "國立雲林科技大學", "國立臺灣海洋大學", "國立彰化師範大學", "國立高雄師範大學", "臺北醫學大學", "中山醫學大學", "中國醫藥大學", "高雄醫學大學", "銘傳大學", "國立臺北商業大學", "國立暨南國際大學", "國立東華大學", "東海大學", "世新大學", "靜宜大學", "實踐大學", "國立高雄大學", "國立嘉義大學", "國立臺中科技大學", "國立虎尾科技大學", "臺北市立大學", "國立臺中教育大學", "國立臺北藝術大學", "國立臺灣藝術大學"];
const requestedDestinationReviewHome = initialQueryParams.get("destination_home") || "";
const destinationReviewDraftStoragePrefix = "exchange.destination-review-draft.v1";
const workflowReviewDraftStoragePrefix = "exchange.workflow-review-draft.v1";
const workflowApplicabilityDraftStoragePrefix = "exchange.workflow-applicability-draft.v1";
const requestedWorkflowReviewStatus = initialQueryParams.get("review_status") || "";
const initialWorkflowReviewStatus = ["pending_review", "published", "rejected"].includes(
  requestedWorkflowReviewStatus
) ? requestedWorkflowReviewStatus : "backlog";
const requestedWorkflowReviewRevision = initialQueryParams.get("workflow_revision") || "";

const state = {
  admin: null,
  revisions: [],
  sourceReplacementCandidates: [],
  backlog: { items: [], total_count: 0, unstaged_count: 0, staged_count: 0, home_universities: [] },
  releaseReadiness: null,
  workflowIssueReports: [],
  workflowIssueReportStatus: "pending",
  workflowIssueReportsLoading: false,
  workflowIssueReportsError: "",
  workflowIssueReportRequestSequence: 0,
  workflowIssueReportReviewing: {},
  workflowIssueReportMutationIds: new Map(),
  destinationProfileReview: null,
  destinationProfileReviewError: "",
  destinationPublicationHistory: null,
  destinationPublicationHistoryError: "",
  destinationReviewHomeUniversity: destinationReviewHomeUniversities.includes(
    requestedDestinationReviewHome
  ) ? requestedDestinationReviewHome : "長庚大學",
  destinationReviewRequestSequence: 0,
  destinationPublicationRequestSequence: 0,
  destinationReviewBatchRequestSequence: 0,
  destinationReviewBatchId: initialQueryParams.get("destination_batch") || "",
  destinationReviewBatchSnapshot: initialQueryParams.get("destination_snapshot") || "",
  destinationReviewBatchSize: Math.min(50, Math.max(1, Number.parseInt(
    initialQueryParams.get("destination_batch_size") || "10",
    10
  ) || 10)),
  destinationReviewBatchProfileHashes: [],
  destinationReviewBatchChecklistPath: "",
  destinationReviewBatchStale: false,
  destinationReviewBatchError: "",
  destinationReviewFocusProfileHash: "",
  workflowPublicationHistory: null,
  workflowPublicationHistoryError: "",
  destinationReviewSearch: "",
  destinationReviewProgressFilter: "",
  destinationReviewReadinessFilter: "",
  destinationReviewVisibleLimit: 10,
  destinationReviewSubmitting: {},
  destinationPromotionSubmitting: {},
  destinationRollbackSubmitting: {},
  workflowRollbackSubmitting: {},
  workflowReviewOwnerFilter: "",
  workflowReviewReadinessFilter: "",
  workflowReviewFocusRevisionId: initialWorkflowReviewStatus === "pending_review"
    && requestedWorkflowReviewRevision.length <= 128
    ? requestedWorkflowReviewRevision
    : "",
  backlogSearch: "",
  backlogHomeUniversity: "",
  backlogGapFilter: "",
  backlogSort: "gaps",
  backlogVisibleLimit: 25,
  workflowDeepLinkKey: new URLSearchParams(window.location.search).get("workflow_key") || "",
  reviewBatchId: new URLSearchParams(window.location.search).get("review_batch") || "",
  reviewBatchSize: Math.min(50, Math.max(1, Number.parseInt(
    new URLSearchParams(window.location.search).get("batch_size") || "10",
    10
  ) || 10)),
  reviewBatchWorkflowKeys: [],
  workflowDeepLinkSnapshot: new URLSearchParams(window.location.search).get("review_snapshot") || "",
  workflowDeepLinkStale: false,
  sourceEvidenceWorkflowKeys: [],
  sourceEvidenceUrl: "",
  staging: {},
  batchStaging: false,
  comparisons: {},
  comparisonLoading: {},
  comparisonErrors: {},
  queueRequestSequence: 0,
  loading: false,
  error: "",
};

const $ = (selector, root = document) => root.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeExternalUrl(value) {
  const raw = String(value ?? "").trim();
  if (!raw) return "#";
  try {
    const parsed = new URL(raw, window.location.origin);
    if (parsed.protocol === "https:" || parsed.protocol === "http:") {
      return parsed.href;
    }
  } catch (_error) {
    // Reject malformed or non-HTTP URLs.
  }
  return "#";
}

function formatDate(value) {
  if (!value) return "待確認";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return new Intl.DateTimeFormat("zh-TW", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const error = new Error(payload?.detail || `操作失敗（${response.status}）`);
    error.status = response.status;
    throw error;
  }
  return payload;
}

function announce(message, tone = "success") {
  const node = $("#review-announcement");
  node.textContent = message;
  node.classList.toggle("is-error", tone === "error");
}

const workflowIssueCategoryLabels = {
  eligibility: "申請資格",
  deadline: "截止期限",
  document: "文件或份數",
  submission: "送件方式",
  source: "官方來源",
  other: "其他",
};

const workflowIssueStatusLabels = {
  pending: "待處理",
  resolved: "已確認",
  dismissed: "不成立",
};

function renderWorkflowIssueReports() {
  const container = $("#workflow-issue-report-queue");
  if (!container) return;
  container.setAttribute("aria-busy", state.workflowIssueReportsLoading ? "true" : "false");
  if (state.workflowIssueReportsLoading) {
    container.innerHTML = '<div class="review-loading">正在載入學生錯誤回報…</div>';
    return;
  }
  if (state.workflowIssueReportsError) {
    container.innerHTML = `<div class="review-error">${escapeHtml(state.workflowIssueReportsError)}</div>`;
    return;
  }
  if (!state.workflowIssueReports.length) {
    container.innerHTML = '<div class="review-empty">這個狀態目前沒有學生錯誤回報。</div>';
    return;
  }

  container.innerHTML = state.workflowIssueReports.map((report) => {
    const reviewing = Boolean(state.workflowIssueReportReviewing[report.id]);
    const context = [report.college, report.department, report.academic_year, report.application_round]
      .filter(Boolean)
      .map(escapeHtml)
      .join(" · ");
    const step = report.step_title
      ? `${escapeHtml(report.step_title)}${report.step_rule_id ? ` <code>${escapeHtml(report.step_rule_id)}</code>` : ""}`
      : "完整申請流程";
    const review = report.review;
    return `
      <article class="workflow-issue-report-card status-${escapeHtml(report.status)}" data-workflow-issue-report-id="${escapeHtml(report.id)}">
        <header>
          <div><span>${escapeHtml(report.home_school)} → ${escapeHtml(report.school_name)}</span><h3>${step}</h3></div>
          <strong>${escapeHtml(workflowIssueStatusLabels[report.status] || report.status)}</strong>
        </header>
        <dl class="workflow-issue-report-meta">
          <div><dt>類型</dt><dd>${escapeHtml(workflowIssueCategoryLabels[report.category] || report.category)}</dd></div>
          <div><dt>流程版本</dt><dd>v${escapeHtml(report.workflow_version)} · <code>${escapeHtml(String(report.workflow_snapshot || "").slice(0, 12))}…</code></dd></div>
          <div><dt>回報時間</dt><dd>${escapeHtml(formatDate(report.created_at))}</dd></div>
          ${context ? `<div><dt>適用情境</dt><dd>${context}</dd></div>` : ""}
        </dl>
        <section class="workflow-issue-report-description"><strong>學生說明</strong><p>${escapeHtml(report.description)}</p></section>
        <a class="workflow-issue-report-source" href="${escapeHtml(safeExternalUrl(report.official_source_url))}" target="_blank" rel="noreferrer">開啟學生附上的官方來源 ↗</a>
        ${report.status === "pending" ? `
          <div class="workflow-issue-report-review">
            <label><span>處理說明（至少 10 個字）</span><textarea data-workflow-issue-report-note minlength="10" maxlength="1000" rows="3" placeholder="記錄核對的官方頁面、判斷與後續處置。" ${reviewing ? "disabled" : ""}></textarea></label>
            <div><button type="button" data-workflow-issue-review="resolved" ${reviewing ? "disabled" : ""}>回報成立，完成核對</button><button type="button" class="secondary" data-workflow-issue-review="dismissed" ${reviewing ? "disabled" : ""}>目前資料正確，標記不成立</button></div>
            <small>回報成立只會關閉本案；如需修正，仍須另外建立 revision 並完成雙人審查。</small>
          </div>` : review ? `
          <div class="workflow-issue-report-decision"><strong>${escapeHtml(review.reviewer_display_name)} · ${escapeHtml(formatDate(review.reviewed_at))}</strong><p>${escapeHtml(review.note)}</p></div>` : ""}
      </article>`;
  }).join("");
}

async function loadWorkflowIssueReports() {
  const requestSequence = ++state.workflowIssueReportRequestSequence;
  state.workflowIssueReportsLoading = true;
  state.workflowIssueReportsError = "";
  renderWorkflowIssueReports();
  const status = state.workflowIssueReportStatus;
  const path = "/admin/application-workflow-issue-reports"
    + (status ? `?status=${encodeURIComponent(status)}` : "");
  try {
    const reports = await requestJson(path);
    if (requestSequence !== state.workflowIssueReportRequestSequence) return "superseded";
    if (!Array.isArray(reports)) throw new Error("待審佇列回應格式不正確。");
    state.workflowIssueReports = reports;
    return "applied";
  } catch (error) {
    if (requestSequence !== state.workflowIssueReportRequestSequence) return "superseded";
    state.workflowIssueReports = [];
    state.workflowIssueReportsError = error.message;
    return "failed";
  } finally {
    if (requestSequence === state.workflowIssueReportRequestSequence) {
      state.workflowIssueReportsLoading = false;
      renderWorkflowIssueReports();
    }
  }
}

function createWorkflowIssueReviewMutationId() {
  const suffix = window.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(16).slice(2)}-${Math.random().toString(16).slice(2)}`;
  return `workflow-report-review-${suffix}`;
}

async function reviewWorkflowIssueReport(button) {
  const card = button.closest("[data-workflow-issue-report-id]");
  const reportId = card?.dataset.workflowIssueReportId || "";
  const status = button.dataset.workflowIssueReview;
  const note = $("[data-workflow-issue-report-note]", card)?.value.trim() || "";
  if (!reportId || !["resolved", "dismissed"].includes(status)) return;
  if (note.length < 10) {
    announce("處理說明至少需要 10 個字，並請留下你實際核對的依據。", "error");
    $("[data-workflow-issue-report-note]", card)?.focus();
    return;
  }
  const payload = JSON.stringify({ status, note });
  const mutationKey = `${reportId}\n${payload}`;
  const mutationId = state.workflowIssueReportMutationIds.get(mutationKey)
    || createWorkflowIssueReviewMutationId();
  state.workflowIssueReportMutationIds.set(mutationKey, mutationId);
  state.workflowIssueReportReviewing[reportId] = true;
  card.querySelectorAll("button, textarea").forEach((control) => { control.disabled = true; });
  const abortController = new AbortController();
  const timeoutId = window.setTimeout(() => abortController.abort(), 30_000);
  try {
    const reviewed = await requestJson(`/admin/application-workflow-issue-reports/${encodeURIComponent(reportId)}`, {
      method: "PATCH",
      headers: { "X-Content-Report-Mutation-ID": mutationId },
      body: payload,
      signal: abortController.signal,
    });
    if (
      !reviewed
      || reviewed.id !== reportId
      || reviewed.status !== status
      || reviewed.review?.status !== status
    ) {
      const error = new Error("伺服器沒有回傳可驗證的審核結果。");
      error.outcomeUnknown = true;
      throw error;
    }
    state.workflowIssueReportMutationIds.delete(mutationKey);
    announce(status === "resolved"
      ? "回報已確認成立；正式規定尚未變更，請另走 revision 與雙人審查。"
      : "回報已標記不成立；正式規定沒有變更。"
    );
    await loadWorkflowIssueReports();
  } catch (error) {
    if (error?.status && error.status < 500) {
      state.workflowIssueReportMutationIds.delete(mutationKey);
    }
    if ([404, 409].includes(error?.status)) {
      const refreshResult = await loadWorkflowIssueReports();
      announce(refreshResult === "applied"
        ? "這筆回報已不存在或已由其他管理員處理，佇列已重新整理。"
        : refreshResult === "superseded"
        ? "這筆回報的狀態已變更；目前正等待較新的佇列載入結果。"
        : "這筆回報的狀態已變更，但佇列重新載入失敗；請稍後手動重試。", "error");
      return;
    }
    announce(!error?.status || error.status >= 500
      ? "連線或伺服器回應中斷，結果尚未確認；請勿修改說明，稍後可安全重試。"
      : error.message, "error");
  } finally {
    window.clearTimeout(timeoutId);
    delete state.workflowIssueReportReviewing[reportId];
    const currentCard = Array.from(
      document.querySelectorAll("[data-workflow-issue-report-id]"),
    ).find((item) => item.dataset.workflowIssueReportId === reportId);
    if (currentCard) {
      currentCard.querySelectorAll("button, textarea").forEach((control) => {
        control.disabled = false;
      });
    }
  }
}

function approvalProgress(revision) {
  const count = revision.review_approvals?.length || 0;
  const required = revision.required_review_count || 2;
  return { count, required, ready: count >= required };
}

function currentAdminApproved(revision) {
  return Boolean(
    state.admin
    && (revision.review_approvals || []).some((row) => row.reviewer_id === state.admin.id)
  );
}

function workflowReviewDraftKey(revision) {
  const reviewerId = state.admin?.id || "";
  const revisionId = revision?.id || "";
  const contentHash = revision?.content_hash || "";
  if (!reviewerId || !revisionId || !contentHash) return "";
  return `${workflowReviewDraftStoragePrefix}:${reviewerId}:${revisionId}:${contentHash}`;
}

function loadWorkflowReviewDraft(revision) {
  const key = workflowReviewDraftKey(revision);
  if (!key) return null;
  try {
    const raw = window.sessionStorage.getItem(key);
    if (!raw) return null;
    const payload = JSON.parse(raw);
    if (
      !payload
      || payload.reviewer_id !== state.admin?.id
      || payload.revision_id !== revision.id
      || payload.content_hash !== revision.content_hash
    ) {
      window.sessionStorage.removeItem(key);
      return null;
    }
    return {
      reviewer_id: state.admin.id,
      revision_id: revision.id,
      content_hash: revision.content_hash,
      reviewed_source_urls: Array.isArray(payload.reviewed_source_urls)
        ? payload.reviewed_source_urls.filter((value) => typeof value === "string")
        : [],
      reviewed_rule_keys: Array.isArray(payload.reviewed_rule_keys)
        ? payload.reviewed_rule_keys.filter((value) => typeof value === "string")
        : [],
      note: typeof payload.note === "string" ? payload.note.slice(0, 2000) : "",
      saved_at: typeof payload.saved_at === "string" ? payload.saved_at : "",
    };
  } catch (_error) {
    try {
      window.sessionStorage.removeItem(key);
    } catch (_storageError) {
      // The review form remains usable even when browser storage is unavailable.
    }
    return null;
  }
}

function clearWorkflowReviewDraft(revision) {
  const key = workflowReviewDraftKey(revision);
  if (!key) return;
  try {
    window.sessionStorage.removeItem(key);
  } catch (_error) {
    // A local convenience draft must never block a backend review action.
  }
}

function saveWorkflowReviewDraftFromItem(item) {
  const revisionId = item?.dataset.revisionId || "";
  const revision = state.revisions.find((row) => row.id === revisionId);
  const key = workflowReviewDraftKey(revision);
  if (!item || !revision || !key) return;
  const payload = {
    reviewer_id: state.admin.id,
    revision_id: revision.id,
    content_hash: revision.content_hash,
    reviewed_source_urls: [...item.querySelectorAll("[data-approval-source]:checked")]
      .map((checkbox) => checkbox.dataset.sourceUrl)
      .filter(Boolean),
    reviewed_rule_keys: [...item.querySelectorAll("[data-approval-rule]:checked")]
      .map((checkbox) => checkbox.dataset.ruleKey)
      .filter(Boolean),
    note: ($("[data-review-note]", item)?.value || "").slice(0, 2000),
    saved_at: new Date().toISOString(),
  };
  const status = $("[data-workflow-review-draft-status]", item);
  const clearButton = $("[data-workflow-review-draft-clear]", item);
  try {
    window.sessionStorage.setItem(key, JSON.stringify(payload));
    if (status) {
      status.textContent = "已在此分頁工作階段暫存；重新整理後重新開啟待審版本即可恢復，但尚未送到後端，也不是核准證據。";
    }
    if (clearButton) clearButton.hidden = false;
  } catch (_error) {
    if (status) {
      status.textContent = "瀏覽器無法保存本頁暫存；請先不要重新整理，已填內容仍可直接送出。";
    }
  }
}

function resetWorkflowReviewDraftItem(item, revision) {
  if (!item || !revision) return;
  clearWorkflowReviewDraft(revision);
  item.querySelectorAll("[data-approval-source], [data-approval-rule]")
    .forEach((checkbox) => {
      checkbox.checked = false;
    });
  const note = $("[data-review-note]", item);
  if (note) note.value = "";
  const status = $("[data-workflow-review-draft-status]", item);
  if (status) {
    status.textContent = "尚未建立本頁暫存；勾選或輸入後會自動保存在這個分頁工作階段。";
  }
  const clearButton = $("[data-workflow-review-draft-clear]", item);
  if (clearButton) clearButton.hidden = true;
  updateApprovalChecklist(item);
}

function workflowApplicabilityDraftKey(revision) {
  const reviewerId = state.admin?.id || "";
  const revisionId = revision?.id || "";
  const contentHash = revision?.content_hash || "";
  if (!reviewerId || !revisionId || !contentHash) return "";
  return `${workflowApplicabilityDraftStoragePrefix}:${reviewerId}:${revisionId}:${contentHash}`;
}

function loadWorkflowApplicabilityDraft(revision) {
  const key = workflowApplicabilityDraftKey(revision);
  if (!key) return null;
  try {
    const raw = window.sessionStorage.getItem(key);
    if (!raw) return null;
    const payload = JSON.parse(raw);
    if (
      !payload
      || payload.reviewer_id !== state.admin?.id
      || payload.revision_id !== revision.id
      || payload.content_hash !== revision.content_hash
    ) {
      window.sessionStorage.removeItem(key);
      return null;
    }
    const knownSourceUrls = new Set(sourceRows(revision.workflow || {}).map((row) => row.url));
    const validRoles = new Set(["", "home_university", "partner_university"]);
    const validAuthorities = new Set([
      "",
      "home_official_notice",
      "home_academic_unit",
      "nomination_notice",
      "partner_official",
    ]);
    const seenSourceUrls = new Set();
    const sourceDrafts = [];
    for (const row of Array.isArray(payload.source_rows) ? payload.source_rows.slice(0, 50) : []) {
      const sourceUrl = typeof row?.source_url === "string" ? row.source_url : "";
      if (!knownSourceUrls.has(sourceUrl) || seenSourceUrls.has(sourceUrl)) continue;
      seenSourceUrls.add(sourceUrl);
      const role = typeof row.role === "string" && validRoles.has(row.role) ? row.role : "";
      const authority = typeof row.authority === "string" && validAuthorities.has(row.authority)
        ? row.authority
        : "";
      sourceDrafts.push({
        source_url: sourceUrl,
        selected: row.selected === true,
        effective_academic_year: typeof row.effective_academic_year === "string"
          ? row.effective_academic_year.slice(0, 3)
          : "",
        application_round: typeof row.application_round === "string"
          ? row.application_round.slice(0, 80)
          : "",
        replacement_source_url: typeof row.replacement_source_url === "string"
          ? row.replacement_source_url.slice(0, 2000)
          : "",
        title: typeof row.title === "string" ? row.title.slice(0, 240) : "",
        role,
        authority,
      });
    }
    return {
      reviewer_id: state.admin.id,
      revision_id: revision.id,
      content_hash: revision.content_hash,
      academic_year: typeof payload.academic_year === "string" ? payload.academic_year.slice(0, 3) : "",
      application_round: typeof payload.application_round === "string" ? payload.application_round.slice(0, 80) : "",
      note: typeof payload.note === "string" ? payload.note.slice(0, 1000) : "",
      source_rows: sourceDrafts,
      saved_at: typeof payload.saved_at === "string" ? payload.saved_at : "",
    };
  } catch (_error) {
    try {
      window.sessionStorage.removeItem(key);
    } catch (_storageError) {
      // The correction form remains usable when browser storage is unavailable.
    }
    return null;
  }
}

function clearWorkflowApplicabilityDraft(revision) {
  const key = workflowApplicabilityDraftKey(revision);
  if (!key) return;
  try {
    window.sessionStorage.removeItem(key);
  } catch (_error) {
    // A local convenience draft must never block a backend correction action.
  }
}

function saveWorkflowApplicabilityDraftFromItem(item) {
  const revisionId = item?.dataset.revisionId || "";
  const revision = state.revisions.find((row) => row.id === revisionId);
  const editor = $(".applicability-editor", item);
  const key = workflowApplicabilityDraftKey(revision);
  if (!item || !revision || !editor || !key) return;
  const payload = {
    reviewer_id: state.admin.id,
    revision_id: revision.id,
    content_hash: revision.content_hash,
    academic_year: ($("[data-applicability-academic-year]", editor)?.value || "").slice(0, 3),
    application_round: ($("[data-applicability-application-round]", editor)?.value || "").slice(0, 80),
    note: ($("[data-applicability-note]", editor)?.value || "").slice(0, 1000),
    source_rows: [...editor.querySelectorAll("[data-applicability-source-row]")].map((row) => ({
      source_url: row.dataset.sourceUrl || "",
      selected: Boolean($("[data-applicability-source]", row)?.checked),
      effective_academic_year: ($("[data-source-academic-year]", row)?.value || "").slice(0, 3),
      application_round: ($("[data-source-application-round]", row)?.value || "").slice(0, 80),
      replacement_source_url: ($("[data-source-replacement-url]", row)?.value || "").slice(0, 2000),
      title: ($("[data-source-title]", row)?.value || "").slice(0, 240),
      role: $("[data-source-role]", row)?.value || "",
      authority: $("[data-source-authority]", row)?.value || "",
    })),
    saved_at: new Date().toISOString(),
  };
  const status = $("[data-workflow-applicability-draft-status]", editor);
  const clearButton = $("[data-workflow-applicability-draft-clear]", editor);
  try {
    window.sessionStorage.setItem(key, JSON.stringify(payload));
    if (status) {
      status.textContent = "已在此分頁工作階段暫存補正內容；重新整理可恢復，但尚未送到後端，也不是核准證據。";
    }
    if (clearButton) clearButton.hidden = false;
  } catch (_error) {
    if (status) {
      status.textContent = "瀏覽器無法保存補正草稿；請先不要重新整理，已填內容仍可直接儲存。";
    }
  }
}

function resetWorkflowApplicabilityDraftItem(item, revision) {
  const editor = $(".applicability-editor", item);
  if (!item || !revision || !editor) return;
  clearWorkflowApplicabilityDraft(revision);
  const workflow = revision.workflow || {};
  const sourceMap = new Map(sourceRows(workflow).map((source) => [source.url, source]));
  const academicYear = $("[data-applicability-academic-year]", editor);
  const applicationRound = $("[data-applicability-application-round]", editor);
  const note = $("[data-applicability-note]", editor);
  if (academicYear) academicYear.value = workflow.academic_year || "";
  if (applicationRound) applicationRound.value = workflow.application_round || "";
  if (note) note.value = "";
  editor.querySelectorAll("[data-applicability-source-row]").forEach((row) => {
    const source = sourceMap.get(row.dataset.sourceUrl || "");
    const metadata = source?.metadata || {};
    const checkbox = $("[data-applicability-source]", row);
    const sourceYear = $("[data-source-academic-year]", row);
    const sourceRound = $("[data-source-application-round]", row);
    const replacementUrl = $("[data-source-replacement-url]", row);
    const title = $("[data-source-title]", row);
    const role = $("[data-source-role]", row);
    const authority = $("[data-source-authority]", row);
    if (checkbox) checkbox.checked = false;
    if (sourceYear) sourceYear.value = metadata.effective_academic_year || "";
    if (sourceRound) sourceRound.value = metadata.application_round || "";
    if (replacementUrl) replacementUrl.value = "";
    if (title) title.value = metadata.title || "";
    if (role) role.value = metadata.role || "";
    if (authority) authority.value = metadata.authority || "";
  });
  const status = $("[data-workflow-applicability-draft-status]", editor);
  if (status) {
    status.textContent = "尚未建立補正草稿；輸入後只會保存在目前瀏覽器分頁，不會送到後端或形成核准證據。";
  }
  const clearButton = $("[data-workflow-applicability-draft-clear]", editor);
  if (clearButton) clearButton.hidden = true;
  updateApplicabilityEditorState(item);
}

function statusLabel(status) {
  return {
    pending_review: "待審",
    published: "已發布",
    rejected: "已退回",
    superseded: "已取代",
    legacy: "舊資料",
  }[status] || status || "未知";
}

function reviewStatusLabel(status) {
  return {
    verified: "適用範圍已核對",
    official_verified: "官方資料已核對",
    official_partial: "官方資料部分核對",
    needs_confirmation: "仍需人工確認",
    not_collected: "尚未收集",
  }[status] || status || "待確認";
}

function changeTypeLabel(changeType) {
  return {
    added: "新增",
    removed: "移除",
    changed: "調整",
  }[changeType] || "變更";
}

function renderComparisonValue(value) {
  if (value === null || value === undefined || value === "") {
    return '<span class="comparison-empty-value">未設定</span>';
  }
  return escapeHtml(value).replaceAll("\n", "<br>");
}

function renderChangeTable(changes, emptyMessage = "這一區沒有欄位變更。") {
  if (!changes?.length) return `<p class="comparison-empty">${escapeHtml(emptyMessage)}</p>`;
  return `
    <div class="comparison-table-wrap">
      <table class="comparison-table">
        <thead><tr><th>欄位</th><th>基準版本</th><th>候選版本</th></tr></thead>
        <tbody>${changes.map((row) => `
          <tr class="comparison-${escapeHtml(row.change_type)}">
            <th scope="row"><span class="change-kind change-${escapeHtml(row.change_type)}">${escapeHtml(changeTypeLabel(row.change_type))}</span>${escapeHtml(row.label)}</th>
            <td data-label="基準版本">${renderComparisonValue(row.before)}</td>
            <td data-label="候選版本">${renderComparisonValue(row.after)}</td>
          </tr>`).join("")}</tbody>
      </table>
    </div>`;
}

function renderComparison(revision) {
  const comparison = state.comparisons[revision.id];
  const loading = state.comparisonLoading[revision.id];
  const error = state.comparisonErrors[revision.id];
  if (loading) {
    return '<div class="comparison-loading" role="status">正在建立基準與候選版本對照…</div>';
  }
  if (error) {
    return `
      <div class="comparison-error" role="alert">
        <span>${escapeHtml(error)}</span>
        <button type="button" class="secondary" data-review-comparison>重新載入版本對照</button>
      </div>`;
  }
  if (!comparison) {
    return `
      <div class="comparison-gate">
        <div>
          <strong>逐欄版本對照尚未載入</strong>
          <p>${revision.base_version ? `將版本 ${escapeHtml(revision.base_version)} 與候選版本 ${escapeHtml(revision.version)} 逐欄比較。` : "這是第一版流程，沒有既有基準版本。"}</p>
        </div>
        <button type="button" class="secondary" data-review-comparison>載入版本對照</button>
      </div>`;
  }
  if (!comparison.has_base) {
    return `
      <section class="comparison-panel" aria-label="版本對照">
        <div class="comparison-first-version">
          <strong>第一版流程，沒有可比較的基準版本</strong>
          <p>請直接逐項核對下方完整流程與所有官方來源；這不代表內容已經完成查核。</p>
        </div>
      </section>`;
  }
  const workflowChanges = comparison.workflow_changes || [];
  const stepChanges = comparison.step_changes || [];
  const sourceChanges = comparison.source_changes || [];
  return `
    <section class="comparison-panel" aria-label="版本對照">
      <header class="comparison-header">
        <div>
          <p class="eyebrow">版本 ${escapeHtml(revision.base_version)} → ${escapeHtml(revision.version)}</p>
          <h5>基準與候選逐欄對照</h5>
        </div>
        <div class="comparison-counts" aria-label="變更統計">
          <span>流程欄位 <strong>${workflowChanges.length}</strong></span>
          <span>步驟 <strong>${stepChanges.length}</strong></span>
          <span>來源 <strong>${sourceChanges.length}</strong></span>
          <span>未變步驟 <strong>${escapeHtml(comparison.unchanged_step_count || 0)}</strong></span>
        </div>
      </header>
      <div class="comparison-group">
        <h6>流程層級欄位</h6>
        ${renderChangeTable(workflowChanges)}
      </div>
      <div class="comparison-group">
        <h6>步驟變更</h6>
        <div class="comparison-items">${stepChanges.map((step) => `
          <details>
            <summary><span><span class="change-kind change-${escapeHtml(step.change_type)}">${escapeHtml(changeTypeLabel(step.change_type))}</span>${escapeHtml(step.title)}</span><span>${escapeHtml(step.changes.length)} 個欄位</span></summary>
            ${renderChangeTable(step.changes, "這個步驟的整體新增或移除已記錄，但沒有額外欄位內容。")}
          </details>`).join("") || '<p class="comparison-empty">所有步驟內容都相同。</p>'}</div>
      </div>
      <div class="comparison-group">
        <h6>官方來源變更</h6>
        <div class="comparison-items">${sourceChanges.map((source) => `
          <details>
            <summary><span><span class="change-kind change-${escapeHtml(source.change_type)}">${escapeHtml(changeTypeLabel(source.change_type))}</span>${escapeHtml(source.title)}</span><span>來源</span></summary>
            <p class="comparison-source-url"><a href="${escapeHtml(safeExternalUrl(source.source_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.source_url)}</a></p>
            ${renderChangeTable(source.changes, "來源網址本身為新增或移除。")}
          </details>`).join("") || '<p class="comparison-empty">官方來源清單與來源屬性都相同。</p>'}</div>
      </div>
    </section>`;
}

function sourceRows(workflow) {
  const rows = [];
  const rowsByUrl = new Map();
  const add = (url, title, detail = "", metadata = null, reference = "") => {
    const normalized = String(url || "").trim();
    const key = normalized.toLocaleLowerCase();
    if (!normalized) return;
    const existing = rowsByUrl.get(key);
    if (existing) {
      if (reference && !existing.references.includes(reference)) existing.references.push(reference);
      if (!existing.metadata && metadata) {
        existing.metadata = metadata;
        existing.tracked = true;
        existing.metadataComplete = Boolean(
          String(metadata.title || "").trim() && metadata.role && metadata.authority
        );
        existing.title = metadata.title || existing.title;
        existing.detail = detail || existing.detail;
      }
      return;
    }
    const row = {
      url: normalized,
      title: metadata?.title || title || normalized,
      detail,
      secure: normalized.toLocaleLowerCase().startsWith("https://"),
      tracked: Boolean(metadata),
      metadataComplete: Boolean(metadata && String(metadata.title || "").trim() && metadata.role && metadata.authority),
      metadata,
      references: reference ? [reference] : [],
    };
    rowsByUrl.set(key, row);
    rows.push(row);
  };
  (workflow.sources || []).forEach((row) => add(
    row.source_url,
    row.title,
    [row.authority, row.effective_academic_year ? `${row.effective_academic_year} 學年度` : "", row.checked_at ? `查核 ${formatDate(row.checked_at)}` : ""].filter(Boolean).join(" · "),
    row,
    "流程適用範圍來源清單"
  ));
  (workflow.steps || []).forEach((step) => {
    const stepLabel = `第 ${step.order} 步「${step.title}」`;
    (step.source_urls || []).forEach((url) => add(
      url,
      `${step.phase}：${step.title}`,
      "",
      null,
      `${stepLabel}的內容與要求`
    ));
    add(
      step.deadline_source_url,
      `${step.phase}：期限來源`,
      "",
      null,
      `${stepLabel}的期限`
    );
    (step.official_form_urls || []).forEach((url) => add(
      url,
      `${step.phase}：官方表單`,
      "",
      null,
      `${stepLabel}的官方表單`
    ));
    (step.document_requirements || []).forEach((document) => {
      const documentLabel = `${stepLabel}的文件「${document.name}」`;
      (document.source_urls || []).forEach((url) => add(
        url,
        `文件：${document.name}`,
        "",
        null,
        `${documentLabel}規定`
      ));
      add(
        document.official_form_url,
        `文件表單：${document.name}`,
        "",
        null,
        `${documentLabel}官方表單`
      );
    });
  });
  return rows;
}

function sourceReplacementCandidatesFor(revisionId, sourceUrl) {
  const sourceKey = String(sourceUrl || "").trim().toLocaleLowerCase();
  return state.sourceReplacementCandidates.filter((candidate) => (
    candidate.revision_id === revisionId
    && candidate.current_url.toLocaleLowerCase() === sourceKey
  ));
}

function sourceReplacementCandidateStatusLabel(status) {
  return status === "strong_candidate" ? "強候選" : "條件候選";
}

function sourceReplacementTransportStatusLabel(status) {
  if (status === "verified_https") return "HTTPS 已驗證";
  if (status === "downgrades_to_http") return "會轉回 HTTP";
  return "傳輸尚未驗證";
}

function sourceResearchLeadRelationshipLabel(relationship) {
  if (relationship === "official_context") return "官方脈絡";
  if (relationship === "adjacent_program") return "相鄰方案";
  if (relationship === "application_system") return "一般申請系統";
  return "研究線索";
}

function renderSourceReplacementCandidate(candidate) {
  const supportingLinks = (candidate.supporting_urls || []).map((url) => `
    <li><a href="${escapeHtml(safeExternalUrl(url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a></li>`).join("");
  const researchLeads = (candidate.research_leads || []).map((lead) => `
    <li class="source-candidate-research-lead" data-eligible-as-replacement="false">
      <strong>${escapeHtml(lead.label)}</strong>
      <span>${escapeHtml(sourceResearchLeadRelationshipLabel(lead.relationship))} · HTTPS 已驗證 · 查核日 ${escapeHtml(lead.transport_checked_at)} · HTTP ${escapeHtml(lead.transport_http_status)}</span>
      <a href="${escapeHtml(safeExternalUrl(lead.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(lead.url)}</a>
      <small>不可直接替代：${escapeHtml(lead.reason_not_equivalent)}</small>
    </li>`).join("");
  const canPrefill = candidate.can_prefill === true;
  const transportDetail = [
    candidate.transport_checked_at ? `查核日 ${candidate.transport_checked_at}` : "",
    candidate.transport_http_status ? `HTTP ${candidate.transport_http_status}` : "",
    candidate.transport_final_url ? `最終網址 ${candidate.transport_final_url}` : "",
  ].filter(Boolean).join(" · ");
  const guard = canPrefill
    ? "不會自動勾選、儲存、核准或發布；請先親自開啟來源並完成上列人工檢查。"
    : "這個網址的 HTTPS 傳輸不安全或尚未驗證，系統禁止填入；候選只保留供人工追查，不得用於來源替換。";
  return `
    <aside class="source-replacement-candidate" data-candidate-status="${escapeHtml(candidate.candidate_status)}" data-transport-status="${escapeHtml(candidate.transport_status)}">
      <header>
        <strong>人工審核候選</strong>
        <span>${escapeHtml(sourceReplacementCandidateStatusLabel(candidate.candidate_status))}</span>
        <span class="transport-status">${escapeHtml(sourceReplacementTransportStatusLabel(candidate.transport_status))}</span>
        <small>${escapeHtml(candidate.batch_id)} · 研究日期 ${escapeHtml(candidate.checked_at)}</small>
      </header>
      <p><a href="${escapeHtml(safeExternalUrl(candidate.candidate_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(candidate.candidate_url)}</a></p>
      <p class="source-candidate-transport">${escapeHtml(transportDetail || "尚無傳輸查核紀錄")}</p>
      <div class="source-candidate-evidence">
        <section><h6>自動研究證據（不能當作核准）</h6><ul>${candidate.automated_evidence.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul></section>
        <section><h6>人工必查</h6><ul>${candidate.required_human_checks.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul></section>
        ${supportingLinks ? `<section><h6>輔助官方連結</h6><ul>${supportingLinks}</ul></section>` : ""}
        ${researchLeads ? `<section class="source-candidate-research-leads"><h6>安全研究線索（不可直接替代）</h6><ul>${researchLeads}</ul></section>` : ""}
      </div>
      <button type="button" class="secondary" data-apply-source-replacement-candidate data-can-prefill="${canPrefill ? "true" : "false"}" data-candidate-url="${escapeHtml(candidate.candidate_url)}" ${canPrefill ? "" : "disabled"}>${canPrefill ? "只填入待審欄位" : "傳輸安全未通過，禁止填入"}</button>
      <small class="source-candidate-guard">${escapeHtml(guard)}</small>
    </aside>`;
}

function renderSourceReferences(source) {
  const references = source.references || [];
  if (!references.length) return "";
  return `
    <div class="source-reference-contexts">
      <strong>此網址支援的規定（${escapeHtml(references.length)}）</strong>
      <ul>${references.map((reference) => `<li>${escapeHtml(reference)}</li>`).join("")}</ul>
    </div>`;
}

function workflowRuleRows(workflow) {
  const sourcesByUrl = new Map(
    sourceRows(workflow).map((row) => [row.url.toLocaleLowerCase(), row])
  );
  const sourcesFor = (urls) => {
    const seen = new Set();
    return (urls || []).map((url) => String(url || "").trim()).filter((url) => {
      const key = url.toLocaleLowerCase();
      if (!url || seen.has(key)) return false;
      seen.add(key);
      return true;
    }).map((url) => sourcesByUrl.get(url.toLocaleLowerCase()) || {
      url,
      title: url,
      detail: "",
      secure: url.toLocaleLowerCase().startsWith("https://"),
    });
  };
  const rows = [{
    key: "workflow:applicability",
    type: "workflow",
    title: "流程適用學年度、梯次與適用狀態",
    detail: `${workflow.academic_year || "學年度待確認"} · ${workflow.application_round || (workflow.effective_application_rounds || []).join("、") || "梯次待確認"}`,
    sources: sourcesFor((workflow.sources || []).map((source) => source.source_url)),
  }];
  (workflow.steps || []).forEach((step, stepIndex) => {
    rows.push({
      key: `step:${stepIndex}`,
      type: "step",
      title: `${step.order}. ${step.phase} · ${step.title}`,
      detail: [step.responsible_unit || step.responsible_party, step.timing, step.submission?.method].filter(Boolean).join(" · "),
      sources: sourcesFor([...(step.source_urls || []), step.deadline_source_url, ...(step.official_form_urls || [])]),
    });
    (step.document_requirements || []).forEach((document, documentIndex) => {
      rows.push({
        key: `document:${stepIndex}:${documentIndex}`,
        type: "document",
        title: `文件：${document.name}`,
        detail: [`第 ${step.order} 步`, document.copies ? `${document.copies} 份` : "份數待確認", document.copy_type].filter(Boolean).join(" · "),
        sources: sourcesFor([...(document.source_urls || []), document.official_form_url]),
      });
    });
  });
  return rows;
}

function renderApplicabilityEditor(revision) {
  if (revision.status !== "pending_review") return "";
  const workflow = revision.workflow || {};
  const sources = sourceRows(workflow);
  const draft = loadWorkflowApplicabilityDraft(revision);
  const draftSourceRows = new Map((draft?.source_rows || []).map((row) => [row.source_url, row]));
  const editRows = (revision.edit_history || []).map((edit) => `
    <li><strong>${escapeHtml(formatDate(edit.edited_at))}</strong> · ${escapeHtml(edit.note)} <small>（${escapeHtml(edit.edited_by)}）</small></li>`).join("");
  const sourceFields = sources.map((source, index) => {
    const checkboxId = `source-applicability-${revision.id}-${index}`;
    const yearId = `source-year-${revision.id}-${index}`;
    const roundId = `source-round-${revision.id}-${index}`;
    const replacementId = `source-replacement-${revision.id}-${index}`;
    const titleId = `source-title-${revision.id}-${index}`;
    const roleId = `source-role-${revision.id}-${index}`;
    const authorityId = `source-authority-${revision.id}-${index}`;
    const secure = source.secure;
    const metadata = source.metadata || {};
    const draftSource = draftSourceRows.get(source.url);
    const needsMetadata = !source.metadataComplete;
    const replacementCandidates = sourceReplacementCandidatesFor(
      revision.id,
      source.url
    );
    return `
      <fieldset class="applicability-source" data-applicability-source-row data-source-url="${escapeHtml(source.url)}" data-source-tracked="${source.tracked}" data-source-metadata-complete="${source.metadataComplete}">
        <legend>
          <label for="${escapeHtml(checkboxId)}">
            <input id="${escapeHtml(checkboxId)}" type="checkbox" data-applicability-source ${draftSource?.selected ? "checked" : ""}>
            <span>${needsMetadata ? "這次已逐頁確認並補齊來源證據資料" : "這次已逐頁確認此來源"}</span>
          </label>
        </legend>
        <a href="${escapeHtml(safeExternalUrl(source.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title || source.url)}</a>
        ${renderSourceReferences(source)}
        <p class="applicability-source-progress" data-applicability-source-progress>本次未選取，不會儲存這列欄位。</p>
        ${needsMetadata ? '<p class="evidence-error applicability-source-metadata">這個來源尚未完整保存名稱、角色、權威層級與查核證據；補齊前不能核准。</p>' : ""}
        ${secure ? "" : '<p class="evidence-error applicability-source-security">目前網址不是 HTTPS；本次必須填入已核實的安全替代網址。</p>'}
        ${replacementCandidates.map(renderSourceReplacementCandidate).join("")}
        <div class="applicability-source-fields">
          ${needsMetadata ? `
            <label for="${escapeHtml(titleId)}"><span>來源名稱</span><input id="${escapeHtml(titleId)}" data-source-title maxlength="240" value="${escapeHtml(draftSource ? draftSource.title : (metadata.title || ""))}" placeholder="請依頁面正式標題填寫"></label>
            <label for="${escapeHtml(roleId)}"><span>來源角色</span><select id="${escapeHtml(roleId)}" data-source-role><option value="">請選擇</option><option value="home_university" ${(draftSource ? draftSource.role : metadata.role) === "home_university" ? "selected" : ""}>本校來源</option><option value="partner_university" ${(draftSource ? draftSource.role : metadata.role) === "partner_university" ? "selected" : ""}>合作校來源</option></select></label>
            <label for="${escapeHtml(authorityId)}"><span>權威層級</span><select id="${escapeHtml(authorityId)}" data-source-authority><option value="">請選擇</option><option value="home_official_notice" ${(draftSource ? draftSource.authority : metadata.authority) === "home_official_notice" ? "selected" : ""}>本校正式公告</option><option value="home_academic_unit" ${(draftSource ? draftSource.authority : metadata.authority) === "home_academic_unit" ? "selected" : ""}>本校院系公告</option><option value="nomination_notice" ${(draftSource ? draftSource.authority : metadata.authority) === "nomination_notice" ? "selected" : ""}>提名通知</option><option value="partner_official" ${(draftSource ? draftSource.authority : metadata.authority) === "partner_official" ? "selected" : ""}>合作校官方頁</option></select></label>` : ""}
          <label for="${escapeHtml(yearId)}"><span>來源適用學年度</span><input id="${escapeHtml(yearId)}" data-source-academic-year inputmode="numeric" pattern="[0-9]{3}" maxlength="3" value="${escapeHtml(draftSource ? draftSource.effective_academic_year : (metadata.effective_academic_year || ""))}" placeholder="例如 115"></label>
          <label for="${escapeHtml(roundId)}"><span>來源適用梯次（選填）</span><input id="${escapeHtml(roundId)}" data-source-application-round maxlength="80" value="${escapeHtml(draftSource ? draftSource.application_round : (metadata.application_round || ""))}" placeholder="例如 第 2 學期"></label>
          ${source.tracked || !secure ? `<label for="${escapeHtml(replacementId)}" class="source-replacement-field"><span>安全替代網址（選填）</span><input id="${escapeHtml(replacementId)}" data-source-replacement-url type="url" maxlength="2000" value="${escapeHtml(draftSource?.replacement_source_url || "")}" placeholder="https://學校官方頁面" aria-describedby="${escapeHtml(replacementId)}-help"><small id="${escapeHtml(replacementId)}-help">只有親自確認相同官方內容的新網址後才填；儲存時會同步更新步驟、期限、表單與文件引用。</small></label>` : ""}
        </div>
      </fieldset>`;
  }).join("");
  return `
    <details class="applicability-editor" ${draft ? "open" : ""}>
      <summary>補正適用學年度與來源證據</summary>
      <div class="applicability-editor-body">
        <p class="applicability-warning">只勾選你已親自開啟並確認適用年度的官方來源。非 HTTPS 或失效網址必須先以已核實的學校官方 HTTPS 頁替換；系統會同步所有規定引用，但不會自動猜網址或把流程年度套到所有來源。任何內容修正都會清除既有核准，要求兩人重新審查。</p>
        <div class="applicability-main-fields">
          <label><span>流程適用學年度</span><input data-applicability-academic-year inputmode="numeric" pattern="[0-9]{3}" maxlength="3" value="${escapeHtml(draft ? draft.academic_year : (workflow.academic_year || ""))}" placeholder="例如 115" required></label>
          <label><span>流程申請梯次（選填）</span><input data-applicability-application-round maxlength="80" value="${escapeHtml(draft ? draft.application_round : (workflow.application_round || ""))}" placeholder="未填時保留現值"></label>
        </div>
        <div class="applicability-editor-progress is-blocked" data-applicability-progress role="status" aria-live="polite">
          <span data-applicability-progress-message>正在檢查本次補正內容…</span>
          <button class="secondary" type="button" data-applicability-next-issue hidden>前往下一個缺少欄位</button>
        </div>
        <div class="applicability-sources">
          <h5>官方來源逐頁確認</h5>
          ${sourceFields || '<p class="review-error">沒有官方來源，不能補正適用範圍。</p>'}
        </div>
        <label><span>本次修正說明</span><textarea data-applicability-note maxlength="1000" placeholder="寫明你核對的公告、頁面內容與仍待確認的範圍。">${escapeHtml(draft?.note || "")}</textarea></label>
        <div class="workflow-applicability-draft">
          <p data-workflow-applicability-draft-status>${draft ? "已從此分頁工作階段恢復補正草稿；尚未送到後端，也不是核准證據。" : "尚未建立補正草稿；輸入後只會保存在目前瀏覽器分頁，不會送到後端或形成核准證據。"}</p>
          <button class="secondary" type="button" data-workflow-applicability-draft-clear ${draft ? "" : "hidden"}>清除補正草稿</button>
        </div>
        <button type="button" data-review-applicability-save disabled>儲存待審修正</button>
        ${editRows ? `<div class="applicability-history"><h5>候選修正紀錄</h5><ol>${editRows}</ol></div>` : ""}
      </div>
    </details>`;
}

function updateApplicabilityEditorState(item) {
  if (!item) return;
  const revision = state.revisions.find((row) => row.id === item.dataset.revisionId);
  const editor = $(".applicability-editor", item);
  const progress = $("[data-applicability-progress]", item);
  const progressMessage = $("[data-applicability-progress-message]", item);
  const nextIssueButton = $("[data-applicability-next-issue]", item);
  const saveButton = $("[data-review-applicability-save]", item);
  if (!revision || !editor || !progress || !progressMessage || !nextIssueButton || !saveButton) return;

  const workflow = revision.workflow || {};
  const academicYearInput = $("[data-applicability-academic-year]", editor);
  const applicationRoundInput = $("[data-applicability-application-round]", editor);
  const noteInput = $("[data-applicability-note]", editor);
  const academicYear = academicYearInput?.value.trim() || "";
  const applicationRound = applicationRoundInput?.value.trim() || "";
  const note = noteInput?.value.trim() || "";
  const sourceRows = [...editor.querySelectorAll("[data-applicability-source-row]")];
  const selectedRows = sourceRows.filter((row) => $("[data-applicability-source]", row)?.checked);
  const prefix = `已選擇 ${selectedRows.length} / ${sourceRows.length} 個來源。`;
  let firstSourceIssue = null;
  editor.querySelectorAll("[data-applicability-current-issue]").forEach((node) => {
    node.removeAttribute("data-applicability-current-issue");
  });

  sourceRows.forEach((row) => {
    const selected = Boolean($("[data-applicability-source]", row)?.checked);
    const rowProgress = $("[data-applicability-source-progress]", row);
    row.classList.toggle("is-selected", selected);
    row.classList.remove("is-ready", "is-blocked");
    if (!rowProgress) return;
    if (!selected) {
      rowProgress.textContent = "本次未選取，不會儲存這列欄位。";
      return;
    }

    const sourceYearInput = $("[data-source-academic-year]", row);
    const sourceYear = sourceYearInput?.value.trim() || "";
    const currentSourceUrl = row.dataset.sourceUrl || "";
    const sourceMetadataComplete = row.dataset.sourceMetadataComplete === "true";
    const replacementInput = $("[data-source-replacement-url]", row);
    const replacementSourceUrl = replacementInput?.value.trim() || "";
    let issue = null;
    if (!/^\d{3}$/.test(sourceYear)) {
      issue = {
        message: "缺少 3 位數來源適用學年度。",
        global: "每個已勾選來源都須填寫 3 位數適用學年度。",
        target: sourceYearInput,
      };
    } else if (replacementSourceUrl && !replacementSourceUrl.toLocaleLowerCase().startsWith("https://")) {
      issue = {
        message: "安全替代網址必須使用 HTTPS。",
        global: "安全替代網址必須使用 HTTPS。",
        target: replacementInput,
      };
    } else if (!currentSourceUrl.toLocaleLowerCase().startsWith("https://") && !replacementSourceUrl) {
      issue = {
        message: "缺少已核實的 HTTPS 替代網址。",
        global: "已勾選的非 HTTPS 來源須填入核實過的安全替代網址。",
        target: replacementInput,
      };
    } else if (!sourceMetadataComplete) {
      const sourceTitleInput = $("[data-source-title]", row);
      const sourceRoleInput = $("[data-source-role]", row);
      const sourceAuthorityInput = $("[data-source-authority]", row);
      if (!sourceTitleInput?.value.trim()) {
        issue = {
          message: "缺少來源名稱。",
          global: "已勾選且證據資料不完整的來源，須補齊名稱、角色與權威層級。",
          target: sourceTitleInput,
        };
      } else if (!sourceRoleInput?.value) {
        issue = {
          message: "缺少來源角色。",
          global: "已勾選且證據資料不完整的來源，須補齊名稱、角色與權威層級。",
          target: sourceRoleInput,
        };
      } else if (!sourceAuthorityInput?.value) {
        issue = {
          message: "缺少權威層級。",
          global: "已勾選且證據資料不完整的來源，須補齊名稱、角色與權威層級。",
          target: sourceAuthorityInput,
        };
      }
    }

    if (issue) {
      row.classList.add("is-blocked");
      rowProgress.textContent = `本次補正尚未完成：${issue.message}`;
      if (!firstSourceIssue) firstSourceIssue = issue;
    } else {
      row.classList.add("is-ready");
      rowProgress.textContent = "本次補正欄位完成；儲存時只會更新這個來源。";
    }
  });

  let nextRequirement = "";
  let nextIssueTarget = null;

  if (!/^\d{3}$/.test(academicYear)) {
    nextRequirement = "流程適用學年度須為 3 位數民國學年度，例如 115。";
    nextIssueTarget = academicYearInput;
  } else if (!note) {
    nextRequirement = "請填寫本次修正說明。";
    nextIssueTarget = noteInput;
  } else if (firstSourceIssue) {
    nextRequirement = firstSourceIssue.global;
    nextIssueTarget = firstSourceIssue.target;
  }

  const workflowYearChanged = academicYear !== String(workflow.academic_year || "");
  const workflowRoundChanged = Boolean(applicationRound) && applicationRound !== String(workflow.application_round || "");
  const hasMeaningfulChange = workflowYearChanged || workflowRoundChanged || selectedRows.length > 0;
  if (!nextRequirement && !hasMeaningfulChange) {
    nextRequirement = "請修改流程適用學年度／梯次，或勾選至少一個已逐頁確認的來源。";
    nextIssueTarget = academicYearInput;
  }

  const ready = !nextRequirement;
  progress.classList.toggle("is-ready", ready);
  progress.classList.toggle("is-blocked", !ready);
  progressMessage.textContent = ready
    ? `${prefix} 可儲存本次逐頁補正；未勾選來源保持不變。`
    : `${prefix} ${nextRequirement} 未勾選來源保持不變。`;
  if (nextIssueTarget && !ready) {
    nextIssueTarget.setAttribute("data-applicability-current-issue", "");
    nextIssueButton.hidden = false;
  } else {
    nextIssueButton.hidden = true;
  }
  saveButton.disabled = !ready;
}

function focusNextApplicabilityIssue(button) {
  const item = button.closest("[data-revision-id]");
  const editor = $(".applicability-editor", item);
  if (!item || !editor) return;
  updateApplicabilityEditorState(item);
  const target = $("[data-applicability-current-issue]", editor);
  if (!target) {
    announce("目前補正欄位已完成，可以再次確認後儲存。", "success");
    return;
  }
  editor.open = true;
  target.scrollIntoView({ block: "center" });
  target.focus({ preventScroll: true });
  announce("已前往下一個尚未完成的補正欄位。");
}

function renderStep(step) {
  const documents = (step.document_requirements || []).map((row) => row.name).filter(Boolean);
  const sources = (step.source_urls || []).filter(Boolean);
  return `
    <details>
      <summary><span>${escapeHtml(step.order)}. ${escapeHtml(step.phase)}｜${escapeHtml(step.title)}</span><span>${escapeHtml(reviewStatusLabel(step.support_status))}</span></summary>
      <div class="workflow-step-content">
        <p><strong>負責：</strong>${escapeHtml(step.responsible_unit || step.responsible_party || "待確認")}</p>
        <p><strong>時程：</strong>${escapeHtml(step.timing || "待確認")}</p>
        <p>${escapeHtml(step.summary || "尚無摘要")}</p>
        <p><strong>文件：</strong>${escapeHtml(documents.join("、") || "沒有列出文件")}</p>
        <p><strong>來源：</strong>${sources.length ? sources.map((url) => `<a href="${escapeHtml(safeExternalUrl(url))}" target="_blank" rel="noopener noreferrer">官方連結</a>`).join("、") : "待補"}</p>
      </div>
    </details>`;
}

function workflowReviewCorrectionState(revision) {
  const workflow = revision.workflow || {};
  const sources = sourceRows(workflow);
  const rules = workflowRuleRows(workflow);
  const insecureSourceCount = sources.filter((row) => !row.secure).length;
  const rulesWithoutSources = rules.filter((row) => !(row.sources || []).length);
  const rulesWithInsecureSources = rules.filter((row) => (
    row.sources || []
  ).some((source) => !source.secure));
  const academicYear = String(workflow.academic_year || "").trim();
  const effectiveRounds = [
    workflow.application_round,
    ...(workflow.effective_application_rounds || []),
  ].filter(Boolean);
  const sourceMetadataGapCount = sources.filter((row) => !row.metadataComplete).length;
  const sourceYearGapCount = sources.filter((row) => (
    row.tracked
    && (
      !row.metadata?.effective_academic_year
      || (academicYear && row.metadata.effective_academic_year !== academicYear)
    )
  )).length;
  const reviewTimestampGapCount = (workflow.last_checked ? 0 : 1)
    + sources.filter((row) => row.tracked && !row.metadata?.checked_at).length
    + (workflow.steps || []).filter((step) => !step.checked_at).length;
  const applicabilityIssues = [
    academicYear ? "" : "流程適用學年度待確認",
    effectiveRounds.length ? "" : "有效梯次待確認",
    workflow.applicability_status === "verified" ? "" : "適用狀態待確認",
    sourceMetadataGapCount ? `${sourceMetadataGapCount} 個來源缺少證據資料` : "",
    sourceYearGapCount ? `${sourceYearGapCount} 個來源年度缺漏或不一致` : "",
  ].filter(Boolean);
  const correctionIssues = [
    sources.length ? "" : "沒有可逐頁查核的官方來源",
    insecureSourceCount ? `${insecureSourceCount} 個官方來源不是 HTTPS` : "",
    rulesWithoutSources.length
      ? `${rulesWithoutSources.length} 個關鍵規定缺少官方來源`
      : "",
    ...applicabilityIssues,
  ].filter(Boolean);
  return {
    workflow,
    sources,
    rules,
    insecureSourceCount,
    rulesWithoutSources,
    rulesWithInsecureSources,
    hasEvidenceIssues: Boolean(
      insecureSourceCount
      || rulesWithoutSources.length
      || rulesWithInsecureSources.length
    ),
    academicYear,
    effectiveRounds,
    sourceMetadataGapCount,
    sourceYearGapCount,
    reviewTimestampGapCount,
    applicabilityIssues,
    hasReviewMetadataIssues: applicabilityIssues.length > 0,
    sourceYearReadyCount: sources.filter((row) => (
      row.tracked && row.metadata?.effective_academic_year === academicYear
    )).length,
    correctionIssues,
    correctionReady: correctionIssues.length === 0,
  };
}

function renderRevision(revision) {
  const correctionState = workflowReviewCorrectionState(revision);
  const {
    workflow,
    sources,
    rules,
    insecureSourceCount,
    rulesWithoutSources,
    rulesWithInsecureSources,
    hasEvidenceIssues,
    academicYear,
    sourceMetadataGapCount,
    sourceYearGapCount,
    reviewTimestampGapCount,
    applicabilityIssues,
    hasReviewMetadataIssues,
    sourceYearReadyCount,
    correctionIssues,
    correctionReady,
  } = correctionState;
  const progress = approvalProgress(revision);
  const approvedByCurrent = currentAdminApproved(revision);
  const comparisonReady = !revision.base_version || Boolean(state.comparisons[revision.id]);
  const pending = revision.status === "pending_review";
  const canContinueBatchTodo = Boolean(
    pending
    && !approvedByCurrent
    && !progress.ready
    && state.reviewBatchId
    && !state.workflowDeepLinkStale
    && state.reviewBatchWorkflowKeys.includes(revision.workflow_key)
  );
  const draft = pending ? loadWorkflowReviewDraft(revision) : null;
  const draftSourceUrls = new Set(draft?.reviewed_source_urls || []);
  const draftRuleKeys = new Set(draft?.reviewed_rule_keys || []);
  const width = Math.min(100, Math.round((progress.count / progress.required) * 100));
  const approvalRows = (revision.review_approvals || []).map((approval, index) => `
    <div class="approval-row">
      <strong>審查者 ${index + 1}${approval.reviewer_id === state.admin?.id ? "（你）" : ""}</strong>
      <span>${escapeHtml(approval.note)}</span>
      <small>${escapeHtml(formatDate(approval.reviewed_at))} · 已逐頁確認 ${escapeHtml((approval.reviewed_source_urls || []).length)} 個來源 · 已逐項確認 ${escapeHtml((approval.reviewed_rule_keys || []).length)} 個關鍵規定 · 版本 ${escapeHtml((approval.reviewed_content_hash || "舊格式").slice(0, 8))}</small>
    </div>`).join("") || '<div class="approval-empty">尚未有人核准；請先完成官方來源查核。</div>';
  const sourceChecklistRows = sources.map((row, index) => {
    const checkboxId = `approval-source-${revision.id}-${index}`;
    const showCheckbox = pending && !approvedByCurrent && !progress.ready;
    return `<li class="${row.secure && row.metadataComplete ? "" : "source-insecure"}">
      <a href="${escapeHtml(safeExternalUrl(row.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(row.title)}</a>
      ${row.detail ? `<small>${escapeHtml(row.detail)}</small>` : ""}
      ${renderSourceReferences(row)}
      ${row.metadataComplete ? "" : '<small class="evidence-error">此引用尚未完整建立來源證據資料，請先在適用範圍編輯器補齊。</small>'}
      ${row.secure ? "" : '<small class="evidence-error">此來源不是 HTTPS，修正前不能核准。</small>'}
      ${showCheckbox ? `<div class="source-attestation">
        <input id="${escapeHtml(checkboxId)}" type="checkbox" data-approval-source data-source-url="${escapeHtml(row.url)}" ${draftSourceUrls.has(row.url) ? "checked" : ""} ${comparisonReady && row.secure && row.metadataComplete && !hasReviewMetadataIssues ? "" : "disabled"}>
        <label for="${escapeHtml(checkboxId)}">${row.secure && row.metadataComplete ? "我已親自開啟並逐頁確認這個來源" : "來源需先補齊證據資料並使用可安全查核的 HTTPS 網址"}</label>
      </div>` : ""}
    </li>`;
  }).join("");
  const ruleChecklistRows = rules.map((row, index) => {
    const checkboxId = `approval-rule-${revision.id}-${index}`;
    const showCheckbox = pending && !approvedByCurrent && !progress.ready;
    const ruleSources = row.sources || [];
    const evidenceReady = ruleSources.length && ruleSources.every((source) => source.secure && source.metadataComplete) && !hasReviewMetadataIssues;
    const ruleSourceLinks = ruleSources.length
      ? ruleSources.map((source) => `<a href="${escapeHtml(safeExternalUrl(source.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)}</a>${source.metadataComplete ? "" : '<span class="source-security-warning">缺來源證據</span>'}${source.secure ? "" : '<span class="source-security-warning">非 HTTPS</span>'}`).join("、")
      : '<span class="evidence-error">缺少對應官方來源</span>';
    return `<li class="rule-${escapeHtml(row.type)}">
      <strong>${escapeHtml(row.title)}</strong>
      ${row.detail ? `<small>${escapeHtml(row.detail)}</small>` : ""}
      <div class="rule-source-links"><span>對應來源：</span>${ruleSourceLinks}</div>
      ${showCheckbox ? `<div class="source-attestation">
        <input id="${escapeHtml(checkboxId)}" type="checkbox" data-approval-rule data-rule-key="${escapeHtml(row.key)}" ${draftRuleKeys.has(row.key) ? "checked" : ""} ${comparisonReady && evidenceReady ? "" : "disabled"}>
        <label for="${escapeHtml(checkboxId)}">${evidenceReady ? "我已逐項核對這條規定及其官方來源" : "補齊安全的對應官方來源後才能核對"}</label>
      </div>` : ""}
    </li>`;
  }).join("");
  const approvalStaticDisabled = approvedByCurrent || progress.ready || !sources.length || !rules.length || !comparisonReady || hasEvidenceIssues || hasReviewMetadataIssues;
  const noteId = `review-note-${revision.id}`;
  return `
    <article class="review-item" data-revision-id="${escapeHtml(revision.id)}" tabindex="-1">
      <header class="review-item-header">
        <div>
          <div class="review-pills">
            <span class="review-pill ${revision.status === "published" ? "success" : "warning"}">${escapeHtml(statusLabel(revision.status))}</span>
            <span class="review-pill">版本 ${escapeHtml(revision.version)}</span>
            <span class="review-pill">${escapeHtml(workflow.home_university || "母校待確認")}</span>
          </div>
          <h3>${escapeHtml(workflow.school_name || revision.workflow_key)}</h3>
          <p>${escapeHtml(workflow.program_type || "交換申請流程")} · 偵測 ${escapeHtml(formatDate(revision.detected_at))}</p>
        </div>
        <div class="approval-progress">
          <strong>${progress.count} / ${progress.required} 位核准</strong>
          <span>${progress.ready ? "已達發布門檻" : `還需 ${progress.required - progress.count} 位不同審查者`}</span>
          <div class="progress-track" aria-label="核准進度 ${progress.count} / ${progress.required}"><i style="width:${width}%"></i></div>
        </div>
      </header>
      ${pending ? `<section class="review-correction-summary${correctionReady ? " is-ready" : ""}" role="status">
        <div>
          <strong>${correctionReady ? "資料門檻完成，可開始真人核對" : `先補資料才能核准（${correctionIssues.length} 項）`}</strong>
          ${correctionReady
            ? "<p>仍須載入版本對照、逐頁開啟全部官方來源並逐項核對規定；這不代表已核准或可發布。</p>"
            : `<ul>${correctionIssues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("")}</ul>`}
        </div>
        ${correctionReady ? "" : '<button type="button" data-review-jump-corrections>前往資料補正</button>'}
      </section>` : ""}
      <div class="review-item-body">
        <div class="review-detail">
          <section class="review-section">
            <h4>適用範圍</h4>
            <dl class="review-meta">
              <div><dt>學年度</dt><dd>${escapeHtml(workflow.academic_year || "待確認")}</dd></div>
              <div><dt>梯次</dt><dd>${escapeHtml(workflow.application_round || (workflow.effective_application_rounds || []).join("、") || "待確認")}</dd></div>
              <div><dt>適用狀態</dt><dd>${escapeHtml(reviewStatusLabel(workflow.applicability_status))}</dd></div>
              <div><dt>來源年度</dt><dd>${escapeHtml(sourceYearReadyCount)} / ${escapeHtml(sources.length)}</dd></div>
              <div><dt>資料涵蓋</dt><dd>${escapeHtml(reviewStatusLabel(workflow.coverage_status))}</dd></div>
              <div><dt>步驟數</dt><dd>${escapeHtml((workflow.steps || []).length)}</dd></div>
            </dl>
          </section>
          <section class="review-section">
            <h4>偵測到的變更</h4>
            <ul>${(revision.change_summary || []).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || "<li>沒有變更摘要；必須人工比較完整內容。</li>"}</ul>
          </section>
          <section class="review-section">
            <h4>基準版本與候選版本</h4>
            ${renderComparison(revision)}
          </section>
          <section class="review-section">
            <h4>官方來源（${sources.length}）</h4>
            ${reviewTimestampGapCount ? `<p class="source-attestation-status">目前有 ${escapeHtml(reviewTimestampGapCount)} 個流程／來源／步驟缺少查核日期；完成本次逐來源、逐規定核准時會以審查時間補上。</p>` : ""}
            <ul class="source-list approval-source-list">${sourceChecklistRows || "<li>沒有官方來源，不能核准。</li>"}</ul>
            ${pending && !approvedByCurrent && !progress.ready && sources.length ? `<p class="source-attestation-status" data-approval-source-status>已逐頁確認 0 / ${sources.length} 個來源；尚有 ${sources.length} 個未確認。</p>` : ""}
          </section>
          <section class="review-section">
            <h4>關鍵規定（${rules.length}）</h4>
            <p class="rule-attestation-intro">流程適用範圍、每個步驟與每份文件都必須逐項核對；每列直接列出對應來源，勾選代表你已開啟並對照該頁。</p>
            ${hasEvidenceIssues ? `<p class="evidence-error rule-source-blocker">發布阻擋：${rulesWithoutSources.length} 個關鍵規定缺少來源，${rulesWithInsecureSources.length} 個關鍵規定含非 HTTPS 來源；請先修正候選資料。</p>` : ""}
            ${hasReviewMetadataIssues ? `<p class="evidence-error review-metadata-blocker">發布阻擋：${escapeHtml(applicabilityIssues.join("；"))}。請先完成適用年度與查核證據。</p>` : ""}
            <ul class="source-list approval-source-list approval-rule-list">${ruleChecklistRows}</ul>
            ${pending && !approvedByCurrent && !progress.ready && rules.length ? `<p class="source-attestation-status" data-approval-rule-status>已逐項確認 0 / ${rules.length} 個關鍵規定；尚有 ${rules.length} 個未確認。</p>` : ""}
          </section>
          <section class="review-section">
            <h4>完整流程步驟</h4>
            <div class="workflow-steps">${(workflow.steps || []).map(renderStep).join("") || "尚無流程步驟"}</div>
          </section>
        </div>
        <aside class="review-actions" aria-label="審查操作">
          ${renderApplicabilityEditor(revision)}
          <h4>獨立核准紀錄</h4>
          <div class="approval-list">${approvalRows}</div>
          ${pending ? `
            ${!approvedByCurrent && !progress.ready ? `<div class="workflow-approval-completion is-blocked" data-approval-completion aria-live="polite">
              <div>
                <strong data-approval-completion-message>正在計算本頁獨立核准進度…</strong>
                <span data-approval-completion-sources>官方來源 0／${escapeHtml(sources.length)}</span>
                <span data-approval-completion-rules>關鍵規定 0／${escapeHtml(rules.length)}</span>
                <span data-approval-completion-note>查核說明未填寫</span>
              </div>
              <button class="secondary" type="button" data-approval-next-issue>前往下一個未完成核准項目</button>
            </div>` : ""}
            <label for="${escapeHtml(noteId)}">
              <span>本次查核說明</span>
              <textarea id="${escapeHtml(noteId)}" data-review-note minlength="1" maxlength="2000" placeholder="請寫明核對的官方來源、學年度、梯次、文件、期限與仍有疑問之處。">${escapeHtml(draft?.note || "")}</textarea>
            </label>
            <div class="workflow-review-draft">
              <p data-workflow-review-draft-status>${draft ? "已從此分頁工作階段恢復暫存；尚未送到後端，也不是核准證據。" : "尚未建立本頁暫存；勾選或輸入後會自動保存在這個分頁工作階段。"}</p>
              <button class="secondary" type="button" data-workflow-review-draft-clear ${draft ? "" : "hidden"}>清除本頁暫存</button>
            </div>
            <div class="action-buttons">
              <button type="button" data-review-action="approve" data-approval-static-disabled="${approvalStaticDisabled}" disabled>${approvedByCurrent ? "你已核准" : (!comparisonReady ? "先載入版本對照" : "核准此版本")}</button>
              ${canContinueBatchTodo ? `<button class="secondary" type="button" data-review-action="approve" data-approval-submit-next data-approval-static-disabled="${approvalStaticDisabled}" disabled>核准並前往下一筆我的待辦</button>` : ""}
              <button type="button" class="danger" data-review-action="reject">退回修正</button>
              <button type="button" class="publish" data-review-action="publish" ${!progress.ready || !approvedByCurrent ? "disabled" : ""}>正式發布</button>
            </div>
            <p class="action-note">有基準版本時，核准前請先載入並逐欄核對版本差異；每位審查者還必須獨立開啟並勾選全部官方來源，以及逐項核對流程適用範圍、步驟與文件。核准會綁定目前內容版本、來源清單與關鍵規定清單。正式發布只開放給已參與核准、且已達 ${progress.required} 人門檻的審查者。</p>` : `
            <p class="action-note">此版本已結束待審狀態，操作按鈕已鎖定。</p>`}
        </aside>
      </div>
    </article>`;
}

function updateApprovalChecklist(item) {
  const sourceCheckboxes = [...item.querySelectorAll("[data-approval-source]")];
  const ruleCheckboxes = [...item.querySelectorAll("[data-approval-rule]")];
  const checkedSourceCount = sourceCheckboxes.filter((checkbox) => checkbox.checked).length;
  const checkedRuleCount = ruleCheckboxes.filter((checkbox) => checkbox.checked).length;
  const sourceStatus = $("[data-approval-source-status]", item);
  const ruleStatus = $("[data-approval-rule-status]", item);
  const noteField = $("[data-review-note]", item);
  const noteReady = Boolean(noteField?.value.trim());
  if (sourceStatus) {
    sourceStatus.textContent = checkedSourceCount === sourceCheckboxes.length
      ? `已逐頁確認 ${checkedSourceCount} / ${sourceCheckboxes.length} 個來源。`
      : `已逐頁確認 ${checkedSourceCount} / ${sourceCheckboxes.length} 個來源；尚有 ${sourceCheckboxes.length - checkedSourceCount} 個未確認。`;
    sourceStatus.classList.toggle("is-complete", checkedSourceCount === sourceCheckboxes.length);
  }
  if (ruleStatus) {
    ruleStatus.textContent = checkedRuleCount === ruleCheckboxes.length
      ? `已逐項確認 ${checkedRuleCount} / ${ruleCheckboxes.length} 個關鍵規定；可提交本次獨立核准。`
      : `已逐項確認 ${checkedRuleCount} / ${ruleCheckboxes.length} 個關鍵規定；尚有 ${ruleCheckboxes.length - checkedRuleCount} 個未確認。`;
    ruleStatus.classList.toggle("is-complete", checkedRuleCount === ruleCheckboxes.length);
  }
  const approveButtons = [...item.querySelectorAll('[data-review-action="approve"]')];
  if (!approveButtons.length) return;
  const staticDisabled = approveButtons[0].dataset.approvalStaticDisabled === "true";
  const submitting = approveButtons.some(
    (button) => button.dataset.approvalSubmitting === "true"
  );
  const sourcesComplete = Boolean(sourceCheckboxes.length)
    && checkedSourceCount === sourceCheckboxes.length;
  const rulesComplete = Boolean(ruleCheckboxes.length)
    && checkedRuleCount === ruleCheckboxes.length;
  const ready = !staticDisabled && sourcesComplete && rulesComplete && noteReady;
  const completion = $("[data-approval-completion]", item);
  const completionMessage = $("[data-approval-completion-message]", item);
  const completionSources = $("[data-approval-completion-sources]", item);
  const completionRules = $("[data-approval-completion-rules]", item);
  const completionNote = $("[data-approval-completion-note]", item);
  const nextIssueButton = $("[data-approval-next-issue]", item);
  item.querySelectorAll("[data-approval-current-issue]").forEach((target) => {
    target.removeAttribute("data-approval-current-issue");
  });
  const nextIssue = staticDisabled
    ? null
    : sourceCheckboxes.find((checkbox) => !checkbox.checked)
      || ruleCheckboxes.find((checkbox) => !checkbox.checked)
      || (!noteReady ? noteField : null);
  if (nextIssue) nextIssue.setAttribute("data-approval-current-issue", "");
  if (completionSources) {
    completionSources.textContent = `官方來源 ${checkedSourceCount}／${sourceCheckboxes.length}`;
  }
  if (completionRules) {
    completionRules.textContent = `關鍵規定 ${checkedRuleCount}／${ruleCheckboxes.length}`;
  }
  if (completionNote) {
    completionNote.textContent = noteReady ? "查核說明已填寫" : "查核說明未填寫";
  }
  if (completionMessage) {
    completionMessage.textContent = staticDisabled
      ? "先完成資料門檻並載入版本對照，才能開始獨立核准。"
      : !sourcesComplete || !rulesComplete
        ? `尚有 ${sourceCheckboxes.length - checkedSourceCount} 個來源、${ruleCheckboxes.length - checkedRuleCount} 個關鍵規定未確認。`
        : !noteReady
          ? "核對項目已完成；請填寫本次查核說明。"
          : "本頁已具備獨立核准送出條件；送出前仍須再次確認內容。";
  }
  completion?.classList.toggle("is-ready", ready);
  completion?.classList.toggle("is-blocked", !ready);
  if (nextIssueButton) {
    nextIssueButton.hidden = staticDisabled || ready;
    nextIssueButton.textContent = nextIssue?.matches("[data-approval-source]")
      ? "前往下一個未確認來源"
      : nextIssue?.matches("[data-approval-rule]")
        ? "前往下一個未確認規定"
        : "前往查核說明";
  }
  approveButtons.forEach((button) => {
    button.disabled = submitting || !ready;
  });
}

function focusNextWorkflowApprovalIssue(button) {
  const item = button.closest("[data-revision-id]");
  if (!item) return;
  updateApprovalChecklist(item);
  const target = $("[data-approval-current-issue]", item);
  if (!target) {
    announce("本頁已具備獨立核准送出條件；送出前請再次確認內容。", "success");
    return;
  }
  target.scrollIntoView({ block: "center" });
  target.focus({ preventScroll: true });
  announce(
    target.matches("[data-approval-source]")
      ? "已前往下一個尚未確認的官方來源。"
      : target.matches("[data-approval-rule]")
        ? "已前往下一個尚未確認的關鍵規定。"
        : "已前往本次查核說明。"
  );
}

function isBacklogMode() {
  return $("#review-status-filter").value === "backlog";
}

function clearWorkflowBacklogLocationState() {
  state.workflowDeepLinkKey = "";
  state.reviewBatchId = "";
  state.reviewBatchWorkflowKeys = [];
  state.workflowDeepLinkSnapshot = "";
  state.workflowDeepLinkStale = false;
}

function updateWorkflowReviewLocation() {
  const status = $("#review-status-filter").value;
  const url = new URL(window.location.href);
  const keepBatchContext = Boolean(
    status === "pending_review"
    && state.reviewBatchId
    && state.workflowDeepLinkSnapshot
  );
  if (["pending_review", "published", "rejected"].includes(status)) {
    url.searchParams.set("review_status", status);
  } else {
    url.searchParams.delete("review_status");
  }
  if (status === "pending_review" && state.workflowReviewFocusRevisionId) {
    url.searchParams.set("workflow_revision", state.workflowReviewFocusRevisionId);
  } else {
    url.searchParams.delete("workflow_revision");
  }
  if (status !== "backlog") {
    url.searchParams.delete("workflow_key");
    if (keepBatchContext) {
      url.searchParams.set("review_batch", state.reviewBatchId);
      url.searchParams.set("batch_size", String(state.reviewBatchSize));
      url.searchParams.set("review_snapshot", state.workflowDeepLinkSnapshot);
    } else {
      url.searchParams.delete("review_batch");
      url.searchParams.delete("batch_size");
      url.searchParams.delete("review_snapshot");
    }
  }
  window.history.replaceState({}, "", url);
}

function syncWorkflowReviewControls() {
  const pending = $("#review-status-filter").value === "pending_review";
  $("#workflow-review-owner-filter-field").hidden = !pending;
  $("#workflow-review-readiness-filter-field").hidden = !pending;
  if (!pending) {
    state.workflowReviewOwnerFilter = "";
    state.workflowReviewReadinessFilter = "";
    $("#workflow-review-owner-filter").value = "";
    $("#workflow-review-readiness-filter").value = "";
  }
}

function filteredWorkflowRevisions() {
  const reviewBatchWorkflowKeys = new Set(state.reviewBatchWorkflowKeys || []);
  return state.revisions.filter((revision) => {
    if (
      state.workflowReviewFocusRevisionId
      && revision.id !== state.workflowReviewFocusRevisionId
    ) return false;
    if (
      $("#review-status-filter").value === "pending_review"
      &&
      state.reviewBatchId
      && !state.workflowDeepLinkStale
      && !reviewBatchWorkflowKeys.has(revision.workflow_key)
    ) return false;
    const progress = approvalProgress(revision);
    const approvedByCurrent = currentAdminApproved(revision);
    if (
      state.workflowReviewOwnerFilter === "mine_unreviewed"
      && (approvedByCurrent || progress.ready || revision.status !== "pending_review")
    ) return false;
    if (state.workflowReviewOwnerFilter === "mine_approved" && !approvedByCurrent) {
      return false;
    }
    if (
      state.workflowReviewOwnerFilter === "mine_publishable"
      && (!approvedByCurrent || !progress.ready)
    ) return false;
    const correctionReady = workflowReviewCorrectionState(revision).correctionReady;
    if (
      state.workflowReviewReadinessFilter === "correction_ready"
      && !correctionReady
    ) return false;
    if (
      state.workflowReviewReadinessFilter === "correction_blocked"
      && correctionReady
    ) return false;
    return true;
  });
}

function workflowReviewBatchTodoRevisions({ ignoreReadiness = false } = {}) {
  if (
    $("#review-status-filter").value !== "pending_review"
    || !state.reviewBatchId
    || state.workflowDeepLinkStale
    || !state.reviewBatchWorkflowKeys.length
  ) return [];
  const revisionsByWorkflow = new Map(
    state.revisions.map((revision) => [revision.workflow_key, revision])
  );
  const todos = state.reviewBatchWorkflowKeys
    .map((workflowKey) => revisionsByWorkflow.get(workflowKey))
    .filter((revision) => {
      if (!revision || revision.status !== "pending_review") return false;
      return !currentAdminApproved(revision) && !approvalProgress(revision).ready;
    });
  if (ignoreReadiness || !state.workflowReviewReadinessFilter) return todos;
  return todos.filter((revision) => {
    const correctionReady = workflowReviewCorrectionState(revision).correctionReady;
    return state.workflowReviewReadinessFilter === "correction_ready"
      ? correctionReady
      : !correctionReady;
  });
}

function nextWorkflowReviewBatchTodoAfter(workflowKey) {
  const orderedTodos = workflowReviewBatchTodoRevisions();
  if (!orderedTodos.length) return null;
  const currentIndex = state.reviewBatchWorkflowKeys.indexOf(workflowKey);
  return orderedTodos.find((revision) => (
    state.reviewBatchWorkflowKeys.indexOf(revision.workflow_key) > currentIndex
  )) || orderedTodos[0];
}

function focusWorkflowReviewRevision(revision) {
  if (!revision) return;
  state.workflowReviewOwnerFilter = "mine_unreviewed";
  state.workflowReviewFocusRevisionId = revision.id;
  $("#workflow-review-owner-filter").value = "mine_unreviewed";
  updateWorkflowReviewLocation();
  renderQueue();
  requestAnimationFrame(() => {
    const target = document.querySelector(
      `[data-revision-id="${CSS.escape(revision.id)}"]`
    );
    if (!target) return;
    target.classList.add("is-focus-target");
    target.focus({ preventScroll: true });
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function openNextWorkflowReviewBatchTodo() {
  const todos = workflowReviewBatchTodoRevisions();
  if (!todos.length) {
    state.workflowReviewFocusRevisionId = "";
    updateWorkflowReviewLocation();
    renderQueue();
    announce("此批次目前沒有屬於你的未核准待辦；這不代表流程已完成雙審或發布。");
    return;
  }
  const currentIndex = todos.findIndex(
    (revision) => revision.id === state.workflowReviewFocusRevisionId
  );
  const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % todos.length : 0;
  const nextRevision = todos[nextIndex];
  focusWorkflowReviewRevision(nextRevision);
  announce(`已開啟此批次第 ${nextIndex + 1}／${todos.length} 筆個人待辦；仍須逐來源、逐規定完成真人核對。`);
}

function showWorkflowReviewBatchTodos() {
  state.workflowReviewFocusRevisionId = "";
  state.workflowReviewOwnerFilter = "mine_unreviewed";
  $("#workflow-review-owner-filter").value = "mine_unreviewed";
  updateWorkflowReviewLocation();
  renderQueue();
  announce("已回到此批次的完整『我的待辦』清單。");
}

function jumpToWorkflowReviewCorrections(button) {
  const item = button.closest("[data-revision-id]");
  const editor = item?.querySelector(".applicability-editor");
  if (!editor) {
    announce("找不到這筆流程的資料補正區，請重新整理後再試。", "error");
    return;
  }
  editor.open = true;
  requestAnimationFrame(() => {
    const summary = editor.querySelector("summary");
    summary?.focus({ preventScroll: true });
    editor.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  announce("已開啟這筆流程的資料補正區；請依官方來源逐頁確認，系統不會替你猜值。");
}

function renderWorkflowReviewFocusFilter() {
  const container = $("#workflow-review-focus-filter");
  const nextButton = $("#open-next-workflow-review");
  const showBatchButton = $("#show-workflow-review-batch");
  const hasBatchContext = Boolean(
    $("#review-status-filter").value === "pending_review"
    && state.reviewBatchId
  );
  const revision = state.revisions.find(
    (row) => row.id === state.workflowReviewFocusRevisionId
  );
  container.hidden = isBacklogMode()
    || (!state.workflowReviewFocusRevisionId && !hasBatchContext);
  if (container.hidden) return;
  if (hasBatchContext) {
    const batchKeys = new Set(state.reviewBatchWorkflowKeys || []);
    const batchRevisions = state.revisions.filter(
      (row) => batchKeys.has(row.workflow_key)
    );
    const unreviewedByCurrent = batchRevisions.filter((row) => {
      const progress = approvalProgress(row);
      return !currentAdminApproved(row) && !progress.ready;
    }).length;
    const approvedByCurrent = batchRevisions.filter(currentAdminApproved).length;
    const readyCount = batchRevisions.filter(
      (row) => approvalProgress(row).ready
    ).length;
    const allTodos = workflowReviewBatchTodoRevisions({ ignoreReadiness: true });
    const correctionReadyCount = allTodos.filter(
      (revision) => workflowReviewCorrectionState(revision).correctionReady
    ).length;
    const correctionBlockedCount = allTodos.length - correctionReadyCount;
    const todos = workflowReviewBatchTodoRevisions();
    const focusedRevision = batchRevisions.find(
      (row) => row.id === state.workflowReviewFocusRevisionId
    );
    const nextItemLabel = state.workflowReviewReadinessFilter === "correction_ready"
      ? "可核對項目"
      : state.workflowReviewReadinessFilter === "correction_blocked"
        ? "待補資料"
        : "待辦";
    container.classList.toggle("is-stale", state.workflowDeepLinkStale);
    nextButton.hidden = state.workflowDeepLinkStale;
    nextButton.disabled = !todos.length || Boolean(focusedRevision && todos.length === 1);
    nextButton.textContent = !todos.length
      ? state.workflowReviewReadinessFilter === "correction_ready"
        ? "目前沒有可開始核對項目"
        : state.workflowReviewReadinessFilter === "correction_blocked"
          ? "目前沒有待補資料項目"
          : "此批次我的待辦已完成"
      : focusedRevision && todos.length === 1
        ? "目前只剩這筆待辦"
        : focusedRevision
          ? `開啟下一筆${nextItemLabel}（${todos.length} 筆）`
          : `開啟第一筆${nextItemLabel}（${todos.length} 筆）`;
    showBatchButton.hidden = state.workflowDeepLinkStale || !focusedRevision;
    $("#clear-workflow-review-focus").textContent = state.workflowDeepLinkStale
      ? "清除過期批次"
      : "離開批次，查看全部待審版本";
    $("#workflow-review-focus-description").textContent = state.workflowDeepLinkStale
      ? "指定的審查批次已過期或不存在；舊範圍未套用，目前只依審查者篩選顯示待審版本。"
      : `目前審查批次 ${state.reviewBatchId}：待審版本 ${batchRevisions.length} 筆、我的待辦 ${unreviewedByCurrent} 筆、可開始真人核對 ${correctionReadyCount} 筆、須先補資料 ${correctionBlockedCount} 筆、我已核准 ${approvedByCurrent} 筆、已達雙審 ${readyCount} 筆。${focusedRevision ? `目前定位 ${focusedRevision.workflow?.school_name || focusedRevision.workflow_key}。` : ""}重新整理仍會重新驗證並維持此批次。`;
    return;
  }
  nextButton.hidden = true;
  showBatchButton.hidden = true;
  container.classList.toggle("is-stale", !revision);
  $("#clear-workflow-review-focus").textContent = "查看全部待審版本";
  $("#workflow-review-focus-description").textContent = revision
    ? `目前定位：${revision.workflow?.school_name || revision.workflow_key} · revision ${revision.id.slice(0, 12)}。重新整理仍會回到這個待審版本。`
    : "指定的待審 revision 已不在目前清單，可能已發布、退回或被取代；定位沒有套用到其他版本。";
}

function filteredBacklogItems() {
  const query = state.backlogSearch.trim().toLocaleLowerCase("zh-Hant");
  const sourceEvidenceWorkflowKeys = new Set(state.sourceEvidenceWorkflowKeys || []);
  const reviewBatchWorkflowKeys = new Set(state.reviewBatchWorkflowKeys || []);
  const filtered = (state.backlog.items || []).filter((row) => {
    if (
      state.workflowDeepLinkKey
      && !state.workflowDeepLinkStale
      && row.workflow_key !== state.workflowDeepLinkKey
    ) return false;
    if (
      state.reviewBatchId
      && !state.workflowDeepLinkStale
      && !reviewBatchWorkflowKeys.has(row.workflow_key)
    ) return false;
    if (state.backlogHomeUniversity && row.home_university !== state.backlogHomeUniversity) return false;
    if (sourceEvidenceWorkflowKeys.size && !sourceEvidenceWorkflowKeys.has(row.workflow_key)) return false;
    if (state.backlogGapFilter === "staged" && !row.has_pending_revision) return false;
    if (state.backlogGapFilter === "unstaged" && row.has_pending_revision) return false;
    if (
      state.backlogGapFilter === "source_replacement_candidate"
      && Number(row.source_replacement_candidate_count || 0) === 0
    ) return false;
    if (
      state.backlogGapFilter === "review_unstarted"
      && (!row.has_pending_revision || Number(row.review_approval_count || 0) !== 0)
    ) return false;
    if (
      state.backlogGapFilter === "review_partial"
      && (
        !row.has_pending_revision
        || Number(row.review_approval_count || 0) === 0
        || Number(row.review_approval_count || 0) >= Number(row.required_review_count || 2)
      )
    ) return false;
    if (state.backlogGapFilter === "review_ready" && !row.review_ready_to_publish) return false;
    if (
      state.backlogGapFilter
      && ![
        "staged",
        "unstaged",
        "review_unstarted",
        "review_partial",
        "review_ready",
        "source_replacement_candidate",
      ].includes(state.backlogGapFilter)
      && !(row.review_gap_codes || []).includes(state.backlogGapFilter)
    ) return false;
    if (!query) return true;
    return [
      row.home_university,
      row.school_name,
      row.country,
      row.program_type,
      row.academic_year,
      row.application_round,
      ...(row.effective_application_rounds || []),
    ].some((value) => String(value || "").toLocaleLowerCase("zh-Hant").includes(query));
  });
  const schoolOrder = (left, right) => left.school_name.localeCompare(right.school_name, "zh-Hant");
  return filtered.sort((left, right) => {
    if (state.backlogSort === "school") return schoolOrder(left, right);
    if (state.backlogSort === "staged") {
      return Number(right.has_pending_revision) - Number(left.has_pending_revision)
        || Number(right.review_gap_count || 0) - Number(left.review_gap_count || 0)
        || schoolOrder(left, right);
    }
    if (state.backlogSort === "approval") {
      const approvalStage = (row) => row.review_ready_to_publish
        ? 3
        : Number(row.review_approval_count || 0) > 0
          ? 2
          : row.has_pending_revision ? 1 : 0;
      return approvalStage(right) - approvalStage(left)
        || Number(right.review_approval_count || 0) - Number(left.review_approval_count || 0)
        || Number(right.review_gap_count || 0) - Number(left.review_gap_count || 0)
        || schoolOrder(left, right);
    }
    if (state.backlogSort === "confirmation") {
      return Number(right.needs_confirmation_count || 0) - Number(left.needs_confirmation_count || 0)
        || schoolOrder(left, right);
    }
    return Number(right.review_gap_count || 0) - Number(left.review_gap_count || 0)
      || Number(!right.academic_year_ready) - Number(!left.academic_year_ready)
      || Number(right.source_metadata_missing_count || 0) - Number(left.source_metadata_missing_count || 0)
      || Number(right.source_year_missing_count || 0) - Number(left.source_year_missing_count || 0)
      || Number(right.review_timestamp_missing_count || 0) - Number(left.review_timestamp_missing_count || 0)
      || Number(right.needs_confirmation_count || 0) - Number(left.needs_confirmation_count || 0)
      || schoolOrder(left, right);
  });
}

const backlogGapLabels = {
  missing_academic_year: "缺適用學年度",
  missing_effective_round: "缺有效申請梯次",
  no_verified_exact_deadline: "缺可驗證精確期限",
  source_year_missing: "官方來源缺適用年度",
  source_metadata_missing: "官方引用缺來源證據資料",
  review_timestamp_missing: "缺最後查核日期",
  critical_rule_source_missing: "關鍵規定缺對應來源",
  insecure_official_source: "含非 HTTPS 官方來源",
  needs_confirmation: "尚有需人工確認步驟",
};

function renderBacklogItem(item) {
  const staged = Boolean(item.has_pending_revision);
  const staging = Boolean(state.staging[item.workflow_key]);
  const approvalCount = Number(item.review_approval_count || 0);
  const requiredReviewCount = Number(item.required_review_count || 2);
  const readyToPublish = Boolean(item.review_ready_to_publish);
  const sourceCandidateCount = Number(item.source_replacement_candidate_count || 0);
  const strongSourceCandidateCount = Number(item.strong_source_replacement_candidate_count || 0);
  const conditionalSourceCandidateCount = Number(item.conditional_source_replacement_candidate_count || 0);
  const transportBlockedSourceCandidateCount = Number(item.transport_blocked_source_replacement_candidate_count || 0);
  const sourceCandidateDetail = [
    strongSourceCandidateCount ? `強 ${strongSourceCandidateCount}` : "",
    conditionalSourceCandidateCount ? `條件 ${conditionalSourceCandidateCount}` : "",
    transportBlockedSourceCandidateCount ? `傳輸阻擋 ${transportBlockedSourceCandidateCount}` : "",
  ].filter(Boolean).join("／");
  const sourceCandidatePill = sourceCandidateCount
    ? `<span class="review-pill candidate">已研究來源候選 ${escapeHtml(sourceCandidateCount)}${sourceCandidateDetail ? `（${escapeHtml(sourceCandidateDetail)}）` : ""}</span>`
    : "";
  const reviewProgressLabel = !staged
    ? "尚未納入雙審"
    : readyToPublish
      ? `已達雙審門檻 ${approvalCount}/${requiredReviewCount}`
      : approvalCount > 0
        ? `待第二位核准 ${approvalCount}/${requiredReviewCount}`
        : `待第一位核准 0/${requiredReviewCount}`;
  const reviewProgressDescription = !staged
    ? "建立後只會出現在待審佇列，學生目前看到的內容與進度不會改變。"
    : readyToPublish
      ? `候選版已有 ${approvalCount}/${requiredReviewCount} 位獨立核准；進入待審版本確認後才可正式發布。`
      : approvalCount > 0
        ? `候選版已有 ${approvalCount}/${requiredReviewCount} 位核准，仍須另一位管理者獨立核對全部來源與規定。`
        : `候選版尚未取得核准；目前缺口與規定數已依這份候選內容重算。`;
  const rounds = item.application_round || (item.effective_application_rounds || []).join("、") || "梯次待確認";
  const gapPills = (item.review_gap_codes || []).map((code) => {
    const suffix = code === "source_year_missing" && item.source_year_missing_count
      ? `（${item.source_year_missing_count} 筆來源）`
      : code === "source_metadata_missing" && item.source_metadata_missing_count
        ? `（${item.source_metadata_missing_count} 個網址）`
      : code === "review_timestamp_missing" && item.review_timestamp_missing_count
        ? `（${item.review_timestamp_missing_count} 筆）`
      : code === "critical_rule_source_missing" && item.critical_rule_source_gap_count
        ? `（${item.critical_rule_source_gap_count} 條規定）`
        : code === "insecure_official_source" && item.insecure_source_count
          ? `（${item.insecure_source_count} 個網址）`
          : "";
    return `<span class="review-pill gap">${escapeHtml((backlogGapLabels[code] || code) + suffix)}</span>`;
  }).join("");
  return `
    <article class="review-item backlog-item" data-workflow-key="${escapeHtml(item.workflow_key)}" tabindex="-1">
      <div class="backlog-item-header">
        <div>
          <div class="review-pills">
            <span class="review-pill ${readyToPublish ? "success" : "warning"}">${escapeHtml(reviewProgressLabel)}</span>
            <span class="review-pill">${escapeHtml(item.home_university)}</span>
            <span class="review-pill">目前版本 ${escapeHtml(item.version)}</span>
          </div>
          <h3>${escapeHtml(item.school_name)}</h3>
          <p>${escapeHtml(item.country || "國家待確認")} · ${escapeHtml(item.program_type || "交換申請流程")} · ${escapeHtml(item.academic_year || "學年度待確認")} · ${escapeHtml(rounds)}</p>
          <div class="review-pills backlog-gap-pills" aria-label="資料缺口與研究候選">${sourceCandidatePill}${gapPills || '<span class="review-pill success">目前無盤點缺口</span>'}</div>
        </div>
        <dl class="backlog-metrics">
          <div><dt>流程步驟</dt><dd>${escapeHtml(item.step_count)}</dd></div>
          <div><dt>官方來源</dt><dd>${escapeHtml(item.source_count)}</dd></div>
          <div><dt>關鍵規定</dt><dd>${escapeHtml(item.critical_rule_count)}</dd></div>
          <div><dt>規定缺來源</dt><dd>${escapeHtml(item.critical_rule_source_gap_count)}</dd></div>
          <div><dt>缺來源證據</dt><dd>${escapeHtml(item.source_metadata_missing_count)}</dd></div>
          <div><dt>非 HTTPS 來源</dt><dd>${escapeHtml(item.insecure_source_count)}</dd></div>
          <div><dt>已研究候選</dt><dd>${escapeHtml(sourceCandidateCount)}</dd></div>
          <div><dt>缺查核日期</dt><dd>${escapeHtml(item.review_timestamp_missing_count)}</dd></div>
          <div><dt>需人工確認</dt><dd>${escapeHtml(item.needs_confirmation_count)}</dd></div>
          <div><dt>可驗證精確期限</dt><dd>${escapeHtml(item.verified_exact_deadline_count)}</dd></div>
          <div><dt>雙審進度</dt><dd>${escapeHtml(`${approvalCount}/${requiredReviewCount}`)}</dd></div>
        </dl>
      </div>
      <div class="backlog-item-footer">
        <p>${escapeHtml(reviewProgressDescription)}</p>
        <button type="button" ${staged ? "class=\"secondary\"" : ""} data-backlog-action="${staged ? "open" : "stage"}" ${staging ? "disabled" : ""}>${staging ? "正在建立…" : staged ? "前往待審版本" : "建立待審版本"}</button>
      </div>
    </article>`;
}

function setSummaryLabels(labels) {
  $("#review-count-label").textContent = labels[0];
  $("#review-unstarted-label").textContent = labels[1];
  $("#review-partial-label").textContent = labels[2];
  $("#review-ready-label").textContent = labels[3];
}

function renderReleaseReadiness() {
  const section = $("#release-readiness");
  const report = state.releaseReadiness;
  section.setAttribute("aria-busy", report ? "false" : "true");
  section.dataset.status = report ? (report.release_ready ? "ready" : "blocked") : "loading";
  if (!report) {
    $("#release-readiness-status").textContent = "檢查中…";
    $("#release-readiness-description").textContent = "正在依目前申請流程、生活情報、來源、期限與雙審證據計算發布阻擋。";
    ["total", "published", "rules", "destinations", "destination-pending", "blockers"].forEach((key) => {
      $(`#release-readiness-${key}`).textContent = "—";
    });
    $("#release-readiness-checks").innerHTML = "";
    $("#release-readiness-fingerprint").textContent = "—";
    $("#release-readiness-generated-at").textContent = "—";
    $("#review-batch-rule-export").hidden = true;
    $("#review-batch-rule-export-description").hidden = true;
    return;
  }

  const failedChecks = (report.checks || []).filter((check) => !check.passed);
  $("#release-readiness-status").textContent = report.release_ready ? "READY" : "NOT READY";
  $("#release-readiness-description").textContent = report.release_ready
    ? "目前資料已通過全部自動化發布檢查；正式決策仍需保留真人審核證據。"
    : `目前仍有 ${report.blocking_check_count} 項發布阻擋；修正資料並完成雙審後重新整理即可重算。`;
  $("#release-readiness-total").textContent = report.total_workflow_count;
  $("#release-readiness-published").textContent = report.published_workflow_count;
  $("#release-readiness-rules").textContent = report.critical_rule_count;
  $("#release-readiness-destinations").textContent = report.total_destination_profile_count;
  $("#release-readiness-destination-pending").textContent = report.pending_destination_profile_review_count;
  $("#release-readiness-blockers").textContent = report.blocking_check_count;
  $("#release-readiness-summary").textContent = failedChecks.length
    ? `查看 ${failedChecks.length} 項阻擋`
    : "全部自動化檢查已通過";
  $("#release-readiness-checks").innerHTML = failedChecks.length
    ? failedChecks.map((check) => `
      <li>
        <strong>${escapeHtml(check.label)}：${escapeHtml(check.actual_count)}</strong>
        <span>${escapeHtml(check.detail)}</span>
      </li>`).join("")
    : '<li class="is-passed"><strong>沒有自動化阻擋</strong><span>仍須由負責人確認真人審查與發布決策。</span></li>';
  $("#release-readiness-fingerprint").textContent = report.snapshot_fingerprint;
  $("#release-readiness-generated-at").textContent = formatDate(report.generated_at);
  const batchRuleExport = $("#review-batch-rule-export");
  const batchRuleDescription = $("#review-batch-rule-export-description");
  const showBatchRuleExport = Boolean(
    state.reviewBatchId
    && !state.workflowDeepLinkStale
    && state.reviewBatchWorkflowKeys.length
  );
  batchRuleExport.hidden = !showBatchRuleExport;
  batchRuleDescription.hidden = !showBatchRuleExport;
  if (showBatchRuleExport) {
    batchRuleExport.href = `/admin/application-workflow-review-batches/${encodeURIComponent(state.reviewBatchId)}/rules.csv?batch_size=${encodeURIComponent(state.reviewBatchSize)}&expected_snapshot=${encodeURIComponent(state.workflowDeepLinkSnapshot)}`;
  }
}

function destinationReviewProgressLabel(progress) {
  return {
    unstarted: "尚未開始真人雙審",
    partial: "已完成一位，等待第二位",
    ready_for_promotion: "兩位已完成，可交內容負責人處理",
    changes_required: "真人已要求修正",
  }[progress] || "待人工審查";
}

function destinationReviewDecisionLabel(decision) {
  return {
    approve: "內容可交下一步處理",
    changes_required: "內容需要修正",
  }[decision] || "尚未留下結論";
}

function renderDestinationText(value) {
  if (value === null || value === undefined || value === "") {
    return '<span class="comparison-empty-value">未提供／待確認</span>';
  }
  return escapeHtml(value).replaceAll("\n", "<br>");
}

function destinationReviewDraftKey(profileHash) {
  const reviewerId = state.admin?.id || "";
  if (!reviewerId || !profileHash) return "";
  return `${destinationReviewDraftStoragePrefix}:${reviewerId}:${profileHash}`;
}

function loadDestinationReviewDraft(profileHash) {
  const key = destinationReviewDraftKey(profileHash);
  if (!key) return null;
  try {
    const raw = window.sessionStorage.getItem(key);
    if (!raw) return null;
    const payload = JSON.parse(raw);
    if (
      !payload
      || payload.profile_content_hash !== profileHash
      || payload.reviewer_id !== state.admin?.id
    ) {
      window.sessionStorage.removeItem(key);
      return null;
    }
    return {
      profile_content_hash: profileHash,
      reviewer_id: state.admin.id,
      reviewed_source_urls: Array.isArray(payload.reviewed_source_urls)
        ? payload.reviewed_source_urls.filter((value) => typeof value === "string")
        : [],
      reviewed_section_keys: Array.isArray(payload.reviewed_section_keys)
        ? payload.reviewed_section_keys.filter((value) => typeof value === "string")
        : [],
      decision: ["approve", "changes_required"].includes(payload.decision)
        ? payload.decision
        : "approve",
      note: typeof payload.note === "string" ? payload.note.slice(0, 2000) : "",
      saved_at: typeof payload.saved_at === "string" ? payload.saved_at : "",
    };
  } catch (_error) {
    try {
      window.sessionStorage.removeItem(key);
    } catch (_storageError) {
      // The workbench remains usable even when browser storage is unavailable.
    }
    return null;
  }
}

function clearDestinationReviewDraft(profileHash) {
  const key = destinationReviewDraftKey(profileHash);
  if (!key) return;
  try {
    window.sessionStorage.removeItem(key);
  } catch (_error) {
    // Clearing a local convenience draft must never block the review workflow.
  }
}

function saveDestinationReviewDraftFromCard(card) {
  const profileHash = card?.dataset.destinationProfileHash || "";
  const key = destinationReviewDraftKey(profileHash);
  if (!card || !key) return;
  const decisionField = $("[data-destination-review-decision]", card);
  const decision = ["approve", "changes_required"].includes(decisionField?.value)
    ? decisionField.value
    : "approve";
  const payload = {
    profile_content_hash: profileHash,
    reviewer_id: state.admin.id,
    reviewed_source_urls: [...card.querySelectorAll("[data-destination-review-source]:checked")]
      .map((checkbox) => checkbox.value),
    reviewed_section_keys: [...card.querySelectorAll("[data-destination-review-section]:checked")]
      .map((checkbox) => checkbox.value),
    decision,
    note: ($("[data-destination-review-note]", card)?.value || "").slice(0, 2000),
    saved_at: new Date().toISOString(),
  };
  const status = $("[data-destination-review-draft-status]", card);
  const clearButton = $("[data-destination-review-draft-clear]", card);
  try {
    window.sessionStorage.setItem(key, JSON.stringify(payload));
    if (status) {
      status.textContent = "已在此分頁工作階段暫存；重新整理可恢復，但尚未送到後端，也不是審查證據。";
    }
    if (clearButton) clearButton.hidden = false;
  } catch (_error) {
    if (status) {
      status.textContent = "瀏覽器無法保存本頁暫存；請先不要重新整理，已填內容仍可直接送出。";
    }
  }
}

function resetDestinationReviewDraftCard(card, row) {
  if (!card || !row) return;
  clearDestinationReviewDraft(row.profile_content_hash);
  card.querySelectorAll(
    "[data-destination-review-source], [data-destination-review-section]"
  ).forEach((checkbox) => {
    checkbox.checked = false;
  });
  const decision = $("[data-destination-review-decision]", card);
  if (decision) {
    decision.value = destinationReviewApprovalBlockers(row).length
      ? "changes_required"
      : row.current_reviewer_decision || "approve";
  }
  const note = $("[data-destination-review-note]", card);
  if (note) note.value = "";
  const status = $("[data-destination-review-draft-status]", card);
  if (status) {
    status.textContent = "尚未建立本頁暫存；勾選或輸入後會自動保存在這個分頁工作階段。";
  }
  const clearButton = $("[data-destination-review-draft-clear]", card);
  if (clearButton) clearButton.hidden = true;
  updateDestinationReviewChecklistProgress(card);
}

function renderDestinationChecklist(title, items) {
  return `
    <section class="destination-content-group">
      <h5>${escapeHtml(title)}</h5>
      ${(items || []).length ? `<ol>${items.map((item) => `
        <li>
          <strong>${escapeHtml(item.title)}</strong>
          <p>${renderDestinationText(item.detail)}</p>
          <small>${escapeHtml(item.timing || "時間點待確認")} · 證據：${escapeHtml(item.evidence_type || "待確認")}</small>
          ${(item.source_urls || []).length ? `<ul class="destination-inline-sources">${item.source_urls.map((url) => `<li>${escapeHtml(url)}</li>`).join("")}</ul>` : ""}
        </li>`).join("")}</ol>` : '<p class="comparison-empty">這一區目前沒有項目；仍須確認是確實不適用或尚未補齊。</p>'}
    </section>`;
}

function filteredDestinationReviewItems() {
  const queue = state.destinationProfileReview;
  if (!queue) return [];
  const needle = state.destinationReviewSearch.trim().toLocaleLowerCase("zh-Hant");
  const batchProfileHashes = new Set(state.destinationReviewBatchProfileHashes);
  return (queue.items || []).filter((row) => {
    if (batchProfileHashes.size && !batchProfileHashes.has(row.profile_content_hash)) {
      return false;
    }
    const progressFilter = state.destinationReviewProgressFilter;
    if (progressFilter === "mine_unreviewed" && row.current_reviewer_decision) return false;
    if (progressFilter === "mine_reviewed" && !row.current_reviewer_decision) return false;
    if (
      progressFilter
      && !["mine_unreviewed", "mine_reviewed"].includes(progressFilter)
      && row.review_progress !== progressFilter
    ) return false;
    const readinessFilter = state.destinationReviewReadinessFilter;
    const approvalBlocked = destinationReviewApprovalBlockers(row).length > 0;
    if (readinessFilter === "approval_ready" && approvalBlocked) return false;
    if (readinessFilter === "approval_blocked" && !approvalBlocked) return false;
    if (!needle) return true;
    return [row.school_name, row.country, row.city, row.coverage_note]
      .filter(Boolean)
      .some((value) => String(value).toLocaleLowerCase("zh-Hant").includes(needle));
  });
}

function destinationReviewBatchTodoRows({ ignoreReadiness = false } = {}) {
  if (
    !state.destinationReviewBatchProfileHashes.length
    || state.destinationReviewBatchStale
    || state.destinationReviewBatchError
  ) return [];
  const rowsByHash = new Map(
    (state.destinationProfileReview?.items || []).map((row) => [
      row.profile_content_hash,
      row,
    ])
  );
  const todos = state.destinationReviewBatchProfileHashes
    .map((hash) => rowsByHash.get(hash))
    .filter((row) => row && !row.current_reviewer_decision);
  if (ignoreReadiness || !state.destinationReviewReadinessFilter) return todos;
  return todos.filter((row) => {
    const approvalBlocked = destinationReviewApprovalBlockers(row).length > 0;
    return state.destinationReviewReadinessFilter === "approval_ready"
      ? !approvalBlocked
      : approvalBlocked;
  });
}

function nextDestinationReviewBatchTodoAfter(profileHash) {
  const orderedTodos = destinationReviewBatchTodoRows();
  if (!orderedTodos.length) return null;
  const currentIndex = state.destinationReviewBatchProfileHashes.indexOf(profileHash);
  return orderedTodos.find((row) => (
    state.destinationReviewBatchProfileHashes.indexOf(row.profile_content_hash)
      > currentIndex
  )) || orderedTodos[0];
}

function openDestinationReviewBatchTodo(row) {
  if (!row) return false;
  state.destinationReviewFocusProfileHash = row.profile_content_hash;
  state.destinationReviewSearch = "";
  state.destinationReviewProgressFilter = "mine_unreviewed";
  state.destinationReviewVisibleLimit = Math.max(
    10,
    state.destinationReviewBatchProfileHashes.length
  );
  $("#destination-review-search").value = "";
  $("#destination-review-progress-filter").value = "mine_unreviewed";
  renderDestinationProfileReviewItems();
  requestAnimationFrame(() => {
    const card = document.querySelector(
      `[data-destination-profile-hash="${CSS.escape(row.profile_content_hash)}"]`
    );
    const detail = card?.querySelector(".destination-review-detail");
    if (!card || !detail) return;
    detail.open = true;
    const summary = detail.querySelector("summary");
    summary?.focus({ preventScroll: true });
    card.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  return true;
}

function openNextDestinationReviewBatchTodo() {
  const nextTodo = nextDestinationReviewBatchTodoAfter(
    state.destinationReviewFocusProfileHash
  );
  if (!openDestinationReviewBatchTodo(nextTodo)) {
    state.destinationReviewFocusProfileHash = "";
    renderDestinationReviewBatchFilter();
    const hasOtherTodos = destinationReviewBatchTodoRows({ ignoreReadiness: true }).length > 0;
    announce(hasOtherTodos && state.destinationReviewReadinessFilter
      ? "目前核可門檻篩選沒有屬於你的未審項目；其他門檻仍可能有待辦。"
      : "此批次目前沒有屬於你的未審項目；這不代表其他審查者、雙審、升級或發布已完成。"
    );
    return;
  }
  const todos = destinationReviewBatchTodoRows();
  const position = todos.findIndex((row) => (
    row.profile_content_hash === nextTodo.profile_content_hash
  ));
  announce(
    `已開啟此批次第 ${position + 1}／${todos.length} 筆我的待辦；仍須逐一核對全部官方來源與 12 個內容區塊。`
  );
}

function showDestinationReviewBatchTodos() {
  state.destinationReviewFocusProfileHash = "";
  state.destinationReviewSearch = "";
  state.destinationReviewProgressFilter = "mine_unreviewed";
  state.destinationReviewVisibleLimit = Math.max(
    10,
    state.destinationReviewBatchProfileHashes.length
  );
  $("#destination-review-search").value = "";
  $("#destination-review-progress-filter").value = "mine_unreviewed";
  renderDestinationProfileReviewItems();
  announce(
    "已顯示此批次的完整『我的待辦』清單；這只是目前帳號的未審項目。"
  );
}

function destinationReviewApprovalBlockers(row) {
  const labels = {
    missing_sources: "缺少可逐頁核對的官方來源",
    insecure_sources: "官方來源包含非 HTTPS 網址",
    missing_last_checked: "缺少最後查核時間",
  };
  return (row.review_gap_codes || [])
    .filter((code) => Object.hasOwn(labels, code))
    .map((code) => ({ code, label: labels[code] }));
}

function updateDestinationReviewChecklistProgress(card) {
  if (!card) return;
  const sourceCheckboxes = [...card.querySelectorAll("[data-destination-review-source]")];
  const sectionCheckboxes = [...card.querySelectorAll("[data-destination-review-section]")];
  const checkedSourceCount = sourceCheckboxes.filter((checkbox) => checkbox.checked).length;
  const checkedSectionCount = sectionCheckboxes.filter((checkbox) => checkbox.checked).length;
  const remainingCount = (
    sourceCheckboxes.length - checkedSourceCount
    + sectionCheckboxes.length - checkedSectionCount
  );
  const progress = $("[data-destination-review-check-progress]", card);
  const sourceProgress = $("[data-destination-review-source-progress]", card);
  const sectionProgress = $("[data-destination-review-section-progress]", card);
  const noteProgress = $("[data-destination-review-note-progress]", card);
  const message = $("[data-destination-review-check-progress-message]", card);
  const nextButton = $("[data-destination-review-next-unchecked]", card);
  const noteField = $("[data-destination-review-note]", card);
  const noteLength = noteField?.value.trim().length || 0;
  const noteReady = noteLength >= 10;
  const submitButtons = card.querySelectorAll(
    "[data-destination-review-submit], [data-destination-review-submit-next]"
  );
  const submitting = Boolean(
    state.destinationReviewSubmitting[card.dataset.destinationProfileHash || ""]
  );
  card.querySelectorAll(
    "[data-destination-review-current-unchecked], [data-destination-review-current-issue]"
  ).forEach((item) => {
    item.removeAttribute("data-destination-review-current-unchecked");
    item.removeAttribute("data-destination-review-current-issue");
  });
  const nextUnchecked = (
    sourceCheckboxes.find((checkbox) => !checkbox.checked)
    || sectionCheckboxes.find((checkbox) => !checkbox.checked)
  );
  const nextIssue = nextUnchecked || (!noteReady ? noteField : null);
  if (nextUnchecked) {
    nextUnchecked.setAttribute("data-destination-review-current-unchecked", "");
  }
  if (nextIssue) nextIssue.setAttribute("data-destination-review-current-issue", "");
  if (sourceProgress) {
    sourceProgress.textContent = sourceCheckboxes.length
      ? `官方來源 ${checkedSourceCount}／${sourceCheckboxes.length}`
      : "官方來源 0／0（目前沒有可勾選來源）";
  }
  if (sectionProgress) {
    sectionProgress.textContent = `內容區塊 ${checkedSectionCount}／${sectionCheckboxes.length}`;
  }
  if (noteProgress) {
    noteProgress.textContent = `審查說明 ${noteLength} 字（至少 10 字）`;
  }
  const checklistComplete = remainingCount === 0;
  const ready = checklistComplete && noteReady;
  progress?.classList.toggle("is-ready", ready);
  progress?.classList.toggle("is-blocked", !ready);
  if (message) {
    message.textContent = !checklistComplete
      ? `尚有 ${remainingCount} 個核對項目未完成；系統不會替你自動勾選。`
      : !noteReady
        ? `核對項目已完成；審查說明尚需 ${10 - noteLength} 字。`
        : "本頁已具備送出條件；送出前仍須由本人再次確認結論。";
  }
  if (nextButton) {
    nextButton.hidden = ready;
    nextButton.textContent = nextUnchecked
      ? "前往下一個未核對項目"
      : "前往審查說明";
  }
  submitButtons.forEach((button) => {
    button.disabled = submitting || !ready;
  });
}

function focusNextDestinationReviewChecklistItem(button) {
  const card = button.closest("[data-destination-profile-hash]");
  if (!card) return;
  updateDestinationReviewChecklistProgress(card);
  const target = $("[data-destination-review-current-issue]", card);
  if (!target) {
    announce("本頁已具備送出條件；送出前請再次確認結論。", "success");
    return;
  }
  target.scrollIntoView({ block: "center" });
  target.focus({ preventScroll: true });
  announce(
    target.matches("[data-destination-review-source]")
      ? "已前往下一個尚未核對的官方來源；請先開啟連結確認，再由本人勾選。"
      : target.matches("[data-destination-review-section]")
        ? "已前往下一個尚未核對的生活情報內容區塊。"
        : "已前往審查說明；請留下至少 10 字的本人查核紀錄。"
  );
}

function renderDestinationReviewCard(row) {
  const profile = row.profile || {};
  const reviews = row.review_history || row.current_reviews || [];
  const currentReviewIds = new Set((row.current_reviews || []).map((review) => review.id));
  const currentReviewerHasDecision = Boolean(row.current_reviewer_decision);
  const sections = state.destinationProfileReview?.review_sections || [];
  const submitting = Boolean(state.destinationReviewSubmitting[row.profile_content_hash]);
  const promotionSubmitting = Boolean(state.destinationPromotionSubmitting[row.profile_content_hash]);
  const canPromote = row.ready_for_promotion && row.current_reviewer_decision === "approve";
  const canContinueBatchTodo = Boolean(
    state.destinationReviewBatchProfileHashes.length
    && !state.destinationReviewBatchStale
    && !state.destinationReviewBatchError
    && !currentReviewerHasDecision
  );
  const approvalBlockers = destinationReviewApprovalBlockers(row);
  const draft = loadDestinationReviewDraft(row.profile_content_hash);
  const draftSourceUrls = new Set(draft?.reviewed_source_urls || []);
  const draftSectionKeys = new Set(draft?.reviewed_section_keys || []);
  const decision = approvalBlockers.length
    ? "changes_required"
    : draft?.decision || row.current_reviewer_decision || "approve";
  const guideSections = profile.student_guide_sections || [];
  const photos = profile.guide_photos || [];
  return `
    <article class="destination-review-card" data-destination-profile-hash="${escapeHtml(row.profile_content_hash)}" data-destination-school-name="${escapeHtml(row.school_name)}">
      <header class="destination-review-card-header">
        <div>
          <p class="eyebrow">優先序 ${escapeHtml(row.priority_order)} · ${escapeHtml(row.country || "國家待確認")}${row.city ? ` · ${escapeHtml(row.city)}` : ""}</p>
          <h4>${escapeHtml(row.school_name)}</h4>
          <p>${escapeHtml(row.coverage_note)}</p>
        </div>
        <div class="destination-review-progress" data-progress="${escapeHtml(row.review_progress)}">
          <strong>${escapeHtml(destinationReviewProgressLabel(row.review_progress))}</strong>
          <span>有效核可 ${escapeHtml(row.review_approval_count)}／${escapeHtml(row.required_review_count)} · 要求修正 ${escapeHtml(row.review_change_request_count)}</span>
        </div>
      </header>
      <details class="destination-review-detail">
        <summary>開啟完整內容、來源與逐項審查表</summary>
        <div class="destination-review-content">
          <dl class="destination-profile-facts">
            <div><dt>費用</dt><dd>${renderDestinationText(profile.cost_summary)}</dd></div>
            <div><dt>住宿</dt><dd>${renderDestinationText(profile.housing_summary)}</dd></div>
            <div><dt>交通</dt><dd>${renderDestinationText(profile.transport_summary)}</dd></div>
            <div><dt>校園生活</dt><dd>${renderDestinationText(profile.campus_life_summary)}</dd></div>
            <div><dt>查核狀態</dt><dd>${escapeHtml(profile.coverage_status || row.coverage_status)}</dd></div>
            <div><dt>最後查核</dt><dd>${escapeHtml(formatDate(profile.last_checked))}</dd></div>
          </dl>
          <section class="destination-content-group">
            <h5>生活指南段落</h5>
            ${guideSections.length ? guideSections.map((section) => `
              <article class="destination-guide-section">
                <strong>${escapeHtml(section.title)}</strong>
                <p>${renderDestinationText(section.summary)}</p>
                ${(section.points || []).length ? `<ul>${section.points.map((point) => `<li>${escapeHtml(point)}</li>`).join("")}</ul>` : ""}
                ${section.caution ? `<p class="destination-caution">警語：${escapeHtml(section.caution)}</p>` : ""}
                <small>證據：${escapeHtml(section.evidence_type || "待確認")} · 來源 ${(section.source_urls || []).length}</small>
              </article>`).join("") : '<p class="comparison-empty">目前沒有生活指南段落。</p>'}
          </section>
          ${renderDestinationChecklist("抵達 72 小時", profile.first_72_hours)}
          ${renderDestinationChecklist("臺灣出發前準備", profile.packing_from_taiwan)}
          ${renderDestinationChecklist("抵達後採買", profile.buy_after_arrival)}
          <section class="destination-content-group">
            <h5>照片與圖說</h5>
            ${photos.length ? `<ul>${photos.map((photo) => `<li><strong>${escapeHtml(photo.alt)}</strong>：${escapeHtml(photo.caption)}<br><small>${escapeHtml(photo.image_url)} · 來源 ${escapeHtml(photo.source_url)}</small></li>`).join("")}</ul>` : '<p class="comparison-empty">目前沒有照片；不影響文字審查，但不得把缺圖誤認為已查核。</p>'}
          </section>
          <section class="destination-review-evidence" aria-label="目前真人審查證據">
            <h5>目前有效的真人審查證據</h5>
            ${reviews.length ? `<ol>${reviews.map((review) => `
              <li data-review-decision="${escapeHtml(review.decision)}">
                <strong>${escapeHtml(review.reviewer_display_name)} · ${escapeHtml(destinationReviewDecisionLabel(review.decision))}${currentReviewIds.has(review.id) ? " · 目前有效" : " · 已由同一審查者後續結論取代"}</strong>
                <span>${escapeHtml(formatDate(review.reviewed_at))}</span>
                <p>${escapeHtml(review.note)}</p>
                <small>內容指紋 ${escapeHtml(review.profile_content_hash.slice(0, 12))} · ${escapeHtml(review.reviewed_source_urls.length)} 個來源 · ${escapeHtml(review.reviewed_section_keys.length)} 個區塊</small>
              </li>`).join("")}</ol>` : '<p class="approval-empty">這個內容指紋還沒有真人審查證據。</p>'}
          </section>
          <section class="destination-review-checklist">
            <div class="destination-review-check-progress is-blocked" data-destination-review-check-progress aria-live="polite">
              <div>
                <strong data-destination-review-check-progress-message>正在計算本頁人工核對進度…</strong>
                <span data-destination-review-source-progress>官方來源 0／${escapeHtml((profile.sources || []).length)}</span>
                <span data-destination-review-section-progress>內容區塊 0／${escapeHtml(sections.length)}</span>
                <span data-destination-review-note-progress>審查說明 0 字（至少 10 字）</span>
              </div>
              <button class="secondary" type="button" data-destination-review-next-unchecked>前往下一個未核對項目</button>
            </div>
            <p>進度只反映此分頁目前的勾選；不會自動勾選、送出、建立審查證據或解除上方核可門檻。</p>
            <h5>一、逐一開啟並核對全部官方來源</h5>
            <p>勾選代表你本人已開啟並確認該來源直接支持目前敘述。</p>
            <div class="destination-review-checkboxes destination-source-checkboxes">
              ${(profile.sources || []).map((source) => `
                <label>
                  <input type="checkbox" data-destination-review-source value="${escapeHtml(source.source_url)}" ${draftSourceUrls.has(source.source_url) ? "checked" : ""} />
                  <span><strong>${escapeHtml(source.title)}</strong><a href="${escapeHtml(safeExternalUrl(source.source_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.source_url)}</a>${source.summary ? `<small>${escapeHtml(source.summary)}</small>` : ""}</span>
                </label>`).join("") || '<p class="approval-empty">目前沒有官方來源；只能選擇要求修正。</p>'}
            </div>
            <h5>二、逐項核對所有內容區塊</h5>
            <div class="destination-review-checkboxes destination-section-checkboxes">
              ${sections.map((section) => `
                <label>
                  <input type="checkbox" data-destination-review-section value="${escapeHtml(section.key)}" ${draftSectionKeys.has(section.key) ? "checked" : ""} />
                  <span><strong>${escapeHtml(section.label)}</strong><small>${escapeHtml(section.description)}</small></span>
                </label>`).join("")}
            </div>
            <h5>三、留下本人的結論與說明</h5>
            <div class="destination-review-decision-gate ${approvalBlockers.length ? "is-blocked" : "is-ready"}" data-destination-review-approval-gate>
              ${approvalBlockers.length ? `
                <strong>目前只能要求修正，不能核可</strong>
                <p>這筆候選仍有後端核可阻擋；即使完成全部勾選，也不能選擇「內容可交下一步處理」。</p>
                <ul>${approvalBlockers.map((blocker) => `<li data-destination-review-blocker="${escapeHtml(blocker.code)}">${escapeHtml(blocker.label)}</li>`).join("")}</ul>
              ` : `
                <strong>目前具備可選擇核可的資料門檻</strong>
                <p>這只表示有 HTTPS 官方來源及查核時間；仍須本人逐頁確認全部來源與內容，不能視為已核可。</p>
              `}
            </div>
            <label class="destination-review-decision-field">
              <span>審查結論</span>
              <select data-destination-review-decision>
                <option value="approve" ${approvalBlockers.length ? "disabled" : ""} ${decision === "approve" ? "selected" : ""}>內容可交下一步處理</option>
                <option value="changes_required" ${decision === "changes_required" ? "selected" : ""}>內容需要修正</option>
              </select>
            </label>
            <label class="destination-review-note-field">
              <span>審查說明（至少 10 字）</span>
              <textarea data-destination-review-note minlength="10" maxlength="2000" placeholder="記錄你核對的年度、校區、適用身分與任何疑義。">${escapeHtml(draft?.note || "")}</textarea>
            </label>
            <div class="destination-review-draft">
              <p data-destination-review-draft-status>${draft ? "已從此分頁工作階段恢復暫存；尚未送到後端，也不是審查證據。" : "尚未建立本頁暫存；勾選或輸入後會自動保存在這個分頁工作階段。"}</p>
              <button class="secondary" type="button" data-destination-review-draft-clear ${draft ? "" : "hidden"}>清除本頁暫存</button>
            </div>
            <div class="destination-review-submit-actions">
              <button type="button" data-destination-review-submit disabled>${submitting ? "正在保存…" : currentReviewerHasDecision ? "更新我的獨立審查" : "保存我的獨立審查"}</button>
              ${canContinueBatchTodo ? `<button class="secondary" type="button" data-destination-review-submit-next disabled>${submitting ? "正在保存…" : "保存並前往下一筆我的待辦"}</button>` : ""}
            </div>
            <p class="action-note">這個動作只新增後端稽核證據；不會修改 profile、升級 official_verified、通知學生或發布資料。</p>
          </section>
          ${row.ready_for_promotion ? `
          <section class="destination-promotion-panel" aria-label="生活情報升級確認">
            <h5>四、由其中一位有效核可者明確升級</h5>
            <p>這不是自動動作。確認後，學生會看到本次雙審鎖定的內容，查核狀態會改為 <code>official_verified</code>；申請規則、截止日、文件與通知不會一起改變。</p>
            ${canPromote ? "" : '<p class="destination-promotion-warning">目前帳號不是這個內容指紋的有效核可者，不能執行升級。</p>'}
            <label class="destination-review-note-field">
              <span>升級說明（至少 10 字）</span>
              <textarea data-destination-promotion-note minlength="10" maxlength="2000" placeholder="確認兩位核可證據、內容指紋及學生可見變更。" ${canPromote ? "" : "disabled"}></textarea>
            </label>
            <label class="destination-promotion-confirmation">
              <input type="checkbox" data-destination-promotion-confirm ${canPromote ? "" : "disabled"} />
              <span>我確認這會把目前雙審版本升級為學生可見的完整查核生活情報。</span>
            </label>
            <button type="button" data-destination-promotion-submit ${canPromote && !promotionSubmitting ? "" : "disabled"}>${promotionSubmitting ? "正在升級…" : "確認升級生活情報"}</button>
            <p class="action-note">升級會新增不可覆寫的後端稽核事件，不改寫原始候選資料；未來候選內容有變更時必須重新雙審。</p>
          </section>` : ""}
          <p class="destination-profile-hash">完整內容指紋：<code>${escapeHtml(row.profile_content_hash)}</code></p>
        </div>
      </details>
    </article>`;
}

function renderDestinationProfileReviewItems() {
  const container = $("#destination-profile-review-items");
  if (!container) return;
  renderDestinationReviewBatchFilter();
  if (state.destinationProfileReviewError) {
    container.innerHTML = `<div class="review-error">${escapeHtml(state.destinationProfileReviewError)}</div>`;
    return;
  }
  if (!state.destinationProfileReview) {
    container.innerHTML = '<div class="review-loading">正在載入生活情報審查表…</div>';
    return;
  }
  const items = filteredDestinationReviewItems();
  const visible = items.slice(0, state.destinationReviewVisibleLimit);
  if (!items.length) {
    container.innerHTML = `<div class="review-loading">${state.destinationReviewReadinessFilter ? "目前核可門檻篩選沒有待審生活情報。" : "目前篩選條件沒有待審生活情報。"}</div>`;
    return;
  }
  container.innerHTML = visible.map(renderDestinationReviewCard).join("") + (
    visible.length < items.length
      ? `<div class="backlog-more"><span>目前顯示 ${visible.length}／${items.length} 筆</span><button type="button" class="secondary" data-destination-review-more>再顯示 10 筆</button></div>`
      : `<p class="destination-review-list-count">目前顯示 ${items.length} 筆符合條件的生活情報。</p>`
  );
  container.querySelectorAll("[data-destination-profile-hash]").forEach((card) => {
    updateDestinationReviewChecklistProgress(card);
  });
}

function renderDestinationProfileReviewSummary() {
  const section = $("#destination-profile-review-summary");
  const title = $("#destination-profile-review-title");
  const description = $("#destination-profile-review-description");
  const download = $("#download-destination-profile-review");
  const batchDownload = $("#download-destination-profile-review-batches");
  const queue = state.destinationProfileReview;
  title.textContent = `${state.destinationReviewHomeUniversity}生活情報獨立雙人審查`;
  section.setAttribute("aria-busy", queue || state.destinationProfileReviewError ? "false" : "true");
  if (state.destinationProfileReviewError) {
    description.textContent = `生活情報待辦暫時無法載入：${state.destinationProfileReviewError}`;
    download.hidden = true;
    batchDownload.hidden = true;
    renderDestinationProfileReviewItems();
    return;
  }
  if (!queue) {
    description.textContent = "正在盤點部分查核 profile 與官方來源…";
    download.hidden = true;
    batchDownload.hidden = true;
    renderDestinationProfileReviewItems();
    return;
  }
  description.textContent = (
    `${queue.home_university || "全部母校"}共有 ${queue.total_profile_count} 筆生活情報；` +
    `${queue.verified_profile_count} 筆完整查核、${queue.pending_review_count} 筆待人工續審。` +
    `其中 ${queue.explicit_second_review_required_count} 筆明確等待第二位真人，` +
    `待審資料共有 ${queue.pending_source_count} 個官方來源。` +
    `目前 ${queue.review_started_profile_count} 筆已有真人證據、${queue.ready_for_promotion_count} 筆完成兩人核對、${queue.change_requested_profile_count} 筆被要求修正。`
  );
  const params = new URLSearchParams({
    expected_snapshot: queue.snapshot_fingerprint,
  });
  if (queue.home_university) params.set("home_university", queue.home_university);
  download.href = `/admin/destination-profile-review-queue.csv?${params.toString()}`;
  download.hidden = queue.pending_review_count === 0;
  download.setAttribute(
    "aria-label",
    `下載 ${queue.pending_review_count} 筆生活情報的唯讀人工審查清單`
  );
  const batchParams = new URLSearchParams({
    home_university: queue.home_university || state.destinationReviewHomeUniversity,
    batch_size: String(state.destinationReviewBatchSize),
  });
  batchDownload.href = `/admin/destination-profile-review-batches.csv?${batchParams.toString()}`;
  batchDownload.hidden = queue.pending_review_count === 0;
  batchDownload.setAttribute(
    "aria-label",
    `下載 ${queue.pending_review_count} 筆生活情報、每批 ${state.destinationReviewBatchSize} 筆的雙人分工清單`
  );
  renderDestinationProfileReviewItems();
}

function renderDestinationReviewBatchFilter() {
  const container = $("#destination-review-batch-filter");
  const description = $("#destination-review-batch-description");
  const openNextButton = $("#open-next-destination-review");
  const showTodosButton = $("#show-destination-review-batch");
  const checklistDownload = $("#download-destination-review-batch-checklist");
  const hasBatch = Boolean(
    state.destinationReviewBatchId
    && state.destinationReviewBatchProfileHashes.length
  );
  const hasProblem = Boolean(
    state.destinationReviewBatchStale || state.destinationReviewBatchError
  );
  container.hidden = !hasBatch && !hasProblem;
  openNextButton.hidden = true;
  showTodosButton.hidden = true;
  checklistDownload.hidden = true;
  if (container.hidden) return;
  container.classList.toggle("is-stale", hasProblem);
  $("#clear-destination-review-batch").textContent = hasProblem
    ? "清除過期批次"
    : "回到這所母校的完整待辦";
  if (state.destinationReviewBatchStale) {
    description.textContent = `這份生活情報分工批次已過期（內容指紋 ${state.destinationReviewBatchSnapshot.slice(0, 12)}）；候選內容或待審成員已變更，舊定位未套用，請重新下載目前版本。`;
    return;
  }
  if (state.destinationReviewBatchError) {
    description.textContent = `生活情報分工批次暫時無法載入：${state.destinationReviewBatchError}`;
    return;
  }
  const hashes = new Set(state.destinationReviewBatchProfileHashes);
  const items = (state.destinationProfileReview?.items || []).filter((row) => (
    hashes.has(row.profile_content_hash)
  ));
  const started = items.filter((row) => (row.current_reviews || []).length).length;
  const ready = items.filter((row) => row.ready_for_promotion).length;
  const changes = items.filter((row) => row.review_progress === "changes_required").length;
  const approvalBlocked = items.filter((row) => (
    destinationReviewApprovalBlockers(row).length > 0
  )).length;
  const approvalReady = items.length - approvalBlocked;
  const allTodos = destinationReviewBatchTodoRows({ ignoreReadiness: true });
  const todos = destinationReviewBatchTodoRows();
  const hasFocus = state.destinationReviewBatchProfileHashes.includes(
    state.destinationReviewFocusProfileHash
  );
  description.textContent = `目前從生活情報分工清單定位：${state.destinationReviewBatchId}，共 ${state.destinationReviewBatchProfileHashes.length} 筆；我的待辦 ${allTodos.length}、可選擇核可 ${approvalReady}、只能要求修正 ${approvalBlocked}、已有真人證據 ${started}、兩人完成 ${ready}、要求修正 ${changes}`;
  openNextButton.hidden = false;
  openNextButton.disabled = !todos.length;
  openNextButton.textContent = todos.length
    ? `${hasFocus ? "開啟下一筆" : "開啟第一筆"}我的待辦（${todos.length} 筆）`
    : allTodos.length && state.destinationReviewReadinessFilter
      ? "目前門檻篩選沒有我的待辦"
      : "此批次我的待辦已完成";
  showTodosButton.hidden = false;
  showTodosButton.disabled = !todos.length;
  if (state.destinationReviewBatchChecklistPath) {
    checklistDownload.href = state.destinationReviewBatchChecklistPath;
    checklistDownload.hidden = false;
    checklistDownload.setAttribute(
      "aria-label",
      `下載 ${state.destinationReviewBatchId} 的全部官方來源與 12 個內容區塊逐項查核表`
    );
  }
}

async function loadDestinationReviewBatch() {
  const requestSequence = ++state.destinationReviewBatchRequestSequence;
  const homeUniversity = state.destinationReviewHomeUniversity;
  if (!state.destinationReviewBatchId || !state.destinationReviewBatchSnapshot) {
    state.destinationReviewBatchProfileHashes = [];
    state.destinationReviewBatchChecklistPath = "";
    state.destinationReviewBatchStale = false;
    state.destinationReviewBatchError = "";
    state.destinationReviewFocusProfileHash = "";
    renderDestinationReviewBatchFilter();
    return;
  }
  state.destinationReviewBatchProfileHashes = [];
  state.destinationReviewBatchChecklistPath = "";
  state.destinationReviewBatchStale = false;
  state.destinationReviewBatchError = "";
  renderDestinationReviewBatchFilter();
  const params = new URLSearchParams({
    home_university: homeUniversity,
    batch_size: String(state.destinationReviewBatchSize),
    expected_snapshot: state.destinationReviewBatchSnapshot,
  });
  try {
    const rows = await requestJson(
      `/admin/destination-profile-review-batches/${encodeURIComponent(state.destinationReviewBatchId)}?${params.toString()}`
    );
    if (
      requestSequence !== state.destinationReviewBatchRequestSequence
      || homeUniversity !== state.destinationReviewHomeUniversity
    ) return;
    state.destinationReviewBatchProfileHashes = rows.map((row) => row.profile_content_hash);
    state.destinationReviewBatchChecklistPath = rows[0]?.batch_checklist_path || "";
    if (!state.destinationReviewBatchProfileHashes.includes(
      state.destinationReviewFocusProfileHash
    )) state.destinationReviewFocusProfileHash = "";
    $("#destination-profile-review-workbench").open = true;
  } catch (error) {
    if (
      requestSequence !== state.destinationReviewBatchRequestSequence
      || homeUniversity !== state.destinationReviewHomeUniversity
    ) return;
    state.destinationReviewBatchStale = [404, 409].includes(error.status);
    if (!state.destinationReviewBatchStale) state.destinationReviewBatchError = error.message;
    state.destinationReviewFocusProfileHash = "";
    $("#destination-profile-review-workbench").open = true;
  }
  renderDestinationReviewBatchFilter();
}

function clearDestinationReviewBatchFilter({ updateUrl = true } = {}) {
  state.destinationReviewBatchRequestSequence += 1;
  state.destinationReviewBatchId = "";
  state.destinationReviewBatchSnapshot = "";
  state.destinationReviewBatchProfileHashes = [];
  state.destinationReviewBatchChecklistPath = "";
  state.destinationReviewBatchStale = false;
  state.destinationReviewBatchError = "";
  state.destinationReviewFocusProfileHash = "";
  if (updateUrl) {
    const url = new URL(window.location.href);
    url.searchParams.delete("destination_home");
    url.searchParams.delete("destination_batch");
    url.searchParams.delete("destination_batch_size");
    url.searchParams.delete("destination_snapshot");
    window.history.replaceState({}, "", url);
  }
  renderDestinationReviewBatchFilter();
}

async function reloadDestinationReviewScope() {
  await loadDestinationReviewBatch();
  await Promise.all([
    loadDestinationProfileReviewQueue(),
    loadDestinationPublicationHistory(),
  ]);
}

function announceDestinationReviewResult(message) {
  if (state.destinationReviewBatchStale) {
    announce(
      `${message} 原生活情報批次因內容指紋或待審成員改變而過期，舊定位未套用；請清除過期批次並重新下載目前版本。`,
      "error"
    );
    return;
  }
  if (state.destinationReviewBatchError) {
    announce(
      `${message} 目前無法重新驗證原生活情報批次，舊定位未套用；請重新整理後重新下載目前版本。`,
      "error"
    );
    return;
  }
  announce(message);
}

async function loadDestinationProfileReviewQueue() {
  const requestSequence = ++state.destinationReviewRequestSequence;
  const homeUniversity = state.destinationReviewHomeUniversity;
  state.destinationProfileReview = null;
  state.destinationProfileReviewError = "";
  renderDestinationProfileReviewSummary();
  try {
    const queue = await requestJson(
      `/admin/destination-profile-review-queue?home_university=${encodeURIComponent(homeUniversity)}`
    );
    if (
      requestSequence !== state.destinationReviewRequestSequence
      || homeUniversity !== state.destinationReviewHomeUniversity
    ) return;
    state.destinationProfileReview = queue;
  } catch (error) {
    if (
      requestSequence !== state.destinationReviewRequestSequence
      || homeUniversity !== state.destinationReviewHomeUniversity
    ) return;
    state.destinationProfileReviewError = error.message;
  }
  renderDestinationProfileReviewSummary();
}

function renderDestinationPublicationHistory() {
  const summary = $("#destination-publication-history-summary");
  const container = $("#destination-publication-history-items");
  const history = state.destinationPublicationHistory;
  if (state.destinationPublicationHistoryError) {
    summary.textContent = `${state.destinationReviewHomeUniversity}公開歷程暫時無法載入：${state.destinationPublicationHistoryError}`;
    container.innerHTML = `<div class="review-error">${escapeHtml(state.destinationPublicationHistoryError)}</div>`;
    return;
  }
  if (!history) {
    summary.textContent = `正在載入${state.destinationReviewHomeUniversity}生活情報公開歷程…`;
    container.innerHTML = '<div class="review-loading">正在載入生活情報公開歷程…</div>';
    return;
  }
  summary.textContent = (
    `${history.home_university || state.destinationReviewHomeUniversity}共有 ${history.profile_with_history_count} 筆生活情報曾執行升級；` +
    `目前 ${history.active_promotion_count} 筆使用已核准公開版本，` +
    `累計 ${history.promotion_event_count} 筆升級與 ${history.rollback_event_count} 筆復原事件。` +
    "所有事件都只新增、不覆寫或刪除。"
  );
  if (!(history.items || []).length) {
    container.innerHTML = `<div class="review-loading">${escapeHtml(history.home_university || state.destinationReviewHomeUniversity)}正式資料目前沒有生活情報升級或復原事件。</div>`;
    return;
  }
  container.innerHTML = history.items.map((item) => {
    const rollbackSubmitting = Boolean(
      state.destinationRollbackSubmitting[item.latest_event_id || item.school_name]
    );
    const promotions = [...(item.promotion_history || [])].reverse();
    const rollbacks = [...(item.rollback_history || [])].reverse();
    return `
      <article class="destination-publication-card" data-publication-school-name="${escapeHtml(item.school_name)}" data-active-promotion-event-id="${escapeHtml(item.active_promotion_event_id || "")}" data-latest-publication-event-id="${escapeHtml(item.latest_event_id || "")}">
        <header>
          <div>
            <p class="eyebrow">${escapeHtml(item.home_university)} · ${escapeHtml(item.current_public_profile.coverage_status)}</p>
            <h4>${escapeHtml(item.school_name)}</h4>
            <p>目前公開內容指紋：<code>${escapeHtml(item.current_public_profile_content_hash.slice(0, 12))}</code></p>
          </div>
          <div class="destination-publication-state ${item.can_rollback ? "is-active" : "is-restored"}">
            <strong>${item.can_rollback ? "目前使用直接升級版本" : "目前為已復原版本"}</strong>
            <span>最後動作：${escapeHtml(item.latest_event_type === "promotion" ? "升級" : "復原")} · ${escapeHtml(formatDate(item.latest_event_at))}</span>
          </div>
        </header>
        ${item.candidate_changed_since_publication ? '<p class="destination-promotion-warning">目前候選內容已改變；學生仍看上一個已核准快照，新候選必須重新雙審。</p>' : ""}
        <details>
          <summary>查看完整升級與復原稽核歷程</summary>
          <div class="destination-publication-audit">
            <section>
              <h5>升級事件（${promotions.length}）</h5>
              ${promotions.length ? `<ol>${promotions.map((event) => `<li><strong>${escapeHtml(event.promoted_by_display_name)} · ${escapeHtml(formatDate(event.promoted_at))}</strong><p>${escapeHtml(event.note)}</p><small>候選 ${escapeHtml(event.source_profile_content_hash.slice(0, 12))} → 公開 ${escapeHtml(event.promoted_profile_content_hash.slice(0, 12))} · ${event.review_event_ids.length} 筆核可</small></li>`).join("")}</ol>` : '<p class="approval-empty">沒有升級事件。</p>'}
            </section>
            <section>
              <h5>復原事件（${rollbacks.length}）</h5>
              ${rollbacks.length ? `<ol>${rollbacks.map((event) => `<li><strong>${escapeHtml(event.rolled_back_by_display_name)} · ${escapeHtml(formatDate(event.rolled_back_at))}</strong><p>${escapeHtml(event.note)}</p><small>撤回 ${escapeHtml(event.previous_profile_content_hash.slice(0, 12))} → 恢復 ${escapeHtml(event.restored_profile_content_hash.slice(0, 12))}</small></li>`).join("")}</ol>` : '<p class="approval-empty">沒有復原事件。</p>'}
            </section>
          </div>
        </details>
        ${item.can_rollback ? `
        <section class="destination-rollback-panel">
          <h5>復原目前直接升級版本</h5>
          <p>復原會回到更早的已核准公開快照；若沒有更早核准版本，會回到目前部分查核候選。舊核可將失效，必須重新雙審。</p>
          <label class="destination-review-note-field">
            <span>復原原因（至少 10 字）</span>
            <textarea data-destination-rollback-note minlength="10" maxlength="2000" placeholder="記錄錯誤、疑義與為何需要立即撤回。"></textarea>
          </label>
          <label class="destination-promotion-confirmation">
            <input type="checkbox" data-destination-rollback-confirm />
            <span>我確認這會立即改變學生目前看到的生活情報公開版本。</span>
          </label>
          <button type="button" class="danger" data-destination-rollback-submit ${rollbackSubmitting ? "disabled" : ""}>${rollbackSubmitting ? "正在復原…" : "確認復原目前版本"}</button>
        </section>` : ""}
      </article>`;
  }).join("");
}

async function loadDestinationPublicationHistory() {
  const requestSequence = ++state.destinationPublicationRequestSequence;
  const homeUniversity = state.destinationReviewHomeUniversity;
  state.destinationPublicationHistory = null;
  state.destinationPublicationHistoryError = "";
  renderDestinationPublicationHistory();
  try {
    const history = await requestJson(
      `/admin/destination-profile-publications?home_university=${encodeURIComponent(homeUniversity)}`
    );
    if (
      requestSequence !== state.destinationPublicationRequestSequence
      || homeUniversity !== state.destinationReviewHomeUniversity
    ) return;
    state.destinationPublicationHistory = history;
  } catch (error) {
    if (
      requestSequence !== state.destinationPublicationRequestSequence
      || homeUniversity !== state.destinationReviewHomeUniversity
    ) return;
    state.destinationPublicationHistoryError = error.message;
  }
  renderDestinationPublicationHistory();
}

function renderWorkflowPublicationHistory() {
  const summary = $("#workflow-publication-history-summary");
  const container = $("#workflow-publication-history-items");
  const history = state.workflowPublicationHistory;
  if (state.workflowPublicationHistoryError) {
    summary.textContent = `公開歷程暫時無法載入：${state.workflowPublicationHistoryError}`;
    container.innerHTML = `<div class="review-error">${escapeHtml(state.workflowPublicationHistoryError)}</div>`;
    return;
  }
  if (!history) {
    summary.textContent = "正在載入申請流程公開歷程…";
    container.innerHTML = '<div class="review-loading">正在載入申請流程公開歷程…</div>';
    return;
  }
  summary.textContent = (
    `共有 ${history.workflow_count} 筆申請流程具有完整雙審發布歷程；` +
    `目前 ${history.rollback_ready_count} 筆可安全恢復舊版，` +
    `累計 ${history.publication_revision_count} 個發布版本與 ${history.rollback_revision_count} 次復原。` +
    "復原只會新增版本，不會覆寫或刪除歷史。"
  );
  if (!(history.items || []).length) {
    container.innerHTML = '<div class="review-loading">正式資料目前沒有具備完整雙審證據的申請流程發布紀錄。</div>';
    return;
  }
  container.innerHTML = history.items.map((item) => {
    const rollbackSubmitting = Boolean(state.workflowRollbackSubmitting[item.workflow_key]);
    const publicationRows = item.publication_history || [];
    const targetOptions = (item.rollback_targets || []).map((target) => (
      `<option value="${escapeHtml(target.revision_id)}">版本 ${escapeHtml(target.version)} · ${escapeHtml(formatDate(target.published_at))} · ${escapeHtml(target.content_hash.slice(0, 12))}</option>`
    )).join("");
    return `
      <article class="workflow-publication-card" data-workflow-publication-key="${escapeHtml(item.workflow_key)}">
        <header>
          <div>
            <p class="eyebrow">${escapeHtml(item.home_university)}${item.program_type ? ` · ${escapeHtml(item.program_type)}` : ""}</p>
            <h4>${escapeHtml(item.school_name)}</h4>
            <p>目前版本 ${escapeHtml(item.current_version)} · 指紋 <code>${escapeHtml(item.current_content_hash.slice(0, 12))}</code></p>
          </div>
          <div class="workflow-publication-state ${item.current_publication_action === "rollback" ? "is-restored" : "is-active"}">
            <strong>${item.current_publication_action === "rollback" ? "目前使用復原後的新版本" : "目前使用一般發布版本"}</strong>
            <span>${escapeHtml(formatDate(item.current_published_at))}</span>
          </div>
        </header>
        ${item.pending_revision_id ? '<p class="destination-promotion-warning">這筆流程仍有待審版本；請先發布或退回，避免復原與待審內容交錯。</p>' : ""}
        <details>
          <summary>查看完整版本稽核歷程（${publicationRows.length}）</summary>
          <ol class="workflow-publication-audit">
            ${publicationRows.map((revision) => `
              <li class="${revision.is_current ? "is-current" : ""}">
                <strong>版本 ${escapeHtml(revision.version)} · ${revision.publication_action === "rollback" ? "安全復原" : "一般發布"}${revision.is_current ? " · 目前公開" : ""}</strong>
                <span>${escapeHtml(revision.published_by)} · ${escapeHtml(formatDate(revision.published_at))}</span>
                ${revision.note ? `<p>${escapeHtml(revision.note)}</p>` : ""}
                <small>指紋 ${escapeHtml(revision.content_hash.slice(0, 12))} · ${escapeHtml(revision.source_count)} 個來源 · ${escapeHtml(revision.step_count)} 個步驟${revision.restored_revision_id ? ` · 恢復自 ${escapeHtml(revision.restored_revision_id)}` : ""}</small>
              </li>`).join("")}
          </ol>
        </details>
        ${item.can_rollback ? `
          <section class="workflow-rollback-panel">
            <h5>安全恢復先前雙審版本</h5>
            <p>系統會把所選快照複製成更高版號並立即成為學生公開內容；原版本與全部雙審、發布、復原歷程都會保留。</p>
            <label class="workflow-rollback-target-field">
              <span>恢復目標</span>
              <select data-workflow-rollback-target>${targetOptions}</select>
            </label>
            <label class="destination-review-note-field">
              <span>復原原因（至少 10 字）</span>
              <textarea data-workflow-rollback-note minlength="10" maxlength="2000" placeholder="記錄目前版本的錯誤、疑義與緊急恢復理由。"></textarea>
            </label>
            <label class="destination-promotion-confirmation">
              <input type="checkbox" data-workflow-rollback-confirm />
              <span>我確認這會立即改變學生目前看到的申請流程；後續修改仍須重新雙審。</span>
            </label>
            <button type="button" class="danger" data-workflow-rollback-submit ${rollbackSubmitting ? "disabled" : ""}>${rollbackSubmitting ? "正在復原…" : "確認恢復所選版本"}</button>
          </section>` : `<p class="workflow-rollback-blocked">${escapeHtml(item.rollback_block_reason || "目前沒有可安全恢復的舊發布版本。")}</p>`}
      </article>`;
  }).join("");
}

async function loadWorkflowPublicationHistory() {
  state.workflowPublicationHistory = null;
  state.workflowPublicationHistoryError = "";
  renderWorkflowPublicationHistory();
  try {
    state.workflowPublicationHistory = await requestJson(
      "/admin/application-workflow-publications"
    );
  } catch (error) {
    state.workflowPublicationHistoryError = error.message;
  }
  renderWorkflowPublicationHistory();
}

async function rollbackApplicationWorkflow(button) {
  const card = button.closest("[data-workflow-publication-key]");
  const workflowKey = card?.dataset.workflowPublicationKey || "";
  const item = (state.workflowPublicationHistory?.items || []).find(
    (row) => row.workflow_key === workflowKey
  );
  if (!card || !item || !item.can_rollback) {
    announce("找不到目前可安全恢復的申請流程版本，請重新整理。", "error");
    return;
  }
  const targetField = $("[data-workflow-rollback-target]", card);
  const restoreRevisionId = targetField?.value || "";
  if (!(item.rollback_targets || []).some((row) => row.revision_id === restoreRevisionId)) {
    announce("請選擇目前可安全恢復的舊發布版本。", "error");
    targetField?.focus();
    return;
  }
  const confirmation = $("[data-workflow-rollback-confirm]", card);
  if (!confirmation?.checked) {
    announce("請先確認復原會立即改變學生目前看到的申請流程。", "error");
    confirmation?.focus();
    return;
  }
  const noteField = $("[data-workflow-rollback-note]", card);
  const note = noteField?.value.trim() || "";
  if (note.length < 10) {
    announce("請留下至少 10 字的申請流程復原原因。", "error");
    noteField?.focus();
    return;
  }
  state.workflowRollbackSubmitting[workflowKey] = true;
  button.disabled = true;
  announce(`正在把 ${item.school_name} 恢復為所選的完整雙審版本…`);
  try {
    const revision = await requestJson("/admin/application-workflow-rollbacks", {
      method: "POST",
      body: JSON.stringify({
        workflow_key: item.workflow_key,
        expected_current_revision_id: item.current_revision_id,
        expected_current_version: item.current_version,
        expected_current_content_hash: item.current_content_hash,
        restore_revision_id: restoreRevisionId,
        note,
      }),
    });
    await Promise.all([loadQueue(), loadWorkflowPublicationHistory()]);
    announce(
      `${item.school_name} 已安全恢復並建立公開版本 ${revision.version}；原版本、原因與完整稽核鏈都已保留。`
    );
  } catch (error) {
    announce(error.message, "error");
    button.disabled = false;
  } finally {
    delete state.workflowRollbackSubmitting[workflowKey];
  }
}

async function submitDestinationProfileReview(button, { advanceToNext = false } = {}) {
  const card = button.closest("[data-destination-profile-hash]");
  const profileHash = card?.dataset.destinationProfileHash || "";
  const schoolName = card?.dataset.destinationSchoolName || "";
  const queue = state.destinationProfileReview;
  const row = (queue?.items || []).find((item) => item.profile_content_hash === profileHash);
  if (!card || !row || !queue) {
    announce("找不到目前待審內容，請重新整理後再試。", "error");
    return;
  }
  const sourceCheckboxes = [...card.querySelectorAll("[data-destination-review-source]")];
  const reviewedSourceUrls = sourceCheckboxes
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.value);
  if (reviewedSourceUrls.length !== sourceCheckboxes.length) {
    announce("請逐一開啟並勾選目前版本的全部官方來源。", "error");
    sourceCheckboxes.find((checkbox) => !checkbox.checked)?.focus();
    return;
  }
  const sectionCheckboxes = [...card.querySelectorAll("[data-destination-review-section]")];
  const reviewedSectionKeys = sectionCheckboxes
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.value);
  if (!sectionCheckboxes.length || reviewedSectionKeys.length !== sectionCheckboxes.length) {
    announce("請逐項核對並勾選全部生活情報內容區塊。", "error");
    sectionCheckboxes.find((checkbox) => !checkbox.checked)?.focus();
    return;
  }
  const noteField = $("[data-destination-review-note]", card);
  const note = noteField?.value.trim() || "";
  if (note.length < 10) {
    announce("請留下至少 10 字的真人審查說明。", "error");
    noteField?.focus();
    return;
  }
  const decision = $("[data-destination-review-decision]", card)?.value || "approve";
  const approvalBlockers = destinationReviewApprovalBlockers(row);
  if (decision === "approve" && approvalBlockers.length) {
    const decisionField = $("[data-destination-review-decision]", card);
    decisionField.value = "changes_required";
    saveDestinationReviewDraftFromCard(card);
    announce(
      `這筆目前只能要求修正：${approvalBlockers.map((blocker) => blocker.label).join("、")}。`,
      "error"
    );
    decisionField.focus();
    return;
  }
  button.disabled = true;
  state.destinationReviewSubmitting[profileHash] = true;
  updateDestinationReviewChecklistProgress(card);
  announce(`正在保存 ${schoolName} 的真人審查證據…`);
  try {
    const event = await requestJson("/admin/destination-profile-reviews", {
      method: "POST",
      body: JSON.stringify({
        home_university: row.home_university,
        school_name: row.school_name,
        expected_snapshot: queue.snapshot_fingerprint,
        expected_profile_content_hash: row.profile_content_hash,
        decision,
        note,
        reviewed_source_urls: reviewedSourceUrls,
        reviewed_section_keys: reviewedSectionKeys,
      }),
    });
    clearDestinationReviewDraft(profileHash);
    delete state.destinationReviewSubmitting[profileHash];
    await reloadDestinationReviewScope();
    const resultMessage = event.decision === "approve"
      ? "獨立審查證據已保存；只有兩位不同真人都完成且沒有修正要求時，才會標示可交下一步處理。"
      : "修正要求已保存；這筆生活情報不會進入下一步，也沒有修改學生目前看到的內容。";
    if (
      advanceToNext
      && !state.destinationReviewBatchStale
      && !state.destinationReviewBatchError
    ) {
      const nextTodo = nextDestinationReviewBatchTodoAfter(profileHash);
      if (openDestinationReviewBatchTodo(nextTodo)) {
        announceDestinationReviewResult(
          `${resultMessage} 已前往此批次下一筆我的待辦；這不代表雙審或發布完成。`
        );
      } else {
        state.destinationReviewSearch = "";
        state.destinationReviewProgressFilter = "mine_unreviewed";
        $("#destination-review-search").value = "";
        $("#destination-review-progress-filter").value = "mine_unreviewed";
        renderDestinationProfileReviewItems();
        const hasOtherTodos = destinationReviewBatchTodoRows({ ignoreReadiness: true }).length > 0;
        announceDestinationReviewResult(
          hasOtherTodos && state.destinationReviewReadinessFilter
            ? `${resultMessage} 目前核可門檻篩選沒有下一筆我的待辦；其他門檻仍可能有待辦。`
            : `${resultMessage} 這個批次目前沒有屬於你的未審項目；這不代表其他審查者、雙審、升級或發布已完成。`
        );
      }
    } else {
      announceDestinationReviewResult(resultMessage);
    }
  } catch (error) {
    announce(error.message, "error");
    button.disabled = false;
  } finally {
    delete state.destinationReviewSubmitting[profileHash];
    updateDestinationReviewChecklistProgress(card);
  }
}

async function rollbackDestinationProfile(button) {
  const card = button.closest("[data-publication-school-name]");
  const schoolName = card?.dataset.publicationSchoolName || "";
  const history = state.destinationPublicationHistory;
  const item = (history?.items || []).find((row) => row.school_name === schoolName);
  if (!card || !item || !item.can_rollback) {
    announce("找不到目前可復原的生活情報公開版本，請重新整理。", "error");
    return;
  }
  const confirmation = $("[data-destination-rollback-confirm]", card);
  if (!confirmation?.checked) {
    announce("請先確認你了解復原會立即改變學生目前看到的版本。", "error");
    confirmation?.focus();
    return;
  }
  const noteField = $("[data-destination-rollback-note]", card);
  const note = noteField?.value.trim() || "";
  if (note.length < 10) {
    announce("請留下至少 10 字的生活情報復原原因。", "error");
    noteField?.focus();
    return;
  }
  const operationKey = item.latest_event_id || schoolName;
  state.destinationRollbackSubmitting[operationKey] = true;
  button.disabled = true;
  announce(`正在復原 ${schoolName} 的上一個公開版本…`);
  try {
    const event = await requestJson("/admin/destination-profile-rollbacks", {
      method: "POST",
      body: JSON.stringify({
        home_university: item.home_university,
        school_name: item.school_name,
        expected_active_promotion_event_id: item.active_promotion_event_id,
        expected_latest_publication_event_id: item.latest_event_id,
        expected_public_profile_content_hash: item.current_public_profile_content_hash,
        note,
      }),
    });
    await reloadDestinationReviewScope();
    announceDestinationReviewResult(
      `${event.school_name} 已復原到上一個公開快照；撤回版本與原因已保存，舊核可不再計入目前候選。`
    );
  } catch (error) {
    announce(error.message, "error");
    button.disabled = false;
  } finally {
    delete state.destinationRollbackSubmitting[operationKey];
  }
}

async function promoteDestinationProfile(button) {
  const card = button.closest("[data-destination-profile-hash]");
  const profileHash = card?.dataset.destinationProfileHash || "";
  const queue = state.destinationProfileReview;
  const row = (queue?.items || []).find((item) => item.profile_content_hash === profileHash);
  if (!card || !row || !queue || !row.ready_for_promotion) {
    announce("找不到目前可升級的雙審內容，請重新整理後再試。", "error");
    return;
  }
  const confirmation = $("[data-destination-promotion-confirm]", card);
  if (!confirmation?.checked) {
    announce("請先確認你了解這會改變學生可見的生活情報狀態。", "error");
    confirmation?.focus();
    return;
  }
  const noteField = $("[data-destination-promotion-note]", card);
  const note = noteField?.value.trim() || "";
  if (note.length < 10) {
    announce("請留下至少 10 字的生活情報升級說明。", "error");
    noteField?.focus();
    return;
  }
  button.disabled = true;
  state.destinationPromotionSubmitting[profileHash] = true;
  announce(`正在升級 ${row.school_name} 的學生可見生活情報…`);
  try {
    const event = await requestJson("/admin/destination-profile-promotions", {
      method: "POST",
      body: JSON.stringify({
        home_university: row.home_university,
        school_name: row.school_name,
        expected_snapshot: queue.snapshot_fingerprint,
        expected_profile_content_hash: row.profile_content_hash,
        note,
      }),
    });
    await reloadDestinationReviewScope();
    announceDestinationReviewResult(
      `${event.school_name} 已依兩位真人核可證據升級為完整查核；申請規則、文件、截止日與通知均未變更。`
    );
  } catch (error) {
    announce(error.message, "error");
    button.disabled = false;
  } finally {
    delete state.destinationPromotionSubmitting[profileHash];
  }
}

function renderWorkflowDeepLinkFilter() {
  const container = $("#workflow-deep-link-filter");
  const batchStageButton = $("#stage-workflow-review-batch");
  const batchReviewButton = $("#open-workflow-review-batch");
  const item = (state.backlog.items || []).find(
    (row) => row.workflow_key === state.workflowDeepLinkKey
  );
  const hasWorkflowLink = Boolean(state.workflowDeepLinkKey && item);
  const hasBatchLink = Boolean(
    state.reviewBatchId && state.reviewBatchWorkflowKeys.length
  );
  batchStageButton.hidden = state.workflowDeepLinkStale || !hasBatchLink;
  batchStageButton.disabled = state.batchStaging;
  batchReviewButton.hidden = true;
  container.hidden = !isBacklogMode()
    || (!state.workflowDeepLinkStale && !hasWorkflowLink && !hasBatchLink);
  if (container.hidden) return;
  container.classList.toggle("is-stale", state.workflowDeepLinkStale);
  $("#clear-workflow-deep-link").textContent = state.workflowDeepLinkStale
    ? "清除過期連結"
    : "回到完整待辦";
  if (state.workflowDeepLinkStale) {
    const expected = state.workflowDeepLinkSnapshot.slice(0, 12);
    $("#workflow-deep-link-description").textContent = `這份分工清單已過期（內容指紋 ${expected}），目前待查核內容或批次成員已變更；舊定位未套用，請重新下載目前版本。`;
    return;
  }
  if (hasBatchLink) {
    const batchKeys = new Set(state.reviewBatchWorkflowKeys);
    const batchItems = (state.backlog.items || []).filter((row) => batchKeys.has(row.workflow_key));
    const stagedCount = batchItems.filter((row) => row.has_pending_revision).length;
    const partiallyApprovedCount = batchItems.filter((row) => (
      Number(row.review_approval_count || 0) > 0
      && !row.review_ready_to_publish
    )).length;
    const readyCount = batchItems.filter((row) => row.review_ready_to_publish).length;
    const unstagedCount = batchItems.filter((row) => !row.has_pending_revision).length;
    batchStageButton.textContent = state.batchStaging
      ? "正在建立批次待審副本…"
      : unstagedCount
        ? `建立目前批次待審副本（${unstagedCount} 筆）`
        : "確認目前批次待審副本";
    batchReviewButton.hidden = unstagedCount > 0;
    batchReviewButton.disabled = state.batchStaging;
    batchReviewButton.textContent = `開始審查此批次（${batchItems.length} 筆）`;
    $("#workflow-deep-link-description").textContent = `目前從分工清單定位：${state.reviewBatchId}，共 ${state.reviewBatchWorkflowKeys.length} 筆流程；已建立待審 ${stagedCount}、待第二位核准 ${partiallyApprovedCount}、已達雙審 ${readyCount}`;
    return;
  }
  $("#workflow-deep-link-description").textContent = `目前從分工清單定位：${item.home_university} × ${item.school_name}`;
}

async function stageWorkflowReviewBatch() {
  if (
    state.batchStaging
    || state.workflowDeepLinkStale
    || !state.reviewBatchId
    || !state.workflowDeepLinkSnapshot
    || !state.reviewBatchWorkflowKeys.length
  ) return;
  const batchKeys = new Set(state.reviewBatchWorkflowKeys);
  const batchItems = (state.backlog.items || []).filter((row) => batchKeys.has(row.workflow_key));
  const unstagedCount = batchItems.filter((row) => !row.has_pending_revision).length;
  const existingCount = batchItems.length - unstagedCount;
  const confirmed = window.confirm(
    `確定要為 ${batchItems.length} 筆流程建立待審副本嗎？其中 ${unstagedCount} 筆尚未建立，已有 ${existingCount} 筆將沿用。這只會建立或重用審查副本，不會核准、發布，也不會改變學生目前看到的內容。`
  );
  if (!confirmed) return;

  state.batchStaging = true;
  renderWorkflowDeepLinkFilter();
  announce("正在建立目前批次的待審副本；學生可見內容不會變更…");
  try {
    const result = await requestJson(
      `/admin/application-workflow-review-batches/${encodeURIComponent(state.reviewBatchId)}/stage`,
      {
        method: "POST",
        body: JSON.stringify({
          expected_snapshot: state.workflowDeepLinkSnapshot,
          batch_size: state.reviewBatchSize,
        }),
      }
    );
    await Promise.all([loadQueue(), loadWorkflowPublicationHistory()]);
    announce(`批次待審副本已確認：新建立 ${result.created_count} 筆、沿用 ${result.existing_count} 筆；沒有核准、發布或變更學生可見內容。`);
  } catch (error) {
    announce(error.message, "error");
  } finally {
    state.batchStaging = false;
    renderWorkflowDeepLinkFilter();
  }
}

async function openWorkflowReviewBatch() {
  if (
    state.workflowDeepLinkStale
    || !state.reviewBatchId
    || !state.workflowDeepLinkSnapshot
    || !state.reviewBatchWorkflowKeys.length
  ) return;
  const batchKeys = new Set(state.reviewBatchWorkflowKeys);
  const batchItems = (state.backlog.items || []).filter(
    (row) => batchKeys.has(row.workflow_key)
  );
  if (
    batchItems.length !== state.reviewBatchWorkflowKeys.length
    || batchItems.some((row) => !row.pending_revision_id)
  ) {
    announce("請先建立目前批次的全部待審副本，再開始批次審查。", "error");
    return;
  }
  state.workflowReviewFocusRevisionId = "";
  state.workflowReviewOwnerFilter = "mine_unreviewed";
  $("#review-status-filter").value = "pending_review";
  $("#workflow-review-owner-filter").value = "mine_unreviewed";
  syncWorkflowReviewControls();
  updateWorkflowReviewLocation();
  await Promise.all([loadQueue(), loadWorkflowPublicationHistory()]);
  announce("已進入目前批次的『我的待辦』；核准一筆後會從這份個人待辦移開，重新整理仍會重新驗證批次。");
}

function renderSummary() {
  if (isBacklogMode()) {
    const items = filteredBacklogItems();
    setSummaryLabels(["符合篩選", "尚未建立", "待審中", "已達雙審"]);
    $("#review-count").textContent = items.length;
    $("#review-unstarted-count").textContent = items.filter((row) => !row.has_pending_revision).length;
    $("#review-partial-count").textContent = items.filter((row) => row.has_pending_revision && !row.review_ready_to_publish).length;
    $("#review-ready-count").textContent = items.filter((row) => row.review_ready_to_publish).length;
    return;
  }
  setSummaryLabels(["目前筆數", "等待第一位", "等待第二位", "可發布"]);
  const revisions = filteredWorkflowRevisions();
  const pending = revisions.filter((row) => row.status === "pending_review");
  $("#review-count").textContent = revisions.length;
  $("#review-unstarted-count").textContent = pending.filter((row) => approvalProgress(row).count === 0).length;
  $("#review-partial-count").textContent = pending.filter((row) => {
    const progress = approvalProgress(row);
    return progress.count > 0 && !progress.ready;
  }).length;
  $("#review-ready-count").textContent = pending.filter((row) => approvalProgress(row).ready).length;
}

function sourceMetadataResearchCandidateMarkup(candidate) {
  if (!candidate) return "";
  const exactSource = candidate.research_status === "verified_exact_source";
  const statusLabel = exactSource
    ? "已核對原始頁面，仍需真人確認"
    : "原始來源失效，需找等價替代頁";
  const proposedMetadata = exactSource
    ? `
      <dl>
        <div><dt>候選標題</dt><dd>${escapeHtml(candidate.proposed_title || "待確認")}</dd></div>
        <div><dt>角色／權威</dt><dd>${escapeHtml(candidate.proposed_role || "待確認")}／${escapeHtml(candidate.proposed_authority || "待確認")}</dd></div>
        <div><dt>候選年度</dt><dd>${escapeHtml(candidate.proposed_effective_academic_year || "仍須逐流程確認")}</dd></div>
      </dl>`
    : '<p class="source-metadata-research-blocker">HTTP 200 只代表請求成功；頁面內容本身顯示找不到，因此沒有可填入的候選中繼資料。</p>';
  const evidence = (candidate.automated_evidence || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  const checks = (candidate.required_human_checks || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  const leads = (candidate.research_leads || [])
    .map((lead) => `
      <li>
        <a href="${escapeHtml(safeExternalUrl(lead.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(lead.label)}</a>
        <span>不可直接替代：${escapeHtml(lead.reason_not_equivalent)}</span>
      </li>`)
    .join("");
  return `
    <section class="source-metadata-research-candidate ${exactSource ? "is-exact-source" : "is-unavailable"}">
      <div class="source-metadata-research-heading">
        <strong>唯讀研究候選</strong>
        <span>${escapeHtml(statusLabel)}</span>
      </div>
      ${proposedMetadata}
      <p>${escapeHtml(candidate.reason_not_ready)}</p>
      <small>研究查核 ${escapeHtml(candidate.checked_at)} · HTTP ${escapeHtml(candidate.transport_http_status)} · 不可自動填入、不建立待審版、不核准、不發布</small>
      <details>
        <summary>查看自動證據與人工檢查事項</summary>
        <h4>自動研究證據</h4>
        <ul>${evidence}</ul>
        <h4>真人仍須確認</h4>
        <ul>${checks}</ul>
        ${leads ? `<h4>安全研究線索</h4><ul class="source-metadata-research-leads">${leads}</ul>` : ""}
      </details>
    </section>`;
}

function renderSourceEvidenceGapSummary() {
  const section = $("#source-evidence-gap-summary");
  const groups = state.backlog.source_metadata_gap_groups || [];
  section.hidden = !isBacklogMode() || !groups.length;
  if (section.hidden) return;

  const activeGroup = groups.find((group) => group.source_url === state.sourceEvidenceUrl);
  $("#clear-source-evidence-filter").hidden = !activeGroup;
  $("#source-evidence-gap-description").textContent = activeGroup
    ? `目前只顯示引用這個網址的 ${activeGroup.workflow_count} 筆流程。清除後可回到完整待辦。`
    : `${state.backlog.source_metadata_gap_reference_count || 0} 筆流程來源證據缺口集中在 ${state.backlog.distinct_source_metadata_gap_url_count || groups.length} 個完全相同的網址。相同網址仍須確認適用於每一份流程；這裡不會批次填值、核准或發布。`;
  $("#source-evidence-gap-groups").innerHTML = groups.map((group, index) => {
    const schools = group.school_names || [];
    const schoolSummary = schools.slice(0, 4).join("、");
    const remainingSchoolCount = Math.max(0, schools.length - 4);
    const active = group.source_url === state.sourceEvidenceUrl;
    return `
      <article class="source-evidence-gap-group${active ? " is-active" : ""}">
        <div>
          <a href="${escapeHtml(safeExternalUrl(group.source_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(group.source_url)}</a>
          <p>${escapeHtml((group.home_universities || []).join("、") || "母校待確認")} · ${escapeHtml(group.workflow_count)} 筆流程 · ${escapeHtml(group.critical_rule_reference_count)} 條關鍵規定引用</p>
          <small>${escapeHtml(schoolSummary || "合作校待確認")}${remainingSchoolCount ? `，另 ${escapeHtml(remainingSchoolCount)} 所` : ""}</small>
          ${sourceMetadataResearchCandidateMarkup(group.research_candidate)}
        </div>
        <div class="source-evidence-gap-actions">
          <a class="source-evidence-export" href="/admin/application-workflow-review-backlog/source-evidence.csv?source_url=${escapeHtml(encodeURIComponent(group.source_url))}&amp;expected_snapshot=${escapeHtml(encodeURIComponent(group.source_evidence_snapshot_fingerprint))}" download>下載唯讀 CSV</a>
          <button type="button" class="secondary" data-source-evidence-group-index="${escapeHtml(index)}" ${active ? "disabled" : ""}>${active ? "目前篩選" : `查看 ${escapeHtml(group.workflow_count)} 筆流程`}</button>
        </div>
      </article>`;
  }).join("");
}

function renderSourceReplacementCandidateSummary() {
  const section = $("#source-replacement-candidate-summary");
  const workflowCount = Number(
    state.backlog.workflows_with_source_replacement_candidates || 0
  );
  const candidateCount = Number(
    state.backlog.source_replacement_candidate_count || 0
  );
  section.hidden = !isBacklogMode() || workflowCount === 0 || candidateCount === 0;
  if (section.hidden) return;
  const candidateItems = (state.backlog.items || []).filter(
    (item) => Number(item.source_replacement_candidate_count || 0) > 0
  );
  const strongCount = candidateItems.reduce(
    (total, item) => total + Number(item.strong_source_replacement_candidate_count || 0),
    0
  );
  const conditionalCount = candidateItems.reduce(
    (total, item) => total + Number(item.conditional_source_replacement_candidate_count || 0),
    0
  );
  const transportBlockedCount = Number(
    state.backlog.transport_blocked_source_replacement_candidate_count || 0
  );
  $("#source-replacement-candidate-summary-description").textContent = (
    `目前 ${workflowCount} 筆流程共有 ${candidateCount} 個研究候選（強候選 ${strongCount}、條件候選 ${conditionalCount}、傳輸阻擋 ${transportBlockedCount}）。` +
    "請先篩選，再由真人逐頁確認後建立或開啟待審版本。"
  );
  const download = $("#download-source-replacement-candidates");
  const exportPath = "/admin/application-workflow-source-replacement-review-queue.csv";
  download.href = state.workflowDeepLinkSnapshot
    ? `${exportPath}?expected_snapshot=${encodeURIComponent(state.workflowDeepLinkSnapshot)}`
    : exportPath;
  download.setAttribute(
    "aria-label",
    `下載 ${candidateCount} 個來源候選的唯讀人工審核清單`
  );
  const button = $("#filter-source-replacement-candidates");
  const active = state.backlogGapFilter === "source_replacement_candidate";
  button.disabled = active;
  button.textContent = active ? `目前顯示 ${workflowCount} 筆` : `顯示 ${workflowCount} 筆流程`;
}

function renderQueue() {
  const container = $("#review-queue");
  renderReleaseReadiness();
  renderWorkflowDeepLinkFilter();
  renderWorkflowReviewFocusFilter();
  renderSourceReplacementCandidateSummary();
  renderSourceEvidenceGapSummary();
  container.setAttribute("aria-busy", state.loading ? "true" : "false");
  if (state.loading) {
    container.innerHTML = '<div class="review-loading">正在讀取流程版本…</div>';
    return;
  }
  if (state.error) {
    container.innerHTML = `<div class="review-error">${escapeHtml(state.error)}</div>`;
    return;
  }
  renderSummary();
  if (isBacklogMode()) {
    const items = filteredBacklogItems();
    const visible = items.slice(0, state.backlogVisibleLimit);
    const remaining = items.length - visible.length;
    container.innerHTML = visible.length
      ? visible.map(renderBacklogItem).join("") + (remaining > 0 ? `
        <div class="backlog-more">
          <span>目前顯示 ${escapeHtml(visible.length)} / ${escapeHtml(items.length)} 筆</span>
          <button type="button" class="secondary" data-backlog-more>再顯示 ${escapeHtml(Math.min(25, remaining))} 筆</button>
        </div>` : "")
      : '<div class="review-empty">目前沒有符合這組篩選條件的既有流程。</div>';
    return;
  }
  const revisions = filteredWorkflowRevisions();
  container.innerHTML = revisions.length
    ? revisions.map(renderRevision).join("")
    : '<div class="review-empty">這個狀態目前沒有流程版本。</div>';
  container.querySelectorAll("[data-revision-id]").forEach((item) => {
    updateApprovalChecklist(item);
    updateApplicabilityEditorState(item);
  });
}

function renderBacklogHomeUniversities() {
  const select = $("#backlog-home-university");
  select.innerHTML = '<option value="">全部母校</option>' + (state.backlog.home_universities || [])
    .map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`)
    .join("");
  select.value = state.backlogHomeUniversity;
  if (select.value !== state.backlogHomeUniversity) {
    state.backlogHomeUniversity = "";
  }
}

async function loadQueueReleaseReadiness(requestSequence) {
  try {
    const report = await requestJson("/admin/web-release-readiness");
    if (requestSequence !== state.queueRequestSequence) return;
    state.releaseReadiness = report;
    renderReleaseReadiness();
  } catch (error) {
    if (requestSequence !== state.queueRequestSequence) return;
    state.releaseReadiness = null;
    renderReleaseReadiness();
    const section = $("#release-readiness");
    section.dataset.status = "blocked";
    section.setAttribute("aria-busy", "false");
    $("#release-readiness-status").textContent = "檢查失敗";
    $("#release-readiness-description").textContent = error.message;
  }
}

async function loadQueue() {
  const requestSequence = ++state.queueRequestSequence;
  state.loading = true;
  state.error = "";
  state.releaseReadiness = null;
  $("#backlog-filters").hidden = !isBacklogMode();
  syncWorkflowReviewControls();
  renderQueue();
  announce("");
  const status = $("#review-status-filter").value;
  try {
    if (status === "backlog") {
      let backlog;
      const hasReviewDeepLink = Boolean(
        state.workflowDeepLinkKey || state.reviewBatchId
      );
      if (hasReviewDeepLink && state.workflowDeepLinkSnapshot) {
        try {
          if (state.reviewBatchId) {
            const batchPath = `/admin/application-workflow-review-batches/${encodeURIComponent(state.reviewBatchId)}?batch_size=${encodeURIComponent(state.reviewBatchSize)}&expected_snapshot=${encodeURIComponent(state.workflowDeepLinkSnapshot)}`;
            const batchRows = await requestJson(batchPath);
            state.reviewBatchWorkflowKeys = batchRows.map((row) => row.workflow_key);
          } else {
            state.reviewBatchWorkflowKeys = [];
          }
          backlog = await requestJson(`/admin/application-workflow-review-backlog?expected_snapshot=${encodeURIComponent(state.workflowDeepLinkSnapshot)}`);
          state.workflowDeepLinkStale = false;
        } catch (error) {
          if (![404, 409].includes(error.status)) throw error;
          state.workflowDeepLinkStale = true;
          state.reviewBatchWorkflowKeys = [];
          backlog = await requestJson("/admin/application-workflow-review-backlog");
        }
      } else {
        backlog = await requestJson("/admin/application-workflow-review-backlog");
        state.workflowDeepLinkStale = Boolean(state.reviewBatchId);
        state.reviewBatchWorkflowKeys = [];
      }
      if (requestSequence !== state.queueRequestSequence) return;
      state.backlog = backlog;
      state.backlogVisibleLimit = 25;
      if (
        state.workflowDeepLinkKey
        && !state.workflowDeepLinkStale
        && !(backlog.items || []).some(
          (row) => row.workflow_key === state.workflowDeepLinkKey
        )
      ) {
        state.workflowDeepLinkKey = "";
        state.reviewBatchId = "";
        state.reviewBatchWorkflowKeys = [];
        state.workflowDeepLinkSnapshot = "";
        const url = new URL(window.location.href);
        url.searchParams.delete("workflow_key");
        url.searchParams.delete("review_batch");
        url.searchParams.delete("batch_size");
        url.searchParams.delete("review_snapshot");
        window.history.replaceState({}, "", url);
        announce("分工清單指定的流程已不在目前待辦，已回到完整清單。", "error");
      } else if (state.workflowDeepLinkStale) {
        announce("這份雙人審查分工清單已過期，舊流程定位未套用；請重新下載目前版本。", "error");
      }
      const activeGroup = (backlog.source_metadata_gap_groups || []).find(
        (group) => group.source_url === state.sourceEvidenceUrl
      );
      state.sourceEvidenceWorkflowKeys = activeGroup?.workflow_keys || [];
      if (!activeGroup) state.sourceEvidenceUrl = "";
      renderBacklogHomeUniversities();
    } else {
      const hasPendingBatchContext = Boolean(
        status === "pending_review" && state.reviewBatchId
      );
      const canValidatePendingBatch = Boolean(
        hasPendingBatchContext && state.workflowDeepLinkSnapshot
      );
      const batchResultPromise = canValidatePendingBatch
        ? requestJson(
          `/admin/application-workflow-review-batches/${encodeURIComponent(state.reviewBatchId)}?batch_size=${encodeURIComponent(state.reviewBatchSize)}&expected_snapshot=${encodeURIComponent(state.workflowDeepLinkSnapshot)}`
        ).then((rows) => ({ rows })).catch((error) => ({ error }))
        : Promise.resolve(null);
      const [revisions, sourceReplacementCandidates, batchResult] = await Promise.all([
        requestJson(`/admin/application-workflow-revisions${status ? `?status=${encodeURIComponent(status)}` : ""}`),
        requestJson("/admin/application-workflow-source-replacement-candidates"),
        batchResultPromise,
      ]);
      if (requestSequence !== state.queueRequestSequence) return;
      state.revisions = revisions;
      state.sourceReplacementCandidates = sourceReplacementCandidates;
      if (hasPendingBatchContext) {
        if (!canValidatePendingBatch) {
          state.workflowDeepLinkStale = true;
          state.reviewBatchWorkflowKeys = [];
          state.workflowReviewFocusRevisionId = "";
          updateWorkflowReviewLocation();
        } else if (batchResult?.error) {
          if (![404, 409].includes(batchResult.error.status)) {
            throw batchResult.error;
          }
          state.workflowDeepLinkStale = true;
          state.reviewBatchWorkflowKeys = [];
          state.workflowReviewFocusRevisionId = "";
          updateWorkflowReviewLocation();
          announce("這份批次審查範圍已過期，舊範圍未套用；目前顯示全部待審版本。", "error");
        } else {
          state.workflowDeepLinkStale = false;
          state.reviewBatchWorkflowKeys = (batchResult?.rows || []).map(
            (row) => row.workflow_key
          );
          const focusedRevision = state.revisions.find(
            (revision) => revision.id === state.workflowReviewFocusRevisionId
          );
          if (
            state.workflowReviewFocusRevisionId
            && (
              !focusedRevision
              || !state.reviewBatchWorkflowKeys.includes(focusedRevision.workflow_key)
              || (
                state.workflowReviewOwnerFilter === "mine_unreviewed"
                && !workflowReviewBatchTodoRevisions().some(
                  (revision) => revision.id === state.workflowReviewFocusRevisionId
                )
              )
            )
          ) {
            state.workflowReviewFocusRevisionId = "";
            updateWorkflowReviewLocation();
          }
        }
      }
    }
  } catch (error) {
    if (requestSequence !== state.queueRequestSequence) return;
    if (status === "backlog") {
      state.backlog = { items: [], total_count: 0, unstaged_count: 0, staged_count: 0, home_universities: [] };
      state.sourceEvidenceWorkflowKeys = [];
      state.sourceEvidenceUrl = "";
    } else {
      state.revisions = [];
      state.sourceReplacementCandidates = [];
    }
    state.releaseReadiness = null;
    state.error = error.message;
    announce(error.message, "error");
  } finally {
    if (requestSequence !== state.queueRequestSequence) return;
    state.loading = false;
    renderQueue();
    // Readiness is an independent, read-only report. Commands continue to
    // validate their exact snapshot, source hashes and human approvals on the
    // server; a slow report must not hide an already validated review queue.
    if (!state.error) void loadQueueReleaseReadiness(requestSequence);
    if (state.workflowDeepLinkKey && !state.workflowDeepLinkStale && isBacklogMode()) {
      requestAnimationFrame(() => {
        const target = [...document.querySelectorAll("[data-workflow-key]")].find(
          (node) => node.dataset.workflowKey === state.workflowDeepLinkKey
        );
        target?.focus({ preventScroll: true });
        target?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } else if (state.workflowReviewFocusRevisionId && !isBacklogMode()) {
      requestAnimationFrame(() => {
        const target = document.querySelector(
          `[data-revision-id="${CSS.escape(state.workflowReviewFocusRevisionId)}"]`
        );
        if (!target) return;
        target.classList.add("is-focus-target");
        target.focus({ preventScroll: true });
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }
}

async function handleBacklogAction(button) {
  const item = button.closest("[data-workflow-key]");
  const workflowKey = item?.dataset.workflowKey;
  const action = button.dataset.backlogAction;
  if (!workflowKey || !action) return;
  if (action === "open") {
    const pendingRevisionId = state.backlog.items.find(
      (row) => row.workflow_key === workflowKey
    )?.pending_revision_id;
    $("#review-status-filter").value = "pending_review";
    state.workflowReviewOwnerFilter = "";
    state.workflowReviewFocusRevisionId = pendingRevisionId || "";
    clearWorkflowBacklogLocationState();
    updateWorkflowReviewLocation();
    await Promise.all([loadQueue(), loadWorkflowPublicationHistory()]);
    if (pendingRevisionId) {
      const target = document.querySelector(
        `[data-revision-id="${CSS.escape(pendingRevisionId)}"]`
      );
      if (target) {
        target.classList.add("is-focus-target");
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
    announce("已切換到待審佇列；請開啟對應版本逐欄核對。");
    return;
  }
  state.staging[workflowKey] = true;
  renderQueue();
  announce("正在複製既有流程到待審區…");
  try {
    const revision = await requestJson(`/admin/application-workflow-review-backlog/${encodeURIComponent(workflowKey)}/stage`, {
      method: "POST",
    });
    state.backlog.items = state.backlog.items.map((row) => row.workflow_key === workflowKey
      ? { ...row, has_pending_revision: true, pending_revision_id: revision.id }
      : row);
    state.backlog.staged_count = state.backlog.items.filter((row) => row.has_pending_revision).length;
    state.backlog.unstaged_count = state.backlog.items.length - state.backlog.staged_count;
    await loadWorkflowPublicationHistory();
    announce("待審版本已建立；學生目前看到的內容沒有變更。");
  } catch (error) {
    announce(error.message, "error");
  } finally {
    delete state.staging[workflowKey];
    renderQueue();
  }
}

async function loadComparison(button) {
  const item = button.closest("[data-revision-id]");
  const revisionId = item?.dataset.revisionId;
  if (!revisionId || state.comparisonLoading[revisionId]) return;
  const scrollPosition = window.scrollY;
  state.comparisonLoading[revisionId] = true;
  delete state.comparisonErrors[revisionId];
  renderQueue();
  announce("正在載入基準與候選版本對照…");
  try {
    state.comparisons[revisionId] = await requestJson(
      `/admin/application-workflow-revisions/${encodeURIComponent(revisionId)}/comparison`
    );
    announce("版本對照已載入；請逐欄核對後再決定是否核准。");
  } catch (error) {
    state.comparisonErrors[revisionId] = error.message;
    announce(error.message, "error");
  } finally {
    delete state.comparisonLoading[revisionId];
    renderQueue();
    window.scrollTo({ top: scrollPosition });
  }
}

async function saveApplicability(button) {
  const item = button.closest("[data-revision-id]");
  const revisionId = item?.dataset.revisionId;
  const revision = state.revisions.find((row) => row.id === revisionId);
  if (!revisionId || !revision) return;
  const hadValidatedBatchContext = Boolean(
    $("#review-status-filter").value === "pending_review"
    && state.reviewBatchId
    && state.workflowDeepLinkSnapshot
    && !state.workflowDeepLinkStale
  );

  const academicYearInput = $("[data-applicability-academic-year]", item);
  const applicationRoundInput = $("[data-applicability-application-round]", item);
  const noteInput = $("[data-applicability-note]", item);
  const academicYear = academicYearInput?.value.trim() || "";
  const note = noteInput?.value.trim() || "";
  if (!/^\d{3}$/.test(academicYear)) {
    announce("流程適用學年度必須是 3 位數民國學年度，例如 115。", "error");
    academicYearInput?.focus();
    return;
  }
  if (!note) {
    announce("請先填寫本次修正說明。", "error");
    noteInput?.focus();
    return;
  }

  const sourceUpdates = [];
  for (const row of item.querySelectorAll("[data-applicability-source-row]")) {
    const checked = $("[data-applicability-source]", row)?.checked;
    if (!checked) continue;
    const sourceYearInput = $("[data-source-academic-year]", row);
    const sourceYear = sourceYearInput?.value.trim() || "";
    if (!/^\d{3}$/.test(sourceYear)) {
      announce("每個勾選的官方來源都必須填寫 3 位數適用學年度。", "error");
      sourceYearInput?.focus();
      return;
    }
    const currentSourceUrl = row.dataset.sourceUrl || "";
    const sourceMetadataComplete = row.dataset.sourceMetadataComplete === "true";
    const replacementInput = $("[data-source-replacement-url]", row);
    const replacementSourceUrl = replacementInput?.value.trim() || "";
    if (replacementSourceUrl && !replacementSourceUrl.toLocaleLowerCase().startsWith("https://")) {
      announce("安全替代網址必須使用 HTTPS。", "error");
      replacementInput?.focus();
      return;
    }
    if (!currentSourceUrl.toLocaleLowerCase().startsWith("https://") && !replacementSourceUrl) {
      announce("非 HTTPS 官方來源必須先填入已核實的安全替代網址。", "error");
      replacementInput?.focus();
      return;
    }
    const sourceTitleInput = $("[data-source-title]", row);
    const sourceRoleInput = $("[data-source-role]", row);
    const sourceAuthorityInput = $("[data-source-authority]", row);
    const sourceTitle = sourceTitleInput?.value.trim() || "";
    const sourceRole = sourceRoleInput?.value || "";
    const sourceAuthority = sourceAuthorityInput?.value || "";
    if (!sourceMetadataComplete && (!sourceTitle || !sourceRole || !sourceAuthority)) {
      announce("尚未建立證據資料的來源必須填寫來源名稱、角色與權威層級。", "error");
      (!sourceTitle ? sourceTitleInput : (!sourceRole ? sourceRoleInput : sourceAuthorityInput))?.focus();
      return;
    }
    sourceUpdates.push({
      source_url: currentSourceUrl,
      replacement_source_url: replacementSourceUrl && replacementSourceUrl !== currentSourceUrl
        ? replacementSourceUrl
        : null,
      effective_academic_year: sourceYear,
      application_round: $("[data-source-application-round]", row)?.value.trim() || null,
      title: sourceMetadataComplete ? null : sourceTitle,
      role: sourceMetadataComplete ? null : sourceRole,
      authority: sourceMetadataComplete ? null : sourceAuthority,
    });
  }
  if ((revision.review_approvals || []).length && !window.confirm("這個候選已有核准。儲存修正後會清除全部核准並要求兩人重新審查，確定繼續？")) return;

  button.disabled = true;
  announce("正在儲存適用範圍修正…");
  try {
    const updated = await requestJson(`/admin/application-workflow-revisions/${encodeURIComponent(revisionId)}/applicability`, {
      method: "PATCH",
      body: JSON.stringify({
        expected_content_hash: revision.content_hash,
        academic_year: academicYear,
        application_round: applicationRoundInput?.value.trim() || null,
        source_updates: sourceUpdates,
        note,
      }),
    });
    clearWorkflowApplicabilityDraft(revision);
    state.revisions = state.revisions.map((row) => row.id === revisionId ? updated : row);
    delete state.comparisons[revisionId];
    delete state.comparisonErrors[revisionId];
    if (hadValidatedBatchContext) {
      await loadQueue();
      if (state.error) {
        state.workflowDeepLinkStale = true;
        state.reviewBatchWorkflowKeys = [];
        state.workflowReviewFocusRevisionId = "";
        updateWorkflowReviewLocation();
        renderQueue();
        announce(
          "待審修正已保存，但目前無法重新驗證原批次；為避免沿用未確認範圍，批次與單筆導覽已停用。請重新整理後下載目前分工清單。",
          "error"
        );
        return;
      }
      if (state.workflowDeepLinkStale) {
        announce(
          "待審修正已保存；學生目前看到的內容仍未變更。候選內容已改變審查指紋，原批次因此過期，單筆定位已清除；請清除過期批次並重新下載目前分工清單。",
          "error"
        );
        return;
      }
    }
    renderQueue();
    announce("待審修正已保存；既有核准已清除，學生目前看到的內容仍未變更。");
  } catch (error) {
    announce(error.message, "error");
    button.disabled = false;
  }
}

function applySourceReplacementCandidate(button) {
  const row = button.closest("[data-applicability-source-row]");
  const input = row ? $("[data-source-replacement-url]", row) : null;
  const candidateUrl = button.dataset.candidateUrl?.trim() || "";
  if (button.dataset.canPrefill !== "true") {
    announce("這個候選未通過 HTTPS 最終傳輸檢查，系統不允許填入待審欄位。", "error");
    return;
  }
  if (!input || !candidateUrl) {
    announce("這個候選無法對應到待審來源欄位，請重新載入。", "error");
    return;
  }
  const currentValue = input.value.trim();
  if (currentValue && currentValue !== candidateUrl) {
    announce("替代網址欄位已有其他內容；為避免覆寫，請先自行確認並清除。", "error");
    input.focus();
    return;
  }
  input.value = candidateUrl;
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.focus();
  announce("候選網址只已填入尚未儲存的欄位；請親自核對、勾選來源並填完說明後再決定是否儲存。");
}

async function handleAction(button) {
  const item = button.closest("[data-revision-id]");
  const revisionId = item?.dataset.revisionId;
  const action = button.dataset.reviewAction;
  const revision = state.revisions.find((row) => row.id === revisionId);
  const advanceToNext = Boolean(
    action === "approve"
    && button.hasAttribute("data-approval-submit-next")
    && state.reviewBatchId
    && !state.workflowDeepLinkStale
    && revision
    && state.reviewBatchWorkflowKeys.includes(revision.workflow_key)
  );
  const note = $("[data-review-note]", item)?.value.trim() || "";
  if (!revisionId || !action || !revision) return;
  if (!note) {
    announce("請先填寫本次查核說明。", "error");
    $("[data-review-note]", item)?.focus();
    return;
  }
  let payload = { note };
  if (action === "approve") {
    const sourceCheckboxes = [...item.querySelectorAll("[data-approval-source]")];
    const ruleCheckboxes = [...item.querySelectorAll("[data-approval-rule]")];
    const reviewedSourceUrls = sourceCheckboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.dataset.sourceUrl);
    if (!sourceCheckboxes.length || reviewedSourceUrls.length !== sourceCheckboxes.length) {
      announce("請先親自開啟並逐頁勾選這個版本的全部官方來源。", "error");
      sourceCheckboxes.find((checkbox) => !checkbox.checked)?.focus();
      return;
    }
    const reviewedRuleKeys = ruleCheckboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.dataset.ruleKey);
    if (!ruleCheckboxes.length || reviewedRuleKeys.length !== ruleCheckboxes.length) {
      announce("請先逐項核對並勾選這個版本的流程適用範圍、全部步驟與文件。", "error");
      ruleCheckboxes.find((checkbox) => !checkbox.checked)?.focus();
      return;
    }
    payload = {
      expected_content_hash: revision.content_hash,
      reviewed_source_urls: reviewedSourceUrls,
      reviewed_rule_keys: reviewedRuleKeys,
      note,
    };
  }
  if (action === "reject" && !window.confirm("確定退回這個版本？退回後必須重新建立待審版本。")) return;
  button.disabled = true;
  if (action === "approve") {
    item.querySelectorAll('[data-review-action="approve"]').forEach((approveButton) => {
      approveButton.dataset.approvalSubmitting = "true";
    });
    updateApprovalChecklist(item);
  }
  announce("正在保存審查結果…");
  try {
    const result = await requestJson(`/admin/application-workflow-revisions/${encodeURIComponent(revisionId)}/${action}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    clearWorkflowReviewDraft(revision);
    clearWorkflowApplicabilityDraft(revision);
    if (
      ["publish", "reject"].includes(action)
      && state.workflowReviewFocusRevisionId === revisionId
    ) {
      state.workflowReviewFocusRevisionId = "";
      updateWorkflowReviewLocation();
    }
    await Promise.all([loadQueue(), loadWorkflowPublicationHistory()]);
    const approveMessage = approvalProgress(result).ready
      ? "第二份獨立核准已保存；目前已達兩人發布門檻。"
      : "核准已保存；仍須由另一個管理帳號獨立核對。";
    if (action === "approve" && advanceToNext) {
      if (state.error) {
        announce(`${approveMessage} 批次重新載入失敗，未自動前往下一筆；請重新整理並重新驗證批次。`, "error");
      } else if (state.workflowDeepLinkStale) {
        announce(`${approveMessage} 原申請流程批次已過期，舊定位未套用；請重新下載目前分工清單。`, "error");
      } else {
        const nextTodo = nextWorkflowReviewBatchTodoAfter(revision.workflow_key);
        if (nextTodo) {
          focusWorkflowReviewRevision(nextTodo);
          announce(`${approveMessage} 已前往此批次下一筆我的待辦；這不代表另一位審查者、雙審或發布已完成。`);
        } else {
          state.workflowReviewFocusRevisionId = "";
          state.workflowReviewOwnerFilter = "mine_unreviewed";
          $("#workflow-review-owner-filter").value = "mine_unreviewed";
          updateWorkflowReviewLocation();
          renderQueue();
          const hasOtherTodos = workflowReviewBatchTodoRevisions({ ignoreReadiness: true }).length > 0;
          announce(
            hasOtherTodos && state.workflowReviewReadinessFilter
              ? `${approveMessage} 目前資料門檻篩選沒有下一筆我的待辦；其他門檻仍可能有待辦。`
              : `${approveMessage} 此批次目前沒有屬於你的未核准項目；這不代表另一位審查者、雙審或發布已完成。`
          );
        }
      }
    } else {
      announce({ approve: approveMessage, publish: "版本已正式發布，受影響學生的內容更新通知將依設定產生。", reject: "版本已退回，不會影響學生目前看到的流程。" }[action]);
    }
  } catch (error) {
    announce(error.message, "error");
    if (action === "approve") {
      item.querySelectorAll('[data-review-action="approve"]').forEach((approveButton) => {
        delete approveButton.dataset.approvalSubmitting;
      });
      updateApprovalChecklist(item);
    }
    else button.disabled = false;
  }
}

async function initialize() {
  try {
    state.admin = await requestJson("/admin/session");
    $("#reviewer-name").textContent = state.admin.display_name;
    $("#reviewer-email").textContent = state.admin.email;
  } catch (error) {
    $("#review-main").innerHTML = `<div class="review-error">${escapeHtml(error.message)} <a href="/">返回學生版登入</a></div>`;
    return;
  }
  $("#review-status-filter").value = initialWorkflowReviewStatus;
  syncWorkflowReviewControls();
  if (
    initialWorkflowReviewStatus === "pending_review"
    && state.reviewBatchId
    && state.workflowDeepLinkSnapshot
  ) {
    state.workflowReviewOwnerFilter = "mine_unreviewed";
    $("#workflow-review-owner-filter").value = "mine_unreviewed";
  }
  $("#destination-review-home-university").value = state.destinationReviewHomeUniversity;
  await loadDestinationReviewBatch();
  // Render the selected review queue before the independent history panels.
  // Their read requests share the governance snapshot lock; starting all of
  // them together can leave a batch deep link hidden behind unrelated work.
  await loadQueue();
  await Promise.all([
    loadWorkflowPublicationHistory(),
    loadWorkflowIssueReports(),
    loadDestinationProfileReviewQueue(),
    loadDestinationPublicationHistory(),
  ]);
}

$("#reload-review-queue").addEventListener("click", async () => {
  await loadDestinationReviewBatch();
  await Promise.all([
    loadQueue(),
    loadWorkflowPublicationHistory(),
    loadWorkflowIssueReports(),
    loadDestinationProfileReviewQueue(),
    loadDestinationPublicationHistory(),
  ]);
});
$("#review-status-filter").addEventListener("change", async (event) => {
  state.workflowReviewOwnerFilter = "";
  $("#workflow-review-owner-filter").value = "";
  if (event.target.value !== "pending_review") {
    state.workflowReviewFocusRevisionId = "";
  }
  if (event.target.value !== "backlog") clearWorkflowBacklogLocationState();
  updateWorkflowReviewLocation();
  await loadQueue();
});
$("#workflow-issue-report-status-filter").addEventListener("change", async (event) => {
  state.workflowIssueReportStatus = event.target.value;
  await loadWorkflowIssueReports();
});
$("#reload-workflow-issue-reports").addEventListener("click", loadWorkflowIssueReports);
$("#workflow-issue-report-queue").addEventListener("click", (event) => {
  const button = event.target.closest("[data-workflow-issue-review]");
  if (button) reviewWorkflowIssueReport(button);
});
$("#workflow-review-owner-filter").addEventListener("change", (event) => {
  state.workflowReviewOwnerFilter = event.target.value;
  if (state.reviewBatchId && state.workflowReviewFocusRevisionId) {
    state.workflowReviewFocusRevisionId = "";
    updateWorkflowReviewLocation();
  }
  renderQueue();
});
$("#workflow-review-readiness-filter").addEventListener("change", (event) => {
  state.workflowReviewReadinessFilter = event.target.value;
  if (state.reviewBatchId && state.workflowReviewFocusRevisionId) {
    state.workflowReviewFocusRevisionId = "";
    updateWorkflowReviewLocation();
  }
  renderQueue();
});
$("#open-next-workflow-review").addEventListener("click", openNextWorkflowReviewBatchTodo);
$("#show-workflow-review-batch").addEventListener("click", showWorkflowReviewBatchTodos);
$("#clear-workflow-review-focus").addEventListener("click", () => {
  const hadBatchContext = Boolean(state.reviewBatchId);
  state.workflowReviewFocusRevisionId = "";
  if (hadBatchContext) clearWorkflowBacklogLocationState();
  updateWorkflowReviewLocation();
  renderQueue();
  announce(hadBatchContext
    ? "已離開批次範圍，顯示目前符合審查者篩選的全部待審版本。"
    : "已清除單一 revision 定位，顯示目前符合審查者篩選的全部待審版本。"
  );
});
$("#destination-review-home-university").addEventListener("change", (event) => {
  state.destinationReviewHomeUniversity = event.target.value;
  clearDestinationReviewBatchFilter();
  state.destinationReviewSearch = "";
  state.destinationReviewProgressFilter = "";
  state.destinationReviewReadinessFilter = "";
  state.destinationReviewVisibleLimit = 10;
  $("#destination-review-search").value = "";
  $("#destination-review-progress-filter").value = "";
  $("#destination-review-readiness-filter").value = "";
  Promise.all([
    loadDestinationProfileReviewQueue(),
    loadDestinationPublicationHistory(),
  ]);
});
$("#open-next-destination-review").addEventListener(
  "click",
  openNextDestinationReviewBatchTodo
);
$("#show-destination-review-batch").addEventListener(
  "click",
  showDestinationReviewBatchTodos
);
$("#clear-destination-review-batch").addEventListener("click", () => {
  clearDestinationReviewBatchFilter();
  state.destinationReviewVisibleLimit = 10;
  renderDestinationProfileReviewItems();
  announce("已清除生活情報分工批次定位，回到這所母校的完整待辦。");
});
$("#destination-review-search").addEventListener("input", (event) => {
  state.destinationReviewFocusProfileHash = "";
  state.destinationReviewSearch = event.target.value;
  state.destinationReviewVisibleLimit = 10;
  renderDestinationProfileReviewItems();
});
$("#destination-review-progress-filter").addEventListener("change", (event) => {
  state.destinationReviewFocusProfileHash = "";
  state.destinationReviewProgressFilter = event.target.value;
  state.destinationReviewVisibleLimit = 10;
  renderDestinationProfileReviewItems();
});
$("#destination-review-readiness-filter").addEventListener("change", (event) => {
  state.destinationReviewFocusProfileHash = "";
  state.destinationReviewReadinessFilter = event.target.value;
  state.destinationReviewVisibleLimit = 10;
  renderDestinationProfileReviewItems();
});
$("#destination-profile-review-items").addEventListener("click", (event) => {
  const detailSummary = event.target.closest(".destination-review-detail > summary");
  if (detailSummary) {
    const card = detailSummary.closest("[data-destination-profile-hash]");
    const profileHash = card?.dataset.destinationProfileHash || "";
    if (
      !state.destinationReviewBatchStale
      && !state.destinationReviewBatchError
      && state.destinationReviewBatchProfileHashes.includes(profileHash)
    ) {
      state.destinationReviewFocusProfileHash = profileHash;
      renderDestinationReviewBatchFilter();
    }
    return;
  }
  const moreButton = event.target.closest("[data-destination-review-more]");
  if (moreButton) {
    state.destinationReviewVisibleLimit += 10;
    renderDestinationProfileReviewItems();
    return;
  }
  const nextUncheckedButton = event.target.closest("[data-destination-review-next-unchecked]");
  if (nextUncheckedButton) {
    focusNextDestinationReviewChecklistItem(nextUncheckedButton);
    return;
  }
  const clearDraftButton = event.target.closest("[data-destination-review-draft-clear]");
  if (clearDraftButton) {
    const card = clearDraftButton.closest("[data-destination-profile-hash]");
    const profileHash = card?.dataset.destinationProfileHash || "";
    const row = (state.destinationProfileReview?.items || [])
      .find((item) => item.profile_content_hash === profileHash);
    if (!card || !row) {
      announce("找不到目前表單，請重新整理後再清除暫存。", "error");
      return;
    }
    resetDestinationReviewDraftCard(card, row);
    announce("已清除這一頁尚未送出的暫存；後端真人審查證據沒有變更。");
    return;
  }
  const submitButton = event.target.closest("[data-destination-review-submit]");
  if (submitButton) {
    submitDestinationProfileReview(submitButton);
    return;
  }
  const submitNextButton = event.target.closest("[data-destination-review-submit-next]");
  if (submitNextButton) {
    submitDestinationProfileReview(submitNextButton, { advanceToNext: true });
    return;
  }
  const promotionButton = event.target.closest("[data-destination-promotion-submit]");
  if (promotionButton) promoteDestinationProfile(promotionButton);
});
$("#destination-profile-review-items").addEventListener("input", (event) => {
  if (!event.target.matches("[data-destination-review-note]")) return;
  const card = event.target.closest("[data-destination-profile-hash]");
  saveDestinationReviewDraftFromCard(card);
  updateDestinationReviewChecklistProgress(card);
});
$("#destination-profile-review-items").addEventListener("change", (event) => {
  if (!event.target.matches(
    "[data-destination-review-source], [data-destination-review-section], [data-destination-review-decision]"
  )) return;
  const card = event.target.closest("[data-destination-profile-hash]");
  saveDestinationReviewDraftFromCard(card);
  updateDestinationReviewChecklistProgress(card);
});
$("#destination-publication-history-items").addEventListener("click", (event) => {
  const rollbackButton = event.target.closest("[data-destination-rollback-submit]");
  if (rollbackButton) rollbackDestinationProfile(rollbackButton);
});
$("#workflow-publication-history-items").addEventListener("click", (event) => {
  const rollbackButton = event.target.closest("[data-workflow-rollback-submit]");
  if (rollbackButton) rollbackApplicationWorkflow(rollbackButton);
});
$("#backlog-search").addEventListener("input", (event) => {
  state.backlogSearch = event.target.value;
  state.backlogVisibleLimit = 25;
  renderQueue();
});
$("#backlog-home-university").addEventListener("change", (event) => {
  state.backlogHomeUniversity = event.target.value;
  state.backlogVisibleLimit = 25;
  renderQueue();
});
$("#backlog-gap-filter").addEventListener("change", (event) => {
  state.backlogGapFilter = event.target.value;
  state.backlogVisibleLimit = 25;
  renderQueue();
});
$("#filter-source-replacement-candidates").addEventListener("click", () => {
  state.backlogGapFilter = "source_replacement_candidate";
  $("#backlog-gap-filter").value = state.backlogGapFilter;
  state.backlogVisibleLimit = 25;
  renderQueue();
  announce("已只顯示具有研究候選的流程；候選仍須真人逐頁確認，這個篩選不會建立或修改待審版本。");
});
$("#backlog-sort").addEventListener("change", (event) => {
  state.backlogSort = event.target.value;
  state.backlogVisibleLimit = 25;
  renderQueue();
});
$("#source-evidence-gap-groups").addEventListener("click", (event) => {
  const button = event.target.closest("[data-source-evidence-group-index]");
  if (!button) return;
  const group = (state.backlog.source_metadata_gap_groups || [])[Number(button.dataset.sourceEvidenceGroupIndex)];
  if (!group) return;
  state.sourceEvidenceUrl = group.source_url;
  state.sourceEvidenceWorkflowKeys = group.workflow_keys || [];
  state.backlogGapFilter = "source_metadata_missing";
  $("#backlog-gap-filter").value = state.backlogGapFilter;
  state.backlogVisibleLimit = 25;
  renderQueue();
  announce(`已篩選 ${group.workflow_count} 筆引用相同官方網址的流程；仍須逐流程確認適用範圍。`);
});
$("#clear-source-evidence-filter").addEventListener("click", () => {
  state.sourceEvidenceUrl = "";
  state.sourceEvidenceWorkflowKeys = [];
  state.backlogVisibleLimit = 25;
  renderQueue();
  announce("已清除相同網址篩選，回到目前的完整待辦條件。");
});
$("#clear-workflow-deep-link").addEventListener("click", () => {
  state.workflowDeepLinkKey = "";
  state.reviewBatchId = "";
  state.reviewBatchWorkflowKeys = [];
  state.workflowDeepLinkSnapshot = "";
  state.workflowDeepLinkStale = false;
  const url = new URL(window.location.href);
  url.searchParams.delete("workflow_key");
  url.searchParams.delete("review_batch");
  url.searchParams.delete("batch_size");
  url.searchParams.delete("review_snapshot");
  window.history.replaceState({}, "", url);
  state.backlogVisibleLimit = 25;
  renderQueue();
  announce("已清除分工清單定位，回到完整待辦。");
});
$("#stage-workflow-review-batch").addEventListener("click", stageWorkflowReviewBatch);
$("#open-workflow-review-batch").addEventListener("click", openWorkflowReviewBatch);
$("#review-queue").addEventListener("click", (event) => {
  const moreButton = event.target.closest("[data-backlog-more]");
  if (moreButton) {
    state.backlogVisibleLimit += 25;
    renderQueue();
    return;
  }
  const backlogButton = event.target.closest("[data-backlog-action]");
  if (backlogButton) {
    handleBacklogAction(backlogButton);
    return;
  }
  const comparisonButton = event.target.closest("[data-review-comparison]");
  if (comparisonButton) {
    loadComparison(comparisonButton);
    return;
  }
  const correctionButton = event.target.closest("[data-review-jump-corrections]");
  if (correctionButton) {
    jumpToWorkflowReviewCorrections(correctionButton);
    return;
  }
  const nextApplicabilityIssueButton = event.target.closest("[data-applicability-next-issue]");
  if (nextApplicabilityIssueButton) {
    focusNextApplicabilityIssue(nextApplicabilityIssueButton);
    return;
  }
  const nextApprovalIssueButton = event.target.closest("[data-approval-next-issue]");
  if (nextApprovalIssueButton) {
    focusNextWorkflowApprovalIssue(nextApprovalIssueButton);
    return;
  }
  const applicabilityButton = event.target.closest("[data-review-applicability-save]");
  if (applicabilityButton) {
    saveApplicability(applicabilityButton);
    return;
  }
  const sourceCandidateButton = event.target.closest("[data-apply-source-replacement-candidate]");
  if (sourceCandidateButton) {
    applySourceReplacementCandidate(sourceCandidateButton);
    return;
  }
  const clearApplicabilityDraftButton = event.target.closest("[data-workflow-applicability-draft-clear]");
  if (clearApplicabilityDraftButton) {
    const item = clearApplicabilityDraftButton.closest("[data-revision-id]");
    const revisionId = item?.dataset.revisionId || "";
    const revision = state.revisions.find((row) => row.id === revisionId);
    if (!item || !revision) {
      announce("找不到目前待審版本，請重新整理後再清除補正草稿。", "error");
      return;
    }
    resetWorkflowApplicabilityDraftItem(item, revision);
    announce("已清除這個待審版本尚未送出的補正草稿；後端內容、核准與發布紀錄沒有變更。");
    return;
  }
  const clearDraftButton = event.target.closest("[data-workflow-review-draft-clear]");
  if (clearDraftButton) {
    const item = clearDraftButton.closest("[data-revision-id]");
    const revisionId = item?.dataset.revisionId || "";
    const revision = state.revisions.find((row) => row.id === revisionId);
    if (!item || !revision) {
      announce("找不到目前待審版本，請重新整理後再清除暫存。", "error");
      return;
    }
    resetWorkflowReviewDraftItem(item, revision);
    announce("已清除這個待審版本尚未送出的本頁暫存；後端核准與發布紀錄沒有變更。");
    return;
  }
  const button = event.target.closest("[data-review-action]");
  if (button) handleAction(button);
});
$("#review-queue").addEventListener("change", (event) => {
  const checkbox = event.target.closest("[data-approval-source], [data-approval-rule]");
  if (checkbox) {
    const item = checkbox.closest("[data-revision-id]");
    updateApprovalChecklist(item);
    saveWorkflowReviewDraftFromItem(item);
  }
  const applicabilityEditor = event.target.closest(".applicability-editor");
  if (applicabilityEditor) {
    const item = applicabilityEditor.closest("[data-revision-id]");
    updateApplicabilityEditorState(item);
    saveWorkflowApplicabilityDraftFromItem(item);
  }
});
$("#review-queue").addEventListener("input", (event) => {
  if (event.target.matches("[data-review-note]")) {
    const item = event.target.closest("[data-revision-id]");
    updateApprovalChecklist(item);
    saveWorkflowReviewDraftFromItem(item);
  }
  const applicabilityEditor = event.target.closest(".applicability-editor");
  if (applicabilityEditor) {
    const item = applicabilityEditor.closest("[data-revision-id]");
    updateApplicabilityEditorState(item);
    saveWorkflowApplicabilityDraftFromItem(item);
  }
});

initialize();

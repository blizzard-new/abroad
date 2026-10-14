import json
import re
from pathlib import Path

from static_asset_contract import assert_versioned_static_assets


STATIC_DIR = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


def test_school_switcher_is_prominent_beside_page_back_control() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    rail_start = html.index('<aside id="glass-navigation"')
    rail_end = html.index("</aside>", rail_start)
    switcher = html.index('id="school-switcher"')
    page_back_start = html.index('<nav class="page-back-bar"')
    page_back_end = html.index("</nav>", page_back_start)

    assert not rail_start < switcher < rail_end
    assert page_back_start < switcher < page_back_end
    assert html.index('id="page-back"', page_back_start) < switcher
    assert "切換就讀學校" in html[page_back_start:page_back_end]


def test_content_review_workbench_exposes_dual_review_without_student_navigation() -> None:
    html = (STATIC_DIR / "content-review.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "content-review.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "content-review.css").read_text(encoding="utf-8")
    student_html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert "申請流程雙審工作台" in html
    assert "content-review.css?v=20261009-governance-3" in html
    assert "content-review.js?v=20261009-governance-3" in html
    assert 'value="review_unstarted"' in html
    assert 'value="review_partial"' in html
    assert 'value="review_ready"' in html
    assert 'value="approval"' in html
    assert 'id="workflow-review-owner-filter-field"' in html
    assert 'id="workflow-review-owner-filter"' in html
    assert 'value="mine_unreviewed"' in html
    assert 'value="mine_approved"' in html
    assert 'value="mine_publishable"' in html
    assert 'id="workflow-review-readiness-filter-field"' in html
    assert 'id="workflow-review-readiness-filter"' in html
    assert 'value="correction_ready"' in html
    assert 'value="correction_blocked"' in html
    assert 'id="workflow-review-focus-filter"' in html
    assert 'id="open-next-workflow-review"' in html
    assert 'id="show-workflow-review-batch"' in html
    assert 'id="clear-workflow-review-focus"' in html
    assert "既有流程待納入雙審" in html
    assert 'id="backlog-search"' in html
    assert 'id="backlog-home-university"' in html
    assert 'id="backlog-gap-filter"' in html
    assert 'value="source_replacement_candidate"' in html
    assert 'id="source-replacement-candidate-summary"' in html
    assert 'id="filter-source-replacement-candidates"' in html
    assert 'id="download-source-replacement-candidates"' in html
    assert "/admin/application-workflow-source-replacement-review-queue.csv" in html
    assert "下載唯讀審核 CSV" in html
    assert 'id="backlog-sort"' in html
    assert 'id="source-evidence-gap-summary"' in html
    assert 'id="source-evidence-gap-groups"' in html
    assert 'id="clear-source-evidence-filter"' in html
    assert "系統只盤點已保存的官方資料，不會猜測學年度或截止日" in html
    assert "建立待審版本只會複製到審核區" in html
    assert 'id="release-readiness"' in html
    assert 'id="release-readiness-fingerprint"' in html
    assert "Web 發布就緒閘門" in html
    assert "不能取代兩位真人逐頁確認申請規定與生活情報來源" in html
    assert 'id="destination-profile-review-summary"' in html
    assert 'id="download-destination-profile-review"' in html
    assert 'id="download-destination-profile-review-batches"' in html
    assert "/admin/destination-profile-review-queue.csv" in html
    assert "/admin/destination-profile-review-batches.csv" in html
    assert "兩人核可後，仍須由其中一位核可者明確確認" in html
    assert 'id="destination-profile-review-workbench"' in html
    assert 'id="destination-review-home-university"' in html
    assert 'value="長庚大學"' in html
    assert 'value="國立臺北大學"' in html
    assert 'id="destination-review-search"' in html
    assert 'id="destination-review-progress-filter"' in html
    assert 'id="destination-review-readiness-filter"' in html
    assert 'value="approval_ready"' in html
    assert 'value="approval_blocked"' in html
    assert 'value="mine_unreviewed"' in html
    assert 'value="mine_reviewed"' in html
    assert 'id="destination-profile-review-items"' in html
    assert 'id="destination-review-batch-filter"' in html
    assert 'id="destination-review-batch-description"' in html
    assert 'id="open-next-destination-review"' in html
    assert 'id="show-destination-review-batch"' in html
    assert 'id="download-destination-review-batch-checklist"' in html
    assert "下載目前批次逐項查核表" in html
    assert 'id="clear-destination-review-batch"' in html
    assert "逐一開啟全部來源、核對所有內容區塊" in html
    assert 'id="destination-publication-history"' in html
    assert 'id="destination-publication-history-summary"' in html
    assert 'id="destination-publication-history-items"' in html
    assert "公開版本與復原紀錄" in html
    assert 'id="workflow-publication-history"' in html
    assert 'id="workflow-publication-history-summary"' in html
    assert 'id="workflow-publication-history-items"' in html
    assert "申請流程公開版本與安全復原紀錄" in html
    assert 'id="review-batch-export"' in html
    assert 'id="review-batch-rule-export"' in html
    assert "下載目前批次逐規定查核表" in html
    assert "/admin/application-workflow-review-batches.csv?batch_size=10" in html
    assert "下載雙人審查分工 CSV" in html
    assert 'id="workflow-deep-link-filter"' in html
    assert 'id="stage-workflow-review-batch"' in html
    assert 'id="open-workflow-review-batch"' in html
    assert 'id="clear-workflow-deep-link"' in html
    assert 'get("review_snapshot")' in script
    assert 'get("review_batch")' in script
    assert 'get("batch_size")' in script
    assert "reviewBatchWorkflowKeys" in script
    assert "function stageWorkflowReviewBatch()" in script
    assert "function openWorkflowReviewBatch()" in script
    assert "function workflowReviewBatchTodoRevisions(" in script
    assert "function nextWorkflowReviewBatchTodoAfter(workflowKey)" in script
    assert "function workflowReviewCorrectionState(revision)" in script
    assert "function openNextWorkflowReviewBatchTodo()" in script
    assert "function showWorkflowReviewBatchTodos()" in script
    assert "function jumpToWorkflowReviewCorrections(button)" in script
    assert "開啟第一筆${nextItemLabel}" in script
    assert "開啟下一筆${nextItemLabel}" in script
    assert "此批次目前沒有屬於你的未核准待辦" in script
    assert "可開始真人核對" in script
    assert "須先補資料" in script
    assert "先補資料才能核准" in script
    assert "data-review-jump-corrections" in script
    assert "只會建立或重用審查副本，不會核准、發布" in script
    assert "created_count" in script
    assert "existing_count" in script
    assert "encodeURIComponent(state.reviewBatchId)}/stage" in script
    assert 'url.searchParams.set("review_batch", state.reviewBatchId)' in script
    assert 'state.workflowReviewOwnerFilter = "mine_unreviewed"' in script
    assert "重新整理仍會重新驗證並維持此批次" in script
    assert "指定的審查批次已過期或不存在" in script
    assert 'state.workflowReviewFocusRevisionId = ""' in script
    assert "/admin/application-workflow-review-batches/${encodeURIComponent(state.reviewBatchId)}" in script
    assert "目前從分工清單定位：${state.reviewBatchId}" in script
    assert "encodeURIComponent(state.reviewBatchId)}/rules.csv" in script
    assert "showBatchRuleExport" in script
    assert "workflowDeepLinkStale" in script
    assert "[404, 409].includes(error.status)" in script
    assert "目前待查核內容或批次成員已變更" in script
    assert "expected_snapshot=${encodeURIComponent(state.workflowDeepLinkSnapshot)}" in script
    assert "這份雙人審查分工清單已過期" in script
    assert 'url.searchParams.delete("review_snapshot")' in script
    assert 'url.searchParams.delete("review_batch")' in script
    assert 'url.searchParams.delete("batch_size")' in script
    assert ".workflow-review-focus-actions" in styles
    assert ".review-correction-summary" in styles
    assert ".applicability-editor-progress" in styles
    assert 'requestJson("/admin/session")' in script
    assert 'requestJson("/admin/application-workflow-review-backlog")' in script
    assert 'requestJson("/admin/web-release-readiness")' in script
    assert 'id="release-readiness-destinations"' in html
    assert 'id="release-readiness-destination-pending"' in html
    assert "function renderDestinationProfileReviewSummary()" in script
    assert "function loadDestinationProfileReviewQueue()" in script
    assert "function renderDestinationProfileReviewItems()" in script
    assert "function submitDestinationProfileReview(button, { advanceToNext = false } = {})" in script
    assert "function promoteDestinationProfile(button)" in script
    assert "function renderDestinationPublicationHistory()" in script
    assert "function loadDestinationPublicationHistory()" in script
    assert "function rollbackDestinationProfile(button)" in script
    assert "function renderWorkflowPublicationHistory()" in script
    assert "function loadWorkflowPublicationHistory()" in script
    assert "function rollbackApplicationWorkflow(button)" in script
    assert "/admin/destination-profile-review-queue?home_university=" in script
    assert "/admin/destination-profile-review-queue.csv?${params.toString()}" in script
    assert "/admin/destination-profile-review-batches.csv?${batchParams.toString()}" in script
    assert "/admin/destination-profile-review-batches/${encodeURIComponent(state.destinationReviewBatchId)}" in script
    assert 'initialQueryParams.get("destination_home")' in script
    assert 'initialQueryParams.get("destination_batch")' in script
    assert 'initialQueryParams.get("destination_snapshot")' in script
    assert 'initialQueryParams.get("destination_batch_size")' in script
    assert "destinationReviewBatchRequestSequence" in script
    assert "destinationReviewBatchProfileHashes" in script
    assert "destinationReviewBatchChecklistPath" in script
    assert "destinationReviewBatchStale" in script
    assert "function renderDestinationReviewBatchFilter()" in script
    assert "function loadDestinationReviewBatch()" in script
    assert "function clearDestinationReviewBatchFilter" in script
    assert "這份生活情報分工批次已過期" in script
    assert "rows[0]?.batch_checklist_path" in script
    assert "全部官方來源與 12 個內容區塊逐項查核表" in script
    assert 'url.searchParams.delete("destination_batch")' in script
    assert 'url.searchParams.delete("destination_snapshot")' in script
    assert 'requestJson("/admin/destination-profile-reviews"' in script
    assert 'requestJson("/admin/destination-profile-promotions"' in script
    assert "/admin/destination-profile-publications?home_university=" in script
    assert "destinationReviewHomeUniversity" in script
    assert "destinationReviewRequestSequence" in script
    assert "destinationPublicationRequestSequence" in script
    assert "encodeURIComponent(homeUniversity)" in script
    assert 'encodeURIComponent("長庚大學")' not in script
    assert 'requestJson("/admin/destination-profile-rollbacks"' in script
    assert '"/admin/application-workflow-publications"' in script
    assert 'requestJson("/admin/application-workflow-rollbacks"' in script
    assert "data-destination-review-source" in script
    assert "data-destination-review-section" in script
    assert "exchange.destination-review-draft.v1" in script
    assert "window.sessionStorage" in script
    assert "function destinationReviewDraftKey(profileHash)" in script
    assert "reviewer_id: state.admin.id" in script
    assert "payload.profile_content_hash !== profileHash" in script
    assert "function saveDestinationReviewDraftFromCard(card)" in script
    assert "function clearDestinationReviewDraft(profileHash)" in script
    assert "clearDestinationReviewDraft(profileHash);" in script
    assert "data-destination-review-draft-clear" in script
    assert 'progressFilter === "mine_unreviewed"' in script
    assert 'progressFilter === "mine_reviewed"' in script
    assert "不能當成審查證據" in html
    assert ".destination-review-draft" in styles
    assert "exchange.workflow-review-draft.v1" in script
    assert "function workflowReviewDraftKey(revision)" in script
    assert "payload.revision_id !== revision.id" in script
    assert "payload.content_hash !== revision.content_hash" in script
    assert "function saveWorkflowReviewDraftFromItem(item)" in script
    assert "function clearWorkflowReviewDraft(revision)" in script
    assert "clearWorkflowReviewDraft(revision);" in script
    assert "data-workflow-review-draft-clear" in script
    assert "尚未送到後端，也不是核准證據" in script
    assert "未送出的表單只暫存在目前瀏覽器分頁" in html
    assert ".workflow-review-draft" in styles
    assert "expected_profile_content_hash" in script
    assert "不會修改 profile、升級 official_verified" in script
    assert "data-destination-promotion-confirm" in script
    assert "data-destination-promotion-note" in script
    assert "這會改變學生可見的生活情報狀態" in script
    assert "申請規則、文件、截止日與通知均未變更" in script
    assert "data-destination-rollback-confirm" in script
    assert "data-destination-rollback-note" in script
    assert "data-workflow-rollback-target" in script
    assert "data-workflow-rollback-note" in script
    assert "data-workflow-rollback-confirm" in script
    assert "後續修改仍須重新雙審" in script
    assert "舊核可不再計入目前候選" in script
    assert "explicit_second_review_required_count" in script
    assert "待審資料共有 ${queue.pending_source_count} 個官方來源" in script
    assert "queue.ready_for_promotion_count" in script
    assert ".destination-publication-card" in styles
    assert ".destination-review-batch-filter" in styles
    assert ".destination-rollback-panel" in styles
    assert ".workflow-publication-card" in styles
    assert ".workflow-rollback-panel" in styles
    assert "function renderReleaseReadiness()" in script
    assert 'report.release_ready ? "READY" : "NOT READY"' in script
    assert "snapshot_fingerprint" in script
    assert 'new URLSearchParams(window.location.search).get("workflow_key")' in script
    assert "function renderWorkflowDeepLinkFilter()" in script
    assert 'url.searchParams.delete("workflow_key")' in script
    assert "分工清單指定的流程已不在目前待辦" in script
    assert "/admin/application-workflow-review-backlog/${encodeURIComponent(workflowKey)}/stage" in script
    assert "/admin/application-workflow-revisions/${encodeURIComponent(revisionId)}/applicability" in script
    assert "補正適用學年度與來源證據" in script
    assert "function updateApplicabilityEditorState(item)" in script
    assert "exchange.workflow-applicability-draft.v1" in script
    assert "function workflowApplicabilityDraftKey(revision)" in script
    assert "function loadWorkflowApplicabilityDraft(revision)" in script
    assert "function saveWorkflowApplicabilityDraftFromItem(item)" in script
    assert "function resetWorkflowApplicabilityDraftItem(item, revision)" in script
    assert "data-workflow-applicability-draft-status" in script
    assert "data-workflow-applicability-draft-clear" in script
    assert "尚未送到後端，也不是核准證據" in script
    assert "data-applicability-progress" in script
    assert "data-applicability-source-progress" in script
    assert "data-applicability-next-issue" in script
    assert "function focusNextApplicabilityIssue(button)" in script
    assert "const hadValidatedBatchContext = Boolean(" in script
    assert "候選內容已改變審查指紋，原批次因此過期" in script
    assert "目前無法重新驗證原批次" in script
    assert "function announceDestinationReviewResult(message)" in script
    assert "原生活情報批次因內容指紋或待審成員改變而過期" in script
    assert "目前無法重新驗證原生活情報批次" in script
    assert "function nextDestinationReviewBatchTodoAfter(profileHash)" in script
    assert "function openDestinationReviewBatchTodo(row)" in script
    assert "function destinationReviewBatchTodoRows({ ignoreReadiness = false } = {})" in script
    assert "function openNextDestinationReviewBatchTodo()" in script
    assert "function showDestinationReviewBatchTodos()" in script
    assert "function destinationReviewApprovalBlockers(row)" in script
    assert "function updateDestinationReviewChecklistProgress(card)" in script
    assert "function focusNextDestinationReviewChecklistItem(button)" in script
    assert "data-destination-review-check-progress" in script
    assert "data-destination-review-source-progress" in script
    assert "data-destination-review-section-progress" in script
    assert "data-destination-review-note-progress" in script
    assert "data-destination-review-next-unchecked" in script
    assert "系統不會替你自動勾選" in script
    assert "不會自動勾選、送出、建立審查證據" in script
    assert "核對項目已完成；審查說明尚需" in script
    assert "本頁已具備送出條件" in script
    assert "button.disabled = submitting || !ready" in script
    assert "data-destination-review-approval-gate" in script
    assert "目前只能要求修正，不能核可" in script
    assert "目前具備可選擇核可的資料門檻" in script
    assert "目前門檻篩選沒有我的待辦" in script
    assert "目前核可門檻篩選沒有待審生活情報" in script
    assert "destinationReviewReadinessFilter" in script
    assert "missing_sources" in script
    assert "insecure_sources" in script
    assert "missing_last_checked" in script
    assert ".destination-review-decision-gate" in styles
    assert ".destination-review-check-progress" in styles
    assert "開啟第一筆" in script
    assert "開啟下一筆" in script
    assert "此批次我的待辦已完成" in script
    assert "已顯示此批次的完整『我的待辦』清單" in script
    assert "data-destination-review-submit-next" in script
    assert "保存並前往下一筆我的待辦" in script
    assert "這不代表雙審或發布完成" in script
    assert ".destination-review-submit-actions" in styles
    assert ".destination-review-batch-actions" in styles
    assert "本次未選取，不會儲存這列欄位" in script
    assert "本次補正欄位完成；儲存時只會更新這個來源" in script
    assert "已前往下一個尚未完成的補正欄位" in script
    assert "已選擇 ${selectedRows.length} / ${sourceRows.length} 個來源" in script
    assert "可儲存本次逐頁補正；未勾選來源保持不變" in script
    assert "請修改流程適用學年度／梯次，或勾選至少一個已逐頁確認的來源" in script
    assert ".workflow-applicability-draft" in styles
    assert ".applicability-source-progress" in styles
    assert "這次已逐頁確認此來源" in script
    assert "這次已逐頁確認並補齊來源證據資料" in script
    assert "data-source-tracked" in script
    assert "data-source-metadata-complete" in script
    assert "data-source-title" in script
    assert "data-source-role" in script
    assert "data-source-authority" in script
    assert "尚未建立證據資料的來源必須填寫來源名稱、角色與權威層級" in script
    assert "安全替代網址（選填）" in script
    assert "data-source-replacement-url" in script
    assert 'requestJson("/admin/application-workflow-source-replacement-candidates")' in script
    assert "人工審核候選" in script
    assert "自動研究證據（不能當作核准）" in script
    assert "data-apply-source-replacement-candidate" in script
    assert 'data-can-prefill="${canPrefill ? "true" : "false"}"' in script
    assert 'data-transport-status="${escapeHtml(candidate.transport_status)}"' in script
    assert 'candidate.can_prefill === true' in script
    assert 'button.dataset.canPrefill !== "true"' in script
    assert "傳輸安全未通過，禁止填入" in script
    assert "安全研究線索（不可直接替代）" in script
    assert "source-candidate-research-leads" in script
    assert 'data-eligible-as-replacement="false"' in script
    assert "不可直接替代" in script
    assert "只填入待審欄位" in script
    assert "不會自動勾選、儲存、核准或發布" in script
    assert "替代網址欄位已有其他內容；為避免覆寫" in script
    assert "候選網址只已填入尚未儲存的欄位" in script
    assert "workflows_with_source_replacement_candidates" in script
    assert "source_replacement_candidate_count" in script
    assert "strong_source_replacement_candidate_count" in script
    assert "conditional_source_replacement_candidate_count" in script
    assert "function renderSourceReplacementCandidateSummary()" in script
    assert 'const download = $("#download-source-replacement-candidates")' in script
    assert "/admin/application-workflow-source-replacement-review-queue.csv" in script
    assert "下載 ${candidateCount} 個來源候選的唯讀人工審核清單" in script
    assert "請先篩選，再由真人逐頁確認" in script
    assert "這個篩選不會建立或修改待審版本" in script
    assert "replacement_source_url" in script
    assert "同步更新步驟、期限、表單與文件引用" in script
    assert "非 HTTPS 官方來源必須先填入已核實的安全替代網址" in script
    assert "不會自動猜網址或把流程年度套到所有來源" in script
    assert "既有核准已清除" in script
    assert "data-review-applicability-save" in script
    assert "適用狀態" in script
    assert "來源年度" in script
    assert "sourceYearReadyCount" in script
    assert "學生目前看到的內容沒有變更" in script
    assert 'data-backlog-action="${staged ? "open" : "stage"}"' in script
    assert "backlogVisibleLimit: 25" in script
    assert "data-backlog-more" in script
    assert "review_gap_codes" in script
    assert "review_approval_count" in script
    assert "required_review_count" in script
    assert "review_ready_to_publish" in script
    assert "待第一位核准" in script
    assert "待第二位核准" in script
    assert "已達雙審門檻" in script
    assert "目前缺口與規定數已依這份候選內容重算" in script
    assert "verified_exact_deadline_count" in script
    assert "critical_rule_count" in script
    assert "critical_rule_source_gap_count" in script
    assert "insecure_source_count" in script
    assert "關鍵規定" in script
    assert "缺可驗證精確期限" in script
    assert "關鍵規定缺對應來源" in script
    assert "含非 HTTPS 官方來源" in script
    assert "缺最後查核日期" in script
    assert "官方引用缺來源證據資料" in script
    assert "source_metadata_missing_count" in script
    assert "source_metadata_gap_reference_count" in script
    assert "distinct_source_metadata_gap_url_count" in script
    assert "source_metadata_gap_groups" in script
    assert "source_evidence_snapshot_fingerprint" in script
    assert "data-source-evidence-group-index" in script
    assert "/admin/application-workflow-review-backlog/source-evidence.csv?source_url=" in script
    assert "&amp;expected_snapshot=" in script
    assert "下載唯讀 CSV" in script
    assert "相同網址仍須確認適用於每一份流程" in script
    assert "這裡不會批次填值、核准或發布" in script
    assert "此網址支援的規定" in script
    assert "流程適用範圍來源清單" in script
    assert "請依頁面正式標題填寫" in script
    assert "review_timestamp_missing_count" in script
    assert "完成本次逐來源、逐規定核准時會以審查時間補上" in script
    assert "目前沒有符合這組篩選條件的既有流程" in script
    assert "target.scrollIntoView" in script
    assert ".source-replacement-candidate-actions" in styles
    assert "/admin/application-workflow-revisions" in script
    assert "/comparison" in script
    assert "載入版本對照" in script
    assert "基準與候選逐欄對照" in script
    assert "核准前請先載入並逐欄核對版本差異" in script
    assert "先載入版本對照" in script
    assert 'data-review-action="approve"' in script
    assert "data-approval-completion" in script
    assert "data-approval-completion-note" in script
    assert "data-approval-next-issue" in script
    assert "data-approval-submit-next" in script
    assert "核准並前往下一筆我的待辦" in script
    assert "function focusNextWorkflowApprovalIssue(button)" in script
    assert "核對項目已完成；請填寫本次查核說明" in script
    assert "本頁已具備獨立核准送出條件" in script
    assert "approveButtons.forEach((button)" in script
    assert "button.disabled = submitting || !ready" in script
    assert "已前往此批次下一筆我的待辦" in script
    assert "原申請流程批次已過期，舊定位未套用" in script
    assert "目前資料門檻篩選沒有下一筆我的待辦" in script
    assert "我已親自開啟並逐頁確認這個來源" in script
    assert "reviewed_source_urls" in script
    assert "reviewed_rule_keys" in script
    assert "expected_content_hash: revision.content_hash" in script
    assert "核准會綁定目前內容版本、來源清單與關鍵規定清單" in script
    assert "我已逐項核對這條規定及其官方來源" in script
    assert "流程適用範圍、每個步驟與每份文件都必須逐項核對" in script
    assert "對應來源：" in script
    assert "補齊安全的對應官方來源後才能核對" in script
    assert "發布阻擋" in script
    assert "source-attestation-status" in styles
    assert ".workflow-approval-completion" in styles
    assert "approval-rule-list" in styles
    assert "rule-source-links" in styles
    assert "source-security-warning" in styles
    assert "source-replacement-field" in styles
    assert "source-replacement-candidate" in styles
    assert "source-replacement-candidate-summary" in styles
    assert '[data-transport-status="downgrades_to_http"]' in styles
    assert "review-pill.candidate" in styles
    assert "source-candidate-guard" in styles
    assert "review-metadata-blocker" in styles
    assert "queueRequestSequence" in script
    assert "requestSequence !== state.queueRequestSequence" in script
    assert 'data-review-action="publish"' in script
    assert 'data-review-action="reject"' in script
    assert "currentAdminApproved" in script
    assert 'initialQueryParams.get("review_status")' in script
    assert 'initialQueryParams.get("workflow_revision")' in script
    assert "function filteredWorkflowRevisions()" in script
    assert 'state.workflowReviewOwnerFilter === "mine_unreviewed"' in script
    assert 'state.workflowReviewOwnerFilter === "mine_approved"' in script
    assert 'state.workflowReviewOwnerFilter === "mine_publishable"' in script
    assert 'url.searchParams.set("review_status", status)' in script
    assert 'url.searchParams.set("workflow_revision", state.workflowReviewFocusRevisionId)' in script
    assert "function renderWorkflowReviewFocusFilter()" in script
    assert ".workflow-review-focus-filter" in styles
    assert "請先填寫本次查核說明。" in script
    assert "第二份獨立核准已保存；目前已達兩人發布門檻。" in script
    assert "同一帳號不能重複核准" in html
    assert "@media (max-width: 520px)" in styles
    assert ".backlog-filters" in styles
    assert ".backlog-metrics" in styles
    assert ".backlog-more" in styles
    assert ".source-evidence-gap-summary" in styles
    assert ".source-evidence-gap-group" in styles
    assert ".source-evidence-export" in styles
    assert ".release-readiness" in styles
    assert '.release-readiness[data-status="ready"]' in styles
    assert ".release-readiness-actions" in styles
    assert ".release-readiness-actions [hidden]" in styles
    assert ".workflow-deep-link-filter" in styles
    assert ".workflow-deep-link-filter.is-stale" in styles
    assert ".source-reference-contexts" in styles
    assert ".comparison-table" in styles
    assert ".comparison-items details:not([open])" in styles
    assert "/admin/content-review" not in student_html


def test_first_visit_school_choice_is_a_single_click_on_the_school_and_still_skippable_with_escape() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "你目前就讀哪一所台灣大學？" in html
    # The rows carry the school's name and nothing else; there are no confirm / browse buttons any more.
    assert "選擇我的學校" not in html
    assert "先看看全部交換學校" not in html
    assert 'id="confirm-school"' not in html and 'id="browse-first"' not in html
    assert "school-option-name" in html and "school-emblem" in html
    assert "完整支援試點" not in html
    assert "75 間合作校" in html
    assert "partner_count: 75" in script
    assert "partner_count: 206" in script
    assert "partner_count: 288" in script
    assert "browseWithoutSchoolSelection" in script


def test_web_routes_states_and_touch_targets_are_consistent() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert '<span>資格與志願</span>' in html
    assert 'eligibility: "資格與志願"' in script
    assert "function focusRouteHeading(selector)" in script
    assert 'focusRouteHeading("#community-hub-title")' in script
    assert '? PUBLIC_COMMUNITY_BOARD' in script
    assert '? "我的追蹤"' in script
    assert "跨校討論交換申請、簽證、住宿與海外生活。" in script
    assert 'role="${isError ? "alert" : "status"}"' in script
    reader = (STATIC_DIR / "community-reader.js").read_text(encoding="utf-8")
    assert 'window.UniWayCommunity.load({ force })' in script
    assert 'feed.innerHTML = message("文章暫時無法載入", error.message, true)' in reader
    assert 'role="status"' in reader
    assert 'data-discussion-retry' in reader
    assert '${escape(text)}' in reader
    assert "/* B6-01: consistent states, touch targets and zoom-safe wrapping */" in styles
    assert ".application-copy-input {\n  min-height: 44px;" in styles


def test_partner_schools_use_verified_official_photo_manifest() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    manifest = json.loads(
        (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
    )

    assert 'id="school-detail-photo"' in html
    assert 'fetchJson("/static/assets/school-images.json?' in script
    assert "renderSchoolPhoto(item, \"table\")" in script
    assert "renderSchoolPhoto(item, \"card\")" in script
    assert "圖片來源" in script
    verified = {
        row["school_name"]
        for row in manifest["schools"]
        if row.get("status") == "verified"
    }
    assert len(verified) >= 71
    assert "蔚山科技大學(Ulsan National Institute of Science and Technology)" in verified
    assert "明知大學(Myongi university)" in verified
    assert "世宗大學 (Sejong University)" in verified


def test_school_onboarding_supports_keyboard_dismissal_and_focus_return() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'event.key === "Escape"' in script
    assert 'event.key !== "Tab"' in script
    assert "onboardingReturnFocus" in script
    assert "returnFocus.focus()" in script


def test_school_detail_does_not_recrawl_empty_experiences_on_open() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'fetchJson(`/student-experiences?school=${school}&home_school=${encodeURIComponent(activeHomeSchool())}`)' in script
    assert "if (!forceRefresh && digest.total_sources === 0)" not in script
    assert "/student-experiences/refresh?school=" in script


def test_destination_profiles_follow_the_active_home_university() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "async function loadDestinationProfiles({ homeSchool = activeHomeSchool() } = {})" in script
    assert "/destination-profiles?home_school=" in script
    assert "isCurrentHomeSchool(requestedSchool)" in script


def test_destination_profiles_distinguish_partial_from_verified_coverage() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'profile.coverage_status === "official_partial"' in script
    assert "官方生活資訊已查核" in script
    assert "官方生活資訊已查核" in script


def test_public_workflow_ui_never_publishes_collected_content_directly() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "/application-workflow/refresh" not in script
    assert "重新載入流程資料" in script
    assert "正式發布前" in script
    assert 'forceRefresh ? { cache: "no-store" } : {}' in script


def test_workflow_ui_exposes_structured_submission_and_confirmation_details() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "workflowRequestParams" in script
    assert 'params.set(key, String(value).trim())' in script
    assert "renderWorkflowSubmission" in script
    assert "renderWorkflowDocumentRequirement" in script
    assert "送件方式待確認" in script
    assert "請聯絡：" in script
    assert "文件形式待確認" in script
    assert "WORKFLOW_SOURCE_LABELS" in script


def test_web_consumes_shared_entitlement_contract_without_payment() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="profile-entitlement-status"' in html
    assert 'fetchJson("/product/entitlements")' in script
    assert 'entitlements.release_mode === "closed_beta"' in script
    assert "目前所有功能都免費開放，系統不會扣款。" in script
    assert "封閉測試" not in script


def test_account_workspace_sync_excludes_sensitive_form_content() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    payload = script.split("function accountWorkspacePayload", maxsplit=1)[1].split(
        "function persistAccountWorkspaceLocally", maxsplit=1
    )[0]
    assert 'fetchJson("/account/workspace"' in script
    assert "favorite_schools" in payload
    assert "application_progress" in payload
    assert "document_readiness" in payload
    assert "submission_progress" in payload
    assert "budget_plans" in payload
    assert "deadline_events" in payload
    assert "applicationProfile" not in payload
    assert "applicationAnswers" not in payload
    assert "applicationFiles" not in payload
    assert "scheduleAccountWorkspaceSync" in script


def test_progressive_login_keeps_device_selection_separate_from_private_plans() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    toggle_favorite = script.split("function toggleFavorite", maxsplit=1)[1].split(
        "function updateFavoriteCounts", maxsplit=1
    )[0]
    toggle_application = script.split("function toggleApplication", maxsplit=1)[1].split(
        "function renderPrimaryFacts", maxsplit=1
    )[0]
    add_calendar_event = script.split("function addCalendarEvent", maxsplit=1)[1].split(
        "function updateCalendarTaskStatus", maxsplit=1
    )[0]
    document_readiness = script.split("function updateDocumentReadiness", maxsplit=1)[1].split(
        "function updateDocumentStatus", maxsplit=1
    )[0]
    application_progress = script.split("function updateApplicationProgress", maxsplit=1)[1].split(
        "function renderWorkflowLoading", maxsplit=1
    )[0]
    application_context = script.split("function persistApplicationContext", maxsplit=1)[1].split(
        "function applicationAnswersForSession", maxsplit=1
    )[0]
    save_budget = script.split("function saveBudgetPlan", maxsplit=1)[1].split(
        "function renderPartnerFilters", maxsplit=1
    )[0]
    advisor_submit = script.split("async function submitAdvisorPlan", maxsplit=1)[1].split(
        "function advisorCitationMeta", maxsplit=1
    )[0]

    assert "guestComparisons: new Set()" in script
    assert "return state.account ? state.favorites : state.guestComparisons;" in script
    assert 'id="discovery-save-note"' in html
    assert "window.localStorage.setItem(STORAGE_KEYS.favorites" in toggle_favorite
    assert toggle_favorite.index("if (state.account)") < toggle_favorite.index(
        "window.localStorage.setItem(STORAGE_KEYS.favorites"
    )
    assert "persistDiscovery" in toggle_favorite
    assert "if (!state.account)" in toggle_application
    assert "openAuthDialog(\"register\")" in toggle_application
    assert toggle_application.index("if (!state.account)") < toggle_application.index(
        "state.applications.add(schoolName)"
    )
    assert "function requireAccountForPrivateAction" in script
    assert "新增個人申請任務需要先登入" in add_calendar_event
    assert add_calendar_event.index("requireAccountForPrivateAction") < add_calendar_event.index(
        "state.calendarEvents.push"
    )
    assert "記錄文件準備狀態需要先登入" in document_readiness
    assert document_readiness.index("requireAccountForPrivateAction") < document_readiness.index(
        "state.documentReadiness[documentId]"
    )
    assert "記錄學校申請進度需要先登入" in application_progress
    assert application_progress.index("requireAccountForPrivateAction") < application_progress.index(
        "state.applicationProgress[state.activeSchool]"
    )
    assert 'state.account ? "" : "disabled"' in script
    assert "登入後才能記錄並同步文件準備狀態" in script
    assert "登入以保存進度" in script
    assert application_context.index("if (!state.account) return;") < application_context.index(
        "window.localStorage.setItem(STORAGE_KEYS.applicationContext"
    )
    assert "if (!state.account)" in save_budget
    assert save_budget.index("if (!state.account)") < save_budget.index(
        "state.budgetPlans[values.schoolName]"
    )
    assert "state.pendingBudgetDraft = values" in save_budget
    assert "window.localStorage.setItem" not in save_budget
    assert "scheduleAccountWorkspaceSync();" in save_budget
    assert 'id="budget-save-note"' in html
    assert "試算不需登入" in html
    assert "未登入可先填寫，登入後才會送出並保存個人方案" in html
    assert "if (!state.account)" in advisor_submit
    assert 'openAuthDialog("register")' in advisor_submit
    assert advisor_submit.index("if (!state.account)") < advisor_submit.index(
        "new FormData(form)"
    )
    assert advisor_submit.index("if (!state.account)") < advisor_submit.index(
        'fetchJson("/advisor/plan"'
    )
    assert advisor_submit.index("if (!state.account)") < advisor_submit.index(
        "window.localStorage.setItem(STORAGE_KEYS.eligibility"
    )


def test_ntpu_uses_the_same_dynamic_web_shell() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'data-home-school="國立臺北大學"' in html
    assert "169 間合作校" in html
    assert 'id="availability-filter"' in html
    assert "合作學校" in html
    assert "refreshHomeUniversityData" in script
    assert "school: requestedSchool" in script
    assert "academicMinimum()" in script
    assert 'href="#university-posts"' in html


def test_home_school_switch_rejects_stale_dashboard_responses() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "function isCurrentHomeSchool" in script
    assert "const requestedSchool = homeSchool;" in script
    assert "if (!schoolDataRequestIsCurrent(request)) return false;" in script
    assert "request.kind] === request.id" in script
    assert "context.version === state.schoolContextVersion && isCurrentHomeSchool(context.homeSchool)" in script
    assert 'window.UniWayNavigation.replaceState({}, "", "#partners")' in script
    assert "const dashboardMismatch = Boolean(state.dashboard?.school_name)" in script
    assert "if (needsRefresh && reload) refreshHomeUniversityData();" in script


def test_home_school_switch_closes_an_open_partner_detail() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    set_home_school = script.split("function setHomeSchool", maxsplit=1)[1].split(
        "function updateSchoolContext", maxsplit=1
    )[0]
    assert 'state.activeSchool || !$("#school-detail-view")?.hidden' in set_home_school
    assert "closeUniversityDetail({ updateHistory: false });" in set_home_school


def test_school_detail_uses_accessible_real_tabs() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'role="tablist"' in html
    detail_tabs = html.split('<nav class="detail-tabs"', 1)[1].split("</nav>", 1)[0]
    assert detail_tabs.count('role="tab"') == 6, "快速了解、申請方式、生活情報、出發前提醒、學生心得、學生社群"
    assert detail_tabs.index("detail-tab-life") < detail_tabs.index("detail-tab-prep") < detail_tabs.index("detail-tab-experiences")
    for panel in ("detail-overview", "detail-application", "detail-life", "detail-prep", "detail-experiences", "detail-community"):
        assert f'aria-controls="{panel}"' in detail_tabs
        assert f'<section id="{panel}"' in script, panel
    assert 'aria-labelledby="detail-tab-prep"' in script and "window.UniWayDestinationTips?.load(item)" in script
    assert 'role="tabpanel"' in script
    assert "activateDetailTab" in script
    assert 'event.key === "ArrowRight"' in script
    assert 'event.key === "ArrowLeft"' in script
    assert 'event.key === "Home"' in script
    assert 'event.key === "End"' in script
    assert "scrollIntoView" in script


def test_student_life_has_ten_decision_categories_and_progressive_disclosure() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    life_block = script.split("const LIFE_SECTIONS = [", 1)[1].split("];", 1)[0]
    assert life_block.count("{ theme:") == 10
    for label in (
        "住宿與宿舍",
        "每月生活預算",
        "飲食與採買",
        "交通與地點",
        "課業與教學",
        "氣候與穿著",
        "校園活動與社交",
        "安全、醫療與保險",
        "文化適應與交朋友",
        "旅行與周邊城市",
    ):
        assert label in life_block
    assert "hasConcretePoints" in script
    assert "renderLifeSourceLinks" in script
    assert "待補資料" in script
    assert "非學生心得" in script


def test_student_life_prioritizes_sources_and_uses_concrete_points() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    render_block = script.split("function renderStudentLife", 1)[1].split(
        "function experienceKeyPoints", 1
    )[0]
    points_block = script.split("function buildLifeKeyPoints", 1)[1].split(
        "function renderLifeSourceLinks", 1
    )[0]

    assert ".sort((left, right)" in render_block
    assert "source_count" in render_block
    assert "highlight.key_points" in points_block
    assert "樣本仍有限" not in points_block


def test_direct_school_link_returns_to_partner_list() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'window.location.hash.startsWith("#school=")' in script
    assert '? "#partners"' in script


def test_quick_overview_explains_fit_strengths_and_risks() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "這間學校適合我嗎？" in script
    assert "適合條件" in script
    assert "學生評價" in script
    assert "申請前先確認" in script
    assert "合作校公開條件" in script
    assert "摘要不取代正式資格審查" in script
    assert "updateQuickDecisionFit(digest)" in script


def test_partner_pages_use_chinese_bullet_summaries_instead_of_raw_english() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "student_summary_zh" in script
    assert "renderStudentPointList" in script
    assert "合作校條件" in script
    assert "資格與語言重點" in script
    assert "中文摘要" in script
    assert "const fullCondition = [item.eligibility, item.application_info]" not in script
    assert ".student-point-list" in styles
    assert ".partner-summary-groups" in styles


def test_school_detail_uses_full_background_photo_liquid_panels_and_scroll_motion() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'variant === "detail"' in script
    assert "setSchoolHeroProgress" in script
    assert "queueSchoolHeroMotion" in script
    assert 'window.addEventListener("scroll", queueSchoolHeroMotion' in script
    assert ".school-detail-photo {\n  position: absolute;" in styles
    assert "--hero-photo-opacity" in styles
    assert ".school-detail-copy,\n.detail-primary-facts" in styles
    assert "backdrop-filter: saturate(170%) blur(28px)" in styles
    assert "/* Liquid Glass interaction system */" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles


def test_school_detail_cards_wrap_highlights_and_replace_long_urls_with_links() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "function renderSummaryText" in script
    assert 'class="summary-inline-link"' in script
    assert ".map((point) => `<li>${renderSummaryText(point)}</li>`)" in script
    assert ".summary-inline-link" in styles
    assert ".text-highlight {\n  -webkit-box-decoration-break: clone;" in styles
    assert "overflow-wrap: anywhere" in styles
    assert "grid-template-columns: repeat(auto-fit, minmax(210px, 1fr))" in styles


def test_premium_web_material_keeps_glass_hierarchy_without_heavy_button_chrome() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "/static/platform.css?v=" in html
    assert "Premium product refinement" in styles
    assert "Final cascade for the premium material" in styles
    assert "--premium-surface" in styles
    assert ".featured-board-card:hover" in styles
    assert ".partner-results" in styles
    assert ".community-empty" in styles
    assert "background-color: rgba(17, 30, 44, 0.94)" in styles


def test_desktop_navigation_rail_expands_over_stationary_content() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    navigation = (STATIC_DIR / "navigation.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "glass-theme.css").read_text(encoding="utf-8")

    assert 'class="rail-action-label">重新整理</span>' in html
    assert 'class="rail-action-label">通知中心</span>' in html
    assert ".glass-navigation-rail:is(:hover, :focus-within)" in styles
    assert "width: 76px" in styles
    assert "width: 240px" in styles
    assert "margin-left: 112px" in styles
    assert "width: calc(100% - 144px)" in styles
    assert "margin-left: 288px" not in styles
    assert "glass-rail-tooltip" not in styles
    assert "glass-rail-tooltip" not in navigation


def test_grounded_advisor_and_document_checker_are_independent_pages() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'href="#advisor" data-section="advisor"' in html
    assert 'data-university-page="advisor"' in html
    assert 'data-university-page="document-check"' in html
    assert 'data-university-page="writing-assistant"' in html
    assert "僅依已查核來源作答；符合度不是錄取機率" in html
    assert 'id="advisor-department"' in html
    assert 'id="advisor-current-year"' in html
    assert 'fetchJson("/ai/status")' in script
    assert "advisorCitationMeta" in script
    assert 'id="document-check-gate"' in html
    assert 'id="document-check-content"' in html
    assert "AI 深度檢查暫緩" in html
    assert "不會把文字傳給外部 AI，也不會啟動本地模型" in html
    assert 'id="document-check-consent" name="consent" type="checkbox" required' in html
    assert "登入不代表同意傳送" in html
    assert "文件改寫（暫緩）" in html
    assert "本地 AI 尚未設定" in html
    assert 'id="writing-assistant-submit" type="submit" class="primary-button full-width" disabled' in html
    assert 'name="text" minlength="20" maxlength="16000" rows="10" placeholder="本地 AI 環境完成後才會開放" disabled' in html
    assert "function documentCompletenessReviewEnabled()" in script
    assert 'entitlementFeatureEnabled("document_completeness_review")' in script
    assert "登入後使用文件完整性檢查" in script
    assert "文件完整性檢查是進階功能" in script
    assert 'data-document-check-login' in script
    assert 'fetchJson("/advisor/plan"' in script
    assert 'fetchJson("/document-check"' in script
    assert "if (!consent.checked)" in script
    assert 'data.set("consent", "true")' in script
    assert "consent.checked = false;" in script
    assert 'fetchJson("/ai/rewrite-document"' not in script
    assert "AI 建議稿" not in script
    assert 'const modeLabel = "規則整理";' in script
    assert "addAdvisorTaskToCalendar" in script
    assert '<details class="document-issue' in script
    assert '<details class="document-check-suggestions' in script
    assert "Grounded advisor and document review" in styles
    assert ".document-check-gate" in styles
    assert "backdrop-filter: blur(28px) saturate(170%)" in styles


def test_frontend_avoids_inline_script_handlers_for_strict_csp() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    review_html = (STATIC_DIR / "content-review.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "onerror=" not in html
    assert "onerror=" not in review_html
    assert 'onerror="this.remove()"' not in script
    assert 'data-remove-on-error="true"' in script
    assert 'document.addEventListener("error"' in script


def test_repeated_information_cards_use_compact_progressive_disclosure() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "點開文件名稱查看整理重點與官方來源" not in html
    assert '<small>${escapeHtml(truncate(rule.summary, 60))}</small>' not in script
    assert '<small>${escapeHtml(truncate(item.summary, 58))}</small>' not in script
    assert '<details class="deadline-card" data-period-status="${escapeHtml(meta.tone)}">' in script
    assert '<details class="search-result-card">' in script
    assert "renderDiscoveryWorkspace();" in script
    assert "Compact disclosure lists" in styles
    assert '<small>${escapeHtml(truncate(meta, 72))}</small>' in script
    assert "-webkit-line-clamp: 2" in styles


def test_wide_desktop_workspace_fills_the_canvas_without_centered_cut_edges() -> None:
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "Wide desktop canvas" in styles
    assert "@media (min-width: 961px)" in styles
    assert "--workspace-pad-x: clamp(30px, 2.8vw, 56px)" in styles
    assert ".workspace {\n    --workspace-pad-x" in styles
    assert "max-width: none" in styles
    assert "margin-inline: calc(0px - var(--workspace-pad-x))" in styles
    assert ".page-section {\n    border: 0;\n    background: transparent;" in styles
    assert "Partner filters: layered Liquid Glass" in styles
    assert "backdrop-filter: blur(30px) saturate(170%);" in styles
    assert "#clear-partner-filters {" in styles


def test_school_community_has_posts_chat_invitation_only_messages_and_safety() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "學生社群" in html
    assert "動態貼文" in script
    assert "公開聊天室" in script
    assert "私訊邀請" in script
    assert "對方接受邀請後" in script
    assert "/community/posts" in script
    assert "/community/chat" in script
    assert "/community/conversations" in script
    assert "/community/blocks" in script
    assert "/community/reports" in script


def test_account_and_global_community_web_flows_are_present() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="auth-dialog"' in html
    assert 'id="register-form"' in html
    assert 'data-oauth-provider="google"' in html
    assert 'data-oauth-provider="facebook"' in html
    assert 'id="profile-form"' in html
    assert 'id="community-hub"' in html
    assert 'id="global-community-form"' in html
    assert "/auth/register" in script
    assert "/auth/login" in script
    assert "/auth/community-identity" in script
    assert "loadGlobalCommunity" in script
    assert "renderApplicationJourney" in script


def test_community_identity_preview_matches_public_name_and_resets_per_submission() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "這次公開顯示：" in script
    assert "（每次送出可重新選擇）" in script
    assert 'aria-live="polite"' in script
    assert "function resetCommunityIdentityPreviews(container)" in script
    assert "resetCommunityIdentityPreviews(form);" in script
    assert "post.viewer_can_delete" in script
    assert "comment.viewer_can_delete" in script
    assert "async function fetchCommunityAuth(url, options = {})" in script
    assert "return fetchCommunityAuth(url, {" in script
    assert 'credentials: "same-origin"' in script
    assert "assertAuthenticatedRequestCurrent(requestContext)" in script


def test_community_mutations_reuse_id_only_for_ambiguous_results() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    scope = script.split(
        "function communityMutationSupportsIdempotency", maxsplit=1
    )[1].split("function createCommunityMutationId", maxsplit=1)[0]
    submitter = script.split(
        "async function submitCommunityJson", maxsplit=1
    )[1].split("async function refreshCommunityHub", maxsplit=1)[0]

    assert "const pendingCommunityMutationIds = new Map();" in script
    assert "canonicalCommunityMutationPayload(payload)" in submitter
    assert 'window.crypto?.randomUUID?.()' in script
    assert 'headers: { "X-Community-Mutation-ID": mutationId }' in submitter
    assert "pendingCommunityMutationIds.get(mutationKey)" in submitter
    assert "pendingCommunityMutationIds.set(mutationKey, mutationId)" in submitter
    assert "if (error?.status && error.status < 500)" in submitter
    assert submitter.count("pendingCommunityMutationIds.delete(mutationKey)") == 2

    for mutation_path in (
        'url === "/community/posts"',
        'url === "/community/questions"',
        'url === "/community/chat"',
        'url === "/experience-submissions"',
        r"\/comments$/.test(url)",
        r"\/answers$/.test(url)",
        'url === "/community/conversations"',
        r"\/accept$/.test(url)",
        r"\/messages$/.test(url)",
        'url === "/community/blocks"',
        'url === "/community/reports"',
    ):
        assert mutation_path in scope


def test_web_notification_center_and_explicit_email_opt_in_are_present() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="notification-button"' in html
    assert 'id="notification-dialog"' in html
    assert 'id="notification-center-list"' in html
    assert 'id="notification-delete-all"' in html
    assert "全部已讀" in html
    assert "全部刪除" in html
    assert 'name="email_notifications"' in html
    assert "只有勾選並儲存後才排入寄送" in html
    assert 'fetchJson("/account/notifications?limit=50")' in script
    assert 'fetchJson("/account/notifications/read-all"' in script
    assert 'method: "DELETE"' in script
    assert 'data-delete-notification' in script
    assert "合作校來源更新" in script
    assert 'id="catalogue-source-status"' not in html
    assert 'values.get("email_notifications") === "on"' in script
    assert "紙本送件以送達日計算" in html
    assert "官方規定更新" in script
    assert "查看逐項變更" in script
    assert 'data-notification-changes' in script
    assert "result.matches_current_plan" in script
    assert "請先確認目前的申請背景，再核對這則歷史通知" in script
    assert "查看官方來源" in script
    assert 'target="_blank" rel="noreferrer"' in script
    assert "notificationOfficialSourceUrl" in script
    assert ".notification-center-item" in styles
    assert ".notification-official-source" in styles
    assert ".notification-badge" in styles
    assert "min-height: 44px" in styles


def test_application_calendar_combines_official_and_personal_planning() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="calendar"' in html
    assert 'id="application-calendar-grid"' in html
    assert 'id="calendar-event-form"' in html
    assert 'id="calendar-event-school"' in html
    assert 'id="calendar-conflict-center"' in html
    assert 'id="calendar-conflict-list"' in html
    assert 'id="calendar-task-schedule-center"' in html
    assert 'id="calendar-task-schedule-list"' in html
    assert 'name="preparation_days"' in html
    assert 'name="status"' in html
    assert "Google 日曆" in script
    assert "downloadCalendarEvents" in script
    assert "BEGIN:VCALENDAR" in script
    assert "officialCalendarEvents" in script
    assert "workflowDeadlineEvents" in script
    assert "ensureApplicationCalendarWorkflows" in script
    assert "dateCandidates" not in script
    assert "return workflowDeadlineEvents();" in script
    assert "step.deadline_source_url" in script
    assert "dateCandidates(partner.application_deadline)" not in script
    assert "dateCandidates(detail" not in script
    assert 'workflow.review_status === "published"' in script
    assert "這是尚未完成正式發布的參考流程" in script
    assert "精確期限已有來源，但流程尚未正式發布。" in script
    assert "紙本文件必須在此日前送達指定收件單位" in script
    assert "exchange-guide-calendar-events" in script
    assert 'id="calendar-sync-panel"' in html
    assert 'data-calendar-provider="google"' in html
    assert 'fetchJson("/calendar-sync/events"' in script
    assert 'entitlementFeatureEnabled("external_calendar_sync")' in script
    assert "外部日曆同步是進階功能" in script
    assert "撤銷舊同步網址" in script
    assert 'fetchJson("/calendar/conflicts/analyze"' in script
    assert 'entitlementFeatureEnabled("application_plan_conflicts")' in script
    assert 'fetchJson("/calendar/tasks/schedule"' in script
    assert 'entitlementFeatureEnabled("smart_reminders")' in script
    assert "scheduledPreparationEvents" in script
    assert "updateCalendarTaskStatus" in script
    assert "data-calendar-task-status" in script
    assert "school_name: event.schoolName" in script
    assert "has-plan-conflict" in script
    assert "subscription_url" in script
    assert ".application-calendar-layout" in styles
    assert ".calendar-conflict-center" in styles
    assert ".calendar-conflict-card" in styles
    assert ".calendar-task-schedule-center" in styles
    assert ".calendar-task-schedule-card" in styles
    assert ".calendar-task-status select" in styles
    assert ".calendar-day.has-plan-conflict" in styles
    assert "min-width: 44px" in styles


def test_unverified_partner_deadlines_are_presented_as_reference_schedules() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "function partnerDeadlineReference(item)" in script
    assert 'label: "合作校參考時程"' in script
    assert "適用年度待確認" in script
    assert 'id="favorites-title"' in html
    assert "資格與申請時程" in html

    function_names = [
        "renderPartnerTableRow",
        "renderPartnerCard",
        "renderComparison",
        "renderPrimaryFacts",
        "renderProgramOptions",
        "renderUniversityOverview",
        "renderQuickDecisionFit",
        "renderSearchResults",
    ]
    for index, function_name in enumerate(function_names):
        start = script.index(f"function {function_name}")
        end = script.index("\nfunction ", start + 1) if index < len(function_names) - 1 else len(script)
        function_block = script[start:end]
        assert "partnerDeadlineReference(" in function_block, function_name

    assert '<span>合作校截止日</span>' not in script
    assert '["合作校截止日", (item) => item.application_deadline || "依公告"]' not in script
    assert '["合作校截止", localizedPartnerValue' not in script
    assert 'localizedPartnerValue(option, "application_deadline", "application_deadline")' not in script


def test_paper_workflow_distinguishes_send_and_arrival_deadlines() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "workflowArrivalDeadlinePending" in script
    assert 'if (!value) return "";' in script
    assert "最晚寄出：${formatDate(submission.send_by_at)}" in script
    assert "必須送達：${formatDate(submission.arrival_deadline_at)}" in script
    assert "必須送達：待確認（不要只以寄出日判斷）" in script
    assert "submission.arrival_deadline_at" in script
    assert 'step.deadline_status !== "verified_exact"' in script
    assert "!step.deadline_reminder_eligible" in script
    assert "目前只有參考時程，沒有當期精確日期。" in script
    assert "這個日期不會加入行事曆或截止提醒" in script
    assert "適用學年度：" in script
    assert "workflow.applicability_note" in script


def test_workflow_ui_records_manual_submission_progress_without_uploading_proof_files() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

    assert "renderWorkflowSubmissionProgress" in script
    assert "handleSubmissionProgressAction" in script
    assert 'fetchJson("/account/submission-progress"' in script
    assert "data-submission-action" in script
    assert "proof_metadata" in script
    assert "submissionProgressActions" in script
    assert "沒有回條，手動標記完成" in script
    assert "完成規定的所有紙本與線上／電子郵件 部分" in script
    assert "學生手動" in script
    assert "await loadAccountWorkspace({ homeSchool: activeHomeSchool() });" in script
    assert "error.status === 409 && current" in script
    assert "[408, 502, 503, 504].includes(error.status)" in script
    assert "已載入最新版本，請確認後再操作" in script
    assert "本次結果尚未確認" in script
    assert "系統不會自動重送" in script
    assert "await hydrateAccountWorkspace();" in script
    assert "if (activeItem) loadApplicationWorkflow(activeItem);" in script
    assert 'document.querySelectorAll("[data-submission-progress-key]")' in script
    assert "if (stepDetails) stepDetails.open = true;" in script
    assert "只保存證明種類、編號與時間，不上傳或保存證明原檔。" in script
    assert "平台不會代送，也不會把這些標記當成校方正式收件結果。" in script
    assert ".workflow-progress" in styles
    assert ".workflow-proof-fields" in styles
    assert ".workflow-progress dd > span" in styles
    assert "min-height: 44px" in styles


def test_student_plan_connects_matching_budget_scholarships_and_documents() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="personal-plan-snapshot"' in html
    assert 'id="recommended-match-list"' in html
    assert 'id="budget-form"' in html
    assert 'id="document-workspace-list"' in html
    assert 'id="scholarship-match-summary"' in html
    assert "function partnerMatch" in script
    assert "function nextPlanAction" in script
    assert "function renderBudgetPlanner" in script
    assert "function scholarshipMatch" in script
    assert "function renderDocumentWorkspace" in script
    assert ".personal-plan-snapshot" in styles
    assert ".recommended-match-card" in styles
    assert ".budget-layout" in styles


def test_application_center_turns_each_document_into_an_independent_form_page() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'href="#application-center"' in html
    assert 'data-university-page="application-center"' in html
    assert 'data-university-page="application-form"' in html
    assert 'id="application-context-form"' in html
    assert 'id="application-profile-form"' in html
    assert 'id="application-document-form"' in html
    assert 'id="download-application-packet"' in html
    assert "#application-form=" in script
    assert "loadApplicationTemplates" in script
    assert "generateApplicationPdf" in script
    assert "APPLICATION_DOCUMENT_STATUSES" in script
    assert "applicationFieldHasValue" in script
    assert "applicationTemplateReviewed" in script
    assert "invalidateApplicationReview" in script
    assert "applicationPrintSidesLabel" in script
    assert "applicationAttachmentOrder" in script
    assert "附件順序" in script
    assert "待確認官方單雙面規定" in script
    assert 'data-application-review-template' in script
    assert "reviewed_version: template.version" in script
    assert "reviewed_content_sha256: preview.review_content_sha256" in script
    assert 'id="application-review-preview"' in html
    assert "逐欄預覽" in script
    assert "留白（不會猜測）" in script
    assert "refreshApplicationReviewPreview" in script
    assert "/application-center/manifest" in script
    assert "if (!state.dashboard) {" in script
    assert 'data-application-status-template' in script
    assert 'fetch("/application-center/pdf"' in script
    assert 'id="application-download-dialog"' in html
    assert 'id="application-download-stats"' in html
    assert 'id="application-download-list"' in html
    assert "伺服器不會永久保存這次產生的 PDF" in html
    assert "applicationFilenameFromDisposition" in script
    assert "downloadApplicationBlob" in script
    assert "renderApplicationDownloadDialog" in script
    assert "X-Application-Packet-Pages" in script
    assert "X-Application-Storage" in script
    assert "invalid_attachment_fields" in script
    assert "附件無法加入列印包" in script
    assert ".application-center-layout" in styles
    assert ".application-form-layout" in styles
    assert ".application-status-control" in styles
    assert ".application-review-control" in styles
    assert ".application-review-preview" in styles
    assert ".application-review-field-list" in styles
    assert ".application-print-note" in styles
    assert ".application-packet-print" in styles
    assert ".application-download-dialog" in styles
    assert ".application-download-stats" in styles
    assert ".application-download-list" in styles
    assert ".application-download-privacy" in styles
    assert "min-height: 44px" in styles


def test_application_center_separates_official_requirements_from_preparation_tools() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="application-requirement-list"' in html
    assert "當期文件與官方表格" in html
    assert "可填寫的準備工具" in html
    assert "不代表當期校方必備文件" in html
    assert "沒有確認的份數或表格不會被當成正式版本" in html
    assert "/application-center/catalog" in script
    assert "renderApplicationDocumentCatalog" in script
    assert "下載校方正式表格" in script
    assert "查看官方規定" in script
    assert "份數待確認" in script
    catalog = script.split("function renderApplicationDocumentCatalog()", 1)[1].split(
        "\nfunction ", 1
    )[0]
    key = script.split("function applicationCatalogContextKey(", 1)[1].split(
        "\nasync function ", 1
    )[0]
    assert "state.applicationDocumentCatalogContextKey === applicationCatalogContextKey()" in catalog
    assert "!catalog?.workflow_found || !catalog.items?.length" in catalog
    assert "目前沒有可安全套用的結構化文件目錄" in catalog
    assert "JSON.stringify([homeSchool" in key
    for field in ("target_school", "department", "academic_year", "application_round"):
        assert f'"{field}"' in key
    assert "template.official_download_url" in script
    assert "下載校方原始表格" in script
    assert ".application-requirement-item" in styles
    assert ".application-official-download" in styles


def test_application_generation_gate_preserves_progressive_login_and_free_forms() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="application-generation-gate"' in html
    assert "function applicationDocumentGenerationEnabled()" in script
    assert 'entitlementFeatureEnabled("application_document_generation")' in script
    assert "登入後使用自動填表與列印套件" in script
    assert "申請規定、官方來源與校方原始表格仍可免登入免費查看" in script
    assert "自動填表與申請文件套件是進階功能" in script
    assert "登入後目前免費使用，系統不會扣款" in script
    assert 'data-application-generation-login' in script
    assert 'class="application-template-official"' in script
    assert "if (!applicationDocumentGenerationEnabled()) return null;" in script
    assert ".application-generation-gate" in styles
    assert ".application-template-official" in styles


def test_application_forms_remember_shared_fields_without_persisting_sensitive_ids() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="application-remember-profile"' in html
    assert 'id="clear-application-profile-memory"' in html
    assert 'id="application-autofill-status"' in html
    assert "function rememberApplicationField" in script
    assert "function persistApplicationProfileMemory" in script
    assert "function clearApplicationProfileMemory" in script
    assert "APPLICATION_PERSISTENT_PROFILE_KEYS" in script
    assert '"id_number",\n    "birth_date",\n    "passport_number",\n    "guardian_id_number",' in script
    assert "delete state.applicationAnswers[template.id][field.id]" in script
    assert ".application-memory-controls" in styles
    assert ".application-autofill-status" in styles


def test_application_forms_encrypt_general_drafts_and_require_per_file_consent() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'id="application-draft-sync-status"' in html
    assert 'id="application-file-consent-dialog"' in html
    assert 'id="application-file-consent-form"' in html
    assert "登入不代表同意上傳" in html
    assert "不同檔案、新版本都要重新同意" in html
    assert "/account/application-drafts" in script
    assert "function applicationDraftSafeProfile" in script
    assert "function applicationDraftSafeAnswers" in script
    assert 'field.field_type !== "files"' in script
    assert "function scheduleApplicationFormDraftSync" in script
    assert "application_draft_revision_conflict" not in script
    assert "current_draft" in script
    assert "function openApplicationFileConsent" in script
    assert "function submitApplicationFileConsent" in script
    assert "function deleteApplicationVaultFile" in script
    assert "function loadApplicationVaultFile" in script
    assert 'payload.append("consent", "true")' in script
    assert "敏感原檔預設只用於本次分頁" in script
    assert ".application-draft-sync-status" in styles
    assert ".application-file-consent-dialog" in styles
    assert ".application-file-preview-row.is-encrypted" in styles


def test_workflow_issue_reporting_uses_school_gate_and_separate_admin_queue() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")
    review_html = (STATIC_DIR / "content-review.html").read_text(encoding="utf-8")
    review_script = (STATIC_DIR / "content-review.js").read_text(encoding="utf-8")
    review_styles = (STATIC_DIR / "content-review.css").read_text(encoding="utf-8")

    assert 'id="workflow-issue-report-dialog"' in html
    assert 'id="workflow-issue-report-form"' in html
    assert 'name="official_source_url"' in html
    assert "不要填寫姓名、電子郵件、電話、學號或其他聯絡資料" in html
    assert "回報不會直接修改學生看到的正式規定" in html
    assert "data-workflow-issue-report" in script
    assert "state.account?.catalog_home_university" in script
    assert "openWorkflowIssueReport" in script
    assert "submitWorkflowIssueReport" in script
    assert '"/application-workflow-issue-reports"' in script
    assert '"X-Content-Report-Mutation-ID"' in script
    assert "issue_report_snapshot" in script
    workflow_key_block = script.split("function workflowContextKey", 1)[1].split(
        "function workflowRequestParams", 1
    )[0]
    assert "state.applicationContext.application_round" in workflow_key_block
    close_block = script.split("function closeWorkflowIssueReport", 1)[1].split(
        "function openWorkflowIssueReport", 1
    )[0]
    assert "state.workflowIssueReportSubmitting && !force" in close_block
    assert "workflowIssueReportPending" in script
    assert "window.sessionStorage.setItem" in script.split(
        "function persistWorkflowIssueReportPending", 1
    )[1].split("function clearWorkflowIssueReportPending", 1)[0]
    assert "workflowIssueReportRequestId" in script
    stored_state_block = script.split("function clearStoredAuthenticatedState", 1)[1].split(
        "function readStoredAuthenticatedState", 1
    )[0]
    assert "preserveWorkflowIssueReportPending" in stored_state_block
    assert "readWorkflowIssueReportPending()" in script.split(
        "function readStoredAuthenticatedState", 1
    )[1].split("function readStoredState", 1)[0]
    submit_block = script.split("async function submitWorkflowIssueReport", 1)[1].split(
        "function workflowSubmissionProgressKey", 1
    )[0]
    assert "requestId !== state.workflowIssueReportRequestId" in submit_block
    assert 'form.querySelectorAll("button, input, select, textarea")' in submit_block
    assert "new AbortController()" in submit_block
    assert "workflowIssueReportResponseMatches(response, payload)" in submit_block
    response_match_block = script.split("function workflowIssueReportResponseMatches", 1)[
        1
    ].split("async function submitWorkflowIssueReport", 1)[0]
    for response_field in (
        "home_school",
        "school_name",
        "workflow_id",
        "workflow_version",
        "workflow_snapshot",
        "category",
        "description",
        "official_source_url",
    ):
        assert f"response.{response_field}" in response_match_block
    assert 'addEventListener("cancel", (event)' in script
    assert "event.preventDefault();" in script.split(
        '$("#workflow-issue-report-dialog").addEventListener("cancel"', 1
    )[1].split("});", 1)[0]
    assert ".workflow-issue-report-dialog" in styles

    assert 'id="workflow-issue-report-queue"' in review_html
    assert 'id="workflow-issue-report-status-filter"' in review_html
    assert "學生回報不會自動建立 revision、核准或發布" in review_html
    assert "loadWorkflowIssueReports" in review_script
    assert "reviewWorkflowIssueReport" in review_script
    assert '"/admin/application-workflow-issue-reports"' in review_script
    assert '"X-Content-Report-Mutation-ID"' in review_script
    assert "workflowIssueReportRequestSequence" in review_script
    issue_load_block = review_script.split("async function loadWorkflowIssueReports", 1)[1].split(
        "function createWorkflowIssueReviewMutationId", 1
    )[0]
    assert "requestSequence !== state.workflowIssueReportRequestSequence" in issue_load_block
    review_block = review_script.split("async function reviewWorkflowIssueReport", 1)[1].split(
        "function approvalProgress", 1
    )[0]
    assert "[404, 409].includes(error?.status)" in review_block
    assert "await loadWorkflowIssueReports();" in review_block
    assert "new AbortController()" in review_block
    assert "error.status >= 500" in review_block
    assert "const refreshResult = await loadWorkflowIssueReports();" in review_block
    assert 'return "superseded"' in issue_load_block
    assert 'return "failed"' in issue_load_block
    assert 'document.querySelectorAll("[data-workflow-issue-report-id]")' in review_block
    assert "step.rule_id" in script.split("function renderWorkflowStep", 1)[1].split(
        "function createCommunityMutationId", 1
    )[0]
    assert ".workflow-issue-report-card" in review_styles


def test_application_pages_keep_primary_actions_visible_and_move_explanations_into_disclosures() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert '<h2 id="application-center-title">申請文件</h2>' in html
    assert "只填一次，自動套入文件" not in html
    assert "線上完成資料、產生可列印 PDF" not in html
    assert "系統會只列出需要的文件" not in html
    assert "在任何文件填過的共用欄位" not in html
    assert '<details class="application-compact-help">' in html
    assert "填寫說明" in html
    assert "列印提醒" in html
    assert "function applicationFieldInput(template, field, inputId" in script
    assert 'class="application-field-help"' in script
    assert '<div><dt>版本</dt>' not in script
    assert 'badge.textContent = template.official_layout ? "官方格式" : "申請整理"' in script
    assert ".application-field-help > summary" in styles
    assert ".application-compact-help > summary" in styles


def test_registration_uses_email_first_and_the_school_is_shown_and_locked_instead_of_verified() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert 'name="email_verification_token"' in html
    assert 'id="request-email-verification"' in html
    assert 'id="profile-dialog"' in html
    assert 'fetchJson("/auth/email-verification/request"' in script
    assert ".profile-verification-summary" in styles
    # The student card check is gone: no upload panel, no calls to the removed endpoints.
    for gone in ('id="student-card-front"', 'id="student-card-back"', 'id="student-verification-step"',
                 'id="verify-student-card"', "不保存證件照片"):
        assert gone not in html, gone
    for gone in ("/auth/student-verification", "verifyStudentCard", "clearStudentCardFiles",
                 "data-student-verification-provider", "student_verification"):
        assert gone not in script, gone
    # The school is shown, and the field is switched off while the 3-day lock runs.
    assert 'id="profile-school-note"' in html
    assert "school_change_locked_until" in script
    assert "form.elements.home_university.disabled = Boolean(lockedUntil)" in script
    assert "學校選定後 3 天內不能更換" in script
    assert 'id="onboarding-lock-note"' in html and "state.chooseSchoolForAccount" in script


def test_account_workspace_sync_has_conflict_merge_offline_retry_and_sensitive_boundary() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "accountWorkspaceRevisions" in script
    assert "accountWorkspaceBases" in script
    assert "accountWorkspacePending" in script
    assert "accountWorkspaceSyncLanes" in script
    assert "function sanitizeAccountWorkspacePayload" in script
    assert "function mergeAccountWorkspaces" not in script
    assert "function mergeAccountWorkspaceConflict" in script
    assert "function mergeWorkspaceSet" in script
    assert "function mergeWorkspaceRecord" in script
    assert "error.status === 409" in script
    assert "function drainAccountWorkspaceSync" in script
    assert "function startAccountWorkspaceDrain" in script
    assert "workspaceComparable(pending) === workspaceComparable(outgoing)" in script
    assert "state.accountWorkspacePending[key] || outgoing" in script
    assert "state.accountWorkspaceBases[key] = savedWorkspace" in script
    conflict_base_update = script.index(
        "state.accountWorkspaceBases[key] = sanitizeAccountWorkspacePayload("
    )
    assert script.index("const mergedPending = mergeAccountWorkspaceConflict(") < conflict_base_update
    assert conflict_base_update < script.index(
        "state.accountWorkspacePending[key] = mergedPending;"
    )
    assert script.index(
        "state.accountWorkspacePending[key] = mergedPending;"
    ) < script.index("applyAccountWorkspace(mergedPending);")
    assert "loadedAccountWorkspaceCanApply(savedWorkspace.home_school" in script
    assert "Math.max(" in script
    assert "function retryPendingWorkspaceSyncs" in script
    assert 'window.addEventListener("online", handleAccountConnectivityRestored)' in script
    assert 'window.addEventListener("offline", renderAccountWorkspaceSyncStatus)' in script
    assert 'authRestoreState: "pending"' in script
    assert "function readStoredAuthenticatedState(accountId)" in script
    assert "function clearStoredAuthenticatedState(" in script
    assert "async function handleAccountConnectivityRestored()" in script
    assert "state.authRestoreState === \"unavailable\"" in script
    assert "readStoredAuthenticatedState(state.account.id);" in script
    assert "state.authToken" not in script
    assert "function storeAuthToken" not in script
    initial_read_block = script.split("function readStoredState()", 1)[1].split(
        "async function loadSupportedUniversities", 1
    )[0]
    for private_state in (
        "state.favorites =",
        "state.applications =",
        "state.applicationProgress =",
        "state.documentReadiness =",
        "state.anonymousIdentity = parseStoredJson",
        "state.applicationProfile =",
        "state.applicationAnswers =",
    ):
        assert private_state not in initial_read_block
    restore_block = script.split("async function restoreAccount", 1)[1].split(
        "async function handleAccountConnectivityRestored", 1
    )[0]
    unavailable_block = restore_block.split("if (!error?.status)", 1)[1].split(
        "clearAuthenticatedClientState();", 1
    )[0]
    assert 'state.authRestoreState = "unavailable";' in unavailable_block
    assert "clearAuthenticatedClientState();" not in unavailable_block
    assert "accountWorkspaceSyncAccountId" in script
    assert "accountWorkspaceSyncErrors" in script
    assert "function resetAccountWorkspaceOwnerScopedState" in script
    assert "function clearAccountWorkspaceClientState()" in script
    assert "window.localStorage.removeItem(STORAGE_KEYS.workspaceSync)" in script
    assert "function clearAuthenticatedClientState()" in script
    assert "function handleExpiredAccountSession()" in script
    assert "authSessionEpoch: 0" in script
    assert "function captureAuthenticatedRequestContext()" in script
    assert "function assertAuthenticatedRequestCurrent(context)" in script
    assert "function authenticatedRequestContextIsCurrent(context)" in script
    assert "error.staleSession = true" in script
    assert "assertAuthenticatedRequestCurrent(requestContext);" in script
    assert 'response.status === 401' in script
    assert 'url !== "/auth/logout"' in script
    assert "error.sessionExpired = sessionExpired" in script
    cleanup_block = script.split("function clearAuthenticatedClientState()", 1)[1].split(
        "function handleExpiredAccountSession", 1
    )[0]
    for private_key in (
        "STORAGE_KEYS.eligibility",
        "STORAGE_KEYS.applicationProfileMemory",
        "STORAGE_KEYS.applicationProfileMemoryEnabled",
        "STORAGE_KEYS.budgetPlans",
        "STORAGE_KEYS.calendarEvents",
    ):
        assert private_key in cleanup_block
    logout_block = script.split("async function logoutAccount()", 1)[1].split(
        "async function deleteAccount", 1
    )[0]
    assert "clearAuthenticatedClientState();" in logout_block
    assert logout_block.index("clearAuthenticatedClientState();") < logout_block.index(
        "await logoutRequest;"
    )
    delete_block = script.split("async function deleteAccount()", 1)[1].split(
        "async function loadDashboard", 1
    )[0]
    assert "APPLICATION_SESSION_KEYS.accountDeletionMutation" in delete_block
    assert '"X-Account-Deletion-Mutation-ID": mutationId' in delete_block
    assert delete_block.index("sessionStorage.getItem") < delete_block.index(
        'fetchJson("/auth/me"'
    )
    assert "resetPrivatePlanningExperience({ renderRelated: false });" in cleanup_block
    load_workspace_block = script.split("async function loadAccountWorkspace", 1)[1].split(
        "function renderAccountState", 1
    )[0]
    assert "loadedAccountWorkspaceCanApply" in load_workspace_block
    assert "authenticatedRequestContextIsCurrent(requestContext)" in load_workspace_block
    assert "mergeAccountWorkspaceConflict" in load_workspace_block
    load_merge_index = load_workspace_block.index("mergeAccountWorkspaceConflict")
    assert load_merge_index < load_workspace_block.index(
        "state.accountWorkspaceBases[key] = remoteWorkspace;",
        load_merge_index,
    )
    assert "async function hydrateAccountWorkspace" in load_workspace_block
    schedule_block = script.split("function scheduleAccountWorkspaceSync()", 1)[1].split(
        "function loadedAccountWorkspaceCanApply", 1
    )[0]
    assert schedule_block.index("queueAccountWorkspaceSync") < schedule_block.index(
        "window.setTimeout"
    )
    assert 'id="account-workspace-sync-status"' in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert 'id="account-workspace-sync-retry"' in html
    assert ".workspace-sync-status" in styles
    assert '.workspace-sync-status[data-sync-state="failed"]' in styles
    payload_start = script.index("function accountWorkspacePayload")
    payload_end = script.index("function persistAccountWorkspaceLocally", payload_start)
    payload_block = script[payload_start:payload_end]
    assert "applicationProfile" not in payload_block
    assert "applicationAnswers" not in payload_block
    assert "applicationFiles" not in payload_block


def test_successful_login_closes_before_noncritical_account_hydration() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    accept_block = script.split("async function acceptAccountSession(session)", 1)[1].split(
        "async function restoreAccount", 1
    )[0]
    submit_block = script.split("async function submitAccountForm(form, endpoint)", 1)[1].split(
        "async function saveAccountProfile", 1
    )[0]

    assert_versioned_static_assets(html, ("app.js", "product-v2.css"))
    assert accept_block.index("closeAuthDialog();") < accept_block.index(
        "await Promise.allSettled(hydrationTasks)"
    )
    for loader in (
        "loadCommunityIdentityOptions()",
        "loadCommunityBoards()",
        "loadProductEntitlements()",
        "hydrateAccountWorkspace()",
        "loadCalendarSyncStatus()",
        "loadNotifications({ quiet: true })",
        "loadGlobalCommunity()",
    ):
        assert loader in accept_block
    assert "hydrationFailureCount" in submit_block
    assert "登入完成；部分資料暫時無法同步" in submit_block
    assert "await loadGlobalCommunity()" not in submit_block


def test_application_template_initialization_does_not_create_a_fake_workspace_write() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    function_block = script.split("function initializeApplicationSelections()", 1)[1].split(
        "async function loadApplicationTemplates", 1
    )[0]

    assert "persistApplicationContext({ sync: false });" in function_block


def test_personal_application_plan_uses_structured_api_and_progressive_login() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    for element_id in (
        "advisor-college",
        "advisor-department",
        "advisor-department-text",
        "eligibility-academic-year",
        "eligibility-application-round",
        "eligibility-preference-1",
        "eligibility-preference-2",
        "eligibility-preference-3",
        "eligibility-preference-4",
        "eligibility-preference-5",
    ):
        assert f'id="{element_id}"' in html
    assert 'id="advisor-department" name="department"' in html
    assert 'id="advisor-form"' in html
    assert '$("#advisor-form").addEventListener("submit"' in script
    assert "建立個人清單時才需要登入" in html
    assert 'fetchJson("/application-plan/evaluate"' in script
    assert 'if (!state.account)' in script
    assert 'openAuthDialog("register")' in script
    assert "function renderPersonalApplicationPlan" in script
    assert "personalApplicationPlan" in script
    assert "application_round: context.application_round" in script
    assert "degree_level: context.degree_level" in script
    assert ".application-plan-choice" in styles
    assert ".application-plan-checklist" in styles


def test_global_home_board_routing_and_following_are_present() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'href="#home"' in html
    assert 'href="#following"' in html
    assert 'href="#language-school-board"' in html
    assert 'href="#board=長庚大學"' in html
    assert 'data-follow-board="長庚大學"' in html
    assert '<span>發布看板</span>' in html
    assert '<select id="global-community-school" name="board_id"' in html
    assert 'id="global-community-compose" type="button" class="primary-button" aria-label="發一篇文章"' in html
    assert '<option value="public-study-abroad">公共留學板</option>' in html
    assert '<option value="language-school">語言學校板</option>' in html
    assert 'fetchJson("/community/boards")' in script
    assert '"#language-school-board": "language"' in script
    assert 'const LANGUAGE_SCHOOL_COMMUNITY_BOARD = "語言學校板"' in script
    assert "function activeCommunityBoardAccess()" in script
    assert "activeBoard && !activeBoard.can_post" in script
    assert "activeBoard.unavailable_reason" in script
    assert "查看驗證狀態" in script
    assert "校級看板限已驗證 Email 的會員查看、發文與留言，不限同校" in script
    assert 'document.body.classList.contains("global-home-mode")' in script
    assert 'document.body.classList.contains("cgu-community-mode")' in script
    assert 'renderCommunityPageContext(["cgu", "university"].includes(globalFeed))' in script
    assert "globalCommunityFeed" in script
    assert "followed_boards" in script
    assert "toggleBoardFollow" in script
    assert "applyAppRoute" in script


def test_departmental_partner_references_are_visible_but_blocked_from_formal_plans() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert '<option value="departmental_reference">院級參考／當期需確認</option>' in html
    assert "中央當期名單未列，請先向所屬學院或國際處確認是否開放" in script
    availability = script.split('if (status === "departmental_reference")', 1)[1].split(
        'if (status === "agreement_only")', 1
    )[0]
    assert "blocked: true" in availability
    assert "function partnerAvailabilityMeta" in script
    assert "function renderPartnerAvailabilityNotice" in script
    assert 'status === "departmental_reference"' in script
    assert 'button.disabled = blocked' in script
    assert 'if (availability.blocked)' in script
    choices = script.split("function renderEligibilityOptions(", 1)[1].split(
        "\nfunction ", 1
    )[0]
    assert '.filter(item=>!partnerAvailabilityMeta(item).blocked)' in choices
    assert ".partner-availability-notice" in styles


def test_home_application_cycles_are_structured_and_distinct_from_reference_dates() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    styles = (STATIC_DIR / "product-v2.css").read_text(encoding="utf-8")

    assert "校內梯次與申請時程" in html
    assert "請留意日期的適用年度與申請身分" in html
    assert "function applicationPeriodMeta" in script
    assert 'action_required: { label: "限符合身分者處理"' in script
    assert "item.deadline_at" in script
    assert "item.status_note" in script
    assert "item.reminder_eligible" in script
    assert ".deadline-status-pill" in styles
    assert ".deadline-period-meta" in styles
    assert ".deadline-reminder-note" in styles

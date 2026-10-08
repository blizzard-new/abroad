"""Explain all 39 baseline failures using fixed-candidate results, without waivers."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

NOTES = {
    'test_college_selects_ignore_partner_notes_and_follow_home_university': ('test_harness', 'Node extraction omitted region/country/availability and academic-render dependencies. Added unrelated UI stubs and actual availability function; college assertions retained.'),
    'test_match_missing_profile_fields_and_real_mismatches': ('test_harness', 'Node extraction omitted homeSelectionRules. Added explicit synthetic cycle fixture; all degree/language/escaping assertions retained.'),
    'test_safe_session_blocks_private_ips': ('test_environment', 'Machine proxy resolved proxy instead of mocked destination. Three tests pass with per-test proxy env isolation; production HTTP/SSRF/proxy configuration unchanged.'),
    'test_public_post_threads_hide_internal_author_ids_but_keep_owner_controls': ('own_response_contract', 'Own POST contained author_id; isolated guest legacy/detail GET already hid it. Removed own response ID and retained owner control. This was not proof of a guest ID leak.'),
    'test_high_risk_content_waits_for_review_and_sensitive_ids_are_blocked': ('runtime_privacy', 'Synthetic passport POST201 approved was visible to guest GET. Now422 before storage/publication; full-width numbers also checked.'),
    'test_account_deletion_keeps_public_content_but_removes_private_links': ('runtime_privacy', 'Synthetic real-name post/comment remained named after DELETE204 and guest GET; identities retained author links. Now deidentified, all linked identities purged, failed cleanup retriable. Supabase RPC routing simulated only.'),
    'test_runtime_includes_tracked_ntpu_public_baseline_with_isolated_private_data': ('runtime_coverage', 'Actual NTPU bundled profile existed but coverage handler counted only CGU/NTU. Counts now depend on matching home ownership; TKU4 profiles also covered without upgrading their partial status.'),
    'test_rules_advisor_works_while_ai_compatibility_endpoints_stay_paused': ('test_request_contract', 'Rewrite request omitted explicit AI consent and correctly returned422 before paused503. Test now sends consent and retains assertion of zero external AI calls; runtime consent gate unchanged.'),
    'test_guest_can_read_every_board_but_unverified_email_cannot_publish': ('board_contract_policy', 'Guest board IDs are cgu/ntpu/ntu/tku plus public boards, rather than two university: IDs. Early set assertion prevents subsequent assertions; cannot infer publish permissions from this failure alone.'),
    'test_ntpu_student_can_use_only_ntpu_board_for_posts_and_comments': ('board_contract_policy', 'Legacy university:ntpu lookup fails before publish assertions. Current code/test elsewhere permits verified-email cross-school board posts; matching-school requirement and OpenAPI metadata conflict. No permission policy changed.'),
    'test_post_rejects_unknown_or_conflicting_board_identifiers': ('response_contract', 'Unknown board returned422 with different wording. Later conflicting-board assertion was not reached; probe separately records actual response. Do not treat this whole test as verified.'),
    'test_identity_is_selected_per_submission_and_public_name_is_server_derived': ('response_contract', 'Verified-department option adds 學生 suffix. Early label assertion prevents later forged-name checks in this test; synthetic privacy checks cover a separate scenario.'),
    'test_reports_and_blocks_validate_targets_and_report_review_is_audited': ('response_contract', 'Self-report is denied403 versus expected422; remaining review/block assertions in this test are not reached. No authorization was weakened to satisfy the test.'),
    'test_author_can_delete_own_post_but_not_another_users_post': ('response_contract', 'Owner deletion returns200 with mutation receipt instead of expected204. Existing modern API uses a receipt; test does not reach final feed assertion. Contract reconciliation remains required.'),
    'test_experience_api_reads_cache_and_refreshes_selected_school': ('experience_source_contract', 'API adds public reference and bundled experience sources to the isolated one-source cache, yielding3. Counts and refresh assertions require source-scope reconciliation; no CGU source removed.'),
    'test_destination_profile_api_returns_verified_official_summary': ('localized_response_contract', 'City is localized 林肯, 坎特伯里 versus legacy English expectation. This does not prove missing destination data; remaining assertions still need reconciliation.'),
    'test_private_community_writes_expose_retry_mutation_header': ('runtime_missing_retry', 'Current legacy private handlers do not expose/implement the requested X-Community-Mutation-ID contract. Repository primitive tests alone cannot establish API retry behavior. Kept failing rather than advertising a fake capability.'),
    'test_workflow_issue_report_contract_exposes_retry_and_admin_review_paths': ('openapi_existing_contract', 'Existing runtime already required content-report mutation header; it is now a validated Header parameter in live/frozen schema.'),
    'test_account_deletion_exposes_dedicated_retry_mutation_header': ('openapi_existing_contract', 'Existing deletion header now explicit optional validated Header in schema, including no-header atomic production path.'),
    'test_api_contract_page_does_not_depend_on_csp_blocked_assets': ('runtime_docs', 'Default Swagger referenced CDN/script blocked by existing CSP. Now script-free OpenAPI download page and redoc redirect; CSP unchanged.'),
    'test_external_calendar_contract_documents_subscription_boundary': ('openapi_existing_contract', 'Documented actual existing401/403 release-mode responses without changing calendar permissions.'),
    'test_application_document_contract_keeps_official_forms_public_and_gates_generation': ('openapi_existing_contract', 'Documented actual generation401/403 responses; official discovery stays public and existing access gates unchanged.'),
    'test_document_completeness_contract_is_subscription_gated_and_ai_stays_paused': ('openapi_existing_contract', 'Documented actual error responses and made required explicit consent visible in multipart schema. No subscription/auth policy changed.'),
    'test_ai_compatibility_contract_is_explicitly_paused': ('openapi_existing_contract', 'Deprecated/503 annotations now describe existing paused compatibility routes. No AI provider enabled.'),
    'test_content_review_contract_exposes_nonpublishing_source_candidates': ('runtime_missing_admin_feature', 'Source replacement candidate schema/routes absent from current app, while historical workbench references them. Needs separate bounded restoration/integration of the review subsystem; no dummy routes added.'),
    'test_workflow_batch_stage_contract_is_snapshot_bound_and_nonpublishing': ('runtime_missing_admin_feature', 'Snapshot-bound review batch stage route absent. Restoring it requires review/concurrency/publication safeguards beyond TKU catalogue adaptation.'),
    'test_destination_profile_review_contract_requires_explicit_audited_promotion': ('runtime_missing_admin_feature', 'Destination review queue/promotion/publication/rollback API family absent from current app. This is an actual unavailable feature, not a schema-only typo.'),
    'test_application_workflow_publication_contract_exposes_safe_rollback': ('runtime_missing_admin_feature', 'Workflow publications/rollback/release-readiness routes absent from current app. Do not imply the existing UI or model files make this service operational.'),
}


def report(result_path, original_path, output):
    result = json.loads(result_path.read_text()); original = json.loads(original_path.read_text())
    failures = {r['id']:r for r in result['failures']}
    rows = []
    for old in original['failures']:
        name = old['id'].split('::')[-1]
        module = old['id'].split('::')[0]
        if name in NOTES:
            category, impact = NOTES[name]
        elif module in {'tests.test_frontend_contract','tests.test_independent_page_routing'}:
            category = 'ui_literal_contract'
            impact = 'Old literal/function-location/asset-version/element-ID assertion differs from current UI. Passing selected real-browser flows do not waive this failed assertion or prove all listed UI functions work. Needs behavior-level reconciliation in shared integration.'
        else:
            raise ValueError(f'Unclassified baseline failure: {old["id"]}')
        rows.append(dict(id=old['id'], category=category, actual_impact=impact,
            original_reason=old['reason'], candidate_status='failed' if old['id'] in failures else 'passed',
            candidate_reason=failures.get(old['id'],{}).get('reason'),
            acceptance_waiver=False))
    assert len(rows)==39
    payload = dict(tested_commit=result['tested_commit'], original_candidate=original['tested_commit'],
        baseline_commit=result['baseline_commit'], cases=rows, category_counts=dict(Counter(r['category'] for r in rows)),
        passed_original_cases=sum(r['candidate_status']=='passed' for r in rows),
        still_failed_original_cases=sum(r['candidate_status']=='failed' for r in rows),
        added_failures=result['added_failures'], matching_baseline_is_acceptable=False,
        decision_required=['Reconcile current verified-email board policy with older matching-school requirement and metadata, without granting rights in this school branch.',
            'Restore/integrate missing private retry and source/destination/workflow review API families with their real persistence and publication safeguards.',
            'Replace obsolete UI string/location expectations with reviewed behavior assertions; do not erase requirements solely for a green result.'],
        source_blockers='gap_triage.json:63 original gaps remain, with bounded public-search or conflict evidence.')
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:payload[k] for k in ['tested_commit','passed_original_cases','still_failed_original_cases','added_failures']}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--original-results',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report(a.results,a.original_results,a.output)

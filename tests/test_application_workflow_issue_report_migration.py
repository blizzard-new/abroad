from __future__ import annotations

import re
from pathlib import Path


MIGRATION = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "20260830100000_application_workflow_issue_reports.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").casefold()


def _function(name: str) -> str:
    match = re.search(
        rf"create or replace function public\.{re.escape(name)}\([\s\S]*?\n\$\$;",
        _sql(),
    )
    assert match is not None, f"missing function {name}"
    return match.group(0)


def test_issue_report_tables_are_private_and_do_not_reference_draft_governance() -> None:
    sql = _sql()
    reports = sql.split(
        "create table public.application_workflow_issue_reports",
        maxsplit=1,
    )[1].split(");", maxsplit=1)[0]

    assert "reporter_account_id text" in reports
    assert "references public.exchange_accounts(id) on delete set null" in reports
    assert "status text not null" in reports
    assert "reporter_deleted_at timestamptz" in reports
    assert "retained_until timestamptz" in reports
    assert "application_workflow_revisions" not in reports
    assert "application_workflow_review_events" not in reports
    assert sql.count("force row level security") >= 2
    assert (
        "revoke all on table public.application_workflow_issue_reports "
        "from public, anon, authenticated, service_role"
    ) in " ".join(sql.split())
    assert "grant select on table public.application_workflow_issue_reports to service_role" in sql


def test_submit_rpc_rebuilds_fingerprint_and_owns_pending_state_and_time() -> None:
    submit = _function("exchange_submit_application_workflow_issue_report")

    assert "from public.exchange_accounts account" in submit
    assert "for update" in submit
    assert "student_status_verified" in submit
    assert "verified_university" in submit
    assert "exchange_community_request_fingerprint" in submit
    for field in (
        "'workflow_key'",
        "'workflow_id'",
        "'workflow_version'",
        "'workflow_snapshot'",
        "'home_school'",
        "'school_name'",
        "'step_rule_id'",
        "'step_title'",
        "'college'",
        "'department'",
        "'academic_year'",
        "'application_round'",
        "'category'",
        "'description'",
        "'official_source_url'",
    ):
        assert field in submit
    assert "p_rate_limit is distinct from 10" in submit
    assert "p_rate_window_seconds is distinct from 3600" in submit
    assert "'pending'" in submit
    assert "clock_timestamp()" in submit
    assert "p_report ->> 'created_at'" not in submit
    assert "p_report ->> 'updated_at'" not in submit
    assert "p_report ->> 'status'" not in submit


def test_review_rpc_is_terminal_idempotent_and_cannot_publish_content() -> None:
    review = _function("exchange_review_application_workflow_issue_report")

    assert review.index("from public.exchange_accounts account") < review.index(
        "from public.application_workflow_issue_reports report"
    )
    assert review.count("for update") >= 2
    assert "in ('resolved', 'dismissed')" in review
    assert "exchange_community_request_fingerprint" in review
    assert "status = v_status" in review
    assert "make_interval(hours => 24)" in review
    assert "v_account.email" not in review
    assert "delete from public.application_workflow_issue_reports" not in review
    assert "application_workflow_revisions" not in review
    assert "application_workflow_review_events" not in review
    assert "published_application_workflows" not in review


def test_submit_rpc_rejects_private_or_non_host_source_urls_and_purge_is_status_agnostic() -> None:
    submit = _function("exchange_submit_application_workflow_issue_report")
    purge = _function("exchange_purge_expired_application_workflow_issue_reports")

    for blocked in (
        "10\\.",
        "192\\.168\\.",
        "172\\.(1[6-9]|2[0-9]|3[01])\\.",
        "169\\.254\\.",
        "192\\.0\\.2\\.",
        "198\\.51\\.100\\.",
        "203\\.0\\.113\\.",
        "(22[4-9]|23[0-9]|24[0-9]|25[0-5])\\.",
        "\\[",
    ):
        assert blocked in submit
    assert "^https://[^/?#:]+\\.[^/?#:]+" in submit
    assert "report.status = 'pending'" not in purge
    assert "reporter_account_id is null" in purge


def test_account_deletion_trigger_applies_reporter_and_reviewer_privacy_rules() -> None:
    sql = _sql()
    cleanup = _function("exchange_deidentify_application_workflow_issue_reports")

    assert "delete from public.application_workflow_issue_reports" in cleanup
    assert "status in ('resolved', 'dismissed')" in cleanup
    assert "status = 'pending'" in cleanup
    assert "reporter_account_id = null" in cleanup
    assert "make_interval(days => 90)" in cleanup
    assert "reviewer_account_id = null" in cleanup
    assert "reviewer_display_name = '已刪除管理員'" in cleanup
    assert "before delete on public.exchange_accounts" in sql
    assert "exchange_deidentify_application_workflow_issue_reports" in sql


def test_only_service_role_can_execute_issue_report_mutations() -> None:
    normalized = " ".join(_sql().split())

    for signature in (
        "exchange_submit_application_workflow_issue_report(text, text, text, jsonb, integer, integer)",
        "exchange_review_application_workflow_issue_report(text, text, text, jsonb)",
        "exchange_purge_expired_application_workflow_issue_reports()",
    ):
        assert f"revoke all on function public.{signature} from public, anon, authenticated, service_role" in normalized
        assert f"grant execute on function public.{signature} to service_role" in normalized

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import subprocess
import sys

import pytest

from exchange_info.repositories import (
    AccountDeletionMutationRequest,
    account_deletion_mutation_fingerprint,
)
from exchange_info.community_repositories import (
    CommunityReportReviewMutationRequest,
    PublicCommunityModerationRequest,
    PublicCommunityResourceType,
    community_mutation_fingerprint,
    private_community_mutation_fingerprint,
)
from exchange_info.models import CommunityReportStatus, ModerationStatus
from exchange_info.workflow_issue_reports import canonical_issue_report_fingerprint


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_supabase_runtime.py"
COMPOSE = ROOT / "supabase" / "runtime-validation" / "docker-compose.yml"


def _module():
    spec = importlib.util.spec_from_file_location("validate_supabase_runtime", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _context(module, *, project_name: str = "exchange-supabase-runtime-test"):
    return module.ValidationContext(
        project_name=project_name,
        postgres_port=15432,
        postgrest_port=13000,
        postgrest_secondary_port=13001,
        storage_port=15000,
        service_token="service-token",
        anon_token="anon-token",
    )


def test_runtime_compose_is_pinned_isolated_and_loopback_only() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert "supabase/postgres:17.6.1.136@sha256:" in text
    assert "postgrest/postgrest:v14.12@sha256:" in text
    assert "supabase/storage-api:v1.60.4@sha256:" in text
    assert text.count("postgrest/postgrest:v14.12@sha256:") == 2
    assert text.count("127.0.0.1:") == 4
    assert "EXCHANGE_RUNTIME_POSTGREST_SECONDARY_PORT" in text
    assert "/var/lib/postgresql/data" in text
    assert "storage-data:/var/lib/storage" in text
    assert "restart: \"no\"" in text
    assert "SUPABASE_URL" not in text
    assert "SUPABASE_SECRET_KEY" not in text


def test_runtime_account_deletion_payload_uses_canonical_application_fingerprint() -> None:
    module = _module()
    payload = module._account_deletion_payload("runtime-success-mutation-0002")
    request = AccountDeletionMutationRequest(
        mutation_id="runtime-success-mutation-0002",
        account_id="runtime-deletion-account",
        session_id="runtime-deletion-session",
        session_token_hash="a" * 64,
        email_fingerprint="b" * 64,
        pending_report_retention_days=90,
        replacement_name="已刪除帳號",
    )
    assert payload["p_request_fingerprint"] == account_deletion_mutation_fingerprint(request)
    assert payload["p_account_id"] == "runtime-deletion-account"
    assert payload["p_session_id"] == "runtime-deletion-session"


def test_runtime_account_deletion_replay_omits_deleted_actor_shape() -> None:
    module = _module()
    initial = module._account_deletion_payload("runtime-success-mutation-0002")
    replay = module._account_deletion_payload("runtime-success-mutation-0002", replay=True)
    assert replay["p_account_id"] is None
    assert replay["p_session_id"] is None
    assert replay["p_email_fingerprint"] is None
    assert replay["p_request_fingerprint"] == initial["p_request_fingerprint"]


def test_runtime_public_moderation_rollback_payload_is_canonical() -> None:
    module = _module()
    request = PublicCommunityModerationRequest(
        mutation_id="runtime-rollback-moderation",
        moderator_id="runtime-rollback-community-moderator",
        resource_type=PublicCommunityResourceType.POST,
        resource_id="runtime-rollback-moderation-post",
        expected_status=ModerationStatus.APPROVED,
        status=ModerationStatus.HIDDEN,
        note="此變更必須因 receipt 失敗而完整回滾。",
    )

    payload = module._public_moderation_payload(request)

    assert payload == {
        "p_mutation_id": "runtime-rollback-moderation",
        "p_request_fingerprint": (
            "f8edba89d399be037aed657a1e9602bd4d69e3298ec6742b61721228ed53d280"
        ),
        "p_moderator_id": "runtime-rollback-community-moderator",
        "p_resource_type": "post",
        "p_resource_id": "runtime-rollback-moderation-post",
        "p_expected_status": "approved",
        "p_status": "hidden",
        "p_note": "此變更必須因 receipt 失敗而完整回滾。",
    }
    assert payload["p_request_fingerprint"] == community_mutation_fingerprint(
        "moderation", request
    )


def test_runtime_account_deletion_validates_workflow_issue_lifecycle_and_purge() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'workflow_issue_rollback == "2|1|1|1"' in text
    assert 'workflow_issue_deletion == "2|0|0|1|1"' in text
    assert "retained_until=reporter_deleted_at+interval '90 days'" in text
    assert "retained_until=updated_at+interval '24 hours'" in text
    assert 'retention_state == "resolved|t|t|t|1"' in text
    assert 'pending_control == "1"' in text
    assert 'expired_states == "1|1"' in text
    assert '"exchange_purge_expired_application_workflow_issue_reports"' in text
    assert 'purged.payload.get("purged_count") == 2' in text
    assert 'purge_state == "0|0|1|1"' in text
    assert 'workflow_issue_cleanup == "0|0|0"' in text
    for summary, count in (
        ("workflow_issue_rollback_preserved_rows", 4),
        ("workflow_issue_pending_deidentified", 2),
        ("workflow_issue_closed_deleted", 1),
        ("workflow_issue_reviewer_deidentified", 1),
        ("workflow_issue_retention_shortened", 1),
        ("workflow_issue_purged", 2),
        ("workflow_issue_purge_controls_preserved", 1),
        ("workflow_issue_review_replays", 1),
    ):
        assert f'"{summary}": {count}' in text


def test_runtime_harness_validates_real_storage_cleanup_scope() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert '"storage_api_scope": "real_storage_api_file_backend"' in text
    assert "_validate_storage_orphan_cleanup" in text
    assert "runtime intentional Storage timeout" in text
    assert "repository.delete_objects([ACCOUNT_DELETION_OBJECT_KEY])" in text
    assert "exchange_list_pending_account_deletion_storage" in text
    assert "exchange_complete_pending_account_deletion_storage" in text
    assert "runtime intentional late receipt failure" in text


def test_runtime_schema_gate_includes_workflow_issue_report_tables() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "Expected at least 32 project tables" in text
    for table in (
        "application_workflow_issue_reports",
        "application_workflow_issue_report_reviews",
    ):
        assert text.count(f"'{table}'") >= 2
        assert f'("{table}", "id")' in text
        assert f"public.{table}', 'SELECT'" in text
        assert f"public.{table}', 'DELETE'" in text


def test_runtime_workflow_issue_payloads_use_canonical_fingerprints() -> None:
    module = _module()
    report = module._workflow_issue_report_payload()
    submit_payload = module._workflow_issue_submit_payload(
        "runtime-workflow-reporter",
        "runtime-workflow-submit-0001",
        report,
    )
    review_payload = module._workflow_issue_review_payload(
        "runtime-workflow-reviewer-a",
        "runtime-workflow-review-a-0001",
        report_id="runtime-workflow-report-0001",
        status="resolved",
        note="已逐頁核對官方公告，確認回報成立。",
    )

    assert submit_payload["p_report"] == report
    assert submit_payload["p_request_fingerprint"] == (
        canonical_issue_report_fingerprint(report)
    )
    assert submit_payload["p_request_fingerprint"] == (
        canonical_issue_report_fingerprint(dict(reversed(report.items())))
    )
    assert review_payload["p_request_fingerprint"] == (
        canonical_issue_report_fingerprint(review_payload["p_review"])
    )


def test_runtime_workflow_issue_rpc_permissions_are_service_role_only() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    signatures = (
        "public.exchange_submit_application_workflow_issue_report"
        "(text,text,text,jsonb,integer,integer)",
        "public.exchange_review_application_workflow_issue_report"
        "(text,text,text,jsonb)",
        "public.exchange_purge_expired_application_workflow_issue_reports()",
    )

    for signature in signatures:
        assert (
            f"has_function_privilege('anon', '{signature}', 'EXECUTE')" in text
        )
        assert (
            f"has_function_privilege('authenticated', '{signature}', 'EXECUTE')"
            in text
        )
        assert (
            f"has_function_privilege('service_role', '{signature}', 'EXECUTE')"
            in text
        )
    assert 'workflow_issue_rpc_privileges == "f|f|t|f|f|t|f|f|t|f"' in text


def test_runtime_workflow_issue_phase_is_wired_into_summary() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    phase = "workflow_issue_reports = _validate_workflow_issue_reports(context)"
    summary = '"workflow_issue_reports": workflow_issue_reports'

    assert text.count(phase) == 1
    assert text.count(summary) == 1
    assert text.index(phase) < text.index(summary)
    for key in (
        "submitted_reports",
        "submit_idempotent_replays",
        "submit_idempotency_conflicts",
        "rate_limited",
        "review_committed",
        "review_status_conflicts",
        "review_idempotent_replays",
        "review_idempotency_conflicts",
    ):
        assert f'"{key}"' in text


def test_runtime_report_review_payload_uses_canonical_community_fingerprint() -> None:
    module = _module()
    request = CommunityReportReviewMutationRequest(
        mutation_id="runtime-report-review-resolved",
        moderator_id="runtime-community-moderator-a",
        report_id="runtime-community-report-review-race",
        expected_status=CommunityReportStatus.PENDING,
        status=CommunityReportStatus.RESOLVED,
        note="審核員甲判定檢舉成立。",
    )
    payload = module._private_report_review_payload(request)
    assert payload["p_request_fingerprint"] == private_community_mutation_fingerprint(
        "community_report_review", request
    )
    assert payload["p_moderator_id"] == "runtime-community-moderator-a"


def test_runtime_harness_declares_two_instance_community_invariants() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "postgrest_secondary" in text
    assert "_validate_community_multi_instance_concurrency" in text
    assert '"postgrest_instances": 2' in text
    assert '"public_idempotent_replays": 1' in text
    assert '"private_report_review_conflicts": 1' in text
    assert "_validate_community_transaction_rollbacks" in text
    assert "runtime intentional late community receipt failure" in text
    assert '"late_failures_propagated": len(failure_mutations)' in text
    assert '"private_report_review_rollbacks": 1' in text
    assert '"partial_rows": 0' in text


def test_runtime_subprocess_timeout_is_bounded_and_redacts_sensitive_context(
    monkeypatch,
) -> None:
    module = _module()
    recorded: dict[str, object] = {}

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded.update(kwargs)
        raise subprocess.TimeoutExpired(
            command,
            kwargs["timeout"],
            output="sensitive partial stdout",
            stderr="sensitive partial stderr",
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    with pytest.raises(module.RuntimeValidationError) as captured:
        module._run(
            ["docker", "info"],
            input_text="sensitive SQL input",
            environment={"SENSITIVE_TOKEN": "sensitive environment value"},
            check=False,
            timeout_seconds=7,
        )

    message = str(captured.value)
    assert message == "Command timed out after 7 seconds: docker info"
    assert recorded["timeout"] == 7
    assert recorded["check"] is False
    assert "sensitive" not in message


def test_runtime_project_names_are_reserved_unique_and_ci_run_bound(
    monkeypatch,
) -> None:
    module = _module()
    tokens = iter(("11111111", "22222222", "33333333", "44444444"))
    monkeypatch.setattr(module.secrets, "token_hex", lambda _: next(tokens))
    monkeypatch.setattr(module.os, "getpid", lambda: 4321)

    local_a = module._new_project_name(environment={})
    local_b = module._new_project_name(environment={})
    ci_a = module._new_project_name(
        environment={"GITHUB_RUN_ID": "12345", "GITHUB_RUN_ATTEMPT": "1"}
    )
    ci_b = module._new_project_name(
        environment={"GITHUB_RUN_ID": "12345", "GITHUB_RUN_ATTEMPT": "2"}
    )

    names = {local_a, local_b, ci_a, ci_b}
    assert len(names) == 4
    assert all(name.startswith(module.PROJECT_NAME_PREFIX + "-") for name in names)
    assert all(re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) for name in names)
    assert "-local-" in local_a
    assert "-gh-" in ci_a
    assert ci_a != ci_b


def test_runtime_rejects_arbitrary_project_names_and_invalid_ci_identity() -> None:
    module = _module()

    with pytest.raises(SystemExit):
        module.parse_args(["--project-name", "production"])
    with pytest.raises(
        module.RuntimeValidationError,
        match="numeric run and attempt values",
    ):
        module._new_project_name(
            environment={"GITHUB_RUN_ID": "../production", "GITHUB_RUN_ATTEMPT": "1"}
        )


def test_runtime_compose_commands_forward_bounded_timeouts(monkeypatch) -> None:
    module = _module()
    context = _context(module)
    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(module, "_run", fake_run)

    module._compose(context, "up", "-d", "postgres", timeout_seconds=17)
    module._compose_with_input(context, ["exec", "-T", "postgres"], "select 1;")

    assert calls[0]["timeout_seconds"] == 17
    assert calls[1]["timeout_seconds"] == module.PSQL_TIMEOUT_SECONDS
    assert calls[1]["input_text"] == "select 1;"


def test_runtime_cleanup_fails_when_project_resources_remain(monkeypatch) -> None:
    module = _module()
    context = _context(module)
    commands: list[list[str]] = []

    monkeypatch.setattr(
        module,
        "_compose",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, "", ""),
    )

    def fake_run(command, **kwargs):
        commands.append(command)
        output = "leftover-container\n" if command[1:3] == ["container", "ls"] else ""
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(module, "_run", fake_run)

    with pytest.raises(module.RuntimeValidationError, match="residual container"):
        module._cleanup_runtime(context, phase="final")

    expected_label = f"label=com.docker.compose.project={context.project_name}"
    assert len(commands) == 3
    assert all(expected_label in command for command in commands)


def test_runtime_cleanup_stops_before_resource_queries_when_down_fails(
    monkeypatch,
) -> None:
    module = _module()
    context = _context(module)

    monkeypatch.setattr(
        module,
        "_compose",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args,
            17,
            "",
            "intentional down failure",
        ),
    )

    def unexpected_run(*args, **kwargs):
        raise AssertionError("resource queries must not run after compose down failure")

    monkeypatch.setattr(module, "_run", unexpected_run)

    with pytest.raises(module.RuntimeValidationError, match=r"cleanup failed \(17\)"):
        module._cleanup_runtime(context, phase="final")


def test_runtime_success_is_not_reported_when_final_cleanup_fails(
    monkeypatch,
    capsys,
) -> None:
    module = _module()
    cleanup_calls: list[str] = []

    monkeypatch.setattr(module, "_new_project_name", lambda: "exchange-supabase-runtime-test")
    monkeypatch.setattr(
        module,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )

    def fake_cleanup(context, *, phase):
        cleanup_calls.append(phase)
        if phase == "final":
            raise module.RuntimeValidationError("final cleanup timed out")

    monkeypatch.setattr(module, "_cleanup_runtime", fake_cleanup)
    monkeypatch.setattr(module, "validate_runtime", lambda context: {"status": "passed"})

    exit_code = module.main(
        [
            "--postgres-port",
            "15432",
            "--postgrest-port",
            "13000",
            "--postgrest-secondary-port",
            "13001",
            "--storage-port",
            "15000",
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 1
    assert cleanup_calls == ["preflight", "final"]
    assert '"status": "passed"' not in output.out
    assert "RUNTIME CLEANUP FAILED: final cleanup timed out" in output.err


def test_runtime_preflight_cleanup_failure_prevents_validation(
    monkeypatch,
    capsys,
) -> None:
    module = _module()
    validation_called = False

    monkeypatch.setattr(module, "_new_project_name", lambda: "exchange-supabase-runtime-test")
    monkeypatch.setattr(
        module,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )

    def fake_cleanup(context, *, phase):
        if phase == "preflight":
            raise module.RuntimeValidationError("preflight cleanup was not clean")

    def fake_validation(context):
        nonlocal validation_called
        validation_called = True
        return {"status": "passed"}

    monkeypatch.setattr(module, "_cleanup_runtime", fake_cleanup)
    monkeypatch.setattr(module, "validate_runtime", fake_validation)
    monkeypatch.setattr(module, "_collect_runtime_logs", lambda context: "")

    exit_code = module.main(
        [
            "--postgres-port",
            "15432",
            "--postgrest-port",
            "13000",
            "--postgrest-secondary-port",
            "13001",
            "--storage-port",
            "15000",
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 1
    assert validation_called is False
    assert "RUNTIME VALIDATION FAILED: preflight cleanup was not clean" in output.err
    assert '"status": "passed"' not in output.out


def test_runtime_clean_success_reports_cleanup_only_after_both_cleanup_phases(
    monkeypatch,
    capsys,
) -> None:
    module = _module()
    events: list[str] = []

    monkeypatch.setattr(module, "_new_project_name", lambda: "exchange-supabase-runtime-test")
    monkeypatch.setattr(
        module,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )
    monkeypatch.setattr(
        module,
        "_cleanup_runtime",
        lambda context, *, phase: events.append(phase),
    )

    def fake_validation(context):
        events.append("validation")
        return {"status": "passed"}

    monkeypatch.setattr(module, "validate_runtime", fake_validation)

    exit_code = module.main(
        [
            "--postgres-port",
            "15432",
            "--postgrest-port",
            "13000",
            "--postgrest-secondary-port",
            "13001",
            "--storage-port",
            "15000",
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert events == ["preflight", "validation", "final"]
    assert '"status": "passed"' in output.out
    assert '"cleanup_status": "passed"' in output.out
    assert '"compose_project": "exchange-supabase-runtime-test"' in output.out


def test_runtime_primary_failure_is_not_hidden_by_diagnostics_or_cleanup(
    monkeypatch,
    capsys,
) -> None:
    module = _module()

    monkeypatch.setattr(module, "_new_project_name", lambda: "exchange-supabase-runtime-test")
    monkeypatch.setattr(
        module,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""),
    )

    def fake_cleanup(context, *, phase):
        if phase == "final":
            raise module.RuntimeValidationError("secondary cleanup timeout")

    def fail_validation(context):
        raise module.RuntimeValidationError("primary invariant failed")

    monkeypatch.setattr(module, "_cleanup_runtime", fake_cleanup)
    monkeypatch.setattr(module, "validate_runtime", fail_validation)
    monkeypatch.setattr(
        module,
        "_collect_runtime_logs",
        lambda context: "RUNTIME LOG COLLECTION FAILED: secondary logs timeout",
    )

    exit_code = module.main(
        [
            "--postgres-port",
            "15432",
            "--postgrest-port",
            "13000",
            "--postgrest-secondary-port",
            "13001",
            "--storage-port",
            "15000",
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 1
    assert "RUNTIME VALIDATION FAILED: primary invariant failed" in output.err
    assert "RUNTIME LOG COLLECTION FAILED: secondary logs timeout" in output.err
    assert "RUNTIME CLEANUP FAILED: secondary cleanup timeout" in output.err
    assert output.err.index("primary invariant failed") < output.err.index(
        "secondary cleanup timeout"
    )


def test_runtime_source_keeps_all_subprocesses_bounded_and_project_scoped() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.count("subprocess.run(") == 1
    assert "timeout=timeout_seconds" in text
    assert text.count("timeout_seconds=COMPOSE_START_TIMEOUT_SECONDS") == 3
    assert "--project-name" not in text
    assert "com.docker.compose.project=" in text

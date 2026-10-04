import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from exchange_info import cli
from exchange_info.models import (
    AccountCalendarEvent,
    AccountNotificationPreferences,
    UserAccount,
    WebReleaseReadinessReport,
)
from exchange_info.repositories import JsonlAccountRepository


class _ReconfigurableStream:
    def __init__(self) -> None:
        self.options: dict[str, str] = {}

    def reconfigure(self, **options: str) -> None:
        self.options = options


def test_cli_configures_utf8_console_output(monkeypatch) -> None:
    stdout = _ReconfigurableStream()
    stderr = _ReconfigurableStream()
    monkeypatch.setattr(cli.sys, "stdout", stdout)
    monkeypatch.setattr(cli.sys, "stderr", stderr)

    cli._configure_console_encoding()

    assert stdout.options == {"encoding": "utf-8", "errors": "replace"}
    assert stderr.options == {"encoding": "utf-8", "errors": "replace"}


def test_run_notifications_cli_creates_due_web_reminder(tmp_path, capsys) -> None:
    repository = JsonlAccountRepository(tmp_path)
    due_date = (datetime.now(ZoneInfo("Asia/Taipei")) + timedelta(days=7)).date()
    account = UserAccount(
        display_name="CLI reminder",
        calendar_events=[
            AccountCalendarEvent(
                id="cli-deadline",
                title="CLI 測試截止",
                date=due_date.isoformat(),
                origin="official",
            )
        ],
        notification_preferences=AccountNotificationPreferences(
            deadline_reminder_days=[7],
            web_enabled=True,
            email_enabled=False,
        ),
    )
    repository.save_account(account)

    assert cli.main(["--data-dir", str(tmp_path), "run-notifications"]) == 0

    output = capsys.readouterr().out
    assert '"created_count":1' in output
    assert repository.list_notifications(account.id)[0].reminder_days == 7


def test_audit_web_release_cli_fails_closed_and_returns_machine_readable_report(
    tmp_path, monkeypatch, capsys
) -> None:
    report = WebReleaseReadinessReport(
        snapshot_fingerprint="0" * 64,
        release_ready=False,
        blocking_check_count=1,
        application_workflow_snapshot_fingerprint="1" * 64,
        destination_profile_snapshot_fingerprint="2" * 64,
    )
    monkeypatch.setattr(cli, "create_content_governance_store", lambda _path: object())
    monkeypatch.setattr(
        cli,
        "create_destination_profile_review_store",
        lambda _path: object(),
    )
    monkeypatch.setattr(
        cli,
        "load_destination_profiles",
        lambda _path, include_bundled_baseline: [],
    )
    monkeypatch.setattr(
        cli,
        "build_web_release_readiness",
        lambda _store, _profiles, _destination_store: report,
    )

    assert cli.main(["--data-dir", str(tmp_path), "audit-web-release"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["release_ready"] is False
    assert payload["blocking_check_count"] == 1
    assert payload["snapshot_fingerprint"] == "0" * 64

    monkeypatch.setattr(
        cli,
        "build_web_release_readiness",
        lambda _store, _profiles, _destination_store: report.model_copy(
            update={"release_ready": True, "blocking_check_count": 0}
        ),
    )
    assert cli.main(["--data-dir", str(tmp_path), "audit-web-release"]) == 0

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import (
    AccountSessionRecord,
    ApplicationSubmissionMethod,
    SubmissionProgressTransitionRequest,
    SubmissionProofMetadata,
    UserAccount,
    utc_now,
)
from exchange_info.storage import save_account_sessions, save_user_accounts
from exchange_info.submission_progress import transition_submission_progress


def _request(
    method: ApplicationSubmissionMethod,
    action: str,
    *,
    proof: SubmissionProofMetadata | None = None,
) -> SubmissionProgressTransitionRequest:
    return SubmissionProgressTransitionRequest(
        home_school="長庚大學",
        progress_key=f"長庚大學::workflow::v1::{method.value}",
        action=action,
        method=method,
        title=f"{method.value} submission",
        responsible_unit="國際事務處",
        send_by_at="2026-09-20T16:00:00+08:00",
        arrival_deadline_at="2026-09-25T16:00:00+08:00",
        proof_metadata=proof,
    )


@pytest.mark.parametrize(
    "method",
    [
        ApplicationSubmissionMethod.PAPER,
        ApplicationSubmissionMethod.ONLINE,
        ApplicationSubmissionMethod.EMAIL,
        ApplicationSubmissionMethod.IN_PERSON,
        ApplicationSubmissionMethod.MIXED,
    ],
)
def test_all_supported_submission_methods_advance_and_revert(method) -> None:
    progress = transition_submission_progress(None, _request(method, "start"))
    assert progress.status == "preparing"
    progress = transition_submission_progress(progress, _request(method, "submit"))
    assert progress.status == "submitted"
    proof = SubmissionProofMetadata(kind="tracking", reference="TRACK-123")
    progress = transition_submission_progress(
        progress,
        _request(method, "confirm_receipt", proof=proof),
    )
    assert progress.status == "receipt_confirmed"
    assert progress.proof_metadata.reference == "TRACK-123"
    progress = transition_submission_progress(progress, _request(method, "complete"))
    assert progress.status == "completed"
    progress = transition_submission_progress(progress, _request(method, "revert"))
    assert progress.status == "receipt_confirmed"


@pytest.mark.parametrize(
    "method",
    [ApplicationSubmissionMethod.PAPER, ApplicationSubmissionMethod.MIXED],
)
def test_paper_arrival_must_be_confirmed_before_completion(method) -> None:
    progress = transition_submission_progress(None, _request(method, "start"))
    progress = transition_submission_progress(progress, _request(method, "submit"))

    with pytest.raises(ValueError, match="必須先確認已送達"):
        transition_submission_progress(progress, _request(method, "complete"))


@pytest.mark.parametrize(
    "method",
    [
        ApplicationSubmissionMethod.ONLINE,
        ApplicationSubmissionMethod.EMAIL,
        ApplicationSubmissionMethod.IN_PERSON,
    ],
)
def test_non_paper_methods_can_be_manually_completed_without_a_receipt(method) -> None:
    progress = transition_submission_progress(None, _request(method, "start"))
    progress = transition_submission_progress(progress, _request(method, "submit"))
    progress = transition_submission_progress(progress, _request(method, "complete"))

    assert progress.status == "completed"
    assert progress.proof_metadata is None
    assert progress.recorded_by == "student"
    assert progress.platform_submitted is False
    reverted = transition_submission_progress(progress, _request(method, "revert"))
    assert reverted.status == "submitted"
    assert reverted.completed_at is None


def test_transition_rejects_skipped_states_and_changed_official_context() -> None:
    with pytest.raises(ValueError, match="請先標記為準備中"):
        transition_submission_progress(
            None,
            _request(ApplicationSubmissionMethod.EMAIL, "submit"),
        )

    started = transition_submission_progress(
        None,
        _request(ApplicationSubmissionMethod.EMAIL, "start"),
    )
    changed = _request(ApplicationSubmissionMethod.EMAIL, "submit")
    changed.responsible_unit = "不是原本的承辦單位"
    with pytest.raises(ValueError, match="送件規定已和開始記錄時不同"):
        transition_submission_progress(started, changed)


def test_receipt_metadata_is_server_recorded_and_never_claims_a_file_was_stored() -> None:
    method = ApplicationSubmissionMethod.ONLINE
    progress = transition_submission_progress(None, _request(method, "start"))
    progress = transition_submission_progress(progress, _request(method, "submit"))
    forged_time = datetime(2000, 1, 1, tzinfo=timezone.utc)
    proof = SubmissionProofMetadata(
        kind="submission_receipt",
        reference="  RECEIPT-001  ",
        file_name="  receipt.pdf  ",
        content_type="  APPLICATION/PDF  ",
        recorded_at=forged_time,
    )
    confirmed = transition_submission_progress(
        progress,
        _request(method, "confirm_receipt", proof=proof),
    )

    assert confirmed.proof_metadata is not None
    assert confirmed.proof_metadata.reference == "RECEIPT-001"
    assert confirmed.proof_metadata.file_name == "receipt.pdf"
    assert confirmed.proof_metadata.content_type == "application/pdf"
    assert confirmed.proof_metadata.recorded_at > forged_time
    assert confirmed.proof_metadata.source == "student_reported"
    assert confirmed.proof_metadata.original_file_stored is False


def _authenticated_client(tmp_path):
    account = UserAccount(display_name="送件測試學生")
    token = "submission-progress-test-token"
    save_user_accounts([account], tmp_path)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        tmp_path,
    )
    return TestClient(create_app(tmp_path)), {"Authorization": f"Bearer {token}"}


def test_submission_progress_api_requires_login_and_syncs_metadata_only(tmp_path) -> None:
    client, headers = _authenticated_client(tmp_path)
    payload = {
        "home_school": "長庚大學",
        "progress_key": "長庚大學::cgu-paper::v1::submit",
        "method": "paper",
        "title": "繳交校內紙本申請",
        "responsible_unit": "國際事務處",
        "send_by_at": "2026-09-20T16:00:00+08:00",
        "arrival_deadline_at": "2026-09-25T16:00:00+08:00",
        "note": "以送達期限為準",
    }
    assert client.post(
        "/account/submission-progress",
        json={**payload, "action": "start"},
    ).status_code == 401

    started = client.post(
        "/account/submission-progress",
        headers=headers,
        json={**payload, "action": "start"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "preparing"
    assert started.headers["cache-control"] == "private, no-store, max-age=0"
    assert started.headers["x-workspace-revision"] == "1"
    assert started.headers["x-submission-recorded-by"] == "student"
    assert started.headers["x-platform-submitted"] == "false"
    submitted = client.post(
        "/account/submission-progress",
        headers=headers,
        json={**payload, "action": "submit"},
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted"

    rejected_raw_file = client.post(
        "/account/submission-progress",
        headers=headers,
        json={
            **payload,
            "action": "confirm_receipt",
            "proof_metadata": {
                "kind": "tracking",
                "reference": "TRACK-123",
                "data_url": "data:application/pdf;base64,not-stored",
            },
        },
    )
    assert rejected_raw_file.status_code == 422

    confirmed = client.post(
        "/account/submission-progress",
        headers=headers,
        json={
            **payload,
            "action": "confirm_receipt",
            "proof_metadata": {
                "kind": "tracking",
                "reference": "TRACK-123",
                "recorded_at": "2000-01-01T00:00:00Z",
            },
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "receipt_confirmed"
    assert confirmed.json()["proof_metadata"]["recorded_at"] != "2000-01-01T00:00:00Z"
    assert confirmed.json()["proof_metadata"]["source"] == "student_reported"
    assert confirmed.json()["proof_metadata"]["original_file_stored"] is False
    assert confirmed.json()["recorded_by"] == "student"
    assert confirmed.json()["platform_submitted"] is False

    completed = client.post(
        "/account/submission-progress",
        headers=headers,
        json={**payload, "action": "complete"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    workspace = client.get(
        "/account/workspace",
        params={"home_school": "長庚大學"},
        headers=headers,
    ).json()["workspace"]
    saved = workspace["submission_progress"][payload["progress_key"]]
    assert datetime.fromisoformat(saved["arrival_deadline_at"]).astimezone(
        timezone.utc
    ) == datetime(2026, 9, 25, 8, tzinfo=timezone.utc)
    assert saved["proof_metadata"]["kind"] == "tracking"
    assert saved["proof_metadata"]["reference"] == "TRACK-123"
    assert saved["proof_metadata"]["source"] == "student_reported"
    assert saved["proof_metadata"]["original_file_stored"] is False
    assert saved["recorded_by"] == "student"
    assert saved["platform_submitted"] is False
    assert "data_url" not in str(saved)
    assert "base64" not in str(saved)

    reverted = client.post(
        "/account/submission-progress",
        headers=headers,
        json={**payload, "action": "revert"},
    )
    assert reverted.status_code == 200
    assert reverted.json()["status"] == "receipt_confirmed"

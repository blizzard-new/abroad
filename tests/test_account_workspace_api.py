import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import AccountSessionRecord, UserAccount, utc_now
from exchange_info.storage import save_account_sessions, save_user_accounts


def _client(tmp_path):
    account = UserAccount(display_name="同步測試學生")
    token = "account-workspace-test-token"
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


def _two_session_clients(tmp_path):
    account = UserAccount(display_name="跨裝置同步學生")
    tokens = ("workspace-device-a-token", "workspace-device-b-token")
    save_user_accounts([account], tmp_path)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
            for token in tokens
        ],
        tmp_path,
    )
    app = create_app(tmp_path)
    return (
        TestClient(app),
        TestClient(app),
        {"Authorization": f"Bearer {tokens[0]}"},
        {"Authorization": f"Bearer {tokens[1]}"},
    )


def _workspace(home_school="長庚大學"):
    return {
        "home_school": home_school,
        "favorite_schools": ["林肯大學 Lincoln University"],
        "application_schools": ["林肯大學 Lincoln University"],
        "application_progress": {
            "林肯大學 Lincoln University": {"choose": True, "documents": False}
        },
        "document_readiness": {
            "transcript": "ready",
            "language-certificate": "preparing",
        },
        "application_context": {
            "school_name": home_school,
            "target_school": "林肯大學 Lincoln University",
            "target_country": "紐西蘭",
            "program_type": "exchange",
            "college": "工學院",
            "department": "資訊工程學系",
            "degree_level": "大學部",
            "academic_year": "115",
            "application_round": "第一梯次",
            "semester": "fall",
            "flags": ["subsidy"],
        },
        "application_selections": {
            "exchange-application": {
                "selected": True,
                "copies": 2,
                "status": "pending_signature",
                "reviewed_version": "2026-07-16",
                "reviewed_content_sha256": "a" * 64,
                "reviewed_at": "2026-07-28T00:00:00Z",
            }
        },
        "submission_progress": {
            "長庚大學::paper-step": {
                "title": "繳交校內紙本申請",
                "method": "paper",
                "status": "submitted",
                "responsible_unit": "國際事務處",
                "send_by_at": "2026-09-20T08:00:00Z",
                "arrival_deadline_at": "2026-09-25T08:00:00Z",
                "submitted_at": "2026-09-19T08:00:00Z",
            }
        },
        "budget_plans": {
            "林肯大學 Lincoln University": {
                "currency": "NZD",
                "months": 5,
                "housing": 4_500,
                "food": 2_100,
                "transport": 700,
                "other": 900,
                "one_time": 52_000,
                "scholarship": 30_000,
                "saved_at": "2026-08-20T08:00:00Z",
            }
        },
        "deadline_events": [
            {
                "id": "lincoln-deadline",
                "title": "Lincoln 申請截止",
                "date": "2026-09-30",
                "category": "application",
                "reminder_days": 7,
                "school_name": "林肯大學 Lincoln University",
                "preparation_days": 21,
                "status": "preparing",
                "origin": "official",
            }
        ],
    }


def test_workspace_requires_login(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/account/workspace").status_code == 401
    assert client.put("/account/workspace", json=_workspace()).status_code == 401


def test_workspace_round_trip_syncs_only_non_sensitive_application_state(tmp_path) -> None:
    client, headers = _client(tmp_path)

    empty = client.get("/account/workspace", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["exists"] is False

    saved = client.put("/account/workspace", headers=headers, json=_workspace())
    assert saved.status_code == 200
    assert saved.json()["exists"] is True
    assert saved.json()["workspace"]["revision"] == 1
    assert saved.json()["workspace"]["document_readiness"]["transcript"] == "ready"

    restored = client.get("/account/workspace", headers=headers)
    assert restored.status_code == 200
    assert restored.json()["workspace"]["revision"] == 1
    assert restored.json()["workspace"]["favorite_schools"] == [
        "林肯大學 Lincoln University"
    ]
    assert restored.json()["workspace"]["deadline_events"][0]["date"] == "2026-09-30"
    assert restored.json()["workspace"]["deadline_events"][0]["school_name"] == (
        "林肯大學 Lincoln University"
    )
    assert restored.json()["workspace"]["deadline_events"][0]["preparation_days"] == 21
    assert restored.json()["workspace"]["deadline_events"][0]["status"] == "preparing"
    restored_context = restored.json()["workspace"]["application_context"]
    assert restored_context["department"] == "資訊工程學系"
    assert restored_context["application_round"] == "第一梯次"
    restored_selection = restored.json()["workspace"]["application_selections"][
        "exchange-application"
    ]
    assert restored_selection["reviewed_version"] == "2026-07-16"
    assert restored_selection["reviewed_content_sha256"] == "a" * 64
    assert restored_selection["reviewed_at"] == "2026-07-28T00:00:00Z"
    assert restored.json()["workspace"]["submission_progress"] == {}
    restored_budget = restored.json()["workspace"]["budget_plans"][
        "林肯大學 Lincoln University"
    ]
    assert restored_budget["currency"] == "NZD"
    assert restored_budget["housing"] == 4_500
    assert restored_budget["one_time"] == 52_000
    serialized = str(restored.json())
    assert "student_name" not in serialized
    assert "passport" not in serialized
    assert "answers" not in serialized
    assert "files" not in serialized


def test_workspace_is_isolated_by_home_school(tmp_path) -> None:
    client, headers = _client(tmp_path)
    assert client.put("/account/workspace", headers=headers, json=_workspace()).status_code == 200

    ntpu = _workspace("國立臺北大學")
    ntpu["favorite_schools"] = ["關西學院大學 (Kwansei Gakuin University)"]
    ntpu["application_schools"] = []
    ntpu["application_progress"] = {}
    assert client.put("/account/workspace", headers=headers, json=ntpu).status_code == 200

    cgu = client.get(
        "/account/workspace",
        params={"home_school": "長庚大學"},
        headers=headers,
    ).json()["workspace"]
    ntpu_saved = client.get(
        "/account/workspace",
        params={"home_school": "國立臺北大學"},
        headers=headers,
    ).json()["workspace"]
    assert cgu["favorite_schools"] == ["林肯大學 Lincoln University"]
    assert ntpu_saved["favorite_schools"] == [
        "關西學院大學 (Kwansei Gakuin University)"
    ]

    calendar = client.get("/calendar-sync", headers=headers).json()
    assert calendar["event_count"] == 1


def test_public_free_account_cannot_save_multiple_active_plans(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    client, headers = _client(tmp_path)
    payload = _workspace()
    payload["application_schools"].append("另一所合作校")

    response = client.put("/account/workspace", headers=headers, json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "免費方案同時只能進行一份申請計畫。"


def test_two_sessions_detect_revision_conflict_and_can_merge_without_data_loss(
    tmp_path,
) -> None:
    device_a, device_b, headers_a, headers_b = _two_session_clients(tmp_path)
    initial = device_a.put(
        "/account/workspace",
        headers=headers_a,
        json=_workspace(),
    ).json()["workspace"]
    snapshot_a = device_a.get("/account/workspace", headers=headers_a).json()["workspace"]
    snapshot_b = device_b.get("/account/workspace", headers=headers_b).json()["workspace"]
    assert initial["revision"] == snapshot_a["revision"] == snapshot_b["revision"] == 1

    snapshot_a["favorite_schools"].append("澳洲 A 大學")
    saved_a = device_a.put(
        "/account/workspace",
        headers=headers_a,
        json=snapshot_a,
    )
    assert saved_a.status_code == 200
    assert saved_a.json()["workspace"]["revision"] == 2

    snapshot_b["document_readiness"]["recommendation"] = "preparing"
    stale_b = device_b.put(
        "/account/workspace",
        headers=headers_b,
        json=snapshot_b,
    )
    assert stale_b.status_code == 409
    detail = stale_b.json()["detail"]
    assert detail["code"] == "workspace_revision_conflict"
    assert detail["current_workspace"]["revision"] == 2
    assert "澳洲 A 大學" in detail["current_workspace"]["favorite_schools"]

    merged = detail["current_workspace"]
    merged["document_readiness"].update(snapshot_b["document_readiness"])
    saved_b = device_b.put(
        "/account/workspace",
        headers=headers_b,
        json=merged,
    )
    assert saved_b.status_code == 200
    assert saved_b.json()["workspace"]["revision"] == 3
    restored = device_a.get("/account/workspace", headers=headers_a).json()["workspace"]
    assert "澳洲 A 大學" in restored["favorite_schools"]
    assert restored["document_readiness"]["recommendation"] == "preparing"


def test_workspace_rejects_sensitive_or_unknown_root_fields(tmp_path) -> None:
    client, headers = _client(tmp_path)
    sensitive_fields = {
        "application_answers": {"passport_number": "P123456789"},
        "files": {"passport": "raw-file-content"},
        "student_name": "王小明",
    }
    for field, value in sensitive_fields.items():
        payload = _workspace()
        payload[field] = value
        response = client.put("/account/workspace", headers=headers, json=payload)
        assert response.status_code == 422

    nested_sensitive = _workspace()
    nested_sensitive["budget_plans"]["林肯大學 Lincoln University"][
        "passport_number"
    ] = "P123456789"
    assert (
        client.put("/account/workspace", headers=headers, json=nested_sensitive).status_code
        == 422
    )

    persisted = b"\n".join(
        path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    )
    assert b"P123456789" not in persisted
    assert b"raw-file-content" not in persisted


def test_submission_progress_bumps_workspace_revision(tmp_path) -> None:
    client, headers = _client(tmp_path)
    saved = client.put(
        "/account/workspace",
        headers=headers,
        json=_workspace(),
    ).json()["workspace"]
    assert saved["revision"] == 1

    progressed = client.post(
        "/account/submission-progress",
        headers=headers,
        json={
            "home_school": "長庚大學",
            "progress_key": "長庚大學::offline-paper-step",
            "action": "start",
            "method": "paper",
            "title": "紙本申請送件",
            "responsible_unit": "國際事務處",
        },
    )
    assert progressed.status_code == 200
    current = client.get("/account/workspace", headers=headers).json()["workspace"]
    assert current["revision"] == 2
    assert current["submission_progress"]["長庚大學::offline-paper-step"]["status"] == "preparing"

    stale = client.put(
        "/account/workspace",
        headers=headers,
        json=saved,
    )
    assert stale.status_code == 409


def test_submission_progress_syncs_between_sessions_and_cannot_be_overwritten_by_workspace_put(
    tmp_path,
) -> None:
    device_a, device_b, headers_a, headers_b = _two_session_clients(tmp_path)
    saved = device_a.put(
        "/account/workspace",
        headers=headers_a,
        json=_workspace(),
    ).json()["workspace"]
    assert saved["revision"] == 1

    payload = {
        "home_school": "長庚大學",
        "progress_key": "長庚大學::cross-device-paper-step",
        "method": "paper",
        "title": "跨裝置紙本送件",
        "responsible_unit": "國際事務處",
        "send_by_at": "2026-09-20T08:00:00Z",
        "arrival_deadline_at": "2026-09-25T08:00:00Z",
    }
    started = device_a.post(
        "/account/submission-progress",
        headers=headers_a,
        json={**payload, "action": "start"},
    )
    assert started.status_code == 200
    assert started.headers["x-workspace-revision"] == "2"

    snapshot_b = device_b.get(
        "/account/workspace",
        headers=headers_b,
    ).json()["workspace"]
    assert snapshot_b["revision"] == 2
    assert snapshot_b["submission_progress"][payload["progress_key"]]["status"] == "preparing"

    snapshot_b["favorite_schools"] = ["不應覆寫送件狀態的大學"]
    snapshot_b["submission_progress"][payload["progress_key"]]["status"] = "completed"
    preserved = device_b.put(
        "/account/workspace",
        headers=headers_b,
        json=snapshot_b,
    )
    assert preserved.status_code == 200
    assert preserved.json()["workspace"]["revision"] == 3
    assert (
        preserved.json()["workspace"]["submission_progress"][payload["progress_key"]]["status"]
        == "preparing"
    )

    submitted = device_b.post(
        "/account/submission-progress",
        headers=headers_b,
        json={**payload, "action": "submit"},
    )
    assert submitted.status_code == 200
    assert submitted.headers["x-workspace-revision"] == "4"

    restored_a = device_a.get(
        "/account/workspace",
        headers=headers_a,
    ).json()["workspace"]
    assert restored_a["revision"] == 4
    assert restored_a["submission_progress"][payload["progress_key"]]["status"] == "submitted"


def test_ncu_document_state_round_trip_keeps_each_period_separate(tmp_path):
    from exchange_info.ncu_document_conditions import preparation_state_key
    client, headers = _client(tmp_path)
    payload = _workspace("國立中央大學")
    school = "首爾市立大學 University of Seoul"
    key = preparation_state_key(school,"116","第一梯次","第一學期")
    next_key = preparation_state_key(school,"116","第一梯次","第二學期")
    payload["application_context"]["partner_document_states"] = {
        key:{"host_admission_status":"accepted","housing_choice":"off_campus"},
        next_key:{"host_admission_status":"unknown","housing_choice":"unknown"},
    }
    saved = client.put("/account/workspace",headers=headers,json=payload)
    assert saved.status_code == 200
    restored = client.get("/account/workspace",headers=headers,params={"home_school":"國立中央大學"})
    assert restored.status_code == 200
    assert restored.json()["workspace"]["application_context"]["partner_document_states"] == payload["application_context"]["partner_document_states"]
    payload["application_context"]["partner_document_states"][key]["host_admission_status"] = "assumed"
    assert client.put("/account/workspace",headers=headers,json=payload).status_code == 422

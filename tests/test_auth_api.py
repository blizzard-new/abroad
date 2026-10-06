import hashlib
import json
from io import BytesIO
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import requests
from fastapi.testclient import TestClient
from PIL import Image

from exchange_info.legal_pages import TERMS_VERSION
from exchange_info.api import (
    _auth_cookie_secure_enabled,
    _browser_security_headers,
    create_app,
)
from exchange_info.models import AccountProviderLink, AuthProvider, UserAccount
from exchange_info.repositories import (
    AccountDeletionMutationResult,
    AccountDeletionMutationStatus,
    AccountRepositoryError,
    JsonlAccountRepository,
)
from exchange_info.storage import ensure_data_dirs
from exchange_info.student_verification import StudentCardVerification
from exchange_info.transient_auth import (
    LocalTransientAuthStore,
    TransientAuthStateKind,
)


class _JsonResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def _start_oauth(client: TestClient, provider: str) -> str:
    response = client.get(
        f"/auth/oauth/{provider}/start?terms={TERMS_VERSION}",
        follow_redirects=False,
    )
    assert response.status_code == 302
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


def _persisted_account_rows(data_dir) -> list[dict]:
    return [
        json.loads(line)
        for line in (data_dir / "processed" / "user_accounts.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]


def _card_image(color: tuple[int, int, int]) -> bytes:
    stream = BytesIO()
    Image.new("RGB", (900, 560), color).save(stream, format="JPEG")
    return stream.getvalue()


def _email_verification_token(client: TestClient, email: str) -> str:
    dispatched = client.post(
        "/auth/email-verification/request",
        json={"email": email},
    )
    assert dispatched.status_code == 202
    code = dispatched.json()["development_code"]
    assert code and len(code) == 6
    confirmed = client.post(
        "/auth/email-verification/confirm",
        json={"email": email, "code": code},
    )
    assert confirmed.status_code == 200
    return confirmed.json()["verification_token"]


def _student_verification_token(
    client: TestClient,
    headers: dict[str, str],
) -> str:
    result = StudentCardVerification(
        school_name="長庚大學",
        checks=("正反面不同", "校名可辨識", "學生證文字可辨識"),
    )
    with patch("exchange_info.api.verify_student_cards", return_value=result):
        response = client.post(
            "/auth/student-verification",
            headers=headers,
            data={"school_name": "長庚大學", "consent": "true"},
            files={
                "front": ("front.jpg", _card_image((230, 238, 246)), "image/jpeg"),
                "back": ("back.jpg", _card_image((210, 222, 232)), "image/jpeg"),
            },
        )
    assert response.status_code == 201
    assert response.json()["images_retained"] is False
    assert response.json()["ocr_text_retained"] is False
    assert response.json()["student_number_retained"] is False
    assert response.json()["verification_method"] == "student_card"
    return response.json()["verification_token"]


def _register(
    client: TestClient,
    *,
    email: str = "student@example.com",
    verify_student: bool = True,
) -> dict:
    email_verification_token = _email_verification_token(client, email)
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct-horse-2026",
            "display_name": "準備交換的小林",
            "email_verification_token": email_verification_token,
            "accept_terms": True,
        },
    )
    assert response.status_code == 201
    session = response.json()
    assert session["profile"]["email_verified"] is True
    assert session["profile"]["student_status_verified"] is False
    if not verify_student:
        return session
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    student_token = _student_verification_token(client, headers)
    confirmed = client.post(
        "/auth/student-verification/confirm",
        headers=headers,
        json={"verification_token": student_token},
    )
    assert confirmed.status_code == 200
    session["profile"] = confirmed.json()
    return session


def test_optional_auth_session_returns_null_for_public_browsing(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))

    anonymous = client.get("/auth/session")
    assert anonymous.status_code == 200
    assert anonymous.json() is None

    session = _register(client)
    authenticated = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {session['access_token']}"},
    )
    assert authenticated.status_code == 200
    assert authenticated.json()["email"] == "student@example.com"


def test_private_account_responses_are_never_cacheable(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    anonymous_session = client.get("/auth/session")
    session = _register(client)
    headers = {"Authorization": f"Bearer {session['access_token']}"}

    responses = [
        anonymous_session,
        client.get("/auth/session", headers=headers),
        client.get("/auth/me", headers=headers),
        client.get("/auth/me/export", headers=headers),
        client.get("/account/workspace", headers=headers),
        client.get("/account/vault/documents", headers=headers),
        client.get("/account/workspace"),
    ]

    for response in responses:
        assert response.headers["cache-control"] == "private, no-store, max-age=0"
        assert response.headers["pragma"] == "no-cache"
        vary = {item.strip().casefold() for item in response.headers["vary"].split(",")}
        assert {"cookie", "authorization", "x-anonymous-token"} <= vary


def test_documented_secure_cookie_flag_and_browser_security_headers(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("EXCHANGE_AUTH_SECURE_COOKIE", "true")
    client = TestClient(create_app(tmp_path))

    verification_token = _email_verification_token(client, "secure@example.com")
    registered = client.post(
        "/auth/register",
        json={
            "email": "secure@example.com",
            "password": "correct-horse-2026",
            "display_name": "安全測試學生",
            "email_verification_token": verification_token,
            "accept_terms": True,
        },
    )
    assert registered.status_code == 201
    auth_cookie = registered.headers["set-cookie"]
    assert "Secure" in auth_cookie
    assert "HttpOnly" in auth_cookie
    assert "SameSite=lax" in auth_cookie

    for response in (
        client.get("/"),
        client.get("/static/app.js"),
        client.get("/health"),
        client.get("/auth/session"),
    ):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["permissions-policy"] == (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        policy = response.headers["content-security-policy"]
        assert "default-src 'self'" in policy
        assert "script-src 'self'" in policy
        assert "script-src-attr 'none'" in policy
        assert "object-src 'none'" in policy
        assert "frame-ancestors 'none'" in policy


def test_auth_cookie_is_fail_closed_in_production() -> None:
    assert _auth_cookie_secure_enabled(
        {"EXCHANGE_ENVIRONMENT": "production"}
    ) is True
    assert _auth_cookie_secure_enabled(
        {
            "EXCHANGE_ENVIRONMENT": "production",
            "EXCHANGE_AUTH_SECURE_COOKIE": "false",
        }
    ) is True
    assert _auth_cookie_secure_enabled(
        {
            "EXCHANGE_ENVIRONMENT": "development",
            "EXCHANGE_AUTH_SECURE_COOKIE": "on",
        }
    ) is True
    assert _auth_cookie_secure_enabled(
        {
            "EXCHANGE_ENVIRONMENT": "development",
            "EXCHANGE_AUTH_SECURE_COOKIE": "false",
        }
    ) is False
    assert _browser_security_headers(
        {"EXCHANGE_ENVIRONMENT": "production"}
    )["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert "Strict-Transport-Security" not in _browser_security_headers(
        {"EXCHANGE_ENVIRONMENT": "development"}
    )


def test_email_account_profile_and_account_linked_community_identity(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    headers = {"Authorization": f"Bearer {session['access_token']}"}

    profile = client.get("/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["display_name"] == "準備交換的小林"
    assert profile.json()["providers"] == ["email"]
    assert profile.json()["student_status_verified"] is True
    assert profile.json()["verified_university"] == "長庚大學"
    assert profile.json()["student_verification_method"] == "student_card"
    assert profile.json()["student_verified_at"]

    updated = client.patch(
        "/auth/me",
        headers=headers,
        json={
            "display_name": "想去日本的小林",
            "home_university": "長庚大學",
            "target_countries": ["日本", "德國", "日本"],
            "application_stage": "documents",
            "followed_boards": ["長庚大學", "長庚大學"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["target_countries"] == ["日本", "德國"]
    assert updated.json()["followed_boards"] == ["長庚大學"]

    identity = client.post("/auth/community-identity", headers=headers)
    assert identity.status_code == 201
    assert identity.json()["display_name"] == "想去日本的小林"

    export = client.get("/auth/me/export", headers=headers)
    assert export.status_code == 200
    assert export.json()["community_identity_ids"] == [identity.json()["id"]]

    deleted = client.delete("/auth/me", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_supabase_account_deletion_replays_after_session_cascade(tmp_path) -> None:
    class ReceiptAccountRepository(JsonlAccountRepository):
        backend_name = "supabase"

        def __init__(self, data_dir):
            super().__init__(data_dir)
            self.receipts = {}
            self.storage_completions = []

        def commit_account_deletion(self, request):
            receipt = self.receipts.get(request.mutation_id)
            if receipt is not None:
                token_hash, result = receipt
                if token_hash != request.session_token_hash:
                    return AccountDeletionMutationResult(
                        status=AccountDeletionMutationStatus.IDEMPOTENCY_CONFLICT
                    )
                return result.model_copy(update={"idempotent": True})
            result = super().commit_account_deletion(request)
            if result.status == AccountDeletionMutationStatus.COMMITTED:
                result = result.model_copy(
                    update={"storage_object_keys": ["vault/deleted-account/file.bin"]}
                )
                self.receipts[request.mutation_id] = (
                    request.session_token_hash,
                    result,
                )
            return result

        def complete_account_deletion_storage(
            self,
            mutation_id,
            session_token_hash,
        ):
            self.storage_completions.append((mutation_id, session_token_hash))
            return AccountDeletionMutationStatus.COMMITTED

    ensure_data_dirs(tmp_path)
    repository = ReceiptAccountRepository(tmp_path)
    app = create_app(tmp_path, account_repository=repository)
    client = TestClient(app)
    first = _register(
        client,
        email="atomic-delete@example.com",
        verify_student=False,
    )
    mutation_id = "account-delete-replay-0001"
    headers = {
        "Authorization": f"Bearer {first['access_token']}",
        "X-Account-Deletion-Mutation-ID": mutation_id,
    }
    original_delete_objects = app.state.document_vault_service.repository.delete_objects
    storage_attempts = 0

    def flaky_delete_objects(object_keys):
        nonlocal storage_attempts
        storage_attempts += 1
        if storage_attempts == 1:
            raise OSError("temporary storage failure")
        original_delete_objects(object_keys)

    app.state.document_vault_service.repository.delete_objects = flaky_delete_objects

    deleted = client.delete("/auth/me", headers=headers)
    replayed = client.delete("/auth/me", headers=headers)
    conflict = client.delete(
        "/auth/me",
        headers={
            "Authorization": "Bearer different-account-delete-token",
            "X-Account-Deletion-Mutation-ID": mutation_id,
        },
    )

    assert deleted.status_code == 503
    assert replayed.status_code == 204
    assert conflict.status_code == 409
    assert deleted.headers["X-Account-Deletion-Mutation-ID"] == mutation_id
    assert replayed.headers["X-Account-Deletion-Mutation-ID"] == mutation_id
    assert len(repository.storage_completions) == 1
    assert storage_attempts == 2


def test_login_rejects_wrong_password_and_accepts_correct_password(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _register(client)

    wrong = client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "wrong-password"},
    )
    assert wrong.status_code == 401

    valid = client.post(
        "/auth/login",
        json={"email": "STUDENT@example.com", "password": "correct-horse-2026"},
    )
    assert valid.status_code == 200
    assert valid.json()["profile"]["email"] == "student@example.com"


def test_email_verification_is_required_and_student_upgrade_is_single_use(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))

    missing = client.post(
        "/auth/register",
        json={
            "email": "missing@example.com",
            "password": "correct-horse-2026",
            "display_name": "未驗證學生",
            "accept_terms": True,
        },
    )
    assert missing.status_code == 422

    first = _register(
        client,
        email="verified@example.com",
        verify_student=False,
    )
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    verification_token = _student_verification_token(client, first_headers)
    second_client = TestClient(client.app)
    second = _register(
        second_client,
        email="second@example.com",
        verify_student=False,
    )
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}

    confirmed = client.post(
        "/auth/student-verification/confirm",
        headers=first_headers,
        json={"verification_token": verification_token},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["student_status_verified"] is True

    reused = second_client.post(
        "/auth/student-verification/confirm",
        headers=second_headers,
        json={"verification_token": verification_token},
    )
    assert reused.status_code == 403


def test_student_card_verification_can_finish_on_another_app_instance(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    shared_store = LocalTransientAuthStore()
    upload_client = TestClient(
        create_app(tmp_path, transient_auth_store=shared_store)
    )
    session = _register(
        upload_client,
        email="cross-instance-card@example.com",
        verify_student=False,
    )
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    confirm_client = TestClient(
        create_app(tmp_path, transient_auth_store=shared_store)
    )
    verification_token = _student_verification_token(upload_client, headers)

    confirmed = confirm_client.post(
        "/auth/student-verification/confirm",
        headers=headers,
        json={"verification_token": verification_token},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["student_status_verified"] is True
    assert confirmed.json()["student_verification_method"] == "student_card"
    assert shared_store.get_state(
        hashlib.sha256(verification_token.encode("utf-8")).hexdigest(),
        TransientAuthStateKind.STUDENT_VERIFICATION_SESSION,
    ) is None


def test_student_card_evidence_remains_retryable_when_account_commit_fails(
    tmp_path,
) -> None:
    class FailingCommitRepository(JsonlAccountRepository):
        fail_commit = True

        def commit_student_verification(self, request):
            if self.fail_commit:
                raise AccountRepositoryError("temporary failure")
            return super().commit_student_verification(request)

    ensure_data_dirs(tmp_path)
    repository = FailingCommitRepository(tmp_path)
    shared_store = LocalTransientAuthStore()
    client = TestClient(
        create_app(
            tmp_path,
            account_repository=repository,
            transient_auth_store=shared_store,
        )
    )
    session = _register(
        client,
        email="retryable-card@example.com",
        verify_student=False,
    )
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    verification_token = _student_verification_token(client, headers)
    state_hash = hashlib.sha256(verification_token.encode("utf-8")).hexdigest()

    failed = client.post(
        "/auth/student-verification/confirm",
        headers=headers,
        json={"verification_token": verification_token},
    )

    assert failed.status_code == 503
    assert shared_store.get_state(
        state_hash,
        TransientAuthStateKind.STUDENT_VERIFICATION_SESSION,
    ) is not None
    repository.fail_commit = False
    retried = client.post(
        "/auth/student-verification/confirm",
        headers=headers,
        json={"verification_token": verification_token},
    )
    assert retried.status_code == 200
    assert retried.json()["student_status_verified"] is True
    assert shared_store.get_state(
        state_hash,
        TransientAuthStateKind.STUDENT_VERIFICATION_SESSION,
    ) is None


def test_profile_update_racing_account_delete_never_resurrects_account(
    tmp_path,
) -> None:
    class DeleteBeforeUpdateRepository(JsonlAccountRepository):
        delete_before_update = False

        def patch_account_fields(self, account_id, updates, *, expected=None):
            if self.delete_before_update:
                self.delete_before_update = False
                self.delete_account(account_id)
            return super().patch_account_fields(
                account_id,
                updates,
                expected=expected,
            )

    ensure_data_dirs(tmp_path)
    repository = DeleteBeforeUpdateRepository(tmp_path)
    client = TestClient(create_app(tmp_path, account_repository=repository))
    session = _register(
        client,
        email="deleted-during-update@example.com",
        verify_student=False,
    )
    repository.delete_before_update = True

    response = client.patch(
        "/auth/me",
        headers={"Authorization": f"Bearer {session['access_token']}"},
        json={"display_name": "Must not return"},
    )

    assert response.status_code == 401
    assert repository.find_account_by_email("deleted-during-update@example.com") is None


def test_global_community_posts_can_be_filtered_by_topic(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    auth_headers = {"Authorization": f"Bearer {session['access_token']}"}
    identity = client.post("/auth/community-identity", headers=auth_headers).json()
    community_headers = {
        **auth_headers,
        "X-Anonymous-ID": identity["id"],
        "X-Anonymous-Token": identity["access_token"],
    }

    response = client.post(
        "/community/posts",
        headers=community_headers,
        json={
            "board_id": "public-study-abroad",
            "post_type": "question",
            "topic": "housing",
            "country": "日本",
            "academic_year": "2027 秋季",
            "application_stage": "preparing",
            "title": "宿舍申請時間請益",
            "body": "想確認交換學生宿舍通常何時開放申請，以及是否需要先付押金。",
        },
    )
    assert response.status_code == 201

    housing = client.get("/community/posts", params={"topic": "housing"})
    assert housing.status_code == 200
    assert housing.json()[0]["post"]["academic_year"] == "2027 秋季"
    assert housing.json()[0]["post"]["board_id"] == "public-study-abroad"
    assert client.get("/community/posts", params={"topic": "visa"}).json() == []

    rejected_partner_board = client.post(
        "/community/posts",
        headers=community_headers,
        json={
            "school_name": "範例大學 Example University",
            "title": "不能建立任意大學板",
            "body": "任意合作校名稱不能繞過固定看板分類與校籍限制。",
        },
    )
    assert rejected_partner_board.status_code == 422


def test_public_and_cgu_boards_can_be_posted_and_filtered(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    auth_headers = {"Authorization": f"Bearer {session['access_token']}"}
    identity = client.post("/auth/community-identity", headers=auth_headers).json()
    community_headers = {
        **auth_headers,
        "X-Anonymous-ID": identity["id"],
        "X-Anonymous-Token": identity["access_token"],
    }

    for board, title in [
        ("公共留學板", "第一次準備留學該從哪裡開始"),
        ("長庚大學", "長庚交換校內申請文件討論"),
    ]:
        response = client.post(
            "/community/posts",
            headers=community_headers,
            json={
                "school_name": board,
                "post_type": "discussion",
                "topic": "application",
                "title": title,
                "body": "想和正在準備交換申請的同學一起整理實際流程與注意事項。",
            },
        )
        assert response.status_code == 201
        assert response.json()["school_name"] == board

    public_posts = client.get(
        "/community/posts", params={"school": "公共留學板"}
    ).json()
    cgu_posts = client.get(
        "/community/posts", params={"school": "長庚大學"}
    ).json()
    all_posts = client.get("/community/posts").json()

    assert [row["post"]["school_name"] for row in public_posts] == ["公共留學板"]
    assert [row["post"]["school_name"] for row in cgu_posts] == ["長庚大學"]
    assert {row["post"]["school_name"] for row in all_posts} == {
        "公共留學板",
        "長庚大學",
    }


def test_social_provider_buttons_report_configuration_state(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("FACEBOOK_APP_ID", raising=False)
    monkeypatch.delenv("FACEBOOK_APP_SECRET", raising=False)
    client = TestClient(create_app(tmp_path))

    providers = {row["provider"]: row for row in client.get("/auth/providers").json()}
    assert providers["email"]["enabled"] is True
    assert providers["google"]["enabled"] is False
    assert providers["facebook"]["enabled"] is False
    assert providers["apple"]["enabled"] is False


def test_google_oauth_state_is_bound_to_initiating_browser_cookie(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    app = create_app(tmp_path)
    initiating_browser = TestClient(app)
    other_browser = TestClient(app)

    start = initiating_browser.get(
        f"/auth/oauth/google/start?terms={TERMS_VERSION}",
        follow_redirects=False,
    )
    assert start.status_code == 302
    params = parse_qs(urlparse(start.headers["location"]).query)
    state = params["state"][0]
    flow_cookie = initiating_browser.cookies.get("exchange_guide_oauth_flow_google")
    assert flow_cookie
    assert flow_cookie != state
    set_cookie = start.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/auth/oauth/google/callback" in set_cookie
    assert "Max-Age=600" in set_cookie
    assert start.headers["cache-control"] == "no-store"
    assert start.headers["referrer-policy"] == "no-referrer"

    token_response = _JsonResponse({"access_token": "google-access-token"})
    user_response = _JsonResponse(
        {
            "sub": "google-subject",
            "email": "google-student@example.com",
            "email_verified": True,
            "name": "Google Student",
        }
    )
    with (
        patch("exchange_info.api.requests.post", return_value=token_response) as post,
        patch("exchange_info.api.requests.get", return_value=user_response) as get,
    ):
        rejected_other_browser = other_browser.get(
            "/auth/oauth/google/callback",
            params={"state": state, "code": "authorization-code"},
            follow_redirects=False,
        )
        assert rejected_other_browser.status_code == 403
        post.assert_not_called()
        get.assert_not_called()

        success = initiating_browser.get(
            "/auth/oauth/google/callback",
            params={"state": state, "code": "authorization-code"},
            follow_redirects=False,
        )
        assert success.status_code == 303
        assert success.headers["location"] == "/#auth=success"
        assert success.headers["cache-control"] == "no-store"
        assert success.headers["referrer-policy"] == "no-referrer"
        assert post.call_count == 1
        assert get.call_count == 1

        replay = initiating_browser.get(
            "/auth/oauth/google/callback",
            params={"state": state, "code": "replayed-code"},
            follow_redirects=False,
        )
    assert replay.status_code == 400
    assert post.call_count == 1
    assert get.call_count == 1
    assert initiating_browser.get("/auth/session").json()["email"] == (
        "google-student@example.com"
    )
    assert other_browser.get("/auth/session").json() is None


def test_google_oauth_callback_can_finish_on_another_app_instance(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    shared_store = LocalTransientAuthStore()
    start_browser = TestClient(
        create_app(tmp_path, transient_auth_store=shared_store)
    )
    callback_browser = TestClient(
        create_app(tmp_path, transient_auth_store=shared_store)
    )

    state = _start_oauth(start_browser, "google")
    flow_cookie = start_browser.cookies.get("exchange_guide_oauth_flow_google")
    assert flow_cookie
    wrong_browser = callback_browser.get(
        "/auth/oauth/google/callback",
        params={"state": state, "code": "authorization-code"},
        follow_redirects=False,
    )
    assert wrong_browser.status_code == 403

    token_response = _JsonResponse({"access_token": "google-access-token"})
    user_response = _JsonResponse(
        {
            "sub": "cross-instance-google-subject",
            "email": "cross-instance-google@example.com",
            "email_verified": True,
            "name": "Cross Instance Student",
        }
    )
    with (
        patch("exchange_info.api.requests.post", return_value=token_response),
        patch("exchange_info.api.requests.get", return_value=user_response),
    ):
        success = callback_browser.get(
            "/auth/oauth/google/callback",
            params={"state": state, "code": "authorization-code"},
            headers={
                "Cookie": f"exchange_guide_oauth_flow_google={flow_cookie}",
            },
            follow_redirects=False,
        )

    assert success.status_code == 303
    assert success.headers["location"] == "/#auth=success"
    assert callback_browser.get("/auth/session").json()["email"] == (
        "cross-instance-google@example.com"
    )
    assert start_browser.get(
        "/auth/oauth/google/callback",
        params={"state": state, "error": "access_denied"},
        follow_redirects=False,
    ).status_code == 400


def test_google_oauth_terminal_failures_consume_state_and_clear_flow_cookie(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    browser = TestClient(create_app(tmp_path))

    cancelled_state = _start_oauth(browser, "google")
    cancelled = browser.get(
        "/auth/oauth/google/callback",
        params={"state": cancelled_state, "error": "access_denied"},
        follow_redirects=False,
    )
    assert cancelled.status_code == 303
    assert cancelled.headers["location"] == "/#auth=cancelled"
    assert cancelled.headers["cache-control"] == "no-store"
    assert cancelled.headers["referrer-policy"] == "no-referrer"
    assert "Max-Age=0" in cancelled.headers["set-cookie"]
    assert browser.cookies.get("exchange_guide_oauth_flow_google") is None
    assert browser.get(
        "/auth/oauth/google/callback",
        params={"state": cancelled_state, "code": "replayed-code"},
        follow_redirects=False,
    ).status_code == 400

    missing_code_state = _start_oauth(browser, "google")
    missing_code = browser.get(
        "/auth/oauth/google/callback",
        params={"state": missing_code_state},
        follow_redirects=False,
    )
    assert missing_code.status_code == 422
    assert missing_code.headers["cache-control"] == "no-store"
    assert "Max-Age=0" in missing_code.headers["set-cookie"]
    assert browser.cookies.get("exchange_guide_oauth_flow_google") is None
    assert browser.get(
        "/auth/oauth/google/callback",
        params={"state": missing_code_state, "code": "replayed-code"},
        follow_redirects=False,
    ).status_code == 400

    provider_failure_state = _start_oauth(browser, "google")
    with patch(
        "exchange_info.api.requests.post",
        side_effect=requests.ConnectionError("provider unavailable"),
    ):
        provider_failure = browser.get(
            "/auth/oauth/google/callback",
            params={"state": provider_failure_state, "code": "provider-code"},
            follow_redirects=False,
        )
    assert provider_failure.status_code == 502
    assert provider_failure.headers["cache-control"] == "no-store"
    assert "Max-Age=0" in provider_failure.headers["set-cookie"]
    assert browser.cookies.get("exchange_guide_oauth_flow_google") is None
    assert browser.get(
        "/auth/oauth/google/callback",
        params={"state": provider_failure_state, "code": "replayed-code"},
        follow_redirects=False,
    ).status_code == 400

    malformed_code_state = _start_oauth(browser, "google")
    malformed_code = browser.get(
        "/auth/oauth/google/callback",
        params={"state": malformed_code_state, "code": "x"},
        follow_redirects=False,
    )
    assert malformed_code.status_code == 422
    assert malformed_code.headers["cache-control"] == "no-store"
    assert "Max-Age=0" in malformed_code.headers["set-cookie"]
    assert browser.cookies.get("exchange_guide_oauth_flow_google") is None
    assert browser.get(
        "/auth/oauth/google/callback",
        params={"state": malformed_code_state, "error": "access_denied"},
        follow_redirects=False,
    ).status_code == 400

    malformed_error_state = _start_oauth(browser, "google")
    malformed_error = browser.get(
        "/auth/oauth/google/callback",
        params={"state": malformed_error_state, "error": "x" * 121},
        follow_redirects=False,
    )
    assert malformed_error.status_code == 422
    assert malformed_error.headers["cache-control"] == "no-store"
    assert "Max-Age=0" in malformed_error.headers["set-cookie"]
    assert browser.get(
        "/auth/oauth/google/callback",
        params={"state": malformed_error_state, "error": "access_denied"},
        follow_redirects=False,
    ).status_code == 400


def test_google_oauth_start_rate_limit_bounds_state_creation(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    browser = TestClient(create_app(tmp_path))

    for _ in range(20):
        response = browser.get(
            f"/auth/oauth/google/start?terms={TERMS_VERSION}",
            follow_redirects=False,
        )
        assert response.status_code == 302
    limited = browser.get(
        f"/auth/oauth/google/start?terms={TERMS_VERSION}",
        follow_redirects=False,
    )
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "600"


def test_oauth_provider_path_mismatch_does_not_consume_valid_state(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    monkeypatch.setenv("FACEBOOK_APP_ID", "facebook-app-id")
    monkeypatch.setenv("FACEBOOK_APP_SECRET", "facebook-app-secret")
    browser = TestClient(create_app(tmp_path))
    state = _start_oauth(browser, "google")

    mismatched = browser.get(
        "/auth/oauth/facebook/callback",
        params={"state": state, "code": "authorization-code"},
        follow_redirects=False,
    )
    assert mismatched.status_code == 400
    cancelled = browser.get(
        "/auth/oauth/google/callback",
        params={"state": state, "error": "access_denied"},
        follow_redirects=False,
    )
    assert cancelled.status_code == 303


def test_google_verified_email_can_link_existing_email_account(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    app = create_app(tmp_path)
    existing_account_browser = TestClient(app)
    google_browser = TestClient(app)
    verified_email = "verified-link@example.com"
    existing_session = _register(
        existing_account_browser,
        email=verified_email,
        verify_student=False,
    )
    existing_account_id = existing_session["profile"]["id"]
    state = _start_oauth(google_browser, "google")

    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "google-access-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {
                    "sub": "verified-google-subject",
                    "email": verified_email,
                    "email_verified": True,
                    "name": "Verified Google Student",
                }
            ),
        ),
    ):
        callback = google_browser.get(
            "/auth/oauth/google/callback",
            params={"state": state, "code": "authorization-code"},
            follow_redirects=False,
        )

    assert callback.status_code == 303
    google_profile = google_browser.get("/auth/me").json()
    existing_profile = existing_account_browser.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {existing_session['access_token']}"
        },
    ).json()
    assert google_profile["id"] == existing_account_id
    assert google_profile["email"] == verified_email
    assert google_profile["email_verified"] is True
    assert google_profile["providers"] == ["email", "google"]
    assert existing_profile == google_profile

    account_rows = _persisted_account_rows(tmp_path)
    assert len(account_rows) == 1
    assert account_rows[0]["provider_links"] == [
        {"provider": "email", "subject": verified_email},
        {"provider": "google", "subject": "verified-google-subject"},
    ]


def test_verified_oauth_email_cannot_claim_legacy_unverified_email_account(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    app = create_app(tmp_path)
    legacy_email = "legacy-unverified@example.com"
    legacy_account = UserAccount(
        email=legacy_email,
        email_verified=False,
        display_name="Legacy Facebook Student",
        provider_links=[
            AccountProviderLink(
                provider=AuthProvider.FACEBOOK,
                subject="legacy-facebook-subject",
            )
        ],
    )
    app.state.account_repository.save_account(legacy_account)
    account_rows_before = _persisted_account_rows(tmp_path)
    google_browser = TestClient(app)
    state = _start_oauth(google_browser, "google")

    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "google-access-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {
                    "sub": "verified-google-subject",
                    "email": legacy_email,
                    "email_verified": True,
                    "name": "Verified Google Student",
                }
            ),
        ),
    ):
        callback = google_browser.get(
            "/auth/oauth/google/callback",
            params={"state": state, "code": "authorization-code"},
            follow_redirects=False,
        )

    assert callback.status_code == 409
    assert google_browser.get("/auth/session").json() is None
    assert _persisted_account_rows(tmp_path) == account_rows_before


def test_provider_subject_cannot_claim_verified_email_owned_by_another_account(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    app = create_app(tmp_path)
    provider_browser = TestClient(app)
    existing_account_browser = TestClient(app)
    provider_subject = "provider-only-google-subject"

    first_state = _start_oauth(provider_browser, "google")
    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "provider-only-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {
                    "sub": provider_subject,
                    "email_verified": False,
                    "name": "Provider Only Student",
                }
            ),
        ),
    ):
        first_callback = provider_browser.get(
            "/auth/oauth/google/callback",
            params={"state": first_state, "code": "provider-only-code"},
            follow_redirects=False,
        )
    assert first_callback.status_code == 303
    provider_profile_before = provider_browser.get("/auth/me").json()
    assert provider_profile_before["email"] is None
    assert provider_profile_before["providers"] == ["google"]

    occupied_email = "already-owned@example.com"
    existing_session = _register(
        existing_account_browser,
        email=occupied_email,
        verify_student=False,
    )
    existing_headers = {
        "Authorization": f"Bearer {existing_session['access_token']}"
    }
    existing_profile_before = existing_account_browser.get(
        "/auth/me",
        headers=existing_headers,
    ).json()
    account_rows_before = _persisted_account_rows(tmp_path)

    second_state = _start_oauth(provider_browser, "google")
    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "verified-email-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {
                    "sub": provider_subject,
                    "email": occupied_email,
                    "email_verified": True,
                    "name": "Provider Only Student",
                }
            ),
        ),
    ):
        conflicting_callback = provider_browser.get(
            "/auth/oauth/google/callback",
            params={"state": second_state, "code": "verified-email-code"},
            follow_redirects=False,
        )

    assert conflicting_callback.status_code == 409
    assert provider_browser.get("/auth/me").json() == provider_profile_before
    assert existing_account_browser.get(
        "/auth/me",
        headers=existing_headers,
    ).json() == existing_profile_before
    assert _persisted_account_rows(tmp_path) == account_rows_before


def test_same_provider_different_subject_cannot_share_verified_email(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-client-secret")
    app = create_app(tmp_path)
    first_subject_browser = TestClient(app)
    second_subject_browser = TestClient(app)
    shared_email = "one-google-identity@example.com"

    first_state = _start_oauth(first_subject_browser, "google")
    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "first-subject-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {
                    "sub": "first-google-subject",
                    "email": shared_email,
                    "email_verified": True,
                    "name": "First Google Student",
                }
            ),
        ),
    ):
        first_callback = first_subject_browser.get(
            "/auth/oauth/google/callback",
            params={"state": first_state, "code": "first-subject-code"},
            follow_redirects=False,
        )
    assert first_callback.status_code == 303
    first_profile_before = first_subject_browser.get("/auth/me").json()
    assert first_profile_before["providers"] == ["google"]
    account_rows_before = _persisted_account_rows(tmp_path)

    second_state = _start_oauth(second_subject_browser, "google")
    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "second-subject-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {
                    "sub": "second-google-subject",
                    "email": shared_email,
                    "email_verified": True,
                    "name": "Second Google Student",
                }
            ),
        ),
    ):
        conflicting_callback = second_subject_browser.get(
            "/auth/oauth/google/callback",
            params={"state": second_state, "code": "second-subject-code"},
            follow_redirects=False,
        )

    assert conflicting_callback.status_code == 409
    assert second_subject_browser.get("/auth/session").json() is None
    assert first_subject_browser.get("/auth/me").json() == first_profile_before
    assert _persisted_account_rows(tmp_path) == account_rows_before
    assert account_rows_before[0]["provider_links"] == [
        {"provider": "google", "subject": "first-google-subject"}
    ]


def test_facebook_unverified_email_does_not_link_or_persist_by_email(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    monkeypatch.setenv("FACEBOOK_APP_ID", "facebook-app-id")
    monkeypatch.setenv("FACEBOOK_APP_SECRET", "facebook-app-secret")
    app = create_app(tmp_path)
    existing_account_browser = TestClient(app)
    facebook_browser = TestClient(app)
    collision_email = "existing-email-account@example.com"
    existing_session = _register(
        existing_account_browser,
        email=collision_email,
        verify_student=False,
    )
    existing_headers = {
        "Authorization": f"Bearer {existing_session['access_token']}"
    }
    existing_account_id = existing_session["profile"]["id"]

    facebook_user = {
        "id": "stable-facebook-subject",
        "email": collision_email,
        "name": "Facebook Student",
        "picture": {"data": {"url": "https://example.com/facebook-avatar.jpg"}},
    }
    responses = [
        _JsonResponse({"access_token": "facebook-access-token-1"}),
        _JsonResponse(facebook_user),
        _JsonResponse({"access_token": "facebook-access-token-2"}),
        _JsonResponse(facebook_user),
    ]
    with patch("exchange_info.api.requests.get", side_effect=responses) as get:
        first_start = facebook_browser.get(
            f"/auth/oauth/facebook/start?terms={TERMS_VERSION}",
            follow_redirects=False,
        )
        assert first_start.status_code == 302
        first_state = parse_qs(urlparse(first_start.headers["location"]).query)[
            "state"
        ][0]
        first_callback = facebook_browser.get(
            "/auth/oauth/facebook/callback",
            params={"state": first_state, "code": "authorization-code-1"},
            follow_redirects=False,
        )
        assert first_callback.status_code == 303
        first_facebook_profile = facebook_browser.get("/auth/me").json()

        assert facebook_browser.post("/auth/logout").status_code == 204
        second_start = facebook_browser.get(
            f"/auth/oauth/facebook/start?terms={TERMS_VERSION}",
            follow_redirects=False,
        )
        assert second_start.status_code == 302
        second_state = parse_qs(urlparse(second_start.headers["location"]).query)[
            "state"
        ][0]
        second_callback = facebook_browser.get(
            "/auth/oauth/facebook/callback",
            params={"state": second_state, "code": "authorization-code-2"},
            follow_redirects=False,
        )
        assert second_callback.status_code == 303
        second_facebook_profile = facebook_browser.get("/auth/me").json()

    assert get.call_count == 4
    assert first_facebook_profile["id"] != existing_account_id
    assert first_facebook_profile["id"] == second_facebook_profile["id"]
    assert first_facebook_profile["email"] is None
    assert first_facebook_profile["email_verified"] is False
    assert first_facebook_profile["providers"] == ["facebook"]

    existing_profile = existing_account_browser.get(
        "/auth/me",
        headers=existing_headers,
    ).json()
    assert existing_profile["id"] == existing_account_id
    assert existing_profile["email"] == collision_email
    assert existing_profile["email_verified"] is True
    assert existing_profile["providers"] == ["email"]

    account_rows = _persisted_account_rows(tmp_path)
    assert len(account_rows) == 2
    by_id = {row["id"]: row for row in account_rows}
    facebook_row = by_id[first_facebook_profile["id"]]
    existing_row = by_id[existing_account_id]
    assert facebook_row["email"] is None
    assert facebook_row["email_verified"] is False
    assert facebook_row["provider_links"] == [
        {"provider": "facebook", "subject": "stable-facebook-subject"}
    ]
    assert existing_row["provider_links"] == [
        {"provider": "email", "subject": collision_email}
    ]

from __future__ import annotations

import hashlib
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.transient_auth import LocalTransientAuthStore
from exchange_info.verification_providers import (
    VerificationProviderError,
    authorization_url,
    new_pkce_pair,
    provider_runtime_configuration,
    validate_provider_identity,
    verification_provider_policy,
    verification_provider_status,
    verification_provider_statuses,
)


PROVIDER_ENV = (
    "EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_ID",
    "EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_SECRET",
    "EXCHANGE_NTPU_STUDENT_ENTRA_TENANT_ID",
)


class _JsonResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def _clear_provider_environment(monkeypatch) -> None:
    for name in PROVIDER_ENV:
        monkeypatch.delenv(name, raising=False)


def _configure_ntpu_entra(monkeypatch) -> None:
    monkeypatch.setenv("EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_ID", "ntpu-client-id")
    monkeypatch.setenv("EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_SECRET", "ntpu-client-secret")
    monkeypatch.setenv(
        "EXCHANGE_NTPU_STUDENT_ENTRA_TENANT_ID",
        "11111111-2222-3333-4444-555555555555",
    )


def _register(client: TestClient, email: str = "provider-owner@example.com") -> dict:
    dispatched = client.post(
        "/auth/email-verification/request",
        json={"email": email},
    )
    assert dispatched.status_code == 202
    confirmed = client.post(
        "/auth/email-verification/confirm",
        json={"email": email, "code": dispatched.json()["development_code"]},
    )
    assert confirmed.status_code == 200
    registered = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct-horse-2026",
            "display_name": "Provider QA",
            "email_verification_token": confirmed.json()["verification_token"],
            "accept_terms": True,
        },
    )
    assert registered.status_code == 201
    return registered.json()


def _headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def _login(
    client: TestClient,
    email: str = "provider-owner@example.com",
) -> dict:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "correct-horse-2026"},
    )
    assert response.status_code == 200
    return response.json()


def _start_ntpu_entra(client: TestClient, headers: dict[str, str]):
    response = client.get(
        "/auth/student-verification/oauth/ntpu-entra/start",
        headers=headers,
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers["location"]
    params = parse_qs(urlparse(location).query)
    return response, params


def test_provider_matrix_is_safe_by_default() -> None:
    statuses = verification_provider_statuses(environment={})
    by_id = {item.id: item for item in statuses}

    assert by_id["cgu-student-card"].enabled is True
    assert by_id["ntpu-student-card"].enabled is True
    assert by_id["cgu-entra"].availability == "school_partnership_required"
    assert by_id["cgu-school-email"].availability == "supporting_only"
    assert by_id["ntpu-entra"].availability == "configuration_required"
    assert by_id["ntpu-entra"].enabled is False
    assert all(item.accepts_school_password is False for item in statuses)
    assert all("secret" not in item.model_dump_json().casefold() for item in statuses)


def test_configured_ntpu_entra_builds_tenant_scoped_pkce_redirect() -> None:
    policy = verification_provider_policy("ntpu-entra")
    environment = {
        "EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_ID": "client-id",
        "EXCHANGE_NTPU_STUDENT_ENTRA_CLIENT_SECRET": "client-secret",
        "EXCHANGE_NTPU_STUDENT_ENTRA_TENANT_ID": "tenant.example.edu",
    }
    status = verification_provider_status(policy, environment)
    configuration = provider_runtime_configuration(policy, environment)
    verifier, challenge = new_pkce_pair()
    location = authorization_url(
        policy,
        configuration,
        redirect_uri="https://example.com/callback",
        state="opaque-state",
        code_challenge=challenge,
    )
    parsed = urlparse(location)
    params = parse_qs(parsed.query)

    assert status.enabled is True
    assert parsed.netloc == "login.microsoftonline.com"
    assert parsed.path.startswith("/tenant.example.edu/")
    assert params["state"] == ["opaque-state"]
    assert params["code_challenge_method"] == ["S256"]
    assert params["code_challenge"] == [challenge]
    assert params["scope"] == ["openid profile email"]
    assert "client-secret" not in location
    assert 43 <= len(verifier) <= 128


def test_entra_identity_requires_student_pattern_and_domain_allowlist() -> None:
    policy = verification_provider_policy("ntpu-entra")
    valid = validate_provider_identity(
        policy,
        {"sub": "stable-subject", "email": "S410987354@ms.ntpu.edu.tw"},
    )
    assert valid == "s410987354@ms.ntpu.edu.tw"

    with pytest.raises(VerificationProviderError, match="允許網域"):
        validate_provider_identity(
            policy,
            {"sub": "stable-subject", "email": "s410987354@example.com"},
        )
    with pytest.raises(VerificationProviderError, match="學生帳號格式"):
        validate_provider_identity(
            policy,
            {"sub": "stable-subject", "email": "staff@ms.ntpu.edu.tw"},
        )
    with pytest.raises(VerificationProviderError, match="識別碼"):
        validate_provider_identity(
            policy,
            {"email": "s410987354@ms.ntpu.edu.tw"},
        )


def test_google_identity_requires_verified_hosted_domain() -> None:
    policy = verification_provider_policy("ntpu-google-workspace")
    assert validate_provider_identity(
        policy,
        {
            "sub": "google-subject",
            "email": "s410987354@gm.ntpu.edu.tw",
            "email_verified": True,
            "hd": "gm.ntpu.edu.tw",
        },
    ) == "s410987354@gm.ntpu.edu.tw"
    with pytest.raises(VerificationProviderError, match="hosted domain"):
        validate_provider_identity(
            policy,
            {
                "sub": "google-subject",
                "email": "s410987354@gm.ntpu.edu.tw",
                "email_verified": True,
                "hd": "gmail.com",
            },
        )
    with pytest.raises(VerificationProviderError, match="已驗證 Email"):
        validate_provider_identity(
            policy,
            {
                "sub": "google-subject",
                "email": "s410987354@gm.ntpu.edu.tw",
                "email_verified": False,
                "hd": "gm.ntpu.edu.tw",
            },
        )


def test_provider_api_filters_school_and_disabled_start_fails_closed(
    tmp_path,
    monkeypatch,
) -> None:
    _clear_provider_environment(monkeypatch)
    client = TestClient(create_app(tmp_path))
    statuses = client.get(
        "/auth/student-verification/providers",
        params={"school_name": "國立臺北大學"},
    )
    assert statuses.status_code == 200
    assert {item["school_name"] for item in statuses.json()} == {"國立臺北大學"}
    assert all(item["accepts_school_password"] is False for item in statuses.json())

    unauthenticated = client.get(
        "/auth/student-verification/oauth/ntpu-entra/start",
        follow_redirects=False,
    )
    assert unauthenticated.status_code == 401
    session = _register(client)
    disabled = client.get(
        "/auth/student-verification/oauth/ntpu-entra/start",
        headers=_headers(session),
        follow_redirects=False,
    )
    assert disabled.status_code == 503
    assert "Microsoft" in disabled.json()["detail"]


def test_oauth_state_is_one_time_and_cancel_callback_is_safe(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    app = create_app(tmp_path)
    owner_client = TestClient(app)
    wrong_session_client = TestClient(app)
    owner_session = _register(owner_client)
    wrong_session = _login(wrong_session_client)
    start, params = _start_ntpu_entra(owner_client, _headers(owner_session))

    assert "ntpu-client-secret" not in start.headers["location"]
    assert params["code_challenge_method"] == ["S256"]
    assert start.headers["cache-control"] == "no-store"
    assert start.headers["referrer-policy"] == "no-referrer"
    state = params["state"][0]
    invalid = owner_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": "wrong-state", "error": "access_denied"},
        headers=_headers(owner_session),
        follow_redirects=False,
    )
    assert invalid.status_code == 400
    rejected_wrong_session = wrong_session_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": state, "error": "access_denied"},
        headers=_headers(wrong_session),
        follow_redirects=False,
    )
    assert rejected_wrong_session.status_code == 403
    assert "原本發起" in rejected_wrong_session.json()["detail"]

    cancelled = owner_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": state, "error": "access_denied"},
        headers=_headers(owner_session),
        follow_redirects=False,
    )
    assert cancelled.status_code == 303
    assert "student_verification=cancelled" in cancelled.headers["location"]
    assert cancelled.headers["cache-control"] == "no-store"
    assert cancelled.headers["referrer-policy"] == "no-referrer"
    replay = owner_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": state, "code": "replayed-code"},
        headers=_headers(owner_session),
        follow_redirects=False,
    )
    assert replay.status_code == 400

    _, malformed_params = _start_ntpu_entra(owner_client, _headers(owner_session))
    malformed_state = malformed_params["state"][0]
    with (
        patch("exchange_info.api.requests.post") as post,
        patch("exchange_info.api.requests.get") as get,
    ):
        malformed = owner_client.get(
            "/auth/student-verification/oauth/ntpu-entra/callback",
            params={"state": malformed_state, "code": "x"},
            headers=_headers(owner_session),
            follow_redirects=False,
        )
    assert malformed.status_code == 422
    assert malformed.headers["cache-control"] == "no-store"
    post.assert_not_called()
    get.assert_not_called()
    assert owner_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": malformed_state, "error": "access_denied"},
        headers=_headers(owner_session),
        follow_redirects=False,
    ).status_code == 400

    _, malformed_error_params = _start_ntpu_entra(
        owner_client,
        _headers(owner_session),
    )
    malformed_error_state = malformed_error_params["state"][0]
    malformed_error = owner_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": malformed_error_state, "error": "x" * 121},
        headers=_headers(owner_session),
        follow_redirects=False,
    )
    assert malformed_error.status_code == 422
    assert malformed_error.headers["cache-control"] == "no-store"
    assert owner_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": malformed_error_state, "error": "access_denied"},
        headers=_headers(owner_session),
        follow_redirects=False,
    ).status_code == 400


def test_student_oauth_callback_can_finish_on_another_app_instance(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    shared_store = LocalTransientAuthStore()
    start_client = TestClient(
        create_app(tmp_path, transient_auth_store=shared_store)
    )
    owner_session = _register(start_client, "cross-instance-owner@example.com")
    callback_client = TestClient(
        create_app(tmp_path, transient_auth_store=shared_store)
    )
    wrong_session = _register(callback_client, "cross-instance-wrong@example.com")
    _, params = _start_ntpu_entra(start_client, _headers(owner_session))
    state = params["state"][0]

    wrong_callback = callback_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": state, "error": "access_denied"},
        headers=_headers(wrong_session),
        follow_redirects=False,
    )
    assert wrong_callback.status_code == 403

    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "cross-instance-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {
                    "sub": "cross-instance-subject",
                    "email": "s410987354@ms.ntpu.edu.tw",
                }
            ),
        ),
    ):
        owner_callback = callback_client.get(
            "/auth/student-verification/oauth/ntpu-entra/callback",
            params={"state": state, "code": "authorization-code"},
            headers=_headers(owner_session),
            follow_redirects=False,
        )
    assert owner_callback.status_code == 303
    assert "student_verification=success" in owner_callback.headers["location"]
    assert callback_client.get(
        "/auth/me",
        headers=_headers(owner_session),
    ).json()["student_status_verified"] is True
    assert start_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": state, "error": "access_denied"},
        headers=_headers(owner_session),
        follow_redirects=False,
    ).status_code == 400


def test_student_oauth_start_rate_limit_preserves_last_valid_state(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    last_state = ""

    for _ in range(20):
        _, params = _start_ntpu_entra(client, _headers(session))
        last_state = params["state"][0]
    limited = client.get(
        "/auth/student-verification/oauth/ntpu-entra/start",
        headers=_headers(session),
        follow_redirects=False,
    )
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "600"

    cancelled = client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": last_state, "error": "access_denied"},
        headers=_headers(session),
        follow_redirects=False,
    )
    assert cancelled.status_code == 303


def test_student_oauth_active_state_capacity_is_bounded(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    monkeypatch.setattr(
        "exchange_info.api.STUDENT_VERIFICATION_OAUTH_MAX_ACTIVE_STATES",
        1,
    )
    app = create_app(tmp_path)
    first_client = TestClient(app)
    second_client = TestClient(app)
    first_session = _register(first_client, "provider-first@example.com")
    second_session = _register(second_client, "provider-second@example.com")

    _start_ntpu_entra(first_client, _headers(first_session))
    limited = second_client.get(
        "/auth/student-verification/oauth/ntpu-entra/start",
        headers=_headers(second_session),
        follow_redirects=False,
    )

    assert limited.status_code == 503
    assert limited.headers["retry-after"] == "60"


def test_entra_callback_verifies_only_state_owner_and_stores_no_school_email(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    app = create_app(tmp_path)
    owner_client = TestClient(app)
    wrong_session_client = TestClient(app)
    owner = _register(owner_client, "provider-owner@example.com")
    wrong_session = _login(wrong_session_client, "provider-owner@example.com")
    _, params = _start_ntpu_entra(owner_client, _headers(owner))
    state = params["state"][0]
    token_response = _JsonResponse({"access_token": "short-lived-access-token"})
    user_response = _JsonResponse(
        {"sub": "ntpu-student-subject", "email": "s410987354@ms.ntpu.edu.tw"}
    )
    with (
        patch("exchange_info.api.requests.post", return_value=token_response) as post,
        patch("exchange_info.api.requests.get", return_value=user_response) as get,
    ):
        rejected_wrong_session = wrong_session_client.get(
            "/auth/student-verification/oauth/ntpu-entra/callback",
            params={"state": state, "code": "authorization-code"},
            headers=_headers(wrong_session),
            follow_redirects=False,
        )
        assert rejected_wrong_session.status_code == 403
        post.assert_not_called()
        get.assert_not_called()

        callback = owner_client.get(
            "/auth/student-verification/oauth/ntpu-entra/callback",
            params={"state": state, "code": "authorization-code"},
            headers=_headers(owner),
            follow_redirects=False,
        )

    assert callback.status_code == 303
    assert "student_verification=success" in callback.headers["location"]
    assert callback.headers["cache-control"] == "no-store"
    assert callback.headers["referrer-policy"] == "no-referrer"
    assert post.call_count == 1
    assert get.call_count == 1
    assert post.call_args.kwargs["data"]["code_verifier"]
    assert get.call_args.kwargs["headers"] == {
        "Authorization": "Bearer short-lived-access-token"
    }
    owner_profile = owner_client.get("/auth/me", headers=_headers(owner)).json()
    assert owner_profile["student_status_verified"] is True
    assert owner_profile["verified_university"] == "國立臺北大學"
    assert owner_profile["student_verification_method"] == "microsoft_entra"
    assert owner_profile["school_email_verified"] is True
    replay = owner_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": state, "code": "replayed-code"},
        headers=_headers(owner),
        follow_redirects=False,
    )
    assert replay.status_code == 400
    persisted = (tmp_path / "processed" / "user_accounts.jsonl").read_text(
        encoding="utf-8"
    )
    assert "s410987354@ms.ntpu.edu.tw" not in persisted
    assert "short-lived-access-token" not in persisted
    assert "ntpu-student-subject" not in persisted


def test_wrong_domain_callback_fails_without_verifying_account(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    _, params = _start_ntpu_entra(client, _headers(session))
    with (
        patch(
            "exchange_info.api.requests.post",
            return_value=_JsonResponse({"access_token": "access-token"}),
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {"sub": "subject", "email": "s410987354@example.com"}
            ),
        ),
    ):
        callback = client.get(
            "/auth/student-verification/oauth/ntpu-entra/callback",
            params={"state": params["state"][0], "code": "authorization-code"},
            follow_redirects=False,
        )

    assert callback.status_code == 403
    profile = client.get("/auth/me", headers=_headers(session)).json()
    assert profile["student_status_verified"] is False


def test_account_deletion_revokes_outstanding_oauth_state(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    _, params = _start_ntpu_entra(client, _headers(session))
    assert client.delete("/auth/me", headers=_headers(session)).status_code == 204

    callback = client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": params["state"][0], "code": "authorization-code"},
        follow_redirects=False,
    )
    assert callback.status_code == 400


def test_revoked_session_cannot_finish_outstanding_oauth_state(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    app = create_app(tmp_path)
    owner_client = TestClient(app)
    replacement_client = TestClient(app)
    owner = _register(owner_client)
    _, params = _start_ntpu_entra(owner_client, _headers(owner))
    state = params["state"][0]

    logged_out = owner_client.post("/auth/logout", headers=_headers(owner))
    assert logged_out.status_code == 204
    with (
        patch("exchange_info.api.requests.post") as post,
        patch("exchange_info.api.requests.get") as get,
    ):
        revoked_callback = owner_client.get(
            "/auth/student-verification/oauth/ntpu-entra/callback",
            params={"state": state, "code": "authorization-code"},
            headers=_headers(owner),
            follow_redirects=False,
        )
    assert revoked_callback.status_code == 401
    post.assert_not_called()
    get.assert_not_called()

    replacement = _login(replacement_client)
    replacement_callback = replacement_client.get(
        "/auth/student-verification/oauth/ntpu-entra/callback",
        params={"state": state, "code": "authorization-code"},
        headers=_headers(replacement),
        follow_redirects=False,
    )
    assert replacement_callback.status_code == 403


def test_session_revoked_during_provider_exchange_cannot_commit_verification(
    tmp_path,
    monkeypatch,
) -> None:
    _configure_ntpu_entra(monkeypatch)
    app = create_app(tmp_path)
    owner_client = TestClient(app)
    replacement_client = TestClient(app)
    owner = _register(owner_client)
    _, params = _start_ntpu_entra(owner_client, _headers(owner))
    token_hash = hashlib.sha256(owner["access_token"].encode("utf-8")).hexdigest()

    def revoke_session_during_exchange(*_args, **_kwargs) -> _JsonResponse:
        app.state.account_repository.delete_session_by_token_hash(token_hash)
        return _JsonResponse({"access_token": "short-lived-access-token"})

    with (
        patch(
            "exchange_info.api.requests.post",
            side_effect=revoke_session_during_exchange,
        ),
        patch(
            "exchange_info.api.requests.get",
            return_value=_JsonResponse(
                {"sub": "subject", "email": "s410987354@ms.ntpu.edu.tw"}
            ),
        ),
    ):
        callback = owner_client.get(
            "/auth/student-verification/oauth/ntpu-entra/callback",
            params={
                "state": params["state"][0],
                "code": "authorization-code",
            },
            headers=_headers(owner),
            follow_redirects=False,
        )

    assert callback.status_code == 401
    replacement = _login(replacement_client)
    profile = replacement_client.get(
        "/auth/me",
        headers=_headers(replacement),
    ).json()
    assert profile["student_status_verified"] is False

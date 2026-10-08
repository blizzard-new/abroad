"""Synthetic API regressions for the privacy failures found during TKU acceptance."""
import hashlib
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.community_repositories import CommunityRepositoryError
from exchange_info.models import AnonymousIdentity
from exchange_info.repositories import AccountDeletionMutationResult, AccountDeletionMutationStatus
from exchange_info.storage import append_anonymous_identity, load_anonymous_identities, load_community_posts, load_user_accounts
from test_community_permissions import _account, _post_payload


@pytest.mark.parametrize('retry_header', [False, True])
@pytest.mark.parametrize('status,expected', [
    (AccountDeletionMutationStatus.COMMITTED, 204),
    (AccountDeletionMutationStatus.INTEGRITY_CONFLICT, 503),
])
def test_supabase_backend_always_uses_atomic_deletion_and_never_local_fallback(tmp_path, retry_header, status, expected):
    # Routing simulation only. No Supabase connection or production data.
    app = create_app(tmp_path)
    with TestClient(app) as client:
        _, headers, _ = _account(tmp_path, client, '合成原子路由測試', home_university='淡江大學')
        local = app.state.account_repository; calls = []
        def commit(request):
            calls.append(request)
            if status == AccountDeletionMutationStatus.COMMITTED:
                # Simulate the RPC's account removal so the local interaction
                # adapter observes the same post-commit condition.
                local.delete_account(request.account_id)
            return AccountDeletionMutationResult(status=status)
        def forbidden_fallback(*args, **kwargs):
            raise AssertionError('Atomic failure must not call legacy account deletion')
        app.state.account_repository = SimpleNamespace(backend_name='supabase',
            find_session_by_token_hash=local.find_session_by_token_hash,
            find_account_by_id=local.find_account_by_id, commit_account_deletion=commit,
            complete_account_deletion_storage=lambda *args: None, delete_account=forbidden_fallback)
        mutation_id = 'synthetic-supabase-routing-0001'
        supplied = {'X-Account-Deletion-Mutation-ID': mutation_id} if retry_header else {}
        response = client.delete('/auth/me', headers={**headers, **supplied})
        assert response.status_code == expected and len(calls) == 1
        assert len(calls[0].mutation_id) >= 16
        assert response.headers['X-Account-Deletion-Mutation-ID'] == calls[0].mutation_id
        if retry_header:
            assert calls[0].mutation_id == mutation_id


@pytest.mark.parametrize("retry_header", [False, True])
def test_deletion_deidentifies_all_linked_identities_and_preserves_other_account(tmp_path, retry_header):
    app = create_app(tmp_path)
    with TestClient(app) as client:
        owner, headers, first = _account(tmp_path, client, "合成淡江刪帳者", home_university="淡江大學")
        other, other_headers, _ = _account(tmp_path, client, "合成保留帳號", home_university="國立臺北大學")
        # The current identity endpoint reuses one identity. Seed another linked
        # legacy identity to exercise deletion of existing multi-identity data.
        legacy_token = "synthetic-legacy-community-token"
        legacy = append_anonymous_identity(AnonymousIdentity(account_id=owner.id,
            display_name="合成舊身分", access_token_hash=hashlib.sha256(legacy_token.encode()).hexdigest()), tmp_path)
        second = {"id": legacy.id, "access_token": legacy_token}
        assert second["id"] != first["id"]
        for identity in [first, second]:
            identity_headers = {**headers, "X-Anonymous-ID": identity["id"], "X-Anonymous-Token": identity["access_token"]}
            post = client.post("/community/posts", headers=identity_headers,
                json=_post_payload("公共留學板", identity_mode="real_name"))
            assert post.status_code == 201
        untouched = client.post("/community/posts", headers=other_headers,
            json=_post_payload("公共留學板", identity_mode="real_name")).json()["id"]
        deletion_headers = {**headers, **({"X-Account-Deletion-Mutation-ID": "synthetic-delete-mutation-0001"} if retry_header else {})}
        assert client.delete("/auth/me", headers=deletion_headers).status_code == 204
        assert client.get("/auth/me", headers=headers).status_code == 401
        assert client.get("/auth/me", headers=other_headers).status_code == 200
        public = client.get("/community/posts").json()
        assert {r["post"]["display_name"] for r in public if r["post"]["id"] != untouched} == {"已刪除帳號"}
        assert next(r["post"]["display_name"] for r in public if r["post"]["id"] == untouched) == other.display_name
        assert not any(r.account_id == owner.id for r in load_anonymous_identities(tmp_path))
        assert all(not r.author_id for r in load_community_posts(tmp_path) if r.id != untouched)


@pytest.mark.parametrize("retry_header", [False, True])
def test_failed_cleanup_retains_account_and_can_be_retried(tmp_path, monkeypatch, retry_header):
    app = create_app(tmp_path)
    with TestClient(app) as client:
        owner, headers, _ = _account(tmp_path, client, "合成清理重試者", home_university="淡江大學")
        assert client.post("/community/posts", headers=headers,
            json=_post_payload("公共留學板", identity_mode="real_name")).status_code == 201
        repository = app.state.community_repository
        original = repository.purge_private_identity
        def fail(request):
            raise CommunityRepositoryError("synthetic cleanup failure")
        monkeypatch.setattr(repository, "purge_private_identity", fail)
        deletion_headers = {**headers, **({"X-Account-Deletion-Mutation-ID": "synthetic-delete-mutation-0002"} if retry_header else {})}
        assert client.delete("/auth/me", headers=deletion_headers).status_code == 503
        assert any(r.id == owner.id for r in load_user_accounts(tmp_path))
        assert client.get("/auth/me", headers=headers).status_code == 200
        monkeypatch.setattr(repository, "purge_private_identity", original)
        assert client.delete("/auth/me", headers=deletion_headers).status_code == 204
        assert client.get("/community/posts").json()[0]["post"]["display_name"] == "已刪除帳號"


@pytest.mark.parametrize("body", [
    "合成護照號碼：A12345678", "合成護照號碼：Ａ１２３４５６７８",
    "合成身分證字號：A123456789", "Synthetic passport number: 123456789",
    "合成護照號碼 A12345678請不要公開",
])
@pytest.mark.parametrize("resource", ["post", "comment"])
def test_sensitive_id_is_rejected_before_storage_and_publication(tmp_path, body, resource):
    with TestClient(create_app(tmp_path)) as client:
        _, headers, _ = _account(tmp_path, client, "合成內容檢核者", home_university="淡江大學")
        if resource == "post":
            response = client.post("/community/posts", headers=headers, json=_post_payload("公共留學板", body=body))
        else:
            parent = client.post("/community/posts", headers=headers, json=_post_payload("公共留學板")).json()
            response = client.post(f"/community/posts/{parent['id']}/comments", headers=headers, json={"body": body})
        assert response.status_code == 422
        assert body not in str(client.get("/community/posts").json())
        assert body not in " ".join(r.body for r in load_community_posts(tmp_path))


def test_id_instructions_and_course_numbers_are_not_blocked(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        _, headers, _ = _account(tmp_path, client, "合成一般內容者", home_university="淡江大學")
        response = client.post("/community/posts", headers=headers,
            json=_post_payload("公共留學板", body="護照號碼請填官方表格，公開討論不要貼號碼。課程代碼 A12345678 僅為合成測試。"))
        assert response.status_code == 201
        assert response.json()["status"] == "approved"

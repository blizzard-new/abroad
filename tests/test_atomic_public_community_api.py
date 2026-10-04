import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import AccountSessionRecord, UserAccount, utc_now
from exchange_info.storage import (
    ensure_data_dirs,
    load_account_sessions,
    load_community_answers,
    load_community_post_comments,
    load_community_posts,
    load_community_publish_events,
    load_user_accounts,
    save_account_sessions,
    save_user_accounts,
)


def _account(
    data_dir: Path,
    client: TestClient,
    name: str,
    *,
    email: str | None = None,
) -> tuple[UserAccount, dict[str, str], dict]:
    account = UserAccount(
        email=email,
        display_name=name,
        email_verified=True,
    )
    access_token = f"account-token-{account.id}"
    save_user_accounts([*load_user_accounts(data_dir), account], data_dir)
    save_account_sessions(
        [
            *load_account_sessions(data_dir),
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            ),
        ],
        data_dir,
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    identity_response = client.post(
        "/auth/community-identity",
        headers=auth_headers,
    )
    assert identity_response.status_code == 201
    identity = identity_response.json()
    return account, {
        **auth_headers,
        "X-Anonymous-ID": identity["id"],
        "X-Anonymous-Token": identity["access_token"],
    }, identity


def _post_payload(*, title: str = "交換申請流程討論") -> dict:
    return {
        "board_id": "public-study-abroad",
        "post_type": "discussion",
        "topic": "application",
        "title": title,
        "body": "想和同學一起整理交換申請步驟與校內繳交文件。",
    }


def _mutation_headers(
    account_headers: dict[str, str],
    mutation_id: str | None = None,
) -> dict[str, str]:
    return {
        **account_headers,
        "X-Community-Mutation-ID": mutation_id or uuid4().hex,
    }


def test_same_public_mutation_replays_one_resource_and_one_rate_event(
    tmp_path: Path,
) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, account_headers, _ = _account(tmp_path, client, "可安全重試的學生")
    mutation_headers = _mutation_headers(account_headers)
    payload = _post_payload()

    created = client.post(
        "/community/posts",
        headers=mutation_headers,
        json=payload,
    )
    replayed = client.post(
        "/community/posts",
        headers=mutation_headers,
        json=dict(reversed(tuple(payload.items()))),
    )

    assert created.status_code == 201
    assert replayed.status_code == 201
    assert replayed.json() == created.json()
    assert len(load_community_posts(tmp_path)) == 1
    assert len(load_community_publish_events(tmp_path)) == 1


def test_same_public_mutation_id_rejects_a_different_payload(
    tmp_path: Path,
) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, account_headers, _ = _account(tmp_path, client, "衝突測試學生")
    mutation_headers = _mutation_headers(account_headers)

    created = client.post(
        "/community/posts",
        headers=mutation_headers,
        json=_post_payload(),
    )
    conflicted = client.post(
        "/community/posts",
        headers=mutation_headers,
        json=_post_payload(title="同一識別碼不能改成另一篇文章"),
    )

    assert created.status_code == 201
    assert conflicted.status_code == 409
    assert len(load_community_posts(tmp_path)) == 1
    assert len(load_community_publish_events(tmp_path)) == 1


def test_two_app_instances_atomically_limit_six_parallel_new_account_posts(
    tmp_path: Path,
) -> None:
    ensure_data_dirs(tmp_path)
    app_a = create_app(tmp_path)
    app_b = create_app(tmp_path)
    client_a = TestClient(app_a)
    client_b = TestClient(app_b)
    _, account_headers, _ = _account(tmp_path, client_a, "並行發布學生")
    barrier = Barrier(6)

    def publish(index: int):
        barrier.wait()
        client = client_a if index % 2 == 0 else client_b
        return client.post(
            "/community/posts",
            headers=_mutation_headers(account_headers),
            json=_post_payload(title=f"並行交換申請流程討論第 {index + 1} 篇"),
        )

    with ThreadPoolExecutor(max_workers=6) as executor:
        responses = list(executor.map(publish, range(6)))

    assert sorted(response.status_code for response in responses) == [
        201,
        201,
        201,
        201,
        201,
        429,
    ]
    limited = next(response for response in responses if response.status_code == 429)
    assert limited.headers["Retry-After"] == "600"
    assert len({
        response.json()["id"]
        for response in responses
        if response.status_code == 201
    }) == 5
    assert len(load_community_posts(tmp_path)) == 5
    assert len(load_community_publish_events(tmp_path)) == 5
    feed = client_a.get(
        "/community/posts",
        params={"school": "公共留學板"},
    )
    assert feed.status_code == 200
    assert len(feed.json()) == 5


def test_missing_answer_and_comment_parents_do_not_consume_publish_quota(
    tmp_path: Path,
) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    _, account_headers, _ = _account(tmp_path, client, "不存在 parent 測試學生")

    answer = client.post(
        "/community/questions/missing-question/answers",
        headers=_mutation_headers(account_headers),
        json={
            "body": "這則回答不應在問題不存在時建立或占用發布額度。",
            "accept_rules": True,
        },
    )
    comment = client.post(
        "/community/posts/missing-post/comments",
        headers=_mutation_headers(account_headers),
        json={"body": "這則留言不應建立。"},
    )

    assert answer.status_code == 404
    assert comment.status_code == 404
    assert load_community_answers(tmp_path) == []
    assert load_community_post_comments(tmp_path) == []
    assert load_community_publish_events(tmp_path) == []


def test_committed_suspension_blocks_publication_without_content_or_rate_event(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", "admin@example.com")
    ensure_data_dirs(tmp_path)
    app_a = create_app(tmp_path)
    app_b = create_app(tmp_path)
    client_a = TestClient(app_a)
    client_b = TestClient(app_b)
    _, admin_headers, _ = _account(
        tmp_path,
        client_a,
        "社群管理員",
        email="admin@example.com",
    )
    _, student_headers, student_identity = _account(
        tmp_path,
        client_a,
        "停權測試學生",
        email="student@example.com",
    )

    suspended = client_a.post(
        f"/admin/community/identities/{student_identity['id']}/suspend",
        headers=admin_headers,
        json={
            "suspended_until": (utc_now() + timedelta(days=7)).isoformat(),
            "reason": "測試跨 instance 的停權與發布順序。",
        },
    )
    published = client_b.post(
        "/community/posts",
        headers=_mutation_headers(student_headers),
        json=_post_payload(title="停權提交後不能發布"),
    )

    assert suspended.status_code == 200
    assert published.status_code == 403
    assert load_community_posts(tmp_path) == []
    assert load_community_publish_events(tmp_path) == []


def test_parallel_same_status_moderation_has_one_winner_and_one_audit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", "admin@example.com")
    ensure_data_dirs(tmp_path)
    app_a = create_app(tmp_path)
    app_b = create_app(tmp_path)
    client_a = TestClient(app_a)
    client_b = TestClient(app_b)
    _, admin_headers, _ = _account(
        tmp_path,
        client_a,
        "內容管理員",
        email="admin@example.com",
    )
    _, student_headers, _ = _account(tmp_path, client_a, "待審學生")
    pending = client_a.post(
        "/community/posts",
        headers=_mutation_headers(student_headers),
        json=_post_payload(title="付費代辦保證錄取"),
    )
    assert pending.status_code == 201
    assert pending.json()["status"] == "pending"
    resource_id = pending.json()["id"]
    barrier = Barrier(2)

    def approve(client: TestClient):
        barrier.wait()
        return client.patch(
            f"/admin/community/post/{resource_id}",
            headers=admin_headers,
            json={
                "status": "approved",
                "note": "已人工確認內容可公開。",
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(approve, (client_a, client_b)))

    assert sorted(response.status_code for response in responses) == [200, 409]
    committed = next(response for response in responses if response.status_code == 200)
    audits_response = client_a.get(
        "/admin/community/moderation-audits",
        headers=admin_headers,
    )
    assert audits_response.status_code == 200
    resource_audits = [
        audit
        for audit in audits_response.json()
        if audit["resource_type"] == "post"
        and audit["resource_id"] == resource_id
    ]
    assert resource_audits == [committed.json()]
    stored_posts = load_community_posts(tmp_path)
    assert len(stored_posts) == 1
    assert stored_posts[0].status.value == "approved"
    assert len(load_community_publish_events(tmp_path)) == 1

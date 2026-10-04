import hashlib
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.community_repositories import JsonlCommunityRepository
from exchange_info.models import (
    AccountSessionRecord, CommunityPost, CommunityPostComment, ModerationStatus,
    UserAccount, utc_now,
)
from exchange_info.storage import (
    ensure_data_dirs, save_user_accounts, save_account_sessions,
    append_community_post, append_community_post_comment, load_community_posts,
    load_community_post_comments,
)


@pytest.fixture
def client(tmp_path):
    ensure_data_dirs(tmp_path)
    return TestClient(create_app(tmp_path))


def post(tmp_path, *, id="post-a", date=None, **values):
    return append_community_post(CommunityPost(
        id=id, board_id="public-study-abroad", board_kind="public_study_abroad",
        school_name="公共留學板", author_id="private-author", display_name="匿名學生",
        title=values.pop("title", "日本交換申請經驗"), body="這是完整文章的內容，請參考官方申請公告。" * 15,
        created_at=date or utc_now() - timedelta(days=1), **values), tmp_path)


def comment(tmp_path, *, id="comment-a", post_id="post-a", date=None, **values):
    return append_community_post_comment(CommunityPostComment(
        id=id, post_id=post_id, author_id="private-commenter", display_name="匿名學生",
        body="可以再確認申請年度與官方公告。", created_at=date or utc_now() - timedelta(hours=1),
        **values), tmp_path)


def login(client, tmp_path, *, suspended=False, verified=True):
    account = UserAccount(display_name="測試學生", email_verified=verified,
                          created_at=utc_now() - timedelta(days=40),
                          community_suspended_until=utc_now() + timedelta(days=1) if suspended else None)
    save_user_accounts([account], tmp_path)
    token = "test-session-" + account.id
    save_account_sessions([AccountSessionRecord(account_id=account.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=utc_now() + timedelta(days=1))], tmp_path)
    # Exercise the same cookie transport as the Web application.
    client.cookies.set("exchange_guide_session", token)
    identity = client.post("/auth/community-identity")
    assert identity.status_code == 201
    return {"X-Anonymous-ID": identity.json()["id"],
            "X-Anonymous-Token": identity.json()["access_token"]}


def test_feed_is_summary_only_and_approved_counts(client, tmp_path):
    post(tmp_path, country="日本", academic_year="2027 秋季")
    post(tmp_path, id="hidden", status=ModerationStatus.HIDDEN)
    comment(tmp_path)
    comment(tmp_path, id="hidden-reply", status=ModerationStatus.HIDDEN)
    result = client.get("/community/feed").json()
    assert len(result["items"]) == 1
    row = result["items"][0]
    assert row["comment_count"] == 1 and len(row["excerpt"]) == 180
    assert not {"body", "comments", "author_id", "viewer_can_delete"} & row.keys()
    assert row["country"] == "日本"


def test_detail_comments_have_separate_visibility_and_stable_floors(client, tmp_path):
    post(tmp_path)
    post(tmp_path, id="hidden", status="hidden")
    for index in range(3):
        comment(tmp_path, id=f"c{index}", date=utc_now() - timedelta(minutes=10-index))
    detail = client.get("/community/posts/post-a").json()
    assert detail["comment_count"] == 3 and "body" in detail
    assert "author_id" not in detail and "comments" not in detail
    latest = client.get("/community/posts/post-a/comments?sort=latest&limit=2").json()
    assert [row["floor"] for row in latest["items"]] == [3, 2]
    assert all("author_id" not in row for row in latest["items"])
    tail = client.get("/community/posts/post-a/comments", params={
        "sort": "latest", "limit": 2, "cursor": latest["next_cursor"]}).json()
    assert [row["floor"] for row in tail["items"]] == [1]
    assert client.get("/community/posts/hidden").status_code == 404
    assert client.get("/community/posts/hidden/comments").status_code == 404


@pytest.mark.parametrize("sort", ["latest", "oldest"])
def test_cursor_ties_and_new_posts_do_not_duplicate_or_skip(client, tmp_path, sort):
    date = utc_now() - timedelta(days=1)
    for index in range(5):
        post(tmp_path, id=f"p{index}", date=date)
    first = client.get("/community/feed", params={"sort": sort, "limit": 2}).json()
    # Explicitly later than the snapshot, independent of Windows clock resolution.
    post(tmp_path, id="new-after-snapshot", date=utc_now() + timedelta(seconds=1))
    ids = [row["id"] for row in first["items"]]
    cursor = first["next_cursor"]
    while cursor:
        result = client.get("/community/feed", params={"sort": sort, "limit": 2, "cursor": cursor}).json()
        ids.extend(row["id"] for row in result["items"])
        cursor = result["next_cursor"]
    assert len(ids) == len(set(ids)) == 5
    assert ids == sorted(ids, reverse=sort == "latest")


def test_filters_saved_ids_and_unanswered_are_server_side(client, tmp_path):
    post(tmp_path, id="japan", country="日本", academic_year="2027")
    post(tmp_path, id="germany", country="德國", topic="housing")
    comment(tmp_path, post_id="japan")
    assert [row["id"] for row in client.get("/community/feed?q=德國&topic=housing").json()["items"]] == ["germany"]
    assert [row["id"] for row in client.get("/community/feed?ids=japan").json()["items"]] == ["japan"]
    assert [row["id"] for row in client.get("/community/feed?sort=unanswered").json()["items"]] == ["germany"]
    assert client.get("/community/feed?boards=language-school").json()["items"] == []


def test_cursor_rejects_tampering_filter_reuse_and_invalid_limits(client, tmp_path):
    post(tmp_path, id="a")
    post(tmp_path, id="b")
    cursor = client.get("/community/feed?limit=1").json()["next_cursor"]
    assert client.get("/community/feed", params={"cursor": cursor, "q": "日本"}).status_code == 422
    assert client.get("/community/feed", params={"cursor": cursor[:-1] + "x"}).status_code == 422
    assert client.get("/community/feed?cursor=broken").status_code == 422
    assert client.get("/community/feed?limit=51").status_code == 422
    assert client.get("/community/feed?sort=popular").status_code == 422


def test_cookie_identity_and_atomic_publication_retry(client, tmp_path):
    headers = login(client, tmp_path)
    payload = {"board_id": "public-study-abroad", "title": "交換申請問題整理", "body": "請問提名完成後要如何準備申請文件？"}
    headers["X-Community-Mutation-ID"] = "mutation-post-0123456789"
    first = client.post("/community/posts", headers=headers, json=payload)
    retry = client.post("/community/posts", headers=headers, json=payload)
    assert first.status_code == retry.status_code == 201
    assert first.json()["id"] == retry.json()["id"]
    assert len(load_community_posts(tmp_path)) == 1
    conflict = client.post("/community/posts", headers=headers, json={**payload, "body": "另一份不同內容的申請問題，需要重新送出。"})
    assert conflict.status_code == 409
    headers["X-Community-Mutation-ID"] = "mutation-reply-0123456789"
    path = f'/community/posts/{first.json()["id"]}/comments'
    reply = client.post(path, headers=headers, json={"body": "我建議先確認官方的文件清單。"})
    retry = client.post(path, headers=headers, json={"body": "我建議先確認官方的文件清單。"})
    assert reply.status_code == retry.status_code == 201
    assert reply.json()["id"] == retry.json()["id"]
    assert len(load_community_post_comments(tmp_path)) == 1


@pytest.mark.parametrize("suspended,verified", [(True, True), (False, False)])
def test_existing_suspension_and_email_gate_still_apply(client, tmp_path, suspended, verified):
    headers = login(client, tmp_path, suspended=suspended, verified=verified)
    result = client.post("/community/posts", headers=headers, json={
        "board_id": "public-study-abroad", "title": "交換申請問題整理", "body": "請問如何確認今年的交換申請文件清單？"})
    assert result.status_code == 403
    assert not load_community_posts(tmp_path)


def test_browsing_uses_injected_repository_instead_of_local_files(tmp_path):
    ensure_data_dirs(tmp_path)
    class Repository(JsonlCommunityRepository):
        def list_posts(self):
            return [CommunityPost(id="remote-post", school_name="公共留學板", author_id="hidden-id",
                                  display_name="匿名學生", title="遠端儲存的文章", body="讀取注入的 repository。",
                                  created_at=utc_now() - timedelta(days=1))]
        def list_comments(self):
            return []
    client = TestClient(create_app(tmp_path, community_repository=Repository(tmp_path)))
    assert client.get("/community/feed").json()["items"][0]["id"] == "remote-post"
    assert client.get("/community/posts/remote-post").status_code == 200
    assert load_community_posts(tmp_path) == []

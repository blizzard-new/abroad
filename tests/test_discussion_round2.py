"""Behavioral checks using isolated data, two app instances, and real account sessions."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.community_repositories import JsonlCommunityRepository
from exchange_info.models import AccountSessionRecord, CommunityPost, CommunityPostComment, UserAccount, utc_now
from exchange_info.storage import (ensure_data_dirs, save_user_accounts, load_user_accounts,
    save_account_sessions, load_account_sessions, append_community_post, append_community_post_comment,
    load_community_post_comments, load_community_moderation_audits)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", "moderator@example.com")
    ensure_data_dirs(tmp_path)
    return tmp_path, TestClient(create_app(tmp_path))


def actor(env, *, email=None, **values):
    path, client = env
    account = UserAccount(display_name="隔離測試學生", email=email, email_verified=True,
        created_at=utc_now() - timedelta(days=40), **values)
    save_user_accounts([*load_user_accounts(path), account], path)
    token = uuid4().hex
    save_account_sessions([*load_account_sessions(path), AccountSessionRecord(account_id=account.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now()+timedelta(days=1))], path)
    auth = {"Authorization": "Bearer " + token}
    identity = client.post("/auth/community-identity", headers=auth).json()
    return account, {**auth, "X-Anonymous-ID": identity["id"], "X-Anonymous-Token": identity["access_token"]}


def post(env, author="seed-author", **values):
    return append_community_post(CommunityPost(board_id="public-study-abroad", board_kind="public_study_abroad",
        school_name="公共留學板", author_id=author, display_name="匿名學生", title="交換申請經驗整理",
        body="請記得對照當年度官方申請公告。", **values), env[0])


def reply(env, post_id, headers, parent=None):
    return env[1].post(f"/community/posts/{post_id}/comments", headers=headers,
        json={"body": "這是實際申請經驗的補充說明。", "parent_id": parent})


def test_real_thread_parent_depth_and_cross_post_rejection(env):
    _, headers = actor(env)
    one, two = post(env), post(env)
    root = reply(env, one.id, headers).json()
    child = reply(env, one.id, headers, root["id"])
    assert child.status_code == 201 and child.json()["parent_id"] == root["id"]
    assert reply(env, two.id, headers, root["id"]).status_code == 404
    assert reply(env, one.id, headers, child.json()["id"]).status_code == 404
    roots = env[1].get(f"/community/posts/{one.id}/comments").json()
    assert len(roots["items"]) == 1 and roots["items"][0]["reply_count"] == 1
    children = env[1].get(f"/community/posts/{one.id}/comments", params={"parent_id": root["id"]}).json()
    assert children["items"][0]["parent_floor"] == 1
    assert roots["discussion_total"] == 2
    assert "author_id" not in children["items"][0]


def test_thread_pagination_cursor_cannot_cross_roots(env):
    one = post(env)
    roots = [append_community_post_comment(CommunityPostComment(post_id=one.id, author_id="private",
        display_name="匿名學生", body="此為原始回覆。"), env[0]) for _ in range(2)]
    for index in range(3):
        append_community_post_comment(CommunityPostComment(post_id=one.id, parent_id=roots[0].id,
            author_id="private", display_name="匿名學生", body=f"串內回覆 {index}"), env[0])
    url = f"/community/posts/{one.id}/comments"
    result = env[1].get(url, params={"parent_id": roots[0].id, "limit": 2}).json()
    assert [row["floor"] for row in result["items"]] == [1, 2]
    tail = env[1].get(url, params={"parent_id": roots[0].id, "cursor": result["next_cursor"]}).json()
    assert [row["floor"] for row in tail["items"]] == [3]
    assert env[1].get(url, params={"parent_id": roots[1].id, "cursor": result["next_cursor"]}).status_code == 422


def test_reaction_desired_state_is_unique_across_instances_and_accounts(env):
    account, headers = actor(env)
    other, other_headers = actor(env)
    one = post(env)
    clients = [env[1], TestClient(create_app(env[0]))]
    url = f"/community/post/{one.id}/reaction"
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda index: clients[index % 2].put(url, headers=headers,
            json={"reaction": "helpful"}), range(12)))
    assert all(row.status_code == 200 for row in results)
    assert results[-1].json()["counts"] == {"helpful": 1, "thanks": 0}
    assert clients[1].put(url, headers=other_headers, json={"reaction": "thanks"}).json()["counts"] == {"helpful": 1, "thanks": 1}
    assert env[1].put(url, headers=headers, json={"reaction": "thanks"}).json()["counts"] == {"helpful": 0, "thanks": 2}
    own = env[1].get(f"/community/posts/{one.id}", headers=headers).json()["reactions"]
    assert own["viewer_reaction"] == "thanks" and "account_id" not in str(own)
    guest = env[1].get(f"/community/posts/{one.id}").json()["reactions"]
    assert guest["viewer_reaction"] is None
    assert env[1].put(url, json={"reaction": "helpful"}).status_code == 401
    assert env[1].put(url, headers=headers, json={"reaction": "heart"}).status_code == 422
    assert env[1].put(url, headers=headers, json={"reaction": None}).json()["counts"] == {"helpful": 0, "thanks": 1}
    assert len(JsonlCommunityRepository(env[0]).list_reactions()) == 1


@pytest.mark.parametrize("values", [{"email_verified": False}, {"community_suspended_until": utc_now()+timedelta(days=1)}])
def test_unverified_or_suspended_account_cannot_react(env, values):
    account, headers = actor(env)
    save_user_accounts([account.model_copy(update=values)], env[0])
    one = post(env)
    assert env[1].put(f"/community/post/{one.id}/reaction", headers=headers, json={"reaction": "helpful"}).status_code == 403


def test_university_reaction_is_open_to_any_verified_email_account(env):
    _, headers = actor(env, student_status_verified=True, verified_university="國立臺北大學")
    from exchange_info.models import CommunityBoardKind
    one = post(env).model_copy(update={"board_id": "cgu", "board_kind": CommunityBoardKind.UNIVERSITY_EXCHANGE, "school_name": "長庚大學"})
    from exchange_info.storage import save_community_posts
    save_community_posts([one], env[0])
    assert env[1].put(f"/community/post/{one.id}/reaction", headers=headers, json={"reaction": "thanks"}).status_code == 200


def test_author_delete_retains_conversation_stub_and_cleans_reactions(env):
    _, owner = actor(env)
    _, stranger = actor(env)
    one = post(env, owner["X-Anonymous-ID"])
    root = reply(env, one.id, owner).json()
    child = reply(env, one.id, stranger, root["id"]).json()
    url = f"/community/posts/{one.id}/comments/{root['id']}"
    assert env[1].delete(url, headers=stranger).status_code == 403
    env[1].put(f"/community/comment/{root['id']}/reaction", headers=stranger, json={"reaction": "helpful"}).raise_for_status()
    key = {**owner, "X-Community-Mutation-ID": uuid4().hex}
    assert env[1].delete(url, headers=key).status_code == 200
    assert env[1].delete(url, headers=key).status_code == 200
    rows = env[1].get(f"/community/posts/{one.id}/comments").json()
    assert rows["items"][0]["deleted"] and rows["items"][0]["body"] == "此留言已刪除"
    assert rows["items"][0]["reply_count"] == 1 and not rows["items"][0]["viewer_can_delete"]
    assert env[1].get(f"/community/posts/{one.id}/comments", params={"parent_id": root["id"]}).json()["items"][0]["id"] == child["id"]
    assert not JsonlCommunityRepository(env[0]).list_reactions()
    assert env[1].delete(f"/community/posts/{one.id}", headers=owner).status_code == 200
    assert not load_community_post_comments(env[0])


def test_moderation_permissions_cas_audit_and_hidden_parent_visibility(env):
    _, admin = actor(env, email="moderator@example.com")
    _, student = actor(env)
    one = post(env)
    root = reply(env, one.id, student).json()
    child = reply(env, one.id, student, root["id"]).json()
    url = f"/admin/community/comment/{root['id']}"
    payload = {"status": "hidden", "expected_status": "approved", "note": "核對原文後隱藏此串。"}
    assert env[1].patch(url, json=payload).status_code == 401
    assert env[1].patch(url, headers=student, json=payload).status_code == 403
    key = {**admin, "X-Community-Mutation-ID": uuid4().hex}
    result = env[1].patch(url, headers=key, json=payload)
    assert result.status_code == 200 and result.json()["previous_status"] == "approved"
    assert env[1].patch(url, headers=key, json=payload).json() == result.json()
    assert env[1].patch(url, headers=admin, json=payload).status_code == 409
    assert len(load_community_moderation_audits(env[0])) == 1
    assert env[1].get(f"/community/posts/{one.id}/comments").json()["discussion_total"] == 0
    assert env[1].get(f"/community/posts/{one.id}/comments", params={"parent_id": root["id"]}).status_code == 404
    assert env[1].put(f"/community/comment/{child['id']}/reaction", headers=student, json={"reaction": "thanks"}).status_code == 404
    assert reply(env, one.id, student, root["id"]).status_code == 404
    # Author deletion must not undo a moderator's decision and reveal the children.
    assert env[1].delete(f"/community/posts/{one.id}/comments/{root['id']}", headers=student).status_code == 200
    assert env[1].get(f"/community/posts/{one.id}/comments").json()["discussion_total"] == 0


def test_suspension_retry_is_idempotent_and_blocks_replies_and_reactions(env):
    _, admin = actor(env, email="moderator@example.com")
    account, student = actor(env)
    one = post(env)
    url = f"/admin/community/identities/{student['X-Anonymous-ID']}/suspend"
    payload = {"suspended_until": (utc_now()+timedelta(days=7)).isoformat(), "reason": "重複違規，暫停發言。"}
    key = {**admin, "X-Community-Mutation-ID": uuid4().hex}
    first = env[1].post(url, headers=key, json=payload)
    assert first.status_code == 200
    assert env[1].post(url, headers=key, json=payload).json() == first.json()
    assert env[1].post(url, headers=key, json={**payload, "reason": "不同原因的另一筆操作"}).status_code == 409
    assert reply(env, one.id, student).status_code == 403
    assert env[1].put(f"/community/post/{one.id}/reaction", headers=student, json={"reaction": "thanks"}).status_code == 403


def test_risky_content_is_pending_until_admin_reviews_and_report_review_is_audited(env):
    _, admin = actor(env, email="moderator@example.com")
    _, student = actor(env)
    created = env[1].post("/community/posts", headers=student, json={"board_id": "public-study-abroad",
        "title": "交換付費代辦與保證錄取", "body": "請問這類宣稱保證錄取的代辦方案可信嗎？"})
    assert created.status_code == 201 and created.json()["status"] == "pending"
    pid = created.json()["id"]
    assert env[1].get(f"/community/posts/{pid}").status_code == 404
    assert reply(env, pid, student).status_code == 404
    env[1].patch(f"/admin/community/post/{pid}", headers=admin,
        json={"status": "approved", "expected_status": "pending", "note": "已確認為提問與提醒，非招攬。"}).raise_for_status()
    _, reporter = actor(env)
    key = {**reporter, "X-Community-Mutation-ID": uuid4().hex}
    reported = env[1].post("/community/reports", headers=key,
        json={"resource_type": "post", "resource_id": pid, "reason": "需要管理員進一步確認資訊。"})
    assert reported.status_code == 202
    assert env[1].post("/community/reports", headers=key,
        json={"resource_type": "post", "resource_id": pid, "reason": "需要管理員進一步確認資訊。"}).json()["id"] == reported.json()["id"]
    queue = env[1].get("/admin/community/reports", headers=admin).json()
    assert len(queue) == 1 and "reporter_id" not in queue[0] and queue[0]["content"]["title"]
    resolved = env[1].patch(f"/admin/community/reports/{reported.json()['id']}", headers=admin,
        json={"status": "resolved", "note": "已查核並完成處理。"})
    assert resolved.status_code == 200 and resolved.json()["resource_type"] == "report"
    assert env[1].get("/admin/community/reports", headers=admin).json() == []


def test_account_deletion_removes_reactions(env):
    _, headers = actor(env)
    one = post(env)
    env[1].put(f"/community/post/{one.id}/reaction", headers=headers, json={"reaction": "helpful"}).raise_for_status()
    result = env[1].delete("/auth/me", headers={**headers, "X-Account-Deletion-Mutation-ID": uuid4().hex})
    assert result.status_code == 204
    assert not JsonlCommunityRepository(env[0]).list_reactions()
    assert not (env[0]/"processed"/"community_reactions.jsonl").read_text(encoding="utf-8").strip()


def test_reaction_storage_failure_preserves_counts_and_delete_rolls_back(env, monkeypatch):
    import exchange_info.community_repositories as repositories
    _, owner = actor(env)
    one = post(env, owner["X-Anonymous-ID"])
    url = f"/community/post/{one.id}/reaction"
    env[1].put(url, headers=owner, json={"reaction": "helpful"}).raise_for_status()
    real_write = repositories.write_jsonl
    failures = [True]
    def fail_once(path, rows):
        if path.name == "community_reactions.jsonl" and failures:
            failures.pop()
            raise OSError("isolated test: unavailable storage")
        return real_write(path, rows)
    monkeypatch.setattr(repositories, "write_jsonl", fail_once)
    assert env[1].put(url, headers=owner, json={"reaction": "thanks"}).status_code == 503
    assert env[1].get(f"/community/posts/{one.id}").json()["reactions"]["counts"] == {"helpful": 1, "thanks": 0}
    failures.append(True)
    assert env[1].delete(f"/community/posts/{one.id}", headers=owner).status_code == 503
    assert env[1].get(f"/community/posts/{one.id}").status_code == 200
    assert env[1].get(f"/community/posts/{one.id}").json()["reactions"]["counts"]["helpful"] == 1


def test_floor_numbers_survive_deleted_comments(env):
    _, owner = actor(env)
    one = post(env)
    first = reply(env, one.id, owner).json()
    second = reply(env, one.id, owner).json()
    env[1].delete(f"/community/posts/{one.id}/comments/{first['id']}", headers=owner).raise_for_status()
    rows = env[1].get(f"/community/posts/{one.id}/comments").json()["items"]
    assert [(row["id"], row["floor"]) for row in rows] == [(second["id"], 2)]


def test_bookmarks_persist_across_devices_and_are_private_and_idempotent(env):
    _, owner = actor(env)
    _, other = actor(env)
    one = post(env)
    url = f"/community/posts/{one.id}/bookmark"
    assert env[1].put(url, json={"saved": True}).status_code == 401
    assert env[1].put(url, headers=owner, json={"saved": True}).status_code == 200
    second_device = TestClient(create_app(env[0]))
    assert second_device.get("/community/bookmarks", headers=owner).json() == {"ids": [one.id]}
    assert second_device.get("/community/bookmarks", headers=other).json() == {"ids": []}
    assert second_device.put(url, headers=owner, json={"saved": True}).status_code == 200
    assert second_device.get("/community/bookmarks", headers=owner).json() == {"ids": [one.id]}
    assert second_device.put(url, headers=owner, json={"saved": False}).status_code == 200
    assert env[1].get("/community/bookmarks", headers=owner).json() == {"ids": []}


def test_bookmarks_have_limit_and_cleanup_with_post_and_account_deletion(env):
    _, owner = actor(env)
    repository = JsonlCommunityRepository(env[0])
    aid = owner["X-Anonymous-ID"]
    for _ in range(100):
        one = post(env, aid)
        assert repository.set_bookmark(load_user_accounts(env[0])[0].id, one.id, True)["status"] == "committed"
    excess = post(env, aid)
    assert env[1].put(f"/community/posts/{excess.id}/bookmark", headers=owner, json={"saved": True}).status_code == 409
    env[1].delete(f"/community/posts/{one.id}", headers=owner).raise_for_status()
    assert len(env[1].get("/community/bookmarks", headers=owner).json()["ids"]) == 99
    assert env[1].delete("/auth/me", headers={**owner,"X-Account-Deletion-Mutation-ID":uuid4().hex}).status_code == 204
    assert not (env[0]/"processed"/"community_bookmarks.jsonl").read_text(encoding="utf-8").strip()

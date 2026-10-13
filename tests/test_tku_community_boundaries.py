"""Synthetic regressions for the explicitly selected community membership policy."""
from cgu_catalogue_fixture import fixed_cgu_catalogue
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.storage import load_community_posts, load_private_conversations, load_private_messages
from test_community_permissions import _account, _post_payload
from test_social_community_api import _partner


@pytest.mark.parametrize("board", ["cgu", "ntpu", "ntu", "tku"])
def test_school_board_reads_and_writes_require_verified_email_across_all_views(tmp_path, board):
    client = TestClient(create_app(tmp_path))
    _, member, _ = _account(tmp_path, client, "跨校會員", home_university="國立臺北大學")
    _, pending, _ = _account(tmp_path, client, "未驗證會員", email_verified=False)
    post = client.post("/community/posts", headers=member, json=_post_payload(None, board_id=board))
    assert post.status_code == 201
    post_id = post.json()["id"]
    reads = [
        ("/community/posts", {"board_id": board}),
        ("/community/feed", {"boards": board}),
        (f"/community/posts/{post_id}", {}),
        (f"/community/posts/{post_id}/comments", {}),
    ]
    for headers, status in [({}, 401), (pending, 403), (member, 200)]:
        for url, params in reads:
            response = client.get(url, params=params, headers=headers)
            assert response.status_code == status, (url, response.text)
            assert "private, no-store" in response.headers.get("cache-control", "") or status != 200
        access = next(row for row in client.get("/community/boards", headers=headers).json() if row["id"] == board)
        assert access["can_read"] == (status == 200)
        assert access["can_post"] == (status == 200)
        created = client.post("/community/posts", headers=headers, json=_post_payload(None, board_id=board))
        assert created.status_code == (201 if status == 200 else status)
        comment = client.post(f"/community/posts/{post_id}/comments", headers=headers, json={"body":"合成跨校留言。"})
        assert comment.status_code == (201 if status == 200 else status)
    for headers in [{}, pending]:
        assert post_id not in {r["id"] for r in client.get("/community/feed", headers=headers).json()["items"]}
        assert post_id not in {r["post"]["id"] for r in client.get("/community/posts", headers=headers).json()}
        # Arbitrary ID filters cannot expose school-board content through the global feed.
        assert client.get("/community/feed", params={"ids":post_id}, headers=headers).json()["items"] == []
    public = client.post("/community/posts", headers=member, json=_post_payload("公共留學板"))
    assert public.status_code == 201
    for headers in [{}, pending]:
        assert client.get(f"/community/posts/{public.json()['id']}", headers=headers).status_code == 200
    assert client.post("/community/posts", headers=pending, json=_post_payload("公共留學板")).status_code == 403


def test_self_declared_school_never_enables_verified_student_bylines(tmp_path):
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "自填母校", home_university="淡江大學", verified_department="自填系所")
    options = client.get("/auth/community-identity-options", headers=headers).json()["options"]
    for mode in ["verified_school", "verified_department"]:
        assert next(row for row in options if row["mode"] == mode)["enabled"] is False
        assert client.post("/community/posts", headers=headers,
                           json=_post_payload("淡江大學", identity_mode=mode)).status_code == 403
    assert load_community_posts(tmp_path) == []
    assert client.post("/community/posts", headers=headers, json=_post_payload("長庚大學")).status_code == 201


@pytest.mark.parametrize("board,status", [("university:",422),("university:   ",422),("university:cgu",201)])
def test_empty_legacy_board_rejected_and_valid_alias_preserved(tmp_path, board, status):
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "合成legacy會員")
    response = client.post("/community/posts", headers=headers, json=_post_payload(None, board_id=board))
    assert response.status_code == status
    if status == 422:
        assert load_community_posts(tmp_path) == []
    else:
        assert response.json()["board_id"] == "cgu" and response.json()["school_name"] == "長庚大學"


@pytest.mark.parametrize("alias", ["CGU", "Ｃ．Ｇ．Ｕ"])
@pytest.mark.parametrize("mode", ["verified_school", "verified_department"])
def test_verified_alias_byline_preview_matches_publication(tmp_path, alias, mode):
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "合成alias學生", verified_university=alias, verified_department="資訊工程學系")
    option = next(row for row in client.get("/auth/community-identity-options", headers=headers).json()["options"] if row["mode"] == mode)
    expected = "長庚大學學生" if mode == "verified_school" else "長庚大學 資訊工程學系學生"
    assert option["enabled"] is True and option["label"] == expected
    response = client.post("/community/posts", headers=headers, json=_post_payload("淡江大學", identity_mode=mode))
    assert response.status_code == 201 and response.json()["display_name"] == expected
    assert load_community_posts(tmp_path)[0].display_name == expected


@pytest.mark.parametrize("value", ["   ","unsupported-school"])
def test_empty_or_unknown_verified_school_never_defaults_to_cgu_byline(tmp_path, value):
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "合成缺母校學生", verified_university=value)
    options = client.get("/auth/community-identity-options", headers=headers).json()["options"]
    assert next(row for row in options if row["mode"] == "verified_school")["enabled"] is False
    response = client.post("/community/posts", headers=headers, json=_post_payload("淡江大學", identity_mode="verified_school"))
    assert response.status_code == 403 and load_community_posts(tmp_path) == []


@pytest.mark.parametrize("mode", ["anonymous", "real_name", "verified_school", "verified_department"])
def test_byline_preview_matches_stored_post_and_comment(tmp_path, mode):
    client = TestClient(create_app(tmp_path))
    _, headers, _ = _account(tmp_path, client, "合成署名", verified_university="長庚大學", verified_department="資訊工程學系")
    option = next(row for row in client.get("/auth/community-identity-options", headers=headers).json()["options"] if row["mode"] == mode)
    post = client.post("/community/posts", headers=headers, json=_post_payload("國立臺北大學", identity_mode=mode))
    assert post.status_code == 201
    assert post.json()["display_name"] == option["label"]
    assert load_community_posts(tmp_path)[0].display_name == option["label"]
    comment = client.post(f"/community/posts/{post.json()['id']}/comments", headers=headers, json={"body":"合成署名一致性留言。", "identity_mode":mode})
    assert comment.status_code == 201
    assert comment.json()["display_name"] == option["label"]


def test_private_mutations_replay_without_duplicate_resources_and_reject_foreign_actor(tmp_path, monkeypatch):
    partner = _partner()
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner]))
    client = TestClient(create_app(tmp_path))
    _, sender, _ = _account(tmp_path, client, "合成寄件者")
    _, recipient, recipient_identity = _account(tmp_path, client, "合成收件者")
    _, outsider, _ = _account(tmp_path, client, "合成外人")
    mutation = {**sender, "X-Community-Mutation-ID":"synthetic-invite-retry-001"}
    payload = {"school_name":partner.school_name,"recipient_id":recipient_identity["id"],"initial_message":"合成邀請，請接受後再傳訊。"}
    with ThreadPoolExecutor(max_workers=3) as pool:
        responses = list(pool.map(lambda _: client.post("/community/conversations", headers=mutation, json=payload), range(3)))
    assert all(r.status_code == 201 for r in responses)
    assert all(r.json() == responses[0].json() for r in responses)
    assert responses[0].headers["X-Community-Mutation-ID"] == mutation["X-Community-Mutation-ID"]
    assert len(load_private_conversations(tmp_path)) == len(load_private_messages(tmp_path)) == 1
    assert client.post("/community/conversations", headers=mutation, json={**payload,"initial_message":"已更改的合成邀請。"}).status_code == 409
    assert client.post("/community/conversations", headers={**outsider,"X-Community-Mutation-ID":mutation["X-Community-Mutation-ID"]}, json=payload).status_code == 409
    assert client.post("/community/conversations", headers={**mutation,"X-Anonymous-Token":"invalid-token"}, json=payload).status_code == 401
    assert client.post("/community/conversations", headers={**outsider,"X-Anonymous-ID":sender["X-Anonymous-ID"],"X-Anonymous-Token":sender["X-Anonymous-Token"]}, json=payload).status_code == 403
    conversation_id = responses[0].json()["id"]
    assert client.get(f"/community/conversations/{conversation_id}/messages", headers=outsider).status_code == 403
    accepted = client.post(f"/community/conversations/{conversation_id}/accept", headers={**recipient,"X-Community-Mutation-ID":"synthetic-accept-retry-001"})
    replay = client.post(f"/community/conversations/{conversation_id}/accept", headers={**recipient,"X-Community-Mutation-ID":"synthetic-accept-retry-001"})
    assert accepted.status_code == replay.status_code == 200 and accepted.json() == replay.json()
    message_headers = {**sender,"X-Community-Mutation-ID":"synthetic-message-retry-001"}
    message = client.post(f"/community/conversations/{conversation_id}/messages", headers=message_headers, json={"body":"合成後續訊息。"})
    replay = client.post(f"/community/conversations/{conversation_id}/messages", headers=message_headers, json={"body":"合成後續訊息。"})
    assert message.status_code == replay.status_code == 201 and message.json() == replay.json()
    assert len(load_private_messages(tmp_path)) == 2
    block_headers = {**recipient,"X-Community-Mutation-ID":"synthetic-block-retry-001"}
    block = client.post("/community/blocks", headers=block_headers, json={"target_id":sender["X-Anonymous-ID"]})
    assert block.status_code == 201
    assert client.post("/community/blocks", headers=block_headers, json={"target_id":sender["X-Anonymous-ID"]}).json() == block.json()
    assert client.post(f"/community/conversations/{conversation_id}/messages", headers=sender, json={"body":"封鎖後不應新增。"}).status_code == 403
    assert len(load_private_messages(tmp_path)) == 2


def test_failed_initial_message_rolls_back_invitation_and_retry_is_safe(tmp_path, monkeypatch):
    import exchange_info.community_repositories as repositories
    partner = _partner()
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner]))
    client = TestClient(create_app(tmp_path))
    _, sender, _ = _account(tmp_path, client, "合成原子寄件者")
    _, _, recipient = _account(tmp_path, client, "合成原子收件者")
    original = repositories.save_private_messages
    calls = 0
    def fail_once(rows, data_dir):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("synthetic message write failure")
        return original(rows, data_dir)
    monkeypatch.setattr(repositories, "save_private_messages", fail_once)
    headers = {**sender,"X-Community-Mutation-ID":"synthetic-rollback-retry-001"}
    payload = {"school_name":partner.school_name,"recipient_id":recipient["id"],"initial_message":"合成故障重試邀請。"}
    assert client.post("/community/conversations", headers=headers, json=payload).status_code == 503
    assert load_private_conversations(tmp_path) == load_private_messages(tmp_path) == []
    assert client.post("/community/conversations", headers=headers, json=payload).status_code == 201
    assert len(load_private_conversations(tmp_path)) == len(load_private_messages(tmp_path)) == 1


def test_tku_runtime_keeps_all_base_checks_and_mandatory_cleanup(monkeypatch):
    from scripts import validate_tku_community_runtime as probe
    calls = []
    monkeypatch.setattr(probe.runtime, "validate_runtime", lambda context: calls.append(("base",context)) or {"status":"passed","base_checks":True})
    monkeypatch.setattr(probe, "validate_policy", lambda context: calls.append(("policy",context)) or {"tested":True})
    def existing_main(argv):
        assert argv == []  # no --keep or user-selected Docker project
        result = probe.runtime.validate_runtime("isolated-context")
        assert result["status"] == "passed" and result["base_checks"] is True
        assert result["tku_selected_community_policy"] == {"tested":True}
        calls.append(("cleanup", "isolated-context"))
        return 0
    monkeypatch.setattr(probe.runtime, "main", existing_main)
    assert probe.main() == 0
    assert calls == [("base","isolated-context"),("policy","isolated-context"),("cleanup","isolated-context")]

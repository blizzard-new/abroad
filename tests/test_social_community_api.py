from cgu_catalogue_fixture import fixed_cgu_catalogue
import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import AccountSessionRecord, PartnerUniversity, UserAccount, utc_now
from exchange_info.storage import (
    ensure_data_dirs,
    load_account_sessions,
    load_anonymous_identities,
    load_private_conversations,
    load_private_messages,
    load_user_accounts,
    save_account_sessions,
    save_anonymous_identities,
    save_user_accounts,
)


def _partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        country="紐西蘭",
        school_name="林肯大學 Lincoln University",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _identity(data_dir, client: TestClient, name: str) -> tuple[dict, dict[str, str]]:
    account = UserAccount(
        display_name=name,
        email_verified=True,
        student_status_verified=True,
        verified_university="長庚大學",
    )
    access_token = f"account-token-{account.id}"
    session_record = AccountSessionRecord(
        account_id=account.id,
        token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
        expires_at=utc_now() + timedelta(days=1),
    )
    save_user_accounts([*load_user_accounts(data_dir), account], data_dir)
    save_account_sessions(
        [*load_account_sessions(data_dir), session_record], data_dir
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    session = client.post("/auth/community-identity", headers=auth_headers).json()
    return session, {
        **auth_headers,
        "X-Anonymous-ID": session["id"],
        "X-Anonymous-Token": session["access_token"],
    }


def test_posts_chat_and_invitation_only_private_messages(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr(
        'exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner])
    )
    client = TestClient(create_app(tmp_path))
    first, first_headers = _identity(tmp_path, client, "匿名海風")
    second, second_headers = _identity(tmp_path, client, "匿名書桌")

    post_response = client.post(
        "/community/posts",
        headers=first_headers,
        json={
            "board_id": "public-study-abroad",
            "post_type": "discussion",
            "title": "想問林肯的住宿選擇",
            "body": "比較在意通勤時間與是否容易認識其他交換學生。",
        },
    )
    assert post_response.status_code == 201
    post = post_response.json()

    comment_response = client.post(
        f"/community/posts/{post['id']}/comments",
        headers=second_headers,
        json={
            "body": "我也想知道宿舍申請通常何時開放。",
            "identity_mode": "real_name",
        },
    )
    assert comment_response.status_code == 201
    threads = client.get(
        "/community/posts", params={"school": "公共留學板"}
    ).json()
    assert threads[0]["post"]["comment_count"] == 1
    assert threads[0]["comments"][0]["display_name"] == "匿名書桌"

    chat_response = client.post(
        "/community/chat",
        headers=first_headers,
        json={"school_name": partner.school_name, "body": "有人也在準備明年春季嗎？"},
    )
    assert chat_response.status_code == 201
    assert client.get(
        "/community/chat", params={"school": partner.school_name}
    ).json()[0]["author_id"] == first["id"]

    conversation_response = client.post(
        "/community/conversations",
        headers=first_headers,
        json={
            "school_name": partner.school_name,
            "recipient_id": second["id"],
            "initial_message": "想私下請教你提到的宿舍時間，可以嗎？",
        },
    )
    assert conversation_response.status_code == 201
    conversation = conversation_response.json()
    assert conversation["status"] == "pending"

    blocked_before_accept = client.post(
        f"/community/conversations/{conversation['id']}/messages",
        headers=first_headers,
        json={"body": "這則還不能送出"},
    )
    assert blocked_before_accept.status_code == 409

    accepted = client.post(
        f"/community/conversations/{conversation['id']}/accept",
        headers=second_headers,
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    reply = client.post(
        f"/community/conversations/{conversation['id']}/messages",
        headers=second_headers,
        json={"body": "可以，我把實際申請順序整理給你。"},
    )
    assert reply.status_code == 201
    messages = client.get(
        f"/community/conversations/{conversation['id']}/messages",
        headers=first_headers,
    ).json()
    assert len(messages) == 2

    report = client.post(
        "/community/reports",
        headers=second_headers,
        json={
            "resource_type": "post",
            "resource_id": post["id"],
            "reason": "內容可能含有過時資訊，請協助確認。",
        },
    )
    assert report.status_code == 202

    block = client.post(
        "/community/blocks",
        headers=second_headers,
        json={"target_id": first["id"]},
    )
    assert block.status_code == 201
    assert client.get(
        f"/community/conversations/{conversation['id']}/messages",
        headers=second_headers,
    ).json() == []


def test_private_conversation_retry_replays_generated_resources(
    tmp_path, monkeypatch
) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr(
        'exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner])
    )
    client = TestClient(create_app(tmp_path))
    _, sender_headers = _identity(tmp_path, client, "匿名海風")
    recipient, _ = _identity(tmp_path, client, "匿名書桌")
    mutation_headers = {
        **sender_headers,
        "X-Community-Mutation-ID": "private-api-retry-0001",
    }
    payload = {
        "school_name": partner.school_name,
        "recipient_id": recipient["id"],
        "initial_message": "相同請求重送時，只能建立一組私訊資料。",
    }

    first = client.post(
        "/community/conversations", headers=mutation_headers, json=payload
    )
    save_anonymous_identities(
        [
            row
            for row in load_anonymous_identities(tmp_path)
            if row.id != recipient["id"]
        ],
        tmp_path,
    )
    replay = client.post(
        "/community/conversations", headers=mutation_headers, json=payload
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    assert len(load_private_conversations(tmp_path)) == 1
    assert len(load_private_messages(tmp_path)) == 1


def test_social_post_requires_a_valid_anonymous_identity(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr(
        'exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner])
    )
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/community/posts",
        json={
            "school_name": partner.school_name,
            "post_type": "question",
            "title": "沒有匿名身分的貼文",
            "body": "這一篇應該要被 API 擋下來，不能直接公開。",
        },
    )

    assert response.status_code == 401

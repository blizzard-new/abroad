from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import PartnerUniversity
from exchange_info.storage import ensure_data_dirs


def _partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        country="紐西蘭",
        school_name="林肯大學 Lincoln University",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _identity(client: TestClient, name: str) -> tuple[dict, dict[str, str]]:
    session = client.post(
        "/community/identities", json={"display_name": name}
    ).json()
    return session, {
        "X-Anonymous-ID": session["id"],
        "X-Anonymous-Token": session["access_token"],
    }


def test_posts_chat_and_invitation_only_private_messages(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr(
        "exchange_info.api.fetch_partner_universities", lambda: [partner]
    )
    client = TestClient(create_app(tmp_path))
    first, first_headers = _identity(client, "匿名海風")
    second, second_headers = _identity(client, "匿名書桌")

    post_response = client.post(
        "/community/posts",
        headers=first_headers,
        json={
            "school_name": partner.school_name,
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
        json={"body": "我也想知道宿舍申請通常何時開放。"},
    )
    assert comment_response.status_code == 201
    threads = client.get(
        "/community/posts", params={"school": partner.school_name}
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


def test_social_post_requires_a_valid_anonymous_identity(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr(
        "exchange_info.api.fetch_partner_universities", lambda: [partner]
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

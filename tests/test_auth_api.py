from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from exchange_info.api import create_app
from exchange_info.models import PartnerUniversity
from exchange_info.storage import ensure_data_dirs
from exchange_info.student_verification import StudentCardVerification


def _card_image(color: tuple[int, int, int]) -> bytes:
    stream = BytesIO()
    Image.new("RGB", (900, 560), color).save(stream, format="JPEG")
    return stream.getvalue()


def _student_verification_token(client: TestClient) -> str:
    result = StudentCardVerification(
        school_name="長庚大學",
        checks=("正反面不同", "校名可辨識", "學生證文字可辨識"),
    )
    with patch("exchange_info.api.verify_student_cards", return_value=result):
        response = client.post(
            "/auth/student-verification",
            data={"school_name": "長庚大學", "consent": "true"},
            files={
                "front": ("front.jpg", _card_image((230, 238, 246)), "image/jpeg"),
                "back": ("back.jpg", _card_image((210, 222, 232)), "image/jpeg"),
            },
        )
    assert response.status_code == 201
    assert response.json()["images_retained"] is False
    return response.json()["verification_token"]


def _register(client: TestClient) -> dict:
    verification_token = _student_verification_token(client)
    response = client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "correct-horse-2026",
            "display_name": "準備交換的小林",
            "student_verification_token": verification_token,
            "accept_terms": True,
        },
    )
    assert response.status_code == 201
    return response.json()


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


def test_student_verification_token_is_required_and_single_use(tmp_path) -> None:
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

    verification_token = _student_verification_token(client)
    first = client.post(
        "/auth/register",
        json={
            "email": "verified@example.com",
            "password": "correct-horse-2026",
            "display_name": "已驗證學生",
            "student_verification_token": verification_token,
            "accept_terms": True,
        },
    )
    assert first.status_code == 201
    assert first.json()["profile"]["student_status_verified"] is True

    reused = client.post(
        "/auth/register",
        json={
            "email": "reused@example.com",
            "password": "correct-horse-2026",
            "display_name": "重複驗證學生",
            "student_verification_token": verification_token,
            "accept_terms": True,
        },
    )
    assert reused.status_code == 403


def test_global_community_posts_can_be_filtered_by_topic(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = PartnerUniversity(
        program_type="交換學生",
        country="日本",
        school_name="範例大學 Example University",
        source_url="https://www.cgu.edu.tw/oia-ch/",
    )
    monkeypatch.setattr(
        "exchange_info.api.fetch_partner_universities", lambda: [partner]
    )
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    auth_headers = {"Authorization": f"Bearer {session['access_token']}"}
    identity = client.post("/auth/community-identity", headers=auth_headers).json()
    community_headers = {
        "X-Anonymous-ID": identity["id"],
        "X-Anonymous-Token": identity["access_token"],
    }

    response = client.post(
        "/community/posts",
        headers=community_headers,
        json={
            "school_name": partner.school_name,
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
    assert client.get("/community/posts", params={"topic": "visa"}).json() == []


def test_public_and_cgu_boards_can_be_posted_and_filtered(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    client = TestClient(create_app(tmp_path))
    session = _register(client)
    auth_headers = {"Authorization": f"Bearer {session['access_token']}"}
    identity = client.post("/auth/community-identity", headers=auth_headers).json()
    community_headers = {
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

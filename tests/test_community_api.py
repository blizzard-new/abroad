import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import (
    AccountSessionRecord,
    ModerationStatus,
    PartnerUniversity,
    UserAccount,
    utc_now,
)
from exchange_info.storage import (
    ensure_data_dirs,
    load_account_sessions,
    load_community_answers,
    load_community_questions,
    load_experience_submissions,
    load_user_accounts,
    save_account_sessions,
    save_community_answers,
    save_community_questions,
    save_user_accounts,
)


def _partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        country="紐西蘭",
        school_name="林肯大學 Lincoln University",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _community_headers(data_dir, client: TestClient) -> dict[str, str]:
    account = UserAccount(
        display_name="已驗證學生",
        student_status_verified=True,
        verified_university="長庚大學",
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
    identity = client.post("/auth/community-identity", headers=auth_headers).json()
    return {
        **auth_headers,
        "X-Anonymous-ID": identity["id"],
        "X-Anonymous-Token": identity["access_token"],
    }


def test_question_answer_and_experience_submission_are_moderated(
    tmp_path, monkeypatch
) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    client = TestClient(create_app(tmp_path))
    headers = _community_headers(tmp_path, client)

    question_response = client.post(
        "/community/questions",
        headers=headers,
        json={
            "school_name": partner.school_name,
            "home_university": "長庚大學",
            "topic": "housing",
            "title": "宿舍通常什麼時候申請？",
            "body": "想知道交換生宿舍是否容易額滿，以及收到提名後多久要申請。",
            "display_name": "匿名學生",
            "accept_rules": True,
        },
    )
    assert question_response.status_code == 202
    question = question_response.json()
    assert question["status"] == "pending"
    assert client.get(
        "/community/questions", params={"school": partner.school_name}
    ).json() == []

    questions = load_community_questions(tmp_path)
    questions[0] = questions[0].model_copy(
        update={"status": ModerationStatus.APPROVED}
    )
    save_community_questions(questions, tmp_path)

    answer_response = client.post(
        f"/community/questions/{question['id']}/answers",
        headers=headers,
        json={
            "body": "我交換的那一年收到入學信後就立刻申請，建議不要等到截止日前。",
            "display_name": "匿名學長姐",
            "exchange_year": "2025",
            "accept_rules": True,
        },
    )
    assert answer_response.status_code == 202
    answers = load_community_answers(tmp_path)
    answers[0] = answers[0].model_copy(
        update={"status": ModerationStatus.APPROVED}
    )
    save_community_answers(answers, tmp_path)

    threads = client.get(
        "/community/questions", params={"school": partner.school_name}
    ).json()
    assert threads[0]["question"]["answer_count"] == 1
    assert threads[0]["answers"][0]["exchange_year"] == "2025"

    submission_response = client.post(
        "/experience-submissions",
        headers=headers,
        json={
            "school_name": partner.school_name,
            "home_university": "長庚大學",
            "title": "林肯大學交換生活整理",
            "summary": "校園距離市區有一段距離，住宿和公車班次最好在出發前一起確認。",
            "exchange_year": "2025",
            "themes": ["housing", "transport"],
            "source_url": "https://example.com/my-exchange-story",
            "display_name": "匿名投稿者",
            "consent_to_publish": True,
        },
    )
    assert submission_response.status_code == 202
    assert load_experience_submissions(tmp_path)[0].status == ModerationStatus.PENDING


def test_community_submission_rejects_contact_details(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    client = TestClient(create_app(tmp_path))
    headers = _community_headers(tmp_path, client)

    response = client.post(
        "/community/questions",
        headers=headers,
        json={
            "school_name": partner.school_name,
            "topic": "life",
            "title": "想詢問當地生活",
            "body": "可以寄信到 student@example.com 告訴我生活情況嗎？",
            "display_name": "匿名學生",
            "accept_rules": True,
        },
    )
    assert response.status_code == 422
    assert "個人聯絡資料" in response.json()["detail"]

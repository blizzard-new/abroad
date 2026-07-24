from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import ModerationStatus, PartnerUniversity
from exchange_info.storage import (
    ensure_data_dirs,
    load_community_answers,
    load_community_questions,
    load_experience_submissions,
    save_community_answers,
    save_community_questions,
)


def _partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        country="紐西蘭",
        school_name="林肯大學 Lincoln University",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def test_question_answer_and_experience_submission_are_moderated(
    tmp_path, monkeypatch
) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    client = TestClient(create_app(tmp_path))

    question_response = client.post(
        "/community/questions",
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

    response = client.post(
        "/community/questions",
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

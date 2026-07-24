from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from exchange_info.advisor import answer_question, build_advisor_plan
from exchange_info.api import create_app
from exchange_info.document_checker import check_document
from exchange_info.models import (
    AdvisorProfile,
    PageCategory,
    PartnerStudentSummary,
    PartnerUniversity,
    ProcessedPage,
    SourceReference,
    StudentDashboard,
    StudentInfoItem,
)


SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/123"


def _dashboard() -> StudentDashboard:
    deadline = date.today() + timedelta(days=21)
    return StudentDashboard(
        school_name="長庚大學",
        application_periods=[
            StudentInfoItem(
                title="交換學生校內申請",
                details=[f"截止日期：{deadline.year}年{deadline.month}月{deadline.day}日"],
                source=SourceReference(title="交換公告", source_url=SOURCE_URL),
            )
        ],
        eligibility=[
            StudentInfoItem(
                title="校內申請資格",
                details=["學業平均成績須達 70 分以上。"],
                source=SourceReference(title="交換公告", source_url=SOURCE_URL),
            )
        ],
        language_requirements=[
            StudentInfoItem(
                title="語言門檻",
                details=["TOEIC 700 分以上。"],
                source=SourceReference(title="交換公告", source_url=SOURCE_URL),
            )
        ],
        required_documents=[
            StudentInfoItem(
                title="申請文件",
                details=["申請表、成績單、讀書計畫與語言證明。"],
                source=SourceReference(title="交換公告", source_url=SOURCE_URL),
            )
        ],
        partner_universities=[
            PartnerUniversity(
                program_type="交換學生",
                country="日本",
                school_name="測試日本大學",
                colleges="全校",
                degree_levels="大學部／研究所",
                eligibility="TOEIC 700",
                application_deadline=f"{deadline.month}月{deadline.day}日",
                source_url=SOURCE_URL,
                image_url="http://testserver/static/assets/schools/test.jpg",
                student_summary_zh=PartnerStudentSummary(
                    eligibility_points=["TOEIC 700 分以上"],
                ),
            ),
            PartnerUniversity(
                program_type="交換學生",
                country="法國",
                school_name="測試法國大學",
                colleges="醫學院",
                degree_levels="大學部",
                eligibility="IELTS 7.0",
                source_url="https://example.edu/france",
            ),
        ],
    )


def _page() -> ProcessedPage:
    return ProcessedPage(
        title="交換學生申請公告",
        source_url=SOURCE_URL,
        text="申請文件包含申請表、成績單、讀書計畫與語言證明。",
        summary="交換申請文件與截止日期整理。",
        category=PageCategory.EXCHANGE_APPLICATION,
        content_hash="advisor-test",
    )


def test_advisor_returns_grounded_match_tasks_and_no_fake_admission_probability(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    plan = build_advisor_plan(
        AdvisorProfile(
            college="工學院",
            degree_level="大學部",
            academic_score=82,
            language_test="toeic",
            language_score=850,
            preferred_country="日本",
            target_term="2027-fall",
            question="交換申請需要哪些文件？",
        ),
        _dashboard(),
        [_page()],
        [],
        [],
    )

    assert plan.recommendations[0].school_name == "測試日本大學"
    assert plan.recommendations[0].match_score > plan.recommendations[1].match_score
    assert plan.answer and plan.answer.sources[0].source_url == SOURCE_URL
    assert any(task.due_date for task in plan.tasks)
    assert "admission_probability" not in plan.model_dump()
    assert "不是錄取機率" in plan.disclaimer


def test_grounded_answer_refuses_when_no_relevant_public_source(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    answer = answer_question("火星寵物檢疫與火箭燃料規定", _dashboard(), [], [], [])

    assert answer.evidence_status == "not_found"
    assert answer.sources == []
    assert "資料不足" in answer.answer


def test_initial_application_document_question_does_not_mix_incoming_or_post_acceptance_files(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    application_page = _page().model_copy(
        update={
            "text": "申請學生須填寫申請表並繳送紙本文件至國際處，完整清單依當期公告。",
            "summary": "校內交換申請入口。",
        }
    )
    incoming_page = _page().model_copy(
        update={
            "title": "簽證資訊",
            "source_url": "https://www.cgu.edu.tw/oia-ch/incoming-visa",
            "text": "交換學生在台就學須檢附護照、健康檢查、財力證明與入學許可。",
            "summary": "來台交換學生簽證文件。",
        }
    )

    answer = answer_question(
        "交換申請需要準備哪些文件？",
        StudentDashboard(school_name="長庚大學"),
        [application_page, incoming_page],
        [],
        [],
    )

    assert answer.evidence_status == "limited"
    assert "尚未列出完整" in answer.answer
    assert "護照" not in "".join(answer.key_points)
    assert all("incoming-visa" not in source.source_url for source in answer.sources)


def test_document_checker_reads_docx_and_flags_missing_study_plan_sections(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    document = Document()
    document.add_heading("交換讀書計畫", level=1)
    document.add_paragraph("我希望到日本交換，申請動機是拓展國際視野。" * 12)
    output = BytesIO()
    document.save(output)

    result = check_document(
        file_name="讀書計畫.docx",
        content=output.getvalue(),
        document_type="auto",
        require_signature=True,
    )

    assert result.document_type == "study_plan"
    assert result.character_count > 100
    assert any(issue.title == "未找到修課規劃" for issue in result.issues)
    assert any(issue.code == "signature_missing" for issue in result.issues)
    assert result.ai_enhanced is False
    assert "不會保存原檔" in result.privacy_note


def test_advisor_and_document_check_api(tmp_path, monkeypatch) -> None:
    dashboard = _dashboard()
    monkeypatch.setattr(
        "exchange_info.api.build_student_dashboard",
        lambda pages, info, **kwargs: dashboard,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(create_app(tmp_path / "data"))

    plan = client.post(
        "/advisor/plan",
        json={
            "college": "工學院",
            "degree_level": "大學部",
            "academic_score": 82,
            "language_test": "toeic",
            "language_score": 850,
            "preferred_country": "日本",
        },
    )
    assert plan.status_code == 200
    assert plan.json()["recommendations"][0]["school_name"] == "測試日本大學"

    checked = client.post(
        "/document-check",
        files={"file": ("履歷.txt", "教育背景：長庚大學。\n技能：英文。\n經歷：交換社團。" * 8, "text/plain")},
        data={"document_type": "resume", "require_signature": "false"},
    )
    assert checked.status_code == 200
    assert checked.json()["file_name"] == "履歷.txt"
    assert checked.json()["document_type"] == "resume"

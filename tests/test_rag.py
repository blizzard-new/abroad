from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.document_rewriter import rewrite_document
from exchange_info.models import (
    AccountSessionRecord,
    DocumentRewriteRequest,
    PageCategory,
    ProcessedPage,
    SourceReference,
    StudentDashboard,
    StudentInfoItem,
    UserAccount,
    utc_now,
)
from exchange_info.rag import (
    build_document_chunks,
    build_rag_index,
    search_document_chunks,
    split_document_text,
)
from exchange_info.storage import (
    save_account_sessions,
    save_processed_pages,
    save_user_accounts,
)
from exchange_info.structured_sources import (
    build_structured_source_index,
    structure_source,
)


SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/rag-test"


def _authenticated_client(data_dir) -> TestClient:
    account = UserAccount(display_name="RAG 文件檢查測試學生")
    token = "rag-document-check-token"
    save_user_accounts([account], data_dir)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        data_dir,
    )
    client = TestClient(create_app(data_dir))
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def _page(text: str = "申請文件包含申請表、成績單、讀書計畫與語言證明。") -> ProcessedPage:
    return ProcessedPage(
        title="交換學生申請公告",
        source_url=SOURCE_URL,
        published_at="2026-07-01",
        summary="交換申請資料整理。",
        text=text,
        category=PageCategory.EXCHANGE_APPLICATION,
        crawled_at=datetime(2026, 7, 19, 3, 0, tzinfo=timezone.utc),
        content_hash="rag-source-v1",
    )


def test_document_chunking_keeps_source_metadata_and_bounded_passages() -> None:
    text = "\n\n".join(f"第 {index} 段。" + "申請資格與文件說明。" * 30 for index in range(8))
    page = _page(text)

    passages = split_document_text(text, max_chars=240, overlap_chars=30)
    chunks = build_document_chunks([page])

    assert len(passages) > 2
    assert all(len(passage) <= 240 for passage in passages)
    assert chunks
    assert all(chunk.source_url == SOURCE_URL for chunk in chunks)
    assert all(chunk.last_checked == page.crawled_at for chunk in chunks)


def test_document_index_excludes_incoming_student_visa_content() -> None:
    incoming = _page(
        "交換學生在台就學期間須申請居留簽證，並附長庚大學核發的入學通知。"
    ).model_copy(update={"title": "簽證資訊"})

    assert build_document_chunks([incoming]) == []


def test_local_rag_index_falls_back_to_keyword_search_without_api_key(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    data_dir = tmp_path / "data"
    status = build_rag_index([_page()], data_dir, use_embeddings=True)

    hits = search_document_chunks("交換需要哪些申請文件？", data_dir)

    assert status.chunk_count >= 1
    assert status.embedded_count == 0
    assert hits
    assert hits[0].match_type == "keyword"
    assert hits[0].chunk.source_url == SOURCE_URL


def test_semantic_search_can_find_related_meaning_without_same_keywords(tmp_path, monkeypatch) -> None:
    page = _page("本計畫接受校內能力證明，不要求另外檢附英語檢定成績。")
    monkeypatch.setattr("exchange_info.rag.ai_enabled", lambda: True)
    monkeypatch.setattr("exchange_info.rag.ai_embedding_model", lambda: "test-embedding")

    def fake_embed(texts: list[str]) -> list[list[float]]:
        return [
            [1.0, 0.0] if "能力證明" in text or "外語很弱" in text else [0.0, 1.0]
            for text in texts
        ]

    monkeypatch.setattr("exchange_info.rag.embed_texts", fake_embed)
    build_rag_index([page], tmp_path / "data", sync_supabase=False)

    hits = search_document_chunks("外語很弱有哪些選擇？", tmp_path / "data")

    assert hits
    assert hits[0].match_type in {"semantic", "hybrid"}
    assert "不要求另外檢附" in hits[0].chunk.text


def test_structured_source_extraction_keeps_official_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.structured_sources.structured_response",
        lambda **kwargs: {
            "program_type": ["交換學生"],
            "academic_year": ["116"],
            "semester": ["春季"],
            "application_start": "2026-11-01",
            "application_end": "2026-12-20",
            "application_period": ["2026-11-01 至 2026-12-20"],
            "eligibility": ["學業平均 70 分以上"],
            "language_requirements": ["依合作校規定"],
            "required_documents": ["申請表", "成績單"],
            "scholarship_info": [],
            "needs_review": False,
        },
    )

    record = structure_source(_page(), use_ai=True)

    assert record.extraction_method == "ai"
    assert record.application_end == "2026-12-20"
    assert record.source_url == SOURCE_URL
    assert record.last_checked == _page().crawled_at
    assert record.needs_review is False


def test_document_rewrite_is_labeled_and_does_not_require_file_storage(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.document_rewriter.structured_response",
        lambda **kwargs: {
            "draft": "I plan to study artificial intelligence courses at the partner university.",
            "changes": ["翻譯為正式英文"],
            "warnings": ["課程名稱仍需由學生核對"],
        },
    )

    result = rewrite_document(
        DocumentRewriteRequest(
            text="我計畫在合作學校修習人工智慧相關課程，並將學習成果帶回原系所分享。",
            action="translate_en",
            school_context="合作學校",
        )
    )

    assert result.ai_enhanced is True
    assert result.action == "translate_en"
    assert "AI 建議稿" in result.disclaimer
    assert result.warnings == ["課程名稱仍需由學生核對"]


def test_rules_advisor_works_while_ai_compatibility_endpoints_stay_paused(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-enable-ai")
    ai_requests: list[str] = []

    def unexpected_ai_post(url: str, **kwargs):
        ai_requests.append(url)
        raise AssertionError("paused runtime must not make an external AI request")

    monkeypatch.setattr("exchange_info.ai_gateway.requests.post", unexpected_ai_post)
    page = _page()
    data_dir = tmp_path / "data"
    save_processed_pages([page], data_dir)
    build_rag_index([page], data_dir, use_embeddings=False)
    build_structured_source_index([page], data_dir, use_ai=False)
    dashboard = StudentDashboard(
        school_name="長庚大學",
        required_documents=[
            StudentInfoItem(
                title="交換申請文件",
                details=["申請表、成績單、讀書計畫與語言證明。"],
                source=SourceReference(title="交換公告", source_url=SOURCE_URL),
            )
        ],
    )
    monkeypatch.setattr(
        "exchange_info.api.build_student_dashboard",
        lambda pages, info, **kwargs: dashboard,
    )
    client = _authenticated_client(data_dir)

    answer = client.post("/advisor/ask", json={"question": "交換需要哪些申請文件？"})
    paused_chat = client.post("/ai/chat", json={"question": "交換需要哪些申請文件？"})
    status = client.get("/ai/status")
    review = client.post(
        "/ai/review-document",
        files={"file": ("讀書計畫.txt", "申請動機與學習計畫。" * 30, "text/plain")},
        data={"document_type": "study_plan", "consent": "true"},
    )
    rewrite = client.post(
        "/ai/rewrite-document",
        json={"text": "這是我自行撰寫且需要調整語氣的交換申請內容。" * 2, "action": "formalize"},
    )

    assert answer.status_code == 200
    assert answer.json()["sources"][0]["published_at"] == "2026-07-01"
    assert answer.json()["sources"][0]["last_checked"].startswith("2026-07-19")
    assert status.json()["rag_index"]["source_count"] == 1
    assert status.json()["structured_source_count"] == 1
    assert status.json()["ai_enabled"] is False
    assert status.json()["runtime_state"] == "paused"
    assert status.json()["provider"] is None
    assert status.json()["model"] is None
    assert "AI API 與本地 AI 目前暫緩" in status.json()["paused_reason"]
    assert paused_chat.status_code == 503
    assert review.status_code == 503
    assert "AI 深度檢查目前暫緩" in review.json()["detail"]
    assert rewrite.status_code == 503
    assert "AI API 與本地 AI 目前暫緩" in rewrite.json()["detail"]
    assert ai_requests == []

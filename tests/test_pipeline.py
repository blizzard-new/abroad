from datetime import datetime, timezone

from exchange_info.cleaner import process_page
from exchange_info.crawler import is_attachment_url
from exchange_info.extractor import build_exchange_info
from exchange_info.models import Attachment, PageCategory, RawPage


def test_cleaner_removes_repeated_boilerplate_and_classifies() -> None:
    raw = RawPage(
        title="出國補助說明",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=1",
        raw_text=(
            "出國補助說明\n"
            "出國補助說明\n"
            "申請資格：限長庚大學在學學生。\n"
            "電話: 03-2118800\n"
            "© Copyright © 2024 長庚大學｜國際事務處\n"
        ),
        attachments=[
            Attachment(url="https://www.cgu.edu.tw/files/sample.pdf", filename="sample.pdf")
        ],
        crawled_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
        content_hash="abc123",
    )

    page = process_page(raw)

    assert page.category == PageCategory.SCHOLARSHIP
    assert page.text.count("出國補助說明") == 1
    assert "電話" not in page.text
    assert page.summary
    assert page.attachments[0].filename == "sample.pdf"


def test_build_exchange_info_extracts_rule_based_fields() -> None:
    raw = RawPage(
        title="115學年度交換學生申請公告",
        source_url="https://www.cgu.edu.tw/oia-ch/Subject/Detail/2",
        raw_text=(
            "115學年度交換學生申請公告\n"
            "申請期間：即日起至6月10日止。\n"
            "申請資格：長庚大學在學學生。\n"
            "語言要求：TOEFL 或 IELTS 成績。\n"
            "申請文件：歷年成績單、自傳、讀書計畫。\n"
        ),
        crawled_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
        content_hash="def456",
    )
    page = process_page(raw)

    info = build_exchange_info([page])

    assert info.school_name == "長庚大學"
    assert "交換學生" in info.program_type
    assert "115學年度" in info.academic_year
    assert any("6月10日" in item for item in info.application_period)
    assert any("TOEFL" in item for item in info.language_requirement)
    assert any("成績單" in item for item in info.required_documents)
    assert info.source_urls == [raw.source_url]


def test_crawler_treats_cgu_serverfile_get_as_attachment() -> None:
    assert is_attachment_url("https://www.cgu.edu.tw/regulation/ServerFile/Get/abc123")
    assert is_attachment_url("https://www.cgu.edu.tw/files/example.pdf")

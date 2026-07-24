from datetime import datetime, timezone

from fastapi.testclient import TestClient

from exchange_info.api import _attach_school_images, create_app
from exchange_info.models import (
    Attachment,
    ExchangeInfo,
    PageCategory,
    PartnerUniversity,
    ProcessedPage,
    RuleExplanation,
    SourceReference,
    StudentDashboard,
)
from exchange_info.storage import ensure_data_dirs, save_exchange_info, save_processed_pages


def test_api_reads_processed_data_without_full_text(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    page = ProcessedPage(
        title="交換學生申請公告",
        source_url="https://www.cgu.edu.tw/oia-ch/Subject/Detail/3",
        published_at="2026/06/01",
        text="申請期間：即日起至6月10日止。\n申請文件：成績單、自傳。",
        summary="申請期間：即日起至6月10日止。",
        category=PageCategory.DEADLINE,
        attachments=[
            Attachment(
                url="https://www.cgu.edu.tw/files/application.pdf",
                filename="application.pdf",
                local_path=str(data_dir / "raw_files" / "application.pdf"),
            )
        ],
        crawled_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
        content_hash="hash123",
    )
    save_processed_pages([page], data_dir)
    save_exchange_info(
        ExchangeInfo(
            school_name="長庚大學",
            program_type=["交換學生"],
            source_urls=[page.source_url],
            last_checked=page.crawled_at,
        ),
        data_dir,
    )
    monkeypatch.setattr(
        "exchange_info.api.build_student_dashboard",
        lambda pages, info, **kwargs: StudentDashboard(
            school_name="長庚大學",
            sources=[],
            document_explanations=[
                RuleExplanation(
                    title="領航者補助作業要點",
                    summary="整理後的學生版摘要。",
                    key_points=["學業平均 70 分以上"],
                    source=SourceReference(
                        title="補助公告",
                        source_url="https://www.cgu.edu.tw/oia-ch/Subject/Detail/4",
                    ),
                    document_url="https://www.cgu.edu.tw/files/rules.pdf",
                    document_type="補助要點",
                )
            ],
        ),
    )

    client = TestClient(create_app(data_dir))

    frontend = client.get("/")
    assert frontend.status_code == 200
    assert frontend.headers["cache-control"] == "no-store"
    assert "台灣大學生交換指南" in frontend.text

    assert client.get("/health").json()["pages"] == 1
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [])
    universities = client.get("/universities").json()
    assert universities[0]["school_name"] == "長庚大學"
    assert universities[0]["supported"] is True
    assert client.get("/exchange-info", params={"school": "長庚大學"}).json()[
        "program_type"
    ] == ["交換學生"]

    sources = client.get("/sources").json()
    assert sources[0]["summary"] == "申請期間：即日起至6月10日止。"
    assert "text" not in sources[0]

    assert client.get("/deadlines").json()[0]["snippets"]
    documents = client.get("/documents").json()
    assert documents[0]["attachment"]["filename"] == "application.pdf"
    assert documents[1]["summary"] == "整理後的學生版摘要。"
    assert documents[1]["key_points"] == ["學業平均 70 分以上"]
    assert client.get("/search", params={"q": "成績單"}).json()[0]["title"] == "交換學生申請公告"
    assert client.get("/student-dashboard", params={"school": "長庚大學"}).json()[
        "school_name"
    ] == "長庚大學"


def test_dashboard_attaches_verified_official_school_image() -> None:
    dashboard = StudentDashboard(
        partner_universities=[
            PartnerUniversity(
                program_type="交換學生",
                country="紐西蘭",
                school_name="林肯大學 Lincoln University",
                source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
            )
        ]
    )

    enriched = _attach_school_images(dashboard, base_url="http://app.test/")
    school = enriched.partner_universities[0]

    assert school.image_status == "verified"
    assert school.image_url and school.image_url.startswith(
        "http://app.test/static/assets/schools/"
    )
    assert school.image_page_url and school.image_page_url.startswith("https://")

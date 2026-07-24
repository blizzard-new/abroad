from datetime import datetime, timezone

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_workflow_collector import (
    LINCOLN_INCOMING_URL,
    collect_application_workflow,
    clean_official_page_title,
    discover_official_partner_pages,
    is_official_partner_url,
    normalize_official_url,
)
from exchange_info.models import (
    ApplicationStep,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from exchange_info.storage import (
    ensure_data_dirs,
    load_application_workflows,
    replace_application_workflow,
)


def _partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生 / 自費研修",
        country="紐西蘭",
        school_name="林肯大學 Lincoln University",
        website="https://www.lincoln.ac.nz/",
        quota="2",
        eligibility="IELTS 6.0 overall, no band below 5.5.",
        application_deadline="Semester 1: 30 September; Semester 2: 30 March",
        application_info="由本校提名後，Lincoln 直接通知申請作業。",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _workflow(
    school_name: str = "林肯大學 Lincoln University",
    title: str = "確認資格",
) -> UniversityApplicationWorkflow:
    return UniversityApplicationWorkflow(
        school_name=school_name,
        country="紐西蘭",
        steps=[
            ApplicationStep(
                order=1,
                phase="校內準備",
                title=title,
                responsible_party="學生",
                summary="核對資格。",
            )
        ],
        last_checked=datetime(2026, 7, 11, tzinfo=timezone.utc),
        coverage_status="official_verified",
    )


def test_official_url_filter_rejects_third_party_hosts() -> None:
    official = "https://www.lincoln.ac.nz/"
    assert is_official_partner_url(LINCOLN_INCOMING_URL, official)
    assert not is_official_partner_url("https://example.com/lincoln-exchange", official)


def test_official_url_filter_distinguishes_thai_academic_domains() -> None:
    official = "https://www.tbs.tu.ac.th/"

    assert is_official_partner_url(
        "https://bba.tbs.tu.ac.th/incoming-exchange",
        official,
    )
    assert not is_official_partner_url(
        "https://som.ait.ac.th/exchange-program",
        official,
    )


def test_official_url_filter_distinguishes_polish_academic_domains() -> None:
    official = "https://www.sggw.edu.pl/en/"

    assert is_official_partner_url(
        "https://welcome.sggw.edu.pl/incoming-exchange",
        official,
    )
    assert not is_official_partner_url(
        "https://en.uw.edu.pl/education/exchange-and-guest-students/",
        official,
    )


def test_discovery_rejects_unrelated_program_pages_on_official_domain(
    monkeypatch,
) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="泰國",
        school_name="泰國法政大學商學院 Thammasat Business School",
        website="https://www.tbs.tu.ac.th/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            ("Master in Finance", "https://mif.tbs.tu.ac.th/"),
            (
                "Center for International Affairs",
                "https://bba.tbs.tu.ac.th/incoming-exchange/",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert any("incoming-exchange" in url for _, url in pages)
    assert all("mif.tbs.tu.ac.th" not in url for _, url in pages)


def test_discovery_requires_exchange_signal_not_generic_application(
    monkeypatch,
) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="德國",
        school_name="德國開姆尼茨工業大學 Chemnitz University of Technology",
        website="https://www.tu-chemnitz.de/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "Application | Advanced Manufacturing",
                "https://www.tu-chemnitz.de/mb/am/studiengang/application.php",
            ),
            (
                "Incoming exchange application",
                "https://www.tu-chemnitz.de/international/incoming/exchange.php",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert any("incoming/exchange" in url for _, url in pages)
    assert all("advanced" not in title.lower() for title, _ in pages)


def test_normalize_official_url_removes_tracking_query() -> None:
    assert normalize_official_url(
        "https://student.example.edu/exchange?semester=fall&gclid=abc&utm_source=test"
    ) == "https://student.example.edu/exchange?semester=fall"


def test_clean_official_page_title_removes_concatenated_results() -> None:
    assert clean_official_page_title(
        "Accommodation | Incoming | TU Chemnitz...English Department | Other Result"
    ) == "Accommodation | Incoming | TU Chemnitz..."


def test_discovery_rejects_outgoing_and_placeholder_paths(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="波蘭",
        school_name="波蘭華沙理工大學Warsaw University of Technology",
        website="https://www.pw.edu.pl/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "Incoming exchange application",
                "https://www.pw.edu.pl/international/incoming-exchange",
            ),
            (
                "Outgoing students",
                "https://www.pw.edu.pl/international/outgoing-students",
            ),
            (
                "International students",
                "https://www.pw.edu.pl/asdfasdf/international-students",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert any("incoming-exchange" in url for _, url in pages)
    assert all("outgoing" not in url and "asdfasdf" not in url for _, url in pages)


def test_discovery_deduplicates_mirrored_page_titles(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="大陸地區",
        school_name="武漢大學 Wuhan University",
        website="https://en.whu.edu.cn/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "Students Exchange Programs-Wuhan University",
                "https://en.whu.edu.cn/jzbf/International1/Students_Exchange_Programs.htm",
            ),
            (
                "Students Exchange Programs-Wuhan University",
                "https://en.whu.edu.cn/International1/Students_Exchange_Programs.htm",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)
    exchange_pages = [url for title, url in pages if "Exchange Programs" in title]

    assert exchange_pages == [
        "https://en.whu.edu.cn/International1/Students_Exchange_Programs.htm"
    ]


def test_discovery_prefers_english_locale_for_duplicate_title(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="法國",
        school_name="歐洲知識經濟與管理學院 Skema Business School",
        website="https://www.skema.edu/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            ("Exchange students | SKEMA", "https://www.skema.edu/br/node/10256"),
            ("Exchange students | SKEMA", "https://www.skema.edu/en/exchange-students"),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)
    exchange_pages = [url for title, url in pages if "Exchange students" in title]

    assert exchange_pages == ["https://www.skema.edu/en/exchange-students"]


def test_discovery_rejects_exchange_event_news(monkeypatch) -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="日本",
        school_name="日本順天堂大學Juntendo University",
        website="https://en.juntendo.ac.jp/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector._search_official_pages",
        lambda *args, **kwargs: [
            (
                "International Student Exchange Event | Juntendo University",
                "https://en.juntendo.ac.jp/news/exchange-event.html",
            ),
        ],
    )

    pages = discover_official_partner_pages(partner, max_pages=5)

    assert all("exchange-event" not in url for _, url in pages)


def test_lincoln_discovery_uses_incoming_official_pages() -> None:
    pages = discover_official_partner_pages(_partner(), max_pages=5)

    assert any(url == LINCOLN_INCOMING_URL for _, url in pages)
    assert all("lincoln.ac.nz" in url for _, url in pages)
    assert all("outbound" not in url for _, url in pages)


def test_lincoln_workflow_has_detailed_official_stages(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector.fetch_official_page_text",
        lambda *args, **kwargs: "",
    )
    workflow = collect_application_workflow(_partner(), rate_limit_seconds=0)

    assert len(workflow.steps) == 9
    assert any(step.responsible_party == "長庚國際處" for step in workflow.steps)
    assert any("護照" in document for step in workflow.steps for document in step.required_documents)
    assert any(step.needs_confirmation for step in workflow.steps)
    assert workflow.coverage_status == "official_verified"


def test_replace_workflow_preserves_other_schools(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    replace_application_workflow(_workflow("其他大學 Other University"), tmp_path)
    replace_application_workflow(_workflow(title="更新後流程"), tmp_path)

    rows = load_application_workflows(tmp_path)
    assert {row.school_name for row in rows} == {
        "其他大學 Other University",
        "林肯大學 Lincoln University",
    }
    assert next(row for row in rows if row.school_name.startswith("林肯")).steps[0].title == "更新後流程"


def test_replace_workflow_consolidates_chinese_name_aliases(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    replace_application_workflow(
        _workflow("諾歐商學院 NEOMA Business School"), tmp_path
    )
    replace_application_workflow(
        _workflow("法國諾歐商學院 NEOMA Business School", title="交換與雙聯流程"),
        tmp_path,
    )

    rows = load_application_workflows(tmp_path)
    assert len(rows) == 1
    assert rows[0].school_name == "法國諾歐商學院 NEOMA Business School"
    assert rows[0].steps[0].title == "交換與雙聯流程"


def test_workflow_api_reads_cache_and_refreshes_selected_school(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    replace_application_workflow(_workflow(), tmp_path)
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    monkeypatch.setattr(
        "exchange_info.api.collect_application_workflow",
        lambda partner, **kwargs: _workflow(title="重新查核流程"),
    )
    client = TestClient(create_app(tmp_path))

    cached = client.get("/application-workflow", params={"school": partner.school_name})
    assert cached.status_code == 200
    assert cached.json()["steps"][0]["title"] == "確認資格"

    refreshed = client.post(
        "/application-workflow/refresh", params={"school": partner.school_name}
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["steps"][0]["title"] == "重新查核流程"
    assert load_application_workflows(tmp_path)[0].steps[0].title == "重新查核流程"

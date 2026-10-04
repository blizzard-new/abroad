from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.models import PartnerUniversity
from exchange_info.ntpu_student_view import (
    NTPU_EXCHANGE_AGREEMENTS_WITHOUT_QUOTA,
    fetch_ntpu_partner_universities,
)
from exchange_info.school_identity import school_identity_key
from exchange_info.storage import ensure_data_dirs
from exchange_info.university_registry import NTPU, resolve_university


def test_ntpu_aliases_resolve_to_the_same_home_university() -> None:
    for alias in ("國立臺北大學", "臺北大學", "台北大學", "北大", "NTPU"):
        assert resolve_university(alias) == NTPU


def test_ntpu_partner_identity_ignores_pdf_location_suffix() -> None:
    assert school_identity_key("東北林業大學 黑龍江省哈爾 濱市") == school_identity_key(
        "東北林業大學"
    )


def test_bundled_official_ntpu_lists_are_available_offline(monkeypatch) -> None:
    def reject_network(*args, **kwargs):  # pragma: no cover - called only on regression
        raise AssertionError("bundled official PDFs should be used before the network")

    monkeypatch.setattr("exchange_info.ntpu_student_view.requests.get", reject_network)
    partners = fetch_ntpu_partner_universities()

    open_partners = [row for row in partners if row.availability_status == "open"]
    agreement_only = [
        row for row in partners if row.availability_status == "agreement_only"
    ]

    # 116 academic-year sheets: 133 + 16 + 21 rows (169 distinct open schools) and the
    # 37 agreements that still have no quota; eleven 115 agreements gained quotas.
    assert len(partners) == 206
    assert len(open_partners) == 169
    assert len(agreement_only) == 37
    assert {"英語組", "日語組", "中文組"}.issubset(
        {
            row.program_type.removeprefix("交換學生（").removesuffix("）")
            for row in open_partners
        }
    )
    assert "東北林業大學" in {row.school_name for row in partners}
    assert all("黑龍江省哈爾" not in row.school_name for row in partners)
    assert all(
        row.source_url.startswith("https://cms-carrier.ntpu.edu.tw/")
        for row in open_partners
    )
    assert {
        row.school_name for row in agreement_only
    } == {
        school_name
        for _, school_name, _, _ in NTPU_EXCHANGE_AGREEMENTS_WITHOUT_QUOTA
    }
    assert all(
        row.source_url == "https://new.ntpu.edu.tw/oia/sister-schools"
        for row in agreement_only
    )
    assert all(row.quota == "本期未開放交換名額" for row in agreement_only)
    assert all("未列入 116 學年度交換名額表" in row.availability_note for row in agreement_only)


def test_ntpu_application_templates_do_not_leak_cgu_copy() -> None:
    templates = all_application_templates("國立臺北大學")
    serialized = "\n".join(template.model_dump_json() for template in templates)

    assert templates
    assert "長庚" not in serialized
    assert "國立臺北大學" in serialized
    assert all(not template.official_layout for template in templates)
    assert all(not template.id.startswith("short-term-") for template in templates)


def test_ntpu_web_api_exposes_dashboard_rules_documents_and_search(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    partner = PartnerUniversity(
        program_type="交換學生（英語組）",
        country="日本",
        school_name="測試合作大學 Test Partner University",
        degree_levels="大學部、研究所",
        eligibility="IELTS 6.0，前一學年平均 75 分以上",
        source_url="https://cms-carrier.ntpu.edu.tw/uploads/test.pdf",
    )
    monkeypatch.setattr(
        "exchange_info.api.fetch_ntpu_partner_universities",
        lambda: [partner],
    )
    client = TestClient(create_app(data_dir))

    universities = client.get("/universities").json()
    ntpu = next(row for row in universities if row["id"] == "ntpu")
    assert ntpu["school_name"] == "國立臺北大學"
    assert ntpu["hero_image"] == "/static/assets/ntpu-campus.jpg"
    assert ntpu["support_level"] == "full"

    dashboard = client.get(
        "/student-dashboard", params={"school": "國立臺北大學"}
    ).json()
    assert dashboard["school_name"] == "國立臺北大學"
    assert dashboard["academic_score_minimum"] == 75
    assert dashboard["partner_universities"][0]["school_name"].startswith("測試合作大學")
    assert any("5,000" in row["details"][2] for row in dashboard["required_documents"])
    current, *recurring = dashboard["application_periods"]
    assert current["academic_year"] == "116" and current["date_status"] == "verified_exact"
    assert current["opens_at"].startswith("2026-10-01T00:00:00+08:00")
    assert current["deadline_at"].startswith("2026-10-23T17:00:00+08:00")
    assert current["reminder_eligible"] is False
    assert current["source"]["source_url"].startswith("https://new.ntpu.edu.tw/oia/news/")
    assert all(
        row["status"] == "reference_only"
        and row["date_status"] == "reference_only"
        and row["reminder_eligible"] is False
        for row in recurring
    )
    assert {row["application_round"] for row in recurring} == {"秋季／全學年梯次", "春季梯次"}

    templates = client.get(
        "/application-center/templates",
        params={"school": "國立臺北大學", "program_type": "exchange"},
    ).json()
    assert templates
    assert "長庚" not in str(templates)

    results = client.get(
        "/search", params={"school": "國立臺北大學", "q": "75分"}
    ).json()
    assert results and results[0]["title"].startswith("臺北大學")


def test_ntpu_116_round_status_follows_the_announced_window_without_guessing() -> None:
    from datetime import datetime, timezone

    from exchange_info.models import ApplicationPeriodStatus
    from exchange_info.ntpu_student_view import build_ntpu_student_dashboard

    def current(moment: datetime):
        return build_ntpu_student_dashboard(
            partner_universities=[], reference_time=moment
        ).application_periods[0]

    assert current(datetime(2026, 9, 30, tzinfo=timezone.utc)).status == ApplicationPeriodStatus.UPCOMING
    assert current(datetime(2026, 10, 3, tzinfo=timezone.utc)).status == ApplicationPeriodStatus.OPEN
    # 17:00 Taiwan time is 09:00 UTC; one minute later the round is closed.
    assert current(datetime(2026, 10, 23, 8, 59, tzinfo=timezone.utc)).status == ApplicationPeriodStatus.OPEN
    assert current(datetime(2026, 10, 23, 9, 1, tzinfo=timezone.utc)).status == ApplicationPeriodStatus.CLOSED
    assert "116 學年度名額表" in " ".join(current(datetime(2026, 10, 3, tzinfo=timezone.utc)).details)


def test_116_quota_sheets_replace_the_115_lists_and_keep_every_continuing_school() -> None:
    partners = fetch_ntpu_partner_universities()
    open_partners = [row for row in partners if row.availability_status == "open"]
    assert all(row.country != "未標示" for row in partners)
    # The three newly listed schools and a school promoted from agreement-only.
    names = " ".join(row.school_name for row in open_partners)
    for expected in ("烏迪內大學", "里昂商學院", "同濟大學", "百麗宮國際大學", "多倫多都會大學"):
        assert expected in names, expected
    agreements = {row.school_name for row in partners if row.availability_status != "open"}
    assert not agreements & {"中央財經大學", "百麗宮國際大學", "拉脫維亞大學"}
    assert all("116" in row.application_deadline for row in open_partners)
    assert all(row.source_url.endswith(("116_0924_da1dafe9d0.pdf", "116_26b28374db.pdf", "116_6524fec218.pdf"))
               for row in open_partners)

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.models import PartnerUniversity
from exchange_info.ntpu_student_view import fetch_ntpu_partner_universities
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

    assert len(partners) == 155
    assert {"英語組", "日語組", "中文組"}.issubset(
        {row.program_type.removeprefix("交換學生（").removesuffix("）") for row in partners}
    )
    assert "東北林業大學" in {row.school_name for row in partners}
    assert all("黑龍江省哈爾" not in row.school_name for row in partners)
    assert all(row.source_url.startswith("https://cms-carrier.ntpu.edu.tw/") for row in partners)


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

    dashboard = client.get(
        "/student-dashboard", params={"school": "國立臺北大學"}
    ).json()
    assert dashboard["school_name"] == "國立臺北大學"
    assert dashboard["academic_score_minimum"] == 75
    assert dashboard["partner_universities"][0]["school_name"].startswith("測試合作大學")
    assert any("5,000" in row["details"][2] for row in dashboard["required_documents"])

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

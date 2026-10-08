import hashlib
import importlib.util
import json

import requests

from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def source(name):
    return json.loads((BUNDLE / "overseas_sources" / f"{name}.json").read_text())


def fields(page):
    return next(
        p.partner_exchange_details
        for p in fetch_ccu_partner_universities()
        if p.source_pages[0] == page
    )


def test_nagoya_university_agreement_resolves_departmental_scope_without_losing_it():
    f = fields(34)
    assert f["program_scope"].status == "verified_current"
    assert "*U" in f["program_scope"].value and "校級" in f["program_scope"].value
    assert f["program_scope"].evidence[0].source_pages == [32]
    assert "Interdepartmental" in source("p34-mirror")["content_academic_year"]
    assert "2026" in source("p34-mirror")["content_academic_year"]
    assert "2026-10-01" in f["nomination_deadline"].value
    assert "2026-10-15" in f["application_deadline"].value
    assert f["host_tuition"].status == "verified_current"
    assert "fee-paying" in f["host_tuition"].value
    assert "3.0" in f["eligibility"].value and "JASSO" in f["eligibility"].value
    assert "15研究小時" in f["course_restrictions"].value
    assert "實驗課" in f["course_restrictions"].value


def test_opened_current_nagoya_templates_do_not_claim_the_full_invitation_form():
    f = fields(34)
    assert f["documents"].status == "verified_current"
    assert "JPY500000" in f["documents"].value
    assert "限定" in f["documents"].value
    assert f["application_forms"].status == "needs_confirmation"
    assert "完整online" in f["application_forms"].value
    for suffix in [
        "study-plan",
        "research-plan",
        "medical-study-plan",
        "clerkship-form",
        "reference-form",
        "health-form",
        "specific-categories",
    ]:
        s = source(f"p34-r5-{suffix}")
        body = (BUNDLE / s["bundled_file"]).read_bytes()
        assert body.startswith((b"%PDF-", b"PK"))
        assert hashlib.sha256(body).hexdigest() == s["sha256"]
        assert s["text_pages"] and s["content_applicability"] == "verified_current"


def test_gachon_2027_calendar_and_checkout_are_separate_from_2025_prices():
    f = fields(52)
    assert f["academic_calendar"].status == "verified_current"
    assert "2027-03-02" in f["academic_calendar"].value
    assert "06-21" in f["academic_calendar"].value
    assert f["housing"].status == "verified_current" and "06-19" in f["housing"].value
    assert f["costs"].status == "needs_confirmation" and "2025" in f["costs"].value
    assert "1486400" in f["costs"].value
    assert "based on 2025 prices" in source("p52-r5-housing-expanded")["text_pages"][1]
    assert f["arrival"].status == "conflict" and "Dec21" in f["arrival"].value
    assert f["eligibility"].status == "conflict"
    assert "recommended" in f["eligibility"].value
    assert f["application_forms"].status == "needs_confirmation"
    assert "簽名" in f["application_forms"].value
    assert f["nomination_deadline"].status != "verified_current"


def test_cau_fall_2026_and_short_programs_do_not_become_spring_2027_policy():
    s = source("p50-r5-factsheet-article")
    assert "2026 Fall Fact Sheet" in s["text_pages"][0]
    assert (
        source("p50-r5-fall26-factsheet")["content_applicability"] == "reference_only"
    )
    f = fields(50)
    for key in ["application_forms", "academic_calendar", "housing_deadline", "visa"]:
        assert f[key].status == "needs_confirmation"
    assert "visiting" in f["host_tuition"].value
    assert f["arrival"].status == "needs_confirmation"
    assert "Medicine" in f["program_scope"].value


def test_bordeaux_current_orientation_and_courses_keep_calendar_and_la_conflicts():
    f = fields(85)
    assert (
        f["arrival"].status == "verified_current" and "2027-01-07" in f["arrival"].value
    )
    assert f["academic_calendar"].status == "conflict"
    assert "weekday" in f["academic_calendar"].value
    assert f["documents"].status == "conflict"
    assert f["course_restrictions"].status == "verified_current"
    assert "全英文授課" in f["course_restrictions"].value
    assert f["language"].status == "needs_confirmation"
    assert "2026-07-01" in f["housing"].value and "不保证" in f["housing"].value
    assert (
        source("p85-r5-government-apl")["authority"]
        == "government_official_public_page"
    )
    assert "February 2026" in source("p85-r5-factsheet")["text_pages"][0]


def test_amu_erasmus_deadlines_do_not_replace_bilateral_and_phd_policy():
    f = fields(95)
    assert f["language"].status == "needs_confirmation"
    assert "recommend" in f["language"].value and "母校" in f["language"].value
    assert f["academic_calendar"].status == "verified_current"
    assert (
        "06-20" in f["academic_calendar"].value
        and "07-04" in f["academic_calendar"].value
    )
    assert f["nomination_deadline"].status == "needs_confirmation"
    assert "Erasmus" in f["nomination_deadline"].value
    assert f["application_deadline"].status == "needs_confirmation"
    assert f["documents"].status == "reference_only"
    assert f["insurance"].status == "missing" and f["insurance"].value is None


def test_fhnw_2027_entry_keeps_actual_2026_basel_and_olten_scope():
    f = fields(104)
    assert f["course_restrictions"].status == "conflict"
    assert "Basel" in f["course_restrictions"].value
    assert "全學年" in f["course_restrictions"].value
    assert source("p104-r5-offer-1")["content_applicability"] == "reference_only"
    assert "SEMESTER 2026" in source("p104-r5-offer-1")["text_pages"][0]
    assert f["academic_calendar"].status == "verified_current"
    assert "Olten" in f["academic_calendar"].value
    assert "2027-02-16" in f["arrival"].value
    assert "07-10" in f["academic_calendar"].value
    assert f["nomination_deadline"].status == "needs_confirmation"
    assert "没有独立" in f["nomination_deadline"].value
    assert f["costs"].status == "conflict"


def test_ledger_records_actual_read_scope_and_the_latest_change_inventory():
    ledger = json.loads((BUNDLE / "semantic-review-ledger.json").read_text())
    assert {r["ccu_page"] for r in ledger}.issuperset({
        24,
        27,
        29,
        34,
        50,
        52,
        74,
        85,
        95,
        104,
        111,
        119,
    })
    assert all(not r["complete_research_claimed"] for r in ledger)
    new = next(r for r in ledger if r["ccu_page"] == 85)
    assert (
        "p85-r5-humanities-master"
        in new["fields"]["course_restrictions"]["partially_reviewed_source_ids"]
    )
    changes = json.loads((BUNDLE / "fifth-pass-changes.json").read_text())
    assert changes["new_source_count"] == 79 and len(changes["changes"]) == 65
    assert sum(c["previous_status"] == "missing" for c in changes["changes"]) == 48
    assert len(reviewed_rows()) == 55
    field = reviewed_rows()[85]["fields"]["costs"]
    assert "不宣稱所有" in field["research_note"]
    check = next(
        s
        for s in field["source_checks"]
        if s["source_id"] == "p85-r5-humanities-master"
    )
    assert "部分" in check["result"] and "不宣稱" in check["result"]


def test_fetcher_reads_public_embedded_tables_and_display_accordions_without_execution(
    tmp_path,
):
    spec = importlib.util.spec_from_file_location(
        "ccu_public_embeds", "scripts/fetch_ccu_overseas_sources.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    html = """<main>2027 Academic Calendar</main>
    <div data-code="&lt;table&gt;&lt;tr&gt;&lt;td&gt;March 2&lt;/td&gt;&lt;/tr&gt;&lt;/table&gt;&lt;script&gt;DO_NOT_EXECUTE&lt;/script&gt;"></div>
    <script>window.__data={"messages":{"content":"unrelated"},"content": {"data":{"blocks":{"a":{"@type":"accordion","data":{"blocks":{"panel":{"title":"Application","data":{"blocks":{"p":{"text":"No nomination deadline","plaintext":"duplicate"}}}}}}}}}}};</script>
    <script>window.__data={"content": malformed}</script>
    <script>window.__data={"content":{"data":{"blocks":"not an object"}}}</script>
    <script>THROW_IF_EXECUTED()</script>"""

    class Session:
        def get(self, url, **kwargs):
            response = requests.Response()
            response.url = url
            response.status_code = 200
            response._content = html.encode()
            response.headers["Content-Type"] = "text/html"
            return response

    s = module.fetch_public_source(
        {
            "url": "https://official.example.edu/page",
            "source_id": "embed",
            "authority": "partner_official_public_page",
        },
        tmp_path,
        Session(),
    )
    assert s["status"] == "html" and s["embedded_content_count"] == 1
    assert s["public_accordion_count"] == 1
    assert "March 2" in s["text_pages"][1]
    assert "No nomination deadline" in s["text_pages"][2]
    assert "DO_NOT_EXECUTE" not in " ".join(s["text_pages"])
    assert "THROW_IF_EXECUTED" not in " ".join(s["text_pages"])
    assert "duplicate" not in " ".join(s["text_pages"])
    assert s["content_applicability"] == "needs_confirmation"

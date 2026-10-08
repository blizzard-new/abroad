"""Protect new public-source evidence, year scope and unresolved conflicts."""

import hashlib
import json

from docx import Document
from pypdf import PdfReader

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.models import UniversityApplicationWorkflow
from exchange_info.storage import read_jsonl


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


def source(sid):
    return json.loads((BUNDLE / "overseas_sources" / (sid + ".json")).read_text())


def test_augsburg_public_ss2027_form_does_not_promote_unversioned_policies():
    fields = at(102).partner_exchange_details
    form = fields["application_forms"]
    assert form.status == "verified_current" and "SS2027" in form.value
    portal = source("p102-r3-application-portal")
    assert "SS 2027" in portal["text_pages"][0]
    assert "Declaration of consent" in portal["text_pages"][0]
    for name in [
        "program_scope",
        "eligibility",
        "language",
        "documents",
        "course_restrictions",
        "insurance",
        "visa",
        "exchange_duration",
    ]:
        assert fields[name].status == "needs_confirmation"
    assert "15–30" in fields["course_restrictions"].value
    assert "非硬性最低" in fields["course_restrictions"].value
    docs = fields["documents"]
    assert "六類" in docs.value and "portfolio" in docs.value
    assert "signature AND STAMP" in docs.value
    assert "500×500" in docs.value and "完整清單" in docs.value
    assert {
        source(sid)["source_url"]
        for sid in [
            "p102-r3-exchange-en",
            "p102-r3-exchange-de",
            "p102-r3-learning-agreement-web",
        ]
    } <= {e.source_url for e in docs.evidence}
    assert "03-01至03-03" in fields["arrival"].value
    assert "03-04至03-14" in fields["arrival"].value


def test_actual_web_pdf_extraction_is_distinct_from_failed_raw_download():
    src = source("p102-r3-learning-agreement-web")
    assert src["status"] == "web_extracted_pdf"
    assert "not raw HTTP or PDF bytes" in src["sha256_basis"]
    assert "http_status" not in src and "bundled_file" not in src
    assert (
        hashlib.sha256(src["web_extraction_response"].encode()).hexdigest()
        == src["sha256"]
    )
    assert "LEARNING AGREEMENT – NON ERASMUS" in src["text_pages"][0]
    assert "STAMP" in src["text_pages"][0]
    assert source("p102-r3-learning-agreement")["http_status"] == 429
    ev = next(
        e
        for e in at(102).partner_exchange_details["documents"].evidence
        if e.source_url == src["source_url"]
    )
    assert ev.source_pages == [1] and ev.status == "needs_confirmation"


def test_ludwigshafen_filename_2026_contains_actual_summer_2027_move_in():
    src = source("p98-r3-accommodation-form")
    path = BUNDLE / src["bundled_file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == src["sha256"]
    assert "Accommodation_Request_2026" in src["source_url"]
    text = PdfReader(path).pages[0].extract_text()
    assert "summer semester 2027" in text and "22nd" in text and "25th" in text
    fields = at(98).partner_exchange_details
    assert fields["arrival"].status == "verified_current"
    assert "2027-02-22至02-25" in fields["arrival"].value
    assert fields["housing_deadline"].status == "missing"
    forms = fields["application_forms"]
    assert "實際讀取" in forms.value and "提交後產生" in forms.value
    assert forms.research_category == "login_or_school_confirmation"
    assert forms.status == "needs_confirmation"
    assert source("p98-r3-application")["http_status"] == 418
    web = source("p98-r3-application-web")
    assert web["status"] == "web_extracted_html" and "http_status" not in web
    assert (
        "JPEG only" in web["text_pages"][0]
        and "signed by the coordinator" in web["text_pages"][0]
    )
    la = source("p98-r3-learning-agreement")
    doc = Document(BUNDLE / la["bundled_file"])
    assert any(
        "Signature" in cell.text
        for table in doc.tables
        for row in table.rows
        for cell in row.cells
    )
    assert "Erasmus" in la["text_pages"][0]


def test_receiving_reciprocity_cap_preserves_ccu_home_quota():
    p = at(48)
    assert p.quota == "一學期(one semester) 2名 或 一學年(one year) 1名"
    assert p.quota_status == "published" and p.availability_status == "open"
    field = p.partner_exchange_details["eligibility"]
    assert field.status == "verified_current"
    assert "最多2名" in field.value and "僅1席" in field.value
    assert {page for e in field.evidence for page in e.source_pages} == {4, 5}
    assert "個人GPA" in field.value


def test_fges_partial_certificate_requirement_and_approximate_welcome():
    p = at(88)
    docs = p.partner_exchange_details["documents"]
    assert docs.status == "verified_current" and "不是完整附件清單" in docs.value
    assert "advised" in docs.value and "未限定證照" in docs.value
    arrival = p.partner_exchange_details["arrival"]
    assert arrival.status == "verified_current" and "1月第一週" in arrival.value
    assert "未列確切日" in arrival.value
    flow = next(
        f
        for f in read_jsonl(
            BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
        )
        if f.school_name == p.school_name
    )
    assert flow.steps[4].required_documents == [docs.value]
    assert flow.steps[4].deadline_at is None


def test_pardubice_calendar_and_application_have_independent_year_evidence():
    p = at(107)
    assert p.quota is None and p.availability_status == "needs_confirmation"
    fields = p.partner_exchange_details
    assert fields["nomination_deadline"].status == "conflict"
    assert "2025/26" in fields["nomination_deadline"].value
    assert fields["application_deadline"].status == "verified_current"
    assert "2026-10-10" in fields["application_deadline"].value
    assert fields["academic_calendar"].status == "verified_current"
    assert "08-16至08-31" in fields["academic_calendar"].value
    assert "faculty可調整" in fields["academic_calendar"].value
    assert "護照影本" in fields["documents"].value
    assert "非護照影本" in fields["documents"].value
    src = source("p107-r3-learning-agreement")
    assert (
        hashlib.sha256((BUNDLE / src["bundled_file"]).read_bytes()).hexdigest()
        == src["sha256"]
    )
    assert "Commitment of the three parties" in src["text_pages"][0]
    assert fields["application_forms"].status == "verified_current"


def test_chitkara_generic_docs_and_brochure_do_not_override_current_deadlines():
    p = at(73)
    fields = p.partner_exchange_details
    assert fields["documents"].status == "needs_confirmation"
    assert "五項" in fields["documents"].value
    deadline = fields["application_deadline"]
    assert deadline.status == "conflict" and "2nd Week of October" in deadline.value
    assert "2026/10/20" in deadline.value and "2026-10-30" in deadline.value
    assert fields["housing"].status == "needs_confirmation"
    assert fields["housing"].evidence[0].source_pages == [25]
    brochure = source("p73-r3-brochure")
    assert brochure["bytes"] == 52662368 and len(brochure["text_pages"]) == 29
    assert "OCR" in brochure["extraction_method"]
    assert "未標交換適用年度" in brochure["content_academic_year"]
    for key in ["housing_deadline", "costs", "insurance", "visa", "host_tuition"]:
        assert fields[key].status == "missing"
    assert at(33).partner_exchange_details["academic_calendar"].status == "missing"


def test_conflicts_are_research_gaps_instead_of_invented_login_blockers():
    audit = json.loads((BUNDLE / "research-gap-audit.json").read_text())
    counts = audit["category_counts"]
    assert sum(counts.values()) == 935
    report = json.loads((BUNDLE / "overseas-completeness.json").read_text())
    assert (
        counts["unresolved_source_conflict"]
        == report["overseas_field_status_counts"]["conflict"]
    )
    assert counts["source_technical_failure"] == 0
    assert counts["alternative_official_sources_not_fully_checked"] <= 656
    for row in audit["schools"]:
        for f in row["fields"].values():
            if f["status"] == "conflict":
                assert f["category"] == "unresolved_source_conflict"
    assert at(101).partner_exchange_details["academic_calendar"].status == "conflict"
    assert "2026" in at(101).partner_exchange_details["academic_calendar"].value
    changes = json.loads((BUNDLE / "third-pass-changes.json").read_text())
    assert changes["new_source_count"] == 30 and len(changes["changes"]) == 45
    assert sum(c["previous_status"] == "missing" for c in changes["changes"]) == 34
    assert not changes["complete_research_claimed"]


def test_altered_web_response_requires_new_content_review(tmp_path, monkeypatch):
    import exchange_info.ccu_overseas as module

    rows = json.loads((BUNDLE / "overseas-reviewed-fields.json").read_text())
    reviewed = next(r for r in rows if r["ccu_page"] == 102)["fields"]["documents"]
    web_ev = next(
        e
        for e in reviewed["evidence"]
        if e["source_id"] == "p102-r3-learning-agreement-web"
    )
    for row in rows:
        for field in row["fields"].values():
            field.update(value=None, status="missing", evidence=[])
    rows[0]["fields"]["documents"].update(
        value="Acquired template", status="needs_confirmation", evidence=[web_ev]
    )
    (tmp_path / "overseas-reviewed-fields.json").write_text(json.dumps(rows))
    directory = tmp_path / "overseas_sources"
    directory.mkdir()
    src = source(web_ev["source_id"])
    src["web_extraction_response"] += " changed extracted body"
    (directory / (src["source_id"] + ".json")).write_text(json.dumps(src))
    monkeypatch.setattr(module, "BUNDLE", tmp_path)
    module.reviewed_rows.cache_clear()
    try:
        import pytest

        with pytest.raises(ValueError, match="Changed CCU web extraction response"):
            module.reviewed_rows()
    finally:
        module.reviewed_rows.cache_clear()

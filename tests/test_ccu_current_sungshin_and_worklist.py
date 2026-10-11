"""Latest receiving documents, stale years and publicly readable research backlog."""
import json

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import (
    build_ccu_workflow,
    fetch_ccu_partner_universities,
)


def read(name):
    return json.loads((BUNDLE / name).read_text())


def school(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_sungshin_new_calendar_and_application_window_supersede_archived_typo():
    partner = school(49)
    assert "2027-03-02" in partner.semester_dates and "2026-10-26" in partner.partner_application_deadline
    assert partner.partner_exchange_details["academic_calendar"].status == "verified_current"
    original = next(r for r in read("overseas-reviewed-fields.json") if r["ccu_page"] == 49)
    assert original["fields"]["academic_calendar"]["status"] == "conflict"
    assert "02-29" in original["fields"]["academic_calendar"]["value"]
    assert partner.application_window_status == "closed" and partner.availability_status == "open"


def test_sungshin_2027_nomination_cell_and_doctoral_limit_stay_conflicting():
    partner = school(49)
    forms = partner.partner_exchange_details["application_forms"]
    assert forms.status == "conflict" and "2025-12-01" in forms.value
    cell = next(e for e in forms.evidence if "113951" in e.source_url)
    assert not cell.source_pages and "1 December 2025" in cell.excerpt
    restriction = partner.partner_exchange_details["course_restrictions"]
    assert restriction.status == "conflict" and "博士" in restriction.value
    assert {tuple(e.source_pages) for e in restriction.evidence if "113855" in e.source_url} == {(2,), (4,), (5,)}
    language = partner.partner_exchange_details["language"]
    assert language.status == "conflict" and "2026-01-20" in language.value and "3.5" in language.value
    assert all(c.scope_choice_required for c in partner.language_conditions)


def test_current_medical_template_is_downloadable_and_old_xray_is_not_universal(tmp_path):
    partner = school(49)
    workflow = build_ccu_workflow(partner)
    step = next(s for s in workflow.steps if s.phase == "合作校申請")
    assert len(step.document_requirements) == 9
    assert sum(r.conditional for r in step.document_requirements) == 1
    assert step.submission.method == "mixed" and "2026-11-23抵校" in step.submission.deadline_note
    medical = next(r for r in step.document_requirements if "Medical" in r.name)
    assert medical.signatures == ["學生"] and medical.needs_confirmation
    assert medical.official_form_verified and medical.applicability_status == "needs_confirmation"
    assert medical.official_form_url.endswith("113856/download.do#page=2")
    assert not any("X-ray" in r.name or "X光" in r.name for r in step.document_requirements)
    client = TestClient(create_app(tmp_path))
    result = client.get("/application-center/catalog", params={"school": HOME, "target_school": partner.school_name})
    assert result.status_code == 200
    actual = next(r for r in result.json()["items"] if "Personal Medical Assessment" in r["name"])
    assert actual["download_available"] and actual["official_form_verified"]
    assert actual["needs_confirmation"] and actual["signatures"] == ["學生"]


def test_sdu_missing_fields_remain_unverified_year_and_account_access_is_scoped():
    partner = school(89)
    for key in ["program_scope", "academic_calendar", "visa", "arrival"]:
        field = partner.partner_exchange_details[key]
        assert field.status == "needs_confirmation" and field.evidence
    row = next(r for r in read("completion-remaining-public-worklist.json")["schools"] if r["ccu_page"] == 89)
    assert {f["field"] for f in row["external_access_limited_steps"]} == {"application_forms"}
    assert row["host_missing_count"] == 0


def test_remaining_worklist_separates_reading_duplicates_assets_and_external_steps():
    queue = read("completion-remaining-public-worklist.json")
    assert len(queue["schools"]) == 104
    assert queue["counts"]["host_missing_fields"] == 638
    sources = [s for r in queue["schools"] for s in r["sources"]] + queue["shared_and_global_sources"]
    assert len(sources) == len({s["source_id"] for s in sources}) == queue["counts"]["sources"]
    assert all(s["source_url"] and s["checked_at"] for s in sources)
    duplicates = next(s for s in sources if s["source_id"] == "p104-current-factsheet-from-official-index")
    assert "p104-mirror" in duplicates["same_bytes_as_recorded_read_sources"]
    assert duplicates["review_state"] != "readable_body_without_recorded_review"
    limitations = read("completion-remaining-limitations.json")
    assert {r["ccu_page"] for r in limitations["schools"]} == {44, 66, 71, 80, 96, 111, 119}
    assert all(not r["official_exclusive_access_proven"] for r in limitations["schools"])
    assert limitations["gamma"]["denominator"] is None and not limitations["gamma"]["official_exclusive_access_proven"]

"""Current receiving references must preserve home scope and older-year limits."""
import gzip
import hashlib
import json

from docx import Document
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def read(name):
    return json.loads((BUNDLE / name).read_text())


def row(page):
    return next(r for r in read("completion-reviewed-fields.json")["schools"] if r["ccu_page"] == page)


def test_priority_review_records_preserve_each_acquisition_and_deduplicate_doc():
    progress = read("completion-seventh-public-progress.json")
    assert progress["priority_urls_processed"] == 37
    assert progress["priority_distinct_bodies_processed"] == 36
    assert not progress["old_priority_still_without_recorded_read"]
    assert progress["new_scoped_reading_records"] == 61
    assert progress["changed_host_fields"] == 30
    assert progress["previously_missing_host_fields_filled"] == 20
    assert progress["remaining_school_public_source_urls"] == 370
    assert progress["remaining_school_public_independent_bodies"] == 369
    assert not progress["remaining_public_sources_exhausted"]
    for record in read("completion-public-body-reviews.json"):
        if record.get("batch") != 7:
            continue
        receipt = read("completion_sources/" + record["source_id"] + ".receipt.json")
        path = BUNDLE / receipt["bundled_file"]
        body = path.read_bytes()
        if path.suffix == ".gz":
            body = gzip.decompress(body)
        assert hashlib.sha256(body).hexdigest() == record["content_hash"] == receipt["sha256"]
        assert record["source_url"] == receipt["source_url"]
        assert record["checked_at"] == receipt["checked_at"]
        assert record["review_extent"] and record["academic_year"]


def test_outgoing_events_and_unversioned_medical_are_read_without_policy_promotion():
    ledger = {r["source_id"]: r for r in read("completion-public-body-reviews.json")}
    for sid in ["p48-host_entry-2", "p53-host_entry-1", "p53-host_entry-2"]:
        assert ledger[sid]["disposition"] == "outgoing_not_ccu_incoming"
    assert ledger["p79-host_entry-1"]["disposition"] == "conference_not_exchange"
    assert ledger["p99-host_entry-2"]["disposition"] == "event_not_exchange"
    assert ledger["p21-reference-folder-3"]["disposition"] == "unversioned_template"
    for page, ids in [(48, {"p48-host_entry-2"}), (53, {"p53-host_entry-1", "p53-host_entry-2"}), (79, {"p79-host_entry-1"}), (99, {"p99-host_entry-2"})]:
        assert not any(e.get("source_id") in ids for field in row(page)["host_fields"].values() for e in field["evidence"])


def test_ucsi_old_deadlines_and_language_stay_reference_only():
    school = row(63)
    assert school["availability_status"] == "not_open"
    for key in ["program_scope", "eligibility", "language", "nomination_deadline", "application_deadline", "course_restrictions", "exchange_duration"]:
        field = school["host_fields"][key]
        assert field["status"] == "reference_only"
        assert all("2025" in e["academic_year"] for e in field["evidence"])
    assert "2024-10-03" in school["host_fields"]["application_deadline"]["value"]
    assert school["host_fields"]["housing"]["status"] == "needs_confirmation"
    assert school["host_fields"]["documents"]["value"] is None


def test_ucy_current_dates_do_not_open_home_or_resolve_language_conflict():
    school = row(84)
    for key in ["nomination_deadline", "application_deadline", "academic_calendar", "housing_deadline"]:
        assert school["host_fields"][key]["status"] == "verified_current"
    language = school["host_fields"]["language"]
    assert language["status"] == "conflict"
    assert {"p84-seventh-current-language", "p84-seventh-discovered-target-13"} <= {e["source_id"] for e in language["evidence"]}
    assert school["host_fields"]["visa"]["status"] == "needs_confirmation"
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages == [84])
    assert partner.quota is None and partner.eligibility is None and partner.language_requirement is None
    assert partner.availability_status == "not_open" and partner.application_window_status == "closed"
    assert not partner.partner_exchange_details


def test_ucy_actual_bilateral_form_has_blank_year_and_signature_roles():
    receipt = read("completion_sources/p84-seventh-current-bilateral-form.receipt.json")
    doc = Document(BUNDLE / receipt["bundled_file"])
    text = " ".join(p.text for p in doc.paragraphs)
    assert "ACADEMIC YEAR 20__ - 20__" in text
    assert "Signature of the Student" in text and "Signature of International office" in text
    field = row(84)["host_fields"]["application_forms"]
    assert field["status"] == "needs_confirmation" and "學年20__" in field["value"]
    assert field["evidence"][0]["source_pages"] == []


def test_csun_annual_installments_are_not_monthly_or_spring_only_quote():
    school = row(115)
    assert school["host_fields"]["housing"]["status"] == "needs_confirmation"
    assert "候補" in school["host_fields"]["housing"]["value"]
    costs = school["host_fields"]["costs"]
    assert costs["status"] == "needs_confirmation"
    assert all(s in costs["value"] for s in ["11351", "9153", "8812", "分期款而非月租", "Spring單期"])
    assert school["host_fields"]["host_tuition"]["value"] is None


def test_sungshin_current_form_aliases_and_stale_form_years_are_explicit():
    docs = read("completion-sungshin-documents.json")
    assert docs["public_nomination"]["academic_year"] == "Spring2027"
    assert len(docs["requirements"]) == 9
    r8, r11 = [read(f"completion_sources/p49-seventh-discovered-target-{n}.receipt.json") for n in [8, 11]]
    assert r8["resolved_url"].split("?")[0] == r11["resolved_url"].split("?")[0]
    forms = row(49)["host_fields"]["application_forms"]
    assert forms["status"] == "conflict"
    assert all(x in forms["value"] for x in ["Fall2026", "已關閉Spring2026", "Page1/2", "2025-12-01"])


def test_leti_official_anchor_identity_does_not_claim_main_body_success():
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages == [96])
    assert partner.website == "https://etu.ru/en/university/"
    assert partner.availability_status == "not_open" and partner.application_window_status == "closed"
    main = read("completion_sources/p96-seventh-linked-university.receipt.json")
    assert main["http_status"] == 503 and main["error"]
    assert row(96)["general_campus_fields"]["website"]["evidence"][0]["source_id"] == "p96-seventh-official-rafu"
    limits = read("completion-remaining-limitations.json")
    assert limits["gamma"]["denominator"] is None
    assert not limits["gamma"]["seventh_result"]["exclusive_access_proven"]
    assert not limits["gamma"]["seventh_result"]["complete_public_export_obtained"]


def test_current_ucy_reference_fields_are_exposed_through_school_scoped_api(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/student-dashboard", params={"school": HOME})
    assert response.status_code == 200
    payload = response.json()
    partners = payload["partner_universities"]
    partner = next(p for p in partners if p["source_pages"] == [84])
    ref = json.loads(partner["reference_data"]["ccu_completion"])["reference_host_fields"]
    assert ref["nomination_deadline"]["status"] == "verified_current"
    assert ref["language"]["status"] == "conflict"
    assert partner["availability_status"] == "not_open" and partner["quota"] is None

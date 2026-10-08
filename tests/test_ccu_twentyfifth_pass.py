"""Actual saved bodies: scoped dispositions, student forms and document stages."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents, verified_form_urls
from exchange_info.ccu_student_view import fetch_ccu_partner_universities

BUNDLE = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/ccu"
HOME = "國立中正大學"


def read(name):
    return json.loads((BUNDLE / name).read_text())


def school(page):
    return next(p.school_name for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_frozen_323_backlog_has_a_body_proved_scoped_disposition():
    review = read("twentyfifth-source-review.json")
    baseline = review["backlog_baseline"]["sources"]
    assert len(baseline) == len({r["source_id"] for r in baseline}) == 323
    assert Counter(r["body_state"] for r in baseline) == {
        "readable_body_not_semantically_reviewed": 149, "read_body_not_mapped": 174,
    }
    entries = {r["source_id"]: r for r in review["source_reviews"]}
    assert len(entries) == 324 and review["additional_review_sources"] == 1
    assert review["backlog_processed"] == 323
    assert review["backlog_remaining_without_disposition"] == 0
    assert Counter(entries[r["source_id"]]["disposition"] for r in baseline) == review["disposition_counts"]
    for sid, entry in entries.items():
        source = read("overseas_sources/" + sid + ".json")
        assert entry["source_content_read"] and entry["review_note"]
        assert entry["sha256"] == source["sha256"]
        assert entry["text_sha256"] == hashlib.sha256(json.dumps(source["text_pages"], ensure_ascii=False).encode()).hexdigest()
        assert entry["checked_at"] and entry["academic_year"] and entry["source_url"]
        assert entry["disposition"] != "mapping_required"
        for proof in entry["body_evidence"]:
            body = " ".join(" ".join(source["text_pages"][p - 1] for p in proof["source_pages"]).split())
            assert proof["excerpt"] in body
        assert entry["all_policy_review_complete"] is False


def test_duplicate_disposition_requires_same_body_and_existing_mapping():
    triage = read("body-review-triage.json")
    sources = {r["source_id"]: r for s in triage["schools"] for r in s["sources"]}
    entries = [r for r in read("twentyfifth-source-review.json")["source_reviews"] if r["disposition"] == "duplicate_mapped_body"]
    assert len(entries) == 21
    for entry in entries:
        body = read("overseas_sources/" + entry["source_id"] + ".json")["text_pages"]
        for counterpart in entry["matched_mapped_sources"]:
            assert read("overseas_sources/" + counterpart + ".json")["text_pages"] == body
            assert sources[counterpart]["mapped_fields"]


def test_document_body_evidence_counts_as_mapping_and_latest_review_is_used():
    triage = read("body-review-triage.json")
    sources = {r["source_id"]: r for s in triage["schools"] for r in s["sources"]}
    for sid in ["p52-r5-form-docx", "p32-r7-jp-evaluation-form", "p37-r7-consent-form"]:
        assert any(r["kind"] == "document" for r in sources[sid]["mapped_fields"])
    # Lexical filename order puts twentyfirst after twentyfifth. The actual
    # newer body decision must win over that older review entry.
    assert sources["p114-r21-127da9624a"]["body_state"] == "reviewed_scoped_exclusion"
    assert sources["p45-r23-follow-3879e18719"]["body_state"] == "reviewed_index_linked_bodies_separate"
    assert all(r["body_state"] not in {"read_body_not_mapped", "readable_body_not_semantically_reviewed"} for r in sources.values())
    evaluation = next(r for r in reviewed_documents()[32]["requirements"] if any(e["source_id"] == "p32-r7-jp-evaluation-form" for e in r["evidence"]))
    # A stamp omitted from extracted DOCX text does not waive the current
    # application index's explicit institutional-stamp requirement.
    assert evaluation["requirement"]["stamps"]
    assert "institutional stamp" in " ".join(e["excerpt"] for e in evaluation["evidence"] if e["source_id"] == "p32-r7-application-index")


def test_actual_gachon_form_has_signature_but_no_invented_current_revision():
    requirements = reviewed_documents()[52]["requirements"]
    assert len(requirements) == 8
    assert all(r["applicability_status"] == "needs_confirmation" for r in requirements)
    form = next(r for r in requirements if "學生申請表" in r["requirement"]["name"])
    assert form["stage"] == "student_application"
    assert form["requirement"]["official_form_url"] in verified_form_urls()
    assert "Signature" in form["requirement"]["signatures"][0]
    assert not form["requirement"]["stamps"]
    assert any(e["source_id"] == "p52-r5-form-docx" and "Signature:" in e["excerpt"] for e in form["evidence"])
    language = next(r for r in requirements if "語言證明" in r["requirement"]["name"])
    assert language["conditional"] and "if applicable" in language["condition"]


def test_gachon_verified_file_and_pending_year_survive_student_catalog(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-center/catalog", params={"school": HOME, "target_school": school(52)})
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    form = next(r for r in items if "一般清單未核2027）學生申請表" in r["name"])
    assert form["official_form_verified"] is True
    assert form["applicability_status"] == "needs_confirmation"
    assert form["stage"] == "student_application" and form["signatures"]


def test_ccnu_arrival_letters_and_fges_nomination_are_separate_stages(tmp_path):
    client = TestClient(create_app(tmp_path))
    ccnu = client.get("/application-center/catalog", params={"school": HOME, "target_school": school(29)}).json()["items"]
    arrival = [r for r in ccnu if "（到校" in r["name"]]
    assert len(arrival) == 3 and all(r["stage"] == "post_offer" for r in arrival)
    assert all(r["applicability_status"] == "needs_confirmation" for r in arrival)
    fges = client.get("/application-center/catalog", params={"school": HOME, "target_school": school(88)}).json()["items"]
    nomination = next(r for r in fges if "逐學生線上提名" in r["name"])
    assert nomination["stage"] == "nomination" and nomination["conditional"]
    assert "母校經辦" in nomination["condition"]


def test_old_years_and_public_indexes_do_not_become_unannounced_or_exhausted():
    review = read("twentyfifth-source-review.json")
    entries = {r["source_id"]: r for r in review["source_reviews"]}
    for sid in ["p48-r9-calendar", "p50-r19-factsheet-notice", "p80-mirror", "p105-mirror", "p108-r19-9220ea9c14"]:
        assert entries[sid]["disposition"] == "reference_only"
    assert entries["p105-r8-calendar-cyprus"]["disposition"] == "out_of_scope"
    assert entries["p95-r5-healthcare"]["disposition"] == "out_of_scope"
    amu = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 95)
    assert amu.partner_exchange_details["insurance"].status == "missing"
    assert amu.partner_exchange_details["insurance"].value is None
    assert review["processable_followups"] and all(not r["external_unannounced"] for r in review["processable_followups"])
    triage = read("body-review-triage.json")
    assert all(s["public_sources_exhausted"] is False for s in triage["schools"])
    unannounced = [(s["ccu_page"], f["field"]) for s in triage["schools"] for f in s["official_explicit_unannounced_fields"]]
    assert unannounced == [(47, "arrival")]

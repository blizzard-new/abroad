"""Fourth public-source pass: scope, original years and visible stage contracts."""
import gzip
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_student_view import build_ncu_student_dashboard

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    with TestClient(create_app(tmp_path_factory.mktemp("ncu-fourth-pass"))) as result:
        yield result


def partner(needle):
    return next(p for p in build_ncu_student_dashboard().partner_universities if needle in p.school_name)


def get(client, endpoint, needle):
    response = client.get(endpoint, params={"school": partner(needle).school_name, "home_school": "NCU"})
    assert response.status_code == 200
    return response.json()


def initial(workflow, rid):
    return next(s for s in workflow["steps"] if s["rule_id"] == rid + "-host-apply")


@pytest.mark.parametrize("needle,rid,count", [
    ("Western Sydney", "ncu-001", 4), ("Douglas", "ncu-100", 4),
    ("Manitoba", "ncu-101", 7), ("Montreal", "ncu-102", 10),
    ("Florida", "ncu-104", 9), ("Northern Arizona", "ncu-105", 6),
])
def test_fourth_pass_actual_interfaces_keep_year_quota_and_documents_unconfirmed(client, needle, rid, count):
    p = partner(needle)
    workflow = get(client, "/application-workflow", needle)
    assert len(initial(workflow, rid)["document_requirements"]) == count
    assert workflow["review_status"] == "pending_review" and p.quota is None
    assert p.availability_status == "agreement_only"
    assert all(not s["deadline_reminder_eligible"] for s in workflow["steps"])
    assert all(d["stage"] == "student_application" for d in initial(workflow, rid)["document_requirements"])
    catalog = client.get("/application-center/catalog", params={"school": "NCU", "target_school": p.school_name, "academic_year": "116"}).json()
    assert all(not d["download_available"] for d in catalog["items"])
    assert all(d["needs_confirmation"] for d in catalog["items"] if d["phase"] != "校內甄選")
    # A later year cannot borrow these reference rules as a current workflow.
    later = client.get("/application-center/catalog", params={"school": "NCU", "target_school": p.school_name, "academic_year": "117"}).json()
    assert not later["workflow_found"]
    audit = get(client, "/partner-source-audit", needle)
    assert audit["fields"]["host_documents"]["current_applicability_status"] == "unconfirmed"
    assert "116" in json.dumps(p.student_summary_zh.model_dump(), ensure_ascii=False)
    life = get(client, "/destination-profile", needle)
    assert "116" in json.dumps(life, ensure_ascii=False)


def test_wsu_offer_payment_oshc_and_dynamic_published_calendar_keep_scope(client):
    w = get(client, "/application-workflow", "Western Sydney")
    docs = initial(w, "ncu-001")["document_requirements"]
    passport = next(d for d in docs if "護照" in d["name"])
    assert passport["conditional"] and "可取得" in passport["condition"]
    acceptance = next(s for s in w["steps"] if s["rule_id"] == "ncu-001-host-post-offer-acceptance")
    assert len(acceptance["document_requirements"]) == 3
    assert all(d["stage"] == "post_offer" for d in acceptance["document_requirements"])
    audit = get(client, "/partner-source-audit", "Western Sydney")
    assert "不是官方尚未公告" in audit["fields"]["study_period"]["note"]
    assert "cross-school" in audit["fields"]["courses"]["note"]
    assert "禁止cross-campus" in audit["fields"]["courses"]["note"]
    guide = next(s for s in audit["source_evidence"] if s["id"] == "ncu-001-p4-03e653da33")
    assert len(guide["pages"]) == 28 and not guide["content_status"]["all_pages_read"]
    assert not guide["pages"][2]["text"].strip()


def test_udem_birth_certificate_caq_forms_and_winter_no_rooms_are_separate(client):
    w = get(client, "/application-workflow", "Montreal")
    assert not any("出生" in d["name"] for d in initial(w, "ncu-102")["document_requirements"])
    birth = next(s for s in w["steps"] if s["rule_id"] == "ncu-102-host-post-offer-identity")
    assert len(birth["document_requirements"]) == 1
    assert birth["document_requirements"][0]["stage"] == "post_offer"
    caq = next(s for s in w["steps"] if s["rule_id"] == "ncu-102-host-post-offer-caq")
    assert len(caq["document_requirements"]) == 5 and all(d["conditional"] for d in caq["document_requirements"])
    consent = next(d for d in caq["document_requirements"] if "D10F" in d["name"])
    assert consent["official_form_verified"] and "optional" in consent["condition"]
    audit = get(client, "/partner-source-audit", "Montreal")
    assert "冬季交換沒有校內名額" in audit["fields"]["housing"]["note"]
    assert "教育冬季6/1" in audit["fields"]["host_deadline"]["note"]
    assert "C2" in audit["fields"]["language"]["note"]
    form = next(s for s in audit["source_evidence"] if s["id"] == "ncu-102-p4f-9690ed7a29")
    assert form["content_status"]["all_pages_read"] and "signature" in form["pages"][0]["text"]


def test_manitoba_document_body_year_beats_old_filename_and_opening_is_not_deadline(client):
    audit = get(client, "/partner-source-audit", "Manitoba")
    fact = next(s for s in audit["source_evidence"] if s["id"] == "ncu-101-p4a-38fdd699f9")
    assert "2026-27" in fact["url"] and "2027" in fact["pages"][0]["text"]
    assert len(fact["pages"]) == 5 and fact["content_status"]["all_pages_read"]
    assert "官方明确exactdates尚未定" in audit["fields"]["study_period"]["unresolved"]
    assert "opening" in audit["fields"]["housing"]["note"]
    assert "開放日而不是截止" in audit["fields"]["housing"]["note"]
    assert "UG" in audit["fields"]["language"]["note"] and "PG" in audit["fields"]["language"]["note"]
    assert "100" in audit["fields"]["language"]["note"]
    docs = initial(get(client, "/application-workflow", "Manitoba"), "ncu-101")["document_requirements"]
    letter = next(d for d in docs if "PG在學" in d["name"])
    assert letter["conditional"] and not letter.get("signatures")
    assert "officialletterhead" in letter["condition"]


def test_uf_immunization_and_j1_entry_records_do_not_enter_initial_application(client):
    w = get(client, "/application-workflow", "Florida")
    docs = initial(w, "ncu-104")["document_requirements"]
    assert not any("Immunization" in d["name"] or "I94" in d["name"] for d in docs)
    health = next(s for s in w["steps"] if s["rule_id"] == "ncu-104-host-post-offer-health")
    assert len(health["document_requirements"]) == 4
    assert health["document_requirements"][0]["official_form_verified"]
    arrival = next(s for s in w["steps"] if s["rule_id"] == "ncu-104-host-post-arrival-checkin")
    assert len(arrival["document_requirements"]) == 2
    assert all(d["stage"] == "post_offer" for d in arrival["document_requirements"])
    assert "入美後" in json.dumps(arrival, ensure_ascii=False)
    audit = get(client, "/partner-source-audit", "Florida")
    assert "J1" in audit["fields"]["visa"]["note"]
    assert "Fall2026" in audit["fields"]["insurance"]["note"] and "1301" in audit["fields"]["insurance"]["note"]


def test_nau_europe_b2_year_typo_paid_track_and_pre_post_entry_are_distinct(client):
    audit = get(client, "/partner-source-audit", "Northern Arizona")
    assert "Europe" in audit["fields"]["language"]["note"] and "2016" in audit["fields"]["language"]["note"]
    assert "20808" in audit["fields"]["cost"]["note"] and "39940" in audit["fields"]["cost"]["note"]
    assert "60%" in audit["fields"]["housing"]["note"]
    w = get(client, "/application-workflow", "Northern Arizona")
    before = next(s for s in w["steps"] if s["rule_id"] == "ncu-105-host-pre-arrival-checkin")
    after = next(s for s in w["steps"] if s["rule_id"] == "ncu-105-host-post-arrival-checkin")
    assert len(before["document_requirements"]) == len(after["document_requirements"]) == 3
    assert all(d["stage"] == "post_offer" for d in before["document_requirements"])
    assert all(d["stage"] == "post_offer" for d in after["document_requirements"])
    assert any("Statement" in d["name"] for d in after["document_requirements"])


def test_douglas_public_browser_raw_shell_closed_cycle_and_exchange_specific_health(client):
    audit = get(client, "/partner-source-audit", "Douglas")
    rendered = next(s for s in audit["source_evidence"] if s["id"] == "ncu-100-p4b-incoming10005")
    raw = next(s for s in audit["source_evidence"] if s["id"] == "ncu-100-p4h-2b439475c4")
    assert "Online application questionnaire" in rendered["pages"][0]["text"]
    assert "This program is not currently accepting applications" in rendered["pages"][0]["text"]
    assert "NOT covered" in rendered["pages"][0]["text"]
    assert rendered["sha256"] != raw["sha256"] and raw["pages"][0]["text"].strip() == "×"
    assert not rendered["content_status"]["all_pages_read"]
    assert "Unlimited在Fee-based Visiting" in audit["fields"]["eligibility"]["note"]
    assert "不收exchange tuition或studentfees" in audit["fields"]["tuition"]["note"]
    assert "豁免" in audit["fields"]["visa"]["note"]
    # Prevent a manual row-ID slip from attaching Canadian facts to the Bahamas.
    bahamas = get(client, "/partner-source-audit", "The Bahamas")
    assert not any(s["id"].startswith("ncu-100-p4") for s in bahamas["source_evidence"])


def test_fourth_pass_keeps_original_native_source_bytes_and_reading_counters_separate():
    records = json.loads(gzip.decompress((ROOT / "sources/ncu/2026-10-11/host-web-evidence.json.gz").read_bytes()))
    reviewed = {s["id"]: s for s in records if "-p4" in s["id"]}
    full = [s for s in reviewed.values() if s.get("reading_review", {}).get("full_document_read")]
    assert len(full) == 16 and all(s["format"] == "pdf" for s in full)
    assert all(s["reading_review"]["source_sha256"] == s["sha256"] for s in full)
    assert len(reviewed["ncu-001-p4-03e653da33"]["pages"]) == 28
    assert not reviewed["ncu-001-p4-03e653da33"]["reading_review"]["full_document_read"]
    assert all(s["row_ids"] == ["ncu-100"] for sid, s in reviewed.items() if sid.startswith("ncu-100-p4g-") or sid.startswith("ncu-100-p4h-") or sid.startswith("ncu-100-p4b-"))

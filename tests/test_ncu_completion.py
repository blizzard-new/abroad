"""NCU reference data reaches real interfaces without approving a later year."""
import gzip
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_student_view import build_ncu_student_dashboard
from exchange_info.ncu_completion import campus_location, campus_photo
from scripts.research_ncu_assets import identity_matches

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ncu"
SOURCE = ROOT / "sources/ncu/2026-10-11"


def school(english):
    return next(p for p in build_ncu_student_dashboard().partner_universities if english in p.school_name)


def test_registry_domain_cannot_substitute_for_school_country_and_campus_identity():
    spec = {"school_name": "龍谷大學 Ryukoku University", "country": "日本"}
    row = {"status": "active", "types": ["education"],
           "locations": [{"geonames_details": {"country_code": "JP"}}],
           "names": [{"value": "Ryukoku Junior College"}],
           "domains": ["ryukoku.ac.jp"]}
    assert not identity_matches(spec, row)
    row["names"] = [{"value": "Ryukoku University"}]
    assert identity_matches(spec, row)
    row["locations"][0]["geonames_details"]["country_code"] = "TW"
    assert not identity_matches(spec, row)
    row["locations"][0]["geonames_details"]["country_code"] = "JP"
    row["locations"].append(row["locations"][0])
    assert not identity_matches(spec, row)


def test_every_usable_photo_has_reviewed_original_bytes_attribution_and_licence():
    photos = json.loads((BUNDLE / "campus-assets.json").read_text())["photos"]
    reviews = json.loads((SOURCE / "campus-photo-reviews.json").read_text())["rows"]
    accepted = {r["sha256"]: r for r in reviews if r["review_status"] == "accepted_campus_reference"}
    assert len(photos) == len(accepted) == 125
    for photo in photos:
        content = ROOT / "src/exchange_info" / photo["image_url"].removeprefix("/")
        assert hashlib.sha256(content.read_bytes()).hexdigest() == photo["content_sha256"]
        reviewed = accepted[photo["content_sha256"]]
        assert (photo["school_name"], photo["country"]) == (reviewed["school_name"], reviewed["country"])
        assert photo["author"] and photo["license_url"] and photo["identity_source_url"]
        assert photo["image_page_url"].startswith("https://commons.wikimedia.org/wiki/File:")
        assert "116錄取校區仍待確認" in photo["caption_zh"]
    assert campus_photo(school("Niigata").school_name, "日本") is None
    assert campus_photo(school("Alicante").school_name, "臺灣") is None


def test_candidate_gps_is_private_until_campus_verification_and_country_stays_scoped():
    pending = school("Donghua")
    loc = campus_location(pending, None)
    assert loc.geocode_status == "needs_review" and loc.latitude is None and loc.longitude is None
    isit = school("ISIT,")
    loc = campus_location(isit, None)
    assert loc.geocode_status == "verified"
    assert loc.latitude == 48.810178 and loc.longitude == 2.333168
    assert "Arcueil" in loc.note
    assert campus_location(isit.model_copy(update={"country": "臺灣"}), None) is None


def test_home_host_and_program_restrictions_keep_their_source_scope(tmp_path):
    client = TestClient(create_app(tmp_path))
    uef = school("Eastern Finland")
    summary = uef.student_summary_zh
    assert "不要求語言測驗" in " ".join(summary.eligibility_points)
    assert "正式外語檢定" in " ".join(summary.application_steps)
    params = {"school": "NCU", "target_school": uef.school_name, "academic_year": "116"}
    catalog = client.get("/application-center/catalog", params=params).json()
    assert any("Learning Agreement" in d["name"] for d in catalog["items"])
    conditional = [d for d in catalog["items"] if "已完成學士" in d["name"]]
    assert len(conditional) == 1 and conditional[0]["conditional"]
    assert conditional[0]["applicability"]["status"] == "needs_confirmation"
    assert all(d["needs_confirmation"] and not d["download_available"] for d in conditional)
    ozu = school("Ozyegin")
    workflow = client.get("/application-workflow", params={"school": ozu.school_name, "home_school": "NCU"}).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-096-host-apply")
    later = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-096-host-post-offer-study-plan")
    assert not initial["document_requirements"]
    assert later["document_requirements"][0]["stage"] == "post_offer"
    assert "IELTS不接受" in " ".join(initial["details"])
    assert workflow["review_status"] == "pending_review"
    assert all(not s["deadline_reminder_eligible"] for s in workflow["steps"])


def test_original_year_conflicts_and_reading_limits_are_visible_in_source_audit(tmp_path):
    client = TestClient(create_app(tmp_path))
    sungshin = school("Sungshin")
    result = client.get("/partner-source-audit", params={"school": sungshin.school_name, "home_school": "NCU"})
    assert result.status_code == 200
    audit = result.json()
    assert "2026/5/21" in audit["fields"]["host_deadline"]["note"]
    assert "9／12" in audit["fields"]["courses"]["unresolved"]
    assert "6月／7月" in audit["fields"]["housing"]["unresolved"]
    source = next(s for s in audit["source_evidence"] if s["id"] == "ncu-152-follow-16597a9652")
    assert "May 21, 2026" in source["pages"][1]["text"]
    assert not source["content_status"]["all_pages_read"]
    assert source["reading_review"]["source_sha256"] == source["sha256"]
    assert audit["fields"]["host_deadline"]["current_applicability_status"] == "unconfirmed"


def test_api_dashboard_coverage_detail_and_life_agree_on_photos(tmp_path):
    client = TestClient(create_app(tmp_path))
    dashboard = client.get("/student-dashboard", params={"school": "NCU"}).json()
    assert sum(p["image_status"] == "verified" for p in dashboard["partner_universities"]) == 125
    assert sum(p["location"]["geocode_status"] == "verified" for p in dashboard["partner_universities"]) == 10
    assert all(p["location"]["latitude"] is None for p in dashboard["partner_universities"] if p["location"]["geocode_status"] != "verified")
    coverage = client.get("/coverage", params={"school": "NCU"}).json()
    assert sum(p["image_status"] == "verified" for p in coverage["partners"]) == 125
    partner = next(p for p in dashboard["partner_universities"] if "Alicante" in p["school_name"])
    photo = client.get(partner["image_url"])
    assert photo.status_code == 200 and photo.headers["content-type"] == "image/jpeg"
    profile = client.get("/destination-profile", params={"school": partner["school_name"], "home_school": "NCU"}).json()
    assert any(p["image_url"] == partner["image_url"].removeprefix("http://testserver") for p in profile["guide_photos"])
    assert "€60" in json.dumps(profile, ensure_ascii=False)
    original = build_ncu_student_dashboard().model_copy(update={"school_name": "國立臺灣大學"})
    from exchange_info.ncu_completion import attach_campus_photos
    assert attach_campus_photos(original) is original


def test_source_attempts_and_agreement_denominators_are_not_current_exchange_approval():
    audit = json.loads((SOURCE / "agreement-denominator-audit.json").read_text())
    assert audit["raw_agreement_count"] == 578 and len(audit["groups"]) == 331
    assert audit["published_summary_count"] == 329
    assert all(g["exchange_availability_status"] == "needs_scope_confirmation" for g in audit["groups"])
    sources = json.loads(gzip.decompress((SOURCE / "host-web-evidence.json.gz").read_bytes()))
    assert len(sources) == len({s["id"] for s in sources})
    for sid in ("ncu-170-site-20261011", "ncu-198-site-20261011"):
        assert next(s for s in sources if s["id"] == sid)["authority_kind"] == "discovery_rejected"
    all_audits = json.loads((BUNDLE / "field-audit.json").read_text())
    assert all(a["collection_attempts"] for a in all_audits)
    assert all(p.quota is None and p.availability_status == "agreement_only" for p in build_ncu_student_dashboard().partner_universities)


def test_2027_utbm_original_content_keeps_initial_and_arrival_documents_separate(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Belfort-")
    params = {"school": partner.school_name, "home_school": "NCU"}
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-035-host-apply")
    arrival = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-035-host-arrival-documents")
    assert len(initial["document_requirements"]) == 5
    assert any("出生證明" in d["name"] and d["conditional"] for d in initial["document_requirements"])
    assert not any("疫苗" in d["name"] for d in initial["document_requirements"])
    assert any("疫苗" in d["name"] for d in arrival["document_requirements"])
    assert all(not s["deadline_reminder_eligible"] for s in workflow["steps"])
    audit = client.get("/partner-source-audit", params=params).json()
    assert "2027/3/29" in audit["fields"]["host_deadline"]["note"]
    source = next(s for s in audit["source_evidence"] if s["id"] == "ncu-035-follow-889ca42b7d")
    assert "2025-2026.pdf" in source["url"]
    assert "Year 2027" in source["pages"][0]["text"]
    assert source["content_status"]["all_pages_read"]
    assert "1.5／2" in audit["fields"]["insurance"]["unresolved"]


def test_portal_prerequisite_does_not_complete_host_documents_and_utar_is_malaysian(tmp_path):
    client = TestClient(create_app(tmp_path))
    zhaw = school("Zurich University")
    audit = client.get("/partner-source-audit", params={"school": zhaw.school_name, "home_school": "NCU"}).json()
    assert audit["fields"]["host_documents"]["status"] == "missing"
    assert audit["fields"]["host_documents"]["reference_status"] == "reviewed_gap_only"
    assert "wk37／7" in audit["fields"]["study_period"]["unresolved"]
    utar = school("Tunku")
    assert utar.country == "馬來西亞" and utar.website == "https://utar.edu.my/"
    assert "ramonllull" not in utar.website
    evidence = json.loads((SOURCE / "edhec-legacy-image-rejection.json").read_text())
    assert evidence["review_status"] == "rejected_not_campus_photo"
    photo = campus_photo(school("EDHEC").school_name, "法國")
    assert photo["content_sha256"] != evidence["actual_local_sha256"]


def test_wurzburg_teacher_forms_and_non_erasmus_course_list_keep_home_test_separate(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Würzburg")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "Physics只建議" in audit["fields"]["language"]["note"]
    assert "Medicine德文B2" in audit["fields"]["language"]["note"]
    assert "中央home正式語檢" in audit["fields"]["language"]["note"]
    assert "押金須收到" in audit["fields"]["housing"]["note"]
    form = next(s for s in audit["source_evidence"] if s["id"] == "ncu-048-next-22fe2f5874")
    assert "not by the student" in form["pages"][0]["text"]
    assert form["content_status"]["all_pages_read"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-048-host-apply")
    assert len(initial["document_requirements"]) == 5
    assert any("預計課程" in d["name"] and d["conditional"] for d in initial["document_requirements"])
    assert not any("Letter of Admission" in d["name"] for d in initial["document_requirements"])
    later = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-048-host-enrolment-documents")
    assert "Letter of Admission" in later["document_requirements"][0]["name"]


def test_dhbw_lorrach_spring_year_old_guide_and_school_insurance_ambiguity(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Baden-Wuerttemberg")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "2026/11/30" in audit["fields"]["host_deadline"]["note"]
    assert "秋2027" in audit["fields"]["host_deadline"]["unresolved"]
    assert "Germanstatutory" in audit["fields"]["insurance"]["unresolved"]
    assert "Schengen" in audit["fields"]["visa"]["unresolved"]
    guide = next(s for s in audit["source_evidence"] if s["id"] == "ncu-047-extra-49050f7416")
    assert "2024-03-22" in guide["url"]
    assert "Edition September 2022" in guide["pages"][-1]["text"]
    assert guide["content_status"]["all_pages_read"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-047-host-apply")
    assert len(initial["document_requirements"]) == 8
    assert all(not s["deadline_reminder_eligible"] for s in workflow["steps"])


def test_thomas_more_full_initial_checklist_remains_missing_despite_later_la(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Thomas More")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert audit["fields"]["host_documents"]["status"] == "missing"
    assert audit["fields"]["host_documents"]["reference_status"] == "reviewed_gap_only"
    assert "不是先來先得" in audit["fields"]["housing"]["note"]
    assert "普通申請4/27–5/4不套exchange" in audit["fields"]["housing"]["note"]
    assert "5560" in audit["fields"]["cost"]["note"]
    assert "缺字" in audit["fields"]["visa"]["unresolved"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-056-host-apply")
    later = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-056-host-post-offer-learning-agreement")
    assert not initial["document_requirements"]
    assert later["document_requirements"][0]["stage"] == "post_offer"


def test_government_visa_documents_are_post_offer_and_do_not_enter_host_initial_checklist(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Würzburg")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    government = next(s for s in audit["source_evidence"] if s["id"] == "ncu-german-taipei-student-20261011")
    assert government["authority_kind"] == "government"
    assert "01.05.2026" in government["pages"][0]["text"]
    assert "Auslandsportal" in audit["fields"]["visa"]["note"]
    workflow = client.get("/application-workflow", params=params).json()
    visa = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-048-host-government-visa-preparation")
    assert len(visa["document_requirements"]) == 8
    assert all(d["stage"] == "post_offer" and d["conditional"] for d in visa["document_requirements"])
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-048-host-apply")
    assert not any("入學許可" in d["name"] or "992" in d["name"] for d in initial["document_requirements"])

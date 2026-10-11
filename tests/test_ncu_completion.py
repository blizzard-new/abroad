"""NCU reference data reaches real interfaces without approving a later year."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest
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


def test_all_ncu_catalogue_tracks_select_their_own_workflow():
    from exchange_info.application_rules import select_application_workflow
    from exchange_info.models import ApplicationRuleContext, UniversityApplicationWorkflow
    from exchange_info.storage import read_jsonl

    workflows = read_jsonl(BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow)
    for partner in build_ncu_student_dashboard().partner_universities:
        selected = select_application_workflow(workflows, ApplicationRuleContext(
            home_university="NCU", partner_university=partner.school_name, academic_year="116"))
        assert selected is not None
        assert selected.school_name == partner.school_name


@pytest.mark.parametrize("english", ["State University of New York Oswego", "University of Hawai'i at Manoa"])
def test_ncu_missing_self_funded_track_cannot_reuse_regular_or_reference_workflow(english):
    from exchange_info.application_rules import select_application_workflow, select_reference_workflow
    from exchange_info.models import ApplicationRuleContext, UniversityApplicationWorkflow
    from exchange_info.storage import read_jsonl

    workflows = read_jsonl(BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow)
    regular = school(english)
    paid = school(english + "（自費）")
    rows = [row.model_copy(update={"academic_year": "115", "review_status": "published"})
            for row in workflows if row.school_name in (regular.school_name, paid.school_name)]
    context = ApplicationRuleContext(home_university="國立中央大學", partner_university=paid.school_name)
    assert select_reference_workflow(rows, context).school_name == paid.school_name
    remaining = [row.model_copy(update={"academic_year": "116"})
                 for row in rows if row.school_name != paid.school_name]
    assert select_application_workflow(remaining, context) is None
    assert select_reference_workflow(remaining, context) is None


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


def test_em_normandie_new_incoming_pack_conflicts_and_hub_documents_keep_stages(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Normandie")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "4/30–5/15" in audit["fields"]["host_deadline"]["unresolved"]
    assert "4/15–4/30" in audit["fields"]["host_deadline"]["unresolved"]
    assert "3／4" in audit["fields"]["host_documents"]["unresolved"]
    assert "6000／4500AED" in audit["fields"]["visa"]["unresolved"]
    assert "語言課不計" in audit["fields"]["courses"]["note"]
    rejected = next(s for s in audit["collection_attempts"] if s["id"] == "ncu-009-site-20261011")
    assert rejected["authority_kind"] == "discovery_rejected"
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-009-host-apply")
    assert len(initial["document_requirements"]) == 4
    assert any("Learning Agreement" in d["name"] and d["conditional"] for d in initial["document_requirements"])
    hub = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-009-host-post-offer-hub-enrolment")
    assert len(hub["document_requirements"]) == 3
    assert all(d["stage"] == "post_offer" for d in hub["document_requirements"])
    assert "不用CVEC" in audit["fields"]["tuition"]["note"]
    assert all(not s["deadline_reminder_eligible"] for s in workflow["steps"])


def test_isit_degree_c1_does_not_become_exchange_and_insurance_conflict_is_preserved(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("ISIT,")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "MasterdegreeC1不可套exchange" in audit["fields"]["language"]["unresolved"]
    assert "recommended／required" in audit["fields"]["insurance"]["unresolved"]
    assert "2025/26" in audit["fields"]["host_deadline"]["note"]
    assert "2026/9/11" in audit["fields"]["study_period"]["note"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-019-host-apply")
    assert len(initial["document_requirements"]) == 5
    assert any("保險" in d["name"] for d in initial["document_requirements"])
    govt = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-019-host-government-france-taiwan-preparation")
    assert all(d["stage"] == "post_offer" and d["conditional"] for d in govt["document_requirements"])
    assert "電子列印" in govt["document_requirements"][1]["name"]
    assert not any("具名法國學校LOA" in d["name"] for d in initial["document_requirements"])


def test_rouen_portal_checklist_and_fee_remain_missing_with_a_later_pre_acceptance_la(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Rouen")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert audit["fields"]["host_documents"]["status"] == "missing"
    assert audit["fields"]["tuition"]["status"] == "missing"
    assert "stronglyrecommended" in audit["fields"]["language"]["note"]
    assert "RENTREE2024" in audit["fields"]["arrival"]["note"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-037-host-apply")
    later = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-037-host-post-initial-learning-agreement")
    assert not initial["document_requirements"]
    assert later["document_requirements"][0]["stage"] == "after_application"
    assert "外校LOA前" in later["timing"]


def test_hohenheim_exchange_fee_and_housing_deadline_are_not_general_degree_fees(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Hohenheim")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "只StudentServicesfee" in audit["fields"]["tuition"]["note"]
    assert "174.50" in audit["fields"]["tuition"]["note"]
    assert "7/15–12/15 vs6/30–1/15" in audit["fields"]["housing"]["unresolved"]
    assert "不要求提交語言證明" in audit["fields"]["language"]["note"]
    assert "October2022" in audit["fields"]["cost"]["note"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-049-host-apply")
    assert len(initial["document_requirements"]) == 6
    assert any("高中" in d["name"] for d in initial["document_requirements"])
    assert sum(d["conditional"] for d in initial["document_requirements"]) == 3
    assert not any("語言" in d["name"] for d in initial["document_requirements"])


def test_liege_unofficial_transcript_language_faculty_scope_and_calendar_wrong_year(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Liège")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "非正式成績也接受" in audit["fields"]["host_documents"]["note"]
    assert "HEC與Law至少B2" in audit["fields"]["language"]["note"]
    assert "推薦" not in audit["fields"]["language"]["note"]
    assert "冬考2026錯年" in audit["fields"]["study_period"]["unresolved"]
    assert "recommendation" in audit["fields"]["host_deadline"]["note"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-051-host-apply")
    assert len(initial["document_requirements"]) == 6
    assert any("非正式版" in d["name"] for d in initial["document_requirements"])
    original = next(s for s in audit["source_evidence"] if s["id"] == "ncu-051-pass2-9682b3e8cd")
    assert "2026" in original["pages"][0]["text"]


def test_cafoscari_overseas_relative_deadline_forms_year_and_course_restrictions(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Foscari")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "一個月" in audit["fields"]["host_deadline"]["note"]
    assert "12ECTS" in audit["fields"]["courses"]["note"]
    assert "Erasmus70%範圍套Overseas" in audit["fields"]["courses"]["note"]
    assert "不能只取一個" in audit["fields"]["courses"]["note"]
    guide = next(s for s in audit["source_evidence"] if s["id"] == "ncu-077-p2x-7a067016e3")
    assert "2025.pdf" in guide["url"] and "2026/2027" in guide["pages"][0]["text"]
    assert guide["content_status"]["all_pages_read"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-077-host-apply")
    assert len(initial["document_requirements"]) == 4
    later = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-077-host-arrival-permit-documents")
    assert len(later["document_requirements"]) == 7
    assert all(d["conditional"] and d["stage"] == "post_offer" for d in later["document_requirements"])
    catalog = client.get("/application-center/catalog", params={"school": "NCU", "target_school": partner.school_name, "academic_year": "116"}).json()
    forms = [d for d in catalog["items"] if "一頁空白表" in d["name"]]
    assert len(forms) == 1 and forms[0]["official_form_verified"]
    assert not forms[0]["download_available"] and forms[0]["needs_confirmation"]


def test_nord_b2_minimum_c1_recommendation_funding_year_and_placement_condition(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Nord University")
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "minimumB2" in audit["fields"]["language"]["note"]
    assert "recommendedC1" in audit["fields"]["language"]["note"]
    assert "提名視作B2confirmation" in audit["fields"]["language"]["note"]
    assert "Spring2026 NOK91014" in audit["fields"]["host_documents"]["note"]
    assert "HTTP403" in audit["fields"]["visa"]["unresolved"]
    assert "JS渲染" in audit["fields"]["housing"]["unresolved"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-082-host-apply")
    assert len(initial["document_requirements"]) == 5
    assert not any("犯罪" in d["name"] for d in initial["document_requirements"])
    later = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-082-host-placement-criminal-record")
    assert later["document_requirements"][0]["conditional"]
    assert not any(s["deadline_reminder_eligible"] for s in workflow["steps"])


def test_centrale_current_identity_and_five_documents_do_not_invent_language_score(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = school("Centrale Marseile")
    assert partner.website == "https://www.centrale-mediterranee.fr/"
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "沒有公開統一CEFR" in audit["fields"]["language"]["note"]
    assert "S8" in audit["fields"]["eligibility"]["note"]
    assert "Marseille／Nice" in audit["fields"]["city"]["unresolved"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-006-host-apply")
    assert len(initial["document_requirements"]) == 5
    assert all(d["stage"] == "student_application" for d in initial["document_requirements"])
    assert not any("語言" in d["name"] or "LOA" in d["name"] for d in initial["document_requirements"])
    assert all(not s["deadline_reminder_eligible"] for s in workflow["steps"])


@pytest.mark.parametrize("rid,english", [
    ("ncu-106", "State University of New York Oswego"),
    ("ncu-108", "State University of New York Oswego（自費）"),
])
def test_oswego_track_fee_language_conflicts_and_download_denial_are_preserved(tmp_path, rid, english):
    partner = school(english)
    client = TestClient(create_app(tmp_path))
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "Cambridge B2／C1" in audit["fields"]["language"]["unresolved"]
    assert "free tuition與fee-paying" in audit["fields"]["tuition"]["note"]
    assert "到校才付款" in audit["fields"]["tuition"]["note"]
    assert "earlyJanuary" in audit["fields"]["tuition"]["note"]
    assert "10個月" in audit["fields"]["housing"]["note"]
    assert "2027/28" in audit["fields"]["study_period"]["note"]
    denied = next(s for s in audit["source_evidence"] if s["id"] == "ncu-106-p3x-official-facts")
    assert "owner hasn't given you permission" in denied["pages"][0]["text"]
    assert not denied["content_status"]["all_pages_read"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == rid + "-host-apply")
    assert workflow["school_name"] == partner.school_name
    later = next(s for s in workflow["steps"] if s["rule_id"] == rid + "-host-post-offer-us-visa")
    assert len(initial["document_requirements"]) == 4
    assert not any("DS160" in d["name"] for d in initial["document_requirements"])
    assert all(d["conditional"] and d["stage"] == "post_offer" for d in later["document_requirements"])
    assert partner.quota is None and partner.availability_status == "agreement_only"
    assert not any(s["deadline_reminder_eligible"] for s in workflow["steps"])


@pytest.mark.parametrize("rid,english", [
    ("ncu-107", "University of Hawai'i at Manoa"),
    ("ncu-113", "University of Hawai'i at Manoa（自費）"),
])
def test_hawaii_postgraduate_official_documents_f1_and_visiting_fees_keep_scope(tmp_path, rid, english):
    partner = school(english)
    client = TestClient(create_app(tmp_path))
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "中央115免學費項限研究生" in audit["fields"]["eligibility"]["note"]
    assert "免ELIPT門檻" in audit["fields"]["language"]["note"]
    assert "3.5" in audit["fields"]["language"]["note"]
    assert "records office" in audit["fields"]["host_documents"]["note"]
    assert "不能refund" in audit["fields"]["tuition"]["note"]
    assert "先繳後" in audit["fields"]["tuition"]["note"]
    assert "22216" in audit["fields"]["cost"]["note"]
    assert "27340" in audit["fields"]["cost"]["note"]
    assert "舊J1與新F1" in audit["fields"]["visa"]["unresolved"]
    fact = next(s for s in audit["source_evidence"] if s["id"] == "ncu-107-p3x-157177aad0")
    assert fact["content_status"]["all_pages_read"]
    insurance = next(s for s in audit["source_evidence"] if s["id"] == "ncu-107-p3x-e119748df4")
    assert [p["text"] for p in insurance["pages"]][1:] == ["", ""]
    assert insurance["content_status"]["all_pages_read"]
    assert insurance["content_status"]["visual_reviewed_page_count"] == 3
    assert not insurance["content_status"]["all_pages_have_text"]
    assert "校方這兩方案免下半" in audit["fields"]["insurance"]["note"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == rid + "-host-apply")
    assert workflow["school_name"] == partner.school_name
    health = next(s for s in workflow["steps"] if s["rule_id"] == rid + "-host-post-offer-health-clearance")
    assert len(health["document_requirements"]) == 3
    acknowledgement = next(d for d in health["document_requirements"] if "StudentAcknowledgment" in d["name"])
    provider = next(d for d in health["document_requirements"] if "InsuranceProviderCertification" in d["name"])
    assert "也須學生確認" in acknowledgement["condition"]
    assert "可免保險公司欄" in provider["condition"]
    assert len(initial["document_requirements"]) == 10
    assert any("學士文憑" in d["name"] for d in initial["document_requirements"])
    assert any("商管修課" in d["name"] and d["conditional"] for d in initial["document_requirements"])
    assert not any("InsuranceProvider" in d["name"] for d in initial["document_requirements"])
    catalog = client.get("/application-center/catalog", params={"school": "NCU", "target_school": partner.school_name, "academic_year": "116"}).json()
    forms = [d for d in catalog["items"] if "Financial Certification" in d["name"]]
    assert len(forms) == 1 and forms[0]["official_form_verified"]
    assert forms[0]["needs_confirmation"] and not forms[0]["download_available"]


def test_visp_funding_can_follow_admission_and_2026_ship_is_not_116(tmp_path):
    partner = school("Wisconsin-Madison")
    client = TestClient(create_app(tmp_path))
    params = {"school": partner.school_name, "home_school": "NCU"}
    audit = client.get("/partner-source-audit", params=params).json()
    assert "6mo" in audit["fields"]["cost"]["note"]
    assert "38446" in audit["fields"]["cost"]["note"]
    assert "已過openenrollment" in audit["fields"]["insurance"]["note"]
    assert "fall655" in audit["fields"]["insurance"]["note"]
    assert "私保不合格" in audit["fields"]["insurance"]["note"]
    assert "2024" in audit["fields"]["visa"]["unresolved"] or "2024" in audit["fields"]["visa"]["note"]
    workflow = client.get("/application-workflow", params=params).json()
    initial = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-114-host-apply")
    funding = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-114-host-post-offer-financial-i20")
    assert len(funding["document_requirements"]) == 5
    assert any("Financial Verification Form" in d["name"] for d in funding["document_requirements"])
    assert any("Personal Information Verification" in d["name"] for d in funding["document_requirements"])
    guide = next(s for s in audit["source_evidence"] if s["id"] == "ncu-114-p3y-291fb67291")
    assert guide["content_status"]["all_pages_read"]
    assert guide["content_status"]["visual_reviewed_page_count"] == 9
    assert "12/31/2024" in audit["fields"]["visa"]["note"]
    assert len(initial["document_requirements"]) == 4
    assert not any("財力文件" in d["name"] or "Affidavit" in d["name"] for d in initial["document_requirements"])
    assert "可初次交或錄取後補" in funding["timing"]
    assert all(d["conditional"] and d["stage"] == "post_offer" for d in funding["document_requirements"])
    assert workflow["review_status"] == "pending_review"
    assert not any(s["deadline_reminder_eligible"] for s in workflow["steps"])

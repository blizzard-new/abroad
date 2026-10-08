"""CCU public templates, incompatible versions, and scoped course constraints."""

import hashlib
import json

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents, verified_form_urls
from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_profile import reviewed_profiles
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def read(name):
    return json.loads((BUNDLE / name).read_text())


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_public_dorm_templates_have_real_signers_without_a_current_template_claim():
    requirements = reviewed_documents()[47]["requirements"]
    for index, signers in [(7, ["學生"]), (8, ["學生", "Clinician"])]:
        item = requirements[index]
        assert item["conditional"]
        assert all(any(s in value for value in item["requirement"]["signatures"]) for s in signers)
        assert item["requirement"]["official_form_url"] in verified_form_urls()
        assert "未" in item["applicability_note"]
        template = next(e for e in item["evidence"] if e["source_url"] == item["requirement"]["official_form_url"])
        source = read("overseas_sources/" + template["source_id"] + ".json")
        assert source["content_applicability"] == "needs_confirmation"
        assert template["source_pages"] == [1]
        assert hashlib.sha256((BUNDLE / source["bundled_file"]).read_bytes()).hexdigest() == source["sha256"]
    health = requirements[8]
    assert health["stage"] == "after_dorm_assignment"
    assert "Global未明示可用skin" in health["condition"]
    assert reviewed_rows()[47]["fields"]["arrival"]["status"] == "explicit_not_announced"


def test_hufs_programme_confirmation_is_later_and_conditional():
    item = next(r for r in reviewed_documents()[47]["requirements"] if "Google Form" in r["requirement"]["name"])
    assert item["stage"] == "after_application" and item["conditional"]
    assert item["applicability_status"] == "needs_confirmation"
    assert item["requirement"]["official_form_url"] is None
    assert "finalized" in item["evidence"][0]["excerpt"]
    housing = reviewed_rows()[47]["fields"]["housing"]
    assert housing["status"] == "conflict"
    assert "約2月" in housing["value"] and "約1月" in housing["value"]
    assert "Flywire" in housing["value"]


def test_dit_new_publication_does_not_merge_regular_degree_and_exchange_lists():
    row = reviewed_rows()[101]["fields"]
    assert row["documents"]["status"] == "conflict"
    assert "exam grade sheet" in row["documents"]["value"]
    assert "passport photos" in row["documents"]["value"]
    assert "regular degree" in row["application_deadline"]["value"]
    assert "12/1" in row["application_deadline"]["value"]
    extra = reviewed_documents()[101]["requirements"][-1]
    assert extra["conditional"] and extra["applicability_status"] == "needs_confirmation"
    assert "transcript" in extra["condition"]
    assert extra["evidence"][0]["source_pages"] == [44]
    source = read("overseas_sources/p101-r20-1e8ffcbb39.json")
    assert "09.2026" in source["text_pages"][43]
    assert source["content_applicability"] == "needs_confirmation"
    assert "免service fee" in row["host_tuition"]["value"]
    assert "不能自行豁免" in row["host_tuition"]["value"]


def test_colabs_actual_spring_2027_calendar_is_not_an_all_programme_calendar():
    field = reviewed_rows()[35]["fields"]["academic_calendar"]
    assert field["status"] == "verified_current"
    assert "4/8" in field["value"] and "8/4–6" in field["value"]
    assert "Early April 2027" in field["value"]
    evidence = next(e for e in field["evidence"] if e["source_id"] == read("twentieth-source-review.json")["aliases"]["p35-r20-c79604cd51"] and "Spring Semester 2027" in e["excerpt"])
    assert "Spring Semester 2027" in evidence["excerpt"]
    assert "April 8 , 2027" in evidence["excerpt"]
    old = read("overseas_sources/p35-r20-a3ce996a54.json")
    assert old["content_applicability"] == "reference_only"
    assert "2022" in old["content_academic_year"]


def test_pardubice_recommendation_and_faculty_percentage_are_distinct():
    value = reviewed_rows()[107]["fields"]["course_restrictions"]["value"]
    assert "建議" in value and "硬性4門門檻" in value
    assert "至少80%" in value and "教授可退課" in value
    assert at(107).quota_status == "not_published"
    degree = reviewed_profiles()[107]["fields"]["degree_levels"]
    assert degree["status"] == "needs_confirmation" and "doctoral" in degree["value"]


def test_zhaw_degree_specific_requirements_do_not_promote_the_undated_year():
    fields = reviewed_rows()[103]["fields"]
    assert fields["language"]["status"] == "needs_confirmation"
    assert "BA English/German B2" in fields["language"]["value"]
    assert "Master English C1" in fields["language"]["value"]
    assert "4sems" in fields["eligibility"]["value"]
    assert "1homeMAsem" in fields["eligibility"]["value"]
    old_housing = read("overseas_sources/p103-r20-9c1db278ea.json")
    assert old_housing["content_applicability"] == "reference_only"
    assert "2021" in old_housing["content_academic_year"]


def test_hiof_2027_autumn_course_is_not_spring_opening_or_admission_degree():
    fields = reviewed_rows()[114]["fields"]
    assert fields["course_restrictions"]["status"] == "needs_confirmation"
    assert "Autumn2027" in fields["course_restrictions"]["value"]
    assert "最低人數" in fields["course_restrictions"]["value"]
    profiles = reviewed_profiles()[114]["fields"]
    assert profiles["degree_levels"]["status"] == "needs_confirmation"
    assert "任教school years非申請年級" in profiles["degree_levels"]["value"]
    assert "Fredrikstad" in profiles["colleges"]["value"] and "Halden" in profiles["colleges"]["value"]


def test_seoultech_2022_visa_bank_amount_never_replaces_2027_admission_amount():
    requirements = reviewed_documents()[48]["requirements"]
    bank = next(r for r in requirements if r["stage"] == "second_submission" and "銀行" in r["requirement"]["name"])
    assert "6000" in bank["requirement"]["name"].replace(",", "")
    old = read("overseas_sources/p48-r20-e409bc2ef0.json")
    assert old["content_applicability"] == "reference_only" and "2022" in old["content_academic_year"]
    assert "不同階段" in reviewed_rows()[48]["fields"]["visa"]["value"]


def test_twentieth_ledger_is_acquisition_proof_without_source_exhaustion():
    report = read("twentieth-source-review.json")
    assert report["acquisition_count"] == len(report["source_reviews"]) == 125
    assert report["new_source_count"] == 95
    assert len(report["unrelated_sources_excluded_from_registry"]) == 27
    assert len(report["same_url_rechecks"]) == 2
    for item in report["same_url_rechecks"]:
        assert item["same_extracted_text"] and item["final_url"]
    assert all(not r["public_sources_exhausted"] for r in read("remaining-gaps.json")["schools"])


def test_document_center_has_actual_downloads_and_uncertainty_notes(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-center/catalog", params={"school": HOME, "target_school": at(47).school_name})
    assert response.status_code == 200
    items = response.json()["items"]
    for needle, source_id in [("宿舍申請表", "1xThdiWsgT4IZ5Tco7UZnpUGFDA16Hknf"), ("健康／TB", "1NwoAHiWT7p3yJO1s-YqyhZCSRN0YQiBy")]:
        item = next(r for r in items if needle in r["name"])
        assert item["download_available"] and item["official_form_verified"]
        assert source_id in item["official_form_url"]
        assert "未" in item["applicability_note"]
    later = next(r for r in items if "Google Form" in r["name"])
    assert later["stage"] == "after_application" and later["conditional"]
    assert not later["download_available"]

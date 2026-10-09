"""Delivery evidence, current follow-up stages and scoped public forms."""

import hashlib
import json

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents
from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import (
    build_ccu_workflow,
    fetch_ccu_partner_universities,
)
from exchange_info.models import ApplicationSubmissionDetails
from exchange_info.workflow_structuring import structure_application_workflow


def read(name):
    return json.loads((BUNDLE / name).read_text())


def partner(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def flow(client, page):
    response = client.get("/application-workflow", params={"home_school": HOME, "school": partner(page).school_name})
    assert response.status_code == 200, response.text
    return response.json()


def test_notification_email_does_not_establish_later_housing_delivery(tmp_path):
    client = TestClient(create_app(tmp_path))
    for page in [32, 89, 104]:
        result = flow(client, page)
        life = next(s for s in result["steps"] if s["phase"] == "合作校行前與生活")
        assert life["submission"]["method"] == "unknown"
        assert result["steps"][1]["submission"]["method"] == "online"
        assert result["steps"][2]["submission"]["method"] == "paper"


def test_explicit_verified_host_life_method_is_preserved():
    workflow = build_ccu_workflow(partner(32))
    life = next(s for s in workflow.steps if s.phase == "合作校行前與生活")
    life.submission = ApplicationSubmissionDetails(method="email", email="verified@example.invalid")
    result = structure_application_workflow(workflow)
    life = next(s for s in result.steps if s.phase == "合作校行前與生活")
    assert life.submission.method == "email" and life.submission.email == "verified@example.invalid"


def test_notification_guard_does_not_change_other_home_inference():
    workflow = build_ccu_workflow(partner(32))
    workflow.home_university = "長庚大學"
    life = next(s for s in workflow.steps if s.phase == "合作校行前與生活")
    life.summary, life.details = "email notification", []
    life.submission = ApplicationSubmissionDetails()
    result = structure_application_workflow(workflow)
    assert next(s for s in result.steps if s.phase == "合作校行前與生活").submission.method == "email"


def test_khu_google_form_is_neutral_followup_with_conditional_physical_copies(tmp_path):
    client = TestClient(create_app(tmp_path))
    result = flow(client, 45)
    second = next(s for s in result["steps"] if s["phase"] == "合作校第二次文件送件")
    assert "未明示須等錄取" in second["summary"] and "TBA" in second["timing"]
    assert second["submission"]["method"] == "mixed"
    assert "非OECD" in second["submission"]["office"]
    assert second["submission"]["portal_url"] is None
    assert all(r["stage"] == "second_submission" for r in second["document_requirements"])
    assert any("銀行" in r["name"] for r in second["document_requirements"])
    assert result["steps"][4]["submission"]["method"] == "mixed"
    assert "2027春季factsheet" not in second["summary"]


def test_khu_current_dorm_tests_do_not_invent_a_three_month_universal_window():
    items = reviewed_documents()[45]["requirements"]
    tests = [r for r in items if r["stage"] == "after_dorm_assignment"]
    assert len(tests) == 2 and all(r["conditional"] for r in tests)
    assert all(r["applicability_status"] == "verified_current" for r in tests)
    assert all(r["evidence"][0]["source_pages"] == [3] for r in tests)
    assert all("TBA" in r["condition"] for r in tests)
    relationship = next(r for r in items if "亲属关系" in r["requirement"]["name"])
    assert relationship["conditional"] and relationship["stage"] == "second_submission"
    assert "父母账户" in relationship["condition"]


def test_khu_unyear_prices_keep_actual_source_conflicts():
    fields = reviewed_rows()[45]["fields"]
    assert all(fields[k]["status"] == "conflict" for k in ["housing", "costs", "insurance"])
    assert "1330000" in fields["housing"]["value"] and "1290000" in fields["housing"]["value"]
    assert "72000" in fields["insurance"]["value"] and "80000" in fields["insurance"]["value"]
    assert fields["eligibility"]["status"] == "verified_current"


def test_epita_degree_certificate_difference_and_signed_la_remain_pending():
    items = reviewed_documents()[86]["requirements"]
    extra = next(r for r in items if "degree certificates" in r["requirement"]["name"])
    assert extra["conditional"] and extra["applicability_status"] == "needs_confirmation"
    assert "2026–2027factsheet七项未列" in extra["condition"]
    la = next(r for r in items if "Learning Agreement" in r["requirement"]["name"])
    assert la["stage"] == "post_offer" and la["requirement"]["signatures"] == ["学生", "母校", "EPITA"]
    assert la["requirement"]["official_form_url"] is None
    assert items[6]["conditional"] and items[6]["evidence"][0]["source_id"] == "p86-mirror"
    assert "International health insurance --> optional" in read("overseas_sources/p86-mirror.json")["text_pages"][1]
    assert reviewed_rows()[86]["fields"]["documents"]["status"] == "conflict"


def test_jena_later_public_forms_have_real_signatures_and_conditional_scope(tmp_path):
    items = reviewed_documents()[99]["requirements"]
    assert len(items) == 3 and all(r["conditional"] and r["stage"] == "post_offer" for r in items)
    extension = next(r for r in items if "双方确认" in r["requirement"]["name"])
    assert extension["requirement"]["signatures"] == ["学生", "母校International Office", "Jena International Office"]
    assert extension["requirement"]["stamps"] == ["母校International Office", "Jena International Office"]
    assert extension["evidence"][0]["source_pages"] == []
    client = TestClient(create_app(tmp_path))
    data = client.get("/application-center/catalog", params={"school": HOME, "target_school": partner(99).school_name}).json()
    forms = [r for r in data["items"] if r.get("stage") == "post_offer"]
    assert len(forms) == 3 and all(r["download_available"] for r in forms)
    assert all(r["official_form_verified"] and r["applicability_status"] == "needs_confirmation" for r in forms)


def test_dit_exchange_exemption_is_supported_by_the_complete_statute_chain():
    original = read("overseas_sources/p101-r22-9a1b533095.json")
    first = read("overseas_sources/p101-r22-132b72bc51.json")
    second = read("overseas_sources/p101-r22-7f290ae53e.json")
    assert "Für Austauschstudierende werden keine Gebühren erhoben" in original["text_pages"][3]
    assert "§ 9 Abs. 2 und 3" in first["text_pages"][0]
    assert "§ 2 wird neu gefasst" in second["text_pages"][0]
    assert "§ 4 Satz 1" in second["text_pages"][0]
    assert "§ 6" not in " ".join(first["text_pages"] + second["text_pages"])
    cost = reviewed_rows()[101]["fields"]["costs"]
    assert cost["status"] == "conflict" and "StudentUnion82/87" in cost["value"]
    assert "全部零费" in cost["value"]


def test_ryukoku_agreement_quota_is_separate_from_current_open_quota():
    source = read("overseas_sources/p32-r22-0c77fdf035.json")
    assert "実際の派遣人数とは必ずしも同じではありません" in source["text_pages"][0]
    assert "国立中正大学\n1\n1\n2016.12.13" in source["text_pages"][0]
    assert source["content_applicability"] == "needs_confirmation"
    assert partner(32).quota_status == "published"


def test_48_acquisitions_and_prior_919_sources_are_accounted_for():
    report = read("twentysecond-source-review.json")
    assert report["acquisition_count"] == len(report["source_reviews"]) == 48
    assert report["new_source_count"] == 24 and len(report["same_body_rechecks"]) == 3
    assert len(report["prior_snapshot_hashes"]) == 919
    for sid, expected in report["prior_snapshot_hashes"].items():
        assert hashlib.sha256((BUNDLE / "overseas_sources" / (sid + ".json")).read_bytes()).hexdigest() == expected
    source = read("overseas_sources/p99-r22-d1d0ea185f.json")
    assert "antiword" in source["extraction_method"] and "physical pagination not verified" in source["extraction_page_semantics"]
    assert hashlib.sha256((BUNDLE / source["bundled_file"]).read_bytes()).hexdigest() == source["sha256"]


def test_link_scope_screening_never_claims_to_have_read_optional_target_bodies():
    report = read("twentysecond-link-scope-screening.json")
    assert report["scope_screened"] == len(report["reviews"]) == 171
    assert not report["source_content_read"] and not report["public_sources_exhausted"]
    for r in report["reviews"]:
        assert not r["source_content_read"] and r["review_extent"] == "link_scope_screening_only"
        assert r["discovery_evidence"]
        for ev in r["discovery_evidence"]:
            parent = read("overseas_sources/" + ev["source_id"] + ".json")
            assert parent["sha256"] == ev["parent_content_hash"]
    labs = [r for r in report["reviews"] if r["disposition"] == "deferred_optional_exchange_project"]
    assert len(labs) == 30 and all("真正可选exchange" in r["review_note"] for r in labs)

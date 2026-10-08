"""Real CCU rows: uncertain scopes, staged documents and readable official links."""

import pytest
from fastapi.testclient import TestClient
from test_ccu_semantics import client_for

from exchange_info.api import create_app
from exchange_info.ccu_student_view import fetch_ccu_partner_universities

HOME = "國立中正大學"


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


@pytest.mark.parametrize("page", [104, 37])
@pytest.mark.parametrize(
    "college,degree", [("管理學院", "大學部"), ("工學院", "博士班")]
)
def test_real_pending_scopes_neither_pass_nor_block_in_both_apis(
    tmp_path, page, college, degree
):
    client = client_for(tmp_path)
    common = {
        "college": college,
        "degree_level": degree,
        "academic_gpa": 3.5,
        "academic_score": 85,
    }
    result = client.post(
        "/advisor/plan",
        json=dict(school_name=HOME, target_school=at(page).school_name, **common),
    )
    assert result.status_code == 200, result.text
    target = result.json()["target_match"]
    assert not target["blocking_reasons"]
    assert not {"符合學院範圍", "符合目前學制"} & set(target["reasons"])
    assert any("學院範圍" in r for r in target["confirmation_items"])
    assert any("學制範圍" in r for r in target["confirmation_items"])
    result = client.post(
        "/application-plan/evaluate",
        json=dict(
            home_school=HOME,
            preferences=[{"rank": 1, "school_name": at(page).school_name}],
            **common,
        ),
    )
    assert result.status_code == 200, result.text
    checks = {r["code"]: r for r in result.json()["choices"][0]["checks"]}
    assert (
        checks["college"]["status"]
        == checks["degree_level"]["status"]
        == "needs_confirmation"
    )


def test_cnu_after_application_deadlines_and_post_offer_project_separately(tmp_path):
    client = TestClient(create_app(tmp_path))
    flow = client.get(
        "/application-workflow",
        params={"home_school": HOME, "school": at(53).school_name},
    ).json()
    assert flow["review_status"] == "legacy"
    after = next(
        s for s in flow["steps"] if s["phase"] == "合作校申請後補件（不等錄取）"
    )
    assert "2026-12-20" in after["timing"] and "2027-01-15" in after["timing"]
    assert "錄取信12月底" in after["timing"]
    assert len(after["document_requirements"]) == 2
    assert all(
        r["stage"] == "after_application" and r["copy_type"] == "original"
        for r in after["document_requirements"]
    )
    catalog = client.get(
        "/application-center/catalog",
        params={"school": HOME, "target_school": at(53).school_name},
    ).json()
    later = [r for r in catalog["items"] if r["stage"] == "after_application"]
    assert len(later) == 2 and all("不等錄取" in r["phase"] for r in later)
    assert all("12/20" in r["name"] and "1/15" in r["name"] for r in later)
    offered = [r for r in catalog["items"] if r["stage"] == "post_offer"]
    assert len(offered) == 3 and all("錄取後" in r["phase"] for r in offered)
    assert not any("銀行" in r["name"] or "認證在學" in r["name"] for r in offered)


def test_hufs_general_essay_has_no_page_minimum_and_program_condition_survives(
    tmp_path,
):
    client = TestClient(create_app(tmp_path))
    catalog = client.get(
        "/application-center/catalog",
        params={"school": HOME, "target_school": at(47).school_name},
    ).json()
    general = next(r for r in catalog["items"] if "brief essay" in r["name"])
    intensive = next(r for r in catalog["items"] if "Intensive Korean" in r["name"])
    assert "未載最少頁數" in general["name"] and not general["conditional"]
    assert "至少1頁" in intensive["name"] and intensive["conditional"]
    assert "Intensive Korean" in intensive["condition"]
    assert (
        next(r for r in catalog["items"] if "財力表" in r["name"])["stage"]
        == "after_application"
    )
    health = next(r for r in catalog["items"] if "健康／TB" in r["name"])
    assert health["conditional"] and health["stage"] == "after_dorm_assignment"
    assert "宿舍成功申請者" in health["condition"]
    assert (
        "brief essay（未載最少頁數）"
        in at(47).partner_exchange_details["documents"].value
    )


def test_ryukoku_template_links_and_institutional_stamp_do_not_publish_workflow(
    tmp_path,
):
    client = TestClient(create_app(tmp_path))
    catalog = client.get(
        "/application-center/catalog",
        params={"school": HOME, "target_school": at(32).school_name},
    ).json()
    plan = next(r for r in catalog["items"] if r["name"] == "學習計畫指定表")
    assert plan["official_form_url"].endswith("/01_plan_of_Study_w.docx")
    assert (
        plan["official_form_verified"]
        and plan["download_available"]
        and plan["needs_confirmation"]
    )
    evaluation = next(r for r in catalog["items"] if r["name"] == "語言評估指定表")
    assert any("institutional stamp" in s for s in evaluation["stamps"])
    assert catalog["workflow_review_status"] == "legacy"
    assert all(r["needs_confirmation"] for r in catalog["items"])


def test_new_document_metadata_preserves_existing_hashes_and_binds_stage_changes():
    import json
    from pathlib import Path

    from exchange_info.content_governance import workflow_content_hash
    from exchange_info.storage import load_bundled_application_workflows

    proof = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs/ccu-validation-2026-10-08/parent-fix-content-hash-compatibility.json"
        ).read_text()
    )
    rows = load_bundled_application_workflows()
    for case in proof["cases"]:
        row = next(
            r
            for r in rows
            if r.home_university == case["home_university"]
            and r.school_name == case["school_name"]
            and r.academic_year == case["academic_year"]
        )
        assert workflow_content_hash(row) == case["sha256"]
    ccu = next(
        r
        for r in rows
        if r.home_university == HOME and r.school_name == at(32).school_name
    )
    changed = ccu.model_copy(deep=True)
    changed.steps[4].document_requirements[0].stage = "post_offer"
    assert workflow_content_hash(changed) != workflow_content_hash(ccu)

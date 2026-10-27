from __future__ import annotations

import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_study_plan_workbench_endpoint_returns_nccu_anti_pitfall_and_six_step_guide() -> None:
    client = TestClient(create_app())

    response = client.get("/application-center/study-plan-workbench", params={"school": "nccu"})
    assert response.status_code == 200
    payload = response.json()

    assert payload["school_id"] == "nccu"
    assert payload["school_name"] == "國立政治大學"
    assert payload["in_next_10_weeks_window"] is True
    assert payload["workbench_url"] == "/?school=nccu#application-form=study-plan"
    assert payload["max_a4_pages_hint"] == 2.0
    assert "20%" in payload["scoring_weight_headline"]
    assert "超出 2 頁不予計分" in payload["official_study_plan_limit_text"]
    assert payload["source_url"].startswith("https://")

    pitfall_titles = " ".join(rule["pitfall_title"] for rule in payload["pitfalls"])
    pitfall_details = " ".join(rule["detail_zh"] for rule in payload["pitfalls"])
    assert "超出 2 頁之內容不予計分" in pitfall_titles or "超出 2 頁之內容不予計分" in pitfall_details
    assert "交換計畫書" in pitfall_details
    assert "履歷表" in pitfall_details

    assert len(payload["six_step_guide"]) == 6
    assert [step["step_number"] for step in payload["six_step_guide"]] == [1, 2, 3, 4, 5, 6]
    assert "Dcard 政治大學板" in payload["dcard_launch_draft"]["dcard_board_name"]
    assert "超出 2 頁之內容不予計分" in payload["dcard_launch_draft"]["markdown_body"]
    assert "/?school=nccu#application-form=study-plan" in payload["dcard_launch_draft"]["markdown_body"]


def test_study_plan_workbench_endpoint_covers_ncku_and_ntust_hardcore_rules() -> None:
    client = TestClient(create_app())

    ncku_resp = client.get("/application-center/study-plan-workbench", params={"school": "ncku"})
    assert ncku_resp.status_code == 200
    ncku = ncku_resp.json()
    assert ncku["school_id"] == "ncku"
    assert "50%" in ncku["scoring_weight_headline"]
    ncku_text = " ".join(rule["pitfall_title"] + " " + rule["detail_zh"] for rule in ncku["pitfalls"])
    assert "第一志願" in ncku_text
    assert "中英雙語" in ncku_text or "中、英文" in ncku_text
    assert "50MB" in ncku_text

    ntust_resp = client.get("/application-center/study-plan-workbench", params={"school": "ntust"})
    assert ntust_resp.status_code == 200
    ntust = ntust_resp.json()
    assert ntust["school_id"] == "ntust"
    assert "0%" in ntust["scoring_weight_headline"]
    assert "60%" in ntust["scoring_weight_headline"]
    ntust_text = " ".join(rule["pitfall_title"] + " " + rule["detail_zh"] for rule in ntust["pitfalls"])
    assert "60%" in ntust_text
    assert "1–2 頁" in ntust_text or "1–2頁" in ntust_text


def test_study_plan_workbench_partner_course_lookup_links_to_cross_school_partner_page() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/application-center/study-plan-workbench",
        params={"school": "ncku", "target_partner": "慕尼黑工業大學"},
    )
    assert response.status_code == 200
    payload = response.json()

    partner = payload["selected_partner_lookup"]
    assert partner is not None
    assert partner["cross_school_partner_path"] == "/partners/germany/technical-university-of-munich?home=ncku"
    assert partner["course_direction_points"]
    assert partner["suggested_course_plan_lines"]
    assert any("慕尼黑工業大學" in line or "TUM" in line for line in partner["suggested_course_plan_lines"])


def test_study_plan_workbench_catalog_tracks_10_week_window_and_all_supported_universities() -> None:
    from exchange_info.university_registry import SUPPORTED_UNIVERSITIES

    client = TestClient(create_app())

    all_resp = client.get("/application-center/study-plan-workbench/catalog")
    assert all_resp.status_code == 200
    all_catalog = all_resp.json()
    assert all_catalog["total_supported_schools"] == len(SUPPORTED_UNIVERSITIES)
    assert all_catalog["active_10_week_window_count"] >= 19
    assert len(all_catalog["schools"]) == len(SUPPORTED_UNIVERSITIES)

    window_resp = client.get(
        "/application-center/study-plan-workbench/catalog",
        params={"only_active_10_week_window": "true"},
    )
    assert window_resp.status_code == 200
    window_catalog = window_resp.json()
    assert len(window_catalog["schools"]) == all_catalog["active_10_week_window_count"]
    assert all(school["in_next_10_weeks_window"] is True for school in window_catalog["schools"])

    for school_id in ("nkust", "yuntech", "ntou"):
        school_resp = client.get("/application-center/study-plan-workbench", params={"school": school_id})
        assert school_resp.status_code == 200
        assert school_resp.json()["school_id"] == school_id


def test_social_media_launch_drafts_and_frontend_contract_for_action3() -> None:
    drafts_md = (ROOT_DIR / "docs" / "social-media-launch-drafts.md").read_text(encoding="utf-8")
    assert "行動 3：【破局 Dcard】不跟 Dcard 拼閒聊，用「母校讀書計畫防雷＋文件工作台」單點爆破各校校板" in drafts_md
    assert "超過 2 頁不計分" in drafts_md
    assert "超出 2 頁之內容不予計分" in drafts_md
    assert "讀書計畫＋自傳占 50%" in drafts_md
    assert "讀書計畫占 0%、語檢占 60%" in drafts_md
    assert "/?school=nccu#application-form=study-plan" in drafts_md
    assert "/?school=ncku#application-form=study-plan" in drafts_md
    assert "/?school=ntust#application-form=study-plan" in drafts_md
    assert "全台第一" not in drafts_md

    html = (ROOT_DIR / "src" / "exchange_info" / "static" / "index.html").read_text(encoding="utf-8")
    js = (ROOT_DIR / "src" / "exchange_info" / "static" / "app.js").read_text(encoding="utf-8")
    assert 'id="study-plan-anti-pitfall-hub"' in html
    assert 'id="workbench-study-plan-assistant"' in html
    assert "loadStudyPlanWorkbench" in js
    assert "data-writing-a4-pages" in js
    assert "data-insert-partner-courses" in js


def test_study_plan_hub_and_assistant_render_the_six_steps_the_api_sends() -> None:
    """The page renders the workbench payload as the API returns it.

    The six writing steps arrive as models.StudyPlanSixStepSection (`heading`, `recommended_min_chars`,
    `recommended_max_chars`, `anti_cliche_warning`). Reading fields the API does not send threw while rendering,
    which left the hub on its loading text and made every later account sync report 同步失敗.
    """
    payload = TestClient(create_app()).get("/application-center/study-plan-workbench", params={"school": "cgu"}).json()
    script = r"""
    const assert = require("node:assert/strict"), fs = require("node:fs");
    const source = fs.readFileSync(process.argv[1], "utf8");
    const payload = JSON.parse(fs.readFileSync(0, "utf8"));
    const take = (name) => (source.match(new RegExp("^function " + name + "\\([^]*?^}", "m")) || [""])[0];
    const hub = { innerHTML: "" }, assistant = { innerHTML: "", hidden: true };
    const $ = (selector) => selector === "#study-plan-anti-pitfall-hub" ? hub : assistant;
    const state = { studyPlanWorkbench: payload, studyPlanActiveStepNumber: 1, studyPlanSandboxText: "" };
    const activeHomeSchool = () => payload.school_name;
    const applicationDocumentGenerationEnabled = () => true;
    const renderPartnerCourseLookupCard = () => "";
    const updateStudyPlanSandboxCounter = () => {};
    const initIcons = () => {};
    for (const name of ["escapeHtml", "applicationNumber", "studyPlanStepShortTitle", "studyPlanStepLength",
      "renderStudyPlanAntiPitfallHub", "renderWorkbenchStudyPlanAssistant"]) eval(take(name));

    renderStudyPlanAntiPitfallHub();
    const first = payload.six_step_guide[0];
    assert.match(hub.innerHTML, /data-study-plan-step-select="6"/);
    assert.ok(hub.innerHTML.includes(`<strong>${escapeHtml(first.heading)}</strong>`), "the open step shows its heading");
    assert.ok(hub.innerHTML.includes(escapeHtml(first.anti_cliche_warning)), "the open step shows its warning");
    assert.ok(hub.innerHTML.includes(`建議篇幅：${first.recommended_min_chars}–${first.recommended_max_chars} 字`));
    assert.ok(!hub.innerHTML.includes("undefined"));

    renderWorkbenchStudyPlanAssistant({ id: "study-plan" });
    assert.equal(assistant.hidden, false);
    assert.equal((assistant.innerHTML.match(/data-workbench-jump-field=/g) || []).length, 6);
    assert.ok(assistant.innerHTML.includes("<strong>申請動機</strong>"), "pills drop the 第 N 段 prefix and the note in brackets");
    assert.ok(assistant.innerHTML.includes("不設建議字數"), "a step without a suggested length says so");
    assert.ok(!assistant.innerHTML.includes("undefined"));
    """
    result = subprocess.run(
        ["node", "-e", script, str(ROOT_DIR / "src" / "exchange_info" / "static" / "app.js")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr

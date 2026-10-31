from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.staged_network_effects import (
    UNLOCK_THRESHOLD_MIN,
    VIRAL_PEAK_THRESHOLD,
    build_partner_specific_preference_heat,
    build_school_staged_network_status,
)
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES


def test_cold_start_protection_for_2_people_never_shows_zero_applicants(tmp_path: Path) -> None:
    """If a school only has 2 plans, never show '目前 0 人填志願' and highlight 3 solo tools."""
    status = build_school_staged_network_status("cgu", data_dir=tmp_path, override_plan_count=2)
    assert status.stage == "solo_tools_only"
    assert status.preference_heat_unlocked is False
    assert status.active_plan_count == 2
    assert status.unlock_threshold_min == UNLOCK_THRESHOLD_MIN
    assert status.plans_needed_to_unlock == 28
    assert len(status.solo_tool_pillars) == 3
    pillar_ids = [p.pillar_id for p in status.solo_tool_pillars]
    assert pillar_ids == [
        "cross_school_partner_page",
        "deadline_calendar_hook",
        "study_plan_workbench",
    ]
    for item in status.partner_preference_heat:
        assert item.heat_unlocked is False
        assert item.total_interested_count is None
        assert item.first_choice_count is None
        assert item.second_or_third_choice_count is None
        assert "0 人填志願" not in item.competition_status_label

    _, heat = build_partner_specific_preference_heat(
        home_school="cgu",
        country_slug="germany",
        institution_slug="technical-university-of-munich",
        partner_name_zh="慕尼黑工業大學",
        partner_name_en="Technical University of Munich",
        country_name_zh="德國",
        quota_hint="校級交換約 2–4 名",
        data_dir=tmp_path,
        override_plan_count=2,
    )
    assert heat.heat_unlocked is False
    assert heat.total_interested_count is None
    assert heat.first_choice_count is None
    assert heat.second_or_third_choice_count is None
    assert "0 人填志願" not in heat.competition_status_label


@pytest.mark.parametrize("quota", ["2", "名額條件" * 100])
@pytest.mark.parametrize("plan_count", [2, 30])
def test_partner_heat_preserves_valid_agreement_quota_bounds(tmp_path: Path, quota: str, plan_count: int) -> None:
    _, heat = build_partner_specific_preference_heat(
        home_school="cgu",
        country_slug="japan",
        institution_slug="example-university",
        partner_name_zh="測試大學",
        partner_name_en="Example University",
        country_name_zh="日本",
        quota_hint=quota,
        data_dir=tmp_path,
        override_plan_count=plan_count,
    )
    assert heat.quota_hint == quota
    assert heat.heat_unlocked is (plan_count >= UNLOCK_THRESHOLD_MIN)


def test_dynamic_unlock_from_solo_tools_to_preference_heat_via_api(tmp_path: Path) -> None:
    """When a school accumulates >= 30 plans, preference heat (匿名搓湯圓) unlocks automatically."""
    client = TestClient(create_app(data_dir=tmp_path))

    # NTPU starts at 27 plans (solo_tools_only)
    initial_resp = client.get("/network-effects/status", params={"school": "ntpu"})
    assert initial_resp.status_code == 200
    initial = initial_resp.json()
    assert initial["school_id"] == "ntpu"
    assert initial["active_plan_count"] == 27
    assert initial["stage"] == "solo_tools_only"
    assert initial["preference_heat_unlocked"] is False
    assert initial["plans_needed_to_unlock"] == 3
    for item in initial["partner_preference_heat"]:
        assert item["heat_unlocked"] is False
        assert item["total_interested_count"] is None

    # Submit 3 anonymous preference signals for NTPU (27 -> 28 -> 29 -> 30)
    payload = {}
    for expected_count in (28, 29, 30):
        post_resp = client.post(
            "/network-effects/preference-signal",
            json={
                "home_school": "ntpu",
                "first_choice_partner": "Waseda University",
                "second_choice_partner": "Technical University of Munich",
                "college_or_major": "商學院",
                "language_score_tag": "日檢 N1",
            },
        )
        assert post_resp.status_code == 200
        payload = post_resp.json()
        assert payload["active_plan_count"] == expected_count

    # At 30 plans, NTPU unlocks preference_heat_active!
    assert payload["preference_heat_unlocked"] is True
    assert payload["stage"] == "preference_heat_active"
    assert payload["plans_needed_to_unlock"] == 0
    waseda_item = next(
        item
        for item in payload["partner_preference_heat"]
        if item["institution_slug"] == "waseda-university"
    )
    assert waseda_item["heat_unlocked"] is True
    assert waseda_item["total_interested_count"] is not None and waseda_item["total_interested_count"] >= 5
    assert waseda_item["first_choice_count"] is not None and waseda_item["first_choice_count"] >= 2
    assert "商學院 · 日檢 N1" in waseda_item["anonymous_applicant_tags"]


def test_viral_final_week_mode_for_schools_over_50_plans(tmp_path: Path) -> None:
    """Schools with >= 50 plans (e.g. NTU, NCCU) enter viral_final_week with share copy."""
    client = TestClient(create_app(data_dir=tmp_path))
    resp = client.get("/network-effects/status", params={"school": "ntu"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_plan_count"] >= VIRAL_PEAK_THRESHOLD
    assert data["stage"] == "viral_final_week"
    assert data["preference_heat_unlocked"] is True
    assert data["viral_last_week_share_title"]
    assert "/partners?home=ntu" in data["viral_last_week_share_body"]

    catalog_resp = client.get("/network-effects/catalog")
    assert catalog_resp.status_code == 200
    catalog = catalog_resp.json()
    assert catalog["unlock_threshold_min"] == 30
    assert catalog["viral_peak_threshold"] == 50
    assert catalog["unlocked_heat_school_count"] >= 6
    assert catalog["solo_stage_school_count"] >= 10
    assert {school["school_id"] for school in catalog["schools"]} == {school.id for school in SUPPORTED_UNIVERSITIES}


def test_partner_page_upper_preference_heat_and_lower_admitted_connect(tmp_path: Path) -> None:
    """Verify /partners/{country}/{institution} renders Stage 1 for CGU, Stage 2/3 for NTU, and #admitted-connect."""
    client = TestClient(create_app(data_dir=tmp_path))

    # 1. CGU (< 30 plans) -> Solo Tools mode in upper layer
    cgu_html_resp = client.get(
        "/partners/germany/technical-university-of-munich",
        params={"home": "cgu"},
    )
    assert cgu_html_resp.status_code == 200
    cgu_html = cgu_html_resp.text
    assert 'id="preference-heat"' in cgu_html
    assert 'data-school-stage="solo_tools_only"' in cgu_html
    assert "cs-heat-locked-box" in cgu_html
    assert "單人工具" in cgu_html
    assert 'id="admitted-connect"' in cgu_html
    assert "本屆「慕尼黑工業大學」錄取生跨校連線" in cgu_html

    # 2. NTU (>= 50 plans) -> Unlocked Preference Heat in upper layer
    ntu_html_resp = client.get(
        "/partners/germany/technical-university-of-munich",
        params={"home": "ntu"},
    )
    assert ntu_html_resp.status_code == 200
    ntu_html = ntu_html_resp.text
    assert 'id="preference-heat"' in ntu_html
    assert 'data-school-stage="viral_final_week"' in ntu_html
    assert "cs-heat-unlocked-box" in ntu_html
    assert "匿名搓湯圓" in ntu_html

    # 3. JSON endpoint includes selected_home_network_status, selected_home_partner_heat, and admitted_student_connect
    json_resp = client.get(
        "/cross-school-partners/germany/technical-university-of-munich",
        params={"home": "nccu"},
    )
    assert json_resp.status_code == 200
    page_data = json_resp.json()
    assert page_data["selected_home_network_status"]["school_id"] == "nccu"
    assert page_data["selected_home_network_status"]["preference_heat_unlocked"] is True
    assert page_data["selected_home_partner_heat"]["heat_unlocked"] is True
    assert page_data["selected_home_partner_heat"]["total_interested_count"] >= 5
    connect = page_data["admitted_student_connect"]
    assert connect["admitted_count"] >= 3
    assert len(connect["participating_home_schools"]) >= 3


def test_admitted_student_connect_registration_and_pii_guard(tmp_path: Path) -> None:
    """Admitted students can register on /network-effects/admitted-connect, and PII is rejected."""
    client = TestClient(create_app(data_dir=tmp_path))

    create_resp = client.post(
        "/network-effects/admitted-connect",
        json={
            "home_school": "cgu",
            "country": "germany",
            "institution": "technical-university-of-munich",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "長庚醫技 L 同學",
            "major_or_college": "醫學院醫學生物技術暨檢驗學系",
            "looking_for_tags": ["合租找房", "同班機／接機"],
            "intro_note_zh": "已收到長庚校內錄取通知，想找慕尼黑合租室友與一起從桃園飛慕尼黑的旅伴！",
        },
    )
    assert create_resp.status_code == 201
    hub = create_resp.json()
    assert "長庚" in hub["participating_home_schools"]
    assert any("長庚校內錄取通知" in c["intro_note_zh"] for c in hub["connections"])

    # Reject LINE ID / phone / email in intro_note_zh
    pii_resp = client.post(
        "/network-effects/admitted-connect",
        json={
            "home_school": "ntu",
            "country": "germany",
            "institution": "technical-university-of-munich",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "臺大資工同學",
            "major_or_college": "電機資訊學院",
            "looking_for_tags": ["合租找房"],
            "intro_note_zh": "加我 line id: abc12345 或打 0912-345-678 聯絡",
        },
    )
    assert pii_resp.status_code == 422


def test_social_media_launch_drafts_action4_section_present() -> None:
    drafts_path = Path(__file__).resolve().parents[1] / "docs" / "social-media-launch-drafts.md"
    content = drafts_path.read_text(encoding="utf-8")
    assert "行動 4：疊加網路效應" in content
    assert "本屆錄取生跨校連線" in content
    assert "#preference-heat" in content
    assert "#admitted-connect" in content
    assert "全台第一" not in content

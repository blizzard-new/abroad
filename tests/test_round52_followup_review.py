from __future__ import annotations

import json
from pathlib import Path
import pytest

from exchange_info import storage
from exchange_info.application_rules import build_personal_application_plan
from exchange_info.models import PersonalApplicationPlanRequest
from exchange_info.ncku_student_view import fetch_ncku_partner_universities
from exchange_info.ntu_student_view import build_ntu_student_dashboard, fetch_ntu_partner_universities
from exchange_info.ntust_student_view import fetch_ntust_partner_universities
from exchange_info.round52_followup_review import (
    NCKU_HOST_LANGUAGE_REVIEWS,
    NTUST_115_2_MAINLAND_REVIEWED,
    ROUND52_MANIFEST_REL,
)
from exchange_info.tku_student_view import fetch_tku_partner_universities

ROOT = Path(__file__).resolve().parents[1]


def test_ntu_and_multi_plan_preference_capacity_consistency() -> None:
    ntu_dashboard = build_ntu_student_dashboard()
    assert ntu_dashboard.maximum_preferences == 30

    ntu_partners = fetch_ntu_partner_universities()
    assert len(ntu_partners) >= 30
    workflows = storage.load_bundled_application_workflows()

    # NTU supports up to 30 preferences across PersonalApplicationPlanRequest
    prefs_30 = [
        {"rank": idx + 1, "school_name": ntu_partners[idx].school_name}
        for idx in range(30)
    ]
    req_ntu = PersonalApplicationPlanRequest(
        home_school="國立臺灣大學",
        academic_year="116",
        application_round="116-1",
        degree_level="學士班",
        current_year="大二",
        academic_gpa=3.8,
        class_rank_percent=15.0,
        language_test="toefl",
        language_score=95.0,
        preferences=prefs_30,
    )
    plan_ntu = build_personal_application_plan(
        req_ntu, ntu_partners, workflows, academic_score_minimum=None
    )
    assert len(plan_ntu.choices) == 30

    # CGU enforces <= 2 preferences
    with pytest.raises(ValueError, match="長庚大學校級交換最多2個志願"):
        build_personal_application_plan(
            PersonalApplicationPlanRequest(
                home_school="長庚大學",
                preferences=prefs_30[:3],
            ),
            [],
            [],
            academic_score_minimum=None,
        )

    # CCU enforces <= 3 preferences
    with pytest.raises(ValueError, match="最多3個志願"):
        build_personal_application_plan(
            PersonalApplicationPlanRequest(
                home_school="國立中正大學",
                preferences=prefs_30[:4],
            ),
            [],
            [],
            academic_score_minimum=None,
        )

    # Frontend multi-plan.js respects state.dashboard?.maximum_preferences
    multi_plan_js = (ROOT / "src/exchange_info/static/multi-plan.js").read_text("utf-8")
    assert "state.dashboard?.maximum_preferences || 5" in multi_plan_js


def test_ntust_mainland_22_schools_reconciled_with_archived_pdf() -> None:
    partners = fetch_ntust_partner_universities()
    mainland_partners = [p for p in partners if p.country == "中國大陸"]
    assert len(mainland_partners) == 44

    open_115_2 = [
        p for p in mainland_partners if "115-2 大陸地區交換公告名額" in (p.quota or "")
    ]
    unlisted_115_2 = [
        p for p in mainland_partners if "未列入 115-2 大陸地區交換學校一覽表" in (p.quota or "")
    ]
    assert len(open_115_2) == 22
    assert len(unlisted_115_2) == 22

    by_zh = {p.school_name.split()[0]: p for p in mainland_partners}
    assert set(NTUST_115_2_MAINLAND_REVIEWED) == {p.school_name.split()[0] for p in open_115_2}

    # Check specific PDF restrictions from reviewed_1152_mainland_schools_20261021.pdf
    assert "含建築系所 1 名" in (by_zh["同濟大學"].quota or "")
    assert "限大學部或碩士生" in (by_zh["同濟大學"].colleges or "")
    assert "電資學院優先" in (by_zh["電子科技大學"].colleges or "")
    assert "限大學部或碩士生" in (by_zh["廈門大學"].colleges or "")
    assert "管理學院不收碩士生" in (by_zh["浙江大學"].colleges or "")
    assert "限大二及大三生" in (by_zh["浙江大學"].degree_levels or "")
    assert "應屆畢業生不得在下學期提出申請" in (by_zh["南京大學"].colleges or "")
    assert "應屆畢業生不得在下學期提出申請" in (by_zh["西安交通大學"].colleges or "")
    assert "不接受大四及應屆畢業生申請" in (by_zh["東南大學"].colleges or "")
    assert "不接受大四及碩二生申請" in (by_zh["華東師範大學"].colleges or "")

    # Unlisted Mainland sister schools must not claim 115-2 quotas or 2-5 seats
    raw_rows = {
        json.loads(line)["school_name"]: json.loads(line)
        for line in (ROOT / "src/exchange_info/official_data/ntust/partners.jsonl")
        .read_text("utf-8")
        .splitlines()
        if line.strip()
    }
    for p in unlisted_115_2:
        assert "每學期約 2–5 名" not in (p.quota or "")
        assert raw_rows[p.school_name]["factsheet_url"] is None
        assert "未列入115-2大陸組開放一覽表" in (p.field_evidence["quota"].note or "")


def test_tku_waseda_round1_japanese_guide_surfaces_in_reference_options() -> None:
    tku_partners = fetch_tku_partner_universities()
    waseda = next(p for p in tku_partners if "早稻田大學" in p.school_name)
    assert len(waseda.program_options) >= 1
    opt = waseda.program_options[0]
    assert opt.quota == "2"
    assert "N1（各系要求不同）" in (opt.eligibility or "")
    assert "GPA依各系要求" in (opt.eligibility or "")

    r42 = json.loads(
        (ROOT / "docs/data-verification-20261021/round42-followup-source-notes.json").read_text("utf-8")
    )
    assert all(f["data_changed"] is True for f in r42["findings"])


def test_ncku_host_language_evidence_attached_for_vmu_and_vsb() -> None:
    ncku_partners = {p.school_name: p for p in fetch_ncku_partner_universities()}
    for school_name, spec in NCKU_HOST_LANGUAGE_REVIEWS.items():
        partner = ncku_partners[school_name]
        assert "TOEIC" in (partner.language_requirement or "") and "讀寫" in (partner.language_requirement or "")
        host_ev = partner.field_evidence["host_language_evidence"]
        assert host_ev.source_url == spec["source_url"]
        assert "785" in (host_ev.excerpt or "")
        assert partner.partner_exchange_details is not None
        host_lang_detail = partner.partner_exchange_details["host_language_requirements"]
        assert host_lang_detail.status == "reference_only"
        assert "TOEIC" in (host_lang_detail.value or "")

    manifest = json.loads((ROOT / ROUND52_MANIFEST_REL).read_text("utf-8"))
    assert manifest["round"] == 52
    assert manifest["ntust_mainland_review"]["reviewed_open_115_2_schools"] == 22

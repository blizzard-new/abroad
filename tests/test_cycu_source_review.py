from __future__ import annotations

import copy
import json
from pathlib import Path

from exchange_info.cycu_source_review import load_tables, match_row, review_partner, review_workflow
from exchange_info.models import PartnerUniversity, UniversityApplicationWorkflow
from exchange_info.cycu_eligibility import cycu_academic_check

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/cycu"


def partner(prefix):
    return next(json.loads(x) for x in (BUNDLE / "partners.jsonl").read_text("utf8").splitlines()
                if json.loads(x)["school_name"].startswith(prefix))


def workflow(name):
    return next(json.loads(x) for x in (BUNDLE / "application_workflows.jsonl").read_text("utf8").splitlines()
                if json.loads(x)["school_name"] == name)


def test_current_round_does_not_reuse_common_deadline():
    tables = load_tables(ROOT)
    for name, deadline in [("安徽大學", "11月20日"), ("福州大學", "11月30日"), ("南京大學", "10月14日")]:
        p = partner(name)
        review_partner(p, tables)
        assert deadline in p["application_deadline"]
        w = workflow(p["school_name"])
        review_workflow(w, p, tables)
        assert all(s["deadline_at"] is None for s in w["steps"])
        assert not any(s["deadline_reminder_eligible"] for s in w["steps"])
        assert all(s["scope"]["academic_years"] == ["115"] for s in w["steps"])
        UniversityApplicationWorkflow.model_validate(w)


def test_missing_dates_and_name_conflicts_stay_unresolved():
    tables = load_tables(ROOT)
    lanzhou = partner("蘭州大學")
    dalian = partner("大連理工大學")
    assert match_row(lanzhou, tables)[1][4] == ""
    assert match_row(dalian, tables)[1] is None
    for p in (lanzhou, dalian):
        review_partner(p, tables)
        assert p["availability_status"] == "needs_confirmation"
        assert "10月20日" not in p["application_deadline"]


def test_international_round_retains_program_exceptions():
    tables = load_tables(ROOT)
    p = partner("匹茲堡州立大學")
    review_partner(p, tables)
    assert "研究生僅一學期" in p["study_period"]
    assert "研究所" in p["language_requirement"] and "80" in p["language_requirement"]
    assert p["availability_status"] == "reference_only"
    assert p["field_evidence"]["language_requirement"]["status"] == "reference_only"
    w = workflow(p["school_name"])
    review_workflow(w, p, tables)
    assert w["steps"][1]["deadline_at"] == "2026-10-07T12:00:00+08:00"
    assert w["steps"][2]["deadline_at"] is None
    assert "10/14" in w["steps"][2]["timing"]
    assert "701B" in w["steps"][1]["submission"]["office"]
    PartnerUniversity.model_validate(p)
    UniversityApplicationWorkflow.model_validate(w)


def test_matching_requires_country_and_never_promotes_missing_rows():
    tables = load_tables(ROOT)
    p = partner("建國大學")
    assert match_row(p, tables)[1] is not None
    p["country"] = "韓國"
    assert match_row(p, tables)[1] is None
    skema = partner("SKEMA商學院")
    review_partner(skema, tables)
    assert skema["availability_status"] == "needs_confirmation"
    assert "終止" in skema["availability_note"]  # Explicitly not inferred.


def test_rank_alternative_conflict_and_percentage_are_not_auto_passes():
    assert cycu_academic_check("學士班", 90, 2.9, 20)[0] == "needs_confirmation"
    assert cycu_academic_check("學士班", 90, None, None)[0] == "needs_confirmation"
    assert cycu_academic_check("學士班", None, 3.0, 50)[0] == "pass"


def test_review_is_idempotent_and_preserves_original_reference():
    p = partner("方提斯應用科技大學")
    tables = load_tables(ROOT)
    review_partner(p, tables)
    first = copy.deepcopy(p)
    review_partner(p, tables)
    assert p == first
    assert "reference_data" in p

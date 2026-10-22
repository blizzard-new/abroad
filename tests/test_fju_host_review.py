"""Round 49 FJU host-source reviews and legacy deposit/cost unification tests."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from exchange_info import storage
from exchange_info.application_rules import _partner_language_threshold
from exchange_info.fju_host_review import (
    ARCHIVE_KEY,
    apply_fju_host_review,
    load_manifest,
)
from exchange_info.fju_student_view import (
    build_fju_student_dashboard,
    fetch_fju_partner_universities,
    fju_exchange_info,
)
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import (
    DestinationProfile,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/fju"


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text("utf8").splitlines() if line.strip()]


def test_round49_host_reviews_preserve_mother_conflicts_and_source_boundaries():
    partners = {p.school_name: p for p in fetch_fju_partner_universities()}
    workflows = {
        w.school_name: w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == "天主教輔仁大學"
    }
    profiles = {
        p.school_name: p
        for p in storage.load_destination_profiles(home_university="天主教輔仁大學")
    }

    temple = partners["天普大學 Temple University"]
    assert temple.website == "https://globalprograms.temple.edu/application-process-costs-and-aid/application-process-and-costs"
    assert "聽讀各390" in temple.language_requirement
    assert "Listening 390" in temple.language_requirement
    assert "美國姊妹校不接受 TOEIC" in temple.language_requirement
    assert temple.field_evidence["language_requirement"].status == "needs_confirmation"
    assert _partner_language_threshold(temple, "toeic", "大學部") is None
    assert "4/1" in workflows["天普大學 Temple University"].steps[3].summary

    udem = partners["蒙特雷大學 Universidad de Monterrey"]
    assert "截斷" in udem.language_requirement
    assert "CEFR B2" in udem.language_requirement
    assert udem.field_evidence["language_requirement"].status == "needs_confirmation"
    assert _partner_language_threshold(udem, "toefl", "大學部") is None
    assert "studyabroad.udem.edu.mx" in workflows["蒙特雷大學 Universidad de Monterrey"].steps[3].summary

    pforzheim = partners["普福爾茨海姆大學 Pforzheim University"]
    assert "截斷" in pforzheim.language_requirement
    assert "PHP" in pforzheim.language_requirement
    assert pforzheim.field_evidence["language_requirement"].status == "needs_confirmation"
    assert _partner_language_threshold(pforzheim, "toefl", "大學部") is None
    assert workflows["普福爾茨海姆大學 Pforzheim University"].steps[3].needs_confirmation is True

    hkbu = partners["香港浸會大學 Hong Kong Baptist University"]
    assert hkbu.field_evidence["degree_levels"].status == "needs_confirmation"
    assert "前後" in hkbu.availability_note and "L4" in hkbu.course_restrictions
    assert "2.50/4.00" in hkbu.student_summary_zh.eligibility_points[3]
    assert "2.5" in hkbu.field_evidence["gpa_requirement"].excerpt
    assert "Undergraduate Halls" in profiles["香港浸會大學 Hong Kong Baptist University"].housing_summary


def test_legacy_deposit_is_unified_as_needs_confirmation_across_partners_workflows_and_singletons():
    partners = fetch_fju_partner_universities()
    general = [p for p in partners if not p.school_name.startswith("(自費)東洋") and not p.school_name.startswith("(自費)南山") and not p.school_name.startswith("(自費)同志社")]
    assert len(general) == 234
    for p in general:
        assert "舊版母校頁面曾載" in p.tuition_info
        assert "待正式通知確認" in p.tuition_info
        assert "待正式通知確認" in p.student_summary_zh.tuition_points[1]
        assert p.field_evidence["tuition_info"].status == "needs_confirmation"

    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == "天主教輔仁大學" and len(w.steps) == 5
    ]
    assert len(workflows) == 234
    for w in workflows:
        step5 = w.steps[4]
        assert "舊版頁面曾載" in step5.summary and "待正式通知確認" in step5.summary
        assert step5.support_status == "needs_confirmation"
        assert step5.needs_confirmation is True

    info = fju_exchange_info()
    assert any("舊版母校頁面曾載" in s and "待正式通知確認" in s for s in info.scholarship_info)
    dashboard = build_fju_student_dashboard()
    assert "待正式通知確認" in dashboard.scholarship_info[0].details[2]
    assert "待正式通知確認" in dashboard.rule_explanations[0].key_points[2]


def test_round49_manifest_validates_all_models_and_replays_idempotently(tmp_path):
    manifest = load_manifest(ROOT)
    assert manifest["round"] == 49
    assert len(manifest["rows"]) == 472
    assert len(manifest["singletons"]) == 3

    models = {
        "partners.jsonl": PartnerUniversity,
        "application_workflows.jsonl": UniversityApplicationWorkflow,
        "destination_profiles.jsonl": DestinationProfile,
    }
    loaded_by_file = {name: _rows(BUNDLE / name) for name in models}
    for name, model in models.items():
        for row in loaded_by_file[name]:
            model.model_validate(row)

    for scope in manifest["rows"]:
        name = Path(scope["file"]).name
        row = next(r for r in loaded_by_file[name] if r["school_name"] == scope["school_name"])
        archive = row["reference_data"][ARCHIVE_KEY]
        archive = json.loads(archive) if isinstance(archive, str) else archive
        for patch in scope["patches"]:
            parent, key = pointer_parent(row, patch["pointer"])
            assert parent[key] == patch["value"]
            assert archive[patch["pointer"]]["existed"] != patch["expected_missing"]

    bundle = tmp_path / "fju"
    shutil.copytree(BUNDLE, bundle)
    before = {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    assert apply_fju_host_review(ROOT, bundle=bundle) == 0
    assert before == {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}

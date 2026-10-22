"""Round 50 NCKU Yonsei Mirae campus identity and Waseda WBS/NCKU follow-up tests."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

from exchange_info import storage
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.models import PartnerUniversity, UniversityApplicationWorkflow
from exchange_info.ncku_student_view import fetch_ncku_partner_universities
from exchange_info.round50_followup_review import (
    ARCHIVE_KEY,
    HOMES,
    MANIFEST,
    apply_round50_followup_review,
    load_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text("utf8").splitlines() if line.strip()]


def test_ncku_yonsei_mirae_campus_identity_and_waseda_workflow_restrictions():
    partners = {p.school_name: p for p in fetch_ncku_partner_universities()}
    mirae = partners["延世大學（未來校區） Yonsei University Mirae Campus"]
    ev = mirae.field_evidence["campus_identity"]
    assert ev.status == "needs_confirmation"
    assert ev.source_url == "https://yiec.yonsei.ac.kr/yiec_en/program/overseas01.do"
    assert "2020-11-06" in ev.excerpt
    assert "2020-11-06" in mirae.availability_note

    workflows = {
        w.school_name: w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == "國立成功大學"
    }
    mirae_wf = workflows["延世大學（未來校區） Yonsei University Mirae Campus"]
    assert "https://yiec.yonsei.ac.kr/yiec_en/program/overseas01.do" in mirae_wf.steps[3].source_urls
    assert any("2020-11-06" in d for d in mirae_wf.steps[3].details)

    waseda_wf = workflows["早稻田大學 Waseda University"]
    assert any("不接受跨領域申請" in d for d in waseda_wf.steps[3].details)


def test_waseda_wbs_departmental_partner_list_is_scoped_reference_on_ntust_ntu_nccu():
    for home_id, target_name in (
        ("ntust", "早稻田大學 Waseda University"),
        ("ntu", "早稻田大學"),
        ("nccu", "早稻田大學 Waseda University"),
    ):
        rows = _rows(ROOT / f"src/exchange_info/official_data/{home_id}/partners.jsonl")
        waseda = PartnerUniversity.model_validate(next(r for r in rows if r["school_name"] == target_name))
        ev = waseda.field_evidence["wbs_departmental_partner_list"]
        assert ev.status == "reference_only"
        assert ev.source_url == "https://www.waseda.jp/fcom/wbs/assets/uploads/2026/07/20260710_List_Partner_Schools.pdf"
        assert "Waseda Business School" in ev.excerpt
        if home_id == "ntust":
            assert "WBS" in waseda.language_review_note


def test_round50_manifest_validates_and_replays_idempotently(tmp_path):
    manifest = load_manifest(ROOT)
    assert manifest["round"] == 50
    assert len(manifest["rows"]) == 6
    models = {
        "partners.jsonl": PartnerUniversity,
        "application_workflows.jsonl": UniversityApplicationWorkflow,
    }
    for scope in manifest["rows"]:
        path = ROOT / scope["file"]
        row = next(r for r in _rows(path) if r["school_name"] == scope["school_name"])
        models[path.name].model_validate(row)
        archive = row["reference_data"][ARCHIVE_KEY]
        if isinstance(archive, str):
            archive = json.loads(archive)
        for patch in scope["patches"]:
            parent, key = pointer_parent(row, patch["pointer"])
            assert parent[key] == patch["value"]
            assert archive[patch["pointer"]]["existed"] != patch["expected_missing"]

    (tmp_path / Path(MANIFEST).parent).mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / MANIFEST, tmp_path / MANIFEST)
    for scope in manifest["rows"]:
        dest = tmp_path / scope["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(ROOT / scope["file"], dest)
    assert apply_round50_followup_review(tmp_path) == 0

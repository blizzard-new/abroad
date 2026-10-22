from __future__ import annotations

import json
from pathlib import Path

from exchange_info.models import PartnerUniversity
from exchange_info.stage1_website_and_roster_review import (
    MANIFEST_PATH,
    ROSTER_RECONCILIATION_SCHOOLS,
    TARGET_WEBSITE_SCHOOLS,
    apply_stage1_website_and_roster_review,
    classify_website_defect,
)

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DATA = ROOT / "src" / "exchange_info" / "official_data"


def _load_partners(school_id: str) -> list[PartnerUniversity]:
    path = OFFICIAL_DATA / school_id / "partners.jsonl"
    return [
        PartnerUniversity.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_stage1_website_defects_are_zero_across_target_schools_and_ncu_audited() -> None:
    manifest = json.loads((ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    assert manifest["website_repairs_count"] == 356
    assert manifest["ncu_audit_only_repairs_count"] == 60
    assert manifest["total_website_defects_resolved"] == 416
    for school_id in TARGET_WEBSITE_SCHOOLS:
        partners = _load_partners(school_id)
        for p in partners:
            defect = classify_website_defect(p.website, p.school_name)
            assert defect is None, f"{school_id} {p.school_name} still has website defect: {defect} ({p.website})"
        pr_path = OFFICIAL_DATA / school_id / "partner_research.jsonl"
        if pr_path.exists():
            for line in pr_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                defect = classify_website_defect(rec.get("official_website"), rec.get("school_name", ""))
                assert defect is None, (
                    f"{school_id} partner_research {rec.get('school_name')} still has defect: {defect}"
                )


def test_stage1_roster_reconciliations_cover_all_214_unmapped_rows() -> None:
    manifest = json.loads((ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    assert manifest["roster_reconciliations_count"] == 214
    expected_counts = {
        "pccu": 48,
        "wzu": 19,
        "fcu": 18,
        "nkust": 10,
        "yuntech": 4,
        "ntou": 78,
        "yzu": 37,
    }
    for school_id, expected in expected_counts.items():
        assert school_id in ROSTER_RECONCILIATION_SCHOOLS
        partners = _load_partners(school_id)
        unmapped = [p for p in partners if p.availability_status == "needs_confirmation"]
        assert len(unmapped) == expected
        for p in unmapped:
            raw_rec = p.reference_data.get("stage1_roster_reconciliation")
            assert raw_rec, f"Missing stage1_roster_reconciliation on {school_id} {p.school_name}"
            rec = json.loads(raw_rec)
            assert rec["home_school"] == school_id
            assert rec["canonical_host_website"].startswith(("http://", "https://"))
            assert rec["school_identity_key"]
            assert rec["reconciliation_class"] == ROSTER_RECONCILIATION_SCHOOLS[school_id]["reconciliation_class"]


def test_stage1_nycu_uc_santa_cruz_and_image_conflict_audits() -> None:
    manifest = json.loads((ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    ucsc = manifest["nycu_ust_uc_santa_cruz_audit"]
    assert ucsc["canonical_host_website"] == "https://www.ucsc.edu/"
    assert "暑期研究" in ucsc["scope"]

    r13 = json.loads((ROOT / "docs/data-verification-20261021/round13-source-conflicts.json").read_text(encoding="utf-8"))
    assert r13["missing_partner_record"]["canonical_host_website"] == "https://www.ucsc.edu/"
    assert r13["missing_partner_record"]["stage1_reconciliation_status"] == (
        "verified_ust_summer_research_only_not_semester_exchange"
    )

    audits = {a["home_school"]: a for a in manifest["campus_image_conflict_audits"]}
    assert set(audits) == {"nsysu", "nycu", "tmu"}
    assert audits["nsysu"]["resolution_policy"] == "fail_closed_in_coverage_api"
    assert audits["nycu"]["resolution_policy"] == "fail_closed_in_coverage_api"
    assert audits["tmu"]["resolution_policy"] == "fail_closed_in_coverage_api"


def test_stage1_apply_is_idempotent() -> None:
    result = apply_stage1_website_and_roster_review(ROOT)
    assert result["website_repairs_count"] == 356
    assert result["ncu_audit_only_repairs_count"] == 60
    assert result["total_website_defects_resolved"] == 416
    assert result["roster_reconciliations_count"] == 214

"""Offline CCU acceptance gate; does not collect sources or modify any catalogue."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from exchange_info.ccu_campus_assets import reviewed_assets
from exchange_info.ccu_completion import reviewed_completion
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.storage import load_destination_profiles

BASE = "59a20f27fcee00fb597abc79e75ec11778317422"
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wheel", type=Path)
    args = parser.parse_args()
    partners = fetch_ccu_partner_universities()
    assets, fields = reviewed_assets(), reviewed_completion()
    assert len(partners) == len(assets) == len(fields) == 104
    assert len({(p.school_name, p.country) for p in partners}) == 104
    assert all(p.school_name and p.country and p.academic_year and p.application_round
               and p.source_url and p.source_pages and p.checked_at for p in partners)
    assert Counter(p.availability_status for p in partners) == {"open": 52, "needs_confirmation": 3, "not_open": 49}
    assert all(p.application_window_status == "closed" for p in partners)
    assert {p.source_pages[0] for p in partners if p.quota_status == "not_published"} == {71, 80, 107}
    assert all(p.quota is None and p.eligibility is None and p.language_requirement is None
               for p in partners if p.availability_status == "not_open")
    assert all(p.quota and (p.quota == "無限制" or any(int(n) > 0 for n in re.findall(r"\d+", p.quota)))
               and p.quota_status == "published" for p in partners if p.availability_status == "open")
    for row in fields.values():
        assert len(row["profile_fields"]) == 7 and len(row["host_fields"]) == 17
        for group in ["host_fields", "profile_fields", "general_campus_fields"]:
            for field in row[group].values():
                assert field["reason"]
                assert field["status"] in {"missing", "verified_current", "reference_only", "needs_confirmation", "conflict", "explicit_not_announced"}
                if field["status"] == "missing":
                    assert field["value"] is None
                for ev in field["evidence"]:
                    assert all(ev.get(k) for k in ["source_url", "checked_at", "academic_year", "excerpt"])
    preserved = subprocess.check_output(["git", "diff", "--name-only", BASE, "--", "src/exchange_info/official_data"], cwd=ROOT, text=True).splitlines()
    assert all(path.startswith(("src/exchange_info/official_data/ccu/completion",
                               "src/exchange_info/official_data/ccu/campus-"))
               or path in {"src/exchange_info/official_data/ccu/destination_profiles.jsonl",
                           "src/exchange_info/official_data/ccu/application_workflows.jsonl"} for path in preserved), preserved
    original_workflows = subprocess.check_output(
        ["git", "show", BASE + ":src/exchange_info/official_data/ccu/application_workflows.jsonl"], cwd=ROOT).splitlines()
    current_workflows = (BUNDLE / "application_workflows.jsonl").read_bytes().splitlines()
    assert len(original_workflows) == len(current_workflows)
    changed_workflows = [(json.loads(old), json.loads(new))
                         for old, new in zip(original_workflows, current_workflows, strict=True) if old != new]
    reviewed_pages = {49, 89}
    reviewed_names = {p.school_name for p in partners if p.source_pages[0] in reviewed_pages}
    assert len(changed_workflows) == len(reviewed_pages)
    assert {old["school_name"] for old, _ in changed_workflows} == reviewed_names
    assert all(old["school_name"] == new["school_name"] for old, new in changed_workflows)
    original = subprocess.check_output(["git", "show", BASE + ":src/exchange_info/official_data/ccu/destination_profiles.jsonl"], cwd=ROOT)
    new = (BUNDLE / "destination_profiles.jsonl").read_bytes()
    assert new.startswith(original) and len(new.splitlines()) == 104
    profiles = load_destination_profiles(ROOT / ".ccu-validation-no-local-data", include_bundled_baseline=True)
    profile_counts = Counter(p.home_university for p in profiles)
    assert profile_counts[HOME] == 104 and profile_counts["長庚大學"] == 77 and profile_counts["國立臺北大學"] == 206
    image_count = sum(p.image_status == "verified" for p in partners)
    point_count = sum(p.location is not None and p.location.geocode_status == "verified" for p in partners)
    assert image_count == 100 and point_count == 101
    package = None
    if args.wheel:
        with ZipFile(args.wheel) as archive:
            prefix = "exchange_info/"
            expected = [*list((BUNDLE / "completion_sources").glob("*")),
                        *list((BUNDLE.parents[1] / "static/assets/ccu/campuses").glob("*")),
                        *list(BUNDLE.glob("completion-*")), *list(BUNDLE.glob("campus-*")),
                        BUNDLE / "destination_profiles.jsonl", BUNDLE / "application_workflows.jsonl",
                        *[BUNDLE.parents[1] / name for name in ["ccu_completion.py", "ccu_overseas.py", "ccu_sungshin_current.py"]]]
            for file in expected:
                if file.is_file():
                    assert archive.read(prefix + str(file.relative_to(BUNDLE.parents[1]))) == file.read_bytes(), file
            package = {"wheel": args.wheel.name, "sha256": hashlib.sha256(args.wheel.read_bytes()).hexdigest(),
                       "ccu_files_verified": sum(file.is_file() for file in expected)}
    result = {"baseline_commit": BASE, "candidate_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "exchange_list": 104, "global_agreements": None, "quotas": {"available": 52, "numeric_positive": 49, "unlimited": 3, "blank": 3, "not_open": 49, "explicit_zero": 0},
              "all_home_windows_closed": True, "profile_counts_all_six_schools": dict(profile_counts),
              "official_website_identity_count": sum(bool(p.website) for p in partners),
              "coordinates": point_count, "licensed_photos": image_count,
              "matrix_counts": {group: dict(Counter(f["status"] for row in fields.values() for f in row[group].values()))
                                for group in ["host_fields", "profile_fields", "general_campus_fields"]},
              "old_official_data_preserved_except_reviewed_workflow_rows": True,
              "published_workflow_refresh": {"changed_rows": len(changed_workflows), "school_names": sorted(reviewed_names),
                                             "reviewed_pages": sorted(reviewed_pages),
                                             "other_rows_preserved_byte_for_byte": len(current_workflows) - len(changed_workflows)},
              "original_ccu_profiles_sha256": hashlib.sha256(original).hexdigest(),
              "package": package}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

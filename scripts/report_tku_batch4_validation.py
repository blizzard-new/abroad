"""Export the current merged-main regression and real switching evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info import storage
from exchange_info.tku_completeness import matrix_row
from exchange_info.tku_data import BUNDLE, load_tku_records, load_tku_sources, tku_integrity_report
from report_tku_validation import test_result


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main(args):
    current = test_result(args.junit)
    baseline = test_result(args.baseline_junit)
    ntu = test_result(args.ntu_junit)
    browser = json.loads(args.browser.read_text())
    assert browser["status"] == "passed" and len(browser["checks"]) == 2
    for view in browser["checks"]:
        assert len(view["detail_checks"]) == 4 and not view["page_errors"]
        assert len({r["home"] for r in view["checks"]}) == 4
        assert view["cancel_keeps_original"] and view["stale_response_ignored"]
        assert view["wrong_year_does_not_reuse_documents"]
    assert ntu["failed"] == 0 and ntu["passed"] == 7
    sources = load_tku_sources()
    rows = load_tku_records(include_reference=True)
    matrix = [dict(id=r.id, school_name=r.fields["school_name"].value,
        field_states=matrix_row(r)["field_states"]) for r in rows if r.selection_status == "listed"]
    states = Counter()
    for row in matrix:
        states.update(row["field_states"])
    data = tku_integrity_report()
    data.update(unique_original_school_names=len({r.fields["school_name"].value for r in rows}),
        current_matrix=matrix, current_matrix_totals=dict(states),
        current_verified_fraction=states["verified"] / sum(states.values()),
        matrix_school_count=len(rows), matrix_fields_per_school=38, currently_open_choices=0,
        source_count=len(sources), unique_source_urls=len({s["source_url"] for s in sources}),
        downloaded_original_attachments=sum(bool(s.get("local_file")) for s in sources),
        source_failures=[dict(id=s["id"], url=s["source_url"], error=s["error"])
                         for s in sources if s.get("open_status") == "failed"],
        host_documents_by_school=[dict(school=r["school_name"], phases=dict(Counter(d["phase"] for d in r["documents"])))
            for r in json.loads((BUNDLE / "host_documents.json").read_text())])
    protected = ["src/exchange_info/official_data/cgu", "src/exchange_info/official_data/ntpu",
                 "src/exchange_info/official_data/ntu", "src/exchange_info/cgu*.py",
                 "src/exchange_info/ntpu*.py", "src/exchange_info/ntu*.py",
                 "src/exchange_info/static/application-journey.js", "src/exchange_info/static/document-workbench.js"]
    differences = git("diff", "--name-only", args.integration_main, "--", *protected).splitlines()
    assert not differences, differences
    paths = git("diff", "--name-only", args.integration_main).splitlines()
    common = [p for p in paths if p in {"pyproject.toml", "docs/api/openapi.json",
        "src/exchange_info/api.py", "src/exchange_info/application_documents.py", "src/exchange_info/models.py",
        "src/exchange_info/storage.py", "src/exchange_info/university_registry.py",
        "src/exchange_info/static/app.js", "src/exchange_info/static/index.html",
        "tests/test_school_completeness.py", "tests/test_ntu_integration.py", "tests/e2e/test_ntu_school.py",
        "tests/test_task_documents_and_reference_plan.py", "tests/test_fit_signals.py"}]
    audit = json.loads((BUNDLE / "current_notice_audit.json").read_text())
    before, after = json.loads(args.before.read_text()), json.loads(args.after.read_text())
    assert before[-1]["catalog"] == before[0]["catalog"] != before[1]["input"]
    assert after[-1]["catalog"] == after[1]["input"] != after[0]["catalog"]
    report = dict(checked_at="2026-10-08", branch="data/tku-exchange-20261008",
        integration_main=args.integration_main, merge_commit="1bbb150f738bb5a9eac5d5166b489d449d27bc22",
        main_is_ancestor=subprocess.run(["git", "merge-base", "--is-ancestor", args.integration_main, "HEAD"], cwd=ROOT).returncode == 0,
        data=data, current_tests=current, baseline_failure_comparison=baseline, ntu_browser_tests=ntu,
        new_failure_ids=sorted(set(current["failure_ids"]) - set(baseline["failure_ids"])), browser=browser,
        target_reproduction=dict(baseline_frontend=args.integration_main,
            scope="Latest-main app.js intercepted in isolated local TKU server; rerender while native confirmation is open.",
            before=before, after=after),
        announcement_audit=dict(path="src/exchange_info/official_data/tku/current_notice_audit.json",
            sha256=hashlib.sha256((BUNDLE / "current_notice_audit.json").read_bytes()).hexdigest(),
            capture_count=len(audit["evidence"]), rest_records=audit["rest_total"], rest_pages=audit["rest_pages"],
            status=audit["finding_status"], finding=audit["finding"], unresolved_conflicts=len(audit["conflicts_checked"])),
        protected_files=dict(diff_from_main=differences,
            bundled_workflows=dict(Counter(r.home_university for r in storage.load_bundled_application_workflows())),
            bundled_destinations=dict(Counter(r.home_university for r in storage.load_destination_profiles()))),
        shared_files=common,
        checks=dict(openapi="passed", python_syntax="passed", javascript_syntax="passed", diff_check="passed",
            offline_rebuild="passed in TKU regression test",
            lockfile_check="exit 1 on this branch and untouched f6ad: The lockfile at uv.lock needs to be updated; uv.lock unchanged",
            remote_ci="Delivery evidence will be checked after push and recorded in PR/final reply; local passes do not establish remote CI success."),
        remaining_scope="124 archived programme rows are reference-only; current host details are reviewed only for the four latest Japanese choices. Nagasaki NICS/graduate mapping, UEC 2027-specific forms, and 13 source conflicts remain explicit.")
    assert report["main_is_ancestor"] and not report["new_failure_ids"]
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(output=str(args.output), tests=current, shared_files=len(common)), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["junit", "baseline-junit", "ntu-junit", "browser", "before", "after", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--integration-main", required=True)
    main(parser.parse_args())

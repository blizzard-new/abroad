"""Run the final candidate checks together, retaining actual failures and skips.

All top-level Python tests plus relevant real-browser suites run in one pytest
invocation, including the source-recovered historical wrapper. Its collection is
also recorded separately. Unknown historical bytecode tests are not claimed.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSERS = ["test_tku_acceptance.py", "test_ntu_school.py", "test_application_workspace.py",
    "test_application_ui_refinements.py", "test_application_periods.py", "test_fit_and_completeness_ui.py",
    "test_planning_workspace.py", "test_tku_draft_handoff.py", "test_tku_source_rendering.py"]


def candidate_state(root, commit):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()
    return dict(commit=head, worktree_status=dirty, valid=head == commit and not dirty)


def execute_checks(root, out, commit, checks, env, report):
    """Fail the process for failed children or changes to the candidate under test."""
    report.update(tested_commit=commit, started_at=time.time(), checks=[])
    report["starting_state"] = candidate_state(root, commit)
    exit_code = 0
    for name, command in checks:
        before = candidate_state(root, commit)
        if not before["valid"]:
            report["candidate_guard_failure"] = dict(check=name, when="before", **before)
            exit_code = 2
            break
        print(f"Running {name} at {commit}", flush=True)
        start = time.time()
        log = out / f"{name}.log"
        with log.open("w") as handle:
            try:
                result = subprocess.run(command, cwd=root, env=env, stdout=handle, stderr=subprocess.STDOUT)
                child_exit = result.returncode
            except OSError as error:
                handle.write(f"Cannot execute command: {error}\n")
                child_exit = 127
        after = candidate_state(root, commit)
        report["checks"].append(dict(name=name, command=command, exit_code=child_exit,
            elapsed_seconds=round(time.time() - start, 2), log=str(log), before=before, after=after))
        if child_exit:
            exit_code = 1
        print(f"{name}: actual exit {child_exit}; {log}", flush=True)
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        if not after["valid"]:
            report["candidate_guard_failure"] = dict(check=name, when="after", **after)
            exit_code = 2
            break
    ending = candidate_state(root, commit)
    if not ending["valid"]:
        exit_code = 2
    report.update(ended_at=time.time(), ending_commit=ending["commit"],
        ending_worktree_status=ending["worktree_status"], runner_exit_code=exit_code,
        all_checks_executed=len(report["checks"]) == len(checks),
        all_checks_passed=exit_code == 0 and len(report["checks"]) == len(checks))
    (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return exit_code


def run(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commit = args.candidate_sha
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
        TKU_ACCEPTANCE_OUTPUT=str(out / "browser"), TKU_SWITCH_OUTPUT=str(out / "switch.json"),
        UV_CACHE_DIR=str(out / "uv-cache"))
    units = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "tests").glob("test_*.py"))]
    browser = [f"tests/e2e/{name}" for name in BROWSERS]
    browser += ["tests/e2e/test_web_next_phase.py::test_application_form_sync_review_and_pdf_download"]
    checks = [
        ("pytest-unit-and-browser", [sys.executable, "-m", "pytest", *units, *browser, "-q", "-ra", f"--junitxml={out / 'suite.xml'}"]),
        ("tku-switching-and-details", [sys.executable, "scripts/check_tku_target_switching.py"]),
        ("openapi", [sys.executable, "scripts/export_openapi.py", "--check"]),
        ("javascript-shared", ["node", "--check", "src/exchange_info/static/app.js"]),
        ("javascript-tku", ["node", "--check", "src/exchange_info/static/tku-academic-units.js"]),
        ("javascript-tku-eligibility", ["node", "--check", "src/exchange_info/static/tku-eligibility.js"]),
        ("diff-check", ["git", "diff", "--check"]),
        ("recovered-wrapper-collection", [sys.executable, "-m", "pytest", "tests/test_content_governance_wrapper.py", "--collect-only", "-q", f"--junitxml={out / 'wrapper.xml'}"]),
        ("lockfile", ["uv", "lock", "--check"]),
    ]
    if args.actionlint_binary:
        checks.append(('actionlint', [str(args.actionlint_binary.resolve()), '.github/workflows/quality.yml']))
    report = dict(browser_files=BROWSERS,
        unit_file_count=len(units), deliberately_not_run=["tests/integration/test_local_ai_runtime.py: unrelated Ollama hardware/runtime integration"], checks=[])
    exit_code = execute_checks(ROOT, out, commit, checks, env, report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True, help="Exact full HEAD SHA; requires a clean unchanged worktree")
    parser.add_argument('--actionlint-binary', type=Path, help='Explicit locally verified actionlint binary')
    sys.exit(run(parser.parse_args()))

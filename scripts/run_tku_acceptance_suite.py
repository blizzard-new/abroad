"""Run the final candidate checks together, retaining actual failures and skips.

All top-level Python tests plus relevant real-browser suites run in one pytest
invocation. The inherited missing-pyc wrapper is attempted separately, recorded
as a collection error, and never counted as passing. No source refresh or deploy.
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
    "test_planning_workspace.py"]


def run(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
        TKU_ACCEPTANCE_OUTPUT=str(out / "browser"), TKU_SWITCH_OUTPUT=str(out / "switch.json"))
    units = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "tests").glob("test_*.py"))
        if p.name != "test_content_governance_wrapper.py"]
    browser = [f"tests/e2e/{name}" for name in BROWSERS]
    browser += ["tests/e2e/test_web_next_phase.py::test_application_form_sync_review_and_pdf_download"]
    checks = [
        ("pytest-unit-and-browser", [sys.executable, "-m", "pytest", *units, *browser, "-q", "-ra", f"--junitxml={out / 'suite.xml'}"]),
        ("tku-switching-and-details", [sys.executable, "scripts/check_tku_target_switching.py"]),
        ("openapi", [sys.executable, "scripts/export_openapi.py", "--check"]),
        ("javascript-shared", ["node", "--check", "src/exchange_info/static/app.js"]),
        ("javascript-tku", ["node", "--check", "src/exchange_info/static/tku-academic-units.js"]),
        ("diff-check", ["git", "diff", "--check"]),
        ("inherited-wrapper-collection", [sys.executable, "-m", "pytest", "tests/test_content_governance_wrapper.py", "--collect-only", "-q", f"--junitxml={out / 'wrapper.xml'}"]),
        ("lockfile", ["uv", "lock", "--check"]),
    ]
    report = dict(tested_commit=commit, started_at=time.time(), browser_files=BROWSERS,
        unit_file_count=len(units), deliberately_not_run=["tests/integration/test_local_ai_runtime.py: unrelated Ollama hardware/runtime integration"], checks=[])
    for name, command in checks:
        print(f"Running {name} at {commit}", flush=True)
        start = time.time()
        log = out / f"{name}.log"
        with log.open("w") as handle:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT)
        report["checks"].append(dict(name=name, command=command, exit_code=result.returncode,
            elapsed_seconds=round(time.time() - start, 2), log=str(log)))
        print(f"{name}: actual exit {result.returncode}; {log}", flush=True)
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    report["ended_at"] = time.time()
    report["ending_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    report["ending_worktree_status"] = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())

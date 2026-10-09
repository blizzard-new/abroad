"""Compare unchanged historical failing tests against immutable main on this runner.

This diagnostic does not waive candidate failures. Both JUnit and actual pytest
exit code are retained. Infrastructure/collection errors fail this command;
ordinary baseline assertion failures are diagnostic results, not a CI gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

MAIN = "f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59"
HISTORICAL = "4e6cabd073e4792f94959545efeb4e323fefc3f5"
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=int, choices=range(4), required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    # Only read Git objects in the candidate checkout; all extraction and test
    # writes stay in this shard's ephemeral, isolated directory.
    for commit in (MAIN, HISTORICAL):
        if subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT, capture_output=True).returncode:
            subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", commit], cwd=ROOT, check=True)
    snapshot = json.loads((ROOT / "scripts/tku_ci_prior_failures.json").read_text())
    assert snapshot["source_commit"] == HISTORICAL
    partition = json.loads((evidence.parent / "partition.json").read_text())
    assert partition["shard"] == args.shard
    assigned_files = set(partition["files_per_shard"][args.shard])
    cases = [row["id"] for row in snapshot["failures"]
             if row["id"].split("::", 1)[0] in assigned_files
             and not row["id"].startswith("tests/e2e/test_tku_acceptance.py::")]
    (evidence / "collect-nodeids.txt").write_text("\n".join(cases) + "\n")
    control = Path(os.environ.get("RUNNER_TEMP", str(evidence.parent.parent))) / f"tku-main-control-checkout-{args.shard}"
    control.mkdir(exist_ok=False)
    for commit, paths in ((MAIN, ["src", "data", "pyproject.toml"]),
                          (HISTORICAL, ["tests", "conftest.py"])):
        archive = control.parent / f"control-{args.shard}-{commit[:7]}.tar"
        subprocess.run(["git", "archive", "-o", str(archive), commit, *paths], cwd=ROOT, check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(control, filter="data")
        archive.unlink()
    environment = {**os.environ, "PYTHONPATH": str(control / "src"),
                   "EXCHANGE_INFO_DATA_DIR": str(control / "isolated-data")}
    source = subprocess.check_output([sys.executable, "-c", "import exchange_info.api as api; print(api.__file__)"],
                                     cwd=control, env=environment, text=True).strip()
    assert Path(source).resolve().is_relative_to(control / "src"), source
    command = [sys.executable, "-m", "pytest", *cases, "-vv", "--tb=short", "--durations=20",
               "-o", f"pythonpath={control / 'src'}", f"--junitxml={evidence / 'suite.xml'}"]
    start = time.monotonic()
    with (evidence / "pytest.log").open("w") as log:
        result = subprocess.run(command, cwd=control, env=environment, stdout=log, stderr=subprocess.STDOUT)
    record = dict(baseline_commit=MAIN, unchanged_test_source_commit=HISTORICAL,
                  candidate_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  shard=args.shard, cases=cases, actual_api_source=source,
                  assignment_source="current candidate partition; each historical case stays on the same job as its candidate",
                  pytest_exit_code=result.returncode, elapsed_seconds=time.monotonic()-start,
                  comparison_environment="same job, interpreter, installed packages, browser and system dependencies",
                  acceptance_waiver=False, log_sha256=hashlib.sha256((evidence / "pytest.log").read_bytes()).hexdigest())
    (evidence / "result.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(record, ensure_ascii=False), flush=True)
    # The immutable diagnostic files above are the deliverable, not this shell
    # status. Never disguise errors that prevented cases from being exercised.
    return 0 if result.returncode in (0, 1) else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

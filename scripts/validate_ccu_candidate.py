"""Run the CCU acceptance gate on one clean SHA; save evidence outside the clone.

No publication, deployment, school login, application submission or branch merge.
Exit nonzero for any failed check; known baseline failures are still failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
sys.path.insert(0, str(ROOT / "src"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def data_proof():
    sources = json.loads((BUNDLE / "overseas-source-registry.json").read_text())
    assert len(sources) == len({s["source_id"] for s in sources})
    previous = json.loads((BUNDLE / "twentythird-source-review.json").read_text())
    for sid, digest in previous["prior_snapshot_hashes"].items():
        assert sha(BUNDLE / "overseas_sources" / (sid + ".json")) == digest, sid
    with_hash = 0
    attachments = 0
    for source in sources:
        raw = json.loads((BUNDLE / "overseas_sources" / (source["source_id"] + ".json")).read_text())
        if raw.get("text_sha256"):
            assert hashlib.sha256(json.dumps(raw.get("text_pages", []), ensure_ascii=False).encode()).hexdigest() == raw["text_sha256"], source["source_id"]
            with_hash += 1
        if raw.get("bundled_file"):
            assert sha(BUNDLE / raw["bundled_file"]) == raw["sha256"], source["source_id"]
            attachments += 1
    main_files = git("ls-tree", "-r", "--name-only", "origin/main", "src/exchange_info/official_data").splitlines()
    for path in main_files:
        original = subprocess.check_output(["git", "show", "origin/main:" + path], cwd=ROOT)
        assert (ROOT / path).read_bytes() == original, path
    from exchange_info.content_governance import workflow_content_hash
    from exchange_info.models import UniversityApplicationWorkflow
    from exchange_info.workflow_structuring import structure_application_workflow

    baseline_hashes = json.loads((ROOT / "docs/ccu-validation-2026-10-08/twentysecond-published-hash-proof.json").read_text())
    assert baseline_hashes["baseline_main"] == git("rev-parse", "origin/main")
    published_hashes = {}
    for line in (ROOT / "src/exchange_info/official_data/cgu/application_workflows.jsonl").read_text().splitlines():
        workflow = UniversityApplicationWorkflow.model_validate_json(line)
        if workflow.review_status == "published":
            published_hashes[workflow.school_name] = workflow_content_hash(structure_application_workflow(workflow))
    assert len(published_hashes) == 77 and published_hashes == baseline_hashes["sha256"]
    from exchange_info.ccu_documents import reviewed_documents
    from exchange_info.ccu_overseas import reviewed_rows
    from exchange_info.ccu_profile import reviewed_profiles
    from exchange_info.ccu_student_view import fetch_ccu_partner_universities

    partners = fetch_ccu_partner_universities()
    assert len(partners) == len({p.school_name for p in partners}) == 104
    assert len(reviewed_rows()) == len(reviewed_profiles()) == 55
    documents = reviewed_documents()
    assert len(documents) == 32
    contract = json.loads((ROOT / "docs/api/openapi.json").read_text())
    main_contract = json.loads(subprocess.check_output(["git", "show", "origin/main:docs/api/openapi.json"], cwd=ROOT))
    assert contract["paths"].keys() == main_contract["paths"].keys()
    existing_changes = []
    for key, original in main_contract["components"]["schemas"].items():
        current = contract["components"]["schemas"][key]
        assert current.get("required", []) == original.get("required", []), key
        if current != original:
            existing_changes.append(key)
    return {"candidate_sha": git("rev-parse", "HEAD"), "main_sha": git("rev-parse", "origin/main"), "source_count": len(sources), "prior_sources_byte_identical": len(previous["prior_snapshot_hashes"]), "source_text_hashes_verified": with_hash, "sources_without_text_hash": len(sources) - with_hash, "bundled_source_files_hash_verified": attachments, "all_main_official_data_files_byte_identical": len(main_files), "published_cgu_hashes_identical_to_independent_main_proof": len(published_hashes), "catalogue_rows": len(partners), "reviewed_host_rows": 55, "host_document_schools": len(documents), "api_paths_preserved": len(contract["paths"]), "existing_schema_changes": existing_changes, "existing_required_fields_preserved": True, "new_schemas": sorted(set(contract["components"]["schemas"]) - set(main_contract["components"]["schemas"])), "full_openapi_identical_to_main": contract == main_contract}


def suite_stats(path):
    suites = ElementTree.parse(path).getroot()
    return {key: sum(float(s.attrib.get(key, 0)) if key == "time" else int(s.attrib.get(key, 0)) for s in suites.findall("testsuite")) for key in ["tests", "failures", "errors", "skipped", "time"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Evidence output must be outside the clone so final checks keep the same SHA")
    initial = git("status", "--porcelain")
    if initial:
        parser.error("Commit the candidate first; this gate requires a clean working tree")
    output.mkdir(parents=True, exist_ok=True)
    candidate = git("rev-parse", "HEAD")
    environment = {**os.environ, "UV_CACHE_DIR": "/tmp/ccu-uv-cache", "UV_TOOL_DIR": "/tmp/ccu-uv-tools", "UV_TOOL_BIN_DIR": "/tmp/ccu-uv-bin", "PLAYWRIGHT_BROWSERS_PATH": "/tmp/ccu-playwright", "CCU_ACCEPTANCE_OUTPUT": str(output / "browser-evidence")}
    results = []

    def run(label, command):
        started = time.monotonic()
        print("START", label, flush=True)
        with (output / (label + ".txt")).open("w") as log:
            result = subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT, check=False)
        row = {"label": label, "command": command, "returncode": result.returncode, "seconds": round(time.monotonic() - started, 3), "candidate_sha": candidate}
        print("END", label, result.returncode, flush=True)
        return row

    before = {str(p.relative_to(BUNDLE)): sha(p) for p in BUNDLE.rglob("*") if p.is_file()}
    for script in ["build_ccu_research_audit", "build_ccu_catalog", "build_ccu_source_audit", "build_ccu_overseas", "build_ccu_remaining_gaps", "build_ccu_public_link_queue"]:
        results.append(run(script, [sys.executable, "scripts/" + script + ".py"]))
    after = {str(p.relative_to(BUNDLE)): sha(p) for p in BUNDLE.rglob("*") if p.is_file()}
    assert before == after, "Offline builders changed candidate data"
    save(output / "deterministic-proof.json", {"candidate_sha": candidate, "ccu_files_byte_identical": len(before), "sha256": after})
    save(output / "data-compatibility-proof.json", data_proof())
    quick = [("lock", ["uvx", "--from", "uv==0.11.26", "uv", "lock", "--check"]), ("openapi", [sys.executable, "scripts/export_openapi.py", "--check"]), ("python-syntax", [sys.executable, "-m", "compileall", "-q", "src", "scripts/validate_ccu_candidate.py"]), ("ruff", ["uvx", "ruff", "check", "scripts/fetch_ccu_overseas_sources.py", "scripts/validate_ccu_candidate.py", "src/exchange_info/ccu_overseas.py", "src/exchange_info/ccu_profile.py", "tests/test_ccu_twentythird_pass.py", "tests/e2e/test_ccu_candidate_acceptance.py"])]
    for path in ["app.js", "ccu-academic-units.js", "ccu-language-conditions.js", "ccu-partner-details.js"]:
        quick.append(("js-" + path, ["node", "--check", "src/exchange_info/static/" + path]))
    for label, command in quick:
        results.append(run(label, command))
    regression = sorted({str(p.relative_to(ROOT)) for p in (ROOT / "tests").glob("test_ccu*.py")} | {"tests/" + name for name in ["test_advisor.py", "test_application_document_catalog.py", "test_application_documents_api.py", "test_application_rules.py", "test_application_workflow.py", "test_cgu_bundled_data.py", "test_ntpu_bundled_data.py", "test_ntpu_support.py", "test_ntu_audit.py", "test_ntu_integration.py", "test_ntu_school_board_migration.py", "test_qualification_scope_consistency.py", "test_school_photo_and_match.py", "test_selection_conditions_sync.py", "test_workflow_structuring.py", "test_account_workspace_api.py"]})
    browser = sorted({str(p.relative_to(ROOT)) for p in (ROOT / "tests/e2e").glob("test_ccu*.py")} | {"tests/e2e/test_ntu_school.py", "tests/e2e/test_school_lists.py", "tests/e2e/test_open_catalog.py"})
    save(output / "test-selection.json", {"regression": regression, "browser": browser, "true_bundled_four_school_browser_file": "tests/e2e/test_ccu_candidate_acceptance.py", "other_browser_fixtures": "Existing e2e conftest replaces CGU partner list; CCU data/API is real. New acceptance file has an independent real production-data server and no response/state mocks."})
    long = [("regression", [sys.executable, "-m", "pytest", "-q", *regression, "--junitxml=" + str(output / "regression.xml")]), ("browser", [sys.executable, "-m", "pytest", "-q", *browser, "--junitxml=" + str(output / "browser.xml")]), ("functional-parity", [sys.executable, "scripts/build_ccu_functional_parity.py", "--output", str(output / "functional-parity.json")]), ("wheel", ["uvx", "--from", "uv==0.11.26", "uv", "build", "--wheel", "--out-dir", str(output / "wheel")])]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results.extend(pool.map(lambda pair: run(*pair), long))
    wheels = list((output / "wheel").glob("*.whl"))
    if len(wheels) == 1:
        with zipfile.ZipFile(wheels[0]) as archive:
            for path in BUNDLE.rglob("*"):
                if path.is_file():
                    assert archive.read(str(path.relative_to(ROOT / "src"))) == path.read_bytes(), path
        save(output / "wheel-proof.json", {"candidate_sha": candidate, "wheel": wheels[0].name, "sha256": sha(wheels[0]), "ccu_files_byte_identical": len(after)})
    if (ROOT / "build").exists():
        shutil.move(str(ROOT / "build"), str(output / "setuptools-build"))
    for label in ["regression", "browser"]:
        if (output / (label + ".xml")).exists():
            next(r for r in results if r["label"] == label)["junit"] = suite_stats(output / (label + ".xml"))
    final = git("status", "--porcelain")
    assert git("rev-parse", "HEAD") == candidate and not final, "Candidate changed during gate"
    summary = {"repository": "blizzard-new/abroad", "branch": git("branch", "--show-current"), "candidate_sha": candidate, "main_sha": git("rev-parse", "origin/main"), "same_sha_before_and_after": True, "working_tree_clean_before_and_after": True, "results": results, "all_executed_commands_passed": all(r["returncode"] == 0 for r in results), "not_run": ["other-school combined branch integration", "delayed-response race across unmerged TKU/NCU/NTU heads", "Supabase isolated runtime", "dependency vulnerability audit", "deployment"], "functional_parity_complete": json.loads((output / "functional-parity.json").read_text())["status_summary"]["functional_parity_complete"], "external_browser_template_checks": [json.loads(p.read_text()) for p in (output / "browser-evidence").glob("external-template-*.json")]}
    summary["ready_for_release"] = False
    save(output / "final-validation-summary.json", summary)
    print(json.dumps({"candidate_sha": candidate, "evidence": str(output), "all_executed_commands_passed": summary["all_executed_commands_passed"], "ready_for_release": False}, ensure_ascii=False), flush=True)
    raise SystemExit(0 if summary["all_executed_commands_passed"] else 1)


if __name__ == "__main__":
    main()

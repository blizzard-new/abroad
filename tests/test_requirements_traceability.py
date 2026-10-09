from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TRACEABILITY_PATH = REPOSITORY_ROOT / "docs" / "requirements-traceability.md"
QUALITY_WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "quality.yml"

EXPECTED_SPEC_IDS = {
    "SPEC-06.1",
    "SPEC-06.2",
    "SPEC-06.3",
    "SPEC-07.1",
    "SPEC-07.2",
    "SPEC-08.1",
    "SPEC-08.2",
    "SPEC-08.3",
    "SPEC-08.4",
    "SPEC-09.1",
    "SPEC-09.2",
    "SPEC-09.3",
    "SPEC-09.4",
    "SPEC-09.5",
    "SPEC-10.1",
    "SPEC-10.2",
    "SPEC-11.1",
    "SPEC-11.2",
    "SPEC-11.3",
    "SPEC-12.1",
    "SPEC-12.2",
    "SPEC-13",
    "SPEC-14.1",
    "SPEC-14.2",
    "SPEC-15.A",
    "SPEC-15.B",
    "SPEC-15.C",
    "SPEC-15.D",
    "SPEC-15.E",
    "SPEC-15.F",
    "SPEC-16",
    "SPEC-17",
    "SPEC-18",
    "SPEC-19",
}

ALLOWED_STATUSES = {
    "已實作",
    "進行中",
    "暫緩",
    "待人工",
    "受核准封鎖",
    "待封測",
    "受前置封鎖",
    "非目標",
}


def _traceability_rows() -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in TRACEABILITY_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| SPEC-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 8, f"Traceability row must have 8 columns: {line}"
        assert cells[0] not in rows, f"Duplicate traceability ID: {cells[0]}"
        rows[cells[0]] = cells
    return rows


def test_product_spec_sections_6_through_19_have_owned_evidence_rows() -> None:
    rows = _traceability_rows()

    assert set(rows) == EXPECTED_SPEC_IDS
    for spec_id, cells in rows.items():
        assert all(cells), f"Traceability row has an empty cell: {spec_id}"
        assert cells[2] != "—", f"Traceability row has no responsible task: {spec_id}"
        assert cells[3] in ALLOWED_STATUSES
        assert cells[6] != "—", f"Traceability row has no evidence: {spec_id}"
        assert cells[7] != "—", f"Traceability row has no next gate: {spec_id}"


def test_traceability_preserves_local_ai_scope_and_web_first_app_gate() -> None:
    rows = _traceability_rows()

    assert rows["SPEC-11.1"][3] == "進行中"
    assert rows["SPEC-11.2"][3] == "進行中"
    assert rows["SPEC-11.3"][3] == "受核准封鎖"
    assert rows["SPEC-15.D"][3] == "受核准封鎖"
    assert rows["SPEC-18"][3] == "非目標"
    text = TRACEABILITY_PATH.read_text(encoding="utf-8")
    assert "本機 AI 只核准 LAI-00～LAI-03 的隔離 provider 基礎" in text
    assert "Advisor／RAG／文件／Web／production 串接仍維持 `paused`" in text
    assert "Flutter 只有在 Web 完成 C-03 並取得明確核准後才能開始" in text


def test_quality_workflow_runs_isolated_web_checks_and_contract_guard() -> None:
    workflow = QUALITY_WORKFLOW_PATH.read_text(encoding="utf-8")

    for required in (
        "EXCHANGE_INFO_DATA_DIR={os.environ['RUNNER_TEMP']}/exchange-info-tests",
        'Path(os.environ["GITHUB_ENV"]).open("a")',
        "python -m pip install --disable-pip-version-check uv==0.11.26",
        "uv lock --check",
        "uv sync --frozen --extra dev",
        "uv run --frozen python -m compileall -q src",
        "node --check src/exchange_info/static/app.js",
        "node --check src/exchange_info/static/content-review.js",
        "uv run --frozen python scripts/export_openapi.py --check",
        "uv run --frozen python scripts/audit_python_dependencies.py",
        "uv run --frozen python scripts/validate_tku_community_runtime.py",
        'uv run --frozen python scripts/run_web_quality_tests.py --shard "$WEB_TEST_SHARD" --shards 4',
        "fail-fast: false",
        "shard: [0, 1, 2, 3]",
        "git diff --exit-code -- src/exchange_info/official_data",
    ):
        assert required in workflow
    assert 'EXCHANGE_INFO_DATA_DIR: ${{ runner.temp }}' not in workflow
    runtime_step = "- name: Validate isolated Supabase runtime"
    runtime_command = "uv run --frozen python scripts/validate_tku_community_runtime.py"
    assert workflow.count(runtime_step) == 1
    assert workflow.count(runtime_command) == 1
    assert "\n    timeout-minutes: 45\n" in workflow

    migration_position = workflow.index(
        "uv run --frozen python scripts/validate_supabase_migrations.py"
    )
    dependency_audit_position = workflow.index(
        "uv run --frozen python scripts/audit_python_dependencies.py"
    )
    runtime_position = workflow.index(runtime_step)
    pytest_position = workflow.index("uv run --frozen python scripts/run_web_quality_tests.py")
    assert migration_position < dependency_audit_position < runtime_position < pytest_position

    runtime_block = workflow[runtime_position:pytest_position]
    assert "timeout-minutes: 20" in runtime_block
    assert runtime_command in runtime_block
    assert "continue-on-error" not in runtime_block
    assert "--keep" not in runtime_block
    assert "pip install -e" not in workflow
    assert "mobile_flutter" not in workflow
    assert "flutter " not in workflow.lower()

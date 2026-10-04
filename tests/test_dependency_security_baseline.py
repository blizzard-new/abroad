from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
import tomllib

from scripts import audit_python_dependencies


ROOT = Path(__file__).resolve().parents[1]


def test_cryptography_security_floor_is_locked() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_dependencies = project["project"]["dependencies"]
    dev_dependencies = project["project"]["optional-dependencies"]["dev"]

    assert "cryptography>=50.0.1,<51.0.0" in runtime_dependencies
    assert "pip-audit==2.10.1" in dev_dependencies

    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked_versions = {
        package["version"]
        for package in lock["package"]
        if package["name"] == "cryptography"
    }
    assert locked_versions == {"50.0.1"}


def test_starlette_testclient_uses_locked_httpx2_without_deprecated_fallback() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = project["project"]["optional-dependencies"]["dev"]

    assert "httpx>=0.27.0" in dev_dependencies
    assert "httpx2>=2.0.0,<3.0.0" in dev_dependencies

    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked_versions = {
        package["version"]
        for package in lock["package"]
        if package["name"] == "httpx2"
    }
    assert locked_versions == {"2.12.0"}

    completed = subprocess.run(
        [
            sys.executable,
            "-W",
            "error",
            "-c",
            (
                "from fastapi.testclient import TestClient; "
                "import starlette.testclient as module; "
                "assert module.httpx.__name__ == 'httpx2'"
            ),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_quality_workflow_enforces_dependency_audit() -> None:
    workflow = (ROOT / ".github" / "workflows" / "quality.yml").read_text(
        encoding="utf-8"
    )

    assert "Audit runtime dependencies for known vulnerabilities" in workflow
    assert "uv run --frozen python scripts/audit_python_dependencies.py" in workflow


def test_quality_workflow_installs_the_frozen_lock_environment() -> None:
    workflow = (ROOT / ".github" / "workflows" / "quality.yml").read_text(
        encoding="utf-8"
    )

    assert "python -m pip install --disable-pip-version-check uv==0.11.26" in workflow
    assert "uv lock --check" in workflow
    assert "uv sync --frozen --extra dev" in workflow
    assert "uv run --frozen python -m playwright install --with-deps chromium" in workflow
    assert "pip install -e" not in workflow


def test_quality_workflow_pins_external_actions_to_full_commit_shas() -> None:
    workflow = (ROOT / ".github" / "workflows" / "quality.yml").read_text(
        encoding="utf-8"
    )
    expected = [
        ("actions/checkout", "11d5960a326750d5838078e36cf38b85af677262"),
        ("actions/setup-python", "a26af69be951a213d495a4c3e4e4022e16d87065"),
        ("actions/setup-node", "49933ea5288caeca8642d1e84afbd3f7d6820020"),
    ]
    actual = re.findall(r"^\s*uses:\s+([^@\s]+)@([^\s#]+)", workflow, re.MULTILINE)

    assert actual == expected
    assert all(re.fullmatch(r"[0-9a-f]{40}", revision) for _, revision in actual)


def test_dependency_audit_launcher_forces_utf8_and_propagates_exit_code(
    monkeypatch,
) -> None:
    recorded: dict[str, object] = {}

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded.update(kwargs)
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(audit_python_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(audit_python_dependencies.sys, "executable", "python-test")
    monkeypatch.setenv("PYTHONUTF8", "0")

    assert audit_python_dependencies.main() == 7
    assert recorded["command"] == [
        "python-test",
        "-m",
        "pip_audit",
        ".",
        "--strict",
        "--progress-spinner",
        "off",
    ]
    assert recorded["cwd"] == audit_python_dependencies.REPOSITORY_ROOT
    assert recorded["env"]["PYTHONUTF8"] == "1"
    assert recorded["check"] is False

"""Run the pinned dependency audit with a Windows-safe UTF-8 child process."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from collections.abc import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AUDIT_ARGUMENTS = (".", "--strict", "--progress-spinner", "off")


def audit_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return an environment that keeps pip output UTF-8 on Windows paths."""

    environment = dict(os.environ if source is None else source)
    environment["PYTHONUTF8"] = "1"
    return environment


def main() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "pip_audit", *AUDIT_ARGUMENTS],
        cwd=REPOSITORY_ROOT,
        env=audit_environment(),
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

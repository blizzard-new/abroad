"""update.ps1 must find what stops a fast-forward, change nothing until told to, and lose nothing.

These run the real scripts in PowerShell against throwaway git repositories (an origin, a developer clone that pushes, and the
"server" clone being updated). They are skipped when no PowerShell is installed; set PWSH to point at one.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "deploy" / "selfhost" / "scripts"
PWSH = os.environ.get("PWSH") or shutil.which("pwsh") or shutil.which("powershell")

pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell is not installed")

CJK = "xlsx_大洋洲 Oceania.json"      # the kind of name that slipped past the first hand-written fix
GLOB = "a[1].json"                    # looks like a pattern; must be treated literally
CJK_TRACKED = "docs/申請說明.md"


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return done.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


class World:
    def __init__(self, base: Path) -> None:
        self.base = base
        self.home = base / "uniway"
        self.home.mkdir()
        origin = base / "origin.git"
        git(base, "init", "--bare", "-q", "-b", "main", str(origin))
        self.dev = base / "dev"
        git(base, "clone", "-q", str(origin), str(self.dev))
        for key, value in (("user.email", "dev@example.com"), ("user.name", "dev")):
            git(self.dev, "config", key, value)
        scripts = self.dev / "deploy" / "selfhost" / "scripts"
        scripts.mkdir(parents=True)
        for name in ("lib.ps1", "update.ps1"):
            shutil.copy(SCRIPTS / name, scripts / name)
        stub = "param([switch]$SkipCloud)\nNew-Item -ItemType File -Force -Path (Join-Path $env:UNIWAY_HOME '{marker}') | Out-Null\nexit 0\n"
        for name, marker in (("backup.ps1", "backup-ran"), ("03-start.ps1", "start-ran"), ("verify.ps1", "verify-ran")):
            write(scripts / name, stub.format(marker=marker))
        write(self.dev / "app.py", "print('v1')\n")
        write(self.dev / "static" / "index.html", "<p>v1</p>\n")
        write(self.dev / "notes" / "keep.txt", "unrelated v1\n")
        write(self.dev / CJK_TRACKED, "說明 v1\n")
        git(self.dev, "add", "-A")
        git(self.dev, "commit", "-q", "-m", "first")
        git(self.dev, "push", "-q", "origin", "main")
        self.server = base / "server"
        git(base, "clone", "-q", str(origin), str(self.server))
        for key, value in (("user.email", "ops@example.com"), ("user.name", "ops")):
            git(self.server, "config", key, value)
        # the next release: edits two files, adds three that the server already has by hand
        write(self.dev / "app.py", "print('v2')\n")
        write(self.dev / "static" / "index.html", "<p>v2</p>\n")
        write(self.dev / CJK_TRACKED, "說明 v2\n")
        for name in (CJK, GLOB, "plain.json"):
            write(self.dev / "sources" / "nchu" / name, f"official {name}\n")
        git(self.dev, "add", "-A")
        git(self.dev, "commit", "-q", "-m", "second")
        git(self.dev, "push", "-q", "origin", "main")

    def hand_made_files(self) -> None:
        for name in (CJK, GLOB, "plain.json"):
            write(self.server / "sources" / "nchu" / name, f"hand made {name}\n")

    def hand_edits(self) -> None:
        write(self.server / "app.py", "print('hand edit')\n")
        write(self.server / CJK_TRACKED, "說明 手動修改\n")
        write(self.server / "notes" / "keep.txt", "unrelated hand edit\n")

    def run(self, *flags: str, branch: str = "main") -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "UNIWAY_HOME": str(self.home)}
        return subprocess.run(
            [PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.server / "deploy" / "selfhost" / "scripts" / "update.ps1"), "-Branch", branch, *flags],
            capture_output=True, text=True, encoding="utf-8", env=env, cwd=self.server, timeout=300,
        )

    def ran(self, marker: str) -> bool:
        return (self.home / marker).exists()

    def read(self, relative: str) -> str:
        return (self.server / relative).read_text(encoding="utf-8")


@pytest.fixture()
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def test_check_only_names_every_blocker_including_chinese_and_pattern_like_names_and_changes_nothing(world: World) -> None:
    world.hand_made_files()
    world.hand_edits()
    before = {p: world.read(p) for p in ("app.py", CJK_TRACKED, "notes/keep.txt", f"sources/nchu/{CJK}")}

    result = world.run("-CheckOnly")

    assert result.returncode == 1, result.stdout + result.stderr
    out = result.stdout
    for name in (CJK, GLOB, "plain.json", "app.py", CJK_TRACKED):
        assert name in out, name
    assert "3 file(s) the update adds already exist here" in out
    assert "2 file(s) the update changes were also edited" in out
    assert "1 other local change(s) are not in the way and will be left alone" in out
    assert "notes/keep.txt" in out.split("will be left alone")[1]
    assert "Check only: nothing was changed" in out
    assert {p: world.read(p) for p in before} == before
    assert not world.ran("backup-ran")


def test_without_set_aside_it_stops_before_the_backup_and_says_how_to_continue(world: World) -> None:
    world.hand_made_files()

    result = world.run()

    assert result.returncode == 1
    assert "Nothing was changed" in result.stdout
    assert "update.ps1 -SetAside" in result.stdout
    assert not world.ran("backup-ran"), "the backup must not start while the update is going to stop"
    assert world.read(f"sources/nchu/{CJK}") == f"hand made {CJK}\n"


def test_set_aside_keeps_every_file_in_a_backup_folder_and_then_fast_forwards(world: World) -> None:
    world.hand_made_files()
    world.hand_edits()

    result = world.run("-SetAside")

    assert result.returncode == 0, result.stdout + result.stderr
    assert git(world.server, "rev-parse", "HEAD") == git(world.server, "rev-parse", "origin/main")
    assert world.read("app.py") == "print('v2')\n"
    assert world.read(CJK_TRACKED) == "說明 v2\n"
    for name in (CJK, GLOB, "plain.json"):
        assert world.read(f"sources/nchu/{name}") == f"official {name}\n"
    assert world.read("notes/keep.txt") == "unrelated hand edit\n", "an edit that was not in the way must stay"
    assert world.ran("backup-ran") and world.ran("start-ran") and world.ran("verify-ran")
    assert "set aside 2 edited and 3 untracked file(s)" in result.stdout

    folders = list((world.home / "backups").glob("update-set-aside-*"))
    assert len(folders) == 1
    saved = folders[0]
    for name in (CJK, GLOB, "plain.json"):
        assert (saved / "untracked-files" / "sources" / "nchu" / name).read_text(encoding="utf-8") == f"hand made {name}\n"
    assert (saved / "edited-files" / "app.py").read_text(encoding="utf-8") == "print('hand edit')\n"
    assert (saved / "edited-files" / "docs" / "申請說明.md").read_text(encoding="utf-8") == "說明 手動修改\n"
    assert not (saved / "edited-files" / "notes").exists()
    assert "Commit before the update" in (saved / "README.txt").read_text(encoding="utf-8")


def test_a_clean_folder_just_updates_and_makes_no_set_aside_folder(world: World) -> None:
    result = world.run()

    assert result.returncode == 0, result.stdout + result.stderr
    assert "nothing is in the way" in result.stdout
    assert world.ran("backup-ran") and world.ran("verify-ran")
    assert world.read("app.py") == "print('v2')\n"
    assert not (world.home / "backups").exists()


def test_a_local_edit_that_the_update_does_not_touch_does_not_block_it(world: World) -> None:
    write(world.server / "notes" / "keep.txt", "unrelated hand edit\n")

    check = world.run("-CheckOnly")
    result = world.run()

    assert check.returncode == 0, check.stdout
    assert "nothing is in the way" in check.stdout and "will be left alone" in check.stdout
    assert result.returncode == 0, result.stdout + result.stderr
    assert world.read("notes/keep.txt") == "unrelated hand edit\n"


@pytest.mark.parametrize("flag", [[], ["-SetAside"]])
def test_the_wrong_branch_is_never_fixed_automatically(world: World, flag: list[str]) -> None:
    git(world.server, "switch", "-q", "-c", "side-work")
    world.hand_made_files()

    result = world.run(*flag)

    assert result.returncode == 1
    assert "is on branch 'side-work', but the update is for 'main'" in result.stdout
    assert "git switch main" in result.stdout
    assert not world.ran("backup-ran")
    assert world.read(f"sources/nchu/{CJK}") == f"hand made {CJK}\n"


@pytest.mark.parametrize("flag", [[], ["-SetAside"]])
def test_commits_that_are_not_on_github_stop_the_update_and_nothing_is_moved(world: World, flag: list[str]) -> None:
    write(world.server / "local-only.txt", "kept in a local commit\n")
    git(world.server, "add", "local-only.txt")
    git(world.server, "commit", "-q", "-m", "local work")
    world.hand_made_files()

    result = world.run(*flag)

    assert result.returncode == 1
    assert "not on origin/main" in result.stdout and "local work" in result.stdout
    assert not world.ran("backup-ran")
    assert world.read(f"sources/nchu/{CJK}") == f"hand made {CJK}\n"


def test_a_staged_new_file_in_the_way_is_reported_not_moved(world: World) -> None:
    write(world.server / "sources" / "nchu" / "plain.json", "staged by hand\n")
    git(world.server, "add", "sources/nchu/plain.json")

    result = world.run("-SetAside")

    assert result.returncode == 1
    assert "staged here but not committed" in result.stdout and "git restore --staged" in result.stdout
    assert "cannot be fixed automatically" in result.stdout
    assert world.read("sources/nchu/plain.json") == "staged by hand\n"
    assert not world.ran("backup-ran")


def test_chinese_names_survive_a_console_that_decodes_output_in_another_encoding(world: World, tmp_path: Path) -> None:
    """The first hand-written fix missed these: PowerShell decoded git's UTF-8 names with the console code page."""

    world.hand_made_files()
    git(world.server, "fetch", "-q", "origin", "main")
    lib = (SCRIPTS / "lib.ps1").as_posix()
    command = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding('iso-8859-1'); "
        f". '{lib}'; "
        f"$info = Get-UpdateBlockers '{world.server.as_posix()}' 'main'; "
        "Write-Output ('NAMES=' + ((@($info.UntrackedBlockers) | ForEach-Object { [uri]::EscapeDataString($_) }) -join '|')); "
        "Write-Output ('ENCODING=' + [Console]::OutputEncoding.WebName)"
    )
    done = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-Command", command], capture_output=True, text=True, encoding="utf-8", timeout=120)

    assert done.returncode == 0, done.stdout + done.stderr
    lines = dict(line.split("=", 1) for line in done.stdout.splitlines() if "=" in line)
    names = [unquote(name) for name in lines["NAMES"].split("|")]
    assert sorted(names) == sorted(f"sources/nchu/{name}" for name in (CJK, GLOB, "plain.json"))
    assert lines["ENCODING"] == "iso-8859-1", "the console encoding must be put back afterwards"

#!/usr/bin/env python3
"""UniWay 本機測試版（離線）：把某個分支／PR／正式版程式碼拉到自己的電腦跑，資料全是虛構的。

用法（在專案根目錄）：
  python scripts/staging.py up                 # 正式版（origin/main）
  python scripts/staging.py up --pr 211        # 某個 PR 的最新內容
  python scripts/staging.py up --branch claude/funny-dirac-43frw3
  python scripts/staging.py up --here          # 直接跑你目前資料夾（含還沒 commit 的修改）
  python scripts/staging.py up --pr 211 --watch   # 每 30 秒檢查一次，PR 有新 commit 就自動更新並重啟
  python scripts/staging.py reset              # 清空測試資料（下次啟動會重建虛構帳號）
  python scripts/staging.py clean              # 刪掉整個 .staging（程式副本、虛擬環境、資料）
  python scripts/staging.py status

所有檔案都放在 .staging/（已加入 .gitignore）。這個工具不會改動你的工作目錄，不會連到 Supabase／Render，
也不會讀取正式環境的任何資料或密鑰。細節見 docs/staging-local-test.md。
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
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STAGING = REPO / ".staging"
APP = STAGING / "app"
VENV = STAGING / "venv"
DATA = STAGING / "data"
STATE = STAGING / "state.json"
RUNNER = REPO / "scripts" / "staging_runner.py"
VENV_PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def sh(*cmd: str, cwd: Path = REPO, capture: bool = False) -> str:
    result = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=capture)
    return (result.stdout or "").strip()


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(**values: object) -> None:
    STAGING.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({**load_state(), **values}, ensure_ascii=False, indent=1), encoding="utf-8")


def resolve(args: argparse.Namespace) -> tuple[str, str]:
    """Fetch the requested code and return (commit sha, human label)."""
    if args.pr:
        sh("git", "fetch", "--quiet", "origin", f"pull/{args.pr}/head")
        return sh("git", "rev-parse", "FETCH_HEAD", capture=True), f"PR #{args.pr}"
    branch = args.branch or (args.ref[len("origin/"):] if args.ref.startswith("origin/") else None)
    if branch:
        sh("git", "fetch", "--quiet", "origin", branch)
        return sh("git", "rev-parse", "FETCH_HEAD", capture=True), f"分支 {branch}"
    return sh("git", "rev-parse", args.ref, capture=True), args.ref


def place_worktree(sha: str) -> None:
    STAGING.mkdir(exist_ok=True)
    if (APP / ".git").exists():
        sh("git", "checkout", "--quiet", "--detach", "--force", sha, cwd=APP)
    else:
        if APP.exists():
            shutil.rmtree(APP)
        sh("git", "worktree", "add", "--quiet", "--detach", str(APP), sha)


def dependency_fingerprint(app_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in ("pyproject.toml", "uv.lock"):
        path = app_dir / name
        digest.update(path.read_bytes() if path.exists() else b"")
    return digest.hexdigest()


def ensure_environment(app_dir: Path) -> None:
    fingerprint = dependency_fingerprint(app_dir)
    state = load_state()
    if VENV_PYTHON.exists() and state.get("deps") == fingerprint and state.get("installed_from") == str(app_dir):
        return
    if not VENV_PYTHON.exists():
        print("建立虛擬環境（第一次會花幾分鐘）…")
        sh(sys.executable, "-m", "venv", str(VENV))
    print("安裝相依套件…")
    sh(str(VENV_PYTHON), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "-e", str(app_dir))
    save_state(deps=fingerprint, installed_from=str(app_dir))


def start(app_dir: Path, label: str, port: int) -> subprocess.Popen:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("EXCHANGE_", "SUPABASE", "GOOGLE_OAUTH", "RENDER"))}
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen([str(VENV_PYTHON), str(RUNNER), "--data-dir", str(DATA), "--port", str(port), "--label", label], cwd=app_dir, env=env)


def up(args: argparse.Namespace) -> None:
    if args.here:
        app_dir, sha, label = REPO, "", "本機工作目錄（含未提交修改）"
    else:
        sha, label = resolve(args)
        place_worktree(sha)
        app_dir = APP
        label = f"{label} {sha[:7]}"
    ensure_environment(app_dir)
    save_state(ref=label, port=args.port)
    process = start(app_dir, label, args.port)
    try:
        while True:
            time.sleep(30 if args.watch and not args.here else 1)
            if process.poll() is not None:
                sys.exit(process.returncode)
            if not (args.watch and not args.here):
                continue
            try:
                new_sha, new_label = resolve(args)
            except subprocess.CalledProcessError:
                print("暫時抓不到最新內容，30 秒後再試。")
                continue
            if new_sha != sha:
                print(f"\n偵測到新版本 {sha[:7]} → {new_sha[:7]}，更新並重啟…")
                process.terminate()
                process.wait(timeout=20)
                sha, label = new_sha, f"{new_label} {new_sha[:7]}"
                place_worktree(sha)
                ensure_environment(APP)
                save_state(ref=label)
                process = start(APP, label, args.port)
    except KeyboardInterrupt:
        process.terminate()
        process.wait(timeout=20)


def reset(_: argparse.Namespace) -> None:
    if DATA.exists():
        shutil.rmtree(DATA)
    print("測試資料已清空。下次 up 會重新建立虛構帳號。")


def clean(_: argparse.Namespace) -> None:
    if (APP / ".git").exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(APP)], cwd=REPO, check=False)
    shutil.rmtree(STAGING, ignore_errors=True)
    print(".staging 已刪除。")


def status(_: argparse.Namespace) -> None:
    state = load_state()
    print(json.dumps(state, ensure_ascii=False, indent=1) if state else "尚未啟動過測試版。")
    print(f"資料夾：{DATA}（{'存在' if DATA.exists() else '不存在'}）")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    up_parser = commands.add_parser("up", help="拉取程式碼並啟動測試版")
    source = up_parser.add_mutually_exclusive_group()
    source.add_argument("--pr", type=int, help="PR 編號")
    source.add_argument("--branch", help="分支名稱")
    source.add_argument("--ref", default="origin/main", help="任意 git 參照（預設 origin/main＝正式版）")
    source.add_argument("--here", action="store_true", help="直接跑目前資料夾")
    up_parser.add_argument("--port", type=int, default=8800)
    up_parser.add_argument("--watch", action="store_true", help="每 30 秒檢查遠端有沒有新 commit，有就自動更新")
    up_parser.set_defaults(handler=up)
    for name, handler, text in (("reset", reset, "清空測試資料"), ("clean", clean, "刪除整個 .staging"), ("status", status, "顯示目前狀態")):
        commands.add_parser(name, help=text).set_defaults(handler=handler)
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()

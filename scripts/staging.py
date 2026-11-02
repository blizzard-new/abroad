#!/usr/bin/env python3
"""UniWay 本機測試版（離線）：用虛構資料在自己的電腦上跑某個 PR／分支，合併前先看成果。

用法（在專案根目錄；Windows 建議用 py -3，找不到 py 再用 python）：
  py -3 scripts/staging.py up                 # 跑目前這個資料夾的程式碼（最快，沒有任何 git 動作）
  py -3 scripts/staging.py up --pr 211        # 先切換到 PR 的最新內容再跑；停止後自動切回原本的分支
  py -3 scripts/staging.py up --branch claude/funny-dirac-43frw3
  py -3 scripts/staging.py up --ref origin/main   # 目前的正式版程式碼
  py -3 scripts/staging.py up --pr 211 --watch    # 每 30 秒檢查一次，PR 有新 commit 就自動更新並重啟
  py -3 scripts/staging.py restore             # 如果上次非正常結束，手動切回原本的分支
  py -3 scripts/staging.py reset               # 清空測試資料（下次啟動重建虛構帳號）
  py -3 scripts/staging.py clean               # 刪掉 .staging（虛擬環境、測試資料）
  py -3 scripts/staging.py status

不會複製專案（src 有 3 GB 以上）：切換版本是在你現有的資料夾裡做 git checkout，只更動有差異的檔案。
如果有尚未提交的修改，會拒絕切換，不會弄丟你的東西。虛擬環境與測試資料放在 .staging/（已加入 .gitignore）。
不會連到 Supabase／Render，也不會讀取正式環境的任何資料或密鑰。細節見 docs/staging-local-test.md。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STAGING = REPO / ".staging"
VENV = STAGING / "venv"
DATA = STAGING / "data"
STATE = STAGING / "state.json"
RUNNER = REPO / "scripts" / "staging_runner.py"
VENV_PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def say(message: str = "") -> None:
    print(message, flush=True)


def fail(message: str) -> None:
    say(f"\n錯誤：{message}")
    sys.exit(1)


def git(*args: str, capture: bool = False, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, check=False, text=True, capture_output=capture)
    if check and result.returncode != 0:
        detail = (result.stderr or "").strip() if capture else ""
        fail(f"git {' '.join(args)} 失敗。{detail}")
    return (result.stdout or "").strip() if capture else ""


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(**values: object) -> None:
    STAGING.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({**load_state(), **values}, ensure_ascii=False, indent=1), encoding="utf-8")


def preflight() -> None:
    say(f"UniWay 測試版啟動器（Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}）")
    if sys.version_info < (3, 11):
        fail("需要 Python 3.11 以上。請從 python.org 安裝新版，或在 Windows 試試 py -3.12。")
    if shutil.which("git") is None:
        fail("找不到 git。請安裝 Git for Windows（https://git-scm.com/download/win）後重開命令提示字元。")
    if not (REPO / ".git").exists():
        fail(f"{REPO} 不是 git 專案資料夾。請在 clone 下來的專案裡執行。")
    if not RUNNER.exists():
        fail(f"找不到 {RUNNER}。請先切到有這個檔案的分支：git fetch origin claude/funny-dirac-43frw3 然後 git checkout claude/funny-dirac-43frw3")


# ---------- switching code in place (no copy) ----------

def wants_switch(args: argparse.Namespace) -> bool:
    return bool(args.pr or args.branch or args.ref)


def resolve(args: argparse.Namespace) -> tuple[str, str]:
    """Fetch the requested code and return (commit sha, label)."""
    if args.pr:
        say(f"取得 PR #{args.pr} 的最新內容（只下載差異）…")
        git("fetch", "origin", f"pull/{args.pr}/head")
        return git("rev-parse", "FETCH_HEAD", capture=True), f"PR #{args.pr}"
    branch = args.branch or (args.ref[len("origin/"):] if args.ref and args.ref.startswith("origin/") else None)
    if branch:
        say(f"取得分支 {branch} 的最新內容（只下載差異）…")
        git("fetch", "origin", branch)
        return git("rev-parse", "FETCH_HEAD", capture=True), f"分支 {branch}"
    return git("rev-parse", args.ref, capture=True), args.ref


def ensure_clean() -> None:
    if git("status", "--porcelain", "--untracked-files=no", capture=True):
        fail("你的工作資料夾有尚未提交的修改。為了不弄丟它們，測試版不會切換版本。\n"
             "請先 commit 或 git stash，或改用不帶 --pr／--branch 的 up（直接跑目前資料夾）。")


def remember_original() -> None:
    if load_state().get("restore"):
        return  # a previous run did not finish; keep the first one
    branch = git("symbolic-ref", "--short", "-q", "HEAD", capture=True, check=False)
    save_state(restore=branch or git("rev-parse", "HEAD", capture=True))


def switch_to(sha: str) -> None:
    ensure_clean()
    remember_original()
    say(f"切換到 {sha[:7]}…（只更動有差異的檔案）")
    git("checkout", "--quiet", "--detach", sha)


def restore_original() -> None:
    target = load_state().get("restore")
    if not target:
        return
    say(f"切回原本的 {target}…")
    if subprocess.run(["git", "checkout", "--quiet", target], cwd=REPO).returncode == 0:
        save_state(restore=None)
    else:
        say(f"沒有切回成功（可能有修改）。請手動執行：git checkout {target}")


# ---------- environment and server ----------

def dependency_fingerprint() -> str:
    digest = hashlib.sha256()
    for name in ("pyproject.toml", "uv.lock"):
        path = REPO / name
        digest.update(path.read_bytes() if path.exists() else b"")
    return digest.hexdigest()


def ensure_environment() -> None:
    fingerprint = dependency_fingerprint()
    if VENV_PYTHON.exists() and load_state().get("deps") == fingerprint:
        say("套件已是最新，略過安裝。")
        return
    if not VENV_PYTHON.exists():
        say("建立虛擬環境…")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    say("安裝套件（第一次約 3–10 分鐘，下面會一直捲動是正常的，請不要關掉）…")
    result = subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-e", str(REPO)])
    if result.returncode != 0:
        fail("套件安裝失敗。把上面的最後幾行貼給我，我來看。")
    save_state(deps=fingerprint)


def start(label: str, port: int) -> subprocess.Popen:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("EXCHANGE_", "SUPABASE", "GOOGLE_OAUTH", "RENDER"))}
    env["PYTHONUNBUFFERED"] = "1"
    say("啟動網站（第一次載入學校資料約 1–2 分鐘，看到「測試版已啟動」才可以開網頁）…")
    return subprocess.Popen([str(VENV_PYTHON), str(RUNNER), "--data-dir", str(DATA), "--port", str(port), "--label", label], cwd=REPO, env=env)


def _stop_requested(*_: object) -> None:
    raise KeyboardInterrupt


def up(args: argparse.Namespace) -> None:
    preflight()
    signal.signal(signal.SIGTERM, _stop_requested)  # a closed terminal or `kill` should also switch back to your branch
    switching = wants_switch(args)
    watching = args.watch and switching and not args.here
    sha, label = "", "目前資料夾的程式碼"
    try:
        say("\n[1/3] 準備程式碼")
        if switching:
            sha, name = resolve(args)
            switch_to(sha)
            label = f"{name} {sha[:7]}"
        else:
            say("使用目前資料夾（沒有 git 動作）。")
        say("\n[2/3] 準備執行環境")
        ensure_environment()
        say("\n[3/3] 啟動")
        save_state(ref=label, port=args.port)
        process = start(label, args.port)
        while True:
            time.sleep(30 if watching else 1)
            if process.poll() is not None:
                sys.exit(process.returncode)
            if not watching:
                continue
            try:
                new_sha, new_name = resolve(args)
            except SystemExit:
                say("暫時抓不到最新內容，30 秒後再試。")
                continue
            if new_sha != sha:
                say(f"\n偵測到新版本 {sha[:7]} → {new_sha[:7]}，更新並重啟…")
                process.terminate()
                process.wait(timeout=30)
                sha = new_sha
                label = f"{new_name} {sha[:7]}"
                switch_to(sha)
                ensure_environment()
                save_state(ref=label)
                process = start(label, args.port)
    except KeyboardInterrupt:
        say("\n停止中…")
        try:
            process.terminate()
            process.wait(timeout=30)
        except (NameError, subprocess.TimeoutExpired, OSError):
            pass
    finally:
        if switching:
            restore_original()


def restore(_: argparse.Namespace) -> None:
    preflight()
    ensure_clean()
    restore_original()
    say("完成。")


def reset(_: argparse.Namespace) -> None:
    if DATA.exists():
        shutil.rmtree(DATA)
    say("測試資料已清空。下次 up 會重新建立虛構帳號。")


def clean(_: argparse.Namespace) -> None:
    shutil.rmtree(STAGING, ignore_errors=True)
    say(".staging 已刪除（虛擬環境與測試資料）。")


def status(_: argparse.Namespace) -> None:
    state = load_state()
    say(json.dumps(state, ensure_ascii=False, indent=1) if state else "尚未啟動過測試版。")
    say(f"資料夾：{DATA}（{'存在' if DATA.exists() else '不存在'}）")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    up_parser = commands.add_parser("up", help="啟動測試版")
    source = up_parser.add_mutually_exclusive_group()
    source.add_argument("--pr", type=int, help="PR 編號")
    source.add_argument("--branch", help="分支名稱")
    source.add_argument("--ref", help="任意 git 參照，例如 origin/main（目前的正式版）")
    up_parser.add_argument("--port", type=int, default=8800)
    up_parser.add_argument("--watch", action="store_true", help="每 30 秒檢查遠端有沒有新 commit，有就自動更新（需搭配 --pr 或 --branch）")
    up_parser.set_defaults(handler=up, here=False)
    for name, handler, text in (("restore", restore, "切回上次執行前的分支"), ("reset", reset, "清空測試資料"),
                                ("clean", clean, "刪除 .staging"), ("status", status, "顯示目前狀態")):
        commands.add_parser(name, help=text).set_defaults(handler=handler)
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()

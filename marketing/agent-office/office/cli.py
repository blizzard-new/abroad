"""Command line for the marketing office.

    uv run office serve                 # open the office at http://127.0.0.1:8780 (the clock starts the day by itself)
    uv run office run --force           # run today's planning and production right now
    uv run office list                  # what is waiting in the inbox
    uv run office approve 12 --now      # approve a draft and publish it on the next tick
    uv run office tick                  # one pass of the clock, for cron instead of `serve`
    uv run office check --ping          # is this computer ready: tools, each desk's AI, the social accounts
    uv run office auth threads --token  # link an account (threads / instagram / youtube)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date

from .config import Settings


def _office(args) -> "object":
    from .office import Office

    overrides = {}
    if getattr(args, "no_render", False):
        overrides["render_media"] = False
    return Office(Settings.from_env(**overrides))


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # a Windows console that cannot show a character should not crash us
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="office", description="UniWay 行銷辦公室")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="開辦公室（網頁＋排程）")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8780)
    serve.add_argument("--no-clock", action="store_true", help="不自動排程，只開網頁")

    run = sub.add_parser("run", help="立刻跑一天的企劃與製作")
    run.add_argument("--date", type=date.fromisoformat)
    run.add_argument("--force", action="store_true", help="今天已經跑過也再跑一次")
    run.add_argument("--no-render", action="store_true", help="只寫文案，不輸出圖片影片")

    sub.add_parser("tick", help="排程器跑一輪（給 cron 用）")
    sub.add_parser("publish", help="發佈所有到時間且已核准的草稿")
    sub.add_parser("facts", help="顯示平台數字與今天的已核實公告")

    listing = sub.add_parser("list", help="列出草稿")
    listing.add_argument("--status")

    approve = sub.add_parser("approve", help="核准草稿")
    approve.add_argument("id", type=int)
    approve.add_argument("--now", action="store_true", help="不等排程時間，下一輪就發")

    reject = sub.add_parser("reject", help="退回草稿")
    reject.add_argument("id", type=int)
    reject.add_argument("--note", default="")

    check = sub.add_parser("check", help="檢查這台電腦：工具、每張桌子的 AI、社群帳號")
    check.add_argument("--ping", action="store_true", help="實際問每個 AI 一句測試，確認有登入")

    auth = sub.add_parser("auth", help="連上社群帳號，或用 telegram 連上你的手機")
    auth.add_argument("platform", choices=["youtube", "threads", "instagram", "telegram"])
    auth.add_argument("--token", "--short-token", dest="token", help="Meta 開發者後台產生的權杖（Threads／Instagram）")

    args = parser.parse_args(argv)

    if args.command == "serve":
        import uvicorn

        from .server import create_app

        settings = Settings.from_env()
        print(f"UniWay 行銷辦公室：http://{args.host}:{args.port}")
        uvicorn.run(create_app(settings, clock=not args.no_clock), host=args.host, port=args.port, log_level="warning")
        return 0

    if args.command == "facts":
        from .brand import load_facts, load_news

        settings = Settings.from_env()
        print(json.dumps(
            {"facts": asdict(load_facts(settings)), "news": [asdict(n) for n in load_news(settings)]},
            ensure_ascii=False, indent=2,
        ))
        return 0

    if args.command == "auth":
        return _auth(args)

    if args.command == "check":
        from . import checkup

        sections = checkup.run(Settings.from_env(), ping=args.ping)
        print("UniWay 行銷辦公室：開工前檢查")
        print(checkup.render(sections))
        return 1 if any(row.ok is False for _, rows in sections for row in rows) else 0

    office = _office(args)
    if args.command == "run":
        from .pipeline import run_day

        run_id = run_day(office, args.date, force=args.force)
        drafts = office.store.drafts(limit=50)
        print(f"run #{run_id}（{office.writer.mode}）")
        _print_drafts([d for d in drafts if d["run_id"] == run_id])
    elif args.command == "tick":
        from .scheduler import tick

        print(json.dumps(tick(office, background=False), ensure_ascii=False))
    elif args.command == "publish":
        print(f"發佈 {office.staff['publisher'].publish_due()} 則")
    elif args.command == "list":
        _print_drafts(office.store.drafts(status=args.status, limit=50))
    elif args.command == "approve":
        draft = office.approve(args.id, publish_now=args.now)
        print(f"#{draft['id']} {draft['status']}，排程 {draft['scheduled_at']}")
    elif args.command == "reject":
        print(f"#{office.reject(args.id, args.note)['id']} 已退回")
    return 0


def _print_drafts(drafts: list[dict]) -> None:
    for d in drafts:
        issues = (d.get("review") or {}).get("issues") or []
        flag = f"  ⚠ {issues[0]}" if issues else ""
        print(f"#{d['id']:<4} {d['status']:<17} {d['channel']:<9} {d['format']:<8} {d['scheduled_at'] or '-':<25} {d['title'][:30]}{flag}")


def _auth(args) -> int:
    import httpx

    from . import accounts
    from .platforms.base import PlatformError
    from .platforms.youtube import authorize
    from .store import Store

    settings = Settings.from_env()
    if args.platform == "telegram":
        return _pair_phone(settings)
    store = Store(settings.db_path)
    label = accounts.LABEL[args.platform]
    try:
        if args.platform == "youtube":
            if not (settings.youtube_client_id and settings.youtube_client_secret):
                print("先在 .env 設定 YOUTUBE_CLIENT_ID 與 YOUTUBE_CLIENT_SECRET（Google Cloud 的 OAuth 用戶端，類型選「電腦版應用程式」）")
                return 1
            channel = accounts.link_youtube(settings, store, authorize(settings.youtube_client_id, settings.youtube_client_secret))
            print(f"已連上 YouTube 頻道「{channel['title']}」（{accounts.DESKS['youtube']}），授權存在 var/office.sqlite3。")
            return 0
        if not args.token:
            print(f"請用 --token 帶入 Meta 開發者後台產生的 {label} 權杖")
            return 1
        account = accounts.link_meta(settings, store, args.platform, args.token)
    except (PlatformError, httpx.HTTPError) as error:
        print(f"{label} 連線失敗：{error}")
        return 1
    print(f"已連上 {label} @{account['username']}（帳號 ID {account['id']}；{accounts.DESKS[args.platform]}）")
    if account["exchanged"]:
        print(f"短期權杖已換成長期權杖（約 {account['days']} 天），辦公室每週會自動延長。")
    elif not (settings.threads_app_secret if args.platform == "threads" else settings.instagram_app_secret):
        print(f"提醒：沒設定 {args.platform.upper()}_APP_SECRET，權杖照原樣存；如果它是 1 小時的短期權杖，設好後再跑一次。")
    else:
        print("這已經是長期權杖（約 60 天），照原樣存好，辦公室每週會自動延長。")
    return 0


def _pair_phone(settings: Settings) -> int:
    import time

    from .office import Office
    from .telegram import PAIR_TTL, TelegramBridge, TelegramError

    if not settings.telegram_bot_token:
        print("先在 .env 設定 TELEGRAM_BOT_TOKEN：在 Telegram 搜尋 @BotFather，傳 /newbot 建立機器人，它會給你一串 token。")
        return 1
    bridge = TelegramBridge(Office(Settings.from_env(render_media=False)), spawn=lambda *_: None)
    try:
        name = bridge.bot_name()
    except TelegramError as error:
        print(f"TELEGRAM_BOT_TOKEN 不對或連不上 Telegram：{error}")
        return 1
    code = bridge.new_pairing_code()
    print(f"用手機打開這個連結，在 Telegram 裡按「開始」（Start）：\n\n  https://t.me/{name}?start={code}\n")
    print(f"（{int(PAIR_TTL.total_seconds() // 60)} 分鐘內有效）等你按…")
    deadline = time.monotonic() + PAIR_TTL.total_seconds()
    while time.monotonic() < deadline:
        if not bridge.pairing_open(code):
            who = bridge.office.store.get("handle:telegram") or "你"
            print(f"已連上 {who} 的 Telegram。重新啟動 uv run office serve 後，直接傳訊息給 @{name} 就是跟 Leo 說話。")
            return 0
        try:
            bridge.poll_once(timeout=20, pairing_only=True)
        except TelegramError as error:
            if error.code != 409:  # 409: `office serve` is polling and will finish the pairing itself
                print(f"Telegram 錯誤：{error}")
                return 1
            time.sleep(3)
    print("等太久了，連結已失效，請再跑一次。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

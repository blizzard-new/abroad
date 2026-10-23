"""Command line for the marketing office.

    uv run office serve                 # open the office at http://127.0.0.1:8780 (the clock starts the day by itself)
    uv run office run --force           # run today's planning and production right now
    uv run office list                  # what is waiting in the inbox
    uv run office approve 12 --now      # approve a draft and publish it on the next tick
    uv run office tick                  # one pass of the clock, for cron instead of `serve`
    uv run office auth youtube          # one-time YouTube authorisation, prints a refresh token
"""

from __future__ import annotations

import argparse
import json
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

    auth = sub.add_parser("auth", help="取得或延長平台授權")
    auth.add_argument("platform", choices=["youtube", "threads", "instagram"])
    auth.add_argument("--short-token", help="Meta 開發者後台產生的短期 token（Threads／Instagram）")

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
    from .platforms.meta import InstagramClient, ThreadsClient
    from .platforms.youtube import authorize
    from .store import Store

    settings = Settings.from_env()
    if args.platform == "youtube":
        if not (settings.youtube_client_id and settings.youtube_client_secret):
            print("先在 .env 設定 YOUTUBE_CLIENT_ID 與 YOUTUBE_CLIENT_SECRET（Google Cloud 的 OAuth 用戶端，類型選「電腦版應用程式」）")
            return 1
        token = authorize(settings.youtube_client_id, settings.youtube_client_secret)
        print(f"\n把這行加進 .env：\nYOUTUBE_REFRESH_TOKEN={token}")
        return 0
    if not args.short_token:
        print("請用 --short-token 帶入 Meta 開發者後台產生的 token")
        return 1
    if args.platform == "threads":
        client, secret = ThreadsClient(settings.threads_user_id, "", dry_run=False), settings.threads_app_secret
    else:
        client = InstagramClient(settings.instagram_user_id, "", host=settings.instagram_graph_host, dry_run=False)
        secret = settings.instagram_app_secret
    if not secret:
        print(f"先在 .env 設定 {args.platform.upper()}_APP_SECRET")
        return 1
    result = client.exchange_token(args.short_token, secret)
    token = result.get("access_token")
    if not token:
        print(json.dumps(result, ensure_ascii=False))
        return 1
    Store(settings.db_path).set(f"{args.platform}_token", token)
    days = int(result.get("expires_in", 0)) // 86400
    print(f"已換成長期 token（約 {days} 天，辦公室每週會自動延長），存在 var/office.sqlite3。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

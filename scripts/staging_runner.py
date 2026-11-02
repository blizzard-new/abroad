"""Run UniWay as the local test edition (測試版). Started by scripts/staging.py inside .staging/venv.

Safety rules, all enforced here and not left to the caller:
  * every EXCHANGE_*, SUPABASE*, GOOGLE_OAUTH* and RENDER* variable of the parent shell is removed first, so this process
    can never reach the production Supabase project, production secrets or production Google sign-in;
  * data lives in one folder (--data-dir) with the plain JSONL repositories; nothing is read from or written to the cloud;
  * the only accounts are the made-up students seeded below; their password is printed on start-up;
  * the server listens on 127.0.0.1 only, so the one-click login routes below can only be used from this computer.

This file never changes the application. A small wrapper adds a "測試版" strip and an account switcher to every HTML page
so a screenshot of the test edition can never be mistaken for the real site.
"""
from __future__ import annotations

import argparse
import html
import os
import socket
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

SCRUBBED_PREFIXES = ("EXCHANGE_", "SUPABASE", "GOOGLE_OAUTH", "RENDER")
PASSWORD = "Staging!2026"
HOME_SCHOOL = "長庚大學"
AUTH_COOKIE = "exchange_guide_session"
SUPER_EMAIL = "super@staging.test"
# alias used in /__staging/login?as=<alias>, email, description, number of plans to create
STUDENTS = (
    ("super", SUPER_EMAIL, "超級帳號：已驗證學生、最高方案、管理頁都能開", 1),
    ("a", "a-first@staging.test", "A 第一次使用，還沒選學校", 0),
    ("b", "b-one-plan@staging.test", "B 有一個目標學校，已開始準備", 1),
    ("c", "c-two-plans@staging.test", "C 同時考慮兩個學期／學校", 2),
)
ALIASES = {alias: email for alias, email, _, _ in STUDENTS}
DEFAULT_LANDING = "/#my-application"


def scrub_environment() -> list[str]:
    removed = sorted(name for name in os.environ if name.startswith(SCRUBBED_PREFIXES))
    for name in removed:
        del os.environ[name]
    # Plain email sign-in for the made-up students; the real site uses Google only.
    os.environ["EXCHANGE_AUTH_METHODS"] = "email"
    os.environ["EXCHANGE_ANALYTICS_FLUSH_SECONDS"] = "0"
    # The super account may open the content-review, analytics and feedback admin pages.
    os.environ["EXCHANGE_CONTENT_ADMIN_EMAILS"] = SUPER_EMAIL
    return removed


class StagingStrip:
    """ASGI wrapper: injects a click-through label and an account switcher before </body> of HTML responses.
    Pure HTML + CSS (the site's CSP blocks inline script)."""

    def __init__(self, app, label: str) -> None:
        text = html.escape(label)
        link = ("display:inline-block;padding:6px 10px;border-radius:8px;background:#fff;color:#23324a;"
                "text-decoration:none;border:1px solid #b9c2cf;margin:2px")
        accounts = "".join(
            f'<a href="/__staging/login?as={alias}&amp;to={quote(DEFAULT_LANDING, safe="")}" style="{link}">'
            f"{html.escape(name)}</a>"
            for alias, name in (("super", "超級帳號"), ("a", "A 新用戶"), ("b", "B 一個計畫"), ("c", "C 兩個計畫")))
        self.app = app
        self.snippet = (
            '<div id="uw-staging-strip" role="note" style="position:fixed;left:50%;bottom:0;transform:translateX(-50%);'
            "z-index:2147483647;max-width:96vw;background:#be4c48;color:#fff;font:600 12px/1.2 system-ui,'Noto Sans TC',sans-serif;"
            'padding:6px 14px;border-radius:10px 10px 0 0;pointer-events:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
            f"測試版・{text}・虛構資料</div>"
            '<details id="uw-staging-accounts" style="position:fixed;left:8px;bottom:34px;z-index:2147483646;'
            "font:600 12px/1.3 system-ui,'Noto Sans TC',sans-serif;max-width:220px\">"
            '<summary style="cursor:pointer;display:inline-block;padding:6px 10px;border-radius:8px;background:#23324a;color:#fff">測試帳號</summary>'
            f'<div style="margin-top:4px;background:#ffffffee;border:1px solid #b9c2cf;border-radius:10px;padding:6px">{accounts}'
            f'<a href="/__staging/logout" style="{link}">登出</a></div></details>'
        ).encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        # Disable the zero-copy file path so HTML bodies pass through here.
        scope = {**scope, "extensions": {k: v for k, v in scope.get("extensions", {}).items() if k != "http.response.pathsend"}}
        held: dict = {}
        chunks: list[bytes] = []

        async def wrapped(message):
            if message["type"] == "http.response.start":
                headers = {k.lower(): v for k, v in message["headers"]}
                if headers.get(b"content-type", b"").startswith(b"text/html") and b"content-encoding" not in headers:
                    held["start"] = message
                    return
            elif message["type"] == "http.response.body" and "start" in held:
                chunks.append(message.get("body", b""))
                if message.get("more_body"):
                    return
                body = b"".join(chunks)
                if b"</body>" in body:
                    body = body.replace(b"</body>", self.snippet + b"</body>", 1)
                headers = [(k, v) for k, v in held["start"]["headers"] if k.lower() != b"content-length"]
                headers.append((b"content-length", str(len(body)).encode()))
                await send({**held["start"], "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return
            await send(message)

        await self.app(scope, receive, wrapped)


def add_login_routes(app, login_cookies) -> None:
    """One-click sign-in for the made-up accounts. `login_cookies(email)` returns the Set-Cookie header values of a real
    /auth/login, so the session is created by the application's own code. Routes go first so no catch-all can shadow them."""
    from fastapi import HTTPException, Query
    from fastapi.responses import RedirectResponse
    from fastapi.routing import APIRoute

    def go(to: str) -> str:
        return to if to.startswith("/") and not to.startswith("//") else DEFAULT_LANDING

    def login(who: str = Query("super", alias="as"), to: str = Query(DEFAULT_LANDING)):
        email = ALIASES.get(who)
        if not email:
            raise HTTPException(404, "沒有這個測試帳號。")
        cookies = login_cookies(email)
        if not cookies:
            raise HTTPException(502, "登入失敗，請看終端機的訊息。")
        response = RedirectResponse(go(to), status_code=303)
        for value in cookies:
            response.raw_headers.append((b"set-cookie", value.encode("latin-1")))
        return response

    def logout():
        response = RedirectResponse("/", status_code=303)
        response.delete_cookie(AUTH_COOKIE, path="/")
        return response

    for path, endpoint in (("/__staging/login", login), ("/__staging/logout", logout)):
        app.router.routes.insert(0, APIRoute(path, endpoint, methods=["GET"], include_in_schema=False))


def seed(base_url: str, data_dir: Path) -> list[tuple[str, str]]:
    """Create any missing made-up account (safe to run on every start). The super account is always (re)upgraded."""
    import requests
    from exchange_info.models import ProductAccessTier
    from exchange_info.repositories import JsonlAccountRepository

    repo = JsonlAccountRepository(data_dir)
    headers = {"Origin": base_url}
    for alias, email, label, plan_count in STUDENTS:
        account = repo.find_account_by_email(email)
        created = account is None
        http = requests.Session()
        if created:
            code = http.post(f"{base_url}/auth/email-verification/request", json={"email": email}, timeout=30).json()["development_code"]
            token = http.post(f"{base_url}/auth/email-verification/confirm", json={"email": email, "code": code}, timeout=30).json()["verification_token"]
            registered = http.post(f"{base_url}/auth/register", timeout=30, json={
                "email": email, "password": PASSWORD, "display_name": ("超級帳號" if alias == "super" else label.split()[0] + " 測試學生"),
                "email_verification_token": token, "accept_terms": True}).json()
            account = repo.find_account_by_id(registered["profile"]["id"])
        updates = {"student_status_verified": True, "verified_university": HOME_SCHOOL,
                   "verified_department": "資訊工程學系", "school_email_verified": True}
        if alias == "super":
            updates["product_tier"] = ProductAccessTier.SUBSCRIPTION
        repo.save_account(account.model_copy(update=updates))
        if not created or not plan_count:
            continue
        http.post(f"{base_url}/auth/login", json={"email": email, "password": PASSWORD}, timeout=30).raise_for_status()
        partners = http.get(f"{base_url}/student-dashboard", params={"school": HOME_SCHOOL}, timeout=120).json().get("partner_universities", [])
        names = [p["school_name"] for p in partners if p.get("school_name")][:plan_count]
        revision = 0
        for index, target in enumerate(names):
            made = http.post(f"{base_url}/account/application-paths", headers=headers, timeout=60, json={
                "revision": revision, "home_school": HOME_SCHOOL, "target_school": target, "academic_year": "116",
                "departure_year": "2027" if index == 0 else "2028", "semester": "fall" if index == 0 else "spring"})
            made.raise_for_status()
            body = made.json()
            revision = body["revision"]
            if index == 0:  # a few finished steps and one half-written draft, so the redesign has something to show
                plan_id = body["plan"]["id"]
                for step_id, step in (("home", {"confirmed": True}), ("term", {"confirmed": True}), ("target", {"confirmed": True}),
                                      ("check-availability", {"confirmed": True}),
                                      ("motivation", {"value": "我想去交換，是因為想在不同的教學環境裡練習用英文做專題。"})):
                    saved = http.put(f"{base_url}/account/application-paths/{plan_id}/steps/{step_id}", headers=headers, timeout=60,
                                     params={"home_school": HOME_SCHOOL},
                                     json={"revision": revision, "step": {"value": step.get("value", ""), "confirmed": step.get("confirmed", False),
                                                                           "version_id": None, "applicable": None}})
                    if saved.ok:
                        revision = saved.json()["revision"]
    # Platform-admin pages are decided by account id, which only exists after the account does.
    super_account = repo.find_account_by_email(SUPER_EMAIL)
    if super_account:
        os.environ["EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS"] = super_account.id
    return [(email, label) for _, email, label, _ in STUDENTS]


def http_login_cookies(base_url: str):
    import requests

    def login(email: str) -> list[str]:
        response = requests.post(f"{base_url}/auth/login", json={"email": email, "password": PASSWORD}, timeout=30)
        return list(response.raw.headers.getlist("Set-Cookie")) if response.ok else []

    return login


def free_port_or_exit(port: int) -> None:
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            sys.exit(f"埠 {port} 已被使用。換一個：python scripts/staging.py up --port {port + 1}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--label", default="本機")
    args = parser.parse_args()
    removed = scrub_environment()
    data_dir = Path(args.data_dir).resolve()
    free_port_or_exit(args.port)

    import uvicorn
    from exchange_info.api import create_app
    from exchange_info.storage import ensure_data_dirs

    ensure_data_dirs(data_dir)
    base_url = f"http://127.0.0.1:{args.port}"
    app = create_app(data_dir)
    add_login_routes(app, http_login_cookies(base_url))
    server = uvicorn.Server(uvicorn.Config(StagingStrip(app, args.label), host="127.0.0.1", port=args.port, log_level="warning", access_log=False))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    import requests
    for _ in range(600):
        try:
            if requests.get(f"{base_url}/health", timeout=2).ok:
                break
        except requests.RequestException:
            time.sleep(0.2)
    else:
        sys.exit("網站沒有在 2 分鐘內啟動。")
    accounts = seed(base_url, data_dir)
    print("\n=== UniWay 測試版已啟動 ===")
    print(f"網址      {base_url}")
    print(f"版本      {args.label}")
    print(f"資料夾    {data_dir}（只有這裡，沒有連到正式資料庫）")
    if removed:
        print(f"已移除這個終端機裡的正式環境變數：{', '.join(removed)}")
    print(f"\n超級帳號一鍵登入（所有功能都開）：\n  {base_url}/__staging/login?as=super")
    print(f"\n測試帳號  密碼都是 {PASSWORD}（網頁左下角「測試帳號」也能一鍵切換）")
    for email, label in accounts:
        print(f"  {email:28s} {label}")
    print("按 Ctrl+C 停止。\n", flush=True)
    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        server.should_exit = True
        thread.join(timeout=10)


if __name__ == "__main__":
    main()

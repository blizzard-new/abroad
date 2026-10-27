import os

import httpx

from fake_cli import install
from office import accounts, checkup
from office.brains import launcher
from office.config import Settings
from office.store import Store


def mock(handler):
    calls = []

    def transport(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    return httpx.Client(transport=httpx.MockTransport(transport)), calls


def settings(tmp_path, **env):
    return Settings.from_env(env={"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAINS": "offline", "OFFICE_RENDER_MEDIA": "0", **env})


def test_threads_short_token_is_extended_and_stored_with_its_account(tmp_path, make_office):
    def handler(request):
        if request.url.path == "/access_token":
            assert request.url.params["grant_type"] == "th_exchange_token"
            return httpx.Response(200, json={"access_token": "LONG", "expires_in": 5184000})
        if request.url.path == "/v1.0/me":
            assert request.url.params["access_token"] == "LONG"
            return httpx.Response(200, json={"id": "123", "username": "uniway.tw"})
        return httpx.Response(404)

    office = make_office(THREADS_APP_SECRET="app-secret", OFFICE_DRY_RUN="0")
    http, _ = mock(handler)
    account = accounts.link_meta(office.settings, office.store, "threads", "SHORT", http=http)
    assert account == {"id": "123", "username": "uniway.tw", "days": 60, "exchanged": True}
    assert office.store.get("threads_token") == "LONG"
    # No THREADS_USER_ID in .env: the publisher posts as the account the token belongs to.
    publisher = office.staff["publisher"]
    assert not publisher.missing_credentials("threads") and publisher.missing_credentials("instagram")
    assert publisher.clients()["threads"].user_id == "123"
    assert office.snapshot()["settings"]["accounts"]["threads"] == {"connected": True, "handle": "uniway.tw"}


def test_instagram_dashboard_token_is_kept_when_it_is_already_long_lived(tmp_path):
    def handler(request):
        if request.url.path == "/access_token":
            return httpx.Response(400, json={"error": {"message": "Session key invalid"}})
        if request.url.path == "/v24.0/me":
            return httpx.Response(200, json={"user_id": "17841", "id": "app-scoped", "username": "uniway"})
        return httpx.Response(404)

    s = settings(tmp_path, INSTAGRAM_APP_SECRET="app-secret")
    store = Store(s.db_path)
    http, _ = mock(handler)
    account = accounts.link_meta(s, store, "instagram", "DASHBOARD", http=http)
    assert account["id"] == "17841" and not account["exchanged"]
    assert store.get("instagram_token") == "DASHBOARD" and store.get("instagram_user_id") == "17841"
    assert store.get("handle:instagram") == "uniway"


def test_check_reads_who_each_token_belongs_to(tmp_path):
    def handler(request):
        host, path = request.url.host, request.url.path
        if host == "graph.threads.net":
            return httpx.Response(200, json={"id": "123", "username": "uniway.tw"})
        if host == "graph.instagram.com":
            return httpx.Response(400, json={"error": {"message": "Error validating access token"}})
        if host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "ya29"})
        if path == "/youtube/v3/channels":
            return httpx.Response(200, json={"items": [{"id": "UC1", "snippet": {"title": "UniWay"}}]})
        if path == "/storage/v1/bucket/marketing-media":
            return httpx.Response(200, json={"public": True})
        return httpx.Response(404)

    s = settings(
        tmp_path, THREADS_USER_ID="123", THREADS_ACCESS_TOKEN="t", INSTAGRAM_USER_ID="17841", INSTAGRAM_ACCESS_TOKEN="old",
        YOUTUBE_CLIENT_ID="id", YOUTUBE_CLIENT_SECRET="secret", YOUTUBE_REFRESH_TOKEN="refresh",
        OFFICE_MEDIA_HOST="supabase", SUPABASE_URL="https://x.supabase.co", SUPABASE_SERVICE_ROLE_KEY="service",
    )
    http, calls = mock(handler)
    rows = {row.name: row for row in accounts.check(s, Store(s.db_path), http=http)}
    assert rows["Threads"].ok and "@uniway.tw" in rows["Threads"].detail and "Pat" in rows["Threads"].detail
    assert rows["Instagram"].ok is False and "office auth instagram" in rows["Instagram"].detail
    assert rows["YouTube"].ok and "UniWay" in rows["YouTube"].detail
    assert rows["圖片影片的公開網址"].ok
    assert all(call.method == "GET" or call.url.host == "oauth2.googleapis.com" for call in calls)  # nothing is posted


def test_check_catches_a_token_for_another_account(tmp_path):
    http, _ = mock(lambda request: httpx.Response(200, json={"id": "555", "username": "someone.else"}))
    s = settings(tmp_path, THREADS_USER_ID="123", THREADS_ACCESS_TOKEN="t")
    threads = next(row for row in accounts.check(s, Store(s.db_path), http=http) if row.name == "Threads")
    assert threads.ok is False and "someone.else" in threads.detail


def test_checkup_asks_each_ai_a_test_question(tmp_path, monkeypatch):
    bin_dir = install(tmp_path / "bin")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("FAKE_FAIL", "codex")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "no-config"))
    s = settings(
        tmp_path, OFFICE_BRAINS="chief=antigravity,reviewer=codex,*=claude-code", OFFICE_BRAIN_FALLBACK="claude-code,api,offline",
    )
    rows = {row.name: row for row in checkup.brain_rows(s, ping=True)}
    assert rows["Antigravity"].ok and "Leo" in rows["Antigravity"].detail
    assert rows["Claude Code"].ok and "阿脆" in rows["Claude Code"].detail
    assert rows["Codex"].ok is False and "Kiki" in rows["Codex"].detail
    assert rows["Claude API"].ok is None  # only a fallback here
    assert rows["離線範本"].ok


def test_npm_shims_on_windows_run_their_script_directly(tmp_path):
    script = tmp_path / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
    script.parent.mkdir(parents=True)
    script.write_text("// cli")
    (tmp_path / "node.exe").write_text("")
    shim = tmp_path / "claude.cmd"
    shim.write_text(
        '@ECHO off\r\nSETLOCAL\r\nendLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & '
        '"%_prog%"  "%dp0%\\node_modules\\@anthropic-ai\\claude-code\\cli.js" %*\r\n'
    )
    assert launcher(str(shim)) == [str(tmp_path / "node.exe"), str(script)]

    native = tmp_path / "node_modules" / "tool" / "tool.exe"
    native.parent.mkdir(parents=True)
    native.write_text("")
    (tmp_path / "tool.cmd").write_text('@"%~dp0\\node_modules\\tool\\tool.exe" %*\r\n')
    assert launcher(str(tmp_path / "tool.cmd")) == [str(native)]

    (tmp_path / "other.cmd").write_text("@echo hi\r\n")
    assert launcher(str(tmp_path / "other.cmd")) == [str(tmp_path / "other.cmd")]
    assert launcher("/usr/local/bin/claude") == ["/usr/local/bin/claude"]


def test_check_shows_whether_the_phone_is_paired(tmp_path):
    http, _ = mock(lambda request: httpx.Response(200, json={"ok": True, "result": {"username": "uniway_office_bot"}}))
    s = settings(tmp_path, TELEGRAM_BOT_TOKEN="123:abc")
    store = Store(s.db_path)
    assert checkup.phone_rows(s, store, http)[0].ok is False
    store.set("telegram_chat_id", "4242")
    store.set("handle:telegram", "boss")
    row = checkup.phone_rows(s, store, http)[0]
    assert row.ok and "@uniway_office_bot" in row.detail and "boss" in row.detail
    assert checkup.phone_rows(settings(tmp_path), store)[0].ok is None  # no bot set up: only a reminder

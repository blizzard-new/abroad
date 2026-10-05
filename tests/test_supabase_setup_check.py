"""The Supabase setup checker and the key headers every repository sends."""
from __future__ import annotations

import base64
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from exchange_info.analytics_repository import SupabaseAnalyticsRepository
from exchange_info.supabase_keys import supabase_key_headers

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_supabase_setup.py"
spec = importlib.util.spec_from_file_location("check_supabase_setup", SCRIPT)
checker = importlib.util.module_from_spec(spec)
sys.modules["check_supabase_setup"] = checker
spec.loader.exec_module(checker)

URL = "https://abcdxyz.supabase.co"
SECRET = "sb_secret_testtesttesttest"
MASTER = base64.urlsafe_b64encode(bytes(range(32))).decode()
GOOD_ENV = {
    "EXCHANGE_SUPABASE_URL": URL, "EXCHANGE_SUPABASE_SECRET_KEY": SECRET, "EXCHANGE_ENVIRONMENT": "production",
    "EXCHANGE_VAULT_MASTER_KEY": MASTER, "EXCHANGE_EMAIL_VERIFICATION_SECRET": MASTER,
    "GOOGLE_OAUTH_CLIENT_ID": "id", "GOOGLE_OAUTH_CLIENT_SECRET": "secret",
    "EXCHANGE_PUBLIC_BASE_URL": "https://uniway.example", "EXCHANGE_CONTENT_ADMIN_EMAILS": "me@example.com",
}


class Reply:
    def __init__(self, status=200, payload=None):
        self.status_code, self.payload = status, payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class FakeSupabase:
    """Answers like a project where everything is set up unless a flag says otherwise."""

    def __init__(self, *, missing=(), bucket="private", key_ok=True, anon_reads=False, rpc=True):
        self.missing, self.bucket, self.key_ok, self.anon_reads, self.rpc = set(missing), bucket, key_ok, anon_reads, rpc
        self.calls = []

    def __call__(self, method, url, headers=None, params=None, json=None, timeout=None):
        self.calls.append((method, url, dict(headers or {})))
        path = url.removeprefix(URL)
        anon = (headers or {}).get("apikey", "").startswith("sb_publishable_")
        if path.startswith("/rest/v1/rpc/exchange_list_pending_account_deletion_storage"):
            return Reply(200, {"status": "committed", "jobs": []}) if self.rpc else Reply(404)
        if path.startswith("/rest/v1/rpc/"):
            return Reply(204 if self.rpc else 404)
        if path.endswith("/exchange_account_deletion_receipts"):
            return Reply(404)  # the migration revokes every API role, so the REST API never lists it
        if path.startswith("/rest/v1/"):
            if anon:
                return Reply(200, [{"id": "x"}] if self.anon_reads else None) if self.anon_reads else Reply(401)
            if not self.key_ok:
                return Reply(401)
            return Reply(404 if path.rsplit("/", 1)[-1] in self.missing else 200, [])
        if path.startswith("/storage/v1/bucket/"):
            if self.bucket == "missing":
                return Reply(404)
            return Reply(200, {"name": "exchange-private-vault", "public": self.bucket == "public"})
        raise AssertionError(path)


def run(env=None, anon="", **kwargs):
    fake = FakeSupabase(**kwargs)
    results = checker.check_project(GOOD_ENV if env is None else env, anon_key=anon, tables=["exchange_accounts", "exchange_notifications"],
                                    request_func=fake)
    return results, fake


def levels(results):
    return [r.level for r in results]


# ----------------------------------------------------------------------------- key headers


def test_new_style_keys_go_in_apikey_only_and_legacy_jwts_in_both():
    assert supabase_key_headers("sb_secret_abc") == {"apikey": "sb_secret_abc"}
    assert supabase_key_headers(" eyJ.legacy.jwt ") == {"apikey": "eyJ.legacy.jwt", "Authorization": "Bearer eyJ.legacy.jwt"}


def test_repositories_use_those_headers():
    seen = []

    def record(method, url, **kwargs):
        seen.append(kwargs["headers"])
        return Reply(200, [])

    start, end = datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc)
    SupabaseAnalyticsRepository(URL, "sb_secret_abc", request_func=record).fetch_api_metrics(start, end)
    assert seen[0]["apikey"] == "sb_secret_abc" and "Authorization" not in seen[0]
    SupabaseAnalyticsRepository(URL, "legacy.service.jwt", request_func=record).fetch_api_metrics(start, end)
    assert seen[1]["Authorization"] == "Bearer legacy.service.jwt"


# ----------------------------------------------------------------------------- the checker


def test_a_fully_set_up_project_passes_and_never_prints_the_key():
    results, fake = run(anon="sb_publishable_xyz")
    assert levels(results) == ["ok"] * len(results)
    assert any("私人儲存桶" in r.title for r in results) and any("公開金鑰讀不到" in r.title for r in results)
    assert SECRET not in "\n".join(r.render() for r in results)
    assert all("Authorization" not in headers for _, _, headers in fake.calls[:3]), "sb_secret keys use apikey only"


def test_missing_tables_function_and_bucket_are_each_reported():
    results, _ = run(missing={"exchange_notifications"})
    assert next(r for r in results if "缺少" in r.title).level == "fail"
    assert "exchange_notifications" in next(r for r in results if "缺少" in r.title).title
    assert any(r.level == "fail" and "資料庫函式" in r.title for r in run(rpc=False)[0])
    assert any(r.level == "fail" and "找不到儲存桶" in r.title for r in run(bucket="missing")[0])


def test_a_public_bucket_is_a_failure():
    result = next(r for r in run(bucket="public")[0] if "公開的" in r.title)
    assert result.level == "fail" and "Public bucket" in result.hint


def test_a_rejected_key_stops_early_with_advice():
    results, fake = run(key_ok=False)
    assert results[-1].level == "fail" and "拒絕" in results[-1].title
    assert len(fake.calls) == 1


def test_publishable_keys_and_missing_settings_are_caught_before_any_request():
    publishable = dict(GOOD_ENV, EXCHANGE_SUPABASE_SECRET_KEY="sb_publishable_oops")
    results, fake = run(publishable)
    assert results[-1].level == "fail" and "公開金鑰" in results[-1].title and not fake.calls
    assert levels(run({})[0]) == ["fail"]
    assert levels(run(dict(GOOD_ENV, EXCHANGE_SUPABASE_URL="http://x.supabase.co"))[0]) == ["fail"]


def test_a_public_key_that_can_read_the_accounts_table_is_a_failure():
    results, _ = run(anon="sb_publishable_xyz", anon_reads=True)
    assert any(r.level == "fail" and "可以讀到帳號" in r.title for r in results)


def test_unreachable_projects_are_explained():
    def offline(*args, **kwargs):
        raise requests.ConnectionError("down")

    results = checker.check_project(GOOD_ENV, tables=[], request_func=offline)
    assert results[-1].level == "fail" and "暫停" in results[-1].hint


def test_environment_check_flags_what_production_needs():
    assert all(r.level == "ok" for r in checker.check_environment(GOOD_ENV))
    bad = checker.check_environment({"EXCHANGE_VAULT_MASTER_KEY": "too-short"})
    failed = [r.title for r in bad if r.level == "fail"]
    assert any("MASTER_KEY" in t for t in failed) and any("VERIFICATION_SECRET" in t for t in failed)
    assert any(r.level == "warn" and "production" in r.title for r in bad)


def test_tables_hidden_from_the_api_are_confirmed_through_their_function():
    tables = ["exchange_accounts", "exchange_account_deletion_receipts"]

    def check(**kwargs):
        fake = FakeSupabase(**kwargs)
        return checker.check_project(GOOD_ENV, tables=tables, request_func=fake), fake

    results, fake = check()
    assert next(r for r in results if "資料表" in r.title).level == "ok", "the revoked table is not reported missing"
    assert any(url.endswith("/rpc/exchange_list_pending_account_deletion_storage") for _, url, _ in fake.calls)
    assert not any(url.endswith("/rest/v1/exchange_account_deletion_receipts") for _, url, _ in fake.calls)
    broken, _ = check(rpc=False)
    assert any(r.level == "fail" and "exchange_account_deletion_receipts" in r.title for r in broken)


def test_every_function_only_table_is_one_the_migrations_really_hide_from_service_role():
    root = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(root.glob("*.sql")))
    for table, (function, _) in checker.FUNCTION_ONLY_TABLES.items():
        assert table in checker.expected_tables()
        assert f"create or replace function public.{function}" in text
        assert f"revoke all on table public.{table}" in text and "service_role" in text.split(f"revoke all on table public.{table}")[1][:120]


def test_all_zero_keys_left_by_a_failed_generator_are_rejected():
    zeros = base64.b64encode(bytes(32)).decode()
    bad = checker.check_environment(dict(GOOD_ENV, EXCHANGE_VAULT_MASTER_KEY=zeros, EXCHANGE_EMAIL_VERIFICATION_SECRET=zeros.rstrip("=")))
    failed = [r.title for r in bad if r.level == "fail"]
    assert any("MASTER_KEY" in t and "相同" in t for t in failed) and any("VERIFICATION_SECRET" in t and "相同" in t for t in failed)
    assert all(r.level != "fail" for r in checker.check_environment(GOOD_ENV))


def test_the_documented_key_generator_works_in_windows_powershell():
    """Windows PowerShell 5.1 has no RandomNumberGenerator.Fill; the guides must use GetBytes."""
    root = Path(__file__).resolve().parents[1]
    for name in ("README.md", "docs/supabase-setup-guide.md"):
        text = (root / name).read_text(encoding="utf-8")
        assert "RandomNumberGenerator]::Fill" not in text, name
        assert "RandomNumberGenerator]::Create().GetBytes" in text, name


def test_the_checker_knows_every_table_the_migrations_create():
    tables = checker.expected_tables()
    assert len(tables) >= 45 and len(tables) == len(set(tables))
    assert {"exchange_accounts", "exchange_analytics_events", "exchange_analytics_api_hourly",
            "application_workflow_issue_reports"} <= set(tables)
    assert all(not name.endswith("_daily") for name in tables), "views are not tables"

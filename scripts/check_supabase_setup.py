"""Check a Supabase project against what this app needs, in plain language.

Reads the same environment variables the server reads and sends a handful of harmless requests (reads,
plus one empty write to a counter function). It never prints a key.

    python scripts/check_supabase_setup.py              # after setting the environment variables
    python scripts/check_supabase_setup.py --anon-key sb_publishable_...   # also proves the public key sees nothing

Exit code 0 means no problem was found; warnings (⚠) are things to look at but do not block.
"""
from __future__ import annotations

import argparse
import base64
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exchange_info.supabase_keys import supabase_key_headers  # noqa: E402

MIGRATIONS = ROOT / "supabase" / "migrations"
DEFAULT_BUCKET = "exchange-private-vault"
TABLE_PATTERN = re.compile(r"create table (?:if not exists )?public\.([a-z0-9_]+)", re.IGNORECASE)
# Tables the migrations hide from every API role (even the secret key), so a direct read always looks like
# "not found". Each is confirmed through a read-only function that selects from it instead.
FUNCTION_ONLY_TABLES = {
    "exchange_account_deletion_receipts": ("exchange_list_pending_account_deletion_storage", {"p_limit": 1}),
}


@dataclass
class Result:
    level: str  # "ok" | "warn" | "fail"
    title: str
    hint: str = ""

    def render(self) -> str:
        mark = {"ok": "✓", "warn": "⚠", "fail": "✗"}[self.level]
        return f"{mark} {self.title}" + (f"\n    → {self.hint}" if self.hint else "")


def first(values: Mapping[str, str], *names: str) -> str:
    return next((values[name].strip() for name in names if values.get(name, "").strip()), "")


def key_role(key: str) -> str:
    """publishable / secret for the new keys; the ``role`` claim (anon, service_role) for a legacy JWT."""
    if key.startswith("sb_publishable_"):
        return "publishable"
    if key.startswith("sb_secret_"):
        return "secret"
    parts = key.split(".")
    if len(parts) == 3:
        try:
            payload = base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
            match = re.search(rb'"role"\s*:\s*"([a-z_]+)"', payload)
            return match.group(1).decode() if match else "unknown"
        except ValueError:
            return "unknown"
    return "unknown"


def decode_key(value: str) -> bytes:
    """The bytes behind a url-safe or standard base64 value, or b"" when it is not base64."""
    value = value.strip()
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)) if value else b""
    except ValueError:
        return b""


def expected_tables() -> list[str]:
    names: list[str] = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        for name in TABLE_PATTERN.findall(path.read_text(encoding="utf-8")):
            if name not in names:
                names.append(name)
    return names


def check_project(
    env: Mapping[str, str],
    *,
    anon_key: str = "",
    tables: list[str] | None = None,
    request_func: Callable[..., requests.Response] = requests.request,
) -> list[Result]:
    results: list[Result] = []
    url = first(env, "EXCHANGE_SUPABASE_URL", "SUPABASE_URL").rstrip("/")
    key = first(env, "EXCHANGE_SUPABASE_SECRET_KEY", "SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY")
    bucket = env.get("EXCHANGE_VAULT_BUCKET", "").strip() or DEFAULT_BUCKET

    def call(method: str, path: str, *, headers: dict | None = None, **kwargs):
        return request_func(method, f"{url}{path}", headers=headers if headers is not None else supabase_key_headers(key),
                            timeout=20, **kwargs)

    if not url or not key:
        return [Result("fail", "還沒有設定 Supabase 網址與後端金鑰",
                       "設定環境變數 EXCHANGE_SUPABASE_URL 與 EXCHANGE_SUPABASE_SECRET_KEY（見 docs/supabase-setup-guide.md 第 5 步）。")]
    if not url.startswith("https://"):
        return [Result("fail", "Supabase 網址必須以 https:// 開頭", "到 Project Settings 複製 Project URL，格式像 https://abcdxyz.supabase.co。")]
    results.append(Result("ok", "網址格式正確"))
    if key_role(key) in {"publishable", "anon"}:
        results.append(Result("fail", "這看起來是公開金鑰，不是後端金鑰", "後端要用 Secret key（sb_secret_ 開頭），不是 Publishable key。"))
        return results

    try:
        probe = call("GET", "/rest/v1/exchange_accounts", params={"select": "id", "limit": "0"})
    except requests.RequestException as exc:
        return results + [Result("fail", f"連不上 Supabase（{type(exc).__name__}）", "檢查網址有沒有打錯、專案有沒有被暫停（免費專案閒置會暫停，到後台按 Restore）。")]
    if probe.status_code in (401, 403):
        results.append(Result("fail", "Supabase 拒絕了這把後端金鑰", "確認複製的是 Secret key 且沒有多餘空白；若是新金鑰仍被拒，改用 Legacy API keys 的 service_role。"))
        return results
    results.append(Result("ok", "後端金鑰被接受"))

    names = tables if tables is not None else expected_tables()
    missing = []
    for name in names:
        try:
            if name in FUNCTION_ONLY_TABLES:
                function, arguments = FUNCTION_ONLY_TABLES[name]
                reply = call("POST", f"/rest/v1/rpc/{function}", json=arguments,
                             headers={**supabase_key_headers(key), "Content-Type": "application/json"})
                if reply.status_code != 200 or (reply.json() or {}).get("status") != "committed":
                    missing.append(name)
                continue
            response = call("GET", f"/rest/v1/{name}", params={"select": "*", "limit": "0"})
        except (requests.RequestException, ValueError, AttributeError):
            missing.append(name)
            continue
        if response.status_code == 404 or response.status_code >= 500 or response.status_code in (401, 403):
            missing.append(name)
    if missing:
        shown = "、".join(missing[:6]) + ("…" if len(missing) > 6 else "")
        results.append(Result("fail", f"缺少 {len(missing)} 張資料表（{shown}）", "migration 沒有套完（或權限不足）：回到第 4 步執行 db push，並看有沒有錯誤訊息。"))
    else:
        results.append(Result("ok", f"{len(names)} 張資料表都在"))

    try:
        rpc = call("POST", "/rest/v1/rpc/exchange_analytics_add_api_hourly", json={"p_rows": []},
                   headers={**supabase_key_headers(key), "Content-Type": "application/json"})
        if rpc.status_code in (200, 204):
            results.append(Result("ok", "資料庫函式可以呼叫（使用統計）"))
        else:
            results.append(Result("fail", "找不到資料庫函式 exchange_analytics_add_api_hourly", "最新的 migration（20261003110000_analytics.sql）沒套用。"))
    except requests.RequestException as exc:
        results.append(Result("fail", f"呼叫資料庫函式失敗（{type(exc).__name__}）"))

    try:
        storage = call("GET", f"/storage/v1/bucket/{bucket}")
        if storage.status_code == 200:
            public = bool(storage.json().get("public"))
            if public:
                results.append(Result("fail", f"儲存桶 {bucket} 是公開的", "到 Storage → 該桶 → Edit bucket，關掉 Public bucket。文件庫的密文不能公開。"))
            else:
                results.append(Result("ok", f"私人儲存桶 {bucket} 存在且不公開"))
        else:
            results.append(Result("fail", f"找不到儲存桶 {bucket}", "到 Storage 建立名稱完全相同的桶，並關閉 Public bucket（第 3 步）。"))
    except (requests.RequestException, ValueError) as exc:
        results.append(Result("fail", f"檢查儲存桶失敗（{type(exc).__name__}）"))

    if anon_key:
        try:
            probe = request_func("GET", f"{url}/rest/v1/exchange_accounts", headers=supabase_key_headers(anon_key),
                                 params={"select": "id", "limit": "1"}, timeout=20)
            if probe.status_code in (401, 403):
                results.append(Result("ok", "公開金鑰讀不到帳號資料表"))
            elif probe.status_code == 200 and probe.json() == []:
                results.append(Result("warn", "公開金鑰讀得到資料表但沒有資料", "表是空的所以看不出差別；上線後有帳號時再測一次。"))
            else:
                results.append(Result("fail", "公開金鑰可以讀到帳號資料表！", "立刻停止上線，確認 migration 都套用成功（它們會撤銷瀏覽器角色的權限）。"))
        except requests.RequestException as exc:
            results.append(Result("fail", f"測試公開金鑰失敗（{type(exc).__name__}）"))
    else:
        results.append(Result("warn", "沒有測試公開金鑰的權限", "加上 --anon-key <Publishable key> 可以確認瀏覽器金鑰讀不到任何資料。"))
    return results


def check_environment(env: Mapping[str, str]) -> list[Result]:
    results: list[Result] = []
    if env.get("EXCHANGE_ENVIRONMENT", "").strip().lower() == "production":
        results.append(Result("ok", "EXCHANGE_ENVIRONMENT=production"))
    else:
        results.append(Result("warn", "EXCHANGE_ENVIRONMENT 不是 production", "正式上線要設成 production，才會強制使用 Supabase 與安全 Cookie。"))
    regenerate = "用指南第 5 步的指令重新產生（要用 GetBytes 那一版）；產生後要另外備份，遺失就無法解密已存的文件。"
    master = decode_key(env.get("EXCHANGE_VAULT_MASTER_KEY", ""))
    if len(master) != 32:
        results.append(Result("fail", "EXCHANGE_VAULT_MASTER_KEY 不是 32 位元組的 base64 金鑰", regenerate))
    elif len(set(master)) == 1:
        results.append(Result("fail", "EXCHANGE_VAULT_MASTER_KEY 是全部相同的位元組（沒有隨機產生）", "產生指令失敗時變數會留下全 0 的值，這種金鑰等於沒有加密。" + regenerate))
    else:
        results.append(Result("ok", "文件庫加密金鑰 EXCHANGE_VAULT_MASTER_KEY 格式正確"))
    verification = env.get("EXCHANGE_EMAIL_VERIFICATION_SECRET", "").strip()
    decoded_secret = decode_key(verification)
    if not verification:
        results.append(Result("fail", "缺 EXCHANGE_EMAIL_VERIFICATION_SECRET", "正式環境一定要有（即使只開放 Google 登入）；用 32 位元組隨機值產生。"))
    elif len(decoded_secret) == 32 and len(set(decoded_secret)) == 1:
        results.append(Result("fail", "EXCHANGE_EMAIL_VERIFICATION_SECRET 是全部相同的位元組（沒有隨機產生）", regenerate))
    else:
        results.append(Result("ok", "EXCHANGE_EMAIL_VERIFICATION_SECRET 已設定"))
    if env.get("GOOGLE_OAUTH_CLIENT_ID", "").strip() and env.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip():
        results.append(Result("ok", "Google 登入金鑰已設定"))
    else:
        results.append(Result("warn", "還沒有設定 Google 登入金鑰", "沒有它就沒有人能登入；網站仍可瀏覽。"))
    if env.get("EXCHANGE_PUBLIC_BASE_URL", "").strip().startswith("https://"):
        results.append(Result("ok", "EXCHANGE_PUBLIC_BASE_URL 是 https 網址"))
    else:
        results.append(Result("warn", "EXCHANGE_PUBLIC_BASE_URL 還沒設成你的 https 網址", "Google 登入的回呼網址與日曆訂閱都靠它。"))
    admins = [item for item in re.split(r"[,\s]+", env.get("EXCHANGE_CONTENT_ADMIN_EMAILS", "")) if item]
    admin_ids = [item for item in re.split(r"[,\s]+", env.get("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", "")) if item]
    if admins or admin_ids:
        results.append(Result("ok", "已指定管理員（可看 /admin/analytics）"))
    else:
        results.append(Result("warn", "沒有指定管理員", "設 EXCHANGE_CONTENT_ADMIN_EMAILS（你的 Google 信箱）才看得到統計儀表板。"))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anon-key", default=os.environ.get("SUPABASE_PUBLISHABLE_KEY", ""),
                        help="The Publishable (anon) key, to prove it cannot read private tables.")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")
    results = [*check_project(os.environ, anon_key=args.anon_key.strip()), *check_environment(os.environ)]
    for result in results:
        print(result.render())
    failures = sum(r.level == "fail" for r in results)
    warnings = sum(r.level == "warn" for r in results)
    print(f"\n{len(results) - failures - warnings} 項正常、{warnings} 項提醒、{failures} 項要修。")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

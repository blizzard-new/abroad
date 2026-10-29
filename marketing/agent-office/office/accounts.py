"""Which social accounts the office works on, linking them, and checking they still answer.

Only three desks ever touch an account, and they share one connection per platform: Pat publishes, Momo reads
comments and sends the replies you approved, Nana reads the numbers. Everyone else only makes drafts.

`office auth` stores each token with the account it belongs to in var/office.sqlite3 (and the clock extends Meta
tokens weekly there); values in .env are the fallback, for people who would rather paste them by hand.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import Settings
from .platforms.base import PlatformError
from .platforms.github import GitHubClient, is_classic_token
from .platforms.meta import InstagramClient, ThreadsClient
from .platforms.youtube import YouTubeClient
from .store import Store

PLATFORMS = ("threads", "instagram", "youtube", "github")
LABEL = {"threads": "Threads", "instagram": "Instagram", "youtube": "YouTube", "github": "GitHub"}
DESKS = {
    "threads": "Pat 發文、Momo 回留言、Nana 看數據",
    "instagram": "Pat 發文、Momo 回留言、Nana 看數據",
    "youtube": "Pat 上傳影片、Nana 看數據",
    "github": "Pat 把你核准的資料更新提案開成 draft PR，不能合併",
}


def credentials(settings: Settings, store: Store) -> dict[str, dict[str, str]]:
    return {
        "threads": {
            "user_id": store.get("threads_user_id") or settings.threads_user_id,
            "token": store.get("threads_token") or settings.threads_token,
        },
        "instagram": {
            "user_id": store.get("instagram_user_id") or settings.instagram_user_id,
            "token": store.get("instagram_token") or settings.instagram_token,
        },
        "youtube": {
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
            "refresh_token": store.get("youtube_refresh_token") or settings.youtube_refresh_token,
        },
        "github": {
            "repo": settings.github_repo,
            "token": store.get("github_token") or settings.github_token,
        },
    }


def connected(settings: Settings, store: Store, platform: str) -> bool:
    return all(credentials(settings, store)[platform].values())


def link_meta(settings: Settings, store: Store, platform: str, token: str, http: httpx.Client | None = None) -> dict:
    """Store a Threads or Instagram token together with the account it belongs to.

    A short-lived token (1 hour) is swapped for a long-lived one (about 60 days) when the app secret is set; a token
    that is already long-lived, like the ones the Instagram dashboard hands out, cannot be swapped and is kept as is.
    """
    if platform == "threads":
        client, secret = ThreadsClient("", token, dry_run=False, http=http), settings.threads_app_secret
    else:
        client = InstagramClient(settings.instagram_user_id, token, host=settings.instagram_graph_host, dry_run=False, http=http)
        secret = settings.instagram_app_secret
    days = None
    if secret:
        try:
            result = client.exchange_token(token, secret)
        except PlatformError:
            result = {}
        if result.get("access_token"):
            client.token = result["access_token"]
            days = int(result.get("expires_in", 0)) // 86400
    account = client.me()
    if not account["id"]:
        raise PlatformError(f"{LABEL[platform]} 沒有回傳帳號 ID")
    store.set(f"{platform}_token", client.token)
    store.set(f"{platform}_user_id", account["id"])
    store.set(f"handle:{platform}", account["username"])
    return {**account, "days": days, "exchanged": days is not None}


def link_youtube(settings: Settings, store: Store, refresh_token: str, http: httpx.Client | None = None) -> dict:
    client = YouTubeClient(settings.youtube_client_id, settings.youtube_client_secret, refresh_token, dry_run=False, http=http)
    channel = client.channel()
    store.set("youtube_refresh_token", refresh_token)
    store.set("handle:youtube", channel["title"])
    return channel


def link_github(settings: Settings, store: Store, token: str, http: httpx.Client | None = None) -> dict:
    """Store a GitHub token after asking GitHub whose it is and whether it can push to the office's repository."""
    client = GitHubClient(settings.github_repo, token, base=settings.github_base, dry_run=False, http=http)
    found = client.check()
    if not found["can_push"]:
        raise PlatformError(f"這個權杖不能寫入 {found['repo']}：fine-grained 權杖要選這個 repository，並給 Contents 與 Pull requests 的讀寫權限")
    store.set("github_token", token)
    store.set("handle:github", found["login"] or found["repo"])
    return {**found, "classic": is_classic_token(token)}


@dataclass
class Row:
    ok: bool | None  # None: not needed yet, or only a warning
    name: str
    detail: str


def check(settings: Settings, store: Store, http: httpx.Client | None = None) -> list[Row]:
    """Ask each platform who the stored token belongs to. Read-only: nothing is posted, even with dry run off."""
    creds = credentials(settings, store)
    rows = []
    for platform in ("threads", "instagram"):
        label, cred = LABEL[platform], creds[platform]
        if not cred["token"]:
            rows.append(Row(False, label, f"還沒連：uv run office auth {platform} --token <權杖>"))
            continue
        if platform == "threads":
            client = ThreadsClient(cred["user_id"], cred["token"], dry_run=False, http=http)
        else:
            client = InstagramClient(cred["user_id"], cred["token"], host=settings.instagram_graph_host, dry_run=False, http=http)
        try:
            account = client.me()
        except (PlatformError, httpx.HTTPError) as error:
            rows.append(Row(False, label, f"權杖無效或過期，重新跑 uv run office auth {platform}（{str(error)[:120]}）"))
            continue
        if cred["user_id"] and account["id"] and cred["user_id"] != account["id"]:
            rows.append(Row(False, label, f"權杖屬於 @{account['username']}（{account['id']}），但帳號 ID 設的是 {cred['user_id']}"))
        elif not cred["user_id"]:
            rows.append(Row(False, label, f"權杖是 @{account['username']} 的，但缺帳號 ID：重新跑 uv run office auth {platform}"))
        else:
            rows.append(Row(True, label, f"@{account['username']}（{DESKS[platform]}）"))
    yt = creds["youtube"]
    if not (yt["client_id"] and yt["client_secret"]):
        rows.append(Row(False, "YouTube", "還沒連：.env 填 YOUTUBE_CLIENT_ID、YOUTUBE_CLIENT_SECRET，再跑 uv run office auth youtube"))
    elif not yt["refresh_token"]:
        rows.append(Row(False, "YouTube", "還沒連：uv run office auth youtube"))
    else:
        try:
            channel = YouTubeClient(yt["client_id"], yt["client_secret"], yt["refresh_token"], dry_run=False, http=http).channel()
            rows.append(Row(True, "YouTube", f"頻道「{channel['title']}」（{DESKS['youtube']}）"))
        except (PlatformError, httpx.HTTPError, KeyError) as error:
            rows.append(Row(False, "YouTube", f"授權失效，重新跑 uv run office auth youtube（{str(error)[:120]}）"))
    rows.append(media_row(settings, http))
    return rows


def github_row(settings: Settings, store: Store, http: httpx.Client | None = None) -> Row:
    """Can the token open draft pull requests in the office's repository? Reads only; nothing is created."""
    name = "GitHub"
    cred = credentials(settings, store)["github"]
    if not cred["token"]:
        return Row(None, name, "還沒連（資料更新提案核准後開不了 PR）：uv run office auth github，見 README「資料更新提案與 draft PR」")
    try:
        found = GitHubClient(cred["repo"], cred["token"], base=settings.github_base, dry_run=False, http=http).check()
    except (PlatformError, httpx.HTTPError) as error:
        return Row(False, name, f"權杖無效、過期，或看不到 {cred['repo']}：重新跑 uv run office auth github（{str(error)[:120]}）")
    mode = "模擬模式，只寫進 var/outbox/" if settings.github_simulated else "正式開 PR"
    if not found["can_push"]:
        return Row(False, name, f"權杖不能寫入 {found['repo']}：需要 Contents 與 Pull requests 的讀寫權限")
    if is_classic_token(cred["token"]):
        return Row(None, name, f"{found['repo']} 可用（{mode}），但這是傳統權杖，權限涵蓋你帳號所有 repo；建議換成只選這個 repo 的 fine-grained 權杖")
    return Row(True, name, f"{found['repo']}（{found['login'] or '權杖'}；{DESKS['github']}；{mode}）")


def media_row(settings: Settings, http: httpx.Client | None = None) -> Row:
    """Instagram and Threads fetch images and videos from a public URL, so the media host has to be reachable."""
    name = "圖片影片的公開網址"
    if settings.media_host == "supabase":
        if not (settings.supabase_url and settings.supabase_service_key):
            return Row(False, name, "OFFICE_MEDIA_HOST=supabase 還缺 SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY")
        key = settings.supabase_service_key
        try:
            response = (http or httpx.Client(timeout=30)).get(
                f"{settings.supabase_url}/storage/v1/bucket/{settings.supabase_bucket}",
                headers={"Authorization": f"Bearer {key}", "apikey": key},
            )
        except httpx.HTTPError as error:
            return Row(False, name, f"連不上 Supabase：{error}")
        if response.status_code >= 400:
            return Row(False, name, f"找不到 bucket「{settings.supabase_bucket}」，先在 Supabase Storage 建一個 public bucket")
        if not response.json().get("public"):
            return Row(False, name, f"bucket「{settings.supabase_bucket}」不是 public，Instagram 抓不到圖")
        return Row(True, name, f"Supabase bucket「{settings.supabase_bucket}」")
    if settings.media_host == "static":
        if not settings.public_base_url:
            return Row(False, name, "OFFICE_MEDIA_HOST=static 需要 OFFICE_PUBLIC_BASE_URL")
        if not settings.access_token:
            return Row(False, name, "辦公室對外公開時一定要設 OFFICE_ACCESS_TOKEN，不然任何人都能按核准")
        return Row(True, name, f"{settings.public_base_url}/media/")
    return Row(None, name, "還沒設定 OFFICE_MEDIA_HOST：Threads 不附圖只發文字，IG 貼文和影片要有它才發得出去")

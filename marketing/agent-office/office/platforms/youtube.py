"""YouTube uploads through the YouTube Data API v3 (OAuth refresh token, resumable upload).

Note from Google's docs: videos uploaded from an API project that has not passed the YouTube API compliance audit
are locked to private. Until the audit is approved, upload as private and switch visibility in YouTube Studio.
Shorts are ordinary uploads: vertical, at most 3 minutes, and #Shorts in the title helps classification.
"""

from __future__ import annotations

import json
import secrets
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .base import Client, PlatformError

TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
THUMBNAIL_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
API_URL = "https://www.googleapis.com/youtube/v3"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
EDUCATION_CATEGORY = "27"


class YouTubeClient(Client):
    name = "YouTube"

    def __init__(self, client_id: str, client_secret: str, refresh_token: str, **kwargs):
        super().__init__(**kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access = ""

    def _token(self) -> str:
        if self._access or self.dry_run:
            return self._access
        response = self.request(
            "POST",
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        self._access = response.json()["access_token"]
        return self._access

    def upload(self, path: Path, *, title: str, description: str, tags: list[str], privacy: str,
               thumbnail: Path | None = None) -> dict:
        metadata = {
            "snippet": {"title": title[:100], "description": description[:5000], "tags": tags[:15], "categoryId": EDUCATION_CATEGORY},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
        }
        size = path.stat().st_size
        headers = {
            "Authorization": f"Bearer {self._token()}",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        }
        session = self.request(
            "POST", f"{UPLOAD_URL}?uploadType=resumable&part=snippet,status", json=metadata, headers=headers, fake=None
        )
        if self.dry_run:
            video_id = self.fake_id("video")
            self.request("PUT", "(resumable upload session)", fake=None)
            return {"id": video_id, "url": f"https://youtu.be/{video_id}"}
        location = session.headers.get("Location")
        if not location:
            raise PlatformError("YouTube 沒有回傳上傳網址")
        uploaded = self.request(
            "PUT", location, content=path.read_bytes(), headers={"Authorization": f"Bearer {self._token()}", "Content-Type": "video/mp4"}
        )
        video_id = uploaded.json()["id"]
        if thumbnail and thumbnail.is_file():
            try:  # Custom thumbnails need a verified channel; a failure here should not fail the upload.
                self.request(
                    "POST", f"{THUMBNAIL_URL}?videoId={video_id}", content=thumbnail.read_bytes(),
                    headers={"Authorization": f"Bearer {self._token()}", "Content-Type": "image/jpeg"},
                )
            except PlatformError as error:
                self.log(f"封面沒有設定成功：{error}")
        return {"id": video_id, "url": f"https://youtu.be/{video_id}"}

    def stats(self, video_ids: list[str]) -> dict[str, dict]:
        if not video_ids:
            return {}
        response = self.request(
            "GET", f"{API_URL}/videos", params={"part": "statistics", "id": ",".join(video_ids)},
            headers={"Authorization": f"Bearer {self._token()}"}, fake=None,
        )
        if self.dry_run:
            return {}
        return {item["id"]: {k: int(v) for k, v in item.get("statistics", {}).items()} for item in response.json().get("items", [])}


def authorize(client_id: str, client_secret: str, port: int = 8765) -> str:
    """One-time desktop OAuth flow (loopback redirect). Returns a refresh token to put in .env."""
    import httpx

    state = secrets.token_urlsafe(16)
    redirect = f"http://127.0.0.1:{port}/"
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    print(f"用瀏覽器打開下面的網址，登入要發影片的 YouTube 頻道並同意授權：\n\n{AUTH_URL}?{query}\n")
    received: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - http.server API
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            received.update(params)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("授權完成，可以關掉這個分頁回到終端機。".encode())

        def log_message(self, *args):
            pass

    with HTTPServer(("127.0.0.1", port), Handler) as server:
        while "code" not in received and "error" not in received:
            server.handle_request()
    if received.get("state") != state or "code" not in received:
        raise PlatformError(f"授權失敗：{json.dumps(received, ensure_ascii=False)}")
    response = httpx.post(
        TOKEN_URL,
        data={
            "code": received["code"],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("refresh_token")
    if not token:
        raise PlatformError("Google 沒有回傳 refresh token；請到帳戶權限移除這個 app 後重試")
    return token

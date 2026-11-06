"""Threads and Instagram publishing through Meta's official Graph APIs.

Both use the same two-step flow: create a media container, wait until it is ready, then publish it. Images and videos
must sit at a public HTTPS URL (Instagram only accepts JPEG images), which is why the publisher uploads media to the
configured media host first.

Threads: https://developers.facebook.com/docs/threads  (graph.threads.net)
Instagram API with Instagram Login: https://developers.facebook.com/docs/instagram-platform  (graph.instagram.com)
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from .base import Client, PlatformError

THREADS_API = "https://graph.threads.net/v1.0"
THREADS_ROOT = "https://graph.threads.net"


def _squash(text: str | None) -> str:
    """Whitespace-insensitive form of a post's text, for matching what was sent against what Threads lists."""
    return " ".join((text or "").split())


def _parse_time(value: str | None) -> datetime | None:
    """Threads timestamps look like 2026-11-06T04:30:12+0000."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


class ThreadsClient(Client):
    name = "Threads"

    def __init__(self, user_id: str, token: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id or "{THREADS_USER_ID}"
        self.token = token

    def _call(self, method: str, path: str, fake=None, retry: bool = False, **params):
        response = self.request(method, f"{THREADS_API}/{path}", params={**params, "access_token": self.token}, fake=fake, retry=retry)
        return fake if self.dry_run else response.json()

    def _wait(self, container_id: str, attempts: int = 20) -> None:
        if self.dry_run:
            return
        for _ in range(attempts):
            status = self._call("GET", container_id, retry=True, fields="status,error_message")
            if status.get("status") in (None, "FINISHED"):
                return
            if status.get("status") in {"ERROR", "EXPIRED"}:
                raise PlatformError(f"Threads 容器 {container_id} 失敗：{status.get('error_message')}")
            time.sleep(3)
        raise PlatformError(f"Threads 容器 {container_id} 等太久還沒準備好")

    def post_text(self, text: str, *, topic_tag: str = "", reply_to_id: str = "", image_url: str = "") -> dict:
        params = {"media_type": "IMAGE", "image_url": image_url, "text": text} if image_url else {"media_type": "TEXT", "text": text}
        if topic_tag:
            params["topic_tag"] = topic_tag
        if reply_to_id:
            params["reply_to_id"] = reply_to_id
        # Making a container publishes nothing, so a temporary failure here can simply be tried again.
        container = self._call("POST", f"{self.user_id}/threads", fake={"id": self.fake_id("container")}, retry=True, **params)
        return self._publish(container["id"], text=text, reply_to_id=reply_to_id)

    def post_carousel(self, image_urls: list[str], text: str, *, topic_tag: str = "") -> dict:
        """One post with several pictures that swipe: a container per picture, then one carousel container that holds them."""
        if not 2 <= len(image_urls) <= 20:
            raise PlatformError("Threads 輪播需要 2～20 張圖")
        children = [
            self._call("POST", f"{self.user_id}/threads", fake={"id": self.fake_id("child")}, retry=True,
                       media_type="IMAGE", image_url=url, is_carousel_item="true")["id"]
            for url in image_urls
        ]
        for child in children:
            self._wait(child)
        params = {"media_type": "CAROUSEL", "children": ",".join(children), "text": text}
        if topic_tag:
            params["topic_tag"] = topic_tag
        container = self._call("POST", f"{self.user_id}/threads", fake={"id": self.fake_id("container")}, retry=True, **params)
        return self._publish(container["id"], text=text)

    def _publish(self, container_id: str, *, text: str = "", reply_to_id: str = "") -> dict:
        """Publish a ready container.

        A temporary failure here can be a lost answer: Meta may answer 500 (or time out) after the post is already live.
        Reporting that as a failure would hide a real post, and repeating the publish blindly could post it twice. So after
        a temporary failure the account is looked at first; only a post that is not there is published again.
        """
        self._wait(container_id)
        started = datetime.now(timezone.utc)
        waits = self.retry_waits or (0.0,)
        published, last_error = None, None
        for attempt in range(len(waits) + 1):
            try:
                published = self._call("POST", f"{self.user_id}/threads_publish", fake={"id": self.fake_id("thread")}, creation_id=container_id)
                break
            except PlatformError as error:
                if not error.transient:
                    raise
                last_error = error
                self._pause(waits[min(attempt, len(waits) - 1)])
                found = self._already_posted(text, reply_to_id, started)
                if found:
                    self.log(f"Threads 回了暫時性錯誤，但貼文其實已經發出去了（{found['id']}）")
                    return found
        if published is None:
            raise last_error
        media_id = published["id"]
        link = self._call("GET", media_id, fake={"permalink": ""}, retry=True, fields="permalink")
        return {"id": media_id, "url": link.get("permalink", "")}

    def _already_posted(self, text: str, reply_to_id: str, since: datetime) -> dict | None:
        """The account's own recent post (or reply) with exactly this text, made since `since`; None when there is none or
        the account cannot be read right now."""
        wanted = _squash(text)
        if not wanted or self.dry_run:
            return None
        path = f"{self.user_id}/replies" if reply_to_id else f"{self.user_id}/threads"
        try:
            data = self._call("GET", path, fields="id,text,permalink,timestamp", limit=25)
        except PlatformError:
            return None
        for item in data.get("data", []):
            if _squash(item.get("text")) != wanted:
                continue
            made = _parse_time(item.get("timestamp"))
            if made is not None and made < since - timedelta(minutes=5):
                continue  # the same words posted earlier are not this post
            return {"id": str(item.get("id", "")), "url": item.get("permalink", "")}
        return None

    def username(self) -> str:
        return self._call("GET", self.user_id, fake={"username": ""}, fields="username").get("username", "")

    def me(self) -> dict:
        """The account this token belongs to: {"id", "username"}."""
        data = self._call("GET", "me", fake={"id": "", "username": ""}, fields="id,username")
        return {"id": str(data.get("id", "")), "username": data.get("username", "")}

    def replies(self, media_id: str) -> list[dict]:
        data = self._call("GET", f"{media_id}/replies", fake={"data": []}, fields="id,text,username,timestamp")
        return [r for r in data.get("data", []) if r.get("text")]

    def insights(self, media_id: str) -> dict:
        data = self._call("GET", f"{media_id}/insights", fake={"data": []}, metric="views,likes,replies,reposts,quotes,shares")
        return _metric_values(data)

    def refresh_token(self) -> dict:
        response = self.request(
            "GET", f"{THREADS_ROOT}/refresh_access_token",
            params={"grant_type": "th_refresh_token", "access_token": self.token}, fake={},
        )
        return {} if self.dry_run else response.json()

    def exchange_token(self, short_token: str, app_secret: str) -> dict:
        response = self.request(
            "GET", f"{THREADS_ROOT}/access_token",
            params={"grant_type": "th_exchange_token", "client_secret": app_secret, "access_token": short_token}, fake={},
        )
        return {} if self.dry_run else response.json()


class InstagramClient(Client):
    name = "Instagram"

    def __init__(self, user_id: str, token: str, host: str = "graph.instagram.com", version: str = "v24.0", **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id or "{INSTAGRAM_USER_ID}"
        self.token = token
        self.host = host
        self.base = f"https://{host}/{version}"

    def _call(self, method: str, path: str, fake=None, **params):
        response = self.request(method, f"{self.base}/{path}", params={**params, "access_token": self.token}, fake=fake)
        return fake if self.dry_run else response.json()

    def _container(self, fake_prefix: str = "container", **params) -> str:
        return self._call("POST", f"{self.user_id}/media", fake={"id": self.fake_id(fake_prefix)}, **params)["id"]

    def _wait(self, container_id: str, attempts: int = 60, delay: float = 5.0) -> None:
        """Videos are processed asynchronously; poll status_code until FINISHED."""
        if self.dry_run:
            return
        for _ in range(attempts):
            status = self._call("GET", container_id, fields="status_code,status")
            code = status.get("status_code")
            if code in (None, "FINISHED"):
                return
            if code in {"ERROR", "EXPIRED"}:
                raise PlatformError(f"Instagram 容器 {container_id} 失敗：{status.get('status')}")
            time.sleep(delay)
        raise PlatformError(f"Instagram 容器 {container_id} 處理超過 {attempts * delay:.0f} 秒")

    def _publish(self, container_id: str, attempts: int = 4, delay: float = 5.0) -> dict:
        # Right after a container reports FINISHED, media_publish can still answer 2207006 ("media not found") for a while.
        for attempt in range(attempts):
            try:
                published = self._call("POST", f"{self.user_id}/media_publish", fake={"id": self.fake_id("media")}, creation_id=container_id)
                break
            except PlatformError as error:
                if "2207006" not in str(error):
                    raise
                if attempt == attempts - 1:
                    raise PlatformError(
                        f"Instagram 一直找不到素材容器 {container_id}（試了 {attempts} 次）：多半是 IG 抓不到圖片或影片網址，"
                        f"或容器已過期。請在審核匣再按一次核准；還是失敗就確認媒體網址能在無痕視窗打開。原始訊息：{error}"
                    ) from None
                time.sleep(delay)
                self._wait(container_id, attempts=10, delay=delay)
        media_id = published["id"]
        link = self._call("GET", media_id, fake={"permalink": ""}, fields="permalink")
        return {"id": media_id, "url": link.get("permalink", "")}

    def post_carousel(self, image_urls: list[str], caption: str) -> dict:
        if not 2 <= len(image_urls) <= 10:
            raise PlatformError("Instagram 輪播需要 2～10 張圖")
        children = [self._container("child", image_url=url, is_carousel_item="true") for url in image_urls]
        for child in children:
            self._wait(child, attempts=20, delay=2)
        parent = self._container(media_type="CAROUSEL", children=",".join(children), caption=caption)
        self._wait(parent, attempts=30, delay=2)
        return self._publish(parent)

    def post_reel(self, video_url: str, caption: str, cover_url: str = "") -> dict:
        params = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true"}
        if cover_url:
            params["cover_url"] = cover_url
        container = self._container(**params)
        self._wait(container)
        return self._publish(container)

    def post_story(self, image_url: str) -> dict:
        container = self._container(media_type="STORIES", image_url=image_url)
        self._wait(container, attempts=20, delay=2)
        return self._publish(container)

    def username(self) -> str:
        return self._call("GET", self.user_id, fake={"username": ""}, fields="username").get("username", "")

    def me(self) -> dict:
        """The professional account this token belongs to: {"id", "username"}. With Instagram Login, `user_id` is the
        ID that publishing uses (`id` is app-scoped); through graph.facebook.com the ID has to come from .env."""
        if self.host != "graph.instagram.com":
            data = self._call("GET", self.user_id, fake={"id": "", "username": ""}, fields="id,username")
            return {"id": str(data.get("id", "")), "username": data.get("username", "")}
        data = self._call("GET", "me", fake={"user_id": "", "username": ""}, fields="user_id,username")
        return {"id": str(data.get("user_id") or data.get("id", "")), "username": data.get("username", "")}

    def comments(self, media_id: str) -> list[dict]:
        data = self._call("GET", f"{media_id}/comments", fake={"data": []}, fields="id,text,username,timestamp")
        return [c for c in data.get("data", []) if c.get("text")]

    def recent_comments(self, media_id: str, limit: int = 50) -> list[dict]:
        """The newest comments on a post (newest first), with who wrote them and when: what the keyword rules read."""
        data = self._call("GET", f"{media_id}/comments", fake={"data": []}, fields="id,text,username,timestamp", limit=limit)
        return [c for c in data.get("data", []) if c.get("text")]

    def private_reply(self, comment_id: str, text: str) -> dict:
        """Answer a comment with a private message. Meta allows one per comment, within 7 days, up to 1000 bytes; the commenter
        does not have to follow us. Needs the instagram_business_manage_messages permission."""
        fake = {"recipient_id": self.fake_id("user"), "message_id": self.fake_id("dm")}
        response = self.request(
            "POST", f"{self.base}/{self.user_id}/messages", params={"access_token": self.token},
            json={"recipient": {"comment_id": comment_id}, "message": {"text": text}}, fake=fake,
        )
        data = fake if self.dry_run else response.json()
        return {"id": data.get("message_id", ""), "recipient": data.get("recipient_id", "")}

    def can_message(self) -> bool:
        """Read-only: does this token reach the messaging side at all? (An error is raised when the permission is missing.)"""
        self._call("GET", f"{self.user_id}/conversations", fake={"data": []}, platform="instagram", limit=1)
        return True

    def reply_comment(self, comment_id: str, message: str) -> dict:
        data = self._call("POST", f"{comment_id}/replies", fake={"id": self.fake_id("reply")}, message=message)
        return {"id": data["id"], "url": ""}

    def insights(self, media_id: str) -> dict:
        data = self._call("GET", f"{media_id}/insights", fake={"data": []}, metric="reach,likes,comments,saved,shares,views")
        return _metric_values(data)

    def refresh_token(self) -> dict:
        response = self.request(
            "GET", f"https://{self.host}/refresh_access_token",
            params={"grant_type": "ig_refresh_token", "access_token": self.token}, fake={},
        )
        return {} if self.dry_run else response.json()

    def exchange_token(self, short_token: str, app_secret: str) -> dict:
        response = self.request(
            "GET", f"https://{self.host}/access_token",
            params={"grant_type": "ig_exchange_token", "client_secret": app_secret, "access_token": short_token}, fake={},
        )
        return {} if self.dry_run else response.json()


def _metric_values(payload: dict) -> dict:
    values = {}
    for metric in payload.get("data", []):
        if "total_value" in metric:
            values[metric["name"]] = metric["total_value"].get("value", 0)
        elif metric.get("values"):
            values[metric["name"]] = metric["values"][0].get("value", 0)
    return values

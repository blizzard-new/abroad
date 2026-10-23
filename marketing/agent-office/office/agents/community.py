"""社群互動：發文後的黃金 30 分鐘去看留言，擬好回覆送老闆審核（回覆陌生人一律要人工核准）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..llm import WriterError
from ..platforms.base import PlatformError
from .base import Agent, Persona

WINDOW = (timedelta(minutes=30), timedelta(hours=3))


class Community(Agent):
    persona = Persona(
        id="community",
        name="Momo",
        title="社群互動",
        duty="發文後 30 分鐘內看留言、擬回覆；回覆一律等老闆核准才送出",
        hair="curly",
        hair_color="#c0392b",
        shirt="#ff8fab",
        accessory="none",
        decor="heart",
    )

    def check(self, now: datetime | None = None) -> int:
        office = self.office
        now = now or datetime.now(timezone.utc)
        since = (now - WINDOW[1]).isoformat(timespec="seconds")
        until = (now - WINDOW[0]).isoformat(timespec="seconds")
        posts = [
            d for d in office.store.published_since(since)
            if d["published_at"] <= until and d["format"] in {"text", "carousel", "reel"} and d["channel"] in {"threads", "instagram"}
            and d["remote_id"] and not d["remote_id"].startswith("dry-") and not office.store.get(f"community:{d['id']}")
        ]
        queued = 0
        for post in posts:
            office.store.set(f"community:{post['id']}", now.isoformat(timespec="seconds"))
            queued += self._answer(post)
        return queued

    def _answer(self, post: dict) -> int:
        office = self.office
        clients = office.staff["publisher"].clients()
        self.status("working", f"看留言：{post['title'][:14]}")
        try:
            if post["channel"] == "threads":
                comments = clients["threads"].replies(post["remote_id"])
            else:
                comments = clients["instagram"].comments(post["remote_id"])
        except PlatformError as error:
            self.status("error", "留言抓不到", screen={"type": "chat", "messages": [{"from": "system", "text": str(error)[:80]}]})
            return 0
        own = self._own_handle(post["channel"], clients[post["channel"]])
        comments = [c for c in comments if c.get("username") != own][:10]
        if not comments:
            self.status("idle", "這篇還沒有新留言")
            return 0
        post_text = post["payload"].get("text") or post["payload"].get("caption_full") or post["title"]
        try:
            batch = office.writer.replies(post_text, comments, office.briefing_for_replies())
        except WriterError as error:
            self.status("error", f"擬回覆失敗：{error}")
            return 0
        by_id = {c["id"]: c for c in comments}
        queued = 0
        messages = []
        for reply in batch.replies:
            comment = by_id.get(reply.comment_id)
            if not comment:
                continue
            office.queue_reply(post, comment, reply.text, sender=self)
            messages += [{"from": comment.get("username", "訪客"), "text": comment["text"][:60]}, {"from": "我們", "text": reply.text[:60]}]
            queued += 1
        self.status("waiting" if queued else "idle", f"擬好 {queued} 則回覆，等老闆核准", screen={"type": "chat", "messages": messages[-6:]})
        return queued

    def _own_handle(self, channel: str, client) -> str:
        """Our own first replies come back in the reply list; skip them by username."""
        key = f"handle:{channel}"
        handle = self.office.store.get(key)
        if not handle:
            try:
                handle = client.username()
            except PlatformError:
                return ""
            if handle:
                self.office.store.set(key, handle)
        return handle or ""

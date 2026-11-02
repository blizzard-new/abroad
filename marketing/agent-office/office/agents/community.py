"""社群互動：發文後的黃金 30 分鐘去看留言，擬好回覆送老闆審核（回覆陌生人一律要人工核准）。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from .. import autodm
from ..llm import WriterError
from ..platforms.base import PlatformError
from .base import Agent, Persona

WINDOW = (timedelta(minutes=30), timedelta(hours=3))


class Community(Agent):
    persona = Persona(
        id="community",
        name="Momo",
        title="社群互動",
        duty="發文後 30 分鐘內看留言、擬回覆（回覆一律等老闆核准才送出）；留言裡有老闆設定的關鍵字，就自動私訊老闆寫好的內容",
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

    # ---- comment keyword -> private message (the boss's rules, see autodm.py) ----
    def auto_dm(self, now: datetime | None = None) -> int:
        """Answer comments that carry one of the boss's keywords with the boss's own private message. Returns how many went out."""
        office, store, settings = self.office, self.office.store, self.office.settings
        now = now or datetime.now(timezone.utc)
        records = autodm.rules(store)
        if not settings.auto_dm or not records or autodm.blocked(store, now):
            return 0
        since = (now - autodm.REPLY_WINDOW).isoformat(timespec="seconds")
        posts = [
            d for d in store.published_since(since)
            if d["channel"] == "instagram" and d["format"] in {"carousel", "reel"} and d["remote_id"] and not d["remote_id"].startswith("dry-")
            and any(r["draft_id"] in (0, d["id"]) for r in records) and self._scan_due(d, now)
        ]
        if not posts:
            return 0
        client = office.staff["publisher"].clients()["instagram"]
        own = self._own_handle("instagram", client)
        sent = 0
        for post in posts:
            store.set(f"dm_scan:{post['id']}", now.isoformat(timespec="seconds"))
            sent += self._dm_post(client, post, [r for r in records if r["draft_id"] in (0, post["id"])], own, now)
            if autodm.blocked(store, now):
                break
        if sent:
            self.status("working", f"自動私訊了 {sent} 位", screen={"type": "lines", "title": "留言自動私訊", "lines": [autodm.describe(r) for r in records[:5]]})
            self._dm_report(now)
        return sent

    def _scan_due(self, post: dict, now: datetime) -> bool:
        """Fresh posts are read every couple of minutes (most comments come early); older ones less and less often."""
        published = datetime.fromisoformat(post["published_at"])
        published = published if published.tzinfo else published.replace(tzinfo=timezone.utc)
        age = now - published
        every = timedelta(minutes=2) if age < timedelta(hours=24) else timedelta(minutes=10) if age < timedelta(hours=72) else timedelta(minutes=30)
        last = self.office.store.get(f"dm_scan:{post['id']}")
        return not last or now - datetime.fromisoformat(last) >= every

    def _dm_post(self, client, post: dict, records: list[dict], own: str, now: datetime) -> int:
        office, store, settings = self.office, self.office.store, self.office.settings
        try:
            comments = client.recent_comments(post["remote_id"])
        except PlatformError as error:
            self._dm_trouble(autodm.classify(error), error, now)
            return 0
        day = now.astimezone(settings.timezone).date()
        sent = failures = 0
        for comment in sorted(comments, key=lambda c: c.get("timestamp") or ""):
            comment_id, who = str(comment.get("id", "")), comment.get("username") or ""
            if not comment_id or who == own or autodm.handled(store, comment_id):
                continue
            rule = autodm.match(records, comment["text"])
            if not rule:
                continue
            wrote = autodm.comment_time(comment.get("timestamp"))
            if wrote is None or wrote < datetime.fromisoformat(rule["created"]):
                continue  # written before the rule existed: not a request for this
            if now - wrote > autodm.REPLY_WINDOW - autodm.EDGE:
                autodm.mark(store, comment_id, "too old")
                continue
            if autodm.recently_messaged(store, rule["id"], who, now):
                autodm.mark(store, comment_id, "same person")
                continue
            if autodm.sent_on(store, day) >= settings.auto_dm_limit:
                tomorrow = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=settings.timezone)
                reason = f"今天已經自動私訊 {settings.auto_dm_limit} 位，到每日上限了，明天自動繼續（上限在 .env 的 OFFICE_AUTO_DM_LIMIT）"
                if autodm.block(store, reason, now, tomorrow - now):
                    office.chat("chief", f"⏸ 留言自動私訊：{reason}")
                return sent
            try:
                client.private_reply(comment_id, rule["message"])
            except PlatformError as error:
                kind = autodm.classify(error)
                if kind in {"permission", "token", "limit"}:
                    self._dm_trouble(kind, error, now)
                    return sent
                autodm.mark(store, comment_id, f"failed: {kind}: {str(error)[:120]}")
                autodm.bump(store, rule["id"], failed=1)
                failures += 1
                if failures >= autodm.GIVE_UP_AFTER:
                    self._dm_trouble("other", error, now)
                    return sent
                continue
            failures = 0
            stamp = now.isoformat(timespec="seconds")
            autodm.mark(store, comment_id, "sent")
            autodm.mark_person(store, rule["id"], who, now)
            autodm.count_sent(store, day)
            autodm.bump(store, rule["id"], sent=1, when=stamp)
            self._dm_remember(rule)
            sent += 1
            if rule.get("public_reply"):  # a courtesy under the comment; the message has already gone, so a failure here costs nothing
                try:
                    client.reply_comment(comment_id, rule["public_reply"])
                except PlatformError as error:
                    self.log(f"私訊傳了，但公開回覆沒成功：{str(error)[:80]}")
        return sent

    def _dm_trouble(self, kind: str, error: Exception, now: datetime) -> None:
        """Meta said no: stop for a while (it tries again by itself) and tell the boss once."""
        store = self.office.store
        reason = autodm.explain(kind) or f"連續傳不出去：{str(error)[:160]}"
        pause = autodm.LIMIT_PAUSE if kind == "limit" else autodm.PERMISSION_PAUSE
        fresh = autodm.block(store, reason, now, pause)
        self.status("error", "自動私訊暫停", screen={"type": "chat", "messages": [{"from": "system", "text": reason[:80]}]})
        if fresh and kind != "limit":
            self.office.chat("chief", f"⚠️ 留言自動私訊先暫停了：{reason}\n我每 30 分鐘會自己再試一次，修好就會恢復；已經留言但還沒收到的人，7 天內都還來得及補傳。")

    def _dm_remember(self, rule: dict) -> None:
        pending = json.loads(self.office.store.get("dm_pending") or "{}")
        pending[str(rule["id"])] = pending.get(str(rule["id"]), 0) + 1
        self.office.store.set("dm_pending", json.dumps(pending))

    def _dm_report(self, now: datetime) -> None:
        """One line in the chat every half hour at most: who was messaged for which rule."""
        store = self.office.store
        last = store.get("dm_reported_at")
        if last and now - datetime.fromisoformat(last) < timedelta(minutes=30):
            return
        pending = json.loads(store.get("dm_pending") or "{}")
        if not pending:
            return
        names = {str(r["id"]): r["keywords"][0] for r in autodm.rules(store)}
        total = sum(pending.values())
        detail = "、".join(f"D{rule_id}「{names.get(rule_id, '已刪除')}」{count} 位" for rule_id, count in pending.items())
        store.set("dm_pending", "{}")
        store.set("dm_reported_at", now.isoformat(timespec="seconds"))
        self.office.chat("chief", f"📨 Momo 剛剛自動私訊了 {total} 位（{detail}）")

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

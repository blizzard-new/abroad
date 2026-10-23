"""發佈排程：到時間就呼叫 Threads／Instagram／YouTube 的官方 API 發文；模擬模式只把要送出的內容寫進 outbox。"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ..platforms.base import PlatformError
from ..platforms.media_host import MediaHost
from ..platforms.meta import InstagramClient, ThreadsClient
from ..platforms.youtube import YouTubeClient
from ..store import now_utc
from .base import Agent, Persona

PLATFORM_LABEL = {"threads": "Threads", "instagram": "Instagram", "youtube": "YouTube"}


class Publisher(Agent):
    persona = Persona(
        id="publisher",
        name="Pat",
        title="發佈排程",
        duty="到排定時間呼叫各平台官方 API 發文，並在 Threads 第一則留言補上連結",
        hair="cap",
        hair_color="#3b2a20",
        shirt="#6c5ce7",
        accessory="cap",
        decor="rocket",
    )

    def __init__(self, office):
        super().__init__(office)
        self.lines: list[str] = []

    def _log(self, line: str) -> None:
        self.lines = (self.lines + [line])[-8:]
        self.status("working", line[:24], screen={"type": "terminal", "lines": list(self.lines)})

    def clients(self) -> dict:
        settings, store = self.office.settings, self.office.store
        dry = settings.dry_run
        return {
            "threads": ThreadsClient(settings.threads_user_id, store.get("threads_token") or settings.threads_token, dry_run=dry, log=self._log),
            "instagram": InstagramClient(
                settings.instagram_user_id, store.get("instagram_token") or settings.instagram_token,
                host=settings.instagram_graph_host, dry_run=dry, log=self._log,
            ),
            "youtube": YouTubeClient(settings.youtube_client_id, settings.youtube_client_secret, settings.youtube_refresh_token, dry_run=dry, log=self._log),
            "media": MediaHost(settings, dry_run=dry, log=self._log),
        }

    def missing_credentials(self, channel: str) -> bool:
        s, store = self.office.settings, self.office.store
        if s.dry_run:
            return False
        if channel == "threads":
            return not (s.threads_user_id and (store.get("threads_token") or s.threads_token))
        if channel == "instagram":
            return not (s.instagram_user_id and (store.get("instagram_token") or s.instagram_token))
        return not (s.youtube_client_id and s.youtube_client_secret and s.youtube_refresh_token)

    def publish_due(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        due = self.office.store.due_drafts(now.isoformat(timespec="seconds"))
        for draft in due:
            self.publish(draft)
        if due:
            self.status("idle", f"發完 {len(due)} 則", screen={"type": "terminal", "lines": list(self.lines)})
        return len(due)

    def publish(self, draft: dict) -> dict:
        store = self.office.store
        label = PLATFORM_LABEL[draft["channel"]]
        if self.missing_credentials(draft["channel"]):
            store.update_draft(draft["id"], status="failed", error=f"{label} 帳號還沒設定（見 README 的帳號設定）")
            self.status("error", f"{label} 帳號還沒設定")
            self.office.draft_changed(draft["id"])
            return store.draft(draft["id"])
        store.update_draft(draft["id"], status="publishing")
        self.office.draft_changed(draft["id"])
        self.lines = []
        self.status("working", f"發 {label}：{draft['title'][:14]}", screen={"type": "terminal", "lines": []})
        clients = self.clients()
        try:
            result = self._send(draft, clients)
        except (PlatformError, OSError, KeyError, ValueError) as error:
            store.update_draft(draft["id"], status="failed", error=str(error)[:500])
            self.status("error", f"{label} 發佈失敗", screen={"type": "terminal", "lines": list(self.lines) + [str(error)[:80]]})
            self.office.draft_changed(draft["id"])
            return store.draft(draft["id"])
        if self.office.settings.dry_run:
            self._write_outbox(draft, clients)
        store.update_draft(
            draft["id"], status="published", published_at=now_utc(), remote_id=result.get("id"), remote_url=result.get("url") or None,
            note="模擬發佈（沒有真的送出）" if self.office.settings.dry_run else None, error=None,
        )
        self.status("done", f"{label} 發佈完成 🚀", screen={"type": "terminal", "lines": list(self.lines)})
        self.office.draft_changed(draft["id"])
        return store.draft(draft["id"])

    def _send(self, draft: dict, clients: dict) -> dict:
        payload, media = draft["payload"], draft["media"] or {}
        channel, fmt = draft["channel"], draft["format"]
        needed = {"carousel": "images", "reel": "video", "story": "image", "short": "video", "long": "video"}.get(fmt)
        if needed and not media.get(needed):
            raise ValueError("這則還沒有輸出圖片或影片（OFFICE_RENDER_MEDIA=0 時只寫文案），請重新製作後再發佈")
        files = self.office.media_file
        if channel == "threads":
            threads: ThreadsClient = clients["threads"]
            if fmt == "reply":
                return threads.post_text(payload["text"], reply_to_id=payload["reply_to_id"])
            post = threads.post_text(payload["text"], topic_tag=payload.get("topic_tag", ""))
            if payload.get("first_reply"):
                threads.post_text(payload["first_reply"], reply_to_id=post["id"])
            return post
        if channel == "instagram":
            instagram: InstagramClient = clients["instagram"]
            host: MediaHost = clients["media"]
            if fmt == "reply":
                return instagram.reply_comment(payload["reply_to_id"], payload["text"])
            if fmt == "carousel":
                urls = [host.public_url(files(ref)) for ref in media["images"]]
                return instagram.post_carousel(urls, payload["caption_full"])
            if fmt == "reel":
                cover = host.public_url(files(media["poster"])) if media.get("poster") else ""
                return instagram.post_reel(host.public_url(files(media["video"])), payload["caption_full"], cover)
            if fmt == "story":
                return instagram.post_story(host.public_url(files(media["image"])))
        if channel == "youtube":
            youtube: YouTubeClient = clients["youtube"]
            return youtube.upload(
                files(media["video"]), title=payload["title"], description=payload["description"], tags=payload.get("tags", []),
                privacy=self.office.settings.youtube_privacy,
                thumbnail=files(media["poster"]) if fmt == "long" and media.get("poster") else None,
            )
        raise ValueError(f"不支援的發佈格式 {channel}/{fmt}")

    def _write_outbox(self, draft: dict, clients: dict) -> None:
        calls = [call for client in clients.values() for call in client.calls]
        folder = self.office.settings.outbox_dir / draft["day"]
        folder.mkdir(parents=True, exist_ok=True)
        record = {"draft_id": draft["id"], "channel": draft["channel"], "format": draft["format"], "title": draft["title"], "calls": calls}
        (folder / f"{draft['id']:05d}-{draft['channel']}-{draft['format']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def refresh_tokens(self) -> list[str]:
        """Long-lived Meta tokens last about 60 days; refreshing weekly keeps them alive."""
        refreshed = []
        clients = self.clients()
        for key in ("threads", "instagram"):
            if self.missing_credentials(key) or self.office.settings.dry_run:
                continue
            try:
                token = clients[key].refresh_token().get("access_token")
            except PlatformError as error:
                self.log(f"{PLATFORM_LABEL[key]} token 更新失敗：{error}")
                continue
            if token:
                self.office.store.set(f"{key}_token", token)
                refreshed.append(key)
        return refreshed

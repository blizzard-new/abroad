"""發佈排程：發文前由這張桌子的 AI 做最後檢查，到時間就呼叫 Threads／Instagram／YouTube 的官方 API 發文；
你核准的資料更新提案，也由這張桌子用固定程式開成 GitHub 的 draft PR（只開 draft，不合併）。
模擬模式只把要送出的內容寫進 outbox。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from .. import accounts
from ..llm import WriterError
from ..platforms.base import PlatformError
from ..platforms.github import GitHubClient
from ..platforms.media_host import MediaHost
from ..platforms.meta import InstagramClient, ThreadsClient
from ..platforms.youtube import YouTubeClient
from ..proposals import FORMAT as PROPOSAL_FORMAT, Proposal
from ..store import now_utc
from .base import Agent, Persona

PLATFORM_LABEL = {"threads": "Threads", "instagram": "Instagram", "youtube": "YouTube", "github": "GitHub"}
PREFLIGHT_HOLD = "發文前檢查擋下："


class Publisher(Agent):
    persona = Persona(
        id="publisher",
        name="Pat",
        title="發佈排程",
        duty="到排定時間呼叫各平台官方 API 發文，並在 Threads 第一則留言補上連結；也把你核准的資料更新提案開成 GitHub draft PR（不合併）",
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
        settings = self.office.settings
        dry = settings.dry_run
        creds = accounts.credentials(settings, self.office.store)
        threads, instagram, youtube = creds["threads"], creds["instagram"], creds["youtube"]
        return {
            "threads": ThreadsClient(threads["user_id"], threads["token"], dry_run=dry, log=self._log),
            "instagram": InstagramClient(
                instagram["user_id"], instagram["token"], host=settings.instagram_graph_host, dry_run=dry, log=self._log,
            ),
            "youtube": YouTubeClient(
                youtube["client_id"], youtube["client_secret"], youtube["refresh_token"], dry_run=dry, log=self._log,
            ),
            "media": MediaHost(settings, dry_run=dry, log=self._log),
            "github": GitHubClient(
                creds["github"]["repo"], creds["github"]["token"], base=settings.github_base, dry_run=settings.github_simulated, log=self._log,
            ),
        }

    def simulated(self, channel: str) -> bool:
        """Whether this channel only records what it would send: GitHub has its own switch, the rest follow OFFICE_DRY_RUN."""
        settings = self.office.settings
        return settings.github_simulated if channel == "github" else settings.dry_run

    def missing_credentials(self, channel: str) -> bool:
        if self.simulated(channel):
            return False
        return not accounts.connected(self.office.settings, self.office.store, channel)

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
            hint = "uv run office auth github" if draft["channel"] == "github" else "見 README 的帳號設定"
            store.update_draft(draft["id"], status="failed", error=f"{label} 帳號還沒設定（{hint}）")
            self.status("error", f"{label} 帳號還沒設定")
            self.office.draft_changed(draft["id"])
            return store.draft(draft["id"])
        if not self._preflight_ok(draft):
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
        simulated = self.simulated(draft["channel"])
        if simulated:
            self._write_outbox(draft, clients)
        store.update_draft(
            draft["id"], status="published", published_at=now_utc(), remote_id=result.get("id"), remote_url=result.get("url") or None,
            note="模擬發佈（沒有真的送出）" if simulated else None, error=None,
        )
        done = "draft PR 開好了 📮" if draft["channel"] == "github" else f"{label} 發佈完成 🚀"
        self.status("done", done, screen={"type": "terminal", "lines": list(self.lines)})
        self.office.draft_changed(draft["id"])
        return store.draft(draft["id"])

    def _preflight_ok(self, draft: dict) -> bool:
        """This desk's brain takes a last look before a post goes out. It can only hold a post back for the boss;
        the API calls themselves stay plain code, so an AI never decides what gets sent where."""
        writer = self.office.writer
        review = draft.get("review") or {}
        if draft["format"] in {"reply", "story", PROPOSAL_FORMAT} or review.get("preflight_overridden") or not writer.uses_model("publisher"):
            return True
        self.status("reviewing", f"發文前最後檢查：{draft['title'][:12]}")
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
        recent = [d["title"] for d in self.office.store.published_since(since) if d["id"] != draft["id"]]
        try:
            verdict = writer.preflight(draft, recent, self.office.briefing_for_replies())
        except WriterError as error:
            self.log(f"發文前檢查沒有完成，照常發佈：{error}")
            return True
        if verdict.go:
            return True
        issues = list(review.get("issues") or []) + [f"{PREFLIGHT_HOLD}{verdict.reason}"]
        self.office.store.update_draft(draft["id"], status="needs_changes", review={**review, "issues": issues})
        self.status("waiting", f"先不發：{verdict.reason[:20]}")
        self.handoff("boss", "發文前擋下", draft_id=draft["id"])
        self.office.draft_changed(draft["id"])
        return False

    def _send(self, draft: dict, clients: dict) -> dict:
        payload, media = draft["payload"], draft["media"] or {}
        channel, fmt = draft["channel"], draft["format"]
        needed = {"carousel": "images", "reel": "video", "story": "image", "short": "video", "long": "video"}.get(fmt)
        if needed and not media.get(needed):
            raise ValueError("這則還沒有輸出圖片或影片（OFFICE_RENDER_MEDIA=0 時只寫文案），請重新製作後再發佈")
        files = self.office.media_file
        if channel == "github" and fmt == PROPOSAL_FORMAT:
            proposal = Proposal.from_payload(payload)
            return clients["github"].open_draft_pr(
                branch=proposal.branch, path=proposal.path, content=proposal.content(), commit_message=proposal.commit_message(),
                title=proposal.pr_title(), body=proposal.pr_body(),
            )
        if channel == "threads":
            threads: ThreadsClient = clients["threads"]
            if fmt == "reply":
                return threads.post_text(payload["text"], reply_to_id=payload["reply_to_id"])
            # Without a public media host the picture cannot reach Threads, so the post goes out as text as before.
            attach = media.get("image") and self.office.settings.media_host != "none"
            image = clients["media"].public_url(files(media["image"])) if attach else ""
            post = threads.post_text(payload["text"], topic_tag=payload.get("topic_tag", ""), image_url=image)
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

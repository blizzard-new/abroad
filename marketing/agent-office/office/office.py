"""The office itself: shared storage, the event bus, the writer, the renderer and the staff at their desks."""

from __future__ import annotations

import threading
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from .agents.analyst import Analyst
from .agents.base import Agent
from .agents.chief import Chief
from .agents.community import Community
from .agents.designer import Designer
from .agents.publisher import PREFLIGHT_HOLD, Publisher
from .agents.reviewer import Reviewer
from .agents.strategist import Strategist
from .agents.threads_writer import ThreadsWriter
from .agents.video_editor import VideoEditor
from . import brains
from .brand import Briefing, load_facts, load_news
from .config import Settings
from .events import EventBus
from .llm import make_writer
from .models import PlanItem
from .render.renderer import Renderer
from .store import Store

# Desk order on the floor, front row first. The chief sits next to your desk, between you and the team.
STAFF: tuple[type[Agent], ...] = (Strategist, ThreadsWriter, Designer, VideoEditor, Reviewer, Publisher, Analyst, Community, Chief)

def desk_of(role: str) -> str:
    """The desk a brain role belongs to: Ivy both researches and plans."""
    return "strategist" if role == "research" else role


# The human's desk. Drafts land here unless OFFICE_APPROVAL=auto.
BOSS = {"id": "boss", "name": "你", "title": "老闆（審核）", "duty": "看審核匣：核准、退回或直接修改草稿"}


class Office:
    def __init__(self, settings: Settings, *, writer=None, renderer=None, images=None):
        self.settings = settings
        self.store = Store(settings.db_path)
        self.bus = EventBus(self.store)
        self._brain_seen: dict[str, str] = {}
        self.writer = writer or make_writer(settings, on_brain=self._brain_used)
        self.renderer = renderer or Renderer(settings)
        # Cover illustrations: Codex's image generation when OFFICE_IMAGES=codex.
        self.images = images if images is not None else (brains.CodexBrain(settings) if settings.images == "codex" else None)
        self.staff: dict[str, Agent] = {cls.persona.id: cls(self) for cls in STAFF}
        self.busy = threading.Lock()
        self._facts = None

    def _brain_used(self, role: str, key: str, failures: list[str]) -> None:
        """Show on the desk which AI is thinking, and say so when a desk had to fall back to another one."""
        if self._brain_seen.get(role) == key and not failures:
            return
        self._brain_seen[role] = key
        label = brains.LABELS[key]
        message = f"{failures[-1][:40]}，改用 {label}" if failures else f"{brains.ROLES[role]}：{label}"
        self.bus.emit(desk_of(role), "brain", message, brain=key, label=label, role=role, fallback=bool(failures))

    def brain_summary(self) -> dict[str, list[str]]:
        return {role: [brains.LABELS[k] for k in brains.chain(self.settings, role)] for role in brains.ROLES}

    # ---- time ----
    def local_now(self) -> datetime:
        return datetime.now(self.settings.timezone)

    def today(self) -> date:
        return self.local_now().date()

    def at(self, day: date, moment: time) -> datetime:
        return datetime.combine(day, moment, tzinfo=self.settings.timezone)

    # ---- media ----
    def day_media_dir(self, day: date) -> Path:
        path = self.settings.media_dir / day.isoformat()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def media_ref(self, path: Path) -> str:
        return path.resolve().relative_to(self.settings.media_dir.resolve()).as_posix()

    def media_file(self, ref: str) -> Path:
        path = (self.settings.media_dir / ref).resolve()
        if self.settings.media_dir.resolve() not in path.parents:
            raise ValueError(f"媒體路徑不在 media 資料夾內：{ref}")
        return path

    # ---- queue ----
    def queue(
        self,
        run_id: int | None,
        item: PlanItem,
        *,
        channel: str,
        format: str,
        title: str,
        payload: dict,
        review: dict,
        passed: bool,
        slot: datetime,
        sender: Agent,
        media: dict | None = None,
        parent_id: int | None = None,
    ) -> int:
        if not passed:
            status = "needs_changes"
        elif self.settings.approval == "auto":
            status = "approved"
        else:
            status = "pending_approval"
        draft_id = self.store.add_draft(
            run_id=run_id,
            day=slot.astimezone(self.settings.timezone).date().isoformat(),
            channel=channel,
            format=format,
            pillar=item.pillar,
            title=title,
            payload=payload,
            media=media,
            review=review,
            status=status,
            scheduled_at=slot.astimezone(timezone.utc).isoformat(timespec="seconds"),
            parent_id=parent_id,
        )
        sender.handoff("publisher" if status == "approved" else "boss", f"{title[:12]}", draft_id=draft_id)
        self.draft_changed(draft_id)
        return draft_id

    def queue_reply(self, post: dict, comment: dict, text: str, sender: Agent) -> int:
        """Replies to strangers always wait for a human, whatever OFFICE_APPROVAL says."""
        draft_id = self.store.add_draft(
            run_id=post["run_id"],
            day=self.today().isoformat(),
            channel=post["channel"],
            format="reply",
            title=f"回覆 @{comment.get('username', '訪客')}",
            payload={"reply_to_id": comment["id"], "comment_text": comment["text"], "username": comment.get("username", ""), "text": text},
            status="pending_approval",
            scheduled_at=None,
            parent_id=post["id"],
        )
        sender.handoff("boss", "留言回覆", draft_id=draft_id)
        self.draft_changed(draft_id)
        return draft_id

    def chat(self, sender: str, text: str, data: dict | None = None) -> dict:
        """A line in the conversation between you ("boss") and the chief ("chief")."""
        message = self.store.add_chat(sender, text, data)
        self.bus.emit("chief", "chat", text, sender=sender, chat=message)
        return message

    def draft_changed(self, draft_id: int) -> None:
        draft = self.store.draft(draft_id)
        if draft:
            self.bus.emit("boss", "draft", draft["title"], draft=draft)

    # ---- decisions from the boss (the UI and the CLI call these) ----
    def approve(self, draft_id: int, publish_now: bool = False) -> dict:
        draft = self._editable(draft_id)
        fields: dict[str, Any] = {"status": "approved", "error": None}
        review = draft["review"] or {}
        if any(issue.startswith(PREFLIGHT_HOLD) for issue in review.get("issues") or []):
            # The boss has seen why the publisher held it back; approving again means send it.
            fields["review"] = {**review, "preflight_overridden": True}
        if publish_now or not draft["scheduled_at"]:
            fields["scheduled_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.store.update_draft(draft_id, **fields)
        self.bus.emit("boss", "handoff", "核准", to="publisher", draft_id=draft_id)
        self.draft_changed(draft_id)
        return self.store.draft(draft_id)

    def reject(self, draft_id: int, note: str = "") -> dict:
        self._editable(draft_id)
        self.store.update_draft(draft_id, status="rejected", note=note or None)
        self.draft_changed(draft_id)
        return self.store.draft(draft_id)

    def edit(self, draft_id: int, changes: dict) -> dict:
        draft = self._editable(draft_id)
        payload = {**draft["payload"]}
        for key in ("text", "first_reply", "topic_tag", "caption_full", "title", "description"):
            if key in changes and isinstance(changes[key], str):
                payload[key] = changes[key]
        fields: dict[str, Any] = {"payload": payload}
        if draft["status"] == "needs_changes":
            fields["status"] = "pending_approval"
        if isinstance(changes.get("title"), str) and draft["channel"] == "youtube":
            fields["title"] = changes["title"]
        self.store.update_draft(draft_id, **fields)
        self.draft_changed(draft_id)
        return self.store.draft(draft_id)

    def _editable(self, draft_id: int) -> dict:
        draft = self.store.draft(draft_id)
        if not draft:
            raise KeyError(draft_id)
        if draft["status"] in {"published", "publishing"}:
            raise ValueError("已經發佈的內容不能再改")
        return draft

    # ---- shared helpers for agents ----
    def facts(self):
        if self._facts is None:
            self._facts = load_facts(self.settings)
        return self._facts

    def briefing_for_replies(self, with_news: bool = False) -> Briefing:
        """A light briefing (platform numbers, optionally today's verified announcements) for work outside the
        morning run: replies, rewrites, extra posts, pre-publish checks."""
        return Briefing(day=self.today(), facts=self.facts(), news=load_news(self.settings) if with_news else [])

    def snapshot(self) -> dict:
        run = self.store.latest_run()
        return {
            "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "today": self.today().isoformat(),
            "timezone": str(self.settings.timezone),
            "boss": BOSS,
            "agents": [
                {
                    **agent.persona.to_dict(),
                    "brain": self._brain_seen.get(agent.id) or self.writer.primary(agent.id) if agent.id in brains.ROLES else None,
                    **self.bus.agent_states.get(agent.id, {"state": "idle", "message": "待命中"}),
                }
                for agent in self.staff.values()
            ],
            "drafts": self.store.drafts(limit=80),
            "run": run,
            "busy": self.busy.locked(),
            "events": self.store.events(limit=80),
            "chat": self.store.chat(limit=60),
            "settings": {
                "approval": self.settings.approval,
                "dry_run": self.settings.dry_run,
                "brains": self.brain_summary(),
                "images": "Codex" if self.images else None,
                "labels": brains.LABELS,
                "daily_at": self.settings.daily_at.strftime("%H:%M"),
                "site_url": self.settings.site_url,
                "accounts": {
                    channel: not self.staff["publisher"].missing_credentials(channel) if not self.settings.dry_run else None
                    for channel in ("threads", "instagram", "youtube")
                },
            },
        }

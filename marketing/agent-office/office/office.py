"""The office itself: shared storage, the event bus, the writer, the renderer and the staff at their desks."""

from __future__ import annotations

import json
import re
import threading
from secrets import token_hex
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from .agents.analyst import Analyst
from .agents.base import Agent
from .agents.chief import Chief
from .agents.community import Community
from .agents.designer import Designer
from .agents.hire import Hire, look as hire_look
from .agents.publisher import PREFLIGHT_HOLD, Publisher
from .agents.reviewer import Reviewer
from .agents.strategist import Strategist
from .agents.threads_writer import ThreadsWriter
from .agents.video_editor import VideoEditor
from . import accounts, brains
from .brand import Briefing, load_facts, load_news, load_schools
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


# Model names the chief may set: letters, digits and the punctuation real names use ("Gemini 3.7 Flash (Low)").
MODEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._:/()\[\]-]{0,79}")
# Which tools can run which family of models. Antigravity also offers some Claude and open GPT models (`agy models`).
MODEL_TOOLS = {"claude": ("claude-code", "api", "antigravity"), "gpt": ("codex", "antigravity"), "gemini": ("antigravity",)}


def _model_family(model: str) -> str:
    name = model.lower()
    if any(word in name for word in ("claude", "opus", "sonnet", "haiku", "fable")):
        return "claude"
    if name.startswith(("gpt", "o3", "o4", "codex")):
        return "gpt"
    if "gemini" in name:
        return "gemini"
    return ""


MAX_HIRES = 6
NAME = re.compile(r"[\w\u4e00-\u9fff ]{1,12}")


# The human's desk. Drafts land here unless OFFICE_APPROVAL=auto.
BOSS = {"id": "boss", "name": "你", "title": "老闆（審核）", "duty": "看審核匣：核准、退回或直接修改草稿"}


class Office:
    def __init__(self, settings: Settings, *, writer=None, renderer=None, images=None):
        self.settings = settings
        self.store = Store(settings.db_path)
        self.bus = EventBus(self.store)
        self._brain_seen: dict[str, str] = {}
        self.writer = writer or make_writer(settings, on_brain=self._brain_used, tuning=self.tuning)
        self.renderer = renderer or Renderer(settings)
        # Cover illustrations: Codex's image generation when OFFICE_IMAGES=codex.
        self.images = images if images is not None else (brains.CodexBrain(settings) if settings.images == "codex" else None)
        self.staff: dict[str, Agent] = {cls.persona.id: cls(self) for cls in STAFF}
        for record in self.hires():
            self._seat(Hire(self, record))
        self.busy = threading.Lock()
        self._facts = None

    def _brain_used(self, role: str, key: str, failures: list[str]) -> None:
        """Show on the desk which AI is thinking, and say so when a desk had to fall back to another one."""
        if self._brain_seen.get(role) == key and not failures:
            return
        self._brain_seen[role] = key
        label = brains.LABELS[key]
        message = f"{failures[-1][:40]}，改用 {label}" if failures else f"{self.roles().get(role, role)}：{label}"
        self.bus.emit(desk_of(role), "brain", message, brain=key, label=label, role=role, fallback=bool(failures))

    def brain_summary(self) -> dict[str, list[str]]:
        def keys(role: str) -> list[str]:
            if hasattr(self.writer, "chain"):
                return [brain.key if brain else "offline" for brain in self.writer.chain(role)]
            return brains.chain(self.settings, role)

        return {role: [brains.LABELS[k] for k in keys(role)] for role in self.roles()}

    def roles(self) -> dict[str, str]:
        """Every job that thinks with an AI: the fixed ones and each colleague the chief hired."""
        return {**brains.ROLES, **{agent.id: agent.persona.title for agent in self.staff.values() if isinstance(agent, Hire)}}

    # ---- colleagues the chief hires ----
    def hires(self) -> list[dict]:
        try:
            value = json.loads(self.store.get("hires") or "[]")
        except json.JSONDecodeError:
            return []
        return value if isinstance(value, list) else []

    def _seat(self, agent: Agent) -> None:
        # New desks go before the chief, who always sits beside the boss.
        chief = self.staff.pop("chief", None)
        self.staff[agent.id] = agent
        if chief:
            self.staff["chief"] = chief

    def hire(self, name: str, title: str, duty: str, *, brain: str = "", model: str = "", effort: str = "") -> Agent:
        name, title, duty = name.strip(), title.strip(), duty.strip()
        if not name or len(name) > 12 or not NAME.fullmatch(name):
            raise ValueError("新同事的名字要 1～12 個字，只能有中英文、數字和空格")
        if any(agent.persona.name == name for agent in self.staff.values()):
            raise ValueError(f"已經有同事叫 {name} 了")
        records = self.hires()
        if len(records) >= MAX_HIRES:
            raise ValueError(f"辦公室最多再加 {MAX_HIRES} 位同事，請先讓一位離開")
        record = {"id": f"hire-{token_hex(3)}", "name": name, "title": (title or "助理")[:16], "duty": (duty or "協助總管交代的工作")[:160],
                  **hire_look(len(records) + int(self.store.get("hires_ever") or 0))}
        agent = Hire(self, record)
        self._seat(agent)
        try:
            if brain or model or effort:
                self.tune(agent.id, brain=brain, model=model, effort=effort)
        except ValueError:
            self.staff.pop(agent.id)
            raise
        self.store.set("hires", json.dumps(records + [record], ensure_ascii=False))
        self.store.set("hires_ever", str(int(self.store.get("hires_ever") or 0) + 1))
        self.bus.emit(agent.id, "staff", f"{name}（{record['title']}）加入辦公室", change="hire")
        return agent

    def dismiss(self, name_or_id: str) -> str:
        agent = self.colleague(name_or_id)
        self.staff.pop(agent.id)
        self.store.set("hires", json.dumps([r for r in self.hires() if r["id"] != agent.id], ensure_ascii=False))
        self.store.set(f"tuning:{agent.id}", "{}")
        self.bus.emit("chief", "staff", f"{agent.persona.name}離開辦公室", change="dismiss", id=agent.id)
        return agent.persona.name

    def update_hire(self, hire_id: str, **fields) -> None:
        records = self.hires()
        for record in records:
            if record["id"] == hire_id:
                record.update(fields)
                self.staff[hire_id].record = record
        self.store.set("hires", json.dumps(records, ensure_ascii=False))

    def split_schools(self, names: list[str]) -> dict[str, list[str]]:
        """Share the platform's universities among these colleagues, in registry order, for a daily round each."""
        colleagues = [self.colleague(name) for name in names]
        if not colleagues:
            raise ValueError("要分給哪幾位新同事？")
        schools = load_schools(self.settings)
        size = -(-len(schools) // len(colleagues))
        shares = {}
        for i, colleague in enumerate(colleagues):
            share = schools[i * size:(i + 1) * size]
            self.update_hire(colleague.id, schools=[s.id for s in share], daily_kind="schools",
                             daily=f"巡查 {len(share)} 所大學官網：交換公告、規定有沒有變，和平台資料一不一致")
            shares[colleague.persona.name] = [s.name for s in share]
        return shares

    def run_hire_dailies(self) -> list[str]:
        """Each new colleague's standing task, once a day; the chief passes the results to the boss."""
        names = []
        for agent in list(self.staff.values()):
            if not isinstance(agent, Hire) or not agent.record.get("daily_kind"):
                continue
            kind, task = agent.record["daily_kind"], agent.record.get("daily", "")

            def work(agent=agent, kind=kind, task=task) -> str:
                if kind == "schools":
                    return agent.check_schools()
                if kind == "threads":
                    return f"{agent.persona.name}寫好今天的 Threads 了（#{agent.write_threads(task, self.staff['chief']._next_slot('threads'))}），在審核匣等你"
                return agent.report(task)

            self.staff["chief"]._background(f"{agent.persona.name}的每日工作", work)
            names.append(agent.persona.name)
        return names

    def colleague(self, name_or_id: str) -> "Hire":
        key = name_or_id.strip()
        for agent in self.staff.values():
            if isinstance(agent, Hire) and key in {agent.id, agent.persona.name}:
                return agent
        if any(agent.persona.name == key for agent in self.staff.values()):
            raise ValueError(f"{key} 是原本的同事，只有新加入的同事能這樣交代或請離開")
        raise ValueError(f"辦公室裡沒有叫 {key} 的新同事")

    # ---- which AI, model and effort each desk thinks with ----
    def tuning(self, role: str) -> dict:
        try:
            value = json.loads(self.store.get(f"tuning:{role}") or "{}")
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def tune(self, role: str, *, brain: str = "", model: str = "", effort: str = "") -> dict:
        """Change one desk's AI. "default" for a field puts that field back to the .env setting."""
        if role not in self.roles():
            raise ValueError(f"沒有「{role}」這個工作（可用：{'、'.join(self.roles())}）")
        current = self.tuning(role)
        if brain:
            if brain == "default":
                current.pop("brain", None)
            elif brain in brains.LABELS:
                current["brain"] = brain
            else:
                raise ValueError(f"沒有「{brain}」這個工具（可用：{'、'.join(brains.LABELS)}）")
        if model:
            model = model.strip()
            if model == "default":
                current.pop("model", None)
            elif not MODEL_NAME.fullmatch(model):
                raise ValueError(f"模型名稱「{model[:40]}」看起來不對")
            else:
                current["model"] = model
        if effort:
            if effort == "default":
                current.pop("effort", None)
            elif effort in brains.EFFORTS:
                current["effort"] = effort
            else:
                raise ValueError(f"思考強度只能是 {'、'.join(brains.EFFORTS)}")
        tool = current.get("brain") or brains.resolve(self.settings.brains, role)
        family = _model_family(current.get("model", ""))
        if family and tool not in MODEL_TOOLS[family]:
            raise ValueError(f"{current['model']} 不能在 {brains.LABELS[tool]} 上跑，要用 {'或'.join(brains.LABELS[k] for k in MODEL_TOOLS[family])}")
        self.store.set(f"tuning:{role}", json.dumps(current, ensure_ascii=False))
        self._brain_seen.pop(role, None)
        key = self.writer.primary(role) if hasattr(self.writer, "primary") else tool
        self.bus.emit(desk_of(role), "brain", f"{self.roles()[role]}改用 {self.describe_brain(role)}", brain=key,
                      label=brains.LABELS[key], role=role, fallback=False)
        return current

    def describe_brain(self, role: str) -> str:
        tune = self.tuning(role)
        tool = tune.get("brain") or brains.resolve(self.settings.brains, role)
        default_model = {"claude-code": self.settings.claude_code_model, "codex": self.settings.codex_model,
                         "api": self.settings.model}.get(tool, "")
        parts = [brains.LABELS[tool], f"模型 {tune.get('model') or default_model or '預設'}"]
        if tool != "offline":
            parts.append(f"思考強度 {tune.get('effort') or '預設'}")
        return "｜".join(parts)

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
                    "brain": self._brain_seen.get(agent.id) or self.writer.primary(agent.id) if agent.id in self.roles() else None,
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
                "tuning": {role: self.describe_brain(role) for role in self.roles()},
                "images": "Codex" if self.images else None,
                "labels": brains.LABELS,
                "daily_at": self.settings.daily_at.strftime("%H:%M"),
                "site_url": self.settings.site_url,
                "accounts": {
                    channel: {
                        "connected": accounts.connected(self.settings, self.store, channel),
                        "handle": self.store.get(f"handle:{channel}") or "",
                    }
                    for channel in accounts.PLATFORMS
                },
            },
        }

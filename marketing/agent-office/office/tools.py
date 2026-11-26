"""The office's hands, for assistants that live somewhere else (the OpenBot team).

The assistants do the thinking: planning, writing, reviewing, answering. Everything the office did with plain code stays
code, and is exposed here as one command per job, each printing a JSON answer:

    uv run office tool status                      # today, the posting day, drafts, accounts
    uv run office tool begin-day                   # is today a posting day? starts the day and lists the slots
    uv run office tool briefing                    # platform numbers, verified announcements, what worked, notes
    uv run office tool check  draft.json           # the rule checks (length, links, banned phrases, numbers ...)
    uv run office tool queue  draft.json           # draw the pictures / render the video, put it in the approval inbox
    uv run office tool approve 12 --now            # the boss's decision, relayed by the chief
    uv run office tool publish-due                 # send what is approved and due (Pat)
    uv run office tool comments-due                # fresh comments to answer (Momo)
    uv run office tool metrics                     # fetch the numbers and rank the posts (Momo)

The accounts are the ones `office auth` linked: the tokens stay in var/office.sqlite3 and the tools use them, so an
assistant never sees them. Nothing is posted for real until `office tool live on` (and OFFICE_DRY_RUN is not 1): until then
every platform call is only recorded in var/outbox/.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from secrets import token_hex
from typing import Any

from pydantic import ValidationError

from . import accounts, autodm, brand, proposals, rules
from .agents.analyst import audit_lines
from .agents.community import WINDOW
from .agents.publisher import PREFLIGHT_HOLD
from .agents.threads_writer import album_media, card_media
from .agents.video_editor import _youtube_payload
from .config import Settings
from .llm import briefing_text
from .models import (
    CarouselDraft,
    PlanItem,
    SchoolCheck,
    ThreadsAlbumDraft,
    ThreadsDraft,
    Verdict,
    VideoScript,
    VisualPlan,
)
from .office import Office
from .rules import instagram_caption
from .store import Store

LIVE_KEY = "tools_live"
OWNER = {("threads", "text"): "阿脆", ("threads", "carousel"): "阿脆（圖片頁交給 Mori）", ("instagram", "carousel"): "Mori",
         ("instagram", "reel"): "阿剪", ("youtube", "long"): "阿剪", ("youtube", "short"): "阿剪"}


class ToolError(Exception):
    """A problem the caller can fix: said plainly, printed as {"ok": false, "error": ...}."""


class ToolWriter:
    """There is no AI inside the tools: the assistants think. The only thing it carries is Mori's page design, which the
    renderer reads through the same call the office's own designer used to make."""

    mode = "openbot"

    def __init__(self, plan: VisualPlan | None = None):
        self.plan = plan

    def uses_model(self, role: str, need_web: bool = False) -> bool:
        return False

    def primary(self, role: str) -> str:
        return "openbot"

    def chain(self, role: str) -> list:
        return [None]

    def visual_plan(self, request: str, slides: list) -> VisualPlan | None:
        return self.plan


class Who:
    """A colleague who is not one of the office's desks (a patrol assistant, a verifier), just a name for the proposal."""

    def __init__(self, name: str):
        self.id = name
        self.persona = type("Persona", (), {"name": name})()

    def handoff(self, *args: Any, **kwargs: Any) -> None:
        return None


# ---------------------------------------------------------------------------------------------------------------
def open_office(*, plan: VisualPlan | None = None, render: bool = True) -> tuple[Office, bool]:
    """The office as the tools see it, and whether it may really post.

    Posting needs two things: `office tool live on` (kept in the office's own database) and OFFICE_DRY_RUN=0 in .env.
    Without both, every platform call is only recorded in var/outbox/, whatever the old office was doing."""
    base = Settings.from_env()
    live = Store(base.db_path).get(LIVE_KEY) == "1"
    overrides: dict[str, Any] = {} if live else {"dry_run": True, "github_dry_run": True}
    if not render:
        overrides["render_media"] = False
    return Office(Settings.from_env(**overrides), writer=ToolWriter(plan)), live


def read_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise ToolError(f"找不到檔案：{path}") from None
    except (OSError, json.JSONDecodeError) as error:
        raise ToolError(f"讀不了 {path}（要是 UTF-8 的 JSON）：{error}") from None


def when(text: str, office: Office) -> datetime:
    """'2026-11-27 12:30' in the office's time zone, or a full ISO time."""
    try:
        moment = datetime.fromisoformat(str(text).strip().replace("/", "-"))
    except ValueError:
        raise ToolError(f"時間「{text}」看不懂，請寫成 2026-11-27 12:30（台北時間）") from None
    return moment if moment.tzinfo else moment.replace(tzinfo=office.settings.timezone)


def pick(model: type, values: dict) -> dict:
    return {key: value for key, value in values.items() if key in model.model_fields}


def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def brief(draft: dict) -> dict:
    review = draft.get("review") or {}
    return {
        "id": draft["id"], "status": draft["status"], "channel": draft["channel"], "format": draft["format"], "day": draft["day"],
        "scheduled_at": draft["scheduled_at"], "title": draft["title"], "issues": review.get("issues") or [],
        "remote_url": draft.get("remote_url"), "error": draft.get("error"),
    }


# ---------------------------------------------------------------------------------------------------------------
class Tools:
    def __init__(self, *, plan: VisualPlan | None = None, render: bool = True):
        self.office, self.live = open_office(plan=plan, render=render)
        self.store = self.office.store
        self.settings = self.office.settings

    # ---- the day ----
    def status(self) -> dict:
        office, today = self.office, self.office.today()
        run = self.store.run_for_day(today.isoformat())
        drafts = self.store.drafts(limit=300)
        return {
            "now": office.local_now().isoformat(timespec="minutes"), "today": today.isoformat(),
            "posting_day": office.posting_day(today), "next_posting_day": office.next_posting_day(today).isoformat(),
            "post_every_days": self.settings.post_every_days, "already_started_today": bool(run),
            "tools_live": self.live, "simulating": self.settings.dry_run,
            "drafts": dict(Counter(d["status"] for d in drafts)),
            "waiting_for_boss": [brief(d) for d in drafts if d["status"] in {"pending_approval", "needs_changes"}][:30],
            "accounts": {c: accounts.connected(self.settings, self.store, c) for c in accounts.PLATFORMS},
            "times": {
                "start": self.settings.daily_at.strftime("%H:%M"), "threads": [t.strftime("%H:%M") for t in self.settings.threads_slots],
                "instagram": self.settings.instagram_slot.strftime("%H:%M"), "youtube": self.settings.youtube_slot.strftime("%H:%M"),
                "analytics": self.settings.analytics_at.strftime("%H:%M"),
            },
        }

    def set_live(self, mode: str) -> dict:
        if mode in {"on", "off"}:
            self.store.set(LIVE_KEY, "1" if mode == "on" else "0")
            self.live = mode == "on"
        env_dry = Settings.from_env().dry_run
        if not self.live:
            say = "模擬中：所有發文、留言回覆、私訊都只記錄在 var/outbox/，不會真的送出。"
        elif env_dry:
            say = "工具已開放，但 .env 的 OFFICE_DRY_RUN 還是 1，所以仍然是模擬。要真的發文，把它改成 0 再重開。"
        else:
            say = "正式模式：核准且到時間的內容會真的發到 Threads／Instagram／YouTube。"
        return {"tools_live": self.live, "env_dry_run": env_dry, "simulating": self.live is False or env_dry, "message": say}

    def slots(self, day: date) -> list[dict]:
        office, s = self.office, self.settings
        threads_times = iter(s.threads_slots)
        out = []
        for index, item in enumerate(office.staff["strategist"].slots(day), 1):
            if item.channel == "threads":
                moment = office.at(day, next(threads_times, s.threads_slots[-1]))
            elif item.channel == "instagram":
                moment = office.at(day, s.instagram_slot)
            else:
                moment = office.at(day, s.youtube_slot) + timedelta(hours=1)
            row = {"n": index, "channel": item.channel, "format": item.format, "pillar": item.pillar, "angle": item.angle,
                   "publish_at": moment.strftime("%Y-%m-%d %H:%M"), "owner": OWNER.get((item.channel, item.format), "")}
            if item.channel == "instagram":
                row["youtube_short_at"] = office.at(day, s.youtube_slot).strftime("%Y-%m-%d %H:%M")
                row["note"] = ("Reels 做好後同一支也會排成 YouTube Shorts" if item.format == "reel"
                               else "輪播做好後，阿剪要把它改寫成 30～40 秒的 YouTube Shorts")
            out.append(row)
        return out

    def begin_day(self, day: date | None, force: bool) -> dict:
        office = self.office
        day = day or office.today()
        existing = self.store.run_for_day(day.isoformat())
        if existing and not force:
            return {"started": False, "posting_day": True, "day": day.isoformat(), "run_id": existing["id"],
                    "message": "今天已經開過工了（要重來請加 --force）", "slots": self.slots(day)}
        if not office.posting_day(day) and not force:
            nxt = office.next_posting_day(day)
            return {"started": False, "posting_day": False, "day": day.isoformat(), "next_posting_day": nxt.isoformat(),
                    "message": f"今天不是發文日（每 {self.settings.post_every_days} 天一次），下一個發文日是 {nxt.month}/{nxt.day}"}
        run_id = self.store.start_run(day.isoformat(), "openbot")
        return {"started": True, "posting_day": True, "day": day.isoformat(), "run_id": run_id, "slots": self.slots(day),
                "message": "今天開工。先請 Ivy 讀簡報、排內容；每個版位的 publish_at 就是發文時間。"}

    def end_day(self, run_id: int, status: str, error: str) -> dict:
        self.store.finish_run(run_id, status, error=error or None)
        drafts = [d for d in self.store.drafts(limit=200) if d["run_id"] == run_id]
        return {"run_id": run_id, "status": status, "drafts": [brief(d) for d in drafts]}

    def briefing(self, day: date | None) -> dict:
        day = day or self.office.today()
        data = self.office.staff["strategist"].briefing(day)
        return {
            "day": day.isoformat(), "facts": asdict(data.facts), "news": [asdict(n) for n in data.news],
            "recent_titles": data.recent_titles, "winners": data.winners, "insights": data.insights, "dm_hooks": data.dm_hooks,
            "text": briefing_text(data),
        }

    def note(self, text: str) -> dict:
        notes = json.loads(self.store.get("boss_notes") or "[]")
        notes.append(text.strip())
        self.store.set("boss_notes", json.dumps(notes[-10:], ensure_ascii=False))
        return {"saved": text.strip(), "pending_notes": len(notes[-10:])}

    # ---- a draft file: what the assistants write ----
    def parse(self, spec: Any) -> tuple[str, str, Any]:
        """(channel, format, the content as the office's own model). The file's shape is in openbot/skills."""
        if not isinstance(spec, dict) or not isinstance(spec.get("payload"), dict):
            raise ToolError('草稿檔要是 {"channel", "format", "publish_at", "title", "payload": {...}}')
        channel, fmt, payload = spec.get("channel"), spec.get("format"), spec["payload"]
        try:
            if (channel, fmt) == ("threads", "text"):
                return channel, fmt, ThreadsDraft(**pick(ThreadsDraft, payload))
            if (channel, fmt) == ("threads", "carousel"):
                return channel, fmt, ThreadsAlbumDraft(**pick(ThreadsAlbumDraft, payload))
            if (channel, fmt) == ("instagram", "carousel"):
                return channel, fmt, CarouselDraft(**pick(CarouselDraft, payload))
            if (channel, fmt) in {("instagram", "reel"), ("youtube", "short"), ("youtube", "long")}:
                return channel, fmt, VideoScript(**pick(VideoScript, payload))
        except ValidationError as error:
            fields = "；".join(f"{'.'.join(str(p) for p in e['loc'])}：{e['msg']}" for e in error.errors()[:6])
            raise ToolError(f"{channel}/{fmt} 的 payload 欄位不對：{fields}") from None
        raise ToolError(f"不支援的 channel／format：{channel}/{fmt}（可以用 threads/text、threads/carousel、instagram/carousel、instagram/reel、youtube/short、youtube/long）")

    def rule_issues(self, channel: str, fmt: str, content: Any, source_url: str) -> list[str]:
        facts = self.office.facts()
        if (channel, fmt) == ("threads", "text"):
            return rules.check_threads(content, facts, source_url)
        if (channel, fmt) == ("threads", "carousel"):
            return rules.check_threads_album(content, facts, source_url)
        if (channel, fmt) == ("instagram", "carousel"):
            return rules.check_carousel(content, facts, source_url)
        return rules.check_video(content, facts, "long" if fmt == "long" else "short", source_url)

    def check(self, spec: Any) -> dict:
        channel, fmt, content = self.parse(spec)
        issues = self.rule_issues(channel, fmt, content, str(spec.get("source_url") or ""))
        return {"ok": not issues, "channel": channel, "format": fmt, "issues": issues}

    # ---- pictures, video and the approval inbox ----
    def queue(self, spec: Any, review_in: dict | None, art: str | None, no_art: bool, parent_id: int | None, force: bool) -> dict:
        office, store = self.office, self.store
        channel, fmt, content = self.parse(spec)
        if not spec.get("publish_at"):
            raise ToolError("草稿檔缺 publish_at（發文時間，例如 2026-11-27 12:30）")
        slot = when(spec["publish_at"], office)
        day = slot.astimezone(self.settings.timezone).date()
        source_url = str(spec.get("source_url") or "")
        item = PlanItem(channel=channel, format=fmt, pillar=spec.get("pillar") or "value", angle=spec.get("angle") or "pain",
                        topic=str(spec.get("title") or "")[:60], brief="", source_url=source_url)
        title = self.title_of(channel, fmt, content, spec)
        twin = next((d for d in store.drafts(day=day.isoformat(), limit=300)
                     if (d["channel"], d["format"], d["title"]) == (channel, fmt, title) and d["status"] not in {"rejected"}), None)
        if twin and twin["status"] == "needs_changes":
            # The author fixed what the review sent back: this version takes its place (and its story / Shorts siblings).
            for old in [twin, *(d for d in store.drafts(day=day.isoformat(), limit=300) if d["parent_id"] == twin["id"])]:
                if old["status"] == "needs_changes":
                    store.update_draft(old["id"], status="rejected", note="已由修改後的版本取代")
                    office.draft_changed(old["id"])
        elif twin and not force:
            raise ToolError(f"同一則已經在審核匣了：#{twin['id']}（{twin['status']}）。要重新做請先退回它，或加 --force")

        issues = self.rule_issues(channel, fmt, content, source_url)
        notes: list[str] = []
        revisions = 0
        if review_in is not None and not isinstance(review_in, dict):
            raise ToolError('審稿結果檔要是 {"approved", "issues", "notes"}')
        if review_in is None:
            notes.append("沒有 AI 審稿結果，只做了規則檢查")
        else:
            issues += [str(i) for i in review_in.get("issues") or []]
            notes += [str(n) for n in review_in.get("notes") or []]
            revisions = int(review_in.get("revisions") or 0)
            if review_in.get("approved") is False and not review_in.get("issues"):
                issues.append("審稿沒有通過（審稿同事沒有寫原因）")
        issues = dedupe(issues)
        review = {"issues": issues, "notes": notes, "revisions": revisions}
        passed = not issues

        run = store.run_for_day(day.isoformat())
        run_id = run["id"] if run else None
        art_path = Path(art).expanduser().resolve() if art else None
        if art_path is not None and not art_path.is_file():
            raise ToolError(f"找不到封面插圖：{art}")
        new_art = art_path is None and not no_art
        also: list[int] = []

        if (channel, fmt) == ("threads", "text"):
            agent = office.staff["threads"]
            media = card_media(agent, content, day)
            payload = {**content.model_dump(), "source_url": source_url, "angle": item.angle}
            draft_id = office.queue(run_id, item, channel=channel, format=fmt, title=title, payload=payload, media=media,
                                    review=review, passed=passed, slot=slot, sender=agent, parent_id=parent_id)
        elif (channel, fmt) == ("threads", "carousel"):
            agent = office.staff["threads"]
            media, plan, made = album_media(agent, content, title, day, f"Threads 多圖貼文《{title}》，文案和審稿都已經完成。",
                                            art=art_path, new_art=new_art)
            payload = {**content.model_dump(), "source_url": source_url, "angle": item.angle}
            if plan:
                payload["visual_plan"] = plan.model_dump()
            review = {**review, "notes": [*notes, *made]}
            draft_id = office.queue(run_id, item, channel=channel, format=fmt, title=title, payload=payload, media=media,
                                    review=review, passed=passed, slot=slot, sender=agent, parent_id=parent_id)
        elif (channel, fmt) == ("instagram", "carousel"):
            agent = office.staff["designer"]
            media, plan_out, folder, art_out = {}, None, office.day_media_dir(day) / f"carousel-{run_id or 0}-{token_hex(3)}", None
            if self.settings.render_media:
                files, plan_out, art_out, made = agent.render_carousel(agent, content, title, folder,
                                                                       f"IG 輪播《{title}》，文案和審稿都已經完成。", art=art_path, new_art=new_art)
                media["images"] = [office.media_ref(p) for p in files]
                if art_out:
                    media["art"] = office.media_ref(art_out)
                review = {**review, "notes": [*notes, *made]}
            payload = {**content.model_dump(), "caption_full": instagram_caption(content.caption, content.hashtags)}
            if plan_out:
                payload["visual_plan"] = plan_out.model_dump()
            draft_id = office.queue(run_id, item, channel=channel, format=fmt, title=title, payload=payload, media=media,
                                    review=review, passed=passed, slot=slot, sender=agent, parent_id=parent_id)
            if self.settings.render_media and content.slides:
                story = office.renderer.story(content.slides[0], folder / "story.jpg", art=art_out, plan=plan_out)
                also.append(office.queue(run_id, item, channel="instagram", format="story", title=f"限動：{content.slides[0].title}",
                                         payload={"cover": content.slides[0].model_dump()}, media={"image": office.media_ref(story)},
                                         review=review, passed=passed, slot=slot + timedelta(minutes=15), sender=agent, parent_id=draft_id))
        else:  # the three video formats
            agent = office.staff["video"]
            orientation = "landscape" if fmt == "long" else "portrait"
            media = agent.render(content, day, orientation)
            if (channel, fmt) == ("instagram", "reel"):
                payload = {**content.model_dump(), "caption_full": instagram_caption(content.caption, content.hashtags)}
                draft_id = office.queue(run_id, item, channel=channel, format=fmt, title=title, payload=payload, media=media,
                                        review=review, passed=passed, slot=slot, sender=agent, parent_id=parent_id)
                short_at = when(spec["youtube_short_at"], office) if spec.get("youtube_short_at") else office.at(day, self.settings.youtube_slot)
                short_item = item.model_copy(update={"channel": "youtube", "format": "short"})
                also.append(office.queue(run_id, short_item, channel="youtube", format="short", title=content.youtube_title,
                                         payload=_youtube_payload(content), media=media, review=review, passed=passed, slot=short_at,
                                         sender=agent, parent_id=draft_id))
            else:
                draft_id = office.queue(run_id, item, channel=channel, format=fmt, title=title, payload=_youtube_payload(content),
                                        media=media, review=review, passed=passed, slot=slot, sender=agent, parent_id=parent_id)
        draft = store.draft(draft_id)
        return {"ok": True, "draft_id": draft_id, "also_queued": also, "status": draft["status"], "scheduled_at": draft["scheduled_at"],
                "issues": issues, "media": draft["media"] or {}, "simulating": self.settings.dry_run,
                "message": ("審稿有問題，已標成「需要修改」，請作者改完後用同一個指令再 queue 一次（新版會取代這則）" if issues
                            else "排進審核匣了，等老闆核准")}

    @staticmethod
    def title_of(channel: str, fmt: str, content: Any, spec: dict) -> str:
        if (channel, fmt) in {("threads", "text"), ("threads", "carousel")}:
            return (content.text.strip().splitlines() or [""])[0][:40]
        if (channel, fmt) == ("instagram", "carousel"):
            return content.slides[0].title if content.slides else str(spec.get("title") or "")
        if (channel, fmt) == ("instagram", "reel"):
            return content.title
        return content.youtube_title

    # ---- the boss's decisions, relayed by the chief ----
    def drafts(self, status: str | None, day: str | None) -> dict:
        return {"drafts": [brief(d) for d in self.store.drafts(status=status, day=day, limit=100)]}

    def show(self, draft_id: int) -> dict:
        draft = self.store.draft(draft_id)
        if not draft:
            raise ToolError(f"沒有編號 #{draft_id} 的草稿")
        media = draft["media"] or {}
        files = {k: [str(self.office.media_file(r)) for r in (v if isinstance(v, list) else [v])]
                 for k, v in media.items() if k in {"images", "image", "video", "poster", "art"} and v}
        return {**draft, "media_files": files}

    def approve(self, draft_id: int, now: bool) -> dict:
        return brief(self._decide(lambda: self.office.approve(draft_id, publish_now=now)))

    def reject(self, draft_id: int, note: str) -> dict:
        return brief(self._decide(lambda: self.office.reject(draft_id, note)))

    def edit(self, draft_id: int, changes: dict) -> dict:
        return brief(self._decide(lambda: self.office.edit(draft_id, changes)))

    def hold(self, draft_id: int, reason: str) -> dict:
        draft = self.store.draft(draft_id)
        if not draft:
            raise ToolError(f"沒有編號 #{draft_id} 的草稿")
        if draft["status"] in {"published", "publishing"}:
            raise ToolError("已經發佈的內容不能擋")
        review = draft["review"] or {}
        self.store.update_draft(draft_id, status="needs_changes", review={**review, "issues": [*(review.get("issues") or []), f"{PREFLIGHT_HOLD}{reason}"]})
        self.office.draft_changed(draft_id)
        return brief(self.store.draft(draft_id))

    @staticmethod
    def _decide(action) -> dict:
        try:
            return action()
        except KeyError as error:
            raise ToolError(f"沒有編號 #{error.args[0]} 的草稿") from None
        except ValueError as error:
            raise ToolError(str(error)) from None

    # ---- Pat ----
    def publish_due(self) -> dict:
        publisher, results = self.office.staff["publisher"], []
        for draft in self.store.due_drafts(datetime.now(timezone.utc).isoformat(timespec="seconds")):
            done = publisher.publish(draft)
            results.append({**brief(done), "simulated": publisher.simulated(done["channel"]), "note": done.get("note")})
        return {"published": results, "count": len(results), "simulating": self.settings.dry_run}

    def refresh_tokens(self) -> dict:
        if self.settings.dry_run:
            return {"skipped": "模擬模式不會更新權杖", "refreshed": []}
        return {"refreshed": self.office.staff["publisher"].refresh_tokens()}

    def accounts(self, ping: bool) -> dict:
        rows = {c: {"connected": accounts.connected(self.settings, self.store, c), "handle": self.store.get(f"handle:{c}") or ""}
                for c in accounts.PLATFORMS}
        result: dict = {"accounts": rows}
        if ping:
            result["check"] = [asdict(r) for r in accounts.check(self.settings, self.store)]
        return result

    # ---- Momo ----
    def comments_due(self) -> dict:
        if self.settings.dry_run:
            return {"posts": [], "skipped": "模擬模式沒有真的貼文，沒有留言可以看"}
        office, now = self.office, datetime.now(timezone.utc)
        community, clients = office.staff["community"], office.staff["publisher"].clients()
        since, until = (now - WINDOW[1]).isoformat(timespec="seconds"), (now - WINDOW[0]).isoformat(timespec="seconds")
        out, problems = [], []
        for post in self.store.published_since(since):
            if (post["published_at"] > until or post["format"] not in {"text", "carousel", "reel"} or post["channel"] not in {"threads", "instagram"}
                    or not post["remote_id"] or post["remote_id"].startswith("dry-") or self.store.get(f"community:{post['id']}")):
                continue
            try:
                comments = clients["threads"].replies(post["remote_id"]) if post["channel"] == "threads" else clients["instagram"].comments(post["remote_id"])
            except Exception as error:  # noqa: BLE001 - one post's trouble must not hide the others
                problems.append(f"#{post['id']} {post['title'][:16]}：留言抓不到（{str(error)[:80]}）")
                continue
            self.store.set(f"community:{post['id']}", now.isoformat(timespec="seconds"))
            own = community._own_handle(post["channel"], clients[post["channel"]])
            fresh = [{"id": c["id"], "text": c["text"], "username": c.get("username", "")} for c in comments if c.get("username") != own][:10]
            if fresh:
                out.append({"post_id": post["id"], "channel": post["channel"], "title": post["title"], "url": post.get("remote_url"),
                            "post_text": post["payload"].get("text") or post["payload"].get("caption_full") or post["title"], "comments": fresh})
        return {"posts": out, "problems": problems}

    def reply(self, spec: Any) -> dict:
        if not isinstance(spec, dict):
            raise ToolError('回覆檔要是 {"post_id", "comment_id", "comment_text", "username", "text"}')
        post = self.store.draft(int(spec.get("post_id") or 0))
        text, comment_id = str(spec.get("text") or "").strip(), str(spec.get("comment_id") or "")
        if not post or post["status"] != "published" or post["channel"] not in {"threads", "instagram"}:
            raise ToolError(f"#{spec.get('post_id')} 不是已經發出去的 Threads／Instagram 貼文")
        if not comment_id or not text:
            raise ToolError("回覆檔要有 comment_id 和 text")
        if len(text) > 500:
            raise ToolError(f"回覆 {len(text)} 字太長，請控制在 30～80 字")
        if any(d["payload"].get("reply_to_id") == comment_id and d["status"] != "rejected" for d in self.store.drafts(limit=400) if d["format"] == "reply"):
            raise ToolError("這則留言已經有回覆草稿了")
        comment = {"id": comment_id, "text": str(spec.get("comment_text") or ""), "username": str(spec.get("username") or "")}
        draft_id = self.office.queue_reply(post, comment, text, sender=self.office.staff["community"])
        return {"ok": True, "draft_id": draft_id, "message": "回覆擬好了，等老闆核准才會送出"}

    def auto_dm(self) -> dict:
        if self.settings.dry_run:
            return {"sent": 0, "skipped": "模擬模式不會真的私訊"}
        return {"sent": self.office.staff["community"].auto_dm(datetime.now(timezone.utc))}

    def dm_rules(self) -> dict:
        records = autodm.rules(self.store)
        return {"rules": [{**r, "text": autodm.describe(r)} for r in records], "blocked": autodm.blocked(self.store, datetime.now(timezone.utc)) or ""}

    def dm_rule_add(self, keywords: list[str], message: str, public_reply: str, offer: str, draft_id: int) -> dict:
        try:
            record = autodm.add(self.store, keywords=keywords, message=message, public_reply=public_reply, offer=offer, draft_id=draft_id)
        except ValueError as error:
            raise ToolError(str(error)) from None
        return {"ok": True, "rule": record, "text": autodm.describe(record)}

    def dm_rule_remove(self, rule_id: int) -> dict:
        try:
            return {"ok": True, "removed": autodm.remove(self.store, rule_id)}
        except ValueError as error:
            raise ToolError(str(error)) from None

    def metrics(self, days: int) -> dict:
        analyst = self.office.staff["analyst"]
        collected = 0 if self.settings.dry_run else analyst.collect()
        rows = analyst.audit(days)
        return {"collected": collected, "simulating": self.settings.dry_run, "audit": rows, "lines": audit_lines(rows),
                "winners": analyst.winners(), "current_insights": json.loads(self.store.get("insights") or "[]")}

    def insights(self, notes: list[str]) -> dict:
        if notes:
            self.store.set("insights", json.dumps([n.strip() for n in notes if n.strip()][:4], ensure_ascii=False))
        return {"insights": json.loads(self.store.get("insights") or "[]")}

    # ---- school patrol ----
    def schools(self, query: str, part: str) -> dict:
        schools = sorted(brand.load_schools(self.settings), key=lambda s: s.id)
        if part:
            try:
                index, total = (int(x) for x in part.split("/"))
                size = -(-len(schools) // total)
                schools = schools[(index - 1) * size:index * size]
            except (ValueError, ZeroDivisionError):
                raise ToolError("--part 要寫成 2/3（三份裡的第 2 份）") from None
        if query:
            schools = [s for s in schools if query.lower() in (s.id + s.name).lower()]
        return {"count": len(schools), "schools": [asdict(s) for s in schools]}

    def school_record(self, school_id: str) -> dict:
        return {"school_id": school_id, "record": brand.platform_record(self.settings, school_id)}

    def proposal(self, spec: Any) -> dict:
        if not isinstance(spec, dict) or not isinstance(spec.get("checks"), list):
            raise ToolError('提案檔要是 {"author", "verifier", "checks": [...], "verdicts": [...]}')
        try:
            checks = [SchoolCheck(**c) for c in spec["checks"]]
            verdicts = [Verdict(**v) for v in spec.get("verdicts") or []] or None
        except (ValidationError, TypeError) as error:
            raise ToolError(f"提案檔的欄位不對：{str(error)[:300]}") from None
        by_name = {s.name: s for s in brand.load_schools(self.settings)}
        verifier = Who(spec["verifier"]) if spec.get("verifier") else None
        queued, notes = proposals.queue_from_checks(
            self.office, Who(spec.get("author") or "巡查員"), checks, by_name, verifier=verifier, verdicts=verdicts,
        )
        return {"queued": [{"draft_id": i, "school": name} for i, name in queued], "notes": notes,
                "message": "資料更新提案放進審核匣了，老闆核准後才會開成 draft PR（合併永遠是老闆自己按）" if queued else "沒有新的提案"}


# ---------------------------------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="office tool", description="給 OpenBot 助理用的工具：每個指令印一份 JSON")
    sub = parser.add_subparsers(dest="name", required=True)
    sub.add_parser("status", help="今天、發文日、草稿、帳號")
    live = sub.add_parser("live", help="開關真的發文（預設關：只模擬）")
    live.add_argument("mode", choices=["on", "off", "status"])
    begin = sub.add_parser("begin-day", help="今天是發文日嗎？是就開工並列出版位")
    begin.add_argument("--date", type=date.fromisoformat)
    begin.add_argument("--force", action="store_true")
    end = sub.add_parser("end-day", help="收工")
    end.add_argument("run_id", type=int)
    end.add_argument("--status", default="done", choices=["done", "partial", "failed"])
    end.add_argument("--error", default="")
    briefing = sub.add_parser("briefing", help="平台數字、已核實公告、爆文、數據建議、老闆交代")
    briefing.add_argument("--date", type=date.fromisoformat)
    note = sub.add_parser("note", help="留一句話給明天的企劃")
    note.add_argument("text")
    check = sub.add_parser("check", help="規則檢查一份草稿檔")
    check.add_argument("file")
    queue = sub.add_parser("queue", help="出圖／出影片，放進審核匣")
    queue.add_argument("file")
    queue.add_argument("--review", help="審稿結果檔 {approved, issues, notes}")
    queue.add_argument("--plan", help="Mori 的版面規劃檔（VisualPlan JSON）")
    queue.add_argument("--art", help="封面插圖檔（不給就照 OFFICE_IMAGES 的設定畫）")
    queue.add_argument("--no-art", action="store_true", help="不畫封面插圖")
    queue.add_argument("--no-render", action="store_true", help="只寫文案，不出圖和影片")
    queue.add_argument("--parent", type=int, help="母草稿編號（例如輪播改編的 Shorts）")
    queue.add_argument("--force", action="store_true")
    listing = sub.add_parser("list", help="草稿清單")
    listing.add_argument("--status")
    listing.add_argument("--day")
    show = sub.add_parser("show", help="一則草稿的全部內容和圖片檔位置")
    show.add_argument("id", type=int)
    approve = sub.add_parser("approve", help="老闆核准（只有老闆明說要核准時才用）")
    approve.add_argument("id", type=int)
    approve.add_argument("--now", action="store_true")
    reject = sub.add_parser("reject", help="老闆退回")
    reject.add_argument("id", type=int)
    reject.add_argument("--note", default="")
    edit = sub.add_parser("edit", help="改草稿的字")
    edit.add_argument("id", type=int)
    edit.add_argument("--set", action="append", default=[], metavar="欄位=內容", help="欄位：text、first_reply、topic_tag、caption_full、title、description")
    hold = sub.add_parser("hold", help="發文前最後檢查：擋下一則")
    hold.add_argument("id", type=int)
    hold.add_argument("--reason", required=True)
    sub.add_parser("publish-due", help="發出已核准且到時間的內容")
    sub.add_parser("refresh-tokens", help="延長 Threads／Instagram 權杖")
    acc = sub.add_parser("accounts", help="社群帳號連上了沒")
    acc.add_argument("--ping", action="store_true", help="實際問平台權杖還有沒有效")
    sub.add_parser("comments-due", help="發文後 30 分鐘～3 小時內、還沒看過的留言")
    reply = sub.add_parser("reply", help="把擬好的留言回覆放進審核匣")
    reply.add_argument("file")
    sub.add_parser("auto-dm", help="掃一輪「留言關鍵字自動私訊」")
    sub.add_parser("dm-rules", help="自動私訊規則")
    add = sub.add_parser("dm-rule-add", help="新增自動私訊規則")
    add.add_argument("--keywords", required=True, help="用逗號分開，每個至少 2 個字")
    add.add_argument("--message", required=True)
    add.add_argument("--public-reply", default="")
    add.add_argument("--offer", default="")
    add.add_argument("--draft-id", type=int, default=0)
    remove = sub.add_parser("dm-rule-remove", help="刪除自動私訊規則")
    remove.add_argument("id", type=int)
    metrics = sub.add_parser("metrics", help="抓成效並和同類貼文比")
    metrics.add_argument("--days", type=int, default=7)
    insights = sub.add_parser("insights", help="寫給企劃的 2～4 點建議（不給 --note 就是看現在的）")
    insights.add_argument("--note", action="append", default=[])
    schools = sub.add_parser("schools", help="平台支援的大學")
    schools.add_argument("--query", default="")
    schools.add_argument("--part", default="", help="分工：2/3 是三份裡的第 2 份")
    record = sub.add_parser("school-record", help="平台對一所學校的已核實規則")
    record.add_argument("school_id")
    proposal = sub.add_parser("proposal", help="把巡查結果送進審核匣當資料更新提案")
    proposal.add_argument("file")
    return parser


def execute(argv: list[str]) -> dict:
    args = build_parser().parse_args(argv)
    name = args.name
    plan = None
    if name == "queue" and args.plan:
        try:
            plan = VisualPlan(**read_json(args.plan))
        except (ValidationError, TypeError) as error:
            raise ToolError(f"版面規劃檔的欄位不對：{str(error)[:300]}") from None
    tools = Tools(plan=plan, render=not getattr(args, "no_render", False))
    if name == "status":
        return tools.status()
    if name == "live":
        return tools.set_live(args.mode)
    if name == "begin-day":
        return tools.begin_day(args.date, args.force)
    if name == "end-day":
        return tools.end_day(args.run_id, args.status, args.error)
    if name == "briefing":
        return tools.briefing(args.date)
    if name == "note":
        return tools.note(args.text)
    if name == "check":
        return tools.check(read_json(args.file))
    if name == "queue":
        review = read_json(args.review) if args.review else None
        return tools.queue(read_json(args.file), review, args.art, args.no_art, args.parent, args.force)
    if name == "list":
        return tools.drafts(args.status, args.day)
    if name == "show":
        return tools.show(args.id)
    if name == "approve":
        return tools.approve(args.id, args.now)
    if name == "reject":
        return tools.reject(args.id, args.note)
    if name == "edit":
        changes = dict(item.split("=", 1) for item in args.set if "=" in item)
        if not changes:
            raise ToolError("請用 --set 欄位=內容 說明要改什麼")
        return tools.edit(args.id, changes)
    if name == "hold":
        return tools.hold(args.id, args.reason)
    if name == "publish-due":
        return tools.publish_due()
    if name == "refresh-tokens":
        return tools.refresh_tokens()
    if name == "accounts":
        return tools.accounts(args.ping)
    if name == "comments-due":
        return tools.comments_due()
    if name == "reply":
        return tools.reply(read_json(args.file))
    if name == "auto-dm":
        return tools.auto_dm()
    if name == "dm-rules":
        return tools.dm_rules()
    if name == "dm-rule-add":
        return tools.dm_rule_add([k.strip() for k in args.keywords.split(",") if k.strip()], args.message, args.public_reply, args.offer, args.draft_id)
    if name == "dm-rule-remove":
        return tools.dm_rule_remove(args.id)
    if name == "metrics":
        return tools.metrics(args.days)
    if name == "insights":
        return tools.insights(args.note)
    if name == "schools":
        return tools.schools(args.query, args.part)
    if name == "school-record":
        return tools.school_record(args.school_id)
    if name == "proposal":
        return tools.proposal(read_json(args.file))
    raise ToolError(f"沒有這個工具：{name}")


def main(argv: list[str]) -> int:
    try:
        result = execute(argv)
    except ToolError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2))
        return 1
    except ValidationError as error:
        fields = "；".join(f"{'.'.join(str(p) for p in e['loc'])}：{e['msg']}" for e in error.errors()[:6])
        print(json.dumps({"ok": False, "error": f"欄位不對：{fields}"}, ensure_ascii=False, indent=2))
        return 1
    except Exception as error:  # noqa: BLE001 - an assistant reads this: say what failed instead of a traceback
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}：{str(error)[:400]}"}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

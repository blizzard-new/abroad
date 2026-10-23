"""One working day: the strategist plans, the writers and designers produce, the reviewer checks, the boss approves."""

from __future__ import annotations

import traceback
from datetime import date, timedelta

from .llm import WriterError
from .office import Office


def run_day(office: Office, day: date | None = None, *, force: bool = False) -> int | None:
    """Produce today's drafts. Returns the run id, or None when another run is in progress."""
    day = day or office.today()
    if not office.busy.acquire(blocking=False):
        return None
    try:
        existing = office.store.run_for_day(day.isoformat())
        if existing and not force:
            return existing["id"]
        return _run(office, day)
    finally:
        office.busy.release()


def _run(office: Office, day: date) -> int:
    settings, staff, store = office.settings, office.staff, office.store
    run_id = store.start_run(day.isoformat(), office.writer.mode)
    office.bus.emit("boss", "run", f"{day.isoformat()} 開工", run_id=run_id, state="running")
    for agent in staff.values():
        agent.status("idle", "到辦公室了 ☕")
    try:
        briefing = staff["strategist"].briefing(day)
        plan = staff["strategist"].plan(briefing)
        store.save_plan(run_id, plan.model_dump())
    except Exception as error:  # noqa: BLE001 - a failed plan ends the day, and the office shows why
        staff["strategist"].status("error", f"企劃失敗：{error}")
        store.finish_run(run_id, "failed", error=_describe(error))
        office.bus.emit("boss", "run", "企劃失敗", run_id=run_id, state="failed")
        return run_id

    threads_slots = iter(settings.threads_slots)
    problems = []
    for item in plan.items:
        owner = {"threads": "threads", "instagram": "designer" if item.format == "carousel" else "video", "youtube": "video"}[item.channel]
        staff["strategist"].handoff(owner, item.topic[:12])
        try:
            if item.channel == "threads":
                staff["threads"].produce(run_id, item, briefing, office.at(day, next(threads_slots, settings.threads_slots[-1])))
            elif item.channel == "instagram" and item.format == "carousel":
                draft_id, carousel = staff["designer"].produce(run_id, item, briefing, office.at(day, settings.instagram_slot))
                staff["designer"].handoff("video", "改成 Shorts")
                staff["video"].short_from_carousel(run_id, carousel, item, briefing, office.at(day, settings.youtube_slot), draft_id)
            elif item.channel == "instagram" and item.format == "reel":
                staff["video"].reel(run_id, item, briefing, office.at(day, settings.instagram_slot), office.at(day, settings.youtube_slot))
            elif item.channel == "youtube" and item.format == "long":
                staff["video"].long(run_id, item, briefing, office.at(day, settings.youtube_slot) + timedelta(hours=1))
        except WriterError as error:
            staff[owner].status("error", f"卡住了：{error}")
            problems.append(f"{item.topic}：{error}")
        except Exception as error:  # noqa: BLE001 - one broken piece should not stop the rest of the day
            staff[owner].status("error", f"出錯了：{type(error).__name__}")
            problems.append(f"{item.topic}：{_describe(error)}")

    pending = len([d for d in store.drafts(day=day.isoformat()) if d["status"] in {"pending_approval", "needs_changes"}])
    store.finish_run(run_id, "done" if not problems else "partial", error="\n".join(problems) or None)
    office.bus.emit("boss", "run", f"今天的草稿都交出來了，{pending} 則等你審核", run_id=run_id, state="done", pending=pending)
    office.staff["chief"].report_day(run_id)
    for agent in staff.values():
        if agent.id in {"publisher", "analyst", "community"}:
            agent.status("idle", "等排程時間到")
    return run_id


def _describe(error: Exception) -> str:
    return "".join(traceback.format_exception_only(type(error), error)).strip()[:500]

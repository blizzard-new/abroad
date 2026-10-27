"""The office clock. Every half minute it checks whether it is time to start the day, publish, read comments or
collect metrics. It runs inside `office serve`, or once per call with `office tick` from cron."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from .office import Office
from .pipeline import run_day

TOKEN_REFRESH_EVERY = timedelta(days=7)


def tick(office: Office, now: datetime | None = None, *, background: bool = True) -> dict:
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(office.settings.timezone)
    day = local.date()
    done: dict = {}
    if local.time() >= office.settings.daily_at and not office.store.run_for_day(day.isoformat()) and not office.busy.locked():
        done["run"] = day.isoformat()
        if background:
            threading.Thread(target=run_day, args=(office, day), daemon=True, name="office-day").start()
        else:
            run_day(office, day)
    started = office.run_hire_dailies(now)
    if started:
        done["hire_dailies"] = started
    if not office.busy.locked():
        done["published"] = office.staff["publisher"].publish_due(now)
    if not office.settings.dry_run:
        done["replies"] = office.staff["community"].check(now)
        if local.time() >= office.settings.analytics_at and office.store.get("analytics_day") != day.isoformat():
            office.store.set("analytics_day", day.isoformat())
            done["metrics"] = office.staff["analyst"].collect()
        last = office.store.get("tokens_refreshed_at")
        if not last or now - datetime.fromisoformat(last) > TOKEN_REFRESH_EVERY:
            office.store.set("tokens_refreshed_at", now.isoformat(timespec="seconds"))
            done["tokens"] = office.staff["publisher"].refresh_tokens()
    return done


def run_forever(office: Office, stop: threading.Event, interval: float = 30.0) -> None:
    while not stop.is_set():
        try:
            tick(office)
        except Exception as error:  # noqa: BLE001 - the clock must keep ticking
            office.bus.emit("boss", "log", f"排程器錯誤：{error}")
        stop.wait(interval)


def start(office: Office, interval: float = 30.0) -> threading.Event:
    stop = threading.Event()
    threading.Thread(target=run_forever, args=(office, stop, interval), daemon=True, name="office-clock").start()
    return stop

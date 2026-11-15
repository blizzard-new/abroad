"""How often the office makes posts: every day, or every N days (OFFICE_POST_EVERY_DAYS).

The count starts from the last day the office worked, not from a fixed calendar, so a pause (the computer was off, the
window was closed) does not leave it waiting for "its" day: the first day it is open again is a posting day.
"""

from __future__ import annotations

from datetime import date, timedelta

from .store import Store


def posting_day(store: Store, every: int, day: date) -> bool:
    """Whether posts are made on `day`: the office already worked that day, nothing came before it, or `every` days have passed."""
    if every <= 1 or store.run_for_day(day.isoformat()):
        return True
    last = store.last_run_day(day.isoformat())
    return last is None or (day - date.fromisoformat(last)).days >= every


def next_posting_day(store: Store, every: int, day: date) -> date:
    """`day` itself when it is a posting day, otherwise the next one."""
    if posting_day(store, every, day):
        return day
    return date.fromisoformat(store.last_run_day(day.isoformat())) + timedelta(days=every)


def last_posting_day(store: Store, day: date) -> date | None:
    """The day the office last made posts on or before `day`."""
    if store.run_for_day(day.isoformat()):
        return day
    last = store.last_run_day(day.isoformat())
    return date.fromisoformat(last) if last else None


def _md(day: date) -> str:
    return f"{day.month}/{day.day}"


def describe(store: Store, every: int, today: date, start_at: str) -> str:
    """One sentence for the boss: is today a posting day, and when is the next one."""
    if last_posting_day(store, today) == today:
        return f"今天已經開工，下一個發文日是 {_md(today + timedelta(days=every))}"
    upcoming = next_posting_day(store, every, today)
    if upcoming == today:
        return f"今天是發文日（{start_at} 開工）"
    return f"今天不發文，下一個發文日是 {_md(upcoming)}"

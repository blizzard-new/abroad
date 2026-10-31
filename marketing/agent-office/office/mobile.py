"""What the phone app asks the office every half minute: what waits for the boss, what just happened, what Leo said.

The app turns each item into a notification and remembers which ones it already showed (draft id and status), so
the office keeps no per-phone state. A draft that stops waiting (approved on the web, say) disappears from the list,
and the app takes its notification down.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from .notices import cut, notification

WAITING = ("pending_approval", "needs_changes")
DONE = ("published", "failed")
RECENT = timedelta(hours=24)
BODY_LIMIT, CHAT_LIMIT, DRAFT_LIMIT = 400, 10, 40


def feed(office, chat_after: int | None = None) -> dict:
    """`chat_after` is the newest chat id the phone has seen; without it only the current newest id comes back, so a
    freshly installed app does not replay old conversations."""
    store = office.store
    latest = store.chat(limit=1)
    chat_last = latest[-1]["id"] if latest else 0
    chat = []
    if chat_after is not None:
        chat = [
            {"id": m["id"], "text": cut(m["text"], BODY_LIMIT), "ts": m["ts"]}
            for m in store.chat(limit=60)
            if m["id"] > chat_after and m["sender"] == "chief"
        ][-CHAT_LIMIT:]
    since = (datetime.now(timezone.utc) - RECENT).isoformat(timespec="seconds")
    drafts = []
    for draft in store.drafts(limit=200):
        waiting = draft["status"] in WAITING
        if not (waiting or (draft["status"] in DONE and draft["updated_at"] >= since)):
            continue
        notice = notification(draft)
        if notice:
            drafts.append({
                "id": draft["id"], "status": draft["status"], "title": notice["title"], "text": cut(notice["text"], BODY_LIMIT),
                "scheduled_at": draft["scheduled_at"], "updated_at": draft["updated_at"],
            })
    drafts = drafts[:DRAFT_LIMIT]
    return {
        "now": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "waiting": sum(d["status"] in WAITING for d in drafts),
        "chat_last": chat_last,
        "chat": chat,
        "drafts": drafts,
    }


class FailureLimit:
    """Locks an address out after too many wrong access tokens, so a token cannot be guessed over the network.

    Only a wrong token counts (a first visit with no token is not an attempt). While locked, even the right token is
    refused: otherwise the guessing could simply carry on during the lock.
    """

    def __init__(self, limit: int = 8, window: float = 600, lock: float = 900, clock=time.monotonic):
        self.limit, self.window, self.lock, self.clock = limit, window, lock, clock
        self.failures: dict[str, list[float]] = {}
        self.locked: dict[str, float] = {}

    def wait(self, key: str) -> int:
        """Seconds left on the lock for this address (0 when it may try)."""
        until = self.locked.get(key, 0)
        left = until - self.clock()
        if left <= 0:
            self.locked.pop(key, None)
            return 0
        return int(left) + 1

    def failed(self, key: str) -> None:
        now = self.clock()
        recent = [t for t in self.failures.get(key, []) if now - t < self.window] + [now]
        self.failures[key] = recent
        if len(recent) >= self.limit:
            self.locked[key] = now + self.lock
            self.failures.pop(key, None)
        if len(self.failures) > 1000:  # a flood of addresses must not grow this without end
            self.failures = {k: v for k, v in self.failures.items() if now - v[-1] < self.window}

    def succeeded(self, key: str) -> None:
        self.failures.pop(key, None)

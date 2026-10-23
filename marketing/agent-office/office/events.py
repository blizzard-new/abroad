"""The office's event bus: every step an agent takes becomes an event the office UI animates.

Agents run in worker threads; the web server reads events on its asyncio loop. Each subscriber registers its own
loop and queue, and events are handed over with call_soon_threadsafe.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone
from typing import Any

from .store import Store

# What an agent can be doing. The UI maps each one to a pose and a bubble style.
STATES = ("idle", "thinking", "working", "rendering", "reviewing", "waiting", "done", "error")


class EventBus:
    def __init__(self, store: Store):
        self.store = store
        self._lock = threading.Lock()
        self._subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue]] = []
        self.agent_states: dict[str, dict[str, Any]] = {}

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        with self._lock:
            self._subscribers.append((asyncio.get_running_loop(), queue))
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers = [(loop, q) for loop, q in self._subscribers if q is not queue]

    def emit(self, agent: str, kind: str, message: str, **data: Any) -> dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        # Screens can carry large previews; the log keeps only what the timeline needs.
        logged = {k: v for k, v in data.items() if k != "screen"}
        event_id = self.store.add_event(ts, agent, kind, message, logged)
        event = {"id": event_id, "ts": ts, "agent": agent, "kind": kind, "message": message, **data}
        if kind == "status":
            with self._lock:
                previous = self.agent_states.get(agent, {})
                state = {**previous, "state": data.get("state", "idle"), "message": message, "ts": ts}
                if "screen" in data:
                    state["screen"] = data["screen"]
                self.agent_states[agent] = state
        with self._lock:
            subscribers = list(self._subscribers)
        for loop, queue in subscribers:
            try:
                loop.call_soon_threadsafe(_offer, queue, event)
            except RuntimeError:  # the subscriber's loop has closed
                self.unsubscribe(queue)
        return event


def _offer(queue: asyncio.Queue, event: dict) -> None:
    if queue.full():
        queue.get_nowait()
    queue.put_nowait(event)

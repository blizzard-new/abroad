"""SQLite storage for runs, drafts (the publishing queue), events, metrics and refreshed tokens."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    status TEXT NOT NULL,
    writer TEXT NOT NULL,
    plan_json TEXT,
    error TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    day TEXT NOT NULL,
    channel TEXT NOT NULL,
    format TEXT NOT NULL,
    pillar TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    media_json TEXT NOT NULL DEFAULT '{}',
    review_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL,
    scheduled_at TEXT,
    published_at TEXT,
    remote_id TEXT,
    remote_url TEXT,
    parent_id INTEGER,
    note TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS drafts_status ON drafts(status, scheduled_at);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    agent TEXT NOT NULL,
    kind TEXT NOT NULL,
    message TEXT NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    data_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    data_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# Draft lifecycle. "needs_changes" drafts failed review twice and wait for a human edit.
DRAFT_STATUSES = (
    "needs_changes",
    "pending_approval",
    "approved",
    "publishing",
    "published",
    "failed",
    "rejected",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for key in list(data):
        if key.endswith("_json"):
            raw = data.pop(key)
            data[key[: -len("_json")]] = json.loads(raw) if raw else None
    return data


class Store:
    def __init__(self, path: Path | str):
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(SCHEMA)
            self._db.commit()

    def _exec(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self._db.execute(sql, params)
            self._db.commit()
            return cursor

    def _all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._lock:
            return [_row(r) for r in self._db.execute(sql, params).fetchall()]

    # ---- runs ----
    def start_run(self, day: str, writer: str) -> int:
        return self._exec(
            "INSERT INTO runs (day, status, writer, started_at) VALUES (?, 'running', ?, ?)", (day, writer, now_utc())
        ).lastrowid

    def finish_run(self, run_id: int, status: str, plan: dict | None = None, error: str | None = None) -> None:
        self._exec(
            "UPDATE runs SET status = ?, plan_json = COALESCE(?, plan_json), error = ?, finished_at = ? WHERE id = ?",
            (status, json.dumps(plan, ensure_ascii=False) if plan is not None else None, error, now_utc(), run_id),
        )

    def save_plan(self, run_id: int, plan: dict) -> None:
        self._exec("UPDATE runs SET plan_json = ? WHERE id = ?", (json.dumps(plan, ensure_ascii=False), run_id))

    def run_for_day(self, day: str) -> dict | None:
        rows = self._all("SELECT * FROM runs WHERE day = ? AND status != 'failed' ORDER BY id DESC LIMIT 1", (day,))
        return rows[0] if rows else None

    def latest_run(self) -> dict | None:
        rows = self._all("SELECT * FROM runs ORDER BY id DESC LIMIT 1")
        return rows[0] if rows else None

    # ---- drafts ----
    def add_draft(
        self,
        *,
        run_id: int | None,
        day: str,
        channel: str,
        format: str,
        title: str,
        payload: dict,
        status: str,
        pillar: str = "",
        media: dict | None = None,
        review: dict | None = None,
        scheduled_at: str | None = None,
        parent_id: int | None = None,
    ) -> int:
        stamp = now_utc()
        return self._exec(
            """INSERT INTO drafts (run_id, day, channel, format, pillar, title, payload_json, media_json, review_json,
                   status, scheduled_at, parent_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                day,
                channel,
                format,
                pillar,
                title,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(media or {}, ensure_ascii=False),
                json.dumps(review or {}, ensure_ascii=False),
                status,
                scheduled_at,
                parent_id,
                stamp,
                stamp,
            ),
        ).lastrowid

    def update_draft(self, draft_id: int, **fields: Any) -> None:
        if not fields:
            return
        columns, params = [], []
        for key, value in fields.items():
            if key in {"payload", "media", "review"}:
                key, value = f"{key}_json", json.dumps(value, ensure_ascii=False)
            columns.append(f"{key} = ?")
            params.append(value)
        columns.append("updated_at = ?")
        params.extend([now_utc(), draft_id])
        self._exec(f"UPDATE drafts SET {', '.join(columns)} WHERE id = ?", tuple(params))

    def draft(self, draft_id: int) -> dict | None:
        rows = self._all("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        return rows[0] if rows else None

    def drafts(self, *, day: str | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
        where, params = [], []
        if day:
            where.append("day = ?")
            params.append(day)
        if status:
            where.append("status = ?")
            params.append(status)
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        return self._all(f"SELECT * FROM drafts {clause} ORDER BY id DESC LIMIT ?", (*params, limit))

    def due_drafts(self, now_iso: str) -> list[dict]:
        return self._all(
            "SELECT * FROM drafts WHERE status = 'approved' AND (scheduled_at IS NULL OR scheduled_at <= ?) ORDER BY scheduled_at, id",
            (now_iso,),
        )

    def published_since(self, since_iso: str) -> list[dict]:
        return self._all(
            "SELECT * FROM drafts WHERE status = 'published' AND published_at >= ? ORDER BY published_at", (since_iso,)
        )

    # ---- events ----
    def add_event(self, ts: str, agent: str, kind: str, message: str, data: dict | None = None) -> int:
        return self._exec(
            "INSERT INTO events (ts, agent, kind, message, data_json) VALUES (?, ?, ?, ?, ?)",
            (ts, agent, kind, message, json.dumps(data or {}, ensure_ascii=False)),
        ).lastrowid

    def events(self, limit: int = 200) -> list[dict]:
        return list(reversed(self._all("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))))

    # ---- chat with the chief ----
    def add_chat(self, sender: str, text: str, data: dict | None = None) -> dict:
        ts = now_utc()
        message_id = self._exec(
            "INSERT INTO chat (ts, sender, text, data_json) VALUES (?, ?, ?, ?)",
            (ts, sender, text, json.dumps(data or {}, ensure_ascii=False)),
        ).lastrowid
        return {"id": message_id, "ts": ts, "sender": sender, "text": text, "data": data or {}}

    def chat(self, limit: int = 50) -> list[dict]:
        return list(reversed(self._all("SELECT * FROM chat ORDER BY id DESC LIMIT ?", (limit,))))

    # ---- metrics ----
    def add_metrics(self, draft_id: int, data: dict) -> None:
        self._exec(
            "INSERT INTO metrics (draft_id, ts, data_json) VALUES (?, ?, ?)",
            (draft_id, now_utc(), json.dumps(data, ensure_ascii=False)),
        )

    def latest_metrics(self) -> dict[int, dict]:
        rows = self._all(
            "SELECT m.* FROM metrics m JOIN (SELECT draft_id, MAX(id) AS id FROM metrics GROUP BY draft_id) last ON m.id = last.id"
        )
        return {row["draft_id"]: row["data"] for row in rows}

    # ---- key/value (refreshed tokens, scheduler bookkeeping) ----
    def get(self, key: str, default: str | None = None) -> str | None:
        with self._lock:
            row = self._db.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        self._exec(
            "INSERT INTO kv (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value, now_utc()),
        )

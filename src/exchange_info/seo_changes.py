"""Durable observations of material page changes, independent of refresh timestamps."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class ContentChanges:
    def __init__(self, directory: Path):
        self.path = directory / "content.sqlite3"

    def observe(self, hashes: dict[str, str], *, now: datetime | None = None) -> dict[str, str]:
        stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path, timeout=5) as db:
            db.execute("CREATE TABLE IF NOT EXISTS pages (path TEXT PRIMARY KEY, hash TEXT NOT NULL, lastmod TEXT)")
            db.execute("BEGIN IMMEDIATE")
            known = {p: (h, m) for p, h, m in db.execute("SELECT path, hash, lastmod FROM pages")}
            result = {}
            for path, content_hash in hashes.items():
                prior = known.get(path)
                # First observation establishes a baseline, never an invented publication date.
                changed = prior is not None and prior[0] != content_hash
                lastmod = max(stamp, prior[1] or stamp) if changed else prior[1] if prior else None
                db.execute("INSERT INTO pages VALUES (?, ?, ?) ON CONFLICT(path) DO UPDATE SET hash=excluded.hash, lastmod=excluded.lastmod",
                           (path, content_hash, lastmod))
                if lastmod:
                    result[path] = lastmod
            return result

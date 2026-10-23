"""Shared plumbing for the platform clients: HTTP with dry-run recording and a log line per call."""

from __future__ import annotations

import time
from typing import Any, Callable

import httpx

Log = Callable[[str], None]
SECRET_KEYS = {"access_token", "client_secret", "refresh_token", "Authorization", "apikey"}


class PlatformError(RuntimeError):
    pass


def redact(params: dict[str, Any] | None) -> dict[str, Any]:
    return {k: ("***" if k in SECRET_KEYS else v) for k, v in (params or {}).items()}


class Client:
    """Base for API clients. In dry-run mode no request leaves the machine: calls are recorded and fake IDs returned."""

    name = "platform"

    def __init__(self, *, dry_run: bool, log: Log | None = None, http: httpx.Client | None = None):
        self.dry_run = dry_run
        self.log = log or (lambda line: None)
        self.http = http or httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0))
        self.calls: list[dict[str, Any]] = []
        self._fake = 0

    def fake_id(self, prefix: str) -> str:
        self._fake += 1
        return f"dry-{prefix}-{int(time.time())}-{self._fake}"

    def request(self, method: str, url: str, *, params: dict | None = None, data: dict | None = None,
                json: Any = None, headers: dict | None = None, content: bytes | None = None, fake: Any = None) -> Any:
        shown = url.split("?")[0]
        self.calls.append({"method": method, "url": shown, "params": redact(params), "data": redact(data), "json": json})
        if self.dry_run:
            self.log(f"[模擬] {method} {shown}")
            return fake
        response = self.http.request(method, url, params=params, data=data, json=json, headers=headers, content=content)
        self.log(f"{method} {shown} → {response.status_code}")
        if response.status_code >= 400:
            raise PlatformError(f"{self.name} {method} {shown} 失敗 {response.status_code}：{response.text[:300]}")
        return response

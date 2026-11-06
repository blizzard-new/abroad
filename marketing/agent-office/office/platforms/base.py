"""Shared plumbing for the platform clients: HTTP with dry-run recording and a log line per call."""

from __future__ import annotations

import time
from typing import Any, Callable

import httpx

Log = Callable[[str], None]
SECRET_KEYS = {"access_token", "client_secret", "refresh_token", "Authorization", "apikey"}


class PlatformError(RuntimeError):
    def __init__(self, message: str = "", status: int = 0, transient: bool = False):
        super().__init__(message)
        self.status = status  # the HTTP status when a platform answered with an error, otherwise 0
        # The platform (a 5xx, or Meta's "is_transient") or the network (no answer, timeout) said the failure is temporary.
        # Trying again may work, but a lost answer does not prove the request failed: check before repeating a publish.
        self.transient = transient


def says_transient(response: httpx.Response) -> bool:
    """A server error, or Meta's own "is_transient": true in its error body."""
    if response.status_code >= 500:
        return True
    try:
        body = response.json()
    except ValueError:
        return False
    error = body.get("error") if isinstance(body, dict) else None
    return isinstance(error, dict) and bool(error.get("is_transient"))


def redact(params: dict[str, Any] | None) -> dict[str, Any]:
    return {k: ("***" if k in SECRET_KEYS else v) for k, v in (params or {}).items()}


class Client:
    """Base for API clients. In dry-run mode no request leaves the machine: calls are recorded and fake IDs returned."""

    name = "platform"
    # How long to wait before each repeat of a call that is safe to repeat (three tries in all). A publish is never
    # repeated blindly: see ThreadsClient._publish.
    retry_waits: tuple[float, ...] = (2.0, 6.0)

    def __init__(self, *, dry_run: bool, log: Log | None = None, http: httpx.Client | None = None):
        self.dry_run = dry_run
        self.log = log or (lambda line: None)
        self.http = http or httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0))
        self.calls: list[dict[str, Any]] = []
        self._fake = 0

    def fake_id(self, prefix: str) -> str:
        self._fake += 1
        return f"dry-{prefix}-{int(time.time())}-{self._fake}"

    def _pause(self, seconds: float) -> None:
        time.sleep(seconds)

    def request(self, method: str, url: str, *, params: dict | None = None, data: dict | None = None,
                json: Any = None, headers: dict | None = None, content: bytes | None = None, fake: Any = None,
                retry: bool = False) -> Any:
        """One HTTP call. With retry=True a temporary failure (a 5xx, Meta's is_transient, no answer) is tried again after a
        short wait; only pass it for a call that cannot do harm twice (a read, or making an unpublished container)."""
        waits = self.retry_waits if retry else ()
        shown = url.split("?")[0]
        for attempt in range(len(waits) + 1):
            try:
                return self._once(method, url, shown, params, data, json, headers, content, fake)
            except PlatformError as error:
                if attempt == len(waits) or not error.transient:
                    raise
                self.log(f"{method} {shown} 暫時失敗（{error.status or '沒有回應'}），{waits[attempt]:.0f} 秒後再試")
                self._pause(waits[attempt])
        raise AssertionError("unreachable")  # the loop always returns or raises

    def _once(self, method, url, shown, params, data, json, headers, content, fake):
        self.calls.append({"method": method, "url": shown, "params": redact(params), "data": redact(data), "json": json})
        if self.dry_run:
            self.log(f"[模擬] {method} {shown}")
            return fake
        try:
            response = self.http.request(method, url, params=params, data=data, json=json, headers=headers, content=content)
        except httpx.TransportError as error:  # no answer at all: a timeout, a dropped connection
            self.log(f"{method} {shown} → 沒有回應（{type(error).__name__}）")
            raise PlatformError(f"{self.name} {method} {shown} 沒有回應（{type(error).__name__}）", 0, transient=True) from error
        self.log(f"{method} {shown} → {response.status_code}")
        if response.status_code >= 400:
            raise PlatformError(
                f"{self.name} {method} {shown} 失敗 {response.status_code}：{response.text[:300]}", response.status_code, transient=says_transient(response),
            )
        return response

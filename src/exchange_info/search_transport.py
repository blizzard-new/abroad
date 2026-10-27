"""DDGS parsers with Requests transport, until primp ships a verified TLS fix.

DDGS is pinned because this deliberately replaces its private engine factory.
No global monkey-patching and no primp Client construction or network calls.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from ddgs.ddgs import DDGS
from ddgs.engines.brave import Brave
from ddgs.engines.yahoo import Yahoo
from ddgs.engines.duckduckgo_videos import DuckduckgoVideos

from .http_client import get_safe_session
from .tls_trust import ca_bundle


class RequestsTransport:
    def __init__(self, timeout: int, headers: dict) -> None:
        self.session = get_safe_session()
        # Our explicit validated bundle remains effective even with trust_env=False.
        # Search does not inherit proxy credentials from the host.
        self.session.trust_env = False
        self.session.verify = ca_bundle()
        self.session.headers.update(headers)
        self.timeout = timeout
        self.client = self  # DDGS Brave's cookie API

    def set_cookies(self, url: str, cookies: dict) -> None:
        for key, value in cookies.items():
            self.session.cookies.set(key, value, domain=urlsplit(url).hostname, path="/")

    def request(self, method: str, url: str, **kwargs):
        return self.session.request(method, url, timeout=self.timeout, **kwargs)


class _RequestsEngine:
    def __init__(self, *, timeout: int) -> None:
        self.http_client = RequestsTransport(timeout, dict(self.headers_update))
        self.results = []


class RequestsDDGS(DDGS):
    _supported = {("text", "brave"): Brave, ("text", "yahoo"): Yahoo,
                  ("videos", "duckduckgo"): DuckduckgoVideos}

    def _get_engines(self, category: str, backend: str):
        # Fail closed for unknown/auto backends: never invoke DDGS's primp factory.
        engine_class = self._supported[(category, backend)]
        if engine_class not in self._engines_cache:
            safe_class = type("Requests" + engine_class.__name__, (_RequestsEngine, engine_class), {})
            self._engines_cache[engine_class] = safe_class(timeout=self._timeout)
        return [self._engines_cache[engine_class]]

    def extract(self, *args, **kwargs):
        raise ValueError("DDGS extraction is disabled; use the verified HTTP client")

    def close(self) -> None:
        for engine in self._engines_cache.values():
            engine.http_client.session.close()

    def __exit__(self, *args) -> None:
        self.close()

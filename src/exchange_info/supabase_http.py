"""One connection pool for the calls to Supabase that did not have one.

``requests.request`` opens a new connection (TCP and TLS) for every call. With the site in Singapore and the database in
Sydney that costs several round trips each time, on top of the call itself, and a signed-in page makes many calls. A shared
session keeps connections open between calls.
"""
from __future__ import annotations

import threading

import requests
from requests.adapters import HTTPAdapter

_lock = threading.Lock()
_session: requests.Session | None = None


def _shared_session() -> requests.Session:
    global _session
    if _session is None:
        with _lock:
            if _session is None:
                session = requests.Session()
                session.mount("https://", HTTPAdapter(pool_connections=4, pool_maxsize=32))
                _session = session
    return _session


def request(method: str, url: str, **kwargs) -> requests.Response:
    """Drop-in for ``requests.request`` that reuses connections."""
    return _shared_session().request(method, url, **kwargs)

"""Where a request really came from, and which public address the site answers on.

Behind a hosting proxy (Render, Cloudflare) the app only ever talks to the proxy: every visitor looks like one address, and
the request arrives over plain http even though the browser used https. Two settings put that right without trusting a header
a visitor could forge:

- ``EXCHANGE_PUBLIC_BASE_URL`` is the site's own https address; absolute links (school photos, calendar feeds, sign-in return
  address) are built from it instead of from the incoming request. Set it when the site has its own domain. On Render, until
  then, ``RENDER_EXTERNAL_URL`` (the service's ``https://….onrender.com`` address, set by Render itself) is used.
- ``EXCHANGE_CLIENT_IP_HEADER`` names the single header the proxy writes itself, replacing whatever the caller sent
  (``CF-Connecting-IP`` on Render, because Cloudflare sits in front). ``X-Forwarded-For`` is deliberately not the default: the
  proxy appends to it, so a visitor who sends their own copy controls its first entry. Unset, the header is ignored, so a
  local run or a deployment without that proxy can not be fooled by a made-up header.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
from collections.abc import Mapping
from typing import Any

PUBLIC_BASE_URL_ENV = "EXCHANGE_PUBLIC_BASE_URL"
HOST_PROVIDED_URL_ENV = "RENDER_EXTERNAL_URL"
CLIENT_IP_HEADER_ENV = "EXCHANGE_CLIENT_IP_HEADER"


def public_base_url(request: Any, environment: Mapping[str, str] | None = None) -> str:
    """The site's public address without a trailing slash: the configured one, else the host's own, else the request's."""
    env = os.environ if environment is None else environment
    configured = env.get(PUBLIC_BASE_URL_ENV, "").strip().rstrip("/")
    if configured:
        return configured
    hosted = env.get(HOST_PROVIDED_URL_ENV, "").strip().rstrip("/")
    if hosted.startswith("https://"):
        return hosted
    return str(request.base_url).rstrip("/")


def client_address(request: Any, environment: Mapping[str, str] | None = None, default: str = "unknown") -> str:
    """The visitor's IP address. Only the configured proxy header is believed, and only when it holds exactly one valid address."""
    env = os.environ if environment is None else environment
    header = env.get(CLIENT_IP_HEADER_ENV, "").strip()
    if header:
        raw = (request.headers.get(header) or "").strip()
        try:
            return str(ipaddress.ip_address(raw))
        except ValueError:
            pass  # missing, a chain of addresses or garbage: fall back to who actually connected
    client = getattr(request, "client", None)
    return client.host if client and client.host else default


def client_fingerprint(request: Any, secret: bytes, environment: Mapping[str, str] | None = None) -> str:
    """A keyed hash of the visitor's address, 64 lowercase hex characters, for rate limits kept in the database.

    The sign-in limiter writes this value to a table whose column only accepts 64 hex characters, and the raw address
    should not sit in the database anyway. HMAC with a server-side secret (not a bare hash) so the small IPv4 space can not
    be enumerated back to addresses from a leaked table. The key is derived per purpose from ``secret``.
    """
    key = hashlib.sha256(b"uniway-client-fingerprint-v1|" + bytes(secret)).digest()
    address = client_address(request, environment)
    return hmac.new(key, address.encode("utf-8"), hashlib.sha256).hexdigest()

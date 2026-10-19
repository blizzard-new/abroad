"""Explicit, disabled-by-default GA4 configuration; never embeds credentials."""
from __future__ import annotations

import os
import re
from collections.abc import Mapping


def measurement_id(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    enabled = env.get("EXCHANGE_GA4_ENABLED", "false").lower() in {"true", "1", "yes", "on"}
    value = env.get("EXCHANGE_GA4_MEASUREMENT_ID", "").strip()
    return value if enabled and re.fullmatch(r"G-[A-Z0-9]{6,20}", value) else ""


def analytics_markup() -> str:
    value = measurement_id()
    if not value:
        return ""
    return (f'<meta name="uniway-ga4-id" content="{value}">'
            '<link rel="stylesheet" href="/static/seo-analytics.css?v=20261019-1">'
            '<script src="/static/seo-analytics.js?v=20261019-1" defer></script>')

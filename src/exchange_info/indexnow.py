"""Validation shared by the public verification file and the manual IndexNow tool."""

import re


def valid_indexnow_key(key: str) -> str | None:
    return key if re.fullmatch(r"[A-Za-z0-9-]{8,128}", key) else None

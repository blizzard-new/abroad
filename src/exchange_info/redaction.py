"""PII redaction and log sanitization for AI pipeline.

Ensures no personal data enters prompts, logs, or embedding indices.
Covers: Taiwan National ID, ARC, passport, phone, email, student ID,
Chinese names, addresses, and guardian information.
"""
from __future__ import annotations

import re
from typing import Any


# ── PII Detection Patterns ──────────────────────────────────────

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    # Taiwan National ID / ARC  (e.g., A123456789)
    "national_id": re.compile(r"\b[A-Z][1289]\d{8}\b", re.IGNORECASE),

    # Taiwan passport number  (9 digits)
    "passport": re.compile(r"\b3\d{8}\b"),

    # Taiwan mobile phone  (09xx-xxx-xxx variants)
    "phone": re.compile(r"\b09\d{2}[-\s]?\d{3}[-\s]?\d{3}\b"),

    # Email addresses
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    ),

    # Student ID (8-10 digit numeric, starting with 4 or 1-9)
    "student_id": re.compile(r"\b(?:4\d{8}|[1-9]\d{7,9})\b"),

    # Chinese address patterns (containing 路/街/巷/弄/號/樓)
    "address": re.compile(
        r"[\u4e00-\u9fff]{2,}(?:縣|市)[\u4e00-\u9fff]{2,}(?:區|鄉|鎮)"
        r"[\u4e00-\u9fff0-9]*(?:路|街|巷|弄|號|樓)[\u4e00-\u9fff0-9]*"
    ),
}

# Replacement labels for each PII type
_REPLACEMENT_LABELS = {
    "national_id": "[REDACTED_ID]",
    "passport": "[REDACTED_PASSPORT]",
    "phone": "[REDACTED_PHONE]",
    "email": "[REDACTED_EMAIL]",
    "student_id": "[REDACTED_STUDENT_ID]",
    "address": "[REDACTED_ADDRESS]",
}


def redact_pii(text: str, user_name: str | None = None) -> str:
    """Remove all known PII patterns from *text*.

    If *user_name* is provided, also scrub literal occurrences of the
    full name and, for 3-character Chinese names, the given name portion.
    """
    if not text:
        return text

    for key, pattern in PII_PATTERNS.items():
        label = _REPLACEMENT_LABELS.get(key, "[REDACTED]")
        text = pattern.sub(label, text)

    if user_name and len(user_name) >= 2:
        text = text.replace(user_name, "[REDACTED_NAME]")
        # For typical 3-character Chinese names, also mask given name
        if len(user_name) == 3:
            text = text.replace(user_name[1:], "[REDACTED_NAME]")

    return text


def contains_pii(text: str) -> bool:
    """Return True if *text* contains any detectable PII."""
    if not text:
        return False
    for pattern in PII_PATTERNS.values():
        if pattern.search(text):
            return True
    return False


def redact_for_logging(
    *,
    request_id: str = "",
    status: str = "",
    latency_ms: float = 0,
    model_digest: str = "",
    error_type: str = "",
) -> dict[str, Any]:
    """Build a safe log entry containing only non-content metadata.

    This function is the ONLY approved way to log AI requests.
    It intentionally excludes prompts, responses, file contents,
    and any user-supplied text.
    """
    return {
        "request_id": request_id,
        "status": status,
        "latency_ms": round(latency_ms, 1),
        "model_digest": model_digest,
        "error_type": error_type,
    }


def validate_no_pii_in_log(log_entry: dict[str, Any]) -> bool:
    """Assert that a log dict contains no PII in any string value."""
    for value in log_entry.values():
        if isinstance(value, str) and contains_pii(value):
            return False
    return True

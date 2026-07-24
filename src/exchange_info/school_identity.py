from __future__ import annotations

import re
import unicodedata


def school_identity_key(value: str) -> str:
    """Return a stable institution key across translated display-name variants."""
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()
    normalized = re.sub(r"\s*黑龍江省哈爾\s*濱市\s*$", "", normalized).strip()
    english_start = re.search(r"[A-Za-z]", normalized)
    identity = normalized[english_start.start() :] if english_start else normalized
    return identity.strip(" ()（）[]【】,，;；").casefold()

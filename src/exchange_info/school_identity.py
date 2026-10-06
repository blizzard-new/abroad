from __future__ import annotations

import re
import unicodedata
from functools import lru_cache


# Merging the workflow catalogue asks for the key of the same few hundred names over a million times per request, which
# kept a request busy for seconds; the key depends only on the text, so remembering it is safe.
@lru_cache(maxsize=16384)
def school_identity_key(value: str) -> str:
    """Return a stable institution key across translated display-name variants."""
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()
    normalized = re.sub(r"\s*黑龍江省哈爾\s*濱市\s*$", "", normalized).strip()
    english_start = re.search(r"[A-Za-z]", normalized)
    identity = normalized[english_start.start() :] if english_start else normalized
    return identity.strip(" ()（）[]【】,，;；").casefold()


def _loose_key(value: str) -> str:
    """Identity key that ignores PDF-extraction noise: spaces, accents, punctuation."""
    decomposed = unicodedata.normalize("NFKD", school_identity_key(value))
    kept = (ch for ch in decomposed if not unicodedata.combining(ch))
    return "".join(ch for ch in kept if ch.isalnum())


def same_school(left: str, right: str) -> bool:
    """True when two display names are the same institution despite extraction noise.

    A trailing Chinese note on one side (a restriction or language line the PDF
    text extraction appended) is tolerated. A longer Latin name is never treated
    as a match, so "University of Economics" stays distinct from
    "University of Economics and Law".
    """
    first, second = _loose_key(left), _loose_key(right)
    if not first or not second:
        return False
    if first == second:
        return True
    shorter, longer = sorted((first, second), key=len)
    if len(shorter) < 14 or not longer.startswith(shorter):
        return False
    return "一" <= longer[len(shorter)] <= "鿿"

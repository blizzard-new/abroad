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
    # NTU annotates several different schools with the same E/V programme note.
    # Those Latin letters describe the programme, not the institution's name.
    normalized = re.sub(r"\s*\([^()]*(?:交換學生計畫|訪問學生計畫)[^()]*\)\s*$", "", normalized).strip()
    english_start = re.search(r"[A-Za-z]", normalized)
    identity = normalized[english_start.start() :] if english_start else normalized
    return identity.strip(" ()（）[]【】,，;；").casefold()


def _loose_key(value: str) -> str:
    """Identity key that ignores PDF-extraction noise: spaces, accents, punctuation."""
    decomposed = unicodedata.normalize("NFKD", school_identity_key(value))
    kept = (ch for ch in decomposed if not unicodedata.combining(ch))
    return "".join(ch for ch in kept if ch.isalnum())


def visual_country_key(value: str | None) -> str:
    country = (value or "").strip()
    return {"南韓": "韓國", "台灣": "臺灣", "中國": "中國大陸", "大陸地區": "中國大陸"}.get(country, country)


def visual_identity_aliases(value: str) -> tuple[str, ...]:
    """Read explicit bilingual labels; never guess a translation or a campus."""
    aliases = [_loose_key(value)]
    name = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()
    name = re.sub(r"\s*\([^()]*(?:交換學生計畫|訪問學生計畫)[^()]*\)\s*$", "", name).strip()
    english = re.search(r"[A-Za-z]", name)
    scoped = re.search(r"校區|分校|研究所|研究科|學部|大學.*學院|大学.*学院|\bcampus\b|\bfaculty\b|\bdepartment\b|\bschool of\b|\bcollege of\b", name, re.I)
    if english and not scoped:
        prefix = name[:english.start()].strip(" ()（）[]【】,，;；")
        suffix = name[english.start():]
        chinese = re.search(r"[\u3400-\u9fff]", suffix)
        if chinese:
            translation = suffix[chinese.start():].strip(" ()（）[]【】,，;；")
            if re.fullmatch(r"[\u3400-\u9fff ]{2,}(?:大學|大学|學院|学院|技術院|技术院)", translation):
                aliases.extend([_loose_key(suffix[:chinese.start()]), _loose_key(translation)])
        if re.fullmatch(r"[\u3400-\u9fff ]{2,}(?:大學|大学|學院|学院|技術院|技术院)", prefix):
            aliases.append(_loose_key(prefix))
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


class VisualRecordIndex(dict):
    """Exact identity first; tolerate extraction noise only for a unique match.

    This deliberately does not change workflow/account identity. Country aliases
    are limited to known equivalent labels; campus suffixes stay significant. An explicit pending
    or rejected record always wins over an alias. Ambiguous aliases fail closed.
    Build once per catalogue read rather than scanning it for every partner.
    """

    def __init__(self, records=()):
        super().__init__(records)
        self._aliases = {}
        for key, row in self.items():
            name = row.get("school_name", key[0]) if isinstance(row, dict) else getattr(row, "school_name", key[0])
            for name_alias in visual_identity_aliases(name):
                self._aliases.setdefault((name_alias, visual_country_key(key[1])), set()).add(key)

    def get(self, key, default=None):
        exact = (school_identity_key(key[0]), key[1])
        if exact in self:
            return super().get(exact)
        for name in visual_identity_aliases(key[0]):
            matches = self._aliases.get((name, visual_country_key(key[1])), set())
            if matches:
                return super().get(next(iter(matches))) if len(matches) == 1 else default
        return default


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

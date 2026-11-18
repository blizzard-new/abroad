"""Expected school-list badges for NCU's currently bundled home nomination round."""
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata


def _name(value):
    return "".join(unicodedata.normalize("NFKC", value).casefold().split())


@lru_cache(maxsize=1)
def _school_badges():
    path = Path(__file__).resolve().parents[2] / "src/exchange_info/official_data/ncu/partners.jsonl"
    labels = {"open": "中央提名名額已列", "not_open": "本期名單未列", "fee_paying": "自費方案"}
    with path.open(encoding="utf-8") as handle:
        return [(_name(row["school_name"]), labels[row["availability_status"]])
                for row in (json.loads(line) for line in handle)]


def roster_badge(query):
    # A short display search can match both the regular and the paid track.
    labels = sorted({label for name, label in _school_badges() if _name(query) in name})
    assert labels, f"NCU catalogue has no school matching {query!r}"
    return re.compile("|".join(map(re.escape, labels)))

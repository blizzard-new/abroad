"""Reject exact, previously inspected generated life claims, including stale caches.

This is a bounded correction index, not a verifier for new external evidence.
Fresh text or a different supporting URL is not classified by this index.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from .school_identity import school_identity_key

INDEX = Path(__file__).parent / "official_data" / "reviewed_life_claims.json"
INDEX_SHA256 = "f23f7e8cf9b8724ac847f916b44db53f801344d108b73c5c6a57ed3d0875f352"
ADDITIONAL_INDEXES = (
    (INDEX.with_name("reviewed_life_claims_round22.json"),
     "e6d92ef4c4aeea5941177931b5d549df2ffbce57853896c46faad2aec85beb5e"),
    (INDEX.with_name("reviewed_life_claims_round23.json"),
     "582628a877780e551808f70d5089ee93e67c406eb7b68d79da81d67addebdc27"),
    (INDEX.with_name("reviewed_life_claims_round51.json"),
     "d669af68b911ff5eee551bd7173057025cdbdaf1d6cfae95188361a904644269"),
)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf8")).hexdigest()


def life_claim_key(school_name, country, row):
    data = row if isinstance(row, dict) else row.model_dump(mode="json")
    return digest([school_identity_key(school_name), country or "", data["theme"],
        data["text"], sorted({source["url"] for source in data.get("sources", [])})])


def profile_claim_key(profile, field, text):
    data = profile if isinstance(profile, dict) else profile.model_dump(mode="json")
    return digest([data.get("home_university") or "", school_identity_key(data["school_name"]),
        data.get("country") or "", field, text])


@lru_cache(maxsize=1)
def _index():
    life_keys, profile_keys = set(), set()
    for path, expected in ((INDEX, INDEX_SHA256), *ADDITIONAL_INDEXES):
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Reviewed life-claim index hash mismatch")
        data = json.loads(raw)
        life_keys.update(data["life_claim_keys"])
        profile_keys.update(data["profile_claim_keys"])
    return frozenset(life_keys), frozenset(profile_keys)


def withdrawn_life_claim(school_name, country, row):
    return life_claim_key(school_name, country, row) in _index()[0]


def unreviewed_profile_claim(profile, field, text):
    return profile_claim_key(profile, field, text) in _index()[1]

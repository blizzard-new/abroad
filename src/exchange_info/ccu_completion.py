"""CCU general campus references for all 104 identities, including closed rows."""
from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
import json

from .ccu_sources import BUNDLE
from .ccu_completion_sources import validate_completion_source
from .models import ExchangeFieldEvidence, PartnerUniversity


class _ReviewedCompletionIndex(Mapping):
    """Retain validated serialized rows; expand only the requested institution."""
    def __init__(self, rows):
        self._records = {
            row["ccu_page"]: json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            for row in rows
        }

    def __getitem__(self, page):
        return json.loads(self._records[page])

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)


@lru_cache(maxsize=1)
def reviewed_completion():
    path = BUNDLE / "completion-reviewed-fields.json"
    if not path.exists():
        return {}
    rows = json.loads(path.read_text())["schools"]
    if len(rows) != 104 or len({r["ccu_page"] for r in rows}) != 104:
        raise ValueError("CCU completion requires 104 unique exchange identities")
    checked = {}
    for row in rows:
        for field in [*row["general_campus_fields"].values(), *row["host_fields"].values()]:
            if field["status"] == "missing" and field["value"] is not None:
                raise ValueError("Missing CCU completion facts must stay null")
            if field["value"] and not field["evidence"]:
                raise ValueError("CCU completion facts need provenance")
            for ev in field["evidence"]:
                validate_completion_source(BUNDLE, ev, checked)
    return _ReviewedCompletionIndex(rows)


def apply_completion(partner: PartnerUniversity) -> PartnerUniversity:
    row = reviewed_completion().get(partner.source_pages[0])
    if not row:
        return partner
    if (row["school_name"] != partner.school_name or row["country"] != partner.country
            or row["availability_status"] != partner.availability_status):
        raise ValueError("CCU completion school / availability mismatch")
    website = row["general_campus_fields"]["website"]
    if not partner.website and website["status"] == "verified_current":
        partner.website = website["value"]
        partner.field_evidence["website"] = ExchangeFieldEvidence.model_validate(website["evidence"][0])
    public = {"general_campus_fields": row["general_campus_fields"],
              "availability_status": row["availability_status"], "review_note": row["review_note"]}
    if row["availability_status"] == "not_open":
        public["reference_host_fields"] = row["host_fields"]
    partner.reference_data = {**partner.reference_data, "ccu_completion": json.dumps(public, ensure_ascii=False)}
    return partner

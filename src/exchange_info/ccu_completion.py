"""CCU general campus references for all 104 identities, including closed rows."""
from __future__ import annotations

import json
import zlib
from collections.abc import Mapping
from functools import lru_cache

from .ccu_completion_sources import validate_completion_source
from .ccu_sources import BUNDLE
from .json_stream import read_json_object_array
from .models import ExchangeFieldEvidence, PartnerExchangeDetailField, PartnerUniversity


class _ReviewedCompletionIndex(Mapping):
    """Retain validated compressed rows; expand only the requested institution."""
    def __init__(self, records):
        self._records = records

    def __getitem__(self, page):
        return json.loads(zlib.decompress(self._records[page]))

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)


@lru_cache(maxsize=1)
def reviewed_completion():
    path = BUNDLE / "completion-reviewed-fields.json"
    if not path.exists():
        return {}
    records = {}
    checked = {}

    def receive(row):
        if row["ccu_page"] in records:
            raise ValueError("CCU completion requires 104 unique exchange identities")
        if set(row.get("host_override_keys", [])) - set(row["host_fields"]):
            raise ValueError("Unknown CCU receiving supplement key")
        for field in [*row["general_campus_fields"].values(), *row["host_fields"].values()]:
            if field["status"] == "missing" and field["value"] is not None:
                raise ValueError("Missing CCU completion facts must stay null")
            if field["value"] and not field["evidence"]:
                raise ValueError("CCU completion facts need provenance")
            for ev in field["evidence"]:
                validate_completion_source(BUNDLE, ev, checked)
        records[row["ccu_page"]] = zlib.compress(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )

    with path.open(encoding="utf-8") as handle:
        read_json_object_array(handle, "schools", receive)
    if len(records) != 104:
        raise ValueError("CCU completion requires 104 unique exchange identities")
    return _ReviewedCompletionIndex(records)


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
    elif row.get("host_override_keys"):
        # Apply only explicitly reviewed CCU receiving supplements. Mother's
        # quotas, qualifications, documents and closed home window stay separate.
        overrides = {
            key: PartnerExchangeDetailField.model_validate(row["host_fields"][key])
            for key in row["host_override_keys"]
        }
        partner.partner_exchange_details = {**partner.partner_exchange_details, **overrides}
        public["host_override_keys"] = row["host_override_keys"]
        language = overrides.get("language")
        if language and language.status in {"conflict", "needs_confirmation"}:
            partner.language_review_note = language.value or language.reason
            for condition in partner.language_conditions:
                condition.requirement_level = language.status
                condition.scope_choice_required = True
                if partner.language_review_note not in condition.additional_conditions:
                    condition.additional_conditions.append(partner.language_review_note)
                condition.evidence.status = language.status
                condition.evidence.note = partner.language_review_note
            if partner.language_review_note not in partner.student_summary_zh.eligibility_points:
                partner.student_summary_zh.eligibility_points.append(partner.language_review_note)
        calendar = overrides.get("academic_calendar")
        if calendar and calendar.status == "conflict":
            if partner.semester_dates:
                partner.reference_data.setdefault("semester_dates", partner.semester_dates)
            partner.semester_dates = calendar.value
            partner.student_summary_zh.study_period = (
                (partner.study_period or "") + "；" + (calendar.value or "")
            )
        deadline = overrides.get("application_deadline")
        if deadline and deadline.status == "conflict":
            if partner.partner_application_deadline:
                partner.reference_data = {
                    **partner.reference_data,
                    "partner_application_deadline": partner.reference_data.get(
                        "partner_application_deadline", partner.partner_application_deadline
                    ),
                }
            partner.partner_application_deadline = deadline.value
            partner.student_summary_zh.application_deadline = deadline.value
            if old := partner.field_evidence.get("partner_application_deadline"):
                partner.field_evidence = {
                    **partner.field_evidence,
                    "partner_application_deadline": old.model_copy(update={
                        "status": "conflict", "note": deadline.reason + "；" + (deadline.value or "")
                    }),
                }
    partner.reference_data = {**partner.reference_data, "ccu_completion": json.dumps(public, ensure_ascii=False)}
    from .ccu_sungshin_current import apply_sungshin_summary
    return apply_sungshin_summary(partner)

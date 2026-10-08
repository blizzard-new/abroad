"""TKU evidence schema and offline readers, independent of other universities."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BUNDLE = Path(__file__).resolve().parent / "official_data" / "tku"
CHECKED_AT = datetime.fromisoformat("2026-10-08T00:00:00+00:00")
HOME = "淡江大學"


class TKUEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    source_url: str
    locator: str
    applicable_year: str
    application_round: str
    role: Literal["home_outbound", "host_incoming", "directory_reference"]
    checked_at: datetime
    quote: str = ""


class TKUFact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str | int | None
    status: Literal["verified", "reference_only", "missing_in_source", "not_verified_new", "needs_confirmation", "not_applicable"]
    evidence: list[TKUEvidence] = Field(min_length=1)

    @model_validator(mode="after")
    def unknown_is_null(self):
        if self.status in {"missing_in_source", "not_verified_new", "not_applicable"} and self.value is not None:
            raise ValueError("unknown/nonapplicable facts must retain a null value")
        return self


class TKUPartnerRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    home_university: Literal["淡江大學"] = HOME
    round_id: str
    academic_year: str
    application_round: str
    selection_status: Literal["listed", "reference_only"]
    quota_status: Literal["numeric", "zero", "blank", "provisional"]
    quota_number: int | None = Field(default=None, ge=0)
    fields: dict[str, TKUFact]
    conflicts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_quota(self):
        if self.quota_status == "numeric" and (self.quota_number is None or self.quota_number <= 0):
            raise ValueError("confirmed numeric quota must be positive")
        if self.quota_status == "zero" and self.quota_number != 0:
            raise ValueError("zero quota must be explicit")
        if self.quota_status in {"blank", "provisional"} and self.quota_number is not None:
            raise ValueError("blank/provisional quota is not a confirmed number")
        for key in ("school_name", "country", "degree_levels", "language", "quota", "home_eligibility", "host_eligibility", "home_deadline", "host_deadline", "study_period", "documents", "housing", "costs", "course_restrictions"):
            if key not in self.fields:
                raise ValueError(f"missing required field state: {key}")
        return self


def load_tku_sources() -> list[dict]:
    return json.loads((BUNDLE / "sources.json").read_text(encoding="utf-8"))


def load_tku_rounds() -> list[dict]:
    return json.loads((BUNDLE / "rounds.json").read_text(encoding="utf-8"))


def load_tku_records(*, include_reference: bool = False) -> list[TKUPartnerRecord]:
    paths = [BUNDLE / "partners_current.jsonl"]
    if include_reference:
        paths.append(BUNDLE / "partners_reference.jsonl")
    return [TKUPartnerRecord.model_validate_json(line) for path in paths
            for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tku_integrity_report() -> dict:
    sources = {row["id"]: row for row in load_tku_sources()}
    rows = load_tku_records(include_reference=True)
    ids = [row.id for row in rows]
    problems = []
    if len(ids) != len(set(ids)):
        problems.append("duplicate programme record IDs")
    states: dict[str, int] = {}
    for row in rows:
        for key, fact in row.fields.items():
            states[fact.status] = states.get(fact.status, 0) + 1
            for evidence in fact.evidence:
                source = sources.get(evidence.source_id)
                if not source or source["source_url"] != evidence.source_url:
                    problems.append(f"{row.id}.{key}: unresolved source")
                if evidence.checked_at != CHECKED_AT:
                    problems.append(f"{row.id}.{key}: unexpected check date")
                if row.selection_status == "listed" and evidence.role == "home_outbound" and evidence.applicable_year != row.academic_year:
                    problems.append(f"{row.id}.{key}: older home evidence in current round")
    return {"records": len(rows), "current_round_records": sum(r.selection_status == "listed" for r in rows),
            "reference_records": sum(r.selection_status == "reference_only" for r in rows),
            "confirmed_current_quota": sum(r.quota_number or 0 for r in rows if r.selection_status == "listed"),
            "fact_states": states, "issues": problems}

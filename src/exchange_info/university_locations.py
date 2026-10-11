"""Reviewed, offline university locations; never geocode during a web request."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from .school_identity import VisualRecordIndex, school_identity_key

LOCATION_CATALOG = Path(__file__).parent / "official_data" / "university_locations.jsonl"
logger = logging.getLogger(__name__)


class UniversityLocation(BaseModel):
    school_name: str
    country: str | None = None
    city: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    geocode_status: Literal["pending", "verified", "needs_review"] = "pending"
    geocoded_at: datetime | None = None
    source_url: str | None = None
    identity_source_url: str | None = None
    precision: Literal["campus", "representative"] = "representative"
    note: str = "座標待確認；不以國家或城市中心代替學校。"

    @model_validator(mode="after")
    def validate_verified_location(self):
        if self.geocode_status == "verified" and (
            self.latitude is None or self.longitude is None
            or not self.source_url or not self.geocoded_at
        ):
            raise ValueError("Verified coordinates require a pair, source and timestamp")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Coordinates must be supplied as a pair")
        return self


def location_key(school_name: str, country: str | None) -> tuple[str, str]:
    return school_identity_key(school_name), (country or "").strip()


def load_university_locations(data_dir: Path) -> dict[tuple[str, str], UniversityLocation]:
    """Use the tracked baseline plus operator-reviewed local overrides.

    A malformed row cannot make unrelated schools disappear. Invalid local rows
    are fail-closed for their own identity, including a previously verified row.
    """
    records: dict[tuple[str, str], UniversityLocation] = {}
    for path in (LOCATION_CATALOG, Path(data_dir) / "processed" / "university_locations.jsonl"):
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            raw = None
            try:
                raw = json.loads(line)
                record = UniversityLocation.model_validate(raw)
            except (ValueError, ValidationError):
                logger.warning("Invalid university location in %s at row %d", path.name, number)
                if isinstance(raw, dict) and isinstance(raw.get("school_name"), str):
                    country = raw.get("country") if isinstance(raw.get("country"), str) else None
                    record = UniversityLocation(school_name=raw["school_name"], country=country, geocode_status="needs_review")
                else:
                    continue
            records[location_key(record.school_name, record.country)] = record
    return VisualRecordIndex(records)


def public_location(records, school_name: str, country: str | None = None) -> UniversityLocation:
    key = (school_name, (country or "").strip()) if isinstance(records, VisualRecordIndex) else location_key(school_name, country)
    record = records.get(key)
    if record is None:
        return UniversityLocation(school_name=school_name, country=country)
    if record.geocode_status != "verified":
        return record.model_copy(update={"latitude": None, "longitude": None})
    return record

from datetime import datetime, timezone
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from exchange_info.api import create_app
from exchange_info.models import PartnerUniversity, StudentDashboard
from exchange_info.university_locations import (
    UniversityLocation, load_university_locations, public_location,
)


def verified(**overrides):
    return UniversityLocation(**{
        "school_name": "Location test university", "country": "日本", "city": "Tokyo",
        "latitude": 35.7, "longitude": 139.8, "geocode_status": "verified",
        "geocoded_at": datetime.now(timezone.utc), "source_url": "https://www.wikidata.org/wiki/Q46492",
        **overrides,
    })


@pytest.mark.parametrize("fields", [
    {"latitude": 91}, {"longitude": -181}, {"latitude": float("nan")},
    {"longitude": float("inf")}, {"longitude": None},
    {"source_url": None}, {"geocoded_at": None},
])
def test_invalid_verified_location_is_rejected(fields):
    with pytest.raises(ValidationError):
        verified(**fields)


def test_bad_row_does_not_break_valid_schools_and_override_fails_closed(tmp_path, monkeypatch):
    import exchange_info.university_locations as locations
    baseline = tmp_path / "baseline.jsonl"
    baseline.write_text(verified().model_dump_json() + "\n", encoding="utf-8")
    monkeypatch.setattr(locations, "LOCATION_CATALOG", baseline)
    processed = tmp_path / "processed"
    processed.mkdir()
    bad_override = verified().model_dump(mode="json") | {"latitude": 1000}
    good = verified(school_name="Other University")
    (processed / "university_locations.jsonl").write_text("not json\n" + json.dumps(bad_override) + "\n" + good.model_dump_json() + "\n", encoding="utf-8")
    records = load_university_locations(tmp_path)
    invalid = public_location(records, "Location test university", "日本")
    assert invalid.geocode_status == "needs_review"
    assert invalid.latitude is None
    assert public_location(records, "Other University", "日本").latitude == 35.7
    assert public_location(records, "Other University", "美國").latitude is None
    assert public_location(records, "Unknown", "日本").geocode_status == "pending"


def test_pending_coordinate_candidate_is_not_exposed(tmp_path, monkeypatch):
    import exchange_info.university_locations as locations
    path = tmp_path / "locations.jsonl"
    path.write_text(verified(geocode_status="needs_review").model_dump_json() + "\n", encoding="utf-8")
    monkeypatch.setattr(locations, "LOCATION_CATALOG", path)
    record = public_location(load_university_locations(tmp_path), "Location test university", "日本")
    assert record.latitude is None and record.longitude is None


def test_dashboard_adds_location_without_changing_partnerships(tmp_path, monkeypatch):
    import exchange_info.api as api
    partner = PartnerUniversity(school_name="Location test university", country="日本", program_type="交換學生", quota="2", source_url="https://example.edu/official")
    monkeypatch.setattr(api, "build_student_dashboard", lambda *a, **k: StudentDashboard(partner_universities=[partner]))
    monkeypatch.setattr(api, "fetch_partner_universities", lambda: [partner])
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "university_locations.jsonl").write_text(verified().model_dump_json() + "\n", encoding="utf-8")
    with TestClient(create_app(tmp_path)) as client:
        response = client.get("/student-dashboard")
        assert response.status_code == 200
        rows = response.json()["partner_universities"]
        assert len(rows) == 1
        assert rows[0]["quota"] == "2" and rows[0]["source_url"] == partner.source_url
        assert rows[0]["location"]["latitude"] == 35.7
        universities = client.get("/universities").json()
        assert len(universities) >= 2
        assert all(row["location"]["school_name"] == row["school_name"] for row in universities)


def test_bundled_locations_are_valid_unique_and_sourced():
    import exchange_info.university_locations as locations
    rows = [UniversityLocation.model_validate_json(line) for line in locations.LOCATION_CATALOG.read_text(encoding="utf-8").splitlines()]
    keys = [locations.location_key(r.school_name, r.country) for r in rows]
    assert len(keys) == len(set(keys))
    for row in rows:
        if row.geocode_status == "verified":
            assert row.source_url.startswith("https://www.wikidata.org/wiki/Q")
            assert row.identity_source_url.startswith("https://ror.org/")
            assert row.city and row.geocoded_at
            assert -90 <= row.latitude <= 90 and -180 <= row.longitude <= 180


def test_offline_candidate_matching_requires_unique_domain_country_and_campus():
    from scripts.refresh_university_locations import verified_candidate
    row = {"school_name": "Test University", "country": "日本", "website": "https://example.ac.jp/"}
    candidate = {"status": "active", "types": ["education"], "domains": ["example.ac.jp"], "locations": [{"geonames_details": {"country_code": "JP"}}]}
    assert verified_candidate(row, [candidate]) == candidate
    assert verified_candidate(row, [candidate, candidate]) is None
    assert verified_candidate(row | {"country": "美國"}, [candidate]) is None
    assert verified_candidate(row | {"website": "https://other.ac.jp"}, [candidate]) is None
    assert verified_candidate(row | {"school_name": "Test University Campus"}, [candidate]) is None

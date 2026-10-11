"""A scoped campus conflict cannot be undone by a broad shared location."""
import json

import pytest

from exchange_info.ncu_completion import campus_location
from exchange_info.ncu_student_view import build_ncu_student_dashboard
from exchange_info.university_locations import (
    UniversityLocation, load_university_locations, public_location,
)


def partner(name):
    return next(p for p in build_ncu_student_dashboard().partner_universities if name in p.school_name)


def test_hiroshima_explicit_campus_hold_precedes_verified_shared_fallback(tmp_path):
    p = partner("Hiroshima")
    shared = public_location(load_university_locations(tmp_path), p.school_name, p.country)
    assert shared.geocode_status == "verified"  # reproduces the integrated input conflict
    result = campus_location(p, shared, tmp_path)
    assert result.geocode_status == "needs_review"
    assert result.latitude is None and result.longitude is None
    assert "校區" in result.note
    # The NCU hold must not change the shared record used by other schools.
    assert public_location(load_university_locations(tmp_path), p.school_name, p.country) == shared


@pytest.mark.parametrize("name,latitude,longitude,scope", [
    ("Chuo", 35.708143, 139.748968, "Korakuen"),
    ("Shanghai Jiao Tong", 31.025393, 121.436348, "閔行"),
])
def test_new_named_campus_evidence_supersedes_its_old_hold(name, latitude, longitude, scope):
    result = campus_location(partner(name), None)
    assert result.geocode_status == "verified"
    assert (result.latitude, result.longitude) == (latitude, longitude)
    assert scope in result.note
    if name == "Chuo":
        assert result.city == "Tokyo / Bunkyo"
        assert "korakuen" in result.identity_source_url


def test_operator_review_can_resolve_a_scoped_hold_without_changing_other_countries(tmp_path):
    p = partner("Hiroshima")
    reviewed = UniversityLocation(
        school_name=p.school_name, country=p.country, latitude=34.4, longitude=132.7,
        geocode_status="verified", geocoded_at="2026-10-11T00:00:00Z",
        source_url="https://example.edu/test-reviewed-campus", note="Isolated operator fixture",
    )
    path = tmp_path / "processed/university_locations.jsonl"
    path.parent.mkdir()
    path.write_text(reviewed.model_dump_json() + "\n")
    assert campus_location(p, None, tmp_path) == reviewed
    assert campus_location(p.model_copy(update={"country": "臺灣"}), None, tmp_path) is None


def test_missing_primary_coordinates_do_not_ban_an_independent_verified_source():
    p = partner("Bingöl")
    independent = UniversityLocation(
        school_name=p.school_name, country=p.country, latitude=38.8, longitude=40.5,
        geocode_status="verified", geocoded_at="2026-10-11T00:00:00Z",
        source_url="https://example.edu/independent-campus-fixture",
    )
    assert campus_location(p, independent) == independent

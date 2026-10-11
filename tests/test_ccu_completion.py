"""All-school coverage, provenance and eligibility boundaries for CCU additions."""
import gzip
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_completion_sources import validate_completion_source
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.storage import load_destination_profiles


def read(name):
    return json.loads((BUNDLE / name).read_text())


def test_full_denominator_and_original_profiles_are_preserved():
    rows = read("completion-reviewed-fields.json")["schools"]
    assert len(rows) == len({r["ccu_page"] for r in rows}) == 104
    assert sum(r["availability_status"] == "not_open" for r in rows) == 49
    assert all(len(r["profile_fields"]) == 7 and len(r["host_fields"]) == 17 for r in rows)
    lines = (BUNDLE / "destination_profiles.jsonl").read_bytes().splitlines(keepends=True)
    assert len(lines) == 104
    assert hashlib.sha256(b"".join(lines[:55])).hexdigest() == "1375f32052bcdeaedfe696073e7ada6d40f40bdebeba0dc1e7f82353e38b78e6"
    baseline = read("completion-baseline.json")
    current = read("completion-inventory.json")
    assert baseline["denominators"]["broader_global_agreements"] is None
    assert current["denominators"]["broader_global_agreements"] is None
    assert current["denominators"]["published_nonzero_quota"] == 52
    assert current["denominators"]["unknown_quota"] == 3


def test_reference_and_blank_quota_schools_do_not_become_eligible():
    partners = fetch_ccu_partner_universities()
    for partner in partners:
        assert partner.application_window_status == "closed"
        if partner.availability_status == "not_open":
            assert partner.quota is None and partner.eligibility is None and partner.language_requirement is None
    assert {p.source_pages[0] for p in partners if p.quota_status == "not_published"} == {71, 80, 107}
    ateneo = next(p for p in partners if p.source_pages[0] == 81)
    fields = json.loads(ateneo.reference_data["ccu_completion"])["reference_host_fields"]
    assert ateneo.availability_status == "not_open"
    assert "2026-09-30" in fields["application_deadline"]["value"]
    assert "2026-09-01" in fields["application_deadline"]["value"]
    assert len({ev["source_id"] for ev in fields["application_deadline"]["evidence"]}) == 2
    assert "iBT79" in fields["language"]["value"] and "iBT80" in fields["language"]["value"]
    assert fields["application_forms"]["status"] == "needs_confirmation"
    assert fields["housing"]["status"] == "missing"


def test_conflicting_years_and_invalid_dates_stay_unresolved():
    rows = {r["ccu_page"]: r for r in read("completion-reviewed-fields.json")["schools"]}
    deadline = rows[51]["host_fields"]["application_deadline"]
    assert deadline["status"] == "conflict"
    assert "November31" in deadline["value"] and "不存在" in deadline["value"]
    assert any("2021" in ev["academic_year"] for ev in deadline["evidence"])
    assert any("2026" in ev["academic_year"] for ev in deadline["evidence"])
    assert "2027" in deadline["value"] and "未核實" in deadline["value"]
    assert rows[13]["host_fields"]["housing"]["status"] == "conflict"
    assert "2025-09-14" in rows[13]["host_fields"]["housing"]["value"]


def test_reviewed_campuses_are_precise_and_unknowns_are_not_city_centres():
    assets = read("campus-assets.json")["schools"]
    points = {r["ccu_page"]: r["coordinates"] for r in assets}
    assert sum(f["status"] == "verified_current" for f in points.values()) == 101
    assert points[41]["value"]["city"] == "Seoul"  # ROR had Suwon; point is Seoul.
    assert points[83]["value"]["latitude"] == 14.5904883
    assert points[83]["value"]["longitude"] == 120.9779484
    assert points[112]["value"]["latitude"] == 50.129976  # Official GPS text, not @ viewport.
    assert points[103]["value"]["latitude"] == 47.4972243  # School of Engineering marker.
    assert points[104]["value"]["longitude"] == 7.911147  # Olten Riggenbachstrasse, not Muttenz.
    assert points[79]["value"]["latitude"] == 20.3555462
    assert points[105]["value"]["longitude"] == 32.8564133
    assert points[105]["value"]["longitude"] != 32.85319811498272  # Embed viewport.
    assert points[107]["value"]["latitude"] == 50.04816
    assert points[107]["value"]["longitude"] != 15.7677468  # Embed viewport.
    assert points[88]["value"]["latitude"] == 50.63312
    assert points[88]["value"]["longitude"] == 3.0439062
    assert points[74]["value"]["latitude"] == 9.5100096
    assert points[74]["value"]["longitude"] == 76.5513594
    assert points[68]["value"]["longitude"] == 106.7719131
    assert points[68]["value"]["longitude"] != 106.7693382
    for page in [71, 111, 119]:
        assert points[page]["value"] is None
    assert "Q1321805" not in points[34]["value"]["source_url"]
    assert "Q1191132" in points[34]["value"]["source_url"]


def test_photos_have_identity_licence_author_and_original_bytes():
    photos = {r["ccu_page"]: r["photo"] for r in read("campus-assets.json")["schools"]}
    assert sum(f["status"] == "verified_current" for f in photos.values()) == 100
    for field in photos.values():
        if field["status"] != "verified_current":
            assert field["value"] is None
            continue
        photo = field["value"]
        assert all(photo[k] for k in ["artist", "license_name", "license_url", "source_page_url", "campus_caption", "checked_at"])
        file = BUNDLE.parents[1] / photo["local_path"].removeprefix("/")
        assert hashlib.sha256(file.read_bytes()).hexdigest() == photo["sha256"]
    assert "Loyola" in photos[81]["value"]["campus_caption"]
    assert "Grade" not in photos[81]["value"]["source_page_url"]
    assert "School_of_Engineering" in photos[103]["value"]["source_page_url"]
    assert "Karvina" in photos[111]["value"]["source_page_url"]
    assert "E-waste-lab" in photos[77]["value"]["source_page_url"]
    assert "Brugg-Windisch" in photos[104]["value"]["campus_caption"]
    assert photos[77]["value"]["sha256"] != read("completion_sources/p77-followup-reviewed-campus.json")["sha256"]


def test_all_fresh_evidence_has_receipts_and_unchanged_response_bytes():
    verified = {}
    for row in read("completion-reviewed-fields.json")["schools"]:
        for field in [*row["general_campus_fields"].values(), *row["host_fields"].values()]:
            assert field["reason"]
            if field["status"] == "missing":
                assert field["value"] is None
            for ev in field["evidence"]:
                assert ev["academic_year"] and ev["checked_at"] and ev["source_url"]
                validate_completion_source(BUNDLE, ev, verified)
    assert len(verified) > 200


def test_compressed_source_tampering_and_mismatched_duplicate_evidence_fail(tmp_path):
    receipts = tmp_path / "completion_sources"
    receipts.mkdir()
    payload = gzip.compress(b"official content", mtime=0)
    (receipts / "p1-root.html.gz").write_bytes(payload)
    digest = hashlib.sha256(b"official content").hexdigest()
    record = {"source_id": "p1-root", "bundled_file": "completion_sources/p1-root.html.gz", "sha256": digest,
              "stored_sha256": hashlib.sha256(payload).hexdigest(), "tls_verify": True, "http_status": 200}
    (receipts / "p1-root.receipt.json").write_text(json.dumps(record))
    ev = {"source_id": "p1-root", "content_hash": digest, "source_url": "https://example.edu"}
    checked = {}
    validate_completion_source(tmp_path, ev, checked)
    with pytest.raises(ValueError, match="Inconsistent"):
        validate_completion_source(tmp_path, {**ev, "content_hash": "0" * 64}, checked)
    (receipts / "p1-root.html.gz").write_bytes(payload + b"changed")
    with pytest.raises(ValueError, match="Changed CCU compressed"):
        validate_completion_source(tmp_path, ev, {})


def test_real_api_serves_all_profiles_and_local_photographs_without_other_school_changes(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("/student-dashboard", params={"school": HOME})
    assert response.status_code == 200
    partners = response.json()["partner_universities"]
    assert len(partners) == 104
    assert sum(p["image_status"] == "verified" for p in partners) == 100
    assert sum(p["location"]["geocode_status"] == "verified" for p in partners) == 101
    for source_page in [34, 81, 103, 111]:
        partner = next(p for p in partners if p["source_pages"][0] == source_page)
        image = client.get(partner["image_url"])
        assert image.status_code == 200 and image.headers["content-type"].startswith("image/")
        metadata = json.loads(partner["reference_data"]["ccu_campus_assets"])
        assert metadata["photo"]["license_url"].startswith("https://")
    coverage = client.get("/coverage", params={"school": HOME}).json()
    assert coverage["image_count"] == 100
    assert coverage["destination_profile_count"] == 104
    profiles = load_destination_profiles(tmp_path, include_bundled_baseline=True)
    assert sum(p.home_university == HOME for p in profiles) == 104
    assert sum(p.home_university == "長庚大學" for p in profiles) == 77
    assert sum(p.home_university == "國立臺北大學" for p in profiles) == 206


def test_shared_alias_photos_and_points_cannot_replace_reviewed_ccu_campus(monkeypatch, tmp_path):
    from exchange_info import api
    from exchange_info.ccu_profile import school_location
    from exchange_info.school_identity import school_identity_key
    from exchange_info.university_locations import UniversityLocation

    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 103)
    monkeypatch.setattr(api, "_load_school_image_manifest", lambda: {
        (school_identity_key(partner.school_name), partner.country): {
            "status": "verified", "local_path": "/static/assets/shared-parent.jpg",
            "image_url": "/static/assets/shared-parent.jpg", "checked_at": "2025-01-01T00:00:00Z"
        }
    })
    client = TestClient(create_app(tmp_path))
    partners = client.get("/student-dashboard", params={"school": HOME}).json()["partner_universities"]
    actual = next(p for p in partners if p["source_pages"][0] == 103)
    assert "/static/assets/ccu/campuses/" in actual["image_url"]
    assert client.get("/coverage", params={"school": HOME}).json()["image_count"] == 100
    shared_parent = UniversityLocation(school_name=partner.school_name, country=partner.country,
        latitude=47.5, longitude=8.7, geocode_status="verified", source_url="https://example.edu/parent",
        geocoded_at="2025-01-01T00:00:00Z")
    assert school_location(partner, shared_parent, tmp_path).latitude == 47.4972243


@pytest.mark.parametrize("status", ["verified", "pending", "invalid"])
def test_explicit_local_operator_campus_decision_is_preserved(status, tmp_path):
    from exchange_info.ccu_profile import school_location
    from exchange_info.university_locations import UniversityLocation

    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 103)
    canonical = next(r for r in read("completion-targets.json") if r["ccu_page"] == 103)["canonical_name"]
    raw = {"school_name": canonical, "country": partner.country, "geocode_status": "pending"}
    if status != "pending":
        raw.update(geocode_status="verified", latitude=47.6, longitude=8.8,
                   source_url="https://example.edu/local-campus", geocoded_at="2026-10-11T00:00:00Z")
    if status == "invalid":
        raw["latitude"] = 999
    path = tmp_path / "processed/university_locations.jsonl"
    path.parent.mkdir()
    path.write_text(json.dumps(raw) + "\n")
    result = school_location(partner, UniversityLocation(school_name=partner.school_name), tmp_path)
    assert result.geocode_status == ("needs_review" if status == "invalid" else status)
    assert result.latitude == (47.6 if status == "verified" else None)
    assert result.longitude == (8.8 if status == "verified" else None)


def test_pr8_restoration_and_new_asset_denominators_are_separate():
    comparison = read("completion-pr8-coverage-comparison.json")
    assert comparison["integration_head"] == "9927ec1d8765a9772671bbaa68e7f920995f1258"


def test_new_iitb_year_and_forms_remain_separate_from_home_eligibility():
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 72)
    assert partner.availability_status == "not_open"
    assert partner.quota is None and partner.eligibility is None and partner.language_requirement is None
    fields = json.loads(partner.reference_data["ccu_completion"])["reference_host_fields"]
    assert fields["application_deadline"]["status"] == "verified_current"
    assert "2026-09-30" in fields["application_deadline"]["value"]
    assert any(ev["source_pages"] == [3] and "2026–2027" in ev["academic_year"] for ev in fields["application_deadline"]["evidence"])
    assert fields["nomination_deadline"]["status"] == "needs_confirmation"
    assert fields["housing_deadline"]["status"] == "needs_confirmation"
    assert fields["application_forms"]["status"] == "needs_confirmation"
    assert "到校後" in fields["application_forms"]["value"]
    assert "版本" in fields["application_forms"]["value"]
    assert "MoU" in fields["host_tuition"]["value"] and "行政" in fields["host_tuition"]["value"]


def test_followup_gap_baseline_and_source_failures_are_not_nonpublication_claims():
    baseline = read("completion-followup-gap-baseline.json")
    current = read("completion-followup-gap-research.json")
    assert baseline["initial_counts"]["host_missing_fields"] == 702
    assert current["initial_counts"]["host_missing_fields"] == 585
    assert current["global_agreements"]["denominator"] is None
    assert "未證明" in current["global_agreements"]["reason"]
    for school in current["schools"]:
        for field in school["unresolved_host_fields"]:
            assert field["classification"] == "research_incomplete"
            assert field["official_not_announced"] is False
            assert field["personal_access_required"] is None
    keimyung = next(s for s in current["schools"] if s["ccu_page"] == 44)
    assert any(s["http_status"] == 503 and s["classification"] == "source_failure" for s in keimyung["attempted_sources"])

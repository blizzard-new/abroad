"""Home-scoped coverage and guides must agree with actual bundled profiles."""

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info import api, storage
from exchange_info.models import DestinationProfile, PartnerUniversity

BUNDLE = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/ccu"


def read(name):
    return json.loads((BUNDLE / name).read_text())


@pytest.mark.parametrize("home", ["國立臺北大學", "國立中正大學"])
def test_coverage_counts_existing_home_scoped_profile(monkeypatch, tmp_path, home):
    profiles = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    profile = next(row for row in profiles if row.home_university == home and row.coverage_status != "not_collected")
    partner = PartnerUniversity(school_name=profile.school_name, country=profile.country, program_type="交換學生", source_url="https://new.ntpu.edu.tw/oia/sister-schools")
    collector = "fetch_ntpu_partner_universities" if home == "國立臺北大學" else "fetch_ccu_partner_universities"
    monkeypatch.setattr(api, collector, lambda: [partner])
    client = TestClient(api.create_app(tmp_path))
    coverage = client.get("/coverage", params={"school": home}).json()
    guide = client.get("/destination-profile", params={"school": partner.school_name, "home_school": home}).json()
    assert coverage["destination_profile_count"] == 1
    assert coverage["partners"][0]["destination_status"] == guide["coverage_status"] == profile.coverage_status
    assert coverage["partners"][0]["destination_last_checked"] == guide["last_checked"]
    assert guide["home_university"] == home


def test_other_home_profile_is_not_counted_or_returned(monkeypatch, tmp_path):
    partner = PartnerUniversity(school_name="Shared Partner University", country="Japan", program_type="交換學生", source_url="https://new.ntpu.edu.tw/oia/sister-schools")
    foreign = DestinationProfile(home_university="長庚大學", school_name=partner.school_name, country="Japan", coverage_status="official_partial", housing_summary="CGU-only housing evidence")
    monkeypatch.setattr(api, "fetch_ntpu_partner_universities", lambda: [partner])
    monkeypatch.setattr(api, "load_destination_profiles", lambda *args, **kwargs: [foreign])
    client = TestClient(api.create_app(tmp_path))
    coverage = client.get("/coverage", params={"school": "國立臺北大學"}).json()
    guide = client.get("/destination-profile", params={"school": partner.school_name, "home_school": "國立臺北大學"}).json()
    assert coverage["destination_profile_count"] == 0
    assert coverage["partners"][0]["destination_status"] == "not_collected"
    assert guide["home_university"] == "國立臺北大學"
    assert guide["coverage_status"] == "not_collected"
    assert not guide["housing_summary"]


def test_current_sungshin_waiver_keeps_visiting_and_language_fees_separate():
    row = next(r for r in read("overseas-reviewed-fields.json") if r["ccu_page"] == 49)
    field = row["fields"]["host_tuition"]
    assert field["status"] == "verified_current"
    assert "visiting" in field["value"] and "160,000" in field["value"] and "800,000" in field["value"]
    assert {tuple(e["source_pages"]) for e in field["evidence"]} == {(3,), (5,)}
    for evidence in field["evidence"]:
        raw = read("overseas_sources/" + evidence["source_id"] + ".json")
        body = " ".join(" ".join(raw["text_pages"][p - 1] for p in evidence["source_pages"]).split())
        assert evidence["excerpt"] in body
    assert row["fields"]["academic_calendar"]["status"] == "conflict"


def test_ludwigshafen_nomination_does_not_invent_language_or_degree_threshold():
    row = next(r for r in read("overseas-reviewed-fields.json") if r["ccu_page"] == 98)
    field = row["fields"]["eligibility"]
    assert field["status"] == "verified_current"
    assert field["evidence"][0]["source_pages"] == [1]
    assert "nominated through the coordinator" in field["evidence"][0]["excerpt"]
    assert row["fields"]["language"]["status"] == "missing"


def test_body_triage_has_review_proof_and_no_false_exhaustion_or_announcement():
    triage = read("body-review-triage.json")
    assert triage["school_count"] == 55
    sources = [r for school in triage["schools"] for r in school["sources"]] + triage["shared_home_sources"]
    registry = read("overseas-source-registry.json")
    assert {r["source_id"] for r in sources} == {r["source_id"] for r in registry}
    assert len(sources) == sum(triage["state_counts"].values()) == len(registry)
    for school in triage["schools"]:
        assert school["public_sources_exhausted"] is False
        for source in school["sources"]:
            if source["body_state"] == "read_body_not_mapped":
                assert source["read_evidence"] and not source["mapped_fields"]
            if source["full_saved_body_read"]:
                assert any(r["extent"] == "complete_saved_text_body" for r in source["read_evidence"])
            assert not source["all_policy_review_complete"]
    for name, digest in triage["input_sha256"].items():
        assert hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest() == digest
    subclaim = triage["explicit_unannounced_subclaims"][0]
    assert subclaim["source_id"] == "p49-mirror" and subclaim["source_pages"] == [6]
    assert "National Health Insurance" in subclaim["scope"]


@pytest.mark.parametrize("home,alias,collector", [
    ("長庚大學", "CGU", "fetch_partner_universities"),
    ("長庚大學", "長庚", "fetch_partner_universities"),
    ("國立臺北大學", "NTPU", "fetch_ntpu_partner_universities"),
    ("國立臺北大學", "北大", "fetch_ntpu_partner_universities"),
    ("國立臺灣大學", "NTU", "fetch_ntu_partner_universities"),
    ("國立臺灣大學", "台大", "fetch_ntu_partner_universities"),
    ("國立中正大學", "CCU", "fetch_ccu_partner_universities"),
    ("國立中正大學", "中正", "fetch_ccu_partner_universities"),
])
def test_destination_home_alias_keeps_real_profile_and_canonical_home(monkeypatch, tmp_path, home, alias, collector):
    profiles = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    profile = next(row for row in profiles if row.home_university == home and row.coverage_status != "not_collected")
    partner = PartnerUniversity(school_name=profile.school_name, country=profile.country, program_type="交換學生", source_url="https://oia.ccu.edu.tw/")
    monkeypatch.setattr(api, collector, lambda: [partner])
    client = TestClient(api.create_app(tmp_path))
    response = client.get("/destination-profile", params={"school": profile.school_name, "home_school": alias})
    assert response.status_code == 200
    guide = response.json()
    assert guide["home_university"] == home
    assert guide["coverage_status"] == profile.coverage_status
    assert guide["last_checked"] == profile.model_dump(mode="json")["last_checked"]
    assert guide["housing_summary"] == profile.housing_summary

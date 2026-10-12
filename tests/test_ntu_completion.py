import copy
import hashlib
import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import pytest

from exchange_info.api import create_app
from exchange_info.models import PartnerUniversity
from exchange_info.ntu_completion import apply_completion, validate, SOURCE

BUNDLE = Path("src/exchange_info/official_data/ntu")


def load_partners(bundle=BUNDLE):
    return [PartnerUniversity.model_validate_json(r) for r in (bundle / "partners.jsonl").read_text().splitlines()]


def test_replay_is_idempotent_and_preserves_selection_and_workflows(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(BUNDLE, bundle)
    before = load_partners(bundle)
    protected = (bundle / "application_workflows.jsonl").read_bytes()
    first = apply_completion(bundle)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir() if p.is_file()}
    assert apply_completion(bundle) == first
    assert hashes == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir() if p.is_file()}
    assert (bundle / "application_workflows.jsonl").read_bytes() == protected
    for prior, after in zip(before, load_partners(bundle)):
        for field in ("eligibility", "quota", "application_deadline", "availability_status", "source_url", "country"):
            assert getattr(prior, field) == getattr(after, field)
    assert first == {"schools": 288, "reviewed_observations": 1485, "photo_additions": 19,
                     "location_additions": 16, "fully_verified_current_cycle_schools": 0}


@pytest.mark.parametrize("failure", ["identity", "country", "selection", "period", "page", "quote", "inventory", "photo_identity", "coordinate_assignment", "field_finality", "field_source", "field_roster"])
def test_invalid_batch_fails_before_writing_any_catalog_file(tmp_path, failure):
    snapshot = json.loads(SOURCE.read_text())
    entry = next(r for r in snapshot["schools"] if r["portal_id"] == "26")
    if failure == "identity":
        entry["school_name"] = "另一間大學"
    elif failure == "country":
        entry["country"] = "美國"
    elif failure == "selection":
        entry["observations"][0]["selection_rule_confirmed"] = True
    elif failure == "period":
        entry["observations"][0]["applicability_status"] = "implicitly_2027"
    elif failure == "page":
        entry["observations"][0]["pdf_page"] = 900
    elif failure == "quote":
        entry["observations"][0]["quote_source_id"] = "missing"
    elif failure == "inventory":
        snapshot["list_receipt"]["rows"][0]["quota"] = "3 名"
    elif failure == "photo_identity":
        next(r for r in snapshot["schools"] if r.get("photo"))["photo"]["country"] = "另一國"
    elif failure == "coordinate_assignment":
        next(r for r in snapshot["schools"] if r.get("location"))["location_review"]["assigned_exchange_campus_confirmed"] = True
    elif failure == "field_finality":
        next(r for r in snapshot["schools"] if r.get("field_review_conclusions"))["field_review_conclusions"][0]["full_current_cycle_requirement_verified"] = True
    elif failure == "field_source":
        next(r for r in snapshot["schools"] if r.get("field_review_conclusions"))["field_review_conclusions"][0]["sources"][0]["field_fitness_note_zh"] = ""
    else:
        snapshot["bounded_field_review"]["field_roster"].pop()
    bundle = tmp_path / "bundle"
    shutil.copytree(BUNDLE, bundle)
    source = tmp_path / "candidate.json"
    source.write_text(json.dumps(snapshot))
    before = {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    with pytest.raises(ValueError):
        apply_completion(bundle, source)
    assert before == {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}


def test_explicit_years_conflicts_and_pending_announcement_remain_distinct():
    snapshot = json.loads(SOURCE.read_text())
    rows = {r["portal_id"]: r for r in snapshot["schools"]}
    validate(snapshot, load_partners())
    ochanomizu = rows["26"]["observations"]
    assert any(r["applicability_status"] == "target_year_explicit" for r in ochanomizu)
    old_nhi = [r for r in ochanomizu if "2021" in r["scope"]]
    assert old_nhi and all(r["applicability_status"] == "older_year_reference" for r in old_nhi)
    assert all(r["applicability_status"] == "target_year_explicit" for r in ochanomizu if r not in old_nhi)
    uqam = [r for r in rows["1061"]["observations"] if r["field"] == "documents"]
    assert uqam[0]["applicability_status"] == "version_conflict" and "2025" in uqam[0]["text_zh"]
    assert any(r["applicability_status"] == "explicitly_pending_announcement" for r in rows["974"]["observations"])
    assert all(not r["selection_rule_confirmed"] for school in rows.values() for r in school["observations"])
    for row in rows.values():
        if row.get("photo"):
            assert row["photo_review"]["assigned_exchange_campus_confirmed"] is False
            assert row["photo"]["artist"] and row["photo"]["license_url"]


def test_all_288_schools_accept_offline_reference_assets_and_guarded_workflows(tmp_path, monkeypatch):
    import requests
    monkeypatch.setattr(requests.Session, "request", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Network in public read")))
    snapshot = json.loads(SOURCE.read_text())
    reviewed = {r["school_name"]: r for r in snapshot["schools"]}
    with TestClient(create_app(tmp_path)) as client:
        dashboard = client.get("/student-dashboard", params={"school": "NTU"}).json()
        partners = dashboard["partner_universities"]
        assert len(partners) == 288 and len({p["school_name"] for p in partners}) == 288
        for partner in partners:
            reference = reviewed[partner["school_name"]]
            assert partner["country"] == reference["country"]
            assert partner["quota"] in (None, "0 名") and partner["availability_status"] != "open"
            application_points = partner["student_summary_zh"]["application_steps"]
            # The public overview displays ten points. Every reference must
            # remain visible there with its scope and source, including late
            # cost/calendar paragraphs containing old years or conflicts.
            if reference["observations"]:
                assert len(application_points) <= 10
            visible_application = "\n\n".join(application_points[:10])
            for observation in reference["observations"]:
                assert observation["text_zh"] in partner["application_info"]
                assert observation["text_zh"] in visible_application
                assert observation["source_url"] in visible_application
                assert observation["scope"] in visible_application
            if reference.get("photo"):
                assert partner["image_status"] == "verified" and partner["image_url"]
            response = client.get("/destination-profile", params={"school": partner["school_name"], "home_school": "NTU"})
            assert response.status_code == 200, partner["school_name"]
            if reference["observations"]:
                guide = next(r for r in response.json()["student_guide_sections"] if r["key"] == "ntu-host-references-20261011")
                assert len(guide["points"]) == len(reference["observations"])
                assert all(r["source_url"] in guide["source_urls"] for r in reference["observations"])
            if reference.get("field_review_conclusions"):
                guide = next(r for r in response.json()["student_guide_sections"] if r["key"] == "ntu-field-conclusions-20261011")
                assert len(guide["points"]) == len(reference["field_review_conclusions"])
                for conclusion in reference["field_review_conclusions"]:
                    assert any(conclusion["note_zh"] in point for point in guide["points"])
                    assert all(source["url"] in guide["source_urls"] for source in conclusion["sources"])
            workflow = client.get("/application-workflow", params={"school": partner["school_name"], "home_school": "NTU", "academic_year": "116"})
            assert workflow.status_code == 200
            assert workflow.json()["published_at"] is None
            assert all(not s["deadline_reminder_eligible"] for s in workflow.json()["steps"])

"""Finite source closure cannot imply current eligibility or private policy."""
import hashlib
import json

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def load(name):
    return json.loads((BUNDLE / name).read_text())


def host(page):
    return next(r["host_fields"] for r in load("completion-reviewed-fields.json")["schools"] if r["ccu_page"] == page)


def test_closure_preserves_partial_extent_and_corrects_only_explicit_complete_flags():
    closure = load("completion-ninth-reading-closures.json")
    records = closure["records"]
    assert len(records) == len({r["source_id"] for r in records}) == 263
    assert sum(r["already_complete_extent"] for r in records) == 17
    assert sum(r["closure"] == "retained_scoped_read_and_closed_for_bounded_acceptance" for r in records) == 229
    assert all(r["source_url"] and r["content_hash"] and r["review_extent"] for r in records)
    assert all(not r["policy_verification_implied_by_closure"] for r in records)
    frozen = load("completion-eighth-reading-input.json")
    assert sum(not r.get("full_visible_read", False) for r in frozen) == 263
    progress = load("completion-ninth-convergence-acceptance.json")
    assert progress["scope_accepted"] and progress["ready_to_wait_for_integration"]
    assert not progress["all_public_research_exhausted"]


def test_source_quotes_pages_and_annual_scope_are_exact():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from review_ccu_public_round8 import visible
    fields = load("completion-ninth-field-input.json")
    assert len(fields) == 21
    for f in fields:
        r = load("completion_sources/" + f["source_id"] + ".receipt.json")
        assert r["tls_verify"] and r["http_status"] == 200 and not r.get("error")
        assert f["quote"] in visible(r, f["source_pages"])
        assert f["academic_year"]
    baseline = load("completion-ninth-baseline.json")
    assert baseline["prior_host_counts"]["missing"] == 604
    assert all(len(f["field_digest"]) == 64 for r in baseline["prior_fields"] for f in r["host_fields"].values())


def test_eduhk_calendar_and_exam_change_are_not_generic_2027_language_certification():
    fields = host(56)
    assert fields["academic_calendar"]["status"] == "verified_current"
    assert "05-03" in fields["academic_calendar"]["value"] and "05-04至17" in fields["academic_calendar"]["value"]
    assert fields["academic_calendar"]["evidence"][0]["source_pages"] == [2]
    assert fields["eligibility"]["status"] == fields["language"]["status"] == "needs_confirmation"
    assert "2026-01-21" in fields["language"]["value"] and "新版iBT4" in fields["language"]["value"]
    assert "12" in fields["course_restrictions"]["value"] and "15" in fields["course_restrictions"]["value"]
    assert fields["nomination_deadline"]["value"] is None
    assert fields["host_tuition"]["value"] is None


def test_old_chandigarh_fact_sheet_and_other_programmes_cannot_become_2027_rules():
    fields = host(75)
    for key in ["academic_calendar", "nomination_deadline", "housing", "host_tuition"]:
        assert fields[key]["status"] == "reference_only"
    assert "2021" in fields["academic_calendar"]["evidence"][0]["academic_year"]
    assert fields["application_deadline"]["status"] == "needs_confirmation"
    assert fields["eligibility"]["value"] is None and fields["course_restrictions"]["value"] is None
    notes = {r["source_id"]: r for r in load("completion-ninth-reading-input.json")}
    assert "outbound" in notes["p75-ninth-partner-programmes"]["review_note"]
    assert "2025" in host(113)["costs"]["evidence"][0]["academic_year"]
    assert host(113)["visa"]["status"] == "missing"  # Interactive options aren't a resolved personal answer.


def test_three_new_form_steps_have_explicit_gates_without_claiming_contents_read():
    for page in [59, 87, 103]:
        forms = host(page)["application_forms"]
        assert forms["status"] == "needs_confirmation"
        assert forms["research_classification"] == "personal_access_required"
        assert forms["access_requirement_evidence"]
        assert all(e["excerpt"] and e["source_url"] and e["content_hash"] for e in forms["access_requirement_evidence"])
    progress = load("completion-ninth-convergence-acceptance.json")
    assert progress["private_school_count"] == 10 and progress["private_field_count"] == 11
    assert host(103)["academic_calendar"]["status"] == "conflict"
    assert host(103)["exchange_duration"]["value"] is None
    assert "協議" in host(18)["insurance"]["value"]


def test_precise_inputs_and_assets_do_not_turn_unknown_into_official_nonpublication():
    inputs = load("completion-ninth-external-inputs.json")["host_fields"]
    assert len(inputs) == 1407 and sum(r["strict_missing"] for r in inputs) == 585
    assert all(r["minimum_required_input"] and r["school_name"] and r["field"] for r in inputs)
    assert sum(r["official_not_announced"] for r in inputs) == 1
    assets = load("completion-ninth-asset-and-gamma-closure.json")
    assert assets["new_network_requests"] == 0
    assert sum(len(r["asset_gaps"]) for r in assets["assets"]) == 8
    assert assets["gamma"]["denominator"] is None
    assert all(not r["official_exclusive_access_proven"] for r in assets["assets"])
    assert not assets["gamma"]["official_exclusive_access_proven"]


def test_bounded_receiving_evidence_preserves_all_home_closed_windows_and_original_profile_prefix():
    partners = fetch_ccu_partner_universities()
    assert len(partners) == 104
    assert all(p.application_window_status == "closed" for p in partners)
    assert sum(p.availability_status == "not_open" for p in partners) == 49
    assert hashlib.sha256(b"\n".join((BUNDLE / "destination_profiles.jsonl").read_bytes().splitlines()[:55]) + b"\n").hexdigest() == "1375f32052bcdeaedfe696073e7ada6d40f40bdebeba0dc1e7f82353e38b78e6"

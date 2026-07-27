from __future__ import annotations

import json

from exchange_info import storage


def test_bundled_ntpu_catalog_is_complete(monkeypatch, tmp_path) -> None:
    # A caller-supplied data directory stays isolated unless it is the configured
    # default directory. This mirrors a fresh Git clone that has no local refresh.
    assert storage.load_partner_research(tmp_path) == []
    assert storage.load_application_workflows(tmp_path) == []
    assert storage.load_destination_profiles(tmp_path) == []

    monkeypatch.setattr(storage, "DEFAULT_DATA_DIR", tmp_path)

    research = storage.load_partner_research(tmp_path)
    workflows = storage.load_application_workflows(tmp_path)
    destinations = storage.load_destination_profiles(tmp_path)

    assert len(research) == 203
    assert len(workflows) == 203
    assert len(destinations) == 203
    assert all(row.verification_status == "official_verified" for row in research)
    assert all(row.official_website for row in research)
    assert all(
        row.housing_summary
        and row.cost_summary
        and row.transport_summary
        and row.campus_life_summary
        for row in destinations
    )


def test_bundled_ntpu_completeness_report_has_all_required_fields() -> None:
    report_path = storage.BUNDLED_NTPU_DIR / "catalog-completeness.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["partner_count"] == 203
    assert report["open_count"] == 155
    assert report["agreement_only_count"] == 48
    assert report["verified_image_count"] == 203
    assert report["workflow_count"] == 203
    assert report["destination_count"] == 203
    assert set(report["fields"].values()) == {203}

"""Keep full source payloads while avoiding unnecessary catalogue allocations."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.models import PartnerResearchRecord, UniversityApplicationWorkflow
from exchange_info.partner_research import apply_partner_research
from exchange_info.workflow_structuring import structure_application_workflow


def test_read_only_partner_overlay_preserves_every_nested_source_field():
    partners = fetch_ccu_partner_universities()
    before = [row.model_dump(mode="json") for row in partners]
    record = PartnerResearchRecord(
        home_university="國立中正大學", school_name=partners[0].school_name,
        official_website="https://example.edu/updated", verification_status="official_verified",
    )
    independent = apply_partner_research(partners, [record], home_university="國立中正大學")
    readonly = apply_partner_research(partners, [record], home_university="國立中正大學", copy_nested=False)
    assert [row.model_dump(mode="json") for row in readonly] == [row.model_dump(mode="json") for row in independent]
    assert readonly[0] is not partners[0]
    assert readonly[0].field_evidence is partners[0].field_evidence
    independent[0].field_evidence.clear()
    readonly[0].website = "https://example.edu/request-only"
    assert [row.model_dump(mode="json") for row in partners] == before


def test_scoped_destination_load_keeps_full_rows_and_local_override(tmp_path, monkeypatch):
    all_rows = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    replacement = all_rows[0].model_copy(update={"coverage_note": "Local reviewed override"})
    storage.save_destination_profiles([replacement], tmp_path)
    baseline = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True)
    read = storage.read_jsonl
    paths = []

    def track(path, model, **kwargs):
        paths.append(path)
        return read(path, model, **kwargs)

    monkeypatch.setattr(storage, "read_jsonl", track)
    for home in {row.home_university for row in baseline}:
        paths.clear()
        selected = storage.load_destination_profiles(tmp_path, include_bundled_baseline=True, home_university=home)
        expected = [row for row in baseline if row.home_university == home]
        assert [row.model_dump(mode="json") for row in selected] == [row.model_dump(mode="json") for row in expected]
        bundle_paths = [path for path in paths if "official_data" in path.parts and path.name == "destination_profiles.jsonl"]
        assert len(bundle_paths) == 1, "A school read must not parse unrelated schools' source graphs"


def test_streamed_workflow_structuring_matches_original_payloads():
    for path in storage._bundled_workflow_paths():
        expected = [structure_application_workflow(row) for row in storage.read_jsonl(path, UniversityApplicationWorkflow)]
        actual = storage.read_jsonl(path, UniversityApplicationWorkflow, transform=structure_application_workflow)
        assert [row.model_dump(mode="json") for row in actual] == [row.model_dump(mode="json") for row in expected]


def test_catalogue_backpressure_keeps_health_available_and_releases_slots(tmp_path):
    from exchange_info.api import create_app

    app = create_app(tmp_path)
    release = threading.Event()
    two_active = threading.Event()
    active = 0
    peak = 0

    app.router.routes[:] = [route for route in app.router.routes if getattr(route, "path", None) != "/coverage"]

    @app.get("/coverage")
    async def blocked_catalogue():
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        if active == 2:
            two_active.set()
        try:
            while not release.is_set():
                await asyncio.sleep(.01)
            return {"complete": True}
        finally:
            active -= 1

    with TestClient(app) as client, ThreadPoolExecutor(max_workers=4) as pool:
        responses = [pool.submit(client.get, "/coverage") for _ in range(3)]
        try:
            assert two_active.wait(5)
            assert pool.submit(client.get, "/health").result(timeout=5).status_code == 200
            assert active == 2 and peak == 2
        finally:
            release.set()
        assert all(future.result(timeout=5).json() == {"complete": True} for future in responses)
        assert client.get("/coverage").status_code == 200
        assert active == 0 and peak == 2

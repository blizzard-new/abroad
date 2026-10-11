"""Current governance workbench with explicitly synthetic, isolated candidates."""
from datetime import datetime, timezone

import requests
from playwright.sync_api import expect

from exchange_info.content_governance import (LocalContentGovernanceStore, stage_workflow_refresh,
    workflow_review_source_urls, workflow_review_rule_keys)
from exchange_info.models import (UniversityApplicationWorkflow, ApplicationStep,
    ApplicationWorkflowSource, DestinationProfile, SourceReference, PartnerUniversity)
from exchange_info.destination_profile_review import REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS
from exchange_info.storage import upsert_destination_profile, load_destination_profiles
from .test_web_next_phase import _auth_headers, _open_content_review_workbench


def test_current_admin_workbench_source_attestations_publish_and_destination_rollback(page, live_server, monkeypatch):
    a = live_server.register("synthetic-tku-governance-a@example.com", "Synthetic governance A")
    b = live_server.register("synthetic-tku-governance-b@example.com", "Synthetic governance B")
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", f"{a['profile']['email']},{b['profile']['email']}")
    headers_a, headers_b = _auth_headers(a), _auth_headers(b)
    base = live_server.base_url
    store = LocalContentGovernanceStore(live_server.data_dir)
    school = "Synthetic TKU governance host"
    # The public catalogue intentionally excludes profiles for unknown partners.
    # Add this explicitly synthetic partner only to this server's fixture.
    import exchange_info.api as api_module
    original_partners = api_module.fetch_tku_partner_universities
    monkeypatch.setattr(api_module, "fetch_tku_partner_universities", lambda **kwargs:
        [*original_partners(**kwargs), PartnerUniversity(program_type="exchange", school_name=school,
            colleges="Synthetic college", degree_levels="大學部", source_url="https://synthetic.edu/exchange")])
    workflow = UniversityApplicationWorkflow(home_university="淡江大學", school_name=school,
        academic_year="117", application_round="Synthetic round", applicability_status="verified",
        coverage_status="official_verified", last_checked=datetime(2026,10,9,tzinfo=timezone.utc),
        sources=[ApplicationWorkflowSource(title="Synthetic official source", source_url="https://synthetic.edu/exchange",
            role="home_university", authority="home_official_notice", effective_academic_year="117",
            application_round="Synthetic round", checked_at=datetime(2026,10,9,tzinfo=timezone.utc))],
        steps=[ApplicationStep(rule_id="synthetic-rule", order=1, phase="Synthetic phase", title="Synthetic requirement",
            responsible_party="Synthetic student", summary="Synthetic bounded rule",
            source_urls=["https://synthetic.edu/exchange"], support_status="verified")])
    revision = stage_workflow_refresh(store, workflow).revision
    profile = DestinationProfile(home_university="淡江大學", school_name=school,
        coverage_status="official_partial", coverage_note="Synthetic scope boundaries; no real official verification claim",
        cost_summary="Synthetic bounded cost", sources=[SourceReference(title="Synthetic official source", source_url="https://synthetic.edu/exchange")],
        last_checked=datetime(2026,10,9,tzinfo=timezone.utc))
    upsert_destination_profile(profile, live_server.data_dir)

    _open_content_review_workbench(page, live_server, a['profile']['email'], a)
    expect(page.locator("#reviewer-email")).to_have_text(a['profile']['email'])
    page.goto(f"{base}/admin/content-review?review_status=pending_review&workflow_revision={revision.id}")
    card = page.locator(f'[data-revision-id="{revision.id}"]')
    expect(card).to_be_visible(timeout=30000)
    expect(card).to_contain_text(school)
    expect(card.locator('[data-review-action="publish"]')).to_be_disabled()

    def approve(headers, row):
        response = requests.post(f"{base}/admin/application-workflow-revisions/{row['id']}/approve", headers=headers,
            json={"expected_content_hash":row['content_hash'], "reviewed_source_urls":workflow_review_source_urls(workflow),
                "reviewed_rule_keys":workflow_review_rule_keys(workflow), "note":"Synthetic independent review of every source and rule"}, timeout=30)
        assert response.status_code == 200, response.text
        return response.json()
    payload = revision.model_dump(mode="json")
    approve(headers_a, payload)
    one = requests.post(f"{base}/admin/application-workflow-revisions/{revision.id}/publish", headers=headers_a,
        json={"note":"Synthetic explicit publication"}, timeout=30)
    assert one.status_code == 409
    approved = approve(headers_b, payload)
    assert len(approved['review_approvals']) == 2
    edited = requests.patch(f"{base}/admin/application-workflow-revisions/{revision.id}/applicability", headers=headers_a,
        json={"expected_content_hash":revision.content_hash,"academic_year":"117","application_round":"Synthetic round",
            "source_updates":[{"source_url":"https://synthetic.edu/exchange","effective_academic_year":"117",
                "application_round":"Synthetic round","title":"Synthetic revised source title"}],
            "note":"Synthetic source change requires two new independent attestations"}, timeout=30)
    assert edited.status_code == 200, edited.text
    updated = edited.json()
    assert updated['review_approvals'] == []
    assert len(updated['edit_history'][-1]['invalidated_review_approvals']) == 2
    stale = requests.post(f"{base}/admin/application-workflow-revisions/{revision.id}/approve", headers=headers_b,
        json={"expected_content_hash":revision.content_hash,"reviewed_source_urls":workflow_review_source_urls(workflow),
            "reviewed_rule_keys":workflow_review_rule_keys(workflow),"note":"Synthetic stale evidence must be rejected"}, timeout=30)
    assert stale.status_code == 409
    approve(headers_a, updated)
    approve(headers_b, updated)
    published = requests.post(f"{base}/admin/application-workflow-revisions/{revision.id}/publish", headers=headers_a,
        json={"note":"Synthetic explicit publication"}, timeout=30)
    assert published.status_code == 200, published.text
    visible_workflow = next(row for row in store.load_published_workflows() if row.school_name == school)
    assert visible_workflow.version == published.json()['version']
    assert visible_workflow.sources[0].title == 'Synthetic revised source title'
    history = requests.get(f"{base}/admin/application-workflow-publications", headers=headers_a, timeout=30)
    assert history.status_code == 200 and any(row['school_name']==school for row in history.json()['items'])

    def queue():
        result = requests.get(f"{base}/admin/destination-profile-review-queue", headers=headers_a,
            params={"home_university":"淡江大學"}, timeout=30)
        assert result.status_code == 200
        return result.json()
    def attest(headers):
        current = queue()
        row = next(item for item in current['items'] if item['school_name']==school)
        result = requests.post(f"{base}/admin/destination-profile-reviews", headers=headers,
            json={"home_university":"淡江大學","school_name":school,"expected_snapshot":current['snapshot_fingerprint'],
                "expected_profile_content_hash":row['profile_content_hash'],"decision":"approve",
                "reviewed_source_urls":[source.source_url for source in profile.sources],
                "reviewed_section_keys":[section.key for section in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS],
                "note":"Synthetic independent destination source and section attestation"}, timeout=30)
        assert result.status_code == 200, result.text
    def promotion_request():
        current = queue()
        row = next(item for item in current['items'] if item['school_name']==school)
        return {"home_university":"淡江大學","school_name":school,"expected_snapshot":current['snapshot_fingerprint'],
            "expected_profile_content_hash":row['profile_content_hash'],"note":"Synthetic explicit destination promotion"}
    attest(headers_a)
    denied = requests.post(f"{base}/admin/destination-profile-promotions", headers=headers_a, json=promotion_request(), timeout=30)
    assert denied.status_code == 409
    attest(headers_b)
    request = promotion_request()
    promoted = requests.post(f"{base}/admin/destination-profile-promotions", headers=headers_a, json=request, timeout=30)
    assert promoted.status_code == 200, promoted.text
    replay = requests.post(f"{base}/admin/destination-profile-promotions", headers=headers_a, json=request, timeout=30)
    assert replay.status_code == 200 and replay.json()['id']==promoted.json()['id']
    public = requests.get(f"{base}/destination-profiles", params={"home_school":"淡江大學"}, timeout=30).json()
    assert next(row for row in public if row['school_name']==school)['coverage_status'] == 'official_verified'
    raw = next(row for row in load_destination_profiles(live_server.data_dir) if row.school_name==school)
    assert raw.coverage_status == 'official_partial' and raw.cost_summary == profile.cost_summary
    history = requests.get(f"{base}/admin/destination-profile-publications", headers=headers_a,
        params={"home_university":"淡江大學"}, timeout=30).json()
    item = next(row for row in history['items'] if row['school_name']==school)
    rollback = {"home_university":"淡江大學","school_name":school,"expected_active_promotion_event_id":item['active_promotion_event_id'],
        "expected_latest_publication_event_id":item['latest_event_id'],"expected_public_profile_content_hash":item['current_public_profile_content_hash'],
        "note":"Synthetic explicit audited destination restoration"}
    restored = requests.post(f"{base}/admin/destination-profile-rollbacks", headers=headers_b, json=rollback, timeout=30)
    assert restored.status_code == 200, restored.text
    repeated = requests.post(f"{base}/admin/destination-profile-rollbacks", headers=headers_b, json=rollback, timeout=30)
    assert repeated.status_code == 200 and repeated.json()['id']==restored.json()['id']
    public = requests.get(f"{base}/destination-profiles", params={"home_school":"淡江大學"}, timeout=30).json()
    result = next(row for row in public if row['school_name']==school)
    assert result['coverage_status']=='official_partial' and result['cost_summary']==profile.cost_summary
    page.goto(f"{base}/admin/content-review?destination_home={requests.utils.quote('淡江大學')}")
    expect(page.locator('#destination-publication-history-summary')).to_contain_text('淡江大學',timeout=30000)
    expect(page.locator('#destination-publication-history-summary')).to_contain_text('1 筆生活情報曾執行升級',timeout=30000)
    expect(page.locator('#destination-publication-history-summary')).to_contain_text('1 筆復原事件')
    expect(page.locator('.destination-publication-card').filter(has_text=school)).to_contain_text('復原',timeout=30000)

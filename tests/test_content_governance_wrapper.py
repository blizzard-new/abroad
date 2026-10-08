"""Source-visible recovery of the only test preserved by the historical wrapper.

The former loader depended on an untracked Python 3.12/pytest9.1.1 bytecode file.
That bytecode and its source are absent from main and every available branch.
Unknown tests exported by that file cannot be recovered or claimed as covered.
This retains the explicit RPC regression visible in the tracked wrapper.
"""
from datetime import datetime, timezone

from exchange_info.content_governance import SupabaseContentGovernanceStore, workflow_content_hash
from exchange_info.models import (
    ApplicationStep, ApplicationWorkflowRevision, ApplicationWorkflowReviewStatus,
    UniversityApplicationWorkflow,
)


def test_supabase_store_writes_revision_and_published_payload_through_backend():
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return []

    def fake_request(method, url, **kwargs):
        calls.append(dict(method=method, url=url, **kwargs))
        return FakeResponse()

    workflow = UniversityApplicationWorkflow(
        school_name='Synthetic RPC school', country='Japan', workflow_id='workflow-key',
        steps=[ApplicationStep(order=1, phase='校內準備', title='Supabase Test',
                               responsible_party='學生', summary='Synthetic test only')],
        last_checked=datetime(2026, 10, 8, tzinfo=timezone.utc),
        review_status=ApplicationWorkflowReviewStatus.PENDING_REVIEW,
    )
    revision = ApplicationWorkflowRevision(workflow_key='workflow-key', version=1,
        content_hash=workflow_content_hash(workflow), workflow=workflow)
    store = SupabaseContentGovernanceStore('https://synthetic.invalid', 'synthetic-test-key', request_func=fake_request)
    store.save_revision(revision)
    store.publish_workflow(workflow.model_copy(update={
        'review_status': ApplicationWorkflowReviewStatus.PUBLISHED,
        'published_at': datetime(2026, 10, 8, tzinfo=timezone.utc),
    }), revision.id, workflow_key='stable-workflow-key')

    assert [call['url'].split('/rest/v1/')[-1] for call in calls] == [
        'rpc/exchange_commit_application_workflow_revision',
        'rpc/exchange_commit_application_workflow_publication',
    ]
    assert calls[0]['json']['p_workflow_payload']['steps'][0]['title'] == 'Supabase Test'
    assert calls[1]['json']['p_published_payload']['review_status'] == 'published'
    assert calls[1]['json']['p_workflow_key'] == 'stable-workflow-key'

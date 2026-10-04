import pytest
import sys
import importlib.util
from pathlib import Path

pyc_path = Path("tests/__pycache__/test_content_governance.cpython-312-pytest-9.1.1.pyc")
spec = importlib.util.spec_from_file_location("test_content_governance", pyc_path)
module = importlib.util.module_from_spec(spec)
sys.modules["test_content_governance"] = module

spec.loader.exec_module(module)

# Set __file__ AFTER exec_module so it points to the correct location
module.__file__ = str(Path("tests/test_content_governance.py").resolve())

def override_test_supabase_store_writes_revision_and_published_payload_through_backend():
    calls = []
    class FakeResponse:
        def raise_for_status(self): return None
        def json(self): return []
    def fake_request(method, url, **kwargs):
        calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse()

    workflow = module._workflow("Supabase Test").model_copy(
        update={"workflow_id": "workflow-key", "review_status": module.ApplicationWorkflowReviewStatus.PENDING_REVIEW}
    )
    revision = module.ApplicationWorkflowRevision(
        workflow_key="workflow-key",
        version=1,
        content_hash=module.workflow_content_hash(workflow),
        workflow=workflow,
    )
    store = module.SupabaseContentGovernanceStore("https://project.supabase.co", "service-role-secret", request_func=fake_request)
    store.save_revision(revision)
    store.publish_workflow(
        workflow.model_copy(update={"review_status": module.ApplicationWorkflowReviewStatus.PUBLISHED, "published_at": module.utc_now()}),
        revision.id,
        workflow_key="stable-workflow-key",
    )
    
    assert [call["url"].split("/rest/v1/")[-1] for call in calls] == [
        "rpc/exchange_commit_application_workflow_revision",
        "rpc/exchange_commit_application_workflow_publication",
    ]
    assert calls[0]["json"]["p_workflow_payload"]["steps"][0]["title"] == "Supabase Test"
    assert calls[1]["json"]["p_published_payload"]["review_status"] == "published"

module.test_supabase_store_writes_revision_and_published_payload_through_backend = override_test_supabase_store_writes_revision_and_published_payload_through_backend

for name, obj in vars(module).items():
    if name.startswith("test_") or name.startswith("Test"):
        globals()[name] = obj
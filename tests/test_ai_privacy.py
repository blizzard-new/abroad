import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from exchange_info.api import create_app
from exchange_info.document_checker import check_document
from exchange_info.redaction import redact_pii

def test_pii_redaction_masks_taiwan_ids():
    text = "My ID is A123456789 and phone is 0912-345-678."
    redacted = redact_pii(text)
    assert "A123456789" not in redacted
    assert "[REDACTED_ID]" in redacted
    assert "0912-345-678" not in redacted
    assert "[REDACTED_PHONE]" in redacted

def test_pii_redaction_masks_emails_and_student_ids():
    text = "Email test@example.com and student ID 410912345."
    redacted = redact_pii(text)
    assert "test@example.com" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "410912345" not in redacted
    assert "[REDACTED_STUDENT_ID]" in redacted

def test_ai_rewrite_requires_consent(tmp_path: Path):
    app = create_app(tmp_path)
    client = TestClient(app)
    
    response = client.post("/ai/rewrite-document", json={
        "text": "Hello world this is a test string over 20 characters",
        "action": "grammar",
        "document_type": "study_plan",
        "ai_consent_granted": False
    })
    
    # Should be 422 if consent not granted
    assert response.status_code == 422
    assert "AI consent required" in response.text

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI


OPENAPI_CONTRACT_VERSION = "2026-10-13.1"

_CONTRACT_BOUNDARIES = {
    "public_read_without_login": True,
    "account_routes_require_bearer_session": True,
    "university_board_reads_require_verified_email": True,
    "university_board_writes_require_verified_email": True,
    "university_board_access_requires_matching_school": False,
    "personal_document_storage_requires_separate_consent": True,
    "workflow_issue_reports_require_verified_student": True,
    "workflow_issue_report_review_cannot_publish": True,
    "platform_submits_applications": False,
    "ai_features": "paused",
}

_COMMON_ERROR_STATUS = {
    "authentication_required": 401,
    "permission_denied": 403,
    "resource_not_found": 404,
    "validation_failed": 422,
    "rate_limited": 429,
}


def apply_openapi_contract_metadata(schema: dict[str, Any]) -> dict[str, Any]:
    """Add stable product boundaries that Web and future Flutter clients share."""

    schema["x-contract-version"] = OPENAPI_CONTRACT_VERSION
    schema["x-product-boundaries"] = dict(_CONTRACT_BOUNDARIES)
    schema["x-common-error-status"] = dict(_COMMON_ERROR_STATUS)
    # Document errors already raised by these handlers; never invent a route or
    # a retry capability that its runtime has not implemented.
    errors = {
        ('/calendar-sync', 'get'): (401, 403),
        ('/calendar-sync/enable', 'post'): (401, 403),
        ('/calendar-sync/events', 'put'): (401, 403),
        ('/application-center/manifest', 'post'): (401, 403),
        ('/application-center/pdf', 'post'): (401, 403),
        ('/application-center/docx', 'post'): (401, 403),
        ('/document-check', 'post'): (401, 403, 422, 503),
        ('/ai/review-document', 'post'): (401, 403, 422, 503),
        ('/ai/chat', 'post'): (503,),
        ('/ai/rewrite-document', 'post'): (503,),
        ('/community/feed', 'get'): (401, 403),
        ('/community/posts', 'get'): (401, 403),
        ('/community/posts/{post_id}', 'get'): (401, 403),
        ('/community/posts/{post_id}/comments', 'get'): (401, 403),
        ('/community/posts', 'post'): (401, 403, 409),
        ('/community/posts/{post_id}/comments', 'post'): (401, 403, 409),
        ('/community/conversations', 'post'): (401, 403, 409, 503),
        ('/community/conversations/{conversation_id}/accept', 'post'): (401, 403, 404, 409, 503),
        ('/community/conversations/{conversation_id}/messages', 'post'): (401, 403, 404, 409, 503),
        ('/community/blocks', 'post'): (401, 403, 404, 409, 503),
    }
    for (path, method), statuses in errors.items():
        operation = schema.get('paths', {}).get(path, {}).get(method)
        if operation:
            for status in statuses:
                operation.setdefault('responses', {}).setdefault(str(status), {
                    'description': 'Existing runtime error; access also depends on release mode and request validation.'})
    return schema


def install_openapi_contract(app: FastAPI) -> None:
    """Version the live schema without changing FastAPI route generation."""

    generated_openapi = app.openapi

    def versioned_openapi() -> dict[str, Any]:
        schema = generated_openapi()
        return apply_openapi_contract_metadata(schema)

    app.openapi = versioned_openapi


def serialize_openapi_contract(schema: Mapping[str, Any]) -> bytes:
    """Return a deterministic UTF-8 representation suitable for a snapshot."""

    return (
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

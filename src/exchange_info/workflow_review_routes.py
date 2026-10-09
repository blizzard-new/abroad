"""Authenticated workflow review actions using the existing dual-review gate."""

from threading import RLock

from fastapi import FastAPI, HTTPException, Query, Request, Response

from .content_governance import (
    approve_workflow_revision,
    compare_workflow_revision,
    publish_workflow_revision,
    reject_workflow_revision,
)
from .models import (
    ApplicationWorkflowApprovalRequest,
    ApplicationWorkflowComparison,
    ApplicationWorkflowReviewRequest,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowRevision,
    UniversityApplicationWorkflow,
)


def register_workflow_review_routes(app: FastAPI, authenticated_admin) -> None:
    # All workflow, source and destination commands share this app's lock.
    review_lock = getattr(app.state, "content_review_lock", None) or RLock()
    app.state.content_review_lock = review_lock
    store = app.state.content_governance_store

    def authorize(request: Request, response: Response):
        account, _ = authenticated_admin(request)
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        return account

    def revision_by_id(revision_id: str):
        rows = store.list_revisions()
        row = next((item for item in rows if item.id == revision_id), None)
        if row is None:
            raise HTTPException(status_code=404, detail="找不到指定的申請流程版本。")
        return rows, row

    def conflict(error: Exception):
        status = 404 if isinstance(error, LookupError) else 409
        raise HTTPException(status_code=status, detail=str(error)) from error

    @app.get("/admin/application-workflow-revisions", response_model=list[ApplicationWorkflowRevision])
    def revisions(request: Request, response: Response,
                  status: ApplicationWorkflowReviewStatus | None = Query(None)):
        authorize(request, response)
        rows = store.list_revisions()
        return [row for row in rows if status is None or row.status == status]

    @app.get("/admin/application-workflow-revisions/{revision_id}/comparison",
             response_model=ApplicationWorkflowComparison)
    def comparison(revision_id: str, request: Request, response: Response):
        authorize(request, response)
        rows, row = revision_by_id(revision_id)
        return compare_workflow_revision(rows, row)

    @app.post("/admin/application-workflow-revisions/{revision_id}/approve",
              response_model=ApplicationWorkflowRevision)
    def approve(revision_id: str, payload: ApplicationWorkflowApprovalRequest,
                request: Request, response: Response):
        account = authorize(request, response)
        with review_lock:
            try:
                return approve_workflow_revision(
                    store, revision_id, reviewer_id=account.id,
                    note=payload.note, expected_content_hash=payload.expected_content_hash,
                    reviewed_source_urls=payload.reviewed_source_urls,
                    reviewed_rule_keys=payload.reviewed_rule_keys,
                )
            except (LookupError, ValueError) as error:
                conflict(error)

    @app.post("/admin/application-workflow-revisions/{revision_id}/publish",
              response_model=UniversityApplicationWorkflow)
    def publish(revision_id: str, payload: ApplicationWorkflowReviewRequest,
                request: Request, response: Response):
        account = authorize(request, response)
        with review_lock:
            _, current = revision_by_id(revision_id)
            if current.status != ApplicationWorkflowReviewStatus.PENDING_REVIEW:
                raise HTTPException(status_code=409, detail="只有待審版本可以正式發布；已發布請求不會重複寫入。")
            try:
                published = publish_workflow_revision(
                    store, revision_id, reviewer_id=account.id, note=payload.note,
                )
            except (LookupError, ValueError) as error:
                conflict(error)
            # In-app notifications are created only after successful publication.
            # The registered service has no email sender and performs no delivery.
            app.state.notification_service.refresh_content_updates()
            return published

    @app.post("/admin/application-workflow-revisions/{revision_id}/reject",
              response_model=ApplicationWorkflowRevision)
    def reject(revision_id: str, payload: ApplicationWorkflowReviewRequest,
               request: Request, response: Response):
        account = authorize(request, response)
        with review_lock:
            try:
                return reject_workflow_revision(
                    store, revision_id, reviewer_id=account.id, note=payload.note,
                )
            except (LookupError, ValueError) as error:
                conflict(error)

"""Private notification center, backed by the existing reminder/revision service."""
from fastapi import FastAPI, HTTPException, Query, Request, Response

from .models import AccountNotification, AccountNotificationChanges, ApplicationWorkflowReviewStatus, NotificationCenterEnvelope, NotificationRunResult, utc_now
from .change_impact import affected_task_impacts
from .notifications import NotificationService, account_has_affected_plan, workflow_action_url


def register_notification_routes(
    app: FastAPI,
    authenticated_account,
    authenticated_admin,
    *,
    catalogue_source_provider=None,
) -> None:
    app.state.notification_service = NotificationService(
        app.state.account_repository, content_store=app.state.content_governance_store,
    )

    def private(response: Response) -> None:
        response.headers['Cache-Control'] = 'private, no-store, max-age=0'
        response.headers['X-Content-Type-Options'] = 'nosniff'

    def center(account_id: str, limit: int = 50) -> NotificationCenterEnvelope:
        rows=app.state.account_repository.list_notifications(account_id,limit=1000)
        return NotificationCenterEnvelope(items=rows[:limit],unread_count=sum(row.read_at is None for row in rows))

    @app.get('/account/notifications',response_model=NotificationCenterEnvelope)
    def notifications(request: Request,response: Response,limit: int=Query(50,ge=1,le=100)):
        account,_=authenticated_account(request)
        private(response)
        # Generate only this account's reminders; no email dispatch occurs on a read.
        app.state.notification_service.refresh_account(account)
        app.state.notification_service.refresh_content_updates(accounts=[account])
        if catalogue_source_provider is not None:
            app.state.notification_service.refresh_catalogue_source(
                account, catalogue_source_provider()
            )
        return center(account.id,limit)

    @app.patch('/account/notifications/read-all',response_model=NotificationCenterEnvelope)
    def read_all(request: Request,response: Response):
        account,_=authenticated_account(request)
        private(response)
        app.state.account_repository.mark_all_notifications_read(account.id,utc_now())
        return center(account.id)

    @app.patch('/account/notifications/{notification_id}/read',response_model=AccountNotification)
    def read(notification_id: str,request: Request,response: Response):
        account,_=authenticated_account(request)
        private(response)
        row=app.state.account_repository.find_notification_by_id(account.id,notification_id)
        if row is None or row.deleted_at is not None:
            raise HTTPException(status_code=404,detail='找不到這則通知。')
        if row.read_at is not None:
            return row
        marked=app.state.account_repository.mark_notification_read(account.id,notification_id,utc_now())
        if marked is None:
            raise HTTPException(status_code=404,detail='找不到這則通知。')
        return marked

    @app.delete('/account/notifications',response_model=NotificationCenterEnvelope)
    def delete_all(request: Request,response: Response):
        account,_=authenticated_account(request)
        private(response)
        app.state.account_repository.delete_all_notifications(account.id,utc_now())
        return center(account.id)

    @app.delete('/account/notifications/{notification_id}',status_code=204)
    def delete(notification_id: str,request: Request,response: Response):
        account,_=authenticated_account(request)
        private(response)
        deleted=app.state.account_repository.delete_notification(
            account.id,notification_id,utc_now()
        )
        if deleted is None:
            raise HTTPException(status_code=404,detail='找不到這則通知。')
        return Response(status_code=204,headers=dict(response.headers))

    @app.post('/admin/notifications/run-due',response_model=NotificationRunResult)
    def run_due(request: Request,response: Response):
        authenticated_admin(request)
        private(response)
        # No sender is configured here. Delivery requires a separately configured service.
        return app.state.notification_service.run_due()

    @app.get('/account/notifications/{notification_id}/changes', response_model=AccountNotificationChanges)
    def changes(notification_id: str, request: Request, response: Response):
        from .content_governance import compare_workflow_revision, _step_identity

        account, _ = authenticated_account(request)
        private(response)
        notification = app.state.account_repository.find_notification_by_id(account.id, notification_id)
        if notification is None or notification.deleted_at is not None or notification.kind != 'content_update':
            raise HTTPException(status_code=404, detail='找不到這則規定更新通知。')
        revision_id = notification.dedupe_key.removeprefix('content-update:')
        rows = app.state.content_governance_store.list_revisions()
        revision = next((row for row in rows if row.id == revision_id), None)
        if revision is None or revision.status not in {
            ApplicationWorkflowReviewStatus.PUBLISHED, ApplicationWorkflowReviewStatus.SUPERSEDED,
        }:
            raise HTTPException(status_code=404, detail='這則通知的已發布來源版本目前無法取得。')
        comparison = compare_workflow_revision(rows, revision)
        matches = account_has_affected_plan(account, revision.workflow, None)
        versions = [revision.workflow, comparison.base_workflow]
        visible_keys = {
            _step_identity(step) for workflow in versions if workflow is not None
            for step in workflow.steps
            if account_has_affected_plan(account, workflow, [step.scope])
        }
        return AccountNotificationChanges(
            revision_id=revision.id, home_university=revision.workflow.home_university,
            school_name=revision.workflow.school_name, academic_year=revision.workflow.academic_year,
            application_round=revision.workflow.application_round,
            from_version=revision.base_version, to_version=revision.version,
            has_base=comparison.has_base, matches_current_plan=matches,
            action_url=workflow_action_url(revision.workflow),
            workflow_changes=comparison.workflow_changes if matches else [],
            step_changes=[row for row in comparison.step_changes if row.step_key in visible_keys] if matches else [],
            source_changes=comparison.source_changes if matches else [],
            affected_tasks=(
                affected_task_impacts(account, comparison, revision.workflow, visible_keys)
                if matches else []
            ),
        )

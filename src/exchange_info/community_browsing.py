"""Public discussion browsing, separate from authenticated publication commands."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import re
from collections import Counter
from datetime import datetime
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request, Response

from .community_repositories import (
    CommunityIdentityMutationRequest, CommunityIdentityMutationStatus,
    CommunityRepositoryError, PublicCommunityPublicationRequest,
    PublicCommunityPublicationStatus, PublicCommunityResourceType,
    PublicCommunityDeleteRequest, PublicCommunityDeleteStatus,
    PublicCommunityModerationRequest, PublicCommunityModerationStatus, reaction_summary,
    CommunityReportMutationRequest, CommunityReportReviewMutationRequest, PrivateCommunityMutationStatus,
)
from .models import (AnonymousIdentity, ModerationStatus, utc_now, CommunityReactionUpdate,
                     CommunityModerationRequest, CommunitySuspensionRequest, CommunityReportReviewRequest, CommunityBookmarkUpdate)
from .repositories import (CommunitySuspensionMutationRequest, CommunitySuspensionMutationStatus,
                           AccountRepositoryError)
from .access_control import is_platform_admin


def install_community_browsing(app: FastAPI, repository, authenticated_account,
                               authenticated_admin, account_repository, anonymous_identity):
    cursor_secret = secrets.token_bytes(32)

    def read(method):
        try:
            return method()
        except CommunityRepositoryError as error:
            raise HTTPException(503, "討論暫時無法載入，請稍後重試。") from error

    def public(row):
        return row.model_dump(mode="json", exclude={"author_id", "viewer_can_delete"})

    def approved_posts():
        return [row for row in read(repository.list_posts) if row.status == ModerationStatus.APPROVED]

    def approved_comments():
        rows = read(repository.list_comments)
        roots = {row.id for row in rows if not row.parent_id and row.status == ModerationStatus.APPROVED}
        return [row for row in rows if row.status == ModerationStatus.APPROVED and not row.deleted
                and (not row.parent_id or row.parent_id in roots)]

    def viewer(request):
        if request.headers.get("Authorization") or request.cookies.get("exchange_guide_session"):
            return authenticated_account(request)[0]
        return None

    def enriched(row, account, identities, reactions, resource_type):
        return {**public(row), "viewer_can_delete": bool(account and not getattr(row, "deleted", False)
                and any(identity.id == row.author_id and identity.account_id == account.id for identity in identities)),
                "reactions": reaction_summary(reactions, resource_type, row.id, account.id if account else None)}

    def post_for(post_id):
        post = next((row for row in approved_posts() if row.id == post_id), None)
        if post is None:
            raise HTTPException(404, "文章已移除或尚未公開。")
        return post

    def page(rows, *, scope, sort, limit, cursor):
        snapshot = utc_now()
        anchor = None
        if cursor:
            try:
                encoded, signature = cursor.split(".")
                raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
                expected = hmac.new(cursor_secret, raw, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected, signature):
                    raise ValueError("signature")
                payload = json.loads(raw)
                if payload["scope"] != scope or payload["sort"] != sort:
                    raise ValueError("scope")
                snapshot = datetime.fromisoformat(payload["snapshot"])
                anchor = (datetime.fromisoformat(payload["date"]), payload["id"])
                if snapshot.tzinfo is None or anchor[0].tzinfo is None:
                    raise ValueError("timezone")
            except (ValueError, KeyError, TypeError, UnicodeError) as error:
                raise HTTPException(422, "分頁已失效，請重新整理列表。") from error
        reverse = sort != "oldest"
        rows = sorted((row for row in rows if row.created_at <= snapshot),
                      key=lambda row: (row.created_at, row.id), reverse=reverse)
        if anchor:
            rows = [row for row in rows if ((row.created_at, row.id) < anchor if reverse
                                           else (row.created_at, row.id) > anchor)]
        selected = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = selected[-1]
            raw = json.dumps({"scope": scope, "sort": sort, "snapshot": snapshot.isoformat(),
                              "date": last.created_at.isoformat(), "id": last.id},
                             ensure_ascii=False, separators=(",", ":")).encode()
            encoded = base64.urlsafe_b64encode(raw).decode().rstrip("=")
            next_cursor = encoded + "." + hmac.new(cursor_secret, raw, hashlib.sha256).hexdigest()
        return selected, next_cursor

    def private_response(response):
        response.headers["Cache-Control"] = "private, no-store"

    @app.get("/community/feed")
    def feed(response: Response, boards: str = Query(default="", max_length=2500),
             ids: str = Query(default="", max_length=4000),
             topic: str = Query(default="", max_length=40),
             q: str = Query(default="", max_length=80),
             sort: Literal["latest", "oldest", "unanswered"] = "latest",
             limit: int = Query(default=20, ge=1, le=50),
             cursor: str | None = Query(default=None, max_length=8000)):
        private_response(response)
        targets = {value.strip().casefold() for value in boards.split(",") if value.strip()}
        selected_ids = {value for value in ids.split(",") if value}
        query = " ".join(q.casefold().split())
        counts = Counter(row.post_id for row in approved_comments())
        rows = [row for row in approved_posts()
                if (not targets or (row.board_id or "").casefold() in targets
                    or row.school_name.casefold() in targets)
                and (not selected_ids or row.id in selected_ids)
                and (not topic or row.topic.value == topic)
                and (sort != "unanswered" or counts[row.id] == 0)
                and (not query or query in " ".join(" ".join([
                    row.title, row.body, row.school_name, row.country or "",
                    row.academic_year or "", row.application_stage or "",
                ]).casefold().split()))]
        scope = hashlib.sha256(json.dumps([sorted(targets), sorted(selected_ids), topic, query]).encode()).hexdigest()
        selected, next_cursor = page(rows, scope=scope, sort=sort, limit=limit, cursor=cursor)
        items = []
        for row in selected:
            item = public(row)
            item["excerpt"] = row.body[:180]
            item.pop("body")
            item["comment_count"] = counts[row.id]
            items.append(item)
        return {"items": items, "next_cursor": next_cursor}

    @app.get("/community/posts/{post_id}")
    def detail(post_id: str, request: Request, response: Response):
        private_response(response)
        account = viewer(request)
        result = enriched(post_for(post_id), account, read(repository.list_identities) if account else [],
                          read(repository.list_reactions), "post")
        result["comment_count"] = sum(row.post_id == post_id for row in approved_comments())
        return result

    @app.get("/community/posts/{post_id}/comments")
    def comments(post_id: str, request: Request, response: Response,
                 parent_id: str | None = Query(default=None, max_length=128),
                 sort: Literal["latest", "oldest"] = "oldest",
                 limit: int = Query(default=20, ge=1, le=50),
                 cursor: str | None = Query(default=None, max_length=8000)):
        private_response(response)
        post_for(post_id)
        all_rows = [row for row in read(repository.list_comments) if row.post_id == post_id]
        visible = [row for row in approved_comments() if row.post_id == post_id]
        counts = Counter(row.parent_id for row in visible if row.parent_id)
        roots = [row for row in all_rows if not row.parent_id and row.status == ModerationStatus.APPROVED
                 and (not row.deleted or counts[row.id])]
        if parent_id and not any(row.id == parent_id for row in roots):
            raise HTTPException(404, "此回覆串已移除或尚未公開。")
        rows = [row for row in visible if row.parent_id == parent_id] if parent_id else roots
        root_floors = {row.id: index + 1 for index, row in enumerate(sorted(
            (row for row in all_rows if not row.parent_id), key=lambda row: (row.created_at, row.id)))}
        floors = {row.id: index + 1 for index, row in enumerate(sorted(
            (row for row in all_rows if row.parent_id == parent_id), key=lambda row: (row.created_at, row.id)))}
        selected, next_cursor = page(rows, scope="comments:" + post_id + ":" + (parent_id or "root"),
                                    sort=sort, limit=limit, cursor=cursor)
        account = viewer(request)
        identities, reactions = read(repository.list_identities) if account else [], read(repository.list_reactions)
        return {"items": [{**enriched(row, account, identities, reactions, "comment"), "floor": floors[row.id],
                           "parent_floor": root_floors.get(parent_id), "reply_count": counts[row.id]} for row in selected],
                "next_cursor": next_cursor, "total": len(rows), "discussion_total": len(visible)}

    @app.put("/community/{resource_type}/{resource_id}/reaction")
    def react(resource_type: Literal["post", "comment"], resource_id: str,
              payload: CommunityReactionUpdate, request: Request):
        account, _ = authenticated_account(request)
        result = read(lambda: repository.set_reaction(account.id, resource_type, resource_id, payload.reaction,
                                                     platform_admin=is_platform_admin(account)))
        if result["status"] == "missing":
            raise HTTPException(404, "內容已移除或尚未公開。")
        if result["status"] != "committed":
            raise HTTPException(403, "請確認信箱、校籍驗證與停權狀態後再參與。")
        return result

    def mutation(request):
        value = request.headers.get("X-Community-Mutation-ID") or uuid4().hex
        if not 16 <= len(value) <= 128:
            raise HTTPException(422, "操作識別碼格式錯誤。")
        return value

    @app.get("/community/bookmarks")
    def bookmarks(request: Request, response: Response):
        private_response(response)
        account, _ = authenticated_account(request)
        return {"ids": read(lambda: repository.list_bookmarks(account.id))}

    @app.put("/community/posts/{post_id}/bookmark")
    def bookmark(post_id: str, payload: CommunityBookmarkUpdate, request: Request):
        account, _ = authenticated_account(request)
        result = read(lambda: repository.set_bookmark(account.id, post_id, payload.saved))
        if result["status"] == "missing":
            raise HTTPException(404, "文章已移除或尚未公開。")
        if result["status"] == "limit":
            raise HTTPException(409, "帳號最多收藏 100 篇，請先移除一些文章。")
        if result["status"] != "committed":
            raise HTTPException(403, "目前無法保存收藏，請重新登入。")
        return result

    def delete(resource_type, resource_id, request):
        account, _ = authenticated_account(request)
        identity = anonymous_identity(request.headers.get("X-Anonymous-ID"), request.headers.get("X-Anonymous-Token"))
        result = read(lambda: repository.delete_public_content(PublicCommunityDeleteRequest(
            mutation_id=mutation(request), account_id=account.id, identity_id=identity.id,
            access_token_hash=identity.access_token_hash, resource_type=resource_type, resource_id=resource_id)))
        if result.status == PublicCommunityDeleteStatus.COMMITTED:
            return result.model_dump(mode="json")
        if result.status == PublicCommunityDeleteStatus.RESOURCE_MISSING:
            raise HTTPException(404, "內容已移除。")
        if result.status == PublicCommunityDeleteStatus.IDEMPOTENCY_CONFLICT:
            raise HTTPException(409, "操作已變更，請重新送出。")
        raise HTTPException(403, "只有作者能刪除此內容。")

    @app.delete("/community/posts/{post_id}")
    def delete_post(post_id: str, request: Request):
        return delete("post", post_id, request)

    @app.delete("/community/posts/{post_id}/comments/{comment_id}")
    def delete_comment(post_id: str, comment_id: str, request: Request):
        authenticated_account(request)
        if not any(row.id == comment_id and row.post_id == post_id for row in read(repository.list_comments)):
            raise HTTPException(404, "找不到這則回覆。")
        return delete("comment", comment_id, request)

    @app.get("/admin/community/session")
    def admin_session(request: Request, response: Response):
        private_response(response)
        authenticated_admin(request)
        return {"can_moderate": True}

    @app.get("/admin/community/moderation-queue")
    def moderation_queue(request: Request, response: Response):
        private_response(response)
        authenticated_admin(request)
        return read(repository.list_moderation_queue).model_dump(mode="json")

    @app.get("/admin/community/content")
    def moderation_content(request: Request, response: Response,
                           status: Literal["pending", "approved", "hidden"] = "pending"):
        private_response(response)
        authenticated_admin(request)
        # Anonymous identity ids are exposed only to an authenticated moderator.
        items = [{**row.model_dump(mode="json"), "resource_type": kind}
                 for kind, method in [("post", repository.list_posts), ("comment", repository.list_comments)]
                 for row in read(method) if row.status.value == status and not getattr(row, "deleted", False)]
        return {"items": sorted(items, key=lambda row: row["created_at"], reverse=True)[:100]}

    @app.get("/admin/community/moderation-audits")
    def moderation_audits(request: Request, response: Response):
        private_response(response)
        authenticated_admin(request)
        return [row.model_dump(mode="json") for row in sorted(read(repository.list_moderation_audits),
                key=lambda row: row.created_at, reverse=True)[:100]]

    @app.get("/admin/community/reports")
    def reports(request: Request, response: Response):
        private_response(response)
        authenticated_admin(request)
        resources = {(kind, row.id): row for kind, method in [("post", repository.list_posts), ("comment", repository.list_comments)] for row in read(method)}
        return [{**row.model_dump(mode="json", exclude={"reporter_id"}),
                 "content": public(resources[(row.resource_type, row.resource_id)]) if (row.resource_type, row.resource_id) in resources else None}
                for row in sorted(read(repository.list_reports), key=lambda row: row.created_at, reverse=True)
                if row.status.value == "pending"][:100]

    @app.patch("/admin/community/reports/{report_id}")
    def review_report(report_id: str, payload: CommunityReportReviewRequest, request: Request):
        moderator, _ = authenticated_admin(request)
        if len(payload.note.strip()) < 2:
            raise HTTPException(422, "請填寫處理原因。")
        result = read(lambda: repository.commit_report_review(CommunityReportReviewMutationRequest(
            mutation_id=mutation(request), moderator_id=moderator.id, report_id=report_id,
            status=payload.status, note=payload.note)))
        if result.status != PrivateCommunityMutationStatus.COMMITTED:
            raise HTTPException(409, "檢舉已由其他管理者處理，請重新載入。")
        return result.audit.model_dump(mode="json")

    @app.patch("/admin/community/{resource_type}/{resource_id}")
    def moderate(resource_type: PublicCommunityResourceType, resource_id: str,
                 payload: CommunityModerationRequest, request: Request):
        account, _ = authenticated_admin(request)
        if len(payload.note.strip()) < 2:
            raise HTTPException(422, "請填寫至少兩個字的處理原因。")
        methods = {"post": repository.list_posts, "comment": repository.list_comments}
        if resource_type.value not in methods:
            raise HTTPException(422, "此介面僅處理討論文章與留言。")
        target = next((row for row in read(methods[resource_type.value]) if row.id == resource_id), None)
        if target is None or (getattr(target, "deleted", False) and payload.status != ModerationStatus.HIDDEN):
            raise HTTPException(404, "內容已移除。")
        result = read(lambda: repository.commit_moderation(PublicCommunityModerationRequest(
            mutation_id=mutation(request), moderator_id=account.id, resource_type=resource_type,
            resource_id=resource_id, expected_status=payload.expected_status or target.status,
            status=payload.status, note=payload.note)))
        if result.status != PublicCommunityModerationStatus.COMMITTED:
            raise HTTPException(409, "內容已由其他管理者更新，請重新載入後確認。")
        return result.audit.model_dump(mode="json")

    @app.post("/admin/community/identities/{identity_id}/suspend")
    def suspend(identity_id: str, payload: CommunitySuspensionRequest, request: Request):
        moderator, _ = authenticated_admin(request)
        event_id = mutation(request)
        existing = next((row for row in read(repository.list_moderation_audits) if row.id == event_id), None)
        if existing:
            if (existing.resource_type == "identity" and existing.resource_id == identity_id
                and existing.moderator_id == moderator.id and existing.note == payload.reason
                and existing.new_suspended_until == payload.suspended_until):
                return existing.model_dump(mode="json")
            raise HTTPException(409, "操作識別碼已被其他停權操作使用。")
        identity = next((row for row in read(repository.list_identities) if row.id == identity_id), None)
        target = account_repository.find_account_by_id(identity.account_id) if identity and identity.account_id else None
        if target is None:
            raise HTTPException(404, "找不到此社群帳號。")
        if target.id == moderator.id:
            raise HTTPException(403, "無法透過此介面停權自己的帳號。")
        try:
            result = account_repository.commit_community_suspension(CommunitySuspensionMutationRequest(
                event_id=event_id, identity_id=identity.id, account_id=target.id, moderator_id=moderator.id,
                expected_suspended_until=target.community_suspended_until,
                suspended_until=payload.suspended_until, reason=payload.reason))
        except AccountRepositoryError as error:
            raise HTTPException(503, "停權操作暫時失敗，請稍後重試。") from error
        if result.status == CommunitySuspensionMutationStatus.INVALID_DEADLINE:
            raise HTTPException(422, "停權期限必須在未來。")
        if result.status != CommunitySuspensionMutationStatus.COMMITTED:
            raise HTTPException(409, "帳號狀態已更新，請重新載入。")
        return result.audit.model_dump(mode="json")

    def create_identity(request: Request):
        account, _ = authenticated_account(request)
        token = secrets.token_urlsafe(32)
        candidate = AnonymousIdentity(account_id=account.id, display_name="匿名學生",
                                      access_token_hash=hashlib.sha256(token.encode()).hexdigest())
        try:
            result = repository.commit_identity(CommunityIdentityMutationRequest(
                mutation_id=uuid4().hex, identity=candidate))
        except CommunityRepositoryError as error:
            raise HTTPException(503, "社群身分暫時無法建立。") from error
        if result.status != CommunityIdentityMutationStatus.COMMITTED or result.identity is None:
            raise HTTPException(409, "社群身分無法建立，請重新登入。")
        return {"id": result.identity.id, "display_name": result.identity.display_name,
                "access_token": token}

    @app.get("/auth/community-identity-options")
    def identity_options(request: Request, response: Response):
        private_response(response)
        account, _ = authenticated_account(request)
        school = bool(account.student_status_verified and account.verified_university)
        department = bool(school and account.verified_department)
        return {"default_mode": "anonymous", "options": [
            {"mode": "anonymous", "label": "匿名學生", "enabled": True},
            {"mode": "real_name", "label": account.display_name, "enabled": True},
            {"mode": "verified_school", "label": f"{account.verified_university}學生" if school else "學校身分",
             "enabled": school, "unavailable_reason": None if school else "完成校籍驗證後可使用"},
            {"mode": "verified_department", "label": f"{account.verified_university} {account.verified_department}學生" if department else "學校與系所",
             "enabled": department, "unavailable_reason": None if department else "尚無已驗證系所"},
        ]}

    def publish(request, account, identity, content, resource_type):
        if re.search(r"付費代辦|保證錄取|保證簽證|保證獲得簽證|匯款代辦", re.sub(r"\s+", "", getattr(content, "title", "") + content.body)):
            content = content.model_copy(update={"status": ModerationStatus.PENDING})
        mutation_id = request.headers.get("X-Community-Mutation-ID") or uuid4().hex
        if not 16 <= len(mutation_id) <= 128:
            raise HTTPException(422, "發布識別碼格式錯誤。")
        try:
            result = repository.commit_publication(PublicCommunityPublicationRequest(
                mutation_id=mutation_id, account_id=account.id, identity_id=identity.id,
                access_token_hash=identity.access_token_hash,
                resource_type=PublicCommunityResourceType(resource_type),
                content=content.model_dump(mode="json")))
        except CommunityRepositoryError as error:
            raise HTTPException(503, "發布暫時失敗，請保留內容後重試。") from error
        if result.status == PublicCommunityPublicationStatus.COMMITTED:
            return result.parsed_content()
        if result.status == PublicCommunityPublicationStatus.RATE_LIMITED:
            raise HTTPException(429, "發言太頻繁，請稍後再試。",
                                headers={"Retry-After": str(result.retry_after_seconds or 60)})
        if result.status == PublicCommunityPublicationStatus.IDEMPOTENCY_CONFLICT:
            raise HTTPException(409, "發布內容已變更，請重新送出。")
        if result.status == PublicCommunityPublicationStatus.PARENT_MISSING:
            raise HTTPException(404, "文章已移除或尚未公開。")
        raise HTTPException(403, "目前無法在此看板發言，請確認登入與驗證狀態。")

    def submit_report(request, identity, report):
        account, _ = authenticated_account(request)
        result = read(lambda: repository.commit_report(CommunityReportMutationRequest(
            mutation_id=mutation(request), account_id=account.id, identity_id=identity.id,
            access_token_hash=identity.access_token_hash, report=report)))
        if result.status == PrivateCommunityMutationStatus.COMMITTED:
            return result.report
        if result.status == PrivateCommunityMutationStatus.RESOURCE_MISSING:
            raise HTTPException(404, "內容已移除。")
        raise HTTPException(403, "目前無法送出檢舉，請確認登入及帳號狀態。")

    return publish, create_identity, submit_report

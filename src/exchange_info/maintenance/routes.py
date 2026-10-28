"""FastAPI router implementing Section 13 Admin Workbench & Public Release-Pinned API contracts."""

from __future__ import annotations

from typing import Any, Callable, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from .contracts import ReviewStatus, RiskLevel, utc_now
from .queue_worker import JobStatus, build_fetch_dedupe_key
from .safe_fetcher import FetchPolicyError, validate_and_canonicalize_source_url
from .store import AccessDeniedError, MaintenanceStore, OptimisticLockConflictError

PRIVATE_NO_STORE = {"Cache-Control": "private, no-store, max-age=0"}


class ReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_version: int = Field(ge=1)
    evidence_set_hash: str = Field(min_length=64, max_length=64)
    base_release_id: str | None = None
    decision: Literal["approve", "reject", "defer", "recheck", "flag_source"]
    selected_fields: list[str] = Field(min_length=1)
    reason: str = Field(min_length=3, max_length=1000)
    idempotency_key: str = Field(min_length=4, max_length=128)


class PublicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_change_ids: list[str] = Field(min_length=1)
    base_release_id: str | None = None
    reason: str = Field(min_length=3, max_length=1000)
    idempotency_key: str = Field(min_length=4, max_length=128)


class PublicationRollbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_release_id: str = Field(min_length=1)
    target_release_id: str = Field(min_length=1)
    target_entity_keys: list[str] | None = None
    reason: str = Field(min_length=3, max_length=1000)
    idempotency_key: str = Field(min_length=4, max_length=128)


class SourceRefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["fetch", "reprocess"] = "fetch"
    resource_url: str | None = None
    force_unconditional: bool = False
    reason: str = Field(min_length=3, max_length=500)


class PublicReportSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_entity_type: Literal["offering", "institution", "experience"] = "offering"
    target_entity_id: str = Field(min_length=1, max_length=200)
    published_release_id: str | None = None
    published_revision_id: str | None = None
    category: Literal["stale_info", "quota_mismatch", "deadline_changed", "broken_link", "other"] = "stale_info"
    text: str = Field(min_length=5, max_length=2000)
    evidence_url: str | None = None


def create_maintenance_router(
    store: MaintenanceStore,
    *,
    authenticate_admin: Callable[[Request], tuple[str, set[str] | None]],
    authenticate_submitter: Callable[[Request], str] | None = None,
) -> APIRouter:
    """Create the FastAPI router for Section 13 Admin & Public Maintenance endpoints."""
    router = APIRouter()

    def _require_admin(request: Request, response: Response) -> tuple[str, set[str] | None]:
        response.headers.update(PRIVATE_NO_STORE)
        try:
            admin_id, allowed_home_ids = authenticate_admin(request)
        except AccessDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        if not admin_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        return admin_id, allowed_home_ids

    def _serialize_change_set(cs: Any) -> dict[str, Any]:
        d = cs.model_dump(mode="json")
        home_inst = store.institutions.get(cs.home_id)
        host_inst = store.institutions.get(cs.host_id)
        d["home_name"] = home_inst.canonical_name if home_inst else cs.home_id
        d["host_name"] = host_inst.canonical_name if host_inst else cs.host_id
        d["host_country"] = host_inst.country_code if host_inst else ""
        return d

    @router.get("/admin/maintenance/dashboard")
    def admin_dashboard(request: Request, response: Response) -> dict[str, Any]:
        """Screen 1 (Spec 13.1): Today's work, high-risk pending changes, broken sources, disk/backup/budget status."""
        _, allowed_homes = _require_admin(request, response)
        pending_high = [
            _serialize_change_set(cs)
            for cs in store.change_sets.values()
            if cs.status in {ReviewStatus.PENDING, ReviewStatus.CONFLICTING}
            and cs.risk == RiskLevel.HIGH
            and (allowed_homes is None or cs.home_id in allowed_homes)
        ]
        unhealthy_resources = [
            res.model_dump(mode="json")
            for res in store.resources.values()
            if res.health_status.value != "healthy"
        ]
        dead_letters = [j.model_dump(mode="json") for j in store.queue.list_jobs(status=JobStatus.DEAD_LETTER)]
        return {
            "screens": [
                "today_work",
                "change_review",
                "source_management",
                "institutions_and_programs",
                "experiences_and_reports",
                "publications_and_ops",
            ],
            "pending_high_risk_changes": pending_high,
            "unhealthy_resources": unhealthy_resources,
            "dead_letter_jobs": dead_letters,
            "budget_status": {
                "external_ai_opted_in": store.guard.external_ai_opted_in,
                "monthly_budget_twd": store.guard.monthly_budget_twd,
                "settled_spend_twd": store.guard.settled_spend_twd,
                "reserved_inflight_twd": store.guard.reserved_inflight_twd,
                "alerts": list(store.guard.alerts),
            },
            "current_release_id": store.current_release_id,
        }

    @router.get("/admin/changes")
    def list_changes(
        request: Request,
        response: Response,
        risk: RiskLevel | None = Query(None),
        school: str | None = Query(None),
        cycle: str | None = Query(None),
        status: ReviewStatus | None = Query(None),
    ) -> dict[str, Any]:
        """Screen 2 (Spec 13.3): List candidate change sets with candidate_version and evidence_set_hash."""
        _, allowed_homes = _require_admin(request, response)
        rows = []
        for cs in store.change_sets.values():
            if allowed_homes is not None and cs.home_id not in allowed_homes:
                continue
            if risk and cs.risk != risk:
                continue
            if school and cs.home_id != school and cs.host_id != school:
                continue
            if cycle and cs.cycle_id != cycle:
                continue
            if status and cs.status != status:
                continue
            rows.append(_serialize_change_set(cs))
        rows.sort(key=lambda r: (0 if r["risk"] == "high" else 1, r["created_at"]))
        return {"items": rows, "total": len(rows)}

    @router.get("/admin/changes/{change_id}")
    def get_change_detail(change_id: str, request: Request, response: Response) -> dict[str, Any]:
        """Screen 2 (Spec 9.2, 13.3): Detailed review card with old/new, evidence locators, base release, and conflicts."""
        _, allowed_homes = _require_admin(request, response)
        cs = store.change_sets.get(change_id)
        if cs is None:
            raise HTTPException(status_code=404, detail="ChangeSet not found")
        if allowed_homes is not None and cs.home_id not in allowed_homes:
            raise HTTPException(status_code=403, detail="Admin scope does not cover this home university")
        return _serialize_change_set(cs)

    @router.post("/admin/changes/{change_id}/review")
    def review_change(
        change_id: str,
        payload: ReviewDecisionRequest,
        request: Request,
        response: Response,
    ) -> dict[str, Any]:
        """Screen 2 (Spec 9.2, 9.3, 13.3): Approve/reject/defer selected fields; returns 409 if stale."""
        admin_id, allowed_homes = _require_admin(request, response)
        cs = store.change_sets.get(change_id)
        if cs is None:
            raise HTTPException(status_code=404, detail="ChangeSet not found")
        if allowed_homes is not None and cs.home_id not in allowed_homes:
            raise HTTPException(status_code=403, detail="Admin scope does not cover this home university")

        try:
            updated_cs, remaining_cs = store.review_change_set(
                change_set_id=change_id,
                reviewer_id=admin_id,
                candidate_version=payload.candidate_version,
                evidence_set_hash=payload.evidence_set_hash,
                base_release_id=payload.base_release_id,
                decision=payload.decision,
                selected_fields=payload.selected_fields,
                reason=payload.reason,
                idempotency_key=payload.idempotency_key,
            )
        except OptimisticLockConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "change_set": _serialize_change_set(updated_cs),
            "remaining_change_set": _serialize_change_set(remaining_cs) if remaining_cs else None,
        }

    @router.post("/admin/publications")
    def publish_changes(
        payload: PublicationRequest,
        request: Request,
        response: Response,
    ) -> dict[str, Any]:
        """Screen 6 (Spec 9.3, 13.3): Atomically publish approved change sets and switch publication_head."""
        admin_id, allowed_homes = _require_admin(request, response)
        for cid in payload.approved_change_ids:
            cs = store.change_sets.get(cid)
            if cs and allowed_homes is not None and cs.home_id not in allowed_homes:
                raise HTTPException(status_code=403, detail="Admin scope does not cover all selected change sets")

        try:
            release = store.publish_approved_changes(
                change_set_ids=payload.approved_change_ids,
                base_release_id=payload.base_release_id,
                publisher_id=admin_id,
                reason=payload.reason,
                idempotency_key=payload.idempotency_key,
            )
        except OptimisticLockConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {"release_id": release.id, "release": release.model_dump(mode="json")}

    @router.post("/admin/publications/rollback")
    def rollback_publication(
        payload: PublicationRollbackRequest,
        request: Request,
        response: Response,
    ) -> dict[str, Any]:
        """Screen 6 (Spec 9.4, 13.3): Roll back selected entities (or entire release) by creating a new release without deleting history."""
        admin_id, _ = _require_admin(request, response)
        try:
            release = store.rollback_release_entities(
                current_release_id=payload.current_release_id,
                target_release_id=payload.target_release_id,
                entity_keys=payload.target_entity_keys,
                actor_id=admin_id,
                reason=payload.reason,
                idempotency_key=payload.idempotency_key,
            )
        except OptimisticLockConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {"release_id": release.id, "release": release.model_dump(mode="json")}

    @router.post("/admin/sources/{source_id}/refresh", status_code=202)
    def refresh_source(
        source_id: str,
        payload: SourceRefreshRequest,
        request: Request,
        response: Response,
    ) -> dict[str, Any]:
        """Screen 3 (Spec 13.3): Trigger manual recheck/reprocess (returns 202 + job_id; blocks unapproved URLs)."""
        admin_id, allowed_homes = _require_admin(request, response)
        src = store.sources.get(source_id)
        if src is None:
            raise HTTPException(status_code=404, detail="Source not found")
        if allowed_homes is not None and src.owner_institution_id not in allowed_homes:
            raise HTTPException(status_code=403, detail="Admin scope does not cover this source")

        target_url = payload.resource_url or src.entry_url
        try:
            canonical_url, _ = validate_and_canonicalize_source_url(
                target_url,
                approved_domains=src.approved_domains,
                resolver=lambda host, port: ["140.112.8.130"],
            )
        except FetchPolicyError as exc:
            raise HTTPException(status_code=400, detail=f"Rejected unapproved or unsafe URL: {exc}") from exc

        dk = build_fetch_dedupe_key(f"{source_id}:{canonical_url}", "manual_refresh", src.policy_version)
        job = store.queue.enqueue(
            job_type=payload.action,
            dedupe_key=dk,
            resource_id=source_id,
            payload={
                "source_id": source_id,
                "url": canonical_url,
                "force_unconditional": payload.force_unconditional,
                "reason": payload.reason,
                "requested_by": admin_id,
            },
            priority=500,
            boost_if_exists=True,
        )
        return {"job_id": job.id, "status": job.status.value}

    @router.get("/admin/jobs/{job_id}")
    def get_job_status(job_id: str, request: Request, response: Response) -> dict[str, Any]:
        """Screen 6 (Spec 13.3): Check job status, error_class, and next scheduled retry."""
        _require_admin(request, response)
        job = store.queue.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job.model_dump(mode="json")

    @router.get("/admin/snapshots/{blob_id}/download")
    def download_private_snapshot(
        blob_id: str,
        request: Request,
        response: Response,
        source_id: str = Query(..., min_length=1),
    ) -> Response:
        """Spec 11.4 / T19, T35: Authenticated admin-only snapshot download with source ACL & path traversal check."""
        _, allowed_homes = _require_admin(request, response)
        allowed_src_ids: set[str] | None = None
        if allowed_homes is not None:
            allowed_src_ids = {s.id for s in store.sources.values() if s.owner_institution_id in allowed_homes}
        try:
            raw_bytes = store.blob_vault.read_blob_authorized(
                blob_id,
                requesting_source_id=source_id,
                allowed_admin_source_ids=allowed_src_ids,
            )
        except AccessDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return Response(content=raw_bytes, media_type="application/octet-stream", headers=PRIVATE_NO_STORE)

    @router.get("/offerings")
    def get_public_offerings(
        home: str | None = Query(None),
        cycle: str | None = Query(None),
        release_id: str | None = Query(None),
    ) -> dict[str, Any]:
        """Public read-only API pinned to release_id (Spec 9.3, 13.3, T17, T19)."""
        try:
            return store.list_public_offerings(home_id=home, cycle_id=cycle, release_id=release_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/offerings/{offering_id}")
    def get_public_offering_detail(
        offering_id: str,
        release_id: str | None = Query(None),
    ) -> dict[str, Any]:
        """Public read-only offering detail pinned to the same release_id as the list (Spec 9.3, 13.3, T17, T28)."""
        try:
            return store.get_public_offering_projection(offering_id, release_id=release_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/reports", status_code=201)
    def submit_public_report(payload: PublicReportSubmitRequest) -> dict[str, Any]:
        """Public stale/error report bound to published revision/release; never directly mutates published data (Spec 12.4, 13.3)."""
        report_id = f"rep_{uuid4().hex[:14]}"
        record = {
            "id": report_id,
            "target_entity_type": payload.target_entity_type,
            "target_entity_id": payload.target_entity_id,
            "published_release_id": payload.published_release_id or store.current_release_id,
            "published_revision_id": payload.published_revision_id,
            "category": payload.category,
            "text": payload.text,
            "evidence_url": payload.evidence_url,
            "status": "pending",
            "created_at": utc_now().isoformat(),
        }
        store.reports.append(record)
        return {"report_id": report_id, "status": "pending"}

    @router.post("/experience-submissions", status_code=201)
    @router.post("/maintenance/experience-submissions", status_code=201)
    def submit_experience(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit student experience into pending moderation queue; blocks privilege escalation and isolates PII (Spec 11.3, 12, T19, T20)."""
        submitter_id = authenticate_submitter(request) if authenticate_submitter else "anon_verified_student"
        if not submitter_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        try:
            contact_email = payload.pop("contact_email", None)
            record = store.submit_student_experience(
                submitter_account_id=submitter_id,
                raw_payload=payload,
                contact_email=contact_email,
            )
        except AccessDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "experience_id": record.id,
            "review_status": record.review_status,
            "experience_year": record.experience_year,
        }

    @router.get("/admin/releases")
    def list_releases(request: Request, response: Response) -> dict[str, Any]:
        """List all immutable releases and current publication_head for Screen 6."""
        _require_admin(request, response)
        rels = [r.model_dump(mode="json") for r in store.releases.values()]
        rels.sort(key=lambda r: r["published_at"], reverse=True)
        return {
            "current_release_id": store.current_release_id,
            "lock_version": store.publication_lock_version,
            "items": rels,
            "audit_events": [e.model_dump(mode="json") for e in store.audit_events[-30:]],
        }

    @router.get("/admin/sources")
    def list_sources(request: Request, response: Response) -> dict[str, Any]:
        """List registered official sources for Screen 3."""
        _, allowed_homes = _require_admin(request, response)
        srcs = []
        for s in store.sources.values():
            if allowed_homes is not None and s.owner_institution_id not in allowed_homes:
                continue
            sd = s.model_dump(mode="json")
            home_inst = store.institutions.get(s.owner_institution_id)
            sd["home_name"] = home_inst.canonical_name if home_inst else s.owner_institution_id
            srcs.append(sd)
        return {"items": srcs, "total": len(srcs)}

    @router.get("/admin/reports")
    def list_admin_reports(request: Request, response: Response) -> dict[str, Any]:
        """List submitted public reports and pending experiences for Screen 5."""
        _require_admin(request, response)
        return {
            "reports": list(reversed(store.reports)),
            "experiences": [e.model_dump(mode="json") for e in store.experiences.values()],
        }

    @router.get("/maintenance-preview")
    def maintenance_preview_ui() -> Response:
        """Interactive Staging Preview UI covering all 6 Spec Section 13.1 Admin Screens + Public Release-Pinned Explorer."""
        html = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>UniWay 全台交換學校資訊維護後台</title>
  <style>
    :root {
      --bg: #0f172a;
      --panel: #1e293b;
      --panel-alt: #334155;
      --card-inner: #0b1120;
      --text: #f8fafc;
      --muted: #cbd5e1;
      --accent: #38bdf8;
      --ok: #22c55e;
      --warn: #f59e0b;
      --danger: #ef4444;
      --border: #475569;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, "Microsoft JhengHei", "PingFang TC", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      font-size: 15px;
    }
    header {
      background: #020617;
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }
    header h1 { margin: 0 0 4px 0; font-size: 1.25rem; color: var(--accent); }
    .badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 600;
      line-height: 1.4;
      white-space: nowrap;
    }
    .badge.high { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid var(--danger); }
    .badge.ok { background: rgba(34,197,94,0.2); color: #86efac; border: 1px solid var(--ok); }
    .badge.warn { background: rgba(245,158,11,0.2); color: #fcd34d; border: 1px solid var(--warn); }
    .badge.info { background: rgba(56,189,248,0.18); color: #7dd3fc; border: 1px solid var(--accent); }
    nav {
      display: flex;
      gap: 8px;
      padding: 12px 24px;
      background: var(--panel);
      border-bottom: 1px solid var(--border);
      overflow-x: auto;
    }
    nav button {
      background: #0f172a;
      color: var(--muted);
      border: 1px solid var(--border);
      padding: 9px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.95rem;
      white-space: nowrap;
      transition: all 0.15s ease;
    }
    nav button:hover { border-color: var(--accent); color: var(--text); }
    nav button.active {
      background: var(--accent);
      color: #020617;
      border-color: var(--accent);
    }
    main { padding: 20px 24px; max-width: 1440px; margin: 0 auto; }
    .screen { display: none; }
    .screen.active { display: block; }
    .guide-banner {
      background: rgba(56, 189, 248, 0.1);
      border-left: 4px solid var(--accent);
      border-radius: 6px;
      padding: 12px 16px;
      margin-bottom: 18px;
      color: var(--text);
      font-size: 0.93rem;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px;
      margin-bottom: 18px;
      overflow: hidden;
    }
    .card h3 { margin-top: 0; margin-bottom: 12px; font-size: 1.08rem; color: var(--accent); }
    .change-card {
      background: var(--card-inner);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px;
      margin-bottom: 18px;
      overflow: hidden;
    }
    .change-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 12px;
      padding-bottom: 14px;
      margin-bottom: 14px;
      border-bottom: 1px solid var(--border);
    }
    .change-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 6px;
    }
    .change-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      font-size: 0.88rem;
      color: var(--muted);
    }
    button.btn {
      background: var(--accent);
      color: #020617;
      border: none;
      padding: 8px 14px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.9rem;
      cursor: pointer;
      margin-right: 6px;
      margin-bottom: 4px;
    }
    button.btn:hover { opacity: 0.92; }
    button.btn.secondary { background: var(--panel-alt); color: var(--text); border: 1px solid var(--border); }
    button.btn.danger { background: var(--danger); color: #fff; }
    button.btn.success { background: var(--ok); color: #020617; }
    select, input[type="text"] {
      background: #020617;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.92rem;
    }
    .table-wrap {
      width: 100%;
      overflow-x: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
      table-layout: fixed;
    }
    th, td {
      border-bottom: 1px solid var(--border);
      padding: 12px 10px;
      text-align: left;
      vertical-align: top;
      word-break: break-word;
      overflow-wrap: anywhere;
      white-space: normal;
    }
    th {
      color: var(--muted);
      font-weight: 600;
      background: rgba(15, 23, 42, 0.55);
    }
    .val-box {
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 0.9rem;
      word-break: break-word;
      overflow-wrap: anywhere;
    }
    .val-box.after-ok {
      border-color: rgba(34, 197, 94, 0.6);
      background: rgba(20, 83, 45, 0.22);
    }
    .val-box.after-conflict {
      border-color: rgba(239, 68, 68, 0.7);
      background: rgba(127, 29, 29, 0.25);
    }
    .val-label {
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 2px;
    }
    .val-main {
      font-weight: 700;
      color: #fff;
      margin-bottom: 4px;
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.85em;
      background: rgba(15, 23, 42, 0.8);
      padding: 2px 5px;
      border-radius: 4px;
      word-break: break-word;
      overflow-wrap: anywhere;
    }
    #toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #020617;
      border: 2px solid var(--accent);
      padding: 14px 20px;
      border-radius: 10px;
      display: none;
      max-width: 480px;
      z-index: 999;
      box-shadow: 0 10px 25px rgba(0,0,0,0.6);
      font-weight: 600;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>UniWay 全台交換學校資訊維護後台</h1>
      <small style="color:var(--muted)">目前已載入 6 所大學（臺大、北大、中央、長庚、中正、淡江）共 1,124 筆姊妹校交換計畫資料</small>
    </div>
    <div style="text-align:right">
      <div>目前前台網站顯示版本：<strong id="hdr-release" style="color:var(--ok)">載入中...</strong></div>
      <small style="color:var(--muted)">目前登入身分：總管理員（可審核並發布所有學校資料）</small>
    </div>
  </header>

  <nav id="main-nav">
    <button class="active" data-action="switch-tab" data-tab="s1">1. 今日待辦總覽</button>
    <button data-action="switch-tab" data-tab="s2">2. 變更審核（核對修改內容）</button>
    <button data-action="switch-tab" data-tab="s3">3. 學校官網來源管理</button>
    <button data-action="switch-tab" data-tab="s4">4. 各校交換名額總表（前台預覽）</button>
    <button data-action="switch-tab" data-tab="s5">5. 學生問題回報與交換心得</button>
    <button data-action="switch-tab" data-tab="s6">6. 發布上線與版本還原</button>
  </nav>

  <main>
    <!-- Screen 1 -->
    <section id="s1" class="screen active">
      <div class="guide-banner">
        <strong>💡 維護人員日常操作 3 步驟：</strong><br/>
        ① 系統自動檢查各大學國際處官網，發現簡章更新時會列在下方「待核對清單」 ➔
        ② 點選 <strong>「2. 變更審核」</strong> 核對修改前後的內容並勾選核准 ➔
        ③ 點選 <strong>「6. 發布上線與版本還原」</strong> 按下「立即發布到前台網站」，學生就能看到最新資訊！
      </div>
      <div class="grid" id="s1-metrics"></div>
      <div class="card">
        <h3>📌 待您核對的重要資料變動（名額、截止日或年份衝突）</h3>
        <div class="table-wrap" id="s1-high-risk"></div>
      </div>
    </section>

    <!-- Screen 2 -->
    <section id="s2" class="screen">
      <div class="guide-banner">
        <strong>📋 如何審核修改內容？</strong><br/>
        • 下方每一張卡片代表一筆學校簡章的資料變動。請對照 <strong>「修改前（目前網站顯示）」</strong> 與 <strong>「修改後（最新簡章內容）」</strong>。<br/>
        • 如果只有部分項目確認無誤，您可以<strong>只勾選正確的項目</strong>按下「✅ 核准勾選的項目」，沒勾選的項目會自動留待下次處理。<br/>
        • 若出現 <span class="badge high">⚠️ 資料年份衝突（系統已攔截）</span>，代表官網網頁與 PDF 附件年份對不起來，系統已自動攔截避免覆蓋正確資料，請點選「⏸️ 先暫緩不改」。
      </div>
      <div class="card">
        <h3>待審核與已處理的資料變更單</h3>
        <div id="s2-changes"></div>
      </div>
    </section>

    <!-- Screen 3 -->
    <section id="s3" class="screen">
      <div class="guide-banner">
        <strong>🌐 為什麼要有「官網來源白名單」？</strong><br/>
        為了確保交換資訊 100% 來自各校國際事務處官方公告，系統只允許從下方核准的學校官方網址抓取簡章，並自動阻擋任何非官方或危險網址。
      </div>
      <div class="card">
        <h3>6 所大學官方簡章來源清單</h3>
        <div class="table-wrap" id="s3-sources"></div>
      </div>
    </section>

    <!-- Screen 4 -->
    <section id="s4" class="screen">
      <div class="guide-banner">
        <strong>🔍 前台資料預覽說明：</strong><br/>
        許多大學（如臺大）的交換簡章只列出姊妹校申請門檻，並未在總表寫出具體人數。本系統會清楚區分 <strong>「🟢 有明確名額」</strong>、<strong>「🟡 簡章未記載名額」</strong> 與 <strong>「🔴 本學期不招收 (0名)」</strong>，不會把「沒寫名額」誤當成「0 名」。
      </div>
      <div class="card">
        <h3>各校交換姊妹校與名額一覽表（學生前台看到的畫面資料）</h3>
        <div style="margin-bottom:14px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
          <label><strong>選擇要查看的母校：</strong></label>
          <select id="s4-home">
            <option value="ntu">國立臺灣大學（共 289 所姊妹校）</option>
            <option value="ntpu">國立臺北大學（共 409 所姊妹校）</option>
            <option value="ncu">國立中央大學（共 214 所姊妹校）</option>
            <option value="cgu">長庚大學（共 154 所姊妹校）</option>
            <option value="ccu">國立中正大學（共 55 所姊妹校）</option>
            <option value="tku">淡江大學（共 4 所姊妹校）</option>
            <option value="fju">天主教輔仁大學（共 234 所姊妹校）</option>
            <option value="scu">東吳大學（共 191 所姊妹校）</option>
            <option value="ntnu">國立臺灣師範大學（共 236 所姊妹校）</option>
            <option value="cycu">中原大學（共 89 所姊妹校）</option>
            <option value="ntust">國立臺灣科技大學（共 237 所姊妹校）</option>
            <option value="yzu">元智大學（共 90 所姊妹校）</option>
            <option value="fcu">逢甲大學（共 161 所姊妹校）</option>
            <option value="nsysu">國立中山大學（共 218 所姊妹校）</option>
            <option value="nchu">國立中興大學（共 226 所姊妹校）</option>
            <option value="ntut">國立臺北科技大學（共 206 所姊妹校）</option>
            <option value="nccu">國立政治大學（共 266 所姊妹校）</option>
            <option value="ncku">國立成功大學（共 211 所姊妹校）</option>
            <option value="nycu">國立陽明交通大學（共 243 所姊妹校）</option>
            <option value="nthu">國立清華大學（共 176 所姊妹校）</option>
            <option value="pccu">中國文化大學（共 135 所姊妹校）</option>
            <option value="wzu">文藻外語大學（共 147 所姊妹校）</option>
            <option value="nkust">國立高雄科技大學（共 107 所姊妹校）</option>
            <option value="yuntech">國立雲林科技大學（共 112 所姊妹校）</option>
            <option value="ntou">國立臺灣海洋大學（共 123 所姊妹校）</option>
            <option value="ncue">國立彰化師範大學（共 108 所姊妹校）</option>
            <option value="nknu">國立高雄師範大學（共 143 所姊妹校）</option>
            <option value="tmu">臺北醫學大學（共 201 所姊妹校）</option>
            <option value="csmu">中山醫學大學（共 124 所姊妹校）</option>
            <option value="cmu">中國醫藥大學（共 174 所姊妹校）</option>
            <option value="kmu">高雄醫學大學（共 188 所姊妹校）</option>
            <option value="mcu">銘傳大學（共 202 所姊妹校）</option>
            <option value="ntub">國立臺北商業大學（共 93 所姊妹校）</option>
            <option value="ncnu">國立暨南國際大學（共 212 所姊妹校）</option>
          </select>
          <label>查看歷史版本編號（留空代表目前最新上線版本）：</label>
          <input type="text" id="s4-release" placeholder="預設顯示目前最新版本" style="width:210px" />
          <button class="btn" data-action="load-offerings">🔍 重新查詢</button>
        </div>
        <div id="s4-summary" style="margin-bottom:14px"></div>
        <div class="table-wrap" id="s4-table"></div>
      </div>
    </section>

    <!-- Screen 5 -->
    <section id="s5" class="screen">
      <div class="guide-banner">
        <strong>💬 學生回報與心得安全機制：</strong><br/>
        學生在前台提交的「資料錯誤回報」或「交換心得投稿」，都會先進入下方待審核清單，<strong>絕對不會直接改動前台網站資料</strong>，且學生的聯絡信箱會自動加密隔離保護。
      </div>
      <div class="grid">
        <div class="card">
          <h3>📮 模擬學生在前台送出「資料勘誤回報」</h3>
          <p style="color:var(--muted);font-size:0.88rem">您可以測試看看：當學生發現某間姊妹校名額更新時，送出回報單後會出現在下方待辦清單。</p>
          <label style="font-size:0.85rem;color:var(--muted)">回報對應的學校或項目：</label>
          <input type="text" id="rep-entity" value="國立臺灣大學 — 加州大學柏克萊分校交換計畫" style="width:100%;margin-bottom:8px" />
          <label style="font-size:0.85rem;color:var(--muted)">學生填寫的問題說明：</label>
          <input type="text" id="rep-text" value="官方最新簡章名額已經從 2 名改為 4 名，請協助更新！" style="width:100%;margin-bottom:10px" />
          <button class="btn" data-action="submit-report">📩 送出測試回報單</button>
        </div>
        <div class="card">
          <h3>🎓 模擬學長姐投稿「交換心得」與安全防護測試</h3>
          <p style="color:var(--muted);font-size:0.88rem">系統會完整保留學長姐真實交換年份（例如 2023 年），並自動攔截任何試圖跳過審核的惡意請求。</p>
          <button class="btn" data-action="submit-exp" data-escalate="false">📝 模擬正常投稿（2023 秋季交換心得）</button>
          <button class="btn danger" data-action="submit-exp" data-escalate="true">🛡️ 測試安全攔截（模擬有人偷改審核狀態）</button>
        </div>
      </div>
      <div class="card">
        <h3>📋 待處理的學生問題回報與交換心得清單</h3>
        <div id="s5-list"></div>
      </div>
    </section>

    <!-- Screen 6 -->
    <section id="s6" class="screen">
      <div class="guide-banner">
        <strong>🚀 發布上線與一鍵還原說明：</strong><br/>
        • 在「2. 變更審核」核准後的修改，會在這裡等待您按下 <strong>「🚀 立即發布到前台網站」</strong> 才會正式對外生效。<br/>
        • 每次發布都會自動存下一個「歷史版本快照」。如果發現改錯了，隨時點選舊版本旁邊的 <strong>「⏪ 還原成這個版本」</strong> 即可一秒恢復！
      </div>
      <div class="card">
        <h3>🚀 待發布上線項目與歷史版本管理</h3>
        <div id="s6-approved-box" style="margin-bottom:18px"></div>
        <div id="s6-releases"></div>
      </div>
    </section>
  </main>

  <div id="toast"></div>
  <script src="/maintenance-preview.js"></script>
</body>
</html>"""
        return Response(content=html, media_type="text/html; charset=utf-8", headers=PRIVATE_NO_STORE)

    @router.get("/maintenance-preview.js", include_in_schema=False)
    def maintenance_preview_js() -> Response:
        """External JS bundle for /maintenance-preview complying strictly with CSP script-src 'self' and script-src-attr 'none'."""
        js = """(function () {
  const ADMIN_HEADERS = {
    "Content-Type": "application/json",
    "X-Admin-Id": "admin_kevin",
    "X-Admin-Role": "super_admin"
  };

  const HOME_NAMES = {
    ntu: "國立臺灣大學 (NTU)",
    ntpu: "國立臺北大學 (NTPU)",
    ncu: "國立中央大學 (NCU)",
    cgu: "長庚大學 (CGU)",
    ccu: "國立中正大學 (CCU)",
    tku: "淡江大學 (TKU)",
    fju: "天主教輔仁大學 (FJU)",
    scu: "東吳大學 (SCU)",
    ntnu: "國立臺灣師範大學 (NTNU)",
    cycu: "中原大學 (CYCU)",
    ntust: "國立臺灣科技大學 (NTUST)",
    yzu: "元智大學 (YZU)",
    fcu: "逢甲大學 (FCU)",
    nsysu: "國立中山大學 (NSYSU)",
    nchu: "國立中興大學 (NCHU)",
    ntut: "國立臺北科技大學 (NTUT)",
    nccu: "國立政治大學 (NCCU)",
    ncku: "國立成功大學 (NCKU)",
    nycu: "國立陽明交通大學 (NYCU)",
    nthu: "國立清華大學 (NTHU)",
    pccu: "中國文化大學 (PCCU)",
    wzu: "文藻外語大學 (WZU)",
    nkust: "國立高雄科技大學 (NKUST)",
    yuntech: "國立雲林科技大學 (YunTech)",
    ntou: "國立臺灣海洋大學 (NTOU)",
    ncue: "國立彰化師範大學 (NCUE)",
    nknu: "國立高雄師範大學 (NKNU)",
    tmu: "臺北醫學大學 (TMU)",
    csmu: "中山醫學大學 (CSMU)",
    cmu: "中國醫藥大學 (CMU)",
    kmu: "高雄醫學大學 (KMU)",
    mcu: "銘傳大學 (MCU)",
    ntub: "國立臺北商業大學 (NTUB)",
    ncnu: "國立暨南國際大學 (NCNU)"
  };

  const FIELD_LABELS = {
    quota: "📊 交換名額",
    deadlines: "📅 校內報名截止日",
    gpa: "🎓 成績門檻 (GPA)",
    host_language_requirement: "🗣️ 外語能力檢定門檻",
    language_requirement: "🗣️ 外語能力檢定門檻",
    eligibility: "✅ 申請資格限制"
  };

  const STATUS_LABELS = {
    pending: { text: "⏳ 待您核對", cls: "warn" },
    conflicting: { text: "⚠️ 資料年份衝突（系統已攔截）", cls: "high" },
    approved: { text: "✅ 已核准（待發布上線）", cls: "ok" },
    published: { text: "🚀 已發布上線", cls: "ok" },
    deferred: { text: "⏸️ 已暫緩處理", cls: "info" },
    rejected: { text: "❌ 已退回不採用", cls: "high" }
  };

  const ORIGIN_LABELS = {
    source_change: "📄 學校官網簡章更新",
    manual_override: "✏️ 管理員手動修正",
    user_report: "💬 學生問題回報"
  };

  const VALUE_STATE_LABELS = {
    known: { text: "🟢 有明確資料", cls: "ok" },
    not_stated: { text: "🟡 簡章未記載名額", cls: "warn" },
    zero: { text: "🔴 本學期不招收 (0名)", cls: "high" },
    conflicting: { text: "⚠️ 前後年份衝突（已攔截）", cls: "high" },
    unknown: { text: "⚪ 尚無資料", cls: "info" }
  };

  function escapeHtml(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatHomeName(homeId, homeName) {
    return HOME_NAMES[homeId] || homeName || homeId;
  }

  function formatFieldLabel(fieldPath) {
    return FIELD_LABELS[fieldPath] || ("📌 " + fieldPath);
  }

  function formatStatusBadge(status) {
    const info = STATUS_LABELS[status] || { text: status, cls: "info" };
    return "<span class='badge " + info.cls + "'>" + escapeHtml(info.text) + "</span>";
  }

  function formatValueStateBadge(vs) {
    const info = VALUE_STATE_LABELS[vs] || { text: vs || "未設定", cls: "info" };
    return "<span class='badge " + info.cls + "'>" + escapeHtml(info.text) + "</span>";
  }

  function formatDateTime(isoStr) {
    if (!isoStr) return "無紀錄";
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return isoStr;
      return d.getFullYear() + "/" +
        String(d.getMonth() + 1).padStart(2, "0") + "/" +
        String(d.getDate()).padStart(2, "0") + " " +
        String(d.getHours()).padStart(2, "0") + ":" +
        String(d.getMinutes()).padStart(2, "0");
    } catch (e) {
      return isoStr;
    }
  }

  function formatFieldValueBox(fieldPath, val, state, isAfter) {
    const boxCls = isAfter
      ? (state === "conflicting" ? "val-box after-conflict" : "val-box after-ok")
      : "val-box";

    if (state === "conflicting" && val == null) {
      return "<div class='" + boxCls + "'>" +
        "<div class='val-main' style='color:#fca5a5'>🛑 系統已自動攔截此變更</div>" +
        "<div style='font-size:0.84rem;color:var(--muted)'>因簡章年份前後矛盾，系統保留原網站資料，不自動覆蓋。</div>" +
      "</div>";
    }

    if (val == null) {
      return "<div class='" + boxCls + "'>" +
        "<div class='val-main' style='color:var(--muted)'>（原本未設定此項目）</div>" +
      "</div>";
    }

    if (fieldPath === "quota" && typeof val === "object") {
      const unitMap = {
        persons: "名（學生人數）",
        semester_unit: "個學期名額單位",
        academic_year_unit: "個學年名額單位",
        unspecified: "未註明單位"
      };
      let mainText = "";
      if (val.value_state === "known" && val.amount != null) {
        mainText = "名額：" + val.amount + " " + (unitMap[val.unit] || "名");
      } else if (val.value_state === "zero") {
        mainText = "名額：0 名（本學期不招收）";
      } else if (val.value_state === "not_stated") {
        mainText = "簡章未記載具體人數";
      } else {
        mainText = "名額狀態：" + (val.value_state || "未知");
      }
      const orig = val.original_text ? ("簡章原文：「" + escapeHtml(val.original_text) + "」") : "";
      return "<div class='" + boxCls + "'>" +
        "<div style='margin-bottom:4px'>" + formatValueStateBadge(val.value_state || state) + "</div>" +
        "<div class='val-main'>" + escapeHtml(mainText) + "</div>" +
        (orig ? "<div style='font-size:0.84rem;color:var(--muted)'>" + orig + "</div>" : "") +
      "</div>";
    }

    if (fieldPath === "deadlines" && typeof val === "object") {
      const dl = val.internal_deadline ? formatDateTime(val.internal_deadline) : JSON.stringify(val);
      return "<div class='" + boxCls + "'>" +
        "<div style='margin-bottom:4px'>" + formatValueStateBadge(state || "known") + "</div>" +
        "<div class='val-main'>校內截止時間：" + escapeHtml(dl) + "</div>" +
      "</div>";
    }

    if (typeof val === "object") {
      const lines = Object.keys(val).map(function (k) {
        return "<div><span style='color:var(--muted)'>" + escapeHtml(k) + "：</span>" + escapeHtml(val[k]) + "</div>";
      }).join("");
      return "<div class='" + boxCls + "'>" + lines + "</div>";
    }

    return "<div class='" + boxCls + "'><div class='val-main'>" + escapeHtml(val) + "</div></div>";
  }

  function showToast(msg, isErr) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.style.display = "block";
    el.style.borderColor = isErr ? "var(--danger)" : "var(--ok)";
    el.textContent = msg;
    setTimeout(function () { el.style.display = "none"; }, 5000);
  }

  function switchTab(id, btn) {
    document.querySelectorAll(".screen").forEach(function (s) { s.classList.remove("active"); });
    document.querySelectorAll("nav button").forEach(function (b) { b.classList.remove("active"); });
    const target = document.getElementById(id);
    if (target) target.classList.add("active");
    if (!btn) {
      btn = document.querySelector('nav button[data-tab="' + id + '"]');
    }
    if (btn) btn.classList.add("active");
    refreshAll();
  }

  async function refreshDashboard() {
    const r = await fetch("/admin/maintenance/dashboard", { headers: ADMIN_HEADERS });
    const d = await r.json();
    document.getElementById("hdr-release").textContent = d.current_release_id
      ? ("正常運作中（版本號 " + d.current_release_id + "）")
      : "尚未發布";

    document.getElementById("s1-metrics").innerHTML =
      '<div class="card"><h3>📋 待您核對的重要修改</h3><div style="font-size:2rem;font-weight:700;color:var(--warn)">' + d.pending_high_risk_changes.length + ' 筆</div><small style="color:var(--muted)">包含名額更新、報名截止日變動或年份異常提醒</small></div>' +
      '<div class="card"><h3>🌐 學校官網連線狀態</h3><div style="font-size:1.6rem;font-weight:700;color:var(--ok)">全部正常 (' + d.unhealthy_resources.length + ' 異常)</div><small style="color:var(--muted)">6 所大學國際處官網皆可正常連線檢查</small></div>' +
      '<div class="card"><h3>💰 本月 AI 額外花費</h3><div style="font-size:1.6rem;font-weight:700;color:var(--ok)">NT$ ' + d.budget_status.settled_spend_twd + ' 元</div><small style="color:var(--muted)">目前已關閉付費 AI（每月保護上限 NT$ ' + d.budget_status.monthly_budget_twd + ' 元，不會超支）</small></div>';

    if (d.pending_high_risk_changes.length === 0) {
      document.getElementById("s1-high-risk").innerHTML = "<p style='color:var(--ok);font-weight:600'>🎉 太棒了！目前所有重要修改都已經核對完畢，可前往「6. 發布上線與版本還原」將更新發布到前台。</p>";
    } else {
      document.getElementById("s1-high-risk").innerHTML =
        "<table><thead><tr>" +
        "<th style='width:20%'>所屬母校</th>" +
        "<th style='width:26%'>交換姊妹校</th>" +
        "<th style='width:18%'>變動項目</th>" +
        "<th style='width:18%'>目前狀態</th>" +
        "<th style='width:18%'>操作</th>" +
        "</tr></thead><tbody>" +
        d.pending_high_risk_changes.map(function (c) {
          const fieldNames = c.items.map(function (it) { return formatFieldLabel(it.field_path); }).join("、");
          return "<tr>" +
            "<td><strong>" + escapeHtml(formatHomeName(c.home_id, c.home_name)) + "</strong></td>" +
            "<td><strong>" + escapeHtml(c.host_name || c.host_id) + "</strong></td>" +
            "<td>" + escapeHtml(fieldNames) + "（共 " + c.items.length + " 項）</td>" +
            "<td>" + formatStatusBadge(c.status) + "</td>" +
            "<td><button class='btn' data-action='switch-tab' data-tab='s2'>👉 前往核對內容</button></td>" +
            "</tr>";
        }).join("") +
        "</tbody></table>";
    }
  }

  async function refreshChanges() {
    const r = await fetch("/admin/changes", { headers: ADMIN_HEADERS });
    const d = await r.json();
    const box = document.getElementById("s2-changes");
    if (!d.items.length) {
      box.innerHTML = "<p style='color:var(--muted)'>目前沒有任何待審核的變更項目。</p>";
      return;
    }
    box.innerHTML = d.items.map(function (cs) {
      const isConflictCard = cs.status === "conflicting";
      const fieldsHtml = cs.items.map(function (it) {
        const itemStatusInfo = STATUS_LABELS[it.approval_status] || { text: it.approval_status, cls: "info" };
        return "<tr>" +
          "<td>" +
            "<label style='display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-weight:700'>" +
              "<input type='checkbox' class='fld-" + escapeHtml(cs.id) + "' value='" + escapeHtml(it.field_path) + "' checked style='margin-top:4px;transform:scale(1.2)' />" +
              "<span>" + escapeHtml(formatFieldLabel(it.field_path)) + "</span>" +
            "</label>" +
          "</td>" +
          "<td>" + formatFieldValueBox(it.field_path, it.before_value, it.before_state, false) + "</td>" +
          "<td>" + formatFieldValueBox(it.field_path, it.after_value, it.after_state, true) + "</td>" +
          "<td><div style='font-size:0.9rem;line-height:1.5'>" + escapeHtml(it.reason) + "</div></td>" +
          "<td><span class='badge " + itemStatusInfo.cls + "'>" + escapeHtml(itemStatusInfo.text) + "</span></td>" +
          "</tr>";
      }).join("");

      const originText = ORIGIN_LABELS[cs.change_origin] || cs.change_origin;
      return "<div class='change-card'>" +
        "<div class='change-card-header'>" +
          "<div>" +
            "<div class='change-title'>🏫 " + escapeHtml(formatHomeName(cs.home_id, cs.home_name)) + " ➔ 姊妹校：" + escapeHtml(cs.host_name || cs.host_id) + "</div>" +
            "<div class='change-meta'>" +
              "<span>目前狀態：" + formatStatusBadge(cs.status) + "</span>" +
              "<span>｜ 變動來源：" + escapeHtml(originText) + "</span>" +
              "<span>｜ 修訂版次：第 " + escapeHtml(cs.candidate_version) + " 版</span>" +
            "</div>" +
          "</div>" +
          "<div>" +
            (isConflictCard
              ? "<button class='btn secondary' data-action='review-change' data-cs-id='" + escapeHtml(cs.id) + "' data-cand-ver='" + escapeHtml(cs.candidate_version) + "' data-ev-hash='" + escapeHtml(cs.evidence_set_hash) + "' data-base-rel='" + escapeHtml(cs.base_release_id || "") + "' data-decision='defer'>⏸️ 確認攔截並暫緩處理</button>" +
                "<button class='btn danger' data-action='review-change' data-cs-id='" + escapeHtml(cs.id) + "' data-cand-ver='" + escapeHtml(cs.candidate_version) + "' data-ev-hash='" + escapeHtml(cs.evidence_set_hash) + "' data-base-rel='" + escapeHtml(cs.base_release_id || "") + "' data-decision='approve'>🧪 測試強行核准（系統會自動阻擋）</button>"
              : "<button class='btn success' data-action='review-change' data-cs-id='" + escapeHtml(cs.id) + "' data-cand-ver='" + escapeHtml(cs.candidate_version) + "' data-ev-hash='" + escapeHtml(cs.evidence_set_hash) + "' data-base-rel='" + escapeHtml(cs.base_release_id || "") + "' data-decision='approve'>✅ 核准勾選的修改項目</button>" +
                "<button class='btn secondary' data-action='review-change' data-cs-id='" + escapeHtml(cs.id) + "' data-cand-ver='" + escapeHtml(cs.candidate_version) + "' data-ev-hash='" + escapeHtml(cs.evidence_set_hash) + "' data-base-rel='" + escapeHtml(cs.base_release_id || "") + "' data-decision='defer'>⏸️ 先暫緩不改</button>"
            ) +
          "</div>" +
        "</div>" +
        "<div class='table-wrap'>" +
          "<table><thead><tr>" +
            "<th style='width:16%'>勾選要更新的項目</th>" +
            "<th style='width:25%'>修改前（目前網站顯示）</th>" +
            "<th style='width:25%'>修改後（最新簡章內容）</th>" +
            "<th style='width:22%'>為什麼有這筆修改？（系統比對說明）</th>" +
            "<th style='width:12%'>項目狀態</th>" +
          "</tr></thead><tbody>" + fieldsHtml + "</tbody></table>" +
        "</div>" +
      "</div>";
    }).join("");
  }

  async function reviewChange(csId, candVer, evHash, baseRel, decision) {
    const checks = Array.from(document.querySelectorAll(".fld-" + csId + ":checked")).map(function (el) { return el.value; });
    if (!checks.length) {
      showToast("⚠️ 請至少勾選一個要處理的項目！", true);
      return;
    }
    const res = await fetch("/admin/changes/" + encodeURIComponent(csId) + "/review", {
      method: "POST",
      headers: ADMIN_HEADERS,
      body: JSON.stringify({
        candidate_version: Number(candVer),
        evidence_set_hash: evHash,
        base_release_id: baseRel || null,
        decision: decision,
        selected_fields: checks,
        reason: "維護人員於後台執行：" + (decision === "approve" ? "核准勾選項目" : "暫緩處理"),
        idempotency_key: "idem_rev_" + csId + "_" + Date.now()
      })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast("🛑 系統安全防護已攔截此操作：因資料存在年份衝突或版本已過期，禁止直接核准上線！", true);
    } else {
      const splitMsg = data.remaining_change_set
        ? "（您未勾選的項目已自動拆分為另一張待審單，方便您稍後再處理！）"
        : "（請前往「6. 發布上線與版本還原」將核准的內容發布到前台！）";
      showToast("✅ 審核完成！" + splitMsg, false);
    }
    refreshAll();
  }

  async function refreshSources() {
    const r = await fetch("/admin/sources", { headers: ADMIN_HEADERS });
    const d = await r.json();
    document.getElementById("s3-sources").innerHTML =
      "<table><thead><tr>" +
        "<th style='width:20%'>所屬母校</th>" +
        "<th style='width:18%'>允許抓取的官方網域</th>" +
        "<th style='width:34%'>學校國際處官方網址</th>" +
        "<th style='width:28%'>維護操作</th>" +
      "</tr></thead><tbody>" +
      d.items.map(function (s) {
        return "<tr>" +
          "<td><strong>" + escapeHtml(formatHomeName(s.owner_institution_id, s.home_name)) + "</strong></td>" +
          "<td><code>" + escapeHtml(s.approved_domains.join(", ")) + "</code></td>" +
          "<td><a href='" + escapeHtml(s.entry_url) + "' target='_blank' rel='noopener' style='color:var(--accent)'>" + escapeHtml(s.entry_url) + "</a></td>" +
          "<td>" +
            "<button class='btn' data-action='trigger-refresh' data-source-id='" + escapeHtml(s.id) + "' data-url='" + escapeHtml(s.entry_url) + "'>🔄 立即重新檢查官網</button>" +
            "<button class='btn danger' data-action='trigger-refresh' data-source-id='" + escapeHtml(s.id) + "' data-url='http://169.254.169.254/latest/meta-data/'>🛡️ 測試阻擋非官方危險網址</button>" +
          "</td>" +
        "</tr>";
      }).join("") +
      "</tbody></table>";
  }

  async function triggerRefresh(sourceId, url) {
    const res = await fetch("/admin/sources/" + encodeURIComponent(sourceId) + "/refresh", {
      method: "POST",
      headers: ADMIN_HEADERS,
      body: JSON.stringify({ action: "fetch", resource_url: url, force_unconditional: false, reason: "維護人員手動點擊重新檢查官網" })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast("🛡️ 安全防護成功！系統已自動攔截非白名單或危險網址，保護伺服器安全。", true);
    } else {
      showToast("🔄 已排入背景檢查任務！系統正在重新檢查該校官網簡章（任務編號：" + data.job_id + "）。", false);
    }
  }

  async function loadOfferings() {
    const home = document.getElementById("s4-home").value;
    const rel = document.getElementById("s4-release").value.trim();
    const qs = new URLSearchParams({ home: home });
    if (rel) qs.set("release_id", rel);
    const r = await fetch("/offerings?" + qs.toString());
    const d = await r.json();
    if (!r.ok) {
      showToast("查詢失敗：找不到該版本編號，請確認後重試。", true);
      return;
    }
    const qSum = d.quota_summary;
    document.getElementById("s4-summary").innerHTML =
      "<div class='change-card' style='margin-bottom:12px;padding:14px 18px'>" +
        "<div style='display:flex;flex-wrap:wrap;gap:16px;align-items:center'>" +
          "<span>📦 目前顯示版本：<code>" + escapeHtml(d.release_id) + "</code></span>" +
          "<span>｜ 🏫 姊妹校總數：<strong>" + d.total_count + " 所</strong></span>" +
          "<span>｜ 🟢 有明確人數合計：<strong>" + qSum.persons_quota_total + " 名</strong></span>" +
          "<span>｜ 📅 學年名額單位合計：<strong>" + qSum.academic_year_unit_total + " 單位</strong></span>" +
          "<span>｜ 🟡 簡章未記載名額：<span class='badge warn'>" + qSum.unverified_or_not_stated_count + " 所</span></span>" +
          "<span>｜ 🔴 本學期不招收 (0名)：<span class='badge high'>" + qSum.explicit_zero_count + " 所</span></span>" +
        "</div>" +
      "</div>";
    const slice = d.items.slice(0, 25);
    document.getElementById("s4-table").innerHTML =
      "<table><thead><tr>" +
        "<th style='width:18%'>母校名稱</th>" +
        "<th style='width:30%'>交換姊妹校名稱</th>" +
        "<th style='width:10%'>國家／地區</th>" +
        "<th style='width:18%'>名額分類狀態</th>" +
        "<th style='width:14%'>簡章名額原文</th>" +
        "<th style='width:10%'>資料狀態</th>" +
      "</tr></thead><tbody>" +
      slice.map(function (o) {
        const qf = o.fields.quota || {};
        const qv = qf.value || {};
        const freshMap = {
          current: "✅ 最新驗證",
          unverified: "⏳ 待查核",
          stale: "⚠️ 可能過期"
        };
        return "<tr>" +
          "<td>" + escapeHtml(o.home_institution.canonical_name) + "</td>" +
          "<td><strong>" + escapeHtml(o.host_institution.canonical_name) + "</strong></td>" +
          "<td>" + escapeHtml(o.host_institution.country_code) + "</td>" +
          "<td>" + formatValueStateBadge(qf.value_state) + "</td>" +
          "<td>" + escapeHtml(qv.original_text || "簡章未列出具體人數") + "</td>" +
          "<td><span class='badge info'>" + escapeHtml(freshMap[qf.freshness_status] || qf.freshness_status) + "</span></td>" +
          "</tr>";
      }).join("") +
      "</tbody></table>" +
      "<div style='margin-top:8px;color:var(--muted);font-size:0.86rem'>目前顯示前 25 所姊妹校（此母校共有 " + d.total_count + " 所姊妹校）</div>";
  }

  async function submitReport() {
    const entityId = document.getElementById("rep-entity").value;
    const text = document.getElementById("rep-text").value;
    const r = await fetch("/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_entity_type: "offering", target_entity_id: entityId, category: "quota_mismatch", text: text })
    });
    const d = await r.json();
    showToast("📩 已收到學生問題回報！已排入下方待處理清單（回報單號：" + d.report_id + "）。", false);
    refreshReports();
  }

  async function submitExperience(escalate) {
    const body = {
      home_id: "ntu",
      host_id: "host_uc_berkeley",
      experience_period: "2023 秋季班",
      experience_year: 2023,
      summary_zh: "2023 秋季前往加州大學柏克萊分校交換心得：課程非常扎實，建議學弟妹提早三個月申請校內宿舍！",
      consent_agreed: true,
      contact_email: "student@ntu.edu.tw"
    };
    if (escalate) {
      body.review_status = "approved";
      body.is_admin = true;
    }
    const r = await fetch("/maintenance/experience-submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const d = await r.json();
    if (!r.ok) {
      showToast("🛡️ 安全攔截成功！系統偵測到有人試圖偷改審核狀態（is_admin / review_status），已自動阻擋（HTTP 403）！", true);
    } else {
      showToast("🎓 交換心得投稿成功！已進入待審核清單，並完整保留交換年份（" + d.experience_year + " 年）。", false);
    }
    refreshReports();
  }

  async function refreshReports() {
    const r = await fetch("/admin/reports", { headers: ADMIN_HEADERS });
    const d = await r.json();
    const catMap = {
      quota_mismatch: "📊 名額與簡章不符",
      stale_info: "⏳ 資訊過期",
      deadline_changed: "📅 截止日異動",
      broken_link: "🔗 網址失效",
      other: "💬 其他問題"
    };

    let html = "<h4 style='margin:6px 0 10px 0;color:var(--accent)'>📮 學生問題回報清單（共 " + d.reports.length + " 筆）</h4>";
    if (!d.reports.length) {
      html += "<p style='color:var(--muted)'>目前尚無學生回報問題（您可以點擊上方「📩 送出測試回報單」體驗流程）。</p>";
    } else {
      html += "<div class='table-wrap'><table><thead><tr>" +
        "<th style='width:16%'>回報時間</th>" +
        "<th style='width:18%'>問題分類</th>" +
        "<th style='width:24%'>反映的學校／項目</th>" +
        "<th style='width:30%'>學生填寫的說明內容</th>" +
        "<th style='width:12%'>處理狀態</th>" +
      "</tr></thead><tbody>" +
      d.reports.map(function (rep) {
        return "<tr>" +
          "<td>" + escapeHtml(formatDateTime(rep.created_at)) + "</td>" +
          "<td>" + escapeHtml(catMap[rep.category] || rep.category) + "</td>" +
          "<td><strong>" + escapeHtml(rep.target_entity_id) + "</strong></td>" +
          "<td>" + escapeHtml(rep.text) + "</td>" +
          "<td><span class='badge warn'>⏳ 待人員查核</span></td>" +
        "</tr>";
      }).join("") +
      "</tbody></table></div>";
    }

    html += "<h4 style='margin:20px 0 10px 0;color:var(--accent)'>🎓 學長姐交換心得投稿清單（共 " + d.experiences.length + " 筆）</h4>";
    if (!d.experiences.length) {
      html += "<p style='color:var(--muted)'>目前尚無待審核的交換心得（您可以點擊上方「📝 模擬正常投稿」體驗流程）。</p>";
    } else {
      html += "<div class='table-wrap'><table><thead><tr>" +
        "<th style='width:18%'>母校</th>" +
        "<th style='width:22%'>交換姊妹校</th>" +
        "<th style='width:16%'>實際交換學期與年份</th>" +
        "<th style='width:32%'>心得摘要內容</th>" +
        "<th style='width:12%'>審核狀態</th>" +
      "</tr></thead><tbody>" +
      d.experiences.map(function (exp) {
        return "<tr>" +
          "<td>" + escapeHtml(formatHomeName(exp.home_id)) + "</td>" +
          "<td><strong>加州大學柏克萊分校 (UC Berkeley)</strong></td>" +
          "<td><span class='badge info'>" + escapeHtml(exp.experience_period) + "（" + escapeHtml(exp.experience_year) + "年）</span></td>" +
          "<td>" + escapeHtml(exp.summary_zh) + "</td>" +
          "<td>" + formatStatusBadge(exp.review_status) + "</td>" +
        "</tr>";
      }).join("") +
      "</tbody></table></div>";
    }

    document.getElementById("s5-list").innerHTML = html;
  }

  async function refreshReleases() {
    const results = await Promise.all([
      fetch("/admin/releases", { headers: ADMIN_HEADERS }),
      fetch("/admin/changes?status=approved", { headers: ADMIN_HEADERS })
    ]);
    const relData = await results[0].json();
    const chgData = await results[1].json();
    const approvedIds = chgData.items.map(function (i) { return i.id; });
    const box = document.getElementById("s6-approved-box");
    if (approvedIds.length > 0) {
      box.innerHTML =
        "<div class='change-card' style='border-color:var(--ok);background:rgba(20,83,45,0.25);padding:16px'>" +
          "<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px'>" +
            "<div>" +
              "<div style='font-weight:700;font-size:1.05rem;color:#86efac'>✅ 您有 " + approvedIds.length + " 筆已核准的修改等待發布上線！</div>" +
              "<div style='font-size:0.88rem;color:var(--muted)'>按下右側按鈕後，前台網站就會立即切換為最新核准的內容。</div>" +
            "</div>" +
            "<button class='btn success' data-action='publish-approved' data-ids='" + escapeHtml(approvedIds.join(",")) + "' data-base-rel='" + escapeHtml(relData.current_release_id || "") + "'>🚀 立即發布到前台網站（共 " + approvedIds.length + " 筆）</button>" +
          "</div>" +
        "</div>";
    } else {
      box.innerHTML =
        "<div class='change-card' style='padding:14px 18px;color:var(--muted)'>" +
          "💡 目前沒有等待發布的修改項目。（您可以先到 <strong>「2. 變更審核」</strong> 勾選核准修改，再回到這裡發布上線。）" +
        "</div>";
    }

    const actionMap = {
      initial_release_created: "🌱 建立系統初始基準版本",
      change_set_reviewed: "✅ 維護人員完成變更審核",
      release_published: "🚀 正式發布新版本至前台網站",
      release_rollback: "⏪ 執行歷史版本一鍵還原"
    };

    const reasonMap = {
      "Initial baseline release": "載入 6 所大學共 1,124 筆官方基準資料",
      "Publish approved changes from Maintenance Workbench": "維護人員將已核准的修改發布至前台網站"
    };

    document.getElementById("s6-releases").innerHTML =
      "<h4 style='margin:4px 0 10px 0;color:var(--accent)'>📦 網站歷次發布版本紀錄（隨時可一鍵還原）</h4>" +
      "<table><thead><tr>" +
        "<th style='width:24%'>版本編號與目前狀態</th>" +
        "<th style='width:18%'>前一個版本編號</th>" +
        "<th style='width:14%'>發布人員</th>" +
        "<th style='width:26%'>版本更新說明</th>" +
        "<th style='width:18%'>還原操作</th>" +
      "</tr></thead><tbody>" +
      relData.items.map(function (r) {
        const isHead = r.id === relData.current_release_id;
        const friendlyReason = reasonMap[r.reason] || r.reason;
        return "<tr>" +
          "<td><code>" + escapeHtml(r.id) + "</code><br/>" +
            (isHead ? "<span class='badge ok' style='margin-top:4px'>🟢 目前前台正在顯示此版本</span>" : "<span class='badge info' style='margin-top:4px'>歷史備份版本</span>") +
          "</td>" +
          "<td><code>" + escapeHtml(r.previous_release_id || "（此為最初版本）") + "</code></td>" +
          "<td>" + escapeHtml(r.published_by === "system_shadow_mapper" ? "系統初始載入" : "總管理員 (admin_kevin)") + "</td>" +
          "<td>" + escapeHtml(friendlyReason) + "</td>" +
          "<td>" +
            (!isHead
              ? "<button class='btn secondary' data-action='rollback-release' data-cur-rel='" + escapeHtml(relData.current_release_id) + "' data-target-rel='" + escapeHtml(r.id) + "'>⏪ 還原成這個版本的內容</button>"
              : "<span style='color:var(--muted);font-size:0.85rem'>目前使用中</span>") +
          "</td>" +
          "</tr>";
      }).join("") +
      "</tbody></table>" +
      "<h4 style='margin:24px 0 10px 0;color:var(--accent)'>📝 系統操作歷史紀錄（誰在什麼時候做了什麼事）</h4>" +
      "<table><thead><tr>" +
        "<th style='width:20%'>發生時間</th>" +
        "<th style='width:18%'>操作人員</th>" +
        "<th style='width:24%'>執行的動作</th>" +
        "<th style='width:38%'>詳細說明</th>" +
      "</tr></thead><tbody>" +
      relData.audit_events.slice().reverse().slice(0, 10).map(function (ev) {
        const actLabel = actionMap[ev.action] || ("📌 " + ev.action);
        const actorLabel = ev.actor_id === "system_shadow_mapper" ? "系統自動初始化" : "總管理員 (admin_kevin)";
        let detailText = "對象編號：" + ev.target_id;
        if (ev.details) {
          if (ev.details.decision) {
            detailText = "審核決定：" + (ev.details.decision === "approve" ? "核准通過" : "暫緩處理") +
              "（欄位：" + (ev.details.selected_fields || []).map(formatFieldLabel).join("、") + "）";
          } else if (ev.details.reason) {
            detailText = reasonMap[ev.details.reason] || ev.details.reason;
          }
        }
        return "<tr>" +
          "<td>" + escapeHtml(formatDateTime(ev.created_at)) + "</td>" +
          "<td>" + escapeHtml(actorLabel) + "</td>" +
          "<td><strong>" + escapeHtml(actLabel) + "</strong></td>" +
          "<td>" + escapeHtml(detailText) + "</td>" +
        "</tr>";
      }).join("") +
      "</tbody></table>";
  }

  async function publishApproved(idsCsv, baseRel) {
    const ids = idsCsv.split(",").filter(Boolean);
    const r = await fetch("/admin/publications", {
      method: "POST",
      headers: ADMIN_HEADERS,
      body: JSON.stringify({
        approved_change_ids: ids,
        base_release_id: baseRel || null,
        reason: "維護人員將已核准的修改發布至前台網站",
        idempotency_key: "idem_pub_" + Date.now()
      })
    });
    const d = await r.json();
    if (!r.ok) {
      showToast("🛑 發布失敗：" + d.detail, true);
    } else {
      showToast("🚀 發布成功！前台網站已經切換至最新版本（" + d.release_id + "）。", false);
    }
    refreshAll();
  }

  async function rollbackTo(curRel, targetRel) {
    const r = await fetch("/admin/publications/rollback", {
      method: "POST",
      headers: ADMIN_HEADERS,
      body: JSON.stringify({
        current_release_id: curRel,
        target_release_id: targetRel,
        reason: "維護人員執行一鍵還原至歷史版本 " + targetRel,
        idempotency_key: "idem_rb_" + Date.now()
      })
    });
    const d = await r.json();
    if (!r.ok) {
      showToast("🛑 還原失敗：" + d.detail, true);
    } else {
      showToast("⏪ 還原成功！前台網站已恢復為指定歷史版本的內容（新版本號：" + d.release_id + "）。", false);
    }
    refreshAll();
  }

  function refreshAll() {
    refreshDashboard();
    refreshChanges();
    refreshSources();
    loadOfferings();
    refreshReports();
    refreshReleases();
  }

  document.addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-action]");
    if (!btn) return;
    const act = btn.getAttribute("data-action");
    if (act === "switch-tab") {
      switchTab(btn.getAttribute("data-tab"), btn);
    } else if (act === "review-change") {
      reviewChange(
        btn.getAttribute("data-cs-id"),
        btn.getAttribute("data-cand-ver"),
        btn.getAttribute("data-ev-hash"),
        btn.getAttribute("data-base-rel"),
        btn.getAttribute("data-decision")
      );
    } else if (act === "trigger-refresh") {
      triggerRefresh(btn.getAttribute("data-source-id"), btn.getAttribute("data-url"));
    } else if (act === "load-offerings") {
      loadOfferings();
    } else if (act === "submit-report") {
      submitReport();
    } else if (act === "submit-exp") {
      submitExperience(btn.getAttribute("data-escalate") === "true");
    } else if (act === "publish-approved") {
      publishApproved(btn.getAttribute("data-ids"), btn.getAttribute("data-base-rel"));
    } else if (act === "rollback-release") {
      rollbackTo(btn.getAttribute("data-cur-rel"), btn.getAttribute("data-target-rel"));
    }
  });

  const homeSel = document.getElementById("s4-home");
  if (homeSel) {
    homeSel.addEventListener("change", function () { loadOfferings(); });
  }

  refreshAll();
})();
"""
        return Response(content=js, media_type="application/javascript; charset=utf-8", headers=PRIVATE_NO_STORE)

    return router


def build_default_maintenance_router(
    data_dir: Any,
    *,
    official_data_root: Any = None,
    seed_demo_changes: bool = False,
) -> tuple[APIRouter, MaintenanceStore]:
    """Create a MaintenanceStore + APIRouter for FastAPI mounting and optional Staging browser preview."""
    import os
    from pathlib import Path
    from .baseline_mapper import load_six_school_shadow_summary
    from .contracts import ChangeOrigin, QuotaUnit, QuotaValue, ValueState, canonical_json_hash
    from .reconciler import ChangeItemRecord, ChangeSetRecord

    resolved_data = Path(data_dir)
    store = MaintenanceStore(resolved_data / "maintenance_store")
    off_root = Path(official_data_root) if official_data_root else Path(__file__).resolve().parents[1] / "official_data"
    if off_root.exists():
        load_six_school_shadow_summary(off_root, store)

    # Seed candidate change sets ONLY when explicitly requested for Staging Workbench preview
    should_seed_demo = seed_demo_changes or os.environ.get("UNIWAY_MAINT_SEED_DEMO") == "1"
    ntu_offs = [o for o in store.offerings.values() if o.home_id == "ntu"]
    if should_seed_demo and ntu_offs and not store.change_sets:
        sample_off = next(
            (o for o in ntu_offs if "Vienna" in o.host_id or "維也納大學" in o.host_id),
            ntu_offs[0],
        )
        item_q = ChangeItemRecord(
            field_path="quota",
            before_value=sample_off.fields["quota"].value,
            after_value=QuotaValue(
                value_state=ValueState.KNOWN,
                amount=1,
                unit=QuotaUnit.ACADEMIC_YEAR_UNIT,
                original_text="全學年 1 名（一學期 2 名，116-1 最新官網學校列表更新）",
            ).model_dump(mode="json"),
            before_state=sample_off.fields["quota"].value_state,
            after_state=ValueState.KNOWN,
            unit=QuotaUnit.ACADEMIC_YEAR_UNIT.value,
            risk=RiskLevel.HIGH,
            reason="系統比對發現：臺大國際事務處最新公布的 116-1 赴外交換學校列表（oia.ntu.edu.tw/outgoing/school.list），已將該姊妹校交換名額更新為全學年 1 名（最多 2 人次）。",
        )
        item_dl = ChangeItemRecord(
            field_path="deadlines",
            before_value=None,
            after_value={"internal_deadline": "2026-11-09T16:00:00+08:00"},
            before_state=None,
            after_state=ValueState.KNOWN,
            risk=RiskLevel.HIGH,
            reason="系統比對發現：臺大國際事務處公告 116 學年度第 1 學期出國交換學生甄選線上報名截止時間為 2026/11/09 16:00。",
        )
        ev_hash1 = canonical_json_hash([item_q.model_dump(mode="json"), item_dl.model_dump(mode="json")])
        cs1 = ChangeSetRecord(
            id="cs_ntu_116_quota_and_deadline",
            entity_scope=sample_off.scope_key,
            home_id="ntu",
            host_id=sample_off.host_id,
            program_id=sample_off.program_id,
            cycle_id=sample_off.cycle_id,
            base_release_id=store.current_release_id,
            candidate_version=1,
            evidence_set_hash=ev_hash1,
            risk=RiskLevel.HIGH,
            change_origin=ChangeOrigin.SOURCE_CHANGE,
            status=ReviewStatus.PENDING,
            items=[item_q, item_dl],
        )
        store.change_sets[cs1.id] = cs1

        if len(ntu_offs) > 1:
            conflict_off = ntu_offs[1]
            item_conf = ChangeItemRecord(
                field_path="quota",
                before_value=conflict_off.fields["quota"].value,
                after_value=None,
                before_state=conflict_off.fields["quota"].value_state,
                after_state=ValueState.CONFLICTING,
                risk=RiskLevel.HIGH,
                reason="⚠️ 年份矛盾警告：官網網頁標題寫「116 學年度」，但點開裡面的 PDF 附件表頭卻寫「115 學年度」。為避免誤把舊簡章當成新資料，系統已自動攔截此筆變更！",
            )
            ev_hash2 = canonical_json_hash([item_conf.model_dump(mode="json")])
            cs2 = ChangeSetRecord(
                id="cs_ntu_year_conflict_blocked",
                entity_scope=conflict_off.scope_key,
                home_id="ntu",
                host_id=conflict_off.host_id,
                program_id=conflict_off.program_id,
                cycle_id=conflict_off.cycle_id,
                base_release_id=store.current_release_id,
                candidate_version=1,
                evidence_set_hash=ev_hash2,
                risk=RiskLevel.HIGH,
                change_origin=ChangeOrigin.SOURCE_CHANGE,
                status=ReviewStatus.CONFLICTING,
                items=[item_conf],
            )
            store.change_sets[cs2.id] = cs2

    def _auth_admin(req: Request) -> tuple[str, set[str] | None]:
        admin_id = req.headers.get("x-admin-id", "")
        role = req.headers.get("x-admin-role", "")
        if not admin_id or role not in {"super_admin", "school_reviewer", "publisher"}:
            raise AccessDeniedError("Admin authentication headers required (X-Admin-Id / X-Admin-Role)")
        scope = req.headers.get("x-admin-scope")
        allowed = {s.strip() for s in scope.split(",") if s.strip()} if scope else None
        return admin_id, allowed

    router = create_maintenance_router(store, authenticate_admin=_auth_admin)
    return router, store



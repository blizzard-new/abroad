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

    @router.get("/admin/maintenance/dashboard")
    def admin_dashboard(request: Request, response: Response) -> dict[str, Any]:
        """Screen 1 (Spec 13.1): Today's work, high-risk pending changes, broken sources, disk/backup/budget status."""
        _, allowed_homes = _require_admin(request, response)
        pending_high = [
            cs.model_dump(mode="json")
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
            rows.append(cs.model_dump(mode="json"))
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
        return cs.model_dump(mode="json")

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
            "change_set": updated_cs.model_dump(mode="json"),
            "remaining_change_set": remaining_cs.model_dump(mode="json") if remaining_cs else None,
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
        srcs = [
            s.model_dump(mode="json")
            for s in store.sources.values()
            if allowed_homes is None or s.owner_institution_id in allowed_homes
        ]
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
  <title>UniWay 交換學校資訊維護系統 v1.1 — Staging 預覽工作台</title>
  <style>
    :root {
      --bg: #0f172a;
      --panel: #1e293b;
      --panel-alt: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --ok: #22c55e;
      --warn: #f59e0b;
      --danger: #ef4444;
      --border: #475569;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, "Microsoft JhengHei", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }
    header {
      background: #020617;
      border-bottom: 1px solid var(--border);
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }
    header h1 { margin: 0; font-size: 1.15rem; color: var(--accent); }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 600;
    }
    .badge.high { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid var(--danger); }
    .badge.ok { background: rgba(34,197,94,0.2); color: #86efac; border: 1px solid var(--ok); }
    .badge.warn { background: rgba(245,158,11,0.2); color: #fcd34d; border: 1px solid var(--warn); }
    nav {
      display: flex;
      gap: 8px;
      padding: 12px 24px;
      background: var(--panel);
      border-bottom: 1px solid var(--border);
      overflow-x: auto;
    }
    nav button {
      background: transparent;
      color: var(--muted);
      border: 1px solid var(--border);
      padding: 7px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      white-space: nowrap;
    }
    nav button.active {
      background: var(--accent);
      color: #020617;
      border-color: var(--accent);
    }
    main { padding: 20px 24px; max-width: 1400px; margin: 0 auto; }
    .screen { display: none; }
    .screen.active { display: block; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px; }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
    }
    .card h3 { margin-top: 0; font-size: 1rem; color: var(--accent); }
    button.btn {
      background: var(--accent);
      color: #020617;
      border: none;
      padding: 6px 12px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      margin-right: 6px;
    }
    button.btn.secondary { background: var(--panel-alt); color: var(--text); border: 1px solid var(--border); }
    button.btn.danger { background: var(--danger); color: #fff; }
    select, input[type="text"] {
      background: #020617;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 6px 10px;
      border-radius: 6px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { border-bottom: 1px solid var(--border); padding: 8px 10px; text-align: left; vertical-align: top; }
    th { color: var(--muted); font-weight: 600; }
    pre {
      background: #020617;
      padding: 10px;
      border-radius: 6px;
      overflow-x: auto;
      font-size: 0.82rem;
      border: 1px solid var(--border);
    }
    #toast {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #020617;
      border: 1px solid var(--accent);
      padding: 12px 18px;
      border-radius: 8px;
      display: none;
      max-width: 460px;
      z-index: 999;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>UniWay 交換學校資訊維護系統（v1.1 本地伺服器版）— Staging 預覽工作台</h1>
      <small style="color:var(--muted)">隔離預覽容器｜已載入 6 校（NTU / NTPU / NCU / CGU / CCU / TKU）共 1,124 筆 Offerings 影子基準</small>
    </div>
    <div>
      <span>目前公開 Release：<strong id="hdr-release" style="color:var(--ok)">載入中...</strong></span>
      <span style="margin-left:12px">管理員身分：<code>admin_kevin (super_admin)</code></span>
    </div>
  </header>

  <nav>
    <button class="active" onclick="switchTab('s1', this)">1. 今日工作頁</button>
    <button onclick="switchTab('s2', this)">2. 變更審核頁（逐欄核准／樂觀鎖）</button>
    <button onclick="switchTab('s3', this)">3. 來源管理頁（白名單／手動重抓）</button>
    <button onclick="switchTab('s4', this)">4. 學校與計畫主檔（6 校公開投影瀏覽）</button>
    <button onclick="switchTab('s5', this)">5. 心得審核與問題回報</button>
    <button onclick="switchTab('s6', this)">6. 發布與運維頁（原子發布／單校回滾）</button>
  </nav>

  <main>
    <!-- Screen 1 -->
    <section id="s1" class="screen active">
      <div class="grid" id="s1-metrics"></div>
      <div class="card">
        <h3>高風險待審變更集（High-Risk Pending / Conflicting ChangeSets）</h3>
        <div id="s1-high-risk"></div>
      </div>
    </section>

    <!-- Screen 2 -->
    <section id="s2" class="screen">
      <div class="card">
        <h3>候選變更集審核（支援部分欄位勾選核准 T28、過期證據 409 攔截 T14、衝突阻擋 T04）</h3>
        <div id="s2-changes"></div>
      </div>
    </section>

    <!-- Screen 3 -->
    <section id="s3" class="screen">
      <div class="card">
        <h3>6 校官方來源白名單與手動重新檢查（POST /admin/sources/{id}/refresh）</h3>
        <div id="s3-sources"></div>
      </div>
    </section>

    <!-- Screen 4 -->
    <section id="s4" class="screen">
      <div class="card">
        <h3>公開 Offerings 版本固定投影瀏覽器（GET /offerings）</h3>
        <div style="margin-bottom:12px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
          <label>選擇母校：</label>
          <select id="s4-home" onchange="loadOfferings()">
            <option value="ntu">國立臺灣大學 (ntu - 288 筆)</option>
            <option value="ntpu">國立臺北大學 (ntpu - 409 筆)</option>
            <option value="ncu">國立中央大學 (ncu - 214 筆)</option>
            <option value="cgu">長庚大學 (cgu - 154 筆)</option>
            <option value="ccu">國立中正大學 (ccu - 55 筆)</option>
            <option value="tku">淡江大學 (tku - 4 筆)</option>
          </select>
          <label>指定 Release ID（留空代表目前最新）：</label>
          <input type="text" id="s4-release" placeholder="例如 rel_..." style="width:220px" />
          <button class="btn" onclick="loadOfferings()">查詢公開投影</button>
        </div>
        <div id="s4-summary" style="margin-bottom:12px"></div>
        <div id="s4-table"></div>
      </div>
    </section>

    <!-- Screen 5 -->
    <section id="s5" class="screen">
      <div class="grid">
        <div class="card">
          <h3>送出公開問題回報（POST /reports）</h3>
          <p style="color:var(--muted);font-size:0.85rem">回報會綁定目前公開 release_id 進入待處理佇列，絕不直接改寫公開資料。</p>
          <input type="text" id="rep-entity" value="off_ntu_sample" style="width:100%;margin-bottom:8px" />
          <input type="text" id="rep-text" value="官方簡章名額已由 2 名更新為 4 名，請重新查核附件 PDF" style="width:100%;margin-bottom:8px" />
          <button class="btn" onclick="submitReport()">送出回報</button>
        </div>
        <div class="card">
          <h3>測試學生心得投稿與防提權攔截（POST /experience-submissions）</h3>
          <p style="color:var(--muted);font-size:0.85rem">驗證 T20（夾帶 is_admin/review_status 立即 403）與 T26（保留真實交換年份 2023）。</p>
          <button class="btn" onclick="submitExperience(false)">正常投稿（2023 年交換心得）</button>
          <button class="btn danger" onclick="submitExperience(true)">模擬惡意提權投稿（夾帶 review_status=approved）</button>
        </div>
      </div>
      <div class="card">
        <h3>待處理問題回報與心得佇列</h3>
        <div id="s5-list"></div>
      </div>
    </section>

    <!-- Screen 6 -->
    <section id="s6" class="screen">
      <div class="card">
        <h3>版本發布與單校回滾工作台（POST /admin/publications & /rollback）</h3>
        <p style="color:var(--muted);font-size:0.85rem">單人團隊模式下，同一管理員可先在「畫面 2」完成 Review 核准，再於此處執行 Publish 發布（系統自動分別寫入 review_decisions 與 releases 兩筆獨立稽核事件）。</p>
        <div id="s6-approved-box" style="margin-bottom:14px"></div>
        <div id="s6-releases"></div>
      </div>
    </section>
  </main>

  <div id="toast"></div>

  <script>
    const ADMIN_HEADERS = {
      "Content-Type": "application/json",
      "X-Admin-Id": "admin_kevin",
      "X-Admin-Role": "super_admin"
    };

    function showToast(msg, isErr = false) {
      const el = document.getElementById("toast");
      el.style.display = "block";
      el.style.borderColor = isErr ? "var(--danger)" : "var(--ok)";
      el.textContent = msg;
      setTimeout(() => { el.style.display = "none"; }, 4500);
    }

    function switchTab(id, btn) {
      document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
      document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
      document.getElementById(id).classList.add("active");
      btn.classList.add("active");
      refreshAll();
    }

    async function refreshDashboard() {
      const r = await fetch("/admin/maintenance/dashboard", { headers: ADMIN_HEADERS });
      const d = await r.json();
      document.getElementById("hdr-release").textContent = d.current_release_id || "none";
      document.getElementById("s1-metrics").innerHTML = `
        <div class="card"><h3>高風險待審變更</h3><div style="font-size:1.8rem;font-weight:700;color:var(--warn)">${d.pending_high_risk_changes.length}</div><small style="color:var(--muted)">需人工逐欄核准才可發布</small></div>
        <div class="card"><h3>異常來源數 / Dead-Letter</h3><div style="font-size:1.8rem;font-weight:700">${d.unhealthy_resources.length} / ${d.dead_letter_jobs.length}</div><small style="color:var(--muted)">HTTP 403/404/429 自動分類隔離</small></div>
        <div class="card"><h3>外部付費模型／OCR 預算</h3><div style="font-size:1.4rem;font-weight:700;color:var(--ok)">NT$ ${d.budget_status.settled_spend_twd} / ${d.budget_status.monthly_budget_twd}</div><small style="color:var(--muted)">預設關閉外部付費 AI（Opt-in: ${d.budget_status.external_ai_opted_in}）</small></div>
      `;
      if (d.pending_high_risk_changes.length === 0) {
        document.getElementById("s1-high-risk").innerHTML = "<p style='color:var(--muted)'>目前無高風險待審變更。</p>";
      } else {
        document.getElementById("s1-high-risk").innerHTML = `<table><thead><tr><th>ChangeSet ID</th><th>母校</th><th>風險</th><th>狀態</th><th>變更欄位數</th><th>來源類型</th></tr></thead><tbody>` +
          d.pending_high_risk_changes.map(c => `<tr><td><code>${c.id}</code></td><td>${c.home_id}</td><td><span class="badge high">${c.risk}</span></td><td>${c.status}</td><td>${c.items.length}</td><td>${c.change_origin}</td></tr>`).join("") +
          `</tbody></table>`;
      }
    }

    async function refreshChanges() {
      const r = await fetch("/admin/changes", { headers: ADMIN_HEADERS });
      const d = await r.json();
      const box = document.getElementById("s2-changes");
      if (!d.items.length) {
        box.innerHTML = "<p>無候選變更集。</p>";
        return;
      }
      box.innerHTML = d.items.map(cs => {
        const fieldsHtml = cs.items.map(it => `
          <tr>
            <td><input type="checkbox" class="fld-${cs.id}" value="${it.field_path}" checked /> <code>${it.field_path}</code></td>
            <td><code>${JSON.stringify(it.before_value)}</code> (${it.before_state || 'none'})</td>
            <td><code>${JSON.stringify(it.after_value)}</code> (<span class="badge ${it.after_state === 'conflicting' ? 'high' : 'ok'}">${it.after_state}</span>)</td>
            <td>${it.reason}</td>
            <td><strong>${it.approval_status}</strong></td>
          </tr>
        `).join("");
        return `
          <div class="card" style="background:#0f172a">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px">
              <div>
                <strong><code>${cs.id}</code></strong> ｜ 母校：<code>${cs.home_id}</code> ｜ 狀態：<span class="badge warn">${cs.status}</span>
                ｜ Version: <code>v${cs.candidate_version}</code> ｜ Base Release: <code>${cs.base_release_id}</code>
              </div>
              <div>
                <button class="btn" onclick='reviewChange(${JSON.stringify(cs.id)}, ${cs.candidate_version}, ${JSON.stringify(cs.evidence_set_hash)}, ${JSON.stringify(cs.base_release_id)}, "approve")'>核准勾選欄位 (Approve Selected)</button>
                <button class="btn secondary" onclick='reviewChange(${JSON.stringify(cs.id)}, ${cs.candidate_version}, ${JSON.stringify(cs.evidence_set_hash)}, ${JSON.stringify(cs.base_release_id)}, "defer")'>暫緩 (Defer)</button>
              </div>
            </div>
            <table>
              <thead><tr><th>勾選欄位</th><th>舊值 (Before)</th><th>新候選值 (After)</th><th>驗證矩陣與摘錄原因</th><th>欄位狀態</th></tr></thead>
              <tbody>${fieldsHtml}</tbody>
            </table>
          </div>
        `;
      }).join("");
    }

    async function reviewChange(csId, candVer, evHash, baseRel, decision) {
      const checks = Array.from(document.querySelectorAll(`.fld-${csId}:checked`)).map(el => el.value);
      if (!checks.length) {
        showToast("請至少勾選一個欄位！", true);
        return;
      }
      const res = await fetch(`/admin/changes/${csId}/review`, {
        method: "POST",
        headers: ADMIN_HEADERS,
        body: JSON.stringify({
          candidate_version: candVer,
          evidence_set_hash: evHash,
          base_release_id: baseRel,
          decision: decision,
          selected_fields: checks,
          reason: `Admin workbench ${decision} on fields: ${checks.join(",")}`,
          idempotency_key: `idem_rev_${csId}_${Date.now()}`
        })
      });
      const data = await res.json();
      if (!res.ok) {
        showToast(`審核遭攔截 (${res.status}): ${data.detail}`, true);
      } else {
        showToast(`審核成功！狀態：${data.change_set.status}` + (data.remaining_change_set ? `（未勾選欄位已自動拆為新待審卡 ${data.remaining_change_set.id}）` : ""));
      }
      refreshAll();
    }

    async function refreshSources() {
      const r = await fetch("/admin/sources", { headers: ADMIN_HEADERS });
      const d = await r.json();
      document.getElementById("s3-sources").innerHTML = `<table><thead><tr><th>Source ID</th><th>母校</th><th>允許網域白名單</th><th>入口 URL</th><th>操作</th></tr></thead><tbody>` +
        d.items.map(s => `
          <tr>
            <td><code>${s.id}</code></td>
            <td>${s.owner_institution_id}</td>
            <td><code>${s.approved_domains.join(", ")}</code></td>
            <td><a href="${s.entry_url}" target="_blank" style="color:var(--accent)">${s.entry_url}</a></td>
            <td>
              <button class="btn" onclick="triggerRefresh('${s.id}', '${s.entry_url}')">排入重抓佇列</button>
              <button class="btn danger" onclick="triggerRefresh('${s.id}', 'http://169.254.169.254/latest/meta-data/')">測試 SSRF 阻擋 (T21)</button>
            </td>
          </tr>
        `).join("") + `</tbody></table>`;
    }

    async function triggerRefresh(sourceId, url) {
      const res = await fetch(`/admin/sources/${sourceId}/refresh`, {
        method: "POST",
        headers: ADMIN_HEADERS,
        body: JSON.stringify({ action: "fetch", resource_url: url, force_unconditional: false, reason: "Staging UI manual check" })
      });
      const data = await res.json();
      if (!res.ok) {
        showToast(`安全策略攔截 (${res.status}): ${data.detail}`, true);
      } else {
        showToast(`已排入佇列！Job ID: ${data.job_id} (${data.status})`);
      }
    }

    async function loadOfferings() {
      const home = document.getElementById("s4-home").value;
      const rel = document.getElementById("s4-release").value.trim();
      const qs = new URLSearchParams({ home });
      if (rel) qs.set("release_id", rel);
      const r = await fetch(`/offerings?${qs.toString()}`);
      const d = await r.json();
      if (!r.ok) {
        showToast(`查詢失敗: ${d.detail}`, true);
        return;
      }
      const qSum = d.quota_summary;
      document.getElementById("s4-summary").innerHTML = `
        <div class="card" style="background:#0f172a;margin-bottom:10px">
          <strong>固定版本 Release ID：<code>${d.release_id}</code></strong> ｜ 總筆數：<strong>${d.total_count}</strong>
          ｜ 明確人數名額合計 (persons)：<strong>${qSum.persons_quota_total}</strong>
          ｜ 學年名額單位合計 (academic_year_unit)：<strong>${qSum.academic_year_unit_total}</strong>
          ｜ 未載明名額學校數 (not_stated)：<span class="badge warn">${qSum.unverified_or_not_stated_count}</span>
          ｜ 明確 0 名額數 (zero)：<span class="badge high">${qSum.explicit_zero_count}</span>
        </div>
      `;
      const slice = d.items.slice(0, 25);
      document.getElementById("s4-table").innerHTML = `<table><thead><tr><th>Offering ID</th><th>母校</th><th>姊妹校 (Host Canonical Name)</th><th>國家</th><th>名額狀態 (value_state)</th><th>原始名額文字</th><th>新鮮度 / 驗證狀態</th></tr></thead><tbody>` +
        slice.map(o => {
          const qf = o.fields.quota || {};
          const qv = qf.value || {};
          return `<tr>
            <td><code>${o.offering_id}</code></td>
            <td>${o.home_institution.canonical_name}</td>
            <td>${o.host_institution.canonical_name}</td>
            <td>${o.host_institution.country_code}</td>
            <td><span class="badge ${qf.value_state === 'known' ? 'ok' : (qf.value_state === 'zero' ? 'high' : 'warn')}">${qf.value_state}</span></td>
            <td>${qv.original_text || '未記載'}</td>
            <td><code>${qf.freshness_status}</code></td>
          </tr>`;
        }).join("") + `</tbody></table><small style="color:var(--muted)">顯示前 25 筆（共 ${d.total_count} 筆）</small>`;
    }

    async function submitReport() {
      const entityId = document.getElementById("rep-entity").value;
      const text = document.getElementById("rep-text").value;
      const r = await fetch("/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_entity_type: "offering", target_entity_id: entityId, category: "quota_mismatch", text })
      });
      const d = await r.json();
      showToast(`問題回報已建立：${d.report_id} (${d.status})`);
      refreshReports();
    }

    async function submitExperience(escalate) {
      const body = {
        home_id: "ntu",
        host_id: "host_uc_berkeley",
        experience_period: "2023 Fall",
        experience_year: 2023,
        summary_zh: "2023 秋季交換心得：課程扎實，建議提早申請宿舍。",
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
        showToast(`防提權防護成功攔截 (${r.status}): ${d.detail}`, true);
      } else {
        showToast(`投稿成功进入待審！ID: ${d.experience_id}，保留真實年份：${d.experience_year}`);
      }
      refreshReports();
    }

    async function refreshReports() {
      const r = await fetch("/admin/reports", { headers: ADMIN_HEADERS });
      const d = await r.json();
      document.getElementById("s5-list").innerHTML = `<pre>${JSON.stringify(d, null, 2)}</pre>`;
    }

    async function refreshReleases() {
      const [relRes, chgRes] = await Promise.all([
        fetch("/admin/releases", { headers: ADMIN_HEADERS }),
        fetch("/admin/changes?status=approved", { headers: ADMIN_HEADERS })
      ]);
      const relData = await relRes.json();
      const chgData = await chgRes.json();
      const approvedIds = chgData.items.map(i => i.id);
      const box = document.getElementById("s6-approved-box");
      if (approvedIds.length > 0) {
        box.innerHTML = `<button class="btn" onclick='publishApproved(${JSON.stringify(approvedIds)}, ${JSON.stringify(relData.current_release_id)})'>原子發布已核准變更集 (${approvedIds.join(", ")})</button>`;
      } else {
        box.innerHTML = `<span style="color:var(--muted)">目前無已核准待發布之 ChangeSet（請先至「畫面 2」核准候選變更）。</span>`;
      }
      document.getElementById("s6-releases").innerHTML = `<table><thead><tr><th>Release ID</th><th>前版 Release</th><th>發布者</th><th>原因</th><th>狀態</th><th>操作</th></tr></thead><tbody>` +
        relData.items.map(r => `
          <tr>
            <td><code>${r.id}</code> ${r.id === relData.current_release_id ? '<span class="badge ok">CURRENT HEAD</span>' : ''}</td>
            <td><code>${r.previous_release_id || '-'}</code></td>
            <td>${r.published_by}</td>
            <td>${r.reason}</td>
            <td>${r.status}</td>
            <td>${r.id !== relData.current_release_id ? `<button class="btn secondary" onclick="rollbackTo('${relData.current_release_id}', '${r.id}')">以新 Release 回復至此版本 (T18)</button>` : ''}</td>
          </tr>
        `).join("") + `</tbody></table>
        <h4 style="margin-top:16px">最近稽核軌跡 (Audit Events)</h4>
        <pre>${JSON.stringify(relData.audit_events.slice(-8), null, 2)}</pre>`;
    }

    async function publishApproved(ids, baseRel) {
      const r = await fetch("/admin/publications", {
        method: "POST",
        headers: ADMIN_HEADERS,
        body: JSON.stringify({
          approved_change_ids: ids,
          base_release_id: baseRel,
          reason: "Publish approved changes from Staging Workbench",
          idempotency_key: `idem_pub_${Date.now()}`
        })
      });
      const d = await r.json();
      if (!r.ok) {
        showToast(`發布失敗 (${r.status}): ${d.detail}`, true);
      } else {
        showToast(`原子發布成功！新 Release Head: ${d.release_id}`);
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
          reason: `Rollback to ${targetRel} from Staging Workbench`,
          idempotency_key: `idem_rb_${Date.now()}`
        })
      });
      const d = await r.json();
      if (!r.ok) {
        showToast(`回滾失敗 (${r.status}): ${d.detail}`, true);
      } else {
        showToast(`回滾完成！已建立新 Release: ${d.release_id}`);
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

    refreshAll();
  </script>
</body>
</html>"""
        return Response(content=html, media_type="text/html; charset=utf-8", headers=PRIVATE_NO_STORE)

    return router


def build_default_maintenance_router(
    data_dir: Any,
    *,
    official_data_root: Any = None,
) -> tuple[APIRouter, MaintenanceStore]:
    """Create a pre-seeded MaintenanceStore + APIRouter for FastAPI mounting and Staging browser preview."""
    from pathlib import Path
    from .baseline_mapper import load_six_school_shadow_summary
    from .contracts import ChangeOrigin, QuotaUnit, QuotaValue, ValueState, canonical_json_hash
    from .reconciler import ChangeItemRecord, ChangeSetRecord

    resolved_data = Path(data_dir)
    store = MaintenanceStore(resolved_data / "maintenance_store")
    off_root = Path(official_data_root) if official_data_root else Path(__file__).resolve().parents[1] / "official_data"
    if off_root.exists():
        load_six_school_shadow_summary(off_root, store)

    # Seed 2 realistic candidate change sets for Staging Workbench preview if none exist
    ntu_offs = [o for o in store.offerings.values() if o.home_id == "ntu"]
    if ntu_offs and not store.change_sets:
        sample_off = ntu_offs[0]
        item_q = ChangeItemRecord(
            field_path="quota",
            before_value=sample_off.fields["quota"].value,
            after_value=QuotaValue(
                value_state=ValueState.KNOWN,
                amount=4,
                unit=QuotaUnit.PERSONS,
                original_text="4 名（116-1 最新簡章附件更新）",
            ).model_dump(mode="json"),
            before_state=sample_off.fields["quota"].value_state,
            after_state=ValueState.KNOWN,
            unit="persons",
            risk=RiskLevel.HIGH,
            reason="國立臺灣大學國際事務處 116-1 最新簡章 PDF 第 1 頁表格更新名額為 4 名",
        )
        item_dl = ChangeItemRecord(
            field_path="deadlines",
            before_value=None,
            after_value={"internal_deadline": "2026-11-25T17:00:00+08:00"},
            before_state=None,
            after_state=ValueState.KNOWN,
            risk=RiskLevel.HIGH,
            reason="校內甄選系統報名截止日更新為 2026/11/25 17:00",
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
                reason="Time/Cycle mismatch: 列表頁標示 116 學年度，但附件 PDF 表頭標示 115 學年度（依規格 T04 自動攔截不升為 current）",
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



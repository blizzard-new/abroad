#!/usr/bin/env python3
"""Validate migrations and encrypted-object cleanup against isolated Supabase services.

The harness owns one generated validation-only Docker Compose project, uses
loopback-only random host ports and stores PostgreSQL data in tmpfs.  It does
not contact or mutate a configured Supabase project, and it never reads
application production secrets.
"""

from __future__ import annotations

import argparse
import base64
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
from http.client import RemoteDisconnected
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
from threading import Barrier
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from exchange_info.repositories import (  # noqa: E402
    AccountDeletionMutationRequest,
    account_deletion_mutation_fingerprint,
)
from exchange_info.community_repositories import (  # noqa: E402
    CommunityBlockMutationRequest,
    CommunityReportMutationRequest,
    CommunityReportReviewMutationRequest,
    PrivateConversationMutationRequest,
    PrivateMessageMutationRequest,
    PublicCommunityDeleteRequest,
    PublicCommunityModerationRequest,
    PublicCommunityPublicationRequest,
    PublicCommunityResourceType,
    community_mutation_fingerprint,
    private_community_mutation_fingerprint,
    public_community_publication_fingerprint,
)
from exchange_info.document_vault import (  # noqa: E402
    DEFAULT_VAULT_BUCKET,
    DocumentVaultService,
    SupabaseDocumentVaultRepository,
)
from exchange_info.models import (  # noqa: E402
    CommunityBlock,
    CommunityBoardKind,
    CommunityIdentityMode,
    CommunityPost,
    CommunityPostComment,
    CommunityPostType,
    CommunityReport,
    CommunityReportStatus,
    CommunityTopic,
    ConversationStatus,
    ModerationStatus,
    PrivateConversation,
    PrivateMessage,
)
from exchange_info.workflow_issue_reports import (  # noqa: E402
    ISSUE_REPORT_RATE_LIMIT,
    ISSUE_REPORT_RATE_WINDOW,
    canonical_issue_report_fingerprint,
)


COMPOSE_FILE = PROJECT_ROOT / "supabase" / "runtime-validation" / "docker-compose.yml"
MIGRATIONS_DIR = PROJECT_ROOT / "supabase" / "migrations"
PROJECT_NAME_PREFIX = "exchange-supabase-runtime"
DOCKER_INFO_TIMEOUT_SECONDS = 30.0
COMPOSE_START_TIMEOUT_SECONDS = 600.0
COMPOSE_CONTROL_TIMEOUT_SECONDS = 120.0
COMPOSE_LOG_TIMEOUT_SECONDS = 30.0
PSQL_TIMEOUT_SECONDS = 120.0
POSTGRES_PROBE_TIMEOUT_SECONDS = 10.0
DB_PASSWORD = "exchange-runtime-validation-only"
JWT_SECRET = "exchange-runtime-validation-jwt-secret-32-bytes"
RUNTIME_VAULT_BUCKET = DEFAULT_VAULT_BUCKET
ACCOUNT_DELETION_OBJECT_KEY = "vault/runtime-deletion/object.cipher"


class RuntimeValidationError(RuntimeError):
    """Raised when the isolated runtime contradicts a required invariant."""


@dataclass(frozen=True)
class HttpResult:
    status: int
    payload: Any


@dataclass(frozen=True)
class ValidationContext:
    project_name: str
    postgres_port: int
    postgrest_port: int
    postgrest_secondary_port: int
    storage_port: int
    service_token: str
    anon_token: str

    @property
    def postgrest_url(self) -> str:
        return f"http://127.0.0.1:{self.postgrest_port}"

    @property
    def postgrest_secondary_url(self) -> str:
        return f"http://127.0.0.1:{self.postgrest_secondary_port}"

    @property
    def storage_url(self) -> str:
        return f"http://127.0.0.1:{self.storage_port}"

    @property
    def compose_environment(self) -> dict[str, str]:
        return {
            "EXCHANGE_RUNTIME_DB_PASSWORD": DB_PASSWORD,
            "EXCHANGE_RUNTIME_JWT_SECRET": JWT_SECRET,
            "EXCHANGE_RUNTIME_POSTGRES_PORT": str(self.postgres_port),
            "EXCHANGE_RUNTIME_POSTGREST_PORT": str(self.postgrest_port),
            "EXCHANGE_RUNTIME_POSTGREST_SECONDARY_PORT": str(
                self.postgrest_secondary_port
            ),
            "EXCHANGE_RUNTIME_STORAGE_PORT": str(self.storage_port),
            "EXCHANGE_RUNTIME_SERVICE_KEY": self.service_token,
            "EXCHANGE_RUNTIME_ANON_KEY": self.anon_token,
        }


def _run(
    command: list[str],
    *,
    timeout_seconds: float,
    input_text: str | None = None,
    environment: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    merged_environment = os.environ.copy()
    if environment:
        merged_environment.update(environment)
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            input=input_text,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=merged_environment,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeValidationError(
            f"Command timed out after {timeout_seconds:g} seconds: {' '.join(command)}"
        ) from error
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeValidationError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n{detail}"
        )
    return completed


def _compose(
    context: ValidationContext,
    *arguments: str,
    check: bool = True,
    timeout_seconds: float = COMPOSE_CONTROL_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "-p",
            context.project_name,
            *arguments,
        ],
        timeout_seconds=timeout_seconds,
        environment=context.compose_environment,
        check=check,
    )


def _psql(context: ValidationContext, sql: str, *, user: str = "postgres") -> str:
    completed = _compose_with_input(
        context,
        [
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            user,
            "-d",
            "postgres",
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-A",
            "-t",
            "-F",
            "|",
        ],
        sql,
    )
    return completed.stdout.strip()


def _compose_with_input(
    context: ValidationContext,
    arguments: list[str],
    input_text: str,
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "-p",
            context.project_name,
            *arguments,
        ],
        timeout_seconds=PSQL_TIMEOUT_SECONDS,
        input_text=input_text,
        environment=context.compose_environment,
    )


def _apply_migrations(context: ValidationContext) -> int:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        raise RuntimeValidationError("No Supabase migrations were found.")
    for migration in migration_files:
        _compose_with_input(
            context,
            [
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "postgres",
                "-d",
                "postgres",
                "-X",
                "-v",
                "ON_ERROR_STOP=1",
            ],
            migration.read_text(encoding="utf-8"),
        )
        print(f"  migration applied: {migration.name}")
    return len(migration_files)


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _jwt(role: str, *, now: datetime | None = None) -> str:
    issued_at = now or datetime.now(UTC)
    header = _base64url(b'{"alg":"HS256","typ":"JWT"}')
    payload = _base64url(
        json.dumps(
            {
                "role": role,
                "iat": int(issued_at.timestamp()),
                "exp": int((issued_at + timedelta(hours=1)).timestamp()),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    unsigned = f"{header}.{payload}"
    signature = _base64url(
        hmac.new(JWT_SECRET.encode("utf-8"), unsigned.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{unsigned}.{signature}"


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: Any = None,
    timeout: float = 20.0,
) -> HttpResult:
    body = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        status = int(error.code)
        raw = error.read().decode("utf-8")
    except (ConnectionResetError, RemoteDisconnected, TimeoutError, URLError) as error:
        raise RuntimeValidationError(f"HTTP request failed for {url}: {error}") from error
    try:
        decoded = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        decoded = raw
    return HttpResult(status=status, payload=decoded)


def _rpc(
    context: ValidationContext,
    name: str,
    payload: dict[str, Any],
    *,
    secondary: bool = False,
) -> HttpResult:
    base_url = (
        context.postgrest_secondary_url if secondary else context.postgrest_url
    )
    return _http_json(
        "POST",
        f"{base_url}/rpc/{name}",
        token=context.service_token,
        payload=payload,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeValidationError(message)


def _wait_for_postgres(context: ValidationContext, timeout: float = 120.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = _compose(
            context,
            "exec",
            "-T",
            "postgres",
            "pg_isready",
            "-U",
            "postgres",
            "-h",
            "localhost",
            check=False,
            timeout_seconds=POSTGRES_PROBE_TIMEOUT_SECONDS,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeValidationError("PostgreSQL did not become ready within 120 seconds.")


def _wait_for_postgrest(
    context: ValidationContext,
    *,
    secondary: bool = False,
    timeout: float = 60.0,
) -> None:
    base_url = (
        context.postgrest_secondary_url if secondary else context.postgrest_url
    )
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = _http_json("GET", base_url, timeout=2)
            if result.status == 200:
                return
        except RuntimeValidationError:
            pass
        time.sleep(1)
    instance = "secondary PostgREST" if secondary else "primary PostgREST"
    raise RuntimeValidationError(f"{instance} did not become ready within 60 seconds.")


def _wait_for_storage(context: ValidationContext, timeout: float = 120.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = _http_json("GET", f"{context.storage_url}/status", timeout=2)
            if result.status == 200:
                return
        except RuntimeValidationError:
            pass
        time.sleep(1)
    raise RuntimeValidationError("Supabase Storage did not become ready within 120 seconds.")


def _runtime_supabase_request(
    context: ValidationContext,
    method: str,
    url: str,
    **kwargs: Any,
) -> requests.Response:
    """Route the production repository's gateway paths to isolated services."""

    parsed = urlsplit(url)
    if parsed.path.startswith("/rest/v1"):
        base_url = context.postgrest_url
        path = parsed.path.removeprefix("/rest/v1") or "/"
    elif parsed.path.startswith("/storage/v1"):
        base_url = context.storage_url
        path = parsed.path.removeprefix("/storage/v1") or "/"
    else:
        raise RuntimeValidationError(f"Unexpected runtime Supabase path: {parsed.path}")
    target = f"{base_url}{path}"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    return requests.request(method, target, **kwargs)


def _create_runtime_vault_repository(
    context: ValidationContext,
) -> SupabaseDocumentVaultRepository:
    repository = SupabaseDocumentVaultRepository(
        "https://runtime-supabase.invalid",
        context.service_token,
        bucket=RUNTIME_VAULT_BUCKET,
        request_func=lambda method, url, **kwargs: _runtime_supabase_request(
            context,
            method,
            url,
            **kwargs,
        ),
    )
    response = repository._request(  # noqa: SLF001 - isolated harness setup
        "POST",
        "/storage/v1/bucket",
        headers={"Content-Type": "application/json"},
        json={
            "id": RUNTIME_VAULT_BUCKET,
            "name": RUNTIME_VAULT_BUCKET,
            "public": False,
        },
    )
    _require(response.status_code == 200, "Runtime private Storage bucket was not created.")
    repository._ensure_private_bucket()  # noqa: SLF001 - verify production invariant
    return repository


def _object_is_missing(
    repository: SupabaseDocumentVaultRepository,
    object_key: str,
) -> bool:
    try:
        repository.read_object(object_key)
    except requests.HTTPError as error:
        if error.response is None or error.response.status_code not in {400, 404}:
            return False
        try:
            payload = error.response.json()
        except requests.JSONDecodeError:
            return False
        return isinstance(payload, dict) and (
            payload.get("statusCode") in {404, "404"}
            and payload.get("error") == "not_found"
            and payload.get("message") == "Object not found"
        )
    return False


def _validate_schema_and_permissions(context: ValidationContext) -> dict[str, int]:
    rls = _psql(
        context,
        """
select count(*), count(*) filter (where c.relrowsecurity)
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relkind = 'r'
  and (
    c.relname like 'exchange_%'
    or c.relname in (
      'application_workflow_issue_reports',
      'application_workflow_issue_report_reviews'
    )
  );
""",
    ).split("|")
    total_tables, rls_tables = (int(value) for value in rls)
    _require(total_tables >= 32, f"Expected at least 32 project tables, found {total_tables}.")
    _require(total_tables == rls_tables, f"RLS is enabled on {rls_tables}/{total_tables} tables.")

    browser_grants = int(
        _psql(
            context,
            """
select count(*)
from information_schema.role_table_grants
where table_schema = 'public'
  and (
    table_name like 'exchange_%'
    or table_name in (
      'application_workflow_issue_reports',
      'application_workflow_issue_report_reviews'
    )
  )
  and grantee in ('anon', 'authenticated');
""",
        )
    )
    _require(browser_grants == 0, f"Browser roles still have {browser_grants} direct grants.")

    privilege_row = _psql(
        context,
        """
select
  has_table_privilege('service_role', 'public.exchange_accounts', 'UPDATE'),
  has_table_privilege('service_role', 'public.exchange_accounts', 'DELETE'),
  has_table_privilege('service_role', 'public.exchange_account_workspaces', 'UPDATE'),
  has_table_privilege('service_role', 'public.exchange_community_questions', 'DELETE'),
  has_table_privilege('service_role', 'public.exchange_account_deletion_receipts', 'SELECT'),
  has_table_privilege('service_role', 'public.application_workflow_issue_reports', 'SELECT'),
  has_table_privilege('service_role', 'public.application_workflow_issue_reports', 'INSERT'),
  has_table_privilege('service_role', 'public.application_workflow_issue_reports', 'UPDATE'),
  has_table_privilege('service_role', 'public.application_workflow_issue_reports', 'DELETE'),
  has_table_privilege('service_role', 'public.application_workflow_issue_report_reviews', 'SELECT'),
  has_table_privilege('service_role', 'public.application_workflow_issue_report_reviews', 'INSERT'),
  has_table_privilege('service_role', 'public.application_workflow_issue_report_reviews', 'UPDATE'),
  has_table_privilege('service_role', 'public.application_workflow_issue_report_reviews', 'DELETE');
""",
    )
    _require(
        privilege_row == "f|f|f|f|f|t|f|f|f|t|f|f|f",
        f"Sensitive service-role grants changed: {privilege_row}",
    )

    workflow_issue_rpc_privileges = _psql(
        context,
        """
select
  has_function_privilege('anon', 'public.exchange_submit_application_workflow_issue_report(text,text,text,jsonb,integer,integer)', 'EXECUTE'),
  has_function_privilege('authenticated', 'public.exchange_submit_application_workflow_issue_report(text,text,text,jsonb,integer,integer)', 'EXECUTE'),
  has_function_privilege('service_role', 'public.exchange_submit_application_workflow_issue_report(text,text,text,jsonb,integer,integer)', 'EXECUTE'),
  has_function_privilege('anon', 'public.exchange_review_application_workflow_issue_report(text,text,text,jsonb)', 'EXECUTE'),
  has_function_privilege('authenticated', 'public.exchange_review_application_workflow_issue_report(text,text,text,jsonb)', 'EXECUTE'),
  has_function_privilege('service_role', 'public.exchange_review_application_workflow_issue_report(text,text,text,jsonb)', 'EXECUTE'),
  has_function_privilege('anon', 'public.exchange_purge_expired_application_workflow_issue_reports()', 'EXECUTE'),
  has_function_privilege('authenticated', 'public.exchange_purge_expired_application_workflow_issue_reports()', 'EXECUTE'),
  has_function_privilege('service_role', 'public.exchange_purge_expired_application_workflow_issue_reports()', 'EXECUTE'),
  has_function_privilege('service_role', 'public.exchange_deidentify_application_workflow_issue_reports()', 'EXECUTE');
""",
    )
    _require(
        workflow_issue_rpc_privileges == "f|f|t|f|f|t|f|f|t|f",
        "Workflow issue report RPC grants changed: "
        f"{workflow_issue_rpc_privileges}",
    )

    anon_get = _http_json("GET", f"{context.postgrest_url}/exchange_accounts?select=id")
    _require(anon_get.status == 401, f"Anonymous direct account read returned {anon_get.status}.")
    service_get = _http_json(
        "GET",
        f"{context.postgrest_url}/exchange_accounts?select=id",
        token=context.service_token,
    )
    _require(service_get.status == 200 and service_get.payload == [], "Service account read failed.")

    for table, key in (
        ("exchange_accounts", "id"),
        ("exchange_account_workspaces", "account_id"),
        ("exchange_community_questions", "id"),
        ("exchange_community_private_messages", "id"),
        ("exchange_account_deletion_receipts", "mutation_id"),
        ("application_workflow_issue_reports", "id"),
        ("application_workflow_issue_report_reviews", "id"),
    ):
        result = _http_json(
            "DELETE",
            f"{context.postgrest_url}/{table}?{key}=eq.runtime-validation-missing",
            token=context.service_token,
        )
        _require(result.status == 403, f"Direct DELETE on {table} returned {result.status}, expected 403.")
    return {
        "tables": total_tables,
        "rls_tables": rls_tables,
        "browser_grants": browser_grants,
        "workflow_issue_service_rpcs": 3,
    }


def _validate_transient_auth_concurrency(context: ValidationContext) -> dict[str, int]:
    now = datetime.now(UTC)
    client_fingerprint = hashlib.sha256(b"runtime-validation-client").hexdigest()

    def start(index: int) -> tuple[str, str]:
        state_hash = hashlib.sha256(f"runtime-validation-state-{index}".encode()).hexdigest()
        result = _rpc(
            context,
            "exchange_start_transient_auth_state",
            {
                "p_state_hash": state_hash,
                "p_kind": "oauth_login",
                "p_provider_id": "runtime-validation-provider",
                "p_account_id": None,
                "p_session_id": f"runtime-validation-session-{index}",
                "p_payload": {"index": index},
                "p_expires_at": (now + timedelta(minutes=10)).isoformat(),
                "p_client_fingerprint": client_fingerprint,
                "p_window_start": (now - timedelta(minutes=1)).isoformat(),
                "p_start_limit": 1,
                "p_max_active": 100,
                "p_replace_session": False,
            },
        )
        _require(result.status == 200 and isinstance(result.payload, dict), "Transient start failed.")
        return state_hash, str(result.payload.get("status"))

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(start, range(8)))
    created = [state for state, status in outcomes if status == "created"]
    limited = [status for _, status in outcomes if status == "rate_limited"]
    _require(len(created) == 1 and len(limited) == 7, f"Transient concurrency mismatch: {outcomes}")

    consume_payload = {
        "p_state_hash": created[0],
        "p_kind": "oauth_login",
        "p_expected_account_id": None,
        "p_expected_session_id": None,
        "p_expected_provider_id": "runtime-validation-provider",
    }
    consumed = _rpc(context, "exchange_consume_transient_auth_state", consume_payload)
    replay = _rpc(context, "exchange_consume_transient_auth_state", consume_payload)
    _require(consumed.status == 200 and isinstance(consumed.payload, dict), "Transient consume failed.")
    _require(replay.status == 200 and replay.payload is None, "Transient state replay was not empty.")
    _psql(
        context,
        "delete from public.exchange_transient_auth_states where provider_id='runtime-validation-provider';\n"
        f"delete from public.exchange_transient_auth_rate_events where client_fingerprint='{client_fingerprint}';\n",
    )
    return {"created": len(created), "rate_limited": len(limited)}


def _validate_workspace_cas(context: ValidationContext) -> dict[str, int]:
    account_id = "runtime-validation-workspace-account"
    _psql(
        context,
        f"""
insert into public.exchange_accounts (id, email, profile, created_at, updated_at)
values ('{account_id}', 'runtime-workspace@example.test', '{{}}'::jsonb, now(), now());
""",
    )
    candidate = {
        "home_school": "長庚大學",
        "revision": 0,
        "application_context": {"school_name": "長庚大學"},
        "favorite_schools": [],
        "application_schools": [],
        "application_progress": {},
        "document_readiness": {},
        "application_selections": {},
        "submission_progress": {},
        "budget_plans": {},
        "deadline_events": [],
    }
    payload = {
        "p_account_id": account_id,
        "p_home_school_key": "長庚大學",
        "p_expected_revision": 0,
        "p_candidate_workspace": candidate,
        "p_mutation_kind": "workspace_replace",
        "p_progress_key": None,
        "p_progress": None,
    }

    def commit(_: int) -> str:
        result = _rpc(context, "exchange_commit_account_workspace", payload)
        _require(result.status == 200 and isinstance(result.payload, dict), "Workspace RPC failed.")
        return str(result.payload.get("status"))

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(commit, range(2)))
    _require(sorted(statuses) == ["committed", "conflict"], f"Workspace CAS mismatch: {statuses}")
    stored = _psql(
        context,
        f"select revision, workspace->>'revision' from public.exchange_account_workspaces where account_id='{account_id}';",
    )
    _require(stored == "1|1", f"Workspace revision mismatch: {stored}")
    _psql(context, f"delete from public.exchange_accounts where id='{account_id}';")
    return {"committed": 1, "conflict": 1}


def _workflow_issue_report_payload(
    *,
    description: str = "官方公告顯示截止日期不同，請重新核對目前學生看到的申請規定。",
    official_source_url: str = "https://example.edu/runtime-official-deadline",
) -> dict[str, Any]:
    return {
        "workflow_key": "長庚大學::runtime-workflow",
        "workflow_id": "runtime-workflow-12345678",
        "workflow_version": 2,
        "workflow_snapshot": "d" * 64,
        "home_school": "長庚大學",
        "school_name": "Runtime Exchange University",
        "step_rule_id": "runtime-deadline-rule",
        "step_title": "繳交校內申請",
        "college": "管理學院",
        "department": "工商管理學系",
        "academic_year": "2026-2027",
        "application_round": "秋季班",
        "category": "deadline",
        "description": description,
        "official_source_url": official_source_url,
    }


def _workflow_issue_submit_payload(
    account_id: str,
    mutation_id: str,
    report: Mapping[str, object],
) -> dict[str, Any]:
    return {
        "p_account_id": account_id,
        "p_mutation_id": mutation_id,
        "p_request_fingerprint": canonical_issue_report_fingerprint(report),
        "p_report": dict(report),
        "p_rate_limit": ISSUE_REPORT_RATE_LIMIT,
        "p_rate_window_seconds": int(ISSUE_REPORT_RATE_WINDOW.total_seconds()),
    }


def _workflow_issue_review_payload(
    reviewer_account_id: str,
    mutation_id: str,
    *,
    report_id: str,
    status: str,
    note: str,
) -> dict[str, Any]:
    review = {"report_id": report_id, "status": status, "note": note}
    return {
        "p_reviewer_account_id": reviewer_account_id,
        "p_mutation_id": mutation_id,
        "p_request_fingerprint": canonical_issue_report_fingerprint(review),
        "p_review": review,
    }


def _validate_workflow_issue_reports(context: ValidationContext) -> dict[str, int]:
    reporter = "runtime-workflow-reporter"
    unverified_reporter = "runtime-workflow-unverified"
    reviewer_a = "runtime-workflow-reviewer-a"
    reviewer_b = "runtime-workflow-reviewer-b"
    submit_rpc = "exchange_submit_application_workflow_issue_report"
    review_rpc = "exchange_review_application_workflow_issue_report"
    _psql(
        context,
        f"""
insert into public.exchange_accounts (id,email,profile,created_at,updated_at)
values
 ('{reporter}','runtime-workflow-reporter@example.test',jsonb_build_object('display_name','回報學生','email_verified',true,'student_status_verified',true,'verified_university','長庚大學'),now()-interval '30 days',now()-interval '30 days'),
 ('{unverified_reporter}','runtime-workflow-unverified@example.test',jsonb_build_object('display_name','未驗證學生','email_verified',true,'student_status_verified',false),now()-interval '30 days',now()-interval '30 days'),
 ('{reviewer_a}','runtime-workflow-reviewer-a@example.test',jsonb_build_object('display_name','內容管理員甲'),now()-interval '30 days',now()-interval '30 days'),
 ('{reviewer_b}','runtime-workflow-reviewer-b@example.test',jsonb_build_object('display_name','內容管理員乙'),now()-interval '30 days',now()-interval '30 days');
""",
    )

    report = _workflow_issue_report_payload()
    missing_account = _rpc(
        context,
        submit_rpc,
        _workflow_issue_submit_payload(
            "runtime-workflow-missing-account",
            "runtime-workflow-missing-account-0001",
            report,
        ),
    )
    _require(
        missing_account.status == 200
        and isinstance(missing_account.payload, dict)
        and missing_account.payload.get("status") == "account_missing",
        f"Missing workflow issue reporter was not rejected: {missing_account}",
    )
    unverified = _rpc(
        context,
        submit_rpc,
        _workflow_issue_submit_payload(
            unverified_reporter,
            "runtime-workflow-unverified-0001",
            report,
        ),
    )
    _require(
        unverified.status == 200
        and isinstance(unverified.payload, dict)
        and unverified.payload.get("status") == "student_verification_required",
        f"Unverified workflow issue reporter was not rejected: {unverified}",
    )

    unsafe_source_urls = (
        "https://127.0.0.1/private-source",
        "https://224.0.0.1/multicast-source",
        "https://240.0.0.1/reserved-source",
        "https://192.0.2.1/documentation-source",
        "https://198.51.100.1/documentation-source",
        "https://203.0.113.1/documentation-source",
    )
    for index, unsafe_source_url in enumerate(unsafe_source_urls, start=1):
        invalid_report = _workflow_issue_report_payload(
            official_source_url=unsafe_source_url
        )
        invalid_source = _rpc(
            context,
            submit_rpc,
            _workflow_issue_submit_payload(
                reporter,
                f"runtime-workflow-invalid-url-{index:04d}",
                invalid_report,
            ),
        )
        _require(
            invalid_source.status == 200
            and isinstance(invalid_source.payload, dict)
            and invalid_source.payload.get("status") == "invalid_request",
            "Unsafe workflow issue source URL was not rejected: "
            f"{unsafe_source_url} -> {invalid_source}",
        )
    rejected_state = _psql(
        context,
        f"""
select
 (select count(*) from public.application_workflow_issue_reports where reporter_account_id='{unverified_reporter}'),
 (select count(*) from public.application_workflow_issue_reports where reporter_account_id='{reporter}');
""",
    )
    _require(
        rejected_state == "0|0",
        f"Rejected workflow issue reports changed persisted state: {rejected_state}",
    )

    first_mutation = "runtime-workflow-submit-0001"
    first_payload = _workflow_issue_submit_payload(reporter, first_mutation, report)
    submit_race = _two_instance_race(
        context,
        (submit_rpc, first_payload),
        (submit_rpc, first_payload),
    )
    for result in submit_race:
        _require(
            result.status == 200
            and isinstance(result.payload, dict)
            and result.payload.get("status") == "committed"
            and isinstance(result.payload.get("idempotent"), bool)
            and isinstance(result.payload.get("report"), dict)
            and isinstance(result.payload["report"].get("id"), str)
            and bool(result.payload["report"]["id"]),
            f"Workflow issue idempotent submit race failed: {submit_race}",
        )
    submit_idempotency = [result.payload["idempotent"] for result in submit_race]
    _require(
        submit_idempotency.count(False) == 1
        and submit_idempotency.count(True) == 1,
        f"Workflow issue submit race did not commit once and replay once: {submit_race}",
    )
    report_ids = {result.payload["report"]["id"] for result in submit_race}
    _require(
        len(report_ids) == 1,
        f"Workflow issue submit race created multiple reports: {report_ids}",
    )
    report_id = next(iter(report_ids))
    first_row_count = _psql(
        context,
        f"select count(*) from public.application_workflow_issue_reports where id='{report_id}' and reporter_account_id='{reporter}' and status='pending';",
    )
    _require(
        first_row_count == "1",
        "Workflow issue submit race did not persist exactly one pending row.",
    )

    missing_reviewer = _rpc(
        context,
        review_rpc,
        _workflow_issue_review_payload(
            "runtime-workflow-missing-reviewer",
            "runtime-workflow-missing-reviewer-0001",
            report_id=report_id,
            status="resolved",
            note="這個不存在的審核帳號不得建立任何審核結論或修改回報狀態。",
        ),
    )
    _require(
        missing_reviewer.status == 200
        and isinstance(missing_reviewer.payload, dict)
        and missing_reviewer.payload.get("status") == "account_missing",
        f"Missing workflow issue reviewer was not rejected: {missing_reviewer}",
    )
    missing_report = _rpc(
        context,
        review_rpc,
        _workflow_issue_review_payload(
            reviewer_a,
            "runtime-workflow-missing-report-0001",
            report_id="runtime-workflow-missing-report",
            status="resolved",
            note="不存在的回報不得建立任何審核結論或留下孤立的審核資料。",
        ),
    )
    _require(
        missing_report.status == 200
        and isinstance(missing_report.payload, dict)
        and missing_report.payload.get("status") == "report_missing",
        f"Missing workflow issue report was not rejected: {missing_report}",
    )

    changed_report = _workflow_issue_report_payload(
        description="同一 mutation 改成不同說明，必須被判定為冪等衝突而不能覆寫原回報。"
    )
    submit_conflict = _rpc(
        context,
        submit_rpc,
        _workflow_issue_submit_payload(reporter, first_mutation, changed_report),
    )
    _require(
        submit_conflict.status == 200
        and isinstance(submit_conflict.payload, dict)
        and submit_conflict.payload.get("status") == "idempotency_conflict",
        f"Workflow issue submit idempotency conflict was not enforced: {submit_conflict}",
    )

    for index in range(2, ISSUE_REPORT_RATE_LIMIT + 1):
        committed = _rpc(
            context,
            submit_rpc,
            _workflow_issue_submit_payload(
                reporter,
                f"runtime-workflow-submit-{index:04d}",
                report,
            ),
        )
        _require(
            committed.status == 200
            and isinstance(committed.payload, dict)
            and committed.payload.get("status") == "committed"
            and committed.payload.get("idempotent") is False,
            f"Workflow issue rate-limit setup failed at report {index}: {committed}",
        )
    rate_limited = _rpc(
        context,
        submit_rpc,
        _workflow_issue_submit_payload(
            reporter,
            "runtime-workflow-submit-0011",
            report,
        ),
    )
    _require(
        rate_limited.status == 200
        and isinstance(rate_limited.payload, dict)
        and rate_limited.payload.get("status") == "rate_limited"
        and type(rate_limited.payload.get("retry_after_seconds")) is int
        and 1 <= rate_limited.payload["retry_after_seconds"] <= 3600,
        f"Workflow issue rate limit did not fail closed: {rate_limited}",
    )
    replay_after_limit = _rpc(context, submit_rpc, first_payload)
    _require(
        replay_after_limit.status == 200
        and isinstance(replay_after_limit.payload, dict)
        and replay_after_limit.payload.get("status") == "committed"
        and replay_after_limit.payload.get("idempotent") is True,
        "An existing workflow issue mutation could not replay after the rate limit.",
    )
    submit_state = _psql(
        context,
        f"""
select
 (select count(*) from public.application_workflow_issue_reports where reporter_account_id='{reporter}'),
 (select count(*) from public.application_workflow_issue_reports where reporter_account_id='{reporter}' and mutation_id='runtime-workflow-submit-0011'),
 (select count(*) from public.application_workflow_issue_reports where id='{report_id}' and description='{report["description"]}' and request_fingerprint='{first_payload["p_request_fingerprint"]}');
""",
    )
    _require(
        submit_state == f"{ISSUE_REPORT_RATE_LIMIT}|0|1",
        f"Workflow issue rate limit or original payload state mismatch: {submit_state}",
    )

    review_payloads = [
        _workflow_issue_review_payload(
            reviewer_a,
            "runtime-workflow-review-a-0001",
            report_id=report_id,
            status="resolved",
            note="已逐頁核對官方公告，確認回報成立；正式規定仍須另走雙人審查。",
        ),
        _workflow_issue_review_payload(
            reviewer_b,
            "runtime-workflow-review-b-0001",
            report_id=report_id,
            status="dismissed",
            note="已逐頁核對官方公告，確認現有內容正確，因此將這筆回報標記不成立。",
        ),
    ]
    review_race = _two_instance_race(
        context,
        (review_rpc, review_payloads[0]),
        (review_rpc, review_payloads[1]),
    )
    for result in review_race:
        _require(
            result.status == 200
            and isinstance(result.payload, dict)
            and result.payload.get("status") in {"committed", "status_conflict"},
            f"Workflow issue review CAS returned an invalid payload: {review_race}",
        )
    review_statuses = [result.payload["status"] for result in review_race]
    _require(
        review_statuses.count("committed") == 1
        and review_statuses.count("status_conflict") == 1,
        f"Workflow issue review CAS race mismatch: {review_race}",
    )
    winning_index = review_statuses.index("committed")
    winning_payload = review_payloads[winning_index]
    winning_status = winning_payload["p_review"]["status"]
    winning_result = review_race[winning_index]
    _require(
        winning_result.payload.get("idempotent") is False
        and isinstance(winning_result.payload.get("report"), dict)
        and isinstance(winning_result.payload.get("review"), dict),
        f"Workflow issue winning review payload was incomplete: {winning_result}",
    )
    review_replay = _rpc(context, review_rpc, winning_payload)
    _require(
        review_replay.status == 200
        and isinstance(review_replay.payload, dict)
        and review_replay.payload.get("status") == "committed"
        and review_replay.payload.get("idempotent") is True,
        f"Workflow issue review replay failed: {review_replay}",
    )
    conflicting_review = _workflow_issue_review_payload(
        winning_payload["p_reviewer_account_id"],
        winning_payload["p_mutation_id"],
        report_id=report_id,
        status=winning_status,
        note="相同 mutation 改成不同審核說明，必須拒絕而不能覆寫第一筆結論。",
    )
    review_conflict = _rpc(context, review_rpc, conflicting_review)
    _require(
        review_conflict.status == 200
        and isinstance(review_conflict.payload, dict)
        and review_conflict.payload.get("status") == "idempotency_conflict",
        f"Workflow issue review idempotency conflict was not enforced: {review_conflict}",
    )
    losing_index = 1 - winning_index
    terminal_conflict_payload = _workflow_issue_review_payload(
        review_payloads[losing_index]["p_reviewer_account_id"],
        "runtime-workflow-terminal-conflict-0001",
        report_id=report_id,
        status=review_payloads[losing_index]["p_review"]["status"],
        note="回報已經結案，使用全新 mutation 也不得建立第二筆互相衝突的審核。",
    )
    terminal_conflict = _rpc(context, review_rpc, terminal_conflict_payload)
    _require(
        terminal_conflict.status == 200
        and isinstance(terminal_conflict.payload, dict)
        and terminal_conflict.payload.get("status") == "status_conflict",
        f"Terminal workflow issue report accepted another review: {terminal_conflict}",
    )
    review_state = _psql(
        context,
        f"""
select report.status,
       (select count(*) from public.application_workflow_issue_report_reviews review where review.report_id=report.id),
       (
         select count(*)
         from public.application_workflow_issue_report_reviews review
         where review.report_id=report.id
           and review.reviewer_account_id='{winning_payload["p_reviewer_account_id"]}'
           and review.mutation_id='{winning_payload["p_mutation_id"]}'
           and review.request_fingerprint='{winning_payload["p_request_fingerprint"]}'
           and review.status='{winning_status}'
       )
from public.application_workflow_issue_reports report
where report.id='{report_id}';
""",
    )
    _require(
        review_state == f"{winning_status}|1|1",
        f"Workflow issue review did not persist one terminal decision: {review_state}",
    )

    _psql(
        context,
        f"""
delete from public.application_workflow_issue_report_reviews
where report_id in (
  select id from public.application_workflow_issue_reports
  where reporter_account_id in ('{reporter}','{unverified_reporter}')
);
delete from public.application_workflow_issue_reports
where reporter_account_id in ('{reporter}','{unverified_reporter}');
delete from public.exchange_accounts
where id in ('{reporter}','{unverified_reporter}','{reviewer_a}','{reviewer_b}');
""",
    )
    cleanup_state = _psql(
        context,
        f"""
select
 (select count(*) from public.application_workflow_issue_reports where reporter_account_id in ('{reporter}','{unverified_reporter}')),
 (select count(*) from public.application_workflow_issue_report_reviews where reviewer_account_id in ('{reviewer_a}','{reviewer_b}')),
 (select count(*) from public.exchange_accounts where id in ('{reporter}','{unverified_reporter}','{reviewer_a}','{reviewer_b}'));
""",
    )
    _require(
        cleanup_state == "0|0|0",
        f"Workflow issue report runtime fixtures were not cleaned: {cleanup_state}",
    )
    return {
        "submitted_reports": ISSUE_REPORT_RATE_LIMIT,
        "submit_idempotent_replays": 2,
        "submit_idempotency_conflicts": 1,
        "unsafe_source_urls_rejected": len(unsafe_source_urls),
        "rate_limited": 1,
        "missing_accounts_rejected": 2,
        "missing_reports_rejected": 1,
        "review_committed": 1,
        "review_status_conflicts": 1,
        "terminal_review_conflicts": 1,
        "review_idempotent_replays": 1,
        "review_idempotency_conflicts": 1,
    }


def _community_token(label: str) -> str:
    return hashlib.sha256(f"runtime-community-{label}".encode()).hexdigest()


def _public_publication_payload(
    request: PublicCommunityPublicationRequest,
) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": public_community_publication_fingerprint(request),
        "p_account_id": request.account_id,
        "p_identity_id": request.identity_id,
        "p_access_token_hash": request.access_token_hash,
        "p_resource_type": request.resource_type.value,
        "p_content": request.content,
    }


def _public_delete_payload(request: PublicCommunityDeleteRequest) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": community_mutation_fingerprint(
            "delete_public_content", request
        ),
        "p_account_id": request.account_id,
        "p_identity_id": request.identity_id,
        "p_access_token_hash": request.access_token_hash,
        "p_resource_type": request.resource_type.value,
        "p_resource_id": request.resource_id,
    }


def _public_moderation_payload(
    request: PublicCommunityModerationRequest,
) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": community_mutation_fingerprint(
            "moderation", request
        ),
        "p_moderator_id": request.moderator_id,
        "p_resource_type": request.resource_type.value,
        "p_resource_id": request.resource_id,
        "p_expected_status": request.expected_status.value,
        "p_status": request.status.value,
        "p_note": request.note,
    }


def _private_conversation_payload(
    request: PrivateConversationMutationRequest,
) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": private_community_mutation_fingerprint(
            "private_conversation", request
        ),
        "p_account_id": request.account_id,
        "p_identity_id": request.identity_id,
        "p_access_token_hash": request.access_token_hash,
        "p_recipient_identity_id": request.recipient_identity_id,
        "p_conversation": request.conversation.model_dump(mode="json"),
        "p_initial_message": request.initial_message.model_dump(mode="json"),
    }


def _private_message_payload(request: PrivateMessageMutationRequest) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": private_community_mutation_fingerprint(
            "private_message", request
        ),
        "p_account_id": request.account_id,
        "p_identity_id": request.identity_id,
        "p_access_token_hash": request.access_token_hash,
        "p_message": request.message.model_dump(mode="json"),
    }


def _private_block_payload(request: CommunityBlockMutationRequest) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": private_community_mutation_fingerprint(
            "community_block", request
        ),
        "p_account_id": request.account_id,
        "p_identity_id": request.identity_id,
        "p_access_token_hash": request.access_token_hash,
        "p_block": request.block.model_dump(mode="json"),
    }


def _private_report_payload(request: CommunityReportMutationRequest) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": private_community_mutation_fingerprint(
            "community_report", request
        ),
        "p_account_id": request.account_id,
        "p_identity_id": request.identity_id,
        "p_access_token_hash": request.access_token_hash,
        "p_report": request.report.model_dump(mode="json"),
    }


def _private_report_review_payload(
    request: CommunityReportReviewMutationRequest,
) -> dict[str, Any]:
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": private_community_mutation_fingerprint(
            "community_report_review", request
        ),
        "p_moderator_id": request.moderator_id,
        "p_report_id": request.report_id,
        "p_expected_status": request.expected_status.value,
        "p_status": request.status.value,
        "p_note": request.note,
    }


def _two_instance_race(
    context: ValidationContext,
    left: tuple[str, dict[str, Any]],
    right: tuple[str, dict[str, Any]],
) -> list[HttpResult]:
    barrier = Barrier(2)

    def invoke(call: tuple[bool, str, dict[str, Any]]) -> HttpResult:
        secondary, name, payload = call
        barrier.wait(timeout=10)
        return _rpc(context, name, payload, secondary=secondary)

    calls = [
        (False, left[0], left[1]),
        (True, right[0], right[1]),
    ]
    with ThreadPoolExecutor(max_workers=2) as executor:
        return list(executor.map(invoke, calls))


def _validate_community_multi_instance_concurrency(
    context: ValidationContext,
) -> dict[str, int]:
    now = datetime.now(UTC)
    account_a = "runtime-community-account-a"
    account_b = "runtime-community-account-b"
    moderator_a = "runtime-community-moderator-a"
    moderator_b = "runtime-community-moderator-b"
    identity_a = "runtime-community-identity-a"
    identity_b = "runtime-community-identity-b"
    token_a = _community_token("token-a")
    token_b = _community_token("token-b")
    _psql(
        context,
        f"""
insert into public.exchange_accounts (id,email,profile,created_at,updated_at)
values
 ('{account_a}','runtime-community-a@example.test',jsonb_build_object('display_name','測試學生甲','email_verified',true,'student_status_verified',true,'verified_university','長庚大學'),now()-interval '30 days',now()-interval '30 days'),
 ('{account_b}','runtime-community-b@example.test',jsonb_build_object('display_name','測試學生乙','email_verified',true,'student_status_verified',true,'verified_university','長庚大學'),now()-interval '30 days',now()-interval '30 days'),
 ('{moderator_a}','runtime-community-mod-a@example.test',jsonb_build_object('display_name','審核員甲'),now()-interval '30 days',now()-interval '30 days'),
 ('{moderator_b}','runtime-community-mod-b@example.test',jsonb_build_object('display_name','審核員乙'),now()-interval '30 days',now()-interval '30 days');
insert into public.exchange_community_identities (id,account_id,display_name,access_token_hash,created_at,updated_at)
values
 ('{identity_a}','{account_a}','測試學生甲','{token_a}',now()-interval '30 days',now()-interval '30 days'),
 ('{identity_b}','{account_b}','測試學生乙','{token_b}',now()-interval '30 days',now()-interval '30 days');
""",
    )

    duplicate_post_id = "runtime-community-idempotent-post"
    duplicate_post_request = PublicCommunityPublicationRequest(
        mutation_id="runtime-community-same-publication",
        account_id=account_a,
        identity_id=identity_a,
        access_token_hash=token_a,
        resource_type=PublicCommunityResourceType.POST,
        content=CommunityPost(
            id=duplicate_post_id,
            board_id="public-study-abroad",
            board_kind=CommunityBoardKind.PUBLIC_STUDY_ABROAD,
            school_name="留學公共區",
            author_id=identity_a,
            display_name="client supplied",
            identity_mode=CommunityIdentityMode.ANONYMOUS,
            post_type=CommunityPostType.DISCUSSION,
            topic=CommunityTopic.APPLICATION,
            title="兩個 API 實例冪等測試",
            body="同一個 mutation 同時送到兩個 API 實例時只能建立一筆貼文。",
            status=ModerationStatus.APPROVED,
            created_at=now,
        ).model_dump(mode="json"),
    )
    duplicate_payload = _public_publication_payload(duplicate_post_request)
    duplicate_results = _two_instance_race(
        context,
        ("exchange_commit_public_community_publication", duplicate_payload),
        ("exchange_commit_public_community_publication", duplicate_payload),
    )
    _require(
        all(result.status == 200 and isinstance(result.payload, dict) for result in duplicate_results),
        f"Public duplicate race returned transport failure: {duplicate_results}",
    )
    _require(
        [result.payload.get("status") for result in duplicate_results] == ["committed", "committed"],
        f"Public duplicate race did not commit/replay: {duplicate_results}",
    )
    _require(
        sorted(bool(result.payload.get("idempotent")) for result in duplicate_results)
        == [False, True],
        f"Public duplicate race did not produce one commit and one replay: {duplicate_results}",
    )
    duplicate_counts = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_community_posts where id='{duplicate_post_id}'),
 (select count(*) from public.exchange_community_mutation_receipts where id='runtime-community-same-publication');
""",
    )
    _require(duplicate_counts == "1|1", f"Public duplicate rows mismatch: {duplicate_counts}")

    parent_post_id = "runtime-community-parent-race-post"
    _psql(
        context,
        f"""
insert into public.exchange_community_posts (
 id,author_identity_id,board_id,board_kind,school_name,display_name,identity_mode,
 post_type,topic,title,body,status,revision,created_at,updated_at
) values (
 '{parent_post_id}','{identity_a}','public-study-abroad','public_study_abroad',
 '留學公共區','匿名學生','anonymous','discussion','application',
 '父貼文與留言競態測試','刪除父貼文與建立留言同時發生時不得留下孤兒留言。',
 'approved',0,now(),now()
);
""",
    )
    comment_id = "runtime-community-racing-comment"
    comment_request = PublicCommunityPublicationRequest(
        mutation_id="runtime-community-comment-race",
        account_id=account_b,
        identity_id=identity_b,
        access_token_hash=token_b,
        resource_type=PublicCommunityResourceType.COMMENT,
        content=CommunityPostComment(
            id=comment_id,
            post_id=parent_post_id,
            author_id=identity_b,
            display_name="client supplied",
            identity_mode=CommunityIdentityMode.ANONYMOUS,
            body="這則留言與父貼文刪除同時送出。",
            status=ModerationStatus.APPROVED,
            created_at=now,
        ).model_dump(mode="json"),
    )
    delete_request = PublicCommunityDeleteRequest(
        mutation_id="runtime-community-delete-race",
        account_id=account_a,
        identity_id=identity_a,
        access_token_hash=token_a,
        resource_type=PublicCommunityResourceType.POST,
        resource_id=parent_post_id,
    )
    parent_child_results = _two_instance_race(
        context,
        ("exchange_delete_public_community_content", _public_delete_payload(delete_request)),
        (
            "exchange_commit_public_community_publication",
            _public_publication_payload(comment_request),
        ),
    )
    delete_result, comment_result = parent_child_results
    _require(
        delete_result.status == 200
        and isinstance(delete_result.payload, dict)
        and delete_result.payload.get("status") == "committed",
        f"Public parent deletion race failed: {delete_result}",
    )
    _require(
        comment_result.status == 200
        and isinstance(comment_result.payload, dict)
        and comment_result.payload.get("status") in {"committed", "parent_missing"},
        f"Public child publication race failed unsafely: {comment_result}",
    )
    parent_child_counts = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_community_posts where id='{parent_post_id}'),
 (select count(*) from public.exchange_community_post_comments where id='{comment_id}'),
 (select count(*) from public.exchange_community_mutation_receipts where id='runtime-community-delete-race'),
 (select count(*) from public.exchange_community_mutation_receipts where id='runtime-community-comment-race');
""",
    )
    expected_comment_receipt = 1 if comment_result.payload.get("status") == "committed" else 0
    _require(
        parent_child_counts == f"0|0|1|{expected_comment_receipt}",
        f"Public parent/child final invariant mismatch: {parent_child_counts}",
    )

    def conversation_request(
        *,
        mutation_id: str,
        conversation_id: str,
        message_id: str,
        sender_account: str,
        sender_identity: str,
        sender_token: str,
        recipient_identity: str,
        body: str,
    ) -> PrivateConversationMutationRequest:
        conversation = PrivateConversation(
            id=conversation_id,
            school_name="林肯大學 Lincoln University",
            sender_id=sender_identity,
            sender_name="client supplied",
            recipient_id=recipient_identity,
            recipient_name="client supplied",
            status=ConversationStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        return PrivateConversationMutationRequest(
            mutation_id=mutation_id,
            account_id=sender_account,
            identity_id=sender_identity,
            access_token_hash=sender_token,
            recipient_identity_id=recipient_identity,
            conversation=conversation,
            initial_message=PrivateMessage(
                id=message_id,
                conversation_id=conversation_id,
                author_id=sender_identity,
                display_name="client supplied",
                body=body,
                created_at=now,
            ),
        )

    invite_a = conversation_request(
        mutation_id="runtime-private-invite-a-to-b",
        conversation_id="runtime-private-conversation-a-to-b",
        message_id="runtime-private-message-a-to-b",
        sender_account=account_a,
        sender_identity=identity_a,
        sender_token=token_a,
        recipient_identity=identity_b,
        body="甲同時向乙送出私訊邀請。",
    )
    invite_b = conversation_request(
        mutation_id="runtime-private-invite-b-to-a",
        conversation_id="runtime-private-conversation-b-to-a",
        message_id="runtime-private-message-b-to-a",
        sender_account=account_b,
        sender_identity=identity_b,
        sender_token=token_b,
        recipient_identity=identity_a,
        body="乙同時向甲送出私訊邀請。",
    )
    invite_results = _two_instance_race(
        context,
        (
            "exchange_commit_private_community_conversation",
            _private_conversation_payload(invite_a),
        ),
        (
            "exchange_commit_private_community_conversation",
            _private_conversation_payload(invite_b),
        ),
    )
    _require(
        all(
            result.status == 200
            and isinstance(result.payload, dict)
            and result.payload.get("status") == "committed"
            for result in invite_results
        ),
        f"Opposite private invitations failed or deadlocked: {invite_results}",
    )
    invite_counts = _psql(
        context,
        """
select
 (select count(*) from public.exchange_community_private_conversations where id in ('runtime-private-conversation-a-to-b','runtime-private-conversation-b-to-a')),
 (select count(*) from public.exchange_community_private_messages where id in ('runtime-private-message-a-to-b','runtime-private-message-b-to-a')),
 (select count(*) from public.exchange_community_mutation_receipts where id in ('runtime-private-invite-a-to-b','runtime-private-invite-b-to-a'));
""",
    )
    _require(invite_counts == "2|2|2", f"Opposite invitation rows mismatch: {invite_counts}")

    accepted_conversation_id = "runtime-private-accepted-race"
    _psql(
        context,
        f"""
insert into public.exchange_community_private_conversations (
 id,school_name,sender_id,sender_name,recipient_id,recipient_name,status,revision,created_at,updated_at
) values (
 '{accepted_conversation_id}','林肯大學 Lincoln University','{identity_a}','測試學生甲',
 '{identity_b}','測試學生乙','accepted',1,now(),now()
);
insert into public.exchange_community_private_messages (
 id,conversation_id,author_id,display_name,body,created_at
) values (
 'runtime-private-accepted-initial','{accepted_conversation_id}','{identity_a}',
 '測試學生甲','競態測試前已存在的訊息。',now()
);
""",
    )
    block_request = CommunityBlockMutationRequest(
        mutation_id="runtime-private-block-race",
        account_id=account_a,
        identity_id=identity_a,
        access_token_hash=token_a,
        block=CommunityBlock(
            id="runtime-private-block-a-to-b",
            owner_id=identity_a,
            target_id=identity_b,
            created_at=now,
        ),
    )
    message_request = PrivateMessageMutationRequest(
        mutation_id="runtime-private-message-race",
        account_id=account_b,
        identity_id=identity_b,
        access_token_hash=token_b,
        message=PrivateMessage(
            id="runtime-private-racing-message",
            conversation_id=accepted_conversation_id,
            author_id=identity_b,
            display_name="client supplied",
            body="這則訊息與封鎖操作同時送出。",
            created_at=now,
        ),
    )
    block_message_results = _two_instance_race(
        context,
        ("exchange_commit_private_community_block", _private_block_payload(block_request)),
        (
            "exchange_commit_private_community_message",
            _private_message_payload(message_request),
        ),
    )
    block_result, message_result = block_message_results
    _require(
        block_result.status == 200
        and isinstance(block_result.payload, dict)
        and block_result.payload.get("status") == "committed",
        f"Private block race failed: {block_result}",
    )
    _require(
        message_result.status == 200
        and isinstance(message_result.payload, dict)
        and message_result.payload.get("status")
        in {"committed", "blocked", "integrity_conflict"},
        f"Private message/block race failed unsafely: {message_result}",
    )
    expected_racing_messages = 1 if message_result.payload.get("status") == "committed" else 0
    block_message_counts = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_community_blocks where owner_id='{identity_a}' and target_id='{identity_b}'),
 (select count(*) from public.exchange_community_private_messages where id='runtime-private-racing-message'),
 (select count(*) from public.exchange_community_mutation_receipts where id='runtime-private-block-race'),
 (select count(*) from public.exchange_community_mutation_receipts where id='runtime-private-message-race');
""",
    )
    _require(
        block_message_counts
        == f"1|{expected_racing_messages}|1|{expected_racing_messages}",
        f"Private message/block final invariant mismatch: {block_message_counts}",
    )

    report_id = "runtime-community-report-review-race"
    _psql(
        context,
        f"""
insert into public.exchange_community_reports (
 id,reporter_id,resource_type,resource_id,reason,status,revision,created_at
) values (
 '{report_id}','{identity_b}','post','{duplicate_post_id}',
 '兩個審核員不得同時覆蓋同一筆檢舉結果。','pending',1,now()
);
""",
    )
    resolved_review = CommunityReportReviewMutationRequest(
        mutation_id="runtime-report-review-resolved",
        moderator_id=moderator_a,
        report_id=report_id,
        expected_status=CommunityReportStatus.PENDING,
        status=CommunityReportStatus.RESOLVED,
        note="審核員甲判定檢舉成立。",
    )
    dismissed_review = CommunityReportReviewMutationRequest(
        mutation_id="runtime-report-review-dismissed",
        moderator_id=moderator_b,
        report_id=report_id,
        expected_status=CommunityReportStatus.PENDING,
        status=CommunityReportStatus.DISMISSED,
        note="審核員乙判定檢舉不成立。",
    )
    review_results = _two_instance_race(
        context,
        (
            "exchange_commit_private_community_report_review",
            _private_report_review_payload(resolved_review),
        ),
        (
            "exchange_commit_private_community_report_review",
            _private_report_review_payload(dismissed_review),
        ),
    )
    _require(
        all(result.status == 200 and isinstance(result.payload, dict) for result in review_results),
        f"Report review race returned transport failure: {review_results}",
    )
    review_statuses = [str(result.payload.get("status")) for result in review_results]
    _require(
        sorted(review_statuses) == ["committed", "status_conflict"],
        f"Report review CAS mismatch: {review_results}",
    )
    committed_review = next(
        result for result in review_results if result.payload.get("status") == "committed"
    )
    final_report_status = str(committed_review.payload["report"]["status"])
    review_counts = _psql(
        context,
        f"""
select
 (select status || '|' || revision::text from public.exchange_community_reports where id='{report_id}'),
 (select count(*) from public.exchange_community_moderation_audits where resource_type='report' and resource_id='{report_id}'),
 (select count(*) from public.exchange_community_mutation_receipts where id in ('runtime-report-review-resolved','runtime-report-review-dismissed'));
""",
    )
    _require(
        review_counts == f"{final_report_status}|2|1|1",
        f"Report review final invariant mismatch: {review_counts}",
    )

    return {
        "postgrest_instances": 2,
        "public_idempotent_commits": 1,
        "public_idempotent_replays": 1,
        "public_parent_child_races": 1,
        "private_opposite_invitations": 2,
        "private_message_block_races": 1,
        "private_message_commits": expected_racing_messages,
        "private_message_blocked": int(message_result.payload.get("status") == "blocked"),
        "private_message_integrity_conflicts": int(
            message_result.payload.get("status") == "integrity_conflict"
        ),
        "private_report_review_commits": 1,
        "private_report_review_conflicts": 1,
    }


def _require_injected_community_failure(result: HttpResult, label: str) -> None:
    _require(
        result.status == 400
        and isinstance(result.payload, dict)
        and result.payload.get("code") == "P0001"
        and "runtime intentional late community receipt failure"
        in str(result.payload.get("message", "")),
        f"{label} did not propagate the injected late failure: {result}",
    )


def _validate_community_transaction_rollbacks(
    context: ValidationContext,
) -> dict[str, int]:
    now = datetime.now(UTC)
    account_a = "runtime-rollback-community-account-a"
    account_b = "runtime-rollback-community-account-b"
    moderator = "runtime-rollback-community-moderator"
    identity_a = "runtime-rollback-community-identity-a"
    identity_b = "runtime-rollback-community-identity-b"
    token_a = _community_token("rollback-token-a")
    token_b = _community_token("rollback-token-b")
    moderation_post_id = "runtime-rollback-moderation-post"
    report_post_id = "runtime-rollback-report-post"
    review_post_id = "runtime-rollback-review-post"
    accepted_conversation_id = "runtime-rollback-accepted-conversation"
    review_report_id = "runtime-rollback-pending-report"
    failure_mutations = (
        "runtime-rollback-publication",
        "runtime-rollback-moderation",
        "runtime-rollback-private-conversation",
        "runtime-rollback-private-message",
        "runtime-rollback-community-report",
        "runtime-rollback-report-review",
    )
    trigger_ids = ",".join(f"'{mutation}'" for mutation in failure_mutations)
    _psql(
        context,
        f"""
insert into public.exchange_accounts (id,email,profile,created_at,updated_at)
values
 ('{account_a}','runtime-rollback-community-a@example.test',jsonb_build_object('display_name','回滾學生甲','email_verified',true,'student_status_verified',true,'verified_university','長庚大學'),now()-interval '30 days',now()-interval '30 days'),
 ('{account_b}','runtime-rollback-community-b@example.test',jsonb_build_object('display_name','回滾學生乙','email_verified',true,'student_status_verified',true,'verified_university','長庚大學'),now()-interval '30 days',now()-interval '30 days'),
 ('{moderator}','runtime-rollback-community-mod@example.test',jsonb_build_object('display_name','回滾審核員'),now()-interval '30 days',now()-interval '30 days');
insert into public.exchange_community_identities (id,account_id,display_name,access_token_hash,created_at,updated_at)
values
 ('{identity_a}','{account_a}','回滾學生甲','{token_a}',now()-interval '30 days',now()-interval '30 days'),
 ('{identity_b}','{account_b}','回滾學生乙','{token_b}',now()-interval '30 days',now()-interval '30 days');
insert into public.exchange_community_posts (
 id,author_identity_id,board_id,board_kind,school_name,display_name,identity_mode,
 post_type,topic,title,body,status,revision,created_at,updated_at
) values
 ('{moderation_post_id}','{identity_a}','public-study-abroad','public_study_abroad','留學公共區','匿名學生','anonymous','discussion','application','公開審核回滾目標','晚期錯誤後貼文狀態與 revision 都必須還原。','approved',0,now(),now()),
 ('{report_post_id}','{identity_a}','public-study-abroad','public_study_abroad','留學公共區','匿名學生','anonymous','discussion','application','私人檢舉回滾目標','晚期錯誤後不得留下未完成的檢舉資料。','approved',0,now(),now()),
 ('{review_post_id}','{identity_a}','public-study-abroad','public_study_abroad','留學公共區','匿名學生','anonymous','discussion','application','檢舉審核回滾目標','晚期錯誤後檢舉狀態與 audit 都必須還原。','approved',0,now(),now());
insert into public.exchange_community_private_conversations (
 id,school_name,sender_id,sender_name,recipient_id,recipient_name,status,revision,created_at,updated_at
) values (
 '{accepted_conversation_id}','林肯大學 Lincoln University','{identity_a}','回滾學生甲',
 '{identity_b}','回滾學生乙','accepted',1,now(),now()
);
insert into public.exchange_community_private_messages (
 id,conversation_id,author_id,display_name,body,created_at
) values (
 'runtime-rollback-accepted-initial','{accepted_conversation_id}','{identity_a}',
 '回滾學生甲','晚期錯誤前已存在的基準訊息。',now()
);
insert into public.exchange_community_reports (
 id,reporter_id,resource_type,resource_id,reason,status,revision,created_at
) values (
 '{review_report_id}','{identity_b}','post','{review_post_id}',
 '此檢舉只用於晚期審核回滾測試。','pending',1,now()
);
create or replace function public.runtime_fail_community_receipt()
returns trigger language plpgsql set search_path=public,pg_temp as $fn$
begin
  if new.id in ({trigger_ids}) then
    raise exception 'runtime intentional late community receipt failure'
      using errcode='P0001';
  end if;
  return new;
end;
$fn$;
create trigger runtime_fail_community_receipt_trigger
before insert on public.exchange_community_mutation_receipts
for each row execute function public.runtime_fail_community_receipt();
""",
    )

    publication_post_id = "runtime-rollback-publication-post"
    publication = PublicCommunityPublicationRequest(
        mutation_id=failure_mutations[0],
        account_id=account_a,
        identity_id=identity_a,
        access_token_hash=token_a,
        resource_type=PublicCommunityResourceType.POST,
        content=CommunityPost(
            id=publication_post_id,
            board_id="public-study-abroad",
            board_kind=CommunityBoardKind.PUBLIC_STUDY_ABROAD,
            school_name="留學公共區",
            author_id=identity_a,
            display_name="client supplied",
            identity_mode=CommunityIdentityMode.ANONYMOUS,
            post_type=CommunityPostType.DISCUSSION,
            topic=CommunityTopic.APPLICATION,
            title="公開發文晚期回滾測試",
            body="receipt 寫入失敗時貼文、限流事件與 receipt 必須全部不存在。",
            status=ModerationStatus.APPROVED,
            created_at=now,
        ).model_dump(mode="json"),
    )
    publication_failure = _rpc(
        context,
        "exchange_commit_public_community_publication",
        _public_publication_payload(publication),
    )
    _require_injected_community_failure(publication_failure, "Public publication")
    publication_state = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_community_posts where id='{publication_post_id}'),
 (select count(*) from public.exchange_community_publish_events where id='{failure_mutations[0]}'),
 (select count(*) from public.exchange_community_mutation_receipts where id='{failure_mutations[0]}');
""",
    )
    _require(
        publication_state == "0|0|0",
        f"Public publication late failure left partial rows: {publication_state}",
    )

    moderation = PublicCommunityModerationRequest(
        mutation_id=failure_mutations[1],
        moderator_id=moderator,
        resource_type=PublicCommunityResourceType.POST,
        resource_id=moderation_post_id,
        expected_status=ModerationStatus.APPROVED,
        status=ModerationStatus.HIDDEN,
        note="此變更必須因 receipt 失敗而完整回滾。",
    )
    moderation_failure = _rpc(
        context,
        "exchange_commit_public_community_moderation",
        _public_moderation_payload(moderation),
    )
    _require_injected_community_failure(moderation_failure, "Public moderation")
    moderation_state = _psql(
        context,
        f"""
select
 (select status || '|' || revision::text from public.exchange_community_posts where id='{moderation_post_id}'),
 (select count(*) from public.exchange_community_moderation_audits where id='{failure_mutations[1]}'),
 (select count(*) from public.exchange_community_mutation_receipts where id='{failure_mutations[1]}');
""",
    )
    _require(
        moderation_state == "approved|0|0|0",
        f"Public moderation late failure left partial state: {moderation_state}",
    )

    failed_conversation_id = "runtime-rollback-private-conversation"
    conversation_request = PrivateConversationMutationRequest(
        mutation_id=failure_mutations[2],
        account_id=account_a,
        identity_id=identity_a,
        access_token_hash=token_a,
        recipient_identity_id=identity_b,
        conversation=PrivateConversation(
            id=failed_conversation_id,
            school_name="林肯大學 Lincoln University",
            sender_id=identity_a,
            sender_name="client supplied",
            recipient_id=identity_b,
            recipient_name="client supplied",
            status=ConversationStatus.PENDING,
            created_at=now,
            updated_at=now,
        ),
        initial_message=PrivateMessage(
            id="runtime-rollback-private-initial-message",
            conversation_id=failed_conversation_id,
            author_id=identity_a,
            display_name="client supplied",
            body="邀請與初始訊息都必須 rollback。",
            created_at=now,
        ),
    )
    conversation_failure = _rpc(
        context,
        "exchange_commit_private_community_conversation",
        _private_conversation_payload(conversation_request),
        secondary=True,
    )
    _require_injected_community_failure(conversation_failure, "Private conversation")
    conversation_state = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_community_private_conversations where id='{failed_conversation_id}'),
 (select count(*) from public.exchange_community_private_messages where id='runtime-rollback-private-initial-message'),
 (select count(*) from public.exchange_community_mutation_receipts where id='{failure_mutations[2]}');
""",
    )
    _require(
        conversation_state == "0|0|0",
        f"Private invitation late failure left partial rows: {conversation_state}",
    )

    private_message = PrivateMessageMutationRequest(
        mutation_id=failure_mutations[3],
        account_id=account_b,
        identity_id=identity_b,
        access_token_hash=token_b,
        message=PrivateMessage(
            id="runtime-rollback-private-message-row",
            conversation_id=accepted_conversation_id,
            author_id=identity_b,
            display_name="client supplied",
            body="訊息與 conversation revision 必須一起 rollback。",
            created_at=now,
        ),
    )
    message_failure = _rpc(
        context,
        "exchange_commit_private_community_message",
        _private_message_payload(private_message),
    )
    _require_injected_community_failure(message_failure, "Private message")
    message_state = _psql(
        context,
        f"""
select
 (select revision from public.exchange_community_private_conversations where id='{accepted_conversation_id}'),
 (select count(*) from public.exchange_community_private_messages where conversation_id='{accepted_conversation_id}'),
 (select count(*) from public.exchange_community_private_messages where id='runtime-rollback-private-message-row'),
 (select count(*) from public.exchange_community_mutation_receipts where id='{failure_mutations[3]}');
""",
    )
    _require(
        message_state == "1|1|0|0",
        f"Private message late failure changed conversation state: {message_state}",
    )

    failed_report_id = "runtime-rollback-community-report-row"
    report_request = CommunityReportMutationRequest(
        mutation_id=failure_mutations[4],
        account_id=account_b,
        identity_id=identity_b,
        access_token_hash=token_b,
        report=CommunityReport(
            id=failed_report_id,
            reporter_id=identity_b,
            resource_type="post",
            resource_id=report_post_id,
            reason="receipt 失敗時不得留下檢舉資料。",
            status=CommunityReportStatus.PENDING,
            created_at=now,
        ),
    )
    report_failure = _rpc(
        context,
        "exchange_commit_private_community_report",
        _private_report_payload(report_request),
        secondary=True,
    )
    _require_injected_community_failure(report_failure, "Private report")
    report_state = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_community_reports where id='{failed_report_id}'),
 (select count(*) from public.exchange_community_mutation_receipts where id='{failure_mutations[4]}');
""",
    )
    _require(
        report_state == "0|0",
        f"Private report late failure left partial rows: {report_state}",
    )

    review_request = CommunityReportReviewMutationRequest(
        mutation_id=failure_mutations[5],
        moderator_id=moderator,
        report_id=review_report_id,
        expected_status=CommunityReportStatus.PENDING,
        status=CommunityReportStatus.RESOLVED,
        note="審核結果與 audit 必須因 receipt 失敗而 rollback。",
    )
    review_failure = _rpc(
        context,
        "exchange_commit_private_community_report_review",
        _private_report_review_payload(review_request),
    )
    _require_injected_community_failure(review_failure, "Private report review")
    review_state = _psql(
        context,
        f"""
select
 (select status || '|' || revision::text || '|' || (reviewed_by is null)::text || '|' || (reviewed_at is null)::text || '|' || (resolution_note is null)::text from public.exchange_community_reports where id='{review_report_id}'),
 (select count(*) from public.exchange_community_moderation_audits where id='{failure_mutations[5]}'),
 (select count(*) from public.exchange_community_mutation_receipts where id='{failure_mutations[5]}');
""",
    )
    _require(
        review_state == "pending|1|true|true|true|0|0",
        f"Private report review late failure left partial state: {review_state}",
    )

    _psql(
        context,
        "drop trigger runtime_fail_community_receipt_trigger on public.exchange_community_mutation_receipts;\n"
        "drop function public.runtime_fail_community_receipt();\n",
    )
    return {
        "late_failures_propagated": len(failure_mutations),
        "public_publication_rollbacks": 1,
        "public_moderation_rollbacks": 1,
        "private_conversation_rollbacks": 1,
        "private_message_rollbacks": 1,
        "private_report_rollbacks": 1,
        "private_report_review_rollbacks": 1,
        "partial_rows": 0,
    }


def _validate_storage_orphan_cleanup(
    context: ValidationContext,
    repository: SupabaseDocumentVaultRepository,
) -> dict[str, int]:
    live_key = "vault/runtime-live/nested/live.cipher"
    orphan_key = "vault/runtime-orphan/deeper/orphan.cipher"
    live_content = b"runtime-live-ciphertext"
    orphan_content = b"runtime-orphan-ciphertext"
    _psql(
        context,
        f"""
insert into public.exchange_accounts (id,email,profile,created_at,updated_at)
values ('runtime-storage-live-account','runtime-storage-live@example.test','{{}}'::jsonb,now(),now());
insert into public.exchange_vault_documents (id,account_id,label_ciphertext,label_nonce,category,latest_version,version_count,created_at,updated_at)
values ('runtime-storage-live-document','runtime-storage-live-account','cipher-label','nonce-label','transcript',1,1,now(),now());
insert into public.exchange_vault_versions (id,document_id,account_id,version_number,file_name_ciphertext,file_name_nonce,media_type,plaintext_size,plaintext_sha256,ciphertext_size,ciphertext_sha256,object_key,encryption_algorithm,wrapped_data_key,wrap_nonce,content_nonce,consent_id,retention_expires_at,created_at)
values ('runtime-storage-live-version','runtime-storage-live-document','runtime-storage-live-account',1,'cipher-file','nonce-file','application/octet-stream',32,repeat('1',64),48,repeat('2',64),'{live_key}','AES-256-GCM','wrapped-key','wrap-nonce','content-nonce','runtime-storage-live-consent',now()+interval '30 days',now());
""",
    )
    repository.upload_object(live_key, live_content)
    repository.upload_object(orphan_key, orphan_content)
    before = repository.list_object_keys()
    _require(
        before == {live_key, orphan_key},
        f"Recursive Storage listing did not find nested objects: {sorted(before)}",
    )

    cleanup = DocumentVaultService(repository, b"r" * 32).cleanup()
    _require(
        cleanup.expired_version_count == 0
        and cleanup.removed_document_count == 0
        and cleanup.orphan_object_count == 1,
        f"Storage orphan cleanup result mismatch: {cleanup}",
    )
    _require(repository.read_object(live_key) == live_content, "Referenced Storage object was deleted.")
    _require(_object_is_missing(repository, orphan_key), "Nested orphan Storage object still exists.")
    _require(
        repository.list_object_keys() == {live_key},
        "Storage orphan cleanup did not preserve exactly the referenced object.",
    )
    audit_count = _psql(
        context,
        "select count(*) from public.exchange_vault_audit_log where action='orphan_removed' and subject_fingerprint=repeat('0',32);",
    )
    _require(audit_count == "1", "Storage orphan cleanup audit was not persisted.")
    _psql(
        context,
        "delete from public.exchange_accounts where id='runtime-storage-live-account';\n"
        "delete from public.exchange_vault_audit_log where action='orphan_removed' and subject_fingerprint=repeat('0',32);\n",
    )
    repository.delete_objects([live_key])
    return {"nested_objects_listed": 2, "orphans_removed": 1, "referenced_preserved": 1}


def _account_deletion_seed_sql() -> str:
    return f"""
insert into public.exchange_accounts (id,email,profile,created_at,updated_at)
values
 ('runtime-deletion-account','runtime-deletion@example.test',jsonb_build_object('display_name','待刪除管理員'),now(),now()),
 ('runtime-deletion-issue-owner','runtime-deletion-issue-owner@example.test',jsonb_build_object('display_name','留存學生'),now(),now()),
 ('runtime-deletion-issue-reviewer','runtime-deletion-issue-reviewer@example.test',jsonb_build_object('display_name','留存管理員'),now(),now());
insert into public.exchange_account_sessions (id,account_id,token_hash,expires_at,created_at)
values ('runtime-deletion-session','runtime-deletion-account',repeat('a',64),now()+interval '1 day',now());
insert into public.exchange_account_workspaces (account_id,home_school_key,workspace,revision,updated_at)
values ('runtime-deletion-account','長庚大學',jsonb_build_object('home_school','長庚大學','revision',0),0,now());
insert into public.exchange_community_identities (id,account_id,display_name,access_token_hash,created_at,updated_at)
values ('runtime-deletion-identity','runtime-deletion-account','回滾測試學生',repeat('c',64),now(),now());
insert into public.exchange_community_questions (id,author_identity_id,school_name,home_university,topic,title,body,display_name,identity_mode,status,revision,created_at,updated_at)
values ('runtime-deletion-question','runtime-deletion-identity','測試交換校','長庚大學','application','回滾測試問題','這是一段只供隔離資料庫回滾驗證使用的測試內容。','回滾測試學生','real_name','approved',0,now(),now());
insert into public.exchange_vault_documents (id,account_id,label_ciphertext,label_nonce,category,latest_version,version_count,created_at,updated_at)
values ('runtime-deletion-document','runtime-deletion-account','cipher-label','nonce-label','transcript',1,1,now(),now());
insert into public.exchange_vault_versions (id,document_id,account_id,version_number,file_name_ciphertext,file_name_nonce,media_type,plaintext_size,plaintext_sha256,ciphertext_size,ciphertext_sha256,object_key,encryption_algorithm,wrapped_data_key,wrap_nonce,content_nonce,consent_id,retention_expires_at,created_at)
values ('runtime-deletion-version','runtime-deletion-document','runtime-deletion-account',1,'cipher-file','nonce-file','application/octet-stream',32,repeat('d',64),48,repeat('e',64),'{ACCOUNT_DELETION_OBJECT_KEY}','AES-256-GCM','wrapped-key','wrap-nonce','content-nonce','runtime-deletion-consent',now()+interval '30 days',now());
insert into public.exchange_email_verifications (id,email_fingerprint,code_hash,attempt_count,requested_at,resend_available_at,expires_at)
values ('runtime-deletion-email',repeat('b',64),repeat('f',64),0,now(),now()+interval '1 minute',now()+interval '10 minutes');
insert into public.application_workflow_issue_reports (
  id,workflow_key,workflow_id,workflow_version,workflow_snapshot,home_school,
  school_name,category,description,official_source_url,status,
  reporter_account_id,mutation_id,request_fingerprint,created_at,updated_at
)
values
 (
  'runtime-deletion-issue-pending-90','長庚大學::runtime-deletion',
  'runtime-deletion-workflow-0001',1,repeat('d',64),'長庚大學',
  'Runtime Exchange University','deadline',
  '這是刪除帳號後保留九十天並測試清除的待處理回報。',
  'https://example.edu/runtime-account-deletion','pending',
  'runtime-deletion-account','runtime-deletion-pending-90-mutation',repeat('1',64),
  now()-interval '2 days',now()-interval '2 days'
 ),
 (
  'runtime-deletion-issue-pending-24','長庚大學::runtime-deletion',
  'runtime-deletion-workflow-0001',1,repeat('d',64),'長庚大學',
  'Runtime Exchange University','deadline',
  '這是刪除帳號後再由管理員結案並測試二十四小時保留的回報。',
  'https://example.edu/runtime-account-deletion','pending',
  'runtime-deletion-account','runtime-deletion-pending-24-mutation',repeat('2',64),
  now()-interval '2 days',now()-interval '2 days'
 ),
 (
  'runtime-deletion-issue-closed-owner','長庚大學::runtime-deletion',
  'runtime-deletion-workflow-0001',1,repeat('d',64),'長庚大學',
  'Runtime Exchange University','deadline',
  '這是刪除回報者帳號時必須立即連同審核一起刪除的已結案回報。',
  'https://example.edu/runtime-account-deletion','resolved',
  'runtime-deletion-account','runtime-deletion-closed-owner-mutation',repeat('3',64),
  now()-interval '2 days',now()-interval '1 day'
 ),
 (
  'runtime-deletion-issue-reviewed-by-deleted','長庚大學::runtime-deletion',
  'runtime-deletion-workflow-0001',1,repeat('d',64),'長庚大學',
  'Runtime Exchange University','deadline',
  '這是刪除審核者帳號後仍須保留結論但必須移除審核者身分的回報。',
  'https://example.edu/runtime-account-deletion','resolved',
  'runtime-deletion-issue-owner','runtime-deletion-external-owner-mutation',repeat('4',64),
  now()-interval '2 days',now()-interval '1 day'
 );
insert into public.application_workflow_issue_report_reviews (
  id,report_id,status,note,reviewer_account_id,reviewer_display_name,
  mutation_id,request_fingerprint,reviewed_at
)
values
 (
  'runtime-deletion-review-closed-owner','runtime-deletion-issue-closed-owner',
  'resolved','已核對完成，這筆已結案回報應在回報者刪帳時立即移除。',
  'runtime-deletion-issue-reviewer','留存管理員',
  'runtime-deletion-review-closed-owner',repeat('5',64),now()-interval '1 day'
 ),
 (
  'runtime-deletion-review-by-deleted','runtime-deletion-issue-reviewed-by-deleted',
  'resolved','已核對完成，刪除審核者後只保留去識別化的處置結論。',
  'runtime-deletion-account','待刪除管理員',
  'runtime-deletion-reviewer-redaction-mutation',repeat('6',64),now()-interval '1 day'
 );
"""


def _account_deletion_payload(mutation_id: str, *, replay: bool = False) -> dict[str, Any]:
    request = AccountDeletionMutationRequest(
        mutation_id=mutation_id,
        account_id=None if replay else "runtime-deletion-account",
        session_id=None if replay else "runtime-deletion-session",
        session_token_hash="a" * 64,
        email_fingerprint=None if replay else "b" * 64,
        pending_report_retention_days=90,
        replacement_name="已刪除帳號",
    )
    return {
        "p_mutation_id": request.mutation_id,
        "p_request_fingerprint": account_deletion_mutation_fingerprint(request),
        "p_account_id": request.account_id,
        "p_session_id": request.session_id,
        "p_session_token_hash": request.session_token_hash,
        "p_email_fingerprint": request.email_fingerprint,
        "p_pending_report_retention_days": request.pending_report_retention_days,
        "p_replacement_name": request.replacement_name,
    }


def _validate_account_deletion(
    context: ValidationContext,
    repository: SupabaseDocumentVaultRepository,
) -> dict[str, int]:
    rollback_mutation = "runtime-rollback-mutation-0001"
    success_mutation = "runtime-success-mutation-0002"
    object_content = b"runtime-account-deletion-ciphertext"
    repository.upload_object(ACCOUNT_DELETION_OBJECT_KEY, object_content)
    _psql(context, _account_deletion_seed_sql())
    _psql(
        context,
        f"""
create or replace function public.runtime_fail_account_deletion_receipt()
returns trigger language plpgsql set search_path=public,pg_temp as $fn$
begin
  if new.mutation_id = '{rollback_mutation}' then
    raise exception 'runtime intentional late receipt failure' using errcode='P0001';
  end if;
  return new;
end;
$fn$;
create trigger runtime_fail_account_deletion_receipt_trigger
before insert on public.exchange_account_deletion_receipts
for each row execute function public.runtime_fail_account_deletion_receipt();
""",
    )
    failed = _rpc(context, "exchange_commit_account_deletion", _account_deletion_payload(rollback_mutation))
    _require(
        failed.status == 400
        and isinstance(failed.payload, dict)
        and failed.payload.get("code") == "P0001",
        f"Late account deletion failure did not propagate safely: {failed}",
    )
    rollback_counts = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_accounts where id='runtime-deletion-account'),
 (select count(*) from public.exchange_account_sessions where id='runtime-deletion-session'),
 (select count(*) from public.exchange_account_workspaces where account_id='runtime-deletion-account'),
 (select count(*) from public.exchange_community_identities where id='runtime-deletion-identity'),
 (select count(*) from public.exchange_community_questions where id='runtime-deletion-question' and author_identity_id='runtime-deletion-identity' and display_name='回滾測試學生' and identity_mode='real_name' and revision=0),
 (select count(*) from public.exchange_vault_documents where id='runtime-deletion-document'),
 (select count(*) from public.exchange_vault_versions where id='runtime-deletion-version'),
 (select count(*) from public.exchange_email_verifications where id='runtime-deletion-email'),
 (select count(*) from public.exchange_account_deletion_receipts where mutation_id='{rollback_mutation}');
""",
    )
    _require(rollback_counts == "1|1|1|1|1|1|1|1|0", f"Deletion rollback mismatch: {rollback_counts}")
    workflow_issue_rollback = _psql(
        context,
        """
select
 (
   select count(*)
   from public.application_workflow_issue_reports
   where reporter_account_id='runtime-deletion-account'
     and status='pending'
     and reporter_deleted_at is null
     and retained_until is null
     and (
       (
         id='runtime-deletion-issue-pending-90'
         and mutation_id='runtime-deletion-pending-90-mutation'
         and request_fingerprint=repeat('1',64)
       )
       or (
         id='runtime-deletion-issue-pending-24'
         and mutation_id='runtime-deletion-pending-24-mutation'
         and request_fingerprint=repeat('2',64)
       )
     )
 ),
 (
   select count(*)
   from public.application_workflow_issue_reports
   where id='runtime-deletion-issue-closed-owner'
     and reporter_account_id='runtime-deletion-account'
     and status='resolved'
 ),
 (
   select count(*)
   from public.application_workflow_issue_report_reviews
   where report_id='runtime-deletion-issue-closed-owner'
     and reviewer_account_id='runtime-deletion-issue-reviewer'
 ),
 (
   select count(*)
   from public.application_workflow_issue_report_reviews
   where report_id='runtime-deletion-issue-reviewed-by-deleted'
     and reviewer_account_id='runtime-deletion-account'
     and reviewer_display_name='待刪除管理員'
     and mutation_id='runtime-deletion-reviewer-redaction-mutation'
     and request_fingerprint=repeat('6',64)
 );
""",
    )
    _require(
        workflow_issue_rollback == "2|1|1|1",
        "Account deletion did not roll back workflow issue report changes: "
        f"{workflow_issue_rollback}",
    )
    _require(
        repository.read_object(ACCOUNT_DELETION_OBJECT_KEY) == object_content,
        "Late database rollback changed the encrypted Storage object.",
    )
    _psql(
        context,
        "drop trigger runtime_fail_account_deletion_receipt_trigger on public.exchange_account_deletion_receipts;\n"
        "drop function public.runtime_fail_account_deletion_receipt();\n",
    )

    committed = _rpc(context, "exchange_commit_account_deletion", _account_deletion_payload(success_mutation))
    _require(
        committed.status == 200
        and isinstance(committed.payload, dict)
        and committed.payload.get("status") == "committed"
        and committed.payload.get("idempotent") is False
        and committed.payload.get("storage_object_keys") == [ACCOUNT_DELETION_OBJECT_KEY],
        f"Account deletion commit mismatch: {committed}",
    )
    replay = _rpc(
        context,
        "exchange_commit_account_deletion",
        _account_deletion_payload(success_mutation, replay=True),
    )
    _require(
        replay.status == 200
        and isinstance(replay.payload, dict)
        and replay.payload.get("status") == "committed"
        and replay.payload.get("idempotent") is True,
        f"Account deletion replay mismatch: {replay}",
    )

    deletion_counts = _psql(
        context,
        f"""
select
 (select count(*) from public.exchange_accounts where id='runtime-deletion-account'),
 (select count(*) from public.exchange_account_sessions where id='runtime-deletion-session'),
 (select count(*) from public.exchange_account_workspaces where account_id='runtime-deletion-account'),
 (select count(*) from public.exchange_community_identities where id='runtime-deletion-identity'),
 (select count(*) from public.exchange_community_questions where id='runtime-deletion-question' and author_identity_id is null and display_name='已刪除帳號' and identity_mode='anonymous' and revision=1),
 (select count(*) from public.exchange_vault_documents where id='runtime-deletion-document'),
 (select count(*) from public.exchange_vault_versions where id='runtime-deletion-version'),
 (select count(*) from public.exchange_email_verifications where id='runtime-deletion-email'),
 (select count(*) from public.exchange_account_deletion_receipts where mutation_id='{success_mutation}' and storage_completed_at is null);
""",
    )
    _require(deletion_counts == "0|0|0|0|1|0|0|0|1", f"Deletion commit mismatch: {deletion_counts}")

    workflow_issue_deletion = _psql(
        context,
        """
select
 (
   select count(*)
   from public.application_workflow_issue_reports
   where id in (
       'runtime-deletion-issue-pending-90',
       'runtime-deletion-issue-pending-24'
     )
     and reporter_account_id is null
     and reporter_deleted_at is not null
     and retained_until=reporter_deleted_at+interval '90 days'
     and mutation_id like 'deleted-%'
     and request_fingerprint not in (repeat('1',64),repeat('2',64))
 ),
 (
   select count(*)
   from public.application_workflow_issue_reports
   where id='runtime-deletion-issue-closed-owner'
 ),
 (
   select count(*)
   from public.application_workflow_issue_report_reviews
   where report_id='runtime-deletion-issue-closed-owner'
 ),
 (
   select count(*)
   from public.application_workflow_issue_reports
   where id='runtime-deletion-issue-reviewed-by-deleted'
     and reporter_account_id='runtime-deletion-issue-owner'
     and status='resolved'
 ),
 (
   select count(*)
   from public.application_workflow_issue_report_reviews
   where report_id='runtime-deletion-issue-reviewed-by-deleted'
     and reviewer_account_id is null
     and reviewer_display_name='已刪除管理員'
     and mutation_id like 'deleted-%'
     and mutation_id<>'runtime-deletion-reviewer-redaction-mutation'
     and request_fingerprint<>repeat('6',64)
 );
""",
    )
    _require(
        workflow_issue_deletion == "2|0|0|1|1",
        "Workflow issue report account-deletion lifecycle mismatch: "
        f"{workflow_issue_deletion}",
    )

    terminal_payload = _workflow_issue_review_payload(
        "runtime-deletion-issue-reviewer",
        "runtime-deletion-post-delete-review",
        report_id="runtime-deletion-issue-pending-24",
        status="resolved",
        note="去識別回報已核對；短暫保留只為支援相同 mutation 安全重送。",
    )
    terminal_review = _rpc(
        context,
        "exchange_review_application_workflow_issue_report",
        terminal_payload,
    )
    _require(
        terminal_review.status == 200
        and isinstance(terminal_review.payload, dict)
        and terminal_review.payload.get("status") == "committed"
        and terminal_review.payload.get("idempotent") is False,
        f"Reviewing a deidentified pending issue report failed: {terminal_review}",
    )
    terminal_replay = _rpc(
        context,
        "exchange_review_application_workflow_issue_report",
        terminal_payload,
    )
    _require(
        terminal_replay.status == 200
        and isinstance(terminal_replay.payload, dict)
        and terminal_replay.payload.get("status") == "committed"
        and terminal_replay.payload.get("idempotent") is True,
        f"Deidentified issue report review replay failed: {terminal_replay}",
    )
    retention_state = _psql(
        context,
        """
select
  status,
  reporter_account_id is null,
  reporter_deleted_at is not null,
  retained_until=updated_at+interval '24 hours',
  (
    select count(*)
    from public.application_workflow_issue_report_reviews review
    where review.report_id=report.id
  )
from public.application_workflow_issue_reports report
where id='runtime-deletion-issue-pending-24';
""",
    )
    _require(
        retention_state == "resolved|t|t|t|1",
        f"Workflow issue report 24-hour retention mismatch: {retention_state}",
    )
    pending_control = _psql(
        context,
        """
select count(*)
from public.application_workflow_issue_reports
where id='runtime-deletion-issue-pending-90'
  and status='pending'
  and reporter_account_id is null
  and retained_until=reporter_deleted_at+interval '90 days';
""",
    )
    _require(
        pending_control == "1",
        "Reviewing one deidentified report changed the independent 90-day report.",
    )

    _psql(
        context,
        """
update public.application_workflow_issue_reports
set reporter_deleted_at=clock_timestamp()-interval '91 days',
    retained_until=clock_timestamp()-interval '1 day'
where id in (
  'runtime-deletion-issue-pending-90',
  'runtime-deletion-issue-pending-24'
);
""",
    )
    expired_states = _psql(
        context,
        """
select
  count(*) filter (where status='pending'),
  count(*) filter (where status='resolved')
from public.application_workflow_issue_reports
where id in (
  'runtime-deletion-issue-pending-90',
  'runtime-deletion-issue-pending-24'
)
  and retained_until<=clock_timestamp();
""",
    )
    _require(
        expired_states == "1|1",
        f"Workflow issue report purge setup mismatch: {expired_states}",
    )
    purged = _rpc(
        context,
        "exchange_purge_expired_application_workflow_issue_reports",
        {},
    )
    _require(
        purged.status == 200
        and isinstance(purged.payload, dict)
        and purged.payload.get("status") == "committed"
        and purged.payload.get("purged_count") == 2,
        f"Workflow issue report purge mismatch: {purged}",
    )
    purge_state = _psql(
        context,
        """
select
 (
   select count(*)
   from public.application_workflow_issue_reports
   where id in (
     'runtime-deletion-issue-pending-90',
     'runtime-deletion-issue-pending-24'
   )
 ),
 (
   select count(*)
   from public.application_workflow_issue_report_reviews
   where report_id='runtime-deletion-issue-pending-24'
 ),
 (
   select count(*)
   from public.application_workflow_issue_reports
   where id='runtime-deletion-issue-reviewed-by-deleted'
     and retained_until is null
 ),
 (
   select count(*)
   from public.application_workflow_issue_report_reviews
   where report_id='runtime-deletion-issue-reviewed-by-deleted'
     and reviewer_account_id is null
 );
""",
    )
    _require(
        purge_state == "0|0|1|1",
        f"Workflow issue report purge over- or under-deleted rows: {purge_state}",
    )

    wrong_proof = _rpc(
        context,
        "exchange_complete_account_deletion_storage",
        {"p_mutation_id": success_mutation, "p_session_token_hash": "0" * 64},
    )
    _require(
        wrong_proof.status == 200
        and isinstance(wrong_proof.payload, dict)
        and wrong_proof.payload.get("status") == "idempotency_conflict",
        "Storage completion accepted the wrong replay proof.",
    )
    pending = _rpc(context, "exchange_list_pending_account_deletion_storage", {"p_limit": 100})
    expected_job = {
        "mutation_id": success_mutation,
        "storage_object_keys": [ACCOUNT_DELETION_OBJECT_KEY],
    }
    _require(
        pending.status == 200
        and isinstance(pending.payload, dict)
        and expected_job in pending.payload.get("jobs", []),
        f"Durable Storage cleanup job missing: {pending}",
    )

    def timeout_request(method: str, url: str, **kwargs: Any) -> requests.Response:
        del method, url, kwargs
        raise requests.Timeout("runtime intentional Storage timeout")

    unavailable_repository = SupabaseDocumentVaultRepository(
        "https://runtime-storage-timeout.invalid",
        context.service_token,
        bucket=RUNTIME_VAULT_BUCKET,
        request_func=timeout_request,
    )
    try:
        unavailable_repository.delete_objects([ACCOUNT_DELETION_OBJECT_KEY])
    except requests.Timeout:
        pass
    else:
        raise RuntimeValidationError("Intentional Storage timeout did not fail closed.")
    pending_after_timeout = _rpc(
        context,
        "exchange_list_pending_account_deletion_storage",
        {"p_limit": 100},
    )
    _require(
        pending_after_timeout.status == 200
        and isinstance(pending_after_timeout.payload, dict)
        and expected_job in pending_after_timeout.payload.get("jobs", []),
        "Storage timeout lost the durable cleanup receipt.",
    )
    _require(
        repository.read_object(ACCOUNT_DELETION_OBJECT_KEY) == object_content,
        "Storage timeout removed or changed the encrypted object.",
    )

    repository.delete_objects([ACCOUNT_DELETION_OBJECT_KEY])
    _require(
        _object_is_missing(repository, ACCOUNT_DELETION_OBJECT_KEY),
        "Supabase Storage API did not permanently delete the account object.",
    )
    repository.delete_objects([ACCOUNT_DELETION_OBJECT_KEY])
    for _ in range(2):
        completed = _rpc(
            context,
            "exchange_complete_pending_account_deletion_storage",
            {"p_mutation_id": success_mutation},
        )
        _require(
            completed.status == 200
            and isinstance(completed.payload, dict)
            and completed.payload.get("status") == "committed",
            "Administrator Storage completion was not idempotent.",
        )
    empty = _rpc(context, "exchange_list_pending_account_deletion_storage", {"p_limit": 100})
    _require(
        empty.status == 200
        and isinstance(empty.payload, dict)
        and empty.payload.get("jobs") == [],
        f"Storage cleanup queue did not empty: {empty}",
    )
    proof_completion = _rpc(
        context,
        "exchange_complete_account_deletion_storage",
        {"p_mutation_id": success_mutation, "p_session_token_hash": "a" * 64},
    )
    _require(
        proof_completion.status == 200
        and isinstance(proof_completion.payload, dict)
        and proof_completion.payload.get("status") == "committed",
        "Proof-bound Storage completion did not remain idempotent.",
    )
    receipt_state = _psql(
        context,
        f"select count(*) from public.exchange_account_deletion_receipts where mutation_id='{success_mutation}' and storage_completed_at is not null;",
    )
    _require(receipt_state == "1", "Storage completion timestamp was not durable.")
    _psql(
        context,
        f"delete from public.exchange_community_questions where id='runtime-deletion-question';\n"
        f"delete from public.exchange_account_deletion_receipts where mutation_id='{success_mutation}';\n"
        "delete from public.exchange_accounts where id in ('runtime-deletion-issue-owner','runtime-deletion-issue-reviewer');\n",
    )
    workflow_issue_cleanup = _psql(
        context,
        """
select
 (select count(*) from public.application_workflow_issue_reports where id like 'runtime-deletion-issue-%'),
 (select count(*) from public.application_workflow_issue_report_reviews where report_id like 'runtime-deletion-issue-%'),
 (select count(*) from public.exchange_accounts where id like 'runtime-deletion-issue-%');
""",
    )
    _require(
        workflow_issue_cleanup == "0|0|0",
        f"Workflow issue report deletion fixtures were not cleaned: {workflow_issue_cleanup}",
    )
    return {
        "rollback_preserved_rows": 8,
        "storage_timeout_receipts_preserved": 1,
        "storage_objects_deleted": 1,
        "storage_delete_replays": 1,
        "storage_jobs_completed": 1,
        "workflow_issue_rollback_preserved_rows": 4,
        "workflow_issue_pending_deidentified": 2,
        "workflow_issue_closed_deleted": 1,
        "workflow_issue_reviewer_deidentified": 1,
        "workflow_issue_retention_shortened": 1,
        "workflow_issue_purged": 2,
        "workflow_issue_purge_controls_preserved": 1,
        "workflow_issue_review_replays": 1,
    }


def validate_runtime(context: ValidationContext) -> dict[str, Any]:
    print("Starting isolated PostgreSQL...")
    _compose(
        context,
        "up",
        "-d",
        "postgres",
        timeout_seconds=COMPOSE_START_TIMEOUT_SECONDS,
    )
    _wait_for_postgres(context)
    _psql(
        context,
        f"alter role authenticator with login password '{DB_PASSWORD}';\n"
        f"alter role supabase_storage_admin with login password '{DB_PASSWORD}';",
        user="supabase_admin",
    )
    migration_count = _apply_migrations(context)
    print("Starting two isolated PostgREST instances...")
    _compose(
        context,
        "up",
        "-d",
        "postgrest",
        "postgrest_secondary",
        timeout_seconds=COMPOSE_START_TIMEOUT_SECONDS,
    )
    _wait_for_postgrest(context)
    _wait_for_postgrest(context, secondary=True)
    print("Starting isolated Supabase Storage API...")
    _compose(
        context,
        "up",
        "-d",
        "storage",
        timeout_seconds=COMPOSE_START_TIMEOUT_SECONDS,
    )
    _wait_for_storage(context)
    vault_repository = _create_runtime_vault_repository(context)
    print("Validating RLS, grants and direct-DML denial...")
    permissions = _validate_schema_and_permissions(context)
    print("Validating transient-auth concurrency...")
    transient = _validate_transient_auth_concurrency(context)
    print("Validating workspace CAS concurrency...")
    workspace = _validate_workspace_cas(context)
    print("Validating application-workflow issue report RPCs...")
    workflow_issue_reports = _validate_workflow_issue_reports(context)
    print("Validating public/private community concurrency across two API instances...")
    community_multi_instance = _validate_community_multi_instance_concurrency(context)
    print("Validating late-failure rollback for public/private community transactions...")
    community_rollbacks = _validate_community_transaction_rollbacks(context)
    print("Validating recursive Storage listing and orphan cleanup...")
    storage = _validate_storage_orphan_cleanup(context, vault_repository)
    print("Validating account-deletion rollback and real Storage cleanup...")
    deletion = _validate_account_deletion(context, vault_repository)
    return {
        "status": "passed",
        "migration_count": migration_count,
        "permissions": permissions,
        "transient_auth": transient,
        "workspace": workspace,
        "workflow_issue_reports": workflow_issue_reports,
        "community_multi_instance": community_multi_instance,
        "community_rollbacks": community_rollbacks,
        "storage": storage,
        "account_deletion": deletion,
        "storage_api_scope": "real_storage_api_file_backend",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--postgres-port",
        type=int,
        default=0,
        help="0 selects a free loopback port.",
    )
    parser.add_argument(
        "--postgrest-port",
        type=int,
        default=0,
        help="0 selects a free loopback port.",
    )
    parser.add_argument(
        "--postgrest-secondary-port",
        type=int,
        default=0,
        help="0 selects a free loopback port for the second API instance.",
    )
    parser.add_argument(
        "--storage-port",
        type=int,
        default=0,
        help="0 selects a free loopback port.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the isolated stack for inspection.",
    )
    return parser.parse_args(argv)


def _new_project_name(
    environment: Mapping[str, str] | None = None,
) -> str:
    current_environment = os.environ if environment is None else environment
    run_id = current_environment.get("GITHUB_RUN_ID", "")
    run_attempt = current_environment.get("GITHUB_RUN_ATTEMPT", "")
    random_token = secrets.token_hex(4)
    if run_id or run_attempt:
        _require(
            run_id.isascii()
            and run_id.isdigit()
            and run_attempt.isascii()
            and run_attempt.isdigit(),
            "GitHub runtime identity must contain numeric run and attempt values.",
        )
        run_token = hashlib.sha256(
            f"{run_id}:{run_attempt}".encode("ascii")
        ).hexdigest()[:10]
        project_name = f"{PROJECT_NAME_PREFIX}-gh-{run_token}-{random_token}"
    else:
        project_name = (
            f"{PROJECT_NAME_PREFIX}-local-{os.getpid():x}-{random_token}"
        )
    _require(
        re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", project_name) is not None,
        "Generated runtime Compose project name is invalid.",
    )
    return project_name


def _project_resource_ids(context: ValidationContext) -> dict[str, tuple[str, ...]]:
    label = f"label=com.docker.compose.project={context.project_name}"
    commands = {
        "container": ["docker", "container", "ls", "-aq", "--filter", label],
        "network": ["docker", "network", "ls", "-q", "--filter", label],
        "volume": ["docker", "volume", "ls", "-q", "--filter", label],
    }
    resources: dict[str, tuple[str, ...]] = {}
    for kind, command in commands.items():
        completed = _run(
            command,
            timeout_seconds=COMPOSE_CONTROL_TIMEOUT_SECONDS,
        )
        resources[kind] = tuple(
            line.strip() for line in completed.stdout.splitlines() if line.strip()
        )
    return resources


def _cleanup_runtime(context: ValidationContext, *, phase: str) -> None:
    completed = _compose(
        context,
        "down",
        "--volumes",
        "--remove-orphans",
        check=False,
        timeout_seconds=COMPOSE_CONTROL_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeValidationError(
            f"{phase} cleanup failed ({completed.returncode}) for Compose project "
            f"{context.project_name}: {detail or 'no diagnostic output'}"
        )
    for kind, identifiers in _project_resource_ids(context).items():
        if identifiers:
            raise RuntimeValidationError(
                f"{phase} cleanup left residual {kind} resources for Compose project "
                f"{context.project_name}: {', '.join(identifiers)}"
            )


def _collect_runtime_logs(context: ValidationContext) -> str:
    try:
        completed = _compose(
            context,
            "logs",
            "--no-color",
            "--tail",
            "120",
            check=False,
            timeout_seconds=COMPOSE_LOG_TIMEOUT_SECONDS,
        )
    except RuntimeValidationError as error:
        return f"RUNTIME LOG COLLECTION FAILED: {error}"
    output = "\n".join(
        part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
    )
    if completed.returncode != 0:
        return (
            f"RUNTIME LOG COLLECTION FAILED ({completed.returncode}): "
            f"{output or 'no diagnostic output'}"
        )
    return output


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _require(COMPOSE_FILE.is_file(), f"Compose file not found: {COMPOSE_FILE}")
    _require(MIGRATIONS_DIR.is_dir(), f"Migrations directory not found: {MIGRATIONS_DIR}")
    try:
        project_name = _new_project_name()
    except RuntimeValidationError as error:
        print(f"RUNTIME VALIDATION FAILED: {error}", file=sys.stderr)
        return 1
    context = ValidationContext(
        project_name=project_name,
        postgres_port=args.postgres_port or _free_loopback_port(),
        postgrest_port=args.postgrest_port or _free_loopback_port(),
        postgrest_secondary_port=(
            args.postgrest_secondary_port or _free_loopback_port()
        ),
        storage_port=args.storage_port or _free_loopback_port(),
        service_token=_jwt("service_role"),
        anon_token=_jwt("anon"),
    )
    _require(
        len(
            {
                context.postgres_port,
                context.postgrest_port,
                context.postgrest_secondary_port,
                context.storage_port,
            }
        )
        == 4,
        "Runtime ports must be distinct.",
    )
    print(f"Runtime Compose project: {context.project_name}", flush=True)
    primary_error: RuntimeValidationError | None = None
    cleanup_error: RuntimeValidationError | None = None
    result: dict[str, Any] | None = None
    try:
        _run(["docker", "info"], timeout_seconds=DOCKER_INFO_TIMEOUT_SECONDS)
        _cleanup_runtime(context, phase="preflight")
        result = validate_runtime(context)
    except RuntimeValidationError as error:
        primary_error = error
        print(f"RUNTIME VALIDATION FAILED: {error}", file=sys.stderr)
        diagnostic = _collect_runtime_logs(context)
        if diagnostic:
            print(diagnostic, file=sys.stderr)
    finally:
        if args.keep:
            print(
                f"Runtime Compose project kept for inspection: {context.project_name}",
                file=sys.stderr,
            )
        else:
            try:
                _cleanup_runtime(context, phase="final")
            except RuntimeValidationError as error:
                cleanup_error = error
                print(f"RUNTIME CLEANUP FAILED: {error}", file=sys.stderr)

    if primary_error is not None or cleanup_error is not None:
        return 1
    _require(result is not None, "Runtime validation produced no result.")
    result["cleanup_status"] = "skipped_by_keep" if args.keep else "passed"
    result["compose_project"] = context.project_name
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

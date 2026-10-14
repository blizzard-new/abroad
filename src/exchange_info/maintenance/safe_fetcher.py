"""Safe network fetching, conditional requests, 3-tier hashing, and parser guards (Spec Sections 6.4, 7, 10.2, 11.1, 11.2)."""

from __future__ import annotations

import hashlib
import io
import ipaddress
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterable, Literal
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from pypdf import PdfReader

from ..http_client import SSRFError
from ..source_url_policy import canonical_source_url_identity
from .contracts import SourceHealthStatus, canonical_json_hash, utc_now

MAX_HTML_BYTES = 5 * 1024 * 1024        # 5 MiB (Spec 10.2)
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25 MiB (Spec 10.2)
MAX_PDF_PAGES = 200                     # 200 pages (Spec 10.2)
MAX_REDIRECT_HOPS = 5                   # Spec 11.1

SENSITIVE_QUERY_KEYS = frozenset({"token", "access_token", "api_key", "key", "secret", "password", "sig", "signature", "session"})

# Words that must NEVER be stripped during normalization (Spec 7.3 / T13)
CRITICAL_SEMANTIC_TOKENS = (
    "不", "非", "無", "僅限", "限", "除外", "不含", "不得", "未開放", "暫停", "停招", "取消",
    "not", "no", "never", "only", "except", "excluding", "suspended", "closed",
)

PROMPT_INJECTION_PATTERNS = (
    re.compile(r"忽略(?:前述|上述|之前|所有).*?(?:指令|規則|設定|限制)", re.I),
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules)", re.I),
    re.compile(r"system\s*prompt\s*:", re.I),
    re.compile(r"(?:執行|呼叫)\s*(?:shell|bash|powershell|cmd|publish|發布)", re.I),
)


class FetchPolicyError(ValueError):
    """Raised when a URL or response violates the safe fetching policy."""

    def __init__(self, message: str, *, error_class: str = "policy_violation") -> None:
        super().__init__(message)
        self.error_class = error_class


def redact_url_for_log(url: str) -> str:
    """Mask sensitive query parameters in logs and error records (Spec 11.1)."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return "[invalid-url]"
    if not parts.query:
        return url
    masked_pairs = []
    for pair in parts.query.split("&"):
        key, sep, val = pair.partition("=")
        if key.strip().lower() in SENSITIVE_QUERY_KEYS:
            masked_pairs.append(f"{key}=[REDACTED]" if sep else key)
        else:
            masked_pairs.append(pair)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "&".join(masked_pairs), ""))


def validate_and_canonicalize_source_url(
    url: str,
    *,
    approved_domains: Iterable[str],
    allow_ports: Iterable[int] = (443,),
    resolver: Callable[[str, int], list[str]] | None = None,
) -> tuple[str, list[str]]:
    """Canonicalize URL and enforce HTTPS, no userinfo, approved domain, and public IP resolution (Spec 11.1 / T21)."""
    raw = (url or "").strip()
    if not raw:
        raise FetchPolicyError("URL cannot be empty", error_class="invalid_url")

    lowered = raw.lower()
    if lowered.startswith(("file:", "data:", "javascript:", "ftp:", "gopher:")):
        raise FetchPolicyError(f"Disallowed URL scheme in {redact_url_for_log(raw)}", error_class="ssrf_blocked")

    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        raise FetchPolicyError(f"Malformed URL: {exc}", error_class="invalid_url") from exc

    if parsed.scheme.lower() != "https":
        raise FetchPolicyError("Only HTTPS scheme is allowed by default", error_class="ssrf_blocked")

    if parsed.username or parsed.password or "@" in parsed.netloc:
        raise FetchPolicyError("Credentials in URL userinfo are forbidden", error_class="ssrf_blocked")

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname or hostname in {"localhost", "localhost.localdomain"} or hostname.endswith((".local", ".internal", ".lan")):
        raise FetchPolicyError(f"Blocked internal hostname: {hostname}", error_class="ssrf_blocked")

    try:
        port = parsed.port or 443
    except ValueError as exc:
        raise FetchPolicyError("Invalid port in URL", error_class="ssrf_blocked") from exc

    if port not in set(allow_ports):
        raise FetchPolicyError(f"Port {port} is not in allowed ports", error_class="ssrf_blocked")

    approved = {d.strip().lower().rstrip(".") for d in approved_domains if d and d.strip()}
    if not approved:
        raise FetchPolicyError("No approved domains configured for this source", error_class="unapproved_domain")

    domain_matched = any(
        hostname == allowed_domain or hostname.endswith(f".{allowed_domain}")
        for allowed_domain in approved
    )
    if not domain_matched:
        raise FetchPolicyError(
            f"Host '{hostname}' is not in approved domains {sorted(approved)}",
            error_class="unapproved_domain",
        )

    # Resolve IPs and verify every single resolved IP is global & public (prevents DNS rebinding / metadata SSRF)
    if resolver is not None:
        resolved_ips = resolver(hostname, port)
    else:
        try:
            infos = socket.getaddrinfo(hostname, port, 0, socket.SOCK_STREAM)
            resolved_ips = [info[4][0] for info in infos]
        except socket.gaierror as exc:
            raise FetchPolicyError(f"DNS resolution failed for {hostname}", error_class="dns_error") from exc

    if not resolved_ips:
        raise FetchPolicyError(f"No IP addresses resolved for {hostname}", error_class="dns_error")

    verified_public_ips: list[str] = []
    for ip_str in resolved_ips:
        clean_ip = ip_str.split("%", 1)[0]
        try:
            ip_obj = ipaddress.ip_address(clean_ip)
        except ValueError as exc:
            raise FetchPolicyError(f"Invalid resolved IP '{ip_str}'", error_class="ssrf_blocked") from exc
        if (
            not ip_obj.is_global
            or ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
            or clean_ip == "169.254.169.254"
        ):
            raise FetchPolicyError(
                f"SSRF blocked: {hostname} resolved to non-public IP {clean_ip}",
                error_class="ssrf_blocked",
            )
        if clean_ip not in verified_public_ips:
            verified_public_ips.append(clean_ip)

    canonical_url = canonical_source_url_identity(
        urlunsplit(("https", hostname if port == 443 else f"{hostname}:{port}", parsed.path or "/", parsed.query, ""))
    )
    return canonical_url, verified_public_ips


def verify_mime_and_magic_bytes(content: bytes, declared_mime: str | None, expected_kind: str) -> str:
    """Verify magic bytes and MIME header without trusting file extensions (Spec 11.1)."""
    if not content:
        raise FetchPolicyError("Empty response body", error_class="empty_body")

    head = content[:1024].lstrip()
    mime = (declared_mime or "").split(";", 1)[0].strip().lower()

    if expected_kind == "pdf_attachment" or mime == "application/pdf":
        if not content.startswith(b"%PDF-"):
            raise FetchPolicyError("File does not start with %PDF- magic header", error_class="mime_rejected")
        return "application/pdf"

    if expected_kind in {"html_list", "html_detail"}:
        if content.startswith((b"%PDF-", b"PK\x03\x04", b"\x7fELF", b"MZ")):
            raise FetchPolicyError("Binary payload rejected where HTML was expected", error_class="mime_rejected")
        if mime and mime not in {"text/html", "application/xhtml+xml", "text/plain"}:
            raise FetchPolicyError(f"Unexpected MIME '{mime}' for HTML resource", error_class="mime_rejected")
        return "text/html"

    if expected_kind == "api_json":
        if not head.startswith((b"{", b"[")):
            raise FetchPolicyError("Payload does not start with JSON object/array", error_class="mime_rejected")
        return "application/json"

    return mime or "application/octet-stream"


def compute_normalized_html_hash(html_bytes: bytes, *, normalization_version: str = "v1") -> tuple[str, str]:
    """Normalize HTML by stripping navigation/view-counters while preserving table cells, footnotes, and negations (Spec 7.2, 7.3)."""
    text_raw = html_bytes.decode("utf-8", errors="replace")
    soup = BeautifulSoup(text_raw, "html.parser")

    for tag in soup.find_all(["script", "style", "noscript", "nav", "footer", "header", "iframe"]):
        tag.decompose()

    cleaned_lines: list[str] = []
    for raw_line in soup.get_text("\n").splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue
        # Strip view counters / tracking noise ONLY when the line contains no critical semantic tokens
        if re.search(r"(?:瀏覽人次|點閱數|瀏覽人數|點閱率|更新日期\s*[:：]?\s*\d+|\bviews?\s*:\s*\d+)", line, re.I):
            if not any(tok in line.lower() for tok in CRITICAL_SEMANTIC_TOKENS):
                continue
        cleaned_lines.append(line)

    normalized_text = f"[norm:{normalization_version}]\n" + "\n".join(cleaned_lines)
    norm_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    return norm_hash, "\n".join(cleaned_lines)


def extract_and_normalize_pdf(pdf_bytes: bytes, *, max_pages: int = MAX_PDF_PAGES) -> tuple[str, str, int]:
    """Safely extract text from PDF with page cap and normalized hash (Spec 7.2, 10.2, T22)."""
    if len(pdf_bytes) > MAX_ATTACHMENT_BYTES:
        raise FetchPolicyError(
            f"PDF exceeds maximum allowed size ({len(pdf_bytes)} > {MAX_ATTACHMENT_BYTES} bytes)",
            error_class="size_exceeded",
        )
    if not pdf_bytes.startswith(b"%PDF-"):
        raise FetchPolicyError("Invalid PDF magic header", error_class="mime_rejected")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
        page_count = len(reader.pages)
    except Exception as exc:
        raise FetchPolicyError(f"PDF structure parse failed: {exc}", error_class="pdf_corrupt") from exc

    if page_count > max_pages:
        raise FetchPolicyError(
            f"PDF page count {page_count} exceeds hard limit {max_pages}; routed to manual review without truncation",
            error_class="page_limit_exceeded",
        )

    page_texts: list[str] = []
    total_extracted_chars = 0
    for idx, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception as exc:
            raise FetchPolicyError(f"PDF page {idx} extraction failed: {exc}", error_class="pdf_corrupt") from exc
        total_extracted_chars += len(txt)
        if total_extracted_chars > 5_000_000:
            raise FetchPolicyError("PDF extracted text exceeds decompression safety cap", error_class="decompression_bomb")
        lines = [" ".join(line.strip().split()) for line in txt.splitlines() if line.strip()]
        page_texts.append(f"[PAGE {idx}]\n" + "\n".join(lines))

    combined = "\n\n".join(page_texts)
    norm_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return norm_hash, combined, page_count


def compute_semantic_field_hash(assertions_summary: list[dict[str, Any]]) -> str:
    """Compute semantic_field_hash from canonical sorted typed fields, states, units, and scopes (Spec 7.2)."""
    canonical_items = []
    for item in assertions_summary:
        canonical_items.append(
            {
                "entity_scope": item.get("entity_scope", ""),
                "field_path": item.get("field_path", ""),
                "typed_value": item.get("typed_value"),
                "value_state": item.get("value_state", ""),
                "unit": item.get("unit"),
                "effective_scope": item.get("effective_scope", {}),
            }
        )
    canonical_items.sort(key=lambda r: (r["entity_scope"], r["field_path"], json.dumps(r["effective_scope"], sort_keys=True)))
    return canonical_json_hash(canonical_items)


def sanitize_untrusted_text_for_extraction(text: str) -> tuple[str, bool]:
    """Treat external content strictly as data; detect & neutralize prompt-injection attempts (Spec 11.2 / T23)."""
    flagged = False
    sanitized = text
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(sanitized):
            flagged = True
            sanitized = pattern.sub("[UNTRUSTED_DIRECTIVE_IGNORED]", sanitized)
    return sanitized, flagged


@dataclass
class SimulatedHttpResponse:
    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    redirect_location: str | None = None


@dataclass
class SafeFetchOutcome:
    outcome: Literal[
        "fetched_200",
        "not_modified_304",
        "http_error",
        "network_error",
        "ssrf_blocked",
        "size_exceeded",
        "mime_rejected",
    ]
    status_code: int | None
    canonical_url: str
    redirect_chain: list[str]
    raw_bytes: bytes | None = None
    raw_sha256: str | None = None
    normalized_content_hash: str | None = None
    normalized_text: str | None = None
    mime: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    retry_after_seconds: int | None = None
    error_class: str | None = None
    error_message: str | None = None
    source_health: SourceHealthStatus = SourceHealthStatus.HEALTHY
    should_retry: bool = False
    backoff_minutes: int | None = None


BACKOFF_SCHEDULE_MINUTES = (1, 5, 15, 60, 60)


def classify_http_failure(status_code: int, headers: dict[str, str], attempt: int) -> tuple[SourceHealthStatus, bool, int | None, int | None]:
    """Classify HTTP errors per Spec Section 6.4 (T08)."""
    retry_after_raw = headers.get("Retry-After") or headers.get("retry-after")
    retry_after_sec: int | None = None
    if retry_after_raw and retry_after_raw.strip().isdigit():
        retry_after_sec = max(1, min(int(retry_after_raw.strip()), 86400))

    if status_code == 429:
        backoff = max(1, (retry_after_sec // 60) if retry_after_sec else BACKOFF_SCHEDULE_MINUTES[min(attempt, len(BACKOFF_SCHEDULE_MINUTES) - 1)])
        return SourceHealthStatus.TEMPORARY_ERROR, attempt < 5, retry_after_sec or (backoff * 60), backoff

    if status_code in {401, 403}:
        # Spec 6.4: Stop automatic fetching for this source, hand to admin; never bypass or delete data
        return SourceHealthStatus.BLOCKED, False, None, None

    if status_code in {404, 410}:
        # Spec 6.4: Record resource missing; do not automatically mark exchange offering closed
        return SourceHealthStatus.MISSING, False, None, None

    if 500 <= status_code <= 599 or status_code == 408:
        if attempt < 5:
            backoff = BACKOFF_SCHEDULE_MINUTES[min(attempt, len(BACKOFF_SCHEDULE_MINUTES) - 1)]
            return SourceHealthStatus.TEMPORARY_ERROR, True, backoff * 60, backoff
        return SourceHealthStatus.TEMPORARY_ERROR, False, None, None

    return SourceHealthStatus.TEMPORARY_ERROR, False, None, None


def execute_safe_fetch(
    url: str,
    *,
    approved_domains: Iterable[str],
    resource_kind: str = "html_detail",
    prior_etag: str | None = None,
    prior_last_modified: str | None = None,
    force_unconditional: bool = False,
    attempt: int = 0,
    transport: Callable[[str, dict[str, str]], SimulatedHttpResponse] | None = None,
    resolver: Callable[[str, int], list[str]] | None = None,
) -> SafeFetchOutcome:
    """Execute a safe, conditional, size-bounded fetch with redirect validation (Spec 6.4, 7.1, 10.2, 11.1)."""
    redirect_chain: list[str] = []
    current_url = url
    max_bytes = MAX_ATTACHMENT_BYTES if resource_kind in {"pdf_attachment", "doc_attachment"} else MAX_HTML_BYTES

    for hop in range(MAX_REDIRECT_HOPS + 1):
        try:
            canonical_url, _ = validate_and_canonicalize_source_url(
                current_url,
                approved_domains=approved_domains,
                resolver=resolver,
            )
        except FetchPolicyError as exc:
            return SafeFetchOutcome(
                outcome="ssrf_blocked",
                status_code=None,
                canonical_url=redact_url_for_log(current_url),
                redirect_chain=redirect_chain,
                error_class=exc.error_class,
                error_message=str(exc),
                source_health=SourceHealthStatus.BLOCKED,
                should_retry=False,
            )

        req_headers: dict[str, str] = {"User-Agent": "Uniway-Maintenance-Worker/1.1 (+https://app.uniway-tw.com)"}
        # Never send admin cookies, tokens, or cloud credentials (Spec 11.1)
        if not force_unconditional:
            if prior_etag:
                req_headers["If-None-Match"] = prior_etag
            if prior_last_modified:
                req_headers["If-Modified-Since"] = prior_last_modified

        if transport is None:
            raise FetchPolicyError("Live network transport is disabled in dry-run/test mode unless explicitly provided", error_class="network_disabled")

        try:
            resp = transport(canonical_url, req_headers)
        except SSRFError as exc:
            return SafeFetchOutcome(
                outcome="ssrf_blocked",
                status_code=None,
                canonical_url=canonical_url,
                redirect_chain=redirect_chain,
                error_class="ssrf_blocked",
                error_message=str(exc),
                source_health=SourceHealthStatus.BLOCKED,
                should_retry=False,
            )
        except TimeoutError as exc:
            backoff = BACKOFF_SCHEDULE_MINUTES[min(attempt, len(BACKOFF_SCHEDULE_MINUTES) - 1)]
            return SafeFetchOutcome(
                outcome="network_error",
                status_code=None,
                canonical_url=canonical_url,
                redirect_chain=redirect_chain,
                error_class="timeout",
                error_message=str(exc),
                source_health=SourceHealthStatus.TEMPORARY_ERROR,
                should_retry=attempt < 5,
                backoff_minutes=backoff if attempt < 5 else None,
            )

        if resp.status_code in {301, 302, 303, 307, 308}:
            if hop >= MAX_REDIRECT_HOPS:
                return SafeFetchOutcome(
                    outcome="ssrf_blocked",
                    status_code=resp.status_code,
                    canonical_url=canonical_url,
                    redirect_chain=redirect_chain,
                    error_class="too_many_redirects",
                    error_message="Exceeded maximum allowed redirect hops",
                    source_health=SourceHealthStatus.BLOCKED,
                    should_retry=False,
                )
            loc = resp.redirect_location or resp.headers.get("Location") or resp.headers.get("location")
            if not loc:
                return SafeFetchOutcome(
                    outcome="http_error",
                    status_code=resp.status_code,
                    canonical_url=canonical_url,
                    redirect_chain=redirect_chain,
                    error_class="invalid_redirect",
                    error_message="Redirect response missing Location header",
                    source_health=SourceHealthStatus.TEMPORARY_ERROR,
                    should_retry=False,
                )
            redirect_chain.append(canonical_url)
            current_url = urljoin(canonical_url, loc)
            continue

        if resp.status_code == 304:
            return SafeFetchOutcome(
                outcome="not_modified_304",
                status_code=304,
                canonical_url=canonical_url,
                redirect_chain=redirect_chain,
                etag=resp.headers.get("ETag") or prior_etag,
                last_modified=resp.headers.get("Last-Modified") or prior_last_modified,
                source_health=SourceHealthStatus.HEALTHY,
                should_retry=False,
            )

        if resp.status_code >= 400:
            health, should_retry, retry_after, backoff = classify_http_failure(resp.status_code, resp.headers, attempt)
            return SafeFetchOutcome(
                outcome="http_error",
                status_code=resp.status_code,
                canonical_url=canonical_url,
                redirect_chain=redirect_chain,
                retry_after_seconds=retry_after,
                error_class=f"http_{resp.status_code}",
                error_message=f"HTTP {resp.status_code} from {redact_url_for_log(canonical_url)}",
                source_health=health,
                should_retry=should_retry,
                backoff_minutes=backoff,
            )

        if len(resp.body) > max_bytes:
            return SafeFetchOutcome(
                outcome="size_exceeded",
                status_code=resp.status_code,
                canonical_url=canonical_url,
                redirect_chain=redirect_chain,
                error_class="size_exceeded",
                error_message=f"Payload size {len(resp.body)} exceeds max {max_bytes} bytes for {resource_kind}",
                source_health=SourceHealthStatus.TEMPORARY_ERROR,
                should_retry=False,
            )

        try:
            verified_mime = verify_mime_and_magic_bytes(resp.body, resp.headers.get("Content-Type"), resource_kind)
            raw_sha256 = hashlib.sha256(resp.body).hexdigest()
            if verified_mime == "application/pdf":
                norm_hash, norm_text, _ = extract_and_normalize_pdf(resp.body)
            else:
                norm_hash, norm_text = compute_normalized_html_hash(resp.body)
        except FetchPolicyError as exc:
            return SafeFetchOutcome(
                outcome="mime_rejected" if exc.error_class == "mime_rejected" else "size_exceeded",
                status_code=resp.status_code,
                canonical_url=canonical_url,
                redirect_chain=redirect_chain,
                error_class=exc.error_class,
                error_message=str(exc),
                source_health=SourceHealthStatus.TEMPORARY_ERROR,
                should_retry=False,
            )

        return SafeFetchOutcome(
            outcome="fetched_200",
            status_code=200,
            canonical_url=canonical_url,
            redirect_chain=redirect_chain,
            raw_bytes=resp.body,
            raw_sha256=raw_sha256,
            normalized_content_hash=norm_hash,
            normalized_text=norm_text,
            mime=verified_mime,
            etag=resp.headers.get("ETag"),
            last_modified=resp.headers.get("Last-Modified"),
            source_health=SourceHealthStatus.HEALTHY,
            should_retry=False,
        )

    return SafeFetchOutcome(
        outcome="ssrf_blocked",
        status_code=None,
        canonical_url=redact_url_for_log(current_url),
        redirect_chain=redirect_chain,
        error_class="too_many_redirects",
        error_message="Exceeded redirect hops",
        source_health=SourceHealthStatus.BLOCKED,
        should_retry=False,
    )

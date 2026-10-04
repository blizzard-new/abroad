from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import requests


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    REPOSITORY_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "review"
    / "source_metadata_research_candidates.json"
)
USER_AGENT = "UniWay source-metadata research audit/1.0"
DEFAULT_MAX_BODY_BYTES = 1024 * 1024
_TITLE_PATTERN = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_NOT_FOUND_MARKERS = (
    "找不到",
    "頁面不存在",
    "页面不存在",
    "page not found",
    "not found",
    "does not exist",
    "has been deleted or moved",
)


@dataclass(frozen=True)
class SourceMetadataObservation:
    url: str
    transport_status: str
    application_level_status: str
    final_url: str | None
    http_status: int | None
    redirect_count: int
    content_type: str | None
    bytes_inspected: int
    detected_title: str | None
    error: str | None = None


def _read_bounded_body(response: Any, *, max_body_bytes: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=8192):
        if not chunk:
            continue
        remaining = max_body_bytes - size
        if remaining <= 0:
            break
        part = bytes(chunk[:remaining])
        chunks.append(part)
        size += len(part)
        if size >= max_body_bytes:
            break
    return b"".join(chunks)


def _decode_html(body: bytes, response: Any) -> str:
    encoding = getattr(response, "encoding", None) or "utf-8"
    try:
        return body.decode(encoding, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def _extract_title(document: str) -> str | None:
    match = _TITLE_PATTERN.search(document)
    if match is None:
        return None
    title = html.unescape(_TAG_PATTERN.sub(" ", match.group(1)))
    title = " ".join(title.split())
    return title or None


def _normalized_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKC", html.unescape(value)).casefold()
    return re.sub(r"[\W_]+", "", normalized, flags=re.UNICODE)


def _classify_html(document: str) -> str:
    visible_text = html.unescape(_TAG_PATTERN.sub(" ", document)).casefold()
    compact_text = " ".join(visible_text.split())
    if any(marker in compact_text for marker in _NOT_FOUND_MARKERS):
        return "not_found_page"
    return "content_available" if compact_text else "unexpected_content"


def inspect_source_metadata_candidate(
    url: str,
    *,
    session: Any = requests,
    timeout: float = 20.0,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
) -> SourceMetadataObservation:
    """Inspect a bounded response preview without saving or mutating research data."""

    response = None
    try:
        response = session.get(
            url,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=timeout,
        )
        final_url = str(response.url)
        http_status = int(response.status_code)
        content_type = response.headers.get("content-type")
        final_scheme = urlsplit(final_url).scheme.casefold()
        if final_scheme == "http":
            transport_status = "downgrades_to_http"
        elif final_scheme == "https" and 200 <= http_status < 300:
            transport_status = "verified_https"
        else:
            transport_status = "unverified"

        if transport_status != "verified_https":
            return SourceMetadataObservation(
                url=url,
                transport_status=transport_status,
                application_level_status="unverified",
                final_url=final_url,
                http_status=http_status,
                redirect_count=len(response.history),
                content_type=content_type,
                bytes_inspected=0,
                detected_title=None,
            )

        body = _read_bounded_body(response, max_body_bytes=max_body_bytes)
        lowered_content_type = (content_type or "").casefold()
        expects_pdf = urlsplit(final_url).path.casefold().endswith(".pdf")
        if "application/pdf" in lowered_content_type or expects_pdf:
            application_level_status = (
                "content_available"
                if body.lstrip().startswith(b"%PDF-")
                else "unexpected_content"
            )
            detected_title = None
        else:
            document = _decode_html(body, response)
            application_level_status = _classify_html(document)
            detected_title = _extract_title(document)

        return SourceMetadataObservation(
            url=url,
            transport_status=transport_status,
            application_level_status=application_level_status,
            final_url=final_url,
            http_status=http_status,
            redirect_count=len(response.history),
            content_type=content_type,
            bytes_inspected=len(body),
            detected_title=detected_title,
        )
    except requests.RequestException as exc:
        return SourceMetadataObservation(
            url=url,
            transport_status="unverified",
            application_level_status="unverified",
            final_url=None,
            http_status=None,
            redirect_count=0,
            content_type=None,
            bytes_inspected=0,
            detected_title=None,
            error=f"{type(exc).__name__}: {exc}",
        )
    finally:
        if response is not None:
            response.close()


def load_candidate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("items"), list):
        raise ValueError("來源中繼資料研究 manifest 缺少 items 清單。")
    return manifest


def audit_source_metadata_manifest(
    manifest: dict[str, Any],
    *,
    session: Any = requests,
    timeout: float = 20.0,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
) -> tuple[list[SourceMetadataObservation], list[str]]:
    observations_by_url: dict[str, SourceMetadataObservation] = {}
    mismatches: list[str] = []

    def observe(url: str) -> SourceMetadataObservation:
        key = url.casefold()
        if key not in observations_by_url:
            observations_by_url[key] = inspect_source_metadata_candidate(
                url,
                session=session,
                timeout=timeout,
                max_body_bytes=max_body_bytes,
            )
        return observations_by_url[key]

    for item_value in manifest["items"]:
        item = dict(item_value)
        source_url = str(item["source_url"])
        observation = observe(source_url)
        expected = (
            "verified_https",
            item.get("application_level_status"),
            item.get("transport_final_url"),
            item.get("transport_http_status"),
        )
        actual = (
            observation.transport_status,
            observation.application_level_status,
            observation.final_url,
            observation.http_status,
        )
        if expected != actual:
            mismatches.append(
                f"source {source_url}: manifest={expected!r}, live={actual!r}"
            )
        if item.get("can_prefill") is not False:
            mismatches.append(f"source {source_url}: can_prefill must remain false")

        proposed_title = item.get("proposed_title")
        if (
            observation.application_level_status == "content_available"
            and observation.detected_title
            and proposed_title
            and _normalized_text(observation.detected_title)
            != _normalized_text(str(proposed_title))
        ):
            mismatches.append(
                f"source {source_url}: proposed_title={proposed_title!r}, "
                f"live_title={observation.detected_title!r}"
            )

        for lead_value in item.get("research_leads", []):
            lead = dict(lead_value)
            lead_url = str(lead["url"])
            if lead.get("eligible_as_replacement") is not False:
                mismatches.append(
                    f"research_lead {lead_url}: eligible_as_replacement must remain false"
                )
            lead_observation = observe(lead_url)
            lead_expected = (
                "verified_https",
                lead.get("transport_final_url"),
                lead.get("transport_http_status"),
            )
            lead_actual = (
                lead_observation.transport_status,
                lead_observation.final_url,
                lead_observation.http_status,
            )
            if lead_expected != lead_actual:
                mismatches.append(
                    f"research_lead {lead_url}: "
                    f"manifest={lead_expected!r}, live={lead_actual!r}"
                )

    return list(observations_by_url.values()), mismatches


def _observation_payloads(
    observations: Iterable[SourceMetadataObservation],
) -> list[dict[str, Any]]:
    return [asdict(item) for item in observations]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only transport and bounded application-level drift audit for "
            "source-metadata research candidates. This command never edits, "
            "prefills, approves, or publishes workflow data."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Source-metadata research manifest to inspect.",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--max-body-bytes",
        type=int,
        default=DEFAULT_MAX_BODY_BYTES,
        help="Maximum in-memory response preview per unique URL.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero when live transport or application status drifts.",
    )
    args = parser.parse_args()
    if args.max_body_bytes < 5:
        parser.error("--max-body-bytes must be at least 5")

    manifest = load_candidate_manifest(args.manifest)
    observations, mismatches = audit_source_metadata_manifest(
        manifest,
        timeout=args.timeout,
        max_body_bytes=args.max_body_bytes,
    )
    print(
        json.dumps(
            _observation_payloads(observations),
            ensure_ascii=False,
            indent=2,
        )
    )
    if mismatches:
        print("\nSource metadata drift mismatches:")
        for mismatch in mismatches:
            print(f"- {mismatch}")
    return 1 if args.check and mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import sys
from urllib.parse import urlsplit

import requests

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
from exchange_info.http_client import get_safe_session
DEFAULT_MANIFEST = (
    REPOSITORY_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "review"
    / "source_replacement_candidates.json"
)
USER_AGENT = "UniWay source-replacement transport audit/1.0"


@dataclass(frozen=True)
class TransportObservation:
    url: str
    transport_status: str
    final_url: str | None
    http_status: int | None
    redirect_count: int
    content_type: str | None
    error: str | None = None


def inspect_candidate_transport(
    url: str,
    *,
    session: Any = None,
    timeout: float = 20.0,
) -> TransportObservation:
    """Inspect redirects and headers without retaining the response body."""
    if session is None:
        session = get_safe_session(require_https=False)

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
        final_scheme = urlsplit(final_url).scheme.casefold()
        if final_scheme == "http":
            transport_status = "downgrades_to_http"
        elif final_scheme == "https" and 200 <= http_status < 300:
            transport_status = "verified_https"
        else:
            transport_status = "unverified"
        return TransportObservation(
            url=url,
            transport_status=transport_status,
            final_url=final_url,
            http_status=http_status,
            redirect_count=len(response.history),
            content_type=response.headers.get("content-type"),
        )
    except requests.RequestException as exc:
        return TransportObservation(
            url=url,
            transport_status="unverified",
            final_url=None,
            http_status=None,
            redirect_count=0,
            content_type=None,
            error=f"{type(exc).__name__}: {exc}",
        )
    finally:
        if response is not None:
            response.close()


def load_candidate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("items"), list):
        raise ValueError("來源替換 manifest 缺少 items 清單。")
    return manifest


def audit_manifest_transports(
    manifest: dict[str, Any],
    *,
    session: Any = None,
    timeout: float = 20.0,
) -> tuple[list[TransportObservation], list[str]]:
    if session is None:
        session = get_safe_session(require_https=False)
    observations_by_url: dict[str, TransportObservation] = {}
    mismatches: list[str] = []

    def observe(url: str) -> TransportObservation:
        key = url.casefold()
        if key not in observations_by_url:
            observations_by_url[key] = inspect_candidate_transport(
                url,
                session=session,
                timeout=timeout,
            )
        return observations_by_url[key]

    def compare_exact(
        *,
        workflow_id: str,
        role: str,
        url: str,
        expected: tuple[Any, Any, Any],
    ) -> None:
        observed = observe(url)
        actual = (
            observed.transport_status,
            observed.final_url,
            observed.http_status,
        )
        if expected != actual:
            mismatches.append(
                f"{workflow_id} {role} {url}: "
                f"manifest={expected!r}, live={actual!r}"
            )

    for item in manifest["items"]:
        workflow_id = str(item.get("workflow_id"))
        candidate_url = str(item["candidate_url"])
        compare_exact(
            workflow_id=workflow_id,
            role="candidate",
            url=candidate_url,
            expected=(
                item.get("transport_status"),
                item.get("transport_final_url"),
                item.get("transport_http_status"),
            ),
        )

        for supporting_url_value in item.get("supporting_urls", []):
            supporting_url = str(supporting_url_value)
            observed = observe(supporting_url)
            if observed.transport_status != "verified_https":
                mismatches.append(
                    f"{workflow_id} supporting {supporting_url}: "
                    "expected='verified_https', "
                    f"live={observed.transport_status!r}, "
                    f"final={observed.final_url!r}, status={observed.http_status!r}"
                )

        for lead_value in item.get("research_leads", []):
            lead = dict(lead_value)
            lead_url = str(lead["url"])
            if lead.get("eligible_as_replacement") is not False:
                mismatches.append(
                    f"{workflow_id} research_lead {lead_url}: "
                    "eligible_as_replacement must remain false"
                )
            compare_exact(
                workflow_id=workflow_id,
                role="research_lead",
                url=lead_url,
                expected=(
                    lead.get("transport_status"),
                    lead.get("transport_final_url"),
                    lead.get("transport_http_status"),
                ),
            )
    return list(observations_by_url.values()), mismatches


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only HTTPS redirect audit for source-replacement candidates, "
            "supporting URLs, and ineligible research leads. "
            "This command never edits, approves, or publishes workflow data."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Candidate manifest to inspect.",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero when live transport differs from the manifest.",
    )
    args = parser.parse_args()

    manifest = load_candidate_manifest(args.manifest)
    observations, mismatches = audit_manifest_transports(
        manifest,
        timeout=args.timeout,
    )
    print(json.dumps([asdict(item) for item in observations], ensure_ascii=False, indent=2))
    if mismatches:
        print("\nTransport mismatches:")
        for mismatch in mismatches:
            print(f"- {mismatch}")
    return 1 if args.check and mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())

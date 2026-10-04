from __future__ import annotations

import requests

from scripts.check_source_replacement_transports import (
    audit_manifest_transports,
    inspect_candidate_transport,
)


class _FakeResponse:
    def __init__(
        self,
        *,
        url: str,
        status_code: int = 200,
        redirect_count: int = 0,
        content_type: str = "text/html; charset=utf-8",
    ) -> None:
        self.url = url
        self.status_code = status_code
        self.history = [object()] * redirect_count
        self.headers = {"content-type": content_type}
        self.closed = False

    @property
    def content(self) -> bytes:
        raise AssertionError("transport audit must not read or retain response bodies")

    def close(self) -> None:
        self.closed = True


class _FakeSession:
    def __init__(self, outcomes: dict[str, _FakeResponse | Exception]) -> None:
        self.outcomes = outcomes
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        outcome = self.outcomes[url]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_transport_inspection_detects_https_downgrade_without_reading_body() -> None:
    candidate_url = "https://exchange.example.edu/incoming"
    response = _FakeResponse(
        url="http://exchange.example.edu/incoming",
        redirect_count=1,
    )
    session = _FakeSession({candidate_url: response})

    observation = inspect_candidate_transport(candidate_url, session=session)

    assert observation.transport_status == "downgrades_to_http"
    assert observation.final_url == "http://exchange.example.edu/incoming"
    assert observation.http_status == 200
    assert observation.redirect_count == 1
    assert response.closed is True
    assert session.calls[0][1]["stream"] is True
    assert session.calls[0][1]["allow_redirects"] is True


def test_transport_inspection_fails_closed_on_network_error() -> None:
    candidate_url = "https://exchange.example.edu/incoming"
    session = _FakeSession(
        {candidate_url: requests.ConnectionError("connection unavailable")}
    )

    observation = inspect_candidate_transport(candidate_url, session=session)

    assert observation.transport_status == "unverified"
    assert observation.final_url is None
    assert observation.http_status is None
    assert "ConnectionError" in (observation.error or "")


def test_manifest_audit_deduplicates_urls_and_reports_live_mismatch() -> None:
    candidate_url = "https://exchange.example.edu/incoming"
    response = _FakeResponse(url=candidate_url)
    supporting_url = "https://exchange.example.edu/context"
    lead_url = "https://exchange.example.edu/apply"
    session = _FakeSession(
        {
            candidate_url: response,
            supporting_url: _FakeResponse(url=supporting_url),
            lead_url: _FakeResponse(url=lead_url),
        }
    )
    manifest = {
        "items": [
            {
                "workflow_id": "workflow-first",
                "candidate_url": candidate_url,
                "transport_status": "verified_https",
                "transport_final_url": candidate_url,
                "transport_http_status": 200,
                "supporting_urls": [supporting_url],
                "research_leads": [
                    {
                        "url": lead_url,
                        "transport_status": "verified_https",
                        "transport_final_url": lead_url,
                        "transport_http_status": 200,
                        "eligible_as_replacement": False,
                    }
                ],
            },
            {
                "workflow_id": "workflow-second",
                "candidate_url": candidate_url,
                "transport_status": "downgrades_to_http",
                "transport_final_url": "http://exchange.example.edu/incoming",
                "transport_http_status": 200,
                "supporting_urls": [supporting_url],
                "research_leads": [],
            },
        ]
    }

    observations, mismatches = audit_manifest_transports(
        manifest,
        session=session,
    )

    assert len(session.calls) == 3
    assert len(observations) == 3
    assert len(mismatches) == 1
    assert "workflow-second" in mismatches[0]


def test_manifest_audit_checks_supporting_urls_and_ineligible_research_leads() -> None:
    candidate_url = "https://exchange.example.edu/incoming"
    supporting_url = "https://exchange.example.edu/context"
    lead_url = "https://exchange.example.edu/apply"
    session = _FakeSession(
        {
            candidate_url: _FakeResponse(url=candidate_url),
            supporting_url: _FakeResponse(url="http://exchange.example.edu/context"),
            lead_url: _FakeResponse(url=lead_url),
        }
    )
    manifest = {
        "items": [
            {
                "workflow_id": "workflow-first",
                "candidate_url": candidate_url,
                "transport_status": "verified_https",
                "transport_final_url": candidate_url,
                "transport_http_status": 200,
                "supporting_urls": [supporting_url],
                "research_leads": [
                    {
                        "url": lead_url,
                        "transport_status": "verified_https",
                        "transport_final_url": lead_url,
                        "transport_http_status": 200,
                        "eligible_as_replacement": True,
                    }
                ],
            }
        ]
    }

    _, mismatches = audit_manifest_transports(manifest, session=session)

    assert len(mismatches) == 2
    assert any("supporting" in item and "verified_https" in item for item in mismatches)
    assert any("eligible_as_replacement" in item for item in mismatches)

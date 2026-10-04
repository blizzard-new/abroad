from __future__ import annotations

import requests

from scripts.check_source_metadata_research import (
    audit_source_metadata_manifest,
    inspect_source_metadata_candidate,
)


class _FakeResponse:
    def __init__(
        self,
        *,
        url: str,
        body: bytes,
        status_code: int = 200,
        redirect_count: int = 0,
        content_type: str = "text/html; charset=utf-8",
        encoding: str = "utf-8",
    ) -> None:
        self.url = url
        self.status_code = status_code
        self.history = [object()] * redirect_count
        self.headers = {"content-type": content_type}
        self.encoding = encoding
        self.body = body
        self.closed = False
        self.iterated_bytes = 0

    def iter_content(self, *, chunk_size: int):
        for start in range(0, len(self.body), chunk_size):
            chunk = self.body[start : start + chunk_size]
            self.iterated_bytes += len(chunk)
            yield chunk

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


def test_inspection_recognizes_real_pdf_magic_with_bounded_read() -> None:
    url = "https://example.edu/exchange.pdf"
    response = _FakeResponse(
        url=url,
        body=b"%PDF-1.7\n" + (b"x" * 100),
        content_type="application/pdf",
    )
    session = _FakeSession({url: response})

    observation = inspect_source_metadata_candidate(
        url,
        session=session,
        max_body_bytes=16,
    )

    assert observation.transport_status == "verified_https"
    assert observation.application_level_status == "content_available"
    assert observation.bytes_inspected == 16
    assert response.closed is True
    assert session.calls[0][1]["stream"] is True
    assert session.calls[0][1]["allow_redirects"] is True


def test_inspection_distinguishes_html_not_found_page_from_http_success() -> None:
    url = "https://example.edu/moved"
    response = _FakeResponse(
        url=url,
        body=(
            "<html><head><title>找不到頁面</title></head>"
            "<body>要求的頁面不存在、已刪除或移動。</body></html>"
        ).encode(),
    )

    observation = inspect_source_metadata_candidate(
        url,
        session=_FakeSession({url: response}),
    )

    assert observation.transport_status == "verified_https"
    assert observation.application_level_status == "not_found_page"
    assert observation.detected_title == "找不到頁面"


def test_inspection_finds_late_not_found_marker_within_default_bound() -> None:
    url = "https://example.edu/moved-late"
    body = (
        b"<html><head><title>Official site</title></head><body>"
        + (b"x" * (700 * 1024))
        + "找不到要求的頁面".encode()
        + b"</body></html>"
    )

    observation = inspect_source_metadata_candidate(
        url,
        session=_FakeSession({url: _FakeResponse(url=url, body=body)}),
    )

    assert observation.application_level_status == "not_found_page"
    assert observation.bytes_inspected == len(body)


def test_inspection_rejects_fake_pdf_and_fails_closed_on_network_error() -> None:
    fake_pdf_url = "https://example.edu/exchange.pdf"
    error_url = "https://example.edu/unavailable"
    session = _FakeSession(
        {
            fake_pdf_url: _FakeResponse(
                url=fake_pdf_url,
                body=b"<html>login page</html>",
                content_type="text/html",
            ),
            error_url: requests.ConnectionError("connection unavailable"),
        }
    )

    fake_pdf = inspect_source_metadata_candidate(fake_pdf_url, session=session)
    network_error = inspect_source_metadata_candidate(error_url, session=session)

    assert fake_pdf.application_level_status == "unexpected_content"
    assert network_error.transport_status == "unverified"
    assert network_error.application_level_status == "unverified"
    assert "ConnectionError" in (network_error.error or "")


def test_manifest_audit_deduplicates_urls_and_accepts_normalized_html_title() -> None:
    source_url = "https://example.edu/sister-schools"
    lead_url = "https://example.edu/context"
    session = _FakeSession(
        {
            source_url: _FakeResponse(
                url=source_url,
                body=(
                    "<html><head><title>International Office - 姊妹校</title></head>"
                    "<body>姊妹校合作名單</body></html>"
                ).encode(),
            ),
            lead_url: _FakeResponse(
                url=lead_url,
                body=b"<html><title>Context</title><body>Official context</body></html>",
            ),
        }
    )
    manifest = {
        "items": [
            {
                "source_url": source_url,
                "application_level_status": "content_available",
                "transport_final_url": source_url,
                "transport_http_status": 200,
                "proposed_title": "International Office 姊妹校",
                "can_prefill": False,
                "research_leads": [
                    {
                        "url": lead_url,
                        "transport_final_url": lead_url,
                        "transport_http_status": 200,
                        "eligible_as_replacement": False,
                    }
                ],
            },
            {
                "source_url": source_url,
                "application_level_status": "content_available",
                "transport_final_url": source_url,
                "transport_http_status": 200,
                "proposed_title": "International Office 姊妹校",
                "can_prefill": False,
                "research_leads": [],
            },
        ]
    }

    observations, mismatches = audit_source_metadata_manifest(
        manifest,
        session=session,
    )

    assert len(observations) == 2
    assert len(session.calls) == 2
    assert mismatches == []


def test_manifest_audit_reports_status_title_and_safety_mismatches() -> None:
    source_url = "https://example.edu/source"
    lead_url = "https://example.edu/lead"
    session = _FakeSession(
        {
            source_url: _FakeResponse(
                url=source_url,
                body=b"<html><title>Changed title</title><body>Current content</body></html>",
            ),
            lead_url: _FakeResponse(
                url="http://example.edu/lead",
                body=b"",
                redirect_count=1,
            ),
        }
    )
    manifest = {
        "items": [
            {
                "source_url": source_url,
                "application_level_status": "not_found_page",
                "transport_final_url": source_url,
                "transport_http_status": 200,
                "proposed_title": "Original title",
                "can_prefill": True,
                "research_leads": [
                    {
                        "url": lead_url,
                        "transport_final_url": lead_url,
                        "transport_http_status": 200,
                        "eligible_as_replacement": True,
                    }
                ],
            }
        ]
    }

    _, mismatches = audit_source_metadata_manifest(manifest, session=session)

    assert any("manifest=" in item and "live=" in item for item in mismatches)
    assert any("proposed_title=" in item and "live_title=" in item for item in mismatches)
    assert any("can_prefill must remain false" in item for item in mismatches)
    assert any("eligible_as_replacement must remain false" in item for item in mismatches)
    assert any("research_lead" in item and "downgrades_to_http" in item for item in mismatches)

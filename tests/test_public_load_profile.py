"""The load tool must detect bad responses and never write to a tested site."""
import asyncio
import importlib.util
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("load_test_public", ROOT / "scripts/load_test_public.py")
load = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(load)


def settings(tmp_path):
    return load.arguments([
        "--base-url", "https://staging.example.test", "--users", "2", "--duration", "0.1",
        "--ramp-seconds", "0", "--think-seconds", "0.02", "--output", str(tmp_path / "report.json"),
    ])


@pytest.mark.parametrize("failure", [None, "status", "type", "timeout"])
def test_profile_reports_errors_and_never_sends_writes(tmp_path, failure):
    seen = []

    def respond(request):
        seen.append(request)
        if request.url.path == "/documents":
            if failure == "status":
                return httpx.Response(503, json={"detail": "busy"})
            if failure == "type":
                return httpx.Response(200, text="an HTML error page")
            if failure == "timeout":
                raise httpx.ReadTimeout("timed out", request=request)
        if request.url.path == "/":
            return httpx.Response(200, text="<!doctype html>", headers={"content-type": "text/html"})
        return httpx.Response(200, json={})

    report = asyncio.run(load.run(settings(tmp_path), transport=httpx.MockTransport(respond)))
    assert report["started_users"] == 2
    assert report["passed"] is (failure is None)
    assert report["errors"] > 0 if failure else report["errors"] == 0
    assert {request.method for request in seen} == {"GET"}
    assert all("authorization" not in request.headers for request in seen)
    assert report["routes"]["/student-dashboard"]["requests"] > 0


@pytest.mark.parametrize("extra", [
    ["--base-url", "https://secret:password@staging.example.test"],
    ["--base-url", "https://staging.example.test?token=secret"],
    ["--think-seconds", "0"], ["--duration", "nan"], ["--users", "0"],
    ["--ramp-seconds", "60"], ["--max-error-rate", "inf"],
])
def test_invalid_or_credential_bearing_configuration_is_rejected(tmp_path, extra):
    with pytest.raises(SystemExit):
        load.arguments(["--base-url", "https://staging.example.test", "--output", str(tmp_path / "x"), *extra])

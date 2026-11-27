from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.cgu_catalogue import CguCatalogue
from exchange_info.tools_and_data_core import MANDATORY_DISCLAIMER


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("EXCHANGE_SEO_INDEXABLE", "true")
        patch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://app.uniway-tw.com")
        original_view = CguCatalogue.view
        patch.setattr(CguCatalogue, "view", lambda self, **_: original_view(self, refresh=False))
        app = create_app(tmp_path_factory.mktemp("wave4-public-api"))
        with TestClient(app, base_url="http://internal.invalid") as browser:
            yield browser


def test_public_openapi_31_spec_and_cors(client):
    preflight = client.options("/api/public/openapi.json")
    assert preflight.status_code == 204
    assert preflight.headers.get("Access-Control-Allow-Origin") == "*"

    resp = client.get("/api/public/openapi.json")
    assert resp.status_code == 200
    assert client.head("/api/public/openapi.json").status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
    assert "noindex" in resp.headers.get("X-Robots-Tag", "")

    spec = resp.json()
    assert spec["openapi"] == "3.1.0"
    assert spec["servers"][0]["url"] == "https://app.uniway-tw.com"
    assert MANDATORY_DISCLAIMER in spec["info"]["description"]
    expected_paths = {
        "/api/public/stats/overview",
        "/api/public/schools",
        "/api/public/partners/filter",
        "/api/public/partners/reverse-lookup",
        "/api/public/deadlines",
    }
    assert set(spec["paths"].keys()) == expected_paths


def test_all_five_public_readonly_endpoints_return_real_data(client):
    ov = client.get("/api/public/stats/overview").json()
    assert ov["university_count"] == 71
    assert ov["unique_foreign_institutions"] > 500
    assert ov["disclaimer"] == MANDATORY_DISCLAIMER

    schools = client.get("/api/public/schools?q=政大&sector=public").json()
    assert schools["count"] >= 1
    assert any(item["school_id"] == "nccu" for item in schools["items"])
    assert schools["disclaimer"] == MANDATORY_DISCLAIMER

    partners = client.get("/api/public/partners/filter?home=nccu&test=ielts&score=6.5&region=europe&limit=10").json()
    assert partners["home_id"] == "nccu"
    assert partners["direct_match_count"] > 0
    assert 1 <= len(partners["items"]) <= 10
    assert partners["items"][0]["partner_url"].startswith("https://app.uniway-tw.com/schools/nccu/partners/")

    rev = client.get("/api/public/partners/reverse-lookup?q=早稻田&country=japan&limit=5").json()
    assert rev["matched_total"] >= 1
    assert rev["items"][0]["contracted_count"] >= 5
    assert len(rev["items"][0]["contracting_taiwan_schools"]) >= 5

    dls = client.get("/api/public/deadlines?month=11&limit=20").json()
    assert 1 <= dls["count"] <= 20
    assert dls["disclaimer"] == MANDATORY_DISCLAIMER


def test_public_api_never_reads_private_sessions_or_mutates_internal_openapi(client, monkeypatch):
    def forbid_session(*_a, **_kw):
        pytest.fail("Public AI API must never access private user sessions")

    monkeypatch.setattr(client.app.state.account_repository, "find_session_by_token_hash", forbid_session)
    for ep in (
        "/api/public/openapi.json",
        "/api/public/stats/overview",
        "/api/public/schools?limit=5",
        "/api/public/partners/filter?home=ntu&limit=5",
        "/api/public/partners/reverse-lookup?q=TUM&limit=3",
        "/api/public/deadlines?limit=5",
    ):
        anon = client.get(ep).content
        with_cookie = client.get(ep, headers={"Cookie": "exchange_session=fake-token"}).content
        assert anon == with_cookie


def test_llms_txt_documents_public_openapi_and_mcp_without_breaking_sitemap_check(client):
    llms = client.get("/llms.txt")
    assert llms.status_code == 200
    assert "/api/public/openapi.json" in llms.text
    assert "integrations/uniway-mcp" in llms.text


def test_claude_mcp_server_jsonrpc_stdio_protocol(client, monkeypatch):
    mcp_path = Path("integrations/uniway-mcp/uniway_mcp_server.py")
    assert mcp_path.is_file()

    # 1. Subprocess stdio handshake & tools/list test
    stdin_lines = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
    ]) + "\n"
    proc = subprocess.run(
        [sys.executable, str(mcp_path)],
        input=stdin_lines,
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    out_msgs = [json.loads(line) for line in proc.stdout.strip().splitlines()]
    assert len(out_msgs) == 2
    assert out_msgs[0]["id"] == 1 and out_msgs[0]["result"]["serverInfo"]["name"] == "uniway-taiwan-exchange"
    tool_names = {t["name"] for t in out_msgs[1]["result"]["tools"]}
    assert tool_names == {
        "get_exchange_overview",
        "search_schools",
        "filter_partners",
        "reverse_lookup_partner",
        "get_school_deadlines",
    }

    # 2. Direct tool execution routed to FastAPI TestClient
    spec = importlib.util.spec_from_file_location("uniway_mcp_server", mcp_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def fake_call_api(path: str, params: dict | None = None):
        r = client.get(path, params=params or {})
        r.raise_for_status()
        return r.json()

    monkeypatch.setattr(mod, "call_uniway_api", fake_call_api)
    call_resp = mod.handle_rpc_message({
        "jsonrpc": "2.0",
        "id": 99,
        "method": "tools/call",
        "params": {"name": "reverse_lookup_partner", "arguments": {"q": "早稻田", "country": "japan"}},
    })
    assert call_resp["result"]["isError"] is False
    parsed_payload = json.loads(call_resp["result"]["content"][0]["text"])
    assert parsed_payload["matched_total"] >= 1
    assert parsed_payload["disclaimer"] == MANDATORY_DISCLAIMER

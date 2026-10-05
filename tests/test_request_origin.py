"""Behind a hosting proxy the app must still know the public address and the real visitor, without believing forged headers."""
from __future__ import annotations

import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.request_origin import client_address, public_base_url


class Headers(dict):
    """A case-insensitive header lookup, like Starlette's."""

    def get(self, key, default=None):  # noqa: A003
        return super().get(key.lower(), default)


def fake_request(headers: dict[str, str] | None = None, host: str | None = "10.0.0.7", base_url: str = "http://internal:10000/"):
    return SimpleNamespace(
        headers=Headers({key.lower(): value for key, value in (headers or {}).items()}),
        client=SimpleNamespace(host=host) if host else None,
        base_url=base_url,
    )


# ----------------------------------------------------------------------------- public address

def test_the_configured_public_address_wins_over_everything_else():
    request = fake_request()
    both = {"EXCHANGE_PUBLIC_BASE_URL": "https://uniway.example.com/", "RENDER_EXTERNAL_URL": "https://uniway.onrender.com"}
    assert public_base_url(request, both) == "https://uniway.example.com"
    assert public_base_url(request, {"EXCHANGE_PUBLIC_BASE_URL": "http://127.0.0.1:8000"}) == "http://127.0.0.1:8000", "local testing"


def test_render_provided_address_is_used_until_a_domain_is_configured():
    request = fake_request()
    assert public_base_url(request, {"RENDER_EXTERNAL_URL": "https://uniway.onrender.com/"}) == "https://uniway.onrender.com"
    assert public_base_url(request, {"EXCHANGE_PUBLIC_BASE_URL": "  ", "RENDER_EXTERNAL_URL": "https://uniway.onrender.com"}) == "https://uniway.onrender.com"
    assert public_base_url(request, {"RENDER_EXTERNAL_URL": "http://plain.example"}) == "http://internal:10000", "only an https host address is trusted"


def test_with_nothing_configured_the_address_the_request_arrived_on_is_used():
    request = fake_request()
    assert public_base_url(request, {}) == "http://internal:10000"
    assert public_base_url(request, {"EXCHANGE_PUBLIC_BASE_URL": "   "}) == "http://internal:10000"


# ----------------------------------------------------------------------------- visitor address

def test_without_a_configured_header_a_forged_one_is_ignored():
    request = fake_request({"CF-Connecting-IP": "203.0.113.9", "X-Forwarded-For": "198.51.100.1"}, host="10.0.0.7")
    assert client_address(request, {}) == "10.0.0.7"


def test_the_configured_header_is_used_and_is_case_insensitive():
    request = fake_request({"cf-connecting-ip": "203.0.113.9"}, host="10.0.0.7")
    assert client_address(request, {"EXCHANGE_CLIENT_IP_HEADER": "CF-Connecting-IP"}) == "203.0.113.9"


def test_ipv6_is_normalised_so_one_visitor_is_one_key():
    request = fake_request({"CF-Connecting-IP": "2001:0DB8:0000:0000:0000:0000:0000:0001"})
    assert client_address(request, {"EXCHANGE_CLIENT_IP_HEADER": "CF-Connecting-IP"}) == "2001:db8::1"


@pytest.mark.parametrize("value", ["", "not-an-ip", "203.0.113.9, 198.51.100.1", "203.0.113.9:443", "<script>"])
def test_a_missing_or_malformed_value_falls_back_to_the_socket_address(value):
    request = fake_request({"CF-Connecting-IP": value}, host="10.0.0.7")
    assert client_address(request, {"EXCHANGE_CLIENT_IP_HEADER": "CF-Connecting-IP"}) == "10.0.0.7"


def test_with_no_socket_and_no_header_the_default_is_used():
    request = fake_request({}, host=None)
    assert client_address(request, {}) == "unknown"
    assert client_address(request, {}, default="127.0.0.1") == "127.0.0.1"


# ----------------------------------------------------------------------------- wired into the app

def test_school_photo_links_use_the_public_https_address_not_the_proxy_one(monkeypatch):
    monkeypatch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://uniway.example.com")
    client = TestClient(create_app(), base_url="http://internal-host:10000")
    text = client.get("/student-dashboard", params={"school": "國立臺北大學"}).text
    assert re.search(r'"https://uniway\.example\.com/static/assets/schools/', text), "photo links are on the public address"
    assert "internal-host" not in text, "no link points at the address the proxy used internally"


def test_without_a_public_address_photo_links_follow_the_request(monkeypatch):
    monkeypatch.delenv("EXCHANGE_PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    client = TestClient(create_app(), base_url="http://127.0.0.1:8000")
    text = client.get("/student-dashboard", params={"school": "長庚大學"}).text
    assert '"http://127.0.0.1:8000/static/assets/schools/' in text


def test_the_sign_in_return_address_is_the_public_one(monkeypatch):
    monkeypatch.setenv("EXCHANGE_PUBLIC_BASE_URL", "https://uniway.example.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "id-for-test")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "secret-for-test")
    client = TestClient(create_app(), base_url="http://internal-host:10000", follow_redirects=False)
    response = client.get("/auth/oauth/google/start")
    location = response.headers.get("location", "")
    assert response.status_code in (302, 303, 307), response.text[:200]
    assert "redirect_uri=https%3A%2F%2Funiway.example.com%2Fauth%2Foauth%2Fgoogle%2Fcallback" in location


def test_on_render_the_sign_in_return_address_comes_from_render_itself(monkeypatch):
    monkeypatch.delenv("EXCHANGE_PUBLIC_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://uniway.onrender.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "id-for-test")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "secret-for-test")
    client = TestClient(create_app(), base_url="http://internal-host:10000", follow_redirects=False)
    location = client.get("/auth/oauth/google/start").headers.get("location", "")
    assert "redirect_uri=https%3A%2F%2Funiway.onrender.com%2Fauth%2Foauth%2Fgoogle%2Fcallback" in location

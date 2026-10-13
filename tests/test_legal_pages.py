"""The privacy policy and terms Google requires before a sign-in app can be published to everyone."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.legal_pages import contact_markup

STATIC = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("EXCHANGE_CONTACT_EMAIL", "hello@example.com")
    return TestClient(create_app())


def test_both_pages_are_public_html_with_the_contact_address_filled_in(client):
    for path, title in (("/privacy", "隱私權政策"), ("/terms", "使用條款")):
        response = client.get(path)
        assert response.status_code == 200 and response.headers["content-type"].startswith("text/html"), path
        assert title in response.text
        assert 'href="mailto:hello@example.com"' in response.text
        assert "{{" not in response.text, "no placeholder is left behind"


def test_the_pages_are_not_part_of_the_api_contract(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/privacy" not in paths and "/terms" not in paths


def test_the_privacy_policy_says_what_google_and_the_law_expect(client):
    text = client.get("/privacy").text
    for needle in ("openid", "email", "profile", "Limited Use", "api-services-user-data-policy", "Supabase", "雪梨", "Render",
                   "localStorage", "不要追蹤", "30 天", "刪除帳號", "個人資料保護法", "不會販售"):
        assert needle in text, needle
    assert "不會記" in text and "IP 位址" in text, "what the anonymous statistics leave out is stated"
    assert "不保存原始 IP" in text, "the sign-in limiter stores only a hash"


def test_the_terms_say_the_data_is_not_official_and_the_service_is_not_an_agency(client):
    text = client.get("/terms").text
    for needle in ("逐筆人工核對", "最新公告為準", "不提供留學代辦服務", "沒有隸屬關係", "目前所有功能都免費", "中華民國"):
        assert needle in text, needle


def test_each_page_links_to_the_other_and_back_to_the_home_page(client):
    privacy, terms = client.get("/privacy").text, client.get("/terms").text
    assert 'href="/terms"' in privacy and 'href="/privacy"' in terms
    assert 'href="/"' in privacy and 'href="/"' in terms


def test_the_home_page_links_to_both_pages(client):
    home = client.get("/").text
    assert 'href="/privacy"' in home and 'href="/terms"' in home, "Google requires the home page to link to the privacy policy"


def test_without_a_configured_address_the_pages_say_so_instead_of_inventing_one(monkeypatch):
    monkeypatch.delenv("EXCHANGE_CONTACT_EMAIL", raising=False)
    text = TestClient(create_app()).get("/privacy").text
    assert "尚未設定聯絡信箱" in text and "mailto:" not in text


@pytest.mark.parametrize("value", ['"><script>alert(1)</script>', "not an address", "a@b", "x@y.z", "a b@example.com", "javascript:alert(1)"])
def test_an_odd_contact_setting_never_becomes_markup(value):
    markup = contact_markup({"EXCHANGE_CONTACT_EMAIL": value})
    assert "<script" not in markup and "mailto:" not in markup and "javascript:" not in markup


def test_the_stylesheet_exists_and_the_pages_load_nothing_from_other_sites():
    for name in ("privacy.html", "terms.html"):
        html = (STATIC / name).read_text(encoding="utf-8")
        assert 'href="/static/legal.css' in html
        assert "<script" not in html, "the site's content security policy allows scripts from itself only"
        assert not re.search(r'(?:src|href)="https?://(?!developers\.google\.com/terms/)', html), name
    assert (STATIC / "legal.css").is_file()


def test_a_self_hosted_deployment_names_its_own_hosting_instead_of_supabase_and_render(monkeypatch):
    monkeypatch.setenv("EXCHANGE_CONTACT_EMAIL", "hello@example.com")
    monkeypatch.setenv("EXCHANGE_HOSTING_PROFILE", "selfhost")
    text = TestClient(create_app()).get("/privacy").text
    assert "{{" not in text
    assert "營運者自行管理的伺服器，位於台灣" in text and "Google Drive" in text and "台灣境內" in text
    assert "約 30 天後自動刪除" in text
    for gone in ("Supabase", "Render", "Cloudflare", "雪梨", "新加坡", "存放在台灣境外"):
        assert gone not in text, gone
    assert "登入：Google" in text


def test_an_unknown_hosting_profile_falls_back_to_the_hosted_wording(monkeypatch):
    monkeypatch.setenv("EXCHANGE_CONTACT_EMAIL", "hello@example.com")
    monkeypatch.setenv("EXCHANGE_HOSTING_PROFILE", "something-else")
    text = TestClient(create_app()).get("/privacy").text
    assert "Supabase" in text and "Render" in text and "台灣境外" in text and "{{" not in text

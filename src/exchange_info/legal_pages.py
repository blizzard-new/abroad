"""The public privacy policy and terms of use.

Google will not publish a sign-in app to everyone without a home page, a privacy policy and terms on the same domain, and the
home page has to link to them. The pages are plain HTML files in ``static/``; the only thing filled in at request time is
the operator's contact address (``EXCHANGE_CONTACT_EMAIL``), so the address is not written into the repository.

These are plain-language statements of what the service does, written from the code and the deployment settings. They are not
legal advice and no lawyer has reviewed them.
"""
from __future__ import annotations

import html
import os
import re
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

CONTACT_ENV = "EXCHANGE_CONTACT_EMAIL"
HOSTING_ENV = "EXCHANGE_HOSTING_PROFILE"
# The date printed at the top of both pages. Signing in requires the visitor to have ticked this exact version, so
# changing the pages means changing this too (a test keeps the two in step).
TERMS_VERSION = "2026-10-19"
PLACEHOLDER = "{{CONTACT}}"
# Where the data lives and who touches it, as section 4 of the privacy policy says it. "render" is the hosted deployment
# (Render + Supabase); "selfhost" is the operator's own server (deploy/selfhost). The two lists are the only difference.
HOSTING_PROFILES = {
    "render": (
        (
            "<li>資料庫與加密文件：Supabase，伺服器位於澳洲雪梨。</li>",
            "<li>網站主機：Render，伺服器位於新加坡，前面有 Cloudflare 的網路。</li>",
        ),
        "你的資料會存放在台灣境外。",
        "提供網站的主機與網路服務（Render，以及它前面的 Cloudflare）為了傳輸與防護，會在它們那端處理連線位址與請求紀錄，依各自的政策保存。",
    ),
    "selfhost": (
        (
            "<li>資料庫與加密文件：存放在營運者自行管理的伺服器，位於台灣。</li>",
            "<li>網站主機：同一台伺服器，位於台灣。</li>",
            "<li>備份：每天一份，先在營運者的伺服器上加密，再存放在 Google Drive；Google 看不到內容，也沒有解密用的密碼。</li>",
        ),
        "你的資料存放在台灣境內；因備份而產生的加密複本存放在 Google 的伺服器，地點不固定。",
        "提供網站的伺服器為了除錯與防護，會保存連線紀錄（連線位址、時間與請求的網址，不含你輸入的內容），約 30 天後自動刪除。",
    ),
}
DEFAULT_HOSTING_PROFILE = "render"
_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_MISSING = "（營運者尚未設定聯絡信箱）"
PAGES = {"/privacy": "privacy.html", "/terms": "terms.html"}


def contact_markup(environment: Mapping[str, str] | None = None) -> str:
    """A mailto link for the configured address, or a visible notice when none (or an odd one) is configured."""
    env = os.environ if environment is None else environment
    address = env.get(CONTACT_ENV, "").strip()
    if not _EMAIL.fullmatch(address):
        return html.escape(_MISSING)
    safe = html.escape(address, quote=True)
    return f'<a href="mailto:{safe}">{safe}</a>'


def hosting_profile(environment: Mapping[str, str] | None = None) -> tuple[str, str, str]:
    """(list items, where the data is, who sees connection logs) for the configured deployment; unknown names mean the hosted one."""
    env = os.environ if environment is None else environment
    name = env.get(HOSTING_ENV, DEFAULT_HOSTING_PROFILE).strip().casefold()
    items, location, network = HOSTING_PROFILES.get(name, HOSTING_PROFILES[DEFAULT_HOSTING_PROFILE])
    return (chr(10) + " " * 8).join(items), location, network


def render_page(static_dir: Path, name: str, environment: Mapping[str, str] | None = None) -> str:
    text = (static_dir / name).read_text(encoding="utf-8")
    items, location, network = hosting_profile(environment)
    text = text.replace("{{HOSTING_LIST}}", items).replace("{{HOSTING_LOCATION}}", location).replace("{{HOSTING_NETWORK}}", network)
    return text.replace(PLACEHOLDER, contact_markup(environment))


def register_legal_pages(app: FastAPI, static_dir: Path) -> None:
    for route, name in PAGES.items():
        def make(file_name: str):
            def page() -> HTMLResponse:
                return HTMLResponse(render_page(static_dir, file_name), headers={"Cache-Control": "no-cache"})
            return page

        app.add_api_route(route, make(name), methods=["GET"], response_class=HTMLResponse, include_in_schema=False)

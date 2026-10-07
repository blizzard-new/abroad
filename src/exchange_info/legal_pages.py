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
# The date printed at the top of both pages. Signing in requires the visitor to have ticked this exact version, so
# changing the pages means changing this too (a test keeps the two in step).
TERMS_VERSION = "2026-10-08"
PLACEHOLDER = "{{CONTACT}}"
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


def render_page(static_dir: Path, name: str, environment: Mapping[str, str] | None = None) -> str:
    text = (static_dir / name).read_text(encoding="utf-8")
    return text.replace(PLACEHOLDER, contact_markup(environment))


def register_legal_pages(app: FastAPI, static_dir: Path) -> None:
    for route, name in PAGES.items():
        def make(file_name: str):
            def page() -> HTMLResponse:
                return HTMLResponse(render_page(static_dir, file_name), headers={"Cache-Control": "no-cache"})
            return page

        app.add_api_route(route, make(name), methods=["GET"], response_class=HTMLResponse, include_in_schema=False)

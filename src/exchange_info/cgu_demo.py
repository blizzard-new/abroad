"""Read-only hackathon app. Deliberately does not import api or its repositories."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse

from .cgu_catalogue import BUNDLED_SNAPSHOT, validate_snapshot

STATIC = Path(__file__).parent / "static"
CONTENT = Path(__file__).parent / "demo_data/content.json"
CURATED_SCHOOLS = (
    "林肯大學 Lincoln University",
    "德國拉芬斯堡-魏恩加騰應用科技大學 Ravensburg-Weingarten University of Applied Sciences",
    "德國巴登-符騰堡州立合作大學 Duale Hochschule Baden-Württemberg Karlsruhe, Germany Baden-Wuerttemberg Cooperative State University",
)
ASSETS = {
    "brand-tokens.css": ("brand-tokens.css", "text/css"),
    "cgu-demo.css": ("cgu-demo.css", "text/css"),
    "cgu-demo.js": ("cgu-demo.js", "text/javascript"),
    "uniway-mark.webp": ("assets/brand/uniway-mark.webp", "image/webp"),
    "favicon.svg": ("favicon.svg", "image/svg+xml"),
}


def demo_catalogue(snapshot_path: Path = BUNDLED_SNAPSHOT) -> dict:
    """Reuse validation, never the refresh thread or writable catalogue cache."""
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        rows = {row.school_name: row for row in validate_snapshot(snapshot)}
        schools = []
        for index, name in enumerate(CURATED_SCHOOLS):
            row = rows.get(name)
            if row is None or "交換" not in row.program_type:
                continue
            schools.append({
                "id": f"school-{index}", "name": row.school_name,
                "country": row.country, "website": row.website,
                "colleges": row.colleges, "degree_levels": row.degree_levels,
                "study_period": row.study_period, "eligibility": row.eligibility,
                "reference_quota": row.quota, "reference_deadline": row.application_deadline,
                "source_url": row.source_url,
                "status": "歷史快照參考・當期適用待確認",
            })
        return {"schools": schools, "snapshot_at": snapshot["fetched_at"], "status": "reference"}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        logging.getLogger(__name__).warning("CGU demo catalogue unavailable; showing official sources only")
        return {"schools": [], "snapshot_at": None, "status": "unavailable"}


def create_demo_app() -> FastAPI:
    """Separate entry point, no account/session/database/email/upload endpoints."""
    app = FastAPI(title="UniWay CGU 展示版", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def demo_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update({
            "X-Robots-Tag": "noindex, nofollow, noarchive",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "DENY",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; "
                "img-src 'self'; connect-src 'self'; font-src 'self'; base-uri 'none'; "
                "form-action 'none'; frame-ancestors 'none'; object-src 'none'",
        })
        return response

    @app.get("/", include_in_schema=False)
    @app.get("/cgu", include_in_schema=False)
    def home():
        return FileResponse(STATIC / "cgu-demo.html", media_type="text/html")

    @app.get("/static/{name}", include_in_schema=False)
    def asset(name: str):
        if name not in ASSETS:
            raise HTTPException(status_code=404)
        relative, media_type = ASSETS[name]
        return FileResponse(STATIC / relative, media_type=media_type)

    @app.get("/demo/content")
    def content():
        try:
            return {**json.loads(CONTENT.read_text(encoding="utf-8")), **demo_catalogue()}
        except (OSError, ValueError):
            raise HTTPException(status_code=503, detail="展示內容暫時無法載入，請重試。") from None

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "cgu-demo", "persistence": "browser-only"}

    @app.get("/robots.txt", response_class=PlainTextResponse)
    def robots():
        return "User-agent: *\nDisallow: /\n"

    return app

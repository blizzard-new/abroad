"""The office as a web page: the floor plan with every agent at their desk, live over server-sent events, and the
boss's inbox for approving drafts."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import mimetypes
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import mobile, scheduler
from .config import Settings
from .mobile import FailureLimit
from .office import Office
from .pipeline import run_day

STATIC = Path(__file__).resolve().parent / "static"
BRAND_FILES = {"uniway-logo.webp", "suitcase.webp"}

# Windows takes these from the registry, where .js is often text/plain; browsers then refuse to load the 3D office's modules.
for _type, _ext in (("text/javascript", ".js"), ("text/javascript", ".mjs"), ("text/css", ".css")):
    mimetypes.add_type(_type, _ext)


def create_app(settings: Settings, *, clock: bool = True, office: Office | None = None) -> FastAPI:
    office = office or Office(settings)
    access_token = settings.access_token

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stops = [scheduler.start(office)] if clock else []
        if settings.telegram_bot_token:
            from .telegram import TelegramBridge

            stops.append(TelegramBridge(office).start())
        yield
        for stop in stops:
            stop.set()

    app = FastAPI(title="UniWay 行銷辦公室", lifespan=lifespan)
    app.state.office = office
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    if settings.fonts_dir.is_dir():
        app.mount("/fonts", StaticFiles(directory=settings.fonts_dir), name="fonts")

    @app.middleware("http")
    async def fresh_static(request: Request, call_next):
        # After a git pull the page must not mix the new office.html with yesterday's cached scripts.
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "frame-ancestors 'none'; object-src 'none'; base-uri 'self'",
        )
        return response

    limit = FailureLimit()
    app.state.failure_limit = limit

    def _client_key(request: Request) -> str:
        peer = request.client.host if request.client else ""
        if peer in {"127.0.0.1", "::1"}:
            cf_ip = (request.headers.get("cf-connecting-ip") or "").strip()
            if cf_ip:
                try:
                    return f"cf:{ipaddress.ip_address(cf_ip)}"
                except ValueError:
                    pass
        return peer

    def _is_https(request: Request) -> bool:
        if request.url.scheme == "https":
            return True
        peer = request.client.host if request.client else ""
        if peer in {"127.0.0.1", "::1"}:
            forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",", 1)[0].strip().lower()
            if forwarded_proto == "https":
                return True
        return False

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        if (
            request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and not request.headers.get("authorization", "").lower().startswith("bearer ")
        ):
            sec_fetch_site = (request.headers.get("sec-fetch-site") or "").strip().lower()
            origin = (request.headers.get("origin") or "").strip().rstrip("/")
            if sec_fetch_site == "cross-site":
                return JSONResponse({"detail": "跨站請求已被拒絕"}, status_code=403)
            if origin:
                forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",", 1)[0].strip().lower()
                host = (request.headers.get("host") or request.base_url.netloc).strip()
                allowed_origins = {
                    f"{request.base_url.scheme}://{request.base_url.netloc}".rstrip("/"),
                    f"http://{host}".rstrip("/"),
                    f"https://{host}".rstrip("/"),
                }
                if forwarded_proto in {"http", "https"} and host:
                    allowed_origins.add(f"{forwarded_proto}://{host}".rstrip("/"))
                if origin == "null" or origin not in allowed_origins:
                    return JSONResponse({"detail": "跨站請求來源驗證失敗"}, status_code=403)

        # Media stays public (Instagram and Threads fetch it); everything else needs the token when one is set.
        # The token comes in the address (?token=…), a cookie, or the phone app's "Authorization: Bearer …" header.
        if not access_token or request.url.path.startswith("/media/"):
            return await call_next(request)
        who = _client_key(request)
        wait = limit.wait(who)
        if wait:
            return JSONResponse({"detail": f"錯誤太多次，請 {wait // 60 + 1} 分鐘後再試"}, status_code=429, headers={"Retry-After": str(wait)})
        bearer = request.headers.get("authorization", "")
        given = (bearer[7:].strip() if bearer[:7].lower() == "bearer " else "") or request.query_params.get("token") or request.cookies.get("office_token") or ""
        if not secrets.compare_digest(given.encode(), access_token.encode()):
            if given:
                limit.failed(who)
            return JSONResponse({"detail": "需要辦公室通行碼（網址加上 ?token=…）"}, status_code=401)
        limit.succeeded(who)
        cookie_secure = _is_https(request)
        if request.method == "GET" and request.url.path in {"/", "/m"} and "token" in request.query_params:
            redirect = RedirectResponse(url=request.url.path, status_code=303)
            redirect.set_cookie(
                "office_token",
                access_token,
                httponly=True,
                secure=cookie_secure,
                samesite="strict",
                max_age=30 * 86400,
            )
            return redirect
        response = await call_next(request)
        if request.cookies.get("office_token") != access_token:
            response.set_cookie(
                "office_token",
                access_token,
                httponly=True,
                secure=cookie_secure,
                samesite="strict",
                max_age=30 * 86400,
            )
        return response

    @app.get("/")
    def home():
        return FileResponse(STATIC / "office.html", headers={"Cache-Control": "no-cache"})

    @app.get("/m")
    def phone():
        """The phone's version: Leo's chat and the inbox, in the Android app's window or any phone browser."""
        return FileResponse(STATIC / "m.html", headers={"Cache-Control": "no-cache"})

    @app.get("/api/mobile/feed")
    def mobile_feed(chat_after: int | None = None):
        return mobile.feed(office, chat_after)

    @app.get("/media/{ref:path}")
    def media(ref: str):
        try:
            path = office.media_file(ref)
        except ValueError:
            raise HTTPException(404) from None
        if not path.is_file():
            raise HTTPException(404)
        return FileResponse(path)

    @app.get("/brand/{name}")
    def brand(name: str):
        if name not in BRAND_FILES or not (settings.brand_assets_dir / name).is_file():
            raise HTTPException(404)
        return FileResponse(settings.brand_assets_dir / name, headers={"Cache-Control": "max-age=86400"})

    @app.get("/api/state")
    def state():
        return office.snapshot()

    @app.get("/api/events")
    async def events(request: Request):
        queue = office.bus.subscribe()

        async def stream():
            try:
                yield "retry: 3000\n\n"
                while not await request.is_disconnected():
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=15)
                    except asyncio.TimeoutError:
                        yield ": ping\n\n"
                        continue
                    yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            finally:
                office.bus.unsubscribe(queue)

        return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.post("/api/run")
    def start_run(force: bool = Body(False, embed=True)):
        if office.busy.locked():
            raise HTTPException(409, "大家正在忙今天的工作")
        if office.store.run_for_day(office.today().isoformat()) and not force:
            raise HTTPException(409, "今天已經跑過了")
        threading.Thread(target=run_day, args=(office,), kwargs={"force": True}, daemon=True, name="office-day").start()
        return {"started": True}

    @app.post("/api/chat")
    def chat(text: str = Body(..., embed=True)):
        """Talk to the chief. The answer arrives on the event stream, since the chief may take a while to think."""
        text = text.strip()
        if not text:
            raise HTTPException(422, "要跟總管說什麼？")
        threading.Thread(target=office.staff["chief"].handle, args=(text[:2000],), daemon=True, name="chief-chat").start()
        return {"accepted": True}

    @app.post("/api/publish")
    def publish_due():
        threading.Thread(target=office.staff["publisher"].publish_due, daemon=True).start()
        return {"started": True}

    @app.post("/api/drafts/{draft_id}/approve")
    def approve(draft_id: int, now: bool = Body(False, embed=True)):
        draft = _guard(lambda: office.approve(draft_id, publish_now=now))
        if now:
            threading.Thread(target=office.staff["publisher"].publish_due, daemon=True).start()
        return draft

    @app.post("/api/drafts/{draft_id}/reject")
    def reject(draft_id: int, note: str = Body("", embed=True)):
        return _guard(lambda: office.reject(draft_id, note))

    @app.patch("/api/drafts/{draft_id}")
    def edit(draft_id: int, changes: dict = Body(...)):
        return _guard(lambda: office.edit(draft_id, changes))

    return app


def _guard(action):
    try:
        return action()
    except KeyError:
        raise HTTPException(404, "找不到這則草稿") from None
    except ValueError as error:
        raise HTTPException(409, str(error)) from None

"""The office as a web page: the floor plan with every agent at their desk, live over server-sent events, and the
boss's inbox for approving drafts."""

from __future__ import annotations

import asyncio
import json
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import scheduler
from .config import Settings
from .office import Office
from .pipeline import run_day

STATIC = Path(__file__).resolve().parent / "static"
BRAND_FILES = {"uniway-logo.webp", "suitcase.webp"}


def create_app(settings: Settings, *, clock: bool = True, office: Office | None = None) -> FastAPI:
    office = office or Office(settings)
    access_token = settings.access_token

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stop = scheduler.start(office) if clock else None
        yield
        if stop:
            stop.set()

    app = FastAPI(title="UniWay 行銷辦公室", lifespan=lifespan)
    app.state.office = office
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    if settings.fonts_dir.is_dir():
        app.mount("/fonts", StaticFiles(directory=settings.fonts_dir), name="fonts")

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        # Media stays public (Instagram and Threads fetch it); everything else needs the token when one is set.
        if not access_token or request.url.path.startswith("/media/"):
            return await call_next(request)
        given = request.query_params.get("token") or request.cookies.get("office_token") or ""
        if not secrets.compare_digest(given, access_token):
            return JSONResponse({"detail": "需要辦公室通行碼（網址加上 ?token=…）"}, status_code=401)
        response = await call_next(request)
        if request.query_params.get("token"):
            response.set_cookie("office_token", access_token, httponly=True, samesite="strict", max_age=30 * 86400)
        return response

    @app.get("/")
    def home():
        return FileResponse(STATIC / "office.html", headers={"Cache-Control": "no-cache"})

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

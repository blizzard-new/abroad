"""Staging-only wrapper. Never included in the production image entrypoint."""
import os
import re

from exchange_info.api import app

RUN_ID = os.environ.get("EXCHANGE_CAPACITY_RUN_ID", "")
if not re.fullmatch(r"[0-9a-f]{32}", RUN_ID):
    raise RuntimeError("A generated capacity run ID is required")


@app.get("/capacity/identity", include_in_schema=False)
async def capacity_identity():
    return {"run_id": RUN_ID, "purpose": "isolated-capacity-test", "pid": os.getpid(),
            "threads": int(os.environ.get("EXCHANGE_WORKER_THREADS", "2")),
            "catalogue_slots": int(os.environ.get("EXCHANGE_CATALOGUE_CONCURRENCY", "1")),
            "dashboard_ready": "cgu" in getattr(app.state, "public_dashboard_cache_ready", set())}


@app.middleware("http")
async def capacity_worker(request, call_next):
    response = await call_next(request)
    response.headers["X-Capacity-Worker"] = str(os.getpid())
    # Probe-only: ask the internal proxy to release this upstream connection,
    # so sequential logout checks can reach every worker. Normal traffic reuses it.
    if request.headers.get("X-Capacity-New-Connection") == "1":
        response.headers["Connection"] = "close"
    return response

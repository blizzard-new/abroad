from pathlib import Path
import os
root=Path('/workspace/abroad-globe-20261011')
def replace(p,s):
 t=p.with_name(p.name+'.memory-fix');t.write_text(s);os.replace(t,p)
p=root/'src/exchange_info/api.py';s=p.read_text().replace('from contextlib import asynccontextmanager','from contextlib import asynccontextmanager, suppress')
marker='    warm_up: list = []'
s=s.replace(marker,'    warm_up: list = []',1)
s=s.replace('        if warm_up and os.environ.get("EXCHANGE_WARM_CACHES", "").strip().lower() in {"1", "on", "true", "yes"}:\n            threading.Thread(target=warm_up[0], name="warm-caches", daemon=True).start()', '        warming_task = None\n        if warm_up and os.environ.get("EXCHANGE_WARM_CACHES", "").strip().lower() in {"1", "on", "true", "yes"}:\n            warming_task = asyncio.create_task(warm_up[0](), name="warm-caches")\n        _app.state.cache_warmup_task = warming_task')
s=s.replace('        finally:\n            catalogue_slots = None', '        finally:\n            if warming_task is not None:\n                warming_task.cancel()\n                with suppress(asyncio.CancelledError):\n                    await warming_task\n            catalogue_slots = None',1)
s=s.replace('    def warm_catalogue_caches() -> None:', '    async def warm_catalogue_caches() -> None:')
s=s.replace('        time.sleep(15)  # let the server start and pass its health check first', '        await asyncio.sleep(CACHE_WARM_UP_DELAY_SECONDS)  # let health become ready first')
s=s.replace('        for step in steps:\n            try:\n                step()', '        for step in steps:\n            try:\n                # Share the catalogue limit and worker arenas with real reads.\n                # Release between steps so waiting visitors can make progress.\n                async with catalogue_slots:\n                    await run_in_threadpool(step)')
assert s.count('CACHE_WARM_UP_DELAY_SECONDS')==1
anchor='from __future__ import annotations\n';s=s.replace(anchor,anchor+'\nCACHE_WARM_UP_DELAY_SECONDS = 15.0\n',1)
replace(p,s)
p=root/'tests/test_catalogue_speed.py';s=p.read_text().replace('from types import SimpleNamespace','import asyncio')
a=s.index('def _warm_threads():');b=s.index('\ndef test_the_warm_up_is_off',a)
s=s[:a]+'''def _wait_for_warm_up(client):
    async def wait():
        await asyncio.wait_for(asyncio.shield(client.app.state.cache_warmup_task), 30)
    client.portal.call(wait)

'''+s[b:]
s=s.replace('with TestClient(api.create_app(data_dir)):\n        assert not _warm_threads()', 'with TestClient(api.create_app(data_dir)) as client:\n        assert client.app.state.cache_warmup_task is None')
s=s.replace('monkeypatch.setattr(api, "time", SimpleNamespace(monotonic=time.monotonic, sleep=lambda seconds: None))','monkeypatch.setattr(api, "CACHE_WARM_UP_DELAY_SECONDS", 0)')
s=s.replace('        for thread in _warm_threads():\n            thread.join(timeout=30)', '        _wait_for_warm_up(client)')
s+='''

def test_warmup_delay_does_not_block_health_or_outlive_lifespan(counted, monkeypatch):
    data_dir, calls = counted
    monkeypatch.setenv("EXCHANGE_WARM_CACHES", "1")
    monkeypatch.setattr(api, "CACHE_WARM_UP_DELAY_SECONDS", 60)
    with TestClient(api.create_app(data_dir)) as client:
        task = client.app.state.cache_warmup_task
        assert task is not None and not task.done()
        assert client.get("/health").status_code == 200
        assert calls["dashboard"] == 0
    assert task.cancelled()
    assert calls["dashboard"] == 0
'''
replace(p,s)
print('Warm-up now uses the existing bounded worker pool, one catalogue slot per step, and lifespan cancellation.')

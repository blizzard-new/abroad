"""Local-only diagnostic endpoint; never included in the application package."""
import gc
import os
from pathlib import Path
import resource
import tracemalloc
from contextlib import asynccontextmanager

if os.environ.get('ABROAD_MEMORY_TRACE') == '1':
    tracemalloc.start(3)

from exchange_info.api import app

if os.environ.get('ABROAD_WORKER_TOKENS'):
    original_lifespan = app.router.lifespan_context
    @asynccontextmanager
    async def bounded_workers(application):
        import anyio.to_thread
        async with original_lifespan(application):
            limiter = anyio.to_thread.current_default_thread_limiter()
            limiter.total_tokens = int(os.environ['ABROAD_WORKER_TOKENS'])
            yield
    app.router.lifespan_context = bounded_workers

if os.environ.get('ABROAD_CATALOGUE_SLOTS'):
    import asyncio
    slots = asyncio.Semaphore(int(os.environ['ABROAD_CATALOGUE_SLOTS']))
    paths = {'/student-dashboard','/coverage','/destination-profiles','/destination-profile',
             '/application-center/templates','/application-center/catalog','/application-period-options',
             '/application-workflow','/application-workflows','/advisor/plan','/advisor/ask',
             '/school-life-context','/school-completeness','/student-experiences'}
    @app.middleware('http')
    async def bounded_catalogue(request, call_next):
        if request.url.path in paths:
            async with slots:
                return await call_next(request)
        return await call_next(request)

@app.get('/__local_memory_probe__', include_in_schema=False)
def memory_probe(collect: bool = False):
    collected = gc.collect() if collect else None
    rss = next(int(line.split()[1]) * 1024 for line in Path('/proc/self/status').read_text().splitlines()
               if line.startswith('VmRSS:'))
    result = {'pid': os.getpid(), 'rss_bytes': rss,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
              'gc_collected': collected}
    if tracemalloc.is_tracing():
        result['traced_bytes'], result['traced_peak_bytes'] = tracemalloc.get_traced_memory()
        result['largest_allocations'] = [{'trace': str(item.traceback), 'bytes': item.size, 'count': item.count}
                                         for item in tracemalloc.take_snapshot().statistics('lineno')[:40]]
        result['largest_traces'] = [{'trace': [str(frame) for frame in item.traceback],
                                     'bytes': item.size, 'count': item.count}
                                    for item in tracemalloc.take_snapshot().statistics('traceback')[:20]]
    return result

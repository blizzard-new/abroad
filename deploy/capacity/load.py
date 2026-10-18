"""Paced mixed workload. Refuses credentials/writes until staging identity matches."""
import argparse
import asyncio
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from datetime import datetime, timezone
import json
import math
import multiprocessing
import os
from pathlib import Path
import re
import time

import httpx


class CheckFailed(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise CheckFailed(reason)


def validate_fixture(fixture, run_id, users):
    require(bool(re.fullmatch(r'[0-9a-f]{32}', run_id)), 'invalid run ID')
    require(fixture.get('run_id') == run_id, 'fixture identity mismatch')
    require(datetime.fromisoformat(fixture['expires_at']) > datetime.now(timezone.utc), 'expired fixtures; reseed')
    require(len(fixture['actors']) >= users + 2, 'not enough distinct fixture accounts')
    actors = fixture['actors']
    require(len({a['account_id'] for a in actors}) == len(actors), 'duplicate accounts')
    require(len({a['token'] for a in actors}) == len(actors), 'duplicate sessions')
    require(all(re.fullmatch(f'capacity-{run_id}-[0-9]{{5}}', a['account_id']) for a in actors), 'foreign fixture account')


async def verify_target(client, run_id):
    # Never send a bearer token in this handshake, including on redirects.
    response = await client.get('/capacity/identity')
    require(response.status_code == 200, 'target is not an isolated capacity stack')
    data = response.json()
    require(data.get('run_id') == run_id and data.get('purpose') == 'isolated-capacity-test', 'target identity mismatch')


class Workload:
    def __init__(self, client, fixture):
        self.client = client
        self.fixture = fixture
        self.times = defaultdict(list)
        self.failures = Counter()
        self.statuses = Counter()
        self.workers = Counter()
        self.bytes = 0
        self.cycles = 0
        self.started = 0
        self.completed = 0
        self.failed_requests = 0
        self.conflict_checks = {}
        self.generators = []

    def snapshot(self):
        return {key: getattr(self, key) for key in (
            'times', 'failures', 'statuses', 'workers', 'bytes', 'cycles',
            'started', 'completed', 'failed_requests')}

    def merge(self, snapshot):
        # Merge samples, not percentile averages: p95 must cover all students.
        for route, values in snapshot['times'].items():
            self.times[route].extend(values)
        for key in ('failures', 'statuses', 'workers'):
            getattr(self, key).update(snapshot[key])
        for key in ('bytes', 'cycles', 'started', 'completed', 'failed_requests'):
            setattr(self, key, getattr(self, key) + snapshot[key])

    async def request(self, actor, method, path, *, expected=(200,), fresh=False, **kwargs):
        start = time.perf_counter()
        key = f'{method} {path}'
        try:
            response = await self.client.request(method, path,
                headers={'Authorization':f"Bearer {actor['token']}", **({'Connection':'close','X-Capacity-New-Connection':'1'} if fresh else {})}, **kwargs)
            self.statuses[f'{key} {response.status_code}'] += 1
            if response.headers.get('X-Capacity-Worker'):
                self.workers[response.headers['X-Capacity-Worker']] += 1
            self.bytes += int(response.headers.get('content-length', len(response.content)))
            require(response.status_code in expected, f'{key}: HTTP {response.status_code}')
            return response
        except (httpx.HTTPError, CheckFailed) as error:
            # Never record response bodies, URLs with query strings, credentials or payloads.
            self.failed_requests += 1
            self.failures[key + ': ' + (str(error) if isinstance(error, CheckFailed) else type(error).__name__)] += 1
            raise CheckFailed(key) from None
        finally:
            self.times[key].append(time.perf_counter() - start)

    def params(self):
        return {'home_school':self.fixture['school']}

    async def workspace(self, actor, marker):
        current = (await self.request(actor, 'GET', '/account/workspace', params=self.params())).json()['workspace']
        current['selection_conditions'] = {'profile':{'course_interests':marker}}
        saved = (await self.request(actor, 'PUT', '/account/workspace', json=current)).json()['workspace']
        require(saved['revision'] == current['revision'] + 1, 'workspace revision did not advance')
        restored = (await self.request(actor, 'GET', '/account/workspace', params=self.params())).json()['workspace']
        require(restored['revision'] == saved['revision'] and restored['selection_conditions']['profile']['course_interests'] == marker,
                'workspace persistence or account isolation failed')

    def draft_payload(self, revision, marker):
        return dict(home_school=self.fixture['school'], template_version=self.fixture['template_version'],
                    revision=revision, profile={}, answers={'overseas_institution':marker}, attachments={})

    async def drafts(self, actor):
        return (await self.request(actor, 'GET', '/account/application-drafts', params=self.params())).json()['items']

    async def draft(self, actor, marker):
        items = await self.drafts(actor)
        current = next((x for x in items if x['template_id'] == self.fixture['template_id']), None)
        revision = current['revision'] if current else 0
        path = '/account/application-drafts/' + self.fixture['template_id']
        saved = (await self.request(actor, 'PUT', path, json=self.draft_payload(revision, marker))).json()
        restored = next(x for x in await self.drafts(actor) if x['template_id'] == self.fixture['template_id'])
        require(saved['revision'] == revision + 1 and restored['revision'] == saved['revision'] and
                restored['answers']['overseas_institution'] == marker, 'draft persistence or account isolation failed')

    async def probes(self, actor, other, expected_workers):
        # Both PUTs use the same revision. Exactly one must commit, including across workers.
        for kind in ('workspace', 'draft'):
            for attempt in range(1 if expected_workers == 1 else 12):
                if kind == 'workspace':
                    payload = (await self.request(actor, 'GET', '/account/workspace', params=self.params())).json()['workspace']
                    path = '/account/workspace'
                    variants = [dict(payload, selection_conditions={'profile':{'course_interests':f'probe-{i}'}}) for i in range(2)]
                else:
                    items = await self.drafts(actor)
                    current = next((x for x in items if x['template_id'] == self.fixture['template_id']), None)
                    path = '/account/application-drafts/' + self.fixture['template_id']
                    variants = [self.draft_payload(current['revision'] if current else 0, f'probe-{i}') for i in range(2)]
                responses = await asyncio.gather(*(self.request(actor, 'PUT', path, json=p, expected=(200,409), fresh=True) for p in variants))
                require(sorted(r.status_code for r in responses) == [200,409], kind + ' atomic conflict failed')
                pids = {r.headers.get('X-Capacity-Worker') for r in responses}
                if None not in pids and len(pids) >= min(2, expected_workers):
                    self.conflict_checks[kind] = [{'status':r.status_code,'worker':r.headers['X-Capacity-Worker']} for r in responses]
                    break
            require(kind in self.conflict_checks, kind + ' conflict was not observed across different workers')
        await self.workspace(other, 'other-account-probe')
        await self.draft(other, 'other-account-probe')
        items = await self.drafts(actor)
        require(all(x['answers'].get('overseas_institution') != 'other-account-probe' for x in items), 'cross-account draft leak')
        await self.request(actor, 'POST', '/auth/logout', expected=(204,))
        # New connection requests cycle through workers; a revoked token must always fail.
        revocation_workers = set()
        for _ in range(max(12, expected_workers * 24)):
            response = await self.request(actor, 'GET', '/auth/me', expected=(401,), fresh=True)
            revocation_workers.add(response.headers.get('X-Capacity-Worker'))
            if len(revocation_workers) >= expected_workers:
                break
        require(None not in revocation_workers and len(revocation_workers) >= expected_workers, 'logout was not verified across every worker')
        require((await self.request(other, 'GET', '/auth/me')).json()['id'] == other['account_id'], 'logout revoked another account')

    async def actor(self, actor, index, users, duration, ramp, pace, start):
        await asyncio.sleep(max(0, start + index / max(1, users - 1) * ramp - time.perf_counter()))
        self.started += 1
        try:
            profile = (await self.request(actor, 'GET', '/auth/me')).json()
            require(profile['id'] == actor['account_id'], 'wrong signed-in account')
            # School browsing/search is client-side after loading the catalogue.
            await self.request(actor, 'GET', '/student-dashboard', params={'school':self.fixture['school']})
            iteration = 0
            while time.perf_counter() - start < duration or iteration == 0:
                cycle_start = time.perf_counter()
                marker = f"{actor['account_id'][-12:]}-{index}-{iteration}"
                await self.request(actor, 'GET', '/documents', params={'school':self.fixture['school']})
                await self.request(actor, 'GET', '/deadlines', params={'school':self.fixture['school']})
                await self.workspace(actor, marker)
                await self.draft(actor, marker)
                self.cycles += 1
                iteration += 1
                remaining = min(pace - (time.perf_counter() - cycle_start), duration - (time.perf_counter() - start))
                if remaining > 0:
                    await asyncio.sleep(remaining)
            self.completed += 1
        except (CheckFailed, KeyError, StopIteration) as error:
            self.failures['actor: ' + (str(error) if isinstance(error, CheckFailed) else type(error).__name__)] += 1

    def report(self, args, elapsed):
        def stats(values):
            values = sorted(values)
            return {'requests':len(values), 'p95_ms':round(values[math.ceil(len(values)*.95)-1]*1000,2),
                    'max_ms':round(values[-1]*1000,2)}
        routes = {k:stats(v) for k,v in self.times.items()}
        count = sum(len(v) for v in self.times.values())
        cpu_seconds = sum(g['cpu_seconds'] for g in self.generators)
        quota = generator_cpu_quota()
        cpu_fraction = cpu_seconds / max(.001, elapsed * quota)
        saturated = (cpu_fraction >= .8 or any(g['cpu_fraction'] >= .85 for g in self.generators))
        # All routes must meet the latency target; correctness is a separate mandatory gate.
        passed = (not self.failures and not saturated and self.completed == args.users and self.cycles >= args.users
                  and len(self.workers) == args.expect_workers
                  and all(v['p95_ms'] <= 2000 for v in routes.values()))
        return dict(passed=passed, users=args.users, started=self.started, completed=self.completed,
                    cycles=self.cycles, elapsed_seconds=round(elapsed,2), duration_seconds=args.duration,
                    ramp_seconds=args.ramp, stable_target_seconds=args.duration-args.ramp,
                    pace_seconds=args.pace, http_requests=count,
                    requests_per_second=round(count/elapsed,2), response_bytes=self.bytes,
                    routes=routes, failed_http_requests=self.failed_requests,
                    http_error_rate=self.failed_requests/max(1,count), conflicts=self.conflict_checks,
                    failures=dict(self.failures), statuses=dict(self.statuses), workers=dict(self.workers),
                    generator=dict(processes=len(self.generators), cpu_quota=quota,
                                   cpu_fraction=round(cpu_fraction,4), saturated=saturated,
                                   shards=self.generators),
                    scope='synthetic authenticated sessions; no external OAuth, uploads, PDFs or WAN measurement')


def generator_cpu_quota():
    try:
        quota, period = Path('/sys/fs/cgroup/cpu.max').read_text().split()
        if quota != 'max':
            return int(quota) / int(period)
    except (OSError, ValueError):
        pass
    return max(1, len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count() or 1)


def capacity_client(args):
    # Bound each pool independently; one large httpx pool can saturate a single
    # Python event loop before the server is busy.
    return httpx.AsyncClient(base_url=args.target, follow_redirects=False, trust_env=False,
        timeout=httpx.Timeout(30, pool=60),
        limits=httpx.Limits(max_connections=args.users_per_process+20, max_keepalive_connections=100))


def run_shard(args, fixture, actors, offset, start):
    async def work():
        async with capacity_client(args) as client:
            await verify_target(client, fixture['run_id'])
            load = Workload(client, fixture)
            cpu_start, wall_start = time.process_time(), time.perf_counter()
            await asyncio.gather(*(load.actor(a, i, args.users, args.duration, args.ramp, args.pace, start)
                                   for i, a in enumerate(actors, start=offset)))
            cpu = time.process_time() - cpu_start
            wall = time.perf_counter() - wall_start
            return load.snapshot(), dict(users=len(actors), cpu_seconds=round(cpu,4),
                                         cpu_fraction=round(cpu/max(.001,wall),4))
    return asyncio.run(work())


async def run(args):
    require(args.target in ('http://web:8080', 'http://127.0.0.1:18000'), 'target must be the isolated loopback/web entrance')
    require(2 <= args.users <= 2000 and args.duration > args.ramp >= 0 and args.pace >= 1, 'invalid workload settings')
    require(1 <= args.users_per_process <= 100, 'each generator must have 1..100 students')
    fixture = json.loads(Path(args.fixtures).read_text())
    run_id = os.environ.get('EXCHANGE_CAPACITY_RUN_ID', '')
    validate_fixture(fixture, run_id, args.users)
    async with capacity_client(args) as client:
        await verify_target(client, run_id)
        load = Workload(client, fixture)
        start = time.perf_counter()
        try:
            await load.probes(*fixture['actors'][args.users:args.users+2], args.expect_workers)
        except CheckFailed as error:
            load.failures['probe: '+str(error)] += 1
    if not load.failures:
        processes = math.ceil(args.users / args.users_per_process)
        load_start = time.perf_counter() + max(3, processes / 2)
        loop = asyncio.get_running_loop()
        # Spawn avoids inheriting open HTTP clients or an active event loop.
        with ProcessPoolExecutor(max_workers=processes, mp_context=multiprocessing.get_context('spawn')) as pool:
            futures = [loop.run_in_executor(pool, run_shard, args, fixture,
                fixture['actors'][offset:min(offset+args.users_per_process,args.users)], offset, load_start)
                for offset in range(0, args.users, args.users_per_process)]
            try:
                results = await asyncio.gather(*futures)
            except (BrokenProcessPool, CheckFailed, httpx.HTTPError) as error:
                load.failures['generator: '+type(error).__name__] += 1
            else:
                for snapshot, generator in results:
                    load.merge(snapshot)
                    load.generators.append(generator)
    report = load.report(args, time.perf_counter()-start)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--target', default='http://web:8080')
    p.add_argument('--fixtures', default='/artifacts/actors.json')
    p.add_argument('--output', default='/artifacts/latest.json')
    p.add_argument('--users', type=int, default=1000)
    p.add_argument('--users-per-process', type=int, default=100)
    p.add_argument('--expect-workers', type=int, choices=(1,2,4), default=1)
    p.add_argument('--duration', type=float, default=300)
    p.add_argument('--ramp', type=float, default=30)
    p.add_argument('--pace', type=float, default=10)
    try:
        raise SystemExit(asyncio.run(run(p.parse_args())))
    except (CheckFailed, httpx.HTTPError) as error:
        print('Capacity check failed: ' + (str(error) if isinstance(error, CheckFailed) else type(error).__name__))
        raise SystemExit(1)

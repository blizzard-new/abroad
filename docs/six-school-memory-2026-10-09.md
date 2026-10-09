# Six-school memory incident and release follow-up

Render reported a `512Mi` OOM kill at 2026-10-09 15:54:55 UTC for main
`1c715d21d1fd23a87087b74bbb068f4efbe74aa1`, deploy `dep-db4gm549v7es73an3su0`.
The process restarted and health recovered, but NTU browser requests received
502 responses. A live deployment was therefore not stable-release acceptance.

The catalogue retained raw and structured workflow graphs together during cold
loading, deep-copied nested partner provenance on every read, and parsed all six
destination bundles for a single home school. Concurrent response construction
compounded those allocations. The fix structures rows during reading, shares
read-only nested partner evidence while keeping collector copies independent,
filters destination bundles and publication history by home school, and permits
two large catalogue response builds at a time. Health/auth/static traffic stays
outside that queue. No source rows or evidence are discarded; the serialized
workflow and destination payloads are checked against the original algorithms.

The fixed Python candidate `bedc9a03c0968a57728d1d08f6654404a3474269` reduced an
owned local single-worker process's peak RSS/HWM for three batches of eight
concurrent CCU dashboard requests from 586.57 MiB to 338.56 MiB (42.28%). With
background cache warming enabled, 360 explicit GETs, 36 school switches and six
complete NTU globe/photo/life runs passed at a 424.57 MiB peak. These are local
process measurements, not Render cgroup metrics or a guarantee for arbitrary
traffic. Full 35-migration PostgREST/Storage and governance runtime checks also
passed, including 74 governance RPC posts and compatibility with the previously
deployed Python modules and models.

Full browser regression additionally exposed a reproducible existing UI race:
`initIcons()` replaced a menu SVG between pointerdown and pointerup, discarding
the click. Icon rendering now preserves unchanged SVG nodes and renders new or
changed icons; the asset URL changes so clients obtain the fix. A controlled
pointer test fails before this change and succeeds afterward. The calendar
reminder test also uses an explicit Taipei browser timezone and its actual
calendar date, matching notification semantics after UTC/Taipei midnight differs.
Its notification and completion assertions remain intact.

This follow-up needs no DB migration. Existing migration bytes, source datasets,
licensed photos, source years, missing/pending/zero distinctions, dependencies,
Actions definitions and security permissions remain unchanged. Quality remains
disabled. Render still auto-deploys a main commit, so merge only the tested SHA;
then verify that exact deploy, low-load six-school and NTU flows, memory headroom
and absence of new failure/restart events. A code revert needs no DB reversal but
returns to the known OOM-prone implementation; do not call that stable recovery.

Complete raw passes, failures, reruns, source guards and the current release gate
are recorded in [the integration evidence branch](https://github.com/blizzard-new/abroad/tree/artifacts/integration-20261009/docs/integration-20261009)
and [PR #6](https://github.com/blizzard-new/abroad/pull/6). Earlier comparative long
browser runs that timed out taking globe screenshots are retained as failures.

# Memory release blocker — isolated fix in progress

Production merge `1c715d21d1fd23a87087b74bbb068f4efbe74aa1` remains live but had a confirmed Render 512Mi OOM on 2026-10-09 15:54:55Z. This is not a stable-release acceptance.

Fixed candidate: `bedc9a03c0968a57728d1d08f6654404a3474269`, branch `integration/six-school-memory-20261009`. Parent explicitly authorized the necessary fix PR, merge and deployment after isolated verification. No plan, Render settings, security permissions, credentials, billing, Quality state or DB changes.

The cold workflow loader retained raw and structured graphs together. Every read deep-copied nested partner evidence, and per-school destination reads parsed all six bundles. Concurrent catalogue response construction compounded these allocations. The candidate structures rows while reading, shares read-only nested partner evidence while retaining independent collector copies, scopes destination parsing and publication history to the requested school, and permits two catalogue response builds at a time during the app lifespan. Health/auth/static requests are outside that queue.

All tracked source datasets, static assets, migrations, lock/dependencies, workflow definitions and OpenAPI remain byte-identical; see memory-release-scope-proof.json. Full-payload regression assertions cover all six workflow bundles, six destination sets with local override, and the complete CCU nested evidence payload.

Exploratory runs (not final acceptance): baseline browser sequence peak 489.8 MiB; shallow copies 453.5; scoped profile reads 445.3; streaming workflow structuring 435.0; bounded catalogue experiment 410.1. The exploratory edited-tree runs are recorded as such. Baseline and fixed-SHA longer soak plus the complete 2,645-case suite are running; no final stability claim. One auxiliary command named a nonexistent test_openapi_contract.py and exited 4 before running tests; corrected fixed-SHA four-test run and the separate OpenAPI exporter both passed.

## Fixed-SHA evidence at 16:35 UTC

Eight parallel CCU dashboard requests, repeated three batches on an otherwise identical owned local process: baseline peak 615,059,456 bytes (586.57 MiB), fixed peak 355,004,416 bytes (338.56 MiB), reduction 42.28%. All HTTP assertions completed; baseline exceeds the 512 MiB budget. Both source guards clean. See memory-eight-concurrent-comparison.json.

Fixed SHA with EXCHANGE_WARM_CACHES=1: 360 explicit GETs, 36 school switches and six complete NTU globe/photo/life tests passed in 8m56s; peak 445,198,336 bytes (424.57 MiB), 87.43 MiB below 512 MiB. This is process RSS/HWM, not a production Render metric. See memory-warm-soak-summary.json. Two earlier non-warm comparative long browser runs failed at Playwright globe screenshot timeout; those raw failures remain and are not relabeled as passes.

Full 35-migration Docker/PostgREST/Storage runtime passed on bedc9a03, including 17 governance groups / 74 RPC posts, account-deletion cleanup, six school forum policy and exact old deployed Python source/model compatibility.

The 2,645-case full suite remains running. One mobile frozen-clock navigation case failed, and its first unchanged isolated candidate rerun also failed. An unchanged original-main isolated rerun passed. The candidate is still draft and not accepted for merge while this difference is investigated.

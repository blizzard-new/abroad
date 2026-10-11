# CGU source recovery — first implementation checkpoint

App candidate: [985224fd01748a6c591fc183362847d6d7d21c35](https://github.com/blizzard-new/abroad/commit/985224fd01748a6c591fc183362847d6d7d21c35), [Draft PR #12](https://github.com/blizzard-new/abroad/pull/12). No main merge, deploy, production DB write or security/billing setting change.

This is an interim checkpoint, not release acceptance. Initial tests ran during implementation (metadata preserves start/end SHA and dirty status). A clean fixed-SHA six-school regression and memory run are still in progress and will be added separately. Do not label these early runs as clean fixed-SHA full-suite acceptance.

| Run | Raw result | Interpretation |
|---|---|---|
| recovery-unit-initial | 46 passed | source faults, API, dashboard/cache |
| recovery-source-rerun | 23 passed / 1 failed | new test used invalid model status `pending_quota`; corrected to actual `quota_unconfirmed` |
| recovery-source-rerun2 | 24 passed | extra zero/missing/pending preservation and schema checks |
| browser-recovery-initial | 2 passed / 2 failed | test referred to nonexistent frontend function |
| browser-recovery-r2 | 3 passed / 1 failed | mobile card needed opening before detail button click |
| browser-recovery-r3 | 4 passed | real browser + local API; recorded-source failure/recovery fixture |
| recovery-full-unit-initial | 2193 passed / 3 failed / 12 skipped | advisor fixture, NCU exact bundle null-field drift, old JS harness missing PR8 helper; fixes tracked separately |
| advisor-fixture-rerun | 1 passed | original assertion preserved; explicit catalogue fixture injected |
| live-source-acceptance | passed, two HTTP200 sources, 77 rows | actual public GET, not a recorded-source response |

The live fetch completed 2026-10-11T10:31:30.918513Z. Row SHA256 is `afbd6356d0a46e1d593d04f3de5a47a4507c0f553bd3cd4a6e617cff689a3ade`, identical to the dated fallback, with each source receipt retained. This verifies retrieval, not a current academic cycle. The fixture browser tests deliberately inject timeout / absence / recovery; they are not live availability evidence.

Screenshots: `browser-source-fixtures-r3` contains mobile390 / desktop1440 saved-outage list/detail and no-snapshot map states. Reviewed mobile detail shows source timestamp and stale/reference explanation above the school detail, with no horizontal overflow.

Pending: full integrated suite after fixes; six-school browser and 512MiB single-worker measurements; #9 NTU source-body delivery, #10 CCU and #11 NCU semantic merge; TKU finished fixed SHA. PR9's missing original source bodies remain a separate unresolved delivery issue.

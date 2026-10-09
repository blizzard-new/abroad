# Memory release status

PR #6 fixed candidate: `f3e0b666f28d82deaf17ceec701d8f0131ea2b5c` (draft, not merged). Main remains `1c715d21`; production OOM is not accepted as stable delivery.

The original memory-only full suite is completing at `bedc9a03`; two failures (SVG pointer race and UTC/Taipei test date) remain visible in raw evidence. Controlled reproduction established both causes; final candidate fixes them without deleting assertions, data or sources. Four focused cases passed. Final complete 2,647-case regression is running. Three navigation screenshot cases failed with explicit local `Errno 28: No space left on device`; isolated PostgreSQL/Storage validation and generated wheel copies exhausted the disk. All files are preserved while inactive generated outputs/worktree are relocated to `/tmp` with original-path symlinks and proof. All three original cases have now passed on unchanged f3 after disk recovery (clean start/end guards). The full-run failures remain recorded.

Local memory-only candidate: eight-request bursts fell from 586.57 to338.56MiB; cache-warm soak passed360GETs/36switches/6NTUflows at424.57MiB. These are process RSS/HWM, not production cgroup readings. Final f3 wheel/lock/OpenAPI/compile/JS/SQL and complete35migration/PostgREST/Storage/governance/oldPython runtime checks passed with clean source guards. Final f3 cache-warm memory soak is running. Data/migrations/security/settings are unchanged.

Next gates: finish all raw tests, reconcile exact collected cases and reruns, run final exact-SHA memory/browser workload, merge only tested PR6 SHA under the parent's explicit authority, verify exact Render deploy live, then low-load six-school/NTU smoke and memory/event stability. Do not change Quality, Render settings, billing or credentials.

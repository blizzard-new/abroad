# 原始run完整索引

數字不跨重疊run加總。診斷exit0只表示量測完成，不表示記憶體budget通過。失敗run若提前停止，後續未執行步驟不可算通過。完整stdout/stderr和精確SHA以metadata及來源manifest為準。

| Run | status (exit) | 起始SHA | 固定性／用途 | pytest原始結尾 |
|---|---|---|---|---|
| [active-warmup-health](active-warmup-health/metadata.json) | passed (0) | 1a3181fa | 開發中／工作樹有變更 | 1 passed in 4.60s |
| [bounded-memory-targeted](bounded-memory-targeted/metadata.json) | passed (0) | 64e23349 | 固定工作樹 | 8 passed in 22.91s |
| [bounded-source-audit-memory-command](bounded-source-audit-memory-command/metadata.json) | failed (1) | 64e23349 | 固定工作樹 |  |
| [browser-recovery-initial](browser-recovery-initial/metadata.json) | failed (1) | 9927ec1d | 開發中／工作樹有變更 | 2 failed, 2 passed in 13.82s |
| [browser-recovery-r2](browser-recovery-r2/metadata.json) | failed (1) | 9927ec1d | 開發中／工作樹有變更 | 1 failed, 3 passed in 44.11s |
| [browser-recovery-r3](browser-recovery-r3/metadata.json) | passed (0) | 9927ec1d | 開發中／工作樹有變更 | 4 passed in 13.85s |
| [compact-completion-targeted](compact-completion-targeted/metadata.json) | passed (0) | 23365f9c | 開發中／工作樹有變更 | 23 passed in 11.26s |
| [compact-final-cold-memory-command](compact-final-cold-memory-command/metadata.json) | passed (0) | 1a3181fa | 固定工作樹 |  |
| [compact-final-contracts](compact-final-contracts/metadata.json) | passed (0) | 1a3181fa | 固定工作樹 |  |
| [compact-final-warm-memory-command](compact-final-warm-memory-command/metadata.json) | failed (1) | 1a3181fa | 固定工作樹 |  |
| [comparison-memory-985224fd-command](comparison-memory-985224fd-command/metadata.json) | failed (1) | 985224fd | 診斷／比較；實際來源看stdout及manifest |  |
| [final-contracts](final-contracts/metadata.json) | passed (0) | 6c8b8382 | 固定工作樹 |  |
| [final-fixed-head-live-fetch](final-fixed-head-live-fetch/metadata.json) | passed (0) | 1a3181fa | 固定工作樹 |  |
| [final-frozen-contracts](final-frozen-contracts/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 |  |
| [final-frozen-delivery-audit](final-frozen-delivery-audit/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 |  |
| [final-full-unit](final-full-unit/metadata.json) | passed (0) | 6c8b8382 | 固定工作樹 | 2240 passed, 12 skipped in 633.12s (0:10:33) |
| [final-live-source-command](final-live-source-command/metadata.json) | passed (0) | 6c8b8382 | 固定工作樹 |  |
| [final-ncu-browser](final-ncu-browser/metadata.json) | passed (0) | 6c8b8382 | 固定工作樹 | 9 passed, 10 deselected in 280.68s (0:04:40) |
| [final-release-live-fetch](final-release-live-fetch/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 |  |
| [final-scoped-memory-targeted](final-scoped-memory-targeted/metadata.json) | passed (0) | 23365f9c | 開發中／工作樹有變更 | 98 passed in 44.42s |
| [final-source-audit](final-source-audit/metadata.json) | passed (0) | 6c8b8382 | 固定工作樹 |  |
| [final-third-pass-source-parity](final-third-pass-source-parity/metadata.json) | passed (0) | 1a3181fa | 固定工作樹 |  |
| [final-wheel-build](final-wheel-build/metadata.json) | failed (1) | 0d3d671e | 固定工作樹 |  |
| [final-wheel-build-r2](final-wheel-build-r2/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 |  |
| [fixed-985224fd-recovery-and-six-school](fixed-985224fd-recovery-and-six-school/metadata.json) | passed (0) | 985224fd | 固定工作樹 | 65 passed in 492.21s (0:08:12) |
| [frozen-final-browser](frozen-final-browser/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 | 91 passed in 1063.04s (0:17:43) |
| [frozen-final-full-unit](frozen-final-full-unit/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 | 2287 passed, 12 skipped in 803.92s (0:13:23) |
| [full-suite-three-failures-rerun](full-suite-three-failures-rerun/metadata.json) | passed (0) | 985224fd | 開發中／工作樹有變更 | 27 passed in 7.20s |
| [integrated-browser](integrated-browser/metadata.json) | passed (0) | b2aaee8f | 固定工作樹 | 42 passed in 743.82s (0:12:23) |
| [integrated-contracts](integrated-contracts/metadata.json) | passed (0) | b2aaee8f | 固定工作樹 |  |
| [integrated-full-unit](integrated-full-unit/metadata.json) | failed (1) | b2aaee8f | 固定工作樹 | 2 failed, 2238 passed, 12 skipped in 730.61s (0:12:10) |
| [integrated-memory-command](integrated-memory-command/metadata.json) | failed (1) | b2aaee8f | 固定工作樹 |  |
| [integrated-source-audit-command](integrated-source-audit-command/metadata.json) | failed (1) | b2aaee8f | 固定工作樹 |  |
| [integrated-source-audit-r2](integrated-source-audit-r2/metadata.json) | failed (1) | b2aaee8f | 固定工作樹 |  |
| [integrated-source-audit-r3](integrated-source-audit-r3/metadata.json) | passed (0) | b2aaee8f | 固定工作樹 |  |
| [integrated-streaming-memory-command](integrated-streaming-memory-command/metadata.json) | failed (1) | 6c8b8382 | 固定工作樹 |  |
| [integrated-targeted-initial](integrated-targeted-initial/metadata.json) | failed (1) | afd76931 | 開發中／工作樹有變更 | 5 failed, 83 passed in 47.15s |
| [integrated-targeted-r2](integrated-targeted-r2/metadata.json) | passed (0) | afd76931 | 開發中／工作樹有變更 | 6 passed in 3.35s |
| [latest-data-before-memory-command](latest-data-before-memory-command/metadata.json) | failed (1) | 0d3d671e | 診斷／比較；實際來源看stdout及manifest |  |
| [live-source-run](live-source-run/metadata.json) | passed (0) | 9927ec1d | 開發中／工作樹有變更 |  |
| [loader-benchmark-old](loader-benchmark-old/metadata.json) | passed (0) | 6c8b8382 | 固定工作樹 |  |
| [loader-benchmark-streaming](loader-benchmark-streaming/metadata.json) | passed (0) | 6c8b8382 | 固定工作樹 |  |
| [memory-985224fd-baseline-command](memory-985224fd-baseline-command/metadata.json) | passed (0) | 985224fd | 固定工作樹 |  |
| [memory-bounded-two-diagnostic-command](memory-bounded-two-diagnostic-command/metadata.json) | failed (1) | 3a4977c9 | 診斷／比較；實際來源看stdout及manifest |  |
| [memory-four-workers-one-catalogue-diagnostic-command](memory-four-workers-one-catalogue-diagnostic-command/metadata.json) | passed (0) | 3a4977c9 | 診斷／比較；實際來源看stdout及manifest |  |
| [memory-held-diagnostic-command](memory-held-diagnostic-command/metadata.json) | passed (0) | 3a4977c9 | 診斷／比較；實際來源看stdout及manifest |  |
| [milestone-browser](milestone-browser/metadata.json) | failed (1) | 3a4977c9 | 固定工作樹 | 2 failed, 76 passed in 1000.91s (0:16:40) |
| [milestone-contracts](milestone-contracts/metadata.json) | failed (1) | 8b77c468 | 固定工作樹 |  |
| [milestone-contracts-r2](milestone-contracts-r2/metadata.json) | passed (0) | 3a4977c9 | 固定工作樹 |  |
| [milestone-delivery-audit](milestone-delivery-audit/metadata.json) | passed (0) | 3a4977c9 | 固定工作樹 |  |
| [milestone-delivery-audit-r2](milestone-delivery-audit-r2/metadata.json) | passed (0) | eb4a5cdd | 固定工作樹 |  |
| [milestone-full-unit](milestone-full-unit/metadata.json) | failed (1) | 3a4977c9 | 固定工作樹 | 1 failed, 2250 passed, 12 skipped in 714.52s (0:11:54) |
| [milestone-memory-command](milestone-memory-command/metadata.json) | failed (1) | 3a4977c9 | 固定工作樹 |  |
| [milestone-ncu-count-diagnostic](milestone-ncu-count-diagnostic/metadata.json) | failed (1) | 3a4977c9 | 診斷／比較；實際來源看stdout及manifest | 1 failed in 1.51s |
| [milestone-ntu-archives](milestone-ntu-archives/metadata.json) | passed (0) | 8b77c468 | 固定工作樹 |  |
| [milestone-photo-license-live](milestone-photo-license-live/metadata.json) | passed (0) | 3a4977c9 | 固定工作樹 |  |
| [milestone-targeted](milestone-targeted/metadata.json) | failed (1) | 8b77c468 | 固定工作樹 | 1 failed, 80 passed in 54.54s |
| [ncu-streaming-and-counts](ncu-streaming-and-counts/metadata.json) | passed (0) | b2aaee8f | 開發中／工作樹有變更 | 126 passed in 40.49s |
| [ntu-third-fixed-input-audit](ntu-third-fixed-input-audit/metadata.json) | failed (1) | 0d3d671e | 固定工作樹 |  |
| [ntu-third-fixed-input-audit-r2](ntu-third-fixed-input-audit-r2/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 |  |
| [pool-final-cold-memory-command](pool-final-cold-memory-command/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 |  |
| [pool-final-warm-memory-command](pool-final-warm-memory-command/metadata.json) | passed (0) | 0d3d671e | 固定工作樹 |  |
| [recovery-full-unit-initial](recovery-full-unit-initial/metadata.json) | failed (1) | 9927ec1d | 開發中／工作樹有變更 | 3 failed, 2193 passed, 12 skipped in 535.82s (0:08:55) |
| [recovery-unit-initial](recovery-unit-initial/metadata.json) | passed (0) | 9927ec1d | 開發中／工作樹有變更 | 46 passed in 7.58s |
| [repaired-browser](repaired-browser/metadata.json) | passed (0) | eb4a5cdd | 固定工作樹 | 78 passed in 979.72s (0:16:19) |
| [repaired-cold-full-memory-command](repaired-cold-full-memory-command/metadata.json) | failed (1) | eb4a5cdd | 固定工作樹 |  |
| [repaired-contracts](repaired-contracts/metadata.json) | passed (0) | eb4a5cdd | 固定工作樹 |  |
| [repaired-full-unit](repaired-full-unit/metadata.json) | passed (0) | eb4a5cdd | 固定工作樹 | 2264 passed, 12 skipped in 748.02s (0:12:28) |
| [repaired-warm-full-memory-command](repaired-warm-full-memory-command/metadata.json) | failed (1) | eb4a5cdd | 固定工作樹 |  |
| [scoped-life-memory-probe-command](scoped-life-memory-probe-command/metadata.json) | failed (1) | eb4a5cdd | 診斷／比較；實際來源看stdout及manifest |  |
| [streamed-audit-targeted](streamed-audit-targeted/metadata.json) | passed (0) | eaf4e1b9 | 固定工作樹 | 135 passed in 45.75s |
| [streamed-hash-memory-probe-command](streamed-hash-memory-probe-command/metadata.json) | failed (1) | eb4a5cdd | 診斷／比較；實際來源看stdout及manifest |  |
| [streamed-ncu-full-payload-parity](streamed-ncu-full-payload-parity/metadata.json) | passed (0) | eaf4e1b9 | 固定工作樹 |  |
| [streamed-source-audit-memory-command](streamed-source-audit-memory-command/metadata.json) | passed (0) | eaf4e1b9 | 固定工作樹 |  |
| [two-worker-scoped-memory-probe-command](two-worker-scoped-memory-probe-command/metadata.json) | failed (1) | eb4a5cdd | 診斷／比較；實際來源看stdout及manifest |  |
| [warm-pool-targeted](warm-pool-targeted/metadata.json) | passed (0) | 1a3181fa | 開發中／工作樹有變更 | 19 passed in 12.18s |

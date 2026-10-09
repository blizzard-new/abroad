# 六校整合與記憶體修正發布驗收完成

依父對話後續明確授權完成四支原PR、必要DB先行發布與OOM修正PR6。本次低負載驗收通過，不等同任意流量容量保證。

正式main：`8139be4d3604a60265029dbbe41af21c094e609d`；Render `dep-db4i4obrjlhs738ng200`於`2026-10-09T17:25:30.577437Z` live，merge tree與最終候選`49882dfce64449abeb682d01ae01a8da5c10ba8d`完全相同。[最終機器驗收](final-release-acceptance.json) · [merge proof](memory-pr6-merge-proof.json) · [Render live](memory-pr6-render-live.json)

|PR|驗收head|實際main merge|
|---|---|---|
|#5|`b33ad27ff13912780dfb94f91504dd11b1ef6a21`|`58a6b7cf09a36d1892a1ac14a71332f1e8747a33`|
|#3|`dc4d054c2746388c40bd256f4203ef066b60be03`|`b22220f811f91cd4b86e16da25da8e0684123d87`|
|#4|`4a28daaa682b7aa55e6bb0497a8a6cde315a967f`|`e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86`|
|#2|`31234305f6ecd477ff8eb3915dd2d3d6f4141477`|`1c715d21d1fd23a87087b74bbb068f4efbe74aa1`|
|#6|`49882dfce64449abeb682d01ae01a8da5c10ba8d`|`8139be4d3604a60265029dbbe41af21c094e609d`|

## 原始測試與補驗

|完整run|唯一案例|passed|failed|原有skip|
|---|---:|---:|---:|---:|
|原整合d182|2641|2599|28|14|
|四PR修正0fdc|2641|2627|0|14|
|記憶體初版bedc|2645|2628|3|14|
|最終產品f3e0b666|2647|2629|4|14|

最後4失敗為3筆本機ENOSPC截圖寫入及1筆app/community-reader配對快取版本。相同f3的3原截圖案例補驗全過；最終49882dfc的6contract/pipe與9forum/session/icon browser全過且起訖clean。有效唯一結果2633passed、0未解決failed、14既有skip，collection/JUnit/log完全對應，沒有遺漏或移除測試。[逐案對帳](memory-final-acceptance-summary.json)、[完整原始結果](memory-final-full-summary.json)。

最終head比完整run只改測試pipe I/O與HTML一個community-reader query版本；所有Python、JavaScript、資料、來源、SQL、依賴、runner byte相同。[精確差異](memory-final-release-delta-proof.json)。前一bedc的SVG pointer競態、UTC/Taipei日期、stderr readline/communicate緩衝問題均獨立定位並保留原失敗。一次browser補驗遇到同時wheel build生成untracked build/，該原guard紀錄保留，之後9案clean重跑通過。

14skip：9PhaseC、4Ollama未啟動、1pytest opt-inDocker；[原清單](original-full-skips.json)。實際完整Docker/PostgREST/Storage另已執行，35migration、17治理組、74RPC、102個舊Python模組和模型相容性全passed，cleanup完成。[runtime](memory-final-runtime-result.json)。

最終wheel、uv lock、OpenAPI、Python compile、JS、SQL parser、whitespace通過；2527entries、2522來源檔byte相同，15張未授權新照片排除。wheelSHA256：`d2283478e7650bc9ad7f945071a6af2bad7c97a9eed1eed2dc047a54e046ab18`。[wheel證據](memory-final-498-release-checks-wheel-proof.json)。

## OOM根因、修正與實站結果

舊main1c715d21在15:54:55UTC遭512Mi OOM並造成NTU502，健康恢復不算穩定發布。原因是原始/結構化流程圖同時駐留、每次deep-copy來源證據、單校讀取解析全六校目的資料及併發回應疊加。PR6改逐筆結構化、只讀共用巢狀證據、按母校載入、最多兩個大型回應建置；沒有刪資料。SVG重繪也保留既有節點，避免pointerdown/up間失去click。

本機同樣三批8併發：586.57→338.56MiB（42.28%降低）。完整暖快取384GET/36選校/6NTU流程passed445.76MiB；最終head再測先完成全部生活頁暖快取、最後三批8併發，384GET/36選校/6NTU全passed442.10MiB。[burst比較](memory-eight-concurrent-comparison.json)、[暖快取](memory-final-warm-soak-summary.json)、[改變順序補驗](memory-final-post-browser-burst-summary.json)。這些是本機程序RSS/HWM，與Render cgroup不可混稱。

正式站首頁/app.js exactbytes、6學校HTTP、6guest論壇401、12次390/1440選校、2個390/1440NTU照片/地球/生活完整流程全部passed。正式站僅公開讀取，沒有建立測試帳號或寫合成內容。[六校](memory-production-six-school-result.json)、[NTU](memory-production-ntu-result.json)、[檔案身份](memory-production-identity-result.json)。

觀察截至`2026-10-09T17:40:36Z`，live後15.09分鐘、流程完成後安靜觀察7.65分鐘。正式採樣峰值463.16MiB、最後457.93MiB、最小採樣餘裕48.84MiB；0新failure/restart事件、0app error log，最後health200。原OOM前採樣峰值508.33MiB。30秒採樣不是瞬時最大值，保留有限流量與時間窗口。[原始Render指標/事件/錯誤查詢](memory-production-final-observation.json)。

## DB與發布控制

正式DB35份已按序套用並逐份readback：CCU/NCU compatibility `20261009135343`先於PR3；TKU `20261009153249_verified_email_school_community`、`20261009153347_community_byline_aliases`、`20261009153438_atomic_governance_commands`先於PR2。SQLbytes、signature/owner/ACL/security/search_path皆已核對；helper未新增service_role授權。[mapping](production-tku-migration-mapping.json)、[01](production-tku-01-readback.json)、[02](production-tku-02-readback.json)、[03](production-tku-03-readback.json)。PR6沒有migration。

Quality374368612維持disabled_manually；Render main/autoDeploy/commit/單worker/free512Mi與其餘核對設定不變。未新增憑證、付費或改branch protection/安全權限。[GitHub最後讀回](final-five-pr-github-state.json)、[Render設定對比](memory-final-render-configuration.json)。Actions帳務阻擋與5個原有migration timestamp差異仍保留，未repair/bulkpush，不以workflow狀態冒充DB成功。

回復：程式可正常Git revert而保留相容DB35份與append-only audit；前版1c715d21已知OOM，回退不是穩定修復，五校e5也曾接近512Mi，應隔離定位後forward修正。不可盲降governanceRPC/capabilitymarker或還原整庫。[原發布依賴與DB計畫](release-plan.md)、[PR6發布/回復計畫](memory-release-plan.md)。

## 尚未完成的資料範圍

CGU154/NTPU409/NTU288原workflow完整payload與f6ad逐校canonicalhash相同。CCU55legacy、NCU214pending、TKU4當期有限partial加124舊年參考仍不是全校當期完整，資料完整度不能宣稱已到長庚標準；missing/pending/zero及來源年度保留。NTU266licensed/20needs_review/2missing、269代表位置、1622生活節錄/124校保留年份，14地區出發提醒仍明確404。

所有原始failed/skip/notrun、修正、補驗與前後SHA都保留；大型原log/XML使用可驗證無損gzip，未刪原始證據。[無損壓縮SHA](lossless-compression-manifest.json) · [全檔SHA](file-manifest.json) · [最後狀態](execution-status.json)。

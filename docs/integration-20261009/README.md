# 六校整合／發布驗收：2026-10-09 15:12 UTC

PR #5、#3、#4 已依序合併，且各自 Render 對應 commit live 後通過實站驗收。現在正式 main 為 `e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86`，Render `dep-db4feg0ae00c73a276s0`，五校 5 HTTP＋390/1440 共 10 browser passed。PR #2 尚未合併、TKU 三份正式 DB migration 尚未套用。

固定候選 `0fdc6cfa6a4902fb83374a77025f45dffb071562` 已推 `integration/six-schools-release-20261009`。完整 2,641 案例正在四片重跑，精確進度見 [final-full-progress.json](final-full-progress.json)；完成前不報全套 passed。工作樹凍結，所有 raw run 都記錄開始／結束 SHA、tree、dirty status、命令、時間及 exit。

- 原完整 `d1827d75`：2,599 passed／28 failed／14 既有 skipped，原始 logs/XML 與逐案例摘要全部保留。離線 TKU builder 造成 35 metadata 差異也記為 source-guard failed；等該 run 結束後才恢復自有生成差異。
- 修正候選 `0fdc6cfa`：原 18 個後端失敗與 10 個瀏覽器失敗全部重跑 passed，65 項契約／SQL／workflow 解析、2 項額外 CCU/NCU API 權限邊界、wheel、uv lock、OpenAPI、JS syntax 通過。無新增 skip 或放寬 skip 條件。
- 全 35 migration runtime 在新建排序、實際部署排序均 passed；另以原五校 `e5c6d5c` 治理 client 連新 DB，stage、雙審、publish、readback 12 次 HTTP 200。真 Storage、2 PostgREST、CAS overlap、late-failure atomicity、17 治理安全組／74 RPC／31 audit、六校跨校 verified-email 政策均已驗證。
- CGU154／NTPU409／NTU288 完整模型 payload 與最初 main `f6ad1b8` canonical hash 逐校相同。wheel 2527 檔確認排除 15 張無授權新照片、納入 TKU 字型 OFL。

## 固定發布紀錄

|PR|合併前 HEAD|main merge SHA|Render deploy|
|---|---|---|---|
|#5|b33ad27ff13912780dfb94f91504dd11b1ef6a21|58a6b7cf09a36d1892a1ac14a71332f1e8747a33|dep-db4ethpbgiqc738r2iag|
|#3|dc4d054c2746388c40bd256f4203ef066b60be03|b22220f811f91cd4b86e16da25da8e0684123d87|dep-db4f56rbc2fs73bo5ok0|
|#4|4a28daaa682b7aa55e6bb0497a8a6cde315a967f|e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86|dep-db4feg0ae00c73a276s0|
|#2|候選0fdc6cfa；原上游b67d79aa|未合併|未部署|

## 發布與資料界線

[release-plan.md](release-plan.md) 記錄依賴圖、三份精確 TKU SQL、正式 DB 定義前置核對、逐份 readback、實際 version 與檔名對齊、程式回退保留相容 DB 的程序。目前正式 DB 僅新增 CCU/NCU allowlist `20261009135343`；四個函式 15:11 UTC 再核對無變動。既有五個 migration timestamp 差異不 repair、不 bulk db push。Quality 374368612 仍 disabled_manually；原 TKU quality.yml 的測試流程改動保留，整合者未修改該檔。Render autoDeploy/trigger/main、branch protection、憑證、費用均未調整。

資料仍有明示缺口：CCU55 legacy、NCU214 pending、TKU4 partial 與124旧年參考不升格為全校當期完整。NTU266 licensed／20 needs_review／2 missing，269代表位置；1622有效生活節錄／124校保留來源年度。14地區出發提醒缺研究資料，API清楚回404。missing／pending／zero維持不同。14原skip詳見 [original-full-skips.json](original-full-skips.json)，其中4項本機Ollama未啟動、9項既有Phase C、1項pytest opt-in Docker（另完整runtime已執行）。

精確狀態：[execution-status.json](execution-status.json)。原始失敗與較早 checkpoint：[checkpoint-before-final-full.md](checkpoint-before-final-full.md)。所有交付檔案 SHA256：[file-manifest.json](file-manifest.json)。

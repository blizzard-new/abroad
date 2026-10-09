# 固定程式SHA驗收：77dfd84（2026-10-08）

所有本目錄原始gate結果只屬於 **`77dfd84008d438d3602da61991733ecfdf8d65a8`**。此目錄是完成測試後新增的證據，後續證據commit沒有重新執行測試，不能把本結果標為該證據commit的測試。歷史e838307原有437passed/1failed結果保留在另一目錄，不覆寫。

[原始summary](final-validation-summary.json)、[gate執行log](gate-orchestration.txt)、[實際測試選檔](test-selection.json)、[起始HEAD/dirty原始stdout](git-boundary-start.json)、[結束HEAD/dirty原始stdout](git-boundary-end.json)可直接審查；兩端SHA一致、porcelain原始stdout皆空。這輪boundary是當時直接捕捉，非事後推導。

|固定SHA實際結果|結果|
|---|---|
|459回歸|452 passed / 7 skipped / 0 failed / 0 errors；JUnit 398.65s|
|102瀏覽器|102 passed / 0 skipped / 0 failed / 0 errors；兩組JUnit合計1166.21s；較長組wall 673.78s|
|實際四校bundle UI/API|4個無response/state mock案例；新延遲／排隊草稿8個案例只改實際response送達時間或browser clock|
|重建／wheel|7 builders、1162檔逐byte相同；wheel SHA `cdeab38818cf698664ff944d1d658e483287051215f8126771c76206bdc832ab`|
|原校資料|46份main官方data及77CGU published hash不變；956份既存raw來源＋131份host附件與e838307逐byte相同|
|合約／語法|110API paths／existing required保留；OpenAPI export、lock（uv0.11.26）、compileall、指定4JS及本輪Ruff通過|

[regression XML](regression.xml)/[log](regression.txt)、[browser XML](browser.xml)、[group1 XML](browser-group-1.xml)/[log](browser-group-1.txt)、[group2 XML](browser-group-2.xml)/[log](browser-group-2.txt)、[case union](case-union.json)列459＋102案例，102個browser ID皆唯一。7skip為6個既有PhaseC＋1個Docker opt-in，實際skip理由保留，不是全執行。

NTPU已載入206 guide而coverage計數0的實際API問題已修，NTU alias回歸亦已修；四校8個home別名、新增隔離及既有NTPU/NTU測試在此SHA通過。失敗53e88e7的443passed/1failed原證據保留，不覆寫。延遲home A→B→A、target/detail晚回應、切校前排隊草稿在390／1440均通過；[network timing receipts與截圖](browser-evidence)保留原API response hash，無假政策response。來源新增當期2欄後海外935欄為306current／331pending／206missing／20reference／71conflict／1explicit_not_announced；0校17欄完整、0完整host文件集合。

本輪程式與可審查部分資料可供整合，**不接受「資料已全完成」「完整CI已通過」「可發布／同等資料完整度已達成」**：[驗收矩陣](acceptance-results.json)分開記錄原因。遠端[run 37851564299](https://github.com/blizzard-new/abroad/actions/runs/37851564299) failure/0 jobs，没有測試；[唯讀CI語法診斷及可審查patch](../ci-readonly/README.md)未變更正式workflow、付款、權限或憑證。

Jena官方DOC實點仍TLS憑證錯誤，見external-template-390/1440記錄；[正常TLS官方替代HTTP receipt](jena-official-alternative-https.json)取得HTTP200、46080bytes且hash與保存官方附件相同。這是交換延長表，不是初次申請／2027新表；沒有停TLS驗證、信任新憑證或回放外部response，也不假稱browser live通過。

[跨分支snapshot](integration-acceptance-snapshot.json)固定main與NTU/NCU/TKU heads及各共享檔hash；沒有合併其他分支。跨分支隔離整合、其餘repo測試、Supabase parse/runtime與dependency vulnerability audit仍未執行。全55校仍未宣稱公開來源查盡，149份可讀尚無語意查核紀錄、174份已讀未映射，後續必須继续逐份查年／計畫／身分。[逐校正文清冊](../../ccu-body-review-triage-2026-10-08.md)與tested bundle的body-review-triage.json可區分來源狀態。

[file manifest](file-manifest.json)為本目錄所有其他檔SHA-256，原始logs/XML未修改。

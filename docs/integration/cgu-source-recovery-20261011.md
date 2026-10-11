# CGU 來源恢復與本輪隔離整合

此分支僅供隔離驗收，從 PR #8 `9927ec1d8765a9772671bbaa68e7f920995f1258` 開始。main 基線 `59a20f27fcee00fb597abc79e75ec11778317422`。尚未 merge main、部署或修改正式 DB；Quality 停用、Render autoDeploy、branch protection、憑證及付費均未改動。

## CGU 小範圍修復

- API 的 dashboard 與合作校／流程查找共用 CGU provider；基礎 dashboard 不再獨立下載及永久快取空名冊。
- 兩份公開表格均 HTTP 200、必要欄位 schema 有效、有可解析學校，且完整批次驗證成功，才原子替换整批。任一來源失敗、空白、結構不符、較舊時間或磁碟寫入失敗，保留前一完整批次。
- 成功批次更新間隔 600 秒，失敗重試至少 60 秒；背景更新 single flight，請求直接讀已存資料。runtime JSON 以同目錄 temporary file、fsync、os.replace 寫入，無額外 DB migration。
- 隨程式交付 2026-10-11 09:58:47 UTC 的 77 筆顯示列及兩份原始公開 GVIZ 內容／SHA256 收據，供暫時性檔案系統的冷啟動備援。records SHA256 `afbd6356d0a46e1d593d04f3de5a47a4507c0f553bd3cd4a6e617cff689a3ade`。77 是顯示列，不是當期可申請學校總數。
- 年度、名額、空白／零值、可申請與發布狀態皆保持來源原值。來源取得成功不等於當期資料已核實，`current_cycle_verified=false`。
- 新增可選 `catalogue_source` API 欄位，區分 `retrieved`、`saved_reference`、`unavailable`，分列上次成功／本次嘗試時間與失敗原因。其他校省略此欄，保持既有 bundle 序列化格式。
- 清單、地圖與詳細頁顯示來源時間／參考性；完全沒有有效備援時顯示暫不可用和「—」，CGU 相依查找回 503 + Retry-After 60。其餘五校及選校入口繼續使用。

既有 API fixture 改為明確注入 `create_cgu_catalogue`，資料與斷言不變；不以測試中的成功冒充 live。NTU 任務負責的原 13 個 live 來源依賴測試修復與 PR #9 原文缺件仍單獨追蹤。

## 第一個實作檢查點（完整整合驗收尚在進行）

- 初輪來源/API/快取/學生 dashboard：46 passed。
- 新來源測試補強必要欄位 schema 與 zero/missing/pending 保留，結果將在最終證據記錄。
- 手機390與桌面1440，錄製来源故障/恢復 browser：4 passed。最初2 failed為測試使用不存在函式，其後1 failed為未展開手機卡片；均已修正测试操作並保留原始 logs。
- 單獨真实公開來源 GET：兩份200，77列，2026-10-11 10:31:30 UTC；與備援 records hash 相同。此為 live 擷取，與上述 fixture 測試分開。
- OpenAPI snapshot、JS syntax、git diff --check 通過。
- 全量 unit/integration suite、六校瀏覽器、512 MiB單worker：本檢查點尚未完成。不得把此檢查點當成上線驗收。

## 固定資料候選及交集

| PR | 固定 SHA | 審查重點／狀態 |
|---|---|---|
| #8 | 9927ec1d8765a9772671bbaa68e7f920995f1258 | 本分支基底；共用視覺身份匹配／六校地球回歸保留 |
| #9 NTU | 4566f7f2b51b3b5c188f5394a56d7b5df190d1c5 | 無 api.py 改動；共用位置檔 ENS Ulm 與 #8 的母校點分別合併。60來源原文交付缺件未解，等待修正固定 SHA |
| #10 CCU | c18aebfceeedf8fceba5e4b24bbdf9dbebf0af18 | 照片／coverage／三處位置投影，需保留共用 matcher 與本機 operator 判定；部分補完 |
| #11 NCU | 5a3b690bff21e28ca85b438d285deb9236e706b9 | 照片／位置／JS sidecar 與共用 hunk 整合；部分補完，仍為 agreement_only，不升級為116當期資料 |
| TKU | 尚待本輪完成固定 SHA | 不重做收集者工作、不宣稱完成 |

## 發布與回滾邊界

本輪 CGU 修复以及上述 #9/#10/#11 相對 main 的 migration 變更為 0。新增來源狀態是 API additive 欄位；舊程式可忽略 runtime source_cache，舊前端可忽略此欄。回滾候選程式不需刪除 DB 或來源證據。

後續父對話決定正式順序前，必須先核對當時 main、每PR固定head、正式DB已套用migration清單與備份／還原證據。Render main commit 自動部署已開啟，而 Supabase Actions 受帳務阻擋，不能假設 main push 會同步 DB。若未來批次帶migration，應先完成隔離升級／舊程式相容性驗證，再依父對話批准執行「可前向相容DB -> 程式 -> 真實健康與功能驗收」；破壞性資料變更另需精確批准。程式退版與DB還原必須分別規劃，不自動下 destructive down migration。此分支沒有執行任何上述正式步驟。

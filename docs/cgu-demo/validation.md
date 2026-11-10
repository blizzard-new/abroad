# 驗證紀錄

2026-11-11（Asia/Taipei）。展示測試及回歸全部使用 `/tmp` 隔離資料，不使用正式資料庫。開始基準為 18622eec；建立 PR 前另整合最新 main，最終結果將在此更新。

## 首輪結果（18622eec + 展示變更）

- 展示 API／隔離／內容：6 項；Chromium E2E：12 項，合計 **18 passed**，30.51 秒。
- 正式相關回歸：**93 passed / 3 failed**，100.75 秒。
- 將原基準 Python 程式及失敗測試從 Git 取到獨立 `/tmp/uniway-cgu-baseline`，使用雜湊確認與原基準相同的唯讀資產，再跑三項失敗：**同樣 3 failed**，43.48 秒，並非本次新增失敗。
- `uv lock --check`、Python compileall、新舊主要 JS 語法、shell 語法、`git diff --check` 通過。專案未設定獨立 lint／靜態型別檢查器，不能稱作完成額外 typecheck。
- 既有 OpenAPI frozen contract 檢查通過；沒有變更正式路由。
- `uv build --wheel` 成功；2,372,205,824 bytes。抽取 wheel 的必要 Python 與資料／資產，在來源目錄之外啟動並驗證全部展示資產，通過。完整 Docker image／遠端部署未執行。

首輪三個既有問題：合作校 refresh 預期 76 卻得到 77；支援校數預期 18 卻得到 60；前端契約仍找無參數 `clearAuthenticatedClientState()`，實作已接受選項參數。沒有擴大修改正式行為或忽略／跳過這些失敗。

原始證據見 `evidence/`；截圖僅含虛構情境。完整建置 log 因包含大量既有學校資產清單未提交，保留摘要與 essential-files 一致性結果。

## 覆蓋範圍

搜尋空結果、快照遺失／竄改、缺來源、內容服務 503 與重試、損壞的本機資料、儲存被封鎖、固定情境／空白計畫、研究目標選擇、所有六階段勾選／反勾、下一步、個人日期、跨頁與重新整理、完成所有待辦後的狀態、可取消重設、正式 key 不受影響、多分頁衝突、非 Lincoln 目的校要求待確認、Cookie 忽略、正式帳號／文件／API 靜態路由不可用、noindex／CSP 等標頭。

Chromium 尺寸：1440×1000、820×1180、390×844、320×720，測試沒有水平溢位；Enter／Space 操作選校及待辦，對話框預設取消且 Escape 可返回。瀏覽器收集 pageerror，通過案例均無執行錯誤。瀏覽器主線請求只含同站 GET，沒有寫入端點。外部官方連結以新分頁開啟；實際來源失敗與限制另見 sources.md。

未跑 Firefox／WebKit、真實 iPhone、完整主站全量 suite、真實雲端／資料庫／校方 API、DNS／HTTPS 或端到端遠端 CI。沒有聲稱這些項目通過；私密資料整合不在展示範圍。

## 截圖

- [桌面探索與來源](evidence/desktop-explore.png)
- [桌面下一步與校內待辦](evidence/desktop-journey.png)
- [手機旅程](evidence/mobile-journey.png)

測試預設將截圖放 `/tmp/uniway-cgu-demo-evidence`，不改 tracked 截圖。需要更新交付截圖時，明確指定 `CGU_DEMO_EVIDENCE_DIR`。

# SEO 第二階段驗收與交付

依「SEO科普解說」最新建議，分成品質政策、內容入口、成效監控三個相依 PR。這份紀錄描述開發環境驗收，**不代表第二階段已部署或 Google 曝光已增加**。

## 已驗證

- 113 個相異的 SEO、品質、內容、報表、隱私、self-host 與既有 analytics 單元／整合測試通過。
- 13 個 Chromium 測試通過，包含手機與桌面免 JavaScript 導覽、GA4 未同意不載入／同意後事件去識別／撤回停止／GPC、既有第一方統計與 opt-out。
- 全部 3,540 個合作校群組完成模板渲染；本地完整 HTTP 檢查 3,569 個 HTML 頁面、19 份子 sitemap、共 3,590 個請求全部通過。新增九個編輯頁列入 sitemap。
- 最後快取調整後再跑代表頁驗收：47 個 HTML 頁面、19 份子 sitemap、共 68 個請求通過。完整／抽查證據見 `seo-enhancement-http-2026-10-19.json`。
- 全資料品質稽核 A 53、B 2,835、C 652；索引決策未變，沒有自動把 C 級取消索引。
- 序列化優化後，逐一比對全部 3,542 筆方案資料的新舊內容雜湊一致，避免效能調整誤觸發 lastmod。
- JavaScript 語法、Python 編譯與 Git whitespace 檢查通過。Google API 請求契約以替身驗證，瀏覽器測試攔截 Google 請求，不送測試資料給 Google。

一次既有瀏覽器測試因等待整頁 networkidle 逾時，改為等待此測試實際關注的 analytics 啟用狀態，再完整驗證上述 13 項；沒有放寬隱私或功能斷言。隱私頁新增官方 Google privacy 連結，原測試的允許清單同步加入該精確網址。

## 效能觀測與限制

本地手機寬度 390px 的四頁樣本均無水平溢出，公開 SEO 頁在 GA4 關閉時 JavaScript 載入量為 0。觀測 TTFB 約為總覽 3 ms、北大頁 46 ms、預算指南 2 ms、日本專區 2,583 ms；日本專區需要彙整多校，快取過期時仍較慢。初次與完整抓取並行時曾觀察到約 6.2 秒冷載入，因此不能宣稱所有頁面已達 Core Web Vitals 良好門檻。

已將合作校分組快取、來源雜湊的序列化縮小到會影響公開內容的欄位，並拆開各母校的快取鎖；保留正式站原有記憶體保護 semaphore。實際 LCP／INP／CLS p75 仍需正式流量及 Google 報表。樣本見 `seo-enhancement-performance-2026-10-19.json`，不是 Windows 主機或受限行動網路的測量。

## 上線與外部驗收

1. 依序審查、合併品質 → 內容 → 監控 PR。後兩張以先前分支為 base；前一張合併後，確認下一張 base 與 diff，再合併到 main。
2. Windows 主機更新到核准版本，依 `seo-launch.md` 備份 image、僅重建並重啟 app。新增 `uniway_seo_state` volume，沒有業務資料庫 migration，不刪除舊資料 volume。
3. 保持 GA4 關閉；使用者已確認尚未設定資源。依 `seo-analytics-monitoring.md` 完成 GA4 串流、隱私設定與 ID 後才啟用。
4. 執行 `scripts/seo_smoke.ps1` 或 Python checker，確認新增頁面已上線及 canonical 正確。這個環境沒有 PowerShell／正式 Windows 主機，PS 包裝腳本未在實際主機執行。
5. 原 sitemap 主索引 URL 不變，不需逐頁重新提交。確認子 sitemap、抽查網址即時測試，再接通唯讀 Google API 取得第一份真實基準。
6. 有有效憑證後安排每週收集／報表；本次沒有建立 Google 資源、持有 OAuth 憑證、修改 Google 後台或啟動無人值守排程。校園合作與學生心得仍需真實素材、授權及回覆。

GitHub 既有 Web quality workflow 仍為停用；本次未啟用，不能把本地測試標成遠端 CI 通過。正式主機與 Google 後台驗收完成前，整體 SEO 第二階段維持待上線／待接通狀態。

# UniWay 索引問題診斷（2026-11-01，臺灣時間）

## 範圍與限制

本次診斷工作樹基準為 `bd647426c727dbc0d0db562fca499d359746eb2d`；建立 PR 時改以 `37ae0344bb5dc0dfa13821479eb061fc385cbe27` 為基礎，其間變更位於 marketing 工具與其 workflow。尚未確認 KEVINSERVER 實際部署的 commit。工作樹及其上層未找到 `AGENTS.md`；已閱讀自架部署指南、SEO 上線與品質政策及相關實作。未取得正式主機的 Caddy／app 歷史日誌或 Search Console 直接存取權，不能斷定 Google 當時所見的每筆 5xx 都由同一例外造成。

使用者提供的 Search Console 匯出包含：5xx 28 筆、404 28 筆，以及「已檢索尚未索引」與「已找到尚未索引」各 1,000 筆。後兩份是匯出樣本，不是截圖所示 1,592／3,301 筆的完整清單。「已找到」檔案的日期欄顯示 1970-01-01；本次不將它視為有效的實際檢索日期。替代頁與 robots 封鎖的分類匯出仍未提供。

## 正式站低頻唯讀樣本

請求序列間隔至少 5 秒；三個跨校 500 連續出現後停止該序列。以下是檢查當時的結果，不是部署後驗證。

| 路由或模板 | HTTP／轉址 | canonical、robots、sitemap 與正文觀察 |
| --- | --- | --- |
| `/robots.txt` | 200，無轉址 | 公開 sitemap；封鎖 `/account/`、`/auth/`、`/admin/`、`/calendar/`。這些規則不是存取控制。 |
| `/sitemap.xml` | 200，無轉址 | 37 個子檔，不含既有 `/sitemaps/partners.xml`。 |
| `/sitemaps/pages.xml` | 200，無轉址 | 72 個位置。 |
| `/sitemaps/partners.xml` | 200，無轉址 | 2,597 個位置，包含 `seinan-gakuin-university` 的正式網址，但未被主 sitemap 列出。 |
| `/` | 200，無轉址 | canonical 為首頁、robots 允許索引；HTML 的 main 約 7,815 字元，樣本中有 13 個站內連結。 |
| `/schools` | 200，無轉址 | canonical 為該網址、robots 允許索引；main 約 13,941 字元，有 40 個站內連結。 |
| `/schools/ntnu` | 200，無轉址 | canonical 為該網址、robots 允許索引；main 約 11,185 字元，有 241 個站內連結。 |
| `/guides/exchange-eligibility` | 200，無轉址 | canonical 為該網址、robots 允許索引；main 約 3,055 字元，有 9 個站內連結。 |
| `/schools/not-a-real-school` | 404，無轉址 | `X-Robots-Tag: noindex, nofollow`；未知校別維持真正的 404。 |
| `/partners/japan/seinan-gakuin-university` | 500，無轉址 | 未取得正常頁面的 canonical、robots meta 或正文。 |
| `/partners/mainland-china/f13ea68d8f4c4c65ddea?home=fju` | 500，無轉址 | 同上。 |
| `/partners/japan/becfe590d7f465bef247?home=ntou` | 500，無轉址 | 同上。 |
| `/partners/thailand/inst-03aafe3344e6?home=nccu` | 404，無轉址 | 舊跨校識別網址；目前正式站尚未套用本次修正。 |
| `/partners/mainland-china/inst-5e7ac3f58de1?home=ncue` | 404，無轉址 | 同上。 |

站內連結數只說明樣本 HTML 內有連結，沒有逐一證明連結有效；正式站沒有進行全站爬取。

## 已重現缺陷與修正

1. **跨校頁 500：名額欄位驗證範圍不一致。** 本機以同一份 28 個 5xx 匯出網址測試，修改前 24 筆拋出 `PartnerPreferenceHeatItem.quota_hint` 驗證錯誤：11 筆是單字元名額、13 筆超過 300 字；另 4 筆在目前程式與隔離資料下已回 200。上游 `CrossSchoolHomeAgreement.quota_summary` 允許 1–400 字，下游原只允許 2–300 字；頁面建構與各母校切換資料都可能觸發。現在下游接受相同範圍並保留原文，沒有以 200 包裝例外。OpenAPI 快照同步反映這個回應欄位範圍的擴充。修改後 28 筆本機均回 200 並有正文；正式站根因仍待日誌確認。
2. **28 個舊網址 404：兩個舊雜湊識別失效。** 舊版程式以合作校識別雜湊前 12 位產生 `inst-...`；目前資料中分別可唯一對應 `burapha-university`（20 筆）及 `china-university-of-political-science-and-law`（8 筆）。本機已核對全部 28 筆：301 到相應頁面、保留 `home`，目標回 200 並宣告不含參數的 canonical。只有目前資料能唯一確認等價機構時才轉址；不存在或有碰撞時保留 404，不導向首頁。
3. **少數正式 canonical 被另一學校別名覆蓋。** 本機索引檢查出 7 個此類衝突，例如 `/partners/france/ece` 被別名表指到 `ece-3`。現在精確的現有正式 slug 優先於別名解析；合理的 `?home=`／舊名稱 canonical 合併保留，沒有對全部頁面強制 self-canonical。
4. **跨校 sitemap 未被主 sitemap 引用。** 主索引現在包含既有 `/sitemaps/partners.xml`。本機該子檔含 2,597 個無重複的正式網址；抽查 57 個（含上述 7 個衝突位置）均回 200、具有對應 canonical 與伺服器正文。此修正改善發現途徑，但不能推定它是 Google 尚未索引的原因，也未逐一驗證全部 2,597 頁。
5. **跨校資料來源失敗被忽略。** 原本彙整器會跳過失敗的母校來源，可能以不完整資料回 200 或錯誤判斷舊網址。公開跨校頁及其 sitemap 現要求來源完整；來源回 503 時保留 503／Retry-After，而不是產生不完整的成功頁或錯誤轉址。這代表任一必要校庫暫時不可用時，跨校聚合頁會暫時不可用；其他既有 API 的部分資料行為未因此改變。

未修改正式站 robots 規則、私人頁 noindex、權限控制或 lastmod 計算；沒有填充虛構內容。

## 未索引與內容樣本

「已檢索尚未索引」1,000 筆匯出中，661 筆是無參數 `/schools/...`，223 筆是含參數 `/partners/...`，101 筆是不含參數 `/partners/...`，12 筆是含參數首頁，其餘 3 筆為其他公開路由。`?home=` 與首頁查詢參數樣本在本機指向乾淨 canonical；它們可能是合理替代頁，不能直接當錯誤修正。

「已找到尚未索引」1,000 筆匯出中，589 筆是 `/schools/...`，408 筆是 `/partners/...`，另有 2 筆指南及 1 筆目的地頁。本機依不同路由及參數模板抽查「已檢索」22 筆與「已找到」9 筆，均回 200 並有 canonical；這不能代表全部網址內容品質或 Google 的索引決定。跨校目錄有顯示數量上限，但母校合作校頁也有跨校連結；尚未完成全站孤立頁與重複內容稽核。

## 驗證結果

- 相關單元與整合測試：原診斷基準 126 passed。第一次執行發現既有測試把支援校數固定為 22，已改為核對實際登錄表後重跑；PR 基礎更新後再執行相關代表測試，15 passed。
- Chromium SEO E2E：5 passed，涵蓋有／無 JavaScript 的代表性頁面。
- 本機 HTTP SEO smoke：38 個子 sitemap、109 個 HTML 頁，149 次請求，通過；不是正式站驗收或 Google 收錄證據。
- 5xx 匯出 28 筆本機重測均回 200；404 匯出 28 筆本機重測均為 301，目標均回 200、canonical 相符。
- OpenAPI snapshot 檢查與 `git diff --check` 通過。
- 容器建置兩次均完成約 2 GB 的 Python wheel 建置、套件安裝及 TLS 檢查，但本工作環境 32 GB 檔案系統在建立後續 Docker 映像層時耗盡，完整映像建置未通過。第二次使用了僅供測試的合併步驟及暫時 CA 掛載；兩次都沒有部署。需在 KEVINSERVER 的適當建置環境重新驗證原始 Dockerfile。

## 待取得與人工部署／回滾方案

請提供 KEVINSERVER 對應檢索時間的 Caddy access log 與 app stack trace（先移除 IP、Cookie、帳號等敏感資料），以及 robots 封鎖和替代頁 canonical 分類匯出。對照 URL、狀態與時間後，才能判斷歷史 5xx、404、封鎖與 canonical 各自的剩餘原因。正式主機的資料來源完整性、實際部署版本與 Google 重新檢索結果均未驗證。

由操作者審查通過後，先在 KEVINSERVER 確認工作樹、目標 commit、目前 `uniway-app:local` image ID、備份和可用磁碟空間。這組修改沒有資料庫 migration；依 `docs/seo-launch.md` 僅備份現有 app image、建置並以 `--no-deps` 重啟 app，避免使用會套用全部 migration 的一般更新腳本。部署後低頻檢查 `/health`、登入與私人頁、兩個舊網址及目標頁、上述 5xx 代表頁、robots 和 sitemap，再視站況以較長間隔執行 SEO smoke。任何檢查失敗即停止並調查日誌。

回滾時將事先保留的舊 app image 重新標記為 `uniway-app:local`，以 `docker compose ... up -d --no-deps --no-build app` 重啟，並還原部署時若有變動的 SEO 設定；保留 `uniway_seo_state` 與業務資料。以上均為人工執行方案，本次沒有部署、合併、變更正式環境、提交 Search Console 驗證或要求索引；不保證 Google 的收錄時間。

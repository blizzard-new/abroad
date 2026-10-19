# SEO 第二階段：搜尋、轉換與效能驗收

## 已交付與尚待接通

程式已提供可啟用的 GA4、唯讀 Search Console／GA4 API 收集器、每週報表、Google 索引診斷、部署 smoke test 與效能量測。使用者確認尚未設定 GA4，因此 **GA4 預設關閉**；此環境沒有 Google OAuth 憑證，沒有讀取真實 Google 後台資料，也沒有建立資源、要求索引或設定無人值守排程。缺少資料時報表填「尚無資料」／null，不填零。

## GA4 一次性設定

1. 在 Google Analytics 建立 GA4 資源，時區選 Asia/Taipei，建立網址為 `https://app.uniway-tw.com` 的 Web 資料串流。記下公開 Measurement ID（`G-...`）與資源數字 ID，兩者不同。
2. **關閉串流所有 Enhanced measurement（加強型評估）**，包含自動網頁歷史事件、站內搜尋、表單與外連；由本站明確定義的事件傳送資料。關閉 Google signals、廣告個人化與廣告資料分享；事件層級資料保留設為 **2 個月**，與新版隱私說明一致。GA 彙總報表不受此保留期限制。
3. 將 `GA4_MEASUREMENT_ID=G-你的ID` 與 `GA4_ENABLED=true` 寫入正式主機 `deploy/selfhost/.env`，只重建／重啟 app。尚未完成前保留 `GA4_ENABLED=false`。一般部署對應 `EXCHANGE_GA4_MEASUREMENT_ID`／`EXCHANGE_GA4_ENABLED`。
4. 在測試瀏覽器檢查：未同意前沒有 Google 請求；同意後只有公開路徑與下列允許事件；撤回、DNT、GPC、既有匿名統計停用時停止。使用 GA4 即時報表確認，不把未接通的測試算成真實成效。
5. GA4 與 Search Console 可在 Google 後台設定產品連結。將 `open_school_planner` 與 `compare_universities` 視營運需求標為關鍵事件；不要將所有瀏覽都視為轉換。

| 事件 | 發送時機 | 允許資料 |
| --- | --- | --- |
| `open_school_planner` | 公開頁點選返回選校／學校工具 | 公開路徑、頁面類別 |
| `compare_universities` | 成功把第二或第三所學校加入比較 | 學校數量 2–3，不含名稱或帳號 |
| `click_official_source` | 點選標記的官方資料連結 | 官方網域，不含完整網址或文字 |
| `view_application_guide` | 同意後讀取一篇申請指南 | 公開指南路徑 |
| `web_vitals` | Google 維護的 web-vitals 完成指標 | LCP／INP／CLS 名稱與值 |

訪客另外選擇同意後才載入 gtag。Cookie 與同意設定期限 180 天；可在公開頁頁尾撤回。資料不含帳號、文件、表單內容、原始查詢字串、hash 或完整來源網址。GA4 仍由 Google 處理連線資訊，公開說明已更新，不能稱為完全匿名或沿用第一方 30 天保留期。CSP 只在明確啟用且 ID 合法時允許 Google script/connect origins，沒有開放 inline script。

新版條款／隱私版本為 2026-10-19，登入同意文字版本同步。正式啟用前需依上述步驟核對 GA 後台設定；單靠前端 `send_page_view: false` 不能取代關閉加強型評估。

## 收錄診斷與每週搜尋報表

收集器需要有該 Search Console 資源讀取權限的 Google OAuth access token，scope 為 `https://www.googleapis.com/auth/webmasters.readonly`；可選 GA4 報表還需 `https://www.googleapis.com/auth/analytics.readonly`、Analytics Data API 與該 GA4 資源讀取權限。使用自己的授權工具取得短效 token，放在執行環境的 `UNIWAY_GOOGLE_ACCESS_TOKEN`，不要寫入程式、Notion、PR 或命令列參數。

```powershell
python scripts/audit_seo.py --output artifacts/seo-quality.json
python scripts/seo_search_console.py --audit artifacts/seo-quality.json --max-inspections 30 --output artifacts/search-console.json
python scripts/seo_report.py --search-console artifacts/search-console.json --audit artifacts/seo-quality.json --output artifacts/seo-weekly.json
```

如已啟用 GA4，在收集器加 `--ga4-property 你的數字資源ID`，取得臺灣 Organic Search 的四個轉換事件次數與使用者數。Google 存取權未配置時命令會清楚失敗，不產生假的成功報表。純本地樣板可直接執行 `seo_report.py --output artifacts/seo-weekly.json`，缺少的欄位會保留未知。

Search Console 使用 Web／臺灣／final data，比較兩個完整 28 天期間；預設截止日為三天前，可用 `--end YYYY-MM-DD` 指定。Google Search Console 以太平洋時區計日，GA4 依資源時區，禁止直接用 GSC 點擊當 GA 轉換率的分母。曝光總數來自無 query 維度的總計，不從可能漏掉匿名查詢的明細加總。非品牌統計僅是回傳查詢中的已觀測數，會標明截斷與匿名查詢限制。

索引樣本先覆蓋母校，再補 A／B／C，預設最多 30 個、上限 100。收集的是 Google **已儲存的索引版本**，不是即時抓取測試。報告保留 coverage、last crawl、Google/user canonical、robots、noindex 與抓取原因；A 級樣本通過率不能冒充全部高品質頁面的收錄率。會另外讀取主 sitemap 的子檔狀態，確認 19 份子 sitemap 的處理情況。

每週先看「抓取錯誤與索引原因 → 已觀測查詢與頁面 → Google 流量的功能使用」，再決定補內容或調整標題。搜尋量、排名和改善幅度沒有實際資料就不推測。排程時應由主機安全提供有效短效 token；本次未存放 refresh token，也未啟用必然失敗的背景排程。

## 效能與自架主機

第一方匿名統計沿用既有 `/admin/analytics` 與隱私選項，改用本地 vendored `web-vitals@4.2.4` 計算 CLS session windows、INP interaction 等規則；GA4 同意後也使用同一版本。LCP ≤ 2500 ms、INP ≤ 200 ms、CLS ≤ 0.1 以實際使用者的 p75 判斷，樣本不足時不能判定正式站達標。官方套件不會主動上傳資料，事件仍走原有收集器或另行同意的 GA4。

合作校分組現在與來源快照一起快取，避免每個頁面重複計算全校的合作校 ID；仍每分鐘重新檢查來源與時效狀態。快取鎖按母校分開，但保留主 app 為限制來源展開記憶體用量而設的單一 catalogue semaphore，因此冷快取請求仍可能排隊；沒有為追求速度取消既有資源限制。公開內容使用完整 HTML 和輕量 CSS，沒有新增首屏圖片、框架或強制第三方追蹤下載。

部署後在 Windows 專案根目錄執行（主機 Python 需已安裝專案依賴）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/seo_smoke.ps1
python scripts/check_seo.py --base-url https://app.uniway-tw.com --json-output artifacts/seo-smoke.json
python scripts/check_seo_performance.py --base-url https://app.uniway-tw.com --output artifacts/seo-mobile-lab.json
```

smoke 腳本唯讀檢查 app health、重啟次數與全部 sitemap／代表 HTML，失敗會回非零；不重啟容器、不跑 migration。效能腳本需要 Playwright Chromium，可用 `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` 指定既有瀏覽器；輸出手機寬度、TTFB、正文大小、JS 大小與水平溢出，是單次實驗室樣本，不宣稱正式站 p75 或 INP。

若 Caddy 已啟用 JSON access log，可把檔案交給 `seo_report.py --access-log 路徑`，彙整 Googlebot User-Agent 的 5xx 與回應耗時，不輸出 IP 或原始網址。User-Agent 可偽造，因此不宣稱已驗證 Googlebot 身分；回應耗時不是 TTFB。主機重啟異常、5xx 增加或 Google 明確報錯時，再檢查容器與 Caddy 原始紀錄。

## 套件來源

`static/vendor/web-vitals/4.2.4/` 來自 npm `web-vitals@4.2.4`，保留 Apache-2.0 LICENSE。JS SHA-256：`4b476648ce848748b2f3b43b9ead830449e6e688c3fa10637e8a7dd8acbc9e05`。瀏覽器從本站載入，不從 CDN 取得執行碼。

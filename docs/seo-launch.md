# UniWay SEO 上線與驗收

來源：[UniWay 2026–2027 規畫](https://app.notion.com/p/3fd068869d8f81319890c5dc2bc5ff4f)。本次涵蓋兩項 SEO 任務：母校／合作校獨立網址，以及 sitemap、robots、標題描述與 Search Console 提交準備。

2026-10-19 正式站唯讀基線：首頁 200、缺 description/canonical；`/robots.txt`、`/sitemap.xml`、`/schools` 均 404。使用者已確認 `app.uniway-tw.com` 的 Google Search Console 驗證完成。本 PR 不代表正式站已更新或 Google 已收錄。

本地測試與完整網址檢查結果見 [驗收紀錄](seo-validation-2026-10-19.md)。

## 網址與內容

| 網址 | 用途 |
| --- | --- |
| `/` | 既有互動首頁，補標題、描述、canonical、社群分享 metadata、WebSite 結構化資料與免 JavaScript 入口 |
| `/schools` | 所有支援母校的公開目錄 |
| `/schools/{home_id}` | 母校交換指南與合作校連結 |
| `/schools/{home_id}/partners/{key}` | 該母校適用的合作校與各方案條件、資料狀態、官方來源 |
| `/sitemap.xml` | Sitemap index，列出基本頁、跨校合作大學與每所母校的 sitemap |
| `/sitemaps/pages.xml` | 首頁、目錄及母校頁 |
| `/sitemaps/partners.xml` | 跨校合作大學的正式 canonical 網址 |
| `/sitemaps/{home_id}.xml` | 該母校的合作校網址 |

所有頁面直接回傳完整 HTML，沒有爬蟲專用內容，不需要登入或 JavaScript。新頁使用既有校庫，不重新推論資格、不發布治理流程中的草稿，也不更動原有 `#school=` 分享與申請工作台。CTA 帶上原有 `?home=母校#school=合作校`，確保回到正確母校。

合作校 ID 由「國家＋既有 institution identity」產生，與名額、年度、列表順序無關。同一母校下相同 institution 的不同方案在同頁逐筆展示；不同母校各有自己的頁面。**修改學校識別名稱或國家會改變網址**：未來此類資料更名須保留舊 ID 到新網址的 301 對照，不能僅換名稱後刪除舊 URL。

舊跨校 `inst-` 雜湊網址若能從目前合作校資料唯一辨認原機構，會以 301 轉到對應的跨校正式網址，並保留 `home` 母校參數；找不到或有多個可能對象時維持 404。跨校彙整所需的校庫資料不可用時，公開頁與該 sitemap 回傳來源錯誤，不以不完整結果假裝成功。

本期、參考、協議、零名額與待確認狀態分開顯示。來源的 `checked_at` 是查核時間，不用來虛構 sitemap `lastmod`；僅有可信的實質內容修改紀錄時才輸出，詳見 [品質政策](seo-quality-policy.md)。CGU 擷取時間不代表本期已驗證。資料來源不可用回 503／Retry-After，未知校別與 ID 回真正 404，皆 noindex。校庫請求共用既有併發限制，並使用最多每所母校一份、有效一分鐘的公開資料快取，避免每個合作校頁面都重新解析資料。HTML 瀏覽器快取一分鐘，sitemap 五分鐘。

## 部署設定

沿用 `EXCHANGE_PUBLIC_BASE_URL=https://app.uniway-tw.com`，canonical 不取使用者可偽造的 Host／Forwarded header。正式 Compose 由既有 `DOMAIN` 傳入此值。

- `EXCHANGE_SEO_INDEXABLE`：正式站 `true`，預覽／測試站務必 `false`。非 production 預設 noindex；正式 Compose 預設 true。
- `GOOGLE_SITE_VERIFICATION`（Compose）／`EXCHANGE_GOOGLE_SITE_VERIFICATION`（程式）：可選 HTML 驗證 token，只輸出在首頁。已透過 DNS 或其他方式驗證者不必改動既有驗證。不可填 Google 密碼或 OAuth token。
- API、帳戶、後台、靜態 HTML 與錯誤回應會有 `X-Robots-Tag: noindex, nofollow`；robots 阻止帳戶、登入、後台與私人日曆路徑。這不是存取控制，既有驗證仍照常運作。
- Sitemap 只包含公開 HTML 頁，無個人頁、登入網址、搜尋條件組合、hash 網址、私人日曆或測試站網址。

## 正式上線步驟

1. 檢查 PR 與 CI 結果，合併後記下核准的 commit SHA。在 Windows 自架主機檢查工作樹乾淨，備份現況，取得該 SHA。
2. 此變更**沒有資料庫 migration**。沿用現有環境，只重建並重啟 `app` 服務；不要為 SEO 使用會套用全部 migrations 的通用 `update.ps1`。從專案根目錄執行：

   ```powershell
   docker image tag uniway-app:local uniway-app:prev
   docker compose --env-file deploy/selfhost/.env -f deploy/selfhost/docker-compose.yml build app
   docker compose --env-file deploy/selfhost/.env -f deploy/selfhost/docker-compose.yml up -d --no-deps app
   ```

   先確認現有 image `uniway-app:local` 存在，並保存舊 commit／image ID；任何指令失敗都應停止，不繼續部署。`--no-deps` 保持資料庫、Storage 與 gateway 服務不變。這些命令須在實際自架主機執行，本次雲端開發環境不是正式主機。
3. 檢查 `/health`、原有登入／選校入口，以及下方 SEO 驗收。若失敗，用保留的舊 image 重新標記為 `uniway-app:local`，再 `up -d --no-deps --no-build app`；若改過 SEO 環境設定一併還原。
4. SEO HTTP 驗收通過後才提交 Search Console。保留部署 SHA、執行日期、驗收輸出及提交成功畫面／紀錄。

## HTTP 驗收

在已安裝本專案依賴的環境：

```powershell
python scripts/check_seo.py --base-url https://app.uniway-tw.com
```

這會依序驗證 robots、主 sitemap 列出的各個子 sitemap、所有基本頁及各子 sitemap 的代表頁。檢查 200、XML、canonical、可索引設定、metadata、伺服器正文及結構化資料。它不連 Google 帳號、不提交網址、不證明已收錄。子 sitemap 數量以 registry 實際校數為準，不把數字硬編碼到程式。

檢查另外涵蓋兩項：`/llms.txt` 回 `text/plain`、以 `# UniWay` 開頭，且每個連結都在 `/sitemaps/pages.xml` 內（`/sitemap.xml` 除外）；首頁 JSON-LD 同時含 `Organization` 與 `WebSite`。robots 只用 `User-agent: *` 群組判斷是否封鎖全站，所以 `EXCHANGE_AI_CRAWLERS=search-only` 時訓練爬蟲群組的 `Disallow: /` 不會被誤判。

隔離環境的完整網址檢查可用 `--all-pages --delay 0`；正式站保持預設間隔，避免旺季造成負擔。`--base-url` 可指向本機，canonical 仍用正式站；本機僅為測試時可暫設 `EXCHANGE_SEO_INDEXABLE=true`，不要公開暴露此測試服務。

## AI 搜尋：`/llms.txt` 與爬蟲政策

- `/llms.txt` 由同一份校庫、指南與國家資料動態產生，列出首頁、校級目錄、各指南、各國家專區與每所母校頁，不列數千個合作校頁（那些在 sitemap）。檔頭註明合作關係不等於當期開放、擷取時間不等於查核時間，請助理原樣轉述狀態。非可索引環境（預覽、測試）回 404，不對外宣告。
- `robots.txt` 明列 AI 搜尋與訓練爬蟲，預設全部允許、私人路徑照舊封鎖；`EXCHANGE_AI_CRAWLERS=search-only` 可只關訓練爬蟲。詳見 [claude-seo 使用手冊](claude-seo-playbook.md)。
- 首頁結構化資料改為 `@graph`：`Organization`（含官方 Instagram、Threads 連結）與 `WebSite`（`publisher` 指向前者）；指南 `Article` 的 `publisher` 以同一個 `@id` 對應。
- 上線後用 `/seo drift compare`（見使用手冊）確認只有這些預期差異。

## Google Search Console：已驗證後的最後一步

1. 開啟 [Search Console sitemap 管理](https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fapp.uniway-tw.com%2F)，選擇已驗證的 `https://app.uniway-tw.com/` URL-prefix 資源，或涵蓋此子網域的 `uniway-tw.com` Domain 資源。
2. 在「新增 Sitemap」輸入 **`https://app.uniway-tw.com/sitemap.xml`** 並提交；若介面已固定網址前綴，只填 `sitemap.xml`。不需逐一提交 18 份合作校 sitemap。
3. 確認 Sitemap 狀態成功；若顯示「無法擷取」，先跑 HTTP 驗收並檢查 DNS／TLS／Caddy，勿將失敗狀態標為完成。
4. 用「網址審查 → 測試實際網址」抽查 `/`、`/schools`、`/schools/ntpu` 及其一個合作校頁，核對可檢索、使用者宣告 canonical 與正文。可對少數代表頁要求建立索引，無需逐頁手動提交。
5. 數天後查看「網頁索引」與「成效」；Google 可以延後或不收錄部分頁面，成功提交不是排名或曝光保證。

目前此工作環境沒有已登入的 Search Console 瀏覽器／API 連線，也沒有 Windows 自架主機操作通道。因此以上兩個外部步驟須有實際執行結果後才勾選；不要在 Notion 把整項 SEO 任務提前標為完成。

## 曝光追蹤與後續內容

優先查詢意圖：`母校名稱＋交換學生`、`母校名稱＋交換申請`、`母校名稱＋合作校名稱＋交換`。既有來源支援的資格、名額及期限自然呈現在頁面中，沒有堆砌關鍵字或虛構當期名額。

每週在 Search Console 記錄同一範圍（搜尋類型 Web、國家臺灣）的曝光、點擊、CTR、平均排名與有效索引頁；比較最近完整 28 天與前 28 天，保留申請季變動背景。依頁面 `/schools/` 與查詢分組，觀察哪些學校曝光但點擊偏低，再調整描述或補齊有來源支持的內容。缺少原始數據時不填零、不假定 SEO 已有效。

指南、心得與學校合作推廣需持續產出，並保留原創內容與授權。本 PR 完成指定技術 SEO 範圍；不把未來數月的搜尋成效、外部反向連結或人工資料查核算作已完成。

# 自架主機容量：從單程序到千人驗證

2026-10-18 使用者提供的實機資訊：i9-12900K（16 核心／24 執行緒）、128 GB RAM、4 TB SSD；正式 Docker 為 8 CPU、約 23.47 GiB。五個服務健康，當時合計約用 1.04 GiB。這是低負載截圖，尚未證明高負載容量。聊天的雲端執行環境與這台 Windows 主機分開。

實測下載 518.77 Mbps、上傳 524.93 Mbps。先以網站整台伺服器上下行各 450 Mbps、朋友上下行各保留 50 Mbps 規劃；一次測速超出的部分視為浮動餘裕。最低保留頻寬需要路由器支援 QoS／頻寬保證，只有 Windows 的 Caddy 上傳限制無法約束備份、更新或下載。現有主機尚未套用本文件的改動。

## 1. 本次程式調整

- OAuth state、登入開始限流、登入紀錄與工作區原本就使用 PostgreSQL；OAuth 回呼可以跨程序完成，不必為此先加 Redis。`EXCHANGE_ENVIRONMENT=production` 仍強制共用持久層。
- 自架 Compose 設 `EXCHANGE_ACCOUNT_READ_CACHE_SECONDS=0`。各程序直接讀取同機資料庫，避免其他程序更新帳號、草稿或撤銷登入後仍沿用最多 20 秒的舊資料。雲端部署的預設值未調整。
- 登出透過 repository 的單筆 token 刪除操作撤銷目前登入。其他程序或裝置的登入不需要被整份讀取、重寫。
- AI 狀態重用開機取得的回應。可見且連線的頁面：AI 暫停每 5 分鐘查一次，運作中每 30 秒，請求失敗每 2 分鐘。隱藏或離線時停止排程；回來時加 0.5～2 秒抖動，且同一頁面最多一個請求進行中。
- 伺服器每個程序將 AI 來源數與索引摘要快取 5 秒；AI 是否暫停、啟用與執行狀態仍每次即時讀取。
- 統計每個程序只排一個背景刷新工作，避免到刷新時間時一批請求建立大量排隊執行緒。

統計事件的防濫用限流仍是**每程序**計算：增加到 4 個程序後，同一來源的總上限最多約為原先 4 倍。它不負責登入驗證。統計小時彙總透過既有 `exchange_analytics_add_api_hourly` RPC 原子累加，不必強制共用程序內的計數器。需要跨程序一致的統計收集限流時，再設共用限流服務；本次沒有建立 Redis 或資料庫 migration。

## 2. 先保留目前 8 CPU／24 GB

先比較 1、2、4 個網站程序，不必先調高 WSL 配額。工作程序會各自建立快取、暖機與連線；它們共用 8 CPU／24 GB，並非每程序獨占這些資源。只有觀察到 CPU 飽和、記憶體不足等證據，才調整實際瓶頸。

先在**使用獨立資料庫、儲存與測試帳號的 staging 安裝**操作。可依 [自架指南](self-host-windows-guide.md) 建立在另一台電腦或獨立 VM；不要讓測試安裝讀寫正式資料。不要在同一個正式 Compose 目錄另跑 `docker compose -p` 就當作隔離：目前 Compose 的磁碟區名稱是固定的，仍可能使用正式資料。

在 staging 的 `deploy\selfhost\.env` 設 `APP_WORKERS=1`，依原本更新流程建置這個版本，再從該目錄執行：

```powershell
docker compose up -d --build --no-deps app
docker compose ps
docker stats --no-stream
docker inspect uniway-app-1 --format '{{json .Config.Cmd}}'
```

先確認 Google 登入、登出、兩個裝置交替儲存／重新整理草稿與文件下載都正常。接著將 `APP_WORKERS` 改成 2，再到 4；每次套用與測試：

```powershell
docker compose up -d --no-deps app
docker compose ps
docker compose logs app --tail 50
```

這會重建網站容器，應安排測試或維護時段。不用停止、重建資料庫或刪除任何磁碟區。部署出問題時先將 `APP_WORKERS=1` 套回；程式版本回復依原指南的 `update.ps1 -Rollback`。

## 3. 從另一台電腦產生流量

使用 Python 3.11 以上。從原始碼目錄，建立專用環境並安裝本次測試使用的 HTTP 客戶端版本：

```powershell
py -3 -m venv .venv-load
.\.venv-load\Scripts\python.exe -m pip install httpx==0.28.1
.\.venv-load\Scripts\python.exe scripts/load_test_public.py --base-url https://STAGING_HOST --users 10 --duration 60 --ramp-seconds 10 --output capacity-1worker-10users.json
```

把 `STAGING_HOST` 換成自己的 staging 網址。接著逐一測試 100、300、500、1000 個模擬訪客；每個程序配置都保留各自報告，例如：

```powershell
.\.venv-load\Scripts\python.exe scripts/load_test_public.py --base-url https://STAGING_HOST --users 1000 --duration 300 --ramp-seconds 60 --think-seconds 10 --school 長庚大學 --school 國立臺灣大學 --school 國立中央大學 --output capacity-4workers-1000users.json
```

每位訪客先讀首頁、學校列表及 AI 狀態，再循環讀學校儀表板、文件與期限，停留 10 秒後繼續。1000 位訪客穩定進入後，這個情境理想上約每秒 300 次 API 請求，初次載入另外計算；實際結果取決於回應時間。慢回應會降低達成的吞吐量，報告中的模擬人數不能代替每秒請求量或回應時間。

報告包含實際啟動人數、每秒請求、錯誤／逾時、各路徑 p95、整體 p50／p95／p99 與回應內容位元組數。HTTP 不是 200 或內容類型錯誤都計為失敗；未達標以非零代碼結束。預設各路徑與整體 p95 都須不超過 2 秒、錯誤率不超過 1%。流量生成端也需監看 CPU、記憶體與網路，避免測到生成端的上限。

位元組數是 HTTP 客戶端解壓後的內容大小，不能直接當作 WAN 傳輸量。本次本機臺大儀表板回應約 4 MB（未壓縮），實際對外仍要量測 Caddy 壓縮、CDN 與首次進站的效果。

**這個工具只測公開 HTTP/API，沒有載入圖片、字型或 JavaScript，也沒有執行登入、私人草稿儲存、上傳、PDF 或真正瀏覽器操作。** 不應將 `passed=true` 對外宣稱為「1000 名學生已能完成申請」。每個程序組合先跑這個基準，才進入下一階段。

## 4. 完整容量驗收的剩餘項目

- 用不同的 staging 學生帳號做瀏覽、搜尋、收藏、登入、草稿讀寫的混合情境，至少維持 1 小時，再測 1500 人短暫尖峰。驗證內容與版本，不能只計算 HTTP 200；也要觀察是否有 409、登入失效、跨帳號資料或存檔遺失。
- 登入含外部 OAuth，不要用大量自動化登入打第三方服務。效能情境使用已建立的測試登入；OAuth 功能另行驗證。
- 圖片、CSS、JavaScript 使用 CDN 快取及版本化網址；公開資料的共用快取須明確區分學校、語系、版本與帳號相關結果。私人文件、帳號與草稿不進共用快取。
- PDF／Word 仍在網站請求的 threadpool 內產生。本次未做獨立文件佇列；大量同時產生文件需另外限量、隔離並測試，不能套用公開查詢容量。
- 監測 CPU、記憶體、磁碟延遲、資料庫慢查詢／連線池與 WAN 上傳。調整 PostgREST 連線池前，先量測查詢及連線等待，不要按 1000 人直接建立 1000 條資料庫連線。
- 路由器針對整台伺服器設上下行 450 Mbps；若支援最低保證，替朋友裝置保留上下行各 50 Mbps，並從外部網路驗證。`01-prepare-windows.ps1` 的新安裝預設 Caddy 上傳上限為 450 Mbps；既有主機不會自動更改，也不用為了改頻寬重跑整個初始化腳本。

## 驗證邊界

本次開發測試在獨立雲端環境執行，不等於使用者的 Windows 主機。單元測試涵蓋跨 repository 的撤銷可見性、單筆登出、來源摘要快取、輪詢生命週期、統計刷新排程與壓測工具的失敗判定。既有 OAuth 跨 app instance 案例一併回歸。未連到使用者主機、未變更路由器、未對正式網站壓測，也未在本次執行完整自架 Supabase 元件的整合壓測。

本次選定案例最後結果為 **209 passed**；1／4 程序的小流量 HTTP 啟動檢查與測試重現指令見 [驗證紀錄](self-host-capacity-validation/README.md)。

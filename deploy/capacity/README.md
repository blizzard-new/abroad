# 第二階段：隔離環境與混合操作壓測

此套件用真正的 PostgreSQL／PostgREST、正式 API、加密草稿與獨立帳號，比較 1／2／4 個 workers。正式平台不會因合併本 PR 自動增加 workers。

## Windows 執行

先取得此 PR 的程式，在專案根目錄執行。需要 Docker Desktop 的 Linux containers、Docker Compose v2.24+、Windows PowerShell 5.1；不需另裝 Python。首次建置含校方文件，預留 **至少 30 GB 可用 Docker 磁碟**。

```powershell
cd C:\uniway\app
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Setup -Users 1000
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Test -Workers 1 -Users 100 -Seconds 300
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Test -Workers 2 -Users 100 -Seconds 300
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Test -Workers 4 -Users 100 -Seconds 300
```

先比較 100 人，再用延遲較低且穩定的 workers 設定逐級測試：

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Test -Workers 4 -Users 300 -Seconds 300
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Test -Workers 4 -Users 500 -Seconds 300
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Test -Workers 4 -Users 1000 -Seconds 3660
```

每次更新程式後，重新執行 Setup 以重建映像；Test 只會切換測試配置。

`4` 是比較候選值，須依結果選擇。前一級失敗就先看報告，調整後重測，勿直接升級人數。最後才測 1500 人短暫尖峰（`-Users 1500 -Seconds 300`）。

報告在 `deploy\capacity\artifacts\日期-w數量-u人數.json`。報告不含 tokens、學生資料或原始回應。`actors.json` 含 **測試憑證**，與 `.env` 一樣不能公開或提交。每次 Test 會輪替本次 fixture 的 sessions，超過 24 小時也須重新執行 Test。請勿同時跑兩個 Test。

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Status
powershell -ExecutionPolicy Bypass -File .\deploy\capacity\Stage.ps1 -Action Stop
```

Stop 停止測試容器，保留隔離資料與報告。正式的 `uniway` 專案不受這個命令控制。

## 測量內容與判定

每個虛擬學生使用不同合成帳號：驗證 session、載入長庚學校目錄，接著每 10 秒一輪，讀文件清單／期限、讀寫並讀回申請工作區、讀寫並讀回加密草稿。30 秒逐步加入全部使用者；負載較高時一輪可能超過 10 秒，報告提供實際 requests/s 和完成輪數。這是有思考時間的同時在線模型，並非每秒 1000 次請求。不是完整瀏覽器測試，不包含圖片／JavaScript 載入或實際操作畫面上的搜尋。

加壓前先檢查同 revision 的並行儲存必須一筆 200、一筆 409，並驗證一個帳號的登出在所有預期 workers 都失效、另一個帳號仍可使用。正確性探針會要求測試代理釋放上游連線，確保請求能到不同 workers；正常加壓流量仍使用連線重用。測試入口必須回覆符合 fixture 的隔離識別碼，才會送出憑證或寫入。正式應用沒有此識別端點。

每個 API 路徑的 p95 應 ≤ 2 秒；這個工具對儲存、讀回與帳號隔離要求 **零錯誤**，因此比 HTTP 錯誤率 <1% 更嚴格。`passed: false` 或非零退出碼表示不合格。`workers` 記錄真正回覆請求的程序 PID，避免只改設定卻沒有測到多個 workers。

本地測試不測 Google OAuth 的外部服務、PDF 產生、檔案上下載、其他學校的大型目錄、外網速度或路由器 QoS。這些須分別驗證；本地 1000 人通過，仍不能直接宣稱正式站全面支援 1000 人。PDF 應另外限制並行量並測試；多校目錄可搭配階段一 `scripts/load_test_public.py`。

## 隔離與資源

- Compose project 固定 `uniway-capacity`，只有 `127.0.0.1:18000` 對主機開放；測試工具在隔離 Docker 網路內存取 web，無需開外網 port。
- 所有資料卷由此 project 自己命名，沒有引用 `uniway_db` 等正式卷。腳本在 migration 前再次驗證資料庫的 project label。
- 獨立產生資料庫密碼、JWT、文件加密金鑰和 run ID；不讀 `deploy/selfhost/.env`。沒有 Google、寄信或 AI API 金鑰。保留正式環境的 Supabase 持久層要求，沒有登入繞過端點。
- Seed 工具只存在測試目錄，用伺服器端 repository 建立合成帳號與標準 session。Load 容器只有測試 session，沒有 service-role／資料庫密碼。
- 候選設定為每 worker 16 threads、2 個 catalogue slots。正式預設保留 2／1；`EXCHANGE_WORKER_THREADS`（1–128）、`EXCHANGE_CATALOGUE_CONCURRENCY`（1–16）可明確設定。
- app 上限 3 CPU／6 GB，db 1 CPU／2 GB，generator 1 CPU／3 GB，其餘服務另設上限。測試和正式服務同機仍會共享 CPU、SSD，請在低流量時段跑；完整驗收最好在獨立測試主機使用與正式相同配置，並由另一台機器產生外網流量。
- 容器記憶體合計仍須留給正式站和 Windows 足夠空間。你目前 Docker 8 CPU／23.47 GiB 可先保留設定，不需要一次配滿實體 128 GB。

完整驗收時，另外觀察 `docker stats`、資料庫連線數、主機記憶體、SSD 與 Caddy 5xx，確認 1000 人持續一小時無累積退化。朋友的 50 Mbps 預留應在路由器做 QoS／流量整形；這套本機測試不會變更網路限速。

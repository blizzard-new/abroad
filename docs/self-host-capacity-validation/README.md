# 自架擴充準備：驗證紀錄

2026-10-18。選定測試依各案例最後一次的結果，去除重跑重複後為 **209 passed、0 failed、0 skipped**。首次自架套件檢查發現指南未記載既有 `daily-source-check.ps1`，補上說明後重跑通過。

同步最新主分支 `b370e6eb` 後，針對容量、帳號快取、自架設定及新合併的文件規則補跑 50 個案例，全部通過。

## 回歸測試

```bash
.venv/bin/python -m pytest -q \
  tests/test_capacity_readiness.py \
  tests/test_capacity_polling.py \
  tests/test_public_load_profile.py \
  tests/test_account_read_cache.py \
  tests/test_analytics_core.py \
  tests/test_analytics_api.py \
  tests/test_transient_auth.py \
  tests/test_selfhost_package.py \
  tests/test_auth_api.py \
  tests/test_frontend_contract.py \
  tests/test_rag.py \
  tests/test_application_writing_guidance.py

PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium \
.venv/bin/python -m pytest -q \
  tests/e2e/test_application_guidance.py \
  tests/e2e/test_web_next_phase.py::test_advisor_waits_for_login_and_clears_private_conditions_on_logout

node --check src/exchange_info/static/app.js
git diff --check
```

其中兩個 app instance 使用不同 repository 物件、共用模擬 REST 資料庫，驗證第二個 instance 立即看到帳號更新，並在第一個 instance 登出後拒絕原 token。這不是實際 PostgREST／PostgreSQL 或多個 OS 程序的整合測試。

輪詢測試執行正式前端的 `AiStatusManager` 類別，模擬時間、視窗可見性與網路事件；另以 Chromium 驗證正常開機、手機／桌面／深色模式、可選欄位驗證與登入草稿交接。統計測試以 1000 筆請求驗證只排一個刷新工作，確認可以繼續下一輪。負載工具測試 HTTP 錯誤、錯誤內容類型、逾時、參數與憑證拒絕條件，並確認只送 GET。

## 真實 HTTP 小流量啟動檢查

使用雲端開發環境（CPU 配額相當於 4 核、記憶體上限 16 GiB），對 loopback 的 Uvicorn 副本執行。使用暫存資料、開發模式及關閉使用統計，沒有連到正式主機、路由器或正式資料庫。

以 1 及 4 個程序分別啟動；同一個讀取情境是 10 位模擬訪客、15 秒、3 秒 ramp、每次讀取後停留 10 秒，臺大公開學校資料。單程序測試前曾讀取儀表板、文件與期限；4 程序檢查沒有逐程序暖機，且執行時另有瀏覽器回歸。**這兩份報告僅確認啟動與工具能實際運作，不能用來比較擴充效率或推算千人容量。**

| 程序 | 模擬訪客 | HTTP 請求 | 錯誤 | 全部請求 p95 | 報告 |
| --- | --- | --- | --- | --- | --- |
| 1 | 10 | 90 | 0 | 72.91 ms | [JSON](public-1worker-smoke.json) |
| 4 | 10 | 90 | 0 | 210.96 ms | [JSON](public-4workers-smoke.json) |

```bash
EXCHANGE_INFO_DATA_DIR=/tmp/abroad-capacity-smoke \
EXCHANGE_ANALYTICS=off EXCHANGE_AUTH_METHODS=google \
.venv/bin/python -m uvicorn exchange_info.api:app \
  --host 127.0.0.1 --port 8765 --workers 4 --no-access-log

# 在另一個終端執行：
.venv/bin/python scripts/load_test_public.py \
  --base-url http://127.0.0.1:8765 --users 10 --duration 15 \
  --ramp-seconds 3 --think-seconds 10 --school 國立臺灣大學 \
  --output /tmp/capacity-smoke.json
```

未執行 Windows PowerShell 的實機 QoS 設定、完整 Docker Supabase 整合壓測、CDN／WAN 測試或千人登入與私人文件的混合負載。PDF／Word 還沒有獨立工作佇列。完整的 staging 與千人驗收步驟見 [自架容量指南](../self-host-capacity.md)。

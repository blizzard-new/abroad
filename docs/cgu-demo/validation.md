# 原平台長庚專屬版驗證

本紀錄適用共用原 UniWay UI 的版本。前一版獨立小型介面的測試不作為本版驗收證據。所有帳號與測試寫入使用隔離暫存目錄；沒有連正式資料庫。

## 實際執行

| 檢查 | 結果 |
| --- | --- |
| 展示 HTML 資產／來源／帳號隔離／儲存與重設 | 9 passed，91.61 秒 |
| Chromium 瀏覽器 | 6 passed，205.08 秒；搜尋、收藏比較、來源、原生六階段計畫、鍵盤完成、重整保存、下一步、取消及確認重設 |
| 最終資料口徑修正後重跑 | 原生旅程及手機／平板 3 passed，170.75 秒；重新擷取截圖 |
| 尺寸與例外 | 1440×1000、390×844、820×1180；手機／平板無水平溢位；來源 503、重試、瀏覽器 storage 拒絕、正式 key 保留 |
| 正式功能回歸 | 106 passed、3 failed，196.99 秒；三個失敗與原基準相同，詳見 evidence/regression-tests.txt |
| Python／JS／shell 語法與 git diff --check | 通過；未配置獨立 lint／typecheck，不冒稱已執行 |
| uv lock --check | 通過，83 packages；未新增依賴 |
| OpenAPI／TLS installed-artifact gate | 通過；OpenAPI current，Node 24.22.1，119 CA roots |
| wheel | 通過；13 個核心檔案內容一致、11,306 個封裝來源檔案大小一致；專案目錄外啟動／原介面／虛構帳號／長庚 dashboard 通過 |

瀏覽器測試收集 pageerror；通過案例無 JavaScript 執行錯誤。測試用真正的原平台按鈕與 API，不以手動 DOM 改值冒充成功。靜態資產內容與原平台一致，僅額外附加展示控制與 storage bootstrap；共用 app.js 有待確認分類及收藏比較狀態的修正。

第一次並行執行完整回歸與 wheel 時環境壅塞，已中止並改分批；中止的回歸／建置不列為通過。打包後啟動檢查也抓到中斷建置留下的暫存資料截斷，已清除 build 暫存重新建置，並加入全部封裝來源檔案大小核對；沒有修改原始官方資料。首次瀏覽器逾時與比較狀態問題經檢查修正，只有最終重跑結果列入驗收。不是只提高 timeout 後忽略錯誤。

## 重跑

```sh
EXCHANGE_INFO_DATA_DIR=/tmp/uniway-cgu-tests .venv/bin/python -m pytest tests/test_cgu_demo.py -q

CGU_DEMO_EVIDENCE_DIR=docs/cgu-demo/evidence \
PLAYWRIGHT_NODEJS_PATH=/path/to/verified-node \
PLAYWRIGHT_BROWSERS_PATH=/path/to/playwright-browsers \
EXCHANGE_INFO_DATA_DIR=/tmp/uniway-cgu-browser \
.venv/bin/python -m pytest tests/test_cgu_demo_browser.py -q
```

展示測試在新進程啟動 factory，避免與一般 API 測試共用 module 全域狀態；會確認父環境指定的資料目錄沒有被讀寫。瀏覽器案例放在 tests 根目錄，不套用原 E2E conftest 的正式測試服務。

## 截圖

- [原首頁](evidence/desktop-home.png)
- [原學校詳細頁](evidence/desktop-school.png)
- [原「我的申請」與六階段](evidence/desktop-journey.png)
- [手機](evidence/mobile-journey.png)

截圖只有虛構學生，來源與當期名額仍依 sources.md 的限制。首屏深／淺色是原平台支援的主題。

## 尚未驗證與限制

- Firefox／WebKit、實體手機、完整主站全量 suite、Docker image／system CA、真實反向代理 HTTPS、正式資料庫、校方 API 與遠端部署未執行。
- 初次完整平台載入要預留暖機；展示前先預演。靜態檔案直接提供並快取，動態資料不快取到公用代理。
- 展示 session 為 24 小時，服務重啟會清除暫存資料；不能當正式長期服務。
- 原基準已有三個測試落差：合作校數 76／77、支援校數 18／60、前端 clearAuthenticatedClientState 函式契約。原始對照保留於 original-base-failures.txt，不能因此把本次任何新增失敗說成已知。
- TLS gate 初始預設 Playwright Node 不符合要求，官方 SHA-256 核對的 Node 24.22.1 能通過；部署需提供符合 gate 的持久化 runtime，不使用本機 /tmp 路徑。

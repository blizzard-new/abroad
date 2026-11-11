# 原平台長庚專屬版驗證

本紀錄適用使用者指定的 PR #299／main `87277daf` UI/UX。所有帳號與測試寫入使用隔離暫存目錄；沒有連正式資料庫。PR #301 合併前紀錄使用 `current-main-*` 檔名；Windows 部署續作以 main `ce86f376` 為基準，結果使用 `windows-*` 檔名。各批次分開記錄，不把過去結果當成本次重跑。

## Windows 部署續作：main `ce86f376`

本批次沒有改動共用 UI、正式 Dockerfile、正式 Compose 或 Python dependency lock。新增的是展示專用容器、固定版本的 Windows 啟動／Caddy 候選設定流程，以及 HTTPS Origin 的驗證修正。

| 實際執行 | 結果 |
| --- | --- |
| 展示 API 與部署隔離 | **22 passed，305.22 秒**；18 個展示／來源／HTTPS Origin 案例及 4 個部署安全案例。Windows Compose 路徑修正後，4 個部署案例再次通過（1.24 秒） |
| Chromium | **7 passed，233.83 秒**；桌面、手機、平板、搜尋收藏比較、六階段、工作台、鍵盤、刷新、重設及來源／storage 例外；無 pageerror |
| 靜態資產版本 | **2 passed，0.14 秒**；與本批次 main 的原資產保持相容 |
| OpenAPI | `scripts/export_openapi.py --check` 通過，正式契約未改變 |
| Docker image | 在 Linux Docker 28.4／amd64 實際建置通過；使用 lockfile hashes、Node 24.22.1 及既有 system CA／TLS gate，沒有降低驗證 |
| 容器內操作與隔離 | **通過**；健康狀態 healthy、六階段／保存／個人待辦／附件阻擋／CSRF／reset。使用 loopback 模擬 HTTPS 代理，並非公開 HTTPS 實測；non-root UID 10001、無 volumes、127.0.0.1:8765、2 GiB 上限、零重啟、build CA 不存在，核心 UI／程式檔 hash 與工作樹相同 |
| PowerShell 語法 | 兩支腳本以 PowerShell 7.4 parser 通過；**不代表已在 Windows PowerShell 5.1 或使用者主機執行** |

本批次共有 **31 個不同的 pytest 案例通過**；重跑的 4 個部署案例不重複計數。Python AST、`git diff --check` 通過；專案沒有獨立 lint／typecheck 設定。未重新執行主站全量 suite，下方歷史結果不當成本批次的新結果。

原始結果見 `evidence/windows-*`。容器測試 image revision 為 `working-tree`，image ID 與來源 hash 留在 windows-image.json／windows-container-isolation.json；Windows 腳本正式建置時改用 checkout 的 commit 作為 image tag 與 health revision。本批次截圖：[桌面首頁](evidence/windows-desktop-home.png)、[手機旅程](evidence/windows-mobile-journey.png)。仍使用原平台 UI，reduced motion 呈現原有地圖 fallback。

初次 Docker 建置碰到這個 Cloud 工作環境的代理憑證，以及 uv 重讀專案鬆綁版本條件時與 hash mode 衝突。已使用僅限 build 的 CA secret mount，並讓安裝器直接依匯出的鎖檔與 hashes 安裝後重跑成功；代理憑證沒有 COPY 到 image。中止或失敗的前置建置不列為通過。

Windows 實機、Docker Desktop、Caddy 排程工作、公開 DNS／HTTPS、公開 HTTPS 完整流程及 ARM64 image 尚未執行。沒有連線或修改使用者主站／正式資料庫，也沒有新增 Render 服務。此續作保留 Draft PR，待主機實測後再審查。

## PR #301 的實際執行

| 檢查 | 結果 |
| --- | --- |
| PR #299 展示 API 與 Chromium | **16 passed，200.50 秒**；9 個 API／資料／隔離案例及 7 個瀏覽器案例 |
| 實際操作 | 搜尋、收藏比較、來源、原生六階段計畫、鍵盤完成、重整保存、下一步、取消及確認重設；準備工作台新增筆記與個人日期、通知文字草稿與附件停用 |
| 尺寸與例外 | 1440×1000、390×844、820×1180；手機／平板無水平溢位；來源 503、重試、瀏覽器 storage 拒絕、正式 key 保留 |
| 正式功能回歸 | **128 passed、4 failed，149.79 秒**；包含 PR #299 準備工作台及靜態資產版本檢查；見 evidence/current-main-regression-tests.txt |
| Python／JS／shell 語法與 git diff --check | 通過；未配置獨立 lint／typecheck，不冒稱已執行 |
| uv lock --check | 通過，83 packages；未新增依賴 |
| OpenAPI／TLS installed-artifact gate | 通過；OpenAPI current，Node 24.22.1，119 CA roots |
| wheel | 通過，2,411,978,825 bytes；18 個核心檔案內容、11,308 個封裝來源檔案大小一致；專案目錄外啟動／PR #299 介面／虛構帳號／長庚 dashboard／工作台保存／上傳邊界通過 |

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
- [PR #299 準備工作台](evidence/desktop-workspace.png)
- [手機](evidence/mobile-journey.png)

截圖只有虛構學生，來源與當期名額仍依 sources.md 的限制。首頁保留 PR #299 的原風格；測試啟用 reduced motion，因此呈現原平台支援的地圖 fallback。搜尋及我的申請維持 PR #299 的樣式範圍。

## PR #301 當時的限制（歷史紀錄）

- Firefox／WebKit、實體手機、完整主站全量 suite、Docker image／system CA、真實反向代理 HTTPS、正式資料庫、校方 API 與遠端部署未執行。
- 初次完整平台載入要預留暖機；展示前先預演。靜態檔案直接提供並快取，動態資料不快取到公用代理。
- 展示 session 為 24 小時，服務重啟會清除暫存資料；不能當正式長期服務。
- 原基準已有三個測試落差：合作校數 76／77、支援校數 18／60、前端 clearAuthenticatedClientState 函式契約。原始對照保留於 original-base-failures.txt。PR #299 另將文件頁標題改為 h1，既有契約仍要求 h2；以 git show 取得 `87277daf` 原始測試及靜態檔案，在獨立 /tmp 目錄重現這項與函式契約兩個失敗（pr299-control.txt／xml）。未為了通過舊測試改回 PR #299 的介面，當時保留 Draft PR（PR #301 之後已合併）；沒有把新增失敗默認為已知。
- TLS gate 初始預設 Playwright Node 不符合要求，官方 SHA-256 核對的 Node 24.22.1 能通過；部署需提供符合 gate 的持久化 runtime，不使用本機 /tmp 路徑。

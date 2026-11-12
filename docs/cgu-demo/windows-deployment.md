# 長庚展示站：Windows 主機獨立部署與維運指南

長庚專屬展示站採用獨立 Git checkout（`C:\uniway-cgu-demo`）、獨立 Docker Compose 專案（`uniway-cgu-demo`）與專用 image，透過 Windows 主機既有 Caddy 反向代理提供公開網址 `https://demo.uniway-tw.com`，與正式主站（`C:\uniway\app`、`https://app.uniway-tw.com`）完全隔離；不新增雲端主機、外部資料庫或付費服務。所有腳本皆需由管理者於主機明確手動執行，不會自動拉取 Git 更新、合併 PR 或更動正式站資料庫。

## 固定版本與隔離

- 使用獨立目錄 `C:\uniway-cgu-demo`。Docker Compose project 為 `uniway-cgu-demo`，只有 `demo` 一個服務，綁定主機 loopback 埠（預設 `8765`，或現場透過 `-Port` 指定如 `8766`）；正式站原有 `8000` 及資料庫不變。
- image 為 `uniway-cgu-demo:<commit 前 12 碼>`，啟動時固定該 image，沒有自動更新機制。更新前建議先對目前穩定運作的 commit 與 Docker image 建立 rollback tag 作為回復點。
- 沒有掛載正式 volumes、讀取正式 `.env`、加入正式 Docker network，或使用正式帳號／OAuth／SMTP。
- 專用 Dockerfile 保留原 TLS gate，另外安裝官方 SHA-256 核對的 Node 24.22.1；不改動正式 Dockerfile。
- 展示進度（含 `MockCguConnector` 模擬送件、詢問單、返國心得與通知）儲存在展示程序暫存目錄；重新整理可保留，容器重啟或重建會清除。

## 1. 首次建立或手動更新展示容器

在 Windows 主機的 PowerShell 執行（切勿在開發分支驗收階段未經指示自行部署覆蓋線上服務）：

```powershell
git clone --depth 1 --branch main --single-branch https://github.com/blizzard-new/abroad.git C:\uniway-cgu-demo
powershell -ExecutionPolicy Bypass -File C:\uniway-cgu-demo\deploy\cgu-demo\start-windows.ps1
```

若現場使用自訂 loopback 連接埠（例如 `8766`），請傳入 `-Port 8766`。腳本拒絕帶有相關未提交修改的原始碼，也拒絕占用主站連接埠。它只建立／啟動展示容器，並自動驗證 `mode=cgu-demo`、commit、Secure Cookie、六階段、進度保存、個人日期、附件阻擋、CSRF 與重設。

## 2. 產生與驗證 Caddy 候選設定

```powershell
powershell -ExecutionPolicy Bypass -File C:\uniway-cgu-demo\deploy\cgu-demo\publish-windows.ps1
```

預設只讀取 `C:\uniway\caddy\Caddyfile`，在旁邊產生 `.cgu-demo.candidate` 並交給 Caddy 驗證，不套用、不重啟。若更換展示 port，兩支腳本都要傳入相同 `-Port`。

## 3. Cloudflare DNS 設定原則

在 `uniway-tw.com` zone 維持 `demo` 子網域指向 Windows 主站對外入口（不要修改原本 `app` 的記錄、全站 SSL 模式或 nameservers，也不需要把內部 loopback 埠開到外網）。

## 4. 明確套用與公開流程檢查

需首次掛上或調整 Caddy 路由時，在**系統管理員 PowerShell**執行：

```powershell
powershell -ExecutionPolicy Bypass -File C:\uniway-cgu-demo\deploy\cgu-demo\publish-windows.ps1 -Apply
```

完成後可執行公開流程檢查：

```powershell
docker compose -p uniway-cgu-demo -f C:\uniway-cgu-demo\deploy\cgu-demo\compose.yml exec -T demo python /opt/demo-verify.py --url https://demo.uniway-tw.com
```

這個驗證器先確認目標確實為展示服務（`mode=cgu-demo`）才會建立虛構計畫；若指到原主站會拒絕任何測試寫入。

## 停止與回復至 Rollback Tag

只停止展示容器：

```powershell
docker compose -p uniway-cgu-demo -f C:\uniway-cgu-demo\deploy\cgu-demo\compose.yml stop demo
```

若需退回先前打好 tag 的穩定版本，可在 `C:\uniway-cgu-demo` 切回對應 rollback tag 並以已保留的 `uniway-cgu-demo:<commit 或 rollback tag>` image 啟動，切勿使用正式 `deploy/selfhost` 的 reset、migration 或 `down -v`，亦不要改動 `uniway-app:local`。

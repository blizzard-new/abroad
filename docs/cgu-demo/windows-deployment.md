# 長庚展示站：沿用 Windows 主機

使用者已確認主站跑在自己的 Windows 電腦，並選擇不用 Render。本方案沿用 repository 的 Docker Desktop（Linux containers）與 Windows Caddy 設定；不新增雲端主機、資料庫或付費方案。這個 Codex Cloud 工作環境不能直接控制那台 Windows，所以主機上的執行與 Cloudflare DNS 仍需要使用者操作。下列腳本不會合併 PR、切換正式 checkout 或執行正式 migrations。

## 固定版本與隔離

- 使用另一個 clone。Docker Compose project 為 `uniway-cgu-demo`，只有 `demo` 一個服務，綁 `127.0.0.1:8765`；正式站原有 `8000` 及資料庫不變。
- image 為 `uniway-cgu-demo:<commit 前 12 碼>`，啟動時固定該 image，沒有 Git 自動更新。重新執行啟動腳本才更新。
- 沒有掛載正式 volumes、讀取正式 `.env`、加入正式 Docker network，或使用正式帳號／OAuth／SMTP。
- 使用既有 Python dependencies 與公開資料。專用 Dockerfile 保留原 TLS gate，另外安裝官方 SHA-256 核對的 Node 24.22.1；沒有降低憑證驗證。這不改動正式 Dockerfile。
- 進度儲存在展示程序的暫存目錄；重啟或重建會清除。比賽當天先暖機、載入計畫，展示中不要更新容器。

## 1. 取得展示分支並啟動

在 **那台 Windows 主機**的 PowerShell 執行。`C:\uniway-cgu-demo` 必須是新的目錄，不能覆蓋主站 checkout；GitHub 登入沿用主機的正常 Git 授權，勿將 token 貼入指令或聊天。

```powershell
git clone --depth 1 --branch codex/cgu-windows-deploy --single-branch https://github.com/blizzard-new/abroad.git C:\uniway-cgu-demo
powershell -ExecutionPolicy Bypass -File C:\uniway-cgu-demo\deploy\cgu-demo\start-windows.ps1
```

第一次要下載 image 與 dependencies；實測 amd64 image 為 4,121,235,816 bytes（約 3.84 GiB），建議連同 clone 與 build cache 至少預留 15 GiB 空間及建置時間。腳本拒絕帶有相關未提交修改的原始碼，也拒絕占用主站連接埠。它只建立／啟動展示容器，會驗證 `mode=cgu-demo`、commit、Secure Cookie、六階段、進度保存、個人日期、附件阻擋、CSRF 與重設；測試只使用新建的虛構帳號。

`http://127.0.0.1:8765/health` 是主機內部檢查入口。完整互動應使用後面的 HTTPS 網址；正式展示 Cookie 是 Secure，不能把 HTTP 的 localhost 頁面當作已驗證的公開網站。

## 2. 產生 Caddy 候選設定

```powershell
powershell -ExecutionPolicy Bypass -File C:\uniway-cgu-demo\deploy\cgu-demo\publish-windows.ps1
```

預設只讀取 `C:\uniway\caddy\Caddyfile`，在旁邊產生 `.cgu-demo.candidate` 並交給 Caddy 驗證，不套用、不重啟。候選設定保留原內容，僅新增 `demo.uniway-tw.com` 導向 `127.0.0.1:8765`。若已有同名網域、候選檔被編輯、主設定在驗證中改變，腳本會停止並保留變更。

如果主站沒有使用這份專案的 `UniWay-Caddy` 排程工作或 Caddyfile 路徑，先確認實際入口，不要執行主站安裝腳本來覆蓋現況。自訂路徑可使用 `-CaddyFile`／`-CaddyExe`；若更換展示 port，兩支腳本都要傳入相同 `-Port`。

## 3. Cloudflare DNS

公開 DNS 查詢確認 `uniway-tw.com` 使用 Cloudflare，查詢時 `demo.uniway-tw.com` 尚無記錄。這不是對 Cloudflare 帳戶設定的讀取；本次沒有新增 DNS。

在該 zone 新增一筆 `demo` 的 **A record**，值使用現有 Windows 主站的實際對外固定 IPv4（向現有主站設定確認）。不要把公開 DNS 查到的 Cloudflare 邊緣 IP 當成你的主機 IP，也不要修改原本 `app` 的記錄、全站 SSL 模式或 nameservers。初次憑證驗證可先設 DNS only；如果目前主站採 Tunnel 或其他方式，需沿用該入口，不能直接套用 A record 步驟。

Windows 既有路由器 80／443 轉送應已服務主站，不需要把 8765 開到外網。不要填猜測的 IP；本工作環境沒有 Cloudflare zone 寫入權限。

## 4. 明確套用與檢查

確認候選檔與 DNS 後，在**系統管理員 PowerShell**執行：

```powershell
powershell -ExecutionPolicy Bypass -File C:\uniway-cgu-demo\deploy\cgu-demo\publish-windows.ps1 -Apply
```

既有 Caddy 設為 `admin off`，所以套用時會**短暫重啟共用 HTTPS 入口**，主站訪客可能短暫遇到中斷；正式 app 與資料庫不會被重啟。腳本先檢查展示模式、既有排程、DNS 與主站健康，備份 Caddyfile，再套用候選設定。主站或展示 HTTPS 健康檢查失敗會還原原設定；若偵測到同時有人編輯，會保留對方變更並停止，不盲目覆蓋。

Caddy 自動申請展示網域的 HTTPS 憑證。成功後，在展示 checkout 執行公開流程檢查：

```powershell
docker compose -p uniway-cgu-demo -f C:\uniway-cgu-demo\deploy\cgu-demo\compose.yml exec -T demo python /opt/demo-verify.py --url https://demo.uniway-tw.com
```

這個驗證器先確認目標確實為展示服務才會建立虛構計畫；若指到原主站會拒絕任何測試寫入。最後用瀏覽器走 [展示腳本](demo-script.md)：搜尋、來源、載入、完成、重新整理、下一步、取消／確認重設。HTTPS `/health` 應顯示實際 image commit，且 `mode=cgu-demo`。

## 停止與回復

只停止展示容器：

```powershell
docker compose -p uniway-cgu-demo -f C:\uniway-cgu-demo\deploy\cgu-demo\compose.yml stop demo
```

不要使用正式 `deploy/selfhost` 的更新、reset、migration 或 `down -v`。要回復展示程式，可使用保留的較早 `uniway-cgu-demo:<commit>` image；不要改動 `uniway-app:local`。要撤回 Caddy 公開入口，應只移除新增的展示 block；若主設定在之後有其他更動，不可整份覆蓋舊備份。

本次可執行的容器／腳本檢查與未執行的 Windows 實機、DNS／HTTPS 項目記在 [驗證紀錄](validation.md)。準備完成不等於主機已上線。

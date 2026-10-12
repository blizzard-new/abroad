# 自架到 Jerry 家的 Windows 電腦：完整步驟

這份指南讓你把 UniWay 從 Render＋Supabase 搬到一台自己管理的 Windows 電腦（Jerry 家那台：128 GB 記憶體、4 TB SSD、固定 IP、一直開機）。所有要裝的東西和要跑的腳本都已經準備好、在這個倉庫的 `deploy/selfhost/` 裡，**每個腳本都在本機實際跑過**（見最後一節「我測過什麼、沒測過什麼」）。

> **誠實說明「不依賴雲端」的範圍。** 網站、資料庫、檔案、備份的主體都在 Jerry 家的電腦上。但以下幾樣仍然要靠外面的服務，沒辦法換掉：
> - **Google**：登入本身（OAuth），以及（選用）把加密後的備份放到你的 Google Drive。
> - **Let's Encrypt**：免費的 HTTPS 憑證，每 60 天自動更新一次。
> - **網域註冊商／DNS**：讓 `app.你的網域.com` 指到 Jerry 家的固定 IP。
> - **GitHub**：取得與更新程式碼。

---

## 0. 先看這裡

### 0.1 全貌

```
使用者的手機／電腦
        │  https://app.你的網域.com   （Jerry 家固定 IP，路由器把 80、443 轉給那台電腦）
        ▼
┌────────────────────────── Jerry 的 Windows 電腦 ──────────────────────────┐
│  Caddy（直接裝在 Windows）  ← 唯一對外開放的程式：HTTPS、壓縮、寫入真實 IP、限速 250 Mbps │
│        │ 127.0.0.1:8000（只有本機連得到）                                              │
│  ┌─────▼──────────────────── Docker ──────────────────────────────┐          │
│  │ app（網站程式，Python）                                         │          │
│  │   │ https://gateway（只在 Docker 內部，內部憑證）                │          │
│  │ gateway ─┬─► rest（PostgREST：資料庫的 REST 門）                 │          │
│  │          └─► storage（私人文件儲存）                            │          │
│  │ db（PostgreSQL 17 ＋ pgvector，與 Supabase 同一個映像檔）        │          │
│  └──────────────────────────────────────────────────────────────┘          │
│  每天 04:00 備份 → C:\uniway\backups → 加密後 → 你的 Google Drive             │
└───────────────────────────────────────────────────────────────────────────┘
```

設計重點（每一點都是實測後才這樣定的）：

| 決定 | 原因 |
|---|---|
| 資料庫用 **自架版 Supabase 的同一組元件**（Postgres＋PostgREST＋Storage），不是改寫成別的資料庫 | 程式透過 REST 呼叫資料庫，31 份 migration 裡有 71 個資料庫函式。這樣**程式碼和 migration 一行都不用改** |
| **Caddy 裝在 Windows 上，不放進 Docker** | Docker Desktop 會把所有連線的來源位址變成同一個內部位址，登入限流就會把全世界當成同一個人。Caddy 直接在 Windows 收連線，才看得到真實來源 IP |
| 資料庫和儲存**完全不對外開放** | 只有 Caddy 的 80／443 對外；網站程式只聽 `127.0.0.1:8000`；資料庫、REST 門、儲存在 Docker 內部網路，外面連不到 |
| 網站程式和資料庫之間用**內部 HTTPS** | 程式有一道安全檢查：資料庫位址不是 `https://` 就拒絕啟動。我們不去繞過它，而是讓內部閘道用 Caddy 的內部憑證，程式信任它 |
| 只開 **1 個工作程序** | 登入限流和使用統計的計數放在程式記憶體裡，開多個程序會各算各的。1 個程序實測每秒約 55 個請求，夠用 |

### 0.2 分工

| 誰 | 做什麼 |
|---|---|
| **Jerry** | 路由器設定（轉送 80／443、保留這台電腦的內網 IP）、確認電腦能一直開、讓你能遠端連進來 |
| **你** | 買網域、設 DNS、Google 登入設定、遠端連到那台電腦後依序執行腳本、切換日當天操作 |
| **腳本**（已寫好） | 檢查電腦、設定 Windows、產生密鑰、啟動全部服務、套用資料庫、安裝 HTTPS、備份、搬資料、驗證 |

### 0.3 要準備的東西

- [ ] 一個**網域**（一年約幾百元台幣）。不能只用 IP：Google 登入不接受裸 IP，也不接受 http。
- [ ] 你的 **Google Cloud 主控台**權限（改 OAuth 的返回網址）。
- [ ] **Supabase 的資料庫密碼**（搬資料時用；忘了可以在 Supabase 重設，不影響網站運作）。
- [ ] **Render 的 Environment 頁面**能看（要抄 `EXCHANGE_CONTENT_ADMIN_EMAILS`、聯絡信箱等設定）。
- [ ] **GitHub 帳號**（`blizzard-new`）能登入（那台電腦要用它取得程式碼）。
- [ ] 密碼管理員（存密鑰用）。
- [ ] （選用）你的 **Google Drive**，備份用。

### 0.4 時間

| 階段 | 約多久 |
|---|---|
| A 與 Jerry 確認、路由器設定 | 30 分鐘 |
| B 網域、Google 設定 | 30 分鐘（DNS 生效可能再等 10～60 分鐘） |
| C 安裝工具 | 30 分鐘（可能要重開機 1～2 次） |
| D～F 啟動、HTTPS、驗證 | 約 1 小時（第一次要下載映像檔、建置，約 15～20 分鐘） |
| G Google 登入測試 | 15 分鐘 |
| H 備份 | 30 分鐘 |
| I 切換日 | 約 30～60 分鐘（網站停機約 10～20 分鐘） |

---

## 階段 A：跟 Jerry 確認與設定（Jerry 做，你照這份清單問）

### A1. 路由器

1. **確認固定 IP**：到路由器的狀態頁看「WAN IP」，確認和 Jerry 給你的一樣，並且是他向電信業者申請的**固定 IP**（會寫在帳單或方案上）。如果其實會變，要用 DDNS，見附錄 D。
2. **保留這台電腦的內網 IP**（DHCP 保留／靜態租約）：讓那台電腦永遠拿到同一個內網 IP（例如 `192.168.1.50`），否則轉送規則哪天會指向錯的機器。
3. **新增兩條連接埠轉送**（port forwarding）：

   | 外部連接埠 | 協定 | 轉到 | 內部連接埠 |
   |---|---|---|---|
   | 80 | TCP | 那台電腦的內網 IP | 80 |
   | 443 | TCP | 那台電腦的內網 IP | 443 |

   80 是給憑證驗證和「http 自動轉成 https」用的。
4. **刪掉先前的測試規則**（外部 23457 那條），不需要了。
5. **關掉 UPnP**（讓電腦裡的程式不能自己在路由器上開洞）。
6. **確認電信業者沒有擋 80／443**：有些家用寬頻會擋。最簡單的測法是做完階段 F 後用手機（**關掉 Wi-Fi，用行動網路**）打開 `https://你的網域/health`。如果進不去，先問 Jerry 的電信業者；備案見附錄 C。
7. （建議）**頻寬上限**：Jerry 說上傳要控制在 250 Mbps、留 50 給他。**這裡的單位是 Mbps（每秒百萬「位元」）**，不是 MBps（每秒百萬「位元組」，1 位元組 = 8 位元）。如果路由器有 QoS／頻寬控制功能，就在路由器對那台電腦設上傳 250 Mbps（最可靠）。階段 D 的腳本也會在 Windows 上設一條同樣的限制，兩邊都設也沒關係。

### A2. 那台電腦

- [ ] **一直開機、不睡眠**（腳本會設，但請 Jerry 知道不要關機、不要按「睡眠」）。
- [ ] **Windows 版本**：Windows 10／11 皆可，專業版較佳（Home 版也能跑，只有部分功能受限，已在腳本裡處理）。
- [ ] **Windows Update**：到「設定 → Windows Update → 進階選項 → 使用時間」設好；選「重新啟動時通知我」，**不要讓它半夜自己重開機**（重開機後要有人登入網站才會回來，見 A2 的自動登入）。
- [ ] **自動登入**（建議）：Docker Desktop 要在使用者登入後才會啟動。電腦意外重開機後，如果沒人登入，網站就會停著。做法：用 Microsoft 的 Sysinternals **Autologon** 工具設定該使用者自動登入（它把密碼加密存放，比 `netplwiz` 安全）。代價：任何人實體碰到這台電腦就能進去，所以這台電腦要放在家裡安全的地方，並啟用磁碟加密（下一點）。
- [ ] **磁碟加密**：Windows 11 「設定 → 隱私權與安全性 → 裝置加密」（或 BitLocker）。因為資料庫裡有使用者的信箱和留言，電腦被偷時不該被讀到。**備份復原金鑰到 Jerry 的 Microsoft 帳號**。
- [ ] **UPS**（不斷電系統）：停電時乾淨關機，避免資料庫損壞。沒有的話至少接穩壓插座。
- [ ] **一顆外接備份硬碟**（建議）：4 TB 的 SSD 只有一顆，壞了就全沒。備份資料夾 `C:\uniway\backups` 之後可以改放外接硬碟。

### A3. 你怎麼遠端連進去

- **建議用 VPN 類工具**（例如 Tailscale，免費）：Jerry 的電腦和你的電腦都裝，你再用「遠端桌面」連它的 Tailscale 位址。**絕對不要在路由器上把 3389（遠端桌面）開到網際網路**，那會在幾小時內被全世界的掃描器攻擊。
- 或用 Jerry 現有的遠端工具（AnyDesk、Chrome 遠端桌面、他的 Parsec 等），你們自己決定。
- **請 Jerry 另外建一個 Windows 使用者給你**（例如 `uniway`），不要用他的主要帳號。這個帳號需要是「系統管理員」，因為安裝 Docker 和設定防火牆需要。
- 注意：Tailscale 的服務程式可能占用 443 埠（我這台電腦就是）。階段 C 的檢查會偵測到；如果 Jerry 也有，要先把它的 443 讓出來。

---

## 階段 B：網域與 Google 登入（你做）

### B1. 買網域

任何註冊商都可以，要求只有一個：**可以自己改 DNS 記錄**。網域可以很短、不用特別好看，例如 `uniway-tw.com`。

### B2. 指到 Jerry 家

在註冊商的 DNS 管理頁新增一筆記錄：

| 類型 | 名稱 | 值 | TTL |
|---|---|---|---|
| A | `app`（網站會是 `app.你的網域.com`；想直接用根網域就留空或填 `@`） | Jerry 家的固定 IP | 300 秒 |

不要開任何「CDN／代理」功能（例如 Cloudflare 的橘色雲朵），否則使用者的連線會先經過別人的伺服器，就不是自架了，而且會看不到真實 IP。

等幾分鐘後，在你自己的電腦測：

```powershell
Resolve-DnsName app.你的網域.com -Type A
```

應該看到 Jerry 的固定 IP。

### B3. Google 登入（OAuth）

到 **Google Cloud 主控台** → 你現有的專案 → **Google 驗證平台（Google Auth Platform）** → **用戶端**（Clients）→ 點你現在用的那個 Web 用戶端（不要新建，這樣 Render 那邊在切換前還能繼續用）。

1. **已授權的 JavaScript 來源**：新增 `https://app.你的網域.com`
2. **已授權的重新導向 URI**：新增 `https://app.你的網域.com/auth/oauth/google/callback`
   （和舊網址那條並存，切換完成前兩個網站都能登入。）
3. 到 **品牌（Branding）／OAuth 同意畫面**：
   - **已授權網域**：新增 `你的網域.com`。Google 可能會要求你先在 Search Console 驗證這個網域（在 DNS 加一筆 TXT，Google 會告訴你填什麼）。
   - **應用程式首頁**、**隱私權政策連結**、**服務條款連結**分別改成 `https://app.你的網域.com/`、`/privacy`、`/terms`。
4. 記下**用戶端 ID** 和**用戶端密碼**（階段 E 用）。**密碼只貼在 Jerry 電腦上腳本問你的地方，不要貼進聊天室或任何文件。**

---

## 階段 C：安裝工具（在 Jerry 的電腦上，用 Administrator 的 PowerShell）

> 開法：開始選單輸入 `PowerShell`，**右鍵 → 以系統管理員身分執行**。

### C1. 安裝 Git、Docker Desktop

```powershell
winget install -e --id Git.Git
winget install -e --id Docker.DockerDesktop
```

裝完 Docker Desktop **重新開機**。開機後登入，Docker Desktop 會自己啟動，第一次會要你接受授權條款，並可能要求啟用 WSL 2（照它說的做，必要時再重開機）。等到畫面左下角顯示 **Engine running**。

如果 `wsl --status` 說沒裝，先執行 `wsl --install`，重開機。

### C2. 限制 Docker 能用的資源

這台電腦有 128 GB 記憶體，但我們不需要那麼多，也不要讓 Docker 吃掉 Jerry 的電腦。在使用者資料夾建立 `C:\Users\<使用者>\.wslconfig`（用記事本，檔名前面有一個點）：

```
[wsl2]
memory=24GB
processors=8
swap=8GB
```

然後執行 `wsl --shutdown`，再重新開啟 Docker Desktop。

在 Docker Desktop → **Settings → General**：勾選 **Start Docker Desktop when you sign in to Windows**。不要在平常使用時按「Quit Docker Desktop」。

### C3. 取得程式碼

```powershell
mkdir C:\uniway
cd C:\uniway
git clone -c core.autocrlf=false --branch main https://github.com/blizzard-new/abroad.git app
```

> **套件目前還在分支 `selfhost/windows-deploy`，還沒合併進 `main`。** 在它合併之前，上面那行請把 `--branch main` 改成 `--branch selfhost/windows-deploy`；合併之後才用 `main`。之後執行 `update.ps1` 會自動跟著你目前所在的分支更新。

第一次會要你用 GitHub 帳號登入（瀏覽器會跳出來）。倉庫很大（約 1.4 GB），需要幾分鐘。

> **為什麼要 `-c core.autocrlf=false`？** Windows 版的 Git 預設會把檔案換成 CRLF 換行。資料庫 migration 會比對函式的原文，多一個看不見的字元就會「資料庫函式和舊伺服器不同」。我們的腳本已經在套用時自動換回 LF、`.gitattributes` 也鎖了 `.sql`，這一行是第三層保險。

之後所有指令都在這個資料夾：

```powershell
cd C:\uniway\app\deploy\selfhost\scripts
```

如果 PowerShell 說「禁止執行指令碼」，每次用 `powershell -ExecutionPolicy Bypass -File .\xxx.ps1` 執行，下面所有範例都是這樣寫。

### C4. 檢查這台電腦（唯讀，什麼都不改）

```powershell
powershell -ExecutionPolicy Bypass -File .\00-check.ps1
```

預期全部 `[ OK ]`。常見的 `[FAIL]`：

- `Nothing else is using ports 80 and 443`：有別的程式占了 80／443（IIS、Skype、Tailscale、別的網頁伺服器）。腳本會告訴你是哪個程式；停掉或改它的埠。

---

## 階段 D：準備 Windows（Administrator）

```powershell
powershell -ExecutionPolicy Bypass -File .\01-prepare-windows.ps1 -UploadMbps 250
```

它會做：

1. 建立 `C:\uniway\{logs,backups,caddy}` 資料夾。
2. 電源：插電時**永不睡眠、永不休眠、硬碟不休眠**（螢幕可以關）。
3. 防火牆：只允許 `caddy.exe` 接受 TCP 80／443 進來。**沒有開任何別的埠**。
4. 上傳限速：Windows QoS 政策，`caddy.exe` 最多 250 Mbps（可用 `-UploadMbps` 改）。如果 Windows 版本不支援，腳本會提醒你改在路由器設。

腳本最後會提醒兩件**要手動做**的事：Windows Update 使用時間、不要把 3389 開到網際網路。

---

## 階段 E：設定與啟動

### E1. 產生密鑰、寫設定檔

```powershell
powershell -ExecutionPolicy Bypass -File .\02-generate-secrets.ps1 `
    -Domain app.你的網域.com -AcmeEmail 你的信箱@gmail.com `
    -ContactEmail 你的信箱@gmail.com -AdminEmails 你的信箱@gmail.com -AskGoogle
```

- `-AskGoogle` 會問你 Google 的用戶端 ID 和密碼（密碼輸入時看不到字，這是正常的）。
- `-AdminEmails`：可以開 `/admin/*`（統計、用戶評價收件匣）的 Gmail，逗號分隔。抄 Render 上 `EXCHANGE_CONTENT_ADMIN_EMAILS` 的值。
- `-ContactEmail`：顯示在 `/privacy` 與 `/terms` 的聯絡信箱，抄 Render 上 `EXCHANGE_CONTACT_EMAIL`。
- 資料庫密碼、JWT 密鑰、文件加密金鑰等**全部由電腦隨機產生**，只存在 `C:\uniway\app\deploy\selfhost\.env`（只有你這個帳號、管理員、系統能讀；已加進 `.gitignore`，不會被提交）。
- 如果 Render 那邊**已經有人存過表單草稿或上傳過文件**，必須沿用舊的加密金鑰（加上 `-UseExistingKeys`，貼上 Render 的 `EXCHANGE_VAULT_MASTER_KEY`），否則舊資料讀不出來。**截至 2026-10-12 正式資料庫裡這兩樣都是 0 筆**，所以用新產生的也可以；但切換日當天要再確認一次（見階段 I）。

腳本最後會提醒你：**現在就把 `.env` 的內容存進密碼管理員（安全筆記）**。`VAULT_MASTER_KEY` 遺失，之後上傳的文件永遠讀不回來。

### E2. 啟動全部

```powershell
powershell -ExecutionPolicy Bypass -File .\03-start.ps1
```

它依序做：建置網站映像檔（第一次約 5～10 分鐘）→ 啟動資料庫並設定內部角色密碼 → 啟動 REST 門、儲存、閘道 → 套用全部 31 份資料庫 migration（自動換成 LF 換行）→ 啟動網站 → 建立私人文件儲存桶。最後會印出 `The stack is running.`。（其中「套用資料庫」那一步是 `04-apply-migrations.ps1`，`03` 會自己呼叫它；之後網站更新帶來新的 migration 時，`update.ps1` 也會呼叫它。可重複執行，已套用的會自動略過。）

> 啟動後前幾分鐘網站會比較慢：程式在背景暖機（建立各校儀表板的快取）。

### E3. 驗證

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1
```

預期最後一行 `VERIFY: everything passed.`。它檢查：網站健康、六所學校的資料都有、資料庫能讀、公開金鑰**不能**讀帳號、內部函式不能從外面呼叫、用戶評價表單能寫進資料庫（測完會刪掉）、私人儲存桶存在且是私人、檔案能存取且不能被公開讀取。

此時網站還只能在 Jerry 的電腦上用 `http://127.0.0.1:8000` 看（還沒有 HTTPS）。

---

## 階段 F：HTTPS 與對外開放

### F1. 安裝 Caddy

```powershell
powershell -ExecutionPolicy Bypass -File .\05-install-caddy.ps1
```

它會從 GitHub 下載官方 Caddy、**驗證 SHA-512 檢查碼**、寫好設定檔、設成開機自動啟動（排程工作 `UniWay-Caddy`，以 SYSTEM 執行，失敗會自動重啟）。Caddy 第一次收到你的網域的連線時會向 Let's Encrypt 申請憑證，約一分鐘。

### F2. 從外面驗證

在**不是 Jerry 家網路**的地方（手機關 Wi-Fi 用行動網路，最簡單）：

1. 開 `https://app.你的網域.com`，應該看到網站，網址列有鎖頭。
2. 開 `http://app.你的網域.com`，應該自動轉到 `https://`。
3. 開 `https://app.你的網域.com/health`，應該顯示 ok。

然後在 Jerry 的電腦上：

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1 -ExpectedIp Jerry家的固定IP
```

**確認網站看到的是訪客的真實 IP（很重要）：** 剛才用手機連過一次後，在 Jerry 的電腦打開 `C:\uniway\logs\access.log` 的最後幾行，找 `"remote_ip"`。它應該是**你手機的公用 IP**（手機瀏覽器搜尋「my ip」可以看到），**不是** `192.168.x.x` 或 `172.x.x.x`。如果是內網位址，代表有東西擋在 Caddy 前面（例如路由器做了奇怪的轉送），這會讓登入限流把全世界當成同一個人，要先排除再繼續。

**確認上傳限速：** 找一個在別的網路的人（或你的手機熱點），同時用多個 `curl` 下載網站上最大的檔案（例如 `/static/app.js`），總速度不應超過約 31 MB/s（= 250 Mbps）。更簡單的辦法是看路由器的流量統計。如果 Windows 的限速沒有生效，就在路由器設（階段 A1 第 7 點）。

---

## 階段 G：Google 登入測試

1. 用手機或另一台電腦開 `https://app.你的網域.com`，點登入。
2. 勾選同意條款 → 用 Google 登入 → 應該回到網站並顯示你的名字。
3. 如果登入按鈕是灰的：`.env` 裡 Google 用戶端 ID／密碼是空的，重新執行 E1 加 `-AskGoogle`，再 `03-start.ps1 -SkipBuild`。
4. 如果 Google 說「redirect_uri_mismatch」：階段 B3 的返回網址和實際的不一樣，逐字比對 `https://app.你的網域.com/auth/oauth/google/callback`。
5. 登入後打開 `https://app.你的網域.com/admin/feedback`（用 `-AdminEmails` 設的那個 Gmail），應該看得到用戶評價收件匣。
6. 打開 `/privacy`，第 4 節應該寫「資料庫與加密文件：存放在營運者自行管理的伺服器，位於台灣」，**不再提到 Supabase 或 Render**。

---

## 階段 H：備份

### H1. 本機備份（自動）

```powershell
powershell -ExecutionPolicy Bypass -File .\07-setup-backup.ps1
```

它建立兩個排程工作（**以目前登入的使用者執行**，因為 Docker Desktop 在使用者的工作階段裡）：

- `UniWay-Backup`：每天 04:00 備份資料庫、文件檔案、`.env` 到 `C:\uniway\backups`，保留 14 天＋8 週＋6 個月。
- `UniWay-Health`：每 5 分鐘執行 `healthcheck.ps1`，檢查網站；本機沒回應就自動 `docker compose up -d`，並記錄在 `C:\uniway\logs\health.log`（對外網址不通、磁碟低於 50 GB 也會寫進去）。

最後會立刻跑一次備份。

### H2. 證明備份真的能還原（一定要做）

```powershell
powershell -ExecutionPolicy Bypass -File .\restore-test.ps1
```

預期 `restore test passed`。它把最新備份還原到一個**拋棄式的資料庫**再比對筆數，不會碰正式資料。**第一次備份後做一次，之後每個月做一次。**

### H3. 備份到你的 Google Drive（加密）

備份檔含使用者的信箱和留言，所以**上傳前先在本機加密**，Google 只會看到亂碼。用 `rclone` 的 `crypt` 功能。以下只要做一次，需要你本人用瀏覽器登入 Google（我不能代做）：

1. 在 Jerry 的電腦安裝：`winget install -e --id Rclone.Rclone`，然後**開一個新的 PowerShell 視窗**。
2. **建立你自己的 Google API 用戶端**（不要用 rclone 預設的，它的額度是全世界共用，很容易被限流）：
   - Google Cloud 主控台 → 建立新專案 `uniway-backup` → **API 和服務 → 啟用 API → Google Drive API**。
   - **Google 驗證平台 → 品牌／同意畫面**：使用者類型「外部」，填應用程式名稱，把你自己的 Gmail 加進測試使用者。
   - **發布狀態：改成「正式版（In production）」**。這點很重要：停在「測試中」的應用程式，授權過期時間只有 **7 天**，備份會一週後悄悄失效。我們只用 `drive.file` 範圍（不屬於敏感範圍），所以不需要 Google 審核。
   - **用戶端 → 建立用戶端 → 應用程式類型：電腦版應用程式（Desktop app）**，記下用戶端 ID 和密碼。
3. 設定第一個遠端（Drive）：

   ```powershell
   rclone config
   ```

   依序：`n`（新增）→ 名稱 `gdrive` → 儲存類型選 `drive` → `client_id`、`client_secret` 貼上剛才的 → `scope` 選 **`drive.file`**（只能看到 rclone 自己建立的檔案，最小權限）→ 其餘按 Enter → 「Use auto config」選 `y` → 瀏覽器登入你的 Google 並同意 → 「Configure as Shared Drive」選 `n`。
4. 設定第二個遠端（加密層）：

   ```powershell
   rclone config
   ```

   `n` → 名稱 **`gdrive-crypt`**（名稱要一模一樣，腳本找這個）→ 儲存類型 `crypt` → remote 填 `gdrive:uniway-crypt` → 檔名加密選 `standard`、目錄名加密選 `true` → 密碼選 `g`（產生，長度 1024 位元）→ 鹽（salt）也選 `g` → 確認。
5. **把產生的兩組密碼（password 與 salt）寫進密碼管理員。** 沒有它們，Drive 裡的備份**永遠無法解開**；遺失 Jerry 的電腦又同時遺失這兩組密碼，就等於沒有備份。
6. 測試：

   ```powershell
   "hello" | Out-File C:\uniway\t.txt
   rclone copy C:\uniway\t.txt gdrive-crypt:test
   rclone ls gdrive-crypt:test
   ```

   去 Google Drive 網頁看，會有一個 `uniway-crypt` 資料夾，裡面的檔名是亂碼。
7. 再執行一次 `07-setup-backup.ps1`（或直接 `backup.ps1`），看最後有 `copied to Google Drive (encrypted)`。Drive 上的備份保留 120 天，更舊的自動刪除。

---

## 階段 I：資料搬家與切換

### I1. 演練（不改任何東西，可以隨時做）

Supabase 儀表板 → 你的專案 → **Connect** → **Session pooler**：記下 Host（像 `aws-0-ap-southeast-2.pooler.supabase.com`）和 User（像 `postgres.abcdefghijkl`）。**用 Session pooler，不要用 Direct connection**：Direct connection 只有 IPv6，家用網路多半連不上。

```powershell
powershell -ExecutionPolicy Bypass -File .\06-migrate-from-cloud.ps1 `
    -SourceHost aws-0-ap-southeast-2.pooler.supabase.com -SourceUser postgres.專案代碼 -Rehearsal
```

腳本會問資料庫密碼（輸入時看不到字、不會存檔）。它只**計算雲端與本機每張表的筆數**，什麼都不改。

### I2. 切換日（網站停機約 10～20 分鐘）

挑一個使用者少的時段（看使用統計：目前每天約 1,000 個事件，凌晨最安靜）。

| 步驟 | 做什麼 |
|---|---|
| 1 | Jerry 的電腦階段 A～H 都做完、`verify.ps1` 通過、備份與還原測試通過 |
| 2 | **確認文件加密金鑰**：Supabase 的 `exchange_application_form_drafts` 和 `exchange_vault_documents` 如果仍是 0 筆，新產生的金鑰就可以；如果不是 0，在 E1 加 `-UseExistingKeys`，貼上 Render 的 `EXCHANGE_VAULT_MASTER_KEY`，再 `03-start.ps1 -SkipBuild` |
| 3 | **Render：暫停服務**（Render 儀表板 → 服務 → Settings → Suspend Service）。從這刻起使用者暫時進不去，這是為了確保最後一次複製時不再有人寫入 |
| 4 | 執行搬資料（加 `-SkipAnalytics` 可以不搬匿名流量統計，那是最大的兩張表；要保留歷史就不加）：<br>`.\06-migrate-from-cloud.ps1 -SourceHost … -SourceUser …` |
| 5 | 腳本最後會逐表比對筆數，印出 `every table has the same number of rows as the cloud` 才算成功；任何一張表不同，它會中止，**不要繼續** |
| 6 | `verify.ps1` 再跑一次；用你的 Google 帳號登入新網站，確認你原本的帳號、儲存的計畫都在 |
| 7 | 通知使用者新網址 `https://app.你的網域.com` |
| 8 | 把 UptimeRobot 的監測網址改成新網址（或刪掉，Jerry 電腦上已有 5 分鐘一次的健康檢查） |

> **使用者要重新登入一次**：登入狀態是依網址（來源）存的，新網址就是新來源，所以大家要再按一次登入、再勾一次同意條款。他們的帳號、儲存的選校和計畫都會在，因為那些存在資料庫裡，已經搬過來了。**本機收藏**（只存在瀏覽器、沒登入過的人）不會跟著搬。

### I3. 回退（出事了怎麼辦）

- **切換後 14 天內不要刪 Supabase 專案和 Render 服務**，只是暫停。
- 如果新網站出大問題：Render 儀表板 → **Resume Service**，把使用者導回舊網址；Google 登入設定裡舊的返回網址還在，會繼續能用。
- **注意**：切換後在新網站發生的新資料（新帳號、留言、評價）**不會自動回到 Supabase**。如果只是切換後的前幾個小時，損失很小，直接回退即可；如果已經過了幾天才回退，要先從 Jerry 電腦做一次備份，再手動把資料搬回去（我可以寫反向腳本，需要時跟我說）。
- 14 天都正常，就可以把 Supabase 專案暫停（免費方案 7 天沒用會自動暫停，不用管）、刪掉 Render 服務。

---

## 日常維運

### 每週看一下（5 分鐘）

```powershell
cd C:\uniway\app\deploy\selfhost
docker compose ps
Get-Content C:\uniway\logs\health.log -Tail 20
Get-Content (Get-ChildItem C:\uniway\logs\backup-*.log | Sort-Object LastWriteTime | Select-Object -Last 1) -Tail 10
(Get-PSDrive C).Free / 1GB
```

- 五個服務（`db`、`rest`、`storage`、`gateway`、`app`）都應該是 `healthy`。
- `health.log` 沒有新的錯誤行（沒有行就是沒事）。
- 備份日誌最後一行是 `backup finished OK`。
- 磁碟可用空間不要低於 50 GB。

### 更新網站

```powershell
powershell -ExecutionPolicy Bypass -File .\update.ps1
```

先自動備份 → 抓你目前分支的最新程式碼（只做快轉合併，有本機修改擋住時會停下來）→ 重建映像檔 → 套用新的資料庫 migration → 重啟 → 跑一次驗證。**出問題時退回上一版：**

```powershell
powershell -ExecutionPolicy Bypass -File .\update.ps1 -Rollback
```

（只退回程式映像檔；如果那次更新改了資料庫，要用備份還原，見下一節。）

### 憑證與其他自動的事

- HTTPS 憑證 Caddy 自己更新，不用管。
- 排程工作：`UniWay-Caddy`（開機）、`UniWay-Backup`（每天 04:00）、`UniWay-Health`（每 5 分鐘）。用 `Get-ScheduledTask UniWay-*` 查看。
- Docker Desktop 偶爾會提示更新：等到凌晨再更新、更新完確認 `docker compose ps` 都回來。
- Windows Update 後如果重開機：有設自動登入就會自己回來；沒設就要有人登入。

### 使用者要求刪除資料

網站的帳號頁已有「刪除帳號」（會做完整的刪除）。如果有人來信要求，請對方自己登入刪除；備份裡的舊資料會在保留期（最長約 6 個月）過後自然消失。

---

## 災難還原（Jerry 的電腦壞了／被偷了）

你需要：**密碼管理員裡的 `.env` 內容**、**rclone 的兩組密碼**（若備份在 Drive）、一台新的 Windows 電腦。

1. 在新電腦做階段 A（路由器改轉送到新電腦的內網 IP）、C（安裝工具、`git clone`）、D。
2. 把保存的 `.env` 放回 `C:\uniway\app\deploy\selfhost\.env`（**不要重新產生密鑰**，要用原本的）。
3. `03-start.ps1`（起一個空的資料庫）、`05-install-caddy.ps1`。
4. 取回最新備份：
   - 從外接硬碟：把 `uniway-db-*.dump` 複製到 `C:\uniway\backups\db`。
   - 從 Drive：裝 rclone、重新設 `gdrive` 與 `gdrive-crypt`（**用同樣的兩組密碼**）→ `rclone copy gdrive-crypt:uniway-backups C:\uniway\backups`。
5. 還原：

   ```powershell
   cd C:\uniway\app\deploy\selfhost\scripts
   powershell -ExecutionPolicy Bypass -File .\08-restore-backup.ps1            # 用最新的備份
   powershell -ExecutionPolicy Bypass -File .\08-restore-backup.ps1 -Stamp 20261012-040000 -Force   # 指定某一天（資料庫已有帳號時要加 -Force）
   ```

   它會依序：停止網站與檔案儲存 → 清掉目前資料列 → 還原資料庫的資料（`public`）→ 還原「有哪些檔案」的清單 → 還原加密檔案本身（保留檔案的延伸屬性，否則取回時會出 500 錯誤）→ 重新啟動 → 印出還原後的筆數。**它會取代目前資料庫裡的資料**，所以通常只在全新的電腦或要回到某一天時使用。
6. 跑 `verify.ps1`，並用幾個既有帳號登入確認資料都在。
7. DNS：固定 IP 如果換了，要改網域的 A 記錄。

---

## 安全檢查清單（做完後逐項打勾）

- [ ] 路由器只轉送 **80、443**；沒有轉送 3389、22、5432、8000 或其他任何埠；UPnP 關閉。
- [ ] 防火牆規則 `UniWay Caddy web` 存在，且沒有其他自建的「允許所有」規則。
- [ ] `docker compose ps` 裡**只有 `app` 有對主機開放的埠，而且是 `127.0.0.1:8000`**。
- [ ] 從外面 `curl https://app.你的網域.com:8000` 連不上；`…:5432` 連不上。
- [ ] `.env` 只有你、Administrators、SYSTEM 能讀（`icacls deploy\selfhost\.env`）。
- [ ] 磁碟加密已開，復原金鑰已備份。
- [ ] `.env` 內容、rclone 兩組密碼都在密碼管理員。
- [ ] `access.log` 的 `remote_ip` 是訪客真實 IP。
- [ ] 備份已跑過、`restore-test.ps1` 通過、Drive 上看得到亂碼檔名。
- [ ] 遠端連線只透過 VPN／遠端工具，沒有裸露的遠端桌面。
- [ ] `/privacy` 已寫成自架版本，聯絡信箱有填。
- [ ] 不要把任何密鑰貼進聊天室、Email 或這個倉庫。

---

## 疑難排解

| 現象 | 原因／處理 |
|---|---|
| `docker` 指令說連不到引擎 | Docker Desktop 沒在跑。開啟它、等 `Engine running`。若一直閃退，到 `%LOCALAPPDATA%\Docker\log\host\com.docker.backend.exe.log` 看最後的錯誤 |
| `03-start` 卡在 `rest`／`storage` unhealthy | 內部角色密碼沒設好：重新執行 `03-start.ps1 -SkipBuild`（它會重設） |
| 網站程式反覆重啟，日誌寫「正式環境禁止使用本機持久層」 | 往上找真正的錯誤。常見：`Supabase URL 必須使用 https://`（`.env` 或 compose 被改過，URL 必須是 `https://gateway`）、金鑰格式錯 |
| 網站程式日誌寫「the gateway's CA certificate never appeared」 | 閘道還沒產生內部憑證：`docker compose logs gateway`，再 `docker compose up -d ca-export app` |
| migration 失敗 `unexpected forum function definition` | migration 檔被換成 CRLF，或資料庫不是從空的開始。用腳本套（它會轉 LF）；若資料庫是殘留的測試資料，`docker compose down -v` 清空再來（**只能在還沒有真實資料時**） |
| Caddy 拿不到憑證 | DNS 沒指到 Jerry 的 IP（`Resolve-DnsName` 查）；路由器沒轉送 80；電信業者擋 80（用手機行動網路測 `http://網域`）；看 `C:\uniway\logs` 與 `Get-ScheduledTask UniWay-Caddy` |
| 用手機行動網路連得到、在 Jerry 家裡連不到 | 路由器不支援「迴環」（hairpin NAT）。在 Jerry 家用內網 IP 測，或請他在路由器設本機 DNS 覆寫 |
| 瀏覽器說憑證不安全 | 用 IP 連而不是網域；或憑證還沒申請成功（等一分鐘、看 Caddy 日誌） |
| 登入後馬上被登出／登入限流全站一起觸發 | 程式看到的來源 IP 是內網位址：確認 `EXCHANGE_CLIENT_IP_HEADER=X-Client-IP`、Caddy 設定有 `header_up X-Client-IP {remote_host}`、`access.log` 裡 `remote_ip` 是真實 IP |
| `verify.ps1` 的 feedback 項目顯示 SKIP | 用戶評價表單 10 分鐘內只收 3 則，剛剛跑太多次，等 10 分鐘再跑 |
| 網站變慢 | 看 `docker stats`；看磁碟是否快滿；看 `access.log` 有沒有異常大量請求；必要時 `docker compose restart app` |
| 備份日誌寫 `rclone remote "gdrive-crypt" is not set up` | 還沒做 H3，或遠端名稱不是 `gdrive-crypt` |
| 一週後 Drive 備份失敗 | Google 應用程式停在「測試中」，授權 7 天過期。到 Google 驗證平台把發布狀態改成「正式版」，再 `rclone config reconnect gdrive:` |

---

## 附錄

### A. 重要檔案位置

| 位置 | 內容 |
|---|---|
| `C:\uniway\app\` | 程式碼（git 倉庫） |
| `C:\uniway\app\deploy\selfhost\.env` | **所有密鑰（機密）** |
| `C:\uniway\app\deploy\selfhost\docker-compose.yml` | 服務定義 |
| `C:\uniway\caddy\` | Caddy 程式與 `Caddyfile` |
| `C:\uniway\logs\` | `access.log`（網站連線，約 30 天後自動輪替刪除）、`health.log`、`backup-YYYYMM.log`、`rclone.log` |
| `C:\uniway\backups\{db,storage,secrets}\` | 備份 |
| Docker 磁碟區 `uniway_db`、`uniway_storage`、`uniway_gateway`、`uniway_ca_public` | 資料庫、文件、內部憑證 |

### B. 指令速查

```powershell
cd C:\uniway\app\deploy\selfhost
docker compose ps                         # 各服務狀態
docker compose logs app --tail 100        # 看網站日誌
docker compose restart app                # 重啟網站
docker compose up -d                      # 全部啟動（重開機後的保險）
docker stats --no-stream                  # 記憶體與 CPU
.\scripts\verify.ps1                      # 全面檢查
.\scripts\backup.ps1                      # 立刻備份
.\scripts\restore-test.ps1                # 備份還原測試
```

### C. 如果電信業者擋 80／443

- 先打電話問：很多家用方案可以申請解除，或提供「商務／固定 IP」方案時已解除。
- 備案：使用其他連接埠（例如 8443）。要改兩處：路由器轉送 `外部 8443 → 內部 443`，以及 Caddyfile 全域區塊加 `https_port` 設定，並改用 **DNS 驗證**申請憑證（需要把 DNS 託管在支援 API 的服務，並用帶外掛的 Caddy）。使用者網址會是 `https://app.你的網域.com:8443`，Google 返回網址也要含埠。這個備案**沒有在這份套件裡實測**，需要時跟我說。

### D. 如果固定 IP 以後會變

DNS 的 A 記錄要自動更新（DDNS）。很多註冊商提供更新用的網址／API；在 Windows 用一個排程工作每 5 分鐘呼叫它即可。這個也沒有包含在套件裡，需要時跟我說。

### E. 資源用量（我在本機實測）

| 項目 | 數值 |
|---|---|
| 全部服務閒置記憶體 | 約 720 MiB（網站 354、資料庫 85、REST 110、儲存 159、閘道 15） |
| 網站映像檔大小 | 約 1.5 GB（含六校資料） |
| 單一工作程序的處理能力 | 24 個同時連線、混合頁面與 API，每秒約 55 個請求，中位數 168 毫秒，0 個錯誤 |
| 資料庫備份大小 | 目前約 0.7 MB（正式資料庫總共 21 MB） |

### F. 費用

| 項目 | 費用 |
|---|---|
| 網域 | 一年約幾百元 |
| 電費 | 那台電腦本來就開著，多出來的負載很小 |
| 其他（Let's Encrypt、Caddy、Docker、rclone、Git） | 免費 |

### G. 我測過什麼、沒測過什麼

**在本機實際跑過、通過的：**

- 建置映像檔、啟動五個服務、套用全部 31 份 migration、建立私人儲存桶。
- `verify.ps1` 的 23 項檢查（六所學校資料、資料庫讀寫、公開金鑰被擋、儲存桶私密、檔案存取）。
- 備份、還原測試（含 `pg_dump`／`pg_restore`），以及**完整災難還原演練**：存入一個檔案 → 備份 → 把整套服務和磁碟區全部刪光 → 重建一個空的系統 → `08-restore-backup.ps1` → 12 個帳號、1,500 筆統計、儲存的檔案內容完全一致（演練中抓到並修好兩個問題：舊的備份會跟遷移紀錄表衝突；檔案備份沒帶延伸屬性，取回時會出 500）。
- 資料搬家：用一個「假雲端」資料庫（同樣的 migration、放入含繁體中文與 emoji 的測試資料）跑完整的 `06-migrate-from-cloud.ps1`，逐表筆數一致。
- Caddy：下載與檢查碼驗證、設定檔驗證、實際在前面擋一個回聲伺服器，確認訪客自己送的 `X-Client-IP`／`X-Forwarded-For` 會被覆寫成真實連線位址。
- 所有腳本的語法檢查與「純 ASCII」檢查（Windows PowerShell 5.1 讀 BOM 的問題）。
- 隱私權政策兩種版本（Render／自架）的測試。

**我沒辦法在這台電腦上測的（第一次在 Jerry 的電腦上要特別留意）：**

- `01-prepare-windows.ps1` 與 `05`/`07` 的**需要系統管理員的部分**（QoS 限速、防火牆規則、排程工作）：我驗證了指令的參數都合法，但沒有實際以管理員身分建立。
- **對外的真實流量**：路由器轉送、網域 DNS、Let's Encrypt 憑證、電信業者是否擋 80／443、Google 登入的完整流程。
- **QoS 限速的實際效果**：Windows Home 版可能沒有這個功能。
- **rclone 與 Google Drive**：需要你本人登入。
- **Docker Desktop 在 Jerry 那台機器上的行為**（重開機後自動回來、自動登入）。

這些都在階段 F、H 有對應的驗證步驟；請你在每個階段做完都停下來確認，不要一口氣做完才驗證。

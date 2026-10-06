# 把網站部署到網路上（Render + Supabase）

給第一次部署的人。**只要照順序做**；每一步都寫了「做完怎麼確認」。資料庫那邊的設定在 [`supabase-setup-guide.md`](supabase-setup-guide.md)，這份只講「把網站放上主機」。

> 規則只有一條：**任何金鑰、密碼只貼在 Render 或 Supabase 的網頁表單裡**，不要貼進聊天室、不要寫進檔案、不要截圖。

## 先搞懂整體長什麼樣

```
使用者的瀏覽器 ──https──▶ Render（跑這個網站的程式，不存任何資料）
                              │
                              └──▶ Supabase（帳號、貼文、加密文件、使用統計都在這裡）
Google 登入：瀏覽器 ──▶ Google ──▶ 回到你的網站 /auth/oauth/google/callback
```

- **Render** 負責「跑程式」。程式碼從 GitHub 自動拉下來；你每推一次 `main`，它就自動重新部署。
- **Supabase** 負責「存資料」。你已經建好專案、套用過資料表。
- 主機本身不存資料，所以主機重開、換掉都不會掉資料。

## 第 0 步：先決定三件事

| 要決定的 | 建議 | 說明 |
| --- | --- | --- |
| 主機方案 | 先用 **Free** 試，正式對外前改 **Starter** | Free：閒置 15 分鐘會休眠，下一位訪客要等約 1 分鐘。Starter 目前約每月 7 美元（以 [Render 定價頁](https://render.com/pricing) 為準），不休眠。這個網站實測只用約 100 MB 記憶體，512 MB 的方案夠用。 |
| 網址 | 先用 Render 送的 `https://xxx.onrender.com` | 能完整測試。有自己的網域再看第 8 步。 |
| Supabase 方案 | 先用 **Free**，有真實使用者內容後再升 **Pro** | Free 閒置 1 週會被暫停（網站會整個壞掉）、沒有備份、資料庫只有 500 MB。見下面「$0 起步」。 |

### $0 起步：現在完全免費，付錢的時機看這裡

GitHub、Render Free、Supabase Free、Google 登入、`onrender.com` 網址，全部是 0 元。代價是這幾件事（依 [Supabase 定價頁](https://supabase.com/pricing) 與 [Render 免費方案說明](https://render.com/docs/free)）：

| 免費的限制 | 影響 | 免費的解法 |
| --- | --- | --- |
| Render Free 閒置 15 分鐘會休眠 | 下一位訪客要等約 1 分鐘 | 測試期告訴使用者「第一次開比較慢」 |
| Supabase Free 閒置 1 週會暫停 | 整個網站壞掉，要到後台按 Restore | 每週至少有人開一次；每週看一眼後台 |
| Supabase Free **沒有備份** | 資料庫出事就沒了 | 每週自己備份一次：`npx supabase@latest db dump -f backup.sql` |
| Supabase Free 資料庫只有 500 MB、流量 5 GB／月 | 使用統計是最可能先塞滿的表（實測一筆事件約 0.6 KB，資料庫裡含索引會更大） | 在 Render 的 Environment 加 `EXCHANGE_ANALYTICS_RETENTION_DAYS` = `30`（程式的最小值就是 30，預設是 400） |

**什麼時候才付錢**（每一項都是出現徵兆才升級，不用預先付）：

1. **使用者開始發文、存申請進度** → 先升 Supabase Pro（約每月 25 美元起，預設開花費上限）。理由是備份與不暫停：資料掉了就找不回來，這是最大的風險。
2. **有人抱怨第一次載入太慢** → Render 升 Starter（約每月 7 美元）。
3. **想在 Google 登入畫面顯示 App 名稱與標誌**（品牌驗證）→ 買自己的網域（`.com` 通常每年約 10 美元）。

全部都升上去，最多大約每月 32 美元加網域每年約 10 美元。

## 第 1 步：確認程式在 GitHub 上是最新的

Render 只讀 GitHub 上 `main` 的內容，所以本機的改動要先推上去。部署需要的檔案是：

- `render.yaml`：告訴 Render 怎麼安裝、怎麼啟動、要哪些設定。
- `.python-version`：把 Python 固定在 3.12（測試用的版本；Render 新服務預設是 3.14，沒測過）。
- `src/exchange_info/request_origin.py`：讓程式在 Render 的代理後面，還能看到正確的網址與訪客（下面「為什麼要這個」）。

**做完怎麼確認**：開 https://github.com/blizzard-new/abroad ，看得到 `render.yaml` 在根目錄。

## 第 2 步：換掉 Supabase 的 Secret key，並檢查設定

你之前把 Secret key 貼進過聊天室，視為外洩，上線前一定要換。

1. Supabase 後台 → **Project Settings → API Keys → Secret keys**，建立一把新的，**複製到密碼管理器**，再把舊的刪除。
2. 同一頁複製 **Project URL**（`https://xxxxxxxx.supabase.co`）。
3. 在 PowerShell 檢查新金鑰能用（逐段貼，**Read-Host 那一段單獨貼**）：

```powershell
cd "C:\Users\User\OneDrive\文件\留學"
$env:EXCHANGE_SUPABASE_URL = "https://你的專案代號.supabase.co"
```

```powershell
$env:EXCHANGE_SUPABASE_SECRET_KEY = [Net.NetworkCredential]::new('', (Read-Host "貼上新的 Secret key" -AsSecureString)).Password
```

```powershell
.venv\Scripts\python.exe scripts\check_supabase_setup.py
```

**做完怎麼確認**：資料表、儲存桶那幾項都是 ✓。關於密鑰、網址的 ⚠ 可以忽略（那是本機沒設，Render 上會設）。有 ✗ 先照畫面提示修。

## 第 3 步：產生兩把密鑰

網站需要兩把隨機密鑰，各 32 bytes。**分兩次執行，各貼進密碼管理器存起來**（輸出就是密鑰本人）：

```powershell
.venv\Scripts\python.exe -c "import secrets,base64;print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('='))"
```

- 第一把：`EXCHANGE_VAULT_MASTER_KEY`（加密文件用）。**一旦有人上傳過文件就不能換**，換了舊文件就解不開。
- 第二把：`EXCHANGE_EMAIL_VERIFICATION_SECRET`。

如果你之前測試時已經上傳過**真的**文件到文件庫，先告訴我，那把密鑰要沿用舊的。

## 第 4 步：在 Render 建立網站

1. 到 https://render.com 註冊，用 **GitHub 登入**最省事。
2. 右上 **New +** → **Blueprint**。
3. 授權 Render 讀你的 GitHub：選 `blizzard-new/abroad`（私人倉庫，要在授權畫面把它勾進去）。
4. Render 讀到 `render.yaml` 後，會列出服務 `uniway`，並請你填幾個**機密**（`sync: false` 的那幾項）：

   | 欄位 | 填什麼 |
   | --- | --- |
   | `EXCHANGE_SUPABASE_URL` | 第 2 步的 Project URL |
   | `EXCHANGE_SUPABASE_SECRET_KEY` | 第 2 步新的 Secret key |
   | `EXCHANGE_VAULT_MASTER_KEY` | 第 3 步第一把 |
   | `EXCHANGE_EMAIL_VERIFICATION_SECRET` | 第 3 步第二把 |
   | `EXCHANGE_CONTENT_ADMIN_EMAILS` | 你自己的 Gmail（看統計儀表板用，可留空之後再加） |

5. 按 **Apply / Deploy Blueprint**。

## 第 5 步：等它跑起來，然後驗收

Render 會先安裝（約 1–3 分鐘），再啟動。服務頁面上方會有網址 `https://uniway-xxxx.onrender.com`，點進去看 **Logs**。

**做完怎麼確認**（把 `你的網址` 換成實際網址）：

1. `你的網址/health` → 看到 `{"status":"ok", …}`。
2. 首頁打得開，點進「學校搜尋」看得到合作校清單，打開一所學校，右上的學校照片有顯示。
3. 學校頁的「出發前提醒」分頁有內容。
4. `你的網址/auth/providers` → 現在 `"enabled":false` 是正常的（還沒設 Google）。

啟動失敗時，看 Logs 的最後幾行：

| Logs 說 | 原因與處理 |
| --- | --- |
| `正式環境禁止使用本機持久層` | 某個 `EXCHANGE_*_BACKEND` 或 Supabase 網址／金鑰沒設對。到 **Environment** 頁檢查，儲存後會自動重新部署。 |
| `EXCHANGE_VAULT_MASTER_KEY 必須是 base64url` 或 `解碼後必須是 32 bytes` | 第 3 步貼錯了：多了空白、換行，或沒貼完整。重貼。 |
| `Supabase URL 與 secret key 必須同時設定` | 兩個欄位有一個是空的。 |
| 安裝階段失敗 | 把 Logs 最後 30 行貼給我（**先確認裡面沒有金鑰**）。 |

## 第 6 步：Google 登入

目標：任何人都能用 Google 帳號登入，不限 100 人。

1. Google Cloud 主控台 → **Google Auth Platform → 用戶端（Clients）→ 建立用戶端**，應用程式類型選 **網頁應用程式**。（舊版介面在 **API 和服務 → 憑證 → 建立憑證 → OAuth 用戶端 ID**，畫面文字可能和這裡略有不同，找「網頁應用程式」那個類型就對了。）
2. **已授權的重新導向 URI** 填（一字不差，換成你的網址）：
   `https://uniway-xxxx.onrender.com/auth/oauth/google/callback`
3. 建立後拿到 **用戶端 ID** 與 **用戶端密碼**。
4. Render → 你的服務 → **Environment** → 新增兩個變數：`GOOGLE_OAUTH_CLIENT_ID`、`GOOGLE_OAUTH_CLIENT_SECRET`，存檔。Render 會自動重新部署（約 1–2 分鐘）。
5. **先在 Render 加一個變數** `EXCHANGE_CONTACT_EMAIL` = 你要公開給使用者的聯絡信箱。網站的隱私權政策（`/privacy`）與使用條款（`/terms`）會顯示它；沒設的話，頁面會寫「尚未設定聯絡信箱」。
6. **填 Google 的 Branding 頁**（Google Auth Platform → Branding）。要切到「正式版」，Google **要求**以下欄位（按鈕灰色、滑鼠移上去會寫缺什麼）：
   - Application home page：`https://uniway-xxxx.onrender.com/`
   - Application privacy policy link：`https://uniway-xxxx.onrender.com/privacy`
   - Application terms of service link：`https://uniway-xxxx.onrender.com/terms`
   - Authorized domains：`uniway-xxxx.onrender.com`（`onrender.com` 在公開網域清單上，所以你的完整子網域本身就是一個頂層私有網域；Google 是否接受要實際試，被拒絕就貼畫面給我）
   - **App logo 先不要上傳**：頁面警告，上傳後正式版要送審核。
   - 首頁、隱私權政策、服務條款要在**同一個網域**，首頁要連得到隱私權政策（網站頁尾已有連結）。
7. **Audience 頁按 Publish app**，狀態變成 In production。
   - 只要求 `openid email profile` 時，依 [Google 的說明](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview)，發布後任何 Google 帳號都能登入，不受 100 人限制；沒有品牌驗證時，同意畫面**不會顯示 App 名稱與標誌**，這不影響登入。
   - 想顯示 App 名稱與標誌，需要自己的網域加「品牌驗證」，可以之後再做。
   - 在你按下 Publish 之前，也可以先停在「測試中」：到 **Audience → Test users** 加入 Gmail，最多 100 位測試使用者可以登入。

**登入前要勾選同意**：網站的登入視窗在「使用 Google 繼續」上面有一個勾選框「我已閱讀並同意使用條款與隱私權政策」，沒勾選就不會前往 Google，伺服器端也會擋（`/auth/oauth/.../start` 沒帶 `terms=<版本>` 會被導回登入視窗）。版本號是 `src/exchange_info/legal_pages.py` 的 `TERMS_VERSION`，必須和兩個頁面頂端的「更新日期」、`index.html` 勾選框的 `data-terms-version` 一致（有測試檢查）。改了條款或隱私權政策、想讓大家重新同意，就把這三處一起改成新日期。目前**沒有**把「誰在什麼時候同意了哪個版本」存進帳號資料，只有「進入登入流程前一定勾選過」這個保證。

**做完怎麼確認**：`你的網址/auth/providers` 的 `google` 變成 `"enabled":true`；用一個沒加進測試名單的 Gmail 登入成功。

| 現象 | 處理 |
| --- | --- |
| Google 說 `redirect_uri_mismatch` | 第 2 點的網址和網站實際網址不一致（`https`、結尾、大小寫都要一樣）。 |
| 登入按鈕是灰的 | 第 4 點兩個變數有一個沒設，或存檔後還沒部署完。 |
| 很多人同時登入失敗 | 登入啟動有限流（同一個 IP 10 分鐘 20 次）。確認 Render 的 **Environment** 裡 `EXCHANGE_CLIENT_IP_HEADER` 是 `CF-Connecting-IP`（`render.yaml` 已設）。 |

## 第 7 步：管理員與使用統計

`EXCHANGE_CONTENT_ADMIN_EMAILS` 裡的信箱登入後，開 `你的網址/admin/analytics` 看統計。統計預設保留 400 天，不存 IP 與帳號。**隱私權政策必須寫明有蒐集匿名使用統計**（見第 9 步）。

## 第 8 步：換成自己的網域（可以之後再做）

1. 買網域（網域註冊商都行；`.com` 通常每年約 10 美元）。
2. Render → 服務 → **Settings → Custom Domains** → 加入網域，照畫面指示到註冊商的 DNS 設定新增紀錄。Render 會自動辦 HTTPS 憑證。
3. 在 Render 的 **Environment** 新增 `EXCHANGE_PUBLIC_BASE_URL` = `https://你的網域`（不要結尾斜線）。**不做的話** Google 登入返回網址與學校照片連結還會指向舊的 onrender.com。
4. Google 憑證頁的重新導向 URI **再加一條** `https://你的網域/auth/oauth/google/callback`。

## 第 9 步：正式對外前的清單

- [ ] **隱私權政策與服務條款**：網站已有 `/privacy` 與 `/terms`（內容依程式實際行為寫成，**不是律師審過的法律文件**）。公開宣傳前請自己讀過一遍，確認每一句都是你的決定（例如「不用於廣告、不販售」、條款裡的免責範圍），有疑慮請專業人士看過。聯絡信箱靠 `EXCHANGE_CONTACT_EMAIL`。
- [ ] **誰管留言**：公共板對所有 Google 帳號開放，要有人處理檢舉。管理員用 `EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS` 指定。
- [ ] **用長庚與北大的真實信箱各登入一次**：學校的信箱可能不是 Google 帳號，或被學校擋第三方登入。
- [ ] **Supabase 升級付費並確認備份**。
- [ ] **Render 改成 Starter**，才不會讓第一位訪客等一分鐘。
- [ ] 資料底部那行「資料整理自各校官方公告，仍在逐筆人工核對」保持清楚，兩校 116 學年度流程**還沒人工核對**。

## 為什麼要有 `request_origin.py`（技術說明）

Render 前面有 Cloudflare 與負載平衡器，程式只看得到它們：

1. **訪客位址**：登入啟動有「每個 IP 10 分鐘 20 次」的限流。沒處理的話，全站訪客看起來是同一個 IP，**整個網站每 10 分鐘只有 20 個人能開始登入**。Render 自己的說明寫，Cloudflare 會寫入並覆蓋 `CF-Connecting-IP`，所以這個值可信；`X-Forwarded-For` 最左邊那筆可以被訪客自己偽造，所以不用它。程式只在設了 `EXCHANGE_CLIENT_IP_HEADER` 時才讀那個標頭，沒設就忽略，本機執行不受影響。
2. **對外網址**：程式以為自己跑在 `http`，學校照片的絕對網址會變成 `http://…`，在 https 頁面被瀏覽器擋掉。現在改用 `EXCHANGE_PUBLIC_BASE_URL`，沒設就用 Render 自動提供的 `RENDER_EXTERNAL_URL`。

## 之後的日常

- **更新網站**：推到 GitHub 的 `main`，Render 自動重新部署，約 2–3 分鐘。服務頁的 **Events** 可以看部署紀錄；新版有問題時，Render 提供回復到前一次部署（Rollback）的功能，畫面位置以 Render 當時的介面為準。
- **看錯誤**：服務頁的 **Logs**。
- **換 Secret key**：Supabase 重新產生，更新 Render 的 `EXCHANGE_SUPABASE_SECRET_KEY`。`EXCHANGE_VAULT_MASTER_KEY` 不能換。
- **每日排程**（`exchange-info cleanup-document-vault`、`exchange-info run-notifications`）：第一次上線可以先不設，要寄提醒信時再設定（Render 的 Cron Job，另外計費，且要先設定寄信的 SMTP）。

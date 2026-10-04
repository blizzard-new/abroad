# Supabase 一步一步設定

目標：把這個網站的帳號、貼文、文件、統計都放到你自己的 Supabase 專案，並確認設定正確。約 30–40 分鐘。後台選單名稱可能和這裡差一兩個字，找關鍵字即可。

**先講清楚幾件事**
- 網站有自己的登入（Google），**不要**用 Supabase 的 Auth 功能。網站的後端用一把「Secret key」直接讀寫資料庫；瀏覽器完全碰不到資料庫（所有資料表都開了 RLS，並撤銷了瀏覽器角色的權限）。
- 金鑰、密碼不要貼到聊天室、截圖或 Git。要貼，貼到密碼管理員或主機的 Secrets 設定。
- 我沒有在你的真實專案上跑過，這份是照程式碼與 migration 寫的；第 6 步的檢查指令會告訴你哪裡不對。

---

## 第 1 步：建立專案

1. 到 https://supabase.com 登入（可用 GitHub 或 Email），點 **New project**。
2. **Name**：`uniway`（隨意）。
3. **Database password**：按 Generate 產生一組強密碼，**馬上存進密碼管理員**。第 4 步會用到，忘了只能重設。
4. **Region**：選離台灣近的 **Northeast Asia (Tokyo)** 或 **Southeast Asia (Singapore)**。建好後不能改。
5. **Plan**：
   - 先測試：Free 就可以。
   - 正式上線：建議付費方案。免費專案閒置約一週會被暫停（網站會整個壞掉），也沒有每日自動備份；付費方案有每日備份。
6. 其他選項維持預設（**Data API 要保持開啟**，後端靠它存取）。按 Create，等 1–2 分鐘。

## 第 2 步：拿到三個值

在專案後台左下角 **Project Settings**：

| 要的東西 | 在哪裡 | 長什麼樣 | 用途 |
| --- | --- | --- | --- |
| Project URL | Data API 或 General 頁 | `https://xxxxxxxx.supabase.co` | 後端連線；其中 `xxxxxxxx` 是第 4 步的 project ref |
| Secret key | **API Keys** → Secret keys | `sb_secret_...` | **只給後端**，等於資料庫的最高權限 |
| Publishable key | **API Keys** → Publishable key | `sb_publishable_...` | 只在第 6 步用來證明「公開金鑰讀不到資料」，網站本身不需要 |

如果你的專案只顯示舊式金鑰（Legacy API keys 頁籤的 `anon` 與 `service_role`），後端用 `service_role` 那把，效果一樣；程式兩種都接受。

## 第 3 步：建立私人儲存桶

使用者的加密文件會放在這裡（內容在存進去之前就加密了）。

1. 左側 **Storage** → **New bucket**。
2. 名稱**完全照打**：`exchange-private-vault`。
3. **Public bucket 一定要關閉**（預設是關的）。其他欄位不用填，不需要建立任何 policy。
4. Create bucket。

## 第 4 步：把資料表建起來（migration）

專案裡 `supabase/migrations/` 有 26 份 SQL，依檔名順序執行就會建好所有資料表、權限、函式與統計檢視。用 Supabase 的命令列工具一次套用最不容易出錯。

在 PowerShell 執行（需要已安裝 Node.js；你的電腦有）。為了避開 OneDrive 同步與中文路徑造成的問題，先複製到英文路徑：

```powershell
mkdir C:\exchange-supabase
xcopy "C:\Users\User\OneDrive\文件\留學\supabase" "C:\exchange-supabase\supabase" /E /I
cd C:\exchange-supabase
```

```powershell
npx supabase@latest login
```
會打開瀏覽器請你授權，完成後回到 PowerShell。

```powershell
npx supabase@latest init
```
如果問你要不要產生 VS Code / IntelliJ 設定，都回答 `N`。

```powershell
npx supabase@latest link --project-ref xxxxxxxx
```
把 `xxxxxxxx` 換成你 Project URL 裡的那段；它會問資料庫密碼，貼第 1 步存的那組。

```powershell
npx supabase@latest db push --dry-run
```
這一步**只列出**將要套用的檔案，應該看到 26 份，第一份是 `202607190001_ai_rag.sql`、最後一份是 `20261003110000_analytics.sql`。（`ai_rag` 是之後 AI 功能用的，現在用不到，但無害，也是驗證時一併套用的。）

```powershell
npx supabase@latest db push
```
輸入 `Y` 確認，會逐份顯示 `Applying migration ...`。**全部成功才算完成**；中途出現紅色錯誤就停下，把錯誤訊息整段留著（先不要重跑，把訊息給我）。

如果出現連線逾時、`no route to host` 之類的錯誤（多半是網路不支援 IPv6），改用 `npx supabase@latest --dns-resolver https db push` 再試。

> 不想用命令列的備案：後台 **SQL Editor** → New query，依檔名順序，一份一份把 SQL 檔的全部內容貼進去按 Run（共 26 份，最大的有兩千多行）。這樣不會記錄套用歷史，之後不要再用 `db push`。

## 第 5 步：設定環境變數

這些值**在你放網站的主機的 Secrets／Environment 設定裡填**（還沒挑主機的話，先在本機 PowerShell 設定來測試）。下面是本機測試用的寫法：

```powershell
$env:EXCHANGE_SUPABASE_URL = "https://xxxxxxxx.supabase.co"
$env:EXCHANGE_SUPABASE_SECRET_KEY = "sb_secret_..."          # 第 2 步的 Secret key
$env:EXCHANGE_ACCOUNT_REPOSITORY = "supabase"
$env:EXCHANGE_VAULT_BACKEND = "supabase"
$env:EXCHANGE_FORM_DRAFT_BACKEND = "supabase"
$env:EXCHANGE_EMAIL_VERIFICATION_BACKEND = "disabled"        # 只用 Google 登入，不寄驗證信
```

兩把要自己產生的密鑰（**產生後立刻存進密碼管理員**；`VAULT_MASTER_KEY` 弄丟，使用者存的文件就永遠打不開）：

```powershell
$key = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Fill($key)
$env:EXCHANGE_VAULT_MASTER_KEY = [Convert]::ToBase64String($key)

$secret = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Fill($secret)
$env:EXCHANGE_EMAIL_VERIFICATION_SECRET = [Convert]::ToBase64String($secret).TrimEnd('=').Replace('+','-').Replace('/','_')
```

網站本身的設定：

```powershell
$env:GOOGLE_OAUTH_CLIENT_ID = "..."                          # Google Cloud 建立的 OAuth 用戶端
$env:GOOGLE_OAUTH_CLIENT_SECRET = "..."
$env:EXCHANGE_PUBLIC_BASE_URL = "https://你的網域"            # 正式上線的網址
$env:EXCHANGE_CONTENT_ADMIN_EMAILS = "你的gmail@gmail.com"   # 看統計儀表板的人，逗號分隔
```

正式上線的主機要再加 `EXCHANGE_ENVIRONMENT=production`（會強制 HTTPS Cookie 與 Supabase）。**本機測試先不要加**：本機是 http，加了之後登入的 Cookie 會失效。

## 第 6 步：檢查有沒有設對

在**同一個 PowerShell 視窗**（環境變數還在）、專案資料夾執行：

```powershell
cd "C:\Users\User\OneDrive\文件\留學"
.venv\Scripts\python.exe scripts\check_supabase_setup.py --anon-key "sb_publishable_..."
```

會逐項印出 ✓ / ⚠ / ✗，每個 ✗ 下面有該怎麼修。它檢查：網址格式、後端金鑰被接受、全部資料表都在、統計函式可呼叫、儲存桶存在且不公開、公開金鑰讀不到帳號資料表，以及第 5 步各項環境變數。**全部沒有 ✗ 才往下。**

也可以在後台 **SQL Editor** 貼這兩段，自己再確認一次：

```sql
-- 專案的資料表是否都開了 RLS：兩個數字要相等
select count(*) as tables, count(*) filter (where c.relrowsecurity) as with_rls
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r'
  and (c.relname like 'exchange_%' or c.relname like 'application_workflow_issue_report%');

-- 瀏覽器角色有沒有任何資料表權限：應該是 0 列
select table_name, grantee, privilege_type from information_schema.role_table_grants
where table_schema = 'public' and grantee in ('anon', 'authenticated')
  and (table_name like 'exchange_%' or table_name like 'application_workflow_issue_report%');
```

## 第 7 步：在本機實際跑一次

仍在同一個 PowerShell 視窗（本機不要設 production）：

```powershell
.venv\Scripts\python.exe -m uvicorn exchange_info.api:app --port 8000
```

1. 瀏覽器開 http://127.0.0.1:8000 ，逛幾頁、打開一所學校、搜尋一次。
2. 到 Supabase 後台 **Table Editor** → `exchange_analytics_events`：約 5 秒後應該有幾筆資料（`visitor_id` 是隨機字串，沒有 IP 或帳號）。
3. 設好 Google 登入的話，登入一次，再看 `exchange_accounts` 有一筆你的帳號。
4. 用 `EXCHANGE_CONTENT_ADMIN_EMAILS` 裡的信箱登入後，開 http://127.0.0.1:8000/admin/analytics 看得到儀表板。

## 第 8 步：上線後的日常

- **備份**：付費方案會自動每日備份；免費方案沒有，至少每週執行一次 `npx supabase@latest db dump -f backup.sql` 自己存一份。
- **每日排程**（在主機的排程功能設定）：`exchange-info cleanup-document-vault`（清掉過期的加密文件）與 `exchange-info run-notifications`（寄出截止日提醒）。
- **使用統計**：預設保留 400 天，程式會自動清除。
- **換金鑰**：Secret key 外洩時，到 API Keys 頁重新產生，更新主機的環境變數即可。`EXCHANGE_VAULT_MASTER_KEY` **不能換**，換了舊文件就解不開。
- **不要做**：在後台手動改資料表的 RLS／權限、改 `storage` 的設定、啟用 Supabase Auth、把 Secret key 放進任何網頁或 App。

## 常見問題

| 現象 | 原因與處理 |
| --- | --- |
| 檢查指令說「Supabase 拒絕了這把後端金鑰」 | 複製時多了空白或換行；或貼成了 Publishable key。重新複製 Secret key。 |
| 檢查指令說缺資料表 | 第 4 步沒套完。重新執行 `db push`（已套用的不會重複）。 |
| 啟動時說「正式環境禁止使用本機持久層」 | production 模式下某一項還在用本機儲存：檢查第 5 步的 `EXCHANGE_ACCOUNT_REPOSITORY`、`VAULT_BACKEND`、`FORM_DRAFT_BACKEND` 都是 `supabase`，URL 與 Secret key 有設。 |
| 啟動時說缺 `EXCHANGE_EMAIL_VERIFICATION_SECRET` 或 `EXCHANGE_VAULT_MASTER_KEY` | 第 5 步的兩把密鑰沒設。 |
| 網站突然全部壞掉，後台顯示 Paused | 免費專案閒置被暫停；在後台按 Restore。正式上線請用付費方案。 |
| 文件上傳失敗 | 儲存桶名稱不對或是公開的；檢查第 3 步。 |
| `db push` 連線逾時 | 網路不支援 IPv6，見第 4 步最後的 `--dns-resolver https`。 |

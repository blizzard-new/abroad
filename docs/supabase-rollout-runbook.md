# Supabase 擴充套用與驗收（待你執行）

> 第一次設定請先看 [`supabase-setup-guide.md`](supabase-setup-guide.md)（一步一步的操作與檢查指令 `scripts/check_supabase_setup.py`）。這份是技術背景與驗收清單。

狀態：**尚未套用，也尚未在隔離 runtime 實跑。** 這份只整理已在本機確認的事實與你要做的步驟。套用到正式專案需要你的專案憑證與決定，不能由開發工具代做。

## 已在本機確認

- `scripts/validate_supabase_migrations.py`：26 份 migration 全部可解析（545 個 statement、11 個 SQL body、65 個 PL/pgSQL 單元，pglast）。`tests/test_supabase_migration_syntax.py` 的預期數字已更新為這個結果。
- 最新的 `20261002120000_workspace_selection_and_planning.sql` 只檢查「工作區層級」欄位白名單；`selection_conditions.profile` 只要求是 object 或 null。因此 2026-10-02 新增的 `preferred_teaching_language`、`course_interests` 兩個條件欄位**不需要新 migration**。
- 任務設定（`preparation_tasks`）、文件對應與工時沿用既有欄位；本輪沒有新增資料表或 RPC。

- 2026-10-03 新增兩份 migration，**都只通過語法解析，還沒在任何 PostgreSQL 實跑**：
  - `20261003100000_open_school_boards.sql`：把 `exchange_commit_public_community_content` 與 `exchange_set_community_reaction` 兩個函式重新定義，只拿掉學校板的校籍檢查（任何 email 已驗證的帳號可在學校板發文、留言、按讚）。問答、分享心得、聊天仍限已驗證學生；用校名署名仍須驗證。內部函式 `exchange_commit_public_community_content` 維持任何角色都不能直接呼叫。
  - `20261003110000_analytics.sql`：兩張資料表（`exchange_analytics_events`、`exchange_analytics_api_hourly`，皆開 RLS 並強制，瀏覽器角色沒有任何權限）、兩個只給 service role 的函式（`exchange_analytics_add_api_hourly`、`exchange_analytics_purge`）、六個每日彙總檢視（`security_invoker`）。說明見 `docs/analytics.md`。

## 還沒做

1. 隔離 runtime 驗證：`scripts/validate_supabase_runtime.py` 需要 Docker Desktop，並拉取 `supabase/runtime-validation/docker-compose.yml` 指定的固定版本映像（PostgreSQL 17.6、兩個 PostgREST、Storage API）。本機目前 Docker 未啟動；拉取映像是大型下載，所以沒有擅自執行。要跑時先啟動 Docker Desktop，再執行：

   ```bash
   uv run --frozen python scripts/validate_supabase_runtime.py
   ```

   通過條件：`status=passed`、`cleanup_status=passed`，之後 container／network／volume 皆為 0。
2. 正式專案套用與驗收（以下由你執行）。

## 套用到正式專案前

1. 在 Supabase 後台建立資料庫備份（或確認 PITR 已開）。
2. 確認已套用的最後一份 migration 版本，只補套用缺少的，**按檔名時間順序**。
3. 先在 staging 專案（若有）完整走一次；沒有 staging 時，先在新建的空專案跑一次，確認 26 份依序成功。
4. 確認應用程式的 service-role 金鑰只存在伺服器環境變數，瀏覽器沒有。

## 正式環境需要的環境變數

`EXCHANGE_ENVIRONMENT=production`、`EXCHANGE_SUPABASE_URL`（https）、`EXCHANGE_SUPABASE_SECRET_KEY`（只放伺服器）、`EXCHANGE_ACCOUNT_REPOSITORY=supabase`、`EXCHANGE_VAULT_BACKEND=supabase`、`EXCHANGE_FORM_DRAFT_BACKEND=supabase`、`EXCHANGE_VAULT_MASTER_KEY`、`EXCHANGE_EMAIL_VERIFICATION_SECRET`、`EXCHANGE_EMAIL_VERIFICATION_BACKEND`（Google 登入不需要寄信，可設 `disabled`）、`EXCHANGE_PUBLIC_BASE_URL`、`GOOGLE_OAUTH_CLIENT_ID`、`GOOGLE_OAUTH_CLIENT_SECRET`、`EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS` 或 `EXCHANGE_CONTENT_ADMIN_EMAILS`。登入方式預設只開 Google（`EXCHANGE_AUTH_METHODS`），功能預設全部免費（`EXCHANGE_PRODUCT_RELEASE_MODE=closed_beta`，不要改成 `public`）。使用統計預設開啟並使用 Supabase；缺 Supabase 設定程式會拒絕啟動，除非設 `EXCHANGE_ANALYTICS=off`。

## 套用後驗收清單

- [ ] 所有 `exchange_*` 資料表啟用 RLS，`anon` 與 `authenticated` 沒有直接 table grant。
- [ ] 敏感表（私人文件、通知、社群私訊）無法直接 DELETE。
- [ ] 工作區寫入：兩個裝置以同一 revision 同時儲存，只有 1 個成功、1 個得到 conflict。
- [ ] 帳號切換選校條件後，另一台裝置讀到同一份（含新欄位：偏好授課語言、想修的領域）。
- [ ] 舊版客戶端（沒有新欄位）寫入不會清掉新欄位。
- [ ] 學校板：一個沒驗證學生身分、但 email 已驗證的帳號，能在長庚板與北大板發文、留言、按讚；用「長庚大學學生」署名會被拒絕；email 未驗證的帳號被拒絕；問答與分享心得對未驗證帳號仍被拒絕。
- [ ] 使用統計：開網站瀏覽幾頁後，`exchange_analytics_events` 出現資料（`visitor_id` 是隨機代號、沒有 IP 或帳號 ID）；`exchange_analytics_api_hourly` 約一分鐘內出現請求計數；六個 `exchange_analytics_*_daily` 檢視能查詢；`anon` 與 `authenticated` 角色讀不到這兩張表；管理員開 `/admin/analytics` 看得到報告，一般帳號被拒絕。
- [ ] 加密文件庫：上傳、下載、永久刪除、同意撤回後無法下載。
- [ ] 通知：content_update 通知只在人工發布後產生一次。
- [ ] 刪除帳號後私人資料清除、公開貼文去識別。
- [ ] Storage 實際 backend 的刪除與孤兒物件清理（`exchange-info cleanup-document-vault`）。

## 回復

- migration 都是向前相容的新增；若套用後發現問題，先停止寫入（維持 single worker），用備份還原到套用前，再回報失敗的 migration 檔名與錯誤。
- 在正式驗收完成前，產品維持 `NOT READY`，也不開放 App 同步。

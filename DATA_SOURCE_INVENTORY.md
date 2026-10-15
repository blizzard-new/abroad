# Uniway 全平台資料來源與儲存位置盤點報告（DATA_SOURCE_INVENTORY）

> **盤點基準日**：`2026-10-15`  
> **GitHub Repository**：`https://github.com/blizzard-new/abroad`（基準分支：`main` @ `d7c9ab06`）  
> **實際部署架構**：Windows Server 自架伺服器（Self-hosted Docker Compose：`C:\uniway\app\deploy\selfhost\docker-compose.yml`）

---

## 一、自架伺服器（Self-Hosted）架構與執行環境盤點

本平台已完全採用**自行架設伺服器（Self-hosted）**架構運作，**不再使用任何外部雲端託管之 Supabase Cloud、Firebase 或 Render 資料庫**。

### 1. 容器服務拓撲（`deploy/selfhost/docker-compose.yml`）

| 容器名稱 | 映像檔 / 技術棧 | 內部連接埠 | 角色與資料職責 | 目前狀態 |
|---|---|---|---|---|
| `uniway-app-1` | Python 3.12 + FastAPI (`uvicorn`) | `8000` | 核心前後端 API 與靜態頁面伺服器；掛載 `/data` 持久化目錄與程式碼內建 `src/exchange_info/official_data/` | Healthy |
| `uniway-gateway-1` | Nginx (`deploy/selfhost/nginx.conf`) | `80` | 反向代理閘道，將 `/auth/v1/*`、`/rest/v1/*`、`/storage/v1/*` 路由至自架服務，其餘導向 `uniway-app-1` | Healthy |
| `uniway-rest-1` | `postgrest/postgrest:v12.2.3` | `3000` | 提供自架 PostgreSQL 之 RESTful 存取層（僅開放已授權之 Schema 與 RLS 保護表） | Healthy |
| `uniway-storage-1` | `supabase/storage-api:v1.11.13` | `5000` | 自架檔案與附件儲存服務（底層掛載本地 Volume `uniway_storage-data`） | Healthy |
| `uniway-db-1` | `supabase/postgres:15.8.1.060` | `5432` | 自架 PostgreSQL 15.8 主資料庫（含 `public`、`auth`、`storage` Schema 共 45 張資料表） | Healthy |
| `uniway-cloudflared` | Cloudflare Tunnel | Host | 對外 HTTPS 安全通道，無直接暴露資料庫埠號 | Running |

### 2. 安全唯讀存取方式與權限邊界

- 本次查核透過本機 Docker Exec 唯讀查詢（`psql -U postgres -d postgres` 之 `SELECT` 語句）檢視自架 PostgreSQL 資料庫內容，**未對正式環境資料庫執行任何 `INSERT` / `UPDATE` / `DELETE` / `ALTER` 操作**。
- 所有資料庫層級之修正均封裝為可重複執行（Idempotent）、具交易保護與回復說明之 SQL Migration（`supabase/migrations/20261015130000_cleanup_synthetic_maintenance_demo_data.sql`），並透過 **PR #33** 提交審查。

---

## 二、自架 PostgreSQL 資料庫（`uniway-db-1`）完整資料表與筆數盤點

經唯讀查核 `uniway-db-1`，目前資料庫共包含 **45 張資料表**（`public` 35 張、`auth` 7 張、`storage` 3 張）：

### 1. 交換內容治理與知識庫資料表（`public` Schema）

| 資料表名稱 | 正式環境筆數 | 用途與結構說明 | 前台讀取關係 |
|---|---:|---|---|
| `public.application_workflow_revisions` | `1,073` | 6 校申請工作流（Application Workflows）治理歷史與發布快照 | 與 `official_data/*/application_workflows.jsonl` 雙向對應 |
| `public.destination_profile_revisions` | `1,179` | 6 校交換目的地生活指南（Destination Profiles）治理歷史與發布快照 | 與 `official_data/*/destination_profiles.jsonl` 雙向對應 |
| `public.document_chunks` | `0` | RAG 向量檢索切塊表（目前自架環境預設關閉外部付費 AI/Embedding） | 僅內部檢索使用 |

### 2. 維護子系統（Maintenance Subsystem）資料表（`public.exchange_maint_*`，共 32 張表）

| 資料表名稱 | 正式環境筆數 | 用途與結構說明 | 查核狀態與對應修正 |
|---|---:|---|---|
| `public.exchange_maint_institutions` | `834` | 6 所台灣母校（`home`）與海外合作姊妹校（`host`）機構主檔 | 含 1 筆誤匯入之 `來臺蹲點實習計畫 TEEP`，已於 **PR #33** 納入清理 Migration |
| `public.exchange_maint_programs` | `6` | 6 校校級赴外交換計畫主檔（`prog_{school}_exchange`） | 正確 |
| `public.exchange_maint_cycles` | `6` | 各校交換學年度/學期週期規格（`116-1`、`116學年度`、`2027春季` 等） | 正確 |
| `public.exchange_maint_sources` | `6` | 6 校官方網站來源註冊表與允許網域白名單（`approved_domains`） | 正確 |
| `public.exchange_maint_offerings` | `1,124` | 各校交換名額與申請條件供給項目（NTU 288、NCU 214、NTPU 409、CGU 154、CCU 55、TKU 4） | 原 `baseline_mapper.py` 對 CCU/TKU 漏匯入、對 NTPU/CGU 重複匯入，已於 **PR #33** 修正為完整去重基準 |
| `public.exchange_maint_entity_revisions` | `1,960` | 機構與交換供給項目之不可變版本紀錄（SHA-256 雜湊驗證） | 正確 |
| `public.exchange_maint_releases` | `2` | 維護子系統發布版本紀錄（`rel_init_ntu_116_baseline`、`rel_eb82a50f3641`） | 正確 |
| `public.exchange_maint_release_members` | `1,958` | 發布版本所包含之實體與版本映射 | 正確 |
| `public.exchange_maint_publication_head` | `1` | 當前生效之發布指標（Singleton Head Lock） | 正確 |
| `public.exchange_maint_change_sets` | `0` (DB) / `2` (App 記憶體預設注入) | 待審核之資料變更集（`routes.py` 原於啟動時無條件在記憶體注入 2 筆虛構臺大截止日變更集） | 已於 **PR #33** 關閉預設注入並修正展示資料與新增 DB 清理 Migration |
| 其餘 22 張 `exchange_maint_*` 表 | `0` | 包含 `change_items`、`review_decisions`、`snapshots`、`content_blobs`、`fetch_attempts`、`extraction_runs`、`evidence`、`field_assertions`、`jobs`、`reports`、`experiences` 等 | 結構與 RLS 權限完整（共 39 個 SQL Migrations 通過 `pglast` 驗證） |

### 3. 認證與儲存資料表（`auth` & `storage` Schema）

- `auth.users`（39 筆測試/管理帳號）、`auth.identities`（0 筆）、`auth.sessions`（0 筆）、`auth.refresh_tokens`（0 筆）、`auth.audit_log_entries`（0 筆）、`auth.mfa_factors`（0 筆）、`auth.one_time_tokens`（0 筆）。
- `storage.buckets`（1 筆：`document-vault`）、`storage.objects`（0 筆）、`storage.migrations`（25 筆）。

---

## 三、程式碼與靜態資料包（`src/exchange_info/` & `sources/` & `data/`）完整盤點

前台學生端各頁面與公開 API（`/schools`、`/dashboard`、`/coverage`、`/application-workflows`、`/destination-profiles`）實際讀取之權威資料來源如下：

### 1. 台灣 6 所大學註冊中心與核心邏輯模組

| 模組路徑 | 適用學校 | 負責組裝之核心資料範圍 |
|---|---|---|
| [`src/exchange_info/university_registry.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/university_registry.py) | 全平台 6 校 (`cgu`, `ntpu`, `ntu`, `ncu`, `ccu`, `tku`) | 學校中英文名稱、官方網站 URL、所屬學院清單（`colleges`）、最低學業成績門檻（`academic_score_minimum`）、姊妹校數量提示（`partner_count_hint`）、資料覆蓋說明（`coverage_note`） |
| [`src/exchange_info/student_view.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/student_view.py) & [`cgu_catalogue.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/cgu_catalogue.py) | 長庚大學 (`cgu`) | 長庚 115 學年度交換簡章時程、申請資格、語言門檻、獎學金、應繳文件，以及 77 筆交換與雙聯目錄（解析自 2 份官方 Google Sheets gviz JSON） |
| [`src/exchange_info/ntpu_student_view.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/ntpu_student_view.py) | 國立臺北大學 (`ntpu`) | 北大 116 學年度第 1、2 學期甄選時程、75 分/前 50% 資格、語言門檻、獎學金，以及即時解析 116 英語組（99 校）、日語組（49 校）、中文組（21 校）與 115 歷史參考（37 校）共 206 校 PDF 表格 |
| [`src/exchange_info/ntu_student_view.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/ntu_student_view.py) & [`ntu_current_updates.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/ntu_current_updates.py) | 國立臺灣大學 (`ntu`) | 臺大 116-1 甄選時程（2026/11/2–11/9 16:00）、GPA 2.70 資格、語言門檻、獎學金、應繳文件及 288 所姊妹校名額與細目頁注意事項 |
| [`src/exchange_info/ncu_student_view.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/ncu_student_view.py) & [`scripts/build_ncu_catalog.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/scripts/build_ncu_catalog.py) | 國立中央大學 (`ncu`) | 中央 116-1 申請時程（2026/11/16–12/4 12:00）、大學部 60 分/研究所 70 分資格、語言門檻、計點公式、表件條件及 214 所去重姊妹校（116-1 官方列表 215 筆 + 115 參考 216 筆） |
| [`src/exchange_info/ccu_student_view.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/ccu_student_view.py) & [`ccu_profile.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/ccu_profile.py) | 國立中正大學 (`ccu`) | 中正 2027 春季班三梯次時程、平均 70 分且 GPA 3.0 門檻、CEFR B2 語言要求、獎學金及 104 所姊妹校（52 校當期開放、49 校歷史參考、3 校未公布） |
| [`src/exchange_info/tku_student_view.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/tku_student_view.py) & [`tku_data.py`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/src/exchange_info/tku_data.py) | 淡江大學 (`tku`) | 淡江 116 學年度日語組二次甄選時程、75 分/前 40% 門檻、語言要求、獎學金及 287 所姊妹校（4 校當期已截止、124 校歷史簡章參考、159 校締約名錄） |

### 2. 內建官方資料包（`src/exchange_info/official_data/`）與原始憑證檔案清冊

| 學校 | 資料檔案位置 | 檔案格式 | `main` 紀錄筆數 | 修正後筆數 | 內容說明 |
|---|---|---|---:|---:|---|
| **長庚 (`cgu`)** | `src/exchange_info/official_data/cgu_catalogue/snapshot.json` | JSON | `77` | `77` | 75 校級開放 + 2 院級參考（含交換與雙聯學位） |
| | `data/source_cache/cgu_catalogue.json` | JSON | `77` | `77` | 執行期快取（PR #29 修正雷恩商學院失效參考連結） |
| | `src/exchange_info/official_data/cgu/application_workflows.jsonl` | JSONL | `154` | `154` | 77 校 × 秋/春二梯次申請工作流 |
| | `src/exchange_info/official_data/cgu/destination_profiles.jsonl` | JSONL | `77` | `77` | 77 校目的地生活與住宿指南 |
| **北大 (`ntpu`)** | `src/exchange_info/official_data/ntpu/116-guidelines-zh.pdf` & `en.pdf` | PDF | `2` 份 | `2` 份 | 116 學年度中英文甄選簡章原始 PDF |
| | `src/exchange_info/official_data/ntpu/116-{english,japanese,chinese}-partners.pdf` | PDF | `3` 份 | `3` 份 | 116 學年度英（99 校）、日（49 校）、中（21 校）姊妹校一覽表 PDF |
| | `src/exchange_info/official_data/ntpu/destination_profiles.jsonl` | JSONL | `206` | `206` | 169 校 116 當期開放 + 37 校 115 參考（PR #30 修正 22 校誤吸校名） |
| | `src/exchange_info/official_data/ntpu/application_workflows.jsonl` | JSONL | `409` | `409` | 115 與 116 學年度申請工作流（PR #30 修正校名） |
| | `src/exchange_info/official_data/ntpu/partner_research.jsonl` | JSONL | `206` | `206` | 206 校外校網站與查證紀錄（PR #30 修正校名） |
| **臺大 (`ntu`)** | `src/exchange_info/official_data/ntu/partners.jsonl` | JSONL | `288` | `288` | 288 所交換計畫（PR #31 更新 20 校確定名額、女王大學 0 名額、夏威夷大學希羅分校正名與 11 所澳洲學校簽證提醒） |
| | `src/exchange_info/official_data/ntu/exchange_info.json` & `student_dashboard.json` | JSON | `288` | `288` | 臺大完整交換資訊與前端 Dashboard 快照 |
| | `src/exchange_info/official_data/ntu/home_rules.json` / `documents.json` / `scholarships.json` | JSON | `3` 份 | `3` 份 | 臺大 116-1 甄選規定、報名文件與獎學金 |
| | `src/exchange_info/official_data/ntu/college_programmes.json` | JSON | `16` 院 | `16` 院 | 16 學院院級交換與獎學金（PR #31 新增管院 2 份 116 獎學金 PDF） |
| | `src/exchange_info/official_data/ntu/application_workflows.jsonl` & `destination_profiles.jsonl` | JSONL | `288` / `288` | `288` / `288` | 288 校申請工作流與目的地指南（PR #31 同步更新 `#369` 校名與 2027-28 要項） |
| **中央 (`ncu`)** | `sources/ncu/2026-10-13/116exchangeschoollist-1013.pdf` & `quota-116-1-rows.json` | PDF / JSON | `0` (缺漏) | `215` | **PR #32 新增**：中央國合處 2026/10/13 最新公告之 116-1 交換學校列表（215 筆） |
| | `sources/ncu/2026-10-08/quota-115-rows.json` | JSON | `216` | `216` | 115 學年度歷史名額表（216 筆，保留作為無當期名額時之規劃參考） |
| | `src/exchange_info/official_data/ncu/partners.jsonl` | JSONL | `214` | `214` | 去重後之中央姊妹校主檔（PR #32 整合 116-1 新增 6 校、移除 7 校及正名羅馬尼亞美利堅大學） |
| | `src/exchange_info/official_data/ncu/exchange_info.json` & `student_dashboard.json` | JSON | `214` | `214` | 中央完整交換資訊與前端快照（PR #32 新增系統升級公告與 11/10 說明會公告） |
| | `src/exchange_info/official_data/ncu/application_workflows.jsonl` & `destination_profiles.jsonl` | JSONL | `214` / `214` | `214` / `214` | 中央申請工作流與目的地生活指南 |
| **中正 (`ccu`)** | `src/exchange_info/official_data/ccu/partners.jsonl` | JSONL | `104` | `104` | 52 校 2027 春季開放 + 49 校歷史參考 + 3 校未公布（PR #33 納入 Shadow Store） |
| | `src/exchange_info/official_data/ccu/home-rules.json` | JSON | `1` 份 | `1` 份 | 中正 2027 春季班三梯次時程、GPA 3.0 / 70 分資格、文件與獎學金 |
| | `src/exchange_info/official_data/ccu/application_workflows.jsonl` & `destination_profiles.jsonl` | JSONL | `55` / `104` | `55` / `104` | 中正申請工作流（55 筆）與目的地指南（104 筆） |
| **淡江 (`tku`)** | `src/exchange_info/official_data/tku/partners_current.jsonl` | JSONL | `4` | `4` | 116 學年度（2027–2028）日語組二次甄選 4 校（立命館、津田塾、電氣通信、北海道） |
| | `src/exchange_info/official_data/tku/partners_reference.jsonl` | JSONL | `124` | `124` | 115 學年度歷次簡章參考學校（124 筆） |
| | `src/exchange_info/official_data/tku/partner_census.jsonl` | JSONL | `286` | `286` | 淡江國際處全校締約姊妹校名錄（286 筆；加上津田塾大學共 287 校） |
| | `src/exchange_info/official_data/tku/destination_profiles.jsonl` | JSONL | `287` | `287` | 淡江全數 287 所姊妹校目的地指南（PR #33 納入 Shadow Store） |

---

## 四、前端各頁面與 API 資料流對應關係

| 前端頁面 / 路由 | 呼叫之核心後端 API | 實際讀取之底層資料來源 | 快取與同步機制 |
|---|---|---|---|
| 首頁與學校選擇器 (`/`, `/app`) | `GET /schools` | `university_registry.py` (`SUPPORTED_UNIVERSITIES`) | 行程內常數，啟動載入 |
| 交換學校總覽與篩選看板 | `GET /dashboard?school={id}` | 各校 `*_student_view.py` 及 `official_data/{id}/student_dashboard.json` / `partners.jsonl` | `@lru_cache` 快取（CGU 支援背景重新整理 `cgu_catalogue.json`） |
| 資料完整度與來源驗證面板 | `GET /coverage?school={id}` | `api.py` 即時統計 Dashboard 欄位完整度與 `official_data/{id}/catalog-completeness.json` | 隨 Dashboard 同步計算 |
| 姊妹校申請流程時間軸 | `GET /application-workflows?school={id}` | `official_data/{id}/application_workflows.jsonl` 與 DB `public.application_workflow_revisions` | 啟動載入 JSONL 並支援治理雙審核更新 |
| 姊妹校城市生活與住宿指南 | `GET /destination-profiles?school={id}` | `official_data/{id}/destination_profiles.jsonl` 與 DB `public.destination_profile_revisions` | 啟動載入 JSONL 並支援治理發布與回滾 |
| 申請中心與文件準備表單 | `GET /application-documents?school={id}` | `application_documents.py`、`official_data/ntu/documents.json`、`ncu_document_conditions.py`、`ccu_documents.py`、`tku_documents.py` | 行程內模組與 JSON 設定 |
| 後台維護與變更審核工作台 (`/maintenance/workbench`) | `GET /maintenance/admin/*`, `GET /maintenance/offerings/*` | `maintenance/routes.py`、`maintenance/baseline_mapper.py`（Shadow Store）與 DB `public.exchange_maint_*` | 本地 `data/maintenance_store` 與 `generate_shadow_sync_sql()` 同步 |

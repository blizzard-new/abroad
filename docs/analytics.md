# 使用統計（匿名、自己的資料庫）

網站的瀏覽與操作資料存在你自己的資料庫（正式環境是 Supabase），不經過 Google Analytics 之類的第三方。用途是看「有多少人來、從哪來、看什麼、卡在哪」，方便之後改版和調整策略。

## 怎麼看

| 方式 | 內容 |
| --- | --- |
| 儀表板 `https://你的網域/admin/analytics` | 完整報告：趨勢、漏斗、來源、學校、搜尋、裝置、速度、錯誤、API 健康、回訪、註冊、社群。要先用管理員帳號登入首頁，再開這頁。 |
| 匯出 CSV（儀表板右上角） | 原始事件，一列一個事件，可以丟進 Excel 或 Google 試算表自己分析。 |
| 終端機 `exchange-info analytics-report --days 30` | 一段文字摘要；加 `--json` 會印完整報告。 |
| Supabase 的 SQL 編輯器 | 六個每日彙總檢視：`exchange_analytics_daily`、`_routes_daily`、`_schools_daily`、`_search_terms_daily`、`_traffic_daily`、`_api_daily`，也可以直接查原始表 `exchange_analytics_events`。 |

誰算管理員：環境變數 `EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS`（帳號 ID，逗號分隔）或 `EXCHANGE_CONTENT_ADMIN_EMAILS`（電子郵件，逗號分隔）。

## 蒐集什麼、不蒐集什麼

| 會記 | 不會記 |
| --- | --- |
| 隨機產生的訪客代號（存在瀏覽器 localStorage，不是 cookie）、每次造訪的代號 | IP 位址、電子郵件、姓名、帳號 ID |
| 看了哪個頁面、停留與捲動多久、點了哪個按鈕 | 表單、貼文、留言、私訊的內容 |
| 搜尋詞（只在看起來是學校、國家、主題時；像電子郵件、電話、學號、網址的會遮掉，只留長度） | 學生證或任何文件 |
| 打開了哪所學校、收藏了哪所、點了哪個外部連結、下載了什麼 | 你在別的網站做什麼 |
| 來源（推薦網站的網域、UTM 參數）、裝置類別、瀏覽器、作業系統、語言、時區、螢幕寬度級距 | 精確位置（國家只在 CDN 提供標頭時才記） |
| 網頁速度、前端錯誤、失敗的請求 | 錯誤訊息裡的網址與長數字（會遮掉） |
| 伺服器自己確認的事：新帳號（只記登入方式與學校依據）、發了貼文／留言（只記哪個板與署名方式） | 發文內容與作者身分 |

保護措施：
- 瀏覽器送出「不要追蹤」（Do Not Track）或 Global Privacy Control 時，完全不記。
- 自動化瀏覽器（機器人、測試）預設不送資料；伺服器端也會依 User-Agent 標記 `is_bot`，所有報告預設排除。
- 頁尾有「停用匿名使用統計」按鈕；你自己的瀏覽器可以開一次 `https://你的網域/?analytics=off` 永久排除自己（`?analytics=on` 恢復）。
- 只接受白名單內的事件名稱，屬性只收簡單文字／數字、最多 16 個，單筆批次最多 40 個事件、64 KB，每個來源每分鐘有上限。
- 資料預設保留 400 天，之後自動刪除（`EXCHANGE_ANALYTICS_RETENTION_DAYS`，最少 30）；也可手動 `exchange-info purge-analytics --days 400` 或在儀表板 API 清除。
- 統計失敗不會影響網站：寫入出錯只會記一筆日誌，使用者看不到。

## 事件目錄

| 事件 | 何時 | 主要屬性 |
| --- | --- | --- |
| `session_start` | 新的一次造訪（閒置 30 分鐘後算新的一次） | — |
| `page_view` | 進站與每次換頁（路由） | `title`、`entry`、`school`／`board`（打開的學校頁或討論板） |
| `engagement` | 換頁、切換分頁、離開時 | `active_ms`（實際操作毫秒）、`max_scroll_pct` |
| `click`／`rage_click` | 點按鈕或連結／1 秒內連點同一處 3 次 | `target`、`label`、`value`（僅限無害的屬性） |
| `school_open` | 打開學校詳情 | `school`、`surface`（list／map／favorites／school_page） |
| `favorite_toggle` | 收藏或取消 | `school`、`saved` |
| `search` | 搜尋框停止輸入後 | `q`（或 `q_redacted`）、`q_len`、`results` |
| `filter_change` | 國家、學院、學制、名額狀態篩選 | `filter`、`value` |
| `view_switch` | 列表／地圖切換 | `view` |
| `auth_dialog_open`、`auth_start`、`auth_success`、`school_pick`、`school_choose`、`home_school_change`、`logout` | 登入與選學校流程 | `provider`、`new_account`、`school_basis`、`school` |
| `advisor_submit`、`planning_action`、`document_action`、`calendar_action` | 顧問、規劃、文件、日曆操作 | `action` |
| `outbound_click`、`file_download` | 外部連結／下載檔案 | `host`、`path`、`school`、`ext` |
| `community_composer_open`、`community_topic`、`board_follow` | 社群操作 | `topic`、`board` |
| `web_vitals` | 每次載入一次 | `metric`（lcp、fcp、ttfb、cls、inp、load）、`value` |
| `js_error`、`unhandled_rejection`、`api_error` | 前端錯誤、失敗的請求 | `message`、`path`、`status` |
| 伺服器事件 `account_created`、`account_login`、`school_choice`、`post_created`、`comment_created` | 伺服器確認後寫入，瀏覽器不能偽造 | 登入方式、學校依據、板、署名方式 |

另有每小時的 API 請求統計（每個端點、每種狀態碼的次數與延遲區間），存在 `exchange_analytics_api_hourly`。

## 指標怎麼算

- **訪客**：不同的訪客代號。換瀏覽器、清除網站資料或用無痕視窗會被算成新的人，所以是「瀏覽器數」，不是真人數。
- **造訪次數**：不同的造訪代號。**頁面瀏覽**：`page_view` 的數量。
- **跳出**：一次造訪只看了一頁、沒有任何互動、實際操作不到 10 秒。
- **新訪客**：瀏覽器第一次出現的訪客代號；**回訪率**只看首次造訪的訪客，第 N 天有再來才算。
- **流量來源**：用造訪第一個有來源的事件判斷：UTM 付費媒介→廣告，有任何 UTM→活動連結，推薦網站是搜尋引擎→搜尋，社群網站→社群，其他→其他網站，沒有來源但在 Line／Instagram／Facebook 的內建瀏覽器開啟→社群（這些 App 不會帶來源），其餘→直接進站。
- **漏斗**：以訪客為單位，每一步都必須發生在上一步之後：進站→打開學校頁→開始規劃（收藏、規劃、文件、顧問、日曆）→開始登入→登入成功→登入後開始規劃。
- **搜尋**：「無結果率」是搜尋結果為 0 的比例；「搜尋後打開學校」是搜尋之後同一次造訪有打開學校的比例。無結果的搜尋詞就是該補資料的地方。
- **網頁速度**：真實使用者的 p50／p75／p95；良好與不佳的門檻依 web.dev（LCP 2.5／4 秒、CLS 0.1／0.25 等）。
- **API 延遲百分位數**：由區間計數推估（<100、<300、<1000、<3000、≥3000 毫秒），只適合拿來比較，不是精確值。
- 日期與時段一律台北時間。

## 上線時要做的事

1. 在 Supabase 套用 `supabase/migrations/20261003110000_analytics.sql`（建表、函式、檢視）。
2. 設定管理員（上面的環境變數）。
3. 預設就會開啟。要關閉設 `EXCHANGE_ANALYTICS=off`；正式環境（`EXCHANGE_ENVIRONMENT=production`）在開啟時一定要用 Supabase，否則拒絕啟動。
4. 在隱私權政策寫明（法律文字請自行確認）：蒐集匿名使用統計（瀏覽的頁面、操作、裝置與瀏覽器類別、來源網站、網頁速度與錯誤），不蒐集 IP、姓名、電子郵件或表單內容；不使用 cookie，只用瀏覽器本機的隨機代號；保留 400 天；可按頁尾的「停用匿名使用統計」或開啟瀏覽器的 Do Not Track。
5. 若放在 Cloudflare 或 CloudFront 後面，可讓 CDN 帶國家標頭（`CF-IPCountry`、`CloudFront-Viewer-Country`），報告才會有國家欄。

## 已知限制

- 儀表板一次最多讀 20 萬筆事件，超過會標示「資料量過大」；流量長大後要改成用資料庫端彙總（六個檢視已經是這個方向）。
- 正式 Supabase 還沒實際跑過：migration 只通過語法解析，寫入／讀取的程式用模擬的 PostgREST 測過，等你套用到專案後要實際看一次資料有沒有進來。
- 目前預設開啟、沒有同意橫幅，因為只收匿名資料、使用者主要在台灣。若之後有歐盟的使用者，把隨機代號存在瀏覽器裡可能需要事先取得同意，屆時要加同意橫幅（或改成不存代號的統計）。
- 收集端點是公開的，誰都能送資料，所以數字可以被刻意灌水；每個來源有流量上限、事件名稱有白名單，但不能完全防止。數字突然異常時，用 CSV 看訪客代號與來源是否集中。
- 用 App 版（Flutter／iOS／Android）的使用者目前沒有統計，只有網頁。
- 新增事件：把名稱加進 `src/exchange_info/analytics.py` 的 `CLIENT_EVENT_NAMES`，在前端呼叫 `UniWayAnalytics.track("名稱", {屬性})`，再到 `analytics_report.py` 加進報告。

## Demo 資料

`python scripts/seed_analytics_demo.py --data-dir <暫存資料夾>` 會產生一份假資料，方便先看儀表板長什麼樣；它不會寫進已有統計資料的資料夾。

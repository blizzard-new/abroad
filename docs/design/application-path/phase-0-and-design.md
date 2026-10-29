# UniWay「我的申請」：現況分析與關卡地圖方案

日期：2026-10-28。範圍：**網站版**。狀態：**Phase 0 / Phase 1，等待外觀與操作方向確認**。

檢查基準：`blizzard-new/abroad` 的 `main`，commit `e91075fa9630f2215c3ab0550f3c420446e9c165`。獨立分支：`codex/web-application-path`。

這份交付只新增設計文件與獨立互動預覽。未修改正式前後端、學校資料、API、資料庫、Docker 配置或原生 App；未套用 migration、部署、合併 PR。未新增大學資料查核。

> 2026-10-29 更新：以下 Phase 1 是 V1 歷史提案；目前的地圖方向、關卡粒度與辦理介面以 [V2 修訂方案](revision-2.md) 為準。Phase 0 程式分析及正式整合限制仍保留。

## Phase 0：現況

### 技術與部署

- 後端：Python、FastAPI、Pydantic。主要入口 `src/exchange_info/api.py`，模型在 `models.py`。
- 前端：`src/exchange_info/static/index.html`、原生 JavaScript、CSS，hash 路由及共享狀態。僅學校選單與地球有各自獨立的 esbuild bundle；不是完整 React SPA。
- 專案與適用祖先目錄沒有具內容的 `AGENTS.md`。已檢視 README、`pyproject.toml`、前後端入口、相關模組與自架配置。
- `deploy/selfhost/docker-compose.yml` 維持 FastAPI、Postgres、PostgREST、Storage API、內部 gateway 及 Windows Caddy。程式中的 Supabase repository 是相容的 REST adapter，自架配置指向內部 gateway；不代表要改用雲端 Supabase。
- 此改版不新增前端框架或動畫套件，不調整 Render、外部託管或 DNS。

### 「我的申請」目前在哪裡

| 部位 | 現有程式與行為 | 改版處理 |
|---|---|---|
| 網站導覽 | `index.html` 的「我的申請」連到 `#advisor`；公開路由分組為 overview | 保留導覽外觀與其他連結；新增地圖入口後仍支援舊深連結 |
| 三階段工作區 | `application-workspace.js` / `.css` 將既有 DOM 收進選校、準備、文件三組 | 地圖作為統一入口，工作區作為真正辦理任務的工具，保留既有事件與未送出輸入 |
| 選校與資格 | `app.js` 的 `#advisor`、favorites、eligibility | 母校、偏好、志願排序、資格判斷與來源全部保留 |
| 準備與時程 | `#overview`、`multi-plan.js`、`application-journey.js`、`platform-tracker.js` | 保留清單／看板／時間軸、每週可用時間、個人事件、任務依賴及工時 |
| 文件 | `document-workbench.js`、application-center、application-form、document-check、documents | 保留草稿、生成／編輯、上傳、私人檔案、檢查、PDF／DOCX 匯出與權限；依現有可用狀態顯示寫作工具 |
| 帳號同步 | `app.js` 工作區 localStorage 暫存、同步與衝突處理 | 保留帳號切換、登出清理、過期請求隔離及同步提示 |
| 其他申請工具 | calendar、deadlines、budget、scholarships、來源回報 | 留下入口，避免地圖取代工具而丟失功能 |

目前入口不是一條逐項可操作的申請地圖，而是三個大工作區。新地圖解決「現在在哪、下一步做什麼」；不刪掉既有詳細操作。

### 現有 API、登入與保存

| 區域 | 已有能力與限制 |
|---|---|
| 認證 | `authenticated_account` 透過 HttpOnly `exchange_guide_session` cookie 或 bearer session 驗證 session hash、有效期及帳號；仍須沿用學校驗證與資料範圍限制 |
| 帳號工作區 | GET / PUT `/account/workspace`，每個帳號＋母校一筆，revision compare-and-set，衝突回 409，回應 no-store |
| 計畫排程 | POST `/application-plan/evaluate`、`/application-plan/schedule`，適用任務、工作量、準備狀態與依賴已有服務 |
| 年度與規則 | GET `/application-period-options`、`/application-workflow`，學校／科系／年度／梯次、來源與資料狀態必須保留 |
| 文件目錄 | `/application-center/templates`、`/catalog`、`/study-plan-workbench`、manifest、PDF、DOCX、私人 vault 與 form draft repositories |
| 提交紀錄 | POST `/account/submission-progress` 為獨立狀態機，不隨一般 workspace JSON 覆蓋；`recorded_by=student`、`platform_submitted=false`，不是校方官方審查狀態 |
| 正式保存 | 自架 Postgres 上的 `exchange_account_workspaces` 及 `exchange_commit_account_workspace` 原子 RPC；開發環境可用 JSONL |
| 方案限制 | 公開模式免費方案對作用中申請校數已有限制；新計畫介面不能繞過既有 entitlement |

`AccountApplicationWorkspace` 含收藏、申請校、application_progress、document_readiness、application_context、application_selections、submission_progress、budget_plans、deadline_events、planning_availability、preparation_tasks 與 revision。

**必須補足的資料隔離：**

1. 工作區目前只有一個作用中的 `application_context`。
2. 準備任務 identity 已包含母校、合作校或明確共用的母校範圍、program、年度、梯次、院系、rule 及來源內容 signature；不依志願名次。但尚無獨立的出國學期識別。
3. `applicationDraftKey` 是 `homeSchool::templateId`。後端草稿查找也是帳號＋母校＋template。這個結構**不足以保證同校不同學期的文件草稿完全隔離**。
4. 部分母校要求現在會跨合作校共用；新需求要每份計畫獨立，不能偷偷共用完成勾選。可提供「從其他計畫複製文件」作為明確操作。
5. 既有 workspace RPC 對欄位有白名單。只在前端加 `plans` 並不會自然獲得正式持久保存。

以上是程式結構檢查，**不是已重現正式帳號資料互相覆蓋**。本次沒有查閱真實使用者的私人文件或更動其帳號。

### 學校流程如何轉成關卡

預覽引用 `official_data/ntpu/application_workflows.jsonl` 內既有的 116 學年度「關西學院大學」「佐賀大學」兩筆公開流程節錄。其 review_status 為 legacy；預覽標註本期適用性待核對，不將其他自動標記視為人工驗證。

- 文件章節使用既有清單：簽名申請表、有效語言證明、交換研修計畫書、正式成績單與排名。**沒有新增所有學校都必須寫自傳、推薦信等假定**。
- 範例有抵達與返國事項，因此保留第七章；不是把使用者給的六章當硬性資料模型。
- 範例沒有可採用的明確 `deadline_at`，且 deadline_status 為 reference_only；不製造倒數日或通知期限。
- 範例沒有可用的正式 dependency，因此一般預覽不鎖定後面的任務。鎖定效果另設「個人前置條件」示意情境，清楚標示非校方規則。
- 現有提交入口或來源可能有歷史年度；預覽用「查看申請公告」避免把舊網址說成已確認可送件的當期入口。正式版應以既有有效性欄位及使用者核對資訊呈現，不在本任務進行新資料查核。

## Phase 1：視覺與操作方案

### 一個方向：UniWay 出發路徑

明亮米白／淡藍背景、UniWay 海藍品牌色、金色完成回饋。沿用藍色行李箱素材與細線圖示；不複製 Duolingo 商標、綠色品牌或貓頭鷹。

參考 [Duolingo 官方 Home Screen 說明](https://blog.duolingo.com/new-duolingo-home-screen-design/) 的關卡路徑、章節組織、回顧已完成關卡與返回目前位置。沿用 [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/ui-ux-pro-max/SKILL.md) 的可讀性、觸控、焦點、動態回饋檢查；圓潤立體效果只用在節點與主要按鈕。

| 區域 | 設計 |
|---|---|
| 上方 | 申請目標＋年度／出國學期＋計畫切換＋實際任務計算出的個人進度 |
| 地圖 | 70px 圓形節點，左右偏移形成 S 路徑；目前節點 78px，品牌藍與「繼續」；已準備金色勾選；未開始灰色且可點；校方處理使用淡紫色時鐘 |
| 章節 | 清楚編號及一句用途；已完成章節可收合、重開，不隱藏資料 |
| 桌機側欄 | 下一個建議任務、可信期限或缺少日期的說明、文件狀態、輕量吉祥物提示 |
| 手機 | 保留網站導覽的收合入口；單欄關卡置中；任務用 bottom sheet，主要操作在底部，內容可捲動 |
| 任務卡片 | 名稱、說明、學校、年度／出國學期、個人狀態、來源及主要操作。無確切期限時不顯示虛構日期 |
| 輔助模式 | 可切換任務列表，視覺不偏好地圖或使用輔助科技的人仍可操作 |

設計預覽的學期、勾選與帳號均為**示意**。預覽中的主要操作連到本機既有工具入口，目前還沒有接上某份計畫的文件內容。這不是完成的資料整合。

### 任務行為與狀態語意

| 任務 | 點下去 | 可以如何完成 |
|---|---|---|
| 母校／目標／資格 | 既有設定、志願管理、資格工具 | 個人確認；不替代校方判定 |
| 讀書／研修計畫 | 既有編輯工作台，帶 plan_id、template_id 與目前學校 | 文件存在／版本與個人 ready 狀態分開 |
| 文件準備 | 既有上傳、vault、檢查與匯出 | 上傳不等於合格；自標完成清楚標記 |
| 校內提交 | 適用官方來源、校方送件入口，及既有提交紀錄 | 外部網站開啟不自動完成；使用者回來記錄，標記為學生自述 |
| 審查、提名、錄取 | 查看正式通知來源與學生自記歷程 | **不提供「勾選即校方錄取」**；沒有校方資料就顯示未記錄／待正式通知 |
| 個人準備 | 個人日期、註記、查看要求與標記 ready | 可撤回，保留變更及同步回饋 |
| 真實前置依賴 | 任務卡仍可打開查來源，顯示阻擋原因及前置任務連結 | 只限制依賴的操作，不把整個章節一律鎖住 |

全站正式整合時，新增 `#my-application` 作為導航入口；舊 hash 路由繼續可用。進工具時記住 plan_id、task_id、地圖捲動位置；返回地圖帶回原關卡。跨帳號、母校或計畫切換時使舊請求失效，不能讓舊文件灌入新計畫。

### 進度與下一步

- 分母是目前計畫「適用、可由學生完成」的葉節點任務。章節／父容器、重複文件摘要不再算一次；校方等待、資訊節點不計入。
- 必填與選填分開，條件不明的任務顯示待確認，不悄悄排除後宣稱所有要求已完成。已不適用的舊紀錄保留，但不計入本期進度。
- 選校、語言、文件等真實目錄產生節點。不能只依顯示標題生成 identity，避免改文案就掉進度。
- 建議下一步優先選未完成、依賴已滿足且目前可操作的事項；有可信日期才排序期限。其餘依流程及最近處理事項排序。
- 逾期依可信日期＋時區判斷，顯示來源；不自動關閉或代替使用者放棄。個人目標日和官方期限分開。
- 主進度名稱為「個人準備」。到 100% 也不表示已正式送出、被受理或錄取。

### 動畫與無障礙

- 節點按壓：translateY 與陰影縮短，150–180ms；主要回饋以 transform / opacity 為主。
- 保存成功後：勾選、短暫亮光／小幅彈跳、少量彩紙（不到 1 秒），不播放循環動畫。
- 路徑：短距離 stroke 更新；長清單只更新受影響段，正式版避免每次重畫整份 DOM。
- 章節完成：aria-live 顯示「完成文件準備階段」，更新建議下一步，不強迫跳頁。
- IntersectionObserver 控制「回到目前關卡」，移動後焦點可繼續操作。
- Skeleton 使用固定空間避免畫面跳動；資料失敗可重試。
- 支援 `prefers-reduced-motion`，停止慶祝、路徑動畫與平滑捲動。
- 原生 dialog 提供焦點限制與 Escape 關閉；保留按鈕名稱、可見焦點、44px 以上主要觸控範圍。
- 不加每日強制登入、連續天數懲罰、扣血或虛擬貨幣。
- 60fps 是實作目標，不是本次桌面預覽已測得的手機實機效能。

## Phase 2 擬議：最小後端擴充（尚未實作、未套用）

單純增加 CSS 無法滿足多學期持久保存。建議採**新增而不破壞舊介面**：

1. 新增 `exchange_application_plans`：不可變的 plan_id、account_id、母校、合作校、program、academic_year、application_round、departure_semester，以及 revision、個人任務狀態、文件 readiness、最後位置。申請梯次與出國學期是兩個欄位。
2. 新增獨立的 `exchange_plan_form_drafts` namespace，唯一鍵為 owner＋plan_id＋template_id，重用現有加密與 vault 授權機制。原 `form_drafts` 及舊客戶端保持可用；引用既有文件必須逐件驗證 owner。
3. 新增受認證的 `/account/application-plans` 列表／建立與 plan 詳情／更新 API、原子 revision RPC。任務更新帶 expected_revision 與 mutation_id，伺服器驗證計畫歸屬、任務適用性及合法狀態，不接受客戶端把個人任務寫成官方審查結果。
4. 伺服器重用既有 evaluate、document catalog 與規則服務產生適用任務、來源、可操作狀態及進度分母。共用的是規則，個人進度依計畫隔離；要跨計畫複製文件時由使用者明確選擇。
5. 舊工作區只在學校／年度／梯次明確時做可重入的 copy-once import，保留 provenance 及原紀錄。無法判定學期的草稿留在「舊文件」，由使用者選擇複製，**不猜、不刪、不靜默合併**。
6. 保留免費方案與資料存取政策；新增表仍採 owner 檢查、RLS／既有 service-only 模式及同源認證。部署環境不變。
7. 409 重新讀取並調和；401 清除可見私人狀態；離線顯示「尚未同步」。只有伺服器確認後才顯示保存成功／完成慶祝。切帳號後不得補送前帳號資料。
8. 新功能需要新增 SQL migration 草稿與驗證，但**不會自行執行**。若後端未開啟能力，前端保留舊工作區並顯示功能未啟用，不假裝已同步。

可實作為新 `application_path` service / repository 與 `application-path.js` / `.css`，透過薄 adapter 呼叫既有工具。具體資料表與欄位需在實作前隨設計確認一併審視。這是針對目前缺口的最小隔離方案，不是重建前端或替換所有工作區服務。

### 預計正式修改範圍

| 類型 | 預計檔案 |
|---|---|
| 導覽與路由 | `static/index.html`、`static/app.js`、`static/application-workspace.js` |
| 新地圖與動畫 | 新 `static/application-path.js`、`.css`，沿用 brand-tokens 與既有素材 |
| 工具銜接 | `multi-plan.js`、`application-journey.js`、`document-workbench.js`：增加 plan context，不搬走現有功能 |
| API／保存 | `api.py`、`models.py`、plan service / repository、form draft adapter；保留原 API 合約 |
| SQL 草稿 | 新增 migration 檔與回滾／停用策略供審查，不自動套用 |
| 測試 | plan owner／revision／學校學期隔離、草稿匯入、來源與狀態、鍵盤／responsive 與既有流程回歸 |

不修改 `official_data`、學校事實、正式環境配置、SEO 公開頁、原生手機端。現有登入、論壇、搜尋、通知、指南等需通過回歸。

## Phase 3：驗證計畫

以下為正式功能實作後的驗收，不把設計預覽測試冒充完成。

| 使用情境 | 驗證方式 |
|---|---|
| 首份計畫 | 空帳號建立；權限、適用梯次、無資料時正確提示 |
| 既有進度 | 匯入保留紀錄；回到目前關卡；未知學期不自動套用 |
| 每種節點操作 | 實際開啟相同計畫的文件、資格、送件或個人任務；校方節點沒有假確認 |
| 完成與回復 | API 成功才更新；撤回、保存失敗、409、離線後同步 |
| 持久保存 | 重新整理、登出再登入、第二瀏覽器讀取同一份計畫 |
| 隔離 | 同母校不同合作校；同合作校不同學期；不同帳號；慢回應／跨計畫切換 |
| 依賴與已完成回顧 | 真依賴有原因與跳轉；非依賴可提前處理；已完成可重開 |
| 期限 | 缺日期、reference_only、舊年度、個人日期、可信逾期與時區邊界 |
| 版面 | 390×844、768×1024、1440×1000；放大字體、長學校名、dialog、橫向溢出 |
| 無障礙與效能 | Tab／Shift-Tab／Escape、focus restoration、螢幕閱讀語意、reduced motion、長路徑效能 |

執行專案現有 pytest（以範圍相關測試開始，完成必要完整回歸），包括 `test_account_workspace_api`、`test_multi_application_plan`、`test_application_plan_api`、`test_application_plan_schedule_api`、`test_form_drafts`、`test_submission_progress`、auth／vault，以及對應 E2E。這是軟體行為測試，不是新增大學資料查核。

JavaScript 用 `node --check`；`git diff --check`。根專案沒有配置獨立 TypeScript typecheck 或根前端 build/lint。若修改隔離 bundle 才執行其 npm build；不為此改版引入新建置架構。Python／原生 JS 型別與 API 合約由現有測試及必要靜態工具驗證。

## Phase 4：PR 與部署邊界

完成方向確認、功能實作與測試後，在獨立分支建立 PR，附修改清單、資料相容性、未套用 SQL、實測結果及改版前後截圖。**不自行合併、不部署、不執行正式 migration**。

本次預覽的實測結果見 [preview-validation.md](preview-validation.md)。

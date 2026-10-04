# Web 審核清單

- 審核標的：留學／交換資訊產品 Web 下一階段
- 審核包版本：2026-08-31-pre-review.129
- 目前狀態：尚未核准、不得移植 Flutter
- 審核範圍：長庚大學、國立臺北大學
- 暫緩範圍：AI API、本地 AI 串接、Flutter、SwiftUI、Kotlin

這份清單是產品負責人、兩位資料審查者與測試學生的共同驗收入口。自動化測試通過只能證明程式流程可運作，不能代替官方規定的人工查核，也不能自動形成 App 移植核准。

## 1. 開始審核前

- [ ] 閱讀 web-data-audit.md，確認已知阻擋項與數字落差。
- [ ] 開啟 `docs/web-review-findings.md`，確認仍使用匿名工作階段代碼、沒有私人資料，並把每個真人發現依 P0～P3、重現、處置、回歸與重驗欄位完整記錄。
- [ ] 確認本次使用的資料快照、提交或壓縮檔版本。
- [ ] 執行完整非 E2E 回歸：`uv run --frozen python -m pytest -q --ignore=tests/e2e`。
- [ ] 確認 `uv lock --check` 與 `uv sync --frozen --extra dev` 通過；不得用 editable pip install 取代 frozen environment。
- [ ] 確認所有外部 GitHub Actions 仍固定完整 commit SHA；版本更新必須由人工解析官方 tag、更新 SHA 與契約測試，不能退回可移動 major tag。
- [ ] 執行 Python runtime dependency 稽核：`uv run --frozen python scripts/audit_python_dependencies.py`；必須輸出 `No known vulnerabilities found`，且不得忽略漏洞 ID。
- [ ] 執行 OpenAPI drift 檢查：python scripts/export_openapi.py --check。
- [ ] 執行來源中繼資料研究候選漂移檢查：`uv run --frozen python scripts/check_source_metadata_research.py --check --timeout 30`。
- [ ] 執行完整 Web E2E：`uv run --frozen python -m pytest -q tests/e2e`。
- [ ] 執行隔離 Supabase runtime：`uv run --frozen python scripts/validate_supabase_runtime.py`；必須回傳 exit code 0、JSON `status=passed` 與 `cleanup_status=passed`，且不能設定 `continue-on-error` 或 `--keep`。輸出的 project 名稱必須使用 `exchange-supabase-runtime-` 保留前綴並且每次不同；所有外部子程序必須有 timeout，preflight／final cleanup 必須確認 down 成功且 container、network、volume 無 label 殘留。任一 validation、timeout、cleanup 或殘留錯誤都必須 exit 1，不能輸出 passed；本機 Docker 無法啟動時不得把既有證據冒充本輪 fresh pass，應等待遠端 CI 或修復 daemon 後重跑。
- [ ] 確認 E2E 資料只寫入 pytest 暫存目錄。
- [ ] 確認測試環境沒有設定或呼叫外部 AI API／本地 AI runtime。
- [ ] 確認 Flutter、SwiftUI、Kotlin 尚未因本次審核而修改。

目前可重跑基線（2026-08-31）：

| 項目 | 結果 |
| --- | --- |
| 完整 pytest | `pre-review.129` 以 CI 相同 frozen environment 分開執行完整非 E2E 與 Chromium E2E：804＋49，合計 853 passed、0 failed；非 E2E 耗時 412.66 秒，E2E 耗時 456.41 秒。除既有依賴安全、登入、隱私、workspace、治理、社群、申請規定錯誤回報、migration parser、Storage 與 runtime 契約，也驗證來源證據 composite snapshot 的 schema／pending revision／candidate manifest 綁定、stale 409 與產生期間變更 409。 |
| Web E2E | `pre-review.129` 單獨重跑 49 項 Chromium E2E，49 passed、0 failed，耗時 456.41 秒。情境涵蓋已驗證學生回報、結果不明同 mutation ID 重試、管理員獨立結案與來源證據 CSV；真實下載 URL、檔名與每列指紋均綁定同一 backlog group snapshot。 |
| Python 相依套件安全 | `cryptography` 已由 46.0.7 升至 50.0.1；`pip-audit 2.10.1` 固定於 dev dependency。`uv run --frozen python scripts/audit_python_dependencies.py` 在 Windows 中文路徑成功完成並回報 0 個已知漏洞；`uv lock --check` 與 `uv pip check` 通過。這只完成 dependency baseline，不代表 F-01 或正式環境安全審查完成。 |
| 本機 Supabase runtime | `pre-review.127` 的必要命令已在 pinned PostgreSQL 17.6／兩個 PostgREST 14.12／Storage API 1.60.4 的全新 tmpfs DB 與隔離 Storage volume 從零套用 21／21 migrations，回傳 `status=passed`、`cleanup_status=passed`。實跑證據包含 32／32 RLS、0 browser grants、3 個 workflow issue service-role-only RPC、submit／review 競態與冪等、每小時 10 筆限流、6 個 unsafe source URL、刪帳 pending 去識別 90 天、terminal 24 小時 replay grace、purge／cascade／control 保留，以及既有雙 API 社群、六種晚期 rollback、Storage delete／replay／orphan cleanup；結束後 project label 下 container／network／volume 均為 0。遠端 CI、正式 Supabase、既有資料升級與正式 Storage backend 仍待驗。 |
| 規格追蹤 | 第 6–19 節共 34 條唯一追蹤列，自動檢查任務、狀態、證據與下一門檻 |
| OpenAPI contract | `2026-08-31.2`；快照與 live schema 完全一致，`uv run --frozen python scripts/export_openapi.py --check` 通過。來源證據 CSV 必須帶 64 位 `expected_snapshot`，backlog group 回傳專用 `source_evidence_snapshot_fingerprint`；來源候選、OAuth、帳號、社群、文件同意、治理、AI 暫緩及隱私邊界維持 fail closed。 |
| 即時來源稽核 | 封裝基線仍為替換來源 20 HTTPS／2 HTTP 降級與 metadata 5 可讀／1 應用層失效；2026-08-31 本次 live recheck 因立教 2 個 URL connect timeout、長庚 1 個 URL read timeout 而各以 exit 1 fail closed。不得勾選開始審核前的兩個來源稽核項目，也不得自動改 manifest、candidate、revision 或公開資料。 |
| 正式唯讀稽核 | `NOT READY`；280 workflows、0 published，生活情報 137 verified／143 pending destination profiles、470 pending sources，共 9 類 blockers，CLI exit code 2。三個 fingerprint 與 `.103` 相同：總指紋 `6c88731481993e0bcf3da9627153db86731a13403605607478fba4f9cb9df49d`、申請流程子指紋 `e72b8c4a35ae34294ad497af9988d740e9f4236caaa9fe3396dbe32f4af4d57c`、生活情報子指紋 `d73804f1ec16ddc7e61e71fc8a199a021b285cd2a7a658e9ec9186077b070011`。 |
| GitHub Actions | workflow 已固定 `uv 0.11.26`、`uv.lock` frozen sync 與三個外部 action 完整 SHA，並包含不能忽略失敗的 20 分鐘隔離 Supabase runtime step；harness 內層具分級 timeout、每 run 唯一 project 與 cleanup fail-closed。本機 frozen 基線 848 項及 current 21／21 fresh runtime 均通過，首次遠端執行仍待完成。 |
| 真實瀏覽器 | `pre-review.129` 已單獨重跑 49 項 Chromium E2E，全部通過。驗收涵蓋申請規定錯誤回報的桌面／390px、結果不明重試、管理員競態，以及來源證據 CSV 的 snapshot-bound URL／檔名／列內容；這仍不能取代 C-02 真人走查。 |
| 本機 fallback 完整性 | JSONL 寫入只在完整 flush／fsync 後原子替換；替換失敗保留舊檔並清除暫存檔；32 個同時帳號 upsert，以及問題／回答／經驗投稿各 24 路追加全數保存。這是本機／測試保護，不取代正式 Supabase repository |
| 測試資料 | pytest session 暫存目錄；人工瀏覽器驗收使用獨立資料目錄，完成後已移至資源回收筒 |

## 2. 產品負責人與測試學生流程

每個情境都要在桌面版與 390px 手機寬度各走一次。問題請記錄實際畫面、帳號身分、學校、操作步驟、預期結果與實際結果。

### A. 未登入探索

- [ ] 不登入即可切換長庚大學與國立臺北大學。
- [ ] 可搜尋、篩選、瀏覽合作校與查看申請規定。
- [ ] 可在未登入狀態比較至少兩所學校；訪客比較只存在當次分頁，不寫入收藏或申請清單。
- [ ] 點選收藏或建立個人申請計畫時先要求登入；登入後收藏才進入帳號工作區並跨裝置同步。
- [ ] 「中央當期開放」、「合作備查」、「院級參考／中央當期未列」與一般資料待確認不會混為一談。
- [ ] 艾克斯馬賽大學管理研究所與雷恩商學院可搜尋、瀏覽、比較、收藏，也能開啟院級官方來源；確認前不能加入正式申請清單或志願選單。
- [ ] 每一項可申請結論都能看見來源、適用年度／梯次與最後查核日期。
- [ ] legacy／參考流程不會顯示成已正式發布；只有具有 published 狀態與 published_at 的版本可以啟用精確期限提醒。

### B. 漸進式登入與學生驗證

- [ ] 純瀏覽不強迫登入。
- [ ] 收藏同步、建立申請計畫、記錄進度、發文或留言時才要求登入。
- [ ] 未登入時文件完成 checkbox、送件資料狀態與學校申請進度保持停用；以 DOM 直接觸發 mutation function 仍不得寫入 localStorage 或私人工作區。
- [ ] 未登入新增個人日曆任務會保留尚未送出的輸入並開啟註冊，不建立本機事件；登入後相同操作才建立並同步。
- [ ] 未登入可即時計算交換預算；按「登入後儲存估算」會保留本次分頁輸入並開啟註冊，`exchange-guide-budget-plans` 保持空白。登入後保存才寫入版本化工作區，第二裝置可還原學校、幣別、月數與各項金額。
- [ ] 未登入可先填規則式申請顧問條件；按「登入後產生方案」只開啟註冊，不呼叫 `/advisor/plan`、不寫入 `exchange-guide-eligibility-profile`，且目前輸入保留。登入後同一份輸入才可送出；登出後表單、顧問結果與保存條件均清空。
- [ ] 登出後才抵達的舊 authenticated response 不得重新套用通知、工作區、表單草稿或私人文件庫；workspace metadata、收藏、申請、進度及資格 storage 仍保持移除。
- [ ] 已登入且有未同步修改時，讓 `/auth/session` 暫時無法連線後重新載入：帳號列顯示「離線」，畫面不出現收藏、資格或表單私人值，且恢復連線前不送出 workspace PUT；相同帳號重新驗證後才還原並同步。
- [ ] 若隔離期間的 server session 已撤銷，恢復連線後須回到「登入」、清除 owner-bound pending 與私人 localStorage／sessionStorage，且不得上傳隔離資料。
- [ ] 登入、重新載入、workspace 同步、社群、私人文件庫與 PDF 下載後，`exchange-guide-auth-token` 均維持不存在；Web 只依賴 HttpOnly session Cookie。
- [ ] development／preview 設定 `EXCHANGE_AUTH_SECURE_COOKIE=true` 後，登入與 OAuth flow Cookie 都包含 `Secure`、`HttpOnly`、`SameSite=Lax`；production 即使旗標缺漏或 false 也必須維持 `Secure`，不能因設定錯誤降級。
- [ ] `/`、靜態 JavaScript、`/health`、`/auth/session` 等公開與私人 response 都包含 CSP、`nosniff`、`DENY` iframe、`no-referrer` 與 Permissions Policy；production HTTPS response 另包含一年 HSTS。
- [ ] 前端沒有 inline `onerror`／`onclick` 等 script handler；學生與管理工作台核心情境在沒有 `unsafe-eval` 的 CSP 下仍可操作，主要訪客流程沒有 CSP console error。
- [ ] 開啟 `/docs` 不載入第三方 CDN、inline script 或互動式 Swagger／ReDoc；可點入 `/openapi.json`，兩頁都沒有 CSP 或 favicon console error，`/redoc` 會明確導回安全契約頁。
- [ ] 帳號 session 建立成功後，登入對話框立即關閉；社群、權益、工作區、日曆、通知與表單草稿分別同步，單一非關鍵載入失敗只顯示稍後重試，不會回滾 session 或誤報登入失敗。
- [ ] 本機 fallback 連續執行註冊、登入、同步與管理工作台時不出現半寫入 JSON、資料解析錯誤或登入 500；正式部署確認實際使用 Supabase repository，而非把 JSONL 當正式多程序資料庫。
- [ ] production 設定 `EXCHANGE_ACCOUNT_REPOSITORY=jsonl` 時，即使 Supabase credentials 齊全也必須拒絕啟動；不得讓明確 local mode 比 `auto` 更寬鬆。
- [ ] production 啟動後 `app.state.persistence_backends` 的 account、content governance、destination review、document vault、form drafts、transient auth、public community、community suspension 與 workflow issue reports 九個 identity 必須全部是指定 Supabase backend；部分 identity 即使共用 repository，獨立檢查也不得被略過。依賴注入本機 service 或 memory transient store 同樣不能繞過；development 則仍可使用隔離 JSONL／local encrypted／memory fallback。
- [ ] 公共板發言至少要求一般帳號與 Email 驗證。
- [ ] 大學板只有已驗證且學校相符的學生可以發文或留言。
- [ ] 學生證影像不落地，不保留 OCR 全文或學號。
- [ ] 系統不要求校務系統密碼。
- [ ] 校方 OAuth callback 只能由原發起帳號的 exact session 完成；另一個帳號或同帳號另一個 session 回呼時須在任何 provider request 前回 403，且不得消耗 state。原 session 隨後仍可成功或取消，終止後重播固定回 400。
- [ ] 原 session 提供過短／過長 authorization code 或過長 error 時，先消耗合法 state 再回 422；相同 state 不能修正參數後重試。成功、取消、缺 code、malformed 參數與 provider failure response 均為 `no-store`。
- [ ] Google／Facebook 一般登入另使用只限 callback path 的 HttpOnly、SameSite=Lax flow cookie；另一個瀏覽器不得移用 state。Facebook 未驗證 Email 不保存、不自動合併；verified provider 也不得接管 legacy `email_verified=false` 帳號，衝突時回 409 且帳號資料完全不變。
- [ ] 校方 OAuth start 同一來源 10 分鐘最多 20 次、每類最多 2,048 個 active state；production 的一般 OAuth、校方 OAuth、學生證 token 與兩類 rate limit 必須共用 Supabase TTL store。以兩個 App instance 驗證 callback、consume、同 session 替換、容量、限流，以及錯誤帳號／session／provider／browser 不耗用真正 state。
- [ ] 套用 `20260823100000_atomic_auth_account_mutations.sql` 後，驗證 provider／subject 唯一性、OAuth account＋provider link＋session 同 transaction commit、學生身分 exact-session CAS、資料庫時鐘與到期競態；一般 profile 僅能 field-level patch，calendar 舊 token 不得在撤銷後復活。`service_role` 對 account table 的 direct UPDATE 必須被撤銷，production repository 的相容 upsert 必須 fail closed。
- [ ] 套用 `20260823130000_atomic_workspace_and_suspension.sql` 後，驗證 workspace typed revision CAS 與 calendar projection 在同一 transaction，且固定採 account → workspace 鎖序；同時驗證學生 suspension 與 private append-only audit 同 transaction、RPC 僅授權 `service_role`、workspace／audit direct DML revoked，以及 audit 超過 90 天的 purge 邊界。
- [x] 歷史證據：在全新本機 PostgreSQL／兩個獨立 PostgREST／Storage API file backend 執行截至 `20260829100000_atomic_account_deletion.sql` 的前 20／20 migration apply、30／30 RLS、grant／direct DML、transient auth／workspace 並行、整體刪帳 rollback／timeout receipt／真實物件 delete／replay 及巢狀 orphan cleanup 驗收。
- [x] 現行 schema：fresh 套用 21／21 migrations，驗證新增兩張 workflow issue report tables 的 RLS、grant、direct DML denial、submit／review RPC、冪等、限流、review CAS、刪帳去識別、90 天 retention、最多 24 小時 terminal replay grace 與 purge；最終必要 run 為 `status=passed`、`cleanup_status=passed`，且 runtime project container／network／volume 均為 0。
- [x] 以兩個獨立 PostgREST 實例驗證公開發文冪等重送、父貼文刪除／留言新增、相反方向邀請、封鎖／傳訊與雙管理員檢舉審核，確認無 orphan、無重複 resource／receipt、無部分寫入。
- [x] 在公開發文、公開 moderation、私人邀請、私人訊息、檢舉與檢舉審核的 mutation receipt 最後寫入點注入 `P0001`；六種操作都向外傳遞錯誤，且 resource／狀態／revision／audit／receipt 均完整 rollback，`partial_rows=0`。
- [ ] 在正式 Supabase project 的實際 Storage backend 重驗 delete timeout、重送、告警與備份還原，並重驗多 API instance 競態與既有資料升級路徑。完成前 production 維持 single worker 並保持 `NOT READY`。

### C. 資格、志願與個人申請計畫

- [ ] 選擇學校、學系、年度與梯次後，系統顯示實際套用的規則範圍。
- [ ] 校系覆寫正確，衝突或缺值顯示待確認而不是猜測。
- [ ] 建立兩個以上志願後，切換、重新整理及第二個瀏覽器 session 都能恢復。
- [ ] 每一步都顯示負責人、承辦單位、送件方式與下一步。
- [ ] 不需要學生再到外部自行拼湊核心申請步驟；若仍需外查，記為問題。

### D. 文件、表單與 PDF

- [ ] 未登入及公開免費帳號仍可查看申請規定、官方來源並下載校方原始表格。
- [ ] 未登入直接呼叫自動填表／PDF API 回傳 401；公開免費帳號回傳 403；不能只靠 Web 按鈕隱藏。
- [ ] 封閉測試帳號仍可免費完成逐欄預覽、核對與 PDF 產生，且畫面清楚說明不會扣款。
- [ ] 文件完整性檢查在封測帳號只執行非 AI 規則；原檔只在當次請求記憶體處理且 response 為 `no-store`。
- [ ] 首次選擇文件時傳送同意預設未勾；未勾直接送出須聚焦同意欄位且 `/document-check` request 數為 0，不能因已登入而自動同意。
- [ ] 勾選本次傳送同意後只送出 1 次；更換文件會立即取消同意，未重新勾選前用 UI 或程式觸發 submit 都不得增加 request。
- [ ] `/auth/`、`/account/`、文件、顧問、日曆、管理等私人 API，以及帶 Cookie／Authorization／匿名身分憑證的動態 response，均不得被瀏覽器或共用快取持久保存；既有 `no-store` header 不被弱化。
- [ ] 未登入文件檢查 API 回傳 401，公開免費帳號回傳 403；直接送出 `use_ai=true` 即使是訂閱帳號也回傳 503。
- [ ] Web 的 AI 深度檢查控制項停用，並明示不會傳給外部 AI、也不會啟動本地模型。
- [ ] 文件改寫頁顯示「本地 AI 尚未設定」，所有輸入與送出按鈕停用，瀏覽器不送出 `/ai/rewrite-document`。
- [ ] 即使測試環境設定 `OPENAI_API_KEY`，`/ai/status` 仍為 `runtime_state=paused`、provider／model 為空，且規則式顧問不發生外部 AI request。
- [ ] 使用全新資料目錄開啟林肯大學生活情報，確認顯示「官方生活資訊已查核」、2 個官方來源；切到未收集的長庚合作校時仍顯示待查核，不以共通國家指南冒充校方資料。
- [ ] 搜尋馬來亞大學並開啟生活情報，確認顯示「官方生活資訊部分查核」、2026 秋季校內宿舍不可用及 3 個官方來源；不得顯示成完整查核。波茲南理工與 UIC Barcelona 同樣須保留年份、費用浮動、床位／合約及第二位真人審查限制。
- [ ] 搜尋香港中文大學、北京清華大學與 UWM 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。CUHK 須區分 2026/27 費用與 2025/26 一般生活估算；清華須明示兩個現行官方頁面的房型描述不完全一致；UWM 須保留 2026-05-01 一般宿舍合約截止、候補與「財力證明不是實際預算」限制，且顯示 6 個來源。
- [ ] 搜尋 Fordham、University of Perugia 與 Paris-Saclay 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。Fordham 須明示 USD 10,000 為財力證明而非預算、其他交換費用仍是 2025/26 且住宿不保證；Perugia 須明示住宿意願不等於床位、生活費為 2026-04-28 更新的估算；Paris-Saclay 須保留多校區差異、2026/27 有限住宿與 48 小時確認，以及生活費頁的 2021／2021-22 金額不能作 2026/27 預算。
- [ ] 搜尋 University of Málaga、KEDGE Business School 與 Thomas More 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。Málaga 須明示校方不提供住宿且沒有現行完整 2026/27 生活費表；KEDGE 須等提名後確認 Bordeaux 或 Marseille，2025/26 fact sheet 與未標學年的房租不得冒充 2026/27；Thomas More 須明示一般學位生 EUR 850–1,150 估算不含學費與交通，且實際交換校區依課程決定。
- [ ] 搜尋 Shanghai Jiao Tong、Fudan 與 TH Lübeck 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。上海交大須保留住宿不保證與宿舍費標準於 2020 年核准的提醒；復旦須區分校級／院級及 Handan Campus 2026 候補，不得套用特定學院舊 fact sheet；TH Lübeck 須明示 2026/27 費用估算、住宿不足，以及 2026 年 3 月迎新日期已過且不能冒充下一梯次。
- [ ] 搜尋 VSB、EIGSI 與 Kangwon National University 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。VSB 須明示 EUR 500／月只是估算、住宿申請與 CZK 8,000 保證金不等於床位；EIGSI 須限定 La Rochelle、保留 residence 目前已滿與春季多為法語；江原國立大學須限定 Chuncheon Campus，同時顯示交換生宿舍保障與公開費用表仍為 2019 年、不能當現行預算。
- [ ] 搜尋 RWU、TU Chemnitz 與 SKEMA 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。RWU 須區分一般 EUR 1,500 國際學費與合作協議交換生免繳、宿舍意願不等於床位；TU Chemnitz 須使用 2026/27 EUR 341.40 學期費，並明示 EUR 970 月估算底層仍是 2021 調查；SKEMA 須先確認 Lille／Grand Paris／Sophia Antipolis，Grand Paris 的 EUR 900–1,800 預算不得套到其他校區，三個法國校區也都沒有校內住宿。
- [ ] 搜尋 SGGW、Toulouse INP 與 Chandigarh University 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。SGGW 須顯示 2026/27 fact sheet 與一般 FAQ 提名期限不一致、交換生住宿不能直接套一般 eHMS 流程；Toulouse INP 須依錄取學校區分期限、校區與 CROUS，未標學年的生活費不可視為現價；Chandigarh 須明示校址為 Mohali、一般國際學生 USD 宿舍價不是交換生費率，2021 fact sheet 的免費住宿不得當成現況。
- [ ] 搜尋 WUM、Gachon 與 UNYP 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。WUM 須區分 Erasmus 國際交換生 PLN 1,220 與其他外校學生 PLN 1,312 的 DS2BIS 月費，不能自行採較低類別；Gachon 須使用 2026 外國學生宿舍價、明示交換頁未標更新日與 Medical Campus 課程限制；UNYP 須把 USD 6,000 可選套裝、自行找房與沒有校內宿舍分開，Fall 2026 的 2026-04-17 截止亦須顯示已過。
- [ ] 搜尋 EPF、ECAM LaSelle 與成城大學經濟學院並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。EPF 須把 Cachan、Montpellier、Troyes 的課程與授課語言分開，2026 暑期法語工程師住宿價不得套到一般學期交換，housing reservation 不等於床位；ECAM 的 EUR 770–1,149 月預算須標成一般工程課程估算，CROUS 與約 150 房校園宿舍都不保證交換生床位；成城須明示依房況分派 Amista 或私人住所、Amista 只有 20 個交換生房間，JPY 80,000 月獎學金也有合作校名額限制。
- [ ] 搜尋 IPSA、DHBW Karlsruhe 與 Rennes School of Business 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。IPSA 須把合作校交換與非合作校 Study Abroad 的 EUR 4,500／學期分開，2025/26 fact sheet 不得冒充 2026/27 現況；DHBW 須明示宿舍只供部分學生、至少六個月租期與提早離開仍須付餘月，限時 KVV 權益也不得寫成全天免費；Rennes 的 EUR 450–700 月租只適用 Rennes、住房協助不保證床位，incoming 頁與 2026/27 fact sheet 對 Level 2 春季資格不一致，須由提名信或 exchange office 確認。
- [ ] 搜尋 Chiang Mai University Faculty of Public Health、HCM-UTE 與 Management and Science University 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。CMU 須使用 2025 年 9 月新版校級 fact sheet，生活費不是公衛學院保證價格、免費校車也不是全清邁免費交通；HCM-UTE 須顯示現行更名，2025/26 本地既有生十二個月宿舍價與 2020 Teaching Practicum 套裝都不得套用學期交換；MSU 須明示 March 2023 文件只是歷史基準、四個月 triple-sharing 只限本地生，一般房型最短六個月且不保證指定房型。
- [ ] 搜尋 Rutgers、TU/e 與 CHA University 並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。Rutgers 須明示未確認長庚雙學位的 school／campus／學位與專案費率，New Brunswick 一般 USD 62,782 估算及 USD 70 通用申請費都不是長庚雙學位帳單；TU/e 須把 EUR 1,200／月一般學位生估算與 2023–24 Chemical Engineering and Chemistry 系所資料留在原適用範圍，舊期限不得建立 2026/27 提醒，住房也不保證；CHA 須明示母校繳學費不等於其他費用全免、Pocheon 宿舍存在不等於交換生有床位，`(~2019)` 與 2023 planned 短期方案不能冒充現行學期交換。
- [ ] 搜尋 UNIFESP、武漢大學與福州大學並開啟生活情報，三者都只能顯示「官方生活資訊部分查核」。UNIFESP 須明示母校繳 tuition／fees 不等於零成本、私人租屋可能有 seguro fiança，且七個 campus 不可混用；武漢須保留 June 2016 交換表、舊站 RMB 600–1,400 月租、2022 免費校車與 2026 儲值 campus card 的時效衝突，舊 15 April／15 October 不可轉成提醒；福州須明示學費互免取決於協議、2026 一般國際學位生費用不是交換帳單、一般雙人房 RMB 3,500／年不保證交換生床位，2025 秋季 15 May 也已過期。
- [ ] 搜尋 ICD Business School 並開啟生活情報，只能顯示「官方生活資訊部分查核」。須等提名或錄取通知確認 Paris／Toulouse campus，incoming 頁提及 Lyon 不代表 2026–27 exchange 已開放；Paris EUR 5,495／學期標示不適用交換生、Toulouse 亦寫明交換免學費，但不得顯示成生活免費。兩校區住宿與交通費率不可混用，住宿搜尋支援不等於床位保證；春季 application 的 1 November／15 November 衝突不得直接建立提醒。
- [ ] 文件清單正確區分正本、影本、份數、簽名、核章及附件順序。
- [ ] 表單缺值保持空白，不使用臆測內容補齊。
- [ ] 每個欄位可逐項預覽；內容變更後，舊的「我已核對」失效。
- [ ] 未勾選核對前不能產生可送件 PDF。
- [ ] PDF 頁數、中文、檔名、附件順序與列印指示正確。
- [ ] 保存每一個個人文件前都再次取得明確同意；登入不等於同意。
- [ ] 未同意保存時，後端拒絕永久保存。

### E. 送件進度、提醒與同步

- [ ] 紙本、線上、Email、親送與混合送件顯示不同且正確的狀態。
- [ ] 紙本流程可分辨寄出期限與送達期限；缺值明確標為待確認。
- [ ] 只有參考月份、慣例或「以當期公告為準」的時程不會被轉成精確日期，也不會加入行事曆或提醒。
- [ ] 長庚 115-2 顯示為「本梯次已截止」，且清楚說明下一梯次不能沿用 2026/04/21–06/06。
- [ ] 長庚 2026/09/21 語言證明期限只顯示給初審名單姓名旁標記 `＊` 的申請者，不冒充所有學生的申請截止日。
- [ ] 國立臺北大學每年 9 月底／10 月等歷年原則只顯示為參考，沒有自動套用下一年。
- [ ] 只有具有官方 HTTPS 來源、查核日期及正確送件語意的精確期限才可產生提醒；紙本只有寄出日、沒有送達日時必須拒絕。
- [ ] 平台不宣稱已代替學生送件。
- [ ] 收件或送達證明明示為學生自行記錄，不保存原始證明檔。
- [ ] Web 通知已讀狀態、期限與完成狀態可跨 session 同步。
- [ ] 文件準備狀態、學校申請進度及個人日曆任務都只能由登入帳號建立或更新；訪客只能查看官方日期、文件說明與申請規定。
- [ ] Email 提醒預設關閉，只有明確選擇後才啟用。
- [ ] 新增個人任務時可選擇所屬申請學校；未選擇的「一般任務」不納入跨校衝突判定，學校欄位可跨 session 同步。
- [ ] 兩所不同申請學校在同日或相距 3 天內有已確認日期時顯示衝突並可定位日期；同校多步驟、無效日期、未公告期限或只有一份計畫時不誤報。
- [ ] 多計畫衝突分析只供登入且具進階權益的帳號使用、回應 `no-store`、不另存分析資料；封測 billing 維持關閉，公開免費層拒絕存取。
- [ ] 新增個人任務時可明確輸入 0–90 天準備時間；0 不自動安排，其他數值只從學生已填期限倒推開始日，不猜測官方期限或文件工期。
- [ ] 建議開始日會顯示在 Web 並同步到外部日曆；開始當天產生站內提醒，任務狀態可切換為未開始、準備中與已完成。
- [ ] 標記完成後，準備開始標記從 Web 與外部日曆移除，該任務不再產生新的站內或外部日曆提醒；重新改回未完成時可依原準備天數重算。
- [ ] 公開免費帳號仍可使用基本 Web 截止提醒，但不能讀取、建立或更新 Google／Apple／Outlook 私人訂閱網址；伺服器回傳 403，不能只靠隱藏按鈕。
- [ ] 帳號失去外部日曆權益後，既有無登入 feed 立即回傳 404；使用者仍能從鎖定說明撤銷舊網址，避免只能由客服清除。
- [ ] 日曆同步狀態、啟用、更新與撤銷 response 均為 `no-store`、`nosniff`；封閉測試帳號維持免費全開且 billing 為 false。

### F. 社群、隱私與刪除帳號

- [ ] 訪客可以公開閱讀，但不能發文或留言。
- [ ] 公共留學板與語言學校板允許符合門檻的帳號匿名發言。
- [ ] 大學板拒絕未驗證學生與跨校學生發言。
- [ ] 發文時可選本名、已驗證校系或匿名；顯示結果符合選擇。
- [ ] 刪除帳號後，私人工作區、表單草稿、私人文件與 session 無法再存取。
- [ ] 公開內容保留，但作者統一顯示「已刪除帳號」，不能連回個人。
- [ ] 訪客、未登入帳號、未完成學生身分驗證者都不能送出申請規定錯誤回報；已驗證學生只能回報自己目前可見且母校相符的 workflow／step。
- [ ] 回報必須提供公開 HTTPS 官方來源；私人網址、Email、電話或其他聯絡資料不得進入來源欄或公開管理卡片。
- [ ] 模擬 POST 已 commit 但 response 遺失後重新整理：Web 必須恢復原內容並沿用同一 mutation ID，不得因修改內容取得新 ID 或建立重複回報。
- [ ] 管理員只能在獨立佇列以「成立／不成立」結案；任何結案都不得直接建立 workflow revision、approval、publication 或降低 release blocker。
- [ ] 兩位管理員同時處理，或 GET／PATCH 遇到 404／409 時，舊 response 不得覆蓋新 filter；佇列重新載入並顯示明確結果不明／已被處理狀態。
- [ ] 帳號匯出包含本人回報；刪帳當下已結案回報立即刪除，pending 回報去識別最多保留 90 天，之後才結案的去識別終態只為冪等 replay 最多再保留 24 小時後 purge。

### G. 易用性與可及性

- [ ] 1440px 桌面與 390px 手機寬度沒有水平溢位。
- [ ] 瀏覽器 200% 縮放仍可完成核心任務。
- [ ] 可只用鍵盤完成登入、搜尋、比較與主要表單。
- [ ] 對話框有合理初始焦點，Escape 可關閉並回到原按鈕。
- [ ] 錯誤、空白與待確認狀態不只靠顏色辨識。
- [ ] 學生能理解下一步，不需要產品人員在旁解釋。

## 3. 兩校關鍵規定雙人查核表

每一條會影響學生「能否申請、何時送件、送什麼、送到哪裡」的規定都必須逐筆登錄。審查者 A 與 B 必須分別開啟官方來源核對，不可由同一人代填兩欄。

系統操作也必須使用兩個不同的內容管理帳號。生活情報部分，A、B 各自在自己的登入狀態下逐筆開啟完整 profile，親自開啟並勾選全部來源、核對 12 個內容區塊，再留下結論與說明；同一審查者更新結論時，舊事件保留但不再計入目前有效進度。兩位都核可且沒有人要求修正時只標示 `ready_for_promotion`，不會自動改變學生資料。其後必須由 A 或 B 其中一位有效核可者填寫升級說明、勾選學生可見變更確認並明確執行；升級事件要保存兩筆核可、候選／公開指紋與完整公開 profile。原始候選不覆寫，之後候選內容若改變必須重新雙審，學生仍看上一個已核准版本。若升級後發現錯誤，內容管理者須從公開歷程確認目前事件與指紋、填寫復原原因並勾選立即變更確認；系統只能 append 新的復原事件，不得修改或刪除舊歷程。復原後先前核可失效，必須由 A、B 重新核對才能再次升級。申請流程部分，A、B 再從「既有流程待納入雙審」搜尋合作校，確認母校、計畫與版本後建立待審副本。建立操作不得改變學生內容，重複操作也不得產生第二份 pending revision。接著前往待審佇列，載入版本對照，逐欄檢視流程層級、步驟、文件與官方來源。A、B 都必須親自開啟並勾選全部來源，逐項核對流程適用範圍、所有步驟與文件，再分別留下查核說明並核准；核准紀錄要顯示相同的候選內容雜湊，以及各自確認的完整來源數與關鍵規定數。同一帳號不能重複核准。畫面必須顯示兩筆不同審查者紀錄，之後才可由其中一位正式發布。表格與真人操作不能由自動化測試或 API fixture 取代。

- [ ] 申請流程載入版本對照後，只勾選部分官方來源／關鍵規定並輸入查核說明；重新整理後回到同一待審 revision、重新載入版本對照，勾選與說明必須恢復。草稿鍵須同時隔離管理者、revision ID 與候選內容雜湊，換管理者或候選內容改變後不得沿用。
- [ ] 按申請流程的「清除本頁暫存」只重設尚未送出的勾選與說明，不得新增、修改或刪除後端核准／發布紀錄；核准、退回或發布成功後清除草稿，後端拒絕或網路錯誤時保留。
- [ ] 申請流程草稿尚未送到後端且不是核准證據；不得用它解鎖發布、增加核准人數、補查核日期、同步到另一裝置或影響 `audit-web-release`。恢復草稿後仍須載入版本對照並完成全部來源與規定，後端完整門檻不變。
- [ ] 在 backlog 按「開啟待審版本」後，URL 只新增 `review_status=pending_review` 與目前 `workflow_revision`，不得包含勾選、查核說明、來源內容或任何 token；重新整理須回到相同受保護 revision 並顯示定位提示。發布、退回或手動清除定位後移除 `workflow_revision`；不存在或已處置的 ID 不得套用到其他版本。
- [ ] 申請流程待審視角選「我的待辦」時，只顯示目前帳號尚未核准且未達雙審門檻的 revision；「我已核准」只依後端有效核准者 ID；「可由我發布」必須同時已達兩人門檻且目前帳號是有效核准者。三種篩選都要同步更新目前筆數與等待／可發布摘要，不得依本機草稿推算。
- [ ] 申請流程獨立核准須即時整合全部官方來源、全部關鍵規定與去除空白後的查核說明；資料補正或版本對照未完成時維持既有靜態阻擋。可開始核對後，下一缺口依來源、規定、說明順序聚焦；只填空白仍視為未填寫，任一項未完成時核准按鈕保持停用。前端完整只開放送出，不得取代後端內容雜湊、完整來源與規定清單驗證。
- [ ] 有效申請流程批次中的未核准 revision 才顯示「核准並前往下一筆我的待辦」，且必須與一般核准共用完整門檻並在送出期間同步鎖定。成功後先重新驗證原 snapshot-bound 批次，再依固定批次順序聚焦下一筆並更新 `workflow_revision`；批次過期、載入失敗、目前資料門檻篩選為空或已無個人待辦時不得跳出目前安全範圍，也不得宣稱雙審或發布完成。
- [ ] 展開「補正適用學年度與來源證據」後，畫面須即時顯示已選來源 X／N、下一個缺少欄位及儲存狀態。只驗證本次勾選來源；未勾選來源保持不變，允許分次補正。流程學年度／梯次沒有實質修改且未勾來源、或任一已勾來源缺年度／證據中繼資料／必要 HTTPS 替代網址時，儲存必須停用；不得提供自動猜值、全選或批次代填。
- [ ] 補正區的流程欄位、說明、來源勾選與各來源欄位輸入後，只暫存在目前分頁；重新整理同一待審 revision 時須自動展開並恢復。草稿鍵必須綁定管理者 ID、revision ID 與候選內容雜湊，讀回只接受目前已知且不重複的來源 URL、允許的角色／權威值與受長度限制的字串；換管理者或內容版本不得沿用。
- [ ] 畫面須明示補正草稿尚未送到後端且不是核准證據。「清除補正草稿」只還原目前候選值，不能修改後端內容、核准或發布；補正儲存、核准、退回或發布成功後清除，後端拒絕或網路錯誤時保留。
- [ ] 每個來源列須即時明示本次未選取、第一個缺少欄位或本次欄位完成；未選取列即使填有候選網址也不得顯示會被儲存。已勾選列只有來源年度、必要 HTTPS 替代網址及缺少的來源名稱／角色／權威層級全部有效時才轉為完成。
- [ ] 「前往下一個缺少欄位」須依流程年度、修正說明、來源列順序定位第一個缺口，展開補正區並把鍵盤焦點移到實際 input／select／textarea；全部本次欄位完成後隱藏。按鈕不得自動填值、勾選、儲存或跳過真人來源確認。

- [ ] 未登入開啟 `/admin/content-review` 會被拒絕；非內容管理者登入後仍會被拒絕。
- [ ] 在生活情報工作台把「母校」切到長庚大學，確認顯示 77 筆、完整查核 19、待人工續審 58、明確等待第二位真人 46、246 個待審來源，下載 58 列 CSV 且每列母校皆為長庚；切換時搜尋與進度篩選須清空。
- [ ] 再切到國立臺北大學，確認顯示 203／118／85／0／224，下載 85 列 CSV 且每列母校皆為臺北大學；公開／復原歷程摘要也須跟著切換，不得短暫或最後停留在長庚 response。兩校 CSV 都須帶目前母校及 64 字元 snapshot，舊 snapshot 為 409。
- [ ] 在生活情報進度篩選選擇「我的待辦」，只顯示目前登入管理者尚未留下有效結論的 profile；選擇「我已留下結論」則只顯示該管理者已留下目前有效結論的 profile，不得把另一位管理者的結論算成自己的。
- [ ] 任一 profile 勾選部分來源／內容區塊並輸入結論與說明後重新整理同一分頁，暫存應恢復；按「清除本頁暫存」後只重設該表單，不得新增、修改或刪除後端審查證據。換管理者或 profile 內容指紋改變時不得沿用舊暫存；成功送出後本頁暫存必須清除，送出失敗則保留。
- [ ] 畫面須明示分頁暫存尚未送到後端且不是審查證據；不得把 `sessionStorage` 草稿用於同步、雙審計數、核准、升級、發布或 Web 發布就緒判定。
- [ ] 下載「生活情報雙人分工 CSV」：長庚 58 筆固定分為 6 批、臺北大學 85 筆固定分為 9 批，預設每批 10 筆，末批分別為 8 與 5 筆。CSV 必須包含完整來源、缺口、工作台路徑及批次位置，人工 A／B、查核時間、問題與處置欄預設空白，且採 UTF-8 BOM、公式防護、`no-store` 與 `nosniff`。
- [ ] 從任一批次工作台連結進入後，只顯示該母校該批的 profile（完整批次正好 10 筆），並明示批次編號與筆數；清除批次定位後恢復該母校完整 queue。切換母校須清除批次參數，舊非同步批次 response 不得覆蓋目前畫面。
- [ ] 批次定位成功後顯示「下載目前批次逐項查核表」；每個 profile 必須恰有 12 列固定內容區塊，另為每個官方來源各列一筆。全部 143 筆待審的理論總量為 2,186 列（長庚 58×12＋246＝942；臺北大學 85×12＋224＝1,244），但 API 每次只匯出目前快照中的單一批次。
- [ ] 逐項表列出項目鍵、名稱、核對要求、目前候選內容、對應來源、profile 指紋、工作台與學生頁路徑；A／B 是否核對、完成時間、說明、疑義與處置欄都保持空白。表格不能匯入或形成審查事件，真人仍須回工作台各自勾選全部來源與 12 區塊。
- [ ] 增加第一位或第二位審查進度不改變生活情報「審查內容指紋」、批次 ID 或成員；profile 內容、待審成員、升級或復原造成實質內容／成員改變時，舊批次指紋回傳 409，工作台不得套用舊定位。不存在的目前批次回傳 404。
- [ ] 從有效生活情報批次保存第一份或第二份審查後，Web 須立即重驗且在指紋未變時維持原批次。明確升級或復原改變待審成員後，操作成功訊息必須同時明示原批次過期、舊定位未套用與須重新下載，逐項表入口隱藏；非 404／409 的重驗錯誤也須明示舊定位未套用。URL 的過期批次參數保留到管理者按「清除過期批次」，不得靜默換成另一批成員。
- [ ] 有效生活情報批次中，目前帳號尚未留下結論的 profile 才顯示「保存並前往下一筆我的待辦」。保存成功後須清除搜尋、切到「我的待辦」，依原批次固定順序展開並聚焦下一筆；若已無個人未審項目，只能宣告目前帳號待辦完成，並明示不代表另一位審查者、雙審、升級或發布完成。批次過期或重驗錯誤時不得續接。
- [ ] 有效生活情報批次摘要須顯示目前帳號的待辦數，並提供「開啟第一筆／下一筆我的待辦」及「顯示此批次我的待辦」。第一筆與下一筆須依分工清單固定順序，清除搜尋、切到個人未審篩選、展開 profile 並移動鍵盤焦點；完整待辦須清除焦點並收合卡片。手動展開批次卡可更新下一筆起點；待辦為零時按鈕停用，過期或載入錯誤時不得顯示這些導覽。
- [ ] 生活情報 row 含 `missing_sources`、`insecure_sources` 或 `missing_last_checked` 時，審查表須逐條顯示阻擋原因、預設並鎖定「內容需要修正」，核可 option 必須 disabled；舊草稿的核可值不得覆蓋。送出函式須再次以目前 queue row 驗證，DOM 竄改也不能呼叫審查 API。只有不存在這三種缺口時可選核可，且綠色提示必須明示仍須逐頁、逐區塊真人核對。
- [ ] 「核可門檻」須獨立於雙審進度提供全部／可選擇核可／只能要求修正篩選，並與單卡使用相同三種阻擋代碼。批次摘要的我的待辦數不受門檻篩選縮小，另顯示兩類結構數；第一筆／下一筆與保存續接只能在目前門檻內前進。門檻為空但其他門檻仍有待辦時，必須顯示專用空狀態與「目前門檻篩選沒有我的待辦」，不得顯示整批完成；切換母校須清除門檻條件。
- [ ] 每張生活情報審查卡須即時顯示官方來源 X／N、內容區塊 X／12 與剩餘數量；「前往下一個未核對項目」依來源後區塊的固定順序移動鍵盤焦點，不得自動開啟、勾選、保存或形成證據。重新整理恢復草稿與手動清除後須依實際勾選重算；全部可核對項目完成只代表可填結論，上方核可阻擋仍有效。受阻擋卡清除草稿後結論仍須固定為要求修正。
- [ ] 單卡即時送出門檻須同時計算全部來源、12 個區塊與去除首尾空白後至少 10 字的審查說明；任一未完成時一般保存及保存續接都停用。勾選完成但說明不足時，導覽改為「前往審查說明」並聚焦 textarea；達成門檻只開放按鈕，不得跳過後端對快照、內容指紋、完整核對清單、說明及核可阻擋的重新驗證。
- [ ] Web 總閘門顯示兩校生活情報 280 筆、完整查核 137、待審 143、待審來源 470。任何一筆 `official_partial`、未收集、待雙審或尚未明確升級都維持發布阻擋。
- [ ] `/admin/destination-profile-review-queue`、`.csv`、`/admin/destination-profile-review-batches.csv`、`/admin/destination-profile-review-batches/{batch_id}`、其 `/checklist.csv`、`POST /admin/destination-profile-reviews`、`POST /admin/destination-profile-promotions`、`GET /admin/destination-profile-publications` 與 `POST /admin/destination-profile-rollbacks` 只允許內容管理者；未登入為 401、一般學生為 403，CSV 回應採 `no-store`、`nosniff`、UTF-8 BOM 及 `= + - @` 公式防護。
- [ ] 以目前 `expected_snapshot` 下載成功，過期指紋回傳 409；CSV 包含每個 partial profile 的完整來源、查核註記、缺口代碼、系統有效核可數、修正要求數、目前有效真人證據與是否可交下一步。CSV 不能匯入、建立 revision、改成 `official_verified` 或發布。
- [ ] 每位審查者提交前必須逐一勾選該 profile 的全部官方來源與 12 個內容區塊，並留下至少 10 字說明；缺任一來源／區塊回傳 422，過期 queue 或 profile 指紋回傳 409。
- [ ] 第一位核可後只顯示 `1/2`；第二位若選擇要求修正，進度為 `changes_required` 且不得顯示可交下一步。第二位重新完整核可後才顯示兩位目前有效證據與 `ready_for_promotion`。
- [ ] 同一審查者更新結論時，前一事件仍留在 append-only 稽核歷程並標示已由後續結論取代；目前進度只計每位審查者最新且綁定目前 profile 內容指紋的事件。profile 內容變更後，舊指紋事件不得套用。
- [ ] `ready_for_promotion` 本身不得修改學生資料；只有其中一位目前有效核可者填寫至少 10 字升級說明並勾選學生可見變更確認後，才能新增升級事件。非核可管理者、核可不足、存在修正要求、過期 queue／profile 指紋都必須拒絕。
- [ ] 生活情報審查、升級與復原事件只透過後端寫入各自的原子 JSONL fallback 或 RLS／service-role-only Supabase append-only 表；沒有 update／delete grant。CSV、核可或修正前後，學生 `/destination-profile` response 必須完全相同；明確升級後才變為 `official_verified`。復原必須新增事件並恢復更早核准快照；若無更早核准版本則恢復目前 `official_partial` 候選。既有歷程不能改寫，復原後舊核可不再計入。升級或復原均不得連帶修改申請規則、文件、期限或通知。
- [ ] `GET /admin/application-workflow-publications` 與 `POST /admin/application-workflow-rollbacks` 只允許內容管理者；未登入為 401、一般學生為 403。復原前須選擇內容不同、曾完整雙審的舊發布 revision，並鎖定目前 revision ID、版號與 64 字元內容指紋；有 pending revision、過期快照、稽核鏈不完整或學生公開內容不一致時均為 409。
- [ ] 申請流程復原必須建立更高版號的 `rollback` revision，保存撤回版、恢復目標、操作者、時間、至少 10 字原因及恢復內容的原雙審證據；不得 update／delete 舊 revision。學生公開流程精確回到舊快照，受影響且已建立計畫的學生只收到一次內容更新通知，後續修改仍須重新雙審。
- [ ] 申請流程發布子指紋必須包含 publication action、base version、撤回／恢復 revision ID、required review count 與復原原因；`publication_history_integrity_gap_count` 必須逐 workflow 核對目前公開 payload、發布快照、版本鏈與原雙審證據。缺失、跨流程、重複或被竄改的復原參照均要改變子指紋與 Web 總指紋並阻止 READY。
- [ ] 正式 Supabase 必須套用 `20260819170000_application_workflow_publication_integrity.sql`；撤回與恢復 revision 以 `(workflow_key, id)` 綁定同一流程、刪除採 restrict，同一撤回／恢復組合只能存在一筆 rollback revision，且不新增 `anon`／`authenticated` 權限。
- [ ] 升級事件保存兩筆目前有效核可、操作者、時間、候選／公開內容指紋及完整公開 profile；相同候選重送須冪等。新候選內容出現時舊審查不得套用，學生維持上一個已核准公開版本，新候選重新進入雙審。
- [ ] 公開歷程依事件時間完整顯示升級者、復原者、原因與前後指紋；只有最新事件仍是直接升級時可復原。送出時若 active promotion、latest event 或目前公開指紋任一已變更必須回傳 409；重送同一復原請求須冪等，不得新增第二筆事件。
- [ ] 工作台頂部 Web 總發布閘門顯示 `NOT READY`、280 筆流程、0 筆正式發布、7,067 個關鍵規定、280 筆生活情報、137 筆完整查核、143 筆待審、9 類阻擋與 64 字元總指紋；重新載入相同資料時指紋一致，任一資料面或審核證據改變後總指紋也改變。
- [ ] `/admin/web-release-readiness` 與 `/admin/application-workflow-release-readiness` 都只有內容管理者可讀，未登入為 401、非管理者為 403，回應採 `no-store` 與 `nosniff`，且不建立或修改任何 revision／審查／升級／復原事件；前者是 Web 總閘門，後者只保留申請流程子報告。
- [ ] `exchange-info --data-dir data audit-web-release` 輸出與 `/admin/web-release-readiness` 相同的總報告；目前有阻擋時 exit code 為 2，只有申請流程與生活情報全部檢查通過才為 0，任一目錄為空也不能被誤判為 READY。
- [ ] 目前 9 類阻擋的實際值為：申請流程的未正式發布 280、缺學年度 77、缺精確期限 280、缺來源證據 215、來源年度缺口 1,834、查核日期缺口 215、非 HTTPS 12、待確認流程／步驟／文件 6,253；以及生活情報待審 143。兩面的發布歷程完整性缺口都為 0。
- [ ] 即使公開資料被直接標為 `published`，若找不到相同版本、公開內容、候選雜湊、兩位不同審查者、完整來源與規定清單的證據，閘門仍維持 NOT READY。
- [ ] 「下載雙人審查分工 CSV」只允許內容管理者使用；未登入為 401、非管理者為 403，回應採 UTF-8 BOM、`no-store`、`nosniff` 與試算表公式防護。
- [ ] 預設每 10 個 workflow 一批，匯出正好為 280 列／28 批、280 個不重複 workflow、7,067 個關鍵規定；CSV 列出申請流程子報告的「發布狀態指紋」及供批次定位的「審查內容指紋」，不得誤用包含生活情報的 Web 總指紋，資料在產生期間有實質內容變更時拒絕交付舊清單。
- [ ] 建立待審版本或增加核准證據時，申請流程發布子指紋與 Web 總指紋會更新，但審查內容指紋、批次 ID、分工順序與既有連結維持不變；候選內容修改或正式發布造成待審成員改變時，審查內容指紋必須更新，舊連結回傳 409。
- [ ] 審查內容指紋包含批次排序 schema 版本；若部署變更批次成員演算法，舊版連結必須過期，不能在相同指紋下靜默指向不同 workflow。
- [ ] workflow 已有 pending revision 時，backlog、分工 CSV、批次 API、來源證據群組與逐規定 CSV 都以最新候選版重算年度、梯次、來源、缺口及規定；學生公開 API 在正式發布前仍維持原公開版。
- [ ] backlog 與分工 CSV 顯示每筆 `0/2`、`1/2`、`2/2` 實際核准進度；工作台可篩選待第一位、待第二位與已達雙審門檻，批次定位摘要顯示該批三種進度數量。
- [ ] 分工順序為固定的內容風險優先排序，非 HTTPS、規定來源證據、來源年度、精確期限與待確認規定等缺口較高者在前；真人核准自動補上的查核時間不參與批次排序，因此 0／1／2 位進度變化不會換批。重複下載相同審查內容指紋時順序與批號一致。
- [ ] 每列的審查者 A／A 查核時間、審查者 B／B 查核時間、問題與決定預設空白；CSV 只供分工，不能匯入、建立 revision、修改公開資料、核准或發布。
- [ ] 從 CSV 的工作台連結開啟後只顯示對應的單一 workflow 並取得焦點；清除精確連結篩選後恢復全部 280 筆待辦。
- [ ] 從同一列的「批次工作台路徑」開啟後，後端只回傳目前快照中該批資料，工作台正好顯示該批 10 筆且標示批次 ID；清除後恢復全部 280 筆。未登入為 401、非管理者為 403、錯誤快照為 409、不存在批次為 404。
- [ ] 批次 ID 必須同時綁定審查內容指紋、batch size 與批號；按「建立目前批次待審副本」前須明示尚未建立／將沿用筆數並再次確認。取消不得寫入；成功只建立或沿用 pending revision，不得建立核准、發布、通知或變更學生 API。相同批次重試須回傳相同 revision IDs，錯誤指紋為 409、size 與 ID 不符或批次不存在為 404。
- [ ] 目前批次全部具有 pending revision 後才顯示「開始審查此批次」。進入後切換為 `pending_review`、預設「我的待辦」，只顯示該批 revision；URL 僅保存 `review_batch`、`batch_size`、`review_snapshot` 等定位，不得包含表單、token 或權限。重新整理必須重新驗證受保護批次 API；不存在或過期時不得套用舊範圍，只依目前審查者篩選顯示待審清單。清除定位後恢復完整 pending queue。
- [ ] 批次「我的待辦」可依固定批次順序開啟第一筆、切到下一筆並返回同批次完整清單；單筆模式只額外保存 `workflow_revision`。合法範圍重新整理後必須回到相同 revision 並重新驗證批次；切換審查者篩選先清除單筆定位。批次 404／409 或快照過期時，批次與 `workflow_revision` 必須一起 fail closed，不能讓舊單筆定位繼續縮小目前安全清單。
- [ ] 在有效批次的單筆頁儲存任何候選內容補正後，Web 必須立即以原 batch ID、size 與 `review_snapshot` 重驗批次。內容指紋改變造成 409 時，當場標示過期、清除 `workflow_revision` 與批次成員並停用第一筆／下一筆／返回導覽；非 404／409 的重新驗證錯誤也須停用舊導覽。不得直接跳到舊批次下一筆，也不得因候選修正改變學生公開 workflow。
- [ ] 待審工具列可篩選「可開始真人核對」與「須先補資料」；判定須與核准閘門一致，涵蓋沒有來源、非 HTTPS、關鍵規定缺直接來源、流程學年度／梯次／適用狀態，以及來源證據與來源年度缺口。批次摘要同步顯示兩類數量；卡片頂部逐條列出缺口並可展開同卡補正區。綠色狀態仍必須明示須載入版本對照並逐來源／逐規定真人核對，不得代表核准、發布或自動補值。
- [ ] 批次工作台顯示「下載目前批次逐規定查核表」；匯出列數等於該批 10 個 workflow 的關鍵規定總數，每個 workflow 都包含一列適用範圍、每個步驟與每份文件，沒有遺漏或重複規定鍵。
- [ ] 每個逐規定列包含可讀規定內容、全部官方來源網址與來源名稱／角色／權威層級／適用年度／查核時間，以及缺來源證據、缺來源年度、缺查核日期、非 HTTPS、待確認與目前阻擋欄；A／B 核對、時間、說明、疑義及處置欄預設空白。
- [ ] 逐規定 CSV 僅限內容管理者、採 UTF-8 BOM、`no-store`、`nosniff` 與試算表公式防護；錯誤快照為 409、不存在批次為 404，且不能匯入、修改流程、形成核准或取代兩位真人各自開啟全部來源。
- [ ] 工作台連結帶有與 CSV 相同的審查內容 `review_snapshot`；若與目前審查內容指紋不同，後端以 409 拒絕舊快照待辦，前端顯示過期警告、維持完整清單且不套用舊 workflow／批次定位，清除後移除對應查詢參數。
- [ ] 「既有流程待納入雙審」顯示 280 筆，可依合作校文字與母校篩選；選到的 workflow 身分與學生版一致。
- [ ] backlog 顯示每筆關鍵規定數，總計為 7,067（長庚 1,780、臺北大學 5,287）；此數字由 280 個流程適用範圍、1,683 個步驟與 5,104 份文件組成。
- [ ] backlog 顯示「關鍵規定缺對應來源」與「含非 HTTPS 官方來源」篩選；目前關鍵規定缺直接來源為 0，非 HTTPS 為 9 筆流程／12 個網址（長庚 3／5、臺北大學 6／7）。
- [ ] 每條流程適用範圍、步驟與文件在勾選列內直接顯示對應官方來源；沒有來源或包含非 HTTPS 來源時，該列不可勾選且核准保持鎖定。
- [ ] 步驟、期限、表單或文件引用的網址若尚未建立來源證據資料，畫面顯示阻擋並要求真人填寫來源名稱、來源角色、權威層級與適用年度；不得由網址或流程年度自動推測。
- [ ] 「來源證據缺口群組」顯示 215 筆流程缺口集中於 6 個完全相同的網址；每組的流程數、關鍵規定引用數與母校正確，按「查看」只顯示該網址影響的流程，清除後回到目前其他篩選條件。
- [ ] 每組的「下載唯讀 CSV」只允許內容管理者使用；未登入為 401，非內容管理者為 403，回應採 UTF-8 BOM、`no-store` 與 `nosniff`。
- [ ] 每組 backlog 回傳專用 64 位 `source_evidence_snapshot_fingerprint`；下載 URL 必須帶相同的 `expected_snapshot`，成功 response 的 `X-Source-Evidence-Snapshot-Fingerprint`、檔名前 12 碼及 CSV 每列第一欄都必須一致。缺少／格式錯誤參數為 422，舊快照或產生期間內容變更為 409，不能交付 CSV。
- [ ] 最大群組匯出正好有 119 筆 workflow、合計 828 筆規定引用；每列包含年度、梯次、規定鍵／名稱、精確引用脈絡、目前證據資料、待審狀態、人工查核空欄及「不能取代逐流程修正、逐來源確認與雙人核准」提醒。
- [ ] CSV 的 `= + - @` 試算表公式前綴會被安全處理；下載不會修改公開 workflow、建立 revision、批次填值、匯入、核准或發布。
- [ ] 待審來源列出該網址實際支援的所有步驟、期限、表單與文件脈絡；尚無證據資料時，來源名稱保持空白並要求依官方頁面正式標題填寫，不可把「期限來源」或「文件」等介面標籤當成頁面名稱。
- [ ] 相同網址群組只協助安排查核，不會批次建立待審、批次填值、批次核准或發布；每份流程仍須各自確認適用範圍並完成雙審。
- [ ] 流程學年度缺漏、來源年度缺漏／與流程不一致或適用狀態仍待確認時，來源與規定核對框及核准按鈕保持鎖定。
- [ ] 依 `docs/review-batches/data-010-batch-001-insecure-official-sources.md` 逐頁確認安全替代候選；不能只把網址字串由 `http` 改為 `https`。
- [ ] 先開啟 `data-010-batch-001-source-candidates.json`，確認 12 列仍與工作台目前的 HTTP 來源完全相同；`strong_candidate` 也不代表已核准，仍須完成每列 `required_human_checks`。
- [ ] 執行 `python scripts/check_source_replacement_transports.py --check --timeout 30`；候選、輔助連結與六筆不可替代研究線索共 22 個去重網址須與 manifest 一致，目前為 20 個最終 HTTPS 2xx、2 個轉回 HTTP。命令只讀 response headers，不保存本文、不修改候選或公開資料；連線失敗不得視為通過。
- [ ] backlog 顯示 `workflows_with_source_replacement_candidates=10`、`source_replacement_candidate_count=13`、`transport_blocked_source_replacement_candidate_count=2`；10 張卡片的候選數合計為 13，其中強候選 8、條件候選 5，原網址在 pending revision 移除後對應計數會自動歸零。
- [ ] 「已有研究候選來源」篩選與上方「顯示 10 筆流程」按鈕只留下同一組 10 筆；每張卡顯示自己的候選數與強／條件分布。操作不建立 revision、不變更公開資料，也不把候選視為真人核准。
- [ ] 「下載唯讀審核 CSV」產生 UTF-8 BOM 的 13 列／10 流程清單，包含目前與候選網址、研究證據、人工必查、輔助網址、傳輸狀態／查核日／最終網址／HTTP 狀態／是否可填入及工作台定位；其中 11 列可填入、2 列不可填入，審查者 A／B、完成時間、結論與處置預設空白。
- [ ] CSV response 為管理員專用、`no-store`、`nosniff`，並同時回傳 64 字元審查內容指紋、10 筆流程與 13 個候選 header；以目前指紋下載成功，過期 `expected_snapshot` 回傳 409。
- [ ] 下載前後 published workflows 與 revisions 完全相同；CSV 不能匯入，也不會套用網址、建立待審版本、勾選來源、形成核准或改變學生資料。
- [ ] `/admin/application-workflow-source-replacement-candidates` 未登入為 401、一般學生為 403，管理者回應採 `no-store` 與 `nosniff`；只回傳仍含原網址的 pending revision 候選，讀取前後不得改變 revision 或公開資料。
- [ ] 工作台候選卡顯示強候選／條件候選、內容研究日期、傳輸狀態與查核結果、自動研究證據、人工必查、輔助官方連結及「安全研究線索（不可直接替代）」；研究線索必須顯示不等價原因且不得提供套用按鈕，「自動研究證據」不能視為真人核准。
- [ ] 最終維持 HTTPS 2xx 的候選按「只填入待審欄位」後只改變瀏覽器內尚未保存的替代網址欄，來源不會被自動勾選，後端 revision 與學生公開資料都不變；欄位已有不同手填值時拒絕覆寫。
- [ ] Lobachevsky 與人民大學 SIS 候選卡明示「會轉回 HTTP」，顯示最終 HTTP 網址，按鈕文字為「傳輸安全未通過，禁止填入」且保持 disabled；兩卡各顯示兩筆最終 HTTPS 200 的官方研究線索，但須逐筆標示 `eligible_as_replacement=false` 與不等價原因，不能用安全脈絡頁、反向交換頁或通用文件繞過內容及傳輸閘門。
- [ ] 山東大學流程須比較 2022–2023 舊 PDF 與 manifest 中 2026–2027 HTTPS PDF；從官方列表重新下載並核對頁數、雜湊、校區、學院、提名與文件後，才能在 pending revision 替換。
- [ ] 在 pending revision 儲存安全替代網址後，步驟、期限、步驟表單、文件來源、文件表單、送件入口與動作網址的相同引用都同步更新；學生公開版本維持不變。
- [ ] 多個舊入口只有在標題、角色、權威、優先級、內容雜湊與本次適用範圍一致時可明確合併；中繼資料衝突、替換到未勾選的既有來源或非 HTTPS 候選都被拒絕。
- [ ] 資料缺口篩選顯示缺適用學年度 77、缺有效申請梯次 0、缺可驗證精確期限 280、官方來源缺適用年度 280；1,619 筆既有來源紀錄缺年度，另有 215 筆規定引用缺少來源證據資料，合計 1,834 筆需補正。另可篩出 215 筆缺可追溯最後查核日期的流程引用；系統沒有自動猜測或批次補值。
- [ ] bundled、目前 runtime 與內容治理載入皆為 280 筆 workflow；NTPU 不會因 local 年度推導時機不同而重複成 406 筆，總數也不會出現 483。
- [ ] 「缺口最多優先」、「已建立待審優先」、「需確認步驟最多」與「合作校名稱」排序符合選項，篩選後摘要數字只計算目前結果。
- [ ] 按「建立待審版本」後，學生版同一流程 response 不變；待辦改顯示「已建立待審」，重複操作仍指向同一 revision。
- [ ] 補正適用範圍時，審查者逐頁開啟來源後只勾選本次已確認項目；流程學年度不會自動複製到所有來源，未勾選來源仍為空白。
- [ ] 儲存補正後，revision ID、版本與 workflow key 維持不變，畫面新增含審查者、時間、說明及前後內容雜湊的修正紀錄；任何既有核准都歸零並須重新雙審。
- [ ] 成功核准會以該審查者的實際核准時間更新候選流程、全部來源與全部步驟的最後查核日期；內容雜湊不因查核時間改變。缺查核日期的舊式／手工核准紀錄不得正式發布。
- [ ] 使用過期內容雜湊送出補正時會收到衝突，不會覆蓋另一位審查者較新的修改；未知來源 URL 也會被拒絕。
- [ ] 有 `base_version` 的待審版本在尚未載入對照時顯示「先載入版本對照」，核准按鈕不可操作。
- [ ] 載入後顯示精確基準版號、候選版號、流程欄位／步驟／來源變更數與未變步驟數。
- [ ] 每個差異都同時顯示基準值與候選值；新增、移除、調整不只靠顏色區分。
- [ ] 審查者只勾選部分來源、步驟或文件時核准按鈕保持停用；全部來源與關鍵規定完成後才解鎖。核准 request 必須綁定目前內容雜湊、完整來源及完整規定清單。
- [ ] 使用過期內容雜湊、漏掉來源／規定、混入未知來源／規定或只有舊格式核准說明時，後端拒絕核准或發布；不能只靠前端按鈕防呆。
- [ ] 快速從 backlog 切到待審佇列時，較舊的非同步 response 不得重繪畫面或清除尚未送出的來源勾選。
- [ ] 審查者 A 核准後顯示 1／2、來源數、關鍵規定數與內容雜湊摘要，正式發布按鈕仍停用。
- [ ] 審查者 B 可看見 A 的查核紀錄，但仍須自行重新勾選全部來源與關鍵規定；獨立核准後顯示 2／2 並解鎖發布。
- [ ] 發布後待審佇列移除該版本；切換「已發布」仍可查看兩筆核准紀錄，操作按鈕保持鎖定。
- [ ] 1440px 與 390px 工作台沒有水平溢位，官方來源可開啟，瀏覽器 console 沒有 error 或 warning。
- [ ] 依 `review-batches/data-003-batch-001-ntpu-shandong-115.md` 核對山東大學第一批來源；2022–2023 舊 PDF 不得被填為 115，校區或學院期限不得外推給所有臺北大學申請者。

| 學校／合作校 | 規定類型 | 適用校／院／系 | 學年度／梯次 | 官方來源 URL | 最後查核日期 | 審查者 A／日期 | 審查者 B／日期 | 結果 | 問題編號 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 待填 | 資格／期限／文件／送件／承辦／例外 | 待填 | 待填 | 待填 | 待填 | 待簽 | 待簽 | 待審 | 待填 |

最低查核範圍：

- 每一個可公開顯示為「可申請」的合作校。
- 校級資格與所有學院／學系例外。
- 校內截止、合作校截止、紙本寄出與必須送達期限。
- 文件名稱、份數、正影本、簽名／核章、表單版本。
- 送件方式、承辦單位、官方聯絡方式。
- 當期開放、名額、交換期間與僅合作備查狀態。

## 4. 問題分級與阻擋規則

| 等級 | 定義 | 是否阻擋 Web 核准 |
| --- | --- | --- |
| P0 | 可能讓學生錯過資格／期限、寄錯單位、漏交必要文件，或造成個資未經同意保存 | 是 |
| P1 | 關鍵規定沒有官方來源、年度、梯次或雙人查核；不同資料面顯示互相矛盾 | 是 |
| P2 | 主要任務可完成，但名稱、提示、RWD 或可及性造成明顯困惑 | 視處置決定 |
| P3 | 不影響正確性與完成任務的外觀或文字改善 | 否 |

Web 核准前必須同時成立：

- [ ] P0 = 0。
- [ ] P1 = 0。
- [ ] 所有關鍵規定都有來源、適用年度／梯次、最後查核日期與兩位審查者結果。
- [ ] 完整回歸與 Web E2E 都通過。
- [ ] 測試學生走完核心情境，所有阻擋問題均關閉。
- [ ] 產品負責人在 web-release-candidate.md 明確填寫核准結果。

## 5. Web 與 App 閘門

下列文字尚未被產品負責人填寫，因此目前不得啟動 Flutter 移植：

> Web 已核准移植 Flutter：＿＿＿＿＿＿＿＿
>
> 產品負責人：＿＿＿＿＿＿＿＿
>
> 日期：＿＿＿＿＿＿＿＿

即使 Web 通過，後續也只移植到 Flutter，由同一套 Flutter 程式產出 iOS 與 Android；不另外擴寫原生 SwiftUI 或 Kotlin 功能。

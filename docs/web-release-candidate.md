# Web Release Candidate

- Candidate：2026-08-31-pre-review.129
- 決定：NOT READY
- Web 核准：否
- Flutter 移植核准：否
- AI API：暫緩
- 本地 AI 串接：LAI-00～LAI-03 隔離 provider 基礎已完成；Advisor／RAG／文件／Web／production 串接仍暫緩並須另行核准

## 1. 目前判定

Web 功能已具備可重跑的核心流程與權限／隱私測試，可交給產品負責人、資料審查者與測試學生開始審核；但兩校資料尚有發布阻擋項，不能標記為正式審核版，也不能進入 Flutter 移植。

| 面向 | 狀態 | 證據／原因 |
| --- | --- | --- |
| 後端與 Web 回歸 | 通過 | CI 相同 frozen environment 已分開跑完 804 項非 E2E 與 49 項 Chromium E2E，合計 853 passed、0 failed；耗時分別為 412.66 與 456.41 秒。除既有帳號、治理、文件、社群與刪帳邊界外，B5-05 已驗證學生回報、C-01 審查批次競態防護，以及 DATA-003 來源證據 CSV 的 candidate／workflow／schema 複合快照、stale 409 與產生中變更 409 都已納入回歸。 |
| 規格與 API 契約基線 | 通過 | 第 6–19 節追蹤列都有任務、狀態、證據與下一門檻；`docs/api/openapi.json` 與 live schema 完全一致，contract 版本為 `2026-08-31.2`。來源證據 CSV 的 `expected_snapshot` 為必填 64 位 hex，backlog group 公開專用 `source_evidence_snapshot_fingerprint`；既有已驗證學生回報與不可直接發布邊界維持不變。 |
| Supabase runtime | 本機 21／21 fresh 通過；正式專案、既有資料升級與遠端 CI 待驗 | pinned PostgreSQL 17.6／兩個獨立 PostgREST 14.12／Storage API 1.60.4 已在全新 tmpfs DB 與隔離 Storage volume 從零套用 21／21 migrations。最終必要執行回傳 `status=passed`、`cleanup_status=passed`，驗證 32／32 RLS、0 browser grants、3 個 workflow issue service-role-only RPC、submit／review 競態與冪等、限流、6 個 unsafe URL、刪帳去識別、90 天 pending retention、24 小時 terminal replay grace、purge／cascade／control 保留，以及既有雙 PostgREST 社群、六種晚期 rollback 與 Storage cleanup。其後 project label 下 container／network／volume 均為 0；正式 Supabase 專案、既有資料升級路徑、正式 Storage backend 與首次遠端 CI 仍待驗。 |
| Supabase migration 語法 | 通過 | `pglast 8.4` 已解析全部 21 份 migration：471 個頂層 statements、11 個 SQL function bodies、51 個 PL/pgSQL units；最新 `20260830100000_application_workflow_issue_reports.sql` 為 29／0／4。`scripts/validate_supabase_migrations.py`、負向／完整性測試及 CI 閘門均保留。 |
| Python 相依套件安全基線 | 通過；不等於完整 F-01 | `uv lock --check` 可解析 88 個 package；`uv run --frozen python -m pip check` 回報 `No broken requirements found`，`uv run --frozen python scripts/audit_python_dependencies.py` 回報 `No known vulnerabilities found`。`cryptography 50.0.1`、`pip-audit 2.10.1` 與 Windows 中文路徑安全 launcher 維持鎖定。此結果只涵蓋已解析的 Python runtime dependencies，不代替程式碼、設定、正式基礎設施、濫用與隱私人工審查。 |
| 遠端 CI | 本機 frozen 與 current 21／21 runtime 基線通過；首次遠端執行待驗 | `.github/workflows/quality.yml` 固定 `uv 0.11.26`、`uv.lock` 及 checkout／setup-python／setup-node 的完整官方 commit SHA，再於 runner 暫存資料目錄執行 Python／JavaScript、OpenAPI、Supabase migration parser、dependency audit、不能忽略失敗的隔離 Supabase runtime harness 及完整 pytest；不使用 editable pip install 或可移動 action major tag。runtime step 外層 20 分鐘，內層所有子程序有 10／30／120／600 秒 timeout；每次 run 由程式生成唯一且經驗證的 Compose project 名稱，cleanup 非零或 label 殘留會使工作失敗。本機 frozen 基線為 853 passed，current 21／21 runtime 通過；尚未觸發 GitHub Actions。 |
| 本機 JSONL fallback | 通過 | 共用 writer 採同目錄暫存、flush／fsync 與原子 replace，讀取不會看到半寫入檔案；同程序交易鎖改用不依賴父目錄／檔案是否已存在的絕對正規化鎖鍵，避免 Windows `Path.resolve()` 在首次建檔競態中讓同一路徑短暫分裂。替換失敗復原、完整 integrity 測試、32 路帳號 upsert 連跑 10 次與三種各 24 路投稿均通過；正式部署仍以 Supabase repository 為目標 |
| 真人審查來源候選 | 封裝可查核；live transport fail closed | 山東大學與 12 個非 HTTPS 來源共 13 筆封裝定義（內容強 8、條件 5）；封裝證據仍為 22 個去重網址中 20 個最終 HTTPS、2 個轉回 HTTP，候選列仍為 11 筆可填入、2 筆禁止填入。2026-08-31 本次唯讀 live recheck 連續兩次都因立教大學候選頁與 supporting page 連線逾時而 exit 1，因此不能把封裝值當成本輪即時通過。Lobachevsky 與人民大學的安全官方脈絡頁都明示內容不等價、`eligible_as_replacement=false`，沒有套用按鈕。所有清單與查核都不建立 revision、核准或公開變更，候選仍須兩位真人確認等價性與規定涵蓋。 |
| 來源中繼資料研究候選 | 封裝可查核；live metadata fail closed | 215 筆缺來源證據流程集中使用 6 個 exact URL。封裝研究結果為 5 個可讀原始來源與 1 個應用層失效 NTPU 頁；工作台只顯示候選值與不可直接替代研究線索，全部固定 `can_prefill=false`。2026-08-31 本次 `scripts/check_source_metadata_research.py --check` 連續兩次都因長庚來源頁讀取逾時而 exit 1，其餘 5 個來源符合封裝狀態；在該頁可重新驗證前不能宣稱 5／1 live check 通過。CSV 沒有填入按鈕，也不建立 revision、核准、查核日或公開變更。 |
| 生活情報人工審查 | 兩校皆可依穩定批次、逐項表與個人待辦續接執行獨立雙審、明確升級及安全復原；正式資料仍阻擋 | 單卡即時計算來源、12 區塊及說明字數；下一步依序聚焦未核對項目或說明欄，完整前停用一般保存與保存續接。草稿恢復及清除均重算，不自動勾選、送出或形成證據；後端門檻不變。工具列核可／修正篩選、批次統計與導覽、三種阻擋、竄改拒絕及安全重設均保留。總閘門仍為 280 筆 profile、137 筆完整查核、143 筆待審、470 個來源；正式資料仍為 0 筆真人事件。 |
| 申請流程發布歷程與復原 | Web 技術完成，正式資料待驗收 | 管理者可查看每筆流程目前 revision、一般發布／復原動作、操作者、原因、時間、內容指紋及完整舊版；也可在 snapshot-bound 批次工作台建立 pending 副本、進入批次個人待辦與逐筆導覽。獨立核准全部來源、規定與非空白說明後，可選擇只核准或核准並續接；後者會先重新驗證批次，再依固定順序開啟下一筆，且不把目前帳號待辦完成誤稱為雙審／發布完成。每個補正來源列即時顯示本次未選取、第一個缺少欄位或完成；全域按鈕依流程年度、修正說明及來源順序把焦點移到下一個缺口，全部完成後隱藏。只有有效且有實質變更時才可儲存，只處理已勾選來源，沒有自動填值或批次代填；非 HTTPS 且尚無 top-level 證據的來源也有必要替代網址欄。補正草稿按管理者、revision 與內容雜湊隔離，重整恢復、手動或成功操作後清除。綠色狀態不代表核准。批次內儲存候選補正後立即以原 snapshot 重驗；指紋更新或無法確認時均清除單筆定位並停用舊批次導覽。這些入口不自動核准、不發布、不觸發通知、不改學生資料。只有內容不同且曾綁定完整雙審的 superseded revision 可復原。正式 `data` 目前沒有 workflow revision／rollback 紀錄，不能把 E2E 事件當正式發布。 |
| B5-05 申請規定錯誤回報 | Web、後端與本機 fresh runtime 完成；正式 Supabase 與真人走查待驗 | 只有已登入且完成學生身分驗證的帳號可回報目前流程或單一步驟，且必須提供官方 HTTPS 來源；後端重新載入並綁定目前 workflow ID、版本、內容快照與受信任步驟標題，拒絕過期或不存在的目標。提交與管理員處置都以 account-scoped mutation ID、語意 fingerprint、限流與 CAS 安全重送；Web 對 30 秒 timeout、網路／5xx 或不可驗證的 2xx 保留同一 mutation，重新整理後只為同帳號恢復。管理員 queue 採 `no-store`、請求序號與卡片級鎖定，404／409 會重載；關閉或切換帳號會清除 DOM／草稿。`20260830100000_application_workflow_issue_reports.sql` 的 RLS、service-role-only RPC、submit／review、刪帳去識別、90 天／24 小時 retention 與 purge 已由 21／21 fresh runtime 實跑；回報成立仍只關閉案件，不建立 revision、核准或發布正式規定。 |
| 真實瀏覽器 E2E | 通過 | `pre-review.129` 單獨重跑 49 項 Chromium E2E，49 passed、0 failed，耗時 456.41 秒。除既有 session、OAuth、離線、workspace、390px、文件、治理、社群與學生黃金路徑，也驗證來源證據下載 URL 帶目前 composite snapshot，實際下載檔名使用其前 12 碼，且 CSV 每列第一欄為完全相同的 64 位指紋。 |
| 即時發布就緒閘門 | 阻擋 | `/admin/web-release-readiness`、工作台與 `exchange-info --data-dir data audit-web-release` 共用唯讀 fail-closed 總規則；既有 `/admin/application-workflow-release-readiness` 保留為流程子報告。正式稽核仍為 280 workflows、0 published；生活情報為 137 verified、143 pending destination profiles、470 pending sources；共 9 類 blockers，CLI exit code 為 2。三個 fingerprint 未改變：總指紋 `6c88731481993e0bcf3da9627153db86731a13403605607478fba4f9cb9df49d`、申請流程子指紋 `e72b8c4a35ae34294ad497af9988d740e9f4236caaa9fe3396dbe32f4af4d57c`、生活情報子指紋 `d73804f1ec16ddc7e61e71fc8a199a021b285cd2a7a658e9ec9186077b070011`。兩面稽核鏈完整性缺口皆為 0；直接改狀態、缺少相符雙審證據或竄改任一事件鏈都會失敗並更新總指紋。 |
| 核心功能流程 | 可審 | 探索、同步、計畫、文件、PDF、送件、提醒、非 AI 文件完整性規則檢查、多計畫日期衝突與學生明填工期排程、官方表格免費下載／進階文件工具的伺服器權益、外部日曆降級停用／安全撤銷、社群、隱私已納入 E2E；App 對等行為仍待 Web 核准後移植 |
| 公開 baseline、合作狀態與跨校隔離 | 通過 | 長庚中央當期 75、院級參考 2、Web 可見與 workflow 相符 77/77、缺流程與 orphan 均為 0；兩筆院級參考禁止加入正式計畫；臺北大學預設與隔離 runtime 皆為官網及 destination 203/203；destination 依 home university 隔離 |
| 年度／梯次與期限防呆 | 通過 | 長庚校級 115-2 申請梯次已結構化為已截止，9/21 語言補件只標示給初審名單有 `＊` 者；臺北大學歷年月份維持原則參考。兩校只有參考時程的 1,683 個合作校步驟都不會產生日曆事件或提醒，舊的月／日自動套年份路徑已移除；原始合作校日期在清單、比較、詳情與搜尋一律標為參考時程及年度待確認 |
| 正式發布防呆 | 通過 | 新 revision 強制由兩個不同內容管理帳號各自核准；每位審查者必須在載入版本對照後，親自勾選候選版去重後的全部官方來源，並逐項核對流程適用範圍、每個步驟與每份文件。每條規定同列顯示直接官方來源；來源集合涵蓋流程來源、步驟來源、期限來源、步驟表單、文件來源及文件表單。缺直接來源、來源引用沒有名稱／角色／權威層級等證據資料、適用年度缺漏或不一致，或含非 HTTPS 來源時，前後端都鎖住核准／發布。核准紀錄會保存候選內容雜湊、完整來源 URL 與關鍵規定鍵清單，並以實際核准時間更新流程、來源與步驟的最後查核日期；過期畫面、缺漏／未知來源或規定、舊格式核准、同帳號重複、核准不足及未參與核准者發布都會被拒絕。工作台預設統計 280 筆「既有流程待納入雙審」，共 7,067 個關鍵規定（長庚 1,780、臺北大學 5,287），目前 0 條缺直接來源；但 9 筆流程仍有 12 個非 HTTPS 官方網址，因此維持發布阻擋。首批只渲染 25 筆，可搜尋、依母校、資料缺口與審查順序篩選／排序，並冪等建立待審副本，建立前後學生內容不變。工作台另精確盤點缺適用學年度 77、缺有效梯次 0、缺可驗證精確期限 280、來源年度有缺口 280；1,619 筆既有來源紀錄缺年度，另有 215 筆規定引用尚未建立來源證據資料，合計 1,834 筆來源證據需補正，且 215 筆流程引用缺少可追溯查核日期。這 215 筆缺證據引用只集中在 6 個相同網址，工作台會列出每組受影響流程與關鍵規定數，並可一鍵限縮待辦；每組另可下載管理者限定、`no-store` 且有試算表公式防護的唯讀 CSV，逐流程保留年度、梯次、規定與精確引用脈絡及人工查核空欄。CSV 不能匯入、建立 revision、批次填值、核准或發布，相同網址仍須逐流程確認。待審適用範圍只能由內容管理者逐頁勾選已確認來源後補正；流程年度不會自動套到來源，未勾選來源維持空白。規定引用尚無來源證據資料時，真人必須依正式頁面標題補上來源名稱、角色與權威層級；結構標籤不再預填成來源名稱。人工核實 HTTPS 替代頁後，可在 pending revision 同步替換所有規定引用；多個中繼資料一致的舊入口可明確合併，任何中繼資料衝突都會拒絕。每次內容修正使用內容雜湊避免覆蓋他人更新、保存前後雜湊與說明、維持相同 workflow 身分並清除既有核准。快速切換佇列時只允許最後一次請求更新畫面，避免較舊 response 重繪並清掉尚未送出的勾選。期限提醒另要求 workflow 為 published 且具有 published_at，Codex 不代替人工 reviewer 簽核 |
| Bundle／runtime 一致性 | 通過 | 已清除 203 份 NTPU legacy workflow 中 1,038 個由流程年度自動衍生的來源年度；正式雙審發布資料不受清理工具影響。workflow 在合併前先完成結構化，bundled、目前 runtime 與內容治理載入現在都為 280 筆，不再有單一路徑出現 483 筆重複資料 |
| 兩校內容完整度 | 阻擋 | 長庚中央當期 75/75 與 Web 可見 77/77 已有參考流程，但 465 個步驟與 1,238 份文件要求仍全部需確認；臺北大學也有大量待確認內容 |
| 關鍵規定時效 | 阻擋 | 長庚 77 筆合作校流程仍缺適用學年度；115-2 校級精確日期已截止且不能證明所有合作校規則；9/21 是條件式補件而非新梯次；兩校 published 0、published_at 0；目前沒有可提供所有申請學生使用的下一梯次精確 deadline |
| 人工資料雙審 | 未完成 | 後端已強制兩位審查者各自保存目前版本、完整來源及關鍵規定查核證明，但尚無兩位真人逐條簽核現有 280 筆流程／7,067 個關鍵規定；自動化 E2E 不算真人核准 |
| 產品與測試學生驗收 | 模板已建立，真人尚未開始 | `docs/web-review-findings.md` 已提供匿名工作階段、11 個 Web-only 情境（含 B5-05 學生回報與管理員獨立結案）、P0～P3、重現／證據／處置／回歸／真人重驗欄位及隱私禁填規則；目前固定 0 真人紀錄、0 開放 finding、Web／Flutter 未核准，不能把空模板或自動化測試當驗收。 |
| App 對等移植 | 關閉 | 只有產品負責人明確核准 Web 後才能開始 Flutter |

完整數字與阻擋證據見 web-data-audit.md；人工流程見 web-review-checklist.md。

- `pre-review.129` 將 DATA-003 單一來源證據 CSV 綁定專用 composite snapshot。每個來源 URL 身分（僅 scheme／host 不分大小寫，path／query 精確區分）的指紋涵蓋 schema 版本、有效 workflow content hash／版本、目前查核時間、pending revision 身分與完整 research candidate；backlog、下載 URL、專用 header、檔名前 12 碼及 CSV 每列第一欄使用同一指紋。缺少／格式錯誤 snapshot 回 422，過期頁面或 manifest／workflow 更新回 409，rows 產生期間變更也 fail closed；不存在的 group 維持 404。單元、API、OpenAPI 與真實 Chromium 下載皆通過，且沒有建立 revision、approval、publication 或修改公開學生資料。完整 frozen 回歸為 804 項非 E2E＋49 項 E2E，合計 853 passed、0 failed；兩套 live source recheck 因立教 2 個 URL 與長庚 1 個 URL timeout 而按設計 exit 1，封裝候選未被自動改寫。正式 release audit 仍為 9 類 blocker，三個 release fingerprint 不變。這不等同正式 Supabase transaction、真人雙審或 Web 發布核准。
- `pre-review.128` 修正 C-01 申請流程審查包的 snapshot TOCTOU：批次產生器不再於 backlog 後過早接受第二次內容指紋，而是在 release readiness 與全部 rows 完成組裝後重算；產生期間若 pending candidate 或待審成員發生實質變更，函式會拒絕回傳，CSV API 回 409 且不交付檔案。兩個隔離競態測試同時確認公開學生 workflows byte-for-byte 不變、沒有 approval 或 publication。完整 frozen 回歸為 801 項非 E2E＋49 項 Chromium E2E，合計 850 passed、0 failed；當時記錄的舊 workspace data-tree Windows aggregate、9 類 blocker 與三個 release fingerprint 前後相同。這只關閉本機審查包混版時間窗，不等同正式 Supabase transaction、真人雙審或 Web 發布核准。
- `pre-review.127` 補齊 B5-05 的 current schema fresh runtime 證據。隔離 harness 在 pinned PostgreSQL 17.6、兩個 PostgREST 14.12 與 Storage API 1.60.4 上從零套用 21／21 migrations，驗證 32／32 RLS、0 browser grants、3 個 workflow issue service-role-only RPC；10 筆提交限流、雙 API submit／review 競態、冪等 replay／conflict、缺帳號／缺報告、6 個不安全來源 URL、review CAS、刪帳 rollback、pending 去識別 90 天、去識別後結案 24 小時、reviewer 去識別、purge／cascade／control 保留全部實跑通過。最終必要執行回傳 `status=passed`、`cleanup_status=passed`，另一次保留環境與獨立重跑也通過；事後 project label 下 container／network／volume 均為 0。OpenAPI `2026-08-31.1`、21 份 migration parser 471／11／51、dependency audit 0 個已知漏洞、799 項非 E2E 與 49 項 Chromium E2E 全部通過，合計 848 passed。正式 release audit 仍是 9 類 blocker、CLI exit 2 且三個 fingerprint 未變，因此維持 `NOT READY`；正式 Supabase、既有資料升級、正式 Storage backend、遠端 CI、C-01／C-02 與 Web／Flutter 核准仍待完成。
- `pre-review.126` 完成 B5-05 的申請規定錯誤回報閉環。只有已驗證學生可針對目前 workflow／step 提供官方 HTTPS 來源；FastAPI 重新建立受信任快照，學生與管理員 mutation 都可冪等重送，Web 對 30 秒 timeout、網路／5xx 與無法精確驗證的 2xx 會跨重新整理保留同一 account-scoped mutation，管理員 queue 另有 request race、404／409 重載及 DOM 隱私清除。`20260830100000_application_workflow_issue_reports.sql` 新增 RLS、service-role-only RPC、限流、CAS、刪帳去識別及 retention；管理員處置只關閉案件，不建立 revision、核准或發布內容。OpenAPI `2026-08-31.1` 無漂移；21 份 migration 的 parser 為 471／11／51，最新檔為 29／0／4；88 個 lock packages、`pip check` 無破損相依、dependency audit 0 個已知漏洞。789 項非 E2E＋49 項 Chromium E2E 合計 838 passed、0 failed、0 warnings，耗時 606.44 秒。歷史 runtime 仍只證明前 20／20 migrations 與 30／30 tables，不含第 21 份；fresh 執行因 Docker Linux engine pipe 缺失而在約 1.35 秒 exit 1。正式稽核仍為 9 類 blocker、CLI exit 2，三個 fingerprint 未變，維持 `NOT READY`，Web／Flutter 皆未核准。
- `pre-review.125` 將 runtime harness 的生命週期本身改為 fail closed。唯一 `_run` 入口強制 docker info 30 秒、Compose cold start 600 秒、控制／cleanup／psql 120 秒、readiness probe 10 秒、logs 30 秒；timeout 錯誤不輸出 SQL、environment、token 或 partial output。任意 `--project-name` 已移除，每次只使用 `exchange-supabase-runtime-` 保留前綴及 GitHub run identity／本機 PID／隨機值生成的唯一名稱。preflight／final cleanup 同時驗證 down return code 與 project label 下的 container、network、volume 為 0；成功 validation 後若 cleanup 失敗，整體仍 exit 1 且沒有 passed JSON，原始 validation error 也不會被 log／cleanup 次要錯誤遮蔽。新增 11 項生命週期測試；761 項非 E2E＋47 項 Chromium E2E 合計 808 passed、0 failed、0 warnings，耗時 661.01 秒，12 份 official data 雜湊前後一致。daemon 不可用的真實 failure path 在 1.5 秒內安全 exit 1；fresh 成功 runtime、遠端 Actions 與正式 Supabase 仍待驗，9 類 blocker、三個指紋、Web／Flutter 核准及產品 AI 狀態不變。
- `pre-review.124` 把 `uv run --frozen python scripts/validate_supabase_runtime.py` 納入 Web quality workflow。job timeout 由 35 調為 45 分鐘，runtime step 自身限制 20 分鐘且失敗不能忽略；契約測試鎖定命令唯一性、migration → dependency audit → runtime → pytest 順序、兩層 timeout 與沒有 `continue-on-error`。本機除 fresh runtime 外的 frozen 品質鏈為 797 passed、0 failed、0 warnings，耗時 581.54 秒；Compose config、migration parser、dependency audit、OpenAPI、兩套來源即時稽核、official data 前後雜湊與 release audit 都符合預期。本輪 fresh runtime 受 Docker Desktop 4.70 的 stale `dockerInference` socket reparse point 啟動錯誤阻擋；可恢復改名也被 Windows 拒絕，因此未做 factory reset 或破壞性清理，不新增 runtime pass。遠端 Actions、正式 Supabase、既有資料升級、實際 Storage backend、9 類 blocker、三個指紋、Web／Flutter 核准及產品 AI 狀態不變。

## 2. 本候選版包含

- 未登入搜尋、瀏覽、當次分頁比較及預算試算；收藏、建立申請計畫與保存預算先要求登入。
- 中央當期、合作備查與院級參考三種狀態；院級參考可查閱但不可建立正式申請計畫。
- 漸進式登入、Email／學生身分權限邊界；規則式個人顧問在送出前要求登入，未登入輸入不送出、不持久化。
- OAuth 登入與校方驗證的 state／session／browser 綁定、一次性終止、限流與 Email auto-link 維持 fail closed；`20260821190000_transient_auth_state.sql` 讓暫態 state 跨 worker 共用，`20260823100000_atomic_auth_account_mutations.sql` 以 service-role-only RPC 原子完成 Google／Facebook 帳號解析或建立、provider link、session 及 exact-session 學生身分提交。一般 profile 只送白名單欄位，calendar sync 以目前 token 做 expected CAS；migration 撤銷 direct account UPDATE，production repository 拒絕相容 upsert。這些是 `pre-review.103` 的歷史完成範圍。
- `pre-review.105` 新增 `CommunityRepository` 與 `20260823160000_atomic_public_community.sql`。公開社群 identity、token rotation、六類內容、帳號級限流、貼文／留言刪除、一般 moderation CAS／audit 及作者去識別改走單次 RPC；每次寫入採固定 account → identity → parent 鎖序與語意型 idempotency。Web 在網路錯誤／5xx 後重用同一 mutation ID，成功或明確 4xx 才清除。production 強制 Supabase 公開社群 backend。這不包含檢舉、封鎖、私訊或整體帳號刪除 transaction；正式 PostgreSQL／PostgREST 也尚未套用，因此 single worker、`NOT READY` 不變。
- `pre-review.106` 新增 `20260824100000_atomic_private_community.sql` 與私人社群設計文件。私訊邀請／接受／訊息、封鎖、檢舉／審核及刪帳前私人清理改走 service-role-only RPC；固定 account → sorted identity → conversation → child 鎖序，private-message report 也先鎖 conversation 再鎖 message。語意 fingerprint 排除重新產生的 ID／名稱／狀態／時間，相同操作可在後續封鎖或 target 移除後回放第一筆結果。Web 私人社群操作同樣重用 mutation ID。整體帳號刪除仍不是單一 transaction／durable saga，正式 PostgreSQL／PostgREST 也尚未套用，因此 single worker、`NOT READY` 不變。
- `pre-review.107` 新增 `20260829100000_atomic_account_deletion.sql`。Supabase exact session、公開去識別、私人資料與 actor receipt 清理、Email challenge、account 與 FK 關聯資料改為單一 DB transaction；direct account DELETE 撤銷。Storage 採 durable receipt、`X-Account-Deletion-Mutation-ID` 重送、proof-bound ack 與管理員 cleanup 續作。67 項聚焦、714 項非 E2E 與 47 項 Chromium E2E 全數通過；OpenAPI 為 `2026-08-29.1`。正式 migration／PostgREST、並行 rollback、RLS／grant 與 Storage timeout 仍待驗收，因此 single worker、`NOT READY` 不變。
- `pre-review.108` 將 PostgreSQL parser 變成可重跑的品質閘門。固定 `pglast 8.4` 為 dev dependency，新增 `scripts/validate_supabase_migrations.py` 與 nested PL/pgSQL 負向測試；20 份 migration 的 442 個 statements、11 個 SQL function bodies 與 47 個 PL/pgSQL units 全部通過，最新刪帳檔為 27／1／6。CI 會在完整 pytest 前執行同一 parser。716 項非 E2E 與 47 項 Chromium E2E 全數通過，合計 763。Docker Desktop 引擎仍無法啟動，故真實 migration／PostgREST 驗收仍未完成，single worker 與 `NOT READY` 不變。
- `pre-review.109` 將 DATA-010 的「網址字串是 HTTPS」提升為最終傳輸查核。新增唯讀 `scripts/check_source_replacement_transports.py`、manifest 傳輸欄位與 API／CSV／backlog／工作台閘門；11 個去重候選現場重查為 9 個 HTTPS 2xx、2 個轉回 HTTP。Lobachevsky 與人民大學 SIS 保留研究證據但禁止填入；docs／runtime 的母校、證據、人工檢查與傳輸狀態由測試鎖定一致，也修正先前臺北大學候選誤寫長庚的文字。OpenAPI `2026-08-29.2` 無漂移，721 項非 E2E 與 47 項 Chromium E2E 全數通過，合計 768；正式資料仍未經真人雙審，`NOT READY` 不變。
- `pre-review.110` 將安全傳輸與內容等價性分開建模。Lobachevsky 的 UNN 外校學生官方入口及人民大學現行國際學生申請系統均為最終 HTTPS 200，但不足以取代原交換規定，故只以 `research_leads` 提供，強制 `eligible_as_replacement=false`。工作台另區顯示且不提供套用按鈕；CSV、API、OpenAPI `2026-08-29.3` 與傳輸稽核同步。稽核現涵蓋 18 個去重網址（16 HTTPS、2 HTTP 降級），722 項非 E2E＋47 項 Chromium E2E 合計 769 passed；正式資料及 9 類阻擋未變，`NOT READY` 不變。
- `pre-review.111` 新增 pinned PostgreSQL／PostgREST 的隔離 runtime gate。`scripts/validate_supabase_runtime.py` 以 tmpfs、隨機 loopback port 與專用 Compose project 從零套用 20／20 migration，驗證 30／30 RLS、0 browser grants、五張敏感表 direct DELETE denial、transient auth／workspace 真實並行，以及帳號刪除 receipt insert 晚期失敗 rollback、成功 cascade／公開匿名化、replay、proof-bound ack 與管理員 durable cleanup。harness 結束會移除自己的容器、network 與 tmpfs data，且明列只證明 durable handoff、不冒充真實 Storage bucket delete。726 項非 E2E＋47 項 Chromium E2E 合計 773 passed；正式 Storage API、公開／私人社群多 API instance、遠端 CI、真人資料雙審與 9 類 blocker 未完成，維持 single worker／`NOT READY`。
- `pre-review.112` 將隔離 gate 擴充至 pinned Supabase Storage API 1.60.4。harness 建立 private bucket 並實際上傳巢狀密文；`list_object_keys()` 改用 `list-v2` cursor 遞迴列舉，修正一般 list 只看見第一層資料夾而可能漏刪深層 orphan 的問題。帳號刪除驗證注入 Storage timeout，確認 pending receipt 與密文保留，再走真實批次 DELETE、重送、proof-bound／管理員 completion；orphan cleanup 只移除未引用物件並保存 audit。727 項非 E2E＋47 項 Chromium E2E 合計 774 passed；正式 Supabase 專案／實際 Storage backend、多 API instance 社群競態、遠端 CI、真人資料雙審與 9 類 blocker 未完成，維持 single worker／`NOT READY`。
- `pre-review.113` 將 runtime gate 擴充為兩個 pinned PostgREST 共用同一 PostgreSQL。公開社群同時驗證同 mutation 發文只產生 1 resource／1 receipt，另以不同 API 競爭父貼文刪除與留言新增，最終不留 orphan。私人社群驗證相反方向邀請的 sorted-identity lock、封鎖／傳訊的 fail-closed 列／receipt 一致性，以及兩個不同管理員搶同一 pending report 時只有 1 commit／1 audit，另一筆回 status conflict。harness 契約測試由 4 增為 6；完整回歸為 729 項非 E2E＋47 項 Chromium E2E，合計 776 passed。正式 Supabase 專案／既有資料升級／實際 Storage backend、遠端 CI、真人資料雙審與 9 類 blocker 仍未完成，維持 single worker／`NOT READY`。
- `pre-review.114` 為公開／私人社群 transaction 補齊可重跑的晚期失敗證據。在 mutation receipt 最後寫入點依序對公開發文、公開 moderation、私人邀請＋初始訊息、私人訊息、公開貼文檢舉與檢舉審核注入 `P0001`；六次錯誤都向 API 傳遞，且對應 resource、rate event、conversation、message、report、status、revision、audit 與 receipt 均完整 rollback，`partial_rows=0`。真實 runtime、729 項非 E2E、47 項 Chromium E2E、OpenAPI drift 與執行後容器／network／volume 清理全部通過；正式 Supabase 專案、既有資料升級、實際 Storage backend、遠端 CI、真人資料雙審與 9 類 blocker 仍未完成，維持 single worker／`NOT READY`。
- `pre-review.115` 為 DATA-010 的 Lobachevsky 與人民大學 SIS 傳輸阻擋候選各補一筆安全官方研究線索：UNN Academic exchanges 頁是 outbound 流程，人民大學擔保書只是通用文件，都不能支援原 incoming exchange 規定，故維持 `eligible_as_replacement=false` 且沒有套用按鈕。唯讀傳輸稽核擴充到 20 個去重網址（18 HTTPS、2 HTTP 降級）；729 項非 E2E、47 項 Chromium E2E 與 OpenAPI drift 通過。正式資料、三個指紋與 9 類 blocker 未變，CLI exit 2，維持 `NOT READY`。
- `pre-review.116` 為 DATA-003 的 215 筆來源證據缺口建立 6 個 exact URL 的唯讀中繼資料研究候選。5 個可讀原始來源提供候選標題、角色、權威及可證明時才提出的年度；1 個舊 NTPU 頁雖為 HTTPS 200，但應用內容顯示找不到，因此不提供候選值，只保留一筆 `eligible_as_replacement=false` 的現行姊妹校研究線索。API、CSV 與工作台固定 `can_prefill=false` 且零修改按鈕，不建立 revision、核准、查核日或公開變更。733 項非 E2E、47 項 Chromium E2E 與 OpenAPI `2026-08-30.1` drift 檢查通過；正式來源缺口、三個指紋與 9 類 blocker 未變，CLI exit 2，維持 `NOT READY`。
- `pre-review.117` 重新查核 DATA-010 的兩個傳輸阻擋候選。UNN 首頁及 semester exchange 精確路徑仍降級為 HTTP；新增的安全聯絡頁沒有 incoming 提名、期限與文件。人民大學 SIS 的三種路徑形態都降級為 HTTP；新增的安全商學院 incoming 頁屬不同學院且期限不同，不能替代 SIS。兩筆都只新增 `eligible_as_replacement=false` 的研究線索，工作台沒有套用按鈕；稽核擴充為 22 個去重網址（20 HTTPS、2 HTTP 降級）。733 項非 E2E、47 項 Chromium E2E 與 OpenAPI `2026-08-30.1` drift 檢查通過；正式資料、三個指紋與 9 類 blocker 未變，CLI exit 2，維持 `NOT READY`。
- `pre-review.118` 為 DATA-003 的 6 個 exact URL 新增有界唯讀漂移稽核，驗證最終 HTTPS、HTTP 狀態、真 PDF、HTML 找不到標記及標題漂移；最多檢查 1 MiB，足以辨識舊 NTPU 頁約 736 KiB 後的應用層失效訊息。即時結果維持 5 個可讀、1 個失效；任一網路或內容漂移皆 fail closed。739 項非 E2E、47 項 Chromium E2E、OpenAPI 與兩套來源稽核通過，合計 786 passed；正式資料、三個指紋與 9 類 blocker 未變，CLI exit 2，維持 `NOT READY`。
- `pre-review.119` 建立 C-02 匿名 `web-review-findings.md` 模板。它涵蓋 10 個 Web-only 真人情境、P0～P3、重現、審核包指紋、官方證據、負責任務、處置、自動回歸與真人重驗，並禁止姓名、Email、學號、學生證、真實文件及未遮蔽截圖進入 repository。P0／P1 不能風險接受，模板不含可填的核准聲明；目前 0 真人紀錄、0 開放 finding、Web／Flutter 未核准。744 項非 E2E＋47 項 Chromium E2E 合計 791 passed；正式資料、三個指紋與 9 類 blocker 未變，維持 `NOT READY`。
- `pre-review.120` 升級 `cryptography 46.0.7` 至 50.0.1，固定 `pip-audit 2.10.1`，並新增 Windows 中文路徑安全的 dependency audit launcher 與 CI 閘門。重查為 0 個已知漏洞，lock／environment 相容性通過；747 項非 E2E＋47 項 Chromium E2E 合計 794 passed。正式資料仍為原三個指紋、9 類 blocker、CLI exit 2；遠端 CI、F-01、真人資料／產品驗收、Web／Flutter 核准均未完成。
- `pre-review.121` 將 CI 從會重新解析版本的 editable pip install 改為固定 `uv 0.11.26`、`uv lock --check`、`uv sync --frozen --extra dev` 與全程 `uv run --frozen`；契約測試防止退回非鎖定安裝。本機以同一品質鏈跑完 795 passed、0 failed，dependency audit 仍為 0 個已知漏洞。正式資料、三個指紋、9 類 blocker 與 CLI exit 2 未變；遠端 Actions 仍待首次執行。
- `pre-review.122` 將 checkout v4.4.0、setup-python v5.6.0、setup-node v4.4.0 固定到官方目前標籤對應的完整 commit SHA；契約測試要求外部 action 清單、順序與 40 字元 SHA 完全相符。本機 frozen 品質鏈為 796 passed、0 failed。正式資料、三個指紋、9 類 blocker 與 CLI exit 2 未變；遠端 Actions 仍待首次執行。
- `pre-review.123` 依 Starlette 1.6.0 官方 TestClient 相依加入 `httpx2>=2.0.0,<3.0.0`，lock 固定 2.12.0；保留 `ddgs` 仍需要的舊 `httpx`。乾淨子程序以 warnings-as-errors 確認實際載入 `httpx2`，完整 frozen 品質鏈為 797 passed、0 failed、0 warnings。正式資料、三個指紋、9 類 blocker 與 CLI exit 2 未變；遠端 Actions 仍待首次執行。
- 資格與志願、個人申請計畫、預算估算及跨 session／裝置工作區同步。
- 校內申請梯次、初審後續與歷年原則時程的分層顯示；已截止、限特定申請者與參考月份不會冒充下一梯次。
- 文件清單、官方表格免費直連，以及需登入且受訂閱權益保護的一般欄位自動填表、逐欄核對、PDF 與列印／送件指示。
- 需登入且受訂閱權益保護的非 AI 文件完整性規則檢查；AI 深度檢查控制項與 API 均明確暫緩。
- AI runtime 由伺服器 fail closed：即使環境誤設 `OPENAI_API_KEY`，也不會建立 provider、產生 embedding 或送出外部 AI request；規則式顧問仍可使用。
- 生活情報工作台可切換長庚與臺北大學；長庚為 58 筆待審／6 批／942 個逐項，臺北大學為 85 筆／9 批／1,244 個逐項。批次內每個 profile 固定列出 12 區塊與全部來源，並可從 Web 直接下載 snapshot-bound 查核表；A／B 欄空白且不能匯入。管理者可只看自己的待辦／已留結論；未送出表單按管理者 ID 與 profile 指紋留在目前分頁工作階段，重整可恢復、手動清除或成功送出後刪除，但不會同步或形成證據。進度更新不換批，實質內容／成員改變使舊連結失效。兩個不同管理帳號仍須回工作台留下 append-only 審查事件，明確升級後才能改變學生資料。
- 紙本、線上、Email、親送與混合送件進度。
- Web 通知與 Email opt-in 邊界。
- 學生明填準備天數的非 AI 任務安排、建議開始日、完成狀態與外部日曆／提醒連動。
- 公共板、語言學校板及兩校大學板權限。
- 逐檔個人文件同意、私人資料清除與公開內容刪帳去識別。
- 規格第 6–19 節的 34 條追蹤矩陣、Web-only quality workflow，以及版本化、可重現的 OpenAPI contract snapshot。
- 只供內容管理者使用的 Web 雙人審查工作台，包含同時涵蓋申請流程與生活情報的即時 `READY`／`NOT READY`、總指紋及兩個子指紋；生活情報可切換兩校並隔離 queue、完整／批次／逐項 CSV、批次深連結、篩選與公開歷程；申請流程另有 280 筆 legacy 待辦搜尋、母校／資料缺口／研究候選篩選、分工 CSV、安全建立待審副本、revision URL 定位、目前管理者視角、逐來源證據補正、最後查核日期閘門、修正稽核紀錄及基準／候選逐欄對照。生活情報審查、申請流程核准及流程資料補正三種表單都能在同一分頁工作階段續接未送出內容，但草稿與 URL 都不形成後端證據或權限。學生版不顯示入口。
- 第一批可供真人逐頁查核的 `DATA-003-BATCH-001` 證據包；明確分開 NTPU 115 學年度校內來源、山東大學 2026–2027 校區／學院來源、通用頁面與過期 2022–2023 PDF，並新增 2026–2027 官方 HTTPS PDF 的 URL、8 頁與 SHA-256 證據。新 PDF 仍只是強候選，尚未核准或發布。
- `DATA-010-BATCH-001` 已列出 9 筆流程的 12 個非 HTTPS 網址，內容研究為 7 個強候選與 5 個條件式候選；傳輸安全另以 `transport_status` 獨立記錄。`scripts/check_source_replacement_transports.py --check` 只讀取 redirect、最終網址、HTTP 狀態與 content type，不保存本文或修改資料。連同 DATA-003 共 13 筆封裝列，11 筆可填入、2 筆會轉回 HTTP 而禁止填入；候選、輔助連結與六筆不可替代研究線索共 22 個去重網址會一起查核。CSV 與 pending-only API 都只限內容管理者且不寫入資料；工作台不會自動勾選、保存、核准或發布。候選尚未由真人認定等價，也未寫入正式 revision。

## 3. 本候選版不包含

- AI API。
- 本地 AI 模型或推論服務串接。
- 平台直接向學校正式送件。
- 學校回傳審查或錄取結果。
- 正式付款或訂閱扣款。
- Flutter 新功能移植。
- SwiftUI 或 Kotlin 原生功能擴寫。
- 長庚與國立臺北大學以外的完整申請陪跑。
- 語言學校與海外學位的完整申請陪跑。

## 4. 重現與審核入口

在專案根目錄執行：

    python -m playwright install chromium
    pytest -q
    pytest -q tests/e2e

人工審核順序：

1. 閱讀 web-data-audit.md。
2. 閱讀 `review-batches/data-003-batch-001-ntpu-shandong-115.md`，確認第一批官方來源的適用範圍與阻擋項。
3. 關閉所有 P0、P1 資料問題。
4. 兩位內容管理者先各自在學生版登入，再開啟 `/admin/content-review`。生活情報先在「獨立雙人審查」逐筆開啟：每人都要親自核對全部來源、12 個內容區塊並留下說明；確認第一位後只顯示 1／2，第二位若要求修正就不可進下一步。兩人都核可後仍只會得到 `ready_for_promotion`；其中一位有效核可者須另填升級說明、勾選學生可見變更確認並明確執行，之後再回學生頁確認只改生活情報查核狀態，沒有改申請規則、文件、期限或通知。
5. 申請流程再以資料缺口篩選「缺適用學年度」、「缺可驗證精確期限」或「官方來源缺適用年度」，搜尋合作校後按「建立待審版本」。此操作只能建立副本，不得改變學生內容。若要補正年度或梯次，必須逐頁開啟官方來源，只勾選這次已確認的來源並留下修正說明；儲存後確認既有核准已清除、未勾選來源仍空白。兩位審查者之後都須各自載入版本對照，再次親自開啟並勾選候選版全部官方來源，並逐項核對流程適用範圍、所有步驟及文件；來源與規定兩份完整清單都完成後，核准鍵才會解鎖。
6. 由兩位審查者填寫 web-review-checklist.md 的關鍵規定雙審表；達到兩人門檻後，才由其中一位在工作台正式發布。
7. 由產品負責人與測試學生走完桌面及 390px 情境。
8. 重新執行完整回歸與 Web E2E。
9. 在下方核准表填寫實際結果。

## 5. 核准表

此表必須由實際審核者填寫，不能由自動化測試或 Codex 代簽。

| 角色 | 姓名 | 日期 | 結果 | 未關閉問題 |
| --- | --- | --- | --- | --- |
| 資料審查者 A | 待填 | 待填 | 待審 | DATA-003 至 DATA-008、DATA-010 |
| 資料審查者 B | 待填 | 待填 | 待審 | DATA-003 至 DATA-008、DATA-010 |
| 測試學生 | 待填 | 待填 | 未開始 | 待填 |
| 產品負責人 | 待填 | 待填 | 未核准 | 待填 |

正式 Web 核准聲明：

> 我確認所有 P0、P1 已關閉，兩校關鍵申請規定已完成雙人查核，並核准此 Web 版本。
>
> 產品負責人：＿＿＿＿＿＿＿＿
>
> 日期：＿＿＿＿＿＿＿＿

Flutter 移植是另一個獨立閘門，只有在上述 Web 核准後才可填寫：

> Web 已核准移植 Flutter：＿＿＿＿＿＿＿＿
>
> 產品負責人：＿＿＿＿＿＿＿＿
>
> 日期：＿＿＿＿＿＿＿＿

## 6. 下一個允許執行的工作

只處理 web-data-audit.md 尚未關閉的 DATA-003 至 DATA-008、DATA-010，補齊雙審證據與 Web 人工驗收。AI 串接與所有 App 修改仍不在允許範圍。

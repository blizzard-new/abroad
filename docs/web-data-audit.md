# Web 資料正確性稽核

- 初始稽核：2026-07-29
- 最近更新：2026-08-31（`pre-review.129` 將 DATA-003 單一來源證據 CSV 綁定 per-source composite snapshot；schema、有效 workflow／pending revision 或完整 research candidate 改變時舊下載回 409，產生期間變更也不交付 CSV。804 項非 E2E＋49 項 Chromium E2E 合計 853 passed；OpenAPI `2026-08-31.2` 與 471／11／51 parser 通過。兩套 live source recheck 因立教 2 個 URL 與長庚 1 個 URL timeout 而 fail closed；三個 release fingerprint 與 9 類 blocker 維持預期）
- 範圍：長庚大學、國立臺北大學的 Web 可見合作校與申請流程
- 結論：仍阻擋發布；DATA-001、DATA-002 與 DATA-009 已關閉，但目前仍不能判定為 0 件已知重大申請錯誤
- AI 狀態：AI API 與本地 AI 串接均暫緩，不納入本次發布條件

## 1. 稽核依據

本次檢查結構、Web 實際載入結果、預設與隔離資料目錄的一致性及可重跑測試；尚未完成兩位人工審查者逐條回查官方來源。

| 類型 | 依據 |
| --- | --- |
| 長庚離線報告 | src/exchange_info/official_data/cgu/catalog-completeness.json |
| 長庚流程資料 | src/exchange_info/official_data/cgu/application_workflows.jsonl |
| 臺北大學離線報告 | src/exchange_info/official_data/ntpu/catalog-completeness.json |
| 臺北大學流程資料 | src/exchange_info/official_data/ntpu/application_workflows.jsonl |
| Web 實際載入 | 2026-07-29 以 create_app() 分別載入預設資料目錄與全新隔離資料目錄 |
| 自動化測試 | `pre-review.129` 使用 CI 相同 frozen environment 分開執行 804 項非 E2E 與 49 項 Web E2E，合計 853 passed、0 failed；耗時分別為 412.66 與 456.41 秒。dependency audit 回報 0 個已知漏洞；除既有 C-01 審查批次競態防護，亦驗證來源證據 snapshot 會涵蓋 schema、有效 workflow、pending revision 身分與完整研究候選，stale／generation race 均回 409，不交付 CSV。OpenAPI `2026-08-31.2` drift 通過；`pglast 8.4` 解析 21 份 migration 的 471 statements／11 SQL bodies／51 PL/pgSQL units，最新檔為 29／0／4。fresh runtime 從零套用 21／21 migrations，實跑 32／32 RLS、0 browser grants、3 個 workflow issue service RPC、submit／review 競態與冪等、限流、6 個 unsafe URL、刪帳 90 天／結案 24 小時 retention、purge／cascade／control 保留，並回傳 `cleanup_status=passed`；其後 container／network／volume 查驗皆為 0。正式 Supabase、既有資料升級、正式 Storage backend、遠端 CI、正式資料雙審與真人產品驗收仍待完成。 |

「有欄位」、「有來源 URL」或「schema 通過」只代表結構存在，不代表規定正確、仍有效或已由兩人查核。

B5-05 目前只建立安全的「學生回報 → 管理員獨立結案」技術流程。回報成立或不成立都不會修改正式 workflow、建立 revision、補來源／年度／查核日、形成 approval 或 publication，也不會降低下列任何資料 blocker。成立後仍必須回到原有內容治理，由兩位不同審查者依官方來源完成候選修正與發布。

## 2. 離線資料結構摘要

| 指標 | 長庚大學 | 國立臺北大學 |
| --- | ---: | ---: |
| 中央當期合作校 | 75 | 203 |
| 院級官方參考／中央當期未列 | 2 | 0 |
| Web 可見合作校 | 77 | 203 |
| workflow catalog | 77 | 203 |
| 與 Web 可見合作校相符的 workflow | 77 | 203 |
| Web 可見合作校缺 workflow | 0 | 0 |
| catalog 中沒有可見合作校身分的 workflow | 0 | 0 |
| 結構化流程 | 77 | 203 |
| 流程步驟 | 465 | 1,218 |
| 報告判定需確認步驟 | 465 | 1,218 |
| 文件要求 | 1,238 | 3,866 |
| 報告判定需確認文件 | 1,238 | 3,052 |
| 關鍵規定核對鍵（流程適用範圍＋步驟＋文件） | 1,780 | 5,287 |
| 缺直接官方來源的關鍵規定 | 0 | 0 |
| 含非 HTTPS 官方來源的流程／網址 | 3／5 | 6／7 |
| 來源 | 581 | 1,038 |
| 規定已引用但尚未建立來源證據資料的網址 | 12 | 203 |
| 結構問題 | 0 | 0 |
| Web 可見合作校 workflow verified／partial／未收集 | 1／76／0 | 110／93／0 |
| 流程 academic_year | 77 筆皆空白 | 203 筆皆為 115 |
| application_round | 77 筆皆空白 | 203 筆皆空白 |
| 從步驟 scope 彙整出的有效梯次 | 77／77 | 203／203 |
| 年度與梯次皆可驗證的流程 | 0／77 | 203／203 |
| 精確且可驗證的截止日期 | 0 | 0 |
| 只有參考時程的步驟 | 465 | 1,218 |
| 可加入行事曆／提醒的流程期限 | 0 | 0 |
| review_status | published 0；legacy 77 | published 0；legacy 203 |
| published_at | 0／77 | 0／203 |
| 流程最後查核日期範圍 | 2026-07-11 至 2026-07-29 | 2026-07-20 至 2026-07-27 |

長庚 completeness report 現在分開記錄 75 所中央當期合作校、2 所院級官方參考、77 所 Web 可見合作校與 77 份相符 workflow。原本的兩份 orphan 並非可直接刪除的舊資料：長庚管理學院近期官方資料仍列艾克斯馬賽大學管理研究所與雷恩商學院，但國際處中央當期名單未列。因此兩校改為 `departmental_reference`，可搜尋、瀏覽、比較與收藏；確認當期開放前，不可加入正式申請計畫或志願選單。原本缺少流程的 15 所中央當期合作校也已補入可追溯官方來源的參考流程，但仍未完成適用年度與雙人查核。

補充：

- 長庚的 581 個來源都有 URL 與 checked_at，但 effective_academic_year 全部空白。
- 臺北大學 203 份流程的流程層級 academic_year 皆為 115；但 1,038 個個別來源頁面沒有逐頁保存可證明 115 學年度的來源適用年度，因此來源層級 effective_academic_year 也全部維持空白。先前由流程年度自動衍生到來源的值已移除，不能當成人工查核證據。
- 兩校 1,619 筆既有來源紀錄都有來源年度缺口；另有 215 筆步驟／期限／表單／文件引用的官方網址尚未建立名稱、角色、權威層級、適用年度與查核日等來源證據資料（長庚 12、臺北大學 203）。因此工作台的完整來源證據缺口是 1,834 筆，而不是只計算 top-level `sources` 的 1,619 筆。這 215 筆流程引用實際只來自 6 個相同網址：NTPU 三份 115 學年度 PDF 與兩個國際處頁面，以及一個長庚國際處頁面；工作台依完整 URL 分組並顯示流程數與關鍵規定引用數。流程層級年度與每個來源頁面的適用年度仍是不同證據，不互相自動代填。
- `DATA-003-BATCH-002` 已為上述 6 個 exact URL 建立人讀／機讀研究包。封裝結果是 5 個可讀原始來源與 1 個應用層失效 NTPU 頁；候選只提出正式標題、母校角色、官方公告權威與可證明時才提出的 115 學年度。`scripts/check_source_metadata_research.py --check --timeout 30` 會去重後以最多 1 MiB 唯讀重查最終 HTTPS、狀態、PDF magic、HTML 應用層狀態與標題；網路錯誤或任何 manifest 漂移都 fail closed。2026-08-31 本次重跑連續兩次因長庚來源頁 read timeout 而 exit 1，其餘 5 個來源符合封裝狀態；因此目前不能宣稱 live 5／1 通過，也不自動更新 manifest。API、工作台與唯讀 CSV 全部固定 `can_prefill=false`，不建立待審版、不填查核日、不核准、不發布；所以 215／1,834／215 三類來源缺口及 release fingerprint 都刻意不變。
- `scripts/clear_derived_source_applicability.py` 預設只做 dry-run；本次明確套用後，從 203 份 NTPU legacy workflow 清除 1,038 個早期衍生值，長庚為 0 個變更。重跑 dry-run 為 0 個變更，正式 `published`、具有 `published_at` 或穩定 governance key 的流程不會被清除。
- `load_application_workflows()` 現在先結構化 local workflow 再與 bundled baseline 合併。修正前，local NTPU row 在合併時尚未推導 115 學年度，會與已推導的 bundled row 被視為不同 key，使部分載入路徑出現 483 筆；修正後 bundled、目前 runtime 與內容治理 store 均為 280 筆且無重複。
- 兩校每個步驟都有 checked_at 與 source_urls，但所有精確 deadline_at 都是空白；465 與 1,218 個步驟目前全部分類為 reference_only。
- Web 只會把 verified_exact、具有 HTTPS 來源與查核日期、且符合送件方式的日期加入行事曆／提醒。紙本或混合送件只有寄出期限、沒有必須送達期限時也不符合資格。
- 參考月份、慣例與「以當期公告為準」會顯示原文、待確認與聯絡單位，但不會被轉成日期，也不會進入提醒。
- 舊版曾從 `application_periods` 與合作校 `application_deadline` 文字擷取月／日並自行套用今年或明年；此路徑已移除。首頁預告、申請日曆、ICS 與第三方日曆現在共用相同 verified_exact 入口。
- 合作校清單、手機卡片、比較表、詳情摘要、方案選項、概覽、快速判斷與全站搜尋都把原始 `application_deadline` 統一標為「合作校參考時程」；沒有已驗證適用年度時會附「適用年度待確認」，不再以「合作校截止日」呈現。
- 截止日安全分類已統一納入「需確認步驟」口徑，因此目前兩校所有步驟都維持需確認；這是 fail closed 結果，不代表其他欄位全部缺失。
- 新的待審版本預設要求 2 位不同內容管理者各自提交核准說明、目前候選內容雜湊、完整官方來源 URL 及完整關鍵規定鍵清單；候選來源由流程來源、步驟來源、期限來源、步驟官方表單、文件來源及文件官方表單去重彙整，關鍵規定固定涵蓋流程適用範圍、每個步驟與每份文件。每條規定另有直接來源映射。漏掉或混入任何來源／規定、關鍵規定缺直接來源、來源引用缺少證據資料、來源年度缺漏／與流程不一致、含非 HTTPS 來源、使用過期雜湊或只有舊格式說明的核准都不能發布。同一帳號重複核准會被拒絕，核准不足時不能發布，未參與核准的第三位管理者也不能代按發布。核准帳號、時間、說明、內容雜湊、來源與規定清單會隨 revision 保存；成功核准同時以該次實際時間更新候選流程、全部來源與全部步驟的最後查核日期，但查核時間不改變內容雜湊。既有資料可相容讀取，但缺少新證明或查核日期的舊式核准不會被誤認為完成目前版本的雙審。
- `/admin/content-review` 由同一套內容管理權限保護，未登入為 401、已登入但未列入內容管理者清單為 403。工作台會呈現適用學年度／梯次、變更摘要、完整步驟、去重後官方來源與核准紀錄；每條適用範圍、步驟及文件都在自己的核對列顯示直接來源，每個來源另列出它支援的全部步驟、期限、表單與文件脈絡。缺來源、來源引用尚無證據資料、來源年度缺漏／不一致或非 HTTPS 時該列不可勾選並顯示發布阻擋；未建證據資料的來源名稱不再以介面脈絡預填，真人必須依官方頁面正式標題輸入。每位審查者須先補正證據、載入版本對照、勾完自己的來源與規定清單，核准鍵才解鎖。快速切換 backlog／待審時以請求序號淘汰較舊 response，避免卡片被舊資料重繪並遺失尚未送出的勾選；學生版沒有入口。
- `/admin/web-release-readiness`、工作台即時閘門與 `exchange-info --data-dir data audit-web-release` 共用唯讀 fail-closed 總檢查；既有 `/admin/application-workflow-release-readiness` 保留為申請流程子報告。申請流程子指紋涵蓋全部公開流程與 revision 的內容、審查及復原證據，`publication_history_integrity_gap_count` 逐 workflow 核對目前公開 payload、發布快照、版本鏈及恢復目標。生活情報子指紋另涵蓋 280 筆 profile 及全部審查、升級、復原事件，`destination_profile_publication_integrity_gap_count` 核對事件 ID、兩位不同審查者、內容雜湊、審查快照、時間順序、升級操作者及復原狀態；既有 `official_verified` 可保留，`official_partial`、未收集、仍待雙審或尚未明確升級者都阻擋 Web 發布。總指紋由兩個子指紋組成，相同資料可重現，任一面改變都會更新。API 僅管理者可讀並採 `no-store`／`nosniff`；CLI 有阻擋時 exit code 2，兩面全部通過才為 0。單純改狀態、缺少相符雙審證據或竄改任一復原鏈，仍列為阻擋。
- `/admin/application-workflow-review-backlog` 會把尚未具有正式 `published_at` 的 280 筆 legacy 流程列為可執行待辦，並回傳母校、合作校、計畫、有效年度／梯次、步驟、來源、關鍵規定、精確／參考期限、來源年度、最後查核日期、規定直接來源、非 HTTPS 及需確認數量。兩校共 7,067 個關鍵規定，等於 280 個流程適用範圍、1,683 個步驟與 5,104 份文件；長庚 1,780、臺北大學 5,287。目前 7,067 條都有直接來源，但 9 筆流程仍含 12 個非 HTTPS 網址（長庚 3 筆／5 網址、臺北大學 6 筆／7 網址）。缺來源證據的回應另提供 215 筆流程引用、6 個 distinct URL，以及每個網址的受影響 workflow key、合作校、母校與關鍵規定引用數；工作台可從群組限縮待辦，但不批次修改或核准。工作台亦可用關鍵規定來源、HTTPS 與最後查核日期等缺口碼精確篩選；完整待辦仍參與統計與搜尋，但畫面先顯示 25 筆並按需載入更多，避免行動裝置一次建立過長 DOM。建立待審副本採冪等操作，重複點擊回傳同一個 pending revision，不會產生多份待審資料；所有統計只反映已保存的官方資料，不推測或自動補入年度、期限或網址。
- `/admin/application-workflow-review-backlog/source-evidence.csv?source_url=...&expected_snapshot=...` 以相同內容管理權限匯出一個來源 URL 身分的唯讀查核清單；scheme／host 不分大小寫，但 path／query 精確區分。一個受影響 workflow 一列，包含年度、梯次、規定鍵／名稱、步驟／期限／表單／文件的精確引用脈絡、目前來源證據與人工查核空欄。每組 backlog 的專用 composite snapshot 涵蓋 schema 版本、有效 workflow content hash／版本、目前查核時間、pending revision 身分與完整 research candidate；參數、`X-Source-Evidence-Snapshot-Fingerprint`、檔名前 12 碼及 CSV 第一欄一致。過期或產生期間變更為 409，不存在的缺口 URL 為 404。回應使用 UTF-8 BOM、`no-store`、`nosniff` 與試算表公式防護；此路徑不接受匯入，也不建立 revision、寫入公開資料、核准或發布。
- `/admin/application-workflow-review-backlog/{workflow_key}/stage` 只建立既有公開版本的精確基準與相同內容候選版，不呼叫 publish，也不覆寫學生 API。兩位管理者正式發布前，學生 response、收藏、清單與進度都維持原狀；相同內容正式納入雙審也不會誤發「規定已更新」通知。
- `/admin/application-workflow-review-batches/{batch_id}/stage` 只允許內容管理者以目前審查內容指紋及 batch size 啟動單一批次。batch ID 格式將內容指紋、三位數 size 與三位數批號一起編碼；size 與 ID 不符或批次不存在為 404，舊指紋為 409。每筆沿用單筆 stage 的冪等語意，回應明列新建與沿用 revision；固定不建立核准、不發布、不發規定更新通知，也不修改學生 workflow。Web 另要求明確確認，取消時沒有 request mutation。
- `/admin/application-workflow-revisions/{revision_id}/comparison` 只回傳給內容管理者，依 `workflow_key + base_version` 找到該 revision 真正取代的 published／superseded 版本，再產生流程欄位、步驟、文件、送件與來源的可讀 before／after。比較採逐卡懶載入，避免一次讀取大量 revision；有基準版本時，工作台在比較載入前不開放核准。
- `PATCH /admin/application-workflow-revisions/{revision_id}/applicability` 只接受內容管理者修改 pending revision，並要求提交目前內容雜湊；較舊畫面送出的雜湊會以 409 拒絕，避免覆蓋另一位管理者的更新。審查者必須逐筆勾選已開啟確認的來源，未知 URL 被拒絕，未勾選來源不變；流程年度不會自動填入所有來源。前端即時顯示本次已選來源數與下一個缺少項目，只檢查已勾選列；流程學年度／梯次有實質修改或已選來源，且學年度、修正說明與所有本次來源欄位有效時才開放儲存。這是送出前便利檢查，不取代後端驗證，也不提供自動猜值、全選或批次代填。若規定引用尚未有 top-level 來源證據資料，只有真人填入來源名稱、角色、權威層級及年度後才會建立紀錄。非 HTTPS 來源可填入真人核實的 HTTPS 替代頁，後端會同步流程來源、合作校網站、步驟來源、期限、步驟表單、文件來源、文件表單、送件入口及動作網址的相同引用。多個舊入口只有在來源中繼資料與本次適用範圍一致時可明確合併；替換到未選取的既有來源、非 HTTPS 候選或中繼資料衝突都被拒絕。
- 適用範圍修正維持原 revision ID、版本與不可變 `workflow_key`，即使新增 academic_year 也不會被誤認為另一份流程。每次內容變更會保存審查者、時間、說明及前後內容雜湊，並清除所有既有核准，要求兩位管理者重新查核；正式發布時會用相同穩定身分取代舊版而不產生重複公開流程。

長庚 115-2 官方公告評估：

- 官方公告 `https://www.cgu.edu.tw/oia-ch/Subject/Detail/77899?nodeId=15817` 明列線上申請為 2026-04-21 起至 2026-06-06 23:59，預計 2027 年 1–3 月出國；以本次稽核日 2026-07-29 判斷已截止。
- 公告是校級梯次，不足以單獨證明 77 份 catalog workflow 內每一條資格、文件與合作校期限都適用 115-2，因此沒有批次覆寫 workflow academic_year，也沒有把已截止事件放入「即將截止」。
- 公告要求截止日前一併繳交紙本，但沒有明列紙本收件時刻；不能用線上 23:59 取代紙本必須送達時間。
- Web 現在把這筆資料建模為「115 學年度／第 2 學期」校內申請梯次，明示 `closed`、所有申請學生、官方精確日期與 2026-07-29 查核日；因已截止且紙本沒有獨立收件時刻，不建立提醒。
- 初審結果公告 `https://www.cgu.edu.tw/oia-ch/Subject/Detail/82632?nodeId=15817` 另列 2026-07-24 17:00 接受／放棄期限，以及只有姓名旁標記 `＊` 者才適用的 2026-09-21 17:00 語言證明補件期限。後者以「條件式申請者」獨立顯示，不會加入所有學生的提醒，也不會冒充新一輪申請截止日。
- 國立臺北大學 115 學年度簡章內的每年 9 月底／10 月與春季原則月份維持 `reference_only`；Web 明示不是下一梯次精確日期，等待當期公告後才可建立提醒。

## 3. Web 實際載入摘要

2026-07-29 修正後，預設資料目錄的 coverage API 顯示：

| 指標 | 長庚大學 | 國立臺北大學 |
| --- | ---: | ---: |
| Web 合作校總數 | 77（中央當期 75／院級參考 2） | 203 |
| Web 有流程 | 77 | 203 |
| workflow verified／partial／未收集 | 1／76／0 | 110／93／0 |
| 有圖片 | 62 | 203 |
| Web 判定有官方網站 | 77 | 203 |
| destination profile | 77 | 203 |
| 經驗查核完成／有來源 | 62／40 | 90／69 |
| 經驗來源數 | 173 | 165 |

另以全新隔離資料目錄啟動相同程式驗證：

| 指標 | 長庚大學 | 國立臺北大學 |
| --- | ---: | ---: |
| Web 合作校總數 | 77 | 203 |
| Web 有流程 | 77 | 203 |
| Web 判定有官方網站 | 77 | 203 |
| destination profile | 77 | 203 |

長庚 77 筆與臺北大學 203 筆 destination 現都屬專案追蹤的公開 bundled baseline，因此預設與全新隔離資料目錄會載入相同筆數；本機人工補正仍依母校＋合作校覆蓋，不會新增重複列。

## 4. 發布阻擋與修正狀態

| ID | 等級 | 狀態 | 問題／修正 | 剩餘影響或關閉證據 |
| --- | --- | --- | --- | --- |
| DATA-001 | P1 | 已關閉（結構與生命週期） | 長庚合作校、workflow catalog 與兩份 orphan 原本沒有明確口徑 | completeness report 現在記錄中央當期 75、院級參考 2、Web 可見 77、workflow 相符 77、缺流程 0、orphan 0；院級參考保留官方來源並禁止建立正式申請計畫 |
| DATA-002 | P1 | 已關閉 | 隔離預覽漏載臺北大學 203 筆官網公開 baseline | runtime 現在明確載入追蹤版公開 baseline；預設與全新隔離資料目錄皆為 203/203，API 回歸測試涵蓋 |
| DATA-003 | P1 | 未關閉（技術防呆、人工分流、逐來源補正介面、首批現行來源候選、6 個共用網址的唯讀中繼資料研究候選及即時漂移稽核已完成） | 工作台可精確篩出 77 筆缺流程學年度、0 筆缺有效梯次，以及 280 筆有來源年度缺口的流程。1,619 筆既有來源紀錄缺年度（長庚 581、臺北大學 1,038），另有 215 筆規定引用缺少來源證據資料（長庚 12、臺北大學 203），完整待補來源證據為 1,834 筆 | 校級 115-2 申請頁可顯示正式年度／梯次／狀態，但不外推到 77 筆長庚合作校流程。山東大學首批另找到官方 2026–2027 列表與 8 頁 HTTPS PDF；6 個來源證據 URL 則以 `DATA-003-BATCH-002` 提供 5 個可讀原始來源與 1 個應用層失效來源的唯讀研究結果，並可用 1 MiB 有界命令重驗傳輸、PDF／HTML 狀態與標題。前者仍須逐流程確認，後者不能提供候選值；兩批都不建立公開變更。未勾選來源保持空白，修正會清除核准並保存前後雜湊，系統不自行猜值 |
| DATA-004 | P1 | 未關閉（雙審閘門、待辦入口與 Web 工作台已完成） | 兩校 280 筆流程都是 legacy，published 0，published_at 0 | 280 筆現在都能由受保護工作台搜尋並安全建立待審副本；重複建立冪等，且學生內容不變。新 revision 必須由兩個不同內容管理帳號核准後，才可由其中一位正式發布；每次核准保存 reviewer、時間、說明、候選內容雜湊、完整來源清單及完整關鍵規定鍵清單。舊格式、過期雜湊、來源或規定不完整的核准不能發布。現有 280 筆尚未由真人完成雙審與發布，所以本項不能關閉 |
| DATA-005 | P1 | 未關閉（結構缺口已補） | 長庚中央當期 75/75 與 Web 可見 77/77 均有 workflow，但 465/465 步驟與 1,238/1,238 文件仍需確認；臺北大學 1,218/1,218 步驟與 3,052/3,866 文件需確認 | 新增 15 份流程皆有合作校官方來源且維持參考／未發布狀態；兩筆院級參考也不會冒充中央當期開放。資格、文件與例外仍須逐條雙審，目前不能宣稱學生只照產品指示就能可靠完成全部申請 |
| DATA-006 | P1 | 未關閉（兩校穩定真人分工、逐項查核表、個人待辦與分頁續接、獨立雙審、明確升級及安全復原機制已完成） | Web 工作台可切換長庚與臺北大學，並隔離 queue、CSV、批次定位、逐項表、目前管理者篩選與公開歷程。長庚 58 筆待審／246 個來源分為 6 批，逐項總量 942；臺北大學 85 筆／224 個來源分為 9 批，逐項總量 1,244。未送出表單只按管理者與內容指紋留在目前分頁工作階段；正式 `data` 仍為 0 筆真人審查、升級與復原事件 | 每位管理者須逐一核對 profile 全部來源與 12 個內容區塊；逐項 CSV 的 A／B 欄預設空白且不能匯入，分頁暫存也不能形成證據。審查進度不使既有批次換員，內容或待審成員改變則使舊連結失效。兩位核可後仍由有效核可者明確升級；自動化不能代替真人，因此 143 筆全部處理前本項不能關閉 |
| DATA-007 | P1 | 未關閉（技術防呆與人工分流已完成） | 工作台可精確篩出 280 筆沒有已驗證精確期限的流程；現有 1,683 個合作校步驟期限全部分類為 reference_only，提醒資格為 0 | 精確期限只有同時具備 `verified_exact`、日期、HTTPS 來源與查核日且符合送件方式時才計入；缺任一項就維持待確認。長庚校級 115-2 已截止期限與 9/21 條件式補件不會冒充下一梯次。內容管理者可依缺口排序處理，但仍須等當期官方公告並補齊來源、查核日及紙本送達期限 |
| DATA-008 | P1 | 未關閉（待辦入口、逐欄比較及逐來源／逐規定雙人證明已完成） | 兩校 280 筆流程共 7,067 個關鍵規定，尚未由兩位真人逐條查核 | 工作台已把全部 legacy 流程變成可操作待辦；兩位審查者都必須各自載入比較、勾選全部來源，再逐項核對流程適用範圍、每個步驟與每份文件，核准才會綁定目前內容雜湊、來源清單及關鍵規定鍵清單。系統拒絕同帳號重複、過期畫面、來源或規定缺漏／未知及核准不足的發布；相同內容候選會明示 0 項流程／步驟／來源變更與未變步驟數。但自動化測試不能代替真人查核，仍須由兩個不同管理帳號逐筆完成 revision 核准、填寫雙審表，且所有疑義有處置紀錄 |
| DATA-009 | P0 | 已關閉 | destination profile 原本沒有 home university，可能把同一合作校的臺北大學研究結果算到長庚 | 模型、儲存鍵、API、advisor 與 Web 載入皆按 home university 隔離；同名合作校雙校資料回歸測試通過 |
| DATA-010 | P1 | 未關閉（盤點、發布阻擋、安全替換、合併工具、12 筆 manifest、全網址傳輸查核、不可替代研究線索、人工候選工作台與唯讀分工 CSV 已完成） | 9 筆流程仍含 12 個非 HTTPS 官方網址；連同 DATA-003 山東大學候選，backlog 現有 10 筆流程／13 個候選（強 8、條件 5），其中 2 個候選的封裝證據顯示 HTTPS 請求轉回 HTTP。六個安全官方頁只提供相鄰、反向、聯絡窗口、通用文件或不同學院脈絡，不能證明內容等價 | `scripts/check_source_replacement_transports.py --check` 會以 TLS 驗證、redirect 與 response headers 重查候選、輔助連結與研究線索共 22 個去重網址，不保存本文或修改資料；封裝基線為 20 個最終 HTTPS、2 個降級 HTTP。2026-08-31 本次重跑連續兩次因立教大學候選頁與 supporting page connect timeout 而 exit 1，不能把封裝基線冒充本輪即時通過，也不自動修改候選。UNN 與人民大學的 2 筆降級候選仍禁止填入，相鄰安全頁也不能替代。工作台與 CSV 分開顯示內容強度、傳輸狀態及不可替代原因；篩選、下載與 API 都不建立 revision、核准或發布。候選仍未由兩位真人逐頁認定等價，所以不得直接更新或關閉 |

目前仍沒有足夠證據宣告 P0=0；DATA-009 已修正，但關鍵規定尚未逐條審完，所以不能宣告不存在其他重大錯誤。

## 5. 已通過但不能取代資料審查的項目

- Web 黃金路徑、權限與隱私負面情境可用真實 Chromium 重跑。
- 訪客搜尋／收藏／比較、登入同步、資格與志願、文件表單、PDF、送件進度、社群權限、個人文件同意與刪帳去識別已納入 E2E。
- `pre-review.129` 非 E2E 804 passed、Web E2E 49 passed，分開執行合計 853 passed、0 failed；OpenAPI `2026-08-31.2`、21 份 migration 的 471／11／51 parser 與 dependency audit 0 個已知漏洞均通過。DATA-003 來源證據 CSV 現在從 backlog 到實際下載全程使用專用 composite snapshot；candidate manifest、schema、workflow 內容或 pending revision 身分變更會使舊快照失效，產生期間競態也 fail closed。單元與 API 測試確認沒有 CSV、副作用、approval 或 publication；Chromium 驗證真實下載 URL、檔名及每列指紋一致。正式三個 release fingerprint 不變，release audit 仍為 9 類 blocker；舊有 112 檔 `data/**`＋`official_data/**` Windows 聚合值雖仍為 `c63d8376e9a14c3d650682ffa30744dd75f21017fa156e38d388fa056244f49c`，但集合含本機 runtime 狀態且依賴 Windows 路徑／排序，不再把它誤稱為跨平台的正式資料專用證據。current 21／21 fresh runtime 邊界維持有效，遠端 CI、正式 Supabase、既有資料升級、正式 Storage backend 與正式安全／隱私人工審查仍未完成。
- `pre-review.128` 非 E2E 801 passed、Web E2E 49 passed，分開執行合計 850 passed、0 failed；OpenAPI `2026-08-31.1`、21 份 migration 的 471／11／51 parser 與 dependency audit 0 個已知漏洞均通過。C-01 的申請流程審查批次改在 readiness 與全部 rows 完成後重算內容指紋；若產生期間有實質內容／成員變更，函式 fail closed、CSV API 回 409。當時記錄的舊 workspace data-tree Windows aggregate 與三個 release fingerprint 前後相同，沒有 revision、approval、publication 或學生資料變更。current 21／21 fresh runtime 仍通過 32／32 RLS、0 browser grants、3 個 workflow issue RPC ACL 與既有 transaction／cleanup 邊界；遠端 CI、正式 Supabase、既有資料升級、正式 Storage backend 與正式安全／隱私人工審查仍未完成。
- 申請流程安全復原已由 API 與真實 Chromium 驗證，但正式 `data/processed/application_workflow_revisions.jsonl` 仍不存在，因此正式資料是 0 筆 workflow revision、0 筆 rollback revision；不把隔離測試的雙審、發布或復原當成人工完成。正式 Supabase 仍須套用 `20260819150000_application_workflow_publication_rollbacks.sql` 並完成營運驗收。
- 生活情報工作台現在能保存真正登入管理者的審查、升級與復原證據，但正式 `data` 仍是 0 筆審查事件、0 筆升級事件、0 筆復原事件；E2E 與 API 使用的兩位測試管理者只證明流程可運作，不能計入 46 筆待第二位真人的完成數，也不能把測試升級或復原當成正式內容核准。
- 目前 Web 總發布閘門為 `NOT READY`，總指紋 `6c88731481993e0bcf3da9627153db86731a13403605607478fba4f9cb9df49d`。申請流程子指紋 `e72b8c4a35ae34294ad497af9988d740e9f4236caaa9fe3396dbe32f4af4d57c` 對應 280 筆流程、0 筆正式發布與 7,067 個關鍵規定，8 類阻擋是未正式發布 280、缺學年度 77、缺精確期限 280、缺來源證據 215、來源年度缺口 1,834、查核日期缺口 215、非 HTTPS 12、待確認流程／步驟／文件 6,253。生活情報子指紋 `d73804f1ec16ddc7e61e71fc8a199a021b285cd2a7a658e9ec9186077b070011` 對應 280 筆 profile、137 筆已完整查核、143 筆待審與 470 個待審來源，新增 1 類阻擋；兩面的發布歷程完整性缺口都是 0，總計 9 類阻擋。真實 Chromium 已驗證工作台顯示相同狀態與數字；CLI 同一快照以 exit code 2 拒絕放行。
- 內容管理者可下載申請流程雙人審查分工 CSV。CSV 列出申請流程子報告的「發布狀態指紋」，不混入生活情報子指紋；另有批次定位使用的「審查內容指紋」，只涵蓋有效候選／公開內容與待審成員，不包含建立 revision、核准時間或核准人等進度證據。預設依非 HTTPS、規定來源證據、來源年度、精確期限與待確認規定等實質內容缺口固定排序；核准時自動補上的查核時間不參與換批。每 10 個 workflow 一批，現況為 280 列／28 批且關鍵規定合計 7,067；A／B、查核時間、問題與決定欄保持空白。產生前後實質內容不同時 API 以 409 拒絕交付，匯出不能匯入、建立 revision、修改公開資料、核准或發布。
- 生活情報另有獨立的審查內容指紋與雙人分工批次：長庚 58 筆／6 批、臺北大學 85 筆／9 批，預設 10 筆一批。CSV 保留完整來源、缺口、人工 A／B 空欄與工作台路徑；批次路徑同時帶母校、批次大小及預期指紋。真人新增審查進度不改變指紋、批次 ID 或成員；profile 內容、待審成員、升級或復原改變實質清單時舊指紋回傳 409，不存在的目前批次回傳 404。匯出採 UTF-8 BOM、公式防護、`no-store`／`nosniff`，且不能匯入、修改、核准、升級或發布。
- Web 在保存生活情報審查、明確升級或復原後都會先重驗目前批次，再重新載入 queue 與公開歷程。第一／第二份審查不改指紋時批次維持；升級／復原改變待審成員造成 409 時，操作成功與舊批次過期在同一訊息呈現、批次成員不套用且逐項表入口隱藏。非 404／409 的重驗錯誤也明示舊定位未套用；過期 URL 保留到管理者明確清除，不會靜默映射到新批次。
- 有效生活情報批次中的個人未審項目可用「保存並前往下一筆我的待辦」續接。保存成功且批次重驗有效後，Web 清除搜尋、切到個人待辦，依原批次固定順序開啟並聚焦下一筆；沒有下一筆時只宣告目前帳號沒有未審項目，明示不代表另一位審查者、雙審、升級或發布完成。過期或重驗錯誤時不執行續接。
- 有效生活情報批次摘要另顯示目前帳號的待辦數，並提供第一筆／下一筆及完整清單導覽。第一筆與下一筆依原分工 profile 順序循環，會清除搜尋、切到個人未審、展開正確卡片並移動鍵盤焦點；回到完整待辦會清除焦點並收合卡片，手動展開批次卡則更新下一筆起點。待辦為零時導覽停用；批次過期或載入錯誤時隱藏，不能越過 snapshot-bound 範圍。
- 審查表會把後端禁止核可的三種缺口提前呈現：`missing_sources`、`insecure_sources`、`missing_last_checked` 分別顯示缺官方來源、非 HTTPS 與缺最後查核時間，強制結論為要求修正並停用核可。`coverage_not_verified` 與 `second_review_required` 仍屬正常人工雙審，不誤列為阻擋。送出前會再次依目前 queue row 驗證，DOM 竄改也不呼叫 API；無阻擋的綠色狀態只代表可選擇核可，仍不取代逐頁與 12 區塊核對。
- 工具列另以同一 helper 獨立篩選可選擇核可／只能要求修正，不與雙審進度混用。批次摘要的完整個人待辦數不因門檻篩選縮小，另列兩類結構數；批次第一筆／下一筆及保存後續接只處理目前門檻。篩選無結果但其他門檻仍有個人待辦時，清單與按鈕明示只是目前門檻為空，不能顯示整批完成；切換母校清除條件。
- 每個生活情報批次另可下載逐項查核表。表內每個 profile 固定有 12 列「內容區塊」，並依其官方來源各產生一列「官方來源」；全體 143 筆待審因此對應 1,716 列區塊與 470 列來源，共 2,186 列。每列保存候選內容、對應來源、profile 指紋與工作台路徑，A／B 核對、時間、說明、疑義及處置全部空白；只有管理者可下載，舊審查內容指紋為 409、不存在批次為 404。這張表只協助逐項分工，不會建立審查事件。
- 生活情報工作台可依目前登入管理者篩選「我的待辦」與「我已留下結論」。尚未送出的來源／12 區塊勾選、結論與說明只保存於 `sessionStorage`，鍵值同時包含管理者 ID 及完整 profile 內容指紋；讀回時再次核對身分、指紋、允許的結論值與欄位型別／長度。重新整理同一分頁可恢復，手動清除或後端成功接受審查後刪除；送出失敗保留，換帳號或內容指紋後不會沿用。這是本機操作便利層，不參與雙審計數、後端事件、升級、發布或 release readiness。
- 申請流程待審表的來源、關鍵規定勾選與查核說明也只保存於 `sessionStorage`，鍵值同時包含管理者 ID、revision ID 及完整候選內容雜湊；讀回時再次驗證三者及欄位型別／長度。重新整理後須回到待審版本並重新載入基準／候選對照，才能在相同安全門檻下繼續；手動清除只重設本頁，核准、退回或發布成功後刪除，後端拒絕時保留。草稿不會補查核時間、增加核准人數、同步到其他裝置、寫入 append-only 事件或參與 release readiness。
- 申請流程資料補正另有獨立 `sessionStorage` 草稿，保存流程年度／梯次、修正說明、逐來源勾選及本次來源欄位；鍵值同樣綁定管理者 ID、revision ID 與候選內容雜湊。讀回會拒絕不相符身分／版本、未知或重複來源 URL、超長／錯誤型別欄位及不在 allowlist 的來源角色／權威層級；重整後自動展開並恢復。「清除補正草稿」只還原目前 revision 候選值，成功補正或審查後刪除，後端拒絕時保留。草稿不寫入 revision、不清除核准、不更新查核日，也不參與雙審或 release readiness。
- 補正表每個來源列即時顯示本次未選、第一個缺少欄位或本次欄位完成；全域導覽依流程年度、修正說明及來源 DOM 順序標記唯一 `data-applicability-current-issue`，將焦點移到實際 input／select／textarea。全部選取來源完成後按鈕隱藏；功能不自動勾選來源、不代填、不觸發儲存或核准。非 HTTPS 且尚無 top-level 證據的候選來源也會顯示必要替代網址欄，避免只能看見缺口卻無法人工修正。
- 申請流程清單模式可用 `review_status` 重載；從 backlog 開啟既有待審版時再以 `workflow_revision` 精確定位並聚焦，切離 backlog 同時清除舊 workflow／batch snapshot 參數。URL 不保存表單內容、審查證據、token 或權限；重新整理仍由管理者 API 重新授權載入。revision 已發布、退回或不存在時顯示失效定位且不套到其他版本，成功處置後移除定位。待審清單的「我的待辦」、「我已核准」與「可由我發布」完全依目前後端 revision 的有效核准者及兩人門檻計算，摘要同步篩選，不讀取 `sessionStorage` 草稿。
- 真實 Chromium 已驗證下載上述 280 列／28 批 CSV：批次工作台正好顯示 10 個 workflow；批次 ID 綁定內容指紋、size 與批號。取消建立不寫入，首次明確確認回報新建 10／沿用 0，第二次重試回報新建 0／沿用 10，revision IDs 相同、核准清單全空且公開 workflow byte-for-byte 不變；E2E teardown 還原進場前 revision 快照。批次 API 僅限內容管理者、採 `no-store`／`nosniff`，錯誤指紋 409、size 不符或不存在 404。建立待審或增加核准不改變審查內容指紋與現行批次；候選內容或成員改變才使舊連結過期。
- 有效批次單筆儲存候選補正時，前端不再只更新本機 revision 後繼續沿用舊批次；它會立即以原 batch ID、size 與 snapshot 重驗。候選內容更新造成 409 後，批次標示過期、成員與 `workflow_revision` 清除，第一筆／下一筆／返回導覽停用；重新驗證若是其他錯誤也採相同 fail-closed 導覽邊界。管理者須清除過期批次並重新下載目前分工清單，不能直接跳到舊批次下一筆。
- 整批 stage 完成後，Web 只有在批次內全部 workflow 都具有 pending revision 時才允許「開始審查此批次」。待審模式保留 batch ID、size 與 snapshot，預設使用目前帳號的「我的待辦」，重新整理會重新呼叫受保護批次 API。真實 Chromium 在 390px 驗證只顯示批次內 10 筆、批次外另 1 筆不混入；重新整理後仍維持 10 筆。竄改 snapshot 時舊範圍不套用，只依目前帳號顯示可存取的 11 筆，清除定位後 URL 也移除批次參數。這些 URL 不保存表單、token 或權限，也不形成任何審查證據。
- 批次個人待辦另提供第一筆／下一筆循序導覽及返回同批次清單；單筆模式同時保存 batch 與 `workflow_revision`，但仍不保存表單、token 或權限。真實 Chromium 在 390px 驗證由 10 筆開啟第一筆、切換到不同 revision、返回 10 筆、再次開啟單筆後重新整理仍停在同一 revision。把 snapshot 竄改為錯誤值後，受保護批次 API 以 409 拒絕，Web 同步移除 `workflow_revision`，不讓舊單筆定位把目前 11 筆安全待辦縮成 1 筆。
- 待審頁把既有核准禁用邏輯收斂為單一 correction state，供資料狀態篩選、批次摘要、卡片頂部缺口與核准按鈕共同使用。檢查範圍是官方來源存在／HTTPS、關鍵規定直接來源、流程年度／梯次／適用狀態、來源證據與來源年度；不把載入對照、真人勾選或核准結果誤算成資料補正。第一批 10 筆在隔離 Chromium 中為可核對 0／須補資料 10；點擊缺口卡會展開同卡人工編輯器。另一條情境逐頁填入正式來源年度與缺少的來源證據後才顯示綠色門檻完成，仍須再走完整雙人核對。
- 審查內容指紋另包含批次 schema 版本。早期版本已將核准自動補上的查核時間移出批次排序，避免第一份或第二份核准造成換批；pre-review.72 再把 batch size 編入 ID（`review-{fingerprint}-{size}-{number}`），因此舊 schema 連結會明確失效，且同一 ID 不能被另一個 size 靜默解讀成不同成員。隔離測試證明核准進度不改變審查內容指紋與成員，而 size 不符的批次 stage 會 404。
- 批次工作台另可下載快照限定的逐規定 CSV。第一批 10 個 workflow 實際展開為 251 列，精確等於該批關鍵規定總數；每列包含規定鍵、可讀內容、全部官方來源及來源證據／年度／查核日／HTTPS／待確認阻擋，並保留 A／B 與疑義處置空欄。真實 Chromium 已完成下載、數量及 10 個 workflow coverage 驗證；清除批次後下載入口也會確實隱藏，不會誤用上一批。
- 待辦、來源證據群組、批次列與逐規定 CSV 現共用同一份最新 pending revision 作為管理者審查內容；候選版補齊來源名稱、角色、權威層級、年度或梯次後，舊缺口會立即從管理者統計與群組消失，逐規定內容也顯示候選值。公開學生資料仍只讀正式發布版。每列另回傳已核准人數、所需核准人數及是否達門檻；工作台可分別篩選待第一位、待第二位與已達雙審，批次摘要顯示各進度數量。
- 新增的隔離 Chromium 情境先驗證 215 筆缺來源證據流程精確群組為 6 個相同網址，從最大群組可限縮到 119 筆流程，並由瀏覽器下載 119 列、合計 828 筆規定引用的唯讀 CSV；每列都保留精確脈絡與人工雙審提醒。清除網址篩選後仍保留「缺來源證據」條件的 215 筆；390px 群組版面沒有水平溢位。第一位真實登入的內容管理者再逐頁補齊全部來源適用年度，並為規定已引用但尚無 top-level 證據資料的 URL 依官方頁面標題補上名稱、角色與權威層級；之後兩個不同內容管理帳號分別在桌面與 390px 畫面載入比較、逐一勾選相同候選版的全部官方來源，再逐項核對流程適用範圍、每個步驟與每份文件，保存兩份獨立核准後由第二位發布。最終 revision 內兩份核准都保存相同內容雜湊、完整來源數及完整關鍵規定數，流程、來源與步驟也保存實際核准時間。初始化 backlog 與切換待審的競態以請求序號淘汰舊 response，不會重繪卡片或清除勾選。
- 登入 E2E 發現成功 session 會被後續非關鍵帳號資料載入延遲而表面卡在登入對話框；Web 現在於 session 成功後立即關閉對話框，並以獨立 settled 結果載入社群、權益、工作區、日曆、通知與表單草稿。局部失敗只顯示可重試提示，不會把成功登入回滾或誤報為失敗。
- 另一個隔離 Chromium 情境從實際 9 筆非 HTTPS backlog 選取單筆流程，驗證來源及受影響規定不可勾選、核准持續鎖定；內容管理者在 pending revision 填入 HTTPS 替代網址後，所有 workflow 內相同引用完成同步、阻擋消失、核准仍為 0，正式公開 backlog 仍保留舊網址與阻擋，證明修正沒有提前發布。
- headed Chromium 已在隔離資料目錄以兩個不同內容管理帳號完成 1／2、2／2、正式發布與已發布鎖定流程；1440px 與 390px 均無水平溢位，console 為 0 errors／warnings。證據為 `output/playwright/c01-review-workbench-admin-a-desktop.png`、`output/playwright/c01-review-workbench-admin-a-mobile.png`、`output/playwright/c01-review-workbench-ready-mobile.png` 與 `output/playwright/c01-review-workbench-published-desktop.png`。
- 另一組隔離 revision 以 headed Chromium 驗證載入前核准鎖定、載入後解鎖、流程層級 1 項、步驟 1 項、來源 1 項、未變步驟 5 項，以及文件份數／新增文件的 before／after；1440px 與 390px 均無水平溢位，console 為 0 errors／warnings。證據為 `output/playwright/c01-review-comparison-desktop.png`、`output/playwright/c01-review-comparison-mobile-collapsed.png` 與 `output/playwright/c01-review-comparison-mobile-expanded.png`。
- 另以隔離帳號載入實際 280 筆 legacy 待辦，驗證首批只渲染 25 筆、按「再顯示 25 筆」後為 50 筆，搜尋林肯大學後重設為單筆，建立待審副本並確認待辦統計由 1／0 改為 0／1；「前往待審版本」會切換佇列並聚焦正確 revision。版本對照顯示流程欄位 0、步驟 0、來源 0、未變步驟 9。1440px 與 390px 的 `scrollWidth` 均等於 viewport，console 為 0 errors／warnings；QA 帳號資料完成後已移到資源回收筒。證據為 `output/playwright/c01-review-backlog-desktop.png`、`output/playwright/c01-review-backlog-mobile.png` 與 `output/playwright/c01-review-backlog-mobile-card.png`。
- 另以全新隔離資料驗證缺口分流：預設 280 筆中缺流程學年度 77、缺有效梯次 0、沒有已驗證精確期限 280、有來源年度缺口 280；1,619 筆既有來源紀錄加上 215 筆未建證據資料的規定引用，合計 1,834 筆來源證據待補，215 筆流程另顯示最後查核日期缺口，且 280 筆都有待確認步驟。215 筆未建證據引用依完整 URL 去重後為 6 組，流程數依序為 119、48、19、15、12、2，合計仍為 215；每組均至少支援一條關鍵規定。「缺學年度」、「來源年度缺口」、「缺最後查核日期」、「缺有效梯次」與「已建立待審版」篩選及缺口優先排序均符合統計，建立待審版後學生內容維持不變。先前 c09 截圖中的 77／581 是來源年度仍被流程年度自動衍生時的舊口徑，已由本次較保守的逐來源證據規則取代。
- 以同一隔離資料的 Lincoln 待審版本驗證只確認第一個來源：候選流程年度為 115、來源年度為 1／9、其餘 8 筆保持空白；版本對照精確顯示流程欄位 2、步驟 9、來源 1，且 0／2 核准。公開版本內容雜湊在補正後仍為 `8d70c1dda937808f6f4e6e112686d0ac7e698caee6555a0925a33b56588255ef`；待審修正紀錄從該雜湊連到新雜湊並沿用相同 workflow key。1440px 與 390px 無水平溢位，390px 的 scrollWidth 與 viewport 同為 390，乾淨 session 為 0 console errors／warnings。證據為 `output/playwright/c10-applicability-edit-desktop.png` 與 `output/playwright/c10-applicability-editor-mobile.png`。
- 第一批人工內容審查證據包為 `docs/review-batches/data-003-batch-001-ntpu-shandong-115.md`。它把 NTPU 115 學年度公告／英文簡章、山東大學 2026–2027 交換計畫、經濟學院與威海校區資料分開，並將一般檔案索引、首頁及明列 2022–2023 的舊 PDF 保持為不得冒充 115 的阻擋。因目前沒有可識別的真人內容管理者登入紀錄，本輪沒有直接寫入 pending revision，也沒有核准或發布。
- JavaScript 語法檢查通過。
- 真實 Chromium 已驗證 Lincoln 流程在 1440px 與 390px 顯示年度待確認、參考時程不進提醒，且空白申請日曆不會出現 11/01、12/20、4/21、6/06 的推測年份；console 為 0 errors／warnings。截圖位於 `output/playwright/c01-deadline-safety-desktop.png`、`output/playwright/c01-deadline-safety-mobile.png` 與 `output/playwright/c01-unverified-deadline-calendar-guard.png`。
- 真實 Chromium 已驗證 legacy 流程顯示「尚未完成正式發布」，不會冒充已發布流程；截圖位於 `output/playwright/c01-publication-guard.png`。
- 真實 Chromium 已驗證 Paris-Saclay 可由合作校清單搜尋、顯示 6 步參考流程與官方來源，2026-10-30 文字不會進入申請日曆；390px 無水平溢位，console 為 0 errors／warnings。截圖位於 `output/playwright/cgu-backfill-paris-saclay-desktop.png`、`output/playwright/cgu-backfill-paris-saclay-mobile.png` 與 `output/playwright/cgu-backfill-calendar-guard-mobile.png`。
- 真實 Chromium 已再次驗證 Paris-Saclay 的桌面詳情、快速判斷與 390px 手機卡片都顯示「合作校參考時程」及「適用年度待確認」，日曆仍沒有 2026-10-30 或 Paris-Saclay 事件；桌面與手機均無水平溢位，console 為 0 errors／warnings。截圖位於 `output/playwright/deadline-reference-paris-saclay-desktop.png`、`output/playwright/deadline-reference-paris-saclay-mobile.png` 與 `output/playwright/deadline-reference-paris-saclay-card-mobile.png`。
- 真實 Chromium 已驗證名額狀態可單獨篩出 2 所院級參考；搜尋雷恩後只顯示 1 所，桌面與 390px 手機卡片／詳情均顯示「中央當期名單未列」與確認要求，正式申請按鈕為 disabled，localStorage 沒有新增申請校。390px 的 scrollWidth 等於 viewport 390，console 為 0 errors／warnings。截圖位於 `output/playwright/c01-departmental-reference-desktop.png`、`output/playwright/c01-departmental-reference-detail-desktop.png`、`output/playwright/c01-departmental-reference-detail-mobile.png` 與 `output/playwright/c01-departmental-reference-card-mobile.png`。
- 真實 Chromium 已驗證長庚校內 115-2 顯示為已截止、紙本精確收件時間待確認；9/21 補件只標示給初審名單有 `＊` 的申請者。切換國立臺北大學後，兩筆歷年原則都只顯示參考時程。1440px 與 390px 版面無水平溢位，390px 的 scrollWidth 等於 viewport 390，console 為 0 errors／warnings。截圖位於 `output/playwright/c02-home-cycle-desktop.png`、`output/playwright/c02-home-cycle-mobile.png` 與 `output/playwright/c02-ntpu-reference-period-mobile.png`。
- 內容治理 API 已驗證零核准、一位核准、同帳號重複核准、未核准第三人發布、過期內容雜湊、漏掉／混入來源、漏掉／混入關鍵規定、關鍵規定缺直接來源、來源引用缺證據資料、流程／來源年度缺漏或不一致、非 HTTPS 來源、缺最後查核日期及缺少新版證明的舊格式核准均被拒絕；只有兩個不同管理帳號都綁定目前版本、完整來源與完整關鍵規定後可發布。來源修正測試另涵蓋為既有規定引用建立來源證據資料、期限、步驟表單、文件來源、文件表單、送件入口與動作網址同步，相容來源合併，以及非 HTTPS、未選取碰撞與中繼資料衝突拒絕。內容更新通知只在正式發布後產生一次。Supabase migration 與 adapter 測試涵蓋 required_review_count、review_approvals JSONB、edit_history、穩定 workflow key、service-role-only 既有表格邊界及舊 revision 安全預設；`pre-review.127` 已在全新本機 PostgreSQL／兩個獨立 PostgREST／Storage API file backend 套用 21／21 migrations，通過 32／32 RLS、0 browser grants、direct DML、transient／workspace 並行、workflow issue submit／review／retention／purge、公開／私人社群多 API instance 競態、六種社群 receipt 晚期錯誤完整 rollback、刪帳 rollback、Storage timeout／實際 delete／replay 與巢狀 orphan cleanup。這仍不等於正式 Supabase project、既有資料升級、正式 Storage backend、遠端 CI 或真人內容雙審已完成。
- 預設與隔離 runtime 的公開 baseline 統計均已實際驗證。
- 測試資料不寫入正式 data 目錄。
- 這些結果證明功能行為，不能證明 280 所 Web 可見合作校的規定內容正確；其中兩所院級參考也不代表中央當期開放。

## 6. 後續關閉順序

1. 由兩位真實內容審查者使用生活情報工作台處理 DATA-006：每人逐筆核對全部來源與 12 個內容區塊；有疑義先要求修正，兩人核可後才由其中一位有效核可者明確升級。若升級後發現錯誤，從公開歷程填寫原因並明確復原，復原後必須重新雙審。不得將測試事件寫入正式資料，也不得自動升級或復原狀態。
2. 優先處理 DATA-003、DATA-007 與 DATA-010 的內容缺口：用工作台逐頁確認 1,619 筆既有來源紀錄的適用年度，為 215 筆既有規定引用建立來源證據資料，依證據包處理 9 筆流程／12 個非 HTTPS 網址；Lobachevsky 與人民大學 SIS 雖已有安全官方脈絡頁，仍須找到最終 HTTPS 且內容等價的正式來源，不能使用目前會降級的候選或直接拿相鄰方案替代。補齊長庚合作校流程適用年度，並在兩校下一梯次公告後建立可驗證精確期限；不沿用已截止日期，也不放寬現有 fail-closed 規則。
3. 每次更新中央或院級資料時，重新確認兩所 `departmental_reference` 是否已進入中央當期名單、仍只屬院級參考或應封存；未確認前維持正式申請阻擋。
4. 逐校查核新補 15 份參考流程、2 份院級參考，以及既有流程的資格、期限、文件、送件方式、承辦與例外。
5. 由第二位審查者獨立複核，差異回到資料修正與回歸測試。
6. 完成正式發布流程與 reviewer／published_at／版本證據，關閉 DATA-004。
7. 只將雙審通過的規定標為可依指示完成；其他資料維持待確認並提供官方聯絡方式。
8. 再由產品負責人與測試學生走完整 Web 審核清單。

## 7. 判定

DATA-001、DATA-002 與 DATA-009 已有程式、API 與測試證據可關閉，但 DATA-003 至 DATA-008、DATA-010 尚未全數關閉，資料正確性仍不符合 C-01 完成條件。Web release candidate 維持 NOT READY，Flutter 移植維持關閉，AI API 與本地 AI 串接維持暫緩。

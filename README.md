# 台灣大學生交換申請資訊整理系統 MVP

目前 Web 版支援長庚大學與國立臺北大學。長庚資料入口為國際事務處公開網站；臺北大學版接入 116 學年度赴外交換簡章（2026-09-24 公告）與英語、日語、中文三組官方名額表（115 學年度資料保留），並補上現行合作資料庫中具交換合約、但尚未列入 116 學年度名額表的 37 所合作校。畫面會區分「本期開放」與「合作備查」，不會把合作合約誤當成當期可申請名額：

https://www.cgu.edu.tw/oia-ch

https://new.ntpu.edu.tw/oia

這個 MVP 會抓公開頁面，整理成 JSONL 與 FastAPI API，供未來 APP 查詢來源索引、摘要、附件與結構化交換資訊。爬蟲不登入任何系統、不蒐集公開頁面中的個資，也不把整篇原文設計成前端回傳格式。申請文件工作台只處理學生主動輸入的資料，產生 PDF 後不會替學生送件。

目前採 Web-first 開發流程：先在網頁版確認資訊架構、內容與操作，再由使用者明確確認後同步到 Flutter 的 iOS 與 Android 版本。國立臺北大學這一輪只加入 Web 與共用 API，尚未同步到原生 App。

目前階段暫不串接任何雲端 AI API，也不要求設定 AI 金鑰。選校、資格、文件與期限先使用已查核的結構化規則；等本機 AI 執行環境準備完成後，再透過既有 provider 邊界接入本地模型。

2026-10-02 補充：申請主線新增文件「一路完成」進度條、官方步驟直達對應文件、年度未發布時的預估清單與建議工時、變更通知的受影響任務、預算／授課語言／課程訊號，以及學校詳情的資料完整度。逐項完成度、仍未完成的部分與已知的工作樹落差見 [`docs/application-journey-completion.md`](docs/application-journey-completion.md)；Supabase 套用步驟見 [`docs/supabase-rollout-runbook.md`](docs/supabase-rollout-runbook.md)。下方的測試基線數字是先前紀錄，目前工作樹的實際結果以該文件為準。

目前 Web 候選為 `2026-08-31-pre-review.129`，決定仍為 `NOT READY`。B5-05 已加入「申請規定錯誤回報」：只有已登入且完成學生身分驗證的帳號能針對目前流程或步驟提交官方 HTTPS 來源，後端會重新載入並綁定目前 workflow ID、版本與內容快照；管理者只能將案件標為成立或不成立，不能由回報直接建立 revision、核准或發布正式規定。Web 對結果不明的提交會跨重新整理保留同一 mutation ID 與帳號範圍內的待重試內容，並以 timeout、精確 2xx payload 驗證、管理員請求競態防護及關閉後 DOM 清除維持 fail closed。C-01 的風險優先雙審批次會在整份 rows 組裝後重算內容指紋；DATA-003 的單一來源證據 CSV 另以來源 URL 身分（僅 scheme／host 不分大小寫，path／query 精確區分）、有效 workflow 內容、目前查核時間、pending revision 身分、schema 版本及完整研究候選建立專用複合快照。舊工作台或產生期間內容變更時 API 回 409，不交付混合 CSV。

目前 frozen 測試基線為 804 項非 E2E＋49 項 Chromium E2E，分開執行合計 853 passed、0 failed；非 E2E 耗時 412.66 秒，E2E 耗時 456.41 秒。OpenAPI contract 為 `2026-08-31.2`；固定版 `pglast 8.4` 已解析 21 份 migration 的 471 個 statements、11 個 SQL function bodies 與 51 個 PL/pgSQL units，最新 `20260830100000_application_workflow_issue_reports.sql` 為 29／0／4。frozen environment 仍解析 88 個 package，dependency audit 回報 0 個已知漏洞。

本輪隔離 runtime 已在 pinned PostgreSQL 17.6、兩個 PostgREST 14.12 與 Storage API 1.60.4 上從零套用 21／21 migrations，驗證 32／32 張 `exchange_*` table 啟用 RLS、0 browser grants、3 個 workflow issue service-role-only RPC，以及回報提交／審核競態、限流、URL 防護、刪帳去識別、90 天／24 小時保留、purge、Storage 與既有社群 rollback。最終必要執行回傳 `status=passed`、`cleanup_status=passed`，其後查驗 runtime container／network／volume 均為 0；正式 Supabase 專案、既有資料升級路徑、實際正式 Storage backend 與遠端 CI 仍待驗。DATA-010 的 13 筆來源候選與 22 個去重網址封裝基線未改變；但 2026-08-31 本次 live recheck 因立教大學 2 個 URL 連線逾時、DATA-003 因長庚 1 個 URL 讀取逾時而各以 exit 1 fail closed，不能宣稱兩套即時來源稽核已通過。候選、正式資料、產品 AI 的 Advisor／RAG／文件／Web 串接與 Flutter 核准狀態都沒有因此改變。

正式唯讀稽核結果未改變：280 workflows、0 published；生活情報 137 verified／143 pending destination profiles、470 pending sources；共 9 類 blockers，CLI exit code 2。三個 fingerprint 維持總指紋 `6c88731481993e0bcf3da9627153db86731a13403605607478fba4f9cb9df49d`、申請流程子指紋 `e72b8c4a35ae34294ad497af9988d740e9f4236caaa9fe3396dbe32f4af4d57c`、生活情報子指紋 `d73804f1ec16ddc7e61e71fc8a199a021b285cd2a7a658e9ec9186077b070011`。

## 專案結構

```text
src/exchange_info/
  crawler.py       # requests/BeautifulSoup crawler, optional Playwright rendering
  cleaner.py       # 去選單、頁尾、重複文字
  classifier.py    # rule-based 分類
  extractor.py     # rule-based 結構化欄位抽取
  student_view.py  # 學生查詢 dashboard 與補助要點整理
  ntpu_student_view.py # 臺北大學官方名額表解析與學生版資訊
  university_registry.py # 支援學校與別名、視覺、驗證訊號設定
  experience_collector.py # 公開學生心得與影片搜尋、去重、主題整理
  content_summary.py # 實際讀取來源正文、產生中文摘要與清理模型格式文字
  application_workflow_collector.py # 合作校官方申請流程查核與步驟整理
  workflow_issue_reports.py # 已驗證學生的流程錯誤回報、冪等重試與管理員處置 repository
  submission_progress.py # 五種送件方式的學生手動狀態機與收件證明 metadata
  partner_research.py # 合作校官網辨識與官方生活資訊查核
  application_documents.py # 個人化文件清單、欄位驗證與列印 PDF 產生器
  document_vault.py # AES-256-GCM 私人文件庫、逐檔同意、版本、下載與永久刪除
  models.py        # pydantic schema
  api.py           # FastAPI app
  cli.py           # CLI
data/
  raw/pages.jsonl          # 原始頁面資料
  raw_files/               # PDF/doc/docx/ppt/pptx 附件與官方規章 PDF
  processed/pages.jsonl    # 清洗與分類後頁面
  processed/exchange_info.json
  processed/student_experiences.jsonl
  processed/application_workflows.jsonl
  processed/partner_research.jsonl
  processed/destination_profiles.jsonl
  processed/collection_audits.jsonl
  processed/community_questions.jsonl
  processed/community_answers.jsonl
  processed/experience_submissions.jsonl
  processed/user_accounts.jsonl
  processed/account_sessions.jsonl
tests/
ios/ExchangeGuide/       # 原生 SwiftUI iOS App 與 XcodeGen 專案設定
docs/design/
  apple-design-system.md # Web/iOS 共用設計 token、46 個元件與無障礙規格
```

## 安裝

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

如果要啟用 Playwright 動態渲染 fallback，再安裝 Chromium：

```powershell
python -m playwright install chromium
```

## 執行爬蟲

預設從長庚國際處首頁開始，只保留 `cgu.edu.tw` 網域內、與國際處/交換/出國/研修/補助/心得/FAQ/可申請學校/說明會/申請公告相關的頁面。

```powershell
exchange-info crawl --max-pages 60 --rate-limit 1.5
```

使用 Playwright：

```powershell
exchange-info crawl --max-pages 60 --rate-limit 1.5 --use-playwright
```

重新用既有 raw data 建立 processed data：

```powershell
exchange-info build-index
```

`crawl` 與 `build-index` 也會增量更新 `structured_sources.jsonl` 與 RAG 文件分段索引。目前產品 AI runtime 仍由程式固定為 `paused`；即使設定 `AI_PROVIDER` 或 `OPENAI_API_KEY`，也只執行規則式整理與無 embedding 的關鍵字索引，不會呼叫外部或本地模型。LAI-00～LAI-03 已另建立 development-only、loopback-only 的 Ollama provider 基礎，但尚未接入 `get_provider()`、Advisor、RAG 或 Web；安裝與 provider-only 檢查方式見 [`docs/local-ai-runbook.md`](docs/local-ai-runbook.md)。`--rules-only` 保留為明確相容選項；`build-ai-index` 在本階段同樣只重建規則式來源與文件分段索引：

```powershell
exchange-info build-ai-index
```

蒐集合作學校的公開學生心得、社群討論與影片：

```powershell
exchange-info collect-experiences --school "林肯大學 Lincoln University" --max-sources 12 --school-delay 1.5
```

省略 `--school` 時會依合作學校清單增量蒐集，已完成或已確認無可靠結果的學校會自動略過；可用 `--max-schools` 控制批次大小、`--school-delay` 控制校際等待時間，或用 `--refresh` 重新查核。蒐集器只保存標題、短摘要、主題、來源類型、公開 URL、查核時間、雜湊，以及來源平台有提供時的公開作者／頻道名稱；不保存私人聯絡資料、不下載影片，也不大量複製文章原文。每次結果會寫入 `collection_audits.jsonl`，區分已找到、已搜尋但無結果與搜尋失敗。

查核合作學校的詳細官方申請流程：

```powershell
exchange-info collect-workflows --school "林肯大學 Lincoln University" --school-delay 1.5
```

流程蒐集只接受所選母校國際處與合作校官方網域，整理校內申請、提名、合作校線上申請、必要文件、錄取、選課、簽證、保險、住宿及返國結案。新結果只會寫入 `application_workflow_revisions.jsonl` 的待審版本，不會直接覆蓋學生看到的正式流程；必須由兩個不同內容管理者分別載入版本對照、親自開啟並勾選候選版全部官方來源，再逐項核對流程適用範圍、每個步驟與每份文件並留下核准說明，之後才允許正式發布。每條規定會在工作台同列顯示其直接來源；缺來源、來源引用沒有名稱／角色／權威層級等證據資料、適用年度缺漏或不一致，或含非 HTTPS 來源時，前後端都會鎖住核准與發布。內容管理者可在 pending revision 中逐頁確認後替來源引用建立證據資料，或填入親自核實的 HTTPS 替代頁；系統會同步更新步驟、期限、表單、文件與送件入口的相同引用，中繼資料一致的多個舊入口可明確合併，有衝突則拒絕。每份核准會保存候選內容雜湊，以及該審查者確認的完整來源與關鍵規定清單，並以實際核准時間更新流程、來源與步驟的最後查核日期；內容變更、來源或規定缺漏、未知項目或舊格式核准都會阻止發布。每所學校依「母校＋合作校＋學年度＋梯次」分開保存，避免不同學校或梯次互相覆蓋。官方頁未公開、無法讀取或日期互相衝突時，系統會標示「需確認」，不自行補造規定或網址。

申請流程一旦有兩個以上曾完成完整雙審的發布快照，管理者可在同一工作台查看逐版稽核歷程，並選擇舊版執行安全復原。復原要求目前 revision ID、版號、內容指紋及恢復目標全部相符，且不得與 pending revision 並存；成功時會建立更高版號的 `rollback` revision，保留撤回版、恢復目標、操作者、時間、原因及原雙審證據，不覆寫或刪除任何舊版。發布閘門會把一般發布／復原動作、基準版、撤回版、恢復目標、理由與雙審證據納入快照指紋，逐流程核對目前公開 payload 與完整歷程；任一參照缺失、跨流程、重複或內容不一致都會 fail closed。復原後受影響且已建立申請計畫的學生會依通知偏好收到規定變更通知；後續修改仍須重新雙審。

完整執行臺北大學合作校的可續跑查核批次：

```powershell
exchange-info research-partners --home-school "國立臺北大學" --max-schools 5 --max-sources 12 --school-delay 1.5
```

內容管理者或 CI 可用唯讀 Web 總發布稽核，同時核對申請流程的來源、期限、雙審與發布／復原鏈，以及生活情報的查核狀態、審查／升級／復原鏈。輸出為 JSON；兩個資料面全部檢查通過時 exit code 才為 `0`，任一面仍有阻擋時為 `2`，任一目錄為空也會 fail closed：

```powershell
exchange-info --data-dir data audit-web-release
```

每校會依序查核官方網域、校園照片、母校與合作校申請流程、官方住宿／生活費／交通／校園生活頁，以及公開學生心得。找到連結後會實際讀取頁面正文，為每個來源產生學生可直接閱讀的中文摘要；無法取得全文時只保留來源並明確標示，不把搜尋片段冒充摘要。省略 `--school` 時會從尚未完成五個階段的學校繼續；`--refresh` 可重新查核。校園照片必須通過來源與影像驗證才計入完成，官網低信心候選會保留為 `needs_review`，搜尋過但沒有可靠結果會記為 `not_found`。

臺北大學 203 所合作校的完整資料會匯出到 `src/exchange_info/official_data/ntpu/`，並與已驗證校園圖片一起納入 Git 版本控制。因此從 GitHub 複製到另一臺 Windows 或 Mac 後，即使當地尚未建立 `data/processed/`，API 仍會自動讀取這份基準資料。重新查核及匯出時使用：

```powershell
$env:PYTHONPATH='src'
python scripts/refresh_ntpu_catalog.py --workers 6 --max-pages 3 --timeout 12
python scripts/refresh_ntpu_images.py
python scripts/export_ntpu_catalog.py
```

`export_ntpu_catalog.py` 會同時產生 `catalog-completeness.json`。交付前應確認合作校、官網、必要詳細欄位、圖片、申請流程與目的地資料的數量全部都是 203。

舊版曾把流程學年度批次複製到每一個來源。這些值沒有逐頁雙審證據，不可繼續當作來源適用年度。先以 dry-run 檢查，再明確套用清理；正式雙審發布過的 workflow 不會被清除：

```powershell
python scripts/clear_derived_source_applicability.py
python scripts/clear_derived_source_applicability.py --apply
```

清理後，來源年度只能由內容管理者在 `/admin/content-review` 親自逐頁核對並保存修正紀錄；流程學年度不會自動回填來源。若步驟、期限、表單或文件已引用官方網址但尚未建立來源證據資料，工作台會要求真人補上來源名稱、角色、權威層級與適用年度，不能只靠網址通過核准。工作台另將相同缺口網址分組，顯示受影響流程與關鍵規定數，並在每個來源下列出它支援的步驟、期限、表單及文件；每組可下載只供內容管理者使用的 UTF-8 CSV，逐流程列出年度、梯次、規定鍵、規定名稱與精確引用脈絡。匯出採 `no-store`、試算表公式防護並保留人工查核空欄，但不能匯入、建立修正、核准或發布。工作台頂部以 Web 總發布規則即時計算 `READY`／`NOT READY`：除了未發布流程、學年度、精確期限、來源證據、來源年度、查核日、HTTPS、待確認規定、雙審證據與申請流程發布歷程完整性，也把全部生活情報的完整查核／明確雙審升級狀態及其審查、升級、復原鏈納入；總指紋由申請流程與生活情報兩個子指紋組成，任一資料面改變都會更新。生活情報工作台可在長庚大學與國立臺北大學間切換，各自載入審查 queue、snapshot-bound CSV 與公開／復原歷程；切換時會清除上一校的搜尋條件，較舊的非同步回應也不能覆蓋目前學校。這仍不能取代真人雙審。內容管理者也可下載申請流程雙人審查分工 CSV：表內保存申請流程子指紋與獨立的審查內容指紋，後者只在候選／公開內容或待審成員真正改變時更新，因此建立待審版本或增加核准進度不會讓整批連結失效。分工表預設依資料風險排序，每 10 個 workflow 一批，保留審查者 A／B、查核時間、問題與決定空欄，以及可精確聚焦單一 workflow 或直接顯示整批 10 筆的工作台連結；進入批次後可另下載逐規定查核表，逐列呈現流程適用範圍、每個步驟與每份文件的規定內容、官方來源與證據／年度／查核日／HTTPS 缺口，A、B 欄預設空白。連結會把審查內容指紋交給後端再次核對；候選內容被修改或發布使批次成員改變時，舊連結不套用定位並要求重新下載。兩種分工表都不能匯入、修改流程或形成核准。

生活情報也有獨立的雙人分工批次：目前長庚 58 筆待審分成 6 批、臺北大學 85 筆分成 9 批，預設每批 10 筆。批次 CSV 保存母校、完整來源、缺口、位置、人工 A／B 空欄及可直接開啟該批的工作台路徑；進入批次後可下載逐項查核表，每個 profile 固定列出 12 個內容區塊，並為每個官方來源另列一項。全體待審對應 1,716 個區塊與 470 個來源，共 2,186 個查核項目。工作台另可只看「我的待辦」或「我已留下結論」；尚未送出的勾選、結論與說明以目前管理者 ID 及 profile 內容指紋隔離，只暫存在該瀏覽器分頁工作階段，重新整理可恢復，手動清除或成功送出後刪除。這份暫存不會同步、不會寫入後端，也不是審查證據；內容指紋改變後不會沿用。新增審查進度不改變批次 ID 或成員，profile 內容、待審成員、升級或復原造成實質清單改變時，後端以審查內容指紋拒絕舊連結。所有 CSV 均採 `no-store`／`nosniff`、公式防護及空白 A／B 欄，不能匯入、修改資料、核准、升級或發布。

生活情報的第一份或第二份真人審查只增加進度，不會讓有效批次換批；明確升級或復原會改變待審成員並使原批次過期。工作台完成任何審查、升級或復原後都會立即重新驗證批次；若批次已過期，成功結果與「舊定位未套用、須重新下載目前版本」會在同一則訊息顯示，逐項表入口同步隱藏。重新驗證暫時失敗時也不沿用舊成員，避免審查者只看見操作成功而誤以為原分工仍有效。

有效生活情報批次中的個人未審項目另提供「保存並前往下一筆我的待辦」。審查成功且批次仍有效時，工作台會清除搜尋、切到「我的待辦」，依原分工批次的固定順序開啟並聚焦下一筆；若目前帳號已沒有未審項目，畫面只宣告「我的待辦」完成，並明示這不代表另一位審查者、雙審、升級或發布完成。一般保存、過期批次及載入錯誤不會使用這條捷徑，仍遵守既有批次重驗與 fail-closed 邊界。

剛進入有效生活情報批次時，批次摘要會直接顯示目前帳號的待辦數，並提供「開啟第一筆我的待辦」；之後可依固定批次順序開啟下一筆，或把全部個人待辦重新收合成批次清單。每次開啟都會切回「我的待辦」、清除搜尋、展開正確 profile 並把鍵盤焦點放到審查摘要；手動展開批次中的任一張卡也會成為下一筆導覽的起點。待辦為零時按鈕只顯示完成狀態且不可操作，不代表雙審、升級或發布完成。

生活情報審查表會在送出前直接套用後端核可門檻：缺少官方來源、含非 HTTPS 官方網址或缺少最後查核時間時，卡片逐條顯示阻擋原因，結論固定為「內容需要修正」，並停用「內容可交下一步處理」。即使前端 DOM 被竄改成核可，送出函式仍會重新依 queue 的缺口代碼拒絕並重設結論；後端相同規則保留為最終防線。沒有這三種結構阻擋時只顯示「可選擇核可」，仍必須由本人逐頁核對全部來源與 12 個內容區塊，不能把綠色提示視為已核可。

生活情報工具列可再依「可選擇核可／只能要求修正」篩選，批次摘要同時顯示兩類結構數量與未受門檻篩選影響的完整個人待辦數。第一筆／下一筆及保存後續接只在目前門檻篩選內前進；如果目前門檻沒有待辦但其他門檻仍有，按鈕停用並明示是「目前門檻篩選沒有我的待辦」，不會冒充整批完成。切換母校會清除門檻篩選，避免上一校條件套到新 queue。

每張生活情報審查卡會即時計算目前分頁已勾選的官方來源與 12 個內容區塊，並顯示下一個仍未核對的項目。「前往下一個未核對項目」只會把鍵盤焦點移到第一個未勾選項目，不會代替真人開啟來源、勾選、保存或形成審查證據；重新整理恢復分頁草稿及手動清除時，計數也會從實際勾選重新計算。全部可核對項目完成後只提示可填結論與說明，上方結構阻擋仍然有效。

生活情報卡的即時門檻也會計算審查說明去除首尾空白後的字數。全部來源、12 個區塊及至少 10 字說明完成前，「保存我的獨立審查」與「保存並前往下一筆」都保持停用；勾選完成但說明不足時，導覽按鈕會改為「前往審查說明」並把焦點移到 textarea。達成門檻只開放送出操作，後端仍會重新驗證內容指紋、完整來源、區塊、說明及核可阻擋。

申請流程雙審表同樣支援安全續接：載入版本對照後，尚未送出的官方來源勾選、關鍵規定勾選與查核說明會以管理者 ID、revision ID 及完整內容雜湊隔離在目前瀏覽器分頁工作階段。重新整理後回到待審版本並重新載入對照即可恢復；手動清除只重設本頁表單，核准、退回或發布成功後才移除暫存，後端拒絕時保留。暫存不會同步、建立核准或參與發布就緒判定；候選內容變更後必須重新逐項核對。從 backlog 開啟既有待審版時，URL 只保存 `review_status=pending_review` 與 `workflow_revision` 定位，不包含表單內容或權限；重新整理會回到同一 revision，已處置的定位不會套到其他版本。整批建立 pending revision 後，可直接進入只顯示該批的「我的待辦」，再開啟第一筆、切到下一筆或返回同批次清單；單筆模式會同時保存 batch 與 `workflow_revision` 定位。批次與待審工具列另區分「可開始真人核對」與「須先補資料」；每張卡頂部逐條列出來源、HTTPS、規定來源、年度／梯次及來源證據缺口，並可直接展開同卡補正區。補正編輯器會即時顯示本次已選來源 X／N、下一個缺少欄位與是否可儲存；只驗證本次勾選的來源，未勾選來源保持不變，因此可分次補正。流程學年度／梯次沒有實質變更且未選來源，或已選來源缺少年度、必要證據資料或 HTTPS 替代網址時，儲存維持停用。這只導引真人逐頁查證，不會自動填值、批次代填或形成核准。重新整理會重新驗證受保護批次 API；過期或不存在時，批次與單筆定位會一起失效，舊範圍不套用。清除批次定位後回到完整 pending queue。待審清單仍可依目前帳號篩選「我的待辦」、「我已核准」與「可由我發布」，摘要數字同步反映目前視角。

申請流程的獨立核准卡會把全部官方來源、全部關鍵規定與去除空白後的查核說明合成同一個即時門檻。資料門檻或版本對照尚未完成時，既有阻擋優先；可開始核對後，「下一個未完成核准項目」依來源、規定、說明的順序移動焦點。說明只填空白仍視為未填寫，全部條件完成前核准按鈕維持停用；達成門檻只開放送出，後端仍會重新驗證候選內容雜湊與完整核對清單。

有效的申請流程分工批次另提供「核准並前往下一筆我的待辦」。它與一般核准共用同一組來源、規定、說明及後端驗證門檻；送出時兩個核准按鈕同步鎖定。核准成功後，Web 會先重新驗證原本的 snapshot-bound 批次，再依分工清單順序開啟下一筆並移動鍵盤焦點。批次過期、重新載入失敗或目前資料門檻篩選沒有下一筆時不會跳出安全範圍；完成目前帳號待辦也不代表另一位審查者、雙審或發布完成。

人工資料補正也有獨立的同分頁草稿：流程學年度／梯次、修正說明、逐來源勾選、來源年度／梯次、缺少的來源名稱／角色／權威層級及 HTTPS 替代網址，會按管理者 ID、revision ID 與完整候選內容雜湊保存在 `sessionStorage`。重新整理同一待審版本時會自動展開補正區並恢復；讀回只接受目前已知且不重複的來源 URL、受長度限制的字串及允許的角色／權威值。換管理者或候選內容改版後不會沿用。畫面明示草稿尚未送到後端且不是核准證據；手動清除只還原目前候選值，補正儲存、核准、退回或發布成功後清除，後端拒絕或網路錯誤時保留。草稿不會修改 revision、核准數、查核日、學生資料或發布就緒狀態。

補正區的每個來源會即時標示「本次未選取」、「尚缺來源年度／HTTPS 替代網址／證據欄位」或「本次補正欄位完成」。上方「前往下一個缺少欄位」會依驗證順序把鍵盤焦點移到流程年度、修正說明或第一個未完成來源欄位；全部完成後才隱藏。這項導覽不會自動勾選、填值、儲存或核准。非 HTTPS 來源即使尚未建立 top-level 證據資料，也會提供必要的安全替代網址欄，仍須真人確認相同官方內容後才能保存。

若管理者從 snapshot-bound 批次的單筆頁儲存候選補正，工作台會立即以原 `review_snapshot` 重新驗證批次。候選內容改變會更新審查內容指紋，因此舊批次以 409 失效、`workflow_revision` 單筆定位立即清除，第一筆／下一筆與返回批次導覽停用；管理者必須清除過期批次並重新下載目前分工清單。若重新驗證本身失敗，畫面同樣 fail closed 停用舊導覽，不會把未知範圍當成仍有效。修正仍只存在 pending revision，不會提前改變學生公開資料。

workflow 已建立 pending revision 後，管理者 backlog、來源證據群組、批次分工及逐規定查核表都以最新候選版重算，不會繼續顯示舊公開版缺口；學生 API 仍只讀正式發布版。backlog 與分工 CSV 同時顯示每筆實際核准數與所需人數，工作台可篩選待第一位、待第二位及已達雙審門檻，讓 28 批審查可以中途恢復與交接。

在 Mac 更新專案時，先執行 `git pull --ff-only`；完成開發並通過測試後，再依序執行 `git add`、`git commit` 與 `git push`。不要把同一份專案放在 OneDrive、iCloud Drive 等同步資料夾內，以免建置產物造成路徑過長或檔案同步衝突。

## 啟動 API

```powershell
uvicorn exchange_info.api:app --reload
```

預設服務位置：

```text
http://127.0.0.1:8000
```

前端頁面：

- `http://127.0.0.1:8000/`

前端會依裝置切換操作方式：桌面版使用固定側邊導覽、多欄摘要與合作學校表格；手機版使用底部導覽、44px 以上觸控區及漸進式揭露。首次進入可選擇目前就讀學校，也可略過後先看長庚資料。首頁以找學校、截止日期、補助與資格初判為主要任務，並提供最近三個可辨識期限、依學生資料計算的基本篩選結果與文件準備清單。訪客比較與公開條件篩選只留在當次分頁；收藏、申請計畫、文件狀態、學校申請進度及個人日曆須登入後才建立及同步。官方文件預設只顯示摘要，展開後才顯示完整重點與來源連結。

「我的計畫」會依學生填寫的學院、學系、學制、成績、語言成績、申請學年度、梯次與志願序，從結構化官方規則產生各志願的資格檢查與個人下一步。公開搜尋與比較不需登入；按下建立個人清單時才要求登入並同步志願與進度。未標示為已發布或尚缺欄位的流程不會被猜成確定規定，而會轉成「向國際事務處／所屬系所確認」任務。獨立的交換預算頁可估算學費、住宿、生活費、交通、保險與簽證，並保留官方生活費來源；文件庫可逐項標記為待準備、準備中或已完成，補助頁則會依個人條件標示優先查看項目。

登入後可在申請日曆啟用私人訂閱網址，讓 Google Calendar、Apple Calendar 或 Outlook 訂閱系統中的申請期限與自訂任務。這是由系統單向同步至第三方日曆的訂閱機制；正式部署需把 `EXCHANGE_PUBLIC_BASE_URL` 設為可由外部日曆服務讀取的公開 HTTPS 網址，本機 `127.0.0.1` 僅供介面與流程預覽。

點擊合作學校會進入完整頁面，查看限制條件、語言門檻、名額、學費、截止日、逐步申請流程、官方住宿與生活費參考，以及公開學生文章、影片、社群討論與跨來源優缺點。官方表格的 69 筆合作紀錄會合併成 62 間不重複學校；同校的交換、雙學位或不同學院方案會在校內分開顯示。桌面版預設展開前兩個流程步驟，手機版展開第一步，其餘保留可掃描的步驟標題。資格初判僅依公開的校內基本門檻提供篩選結果，不代表正式錄取或校方認定。

網頁另有固定的公共留學板、語言學校板，以及每所支援大學的交換板。所有人都能公開閱讀；一般帳號完成 Email 驗證後可在兩個公共板發文與留言，只有完成學生身分驗證者才能在本人學校的交換板發言。每次發文或留言都能選匿名、公開暱稱、本名或已驗證校籍（依實際驗證狀態開放）。API 會拒絕 Email、電話與常見社群帳號格式，並提供風險式審核、檢舉、封鎖及邀請制私訊。合作校頁面保留既有校友問答，但不再建立任意的新貼文板。

網頁預設使用淺色 Apple 風格語義色彩、圖片導向的首頁與半透明玻璃材質，可由頂部按鈕切換深色模式。完整跨平台設計規格位於 `docs/design/apple-design-system.md`，包含深淺色 token、Dynamic Type、12 欄網格、8px 間距、互動狀態與 46 個原生元件的 accessibility 規格。

本次首頁與社群照片來源及授權連結整理在 `docs/image-credits.md`。

### 申請文件工作台

網頁的「申請文件」是一個獨立工作區。學生先選擇交換計畫、目標學校、學年度、學期及補助等條件，再建立一次共用個人資料；系統只顯示該身分需要的文件，重複欄位會自動帶入。每份文件都有獨立填寫頁，支援必填、Email、數字、日期先後、附件與照片數量檢查，也會列出預設列印份數、送件單位、親簽及核章對象。

「當期文件與官方表格」會依本校、志願學校、學系、學位、學年度與梯次顯示來源、份數、正影本、簽名、核章及附件順序。只有經人工發布且附有明確 HTTPS 校方表格網址的項目可直接下載；舊年度、未標示年度或尚待查核的資料一律顯示「待確認」，不會被當成目前正式版本。下方「可填寫的準備工具」只是整理草稿與列印，不代表當期校方必備文件。

目前涵蓋校內申請資料、家長同意書、讀書計畫（中文與選填英文版）、初審同意聲明、課程預選及學分規劃、雙聯學籍、出國切結、役男文件、出國前通知、補助收據、行政契約、抵達報到、海外學期報告、返國成果及學分採認。境外短期學分課程的 `2B0001001` 至 `2B0001004` 會優先套入長庚公開的正式 DOCX 版面；校方尚未公開正式檔案的項目會清楚標示為「資料整理列印版」，不可冒充正式表格。

產生 PDF 前會先顯示逐欄只讀預覽，包含實際填入值、留白欄位、份數、單雙面、附件順序、送件單位、簽名及核章位置；缺少或不確定的欄位會明確顯示「留白（不會猜測）」。學生完成「我已核對」後，系統才會開放目前內容的 PDF；後端以由文件庫主金鑰分離出的 HMAC-SHA256 token 綁定表單版本、申請脈絡、內容、附件與份數，任何一項改動都會使核對失效並要求重新確認。

產生「整包 PDF」時，封面會逐份列出份數、紙張、單雙面、交件位置、簽名、核章及實際附件順序；附件包含檔名與 PDF 頁數，後續頁面依設定重複排入。附件中的 PDF 會照順序接在對應文件後方，成果照片則標示為排入文件內。損壞、偽裝格式、超過數量或無法讀取的附件會在預覽時明確阻止核對與產生，不會被靜默略過。學生自行列印與送件，系統不會連線至校方申請系統，也不會自動送出。每份文件可追蹤「待列印、待簽名、待系所核章、待送件、已完成」，並提示下一位應聯絡或簽核的人。

合作校詳細流程中的每一個已確認送件步驟，都可登入後記錄「尚未開始、準備中、已由我送出、我已記錄收件、我已標記完成」。紙本與混合流程會同時顯示最晚寄出與必須送達時間；若官方未提供送達期限，固定顯示「待確認」，而且不能只以寄出日標記完成。線上、Email 與親送若沒有回條，可由學生明確選擇手動完成。收件證明只保存種類、參考編號、可選檔名／內容類型及由伺服器產生的記錄時間，原檔不會進入一般工作區；狀態固定標示為學生自行回報，平台不會宣稱代送或取得校方正式收件結果。所有轉換可逐步撤銷，並透過帳號工作區跨裝置同步。

未登入時，個人資料與表單草稿只保留在瀏覽器分頁的工作階段，附件只留在記憶體。登入後，一般且非敏感的表單欄位會以 AES-256-GCM 加密同步，讓學生能跨裝置繼續；護照、證件號碼及所有原始附件都不會因登入而自動保存，也不會被塞入一般工作區 JSON。學生若要跨裝置保存單一附件，必須逐檔選擇用途與保存期限並明確勾選同意；保存同意不包含公開分享、社群引用或 AI 訓練。畫面可逐檔載入、撤回／永久刪除，期限到期後由文件庫清理。後端只在請求期間產生 PDF，回應帶有總頁數、文件數、列印總份數、附件數與 `request-only` 保存標記，回傳後不會自動保存；下載完成對話框也會再次提醒此邊界，如要保存產生檔仍須在私人文件庫另外同意。Windows 有 Microsoft Word 時可將官方 DOCX 精準轉成 PDF；Linux 正式環境應另配置 LibreOffice 或文件轉檔服務。

## 帳號與第三方登入

Email 建立帳號採兩階段流程：先取得六位數驗證碼，再用一次性 token 建立一般帳號。驗證碼 15 分鐘有效、重送至少間隔 60 秒、每小時最多五次，錯誤五次即失效；持久層只保存 Email 的 HMAC 指紋、驗證碼雜湊及 token 雜湊，不保存明碼。建立帳號後才可選擇上傳學生證正反面升級校籍權限；驗證 token 綁定當時登入帳號，不能轉交另一個帳號使用。原圖只在當次請求記憶體處理，帳號只保存學校、卡面可明確辨識的系所、驗證方式、狀態與時間，不保存照片、完整學號、姓名或 OCR 全文。密碼只在後端以 PBKDF2 雜湊儲存，登入狀態同時支援 HttpOnly Cookie 與 API Bearer Token。

Google Workspace、Microsoft Entra、校方 SSO 與校方 Email OTP 採學校別 provider policy；未完成校方合作或後端設定時預設停用，不得退回讓學生在本平台輸入校務密碼。兩校帳號生命週期、開放狀態、官方來源與 Entra 設定方式見 [`docs/student-verification-provider-matrix.md`](docs/student-verification-provider-matrix.md)。

登入後，收藏、單一／多個申請計畫、文件準備狀態、期限與完成狀態會同步到帳號工作區；未登入時的比較不會被默認匯入收藏。每次寫入都帶版本號；舊裝置若送出過期版本，API 會回傳最新版，Web 合併兩端的非敏感進度後再重試。離線修改會放入該帳號專屬的待同步佇列，網路恢復時重送；同一瀏覽器切換帳號時不會沿用前一個帳號的佇列。工作區 API 採欄位白名單並拒絕未知根欄位，個人表單答案、護照／成績單等敏感資料與附件不會因工作區同步而被隱性保存。帳號 session 一旦建立成功，登入對話框會先關閉；社群身分、看板、權益、工作區、日曆、通知與表單草稿再各自同步，單一非關鍵載入失敗不會把成功登入誤報為失敗，畫面會保留 session 並提示稍後重試。

本機開發預設使用 `development` Email backend，驗證碼只會回傳到本機 Web 畫面，不寫入 log。正式環境必須設定固定的 32-byte secret 並選用 SMTP；development backend 在 production 會拒絕啟動：

```powershell
$secret = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($secret)
$env:EXCHANGE_EMAIL_VERIFICATION_SECRET=([Convert]::ToBase64String($secret).TrimEnd('=').Replace('+','-').Replace('/','_'))
$env:EXCHANGE_EMAIL_VERIFICATION_BACKEND='smtp'
$env:EXCHANGE_SMTP_HOST='smtp.example.com'
$env:EXCHANGE_SMTP_PORT='587'
$env:EXCHANGE_SMTP_FROM='no-reply@example.com'
$env:EXCHANGE_SMTP_USERNAME='後端 SMTP 帳號'
$env:EXCHANGE_SMTP_PASSWORD='後端 SMTP 密碼'
$env:EXCHANGE_SMTP_STARTTLS='1'
```

2026-10-03 起，兩校官方資料不需登入即可瀏覽，帳號只開放 Google：`EXCHANGE_AUTH_METHODS` 預設 `google`（Email 註冊與登入、Facebook 都關閉）；本機要用 Email 登入可設成 `email,google`。Google 已驗證信箱的網域是 `cgu.edu.tw` 或 `ntpu.edu.tw` 時自動帶入學校，其他信箱登入後再選；這兩種都不算驗證在學，學校板發文仍須驗證學生身分。所有討論板（含兩校板）的發文、留言與按讚只需 email 已驗證的帳號，用校名署名仍須驗證在學身分；功能全部免費。上線前清單見 [`docs/launch-plan-2026-10-03.md`](docs/launch-plan-2026-10-03.md)。

網站內建匿名使用統計（不用 cookie、不存 IP 與個資），管理員打開 `/admin/analytics` 看儀表板，也可用 `exchange-info analytics-report` 或匯出 CSV；`EXCHANGE_ANALYTICS=off` 可關閉。蒐集項目、指標定義與隱私說明見 [`docs/analytics.md`](docs/analytics.md)。

學校頁的「出發前提醒」分頁提供各國的共通提醒（中國大陸、日本、韓國、法國、美國有較完整的內容），「學生心得」分頁的心得附有繁體中文整理；兩者都是隨程式發布的離線資料，每項附來源，預設為待審核草稿，心得是整理而不是全文翻譯。維護方式見 [`docs/country-tips-and-experience-digests.md`](docs/country-tips-and-experience-digests.md)。

Google 與 Facebook 登入按鈕已完成 OAuth 流程，但需要先在各平台建立應用程式並設定環境變數；未設定時按鈕會顯示為暫不可用（Facebook 另需把 `facebook` 加進 `EXCHANGE_AUTH_METHODS` 才會啟用）：

```powershell
$env:EXCHANGE_PUBLIC_BASE_URL='http://127.0.0.1:8000'
$env:GOOGLE_OAUTH_CLIENT_ID='你的 Google Client ID'
$env:GOOGLE_OAUTH_CLIENT_SECRET='你的 Google Client Secret'
$env:FACEBOOK_APP_ID='你的 Facebook App ID'
$env:FACEBOOK_APP_SECRET='你的 Facebook App Secret'
uvicorn exchange_info.api:app --reload
```

開發環境的 callback URL 分別是 `http://127.0.0.1:8000/auth/oauth/google/callback` 與 `http://127.0.0.1:8000/auth/oauth/facebook/callback`。正式部署必須改用 HTTPS 並設定 `EXCHANGE_ENVIRONMENT=production`；production 會無條件強制登入與 OAuth flow Cookie 使用 `Secure`，即使 `EXCHANGE_AUTH_SECURE_COOKIE` 缺漏或設為 false 也不降級。development／preview 若在 HTTPS 下驗證 Cookie，可設定 `EXCHANGE_AUTH_SECURE_COOKIE=true`，亦接受 `1`、`yes`、`on`。Apple 登入會等 App 上架需要時再接 Apple Developer 設定。

## 啟動原生 iOS App

iOS 端使用 SwiftUI，最低支援 iOS 17。請在安裝 Xcode 26 與 XcodeGen 的 macOS 執行：

```bash
cd ios/ExchangeGuide
xcodegen generate
open ExchangeGuide.xcodeproj
```

iOS Simulator 預設讀取 `http://127.0.0.1:8000`。實機測試時，在 Xcode Scheme 的 Launch Environment Variables 設定 `EXCHANGE_API_BASE_URL` 為執行 FastAPI 的 Mac 區網網址；正式上架必須改用 HTTPS。App 已實作淺色玻璃感首頁、圓形資料圖、找學校、學校限制、詳細流程、具體生活情報、公開學生心得、匿名社群、截止日、補助文件摘要與資格初判，並依裝置寬度在 iPhone Tab Bar 與 iPad Sidebar 間切換。iOS 26 使用原生 Liquid Glass；iOS 17-25 使用系統材質 fallback。

## 啟動原生 Android App

Android 端使用 Kotlin、Jetpack Compose 與 Material 3。用 Android Studio 開啟 `android/ExchangeGuideAndroid`，啟動本機 FastAPI 後即可執行 `app`。Android 模擬器預設透過 `http://10.0.2.2:8000` 連線到後端；實機測試需將 `app/build.gradle.kts` 的 `API_BASE_URL` 改為同一個 Wi-Fi 內的電腦 IP，正式版本則必須使用 HTTPS。

Android App 保留 iOS 版的核心資訊與社群流程，並依平台改用手機 Bottom Navigation、平板 Navigation Rail、淺色磨砂卡片與 48dp 最小觸控區。完整執行與建置說明位於 `android/ExchangeGuideAndroid/README.md`。

API:

- `GET /health`
- `GET /sources`
- `GET /exchange-info?school=長庚大學`
- `GET /student-dashboard?school=長庚大學`
- `GET /advisor/status`
- `GET /ai/status`
- `POST /advisor/plan`
- `POST /advisor/ask`
- `POST /ai/chat`
- `GET /ai/structured-sources`
- `POST /document-check`
- `POST /ai/review-document`
- `POST /ai/rewrite-document`
- `GET /student-experiences?school=林肯大學%20Lincoln%20University`
- `POST /student-experiences/refresh?school=林肯大學%20Lincoln%20University`
- `GET /application-workflow?school=林肯大學%20Lincoln%20University`
- `POST /application-workflow-issue-reports`（只有已登入且完成學生身分驗證的帳號可送出；必須帶目前 workflow ID、版本、快照與官方 HTTPS 來源，使用 `X-Content-Report-Mutation-ID` 安全重送，回報不會建立 revision 或發布內容）
- `GET /admin/application-workflow-issue-reports?status=pending`（內容管理者唯讀載入 `no-store` 待審佇列；不回傳學生 Email）
- `PATCH /admin/application-workflow-issue-reports/{report_id}`（內容管理者以 mutation ID 將案件標為 `resolved` 或 `dismissed`；只關閉案件，不核准、修改或發布申請規定）
- `GET /admin/content-review`（內容管理者雙人審查工作台；未登入與非管理者不可存取）
- `GET /admin/session`（工作台顯示目前內容管理者所需的最小帳號資訊）
- `GET /admin/destination-profile-review-queue?home_university=...`（以長庚大學或國立臺北大學列出各自的生活情報 profile 快照、單筆內容指紋、有效真人審查進度及完整稽核歷程；不修改學生資料）
- `GET /admin/destination-profile-review-queue.csv?home_university=...&expected_snapshot=...`（下載該母校快照綁定的生活情報完整唯讀清單；目前長庚 58 列、臺北大學 85 列，回報系統有效審查證據並保留人工 A／B 空欄，不可匯入或發布）
- `GET /admin/destination-profile-review-batches.csv?home_university=...&batch_size=10`（下載該母校穩定雙人分工 CSV；長庚 6 批、臺北大學 9 批，預設每批 10 筆，包含完整來源、缺口、批次位置與 snapshot-bound 工作台連結）
- `GET /admin/destination-profile-review-batches/{batch_id}?home_university=...&batch_size=10&expected_snapshot=...`（取得單一目前批次；審查進度不換批，實質內容或成員變更後舊指紋回傳 409，不存在批次回傳 404）
- `GET /admin/destination-profile-review-batches/{batch_id}/checklist.csv?home_university=...&batch_size=10&expected_snapshot=...`（下載目前批次逐項查核表；每個 profile 恰有 12 列固定內容區塊，全部官方來源各有一列，A／B 欄保持空白且不能匯入或形成核准）
- `POST /admin/destination-profile-reviews`（內容管理者逐一核對目前 profile 的全部官方來源與 12 個內容區塊後保存 append-only 真人事件；過期 queue／profile 指紋拒絕，同一人更新結論保留取代鏈，兩人核可也不會自動升級或發布）
- `POST /admin/destination-profile-promotions`（兩位不同真人核可且沒有修正要求後，由其中一位有效核可者明確升級；append-only 事件保存兩筆核可、來源／公開內容指紋及完整公開快照。原始候選不被覆寫，候選內容日後變更時會重新進入雙審，學生仍看到上一個已核准版本）
- `GET /admin/destination-profile-publications?home_university=...`（內容管理者依母校唯讀查看每筆生活情報目前公開快照、候選是否已變更、升級／復原 append-only 歷程與是否可安全復原；不修改公開資料）
- `POST /admin/destination-profile-rollbacks`（內容管理者以目前升級事件、最新公開事件及公開內容指紋做並行鎖定，填寫至少 10 字原因後復原到更早核准快照；若沒有更早核准版本則恢復目前 `official_partial` 候選。事件保存撤回／恢復指紋、操作者、時間與完整恢復 profile，不更新或刪除既有事件。復原後同一候選的舊核可失效，必須重新雙審）
- `GET /admin/application-workflow-review-backlog?expected_snapshot=...`（列出尚未通過雙審的既有公開流程、目前待審狀態，以及學年度、有效梯次、精確期限、來源年度、最後查核日期、關鍵規定直接來源與非 HTTPS 來源缺口統計；分工連結可帶 64 字元預期快照，過期時回傳 409）
- `GET /admin/application-workflow-publications?home_university=...`（內容管理者唯讀取得申請流程目前公開 revision、完整發布／復原歷程、pending 阻擋與可安全恢復的舊雙審版本；事件鏈或公開內容不一致時 fail closed）
- `POST /admin/application-workflow-rollbacks`（內容管理者以目前 revision ID、版號、內容指紋及舊版 ID 做並行鎖定；建立新的較高版號復原 revision，不覆寫歷史，並刷新受影響學生的內容更新通知）
- `GET /admin/web-release-readiness`（內容管理者唯讀的 Web 總發布閘門；合併申請流程與生活情報子指紋、逐項 pass／fail、待審數與剩餘阻擋，採 `no-store`，不修改任何內容或審核紀錄）
- `GET /admin/application-workflow-release-readiness`（內容管理者唯讀的申請流程子閘門；保留給流程分工與診斷，Web 是否可發布以總閘門為準）
- `GET /admin/application-workflow-review-batches.csv?batch_size=10`（內容管理者下載與目前快照指紋綁定的風險優先雙人審查分工表；預設每 10 個 workflow 一批，保留 A／B 人工欄位與工作台精確連結，不可匯入或形成核准）
- `GET /admin/application-workflow-review-batches/{batch_id}?batch_size=10&expected_snapshot=...`（內容管理者唯讀取得目前快照中的單一審查批次；batch ID 同時綁定內容指紋、batch size 與批號，回傳該批 workflow，錯誤快照為 409、不存在或大小不符為 404）
- `POST /admin/application-workflow-review-batches/{batch_id}/stage`（內容管理者以 request body 的目前 `expected_snapshot` 與 `batch_size` 冪等建立整批待審副本；已存在者沿用同一 revision，只回報建立／沿用結果，不建立核准、不發布，也不修改學生資料）
- `GET /admin/application-workflow-review-batches/{batch_id}/rules.csv?batch_size=10&expected_snapshot=...`（內容管理者下載該批逐規定唯讀查核表；包含規定內容、官方來源、缺口及 A／B 空欄，不可匯入或形成核准）
- `GET /admin/application-workflow-review-backlog/source-evidence.csv?source_url=...&expected_snapshot=...`（內容管理者下載單一缺口網址的唯讀 UTF-8 CSV；`expected_snapshot` 必須使用 backlog 該分組的來源證據複合快照，並與專用 response header、檔名前 12 碼及 CSV 每列第一欄一致；過期或產生期間變更回 409。逐流程列出年度、梯次、規定及精確引用脈絡，採 `no-store` 與試算表公式防護，不建立 revision 或變更公開資料）
- `POST /admin/application-workflow-review-backlog/{workflow_key}/stage`（冪等建立既有流程的待審副本；不修改學生目前看到的內容）
- `GET /admin/application-workflow-revisions/{revision_id}/comparison`（以精確 `base_version` 產生流程、步驟、文件、送件與來源的基準／候選逐欄對照）
- `PATCH /admin/application-workflow-revisions/{revision_id}/applicability`（只允許內容管理者修改待審版本；以內容雜湊做並行鎖定，來源必須逐頁勾選才會更新年度／梯次；尚無證據資料的規定引用可在真人確認後補上來源名稱、角色與權威層級；也可填入已核實的 HTTPS 替代網址並同步全部相同引用，相容舊入口可明確合併、衝突則拒絕；修正後清除既有核准並保存稽核紀錄，不修改學生目前看到的內容）
- `POST /admin/application-workflows/refresh?school=林肯大學%20Lincoln%20University`（僅內容管理者；建立待審版本，不會直接發布）
- `POST /admin/application-workflow-revisions/{revision_id}/approve`（內容管理者獨立核准；request 必須帶目前 `expected_content_hash`、逐頁確認的完整 `reviewed_source_urls`、逐項確認的完整 `reviewed_rule_keys` 與說明，同一帳號不能重複）
- `POST /admin/application-workflow-revisions/{revision_id}/publish`（兩個不同帳號的核准都必須綁定目前版本、完整來源與完整關鍵規定清單，之後才能正式發布）
- `POST /admin/application-workflow-revisions/{revision_id}/reject`（退回待審版本）
- `GET /application-center/templates?program_type=exchange&flags=subsidy`
- `POST /application-center/manifest`
- `POST /application-center/pdf`
- `GET /destination-profile?school=林肯大學%20Lincoln%20University`
- `POST /destination-profile/refresh?school=林肯大學%20Lincoln%20University`
- `GET /destination-profiles`
- `GET /coverage`
- `GET /community/questions?school=林肯大學%20Lincoln%20University`
- `GET /community/posts?topic=scholarship&q=補助`
- `POST /community/questions`
- `POST /community/questions/{question_id}/answers`
- `POST /experience-submissions`
- `GET /deadlines`
- `GET /documents`
- `GET /search?q=交換學生`
- `GET /auth/providers`
- `POST /auth/email-verification/request`
- `POST /auth/email-verification/confirm`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PATCH /auth/me`
- `POST /auth/student-verification`（登入後一次性處理學生證影像）
- `POST /auth/student-verification/confirm`（套用已驗證校籍）
- `POST /auth/logout`
- `GET /community/boards`（固定看板與目前帳號權限）
- `POST /account/submission-progress`（學生手動送件狀態、收件證明 metadata 與工作區版本同步）
- `GET /account/vault/documents`
- `POST /account/vault/documents`（逐檔同意後加密保存）
- `POST /account/vault/documents/{document_id}/versions`（新版本重新同意）
- `POST /account/vault/versions/{version_id}/download-grant`
- `POST /account/vault/download`（短效授權放在 `X-Vault-Download-Token` Header）
- `DELETE /account/vault/documents/{document_id}`（永久刪除所有版本）

`/student-dashboard` 是學生前端主要使用的整理後資料，包含申請期間、申請資格、語言門檻、官方文件摘要、補助要點解讀，以及可申請學校清單。官方文件會把公開規章 PDF 或表單連結整理成 `document_explanations`，例如「領航者補助作業要點」、「學海惜珠補助要點」、境外交流作業要點、短期學分補助要點，以及申請表、同意書、計畫書、報告、聲明書等文件。學生預設先看摘要與重點；需要完整版本時，再點官方完整文件連結。`/sources` 與 `/search` 只回傳摘要、片段與來源 URL，不回傳整篇內文，避免把原站文章大量複製到前端。

## 資料儲存位置

- `data/raw/pages.jsonl`: 每筆原始頁面包含 `source_url`, `crawled_at`, `content_hash`, `attachments`
- `data/raw_files`: 下載的 PDF、docx、pptx 等附件，包含官方規章 PDF 與表單文件
- `data/processed/pages.jsonl`: 清洗後頁面，含 rule-based category
- `data/processed/exchange_info.json`: 給 APP 使用的結構化欄位
- `data/processed/structured_sources.jsonl`: 每份公告的計畫、年度、學期、期限、資格、語言、文件與補助欄位，並標示規則式或 AI 抽取及是否待複核
- `data/processed/document_chunks.jsonl`: RAG 使用的短段落、來源、發布日期、最後查核時間、內容雜湊與選配 embedding
- `data/processed/student_experiences.jsonl`: 各合作學校的公開學生心得與影片索引、短摘要、主題及來源 URL
- `data/processed/application_workflows.jsonl`: 各合作學校的官方申請步驟、負責單位、期限、文件、來源與最後查核時間
- `data/processed/application_workflow_issue_reports.jsonl`: 僅供本機開發與測試的申請規定錯誤回報 repository fallback
- `data/processed/partner_research.jsonl`: 依母校隔離的合作校官方網域、信心狀態、發現來源與查核時間
- `data/processed/destination_profiles.jsonl`: 已查核的城市、住宿、生活費、交通與官方來源
- `data/processed/collection_audits.jsonl`: 依母校記錄每間合作校的官網、心得、流程與生活資訊查核狀態，包含零結果與失敗紀錄
- `data/processed/community_posts.jsonl`、`community_post_comments.jsonl`: 匿名公開貼文與留言
- `data/processed/public_chat_messages.jsonl`: 各合作校公開聊天室訊息
- `data/processed/private_conversations.jsonl`、`private_messages.jsonl`: 邀請制私訊與對話
- `data/processed/community_blocks.jsonl`、`community_reports.jsonl`: 封鎖與檢舉紀錄
- `data/processed/user_accounts.jsonl`: 僅供本機開發與測試的帳號 repository fallback
- `data/processed/account_sessions.jsonl`: 僅供本機開發與測試的可撤銷 session fallback
- `data/processed/community_questions.jsonl`: 待審核或已核准的公開問題
- `data/processed/community_answers.jsonl`: 待審核或已核准的公開回答
- `data/processed/experience_submissions.jsonl`: 學生投稿的交換經驗與原始公開連結
- `data/private_vault/`: 僅供本機開發的加密文件、加密 metadata 與去識別 audit；整個目錄不納入 Git

所有頁面與結構化資訊都保留來源 URL，因為交換申請資訊可能會異動。

申請文件的個人資料、答案與附件不寫入上述 `data/processed` 檔案；只有使用者在私人文件庫逐檔同意後，才會進入獨立的加密儲存區。

## 測試

完整測試包含 Chromium Web 端到端流程；第一次執行前請先安裝瀏覽器：

```powershell
python -m playwright install chromium
```

```powershell
pytest
```

只重跑下一階段的 Web 黃金路徑與權限負面情境：

```powershell
pytest -q tests/e2e
```

E2E 會在隨機本機連接埠啟動 FastAPI，並將帳號、表單、私人文件與社群驗收資料寫入 pytest 的隔離暫存目錄，不會修改正式 `data/`。

`2026-08-31-pre-review.129` 的目前驗證基線：CI 相同 frozen environment 以隔離資料目錄分開跑完 804 項非 E2E 與 49 項 Chromium E2E，合計 853 passed、0 failed；耗時分別為 412.66 與 456.41 秒。除審查批次競態防護外，新增單元、API、OpenAPI 與 Chromium 證據證明來源證據 CSV 會綁定專用複合快照；候選 manifest、schema、workflow 內容、目前查核時間或 pending revision 身分改變時舊下載回 409，產生期間變動也不交付 CSV。`uv lock --check` 可解析 88 個 package，runtime dependency audit 為 0 個已知漏洞；OpenAPI `2026-08-31.2` drift 檢查、21 份 migration 的 471／11／51 parser 檢查，以及最新 migration 的 29／0／4 檢查均通過。兩套來源封裝基線仍為 22 個去重網址（20 個最終 HTTPS、2 個轉回 HTTP）及 5 個可讀、1 個應用層失效；本次 live recheck 則因立教 2 個 URL 與長庚 1 個 URL timeout 而 fail closed。正式 release audit 仍為 9 類 blocker 且三個 fingerprint 未變。

Web 與未來 Flutter 共用的 API contract 固定在 `docs/api/openapi.json`。修改 request、response、enum、錯誤狀態或權限邊界後，先人工確認相容性，再更新並檢查快照：

```powershell
uv run --frozen python scripts/export_openapi.py
uv run --frozen python scripts/export_openapi.py --check
```

Supabase migration 的頂層 SQL 與巢狀 SQL／PL/pgSQL function body 也必須通過固定版 parser；先安裝 `.[dev]` 後執行：

```powershell
uv run --frozen python scripts/validate_supabase_migrations.py
```

Docker Desktop 運行時，可再以全新 tmpfs PostgreSQL 與隨機 loopback port 重跑真實 migration／PostgREST 安全邊界。腳本不接受任意完整 Compose project 名稱；它只使用 `exchange-supabase-runtime-` 保留前綴，依 GitHub run identity 或本機 PID 加密雜湊／隨機值產生每次唯一名稱，也不讀取正式 Supabase credentials。image tag 與 digest 固定在 `supabase/runtime-validation/docker-compose.yml`：

```powershell
uv run --frozen python scripts/validate_supabase_runtime.py
```

這個 runtime harness 驗證 migration apply、RLS／grant、direct DML denial、transient auth／workspace concurrency、workflow issue submit／review／限流／刪帳 retention／purge、公開／私人社群多 API 競態與六種晚期失敗 rollback、刪帳晚期 rollback、冪等 replay、真實 Supabase Storage API file backend 刪除及 durable cleanup queue。`pre-review.127` 已從零套用 21／21 migrations 並通過 32／32 RLS、0 browser grants、3 個 workflow issue service RPC ACL；最終必要 run 回傳 `status=passed`、`cleanup_status=passed`，事後 container／network／volume 查驗均為 0。`docker info` 最多 30 秒、冷啟 Compose 最多 600 秒、控制／清理及每次 psql 最多 120 秒、單次 readiness probe 最多 10 秒、log 收集最多 30 秒；timeout 訊息不包含 SQL、token、environment 或部分輸出。啟動前及正常／失敗／timeout 結束時只清理該次專用 project，並以 Docker project label 檢查 container、network、volume；清理非零或仍有殘留都使整體 exit 1，且不掩蓋原始驗證錯誤。它使用隔離的本機 file backend，不代表正式 Supabase project 的實際 Storage backend、備份還原或升級路徑已通過。

啟動 FastAPI 後可從 `/docs` 開啟安全的契約入口並連到即時 `/openapi.json`。這個入口不載入第三方 Swagger／ReDoc CDN，也不執行 inline JavaScript；舊 `/redoc` 會導向同一頁。互動式 API renderer 不應以放寬 production CSP 為代價重新啟用。

`.github/workflows/quality.yml` 會固定安裝 `uv 0.11.26`，先以 `uv lock --check` 與 `uv sync --frozen --extra dev` 建立和本機相同的鎖定環境，再於隔離的 `EXCHANGE_INFO_DATA_DIR` 重跑 Python／JavaScript 語法、OpenAPI drift、Supabase migration／function body parser、dependency audit、真實隔離 Supabase runtime harness 與完整 pytest。runtime step 有 20 分鐘外層硬上限且不能忽略失敗，腳本內每個外部子程序另有較短 timeout；每次 run 會產生唯一且經驗證的 Compose project 名稱，cleanup 非零或 label 殘留會使 CI fail closed。整體 job 上限為 45 分鐘；checkout、setup-python 與 setup-node 都固定到官方版本標籤當下的完整 commit SHA。workflow 不使用會重新解析版本的 editable pip install，也不執行 AI 或 Flutter 工作。遠端 GitHub Actions 尚未首次執行。

## AI 模組（本機 provider 基礎完成，產品串接仍暫緩）

LAI-00～LAI-03 已建立 `LocalGemmaProvider`、固定 loopback／model 設定、JSON Schema 驗證、單一推論 slot、timeout 及 fail-closed 測試，核准模型為 Ollama `gemma4:12b` 與 `embeddinggemma`。只有明確的 `EXCHANGE_LOCAL_AI_MODE=prototype` 加 development runtime 才能建立隔離 provider；production、非 loopback、其他模型或 cloud tag 都會拒絕。這個隔離 factory 只供 runtime／provider 驗證，不能因環境變數自動接管產品。

產品 AI runtime 仍固定為 `paused`：`get_provider()` 回傳 `None`，相容 AI 端點維持 503，既有顧問與文件檢查只使用已查核來源、關鍵字檢索及規則式邏輯。Advisor／RAG 串接屬於 LAI-04 之後的獨立核准範圍；啟用時仍須保留 server-owned 引用、fresh consent、資料不作訓練、零內容 log 及官方規則優先等邊界。

**B4-04 / LAI-08～11 進度：**
- `redaction.py`：PII 去識別（身分證、護照、電話、Email、學號、姓名、地址），含 `redact_for_logging()` 安全 log 建構
- Web AI 狀態晶片：即時顯示 Gemma 4 狀態（暫停/離線/載入中/就緒/忙碌/降級），含 ARIA live region
- 降級 UI：AI 離線時自動切換至規則式結果，不影響搜尋、比較、資格等功能
- 可靠性腳本：固定 10 題繁中問答、冷啟動計時、VRAM 監控（`scripts/benchmark_local_ai.py`）
- 安全稽核測試：SSRF、prompt injection、log 隱私、暫存檔、網路隔離
- 詳細說明見 [`docs/local-ai-runbook.md`](docs/local-ai-runbook.md)、[`docs/local-ai-web-review.md`](docs/local-ai-web-review.md)

### 選配 Supabase PostgreSQL + pgvector

第一次設定 Supabase 請照 [`docs/supabase-setup-guide.md`](docs/supabase-setup-guide.md) 一步一步做，最後用 `scripts/check_supabase_setup.py` 檢查。後端金鑰新舊兩種格式（`sb_secret_...` 與舊的 `service_role`）都支援。

把網站放上主機（Render）請照 [`docs/deploy-render-guide.md`](docs/deploy-render-guide.md)；`render.yaml` 是對應的部署設定。主機前面有代理時，程式靠 `EXCHANGE_CLIENT_IP_HEADER` 與 `EXCHANGE_PUBLIC_BASE_URL`（Render 上沒設時退回 `RENDER_EXTERNAL_URL`）取得真實訪客位址與對外網址，見 `src/exchange_info/request_origin.py`。

本機開發不設定雲端服務也能運作。非 AI 階段的正式環境需依 migration 檔名順序套用 `supabase/migrations/`，包含內容治理、帳號工作區、通知、文件庫、Email 驗證、表單草稿、雙人流程審查、revision 修正歷程、生活情報審查／升級／復原、申請流程復原、暫態 OAuth／學生驗證 state、原子帳號驗證提交、`20260823130000_atomic_workspace_and_suspension.sql`、`20260823160000_atomic_public_community.sql`、`20260824100000_atomic_private_community.sql`、`20260829100000_atomic_account_deletion.sql`、`20260830100000_application_workflow_issue_reports.sql`，以及 `20260819170000_application_workflow_publication_integrity.sql` 的同流程自我參照與復原事件唯一性約束；`202607190001_ai_rag.sql` 留到本地 AI／RAG 階段再評估。帳號、工作區、session、正規化 provider link、通知、Email 驗證 challenge、私人文件 metadata、表單草稿密文、暫態驗證資料、公開／私人社群內容、申請規定錯誤回報與內容核准／修正紀錄都開啟 RLS，並撤銷瀏覽器角色的直接 mutation 權限；Web 與未來 Flutter 都只能經由 FastAPI 存取。

正式環境必須明確選用 Supabase repository。API 會集中核對帳號、內容治理、生活情報審查、私人文件庫、加密表單草稿、暫態驗證 state、公開社群、社群停權稽核與申請規定錯誤回報九個 backend identity；社群停權稽核與帳號共用 repository，但仍有獨立的啟動檢查。若任一仍是 JSONL／local encrypted／memory、缺少 URL 或後端 secret，就拒絕啟動。明確設定 `EXCHANGE_ACCOUNT_REPOSITORY=jsonl`、`EXCHANGE_COMMUNITY_REPOSITORY=jsonl`、`EXCHANGE_TRANSIENT_AUTH_BACKEND=memory`、`EXCHANGE_WORKFLOW_ISSUE_REPORT_BACKEND=jsonl` 或以依賴注入傳入本機 service 也不能繞過；development／test 的隔離 fallback 維持可用：

```powershell
$env:SUPABASE_URL="https://你的專案.supabase.co"
$env:SUPABASE_SECRET_KEY="後端專用 sb_secret 金鑰"
$env:EXCHANGE_ACCOUNT_REPOSITORY="supabase"
$env:EXCHANGE_VAULT_BACKEND="supabase"
$env:EXCHANGE_FORM_DRAFT_BACKEND="supabase"
$env:EXCHANGE_TRANSIENT_AUTH_BACKEND="supabase"
$env:EXCHANGE_COMMUNITY_REPOSITORY="supabase"
$env:EXCHANGE_WORKFLOW_ISSUE_REPORT_BACKEND="supabase"
$env:EXCHANGE_ENVIRONMENT="production"
$env:EXCHANGE_CONTENT_ADMIN_EMAILS="admin@example.com"
$key = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($key)
$env:EXCHANGE_VAULT_MASTER_KEY=[Convert]::ToBase64String($key)
```

`20260821190000_transient_auth_state.sql` 讓 Google／Facebook 登入、校方 OAuth 與學生證一次性 token 共用 Supabase TTL store；start 的限流／容量／同 session 替換及 callback consume 都在資料庫交易鎖內完成，因此這些暫態資料可由多個 Web worker 共用。限流只保存以伺服器金鑰 HMAC 後的 client fingerprint，不保存原始 IP；錯誤帳號、session、provider 或瀏覽器只會被拒絕，不會先耗用真正發起者的 state。

`20260823100000_atomic_auth_account_mutations.sql` 另將 provider link 正規化，並以只開放給 `service_role` 的 RPC，在同一資料庫 transaction 內完成 Google／Facebook 帳號解析或建立、provider link 與 session 建立，以及校方 OAuth／學生證的 exact-session 學生身分提交。一般 profile 改用欄位白名單 patch；日曆同步以目前 token 作 expected CAS，撤銷後才抵達的舊同步不能復活 feed。Migration 同時撤銷 `service_role` 對 account table 的直接 UPDATE，正式 repository 也拒絕相容整份 upsert；註冊只 insert、刪帳後的舊寫入不會重建帳號。本機 JSONL 對齊相同欄位與衝突語意。這是 `pre-review.103` 已完成的 auth／profile 範圍，仍保留作歷史基線。

`20260823130000_atomic_workspace_and_suspension.sql` 是 `pre-review.104` 新增的資料庫邊界：以 typed revision 與 compare-and-swap（CAS）提交單一 workspace，並在同一 transaction 更新 calendar projection；交易採固定的 account → workspace 鎖序。學生停權改由專用 RPC 在同一 transaction 寫入停權狀態及 private append-only audit，audit 保留 90 天並提供 purge 邊界。這些 RPC 只授權 `service_role`，workspace 與停權 audit 的直接 DML 均已撤銷。

`20260823160000_atomic_public_community.sql` 是 `pre-review.105` 的公開社群交易邊界：identity 與 token rotation、問題、回答、貼文、留言、公開聊天室與心得投稿、發布限流、貼文／留言刪除、moderation CAS／audit、操作冪等與刪帳公開作者去識別都改由 `service_role` 專用 RPC 原子提交。交易採 account → identity → parent 的固定鎖序，缺少 Email／學生驗證欄位一律 fail closed；相同 mutation ID 與相同語意重送會回放第一筆結果，不重複計入限流或建立內容。瀏覽器端會為六類發布保存並重用 mutation ID，成功或明確 4xx 後才清除。

`20260824100000_atomic_private_community.sql` 是 `pre-review.106` 的私人社群交易邊界：私訊邀請與初始訊息、接受邀請、後續訊息、封鎖、公開／私訊檢舉、檢舉 CAS 審核＋audit，以及單一 identity 的刪帳前私人清理都改由 `service_role` 專用 RPC 原子提交。交易採 account → sorted identity → conversation → child 固定鎖序；相同使用者語意重送時，API 重新產生的 ID、顯示名稱、狀態與時間不列入 fingerprint，Web 也會在網路錯誤／5xx 後重用同一 mutation ID。完整設計與尚未完成邊界見 `docs/private-community-persistence-design.md`。

`20260829100000_atomic_account_deletion.sql` 是 `pre-review.107` 的整體刪帳邊界：exact session 驗證、公開作者去識別、私人資料與敏感 mutation receipt 清理、Email challenge、account 與所有 FK 關聯資料在單一 PostgreSQL transaction 完成，並撤銷 service role 的 direct account DELETE。加密檔案物件位於 Supabase Storage API，無法加入 DB transaction；因此 RPC 先保存 object keys 與不含帳號個資的 durable receipt，Web 以 `X-Account-Deletion-Mutation-ID` 安全重送，commit 後刪除物件並 ack，管理員文件庫 cleanup 也會續作 pending receipt。

`20260830100000_application_workflow_issue_reports.sql` 是 B5-05 的申請規定錯誤回報邊界：兩張強制 RLS 的表與 service-role-only RPC 原子保存學生回報、每小時限流、語意型冪等重送及管理員 CAS 處置。API 會以目前 workflow 重新建立受信任的流程／步驟快照，不接受瀏覽器自行宣告的標題或版本；回報成立只會關閉案件，任何正式內容修正仍須另開 revision 並走既有雙人審查。刪除帳號時 pending 回報去識別後最多保留 90 天；若案件之後被處置，只為不確定結果的安全 replay 短暫保留最多 24 小時，之後清除。

這仍不代表已可多 worker 安全部署。本輪隔離 harness 已在真實 PostgreSQL／兩個 PostgREST／Supabase Storage API file backend 依序套用 21／21 migrations，並驗證 32／32 RLS、0 browser direct grants、五張敏感表 direct DELETE denial、transient auth／workspace 並行、workflow issue submit／review／限流／刪帳 retention／purge、公開／私人社群相反方向競態、六種社群 transaction 晚期錯誤完整 rollback、刪帳晚期 rollback、Storage timeout 後 receipt 保留、實際 bucket 物件刪除／重送與巢狀 orphan cleanup；但尚未在正式 Supabase project 的正式 Storage backend、既有資料升級與備份還原路徑重驗，也沒有首次遠端 CI 證據。production 因此仍限制為 single worker，發布狀態維持 `NOT READY`。產品 AI 的 Advisor／RAG／文件／Web 串接、Flutter、SwiftUI 與 Kotlin 仍不在本階段實作範圍。

另外要在 Supabase Dashboard 或 Storage API 建立名稱為 `exchange-private-vault` 的 **private bucket**；不要直接修改 `storage` schema。bucket 保存的只有 AES-256-GCM 密文，原始檔名與顯示名稱也以密文存在 metadata。後端會在第一次存取 Storage 前驗證 bucket，若是 public bucket 就拒絕操作；`EXCHANGE_VAULT_MASTER_KEY` 必須是固定保存、base64url 相容的 32-byte 隨機金鑰，遺失後既有文件無法解密，輪替前必須先設計金鑰版本與重加密流程。若使用其他 bucket 名稱，可設定 `EXCHANGE_VAULT_BUCKET`。

`EXCHANGE_CONTENT_ADMIN_EMAILS` 可用逗號分隔多位平台內容管理者；至少應設定兩個實際由不同人控制的帳號。只有清單內已登入帳號能開啟 `/admin/content-review`、建立待審版本、留下生活情報獨立審查事件、核准申請流程、發布或退回。生活情報要求兩人各自確認完整來源與 12 個內容區塊；完成只會標記可交內容負責人處理，不會自動改成 `official_verified`。申請流程正式發布則要求兩個不同帳號都對目前版本逐一確認完整官方來源、流程步驟與文件，且發布者必須是其中一位審查者。`SUPABASE_SECRET_KEY` 與 `EXCHANGE_VAULT_MASTER_KEY` 都不可放進網頁或 Flutter；既有部署仍可暫用 `SUPABASE_SERVICE_ROLE_KEY`，但同樣只能存在 FastAPI 的 secrets 設定。AI API 與本地 AI 目前均暫緩；既有 `202607190001_ai_rag.sql` 不屬於本階段部署要求。

正式環境應每日執行 `exchange-info cleanup-document-vault`，永久移除已超過使用者所選期限的版本及孤兒密文物件。受權管理者也可呼叫 `POST /admin/document-vault/cleanup`。本機開發會在 `data/private_vault/.local-master-key` 自動建立測試金鑰；該 fallback 不允許用於 production。

### Web 與 Email 截止提醒

登入帳號可在個人設定選擇 30／14／7／3／1 天提醒，並分別開關 Web 與 Email。Web 通知會在開啟通知中心時以冪等方式補齊；正式排程可每日執行 `exchange-info run-notifications`，或由受權管理者呼叫 `POST /admin/notifications/run-due`。紙本與混合送件只使用「必須送達」日期，不會把最晚寄出日冒充截止完成日。

官方申請規定只有在內容管理者人工發布新版本後才會產生異動通知；待審與退回版本不會通知。系統會以本校、合作校、學年度、申請梯次及異動規則的學系範圍，比對已建立的申請計畫，只通知真正受影響的帳號。通知包含舊／新版號、人工審核的變更摘要與官方來源，同一發布版本對同一帳號只建立一次；排程工作與學生開啟通知中心都可補償先前未完成的通知建立。

Email 預設關閉。只有使用者選擇加入，且 FastAPI 設定完整 SMTP secrets 時才會實際寄送；失敗會依序在 5 分鐘、30 分鐘與 2 小時後重試，紀錄只保存錯誤類別，不保存供應商回傳原文：

```powershell
$env:EXCHANGE_NOTIFICATION_EMAIL_ENABLED="1"
$env:EXCHANGE_SMTP_HOST="smtp.example.com"
$env:EXCHANGE_SMTP_PORT="587"
$env:EXCHANGE_SMTP_FROM="no-reply@example.com"
$env:EXCHANGE_SMTP_USERNAME="後端 SMTP 帳號"
$env:EXCHANGE_SMTP_PASSWORD="後端 SMTP 密碼"
$env:EXCHANGE_SMTP_STARTTLS="1"
```

## Flutter 手機 App（目前主要版本）

Android 與 iOS 手機端已整合到 `mobile_flutter/`，共用同一套 Dart 程式碼。現有 `android/ExchangeGuideAndroid/` 與 `ios/ExchangeGuide/` 暫時保留作為功能與版面對照，不再作為後續功能的主要實作位置。

Flutter 版包含獨立的公共留學首頁與長庚大學板、個人交換計畫、條件式學校推薦、三段文件進度、交換預算、可寫入第三方日曆的申請時程、合作校搜尋與收藏、官方文件摘要、詳細流程、生活情報、學生心得、全校結構化留學社群、校別聊天室、邀請制私訊，以及 Android／iOS 桌面與鎖定畫面 Widget。App 字型與文字大小跟隨手機系統設定。

Windows 可執行 Android 分析、測試與 APK 建置；iOS 原始專案也會同步生成，但最後的 iPhone 測試、簽署與 App Store 上架仍需要 macOS 與 Xcode。完整指令請參考 `mobile_flutter/README.md`。

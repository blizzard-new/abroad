# TKU 第四批：最新 main 整合、文件切換與公告查核

2026-10-08 查核；repository `blizzard-new/abroad`；獨立目錄 `/workspace/abroad-tku`；分支 `data/tku-exchange-20261008`。本批已依後續授權將最新 main `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59` 合併到本分支，merge commit `1bbb150f738bb5a9eac5d5166b489d449d27bc22`。没有反向 merge main、部署或 force push，未使用其他 session 的工作目錄。

本文件與 [實際驗證 JSON](tku-batch-4-validation-2026-10-08.json) 是最新交接；前三批檔案保留歷史。校別資料與原附件不重寫，已核實的 53 項外校文件與 28 份附件仍保留。

## 資料範圍與完整度

128 個計畫列、119 個原文學校名稱、無重複記錄 ID。最新可核實校級名單為 **2027–2028 日語第二次甄選 4 校、7 名**；2026/9/30 12:00 臺北時間校內截止，查核時 **0 個可新申請選項**。124 列英歐／中文組 115 舊期資料只作參考；姊妹校協議、大三出國及院系計畫沒有併成當期校級可選名單。名額 TBC、空白、零、正數各有獨立狀態，不補猜缺值。

每個重要欄位保留官方 URL、頁碼／原文位置、適用原生年度、角色與查核日；母校 outbound 與外校 incoming 條件分開。四校 38 欄矩陣共 152 格：**85 verified（55.9%）、20 reference_only、19 needs_confirmation、17 missing_in_source、11 not_verified_new**。完整度不是申請保證。

| 四校 | verified | reference_only | needs_confirmation | missing_in_source | not_verified_new |
| --- | ---: | ---: | ---: | ---: | ---: |
| 立命館 | 26 | 3 | 4 | 4 | 1 |
| 長崎外國語 | 22 | 2 | 6 | 6 | 2 |
| 成蹊 | 26 | 1 | 5 | 5 | 1 |
| 電氣通信 | 11 | 14 | 4 | 2 | 7 |

72 筆原來源快照／嘗試（67 個不同 URL）、28 份原附件；保留 3 個既有 failed 入口及 HTTP 錯誤。外校申請 45 項、行前 8 項，合計 53 項；均標提名／計畫條件。UEC 一般表格明示「一般參考／2027版未核實」。4 個流程各 6 步，仍為未發布的 legacy 流程，沒有啟用官方期限提醒。4 個生活指南各有 14 區塊。

## 已修正的行為

文件中心在確認目標切換時，背景 workspace/draft render 可能把 select 恢復為舊目標；原 handler 在 await 後才讀取 select，於是確認 A→B 後仍顯示 A。本批用最新 main 的 app.js 在獨立本機 TKU server 實際重現此路徑；前後狀態逐項保存在驗證 JSON。簡單、不插入背景 render 的切換本來就可成功，不能說每次都會發生。

修正先保存使用者提出的目標，確認後採該值；確認期间停用重複切換。每次載入保存母校、目標、計畫、年度、梯次、學制、科系、flags 與帳號情境，新的 request ID 使舊成功、失敗和 finally 都不能覆蓋新情境。切換即清除舊文件及來源，載入時不呈現前校文件。母校切換也立即失效舊請求；母校資料／帳號 workspace 載入後再次核對母校。templates API／UI 現在傳遞原生年度與梯次，未知年度不沿用 2027 文件。

文件目錄 API 使用四母校既有 workflows accessor，在隔離資料目錄仍能讀到正確母校的公開 bundle；保留發布流程的審查條件。長崎 dashboard 已刪除「正確交換頁、2027期限、住宿價目尚未核實」的過期說法，補上已知 NICS 2027 春期限／費用與 Form A、誓約書、合作名單來源；搜尋／advisor 使用的 ProcessedPage 亦有已讀外校資料與各版本警語。dashboard 有 16 個來源，搜尋有 52 個來源頁；來源多不代表對應資格已確認。

長崎 NICS 春季出願為 2026/10/31 消印有效，未填官方未載的時刻。費用保留 NICS 的授課費、活動費、宿舍、餐費、保險個別條件；**淡江本輪必對應 NICS 及研究生是否適用仍待確認**，不將 NICS 年度、校區或收費套給所有提名者。

## 新版公告的有界負面查核

新檔 [current_notice_audit.json](../src/exchange_info/official_data/tku/current_notice_audit.json) 與 `scripts/audit_tku_current_notices.py` 保存 25 個官方入口／回查結果，不與原 72 筆來源相加成不重複來源數。查核首頁、公告索引、赴外入口及五個官方搜尋，並讀完 **2025/9/1–2026/10/8 公開 custom-news REST 的 293 筆 metadata、全部 3 頁**；逐筆保留 ID、發表／修改日、標題、URL。對發現的相關現存公告及外校入口另回查內文；不是逐篇讀完 293 篇全文。

HTML 公告首頁停在 9/24，REST 有 10/6 新公告，故沒有只取首頁。指定範圍公告標題與已查入口未發現 2027–2028 英歐／中文組新版；既有英歐 2025/10/17、中文 2025/12/30 公告內文及附件仍為 115／2026–2027。狀態為 **not_verified_new（尚未核實新版）**，不是官方明示「尚未公告」，也不排除其他網站／非公開資料有新版。REST 查核來源可在 dashboard／搜尋追溯；舊公告、結果公告明示不是當期申請文件。

另找到 2027–2028 日語第一次甄選公告 22353，內文學生截止 2026/3/1 17:00、系所 3/2 17:00。這是前一個已結束梯次，沒有加入 9 月二甄四校名單。舊赴外 pretty URL 404 與可選 sitemap 404 只記錄讀取失敗，不用作未公告證據。

11 個既有公告／外校頁回查未改變已核實事實：10 個位元相同，長崎 Form A 動態 HTML 的 visible text 相同。長崎當期 NICS／合作關係仍可查，公開頁仍未解決淡江本輪／研究生映射；UEC 一般申請頁仍為一般版本，課表入口仍是 2026，沒有升為 2027 專屬。13 組來源矛盾保留原依據與待確認狀態。

## 共用檔與臺大保留

相對上述 main 的必要共用變更共 **14 檔**：

| 檔案 | 變更目的 |
| --- | --- |
| university_registry.py | 四校 registry，保留 NTU，加入 TKU aliases/profile |
| models.py | closed／reference_only／quota_unconfirmed 狀態 |
| api.py | TKU 分流、逐欄完整度、四母校文件目錄、templates 年度／梯次 |
| storage.py | 加入 TKU bundle；保留三校資料讀取 |
| application_documents.py | TKU 兩種準備稿與獨立適用期／查核日；保留 NTU |
| static/app.js | TKU 顯示與上述文件情境／請求同步修正 |
| static/index.html | 可用性篩選、通用搜尋空狀態、app 資產版號；保留 NTU scripts |
| pyproject.toml | 打包 TKU 官方 DOCX/XLSX |
| docs/api/openapi.json | enum 與 templates 兩個 optional query 欄位 |
| tests/test_school_completeness.py | 575 目的地及四校各自數量 |
| tests/test_ntu_integration.py | registry 3→4；NTU 其他斷言不變 |
| tests/e2e/test_ntu_school.py | 選校數量 3→4；NTU 使用流程不變 |
| tests/test_fit_signals.py | destination 571→575，保留預算誠實性斷言 |
| tests/test_task_documents_and_reference_plan.py | workflow 851→855；TKU 原生未發布年度與外校清單獨立斷言 |

其餘 TKU 資料、抓取程式、adapter、測試及文件皆為校別独立。CGU／NTPU／NTU 官方資料、校別模組與兩個 NTU 引入的 journey/workbench scripts 相對 main 沒有 diff；不改其來源內容。保留 CGU 154、NTPU 409、NTU 288 workflows，加 TKU 4 共 855；目的地 CGU 77、NTPU 206、NTU 288、TKU 4 共 575。

## 實際驗證與剩餘事項

TKU **20 passed**。擴大回歸 **301 passed、9 failed、6 skipped**；9 個 failure ID 在未改的最新 main f6ad 基準上均重現（基準檢查 49 passed、9 failed），新增失敗集合為空。8 項為既有 frontend 文字 contract，1 項為既有 NTPU isolated-data destination coverage；没有修改這些 out-of-scope 問題掩蓋結果。原硬編碼總數新增失敗已修正後重新跑到實際行為。

臺大 Chromium E2E **7 passed**，包括 390px／1440px、瀏覽／詳情／母校返回、GPA／排名條件保存。TKU Chromium 1280×900 與 390×844 在同一學生情境走所有六組校對的 A→B→A、取消、延遲舊回應、未知年度文件清空，以及 TKU→NTPU→CGU→NTU→TKU。逐校核對可見標題、年份、文件數及官方來源 URL；四校詳頁實際展開外校申請、14 個生活區塊、38 個完整度欄，沒有 page error 或 TKU 詳頁橫向溢出。完整步驟與結果保存在驗證 JSON；截圖 `/tmp/tku-detail-switch-{1280,390}-{0..3}.png`，可由程式重做。

OpenAPI --check、Python／JavaScript 語法、git diff --check 及資料離線重建逐位元一致通過。`uv lock --check` 在本分支及未改 f6ad 基準均實際 exit 1：`The lockfile at uv.lock needs to be updated`；未修改 lockfile，使用既有 frozen venv。

程式／資料 commit `78849153528068a61aabec9de0437d4ee9d132ba` 已正常推送，`git ls-remote` 與本地一致；[draft PR #2](https://github.com/blizzard-new/abroad/pull/2) 為 OPEN／draft／MERGEABLE，main 仍為 f6ad。後續證據提交只更新交接文件。

本輪 [quality run 37728615498](https://github.com/blizzard-new/abroad/actions/runs/37728615498) 為 completed／failure、jobs **0**；取失敗 log 實際 exit 1：`failed to get run log: log not found`。該 commit 的 check-runs **1**，為 `Supabase Preview`／completed／skipped；沒有品質 job 執行結果或部署成功證據。失敗原因尚未核實，不推測為配額或宣稱 CI 通過。此前 main f6ad 的 quality run 37723868722 亦 failure；本地通過不表示遠端 CI 綠燈。最終文件提交的遠端 HEAD 與 CI 查核另在 PR／最後回覆回報。

未解資料為英歐／中文新版、各系所提前截止、長崎 NICS／研究生對應、UEC 2027 專屬版及 13 組來源矛盾；124 舊期學校外校欄位未逐校查新期，不冒稱完整。需官方新版／提名材料／承辦澄清才能提升狀態，未聯繫校方。

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_tku_current_notices.py --output /tmp/tku-current-notice-audit.json
PLAYWRIGHT_BROWSERS_PATH=/tmp/tku-browsers PYTHONPATH=src .venv/bin/python scripts/check_tku_target_switching.py
.venv/bin/pytest tests/test_tku_support.py -q
.venv/bin/python scripts/export_openapi.py --check
```

報表以 `scripts/report_tku_batch4_validation.py` 讀本輪、最新 main 基準、NTU JUnit、browser 結果、切換前後重現 JSON 及明示 baseline commit 產生；驗證依據不靠手填測試成功。

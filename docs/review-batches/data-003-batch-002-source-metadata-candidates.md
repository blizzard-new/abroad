# DATA-003-BATCH-002：共用來源中繼資料研究候選

- 研究日期：2026-08-30
- 範圍：215 份流程共同引用、但尚未建立完整來源名稱／角色／權威層級的 6 個 exact URL
- 狀態：`human_review_required`
- 發布效果：`none`
- 可自動填入：全部為 `false`
- 正式資料變更：0
- 建立待審版本／核准／發布：0／0／0

這份證據包只把已能從原始官方頁面辨識的候選中繼資料放到管理者工作台與唯讀 CSV，減少真人重新尋找頁面標題的時間。候選不會寫入 workflow，也不能取代逐流程適用性、年度、梯次、規定內容與兩位審查者的核對。

## 候選摘要

| 原始網址 | 受影響流程 | 研究判定 | 候選標題 | 候選年度 | 下一個人工門檻 |
| --- | ---: | --- | --- | --- | --- |
| [NTPU 英語組 PDF](https://cms-carrier.ntpu.edu.tw/uploads/115_1003_f908ed3fae.pdf) | 119 | 原始內容可讀 | 115學年度交換學生申請資訊一覽表(英語組) | 115 | 逐校核對 PDF 列與 828 條規定引用 |
| [NTPU 姊妹校](https://new.ntpu.edu.tw/oia/sister-schools) | 48 | 原始內容可讀 | 國際事務處 - 姊妹校 | 待確認 | 不得把合作關係清單冒充當期名額或申請規定 |
| [NTPU 中文組 PDF](https://cms-carrier.ntpu.edu.tw/uploads/115_1014_dd8dc7eafd.pdf) | 19 | 原始內容可讀 | 115學年度國立臺北大學交換生名額一覽表(中文組) | 115 | 逐校核對限制、備註與申請梯次 |
| [NTPU 日語組 PDF](https://cms-carrier.ntpu.edu.tw/uploads/115_da8ac19670.pdf) | 15 | 原始內容可讀 | 115學年度交換學生申請資訊一覽表(日語組) | 115 | 人工判讀原頁日期文字並逐校核對 |
| [CGU 雙學位可申請學校](https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533) | 12 | 原始內容可讀 | 長庚大學 可申請學校 (雙學位) | 待確認 | 確認每份流程確屬雙學位且一般期間不冒充精確期限 |
| [NTPU 舊海外合作校頁](https://new.ntpu.edu.tw/oia/overseas-partner-schools) | 2 | HTTP 200，但應用頁面顯示找不到 | 不提供 | 不提供 | 找到內容等價的現行正式頁面後，逐流程替換與雙審 |

## 失效網址的安全研究線索

舊海外合作校網址雖回 HTTP 200，頁面內容本身顯示找不到，因此不能建立任何候選標題、角色、權威或年度。現行 [NTPU 姊妹校頁](https://new.ntpu.edu.tw/oia/sister-schools) 只作為官方研究線索；目前沒有證據證明它能等價支持越南國家大學河內校與樂鴻大學兩份流程的原規定，所以固定 `eligible_as_replacement=false`。

## 真人處理順序

1. 在工作台開啟 exact URL，對照本批次候選與原始頁面。
2. 從唯讀 CSV 逐流程確認合作校、引用規定、年度、梯次及實際引用脈絡。
3. 只在已建立的個別 pending revision 中保存這次真正核對完成的來源欄位；不要批次代填。
4. 候選內容更新後重新載入比較，由兩位不同內容管理者各自勾選全部來源與規定。
5. 只有完整雙審且沒有其他發布阻擋時，才由有效核可者明確發布。

## 可重跑漂移檢查

執行 `uv run --frozen python scripts/check_source_metadata_research.py --check --timeout 30`。檢查器只讀取 manifest 與官方網址，去重後驗證最終 HTTPS、HTTP 狀態、PDF magic、HTML 應用層失效標記及候選標題；每個 response 最多檢查 1 MiB，網路錯誤或任何狀態漂移都 fail closed。它不會填值、更新查核日、建立 revision、核准或發布。

2026-08-30 實跑結果為 6 個去重網址全部傳輸維持 HTTPS：5 個 `content_available`、1 個 `not_found_page`。舊 NTPU 海外合作校頁的找不到訊息位於約 736 KiB 後，因此有界檢查上限固定為 1 MiB；這只證明目前研究頁面狀態，不能取代逐流程內容等價性與兩位真人查核。

機器可讀鏡像位於 `data-003-batch-002-source-metadata-candidates.json`；封裝 runtime manifest 位於 `src/exchange_info/official_data/review/source_metadata_research_candidates.json`，測試要求兩者完全一致。

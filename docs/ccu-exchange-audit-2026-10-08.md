# 中正大學 2027 春季校級薦外交換資料交接

查核日：2026-10-08。Repository：`blizzard-new/abroad`。
獨立 clone：`/workspace/abroad-ccu-20261008`；分支：`data/ccu-exchange-20261008`。
基準：從 GitHub 最新 main 取得 `f741d540f546d6ddbbf3174c9a34b5ef103c8816`，建分支前未發現同名遠端分支。
交付前遠端 main 已前進至 `293546e807294dc0812f390b240a4cfb68e86cd0`；本分支保留開工時基準，未重寫其他 session 工作或自行整合 main。
本 clone 未找到 AGENTS.md 或適用 `.agents/skills`。未寫入其他學校 session 的工作目錄。

## 已核實適用範圍

目前核實最新版是 [2027 春季公告](https://oia.ccu.edu.tw/p/406-1008-93586,r1714.php?Lang=zh-tw)，發布日 2026-08-18。
官方稱「2027春季」；平台 `academic_year=115` 是春季 2027 = 115 學年度第二學期的曆年換算，並非另一份官方以 115 命名的簡章。
[學校資訊](https://oia.ccu.edu.tw/var/file/8/1008/img/1130/717520038.pdf)內容日期 2026.09.17，共 121 頁；[簡章](https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf)共 8 頁，內容日期 2026.08.18。
DOC 和 ODT 內容均確認「2027春季」，家長同意書為公告當期所連結的無年度表格。
5 份檔案已保存，PDF/ODT 可解析、DOC 複合檔格式及內嵌標題可驗證；URL、SHA-256、頁數及年度見 `source-manifest.json`。
2027 秋季新版**尚未核實**；沒有把未查得新版寫成官方明示「尚未公告」。
公告本身明示部分合作校資訊仍未到、持續更新；未逐校猜測哪一份尚未公告。

## 資料筆數及完整度

`official_data/ccu/partners.jsonl` 共 **104 筆不同條目**，包含當期表中不同學院計畫及歷史參考條目；不是 104 所現在可申請。

| 狀態 | 筆數 | 處理 |
| --- | ---: | --- |
| 當期名額已列 (`open`) | 52 | 代表此梯次曾列名額；另存 `application_window_status=closed` |
| 全筆含校名灰色，官方明示本季未開放 (`not_open`) | 49 | 當期名額／資格／語言留空，灰字存 `reference_data` |
| 名額欄空白 (`needs_confirmation`) | 3 | 同奈科技 p71、Presidency p80、Pardubice p107；空白不等於零、不推定可申請 |
| 明示零名額 | 0 | 模型支援 `zero_quota`，本次來源未找到 |

p7 的灰字規則以 PDF 文字填色及表格座標讀取；部分灰字只代表該欄沿用舊資料，不能從文字抽取結果丟失顏色後當成當期。
PDF 目錄不是完整開放名單，未以目錄行數推估名額或覆蓋率。
其中 55 筆非整校灰字條目有校別流程，共 **55 筆 × 7 步驟**；另有 8 種中正專用準備工具，生成頁是個人整理工具，正式簽章申請仍用官方 DOC/ODT。

以這 55 筆當期有內容或名額待確認條目為分母：

| 當期中正 PDF 可核對欄位 | 筆數 |
| --- | ---: |
| 交換期程 | 55/55 |
| 語言原文 | 51/55 當期原文、3/55 矛盾、1/55 未載；另存強制／建議／範圍條件 |
| 合作校資格原文 | 47/55 |
| 合作校實際文件要求原文 | 37/55；8/55 待確認、6/55 未載、4/55 歷史清單。37筆亦不代表完整海外清單 |
| 合作校申請日期原文 | 55/55，保留計畫範圍，不猜時刻 |
| 學期日期 | 50/55，忠南年份矛盾不自行改正 |
| 課程限制相關原文 | 49/55 |
| 住宿相關文字或來源連結 | 19/55，不代表均有價目或保證住宿 |
| 費用相關原文 | 3/55（安卡拉明示舊資訊已移為參考），另有 Pardubice 繳學費矛盾 |
| 可單獨規範化的學制 | 4/55，其餘保留條件原文、不猜缺值 |
| 逐校精確提名截止 | 0/55 未核實；不能用學生申請截止代替 |
| 合作校 fact sheet 附件內容獨立核實 | 0/55；連結逐筆保留並標待確認／歷史參考 |

以上「當期已核實」指**中正當期官方 PDF 所載內容**，不是宣稱已經獨立查核全部海外合作校附件。
所有重要欄位有官方 URL、頁碼或原文、年度／梯次及查核日；缺值、灰字、矛盾的狀態可由 `field_evidence`、`field-audit.json`、`completeness.json` 追蹤。
住宿與價格只保留可核實資料，不生成估價。財力證明金額保留在文件欄，不混作生活費。

## 母校流程及計畫差異

- GPA ≥ 3.0 **且**歷年平均 ≥ 70；就讀滿兩學期；大二至大四上／碩博士二年級以上；交換全程保有學籍。
- 校級、院級擇一，最多 3 志願。線上申請後仍須繳交完整紙本；申請表和彌封推薦函不需線上上傳。
- 第一梯次（Thammasat）：線上 8/26 23:59，紙本 8/27 17:00。
- 第二梯次（SDU、Hokkaido、Presidency、HCMUT、Vel Tech）：線上 9/6 23:59，紙本 9/7 17:00。
- 第三梯次（其他已公告名額）：線上 9/20 23:59，紙本 9/21 17:00。以上均為 **2026 年、Asia/Taipei +08:00**，截至查核日皆已截止。
- 家長同意書在校內錄取後；在中正註冊繳費、海外校學費原則免繳，生活、機票及保險自付。
- 返國心得一個月內；抵達立即回報安全；申請表另有抵達／返國兩週內各填送教學組通知。三件事分開，不複用長庚規則。
- 北海道 HUSTEP／SA／SRS、東北 IPLA／JYPE／COLABS／DEEP、ZHAW 工學院學士／碩士、波爾多普通課程／DEFLE 分開列。
- 北海道 C1、TOEFL 79、IELTS 6.5 為官方並列原文，未自行做 CEFR 換算；SA 日文 N2 不套用 HUSTEP 門檻。
- SDU 10/1 學生申請與 11/1 住宿申請分開；Hokkaido 10/23 HUSTEP 與 11/13 SA/SRS 分開。
- 各方案名額共用全校名額，不把方案數乘上名額；海外接收條件與中正 outbound 資格分開。

## 尚待確認

`conflicts.json` 保存 8 項：簡章時程標題誤留 2026 秋季、大四專案例外、忠南學期終日年份、墨西哥語言 B2/B1、Pardubice 一般入學／交換文件與繳學費、東北 JYPE 春季適用性、St Gits TOEFL 92／80、誠信語言證明強制性。
BNU 當期 PDF 仍連向 2022/2023 系所頁，不能當成核實的 2027 課程表。
Presidency 等明示舊簡章的黑字連結也移入歷史參考，不能僅以黑色文字視為新版。
尚缺逐份合作校附件的適用年度、表格、校區、完整住宿價目與提名日核對；另缺 2027 學海補助新版（簡章 p7 仍引 2026 已過期日期）。
中正特有母校規則可用；整批流程維持 `legacy`／`official_partial`，沒有冒充雙人審核發布，也未啟用官方截止提醒。

## 檔案及合併清單

校別檔案可以獨立合併：

- `src/exchange_info/official_data/ccu/`：104 筆資料、55 筆流程、原始附件、公告快照、來源／規則／矛盾／完整度稽核。
- `ccu_sources.py`、`ccu_student_view.py`、`ccu_application_documents.py`。
- `static/ccu-academic-units.js`：中正官方 7 學院系所目錄，附官方 URL 與查核日。
- `scripts/build_ccu_catalog.py`、`scripts/build_ccu_source_audit.py`、`tests/test_ccu_support.py`、`tests/test_ccu_semantics.py`。
- `ccu_partner_semantics.py`、`ccu_language.py`、`static/ccu-language-conditions.js`：全55筆語義稽核與中正專用資格判斷。

以下共用檔需統一合併，尤其可能與臺大 session 修改同檔：

| 共用檔 | 必要變更 |
| --- | --- |
| `university_registry.py` | 加 CCU alias、7 學院、basic 覆蓋與 52 筆名額提示；不挪用其他學校校園照片 |
| `models.py` | 欄位來源與名額／收件狀態；GPA、3 志願 dashboard 與資格檢查碼；舊帳戶 GPA 空值不改既有序列化形狀 |
| `api.py` | CCU partners／pages／exchange-info／dashboard dispatch |
| `storage.py` | 只增加 CCU bundled workflow 路徑 |
| `application_rules.py`、`advisor.py` | 雙成績、3 志願、校內截止及年度待確認；中正使用逐頁人工核對的結構化語言條件；建議、範圍、矛盾及未選定分流不硬判；其他母校保留既有解析 |
| `application_documents.py` | CCU 專用模板及查核日 dispatch |
| `application_workflow_collector.py`、`cli.py` | CCU 校別來源，避免 generic CGU 流程及不必要網路抓取 |
| `static/app.js`、`static/index.html` | GPA 保存／回填、3 志願、收件截止及灰字／空白狀態、逐欄證據、系所 JS 載入 |
| `docs/api/openapi.json` | 由專案 export script 完整重建，與 live schema 一致 |
| `pyproject.toml` | package data 納入 CCU DOC／ODT |

未修改既有 CGU／NTPU 資料檔、NTU 檔、憑證、權限、付款／安全設定。未 merge 或部署。

## 實際驗證

- 中正新增測試：**16 passed**；最終中正＋條件保存回歸 **24 passed in 3.88s**。涵蓋筆數、重複、必填來源、版本／灰字／空白、文件檔案、矛盾、日期分組、計畫條件、GPA＋平均、3 志願、API／搜尋／流程、模板與前端學校切換。
- 擴大回歸：**107 passed, 5 skipped, 2 failed in 57.39s**。跳過由既有 root `conftest.py` 設定，未修改或新增跳過。
- 兩項失敗在以 `git archive f741d54` 建立的 `/tmp/ccu-baseline-f741d54` 原始基準亦重現：
  - `test_runtime_includes_tracked_ntpu_public_baseline_with_isolated_private_data`：destination profile count 預期 1 實際 0。
  - `test_college_selects_ignore_partner_notes_and_follow_home_university`：既有 Node 測試 stub 缺 `renderApplicationPeriodOptions`，ReferenceError。
- Python 編譯、兩個 JS `node --check`、`git diff --check` 通過；wheel 建置成功，8 項必要中正資源皆有打包。
- 原 CGU／NTPU bundle 對基準逐檔 byte 比對無改動；CGU 77 destination profiles，NTPU 206 partners = 169 當期＋37 協議參考。
- 2 次離線 rebuild 輸出 hash 一致；見 `official_data/ccu/validation.json`。
- uv 預設家目錄 cache/tools 遇到唯讀錯誤，已改用 `/tmp/ccu-uv-*`，環境安裝與格式工具均成功，沒有更改存取權限。

可重跑：

```bash
UV_CACHE_DIR=/tmp/ccu-uv-cache uv sync --frozen --extra dev
.venv/bin/python scripts/build_ccu_catalog.py
.venv/bin/python scripts/build_ccu_source_audit.py
.venv/bin/pytest -q tests/test_ccu_support.py
node --check src/exchange_info/static/app.js
node --check src/exchange_info/static/ccu-academic-units.js
```

`build_ccu_catalog.py` 預設離線，`--refresh` 僅抓中正官方附件，五個檔案的格式、頁數和2027春季標題全部核對後才覆寫；內容不符會失敗，跨查核日刷新須先更新來源查核日；不寫其他學校 bundle。
新年度、來源日期或 PDF 排版改變時需重新讀內容及更新 `STARTS`／`ccu_sources.py`，不能把這次快照当成通用自動年度推斷。


## 第一輪交付缺漏修正（2026-10-08，後續仍繼續深查）

已重新讀全55筆當期語言與文件欄。提名前提另存 `partner_application_prerequisite`，不計為文件涵蓋；p32/p33/p39的灰字文件與p105明示舊資訊列歷史參考。連結／程序亦不計為實際要求。
語言條件保存必須／建議、檢定種類、學制、track、合作校學院／授課語言範圍、額外單項条件及原文證據；只有人工核對的無分流強制分數可自動比對。
`semantic-review-lock.json` 鎖定逐頁語言與文件原文 hash，來源變動會要求重讀語義，不能默用舊分數。

OpenAPI 由 `.venv/bin/python scripts/export_openapi.py` 產生，`--check` 通過。
差異審閱：路由無增刪或定義變動；新增 `ExchangeFieldEvidence`、`PartnerLanguageCondition` schema，更新6個既有schema（GPA、來源、名額狀態、語義條件與提名前提）。沒有新增必填輸入或移除欄位；回應新增enum值，嚴格列舉的舊client需更新未知值處理。契約版本維持 live 程式既有 `2026-10-02.1`，權限與產品邊界未改。

契約套件修正前 **13 failed / 7 passed**，重建後 **12 failed / 8 passed**；凍結快照與 live 一致的測試已通過。其餘12個失敗為既有路由、header及權限契約落差，失敗集合與修正前扣除快照測試後一致，沒有刪改測試或設定來掩蓋。
中正語義／API／前端、GPA保存及CGU／NTPU語言規則回歸 **91 passed**；另記本次最終實際耗時於 `validation.json`。
沒有修改 `.github/workflows/quality.yml`，沒有把既有零jobs CI失敗說成通過。

本批只修正審查問題，不是全部交換生資料的最終完成；海外附件逐份查核仍繼續，逐校逐欄矩陣會保存新來源及真正無法確認的原因。


## 海外資料 checkpoint（2026-10-08）

本批補入55校×17類海外欄位、55份生活指南與每校7步流程；127筆來源紀錄（124個不同URL）包含47筆PDF、2筆DOCX、66筆HTML及12筆失敗。27校有當期海外依據，213/935欄當期可核實，尚無一校17類全數核實；24欄來源矛盾、151欄適用待確認、31欄歷史參考、515欄缺值、1欄官方TBC。完整矩陣、逐校問題與來源快照已保存；不把下載成功或未標年度資料計為當期。115項功能與回歸測試通過；既有資料測試62通過/4跳過/1個已重現基準失敗，契約8通過/12個既有失敗，集合與前次一致。

本checkpoint仍在完成生活頁的瀏覽器驗證及最終交接文件，不宣稱55校完整。遠端main已到f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59，本分支未整合或改動其他session。

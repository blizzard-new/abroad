# 中正大學 2027 春季校級薦外交換資料交接

查核日：2026-10-08。Repository：`blizzard-new/abroad`。
獨立 clone：`/workspace/abroad-ccu-20261008`；分支：`data/ccu-exchange-20261008`。
基準：從 GitHub 最新 main 取得 `f741d540f546d6ddbbf3174c9a34b5ef103c8816`，建分支前未發現同名遠端分支。
交付前遠端 main 已前進至 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`（第一批交付時為 `293546e807294dc0812f390b240a4cfb68e86cd0`）；本分支保留開工時基準，未重寫其他 session 工作或自行整合 main。
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
| 母校表單可獨立列出的海外提名截止 | 0/55；海外新查15/55另列，不以學生申請截止代替 |
| 母校 PDF 的 fact sheet 連結欄 | 不用連結本身推定附件已核實；海外內容與年度另見下方查核表 |

以上表格僅計**中正當期官方 PDF 所載內容**；海外附件與校方原始頁面的独立查核另列，不把兩種來源覆蓋率相加。
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
海外查核已逐校保存，仍缺的適用年度、表格、校區、完整住宿價目與提名日詳見 `confirmation-questions.json`；另缺 2027 學海補助新版（簡章 p7 仍引 2026 已過期日期）。
中正特有母校規則可用；整批流程維持 `legacy`／`official_partial`，沒有冒充雙人審核發布，也未啟用官方截止提醒。

## 檔案及合併清單

校別檔案可以獨立合併：

- `src/exchange_info/official_data/ccu/`：104 筆資料、55 筆流程、原始附件、公告快照、來源／規則／矛盾／完整度稽核。
- `ccu_sources.py`、`ccu_student_view.py`、`ccu_application_documents.py`、`ccu_overseas.py`。
- `static/ccu-partner-details.js`：逐欄來源、年度、缺值、矛盾及生活資料呈現。
- `static/ccu-academic-units.js`：中正官方 7 學院系所目錄，附官方 URL 與查核日。
- `scripts/build_ccu_catalog.py`、`scripts/build_ccu_source_audit.py`、`scripts/fetch_ccu_overseas_sources.py`、`scripts/build_ccu_overseas.py`，及3份 `test_ccu_*.py`。
- `ccu_partner_semantics.py`、`ccu_language.py`、`static/ccu-language-conditions.js`：全55筆語義稽核與中正專用資格判斷。

以下共用檔需統一合併，尤其可能與臺大 session 修改同檔：

| 共用檔 | 必要變更 |
| --- | --- |
| `university_registry.py` | 加 CCU alias、7 學院、basic 覆蓋與 52 筆名額提示；不挪用其他學校校園照片 |
| `models.py` | `PartnerExchangeDetailField` 與17類接收資料；欄位來源與名額／收件狀態；GPA、3 志願 dashboard 與資格檢查碼；舊帳戶 GPA 空值不改既有序列化形狀 |
| `api.py` | CCU partners／pages／exchange-info／dashboard dispatch |
| `storage.py` | 增加 CCU bundled workflow 及 destination profile 路徑；以母校+合作校 identity 保存 |
| `application_rules.py`、`advisor.py` | 雙成績、3 志願、校內截止及年度待確認；中正使用逐頁人工核對的結構化語言條件；建議、範圍、矛盾及未選定分流不硬判；其他母校保留既有解析 |
| `application_documents.py` | CCU 專用模板及查核日 dispatch |
| `application_workflow_collector.py`、`cli.py` | CCU 校別來源，避免 generic CGU 流程及不必要網路抓取 |
| `static/app.js`、`static/index.html` | GPA 保存／回填、3 志願、收件截止及灰字／空白狀態、逐欄證據、系所與接收資料 JS 載入；生活頁同樣顯示歷史／待確認項，避免通用 renderer 隱藏28校資料 |
| `docs/api/openapi.json` | 由專案 export script 完整重建，與 live schema 一致 |
| `pyproject.toml` | package data 納入 CCU DOC／ODT及合作校DOCX表格；原JSON通配涵蓋來源子目錄 |

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

上述為第二個commit的歷史驗證。最新海外來源、真正缺值與未解項已保存下列交接，不宣稱55校資料完整。


## 海外資料 checkpoint（2026-10-08）

本批補入55校×17類海外欄位、55份生活指南與每校7步流程；127筆來源紀錄（124個不同URL）包含47筆PDF、2筆DOCX、66筆HTML及12筆失敗。27校有當期海外依據，213/935欄當期可核實，尚無一校17類全數核實；24欄來源矛盾、151欄適用待確認、31欄歷史參考、515欄缺值、1欄官方TBC。完整矩陣、逐校問題與來源快照已保存；不把下載成功或未標年度資料計為當期。115項功能與回歸測試通過；既有資料測試62通過/4跳過/1個已重現基準失敗，契約8通過/12個既有失敗，集合與前次一致。

本checkpoint仍在完成生活頁的瀏覽器驗證及最終交接文件，不宣稱55校完整。遠端main已到f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59，本分支未整合或改動其他session。

## 海外來源與平台適配最終交接

Checkpoint `abce2c7ec1d6184031ba36cc45910f3b7f2d6e69` 已推送；後續補查4個官方表格入口，來源紀錄為 **131筆、128個不同URL**。47筆PDF來源及2筆DOCX已下载並解析（UESTC中文掃描頁以渲染圖人工核對）；68筆HTML包含介紹／JS載入頁，不能把HTML成功下載等同已核實表格。14筆取得失敗分別保留HTTP／連線錯誤。來源全文、SHA-256、正文年度、計畫、查核日、連結及取得結果存 `overseas_sources/`；47筆PDF是取得紀錄數，部分官方重下載有重複内容，不能宣稱47份不同當期簡章。

所有55筆當期名額已列或名額空白條目都有17類接收資料查核，49筆本期未開放資料仍只保留母校歷史參考。`partners.jsonl`增加`partner_exchange_details`，每個值保留自己的海外適用年／計畫及來源；不把海外2026/27與母校115學年度欄位相互覆寫。缺值維持null，歷史值僅在有reference標籤的欄位顯示。

| 海外欄位狀態 | 數量／935欄 |
| --- | ---: |
| 已核實當期來源所列事實 | 213（22.8%）；仍不代表整欄細節或文件清單完整 |
| 適用年度／條件待確認 | 151 |
| 歷史參考 | 31 |
| 來源矛盾 | 24 |
| 缺值／當期未核實 | 515 |
| 官方明示TBC | 1（HUFS迎新日，沒有將未載截止冒充官方尚未公告） |

**27/55校**有至少一項當期海外事實；**0/55校**的17類資訊全數已核實。當期海外提名截止15校、學生申請截止20校、實際文件要求18校、校曆19校、住宿20校、費用16校、課程17校、保險16校。文件欄只列已讀到的要求，不保證完整性；取得程序、登入後表格、科系／學制附加條件仍另列。

具體新核實與未解項：

- 釜山：中正鏡像404，合作校替代PDF檔名2026Fall但封面與內頁為2026/2027，依正文核實。2027春季提名10/20、申請10/30；英文文件、按護照國籍的認證與銀行附加額、學分、宿舍／餐費、保險與校區分配均分開保存。
- HCMUT：學生專用DOCX實際下載及全文／表格解析，保存於`partner_forms/p67-student-academic-form.docx`；它本身未標年，由2026/27當期factsheet的學生連結取得，與scholar／staff表分開。8項required attachments、親簽宣告及課程計畫均已讀；同份factsheet的簽證段卻混入京都／日本CoE，保留矛盾。
- Hokkaido：HUSTEP／JLCSP／SA學士／SA研究生／SRS分開，複合欄附每個相關頁的證據。SRS不授學分；提名9/25、申請11/13與HUSTEP/JLCSP10/23不同。TAO表提名後提供，不假稱公開表已取得。
- Strasbourg：頁面明确2026/27第二學期第二campaign提名／申請10/1；同頁錄取結果仍2025年，另標矛盾，不自行順延截止。
- Østfold：2027春季提名／申請頁、bilateral清單和2026/27校曆已讀；春季2027-01-04至06-18含迎新／考試。factsheet頁仍2024/25；住宿合約1/1–6/30是租期，不能當授課期間。
- Thammasat：新檔名2027-28，正文只載更新2026-07-20及一般月份，沒有明示適用年；申請文件及學院語言條件保持待確認。月費總表與分項合計不同亦保留矛盾。
- Mapua春季截止2027-11-30晚於學期、Sungshin無效2027-02-29及舊年校曆、Kyungsung春季文件內秋季宿期、ZHAW碩士intro week37、Silesian春季2027截止卻寫2027年10/11月、TomasBata價單July2025及合計差異等均不自行修正。
- 忠南兩份公開GoogleForms實測401，未登入；FGES母校Spring提名表可讀但未標年，且不是學生申請表；Uninter MicrosoftForms HTTP200僅Loading，公開瀏覽器遇ERR_CERT_AUTHORITY_INVALID，未更改憑證或信任設定。這些不算完整本期表格。
- 3個母校名額空白、2027秋季中正新版、2027學海補助，以及各校個別提名通知、文件版次、住宿申請／付款日、費用與計畫適用仍須承辦確認。`confirmation-questions.json`逐校逐欄列具體問題、參考值、證據及失敗紀錄；没有對外聯絡學校。

平台中55份流程改成7步，在海外申請之後加入校曆／住宿／保險／抵達步驟；只有當期核實的實際文件要求進入required documents，歷史清單不混入必交。日級日期、多計畫日期與矛盾不補午夜timestamp、不開提醒。55份生活指南有8個來源欄；詳頁與生活頁都逐欄顯示年度、查核日期、原文、缺值和矛盾，歷史價格不被通用renderer隱藏或改稱current。

UBM、EPITA、SDU的新接收資料顯示替代語言證明／program分流或與中正門檻差異，中正資格判斷改為待確認。其他母校維持原有語言解析，沒有以當期海外推薦分數硬判中正學生。

最終驗證：中正資料／API／前端／生活頁及CGU、NTPU選校規則 **116 passed**；既有資料套件 **62 passed、4 skipped、1 failed**（NTPU既有destination count基準失敗）；OpenAPI契約 **8 passed、12 failed**，與前階段既有失敗集合一致。無新增skip或改CI。CGU/NTPU15檔逐byte比對原始main零變更；CGU77生活指南、NTPU206筆（169當期/37協議）不變。OpenAPI快照新增1個接收欄位schema和PartnerUniversity可選欄位，沒有route變更／新增必填輸入。離線重建12個輸出hash一致；wheel驗證來源子目錄、生活指南、DOCX與JS均有打包。具體耗時、hash及結果見`validation.json`。

瀏覽器檢查包括Mapua桌面1440×1000、釜山手機390×844、重慶歷史資料1024×900：每個詳頁17欄、流程7步、生活8欄，無page error或水平溢出。預覽證據見[桌面](ccu-validation-2026-10-08/ccu-overseas-desktop.png)、[手機](ccu-validation-2026-10-08/ccu-overseas-mobile.png)、[歷史生活資料](ccu-validation-2026-10-08/ccu-life-reference.png)。

可重建／驗證：

```bash
.venv/bin/python scripts/build_ccu_catalog.py
.venv/bin/python scripts/build_ccu_source_audit.py
.venv/bin/python scripts/build_ccu_overseas.py
.venv/bin/python scripts/export_openapi.py --check
.venv/bin/pytest -q tests/test_ccu_overseas.py tests/test_ccu_semantics.py tests/test_ccu_support.py tests/test_advisor.py tests/test_application_rules.py tests/test_ntpu_support.py tests/test_selection_conditions_sync.py
.venv/bin/python scripts/fetch_ccu_overseas_sources.py --output /tmp/ccu-next-source-candidates
```

海外fetch腳本只向已記錄公開來源取資料，記錄真實成功／失敗，候選目錄不可放在reviewed bundle內。下載成功仍是needs_confirmation，未標年/不同program不自動升為當期；修改正文或表格hash會要求重新查核。此次整理保留整批legacy／partial狀態，沒有正式發布、merge main或部署。

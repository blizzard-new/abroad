# 中正大學 2027 春季校級薦外交換資料交接

查核日：2026-10-08。Repository：`blizzard-new/abroad`。
獨立 clone：`/workspace/abroad-ccu-20261008`；分支：`data/ccu-exchange-20261008`。
基準：從 GitHub 最新 main 取得 `f741d540f546d6ddbbf3174c9a34b5ef103c8816`，建分支前未發現同名遠端分支。
交付前遠端 main 已前進至 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`（第一批交付時為 `293546e807294dc0812f390b240a4cfb68e86cd0`）；第一批交付保留開工基準；第二輪依使用者要求安全整合此最新main，保留臺大與既有資料，未寫入其他session工作目錄。
本 clone 未找到 AGENTS.md 或適用 `.agents/skills`。未寫入其他學校 session 的工作目錄。

最新數量、功能對照與實際驗證見末節第十八輪及 [55筆功能對照](ccu-functional-parity-2026-10-08.md)；前節保留歷史檢查點，不能取代最新數字。

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

## 第一階段海外來源與平台適配交接（歷史檢查點，以下數量已由第二輪更新）

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


## 第二輪可審查檢查點：最新main整合與官方深查

本輪不是全資料完成。從已推送 `bd740bc29ce76e4704a8bca4f6809f3c3769f71c` 繼續，安全合入 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59` 的臺大功能，未force push、merge回main或部署。CGU/NTPU/NTU與既有`data`共49份main資料檔逐byte不變；證據在`ccu-validation-2026-10-08/preservation-latest-main.json`。

中正仍為104所：52有當期名額、49未開放協議參考、3空白名額；55申請流程／生活指南。海外取得紀錄172份（增加41），56個欄位已新增或修正，缺值515→467。當期已核實215/935（23.0%）、待確認182、其他年度／梯次參考41、矛盾29、官方明示TBC1；28/55校至少一欄當期核實，0/55校全17欄核實。

| 查核工作進度 | 欄數 | 實際含義 |
| --- | ---: | --- |
| 已有當期依據 | 215 | 僅本欄所列事實，不保證清單或所有細節完整 |
| 官方明示未公告 | 1 | 只有HUFS迎新TBC，無把缺值改稱未公告 |
| 個別通知／須校方釐清 | 38 | 29矛盾及實際通知／授權限制；未登入或聯絡 |
| 已查入口技術失敗 | 2 | Augsburg申請入口404、Ludwigshafen418；替代入口仍可續查 |
| 官方替代來源尚未查完 | 679 | 含已取得尚未映射段落、年度／身分未核，繼續查，不當作阻塞結案 |

`research-gap-audit.json`把55×17欄逐一分類，保存本校已查URL、實際日期／時間及結果；舊快照00:00Z只聲明日期精度，不假裝精確讀取時間。`acquired-content-review.json`列17類關鍵字候選及本輪人工重讀欄位，索引不當作已核實證據。`source-failure-followup.json`列14個原失敗來源的實際重試，東北師大首頁200，其餘13原入口仍失敗，均列安全替代入口結果。來源失敗不代表全校全部資料不存在。

本轮具體修正：

- 釜山：全文重讀2026/27 PDF14頁`STUDY PLAN [FORM #1]`、15頁`AFFIDAVIT OF SUPPORT [FORM #2]`、直系支持人原則／銀行與親屬證明／簽名日期／non-OECD郵寄條件；保存可讀原PDF並在UI加頁碼錨點，移除「附表未查得」的錯誤結論。
- HCMUT：2026/27 PDF迎新明載2026年12月下旬／2027年初，補入arrival，沒有造精確報到日。中正轉載10/15與同梯次合作校10/1無延期依據，兩者一律列跨來源矛盾；9/15提名保持分開。
- UESTC（中正11/30／合作校12/31）、Chitkara（10/20／10/30）、EPITA（10/30／10/31）同梯次申請截止一併標矛盾；Østfold2027入口11/1與現行共用DOC11/15也保留矛盾。原中正文字留在`reference_data.partner_application_deadline`，主要欄、摘要、home field evidence、卡片、詳頁與workflow均顯示比較，不任選較晚日期，不開精確提醒。
- Østfold：當前bilateral文件頁仍連完整`rev2018.doc`，讀全部DOC實際內容，年度20__/20__、課程ECTS、語言、學生及母校簽名／上傳要求；以現行連結核實「取得方式」，不以舊檔名排除或把11/15當本期延期。保險是共用模板一般建議，2027及國籍適用待確認。
- Ostfalia：可讀替代交換頁與2027夏季正式校曆已取得；3/1授課開始、7/9授課末，考試另公告。一般估算費用、非EHIC保險、住房自申請、offer後2日接受均未標2027，保留待確認，房屋接受2日不是統一申請截止。
- 東北師大：官方交換、住房及保險入口取得；交換正文明載「非中國籍」且未標年，保留一般資訊及臺籍流程未核，不能將X1/X2或11/20 deadline套臺籍當期。
- 常磐：官網所連6頁guideline只載FALL且未標年；文件、住房、費用及保險以其他梯次參考保存，不混入2027春季必交文件。SDU完整語言表已讀簽章，但88分與中正83／現行B2文字另記適用性差異。
- Augsburg：當期PDF官方Application-and-Arrival連結及其他安全入口實測404。沒有把搜尋摘要或別處可見的七類文件冒充已全文取得；繼續列技術失敗及替代查核工作。

共享合併範圍：registry、API與storage四校dispatch；advisor與application_rules維持中正GPA3.0 **且** 平均70、最多3志願，保留臺大GPA/排名擇一與研究生豁免；文件入口、collector／CLI、model可選接收證據與查核狀態、主UI/index、OpenAPI及wheel資料包含。NTU舊資料的空CCU欄不額外序列化，NTU離線重建仍逐byte相同；既有GPA4.3輸入上限保留。其餘爬取、人工來源與renderer均校別獨立。API共110 routes，沒有增加必填欄位；沒有修改憑證、權限、付款或安全設定。

實際驗證：最後參考標籤修正後中正專用 **87 passed**；資料／資格／文件／四校回歸 **208 passed、5 skipped、1 failed**（最新main同一NTPU destination count失敗）。既有前端契約 **8失敗** 與最新main逐名稱相同；API契約 **8 passed、12 failed** 與最新main相同，不隱藏失敗、不增skip。實機瀏覽器中正桌面／手機、四校切換、臺大GPA排名／保存條件／新TOEFL／文件語組共 **10個不同案例已通過**（四校案例初次因測試未等待onboarding失敗，修正測試進站流程後重跑通過）。中正兩種螢幕無page error或水平溢出；證據與實際log保存在本交接驗證目錄。OpenAPI快照檢查、JS語法、ruff、git diff檢查通過；16份離線輸出重建hash一致；wheel含DOC/DOCX/PDF、來源、查核分類與校別JS。

本輪仍剩467缺值欄及其他年度／條件、個別通知與矛盾核對工作；3空白名額、2027秋季新版／補助尚未核實，不等同官方未公告。Draft PR是可審查資料與適配檢查點，後續依工作佇列續查；無聯絡學校、無建立校方帳號、无繞過憑證警告。

重建順序先跑`build_ccu_research_audit.py`，再依前節順序重建catalog、source audit、overseas。第二輪實際結果與hash見`validation.json`的`second_pass`，第一階段資料保留為歷史驗證。

## 第三輪可審查檢查點：公開新入口、表格正文與矛盾分類

從已推送`51a254cc96a76b5785b8e54b2f4e8fd6f30c6b70`繼續，獨立分支仍為`data/ccu-exchange-20261008`。2026-10-08再次讀取遠端main，仍為`f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。本輪沒有改其他session目錄，也沒有merge回main或部署。前兩輪數字與測試是歷史檢查點，最新進度以本節及`validation.json.third_pass`為準。

新增**30份實際取得紀錄**，共202份；其中新紀錄25份可讀、5份取得失敗。修改45個欄位，補上34個原缺值欄位；新增來源不等於新增當期事實，同一Augsburg英德內容沒有重複計算。104筆學校條目、52笔名額已列、49筆未開放參考、3筆名額空白、55份7步流程與55份生活指南不變。52筆名額表示2027春季表曾列席次；中正校內2026年8月至9月申請已截止。

| 接收端欄位狀態 | 最新數量／935欄 |
| --- | ---: |
| 當期來源支持已列事實，仍可能只有部分要求 | 237（25.3%） |
| 適用年度或條件待確認 | 192 |
| 其他年度／梯次參考 | 41 |
| 來源矛盾 | 31 |
| 缺值／當期未核實 | 433 |
| 官方明示TBC | 1 |

29/55校至少一項當期事實，0/55校17欄全部核實。沒有將讀取成功、一般未標年网页、模板、排名年或照片年提升為本期完整。

本輪已核對：

- **Augsburg**：官方新路徑英德頁均已讀，六類附件、Design/Architecture/Civil Engineering的portfolio、Non-EU LA三方簽名與兩校STAMP、15–30 ECTS建議及先修/准入均保存。這些指引未標適用年度，保持待確認。Mobility-Online公開空白表實際有2026/27、SS2027選項，取得方式可核；沒有提交或登入。當期factsheet較精確的3/1–3/3抵達、3/4–3/14迎新保留。LA原始下載429仍記錄，另由web工具讀到完整一頁PDF；SHA明示是提取回應，沒有冒稱原始PDF已下載或HTTP200。
- **Ludwigshafen**：直接查Your application子頁，shell418另保留，web工具取得三步公開正文：JPEG照片、護照PDF、online提交後產生PDF、母校coordinator簽名，再依指引email送LA與住宿表。實際下載並讀取LA DOCX及住宿PDF；住宿檔名2026但正文summer2027，2/22起可住、2/22–2/25 move-in，偏好公寓不保證。沒有獨立住宿付款截止；LA含Erasmus grant模板文字，不能當中正雙邊獎助資格。個人PDF須建立帳號並提交後產生，該部分未取得，公開附件不再整體標技術阻塞。
- **SeoulTech**：重讀2026/27 factsheet第4–5頁，每伙伴每期最多2人、前兩期無SeoulTech赴伙伴則僅1席。這是接收端互惠規則；中正名額原文「一學期2名或一學年1名」未改，不冒充個人GPA條件。
- **Kyungsung／FGES**：重讀已有當期PDF，不重掃首頁。Kyungsung英語Global College範圍與一學期期間補上，研究所介紹不推定皆開放；email送件方式已讀但附件名稱仍缺。FGES第2頁Spring2027迎新為1月第一週，沒有精確日期；第3頁語言證明必繳、B2僅advised，文件欄只列這個已知要求並明說不是完整清單。
- **Pardubice**：Other exchange頁正文Academic year2026/27及2026年summer附件期限支持當期申請、B2替代證明、照片與LA、院系補要求、住宿/visa文件程序。指定LA DOCX實際讀取並保存；雖稱freemover模板，由當期Other exchange頁直接指定，不套grant/doctoral模板期間。正式Rector PDF適用2026/27，summer考試5/17–7/4另有8/16–8/31，faculty可調整；網頁簡表漏列後段，不能保證7/4即可離校。coordinators頁標題2026/27但段落2025/26，提名截止獨立列矛盾；中正名額仍空白，不提升為可申請席次。
- **Deggendorf／West Bohemia／Chiba**：Deggendorf Summersemester2027授課3/15–7/9，但同區exam/break寫2026，保留矛盾；summer2027學生服務費EUR87單獨保存，整體生活預算仍未核。West Bohemia2026/27課程篩選入口可讀但課目明細未取得，住宿子頁summer12/10預約費未標年。Chiba新查頁只有2026年10月校曆與一般外國留學生支援，不拿來填2027春季交換缺值。
- **Chitkara**：Inbound公開頁五類附件、一般semester/short mobility/internship範圍已讀，未標2027而保留待確認。52,662,368 bytes brochure確實下載，29頁全OCR，第23及25頁再視覺核對；只補一般住宿支援，不填沒有的費率、簽證、保險或床位保證。一般Spring第二週10月与当期factsheet10/30、中正10/20三種來源及範圍分開，不推延當期截止。

查核進度重新分類：**237已支持、1官方TBC、31未解來源矛盾、10個別通知/登入後個人表、0整欄技術失敗、656公開替代來源未查完**。0技術失敗欄不表示每一URL都成功（202份紀錄仍有39份失敗）；只表示不再因一個入口失敗就整欄判阻塞。31個矛盾使用新增`unresolved_source_conflict`，不一律假稱登入或需聯絡校方。沒有對外聯絡、註冊、送件或改憑證。

本輪共用處只有`models.py`接收欄位研究狀態enum及其生成的`docs/api/openapi.json`；其他修改均CCU資料、研究分類/完整度腳本、CCU校方資料讀取驗證與renderer、測試及交接文件。全分支最終合併清單仍見前節共用檔表。web提取回應增加SHA驗證，文字提取與原始文件hash分開；新PDF/DOCX三份保存於CCU `partner_forms/`，已有package通配實際包含。

本輪實際驗證：

- CCU全套**96 passed in 26.97s**，新來源9項於最後分類說明修改後再驗證**9 passed in 1.17s**。初次新測試兩項誤用API模型沒有的source_id，改以模型已有source_url斷言後通過，初次log也保留；未修改資料去迎合錯誤測試。
- 四校資格/資料回歸**130 passed、4 skipped、1 failed in 17.83s**；唯一NTPU destination count仍是第二輪已在main獨立副本重現的同名失敗，未改skip/CI。
- 實機**9 passed in 61.81s**：Augsburg/Ludwigshafen/Deggendorf手機390與桌面1440、新來源/年度/矛盾標籤、原有HCMUT/釜山與四校成績控制；無pageerror或水平溢出。Ludwigshafen個人表查核說明最後再跑兩個viewport：2 passed、7 deselected in 13.56s，結果另存證據。
- 49份main既有CGU/NTPU/NTU及公開資料逐byte仍零變更；16個CCU離線輸出重建hash一致；110個API route及既有required欄不變，OpenAPI快照檢查與Python/JS語法、format、diff檢查通過；wheel實際讀取新表格與来源/JS。

最新快照、原文與每欄時間在`official_data/ccu/overseas_sources/`及`overseas-reviewed-fields.json`；45項差異在`third-pass-changes.json`。測試與package/rebuild證據在`docs/ccu-validation-2026-10-08/`；手機/桌面截圖為`ccu-public-*-*.png`。

剩餘656欄仍需深查公開官方來源，433個缺值、31個矛盾及各校未標年度/院系/費率/完整文件/住宿期限不能稱已完成；10個私有表或個別通知只表示已讀原文中的取得限制，不排除其他公開替代來源。2027秋季中正新版及學海新版尚未核實，未改稱官方尚未公告。這仍是可審查檢查點，PR維持draft。


## 第四輪：六校附件全文與存取結果核對（仍持續第五輪）

从`8c14e949a219a43668ad62783e87c424b65723be`續作；遠端main仍為`f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。新增39筆實際取得紀錄，總241筆；更新22欄，其中14欄原先缺值。104筆學校、52筆已列當期名額／49筆未開放參考／3筆名額空白、55份流程及生活指南保留；52筆名額不是目前正在受理，中正校內當期截止已過。

935欄現為當期已核實245（26.2%）、待確認197、歷史參考41、來源矛盾32、缺值419、官方明示TBC1。29/55校至少一項當期依據，0校全17欄已核實。查核工作分類245已支持、1官方TBC、32未解來源矛盾、10個別通知/登入後個人表、0整欄技術失敗、647其他公開来源未查完；不宣稱研究完成。

天津2頁、電子科技2頁、華中師範22頁、Saintgits4頁、Opava管理學院9頁、Uninter10頁均全文重讀。`semantic-review-ledger.json`逐校逐欄區分已讀未載、已映射、舊年度及實際取得限制；關鍵字候選不再冒充尚未讀完。母校條件仍與海外接收端分開。

- 電子科技：兩頁圖像全文視覺核對，補選拔、保留母校學籍、一學期上限、不得打工、期滿返臺、保險開學一週內購買、不可指定宿舍及申請材料不退件。中文OCR仍有錯字，證據只用人工核實段落；原PDF實際保存並核SHA。學雜費句子同時說「繳交」與「費用由本校負擔」，協議可另規定，保留待確認，不造免學費。
- 華中師範：當期申報表除簽名外簡體打印，推薦函學校章、體檢醫院章完整補入。公開incoming規則與下載只找到2016版，舊附件下載要求驗證碼，沒有取得DOC或解碼；新版申報表未核實，不把舊研修/住宿表加入當期必繳。
- Opava：校方七個子頁實際HTTP200為Anubis限制頁，非課程/住宿政策讀取成功；兩個UESTC入口HTTP202正文空白，另有CCNU旧附件驗證碼頁。上述10個限制/空白紀錄保存`access_result`，新增檢核防止提升為當期政策。241筆取得紀錄另有52筆`fetch_failed`，這些數目不等於整欄研究無法繼續。
- Opava公開mobility：匿名GET實讀2026/27 Partner university students入口及Taiwan國家選單；與staff、freemover virtual分開。完整後續字段仍未取得，沒有建立申請。校方保險EUR60000與捷克內政部/外交部現行長期EUR400000且無自負額明确矛盾；國籍、停留、協定豁免及現行查核時點分開，不保證2027法規或中正Erasmus豁免。
- Saintgits：一般六棟宿舍資訊僅待確認線索；公開exchange頁是赴UMass Lowell學位2+2/3+1，不能套中正incoming。Uninter補接收計畫、當期已知期間與buddy服務，但2027迎新錯寫2026的矛盾保留。

實測：CCU **103 passed**；四校資料/流程範圍 **194 passed、5 skipped、1 failed**，唯一失敗是已在main重現的NTPU既有destination計數測試；CCU真實Chromium **9 passed**。16個離線產物重建SHA完全一致；49個既有main資料檔無byte變更，110條API route及必填schema無變更。完整實際log在`ccu-validation-2026-10-08/fourth-pass-*`。

本批修改學校獨立資料、`ccu_overseas.py`及兩個CCU離線build script；沒有本輪新增核心registry/API/UI共用改動。全分支必要共用改動仍以前述清單為準。Draft PR#3維持draft，沒有merge或部署；接續第五輪公開來源查核。

第四輪靜態檢核初次發現18項CCU檔案的import/格式/明示subprocess check選項問題，已修正後ruff全數通過；修正後CCU重跑103 passed（28.14秒）。沒有隱藏初次結果，原log另保留。


## 第五輪：校級協議、公開嵌入表與年度範圍核對

從已推送`05a72ffdc2d68dec018d2970db16e026968933a1`續作，遠端main實讀仍為`f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。新增79份實際取得紀錄（其中78成功取得、1實際失敗），共320份。更新65欄，補48個原缺值；104筆學校、52筆當期曾列名額、49筆不開放參考、3筆名額空白、55份七步流程/生活指南保留。中正校內2027春季當期收件已截止。

935欄現在為當期原文支持272（29.1%）、待確認214、參考40、來源矛盾37、缺值371、官方明示TBC1；33/55校至少一項當期事實、0校全部17欄當期已核。來源紀錄另有53份fetch_failed及10份限制/空白回應；不以這些數字宣稱全部官方資料不能取得。研究分類272已支持、1官方TBC、37未解矛盾、10個別通知/登入後個人表、0整欄技術失敗、615其他公開來源仍可續查。沒有以檢查點或PR表示研究完成。

- 名古屋：完整2026/27 NUPACE第32頁列中正`*U`，第29頁定義校級/院系及豁免，支持中正校級協議，原2頁Interdepartmental版保留且補正其正文年度。春季提名2026-10-01、學生申請2026-10-15；GPA3.0/4.0、JASSO3.1另計畫、英/日語分流、15學分或15研究小時分開。當期十項文件與一/兩學期财力、lab/GIS限制、日程/住房/校方保險/簽證/條件式免學費已逐段核對；七份指定DOCX/PDF實際開啟保存。邀請式online完整字段未取得，application_forms整欄仍待確認。未把2025示例課程或醫學實習條件套一般本科。
- 嘉泉：公開GoogleSites實際`data-code`表支援2027正規Spring03-02至06-21；宿舍頁明示2027-06-19退宿，與課程末日分開。費率嵌入表明示2025 prices，只参考；沒有升為2027費率。GPA官網沒寫recommended、母校附件寫recommended，保留矛盾。Timeline有February抵達但Dec21學期末，年/梯次未明，保留矛盾。公开DOCX/PDF模板已實開，但未標2027，保留待確認；不同track、碩士/本科、medicalcampus及國籍認證分開。
- 中央大學：新OIA公開公告正文明示2026FallFactSheet，已讀六頁，沒有只憑檔名推當期。2026Brochure的CAT短期保證床位/價格不套一般semesterexchange；一般exchange免學費與visiting付費分開。Spring2027新版仍未核實，不寫官方尚未公告。
- 蒙田波爾多：2026/27官方迎新2027-01-07與授課01-11至04-30已核；同頁Christmas兩段及星期矛盾保留。EnglishFriendly2026/27單頁實開，不當全英授課/免FrenchB2；一般FAQ的LA僅母校要求與February2026清單通用LA不同，保留待確認/矛盾。住宿APL段2026-07-01規則變更已與法國ServicePublic互核，國籍/助學金/工作等例外分開，不保證臺灣交換生補貼或2027規則不變。25頁Humanities課表仍部分待讀，不憑檔名定年。
- AMU：官方2026/27Spring授課/考試分段、bilateral附件appendix明示2026/27 B2或母校確認函已核；獨立證照仍recommend，不將學位法規套短期雙邊。新五頁Erasmusfactsheet11/30、12/15截止不自動套中正bilateral。公開根頁只有招生分類，未註冊/取得完整當期表；PhD醫療免費條款不補本科/碩士交換保險。
- FHNW：匿名公開HTML內十二個accordion使用JSON解碼讀display content，不執行網站JavaScript。Spring2027入口Basel兩PDF正文實為2026，保留來源年矛盾；Brugg-Windisch/Olten課表正文2027已讀，先修/只可選一專門化/全年專屬前期項目與新生迎新限制分開。當期Olten校曆強制2/16InfoSession、2/22起授課、6/21–7/10考試只限該校區。

新增source fetcher支援公開escaped HTML表與FHNW accordion，仍只寫candidate目錄且不把取得成功自動升當期。來源的全文、部分政策/細目、取得未完成語意查核分開保存；`build_ccu_research_audit.py`不再把部分來源寫成全文已核。17類欄位、來源頁碼/原文、適用年、查核時間、原檔SHA均保留。未聯絡學校、註冊、送件或解驗證碼。

實測中正112 passed；四校資料/條件/流程211 passed、5 skipped、1 failed（已在main重現的NTPU既有destination計數）；Chromium中正/臺大16 passed。16份離線產物重建SHA一致，49份原main資料逐byte不變；110 API routes及必填schema不變。此次更動檔ruff、Python編譯及diff檢查通過；擴大lint查到未更動舊CCU測試19個style問題，保留log，不宣稱整個repo lint全通過。

原始驗證失敗亦保留：新測試初次兩個文字斷言與實際內容措辭不同已修；第一次四校命令引用不存在檔而無測試執行；第一次hash比較與另一次重建重疊失敗，改順序後16份相同。有效結果見`validation.json.fifth_pass`及`ccu-validation-2026-10-08/fifth-pass-*`。

本輪新增範圍僅CCU資料、兩個CCU script及CCU測試/交接證據；沒有新增核心registry/API/UI共用修改。全分支必要共用改動以前述合併清單為準。PR#3維持draft，未merge或部署，接續公開來源查核。

## 第六批：接收政策、實際 XLSX 與複核同步

本批保留104筆名單：52筆官方名額表列可交換但中正三梯次校內申請已截止、49筆未開放參考、3筆名額空白待確認；不把空白當零或新增名額。55筆逐校17欄（935欄）目前292欄當期原文支持、242欄適用年度／條件待確認、40欄其他年度／梯次參考、46欄來源矛盾、314欄缺值、1欄官方明示尚未公告。當期支持只限已列事實，0校宣稱17欄全部完整，研究尚在持續。

第六批續讀千葉商科、HCMUTE、同奈、Presidency、Jena及西波希米亞，另修正Bordeaux、名古屋與AMU。新增69個來源紀錄：65次新匿名公開網頁／檔案取得、4次已保存官方PDF離線重讀；不是69次成功下載。62個本輪新取得來源可讀，3個ZCU錯誤公開索引host回應404保留，再從校方JavaScript文字的公開顯示端點取得真正索引與附件，沒有執行JS或登入。來源總數389，56個取得失敗；7個Anubis、2個HTTP202空回應、1個captcha仍無可讀政策。新增65個欄位映射，其中57個原缺值；3項複核另列 `sixth-pass-parent-corrections.json`。18校有逐欄完整／部分閱讀台帳，均不宣稱公開研究耗盡。

- 千葉商科：N2是一般預期能力，沒造必繳JLPT證書；38,000 JPY/月含水電網但不含餐與床墊，2027價格未核。late-March與April迎新指引相異；2027完整申請guideline由母校承辦接收，未取得不等官方未公告。
- HCMUTE：實開3頁2026Fall／2027Spring簡章；5項mandatory、2項optional與英語B2能力分開，接收校GPA不限不取消中正GPA3.0且平均70。中正2027-01-25與Spring兩term學生截止2027-01-04／04-12三者矛盾同步到主欄、summary、evidence及流程；後兩日期不是授課開始日。各宿舍月／年、整房／每人單位保留，不換成未核學期價格。
- 同奈：仍17欄缺值及名額空白。新聞的Chinese Culture University(CCU)是文化大學；兩週Hoseo／PAS活動與一般本科表不能推中正學期incoming支援。未取到規定不寫成官方明示尚未公告。
- Presidency：實開3頁Inbound申請表、12頁正文2025–26舊factsheet及2026/27校曆；PUoutgoing的CGPA6及9/30不套中正incoming。普通UG/PG1/18–5/14與MBA1/27–5/21不同，校級all字樣範圍矛盾保留。2025價格／截止／學分仍參考，名額空白未補。
- Jena：2026/27指南Guest Studies第15頁summer母校提名11/15、學生申請1/15及住房1/15各自核對；申請時本科第4semester與一般頁已讀2semester差異保留。指南迎新4/1–9與現行校曆probably4/5–9、註冊範圍相異不任選。真實公開XLSX及研究supervision PDF保存；公式只讀文字不計算，不從研究表推一般課程生必繳。Winter2026/27費333.05+20不是Summer2027價格，2023財力數值不套當期。
- 西波希米亞：3頁正式2026/27校曆支持普通summer2/15–8/31、授課至5/18、考試5/19–6/30及8/16–31；Health1/25起另院系。宿舍6,000 CZK含2,500 security及3,500 blocking，不宣稱全退押金；12/10一般住房付款日與學生申請／母校提名分開。公開房價表正文無生效年、索引標題與檔名相異仍待確認。

三項複核已同步：Bordeaux APL政府原文的 `activité professionnelle` 或 `contrat d’apprentissage/de professionnalisation` 是從事工作或持學徒／職業化培訓合約者可能符合，不能泛化一般stage實習，個人／臺籍與2027補貼不保證。名古屋母校第34頁4/12與NUPACE2026/27第6頁暫定4/9授課均保留，`semester_dates`、summary、home evidence、校曆、交換期間及指南均標來源差異；4/1抵達迎新另列。AMU2026/27第2、10頁承認B2證書或Rector／Dean／Coordinator確認函，独立證照為recommended；中正當期逐校數字及簡章第3頁兩年內有效檢定仍另有母校繳件層級，是否接受函替代未核。數字條件改needs_confirmation及scope_choice_required並新增other確認函路徑；IELTS5.0加持函的API／JS不直接fail，也不自動pass。

實際驗證：最終四校選定測試251 passed、5 skipped、1既有NTPU destination_profile_count失敗（58.00s）；其中130個CCU案例全部passed。初次三個新增測試斷言錯誤的原始log保留，修正後重跑。手機390／桌面1440及NTU四校瀏覽器22 passed（150.50s），含名古屋雙開課日、HCMUTE三截止日與AMU替代函提示；六張實際截圖保存在本批驗證目錄。16輸出離線重建hash一致，49個最新main既有CGU/NTPU/NTU資料檔hash不變，110條API路由及required欄位不變。Python編譯、改動檔ruff、JS語法及OpenAPI contract檢查成功；完整wheel附件包裝證據另見sixth-pass-final-wheel-proof.json。

本批唯一新增共用檔變更是 `pyproject.toml` 的CCU partner_forms XLSX glob。資料／fetcher、AMU與名古屋適配均在CCU獨立檔；共用registry/API/UI等先前分支改動仍按本文件既有整合清單協調。未merge或部署，沒有改NTU工作、憑證、權限、付款或安全設定。第七批已開始龍谷、東北、北海道、常磐、東亞、慶星公開来源續查；本批推送是可複核檢查點，不能當研究完成。

## 第七輪：龍谷、東北、北海道、常磐、東亞、慶星

新增72筆來源紀錄：65次匿名公開網路取得，7筆離線重讀既有官方附件（六校母校表頁及慶星2027春表）。60欄更新、29個原missing填入有證據資訊；截至本輪935海外欄為306當期已核、257待確認、31參考、55矛盾、285missing、1官方明示未公告。461來源中59fetch_failed、另10個challenge/captcha/空回應不作政策依據。24校有語義查核帳本；沒有任何學校宣稱17欄全部本期完整。

- 龍谷當期官方Spring2027申請頁與16頁指南、六指定項目/實表已開啟。接收端11/9 23:59JST vs母校11/15及JLPT ifavailable vs母校必附保留差異；推薦/醫師胸檢替代要求按實表，模板舊JEP標籤不擅改。寢具1960/1980、required/optional及退宿5日/7日、獎助扣除說法另待確認。
- 東北COLABS事前接受10/15 15:00JST與TAO Oct1–Nov15分段，事前接受不当母校nomination截止或入學；masters checkbox/graduate範圍仍待核。IPLA/COLABS Spring2027校曆與JYPE Fallonly、DEEP舊Spring2026分開。英授在學函替代、ECTS等量與TU學分不亂轉。
- 北海道HUSTEP 10/23、SA/SRS nomination9/25/application11/13及學制/學籍末日分開；新iBT4.5只2028起、JASSO畢業日限制只獎助段。四個HUSTEP實表含Spring2027舊XLS已讀原儲存值，不執行宏/公式；TAO完整個人字段未取得。10/10.5小時及寢具價格/稅別矛盾保留，普通宿舍招租不套HUSTEP截止。
- 常磐公開Fall交換與2026FallPartTime（收學費）不是2027春新簡章；中正當期日期仍待接收端核。東亞Outbound/degree/韓語研修條件不填CCUincoming缺值，一般保險30%off算式與未年住宿價差另列。慶星Spring表內Fall住宿價不當春帳單，英文學位招生門檻不套交換。

實際驗證：141項CCU測試全過；四校選定回歸262 passed、5 skipped、1既有NTPU目的地計數失敗（已於main重現）。瀏覽器同次22項既有通過；四個新案例因重複有效URL數量假設失敗後修正，單獨重跑4 passed/25.08s。16輸出離線重建雜湊一致；49個CGU/NTPU/NTU main資料雜湊不變；110 API路徑及必填schema不變。最終wheel562份CCU檔案逐byte一致、實際XLS已包含，SHA見seventh-pass-final-wheel-proof.json。初始指令/測試問題、真實日誌與截圖保留於validation和本目錄。

本輪共用處變更僅pyproject.toml的CCU legacy-XLS package-data glob；校別程式新增optional xlrd研究依賴及唯讀XLS擷取，CCU adapter補語言計畫/替代說明、龍谷文件待確認。累計核心registry/storage/API/UI/資格與文件協調改動見此前檔案清單。下一輪公開源續查p16/23/61/77/87/105；此仍是可整合檢查點，未標整體研究已耗盡。

## 第八至十一輪：逐校文件、生活資料及實際 API 對照

此節更新前述歷史檢查點。截至2026-10-08，104條目分類仍為52筆當期列名額（校內收件已截止）、49筆本季不開放、3筆名額空白待確認，無明示零名額。55筆流程各7步驟及55筆指南可由實際API讀取；流程保持legacy／official_partial。

新增個別外校文件清單：23校175項，保留申請、錄取後、條件計畫三種階段。每項具有官方URL、原文、物理PDF頁碼或網頁、年度／梯次、查核日期、hash；份數、簽章、正本、form URL僅按實讀內容設定。全23份清單標為partial_not_exhaustive，不代表全部文件。母校9類第一階個別準備文件及37筆當期逐校第二階要求另放在母校與提名步驟，不能被外校清單覆盖或當成host申請規定。

新增55×7逐欄基本資料：城市／校址各54筆有來源、網站55筆、学制21筆、學院11筆、交通45筆、生活48筆有查得內容；非空不等於2027適用，逐欄狀態見功能對照。地圖經緯度全部保持pending，54筆城市可核對且1筆缺值，不從名稱猜座標。p71官方入口回傳不相關內容，保存異常而不採作政策、校址或城市依據。多校區、SoE／Erasmus／HUSTEP／研究所等條件分別保留。學術filter中待確認標記保持unknown，不能自動判符合。

接收校17類欄位共935項：310當期已核實、229缺值、314適用年度或條件待確認、20其他年度參考、61來源矛盾、1官方明示尚未公告（HUFS到校前TB窗口）。39校至少一项當期海外事實，0校17项全核實，0校完整外校申請文件集合，functional_parity_complete=false。剩餘公開交通、生活、學制／學院及政策適用年仍是公開查核工作；登入／提名後個人表、技術失敗与承辦确认另列，沒有把所有缺值都稱為只能聯絡學校。

本輪實讀校務內容的重大修正：

- 東北COLABS的request提交為2026-10-15 15:00JST，Oct1–15提交對應EarlyNovember結果通知；舊Q5時程內部矛盾保留，request、結果與TAO Oct1–Nov15分開。
- 龍谷母校灰字十項文件保持舊參考，current Spring2027接收清單的JLPT是if available；中正兩年內語言證明不因此豁免。
- KMUTT AY2026正式校曆的Sem2/2026課程為2027-01-13至05-28；01-11/12是registration而非開課，與中正母校表01-11至05-15矛盾保留；SIT研究所另計。
- ASBU主校2026/27本科、研究所與Cyprus校區分開；主校春季授課2027-02-08至06-04，Cyprus內部exchange日期不能當CCU接收申請截止。舊2025/26flyer的春秋nomination標籤疑義不自行修正。
- HUFS新Spring2027–Fall2027 factsheet與語言替代簽章表實際可開啟；GPA≥2.5，英文與韓文有各自替代條件。非OECD passport財力認證、提名後個人finance表及NHIS與私人保險分開。
- 忠南2027 current factsheet修正一般申請12/1、bank／認證在學12/20上傳、2027-01-15正本抵校，健康／TB與participation agreements錄取後；regular與GSP住房／餐費條件不同。
- Strasbourg2026/27 nomination與student application均到Oct1；Learning Agreement實得PDF實際有本人與兩校coord簽章、至少50%同系課程。2026住房指南、CROUS流程與法國政府住房補貼条件分開。
- VelTech所謂application DOCX實際是factsheet，web與文件截止／住宿價格矛盾保留。Xiamen health.pdf實際DOCX可讀；另一physical exam captcha不冒充PDF表格。CQU/HMT与一般foreign，NENU/BNU外國生規定與Taiwan路徑分開。

637個來源ID唯一且對應637請求，81個合作校附件均可解析（60PDF、16DOCX、3XLSX、1XLS、1DOC）；附件可開啟只證明可讀，不能推定當期或完整清單。70筆fetch_failed另記；7challenge、3空回應、2captcha、1不相關內容異常不採作規定正文。20筆failed followup中14筆實際重試、6筆僅首次失敗無重試，未捏造結果。

本輪校別新程式為ccu_profile.py、ccu_documents.py、build_ccu_functional_parity.py；新增資料獨立放在official_data/ccu。相對第七輪的核心差異是api.py（CCU城市、生活与completeness對應真實來源）、storage.py（CCU缺值不改成官方未公告）、static/app.js（載入CCU交通／生活段落）、static/index.html（保留NTU前綴並更新CCU資源版本）。本輪沒有新增API路徑或改required schema。初始分支至main的其他共用差異仍見前表，供統一合併。

實際檢查及證據均存於docs/ccu-validation-2026-10-08：

- 四校回歸：282 passed、5 skipped、1 failed（臺北大學destination profile count預期1實際0，在最新main独立環境已重現）；沒有CCU新增失敗。5skip為4個既有CGU Phase C與1個NTU Docker opt-in。
- 全CCU手機／桌面瀏覽器27 passed；補強實際展開生活指南及母校／host文件後的兩個聚焦測試亦通過。截圖可見Winterthur交通、ALIAS及忠南12/20上傳／1/15正本抵校要求，無水平溢出。
- 最新main的49個CGU／NTPU／NTU資料檔逐檔hash不變；20份輸出重建前後一致；110條API路徑及required schema不變。
- 新增與實質修改的10個Python檔Ruff通過，JS node --check通過。擴大到較早學校測試與build程式的Ruff有47筆既存樣式問題，保留實際結果，不能宣稱全專案lint通過。
- wheel建置成功，760個CCU資料檔與來源byte一致，ccu_profile.py、ccu_documents.py與CCU生活renderer納入套件；最新SHA見eighth-eleventh-wheel-proof.json。

長庚基準亦經實際API核對：原始154流程＝77 published(115)＋77 legacy(116)。無年度API回傳77 legacy；指定academic_year=115才是77 published，已在最新main解包API重現。中正與長庚照片、72小時、行李、到校採購皆為0，不能列成中正單方缺口。完整55筆逐校對照、來源狀態、文件階段與尚缺欄位見ccu-functional-parity-2026-10-08.md及functional-parity.json。

## 第十二輪：當期學制來源一致性修正

續查逐校學制缺值時，核對中正當期學校資訊p39的黑字「限大學部(大四下畢業者亦不可申請)」及undergraduate GPA原文。常磐大學原API保留資格原文，卻沒有結構化學制及profile證據；現補成當期母校依據，含相同附件hash、物理頁39與原文，不以host無年份頁推定年度。沒有把本科年級字眼或學校開設碩博士課程擴張成交換接收資格。

學制profile非空由21增至22，狀態變為8已核實、14待確認、33缺值；實際API學制非空由22增至23，可確定學制篩選由8增至9；常磐大學本科符合、碩博士排除已以實際程式檢查。其他6類profile及935個獨立海外欄位狀態不變，637來源、81合作校附件、104條目與55流程數不變。這項是來源稽核一致性修正，不能宣稱資料已與長庚相同完整。

第八至十一輪提交4db9cd381d0316c6bf012e6f7b3825dc5933b3f7已推送，origin分支讀回相同SHA，PR #3仍為draft。第十二輪追加驗證及交付證據另存twelfth-*檔；第十二、十三輪一起提交，最新遠端SHA以交付回報及GitHub分支為準。

第十二輪實際驗證：91 passed（CCU來源完整性、資格、文件、生活及API檢查），無skip/fail；重新量測CGU 77份unscoped／77份115 published及CCU55份實際workflow，學制非空23、可確定9；20個輸出再次重建一致、49個既有學校檔案不變、110 API路徑及required schema不變。本輪曾建置wheel，最終逐byte驗證以第十三輪parent-fix-wheel-proof.json為準。此輪未改renderer或共用程式，前輪27個瀏覽器測試及兩項展開可見性驗證仍是當時適用畫面證據，沒有重複宣稱另跑全部四校。

## 第十三輪：待確認資格、文件階段及官方附件修正

本輪回應實際前後端差異及逐份文件誤讀，沒有增加104條目或假裝外校完整度完成。935海外欄位仍為310已核、229缺值、314待確認、20參考、61矛盾及1官方明示未公告；637來源、81可解析合作校附件及23校175項partial_not_exhaustive文件清單不變。

- FHNW p104及北海道p37的待確認學院／學制，前端原會依文字加分或排除，現與API使用相同保守判斷，連field_evidence.status亦核對；unknown保留篩選可見、沒有確定符合或不符。實際兩校×手機390／桌面1440、符合文字與不符文字兩種申請者皆核對前端、advisor及application-plan。ZHAW p103學院有字串但來源待確認，實際可確定學院重新計為1；學制可確定9。
- 忠南p53的2027 factsheet物理p2明示申請後2026-12-20上傳銀行／認證在學證明，2027-01-15原件抵校，錄取信12月底；兩項由post_offer改after_application，另設不等錄取的補件步驟。健康／TB及participation agreements仍錄取後，沒有將所有文件塞入學生申請一步。
- HUFS p47的2027 factsheet物理p3一般brief essay未載最低頁數；至少1頁只適用Intensive Korean Program study essay。一般與條件項分開，conditional及condition傳到流程與文件目錄。finance是申請期後，宿舍健康表在宿舍分配後；兩者不混作一般錄取後文件。舊第九輪錯誤歷史記錄標superseded_by及原因，最新依thirteenth-document-corrections.json。
- 18個官方附件已有實際取得內容及hash，現在legacy／適用性待確認仍可直接開啟，並保留完整清單與適用性提示。附件含指引而不全是空白表格。龍谷學習計畫及語言評估DOCX的即時匿名HTTP均200且byte與保存檔相同；評估表institutional stamp單獨保存。瀏覽器实际點擊流程及文件目錄下載、驗證hash；瀏覽器外網以保存的真實DOCX回放，沒有將回放說成即時網路成功。

55流程現為53筆7步驟、忠南及HUFS2筆8步驟，均維持legacy／official_partial。實際55校文件目錄保留175個host階段、26個條件項及18個已核實官方連結。長庚指定115 published基準1238項文件、0個form URL；未指定年度116 legacy為1469項及77個form URL，年度分開量測。

相對第八至十一輪，需要協調的共用差異：qualification_scopes.py、advisor.py、application_rules.py（同一來源狀態守門）；models.py（兩種文件模型各新增stage、conditional、condition及official_form_verified選填metadata）；application_documents.py（個別階段、條件、CCU已核附件開啟與提示）；api.py（CCU文件目錄由bundled資料取得且canonical母校名）；static/app.js與index.html（未知篩選、文件連結／條件呈現及資源版本）；content_governance.py（忽略新增metadata的空預設值，維持既有內容hash，但有值的條件／階段仍hash約束）；docs/api/openapi.json（新增選填欄，110路徑與required欄不變）。tests/test_school_photo_and_match.py補其既有Node fixture所需helper及stub；其他新增測試及產出留校別獨立檔。這些是可合併程式差異，未修改權限、憑證或安全設定。

實際驗證及可重查證據保存在docs/ccu-validation-2026-10-08/parent-fix-*：

- 擴大四校回歸312 passed、5 skipped、1既有NTPU目的地數量失敗（165.40s），失敗已在最新main獨立重現。沒有把失敗算成功。
- 完整CCU手機／桌面瀏覽器33 passed（240.35s），涵蓋實際unknown篩選、兩API與流程／目錄點擊下载；另兩個聚焦下載測試2 passed。
- 後續新增內容hash相容性及最新提示的完整性測試8 passed（15.21s）；四校及33瀏覽器在這兩項最後調整前執行，沒有宣稱之後重跑全套。
- 20份輸出離線重建hash相同；49份CGU／NTPU／NTU main資料逐檔未變；API110路徑及required欄不變，選填schema有上述增加。CGU115 published上海交大及NTPU115 legacy ESIC的內容hash與main一致，選填非空階段變更會改hash。
- 相關新增／改動檔Ruff、JS語法及OpenAPI contract成功；不宣稱整個專案lint全過。wheel成功，762個CCU資料及12個相關程式／UI檔byte一致，SHA見parent-fix-wheel-proof.json。
- 既有content_governance測試wrapper無法collect：缺少tests/__pycache__/test_content_governance.cpython-312-pytest-9.1.1.pyc。真實collection错误保存在existing-governance-wrapper-unavailable.txt；改以獨立main內容hash證據及新增完整性測試驗證，沒有捏造wrapper通過。

本輪是已驗證修正的可整合檢查點。公開學制33校、學院44校、交通10校、生活7校仍有缺值，另有登入／提名後個人表、來源矛盾及當期適用性未核；functional_parity_complete=false，未直接merge或部署。

## 第十四至十五輪：首爾科技新版及公開交通／生活續查

本批新增14個來源紀錄，總數651且ID唯一；新增兩個可開啟PDF，合作校附件共83（62PDF、16DOCX、3XLSX、1XLS、1DOC）。71筆fetch_failed，另有7challenge、6空正文／JavaScript外殼、2captcha及1不相關內容異常。不將HTTP2xx、搜尋摘要或連結標籤當作已讀政策正文。

首爾科技官方新入口標2027/2028，但連結的8頁PDF正文實際是2027 Spring；逐頁實讀並渲染核對物理p3文件表、p6住宿／價格表。舊2026/27兩份來源保存原bytes，metadata標reference_only及superseded_by；當期host清單不再沿用旧版。主要差異：

- 新版明示exchange宿舍不保證，International Hall僅候補；男單1329120、男雙1045980、女雙1062360 KRW／期，International Hall各房型及餐費另列且可變。不是保個人房型或帳單。
- 日期2027-03-02至06-21與中正當期p48一致，旧6/22 tentative被新版取代。Host最低2credits、中正最低3且推薦12仍分來源標conflict；不自行覆蓋母校最低學分。
- Host第一次7項（online、在學、成績、語言、Study Plan、護照、照片），第二次3項（visa copy、航班、本人銀行），另2項僅宿舍申請者（TB、兩劑麻疹）。第二次／宿舍送件日期與啟動條件未載，不套旧資料抵韓前2週或推定錄取前後。清單仍partial_not_exhaustive，提名後個人online及声稱attached的空白Form1未取得；8頁PDF不是Study Plan表。
- 新host清單未列推薦信，中正當期母校第二階仍列Recommendation Letter，保留在母校提名步驟並標兩層差異，未擅免除。第十六輪按p3／p7修正：非OECD在學／成績須正本及條件認證；銀行列本人名下金額及非OECD正本，未列銀行認證；一般入口original字樣與PDF範圍差異另保待確認。
- 2027/2028 incoming明載Undergraduate至少2學期、Graduate至少1學期及partner exchange依協議免tuition，Visiting不免。前者是接收端，不能抵銷中正所有outbound滿2學期、GPA／平均資格。NHIS 79310月費只標as of2026，未保2027費率；密集韓語非學分另收費。

新增交通原文：東北師範一般foreign頁的指定日接機隨通知（臺籍HMT適用未核）；電子科技大學27頁指南實際封面／前言均2025，只作舊路線參考，抽取數字異常不猜時間或價格；托馬斯拔佳incoming列PRG／Otrokovice／Zlín轉乘及查班次入口，未標2027；西波希米亞教育學院FAQ列Plzeň交通，不能套所有學院／Cheb或ArtCamp暑校票。廈門圖書館Reader’s Guide的院方簽章借閱啟用及Siming／Xiang’an櫃檯作一般生活資料，不是交換申請文件；天津2026年9月foreign／degree新生welcome pack只參考，未套臺籍2027交換簽證、照片或學費。HCMUT新頁僅取得44字JavaScript外殼，生活欄保持空值，不用搜尋摘要冒充正文。

最新實際資料／API數量：104條目分類不變，55流程與指南均legacy／official_partial；52筆7步驟、忠南／HUFS／首爾科技3筆8步驟。23校177項外校個別文件、26條件項、18已核實官方文件連結；55校實際文件目錄與階段可讀。網站55、城市54、交通49、生活50筆非空；學制profile23筆非空（9核／14待／32缺），實際API24筆非空、可確定學制10；學院11筆非空、可確定1。935海外欄為311核／229缺／312待／20參考／62矛盾／1官方明示未公告，39校至少一項已核、0校17欄或全部host文件完整，functional_parity_complete=false。

本批額外共用變更只有application_documents.py（after_application目錄按實際school step.phase；當時只修phase，逐項stage仍誤標不等錄取，第十六輪另修）及workflow_structuring.py（已逐項核對且有stage的文件保留copies／copy_type／signatures缺值，不從條件名稱自動推所有人須正本或簽名）。source-bound metadata無stage的既有CGU／NTPU／NTU仍沿原整理方式；本批未新增API路徑／模型必填欄或改UI程式。其他分支累計共用整合點仍見前節清單。校別適配在ccu_documents.py，來源、程式輸出及測試獨立。

實際驗證與證據見docs/ccu-validation-2026-10-08/fourteenth-fifteenth-*：

- 最終四校選定回歸318 passed、5 skipped、1既有NTPU目的地計數失敗（183.76s）。初次9失敗含漏稽核旗標、旧资格斷言、新測試HTTP碼假設及條件正本被自動推定；原始結果保留，修正後無CCU新增失敗。
- 最新手機390／桌面1440聚焦瀏覽器8 passed（83.43s），包括待確認資格／兩API、流程與目錄實際官方DOCX點擊下載、首爾科技新版住宿／價格／最低學分來源差異及第二次送件；五張最新畫面與PDF表格渲染存檔。前次完整33瀏覽器另保留，未冒稱本次重跑全33。
- 20份輸出最終重建一致、49份main既有CGU／NTPU／NTU資料hash不變、110 API路徑及required欄不變。初次4個衍生檔尚待研究稽核後重建的差異紀錄保留，未將初次失敗算通過。
- 651請求ID唯一；83合作校附件逐檔hash核對，新增PDF物理8／27頁可解析，原81可讀證據沿用且bytes不變。當期適用性另核，沒有把舊2025指南當2027。
- 改動校別檔Ruff及OpenAPI contract成功；整個專案lint和缺pyc的content-governance wrapper未宣稱通過，後者限制見前節。新版wheel成功，781個CCU資料檔及13個程式／UI檔逐byte一致，SHA為d065454f2edeb4dfa46a6f6a670ee6d9db4d20e0811a248311784a96e998b979。

第十三輪提交0f300be0d0a691875aaa5506f8ba2c1c7d0e9f0e已推送、遠端读回一致且PR#3為draft；本批最新提交以交付回報及GitHub分支为准。交付前遠端main仍f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59。公開交通6校、生活5校、學制32校、學院44校仍未載；另有未年／跨校區來源、個人表、國籍適用性及矛盾未解，沒有把公開查核缺口一律稱為承辦阻塞。未合併main、部署、登入學校系統、聯絡／送件或改憑證／權限／付款／安全設定。


## 第十六輪：HCMUT當期正文、新表格及逐項範圍修正

本輪新增28個官方來源紀錄，679個source/request ID唯一。合作校附件87份（64PDF、18DOCX、3XLSX、1XLS、1DOC），逐檔SHA核对；新兩份PDF各4頁、兩份DOCX實際含表格，內容可解析。舊83份readability證據保留且bytes不變。77筆fetch_failed，另7challenge、7空正文、2captcha、2不相關內容異常；取得失敗不表示官方尚未公告。

### HCMUT新版正文與當期文件

先前HTML只有44字JavaScript外殼。本輪匿名瀏覽器真實回報ERR_CERT_AUTHORITY_INVALID，沒有跳過TLS驗證。讀官方public JavaScript確認read-only API，再取得[2026-08-26公開公告正文](https://hcmut.edu.vn/api/home/tt-tin-tuc/item?ma=24702&lang=en)（對應[人類入口](https://hcmut.edu.vn/news-en/item/24702)）；API標public/active，原始JSON、SHA及解析器保存。只有公開body被提取，internal/inactive紀錄會拒絕。舊19961公告實際是2025/26 Semester2，不作當期。

- [Updated August 2026 factsheet](https://drive.google.com/file/d/1TH6YSfT3MbusPqHtTZeNER4hRgUwiLt1/view)正文與公告一致：AY2026/2027 Semester2、提名2026-09-30、學生申請2026-10-15，未猜截止時刻。Orientation2027-01-08；課程及考試2027-01-11至06-07。中正p67的10/15也一致，application_deadline由conflict轉verified_current。March版9/15及10/1保留reference_only及被取代依據。
- [新版学生申請DOCX](https://drive.google.com/file/d/1VAxq2TwOtQaUN5x2OIYzZHM16bZCYRhJ/view)與[母校提名範本](https://drive.google.com/file/d/1XQm-iF-4EZNrZt_c35zhvPTJTl3eya4M/view)逐段、逐表讀取。提名信須母校letterhead、負責人簽名與Seal；學生申請仍須附，不誤改成學生自行提名。保險copy在到校前一週送；護照與照片copy各一份依新表核實。HCMUT共9項跨nomination/student_application/post_offer，仍partial_not_exhaustive。
- 公告與PDF兩個線上申請shortlink均HTTP401且導至同個GoogleForm；沒有登入或送件，個人online額外欄位未讀，因此application_forms保持needs_confirmation，不能把DOCX集合稱作全部文件。
- March及August兩份PDF physical p4文字抽取均帶出Kyoto／CoE／Japanese段落，但實際渲染畫面完全沒有這段；兩張原始畫面、抽取原文與hash均保存。先前把隱藏文字当作官方簽證矛盾的判定已撤回，理由及before/after明載。可見PDF流程與新版學生表均為Vietnam Immigration發Visa Approval及Acceptance，再至指定Vietnamese Embassy/Consulate。visa現為verified_current，沒有以改動原文來掩蓋差異。

### 首爾科技：第二次送件與銀行認證範圍

首爾科技physical p3分第一次7項、第二次3項；只確認順序，第二次確切日期與啟動條件未載。原after_application會在每項UI顯示「不等錄取」，已新增中性second_submission模型值／標籤，三份個別文件改用此值；流程与目錄群組、逐項手機／桌面顯示均待確認時點。忠南及HUFS已核實after_application保留「不等錄取」。修正不是猜第二次發生在錄取前或後。

按physical p3及p7原文與實際p7圖片，認證只列在非OECD在學／成績文件。銀行列本人名下USD6000一期／12000一年，以及非OECD正本，未列銀行Apostille／韓國使領館認證。已修documents及visa摘要、所有衍生資料；個別銀行stamps維持空，原在學／成績stamps保留。p7簽證清單本身明示reference only，不能變成個人使領館確定清單。before/after另存sixteenth-seoultech-bank-correction.json及stage-correction.json。

### 公開交通與生活續查

首爾科技Gongreung／Gongneung交通、Ostfalia數位Deutschlandsemester票及丘庫羅瓦會議頁交通只作一般路線或範圍待確認，未標2027的票價及跨校區資訊未冒作當期保證。重慶2023圖書館／場館為reference；東北師範Ehall郵件服務的臺籍適用未核；HCMUTE 2026校園商店／宿舍合作MOU及2025醫療服務為reference，不當個人住房保證。HCMUT當期到校指南支持campus_life當期來源。DNTU新校園頁尾夾帶不相關內容，整頁不作政策。UNINTER指南三次HTTP503、HCMUTE數位圖書館503、HCMUT空support JSON均保存實際限制。

### 最新数量及共用整合點

104条目仍52當期名額已列／49整校灰字未開放／3空名額待確認／0明示零名額；母校收件已截止。55流程与指南均legacy／official_partial，52筆7步驟＋3筆8步驟。23校178項外校個別文件、26條件項、19已核實官方文件連結；实际流程含母校通用共1113項文件，不與178項host文件等同。網站55、城市54、交通52、生活54非空；可確定學制10及學院1。935海外欄312核／229缺／313待／20參考／60矛盾／1官方明示未公告；39校至少一項核實、0校17欄或完整host文件全核，functional_parity_complete=false。

本輪核心共用差異是models.py（兩個stage Literal選填值）、application_documents.py（second_submission階段及school step.phase）、static/app.js（中性逐項標籤）、static/index.html（保留NTU前綴更新CCU資源版本）、docs/api/openapi.json（只加選填stage enum值）。110API路徑及required欄維持原樣。校別資料與fetcher/public JSON解析留CCU独立檔；全分支累計registry/API/資格守門/governance差異仍見前節完整合併表。

### 最新實際驗證

- 四校最終選定回歸 **322 passed、5 skipped、1既有NTPU失敗（186.89s）**。唯一失敗為test_ntpu_bundled_data.py:110，destination_profile_count期望1／實際0，已在最新main獨立重現，證據見ccu-latest-main-baseline-tests.txt。所有本輪CCU、共用文件API與資格守門測試通過；初次CCU旧步驟斷言及新source頁碼測試假設失敗均保留原始紀錄並修正。
- 手機390／桌面1440真實UI：首輪8 passed／2個HCMUT定位器失敗；因「母校提名」同時命中兩步驟，改為只選含提名文件的步驟後兩項重跑 **2 passed（21.56s）**。其餘8項已通過且程式／資料未變。包含首爾科技三項逐一不含「不等錄取」、目錄中性phase及銀行範圍，HCMUT新截止日及真實DOCX下載hash；四張新畫面保存。新官方來源HTTP200／原檔hash獨立紀錄，下載回放不冒作即時外網。
- 20份衍生檔確定性重建一致；49份既有CGU／NTPU／NTU資料SHA維持，110API路徑及必填欄不變。OpenAPI完整比對通過，僅選填stage enum增加second_submission。
- 679個請求ID唯一，87附件SHA全符。新兩PDF／兩DOCX可解析，當期適用性與物理p4渲染分開核實。正文摘要首次超過240字導致建置停止，改成202字保留完整逐項來源後重建成功。
- 改動校別fetcher／documents與新測試Ruff通過，app.js語法通過。共用models/application_documents及旧second-pass測試51個既有Ruff診斷與前提交b97c逐項類型／訊息一致，未宣稱整個專案lint通過。既有content-governance wrapper仍缺pyc不可collect，保留此前真實錯誤，另有獨立main hash及metadata測試。
- Python build模組不可用（No module named build），改用uv build成功。818個CCU資料檔、13個程式／UI檔與wheel逐byte一致，wheel SHA256：1b5b1858fd1beeaaad8b977ac9d31bdbb714e087157a1ae702276a0085a05e4a。沒有把初次錯誤當成功。


公開交通尚缺HCMUTE／DNTU／UNINTER三校，生活尚缺DNTU；學制32、學院44校仍未載，另有無年／國籍／校區適用性、個人表及60項矛盾。沒有把所有公開查核缺口當作只能問承辦。資料、API、UI適配可供整合，但不能宣稱外校完整功能已齊。遠端main查核仍f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59；未merge main、部署、登入校方、聯絡承辦、送件或修改憑證／存取／付款／安全設定。

## 第十七輪：學院學制配對、待確認文件及逐校續查

以已推送 `15270145ea93fab2c4d72a7112fe72cdcff5c6a3` 為前一檢查點，最新 main 仍為 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`。全部在同一獨立 clone／分支作業，保留臺大、長庚及臺北大學原始資料。

名古屋當期母校PDF physical p34明載教育學院大學部／研究生、法學院僅碩士，建立兩組 program_options 並接通兩支資格API及前端配對／篩選。法學本科／博士不能由教育條件組合通過，兩組不另增加共同名額。ZHAW工學院由當期母校p103核實；重慶相關專業、慶熙校區限制與Ludwigshafen Business Administration文字補入profile，不能把未核對院系映射當作全院通過。

Ludwigshafen 5項、Augsburg 10項及廈門台港澳4項文件新增逐項結構。解除兩層「整體documents必須verified_current才可顯示」門檻，改按每項 applicability_status／year／note 呈現。母校當期的Ludwigshafen照片JPEG／護照PDF與未標年online→生成個人PDF→母校coordinator簽名→掃描email流程分開；LA／住宿表原檔hash可核，住宿表2027移入日期已讀但不保証住宿。Augsburg非Erasmus LA正文可讀、原檔重試429，顯示待核实來源，不當作下載成功；EU無EHIC聲明及作品集／居留證保留各自條件。廈門HMT正文2026-03-03四類只作未核2027適用的條件清單，健康PDF未取得href，不猜連結。

HCMUTE2027 factsheet的5 mandatory／2 optional資料由母校整包彙整email寄提名信，七項均移至nomination，未誤作學生自行online申請。CS1停車／通勤只保留一般校區指引，不推成接機。DNTU乾淨的獨立官方圖書館服務可讀，借閱展延、查找支援、研讀室及先訓練啟用可作一般參考；2027交換生資格、住宿與保障未核。2026-01-19生效公告08:00–17:00與同頁／root頁尾07:30–17:00差異另存，不把root當確定時段；本轮HTTP服務頁亦為07:30–17:00，與web舊快取不同。主站實際含phpshells.net內容的八份新／舊來源僅標異常，原文及hash保留，不作政策。

本輪從實際href續查廈門商學院、TBU與西波希米亞來源。廈門索引仍是2015–2019歷史訊息，不稱官方明示尚未公告；TBU一般faculty導航不當作允許，母校排除物流／危機管理限制保留。西波希米亞交通／buddy兩份一頁PDF已開啟並讀正文，分開補一般路線及自行註冊，2027身分／班次／結果仍待核。UNINTER三個替代官方入口／指南仍503。

最新為697個唯一來源／697請求紀錄：本輪16次匿名網路候選取得＋2份既有母校PDF物理p98／p102重新抽取實讀，不能稱後兩份是新的HTTP取得。89份合作校附件＝66 PDF、18 DOCX、3 XLSX、1 XLS、1 DOC，全部保存檔案hash吻合；679份既有來源的hash及抽取正文未變。當期／參考／灰字／空白名額分開仍為104條、52已列名額、49全筆灰字未開放、3空白及0明示零；母校三梯次收件已截止。

55流程保持legacy／official_partial，26校197項外校文件全部partial_not_exhaustive，33項有條件，21個已驗證文件直連（含指引，非全是空白表）。1132項流程需求包含母校通用準備，不能等同197項host清單。城市／校址55、交通53、生活55是有來源可呈現；當期／身分核實狀態另列，不代表全數2027完整或座標已核。935個host欄位312當期、229缺、313待、20參考、60矛盾及1明示未公告，39校至少一项當期事實，0校17項全核／0校完整host集合，functional_parity_complete=false。

[逐校缺口清冊](ccu-remaining-gaps-2026-10-08.md)與remaining-gaps.json逐校保存學院／學制／文件／交通／生活缺口、官方URL／原文年度／查核時間、HTTP及未映射附件狀態。提名／個人表限制僅廈門、Augsburg、Ludwigshafen相應步驟具逐字依據，不把全校公開缺值歸為承辦阻塞。尚列593個候選href；全部public_sources_exhausted=false，不能宣称所有公開來源已查完。其餘新版尚未核實，只有HUFS到校前TB窗口可稱官方明示尚未公告。

必要共用變更：models.py兩個文件模型各加3個可選適用性欄位；application_documents.py傳遞至catalog；qualification_scopes.py／advisor.py／application_rules.py增加有當期來源的學院學制配對；content_governance.py僅對None預設值省略以保既有發布hash；app.js／index.html呈現配對、年份／適用性及未核下載來源並更新cache版本。沒有新增API路徑或required欄位。整個分支相對main的14個共用程式檔與本輪8檔列於seventeenth-merge-scope.json，供其他session統一合併。

驗證：最終四校選定回歸336 passed、5 skipped、1個NTPU既有失敗（目的地1對預期0，前輪已在main重現）；CCU相關全部通過。瀏覽器完整同次16 passed，手機390／桌面1440核對配對排除、官方表格／待核標示與HCMUT保存真實DOCX回放下載；即時取得HTTP與hash另存，回放不冒稱新外網取得。初次focused81 passed／2舊斷言失敗，初次四校333 passed／3 failed／5 skipped及瀏覽器10 passed／6定位或等待失敗保留；修正後完整結果如上。文件個別metadata不複製整校review_note，避免把提名Seal等條件混入护照等項目。

20生成檔重建一致，49份原main學校資料hash保留，110 API路徑與required欄位不變、OpenAPI完整snapshot一致。校別程式／新增測試Ruff通過，6個共用Python檔56項既有診斷在同pyproject設定下與1527014一致、無新增診斷；Node語法通過。實際log、XML、截圖、來源／附件、套件及重建證據位於ccu-validation-2026-10-08/seventeenth-*。未merge main、部署、登入外校系統、提交學生資料、聯絡承辦或改動存取／帳號／安全設定。

第十七輪 wheel SHA-256：`f5979b7f307ca4f225bdfdb11e93fe15db31a665da6f6b6f8a9f73eab9704076`；841份CCU檔案及13個關鍵程式／靜態檔与工作樹逐byte一致。

封存清冊時再核對分類：source_checks僅代表取得／查核紀錄，不計作已映射政策；只以各欄evidence及逐項文件證據判定mapped。此報告分類修正後的獨立測試1 passed，未改runtime資料／API／UI。


## 第十八輪：真實表單及送件投影修正，公開href篩查

名古屋真實#advisor-degree新增碩士班／博士班，保留舊研究所值但標未細分。兩API與前端先用current_year細分舊研究所；法學博士／本科不符、法學碩士符合，僅研究所未知則待確認、不加符合分；教育學院本科與研究生仍符合。耦合unknown不退回全校學制聯集。手機390／桌面1440實際操作select、展開年級、提交兩個API：七種身分×兩寬度×兩模式＝28次真實條件表單請求，沒有注入虛構degree option。HCMUTE第4／5步明確submission.method=email、母校彙整責任及factsheet p1列明oia@hcmute.edu.vn；七項提名文件／兩項選附保留。否定句不再推斷online/mixed。西波希米亞只補正機場巴士100至Zličín後三條轉乘：直接巴士、B線Florenc轉巴士、B線Florenc轉C線至中央車站轉火車；2027年度與班次費用仍待核。

初始593 href已去fragment／tracking去重582 URL，逐校保留來源occurrences與處置，不把首頁／研究技術application／incoming staff／outgoing／一般学位招生／CMS登录当必要學生規定。目前588 href／577 URL，其中355待正文、180明確不同對象／計畫或無關導覽研究事件招生、41參考或低優先、1已取得來源；各校public_sources_exhausted=false，這不是全部公開資料已讀或有證據的阻塞清單。

新增七份來源（六份成功，一份429），其中三PDF共七物理頁、一DOCX及兩HTML；另五份FHNW相同URL複查已識別原registry，PDF hash和抽取內容未變、兩HTML抽取文字未變，不覆蓋原檔或算新增。DIT一般incoming checklist拆五項Mobility Online上傳文件與行前LA，共六項待年度核實；簽證／保險行動不猜成申請附件。ZHAW一般spring timeline補orientation week7及buddy前2週；不把未標年自升2027或擅修碩士另一PDF week37疑點。東北ApplicationGuide正文為October2026住宿，期間段仍October2024–2026，僅參考；不是學術申請指南。TBU一般頁Portfolio Arts specialization與當期factsheet指定FMC課有範圍差異，documents標conflict，不選其中一個條件。Østfold新增study LA模板實為Erasmus+國家間mobility，留獨立來源、不替代bilateral表。Augsburg原檔合理間隔單次再查仍429，未取得原檔不設verified download；401提名個人表不繞過。

704唯一來源對704請求／source JSON；93合作校附件＝69PDF、19DOCX、3XLSX、1XLS、1DOC，檔案hash全吻合。原697來源JSON逐字不變。104母校條目仍52當期已列名額、49灰字歷史不開放、3空白非零、0明示零；55當期／名額待核身分與55 legacy／official_partial流程維持。27校203項host文件均partial_not_exhaustive、33有條件、21已驗證文件直連；1138項workflow要求含母校，不與203混算。935 host欄位311核、224缺、318待、20參、61矛、1官方明示未公告；0校17项全核、0完整host集合，functional_parity_complete=false。

本輪五個共用程式修改及校別ccu_documents.py列於eighteenth-merge-scope.json；整分支相對main仍14共用code paths。四校最終375 passed、7 skipped、1 NTPU既有失敗，獨立解包最新main f6ad1b8再次重現目的地0對預期1；中正相關全通過。瀏覽器同次31 passed，含28次真實表單、HCMUTE畫面及NTU／共用條件回歸。首輪四校374 passed、7 skipped、2 failed（中正舊26校斷言與同一NTPU失敗）；舊斷言更新27校後同套完整重跑。首輪瀏覽器4 failed（測試未展開年級及email空白定位），第二輪3 passed/1 failed（攔到multi-plan背景請求），真實條件表單請求辨識後4 passed，再完整31 passed。原始失敗與最終logs/XML均保留，不宣稱全repo測試通過。

六個builder、22生成檔重建一致；49個原CGU/NTPU/NTU檔案及77原published hash與latest main一致；110 API routes、required欄位及完整OpenAPI snapshot不變。Ruff校別／新測試通過；六共用Python檔與37a36ec基準56既有診斷相同、无新增。wheel含855中正檔案與13相關code檔byte一致，hash與來源／頁數／API／截圖證據在eighteenth-*。未合併或部署，不登入外校、提交學生資料、聯絡學校或改存取／安全設定。公開候選仍可續查，不把partial或缺值當作全部工作無法繼續的理由。

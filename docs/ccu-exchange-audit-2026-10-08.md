# 中正大學 2027 春季校級薦外交換資料交接

查核日：2026-10-08。Repository：`blizzard-new/abroad`。
獨立 clone：`/workspace/abroad-ccu-20261008`；分支：`data/ccu-exchange-20261008`。
基準：從 GitHub 最新 main 取得 `f741d540f546d6ddbbf3174c9a34b5ef103c8816`，建分支前未發現同名遠端分支。
交付前遠端 main 已前進至 `f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59`（第一批交付時為 `293546e807294dc0812f390b240a4cfb68e86cd0`）；第一批交付保留開工基準；第二輪依使用者要求安全整合此最新main，保留臺大與既有資料，未寫入其他session工作目錄。
本 clone 未找到 AGENTS.md 或適用 `.agents/skills`。未寫入其他學校 session 的工作目錄。

最新數量與分類見末節「第四輪：六校附件全文與存取結果核對」；前節保留歷史檢查點及最新main整合的資料與驗證。

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

# 中正全名冊補查與平台適配（2026-10-11）

本分支從 `main` 的 `59a20f27fcee00fb597abc79e75ec11778317422` 開始，以中正獨立資料、抓取程式及素材補查全部 **104 個交換名冊身份**。不把一般校園資料、歷史附件或接待校政策轉成母校當期可申請資格。

## 分母與適用梯次

- 母校最新已核實梯次為 **115 學年度／2027 春季**，不是沿用臺大的年度。公告正文日期為 2026-08-18；三梯線上截止 8/26、9/6、9/20，紙本截止 8/27、9/7、9/21。查核日全部已截止。
- 104 身份：52 公布可用名額（49 有數字、3 明示無限制）、3 名額空白、49 灰字歷史參考且本期未開放。沒有把空白或灰字改成零名額。
- **104 不是全球協議姊妹校總數。** 官方全球頁連至 Gamma，公開 HTML 只取得應用殼，匿名 snapshot 回覆 `FORBIDDEN`；全量協議分母仍為 null。未登入或繞過限制。
- 下一梯次／2027 秋季尚未核實，不能寫成官方已明示「尚未公告」。

母校來源：[當期公告](https://oia.ccu.edu.tw/p/406-1008-93586,r1714.php?Lang=zh-tw)、[交換名冊](https://oia.ccu.edu.tw/var/file/8/1008/img/1130/717520038.pdf)、[甄選簡章](https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf)、[全球姊妹校頁](https://oia.ccu.edu.tw/p/412-1008-1509.php?Lang=zh-tw)。本次重新抓取的名冊、簡章及 DOC/ODT 申請表與既有檔案 SHA256 相同。

## 可供整合的資料

| 資料 | 本分支總數／完整度 | 與原有資料的關係 |
| --- | --- | --- |
| 交換名冊身份 | 104／104 | 原始 partners 保持不變 |
| 目的地介紹 | 104／104 | 原有 55 行逐 byte 保留，另補 49 本期未開放參考校 |
| 可定位校園代表點 | 99／104 | 獨立身份、國家與校區複核；5 筆未猜值 |
| 校園照片 | 100／104 | 真實影像、作者、授權 URL、來源頁、校區說明及 SHA256；保留下載原始 bytes |
| 官方網站身份 | 102／104 | 101 網站正文／官方國際處＋Ateneo 當期簡章直接列示 URL；網址身份與網站連線成功分開 |
| 接待欄位矩陣 | 17 × 104 = 1,768 | current 351、reference 322、missing 649、needs_confirmation 365、conflict 80、explicit_not_announced 1 |
| 校園／院系欄位矩陣 | 7 × 104 = 728 | current 368、reference 95、missing 176、needs_confirmation 89 |
| 另列一般校園欄位 | 7 × 104 = 728 | current 288、missing 440；不得與接待政策欄重複算完整度 |
| 讀過內容的參考附件 | 25 | 其中 Ateneo 本科／研究所各一份明載 Spring 2027；其他舊年或未標年分開 |
| 新抓取紀錄 | 1,194 | 成功、失敗、HTTP 200 阻擋頁、錯誤候選均留存；不是 1,194 項已核實政策 |

PR #8 固定 head `9927ec1d8765a9772671bbaa68e7f920995f1258` 已恢復既有 30 點、31 照片，均與本次核對重疊。因此 **真正新增 69 點、69 照片**，不將顯示恢復重算為新增資料。[逐校重疊比對](../src/exchange_info/official_data/ccu/completion-pr8-coverage-comparison.json)。

重要資料檔：

- [初始缺口盤點](../src/exchange_info/official_data/ccu/completion-baseline.json) 與 [本次逐校逐欄結果](../src/exchange_info/official_data/ccu/completion-inventory.json)，另有 CSV。baseline 不覆寫。
- [完整欄位與原文依據](../src/exchange_info/official_data/ccu/completion-reviewed-fields.json)：每欄明示狀態、原因、官方 URL、實體 PDF 頁碼或文字／JSON 位置、原文、適用年度與查核時間。
- [校園素材](../src/exchange_info/official_data/ccu/campus-assets.json)、[座標複核](../src/exchange_info/official_data/ccu/campus-coordinate-review.json)、[照片選擇／排除](../src/exchange_info/official_data/ccu/campus-photo-review.json)。ROR 城市不是校園座標；多校區照片與地圖點不必相同，逐校明示。
- [附件內容年度複核](../src/exchange_info/official_data/ccu/completion-reference-document-reviews.json)、[官方 PDF 精確附件連結](../src/exchange_info/official_data/ccu/completion-reference-document-links.json)、[公開資料夾檔案連結](../src/exchange_info/official_data/ccu/completion-public-folder-file-links.json)。資料夾子檔案鍵含父連結序號，不猜 Google ID。
- [全部來源篩選與排除](../src/exchange_info/official_data/ccu/completion-public-source-screening.json)。443 來源被特定欄位引用、46 技術失敗、6 阻擋／錯誤頁、7 特定候選排除、692 僅抓取未核实政策。原 bytes 位於 `completion_sources/`；HTML gzip 無損保存，原 response SHA 與儲存 SHA 分開。

## 已確認的重要差異

- **Ateneo，本期未開放（p81–82）**：AY2026–2027 本科 Spring 2027 期限 2026-09-30、TOEFL iBT79／IELTS6.0；研究所期限 2026-09-01、iBT80／IELTS6.5，另須本科學位及成績證明由母校 Registrar 直接提供。初申文件、後續健康／錄取步驟分開。已取得文件要求不表示所有個人表已公開取得；不提升可申請狀態。
- **IIT Bombay，本期未開放（p72）**：主站503與國際處正常200分開。已讀官方2026–2027 Fact Sheet全部5頁；Spring課程申請截止2026-09-30、project全年但提前2個月；17欄中14當期核實、提名獨立日／住宿截止／無版本日期的表格3項待確認。Host Bonafide/FRRO表是到校後，不能混入母校初申證明；MoU免課程費仍另付行政和住宿費，住宿按到校時床位。接待規定不改母校未開放狀態。
- **FGES（p88）**：學院2026–2027與母大學同年度簡章正文的期限、法語要求強度及校曆有差異。母大學p9內文日期仍2025，不能自行修成年份或選較晚日期；公開帳號流程證明學生表須提名後個人入口取得。p8已目視核對FGES列，不借用FD或FLSH條件。新增All官方指定服務公開SSR的FGES Vauban marker，WeNov另列且不保證個人校區。
- **QUT，本期未開放（p120）**：官方2027費率、Semester1校曆已讀。MoU提名Exchange免學費與StudyAbroad AUD9900／13200分開，AUD1000簽證獎助排除Exchange。生活費原表合計與各項上界矛盾；2026更新頁仍列舊TOEFL刻度及2022COVID條文，未假定2027適用。Exchange個人申請link須accepted nomination，不由全年StudyAbroad收件推定交換截止。
- **全北，本期未開放（p51）**：國際處正文 Calendar2026、主站 Calendar2021；期限、照片張數、疫苗項不一致，且國際處表格載不存在的 November31。保存原文衝突；2027 新版尚未核實。
- **同濟，本期未開放（p13）**：邀請與申請表正文 2026 秋季；住宿表混載 2025–2027 日期及 2026 春季費率。不可作 2027 春季申請表或當期費率。
- ZHAW 使用 School of Engineering 的官方地圖 marker 與工程學院照片；FHNW 使用商學院 Olten 校區公開地點；Karviná 商學院與 Opava 母校分開。FGES、Saintgits、Uninter Mexico 不任意套用同集團或同名他國校區。
- Ateneo Grade School 照片、校徽／標誌及人物主導活動照排除。照片授權與實際圖片一同顯示，避免共用別名素材覆蓋成不同圖片卻沿用本次作者授權。

## 仍未核實的項目

完整逐校原因見 inventory，不代表已窮盡所有公開網頁。

- 全球協議清單全量與分母：Gamma 可讀內容未取得。
- 5 點未刊登：p68 HCMUTE（兩個 P625，缺一手定位選擇）、p71 DNTU、p74 Saintgits、p111 Karviná 商學院、p119 Uninter Mexico。相機視窗或未確認子校区不能當 marker。
- 4 校尚無可刊登的已複核授權照片：p66 UEL、p71 DNTU、p80 Presidency、p119 Uninter Mexico。
- 2 校官方網站正文／身份補查仍受阻或新版尚未核實：p44 Keimyung、p96 LETI。Ateneo 網域已由當期官方簡章正文核實，但首頁抓取仍受阻。
- 649 接待欄缺值，其餘非 current 欄各有年份、衝突或範圍理由；尤其當期完整文件集、提名後個人表、住宿床位、費用、課程／学制限制不能由一般服務入口推定。

## 程式與合併邊界

新資料與照片不寫入共用 `university_locations.jsonl` 或 `school-images.json`。不重寫 PR #8 的共用姓名／國家匹配器。

學校專屬程式：`ccu_completion.py`、`ccu_completion_sources.py`、`ccu_campus_assets.py`、`ccu_profile.py`、`ccu_student_view.py`、`static/ccu-partner-details.js`，以及 `scripts/*ccu*completion*`、`*ccu*campus*`、`*ccu*reference*`、`prepare_ccu_reviewed_photos.py`。一般校園與49參考校 host 矩陣分開顯示；原有55接待矩陣以明示override欄位補充；原始資格及文件規則保留。

必要共用檔案變更，供中央整合者與 PR #8 對照：

1. `api.py`：僅 CCU 使用新素材投影，照片/授權一致；`/coverage` 與 dashboard 同報100照片；三處 CCU 地圖呼叫傳入本機資料目錄，保留本機 operator 的 verified/pending/invalid 決定。其他母校與共用 matcher 原邏輯保留。
2. `static/index.html`：CCU 模組的 cache 版本 query。
3. `pyproject.toml`：打包 `official_data/ccu/completion_sources/*`，含 gzip 回應與附件。
4. `scripts/build_ccu_catalog.py`：生成原55流程後再補49參考介紹；新 serializer 略去 null/default 時，若 Pydantic 正規化後意義相同，保留已刊流程 bytes。
5. `tests/test_fit_signals.py`、`tests/test_school_completeness.py`：介紹總數844→893，中正55→104；其他五校數量不變，原費用與完整度斷言保留，另驗證49參考介紹不推定當期預算。

原55介紹 prefix SHA256 `1375f32052bcdeaedfe696073e7ada6d40f40bdebeba0dc1e7f82353e38b78e6`。重新生成後，既有官方資料只允許追加 CCU 的49介紹；CGU/NTPU/TKU/NTU/NCU 資料與原 CCU partners、55流程、資格、文件及附件保持不變。

## 重現與驗證

抓取使用 normal TLS、公開 GET、正常 User-Agent；無登入、表單提交或 certificate bypass。候選抓取與人工內容／影像複核分開，重跑抓取不自動核准候選。原始失敗測試紀錄保留，修正後結果另存。

```bash
python scripts/fetch_ccu_completion_sources.py --kind root
python scripts/fetch_ccu_reference_school_documents.py
python scripts/build_ccu_reference_document_reviews.py
python scripts/review_ccu_public_followup.py
python scripts/review_ccu_czu_usj_followup.py
python scripts/build_ccu_completion_reviews.py
python scripts/build_ccu_campus_assets.py
python scripts/compact_ccu_completion_archives.py
python scripts/audit_ccu_completion_sources.py
python scripts/build_ccu_completion_inventory.py
python scripts/validate_ccu_completion.py --output /tmp/ccu-gate.json
PLAYWRIGHT_BROWSERS_PATH=/tmp/ccu-playwright python -m pytest -q tests/test_ccu_completion.py tests/e2e/test_ccu_completion.py
```

完整測試採專案 `run_web_quality_tests.py` 四 shard，無新增排除，保留全部 node ID、JUnit、原始 log 與實測 commit。實際結果列於本次 Draft PR 及交付回報；本環境證據目錄 `/workspace/ccu-completion-artifacts-20261011`。Python/JS、OpenAPI、lock、依賴稽核與打包另驗。SQL migration parser 通過35 migrations／564 statements／11 SQL bodies／74 PL/pgSQL units；隔離 Supabase runtime 的 Docker 映像拉取遇 `no space left on device`，不列成功。沒有啟用 Quality workflow、merge main 或部署。

[實測結果與原始證據](ccu-completion-validation-2026-10-11/report.json)：production commit `c18aebfceeedf8fceba5e4b24bbdf9dbebf0af18` 全套2,668項實際為2,650通過／14略過／4失敗。兩項舊數量常數已修正，相关兩個共用測試檔與中正completion單元測試共31項重跑通過；剩兩項臺大截圖路徑失敗在未改main也同樣重現。仅使用暫存目錄的修補提案於独立對照副本另2項通過，未改臺大測試或工作目錄。截至首批交付cf4d86f，後續commit僅更新兩項共用數量測試與證據文件，所有production Git objects保持一致；不把整套結果改寫成全綠。

第二批從不可覆寫的[9點／7照片／3網站／702欄基準](../src/exchange_info/official_data/ccu/completion-followup-gap-baseline.json)續查，新增3點、3照片、1網站身份並實際填補12個接待缺欄。逐校嘗試URL及來源失敗／研究未完成分開列在[續查清單](ccu-followup-gap-list-2026-10-11.md)；取得公開網頁不等於已核實當期政策。第二批測試及包裝證據另存，首批完整測試報告保留其原commit與原始結果。

[第二批資料與實測證據](ccu-completion-validation-2026-10-11/followup-02/report.json)：選定回歸452項為445通過／4略過／3失敗；兩項已修正且相关四檔41項通過，Jena390原樣重跑通過但保留一次hidden-link不穩定紀錄。CCU completion手机／桌面6項通過；3186個CCU打包檔案逐byte核對。沒有重跑全套2668項或把本批結果宣稱全綠。

第三批續查FGES與QUT，新增1個身份明確的校園marker、填補17個原缺值；期限／語言／校曆矛盾保留，非current項的研究分類與已嘗試URL可在current gap JSON／CSV檢索。母校原partners、49灰字狀態、55原介紹prefix及其他五校資料未改。第三批測試與固定commit證據另列，不覆寫首兩批實測報告。

[第三批固定版本與證據](ccu-completion-validation-2026-10-11/followup-03/report.json)：production `102164aca2bb55b967dea77dc0820db80d71ede7`。全部CCU單元、CGU/NTPU及共用數量回歸365項為361通過／4既有略過；completion手機／桌面10項通過，無新增排除。3249個CCU打包檔案逐byte核對，wheel SHA256 `5ba8dc58e8ad11d90bce90d738505d8a22796e6af52caba370226f81c416d26e`。未重跑全套2668項；首批NTU路徑失敗及第二批Jena390不穩定仍保留。

第四批續查CZU、USJ及QUT住宿，共減少24個原缺欄，現缺值649；CZU2026/2027頁明確區分當期／舊年、Erasmus／non-Erasmus、冬季申請日／Spring未核日期。考試期間只有Summer段原文明示To be specified，其餘日期已核實，不把整份校曆當未公告。USJ2026–2027 PDF5頁及公開Non-European DOCX正文已讀；語言一般B1 recommended／臨床及翻譯B2 mandatory分開，Spring重考PDF7/3與web7/2矛盾保留，個人表未核年份。僅提名後另給通知不自動視為本人登入權限；USJ表格續查分類為research_incomplete。CZU UIS明示個人credentials才標須本人權限。

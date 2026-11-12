# 2026-11-12 每日兩篇驗收

批次日期採 Asia/Taipei；隔離分支 `codex/seo-daily-20261112`，基於 main `0bb1d5c2f043d78451f66ade6c72d7d28c630768`。本批兩篇同屬一個待審 PR；PR：待建立。未合併、部署、寄信或要求 Google 建立索引。排程與 PR 不代表已上線或已收錄。

## 文章與選題

| 題目 | slug | 候選方向與獨立意圖 |
| --- | --- | --- |
| 交換申請截止時間怎麼換算？時區、夏令時間與跨日檢查表 | `exchange-deadline-timezones` | 9 的時間欄位專題：完整原文、日期適用偏移量、跨日、秋季重複時刻、正式詢問與雙時區紀錄。原 Fact Sheet／申請指南保留版本、階段與整體流程。 |
| 托福 Read in Daily Life 怎麼練？校園公告、郵件與原創題目解析 | `toefl-read-in-daily-life` | 19 的日常短文任務：用途、條件、對象與有限推論；兩篇自寫材料、六題四選項、逐項解析及條件換題。與學術科普閱讀、缺字補全及四科總覽分工。 |

選題依編輯判斷，沒有使用者 Search Console、搜尋量或排名資料。遵循本日 main workflow／backlog 及使用者每日兩篇規則；查無適用祖先或 tracked AGENTS。#78、#92 的合併提交已確認為 main 祖先，無未合併基礎相依。既有 47 篇 JSON、網址、published、modified 均未更動，新增後共 49 篇。10/30 `exchange-study-plan` 更新 `97de3fda` 未重做；未實測三工具比較，不製造成果。

## 同日與待審查核

開始及提交前，main 均為上述 SHA；全部五個 open PR #324、#325、#326、#327、#328 的說明與完整分頁檔案清單已讀。#325 雖有 408 個檔案，但屬學校校園攝影與資料清理，不含 editorial JSON、renderer、workflow 或 AGENTS；未搬入其變更。其他為 CGU 展示或影片，不含同意圖文章。提交前五個 head 均未變，同日全狀態 PR 查詢為空；沿用本日唯一隔離分支。

#272、#285、#302 已合併，六篇均在 main；排除重做。下方歷史 backlog 的「待審」以本日實際盤點優先。完整 PR body、head、檔案清單與狀態保存在 [PR 查核](seo-editorial-pr-audit-2026-11-12.json)，47 篇原文雜湊見 [庫存證據](seo-editorial-inventory-2026-11-12.json)。

## 官方來源與數學

[來源與主張紀錄](seo-editorial-sources-2026-11-12.json) 記錄來源版本、查核日、HTTP、解析後頁面範圍、回應雜湊與限制。不是僅檢查網址可連線。

- GOV.UK 時鐘頁實讀正文及 2025–2028 日期表，Last updated 2025-11-24。2027 年前撥為 3/28、回撥為 10/31；不作學校受理依據。
- IANA 當日最新列 2026f（2026-10-27）。循官方 release 下載 tzdata，核對 version、asia 的 Taipei／Taiwan 與 europe 的 London／EU 規則；以該資料編譯，逐一經 UTC 往返核對四個時間點，未用未知版本工具結果代替。計算見 [四個時間點](seo-editorial-timezone-examples-2026-11-12.json)。
- 冬季假設倫敦 2027-02-15 17:00 GMT → UTC 17:00 → 台北 2/16 01:00；17+8=25。夏季 6/15 17:00 BST → UTC 16:00 → 台北 6/16 00:00；17+7=24。10/31 的 01:30 BST／GMT 各對台北 08:30／09:30，相差一小時。全為假設，歧義須窗口確認，不自行選較晚時刻。
- ETS 現行閱讀頁、2026 Update 印刷頁 7–9 及成績尺度實讀。適用 2026-01-21 起版本；1–6 半分及兩年 0–120 整體對照過渡已區分。六題 24 選項答案 D/B/C/A/D/B 逐項核對；沒有把自編答對率換成正式分數、難度、CEFR、錄取或滿分機率。
- 舊標準時間網址 `https://www.stdtime.gov.tw/chinese/` 回 404／空正文，未引用、不捏造存檔；台北偏移量改用可核對的 IANA 官方資料。所有實際引用官方來源均 HTTP 200。沒有未查證費用、資格、獎學金、簽證或真實校方期限。

## 圖片與閱讀畫面

兩張本批專用的真實授權攝影：Pixabay／Pexels 手錶（277390），Katerina Holmes／Pexels 書寫筆記（5905852）。實讀兩張來源頁、ImageObject 及 Pexels License，檢視原始 JPEG；非生成圖。兩張來源 ID 均未用於原 47 篇；新加 WebP 1536×1024，分別 136,972 與 172,874 bytes，低於 450 KB。用 RGB／LANCZOS 等比中心裁切，WebP quality 83，未重繪或變色。圖說不把素材當真實考生／校方通知；手錶品牌不作推薦或背書。

[攝影來源與處理](seo-editorial-photography-2026-11-12.json) 保留作者、來源、原始尺寸、發布日、授權連結、回應／成品雜湊。保留 alt、圖說、作者連結、尺寸與 lazy loading；原創 HTML 五步圖解可直接讀，未改 renderer、metadata、CSS 或 JS。手機表格原生橫捲、FAQ 原生 details，關閉 JavaScript 仍可閱讀。

已目視全部 15 張最終驗收圖，中文／英文、圖解、題目解析與詢問範本可讀，攝影裁切保留主體。最終預覽包括桌面、320px 手機、兩張文中圖、兩個圖解、八個長內容區塊及 3:2／2:1 裁切，共 15 張。只在長區塊截圖暫時隱藏固定頁首與裝飾線，以免拼接蓋住文字；實際頁面、完整畫面及檢查斷言未改。見 [預覽目錄](seo-previews-2026-11-12/desktop-1440.jpg)、[手機](seo-previews-2026-11-12/mobile-320.jpg)、[裁切](seo-previews-2026-11-12/photography-crops.jpg)。

## 驗證結果

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，49 篇，0 errors；完整輸出見 gate JSON |
| 六模組 SEO 單元／整合／release gate | 最終 176 項通過；保留初次 175／1 及修正原因 |
| 三模組桌面／手機 E2E | 換圖前及換圖後各完整 59 項通過；不重複加總 |
| 320／390／1440、兩篇、JavaScript 關閉 | 六組通過；canonical、Article/Breadcrumb、目錄、FAQ、照片、來源、橫捲表格、相關與選校連結 |
| wheel 建置、逐檔核對、checkout 外載入 | 通過；49 JSON／49 專用 WebP／全部 57 CSS／481 個字型目錄檔案及其他閱讀資產，共 637 唯一檔逐位元相同；checkout 外載入 49 篇及兩個新 slug |

初次 SEO 175 通過、1 失敗：最新 main 要求每篇獨立照片，初稿兩篇重用舊圖造成 47／49 不符。已換成兩張新授權攝影並保留原測試斷言；內容與資產固定後完整重跑，不隱藏初跑失敗。其後不再更動文章／圖片，原有 47 篇雜湊維持相同。

本批 wheel 2,424,811,264 bytes，僅留任務 cache，不提交大型套件；字型目錄內 CSS 已去重計算。瀏覽器結果為本地閱讀檢查，不是 production 部署、搜尋排名或真實 Core Web Vitals。初次成功的瀏覽器案例不與最終重跑重複加總。完整命令、各跑次輸出及證據：

- [Release gate](seo-editorial-checks-2026-11-12.json)
- [測試與建置輸出](seo-editorial-tests-2026-11-12.txt)
- [六組瀏覽器與 15 張截圖雜湊](seo-editorial-browser-2026-11-12.json)
- [套件逐檔清單及外部載入](seo-editorial-package-2026-11-12.json)

## 待確認與發布邊界

真實申請的缺漏時區／受理條件由學生向正式窗口核對；本文不假造回覆。未來時區政策或考試版本若變更需重查官方。PR 與 CI 狀態於建立後記錄；本批不自動合併、不部署正式伺服器、不宣稱上線／收錄。任務附件狀態於附加呼叫後記錄。

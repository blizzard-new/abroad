# 2026-11-06 每日雙篇驗收

日期採 Asia/Taipei，依即時 UTC 時鐘確認本次為 11/6 批次。新增兩篇完整繁體中文圖文文章，選題依編輯判斷，沒有使用者 Search Console、搜尋量或排名資料。隔離分支 `codex/seo-daily-20261106`；兩篇同屬一個 PR，[PR #247](https://github.com/blizzard-new/abroad/pull/247) 待審、尚未合併。

| 方向／完整文章 | slug | 實作價值 |
| --- | --- | --- |
| 19：托福 Academic Discussion 怎麼寫？立場、回應同學與原創範例 | `toefl-academic-discussion` | 原創教授提問與兩則同學留言、觀點表、弱稿修改、完整英文回覆、第二個議題與分級檢查 |
| 20：多益 Part 5 詞性題怎麼判斷？空格位置、字族與原創題解析 | `toeic-part-five-word-forms` | 七題原創填空、逐題理由、主幹／修飾關係、口訣限制與換題訂正表 |

## 基準、庫存與防重複

基於 main `18622eec20364822f10674b8b1d84ff1a0b5fc7e`。核對當期 workflow 與先前已完整閱讀版本無差異，讀取最新 backlog、35 篇庫存與相關正文：托福總覽、Build a Sentence、多益聽讀總覽；先前郵件、口說、閱讀及最近四篇均已核對並排除。未發現適用 AGENTS.md。

全部 11 個 open PR #234、#236、#237、#239–#246 的標題、說明及完整分頁檔案清單均核對；三個校務型錄及八個稽核提案沒有 editorial JSON 或 SEO 流程檔案。本次沒有既存同日分支／任何狀態同日 PR。詳見 [PR 查核](seo-editorial-pr-audit-2026-11-06.json)。

基礎 #78、流程 #92 已合併。11/4 #233 與 11/5 #238 也已合併，其四篇已在 main；下方歷史 backlog 的待審字樣代表當時狀態，見 [前批狀態](seo-editorial-previous-batches-2026-11-06.json)。10/30 讀書計畫擴充保留於 `97de3fda`，沒有重做；候選 15 未取得實測，沒有製造工具比較。本批直接沿用 main，沒有未合併的內容基礎相依。

討論篇聚焦自己的立場如何回應他人理由並增加內容，與郵件任務、給定片段組句及四科總覽分工。詞性篇聚焦句中空格功能、詞形及意思，與全卷安排、Part 2 應答、Part 3 圖表及 Part 7 跨文件分工。兩篇有完整獨立練習，不以品牌／年份／改標題重發。原有 35 篇 JSON 逐檔對 Git 基準相同，URL、published、modified／lastmod 保留，見 [庫存雜湊](seo-editorial-inventory-2026-11-06.json)。本分支共 37 篇，沒有改 renderer、CSS、schema、資料庫或原共用 checkout。

## 來源、版本與示例核對

- 實讀 ETS 現行寫作頁：討論任務為陳述支持意見、發展想法、回應他人及學術語氣；讀取 2026 Update 規格文件寫作章節印刷頁 13–14 的情境、組織與支持細節。未將原始點數／預估時長改成正式級距或每題固定秒數，也沒有自行宣布所有題目共用的人物數、字數或句數。
- 實讀 ETS 成績頁：2026-01-21 起 1–6 半分尺度，最高 6；兩年過渡期間有可對照的 0–120 整體分數。自編寫作沒有官方評分、換算或提分保證。
- 實讀臺灣多益官方內容表與 Part 5 directions／題型：30 題，每句缺字或片語、四選一。沒有把 Part 5 全部說成詞性題；官方 101–105 範例沒有轉載進文章。
- 實讀 British Council 文法本文：形容詞位置、方式副詞、名詞片語及名詞修飾名詞。只依教學本文，不以留言區作依據。Adjectives 索引只用來找到具體教學頁，沒有作實質文法證據。所有必要來源均 HTTP 200；未見確切修訂日的網頁已明示當日版本限制。
- 討論例題問的是是否要求**所有一年級學生**加入，回覆清楚選自願安排。認可 Lina 提問空間的理由，不把她改成反對強制；承接 Omar 的時段限制，不新增實際工作／通勤時數。共用文件與短會議是明示的假設做法，沒有當成校方政策、學生研究或成效數據。換題錄影議題也是自編。
- 七題詞性答案依次 **B、C、C、A、C、B、C**：carefully、decision、successfully、visible、applies、clear、electronically。逐句核對空格功能、動詞結構、單數主詞、修飾關係與語意；第 5 題星期一只是虛構句子的條件。沒有費用試算、期限／採認保證、假設統計或練習正確率到正式分數的換算。
- 全部題目、人物、草稿、回覆、解析與練習分級均為 UniWay 自編教學，沒有學生訪談、模型實測、專家審核、官方難度或 CEFR 校準。

可核對 URL、來源版本、HTTP 狀態、回應 SHA-256、讀取範圍與主張邊界見 [來源紀錄](seo-editorial-sources-2026-11-06.json)。

## 圖片與閱讀畫面

重新讀取兩張 Pexels 原始照片頁與 License。沿用 Zen Chung 戶外筆記照與 PNW Production 書寫特寫，1536×1024 WebP，111,030／88,086 bytes，皆低於 450 KB，像素不變。文章有主題 alt、素材情境圖說、攝影者與來源，沒有宣稱真實考生／考場、練習成果或校園；見 [攝影與授權紀錄](seo-editorial-photography-2026-11-06.json)。

使用實際 `create_app`、拋棄式資料目錄、Chromium，關閉 JavaScript，兩篇各 320／390／1440 px，共六組。驗證 H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ、圖片載入／alt／lazy／來源／尺寸、相關文章與母校／目的地／選校工具連結。手機表格實際改變 scrollLeft 確認可捲動，頁面本身無水平溢出。撰文代理目視檢查文字、來源、攝影、圖解與練習區塊，並核對 3:2／2:1 裁切保留主體。

- [桌機](seo-previews-2026-11-06/desktop-1440.jpg)、[手機](seo-previews-2026-11-06/mobile-320.jpg)、[攝影裁切](seo-previews-2026-11-06/photography-crops.jpg)
- [討論題](seo-previews-2026-11-06/toefl-academic-discussion-original-discussion-390.jpg)、[弱稿修改](seo-previews-2026-11-06/toefl-academic-discussion-revise-a-draft-390.jpg)、[完整回覆](seo-previews-2026-11-06/toefl-academic-discussion-complete-response-390.jpg)、[換題](seo-previews-2026-11-06/toefl-academic-discussion-transfer-and-check-390.jpg)
- [詞性題](seo-previews-2026-11-06/toeic-part-five-word-forms-original-questions-390.jpg)、[解析與圖解](seo-previews-2026-11-06/toeic-part-five-word-forms-answers-and-relations-390.jpg)、[口訣限制](seo-previews-2026-11-06/toeic-part-five-word-forms-limits-of-shortcuts-390.jpg)、[換題](seo-previews-2026-11-06/toeic-part-five-word-forms-transfer-practice-390.jpg)
- [討論篇圖片與圖說](seo-previews-2026-11-06/toefl-study-photo-390.jpg)、[詞性篇圖片與圖說](seo-previews-2026-11-06/writing-photo-390.jpg)

## 驗收

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，37 篇 |
| SEO 單元／整合／release gate 六模組 | 153 passed |
| SEO 文章／頁面／analytics E2E 三模組 | 47 passed |
| 無 JavaScript 桌機／手機閱讀 | 六組通過，目視完成 |
| `uv build --wheel` 與套件核對 | 通過；37 JSON、27 張唯一 WebP、CSS／renderer／init 共 67 檔逐位元相同 |
| checkout 外載入抽出套件 | 通過，37 篇與兩個新 slug 可載入 |

證據見 [release gate](seo-editorial-checks-2026-11-06.json)、[測試紀錄](seo-editorial-tests-2026-11-06.txt)、[瀏覽器紀錄](seo-editorial-browser-2026-11-06.json)、[套件 manifest](seo-editorial-package-2026-11-06.json)。本批實際 wheel 為 2,372,201,430 bytes，留於任務 cache，沒有提交 Git。

## 待審與發布邊界

[PR #247](https://github.com/blizzard-new/abroad/pull/247) 待審、尚未合併。兩篇一起審閱，沒有合併、Windows 正式部署、寄信或要求 Google 批次索引。PR 與本機驗收不代表已上線、收錄或具有排名；自編教材也不代替正式成績與採認規定。

任務附件服務已呼叫，60 秒未回覆；附件清單也在 10 秒內未回覆，無法確認掛載。GitHub PR 已成功建立並另行核對，附件狀態不冒稱成功。

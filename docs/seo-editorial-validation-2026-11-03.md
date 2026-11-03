# 2026-11-03 SEO 雙篇驗收

日期採 Asia/Taipei；開始查核時間 2026-11-03 08:03:33。隔離分支 `codex/seo-daily-20261103`，基於 main `7f124f1205dec0ed6cce046089b45a6a342208c9`。兩篇完整圖文及必要驗收已完成，同屬本日唯一 [PR #222](https://github.com/blizzard-new/abroad/pull/222)，目前待審；未合併或部署。

## 文章與選題分工

| 標題 | slug | 內容 |
| --- | --- | --- |
| 用 AI 練英文閱讀怎麼做？精讀 Prompt、原文證據與訂正示例 | `ai-english-reading-practice` | 三輪有填寫欄位的 Prompt、兩段原創短文與簡化版、人工問答訂正、故意錯誤回饋查核、分級換題 |
| 托福 Write an Email 怎麼寫？題目拆解、回信範例與檢查表 | `toefl-write-an-email` | 完整原創題目、事實／任務對照、初稿修改與原因、完整郵件及不同情境的轉用練習 |

本批取自原候選方向 17、19，依編輯判斷，沒有 Search Console 成效、搜尋量或排名證據。完整重讀 `ai-english-learning`，並核對既有托福總覽與昨日文章；新文分別處理單段閱讀回饋查核及 Write an Email 的完整實作。既有總覽保留每日四技能安排與版本／四科／計分概觀，新頁以新的材料與解析完成具體任務，不是改標題、換年份或為各品牌複製頁面。

開始前查核 main 27 篇、工作區／祖先及 main 全樹的 `AGENTS.md`（無適用檔案）、所有 12 個待審 PR 的標題、說明摘要與完整變更檔案清單：#209、#210、#211、#212、#213、#214、#216、#217、#218、#219、#220、#221。#213 的兩篇已選並排除，其餘沒有 editorial JSON 變更。#78、#92 已合併；本批直接基於 main，不依賴其他待審分支。

同日分支／所有狀態 PR 開始前均不存在。10/30 的讀書計畫更新保留在原分支，11/2 PR #213 的托福重述與多益跨篇題組亦保留；沒有重做或移入本批。原共享 checkout 及他人工作未改動。新文章的 published／modified／checked 均為 2026-11-03；原有 27 篇 JSON 位元、網址、刊載日、modified／lastmod 均不變。本分支共 29 篇，不將仍在 #213 的兩篇誤算為本分支內容。

## 來源與主張核對

[來源清單](seo-editorial-sources-2026-11-03.json) 保存八個引用來源的 URL、當日 HTTP 結果、回應 SHA-256、版本、支援主張與限制。全部成功實際讀取，未用搜尋摘要代替正文。

- AI 閱讀：British Council 現行閱讀頁及 Level test，核對按 CEFR 整理的材料入口及程度測驗為概略指引；OpenAI 提示指引與準確性說明，核對明確背景、逐輪檢視、錯誤／虛構引文及重要資訊須查證。沒有把這些來源當成本文方法的成效研究，也未使用其商品／方案敘述作功能承諾。閱讀頁實際轉到 `/free-resources/reading`，文章引用現行網址。
- 托福：ETS 現行寫作、內容、版本／成績頁及 18 頁 `2026 Update` 規格文件。讀取實體第 6 頁寫作表與第 14–15 頁目的、收件對象、組織和語氣說明，核對封面版本與規格微調限制，以現行 HTML 交叉確認任務。版本說明明示 2026-01-21，本文未套用原始點數、預估時間、字數或逐項扣分公式。

官方 HTML 未明示確切修訂日期，保存當日版本；OpenAI 頁面相對更新標示分別是 14 天、11 天，未反推成確切修訂日。沒有新增真實費用、期限、語言門檻、獎助金額或簽證要求。

## 原創示例的驗算與限制

AI 篇的閱讀室、線上工作坊及較短版本均獨立自寫，只有簡化版刻意減少資訊並明示不完整。問答、訂正及「星期五九點開門」錯誤回饋是人工設計，未宣稱任何工具實際產生這些內容。核對時間關係：星期三 7:30 晚於可入室的 7:00、早於服務台 9:00；星期四的前一天是星期三，第一段最晚 18:00 預約，轉用段為中午 12:00，不沿用舊答案。星期五的 usual hours 沒有確切時間；桌位不保證筆電。所有時間只屬虛構語言材料，不是校方規定。

托福的 Ms. Lee／Alex、確認信與預約情境均為假設。原要求星期五 15:00，收到的紀錄為星期四 15:00；星期一 15:00 僅為星期五無法安排時的備案。完整範例逐項回應差異、請求／條件與書面確認，沒有新增房號、付款、核准或真實寄信。初稿、修改與完整郵件不是 ETS 題目、實際考生答案或模型輸出，未提供官方分數。

三輪 AI Prompt 各有輸入欄位、操作順序、原文查核及人工檢查表；本文沒有品牌比較、模型／方案／地區實測、語音或上傳功能主張。分級為編輯負荷調整，不認定 CEFR；練習不替代正式語言成績，不保證錄取或固定天數進步。

## 攝影與實際閱讀畫面

沿用兩張像素未修改的 Pexels 真實攝影：Roxanne Minnish 的 `english-guide-photo.webp`（121,464 bytes）及 PNW Production 的 `writing-photo.webp`（88,086 bytes），皆 1536×1024、低於 450 KB。重新閱讀素材頁與完整 Pexels License，提供作者、來源、正確 alt、圖說與素材身分揭露，見[攝影來源紀錄](seo-editorial-photography-2026-11-03.json)。沒有生成、替換圖片或將衣服標誌、人物、筆電與筆記冒稱特定校園、官方題目或考生成效。

產文代理已實際開啟原圖、3:2／2:1 裁切、桌機 1440、手機 320 閱讀圖、390 的兩張五步 HTML 圖解、兩張照片／圖說，以及原創短文、Prompt／答案、初稿修改與完整郵件局部截圖。中文、英文及材料可讀；表格在手機能橫向捲動，整頁無水平溢出。沒有聲稱人類、專家或實際學習者測試。

- [桌機](seo-previews-2026-11-03/desktop-1440.jpg)、[手機](seo-previews-2026-11-03/mobile-320.jpg)、[圖片裁切](seo-previews-2026-11-03/photo-crops.jpg)
- [AI 精讀五步圖](seo-previews-2026-11-03/ai-english-reading-practice-diagram-390.jpg)、[郵件五步圖](seo-previews-2026-11-03/toefl-write-an-email-diagram-390.jpg)
- [原創短文](seo-previews-2026-11-03/ai-english-reading-practice-original-reading-390.jpg)、[Prompt 與訂正](seo-previews-2026-11-03/ai-english-reading-practice-prompt-two-and-answers-390.jpg)
- [初稿修改](seo-previews-2026-11-03/toefl-write-an-email-draft-to-revision-390.jpg)、[完整郵件](seo-previews-2026-11-03/toefl-write-an-email-complete-example-390.jpg)

## 測試及套件

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 29 篇、零錯誤；[完整報告](seo-editorial-checks-2026-11-03.json) |
| SEO 單元／整合／發行 gate | 135 passed，95.55 秒 |
| Chromium E2E | 39 passed，178.02 秒 |
| 新文無 JavaScript 閱讀 | 兩篇 × 320／390／1440，6／6 通過；[瀏覽器紀錄](seo-editorial-browser-2026-11-03.json) |
| Wheel | `uv build --wheel` 成功；29 JSON、27 張不重複 WebP、CSS／renderer／初始化檔共 59 檔逐位元一致；checkout 外載入 29 篇並確認新文；[套件紀錄](seo-editorial-package-2026-11-03.json) |

測試使用既有虛擬環境、`PYTHONPATH=src` 與隔離資料目錄。SEO 範圍：`test_seo_articles.py`、`test_seo.py`、`test_seo_content.py`、`test_seo_quality.py`、`test_seo_reporting.py`、`test_editorial_release_gate.py`；E2E 為 `test_seo_articles.py`、`test_seo_pages.py`、`test_seo_analytics.py`，使用 `/usr/bin/chromium`。[完整 pytest 輸出](seo-editorial-tests-2026-11-03.txt) 保存於本批。

瀏覽器另核對 HTTP 200、唯一 H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ 展開、照片尺寸／lazy loading／alt／來源、相關導航及母校／目的地／選校工具入口。手機 AI 篇兩張、托福篇三張表格皆實際可捲動。沿用社群標記與 Sitemap，無 renderer、CSS、路由、資料庫或第三方腳本變更。這是本機驗收，不是正式站狀態、Core Web Vitals、搜尋排名或 Google 收錄證據。大型 wheel 不加入 Git。

## 交付邊界

兩篇連同來源、照片授權、截圖、測試及選題紀錄進入本日一個待審 PR。內容仍待人工審閱；無未查證的核心制度主張待填補。本次未合併、未部署 Windows 正式伺服器、未寄信給第三方或批量要求 Google 索引，不宣稱排程完成即已上線／收錄。
